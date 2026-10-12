# ============================================================
# TEST 23: W10 Engel Strategies
#          monovariants, semi-invariants, invariance, extremal
#          (box principle: obligationed, not asserted)
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test23_engel_strategies.py
#
# Slot 23 is the one `delegation/README.md` pre-allocates to
# `W10-engel-strategies.md`; slots 20-22 belong to W07/W08/W09.
#
# Scope, stated honestly. This branch carries none of the modules the W10
# brief's "what already exists" section assumes -- playground.py,
# invariant_miner.py, evaluator.py, curriculum.py, checker_b.py,
# promotion_ledger.py are all absent -- so the parts of its done-definition
# that need discovery, held-out/decoy evidence, ablation or a Checker B receipt
# cannot be met here and are not claimed. What is verified below is the schema
# layer and the planner methods, over symbolic measures and move sets, with no
# problem named anywhere in the pack or in this suite.
#
# The suite imports the package under whatever name the checkout carries
# (`hyge` on the author's machine, `cat_theo_machine` here) so it runs
# unchanged from either.
#
# Host layer only below: file paths, timings, counting and printing. Every
# assertion about the machine is a Compare / IdentityCompare / IsPair on
# machine terms, and the printer resolves names by IdentityCompare against a
# table of the atoms this file created -- it never reaches into a machine value
# for a payload, and it never takes a Python id().

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
persistence = importlib.import_module(PACKAGE + ".persistence")
packs = importlib.import_module(PACKAGE + ".packs")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
main_mod = importlib.import_module(PACKAGE + ".main")

T0 = time.time()
EMPTY = M.EmptyList

print("=== TEST 23: W10 Engel Strategies ===")
print()

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    line = "    PASS  " if ok else "    FAIL  "
    if detail:
        line = line + name + "  -- " + detail
    else:
        line = line + name
    print(line)


# ---------------------------------------------------------------------------
# host-layer helpers
# ---------------------------------------------------------------------------

NAMES = EMPTY


def named(term, name):
    """Register a name for an atom the suite itself created."""
    global NAMES
    NAMES = M.Pair(M.Pair(term, M.Pair(name, EMPTY)), NAMES)
    return term


def _name_label(label, name):
    return named(label, name)


def name_of(term):
    cursor = NAMES
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        entry = M.Head(cursor)()
        if M.IdentityCompare(M.Head(entry)(), term)() is M.truth_value:
            return M.Head(M.Tail(entry)())()
        cursor = M.Tail(cursor)()
    return "<?>"


_name_label(L.TerminatesLabel, "Terminates")
_name_label(L.MonovariantLabel, "Monovariant")
_name_label(L.SemiInvariantLabel, "SemiInvariant")
_name_label(L.StrictlyDecreasesLabel, "StrictlyDecreases")
_name_label(L.AllMovesDecreaseLabel, "AllMovesDecrease")
_name_label(L.MoveSetLabel, "MoveSet")
_name_label(L.MovesDecreasingLabel, "MovesDecreasing")
_name_label(L.MovesPreservingLabel, "MovesPreserving")
_name_label(L.MovesNonIncreasingLabel, "MovesNonIncreasing")
_name_label(L.NonIncreasesLabel, "NonIncreases")
_name_label(L.AllMovesNonIncreaseLabel, "AllMovesNonIncrease")
_name_label(L.EventuallyDecreasesLabel, "EventuallyDecreases")
_name_label(L.SemiInvariantMethodLabel, "SemiInvariantMethod")
_name_label(L.BoundedBelowLabel, "BoundedBelow")
_name_label(L.InvariantLabel, "Invariant")
_name_label(L.PreservesLabel, "Preserves")
_name_label(L.ReadingLabel, "Reading")
_name_label(L.ApartLabel, "Apart")
_name_label(L.UnreachableLabel, "Unreachable")
_name_label(L.FiniteLabel, "Finite")
_name_label(L.NonEmptyLabel, "NonEmpty")
_name_label(L.MeasureLabel, "Measure")
_name_label(L.DirectionLabel, "Direction")
_name_label(L.AttainsLabel, "Attains")
_name_label(L.CardinalityLabel, "Cardinality")
_name_label(L.TotalMapLabel, "TotalMap")
_name_label(L.NatLessLabel, "NatLess")
_name_label(L.CollisionLabel, "Collision")
_name_label(L.KnowledgeLabel, "Knowledge")
_name_label(L.ExtremalMinLabel, "min")
_name_label(L.ExtremalMaxLabel, "max")
_name_label(M.VarTag, "?")
_name_label(M.Char("p"), "?p")


