import os

from . import machine as M
from . import mining as Min
from . import wire as W


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
        if mode_text == "cubic":
            result = Min.ReplayInstalledCubicLemma(
                graph_version, goal, assumptions, registry,
            )()
        elif mode_text == "direct":
            result = Min.ReplayInventedLemma(
                graph_version, goal, registry,
            )()
        else:
            result = Min.ReplayInventedLemmaChain(
                graph_version, goal, registry,
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
