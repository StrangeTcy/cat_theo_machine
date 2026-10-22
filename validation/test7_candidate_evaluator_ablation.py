# ============================================================
# TEST 7: ODR CL4 Candidate Macro Expander, Evaluator & Ablation
# ============================================================
import os
import sys
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import evaluator as Eval
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 7: ODR CL4 Candidate Expander & Evaluator ===")
print()

print("[1] Initializing runtime and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

# Define constructor tags for domain
tag_succ = M.Atom()
tag_double = M.Atom()
tag_quad = M.Atom()
tag_oct = M.Atom()
tag_hex = M.Atom()

# Variable x
var_x = M.Var()
var_pattern_x = M.Pair(M.VarTag, M.Pair(var_x, M.EmptyList))

# Define patterns:
# Pattern 1: Pair(tag_succ, var_pattern_x)
# Pattern 2: Pair(tag_double, var_pattern_x)
# Pattern 3: Pair(tag_quad, var_pattern_x)
# Pattern 4: Pair(tag_oct, var_pattern_x)
pat_succ = M.Pair(tag_succ, var_pattern_x)
pat_double = M.Pair(tag_double, var_pattern_x)
pat_quad = M.Pair(tag_quad, var_pattern_x)
pat_oct = M.Pair(tag_oct, var_pattern_x)
pat_hex = M.Pair(tag_hex, var_pattern_x)

# Build trusted primitive rules:
# Rule 1: Succ(x) -> Double(x)
# Rule 2: Double(x) -> Quad(x)
# Rule 3: Quad(x) -> Oct(x)
rule_1 = P.Rule(pat_succ, pat_double)()
rule_2 = P.Rule(pat_double, pat_quad)()
rule_3 = P.Rule(pat_quad, pat_oct)()
trusted_rules = M.Pair(rule_1, M.Pair(rule_2, M.Pair(rule_3, M.EmptyList)))

# Build untrusted / fabricated rule:
fake_rule = P.Rule(pat_quad, pat_hex)()

# Build plan of actions for macro: [RewriteAction(rule_1), RewriteAction(rule_2), RewriteAction(rule_3)]
plan = M.Pair(
    P.RewriteAction(rule_1, M.EmptyList)(),
    M.Pair(
        P.RewriteAction(rule_2, M.EmptyList)(),
        M.Pair(
            P.RewriteAction(rule_3, M.EmptyList)(),
            M.EmptyList,
        ),
    ),
)

# Build CandidateMacro: Succ(x) -> Oct(x) via 3-step plan
macro_id = M.Atom()
candidate_macro = Eval.CandidateMacro(macro_id, pat_succ, pat_oct, plan)()

# Concrete test terms for instances:
val_1 = M.Atom()
val_2 = M.Atom()
val_3 = M.Atom()

inst1_start = M.Pair(tag_succ, M.Pair(val_1, M.EmptyList))
inst1_goal = M.Pair(tag_oct, M.Pair(val_1, M.EmptyList))

inst2_start = M.Pair(tag_succ, M.Pair(val_2, M.EmptyList))
inst2_goal = M.Pair(tag_oct, M.Pair(val_2, M.EmptyList))

inst3_start = M.Pair(tag_succ, M.Pair(val_3, M.EmptyList))
inst3_goal = M.Pair(tag_oct, M.Pair(val_3, M.EmptyList))

# Near-miss negative instance: goal is Hex(val_1) instead of Oct(val_1)
inst_neg1_goal = M.Pair(tag_hex, M.Pair(val_1, M.EmptyList))

print(
    "[2] Test Case 1: Expanding Candidate Macro on Concrete Instance (Succ -> Oct)..."
)
exp_res = Eval.ExpandCandidateMacro(
    candidate_macro, inst1_start, inst1_goal, registry
)()
exp_tag = M.Head(exp_res)()
is_expanded = (
    M.IdentityCompare(exp_tag, L.CandidateExpandedLabel)() is M.truth_value
)
print(f"    Expansion Verdict: {exp_tag} (Passed: {is_expanded})")
assert is_expanded, f"Test 1 Failed: Candidate macro did not expand: {exp_tag}"

print(
    "[3] Test Case 2: Evaluating Candidate Proof with Independent Checker B..."
)
eval_res = Eval.EvaluateCandidateProof(
    candidate_macro, inst1_start, inst1_goal, trusted_rules, registry
)()
eval_tag = M.Head(eval_res)()
is_evaluated = (
    M.IdentityCompare(eval_tag, L.CandidateEvaluatedLabel)() is M.truth_value
)
print(f"    Evaluation Verdict: {eval_tag} (Passed: {is_evaluated})")
assert (
    is_evaluated
), f"Test 2 Failed: Expanded proof failed checker evaluation: {eval_tag}"

print("[4] Test Case 3: Running Ablation Trial (With vs Without Macro)...")
abl_res = Eval.AblationTrial(
    candidate_macro, inst1_start, inst1_goal, trusted_rules, registry
)()
abl_tag = M.Head(abl_res)()
is_ablation_verified = (
    M.IdentityCompare(abl_tag, L.AblationVerifiedLabel)() is M.truth_value
)
print(f"    Ablation Verdict: {abl_tag} (Passed: {is_ablation_verified})")
assert (
    is_ablation_verified
), f"Test 3 Failed: Ablation trial did not verify: {abl_tag}"

print(
    "[5] Test Case 4: Near-Miss Negative Control (Unmatched Goal Pattern)..."
)
neg_res = Eval.EvaluateCandidateProof(
    candidate_macro, inst1_start, inst_neg1_goal, trusted_rules, registry
)()
neg_tag = M.Head(neg_res)()
is_neg_rejected = (
    M.IdentityCompare(neg_tag, L.CandidateMatchFailureLabel)() is M.truth_value
)
print(
    f"    Near-Miss Negative Verdict: {neg_tag} (Rejected as expected: {is_neg_rejected})"
)
assert (
    is_neg_rejected
), f"Test 4 Failed: Near-miss negative was not rejected: {neg_tag}"

print(
    "[6] Test Case 5: Untrusted Rule Injection Attack inside Candidate Plan..."
)
corrupt_plan = M.Pair(
    P.RewriteAction(rule_1, M.EmptyList)(),
    M.Pair(
        P.RewriteAction(fake_rule, M.EmptyList)(),
        M.Pair(
            P.RewriteAction(rule_3, M.EmptyList)(),
            M.EmptyList,
        ),
    ),
)
corrupt_macro = Eval.CandidateMacro(
    macro_id, pat_succ, pat_oct, corrupt_plan
)()
corrupt_res = Eval.EvaluateCandidateProof(
    corrupt_macro, inst1_start, inst1_goal, trusted_rules, registry
)()
corrupt_tag = M.Head(corrupt_res)()
is_unknown_caught = (
    M.IdentityCompare(corrupt_tag, L.UnknownRuleLabel)() is M.truth_value
)
print(
    f"    Injected Rule Verdict: {corrupt_tag} (Caught by Checker: {is_unknown_caught})"
)
assert (
    is_unknown_caught
), f"Test 5 Failed: Injected rule was not caught by UnknownRuleLabel: {corrupt_tag}"

print(
    "[7] Test Case 6: Evaluating Withheld Holdout Suite (3 Positives + 2 Negatives)..."
)
holdouts = M.Pair(
    M.Pair(inst1_start, M.Pair(inst1_goal, M.Pair(M.truth_value, M.EmptyList))),
    M.Pair(
        M.Pair(
            inst2_start, M.Pair(inst2_goal, M.Pair(M.truth_value, M.EmptyList))
        ),
        M.Pair(
            M.Pair(
                inst3_start,
                M.Pair(inst3_goal, M.Pair(M.truth_value, M.EmptyList)),
            ),
            M.Pair(
                M.Pair(
                    inst1_start,
                    M.Pair(inst_neg1_goal, M.Pair(M.false_value, M.EmptyList)),
                ),
                M.Pair(
                    M.Pair(
                        inst2_start,
                        M.Pair(
                            inst_neg1_goal, M.Pair(M.false_value, M.EmptyList)
                        ),
                    ),
                    M.EmptyList,
                ),
            ),
        ),
    ),
)
suite_res = Eval.EvaluateHoldoutSuite(
    candidate_macro, holdouts, trusted_rules, registry
)()
suite_tag = M.Head(suite_res)()
is_suite_passed = (
    M.IdentityCompare(suite_tag, L.HoldoutSuiteResultLabel)() is M.truth_value
)
passed_list = M.Head(M.Tail(suite_res)())()
failed_list = M.Head(M.Tail(M.Tail(suite_res)())())()

passed_count = 0
cur = passed_list
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    passed_count += 1
    cur = M.Tail(cur)()

failed_count = 0
cur = failed_list
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    failed_count += 1
    cur = M.Tail(cur)()

print(f"    Holdout Suite Verdict: {suite_tag} (Passed: {is_suite_passed})")
print(
    f"    Passed Count: {passed_count}, Failed Count: {failed_count} (Expected 5 passes, 0 fails)"
)
assert is_suite_passed, f"Test 6 Failed: Holdout suite failed: {suite_tag}"
assert (
    failed_count == 0
), f"Test 6 Failed: Some holdout tests failed: {failed_count}"
assert (
    passed_count == 5
), f"Test 6 Failed: Expected 5 passed holdout tests: {passed_count}"

print()
print(
    f"=== ALL 6 CL4 EVALUATOR & ABLATION TESTS PASSED in {time.time() - t0:.3f}s ==="
)
