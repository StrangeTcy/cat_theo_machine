"""C-C tests: checked AND/OR joins, stale-result rejection, invalid-certificate
rejection, incompatible-assumption rejection, serial admission gate order,
end-to-end two workers -> checked parent join.
"""
from __future__ import annotations

import datetime as _dt, json as _json, os, sys, tempfile, time as _time, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import hyge_int_pkg.machine as M
import hyge_int_pkg.programme_c as P
import hyge_int_pkg.programme_c.join as J
import hyge_int_pkg.programme_c.snapshot_id as sid
import hyge_int_pkg.programme_c.worker as W


def _today(): return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
def _art():
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", _today())
    os.makedirs(d, exist_ok=True); return d


def _min_snap(p):
    with open(p, "w") as fh:
        fh.write('{"header":{},"roots":{"r":"x"},"symbols":{},"objects":[{"id":1}]}')


def _env(task_id, attempt_id, status, snapshot_id, obligation, ah="",
         kind="result", reason=None, body="ok"):
    e = M.EmptyList
    e = P.alist_put(e, P.K_KIND, P.text_atom(kind))
    e = P.alist_put(e, P.K_STATUS, P.text_atom(status))
    e = P.alist_put(e, P.K_TASK_ID, P.text_atom(task_id))
    e = P.alist_put(e, P.K_ATTEMPT_ID, P.text_atom(attempt_id))
    e = P.alist_put(e, P.K_WORKER_ID, P.text_atom("w0"))
    e = P.alist_put(e, P.K_DECLARED_SNAPSHOT, P.text_atom(snapshot_id))
    e = P.alist_put(e, P.K_DECLARED_OBLIGATION, P.text_atom(obligation))
    e = P.alist_put(e, P.K_BODY, P.text_atom(body))
    if ah:
        e = P.alist_put(e, P.K_ASSUMPTION_HASH, P.text_atom(ah))
    if reason is not None:
        e = P.alist_put(e, P.K_REASON, reason)
    return e


def _make_ident_and_pool(td):
    snap = os.path.join(td, "s.json"); _min_snap(snap)
    ident, _ = sid.compute_identity(snap); sid.write_sidecar(snap, ident)
    return ident, snap, W.BoundedWorkerPool(td, ident, check_restore=False)


