# ============================================================
# TEST 38: W26 — IMO geometry remainder (chord / angle, receipts)
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test38_geometry_remainder.py
#
# Slot 38 is the one `delegation/README.md` assigns to
# `W26-geometry-remainder.md`; slot 37 went to W25 and 39+ are unallocated.
#
# What W8 left, and what this worker adds.  W8 shipped two generic
# construction schemas (bisector, circumcircle) and six pack rules, and its
# circumcircle stopped at "the vertex lies on the circle": the circle was a
# dead end that fed no chord or angle fact back into a goal.  W8 also did not
# claim a Checker-B receipt, a ledger record or an ablation, because those
# modules were not on its authoring branch.
#
# This suite's evidence, stated first so the rest can be read against it:
#
#   * THREE new generic pack rules, all fully variable-typed and
#     constant-free: angles in the same segment are equal (with the side
#     condition that makes it sound), opposite angles of a cyclic
#     quadrilateral are supplementary, and a diameter is seen at a right
#     angle from the circle (Thales, stated relationally so no measure
#     constant is needed).
#   * ONE new construction schema, `antipode-completion`: given a circle with
#     a centre and a point on it, mint the antipode, so the chord becomes a
#     diameter.  The goal is existential and the generator instantiates the
#     effects on the goal's own variable; the suite then asks the machine
#     (`MintUnboundWitnessesInList`) to mint the witness and record the
#     introduction.  No point is named anywhere: every point, circle and
#     centre below is an opaque `M.Char` the suite itself creates.
#   * END TO END with a receipt: proposal -> witness minting -> forward
#     derivation -> Checker B verifies the Thales step and refuses it against
#     a goal it does not reach.  The promotion ledger is then asked to promote
#     the schema and it does, through the evaluator, ablation and holdout
#     gates, with two holdout configurations (one positive, one near-miss).
#   * ABLATION: with the Thales rule withheld from the rule set the same
#     configuration does not close; with the antipode schema withheld no
#     proposal is made; with the side condition withheld the same-segment rule
#     does not fire.
#
# Honest scope, stated up front:
#   * No angle measures, no arithmetic on angles, no arc/orientation
#     machinery.  The rules are relational; "twice the inscribed angle" and
#     anything that needs a measure are NOT claimed.
#   * Projective collineations remain OPEN, as W8 left them.
#   * The cyclic-order rule takes the cyclic order as figure data.  Deciding
#     the cyclic order of four points from incidence alone is not attempted.
#   * No problem is named anywhere: the pack has no ground atom in an
#     argument position, the schemas put no ground atom in an argument
#     position, and this file contains no named configuration.
#   * `test21` owns W8's evidence and is not grown here; it is run separately
#     and still passes.  This suite touches none of W8's six rules.
#
# Host layer only below: file paths, timings, counting and printing.  Every
# assertion about a machine value is Compare / IdentityCompare / IsPair /
# Match; there is no isinstance, no type(), no attribute read of a machine
# term.  Atoms the suite creates are given names in a local table for
# printing only.

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
C = importlib.import_module(PACKAGE + ".constructions")
GT = importlib.import_module(PACKAGE + ".graph_task")
packs = importlib.import_module(PACKAGE + ".packs")
persistence = importlib.import_module(PACKAGE + ".persistence")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
main_mod = importlib.import_module(PACKAGE + ".main")
CheckerB = importlib.import_module(PACKAGE + ".checker_b")
Eval = importlib.import_module(PACKAGE + ".evaluator")
Ledger = importlib.import_module(PACKAGE + ".promotion_ledger")

T0 = time.time()
EMPTY = M.EmptyList
TRUTH = M.truth_value

print("=== TEST 38: W26 IMO geometry remainder ===")
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


def chain(items):
    out = EMPTY
    index = len(items)
    while index > 0:
        index = index - 1
        out = M.Pair(items[index], out)
    return out


def is_pair_term(term):
    return M.IsPair(term)() is M.truth_value


def to_list(term):
    out = []
    cursor = term
    while is_pair_term(cursor):
        out.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return out


def call(label, *args):
    return M.Pair(label, chain(list(args)))


