import multiprocessing
import os

from . import machine as M
from . import wire as W
from .proof_lookup_worker import ProofLookupWorker


class ProofLookupProcess(multiprocessing.Process):
    def __init__(self, mode_text, request_path, result_path):
        self.mode_text = mode_text
        self.request_path = request_path
        self.result_path = result_path
        super().__init__()

    def run(self):
        try:
            ProofLookupWorker(
                self.mode_text, self.request_path, self.result_path,
            )
        except Exception as failure:
            temporary_path = self.result_path + ".tmp"
            with open(temporary_path, "w", encoding="utf-8") as result_stream:
                result_stream.write("E")
            os.replace(temporary_path, self.result_path)
            print(
                "[foreground worker " + str(os.getpid()) + "] failed "
                + self.mode_text + " lemma lookup: " + str(failure),
                flush=True,
            )


class ParallelProofLookupMode(M.Edge):
    def __init__(self, graph_version, goal, assumptions):
        process_text = str(os.getpid())
        request_path = os.path.join(
            os.path.dirname(__file__), "snapshots",
            "foreground-proof-" + process_text + ".wire",
        )
        cubic_path = request_path + ".cubic"
        direct_path = request_path + ".direct"
        chain_path = request_path + ".chain"
        request = M.Pair(
            graph_version,
            M.Pair(goal, M.Pair(assumptions, M.EmptyList)),
        )
        with open(request_path, "wb") as request_stream:
            request_stream.write(W.serialize_term(request))
        cubic_process = ProofLookupProcess("cubic", request_path, cubic_path)
        direct_process = ProofLookupProcess("direct", request_path, direct_path)
        chain_process = ProofLookupProcess("chain", request_path, chain_path)
        cubic_process.start()
        direct_process.start()
        chain_process.start()
        print(
            "DEBUG [foreground coordinator " + process_text
            + "]: spawned cubic lookup process " + str(cubic_process.pid),
            flush=True,
        )
        print(
            "DEBUG [foreground coordinator " + process_text
            + "]: spawned direct lookup process " + str(direct_process.pid),
            flush=True,
        )
        print(
            "DEBUG [foreground coordinator " + process_text
            + "]: spawned chain lookup process " + str(chain_process.pid),
            flush=True,
        )
        cubic_process.join()
        direct_process.join()
        chain_process.join()
        cubic_found = "0"
        direct_found = "0"
        chain_found = "0"
        if os.path.exists(cubic_path):
            with open(cubic_path, "r", encoding="utf-8") as result_stream:
                cubic_found = result_stream.read().strip()
        if os.path.exists(direct_path):
            with open(direct_path, "r", encoding="utf-8") as result_stream:
                direct_found = result_stream.read().strip()
        if os.path.exists(chain_path):
            with open(chain_path, "r", encoding="utf-8") as result_stream:
                chain_found = result_stream.read().strip()
        self.result = "none"
        if cubic_found == "E":
            self.result = "worker-failure"
        elif direct_found == "E":
            self.result = "worker-failure"
        elif chain_found == "E":
            self.result = "worker-failure"
        elif cubic_found == "1":
            self.result = "cubic"
        elif direct_found == "1":
            self.result = "direct"
        elif chain_found == "1":
            self.result = "chain"
        if os.path.exists(request_path):
            os.remove(request_path)
        if os.path.exists(cubic_path):
            os.remove(cubic_path)
        if os.path.exists(direct_path):
            os.remove(direct_path)
        if os.path.exists(chain_path):
            os.remove(chain_path)
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(goal, M.EmptyList)),
            results=M.Char(self.result),
        )

    def __call__(self):
        return self.result
