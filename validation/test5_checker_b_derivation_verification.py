# ============================================================
# TEST 5: Independent Proof Checker B — Step-Level Derivation Verification
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
print("=== TEST 5: Independent Proof Checker B ===")
print()

print("[1] Creating fresh runtime and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

# Build terms: A, B, C, D
atom_a = M.Atom()
atom_b = M.Atom()
atom_c = M.Atom()
atom_d = M.Atom()

term_a = M.Pair(atom_a, M.EmptyList)
term_b = M.Pair(atom_b, M.EmptyList)
term_c = M.Pair(atom_c, M.EmptyList)
term_d = M.Pair(atom_d, M.EmptyList)

# Build trusted rules:
# Rule 1: term_a -> term_b
# Rule 2: term_b -> term_c
rule_1 = P.Rule(term_a, term_b)()
rule_2 = P.Rule(term_b, term_c)()
trusted_rules = M.Pair(rule_1, M.Pair(rule_2, M.EmptyList))

# Untrusted / fabricated rule:
fake_rule = P.Rule(term_b, term_c)()

# Build valid steps and actions
action_1 = P.RewriteAction(rule_1, M.EmptyList)()
step_1_res = P.Step(term_a, action_1, term_b, registry)()
step_1 = M.Head(step_1_res)()
registry = M.Head(M.Tail(step_1_res)())()

action_2 = P.RewriteAction(rule_2, M.EmptyList)()
step_2_res = P.Step(term_b, action_2, term_c, registry)()
step_2 = M.Head(step_2_res)()
registry = M.Head(M.Tail(step_2_res)())()

valid_steps = M.Pair(step_1, M.Pair(step_2, M.EmptyList))
cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
der_res = P.Derivation(valid_steps, cost_zero, registry)()
valid_derivation = M.Head(der_res)()
registry = M.Head(M.Tail(der_res)())()

print("[2] Running Test Case 1: Valid 2-Step Derivation (A -> B -> C)...")
res1 = CheckerB.VerifyDerivation(
    valid_derivation, term_a, term_c, trusted_rules, registry
)()
tag1 = M.Head(res1)()
is_verified = M.IdentityCompare(tag1, L.DerivationVerifiedLabel)() is M.truth_value
print(f"    Verdict: {tag1} (Passed: {is_verified})")
assert is_verified, f"Test 1 Failed: Valid derivation was not verified: {tag1}"

print("[3] Running Test Case 2: Tampered Intermediate Conclusion (A -> D -> C)...")
tampered_step_1_res = P.Step(term_a, action_1, term_d, registry)()
tampered_step_1 = M.Head(tampered_step_1_res)()
registry = M.Head(M.Tail(tampered_step_1_res)())()

tampered_steps = M.Pair(tampered_step_1, M.Pair(step_2, M.EmptyList))
tampered_der_res = P.Derivation(tampered_steps, cost_zero, registry)()
tampered_derivation = M.Head(tampered_der_res)()
registry = M.Head(M.Tail(tampered_der_res)())()

res2 = CheckerB.VerifyDerivation(
    tampered_derivation, term_a, term_c, trusted_rules, registry
)()
tag2 = M.Head(res2)()
is_mutation_caught = (
    M.IdentityCompare(tag2, L.ConclusionMutationLabel)() is M.truth_value
)
print(f"    Verdict: {tag2} (Rejected as expected: {is_mutation_caught})")
assert (
    is_mutation_caught
), f"Test 2 Failed: Tampered step was not caught by ConclusionMutationLabel: {tag2}"

print("[4] Running Test Case 3: Untrusted / Fabricated Rule Injection...")
fake_action = P.RewriteAction(fake_rule, M.EmptyList)()
fake_step_res = P.Step(term_b, fake_action, term_c, registry)()
fake_step = M.Head(fake_step_res)()
registry = M.Head(M.Tail(fake_step_res)())()

fake_steps = M.Pair(step_1, M.Pair(fake_step, M.EmptyList))
fake_der_res = P.Derivation(fake_steps, cost_zero, registry)()
fake_derivation = M.Head(fake_der_res)()
registry = M.Head(M.Tail(fake_der_res)())()

res3 = CheckerB.VerifyDerivation(
    fake_derivation, term_a, term_c, trusted_rules, registry
)()
tag3 = M.Head(res3)()
is_unknown_rule_caught = (
    M.IdentityCompare(tag3, L.UnknownRuleLabel)() is M.truth_value
)
print(f"    Verdict: {tag3} (Rejected as expected: {is_unknown_rule_caught})")
assert (
    is_unknown_rule_caught
), f"Test 3 Failed: Fabricated rule was not rejected by UnknownRuleLabel: {tag3}"

print("[5] Running Test Case 4: Goal Mismatch (Derives C, but Goal is D)...")
res4 = CheckerB.VerifyDerivation(
    valid_derivation, term_a, term_d, trusted_rules, registry
)()
tag4 = M.Head(res4)()
is_goal_mismatch_caught = (
    M.IdentityCompare(tag4, L.GoalMismatchLabel)() is M.truth_value
)
print(f"    Verdict: {tag4} (Rejected as expected: {is_goal_mismatch_caught})")
assert (
    is_goal_mismatch_caught
), f"Test 4 Failed: Goal mismatch was not rejected by GoalMismatchLabel: {tag4}"

print("[6] Running Test Case 5: Full ProofReceipt Verification...")
session_id = M.Atom()
receipt = M.Pair(
    L.ProofReceiptLabel,
    M.Pair(
        session_id,
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
policy = M.Pair(
    L.CheckPolicyLabel,
    M.Pair(
        session_id,
        M.Pair(
            term_a,
            M.Pair(
                term_c,
                M.EmptyList,
            ),
        ),
    ),
)
res5 = CheckerB.VerifyProofReceipt(receipt, policy, trusted_rules, registry)()
tag5 = M.Head(res5)()
is_receipt_verified = (
    M.IdentityCompare(tag5, L.DerivationVerifiedLabel)() is M.truth_value
)
print(f"    Verdict: {tag5} (Passed: {is_receipt_verified})")
assert (
    is_receipt_verified
), f"Test 5 Failed: Valid ProofReceipt was not verified: {tag5}"

print("[7] Running Test Case 6: Policy Session ID Mismatch...")
diff_session_id = M.Atom()
mismatched_policy = M.Pair(
    L.CheckPolicyLabel,
    M.Pair(
        diff_session_id,
        M.Pair(
            term_a,
            M.Pair(
                term_c,
                M.EmptyList,
            ),
        ),
    ),
)
res6 = CheckerB.VerifyProofReceipt(
    receipt, mismatched_policy, trusted_rules, registry
)()
tag6 = M.Head(res6)()
is_scope_mismatch_caught = (
    M.IdentityCompare(tag6, L.CandidateScopeMismatchLabel)() is M.truth_value
)
print(f"    Verdict: {tag6} (Rejected as expected: {is_scope_mismatch_caught})")
assert (
    is_scope_mismatch_caught
), f"Test 6 Failed: Session scope mismatch was not rejected: {tag6}"

print("[8] Running Test Case 7: Policy Premise Mismatch...")
mismatched_premise_policy = M.Pair(
    L.CheckPolicyLabel,
    M.Pair(
        session_id,
        M.Pair(
            term_b,
            M.Pair(
                term_c,
                M.EmptyList,
            ),
        ),
    ),
)
res7 = CheckerB.VerifyProofReceipt(
    receipt, mismatched_premise_policy, trusted_rules, registry
)()
tag7 = M.Head(res7)()
is_premise_mismatch_caught = (
    M.IdentityCompare(tag7, L.PremiseMismatchLabel)() is M.truth_value
)
print(f"    Verdict: {tag7} (Rejected as expected: {is_premise_mismatch_caught})")
assert (
    is_premise_mismatch_caught
), f"Test 7 Failed: Premise mismatch was not rejected: {tag7}"

print("[9] Running Test Case 8: Empty Derivation Identity Proof (A -> A)...")
empty_der_res = P.Derivation(M.EmptyList, cost_zero, registry)()
empty_derivation = M.Head(empty_der_res)()
registry = M.Head(M.Tail(empty_der_res)())()

res8_pass = CheckerB.VerifyDerivation(
    empty_derivation, term_a, term_a, trusted_rules, registry
)()
tag8_pass = M.Head(res8_pass)()
is_identity_pass = (
    M.IdentityCompare(tag8_pass, L.DerivationVerifiedLabel)() is M.truth_value
)
print(f"    Verdict (A == A): {tag8_pass} (Passed: {is_identity_pass})")
assert (
    is_identity_pass
), f"Test 8a Failed: Empty derivation for identical start/goal did not verify: {tag8_pass}"

res8_fail = CheckerB.VerifyDerivation(
    empty_derivation, term_a, term_c, trusted_rules, registry
)()
tag8_fail = M.Head(res8_fail)()
is_identity_fail = (
    M.IdentityCompare(tag8_fail, L.GoalMismatchLabel)() is M.truth_value
)
print(
    f"    Verdict (A != C): {tag8_fail} (Rejected as expected: {is_identity_fail})"
)
assert (
    is_identity_fail
), f"Test 8b Failed: Empty derivation for different start/goal was not rejected: {tag8_fail}"

print()
print(
    f"=== ALL 8 CHECKER B VERIFICATION TESTS PASSED in {time.time() - t0:.3f}s ==="
)