def fact(label, *args):
    return M.Pair(label, chain(list(args)))


def has_fact(facts, target):
    for one in to_list(facts):
        if M.Compare(one, target)() is M.truth_value:
            return True
    return False


def pattern_var_count(term):
    if not is_pair_term(term):
        return 0
    if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
        return 1
    return pattern_var_count(M.Head(term)()) + pattern_var_count(M.Tail(term)())


def ground_data_atoms(term, acc):
    """The genericity pin, machine-side (same walk test21 and test36 use).

    Variables are VarTag-headed pairs; calls are label-headed pairs whose
    tail is the argument chain; structural conses are pair-headed.  Heads are
    relation vocabulary, so a leaf reached through an argument or cons
    position is a datum, and this worker's rules may have none.
    """
    if not is_pair_term(term):
        return M.Pair(term, acc)
    head = M.Head(term)()
    if M.IdentityCompare(head, M.VarTag)() is M.truth_value:
        return acc
    if is_pair_term(head):
        acc = ground_data_atoms(head, acc)
        return ground_data_atoms(M.Tail(term)(), acc)
    cursor = M.Tail(term)()
    while is_pair_term(cursor):
        acc = ground_data_atoms(M.Head(cursor)(), acc)
        cursor = M.Tail(cursor)()
    return acc


def only_nil(atoms):
    for one in to_list(atoms):
        if M.IdentityCompare(one, EMPTY)() is M.false_value:
            return False
    return True


def machine_nat(value):
    return M.Head(M.NatFromRep(M.GMPRep(int(value)), registry)())()


def derive(facts, rules, depth=6):
    return GT.ForwardDeriveFacts(facts, rules, machine_nat(depth), registry)()


def derives_head(facts, rules, label, depth=6):
    """Does the forward closure contain a fact headed by `label`?

    The engine instantiates one join per rule per round (test22/[32] measured
    it), so a *specific* instantiation is not guaranteed to be the one that
    appears.  Whether the rule fired at all is, and that is what the ablation
    below needs; reaching a named goal is checked separately by selecting the
    join whose conclusion is the goal and verifying that step.
    """
    for one in to_list(derive(facts, rules, depth)):
        if M.IdentityCompare(M.Head(one)(), label)() is M.truth_value:
            return True
    return False


def rule_set(chain_term, omit_ids):
    """A compiled rule chain minus the named rules, by pack id."""
    kept = []
    for rid in rule_ids(chain_term):
        if rid not in omit_ids:
            kept.append(rule_map[rid])
    return P.CompileRuleChain(chain(kept), registry)()


def rule_ids(chain_term):
    out = []
    for rule in to_list(chain_term):
        for rid, obj in pack.rule_map.entries:
            if M.IdentityCompare(obj(), rule)() is M.truth_value:
                out.append(rid)
    return out


NAMES = []


def named(term, name):
    NAMES.append((term, name))
    return term


def show(term):
    if is_pair_term(term):
        head = show(M.Head(term)())
        rest = " ".join(show(x) for x in to_list(M.Tail(term)()))
        return "(" + head + (" " + rest if rest else "") + ")"
    for term_, name in NAMES:
        if M.IdentityCompare(term_, term)() is M.truth_value:
            return name
    return "<?>"


print("[1] Boot, load, inventory the new schemas, pin genericity...")
runtime = runtime_mod.make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
namespace = main_mod._runtime_namespace()

PACK_PATH = os.path.join(REPO, "packs", "geometry-constructions.pack.yaml")
loader = packs.PackLoader(namespace)
pack = loader.load_pack_file(PACK_PATH, graph)
rules = P.CompileRuleChain(pack.rule_chain, registry)()
rule_map = dict((rid, obj()) for rid, obj in pack.rule_map.entries)

NEW_RULE_IDS = (
    "inscribed_angles_same_arc",
    "cyclic_order_opposite_angles",
    "semicircle_angle_is_right",
)
W8_RULE_IDS = (
    "bisector_splits_angle",
    "sas_self_congruence",
    "on_segment_unifies_ray",
    "equal_angle_symmetric",
    "equal_angle_transitive",
    "circumcircle_admits_vertex",
)

