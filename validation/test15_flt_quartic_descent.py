# ============================================================
# TEST 15: FLT n = 4 Quartic Descent (W6)
#
# Verifies packs/flt-quartic.pack.yaml:
#   - the pack loads with six rules and two replayable examples
#   - the mod 4 parity obstruction is the one the W3 Cartesian sweep
#     discovers on its own, not a number written into the pack
#   - the obstruction route prunes the goal with zero search expansions
#   - the descent route replays a five step derivation whose last step is
#     licensed by well-foundedness, and reaches NoSolution
#   - the algebraic content of every named lemma is checked by machine
#     arithmetic on concrete instances (parametrization, coprime factors,
#     relapse identities, strict decrease)
#   - negative controls: no minimality -> no descent; equal readings -> no prune
#   - the start state carries no numeral at all
#
# Flat machine-native style: no helper functions, no loops, no lists, no
# dicts, no python bools. Numerals are machine nodes built from reps, and
# every comparison is an edge call.
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
from cat_theo_machine import playground as PG
from cat_theo_machine.math import arithmetic as A
from cat_theo_machine.runtime import make_fresh_runtime
from cat_theo_machine import heuristics as H
from cat_theo_machine import invariance as I
from cat_theo_machine import packs as PACKS
from cat_theo_machine import proof as P

t0 = time.time()
print("=== TEST 15: FLT n = 4 Quartic Descent ===")
print()

print("[1] Initializing runtime, hypergraph, and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
graph._search_disable_console = M.truth_value
graph._search_disable_progress_ticker = M.truth_value
print("    Runtime OK.")
print()

# --- [2] load the pack ------------------------------------------------------
print("[2] Loading packs/flt-quartic.pack.yaml...")
namespace = dict(vars(M))
namespace.update(vars(L))
namespace.update(vars(P))
loader = PACKS.PackLoader(namespace)
pack_path = os.path.join(IMPORT_ROOT, "cat_theo_machine", "packs", "flt-quartic.pack.yaml")
pack = loader.load_pack_file(pack_path, graph)
obstruction_start, obstruction_goal = pack.examples["flt_e4_parity_obstruction"]
descent_start, descent_goal = pack.examples["flt_e4_quartic_descent"]

rule_count_pair = M.NatFromRep(M.CountRep(pack.rule_chain)(), registry)()
rule_count = M.Head(rule_count_pair)()
rule_count_reg = M.Head(M.Tail(rule_count_pair)())()
six_pair = M.NatFromRep(M.GMPRep("6"), rule_count_reg)()
six_nat = M.Head(six_pair)()
six_reg = M.Head(M.Tail(six_pair)())()
assert M.NatEq(rule_count, six_nat, six_reg)() is M.truth_value, "the pack must carry six rules"
print("    Pack loaded: six rules, two examples.")
print()

# --- [3] the sweep discovers the obstruction, the pack cites it -------------
print("[3] Grounding: W3 Cartesian sweep vs the pack's mod 4 observable...")
g_eleven_pair = M.NatFromRep(M.GMPRep("11"), registry)()
g_eleven = M.Head(g_eleven_pair)()
g_eleven_reg = M.Head(M.Tail(g_eleven_pair)())()
g_mod_four_pair = M.NatFromRep(M.GMPRep("4"), g_eleven_reg)()
g_mod_four = M.Head(g_mod_four_pair)()
g_mod_four_reg = M.Head(M.Tail(g_mod_four_pair)())()
g_sweep_pair = PG.RunPlaygroundCartesianSweep(g_eleven, g_mod_four, g_mod_four_reg)()
g_sweep = M.Head(g_sweep_pair)()
g_sweep_reg = M.Head(M.Tail(g_sweep_pair)())()
assert M.IdentityCompare(M.Head(g_sweep)(), L.DiscoveredInvariantLabel)() is M.truth_value, (
    "the sweep must report a discovered invariant"
)

g_square_image = M.Head(M.Tail(M.Tail(g_sweep)())())()
g_odd_image = M.Head(M.Tail(M.Tail(M.Tail(g_sweep)())())())()
g_images_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(g_sweep)())())())())()
assert g_images_disjoint is M.truth_value, "the sweep must find the two images disjoint"

g_zero_pair = M.NatFromRep(M.GMPRep("0"), g_sweep_reg)()
g_zero = M.Head(g_zero_pair)()
g_zero_reg = M.Head(M.Tail(g_zero_pair)())()
g_one_pair = M.NatFromRep(M.GMPRep("1"), g_zero_reg)()
g_one = M.Head(g_one_pair)()
g_one_reg = M.Head(M.Tail(g_one_pair)())()
g_two_pair = M.NatFromRep(M.GMPRep("2"), g_one_reg)()
g_two = M.Head(g_two_pair)()
g_two_reg = M.Head(M.Tail(g_two_pair)())()

assert M.IdentityCompare(M.Tail(M.Tail(g_square_image)())(), M.EmptyList)() is M.truth_value, (
    "the square image must hold exactly two residues"
)
g_square_first = M.Head(g_square_image)()
g_square_second = M.Head(M.Tail(g_square_image)())()
assert M.OrAtom(
    M.NatEq(g_square_first, g_zero, g_two_reg)(), M.NatEq(g_square_first, g_one, g_two_reg)()
)() is M.truth_value, "every square residue must be 0 or 1"
assert M.OrAtom(
    M.NatEq(g_square_second, g_zero, g_two_reg)(), M.NatEq(g_square_second, g_one, g_two_reg)()
)() is M.truth_value, "every square residue must be 0 or 1"
assert M.IdentityCompare(M.Tail(g_odd_image)(), M.EmptyList)() is M.truth_value, (
    "the odd sum image must hold exactly one residue"
)
g_odd_first = M.Head(g_odd_image)()
assert M.NatEq(g_odd_first, g_two, g_two_reg)() is M.truth_value, "the odd sum residue must be 2"
print("    Square image residue A:", M.GMPRepText(M.NatRepOf(g_square_first, g_two_reg)())())
print("    Square image residue B:", M.GMPRepText(M.NatRepOf(g_square_second, g_two_reg)())())
print("    Odd sum mod 4 residue:", M.GMPRepText(M.NatRepOf(g_odd_first, g_two_reg)())())
print("    Disjoint images:", g_images_disjoint is M.truth_value)

g_start_fact = M.Head(P.KnowledgeFacts(obstruction_start)())()
g_goal_fact = M.Head(P.KnowledgeFacts(obstruction_goal)())()
assert M.IdentityCompare(M.Head(g_start_fact)(), L.ParityMod4InvariantLabel)() is M.truth_value, (
    "the obstruction start must read the parity residue"
)
assert M.IdentityCompare(M.Head(g_goal_fact)(), L.ParityMod4InvariantLabel)() is M.truth_value, (
    "the obstruction goal must read the parity residue"
)
g_start_residue = M.Head(M.Tail(g_start_fact)())()
g_goal_residue = M.Head(M.Tail(g_goal_fact)())()
assert M.OrAtom(
    M.NatEq(g_start_residue, g_zero, g_two_reg)(), M.NatEq(g_start_residue, g_one, g_two_reg)()
)() is M.truth_value, "the start residue must be one the square image produces"
assert M.NatEq(g_goal_residue, g_two, g_two_reg)() is M.truth_value, (
    "the goal residue must be the odd sum residue"
)
assert M.AndAtom(
    M.NatEq(g_goal_residue, g_zero, g_two_reg)(), M.NatEq(g_goal_residue, g_one, g_two_reg)()
)() is M.false_value, "the goal residue must lie outside the square image"
print("    Start residue:", M.GMPRepText(M.NatRepOf(g_start_residue, g_two_reg)())())
print("    Goal residue:", M.GMPRepText(M.NatRepOf(g_goal_residue, g_two_reg)())())
print()

