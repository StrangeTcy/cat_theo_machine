"""Wrapper module for dispatching into the existing `search-worker` subprocess
entry point under BoundedWorkerPool semantics (C-A wrap, not replace).

The existing compare_subprocess.py worker launch (`_compare_all_modes_independent`,
_compare_all_modes`) is preserved unchanged; this module adds a parallel path that
drives the same `python -m <pkg>.main search-worker <mode> <result> <timeout>`
command from BoundedWorkerPool, with:

  * readiness ack: detected by watching for the first checkpoint write;
  * isolated cwd: per-task worker dir under scratch/workers/<id>;
  * budget/deadline + SIGTERM -> SIGKILL cancellation;
  * every ready/result/failure envelope stamped with K_TASK_ID, K_ATTEMPT_ID,
    K_WORKER_ID, K_DECLARED_SNAPSHOT, K_DECLARED_OBLIGATION, K_ASSUMPTION_HASH,
    K_BUDGET, K_REASON;
  * snapshot-identity pre-flight against a computed codebase snapshot;
  * exit-code mapping: rc=0 success, rc=2 timeout, rc=4 awaiting-derivation
    (treated as success-plan-found), rc=1 failure (execution error), and
    signal kill = F_CRASH / F_TIMEOUT.
"""
from __future__ import annotations

import json as _json
import os
import subprocess as _sp
import sys as _sys
import time as _time

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c as P
import hyge_int_pkg.programme_c.snapshot_id as _sid
from hyge_int_pkg.programme_c import (
    S_COMPLETED, S_FAILED, S_CANCELLED, S_DISPATCHED, S_RUNNING, S_READY,
    F_CRASH, F_TIMEOUT, F_CANCELLED, F_LAUNCH_ERROR, F_SNAPSHOT_MISMATCH,
    K_TASK_ID, K_ATTEMPT_ID, K_WORKER_ID, K_STATUS, K_KIND, K_BODY,
    K_SNAPSHOT_ID, K_OBLIGATION, K_ASSUMPTION_HASH, K_BUDGET, K_REASON,
    K_DECLARED_SNAPSHOT, K_DECLARED_OBLIGATION,
    alist_put, alist_get,
    text_atom,
)
from hyge_int_pkg.programme_c.worker import (
    WorkerEnvelope, WorkerTicket, BoundedWorkerPool, _terminate, _assumption_hash,
)

READY_POLL_INTERVAL_SEC = 0.05
READY_POLL_FIRST_STAGES = ("running-search", "success-plan-found",
                           "running-derivation", "success-derivation-built",
                           "timed_out", "failure-search")


def compute_codebase_identity(package_root, scratch_dir):
    """Compute a snapshot identity over the codebase (persistence.py + snapshot_id.py
    + worker_dispatch.py are the restore-critical surface) so the dispatch
    pre-flight can verify codebase identity before spawning.

    Builds a temporary canonical "codebase snapshot" directory inside scratch_dir
    that records the hash of the relevant source files, returning a
    SnapshotIdentityRecord pointing at it.
    """
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
    import hashlib
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


def _read_search_worker_stage(result_path):
    """Read the latest stage/completion_reason from a search-worker snapshot.

    Returns (stage_text, status_atom, reason_atom, body_text) or None if no
    checkpoint is present.
    """
    try:
        with open(result_path, "r", encoding="utf-8") as h:
            snap = _json.load(h)
    except (FileNotFoundError, _json.JSONDecodeError, OSError):
        return None
    attempts = snap.get("search_history") or snap.get("attempts")
    if not attempts:
        return None
    # Last attempt is the latest.
    last = attempts[-1]
    stage = last.get("completion_reason") or last.get("stage") or ""
    status = last.get("status") or ""
    body_text = ""
    if "elapsed_milliseconds" in last:
        body_text = "elapsed_ms=" + str(last["elapsed_milliseconds"])
    reason_term = None
    if status == "success" or stage in ("success-plan-found", "success-derivation-built", "running-derivation"):
        status_atom = S_COMPLETED
    elif stage == "timed_out" or status == "timed_out":
        status_atom = S_FAILED; reason_term = F_TIMEOUT
    else:
        status_atom = S_FAILED; reason_term = F_CRASH
    return stage, status_atom, reason_term, body_text


