# ============================================================
# TEST 33: Existential witness introduction (W21)
#
# A knowledge-rewrite replacement may mention a variable the premises
# did not bind. Instantiation must mint a fresh Thingy and record the
# introduction; Checker B accepts the step only when that record is
# present, and refuses a successor that still contains a Var.
#
# Generic: two opaque relations and anonymous atoms. No FLT, no named
# witnesses (no m, n, foot), no geometry catalogue.
#
# Not claimed: EveryStateMoves, unique factorisation, constructions.
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
from cat_theo_machine import evaluator as Eval
from cat_theo_machine import graph_task as GT
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine import promotion_ledger as Ledger
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 33: Existential witness introduction ===")
print()
print("    Not claimed: FLT, EveryStateMoves, geometry constructions.")
print()


def var_pattern():
    return M.Pair(M.VarTag, M.Pair(M.Var(), M.EmptyList))


def fact2(rel, a):
    return M.Pair(rel, M.Pair(a, M.EmptyList))


def fact3(rel, a, b, c):
    return M.Pair(rel, M.Pair(a, M.Pair(b, M.Pair(c, M.EmptyList))))


def fact_bound(rel, a, b):
    return M.Pair(rel, M.Pair(a, M.Pair(b, M.EmptyList)))


def prepend_bindings(extra, base):
    acc = base
    cur = extra
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        acc = M.Pair(M.Head(cur)(), acc)
        cur = M.Tail(cur)()
    return acc


runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()

rel_p = M.Atom()
rel_q = M.Atom()
rel_r = M.Atom()
rel_s = M.Atom()
atom_a = M.Atom()
atom_b = M.Atom()
atom_c = M.Atom()
atom_d = M.Atom()

vx = var_pattern()
vy = var_pattern()
vz = var_pattern()

premises = M.Pair(
    fact2(rel_p, vx),
    M.Pair(fact2(rel_q, vy), M.EmptyList),
)
replacement = M.Pair(fact3(rel_r, vx, vy, vz), M.EmptyList)
rule = P.MultiRule(premises, replacement)()
trusted = M.Pair(rule, M.EmptyList)
assert P.ReplacementIsFactList(rule)() is M.truth_value

fact_p = fact2(rel_p, atom_a)
fact_q = fact2(rel_q, atom_b)
start_facts = M.Pair(fact_p, M.Pair(fact_q, M.EmptyList))
start_state = P.Knowledge(start_facts)()

# --- [1] forward engine mints a Thingy, not a leftover Var ----------------
print("[1] ForwardDeriveFacts on a two-premise rule with a third replacement var...")
one = M.Head(M.Succ(M.Zero, registry)())()
derived = GT.ForwardDeriveFacts(start_facts, trusted, one, registry)()
assert P.ContainsVar(derived)() is M.false_value, (
    "derived facts must not contain leftover Var patterns"
)
new_fact = None
cur = derived
found_new = M.false_value
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    f = M.Head(cur)()
    is_old_p = M.Compare(f, fact_p)() is M.truth_value
    is_old_q = M.Compare(f, fact_q)() is M.truth_value
    if (not is_old_p) and (not is_old_q):
        new_fact = f
        found_new = M.truth_value
        break
    cur = M.Tail(cur)()
assert found_new is M.truth_value, "the rule must produce a new fact"
assert P.ContainsVar(new_fact)() is M.false_value, "the new fact must be ground"
print("    New fact is ground (no leftover Var).")
print()

# --- [2] two mintings produce distinct witnesses --------------------------
print("[2] Two mintings of the same leftover-var term are Compare-unequal...")
joins = P.JoinPremises(P.RulePremises(rule)(), start_facts, M.EmptyList)()
assert M.IdentityCompare(joins, M.EmptyList)() is M.false_value
premise_bindings = M.Head(joins)()
inst_list = P.InstantiateFactList(P.RuleReplacement(rule)(), premise_bindings)()
assert P.ContainsVar(inst_list)() is M.truth_value, (
    "Instantiate without minting must leave the unbound var"
)
m1 = GT.MintUnboundWitnessesInList(inst_list)()
m2 = GT.MintUnboundWitnessesInList(inst_list)()
ground1 = M.Head(m1)()
ground2 = M.Head(m2)()
assert M.Compare(ground1, ground2)() is M.false_value, (
    "two firings must mint distinct witnesses"
)
print("    Distinct Thingy witnesses (Compare unequal).")
print()