# --- [4] the obstruction route prunes with zero search ----------------------
print("[4] Obstruction: ReachabilityPrune with the residue invariant...")
o_carrier_rule = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(pack.rule_chain)())())())())()
o_carrier_chain = M.Pair(o_carrier_rule, M.EmptyList)
o_heuristic = H.Heuristic(M.DFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
o_phi = pack.phi
o_invariant = I.Invariant(o_phi, o_carrier_chain, registry, obstruction_start, o_carrier_chain)()
assert I.IsInvariant(o_invariant)() is M.truth_value, "the residue reading must be invariant"
assert I.PhiHolds(obstruction_start, o_phi)() is M.truth_value, "phi must hold on the start"
o_prune = I.ReachabilityPrune(obstruction_start, obstruction_goal, o_invariant, o_phi, registry)()
assert I.IsUnreachable(o_prune)() is M.truth_value, "the residue goal must be unreachable"

o_search_pair = I.SearchWithInvariant(
    graph, obstruction_start, obstruction_goal, o_carrier_chain, o_heuristic, registry, o_phi
)()
o_search_plan = M.Head(o_search_pair)()
o_search_cost = M.Head(M.Tail(o_search_pair)())()
o_search_prune = M.Head(M.Tail(M.Tail(o_search_pair)())())()
assert M.IdentityCompare(o_search_plan, M.EmptyList)() is M.truth_value, (
    "the pruned search must return no plan"
)
assert I.IsUnreachable(o_search_prune)() is M.truth_value, "the pruned search must report unreachable"
o_zero_pair = M.NatFromRep(M.GMPRep("0"), registry)()
o_zero = M.Head(o_zero_pair)()
o_zero_reg = M.Head(M.Tail(o_zero_pair)())()
assert M.NatEq(M.SearchCostExpanded(o_search_cost)(), o_zero, o_zero_reg)() is M.truth_value, (
    "the obstruction must be discharged with zero expansions"
)
print("    Plan empty; unreachable; expansions:",
      M.GMPRepText(M.NatRepOf(M.SearchCostExpanded(o_search_cost)(), o_zero_reg)())())
print("    Obstruction discharged without search.")
print()

# --- [5] the same route through the public prove entry point ---------------
print("[5] Obstruction through Prove(start, goal, rules, heuristic, registry, phi)...")
p_prove_pair = P.Prove(
    graph, obstruction_start, obstruction_goal, o_carrier_chain, o_heuristic, registry, o_phi
)()
p_prove_result = M.Head(p_prove_pair)()
assert I.IsUnreachable(p_prove_result)() is M.truth_value, (
    "Prove must return the unreachability record"
)
print("    Prove reports the residue goal unreachable.")
print()

# --- [6] negative control: equal readings never prune ----------------------
print("[6] Negative control: a goal with the same reading is not pruned...")
n_same_goal = P.Knowledge(
    M.Pair(M.Pair(L.ParityMod4InvariantLabel, M.Pair(M.one, M.EmptyList)), M.EmptyList)
)()
n_same_invariant = I.Invariant(o_phi, o_carrier_chain, registry, n_same_goal, o_carrier_chain)()
assert I.IsInvariant(n_same_invariant)() is M.truth_value, "the reading must stay invariant"
n_same_prune = I.ReachabilityPrune(obstruction_start, n_same_goal, n_same_invariant, o_phi, registry)()
assert I.IsUnreachable(n_same_prune)() is M.false_value, "equal readings must not prune"
print("    Same reading unreachable:",
      I.IsUnreachable(n_same_prune)() is M.truth_value)
print()

# --- [7] the descent route --------------------------------------------------
print("[7] Descent: five step derivation to NoSolution...")
d_t0 = time.time()
d_plan = I.RewriteSearch(descent_start, descent_goal, pack.rule_chain, registry)()
d_elapsed = time.time() - d_t0
assert M.IdentityCompare(d_plan, M.EmptyList)() is M.false_value, "the descent must produce a plan"
d_step_1 = M.Head(d_plan)()
d_step_2 = M.Head(M.Tail(d_plan)())()
d_step_3 = M.Head(M.Tail(M.Tail(d_plan)())())()
d_step_4 = M.Head(M.Tail(M.Tail(M.Tail(d_plan)())())())()
d_step_5 = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(d_plan)())())())())()
assert M.IdentityCompare(
    M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(d_plan)())())())())(), M.EmptyList
)() is M.truth_value, "the descent must be exactly five steps"
print("    Plan length:", M.GMPRepText(M.CountRep(d_plan)())())
print("    Rewrite search time: %.3fs" % d_elapsed)

d_derivation_pair = P.BuildDerivation(descent_start, d_plan, registry)()
d_derivation = M.Head(d_derivation_pair)()
d_replay_registry = M.Head(M.Tail(d_derivation_pair)())()
d_end_state = P.DerivationEnd(d_derivation, d_replay_registry)()
d_end_facts = P.KnowledgeFacts(d_end_state)()
assert P.FactsCover(P.KnowledgeFacts(descent_goal)(), d_end_facts)() is M.truth_value, (
    "the replay must cover the goal"
)
d_goal_fact = M.Head(P.KnowledgeFacts(descent_goal)())()
assert M.IdentityCompare(M.Head(d_goal_fact)(), L.NoSolutionLabel)() is M.truth_value, (
    "the goal must be the NoSolution fact"
)
print("    Replay covers the NoSolution goal.")

assert I.TermContains(
    P.RulePremises(P.ActionRule(d_step_5)())(), L.NoInfiniteDescentLabel
)() is M.truth_value, "the last step must cite well-foundedness"
assert I.TermContains(
    P.RulePremises(P.ActionRule(d_step_5)())(), L.NatLessLabel
)() is M.truth_value, "the last step must consume the strict decrease"
print("    Last step cites NoInfiniteDescent and NatLess.")
print()

# --- [8] negative control: no minimality, no descent -----------------------
print("[8] Negative control: without the minimal solution the descent stalls...")
c_fact_1 = M.Pair(
    L.QuarticSolutionLabel,
    M.Pair(M.Char("x"), M.Pair(M.Char("y"), M.Pair(M.Char("z"), M.EmptyList))),
)
c_fact_2 = M.Pair(L.CoprimeLabel, M.Pair(M.Char("x"), M.Pair(M.Char("y"), M.EmptyList)))
c_fact_3 = M.Pair(L.ParityLabel, M.Pair(M.Char("x"), M.Pair(L.OddLabel, M.EmptyList)))
c_fact_4 = M.Pair(L.ParityLabel, M.Pair(M.Char("y"), M.Pair(L.EvenLabel, M.EmptyList)))
c_fact_5 = M.Pair(L.NoInfiniteDescentLabel, M.Pair(M.Char("z"), M.EmptyList))
c_bare_start = P.Knowledge(
    M.Pair(c_fact_1, M.Pair(c_fact_2, M.Pair(c_fact_3, M.Pair(c_fact_4, M.Pair(c_fact_5, M.EmptyList)))))
)()
c_bare_plan = I.RewriteSearch(c_bare_start, descent_goal, pack.rule_chain, registry)()
assert M.IdentityCompare(c_bare_plan, M.EmptyList)() is M.truth_value, (
    "no minimal solution must yield no descent proof"
)
print("    No plan without MinimalSolution.")
print()

