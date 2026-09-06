"""[SHARED] process workers: parallel exploration, checked join, serial promotion.

A worker is an OS process plus a snapshot identity plus one obligation.
Workers never write the parent's knowledge store. The coordinator validates
certificates and joins. Adoption-class journal entries queue for the existing
gate; they never install a rule.
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
import subprocess
import sys
import tempfile
import time

from . import labels as L
from . import machine as M


class WorkItem(M.Edge):
    def __init__(self, task_id, parent_id, snapshot_id, obligation, context, budget):
        self.result = M.Pair(
            L.WorkItemLabel,
            M.Pair(
                task_id,
                M.Pair(
                    parent_id,
                    M.Pair(
                        snapshot_id,
                        M.Pair(
                            obligation,
                            M.Pair(context, M.Pair(budget, M.EmptyList)),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(task_id, M.Pair(parent_id, M.Pair(snapshot_id, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Claim(M.Edge):
    def __init__(self, task_id, attempt_id, worker_id):
        self.result = M.Pair(
            L.ClaimLabel,
            M.Pair(task_id, M.Pair(attempt_id, M.Pair(worker_id, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(task_id, M.Pair(attempt_id, M.Pair(worker_id, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WorkerResult(M.Edge):
    def __init__(self, task_id, attempt_id, snapshot_id, outcome, certificate, journal, counters):
        self.result = M.Pair(
            L.WorkerResultLabel,
            M.Pair(
                task_id,
                M.Pair(
                    attempt_id,
                    M.Pair(
                        snapshot_id,
                        M.Pair(
                            outcome,
                            M.Pair(
                                certificate,
                                M.Pair(journal, M.Pair(counters, M.EmptyList)),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(task_id, M.Pair(attempt_id, M.Pair(snapshot_id, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ObservationJournal(M.Edge):
    def __init__(self, entries):
        self.result = M.Pair(L.ObservationJournalLabel, M.Pair(entries, M.EmptyList))
        super().__init__(inputs=M.Pair(entries, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalJournal(M.Edge):
    def __init__(self, entries):
        self.result = M.Pair(L.ProposalJournalLabel, M.Pair(entries, M.EmptyList))
        super().__init__(inputs=M.Pair(entries, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SnapshotIdentity(M.Edge):
    def __init__(self, path):
        digest = M.EmptyList
        if os.path.isfile(path):
            hasher = hashlib.sha256()
            handle = open(path, "rb")
            block = handle.read(65536)
            while block != b"":
                hasher.update(block)
                block = handle.read(65536)
            handle.close()
            digest = M.Char(hasher.hexdigest())
        self.result = digest
        super().__init__(inputs=M.Pair(M.Char(path), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SnapshotFormatOk(M.Edge):
    def __init__(self, path):
        self.result = M.false_value
        if os.path.isfile(path):
            handle = open(path, "r", encoding="utf-8")
            payload = json.load(handle)
            handle.close()
            header = payload["header"]
            if header["format"] == "hyge-proof-kernel":
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(M.Char(path), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DischargeCharObligation(M.Edge):
    def __init__(self, left_text, right_text):
        left = M.Char(left_text)
        right = M.Char(right_text)
        if M.Compare(left, right)() is M.truth_value:
            self.result = L.ObligationDischargedLabel
        else:
            self.result = L.ObligationOpenLabel
        super().__init__(
            inputs=M.Pair(left, M.Pair(right, M.EmptyList)),
            results=M.Pair(self.result, M.EmptyList),
        )

    def __call__(self):
        return self.result


class WorkerResultOutcome(M.Edge):
    def __init__(self, result_term):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(result_term)())())())(),
        )()
        super().__init__(inputs=M.Pair(result_term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class WorkerResultAttempt(M.Edge):
    def __init__(self, result_term):
        self.result = M.Head(M.Tail(M.Tail(result_term)())())()
        super().__init__(inputs=M.Pair(result_term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AndJoin(M.Edge):
    def __init__(self, left_outcome, right_outcome):
        self.result = M.false_value
        if M.IdentityCompare(left_outcome, L.ObligationDischargedLabel)() is M.truth_value:
            if M.IdentityCompare(right_outcome, L.ObligationDischargedLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(
            inputs=M.Pair(left_outcome, M.Pair(right_outcome, M.EmptyList)),
            results=M.Pair(self.result, M.EmptyList),
        )

    def __call__(self):
        return self.result


class OrJoin(M.Edge):
    def __init__(self, left_outcome, right_outcome):
        self.result = M.false_value
        if M.IdentityCompare(left_outcome, L.ObligationDischargedLabel)() is M.truth_value:
            self.result = M.truth_value
        elif M.IdentityCompare(right_outcome, L.ObligationDischargedLabel)() is M.truth_value:
            self.result = M.truth_value
        super().__init__(
            inputs=M.Pair(left_outcome, M.Pair(right_outcome, M.EmptyList)),
            results=M.Pair(self.result, M.EmptyList),
        )

    def __call__(self):
        return self.result


class SerialAdmitProposal(M.Edge):
    def __init__(self, admitted, proposal):
        self.result = admitted
        if M.IdentityCompare(M.Head(proposal)(), L.ProposalJournalLabel)() is M.truth_value:
            self.result = M.Pair(proposal, admitted)
        super().__init__(
            inputs=M.Pair(admitted, M.Pair(proposal, M.EmptyList)),
            results=M.Pair(self.result, M.EmptyList),
        )

    def __call__(self):
        return self.result


def _worker_process_main(output_path, snapshot_path, expected_digest, left_text, right_text, hold_seconds, crash):
    started = time.monotonic()
    outcome_name = "ExecutionFailure"
    try:
        if crash:
            raise RuntimeError("worker crash requested")
        if hold_seconds > 0:
            time.sleep(hold_seconds)
        hasher = hashlib.sha256()
        handle = open(snapshot_path, "rb")
        block = handle.read(65536)
        while block != b"":
            hasher.update(block)
            block = handle.read(65536)
        handle.close()
        digest = hasher.hexdigest()
        if digest != expected_digest:
            outcome_name = "ExecutionFailure"
        else:
            left = M.Char(left_text)
            right = M.Char(right_text)
            if M.Compare(left, right)() is M.truth_value:
                outcome_name = "ObligationDischarged"
            else:
                outcome_name = "ObligationOpen"
        payload = {
            "outcome": outcome_name,
            "digest": digest,
            "pid": os.getpid(),
            "started": started,
            "finished": time.monotonic(),
        }
        temp_path = output_path + ".tmp"
        handle = open(temp_path, "wb")
        pickle.dump(payload, handle)
        handle.close()
        os.replace(temp_path, output_path)
    except Exception:
        payload = {
            "outcome": "ExecutionFailure",
            "digest": "",
            "pid": os.getpid(),
            "started": started,
            "finished": time.monotonic(),
        }
        temp_path = output_path + ".tmp"
        handle = open(temp_path, "wb")
        pickle.dump(payload, handle)
        handle.close()
        os.replace(temp_path, output_path)


class LaunchTwoWorkers(M.Edge):
    def __init__(
        self,
        snapshot_path,
        left_a,
        right_a,
        left_b,
        right_b,
        hold_seconds,
        crash_a,
        crash_b,
    ):
        digest_term = SnapshotIdentity(snapshot_path)()
        digest_text = digest_term.symbol
        work_dir = tempfile.mkdtemp(prefix="hyge-shared-workers-")
        path_a = os.path.join(work_dir, "a.pickle")
        path_b = os.path.join(work_dir, "b.pickle")
        crash_a_flag = "0"
        crash_b_flag = "0"
        if crash_a:
            crash_a_flag = "1"
        if crash_b:
            crash_b_flag = "1"
        child_env = os.environ.copy()
        existing = ""
        if "PYTHONPATH" in child_env:
            existing = child_env["PYTHONPATH"]
        package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if existing == "":
            child_env["PYTHONPATH"] = package_root
        else:
            child_env["PYTHONPATH"] = package_root + os.pathsep + existing
        process_a = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "cat_theo_machine.workers",
                path_a,
                snapshot_path,
                digest_text,
                left_a,
                right_a,
                str(hold_seconds),
                crash_a_flag,
            ],
            env=child_env,
        )
        process_b = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "cat_theo_machine.workers",
                path_b,
                snapshot_path,
                digest_text,
                left_b,
                right_b,
                str(hold_seconds),
                crash_b_flag,
            ],
            env=child_env,
        )
        pid_a = process_a.pid
        pid_b = process_b.pid
        process_a.wait()
        process_b.wait()
        payload_a = {"outcome": "ExecutionFailure", "digest": "", "pid": pid_a, "started": 0, "finished": 0}
        payload_b = {"outcome": "ExecutionFailure", "digest": "", "pid": pid_b, "started": 0, "finished": 0}
        if os.path.isfile(path_a):
            handle = open(path_a, "rb")
            payload_a = pickle.load(handle)
            handle.close()
        if os.path.isfile(path_b):
            handle = open(path_b, "rb")
            payload_b = pickle.load(handle)
            handle.close()
        try:
            os.remove(path_a)
        except OSError:
            pass
        try:
            os.remove(path_b)
        except OSError:
            pass
        try:
            os.rmdir(work_dir)
        except OSError:
            pass
        self.payload_a = payload_a
        self.payload_b = payload_b
        self.pid_a = pid_a
        self.pid_b = pid_b
        self.digest_text = digest_text
        self.result = M.Pair(
            Claim(M.Char("task"), M.Char("attempt-a"), M.Char(str(pid_a)))(),
            M.Pair(Claim(M.Char("task"), M.Char("attempt-b"), M.Char(str(pid_b)))(), M.EmptyList),
        )
        super().__init__(inputs=M.Pair(M.Char(snapshot_path), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomeFromName(M.Edge):
    def __init__(self, name):
        self.result = L.ExecutionFailureLabel
        if name == "ObligationDischarged":
            self.result = L.ObligationDischargedLabel
        elif name == "ObligationOpen":
            self.result = L.ObligationOpenLabel
        super().__init__(inputs=M.Pair(M.Char(name), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class WriteMinimalSnapshot(M.Edge):
    def __init__(self, path):
        payload = {
            "header": {"format": "hyge-proof-kernel", "version": 4, "protocol_version": 3},
            "roots": {},
            "symbols": {},
            "objects": [],
        }
        handle = open(path, "w", encoding="utf-8")
        json.dump(payload, handle)
        handle.close()
        self.result = M.Char(path)
        super().__init__(inputs=M.Pair(M.Char(path), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


if __name__ == "__main__":
    output_path = sys.argv[1]
    snapshot_path = sys.argv[2]
    expected_digest = sys.argv[3]
    left_text = sys.argv[4]
    right_text = sys.argv[5]
    hold_seconds = float(sys.argv[6])
    crash = sys.argv[7] == "1"
    _worker_process_main(
        output_path,
        snapshot_path,
        expected_digest,
        left_text,
        right_text,
        hold_seconds,
        crash,
    )
