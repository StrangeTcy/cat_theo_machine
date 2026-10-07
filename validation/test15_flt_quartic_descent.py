# ============================================================
# TEST 15: FLT n = 4 Quartic Descent (W6)
#
# Verifies packs/flt-quartic.pack.yaml:
#   - the pack loads and its two examples are machine-replayable
#   - the mod 4 parity obstruction is the one the W3 Cartesian sweep
#     discovers on its own, not a number written into the pack
#   - the obstruction route prunes the goal with zero search
#   - the descent route replays a five step derivation whose last step is
#     licensed by well-foundedness, and reaches NoSolution
#   - the algebraic content of every named lemma is checked by machine
#     arithmetic on concrete instances (parametrization, coprime factors,
#     relapse identities, strict decrease)
#   - negative controls: no minimality -> no descent; equal readings -> no prune
#   - the start state carries no numeral at all
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
from cat_theo_machine.prettyprinting import PrettyTerm
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


def pretty(term, reg=None):
    if reg is None:
        reg = registry
    return PrettyTerm(term, reg)()


def chain_of(items):
    out = M.EmptyList
    for item in reversed(items):
        out = M.Pair(item, out)
    return out


def the_rule(rules, index):
    cur = rules
    i = 0
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        if i == index:
            return M.Head(cur)()
        cur = M.Tail(cur)()
        i += 1
    return M.EmptyList


# --- machine-native arithmetic helpers -------------------------------------
def nat_of(value, reg):
    return M.NatRepOf(value, reg)()()


def nat_from_int(n, reg):
    pair = M.NatFromRep(M.GMPRep(n), reg)()
    return M.Head(pair)(), M.Head(M.Tail(pair)())()


def add_nodes(a, b, reg):
    pair = A.Add(a, b, reg)()
    return M.Head(pair)(), M.Head(M.Tail(pair)())()


def mul_nodes(a, b, reg):
    pair = A.Multiply(a, b, reg)()
    return M.Head(pair)(), M.Head(M.Tail(pair)())()


def square_node(a, reg):
    return mul_nodes(a, a, reg)


def fourth_node(a, reg):
    sq, reg1 = square_node(a, reg)
    return square_node(sq, reg1)


def mod_nodes(a, b, reg):
    pair = A.Modulo(a, b, reg)()
    return M.Head(pair)(), M.Head(M.Tail(pair)())()


def nat_less(a, b, reg):
    return M.NatLess(a, b, reg)() is M.truth_value


def is_coprime(a, b, reg):
    return A.IsCoprime(a, b, reg)() is M.truth_value


def holds_nat_eq(a, b, reg):
    return M.NatEq(a, b, reg)() is M.truth_value


def fact(head, args):
    return M.Pair(head, chain_of(args))


def fact_head_value(the_fact, reg):
    """Second slot of a two-slot fact, as a Python integer."""
    return nat_of(M.Head(M.Tail(the_fact)())(), reg)


def term_has_nat_node(term, reg):
    if M.IsNat(term, reg)() is M.truth_value:
        return True
    if M.IsPair(term)() is M.truth_value:
        if term_has_nat_node(M.Head(term)(), reg):
            return True
        return term_has_nat_node(M.Tail(term)(), reg)
    return False


def facts_chain_has_nat_node(node, reg):
    if M.IdentityCompare(node, M.EmptyList)() is M.truth_value:
        return False
    if term_has_nat_node(M.Head(node)(), reg):
        return True
    return facts_chain_has_nat_node(M.Tail(node)(), reg)


# --- [2] load the pack ------------------------------------------------------
print("[2] Loading packs/flt-quartic.pack.yaml...")
namespace = dict(vars(M))
namespace.update(vars(L))
namespace.update(vars(P))
loader = PACKS.PackLoader(namespace)
pack_path = os.path.join(IMPORT_ROOT, "cat_theo_machine", "packs", "flt-quartic.pack.yaml")
pack = loader.load_pack_file(pack_path, graph)
summary = PACKS.pack_summary(pack)
print(f"    Pack summary: {summary}")
assert summary["name"] == "flt-quartic", "expected the flt-quartic pack"
assert summary["rule_count"] == 6, f"expected 6 rules, got {summary['rule_count']}"
assert summary["example_count"] == 2, f"expected 2 examples, got {summary['example_count']}"
print("    Pack loaded.")
print()