# --- [9] the algebra the named lemmas assert, checked on instances ---------
print("[9] Machine arithmetic on the parametrization and the relapse...")
# m^2 - n^2 and p^2 - q^2 are supplied as harness integers; every following
# identity and inequality is computed by the machine itself.
w1_m_pair = M.NatFromRep(M.GMPRep("2"), registry)()
w1_m = M.Head(w1_m_pair)()
w1_r1 = M.Head(M.Tail(w1_m_pair)())()
w1_n_pair = M.NatFromRep(M.GMPRep("1"), w1_r1)()
w1_n = M.Head(w1_n_pair)()
w1_r2 = M.Head(M.Tail(w1_n_pair)())()
w1_m_sq_pair = A.Multiply(w1_m, w1_m, w1_r2)()
w1_m_sq = M.Head(w1_m_sq_pair)()
w1_r3 = M.Head(M.Tail(w1_m_sq_pair)())()
w1_n_sq_pair = A.Multiply(w1_n, w1_n, w1_r3)()
w1_n_sq = M.Head(w1_n_sq_pair)()
w1_r4 = M.Head(M.Tail(w1_n_sq_pair)())()
w1_a_pair = M.NatFromRep(M.GMPRep("3"), w1_r4)()
w1_a = M.Head(w1_a_pair)()
w1_r5 = M.Head(M.Tail(w1_a_pair)())()
w1_plus_pair = A.Add(w1_m, w1_n, w1_r5)()
w1_plus = M.Head(w1_plus_pair)()
w1_r6 = M.Head(M.Tail(w1_plus_pair)())()
w1_minus_pair = M.NatFromRep(M.GMPRep("1"), w1_r6)()
w1_minus = M.Head(w1_minus_pair)()
w1_r7 = M.Head(M.Tail(w1_minus_pair)())()
w1_factored_pair = A.Multiply(w1_minus, w1_plus, w1_r7)()
w1_factored = M.Head(w1_factored_pair)()
w1_r8 = M.Head(M.Tail(w1_factored_pair)())()
assert M.NatEq(w1_factored, w1_a, w1_r8)() is M.truth_value, "(m-n)(m+n) != m^2-n^2 for (2, 1)"
assert A.IsCoprime(w1_minus, w1_plus, w1_r8)() is M.truth_value, "coprime factors failed for (2, 1)"
w1_two_pair = M.NatFromRep(M.GMPRep("2"), w1_r8)()
w1_two = M.Head(w1_two_pair)()
w1_r9 = M.Head(M.Tail(w1_two_pair)())()
w1_mn_pair = A.Multiply(w1_m, w1_n, w1_r9)()
w1_mn = M.Head(w1_mn_pair)()
w1_r10 = M.Head(M.Tail(w1_mn_pair)())()
w1_b_pair = A.Multiply(w1_two, w1_mn, w1_r10)()
w1_b = M.Head(w1_b_pair)()
w1_r11 = M.Head(M.Tail(w1_b_pair)())()
w1_c_pair = A.Add(w1_m_sq, w1_n_sq, w1_r11)()
w1_c = M.Head(w1_c_pair)()
w1_r12 = M.Head(M.Tail(w1_c_pair)())()
w1_a_sq_pair = A.Multiply(w1_a, w1_a, w1_r12)()
w1_a_sq = M.Head(w1_a_sq_pair)()
w1_r13 = M.Head(M.Tail(w1_a_sq_pair)())()
w1_b_sq_pair = A.Multiply(w1_b, w1_b, w1_r13)()
w1_b_sq = M.Head(w1_b_sq_pair)()
w1_r14 = M.Head(M.Tail(w1_b_sq_pair)())()
w1_c_sq_pair = A.Multiply(w1_c, w1_c, w1_r14)()
w1_c_sq = M.Head(w1_c_sq_pair)()
w1_r15 = M.Head(M.Tail(w1_c_sq_pair)())()
w1_lhs_pair = A.Add(w1_a_sq, w1_b_sq, w1_r15)()
w1_lhs = M.Head(w1_lhs_pair)()
w1_r16 = M.Head(M.Tail(w1_lhs_pair)())()
assert M.NatEq(w1_lhs, w1_c_sq, w1_r16)() is M.truth_value, "a^2 + b^2 != c^2 for (2, 1)"

w2_m_pair = M.NatFromRep(M.GMPRep("3"), registry)()
w2_m = M.Head(w2_m_pair)()
w2_r1 = M.Head(M.Tail(w2_m_pair)())()
w2_n_pair = M.NatFromRep(M.GMPRep("2"), w2_r1)()
w2_n = M.Head(w2_n_pair)()
w2_r2 = M.Head(M.Tail(w2_n_pair)())()
w2_m_sq_pair = A.Multiply(w2_m, w2_m, w2_r2)()
w2_m_sq = M.Head(w2_m_sq_pair)()
w2_r3 = M.Head(M.Tail(w2_m_sq_pair)())()
w2_n_sq_pair = A.Multiply(w2_n, w2_n, w2_r3)()
w2_n_sq = M.Head(w2_n_sq_pair)()
w2_r4 = M.Head(M.Tail(w2_n_sq_pair)())()
w2_a_pair = M.NatFromRep(M.GMPRep("5"), w2_r4)()
w2_a = M.Head(w2_a_pair)()
w2_r5 = M.Head(M.Tail(w2_a_pair)())()
w2_plus_pair = A.Add(w2_m, w2_n, w2_r5)()
w2_plus = M.Head(w2_plus_pair)()
w2_r6 = M.Head(M.Tail(w2_plus_pair)())()
w2_minus_pair = M.NatFromRep(M.GMPRep("1"), w2_r6)()
w2_minus = M.Head(w2_minus_pair)()
w2_r7 = M.Head(M.Tail(w2_minus_pair)())()
w2_factored_pair = A.Multiply(w2_minus, w2_plus, w2_r7)()
w2_factored = M.Head(w2_factored_pair)()
w2_r8 = M.Head(M.Tail(w2_factored_pair)())()
assert M.NatEq(w2_factored, w2_a, w2_r8)() is M.truth_value, "(m-n)(m+n) != m^2-n^2 for (3, 2)"
assert A.IsCoprime(w2_minus, w2_plus, w2_r8)() is M.truth_value, "coprime factors failed for (3, 2)"
w2_two_pair = M.NatFromRep(M.GMPRep("2"), w2_r8)()
w2_two = M.Head(w2_two_pair)()
w2_r9 = M.Head(M.Tail(w2_two_pair)())()
w2_mn_pair = A.Multiply(w2_m, w2_n, w2_r9)()
w2_mn = M.Head(w2_mn_pair)()
w2_r10 = M.Head(M.Tail(w2_mn_pair)())()
w2_b_pair = A.Multiply(w2_two, w2_mn, w2_r10)()
w2_b = M.Head(w2_b_pair)()
w2_r11 = M.Head(M.Tail(w2_b_pair)())()
w2_c_pair = A.Add(w2_m_sq, w2_n_sq, w2_r11)()
w2_c = M.Head(w2_c_pair)()
w2_r12 = M.Head(M.Tail(w2_c_pair)())()
w2_a_sq_pair = A.Multiply(w2_a, w2_a, w2_r12)()
w2_a_sq = M.Head(w2_a_sq_pair)()
w2_r13 = M.Head(M.Tail(w2_a_sq_pair)())()
w2_b_sq_pair = A.Multiply(w2_b, w2_b, w2_r13)()
w2_b_sq = M.Head(w2_b_sq_pair)()
w2_r14 = M.Head(M.Tail(w2_b_sq_pair)())()
w2_c_sq_pair = A.Multiply(w2_c, w2_c, w2_r14)()
w2_c_sq = M.Head(w2_c_sq_pair)()
w2_r15 = M.Head(M.Tail(w2_c_sq_pair)())()
w2_lhs_pair = A.Add(w2_a_sq, w2_b_sq, w2_r15)()
w2_lhs = M.Head(w2_lhs_pair)()
w2_r16 = M.Head(M.Tail(w2_lhs_pair)())()
assert M.NatEq(w2_lhs, w2_c_sq, w2_r16)() is M.truth_value, "a^2 + b^2 != c^2 for (3, 2)"

