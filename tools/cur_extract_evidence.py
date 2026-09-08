#!/usr/bin/env python3
"""cur_extract_evidence.py — frozen G-ENG-style artifact -> structural evidence manifest.

Converts a frozen G-ENG-style evaluator bundle (derivation nodes, citations, ablation/
preservation/separation records, contract-family parameters) into a structured evidence
manifest consumable by tools/cur_grade_artifact.py.

SCOPE / HOST TOOL BOUNDARY
--------------------------
This is host-side tooling under tools/ exactly like the grader. It does NOT construct machine
values or machine terms and is NOT part of the machine runtime (core.py / labels.py / packs).
The engine constraints on machine-native values/types govern machine code, not this evaluator.
This file deliberately avoids isinstance/type/getattr/callable and uses only identity and
attribute-availability checks. It never imports or reads the grader's sealed expected-results
table, nor any expected/discrepancy label a bundle might carry. It derives every evidence bit
from cited source references.

EVIDENCE DISCIPLINE (hard rules)
--------------------------------
1. A true evidence bit is set ONLY when a bundle item (node/record) carries a recognized role
   AND every id it cites resolves to a known claim/node/record. The bit's citations list that
   item id (plus, as a secondary locator, any cited nodes).
2. If a referencing item has a broken/missing ref, or cites nothing, its evidence bit is NOT
   set; a diagnostic is emitted and the extractor reports partial extraction (exit 1).
3. Missing support (a check with no recognized role and no resolved evidence) is NOT an error:
   the bit stays absent and the grader yields CANNOT_DETERMINE.
4. No reading of the grader's sealed expected-results table, no reading of a bundle's
   self-declared verdict.

EXIT CODES
  0  manifest written, no broken/unresolved refs
  1  manifest written, but with unresolved refs / partial extraction
  2  malformed / unsupported / unsupported-contract input (no manifest written)

CONTRACT FAMILY
  The bundle MUST carry an explicit "contract" field in {E3, E4, E7}; otherwise exit 2.
"""

import importlib
import json
import os
import sys

# The grader's constants are the single source of truth for the manifest schema/ruleset and the
# pinned contract/rubric identities, guaranteeing the emitted manifest validates.
_GRADER_MOD = importlib.import_module("cur_grade_artifact")
SCHEMA_VERSION = _GRADER_MOD.SCHEMA_VERSION
RULESET_ID = _GRADER_MOD.RULESET_ID
PINNED_RUBRIC_REF = _GRADER_MOD.PINNED_RUBRIC_REF
PINNED_CONTRACT_REFS = _GRADER_MOD.PINNED_CONTRACT_REFS

BUNDLE_SCHEMA = "geng-bundle/v1"
CHECKS = ("C1", "C2", "C3", "C4", "C5", "C6")

# role -> evidence key (PASS column). A recognized role on a *resolved* item sets that key true.
PASS_ROLE = {
    "E4": {
        "degree-bound": "cites_max_degree_le_3",
        "two-houses": "states_exactly_two_houses",
        "descent-monovariant": "derives_delta_h_le_minus1",
        "bounded-below": "notes_h_bounded_below",
        "not-global-min": "termination_not_global_min",
        "derived-measure": "measure_derived",
    },
    "E7": {
        "flip-sign-derivation": "derived_from_flip_sign",
        "even-window-delta": "shows_even_window_delta",
        "residue-separation": "start_residue_differs",
        "odd-width-control": "emits_odd_width_control",
        "rejected-classification": "classifies_rejected",
        "derived-observable": "observable_derived",
    },
    "E3": {
        "move-constraint-derivation": "derived_from_move_constraints",
        "preserving-reading": "preserved_all_moves",
        "start-target-separation": "start_differs_from_target",
        "no-nonzero-observable": "emits_no_nonzero_observable",
        "removal-removes-candidate": "generation_disabled_removes_candidate",
        "derived-weights": "weights_derived",
    },
}

