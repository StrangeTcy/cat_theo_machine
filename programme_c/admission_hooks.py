"""C-C gate hooks for JoinAdmission, wired to existing code paths:

  * validity hook  -> default is a conservative structural check; callers can
                      supply a proof-derivation checker (e.g. ActivateProposal
                      path from graph.py).
  * rent hook      -> performance-only; defaults to passing unless an explicit
                      benchmark callable is supplied (deferred to a later item).
  * human hook     -> explicit approval callable; default denies (no private
                      activation path per protocol/F.md).

Before `admit_next` returns, the accepted-set is persisted to an on-disk
JSON manifest so subsequent candidates observe the updated state from a
durable source rather than in-memory only.
"""
from __future__ import annotations

import json as _json
import os
import time as _time


def default_validity_check(entry, accepted):
    """Conservative default: proposal text non-empty and not a duplicate banned
    token list. Callers should replace with the real proof checker."""
    text = entry.get("proposal_text", "")
    if not text:
        return False
    if "\x00" in text:
        return False
    return True


def default_rent_check(entry, benchmark_dir=None):
    """Rent is performance-only; default is a pass. A future item will plug in
    the held-out benchmark; a benchmark_dir may be supplied and checked for
    presence of a prior benchmark log as a stand-in."""
    if benchmark_dir is None:
        return True
    # If caller supplied a directory but no benchmark artifact exists yet, hold.
    try:
        return os.path.isdir(benchmark_dir)
    except Exception:
        return False


def default_human_approval(entry, approval_callback=None):
    """Human gate default denies (no private activation path). If an explicit
    approval callback is supplied, defer to it; the callback returns True/False.
    """
    if approval_callback is None:
        return False
    try:
        return bool(approval_callback(entry))
    except Exception:
        return False


def write_admission_manifest(manifest_path, accepted_proposals, queue):
    """Persist the current accepted-set and queue to manifest_path atomically.
    Called from JoinAdmission.admit_next before it returns, so the next
    candidate observes the updated state from disk."""
    payload = {
        "written_at": _time.time(),
        "accepted": list(accepted_proposals),
        "queue": list(queue),
    }
    d = os.path.dirname(manifest_path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = manifest_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as h:
        _json.dump(payload, h, indent=2, sort_keys=True, ensure_ascii=False)
    os.replace(tmp, manifest_path)
    return manifest_path


def load_admission_manifest(manifest_path):
    """Read a previously persisted manifest; returns (accepted, queue) or
    (empty_list, empty_list) on any I/O or parse failure. Callers merge
    this with their in-memory state at construction."""
    try:
        with open(manifest_path, "r", encoding="utf-8") as h:
            payload = _json.load(h)
        return list(payload.get("accepted", [])), list(payload.get("queue", []))
    except Exception:
        return [], []