def _spawn_search_worker_process(package_root, worker_dir, mode_token,
                                 result_path, timeout_seconds, import_root=None):
    cmd = [_sys.executable, "-m", "hyge_int_pkg.main", "search-worker",
           mode_token, result_path, str(int(timeout_seconds))]
    env = os.environ.copy()
    # import_root must be the directory *containing* the hyge_int_pkg package.
    if import_root is None:
        import_root = os.path.dirname(package_root)
    env["PYTHONPATH"] = import_root
    env["HYGE_SEARCH_WORKER_DEFER_DERIVATION"] = "1"
    proc = _sp.Popen(
        cmd,
        stdout=_sp.PIPE,
        stderr=_sp.STDOUT,
        cwd=worker_dir,
        env=env,
    )
    return proc


class SearchWorkerDispatch:
    """Wrapper entry added to BoundedWorkerPool — NOT replacing the existing
    compare_executors resident pool. Drives the existing search-worker
    subprocess through the bounded envelope protocol."""

    def __init__(self, pool, package_root):
        self.pool = pool
        self.package_root = package_root

    def spawn(self, mode_token, start_text, goal_text, task_id, attempt_id,
              obligation_text, assumptions_term, budget_millis,
              worker_timeout_seconds=None):
        """Spawn a search-worker subprocess in an isolated dir.

        Returns a SearchWorkerTicket with the same poll/cancel/cleanup
        contract as BoundedWorkerPool.spawn_worker.
        """
        if worker_timeout_seconds is None:
            worker_timeout_seconds = max(1, int(budget_millis // 1000))
        worker_id = self.pool._new_worker_id()
        work_dir = self.pool._isolation_dir(worker_id)
        env = WorkerEnvelope(task_id, attempt_id, worker_id)
        assumption_hash = _assumption_hash(assumptions_term)
        # Pre-flight: compute codebase identity and verify against pool expectation.
        code_ident, code_snap = compute_codebase_identity(self.package_root, work_dir)
        if self.pool.snapshot_ident is None:
            # Bind pool identity to the codebase snapshot computed on first dispatch.
            self.pool.snapshot_ident = code_ident
        if code_ident.snapshot_id != self.pool.snapshot_ident.snapshot_id:
            ok, got = False, code_ident.snapshot_id
        else:
            ok, got = True, code_ident.snapshot_id
        if not ok:
            t = WorkerTicket(task_id, attempt_id, worker_id, work_dir,
                             self.pool.snapshot_ident.snapshot_id if self.pool.snapshot_ident else code_ident.snapshot_id,
                             obligation_text, assumptions_term, budget_millis, None, None, 0)
            t.result_term = env.make_failure(F_SNAPSHOT_MISMATCH, "codebase snapshot mismatch: " + str(got))
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
                                                worker_timeout_seconds)
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
                                     deadline_millis)
        ticket.status = S_RUNNING; self.pool.tickets.append(ticket)
        self.pool._outstanding += 1
        # Readiness: wait until first checkpoint appears (or crash/timeout).
        ready_env = self._wait_ready(ticket, env, code_ident.snapshot_id, obligation_text)
        if ready_env is not None:
            ticket._ready_env = ready_env
            ticket.status = S_DISPATCHED
        return ticket

    def _wait_ready(self, ticket, env, snapshot_id, obligation_text):
        saw_checkpoint = False
        while True:
            now = _time.time()*1000.0
            if now >= ticket.deadline_millis:
                _terminate(ticket.proc)
                ticket.result_term = env.make_failure(F_TIMEOUT, "ready handshake (first checkpoint) timed out")
                ticket.status = S_FAILED; self.pool._mark_terminal(ticket); return None
            stage_info = _read_search_worker_stage(ticket.result_path)
            if stage_info is not None:
                saw_checkpoint = True
            rc = ticket.proc.poll()
            if rc is not None:
                # Process exited. rc==0/4 (success) or rc==2 (timeout) all mean
                # the worker booted and wrote at least one checkpoint (or hit a
                # search time-out); synthesize ready and let poll() report F_TIMEOUT
                # or completed based on the stage/rc.  If a checkpoint was seen
                # on disk, same treatment regardless of rc.
                if rc in (0, 2, 4) or saw_checkpoint:
                    return env.make_ready(snapshot_id, obligation_text)
                ticket.proc.wait(timeout=2)
                try:
                    out, _ = ticket.proc.communicate(timeout=1)
                    body_text = out.decode("utf-8", "replace")[-2000:]
                except Exception:
                    body_text = ""
                ticket.result_term = env.make_failure(F_CRASH, "worker exited before ready rc=" + str(rc) + ": " + body_text[-500:])
                ticket.status = S_FAILED; self.pool._mark_terminal(ticket); return None
            if saw_checkpoint:
                return env.make_ready(snapshot_id, obligation_text)
            _time.sleep(READY_POLL_INTERVAL_SEC)

    def poll(self, ticket):
        is_search_worker_ticket = False
        try:
            _ = ticket.result_path
            is_search_worker_ticket = True
        except AttributeError:
            is_search_worker_ticket = False
        if not is_search_worker_ticket:
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
            return M.EmptyList  # still running
        ticket.proc.wait(timeout=2)
        env = WorkerEnvelope(ticket.task_id, ticket.attempt_id, ticket.worker_id)
        try:
            out = b""
            try:
                out, _ = ticket.proc.communicate(timeout=1)
            except Exception:
                pass
            body_text = out.decode("utf-8", "replace")[-2000:]
        except Exception:
            body_text = ""
        stage_info = _read_search_worker_stage(ticket.result_path)
        assumption_hash = _assumption_hash(ticket.assumptions)
        budget_text = str(ticket.budget_millis)
        if rc == 0:
            ticket.result_term = env.make_result(body_text, ticket.snapshot_id,
                                                 ticket.obligation_text,
                                                 assumption_hash, budget_text)
            ticket.status = S_COMPLETED
        elif rc == 4:
            # defer-derivation (success-plan-found, awaiting replay approval).
            # Treat as completed (plan found before derivation replay).
            ticket.result_term = env.make_result(body_text, ticket.snapshot_id,
                                                 ticket.obligation_text,
                                                 assumption_hash, budget_text)
            ticket.status = S_COMPLETED
        elif rc == 2:
            ticket.result_term = env.make_failure(F_TIMEOUT, "search timed out: " + body_text[-500:])
            ticket.status = S_FAILED
        elif rc < 0:
            ticket.result_term = env.make_failure(F_CRASH, "signal " + str(-rc) + ": " + body_text[-500:])
            ticket.status = S_FAILED
        else:
            # rc == 1: check stage to distinguish timeout vs crash vs refutation.
            if stage_info is not None:
                _stage, status_atom, reason_term, _body = stage_info
                if reason_term is F_TIMEOUT:
                    ticket.result_term = env.make_failure(F_TIMEOUT, "stage=timed_out: " + body_text[-500:])
                else:
                    ticket.result_term = env.make_failure(F_CRASH, "stage=failure: " + body_text[-500:])
            else:
                ticket.result_term = env.make_failure(F_CRASH, "rc=1 no checkpoint: " + body_text[-500:])
            ticket.status = S_FAILED
        self.pool._mark_terminal(ticket)
        return ticket.result_term

    def cancel(self, ticket):
        is_search_worker_ticket = False
        try:
            _ = ticket.result_path
            is_search_worker_ticket = True
        except AttributeError:
            is_search_worker_ticket = False
        if not is_search_worker_ticket:
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
                 deadline_millis):
        super().__init__(task_id, attempt_id, worker_id, worker_dir, snapshot_id,
                         obligation_text, assumptions, budget_millis, proc, None,
                         deadline_millis)
        self.result_path = result_path
        self._ready_env = None
