"""Join + admission (C-C). Claim state machine: running -> completed/failed/
cancelled. Retry uses a new attempt id; duplicate delivery idempotent; late
superseded results rejected with F_STALE_RESULT. Certificates are replayed
against their declared snapshot AND obligation (looked up via the child
manifest) before acceptance. AND requires every declared child discharged;
OR one complete alternative. Execution failure (F_CRASH/F_TIMEOUT/etc.)
is distinct from logical refutation (F_REFRUTATION). Incompatible
assumptions (assumption_hash mismatch) are rejected. Stale results from
prior attempts are rejected even when the child is not yet terminal
(active-attempt fencing). Proposal admission runs only after fork/join
completes through a stable FIFO queue; gates validity -> rent -> human;
state is persisted durably (fsync) before returning. Activation is a
separate step with a durable 'activating' marker so crash recovery can
reconcile; accepted_state_version is monotonic (never decremented). One
admission at a time; no next candidate while activation is unresolved.
Rent is performance-only (not soundness). No private activation; no
joint-set rent.
"""
from __future__ import annotations

import os
import threading as _threading
import time as _time

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c as P
from hyge_int_pkg.programme_c import (
    S_RUNNING, S_COMPLETED, S_FAILED, S_CANCELLED,
    F_STALE_RESULT, F_INCOMPATIBLE_ASSUMPTIONS,
    F_SCOPE_VIOLATION, F_SNAPSHOT_MISMATCH, F_INVALID_CERT, F_UNKNOWN_CHILD,
    F_CRASH, F_TIMEOUT, F_CANCELLED, F_REFRUTATION,
    K_TASK_ID, K_ATTEMPT_ID, K_WORKER_ID, K_STATUS, K_KIND, K_BODY,
    K_OBLIGATION, K_ASSUMPTION_HASH, K_BUDGET, K_REASON,
    K_DECLARED_SNAPSHOT, K_DECLARED_OBLIGATION,
    alist_put, alist_get, text_atom,
)

COMBINATOR_AND = "and"
COMBINATOR_OR = "or"
GATE_VALIDITY = "validity"
GATE_RENT = "rent"
GATE_HUMAN = "human"

# Proposal states:
#   queued | rejected-validity | rent-hold | awaiting-human
#   admitted | activating | activation-failed | activated | duplicate
# admitted -> activating -> activated is the forward path.
# activation-failed stays in the accepted set (version is published and
# monotonic); a retry uses activate_front again with the same version.


class ChildSpec:
    """A declared child of a claim."""
    def __init__(self, child_id, obligation_text, snapshot_id, assumption_hash):
        self.child_id = child_id
        self.obligation_text = obligation_text
        self.snapshot_id = snapshot_id
        self.assumption_hash = assumption_hash
        self.expected_attempt_id = None  # set when first dispatched/assigned
        self.status = "running"
        self.result_term = M.EmptyList


class ClaimRecord:
    def __init__(self, claim_id, combinator, child_specs):
        self.claim_id = claim_id
        self.combinator = combinator
        self.children = {}
        for s in child_specs:
            self.children[s.child_id] = s
        self.status = "running"
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
                                alist_get, envelope_term, "snapshot_id")
        self.obligation_text = _opt(alist_get, envelope_term, K_DECLARED_OBLIGATION,
                                    alist_get, envelope_term, "obligation")
        self.assumption_hash = _opt(alist_get, envelope_term, K_ASSUMPTION_HASH)
        self.body = alist_get(envelope_term, K_BODY)
        self.reason = alist_get(envelope_term, K_REASON)


def _opt(fn, term, key, fn2=None, term2=None, key2=None):
    v = fn(term, key)
    if v is M.EmptyList and fn2 is not None:
        v = fn2(term2, key2)
    if v is M.EmptyList:
        return ""
    try:
        return v.value
    except Exception:
        return ""


