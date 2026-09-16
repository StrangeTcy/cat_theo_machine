"""Bounded worker runtime (C-A). Reuses the existing resident pool in
search.compare_executors and adds: max_workers=2, explicit 'spawn' start
method, per-task isolated working directory, snapshot-identity pre-flight
(and fresh-process restore cross-check), readiness-ack handshake,
task_id/attempt_id + declared snapshot/obligation/assumptions on every
envelope, budgets/timeouts/cancellation/cleanup. Crashes and timeouts
become machine failure terms (F_CRASH/F_TIMEOUT), never proof failure.
"""
from __future__ import annotations

import atexit as _atexit
import multiprocessing as _mp
import os
import shutil as _shutil
import time as _time

import hyge_cc.machine as M
import hyge_cc.programme_c as P
import hyge_cc.programme_c.snapshot_id as _sid
from hyge_cc.programme_c import (
    S_RUNNING, S_COMPLETED, S_FAILED, S_CANCELLED, S_DISPATCHED, S_READY,
    F_LAUNCH_ERROR, F_TIMEOUT, F_CRASH, F_CANCELLED, F_SNAPSHOT_MISMATCH,
    F_INVALID_CERT,
    K_TASK_ID, K_ATTEMPT_ID, K_WORKER_ID, K_STATUS, K_KIND, K_BODY,
    K_SNAPSHOT_ID, K_OBLIGATION, K_ASSUMPTIONS, K_ASSUMPTION_HASH, K_BUDGET, K_REASON,
    K_DECLARED_SNAPSHOT, K_DECLARED_OBLIGATION,
    alist_put, alist_get,
    text_atom, int_atom,
    F_MALFORMED_JOURNAL,
)

MAX_WORKERS = 2
EXPLICIT_START_METHOD = "spawn"
READY_ACK_KIND = "ready"
RESULT_KIND = "result"
FAILURE_KIND = "failure"


class WorkerEnvelope:
    def __init__(self, task_id, attempt_id, worker_id):
        self.task_id = task_id; self.attempt_id = attempt_id; self.worker_id = worker_id

    def make_ready(self, snapshot_id, obligation_text):
        e = M.EmptyList
        e = alist_put(e, K_KIND, text_atom(READY_ACK_KIND))
        e = alist_put(e, K_TASK_ID, text_atom(self.task_id))
        e = alist_put(e, K_ATTEMPT_ID, text_atom(self.attempt_id))
        e = alist_put(e, K_WORKER_ID, text_atom(self.worker_id))
        e = alist_put(e, K_STATUS, S_READY)
        e = alist_put(e, K_DECLARED_SNAPSHOT, text_atom(snapshot_id))
        e = alist_put(e, K_DECLARED_OBLIGATION, text_atom(obligation_text))
        return e

    def make_result(self, body_text, snapshot_id, obligation_text, assumption_hash, budget_text):
        e = M.EmptyList
        e = alist_put(e, K_KIND, text_atom(RESULT_KIND))
        e = alist_put(e, K_TASK_ID, text_atom(self.task_id))
        e = alist_put(e, K_ATTEMPT_ID, text_atom(self.attempt_id))
        e = alist_put(e, K_WORKER_ID, text_atom(self.worker_id))
        e = alist_put(e, K_STATUS, S_COMPLETED)
        e = alist_put(e, K_BODY, text_atom(body_text))
        e = alist_put(e, K_DECLARED_SNAPSHOT, text_atom(snapshot_id))
        e = alist_put(e, K_DECLARED_OBLIGATION, text_atom(obligation_text))
        e = alist_put(e, K_ASSUMPTION_HASH, text_atom(assumption_hash or "0"))
        e = alist_put(e, K_BUDGET, text_atom(budget_text))
        return e

    def make_failure(self, reason_term, detail_text):
        e = M.EmptyList
        e = alist_put(e, K_KIND, text_atom(FAILURE_KIND))
        e = alist_put(e, K_TASK_ID, text_atom(self.task_id))
        e = alist_put(e, K_ATTEMPT_ID, text_atom(self.attempt_id))
        e = alist_put(e, K_WORKER_ID, text_atom(self.worker_id))
        e = alist_put(e, K_STATUS, S_FAILED)
        e = alist_put(e, K_BODY, text_atom(detail_text))
        e = alist_put(e, K_REASON, reason_term)
        return e


class WorkerTicket:
    def __init__(self, task_id, attempt_id, worker_id, worker_dir, snapshot_id,
                 obligation_text, assumptions_term, budget_millis, proc, conn, deadline_millis):
        self.task_id = task_id; self.attempt_id = attempt_id; self.worker_id = worker_id
        self.worker_dir = worker_dir; self.snapshot_id = snapshot_id
        self.obligation_text = obligation_text; self.assumptions = assumptions_term
        self.budget_millis = budget_millis; self.proc = proc; self.conn = conn
        self.deadline_millis = deadline_millis
        self.status = S_FAILED  # overridden by caller
        self.result_term = M.EmptyList
        self._terminal = False