w3_m_pair = M.NatFromRep(M.GMPRep("6"), registry)()
w3_m = M.Head(w3_m_pair)()
w3_r1 = M.Head(M.Tail(w3_m_pair)())()
w3_n_pair = M.NatFromRep(M.GMPRep("1"), w3_r1)()
w3_n = M.Head(w3_n_pair)()
w3_r2 = M.Head(M.Tail(w3_n_pair)())()
w3_m_sq_pair = A.Multiply(w3_m, w3_m, w3_r2)()
w3_m_sq = M.Head(w3_m_sq_pair)()
w3_r3 = M.Head(M.Tail(w3_m_sq_pair)())()
w3_n_sq_pair = A.Multiply(w3_n, w3_n, w3_r3)()
w3_n_sq = M.Head(w3_n_sq_pair)()
w3_r4 = M.Head(M.Tail(w3_n_sq_pair)())()
w3_a_pair = M.NatFromRep(M.GMPRep("35"), w3_r4)()
w3_a = M.Head(w3_a_pair)()
w3_r5 = M.Head(M.Tail(w3_a_pair)())()
w3_plus_pair = A.Add(w3_m, w3_n, w3_r5)()
w3_plus = M.Head(w3_plus_pair)()
w3_r6 = M.Head(M.Tail(w3_plus_pair)())()
w3_minus_pair = M.NatFromRep(M.GMPRep("5"), w3_r6)()
w3_minus = M.Head(w3_minus_pair)()
w3_r7 = M.Head(M.Tail(w3_minus_pair)())()
w3_factored_pair = A.Multiply(w3_minus, w3_plus, w3_r7)()
w3_factored = M.Head(w3_factored_pair)()
w3_r8 = M.Head(M.Tail(w3_factored_pair)())()
assert M.NatEq(w3_factored, w3_a, w3_r8)() is M.truth_value, "(m-n)(m+n) != m^2-n^2 for (6, 1)"
assert A.IsCoprime(w3_minus, w3_plus, w3_r8)() is M.truth_value, "coprime factors failed for (6, 1)"
w3_two_pair = M.NatFromRep(M.GMPRep("2"), w3_r8)()
w3_two = M.Head(w3_two_pair)()
w3_r9 = M.Head(M.Tail(w3_two_pair)())()
w3_mn_pair = A.Multiply(w3_m, w3_n, w3_r9)()
w3_mn = M.Head(w3_mn_pair)()
w3_r10 = M.Head(M.Tail(w3_mn_pair)())()
w3_b_pair = A.Multiply(w3_two, w3_mn, w3_r10)()
w3_b = M.Head(w3_b_pair)()
w3_r11 = M.Head(M.Tail(w3_b_pair)())()
w3_c_pair = A.Add(w3_m_sq, w3_n_sq, w3_r11)()
w3_c = M.Head(w3_c_pair)()
w3_r12 = M.Head(M.Tail(w3_c_pair)())()
w3_a_sq_pair = A.Multiply(w3_a, w3_a, w3_r12)()
w3_a_sq = M.Head(w3_a_sq_pair)()
w3_r13 = M.Head(M.Tail(w3_a_sq_pair)())()
w3_b_sq_pair = A.Multiply(w3_b, w3_b, w3_r13)()
w3_b_sq = M.Head(w3_b_sq_pair)()
w3_r14 = M.Head(M.Tail(w3_b_sq_pair)())()
w3_c_sq_pair = A.Multiply(w3_c, w3_c, w3_r14)()
w3_c_sq = M.Head(w3_c_sq_pair)()
w3_r15 = M.Head(M.Tail(w3_c_sq_pair)())()
w3_lhs_pair = A.Add(w3_a_sq, w3_b_sq, w3_r15)()
w3_lhs = M.Head(w3_lhs_pair)()
w3_r16 = M.Head(M.Tail(w3_lhs_pair)())()
assert M.NatEq(w3_lhs, w3_c_sq, w3_r16)() is M.truth_value, "a^2 + b^2 != c^2 for (6, 1)"
print("    Parametrization, coprime factors, and a^2 + b^2 = c^2 on (2, 1), (3, 2), (6, 1).")

q1_p_pair = M.NatFromRep(M.GMPRep("2"), registry)()
q1_p = M.Head(q1_p_pair)()
q1_r1 = M.Head(M.Tail(q1_p_pair)())()
q1_q_pair = M.NatFromRep(M.GMPRep("1"), q1_r1)()
q1_q = M.Head(q1_q_pair)()
q1_r2 = M.Head(M.Tail(q1_q_pair)())()
q1_p_sq_pair = A.Multiply(q1_p, q1_p, q1_r2)()
q1_p_sq = M.Head(q1_p_sq_pair)()
q1_r3 = M.Head(M.Tail(q1_p_sq_pair)())()
q1_q_sq_pair = A.Multiply(q1_q, q1_q, q1_r3)()
q1_q_sq = M.Head(q1_q_sq_pair)()
q1_r4 = M.Head(M.Tail(q1_q_sq_pair)())()
q1_p4_pair = A.Multiply(q1_p_sq, q1_p_sq, q1_r4)()
q1_p4 = M.Head(q1_p4_pair)()
q1_r5 = M.Head(M.Tail(q1_p4_pair)())()
q1_q4_pair = A.Multiply(q1_q_sq, q1_q_sq, q1_r5)()
q1_q4 = M.Head(q1_q4_pair)()
q1_r6 = M.Head(M.Tail(q1_q4_pair)())()
q1_s_pair = M.NatFromRep(M.GMPRep("3"), q1_r6)()
q1_s = M.Head(q1_s_pair)()
q1_r7 = M.Head(M.Tail(q1_s_pair)())()
q1_r_pair = A.Add(q1_p_sq, q1_q_sq, q1_r7)()
q1_r = M.Head(q1_r_pair)()
q1_r8 = M.Head(M.Tail(q1_r_pair)())()
q1_s_sq_pair = A.Multiply(q1_s, q1_s, q1_r8)()
q1_s_sq = M.Head(q1_s_sq_pair)()
q1_r9 = M.Head(M.Tail(q1_s_sq_pair)())()
q1_r_sq_pair = A.Multiply(q1_r, q1_r, q1_r9)()
q1_r_sq = M.Head(q1_r_sq_pair)()
q1_r10 = M.Head(M.Tail(q1_r_sq_pair)())()
q1_u_sq_pair = A.Add(q1_p4, q1_q4, q1_r10)()
q1_u_sq = M.Head(q1_u_sq_pair)()
q1_r11 = M.Head(M.Tail(q1_u_sq_pair)())()
q1_sum_pair = A.Add(q1_r_sq, q1_s_sq, q1_r11)()
q1_sum = M.Head(q1_sum_pair)()
q1_r12 = M.Head(M.Tail(q1_sum_pair)())()
q1_two_pair = M.NatFromRep(M.GMPRep("2"), q1_r12)()
q1_two = M.Head(q1_two_pair)()
q1_r13 = M.Head(M.Tail(q1_two_pair)())()
q1_twice_u_pair = A.Multiply(q1_two, q1_u_sq, q1_r13)()
q1_twice_u = M.Head(q1_twice_u_pair)()
q1_r14 = M.Head(M.Tail(q1_twice_u_pair)())()
assert M.NatEq(q1_sum, q1_twice_u, q1_r14)() is M.truth_value, "r^2 + s^2 != 2u^2 for (2, 1)"
q1_four_pair = M.NatFromRep(M.GMPRep("4"), q1_r14)()
q1_four = M.Head(q1_four_pair)()
q1_r15 = M.Head(M.Tail(q1_four_pair)())()
q1_pq_pair = A.Multiply(q1_p, q1_q, q1_r15)()
q1_pq = M.Head(q1_pq_pair)()
q1_r16 = M.Head(M.Tail(q1_pq_pair)())()
q1_pq_sq_pair = A.Multiply(q1_pq, q1_pq, q1_r16)()
q1_pq_sq = M.Head(q1_pq_sq_pair)()
q1_r17 = M.Head(M.Tail(q1_pq_sq_pair)())()
q1_four_pq_sq_pair = A.Multiply(q1_four, q1_pq_sq, q1_r17)()
q1_four_pq_sq = M.Head(q1_four_pq_sq_pair)()
q1_r18 = M.Head(M.Tail(q1_four_pq_sq_pair)())()
q1_s_sq_plus_pair = A.Add(q1_s_sq, q1_four_pq_sq, q1_r18)()
q1_s_sq_plus = M.Head(q1_s_sq_plus_pair)()
q1_r19 = M.Head(M.Tail(q1_s_sq_plus_pair)())()
assert M.NatEq(q1_r_sq, q1_s_sq_plus, q1_r19)() is M.truth_value, "r^2 != s^2 + 4p^2q^2 for (2, 1)"
q1_u4_pair = A.Multiply(q1_u_sq, q1_u_sq, q1_r19)()
q1_u4 = M.Head(q1_u4_pair)()
q1_r20 = M.Head(M.Tail(q1_u4_pair)())()
q1_p4q4_pair = A.Multiply(q1_p4, q1_q4, q1_r20)()
q1_p4q4 = M.Head(q1_p4q4_pair)()
q1_r21 = M.Head(M.Tail(q1_p4q4_pair)())()
q1_four_p4q4_pair = A.Multiply(q1_four, q1_p4q4, q1_r21)()
q1_four_p4q4 = M.Head(q1_four_p4q4_pair)()
q1_r22 = M.Head(M.Tail(q1_four_p4q4_pair)())()
q1_z_pair = A.Add(q1_u4, q1_four_p4q4, q1_r22)()
q1_z = M.Head(q1_z_pair)()
q1_r23 = M.Head(M.Tail(q1_z_pair)())()
assert M.NatLess(q1_u_sq, q1_z, q1_r23)() is M.truth_value, "strict decrease failed for (2, 1)"

