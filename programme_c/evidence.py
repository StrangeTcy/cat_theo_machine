"""Inert evidence archive (C-B §4). Validates and deduplicates observations;
never feeds search or learning; duplicate import idempotent; proposals stay
inactive.
"""
from __future__ import annotations

import hashlib
import json as _json
import os

import hyge_cc.machine as M
from hyge_cc.programme_c import K_KIND, K_BODY, K_ENTRY_ID, alist_get


ARCHIVE_VERSION = 1


def _content_hash(record_text):
    return hashlib.blake2b(record_text.encode("utf-8"), digest_size=32).hexdigest()


def _safe_name(entry_id):
    out = ""
    i = 0
    while i < len(entry_id):
        ch = entry_id[i]
        out = out + ("_" if ch in "/:\\" else ch)
        i += 1
    return out


class EvidenceArchive:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.obs_dir = os.path.join(root_dir, "obs")
        self.pro_dir = os.path.join(root_dir, "pro")
        self.manifest_path = os.path.join(root_dir, "manifest.json")


def _atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def _read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return _json.load(fh)


def _write_entry(sub_dir, entry_id, record_text, header):
    safe = _safe_name(entry_id) + ".json"
    path = os.path.join(sub_dir, safe)
    payload = ('{"provenance":{"entry_id":' + _json.dumps(entry_id)
               + ',"header":' + _json.dumps(header, sort_keys=True, ensure_ascii=False)
               + '},"record":' + record_text + '}')
    _json.loads(payload)
    _atomic_write(path, _json.dumps(_json.loads(payload), sort_keys=True, indent=2) + "\n")
    return path


def init_archive(root_dir):
    ar = EvidenceArchive(root_dir)
    os.makedirs(ar.obs_dir, exist_ok=True)
    os.makedirs(ar.pro_dir, exist_ok=True)
    if not os.path.exists(ar.manifest_path):
        _atomic_write(ar.manifest_path,
                      _json.dumps(_json.loads('{"v":1,"obs":[],"pro":[],"index":{}}'),
                                  sort_keys=True, indent=2) + "\n")
    return ar


def _reverse(term):
    out = M.EmptyList
    cur = term
    while M.IsPair(cur)() is M.truth_value:
        out = M.Pair(M.Head(cur)(), out)
        cur = M.Tail(cur)()
    return out


def _entry_field(entry, key):
    return alist_get(entry, key).value


def import_journal(ar, loaded):
    m = _read_json(ar.manifest_path)
    index = m.get("index", _json.loads("{}"))
    obs_list = m.get("obs", _json.loads("[]"))
    pro_list = m.get("pro", _json.loads("[]"))
    new_obs = 0; new_pro = 0; dup_obs = 0; dup_pro = 0
    cur = _reverse(loaded.entries_term)
    while M.IsPair(cur)() is M.truth_value:
        entry = M.Head(cur)(); cur = M.Tail(cur)()
        eid = _entry_field(entry, K_ENTRY_ID); kind = _entry_field(entry, K_KIND)
        body = _entry_field(entry, K_BODY)
        rec = _json.loads(body)
        rec_text = _json.dumps(rec, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        ch = _content_hash(rec_text)
        existing = index.get(eid)
        if existing is not None:
            if existing.get("content_hash") == ch:
                if kind == "observation": dup_obs += 1
                else: dup_pro += 1
                continue
            raise RuntimeError("entry_id collision with differing content: " + eid)
        if kind == "observation":
            _write_entry(ar.obs_dir, eid, rec_text, loaded.header)
            obs_list.append(eid); new_obs += 1
        elif kind == "proposal":
            if rec.get("state") != "inactive":
                raise RuntimeError("refusing non-inactive proposal: " + eid)
            _write_entry(ar.pro_dir, eid, rec_text, loaded.header)
            pro_list.append(eid); new_pro += 1
        index[eid] = {"content_hash": ch, "kind": kind}
    m["index"] = index; m["obs"] = obs_list; m["pro"] = pro_list
    _atomic_write(ar.manifest_path, _json.dumps(m, sort_keys=True, indent=2) + "\n")
    return new_obs, new_pro, dup_obs, dup_pro


def archive_counts(ar):
    m = _read_json(ar.manifest_path)
    return len(m.get("obs", _json.loads("[]"))), len(m.get("pro", _json.loads("[]")))
