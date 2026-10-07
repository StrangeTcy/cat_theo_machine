# ============================================================
# TEST 16: W6 Live Session - the machine learns the n = 4 obstruction
#
# The pack states conjectures. This session makes the machine earn them:
#
#   [2] the machine searches the descent and keeps its own derivation as
#       the experience trace of the session
#   [3] modulus discovery - the machine sweeps residues modulo 2, 3, 4, 5
#       and records which modulus separates the square image from the
#       odd-pair image, and which residue classes each image holds
#   [4] mining - a decoy template is offered first and refuted, the
#       conjecture template is certified by MineInvariantFromTrace
#   [5] obstruction - UnreachabilityProverByInvariant turns the certificate
#       into a machine proof that the residue goal cannot be reached
#   [6] conjecture checks - every descent lemma is checked by the machine's
#       own arithmetic, and a corrupted near-miss is refuted
#   [7] gated promotion - the learned schema passes Checker B, ablation and
#       withheld holdouts, then commits to the ledger; a failing holdout is
#       rejected and the ledger does not move
#   [8] replay - the promoted schema reproduces the derivation from the
#       ledger alone, Checker B verified
#
# Flat machine-native style: no helper functions, no loops, no lists, no
# dicts, no python bools.
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
from cat_theo_machine import checker_b as CheckerB
from cat_theo_machine import evaluator as Eval
from cat_theo_machine import invariance as I
from cat_theo_machine import invariant_miner as Miner
from cat_theo_machine import packs as PACKS
from cat_theo_machine import promotion_ledger as Ledger
from cat_theo_machine import proof as P

t0 = time.time()
print("=== TEST 16: W6 Live Session - learning the n = 4 obstruction ===")
print()

# --- [1] a bare machine and the conjecture pack ----------------------------
print("[1] Fresh runtime; the pack carries conjectures, nothing is trusted yet...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
graph._search_disable_console = M.truth_value
graph._search_disable_progress_ticker = M.truth_value
namespace = dict(vars(M))
namespace.update(vars(L))
namespace.update(vars(P))
loader = PACKS.PackLoader(namespace)
pack_path = os.path.join(IMPORT_ROOT, "cat_theo_machine", "packs", "flt-quartic.pack.yaml")
pack = loader.load_pack_file(pack_path, graph)
obstruction_start, obstruction_goal = pack.examples["flt_e4_parity_obstruction"]
descent_start, descent_goal = pack.examples["flt_e4_quartic_descent"]
conjectures = pack.rule_chain
carrier_rule = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(conjectures)())())())())()
carrier_chain = M.Pair(carrier_rule, M.EmptyList)
print("    Runtime and conjectures loaded; no verification has run yet.")
print()

# --- [2] the machine runs the descent and keeps the derivation -------------
print("[2] The machine searches the descent; its derivation is the session trace...")
d_t0 = time.time()
plan = I.RewriteSearch(descent_start, descent_goal, conjectures, registry)()
print("    Search time: %.3fs" % (time.time() - d_t0))
assert M.IdentityCompare(plan, M.EmptyList)() is M.false_value, "the descent search must find a plan"
assert M.IdentityCompare(
    M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())(), M.EmptyList
)() is M.truth_value, "the learned plan must be five steps"
trace_pair = P.BuildDerivation(descent_start, plan, registry)()
session_trace = M.Head(trace_pair)()
trace_registry = M.Head(M.Tail(trace_pair)())()
assert P.FactsCover(P.KnowledgeFacts(descent_goal)(), P.KnowledgeFacts(P.DerivationEnd(session_trace, trace_registry)())())() is M.truth_value, (
    "the session trace must reach the goal"
)
print("    Trace holds five steps and reaches the goal.")
print()

# --- [3] the machine discovers which modulus separates the images ----------
print("[3] Modulus discovery: sweeping residues 0..10 against moduli 2, 3, 4, 5...")
bound_pair = M.NatFromRep(M.GMPRep("11"), registry)()
bound = M.Head(bound_pair)()
bound_reg = M.Head(M.Tail(bound_pair)())()
mod_two_pair = M.NatFromRep(M.GMPRep("2"), bound_reg)()
mod_two = M.Head(mod_two_pair)()
mod_two_reg = M.Head(M.Tail(mod_two_pair)())()
sweep_two = M.Head(PG.RunPlaygroundCartesianSweep(bound, mod_two, mod_two_reg)())()
sweep_two_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(sweep_two)())())())())()
assert sweep_two_disjoint is M.false_value, "modulus 2 must not separate the images"