q2_p_pair = M.NatFromRep(M.GMPRep("3"), registry)()
q2_p = M.Head(q2_p_pair)()
q2_r1 = M.Head(M.Tail(q2_p_pair)())()
q2_q_pair = M.NatFromRep(M.GMPRep("2"), q2_r1)()
q2_q = M.Head(q2_q_pair)()
q2_r2 = M.Head(M.Tail(q2_q_pair)())()
q2_p_sq_pair = A.Multiply(q2_p, q2_p, q2_r2)()
q2_p_sq = M.Head(q2_p_sq_pair)()
q2_r3 = M.Head(M.Tail(q2_p_sq_pair)())()
q2_q_sq_pair = A.Multiply(q2_q, q2_q, q2_r3)()
q2_q_sq = M.Head(q2_q_sq_pair)()
q2_r4 = M.Head(M.Tail(q2_q_sq_pair)())()
q2_p4_pair = A.Multiply(q2_p_sq, q2_p_sq, q2_r4)()
q2_p4 = M.Head(q2_p4_pair)()
q2_r5 = M.Head(M.Tail(q2_p4_pair)())()
q2_q4_pair = A.Multiply(q2_q_sq, q2_q_sq, q2_r5)()
q2_q4 = M.Head(q2_q4_pair)()
q2_r6 = M.Head(M.Tail(q2_q4_pair)())()
q2_s_pair = M.NatFromRep(M.GMPRep("5"), q2_r6)()
q2_s = M.Head(q2_s_pair)()
q2_r7 = M.Head(M.Tail(q2_s_pair)())()
q2_r_pair = A.Add(q2_p_sq, q2_q_sq, q2_r7)()
q2_r = M.Head(q2_r_pair)()
q2_r8 = M.Head(M.Tail(q2_r_pair)())()
q2_s_sq_pair = A.Multiply(q2_s, q2_s, q2_r8)()
q2_s_sq = M.Head(q2_s_sq_pair)()
q2_r9 = M.Head(M.Tail(q2_s_sq_pair)())()
q2_r_sq_pair = A.Multiply(q2_r, q2_r, q2_r9)()
q2_r_sq = M.Head(q2_r_sq_pair)()
q2_r10 = M.Head(M.Tail(q2_r_sq_pair)())()
q2_u_sq_pair = A.Add(q2_p4, q2_q4, q2_r10)()
q2_u_sq = M.Head(q2_u_sq_pair)()
q2_r11 = M.Head(M.Tail(q2_u_sq_pair)())()
q2_sum_pair = A.Add(q2_r_sq, q2_s_sq, q2_r11)()
q2_sum = M.Head(q2_sum_pair)()
q2_r12 = M.Head(M.Tail(q2_sum_pair)())()
q2_two_pair = M.NatFromRep(M.GMPRep("2"), q2_r12)()
q2_two = M.Head(q2_two_pair)()
q2_r13 = M.Head(M.Tail(q2_two_pair)())()
q2_twice_u_pair = A.Multiply(q2_two, q2_u_sq, q2_r13)()
q2_twice_u = M.Head(q2_twice_u_pair)()
q2_r14 = M.Head(M.Tail(q2_twice_u_pair)())()
assert M.NatEq(q2_sum, q2_twice_u, q2_r14)() is M.truth_value, "r^2 + s^2 != 2u^2 for (3, 2)"
q2_four_pair = M.NatFromRep(M.GMPRep("4"), q2_r14)()
q2_four = M.Head(q2_four_pair)()
q2_r15 = M.Head(M.Tail(q2_four_pair)())()
q2_pq_pair = A.Multiply(q2_p, q2_q, q2_r15)()
q2_pq = M.Head(q2_pq_pair)()
q2_r16 = M.Head(M.Tail(q2_pq_pair)())()
q2_pq_sq_pair = A.Multiply(q2_pq, q2_pq, q2_r16)()
q2_pq_sq = M.Head(q2_pq_sq_pair)()
q2_r17 = M.Head(M.Tail(q2_pq_sq_pair)())()
q2_four_pq_sq_pair = A.Multiply(q2_four, q2_pq_sq, q2_r17)()
q2_four_pq_sq = M.Head(q2_four_pq_sq_pair)()
q2_r18 = M.Head(M.Tail(q2_four_pq_sq_pair)())()
q2_s_sq_plus_pair = A.Add(q2_s_sq, q2_four_pq_sq, q2_r18)()
q2_s_sq_plus = M.Head(q2_s_sq_plus_pair)()
q2_r19 = M.Head(M.Tail(q2_s_sq_plus_pair)())()
assert M.NatEq(q2_r_sq, q2_s_sq_plus, q2_r19)() is M.truth_value, "r^2 != s^2 + 4p^2q^2 for (3, 2)"
q2_u4_pair = A.Multiply(q2_u_sq, q2_u_sq, q2_r19)()
q2_u4 = M.Head(q2_u4_pair)()
q2_r20 = M.Head(M.Tail(q2_u4_pair)())()
q2_p4q4_pair = A.Multiply(q2_p4, q2_q4, q2_r20)()
q2_p4q4 = M.Head(q2_p4q4_pair)()
q2_r21 = M.Head(M.Tail(q2_p4q4_pair)())()
q2_four_p4q4_pair = A.Multiply(q2_four, q2_p4q4, q2_r21)()
q2_four_p4q4 = M.Head(q2_four_p4q4_pair)()
q2_r22 = M.Head(M.Tail(q2_four_p4q4_pair)())()
q2_z_pair = A.Add(q2_u4, q2_four_p4q4, q2_r22)()
q2_z = M.Head(q2_z_pair)()
q2_r23 = M.Head(M.Tail(q2_z_pair)())()
assert M.NatLess(q2_u_sq, q2_z, q2_r23)() is M.truth_value, "strict decrease failed for (3, 2)"

