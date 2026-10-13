# ============================================================
# TEST 22: IMO combinatorics — families 1 and 2 delivered
#
# FAMILY 1 (sections [0]-[12]): discrete combinatorial configurations
# as fact hypergraphs closed by generic multi-premise rules, with the
# terminating invariant found by invariant_miner.py.
#
# FAMILY 2 (sections [13]-[20]): functional equations as rewrite
# schemas — the equation is DATA (an ExprEq term), compiled by a
# generic machine edge into a unary rewrite schema whose consequences
# are derived, closed, and Checker-B-verified.
#
# Delegation slot: W09 "IMO combinatorics / functional equations",
# families 1 and 2 of 3 (see delegation/W09-imo-combinatorics-funceq.md).
#
# WHAT THIS SUITE DERIVES (machine rules only, no authored answers):
#   [family 1] A generic collision rule over an opaque fact hypergraph —
#       residue(x,r) & residue(y,r) & distinct(x,y)
#           -> shares_class(x,y) & residue(x,r) & residue(y,r)
#   — is closed by the machine's own forward engine over a concrete
#   configuration (three values assigned to two classes).  The mined
#   persistence invariant (an element's class assignment survives the
#   rule) is machine-verified as preserved; a rival candidate
#   (distinctness survives) is machine-refuted.  The same invariant
#   drives a machine proof that the near-miss (injective) configuration
#   cannot reach a collision-only state.  A generic candidate macro
#   built from the trace is verified step-by-step by Checker B, passes
#   a held-out suite of positives and near-miss negatives, is promoted
#   through the ledger with the invariant certificate as provenance,
#   and the decoy claim (collision from an injective configuration) is
#   refused at the promotion gate with a machine-stated reason.
#   [family 2] Cauchy's additive equation, as data, is compiled into a
#   rewrite schema by a generic machine edge (math/funceq.py); the
#   machine closes f((x+y)+z) under that schema to the expanded normal
#   form f(x)+f(y)+f(z) with machine-checked termination evidence,
#   verifies the two-step expansion (root step + path step) under
#   Checker B, and shows the multiplicative claim is NOT derivable from
#   the additive schema.  A second equation (multiplicative Cauchy)
#   goes through the same compiler unchanged, and a generic consequence
#   macro is promoted by the ledger while the decoy claim is refused.
#
# WHAT THIS SUITE DOES NOT DERIVE (stated, and machine-checked where
# checkable — see the boundary sections at the end):
#   [family 1] the counting bound "n+1 values into n classes forces a
#     collision" is NOT mechanized (no cardinality reasoning); the
#     arithmetic reading "same class <=> difference divisible by n" is
#     NOT mechanized (no integer/divisibility constructors — the card's
#     own "missing constructors" list); the closure engine instantiates
#     the first join per depth step; PhiReading is first-match, so the
#     unreachability prover is used only where that reading is sound.
#   [family 2] consequences are expansion-level only: cancellation
#     (f(0) = 0), induction (f(nx) = n f(x)) and regularity-based
#     linearity are NOT derived; the equation orients as authored (no
#     reduction order, no termination proof beyond the machine-checked
#     normal form); the invariant miner's first-match preservation
#     semantics does not fit the expansion schema (machine-verified
#     refusals, reported honestly); the curriculum contains no
#     functional-equation cards, so held-out evidence for family 2 is
#     unseen instances plus refused decoys, not curriculum cards.
#   [family 3] number theory (coprimality, divisibility, residues over
#     Peano/GMP) is NOT derived by this suite.
#
# No new labels, no kernel edits, no packs, no curriculum cards
# encoded: instances below are data built from opaque nodes; the
# proposition text lives only in the curriculum corpus.
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
from cat_theo_machine import invariant_miner as Miner
from cat_theo_machine import invariance as Inv
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine import promotion_ledger as Ledger
from cat_theo_machine.math import funceq as FE
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 22: IMO combinatorics family 1 — configuration hypergraphs ===")
print()

# --- [0] runtime, opaque vocabulary, term helpers ---------------------------
print("[0] Initializing runtime and the opaque fact vocabulary...")
runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()

# Relation nodes are opaque ontology vocabulary, not problem answers.
rel_residue = M.Char("residue")
rel_distinct = M.Char("distinct")
rel_shares = M.Char("shares_class")
rel_certified = M.Char("certified")


def var_pattern():
    return M.Pair(M.VarTag, M.Pair(M.Var(), M.EmptyList))


def fact(rel, x, y):
    return M.Pair(rel, M.Pair(x, M.Pair(y, M.EmptyList)))


def chain(items):
    out = M.EmptyList
    for item in reversed(items):
        out = M.Pair(item, out)
    return out


def to_list(term):
    out = []
    cur = term
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        out.append(M.Head(cur)())
        cur = M.Tail(cur)()
    return out


def contains(facts, target):
    for f in facts:
        if M.Compare(f, target)() is M.truth_value:
            return True
    return False


def count_head(facts, rel):
    n = 0
    for f in facts:
        if M.IdentityCompare(M.Head(f)(), rel)() is M.truth_value:
            n += 1
    return n


def knowledge(items):
    return P.Knowledge(chain(items))()


def label_name(term):
    return type(term).__name__


def machine_nat(n):
    t = M.Zero
    for _ in range(n):
        t = M.Head(M.Succ(t, registry)())()
    return t


vx, vy, vr = var_pattern(), var_pattern(), var_pattern()
print("    Vocabulary: residue / distinct / shares_class / certified (opaque nodes).")
print()