# role -> evidence key (FAIL column). A recognized role on a *resolved* item sets that key true.
FAIL_ROLE = {
    "E4": {
        "e-in-alone": "argues_from_e_in_alone",
        "ambiguous-house": "house_target_ambiguous",
        "unbounded-descent": "asserts_unbounded_descent",
        "no-lower-bound": "termination_no_lower_bound",
        "global-minimum": "concludes_global_minimum",
        "injected-constant": "measure_injected",
    },
    "E7": {
        "no-move-set": "invented_without_move_set",
        "no-even-argument": "preservation_no_even_argument",
        "cannot-separate": "cannot_separate_4_divides",
        "omits-odd-control": "omits_odd_width_control",
        "misclassifies-rejected": "misclassifies_rejected",
        "injected-weights": "weights_injected",
    },
    "E3": {
        "no-move-family": "stated_without_move_family",
        "move-changes-reading": "a_move_changes_reading",
        "start-equals-target": "start_equals_target",
        "odd-cycle-invariant": "odd_cycle_false_invariant",
        "candidate-survives": "candidate_survives_removal",
        "injected-weights": "weights_injected",
    },
}

# evidence key -> (parameter name, expected value). A bundle parameter equal to the expected value
# satisfies the key, cited as "parameters:<name>". These are the rubric's numeric facts.
PARAM_PASS = {
    "E4": {
        "cites_max_degree_le_3": ("degree_bound", 3),
        "states_exactly_two_houses": ("houses", 2),
    },
    "E7": {
        "shows_even_window_delta": ("window_width", 4),
        "start_residue_differs": ("modulus", 4),
    },
    "E3": {
        "start_differs_from_target": ("start_equals_target", False),
    },
}


def _is_mapping(value):
    """True iff value is a JSON object (mapping). Identity/attribute-availability, no type()."""
    if value is True or value is False or value is None:
        return False
    try:
        value.keys
    except AttributeError:
        return False
    return True


def _is_json_array(value):
    """True iff value is a JSON array. json.load only ever yields a Python list, which exposes
    .append; no other json-native scalar/object does, so attribute availability is sufficient."""
    if value is True or value is False or value is None:
        return False
    if _is_mapping(value):
        return False
    try:
        value.append
    except AttributeError:
        return False
    return True


def _bundle_items(bundle):
    """Return (items, known_ids). Each item is {id, role, cites[], container, ctx}."""
    items = []
    known = set()
    for c in bundle.get("claims", []) or []:
        if _is_mapping(c) and c.get("id"):
            known.add(c["id"])
    cand = bundle.get("candidate")
    if _is_mapping(cand) and cand.get("id"):
        known.add(cand["id"])

    nodes = bundle.get("nodes") or []
    if not _is_json_array(nodes):
        raise ValueError("malformed: 'nodes' must be an array")
    for idx, n in enumerate(nodes):
        if not _is_mapping(n):
            raise ValueError("malformed: node %d is not an object" % idx)
        nid = n.get("id")
        if not nid:
            raise ValueError("malformed: node %d has no id" % idx)
        if nid in known:
            raise ValueError("malformed: duplicate id %r" % (nid,))
        known.add(nid)
        items.append({"id": nid, "role": n.get("role"), "cites": n.get("cites") or n.get("refs") or [],
                      "container": "nodes", "ctx": "node:%s" % (nid,)})

    records = bundle.get("records") or {}
    if not _is_mapping(records):
        raise ValueError("malformed: 'records' must be an object")
    for rname, arr in records.items():
        if not _is_json_array(arr):
            raise ValueError("malformed: records.%s must be an array" % rname)
        for ridx, r in enumerate(arr):
            if not _is_mapping(r):
                raise ValueError("malformed: records.%s[%d] is not an object" % (rname, ridx))
            rid = r.get("id") if r.get("id") else "%s-%d" % (rname, ridx)
            if rid in known:
                raise ValueError("malformed: duplicate id %r" % (rid,))
            known.add(rid)
            items.append({"id": rid, "role": r.get("role"), "cites": r.get("cites") or r.get("refs") or [],
                          "container": rname, "ctx": "record:%s/%s" % (rname, rid)})

    return items, known


def _resolved(item, known):
    """Return (ok, broken_refs). An item is resolved iff it cites >=1 id and all cited ids are known."""
    cites = list(item["cites"])
    if not cites:
        return False, []
    broken = [c for c in cites if c not in known]
    if broken:
        return False, broken
    return True, []


def _key_to_check(contract, key):
    """Map an evidence key to its check (C1..C6) using the grader's canonical rule tables."""
    rules = _GRADER_MOD.CONTRACT_EVIDENCE_RULES[contract]
    for ck in rules:
        pass_keys, fail_keys = rules[ck]
        if key in pass_keys or key in fail_keys:
            return ck
    return None


