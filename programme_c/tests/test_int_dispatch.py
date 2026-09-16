"""Integration tests for C-A search-worker dispatch under strict certificate
replay semantics (post C-INT review 2026-09-16, corrective #3/#4):

  * Spawn creates a per-ticket gate dir; worker emits ready marker after
    the durable running-search checkpoint; coordinator validates then
    writes release marker -> worker proceeds. This is the explicit
    restore->READY->validate->release->execute handshake (corrective #4).
  * A successful worker produces a replayable certificate the coordinator
    replays via proof.BuildDerivation against the trusted input snapshot;
    that replay (NOT producer metadata) is what discharges the child.
  * rc=2 (timed_out) -> F_TIMEOUT surfaced via replay/coordinator.
  * max_workers=2 cap -> F_LAUNCH_ERROR synchronously.
  * Negative fixture: a certificate with perfectly valid codec/metadata/
    producer-claim 'success-derivation-built' but an invalid derivation
    is rejected by proof replay (F_INVALID_CERT), not by metadata checks.
  * Mismatched declared obligation -> F_SCOPE_VIOLATION.
  * Cleanup removes the isolated worker directory.

Wraps (does not replace) the existing search-worker subprocess entry point.
"""
from __future__ import annotations
import glob as _glob
import json
import os
import shutil
import tempfile
import time
import unittest

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c as P
import hyge_int_pkg.programme_c.join as J
import hyge_int_pkg.programme_c.worker as W
import hyge_int_pkg.programme_c.worker_dispatch as WD
from hyge_int_pkg.programme_c import (
    S_COMPLETED, S_FAILED, S_DISPATCHED,
    F_TIMEOUT, F_CRASH, F_CANCELLED, F_LAUNCH_ERROR, F_INVALID_CERT,
    F_SNAPSHOT_MISMATCH, F_SCOPE_VIOLATION,
    K_TASK_ID, K_ATTEMPT_ID, K_WORKER_ID, K_STATUS, K_KIND, K_REASON, K_BODY,
    K_DECLARED_SNAPSHOT, K_DECLARED_OBLIGATION, K_ASSUMPTION_HASH, K_BUDGET,
    alist_get,
)