# --- [1] the generic multi-premise collision rule ---------------------------
print("[1] The generic collision rule (multi-premise, fact-list replacement)...")
# Same-class + distinctness  =>  the pair is related; both class
# assignments are re-stated so the rewrite preserves them.
premises = chain([
    fact(rel_residue, vx, vr),
    fact(rel_residue, vy, vr),
    fact(rel_distinct, vx, vy),
])
replacement = chain([
    fact(rel_shares, vx, vy),
    fact(rel_residue, vx, vr),
    fact(rel_residue, vy, vr),
])
rule_collision = P.MultiRule(premises, replacement)()
trusted_rules = M.Pair(rule_collision, M.EmptyList)
assert P.ReplacementIsFactList(rule_collision)() is M.truth_value
print("    premises:    " + M.PrettyTerm(premises, registry)())
print("    replacement: " + M.PrettyTerm(replacement, registry)())

# Soundness audit rule: a derived relation must be backed by a shared class.
audit_premises = chain([
    fact(rel_shares, vx, vy),
    fact(rel_residue, vx, vr),
    fact(rel_residue, vy, vr),
])
audit_replacement = chain([fact(rel_certified, vx, vy)])
rule_audit = P.MultiRule(audit_premises, audit_replacement)()
audited_rules = chain([rule_collision, rule_audit])
print("    audit rule:  " + M.PrettyTerm(audit_premises, registry)())
print("                -> " + M.PrettyTerm(audit_replacement, registry)())
print()

# --- [2] the machine closes a concrete configuration ------------------------
# Instance data (opaque nodes): three values s0,s1,s2 assigned to two
# classes r0,r1, pairwise distinct.  The colliding pair is (s0,s2).
s0, s1, s2 = M.Char("s0"), M.Char("s1"), M.Char("s2")
r0, r1 = M.Char("r0"), M.Char("r1")
config = chain([
    fact(rel_residue, s0, r0), fact(rel_residue, s1, r1), fact(rel_residue, s2, r0),
    fact(rel_distinct, s0, s1), fact(rel_distinct, s0, s2), fact(rel_distinct, s1, s2),
])
print("[2] Closing the configuration with the machine's forward engine...")
closure = GT.ForwardDeriveFacts(config, trusted_rules, machine_nat(3), registry)()
closure_facts = to_list(closure)
for f in closure_facts:
    print("      " + M.PrettyTerm(f, registry)())
assert contains(closure_facts, fact(rel_shares, s0, s2)), (
    "the closure must derive the collision shares_class(s0,s2)"
)
spurious = [
    f for f in closure_facts
    if not contains(to_list(config), f)
    and M.Compare(f, fact(rel_shares, s0, s2))() is M.false_value
]
assert not spurious, "the closure must not derive anything beyond the collision"
print("    OK: closure is exactly the configuration plus shares_class(s0,s2).")
print()

# --- [3] soundness: every derived collision is class-backed ------------------
print("[3] Auditing the closure: every collision must be class-certified...")
audited_closure = to_list(
    GT.ForwardDeriveFacts(config, audited_rules, machine_nat(3), registry)()
)
n_shares = count_head(audited_closure, rel_shares)
n_certified = count_head(audited_closure, rel_certified)
print(f"    derived shares_class facts: {n_shares}; certified facts: {n_certified}")
assert n_shares >= 1, "at least one collision must be derived"
assert n_certified == n_shares, (
    "every derived collision must be certified by a shared class"
)
assert contains(audited_closure, fact(rel_certified, s0, s2))
print("    OK: each derived collision carries a machine certification.")
print()

# --- [4] the near-miss configuration: no collision, and the counting bound
#         is NOT mechanized (boundary, machine-checked) ----------------------
print("[4] Near-miss configuration (three values, three distinct classes)...")
a, b, c = M.Char("a"), M.Char("b"), M.Char("c")
k0, k1, k2 = M.Char("k0"), M.Char("k1"), M.Char("k2")
injective = chain([
    fact(rel_residue, a, k0), fact(rel_residue, b, k1), fact(rel_residue, c, k2),
    fact(rel_distinct, a, b), fact(rel_distinct, a, c), fact(rel_distinct, b, c),
])
injective_closure = GT.ForwardDeriveFacts(injective, trusted_rules, machine_nat(3), registry)()
assert M.Compare(injective_closure, injective)() is M.truth_value, (
    "an injective configuration must close to itself: no collision is derivable"
)
injective_audited = to_list(
    GT.ForwardDeriveFacts(injective, audited_rules, machine_nat(3), registry)()
)
assert count_head(injective_audited, rel_shares) == 0
assert count_head(injective_audited, rel_certified) == 0
print("    OK: the injective configuration derives no collision and no certificate.")
print("    NOTE: the engine sees a perfectly consistent configuration here — the")
print("    counting bound (3 values into 3 classes is fine) is NOT mechanized;")
print("    the machine cannot infer from sizes alone that a collision must exist.")
print()

# --- [5] mining the terminating invariant from the trace ---------------------
print("[5] Building the training trace and mining the persistence invariant...")
inst_start = knowledge([
    fact(rel_residue, a, k0), fact(rel_residue, b, k0), fact(rel_distinct, a, b),
])
join_res = P.JoinPremises(
    P.RulePremises(rule_collision)(), P.KnowledgeFacts(inst_start)(), M.EmptyList
)()
assert M.IdentityCompare(join_res, M.EmptyList)() is M.false_value, (
    "the premises must join against the configuration"
)
inst_bindings = M.Head(join_res)()
inst_next = P.ApplyKnowledgeRewrite(inst_start, rule_collision, inst_bindings)()
print("    successor:   " + M.PrettyTerm(P.KnowledgeFacts(inst_next)(), registry)())
action = P.TheoremAction(rule_collision, inst_bindings)()
step_pair = P.Step(inst_start, action, inst_next, registry)()
step = M.Head(step_pair)()
reg_after_step = M.Head(M.Tail(step_pair)())()
cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
der_pair = P.Derivation(M.Pair(step, M.EmptyList), cost_zero, reg_after_step)()
trace = M.Head(der_pair)()
registry = M.Head(M.Tail(der_pair)())()

