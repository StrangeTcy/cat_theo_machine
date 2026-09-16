"""Wrapper module for dispatching into the existing `search-worker` subprocess
entry point under BoundedWorkerPool semantics (C-A wrap, not replace).

Strict per-C-INT review (2026-09-16):

  * Readiness is a validated child record (first checkpoint) emitted AFTER
    restore and BEFORE obligation execution. It is accepted only when the
    checkpoint's manifest (written alongside the result) declares the
    expected snapshot_id and obligation.
  * Neither rc=0 nor rc=4 discharges a child by itself. On completion the
    coordinator replays the real worker's certificate against the declared
    child snapshot, obligation, and assumption hash before accepting the
    result.
  * Isolated cwd, explicit 'spawn' (via subprocess.Popen with the same CLI
    as compare_subprocess), budget/deadline + SIGTERM -> SIGKILL,
    max_workers=2 enforced synchronously.
  * Every envelope stamped with K_TASK_ID/K_ATTEMPT_ID/K_WORKER_ID/
    K_DECLARED_SNAPSHOT/K_DECLARED_OBLIGATION/K_ASSUMPTION_HASH/K_BUDGET,
    plus K_REASON on failures.
"""
from __future__ import annotations

import hashlib
import json as _json
import os
import subprocess as _sp
import sys as _sys
import time as _time

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c as P
import hyge_int_pkg.programme_c.snapshot_id as _sid
try:
    from hyge_int_pkg.main import _runtime_namespace as _main_runtime_namespace
    from hyge_int_pkg.persistence import SnapshotCodec as _SnapshotCodec
    from hyge_int_pkg.search import modes as _Smod
    _HAS_CODEC = True
except Exception:
    _HAS_CODEC = False
from hyge_int_pkg.programme_c import (
    S_COMPLETED, S_FAILED, S_CANCELLED, S_DISPATCHED, S_RUNNING, S_READY,
    F_CRASH, F_TIMEOUT, F_CANCELLED, F_LAUNCH_ERROR, F_SNAPSHOT_MISMATCH,
    F_INVALID_CERT, F_SCOPE_VIOLATION, F_INCOMPATIBLE_ASSUMPTIONS,
    K_TASK_ID, K_ATTEMPT_ID, K_WORKER_ID, K_STATUS, K_KIND, K_BODY,
    K_SNAPSHOT_ID, K_OBLIGATION, K_ASSUMPTION_HASH, K_BUDGET, K_REASON,
    K_DECLARED_SNAPSHOT, K_DECLARED_OBLIGATION,
    alist_put, alist_get,
    text_atom,
)
from hyge_int_pkg.programme_c.worker import (
    WorkerEnvelope, WorkerTicket, BoundedWorkerPool, _terminate, _assumption_hash,
    _proc_is_alive,
)

READY_POLL_INTERVAL_SEC = 0.05
READY_STAGES = ("running-search", "success-plan-found", "running-derivation",
                "success-derivation-built")
FAILED_STAGES = ("timed_out", "failure-search", "failure-memory-error")