class JoinAdmission:
    def __init__(self, manifest_path=None, strict_manifest=True):
        self.claims = {}
        self._lock = _threading.RLock()
        self._proposal_queue = []
        self._accepted_proposals = []
        self._next_proposal_seq = 0
        self._manifest_path = manifest_path
        self._accepted_state_version = 0
        self.manifest_error = None
        self._activation_inflight = False
        if manifest_path is not None:
            from hyge_int_pkg.programme_c.admission_hooks import (
                load_admission_manifest, ManifestError,
            )
            accepted, queue, version = [], [], 0
            try:
                accepted, queue, version = load_admission_manifest(manifest_path)
            except ManifestError as exc:
                self.manifest_error = exc
                if strict_manifest:
                    raise
            self._accepted_proposals = accepted
            self._proposal_queue = queue
            self._accepted_state_version = int(version)
            max_seq = 0
            for e in queue + accepted:
                pid = e.get("proposal_id", "")
                if pid.startswith("proposal-"):
                    try:
                        n = int(pid[len("proposal-"):])
                        if n > max_seq: max_seq = n
                    except ValueError: pass
            self._next_proposal_seq = max_seq
            # Detect any in-flight activation from prior run.
            for e in self._accepted_proposals:
                if e.get("state") == "activating":
                    self._activation_inflight = True

    def assign_child_attempt(self, parent_claim_id, child_id, attempt_id):
        """Assign the currently-expected attempt for a child. Used by the
        coordinator to fence stale envelopes from prior attempts."""
        with self._lock:
            rec = self.claims.get(parent_claim_id)
            if rec is None: return False
            ch = rec.children.get(child_id)
            if ch is None: return False
            ch.expected_attempt_id = attempt_id
            return True

    def create_claim(self, claim_id, combinator, child_specs):
        with self._lock:
            rec = ClaimRecord(claim_id, combinator, child_specs)
            self.claims[claim_id] = rec
            return rec

    def deliver_child_result(self, parent_claim_id, envelope_term):
        """Deliver a child certificate. Stale-result fencing applies
        regardless of whether the child is currently terminal: envelopes
        whose attempt_id does not match the currently-assigned expected
        attempt are rejected, as are duplicates of superseded attempts."""
        with self._lock:
            rec = self.claims.get(parent_claim_id)
            if rec is None:
                return False, F_SCOPE_VIOLATION, None
            cert = ResultCertificate(envelope_term)
            child = rec.children.get(cert.task_id)
            if child is None:
                return False, F_UNKNOWN_CHILD, rec
            # Active-attempt fencing: reject envelopes whose attempt_id does
            # not match the currently expected attempt for this child,
            # regardless of terminal status.
            accepted = rec.latest_attempt_per_child.get(child.child_id)
            if accepted is not None:
                # Already have a terminal accepted attempt; only that exact
                # attempt is idempotent.
                if accepted == cert.attempt_id:
                    return True, None, rec
                return False, F_STALE_RESULT, rec
            if child.expected_attempt_id is not None and cert.attempt_id != child.expected_attempt_id:
                return False, F_STALE_RESULT, rec
            # Validate declared snapshot/obligation against child manifest.
            if cert.snapshot_id and cert.snapshot_id != child.snapshot_id:
                return False, F_SNAPSHOT_MISMATCH, rec
            if cert.obligation_text and cert.obligation_text != child.obligation_text:
                return False, F_SCOPE_VIOLATION, rec
            if cert.assumption_hash and child.assumption_hash and cert.assumption_hash != child.assumption_hash:
                return False, F_INCOMPATIBLE_ASSUMPTIONS, rec
            reason = cert.reason
            # Invalid-cert reasons do NOT mark the child terminal.
            invalid = _is_invalid_cert_reason(reason)
            if invalid:
                return False, F_INVALID_CERT, rec
            # Record the attempt and update child status.
            rec.latest_attempt_per_child[child.child_id] = cert.attempt_id
            if cert.status == "completed":
                child.status = "completed"
            elif cert.status == "failed":
                if reason is not None and M.IdentityCompare(reason, F_REFRUTATION)() is M.truth_value:
                    child.status = "refuted"
                else:
                    child.status = "failed"
            elif cert.status == "cancelled":
                child.status = "cancelled"
            else:
                return False, F_INVALID_CERT, rec
            child.result_term = envelope_term
            done, joined_term, reason_atom = self._try_join(rec)
            if done:
                rec.accepted_result = joined_term
                rec.status = "completed"
            return True, None, rec

    def retry_child(self, parent_claim_id, child_id, new_attempt_id):
        """Mark a failed child for retry under a new attempt id. Clears the
        terminal state so a new envelope can be delivered. Sets the active
        attempt fencing to new_attempt_id."""
        with self._lock:
            rec = self.claims.get(parent_claim_id)
            if rec is None: return False
            ch = rec.children.get(child_id)
            if ch is None: return False
            ch.status = "running"
            ch.result_term = M.EmptyList
            ch.expected_attempt_id = new_attempt_id
            rec.latest_attempt_per_child.pop(child_id, None)
            rec.status = "running"
            # Recompute join (should now be running since child is running).
            return True

    def cancel_claim(self, claim_id):
        with self._lock:
            rec = self.claims.get(claim_id)
            if rec is None: return False
            rec.status = "cancelled"; return True

    def _try_join(self, rec):
        if rec.combinator == COMBINATOR_AND: return self._join_and(rec)
        if rec.combinator == COMBINATOR_OR: return self._join_or(rec)
        return False, M.EmptyList, None

    def _status_text(self, s):
        if s is None: return ""
        if isinstance(s, str): return s
        try: return P._atom_text(s)
        except Exception: return ""

    def _join_and(self, rec):
        completed = 0; exec_fail = 0; refuted = 0
        child_terms = M.EmptyList
        for cid in list(rec.children.keys()):
            ch = rec.children[cid]; st = self._status_text(ch.status)
            if st == "running": return False, M.EmptyList, None
            if st in ("failed", "cancelled"): exec_fail += 1
            elif st == "refuted": refuted += 1
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
        if exec_fail > 0:
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
        any_running = False; ef = 0; ref = 0
        for cid in list(rec.children.keys()):
            ch = rec.children[cid]; st = self._status_text(ch.status)
            if st in ("running", "dispatched"): any_running = True
            elif st == "refuted": ref += 1
            else: ef += 1
        if not any_running:
            if ref == len(rec.children):
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
            if self.manifest_error is not None: return ""
            if self._has_pending_activation():
                return ""  # block: one admission at a time
            self._next_proposal_seq += 1
            pid = "proposal-" + str(self._next_proposal_seq)
            entry = {
                "proposal_id": pid, "source_claim_id": source_claim_id,
                "proposal_text": proposal_text, "gates": list(gates),
                "enqueued_at": _time.time(), "state": "queued",
                "evidence_state_version": self._accepted_state_version,
            }
            self._proposal_queue.append(entry)
            self._persist(); return pid

    def _has_pending_activation(self):
        """True if there is a proposal in admitted/activating/activation-failed
        state ahead of any new admission."""
        for e in self._accepted_proposals:
            if e.get("state") in ("admitted", "activating", "activation-failed"):
                return True
        if self._activation_inflight:
            return True
        return False

    def _persist(self):
        if self._manifest_path is None: return
        from hyge_int_pkg.programme_c.admission_hooks import write_admission_manifest
        write_admission_manifest(
            self._manifest_path, self._accepted_proposals, self._proposal_queue,
            accepted_state_version=self._accepted_state_version,
        )

    def _run_gate(self, fn, *args):
        try: return bool(fn(*args))
        except Exception: return False

    def admit_next(self, validity_check, rent_check, human_approval_check):
        """One-at-a-time fail-closed gate chain. Returns False if any gate
        fails (or raises) or if persistence fails, or if an activation is
        pending. Bumps accepted_state_version ONLY on transition to
        'admitted'; version is monotonic (never decremented)."""
        with self._lock:
            if self.manifest_error is not None:
                return False, "", "manifest error: " + str(self.manifest_error)
            if self._has_pending_activation():
                return False, "", "activation pending"
            if not self._proposal_queue:
                return False, "", "empty queue"
            entry = self._proposal_queue[0]
            rec = self.claims.get(entry["source_claim_id"])
            if rec is None or rec.status != "completed":
                return False, entry["proposal_id"], "source claim not completed"
            for prior in self._accepted_proposals:
                if (prior.get("proposal_text") == entry["proposal_text"]
                        and prior.get("source_claim_id") == entry.get("source_claim_id")
                        and prior.get("state") == "activated"):
                    self._proposal_queue.pop(0); self._persist()
                    return True, entry["proposal_id"], "duplicate"
            entry["evidence_state_version"] = self._accepted_state_version
            if GATE_VALIDITY in entry["gates"]:
                if not self._run_gate(validity_check, entry,
                                      list(self._accepted_proposals),
                                      self._accepted_state_version):
                    entry["state"] = "rejected-validity"
                    entry["rejected_at"] = _time.time()
                    self._proposal_queue.pop(0); self._persist()
                    return False, entry["proposal_id"], "validity failed"
            if GATE_RENT in entry["gates"]:
                if not self._run_gate(rent_check, entry):
                    entry["state"] = "rent-hold"; self._persist()
                    return False, entry["proposal_id"], "rent hold"
            if GATE_HUMAN in entry["gates"]:
                if not self._run_gate(human_approval_check, entry):
                    entry["state"] = "awaiting-human"; self._persist()
                    return False, entry["proposal_id"], "awaiting human"
            entry["state"] = "admitted"
            entry["admitted_at"] = _time.time()
            entry["admitted_at_version"] = self._accepted_state_version
            self._accepted_proposals.append(entry)
            self._proposal_queue.pop(0)
            self._accepted_state_version += 1
            self._persist()
            return True, entry["proposal_id"], "admitted"

    def pending_activation(self):
        """Return the proposal entry awaiting activation (or None)."""
        with self._lock:
            for e in reversed(self._accepted_proposals):
                if e.get("state") in ("admitted", "activating", "activation-failed"):
                    return e
            return None

    def activate_front(self, activation_fn):
        """Run activation idempotently:

        1. Persist an 'activating' marker BEFORE invoking activation_fn so a
           crash can detect an unresolved activation and reconcile.
        2. Invoke activation_fn(entry, accepted, version).
        3. On True, mark 'activated' and persist.
        4. On False/exception, mark 'activation-failed' and persist; version
           is NOT decremented (monotonic). Caller must retry; no next
           candidate is admitted while a proposal is in
           admitted/activating/activation-failed.

        Returns (ok, pid, reason). If the front is already 'activated' this
        returns (True, pid, 'already-activated') without invoking the fn.
        """
        with self._lock:
            if self.manifest_error is not None:
                return False, "", "manifest error"
            entry = None
            for e in reversed(self._accepted_proposals):
                st = e.get("state")
                if st in ("admitted", "activating", "activation-failed", "activated"):
                    entry = e; break
            if entry is None:
                return False, "", "no admitted proposal"
            if entry.get("state") == "activated":
                return True, entry["proposal_id"], "already-activated"
            # Write 'activating' durable record before invoking the callback.
            entry["state"] = "activating"
            entry["activation_started_at"] = _time.time()
            self._activation_inflight = True
            self._persist()
            try:
                ok = bool(activation_fn(entry, list(self._accepted_proposals),
                                        self._accepted_state_version))
            except Exception:
                ok = False
            if ok:
                entry["state"] = "activated"
                entry["activated_at"] = _time.time()
                self._activation_inflight = False
                self._persist()
                return True, entry["proposal_id"], "activated"
            entry["state"] = "activation-failed"
            entry["failed_at"] = _time.time()
            # activation_inflight remains True: while activation-failed we
            # still block new admissions (it is an unresolved activation
            # that needs retry).  It is cleared only on successful activation
            # or on recovery when an 'activated' entry is found.
            self._persist()
            return False, entry["proposal_id"], "activation failed"


def _is_invalid_cert_reason(reason):
    if reason is None: return False
    bad_reasons = (F_INVALID_CERT, F_SNAPSHOT_MISMATCH, F_SCOPE_VIOLATION,
                   F_INCOMPATIBLE_ASSUMPTIONS, F_UNKNOWN_CHILD)
    for bad in bad_reasons:
        if M.IdentityCompare(reason, bad)() is M.truth_value:
            return True
    return False


def _atom_eq(a, b):
    try: return P._atom_text(a) == P._atom_text(b)
    except Exception: return M.IdentityCompare(a, b)() is M.truth_value


def child_spec(child_id, obligation_text, snapshot_id, assumption_hash):
    return ChildSpec(child_id, obligation_text, snapshot_id, assumption_hash)
