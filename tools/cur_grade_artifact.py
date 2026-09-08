#!/usr/bin/env python3
"""cur_grade_artifact.py — executable evaluator for the E3/E4/E7 grader contracts.

This tool consumes a *structured evaluator artifact* (JSON) and derives, per check C1..C6, a
verdict of PASS / FAIL / CANNOT_DETERMINE from the artifact's **evidence fields** — never from
any expected/discrepancy label the fixture might carry. It implements the grading logic the
CUR-GRADER-RUBRIC.md defines, applied to the contract's checks.

Scope: this is evaluator-side tooling under tools/. It does NOT touch machine implementation
files, oracle cards, packs, planner/search/matcher, TrainingRecords, or tags.

Exit codes:
  0  all six checks PASS
  1  one or more checks FAIL
  2  malformed or contradictory input (structurally invalid, or a check's evidence is both
     PASS-satisfying and FAIL-triggering)
  3  no failed checks, but at least one CANNOT_DETERMINE

The grader derives each verdict from evidence. A table mapping fixture ids to expected labels
would be a cheat; this tool contains no expected-label table and ignores any provided one.
"""

import json
import sys
import os

CHECKS = ["C1", "C2", "C3", "C4", "C5", "C6"]


# -----------------------------------------------------------------------------
# Contract-specific evidence rules.
#
# For each contract and each check, we define:
#   pass_evidence : list of boolean evidence keys. VERDICT = PASS iff ALL are True
#                   AND no fail_evidence key is True.
#   fail_evidence : list of boolean evidence keys. If ANY is True, the check is FAIL
#                   (present-but-wrong), regardless of pass evidence.
# If neither set is satisfied (some pass evidence missing and no fail trigger present),
# VERDICT = CANNOT_DETERMINE (no evidence either way).
#
# The evidence keys are exactly the fields the rubric names for that contract/check's
# PASS/FAIL columns. This is the "what does the artifact assert/cite" dimension.
# -----------------------------------------------------------------------------

EVIDENCE_RULES = {
    "E4": {
        "C1": {
            "pass": ["cites_max_degree_le_3"],     # rubric: states the max-degree<=3 bound as load-bearing
            "fail": ["argues_from_e_in_alone"],    # rubric FAIL: descent from e_in>=2 alone
        },
        "C2": {
            "pass": ["states_exactly_two_houses"], # rubric: exactly two houses
            "fail": ["house_target_ambiguous"],    # rubric FAIL: houses not bounded / target ambiguous
        },
        "C3": {
            "pass": ["derives_delta_h_le_minus1"], # rubric: shows e_in+e_out<=3 => e_out<=1 => dH<=-1
            "fail": ["asserts_unbounded_descent"], # rubric FAIL: strict descent without e_out<=1 bound
        },
        "C4": {
            "pass": ["notes_h_bounded_below"],     # rubric: H bounded below by 0 + integer
            "fail": ["termination_no_lower_bound"],# rubric FAIL: termination claimed w/o a lower bound
        },
        "C5": {
            "pass": ["termination_not_global_min"],# rubric: says terminates, not a global minimum
            "fail": ["concludes_global_minimum"],  # rubric FAIL: concludes minimality
        },
        "C6": {
            "pass": ["measure_derived"],           # rubric: measure derived, not supplied
            "fail": ["measure_injected"],          # rubric FAIL: measure present as input constant
        },
    },
    "E7": {
        "C1": {
            "pass": ["derived_from_flip_sign"],    # rubric: cites FlipSign + derives from width-4 structure
            "fail": ["invented_without_move_set"], # rubric FAIL: invented without the move set
        },
        "C2": {
            "pass": ["shows_even_window_delta"],   # rubric: dS=-2(p1+p2+p3+p4) with even sum
            "fail": ["preservation_no_even_argument"], # rubric FAIL: claimed without even-window arg
        },
        "C3": {
            "pass": ["start_residue_differs"],     # rubric: start residue 0 differs from target n mod 4
            "fail": ["cannot_separate_4_divides"], # rubric FAIL: cannot separate 4|n from 4!|n
        },
        "C4": {
            "pass": ["emits_odd_width_control"],   # rubric: width-3 control as a negative control
            "fail": ["omits_odd_width_control"],   # rubric FAIL: width-3 omitted / claimed for all widths
        },
        "C5": {
            "pass": ["classifies_rejected"],       # rubric: sum a_i / prod a_i not invariant, Parity non-sep
            "fail": ["misclassifies_rejected"],    # rubric FAIL: rejects invariant or parity claimed to separate
        },
        "C6": {
            "pass": ["observable_derived"],        # rubric: observable derived
            "fail": ["weights_injected"],          # rubric FAIL: E7 weights present as input constant
        },
    },
    "E3": {
        "C1": {
            "pass": ["derived_from_move_constraints"], # rubric: w derived from six move constraints (kernel)
            "fail": ["stated_without_move_family"],    # rubric FAIL: stated without the move family
        },
        "C2": {
            "pass": ["preserved_all_moves"],       # rubric: w_i + w_{i+1} = 0 for all six moves
            "fail": ["a_move_changes_reading"],    # rubric FAIL: any single move changes the reading
        },
        "C3": {
            "pass": ["start_differs_from_target"], # rubric: start reading (2) differs from all-equal (0)
            "fail": ["start_equals_target"],       # rubric FAIL: start and target readings coincide
        },
        "C4": {
            "pass": ["emits_no_nonzero_observable"], # rubric: emits NoNonzeroExactLinearObservable
            "fail": ["odd_cycle_false_invariant"],   # rubric FAIL: nonzero candidate on odd cycle / omits control
        },
        "C5": {
            "pass": ["generation_disabled_removes_candidate"], # rubric: candidate absent when generator off
            "fail": ["candidate_survives_removal"],             # rubric FAIL: candidate survives (constant/second path)
        },
        "C6": {
            "pass": ["weights_derived"],           # rubric: weights derived, not fed
            "fail": ["weights_injected"],          # rubric FAIL: E3 weights present as input/constant
        },
    },
}


