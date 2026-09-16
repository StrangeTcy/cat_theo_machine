"""C-C gate + on-disk admission manifest tests under fail-closed semantics
(post corrective 2026-09-16 #2):

  * Validity/rent/human each fail closed when callback missing/raising.
  * Gate order; human deny -> approve -> admit -> activate with crash-safe
    'activating' durable record; version monotonic (never decremented);
    failed activation stays in accepted set and blocks further admission
    until retried; activation after success is idempotent.
  * Enqueue persisted; restart rehydrates queue/accepted/version and
    prevents duplicate activation (idempotent).
  * Corrupt/wrong-schema manifests raise ManifestError.
  * Persistence failures raise (fail closed).
  * No next candidate admitted while activation pending.
  * One admission at a time.
"""
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
        benchmark_dir = os.path.join(self.scratch, "bench")
        os.makedirs(benchmark_dir)
        rent = make_rent_check(benchmark_dir=benchmark_dir)
        human_state = {"ok": False}
        human = make_human_check(lambda e: human_state["ok"])
        pid = ja.enqueue_proposal("proposal-ok", "c-1",
                                  [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        self.assertTrue(pid)
        ok, _, reason = ja.admit_next(
            lambda e, a, v: (calls.append("validity"), val(e, a, v))[1],
            lambda e: (calls.append("rent"), rent(e))[1],
            human)
        self.assertFalse(ok); self.assertEqual(reason, "rent hold")
        with open(os.path.join(benchmark_dir, "rent_benchmark.json"), "w") as h:
            json.dump({"baseline_ms": 100}, h)
        ok2, _, reason2 = ja.admit_next(
            lambda e, a, v: (calls.append("validity2"), val(e, a, v))[1],
            lambda e: (calls.append("rent2"), rent(e))[1],
            human)
        self.assertFalse(ok2); self.assertEqual(reason2, "awaiting human")
        # Before admit nothing blocks enqueue; the block applies only once
        # the front has been admitted (enters admitted/activating/activation-failed).
        self.assertTrue(ja.enqueue_proposal("queued-while-awaiting-human", "c-1", []))
        # Pop it to keep the rest of the test clean.
        ja._proposal_queue.pop()
        # Approve -> admit. Version becomes 1.
        human_state["ok"] = True
        ok3, _, reason3 = ja.admit_next(
            lambda e, a, v: (calls.append("validity3"), val(e, a, v))[1],
            lambda e: (calls.append("rent3"), rent(e))[1],
            human)
        self.assertTrue(ok3, reason3); self.assertEqual(reason3, "admitted")
        self.assertEqual(ja._accepted_state_version, 1)
        # No second admission/enqueue can proceed while activation is pending.
        self.assertEqual(ja.enqueue_proposal("blocked", "c-1", []), "")
        # Activator fails -> activation-failed, version stays 1.
        ok_a, _, ra = ja.activate_front(lambda e, a, v: False)
        self.assertFalse(ok_a); self.assertEqual(ra, "activation failed")
        self.assertEqual(ja._accepted_state_version, 1)
        self.assertEqual(ja._accepted_proposals[-1]["state"], "activation-failed")
        # Still cannot enqueue (pending activation).
        self.assertFalse(ja.enqueue_proposal("blocked2", "c-1", []))
        # Retry activation successfully.
        n_act = {"n": 0}
        ok_a2, _, ra2 = ja.activate_front(
            lambda e, a, v: (n_act.__setitem__("n", n_act["n"]+1) or True))
        self.assertTrue(ok_a2, ra2)
        self.assertEqual(n_act["n"], 1)
        # Idempotent: second activate_front is already-activated, no extra call.
        ok_a3, _, ra3 = ja.activate_front(
            lambda e, a, v: (n_act.__setitem__("n", n_act["n"]+1) or True))
        self.assertTrue(ok_a3); self.assertEqual(ra3, "already-activated")
        self.assertEqual(n_act["n"], 1)
        # Activation-failed remains unresolved (blocking further admission)
        # until activation succeeds. That was already verified above when
        # enqueue_proposal("blocked2", ...) returned "".
        # Manifest reflects activated state and version=1 (monotonic).
        with open(self.manifest) as h:
            m = json.load(h)
        self.assertEqual(m["accepted"][-1]["state"], "activated")
        self.assertEqual(m["accepted_state_version"], 1)
        self.assertEqual(m["queue"], [])
        # Now enqueue/pass again is allowed.
        pid2 = ja.enqueue_proposal("next", "c-1", [])
        self.assertTrue(pid2)

    def test_missing_validity_callback_fails_closed(self):
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        ja.enqueue_proposal("p", "c-1", [GATE_VALIDITY])
        ok, _, reason = ja.admit_next(make_validity_check(None),
                                      make_rent_check(None),
                                      make_human_check(None))
        self.assertFalse(ok); self.assertEqual(reason, "validity failed")

    def test_missing_rent_benchmark_fails_closed(self):
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        ja.enqueue_proposal("p", "c-1", [GATE_VALIDITY, GATE_RENT])
        ok, _, reason = ja.admit_next(
            make_validity_check(structural_only_validity_for_tests()),
            make_rent_check(benchmark_dir=None),
            make_human_check(None))
        self.assertFalse(ok); self.assertEqual(reason, "rent hold")

    def test_missing_human_callback_fails_closed(self):
        benchmark_dir = os.path.join(self.scratch, "bench")
        os.makedirs(benchmark_dir)
        with open(os.path.join(benchmark_dir, "rent_benchmark.json"), "w") as h:
            json.dump({"x": 1}, h)
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        ja.enqueue_proposal("p", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        ok, _, reason = ja.admit_next(
            make_validity_check(structural_only_validity_for_tests()),
            make_rent_check(benchmark_dir=benchmark_dir),
            make_human_check(None))
        self.assertFalse(ok); self.assertEqual(reason, "awaiting human")

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

    def test_activating_marker_survives_restart_and_prevents_admission(self):
        # Crash after writing 'activating' but before activation completes:
        # restart must see activation pending and refuse new admission.
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        benchmark_dir = os.path.join(self.scratch, "bench"); os.makedirs(benchmark_dir)
        with open(os.path.join(benchmark_dir, "rent_benchmark.json"), "w") as h:
            json.dump({"x":1}, h)
        ja.enqueue_proposal("law-x", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        ok, _, _ = ja.admit_next(
            make_validity_check(structural_only_validity_for_tests()),
            make_rent_check(benchmark_dir=benchmark_dir),
            make_human_check(lambda e: True))
        self.assertTrue(ok)
        # Manually set 'activating' (simulating a crash between persist of
        # 'activating' and completion of activation_fn) and rebuild.
        ja._accepted_proposals[-1]["state"] = "activating"
        ja._activation_inflight = True
        ja._persist()
        del ja
        ja2 = J.JoinAdmission(manifest_path=self.manifest, strict_manifest=True)
        # Recovery detects inflight activation and blocks admission.
        self.assertTrue(ja2._activation_inflight)
        self.assertEqual(ja2.pending_activation()["state"], "activating")
        self.assertFalse(ja2.enqueue_proposal("blocked", "c-1", []))
        # Completing activation clears the marker.
        n = {"calls": 0}
        ok2, _, r2 = ja2.activate_front(lambda e, a, v: (n.__setitem__("calls", n["calls"]+1) or True))
        self.assertTrue(ok2, r2); self.assertEqual(n["calls"], 1)
        self.assertFalse(ja2._activation_inflight)

    def test_corrupt_manifest_fails_closed(self):
        with open(self.manifest, "w") as h:
            h.write("{not valid json")
        with self.assertRaises(ManifestError):
            J.JoinAdmission(manifest_path=self.manifest, strict_manifest=True)

    def test_wrong_schema_manifest_fails_closed(self):
        write_admission_manifest(self.manifest, [], [],
                                accepted_state_version=0, schema_version=99999)
        with self.assertRaises(ManifestError):
            J.JoinAdmission(manifest_path=self.manifest, strict_manifest=True)

    def test_persistence_failure_propagates(self):
        ro_dir = os.path.join(self.scratch, "ro")
        os.makedirs(ro_dir); os.chmod(ro_dir, 0o500)
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
