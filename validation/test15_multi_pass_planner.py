#!/usr/bin/env python3
"""
Validation Test Suite 15: Dimension 2/3 / W13 — Multi-Pass Backward Planning & Goal Decomposition.
Tests goal conjunction decomposition, auxiliary witness synthesis, sub-derivation splicing,
and end-to-end multi-pass planned query execution.
"""
from __future__ import annotations

import os
import sys
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import checker_b as CB
from cat_theo_machine import graph_task as GT
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine import story_renderer as SR
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 15: W13 Multi-Pass Backward Planning & Goal Decomposition ===")

print("\n[1] Initializing hypergraph runtime and registry...")
runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
print("    Runtime and registry initialized.")

print("\n[2] Test Case 1: Universal Goal Conjunction Decomposition...")
node_a = M.Atom()
node_b = M.Atom()
node_c = M.Atom()
node_x = M.Atom()

# Goal: (Triangle A B C) /\ (IsReal X)
q1 = M.Pair(L.TriangleLabel, M.Pair(node_a, M.Pair(node_b, M.Pair(node_c, M.EmptyList))))
q2 = M.Pair(L.IsRealLabel, M.Pair(node_x, M.EmptyList))
compound_query = M.Pair(L.TaskQueryLabel, M.Pair(q1, M.Pair(q2, M.EmptyList)))

decomp = GT.DecomposeGoalConjunction(compound_query, registry)()
decomp_tag = M.Head(decomp)()
assert (
    M.IdentityCompare(decomp_tag, L.GoalDecompositionLabel)() is M.truth_value
), "Test 1 Failed: Goal decomposition label mismatch!"
sub_goals = M.Head(M.Tail(decomp)())()
print(f"    Goal Decomposition Tag: {decomp_tag} (Passed)")

print("\n[3] Test Case 2: Auxiliary Existential Witness Synthesis...")
open_pattern = L.AngleLabel
facts = M.Pair(q1, M.EmptyList)
aux_res = GT.SynthesizeAuxiliaryWitness(open_pattern, facts, registry)()
aux_tag = M.Head(aux_res)()
assert (
    M.IdentityCompare(aux_tag, L.AuxiliaryWitnessLabel)() is M.truth_value
), "Test 2 Failed: Auxiliary witness synthesis label mismatch!"
witness_atom = M.Head(M.Tail(aux_res)())()
updated_facts = M.Head(M.Tail(M.Tail(aux_res)())())()
print(f"    Auxiliary Witness Tag: {aux_tag}, Witness: {witness_atom} (Passed)")

print("\n[4] Test Case 3: Proof Derivation Splicing (D1 + D2 -> D_unified)...")
# Build Derivation 1: A -> B
r1 = P.Rule(M.Char("A"), M.Char("B"))()
r2 = P.Rule(M.Char("B"), M.Char("C"))()

step1_res = P.Step(
    M.Char("A"),
    P.RewriteAction(r1, M.EmptyList)(),
    M.Char("B"),
    registry,
)()
s1 = M.Head(step1_res)()
reg1 = M.Head(M.Tail(step1_res)())()
cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
d1_res = P.Derivation(M.Pair(s1, M.EmptyList), cost_zero, reg1)()
d1 = M.Head(d1_res)()
reg2 = M.Head(M.Tail(d1_res)())()

# Build Derivation 2: B -> C
step2_res = P.Step(
    M.Char("B"),
    P.RewriteAction(r2, M.EmptyList)(),
    M.Char("C"),
    reg2,
)()
s2 = M.Head(step2_res)()
reg3 = M.Head(M.Tail(step2_res)())()
d2_res = P.Derivation(M.Pair(s2, M.EmptyList), cost_zero, reg3)()
d2 = M.Head(d2_res)()
reg4 = M.Head(M.Tail(d2_res)())()

# Splice D1 and D2
spliced_d = GT.SpliceProofDerivations(M.Pair(d1, M.Pair(d2, M.EmptyList)), reg4)()
spliced_steps = P.DerivationSteps(spliced_d, reg4)()

# Verify spliced derivation with Checker B
trusted_rules = M.Pair(r1, M.Pair(r2, M.EmptyList))
check_res = CB.VerifyDerivation(
    spliced_d, M.Char("A"), M.Char("C"), trusted_rules, reg4
)()
check_tag = M.Head(check_res)()
assert (
    M.IdentityCompare(check_tag, L.DerivationVerifiedLabel)() is M.truth_value
), "Test 3 Failed: Spliced derivation verification failed in Checker B!"
print(f"    Spliced Derivation Checker B Verdict: {check_tag} (Verified)")

