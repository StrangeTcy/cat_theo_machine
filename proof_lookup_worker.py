import os

from . import machine as M
from . import graph as G
from . import mining as Min
from . import wire as W
from .gmprep import GMPEqualText, GMPPredText


class BoundedNodeChunk(M.Edge):
    def __init__(self, nodes, remaining_text):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
        elif GMPEqualText(remaining_text, "0")() is M.truth_value:
            self.result = M.Pair(M.EmptyList, M.Pair(nodes, M.EmptyList))
        else:
            tail = BoundedNodeChunk(
                M.Tail(nodes)(), GMPPredText(remaining_text)(),
            )()
            self.result = M.Pair(
                M.Pair(M.Head(nodes)(), M.Head(tail)()),
                M.Pair(M.Head(M.Tail(tail)())(), M.EmptyList),
            )
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ChunkedProofLookup(M.Edge):
    def __init__(self, mode_text, graph_version, goal, assumptions, registry, nodes):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            chunked = BoundedNodeChunk(nodes, "384")()
            chunk = M.Head(chunked)()
            remainder = M.Head(M.Tail(chunked)())()
            if mode_text == "cubic":
                hit = Min.ReplayInstalledCubicLemma(
                    graph_version, goal, assumptions, registry,
                    chunk, M.truth_value,
                )()
            elif mode_text == "direct":
                hit = Min.ReplayInventedLemma(
                    graph_version, goal, registry, chunk, M.truth_value,
                )()
            else:
                hit = Min.ReplayInventedLemmaChain(
                    graph_version, goal, registry, chunk, M.truth_value,
                )()
            if M.IdentityCompare(hit, M.EmptyList)() is M.false_value:
                self.result = hit
            else:
                self.result = ChunkedProofLookup(
                    mode_text, graph_version, goal, assumptions,
                    registry, remainder,
                )()
        super().__init__(inputs=M.Pair(graph_version, M.Pair(goal, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ProofLookupWorker:
    def __init__(self, mode_text, request_path, result_path):
        process_text = str(os.getpid())
        print(
            "[foreground worker " + process_text + "] starting "
            + mode_text + " lemma lookup",
            flush=True,
        )
        with open(request_path, "rb") as request_stream:
            request = W.deserialize_term(request_stream.read())
        graph_version = M.Head(request)()
        goal = M.Head(M.Tail(request)())()
        assumptions = M.Head(M.Tail(M.Tail(request)())())()
        registry = M.AllConstructors
        result = ChunkedProofLookup(
            mode_text,
            graph_version,
            goal,
            assumptions,
            registry,
            G.GraphNodes(graph_version)(),
        )()
        temporary_path = result_path + ".tmp"
        found_text = "no match"
        found_flag = "0"
        if M.IdentityCompare(result, M.EmptyList)() is M.false_value:
            found_text = "match found"
            found_flag = "1"
        with open(temporary_path, "w", encoding="utf-8") as result_stream:
            result_stream.write(found_flag)
        os.replace(temporary_path, result_path)
        print(
            "[foreground worker " + process_text + "] finished "
            + mode_text + " lemma lookup: " + found_text,
            flush=True,
        )