q3_p_pair = M.NatFromRep(M.GMPRep("7"), registry)()
q3_p = M.Head(q3_p_pair)()
q3_r1 = M.Head(M.Tail(q3_p_pair)())()
q3_q_pair = M.NatFromRep(M.GMPRep("2"), q3_r1)()
q3_q = M.Head(q3_q_pair)()
q3_r2 = M.Head(M.Tail(q3_q_pair)())()
q3_p_sq_pair = A.Multiply(q3_p, q3_p, q3_r2)()
q3_p_sq = M.Head(q3_p_sq_pair)()
q3_r3 = M.Head(M.Tail(q3_p_sq_pair)())()
q3_q_sq_pair = A.Multiply(q3_q, q3_q, q3_r3)()
q3_q_sq = M.Head(q3_q_sq_pair)()
q3_r4 = M.Head(M.Tail(q3_q_sq_pair)())()
q3_p4_pair = A.Multiply(q3_p_sq, q3_p_sq, q3_r4)()
q3_p4 = M.Head(q3_p4_pair)()
q3_r5 = M.Head(M.Tail(q3_p4_pair)())()
q3_q4_pair = A.Multiply(q3_q_sq, q3_q_sq, q3_r5)()
q3_q4 = M.Head(q3_q4_pair)()
q3_r6 = M.Head(M.Tail(q3_q4_pair)())()
q3_s_pair = M.NatFromRep(M.GMPRep("45"), q3_r6)()
q3_s = M.Head(q3_s_pair)()
q3_r7 = M.Head(M.Tail(q3_s_pair)())()
q3_r_pair = A.Add(q3_p_sq, q3_q_sq, q3_r7)()
q3_r = M.Head(q3_r_pair)()
q3_r8 = M.Head(M.Tail(q3_r_pair)())()
q3_s_sq_pair = A.Multiply(q3_s, q3_s, q3_r8)()
q3_s_sq = M.Head(q3_s_sq_pair)()
q3_r9 = M.Head(M.Tail(q3_s_sq_pair)())()
q3_r_sq_pair = A.Multiply(q3_r, q3_r, q3_r9)()
q3_r_sq = M.Head(q3_r_sq_pair)()
q3_r10 = M.Head(M.Tail(q3_r_sq_pair)())()
q3_u_sq_pair = A.Add(q3_p4, q3_q4, q3_r10)()
q3_u_sq = M.Head(q3_u_sq_pair)()
q3_r11 = M.Head(M.Tail(q3_u_sq_pair)())()
q3_sum_pair = A.Add(q3_r_sq, q3_s_sq, q3_r11)()
q3_sum = M.Head(q3_sum_pair)()
q3_r12 = M.Head(M.Tail(q3_sum_pair)())()
q3_two_pair = M.NatFromRep(M.GMPRep("2"), q3_r12)()
q3_two = M.Head(q3_two_pair)()
q3_r13 = M.Head(M.Tail(q3_two_pair)())()
q3_twice_u_pair = A.Multiply(q3_two, q3_u_sq, q3_r13)()
q3_twice_u = M.Head(q3_twice_u_pair)()
q3_r14 = M.Head(M.Tail(q3_twice_u_pair)())()
assert M.NatEq(q3_sum, q3_twice_u, q3_r14)() is M.truth_value, "r^2 + s^2 != 2u^2 for (7, 2)"
q3_four_pair = M.NatFromRep(M.GMPRep("4"), q3_r14)()
q3_four = M.Head(q3_four_pair)()
q3_r15 = M.Head(M.Tail(q3_four_pair)())()
q3_pq_pair = A.Multiply(q3_p, q3_q, q3_r15)()
q3_pq = M.Head(q3_pq_pair)()
q3_r16 = M.Head(M.Tail(q3_pq_pair)())()
q3_pq_sq_pair = A.Multiply(q3_pq, q3_pq, q3_r16)()
q3_pq_sq = M.Head(q3_pq_sq_pair)()
q3_r17 = M.Head(M.Tail(q3_pq_sq_pair)())()
q3_four_pq_sq_pair = A.Multiply(q3_four, q3_pq_sq, q3_r17)()
q3_four_pq_sq = M.Head(q3_four_pq_sq_pair)()
q3_r18 = M.Head(M.Tail(q3_four_pq_sq_pair)())()
q3_s_sq_plus_pair = A.Add(q3_s_sq, q3_four_pq_sq, q3_r18)()
q3_s_sq_plus = M.Head(q3_s_sq_plus_pair)()
q3_r19 = M.Head(M.Tail(q3_s_sq_plus_pair)())()
assert M.NatEq(q3_r_sq, q3_s_sq_plus, q3_r19)() is M.truth_value, "r^2 != s^2 + 4p^2q^2 for (7, 2)"
q3_u4_pair = A.Multiply(q3_u_sq, q3_u_sq, q3_r19)()
q3_u4 = M.Head(q3_u4_pair)()
q3_r20 = M.Head(M.Tail(q3_u4_pair)())()
q3_p4q4_pair = A.Multiply(q3_p4, q3_q4, q3_r20)()
q3_p4q4 = M.Head(q3_p4q4_pair)()
q3_r21 = M.Head(M.Tail(q3_p4q4_pair)())()
q3_four_p4q4_pair = A.Multiply(q3_four, q3_p4q4, q3_r21)()
q3_four_p4q4 = M.Head(q3_four_p4q4_pair)()
q3_r22 = M.Head(M.Tail(q3_four_p4q4_pair)())()
q3_z_pair = A.Add(q3_u4, q3_four_p4q4, q3_r22)()
q3_z = M.Head(q3_z_pair)()
q3_r23 = M.Head(M.Tail(q3_z_pair)())()
assert M.NatLess(q3_u_sq, q3_z, q3_r23)() is M.truth_value, "strict decrease failed for (7, 2)"
print("    Relapse identities and strict decrease on (2, 1), (3, 2), (7, 2).")

de_two_pair = M.NatFromRep(M.GMPRep("2"), registry)()
de_two = M.Head(de_two_pair)()
de_r1 = M.Head(M.Tail(de_two_pair)())()
de_two_sq_pair = A.Multiply(de_two, de_two, de_r1)()
de_two_sq = M.Head(de_two_sq_pair)()
de_r2 = M.Head(M.Tail(de_two_sq_pair)())()
assert M.NatLess(de_two, de_two_sq, de_r2)() is M.truth_value, "u < u^2 failed for u = 2"
de_three_pair = M.NatFromRep(M.GMPRep("3"), registry)()
de_three = M.Head(de_three_pair)()
de_r3 = M.Head(M.Tail(de_three_pair)())()
de_three_sq_pair = A.Multiply(de_three, de_three, de_r3)()
de_three_sq = M.Head(de_three_sq_pair)()
de_r4 = M.Head(M.Tail(de_three_sq_pair)())()
assert M.NatLess(de_three, de_three_sq, de_r4)() is M.truth_value, "u < u^2 failed for u = 3"
de_four_pair = M.NatFromRep(M.GMPRep("4"), registry)()
de_four = M.Head(de_four_pair)()
de_r5 = M.Head(M.Tail(de_four_pair)())()
de_four_sq_pair = A.Multiply(de_four, de_four, de_r5)()
de_four_sq = M.Head(de_four_sq_pair)()
de_r6 = M.Head(M.Tail(de_four_sq_pair)())()
assert M.NatLess(de_four, de_four_sq, de_r6)() is M.truth_value, "u < u^2 failed for u = 4"
print("    u < u^2 verified for u = 2, 3, 4.")

