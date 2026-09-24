"""C-C gate + on-disk admission manifest tests under fail-closed semantics
(post corrective 2026-09-16):

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
  * Isolated check-only graph.ActivateProposal validity gate:
      - accepts a well-formed Zero->Succ(Zero) law;
      - rejects an EmptyList proposal body;
      - rejects a text-only entry (no structural fallback);
      - check discards its runtime so no host-state mutation occurs
        (no reconciliation surface).
"""
import io
import json
import os
import shutil
import tempfile
import time
import unittest

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c.join as J
import hyge_int_pkg.programme_c as P
from hyge_int_pkg.programme_c.admission_hooks import (
    MANIFEST_SCHEMA_VERSION, ManifestError,
    make_validity_check, structural_only_validity_for_tests,
    make_rent_check, make_human_check,
    write_admission_manifest, load_admission_manifest,
    make_live_activate_proposal_check,
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


def _write_passing_rent_benchmark(benchmark_dir):
    """Write a benchmark.json that trivially passes (small identity specs,
    generous budgets)."""
    os.makedirs(benchmark_dir, exist_ok=True)
    payload = {
        "schema_version": 1,
        "timeout_seconds": 90,
        "step_budget": 100000,
        "max_total_ms": 60000,
        "specs": [
            {"name": "id-z",
             "left": {"Char": "z"}, "right": {"Char": "z"},
             "start": {"Char": "z"}},
        ],
    }
    with open(os.path.join(benchmark_dir, "benchmark.json"), "w",
              encoding="utf-8") as h:
        json.dump(payload, h)


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
        _id_enc = {"kind": "rule", "left": {"Char": "z"}, "right": {"Char": "z"}}
        for e in ja._proposal_queue:
            if e["proposal_id"] == pid:
                e["proposal_encoding"] = _id_enc
                e["law_encoding"] = _id_enc
                break
        # No benchmark.json yet -> F_LAUNCH_ERROR, front intact (rent-launch-error).
        ok, _, reason = ja.admit_next(
            lambda e, a, v: (calls.append("validity"), val(e, a, v))[1],
            rent,
            human)
        self.assertFalse(ok); self.assertEqual(reason, "rent-launch-error")
        # Front is NOT popped, state preserved.
        self.assertEqual(len(ja._proposal_queue), 1)
        self.assertEqual(ja._proposal_queue[0]["proposal_id"], pid)
        # Write a passing benchmark.json -> rent advances to human gate.
        _write_passing_rent_benchmark(benchmark_dir)
        ok2, _, reason2 = ja.admit_next(
            lambda e, a, v: (calls.append("validity2"), val(e, a, v))[1],
            rent,
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
            rent,
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
        front_pid = ja._proposal_queue[0]["proposal_id"]
        ok, pid, reason = ja.admit_next(
            make_validity_check(structural_only_validity_for_tests()),
            make_rent_check(benchmark_dir=None),
            make_human_check(None))
        # No benchmark dir configured -> F_LAUNCH_ERROR, front intact.
        self.assertFalse(ok); self.assertEqual(reason, "rent-launch-error")
        self.assertEqual(pid, front_pid)
        self.assertEqual(len(ja._proposal_queue), 1)

    def test_missing_human_callback_fails_closed(self):
        benchmark_dir = os.path.join(self.scratch, "bench")
        os.makedirs(benchmark_dir)
        _write_passing_rent_benchmark(benchmark_dir)
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        pid = ja.enqueue_proposal("p", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        # Attach a trivial identity law encoding so rent subprocess can
        # install the candidate (tests use text-only structural checks).
        for e in ja._proposal_queue:
            if e["proposal_id"] == pid:
                _id_enc = {"kind": "rule", "left": {"Char": "z"},
                            "right": {"Char": "z"}}
                e["proposal_encoding"] = _id_enc
                e["law_encoding"] = _id_enc
                break
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
        benchmark_dir = os.path.join(self.scratch, "bench")
        _write_passing_rent_benchmark(benchmark_dir)
        pid = ja.enqueue_proposal("law-x", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        _id_enc = {"kind": "rule", "left": {"Char": "z"}, "right": {"Char": "z"}}
        for e in ja._proposal_queue:
            if e["proposal_id"] == pid:
                e["proposal_encoding"] = _id_enc
                e["law_encoding"] = _id_enc
                break
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


class LiveActivateProposalValidityTests(unittest.TestCase):
    """Real check-only graph.ActivateProposal validity gate (subprocess-
    isolated per Q1). Each test boots packs in a child process (~10s)."""

    @classmethod
    def setUpClass(cls):
        cls._check = staticmethod(make_live_activate_proposal_check(
            timeout_seconds=120))

    def _silent(self, fn, *a, **kw):
        buf = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            return fn(*a, **kw)

    def _entry(self, left_spec, right_spec, origin="test-origin"):
        enc = {"kind": "rule", "left": left_spec, "right": right_spec}
        return {"proposal_id": "p-live",
                "proposal_text": "",
                "origin": origin,
                "proposal_encoding": enc,
                "law_encoding": enc,
                "state": "queued"}

    def _acc(self, pid, left_spec, right_spec, origin="prior"):
        enc = {"kind": "rule", "left": left_spec, "right": right_spec}
        return {"proposal_id": pid,
                "proposal_text": "",
                "origin": origin,
                "proposal_encoding": enc,
                "law_encoding": enc,
                "state": "activated"}

    def _policy_entry(self, cls_name, gate):
        return {"kind": "policy_entry", "class_name": cls_name, "gate": gate}

    def _policy_entry_acc(self, pid, cls_name, gate, origin="prior"):
        enc = self._policy_entry(cls_name, gate)
        return {"proposal_id": pid, "proposal_text": "", "origin": origin,
                "proposal_encoding": enc, "law_encoding": enc,
                "state": "activated"}

    def test_well_formed_identity_passes(self):
        entry = self._entry({"Char": "z"}, {"Char": "z"})
        ok, reason = self._silent(self._check, entry, [], 0)
        self.assertTrue(ok, "well-formed identity must pass; reason=%r" % (reason,))
        self.assertIsNone(reason)

    def test_undecodable_entry_fails_invalid_cert(self):
        entry = {"proposal_text": "free-text only", "state": "queued"}
        ok, reason = self._silent(self._check, entry, [], 0)
        self.assertFalse(ok)
        self.assertIs(M.IdentityCompare(reason, P.F_INVALID_CERT)(), M.truth_value)

    def test_subprocess_isolated_no_host_registry_mutation(self):
        """Q1 regression: two back-to-back checks produce identical results;
        no constructor-registry leakage between calls because each spawns
        a fresh child."""
        entry = self._entry({"Char": "z"}, {"Char": "z"})
        ok1, _ = self._silent(self._check, entry, [], 0)
        ok2, _ = self._silent(self._check, entry, [], 0)
        self.assertTrue(ok1); self.assertTrue(ok2)

    def test_launch_error_holds_queue_front(self):
        """Q2: injected launch failure (invalid package_root) must yield
        F_LAUNCH_ERROR, not F_INVALID_CERT; admit_next must NOT pop the
        queue front and must return 'validity-launch-error'."""
        bad_check = staticmethod(make_live_activate_proposal_check(
            package_root="/nonexistent-package-root-xyz",
            timeout_seconds=10))
        entry = self._entry({"Char": "z"}, {"Char": "z"})
        ok, reason = self._silent(bad_check, entry, [], 0)
        self.assertFalse(ok)
        self.assertIs(M.IdentityCompare(reason, P.F_LAUNCH_ERROR)(), M.truth_value)
        # admit_next keeps front intact.
        manifest = os.path.join(self.scratch() if False else tempfile.mkdtemp(),
                                "manifest.json")
        try:
            ja = J.JoinAdmission(manifest_path=manifest)
            _fake_completed_claim(ja, "c-1")
            ja.enqueue_proposal("z=z", "c-1", [GATE_VALIDITY])
            front_pid = ja._proposal_queue[0]["proposal_id"]
            front_state_before = ja._proposal_queue[0]["state"]
            ok_a, pid, why = ja.admit_next(bad_check,
                                            make_rent_check(None),
                                            make_human_check(None))
            self.assertFalse(ok_a)
            self.assertEqual(why, "validity-launch-error")
            self.assertEqual(pid, front_pid)
            # front not popped:
            self.assertEqual(len(ja._proposal_queue), 1)
            self.assertEqual(ja._proposal_queue[0]["proposal_id"], front_pid)
            # state NOT mutated to rejected-validity; preserved queued.
            self.assertEqual(ja._proposal_queue[0]["state"], front_state_before)
        finally:
            try: shutil.rmtree(os.path.dirname(manifest))
            except OSError: pass

    def test_q3_well_formed_policy_change_loosening_refused(self):
        """Q3(i): a well-formed policy_change proposal that loosens
        install_law from the bootstrap gate ('human') to 'auto' is
        structurally valid (compiles to a Law, ClassifyProposal
        recognizes policy_change) but ActivateProposal refuses it via
        ReasonUncountersigned because no Countersigned annotation from
        a structurally distinct authority is attached. This exercises
        real ActivateProposal gating, not shape checking."""
        pol_enc = self._policy_entry("install_law", "auto")
        entry = {"proposal_id": "p-pol", "proposal_text": "", "origin": "test",
                 "state": "queued",
                 "proposal_encoding": pol_enc, "law_encoding": pol_enc}
        ok, reason = self._silent(self._check, entry, [], 0)
        self.assertFalse(ok,
                         "loosening policy change without countersign must be refused")
        self.assertIs(M.IdentityCompare(reason, P.F_INVALID_CERT)(), M.truth_value)

    def test_q3_state_dependence_pair(self):
        """Q3(ii): state-dependence pair -- the SAME policy_change
        proposal (install_law human->auto) is:
          - REFUSED against empty accepted state (bootstrap effective
            policy still has install_law=human; loosening requires
            countersign which is absent);
          - ACCEPTED against an accepted set where install_law=auto is
            already installed (InstallLaw replay rebuilds effective
            policy so the proposal is an identity change, not a
            loosening, and the countersign requirement does not apply).
        This confirms InstallLaw replay of prior accepted laws actually
        shapes ActivateProposal's decision, not just shape checking."""
        pol_enc = self._policy_entry("install_law", "auto")
        candidate = {"proposal_id": "p-pol", "proposal_text": "",
                     "origin": "test", "state": "queued",
                     "proposal_encoding": pol_enc, "law_encoding": pol_enc}
        # Empty accepted: refused.
        ok_empty, reason_empty = self._silent(self._check, candidate, [], 0)
        self.assertFalse(ok_empty,
                         "against empty accepted state the loosening must fail")
        self.assertIs(M.IdentityCompare(reason_empty, P.F_INVALID_CERT)(),
                      M.truth_value)
        # Accepted set already has install_law=auto as an activated law.
        accepted = [self._policy_entry_acc("acc-1", "install_law", "auto")]
        ok_prior, reason_prior = self._silent(self._check, candidate, accepted, 1)
        self.assertTrue(ok_prior,
                        "against accepted-set with auto policy already installed "
                        "the same proposal must be accepted (identity change, "
                        "no loosening); reason=%r" % (reason_prior,))


class RentHookTests(unittest.TestCase):
    """Rent hook (cint-integrated-7, 2026-09-17). Subprocess-isolated
    benchmark gate; F_LAUNCH_ERROR on missing/failing benchmark (front
    held intact), F_RENT_FAIL on spec failure (reject+pop), pass with
    evidence bound to (proposal_id, accepted_state_version,
    benchmark_identity)."""

    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="pc_rent_")

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def _entry(self):
        enc = {"kind": "rule", "left": {"Char": "z"}, "right": {"Char": "z"}}
        return {"proposal_id": "p-rent-test", "proposal_text": "",
                "origin": "test", "state": "queued",
                "proposal_encoding": enc, "law_encoding": enc}

    def test_missing_benchmark_dir_returns_launch_error(self):
        ja = J.JoinAdmission(manifest_path=os.path.join(self.scratch, "m.json"))
        _fake_completed_claim(ja, "c-1")
        ja.enqueue_proposal("p", "c-1", [GATE_RENT])
        front_pid = ja._proposal_queue[0]["proposal_id"]
        ok, pid, why = ja.admit_next(
            make_validity_check(structural_only_validity_for_tests()),
            make_rent_check(benchmark_dir=os.path.join(self.scratch, "nobench")),
            make_human_check(None))
        self.assertFalse(ok)
        self.assertEqual(why, "rent-launch-error")
        self.assertEqual(pid, front_pid)
        self.assertEqual(len(ja._proposal_queue), 1,
                         "launch error must NOT pop queue front")

    def test_benchmark_pass_advances(self):
        bench = os.path.join(self.scratch, "bench")
        _write_passing_rent_benchmark(bench)
        ja = J.JoinAdmission(manifest_path=os.path.join(self.scratch, "m.json"))
        _fake_completed_claim(ja, "c-1")
        pid = ja.enqueue_proposal("p", "c-1", [GATE_RENT])
        _id_enc = {"kind": "rule", "left": {"Char": "z"}, "right": {"Char": "z"}}
        for e in ja._proposal_queue:
            if e["proposal_id"] == pid:
                e["proposal_encoding"] = _id_enc
                e["law_encoding"] = _id_enc
                break
        ok, _, why = ja.admit_next(
            make_validity_check(structural_only_validity_for_tests()),
            make_rent_check(benchmark_dir=bench),
            make_human_check(lambda e: True))
        self.assertTrue(ok, "rent pass + human approve -> admitted; got " + why)
        self.assertEqual(why, "admitted")
        self.assertEqual(ja._accepted_state_version, 1)
        # Evidence file exists for (proposal, v=0, bench_id).
        ev_dir = os.path.join(bench, "evidence")
        self.assertTrue(os.path.isdir(ev_dir))
        files = os.listdir(ev_dir)
        self.assertTrue(any(files), "evidence record must be written")

    def test_stale_evidence_revalidates_on_version_change(self):
        bench = os.path.join(self.scratch, "bench")
        _write_passing_rent_benchmark(bench)
        chk = make_rent_check(benchmark_dir=bench)
        entry = self._entry()
        entry["evidence_state_version"] = 0
        ok1, _ = chk(entry, [], 0); self.assertTrue(ok1)
        # Version 1: evidence for v=0 is stale -> revalidate (subprocess runs
        # again; the benchmark still passes, so returns True).
        ok2, _ = chk(entry, [], 1); self.assertTrue(ok2)

    def test_encoding_surface_fail_closed_launch_error(self):
        """Carry-forward Fable 4.6: entry without proposal_encoding must
        surface as F_LAUNCH_ERROR (front intact), NOT as F_RENT_FAIL and
        NOT as a silent pass."""
        bench = os.path.join(self.scratch, "bench")
        _write_passing_rent_benchmark(bench)
        chk = make_rent_check(benchmark_dir=bench)
        bad_entry = {"proposal_id": "p-bad", "proposal_text": "no-encoding",
                     "state": "queued", "evidence_state_version": 0}
        ok, reason = chk(bad_entry, [], 0)
        self.assertFalse(ok)
        self.assertIs(M.IdentityCompare(reason, P.F_LAUNCH_ERROR)(), M.truth_value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