class JoinTests(unittest.TestCase):
    def test_and_join_completes_all_children(self):
        ja = J.JoinAdmission()
        specs = [J.child_spec(c, "ob-"+c, "SID", "") for c in ("a","b","c")]
        ja.create_claim("p", J.COMBINATOR_AND, specs)
        for c in ("a","b"):
            ok, r, rec = ja.deliver_child_result("p", _env(c,"att-1","completed","SID","ob-"+c))
            self.assertTrue(ok); self.assertEqual(rec.status, "running")
        ok, _, rec = ja.deliver_child_result("p", _env("c","att-1","completed","SID","ob-c"))
        self.assertTrue(ok); self.assertEqual(rec.status, "completed")

    def test_or_first_alternative(self):
        ja = J.JoinAdmission()
        specs = [J.child_spec(c, "ob-"+c, "SID", "") for c in ("a","b","c")]
        ja.create_claim("p", J.COMBINATOR_OR, specs)
        ok, _, rec = ja.deliver_child_result("p", _env("b","att-1","completed","SID","ob-b"))
        self.assertTrue(ok); self.assertEqual(rec.status, "completed")
        sel = P.alist_get(rec.accepted_result, P.text_atom("selected_child")).value
        self.assertEqual(sel, "b")

    def test_stale_superseded_rejected(self):
        ja = J.JoinAdmission()
        ja.create_claim("p", J.COMBINATOR_AND, [J.child_spec("a","ob-a","SID","")])
        # Pre-assign to att-1 (as dispatcher does) then deliver.
        ja.assign_child_attempt("p", "a", "att-1")
        ok, _, rec = ja.deliver_child_result("p", _env("a","att-1","completed","SID","ob-a"))
        self.assertTrue(ok); self.assertEqual(rec.status, "completed")
        ok2, reason, _ = ja.deliver_child_result("p", _env("a","att-2","completed","SID","ob-a"))
        self.assertFalse(ok2)
        self.assertTrue(M.IdentityCompare(reason, P.F_STALE_RESULT)() is M.truth_value)
        # Duplicate of accepted is idempotent.
        ok3, _, _ = ja.deliver_child_result("p", _env("a","att-1","completed","SID","ob-a"))
        self.assertTrue(ok3)

    def test_invalid_cert_unknown_child(self):
        ja = J.JoinAdmission()
        ja.create_claim("p", J.COMBINATOR_AND, [J.child_spec("a","ob-a","SID","")])
        ok, reason, _ = ja.deliver_child_result("p", _env("bogus","att-1","completed","SID","ob-bogus"))
        self.assertFalse(ok)
        self.assertTrue(M.IdentityCompare(reason, P.F_UNKNOWN_CHILD)() is M.truth_value)

    def test_snapshot_mismatch_rejected(self):
        ja = J.JoinAdmission()
        ja.create_claim("p", J.COMBINATOR_AND, [J.child_spec("a","ob-a","SID","")])
        ok, reason, _ = ja.deliver_child_result("p", _env("a","att-1","completed","WRONG","ob-a"))
        self.assertFalse(ok)
        self.assertTrue(M.IdentityCompare(reason, P.F_SNAPSHOT_MISMATCH)() is M.truth_value)

    def test_obligation_mismatch_rejected(self):
        ja = J.JoinAdmission()
        ja.create_claim("p", J.COMBINATOR_AND, [J.child_spec("a","ob-a","SID","")])
        ok, reason, _ = ja.deliver_child_result("p", _env("a","att-1","completed","SID","ob-OTHER"))
        self.assertFalse(ok)
        self.assertTrue(M.IdentityCompare(reason, P.F_SCOPE_VIOLATION)() is M.truth_value)

    def test_assumption_hash_incompatible(self):
        ja = J.JoinAdmission()
        ja.create_claim("p", J.COMBINATOR_AND, [J.child_spec("a","ob-a","SID","deadbeef")])
        ok, reason, _ = ja.deliver_child_result("p", _env("a","att-1","completed","SID","ob-a", ah="cafebabe"))
        self.assertFalse(ok)
        self.assertTrue(M.IdentityCompare(reason, P.F_INCOMPATIBLE_ASSUMPTIONS)() is M.truth_value)

    def test_execution_failure_distinct_from_refutation(self):
        ja = J.JoinAdmission()
        ja.create_claim("p", J.COMBINATOR_AND, [J.child_spec("a","ob-a","SID","")])
        env = _env("a","att-1","failed","SID","ob-a", reason=P.F_CRASH)
        ok, _, rec = ja.deliver_child_result("p", env)
        self.assertTrue(ok)
        self.assertEqual(rec.status, "completed")  # parent join completes with failure
        kind = P.alist_get(rec.accepted_result, P.K_KIND).value
        self.assertEqual(kind, "failure")
        reason = P.alist_get(rec.accepted_result, P.K_REASON)
        self.assertTrue(M.IdentityCompare(reason, P.F_CRASH)() is M.truth_value)

    def test_and_all_refuted(self):
        ja = J.JoinAdmission()
        ja.create_claim("p", J.COMBINATOR_AND, [J.child_spec("a","ob-a","SID","")])
        env = _env("a","att-1","failed","SID","ob-a", reason=P.F_REFRUTATION)
        ok, _, rec = ja.deliver_child_result("p", env)
        self.assertTrue(ok)
        self.assertEqual(rec.status, "completed")
        kind = P.alist_get(rec.accepted_result, P.K_KIND).value
        self.assertEqual(kind, "refuted")


class AdmissionTests(unittest.TestCase):
    def test_serial_gate_order(self):
        ja = J.JoinAdmission()
        specs = [J.child_spec("a","ob-a","SID","")]
        ja.create_claim("p", J.COMBINATOR_AND, specs)
        ja.deliver_child_result("p", _env("a","att-1","completed","SID","ob-a"))
        pid = ja.enqueue_proposal("law-x", "p", [J.GATE_VALIDITY, J.GATE_RENT, J.GATE_HUMAN])
        v_calls=[]; r_calls=[]; h_calls=[]
        def v(e, acc=0, ver=0): v_calls.append(1); return True
        def r(e, acc=0, ver=0): r_calls.append(1); return False
        def h(e, acc=0, ver=0): h_calls.append(1); return True
        ok, _, det = ja.admit_next(v, r, h)
        self.assertFalse(ok); self.assertEqual(det, "rent hold"); self.assertEqual(v_calls+r_calls+h_calls, [1,1])
        v_calls=[]; r_calls=[]; h_calls=[]
        def rok(e, acc=0, ver=0): r_calls.append(1); return True
        def hno(e, acc=0, ver=0): h_calls.append(1); return False
        ok, _, det = ja.admit_next(v, rok, hno)
        self.assertFalse(ok); self.assertEqual(det, "awaiting human"); self.assertEqual(v_calls+r_calls+h_calls, [1,1,1])
        def hyes(e, acc=0, ver=0): h_calls.append(1); return True
        ok, _, det = ja.admit_next(v, rok, hyes)
        self.assertTrue(ok); self.assertEqual(det, "admitted")
        with open(os.path.join(_art(), "cc_serial_admission.log"), "w") as fh:
            fh.write("admitted " + pid + " after v->r->h sequence\n")


