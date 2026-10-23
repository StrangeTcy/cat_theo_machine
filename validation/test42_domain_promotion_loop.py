# ============================================================
# TEST 42: W30 Domain Packs Through the Closed Loop
# ============================================================
# W12's closed loop (miner -> Checker B -> ablation -> ledger) ran
# end-to-end on combinatorics family 1 (test22).  Phase 4b then
# produced derivations in three domains -- funceq/NT (W24), geometry
# (W26), Engel strategies (W10 + W27) -- and test36/test38 promoted
# one schema each in-suite.  This suite drives the loop as such over
# all three domains against ONE shared promotion ledger, with fresh
# instances, and gives the Engel derivations their first Checker-B
# receipts.
#
# Two substrate facts the suite works within, stated plainly:
#
# (1) Knowledge rewrite CONSUMES matched premise facts
#     (DropMatchedFacts drops one occurrence per use).  A derivation
#     is therefore a resource argument: a fact used by k inferences
#     is listed k times in the start state.  The Engel strategy chains
#     reuse Reading / Monovariant facts (the threading rule and the
#     closer both need them), so those facts are listed twice below.
#     This is the same non-monotonicity test23's forward-chaining
#     closure was built around; nothing here changes the semantics.
#
# (2) Candidate macros are single-rule-shaped: their patterns must be
#     the rule's own premise/replacement templates (test36/test38
#     idiom), because ExpandCandidateMacro seeds BuildDerivation with
#     the pattern-match bindings.  A multi-rule strategy plan under
#     seeded bindings produces un-instantiated steps (witnessed while
#     developing this suite).  So the multi-step Engel chains earn
#     receipts via VerifyDerivation [2], and the promoted Engel
#     macros are the two closer rules, whose threaded premises
#     (Invariant / AllMovesDecrease) are exactly what those chains
#     derive.
#
# Two loop strengthenings land with W30 and are exercised here:
#  * Gate-4 provenance for ground observables: a promotion may offer
#    a GroundObservableCertificate (verdict label, descriptor, moves,
#    transitions); the ledger re-runs the ground-transition verifier
#    for every move before trusting it (promotion_ledger.py +
#    invariant_miner.VerifyGroundObservableCertificate).  The mined
#    premise facts are thus re-checked at promotion time, not just
#    at derivation time.  A forged certificate is refused [4].
#  * Withheld-rule ablation (evaluator.py): AblationTrial only checks
#    an instance is not trivially closed; the new trial demands the
#    candidate stops evaluating when its rule is actually removed
#    from the trusted set, and does not cry wolf over unused rules.
#
# Checker B verifies derivations FROM STATED PREMISES.  The receipts
# certify the inference chains; the miner-verified premise facts are
# inputs whose own justification is the transition enumeration
# (re-run by the certificate gate), not the receipt.  The chameleon
# observable is the one mined in test39 -- discovery is not re-run
# here; this suite consumes Phase 4b output, which is W30's remit.
#
# Wall clock is dominated by the miner re-verifications at the
# machine's ~20 ms/op arithmetic rate (~2.5-4 min on 2 vCPU).

import importlib
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PARENT = os.path.dirname(REPO)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine import invariant_miner as Miner
from cat_theo_machine import persistence
from cat_theo_machine.math import arithmetic as Arith
from cat_theo_machine.runtime import make_fresh_runtime

checker_b = importlib.import_module("cat_theo_machine.checker_b")
packs = importlib.import_module("cat_theo_machine.packs")
main_mod = importlib.import_module("cat_theo_machine.main")
Eval = importlib.import_module("cat_theo_machine.evaluator")
Ledger = importlib.import_module("cat_theo_machine.promotion_ledger")

T0 = time.time()
RESULT = []


def check(name, ok, detail=""):
    ok = bool(ok)
    RESULT.append((name, ok, detail))
    line = "    PASS  " if ok else "    FAIL  "
    print(line + name + (("  -- " + str(detail)) if detail else ""))


def section(number, title):
    print()
    print("[%d] %s  (%.1fs elapsed)" % (number, title, time.time() - T0))


runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
EMPTY = M.EmptyList


def _take(pair):
    global registry
    value = M.Head(pair)()
    registry = M.Head(M.Tail(pair)())()
    return value


def nat(value):
    if value == 0:
        return M.Zero
    return _take(M.NatFromRep(M.GMPRep(int(value)), registry)())


