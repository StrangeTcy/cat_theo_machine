# ============================================================
# TEST 15: FLT n = 4 residue obstruction, discovered live
#
# No pack, no quartic rules, no solution written anywhere. This suite loads
# nothing and hand-writes no mathematics: the machine's Cartesian sweep
# discovers which modulus separates the square image from the odd square-sum
# image, the machine's own arithmetic then runs the complete residue case
# analysis modulo 4, and the promotion ledger is asked to promote the
# discovery. It refuses, because a ledger entry needs a Checker B receipt
# over a machine-verified derivation - a sweep discovery carries none.
#
# The classical Pythagorean parametrization descent needed for the full
# n = 4 theorem is not derivable by the current machinery; nothing here
# claims it. What is claimed is exactly what the machine did, on its own.
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
from cat_theo_machine import evaluator as Eval
from cat_theo_machine import promotion_ledger as Ledger
from cat_theo_machine import proof as P

t0 = time.time()
print("=== TEST 15: FLT n = 4 residue obstruction, discovered live ===")
print()

# --- [1] a bare machine; nothing is loaded -------------------------------
print("[1] Fresh runtime, no packs loaded, no quartic rules...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
graph._search_disable_console = M.truth_value
graph._search_disable_progress_ticker = M.truth_value
print("    Machine is bare; discovery must come from the sweep and arithmetic.")
print()

# --- [2] the sweep discovers the separating modulus ----------------------
print("[2] Sweeping squares and odd square sums, moduli 2, 3, 4, 5...")
bound_pair = M.NatFromRep(M.GMPRep("11"), registry)()
bound = M.Head(bound_pair)()
bound_reg = M.Head(M.Tail(bound_pair)())()
assert A.IsNat(bound, bound_reg)() is M.truth_value, "the sweep domain must be a Nat"

mod_two_pair = M.NatFromRep(M.GMPRep("2"), bound_reg)()
mod_two = M.Head(mod_two_pair)()
mod_two_reg = M.Head(M.Tail(mod_two_pair)())()
record_two = M.Head(PG.RunPlaygroundCartesianSweep(bound, mod_two, mod_two_reg)())()
disjoint_two = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record_two)())())())())()
assert disjoint_two is M.false_value, "modulus 2 must not separate the images"

mod_three_pair = M.NatFromRep(M.GMPRep("3"), registry)()
mod_three = M.Head(mod_three_pair)()
mod_three_reg = M.Head(M.Tail(mod_three_pair)())()
record_three = M.Head(PG.RunPlaygroundCartesianSweep(bound, mod_three, mod_three_reg)())()
disjoint_three = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record_three)())())())())()
assert disjoint_three is M.false_value, "modulus 3 must not separate the images"

mod_four_pair = M.NatFromRep(M.GMPRep("4"), registry)()
mod_four = M.Head(mod_four_pair)()
mod_four_reg = M.Head(M.Tail(mod_four_pair)())()
sweep_four_pair = PG.RunPlaygroundCartesianSweep(bound, mod_four, mod_four_reg)()
record_four = M.Head(sweep_four_pair)()
record_four_reg = M.Head(M.Tail(sweep_four_pair)())()
disjoint_four = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record_four)())())())())()
assert disjoint_four is M.truth_value, "modulus 4 must separate the images"

mod_five_pair = M.NatFromRep(M.GMPRep("5"), registry)()
mod_five = M.Head(mod_five_pair)()
mod_five_reg = M.Head(M.Tail(mod_five_pair)())()
record_five = M.Head(PG.RunPlaygroundCartesianSweep(bound, mod_five, mod_five_reg)())()
disjoint_five = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record_five)())())())())()
assert disjoint_five is M.false_value, "modulus 5 must not separate the images"