class EndToEndTests(unittest.TestCase):
    def test_two_workers_to_checked_parent_join(self):
        with tempfile.TemporaryDirectory() as td:
            ident, snap, pool = _make_ident_and_pool(td)
            ja = J.JoinAdmission()
            child_specs = [
                J.child_spec("c1","ob-c1",ident.snapshot_id,""),
                J.child_spec("c2","ob-c2",ident.snapshot_id,""),
            ]
            ja.create_claim("parent", J.COMBINATOR_AND, child_specs)
            t1 = pool.spawn_worker(_echo, {"label":"c1","sleep":0.05,"touch":"a.txt"},
                                   "c1","att-1","ob-c1", M.EmptyList, 5000, snap)
            t2 = pool.spawn_worker(_echo, {"label":"c2","sleep":0.05,"touch":"b.txt"},
                                   "c2","att-1","ob-c2", M.EmptyList, 5000, snap)
            deadline = _time.time() + 8.0
            results = {}
            while len(results) < 2 and _time.time() < deadline:
                for t in (t1, t2):
                    if t.task_id in results: continue
                    r = pool.poll(t)
                    if r is not M.EmptyList:
                        ok, reason, rec = ja.deliver_child_result("parent", r)
                        self.assertTrue(ok, "deliver failed: " + str(reason.value if reason is not None and reason is not M.EmptyList else reason))
                        results[t.task_id] = r
                _time.sleep(0.02)
            self.assertEqual(ja.claims["parent"].status, "completed")
            pool.cleanup(t1); pool.cleanup(t2); pool.shutdown()
            with open(os.path.join(_art(), "cc_end_to_end.log"), "w") as fh:
                fh.write("two workers -> AND join completed parent=parent\n")

    def test_stale_attempt_after_retry_does_not_overwrite(self):
        # Issue a first attempt that crashes, retry succeeds, late first result rejected.
        # Fencing also applies WHILE the retry is still running, not only when
        # it has completed.
        with tempfile.TemporaryDirectory() as td:
            ident, snap, pool = _make_ident_and_pool(td)
            ja = J.JoinAdmission()
            ja.create_claim("p", J.COMBINATOR_AND, [J.child_spec("a","ob-a",ident.snapshot_id,"")])
            # Assign first attempt (as dispatcher would).  Fence is active.
            ja.assign_child_attempt("p", "a", "att-1")
            # Stale-attempt rejection works before the retry is even dispatched:
            ok_pre, reason_pre, _ = ja.deliver_child_result(
                "p", _env("a","att-0","completed",ident.snapshot_id,"ob-a"))
            self.assertFalse(ok_pre)
            self.assertTrue(M.IdentityCompare(reason_pre, P.F_STALE_RESULT)() is M.truth_value)
            # Simulate retry: assign att-2, which supersedes att-1.
            ja.retry_child("p", "a", "att-2")
            # While att-2 is still running (child not terminal), a late att-1 envelope
            # is rejected by fencing BEFORE cert validation.
            ok_mid, reason_mid, _ = ja.deliver_child_result(
                "p", _env("a","att-1","completed",ident.snapshot_id,"ob-a"))
            self.assertFalse(ok_mid)
            self.assertTrue(M.IdentityCompare(reason_mid, P.F_STALE_RESULT)() is M.truth_value)
            # Now att-2 completes successfully.
            ok, _, rec = ja.deliver_child_result("p", _env("a","att-2","completed",ident.snapshot_id,"ob-a"))
            self.assertTrue(ok); self.assertEqual(rec.status, "completed")
            # Late att-1 result (e.g. a timeout-delayed packet) still rejected.
            ok2, reason, _ = ja.deliver_child_result("p", _env("a","att-1","completed",ident.snapshot_id,"ob-a"))
            self.assertFalse(ok2)
            self.assertTrue(M.IdentityCompare(reason, P.F_STALE_RESULT)() is M.truth_value)
            # Duplicate of att-2 accepted idempotently.
            ok3, _, _ = ja.deliver_child_result("p", _env("a","att-2","completed",ident.snapshot_id,"ob-a"))
            self.assertTrue(ok3)
            pool.shutdown()


def _echo(conn, work_dir, args, task_id, attempt_id, worker_id, sid_id, ob, ah, budget, snap_path):
    import time, json, os
    name = args.get("touch", "ok.txt")
    with open(os.path.join(work_dir, name), "w") as fh: fh.write("ok")
    time.sleep(args.get("sleep", 0.05))
    return json.dumps({"label":args.get("label",""),"worker_id":worker_id,"task_id":task_id}, sort_keys=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
