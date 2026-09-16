"""C-B tests: snapshot round-trip with fresh-process restore equivalence,
tamper detection, scope isolation (incl. assumption hash), duplicate import.
"""
from __future__ import annotations

import datetime as _dt
import json as _json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import hyge_cb.machine as M
import hyge_cb.programme_c as P
import hyge_cb.programme_c.snapshot_id as sid
import hyge_cb.programme_c.journal as jrn
import hyge_cb.programme_c.evidence as ev


def _today():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


def _art():
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", _today())
    os.makedirs(d, exist_ok=True)
    return d


def _min_snap(path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('{"header":{"format":"test"},"roots":{"r":"x"},"symbols":{"EmptyList":0},'
                 '"objects":[{"id":0,"k":"a"},{"id":1,"k":"b"},{"id":2,"k":"c"}]}')


class SnapTests(unittest.TestCase):
    def test_round_trip_and_verify(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "s.json"); _min_snap(p)
            ident, _ = sid.compute_identity(p); sid.write_sidecar(p, ident)
            ok, _, _ = sid.verify_identity(p, ident); self.assertTrue(ok)
            ident2 = sid.read_sidecar(p); self.assertEqual(ident.snapshot_id, ident2.snapshot_id)
            shutil.copy(sid.sidecar_path(p), os.path.join(_art(), "cb_snap_roundtrip.identity.json"))
            shutil.copy(p, os.path.join(_art(), "cb_snap_roundtrip.snapshot.json"))

    def test_tamper_detection(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "s.json"); _min_snap(p)
            ident, _ = sid.compute_identity(p); sid.write_sidecar(p, ident)
            with open(p) as fh: o = _json.load(fh)
            o["objects"].append({"id": 9});
            with open(p, "w") as fh: _json.dump(o, fh)
            ok, _, _ = sid.verify_identity(p, ident); self.assertFalse(ok)
            with open(os.path.join(_art(), "cb_tamper.log"), "w") as fh: fh.write("tamper ok=False\n")

    def test_fresh_process_restore_equivalence(self):
        """Verify that a fresh python process reading the snapshot arrives at
        the same digest."""
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "s.json"); _min_snap(p)
            ident, _ = sid.compute_identity(p); sid.write_sidecar(p, ident)
            ok, got = sid.verify_restore_fresh_process(p, ident)
            self.assertTrue(ok, "fresh-process digest mismatch: " + str(got))
            with open(os.path.join(_art(), "cb_fresh_restore.log"), "w") as fh:
                fh.write("fresh_process_digest=" + got + " expected=" + ident.snapshot_id + " ok=" + str(ok) + "\n")


class JournalTests(unittest.TestCase):
    def _assump(self, *items):
        t = M.EmptyList
        for s in items:
            t = M.Pair(P.text_atom(s), t)
        return t

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            jp = os.path.join(td, "w.jrnl")
            assump = self._assump("peano")
            j = jrn.open_journal(jp, "sid-1", "t1", "a1", assump, "d", "1s", "w0")
            jrn.observation(j, "trace", "ready"); jrn.proposal(j, "candidate_law", "x")
            jrn.close(j)
            loaded = jrn.load_journal(jp, "sid-1", "t1", "a1", assump)
            self.assertEqual(loaded.observation_count, 1)
            self.assertEqual(loaded.proposal_count, 1)
            shutil.copy(jp, os.path.join(_art(), "cb_journal_roundtrip.jrnl"))

    def test_truncated_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            jp = os.path.join(td, "w.jrnl")
            j = jrn.open_journal(jp, "s", "t", "a", M.EmptyList, "d", "1s", "w")
            jrn.observation(j, "trace", "x")
            j._closed = True; j._fh.close(); j._fh = None
            self.assertRaises(jrn.JournalTruncated,
                              lambda: jrn.load_journal(jp, "s", "t", "a"))

    def test_scope_misattribution_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            jp = os.path.join(td, "w.jrnl")
            j = jrn.open_journal(jp, "s", "t", "a", M.EmptyList, "d", "1s", "w")
            jrn.observation(j, "trace", "x"); jrn.close(j)
            self.assertRaises(jrn.JournalScope, lambda: jrn.load_journal(jp, "s2", "t", "a"))
            self.assertRaises(jrn.JournalScope, lambda: jrn.load_journal(jp, "s", "t2", "a"))
            self.assertRaises(jrn.JournalScope, lambda: jrn.load_journal(jp, "s", "t", "a2"))

    def test_assumption_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            jp = os.path.join(td, "w.jrnl")
            a1 = self._assump("peano")
            a2 = self._assump("zfc")
            j = jrn.open_journal(jp, "s", "t", "a", a1, "d", "1s", "w")
            jrn.close(j)
            self.assertRaises(jrn.JournalScope, lambda: jrn.load_journal(jp, "s", "t", "a", a2))

    def test_malformed_line_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            jp = os.path.join(td, "w.jrnl")
            with open(jp, "wb") as fh:
                fh.write(b'{"header":{"v":1,"snapshot_id":"s","task_id":"t","attempt_id":"a",'
                         b'"worker_id":"w","memory_profile":"d","budget":"b",'
                         b'"assumption_hash":"0000000000000000","assumptions":[]}}\n')
                fh.write(b"not json\n")
                fh.write(b'{"footer":{"closed":true,"seq":0}}\n')
            self.assertRaises(jrn.JournalMalformed, lambda: jrn.load_journal(jp, "s", "t", "a"))


class EvidenceTests(unittest.TestCase):
    def test_duplicate_import_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            ar_dir = os.path.join(td, "a"); jp = os.path.join(td, "w.jrnl")
            j = jrn.open_journal(jp, "s", "t", "a", M.EmptyList, "d", "1s", "w")
            jrn.observation(j, "trace", "h"); jrn.proposal(j, "candidate_policy", "p")
            jrn.close(j)
            loaded = jrn.load_journal(jp, "s", "t", "a")
            ar = ev.init_archive(ar_dir)
            n1o, n1p, d1o, d1p = ev.import_journal(ar, loaded)
            self.assertEqual((n1o, n1p, d1o, d1p), (1, 1, 0, 0))
            n2o, n2p, d2o, d2p = ev.import_journal(ar, loaded)
            self.assertEqual((n2o, n2p, d2o, d2p), (0, 0, 1, 1))
            oc, pc = ev.archive_counts(ar); self.assertEqual((oc, pc), (1, 1))
            shutil.copy(os.path.join(ar_dir, "manifest.json"),
                        os.path.join(_art(), "cb_dup_import.manifest.json"))

    def test_scope_isolation_between_workers(self):
        with tempfile.TemporaryDirectory() as td:
            ar = ev.init_archive(os.path.join(td, "a"))
            for w in ("w1", "w2"):
                jp = os.path.join(td, w + ".jrnl")
                j = jrn.open_journal(jp, "s", "t-" + w, "a1", M.EmptyList, "d", "1s", w)
                jrn.observation(j, "trace", w); jrn.close(j)
                ev.import_journal(ar, jrn.load_journal(jp, "s", "t-" + w, "a1"))
            oc, _ = ev.archive_counts(ar); self.assertEqual(oc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