mod_three_pair = M.NatFromRep(M.GMPRep("3"), registry)()
mod_three = M.Head(mod_three_pair)()
mod_three_reg = M.Head(M.Tail(mod_three_pair)())()
sweep_three = M.Head(PG.RunPlaygroundCartesianSweep(bound, mod_three, mod_three_reg)())()
sweep_three_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(sweep_three)())())())())()
assert sweep_three_disjoint is M.false_value, "modulus 3 must not separate the images"

mod_four_pair = M.NatFromRep(M.GMPRep("4"), registry)()
mod_four = M.Head(mod_four_pair)()
mod_four_reg = M.Head(M.Tail(mod_four_pair)())()
sweep_four_pair = PG.RunPlaygroundCartesianSweep(bound, mod_four, mod_four_reg)()
sweep_four = M.Head(sweep_four_pair)()
sweep_four_reg = M.Head(M.Tail(sweep_four_pair)())()
sweep_four_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(sweep_four)())())())())()
assert sweep_four_disjoint is M.truth_value, "modulus 4 must separate the images"

mod_five_pair = M.NatFromRep(M.GMPRep("5"), registry)()
mod_five = M.Head(mod_five_pair)()
mod_five_reg = M.Head(M.Tail(mod_five_pair)())()
sweep_five = M.Head(PG.RunPlaygroundCartesianSweep(bound, mod_five, mod_five_reg)())()
sweep_five_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(sweep_five)())())())())()
assert sweep_five_disjoint is M.false_value, "modulus 5 must not separate the images"

fours_square_image = M.Head(M.Tail(M.Tail(sweep_four)())())()
fours_odd_image = M.Head(M.Tail(M.Tail(M.Tail(sweep_four)())())())()
fours_odd_residue = M.Head(fours_odd_image)()
assert M.IdentityCompare(M.Tail(fours_odd_image)(), M.EmptyList)() is M.truth_value, (
    "the odd pair image must be a single residue class"
)
residue_two_pair = M.NatFromRep(M.GMPRep("2"), sweep_four_reg)()
residue_two = M.Head(residue_two_pair)()
residue_two_reg = M.Head(M.Tail(residue_two_pair)())()
assert M.NatEq(fours_odd_residue, residue_two, residue_two_reg)() is M.truth_value, (
    "the odd pair residue class must be 2"
)
squares_first = M.Head(fours_square_image)()
squares_second = M.Head(M.Tail(fours_square_image)())()
assert M.IdentityCompare(M.Tail(M.Tail(fours_square_image)())(), M.EmptyList)() is M.truth_value, (
    "the square image must hold two residue classes"
)
residue_zero_pair = M.NatFromRep(M.GMPRep("0"), registry)()
residue_zero = M.Head(residue_zero_pair)()
residue_zero_reg = M.Head(M.Tail(residue_zero_pair)())()
residue_one_pair = M.NatFromRep(M.GMPRep("1"), residue_zero_reg)()
residue_one = M.Head(residue_one_pair)()
residue_one_reg = M.Head(M.Tail(residue_one_pair)())()
assert M.OrAtom(
    M.NatEq(squares_first, residue_zero, residue_one_reg)(),
    M.NatEq(squares_first, residue_one, residue_one_reg)(),
)() is M.truth_value, "every square residue must be 0 or 1"
assert M.OrAtom(
    M.NatEq(squares_second, residue_zero, residue_one_reg)(),
    M.NatEq(squares_second, residue_one, residue_one_reg)(),
)() is M.truth_value, "every square residue must be 0 or 1"
assert M.AndAtom(
    M.NatEq(fours_odd_residue, residue_zero, residue_one_reg)(),
    M.NatEq(fours_odd_residue, residue_one, residue_one_reg)(),
)() is M.false_value, "residue 2 must lie outside the square image"
print("    Moduli 2, 3, 5 overlap; modulus 4 leaves squares in {0, 1} and odd pairs in {2}.")
print()

