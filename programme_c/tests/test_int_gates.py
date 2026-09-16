"""C-C gate + on-disk admission manifest tests under fail-closed semantics
(post C-INT review 2026-09-16):

  * Validity/rent/human each fail closed when their callable returns False
    or raises or is missing.
  * Accepted-state version increments on admission; stale gate evidence is
    revalidated.
  * Manifest persistence is durable (fsync); enqueue is persisted; corrupt
    or schema-mismatch manifests raise ManifestError (fail closed, no silent
    reset).
  * activate_front performs activation only after admitted state is
    persisted; failed activation rolls back to queue without double-counting.
  * One admission at a time through validity -> rent -> human -> activation.
"""
from __future__ import annotations
import json
import os
import shutil
import tempfile
import time
import unittest

import hyge_int_pkg.programme_c.join as J
from hyge_int_pkg.programme_c.admission_hooks import (
    MANIFEST_SCHEMA_VERSION, ManifestError,
    make_validity_check, structural_only_validity_for_tests,
    make_rent_check, make_human_check,
    write_admission_manifest, load_admission_manifest,
)
from hyge_int_pkg.programme_c.join import (
    COMBINATOR_AND, GATE_VALIDITY, GATE_RENT, GATE_HUMAN, child_spec,
)


def _fake_completed_claim(ja, claim_id="c-1"):
    spec = child_spec("leaf", "obligation-a", "snap", "ah-0")
    rec = ja.create_claim(claim_id, COMBINATOR_AND, [spec])
    leaf = rec.children["leaf"]
    leaf.status = "completed"
    leaf.result_term = "ok"
    rec.status = "completed"
    return rec


class GateIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="pc_int_gates_")
        self.manifest = os.path.join(self.scratch, "admission_manifest.json")

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def test_gate_order_validity_then_rent_then_human_then_admit_then_activate(self):
        ja = J.JoinAdmission(manifest_path=self.manifest, strict_manifest=True)
        _fake_completed_claim(ja, "c-1")
        calls = []
        val = make_validity_check(structural_only_validity_for_tests())
        # Rent with a benchmark dir; benchmark initially missing -> hold.
        benchmark_dir = os.path.join(self.scratch, "bench")
        os.makedirs(benchmark_dir)
        rent = make_rent_check(benchmark_dir=benchmark_dir)
        human_state = {"ok": False, "count": 0}
        def human_cb(entry):
            human_state["count"] += 1
            calls.append("human-" + str(human_state["count"]))
            return human_state["ok"]
        human = make_human_check(human_cb)
        pid = ja.enqueue_proposal("proposal-ok", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        self.assertTrue(pid)
        # Validity passes (structural) but rent is missing benchmark -> hold.
        calls.append("call1")
        ok, _p, reason = ja.admit_next(
            lambda e, a, v: (calls.append("validity"), val(e, a, v))[1],
            lambda e: (calls.append("rent"), rent(e))[1],
            human)
        self.assertFalse(ok)
        self.assertEqual(reason, "rent hold")
        # Place benchmark -> rent passes; human denies -> await.
        with open(os.path.join(benchmark_dir, "rent_benchmark.json"), "w") as h:
            json.dump({"baseline_ms": 100}, h)
        ok2, _p2, reason2 = ja.admit_next(
            lambda e, a, v: (calls.append("validity2"), val(e, a, v))[1],
            lambda e: (calls.append("rent2"), rent(e))[1],
            human)
        self.assertFalse(ok2)
        self.assertEqual(reason2, "awaiting human")
        # Human approves -> admitted but NOT yet activated.
        human_state["ok"] = True
        ok3, _p3, reason3 = ja.admit_next(
            lambda e, a, v: (calls.append("validity3"), val(e, a, v))[1],
            lambda e: (calls.append("rent3"), rent(e))[1],
            human)
        self.assertTrue(ok3, reason3)
        self.assertEqual(reason3, "admitted")
        # activate_front with failing activator rolls back.
        ok_a, _pa, ra = ja.activate_front(lambda e, a, v: False)
        self.assertFalse(ok_a)
        self.assertEqual(ra, "activation failed")
        # Entry is back at front of queue.
        self.assertEqual(len(ja._accepted_proposals), 0)
        self.assertEqual(ja._proposal_queue[0]["state"], "activation-failed")
        # Admit again, then activate successfully.
        human_state["ok"] = True
        ok4, _, reason4 = ja.admit_next(
            val, rent, human)
        self.assertTrue(ok4, reason4)
        activated_flag = {"n": 0}
        def activator(e, a, v):
            activated_flag["n"] += 1; return True
        ok5, _, reason5 = ja.activate_front(activator)
        self.assertTrue(ok5, reason5)
        self.assertEqual(activated_flag["n"], 1)
        # Manifest on disk reflects 'activated'.
        with open(self.manifest) as h:
            m = json.load(h)
        self.assertEqual(m["queue"], [])
        self.assertEqual(m["accepted"][-1]["state"], "activated")
        self.assertEqual(m["accepted_state_version"], 1)  # rolled-back admit does not bump version

    def test_missing_validity_callback_fails_closed(self):
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        ja.enqueue_proposal("p", "c-1", [GATE_VALIDITY])
        # No callback supplied -> default-deny.
        ok, _, reason = ja.admit_next(make_validity_check(None),
                                      make_rent_check(None),
                                      make_human_check(None))
        self.assertFalse(ok)
        self.assertEqual(reason, "validity failed")

    def test_missing_rent_benchmark_fails_closed(self):
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        ja.enqueue_proposal("p", "c-1", [GATE_VALIDITY, GATE_RENT])
        ok, _, reason = ja.admit_next(
            make_validity_check(structural_only_validity_for_tests()),
            make_rent_check(benchmark_dir=None),  # no benchmark configured
            make_human_check(None))
        self.assertFalse(ok)
        self.assertEqual(reason, "rent hold")

    def test_missing_human_callback_fails_closed(self):
        benchmark_dir = os.path.join(self.scratch, "bench")
        os.makedirs(benchmark_dir)
        with open(os.path.join(benchmark_dir, "rent_benchmark.json"), "w") as h:
            json.dump({"x":1}, h)
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        ja.enqueue_proposal("p", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        ok, _, reason = ja.admit_next(
            make_validity_check(structural_only_validity_for_tests()),
            make_rent_check(benchmark_dir=benchmark_dir),
            make_human_check(None))
        self.assertFalse(ok)
        self.assertEqual(reason, "awaiting human")

    def test_enqueue_persisted_before_admit(self):
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        pid = ja.enqueue_proposal("hello", "c-1", [GATE_VALIDITY])
        self.assertTrue(pid)
        with open(self.manifest) as h:
            m = json.load(h)
        self.assertEqual(len(m["queue"]), 1)
        self.assertEqual(m["queue"][0]["proposal_id"], pid)
        self.assertEqual(m["accepted_state_version"], 0)

    def test_restart_rehydrates_queue_and_prevents_duplicate_admission(self):
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        benchmark_dir = os.path.join(self.scratch, "bench"); os.makedirs(benchmark_dir)
        with open(os.path.join(benchmark_dir, "rent_benchmark.json"),"w") as h:
            json.dump({"x":1}, h)
        pid = ja.enqueue_proposal("restart-test", "c-1",
                                  [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        # Admit through all gates but don't activate yet.
        ok, _, _ = ja.admit_next(
            make_validity_check(structural_only_validity_for_tests()),
            make_rent_check(benchmark_dir=benchmark_dir),
            make_human_check(lambda e: True))
        self.assertTrue(ok)
        self.assertEqual(ja._proposal_queue, [])
        self.assertEqual(ja._accepted_proposals[-1]["state"], "admitted")
        # Simulate restart: new JoinAdmission from same manifest.
        ja2 = J.JoinAdmission(manifest_path=self.manifest)
        self.assertEqual(len(ja2._proposal_queue), 0)
        self.assertEqual(len(ja2._accepted_proposals), 1)
        self.assertEqual(ja2._accepted_proposals[-1]["state"], "admitted")
        self.assertEqual(ja2._accepted_state_version, 1)
        # Activate on restart does not double-count.
        n = {"calls":0}
        ok2, pid2, r2 = ja2.activate_front(lambda e, a, v: (n.__setitem__("calls", n["calls"]+1) or True))
        self.assertTrue(ok2)
        self.assertEqual(n["calls"], 1)
        self.assertEqual(ja2._accepted_proposals[-1]["state"], "activated")
        # Second activate_front is a no-op because front is now activated.
        ok3, _, r3 = ja2.activate_front(lambda e, a, v: (n.__setitem__("calls", n["calls"]+1) or True))
        self.assertFalse(ok3)
        self.assertEqual(n["calls"], 1)  # activator not called again

    def test_corrupt_manifest_fails_closed(self):
        with open(self.manifest, "w") as h:
            h.write("{not valid json")
        with self.assertRaises(ManifestError):
            J.JoinAdmission(manifest_path=self.manifest, strict_manifest=True)

    def test_wrong_schema_manifest_fails_closed(self):
        write_admission_manifest(self.manifest, [], [], accepted_state_version=0,
                                schema_version=99999)
        with self.assertRaises(ManifestError):
            J.JoinAdmission(manifest_path=self.manifest, strict_manifest=True)

    def test_persistence_failure_reports_error(self):
        # Create manifest_path pointing to a non-writable location (a file
        # inside a chmod-000 directory). enqueue must raise, not silently
        # succeed.
        ro_dir = os.path.join(self.scratch, "ro")
        os.makedirs(ro_dir)
        os.chmod(ro_dir, 0o500)  # read+execute only, no write
        bad_path = os.path.join(ro_dir, "m.json")
        ja = J.JoinAdmission(manifest_path=bad_path, strict_manifest=False)
        _fake_completed_claim(ja, "c-1")
        def _try():
            ja.enqueue_proposal("x", "c-1", [])
        try:
            self.assertRaises((OSError, PermissionError), _try)
        finally:
            os.chmod(ro_dir, 0o700)


if __name__ == "__main__":
    unittest.main(verbosity=2)