def int_of(nat_term):
    return int(M.NatRepOf(nat_term, registry)()())


def succ(term):
    return _take(M.Succ(term, registry)())


def pred(term):
    return _take(M.NatPred(term, registry)())


def succ2(term):
    return succ(succ(term))


def chain(items):
    out = EMPTY
    for item in reversed(items):
        out = M.Pair(item, out)
    return out


def fact(label, *args):
    return M.Pair(label, chain(args))


def call(label, *args):
    return M.Pair(label, chain(args))


def to_list(term):
    out = []
    cursor = term
    while M.IsPair(cursor)() is M.truth_value:
        out.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return out


def count_of(term):
    return int(M.GMPRepText(M.CountRep(term)())())


def head_is(term, label):
    return (M.IsPair(term)() is M.truth_value
            and M.IdentityCompare(M.Head(term)(), label)() is M.truth_value)


def observable(coeffs, modulus=None):
    return Miner.LinearObservable(
        chain([nat(c) for c in coeffs]),
        EMPTY if modulus is None else nat(modulus),
    )()


def reading(obs, state):
    return _take(Miner.LinearObservableValue(obs, state, registry)())


def transition(move, state, next_state):
    return M.Pair(move, M.Pair(state, M.Pair(next_state, EMPTY)))


def positive(term):
    return M.NatEq(term, M.Zero, registry)() is M.false_value


def divides_holds(a, b):
    return Arith.Divides(a, b, registry)() is M.truth_value


print("=== TEST 42: W30 Domain Packs Through the Closed Loop ===")

# ---------------------------------------------------------------------------
# [1] boot; load the three domain packs
# ---------------------------------------------------------------------------

section(1, "Booting and loading the three domain packs")

namespace = main_mod._runtime_namespace()
loader = packs.PackLoader(namespace)


def load(name):
    return loader.load_pack_file(os.path.join(REPO, "packs", name), graph)


funceq_pack = load("funceq-nt.pack.yaml")
geometry_pack = load("geometry-constructions.pack.yaml")
engel_pack = load("engel-strategies.pack.yaml")

check("funceq-nt pack carries its 33 rules",
      count_of(funceq_pack.rule_chain) == 33,
      str(count_of(funceq_pack.rule_chain)) + " rules")
check("geometry pack carries its 9 rules",
      count_of(geometry_pack.rule_chain) == 9,
      str(count_of(geometry_pack.rule_chain)) + " rules")
check("Engel strategy pack carries its 13 rules",
      count_of(engel_pack.rule_chain) == 13,
      str(count_of(engel_pack.rule_chain)) + " rules")

# Raw rule edges by pack id: TheoremAction unwraps compiled rules to
# these, and Checker B matches trusted rules by identity, so plans and
# trusted sets below use the raw objects throughout.
funceq_rules = {rid: obj for rid, obj in funceq_pack.rule_map.entries}
geometry_rules = {rid: obj for rid, obj in geometry_pack.rule_map.entries}
engel_rules = {rid: obj for rid, obj in engel_pack.rule_map.entries}
engel_trusted = chain([obj for _rid, obj in engel_pack.rule_map.entries])

# ---------------------------------------------------------------------------
# [2] Engel receipts: the two W27 chains, Checker-B verified end to end
# ---------------------------------------------------------------------------

section(2, "Engel receipts: full strategy chains through Checker B")

# --- Instance I (chameleons, population 9), as in test39 ---
CHAMELEON = M.Char("chameleon-problem")
MEET12 = M.Char("meet-1-2")
MEET13 = M.Char("meet-1-3")
MEET23 = M.Char("meet-2-3")
CHAMELEON_MOVES = chain([MEET12, MEET13, MEET23])
TOTAL_CH = 9

ch_states = []
for r in range(TOTAL_CH + 1):
    for g in range(TOTAL_CH + 1 - r):
        b = TOTAL_CH - r - g
        rt, gt, bt = nat(r), nat(g), nat(b)
        ch_states.append((rt, gt, bt, chain([rt, gt, bt])))

ch_transitions = []
for rt, gt, bt, state in ch_states:
    if positive(rt) and positive(gt):
        ch_transitions.append(transition(
            MEET12, state, chain([pred(rt), pred(gt), succ2(bt)])))
    if positive(rt) and positive(bt):
        ch_transitions.append(transition(
            MEET13, state, chain([pred(rt), succ2(gt), pred(bt)])))
    if positive(gt) and positive(bt):
        ch_transitions.append(transition(
            MEET23, state, chain([succ2(rt), pred(gt), pred(bt)])))
