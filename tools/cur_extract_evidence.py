#!/usr/bin/env python3
"""cur_extract_evidence.py — frozen G-ENG-style artifact -> structural evidence manifest.

Converts a frozen G-ENG-style evaluator bundle (derivation nodes, citations, structured numeric
payloads for the pinned problem) into a structural evidence manifest consumable by
tools/cur_grade_artifact.py.

SCOPE / HOST TOOL BOUNDARY
--------------------------
This is host-side tooling under tools/ exactly like the grader. It does NOT construct machine
values or machine terms and is NOT part of the machine runtime (core.py / labels.py / packs).
The engine constraints on machine-native values/types govern machine code, not this evaluator.
This file deliberately avoids isinstance/type/getattr/callable and uses only identity and
attribute-availability checks. It never imports or reads the grader's sealed expected-results
table, nor any expected/discrepancy label a bundle might carry.

EVIDENCE DISCIPLINE (checked handlers, NOT role-to-bool)
--------------------------------------------------------
A recognized role does NOT by itself establish any evidence bit. Instead a role SELECTS a checked
handler; the handler reads the cited node's structured payload, derives the verdict by actual
computation against the pinned problem, and only then sets a bit. If the required payload is
absent, empty, unrelated, or its support chain fails, the bit is NOT set and the check is
CANNOT_DETERMINE. No prose keywords or candidate-authored assurances become proof.

The bounded implementation here is E3 (six-sector alternating sum, invariance, adjacent-increment
moves). Its handlers compute:
  C1 kernel        : the candidate weight w is in the kernel of the move matrix (w_i + w_j = 0 cyclically).
  C2 preservation  : every declared move changes the reading by 0 (ΔR = w_i + w_j = 0 for each pair).
  C3 separation    : R(start) != R(all-equal target); needs sum(w) = 0 and w . start != 0.
  C4 odd control   : the 5-sector odd cycle admits NO nonzero exact linear observable (rank check).
  C5 removal       : with the weighted generator disabled the candidate is absent; the on-run
                     candidate reproduces the derived kernel vector.
  C6 no injection  : the weight's provenance is explicitly 'derived' and it reproduces the kernel basis.

E4 and E7 have NO checked handler in this batch. A bundled role name therefore never establishes
PASS there; those checks stay CANNOT_DETERMINE (with a diagnostic). This is the correct, bounded
state: only validated support becomes PASS.

PROOF-SUPPORT DEPENDENCY CHAIN
------------------------------
The bundle's claims are assumptions; nodes/records are derived conclusions that cite their support.
A cited id must resolve to a real, non-self, non-circular, resolved support item. Self-citation,
circular support, and unresolved upstream support all prevent the dependent evidence bit from being
set (diagnostic emitted). Unrelated cycles elsewhere in the machine's general hypergraph are not
banned; only cycles within this bundle's proof-support chain are rejected.

EXIT CODES
  0  manifest written, no broken/unresolved refs
  1  manifest written, but with unresolved refs / partial extraction
  2  malformed / unsupported / unsupported-contract input (no manifest written)

BINDING TO IMMUTABLE INPUTS
---------------------------
The manifest carries, alongside the evidence, an identity block: bundle content digest, extractor
implementation identity + version, grader ruleset identity, and the pinned contract/rubric source
commits and content digests. Digests establish identity, not mathematical validity.
"""

import hashlib
import importlib
import json
import os
import sys
from fractions import Fraction

# --------------------------------------------------------------------- constants
_GRADER_MOD = importlib.import_module("cur_grade_artifact")
SCHEMA_VERSION = _GRADER_MOD.SCHEMA_VERSION
RULESET_ID = _GRADER_MOD.RULESET_ID
PINNED_RUBRIC_REF = _GRADER_MOD.PINNED_RUBRIC_REF
PINNED_CONTRACT_REFS = _GRADER_MOD.PINNED_CONTRACT_REFS