# --- [4] mining: the decoy is refuted, the conjecture is certified ---------
print("[4] Mining: a decoy template is offered first and refuted...")
decoy_observable = M.Atom()
decoy_key = M.Char("r")
decoy_template = I.Phi(
    M.Pair(decoy_observable, M.Pair(M.Pair(M.VarTag, M.Pair(decoy_key, M.EmptyList)), M.EmptyList))
)()
candidate_templates = M.Pair(decoy_template, M.Pair(pack.phi, M.EmptyList))
decoy_preservation = Miner.CheckInvariantPreservationAcrossRules(
    decoy_template, carrier_chain, registry
)()
assert M.IdentityCompare(M.Head(decoy_preservation)(), M.truth_value)() is M.false_value, (
    "the decoy template must be refuted"
)
mine_pair = Miner.MineInvariantFromTrace(
    session_trace, obstruction_start, carrier_chain, candidate_templates, registry
)()
assert M.IdentityCompare(M.Head(mine_pair)(), M.truth_value)() is M.truth_value, (
    "the miner must return the surviving template"
)
certificate = M.Head(M.Tail(mine_pair)())()
assert M.IdentityCompare(M.Head(certificate)(), L.InvariantCertificateLabel)() is M.truth_value, (
    "the miner must issue an invariant certificate"
)
certified_phi = Miner.InvariantCertificatePhi(certificate)()
assert M.Compare(certified_phi, pack.phi)() is M.truth_value, (
    "the certificate must carry the conjecture template, not the decoy"
)
assert M.Compare(Miner.InvariantCertificateProvenance(certificate)(), session_trace)() is M.truth_value, (
    "the certificate must name the session trace as provenance"
)
print("    Decoy refuted; conjecture certified against the session trace.")
print()

# --- [5] the certificate proves the obstruction ----------------------------
print("[5] Obstruction: UnreachabilityProverByInvariant on the certified template...")
obstruction = Miner.UnreachabilityProverByInvariant(
    obstruction_start, obstruction_goal, carrier_chain, certified_phi, registry
)()
assert M.IdentityCompare(M.Head(obstruction)(), L.UnreachableLabel)() is M.truth_value, (
    "the certified invariant must refute the residue goal"
)
assert I.PhiHolds(obstruction_start, certified_phi)() is M.truth_value, (
    "the invariant must hold on the start state"
)
assert I.IsUnreachable(obstruction)() is M.truth_value, (
    "the obstruction record must read as unreachable"
)
print("    Certified invariant makes the residue goal unreachable.")
print()

# --- [6] the descent conjectures are checked by the machine ----------------
print("[6] Conjecture checks: the machine tests the lemmas on instances...")
w_m_pair = M.NatFromRep(M.GMPRep("2"), registry)()
w_m = M.Head(w_m_pair)()
w_r1 = M.Head(M.Tail(w_m_pair)())()
w_n_pair = M.NatFromRep(M.GMPRep("1"), w_r1)()
w_n = M.Head(w_n_pair)()
w_r2 = M.Head(M.Tail(w_n_pair)())()
w_m_sq_pair = A.Multiply(w_m, w_m, w_r2)()
w_m_sq = M.Head(w_m_sq_pair)()
w_r3 = M.Head(M.Tail(w_m_sq_pair)())()
w_n_sq_pair = A.Multiply(w_n, w_n, w_r3)()
w_n_sq = M.Head(w_n_sq_pair)()
w_r4 = M.Head(M.Tail(w_n_sq_pair)())()
w_plus_pair = A.Add(w_m, w_n, w_r4)()
w_plus = M.Head(w_plus_pair)()
w_r5 = M.Head(M.Tail(w_plus_pair)())()
w_minus_pair = M.NatFromRep(M.GMPRep("1"), w_r5)()
w_minus = M.Head(w_minus_pair)()
w_r6 = M.Head(M.Tail(w_minus_pair)())()
w_a_pair = M.NatFromRep(M.GMPRep("3"), w_r6)()
w_a = M.Head(w_a_pair)()
w_r7 = M.Head(M.Tail(w_a_pair)())()
w_factored_pair = A.Multiply(w_minus, w_plus, w_r7)()
w_factored = M.Head(w_factored_pair)()
w_r8 = M.Head(M.Tail(w_factored_pair)())()
assert M.NatEq(w_factored, w_a, w_r8)() is M.truth_value, "conjecture (m-n)(m+n) = m^2-n^2 failed"
assert A.IsCoprime(w_minus, w_plus, w_r8)() is M.truth_value, "conjecture coprime(m-n, m+n) failed"
w_c_pair = A.Add(w_m_sq, w_n_sq, w_r8)()
w_c = M.Head(w_c_pair)()
w_r9 = M.Head(M.Tail(w_c_pair)())()
w_a_sq_pair = A.Multiply(w_a, w_a, w_r9)()
w_a_sq = M.Head(w_a_sq_pair)()
w_r10 = M.Head(M.Tail(w_a_sq_pair)())()
w_two_pair = M.NatFromRep(M.GMPRep("2"), w_r10)()
w_two = M.Head(w_two_pair)()
w_r11 = M.Head(M.Tail(w_two_pair)())()
w_mn_pair = A.Multiply(w_m, w_n, w_r11)()
w_mn = M.Head(w_mn_pair)()
w_r12 = M.Head(M.Tail(w_mn_pair)())()
w_b_pair = A.Multiply(w_two, w_mn, w_r12)()
w_b = M.Head(w_b_pair)()
w_r13 = M.Head(M.Tail(w_b_pair)())()
w_b_sq_pair = A.Multiply(w_b, w_b, w_r13)()
w_b_sq = M.Head(w_b_sq_pair)()
w_r14 = M.Head(M.Tail(w_b_sq_pair)())()
w_c_sq_pair = A.Multiply(w_c, w_c, w_r14)()
w_c_sq = M.Head(w_c_sq_pair)()
w_r15 = M.Head(M.Tail(w_c_sq_pair)())()
w_lhs_pair = A.Add(w_a_sq, w_b_sq, w_r15)()
w_lhs = M.Head(w_lhs_pair)()
w_r16 = M.Head(M.Tail(w_lhs_pair)())()
assert M.NatEq(w_lhs, w_c_sq, w_r16)() is M.truth_value, "conjecture a^2 + b^2 = c^2 failed"