def RuleReplacementOf(rule):
    return P.RuleReplacement(rule)()


def chain(items):
    """Build a machine list from the host-side items, as packs.py does."""
    out = EMPTY
    index = len(items)
    while index > 0:
        index = index - 1
        out = M.Pair(items[index], out)
    return out


def fact(label, *args):
    return M.Pair(label, chain(args))


def is_list_term(term):
    """Is this a machine list? Atoms -- symbolic move sets -- are not peelable."""
    return M.IdentityCompare(M.IsPair(term)(), M.truth_value)() is M.truth_value


def mpylist(term):
    """Walk a machine list with the machine's own predicates."""
    out = []
    cursor = term
    while is_list_term(cursor):
        out.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return out


def show(term):
    if M.IsPair(term)() is M.truth_value:
        head = show(M.Head(term)())
        tail = mpylist(M.Tail(term)())
        rendered = " ".join(show(item) for item in tail)
        if rendered:
            return "(" + head + " " + rendered + ")"
        return "(" + head + ")"
    return name_of(term)


def has_fact(facts, target):
    cursor = facts
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        if M.Compare(M.Head(cursor)(), target)() is M.truth_value:
            return True
        cursor = M.Tail(cursor)()
    return False


def obligation_goal(obligation):
    """Obligations read (PlannerObligationLabel, id, problem_id, goal, ...)."""
    return M.Head(M.Tail(M.Tail(M.Tail(obligation)())())())()


def all_machine(term, registry):
    """True when `term` is built only from pairs and atoms."""
    if M.IsPair(term)() is M.truth_value:
        return all_machine(M.Head(term)(), registry) and all_machine(M.Tail(term)(), registry)
    return M.IsAtom(term, registry)() is M.truth_value


def closure(facts, rules, registry, rounds=24):
    """
    Monotone forward chaining: every rule contributes its instantiated
    replacement and nothing is consumed. Rules here state strategy
    conclusions; consuming their premises would retract the very facts the
    argument rests on.

    Rules are joined directly with JoinPremises instead of going through
    FilterApplicableRules. That filter is a head-index prefilter: it decides
    which rules *cannot* match, not what they derive, and it costs seconds
    per call in this codebase (see "Diagnosing the slow applicability scan"
    in `08August2026 -- opus 5 answer.md`). Section [9] checks separately
    that the production path admits the very rules this loop relies on, so
    bypassing it here costs no coverage.
    """
    rounds_left = rounds
    state = P.Knowledge(facts)()
    while rounds_left > 0:
        rounds_left = rounds_left - 1
        changed = False
        current = P.KnowledgeFacts(state)()
        cursor = rules
        while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
            rule = M.Head(cursor)()
            cursor = M.Tail(cursor)()
            premises = P.RulePremises(rule)()
            replacement = P.RuleReplacement(rule)()
            bindings = P.JoinPremises(premises, current, EMPTY)()
            bcursor = bindings
            while M.IdentityCompare(bcursor, EMPTY)() is M.false_value:
                added = P.InstantiateFactList(replacement, M.Head(bcursor)())()
                acursor = added
                while M.IdentityCompare(acursor, EMPTY)() is M.false_value:
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


# ---------------------------------------------------------------------------
# [1] boot and load the pack
# ---------------------------------------------------------------------------

print("[1] Booting a fresh runtime and loading packs/engel-strategies.pack.yaml")

runtime = runtime_mod.make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
namespace = main_mod._runtime_namespace()

PACK_PATH = os.path.join(REPO, "packs", "engel-strategies.pack.yaml")
loader = packs.PackLoader(namespace)
pack = loader.load_pack_file(PACK_PATH, graph)
rules = P.CompileRuleChain(pack.rule_chain, registry)()

check("pack name is engel-strategies", pack.name == "engel-strategies", pack.name)
check("pack carries 13 strategy rules", len(mpylist(pack.rule_chain)) == 13,
      str(len(mpylist(pack.rule_chain))) + " rules")
check("phi is Terminates(?p)",
      M.Compare(pack.phi, fact(L.TerminatesLabel, M.Pair(M.VarTag, M.Pair(M.Char("p"), EMPTY))))() is M.truth_value,
      show(pack.phi))
check("the pack names no problem instance (no examples block)",
      len(pack.examples.entries) == 0, str(len(pack.examples.entries)) + " examples")

print()