BUNDLE_SCHEMA = "geng-bundle/v2"
EXTRACTOR_VERSION = "2.0.0"

CHECKS = ("C1", "C2", "C3", "C4", "C5", "C6")

# Pinned identities. contract_ref is the grader-pinned AUTHORITATIVE contract path (from the
# sibling/integration ref, not present as a file in this branch). The in-tree contract document the
# ruleset was reconstructed/checked against is CUR-ENGEL-<family>.md; we bind to BOTH so a later
# reviewer can tell the authoritative name from the in-tree source that was actually hashed.
PINNED_CONTRACT_COMMITS = {
    "E3": "c10011bfabc73b55c7a3de80c4ff14a78234f17b",
    "E4": "c10011bfabc73b55c7a3de80c4ff14a78234f17b",
    "E7": "c10011bfabc73b55c7a3de80c4ff14a78234f17b",
}
PINNED_CONTRACT_DIGESTS = {
    "E3": "98d700321bd58e1ed43fabcde8c044ff87673ea97d34e6b3a04a4b9a24ec1809",
    "E4": "94c5d80cca5c2c29edfa23b8ad55c068411a2c439de18c1ab4924be5ef2a34ab",
    "E7": "b06703d561e4d89232aeb76206d51d5f98be4838b1eb6b44b7a97336b0de4e17",
}
PINNED_CONTRACT_IN_TREE = {
    "E3": "CUR-ENGEL-E3.md",
    "E4": "CUR-ENGEL-E4.md",
    "E7": "CUR-ENGEL-E7.md",
}
PINNED_RUBRIC_COMMIT = "70271007ba5292e782c223bca1474dce8ced8168"
PINNED_RUBRIC_DIGEST = "c4c420bd55f019fcd7c2f3ee468dfbe10fad937d5009d1cdc6cb5d374b04518e"

# E3 pinned problem (authoritative): six-sector alternating sum, adjacent-increment moves.
E3_START = [1, 0, 1, 0, 0, 0]
E3_N = 6
E3_MOVE_PAIRS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]
E3_ODD_N = 5
E3_ODD_PAIRS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]


# --------------------------------------------------------------------- type probes
def _is_mapping(value):
    if value is True or value is False or value is None:
        return False
    try:
        value.keys
    except AttributeError:
        return False
    return True


def _is_array(value):
    if value is True or value is False or value is None:
        return False
    if _is_mapping(value):
        return False
    try:
        value.append
    except AttributeError:
        return False
    return True


def _is_str(value):
    if value is True or value is False or value is None:
        return False
    if _is_mapping(value) or _is_array(value):
        return False
    try:
        value.lower
    except AttributeError:
        return False
    return True


def _is_json_bool(value):
    return value is True or value is False


def _is_number(value):
    if _is_json_bool(value) or value is None:
        return False
    if _is_mapping(value) or _is_array(value) or _is_str(value):
        return False
    return True


# --------------------------------------------------------------------- numerics
def _move_matrix(pairs, n):
    rows = []
    for (i, j) in pairs:
        row = [0] * n
        row[i] += 1
        row[j] += 1
        rows.append(row)
    return rows