x_p_pair = M.NatFromRep(M.GMPRep("2"), registry)()
x_p = M.Head(x_p_pair)()
x_r1 = M.Head(M.Tail(x_p_pair)())()
x_q_pair = M.NatFromRep(M.GMPRep("1"), x_r1)()
x_q = M.Head(x_q_pair)()
x_r2 = M.Head(M.Tail(x_q_pair)())()
x_p_sq_pair = A.Multiply(x_p, x_p, x_r2)()
x_p_sq = M.Head(x_p_sq_pair)()
x_r3 = M.Head(M.Tail(x_p_sq_pair)())()
x_q_sq_pair = A.Multiply(x_q, x_q, x_r3)()
x_q_sq = M.Head(x_q_sq_pair)()
x_r4 = M.Head(M.Tail(x_q_sq_pair)())()
x_p4_pair = A.Multiply(x_p_sq, x_p_sq, x_r4)()
x_p4 = M.Head(x_p4_pair)()
x_r4b = M.Head(M.Tail(x_p4_pair)())()
x_q4_pair = A.Multiply(x_q_sq, x_q_sq, x_r4b)()
x_q4 = M.Head(x_q4_pair)()
x_r4c = M.Head(M.Tail(x_q4_pair)())()
x_r_pair = A.Add(x_p_sq, x_q_sq, x_r4c)()
x_r = M.Head(x_r_pair)()
x_r5 = M.Head(M.Tail(x_r_pair)())()
x_s_pair = M.NatFromRep(M.GMPRep("3"), x_r5)()
x_s = M.Head(x_s_pair)()
x_r6 = M.Head(M.Tail(x_s_pair)())()
x_r_sq_pair = A.Multiply(x_r, x_r, x_r6)()
x_r_sq = M.Head(x_r_sq_pair)()
x_r7 = M.Head(M.Tail(x_r_sq_pair)())()
x_s_sq_pair = A.Multiply(x_s, x_s, x_r7)()
x_s_sq = M.Head(x_s_sq_pair)()
x_r8 = M.Head(M.Tail(x_s_sq_pair)())()
x_u_sq_pair = A.Add(x_p4, x_q4, x_r8)()
x_u_sq = M.Head(x_u_sq_pair)()
x_r9 = M.Head(M.Tail(x_u_sq_pair)())()
x_two_pair = M.NatFromRep(M.GMPRep("2"), x_r9)()
x_two = M.Head(x_two_pair)()
x_r10 = M.Head(M.Tail(x_two_pair)())()
x_twice_pair = A.Multiply(x_two, x_u_sq, x_r10)()
x_twice = M.Head(x_twice_pair)()
x_r11 = M.Head(M.Tail(x_twice_pair)())()
x_sum_pair = A.Add(x_r_sq, x_s_sq, x_r11)()
x_sum = M.Head(x_sum_pair)()
x_r12 = M.Head(M.Tail(x_sum_pair)())()
assert M.NatEq(x_sum, x_twice, x_r12)() is M.truth_value, "conjecture r^2 + s^2 = 2u^2 failed"
x_four_pair = M.NatFromRep(M.GMPRep("4"), x_r12)()
x_four = M.Head(x_four_pair)()
x_r13 = M.Head(M.Tail(x_four_pair)())()
x_pq_pair = A.Multiply(x_p, x_q, x_r13)()
x_pq = M.Head(x_pq_pair)()
x_r14 = M.Head(M.Tail(x_pq_pair)())()
x_pq_sq_pair = A.Multiply(x_pq, x_pq, x_r14)()
x_pq_sq = M.Head(x_pq_sq_pair)()
x_r15 = M.Head(M.Tail(x_pq_sq_pair)())()
x_four_pq_sq_pair = A.Multiply(x_four, x_pq_sq, x_r15)()
x_four_pq_sq = M.Head(x_four_pq_sq_pair)()
x_r16 = M.Head(M.Tail(x_four_pq_sq_pair)())()
x_relapse_pair = A.Add(x_s_sq, x_four_pq_sq, x_r16)()
x_relapse = M.Head(x_relapse_pair)()
x_r17 = M.Head(M.Tail(x_relapse_pair)())()
assert M.NatEq(x_r_sq, x_relapse, x_r17)() is M.truth_value, "conjecture r^2 = s^2 + 4p^2q^2 failed"
x_one_pair = M.NatFromRep(M.GMPRep("1"), x_r17)()
x_one = M.Head(x_one_pair)()
x_r18 = M.Head(M.Tail(x_one_pair)())()
x_corrupt_pair = A.Add(x_relapse, x_one, x_r18)()
x_corrupt = M.Head(x_corrupt_pair)()
x_r19 = M.Head(M.Tail(x_corrupt_pair)())()
assert M.NatEq(x_r_sq, x_corrupt, x_r19)() is M.false_value, (
    "the corrupted near-miss identity must be refuted"
)
print("    Lemmas verified on instances; the corrupted near-miss refuted.")
print()

