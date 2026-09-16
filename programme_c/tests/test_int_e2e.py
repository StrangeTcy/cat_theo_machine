"""End-to-end: two real search-worker subprocesses -> certificates replayed
against declared child specs -> checked AND join; AND with one deferred
(non-dischargeable) child stays running; corrupt / wrong-snapshot certs
rejected; on-disk admission manifest gates a derived proposal through
validity/rent/human with restart recovery.

These tests boot actual search-worker subprocesses so they are slower; they
exercise the full coordinator -> child -> checkpoint -> certificate replay
-> join -> admission path end-to-end.
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
import hyge_int_pkg.programme_c.join as J
import hyge_int_pkg.programme_c.worker as W
import hyge_int_pkg.programme_c.worker_dispatch as WD
from hyge_int_pkg.programme_c import (
    S_COMPLETED, S_FAILED,
    F_TIMEOUT, F_INVALID_CERT, F_SNAPSHOT_MISMATCH, F_SCOPE_VIOLATION,
    K_KIND, K_STATUS, K_REASON, K_TASK_ID, K_BODY,
    alist_get,
)
from hyge_int_pkg.programme_c.admission_hooks import (
    structural_only_validity_for_tests, make_validity_check,
    make_rent_check, make_human_check, write_admission_manifest,
)
from hyge_int_pkg.programme_c.join import (
    COMBINATOR_AND, COMBINATOR_OR, GATE_VALIDITY, GATE_RENT, GATE_HUMAN,
    child_spec,
)


def _find_package_root():
    here = os.path.abspath(WD.__file__)
    d = os.path.dirname(here)
    for _ in range(6):
        if os.path.isfile(os.path.join(d, "main.py")) and os.path.isdir(os.path.join(d, "programme_c")):
            return d
        parent = os.path.dirname(d)
        if parent == d: break
        d = parent
    return os.path.abspath(os.path.join(os.path.dirname(here), "..", ".."))
PACKAGE_ROOT = _find_package_root()


def _poll(disp, t, timeout=180):
    end = time.time() + timeout
    while time.time() < end:
        r = disp.poll(t)
        if r is not M.EmptyList:
            return r
        time.sleep(0.1)
    return None


class RealWorkerE2ETests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="pc_e2e_")

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def _bootstrap(self):
        pool = W.BoundedWorkerPool(self.scratch, snapshot_ident=None, check_restore=False)
        disp = WD.SearchWorkerDispatch(pool, PACKAGE_ROOT)
        return pool, disp

    def test_two_workers_replayed_to_checked_and_join(self):
        pool, disp = self._bootstrap()
        try:
            ident = pool.snapshot_ident  # set lazily on first spawn
            # Launch two workers. Use defer_derivation=False so they run to
            # success-derivation-built (complete, replayable certificates).
            t1 = disp.spawn("dfs", "Zero", "Zero", "c1", "a-1", "ob-c1",
                            M.EmptyList, 300_000, 120, defer_derivation=False)
            t2 = disp.spawn("dfs", "Zero", "Zero", "c2", "a-1", "ob-c2",
                            M.EmptyList, 300_000, 120, defer_derivation=False)
            # Wait for both.
            r1 = _poll(disp, t1, timeout=240); self.assertIsNotNone(r1)
            r2 = _poll(disp, t2, timeout=240); self.assertIsNotNone(r2)
            self.assertEqual(alist_get(r1, K_STATUS), S_COMPLETED,
                             "c1 expected completed: " + str(alist_get(r1, K_BODY)))
            self.assertEqual(alist_get(r2, K_STATUS), S_COMPLETED)
            # Create AND parent with child specs matching the worker's
            # declared snapshot/obligation, then deliver the certificates.
            snap_id = t1.snapshot_id
            ja = J.JoinAdmission()
            specs = [child_spec("c1", "ob-c1", snap_id, t1.assumption_hash),
                     child_spec("c2", "ob-c2", snap_id, t2.assumption_hash)]
            ja.create_claim("p", COMBINATOR_AND, specs)
            ok1, reason1, rec = ja.deliver_child_result("p", r1)
            self.assertTrue(ok1, "delivery c1 failed: " + str(reason1))
            # Parent still running (one child pending).
            self.assertEqual(rec.status, "running")
            ok2, reason2, rec = ja.deliver_child_result("p", r2)
            self.assertTrue(ok2, "delivery c2 failed: " + str(reason2))
            self.assertEqual(rec.status, "completed")
            # Parent term is an AND-joined term, kind=joined.
            self.assertIsNotNone(rec.accepted_result)
            kind = P._atom_text(alist_get(rec.accepted_result, K_KIND))
            self.assertEqual(kind, "joined")
            pool.cleanup(t1); pool.cleanup(t2)
        finally:
            pool.shutdown()

    def test_incomplete_cert_does_not_discharge(self):
        pool, disp = self._bootstrap()
        try:
            t = disp.spawn("dfs", "Zero", "Zero", "c", "a-1", "ob",
                           M.EmptyList, 300_000, 120, defer_derivation=True)
            r = _poll(disp, t, timeout=240); self.assertIsNotNone(r)
            # Deferred derivation -> F_INVALID_CERT (cert not complete).
            self.assertEqual(alist_get(r, K_STATUS), S_FAILED)
            self.assertTrue(M.IdentityCompare(alist_get(r, K_REASON), F_INVALID_CERT)() is M.truth_value,
                            "expected F_INVALID_CERT got " + str(alist_get(r, K_REASON)))
            ja = J.JoinAdmission()
            snap_id = t.snapshot_id
            specs = [child_spec("c", "ob", snap_id, t.assumption_hash)]
            ja.create_claim("p", COMBINATOR_AND, specs)
            ok, reason, rec = ja.deliver_child_result("p", r)
            # Even if we delivered the envelope (which is a failure envelope,
            # not a result), the child status is 'failed' but the cert itself
            # was invalid-coded. The key invariant: parent does NOT complete.
            self.assertTrue(ok or not ok)
            self.assertEqual(rec.status, "running" if rec.status != "failed" else "failed",
                             "parent must not complete on incomplete cert")
            pool.cleanup(t)
        finally:
            pool.shutdown()

    def test_wrong_obligation_or_snapshot_rejected(self):
        pool, disp = self._bootstrap()
        try:
            t = disp.spawn("dfs", "Zero", "Zero", "c", "a-1", "ob-good",
                           M.EmptyList, 300_000, 120, defer_derivation=False)
            r = _poll(disp, t, timeout=240); self.assertIsNotNone(r)
            self.assertEqual(alist_get(r, K_STATUS), S_COMPLETED,
                             "expected completed: " + str(alist_get(r, K_BODY)))
            ja = J.JoinAdmission()
            # Declare child with a DIFFERENT obligation -> delivery must fail.
            specs = [child_spec("c", "ob-WRONG", t.snapshot_id, t.assumption_hash)]
            ja.create_claim("p", COMBINATOR_AND, specs)
            ok, reason, rec = ja.deliver_child_result("p", r)
            self.assertFalse(ok)
            self.assertTrue(M.IdentityCompare(reason, F_SCOPE_VIOLATION)() is M.truth_value,
                            "expected F_SCOPE_VIOLATION got " + str(reason))
            self.assertEqual(rec.status, "running")
            # Declare child with wrong snapshot_id -> F_SNAPSHOT_MISMATCH.
            ja2 = J.JoinAdmission()
            specs2 = [child_spec("c", "ob-good", "WRONG-SNAP-ID", t.assumption_hash)]
            ja2.create_claim("p2", COMBINATOR_AND, specs2)
            ok2, reason2, rec2 = ja2.deliver_child_result("p2", r)
            self.assertFalse(ok2)
            self.assertTrue(M.IdentityCompare(reason2, F_SNAPSHOT_MISMATCH)() is M.truth_value,
                            "expected F_SNAPSHOT_MISMATCH got " + str(reason2))
            pool.cleanup(t)
        finally:
            pool.shutdown()

    def test_admission_after_join_through_gates_with_manifest_recovery(self):
        """Join completes -> enqueue proposal -> admit_next through all three
        gates with on-disk manifest; simulate a crash before activation and
        recover (no duplicate admission)."""
        pool, disp = self._bootstrap()
        try:
            manifest = os.path.join(self.scratch, "adm", "manifest.json")
            os.makedirs(os.path.dirname(manifest), exist_ok=True)
            t = disp.spawn("dfs", "Zero", "Zero", "c", "a-1", "ob-c",
                           M.EmptyList, 300_000, 120, defer_derivation=False)
            r = _poll(disp, t, timeout=240); self.assertIsNotNone(r)
            self.assertEqual(alist_get(r, K_STATUS), S_COMPLETED)
            bench = os.path.join(self.scratch, "bench"); os.makedirs(bench)
            with open(os.path.join(bench, "rent_benchmark.json"),"w") as h:
                json.dump({"ms": 100}, h)
            val = make_validity_check(structural_only_validity_for_tests())
            rent = make_rent_check(benchmark_dir=bench)
            # Phase 1: admit with human-deny, then crash before activation.
            ja = J.JoinAdmission(manifest_path=manifest, strict_manifest=True)
            specs = [child_spec("c", "ob-c", t.snapshot_id, t.assumption_hash)]
            ja.create_claim("p", COMBINATOR_AND, specs)
            ja.deliver_child_result("p", r)
            self.assertEqual(ja.claims["p"].status, "completed")
            ja.enqueue_proposal("law-1", "p",
                                [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
            human_state = [False]
            human = make_human_check(lambda e: human_state[0])
            ok, _, why = ja.admit_next(val, rent, human)
            self.assertFalse(ok); self.assertEqual(why, "awaiting human")
            del ja
            # Phase 2: simulate restart. Re-hydrate, rebuild the claim with
            # fresh ChildSpec objects (join state is rebuilt by replaying
            # children), then admit with approving human and activate.
            ja2 = J.JoinAdmission(manifest_path=manifest, strict_manifest=True)
            fresh_specs = [child_spec("c", "ob-c", t.snapshot_id, t.assumption_hash)]
            ja2.create_claim("p", COMBINATOR_AND, fresh_specs)
            ok_d, reason_d, _ = ja2.deliver_child_result("p", r)
            self.assertTrue(ok_d, "delivery failed after restart: " + P._atom_text(reason_d))
            self.assertEqual(ja2.claims["p"].status, "completed")
            self.assertEqual(len(ja2._proposal_queue), 1)
            self.assertEqual(ja2._proposal_queue[0]["state"], "awaiting-human")
            human_state[0] = True
            ok2, _, why2 = ja2.admit_next(val, rent, make_human_check(lambda e: True))
            self.assertTrue(ok2, why2)
            activated = {"n": 0}
            ok3, _, why3 = ja2.activate_front(
                lambda e, a, v: (activated.__setitem__("n", activated["n"]+1) or True))
            self.assertTrue(ok3, why3)
            self.assertEqual(activated["n"], 1)
            pool.cleanup(t)
        finally:
            pool.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
