# ============================================================
# TEST 39: W27 Engel Remainder
#          two unnamed instances closed by the strategy pack,
#          strategy methods proposed in ordinary planner runs,
#          one observable discovered by the invariant miner
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test39_engel_remainder.py
#
# Slot 39 is the one `delegation/README.md` pre-allocates to
# `W27-engel-remainder.md`. W10 (test23) landed the strategy schemas
# over symbolic problems; this suite is the remainder its DAG entry
# named. What is verified below, in the brief's three parts:
#
#   Instances.  Two unnamed processes, present only as evaluation
#   data (ground transition relations built below): Euclid's
#   algorithm by repeated subtraction, closed by the monovariant
#   schema; and the chameleon process (two chameleons of different
#   colours meet and both take the third colour), closed by the
#   invariance schema for all three monochrome targets. The per-move
#   claims the schemas consume (StrictlyDecreases / Preserves) are
#   not asserted by this suite: they are the verdict terms of the
#   miner's new verifier edges, discharged by machine arithmetic
#   over every ground transition of the instance. Neither instance
#   is one of the three named Engel packs, and `main.py` gains no
#   agenda case. The instances are deliberately small (pairs bounded
#   by 12; nine chameleons) so the exhaustive verification is over
#   the *whole* state space of each process as defined; no claim is
#   made beyond the enumerated space.
#
#   Discovery.  The chameleon observable that closes the instance is
#   not chosen here: MinePreservedObservables tests every linear
#   form with coefficients in {0,1,2}, raw and mod 3, over the
#   transition relation, certifies the preserved ones, and the
#   suite's separation check (machine readings at the start and the
#   three targets) selects the first certified observable that
#   actually separates. The ablation (a lone colour change added
#   to the moves) leaves no separating observable, which is pinned.
#
#   Search firing.  ProposeStrategyMethods reads a problem's facts
#   and goal and emits the Monovariant / Invariance / SemiInvariant
#   method terms the declarations support; a PlannerProblem built
#   with no method term, passed through PlannerProblemWithProposals,
#   decomposes its root into exactly the method obligations, and
#   each obligation the problem's facts already carry is Proved on
#   creation. With the generator withheld, no strategy alternative
#   appears. Stated honestly: the root obligation does NOT reach
#   Proved in these runs. Its discharge is an assembly search job,
#   and the production search stalls on this pack in two
#   independently pinned ways (see the note in [5]); the instances
#   close mathematically by forward chaining, the same closure
#   test23 and test37 use. The suite pins the observed planner
#   outcome rather than a wished-for one.
#
# Host layer only below: file paths, timings, enumeration of
# candidate states/transitions, counting and printing. Every
# mathematical claim (a reading, a decrease, a preservation, a
# derived fact, an obligation status) is decided by machine edges;
# host code decides only where to look next.

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

PACKAGE = os.path.basename(REPO)

M = importlib.import_module(PACKAGE + ".machine")
P = importlib.import_module(PACKAGE + ".proof")
L = importlib.import_module(PACKAGE + ".labels")
Planner = importlib.import_module(PACKAGE + ".planner")
Miner = importlib.import_module(PACKAGE + ".invariant_miner")
Arith = importlib.import_module(PACKAGE + ".math.arithmetic")
persistence = importlib.import_module(PACKAGE + ".persistence")
packs = importlib.import_module(PACKAGE + ".packs")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
main_mod = importlib.import_module(PACKAGE + ".main")

T0 = time.time()
EMPTY = M.EmptyList

print("=== TEST 39: W27 Engel Remainder ===")
print()

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    line = "    PASS  " if ok else "    FAIL  "
    line = line + name + ("  -- " + detail if detail else "")
    print(line)


def section(number, title):
    print()
    print("[%d] %s  (%.1fs elapsed)" % (number, title, time.time() - T0))


# ---------------------------------------------------------------------------
# host-layer helpers (machine predicates decide everything mathematical)
# ---------------------------------------------------------------------------

runtime = runtime_mod.make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()


def _take(pair):
    """Split a Pair(value, Pair(registry, ...)) result, threading registry."""
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


def chain(items):
    out = EMPTY
    for item in reversed(items):
        out = M.Pair(item, out)
    return out


def fact(label, *args):
    return M.Pair(label, chain(args))


def is_list_term(term):
    return M.IsPair(term)() is M.truth_value or term is EMPTY