phi_residue = Inv.Phi(fact(rel_residue, vx, vr))()
phi_distinct = Inv.Phi(fact(rel_distinct, vx, vy))()
templates = M.Pair(phi_residue, M.Pair(phi_distinct, M.EmptyList))

pres_residue = Miner.CheckInvariantPreservationAcrossRules(
    phi_residue, trusted_rules, registry
)()
assert M.IdentityCompare(M.Head(pres_residue)(), M.truth_value)() is M.truth_value, (
    "the class-assignment invariant must be preserved by the collision rule"
)
pres_distinct = Miner.CheckInvariantPreservationAcrossRules(
    phi_distinct, trusted_rules, registry
)()
assert M.IdentityCompare(M.Head(pres_distinct)(), M.false_value)() is M.truth_value, (
    "the distinctness candidate must be refuted"
)
refutation = M.Head(M.Tail(M.Tail(pres_distinct)())())()
assert M.IdentityCompare(M.Head(refutation)(), L.InvariantRefutedLabel)() is M.truth_value
print("    OK: residue-assignment invariant PRESERVED (machine-verified);")
print("        distinctness candidate REFUTED (machine-verified).")

mine_res = Miner.MineInvariantFromTrace(trace, inst_start, trusted_rules, templates, registry)()
assert M.IdentityCompare(M.Head(mine_res)(), M.truth_value)() is M.truth_value, (
    "the miner must find a preserved invariant from the trace"
)
certificate = M.Head(M.Tail(mine_res)())()
cert_phi = Miner.InvariantCertificatePhi(certificate)()
assert M.Compare(cert_phi, phi_residue)() is M.truth_value, (
    "the mined certificate must carry the residue-assignment invariant"
)
print("    OK: invariant certificate issued by the miner.")
print()

# --- [6] ablation: the invariant is what terminates the argument -------------
print("[6] Ablation — with the mined invariant vs. with the refuted candidate...")
collision_only_goal = knowledge([fact(rel_shares, a, b)])
injective_state = P.Knowledge(injective)()
with_invariant = Miner.UnreachabilityProverByInvariant(
    injective_state, collision_only_goal, trusted_rules, phi_residue, registry
)()
assert M.IdentityCompare(M.Head(with_invariant)(), L.UnreachableLabel)() is M.truth_value, (
    "the mined invariant must certify the collision-only state as unreachable"
)
ablated = Miner.UnreachabilityProverByInvariant(
    injective_state, collision_only_goal, trusted_rules, phi_distinct, registry
)()
assert M.IdentityCompare(M.Head(ablated)(), L.InvariantRefutedLabel)() is M.truth_value, (
    "without a preserved invariant the argument cannot terminate"
)
print("    with mined phi:      " + label_name(M.Head(with_invariant)()))
print("    with refuted phi':   " + label_name(M.Head(ablated)()))
print("    OK: the invariant measurably supplies the termination certificate;")
print("        the refuted candidate leaves the argument open.")
print()

# --- [7] the decoy claim is unreachable; the positive instance is not --------
#         accused by the prover's first-match reading (limitation, not
#         asserted — the positive instance is cleared by Checker B in [9]).
print("[7] Unreachability of the decoy claim, and the reading limitation...")
unreach = Miner.UnreachabilityProverByInvariant(
    injective_state, collision_only_goal, trusted_rules, phi_residue, registry
)()
assert M.IdentityCompare(M.Head(unreach)(), L.UnreachableLabel)() is M.truth_value
phi_start = Inv.PhiReading(injective_state, phi_residue)()
phi_target = Inv.PhiReading(collision_only_goal, phi_residue)()
assert M.Compare(phi_start, phi_target)() is M.false_value
print("    phi(injective config) = " + M.PrettyTerm(phi_start, registry)())
print("    phi(collision-only state) = " + M.PrettyTerm(phi_target, registry)())
positive_direction = Miner.UnreachabilityProverByInvariant(
    inst_start, inst_next, trusted_rules, phi_residue, registry
)()
print("    NOTE: the prover's reading is first-match, so it is NOT canonical")
print("    across states with several invariant witnesses; the positive")
print("    direction reading (" + label_name(M.Head(positive_direction)) + ") is a")
print("    measured limitation, not asserted — the positive instance is cleared")
print("    by the Checker-B-verified derivation below, not by the prover.")
print()

# --- [8] the generic candidate macro, verified by Checker B ------------------
print("[8] Generic candidate macro (same-class pair -> related pair)...")
start_pattern = knowledge([
    fact(rel_residue, vx, vr), fact(rel_residue, vy, vr), fact(rel_distinct, vx, vy),
])
goal_pattern = knowledge([fact(rel_shares, vx, vy)])
plan = M.Pair(P.TheoremAction(rule_collision, M.EmptyList)(), M.EmptyList)
macro_id = M.Atom()
macro = Eval.CandidateMacro(macro_id, start_pattern, goal_pattern, plan)()
inst_goal = collision_only_goal
eval_res = Eval.EvaluateCandidateProof(macro, inst_start, inst_goal, trusted_rules, registry)()
assert M.IdentityCompare(M.Head(eval_res)(), L.CandidateEvaluatedLabel)() is M.truth_value, (
    "the candidate proof must be verified by Checker B"
)
receipt = M.Head(M.Tail(eval_res)())()
assert M.IdentityCompare(M.Head(receipt)(), L.ProofReceiptLabel)() is M.truth_value
print("    OK: Checker B verified the expansion; proof receipt issued.")
print()