# --- [3] Checker B verifies a recorded introduction -----------------------
print("[3] Checker B verifies a step whose action records the minted witness...")
applied = GT.ApplyKnowledgeRewriteWithWitnesses(
    start_state, rule, premise_bindings
)()
next_state = M.Head(applied)()
extra = M.Tail(applied)()
assert M.IdentityCompare(extra, M.EmptyList)() is M.false_value, (
    "the introduction must be recorded"
)
assert P.ContainsVar(next_state)() is M.false_value
action_bindings = prepend_bindings(extra, premise_bindings)
action = P.TheoremAction(rule, action_bindings)()
step_pair = P.Step(start_state, action, next_state, registry)()
step = M.Head(step_pair)()
step_reg = M.Head(M.Tail(step_pair)())()
step_check = CheckerB.VerifyProofStep(
    step, trusted, M.Pair(start_state, M.EmptyList), M.Pair(start_state, M.EmptyList), step_reg
)()
assert M.IdentityCompare(M.Head(step_check)(), L.StepVerifiedLabel)() is M.truth_value, (
    "Checker B must accept a step whose introductions are recorded"
)
print("    Step verified.")
print()

# --- [4] same steps against a different goal are refused ------------------
print("[4] The same derivation against a different goal is refused...")
cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
der_pair = P.Derivation(M.Pair(step, M.EmptyList), cost_zero, step_reg)()
derivation = M.Head(der_pair)()
der_reg = M.Head(M.Tail(der_pair)())()
ok_verdict = CheckerB.VerifyDerivation(
    derivation, start_state, next_state, trusted, der_reg
)()
assert M.IdentityCompare(M.Head(ok_verdict)(), L.DerivationVerifiedLabel)() is M.truth_value, (
    "the derivation must verify against the reached state"
)
wrong_goal = P.Knowledge(M.Pair(fact2(rel_s, atom_c), M.EmptyList))()
wrong_verdict = CheckerB.VerifyDerivation(
    derivation, start_state, wrong_goal, trusted, der_reg
)()
assert M.IdentityCompare(M.Head(wrong_verdict)(), L.DerivationVerifiedLabel)() is M.false_value, (
    "a different goal must not verify"
)
print("    Wrong goal refused.")
print()

# --- [5] smuggled unbound Var is refused ----------------------------------
print("[5] A successor that still contains a Var is refused...")
raw_next = P.ApplyKnowledgeRewrite(start_state, rule, premise_bindings)()
assert P.ContainsVar(raw_next)() is M.truth_value, (
    "ApplyKnowledgeRewrite without minting leaves the unbound var"
)
smuggle_action = P.TheoremAction(rule, premise_bindings)()
smuggle_pair = P.Step(start_state, smuggle_action, raw_next, der_reg)()
smuggle_step = M.Head(smuggle_pair)()
smuggle_reg = M.Head(M.Tail(smuggle_pair)())()
smuggle_check = CheckerB.VerifyProofStep(
    smuggle_step,
    trusted,
    M.Pair(start_state, M.EmptyList),
    M.Pair(start_state, M.EmptyList),
    smuggle_reg,
)()
assert M.IdentityCompare(M.Head(smuggle_check)(), L.UnboundVariableLabel)() is M.truth_value, (
    "a successor carrying a leftover Var must be UnboundVariable, not StepVerified"
)
print("    UnboundVariable refused.")
print()