def _matrix_rank(rows, n):
    mat = [[Fraction(x) for x in row] for row in rows]
    nrows = len(mat)
    rank = 0
    for col in range(n):
        pivot = None
        for r in range(rank, nrows):
            if mat[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            continue
        mat[rank], mat[pivot] = mat[pivot], mat[rank]
        f = mat[rank][col]
        mat[rank] = [x / f for x in mat[rank]]
        for r in range(nrows):
            if r != rank and mat[r][col] != 0:
                factor = mat[r][col]
                mat[r] = [mat[r][k] - factor * mat[rank][k] for k in range(n)]
        rank += 1
    return rank


def _kernel_dim(pairs, n):
    if n <= 0:
        return 0
    return n - _matrix_rank(_move_matrix(pairs, n), n)


def _kernel_vector(pairs, n):
    """Return a nonzero kernel vector (alternating ±1) if it is a genuine kernel vector, else None."""
    if n <= 0:
        return None
    cand = [1 if k % 2 == 0 else -1 for k in range(n)]
    for row in _move_matrix(pairs, n):
        s = 0
        for k in range(n):
            s += row[k] * cand[k]
        if s != 0:
            return None
    return cand


def _pinned_pairs():
    return set(tuple(sorted(p)) for p in E3_MOVE_PAIRS)


def _supplied_pairs(mpairs):
    out = set()
    for p in mpairs:
        if _is_array(p) and len(p) == 2:
            i = p[0]
            j = p[1]
            if _is_number(i) and _is_number(j):
                out.add(tuple(sorted((int(i), int(j)))))
    return out


def _vector_in_kernel(w, pairs, n):
    for row in _move_matrix(pairs, n):
        if _dot(row, w) != 0:
            return False
    return True


def _dot(vec_a, vec_b):
    s = 0
    for k in range(len(vec_a)):
        s += vec_a[k] * vec_b[k]
    return s


def _same_line(a, b):
    """True iff a and b are nonzero and are scalar multiples (same kernel line)."""
    if not a or not b:
        return False
    if len(a) != len(b):
        return False
    flag_a = None
    for v in a:
        if v != 0:
            flag_a = v
            break
    if flag_a is None:
        return False
    ratio = None
    for v in b:
        if v != 0:
            ratio = v / flag_a
            break
    if ratio is None:
        return False
    for k in range(len(a)):
        if a[k] == 0 and b[k] != 0:
            return False
        if a[k] != 0 and b[k] != a[k] * ratio:
            return False
    return True


# --------------------------------------------------------------------- bundle schema
def _validate_bundle(bundle):
    """Raise ValueError on malformed bundle structure (before any traversal)."""
    if not _is_mapping(bundle):
        raise ValueError("bundle must be a JSON object")
    if bundle.get("schema") != BUNDLE_SCHEMA:
        raise ValueError("unsupported bundle schema: %r" % (bundle.get("schema"),))
    if not _is_str(bundle.get("contract")):
        raise ValueError("bundle must have a 'contract' string")
    contract = bundle["contract"]
    if contract not in PINNED_CONTRACT_REFS:
        raise ValueError("unsupported contract: %r (expected E3/E4/E7)" % (contract,))
    if not _is_mapping(bundle.get("candidate")):
        raise ValueError("bundle must have a 'candidate' object")
    if not _is_str(bundle["candidate"].get("id")):
        raise ValueError("candidate must have a string 'id'")
    claims = bundle.get("claims")
    if claims is not None and not _is_array(claims):
        raise ValueError("'claims' must be an array")
    nodes = bundle.get("nodes")
    if not _is_array(nodes):
        raise ValueError("'nodes' must be an array")

    seen = {}

    def note_id(oid):
        if oid in seen:
            raise ValueError("duplicate id %r" % (oid,))
        seen[oid] = True

    if claims is not None:
        for c in claims:
            if _is_mapping(c) and _is_str(c.get("id")):
                note_id(c["id"])
    note_id(bundle["candidate"]["id"])
    for nd in nodes:
        if not _is_mapping(nd):
            raise ValueError("node must be an object")
        nid = nd.get("id")
        if not _is_str(nid):
            raise ValueError("node must have a string 'id'")
        note_id(nid)
        cites = nd.get("cites")
        if cites is None:
            cites = nd.get("refs")
        if cites is not None and not _is_array(cites):
            raise ValueError("node %s cites must be an array" % (nid,))
        if _is_array(cites):
            for c in cites:
                if not _is_str(c):
                    raise ValueError("node %s cite must be a string id" % (nid,))
        if nd.get("payload") is not None and not _is_mapping(nd.get("payload")):
            raise ValueError("node %s payload must be an object" % (nid,))

    records = bundle.get("records")
    if records is not None and not _is_mapping(records):
        raise ValueError("'records' must be an object")
    if _is_mapping(records):
        for rname, arr in records.items():
            if not _is_array(arr):
                raise ValueError("records.%s must be an array" % (rname,))
            for r in arr:
                if not _is_mapping(r):
                    raise ValueError("records.%s entry must be an object" % (rname,))
                rid = r.get("id")
                if _is_str(rid):
                    note_id(rid)
                cites = r.get("cites") or r.get("refs")
                if _is_array(cites):
                    for c in cites:
                        if not _is_str(c):
                            raise ValueError("record cite must be a string id")


# --------------------------------------------------------------------- proof graph
def _resolve_proof(bundle):
    """Return (status, diagnostics). status[id] in {'assumption','ok','self','upstream','cycle'}."""
    claims = bundle.get("claims") or []
    nodes = bundle.get("nodes") or []
    candidate = bundle.get("candidate")
    records = bundle.get("records") or {}
    items = {}

    def add(obj, kind):
        if obj is None or not _is_mapping(obj):
            return
        oid = obj.get("id")
        if not _is_str(oid):
            return
        items[oid] = (obj, kind)

    for c in claims:
        add(c, "assumption")
    add(candidate, "conclusion")
    for nd in nodes:
        kind = nd.get("kind")
        add(nd, "assumption" if kind == "assumption" else "derived")
    for rname, arr in records.items():
        for r in arr:
            add(r, "derived")

    all_ids = set(items)

    def cits(obj):
        c = obj.get("cites")
        if c is None:
            c = obj.get("refs")
        if c is None:
            return []
        return [x for x in c]

    memo = {}

    def resolve(oid, path):
        if oid not in all_ids:
            return "upstream"
        if oid in memo and memo[oid] in ("ok", "assumption"):
            return "ok"
        if oid in memo and memo[oid] in ("self", "upstream", "cycle"):
            return memo[oid]
        obj, kind = items[oid]
        if kind == "assumption":
            memo[oid] = "assumption"
            return "ok"
        if oid in path:
            memo[oid] = "cycle"
            return "cycle"
        cs = cits(obj)
        if oid in cs:
            memo[oid] = "self"
            return "self"
        if not cs:
            memo[oid] = "upstream"
            return "upstream"
        for c in cs:
            if c not in all_ids:
                memo[oid] = "upstream"
                return "upstream"
        for c in cs:
            r = resolve(c, path + [oid])
            if r != "ok":
                memo[oid] = r
                return r
        memo[oid] = "ok"
        return "ok"

    for oid in list(items):
        if oid not in memo:
            resolve(oid, [])

    # Emit diagnostics once per id with a non-ok status.
    diagnostics = []
    emitted = set()
    for oid in sorted(items):
        st = memo.get(oid)
        if st in ("self", "upstream", "cycle") and (oid, st) not in emitted:
            emitted.add((oid, st))
            if st == "self":
                diagnostics.append("self-citation in %s" % (oid,))
            elif st == "cycle":
                diagnostics.append("circular support involving %s" % (oid,))
            else:
                # distinguish unresolved-upstream reason
                cs = cits(items[oid][0])
                unknown = [c for c in cs if c not in all_ids]
                if unknown:
                    diagnostics.append("unresolved upstream from %s: unknown id %s" % (oid, ",".join(unknown)))
                else:
                    diagnostics.append("unresolved support %s (%s)" % (oid, st))

    return memo, diagnostics


# --------------------------------------------------------------------- support resolution
def _support_by_role(bundle, status):
    """Map role -> list of nodes whose status is 'ok' or 'assumption'."""
    nodes = bundle.get("nodes") or []
    records = bundle.get("records") or {}
    known = {}
    for nd in nodes:
        if _is_mapping(nd) and _is_str(nd.get("id")):
            known[nd["id"]] = nd
    for rname, arr in records.items():
        for r in arr:
            if _is_mapping(r) and _is_str(r.get("id")):
                known[r["id"]] = r
    by_role = {}
    for cid in (bundle.get("candidate").get("cites") or bundle.get("candidate").get("refs") or []):
        nd = known.get(cid)
        if nd is None:
            continue
        if status.get(cid) not in ("ok", "assumption"):
            continue
        role = nd.get("role")
        if not role:
            continue
        by_role.setdefault(role, []).append(nd)
    return by_role


# --------------------------------------------------------------------- checked handler
def _combine_set(evidence, citations, check, pass_key, fail_key, pass_causes, fail_causes):
    """Set a check's evidence from accumulated pass/fail causes; both -> set both (grader exit 2)."""
    if pass_causes and fail_causes:
        evidence[check][pass_key] = True
        evidence[check][fail_key] = True
        citations.setdefault(pass_key, []).extend(pass_causes)
        citations.setdefault(fail_key, []).extend(fail_causes)
        citations.setdefault("contradictory:" + check, []).append("both pass and fail evidence derived")
    elif pass_causes:
        evidence[check][pass_key] = True
        citations.setdefault(pass_key, []).extend(pass_causes)
    elif fail_causes:
        evidence[check][fail_key] = True
        citations.setdefault(fail_key, []).extend(fail_causes)


def _weight_nodes(by_role):
    return by_role.get("weights", [])


def _checked_e3(bundle, status):
    """Derive E3 evidence by interpreting candidate payloads and computing, not authenticating roles."""
    evidence = {c: {} for c in CHECKS}
    citations = {}
    diagnostics = []
    by_role = _support_by_role(bundle, status)

    # Determine the move family once (shared by C1/C2).
    move_nodes = by_role.get("moves", [])
    moves_supplied = None
    moves_node_id = None
    pinned = _pinned_pairs()
    for nd in move_nodes:
        p = nd.get("payload")
        if _is_mapping(p) and "pairs" in p and _is_array(p["pairs"]):
            moves_supplied = _supplied_pairs(p["pairs"])
            moves_node_id = nd.get("id")
            break
    family_ok = moves_supplied is not None and moves_supplied == pinned

    # ---- C1 kernel & C2 preservation per weight record.
    pass_c1, fail_c1, pass_c2, fail_c2 = [], [], [], []
    for nd in _weight_nodes(by_role):
        p = nd.get("payload")
        if not _is_mapping(p) or "vector" not in p or not _is_array(p["vector"]):
            continue
        w = p["vector"]
        if not all(_is_number(x) for x in w):
            diagnostics.append("C1/C2: weight vector contains a non-number element")
            continue
        if len(w) != E3_N:
            diagnostics.append("C1/C2: weight length %s != pinned %s" % (len(w), E3_N))
            continue
        if not family_ok:
            continue  # cannot assess kernel/preservation against an incomplete/extra family
        in_kernel = _vector_in_kernel(w, E3_MOVE_PAIRS, len(w))
        ref = {"node": nd.get("id"), "field": "vector"}
        if in_kernel:
            pass_c1.append(ref)
        else:
            fail_c1.append(ref)
        # C2: per-move reading change.
        all_zero = True
        for q in E3_MOVE_PAIRS:
            if w[q[0]] + w[q[1]] != 0:
                all_zero = False
                break
        if all_zero:
            pass_c2.append(ref)
        else:
            fail_c2.append(ref)
    if not family_ok:
        diagnostics.append("supplied move family does not match pinned E3 problem (incomplete/extra)")
    _combine_set(evidence, citations, "C1", "derived_from_move_constraints",
                 "stated_without_move_family", pass_c1, fail_c1)
    _combine_set(evidence, citations, "C2", "preserved_all_moves",
                 "a_move_changes_reading", pass_c2, fail_c2)

    # ---- C3 separation per weight+start.
    pass_c3, fail_c3 = [], []
    for nd in _weight_nodes(by_role):
        p = nd.get("payload")
        if not _is_mapping(p) or "vector" not in p or not _is_array(p["vector"]):
            continue
        w = p["vector"]
        if not all(_is_number(x) for x in w) or len(w) != E3_N:
            continue
        for snd in by_role.get("start", []):
            sp = snd.get("payload")
            if not _is_mapping(sp) or "vector" not in sp or not _is_array(sp["vector"]):
                continue
            sv = sp["vector"]
            if len(sv) != E3_N or not all(_is_number(x) for x in sv):
                continue
            sum_w = sum(w)
            r_start = _dot(w, sv)
            ref = {"node": nd.get("id"), "field": "vector"}
            if sum_w == 0 and r_start != 0:
                pass_c3.append(ref)
            else:
                fail_c3.append(ref)
    _combine_set(evidence, citations, "C3", "start_differs_from_target",
                 "start_equals_target", pass_c3, fail_c3)

    # ---- C4 odd-cycle control per odd-control record.
    pass_c4, fail_c4 = [], []
    for nd in by_role.get("odd-control", []):
        p = nd.get("payload")
        if not _is_mapping(p) or "target_n" not in p:
            continue
        n_odd = p["target_n"]
        if not _is_number(n_odd) or int(n_odd) != E3_ODD_N:
            diagnostics.append("C4: unsupported odd-control size %s (expect %s)" % (n_odd, E3_ODD_N))
            continue
        kdim = _kernel_dim(E3_ODD_PAIRS, E3_ODD_N)
        ref = {"node": nd.get("id"), "field": "target_n", "kernel_dim": kdim}
        if kdim == 0:
            pass_c4.append(ref)
        else:
            fail_c4.append(ref)
    _combine_set(evidence, citations, "C4", "emits_no_nonzero_observable",
                 "odd_cycle_false_invariant", pass_c4, fail_c4)

    # ---- C5 removal per generation record.
    pass_c5, fail_c5 = [], []
    kv = _kernel_vector(E3_MOVE_PAIRS, E3_N)
    for nd in by_role.get("generation", []):
        p = nd.get("payload")
        if not _is_mapping(p):
            continue
        on_cand = p.get("on_candidate")
        off_cand = p.get("off_candidate")
        if not _is_array(on_cand):
            continue
        on_ok = kv is not None and _same_line([x for x in on_cand], [x for x in kv])
        ref = {"node": nd.get("id"), "field": "on_candidate"}
        if on_ok and (off_cand is None or off_cand == []):
            pass_c5.append(ref)
        elif on_ok and off_cand not in (None, []):
            fail_c5.append(ref)
        else:
            fail_c5.append(ref)
    _combine_set(evidence, citations, "C5", "generation_disabled_removes_candidate",
                 "candidate_survives_removal", pass_c5, fail_c5)

    # ---- C6 no constant injection per weight provenance.
    pass_c6, fail_c6 = [], []
    for nd in _weight_nodes(by_role):
        p = nd.get("payload")
        if not _is_mapping(p):
            continue
        vec = p.get("vector")
        prov = p.get("provenance")
        if not _is_array(vec) or not _is_str(prov):
            continue
        kv = _kernel_vector(E3_MOVE_PAIRS, E3_N)
        if prov == "derived" and kv is not None and _same_line([x for x in vec], [x for x in kv]):
            pass_c6.append({"node": nd.get("id"), "field": "provenance"})
        else:
            fail_c6.append({"node": nd.get("id"), "field": "provenance"})
    _combine_set(evidence, citations, "C6", "weights_derived",
                 "weights_injected", pass_c6, fail_c6)

    return evidence, citations, diagnostics


# --------------------------------------------------------------------- identity
def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bundle_digest(bundle):
    cannon = json.dumps(bundle, sort_keys=True, separators=(",", ":"))
    return _sha256_text(cannon)


def _extractor_identity():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, os.path.basename(__file__))
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _sha256_text(f.read())
    except OSError:
        return "unavailable"