# --- [9] ablation trial: the proof is non-trivial ----------------------------
print("[9] Ablation trial (the proof must do real work)...")
ablation = Eval.AblationTrial(macro, inst_start, inst_goal, trusted_rules, registry)()
assert M.IdentityCompare(M.Head(ablation)(), L.AblationVerifiedLabel)() is M.truth_value
ablation_status = M.Head(M.Tail(M.Tail(ablation)())())()
assert M.IdentityCompare(ablation_status, L.ProvedLabel)() is M.truth_value, (
    "start != goal, so the derivation must be non-trivial"
)
print("    OK: ablation ProvedLabel — the collision is not vacuously closed.")
print()

# --- [10] held-out suite: positives and near-miss negatives ------------------
print("[10] Held-out suite (3 positives + 3 near-miss negatives)...")
p, q = M.Char("p"), M.Char("q")
g, h = M.Char("g"), M.Char("h")
m_, n_ = M.Char("m"), M.Char("n")
u, v = M.Char("u"), M.Char("v")
k3, k5 = M.Char("k3"), M.Char("k5")

pos1 = M.Pair(inst_start, M.Pair(collision_only_goal, M.Pair(M.truth_value, M.EmptyList)))
# held-out-card core: the colliding prefix-sum pair shares a class.
heldout_core_start = knowledge([
    fact(rel_residue, s0, r0), fact(rel_residue, s2, r0), fact(rel_distinct, s0, s2),
])
heldout_core_goal = knowledge([fact(rel_shares, s0, s2)])
pos2 = M.Pair(heldout_core_start, M.Pair(heldout_core_goal, M.Pair(M.truth_value, M.EmptyList)))
fresh_start = knowledge([
    fact(rel_residue, g, k5), fact(rel_residue, h, k5), fact(rel_distinct, g, h),
])
fresh_goal = knowledge([fact(rel_shares, g, h)])
pos3 = M.Pair(fresh_start, M.Pair(fresh_goal, M.Pair(M.truth_value, M.EmptyList)))
# near-miss 1: different classes (the modulus must match).
neg1_start = knowledge([
    fact(rel_residue, m_, k2), fact(rel_residue, n_, k3), fact(rel_distinct, m_, n_),
])
neg1 = M.Pair(neg1_start, M.Pair(knowledge([fact(rel_shares, m_, n_)]), M.Pair(M.false_value, M.EmptyList)))
# near-miss 2: the held-out card's negative control — only n values, injective.
neg2_start = knowledge([
    fact(rel_residue, u, r0), fact(rel_residue, v, r1), fact(rel_distinct, u, v),
])
neg2 = M.Pair(neg2_start, M.Pair(knowledge([fact(rel_shares, u, v)]), M.Pair(M.false_value, M.EmptyList)))
# near-miss 3: the goal names a pair the configuration cannot relate.
neg3_goal = knowledge([fact(rel_shares, a, c)])
neg3 = M.Pair(inst_start, M.Pair(neg3_goal, M.Pair(M.false_value, M.EmptyList)))

holdouts = chain([pos1, pos2, pos3, neg1, neg2, neg3])
suite_res = Eval.EvaluateHoldoutSuite(macro, holdouts, trusted_rules, registry)()
assert M.IdentityCompare(M.Head(suite_res)(), L.HoldoutSuiteResultLabel)() is M.truth_value
passed = to_list(M.Head(M.Tail(suite_res)())())
failed = to_list(M.Head(M.Tail(M.Tail(suite_res)())())())
print(f"    passed: {len(passed)}, failed: {len(failed)}")
assert len(passed) == 6, f"all six holdout items must behave as expected: {len(passed)}"
assert len(failed) == 0, f"no holdout item may fail: {len(failed)}"
print("    OK: positives verified; near-miss negatives rejected as expected.")
print()

# --- [11] promotion ledger: promote the verified schema, refuse the decoy ----
print("[11] Promotion ledger — autonomous cycle, then the decoy refusal...")
baseline_cost = P.ProofCost(machine_nat(1), M.Zero, M.Zero, M.Zero)()
empty_ledger = Ledger.EmptyPromotionLedger(registry)()
assert M.IdentityCompare(Ledger.PromotionLedgerVersion(empty_ledger)(), M.Zero)() is M.truth_value

cycle_res = Ledger.ExecuteAutonomousDiscoveryCycle(
    trace, start_pattern, goal_pattern, trusted_rules, templates, macro_id, plan,
    baseline_cost, holdouts, L.ProofSchemaPromotionLabel, empty_ledger, registry,
)()
assert M.IdentityCompare(M.Head(cycle_res)(), L.AutonomousCycleCompletedLabel)() is M.truth_value, (
    "the verified cycle must complete: trace -> miner -> macro -> checker -> ledger"
)
ledger_v1 = M.Head(M.Tail(cycle_res)())()
promoted_entry = M.Head(M.Tail(M.Tail(cycle_res)())())()
assert M.IdentityCompare(Ledger.LedgerEntryStatus(promoted_entry)(), L.PromotionActiveLabel)() is M.truth_value
active_v1 = Ledger.QueryActivePromotions(ledger_v1, L.ProofSchemaPromotionLabel, registry)()
assert len(to_list(active_v1)) == 1
print("    OK: schema promoted with the invariant certificate as provenance.")

