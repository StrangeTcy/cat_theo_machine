# ============================================================
# TEST 20: W10 Engel Strategies
#          monovariants, semi-invariants, invariance,
#          extremal principle, box principle
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test20_engel_strategies.py
#
# The suite imports the package under whatever name the checkout carries
# (`hyge` on the author's machine, `cat_theo_machine` here) so it runs
# unchanged from either.
#
# Only *.md-free, machine-side facts are asserted: every check below is a
# Compare/IdentityCompare on machine terms. The printer is host-layer only and
# maps the atoms this file created back to the names it gave them; it never
# reaches into a machine value for a payload.

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
packs = importlib.import_module(PACKAGE + ".packs")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
persistence = importlib.import_module(PACKAGE + ".persistence")
main_mod = importlib.import_module(PACKAGE + ".main")

T0 = time.time()
EMPTY = M.EmptyList

print("=== TEST 20: W10 Engel Strategies ===")
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
# host-layer helpers (Python natives live here, never inside a machine term)
# ---------------------------------------------------------------------------

NAMES = {}


def RuleReplacementOf(rule):
    return P.RuleReplacement(rule)()


def _name_label(label, name):
    NAMES[id(label)] = name
    return label


_name_label(L.TerminatesLabel, "Terminates")
_name_label(L.MonovariantLabel, "Monovariant")
_name_label(L.SemiInvariantLabel, "SemiInvariant")
_name_label(L.StrictlyDecreasesLabel, "StrictlyDecreases")
_name_label(L.AllMovesDecreaseLabel, "AllMovesDecrease")
_name_label(L.MoveSetLabel, "MoveSet")
_name_label(L.BoundedBelowLabel, "BoundedBelow")
_name_label(L.InvariantLabel, "Invariant")
_name_label(L.PreservesLabel, "Preserves")
_name_label(L.ReadingLabel, "Reading")
_name_label(L.ApartLabel, "Apart")
_name_label(L.UnreachableLabel, "Unreachable")
_name_label(L.FiniteLabel, "Finite")
_name_label(L.NonEmptyLabel, "NonEmpty")
_name_label(L.MeasureLabel, "Measure")
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


def named(term, name):
    NAMES[id(term)] = name
    return term


def chain(items):
    out = EMPTY
    for item in reversed(list(items)):
        out = M.Pair(item, out)
    return out


def fact(label, *args):
    return M.Pair(label, chain(args))


def mpylist(term):
    """Walk a machine list with the machine's own predicates."""
    out = []
    cursor = term
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        out.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return out


def show(term):
    if M.IsPair(term)() is M.truth_value:
        head = show(M.Head(term)())
        if head.startswith("(") or " " in head:
            return "(" + head + ")" + "".join(" " + show(a) for a in mpylist(M.Tail(term)()))
        return "(" + head + "".join(" " + show(a) for a in mpylist(M.Tail(term)())) + ")"
    return NAMES.get(id(term), "<?>")


def obligation_goal(obligation):
    """Obligations read (PlannerObligationLabel, id, problem_id, goal, ...)."""
    return M.Head(M.Tail(M.Tail(M.Tail(obligation)())())())()


def has_fact(facts, target):
    cursor = facts
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        if M.Compare(M.Head(cursor)(), target)() is M.truth_value:
            return True
        cursor = M.Tail(cursor)()
    return False


def all_machine(term, registry):
    """True when `term` is built only from pairs and atoms."""
    if M.IsPair(term)() is M.truth_value:
        return all_machine(M.Head(term)(), registry) and all_machine(M.Tail(term)(), registry)
    return M.IsAtom(term, registry)() is M.truth_value


