"""Worker journal (C-B §2-5). Per-attempt append log bound to snapshot/task/
attempt/assumptions/memory-profile/budget. Records observations
(trace/attempt/residual/counterfactual) and proposals (candidate_law/
candidate_policy, always inactive). Truncated/malformed/misattributed
journals are rejected by the loader.
"""
from __future__ import annotations

import io as _io
import json as _json
import os
import time as _time

import hyge_cb.machine as M
from hyge_cb.programme_c import (
    K_KIND, K_BODY, K_SEQUENCE, K_ENTRY_ID,
    K_TASK_ID, K_ATTEMPT_ID, K_WORKER_ID, K_SNAPSHOT_ID,
    K_ASSUMPTIONS, K_ASSUMPTION_HASH, K_MEMORY_PROFILE, K_BUDGET,
    alist_put, _atom_text,
    text_atom, int_atom,
    pair_list_to_py,
    F_MALFORMED_JOURNAL, F_TRUNCATED_JOURNAL, F_MISATTRIBUTED_JOURNAL,
)


OBSERVATION_KINDS = ("trace", "attempt", "residual", "counterfactual")
PROPOSAL_KINDS = ("candidate_law", "candidate_policy")
JOURNAL_VERSION = 1


class JournalError(Exception):
    reason_term = F_MALFORMED_JOURNAL


class JournalTruncated(JournalError):
    reason_term = F_TRUNCATED_JOURNAL


class JournalScope(JournalError):
    reason_term = F_MISATTRIBUTED_JOURNAL


class JournalMalformed(JournalError):
    reason_term = F_MALFORMED_JOURNAL


class LoadedJournal:
    def __init__(self, header, entries_term, observation_count, proposal_count):
        self.header = header
        self.entries_term = entries_term
        self.observation_count = observation_count
        self.proposal_count = proposal_count


class WorkerJournal:
    def __init__(self, fh, path, snapshot_id, task_id, attempt_id,
                 assumptions_term, memory_profile, budget, worker_id):
        self._fh = fh
        self.path = path
        self.snapshot_id = snapshot_id
        self.task_id = task_id
        self.attempt_id = attempt_id
        self.assumptions = assumptions_term
        self.memory_profile = memory_profile
        self.budget = budget
        self.worker_id = worker_id
        self.entries_term = M.EmptyList
        self._seq = 0
        self._closed = False


def _format_seq(seq):
    s = str(seq)
    while len(s) < 8:
        s = "0" + s
    return s


def _contains(seq, value):
    i = 0
    while i < len(seq):
        if seq[i] == value:
            return True
        i += 1
    return False


def _assumption_hash(term):
    h = 0
    cur = term
    while M.IsPair(cur)() is M.truth_value:
        h = (h * 1315423911) ^ hash(_atom_text(M.Head(cur)()))
        cur = M.Tail(cur)()
    return format(h & 0xFFFFFFFFFFFFFFFF, "016x")


def _assumptions_py(term):
    return pair_list_to_py(term, lambda a: a.value)


def _write_header(j):
    text = ('{"header":{'
            '"v":' + str(JOURNAL_VERSION)
            + ',"snapshot_id":' + _json.dumps(j.snapshot_id)
            + ',"task_id":' + _json.dumps(j.task_id)
            + ',"attempt_id":' + _json.dumps(j.attempt_id)
            + ',"worker_id":' + _json.dumps(j.worker_id)
            + ',"memory_profile":' + _json.dumps(j.memory_profile)
            + ',"budget":' + _json.dumps(j.budget)
            + ',"assumption_hash":' + _json.dumps(_assumption_hash(j.assumptions))
            + ',"assumptions":' + _json.dumps(_assumptions_py(j.assumptions))
            + '}}')
    _json.loads(text)
    j._fh.write(text.encode("utf-8"))
    j._fh.write(b"\n")


def _append(j, kind, record_text):
    if j._closed:
        raise RuntimeError("journal closed")
    j._seq += 1
    seq = j._seq
    entry_id = j.task_id + ":" + j.attempt_id + ":" + _format_seq(seq)
    env_text = ('{"seq":' + str(seq)
                + ',"entry_id":' + _json.dumps(entry_id)
                + ',"kind":' + _json.dumps(kind)
                + ',"record":' + record_text + '}')
    _json.loads(env_text)
    j._fh.write(env_text.encode("utf-8")); j._fh.write(b"\n"); j._fh.flush()
    entry = M.EmptyList
    entry = alist_put(entry, K_KIND, text_atom(kind))
    entry = alist_put(entry, K_BODY, text_atom(record_text))
    entry = alist_put(entry, K_ENTRY_ID, text_atom(entry_id))
    entry = alist_put(entry, K_SEQUENCE, int_atom(seq))
    j.entries_term = M.Pair(entry, j.entries_term)
    return entry