record_modulus = M.Head(M.Tail(record_four)())()
assert M.NatEq(record_modulus, M.four, record_four_reg)() is M.truth_value, (
    "the separating modulus discovered must be 4"
)
square_image = M.Head(M.Tail(M.Tail(record_four)())())()
odd_image = M.Head(M.Tail(M.Tail(M.Tail(record_four)())())())()
assert M.IdentityCompare(M.Tail(odd_image)(), M.EmptyList)() is M.truth_value, (
    "the odd square-sum image must be a single residue class"
)
odd_residue = M.Head(odd_image)()
assert M.NatEq(odd_residue, M.two, record_four_reg)() is M.truth_value, (
    "the odd square-sum residue class must be 2"
)
squares_first = M.Head(square_image)()
squares_second = M.Head(M.Tail(square_image)())()
assert M.IdentityCompare(M.Tail(M.Tail(square_image)())(), M.EmptyList)() is M.truth_value, (
    "the square image must hold two residue classes"
)
assert M.OrAtom(
    M.NatEq(squares_first, M.Zero, record_four_reg)(),
    M.NatEq(squares_first, M.one, record_four_reg)(),
)() is M.truth_value, "every square residue must be 0 or 1"
assert M.OrAtom(
    M.NatEq(squares_second, M.Zero, record_four_reg)(),
    M.NatEq(squares_second, M.one, record_four_reg)(),
)() is M.truth_value, "every square residue must be 0 or 1"
assert M.AndAtom(
    M.NatEq(odd_residue, M.Zero, record_four_reg)(),
    M.NatEq(odd_residue, M.one, record_four_reg)(),
)() is M.false_value, "residue 2 must lie outside the square image"
print("    Moduli 2, 3, 5 overlap; modulus 4 leaves squares in {0, 1} and odd sums in {2}.")
print()

# --- [3] the complete residue case analysis, run by machine arithmetic ----
print("[3] Fourth-power residues modulo 4, all four residue classes...")
r0_pair = M.NatFromRep(M.GMPRep("0"), registry)()
r0 = M.Head(r0_pair)()
r0_reg = M.Head(M.Tail(r0_pair)())()
r0_sq_pair = A.Multiply(r0, r0, r0_reg)()
r0_sq = M.Head(r0_sq_pair)()
r0_reg = M.Head(M.Tail(r0_sq_pair)())()
r0_quad_pair = A.Multiply(r0_sq, r0_sq, r0_reg)()
r0_quad = M.Head(r0_quad_pair)()
r0_reg = M.Head(M.Tail(r0_quad_pair)())()
r0_mod_pair = A.Modulo(r0_quad, M.four, r0_reg)()
r0_mod = M.Head(r0_mod_pair)()
r0_reg = M.Head(M.Tail(r0_mod_pair)())()
assert M.NatEq(r0_mod, M.Zero, r0_reg)() is M.truth_value, "0^4 must be 0 mod 4"

r1_pair = M.NatFromRep(M.GMPRep("1"), registry)()
r1 = M.Head(r1_pair)()
r1_reg = M.Head(M.Tail(r1_pair)())()
r1_sq_pair = A.Multiply(r1, r1, r1_reg)()
r1_sq = M.Head(r1_sq_pair)()
r1_reg = M.Head(M.Tail(r1_sq_pair)())()
r1_quad_pair = A.Multiply(r1_sq, r1_sq, r1_reg)()
r1_quad = M.Head(r1_quad_pair)()
r1_reg = M.Head(M.Tail(r1_quad_pair)())()
r1_mod_pair = A.Modulo(r1_quad, M.four, r1_reg)()
r1_mod = M.Head(r1_mod_pair)()
r1_reg = M.Head(M.Tail(r1_mod_pair)())()
assert M.NatEq(r1_mod, M.one, r1_reg)() is M.truth_value, "1^4 must be 1 mod 4"

r2_pair = M.NatFromRep(M.GMPRep("2"), registry)()
r2 = M.Head(r2_pair)()
r2_reg = M.Head(M.Tail(r2_pair)())()
r2_sq_pair = A.Multiply(r2, r2, r2_reg)()
r2_sq = M.Head(r2_sq_pair)()
r2_reg = M.Head(M.Tail(r2_sq_pair)())()
r2_quad_pair = A.Multiply(r2_sq, r2_sq, r2_reg)()
r2_quad = M.Head(r2_quad_pair)()
r2_reg = M.Head(M.Tail(r2_quad_pair)())()
r2_mod_pair = A.Modulo(r2_quad, M.four, r2_reg)()
r2_mod = M.Head(r2_mod_pair)()
r2_reg = M.Head(M.Tail(r2_mod_pair)())()
assert M.NatEq(r2_mod, M.Zero, r2_reg)() is M.truth_value, "2^4 must be 0 mod 4"