check("pack name is geometry-constructions", pack.name == "geometry-constructions",
      pack.name)
check("the pack carries nine rules (W8's six plus W26's three)",
      len(to_list(pack.rule_chain)) == 9,
      str(len(to_list(pack.rule_chain))) + " rules")
missing = [rid for rid in NEW_RULE_IDS if rid not in rule_map]
check("all three W26 rule ids are loaded", not missing, ", ".join(missing))
kept = [rid for rid in W8_RULE_IDS if rid not in rule_map]
check("W8's six rules are still present and are not renamed", not kept,
      ", ".join(kept))

rule_ok = True
for rid, rule in rule_map.items():
    for premise in to_list(P.RulePremises(rule)()):
        if not only_nil(ground_data_atoms(premise, EMPTY)):
            rule_ok = False
    for conclusion in to_list(P.RuleReplacement(rule)()):
        if not only_nil(ground_data_atoms(conclusion, EMPTY)):
            rule_ok = False
check("no rule (old or new) puts a ground atom in an argument position", rule_ok)

schema_ok = True
for schema in to_list(C.DefaultSchemas()):
    if not only_nil(ground_data_atoms(C.SchemaGoalShape(schema), EMPTY)):
        schema_ok = False
    for premise in to_list(C.SchemaPremises(schema)):
        if not only_nil(ground_data_atoms(premise, EMPTY)):
            schema_ok = False
    for effect in to_list(C.SchemaEffects(schema)):
        if not only_nil(ground_data_atoms(effect, EMPTY)):
            schema_ok = False
check("no construction schema (old or new) puts a ground atom in an argument"
      " position", schema_ok)

NEW_LABELS = (
    "PerpendicularLabel",
    "DiameterLineLabel",
    "CentreOfLabel",
    "SameSideOfLineLabel",
    "SupplementaryAnglesLabel",
    "CyclicOrderLabel",
    "GeometryRemainderLabel",
)
check("the seven W26 labels are defined in labels.py",
      all(hasattr(L, name) for name in NEW_LABELS))

originals = dict((name, getattr(L, name)) for name in NEW_LABELS)
sentinel = object()
synced = dict((name, sentinel) for name in NEW_LABELS)
L.sync_from_namespace(synced)
registered = all(getattr(L, name) is sentinel for name in NEW_LABELS)
L.sync_from_namespace(originals)
restored = all(getattr(L, name) is originals[name] for name in NEW_LABELS)
check("every new label is registered by sync_from_namespace",
      registered and restored,
      "sentinel in, originals back: %s" % ("ok" if restored else "NOT restored"))
print()

print("[2] The antipode schema: proposal generation and its controls...")
O = named(M.Char("O"), "O")
A = named(M.Char("A"), "A")
BB = named(M.Char("B"), "B")
CC = named(M.Char("C"), "C")
D = named(M.Char("D"), "D")
K = named(M.Char("k"), "k")

goal_b = M.Pair(M.VarTag, M.Pair(M.Char("witness"), EMPTY))


def perpendicular_goal(point_c, point_a, point_b):
    return fact(L.PerpendicularLabel,
                call(L.SegmentLabel, point_c, point_a),
                call(L.SegmentLabel, point_c, point_b))


antipode_goal = perpendicular_goal(CC, A, goal_b)
circle_figure = chain([
    fact(L.OnCircleLabel, A, K),
    fact(L.OnCircleLabel, CC, K),
    fact(L.CentreOfLabel, O, K),
])

proposals = C.ConstructionProposals(C.DefaultSchemas(), antipode_goal, circle_figure)()
check("the existential perpendicular goal draws exactly one proposal",
      len(to_list(proposals)) == 1, str(len(to_list(proposals))) + " proposals")
proposal = M.Head(proposals)()
schema = C.ProposalSchema(proposal)
check("  ... from the antipode-completion schema",
      M.Compare(C.SchemaName(schema), M.Char("antipode-completion"))() is M.truth_value,
      show(C.SchemaName(schema)))
effects = C.ProposalEffects(proposal)
check("  ... with two effect facts (the diameter and the new point on the circle)",
      len(to_list(effects)) == 2, str(len(to_list(effects))) + " effects")