sq_x0_pair = M.NatFromRep(M.GMPRep("0"), registry)()
sq_x0 = M.Head(sq_x0_pair)()
sq_r1 = M.Head(M.Tail(sq_x0_pair)())()
sq_four_pair = M.NatFromRep(M.GMPRep("4"), sq_r1)()
sq_four = M.Head(sq_four_pair)()
sq_r2 = M.Head(M.Tail(sq_four_pair)())()
sq_x0_sq_pair = A.Multiply(sq_x0, sq_x0, sq_r2)()
sq_x0_sq = M.Head(sq_x0_sq_pair)()
sq_r3 = M.Head(M.Tail(sq_x0_sq_pair)())()
sq_x0_rem_pair = A.Modulo(sq_x0_sq, sq_four, sq_r3)()
sq_x0_rem = M.Head(sq_x0_rem_pair)()
sq_r4 = M.Head(M.Tail(sq_x0_rem_pair)())()
sq_zero_pair = M.NatFromRep(M.GMPRep("0"), sq_r4)()
sq_zero = M.Head(sq_zero_pair)()
sq_r5 = M.Head(M.Tail(sq_zero_pair)())()
assert M.NatEq(sq_x0_rem, sq_zero, sq_r5)() is M.truth_value, "0^2 mod 4 != 0"

sq_x1_pair = M.NatFromRep(M.GMPRep("1"), registry)()
sq_x1 = M.Head(sq_x1_pair)()
sq_r6 = M.Head(M.Tail(sq_x1_pair)())()
sq_x1_sq_pair = A.Multiply(sq_x1, sq_x1, sq_r6)()
sq_x1_sq = M.Head(sq_x1_sq_pair)()
sq_r7 = M.Head(M.Tail(sq_x1_sq_pair)())()
sq_x1_rem_pair = A.Modulo(sq_x1_sq, sq_four, sq_r7)()
sq_x1_rem = M.Head(sq_x1_rem_pair)()
sq_r8 = M.Head(M.Tail(sq_x1_rem_pair)())()
sq_one_pair = M.NatFromRep(M.GMPRep("1"), sq_r8)()
sq_one = M.Head(sq_one_pair)()
sq_r9 = M.Head(M.Tail(sq_one_pair)())()
assert M.NatEq(sq_x1_rem, sq_one, sq_r9)() is M.truth_value, "1^2 mod 4 != 1"

sq_x2_pair = M.NatFromRep(M.GMPRep("2"), registry)()
sq_x2 = M.Head(sq_x2_pair)()
sq_r10 = M.Head(M.Tail(sq_x2_pair)())()
sq_x2_sq_pair = A.Multiply(sq_x2, sq_x2, sq_r10)()
sq_x2_sq = M.Head(sq_x2_sq_pair)()
sq_r11 = M.Head(M.Tail(sq_x2_sq_pair)())()
sq_x2_rem_pair = A.Modulo(sq_x2_sq, sq_four, sq_r11)()
sq_x2_rem = M.Head(sq_x2_rem_pair)()
sq_r12 = M.Head(M.Tail(sq_x2_rem_pair)())()
assert M.NatEq(sq_x2_rem, sq_zero, sq_r12)() is M.truth_value, "2^2 mod 4 != 0"

sq_x3_pair = M.NatFromRep(M.GMPRep("3"), registry)()
sq_x3 = M.Head(sq_x3_pair)()
sq_r13 = M.Head(M.Tail(sq_x3_pair)())()
sq_x3_sq_pair = A.Multiply(sq_x3, sq_x3, sq_r13)()
sq_x3_sq = M.Head(sq_x3_sq_pair)()
sq_r14 = M.Head(M.Tail(sq_x3_sq_pair)())()
sq_x3_rem_pair = A.Modulo(sq_x3_sq, sq_four, sq_r14)()
sq_x3_rem = M.Head(sq_x3_rem_pair)()
sq_r15 = M.Head(M.Tail(sq_x3_rem_pair)())()
assert M.NatEq(sq_x3_rem, sq_one, sq_r15)() is M.truth_value, "3^2 mod 4 != 1"
print("    Squares mod 4 in {0, 1} for x = 0, 1, 2, 3.")

fp_x1_pair = M.NatFromRep(M.GMPRep("1"), registry)()
fp_x1 = M.Head(fp_x1_pair)()
fp_r1 = M.Head(M.Tail(fp_x1_pair)())()
fp_sixteen_pair = M.NatFromRep(M.GMPRep("16"), fp_r1)()
fp_sixteen = M.Head(fp_sixteen_pair)()
fp_r2 = M.Head(M.Tail(fp_sixteen_pair)())()
fp_x1_sq_pair = A.Multiply(fp_x1, fp_x1, fp_r2)()
fp_x1_sq = M.Head(fp_x1_sq_pair)()
fp_r3 = M.Head(M.Tail(fp_x1_sq_pair)())()
fp_x1_fourth_pair = A.Multiply(fp_x1_sq, fp_x1_sq, fp_r3)()
fp_x1_fourth = M.Head(fp_x1_fourth_pair)()
fp_r4 = M.Head(M.Tail(fp_x1_fourth_pair)())()
fp_x1_rem_pair = A.Modulo(fp_x1_fourth, fp_sixteen, fp_r4)()
fp_x1_rem = M.Head(fp_x1_rem_pair)()
fp_r5 = M.Head(M.Tail(fp_x1_rem_pair)())()
fp_one_pair = M.NatFromRep(M.GMPRep("1"), fp_r5)()
fp_one = M.Head(fp_one_pair)()
fp_r6 = M.Head(M.Tail(fp_one_pair)())()
assert M.NatEq(fp_x1_rem, fp_one, fp_r6)() is M.truth_value, "1^4 mod 16 != 1"

fp_x3_pair = M.NatFromRep(M.GMPRep("3"), registry)()
fp_x3 = M.Head(fp_x3_pair)()
fp_r7 = M.Head(M.Tail(fp_x3_pair)())()
fp_x3_sq_pair = A.Multiply(fp_x3, fp_x3, fp_r7)()
fp_x3_sq = M.Head(fp_x3_sq_pair)()
fp_r8 = M.Head(M.Tail(fp_x3_sq_pair)())()
fp_x3_fourth_pair = A.Multiply(fp_x3_sq, fp_x3_sq, fp_r8)()
fp_x3_fourth = M.Head(fp_x3_fourth_pair)()
fp_r9 = M.Head(M.Tail(fp_x3_fourth_pair)())()
fp_x3_rem_pair = A.Modulo(fp_x3_fourth, fp_sixteen, fp_r9)()
fp_x3_rem = M.Head(fp_x3_rem_pair)()
fp_r10 = M.Head(M.Tail(fp_x3_rem_pair)())()
assert M.NatEq(fp_x3_rem, fp_one, fp_r10)() is M.truth_value, "3^4 mod 16 != 1"