# ---------------------------------------------------------------------------
# [2] monovariant termination, by recursion over the move list
# ---------------------------------------------------------------------------

print("[2] Monovariant termination  (section 1 took %.1fs)" % (time.time() - T0))

PROBLEM = named(M.Char("P"), "P")
MU = named(M.Char("mu"), "mu")
STEP = named(M.Char("step"), "step")
STEP2 = named(M.Char("step2"), "step2")
STEP3 = named(M.Char("step3"), "step3")
STEP4 = named(M.Char("step4"), "step4")
STEP5 = named(M.Char("step5"), "step5")
ZERO = named(M.Zero, "Zero")
ONE_MOVE = chain([STEP])
TWO_MOVES = chain([STEP, STEP2])
FIVE_MOVES = chain([STEP, STEP2, STEP3, STEP4, STEP5])

terminates = fact(L.TerminatesLabel, PROBLEM)
all_decrease = fact(L.AllMovesDecreaseLabel, PROBLEM, MU)


def monovariant_facts(moves, decreasing, bound=True):
    items = [fact(L.MonovariantLabel, PROBLEM, MU), fact(L.MoveSetLabel, PROBLEM, moves)]
    for move in (mpylist(moves) if is_list_term(moves) else ()):
        if move in decreasing:
            items.append(fact(L.StrictlyDecreasesLabel, move, MU))
    if bound:
        items.append(fact(L.BoundedBelowLabel, MU, ZERO))
    return chain(items)


final = closure(monovariant_facts(ONE_MOVE, [STEP]), rules, registry)
got = P.KnowledgeFacts(final)()
check("one move + bound derives Terminates", has_fact(got, terminates), show(final))

final = closure(monovariant_facts(TWO_MOVES, [STEP, STEP2]), rules, registry)
got = P.KnowledgeFacts(final)()
check("two moves + bound derives Terminates", has_fact(got, terminates), show(final))
check("  ... and AllMovesDecrease on the way", has_fact(got, all_decrease))

final = closure(monovariant_facts(FIVE_MOVES, [STEP, STEP2, STEP3, STEP4, STEP5]), rules, registry)
got = P.KnowledgeFacts(final)()
check("five moves + bound derives Terminates", has_fact(got, terminates), show(final))
check("  ... so the recursion is not pinned to a list length", has_fact(got, all_decrease))

final = closure(monovariant_facts(TWO_MOVES, [STEP]), rules, registry)
got = P.KnowledgeFacts(final)()
check("one of two moves not decreasing refuses AllMovesDecrease", not has_fact(got, all_decrease))
check("  ... and therefore refuses Terminates", not has_fact(got, terminates))

final = closure(monovariant_facts(FIVE_MOVES, [STEP, STEP2, STEP4, STEP5]), rules, registry)
got = P.KnowledgeFacts(final)()
check("a single failure in the middle of five refuses the universal",
      not has_fact(got, all_decrease) and not has_fact(got, terminates))

final = closure(monovariant_facts(FIVE_MOVES, [STEP5, STEP4, STEP3, STEP2]), rules, registry)
got = P.KnowledgeFacts(final)()
check("  ... including when only the first move is the failure",
      not has_fact(got, all_decrease) and not has_fact(got, terminates))

final = closure(monovariant_facts(ONE_MOVE, [STEP], bound=False), rules, registry)
got = P.KnowledgeFacts(final)()
check("no bound refuses Terminates", not has_fact(got, terminates))
check("  ... while AllMovesDecrease still holds", has_fact(got, all_decrease))

final = closure(chain([
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
]), rules, registry)
got = P.KnowledgeFacts(final)()
check("an undeclared measure refuses Terminates", not has_fact(got, terminates))

SYMBOLIC_MOVES = named(M.Char("moves"), "moves")
final = closure(monovariant_facts(SYMBOLIC_MOVES, [SYMBOLIC_MOVES]), rules, registry)
got = P.KnowledgeFacts(final)()
check("a symbolic move set cannot be peeled, so it derives nothing",
      not has_fact(got, all_decrease) and not has_fact(got, terminates))

print()

# ---------------------------------------------------------------------------
# [3] semi-invariants
# ---------------------------------------------------------------------------

print("[3] Semi-invariant termination")

eventually = fact(L.EventuallyDecreasesLabel, PROBLEM, MU)
all_non_increase = fact(L.AllMovesNonIncreaseLabel, PROBLEM, MU)


