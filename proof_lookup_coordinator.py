import multiprocessing
import os

from . import machine as M
from . import wire as W
from .proof_lookup_worker import ProofLookupWorker


class ProofLookupProcess(multiprocessing.Process):
    def __init__(self, shard_text, worker_count_text, request_path, result_path):
        self.shard_text = shard_text
        self.worker_count_text = worker_count_text
        self.request_path = request_path
        self.result_path = result_path
        super().__init__()

    def run(self):
        try:
            ProofLookupWorker(
                self.shard_text,
                self.worker_count_text,
                self.request_path,
                self.result_path,
            )
        except Exception as failure:
            temporary_path = self.result_path + ".tmp"
            with open(temporary_path, "w", encoding="utf-8") as result_stream:
                result_stream.write("E")
            os.replace(temporary_path, self.result_path)
            print(
                "[foreground worker " + str(os.getpid()) + "] failed equal graph shard "
                + self.shard_text + " of " + self.worker_count_text + ": "
                + str(failure),
                flush=True,
            )


class ParallelProofLookupMode(M.Edge):
    def __init__(self, graph_version, goal, assumptions):
        process_text = str(os.getpid())
        worker_count_text = "3"
        request_path = os.path.join(
            os.path.dirname(__file__), "snapshots",
            "foreground-proof-" + process_text + ".wire",
        )
        first_path = request_path + ".shard-0"
        second_path = request_path + ".shard-1"
        third_path = request_path + ".shard-2"
        request = M.Pair(
            graph_version,
            M.Pair(goal, M.Pair(assumptions, M.EmptyList)),
        )
        with open(request_path, "wb") as request_stream:
            request_stream.write(W.serialize_term(request))
        first_process = ProofLookupProcess(
            "0", worker_count_text, request_path, first_path,
        )
        second_process = ProofLookupProcess(
            "1", worker_count_text, request_path, second_path,
        )
        third_process = ProofLookupProcess(
            "2", worker_count_text, request_path, third_path,
        )
        first_process.start()
        second_process.start()
        third_process.start()
        print(
            "DEBUG [foreground coordinator " + process_text
            + "]: assigned equal graph shard 0 of 3 to process "
            + str(first_process.pid),
            flush=True,
        )
        print(
            "DEBUG [foreground coordinator " + process_text
            + "]: assigned equal graph shard 1 of 3 to process "
            + str(second_process.pid),
            flush=True,
        )
        print(
            "DEBUG [foreground coordinator " + process_text
            + "]: assigned equal graph shard 2 of 3 to process "
            + str(third_process.pid),
            flush=True,
        )
        first_process.join()
        second_process.join()
        third_process.join()
        first_found = "0"
        second_found = "0"
        third_found = "0"
        if os.path.exists(first_path):
            with open(first_path, "r", encoding="utf-8") as result_stream:
                first_found = result_stream.read().strip()
        if os.path.exists(second_path):
            with open(second_path, "r", encoding="utf-8") as result_stream:
                second_found = result_stream.read().strip()
        if os.path.exists(third_path):
            with open(third_path, "r", encoding="utf-8") as result_stream:
                third_found = result_stream.read().strip()
        self.result = "none"
        if first_found == "E":
            self.result = "worker-failure"
        elif second_found == "E":
            self.result = "worker-failure"
        elif third_found == "E":
            self.result = "worker-failure"
        elif first_found == "C":
            self.result = "cubic"
        elif second_found == "C":
            self.result = "cubic"
        elif third_found == "C":
            self.result = "cubic"
        elif first_found == "D":
            self.result = "direct"
        elif second_found == "D":
            self.result = "direct"
        elif third_found == "D":
            self.result = "direct"
        elif first_found == "H":
            self.result = "chain"
        elif second_found == "H":
            self.result = "chain"
        elif third_found == "H":
            self.result = "chain"
        if os.path.exists(request_path):
            os.remove(request_path)
        if os.path.exists(first_path):
            os.remove(first_path)
        if os.path.exists(second_path):
            os.remove(second_path)
        if os.path.exists(third_path):
            os.remove(third_path)
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(goal, M.EmptyList)),
            results=M.Char(self.result),
        )

    def __call__(self):
        return self.result