def to_list(term):
    out = []
    cursor = term
    while M.IsPair(cursor)() is M.truth_value:
        out.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return out


def count_of(term):
    return int(M.GMPRepText(M.CountRep(term)())())


def has_fact(facts, target):
    cursor = facts
    while M.IsPair(cursor)() is M.truth_value:
        if M.Compare(M.Head(cursor)(), target)() is M.truth_value:
            return True
        cursor = M.Tail(cursor)()
    return False


def head_is(term, label):
    return (M.IsPair(term)() is M.truth_value
            and M.IdentityCompare(M.Head(term)(), label)() is M.truth_value)


def observable(coeffs, modulus=None):
    modulus_term = EMPTY if modulus is None else nat(modulus)
    return Miner.LinearObservable(chain([nat(c) for c in coeffs]), modulus_term)()


def reading(obs, state):
    return _take(Miner.LinearObservableValue(obs, state, registry)())


def transition(move, state, next_state):
    return M.Pair(move, M.Pair(state, M.Pair(next_state, EMPTY)))


def transition_move(term):
    return M.Head(term)()


def closure(facts, rules, rounds=24):
    """Monotone forward chaining, as in test23/test37: strategy rules
    state conclusions, and consuming their premises would retract the
    facts the argument rests on."""
    state = P.Knowledge(facts)()
    for _round in range(rounds):
        changed = False
        current = P.KnowledgeFacts(state)()
        cursor = rules
        while M.IsPair(cursor)() is M.truth_value:
            rule = M.Head(cursor)()
            cursor = M.Tail(cursor)()
            bindings = P.JoinPremises(P.RulePremises(rule)(), current, EMPTY)()
            bcursor = bindings
            while M.IsPair(bcursor)() is M.truth_value:
                added = P.InstantiateFactList(P.RuleReplacement(rule)(),
                                              M.Head(bcursor)())()
                acursor = added
                while M.IsPair(acursor)() is M.truth_value:
                    one = M.Head(acursor)()
                    if not has_fact(current, one):
                        current = M.Pair(one, current)
                        changed = True
                    acursor = M.Tail(acursor)()
                bcursor = M.Tail(bcursor)()
            state = P.Knowledge(current)()
        if not changed:
            break
    return P.NormalizeKnowledge(state, registry)()


def closed_facts(facts, rules, rounds=24):
    return P.KnowledgeFacts(closure(facts, rules, rounds))()


# ---------------------------------------------------------------------------
# [1] boot and load the strategy pack
# ---------------------------------------------------------------------------

section(1, "Booting and loading packs/engel-strategies.pack.yaml")

namespace = main_mod._runtime_namespace()
loader = packs.PackLoader(namespace)
pack = loader.load_pack_file(
    os.path.join(REPO, "packs", "engel-strategies.pack.yaml"), graph)
rules = P.CompileRuleChain(pack.rule_chain, registry)()

check("strategy pack still carries its thirteen rules (ontology unchanged)",
      count_of(pack.rule_chain) == 13, str(count_of(pack.rule_chain)) + " rules")
check("the pack still names no instance (no examples block)",
      len(pack.examples.entries) == 0)

# ---------------------------------------------------------------------------
# [2] Instance M: Euclid by repeated subtraction (monovariant)
# ---------------------------------------------------------------------------

section(2, "Instance M: Euclid by subtraction, components 1..12")

EUCLID = M.Char("euclid-problem")
SHRINK_LEFT = M.Char("shrink-left")
SHRINK_RIGHT = M.Char("shrink-right")
EUCLID_MOVES = chain([SHRINK_LEFT, SHRINK_RIGHT])
SUM = observable([1, 1])  # the measure descriptor: a + b, raw

euclid_states = []  # host bookkeeping: (a_term, b_term, state_term)
for a in range(1, 13):
    for b in range(1, 13):
        a_term, b_term = nat(a), nat(b)
        euclid_states.append((a_term, b_term, chain([a_term, b_term])))

euclid_transitions = []
for a_term, b_term, state in euclid_states:
    if M.NatLess(b_term, a_term, registry)() is M.truth_value:
        diff = _take(Arith.NatSubtract(a_term, b_term, registry)())
        euclid_transitions.append(
            transition(SHRINK_LEFT, state, chain([diff, b_term])))
    elif M.NatLess(a_term, b_term, registry)() is M.truth_value:
        diff = _take(Arith.NatSubtract(b_term, a_term, registry)())
        euclid_transitions.append(
            transition(SHRINK_RIGHT, state, chain([a_term, diff])))