fp_x5_pair = M.NatFromRep(M.GMPRep("5"), registry)()
fp_x5 = M.Head(fp_x5_pair)()
fp_r11 = M.Head(M.Tail(fp_x5_pair)())()
fp_x5_sq_pair = A.Multiply(fp_x5, fp_x5, fp_r11)()
fp_x5_sq = M.Head(fp_x5_sq_pair)()
fp_r12 = M.Head(M.Tail(fp_x5_sq_pair)())()
fp_x5_fourth_pair = A.Multiply(fp_x5_sq, fp_x5_sq, fp_r12)()
fp_x5_fourth = M.Head(fp_x5_fourth_pair)()
fp_r13 = M.Head(M.Tail(fp_x5_fourth_pair)())()
fp_x5_rem_pair = A.Modulo(fp_x5_fourth, fp_sixteen, fp_r13)()
fp_x5_rem = M.Head(fp_x5_rem_pair)()
fp_r14 = M.Head(M.Tail(fp_x5_rem_pair)())()
assert M.NatEq(fp_x5_rem, fp_one, fp_r14)() is M.truth_value, "5^4 mod 16 != 1"

fp_x7_pair = M.NatFromRep(M.GMPRep("7"), registry)()
fp_x7 = M.Head(fp_x7_pair)()
fp_r15 = M.Head(M.Tail(fp_x7_pair)())()
fp_x7_sq_pair = A.Multiply(fp_x7, fp_x7, fp_r15)()
fp_x7_sq = M.Head(fp_x7_sq_pair)()
fp_r16 = M.Head(M.Tail(fp_x7_sq_pair)())()
fp_x7_fourth_pair = A.Multiply(fp_x7_sq, fp_x7_sq, fp_r16)()
fp_x7_fourth = M.Head(fp_x7_fourth_pair)()
fp_r17 = M.Head(M.Tail(fp_x7_fourth_pair)())()
fp_x7_rem_pair = A.Modulo(fp_x7_fourth, fp_sixteen, fp_r17)()
fp_x7_rem = M.Head(fp_x7_rem_pair)()
fp_r18 = M.Head(M.Tail(fp_x7_rem_pair)())()
assert M.NatEq(fp_x7_rem, fp_one, fp_r18)() is M.truth_value, "7^4 mod 16 != 1"
print("    Odd fourth powers = 1 mod 16 for x = 1, 3, 5, 7.")
print()

# --- [10] purity: the start state names no numeral -------------------------
print("[10] Purity: the descent start carries no numeral...")
pur_facts = P.KnowledgeFacts(descent_start)()
pur_fact_1 = M.Head(pur_facts)()
pur_fact_1_args = M.Tail(pur_fact_1)()
assert M.IsNat(M.Head(pur_fact_1)(), registry)() is M.false_value, "fact 1 head must not be a numeral"
assert M.IsNat(M.Head(pur_fact_1_args)(), registry)() is M.false_value, "QuarticSolution arg x must not be a numeral"
assert M.IsNat(M.Head(M.Tail(pur_fact_1_args)())(), registry)() is M.false_value, "QuarticSolution arg y must not be a numeral"
assert M.IsNat(M.Head(M.Tail(M.Tail(pur_fact_1_args)())())(), registry)() is M.false_value, "QuarticSolution arg z must not be a numeral"
assert M.IdentityCompare(M.Tail(M.Tail(M.Tail(pur_fact_1_args)())())(), M.EmptyList)() is M.truth_value, (
    "QuarticSolution must carry exactly three arguments"
)

pur_fact_2 = M.Head(M.Tail(pur_facts)())()
pur_fact_2_args = M.Tail(pur_fact_2)()
assert M.IsNat(M.Head(pur_fact_2)(), registry)() is M.false_value, "fact 2 head must not be a numeral"
assert M.IsNat(M.Head(pur_fact_2_args)(), registry)() is M.false_value, "MinimalSolution arg must not be a numeral"
assert M.IdentityCompare(M.Tail(pur_fact_2_args)(), M.EmptyList)() is M.truth_value, (
    "MinimalSolution must carry exactly one argument"
)

pur_fact_3 = M.Head(M.Tail(M.Tail(pur_facts)())())()
pur_fact_3_args = M.Tail(pur_fact_3)()
assert M.IsNat(M.Head(pur_fact_3)(), registry)() is M.false_value, "fact 3 head must not be a numeral"
assert M.IsNat(M.Head(pur_fact_3_args)(), registry)() is M.false_value, "Coprime arg x must not be a numeral"
assert M.IsNat(M.Head(M.Tail(pur_fact_3_args)())(), registry)() is M.false_value, "Coprime arg y must not be a numeral"
assert M.IdentityCompare(M.Tail(M.Tail(pur_fact_3_args)())(), M.EmptyList)() is M.truth_value, (
    "Coprime must carry exactly two arguments"
)

pur_fact_4 = M.Head(M.Tail(M.Tail(M.Tail(pur_facts)())())())()
pur_fact_4_args = M.Tail(pur_fact_4)()
assert M.IsNat(M.Head(pur_fact_4)(), registry)() is M.false_value, "fact 4 head must not be a numeral"
assert M.IsNat(M.Head(pur_fact_4_args)(), registry)() is M.false_value, "Parity arg x must not be a numeral"
assert M.IsNat(M.Head(M.Tail(pur_fact_4_args)())(), registry)() is M.false_value, "Parity polarity must not be a numeral"
assert M.IdentityCompare(M.Tail(M.Tail(pur_fact_4_args)())(), M.EmptyList)() is M.truth_value, (
    "Parity must carry exactly two arguments"
)

pur_fact_5 = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(pur_facts)())())())())()
pur_fact_5_args = M.Tail(pur_fact_5)()
assert M.IsNat(M.Head(pur_fact_5)(), registry)() is M.false_value, "fact 5 head must not be a numeral"
assert M.IsNat(M.Head(pur_fact_5_args)(), registry)() is M.false_value, "Parity arg y must not be a numeral"
assert M.IsNat(M.Head(M.Tail(pur_fact_5_args)())(), registry)() is M.false_value, "Parity polarity must not be a numeral"
assert M.IdentityCompare(M.Tail(M.Tail(pur_fact_5_args)())(), M.EmptyList)() is M.truth_value, (
    "Parity must carry exactly two arguments"
)

pur_fact_6 = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(pur_facts)())())())())())()
pur_fact_6_args = M.Tail(pur_fact_6)()
assert M.IsNat(M.Head(pur_fact_6)(), registry)() is M.false_value, "fact 6 head must not be a numeral"
assert M.IsNat(M.Head(pur_fact_6_args)(), registry)() is M.false_value, "NoInfiniteDescent arg must not be a numeral"
assert M.IdentityCompare(M.Tail(pur_fact_6_args)(), M.EmptyList)() is M.truth_value, (
    "NoInfiniteDescent must carry exactly one argument"
)
assert M.IdentityCompare(
    M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(pur_facts)())())())())())(), M.EmptyList
)() is M.truth_value, "the descent start must carry exactly six facts"
print("    Start facts are six labelled facts, none of them a numeral.")

pur_goal_fact = M.Head(P.KnowledgeFacts(descent_goal)())()
pur_goal_args = M.Tail(pur_goal_fact)()
assert M.IsNat(M.Head(pur_goal_fact)(), registry)() is M.false_value, "the goal head must not be a numeral"
assert M.IsNat(M.Head(pur_goal_args)(), registry)() is M.false_value, "the goal argument must not be a numeral"
assert M.IdentityCompare(M.Tail(pur_goal_args)(), M.EmptyList)() is M.truth_value, (
    "NoSolution must carry exactly one argument"
)
assert M.IdentityCompare(M.Head(I.PhiPattern(pack.phi)())(), L.ParityMod4InvariantLabel)() is M.truth_value, (
    "phi must be the ParityMod4Invariant observable"
)
print("    Goal carries no numeral; phi is the ParityMod4Invariant observable.")
print()

print("=== ALL TEST 15 FLT n = 4 QUARTIC DESCENT CHECKS PASSED in %.3fs ===" % (time.time() - t0))