ch_transitions_term = chain(ch_transitions)
check("chameleon instance rebuilt: 55 states, 108 transitions",
      len(ch_states) == 55 and count_of(ch_transitions_term) == 108)

PHI = observable([0, 1, 2], 3)  # the test39-mined descriptor
print("    verifying the mined observable per move ...")
preserves_facts = []
preserves_ok = True
for move in (MEET12, MEET13, MEET23):
    verdict = _take(Miner.VerifyObservablePreserved(
        move, PHI, ch_transitions_term, registry)())
    if M.Compare(verdict, fact(L.PreservesLabel, move, PHI))() is M.false_value:
        preserves_ok = False
    preserves_facts.append(verdict)
check("the test39-mined phi re-verifies per move (Preserves x3)",
      preserves_ok)

START_CH = chain([nat(2), nat(3), nat(4)])
TARGET_CH = chain([nat(9), nat(0), nat(0)])
TARGET_CH2 = chain([nat(0), nat(9), nat(0)])
SAME_CH = chain([nat(7), nat(2), nat(0)])
start_value = reading(PHI, START_CH)
target_value = reading(PHI, TARGET_CH)
check("start and monochrome readings are machine-apart",
      M.NatEq(start_value, target_value, registry)() is M.false_value)

read_start = fact(L.ReadingLabel, PHI, START_CH, start_value)
read_target = fact(L.ReadingLabel, PHI, TARGET_CH, target_value)
ch_start_facts = chain(
    [fact(L.MoveSetLabel, CHAMELEON, CHAMELEON_MOVES)] + preserves_facts + [
        read_start, read_start,   # used twice: threading + obstruction
        read_target, read_target,
        fact(L.ApartLabel, start_value, target_value),
    ])
ch_start = P.Knowledge(ch_start_facts)()
ch_goal = P.Knowledge(M.Pair(
    fact(L.UnreachableLabel, CHAMELEON, TARGET_CH), EMPTY))()
ch_plan = chain([
    P.TheoremAction(engel_rules["thread_preserving_moves"], EMPTY)(),
    P.TheoremAction(engel_rules["preserving_moves_step"], EMPTY)(),
    P.TheoremAction(engel_rules["preserving_moves_step"], EMPTY)(),
    P.TheoremAction(engel_rules["preserving_moves_step"], EMPTY)(),
    P.TheoremAction(engel_rules["preserving_moves_empty"], EMPTY)(),
    P.TheoremAction(engel_rules["invariant_obstruction"], EMPTY)(),
])
ch_built = P.BuildDerivation(ch_start, ch_plan, registry)()
ch_derivation = M.Head(ch_built)()
ch_deriv_registry = M.Head(M.Tail(ch_built)())()
check("the invariance chain builds as a 6-step derivation",
      count_of(P.DerivationSteps(ch_derivation, ch_deriv_registry)()) == 6)
ch_verdict = checker_b.VerifyDerivation(
    ch_derivation, ch_start, ch_goal, engel_trusted, ch_deriv_registry)()
check("Checker B verifies the chameleon invariance chain to Unreachable",
      head_is(ch_verdict, L.DerivationVerifiedLabel))

wrong_goal = P.Knowledge(M.Pair(
    fact(L.UnreachableLabel, CHAMELEON, SAME_CH), EMPTY))()
check("the decoy state really shares the start reading (machine-checked)",
      M.NatEq(start_value, reading(PHI, SAME_CH), registry)() is M.truth_value)
wrong_verdict = checker_b.VerifyDerivation(
    ch_derivation, ch_start, wrong_goal, engel_trusted, ch_deriv_registry)()
check("  ... and the same derivation is refused against it (GoalMismatch)",
      head_is(wrong_verdict, L.GoalMismatchLabel))

no_closer = chain([obj for rid, obj in engel_pack.rule_map.entries
                   if rid != "invariant_obstruction"])
untrusted_verdict = checker_b.VerifyDerivation(
    ch_derivation, ch_start, ch_goal, no_closer, ch_deriv_registry)()
check("with the closer untrusted the chain is refused (UnknownRule)",
      head_is(untrusted_verdict, L.UnknownRuleLabel))