def semi_facts(moves, non_increasing, bound=True, eventual=True):
    items = [fact(L.SemiInvariantLabel, PROBLEM, MU), fact(L.MoveSetLabel, PROBLEM, moves)]
    for move in (mpylist(moves) if is_list_term(moves) else ()):
        if move in non_increasing:
            items.append(fact(L.NonIncreasesLabel, move, MU))
    if bound:
        items.append(fact(L.BoundedBelowLabel, MU, ZERO))
    if eventual:
        items.append(eventually)
    return chain(items)


final = closure(semi_facts(ONE_MOVE, [STEP]), rules, registry)
got = P.KnowledgeFacts(final)()
check("never rises + drops eventually + bounded derives Terminates",
      has_fact(got, terminates), show(final))
check("  ... and AllMovesNonIncrease on the way", has_fact(got, all_non_increase))

final = closure(semi_facts(FIVE_MOVES, [STEP, STEP2, STEP3, STEP4, STEP5]), rules, registry)
got = P.KnowledgeFacts(final)()
check("five non-increasing moves still derive Terminates", has_fact(got, terminates))

# The drop is an obligation, not an assumption: without it a measure that
# simply sits still would pass every obligation and prove nothing.
final = closure(semi_facts(FIVE_MOVES, [STEP, STEP2, STEP3, STEP4, STEP5], eventual=False),
                rules, registry)
got = P.KnowledgeFacts(final)()
check("a semi-invariant that is never shown to drop refuses Terminates",
      not has_fact(got, terminates))
check("  ... even though the universal still holds", has_fact(got, all_non_increase))

final = closure(semi_facts(FIVE_MOVES, [STEP, STEP2, STEP4, STEP5]), rules, registry)
got = P.KnowledgeFacts(final)()
check("one move that may rise refuses the universal",
      not has_fact(got, all_non_increase) and not has_fact(got, terminates))

final = closure(semi_facts(FIVE_MOVES, [STEP2, STEP3, STEP4, STEP5]), rules, registry)
got = P.KnowledgeFacts(final)()
check("  ... including when it is the first move", not has_fact(got, terminates))

final = closure(semi_facts(ONE_MOVE, [STEP], bound=False), rules, registry)
got = P.KnowledgeFacts(final)()
check("no bound refuses Terminates", not has_fact(got, terminates))

# A symbolic move set cannot be peeled, so the universal is owed whole.
final = closure(semi_facts(SYMBOLIC_MOVES, []), rules, registry)
got = P.KnowledgeFacts(final)()
check("a symbolic move set derives nothing on its own", not has_fact(got, terminates))

final = closure(chain([fact(L.SemiInvariantLabel, PROBLEM, MU),
                       fact(L.MoveSetLabel, PROBLEM, SYMBOLIC_MOVES),
                       all_non_increase,
                       eventually,
                       fact(L.BoundedBelowLabel, MU, ZERO)]), rules, registry)
got = P.KnowledgeFacts(final)()
check("  ... it must supply AllMovesNonIncrease itself", has_fact(got, terminates))

# Engel's distinction is preserved: a semi-invariant is weaker than a
# monovariant, and pretending otherwise would make the term meaningless.
final = closure(chain([
    fact(L.MonovariantLabel, PROBLEM, MU),
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.NonIncreasesLabel, STEP, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
]), rules, registry)
got = P.KnowledgeFacts(final)()
check("a declared monovariant that only never rises does not terminate",
      not has_fact(got, terminates), show(final))

print()

# ---------------------------------------------------------------------------
# [4] invariance obstruction
# ---------------------------------------------------------------------------

print("[4] Invariance obstruction")

PHI = named(M.Char("phi"), "phi")
START_S = named(M.Char("start"), "start")
TARGET_S = named(M.Char("target"), "target")
ODD = named(M.Char("odd"), "odd")
EVEN = named(M.Char("even"), "even")
unreachable = fact(L.UnreachableLabel, PROBLEM, TARGET_S)
inv_phi = fact(L.InvariantLabel, PROBLEM, PHI)


def invariance_facts(moves, preserving):
    items = [fact(L.MoveSetLabel, PROBLEM, moves)]
    for move in mpylist(moves):
        if move in preserving:
            items.append(fact(L.PreservesLabel, move, PHI))
    items.append(fact(L.ReadingLabel, PHI, START_S, ODD))
    items.append(fact(L.ReadingLabel, PHI, TARGET_S, EVEN))
    items.append(fact(L.ApartLabel, ODD, EVEN))
    return chain(items)


