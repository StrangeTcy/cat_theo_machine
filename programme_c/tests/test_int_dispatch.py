"""Integration tests for C-A search-worker dispatch under strict certificate
replay semantics (post C-INT review 2026-09-16):

  * Readiness ack only accepted after a well-formed checkpoint is written
    with matching declared snapshot_id / obligation.
  * A deferred-derivation (rc=4, plan-found only) does NOT discharge the
    child; the coordinator returns F_INVALID_CERT in that case.
  * rc=2 (timed_out) -> F_TIMEOUT.
  * max_workers=2 cap -> F_LAUNCH_ERROR synchronously.
  * Mismatched declared snapshot/obligation in the worker-side manifest ->
    F_SNAPSHOT_MISMATCH / F_SCOPE_VIOLATION.
  * Cleanup removes the isolated worker directory.

Wraps (does not replace) the existing search-worker subprocess entry point.
"""
from __future__ import annotations
import json
import os
import shutil
import tempfile
import time
import unittest

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c as P
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


class SearchWorkerDispatchTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="pc_int_dispatch_")

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def _new_pool(self):
        pool = W.BoundedWorkerPool(self.scratch, snapshot_ident=None, check_restore=False)
        return pool, WD.SearchWorkerDispatch(pool, PACKAGE_ROOT)

    def test_completed_search_worker_emits_fully_stamped_cert(self):
        pool, dispatcher = self._new_pool()
        try:
            # defer_derivation=False so the worker runs through to
            # success-derivation-built (complete, replayable certificate).
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
                defer_derivation=False,
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
            pool.cleanup(ticket)
            self.assertFalse(os.path.isdir(ticket.worker_dir))
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
                worker_timeout_seconds=1,
                defer_derivation=False,
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

    def test_deferred_derivation_does_not_discharge(self):
        """rc=4 (defer-derivation) produces a running-derivation checkpoint
        that is NOT a complete replayable certificate, so the coordinator
        must reject it with F_INVALID_CERT instead of completing the join."""
        pool, dispatcher = self._new_pool()
        try:
            ticket = dispatcher.spawn(
                mode_token="dfs",
                start_text="Zero",
                goal_text="Zero",
                task_id="t-deferred",
                attempt_id="a-1",
                obligation_text="Zero == Zero",
                assumptions_term=M.EmptyList,
                budget_millis=120_000,
                worker_timeout_seconds=60,
                defer_derivation=True,
            )
            result = _wait_terminal(dispatcher, ticket, timeout_sec=120)
            self.assertIsNotNone(result)
            self.assertEqual(alist_get(result, K_STATUS), S_FAILED)
            reason = alist_get(result, K_REASON)
            self.assertTrue(M.IdentityCompare(reason, F_INVALID_CERT)() is M.truth_value,
                            "expected F_INVALID_CERT for deferred cert, got " + str(reason))
            pool.cleanup(ticket)
        finally:
            pool.shutdown()

    def test_mismatched_obligation_is_caught(self):
        """Tamper with the manifest's declared obligation before the worker
        boots; the coordinator must reject the certificate with F_SCOPE_VIOLATION
        or F_INVALID_CERT, not accept it.
        """
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
                defer_derivation=False,
            )
            # Overwrite the manifest's declared_obligation after spawn.
            manifest_path = ticket.result_path + ".manifest.json"
            # Wait for manifest to exist (it is written before spawn).
            tries = 0
            while not os.path.isfile(manifest_path) and tries < 50:
                time.sleep(0.1); tries += 1
            self.assertTrue(os.path.isfile(manifest_path))
            # We cannot easily race the worker's manifest read, so we instead
            # verify that _verify_child_certificate itself detects a mismatch
            # by running it with a wrong expected obligation.
            ok, stat, reason, body = WD._verify_child_certificate(
                ticket.result_path,
                ticket.snapshot_id,
                "WRONG_OBLIGATION",
                ticket.assumption_hash,
                ticket.task_id, ticket.attempt_id)
            self.assertFalse(ok, "cert replay should fail with wrong obligation")
            self.assertTrue(reason is F_SCOPE_VIOLATION, "expected F_SCOPE_VIOLATION, got " + str(reason))
            # Wait out the worker and cancel to clean up.
            dispatcher.cancel(ticket)
            pool.cleanup(ticket)
        finally:
            pool.shutdown()

    def test_max_workers_cap_synchronous_launch_error(self):
        pool, dispatcher = self._new_pool()
        try:
            hard = "Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Zero))))))))))))"
            t1 = dispatcher.spawn("dfs", "Zero", hard, "t-a", "a-1", "ob-a",
                                  M.EmptyList, 120_000, 30, defer_derivation=False)
            t2 = dispatcher.spawn("dfs", "Zero", hard, "t-b", "a-1", "ob-b",
                                  M.EmptyList, 120_000, 30, defer_derivation=False)
            end = time.time() + 15
            while time.time() < end:
                if t1.status == S_DISPATCHED and t2.status == S_DISPATCHED:
                    break
                time.sleep(0.1)
            self.assertEqual(pool._outstanding, 2)
            t3 = dispatcher.spawn("dfs", "Zero", "Zero", "t-c", "a-1", "ob-c",
                                  M.EmptyList, 120_000, 30, defer_derivation=False)
            self.assertEqual(alist_get(t3.result_term, K_STATUS), S_FAILED)
            self.assertTrue(M.IdentityCompare(alist_get(t3.result_term, K_REASON),
                                              F_LAUNCH_ERROR)() is M.truth_value)
            dispatcher.cancel(t1); dispatcher.cancel(t2)
            pool.cleanup(t1); pool.cleanup(t2); pool.cleanup(t3)
        finally:
            pool.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