# --- Instance M (Euclid by subtraction, components 1..12) ---
EUCLID = M.Char("euclid-problem")
SHRINK_LEFT = M.Char("shrink-left")
SHRINK_RIGHT = M.Char("shrink-right")
EUCLID_MOVES = chain([SHRINK_LEFT, SHRINK_RIGHT])
SUM = observable([1, 1])


def euclid_transitions(limit):
    states = []
    for a in range(1, limit + 1):
        for b in range(1, limit + 1):
            at, bt = nat(a), nat(b)
            states.append((at, bt, chain([at, bt])))
    out = []
    for at, bt, st in states:
        if M.NatLess(bt, at, registry)() is M.truth_value:
            d = _take(Arith.NatSubtract(at, bt, registry)())
            out.append(transition(SHRINK_LEFT, st, chain([d, bt])))
        elif M.NatLess(at, bt, registry)() is M.truth_value:
            d = _take(Arith.NatSubtract(bt, at, registry)())
            out.append(transition(SHRINK_RIGHT, st, chain([at, d])))
    return chain(out)


euclid_transitions_term = euclid_transitions(12)
check("Euclid instance rebuilt: 132 transitions over 144 states",
      count_of(euclid_transitions_term) == 132)
print("    verifying the sum measure per move ...")
decrease_facts = []
decrease_ok = True
for move in (SHRINK_LEFT, SHRINK_RIGHT):
    verdict = _take(Miner.VerifyMeasureDecrease(
        move, SUM, euclid_transitions_term, registry)())
    if M.Compare(verdict,
                 fact(L.StrictlyDecreasesLabel, move, SUM))() is M.false_value:
        decrease_ok = False
    decrease_facts.append(verdict)
check("the sum measure re-verifies per move (StrictlyDecreases x2)",
      decrease_ok)

mono_fact = fact(L.MonovariantLabel, EUCLID, SUM)
euclid_start_facts = chain([
    mono_fact, mono_fact,   # used twice: threading + closer
    fact(L.MoveSetLabel, EUCLID, EUCLID_MOVES),
] + decrease_facts + [
    fact(L.BoundedBelowLabel, SUM, M.Zero),
])
euclid_start = P.Knowledge(euclid_start_facts)()
euclid_goal = P.Knowledge(M.Pair(fact(L.TerminatesLabel, EUCLID), EMPTY))()
euclid_plan = chain([
    P.TheoremAction(engel_rules["thread_decreasing_moves"], EMPTY)(),
    P.TheoremAction(engel_rules["decreasing_moves_step"], EMPTY)(),
    P.TheoremAction(engel_rules["decreasing_moves_step"], EMPTY)(),
    P.TheoremAction(engel_rules["decreasing_moves_empty"], EMPTY)(),
    P.TheoremAction(engel_rules["monovariant_terminates"], EMPTY)(),
])
euclid_built = P.BuildDerivation(euclid_start, euclid_plan, registry)()
euclid_derivation = M.Head(euclid_built)()
euclid_registry = M.Head(M.Tail(euclid_built)())()
euclid_verdict = checker_b.VerifyDerivation(
    euclid_derivation, euclid_start, euclid_goal,
    engel_trusted, euclid_registry)()
check("Checker B verifies the Euclid monovariant chain to Terminates",
      head_is(euclid_verdict, L.DerivationVerifiedLabel))

# A second, smaller Euclid instance whose AllMovesDecrease premise is
# itself derived and verified -- it backs the terminates holdout in [3].
EUCLID_SMALL = M.Char("euclid-problem-small")
small_transitions = euclid_transitions(9)
small_decrease = []
for move in (SHRINK_LEFT, SHRINK_RIGHT):
    small_decrease.append(_take(Miner.VerifyMeasureDecrease(
        move, SUM, small_transitions, registry)()))
small_start = P.Knowledge(chain([
    fact(L.MonovariantLabel, EUCLID_SMALL, SUM),
    fact(L.MoveSetLabel, EUCLID_SMALL, EUCLID_MOVES),
] + small_decrease))()
small_goal = P.Knowledge(M.Pair(
    fact(L.AllMovesDecreaseLabel, EUCLID_SMALL, SUM), EMPTY))()
