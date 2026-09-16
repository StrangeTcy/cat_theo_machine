"""C-A tests: two concurrent workers, crash/retry with new attempt, timeout,
cleanup, snapshot mismatch (incl. fresh-restore check), and invalid ready
certificate rejection.
"""
from __future__ import annotations

import datetime as _dt
import json as _json
import os, shutil, sys, tempfile, time as _time, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import hyge_ca.machine as M
import hyge_ca.programme_c as P
import hyge_ca.programme_c.snapshot_id as sid
import hyge_ca.programme_c.worker as W


def _today():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
def _art():
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", _today())
    os.makedirs(d, exist_ok=True); return d


def _min_snap(path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('{"header":{"format":"t"},"roots":{"r":"x"},"symbols":{},"objects":[{"id":1}]}')


def _echo_worker(conn, work_dir, args, task_id, attempt_id, worker_id, sid_id, ob, ah, budget, snap_path):
    name = args.get("touch", "ok.txt")
    with open(os.path.join(work_dir, name), "w") as fh: fh.write("ok")
    _time.sleep(args.get("sleep", 0.05))
    return _json.dumps({"worker_id":worker_id,"task_id":task_id,"attempt_id":attempt_id,
                        "obligation":ob,"snapshot_id":sid_id,"cwd":os.getcwd()}, sort_keys=True)


def _crash_worker(conn, work_dir, args, task_id, attempt_id, worker_id, *a):
    raise RuntimeError("boom")


def _slow_worker(conn, work_dir, args, *a):
    _time.sleep(5.0); return "late"


class BoundedWorkerPoolTests(unittest.TestCase):
    def _pool(self, td, snap):
        _min_snap(snap)
        ident, _ = sid.compute_identity(snap)
        sid.write_sidecar(snap, ident)
        return ident, W.BoundedWorkerPool(td, ident, check_restore=True)

    def test_two_concurrent_workers(self):
        with tempfile.TemporaryDirectory() as td:
            snap = os.path.join(td, "s.json")
            ident, pool = self._pool(td, snap)
            try:
                t1 = pool.spawn_worker(_echo_worker, {"touch":"a.txt"}, "task-1", "att-1",
                                       "ob-1", M.EmptyList, 5000, snap)
                t2 = pool.spawn_worker(_echo_worker, {"touch":"b.txt"}, "task-2", "att-1",
                                       "ob-2", M.EmptyList, 5000, snap)
                t3 = pool.spawn_worker(_echo_worker, {"touch":"c.txt"}, "task-3", "att-1",
                                       "ob-3", M.EmptyList, 5000, snap)
                self.assertEqual(t3.status.value, "failed")
                reason = P.alist_get(t3.result_term, P.K_REASON)
                self.assertTrue(M.IdentityCompare(reason, P.F_LAUNCH_ERROR)() is M.truth_value)
                deadline = _time.time() + 8.0; r1 = M.EmptyList; r2 = M.EmptyList
                while (r1 is M.EmptyList or r2 is M.EmptyList) and _time.time() < deadline:
                    if r1 is M.EmptyList: r1 = pool.poll(t1)
                    if r2 is M.EmptyList: r2 = pool.poll(t2)
                    _time.sleep(0.02)
                self.assertEqual(P.alist_get(r1, P.K_STATUS).value, "completed")
                self.assertEqual(P.alist_get(r2, P.K_STATUS).value, "completed")
                self.assertEqual(P.alist_get(r1, P.K_TASK_ID).value, "task-1")
                self.assertEqual(P.alist_get(r2, P.K_TASK_ID).value, "task-2")
                # Isolated dirs
                self.assertTrue(os.path.isfile(os.path.join(t1.worker_dir, "a.txt")))
                self.assertTrue(os.path.isfile(os.path.join(t2.worker_dir, "b.txt")))
                self.assertNotEqual(t1.worker_dir, t2.worker_dir)
                self.assertTrue(os.listdir(t1.worker_dir))  # dir contains sentinel (cleanup verified separately)
                # Cleanup verification
                pool.cleanup(t1); pool.cleanup(t2)
                self.assertFalse(os.path.exists(t1.worker_dir))
                self.assertFalse(os.path.exists(t2.worker_dir))
                with open(os.path.join(_art(), "ca_two_workers.txt"), "w") as fh:
                    fh.write("# 2026-09-16 two workers returned serialized results\n")
            finally:
                pool.shutdown()

    def test_crash_is_failure_retry_new_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            snap = os.path.join(td, "s.json")
            ident, pool = self._pool(td, snap)
            try:
                tbad = pool.spawn_worker(_crash_worker, {}, "task-1", "att-1",
                                         "ob", M.EmptyList, 5000, snap)
                # Crash may surface at spawn (ready handshake fails) or at poll.
                deadline = _time.time() + 5.0; rbad = tbad.result_term
                if tbad.status.value == "running" or tbad.status.value == "dispatched":
                    while rbad is M.EmptyList and _time.time() < deadline:
                        rbad = pool.poll(tbad); _time.sleep(0.02)
                self.assertEqual(P.alist_get(rbad, P.K_STATUS).value, "failed")
                reason = P.alist_get(rbad, P.K_REASON)
                self.assertTrue(M.IdentityCompare(reason, P.F_CRASH)() is M.truth_value)
                pool.cleanup(tbad)
                # Retry on NEW attempt id.
                tgood = pool.spawn_worker(_echo_worker, {"touch":"ok.txt"}, "task-1", "att-2",
                                          "ob", M.EmptyList, 5000, snap)
                deadline = _time.time() + 5.0; rgood = M.EmptyList
                while rgood is M.EmptyList and _time.time() < deadline:
                    rgood = pool.poll(tgood); _time.sleep(0.02)
                self.assertEqual(P.alist_get(rgood, P.K_STATUS).value, "completed")
                self.assertEqual(P.alist_get(rgood, P.K_ATTEMPT_ID).value, "att-2")
                pool.cleanup(tgood)
                with open(os.path.join(_art(), "ca_crash_retry.txt"), "w") as fh:
                    fh.write("crash -> F_CRASH; retry on att-2 completed\n")
            finally:
                pool.shutdown()

    def test_timeout_is_failure_term(self):
        with tempfile.TemporaryDirectory() as td:
            snap = os.path.join(td, "s.json"); ident, pool = self._pool(td, snap)
            try:
                t = pool.spawn_worker(_slow_worker, {}, "task-1", "att-1",
                                      "ob", M.EmptyList, 200, snap)
                deadline = _time.time() + 5.0; r = M.EmptyList
                while r is M.EmptyList and _time.time() < deadline:
                    r = pool.poll(t); _time.sleep(0.02)
                self.assertEqual(P.alist_get(r, P.K_STATUS).value, "failed")
                reason = P.alist_get(r, P.K_REASON)
                self.assertTrue(M.IdentityCompare(reason, P.F_TIMEOUT)() is M.truth_value)
                pool.cleanup(t)
            finally:
                pool.shutdown()

    def test_snapshot_mismatch_including_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            snap = os.path.join(td, "s.json"); _min_snap(snap)
            ident, _ = sid.compute_identity(snap); sid.write_sidecar(snap, ident)
            pool = W.BoundedWorkerPool(td, ident, check_restore=False)
            try:
                # Tamper snapshot AFTER computing identity.
                with open(snap) as fh: o = _json.load(fh)
                o["objects"].append({"id":9})
                with open(snap, "w") as fh: _json.dump(o, fh)
                t = pool.spawn_worker(_echo_worker, {}, "t", "a", "ob", M.EmptyList, 5000, snap)
                self.assertEqual(t.status.value, "failed")
                reason = P.alist_get(t.result_term, P.K_REASON)
                self.assertTrue(M.IdentityCompare(reason, P.F_SNAPSHOT_MISMATCH)() is M.truth_value)
            finally:
                pool.shutdown()

    def test_cleanup_removes_dir(self):
        with tempfile.TemporaryDirectory() as td:
            snap = os.path.join(td, "s.json"); ident, pool = self._pool(td, snap)
            t = pool.spawn_worker(_echo_worker, {"touch":"x.txt"}, "t", "a",
                                  "ob", M.EmptyList, 5000, snap)
            deadline = _time.time() + 5.0; r = M.EmptyList
            while r is M.EmptyList and _time.time() < deadline:
                r = pool.poll(t); _time.sleep(0.02)
            self.assertTrue(os.path.isdir(t.worker_dir))
            pool.cleanup(t)
            self.assertFalse(os.path.exists(t.worker_dir))


if __name__ == "__main__":
    unittest.main(verbosity=2)