euclid_transitions_term = chain(euclid_transitions)

left_count = count_of(chain([t for t in euclid_transitions
                             if transition_move(t) is SHRINK_LEFT]))
right_count = count_of(chain([t for t in euclid_transitions
                              if transition_move(t) is SHRINK_RIGHT]))
check("the transition relation partitions the 144 states: 66 + 66 moves, "
      "12 equal pairs moveless (machine-counted)",
      left_count == 66 and right_count == 66
      and count_of(euclid_transitions_term) == 132,
      "%d left, %d right" % (left_count, right_count))

verdict_left = _take(Miner.VerifyMeasureDecrease(
    SHRINK_LEFT, SUM, euclid_transitions_term, registry)())
verdict_right = _take(Miner.VerifyMeasureDecrease(
    SHRINK_RIGHT, SUM, euclid_transitions_term, registry)())
expected_left = fact(L.StrictlyDecreasesLabel, SHRINK_LEFT, SUM)
expected_right = fact(L.StrictlyDecreasesLabel, SHRINK_RIGHT, SUM)
check("miner certifies shrink-left strictly decreases the sum (all 66 transitions)",
      M.Compare(verdict_left, expected_left)() is M.truth_value)
check("miner certifies shrink-right strictly decreases the sum (all 66 transitions)",
      M.Compare(verdict_right, expected_right)() is M.truth_value)

first_only = observable([1, 0])
verdict_first = _take(Miner.VerifyMeasureDecrease(
    SHRINK_RIGHT, first_only, euclid_transitions_term, registry)())
check("the first component alone does not strictly decrease on shrink-right "
      "(Counterexample, independently verified)",
      head_is(verdict_first, L.CounterexampleLabel))
verdict_first_ni = _take(Miner.VerifyMeasureNonIncrease(
    SHRINK_RIGHT, first_only, euclid_transitions_term, registry)())
check("  ... but it does never rise there (NonIncreases)",
      M.Compare(verdict_first_ni,
                fact(L.NonIncreasesLabel, SHRINK_RIGHT, first_only))() is M.truth_value)

ghost = M.Char("no-such-move")
verdict_ghost = _take(Miner.VerifyMeasureDecrease(
    ghost, SUM, euclid_transitions_term, registry)())
check("a move with no transitions earns no certificate (no vacuous passage)",
      head_is(verdict_ghost, L.CounterexampleLabel))

terminates_euclid = fact(L.TerminatesLabel, EUCLID)
euclid_facts = chain([
    fact(L.MonovariantLabel, EUCLID, SUM),
    fact(L.MoveSetLabel, EUCLID, EUCLID_MOVES),
    verdict_left,
    verdict_right,
    fact(L.BoundedBelowLabel, SUM, M.Zero),
])
got = closed_facts(euclid_facts, rules)
check("the strategy pack derives AllMovesDecrease from the miner's verdicts",
      has_fact(got, fact(L.AllMovesDecreaseLabel, EUCLID, SUM)))
check("  ... and Terminates: the unnamed instance closes",
      has_fact(got, terminates_euclid))

euclid_facts_nobound = chain([
    fact(L.MonovariantLabel, EUCLID, SUM),
    fact(L.MoveSetLabel, EUCLID, EUCLID_MOVES),
    verdict_left,
    verdict_right,
])
got_nobound = closed_facts(euclid_facts_nobound, rules)
check("without the bound the instance does not close",
      has_fact(got_nobound, fact(L.AllMovesDecreaseLabel, EUCLID, SUM))
      and not has_fact(got_nobound, terminates_euclid))

# Corroboration: actually run the process. Host chooses the applicable
# move by the machine's comparisons; every successor is computed by
# the machine's subtraction. The theorem says this cannot run forever;
# here it is seen to stop, at an equal pair, on two starts.
for start_pair, expected_steps in (((12, 8), 2), ((11, 7), 5)):
    a_term, b_term = nat(start_pair[0]), nat(start_pair[1])
    steps = 0
    while steps <= 20 and M.NatEq(a_term, b_term, registry)() is M.false_value:
        if M.NatLess(b_term, a_term, registry)() is M.truth_value:
            a_term = _take(Arith.NatSubtract(a_term, b_term, registry)())
        else:
            b_term = _take(Arith.NatSubtract(b_term, a_term, registry)())
        steps += 1
    check("the concrete run from %s halts at an equal pair in %d machine steps"
          % (start_pair, expected_steps),
          steps == expected_steps
          and M.NatEq(a_term, b_term, registry)() is M.truth_value,
          "halted at (%d, %d)" % (int_of(a_term), int_of(b_term)))