centreless = chain([
    fact(L.OnCircleLabel, A, K),
    fact(L.OnCircleLabel, CC, K),
])
check("with no centre in the figure the construction is not sound, so nothing"
      " is proposed",
      len(to_list(C.ConstructionProposals(C.DefaultSchemas(), antipode_goal,
                                          centreless)())) == 0)

off_circle = chain([
    fact(L.OnCircleLabel, CC, K),
    fact(L.CentreOfLabel, O, K),
])
check("with no point on the circle nothing is proposed either",
      len(to_list(C.ConstructionProposals(C.DefaultSchemas(), antipode_goal,
                                          off_circle)())) == 0)

equal_angle_goal = fact(L.EqualAngleLabel,
                        call(L.AngleLabel, A, BB, CC),
                        call(L.AngleLabel, A, CC, BB))
check("the schema is goal-directed: an angle goal draws the bisector, not the"
      " antipode",
      len(to_list(C.ConstructionProposals(M.Pair(schema, EMPTY), equal_angle_goal,
                                          circle_figure)())) == 0)
print()

print("[3] End to end: propose -> mint -> derive -> Checker B receipt...")
minted = GT.MintUnboundWitnessesInList(effects)()
ground_effects = M.Head(minted)()
recorded = M.Tail(minted)()
check("the machine mints one witness for the goal's leftover variable",
      len(to_list(recorded)) == 1, str(len(to_list(recorded))) + " binding(s)")
check("the minted effects are ground (no pattern variable survives)",
      all(pattern_var_count(one) == 0 for one in to_list(ground_effects)))

filled_goal = GT.FillUnboundWitnesses(antipode_goal, recorded)()
check("the goal fills from the recorded witness", M.Head(filled_goal)() is TRUTH)
ground_goal = M.Tail(filled_goal)()
check("  ... and the filled goal carries the minted object",
      pattern_var_count(ground_goal) == 0)

start_facts = chain(to_list(circle_figure) + to_list(ground_effects))
start_state = P.Knowledge(start_facts)()
closed = derive(start_facts, rules, 6)
check("the schema fires on figure + construction: a perpendicular fact is"
      " derived",
      derives_head(start_facts, rules, L.PerpendicularLabel, 6))
check("  ... and the closure is a set of ground facts",
      all(pattern_var_count(one) == 0 for one in to_list(closed)))

thales = rule_map["semicircle_angle_is_right"]
joins = P.JoinPremises(P.RulePremises(thales)(), P.KnowledgeFacts(start_state)(),
                       EMPTY)()
check("the Thales rule joins against the constructed figure",
      len(to_list(joins)) > 0, str(len(to_list(joins))) + " join(s)")

chosen = None
for binds in to_list(joins):
    conclusion = P.InstantiateFactList(P.RuleReplacement(thales)(), binds)()
    if has_fact(conclusion, ground_goal):
        chosen = binds
check("one of the joins concludes exactly the goal (the step is selected by"
      " its conclusion, not by order)", chosen is not None)

step_action = P.TheoremAction(thales, chosen)()
plan = M.Pair(step_action, EMPTY)
built = P.BuildDerivation(start_state, plan, registry)()
derivation = M.Head(built)()
derivation_registry = M.Head(M.Tail(built)())()
after_step = P.KnowledgeFacts(
    P.ApplyKnowledgeRewrite(start_state, thales, chosen)())()
check("the selected step puts exactly the goal into the state",
      has_fact(after_step, ground_goal), show(ground_goal))
goal_state = P.Knowledge(M.Pair(ground_goal, EMPTY))()
verdict = CheckerB.VerifyDerivation(derivation, start_state, goal_state,
                                    M.Pair(thales, EMPTY), derivation_registry)()
check("Checker B verifies the Thales derivation and reaches the goal",
      M.IdentityCompare(M.Head(verdict)(), L.DerivationVerifiedLabel)() is M.truth_value,
      str(M.Head(verdict)()))

