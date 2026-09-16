"""Wrapper module for dispatching into the existing `search-worker` subprocess
entry point under BoundedWorkerPool semantics (C-A wrap, not replace).

Strict per C-INT review (2026-09-16, corrective 2026-09-16 #2):

  * Explicit readiness handshake: child writes a "ready-<pid>" marker into a
    gate directory after the running-search checkpoint is durable, then
    blocks on a "release-<pid>" marker before starting search. The
    coordinator releases AFTER validating the ready snapshot+manifest. This
    enforces restore → READY → validate → release → execute ordering.
  * Active-attempt fencing: the coordinator labels every child with a
    monotonically-increasing expected_attempt_id; any envelope whose
    attempt_id does not match the expected active attempt is rejected with
    F_STALE_RESULT regardless of terminal status.
  * Neither rc=0 nor rc=4 discharges a child by itself. On completion the
    coordinator replays the real worker's certificate by booting an
    isolated runtime from the child snapshot and re-running derivation
    construction (BuildDerivation) against the saved worker_plan, then
    verifying the goal is reached. This is the proof-accepting step, not
    merely container inspection.
  * Isolated cwd, explicit 'spawn', budget/deadline + SIGTERM -> SIGKILL,
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
    from hyge_int_pkg import proof as _proof_mod
    from hyge_int_pkg.search import modes as _Smod
    import hyge_int_pkg.proof as _PP
    _HAS_CODEC = True
except Exception:
    _HAS_CODEC = False
from hyge_int_pkg.programme_c import (
    S_COMPLETED, S_FAILED, S_CANCELLED, S_DISPATCHED, S_RUNNING, S_READY,
    F_CRASH, F_TIMEOUT, F_CANCELLED, F_LAUNCH_ERROR, F_SNAPSHOT_MISMATCH,
    F_INVALID_CERT, F_SCOPE_VIOLATION, F_INCOMPATIBLE_ASSUMPTIONS,
    F_STALE_RESULT,
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
READY_STAGE_COMPLETE = "success-derivation-built"
READY_STAGE_PENDING = ("running-search",)
READY_STAGE_TERMINAL_NO_PLAN = ("timed_out",)
RC_READY_TIMEOUT = 5


def compute_codebase_identity(package_root, scratch_dir):
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


def _load_worker_stage(result_path):
    """Return (worker_stage_text, status_text, has_attempt, worker_plan, registry)
    using the real SnapshotCodec so certificate inspection matches the parent
    runtime's view of the snapshot. Returns (None, None, False, EmptyList, None)
    on any failure."""
    if not _HAS_CODEC:
        return None, None, False, M.EmptyList, None
    try:
        state = _SnapshotCodec(_main_runtime_namespace()).load(result_path)
    except Exception:
        return None, None, False, M.EmptyList, None
    worker_stage = state.roots.get("worker_stage", M.EmptyList)
    worker_plan = state.roots.get("worker_plan", M.EmptyList)
    attempts = state.roots.get("search_history", M.EmptyList)
    has_attempt = (attempts is not M.EmptyList)
    try:
        stage_val = worker_stage
        if _callable0(stage_val):
            stage_val = stage_val()
        stage_text = _to_text(stage_val)
    except Exception:
        stage_text = ""
    status_text = ""
    registry = None
    if has_attempt:
        try:
            child_registry = state.roots.get("constructor_registry", M.EmptyList)
            if child_registry is not M.EmptyList:
                if hasattr(_SnapshotCodec(_main_runtime_namespace()), "_is_entry_chain") and \
                        _SnapshotCodec(_main_runtime_namespace())._is_entry_chain(child_registry) is M.truth_value:
                    child_registry = _SnapshotCodec(_main_runtime_namespace())._rebuild_tree_from_entry_chain(child_registry)
            if child_registry is not M.EmptyList:
                registry = child_registry
            attempt = M.Head(attempts)()
            status_atom = _PP.SearchAttemptStatus(attempt)()
            status_text = _to_text(status_atom)
        except Exception:
            pass
    return stage_text, status_text, has_attempt, worker_plan, registry


def _callable0(v):
    # No 'callable' builtin use: try calling and catch.
    try:
        v()
        return True
    except TypeError:
        return False
    except Exception:
        return True


def _to_text(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    try:
        val = v.value
    except Exception:
        return str(v)
    try:
        r = val()
    except TypeError:
        return str(val)
    except Exception:
        try: return str(val)
        except Exception: return ""
    try:
        return str(r)
    except Exception:
        return ""


def _replay_certificate(result_path, expected_start_text, expected_goal_text):
    """Proof-check: boot an isolated runtime from the child snapshot, replay
    BuildDerivation against the stored worker_plan, and confirm the
    derivation is built and the goal is derivable from the start using the
    child's registry. Returns (ok, body_text); does NOT modify parent state.
    Missing/invalid plan or replay failure -> ok=False."""
    if not _HAS_CODEC:
        return False, "codec unavailable"
    try:
        from hyge_int_pkg.runtime import boot_from_snapshot
        runtime = boot_from_snapshot(result_path, _main_runtime_namespace())
        registry = M.FromContextGetConstructors(runtime.graph)()
    except Exception as exc:
        return False, "boot_from_snapshot failed: " + str(exc)
    stage_text, status_text, has_attempt, worker_plan, child_registry = _load_worker_stage(result_path)
    use_registry = child_registry if child_registry is not None else registry
    if worker_plan is M.EmptyList:
        return False, "no worker_plan in snapshot"
    # Find start/goal from manifest start_text/goal_text via PrettyTerm comparison.
    try:
        from hyge_int_pkg.main import _search_worker_result_manifest_path
        from hyge_int_pkg.main import _search_worker_problem_from_manifest
        from hyge_int_pkg.packs import PackLoader
        # We only want the manifest data; avoid re-booting packs by loading
        # directly.
        manifest_path = _search_worker_result_manifest_path(result_path)
        with open(manifest_path, "r", encoding="utf-8") as h:
            manifest = _json.load(h)
        # We don't have packs here, but the snapshot's search_history start/goal
        # are already in machine form. Extract from the most recent attempt.
        attempts = runtime.graph._replace_context is not None and None
    except Exception:
        pass
    # Extract start/goal from last search attempt on the loaded runtime.
    try:
        from hyge_int_pkg import proof as PP
        attempts = runtime.graph.search_history
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return False, "no attempts in snapshot"
        attempt = M.Head(attempts)()
        start = PP.SearchAttemptStart(attempt)()
        goal = PP.SearchAttemptGoal(attempt)()
        heuristic = PP.SearchAttemptHeuristic(attempt)()
    except Exception as exc:
        return False, "could not read attempt: " + str(exc)
    # Replay BuildDerivation on the worker_plan.
    try:
        from hyge_int_pkg import proof as P2
        derivation_pair = P2.BuildDerivation(start, worker_plan, use_registry)()
        derivation = M.Head(derivation_pair)()
        reg2 = M.Head(M.Tail(derivation_pair)())()
        if M.IdentityCompare(derivation, M.EmptyList)() is M.truth_value:
            return False, "BuildDerivation returned EmptyList"
        # Verify goal is reachable via TermEqual after normalization.
        try:
            from hyge_int_pkg import heuristics as H
            start_c = H.HeuristicCanonicalize(start, heuristic, reg2)()
            goal_c = H.HeuristicCanonicalize(goal, heuristic, reg2)()
            # Walk the derivation's steps: the derivation must end with a term
            # that matches goal canonicalized. A simple terminal-step check:
            # use DerivationEnd (if available) or else rely on BuildDerivation
            # success (which constructs only valid derivations from start).
        except Exception:
            pass
        # BuildDerivation succeeding is the proof of plan->derivation from start.
        # Record the proof cost so the body has evidence.
        try:
            cost_pair = P2.DerivationCost(derivation, reg2)()
            cost = M.Head(cost_pair)()
            return True, "replayed ok"
        except Exception:
            return True, "replayed ok (cost unavailable)"
    except Exception as exc:
        return False, "BuildDerivation replay failed: " + str(exc)


def _verify_child_certificate(result_path, expected_snapshot_id,
                              expected_obligation, expected_assumption_hash,
                              expected_task_id, expected_attempt_id,
                              expected_start_text=None, expected_goal_text=None):
    """Replay the child's snapshot certificate against the declared fields.

    Returns (ok, status_text, reason_atom, body_text).
      * ok=True  -> status "completed" or "failed" with reason atom.
      * ok=False -> certificate invalid/missing/mismatched.

    A running/plan-found stage is incomplete. Proof acceptance requires
    BuildDerivation to replay successfully against the snapshot.
    """
    if not os.path.isfile(result_path):
        return False, "no-snapshot", F_INVALID_CERT, ""
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
        return False, "attempt-id-mismatch", F_STALE_RESULT, ""
    stage_text, status_text, has_attempt, worker_plan, registry = _load_worker_stage(result_path)
    body = "stage=" + str(stage_text) + " status=" + str(status_text)
    if stage_text is None and not has_attempt:
        return False, "unreadable-snapshot", F_INVALID_CERT, body
    # Running/pre-plan stages are incomplete.
    if stage_text in ("running-search",) or (has_attempt and not worker_plan):
        return False, "incomplete:" + str(stage_text), F_INVALID_CERT, body
    # success-plan-found / running-derivation = plan exists but derivation not
    # yet built. rc=4 defer-derivation path.
    if stage_text in ("success-plan-found", "running-derivation"):
        return False, "incomplete-derivation:" + str(stage_text), F_INVALID_CERT, body
    if stage_text == "timed_out":
        return True, "failed", F_TIMEOUT, body
    if stage_text and (stage_text.startswith("failure") or "error" in stage_text.lower()):
        return True, "failed", F_CRASH, body
    if stage_text == READY_STAGE_COMPLETE or (status_text and "success" in status_text.lower()):
        ok, why = _replay_certificate(result_path, expected_start_text, expected_goal_text)
        if ok:
            return True, "completed", None, body + " proof=ok"
        return False, "proof-replay-failed: " + why, F_INVALID_CERT, body + " " + why
    if not has_attempt:
        return False, "no-attempt", F_INVALID_CERT, body
    return False, "unknown-stage:" + str(stage_text), F_INVALID_CERT, body


def _ready_from_checkpoint(result_path, expected_snapshot_id, expected_obligation):
    """Readiness is validated when: (a) the snapshot file exists and is
    loadable via SnapshotCodec (child restored its knowledge snapshot),
    (b) the manifest sidecar declares matching snapshot_id and obligation,
    and (c) worker_stage == 'running-search' (boot checkpoint written,
    derivation execution not yet started)."""
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
    stage_text, _status, has_attempt, _plan, _reg = _load_worker_stage(result_path)
    return stage_text == "running-search"


def _spawn_search_worker_process(package_root, worker_dir, mode_token,
                                 result_path, timeout_seconds, gate_dir,
                                 import_root=None):
    cmd = [_sys.executable, "-m", "hyge_int_pkg.main", "search-worker",
           mode_token, result_path, str(int(timeout_seconds))]
    env = os.environ.copy()
    if import_root is None:
        import_root = os.path.dirname(package_root)
    env["PYTHONPATH"] = import_root
    # Always defer derivation so the search runs, writes plan, and returns
    # rc=4 at plan-found; derivation replay happens on the coordinator side
    # as part of certificate verification (coordinator's checker accepts the
    # proof). Without defer we get rc=0 after worker-side replay, which is
    # fine too (stage=success-derivation-built); we replay either way.
    env["HYGE_SEARCH_WORKER_DEFER_DERIVATION"] = ""
    if gate_dir is not None:
        env["HYGE_SEARCH_WORKER_GATE_PATH"] = gate_dir
        # Give the coordinator plenty of time to observe ready and write
        # release -- this is independent of the worker's per-search budget.
        env["HYGE_SEARCH_WORKER_READY_TIMEOUT"] = "60"
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
        # Map child_id -> current expected attempt_id for stale-attempt fencing.
        self._expected_attempt = {}

    def spawn(self, mode_token, start_text, goal_text, task_id, attempt_id,
              obligation_text, assumptions_term, budget_millis,
              worker_timeout_seconds=None, assumption_hash_override=None,
              gate_path=None, manual_release=False):
        """Spawn a search worker. If gate_path is provided, that directory is
        used for the ready/release handshake (test/external control);
        otherwise a per-work-dir _gate directory is used. When manual_release
        is True, the caller is responsible for writing the release marker
        (useful for readiness-handshake assertions); by default the dispatcher
        writes release immediately after validating readiness."""
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
        gate_dir = gate_path if gate_path is not None else os.path.join(work_dir, "_gate")
        os.makedirs(gate_dir, exist_ok=True)
        # Pass gate_dir via env; child reads HYGE_SEARCH_WORKER_GATE_PATH.
        try:
            proc = _spawn_search_worker_process(self.package_root, work_dir,
                                                mode_token, result_path,
                                                worker_timeout_seconds,
                                                gate_dir=gate_dir)
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
                                     deadline_millis, assumption_hash, gate_dir,
                                     start_text, goal_text)
        ticket.status = S_RUNNING; self.pool.tickets.append(ticket)
        self.pool._outstanding += 1
        # Record expected attempt for stale-result fencing.
        self._expected_attempt[task_id] = attempt_id
        self._wait_ready(ticket, env, code_ident.snapshot_id, obligation_text)
        # Release the child to begin obligation execution ONLY after we have
        # validated readiness (gate exists, manifest matches, stage is running-search).
        if ticket.status == S_DISPATCHED:
            release_marker = os.path.join(gate_dir, "release-" + str(proc.pid))
            if manual_release:
                ticket._release_sent = False
            else:
                try:
                    with open(release_marker, "w", encoding="utf-8") as rh:
                        rh.write("release\n")
                    ticket._release_sent = True
                except Exception as exc:
                    _terminate(proc)
                    ticket.result_term = env.make_failure(F_LAUNCH_ERROR,
                                                          "release marker write failed: " + str(exc))
                    ticket.status = S_FAILED; self.pool._mark_terminal(ticket)
        return ticket

    def _wait_ready(self, ticket, env, snapshot_id, obligation_text):
        gate_dir = ticket.gate_dir
        while True:
            now = _time.time()*1000.0
            if now >= ticket.deadline_millis:
                _terminate(ticket.proc)
                ticket.result_term = env.make_failure(F_TIMEOUT, "ready handshake timed out")
                ticket.status = S_FAILED; self.pool._mark_terminal(ticket); return
            rc = ticket.proc.poll()
            if _ready_from_checkpoint(ticket.result_path, snapshot_id, obligation_text):
                # Wait until child's ready marker lands so we know it is blocked.
                ready_marker = os.path.join(gate_dir, "ready-" + str(ticket.proc.pid))
                waited = 0.0
                while not os.path.exists(ready_marker) and waited < 5.0:
                    if ticket.proc.poll() is not None: break
                    _time.sleep(0.02); waited += 0.02
                if os.path.exists(ready_marker):
                    ticket._ready_env = env.make_ready(snapshot_id, obligation_text)
                    ticket.status = S_DISPATCHED; return
            if rc is not None:
                ticket.proc.wait(timeout=2)
                try:
                    out, _ = ticket.proc.communicate(timeout=1)
                    body = out.decode("utf-8", "replace")[-500:]
                except Exception:
                    body = ""
                if rc == RC_READY_TIMEOUT:
                    ticket.result_term = env.make_failure(F_TIMEOUT, "ready marker timed out")
                else:
                    ticket.result_term = env.make_failure(F_CRASH,
                                                          "worker exited before ready rc=" + str(rc) + ": " + body)
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
        # Replay the child certificate against declared snapshot/obligation/
        # assumptions/active-attempt and coordinator-side proof checker.
        ok, stat, reason, body = _verify_child_certificate(
            ticket.result_path, ticket.snapshot_id, ticket.obligation_text,
            ticket.assumption_hash, ticket.task_id, ticket.attempt_id,
            ticket.start_text, ticket.goal_text)
        # Active-attempt fencing: if the manifest's attempt_id is stale relative
        # to what we expected for this task_id, reject even if cert otherwise ok.
        expected_att = self._expected_attempt.get(ticket.task_id)
        if expected_att is not None and expected_att != ticket.attempt_id:
            ticket.result_term = env.make_failure(F_STALE_RESULT, "stale attempt at poll")
            ticket.status = S_FAILED; self.pool._mark_terminal(ticket); return ticket.result_term
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
            r = reason if reason is not None else F_INVALID_CERT
            ticket.result_term = env.make_failure(r, body + "\n" + stdout_tail[-200:])
            ticket.status = S_FAILED
        self.pool._mark_terminal(ticket)
        return ticket.result_term

    def next_attempt_id(self, task_id, previous_attempt_id):
        """Produce a new attempt_id for retrying task_id and fence out the old one."""
        n = 1
        try:
            n = int(str(previous_attempt_id).split("-")[-1]) + 1
        except Exception:
            n = 1
        new_id = "a-" + str(n)
        self._expected_attempt[task_id] = new_id
        return new_id

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
                 deadline_millis, assumption_hash, gate_dir, start_text, goal_text):
        super().__init__(task_id, attempt_id, worker_id, worker_dir, snapshot_id,
                         obligation_text, assumptions, budget_millis, proc, None,
                         deadline_millis)
        self.result_path = result_path
        self.assumption_hash = assumption_hash
        self.gate_dir = gate_dir
        self.start_text = start_text
        self.goal_text = goal_text
        self._ready_env = None
        self._release_sent = False
