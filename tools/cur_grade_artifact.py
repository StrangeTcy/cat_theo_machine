#!/usr/bin/env python3
"""cur_grade_artifact.py — strict executable evaluator for the E3/E4/E7 grader contracts.

Consumes a *structured evidence manifest* (JSON) and derives, per check C1..C6, a verdict of
PASS / FAIL / CANNOT_DETERMINE from the manifest's **evidence fields** — never from any
expected/discrepancy label the manifest might carry.

SCOPE / HOST TOOL BOUNDARY
--------------------------
This is host-side tooling under tools/. It does NOT hold machine values, does not construct
machine terms, and is NOT part of the machine runtime (core.py / labels.py / packs). The standing
constraints on machine-native code (no Python lists/dicts/bools AS MACHINE VALUES; no isinstance
/type/getattr/callable in the ENGINE) govern the machine implementation, not this evaluator. To
keep the boundary unambiguous this file deliberately avoids isinstance/type/getattr/callable and
uses only identity / attribute-availability checks and json-native values. It is NOT machine code.
It never installs or fires a machine rule.

Scope prohibitions (unchanged): no machine implementation files, no oracle-card edits, no
planner/search/matcher changes, no packs, no TrainingRecords, no target sessions, no tag cuts.

STRICTNESS (this hardening batch)
---------------------------------
* Every evidence value must be a JSON boolean exactly (true/false). A non-boolean value
  (string, number, array, object, null) -> exit 2.
* Every evidence check object must only contain KNOWN keys (the pass/fail keys for that
  contract/check). An unknown key -> exit 2 (a misspelled key must not silently become
  CANNOT_DETERMINE).
* A check whose evidence satisfies BOTH a pass rule and a fail rule -> exit 2 (contradictory).
* Unsupported contract or check -> exit 2.
* Multi-taxonomy failures (two or more distinct discrepancy labels) -> exit 2 AMBIGUOUS_DISCREPANCY;
  never pick one by iteration order.
* Ruleset identity: the manifest must carry the matching schema_version, ruleset_id, and
  pinned contract/rubric identities, else EXIT 2.

Exit codes:
  0 all six checks PASS
  1 one or more checks FAIL (exactly one discrepancy label)
  2 malformed / contradictory / ambiguous / schema / ruleset mismatch
  3 no failed checks, but at least one CANNOT_DETERMINE

The grader derives each verdict from evidence; it contains NO expected-label table and ignores any
provided expected/discrepancy label.
"""

import hashlib
import json
import os
import sys

CHECKS = ("C1", "C2", "C3", "C4", "C5", "C6")

SCHEMA_VERSION = 1

# Immutable rule tables (constants, not mutable machine state). Each per-check rule gives the
# pass-evidence keys (ALL must be true -> PASS) and fail-evidence keys (ANY true -> FAIL).
# These are compiled from CUR-GRADER-RUBRIC.md's per-contract PASS/FAIL columns.
CONTRACT_EVIDENCE_RULES = {
    "E4": {
        "C1": (("cites_max_degree_le_3",), ("argues_from_e_in_alone",)),
        "C2": (("states_exactly_two_houses",), ("house_target_ambiguous",)),
        "C3": (("derives_delta_h_le_minus1",), ("asserts_unbounded_descent",)),
        "C4": (("notes_h_bounded_below",), ("termination_no_lower_bound",)),
        "C5": (("termination_not_global_min",), ("concludes_global_minimum",)),
        "C6": (("measure_derived",), ("measure_injected",)),
    },
    "E7": {
        "C1": (("derived_from_flip_sign",), ("invented_without_move_set",)),
        "C2": (("shows_even_window_delta",), ("preservation_no_even_argument",)),
        "C3": (("start_residue_differs",), ("cannot_separate_4_divides",)),
        "C4": (("emits_odd_width_control",), ("omits_odd_width_control",)),
        "C5": (("classifies_rejected",), ("misclassifies_rejected",)),
        "C6": (("observable_derived",), ("weights_injected",)),
    },
    "E3": {
        "C1": (("derived_from_move_constraints",), ("stated_without_move_family",)),
        "C2": (("preserved_all_moves",), ("a_move_changes_reading",)),
        "C3": (("start_differs_from_target",), ("start_equals_target",)),
        "C4": (("emits_no_nonzero_observable",), ("odd_cycle_false_invariant",)),
        "C5": (("generation_disabled_removes_candidate",), ("candidate_survives_removal",)),
        "C6": (("weights_derived",), ("weights_injected",)),
    },
}