def observation(j, kind, body_text):
    if not _contains(OBSERVATION_KINDS, kind):
        raise JournalMalformed("unknown observation kind: " + kind)
    rec = ('{"kind":' + _json.dumps(kind) + ',"body":' + _json.dumps(body_text)
           + ',"ts":' + repr(_time.time()) + '}')
    _json.loads(rec)
    return _append(j, "observation", rec)


def proposal(j, kind, body_text):
    if not _contains(PROPOSAL_KINDS, kind):
        raise JournalMalformed("unknown proposal kind: " + kind)
    rec = ('{"kind":' + _json.dumps(kind) + ',"body":' + _json.dumps(body_text)
           + ',"ts":' + repr(_time.time()) + ',"state":"inactive"}')
    _json.loads(rec)
    return _append(j, "proposal", rec)


def close(j):
    if j._closed:
        return
    j._closed = True
    footer = '{"footer":{"closed":true,"seq":' + str(j._seq) + '}}'
    _json.loads(footer)
    j._fh.write(footer.encode("utf-8")); j._fh.write(b"\n"); j._fh.flush()
    j._fh.close(); j._fh = None


def open_journal(path, snapshot_id, task_id, attempt_id, assumptions_term,
                 memory_profile, budget, worker_id):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    fh = open(path, "wb")
    j = WorkerJournal(fh, path, snapshot_id, task_id, attempt_id,
                      assumptions_term, memory_profile, budget, worker_id)
    _write_header(j)
    return j


def _check_binding(header, snapshot_id, task_id, attempt_id, assumptions_term):
    if header.get("snapshot_id") != snapshot_id:
        raise JournalScope("snapshot_id mismatch")
    if header.get("task_id") != task_id:
        raise JournalScope("task_id mismatch")
    if header.get("attempt_id") != attempt_id:
        raise JournalScope("attempt_id mismatch")
    decl_hash = header.get("assumption_hash", "")
    if decl_hash and decl_hash != _assumption_hash(assumptions_term):
        raise JournalScope("assumption hash mismatch")


def load_journal(path, snapshot_id, task_id, attempt_id, assumptions_term=None):
    if not os.path.exists(path):
        raise JournalMalformed("journal missing: " + path)
    with open(path, "rb") as fh:
        raw = fh.read()
    stream = _io.BytesIO(raw)
    header_line = stream.readline()
    if not header_line:
        raise JournalMalformed("empty journal")
    try:
        env = _json.loads(header_line.decode("utf-8"))
    except Exception as exc:
        raise JournalMalformed("bad header: " + str(exc))
    if "header" not in env:
        raise JournalMalformed("first line must be header")
    _check_binding(env["header"], snapshot_id, task_id, attempt_id,
                   assumptions_term if assumptions_term is not None else M.EmptyList)
    entries = M.EmptyList
    obs = 0; prop = 0; last_seq = 0; footer_seen = False; line_no = 1
    while True:
        line = stream.readline()
        if not line:
            break
        line_no += 1
        if not line.strip():
            continue
        try:
            e = _json.loads(line.decode("utf-8"))
        except Exception as exc:
            raise JournalMalformed("bad json line " + str(line_no) + ": " + str(exc))
        if "footer" in e:
            footer_seen = True
            if e["footer"].get("seq") != last_seq:
                raise JournalMalformed("footer seq mismatch")
            continue
        if "kind" not in e or "record" not in e:
            raise JournalMalformed("entry missing fields line " + str(line_no))
        seq = e.get("seq", 0)
        if seq != last_seq + 1:
            raise JournalMalformed("non-monotonic seq line " + str(line_no))
        last_seq = seq
        kind = e["kind"]; rec = e["record"]
        if kind == "observation":
            if not _contains(OBSERVATION_KINDS, rec.get("kind")):
                raise JournalMalformed("unknown observation kind line " + str(line_no))
            obs += 1
        elif kind == "proposal":
            if not _contains(PROPOSAL_KINDS, rec.get("kind")):
                raise JournalMalformed("unknown proposal kind line " + str(line_no))
            if rec.get("state") != "inactive":
                raise JournalMalformed("proposal not inactive line " + str(line_no))
            prop += 1
        else:
            raise JournalMalformed("unknown envelope kind line " + str(line_no))
        entry = M.EmptyList
        entry = alist_put(entry, K_KIND, text_atom(kind))
        entry = alist_put(entry, K_BODY, text_atom(_json.dumps(rec, sort_keys=True, ensure_ascii=False)))
        entry = alist_put(entry, K_ENTRY_ID, text_atom(e.get("entry_id", "")))
        entry = alist_put(entry, K_SEQUENCE, int_atom(seq))
        entries = M.Pair(entry, entries)
    if not footer_seen:
        raise JournalTruncated("no footer; journal did not close cleanly")
    return LoadedJournal(header=env["header"], entries_term=entries,
                         observation_count=obs, proposal_count=prop)