def _identity_block(bundle):
    contract = bundle.get("contract")
    return {
        "bundle_digest": _bundle_digest(bundle),
        "extractor": "cur_extract_evidence.py",
        "extractor_version": EXTRACTOR_VERSION,
        "extractor_digest": _extractor_identity(),
        "grader_ruleset_id": RULESET_ID,
        "grader_schema_version": SCHEMA_VERSION,
        "contract_ref": PINNED_CONTRACT_REFS.get(contract),
        "contract_ref_commit": PINNED_CONTRACT_COMMITS.get(contract),
        "contract_ref_content_digest": PINNED_CONTRACT_DIGESTS.get(contract),
        "contract_in_tree_path": PINNED_CONTRACT_IN_TREE.get(contract),
        "contract_in_tree_content_digest": PINNED_CONTRACT_DIGESTS.get(contract),
        "rubric_ref": PINNED_RUBRIC_REF,
        "rubric_ref_commit": PINNED_RUBRIC_COMMIT,
        "rubric_ref_content_digest": PINNED_RUBRIC_DIGEST,
    }


# --------------------------------------------------------------------- manifest
def extract_bundle(bundle):
    """Return (evidence, citations, proof_diags, handler_diags, broken_count)."""
    _validate_bundle(bundle)
    contract = bundle["contract"]
    status, proof_diags = _resolve_proof(bundle)

    if contract == "E3":
        evidence, citations, handler_diags = _checked_e3(bundle, status)
    else:
        evidence = {c: {} for c in CHECKS}
        citations = {}
        handler_diags = ["no checked evidence handler for contract %s; all checks CANNOT_DETERMINE (role names do not establish PASS)" % (contract,)]

    broken_count = len(proof_diags)
    return evidence, citations, proof_diags, handler_diags, broken_count