# --- [7] the learned schema must earn its promotion -------------------------
print("[7] Gated promotion: Checker B, ablation, withheld holdouts, then commit...")
macro_id = M.Atom()
candidate = Eval.CandidateMacro(macro_id, descent_start, descent_goal, plan)()
receipt_pair = Eval.EvaluateCandidateProof(
    candidate, descent_start, descent_goal, conjectures, registry
)()
assert M.IdentityCompare(M.Head(receipt_pair)(), L.CandidateEvaluatedLabel)() is M.truth_value, (
    "Checker B must verify the candidate proof"
)
proof_receipt = M.Head(M.Tail(receipt_pair)())()
assert M.IdentityCompare(M.Head(proof_receipt)(), L.ProofReceiptLabel)() is M.truth_value, (
    "the evaluation must emit a proof receipt"
)
ablation_pair = Eval.AblationTrial(candidate, descent_start, descent_goal, conjectures, registry)()
assert M.IdentityCompare(M.Head(ablation_pair)(), L.AblationVerifiedLabel)() is M.truth_value, (
    "the ablation trial must pass"
)
assert M.IdentityCompare(M.Head(M.Tail(M.Tail(ablation_pair)())())(), L.ProvedLabel)() is M.truth_value, (
    "the ablation must show the schema is not trivially closed"
)
holdout_positive = M.Pair(
    descent_start, M.Pair(descent_goal, M.Pair(M.truth_value, M.EmptyList))
)
holdout_near_miss = M.Pair(
    descent_start, M.Pair(obstruction_goal, M.Pair(M.false_value, M.EmptyList))
)
holdout_unprovable_claim = M.Pair(
    descent_start, M.Pair(obstruction_goal, M.Pair(M.truth_value, M.EmptyList))
)
holdout_suite = M.Pair(holdout_positive, M.Pair(holdout_near_miss, M.EmptyList))
holdout_pair = Eval.EvaluateHoldoutSuite(candidate, holdout_suite, conjectures, registry)()
assert M.IdentityCompare(M.Head(holdout_pair)(), L.HoldoutSuiteResultLabel)() is M.truth_value, (
    "the holdout suite must report a result"
)
holdout_passed = M.Head(M.Tail(holdout_pair)())()
holdout_failed = M.Head(M.Tail(M.Tail(holdout_pair)())())()
assert M.IdentityCompare(holdout_failed, M.EmptyList)() is M.truth_value, (
    "no withheld instance may fail the learned schema"
)
assert M.IdentityCompare(M.Tail(holdout_passed)(), M.EmptyList)() is M.false_value, (
    "the withheld near-miss must be recorded as passed"
)