small_plan = chain([
    P.TheoremAction(engel_rules["thread_decreasing_moves"], EMPTY)(),
    P.TheoremAction(engel_rules["decreasing_moves_step"], EMPTY)(),
    P.TheoremAction(engel_rules["decreasing_moves_step"], EMPTY)(),
    P.TheoremAction(engel_rules["decreasing_moves_empty"], EMPTY)(),
])
small_built = P.BuildDerivation(small_start, small_plan, registry)()
small_verdict = checker_b.VerifyDerivation(
    M.Head(small_built)(), small_start, small_goal,
    engel_trusted, M.Head(M.Tail(small_built)())())()
check("the small Euclid instance's AllMovesDecrease is likewise "
      "Checker-B derived (backs the [3] holdout)",
      head_is(small_verdict, L.DerivationVerifiedLabel))

# ---------------------------------------------------------------------------
# [3] one ledger, three domains, promoted in sequence
# ---------------------------------------------------------------------------

section(3, "One ledger, three domains, promoted in sequence")

ledger = Ledger.EmptyPromotionLedger(registry)()
zero_cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
entries = {}


def rule_macro(name, rule):
    return Eval.CandidateMacro(
        M.Char(name),
        M.Pair(P.KnowledgeLabel, M.Pair(P.RulePremises(rule)(), EMPTY)),
        M.Pair(P.KnowledgeLabel, M.Pair(P.RuleReplacement(rule)(), EMPTY)),
        M.Pair(P.TheoremAction(rule, EMPTY)(), EMPTY),
    )()


def submit(tag, macro, start, goal, holdouts, provenance, trusted,
           expect_version):
    global ledger
    outcome = Ledger.SubmitCandidateForPromotion(
        ledger, macro, L.ProofSchemaPromotionLabel, start, goal,
        zero_cost, holdouts, provenance, trusted, registry)()
    approved = head_is(outcome, L.PromotionApprovedLabel)
    check(tag + ": promoted through evaluator, ablation and holdout gates",
          approved)
    if not approved:
        check(tag + ": ledger version advanced", False, "promotion refused")
        check(tag + ": entry active with ProofReceipt", False,
              "promotion refused")
        return None
    ledger = M.Head(M.Tail(outcome)())()
    entry = M.Head(M.Tail(M.Tail(outcome)())())()
    entries[tag] = entry
    check(tag + ": ledger version advanced to " + str(expect_version),
          M.IdentityCompare(Ledger.PromotionLedgerVersion(ledger)(),
                            nat(expect_version))() is M.truth_value)
    check(tag + ": entry active and carries a ProofReceipt",
          M.IdentityCompare(Ledger.LedgerEntryStatus(entry)(),
                            L.PromotionActiveLabel)() is M.truth_value
          and head_is(Ledger.LedgerEntryReceipt(entry)(),
                      L.ProofReceiptLabel))
    return entry


def holdout(start_facts, goal_fact, expected):
    return M.Pair(
        P.Knowledge(chain(start_facts))(),
        M.Pair(P.Knowledge(M.Pair(goal_fact, EMPTY))(),
               M.Pair(M.truth_value if expected else M.false_value, EMPTY)))


# --- funceq/NT: divisibility transitivity (fresh numbers) ---
rule_t = funceq_rules["divisibility_transitive"]


def divides_f(a, b):
    return fact(L.DividesLabel, nat(a), nat(b))


check("the funceq instance's divisibility premises are machine-true "
      "(4|12, 12|36, hence 4|36)",
      divides_holds(nat(4), nat(12)) and divides_holds(nat(12), nat(36))
      and divides_holds(nat(4), nat(36)))
trans_macro = rule_macro("divisibility-transitivity", rule_t)
trans_start = P.Knowledge(chain([divides_f(4, 12), divides_f(12, 36)]))()
trans_goal = P.Knowledge(M.Pair(divides_f(4, 36), EMPTY))()
trans_holdouts = chain([
    holdout([divides_f(6, 30), divides_f(30, 90)], divides_f(6, 90), True),
    holdout([divides_f(7, 21), divides_f(21, 84)], divides_f(7, 84), True),
    holdout([divides_f(4, 12), divides_f(6, 12)], divides_f(4, 6), False),
])
submit("funceq/NT transitivity", trans_macro, trans_start, trans_goal,
       trans_holdouts, EMPTY, M.Pair(rule_t, EMPTY), 1)

# --- geometry: Thales (fresh figure names) ---
thales = geometry_rules["semicircle_angle_is_right"]
K9 = M.Char("k9")
P9, Q9, R9 = M.Char("P9"), M.Char("Q9"), M.Char("R9")


