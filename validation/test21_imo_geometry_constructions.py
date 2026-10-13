# ============================================================
# TEST 21: W8 IMO Geometry — auxiliary construction generation
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test21_imo_geometry_constructions.py
#
# Slot 21 is the one `delegation/README.md` pre-allocates to
# `W08-imo-geometry.md`; slot 20 belongs to W7 and 22 to W9.
#
# Scope, stated honestly. This branch carries `matching.py`, `graph.py`,
# `planner.py` and the geometry packs, but not the modules the W8 brief's
# "what already exists" section also names: `checker_b.py`, `graph_task.py`,
# `evaluator.py`, `playground.py` and their suites are all absent. The parts
# of the done-definition that need a Checker B receipt, a ledger record or
# evaluator ablation are therefore NOT met here and are NOT claimed; what is
# verified below is the brief's items 1-3 in the shape this branch supports:
#
#   * a construction generator (`constructions.py`) that proposes candidate
#     auxiliary objects as generic schemas instantiated by machine matching,
#     goal-directed but problem-free (no table of problems, no named
#     auxiliary points -- pinned by the genericity checks in [1] and [7]),
#   * the proposals carried into `planner.py`'s search as Construction
#     methods whose effects become obligations [4],
#   * an end-to-end derivation on an olympiad-style configuration (base
#     angles of an isosceles triangle) whose auxiliary point is minted by
#     the generator and is named nowhere in the tree [2][3],
#   * negative controls: with the generator's proposal withheld the search
#     does not close, and on an unsound (scalene) figure it proposes nothing
#     [3][5] -- without these the generator has not been shown to do
#     anything.
#
# Host layer only below: file paths, timings, counting and printing. Every
# assertion about the machine is a Compare / IdentityCompare / IsPair on
# machine terms; the printer resolves names by IdentityCompare against a
# table of the atoms this file created and never reaches into a machine
# value for a payload.

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
C = importlib.import_module(PACKAGE + ".constructions")
persistence = importlib.import_module(PACKAGE + ".persistence")
packs = importlib.import_module(PACKAGE + ".packs")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
main_mod = importlib.import_module(PACKAGE + ".main")

T0 = time.time()
EMPTY = M.EmptyList

print("=== TEST 21: W8 IMO Geometry constructions ===")
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


def RuleReplacementOf(rule):
    return P.RuleReplacement(rule)()


def chain(items):
    """Build a flat machine list from host items, as packs.py does."""
    out = EMPTY
    index = len(items)
    while index > 0:
        index = index - 1
        out = M.Pair(items[index], out)
    return out


def append(a, b):
    """Concatenate two machine lists (a fact store must stay flat)."""
    return chain(mpylist(a) + mpylist(b))


def fact(label, *args):
    return M.Pair(label, chain(args))


def is_list_term(term):
    """Is this a machine list? Atoms are not walkable."""
    return M.IdentityCompare(M.IsPair(term)(), M.truth_value)() is M.truth_value


def mpylist(term):
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


def goal_hit(goal, facts):
    """Does any fact answer the goal? The goal may carry pattern variables,
    so this is a Match, not a Compare."""
    cursor = facts
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        match = M.Match(goal, M.Head(cursor)())()
        if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
            return True
        cursor = M.Tail(cursor)()
    return False


def count_list(term):
    return len(mpylist(term))


def pattern_var_count(term):
    """Number of VarTag-headed leaves anywhere in a term."""
    if M.IsPair(term)() is M.false_value:
        return 0
    if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
        return 1
    return pattern_var_count(M.Head(term)()) + pattern_var_count(M.Tail(term)())