def closure(facts, rules, registry, rounds=8):
    """
    Monotone forward chaining: every rule contributes its instantiated
    replacement and nothing is consumed. Rules here state strategy
    conclusions; consuming their premises would retract the very facts the
    argument rests on.

    Rules are joined directly with JoinPremises instead of going through
    FilterApplicableRules. That filter is a head-index prefilter: it decides
    which rules *cannot* match, not what they derive, and it costs seconds
    per call in this codebase (see "Diagnosing the slow applicability scan"
    in `08August2026 -- opus 5 answer.md`). Section [10] checks separately
    that the production path admits the very rules this loop relies on, so
    bypassing it here costs no coverage.
    """
    state = P.Knowledge(facts)()
    for _ in range(rounds):
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
check("pack carries 11 strategy rules", len(mpylist(pack.rule_chain)) == 11,
      str(len(mpylist(pack.rule_chain))) + " rules")
check("phi is Terminates(?p)", M.Compare(pack.phi, fact(L.TerminatesLabel, M.Pair(M.VarTag, M.Pair(M.Char("p"), EMPTY))))() is M.truth_value,
      show(pack.phi))
check("two examples are registered", "engel_monovariant_terminates" in pack.examples and "engel_invariant_obstruction" in pack.examples)

print()

# ---------------------------------------------------------------------------
# [2] monovariant termination
# ---------------------------------------------------------------------------

print("[2] Monovariant termination  (section 1 took %.1fs)" % (time.time() - T0))

PROBLEM = named(M.Char("P"), "P")
MU = named(M.Char("mu"), "mu")
STEP = named(M.Char("step"), "step")
STEP2 = named(M.Char("step2"), "step2")
ZERO = named(M.Zero, "Zero")
ONE_MOVE = chain([STEP])
TWO_MOVES = chain([STEP, STEP2])

terminates = fact(L.TerminatesLabel, PROBLEM)
all_decrease = fact(L.AllMovesDecreaseLabel, PROBLEM, MU)
invariant = fact(L.InvariantLabel, PROBLEM, MU)