final = closure(invariance_facts(ONE_MOVE, [STEP]), rules, registry)
got = P.KnowledgeFacts(final)()
check("a preserved phi makes Invariant", has_fact(got, inv_phi))
check("different readings obstruct the target", has_fact(got, unreachable), show(final))

final = closure(invariance_facts(FIVE_MOVES, [STEP, STEP2, STEP3, STEP4, STEP5]), rules, registry)
got = P.KnowledgeFacts(final)()
check("five preserving moves still make Invariant", has_fact(got, inv_phi))
check("  ... and still obstruct", has_fact(got, unreachable))

final = closure(invariance_facts(TWO_MOVES, [STEP]), rules, registry)
got = P.KnowledgeFacts(final)()
check("one unpreserved move of two refuses Invariant", not has_fact(got, inv_phi))
check("  ... and refuses the obstruction", not has_fact(got, unreachable))

final = closure(invariance_facts(FIVE_MOVES, [STEP, STEP2, STEP4, STEP5]), rules, registry)
got = P.KnowledgeFacts(final)()
check("a single gap in the middle refuses Invariant",
      not has_fact(got, inv_phi) and not has_fact(got, unreachable))

final = closure(chain([
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.PreservesLabel, STEP, PHI),
    fact(L.ReadingLabel, PHI, START_S, ODD),
    fact(L.ReadingLabel, PHI, TARGET_S, ODD),
]), rules, registry)
got = P.KnowledgeFacts(final)()
check("equal readings obstruct nothing", has_fact(got, inv_phi) and not has_fact(got, unreachable))

print()

# ---------------------------------------------------------------------------
# [5] extremal principle -- the direction is supplied, never assumed
# ---------------------------------------------------------------------------

print("[5] Extremal principle")

FAMILY = named(M.Char("F"), "F")
MIN_DIR = named(Planner.ExtremalMin()(), "(min)")
MAX_DIR = named(Planner.ExtremalMax()(), "(max)")
attains_min = fact(L.AttainsLabel, FAMILY, MU, Planner.ExtremalMin()())
attains_max = fact(L.AttainsLabel, FAMILY, MU, Planner.ExtremalMax()())

base_family = chain([
    fact(L.FiniteLabel, FAMILY),
    fact(L.NonEmptyLabel, FAMILY),
    fact(L.MeasureLabel, FAMILY, MU),
])


def with_direction(direction):
    return M.Pair(fact(L.DirectionLabel, direction), base_family)


final = closure(with_direction(Planner.ExtremalMin()()), rules, registry)
got = P.KnowledgeFacts(final)()
check("a finite nonempty measured family attains the direction it asks for",
      has_fact(got, attains_min) and not has_fact(got, attains_max), show(final))

final = closure(with_direction(Planner.ExtremalMax()()), rules, registry)
got = P.KnowledgeFacts(final)()
check("  ... and only that direction",
      has_fact(got, attains_max) and not has_fact(got, attains_min))

final = closure(base_family, rules, registry)
got = P.KnowledgeFacts(final)()
check("with no direction supplied nothing is attained",
      not has_fact(got, attains_min) and not has_fact(got, attains_max))

final = closure(M.Pair(fact(L.DirectionLabel, Planner.ExtremalMin()()), chain([
    fact(L.NonEmptyLabel, FAMILY),
    fact(L.MeasureLabel, FAMILY, MU),
])), rules, registry)
got = P.KnowledgeFacts(final)()
check("an infinite family attains nothing",
      not has_fact(got, attains_min) and not has_fact(got, attains_max))

print()

# ---------------------------------------------------------------------------
# [6] box principle -- obligationed by the planner, not asserted by the pack
# ---------------------------------------------------------------------------

print("[6] Box principle is obligationed, not asserted")

DOM = named(M.Char("D"), "D")
COD = named(M.Char("C"), "C")
ASSIGN = named(M.Char("f"), "f")
N = named(M.Char("n"), "n")
K = named(M.Char("k"), "k")

collision = fact(L.CollisionLabel, ASSIGN)

# The pack must not carry the counting conclusion as a rule: from a cardinality
# mismatch and a total map, "two pigeons share a box" is arithmetic the machine
# should establish, not a schema it should be handed.
concludes_collision = False
rcursor = pack.rule_chain
while M.IdentityCompare(rcursor, EMPTY)() is M.false_value:
    rule = M.Head(rcursor)()
    replacement = P.RuleReplacement(rule)()
    fcursor = replacement
    while M.IdentityCompare(fcursor, EMPTY)() is M.false_value:
        if M.IdentityCompare(M.Head(M.Head(fcursor)())(), L.CollisionLabel)() is M.truth_value:
            concludes_collision = True
        fcursor = M.Tail(fcursor)()
    rcursor = M.Tail(rcursor)()