def closure(facts, rules, registry, rounds=24):
    """
    Monotone forward chaining: every rule contributes its instantiated
    replacement and nothing is consumed. Rules joined directly with
    JoinPremises; section [4] checks separately that the production planner
    admits the same rules, so bypassing the applicability prefilter here
    costs no coverage.
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


def all_machine(term, registry, namespace_atoms):
    """True when `term` is built only from pairs, pattern variables, and
    atoms the namespace already knows (labels). Anything else -- in
    particular a fresh Char constant -- is hardcoded content."""
    if M.IsPair(term)() is M.truth_value:
        if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
            return True
        return all_machine(M.Head(term)(), registry, namespace_atoms) and all_machine(
            M.Tail(term)(), registry, namespace_atoms
        )
    if M.IsAtom(term, registry)() is M.false_value:
        return False
    cursor = namespace_atoms
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        if M.IdentityCompare(M.Head(cursor)(), term)() is M.truth_value:
            return True
        cursor = M.Tail(cursor)()
    return False


# ---------------------------------------------------------------------------
# [1] boot, load, and genericity of the pack
# ---------------------------------------------------------------------------

print("[1] Booting a fresh runtime and loading packs/geometry-constructions.pack.yaml")

runtime = runtime_mod.make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
namespace = main_mod._runtime_namespace()

PACK_PATH = os.path.join(REPO, "packs", "geometry-constructions.pack.yaml")
loader = packs.PackLoader(namespace)
pack = loader.load_pack_file(PACK_PATH, graph)
rules = P.CompileRuleChain(pack.rule_chain, registry)()

# The pack's declared vocabulary: the only atoms its compiled rules may
# contain besides pattern variables. An explicit allowlist is the pin -- a
# Char naming a point or a problem would be neither a variable nor one of
# these labels. (Reading the namespace to resolve the labels is host work on
# a host dict; the membership test itself stays machine-side.)
PACK_VOCABULARY = (
    L.BisectorFromLabel,
    L.TriangleLabel,
    L.LengthLabel,
    L.SegmentLabel,
    L.EqualAngleLabel,
    L.AngleLabel,
    L.PointOnLabel,
    L.CircumcircleOfLabel,
    L.VertexOfLabel,
    L.OnCircleLabel,
    M.VarTag,
    M.EmptyList,
)
namespace_atoms = chain(list(PACK_VOCABULARY))

check("pack name is geometry-constructions", pack.name == "geometry-constructions", pack.name)
check("pack carries 6 generic schema rules", count_list(pack.rule_chain) == 6,
      str(count_list(pack.rule_chain)) + " rules")

# Genericity pin: no leaf constant. Every leaf of every premise and
# replacement is a pattern variable or a known label -- a Char naming a
# point, a triangle or a problem would be neither, and would be exactly the
# hardcoding the W8 brief forbids.
rule_ok = True
rcursor = pack.rule_chain
while M.IdentityCompare(rcursor, EMPTY)() is M.false_value:
    rule = M.Head(rcursor)()
    pcursor = P.RulePremises(rule)()
    while M.IdentityCompare(pcursor, EMPTY)() is M.false_value:
        if not all_machine(M.Head(pcursor)(), registry, namespace_atoms):
            rule_ok = False
        pcursor = M.Tail(pcursor)()
    rcursor2 = P.RuleReplacement(rule)()
    while M.IdentityCompare(rcursor2, EMPTY)() is M.false_value:
        if not all_machine(M.Head(rcursor2)(), registry, namespace_atoms):
            rule_ok = False
        rcursor2 = M.Tail(rcursor2)()
    rcursor = M.Tail(rcursor)()
check("no rule in the pack contains a hardcoded constant", rule_ok)

print()

# ---------------------------------------------------------------------------
# [2] the generator: goal-directed proposals over symbolic figures
# ---------------------------------------------------------------------------

print("[2] Construction proposals  (section 1 took %.1fs)" % (time.time() - T0))

P_PT = named(M.Char("P"), "P")
Q_PT = named(M.Char("Q"), "Q")
R_PT = named(M.Char("R"), "R")
T_TRI = named(M.Char("Tri"), "Tri")
LEN_EQ = named(M.Char("s"), "s")
LEN_OTHER = named(M.Char("t"), "t")

circle_var = named(M.Pair(M.VarTag, M.Pair(M.Char("k"), EMPTY)), "?k")


def isosceles_figure():
    return chain([
        fact(L.TriangleLabel, P_PT, Q_PT, R_PT),
        fact(L.VertexOfLabel, T_TRI, P_PT),
        fact(L.VertexOfLabel, T_TRI, Q_PT),
        fact(L.VertexOfLabel, T_TRI, R_PT),
        fact(L.TriangleLabel, T_TRI),
        fact(L.LengthLabel, fact(L.SegmentLabel, P_PT, Q_PT), LEN_EQ),
        fact(L.LengthLabel, fact(L.SegmentLabel, P_PT, R_PT), LEN_EQ),
    ])


def scalene_figure():
    return chain([
        fact(L.TriangleLabel, P_PT, Q_PT, R_PT),
        fact(L.VertexOfLabel, T_TRI, P_PT),
        fact(L.VertexOfLabel, T_TRI, Q_PT),
        fact(L.VertexOfLabel, T_TRI, R_PT),
        fact(L.TriangleLabel, T_TRI),
        fact(L.LengthLabel, fact(L.SegmentLabel, P_PT, Q_PT), LEN_EQ),
        fact(L.LengthLabel, fact(L.SegmentLabel, P_PT, R_PT), LEN_OTHER),
    ])


base_angle_goal = fact(L.EqualAngleLabel,
                       fact(L.AngleLabel, P_PT, Q_PT, R_PT),
                       fact(L.AngleLabel, P_PT, R_PT, Q_PT))

proposals = C.ConstructionProposals(C.DefaultSchemas(), base_angle_goal, isosceles_figure())()
check("the isosceles base-angle goal draws exactly one proposal",
      count_list(proposals) == 1, str(count_list(proposals)) + " proposals")

proposal = M.Head(proposals)()
schema = C.ProposalSchema(proposal)
effects = C.ProposalEffects(proposal)
check("  ... from the bisector-completion schema",
      M.Compare(C.SchemaName(schema), M.Char("bisector-completion"))() is M.truth_value,
      show(C.SchemaName(schema)))
check("  ... with five effect facts", count_list(effects) == 5, str(count_list(effects)))

vars_left = 0
ecursor = effects
while M.IdentityCompare(ecursor, EMPTY)() is M.false_value:
    vars_left += pattern_var_count(M.Head(ecursor)())
    ecursor = M.Tail(ecursor)()
check("  ... fully instantiated (no pattern variable survives)", vars_left == 0)

aux = M.Head(M.Tail(M.Head(effects)())())()


def contains(term, atom):
    if M.IsPair(term)() is M.false_value:
        return M.IdentityCompare(term, atom)() is M.truth_value
    return contains(M.Head(term)(), atom) or contains(M.Tail(term)(), atom)


aux_uses = 0
ecursor = effects
while M.IdentityCompare(ecursor, EMPTY)() is M.false_value:
    if contains(M.Head(ecursor)(), aux):
        aux_uses += 1
    ecursor = M.Tail(ecursor)()
check("  ... one minted auxiliary object, present in every fact that needs it",
      aux_uses == 5, str(aux_uses) + " facts carry it")

# goal-directedness: a goal of a different shape draws the other schema, and
# a goal no schema bears on draws nothing.
on_circle_goal = fact(L.OnCircleLabel, Q_PT, circle_var)
proposals_c = C.ConstructionProposals(C.DefaultSchemas(), on_circle_goal, isosceles_figure())()
check("an OnCircle goal draws exactly the circumcircle proposal",
      count_list(proposals_c) == 1
      and M.Compare(C.SchemaName(C.ProposalSchema(M.Head(proposals_c)())),
                    M.Char("circumcircle-completion"))() is M.truth_value,
      str(count_list(proposals_c)) + " proposals")

length_goal = fact(L.LengthLabel, fact(L.SegmentLabel, P_PT, Q_PT), LEN_EQ)
proposals_l = C.ConstructionProposals(C.DefaultSchemas(), length_goal, isosceles_figure())()
check("a goal no schema bears on draws nothing", count_list(proposals_l) == 0)

proposals_s = C.ConstructionProposals(C.DefaultSchemas(), base_angle_goal, scalene_figure())()
check("on a scalene figure the bisector schema is not sound, so it proposes nothing",
      count_list(proposals_s) == 0, str(count_list(proposals_s)) + " proposals")

print()

# ---------------------------------------------------------------------------
# [3] the end-to-end derivation: the auxiliary point is minted, not named
# ---------------------------------------------------------------------------

print("[3] End-to-end: isosceles base angles via the minted bisector")

D_AUX = aux
segment_goal_ray = fact(L.EqualAngleLabel,
                        fact(L.AngleLabel, P_PT, Q_PT, D_AUX),
                        fact(L.AngleLabel, P_PT, Q_PT, R_PT))
sas_step = fact(L.EqualAngleLabel,
                fact(L.AngleLabel, P_PT, Q_PT, D_AUX),
                fact(L.AngleLabel, P_PT, R_PT, D_AUX))
bisector_step = fact(L.EqualAngleLabel,
                     fact(L.AngleLabel, Q_PT, P_PT, D_AUX),
                     fact(L.AngleLabel, D_AUX, P_PT, R_PT))

full = closure(append(isosceles_figure(), effects), rules, registry)
got = P.KnowledgeFacts(full)()
check("figure + construction closes the goal", has_fact(got, base_angle_goal), show(full))
check("  ... through the bisector definition", has_fact(got, bisector_step))
check("  ... through the SAS self-congruence", has_fact(got, sas_step))
check("  ... through the ray identity on the constructed foot", has_fact(got, segment_goal_ray))

bare = closure(isosceles_figure(), rules, registry)
got_bare = P.KnowledgeFacts(bare)()
check("without the construction the goal does not close", not has_fact(got_bare, base_angle_goal))
check("  ... and no half-angle step exists either", not has_fact(got_bare, bisector_step))

scalene = closure(append(scalene_figure(), C.ProposalEffects(M.Head(proposals_s)()) if
                         M.IdentityCompare(proposals_s, EMPTY)() is M.false_value else EMPTY),
                  rules, registry)
got_scalene = P.KnowledgeFacts(scalene)()
check("and on a scalene figure nothing closes, because nothing is proposed",
      not has_fact(got_scalene, base_angle_goal))

circ = closure(append(isosceles_figure(),
                      C.ProposalEffects(M.Head(proposals_c)())), rules, registry)
check("figure + circumcircle closes the existential OnCircle goal",
      goal_hit(on_circle_goal, P.KnowledgeFacts(circ)()))
check("  ... without it, no vertex lies on any circle",
      not goal_hit(on_circle_goal, P.KnowledgeFacts(bare)()))

print()

# ---------------------------------------------------------------------------
# [4] the planner carries proposals, obligations and the conclusion
# ---------------------------------------------------------------------------

print("[4] Planner integration")

bisector_method = Planner.Construction(base_angle_goal, effects)()
method_obligations = Planner.ConstructionObligations(bisector_method)()
method_conclusion = Planner.ConstructionConclusion(bisector_method)()

check("the Construction method obligationes every effect",
      count_list(method_obligations) == count_list(effects)
      and goal_hit(fact(L.PointOnLabel, aux, circle_var), method_obligations),
      str(count_list(method_obligations)) + " obligations")
check("  ... and concludes exactly the goal it was proposed for",
      M.Compare(method_conclusion, base_angle_goal)() is M.truth_value)

both_methods = chain([
    Planner.Construction(base_angle_goal, effects)(),
    Planner.Construction(on_circle_goal, C.ProposalEffects(M.Head(proposals_c)()))(),
])
problem_term = Planner.PlannerProblem(
    P.Knowledge(isosceles_figure())(),
    base_angle_goal,
    rules,
    runtime.theorem_heuristic,
    both_methods,
)()
state = Planner.PlannerState(problem_term, registry)()
ran = Planner.PlannerRun(graph, state, M.three)()

alternatives = Planner.PlannerStateAlternatives(ran)()
found = EMPTY
cursor = alternatives
while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
    alternative = M.Head(cursor)()
    if M.TermEqual(Planner.PlannerAlternativeMethod(alternative)(), bisector_method)() is M.truth_value:
        found = alternative
        cursor = EMPTY
    else:
        cursor = M.Tail(cursor)()

check("the construction proposal became a planner alternative",
      M.IdentityCompare(found, EMPTY)() is M.false_value)
check("  ... with one child per obligation",
      count_list(Planner.PlannerAlternativeChildren(found)()) == count_list(effects),
      str(count_list(Planner.PlannerAlternativeChildren(found)())) + " children")

state_obligations = M.Head(M.Tail(ran)())()
matched = 0
children = Planner.PlannerAlternativeChildren(found)()
ccursor = children
while M.IdentityCompare(ccursor, EMPTY)() is M.false_value:
    child_id = M.Head(ccursor)()
    ocursor = state_obligations
    while M.IdentityCompare(ocursor, EMPTY)() is M.false_value:
        obligation = M.Head(ocursor)()
        if M.Compare(M.Head(M.Tail(obligation)())(), child_id)() is M.truth_value:
            goal_term = M.Head(M.Tail(M.Tail(M.Tail(obligation)())())())()
            if has_fact(effects, goal_term):
                matched = matched + 1
            ocursor = EMPTY
        else:
            ocursor = M.Tail(ocursor)()
    ccursor = M.Tail(ccursor)()
check("  ... each child goal is one of the construction's effects",
      matched == count_list(effects), str(matched) + " of " + str(count_list(effects)))

plain_problem = Planner.PlannerProblem(
    P.Knowledge(isosceles_figure())(),
    base_angle_goal,
    rules,
    runtime.theorem_heuristic,
)()
plain_state = Planner.PlannerState(plain_problem, registry)()
plain_ran = Planner.PlannerRun(graph, plain_state, M.three)()
check("with no generator there is no construction alternative",
      M.IdentityCompare(Planner.PlannerStateAlternatives(plain_ran)(), EMPTY)() is M.truth_value,
      str(count_list(Planner.PlannerStateAlternatives(plain_ran)())) + " alternatives")

print()

# ---------------------------------------------------------------------------
# [5] negative control summary: the generator is doing the work
# ---------------------------------------------------------------------------

print("[5] Negative controls")

check("generator off  -> goal unreachable (figure alone, closure)", not has_fact(got_bare, base_angle_goal))
check("generator off  -> no construction alternative in the planner",
      M.IdentityCompare(Planner.PlannerStateAlternatives(plain_ran)(), EMPTY)() is M.truth_value)
check("figure unsound -> no proposal, hence nothing to close",
      count_list(proposals_s) == 0 and not has_fact(got_scalene, base_angle_goal))
check("goal elsewhere -> no schema fires (a length goal draws nothing)",
      count_list(proposals_l) == 0)

print()

# ---------------------------------------------------------------------------
# [6] the new labels survive a snapshot round-trip
# ---------------------------------------------------------------------------

print("[6] Snapshot symbol round-trip")

NEW_LABEL_NAMES = (
    "EqualAngleLabel",
    "BisectorFromLabel",
    "PointOnLabel",
    "CircumcircleOfLabel",
    "OnCircleLabel",
    "ConstructionSchemaLabel",
    "ConstructionMethodLabel",
)

snapshot_path = os.path.join(tempfile.mkdtemp(prefix="test21-"), "snapshot.json")
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
# [7] representation: schemas are as generic as the pack
# ---------------------------------------------------------------------------

print("[7] Representation checks")

schemas = C.DefaultSchemas()
schema_ok = True
scursor = schemas
while M.IdentityCompare(scursor, EMPTY)() is M.false_value:
    schema = M.Head(scursor)()
    scursor = M.Tail(scursor)()
    for part in (C.SchemaGoalShape(schema), C.SchemaPremises(schema), C.SchemaEffects(schema)):
        if not all_machine(part, registry, namespace_atoms):
            schema_ok = False
check("every schema (goal shape, premises, effects) names no constant", schema_ok)

check("the minted auxiliary object is anonymous (an atom, not a named Char)",
      M.IsAtom(D_AUX, registry)() is M.truth_value
      and M.IdentityCompare(D_AUX, EMPTY)() is M.false_value,
      show(D_AUX))

check("the derived knowledge is a Knowledge term", P.IsKnowledge(full)() is M.truth_value)

# The pack vocabulary pin does not apply to derived knowledge: the figure's
# own named points are supposed to be there. What must hold is that every
# fact is a machine pair and ground -- a derivation may never leak a
# pattern variable into Knowledge.
fact_cursor = got
facts_ok = True
while M.IdentityCompare(fact_cursor, EMPTY)() is M.false_value:
    one = M.Head(fact_cursor)()
    if M.IsPair(one)() is M.false_value and M.IsAtom(one, registry)() is M.false_value:
        facts_ok = False
    if pattern_var_count(one) > 0:
        facts_ok = False
    fact_cursor = M.Tail(fact_cursor)()
check("  ... whose every fact is machine-side and variable-free", facts_ok)

print()
print("=== TEST 21 RESULTS ===")
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
    print("=== TEST 21 FAILED ===")
    sys.exit(1)
print("=== TEST 21 COMPLETE ===")