# ---------------------------------------------------------------------------
# [3] Discovery: mine the chameleon observable
# ---------------------------------------------------------------------------

section(3, "Instance I data + discovery: nine chameleons, three colours")

CHAMELEON = M.Char("chameleon-problem")
MEET12 = M.Char("meet-1-2")
MEET13 = M.Char("meet-1-3")
MEET23 = M.Char("meet-2-3")
CHAMELEON_MOVES = chain([MEET12, MEET13, MEET23])
TOTAL_CHAMELEONS = 9

ch_states = []  # host bookkeeping: (r, g, b, state_term)
for r in range(TOTAL_CHAMELEONS + 1):
    for g in range(TOTAL_CHAMELEONS + 1 - r):
        b = TOTAL_CHAMELEONS - r - g
        ch_states.append((nat(r), nat(g), nat(b), chain([nat(r), nat(g), nat(b)])))

def state_total(state):
    parts = to_list(state)
    total = _take(Arith.Add(parts[0], parts[1], registry)())
    return _take(Arith.Add(total, parts[2], registry)())

all_states_sum_to_total = all(
    M.NatEq(state_total(state), nat(TOTAL_CHAMELEONS), registry)() is M.truth_value
    for (_r, _g, _b, state) in ch_states)
check("every enumerated state machine-sums to the population (55 states)",
      all_states_sum_to_total and len(ch_states) == 55)

def positive(term):
    return M.NatEq(term, M.Zero, registry)() is M.false_value

def succ2(term):
    return succ(succ(term))

ch_transitions = []
for r_term, g_term, b_term, state in ch_states:
    if positive(r_term) and positive(g_term):
        ch_transitions.append(transition(
            MEET12, state, chain([pred(r_term), pred(g_term), succ2(b_term)])))
    if positive(r_term) and positive(b_term):
        ch_transitions.append(transition(
            MEET13, state, chain([pred(r_term), succ2(g_term), pred(b_term)])))
    if positive(g_term) and positive(b_term):
        ch_transitions.append(transition(
            MEET23, state, chain([succ2(r_term), pred(g_term), pred(b_term)])))
ch_transitions_term = chain(ch_transitions)

targets_stay_in_space = True
for t in ch_transitions:
    _mv = M.Head(t)()
    nxt = M.Head(M.Tail(M.Tail(t)())())()
    if M.NatEq(state_total(nxt), nat(TOTAL_CHAMELEONS), registry)() is M.false_value:
        targets_stay_in_space = False
check("every transition target machine-sums to the population: "
      "the relation is closed over the 55 states",
      targets_stay_in_space,
      str(count_of(ch_transitions_term)) + " transitions")

candidates = []
for alpha in (0, 1, 2):
    for beta in (0, 1, 2):
        for gamma in (0, 1, 2):
            if (alpha, beta, gamma) == (0, 0, 0):
                continue
            candidates.append(observable([alpha, beta, gamma], 3))
            candidates.append(observable([alpha, beta, gamma]))
candidates_term = chain(candidates)
check("the candidate space is every nonzero {0,1,2} form, mod 3 and raw",
      count_of(candidates_term) == 52)

print("    mining over %d transitions x 52 candidates ..."
      % count_of(ch_transitions_term))
mine_pair = Miner.MinePreservedObservables(
    ch_transitions_term, candidates_term, registry)()
certified_term = M.Head(mine_pair)()
refuted_term = M.Head(M.Tail(mine_pair)())()
registry = M.Head(M.Tail(M.Tail(mine_pair)())())()
certified = to_list(certified_term)

def descriptor_in(terms, coeffs, modulus=None):
    wanted = observable(coeffs, modulus)
    return any(M.Compare(t, wanted)() is M.truth_value for t in terms)

check("every candidate is decided: certified + refuted = 52",
      count_of(certified_term) + count_of(refuted_term) == 52,
      "%d certified, %d refuted" % (count_of(certified_term), count_of(refuted_term)))
check("the classic observable (1,2,0) mod 3 is among the certified",
      descriptor_in(certified, [1, 2, 0], 3))