class BoundedWorkerPool:
    def __init__(self, scratch_root, snapshot_ident, check_restore=True):
        self.scratch_root = scratch_root; self.snapshot_ident = snapshot_ident
        self.workers_dir = os.path.join(scratch_root, "workers")
        os.makedirs(self.workers_dir, exist_ok=True)
        self.tickets = []; self._outstanding = 0; self._next_slot = 0
        self._mp_context = _mp.get_context(EXPLICIT_START_METHOD)
        self._check_restore = check_restore
        _atexit.register(self.shutdown)

    def _new_worker_id(self):
        self._next_slot += 1; return "w-" + str(self._next_slot)

    def _isolation_dir(self, worker_id):
        d = os.path.join(self.workers_dir, worker_id)
        os.makedirs(d, exist_ok=True); return d

    def _mark_terminal(self, t):
        if not t._terminal:
            t._terminal = True; self._outstanding -= 1

    def spawn_worker(self, worker_entry, worker_args, task_id, attempt_id,
                     obligation_text, assumptions_term, budget_millis, snapshot_path):
        worker_id = self._new_worker_id()
        work_dir = self._isolation_dir(worker_id)
        env = WorkerEnvelope(task_id, attempt_id, worker_id)
        # Snapshot pre-flight: identity match AND fresh-process restore equivalence.
        ok, actual, _ = _sid.verify_identity(snapshot_path, self.snapshot_ident)
        if not ok:
            return self._prefailed(env, task_id, attempt_id, worker_id, work_dir,
                                   F_SNAPSHOT_MISMATCH, "snapshot identity mismatch")
        if self._check_restore:
            ok2, got = _sid.verify_restore_fresh_process(snapshot_path, self.snapshot_ident)
            if not ok2:
                return self._prefailed(env, task_id, attempt_id, worker_id, work_dir,
                                       F_SNAPSHOT_MISMATCH, "fresh-restore mismatch: " + str(got))
        if self._outstanding >= MAX_WORKERS:
            return self._prefailed(env, task_id, attempt_id, worker_id, work_dir,
                                   F_LAUNCH_ERROR, "max_workers exceeded")
        parent_conn, child_conn = self._mp_context.Pipe(duplex=True)
        proc = self._mp_context.Process(
            target=_worker_bootstrap,
            args=(child_conn, work_dir, worker_entry, worker_args,
                  task_id, attempt_id, worker_id, self.snapshot_ident.snapshot_id,
                  obligation_text, _assumption_hash(assumptions_term), budget_millis,
                  snapshot_path),
            name="hyge-c-" + worker_id,
        )
        proc.start(); child_conn.close()
        ticket = WorkerTicket(task_id, attempt_id, worker_id, work_dir,
                              self.snapshot_ident.snapshot_id, obligation_text,
                              assumptions_term, budget_millis, proc, parent_conn,
                              _time.time()*1000.0 + budget_millis)
        ticket.status = S_RUNNING; self.tickets.append(ticket); self._outstanding += 1
        ready = _poll_ack(parent_conn, ticket.deadline_millis, worker_id, task_id, attempt_id)
        if isinstance(ready, str) and ready == "__crash__":
            ticket.result_term = env.make_failure(F_CRASH, "worker exited before ready")
            ticket.status = S_FAILED; self._mark_terminal(ticket); return ticket
        if ready is None:
            _terminate(proc)
            ticket.result_term = env.make_failure(F_TIMEOUT, "ready handshake timed out")
            ticket.status = S_FAILED; self._mark_terminal(ticket); return ticket
        # Validate ready acks declare expected snapshot/obligation.
        decl_snap = alist_get(ready, K_DECLARED_SNAPSHOT).value
        decl_ob = alist_get(ready, K_DECLARED_OBLIGATION).value
        if decl_snap != self.snapshot_ident.snapshot_id or decl_ob != obligation_text:
            _terminate(proc)
            ticket.result_term = env.make_failure(F_INVALID_CERT, "ready ack has wrong snapshot/obligation")
            ticket.status = S_FAILED; self._mark_terminal(ticket); return ticket
        ticket.status = S_DISPATCHED
        return ticket

    def _prefailed(self, env, task_id, attempt_id, worker_id, work_dir, reason, detail):
        t = WorkerTicket(task_id, attempt_id, worker_id, work_dir,
                         self.snapshot_ident.snapshot_id, "", M.EmptyList, 0, None, None, 0)
        t.result_term = env.make_failure(reason, detail)
        t.status = S_FAILED; t._terminal = True; self.tickets.append(t); return t

    def poll(self, ticket):
        if ticket.proc is None:
            return ticket.result_term
        if ticket.status != S_RUNNING and ticket.status != S_DISPATCHED:
            return ticket.result_term
        if not ticket.proc.is_alive():
            ticket.proc.join(timeout=1)
            env = WorkerEnvelope(ticket.task_id, ticket.attempt_id, ticket.worker_id)
            msg = _recv_nonblock(ticket.conn)
            if msg is not None and not isinstance(msg, str) and alist_get(msg, K_KIND).value == RESULT_KIND:
                ticket.result_term = msg; ticket.status = S_COMPLETED
            else:
                code = ticket.proc.exitcode
                detail = "worker exited with code " + str(code)
                ticket.result_term = env.make_failure(F_CRASH, detail)
                ticket.status = S_FAILED
            self._mark_terminal(ticket); return ticket.result_term
        now = _time.time()*1000.0
        if now >= ticket.deadline_millis:
            _terminate(ticket.proc)
            env = WorkerEnvelope(ticket.task_id, ticket.attempt_id, ticket.worker_id)
            ticket.result_term = env.make_failure(F_TIMEOUT, "budget exhausted")
            ticket.status = S_FAILED; self._mark_terminal(ticket); return ticket.result_term
        msg = _recv_nonblock(ticket.conn)
        if msg is None or isinstance(msg, str):
            return M.EmptyList
        kind = alist_get(msg, K_KIND).value
        if kind == RESULT_KIND:
            ticket.result_term = msg; ticket.status = S_COMPLETED
        else:
            env = WorkerEnvelope(ticket.task_id, ticket.attempt_id, ticket.worker_id)
            ticket.result_term = env.make_failure(F_CRASH, "unexpected envelope kind: " + kind)
            ticket.status = S_FAILED
        self._mark_terminal(ticket); return ticket.result_term

    def cancel(self, ticket):
        if ticket.proc is None:
            return ticket.result_term
        if ticket.status == S_RUNNING or ticket.status == S_DISPATCHED:
            _terminate(ticket.proc)
            env = WorkerEnvelope(ticket.task_id, ticket.attempt_id, ticket.worker_id)
            ticket.result_term = env.make_failure(F_CANCELLED, "cancelled by pool")
            ticket.status = S_CANCELLED; self._mark_terminal(ticket)
        return ticket.result_term

    def cleanup(self, ticket):
        if ticket.status == S_RUNNING or ticket.status == S_DISPATCHED:
            return
        try:
            if ticket.conn is not None:
                ticket.conn.close()
        except Exception:
            pass
        if ticket.proc is not None and ticket.proc.is_alive():
            _terminate(ticket.proc)
        if os.path.isdir(ticket.worker_dir):
            _shutil.rmtree(ticket.worker_dir, ignore_errors=True)

    def shutdown(self):
        for t in self.tickets:
            if not t._terminal:
                self.cancel(t)
            self.cleanup(t)


