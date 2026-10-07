# ============================================================
# TEST 8: ODR G4/CL2B Invariant Trace Miner & Unreachability Prover
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
from cat_theo_machine import invariant_miner as Miner
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 8: ODR G4/CL2B Invariant Trace Miner ===")
print()

print("[1] Initializing runtime, hypergraph, and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

# Define tags:
tag_even = M.Atom()
tag_odd = M.Atom()
tag_step1 = M.Atom()
tag_step2 = M.Atom()
tag_step3 = M.Atom()

# Invariant property patterns:
phi_parity = Inv.Phi(tag_even)()
phi_step1 = Inv.Phi(tag_step1)()

# Candidate templates chain:
candidate_templates = M.Pair(phi_step1, M.Pair(phi_parity, M.EmptyList))

# Domain states:
# Each state is a Pair chain containing the parity invariant tag:
# state_1: tag_even -> state_2: tag_even -> state_3: tag_even
# state_odd: tag_odd
state_1 = tag_even
state_2 = tag_even
state_3 = tag_even
state_odd = tag_odd

# Rules:
# Rule 1: state_1 -> state_2 (Preserves tag_even)
# Rule 2: state_2 -> state_3 (Preserves tag_even)
# Rule 3 (Scope Breaker): state_1 -> state_odd (Breaks tag_even)
rule_1 = P.Rule(state_1, state_2)()
rule_2 = P.Rule(state_2, state_3)()
rule_breaker = P.Rule(state_1, state_odd)()

even_rules = M.Pair(rule_1, M.Pair(rule_2, M.EmptyList))
mixed_rules = M.Pair(rule_1, M.Pair(rule_2, M.Pair(rule_breaker, M.EmptyList)))

# Build training trace from rule_1 and rule_2:
action_1 = P.RewriteAction(rule_1, M.EmptyList)()
step_1_res = P.Step(state_1, action_1, state_2, registry)()
step_1 = M.Head(step_1_res)()
registry = M.Head(M.Tail(step_1_res)())()

action_2 = P.RewriteAction(rule_2, M.EmptyList)()
step_2_res = P.Step(state_2, action_2, state_3, registry)()
step_2 = M.Head(step_2_res)()
registry = M.Head(M.Tail(step_2_res)())()

valid_steps = M.Pair(step_1, M.Pair(step_2, M.EmptyList))
cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
der_res = P.Derivation(valid_steps, cost_zero, registry)()
training_trace = M.Head(der_res)()
registry = M.Head(M.Tail(der_res)())()

print("[2] Test Case 1: Extracting Intermediate States from Trace...")
states_res = Miner.ExtractTraceStates(training_trace, state_1, registry)()
count_states = 0
cur = states_res
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    count_states += 1
    cur = M.Tail(cur)()
print(f"    Extracted {count_states} trace states (Expected 3).")
assert (
    count_states == 3
), f"Test 1 Failed: Expected 3 trace states, got {count_states}"

print(
    "[3] Test Case 2: Testing Invariant Preservation Across Even Ruleset (Phi_Parity)..."
)
pres_res1 = Miner.CheckInvariantPreservationAcrossRules(
    phi_parity, even_rules, registry
)()
is_preserved_1 = M.Head(pres_res1)()
is_preserved_bool = (
    M.IdentityCompare(is_preserved_1, M.truth_value)() is M.truth_value
)
print(f"    Preservation Result: {is_preserved_1} (Passed: {is_preserved_bool})")
assert (
    is_preserved_bool
), "Test 2 Failed: Phi_Parity was not preserved across even_rules!"

print(
    "[4] Test Case 3: Testing Invariant Refutation with Scope Breaker Rule..."
)
pres_res2 = Miner.CheckInvariantPreservationAcrossRules(
    phi_parity, mixed_rules, registry
)()
is_preserved_2 = M.Head(pres_res2)()
is_refuted_bool = (
    M.IdentityCompare(is_preserved_2, M.false_value)() is M.truth_value
)
print(
    f"    Refutation Result: {is_preserved_2} (Refuted as expected: {is_refuted_bool})"
)
assert (
    is_refuted_bool
), "Test 3 Failed: Scope breaker rule was not caught by preservation check!"

print("[5] Test Case 4: Mining Invariant from Trace & Emitting Certificate...")
mine_res = Miner.MineInvariantFromTrace(
    training_trace, state_1, even_rules, candidate_templates, registry
)()
is_mined = M.Head(mine_res)()
is_mined_bool = M.IdentityCompare(is_mined, M.truth_value)() is M.truth_value
cert = M.Head(M.Tail(mine_res)())()
cert_phi = Miner.InvariantCertificatePhi(cert)()
print(
    f"    Mining Result: {is_mined} (Mined Phi: {cert_phi}, Passed: {is_mined_bool})"
)
assert is_mined_bool, "Test 4 Failed: Invariant was not mined from trace!"

print(
    "[6] Test Case 5: Converting Invariant to CandidateMacro and Evaluating Proof..."
)
macro_id = M.Atom()
macro_plan = M.Pair(action_1, M.Pair(action_2, M.EmptyList))
macro_res = Miner.MineInvariantToCandidateMacro(
    training_trace,
    state_1,
    state_3,
    even_rules,
    candidate_templates,
    macro_id,
    macro_plan,
    registry,
)()
macro_tag = M.Head(macro_res)()
is_macro_created = (
    M.IdentityCompare(macro_tag, L.CandidateMacroLabel)() is M.truth_value
)
print(f"    Candidate Macro Tag: {macro_tag} (Passed: {is_macro_created})")
assert (
    is_macro_created
), f"Test 5 Failed: CandidateMacro was not created: {macro_tag}"

candidate_macro = M.Head(M.Tail(macro_res)())()

# Feed mined candidate macro directly into CL4 Evaluator
eval_res = Eval.EvaluateCandidateProof(
    candidate_macro, state_1, state_3, even_rules, registry
)()
eval_tag = M.Head(eval_res)()
is_eval_passed = (
    M.IdentityCompare(eval_tag, L.CandidateEvaluatedLabel)() is M.truth_value
)
print(
    f"    Evaluator + Checker B Result: {eval_tag} (Verified: {is_eval_passed})"
)
assert (
    is_eval_passed
), f"Test 5 Failed: Mined macro failed evaluation: {eval_tag}"

print(
    "[7] Test Case 6: Mathematical Unreachability Proof by Invariant Obstruction..."
)
unreach_res = Miner.UnreachabilityProverByInvariant(
    state_1, state_odd, even_rules, phi_parity, registry
)()
unreach_tag = M.Head(unreach_res)()
is_unreachable_proved = (
    M.IdentityCompare(unreach_tag, L.UnreachableLabel)() is M.truth_value
)
print(
    f"    Unreachability Proof Tag: {unreach_tag} (Proved: {is_unreachable_proved})"
)
assert (
    is_unreachable_proved
), f"Test 6 Failed: Unreachability was not proved: {unreach_tag}"

print()
print(
    f"=== ALL 6 G4/CL2B INVARIANT MINER TESTS PASSED in {time.time() - t0:.3f}s ==="
)