check("no rule in the pack concludes a collision", not concludes_collision)

# It is obligationed instead, by the Pigeonhole method that already exists.
pigeonhole_method = Planner.Pigeonhole(DOM, COD, ASSIGN)()
domain_size = M.Pair(L.CardinalityLabel, M.Pair(DOM, EMPTY))
codomain_size = M.Pair(L.CardinalityLabel, M.Pair(COD, EMPTY))
box_obligations = Planner.PigeonholeObligations(pigeonhole_method, domain_size, codomain_size)()

check("Pigeonhole obligationes finiteness of both sides",
      has_fact(box_obligations, fact(L.FiniteLabel, DOM))
      and has_fact(box_obligations, fact(L.FiniteLabel, COD)))
check("  ... totality of the assignment",
      has_fact(box_obligations, fact(L.TotalMapLabel, ASSIGN, DOM, COD)))
check("  ... both cardinalities",
      has_fact(box_obligations, fact(L.CardinalityLabel, DOM, domain_size))
      and has_fact(box_obligations, fact(L.CardinalityLabel, COD, codomain_size)))
check("  ... and the strict inequality that makes the box bite",
      has_fact(box_obligations, fact(L.NatLessLabel, codomain_size, domain_size)))
check("  ... and never names the pigeons that collide",
      not has_fact(box_obligations, collision))

final = closure(chain([
    fact(L.FiniteLabel, DOM),
    fact(L.FiniteLabel, COD),
    fact(L.TotalMapLabel, ASSIGN, DOM, COD),
    fact(L.CardinalityLabel, DOM, N),
    fact(L.CardinalityLabel, COD, K),
    fact(L.NatLessLabel, K, N),
]), rules, registry)
got = P.KnowledgeFacts(final)()
check("so the facts alone do not manufacture a collision",
      not has_fact(got, collision), show(final))

print()

# ---------------------------------------------------------------------------
# [7] planner methods
# ---------------------------------------------------------------------------

print("[7] Planner method decomposition")

monovariant_method = Planner.Monovariant(PROBLEM, MU, ZERO, TWO_MOVES)()
obligations = Planner.MonovariantObligations(monovariant_method)()

check("Monovariant obligationes the move set", has_fact(obligations, fact(L.MoveSetLabel, PROBLEM, TWO_MOVES)))
check("  ... the bound", has_fact(obligations, fact(L.BoundedBelowLabel, MU, ZERO)))
check("  ... and each move separately",
      has_fact(obligations, fact(L.StrictlyDecreasesLabel, STEP, MU))
      and has_fact(obligations, fact(L.StrictlyDecreasesLabel, STEP2, MU)))
check("  ... and not the universal it cannot phrase", not has_fact(obligations, all_decrease))
check("Monovariant concludes Terminates",
      M.Compare(Planner.MonovariantConclusion(monovariant_method)(), terminates)() is M.truth_value)

symbolic_method = Planner.Monovariant(PROBLEM, MU, ZERO, SYMBOLIC_MOVES)()
symbolic_obligations = Planner.MonovariantObligations(symbolic_method)()
check("a symbolic move set obligationes the universal instead",
      has_fact(symbolic_obligations, all_decrease))
check("  ... and asks for no individual move",
      not has_fact(symbolic_obligations, fact(L.StrictlyDecreasesLabel, SYMBOLIC_MOVES, MU)))

semi_method = Planner.SemiInvariant(PROBLEM, MU, ZERO, TWO_MOVES)()
semi_obligations = Planner.SemiInvariantObligations(semi_method)()
check("SemiInvariant obligationes the move set",
      has_fact(semi_obligations, fact(L.MoveSetLabel, PROBLEM, TWO_MOVES)))
check("  ... the bound", has_fact(semi_obligations, fact(L.BoundedBelowLabel, MU, ZERO)))
check("  ... the eventual drop it must still earn",
      has_fact(semi_obligations, eventually))
check("  ... each move as NonIncreases, not a strict drop",
      has_fact(semi_obligations, fact(L.NonIncreasesLabel, STEP, MU))
      and has_fact(semi_obligations, fact(L.NonIncreasesLabel, STEP2, MU))
      and not has_fact(semi_obligations, fact(L.StrictlyDecreasesLabel, STEP, MU)))
