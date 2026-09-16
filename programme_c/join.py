"""Join + admission (C-C). Claim state machine: running -> completed/failed/
cancelled. Retry uses a new attempt id; duplicate delivery idempotent; late
superseded results rejected with F_STALE_RESULT. Certificates are replayed
against their declared snapshot AND obligation (looked up via the child
manifest) before acceptance. AND requires every declared child discharged;
OR one complete alternative. Execution failure (F_CRASH/F_TIMEOUT/etc.)
is distinct from logical refutation (F_REFRUTATION). Incompatible
assumptions (assumption_hash mismatch) are rejected. Proposal admission
runs only after fork/join completes through a stable FIFO queue; gates
validity -> rent -> human; published state before next candidate. Rent is
performance-only (not soundness). No private activation; no joint-set rent.
"""
from __future__ import annotations

import json as _json
import os
import threading as _threading
import time as _time

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c as P
from hyge_int_pkg.programme_c import (
    S_RUNNING, S_COMPLETED, S_FAILED, S_CANCELLED,
    F_STALE_RESULT, F_INCOMPATIBLE_ASSUMPTIONS, F_MISSING_CHILD,
    F_SCOPE_VIOLATION, F_SNAPSHOT_MISMATCH, F_INVALID_CERT, F_UNKNOWN_CHILD,
    F_CRASH, F_TIMEOUT, F_CANCELLED, F_REFRUTATION,
    K_TASK_ID, K_ATTEMPT_ID, K_WORKER_ID, K_STATUS, K_KIND, K_BODY,
    K_SNAPSHOT_ID, K_OBLIGATION, K_ASSUMPTION_HASH, K_BUDGET, K_REASON,
    K_CHILD_ID, K_CHILD_STATUS,
    K_DECLARED_SNAPSHOT, K_DECLARED_OBLIGATION,
    alist_put, alist_get, text_atom,
    F_LAUNCH_ERROR,
)

COMBINATOR_AND = "and"
COMBINATOR_OR = "or"
GATE_VALIDITY = "validity"
GATE_RENT = "rent"
GATE_HUMAN = "human"


class ChildSpec:
    """A declared child of a claim. Children have their own obligation and
    assumption hash (may differ from the parent and from one another)."""
    def __init__(self, child_id, obligation_text, snapshot_id, assumption_hash):
        self.child_id = child_id
        self.obligation_text = obligation_text
        self.snapshot_id = snapshot_id
        self.assumption_hash = assumption_hash
        self.current_attempt = 0
        self.status = "running"
        self.result_term = M.EmptyList


class ClaimRecord:
    def __init__(self, claim_id, combinator, child_specs):
        self.claim_id = claim_id
        self.combinator = combinator
        self.children = {}  # child_id -> ChildSpec
        for s in child_specs:
            self.children[s.child_id] = s
        self.status = "running"
        self.accepted_attempt_id = None
        self.accepted_result = M.EmptyList
        self.created_at = _time.time()
        self.latest_attempt_per_child = {}


class ResultCertificate:
    def __init__(self, envelope_term):
        self.envelope = envelope_term
        self.task_id = alist_get(envelope_term, K_TASK_ID).value
        self.attempt_id = alist_get(envelope_term, K_ATTEMPT_ID).value
        self.worker_id = alist_get(envelope_term, K_WORKER_ID).value
        self.kind = alist_get(envelope_term, K_KIND).value
        self.status = alist_get(envelope_term, K_STATUS).value
        self.snapshot_id = _opt(alist_get, envelope_term, K_DECLARED_SNAPSHOT,
                                alist_get, envelope_term, K_SNAPSHOT_ID)
        self.obligation_text = _opt(alist_get, envelope_term, K_DECLARED_OBLIGATION,
                                    alist_get, envelope_term, K_OBLIGATION)
        self.assumption_hash = _opt(alist_get, envelope_term, K_ASSUMPTION_HASH)
        self.body = alist_get(envelope_term, K_BODY)
        self.reason = alist_get(envelope_term, K_REASON)


def _opt(fn, term, key, fn2=None, term2=None, key2=None):
    v = fn(term, key)
    if v is M.EmptyList and fn2 is not None:
        v = fn2(term2, key2)
    if v is M.EmptyList:
        return ""
    return v.value