check("  ... and its mirror (2,1,0) mod 3 with it",
      descriptor_in(certified, [2, 1, 0], 3))
check("  ... and the total count (1,1,1), trivially, as it should be",
      descriptor_in(certified, [1, 1, 1]))
check("the raw first-colour count (1,0,0) is refuted, with a witness",
      not descriptor_in(certified, [1, 0, 0])
      and not descriptor_in(certified, [1, 0, 0], 3))

# Separation: a certified observable only obstructs if it reads
# differently at the start and at a target. Decided per candidate by
# machine readings; the first certified observable separating ALL
# THREE monochrome targets is the one the instance will use.
START_CH = chain([nat(2), nat(3), nat(4)])
TARGETS_CH = [chain([nat(9), nat(0), nat(0)]),
              chain([nat(0), nat(9), nat(0)]),
              chain([nat(0), nat(0), nat(9)])]

def separates_all(obs):
    start_value = reading(obs, START_CH)
    for target in TARGETS_CH:
        if M.NatEq(start_value, reading(obs, target), registry)() is M.truth_value:
            return False
    return True

MINED_PHI = None
for obs in certified:
    if separates_all(obs):
        MINED_PHI = obs
        break

def describe_observable(obs):
    fields = to_list(M.Tail(obs)())
    coeffs = [int_of(c) for c in to_list(fields[0])]
    modulus = fields[1]
    suffix = "raw" if modulus is EMPTY else "mod %d" % int_of(modulus)
    return "(%s) %s" % (",".join(str(c) for c in coeffs), suffix)

check("the miner found a certified observable separating all three targets",
      MINED_PHI is not None,
      describe_observable(MINED_PHI) if MINED_PHI is not None else "none")
total_obs = observable([1, 1, 1])
check("the trivial total, though certified, separates nothing",
      not separates_all(total_obs))

# Ablation: a lone colour change is enough to destroy every
# separating observable. If the ablation still separated, the
# mined observable would not be doing the work.
LONE = M.Char("lone-change")
breaker_transitions = list(ch_transitions)
for r_term, g_term, b_term, state in ch_states:
    if positive(r_term):
        breaker_transitions.append(transition(
            LONE, state, chain([pred(r_term), succ(g_term), b_term])))
print("    re-mining with the lone-change move added (ablation) ...")
abl_pair = Miner.MinePreservedObservables(
    chain(breaker_transitions), candidates_term, registry)()
abl_certified = to_list(M.Head(abl_pair)())
registry = M.Head(M.Tail(M.Tail(abl_pair)())())()
abl_separators = [o for o in abl_certified if separates_all(o)]
check("ablation: with a lone colour change available, no candidate both "
      "is preserved and separates",
      len(abl_separators) == 0,
      "%d still certified, none separating" % len(abl_certified))

# ---------------------------------------------------------------------------
# [4] Instance I closes through the pack with the mined observable
# ---------------------------------------------------------------------------

section(4, "Instance I: monochrome chameleons are unreachable")

preserves_facts = []
all_moves_certified = True
for move in to_list(CHAMELEON_MOVES):
    verdict = _take(Miner.VerifyObservablePreserved(
        move, MINED_PHI, ch_transitions_term, registry)())
    if M.Compare(verdict, fact(L.PreservesLabel, move, MINED_PHI))() is M.false_value:
        all_moves_certified = False
    preserves_facts.append(verdict)
check("each of the three moves independently verified to preserve the mined phi",
      all_moves_certified)

refuted_phi = observable([1, 0, 0], 3)
verdict_bad = _take(Miner.VerifyObservablePreserved(
    MEET23, refuted_phi, ch_transitions_term, registry)())
check("a non-observable is refused per move (first colour jumps by 2 on meet-2-3)",
      head_is(verdict_bad, L.InvariantRefutedLabel))

start_reading = reading(MINED_PHI, START_CH)
ch_facts_items = [
    fact(L.MoveSetLabel, CHAMELEON, CHAMELEON_MOVES),
    fact(L.ReadingLabel, MINED_PHI, START_CH, start_reading),
] + preserves_facts
apart_ok = True
for target in TARGETS_CH:
    target_reading = reading(MINED_PHI, target)
    ch_facts_items.append(fact(L.ReadingLabel, MINED_PHI, target, target_reading))
    if M.NatEq(start_reading, target_reading, registry)() is M.false_value:
        ch_facts_items.append(fact(L.ApartLabel, start_reading, target_reading))
    else:
        apart_ok = False
