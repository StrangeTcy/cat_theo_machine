"""C-C gate-hook + on-disk admission manifest integration tests. Validates:

  * admit_next calls validity/rent/human callables in order;
  * validity fail rejects; rent hold leaves the proposal at the front;
    human-hold leaves it at the front; explicit approval admits;
  * on-disk manifest is written before admit_next returns, and a freshly
    constructed JoinAdmission re-hydrates from that manifest (so the next
    candidate observes durable, not just in-memory, state).
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
    default_validity_check, default_rent_check, default_human_approval,
)
from hyge_int_pkg.programme_c.join import (
    COMBINATOR_AND, GATE_VALIDITY, GATE_RENT, GATE_HUMAN,
    child_spec,
)


def _fake_completed_claim(ja, claim_id="c-1"):
    # Single completed AND child ("leaf") so source-claim can be admitted.
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

    def test_gate_order_validity_then_rent_then_human_then_admit(self):
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        calls = []

        def v_check(entry, accepted):
            calls.append("validity"); return default_validity_check(entry, accepted)
        def r_check(entry):
            calls.append("rent"); return True
        # First call: human denies -> hold; second call: human approves.
        self._human_calls = 0
        def h_check(entry):
            self._human_calls += 1
            calls.append("human-" + str(self._human_calls))
            return self._human_calls >= 2
        ja.enqueue_proposal("proposal-ok", "c-1", [GATE_VALIDITY, GATE_RENT, GATE_HUMAN])
        ok, pid, reason = ja.admit_next(v_check, r_check, h_check)
        self.assertFalse(ok, "expected human hold first")
        self.assertEqual(calls, ["validity", "rent", "human-1"])
        self.assertEqual(reason, "awaiting human")
        # Manifest must exist and reflect the hold state.
        self.assertTrue(os.path.isfile(self.manifest))
        with open(self.manifest) as h:
            m = json.load(h)
        self.assertEqual(len(m["queue"]), 1)
        self.assertEqual(m["queue"][0]["state"], "awaiting-human")
        self.assertEqual(m["accepted"], [])
        # Second admit: human approves -> admitted, manifest updated.
        ok2, pid2, reason2 = ja.admit_next(v_check, r_check, h_check)
        self.assertTrue(ok2, "expected admission: " + reason2)
        with open(self.manifest) as h:
            m = json.load(h)
        self.assertEqual(m["queue"], [])
        self.assertEqual(len(m["accepted"]), 1)
        self.assertEqual(m["accepted"][0]["state"], "admitted")

    def test_manifest_rehydrated_on_construction(self):
        ja1 = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja1, "c-1")
        ja1.enqueue_proposal("accepted-law", "c-1", [GATE_VALIDITY])
        # Default validity passes, default rent passes (no gate), default human
        # denies only if GATE_HUMAN present — it isn't.
        ok, _pid, reason = ja1.admit_next(default_validity_check,
                                          lambda e: default_rent_check(e),
                                          lambda e: True)
        self.assertTrue(ok, reason)
        # Fresh JoinAdmission sees the accepted proposal on disk.
        ja2 = J.JoinAdmission(manifest_path=self.manifest)
        self.assertEqual(len(ja2._accepted_proposals), 1)
        self.assertEqual(ja2._accepted_proposals[0]["proposal_text"], "accepted-law")

    def test_validity_failure_rejects_from_front(self):
        ja = J.JoinAdmission(manifest_path=self.manifest)
        _fake_completed_claim(ja, "c-1")
        ja.enqueue_proposal("bad-one", "c-1", [GATE_VALIDITY])
        ja.enqueue_proposal("good-one", "c-1", [GATE_VALIDITY])
        ok, _pid, reason = ja.admit_next(lambda e, a: False,
                                          lambda e: True, lambda e: True)
        self.assertFalse(ok)
        self.assertEqual(reason, "validity failed")
        # Next candidate is now at the front.
        ok2, _pid2, reason2 = ja.admit_next(lambda e, a: True,
                                             lambda e: True, lambda e: True)
        self.assertTrue(ok2, reason2)
        self.assertEqual(ja._accepted_proposals[-1]["proposal_text"], "good-one")


if __name__ == "__main__":
    unittest.main(verbosity=2)