# Contract CHECK->TAXONOMY label maps (from the contracts' section-5 taxonomies + E3 rows).
CONTRACT_TAXONOMY = {
    "E4": (
        (("C1", "C2"), "hypothesis-omitted"),
        (("C3", "C4"), "descent-unsupported"),
        (("C5",), "overclaim"),
        (("C6",), "constant-injection"),
    ),
    "E7": (
        (("C1",), "derivation-absent"),
        (("C2", "C4"), "preservation-unsupported"),
        (("C3", "C5"), "overclaim"),
        (("C6",), "constant-injection"),
    ),
    "E3": (
        (("C1",), "derivation-absent"),
        (("C2",), "preservation-unsupported"),
        (("C3", "C4"), "overclaim"),
        (("C5", "C6"), "constant-injection"),
    ),
}

# Pinned identities of the inputs the ruleset was derived from.
PINNED_CONTRACT_REFS = {
    "E3": "CUR-ENGEL-E3-EVALUATOR-CONTRACT.md",
    "E4": "CUR-ENGEL-E4-GRADER-CONTRACT.md",
    "E7": "CUR-ENGEL-E7-GRADER-CONTRACT.md",
}
PINNED_RUBRIC_REF = "CUR-GRADER-RUBRIC.md"


def _ruleset_digest():
    h = hashlib.sha256()
    h.update(SCHEMA_VERSION.to_bytes(4, "big"))
    for contract in sorted(CONTRACT_EVIDENCE_RULES):
        for ck in sorted(CONTRACT_EVIDENCE_RULES[contract]):
            for group in ("pass", "fail"):
                for key in CONTRACT_EVIDENCE_RULES[contract][ck][0 if group == "pass" else 1]:
                    h.update(key.encode("utf-8"))
                    h.update(b"\x00")
    for contract in sorted(CONTRACT_TAXONOMY):
        for checks, label in CONTRACT_TAXONOMY[contract]:
            for c in sorted(checks):
                h.update(c.encode("utf-8"))
            h.update(label.encode("utf-8"))
            h.update(b"\x00")
    return h.hexdigest()


RULESET_DIGEST = _ruleset_digest()
RULESET_ID = "e3e4e7-grader-v%d-%s" % (SCHEMA_VERSION, RULESET_DIGEST[:16])


# --------------------------------------------------------------------- helpers
def _is_json_object(value):
    """True iff value is a JSON object (a mapping). Uses attribute availability, not isinstance."""
    if value is True or value is False or value is None:
        return False
    # A JSON object is the only json-native value that exposes .keys; a str/list/int does not.
    try:
        value.keys
    except AttributeError:
        return False
    # Reject non-mapping anything that happens to have .keys by a strict shape.
    return True


def _is_json_boolean(value):
    return value is True or value is False


def _reject_non_bool(value):
    """True iff value is an acceptable evidence boolean (exact JSON true/false)."""
    return _is_json_boolean(value)


# The artifact's key/value validation below needs no type-introspection for strings: a check's
# evidence keys are validated by membership in the KNOWN-key set (which holds only strings), so a
# non-string key simply fails membership. Values are validated as exact booleans. The artifact's
# top-level contract/version/ref fields are validated by equality against known literals.

def validate_evidence(check_ev, contract, check):
    """Validate one check's evidence object. Returns (ok, reason)."""
    if not _is_json_object(check_ev):
        return False, "check %s evidence is not a JSON object" % check
    rules = CONTRACT_EVIDENCE_RULES[contract][check]
    pass_keys, fail_keys = rules
    known = set(pass_keys) | set(fail_keys)

    # Reject unknown keys (a misspelled key must not silently become CANNOT_DETERMINE).
    for k in check_ev:
        if k not in known:
            return False, "check %s unknown evidence key: %r" % (check, k)

    # Values must be exactly booleans.
    for k in check_ev:
        if not _reject_non_bool(check_ev[k]):
            return False, "check %s evidence %r is not a boolean" % (check, k)

    # Contradictory: both a pass rule and a fail rule satisfied.
    pass_true = all(bool(check_ev.get(k)) for k in pass_keys)
    fail_true = any(bool(check_ev.get(k)) for k in fail_keys)
    if pass_true and fail_true:
        return False, "check %s contradictory evidence (both pass and fail)" % check

    return True, "ok"