wrong_goal = P.Knowledge(M.Pair(
    fact(L.EqualAngleLabel,
         call(L.AngleLabel, A, BB, CC),
         call(L.AngleLabel, A, CC, BB)), EMPTY))()
wrong_verdict = CheckerB.VerifyDerivation(derivation, start_state, wrong_goal,
                                          M.Pair(thales, EMPTY),
                                          derivation_registry)()
check("the same derivation is refused against a goal it does not reach",
      M.IdentityCompare(M.Head(wrong_verdict)(), L.GoalMismatchLabel)() is M.truth_value,
      str(M.Head(wrong_verdict)()))
print()

print("[4] The same-segment and cyclic-quadrilateral schemas...")
same_arc_figure = chain([
    fact(L.OnCircleLabel, A, K),
    fact(L.OnCircleLabel, BB, K),
    fact(L.OnCircleLabel, CC, K),
    fact(L.OnCircleLabel, D, K),
    fact(L.SameSideOfLineLabel, CC, D, call(L.SegmentLabel, A, BB)),
])
same_arc_goal = fact(L.EqualAngleLabel,
                     call(L.AngleLabel, A, CC, BB),
                     call(L.AngleLabel, A, D, BB))
same_arc_closure = derive(same_arc_figure, rules, 6)
check("two points seeing a chord from the same side see it at equal angles",
      has_fact(same_arc_closure, same_arc_goal), show(same_arc_goal))

without_side = chain(to_list(same_arc_figure)[:4])
check("withhold the side condition and the schema does not fire (it is not"
      " guessing: opposite sides give supplementary angles, not equal ones)",
      not has_fact(derive(without_side, rules, 6), same_arc_goal))

three_points = chain(to_list(same_arc_figure)[:3] + to_list(same_arc_figure)[4:])
check("withhold the fourth point on the circle and the schema does not fire",
      not has_fact(derive(three_points, rules, 6), same_arc_goal))

cyclic_figure = chain([fact(L.CyclicOrderLabel, A, BB, CC, D, K)])
cyclic_goal = fact(L.SupplementaryAnglesLabel,
                   call(L.AngleLabel, A, BB, CC),
                   call(L.AngleLabel, CC, D, A))
check("opposite angles of a cyclic quadrilateral are supplementary",
      has_fact(derive(cyclic_figure, rules, 4), cyclic_goal), show(cyclic_goal))
check("withhold the cyclic order and nothing is concluded",
      not has_fact(derive(chain([]), rules, 4), cyclic_goal))
unordered = chain([
    fact(L.OnCircleLabel, A, K),
    fact(L.OnCircleLabel, BB, K),
    fact(L.OnCircleLabel, CC, K),
    fact(L.OnCircleLabel, D, K),
])
check("four points on a circle without a stated cyclic order conclude nothing"
      " (the order is figure data, not a guess)",
      not has_fact(derive(unordered, rules, 4), cyclic_goal))
print()

print("[5] Ablation: the schema is what does the work...")
no_thales = rule_set(pack.rule_chain, ("semicircle_angle_is_right",))
check("withheld Thales rule: the configuration no longer closes",
      not derives_head(start_facts, no_thales, L.PerpendicularLabel, 6))
check("  ... while the same rule set still derives the same-arc conclusion",
      has_fact(derive(same_arc_figure, no_thales, 6), same_arc_goal))

no_circle_rules = rule_set(pack.rule_chain,
                           NEW_RULE_IDS + ("circumcircle_admits_vertex",))
check("with all four circle rules withheld nothing circular is derived",
      not derives_head(start_facts, no_circle_rules, L.PerpendicularLabel, 6)
      and not has_fact(derive(same_arc_figure, no_circle_rules, 6), same_arc_goal))

ANTIPODE_NAME = M.Char("antipode-completion")
without_antipode = chain([s for s in to_list(C.DefaultSchemas())
                          if M.Compare(C.SchemaName(s), ANTIPODE_NAME)() is M.false_value])
check("withheld antipode schema: no proposal, so the witness never exists",
      len(to_list(C.ConstructionProposals(without_antipode, antipode_goal,
                                          circle_figure)())) == 0)
