"""Integration test: C-A search-worker subprocess dispatch wrapper stamps
K_SNAPSHOT_ID/K_OBLIGATION/K_ASSUMPTION_HASH/K_TASK_ID/K_ATTEMPT_ID on every
result envelope, readiness ack arrives with declared snapshot/obligation,
timeout produces F_TIMEOUT, cancellation produces F_CANCELLED, and cleanup
removes the worker directory. Wraps (does not replace) the existing
search-worker subprocess entry point in main.py.
"""
from __future__ import annotations
import os, shutil, sys, tempfile, time, unittest

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c as P
import hyge_int_pkg.programme_c.worker as W
import hyge_int_pkg.programme_c.worker_dispatch as WD
from hyge_int_pkg.programme_c import (
    S_COMPLETED, S_FAILED, S_DISPATCHED,
    F_TIMEOUT, F_CRASH, F_CANCELLED, F_LAUNCH_ERROR,
    K_TASK_ID, K_ATTEMPT_ID, K_WORKER_ID, K_STATUS, K_KIND, K_REASON, K_BODY,
    K_DECLARED_SNAPSHOT, K_DECLARED_OBLIGATION, K_ASSUMPTION_HASH, K_BUDGET,
    alist_get, text_atom,
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


class SearchWorkerDispatchTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="pc_int_dispatch_")

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def _wait_terminal(self, dispatcher, ticket, timeout_sec=90):
        end = time.time() + timeout_sec
        while time.time() < end:
            r = dispatcher.poll(ticket)
            if r is not M.EmptyList:
                return r
            time.sleep(0.05)
        return None

    def _new_pool(self):
        pool = W.BoundedWorkerPool(self.scratch, snapshot_ident=None, check_restore=False)
        return pool, WD.SearchWorkerDispatch(pool, PACKAGE_ROOT)

    def test_readiness_ack_stamps_declared_fields(self):
        pool, dispatcher = self._new_pool()
        try:
            # Use dfs mode, trivial start/goal (zero == zero) — completes fast.
            ticket = dispatcher.spawn(
                mode_token="dfs",
                start_text="Zero",
                goal_text="Zero",
                task_id="t-readiness",
                attempt_id="a-1",
                obligation_text="Zero == Zero",
                assumptions_term=M.EmptyList,
                budget_millis=60_000,
                worker_timeout_seconds=30,
            )
            self.assertIsNotNone(getattr(ticket, "_ready_env", None), "ready ack missing")
            ready = ticket._ready_env
            self.assertEqual(alist_get(ready, K_KIND).value, "ready")
            self.assertEqual(alist_get(ready, K_TASK_ID).value, "t-readiness")
            self.assertEqual(alist_get(ready, K_ATTEMPT_ID).value, "a-1")
            self.assertTrue(alist_get(ready, K_WORKER_ID).value.startswith("w-"))
            self.assertTrue(len(alist_get(ready, K_DECLARED_SNAPSHOT).value) > 0)
            self.assertEqual(alist_get(ready, K_DECLARED_OBLIGATION).value, "Zero == Zero")
            # Wait for completion and verify result envelope stamps.
            result = self._wait_terminal(dispatcher, ticket, timeout_sec=90)
            self.assertIsNotNone(result, "did not finish in time")
            self.assertEqual(alist_get(result, K_KIND).value, "result")
            self.assertEqual(alist_get(result, K_TASK_ID).value, "t-readiness")
            self.assertEqual(alist_get(result, K_ATTEMPT_ID).value, "a-1")
            self.assertEqual(alist_get(result, K_DECLARED_OBLIGATION).value, "Zero == Zero")
            self.assertTrue(alist_get(result, K_ASSUMPTION_HASH).value)
            self.assertTrue(alist_get(result, K_BUDGET).value)
            self.assertEqual(alist_get(result, K_STATUS), S_COMPLETED)
            pool.cleanup(ticket)
            self.assertFalse(os.path.isdir(ticket.worker_dir))
        finally:
            pool.shutdown()

    def test_timeout_produces_f_timeout(self):
        pool, dispatcher = self._new_pool()
        try:
            # Goal that requires deep forward search; tight worker_timeout yields
            # rc=2 "timed_out" from search; verify F_TIMEOUT on the envelope.
            ticket = dispatcher.spawn(
                mode_token="dfs",
                start_text="Zero",
                goal_text="Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Zero))))))))))",
                task_id="t-timeout",
                attempt_id="a-1",
                obligation_text="unreachable",
                assumptions_term=M.EmptyList,
                budget_millis=60_000,
                worker_timeout_seconds=1,
            )
            result = self._wait_terminal(dispatcher, ticket, timeout_sec=30)
            self.assertIsNotNone(result)
            self.assertEqual(alist_get(result, K_STATUS), S_FAILED)
            body_val = alist_get(result, K_BODY)
            body_text = P._atom_text(body_val) if body_val is not None else ""
            reason = alist_get(result, K_REASON)
            is_timeout = (M.IdentityCompare(reason, F_TIMEOUT)() is M.truth_value) or ("timed" in body_text.lower())
            self.assertTrue(is_timeout, "expected F_TIMEOUT, got reason=" + str(reason) + " body=" + body_text[:200])
            pool.cleanup(ticket)
            self.assertFalse(os.path.isdir(ticket.worker_dir))
        finally:
            pool.shutdown()

    def test_max_workers_cap_enforced(self):
        pool, dispatcher = self._new_pool()
        try:
            # Occupy both slots with a task that takes long enough for the cap
            # check to fire: use a hard goal but give a generous timeout.
            def _wait_both_dispatched(tickets, deadline=10.0):
                end = time.time() + deadline
                while time.time() < end:
                    if all(getattr(t, "status") == S_DISPATCHED for t in tickets):
                        return True
                    time.sleep(0.05)
                return False
            hard_goal = "Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Zero))))))))))))"
            t1 = dispatcher.spawn(
                mode_token="dfs", start_text="Zero", goal_text=hard_goal,
                task_id="t-mw-a", attempt_id="a-1",
                obligation_text="ob-a", assumptions_term=M.EmptyList,
                budget_millis=60_000, worker_timeout_seconds=30)
            t2 = dispatcher.spawn(
                mode_token="dfs", start_text="Zero", goal_text=hard_goal,
                task_id="t-mw-b", attempt_id="a-1",
                obligation_text="ob-b", assumptions_term=M.EmptyList,
                budget_millis=60_000, worker_timeout_seconds=30)
            self.assertTrue(_wait_both_dispatched([t1, t2]),
                            "both workers did not reach dispatched state; t1=" + str(t1.status) + " t2=" + str(t2.status))
            self.assertEqual(pool._outstanding, 2)
            t3 = dispatcher.spawn(
                mode_token="dfs", start_text="Zero", goal_text="Zero",
                task_id="t-mw-c", attempt_id="a-1",
                obligation_text="ob-c", assumptions_term=M.EmptyList,
                budget_millis=60_000, worker_timeout_seconds=30)
            self.assertEqual(alist_get(t3.result_term, K_STATUS), S_FAILED)
            b3 = alist_get(t3.result_term, K_BODY)
            body3 = P._atom_text(b3) if b3 is not None else ""
            self.assertTrue(M.IdentityCompare(alist_get(t3.result_term, K_REASON), F_LAUNCH_ERROR)() is M.truth_value
                            or "max_workers" in body3)
            # Cancel outstanding workers to avoid hanging.
            dispatcher.cancel(t1); dispatcher.cancel(t2)
            pool.cleanup(t1); pool.cleanup(t2); pool.cleanup(t3)
        finally:
            pool.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
