# ============================================================
# TEST 6: ODR CL7 Adversarial Red-Team Verification Suite
# ============================================================
import os
import sys
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import checker_b as CheckerB
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 6: ODR CL7 Adversarial Red-Team Verification Suite ===")
print()

print("[1] Initializing runtime, hypergraph, and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()

# Record initial baseline state to verify non-leakage
initial_all_rules = graph.all_rules
initial_derivations = graph.derivations
initial_registry = registry
print("    Runtime initialized. Baseline recorded.")
print()

# Build baseline terms: A, B, C, D, E
atom_a = M.Atom()
atom_b = M.Atom()
atom_c = M.Atom()
atom_d = M.Atom()
atom_e = M.Atom()

term_a = M.Pair(atom_a, M.EmptyList)
term_b = M.Pair(atom_b, M.EmptyList)
term_c = M.Pair(atom_c, M.EmptyList)
term_d = M.Pair(atom_d, M.EmptyList)
term_e = M.Pair(atom_e, M.EmptyList)

# Build trusted rules:
# Rule 1: term_a -> term_b
# Rule 2: term_b -> term_c
rule_1 = P.Rule(term_a, term_b)()
rule_2 = P.Rule(term_b, term_c)()
trusted_rules = M.Pair(rule_1, M.Pair(rule_2, M.EmptyList))

# Valid Steps:
action_1 = P.RewriteAction(rule_1, M.EmptyList)()
step_1_res = P.Step(term_a, action_1, term_b, registry)()
step_1 = M.Head(step_1_res)()
registry = M.Head(M.Tail(step_1_res)())()

action_2 = P.RewriteAction(rule_2, M.EmptyList)()
step_2_res = P.Step(term_b, action_2, term_c, registry)()
step_2 = M.Head(step_2_res)()
registry = M.Head(M.Tail(step_2_res)())()

cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()

print(
    "[2] Attack Vector 1: Step Permutation / Discontinuity Attack [Step 2, Step 1]..."
)
# Swapping step 2 and step 1 creates a chain discontinuity (step 2 tries to start at B while chain is at A)
permuted_steps = M.Pair(step_2, M.Pair(step_1, M.EmptyList))
permuted_der_res = P.Derivation(permuted_steps, cost_zero, registry)()
permuted_derivation = M.Head(permuted_der_res)()
registry = M.Head(M.Tail(permuted_der_res)())()

res1 = CheckerB.VerifyDerivation(
    permuted_derivation, term_a, term_c, trusted_rules, registry
)()
tag1 = M.Head(res1)()
is_discontinuity_caught = (
    M.IdentityCompare(tag1, L.StepDiscontinuityLabel)() is M.truth_value
)
print(f"    Verdict: {tag1} (Rejected: {is_discontinuity_caught})")
assert (
    is_discontinuity_caught
), f"Attack 1 Failed: Permuted steps not caught by StepDiscontinuityLabel: {tag1}"

print(
    "[3] Attack Vector 2: Forward Reference / Unproved Start State Attack (E -> B -> C)..."
)
# Step 1 claims to start at disconnected term_e
unproved_step_1_res = P.Step(term_e, action_1, term_b, registry)()
unproved_step_1 = M.Head(unproved_step_1_res)()
registry = M.Head(M.Tail(unproved_step_1_res)())()

unproved_steps = M.Pair(unproved_step_1, M.Pair(step_2, M.EmptyList))
unproved_der_res = P.Derivation(unproved_steps, cost_zero, registry)()
unproved_derivation = M.Head(unproved_der_res)()
registry = M.Head(M.Tail(unproved_der_res)())()

res2 = CheckerB.VerifyDerivation(
    unproved_derivation, term_a, term_c, trusted_rules, registry
)()
tag2 = M.Head(res2)()
is_unproved_start_caught = (
    M.IdentityCompare(tag2, L.StepDiscontinuityLabel)() is M.truth_value
)
print(f"    Verdict: {tag2} (Rejected: {is_unproved_start_caught})")
assert (
    is_unproved_start_caught
), f"Attack 2 Failed: Unproved start state not caught by StepDiscontinuityLabel: {tag2}"

print(
    "[4] Attack Vector 3: Conclusion Mutation on Self-Loop (A -> A via A -> B rule)..."
)
# Step claims rule 1 derives A instead of B
forged_step_res = P.Step(term_a, action_1, term_a, registry)()
forged_step = M.Head(forged_step_res)()
registry = M.Head(M.Tail(forged_step_res)())()

forged_steps = M.Pair(forged_step, M.EmptyList)
forged_der_res = P.Derivation(forged_steps, cost_zero, registry)()
forged_derivation = M.Head(forged_der_res)()
registry = M.Head(M.Tail(forged_der_res)())()

res3 = CheckerB.VerifyDerivation(
    forged_derivation, term_a, term_a, trusted_rules, registry
)()
tag3 = M.Head(res3)()
is_forged_conclusion_caught = (
    M.IdentityCompare(tag3, L.ConclusionMutationLabel)() is M.truth_value
)
print(f"    Verdict: {tag3} (Rejected: {is_forged_conclusion_caught})")
assert (
    is_forged_conclusion_caught
), f"Attack 3 Failed: Forged self-conclusion not caught by ConclusionMutationLabel: {tag3}"

print(
    "[5] Attack Vector 4: Stale / Altered Ruleset Attack (Rule 2 replaced with Rule 2')..."
)
# Valid derivation checked against a modified ruleset where Rule 2 is altered
altered_rule_2 = P.Rule(term_b, term_d)()
altered_rules = M.Pair(rule_1, M.Pair(altered_rule_2, M.EmptyList))

valid_steps = M.Pair(step_1, M.Pair(step_2, M.EmptyList))
valid_der_res = P.Derivation(valid_steps, cost_zero, registry)()
valid_derivation = M.Head(valid_der_res)()
registry = M.Head(M.Tail(valid_der_res)())()

res4 = CheckerB.VerifyDerivation(
    valid_derivation, term_a, term_c, altered_rules, registry
)()
tag4 = M.Head(res4)()
is_unknown_rule_caught = (
    M.IdentityCompare(tag4, L.UnknownRuleLabel)() is M.truth_value
)
print(f"    Verdict: {tag4} (Rejected: {is_unknown_rule_caught})")
assert (
    is_unknown_rule_caught
), f"Attack 4 Failed: Altered ruleset not caught by UnknownRuleLabel: {tag4}"

print(
    "[6] Attack Vector 5: Variable Pattern Matching Forgery (Non-Matching Term)..."
)
# Rule: Pair(ZeroLabel, var_pattern) -> var_pattern
var_x = M.Var()
var_pattern = M.Pair(M.VarTag, M.Pair(var_x, M.EmptyList))
rule_pattern = M.Pair(L.ZeroLabel, var_pattern)
var_rule = P.Rule(rule_pattern, var_pattern)()
var_rules = M.Pair(var_rule, M.EmptyList)

# Target term is Pair(SuccLabel, atom_a) - does NOT match ZeroLabel!
non_matching_term = M.Pair(L.SuccLabel, atom_a)
var_action = P.RewriteAction(var_rule, M.EmptyList)()

# Adversary claims var_action derived atom_a from non_matching_term
forged_var_step_res = P.Step(
    non_matching_term, var_action, term_a, registry
)()
forged_var_step = M.Head(forged_var_step_res)()
registry = M.Head(M.Tail(forged_var_step_res)())()

forged_var_steps = M.Pair(forged_var_step, M.EmptyList)
forged_var_der_res = P.Derivation(forged_var_steps, cost_zero, registry)()
forged_var_derivation = M.Head(forged_var_der_res)()
registry = M.Head(M.Tail(forged_var_der_res)())()

res5 = CheckerB.VerifyDerivation(
    forged_var_derivation, non_matching_term, term_a, var_rules, registry
)()
tag5 = M.Head(res5)()
is_var_mismatch_caught = (
    M.IdentityCompare(tag5, L.ConclusionMutationLabel)() is M.truth_value
)
print(f"    Verdict: {tag5} (Rejected: {is_var_mismatch_caught})")
assert (
    is_var_mismatch_caught
), f"Attack 5 Failed: Non-matching variable pattern derivation not caught: {tag5}"

print(
    "[7] Attack Vector 6: Foreign Goal Replay (Valid A -> C Proof for Goal D)..."
)
res6 = CheckerB.VerifyDerivation(
    valid_derivation, term_a, term_d, trusted_rules, registry
)()
tag6 = M.Head(res6)()
is_foreign_goal_caught = (
    M.IdentityCompare(tag6, L.GoalMismatchLabel)() is M.truth_value
)
print(f"    Verdict: {tag6} (Rejected: {is_foreign_goal_caught})")
assert (
    is_foreign_goal_caught
), f"Attack 6 Failed: Foreign goal replay not caught by GoalMismatchLabel: {tag6}"

print(
    "[8] Attack Vector 7: Policy Scope & Session Smuggling Attack..."
)
session_one = M.Atom()
session_two = M.Atom()

valid_receipt = M.Pair(
    L.ProofReceiptLabel,
    M.Pair(
        session_one,
        M.Pair(
            term_a,
            M.Pair(
                term_c,
                M.Pair(
                    valid_derivation,
                    M.EmptyList,
                ),
            ),
        ),
    ),
)
foreign_policy = M.Pair(
    L.CheckPolicyLabel,
    M.Pair(
        session_two,
        M.Pair(
            term_a,
            M.Pair(
                term_c,
                M.EmptyList,
            ),
        ),
    ),
)
res7 = CheckerB.VerifyProofReceipt(
    valid_receipt, foreign_policy, trusted_rules, registry
)()
tag7 = M.Head(res7)()
is_scope_smuggle_caught = (
    M.IdentityCompare(tag7, L.CandidateScopeMismatchLabel)() is M.truth_value
)
print(f"    Verdict: {tag7} (Rejected: {is_scope_smuggle_caught})")
assert (
    is_scope_smuggle_caught
), f"Attack 7 Failed: Session scope mismatch not caught: {tag7}"

print(
    "[9] Attack Vector 8: Knowledge Immutability & Trust Boundary Integrity..."
)
# Verify that running all checks left the hypergraph and rule sets completely unmutated
rules_unchanged = (
    M.IdentityCompare(initial_all_rules, graph.all_rules)() is M.truth_value
)
derivations_unchanged = (
    M.IdentityCompare(initial_derivations, graph.derivations)()
    is M.truth_value
)

print(f"    Rules store unchanged: {rules_unchanged}")
print(f"    Derivations store unchanged: {derivations_unchanged}")
assert rules_unchanged, "Attack 8 Failed: Rule store was mutated during checking!"
assert (
    derivations_unchanged
), "Attack 8 Failed: Derivation store was mutated during checking!"

print()
print(
    f"=== ALL 8 ADVERSARIAL RED-TEAM PROBES PASSED in {time.time() - t0:.3f}s ==="
)