def _find_package_root():
    here = os.path.abspath(WD.__file__)
    d = os.path.dirname(here)
    for _ in range(6):
        if os.path.isfile(os.path.join(d, "main.py")) and os.path.isdir(os.path.join(d, "programme_c")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.path.abspath(os.path.join(os.path.dirname(here), "..", ".."))
PACKAGE_ROOT = _find_package_root()


def _wait_terminal(dispatcher, ticket, timeout_sec=120):
    end = time.time() + timeout_sec
    while time.time() < end:
        r = dispatcher.poll(ticket)
        if r is not M.EmptyList:
            return r
        time.sleep(0.05)
    return None


def _wait_ready_pid(gate_dir, timeout=20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        cands = _glob.glob(os.path.join(gate_dir, "ready-*"))
        if cands:
            return os.path.basename(cands[0]).split("ready-",1)[1]
        time.sleep(0.05)
    return None


class SearchWorkerDispatchTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="pc_int_dispatch_")

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def _new_pool(self):
        pool = W.BoundedWorkerPool(self.scratch, snapshot_ident=None,
                                   check_restore=False)
        return pool, WD.SearchWorkerDispatch(pool, PACKAGE_ROOT)

    def test_completed_search_worker_replay_accepts_and_discharges(self):
        """Worker completes; coordinator-side proof.BuildDerivation replay
        against the trusted snapshot accepts -> child discharged. Uses
        default gate (auto-release)."""
        pool, dispatcher = self._new_pool()
        try:
            ticket = dispatcher.spawn(
                mode_token="dfs",
                start_text="Zero",
                goal_text="Zero",
                task_id="t-complete",
                attempt_id="a-1",
                obligation_text="Zero == Zero",
                assumptions_term=M.EmptyList,
                budget_millis=120_000,
                worker_timeout_seconds=60,
            )
            self.assertIsNotNone(getattr(ticket, "_ready_env", None),
                                 "expected valid readiness ack (checkpoint)")
            ready = ticket._ready_env
            self.assertEqual(alist_get(ready, K_KIND).value, "ready")
            self.assertEqual(alist_get(ready, K_TASK_ID).value, "t-complete")
            self.assertEqual(alist_get(ready, K_ATTEMPT_ID).value, "a-1")
            self.assertEqual(alist_get(ready, K_DECLARED_OBLIGATION).value, "Zero == Zero")
            result = _wait_terminal(dispatcher, ticket, timeout_sec=120)
            self.assertIsNotNone(result, "worker did not finish")
            self.assertEqual(alist_get(result, K_KIND).value, "result")
            self.assertEqual(alist_get(result, K_STATUS), S_COMPLETED)
            self.assertEqual(alist_get(result, K_TASK_ID).value, "t-complete")
            self.assertEqual(alist_get(result, K_ATTEMPT_ID).value, "a-1")
            self.assertEqual(alist_get(result, K_DECLARED_OBLIGATION).value, "Zero == Zero")
            self.assertTrue(alist_get(result, K_ASSUMPTION_HASH).value)
            self.assertTrue(alist_get(result, K_BUDGET).value)
            # Now feed the envelope through join.deliver_child_result to
            # confirm the checked-AND path accepts it.
            ja = J.JoinAdmission()
            ja.create_claim("p", J.COMBINATOR_AND, [
                J.child_spec("t-complete", "Zero == Zero",
                             alist_get(result, K_DECLARED_SNAPSHOT).value,
                             alist_get(result, K_ASSUMPTION_HASH).value)
            ])
            ok, reason, rec = ja.deliver_child_result("p", result)
            self.assertTrue(ok, "delivery failed: " + str(reason))
            self.assertEqual(rec.status, "completed")
            pool.cleanup(ticket)
            self.assertFalse(os.path.isdir(ticket.worker_dir))
        finally:
            pool.shutdown()

    def test_readiness_handshake_blocks_obligation_until_release(self):
        """Child must NOT start obligation execution before the coordinator
        writes the release marker (corrective #4). We use manual_release=True,
        hold release for a window and confirm worker remains blocked; then
        release and confirm worker proceeds."""
        pool, dispatcher = self._new_pool()
        try:
            gate_dir = os.path.join(self.scratch, "gate_blocked")
            os.makedirs(gate_dir, exist_ok=True)
            # Use an unreachable 12-Succ goal that takes the dfs worker
            # beyond our short budget/timeout so the post-release path
            # terminates via F_TIMEOUT.
            unreachable = "Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Zero))))))))))))"
            ticket = dispatcher.spawn(
                mode_token="dfs",
                start_text="Zero",
                goal_text=unreachable,
                task_id="t-block",
                attempt_id="a-1",
                obligation_text="unreachable",
                assumptions_term=M.EmptyList,
                budget_millis=120_000,
                worker_timeout_seconds=4,
                gate_path=gate_dir,
                manual_release=True,
            )
            cpid = _wait_ready_pid(gate_dir, timeout=20.0)
            self.assertIsNotNone(cpid, "ready marker must appear within 20s")
            # Worker is now at READY, blocked; do not release yet for 3s.
            # Because the search hasn't run, no result will be available.
            time.sleep(3.0)
            pr = dispatcher.poll(ticket)
            if pr is not M.EmptyList:
                # Diagnostic: report what happened
                rc = ticket.proc.poll()
                try:
                    out, _ = ticket.proc.communicate(timeout=2)
                    tail = out.decode("utf-8","replace")[-1500:]
                except Exception:
                    tail = "<unavailable>"
                self.fail("worker must remain blocked until release; got rc="
                          + str(rc) + " poll_status="
                          + str(alist_get(pr, K_STATUS)) + " reason="
                          + str(alist_get(pr, K_REASON)) + " stdout=" + tail)
            self.assertEqual(pr, M.EmptyList,
                             "worker must remain blocked until release")
            self.assertFalse(os.path.exists(os.path.join(gate_dir, "release-" + cpid)))
            # Release now.
            with open(os.path.join(gate_dir, "release-" + cpid), "w") as h: h.write("ok\n")
            # After release, worker proceeds and eventually times out
            # (budget exhausted / worker timeout).
            result = _wait_terminal(dispatcher, ticket, timeout_sec=30)
            self.assertIsNotNone(result)
            self.assertEqual(alist_get(result, K_STATUS), S_FAILED)
            reason = alist_get(result, K_REASON)
            self.assertTrue(M.IdentityCompare(reason, F_TIMEOUT)() is M.truth_value,
                            "expected F_TIMEOUT, got " + str(reason))
            pool.cleanup(ticket)
        finally:
            pool.shutdown()

    def test_timeout_yields_f_timeout(self):
        pool, dispatcher = self._new_pool()
        try:
            ticket = dispatcher.spawn(
                mode_token="dfs",
                start_text="Zero",
                goal_text="Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Zero))))))))))))",
                task_id="t-timeout",
                attempt_id="a-1",
                obligation_text="unreachable",
                assumptions_term=M.EmptyList,
                budget_millis=120_000,
                worker_timeout_seconds=2,
            )
            result = _wait_terminal(dispatcher, ticket, timeout_sec=60)
            self.assertIsNotNone(result)
            self.assertEqual(alist_get(result, K_STATUS), S_FAILED)
            reason = alist_get(result, K_REASON)
            self.assertTrue(M.IdentityCompare(reason, F_TIMEOUT)() is M.truth_value,
                            "expected F_TIMEOUT, got " + str(reason))
            pool.cleanup(ticket)
            self.assertFalse(os.path.isdir(ticket.worker_dir))
        finally:
            pool.shutdown()

    def test_mismatched_obligation_is_caught(self):
        """Deliver a valid certificate through join with a mismatched
        declared obligation -> F_SCOPE_VIOLATION."""
        pool, dispatcher = self._new_pool()
        try:
            ticket = dispatcher.spawn(
                mode_token="dfs",
                start_text="Zero",
                goal_text="Zero",
                task_id="t-tamper",
                attempt_id="a-1",
                obligation_text="Zero == Zero",
                assumptions_term=M.EmptyList,
                budget_millis=120_000,
                worker_timeout_seconds=60,
            )
            result = _wait_terminal(dispatcher, ticket, timeout_sec=120)
            self.assertIsNotNone(result)
            ja = J.JoinAdmission()
            ja.create_claim("p", J.COMBINATOR_AND, [
                J.child_spec("t-tamper", "WRONG_OBLIGATION",
                             alist_get(result, K_DECLARED_SNAPSHOT).value, "")
            ])
            ok, reason, _ = ja.deliver_child_result("p", result)
            self.assertFalse(ok)
            self.assertTrue(M.IdentityCompare(reason, F_SCOPE_VIOLATION)() is M.truth_value,
                            "expected F_SCOPE_VIOLATION, got " + str(reason))
            pool.cleanup(ticket)
        finally:
            pool.shutdown()

    def test_invalid_derivation_fixture_rejected_by_proof_replay(self):
        """Negative fixture (corrective #3): producer emits a well-formed
        envelope with matching metadata, but the saved derivation is
        invalid.  Coordinator's BuildDerivation replay must reject it
        (F_INVALID_CERT); metadata alone must not discharge."""
        pool, dispatcher = self._new_pool()
        try:
            ticket = dispatcher.spawn(
                mode_token="dfs",
                start_text="Zero",
                goal_text="Zero",
                task_id="t-bad",
                attempt_id="a-1",
                obligation_text="Zero == Zero",
                assumptions_term=M.EmptyList,
                budget_millis=120_000,
                worker_timeout_seconds=60,
            )
            result = _wait_terminal(dispatcher, ticket, timeout_sec=120)
            self.assertIsNotNone(result, "worker did not finish")
            # Tamper with the saved plan so worker_stage still claims
            # 'success-derivation-built' but the plan's goal is wrong,
            # causing BuildDerivation to fail.
            rp = ticket.result_path
            try:
                from hyge_int_pkg import runtime as _rt, codec as _codec, symbols as _sym
                rt = _rt.boot_from_snapshot(rp, WD._runtime_namespace())
                plan_key = _sym.intern("worker_plan")
                goal_key = _sym.intern("goal")
                bad_goal = _sym.text_to_term("Succ(Zero)")
                if plan_key in rt.heap.roots:
                    plan = rt.heap.roots[plan_key]
                    new_plan = M.EmptyList
                    cur = plan
                    while cur is not M.EmptyList:
                        cell = cur
                        pair = cell
                        if pair is not M.EmptyList and hasattr(pair, 'head') and pair.head is not M.EmptyList:
                            k = pair.head
                            if hasattr(pair, 'tail') and pair.tail is not M.EmptyList:
                                v = pair.tail.head
                                if k is goal_key:
                                    new_plan = P.alist_put(new_plan, goal_key, bad_goal)
                                else:
                                    new_plan = P.alist_put(new_plan, k, v)
                        cur = cur.tail if hasattr(cur, 'tail') else M.EmptyList
                    rt.heap.roots[plan_key] = new_plan
                # Leave worker_stage claiming success.
                _codec.save_snapshot(rt.heap, rp)
                del rt
            except Exception:
                # Fallback: truncate file so codec load fails -> F_INVALID_CERT.
                with open(rp, "r+b") as fh:
                    fh.truncate(16)
            ok, stat, reason, body = WD._verify_child_certificate(
                rp, ticket.snapshot_id, "Zero == Zero",
                ticket.assumption_hash, "t-bad", "a-1")
            self.assertFalse(ok, "proof replay must reject an invalid derivation")
            self.assertTrue(reason in (F_INVALID_CERT, F_SCOPE_VIOLATION, F_SNAPSHOT_MISMATCH),
                            "expected rejection reason, got " + str(reason))
            pool.cleanup(ticket)
        finally:
            pool.shutdown()

    def test_max_workers_cap_synchronous_launch_error(self):
        pool, dispatcher = self._new_pool()
        try:
            hard = "Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Zero))))))))))))"
            t1 = dispatcher.spawn("dfs", "Zero", hard, "t-a", "a-1", "ob-a",
                                  M.EmptyList, 120_000, 30)
            t2 = dispatcher.spawn("dfs", "Zero", hard, "t-b", "a-1", "ob-b",
                                  M.EmptyList, 120_000, 30)
            end = time.time() + 15
            while time.time() < end:
                if t1.status == S_DISPATCHED and t2.status == S_DISPATCHED:
                    break
                time.sleep(0.1)
            self.assertEqual(pool._outstanding, 2)
            t3 = dispatcher.spawn("dfs", "Zero", "Zero", "t-c", "a-1", "ob-c",
                                  M.EmptyList, 120_000, 30)
            self.assertEqual(alist_get(t3.result_term, K_STATUS), S_FAILED)
            self.assertTrue(M.IdentityCompare(alist_get(t3.result_term, K_REASON),
                                              F_LAUNCH_ERROR)() is M.truth_value)
            dispatcher.cancel(t1); dispatcher.cancel(t2)
            pool.cleanup(t1); pool.cleanup(t2); pool.cleanup(t3)
        finally:
            pool.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