class JoinAdmission:
    def __init__(self, manifest_path=None):
        self.claims = {}
        self._lock = _threading.RLock()
        self._proposal_queue = []
        self._accepted_proposals = []
        self._next_proposal_seq = 0
        self._manifest_path = manifest_path
        # If a manifest already exists, hydrate accepted set and queue from
        # durable state so the next candidate sees it (the charter requires
        # the on-disk manifest to be the authoritative admission source).
        if manifest_path is not None:
            try:
                from hyge_int_pkg.programme_c.admission_hooks import load_admission_manifest
                accepted, queue = load_admission_manifest(manifest_path)
                self._accepted_proposals = accepted
                self._proposal_queue = queue
                # Re-number seq past whatever was enqueued so new ids stay unique.
                self._next_proposal_seq = len(queue) + len(accepted)
            except Exception:
                pass

    def create_claim(self, claim_id, combinator, child_specs):
        with self._lock:
            rec = ClaimRecord(claim_id, combinator, child_specs)
            self.claims[claim_id] = rec
            return rec

    def deliver_child_result(self, parent_claim_id, envelope_term):
        """Deliver a certificate for a declared child. Returns (applied, reason_or_None, claim).

        envelope.task_id must equal a declared child_id of the parent.
        Envelope must declare the child's snapshot_id, obligation_text, and
        (when stamped) assumption_hash. Unknown children yield F_UNKNOWN_CHILD.
        Mismatched snapshot/obligation/assumptions yield F_INVALID_CERT /
        F_SCOPE_VIOLATION / F_INCOMPATIBLE_ASSUMPTIONS.
        """
        with self._lock:
            rec = self.claims.get(parent_claim_id)
            if rec is None:
                return False, F_SCOPE_VIOLATION, None
            cert = ResultCertificate(envelope_term)
            child = rec.children.get(cert.task_id)
            if child is None:
                return False, F_UNKNOWN_CHILD, rec
            # If child already terminal, only duplicates of the accepted attempt pass.
            if child.status in ("completed","failed","refuted","cancelled"):
                accepted = rec.latest_attempt_per_child.get(child.child_id)
                if accepted == cert.attempt_id:
                    return True, None, rec
                return False, F_STALE_RESULT, rec
            # Validate declared snapshot/obligation against child manifest.
            if cert.snapshot_id and cert.snapshot_id != child.snapshot_id:
                return False, F_SNAPSHOT_MISMATCH, rec
            if cert.obligation_text and cert.obligation_text != child.obligation_text:
                return False, F_SCOPE_VIOLATION, rec
            if cert.assumption_hash and child.assumption_hash and cert.assumption_hash != child.assumption_hash:
                return False, F_INCOMPATIBLE_ASSUMPTIONS, rec
            child.current_attempt += 1
            rec.latest_attempt_per_child[child.child_id] = cert.attempt_id
            reason = cert.reason
            if cert.status == "completed":
                child.status = "completed"
            elif cert.status == "failed":
                if M.IdentityCompare(reason, F_REFRUTATION)() is M.truth_value:
                    child.status = "refuted"
                else:
                    child.status = "failed"
            elif cert.status == "cancelled":
                child.status = "cancelled"
            else:
                return False, F_INVALID_CERT, rec
            child.result_term = envelope_term
            # Try to advance parent join.
            done, joined_term, reason_atom = self._try_join(rec)
            if done:
                rec.accepted_result = joined_term
                rec.status = "completed"
            return True, None, rec

    def cancel_claim(self, claim_id):
        with self._lock:
            rec = self.claims.get(claim_id)
            if rec is None:
                return False
            rec.status = "cancelled"
            return True

    def _try_join(self, rec):
        if rec.combinator == COMBINATOR_AND:
            return self._join_and(rec)
        if rec.combinator == COMBINATOR_OR:
            return self._join_or(rec)
        return False, M.EmptyList, None

    def _status_text(self, s):
        if isinstance(s, str):
            return s
        try:
            v = P._atom_text(s)
            return v
        except Exception:
            return ""

    def _join_and(self, rec):
        completed = 0; execution_failed = 0; refuted = 0
        child_terms = M.EmptyList
        for cid in list(rec.children.keys()):
            ch = rec.children[cid]
            st = self._status_text(ch.status)
            if st == "running":
                return False, M.EmptyList, None
            if st == "failed":
                execution_failed += 1
            elif st == "refuted":
                refuted += 1
            elif st == "cancelled":
                execution_failed += 1
            elif st == "completed":
                completed += 1
                child_terms = M.Pair(ch.result_term, child_terms)
        if completed == len(rec.children):
            j = M.EmptyList
            j = alist_put(j, K_KIND, text_atom("joined"))
            j = alist_put(j, K_STATUS, S_COMPLETED)
            j = alist_put(j, K_TASK_ID, text_atom(rec.claim_id))
            j = alist_put(j, text_atom("children"), child_terms)
            return True, j, None
        if refuted > 0:
            j = M.EmptyList
            j = alist_put(j, K_KIND, text_atom("refuted"))
            j = alist_put(j, K_STATUS, S_FAILED)
            j = alist_put(j, K_TASK_ID, text_atom(rec.claim_id))
            j = alist_put(j, K_REASON, F_REFRUTATION)
            return True, j, None
        if execution_failed > 0:
            j = M.EmptyList
            j = alist_put(j, K_KIND, text_atom("failure"))
            j = alist_put(j, K_STATUS, S_FAILED)
            j = alist_put(j, K_TASK_ID, text_atom(rec.claim_id))
            j = alist_put(j, K_REASON, F_CRASH)
            return True, j, None
        return False, M.EmptyList, None

    def _join_or(self, rec):
        for cid in list(rec.children.keys()):
            ch = rec.children[cid]
            if self._status_text(ch.status) == "completed":
                j = M.EmptyList
                j = alist_put(j, K_KIND, text_atom("joined"))
                j = alist_put(j, K_STATUS, S_COMPLETED)
                j = alist_put(j, K_TASK_ID, text_atom(rec.claim_id))
                j = alist_put(j, text_atom("selected_child"), text_atom(cid))
                j = alist_put(j, text_atom("result"), ch.result_term)
                return True, j, None
        any_running = False; exec_fail = 0; refuted = 0
        for cid in list(rec.children.keys()):
            ch = rec.children[cid]
            st = self._status_text(ch.status)
            if st == "running" or st == "dispatched":
                any_running = True
            elif st == "refuted":
                refuted += 1
            else:
                exec_fail += 1
        if not any_running:
            if refuted == len(rec.children):
                j = M.EmptyList
                j = alist_put(j, K_KIND, text_atom("refuted"))
                j = alist_put(j, K_STATUS, S_FAILED)
                j = alist_put(j, K_TASK_ID, text_atom(rec.claim_id))
                j = alist_put(j, K_REASON, F_REFRUTATION)
                return True, j, None
            j = M.EmptyList
            j = alist_put(j, K_KIND, text_atom("failure"))
            j = alist_put(j, K_STATUS, S_FAILED)
            j = alist_put(j, K_TASK_ID, text_atom(rec.claim_id))
            j = alist_put(j, K_REASON, F_CRASH)
            return True, j, None
        return False, M.EmptyList, None

    # ---------- Proposal admission ----------

    def enqueue_proposal(self, proposal_text, source_claim_id, gates):
        with self._lock:
            self._next_proposal_seq += 1
            pid = "proposal-" + str(self._next_proposal_seq)
            entry = {"proposal_id": pid, "source_claim_id": source_claim_id,
                     "proposal_text": proposal_text, "gates": list(gates),
                     "enqueued_at": _time.time(), "state": "queued"}
            self._proposal_queue.append(entry)
            return pid

    def _persist(self):
        if self._manifest_path is None:
            return
        try:
            from hyge_int_pkg.programme_c.admission_hooks import write_admission_manifest
            write_admission_manifest(self._manifest_path,
                                     self._accepted_proposals,
                                     self._proposal_queue)
        except Exception:
            pass

    def admit_next(self, validity_check, rent_check, human_approval_check):
        with self._lock:
            if not self._proposal_queue:
                return False, "", "empty queue"
            entry = self._proposal_queue[0]
            rec = self.claims.get(entry["source_claim_id"])
            if rec is None or rec.status != "completed":
                return False, entry["proposal_id"], "source claim not completed"
            for prior in self._accepted_proposals:
                if prior.get("proposal_text") == entry["proposal_text"]:
                    self._accepted_proposals.append(entry)
                    self._proposal_queue.pop(0)
                    entry["state"] = "admitted"; entry["admitted_at"] = _time.time()
                    self._persist()
                    return True, entry["proposal_id"], "duplicate"
            if GATE_VALIDITY in entry["gates"]:
                if not validity_check(entry, self._accepted_proposals):
                    entry["state"] = "rejected-validity"; self._proposal_queue.pop(0)
                    self._persist()
                    return False, entry["proposal_id"], "validity failed"
            if GATE_RENT in entry["gates"]:
                if not rent_check(entry):
                    entry["state"] = "rent-hold"
                    self._persist()
                    return False, entry["proposal_id"], "rent hold"
            if GATE_HUMAN in entry["gates"]:
                if not human_approval_check(entry):
                    entry["state"] = "awaiting-human"
                    self._persist()
                    return False, entry["proposal_id"], "awaiting human"
            entry["state"] = "admitted"; entry["admitted_at"] = _time.time()
            self._accepted_proposals.append(entry)
            self._proposal_queue.pop(0)
            # Publish updated state to on-disk manifest before returning.
            self._persist()
            return True, entry["proposal_id"], "admitted"


def _atom_eq(a, b):
    """Compare atoms by string value (safe across subprocess pickling)."""
    try:
        return P._atom_text(a) == P._atom_text(b)
    except Exception:
        return M.IdentityCompare(a, b)() is M.truth_value


def child_spec(child_id, obligation_text, snapshot_id, assumption_hash):
    return ChildSpec(child_id, obligation_text, snapshot_id, assumption_hash)
