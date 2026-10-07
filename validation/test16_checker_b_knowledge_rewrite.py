# ============================================================
# TEST 16: Checker B over knowledge-rewriting derivations
#
# Independent verification of fact-list (knowledge) steps: the verifier must
# re-join a rule's premises against the current facts and reproduce the
# successor on its own, without trusting the recorded bindings, and it must
# accept a knowledge goal that the reached state covers.
#
# This is the generic coverage for the checker_b extension that the FLT
# n = 4 work forced: before it, every fact-list step was reported as
# ConclusionMutation because the rule pattern was matched against the whole
# knowledge term. No packs, no domain content, no search: two facts and one
# rewrite rule.
# ============================================================
import os
import sys
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine.runtime import make_fresh_runtime
from cat_theo_machine import checker_b as CheckerB
from cat_theo_machine import proof as P

t0 = time.time()
print("=== TEST 16: Checker B over knowledge-rewriting derivations ===")
print()

# --- [1] a machine, two facts, one fact-list rule -------------------------
print("[1] Building a knowledge rewrite: [fact_1, fact_2] -> [produced]...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
atom_a = M.Atom()
atom_b = M.Atom()
atom_c = M.Atom()
atom_d = M.Atom()
fact_one = M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))
fact_two = M.Pair(atom_c, M.Pair(atom_d, M.EmptyList))
produced_fact = M.Pair(atom_a, M.Pair(atom_d, M.EmptyList))
wrong_fact = M.Pair(atom_c, M.Pair(atom_b, M.EmptyList))
premises = M.Pair(fact_one, M.Pair(fact_two, M.EmptyList))
replacement = M.Pair(produced_fact, M.EmptyList)
rule = P.MultiRule(premises, replacement)()
trusted_rules = M.Pair(rule, M.EmptyList)
start_state = P.Knowledge(M.Pair(fact_one, M.Pair(fact_two, M.EmptyList)))()
assert P.IsKnowledge(start_state)() is M.truth_value, "the state must be a knowledge state"
assert P.ReplacementIsFactList(rule)() is M.truth_value, "the replacement must be a fact list"
print("    Rule is a multi-premise fact-list rewrite.")
print()

# --- [2] the machine joins the premises and applies the successor ---------
print("[2] The machine joins the premises against the facts and rewrites...")
joins = P.JoinPremises(P.RulePremises(rule)(), P.KnowledgeFacts(start_state)(), M.EmptyList)()
assert M.IdentityCompare(joins, M.EmptyList)() is M.false_value, "the premises must join"
bindings = M.Head(joins)()
next_state = P.ApplyKnowledgeRewrite(start_state, rule, bindings)()
action = P.TheoremAction(rule, bindings)()
step_pair = P.Step(start_state, action, next_state, registry)()
step = M.Head(step_pair)()
step_registry = M.Head(M.Tail(step_pair)())()
assert M.Compare(P.KnowledgeFacts(next_state)(), M.Pair(produced_fact, M.EmptyList))() is M.truth_value, (
    "the successor must be the produced fact"
)
print("    Successor knowledge state computed.")
print()

# --- [3] the step verifies independently -----------------------------------
print("[3] VerifyProofStep must re-derive the successor and accept it...")
step_check = CheckerB.VerifyProofStep(
    step, trusted_rules, M.Pair(start_state, M.EmptyList), M.Pair(start_state, M.EmptyList), step_registry
)()
assert M.IdentityCompare(M.Head(step_check)(), L.StepVerifiedLabel)() is M.truth_value, (
    "the verified step must reproduce the successor from the facts alone"
)
print("    Step verified from the facts, not from the recorded bindings.")
print()

# --- [4] a tampered successor must be refused ------------------------------
print("[4] A mutated successor must be rejected...")
tampered_state = P.Knowledge(M.Pair(wrong_fact, M.Pair(produced_fact, M.EmptyList)))()
tampered_pair = P.Step(start_state, action, tampered_state, step_registry)()
tampered_step = M.Head(tampered_pair)()
tampered_registry = M.Head(M.Tail(tampered_pair)())()
tampered_check = CheckerB.VerifyProofStep(
    tampered_step, trusted_rules, M.Pair(start_state, M.EmptyList), M.Pair(start_state, M.EmptyList), tampered_registry
)()
assert M.IdentityCompare(M.Head(tampered_check)(), L.ConclusionMutationLabel)() is M.truth_value, (
    "a mutated successor must be reported as a conclusion mutation"
)
print("    Mutation caught.")
print()

# --- [5] the full derivation verifies -------------------------------------
print("[5] A one-step derivation must verify against the reached state...")
cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
derivation_pair = P.Derivation(M.Pair(step, M.EmptyList), cost_zero, step_registry)()
derivation = M.Head(derivation_pair)()
derivation_registry = M.Head(M.Tail(derivation_pair)())()
verdict = CheckerB.VerifyDerivation(
    derivation, start_state, next_state, trusted_rules, derivation_registry
)()
assert M.IdentityCompare(M.Head(verdict)(), L.DerivationVerifiedLabel)() is M.truth_value, (
    "the derivation must verify against the exact reached state"
)
print("    Derivation verified.")
print()

# --- [6] a knowledge goal covered by the reached state is accepted ---------
print("[6] A covered knowledge goal must verify; a wrong goal must not...")
covered_goal = P.Knowledge(M.Pair(produced_fact, M.EmptyList))()
covered_verdict = CheckerB.VerifyDerivation(
    derivation, start_state, covered_goal, trusted_rules, derivation_registry
)()
assert M.IdentityCompare(M.Head(covered_verdict)(), L.DerivationVerifiedLabel)() is M.truth_value, (
    "a knowledge goal whose facts the reached state covers must verify"
)
wrong_goal = P.Knowledge(M.Pair(wrong_fact, M.EmptyList))()
wrong_verdict = CheckerB.VerifyDerivation(
    derivation, start_state, wrong_goal, trusted_rules, derivation_registry
)()
assert M.IdentityCompare(M.Head(wrong_verdict)(), L.GoalMismatchLabel)() is M.truth_value, (
    "an uncovered knowledge goal must be refused"
)
print("    Cover accepted, wrong goal refused.")
print()

# --- [7] the rule must be in the trusted set ------------------------------
print("[7] A step under an untrusted rule set must be refused...")
untrusted_check = CheckerB.VerifyProofStep(
    step, M.EmptyList, M.Pair(start_state, M.EmptyList), M.Pair(start_state, M.EmptyList), step_registry
)()
assert M.IdentityCompare(M.Head(untrusted_check)(), L.UnknownRuleLabel)() is M.truth_value, (
    "a rule outside the trusted set must be refused"
)
print("    Untrusted rule refused.")
print()

print("=== ALL TEST 16 KNOWLEDGE-REWRITE VERIFICATION CHECKS PASSED in %.3fs ===" % (time.time() - t0))