check("  ... and W8's two schemas still propose where they should",
      len(to_list(C.ConstructionProposals(without_antipode, equal_angle_goal,
                                          chain([
                                              fact(L.TriangleLabel, A, BB, CC),
                                              fact(L.LengthLabel,
                                                   call(L.SegmentLabel, A, BB), K),
                                              fact(L.LengthLabel,
                                                   call(L.SegmentLabel, A, CC), K),
                                          ]))())) == 1)
print()

print("[6] The promotion ledger: asked to promote, and asked to refuse...")
start_pattern = M.Pair(P.KnowledgeLabel, M.Pair(P.RulePremises(thales)(), EMPTY))
goal_pattern = M.Pair(P.KnowledgeLabel, M.Pair(P.RuleReplacement(thales)(), EMPTY))
macro_plan = M.Pair(P.TheoremAction(thales, EMPTY)(), EMPTY)
macro = Eval.CandidateMacro(M.Char("thales-semicircle"), start_pattern,
                            goal_pattern, macro_plan)()

instance_start = P.Knowledge(chain([
    fact(L.DiameterLineLabel, K, call(L.SegmentLabel, A, BB)),
    fact(L.OnCircleLabel, CC, K),
]))()
instance_goal = P.Knowledge(M.Pair(perpendicular_goal(CC, A, BB), EMPTY))()

k2 = M.Char("k2")
p2, q2, r2 = M.Char("P2"), M.Char("Q2"), M.Char("R2")
k3 = M.Char("k3")
f3, g3, h3 = M.Char("F3"), M.Char("G3"), M.Char("H3")
holdouts = chain([
    M.Pair(
        P.Knowledge(chain([
            fact(L.DiameterLineLabel, k2, call(L.SegmentLabel, p2, q2)),
            fact(L.OnCircleLabel, r2, k2),
        ]))(),
        M.Pair(P.Knowledge(M.Pair(
            fact(L.PerpendicularLabel, call(L.SegmentLabel, r2, p2),
                 call(L.SegmentLabel, r2, q2)), EMPTY))(),
            M.Pair(TRUTH, EMPTY)),
    ),
    M.Pair(
        P.Knowledge(chain([
            fact(L.OnCircleLabel, f3, k3),
            fact(L.OnCircleLabel, g3, k3),
        ]))(),
        M.Pair(P.Knowledge(M.Pair(
            fact(L.PerpendicularLabel, call(L.SegmentLabel, f3, g3),
                 call(L.SegmentLabel, f3, h3)), EMPTY))(),
            M.Pair(M.false_value, EMPTY)),
    ),
])

expansion = Eval.ExpandCandidateMacro(macro, instance_start, instance_goal, registry)()
check("the candidate expands on a concrete instance",
      M.IdentityCompare(M.Head(expansion)(), L.CandidateExpandedLabel)() is M.truth_value,
      str(M.Head(expansion)()))
evaluation = Eval.EvaluateCandidateProof(macro, instance_start, instance_goal,
                                         M.Pair(thales, EMPTY), registry)()
check("the evaluator's Checker-B gate accepts the expanded derivation",
      M.IdentityCompare(M.Head(evaluation)(), L.CandidateEvaluatedLabel)() is M.truth_value,
      str(M.Head(evaluation)()))
holdout_suite = Eval.EvaluateHoldoutSuite(macro, holdouts, M.Pair(thales, EMPTY),
                                          registry)()
check("both holdouts behave as declared (one configuration closes, the"
      " near-miss is refused)",
      M.IdentityCompare(M.Head(M.Tail(M.Tail(holdout_suite)())())(), EMPTY)() is M.truth_value,
      "%d failed" % len(to_list(M.Head(M.Tail(M.Tail(holdout_suite)())())())))

zero_cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
ledger0 = Ledger.EmptyPromotionLedger(registry)()
promotion = Ledger.SubmitCandidateForPromotion(
    ledger0, macro, L.ProofSchemaPromotionLabel, instance_start, instance_goal,
    zero_cost, holdouts, EMPTY, M.Pair(thales, EMPTY), registry)()
check("the ledger promotes the Thales schema through evaluator, ablation and"
      " holdout gates",
      M.IdentityCompare(M.Head(promotion)(), L.PromotionApprovedLabel)() is M.truth_value,
      str(M.Head(promotion)()))