# one move, bounded below
facts = chain([
    fact(L.MonovariantLabel, PROBLEM, MU),
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("one move + bound derives Terminates", has_fact(got, terminates), show(final))

# two moves, both decreasing
facts = chain([
    fact(L.MonovariantLabel, PROBLEM, MU),
    fact(L.MoveSetLabel, PROBLEM, TWO_MOVES),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
    fact(L.StrictlyDecreasesLabel, STEP2, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("two moves + bound derives Terminates", has_fact(got, terminates), show(final))
check("  ... and AllMovesDecrease on the way", has_fact(got, all_decrease))

# no bound: the plumbing works, the conclusion does not follow
facts = chain([
    fact(L.MonovariantLabel, PROBLEM, MU),
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("no bound refuses Terminates", not has_fact(got, terminates))
check("  ... while AllMovesDecrease still holds", has_fact(got, all_decrease))

# one of two moves does not decrease: the universal must not be claimed
facts = chain([
    fact(L.MonovariantLabel, PROBLEM, MU),
    fact(L.MoveSetLabel, PROBLEM, TWO_MOVES),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("a non-decreasing move refuses AllMovesDecrease", not has_fact(got, all_decrease))
check("  ... and therefore refuses Terminates", not has_fact(got, terminates))

# no monovariant declared
facts = chain([
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("an undeclared measure refuses Terminates", not has_fact(got, terminates))

print()

# ---------------------------------------------------------------------------
# [3] semi-invariants
# ---------------------------------------------------------------------------

print("[3] Semi-invariant termination")

KSTEPS = named(M.Char("k"), "k")
facts = chain([
    fact(L.SemiInvariantLabel, PROBLEM, MU, KSTEPS),
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("semi-invariant + bound derives Terminates", has_fact(got, terminates), show(final))

facts = chain([
    fact(L.SemiInvariantLabel, PROBLEM, MU, KSTEPS),
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("semi-invariant without a bound refuses Terminates", not has_fact(got, terminates))

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

facts = chain([
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.PreservesLabel, STEP, PHI),
    fact(L.ReadingLabel, PHI, START_S, ODD),
    fact(L.ReadingLabel, PHI, TARGET_S, EVEN),
    fact(L.ApartLabel, ODD, EVEN),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("a preserved phi makes Invariant", has_fact(got, inv_phi))
check("different readings obstruct the target", has_fact(got, unreachable), show(final))

facts = chain([
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.PreservesLabel, STEP, PHI),
    fact(L.ReadingLabel, PHI, START_S, ODD),
    fact(L.ReadingLabel, PHI, TARGET_S, ODD),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("equal readings obstruct nothing", has_fact(got, inv_phi) and not has_fact(got, unreachable))

facts = chain([
    fact(L.MoveSetLabel, PROBLEM, TWO_MOVES),
    fact(L.PreservesLabel, STEP, PHI),
    fact(L.ReadingLabel, PHI, START_S, ODD),
    fact(L.ReadingLabel, PHI, TARGET_S, EVEN),
    fact(L.ApartLabel, ODD, EVEN),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("one unpreserved move of two refuses Invariant", not has_fact(got, inv_phi))
check("  ... and refuses the obstruction", not has_fact(got, unreachable))

print()

# ---------------------------------------------------------------------------
# [5] extremal principle
# ---------------------------------------------------------------------------

print("[5] Extremal principle")

FAMILY = named(M.Char("F"), "F")
attains_min = fact(L.AttainsLabel, FAMILY, MU, Planner.ExtremalMin()())
attains_max = fact(L.AttainsLabel, FAMILY, MU, Planner.ExtremalMax()())

facts = chain([
    fact(L.FiniteLabel, FAMILY),
    fact(L.NonEmptyLabel, FAMILY),
    fact(L.MeasureLabel, FAMILY, MU),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("a finite nonempty measured family attains its min", has_fact(got, attains_min), show(final))
check("  ... and its max", has_fact(got, attains_max))

facts = chain([
    fact(L.NonEmptyLabel, FAMILY),
    fact(L.MeasureLabel, FAMILY, MU),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("an infinite family attains nothing", not has_fact(got, attains_min) and not has_fact(got, attains_max))

print()

# ---------------------------------------------------------------------------
# [6] box principle
# ---------------------------------------------------------------------------

print("[6] Box principle")

DOM = named(M.Char("D"), "D")
COD = named(M.Char("C"), "C")
ASSIGN = named(M.Char("f"), "f")
N = named(M.Char("n"), "n")
K = named(M.Char("k"), "k")
collision = fact(L.CollisionLabel, ASSIGN)

facts = chain([
    fact(L.FiniteLabel, DOM),
    fact(L.FiniteLabel, COD),
    fact(L.TotalMapLabel, ASSIGN, DOM, COD),
    fact(L.CardinalityLabel, DOM, N),
    fact(L.CardinalityLabel, COD, K),
    fact(L.NatLessLabel, K, N),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("more pigeons than boxes collides", has_fact(got, collision), show(final))

facts = chain([
    fact(L.FiniteLabel, DOM),
    fact(L.FiniteLabel, COD),
    fact(L.TotalMapLabel, ASSIGN, DOM, COD),
    fact(L.CardinalityLabel, DOM, N),
    fact(L.CardinalityLabel, COD, K),
    fact(L.NatLessLabel, N, K),
])
final = closure(facts, rules, registry)
got = P.KnowledgeFacts(final)()
check("more boxes than pigeons collides nothing", not has_fact(got, collision))

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

SYMBOLIC_MOVES = named(M.Char("moves"), "moves")
symbolic_method = Planner.Monovariant(PROBLEM, MU, ZERO, SYMBOLIC_MOVES)()
symbolic_obligations = Planner.MonovariantObligations(symbolic_method)()
check("a symbolic move set obligationes the universal instead",
      has_fact(symbolic_obligations, all_decrease))
check("  ... and asks for no individual move",
      not has_fact(symbolic_obligations, fact(L.StrictlyDecreasesLabel, SYMBOLIC_MOVES, MU)))

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

start_state = P.Knowledge(chain([
    fact(L.MonovariantLabel, PROBLEM, MU),
    fact(L.MoveSetLabel, PROBLEM, TWO_MOVES),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
    fact(L.StrictlyDecreasesLabel, STEP2, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
]))()
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
# [10] the production admission path agrees with the join used above
# ---------------------------------------------------------------------------

print("[10] Production admission path")

admission_facts = chain([
    fact(L.MonovariantLabel, PROBLEM, MU),
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
])
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


check("before the derivation AllMovesDecrease is missing, so termination is not admitted",
      admits(before, "decreases_all_one") and not admits(before, "monovariant_terminates"))
check("after it, the production path admits monovariant_terminates",
      admits(after, "monovariant_terminates"))
check("and still refuses the box principle, whose premises are absent",
      not admits(before, "box_principle_collision") and not admits(after, "box_principle_collision"))

print()

# ---------------------------------------------------------------------------
# [11] the new labels survive a snapshot round-trip
# ---------------------------------------------------------------------------

print("[11] Snapshot symbol round-trip")

NEW_LABEL_NAMES = (
    "MonovariantLabel",
    "SemiInvariantLabel",
    "StrictlyDecreasesLabel",
    "AllMovesDecreaseLabel",
    "MoveSetLabel",
    "ReadingLabel",
    "TerminatesLabel",
    "MonovariantMethodLabel",
    "InvarianceMethodLabel",
    "MeasureLabel",
)

snapshot_path = os.path.join(tempfile.mkdtemp(prefix="test20-"), "snapshot.json")
codec = persistence.SnapshotCodec(namespace)
codec.save(graph, snapshot_path)
restored = codec.load(snapshot_path)
os.remove(snapshot_path)
os.rmdir(os.path.dirname(snapshot_path))

absent = [name for name in NEW_LABEL_NAMES if name not in restored.symbols]
check("every new label is written into the snapshot symbol table", not absent, ",".join(absent))
check("  ... and restores to the live label object",
      all(restored.symbols[name] is namespace[name] for name in NEW_LABEL_NAMES if name in restored.symbols))

print()

# ---------------------------------------------------------------------------
# [12] representation: everything the pack produced is machine-side
# ---------------------------------------------------------------------------

print("[12] Representation checks")

rcursor = pack.rule_chain
rule_ok = True
while M.IdentityCompare(rcursor, EMPTY)() is M.false_value:
    rule = M.Head(rcursor)()
    premises = P.RulePremises(rule)()
    replacement = P.RuleReplacement(rule)()
    pcursor = premises
    while M.IdentityCompare(pcursor, EMPTY)() is M.false_value:
        if not all_machine(M.Head(pcursor)(), registry):
            rule_ok = False
        pcursor = M.Tail(pcursor)()
    if not all_machine(replacement, registry):
        rule_ok = False
    rcursor = M.Tail(rcursor)()
check("every pack rule is built from pairs and atoms only", rule_ok)

check("Terminates(P) is a machine pair, not a host string",
      M.IsPair(terminates)() is M.truth_value
      and M.IdentityCompare(M.Head(terminates)(), L.TerminatesLabel)() is M.truth_value)

derived = closure(chain([
    fact(L.MonovariantLabel, PROBLEM, MU),
    fact(L.MoveSetLabel, PROBLEM, ONE_MOVE),
    fact(L.StrictlyDecreasesLabel, STEP, MU),
    fact(L.BoundedBelowLabel, MU, ZERO),
]), rules, registry)
check("the derived knowledge is a Knowledge term",
      P.IsKnowledge(derived)() is M.truth_value)
check("  ... whose every fact is machine-side",
      all(all_machine(f, registry) for f in mpylist(P.KnowledgeFacts(derived)())))

print()
print("=== TEST 20 RESULTS ===")
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = len(RESULTS) - passed
for name, ok, detail in RESULTS:
    if not ok:
        print("  FAILED: " + name + ("  -- " + detail if detail else ""))
print(f"  Checks passed: {passed}/{len(RESULTS)}")
print(f"  Total time:    {time.time() - T0:.3f}s")
print()
if failed:
    print("=== TEST 20 FAILED ===")
    sys.exit(1)
print("=== TEST 20 COMPLETE ===")