# Manual submission carrying the mined certificate as provenance: the ledger
# re-verifies the invariant at its own gate (Gate 4) before committing.
manual_ledger = Ledger.EmptyPromotionLedger(registry)()
manual_res = Ledger.SubmitCandidateForPromotion(
    manual_ledger, macro, L.ProofSchemaPromotionLabel, inst_start, inst_goal,
    baseline_cost, holdouts, certificate, trusted_rules, registry,
)()
assert M.IdentityCompare(M.Head(manual_res)(), L.PromotionApprovedLabel)() is M.truth_value, (
    "a receipted, holdout-clean, invariant-certified submission must be approved"
)
print("    OK: manual submission with certificate provenance approved.")

# The decoy claim — collision derivable from an injective configuration —
# must be refused, with a machine-stated reason, and no ledger movement.
decoy_ledger = Ledger.EmptyPromotionLedger(registry)()
refusal = Ledger.SubmitCandidateForPromotion(
    decoy_ledger, macro, L.ProofSchemaPromotionLabel, neg1_start,
    knowledge([fact(rel_shares, m_, n_)]), baseline_cost, holdouts, M.EmptyList,
    trusted_rules, registry,
)()
assert M.IdentityCompare(M.Head(refusal)(), L.PromotionRejectedLabel)() is M.truth_value, (
    "the decoy claim must be refused at the promotion gate"
)
refusal_reason = M.Head(M.Tail(refusal)())()
assert M.IdentityCompare(
    Ledger.PromotionLedgerVersion(decoy_ledger)(), M.Zero
)() is M.truth_value, "a refused submission must not advance the ledger"
assert M.IdentityCompare(
    Ledger.QueryActivePromotions(decoy_ledger, L.ProofSchemaPromotionLabel, registry)(),
    M.EmptyList,
)() is M.truth_value
print("    OK: decoy refused, reason: " + label_name(refusal_reason))
print("        ledger unchanged (version 0, no active promotions).")
print()

# --- [12] boundaries: what fails and why (machine-checked where possible) ----
print("[12] Boundaries — what this suite does NOT establish:")
print("  (a) The counting bound 'n+1 values into n classes forces a collision'")
print("      is NOT mechanized: [4] shows the injective configuration closes to")
print("      itself with no contradiction, i.e. the engine cannot infer from")
print("      sizes alone that a collision must exist; it needs the shared-class")
print("      fact as input.")
print("  (b) The arithmetic reading 'same class <=> difference divisible by n'")
print("      is NOT mechanized: the machine's conclusion is the same-class")
print("      relation itself; no integer/divisibility constructors are used")
print("      (the curriculum card lists them as missing).")
print("  (c) The closure engine instantiates the first join per depth step; it")
print("      does not enumerate all joins ([2] derives one oriented collision).")
print("  (d) PhiReading is first-match; the unreachability prover is therefore")
print("      used only in the sound direction ([6]/[7]) — see the note in [7].")
print("  (e) Family 2 (functional equations) is delivered below in [13]-[20];")
print("      family 3 (number theory over Peano/GMP residues) is NOT derived")
print("      here.")
print()

# ============================================================
# FAMILY 2 — functional equations as rewrite schemas
# ============================================================
print()
print("=== FAMILY 2: functional equations as rewrite schemas ===")
print()


def vp():
    return M.Pair(M.VarTag, M.Pair(M.Var(), M.EmptyList))


def ex_add(x, y):
    return M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(y, M.EmptyList)))


def ex_mul(x, y):
    return M.Pair(L.ExprMulLabel, M.Pair(x, M.Pair(y, M.EmptyList)))


def ex_apply(func, arg):
    return M.Pair(L.ApplyLabel, M.Pair(func, M.Pair(arg, M.EmptyList)))


# --- [13] the equation as data, compiled into a schema -----------------------
print("[13] Cauchy's additive equation as data, compiled to a schema...")
func_f = M.Char("f")
func_g = M.Char("g")
ea, eb, ec = M.Char("a"), M.Char("b"), M.Char("c")
ep, eq, er = M.Char("p"), M.Char("q"), M.Char("r")
eu, ev, ew = M.Char("u"), M.Char("v"), M.Char("w")
vx2, vy2 = vp(), vp()
equation_add = FE.FuncEq(
    ex_apply(func_f, ex_add(vx2, vy2)),
    ex_add(ex_apply(func_f, vx2), ex_apply(func_f, vy2)),
)()
print("    equation: " + M.PrettyTerm(equation_add, registry)())
assert FE.IsEquationTerm(equation_add)() is M.truth_value
assert FE.IsEquationTerm(ex_add(ea, eb))() is M.false_value, (
    "a non-equation term must be refused by the validator"
)
compiled_add = FE.CompileEquationToSchema(equation_add, registry)()
assert M.IdentityCompare(M.Head(compiled_add)(), M.truth_value)() is M.truth_value
schema_add = M.Head(M.Tail(compiled_add)())()
assert P.RuleIsUnary(schema_add)() is M.truth_value
print("    schema pattern:     " + M.PrettyTerm(P.RulePattern(schema_add)(), registry)())
print("    schema replacement: " + M.PrettyTerm(P.RuleReplacement(schema_add)(), registry)())
schema_rules = M.Pair(schema_add, M.EmptyList)
bad_compile = FE.CompileEquationToSchema(ex_add(ea, eb), registry)()
assert M.IdentityCompare(M.Head(bad_compile)(), M.false_value)() is M.truth_value, (
    "the compiler must refuse a non-equation term"
)
print("    OK: equation compiled; non-equation input refused.")
print()