r3_pair = M.NatFromRep(M.GMPRep("3"), registry)()
r3 = M.Head(r3_pair)()
r3_reg = M.Head(M.Tail(r3_pair)())()
r3_sq_pair = A.Multiply(r3, r3, r3_reg)()
r3_sq = M.Head(r3_sq_pair)()
r3_reg = M.Head(M.Tail(r3_sq_pair)())()
r3_quad_pair = A.Multiply(r3_sq, r3_sq, r3_reg)()
r3_quad = M.Head(r3_quad_pair)()
r3_reg = M.Head(M.Tail(r3_quad_pair)())()
r3_mod_pair = A.Modulo(r3_quad, M.four, r3_reg)()
r3_mod = M.Head(r3_mod_pair)()
r3_reg = M.Head(M.Tail(r3_mod_pair)())()
assert M.NatEq(r3_mod, M.one, r3_reg)() is M.truth_value, "3^4 must be 1 mod 4"

odd_quad_sum_pair = A.Add(r1_mod, r3_mod, r3_reg)()
odd_quad_sum = M.Head(odd_quad_sum_pair)()
odd_quad_sum_reg = M.Head(M.Tail(odd_quad_sum_pair)())()
odd_sum_mod_pair = A.Modulo(odd_quad_sum, M.four, odd_quad_sum_reg)()
odd_sum_mod = M.Head(odd_sum_mod_pair)()
odd_sum_mod_reg = M.Head(M.Tail(odd_sum_mod_pair)())()
assert M.NatEq(odd_sum_mod, M.two, odd_sum_mod_reg)() is M.truth_value, (
    "two odd fourth powers must sum to 2 mod 4"
)
assert M.AndAtom(
    M.NatEq(odd_sum_mod, M.Zero, odd_sum_mod_reg)(),
    M.NatEq(odd_sum_mod, M.one, odd_sum_mod_reg)(),
)() is M.false_value, "2 mod 4 lies outside the fourth-power image {0, 1}"
print("    All four residue classes analysed: 4th powers are {0, 1}; odd pairs give 2,")
print("    which is outside the image, so x and y cannot both be odd in any solution.")
print()

print("[4] The sweep record names the discovered obstruction, modulo", end=" ")
discovered_modulus = M.NatRepOf(record_modulus, record_four_reg)()()
candidate_name = M.Char("mod_%d_disjoint_image_obstruction" % discovered_modulus)
print("%d..." % discovered_modulus)
assert discovered_modulus == 4, "the synthesized lemma must come from the discovered modulus"
ledger = Ledger.EmptyPromotionLedger(record_four_reg)()
assert M.IdentityCompare(Ledger.PromotionLedgerVersion(ledger)(), M.Zero)() is M.truth_value, (
    "a fresh ledger starts at version zero"
)
print("    Candidate lemma synthesized from machine data: mod_4_disjoint_image_obstruction")
print()

# --- [5] the gate refuses discovery without a derivation -------------------
print("[5] Asking the ledger to promote the sweep discovery...")
discovery_start = M.Atom()
discovery_goal = M.Atom()
discovery_candidate = Eval.CandidateMacro(
    candidate_name, discovery_start, discovery_goal, M.EmptyList
)()
evidence = Eval.EvaluateCandidateProof(
    discovery_candidate, discovery_start, discovery_goal, M.EmptyList, record_four_reg
)()
assert M.IdentityCompare(M.Head(evidence)(), L.CandidateEvaluatedLabel)() is M.false_value, (
    "a sweep discovery is not a proof and must not be certified as one"
)
assert M.IdentityCompare(M.Head(evidence)(), L.GoalMismatchLabel)() is M.truth_value, (
    "the refusal reason must be that no derivation reaches the goal"
)
baseline_cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
promotion = Ledger.SubmitCandidateForPromotion(
    ledger,
    discovery_candidate,
    L.ProofSchemaPromotionLabel,
    discovery_start,
    discovery_goal,
    baseline_cost,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    record_four_reg,
)()
assert M.IdentityCompare(M.Head(promotion)(), L.PromotionRejectedLabel)() is M.truth_value, (
    "the promotion gate must reject a discovery with no Checker B receipt"
)
assert M.NatEq(Ledger.PromotionLedgerVersion(ledger)(), M.Zero, record_four_reg)() is M.truth_value, (
    "the ledger must not move on a rejected candidate"
)
print("    Rejected, exactly as it must be: no receipt, no ledger entry.")
print()

print("=== ALL TEST 15 RESIDUE DISCOVERY CHECKS PASSED in %.3fs ===" % (time.time() - t0))
print("Boundary: the Pythagorean parametrization descent needed for the full")
print("n = 4 theorem is not derivable by the current machinery and is not claimed here.")