check("  ... and not the universal it cannot phrase",
      not has_fact(semi_obligations, all_non_increase))
check("SemiInvariant concludes Terminates",
      M.Compare(Planner.SemiInvariantConclusion(semi_method)(), terminates)() is M.truth_value)

symbolic_semi = Planner.SemiInvariant(PROBLEM, MU, ZERO, SYMBOLIC_MOVES)()
symbolic_semi_obligations = Planner.SemiInvariantObligations(symbolic_semi)()
check("a symbolic move set obligationes the universal NonIncrease instead",
      has_fact(symbolic_semi_obligations, all_non_increase))

invariance_method = Planner.Invariance(PROBLEM, PHI, ONE_MOVE, START_S, ODD, TARGET_S, EVEN)()
inv_obligations = Planner.InvarianceObligations(invariance_method)()
check("Invariance obligationes preservation",
      has_fact(inv_obligations, fact(L.PreservesLabel, STEP, PHI)))
check("  ... both readings",
      has_fact(inv_obligations, fact(L.ReadingLabel, PHI, START_S, ODD))
      and has_fact(inv_obligations, fact(L.ReadingLabel, PHI, TARGET_S, EVEN)))
check("  ... and their distinctness", has_fact(inv_obligations, fact(L.ApartLabel, ODD, EVEN)))
check("Invariance concludes Unreachable",
      M.Compare(Planner.InvarianceConclusion(invariance_method)(), unreachable)() is M.truth_value)

symbolic_invariance = Planner.Invariance(PROBLEM, PHI, SYMBOLIC_MOVES, START_S, ODD, TARGET_S, EVEN)()
symbolic_invariance_obligations = Planner.InvarianceObligations(symbolic_invariance)()
check("a symbolic move set obligationes the universal Invariant instead",
      has_fact(symbolic_invariance_obligations, inv_phi))
check("  ... and asks for no individual move",
      not has_fact(symbolic_invariance_obligations, fact(L.PreservesLabel, SYMBOLIC_MOVES, PHI)))

print()

# ---------------------------------------------------------------------------
# [8] the planner actually decomposes with these methods
# ---------------------------------------------------------------------------

print("[8] Planner run over the strategy pack")

start_state = P.Knowledge(monovariant_facts(TWO_MOVES, [STEP, STEP2]))()
goal = terminates

problem_term = Planner.PlannerProblem(start_state, goal, rules, runtime.theorem_heuristic,
                                      chain([monovariant_method]))()
state = Planner.PlannerState(problem_term, registry)()
ran = Planner.PlannerRun(graph, state, M.three)()

state_obligations = M.Head(M.Tail(ran)())()
alternatives = Planner.PlannerStateAlternatives(ran)()

found_method = EMPTY
cursor = alternatives
while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
    alternative = M.Head(cursor)()
    if M.TermEqual(Planner.PlannerAlternativeMethod(alternative)(), monovariant_method)() is M.truth_value:
        found_method = alternative
        cursor = EMPTY
    else:
        cursor = M.Tail(cursor)()

check("the monovariant method became an alternative",
      M.IdentityCompare(found_method, EMPTY)() is M.false_value)

if M.IdentityCompare(found_method, EMPTY)() is M.false_value:
    children = Planner.PlannerAlternativeChildren(found_method)()
    check("  ... and spawned one child per obligation",
          len(mpylist(children)) == len(mpylist(obligations)),
          str(len(mpylist(children))) + " children for " + str(len(mpylist(obligations))) + " obligations")
    matched = 0
    shown = []
    ccursor = children
    while M.IdentityCompare(ccursor, EMPTY)() is M.false_value:
        child_id = M.Head(ccursor)()
        ocursor = state_obligations
        while M.IdentityCompare(ocursor, EMPTY)() is M.false_value:
            obligation = M.Head(ocursor)()
            if M.Compare(M.Head(M.Tail(obligation)())(), child_id)() is M.truth_value:
                goal_term = obligation_goal(obligation)
                shown.append(show(goal_term))
                if has_fact(obligations, goal_term):
                    matched = matched + 1
                ocursor = EMPTY
            else:
                ocursor = M.Tail(ocursor)()
        ccursor = M.Tail(ccursor)()
    check("  ... each child goal is one of the obligations",
          matched == len(mpylist(children)), ", ".join(shown))

print()

# ---------------------------------------------------------------------------
# [9] the production admission path agrees with the join used above
# ---------------------------------------------------------------------------

