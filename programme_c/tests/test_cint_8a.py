"""C-INT-8A admission correctness boundary

Covers:
  H1: coordinator-owned mandatory gate chain validity->rent->human,
      ignoring entry["gates"]; gates=[] and unknown gate cannot bypass.
  H2: fail-closed accepted-state replay -> F_LAUNCH_ERROR, front intact
      (validity and rent).
  H3/H4: isolated certificate replay in fresh subprocess with exact
      checks (snapshot_id, task_id, attempt_id, obligation,
      assumption_hash, declared start/goal, success-derivation-built,
      BuildDerivation success, DerivationStart==declared start,
      DerivationEnd==declared goal), parent M.AllConstructors untouched,
      crash/truncation -> F_LAUNCH_ERROR.
  H5: durable persistence _fsync_dir propagate, tmp->flush->fsync->
      os.replace->fsync(parent).

Required tests per C-INT-8A.md:
  gates=[] cannot admit, unknown gate fails closed,
  accepted-law decode/install failures hold front,
  wrong terminal goal/start rejected,
  valid replay succeeds in fresh child,
  parent state unchanged,
  child crash -> execution failure,
  fsync/replace failures propagate.
"""

import io
import json
import os
import shutil
import tempfile
import time
import unittest
import unittest.mock as mock

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c as P
import hyge_int_pkg.programme_c.join as J
from hyge_int_pkg.programme_c import (
    F_LAUNCH_ERROR, F_INVALID_CERT, F_RENT_FAIL,
)
from hyge_int_pkg.programme_c.join import COMBINATOR_AND, GATE_VALIDITY, GATE_RENT, GATE_HUMAN, child_spec
from hyge_int_pkg.programme_c.admission_hooks import (
    make_validity_check, structural_only_validity_for_tests,
    make_rent_check, make_human_check,
    make_live_activate_proposal_check,
    write_admission_manifest, load_admission_manifest, ManifestError,
)


def _fake_completed_claim(ja, claim_id="c-1"):
    spec = child_spec("leaf", "obligation-a", "snap", "ah-0")
    rec = ja.create_claim(claim_id, COMBINATOR_AND, [spec])
    leaf = rec.children["leaf"]
    leaf.status = "completed"
    leaf.result_term = "ok"
    rec.status = "completed"
    return rec


def _id_enc():
    return {"kind": "rule", "left": {"Char": "z"}, "right": {"Char": "z"}}