# --- [3] the sweep discovers the obstruction, the pack cites it -------------
print("[3] Grounding: W3 Cartesian sweep vs the pack's mod 4 observable...")
n11, reg1 = nat_from_int(11, registry)
n4, reg2 = nat_from_int(4, reg1)
sweep_pair = PG.RunPlaygroundCartesianSweep(n11, n4, reg2)()
sweep_record = M.Head(sweep_pair)()
sweep_reg = M.Head(M.Tail(sweep_pair)())()
record_label = M.Head(sweep_record)()
assert M.IdentityCompare(record_label, L.DiscoveredInvariantLabel)() is M.truth_value

sq_set = M.Head(M.Tail(M.Tail(sweep_record)())())()
odd_set = M.Head(M.Tail(M.Tail(M.Tail(sweep_record)())())())()
is_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(sweep_record)())())())())()


def set_values(set_chain, reg):
    values = []
    cur = set_chain
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        v = nat_of(M.Head(cur)(), reg)
        if v not in values:
            values.append(v)
        cur = M.Tail(cur)()
    return sorted(values)


sq_values = set_values(sq_set, sweep_reg)
odd_values = set_values(odd_set, sweep_reg)
print(f"    Squares mod 4 image:            {sq_values}")
print(f"    Odd sum of squares mod 4 image: {odd_values}")
print(f"    Disjoint images:                {is_disjoint is M.truth_value}")
assert sq_values == [0, 1], f"sweep found squares mod 4 = {sq_values}"
assert odd_values == [2], f"sweep found odd sums mod 4 = {odd_values}"
assert is_disjoint is M.truth_value, "sweep must find the two images disjoint"

obstruction_start, obstruction_goal = pack.examples["flt_e4_parity_obstruction"]
start_reading_fact = M.Head(P.KnowledgeFacts(obstruction_start)())()
goal_reading_fact = M.Head(P.KnowledgeFacts(obstruction_goal)())()
print(f"    Pack start reading:             {pretty(start_reading_fact, sweep_reg)}")
print(f"    Pack goal reading:              {pretty(goal_reading_fact, sweep_reg)}")
start_reading = fact_head_value(start_reading_fact, sweep_reg)
goal_reading = fact_head_value(goal_reading_fact, sweep_reg)
assert M.IdentityCompare(M.Head(start_reading_fact)(), L.ParityMod4InvariantLabel)() is M.truth_value
assert M.IdentityCompare(M.Head(goal_reading_fact)(), L.ParityMod4InvariantLabel)() is M.truth_value
assert start_reading in sq_values, "start reading must be a residue the sweep produces"
assert goal_reading in odd_values, "goal reading must be the odd sum residue"
assert goal_reading not in sq_values, "goal reading must be outside the square image"
print(f"    Residue {goal_reading} is produced by odd sums and absent from {sq_values}.")
print()