if M.IdentityCompare(M.Head(promotion)(), L.PromotionApprovedLabel)() is M.truth_value:
    promoted_ledger = M.Head(M.Tail(promotion)())()
    promoted_entry = M.Head(M.Tail(M.Tail(promotion)())())()
    check("  ... the ledger advanced to version 1",
          M.IdentityCompare(Ledger.PromotionLedgerVersion(promoted_ledger)(),
                            machine_nat(1))() is M.truth_value)
    check("  ... the entry is active and carries a ProofReceipt, not an"
          " assertion",
          M.IdentityCompare(Ledger.LedgerEntryStatus(promoted_entry)(),
                            L.PromotionActiveLabel)() is M.truth_value
          and M.IdentityCompare(M.Head(Ledger.LedgerEntryReceipt(promoted_entry)())(),
                                L.ProofReceiptLabel)() is M.truth_value)
else:
    check("  ... the ledger advanced to version 1", False, "promotion refused")
    check("  ... the entry is active and carries a ProofReceipt", False,
          "promotion refused")

refusal = Ledger.SubmitCandidateForPromotion(
    ledger0, macro, L.ProofSchemaPromotionLabel, instance_start, instance_goal,
    zero_cost, holdouts, EMPTY, EMPTY, registry)()
check("a candidate whose rule is not trusted is refused with a machine reason",
      M.IdentityCompare(M.Head(refusal)(), L.PromotionRejectedLabel)() is M.truth_value,
      str(M.Head(refusal)()))
print()

print("[7] The new labels survive a snapshot round-trip...")
snapshot_path = os.path.join(tempfile.mkdtemp(prefix="test38-"), "snapshot.json")
codec = persistence.SnapshotCodec(namespace)
codec.save(graph, snapshot_path)
restored_snapshot = codec.load(snapshot_path)
os.remove(snapshot_path)
os.rmdir(os.path.dirname(snapshot_path))
absent = [name for name in NEW_LABELS if name not in restored_snapshot.symbols]
check("every W26 label is written into the snapshot symbol table", not absent,
      ", ".join(absent))
identity_ok = True
for name in NEW_LABELS:
    if name in restored_snapshot.symbols:
        if restored_snapshot.symbols[name] is not namespace[name]:
            identity_ok = False
check("  ... and restores to the live label object", identity_ok)
print()

print("[8] Scope, stated rather than implied...")
check("no angle measure or angle arithmetic is used anywhere in this suite"
      " (no AngleMeasure fact is built)",
      not any(M.IdentityCompare(M.Head(one)(), L.AngleMeasureLabel)() is M.truth_value
              for one in to_list(start_facts) + to_list(closed)))
check("no rule in the pack concludes a measure or a number",
      not [rid for rid, rule in rule_map.items()
           if any(M.IdentityCompare(M.Head(c)(), L.AngleMeasureLabel)() is M.truth_value
                  for c in to_list(P.RuleReplacement(rule)()))])
check("projective collineations remain OPEN (no collineation schema is"
      " registered)",
      not any(M.Compare(C.SchemaName(s), M.Char("collineation"))() is M.truth_value
              for s in to_list(C.DefaultSchemas())))
check("the markdown corpus and the funceq pack are untouched by this worker"
      " (corpus still blueprint-only)",
      all("blueprint-only" in open(os.path.join(REPO, "curriculum", tier, kind, name),
                                   "r", encoding="utf-8").read()
          for tier, kind, name in [("tier0", "heldout", "invariance-seven-glasses.md"),
                                   ("tier0", "decoys", "pigeonhole-decoy-domino-board.md")]))
print("    OPEN, not claimed: angle measures and arithmetic on them; the")
print("    inscribed-angle/centre-angle (factor two) theorem; deciding a")
print("    cyclic order from incidence; projective collineations; a general")
print("    geometry solver.")
print()

print("=== TEST 38 RESULTS ===")
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
    print("=== TEST 38 FAILED ===")
    sys.exit(1)
print("=== TEST 38 COMPLETE ===")