check("the start reading is machine-apart from every monochrome reading",
      apart_ok,
      "start=%d" % int_of(start_reading))

got_ch = closed_facts(chain(ch_facts_items), rules)
check("the pack derives Invariant for the mined phi",
      has_fact(got_ch, fact(L.InvariantLabel, CHAMELEON, MINED_PHI)))
for index, target in enumerate(TARGETS_CH):
    check("  ... and obstructs monochrome target %d of 3" % (index + 1),
          has_fact(got_ch, fact(L.UnreachableLabel, CHAMELEON, target)))

# Same-reading control: some other state shares the start reading;
# the machinery must decline to obstruct it (no Apart is even true).
same_reading_state = None
for (_r, _g, _b, state) in ch_states:
    if M.Compare(state, START_CH)() is M.truth_value:
        continue
    if M.NatEq(reading(MINED_PHI, state), start_reading, registry)() is M.truth_value:
        same_reading_state = state
        break
control_items = [
    fact(L.MoveSetLabel, CHAMELEON, CHAMELEON_MOVES),
    fact(L.ReadingLabel, MINED_PHI, START_CH, start_reading),
    fact(L.ReadingLabel, MINED_PHI, same_reading_state, start_reading),
] + preserves_facts
got_control = closed_facts(chain(control_items), rules)
check("a state sharing the start reading is found by machine readings",
      same_reading_state is not None)
check("  ... and is correctly not obstructed",
      not has_fact(got_control,
                   fact(L.UnreachableLabel, CHAMELEON, same_reading_state)))

gapped_items = [
    fact(L.MoveSetLabel, CHAMELEON, CHAMELEON_MOVES),
    fact(L.ReadingLabel, MINED_PHI, START_CH, start_reading),
    fact(L.ReadingLabel, MINED_PHI, TARGETS_CH[0], reading(MINED_PHI, TARGETS_CH[0])),
    fact(L.ApartLabel, start_reading, reading(MINED_PHI, TARGETS_CH[0])),
] + preserves_facts[:2]
got_gapped = closed_facts(chain(gapped_items), rules)
check("with one move's preservation missing, no Invariant and no obstruction",
      not has_fact(got_gapped, fact(L.InvariantLabel, CHAMELEON, MINED_PHI))
      and not has_fact(got_gapped,
                       fact(L.UnreachableLabel, CHAMELEON, TARGETS_CH[0])))

# ---------------------------------------------------------------------------
# [5] Search firing: strategy methods proposed in ordinary runs
# ---------------------------------------------------------------------------
#
# Two facts about the production search delimit what can be pinned
# here, both found while building this suite and reproducible with
# a bare SearchJob over this pack:
#   (i)  a goal fact already present in the start Knowledge cannot
#        be reported as reached -- its plan is empty and the search
#        step reads an empty plan as no success (this is why method
#        obligations the facts meet are discharged on creation in
#        PlannerStep rather than sent to a job);
#   (ii) theorem saturation over Knowledge states derives the first
#        pass of this pack (the threading step) and then stalls:
#        advancing the successor state produces no further delta,
#        although per-rule application -- and the JoinPremises
#        closure above -- derive every step. So the root's assembly
#        job fails, and the root obligation stays unproved however
#        the method arrived. If a future worker closes either gap,
#        the two "root is not Proved" pins below are the checks
#        that should flip.

section(5, "Search firing: proposals, decomposition, and the assembly gap")

props = Planner.ProposeStrategyMethods(P.Knowledge(euclid_facts)(), terminates_euclid)()
check("the proposer emits exactly one method for the Euclid declarations",
      count_of(props) == 1)
check("  ... and it is term-equal to the hand-written Monovariant term",
      M.TermEqual(M.Head(props)(),
                  Planner.Monovariant(EUCLID, SUM, M.Zero, EUCLID_MOVES)())() is M.truth_value)

goal_unreach = fact(L.UnreachableLabel, CHAMELEON, TARGETS_CH[0])
props_ch = Planner.ProposeStrategyMethods(P.Knowledge(chain(ch_facts_items))(), goal_unreach)()
expected_inv = Planner.Invariance(
    CHAMELEON, MINED_PHI, CHAMELEON_MOVES,
    START_CH, start_reading, TARGETS_CH[0], reading(MINED_PHI, TARGETS_CH[0]))()