def derive_check(contract, check, evidence):
    """Return (verdict, reason) for one check given its evidence dict.

    Precedence:
      1. any fail evidence True  -> FAIL
      2. all pass evidence True  -> PASS
      3. otherwise               -> CANNOT_DETERMINE
    """
    rules = EVIDENCE_RULES[contract][check]
    pass_keys = rules["pass"]
    fail_keys = rules["fail"]
    pass_true = all(bool(evidence.get(k)) for k in pass_keys)
    fail_true = any(bool(evidence.get(k)) for k in fail_keys)

    if fail_true and pass_true:
        return ("CONTRADICTORY", "evidence satisfies both PASS and FAIL")
    if fail_true:
        return ("FAIL", "fail evidence present: " + ",".join(k for k in fail_keys if evidence.get(k)))
    if pass_true:
        return ("PASS", "pass evidence present")
    return ("CANNOT_DETERMINE", "no evidence either way")


def grade(artifact):
    """Grade one structured artifact. Returns (verdicts, final, discrepancy) and sets exit code.

    Raises ValueError for malformed/contradictory input.
    """
    if not isinstance(artifact, dict):
        raise ValueError("artifact must be a JSON object")

    contract = artifact.get("contract")
    if contract not in EVIDENCE_RULES:
        raise ValueError(f"unknown contract: {contract!r} (expected E3/E4/E7)")

    evidence = artifact.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("artifact must have an 'evidence' object")

    # Collect per-check verdicts. A check with a structurally invalid evidence value is malformed.
    verdicts = {}
    discrepancy_checks = []
    cannot_determine = False
    malformed = False

    for c in CHECKS:
        ev = evidence.get(c, {})
        if not isinstance(ev, dict):
            # malformed: check present but not an object
            malformed = True
            verdicts[c] = "CANNOT_DETERMINE"
            continue
        verdict, reason = derive_check(contract, c, ev)
        verdicts[c] = verdict
        if verdict == "CONTRADICTORY":
            malformed = True   # contradictory evidence -> exit 2
        elif verdict == "FAIL":
            discrepancy_checks.append(c)
        elif verdict == "CANNOT_DETERMINE":
            cannot_determine = True

    if malformed:
        # determine if it is purely contradiction (still exit 2) vs structural
        raise ValueError("contradictory or malformed evidence present")

    # Final verdict.
    if discrepancy_checks:
        final = "FAIL"
    elif cannot_determine:
        final = "CANNOT_DETERMINE"
    else:
        final = "PASS"

    # Discrepancy taxonomy label (single best label). Map from the contract's declared taxonomy.
    label = discrepancy_label(contract, discrepancy_checks)
    return verdicts, final, label


# --- Contract CHECK->TAXONOMY label maps (verbatim from the contracts' section 5 taxonomies,
#     plus the E3 rows derived in the battery) ---
TAXONOMY = {
    "E4": {
        ("C1", "C2"): "hypothesis-omitted",
        ("C3", "C4"): "descent-unsupported",
        ("C5",): "overclaim",
        ("C6",): "constant-injection",
    },
    "E7": {
        ("C1",): "derivation-absent",
        ("C2", "C4"): "preservation-unsupported",
        ("C3", "C5"): "overclaim",
        ("C6",): "constant-injection",
    },
    "E3": {
        ("C1",): "derivation-absent",
        ("C2",): "preservation-unsupported",
        ("C3", "C4"): "overclaim",
        ("C5", "C6"): "constant-injection",
    },
}


def discrepancy_label(contract, failed_checks):
    """Return the single taxonomy label implied by the failed check set (or 'none')."""
    best = None
    for checks, label in TAXONOMY[contract].items():
        if set(checks) & set(failed_checks):
            best = label
    # If more than one distinct label is implied, that's ambiguous; report the first
    # but flag it? The selftest asserts single-label, so ambiguous won't arise for good fixtures.
    return best if best else "none"


def main(argv):
    if len(argv) != 2:
        print("usage: cur_grade_artifact.py <artifact.json>", file=sys.stderr)
        return 2
    path = argv[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            artifact = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"error": f"cannot read/parse artifact: {e}"}), file=sys.stderr)
        return 2

    try:
        verdicts, final, label = grade(artifact)
    except ValueError as e:
        print(json.dumps({"error": str(e), "verdicts": "MALFORMED",
                          "final": "MALFORMED", "discrepancy": "none"}))
        return 2

    # Emit the structured result.
    out = {
        "contract": artifact.get("contract"),
        "checks": verdicts,
        "final": final,
        "discrepancy": label,
    }
    print(json.dumps(out))

    # Exit code.
    if final == "FAIL":
        return 1
    if final == "CANNOT_DETERMINE":
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
