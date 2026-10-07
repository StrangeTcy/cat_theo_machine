#!/usr/bin/env python3
"""
Validation Test Suite 14: W14 — Proof Storyteller & Derivation Narrative Generator.
Tests formal hypergraph proof receipts rendering into structured mathematical
proof stories with domain rationales across the 5 Dimensions.
"""
from __future__ import annotations

import sys
import os
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine import checker_b as CB
from cat_theo_machine import story_renderer as SR
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 14: W14 Proof Storyteller & Derivation Narrative Generator ===")

print("\n[1] Initializing hypergraph runtime and registry...")
runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
print("    Runtime and registry initialized.")

# Helper to create a derivation step
def make_step(action_name, premise_terms, conclusion_term):
    rule = P.Rule(premise_terms, conclusion_term)()
    action = P.RewriteAction(rule, M.EmptyList)()
    step_res = P.Step(premise_terms, action, conclusion_term, registry)()
    return M.Head(step_res)()

print("\n[2] Test Case 1: Narrative Step Construction & Rationale Classification...")
s_alg = make_step("AlgebraicDistribute", M.Char("Algebraic A"), M.Char("Algebraic B"))
r_alg = SR.ClassifyInferenceRationale(s_alg, registry)()
assert (
    M.IdentityCompare(r_alg, L.RationaleAlgebraicLabel)() is M.truth_value
), "Test 1 Failed: Algebraic rationale classification mismatch!"
print(f"    Algebraic Step Rationale: {r_alg} (Passed)")

s_obs = make_step("Modulo4ParityObstruction", M.Char("mod 4 x^2+y^2 parity"), M.Char("obstruction disjoint"))
r_obs = SR.ClassifyInferenceRationale(s_obs, registry)()
assert (
    M.IdentityCompare(r_obs, L.RationaleParityObstructionLabel)() is M.truth_value
), "Test 1 Failed: Parity Obstruction rationale classification mismatch!"
print(f"    Parity Obstruction Step Rationale: {r_obs} (Passed)")

s_geom = make_step("AuxiliaryCircumcircleConstruction", M.Char("Triangle auxiliary point"), M.Char("CyclicQuad geom circle"))
r_geom = SR.ClassifyInferenceRationale(s_geom, registry)()
assert (
    M.IdentityCompare(r_geom, L.RationaleAuxiliaryConstructionLabel)() is M.truth_value
), "Test 1 Failed: Auxiliary Construction rationale classification mismatch!"
print(f"    Auxiliary Geometry Step Rationale: {r_geom} (Passed)")

s_mono = make_step("EngelMonovariantStep", M.Char("monovariant semi-invariant Phi(S_k)"), M.Char("decrease Phi(S_k+1)"))
r_mono = SR.ClassifyInferenceRationale(s_mono, registry)()
assert (
    M.IdentityCompare(r_mono, L.RationaleMonovariantLabel)() is M.truth_value
), "Test 1 Failed: Monovariant rationale classification mismatch!"
print(f"    Monovariant Step Rationale: {r_mono} (Passed)")

s_desc = make_step("FermatInfiniteDescentStep", M.Char("infinite descent z_k"), M.Char("well_founded smaller z_k+1"))
r_desc = SR.ClassifyInferenceRationale(s_desc, registry)()
assert (
    M.IdentityCompare(r_desc, L.RationaleDescentLabel)() is M.truth_value
), "Test 1 Failed: Infinite Descent rationale classification mismatch!"
print(f"    Infinite Descent Step Rationale: {r_desc} (Passed)")

print("\n[3] Test Case 2: Multi-Step Derivation & Checker B Verification...")
step1 = make_step("Modulo4ParityObstruction", M.Char("mod 4 A"), M.Char("parity B"))
step2 = make_step("FermatInfiniteDescentStep", M.Char("parity B"), M.Char("descent C"))

rule1_named = P.ActionRule(P.StepAction(step1, registry)())()
rule2_named = P.ActionRule(P.StepAction(step2, registry)())()

steps_chain = M.Pair(step1, M.Pair(step2, M.EmptyList))
cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
der_res = P.Derivation(steps_chain, cost_zero, registry)()
derivation = M.Head(der_res)()

# Verify with Independent Checker B
trusted_rules = M.Pair(rule1_named, M.Pair(rule2_named, M.EmptyList))
check_verdict = CB.VerifyDerivation(
    derivation, M.Char("mod 4 A"), M.Char("descent C"), trusted_rules, registry
)()
check_tag = M.Head(check_verdict)()
assert (
    M.IdentityCompare(check_tag, L.DerivationVerifiedLabel)() is M.truth_value
), "Test 2 Failed: Derivation verification failed in Checker B!"
print(f"    Independent Checker B Verdict Tag: {check_tag} (Verified)")

print("\n[4] Test Case 3: Proof Receipt to Proof Story Rendering...")
receipt = M.Pair(
    L.ProofReceiptLabel,
    M.Pair(
        M.Char("flt_session_001"),
        M.Pair(
            M.Char("mod 4 A"),
            M.Pair(
                M.Char("descent C"),
                M.Pair(derivation, registry),
            ),
        ),
    ),
)

story = SR.RenderProofStory(receipt, registry)()
story_tag = M.Head(story)()
assert (
    M.IdentityCompare(story_tag, L.ProofStoryLabel)() is M.truth_value
), "Test 3 Failed: RenderProofStory result is not a ProofStoryLabel!"
print(f"    Proof Story Container Tag: {story_tag} (Passed)")

print("\n[5] Test Case 4: Formatting Proof Story to Natural Mathematical Markdown...")
md_output = SR.FormatStoryToMarkdown(story)
print(f"\n--- GENERATED PROOF STORY ---\n{md_output}\n--- END PROOF STORY ---")

assert "Proof Narrative: Session `flt_session_001`" in md_output
assert "mod 4 A -> parity B" in md_output
assert "parity B -> descent C" in md_output
assert "Conclusion (Q.E.D.)" in md_output
print("\n    Markdown Narrative Content Verified.")

print()
print(
    f"=== ALL TEST 14 PROOF STORYTELLER & NARRATIVE CHECKS PASSED in {time.time() - t0:.3f}s ==="
)