# --- [6] fully-bound replacement introduces nothing -----------------------
print("[6] A fully-bound rule is unchanged: no witness minted...")
vx2 = var_pattern()
vy2 = var_pattern()
bound_premises = M.Pair(
    fact2(rel_p, vx2),
    M.Pair(fact2(rel_q, vy2), M.EmptyList),
)
bound_replacement = M.Pair(fact_bound(rel_s, vx2, vy2), M.EmptyList)
bound_rule = P.MultiRule(bound_premises, bound_replacement)()
bound_trusted = M.Pair(bound_rule, M.EmptyList)
bound_derived = GT.ForwardDeriveFacts(start_facts, bound_trusted, one, registry)()
expected_bound = fact_bound(rel_s, atom_a, atom_b)
has_expected = M.false_value
cur = bound_derived
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    if M.Compare(M.Head(cur)(), expected_bound)() is M.truth_value:
        has_expected = M.truth_value
        break
    cur = M.Tail(cur)()
assert has_expected is M.truth_value, (
    "the fully-bound rule must derive exactly R(a,b), no extra witness argument"
)
assert P.ContainsVar(bound_derived)() is M.false_value
bound_joins = P.JoinPremises(
    P.RulePremises(bound_rule)(), start_facts, M.EmptyList
)()
bound_bindings = M.Head(bound_joins)()
bound_inst = P.InstantiateFactList(
    P.RuleReplacement(bound_rule)(), bound_bindings
)()
bound_mint = GT.MintUnboundWitnessesInList(bound_inst)()
assert M.IdentityCompare(M.Tail(bound_mint)(), M.EmptyList)() is M.truth_value, (
    "a fully-bound replacement must record no introductions"
)
assert M.Compare(M.Head(bound_mint)(), bound_inst)() is M.truth_value, (
    "minting must be a no-op on a fully-bound fact list"
)
print("    Fully-bound rule: no introductions, fact is R(a,b).")
print()

# --- [7] introduction without a record is not verified --------------------
print("[7] Ground successor with no recorded introduction is refused...")
bare_action = P.TheoremAction(rule, premise_bindings)()
bare_pair = P.Step(start_state, bare_action, next_state, der_reg)()
bare_step = M.Head(bare_pair)()
bare_reg = M.Head(M.Tail(bare_pair)())()
bare_check = CheckerB.VerifyProofStep(
    bare_step,
    trusted,
    M.Pair(start_state, M.EmptyList),
    M.Pair(start_state, M.EmptyList),
    bare_reg,
)()
assert M.IdentityCompare(M.Head(bare_check)(), L.StepVerifiedLabel)() is M.false_value, (
    "Checker B must not accept a minted successor whose introductions were not recorded"
)
print("    Unrecorded introduction refused (" + str(M.Head(bare_check)()) + ").")
print()

# --- [8] ledger is asked --------------------------------------------------
print("[8] Asking the ledger to promote a candidate that uses the witness...")
macro = Eval.CandidateMacro(
    M.Char("witness_intro_candidate"),
    start_state,
    next_state,
    M.EmptyList,
)()
empty_ledger = Ledger.EmptyPromotionLedger(der_reg)()
promotion = Ledger.SubmitCandidateForPromotion(
    empty_ledger,
    macro,
    L.ProofSchemaPromotionLabel,
    start_state,
    next_state,
    cost_zero,
    M.EmptyList,
    M.EmptyList,
    trusted,
    der_reg,
)()
promo_tag = M.Head(promotion)()
assert (
    M.IdentityCompare(promo_tag, L.PromotionApprovedLabel)() is M.truth_value
    or M.IdentityCompare(promo_tag, L.PromotionRejectedLabel)() is M.truth_value
), "the ledger must answer, not skip"
if M.IdentityCompare(promo_tag, L.PromotionRejectedLabel)() is M.truth_value:
    reason = M.Head(M.Tail(promotion)())()
    print("    Ledger refused with a stated reason (tag=" + str(reason) + ").")
    assert M.NatEq(
        Ledger.PromotionLedgerVersion(empty_ledger)(), M.Zero, der_reg
    )() is M.truth_value, "a refusal must not advance the ledger"
else:
    print("    Ledger approved (receipt present).")
print()

elapsed = time.time() - t0
print("=== TEST 33 complete: 8/8 checks green (%.1f s) ===" % elapsed)
print("    Not derived: EveryStateMoves, FLT n=3/n=4, geometry constructions.")
