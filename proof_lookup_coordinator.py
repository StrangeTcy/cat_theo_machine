import multiprocessing
import os

from . import machine as M
from . import wire as W
from .gmprep import GMPEqualText, GMPLessText, GMPPredText, GMPSuccText
from .proof_lookup_worker import ProofLookupWorker


PROOF_LOOKUP_REQUEST_NAME = "proof_lookup_request.wire"
PROOF_LOOKUP_TAKEN_NAME = "proof_lookup_request.wire.taken"
PROOF_LOOKUP_RESPONSE_NAME = "proof_lookup_response.txt"


class WaitForProofLookupResponse(M.Edge):
    def __init__(self, response_path, attempts_text):
        if os.path.exists(response_path):
            with open(response_path, "r", encoding="utf-8") as response_stream:
                self.result = response_stream.read().strip()
        elif GMPEqualText(attempts_text, "0")() is M.truth_value:
            self.result = "service-timeout"
        else:
            import time

            time.sleep(0.25)
            self.result = WaitForProofLookupResponse(
                response_path, GMPPredText(attempts_text)(),
            )()
        super().__init__(inputs=M.Pair(M.Char(response_path), M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result


class DaemonProofLookupMode(M.Edge):
    def __init__(self, snapshot_dir, graph_version, goal, assumptions):
        request_path = os.path.join(snapshot_dir, PROOF_LOOKUP_REQUEST_NAME)
        response_path = os.path.join(snapshot_dir, PROOF_LOOKUP_RESPONSE_NAME)
        if os.path.exists(response_path):
            os.remove(response_path)
        request = M.Pair(
            graph_version,
            M.Pair(goal, M.Pair(assumptions, M.EmptyList)),
        )
        temporary_path = request_path + ".tmp"
        with open(temporary_path, "wb") as request_stream:
            request_stream.write(W.serialize_term(request))
        os.replace(temporary_path, request_path)
        print(
            "DEBUG [foreground coordinator " + str(os.getpid())
            + "]: submitted equal-shard proof lookup to the existing daemon worker service",
            flush=True,
        )
        self.result = WaitForProofLookupResponse(response_path, "480")()
        if os.path.exists(response_path):
            os.remove(response_path)
        super().__init__(inputs=M.Pair(graph_version, M.Pair(goal, M.EmptyList)), results=M.Char(self.result))

    def __call__(self):
        return self.result


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
                "[daemon proof worker " + str(os.getpid()) + "] failed equal graph shard "
                + self.shard_text + " of " + self.worker_count_text + ": "
                + str(failure),
                flush=True,
            )


class ProofLookupWorkPacket(M.Edge):
    def __init__(self, shard_text, worker_count_text, result_path):
        self.result = M.Pair(
            M.Char("proof-lookup-shard"),
            M.Pair(
                M.Char(shard_text),
                M.Pair(
                    M.Char(worker_count_text),
                    M.Pair(M.Char(result_path), M.EmptyList),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(M.Char(shard_text), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofLookupWorkPlan(M.Edge):
    def __init__(self, shard_text, worker_count_text, request_path):
        if GMPEqualText(shard_text, worker_count_text)() is M.truth_value:
            self.result = M.EmptyList
        else:
            result_path = request_path + ".shard-" + shard_text
            packet = ProofLookupWorkPacket(
                shard_text, worker_count_text, result_path,
            )()
            self.result = M.Pair(
                packet,
                ProofLookupWorkPlan(
                    GMPSuccText(shard_text)(), worker_count_text, request_path,
                )(),
            )
        super().__init__(inputs=M.Pair(M.Char(shard_text), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SpawnProofLookupPlan(M.Edge):
    def __init__(self, plan, request_path, coordinator_text):
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            packet = M.Head(plan)()
            shard_text = M.Head(M.Tail(packet)())()()
            worker_count_text = M.Head(M.Tail(M.Tail(packet)())())()()
            result_path = M.Head(M.Tail(M.Tail(M.Tail(packet)())())())()()
            process = ProofLookupProcess(
                shard_text, worker_count_text, request_path, result_path,
            )
            process.start()
            print(
                "DEBUG [daemon worker coordinator " + coordinator_text
                + "]: assigned equal graph shard " + shard_text + " of "
                + worker_count_text + " to process " + str(process.pid),
                flush=True,
            )
            self.result = M.Pair(
                process,
                SpawnProofLookupPlan(
                    M.Tail(plan)(), request_path, coordinator_text,
                )(),
            )
        super().__init__(inputs=M.Pair(plan, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class JoinProofLookupProcesses(M.Edge):
    def __init__(self, processes):
        if M.IdentityCompare(processes, M.EmptyList)() is M.truth_value:
            self.result = M.truth_value
        else:
            process = M.Head(processes)()
            process.join()
            self.result = JoinProofLookupProcesses(M.Tail(processes)())()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ProofLookupModeMerge(M.Edge):
    def __init__(self, left_text, right_text):
        self.result = right_text
        if left_text == "worker-failure":
            self.result = left_text
        elif right_text == "worker-failure":
            self.result = right_text
        elif left_text == "cubic":
            self.result = left_text
        elif right_text == "cubic":
            self.result = right_text
        elif left_text == "direct":
            self.result = left_text
        elif right_text == "direct":
            self.result = right_text
        elif left_text == "chain":
            self.result = left_text
        super().__init__(inputs=M.Pair(M.Char(left_text), M.Pair(M.Char(right_text), M.EmptyList)), results=M.Char(self.result))

    def __call__(self):
        return self.result


class ProofLookupPlanResult(M.Edge):
    def __init__(self, plan):
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            self.result = "none"
        else:
            packet = M.Head(plan)()
            result_path = M.Head(M.Tail(M.Tail(M.Tail(packet)())())())()()
            result_flag = "E"
            if os.path.exists(result_path):
                with open(result_path, "r", encoding="utf-8") as result_stream:
                    result_flag = result_stream.read().strip()
            local_mode = "none"
            if result_flag == "E":
                local_mode = "worker-failure"
            elif result_flag == "C":
                local_mode = "cubic"
            elif result_flag == "D":
                local_mode = "direct"
            elif result_flag == "H":
                local_mode = "chain"
            tail_mode = ProofLookupPlanResult(M.Tail(plan)())()
            self.result = ProofLookupModeMerge(local_mode, tail_mode)()
        super().__init__(inputs=M.Pair(plan, M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result


class RemoveProofLookupPlanResults(M.Edge):
    def __init__(self, plan):
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            self.result = M.truth_value
        else:
            packet = M.Head(plan)()
            result_path = M.Head(M.Tail(M.Tail(M.Tail(packet)())())())()()
            if os.path.exists(result_path):
                os.remove(result_path)
            self.result = RemoveProofLookupPlanResults(M.Tail(plan)())()
        super().__init__(inputs=M.Pair(plan, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ParallelProofLookupMode(M.Edge):
    def __init__(self, graph_version, goal, assumptions):
        process_text = str(os.getpid())
        worker_count_text = os.environ.get("HYGE_FOREGROUND_WORKERS", "1")
        if GMPLessText(worker_count_text, "1")() is M.truth_value:
            worker_count_text = "1"
        request_path = os.path.join(
            os.path.dirname(__file__), "snapshots",
            "foreground-proof-" + process_text + ".wire",
        )
        request = M.Pair(
            graph_version,
            M.Pair(goal, M.Pair(assumptions, M.EmptyList)),
        )
        with open(request_path, "wb") as request_stream:
            request_stream.write(W.serialize_term(request))
        plan = ProofLookupWorkPlan("0", worker_count_text, request_path)()
        processes = SpawnProofLookupPlan(plan, request_path, process_text)()
        JoinProofLookupProcesses(processes)()
        self.result = ProofLookupPlanResult(plan)()
        if os.path.exists(request_path):
            os.remove(request_path)
        RemoveProofLookupPlanResults(plan)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(goal, M.EmptyList)),
            results=M.Char(self.result),
        )

    def __call__(self):
        return self.result