# --- [14] machine closure and normal-form evidence ----------------------------
print("[14] Closing f((a+b)+c) under the compiled schema...")
term_start = ex_apply(func_f, ex_add(ex_add(ea, eb), ec))
print("    start:  " + M.PrettyTerm(term_start, registry)())
closure_add = to_list(FE.CloseTermUnderRules(term_start, schema_rules, machine_nat(4), registry)())
for t in closure_add:
    print("      reachable: " + M.PrettyTerm(t, registry)())
term_expanded = ex_add(ex_add(ex_apply(func_f, ea), ex_apply(func_f, eb)), ex_apply(func_f, ec))
term_one_step = ex_add(ex_apply(func_f, ex_add(ea, eb)), ex_apply(func_f, ec))
assert contains(closure_add, term_expanded), "the expanded form must be reachable"
assert contains(closure_add, term_one_step), "the one-step expansion must be reachable"
assert len(closure_add) == 3, "the closure must be exactly the three expected terms"
assert FE.IsNormalForm(term_expanded, schema_rules, registry)() is M.truth_value, (
    "the fully expanded form must admit no further schema step"
)
assert FE.IsNormalForm(term_start, schema_rules, registry)() is M.false_value
print("    OK: closure is exactly 3 terms; the expanded form is a machine-checked")
print("        normal form (termination evidence for the expansion).")
print()

# --- [15] decoy: multiplicativity is not a consequence of additivity ----------
print("[15] Decoy — multiplicativity claimed from the additive equation...")
term_mul_start = ex_apply(func_f, ex_mul(ea, eb))
term_mul_claim = ex_mul(ex_apply(func_f, ea), ex_apply(func_f, eb))
mul_closure = to_list(FE.CloseTermUnderRules(term_mul_start, schema_rules, machine_nat(4), registry)())
print("    closure of f(a*b): %d term(s); multiplicative claim reachable: %s" % (
    len(mul_closure), contains(mul_closure, term_mul_claim)))
assert len(mul_closure) == 1, "the additive schema must not rewrite f(a*b) at all"
assert not contains(mul_closure, term_mul_claim)
assert FE.IsNormalForm(term_mul_start, schema_rules, registry)() is M.truth_value
print("    OK: the multiplicative consequence is NOT derivable from the additive")
print("        schema — the machine refuses the claim, no authored special case.")
print()

# --- [16] a second equation through the same compiler --------------------------
print("[16] The multiplicative equation through the same generic compiler...")
equation_mul = FE.FuncEq(
    ex_apply(func_g, ex_add(vx2, vy2)),
    ex_mul(ex_apply(func_g, vx2), ex_apply(func_g, vy2)),
)()
compiled_mul = FE.CompileEquationToSchema(equation_mul, registry)()
assert M.IdentityCompare(M.Head(compiled_mul)(), M.truth_value)() is M.truth_value
schema_mul = M.Head(M.Tail(compiled_mul)())()
schema_mul_rules = M.Pair(schema_mul, M.EmptyList)
g_start = ex_apply(func_g, ex_add(ex_add(ea, eb), ec))
g_closure = to_list(FE.CloseTermUnderRules(g_start, schema_mul_rules, machine_nat(4), registry)())
for t in g_closure:
    print("      reachable: " + M.PrettyTerm(t, registry)())
g_expanded = ex_mul(ex_mul(ex_apply(func_g, ea), ex_apply(func_g, eb)), ex_apply(func_g, ec))
assert contains(g_closure, g_expanded) and len(g_closure) == 3
assert FE.IsNormalForm(g_expanded, schema_mul_rules, registry)() is M.truth_value
print("    OK: the compiler is equation-agnostic (additive and multiplicative")
print("        equations both close to their expanded normal forms).")
print()

# --- [17] Checker B over the two-step expansion --------------------------------
print("[17] Checker B over the two-step expansion derivation...")
state_0 = term_start
action_1 = P.RewriteAction(schema_add, M.EmptyList)()
state_1 = P.RewriteAtPath(schema_add, state_0, M.EmptyList, registry)()
step1_pair = P.Step(state_0, action_1, state_1, registry)()
step_1 = M.Head(step1_pair)()
reg_1 = M.Head(M.Tail(step1_pair)())()
inner_path = chain([machine_nat(1), machine_nat(0)])
action_2 = P.RewriteAction(schema_add, inner_path)()
state_2 = P.RewriteAtPath(schema_add, state_1, inner_path, reg_1)()
print("    step 2 at path [1,0]: " + M.PrettyTerm(state_1, registry)())
print("                        -> " + M.PrettyTerm(state_2, registry)())
step2_pair = P.Step(state_1, action_2, state_2, reg_1)()
step_2 = M.Head(step2_pair)()
reg_2 = M.Head(M.Tail(step2_pair)())()
check_1 = CheckerB.VerifyProofStep(
    step_1, schema_rules, M.Pair(state_0, M.EmptyList), M.Pair(state_0, M.EmptyList), reg_1
)()
assert M.IdentityCompare(M.Head(check_1)(), L.StepVerifiedLabel)() is M.truth_value
check_2 = CheckerB.VerifyProofStep(
    step_2, schema_rules, M.Pair(state_1, M.EmptyList), M.Pair(state_1, M.EmptyList), reg_2
)()
assert M.IdentityCompare(M.Head(check_2)(), L.StepVerifiedLabel)() is M.truth_value
der_pair = P.Derivation(
    M.Pair(step_1, M.Pair(step_2, M.EmptyList)), cost_zero, reg_2
)()
trace_fe = M.Head(der_pair)()
reg_fe = M.Head(M.Tail(der_pair)())()
verdict_fe = CheckerB.VerifyDerivation(trace_fe, state_0, term_expanded, schema_rules, reg_fe)()
assert M.IdentityCompare(M.Head(verdict_fe)(), L.DerivationVerifiedLabel)() is M.truth_value
# a recorded successor that the rule cannot reproduce must be refused
tampered_pair = P.Step(state_1, action_2, state_1, reg_2)()
tampered_step = M.Head(tampered_pair)()
reg_tampered = M.Head(M.Tail(tampered_pair)())()
tampered_check = CheckerB.VerifyProofStep(
    tampered_step, schema_rules, M.Pair(state_1, M.EmptyList), M.Pair(state_1, M.EmptyList), reg_tampered
)()
assert M.IdentityCompare(M.Head(tampered_check)(), L.ConclusionMutationLabel)() is M.truth_value
untrusted_check = CheckerB.VerifyProofStep(
    step_2, M.EmptyList, M.Pair(state_1, M.EmptyList), M.Pair(state_1, M.EmptyList), reg_2
)()
assert M.IdentityCompare(M.Head(untrusted_check)(), L.UnknownRuleLabel)() is M.truth_value
print("    OK: both steps verified from the rules alone; a mutated successor is")
print("        refused (%s) and an untrusted rule set is refused (%s)." % (
    label_name(M.Head(tampered_check)()), label_name(M.Head(untrusted_check)())))