check("the proposer emits the Invariance method for the chameleon declarations",
      any(M.TermEqual(p, expected_inv)() is M.truth_value
          for p in to_list(props_ch)))

semi_facts = chain([
    fact(L.SemiInvariantLabel, EUCLID, SUM),
    fact(L.MoveSetLabel, EUCLID, EUCLID_MOVES),
    fact(L.BoundedBelowLabel, SUM, M.Zero),
])
props_semi = Planner.ProposeStrategyMethods(P.Knowledge(semi_facts)(), terminates_euclid)()
check("a SemiInvariant declaration proposes a SemiInvariant method",
      count_of(props_semi) == 1
      and M.TermEqual(M.Head(props_semi)(),
                      Planner.SemiInvariant(EUCLID, SUM, M.Zero, EUCLID_MOVES)())() is M.truth_value)

no_moveset = chain([
    fact(L.MonovariantLabel, EUCLID, SUM),
    fact(L.BoundedBelowLabel, SUM, M.Zero),
])
check("an incomplete declaration (no MoveSet) proposes nothing",
      count_of(Planner.ProposeStrategyMethods(
          P.Knowledge(no_moveset)(), terminates_euclid)()) == 0)
check("a strategy-shaped goal is required: invariance facts under a "
      "Terminates goal propose nothing",
      count_of(Planner.ProposeStrategyMethods(
          P.Knowledge(chain(ch_facts_items))(),
          fact(L.TerminatesLabel, CHAMELEON))()) == 0)


def obligation_rows(state_term):
    obligations = M.Head(M.Tail(state_term)())()
    rows = []
    for obligation in to_list(obligations):
        fields = M.Tail(obligation)()
        oid = M.Head(fields)()
        fields = M.Tail(fields)()
        fields = M.Tail(fields)()
        goal = M.Head(fields)()
        status = M.Head(M.Tail(fields)())()
        rows.append((oid, goal, status))
    return rows


def root_status(rows):
    for oid, _goal, status in rows:
        if M.TermEqual(oid, M.Zero)() is M.truth_value:
            return status
    return None


STRATEGY_HEADS = (L.MonovariantMethodLabel, L.SemiInvariantMethodLabel,
                  L.InvarianceMethodLabel)


def strategy_alternatives(state_term):
    found = []
    for alternative in to_list(Planner.PlannerStateAlternatives(state_term)()):
        method = Planner.PlannerAlternativeMethod(alternative)()
        if M.IsPair(method)() is M.false_value:
            continue
        head = M.Head(method)()
        if any(M.IdentityCompare(head, h)() is M.truth_value for h in STRATEGY_HEADS):
            found.append(alternative)
    return found


plain_problem = Planner.PlannerProblem(
    P.Knowledge(euclid_facts)(), terminates_euclid, rules,
    runtime.theorem_heuristic)()

print("    PlannerRun with the generator withheld ...")
plain_ran = Planner.PlannerRun(
    graph, Planner.PlannerState(plain_problem, registry)(), M.three)()
check("generator withheld -> no strategy alternative is proposed",
      len(strategy_alternatives(plain_ran)) == 0)
check("  ... and the root is not proved that way either",
      root_status(obligation_rows(plain_ran)) is not L.ProvedLabel)

proposed_problem = Planner.PlannerProblemWithProposals(plain_problem)()
print("    PlannerRun with proposals (no hand-written method term) ...")
proposed_ran = Planner.PlannerRun(
    graph, Planner.PlannerState(proposed_problem, registry)(), M.three)()
alts = strategy_alternatives(proposed_ran)
check("generator on -> exactly one strategy alternative, the proposed method",
      len(alts) == 1
      and M.TermEqual(Planner.PlannerAlternativeMethod(alts[0])(),
                      M.Head(props)())() is M.truth_value)
rows = obligation_rows(proposed_ran)
status_by_id = {}
for oid, _g, status in rows:
    status_by_id[oid] = status

def same_id(a, b):
    return M.TermEqual(a, b)() is M.truth_value

children = to_list(Planner.PlannerAlternativeChildren(alts[0])())
expected_obligations = Planner.MonovariantObligations(M.Head(props)())()
check("the alternative carries one child per method obligation",
      len(children) == count_of(expected_obligations),
      "%d children" % len(children))