def thales_facts(k, p, q, r, diameter=True):
    facts = []
    if diameter:
        facts.append(fact(L.DiameterLineLabel, k, call(L.SegmentLabel, p, q)))
    facts.append(fact(L.OnCircleLabel, r, k))
    return facts


def perp_goal(p, q, r):
    return fact(L.PerpendicularLabel,
                call(L.SegmentLabel, r, p), call(L.SegmentLabel, r, q))


thales_macro = rule_macro("thales-semicircle", thales)
thales_start = P.Knowledge(chain(thales_facts(K9, P9, Q9, R9)))()
thales_goal = P.Knowledge(M.Pair(perp_goal(P9, Q9, R9), EMPTY))()
K10 = M.Char("k10")
P10, Q10, R10 = M.Char("P10"), M.Char("Q10"), M.Char("R10")
K11 = M.Char("k11")
P11, Q11, R11 = M.Char("P11"), M.Char("Q11"), M.Char("R11")
thales_holdouts = chain([
    holdout(thales_facts(K10, P10, Q10, R10), perp_goal(P10, Q10, R10), True),
    holdout(thales_facts(K11, P11, Q11, R11, diameter=False),
            perp_goal(P11, Q11, R11), False),
])
submit("geometry Thales", thales_macro, thales_start, thales_goal,
       thales_holdouts, EMPTY, M.Pair(thales, EMPTY), 2)

# --- Engel invariance: the obstruction closer, certificate provenance ---
obstruction = engel_rules["invariant_obstruction"]
obs_macro = rule_macro("engel-invariant-obstruction", obstruction)
invariant_fact = fact(L.InvariantLabel, CHAMELEON, PHI)


def obstruction_start(target, value, apart=True):
    facts = [invariant_fact, read_start,
             fact(L.ReadingLabel, PHI, target, value)]
    if apart:
        facts.append(fact(L.ApartLabel, start_value, value))
    return P.Knowledge(chain(facts))()


obs_start = obstruction_start(TARGET_CH, target_value)
obs_goal = P.Knowledge(M.Pair(
    fact(L.UnreachableLabel, CHAMELEON, TARGET_CH), EMPTY))()
obs_holdouts = chain([
    M.Pair(obstruction_start(TARGET_CH2, reading(PHI, TARGET_CH2)),
           M.Pair(P.Knowledge(M.Pair(
               fact(L.UnreachableLabel, CHAMELEON, TARGET_CH2),
               EMPTY))(), M.Pair(M.truth_value, EMPTY))),
    M.Pair(obstruction_start(SAME_CH, reading(PHI, SAME_CH), apart=False),
           M.Pair(P.Knowledge(M.Pair(
               fact(L.UnreachableLabel, CHAMELEON, SAME_CH),
               EMPTY))(), M.Pair(M.false_value, EMPTY))),
])
phi_certificate = Miner.GroundObservableCertificate(
    L.PreservesLabel, PHI, CHAMELEON_MOVES, ch_transitions_term)()
print("    submitting with certificate provenance (ledger re-verifies "
      "preservation over all 108 transitions) ...")
submit("Engel invariance obstruction", obs_macro, obs_start, obs_goal,
       obs_holdouts, phi_certificate, M.Pair(obstruction, EMPTY), 3)

# --- Engel monovariant: the terminates closer, certificate provenance ---
terminates = engel_rules["monovariant_terminates"]
term_macro = rule_macro("engel-monovariant-terminates", terminates)
all_decrease_fact = fact(L.AllMovesDecreaseLabel, EUCLID, SUM)
term_start = P.Knowledge(chain([
    mono_fact, all_decrease_fact,
    fact(L.BoundedBelowLabel, SUM, M.Zero)]))()
term_goal = P.Knowledge(M.Pair(fact(L.TerminatesLabel, EUCLID), EMPTY))()
term_holdouts = chain([
    holdout([fact(L.MonovariantLabel, EUCLID_SMALL, SUM),
             fact(L.AllMovesDecreaseLabel, EUCLID_SMALL, SUM),
             fact(L.BoundedBelowLabel, SUM, M.Zero)],
            fact(L.TerminatesLabel, EUCLID_SMALL), True),
    holdout([mono_fact, all_decrease_fact],
            fact(L.TerminatesLabel, EUCLID), False),
])
sum_certificate = Miner.GroundObservableCertificate(
    L.StrictlyDecreasesLabel, SUM, EUCLID_MOVES, euclid_transitions_term)()
