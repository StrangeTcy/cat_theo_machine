import os

from . import machine as M
from . import graph as G
from . import mining as Min
from . import wire as W
from .gmprep import GMPEqualText, GMPPredText, GMPSuccText


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


class BoundedRoundRobinShardChunk(M.Edge):
    def __init__(self, nodes, remaining_text, cursor_text, shard_text, worker_count_text):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(
                M.EmptyList,
                M.Pair(M.EmptyList, M.Pair(M.Char(cursor_text), M.EmptyList)),
            )
        elif GMPEqualText(remaining_text, "0")() is M.truth_value:
            self.result = M.Pair(
                M.EmptyList,
                M.Pair(nodes, M.Pair(M.Char(cursor_text), M.EmptyList)),
            )
        else:
            next_cursor_text = GMPSuccText(cursor_text)()
            if GMPEqualText(next_cursor_text, worker_count_text)() is M.truth_value:
                next_cursor_text = "0"
            tail = BoundedRoundRobinShardChunk(
                M.Tail(nodes)(),
                GMPPredText(remaining_text)(),
                next_cursor_text,
                shard_text,
                worker_count_text,
            )()
            selected = M.Head(tail)()
            if GMPEqualText(cursor_text, shard_text)() is M.truth_value:
                selected = M.Pair(M.Head(nodes)(), selected)
            self.result = M.Pair(
                selected,
                M.Pair(
                    M.Head(M.Tail(tail)())(),
                    M.Pair(
                        M.Head(M.Tail(M.Tail(tail)())())(),
                        M.EmptyList,
                    ),
                ),
            )
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RoundRobinWorkerShard(M.Edge):
    def __init__(self, nodes, cursor_text, shard_text, worker_count_text):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            chunk = BoundedRoundRobinShardChunk(
                nodes, "256", cursor_text, shard_text, worker_count_text,
            )()
            selected = M.Head(chunk)()
            remainder = M.Head(M.Tail(chunk)())()
            next_cursor_text = M.Head(M.Tail(M.Tail(chunk)())())()()
            later = RoundRobinWorkerShard(
                remainder,
                next_cursor_text,
                shard_text,
                worker_count_text,
            )()
            self.result = Min.AppendMachineChains(selected, later)()
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
    def __init__(self, shard_text, worker_count_text, request_path, result_path):
        process_text = str(os.getpid())
        print(
            "[foreground worker " + process_text + "] starting equal graph shard "
            + shard_text + " of " + worker_count_text,
            flush=True,
        )
        with open(request_path, "rb") as request_stream:
            request = W.deserialize_term(request_stream.read())
        graph_version = M.Head(request)()
        goal = M.Head(M.Tail(request)())()
        assumptions = M.Head(M.Tail(M.Tail(request)())())()
        registry = M.AllConstructors
        shard = RoundRobinWorkerShard(
            G.GraphNodes(graph_version)(), "0", shard_text, worker_count_text,
        )()
        result_mode = "none"
        result = ChunkedProofLookup(
            "cubic", graph_version, goal, assumptions, registry, shard,
        )()
        if M.IdentityCompare(result, M.EmptyList)() is M.false_value:
            result_mode = "cubic"
        else:
            result = ChunkedProofLookup(
                "direct", graph_version, goal, assumptions, registry, shard,
            )()
            if M.IdentityCompare(result, M.EmptyList)() is M.false_value:
                result_mode = "direct"
            else:
                result = ChunkedProofLookup(
                    "chain", graph_version, goal, assumptions, registry, shard,
                )()
                if M.IdentityCompare(result, M.EmptyList)() is M.false_value:
                    result_mode = "chain"
        result_flag = "0"
        if result_mode == "cubic":
            result_flag = "C"
        elif result_mode == "direct":
            result_flag = "D"
        elif result_mode == "chain":
            result_flag = "H"
        temporary_path = result_path + ".tmp"
        with open(temporary_path, "w", encoding="utf-8") as result_stream:
            result_stream.write(result_flag)
        os.replace(temporary_path, result_path)
        print(
            "[foreground worker " + process_text + "] finished equal graph shard "
            + shard_text + " of " + worker_count_text + ": " + result_mode,
            flush=True,
        )