def extract_bundle(bundle):
    """Full extraction. Returns (evidence, citations, diagnostics, broken_count).

    evidence:      {C1..C6: {only-true-evidence-keys}} (absent keys stay absent -> false).
    citations:     {evidence_key: [ref strings]}.
    diagnostics:   list of strings describing broken/unresolved refs.
    broken_count:  count of referencing items whose refs did not resolve.
    """
    contract = bundle.get("contract")
    if contract not in PASS_ROLE:
        raise ValueError("unsupported contract: %r (expected E3/E4/E7)" % (contract,))

    items, known = _bundle_items(bundle)
    params = bundle.get("parameters") or {}
    if not _is_mapping(params):
        raise ValueError("malformed: 'parameters' must be an object")

    evidence = {c: {} for c in CHECKS}
    citations = {}
    diagnostics = []
    broken_count = 0

    for item in items:
        role = item.get("role")
        if not role:
            continue
        key = None
        if contract in PASS_ROLE and role in PASS_ROLE[contract]:
            key = PASS_ROLE[contract][role]
        elif contract in FAIL_ROLE and role in FAIL_ROLE[contract]:
            key = FAIL_ROLE[contract][role]
        if key is None:
            continue  # unrecognized role: not evidence.

        ok, broken = _resolved(item, known)
        if not ok:
            broken_count += 1
            if broken:
                diagnostics.append("unresolved ref in %s: cites unknown %s" % (item["ctx"], ",".join(broken)))
            else:
                diagnostics.append("unjustified %s: role %s cites nothing" % (item["ctx"], role))
            continue  # do NOT set the bit.

        ck = _key_to_check(contract, key)
        if ck is None:
            raise ValueError("malformed: no check for evidence key %r" % (key,))
        evidence[ck][key] = True
        if key not in citations:
            citations[key] = []
        citations[key].append(item["id"])

    # Parameter facts satisfying PASS keys.
    for key, (pname, expected) in PARAM_PASS.get(contract, {}).items():
        if params.get(pname) == expected:
            ck = _key_to_check(contract, key)
            if ck is not None and not evidence[ck].get(key):
                evidence[ck][key] = True
                if key not in citations:
                    citations[key] = []
                citations[key].append("parameters:%s" % pname)

    return evidence, citations, diagnostics, broken_count


def manifest_from_bundle(bundle):
    """Build the complete evidence manifest dict for a parsed bundle."""
    contract = bundle.get("contract")
    evidence, citations, diagnostics, broken_count = extract_bundle(bundle)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "ruleset_id": RULESET_ID,
        "contract": contract,
        "contract_ref": PINNED_CONTRACT_REFS[contract],
        "rubric_ref": PINNED_RUBRIC_REF,
        "evidence": evidence,
        "extractor": "cur_extract_evidence.py",
        "extractor_schema": BUNDLE_SCHEMA,
        "extractor_diagnostics": diagnostics,
        "citations": citations,
    }
    return manifest, broken_count


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

    # Accept a bundle file path or a directory containing exactly one .json bundle.
    if os.path.isdir(src):
        jsons = sorted(f for f in os.listdir(src) if f.endswith(".json"))
        if len(jsons) != 1:
            print(json.dumps({"error": "directory must contain exactly one bundle json",
                              "final": "MALFORMED"}), file=sys.stderr)
            return 2
        src = os.path.join(src, jsons[0])

    try:
        with open(src, "r", encoding="utf-8") as f:
            bundle = json.load(f)
    except OSError as e:
        print(json.dumps({"error": "cannot read bundle: %s" % e, "final": "MALFORMED"}), file=sys.stderr)
        return 2
    except ValueError as e:
        print(json.dumps({"error": "invalid JSON: %s" % e, "final": "MALFORMED"}), file=sys.stderr)
        return 2

    if not _is_mapping(bundle):
        print(json.dumps({"error": "bundle must be a JSON object", "final": "MALFORMED"}), file=sys.stderr)
        return 2
    if bundle.get("schema") != BUNDLE_SCHEMA:
        print(json.dumps({"error": "unsupported bundle schema: %r" % bundle.get("schema"),
                          "final": "MALFORMED"}), file=sys.stderr)
        return 2

    try:
        manifest, broken_count = manifest_from_bundle(bundle)
    except ValueError as e:
        print(json.dumps({"error": str(e), "final": "MALFORMED"}), file=sys.stderr)
        return 2

    text = json.dumps(manifest)
    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as e:
            print(json.dumps({"error": "cannot write manifest: %s" % e, "final": "MALFORMED"}), file=sys.stderr)
            return 2
    else:
        print(text)

    return 1 if broken_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
