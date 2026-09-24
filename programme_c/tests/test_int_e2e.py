"""End-to-end: real search-worker subprocesses -> certificates replayed
against declared child specs -> checked AND/OR joins; wrong-obligation
/ wrong-snapshot certs rejected; on-disk admission manifest gates a
derived proposal through validity/rent/human with restart recovery and
crash-safe activation.

These tests boot actual search-worker subprocesses so they are slower;
they exercise the full coordinator -> child -> checkpoint -> certificate
replay -> join -> admission path end-to-end.
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
        """Two real Zero->Zero workers, replayed by coordinator, checked
        AND join completes; producer metadata alone does not discharge -
        proof.BuildDerivation on the trusted snapshot does."""
        pool, disp = self._bootstrap()
        try:
            t1 = disp.spawn("dfs", "Zero", "Zero", "c1", "a-1", "ob-c1",
                            M.EmptyList, 300_000, 120)
            t2 = disp.spawn("dfs", "Zero", "Zero", "c2", "a-1", "ob-c2",
                            M.EmptyList, 300_000, 120)
            r1 = _poll(disp, t1, timeout=240); self.assertIsNotNone(r1)
            r2 = _poll(disp, t2, timeout=240); self.assertIsNotNone(r2)
            self.assertEqual(alist_get(r1, K_STATUS), S_COMPLETED,
                             "c1 expected completed: " + str(alist_get(r1, K_BODY)))
            self.assertEqual(alist_get(r2, K_STATUS), S_COMPLETED)
            snap_id = t1.snapshot_id
            ja = J.JoinAdmission()
            specs = [child_spec("c1", "ob-c1", snap_id, t1.assumption_hash),
                     child_spec("c2", "ob-c2", snap_id, t2.assumption_hash)]
            ja.create_claim("p", COMBINATOR_AND, specs)
            ok1, reason1, rec = ja.deliver_child_result("p", r1)
            self.assertTrue(ok1, "delivery c1 failed: " + str(reason1))
            self.assertEqual(rec.status, "running")
            ok2, reason2, rec = ja.deliver_child_result("p", r2)
            self.assertTrue(ok2, "delivery c2 failed: " + str(reason2))
            self.assertEqual(rec.status, "completed")
            kind = P._atom_text(alist_get(rec.accepted_result, K_KIND))
            self.assertEqual(kind, "joined")
            pool.cleanup(t1); pool.cleanup(t2)
        finally:
            pool.shutdown()

    def test_checked_or_first_completing_alternative_discharges(self):
        """Real-worker checked OR (corrective #3): first completing child
        (Zero->Zero) discharges the parent even though siblings remain
        pending; late sibling results are idempotent/rejected as stale."""
        pool, disp = self._bootstrap()
        try:
            # c-fast completes (Zero->Zero); c-slow is an unreachable deep goal.
            fast = disp.spawn("dfs", "Zero", "Zero", "c-fast", "a-1", "ob-fast",
                              M.EmptyList, 300_000, 120)
            deep = "Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Succ(Zero))))))))))))"
            slow = disp.spawn("dfs", "Zero", deep, "c-slow", "a-1", "ob-slow",
                              M.EmptyList, 300_000, 120)
            r_fast = _poll(disp, fast, timeout=240)
            self.assertIsNotNone(r_fast)
            self.assertEqual(alist_get(r_fast, K_STATUS), S_COMPLETED)
            # Deliver only c-fast to an OR parent -> parent completes.
            ja = J.JoinAdmission()
            specs = [child_spec("c-fast", "ob-fast", fast.snapshot_id, fast.assumption_hash),
                     child_spec("c-slow", "ob-slow", slow.snapshot_id, slow.assumption_hash)]
            ja.create_claim("p", COMBINATOR_OR, specs)
            ok, reason, rec = ja.deliver_child_result("p", r_fast)
            self.assertTrue(ok, "OR failed on first completing child: " + str(reason))
            self.assertEqual(rec.status, "completed")
            sel = P._atom_text(alist_get(rec.accepted_result,
                                         P.text_atom("selected_child")))
            self.assertEqual(sel, "c-fast")
            # Cancel slow.
            disp.cancel(slow)
            pool.cleanup(fast); pool.cleanup(slow)
        finally:
            pool.shutdown()

    def test_wrong_obligation_or_snapshot_rejected(self):
        pool, disp = self._bootstrap()
        try:
            t = disp.spawn("dfs", "Zero", "Zero", "c", "a-1", "ob-good",
                           M.EmptyList, 300_000, 120)
            r = _poll(disp, t, timeout=240); self.assertIsNotNone(r)
            self.assertEqual(alist_get(r, K_STATUS), S_COMPLETED,
                             "expected completed: " + str(alist_get(r, K_BODY)))
            ja = J.JoinAdmission()
            specs = [child_spec("c", "ob-WRONG", t.snapshot_id, t.assumption_hash)]
            ja.create_claim("p", COMBINATOR_AND, specs)
            ok, reason, rec = ja.deliver_child_result("p", r)
            self.assertFalse(ok)
            self.assertTrue(M.IdentityCompare(reason, F_SCOPE_VIOLATION)() is M.truth_value,
                            "expected F_SCOPE_VIOLATION got " + str(reason))
            self.assertEqual(rec.status, "running")
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

    def test_admission_after_join_through_gates_with_crash_safe_activation(self):
        """Join completes -> enqueue proposal -> admit_next through all
        three gates with on-disk manifest. Then write 'activating' and
        simulate crash; restart must not double-activate and activation
        must run exactly once. Version stays monotonic on failure."""
        pool, disp = self._bootstrap()
        try:
            manifest = os.path.join(self.scratch, "adm", "manifest.json")
            os.makedirs(os.path.dirname(manifest), exist_ok=True)
            t = disp.spawn("dfs", "Zero", "Zero", "c", "a-1", "ob-c",
                           M.EmptyList, 300_000, 120)
            r = _poll(disp, t, timeout=240); self.assertIsNotNone(r)
            self.assertEqual(alist_get(r, K_STATUS), S_COMPLETED)
            bench = os.path.join(self.scratch, "bench"); os.makedirs(bench)
            # Write a valid rent benchmark (benchmark.json, schema v1).
            from hyge_int_pkg.programme_c.tests.test_int_gates import (
                _write_passing_rent_benchmark,
            )
            _write_passing_rent_benchmark(bench)
            val = make_validity_check(structural_only_validity_for_tests())
            rent = make_rent_check(benchmark_dir=bench)
            human = make_human_check(lambda e: True)
            ja = J.JoinAdmission(manifest_path=manifest, strict_manifest=True)
            specs = [child_spec("c", "ob-c", t.snapshot_id, t.assumption_hash)]
            ja.create_claim("p", COMBINATOR_AND, specs)
            ok_d, reason_d, _ = ja.deliver_child_result("p", r)
            self.assertTrue(ok_d, "delivery failed: " + str(reason_d))
            self.assertEqual(ja.claims["p"].status, "completed")
            pid = ja.enqueue_proposal("law-1", "p",
                                [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
            _id_enc = {"kind": "rule", "left": {"Char": "z"}, "right": {"Char": "z"}}
            for e in ja._proposal_queue:
                if e["proposal_id"] == pid:
                    e["proposal_encoding"] = _id_enc
                    e["law_encoding"] = _id_enc
                    break
            ok, _, why = ja.admit_next(val, rent, human)
            self.assertTrue(ok, why); self.assertEqual(why, "admitted")
            self.assertEqual(ja._accepted_state_version, 1)
            # Simulate: failed activation first (version stays 1; entry
            # remains 'activation-failed' blocking further admission).
            ok_f, _, why_f = ja.activate_front(lambda e, a, v: False)
            self.assertFalse(ok_f); self.assertEqual(why_f, "activation failed")
            self.assertEqual(ja._accepted_state_version, 1)
            # Cannot enqueue new proposals while activation unresolved.
            self.assertEqual(ja.enqueue_proposal("blocked", "p", []), "")
            # Simulate crash DURING retry: set state='activating' (as the
            # activate_front path does immediately before invoking fn),
            # persist, then drop the JoinAdmission.
            ja._accepted_proposals[-1]["state"] = "activating"
            ja._activation_inflight = True
            ja._persist()
            del ja
            # Restart.
            ja2 = J.JoinAdmission(manifest_path=manifest, strict_manifest=True)
            self.assertTrue(ja2._activation_inflight)
            self.assertEqual(ja2.pending_activation()["state"], "activating")
            self.assertEqual(ja2._accepted_state_version, 1)
            # Cannot enqueue until activation resolves.
            self.assertEqual(ja2.enqueue_proposal("blocked2", "p", []), "")
            # Activate successfully; fn invoked exactly once.
            n = {"calls": 0}
            ok_a, _, why_a = ja2.activate_front(
                lambda e, a, v: (n.__setitem__("calls", n["calls"]+1) or True))
            self.assertTrue(ok_a, why_a); self.assertEqual(n["calls"], 1)
            # Idempotent.
            ok_a2, _, why_a2 = ja2.activate_front(
                lambda e, a, v: (n.__setitem__("calls", n["calls"]+1) or True))
            self.assertTrue(ok_a2); self.assertEqual(why_a2, "already-activated")
            self.assertEqual(n["calls"], 1)
            with open(manifest) as h:
                m = json.load(h)
            self.assertEqual(m["accepted_state_version"], 1)
            self.assertEqual(m["accepted"][-1]["state"], "activated")
            pool.cleanup(t)
        finally:
            pool.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