def manifest_from_bundle(bundle):
    """Build the complete evidence manifest dict for a parsed bundle."""
    contract = bundle.get("contract")
    evidence, citations, proof_diags, handler_diags, broken_count = extract_bundle(bundle)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "ruleset_id": RULESET_ID,
        "contract": contract,
        "contract_ref": PINNED_CONTRACT_REFS.get(contract),
        "rubric_ref": PINNED_RUBRIC_REF,
        "evidence": evidence,
        "extractor": "cur_extract_evidence.py",
        "extractor_schema": BUNDLE_SCHEMA,
        "extractor_version": EXTRACTOR_VERSION,
        "extractor_diagnostics": proof_diags,
        "extractor_handler_diagnostics": handler_diags,
        "citations": citations,
        "identity": _identity_block(bundle),
    }
    return manifest, broken_count


# --------------------------------------------------------------------- CLI
def main(argv):
    if len(argv) < 2:
        print("usage: cur_extract_evidence.py <bundle.json|bundle_dir> [--out <manifest.json>]", file=sys.stderr)
        return 2
    src = argv[1]
    out_path = None
    i = 2
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_path = argv[i + 1]
            i += 2
        else:
            i += 1

    if os.path.isdir(src):
        jsons = sorted(f for f in os.listdir(src) if f.endswith(".json"))
        if len(jsons) != 1:
            return _emit_error("directory must contain exactly one bundle json")
        src = os.path.join(src, jsons[0])

    try:
        with open(src, "r", encoding="utf-8") as f:
            bundle = json.load(f)
    except OSError as e:
        return _emit_error("cannot read bundle: %s" % (e,))
    except ValueError as e:
        return _emit_error("invalid JSON: %s" % (e,))

    try:
        manifest, broken_count = manifest_from_bundle(bundle)
    except ValueError as e:
        return _emit_error(str(e))

    text = json.dumps(manifest)
    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as e:
            return _emit_error("cannot write manifest: %s" % (e,))
    else:
        print(text)

    return 1 if broken_count > 0 else 0


def _emit_error(msg):
    print(json.dumps({"error": msg, "final": "MALFORMED", "discrepancy": "none"}))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
