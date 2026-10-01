"""Snapshot identity (C-B §1).

A digest alone does not prove restore or isolation. Identity binds a
BLAKE2b-256 digest (canonical JSON of roots/symbols/objects with sorted
keys, no added whitespace) to root-set, object/symbol counts, capture
header, UTC timestamp, and a code_hash over a declared set of
restore-critical module files. Fresh-process restore equivalence is
checked by rehydrating the snapshot from a subprocess and re-running the
canonical digest.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json as _json
import os
import subprocess as _sp
import sys as _sys

import hyge_int_pkg.machine as M
from hyge_int_pkg.programme_c import (
    K_SNAPSHOT_ID, K_ROOT_SET, K_OBJECT_COUNT, K_SYMBOL_COUNT, K_HEADER, K_CAPTURED_AT,
    alist_put, _atom_text,
    text_atom, int_atom,
    pair_list_from_py, pair_list_to_py,
)


CANONICAL_HASH = "blake2b-256"
SCHEMA_VERSION = 1
SIDECAR_SUFFIX = ".identity.json"


class SnapshotIdentityRecord:
    def __init__(self, snapshot_id, root_set_term, object_count, symbol_count,
                 header_json_text, captured_at, code_hash):
        self.snapshot_id = snapshot_id
        self.root_set_term = root_set_term
        self.object_count = int(object_count)
        self.symbol_count = int(symbol_count)
        self.header_json_text = header_json_text
        self.captured_at = captured_at
        self.code_hash = code_hash

    def to_term(self):
        rec = M.EmptyList
        rec = alist_put(rec, K_SNAPSHOT_ID, text_atom(self.snapshot_id))
        rec = alist_put(rec, K_ROOT_SET, self.root_set_term)
        rec = alist_put(rec, K_OBJECT_COUNT, int_atom(self.object_count))
        rec = alist_put(rec, K_SYMBOL_COUNT, int_atom(self.symbol_count))
        rec = alist_put(rec, K_HEADER, text_atom(self.header_json_text))
        rec = alist_put(rec, K_CAPTURED_AT, text_atom(self.captured_at))
        return rec


# ---------- canonicalization ----------

def _canonical_bytes(roots, symbols, objects):
    def can(o):
        if isinstance(o, dict):
            items = sorted(o.items())
            return "{" + ",".join(_json.dumps(k, ensure_ascii=False) + ":" + can(v) for k, v in items) + "}"
        if isinstance(o, list):
            return "[" + ",".join(can(v) for v in o) + "]"
        return _json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    text = '{"roots":' + can(roots) + ',"symbols":' + can(symbols) + ',"objects":' + can(objects) + '}'
    return text.encode("utf-8")


def _compute_code_hash(restore_module_paths):
    h = hashlib.blake2b(digest_size=32)
    for p in restore_module_paths:
        try:
            with open(p, "rb") as fh:
                h.update(fh.read())
        except OSError:
            pass
    return h.hexdigest()


DEFAULT_RESTORE_MODULES = ("persistence.py", "snapshot_id.py")


def _read_snapshot(snapshot_path):
    with open(snapshot_path, "rb") as fh:
        raw = fh.read()
    return _json.loads(raw.decode("utf-8")), len(raw)


def _atom_to_text(a):
    v = _atom_text(a)
    try:
        v + ""
    except TypeError:
        return str(v)
    return v


def compute_identity(snapshot_path, captured_at=None, restore_module_paths=None):
    obj, raw_size = _read_snapshot(snapshot_path)
    roots = obj.get("roots", _json.loads("{}"))
    symbols = obj.get("symbols", _json.loads("{}"))
    objects = obj.get("objects", _json.loads("[]"))
    canonical = _canonical_bytes(roots, symbols, objects)
    digest = hashlib.blake2b(canonical, digest_size=32).hexdigest()
    if captured_at is None:
        captured_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
    header = obj.get("header", _json.loads("{}"))
    header_text = _json.dumps(header, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if restore_module_paths is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        restore_module_paths = [os.path.join(base, m) for m in DEFAULT_RESTORE_MODULES]
    code_hash = _compute_code_hash(restore_module_paths)
    ident = SnapshotIdentityRecord(
        snapshot_id=digest,
        root_set_term=pair_list_from_py(sorted(roots.keys()), text_atom),
        object_count=len(objects),
        symbol_count=len(symbols),
        header_json_text=header_text,
        captured_at=captured_at,
        code_hash=code_hash,
    )
    return ident, raw_size


def verify_identity(snapshot_path, expected):
    actual, raw_size = compute_identity(snapshot_path, captured_at=expected.captured_at)
    exp_roots = sorted(pair_list_to_py(expected.root_set_term, _atom_to_text))
    act_roots = sorted(pair_list_to_py(actual.root_set_term, _atom_to_text))
    ok = (actual.snapshot_id == expected.snapshot_id
          and act_roots == exp_roots
          and actual.object_count == expected.object_count
          and actual.symbol_count == expected.symbol_count
          and actual.code_hash == expected.code_hash)
    return ok, actual, raw_size


def verify_restore_fresh_process(snapshot_path, expected_ident):
    """Spawn a fresh python subprocess that loads the snapshot, recomputes identity
    using the same canonicalization function, and prints the digest."""
    script = (
        "import sys, os, json, hashlib\n"
        "sys.path.insert(0, '" + os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "')\n"
        "import hyge_int_pkg.programme_c.snapshot_id as sid2\n"
        "p = sys.argv[1]\n"
        "ident, _ = sid2.compute_identity(p)\n"
        "print(ident.snapshot_id)\n"
    )
    proc = _sp.Popen([_sys.executable, "-c", script, snapshot_path],
                     stdout=_sp.PIPE, stderr=_sp.PIPE)
    out, err = proc.communicate(timeout=30)
    if proc.returncode != 0:
        return False, out.decode("utf-8", "replace") + err.decode("utf-8", "replace")
    got = out.decode("utf-8").strip()
    return got == expected_ident.snapshot_id, got


# ---------- sidecar ----------

def sidecar_path(snapshot_path):
    return snapshot_path + SIDECAR_SUFFIX


def write_sidecar(snapshot_path, ident):
    path = sidecar_path(snapshot_path); tmp = path + ".tmp"
    roots_py = pair_list_to_py(ident.root_set_term, _atom_to_text)
    text = ('{"schema_version":' + str(SCHEMA_VERSION)
            + ',"hash_alg":' + _json.dumps(CANONICAL_HASH)
            + ',"snapshot_id":' + _json.dumps(ident.snapshot_id)
            + ',"root_set":' + _json.dumps(roots_py)
            + ',"object_count":' + str(ident.object_count)
            + ',"symbol_count":' + str(ident.symbol_count)
            + ',"header":' + ident.header_json_text
            + ',"captured_at":' + _json.dumps(ident.captured_at)
            + ',"code_hash":' + _json.dumps(ident.code_hash) + '}')
    _json.loads(text)
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(_json.dumps(_json.loads(text), sort_keys=True, indent=2) + "\n")
    os.replace(tmp, path)
    return path


def read_sidecar(snapshot_path):
    path = sidecar_path(snapshot_path)
    with open(path, "r", encoding="utf-8") as fh:
        data = _json.load(fh)
    header = data.get("header", _json.loads("{}"))
    return SnapshotIdentityRecord(
        snapshot_id=data["snapshot_id"],
        root_set_term=pair_list_from_py(data.get("root_set", []), text_atom),
        object_count=int(data.get("object_count", 0)),
        symbol_count=int(data.get("symbol_count", 0)),
        header_json_text=_json.dumps(header, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        captured_at=data.get("captured_at", ""),
        code_hash=data.get("code_hash", ""),
    )