print("    submitting with certificate provenance (ledger re-verifies "
      "strict decrease over all 132 transitions) ...")
submit("Engel monovariant terminates", term_macro, term_start, term_goal,
       term_holdouts, sum_certificate, M.Pair(terminates, EMPTY), 4)

check("the shared ledger holds four active schemata (one per domain "
      "derivation, two for Engel)",
      count_of(Ledger.PromotionLedgerProofSchemata(ledger)()) == 4)

# ---------------------------------------------------------------------------
# [4] refusals, each for a stated machine reason
# ---------------------------------------------------------------------------

section(4, "Refusals, each for a stated machine reason")

BAD_PHI = observable([1, 0, 0])
forged_certificate = Miner.GroundObservableCertificate(
    L.PreservesLabel, BAD_PHI, CHAMELEON_MOVES, ch_transitions_term)()
forged_direct = Miner.VerifyGroundObservableCertificate(
    forged_certificate, registry)()
registry = M.Head(M.Tail(M.Tail(forged_direct)())())()
check("a certificate for a non-preserved observable fails direct "
      "re-verification, reason InvariantRefuted",
      M.Head(forged_direct)() is M.false_value
      and head_is(M.Head(M.Tail(forged_direct)())(),
                  L.InvariantRefutedLabel))

forged_outcome = Ledger.SubmitCandidateForPromotion(
    ledger, obs_macro, L.ProofSchemaPromotionLabel, obs_start, obs_goal,
    zero_cost, obs_holdouts, forged_certificate,
    M.Pair(obstruction, EMPTY), registry)()
check("the same certificate offered as provenance gets the promotion "
      "refused at the ledger's gate 4",
      head_is(forged_outcome, L.PromotionRejectedLabel)
      and M.IdentityCompare(
          M.Head(M.Tail(forged_outcome)())(),
          L.InvariantRefutedLabel)() is M.truth_value)

empty_cert = Miner.GroundObservableCertificate(
    L.PreservesLabel, PHI, EMPTY, ch_transitions_term)()
empty_direct = Miner.VerifyGroundObservableCertificate(empty_cert, registry)()
registry = M.Head(M.Tail(M.Tail(empty_direct)())())()
check("a certificate listing no moves refuses (no vacuous passage)",
      M.Head(empty_direct)() is M.false_value)

untrusted_outcome = Ledger.SubmitCandidateForPromotion(
    ledger, thales_macro, L.ProofSchemaPromotionLabel,
    thales_start, thales_goal, zero_cost, thales_holdouts,
    EMPTY, EMPTY, registry)()
check("a candidate whose rule is not trusted is refused",
      head_is(untrusted_outcome, L.PromotionRejectedLabel))

check("refusals did not advance the ledger (still version 4)",
      M.IdentityCompare(Ledger.PromotionLedgerVersion(ledger)(),
                        nat(4))() is M.truth_value)

# ---------------------------------------------------------------------------
# [5] ablation via the evaluator: withheld rules
# ---------------------------------------------------------------------------

section(5, "Ablation via evaluator.py: withholding the load-bearing rule")


def ablation_status(result):
    return M.Head(M.Tail(M.Tail(result)())())()


obs_ablation = Eval.WithheldRuleAblationTrial(
    obs_macro, obs_start, obs_goal, M.Pair(obstruction, EMPTY),
    M.Pair(obstruction, EMPTY), registry)()
check("Engel: withhold invariant_obstruction -> the candidate stops "
      "evaluating (ablation status Proved)",
      head_is(obs_ablation, L.AblationVerifiedLabel)
      and M.IdentityCompare(ablation_status(obs_ablation),
                            L.ProvedLabel)() is M.truth_value)

trans_ablation = Eval.WithheldRuleAblationTrial(
    trans_macro, trans_start, trans_goal, M.Pair(rule_t, EMPTY),
    M.Pair(rule_t, EMPTY), registry)()
check("funceq/NT: withhold divisibility_transitive -> likewise",
      head_is(trans_ablation, L.AblationVerifiedLabel)
      and M.IdentityCompare(ablation_status(trans_ablation),
                            L.ProvedLabel)() is M.truth_value)

generous_trusted = M.Pair(
    obstruction,
    M.Pair(engel_rules["thread_preserving_moves"], EMPTY))