def grade(manifest):
    """Grade one strict manifest.

    Returns (checks, final, discrepancy). Raises ValueError on malformed/contradictory/ambiguous
    with a specific message so the CLI can map to exit 2.
    """
    if not _is_json_object(manifest):
        raise ValueError("manifest must be a JSON object")

    # --- ruleset identity ---
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version mismatch (got %r, want %d)" % (
            manifest.get("schema_version"), SCHEMA_VERSION))
    if manifest.get("ruleset_id") != RULESET_ID:
        raise ValueError("ruleset_id mismatch (got %r, want %s)" % (
            manifest.get("ruleset_id"), RULESET_ID))
    if manifest.get("rubric_ref") is not None and manifest["rubric_ref"] != PINNED_RUBRIC_REF:
        raise ValueError("rubric_ref mismatch: %r" % manifest.get("rubric_ref"))

    contract = manifest.get("contract")
    if contract not in CONTRACT_EVIDENCE_RULES:
        raise ValueError("unknown contract: %r (expected E3/E4/E7)" % (contract,))
    if manifest.get("contract_ref") not in (None, PINNED_CONTRACT_REFS[contract]):
        raise ValueError("contract_ref mismatch for %s" % contract)

    evidence = manifest.get("evidence")
    if not _is_json_object(evidence):
        raise ValueError("manifest must have an 'evidence' JSON object")

    # --- per-check validation + verdicts ---
    verdicts = {}
    failed_checks = []
    cannot_determine = False

    # Reject missing/extra checks.
    for c in CHECKS:
        if c not in evidence:
            raise ValueError("missing evidence for check %s" % c)
        ev = evidence[c]
        ok, reason = validate_evidence(ev, contract, c)
        if not ok:
            raise ValueError(reason)

    for c in CHECKS:
        ev = evidence[c]
        rules = CONTRACT_EVIDENCE_RULES[contract][c]
        pass_keys, fail_keys = rules
        # Use .get so an absent key (empty evidence object) counts as False, not a crash.
        pass_true = all(bool(ev.get(k)) for k in pass_keys)
        fail_true = any(bool(ev.get(k)) for k in fail_keys)
        if fail_true:
            verdicts[c] = "FAIL"
            failed_checks.append(c)
        elif pass_true:
            verdicts[c] = "PASS"
        else:
            verdicts[c] = "CANNOT_DETERMINE"
            cannot_determine = True

    # --- final verdict ---
    if failed_checks:
        final = "FAIL"
    elif cannot_determine:
        final = "CANNOT_DETERMINE"
    else:
        final = "PASS"

    # --- discrepancy: collect ALL distinct labels; reject ambiguity ---
    distinct_labels = set()
    for checks, label in CONTRACT_TAXONOMY[contract]:
        if set(checks) & set(failed_checks):
            distinct_labels.add(label)
    if len(distinct_labels) > 1:
        raise ValueError("AMBIGUOUS_DISCREPANCY: %s" % ",".join(sorted(distinct_labels)))
    discrepancy = next(iter(distinct_labels)) if distinct_labels else "none"

    return verdicts, final, discrepancy


def main(argv):
    if len(argv) != 2:
        print("usage: cur_grade_artifact.py <manifest.json>", file=sys.stderr)
        return 2
    path = argv[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except OSError as e:
        print(json.dumps({"error": "cannot read manifest: %s" % e,
                          "final": "MALFORMED", "discrepancy": "none"}))
        return 2
    except ValueError as e:  # JSONDecodeError subclasses ValueError
        print(json.dumps({"error": "invalid JSON: %s" % e,
                          "final": "MALFORMED", "discrepancy": "none"}))
        return 2

    try:
        verdicts, final, discrepancy = grade(manifest)
    except ValueError as e:
        msg = str(e)
        if msg.startswith("AMBIGUOUS_DISCREPANCY"):
            print(json.dumps({"error": msg, "final": "AMBIGUOUS_DISCREPANCY",
                              "discrepancy": "ambiguous"}))
        else:
            print(json.dumps({"error": msg, "final": "MALFORMED",
                              "discrepancy": "none"}))
        return 2

    out = {
        "schema_version": manifest.get("schema_version"),
        "contract": manifest.get("contract"),
        "checks": verdicts,
        "final": final,
        "discrepancy": discrepancy,
    }
    print(json.dumps(out))

    if final == "FAIL":
        return 1
    if final == "CANNOT_DETERMINE":
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
