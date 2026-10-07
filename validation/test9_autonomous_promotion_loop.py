# ============================================================
# TEST 9: ODR CL5 Autonomous Closed-Loop Promotion Pipeline & Ledger
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
from cat_theo_machine import invariance as Inv
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine import promotion_ledger as Ledger
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print(
    "=== TEST 9: ODR CL5 Autonomous Closed-Loop Promotion Pipeline & Ledger ==="
)
print()

print("[1] Initializing runtime, hypergraph, and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

# Define domain terms and tags
term_a = M.Atom()
term_b = M.Atom()
term_c = M.Atom()
term_invalid = M.Atom()

# Rules
rule_ab = P.Rule(term_a, term_b)()
rule_bc = P.Rule(term_b, term_c)()
rule_invalid = P.Rule(term_a, term_invalid)()

valid_rules = M.Pair(rule_ab, M.Pair(rule_bc, M.EmptyList))

# Actions
act_1 = P.RewriteAction(rule_ab, M.EmptyList)()
act_2 = P.RewriteAction(rule_bc, M.EmptyList)()
valid_plan = M.Pair(act_1, M.Pair(act_2, M.EmptyList))

# Training trace (term_a -> term_b -> term_c)
step_1_res = P.Step(term_a, act_1, term_b, registry)()
step_1 = M.Head(step_1_res)()
registry = M.Head(M.Tail(step_1_res)())()

step_2_res = P.Step(term_b, act_2, term_c, registry)()
step_2 = M.Head(step_2_res)()
registry = M.Head(M.Tail(step_2_res)())()

cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
der_res = P.Derivation(
    M.Pair(step_1, M.Pair(step_2, M.EmptyList)), cost_zero, registry
)()
training_trace = M.Head(der_res)()
registry = M.Head(M.Tail(der_res)())()

# Candidate Templates
phi_parity = Inv.Phi(term_a)()
candidate_templates = M.Pair(phi_parity, M.EmptyList)

# Baseline Cost for Ablation (4 steps)
r1 = M.Succ(M.Zero, registry)()
c1 = M.Head(r1)()
registry = M.Head(M.Tail(r1)())()

r2 = M.Succ(c1, registry)()
c2 = M.Head(r2)()
registry = M.Head(M.Tail(r2)())()

r3 = M.Succ(c2, registry)()
c3 = M.Head(r3)()
registry = M.Head(M.Tail(r3)())()

r4 = M.Succ(c3, registry)()
c4 = M.Head(r4)()
registry = M.Head(M.Tail(r4)())()

baseline_cost = P.ProofCost(c4, M.Zero, M.Zero, M.Zero)()

# Baseline Cost too small for negative ablation probe (0 steps)
insufficient_baseline_cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()

# Holdout Suite (Positive tests)
holdout_1 = M.Pair(term_a, M.Pair(term_c, M.Pair(M.truth_value, M.EmptyList)))
holdout_suite_clean = M.Pair(holdout_1, M.EmptyList)

# Holdout Suite with Failing Negative Target
holdout_failing = M.Pair(
    term_a, M.Pair(term_b, M.Pair(M.truth_value, M.EmptyList))
)  # Plan yields term_c != term_b
holdout_suite_failing = M.Pair(holdout_failing, M.EmptyList)

print("[2] Test Case 1: Initializing Empty Promotion Ledger...")
empty_ledger_res = Ledger.EmptyPromotionLedger(registry)()
init_ver = Ledger.PromotionLedgerVersion(empty_ledger_res)()
is_ver_zero = M.IdentityCompare(init_ver, M.Zero)() is M.truth_value
print(f"    Initial Ledger Version: {init_ver} (Version 0: {is_ver_zero})")
assert is_ver_zero, "Test 1 Failed: Initial ledger version is not zero!"

active_schemata = Ledger.QueryActivePromotions(
    empty_ledger_res, L.ProofSchemaPromotionLabel, registry
)()
is_empty_schemata = (
    M.IdentityCompare(active_schemata, M.EmptyList)() is M.truth_value
)
assert is_empty_schemata, "Test 1 Failed: Initial active schemata not empty!"
print("    Empty ledger verified.")

print(
    "[3] Test Case 2: Executing End-to-End Autonomous Discovery & Promotion Cycle..."
)
macro_id = M.Atom()
cycle_res = Ledger.ExecuteAutonomousDiscoveryCycle(
    training_trace,
    term_a,
    term_c,
    valid_rules,
    candidate_templates,
    macro_id,
    valid_plan,
    baseline_cost,
    holdout_suite_clean,
    L.ProofSchemaPromotionLabel,
    empty_ledger_res,
    registry,
)()
cycle_tag = M.Head(cycle_res)()
is_cycle_ok = (
    M.IdentityCompare(cycle_tag, L.AutonomousCycleCompletedLabel)()
    is M.truth_value
)
print(f"    Cycle Outcome: {cycle_tag} (Passed: {is_cycle_ok})")
assert (
    is_cycle_ok
), f"Test 2 Failed: Autonomous cycle failed with tag {cycle_tag}"

ledger_v1 = M.Head(M.Tail(cycle_res)())()
promoted_entry = M.Head(M.Tail(M.Tail(cycle_res)())())()

v1 = Ledger.PromotionLedgerVersion(ledger_v1)()
entry_id = Ledger.LedgerEntryId(promoted_entry)()
entry_status = Ledger.LedgerEntryStatus(promoted_entry)()
is_entry_active = (
    M.IdentityCompare(entry_status, L.PromotionActiveLabel)() is M.truth_value
)
print(
    f"    Ledger Version: {v1}, Promoted Entry ID: {entry_id}, Status: {entry_status}"
)
assert is_entry_active, "Test 2 Failed: Promoted entry is not marked active!"

# Query active promotions in ledger v1
active_v1 = Ledger.QueryActivePromotions(
    ledger_v1, L.ProofSchemaPromotionLabel, registry
)()
count_active = 0
cur = active_v1
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    count_active += 1
    cur = M.Tail(cur)()
print(f"    Active Schemata in Ledger: {count_active} (Expected 1)")
assert count_active == 1, "Test 2 Failed: Expected 1 active schema in ledger v1"

print(
    "[4] Test Case 3: Rejection Probe A — Corrupted/Untrusted Derivation Step..."
)
act_corrupt = P.RewriteAction(rule_invalid, M.EmptyList)()
corrupt_plan = M.Pair(act_corrupt, M.Pair(act_2, M.EmptyList))
bad_macro = Eval.CandidateMacro(macro_id, term_a, term_c, corrupt_plan)()

rej_a_res = Ledger.SubmitCandidateForPromotion(
    ledger_v1,
    bad_macro,
    L.ProofSchemaPromotionLabel,
    term_a,
    term_c,
    baseline_cost,
    holdout_suite_clean,
    M.EmptyList,
    valid_rules,
    registry,
)()
rej_a_tag = M.Head(rej_a_res)()
is_rej_a = (
    M.IdentityCompare(rej_a_tag, L.PromotionRejectedLabel)() is M.truth_value
)
print(
    f"    Corrupted Step Rejection Tag: {rej_a_tag} (Rejected as expected: {is_rej_a})"
)
assert is_rej_a, "Test 3 Failed: Corrupted step was not rejected at Gate 1!"

print("[5] Test Case 4: Rejection Probe B — Ablation Regression Gate...")
cand_macro = Ledger.LedgerEntryCandidate(promoted_entry)()
rej_b_res = Ledger.SubmitCandidateForPromotion(
    ledger_v1,
    cand_macro,
    L.ProofSchemaPromotionLabel,
    term_a,
    term_a,  # Trivial closure probe: start == goal
    baseline_cost,
    holdout_suite_clean,
    M.EmptyList,
    valid_rules,
    registry,
)()
rej_b_tag = M.Head(rej_b_res)()
is_rej_b = (
    M.IdentityCompare(rej_b_tag, L.PromotionRejectedLabel)() is M.truth_value
)
print(
    f"    Ablation Regression Tag: {rej_b_tag} (Rejected as expected: {is_rej_b})"
)
assert is_rej_b, "Test 4 Failed: Ablation regression was not caught at Gate 2!"

print(
    "[6] Test Case 5: Rejection Probe C — Withheld Holdout Regression Gate..."
)
rej_c_res = Ledger.SubmitCandidateForPromotion(
    ledger_v1,
    cand_macro,
    L.ProofSchemaPromotionLabel,
    term_a,
    term_c,
    baseline_cost,
    holdout_suite_failing,
    M.EmptyList,
    valid_rules,
    registry,
)()
rej_c_tag = M.Head(rej_c_res)()
is_rej_c = (
    M.IdentityCompare(rej_c_tag, L.PromotionRejectedLabel)() is M.truth_value
)
print(
    f"    Holdout Regression Tag: {rej_c_tag} (Rejected as expected: {is_rej_c})"
)
assert (
    is_rej_c
), "Test 5 Failed: Holdout suite failure was not caught at Gate 3!"

print("[7] Test Case 6: Promotion Rollback & Audit Provenance...")
revocation_reason = L.AblationRegressionLabel
rollback_res = Ledger.RollbackPromotion(
    ledger_v1, entry_id, revocation_reason, registry
)()
rollback_tag = M.Head(rollback_res)()
is_rollback_ok = (
    M.IdentityCompare(rollback_tag, L.PromotionRevokedLabel)() is M.truth_value
)
print(f"    Rollback Outcome: {rollback_tag} (Passed: {is_rollback_ok})")
assert is_rollback_ok, "Test 6 Failed: Rollback failed!"

ledger_v2 = M.Head(M.Tail(rollback_res)())()
v2 = Ledger.PromotionLedgerVersion(ledger_v2)()
revoked_entry = M.Head(M.Tail(M.Tail(rollback_res)())())()
revoked_status = Ledger.LedgerEntryStatus(revoked_entry)()
is_status_revoked = (
    M.IdentityCompare(revoked_status, L.PromotionRevokedLabel)()
    is M.truth_value
)
print(
    f"    Ledger Version after Rollback: {v2}, Revoked Entry Status: {revoked_status}"
)
assert is_status_revoked, "Test 6 Failed: Entry status is not revoked!"

active_v2 = Ledger.QueryActivePromotions(
    ledger_v2, L.ProofSchemaPromotionLabel, registry
)()
is_active_empty = (
    M.IdentityCompare(active_v2, M.EmptyList)() is M.truth_value
)
print(
    f"    Active Promoted Schemata after Rollback: {active_v2} (Empty: {is_active_empty})"
)
assert (
    is_active_empty
), "Test 6 Failed: Active schemata not empty after rollback!"

print(
    "[8] Test Case 7: Search Policy vs Proof Schema Dual-Ledger Separation..."
)
policy_id = M.Atom()
policy_hint = M.Pair(M.Atom(), M.Atom())
submit_policy_res = Ledger.SubmitCandidateForPromotion(
    ledger_v2,
    cand_macro,
    L.SearchPolicyPromotionLabel,
    term_a,
    term_c,
    baseline_cost,
    holdout_suite_clean,
    M.EmptyList,
    valid_rules,
    registry,
)()
policy_tag = M.Head(submit_policy_res)()
is_policy_promoted = (
    M.IdentityCompare(policy_tag, L.PromotionApprovedLabel)() is M.truth_value
)
print(f"    Search Policy Promotion Tag: {policy_tag} (Passed: {is_policy_promoted})")
assert is_policy_promoted, "Test 7 Failed: Search policy hint promotion failed!"

ledger_v3 = M.Head(M.Tail(submit_policy_res)())()
active_policies = Ledger.QueryActivePromotions(
    ledger_v3, L.SearchPolicyPromotionLabel, registry
)()
active_schemata_v3 = Ledger.QueryActivePromotions(
    ledger_v3, L.ProofSchemaPromotionLabel, registry
)()

count_active_policies = 0
cur_p = active_policies
while M.IdentityCompare(cur_p, M.EmptyList)() is M.false_value:
    count_active_policies += 1
    cur_p = M.Tail(cur_p)()

is_schemata_still_empty = (
    M.IdentityCompare(active_schemata_v3, M.EmptyList)() is M.truth_value
)
print(
    f"    Active Policies: {count_active_policies} (Expected 1), Active Schemata: (Empty: {is_schemata_still_empty})"
)
assert (
    count_active_policies == 1 and is_schemata_still_empty
), "Test 7 Failed: Dual-ledger separation violated!"

print()
print(
    f"=== ALL 7 CL5 AUTONOMOUS PROMOTION & LEDGER TESTS PASSED in {time.time() - t0:.3f}s ==="
)