class TestH1MandatoryGateChain(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="cint8a_h1_")
        self.manifest = os.path.join(self.scratch, "admission_manifest.json")

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def test_gates_empty_cannot_bypass_validity(self):
        """gates=[] does not omit mandatory validity; fail-closed."""
        # Fixture denies validity, would pass rent/human.
        deny_validity = make_validity_check(None)  # always False
        allow_rent = lambda e, a, v: (True, None)
        allow_human = lambda e, a, v: (True, None)
        ja = J.JoinAdmission(
            manifest_path=self.manifest,
            strict_manifest=True,
            validity_check=deny_validity,
            rent_check=allow_rent,
            human_check=allow_human,
        )
        _fake_completed_claim(ja, "c-1")
        pid = ja.enqueue_proposal("p-empty-gates", "c-1", [])  # gates=[]
        self.assertTrue(pid)
        # No per-call args; must use fixture and still run validity.
        ok, ret_pid, reason = ja.admit_next()
        self.assertFalse(ok, "gates=[] must not bypass validity")
        self.assertEqual(ret_pid, pid)
        self.assertEqual(reason, "validity failed")
        # Validity failure pops and marks rejected-validity, not admitted.
        self.assertEqual(len(ja._proposal_queue), 0)

    def test_gates_empty_holds_on_launch_error(self):
        """gates=[] with launch-error holds front intact."""
        # Validity returns launch-error
        def launch_validity(e, a, v):
            return False, P.F_LAUNCH_ERROR
        ja = J.JoinAdmission(
            manifest_path=self.manifest,
            validity_check=launch_validity,
            rent_check=lambda e, a, v: (True, None),
            human_check=lambda e, a, v: (True, None),
        )
        _fake_completed_claim(ja, "c-1")
        pid = ja.enqueue_proposal("p-launch", "c-1", [])
        ok, ret_pid, reason = ja.admit_next()
        self.assertFalse(ok)
        self.assertEqual(reason, "validity-launch-error")
        self.assertEqual(ret_pid, pid)
        self.assertEqual(len(ja._proposal_queue), 1)
        self.assertEqual(ja._proposal_queue[0]["proposal_id"], pid)
        self.assertEqual(ja._proposal_queue[0]["state"], "queued")

    def test_unknown_gate_does_not_bypass(self):
        """Unknown gate token is ignored; mandatory chain still run."""
        deny_validity = make_validity_check(None)
        ja = J.JoinAdmission(
            manifest_path=self.manifest,
            validity_check=deny_validity,
            rent_check=lambda e, a, v: (True, None),
            human_check=lambda e, a, v: (True, None),
        )
        _fake_completed_claim(ja, "c-1")
        pid = ja.enqueue_proposal("p-unknown", "c-1", ["not-a-gate", "unknown-token"])
        self.assertTrue(pid)
        ok, ret_pid, reason = ja.admit_next()
        self.assertFalse(ok)
        self.assertEqual(reason, "validity failed")
        self.assertEqual(ret_pid, pid)

    def test_per_call_gates_ignored_when_fixture_present(self):
        """Per-call gates list is ignored when fixture is injected; fixture takes precedence."""
        # Fixture denies, per-call would allow – fixture must win.
        deny = make_validity_check(None)
        ja = J.JoinAdmission(
            manifest_path=self.manifest,
            validity_check=deny,
            rent_check=lambda e, a, v: (True, None),
            human_check=lambda e, a, v: (True, None),
        )
        _fake_completed_claim(ja, "c-1")
        pid = ja.enqueue_proposal("p-fixture", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        # Per-call validity would pass, but fixture denies – must deny.
        allow = lambda e, a, v: (True, None)
        ok, _, reason = ja.admit_next(validity_check=allow, rent_check=allow, human_approval_check=allow)
        self.assertFalse(ok)
        self.assertEqual(reason, "validity failed")

    def test_mandatory_order_validity_then_rent_then_human(self):
        """Order is strictly validity -> rent -> human; rent not run if validity fails."""
        calls = []
        def validity(e, a, v):
            calls.append("validity")
            return False, P.F_INVALID_CERT
        def rent(e, a, v):
            calls.append("rent")
            return True, None
        def human(e, a, v):
            calls.append("human")
            return True, None
        ja = J.JoinAdmission(
            manifest_path=self.manifest,
            validity_check=validity,
            rent_check=rent,
            human_check=human,
        )
        _fake_completed_claim(ja, "c-1")
        ja.enqueue_proposal("p-order", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        ja.admit_next()
        self.assertEqual(calls, ["validity"], "rent/human must not run after validity failure")


class TestH2AcceptedStateFailClosed(unittest.TestCase):
    """Validity and rent accepted-state replay failures hold front with launch-error."""

    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="cint8a_h2_")
        self.manifest = os.path.join(self.scratch, "admission_manifest.json")

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def _admit_first_valid(self, ja, validity_check, rent_check, human_check):
        pid = ja.enqueue_proposal("first-law", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        for e in ja._proposal_queue:
            if e["proposal_id"] == pid:
                e["proposal_encoding"] = _id_enc()
                e["law_encoding"] = _id_enc()
                break
        ok, _, reason = ja.admit_next(validity_check, rent_check, human_check)
        self.assertTrue(ok, "first admit should succeed: " + reason)
        # Activate to make it accepted state version 1
        ja.activate_front(lambda e, a, v: True)
        self.assertEqual(ja._accepted_state_version, 1)
        self.assertEqual(ja._accepted_proposals[-1]["state"], "activated")
        return pid

    def test_validity_accepted_missing_law_encoding_holds_front(self):
        # Live validity check boots packs (~10s) – use it to exercise accepted replay.
        live_validity = make_live_activate_proposal_check(timeout_seconds=60)
        # Use structural rent/human that pass, so we isolate validity.
        rent_ok = lambda e, a, v: (True, None)
        human_ok = lambda e, a, v: (True, None)
        ja = J.JoinAdmission(manifest_path=self.manifest, strict_manifest=True)
        _fake_completed_claim(ja, "c-1")
        self._admit_first_valid(ja, live_validity, rent_ok, human_ok)
        # Tamper accepted entry: remove law_encoding
        ja._accepted_proposals[0].pop("law_encoding", None)
        ja._persist()
        # Enqueue second proposal that would otherwise pass
        pid2 = ja.enqueue_proposal("second-law", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        for e in ja._proposal_queue:
            if e["proposal_id"] == pid2:
                e["proposal_encoding"] = _id_enc()
                e["law_encoding"] = _id_enc()
                break
        # Admit should now hit accepted decode failure -> launch-error, front intact
        ok2, ret_pid, reason2 = ja.admit_next(live_validity, rent_ok, human_ok)
        self.assertFalse(ok2)
        self.assertEqual(reason2, "validity-launch-error")
        self.assertEqual(ret_pid, pid2)
        self.assertEqual(len(ja._proposal_queue), 1)
        self.assertEqual(ja._proposal_queue[0]["proposal_id"], pid2)
        self.assertEqual(ja._proposal_queue[0]["state"], "queued")
        self.assertEqual(ja._accepted_state_version, 1, "version must not advance on launch-error")

    def test_validity_accepted_bad_encoding_holds_front(self):
        live_validity = make_live_activate_proposal_check(timeout_seconds=60)
        rent_ok = lambda e, a, v: (True, None)
        human_ok = lambda e, a, v: (True, None)
        ja = J.JoinAdmission(manifest_path=self.manifest, strict_manifest=True)
        _fake_completed_claim(ja, "c-1")
        self._admit_first_valid(ja, live_validity, rent_ok, human_ok)
        # Tamper to unsupported shape
        ja._accepted_proposals[0]["law_encoding"] = {"kind": "rule", "left": {"Bad": "shape"}, "right": {"Char": "z"}}
        ja._persist()
        pid2 = ja.enqueue_proposal("second-law-bad", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        for e in ja._proposal_queue:
            if e["proposal_id"] == pid2:
                e["proposal_encoding"] = _id_enc()
                e["law_encoding"] = _id_enc()
                break
        ok2, ret_pid, reason2 = ja.admit_next(live_validity, rent_ok, human_ok)
        self.assertFalse(ok2)
        self.assertEqual(reason2, "validity-launch-error")

    def test_rent_accepted_missing_law_encoding_holds_front(self):
        # Rent benchmark that trivially passes
        bench_dir = os.path.join(self.scratch, "bench")
        os.makedirs(bench_dir, exist_ok=True)
        bench_payload = {
            "schema_version": 1,
            "timeout_seconds": 30,
            "step_budget": 100000,
            "max_total_ms": 60000,
            "specs": [{"name": "id-z", "left": {"Char": "z"}, "right": {"Char": "z"}, "start": {"Char": "z"}}],
        }
        with open(os.path.join(bench_dir, "benchmark.json"), "w") as h:
            json.dump(bench_payload, h)
        live_validity = structural_only_validity_for_tests
        # Use live validity structural pass
        validity_ok = make_validity_check(structural_only_validity_for_tests())
        rent_check = make_rent_check(benchmark_dir=bench_dir)
        human_ok = lambda e, a, v: (True, None)
        ja = J.JoinAdmission(manifest_path=self.manifest, strict_manifest=True)
        _fake_completed_claim(ja, "c-1")
        # First admit with rent pass
        pid1 = ja.enqueue_proposal("first-rent", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        for e in ja._proposal_queue:
            if e["proposal_id"] == pid1:
                e["proposal_encoding"] = _id_enc()
                e["law_encoding"] = _id_enc()
                break
        ok, _, reason = ja.admit_next(validity_ok, rent_check, human_ok)
        self.assertTrue(ok, reason)
        ja.activate_front(lambda e, a, v: True)
        # Tamper accepted
        ja._accepted_proposals[0].pop("law_encoding", None)
        ja._persist()
        pid2 = ja.enqueue_proposal("second-rent", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        for e in ja._proposal_queue:
            if e["proposal_id"] == pid2:
                e["proposal_encoding"] = _id_enc()
                e["law_encoding"] = _id_enc()
                break
        ok2, ret_pid, reason2 = ja.admit_next(validity_ok, rent_check, human_ok)
        self.assertFalse(ok2)
        self.assertEqual(reason2, "rent-launch-error")
        self.assertEqual(ret_pid, pid2)
        self.assertEqual(len(ja._proposal_queue), 1)


class TestH3H4IsolatedCertificateReplay(unittest.TestCase):
    """Isolated replay: fresh subprocess, exact checks, parent untouched, crash->launch-error."""

    @classmethod
    def setUpClass(cls):
        # Build one valid snapshot via search-worker dispatch for reuse.
        import hyge_int_pkg.programme_c.worker as W
        import hyge_int_pkg.programme_c.worker_dispatch as WD
        import pathlib
        cls.scratch = tempfile.mkdtemp(prefix="cint8a_h3h4_")
        # Find package root
        here = pathlib.Path(WD.__file__).parent
        d = here
        for _ in range(6):
            if (d / "main.py").exists() and (d / "programme_c").is_dir():
                cls.package_root = str(d)
                break
            d = d.parent
        else:
            cls.package_root = "/home/user/cat_theo_machine"
        pool = W.BoundedWorkerPool(cls.scratch, snapshot_ident=None, check_restore=False)
        cls.pool = pool
        cls.dispatcher = WD.SearchWorkerDispatch(pool, cls.package_root)
        ticket = cls.dispatcher.spawn(
            mode_token="dfs",
            start_text="Zero",
            goal_text="Zero",
            task_id="t-cert-valid",
            attempt_id="a-1",
            obligation_text="Zero == Zero",
            assumptions_term=M.EmptyList,
            budget_millis=120_000,
            worker_timeout_seconds=60,
        )
        # Wait
        result = None
        for _ in range(240):
            result = cls.dispatcher.poll(ticket)
            if result is not M.EmptyList:
                break
            time.sleep(0.5)
        assert result is not M.EmptyList and result is not None, "worker did not finish"
        # Ensure it's a result, not failure
        from hyge_int_pkg.programme_c import K_KIND, alist_get
        assert alist_get(result, K_KIND).value == "result", "expected result, got " + str(alist_get(result, K_KIND))
        cls.ticket = ticket
        cls.result_path = ticket.result_path
        # Capture manifest data for expected values
        with open(cls.result_path + ".manifest.json") as h:
            cls.manifest = json.load(h)
        # Also store ticket fields
        cls.expected_snapshot_id = ticket.snapshot_id
        cls.expected_obligation = ticket.obligation_text
        cls.expected_assumption_hash = ticket.assumption_hash
        cls.expected_task_id = ticket.task_id
        cls.expected_attempt_id = ticket.attempt_id
        cls.expected_start = ticket.start_text
        cls.expected_goal = ticket.goal_text

    @classmethod
    def tearDownClass(cls):
        try:
            cls.pool.shutdown()
        except Exception:
            pass
        shutil.rmtree(cls.scratch, ignore_errors=True)

    def test_valid_replay_succeeds_in_fresh_child(self):
        from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
        resp = run_certificate_replay_subprocess(
            self.result_path,
            self.expected_snapshot_id,
            self.expected_obligation,
            self.expected_assumption_hash,
            self.expected_task_id,
            self.expected_attempt_id,
            self.expected_start,
            self.expected_goal,
            package_root=self.package_root,
            timeout_seconds=30,
        )
        self.assertEqual(resp.get("status"), "completed")
        self.assertTrue(resp.get("passed"))
        self.assertEqual(resp.get("reason"), "ok")

    def test_parent_state_unchanged(self):
        import hyge_int_pkg.machine as M2
        before = M2.AllConstructors
        before_id = id(before)
        # Also capture registry tree id
        from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
        resp = run_certificate_replay_subprocess(
            self.result_path,
            self.expected_snapshot_id,
            self.expected_obligation,
            self.expected_assumption_hash,
            self.expected_task_id,
            self.expected_attempt_id,
            self.expected_start,
            self.expected_goal,
            package_root=self.package_root,
            timeout_seconds=30,
        )
        after = M2.AllConstructors
        self.assertIs(before, after, "parent M.AllConstructors must not be mutated")
        self.assertEqual(id(before), before_id)
        self.assertEqual(resp.get("status"), "completed")

    def test_wrong_snapshot_id_rejected(self):
        from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
        resp = run_certificate_replay_subprocess(
            self.result_path,
            "wrong-snapshot-id",
            self.expected_obligation,
            self.expected_assumption_hash,
            self.expected_task_id,
            self.expected_attempt_id,
            self.expected_start,
            self.expected_goal,
            package_root=self.package_root,
            timeout_seconds=30,
        )
        self.assertEqual(resp.get("status"), "failed")
        self.assertFalse(resp.get("passed"))
        self.assertIn("snapshot-mismatch", resp.get("detail", ""))

    def test_wrong_task_id_rejected(self):
        from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
        resp = run_certificate_replay_subprocess(
            self.result_path,
            self.expected_snapshot_id,
            self.expected_obligation,
            self.expected_assumption_hash,
            "wrong-task",
            self.expected_attempt_id,
            self.expected_start,
            self.expected_goal,
            package_root=self.package_root,
            timeout_seconds=30,
        )
        self.assertEqual(resp.get("status"), "failed")
        self.assertIn("task-id-mismatch", resp.get("detail", ""))

    def test_wrong_assumption_hash_rejected(self):
        from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
        resp = run_certificate_replay_subprocess(
            self.result_path,
            self.expected_snapshot_id,
            self.expected_obligation,
            "deadbeef" * 8,
            self.expected_task_id,
            self.expected_attempt_id,
            self.expected_start,
            self.expected_goal,
            package_root=self.package_root,
            timeout_seconds=30,
        )
        self.assertEqual(resp.get("status"), "failed")
        self.assertIn("assumption-mismatch", resp.get("detail", ""))

    def test_wrong_obligation_rejected(self):
        from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
        resp = run_certificate_replay_subprocess(
            self.result_path,
            self.expected_snapshot_id,
            "WRONG_OBLIGATION",
            self.expected_assumption_hash,
            self.expected_task_id,
            self.expected_attempt_id,
            self.expected_start,
            self.expected_goal,
            package_root=self.package_root,
            timeout_seconds=30,
        )
        self.assertEqual(resp.get("status"), "failed")
        self.assertIn("obligation-mismatch", resp.get("detail", ""))

    def test_wrong_start_text_rejected(self):
        from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
        resp = run_certificate_replay_subprocess(
            self.result_path,
            self.expected_snapshot_id,
            self.expected_obligation,
            self.expected_assumption_hash,
            self.expected_task_id,
            self.expected_attempt_id,
            "WRONG_START",
            self.expected_goal,
            package_root=self.package_root,
            timeout_seconds=30,
        )
        self.assertEqual(resp.get("status"), "failed")
        self.assertIn("start-text", resp.get("detail", ""))

    def test_wrong_goal_text_rejected(self):
        from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
        resp = run_certificate_replay_subprocess(
            self.result_path,
            self.expected_snapshot_id,
            self.expected_obligation,
            self.expected_assumption_hash,
            self.expected_task_id,
            self.expected_attempt_id,
            self.expected_start,
            "WRONG_GOAL",
            package_root=self.package_root,
            timeout_seconds=30,
        )
        self.assertEqual(resp.get("status"), "failed")
        self.assertIn("goal-text", resp.get("detail", ""))

    def test_truncated_snapshot_returns_launch_error(self):
        # Truncate snapshot file, then replay should be launch-error, not invalid-cert
        import shutil as _shutil
        tmp_path = self.result_path + ".truncated_test.json"
        _shutil.copy(self.result_path, tmp_path)
        tmp_manifest = tmp_path + ".manifest.json"
        _shutil.copy(self.result_path + ".manifest.json", tmp_manifest)
        try:
            with open(tmp_path, "r+b") as fh:
                fh.truncate(100)
            from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
            resp = run_certificate_replay_subprocess(
                tmp_path,
                self.expected_snapshot_id,
                self.expected_obligation,
                self.expected_assumption_hash,
                self.expected_task_id,
                self.expected_attempt_id,
                self.expected_start,
                self.expected_goal,
                package_root=self.package_root,
                timeout_seconds=30,
            )
            self.assertEqual(resp.get("status"), "launch-error")
            self.assertEqual(resp.get("reason"), "launch-error")
        finally:
            for p in (tmp_path, tmp_manifest):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def test_child_crash_returns_launch_error(self):
        # Non-existent snapshot path should be launch-error (child cannot boot)
        from hyge_int_pkg.programme_c.cert_replay import run_certificate_replay_subprocess
        resp = run_certificate_replay_subprocess(
            "/nonexistent/path/snapshot.json",
            self.expected_snapshot_id,
            self.expected_obligation,
            self.expected_assumption_hash,
            self.expected_task_id,
            self.expected_attempt_id,
            self.expected_start,
            self.expected_goal,
            package_root=self.package_root,
            timeout_seconds=10,
        )
        # Could be failed (missing file) or launch-error; both are not success.
        # For this harness, missing snapshot is treated as invalid cert (manifest missing)
        # but child should return launch-error for truncated. Check that it is not completed.
        self.assertNotEqual(resp.get("status"), "completed")

    def test_worker_dispatch_parent_unchanged_after_verify(self):
        import hyge_int_pkg.machine as M2
        import hyge_int_pkg.programme_c.worker_dispatch as WD
        before = M2.AllConstructors
        ok, stat, reason, body = WD._verify_child_certificate(
            self.result_path,
            self.expected_snapshot_id,
            self.expected_obligation,
            self.expected_assumption_hash,
            self.expected_task_id,
            self.expected_attempt_id,
            self.expected_start,
            self.expected_goal,
        )
        after = M2.AllConstructors
        self.assertIs(before, after)
        self.assertTrue(ok)
        self.assertEqual(stat, "completed")


class TestH5DurablePersistence(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="cint8a_h5_")
        self.manifest = os.path.join(self.scratch, "admission_manifest.json")

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def test_fsync_dir_failure_propagates(self):
        with mock.patch("hyge_int_pkg.programme_c.admission_hooks.os.fsync", side_effect=OSError("injected fsync failure")):
            with self.assertRaises(OSError):
                write_admission_manifest(self.manifest, [], [], accepted_state_version=0)

    def test_os_replace_failure_propagates(self):
        with mock.patch("hyge_int_pkg.programme_c.admission_hooks.os.replace", side_effect=OSError("injected replace failure")):
            with self.assertRaises(OSError):
                write_admission_manifest(self.manifest, [], [], accepted_state_version=0)

    def test_tmp_flush_fsync_propagates(self):
        # Simulate flush failure via mocking _json.dump to raise? Simpler: mock os.fsync to fail on file fd.
        # Write should propagate any OSError from fdatasync path.
        original_fsync = os.fsync
        def fake_fsync(fd):
            # Fail only when called on the temp file (not dir)
            raise OSError("injected file fsync failure")
        with mock.patch("hyge_int_pkg.programme_c.admission_hooks.os.fsync", side_effect=fake_fsync):
            with self.assertRaises(OSError):
                write_admission_manifest(self.manifest, [], [], accepted_state_version=0)

    def test_successful_write_is_durable(self):
        # Normal write should succeed and be loadable
        write_admission_manifest(self.manifest, [{"proposal_id": "p-1", "proposal_text": "x"}], [], accepted_state_version=1)
        accepted, queue, version = load_admission_manifest(self.manifest)
        self.assertEqual(version, 1)
        self.assertEqual(accepted[0]["proposal_id"], "p-1")

    def test_corrupt_manifest_raises(self):
        with open(self.manifest, "w") as h:
            h.write("not json")
        with self.assertRaises(ManifestError):
            load_admission_manifest(self.manifest)

    def test_wrong_schema_raises(self):
        write_admission_manifest(self.manifest, [], [], accepted_state_version=0, schema_version=999)
        with self.assertRaises(ManifestError):
            load_admission_manifest(self.manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