print("[9] Production admission path")

admission_facts = monovariant_facts(ONE_MOVE, [STEP])
before = P.FilterApplicableRules(rules, P.Knowledge(admission_facts)(), registry)()
after = P.FilterApplicableRules(rules, closure(admission_facts, rules, registry), registry)()


def admits(applicable, rule_id):
    wanted = RuleReplacementOf(pack.rule_map[rule_id])
    cursor = applicable
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        if M.TermEqual(RuleReplacementOf(M.Head(cursor)()), wanted)() is M.truth_value:
            return True
        cursor = M.Tail(cursor)()
    return False


check("before the derivation the universal is missing, so termination is not admitted",
      admits(before, "thread_decreasing_moves") and not admits(before, "monovariant_terminates"))
check("  ... and the peeling rule is not admitted either",
      not admits(before, "decreasing_moves_step"))
check("after it, the production path admits monovariant_terminates",
      admits(after, "monovariant_terminates"))
check("and refuses extremal_choice while no direction has been supplied",
      not admits(before, "extremal_choice") and not admits(after, "extremal_choice"))

print()

# ---------------------------------------------------------------------------
# [10] the new labels survive a snapshot round-trip
# ---------------------------------------------------------------------------

print("[10] Snapshot symbol round-trip")

NEW_LABEL_NAMES = (
    "MonovariantLabel",
    "SemiInvariantLabel",
    "StrictlyDecreasesLabel",
    "AllMovesDecreaseLabel",
    "MoveSetLabel",
    "MovesDecreasingLabel",
    "MovesPreservingLabel",
    "MovesNonIncreasingLabel",
    "NonIncreasesLabel",
    "AllMovesNonIncreaseLabel",
    "EventuallyDecreasesLabel",
    "SemiInvariantMethodLabel",
    "DirectionLabel",
    "MeasureLabel",
    "ReadingLabel",
    "TerminatesLabel",
    "MonovariantMethodLabel",
    "InvarianceMethodLabel",
)

snapshot_path = os.path.join(tempfile.mkdtemp(prefix="test20-"), "snapshot.json")
codec = persistence.SnapshotCodec(namespace)
codec.save(graph, snapshot_path)
restored = codec.load(snapshot_path)
os.remove(snapshot_path)
os.rmdir(os.path.dirname(snapshot_path))

absent = [name for name in NEW_LABEL_NAMES if name not in restored.symbols]
check("every new label is written into the snapshot symbol table", not absent, ",".join(absent))

identity_ok = True
for name in NEW_LABEL_NAMES:
    if name in restored.symbols:
        if restored.symbols[name] is not namespace[name]:
            identity_ok = False
check("  ... and restores to the live label object", identity_ok)

print()

# ---------------------------------------------------------------------------
# [11] representation: everything the pack produced is machine-side
# ---------------------------------------------------------------------------

print("[11] Representation checks")

rule_ok = True
rcursor = pack.rule_chain
while M.IdentityCompare(rcursor, EMPTY)() is M.false_value:
    rule = M.Head(rcursor)()
    pcursor = P.RulePremises(rule)()
    while M.IdentityCompare(pcursor, EMPTY)() is M.false_value:
        if not all_machine(M.Head(pcursor)(), registry):
            rule_ok = False
        pcursor = M.Tail(pcursor)()
    if not all_machine(P.RuleReplacement(rule)(), registry):
        rule_ok = False
    rcursor = M.Tail(rcursor)()
check("every pack rule is built from pairs and atoms only", rule_ok)

check("Terminates(P) is a machine pair, not a host string",
      M.IsPair(terminates)() is M.truth_value
      and M.IdentityCompare(M.Head(terminates)(), L.TerminatesLabel)() is M.truth_value)

derived = closure(monovariant_facts(ONE_MOVE, [STEP]), rules, registry)
check("the derived knowledge is a Knowledge term", P.IsKnowledge(derived)() is M.truth_value)

fact_cursor = P.KnowledgeFacts(derived)()
facts_ok = True
while M.IdentityCompare(fact_cursor, EMPTY)() is M.false_value:
    if not all_machine(M.Head(fact_cursor)(), registry):
        facts_ok = False
    fact_cursor = M.Tail(fact_cursor)()
check("  ... whose every fact is machine-side", facts_ok)

print()
print("=== TEST 23 RESULTS ===")
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
    print("=== TEST 23 FAILED ===")
    sys.exit(1)
print("=== TEST 23 COMPLETE ===")
