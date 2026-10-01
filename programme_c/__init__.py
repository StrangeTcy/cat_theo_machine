"""Programme C orchestration boundary (C-B: snapshot + journal).

Plain-Python containers appear only at the JSON/process I/O boundary and are
never injected into machine terms. Values entering the machine are Pair
chains / string-bearing atoms via text_atom/gmp_atom/int_atom.
"""
from __future__ import annotations

import hyge_int_pkg.machine as M
import hyge_int_pkg.gmprep as GMP


def text_atom(text):
    a = M.Atom(); a.value = text; return a


def gmp_atom(text):
    a = M.Atom(); a.value = GMP.GMPRep(text); return a


def int_atom(value):
    return gmp_atom(str(int(value)))


def alist_put(alist, key_atom, value):
    return M.Pair(key_atom, M.Pair(value, alist))


def alist_get(alist, key_atom):
    """Fetch by string value of the key atom. Works across subprocess boundaries
    where atom identity (id()) is not preserved after spawn pickling."""
    target = key_atom.value
    cur = alist
    while M.IsPair(cur)() is M.truth_value:
        k = M.Head(cur)()
        rest = M.Tail(cur)()
        v = M.Head(rest)()
        if _atom_text(k) == target:
            return v
        cur = M.Tail(rest)()
    return M.EmptyList


def _atom_text(atom):
    """Return host string for an atom's value. Try/except only (no callable/type)."""
    if atom is None:
        return ""
    try:
        v = atom.value
    except Exception:
        return str(atom)
    try:
        r = v()
        return r
    except TypeError:
        return v
    except Exception:
        try:
            return str(v)
        except Exception:
            return ""


def pair_list_from_py(py_seq, to_term):
    out = M.EmptyList
    i = len(py_seq) - 1
    while i >= 0:
        out = M.Pair(to_term(py_seq[i]), out)
        i -= 1
    return out


def pair_list_to_py(term, from_term):
    out = []
    cur = term
    while M.IsPair(cur)() is M.truth_value:
        out.append(from_term(M.Head(cur)()))
        cur = M.Tail(cur)()
    return out


# Canonical keys (shared across A/B/C).
K_SNAPSHOT_ID = text_atom("snapshot_id")
K_ROOT_SET = text_atom("root_set")
K_OBJECT_COUNT = text_atom("object_count")
K_SYMBOL_COUNT = text_atom("symbol_count")
K_HEADER = text_atom("header")
K_CAPTURED_AT = text_atom("captured_at")
K_TASK_ID = text_atom("task_id")
K_ATTEMPT_ID = text_atom("attempt_id")
K_WORKER_ID = text_atom("worker_id")
K_ASSUMPTIONS = text_atom("assumptions")
K_ASSUMPTION_HASH = text_atom("assumption_hash")
K_MEMORY_PROFILE = text_atom("memory_profile")
K_BUDGET = text_atom("budget")
K_STATUS = text_atom("status")
K_KIND = text_atom("kind")
K_BODY = text_atom("body")
K_SEQUENCE = text_atom("sequence")
K_ENTRY_ID = text_atom("entry_id")
K_PARENT_ATTEMPT = text_atom("parent_attempt")
K_OBLIGATION = text_atom("obligation")
K_REASON = text_atom("reason")
K_CHILD_ID = text_atom("child_id")
K_CHILD_STATUS = text_atom("child_status")
K_DECLARED_SNAPSHOT = text_atom("declared_snapshot_id")
K_DECLARED_OBLIGATION = text_atom("declared_obligation")

# Status atoms.
S_RUNNING = text_atom("running")
S_COMPLETED = text_atom("completed")
S_FAILED = text_atom("failed")
S_CANCELLED = text_atom("cancelled")
S_READY = text_atom("ready")
S_DISPATCHED = text_atom("dispatched")

# Failure reason atoms.
F_LAUNCH_ERROR = text_atom("launch-error")
F_TIMEOUT = text_atom("timeout")
F_CRASH = text_atom("crash")
F_CANCELLED = text_atom("cancelled")
F_SNAPSHOT_MISMATCH = text_atom("snapshot-mismatch")
F_MALFORMED_JOURNAL = text_atom("malformed-journal")
F_MISATTRIBUTED_JOURNAL = text_atom("misattributed-journal")
F_TRUNCATED_JOURNAL = text_atom("truncated-journal")
F_SCOPE_VIOLATION = text_atom("scope-violation")
F_STALE_RESULT = text_atom("stale-result")
F_INCOMPATIBLE_ASSUMPTIONS = text_atom("incompatible-assumptions")
F_MISSING_CHILD = text_atom("missing-child")
F_INVALID_CERT = text_atom("invalid-certificate")
F_UNKNOWN_CHILD = text_atom("unknown-child")
F_REFRUTATION = text_atom("refutation")  # logical, distinct from execution failure
F_RENT_FAIL = text_atom("rent-fail")  # performance-only; reject + pop