def compute_codebase_identity(package_root, scratch_dir):
    """Compute a snapshot identity over restore-critical source modules. This
    is additional provenance; it does NOT substitute for verifying that the
    child restored the declared knowledge snapshot / memory profile."""
    os.makedirs(scratch_dir, exist_ok=True)
    code_dir = os.path.join(scratch_dir, "_codebase_snapshot")
    os.makedirs(code_dir, exist_ok=True)
    src_files = [
        os.path.join(package_root, "persistence.py"),
        os.path.join(package_root, "programme_c", "snapshot_id.py"),
        os.path.join(package_root, "programme_c", "worker.py"),
        os.path.join(package_root, "programme_c", "worker_dispatch.py"),
        os.path.join(package_root, "main.py"),
    ]
    body = {"files": []}
    for f in src_files:
        rel = os.path.relpath(f, package_root)
        try:
            with open(f, "rb") as h:
                data = h.read()
            digest = hashlib.blake2b(data, digest_size=32).hexdigest()
            body["files"].append({"path": rel, "blake2b_256": digest, "size": len(data)})
        except FileNotFoundError:
            body["files"].append({"path": rel, "missing": True})
    snap_path = os.path.join(code_dir, "codebase.snapshot.json")
    with open(snap_path, "w", encoding="utf-8") as h:
        _json.dump(body, h, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    ident, _ = _sid.compute_identity(snap_path)
    return ident, snap_path


def _write_search_worker_manifest(result_path, start_text, goal_text,
                                  task_id, attempt_id, worker_id,
                                  obligation_text, assumption_hash,
                                  snapshot_id, budget_text):
    manifest = {
        "start_text": start_text,
        "goal_text": goal_text,
        "task_id": task_id,
        "attempt_id": attempt_id,
        "worker_id": worker_id,
        "declared_snapshot_id": snapshot_id,
        "declared_obligation": obligation_text,
        "assumption_hash": assumption_hash,
        "budget_millis": budget_text,
    }
    manifest_path = result_path + ".manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as h:
        _json.dump(manifest, h, sort_keys=True, ensure_ascii=False)


def _load_search_worker_snapshot_raw(result_path):
    try:
        with open(result_path, "r", encoding="utf-8") as h:
            return _json.load(h)
    except (FileNotFoundError, _json.JSONDecodeError, OSError):
        return None


def _load_worker_stage(result_path):
    """Return (worker_stage_text, status_atom_text, has_attempt) using the real
    SnapshotCodec so certificate inspection matches the parent runtime's view
    of the snapshot. Returns (None, None, False) on any failure."""
    if not _HAS_CODEC:
        return None, None, False
    try:
        state = _SnapshotCodec(_main_runtime_namespace()).load(result_path)
    except Exception:
        return None, None, False
    worker_stage = state.roots.get("worker_stage", M.EmptyList)
    attempts = state.roots.get("search_history", M.EmptyList)
    has_attempt = (attempts is not M.EmptyList)
    try:
        stage_val = worker_stage
        if hasattr(stage_val, "__call__"):
            stage_val = stage_val()
        try:
            stage_text = stage_val.value
            if hasattr(stage_text, "value"):
                stage_text = stage_text.value
        except Exception:
            stage_text = str(stage_val)
        if isinstance(stage_text, bytes):
            stage_text = stage_text.decode("utf-8", "replace")
        stage_text = str(stage_text)
    except Exception:
        stage_text = ""
    attempts_has_success = False
    if has_attempt:
        try:
            attempt = M.Head(attempts)()
            import hyge_int_pkg.proof as PP
            status_atom = PP.SearchAttemptStatus(attempt)()
            try:
                status_text = status_atom.value
                if hasattr(status_text, "value"): status_text = status_text.value
            except Exception:
                status_text = str(status_atom)
            if "success" in str(status_text).lower():
                attempts_has_success = True
            outcome = _Smod.SearchCostOutcome(PP.SearchAttemptSearchCost(attempt)())()
            outcome_text = str(outcome.value) if hasattr(outcome, "value") else str(outcome)
        except Exception:
            outcome_text = ""
    else:
        status_text = ""
    return stage_text, status_text, has_attempt


def _verify_child_certificate(result_path, expected_snapshot_id,
                              expected_obligation, expected_assumption_hash,
                              expected_task_id, expected_attempt_id):
    """Replay the child's snapshot certificate against the declared fields.

    Returns (ok, status_text, reason_atom, body_text):
      * ok=True  -> status in {"completed","failed"} with a reason atom.
      * ok=False -> certificate invalid / missing / mismatched.

    A deferred-derivation (running-derivation / success-plan-found) checkpoint
    is NOT accepted as discharge; it is an incomplete certificate.
    """
    if not os.path.isfile(result_path):
        return False, "no-snapshot", F_INVALID_CERT, ""
    # Manifest sidecar must declare matching snapshot_id, obligation,
    # assumption_hash, task_id, attempt_id.
    manifest_path = result_path + ".manifest.json"
    try:
        with open(manifest_path, "r", encoding="utf-8") as h:
            manifest = _json.load(h)
    except Exception:
        return False, "manifest-missing", F_INVALID_CERT, ""
    if manifest.get("declared_snapshot_id") != expected_snapshot_id:
        return False, "snapshot-mismatch", F_SNAPSHOT_MISMATCH, ""
    if manifest.get("declared_obligation") != expected_obligation:
        return False, "obligation-mismatch", F_SCOPE_VIOLATION, ""
    if expected_assumption_hash and manifest.get("assumption_hash") != expected_assumption_hash:
        return False, "assumption-mismatch", F_INCOMPATIBLE_ASSUMPTIONS, ""
    if expected_task_id and manifest.get("task_id") != expected_task_id:
        return False, "task-id-mismatch", F_INVALID_CERT, ""
    if expected_attempt_id and manifest.get("attempt_id") != expected_attempt_id:
        return False, "attempt-id-mismatch", F_INVALID_CERT, ""
    # Use real codec to read the worker stage.
    stage_text, status_text, has_attempt = _load_worker_stage(result_path)
    if stage_text is None and not has_attempt:
        return False, "unreadable-snapshot", F_INVALID_CERT, ""
    body_text = "stage=" + str(stage_text) + " status=" + str(status_text)
    # Running stages -> incomplete certificate.
    if stage_text in ("running-search", "running-derivation", "success-plan-found"):
        return False, "incomplete:" + str(stage_text), F_INVALID_CERT, body_text
    if stage_text == "success-derivation-built" or (status_text and "success" in status_text.lower()):
        return True, "completed", None, body_text
    if stage_text == "timed_out":
        return True, "failed", F_TIMEOUT, body_text
    if stage_text and (stage_text.startswith("failure") or "error" in stage_text.lower()):
        return True, "failed", F_CRASH, body_text
    # No attempt captured at all -> incomplete.
    if not has_attempt:
        return False, "no-attempt:" + str(stage_text), F_INVALID_CERT, body_text
    return False, "unknown-stage:" + str(stage_text), F_INVALID_CERT, body_text


def _ready_from_checkpoint(result_path, expected_snapshot_id, expected_obligation):
    """Readiness is validated when: (a) the snapshot file exists and is
    loadable via SnapshotCodec (i.e. the child restored its knowledge
    snapshot), (b) the manifest sidecar declares matching snapshot_id and
    obligation (so we know the child is working against the declared task),
    and (c) worker_stage has been written to a non-empty value (any stage
    after restore — running-search or terminal)."""
    if not os.path.isfile(result_path):
        return False
    manifest_path = result_path + ".manifest.json"
    try:
        with open(manifest_path, "r", encoding="utf-8") as h:
            manifest = _json.load(h)
    except Exception:
        return False
    if manifest.get("declared_snapshot_id") != expected_snapshot_id:
        return False
    if manifest.get("declared_obligation") != expected_obligation:
        return False
    stage_text, status_text, has_attempt = _load_worker_stage(result_path)
    if stage_text is None and not has_attempt:
        return False
    # Any recorded worker_stage (after boot + first checkpoint) counts as
    # readiness — the child has restored its snapshot and written its
    # first record. The terminal poll will later replay the certificate.
    return bool(stage_text) or has_attempt


def _spawn_search_worker_process(package_root, worker_dir, mode_token,
                                 result_path, timeout_seconds, import_root=None,
                                 defer_derivation=True):
    cmd = [_sys.executable, "-m", "hyge_int_pkg.main", "search-worker",
           mode_token, result_path, str(int(timeout_seconds))]
    env = os.environ.copy()
    if import_root is None:
        import_root = os.path.dirname(package_root)
    env["PYTHONPATH"] = import_root
    env["HYGE_SEARCH_WORKER_DEFER_DERIVATION"] = "1" if defer_derivation else ""
    proc = _sp.Popen(
        cmd,
        stdout=_sp.PIPE,
        stderr=_sp.STDOUT,
        cwd=worker_dir,
        env=env,
    )
    return proc


class SearchWorkerDispatch:
    def __init__(self, pool, package_root):
        self.pool = pool
        self.package_root = package_root

    def spawn(self, mode_token, start_text, goal_text, task_id, attempt_id,
              obligation_text, assumptions_term, budget_millis,
              worker_timeout_seconds=None, assumption_hash_override=None,
              defer_derivation=True):
        if worker_timeout_seconds is None:
            worker_timeout_seconds = max(1, int(budget_millis // 1000))
        worker_id = self.pool._new_worker_id()
        work_dir = self.pool._isolation_dir(worker_id)
        env = WorkerEnvelope(task_id, attempt_id, worker_id)
        assumption_hash = assumption_hash_override or _assumption_hash(assumptions_term)
        code_ident, _code_snap = compute_codebase_identity(self.package_root, work_dir)
        if self.pool.snapshot_ident is None:
            self.pool.snapshot_ident = code_ident
        if code_ident.snapshot_id != self.pool.snapshot_ident.snapshot_id:
            t = WorkerTicket(task_id, attempt_id, worker_id, work_dir,
                             code_ident.snapshot_id, obligation_text,
                             assumptions_term, budget_millis, None, None, 0)
            t.result_term = env.make_failure(F_SNAPSHOT_MISMATCH,
                                             "codebase snapshot mismatch")
            t.status = S_FAILED; t._terminal = True; self.pool.tickets.append(t); return t
        if self.pool._outstanding >= 2:
            t = WorkerTicket(task_id, attempt_id, worker_id, work_dir,
                             code_ident.snapshot_id, obligation_text,
                             assumptions_term, budget_millis, None, None, 0)
            t.result_term = env.make_failure(F_LAUNCH_ERROR, "max_workers=2 exceeded")
            t.status = S_FAILED; t._terminal = True; self.pool.tickets.append(t); return t
        result_path = os.path.join(work_dir, mode_token + ".snapshot.json")
        _write_search_worker_manifest(result_path, start_text, goal_text,
                                      task_id, attempt_id, worker_id,
                                      obligation_text, assumption_hash,
                                      code_ident.snapshot_id, str(budget_millis))
        try:
            proc = _spawn_search_worker_process(self.package_root, work_dir,
                                                mode_token, result_path,
                                                worker_timeout_seconds,
                                                defer_derivation=defer_derivation)
        except Exception as exc:
            t = WorkerTicket(task_id, attempt_id, worker_id, work_dir,
                             code_ident.snapshot_id, obligation_text,
                             assumptions_term, budget_millis, None, None, 0)
            t.result_term = env.make_failure(F_LAUNCH_ERROR, str(exc))
            t.status = S_FAILED; t._terminal = True; self.pool.tickets.append(t); return t
        deadline_millis = _time.time()*1000.0 + budget_millis
        ticket = _SearchWorkerTicket(task_id, attempt_id, worker_id, work_dir,
                                     code_ident.snapshot_id, obligation_text,
                                     assumptions_term, budget_millis, proc, result_path,
                                     deadline_millis, assumption_hash)
        ticket.status = S_RUNNING; self.pool.tickets.append(ticket)
        self.pool._outstanding += 1
        self._wait_ready(ticket, env, code_ident.snapshot_id, obligation_text)
        return ticket

    def _wait_ready(self, ticket, env, snapshot_id, obligation_text):
        while True:
            now = _time.time()*1000.0
            if now >= ticket.deadline_millis:
                _terminate(ticket.proc)
                ticket.result_term = env.make_failure(F_TIMEOUT, "ready handshake timed out")
                ticket.status = S_FAILED; self.pool._mark_terminal(ticket); return
            rc = ticket.proc.poll()
            if _ready_from_checkpoint(ticket.result_path, snapshot_id, obligation_text):
                ticket._ready_env = env.make_ready(snapshot_id, obligation_text)
                ticket.status = S_DISPATCHED; return
            if rc is not None:
                # Process exited without producing a valid readiness checkpoint.
                ticket.proc.wait(timeout=2)
                try:
                    out, _ = ticket.proc.communicate(timeout=1)
                    body = out.decode("utf-8", "replace")[-500:]
                except Exception:
                    body = ""
                # If there is a snapshot at all, run cert verification to
                # distinguish F_TIMEOUT vs malformed cert; else F_CRASH.
                ok, _stat, reason, _body = _verify_child_certificate(
                    ticket.result_path, snapshot_id, obligation_text,
                    ticket.assumption_hash, ticket.task_id, ticket.attempt_id)
                if ok and reason is F_TIMEOUT:
                    ticket.result_term = env.make_failure(F_TIMEOUT, "worker timed out before ready")
                else:
                    ticket.result_term = env.make_failure(F_INVALID_CERT,
                                                          "no valid readiness checkpoint: " + body)
                ticket.status = S_FAILED; self.pool._mark_terminal(ticket); return
            _time.sleep(READY_POLL_INTERVAL_SEC)

    def poll(self, ticket):
        is_sw = False
        try:
            _ = ticket.result_path; is_sw = True
        except AttributeError:
            is_sw = False
        if not is_sw:
            return self.pool.poll(ticket)
        if ticket.status != S_RUNNING and ticket.status != S_DISPATCHED:
            return ticket.result_term
        now = _time.time()*1000.0
        if now >= ticket.deadline_millis:
            _terminate(ticket.proc)
            env = WorkerEnvelope(ticket.task_id, ticket.attempt_id, ticket.worker_id)
            ticket.result_term = env.make_failure(F_TIMEOUT, "budget exhausted")
            ticket.status = S_FAILED; self.pool._mark_terminal(ticket); return ticket.result_term
        rc = ticket.proc.poll()
        if rc is None:
            return M.EmptyList
        ticket.proc.wait(timeout=2)
        env = WorkerEnvelope(ticket.task_id, ticket.attempt_id, ticket.worker_id)
        try:
            out, _ = ticket.proc.communicate(timeout=1)
            stdout_tail = out.decode("utf-8", "replace")[-1000:]
        except Exception:
            stdout_tail = ""
        # Replay the child certificate against declared snapshot/obligation/assumptions.
        ok, stat, reason, body = _verify_child_certificate(
            ticket.result_path, ticket.snapshot_id, ticket.obligation_text,
            ticket.assumption_hash, ticket.task_id, ticket.attempt_id)
        assumption_hash = ticket.assumption_hash or "0"
        if ok and stat == "completed" and reason is None:
            ticket.result_term = env.make_result(
                body + "\n" + stdout_tail[-200:], ticket.snapshot_id,
                ticket.obligation_text, assumption_hash, str(ticket.budget_millis))
            ticket.status = S_COMPLETED
        elif ok and stat == "failed":
            r = reason if reason is not None else F_CRASH
            ticket.result_term = env.make_failure(r, body + "\n" + stdout_tail[-200:])
            ticket.status = S_FAILED
        else:
            # Certificate invalid even though process exited.
            r = reason if reason is not None else F_INVALID_CERT
            ticket.result_term = env.make_failure(r, body + "\n" + stdout_tail[-200:])
            ticket.status = S_FAILED
        self.pool._mark_terminal(ticket)
        return ticket.result_term

    def cancel(self, ticket):
        is_sw = False
        try:
            _ = ticket.result_path; is_sw = True
        except AttributeError:
            is_sw = False
        if not is_sw:
            return self.pool.cancel(ticket)
        if ticket.status == S_RUNNING or ticket.status == S_DISPATCHED:
            _terminate(ticket.proc)
            env = WorkerEnvelope(ticket.task_id, ticket.attempt_id, ticket.worker_id)
            ticket.result_term = env.make_failure(F_CANCELLED, "cancelled by pool")
            ticket.status = S_CANCELLED; self.pool._mark_terminal(ticket)
        return ticket.result_term

    def cleanup(self, ticket):
        self.pool.cleanup(ticket)


class _SearchWorkerTicket(WorkerTicket):
    def __init__(self, task_id, attempt_id, worker_id, worker_dir, snapshot_id,
                 obligation_text, assumptions, budget_millis, proc, result_path,
                 deadline_millis, assumption_hash):
        super().__init__(task_id, attempt_id, worker_id, worker_dir, snapshot_id,
                         obligation_text, assumptions, budget_millis, proc, None,
                         deadline_millis)
        self.result_path = result_path
        self.assumption_hash = assumption_hash
        self._ready_env = None