print()

# --- [18] the invariant miner's verdict, reported honestly ---------------------
print("[18] What does the invariant miner say about the expansion schema?...")
candidate_phis = chain([
    ex_apply(func_f, vp()),
    ex_add(vp(), vp()),
    ex_mul(vp(), vp()),
    ex_apply(func_f, ex_add(vp(), vp())),
])
cur_phi = candidate_phis
while M.IdentityCompare(cur_phi, M.EmptyList)() is M.false_value:
    phi = M.Head(cur_phi)()
    pres = Miner.CheckInvariantPreservationAcrossRules(phi, schema_rules, reg_fe)()
    verdict = "preserved" if M.IdentityCompare(M.Head(pres)(), M.truth_value)() is M.truth_value else "refuted"
    print("      %-44s -> %s" % (M.PrettyTerm(phi, reg_fe)(), verdict))
    assert M.IdentityCompare(M.Head(pres)(), M.false_value)() is M.truth_value, (
        "no first-match candidate may be reported as preserved for this schema"
    )
    cur_phi = M.Tail(cur_phi)()
mine_fe = Miner.MineInvariantFromTrace(trace_fe, state_0, schema_rules, candidate_phis, reg_fe)()
assert M.IdentityCompare(M.Head(mine_fe)(), M.false_value)() is M.truth_value, (
    "the miner must refuse to certify an invariant for the expansion schema"
)
print("    OK: every candidate is machine-refuted.  The expansion's natural")
print("        invariants (free-variable set preserved; compound-application")
print("        count decreasing) are NOT first-match expressible, so termination")
print("        is evidenced by the machine-checked normal form in [14] instead.")
print()

# --- [19] consequence macro, holdout suite, promotion --------------------------
print("[19] Generic consequence macro, holdout suite, and the ledger...")
vx3, vy3, vz3 = vp(), vp(), vp()
macro_start_pattern = ex_apply(func_f, ex_add(ex_add(vx3, vy3), vz3))
macro_goal_pattern = ex_add(
    ex_add(ex_apply(func_f, vx3), ex_apply(func_f, vy3)), ex_apply(func_f, vz3)
)
macro_plan = M.Pair(
    P.RewriteAction(schema_add, M.EmptyList)(),
    M.Pair(P.RewriteAction(schema_add, inner_path)(), M.EmptyList),
)
macro_id_fe = M.Atom()
macro_fe = Eval.CandidateMacro(macro_id_fe, macro_start_pattern, macro_goal_pattern, macro_plan)()
eval_fe = Eval.EvaluateCandidateProof(macro_fe, state_0, term_expanded, schema_rules, reg_fe)()
assert M.IdentityCompare(M.Head(eval_fe)(), L.CandidateEvaluatedLabel)() is M.truth_value
receipt_fe = M.Head(M.Tail(eval_fe)())()
assert M.IdentityCompare(M.Head(receipt_fe)(), L.ProofReceiptLabel)() is M.truth_value
ablation_fe = Eval.AblationTrial(macro_fe, state_0, term_expanded, schema_rules, reg_fe)()
assert M.IdentityCompare(M.Head(ablation_fe)(), L.AblationVerifiedLabel)() is M.truth_value
assert M.IdentityCompare(
    M.Head(M.Tail(M.Tail(ablation_fe)())())(), L.ProvedLabel
)() is M.truth_value
print("    OK: Checker B verified the expansion; ablation ProvedLabel.")


def holdout_item(start, goal, expected):
    return M.Pair(start, M.Pair(goal, M.Pair(expected, M.EmptyList)))


def expanded_form(func, x, y, z):
    return ex_add(ex_add(ex_apply(func, x), ex_apply(func, y)), ex_apply(func, z))


fe_pos1 = holdout_item(
    ex_apply(func_f, ex_add(ex_add(ep, eq), er)),
    expanded_form(func_f, ep, eq, er), M.truth_value)
fe_pos2 = holdout_item(
    ex_apply(func_f, ex_add(ex_add(eu, ev), ew)),
    expanded_form(func_f, eu, ev, ew), M.truth_value)