# --- [4] the obstruction route prunes with zero search ----------------------
print("[4] Obstruction: ReachabilityPrune with the residue invariant...")
carrier_rule = the_rule(pack.rule_chain, 4)
carrier_chain = M.Pair(carrier_rule, M.EmptyList)
heuristic = H.Heuristic(M.DFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
phi = pack.phi
invariant = I.Invariant(phi, carrier_chain, registry, obstruction_start, carrier_chain)()
assert I.IsInvariant(invariant)() is M.truth_value, "the residue reading must be invariant"
assert I.PhiHolds(obstruction_start, phi)() is M.truth_value, "phi must hold on the start"
prune = I.ReachabilityPrune(obstruction_start, obstruction_goal, invariant, phi, registry)()
assert I.IsUnreachable(prune)() is M.truth_value, "the residue goal must be unreachable"

search_pair = I.SearchWithInvariant(
    graph, obstruction_start, obstruction_goal, carrier_chain, heuristic, registry, phi
)()
search_plan = M.Head(search_pair)()
search_cost = M.Head(M.Tail(search_pair)())()
search_prune = M.Head(M.Tail(M.Tail(search_pair)())())()
expanded = nat_of(M.SearchCostExpanded(search_cost)(), registry)
print(f"    Plan empty: {M.IdentityCompare(search_plan, M.EmptyList)() is M.truth_value}")
print(f"    Unreachable: {I.IsUnreachable(search_prune)() is M.truth_value}")
print(f"    Search expanded: {expanded}")
assert M.IdentityCompare(search_plan, M.EmptyList)() is M.truth_value
assert I.IsUnreachable(search_prune)() is M.truth_value
assert expanded == 0, f"expected zero search, expanded={expanded}"
print("    Obstruction discharged without search.")
print()

# --- [5] the same route through the public prove entry point ---------------
print("[5] Obstruction through Prove(start, goal, rules, heuristic, registry, phi)...")
prove_pair = P.Prove(
    graph, obstruction_start, obstruction_goal, carrier_chain, heuristic, registry, phi
)()
prove_result = M.Head(prove_pair)()
print(f"    Prove result: {pretty(prove_result, registry)[:120]}")
assert I.IsUnreachable(prove_result)() is M.truth_value, "Prove must return the unreachability record"
print("    Prove reports the residue goal unreachable.")
print()

# --- [6] negative control: equal readings never prune ----------------------
print("[6] Negative control: a goal with the same reading is not pruned...")
same_goal = P.Knowledge(
    M.Pair(fact(L.ParityMod4InvariantLabel, [M.one]), M.EmptyList)
)()
same_invariant = I.Invariant(phi, carrier_chain, registry, same_goal, carrier_chain)()
assert I.IsInvariant(same_invariant)() is M.truth_value
same_prune = I.ReachabilityPrune(obstruction_start, same_goal, same_invariant, phi, registry)()
print(f"    Same reading unreachable: {I.IsUnreachable(same_prune)() is M.truth_value}")
assert I.IsUnreachable(same_prune)() is M.false_value, "equal readings must not prune"
print()

# --- [7] the descent route --------------------------------------------------
print("[7] Descent: five step derivation to NoSolution...")
descent_start, descent_goal = pack.examples["flt_e4_quartic_descent"]
t_descent = time.time()
plan = I.RewriteSearch(descent_start, descent_goal, pack.rule_chain, registry)()
elapsed = time.time() - t_descent
assert M.IdentityCompare(plan, M.EmptyList)() is M.false_value, "the descent must produce a plan"

steps = []
cur = plan
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    steps.append(M.Head(cur)())
    cur = M.Tail(cur)()
print(f"    Plan length: {len(steps)} steps in {elapsed:.2f}s")
assert len(steps) == 5, f"expected 5 descent steps, got {len(steps)}"

derivation_pair = P.BuildDerivation(descent_start, plan, registry)()
derivation = M.Head(derivation_pair)()
replay_registry = M.Head(M.Tail(derivation_pair)())()
end_state = P.DerivationEnd(derivation, replay_registry)()
end_facts = P.KnowledgeFacts(end_state)()
assert P.FactsCover(P.KnowledgeFacts(descent_goal)(), end_facts)() is M.truth_value, "replay must cover the goal"

no_solution_seen = M.false_value
cur = end_facts
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    the_fact = M.Head(cur)()
    if M.IdentityCompare(M.Head(the_fact)(), L.NoSolutionLabel)() is M.truth_value:
        no_solution_seen = M.truth_value
        print(f"    Derived: {pretty(the_fact, replay_registry)}")
    cur = M.Tail(cur)()
assert no_solution_seen is M.truth_value, "the derivation must derive NoSolution"

def term_mentions_label(term, label):
    if M.IdentityCompare(term, label)() is M.truth_value:
        return True
    if M.IsPair(term)() is M.false_value:
        return False
    if term_mentions_label(M.Head(term)(), label):
        return True
    return term_mentions_label(M.Tail(term)(), label)


last_action = steps[len(steps) - 1]
last_rule = P.ActionRule(last_action)()
assert term_mentions_label(P.RulePremises(last_rule)(), L.NoInfiniteDescentLabel), (
    "the last step must cite well-foundedness"
)
assert term_mentions_label(P.RulePremises(last_rule)(), L.NatLessLabel), (
    "the last step must consume the strict decrease"
)
print("    Last step cites NoInfiniteDescent: the chain is closed by well-foundedness.")
print()

# --- [8] negative control: no minimality, no descent -----------------------
print("[8] Negative control: without the minimal solution the descent stalls...")
bare_facts = chain_of(
    [
        fact(L.QuarticSolutionLabel, [M.Char("x"), M.Char("y"), M.Char("z")]),
        fact(L.CoprimeLabel, [M.Char("x"), M.Char("y")]),
        fact(L.ParityLabel, [M.Char("x"), L.OddLabel]),
        fact(L.ParityLabel, [M.Char("y"), L.EvenLabel]),
        fact(L.NoInfiniteDescentLabel, [M.Char("z")]),
    ]
)
bare_start = P.Knowledge(bare_facts)()
bare_plan = I.RewriteSearch(bare_start, descent_goal, pack.rule_chain, registry)()
print(f"    Plan empty without MinimalSolution: {M.IdentityCompare(bare_plan, M.EmptyList)() is M.truth_value}")
assert M.IdentityCompare(bare_plan, M.EmptyList)() is M.truth_value, "no minimal solution must yield no descent proof"
print()

# --- [9] the algebra the named lemmas assert, checked on instances ---------
print("[9] Machine arithmetic on the parametrization and the relapse...")
# m^2 - n^2 and p^2 - q^2 are supplied as integers by the harness; every
# following identity and inequality is computed by the machine itself.
grid = [(2, 1), (3, 2), (4, 1), (4, 3), (5, 2), (5, 4), (6, 1), (6, 5), (7, 2), (7, 4)]
checked = 0
reg = registry
for m_int, n_int in grid:
    m_node, reg = nat_from_int(m_int, reg)
    n_node, reg = nat_from_int(n_int, reg)
    m_sq, reg = square_node(m_node, reg)
    n_sq, reg = square_node(n_node, reg)

    a_int = m_int * m_int - n_int * n_int
    a_node, reg = nat_from_int(a_int, reg)
    two_node, reg = nat_from_int(2, reg)
    mn, reg = mul_nodes(m_node, n_node, reg)
    b_node, reg = mul_nodes(two_node, mn, reg)
    c_node, reg = add_nodes(m_sq, n_sq, reg)

    # a = m^2 - n^2 really is (m - n)(m + n), machine checked
    m_plus_n, reg = add_nodes(m_node, n_node, reg)
    m_minus_n, reg = nat_from_int(m_int - n_int, reg)
    factored, reg = mul_nodes(m_minus_n, m_plus_n, reg)
    assert holds_nat_eq(factored, a_node, reg), f"(m-n)(m+n) != m^2-n^2 for ({m_int}, {n_int})"
    assert is_coprime(m_minus_n, m_plus_n, reg), f"coprime factors failed for ({m_int}, {n_int})"

    # a^2 + b^2 = c^2
    a_sq, reg = square_node(a_node, reg)
    b_sq, reg = square_node(b_node, reg)
    c_sq, reg = square_node(c_node, reg)
    lhs, reg = add_nodes(a_sq, b_sq, reg)
    assert holds_nat_eq(lhs, c_sq, reg), f"parametrization failed for ({m_int}, {n_int})"
    checked += 1
print(f"    Parametrization (m-n)(m+n) = m^2-n^2, coprime factors, and a^2 + b^2 = c^2 on {checked} instances.")

relapse_grid = [(2, 1), (3, 2), (4, 3), (5, 2), (5, 4), (6, 5), (7, 2), (7, 6)]
relapse_checked = 0
reg = registry
for p_int, q_int in relapse_grid:
    p_node, reg = nat_from_int(p_int, reg)
    q_node, reg = nat_from_int(q_int, reg)

    p_sq, reg = square_node(p_node, reg)
    q_sq, reg = square_node(q_node, reg)
    p_fourth, reg = square_node(p_sq, reg)
    q_fourth, reg = square_node(q_sq, reg)

    s_node, reg = nat_from_int(p_int * p_int - q_int * q_int, reg)
    r_node, reg = add_nodes(p_sq, q_sq, reg)
    s_sq, reg = square_node(s_node, reg)
    r_sq, reg = square_node(r_node, reg)

    # u^2 = p^4 + q^4 and r^2 + s^2 = 2 u^2
    u_sq, reg = add_nodes(p_fourth, q_fourth, reg)
    r_sq_plus_s_sq, reg = add_nodes(r_sq, s_sq, reg)
    two_node, reg = nat_from_int(2, reg)
    twice_u_sq, reg = mul_nodes(two_node, u_sq, reg)
    assert holds_nat_eq(r_sq_plus_s_sq, twice_u_sq, reg), f"relapse sum failed for ({p_int}, {q_int})"

    # r^2 = s^2 + 4 p^2 q^2
    four_node, reg = nat_from_int(4, reg)
    pq, reg = mul_nodes(p_node, q_node, reg)
    pq_sq, reg = square_node(pq, reg)
    four_pq_sq, reg = mul_nodes(four_node, pq_sq, reg)
    s_sq_plus_four_pq_sq, reg = add_nodes(s_sq, four_pq_sq, reg)
    assert holds_nat_eq(r_sq, s_sq_plus_four_pq_sq, reg), f"relapse difference failed for ({p_int}, {q_int})"

    # z = u^4 + 4 p^4 q^4 is above u^2 = p^4 + q^4, and u < u^2, so u < z
    u_fourth, reg = square_node(u_sq, reg)
    p_fourth_q_fourth, reg = mul_nodes(p_fourth, q_fourth, reg)
    four_p_fourth_q_fourth, reg = mul_nodes(four_node, p_fourth_q_fourth, reg)
    z_node, reg = add_nodes(u_fourth, four_p_fourth_q_fourth, reg)
    assert nat_less(u_sq, z_node, reg), f"strict decrease failed for ({p_int}, {q_int})"
    relapse_checked += 1
print(f"    Relapse identities and strict decrease on {relapse_checked} instances.")

# the decrease lands on a genuine descent witness: u^2 = z is impossible below z
reg = registry
for u_int in range(2, 7):
    u_node, reg = nat_from_int(u_int, reg)
    u_sq, reg = square_node(u_node, reg)
    assert nat_less(u_node, u_sq, reg), f"u < u^2 failed for u={u_int}"
print("    u < u^2 verified for u in 2..6.")

# fourth powers modulo 4 and modulo 16
reg = registry
four_node, reg = nat_from_int(4, reg)
sixteen_node, reg = nat_from_int(16, reg)
one_node, reg = nat_from_int(1, reg)
for x_int in range(0, 12):
    x_node, reg = nat_from_int(x_int, reg)
    sq, reg = square_node(x_node, reg)
    rem, reg = mod_nodes(sq, four_node, reg)
    residue = nat_of(rem, reg)
    assert residue in (0, 1), f"{x_int}^2 mod 4 = {residue}"
    if x_int % 2 == 1:
        x_fourth, reg = square_node(sq, reg)
        rem16, reg = mod_nodes(x_fourth, sixteen_node, reg)
        assert nat_of(rem16, reg) == 1, f"{x_int}^4 mod 16 != 1"
print("    Squares mod 4 in {0, 1}; odd fourth powers = 1 mod 16.")
print()

# --- [10] purity: the start state names no numeral -------------------------
print("[10] Purity: the descent start carries no numeral...")
assert facts_chain_has_nat_node(P.KnowledgeFacts(descent_start)(), registry) is False, (
    "the descent start must not contain a numeral"
)
start_label_heads = []
remaining = P.KnowledgeFacts(descent_start)()
while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
    start_label_heads.append(M.Head(M.Head(remaining)())())
    remaining = M.Tail(remaining)()
print(f"    Start facts: {len(start_label_heads)}, none of them a numeral.")

goal_facts = P.KnowledgeFacts(descent_goal)()
assert facts_chain_has_nat_node(goal_facts, registry) is False, "the goal must not contain a numeral"

phi_pattern_term = I.PhiPattern(phi)()
assert M.IdentityCompare(M.Head(phi_pattern_term)(), L.ParityMod4InvariantLabel)() is M.truth_value
print("    Pack phi is the ParityMod4Invariant observable.")
print()

print(f"=== ALL TEST 15 FLT n = 4 QUARTIC DESCENT CHECKS PASSED in {time.time() - t0:.3f}s ===")