print("\n[5] Test Case 4: Multi-Pass Planned Query Execution...")
# Case 4a: Positive planned execution with multi-hop derivation
var_a = M.Var()
var_b = M.Var()
var_c = M.Var()

pat_a = M.Pair(M.VarTag, M.Pair(var_a, M.EmptyList))
pat_b = M.Pair(M.VarTag, M.Pair(var_b, M.EmptyList))
pat_c = M.Pair(M.VarTag, M.Pair(var_c, M.EmptyList))

rule_triangle = P.MultiRule(
    M.Pair(
        M.Pair(L.SegmentLabel, M.Pair(pat_a, M.Pair(pat_b, M.EmptyList))),
        M.Pair(
            M.Pair(L.SegmentLabel, M.Pair(pat_b, M.Pair(pat_c, M.EmptyList))),
            M.EmptyList,
        ),
    ),
    M.Pair(L.TriangleLabel, M.Pair(pat_a, M.Pair(pat_b, M.Pair(pat_c, M.EmptyList)))),
)()

task_pos = GT.GraphTaskRecord(
    M.Char("multi_pass_task_pos"),
    L.Rung7PlannerLabel,
    M.Pair(
        M.Pair(L.SegmentLabel, M.Pair(node_a, M.Pair(node_b, M.EmptyList))),
        M.Pair(
            M.Pair(L.SegmentLabel, M.Pair(node_b, M.Pair(node_c, M.EmptyList))),
            M.EmptyList,
        ),
    ),
    q1,
    M.EmptyList,
    M.Pair(rule_triangle, M.EmptyList),
    M.Char("provenance_w13_pos"),
)()

plan_pos_res = GT.ExecuteMultiPassPlannedQuery(task_pos, reg4)()
plan_pos_tag = M.Head(plan_pos_res)()
assert (
    M.IdentityCompare(plan_pos_tag, L.MultiPassPlanSuccessLabel)() is M.truth_value
), "Test 4 Failed: Positive multi-pass planning should return MultiPassPlanSuccessLabel!"
print(f"    Positive Multi-Pass Planning Tag: {plan_pos_tag} (Passed)")

# Case 4b: Negative planned execution with unsatisfied sub-goal
task_neg = GT.GraphTaskRecord(
    M.Char("multi_pass_task_neg"),
    L.Rung7PlannerLabel,
    M.Pair(
        M.Pair(L.SegmentLabel, M.Pair(node_a, M.Pair(node_b, M.EmptyList))),
        M.Pair(
            M.Pair(L.SegmentLabel, M.Pair(node_b, M.Pair(node_c, M.EmptyList))),
            M.EmptyList,
        ),
    ),
    compound_query,
    M.EmptyList,
    M.EmptyList,
    M.Char("provenance_w13_neg"),
)()

plan_neg_res = GT.ExecuteMultiPassPlannedQuery(task_neg, reg4)()
plan_neg_tag = M.Head(plan_neg_res)()
assert (
    M.IdentityCompare(plan_neg_tag, L.MultiPassPlanFailureLabel)() is M.truth_value
), "Test 4 Failed: Negative multi-pass planning should return MultiPassPlanFailureLabel!"
print(f"    Negative Multi-Pass Planning Tag: {plan_neg_tag} (Passed)")

print("\n[6] Test Case 5: Story Rendering of Spliced Multi-Pass Derivation...")
receipt = M.Pair(
    L.ProofReceiptLabel,
    M.Pair(
        M.Char("multi_pass_spliced_session"),
        M.Pair(
            M.Char("A"),
            M.Pair(
                M.Char("C"),
                M.Pair(spliced_d, reg4),
            ),
        ),
    ),
)
story = SR.RenderProofStory(receipt, reg4)()
story_tag = M.Head(story)()
assert (
    M.IdentityCompare(story_tag, L.ProofStoryLabel)() is M.truth_value
), "Test 5 Failed: RenderProofStory result is not a ProofStoryLabel!"

md_story = SR.FormatStoryToMarkdown(story)
print(f"\n--- SPLICED MULTI-PASS PROOF NARRATIVE ---\n{md_story}\n--- END NARRATIVE ---")

assert "Proof Narrative: Session `multi_pass_spliced_session`" in md_story
assert "A -> B" in md_story
assert "B -> C" in md_story
assert "Conclusion (Q.E.D.)" in md_story
print("\n    Markdown Narrative Content Verified.")

print()
print(
    f"=== ALL TEST 15 MULTI-PASS BACKWARD PLANNING CHECKS PASSED in {time.time() - t0:.3f}s ==="
)