control_ablation = Eval.WithheldRuleAblationTrial(
    obs_macro, obs_start, obs_goal, generous_trusted,
    M.Pair(engel_rules["thread_preserving_moves"], EMPTY), registry)()
check("control: withhold a rule the derivation never uses -> still "
      "evaluates, status Failed (the trial does not cry wolf)",
      head_is(control_ablation, L.AblationVerifiedLabel)
      and M.IdentityCompare(ablation_status(control_ablation),
                            L.FailedLabel)() is M.truth_value)

builtin = Eval.AblationTrial(
    obs_macro, obs_start, obs_goal, M.Pair(obstruction, EMPTY), registry)()
check("the ledger's built-in (triviality) ablation also passes the "
      "promoted obstruction macro, for the record",
      head_is(builtin, L.AblationVerifiedLabel)
      and M.IdentityCompare(ablation_status(builtin),
                            L.ProvedLabel)() is M.truth_value)

# ---------------------------------------------------------------------------
# [6] receipts re-verified against policy; snapshot round-trip
# ---------------------------------------------------------------------------

section(6, "Receipts re-verified against policy; snapshot round-trip")

entry = entries.get("Engel invariance obstruction")
if entry is not None:
    receipt = Ledger.LedgerEntryReceipt(entry)()
    policy = M.Pair(
        L.CheckPolicyLabel,
        M.Pair(M.Char("engel-invariant-obstruction"),
               M.Pair(obs_start, M.Pair(obs_goal, EMPTY))))
    receipt_verdict = checker_b.VerifyProofReceipt(
        receipt, policy, M.Pair(obstruction, EMPTY), registry)()
    check("the ledger entry's ProofReceipt re-verifies against policy",
          head_is(receipt_verdict, L.DerivationVerifiedLabel))
    bad_policy = M.Pair(
        L.CheckPolicyLabel,
        M.Pair(M.Char("engel-invariant-obstruction"),
               M.Pair(obs_start, M.Pair(wrong_goal, EMPTY))))
    bad_verdict = checker_b.VerifyProofReceipt(
        receipt, bad_policy, M.Pair(obstruction, EMPTY), registry)()
    check("  ... and is refused against a policy naming the decoy goal",
          head_is(bad_verdict, L.GoalMismatchLabel))
else:
    check("the ledger entry's ProofReceipt re-verifies against policy",
          False, "promotion did not land")
    check("  ... and is refused against a policy naming the decoy goal",
          False, "promotion did not land")

snapshot_dir = tempfile.mkdtemp(prefix="test42-")
snapshot_path = os.path.join(snapshot_dir, "snapshot.json")
codec = persistence.SnapshotCodec(namespace)
codec.save(graph, snapshot_path)
restored = codec.load(snapshot_path)
os.remove(snapshot_path)
os.rmdir(snapshot_dir)
check("GroundObservableCertificateLabel is in the snapshot symbol table",
      "GroundObservableCertificateLabel" in restored.symbols)
check("  ... and restores to the live label object",
      restored.symbols.get("GroundObservableCertificateLabel")
      is namespace["GroundObservableCertificateLabel"])

print()
print("Landed: Checker-B receipts for both W27 Engel chains; one shared")
print("        ledger promoting funceq/NT transitivity, geometry Thales,")
print("        and both Engel closers (versions 1-4); gate-4 provenance")
print("        re-verification of ground-observable certificates (forged")
print("        certificate refused); withheld-rule ablation on two domains.")
print("Pinned open: multi-rule candidate macros (patterns are the rules'")
print("        own templates; seeded bindings poison multi-step plans),")
print("        so strategy chains are receipted via VerifyDerivation and")
print("        their closers are what the ledger promotes; monotone replay")
print("        of a strategy argument needs multiply-used facts listed")
print("        multiply (knowledge rewrite consumes).  The search-leg")
print("        assembly gap (test39 [5]) is untouched by this suite.")
print()

print("=== TEST 42 RESULTS ===")
passed = sum(1 for _n, ok, _d in RESULT if ok)
failed = len(RESULT) - passed
for name, ok, detail in RESULT:
    if not ok:
        print("  FAILED: " + name + (("  -- " + str(detail)) if detail else ""))
print("  Checks passed: %d/%d" % (passed, len(RESULT)))
print("  Total time:    %.3fs" % (time.time() - T0))
print()
if failed:
    print("=== TEST 42 FAILED ===")
    sys.exit(1)
print("=== TEST 42 COMPLETE ===")