fe_neg1 = holdout_item(
    ex_apply(func_f, ex_add(ex_add(ep, eq), er)),
    ex_mul(ex_apply(func_f, ep), ex_apply(func_f, eq)), M.false_value)
fe_neg2 = holdout_item(
    ex_apply(func_g, ex_add(ex_add(ep, eq), er)),
    ex_mul(ex_mul(ex_apply(func_g, ep), ex_apply(func_g, eq)), ex_apply(func_g, er)), M.false_value)
fe_neg3 = holdout_item(
    ex_apply(func_f, ex_add(ex_add(ep, eq), er)),
    ex_add(ex_apply(func_f, ep), ex_apply(func_f, eq)), M.false_value)
fe_neg4 = holdout_item(
    ex_apply(func_f, ex_add(ex_add(ep, eq), er)),
    expanded_form(func_f, ep, eq, ep), M.false_value)
holdouts_fe = chain([fe_pos1, fe_pos2, fe_neg1, fe_neg2, fe_neg3, fe_neg4])
suite_fe = Eval.EvaluateHoldoutSuite(macro_fe, holdouts_fe, schema_rules, reg_fe)()
passed_fe = to_list(M.Head(M.Tail(suite_fe)())())
failed_fe = to_list(M.Head(M.Tail(M.Tail(suite_fe)())())())
print("    holdout suite: passed=%d failed=%d" % (len(passed_fe), len(failed_fe)))
assert len(passed_fe) == 6 and len(failed_fe) == 0
print("    OK: 2 positives (unseen variables) + 4 near-miss negatives.")
# the schema-necessity ablation: without the compiled schema nothing expands
ablated_closure = to_list(FE.CloseTermUnderRules(term_start, M.EmptyList, machine_nat(4), registry)())
assert len(ablated_closure) == 1, "without the schema the term must not expand"
assert M.Compare(ablated_closure[0], term_start)() is M.truth_value
print("    OK: schema ablation — with the schema the closure has 3 terms, without")
print("        it the closure is the term itself (the schema does the work).")

baseline_cost_fe = P.ProofCost(machine_nat(1), M.Zero, M.Zero, M.Zero)()
cycle_fe = Ledger.ExecuteAutonomousDiscoveryCycle(
    trace_fe, macro_start_pattern, macro_goal_pattern, schema_rules, candidate_phis,
    macro_id_fe, macro_plan, baseline_cost_fe, holdouts_fe,
    L.ProofSchemaPromotionLabel, Ledger.EmptyPromotionLedger(registry)(), reg_fe,
)()
assert M.IdentityCompare(M.Head(cycle_fe)(), L.AutonomousCycleCompletedLabel)() is M.truth_value, (
    "the cycle must complete: trace -> miner (refused) -> macro -> checker -> ledger"
)
ledger_fe = M.Head(M.Tail(cycle_fe)())()
entry_fe = M.Head(M.Tail(M.Tail(cycle_fe)())())()
assert M.IdentityCompare(Ledger.LedgerEntryStatus(entry_fe)(), L.PromotionActiveLabel)() is M.truth_value
active_fe = to_list(Ledger.QueryActivePromotions(ledger_fe, L.ProofSchemaPromotionLabel, registry)())
assert len(active_fe) == 1
print("    OK: schema promoted (the ledger still demanded Checker B + holdouts,")
print("        and proceeded without an invariant certificate after the miner refused).")
decoy_ledger_fe = Ledger.EmptyPromotionLedger(registry)()
refusal_fe = Ledger.SubmitCandidateForPromotion(
    decoy_ledger_fe, macro_fe, L.ProofSchemaPromotionLabel,
    term_mul_start, term_mul_claim, baseline_cost_fe, holdouts_fe, M.EmptyList,
    schema_rules, reg_fe,
)()
assert M.IdentityCompare(M.Head(refusal_fe)(), L.PromotionRejectedLabel)() is M.truth_value
assert M.IdentityCompare(
    Ledger.PromotionLedgerVersion(decoy_ledger_fe)(), M.Zero
)() is M.truth_value
assert M.IdentityCompare(
    Ledger.QueryActivePromotions(decoy_ledger_fe, L.ProofSchemaPromotionLabel, registry)(),
    M.EmptyList,
)() is M.truth_value
print("    OK: decoy claim refused, reason: %s; ledger unmoved." % label_name(M.Head(M.Tail(refusal_fe)())()))
print()

# --- [20] family-2 boundaries ---------------------------------------------------
print("[20] Boundaries — what family 2 does NOT establish:")
print("  (a) Consequences are expansion-level only: cancellation (f(0) = 0 from")
print("      f(0+0) = f(0)+f(0)) needs an equational solver that does not exist")
print("      here; induction (f(nx) = n f(x)) and regularity-based linearity are")
print("      not derived.")
print("  (b) The equation orients exactly as authored (lhs -> rhs); no reduction")
print("      order is imposed and no termination proof is attempted beyond the")
print("      machine-checked normal form in [14].")
print("  (c) The invariant miner's first-match preservation semantics does not")
print("      fit the expansion schema: every candidate is machine-refuted ([18]),")
print("      so the closure's normal form — not a mined invariant — carries the")
print("      termination evidence.")
print("  (d) The curriculum contains no functional-equation cards, so held-out")
print("      evidence for family 2 is unseen instances and refused decoys ([19]),")
print("      NOT curriculum held-out cards; no card coverage is claimed.")
print("  (e) Family 3 (number theory over Peano/GMP) is NOT derived here.")
print()

print(
    "=== ALL TEST 22 CHECKS PASSED in %.3fs ===" % (time.time() - t0)
)