def _assumption_hash(term):
    h = 0
    cur = term
    while M.IsPair(cur)() is M.truth_value:
        v = P._atom_text(M.Head(cur)())
        try: v + ""
        except TypeError: v = str(v)
        h = (h * 1315423911) ^ hash(v); cur = M.Tail(cur)()
    return format(h & 0xFFFFFFFFFFFFFFFF, "016x")


def _terminate(proc):
    try:
        if proc.is_alive():
            proc.terminate(); proc.join(timeout=2)
            if proc.is_alive():
                proc.kill(); proc.join(timeout=2)
    except Exception:
        pass


def _recv_nonblock(conn):
    try:
        if conn.poll(timeout=0):
            try:
                return conn.recv()
            except EOFError:
                return "__crash__"
    except Exception:
        return "__crash__"
    return None


def _poll_ack(conn, deadline_millis, worker_id, task_id, attempt_id):
    while True:
        now = _time.time()*1000.0
        if now >= deadline_millis:
            return None
        msg = _recv_nonblock(conn)
        if msg == "__crash__":
            return "__crash__"
        if msg is None:
            _time.sleep(0.01); continue
        if not isinstance(msg, str) and alist_get(msg, K_KIND).value == READY_ACK_KIND:
            return msg
        # Skip stray messages; continue waiting for ready.


def _worker_bootstrap(conn, work_dir, entry_fn, entry_args, task_id, attempt_id,
                      worker_id, snapshot_id, obligation_text, assumption_hash,
                      budget_millis, snapshot_path):
    os.chdir(work_dir)
    env = WorkerEnvelope(task_id, attempt_id, worker_id)
    try:
        conn.send(env.make_ready(snapshot_id, obligation_text))
        body_text = entry_fn(conn, work_dir, entry_args, task_id, attempt_id,
                             worker_id, snapshot_id, obligation_text, assumption_hash,
                             budget_millis, snapshot_path)
        conn.send(env.make_result(body_text, snapshot_id, obligation_text,
                                  assumption_hash or "0", str(budget_millis)))
    except Exception as exc:
        try:
            conn.send(env.make_failure(F_CRASH, str(exc)))
        except Exception:
            pass
    finally:
        try: conn.close()
        except Exception: pass