baseline_eight_pair = M.NatFromRep(M.GMPRep("8"), registry)()
baseline_eight = M.Head(baseline_eight_pair)()
baseline_reg = M.Head(M.Tail(baseline_eight_pair)())()
baseline_cost = P.ProofCost(baseline_eight, M.Zero, M.Zero, M.Zero)()
ledger_empty = Ledger.EmptyPromotionLedger(registry)()
assert M.IdentityCompare(Ledger.PromotionLedgerVersion(ledger_empty)(), M.Zero)() is M.truth_value, (
    "a fresh ledger starts at version zero"
)
promotion = Ledger.SubmitCandidateForPromotion(
    ledger_empty,
    candidate,
    L.ProofSchemaPromotionLabel,
    descent_start,
    descent_goal,
    baseline_cost,
    holdout_suite,
    M.EmptyList,
    conjectures,
    registry,
)()
assert M.IdentityCompare(M.Head(promotion)(), L.PromotionApprovedLabel)() is M.truth_value, (
    "the schema must pass every gate"
)
ledger_one = M.Head(M.Tail(promotion)())()
promoted_entry = M.Head(M.Tail(M.Tail(promotion)())())()
assert M.IdentityCompare(Ledger.LedgerEntryStatus(promoted_entry)(), L.PromotionActiveLabel)() is M.truth_value, (
    "the promoted entry must be active"
)
assert M.Compare(Ledger.LedgerEntryCandidate(promoted_entry)(), candidate)() is M.truth_value, (
    "the ledger must record the learned schema"
)
assert M.Compare(Ledger.LedgerEntryReceipt(promoted_entry)(), proof_receipt)() is M.truth_value, (
    "the ledger must record the Checker B receipt"
)
assert M.NatEq(Ledger.PromotionLedgerVersion(ledger_one)(), M.one, registry)() is M.truth_value, (
    "the promoted ledger must advance to version one"
)

rejection = Ledger.SubmitCandidateForPromotion(
    ledger_one,
    candidate,
    L.ProofSchemaPromotionLabel,
    descent_start,
    descent_goal,
    baseline_cost,
    M.Pair(holdout_unprovable_claim, M.EmptyList),
    M.EmptyList,
    conjectures,
    registry,
)()
assert M.IdentityCompare(M.Head(rejection)(), L.PromotionRejectedLabel)() is M.truth_value, (
    "a failing holdout must block promotion"
)
assert M.NatEq(Ledger.PromotionLedgerVersion(ledger_one)(), M.one, registry)() is M.truth_value, (
    "the ledger must not move on a rejected candidate"
)
print("    Schema promoted with receipt; the failing holdout was rejected.")
print()

# --- [8] replay from the promoted ledger ------------------------------------
print("[8] Replay: the promoted schema reproduces the derivation...")
active = Ledger.QueryActivePromotions(ledger_one, L.ProofSchemaPromotionLabel, registry)()
assert M.IdentityCompare(active, M.EmptyList)() is M.false_value, "the ledger must hold an active schema"
active_macro = Ledger.LedgerEntryCandidate(M.Head(active)())()
replay_pair = Eval.ExpandCandidateMacro(active_macro, descent_start, descent_goal, registry)()
assert M.IdentityCompare(M.Head(replay_pair)(), L.CandidateExpandedLabel)() is M.truth_value, (
    "the promoted schema must expand"
)
replay_derivation = M.Head(M.Tail(replay_pair)())()
replay_registry = M.Head(M.Tail(M.Tail(replay_pair)())())()
replay_end = P.DerivationEnd(replay_derivation, replay_registry)()
assert P.FactsCover(P.KnowledgeFacts(descent_goal)(), P.KnowledgeFacts(replay_end)())() is M.truth_value, (
    "the replayed derivation must cover the goal"
)
verification = CheckerB.VerifyDerivation(
    replay_derivation, descent_start, descent_goal, conjectures, replay_registry
)()
assert M.IdentityCompare(M.Head(verification)(), L.DerivationVerifiedLabel)() is M.truth_value, (
    "Checker B must verify the replayed derivation"
)
print("    Promoted schema replayed and independently verified.")
print()

print("=== ALL TEST 16 LIVE SESSION CHECKS PASSED in %.3fs ===" % (time.time() - t0))