all_children_proved = all(
    any(same_id(oid, child) and status is L.ProvedLabel
        for (oid, _g, status) in rows)
    for child in children)
check("every method obligation the facts carry is Proved (discharged, not searched)",
      all_children_proved)
check("the root is not Proved: assembly is a search job and the search "
      "stalls on this pack (see the note above)",
      root_status(rows) is not L.ProvedLabel)

# Ablation: same proposal path, one discharged fact removed. The
# corresponding child must not be rubber-stamped.
euclid_facts_ablated = chain([
    fact(L.MonovariantLabel, EUCLID, SUM),
    fact(L.MoveSetLabel, EUCLID, EUCLID_MOVES),
    verdict_left,
    fact(L.BoundedBelowLabel, SUM, M.Zero),
])
ablated_problem = Planner.PlannerProblemWithProposals(Planner.PlannerProblem(
    P.Knowledge(euclid_facts_ablated)(), terminates_euclid, rules,
    runtime.theorem_heuristic)())()
print("    PlannerRun, ablated: one StrictlyDecreases fact withheld ...")
ablated_ran = Planner.PlannerRun(
    graph, Planner.PlannerState(ablated_problem, registry)(), M.three)()
abl_alts = strategy_alternatives(ablated_ran)
abl_rows = obligation_rows(ablated_ran)
missing_goal = fact(L.StrictlyDecreasesLabel, SHRINK_RIGHT, SUM)
missing_status = None
kept_proved = False
for _oid, goal, status in abl_rows:
    if M.Compare(goal, missing_goal)() is M.truth_value:
        missing_status = status
    if M.Compare(goal, fact(L.StrictlyDecreasesLabel, SHRINK_LEFT, SUM))() is M.truth_value:
        kept_proved = status is L.ProvedLabel
check("ablation: the withheld obligation is not Proved ...",
      len(abl_alts) == 1 and missing_status is not L.ProvedLabel)
check("  ... while the supplied one still is (discharge is per-fact)",
      kept_proved)

# ---------------------------------------------------------------------------
# [6] representation and snapshot round-trip
# ---------------------------------------------------------------------------

section(6, "Representation checks and snapshot round-trip")


def pattern_var_count(term):
    if M.IsPair(term)() is M.false_value:
        return 0
    if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
        return 1
    return pattern_var_count(M.Head(term)()) + pattern_var_count(M.Tail(term)())


check("an observable descriptor is a machine pair headed LinearObservableLabel",
      head_is(SUM, L.LinearObservableLabel))
check("every fact of the Euclid closure is a ground machine pair (no pattern variables)",
      all(pattern_var_count(f) == 0 and M.IsPair(f)() is M.truth_value
          for f in to_list(got)))
check("the mined phi is a descriptor term, not a host string",
      head_is(MINED_PHI, L.LinearObservableLabel))

snapshot_path = os.path.join(tempfile.mkdtemp(prefix="test39-"), "snapshot.json")
codec = persistence.SnapshotCodec(namespace)
codec.save(graph, snapshot_path)
restored = codec.load(snapshot_path)
os.remove(snapshot_path)
os.rmdir(os.path.dirname(snapshot_path))
check("LinearObservableLabel is written into the snapshot symbol table",
      "LinearObservableLabel" in restored.symbols)
check("  ... and restores to the live label object",
      restored.symbols.get("LinearObservableLabel") is namespace["LinearObservableLabel"])

print()
print("Landed: two unnamed instances closed (monovariant + invariance);")
print("        strategy proposals fire in PlannerRun and their supplied")
print("        obligations discharge; the chameleon observable was mined,")
print("        not handed in; its ablation separates nothing.")
print("Not landed: end-to-end root closure inside PlannerRun -- the")
print("        assembly search job stalls on this pack ([5] note). The")
print("        instances close by forward chaining, as in test23/test37.")
print()
print("=== TEST 39 RESULTS ===")
passed = 0
for _name, ok, _detail in RESULTS:
    if ok:
        passed = passed + 1
failed = len(RESULTS) - passed
for name, ok, detail in RESULTS:
    if not ok:
        print("  FAILED: " + name + ("  -- " + detail if detail else ""))
print("  Checks passed: " + str(passed) + "/" + str(len(RESULTS)))
print("  Total time:    %.3fs" % (time.time() - T0))
print()
if failed:
    print("=== TEST 39 FAILED ===")
    sys.exit(1)
print("=== TEST 39 COMPLETE ===")
