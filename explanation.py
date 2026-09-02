"""The explanation substrate: derivations projected into teaching structures.

A derivation is a certificate. An explanation is a *selection* over that
certificate, aimed at a reader. The two are different objects and this
module keeps them different objects. Nothing here weakens, replaces, or
rewrites a derivation; every term built here points back at the derivation
it was projected from, and the projection is measured, never asserted.

Three artifacts stay distinct, exactly as Proved/Supported/Hypothesized do:

    Derivation        -- the trusted certificate, untouched by this module
    ExplanationSpine  -- a measured load-bearing subset, tagged as such
    ExplanationPlan   -- the chosen idea/example/order, a rendering choice

THE SPINE IS RULE-ABLATION, NOT STEP-DELETION
---------------------------------------------
The obvious design -- "remove step S from the derivation, see whether the
goal still closes" -- cannot be implemented against this machine's
derivation representation, and pretending otherwise would produce a spine
that measures nothing. `proof.Step` is a chain link carrying
(current, action, next): the steps form a *linear* sequence where each
step's `current` is the previous step's `next`. Deleting a middle link
does not yield a smaller valid derivation, it yields a severed chain, and
re-running it would report "does not close" for every step regardless of
whether that step was load-bearing. Every step would look essential and
the measurement would be vacuous.

What is genuinely ablatable is the *rule set*. So the spine is measured by
withholding one rule at a time and re-running the same bounded search from
the same start facts at the same fuel:

    baseline  = search(facts, goal, all rules)          -- must close
    ablated_r = search(facts, goal, all rules minus r)  -- for each fired r

A rule whose removal breaks closure is load-bearing: it is on the spine.
A rule whose removal leaves the goal closed is not on the spine -- the
proof routes around it. This is `research.counterfactual_evaluation` run
subtractively: that function measures a rule's *addition*, this one
measures a rule's *removal*, and both bottom out in the same
`evaluated_search` fork so the two directions stay commensurable.

Fan-out ranks the surviving spine rules by how much of the proof depends
on them: the number of firings whose instantiated premises consume a fact
that the rule's own firings produced. The highest-fan-out spine rule is
the governing idea's locus -- the "aha".

WHAT THIS MODULE MAY NOT DO
---------------------------
No free prose generation. No LLM. No theorem-specific text. A rendered
sentence is a chain of word atoms and *embedded machine terms* -- never a
printed copy of a term, so a sentence naming an invariant holds the actual
invariant term and `why did you say that` resolves to a specific law and a
specific spine step. A renderer that cannot cite its law is a defect, not
a style.
"""

from __future__ import annotations

from . import machine as M
from . import labels as Lmod
from .core import Edge, EmptyList, Pair, Head, Tail, IdentityCompare


# ---------------------------------------------------------------------------
# Phase 1 ontology.
#
# Each constructor is a tagged chain. They are deliberately thin: this
# layer's value is in the measurement, not in the term algebra.
# ---------------------------------------------------------------------------


class SpineStep(Edge):
    """One load-bearing rule, with the evidence that it is load-bearing.

    `verdict` is truth_value when withholding this rule broke closure.
    `fanout` is a mark chain counting dependent firings.
    """

    def __init__(self, rule, verdict, fanout):
        args = Pair(rule, Pair(verdict, Pair(fanout, EmptyList)))
        self.result = Pair(Lmod.SpineStepLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class ExplanationSpine(Edge):
    """The measured load-bearing subset of a derivation.

    Carries the goal it was measured against, so a spine can never be read
    as a free-floating claim, and the ablation baseline cost, so the
    measurement is auditable.
    """

    def __init__(self, goal, steps, baseline_cost):
        args = Pair(goal, Pair(steps, Pair(baseline_cost, EmptyList)))
        self.result = Pair(Lmod.ExplanationSpineLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class CoreIdea(Edge):
    def __init__(self, goal, idea):
        args = Pair(goal, Pair(idea, EmptyList))
        self.result = Pair(Lmod.CoreIdeaLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class RepresentationShift(Edge):
    def __init__(self, source, target, reason):
        args = Pair(source, Pair(target, Pair(reason, EmptyList)))
        self.result = Pair(Lmod.RepresentationShiftLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class KeyInvariant(Edge):
    def __init__(self, problem, invariant):
        args = Pair(problem, Pair(invariant, EmptyList))
        self.result = Pair(Lmod.KeyInvariantLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class NaiveFailure(Edge):
    def __init__(self, goal, obstacle):
        args = Pair(goal, Pair(obstacle, EmptyList))
        self.result = Pair(Lmod.NaiveFailureLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class BridgeLemma(Edge):
    def __init__(self, lemma, role):
        args = Pair(lemma, Pair(role, EmptyList))
        self.result = Pair(Lmod.BridgeLemmaLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class NeededFor(Edge):
    def __init__(self, lemma, goal):
        args = Pair(lemma, Pair(goal, EmptyList))
        self.result = Pair(Lmod.NeededForLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class ImportedBecause(Edge):
    def __init__(self, theorem, capability_gap):
        args = Pair(theorem, Pair(capability_gap, EmptyList))
        self.result = Pair(Lmod.ImportedBecauseLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class OmittedDetail(Edge):
    def __init__(self, detail, reason):
        args = Pair(detail, Pair(reason, EmptyList))
        self.result = Pair(Lmod.OmittedDetailLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class AudienceLevel(Edge):
    def __init__(self, level):
        args = Pair(level, EmptyList)
        self.result = Pair(Lmod.AudienceLevelLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class ExplanationPlan(Edge):
    """The rendering choice. Explicitly not a proof.

    Holds the audience, the goal, the measured spine, the classified core
    idea, and the key invariant. Anything absent is EmptyList -- a plan is
    allowed to be partial, and a partial plan renders fewer sentences
    rather than inventing them.
    """

    def __init__(self, audience, goal, spine, core_idea, key_invariant):
        args = Pair(
            audience,
            Pair(goal, Pair(spine, Pair(core_idea, Pair(key_invariant, EmptyList)))),
        )
        self.result = Pair(Lmod.ExplanationPlanLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


# --- accessors -------------------------------------------------------------


class TaggedArgs(Edge):
    """The argument chain of a tagged term, or EmptyList on a tag mismatch."""

    def __init__(self, term, label):
        self.result = EmptyList
        if M.IsPair(term)() is M.truth_value:
            if IdentityCompare(Head(term)(), label)() is M.truth_value:
                self.result = Tail(term)()
        super().__init__(inputs=Pair(term, Pair(label, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SpineStepRule(Edge):
    def __init__(self, step):
        args = TaggedArgs(step, Lmod.SpineStepLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(args)()
        super().__init__(inputs=Pair(step, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SpineStepVerdict(Edge):
    def __init__(self, step):
        args = TaggedArgs(step, Lmod.SpineStepLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(args)())()
        super().__init__(inputs=Pair(step, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SpineStepFanout(Edge):
    def __init__(self, step):
        args = TaggedArgs(step, Lmod.SpineStepLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(Tail(args)())())()
        super().__init__(inputs=Pair(step, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SpineGoal(Edge):
    def __init__(self, spine):
        args = TaggedArgs(spine, Lmod.ExplanationSpineLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(args)()
        super().__init__(inputs=Pair(spine, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SpineSteps(Edge):
    def __init__(self, spine):
        args = TaggedArgs(spine, Lmod.ExplanationSpineLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(args)())()
        super().__init__(inputs=Pair(spine, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PlanAudience(Edge):
    def __init__(self, plan):
        args = TaggedArgs(plan, Lmod.ExplanationPlanLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(args)()
        super().__init__(inputs=Pair(plan, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PlanGoal(Edge):
    def __init__(self, plan):
        args = TaggedArgs(plan, Lmod.ExplanationPlanLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(args)())()
        super().__init__(inputs=Pair(plan, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PlanSpine(Edge):
    def __init__(self, plan):
        args = TaggedArgs(plan, Lmod.ExplanationPlanLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(Tail(args)())())()
        super().__init__(inputs=Pair(plan, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PlanCoreIdea(Edge):
    def __init__(self, plan):
        args = TaggedArgs(plan, Lmod.ExplanationPlanLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(Tail(Tail(args)())())())()
        super().__init__(inputs=Pair(plan, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PlanKeyInvariant(Edge):
    def __init__(self, plan):
        args = TaggedArgs(plan, Lmod.ExplanationPlanLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(Tail(Tail(Tail(args)())())())())()
        super().__init__(inputs=Pair(plan, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CoreIdeaShape(Edge):
    def __init__(self, core):
        args = TaggedArgs(core, Lmod.CoreIdeaLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(args)())()
        super().__init__(inputs=Pair(core, EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# The fixed idea-shape library.
#
# Same discipline as the invariant observable library: a small, inspectable,
# closed set. Classification is by term shape against machinery that already
# exists; an unrecognised proof gets EmptyList, never a guess. Growing this
# list is a human-gated act, exactly like teaching a new observable.
# ---------------------------------------------------------------------------

IDEA_INVARIANT = Lmod.KeyInvariantLabel
IDEA_UNCLASSIFIED = EmptyList


class ClassifyIdeaShape(Edge):
    """Name the governing idea of a rule, or refuse.

    Today exactly one shape is wired: Invariant, recognised when the rule
    is `Preserves`-shaped under the invariance module's own predicate. The
    remaining shapes named in the design (Extremal, Bijection, Descent,
    Contradiction, RepresentationChange) are deliberately NOT stubbed --
    an unimplemented classifier that returns a plausible label is worse
    than one that returns nothing, because it manufactures agreement in
    the transfer test. Each additional shape must arrive with its own
    recogniser and its own held-out evidence.
    """

    def __init__(self, term):
        from . import invariance as Imod

        self.result = IDEA_UNCLASSIFIED
        if Imod.IsPreserves(term)() is M.truth_value:
            self.result = IDEA_INVARIANT
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Chain measurement.
# ---------------------------------------------------------------------------


class ChainWithout(Edge):
    """A chain with every occurrence of one item removed, by identity."""

    def __init__(self, chain, victim):
        kept = EmptyList
        cursor = chain
        while IdentityCompare(cursor, EmptyList)() is M.false_value:
            item = Head(cursor)()
            if IdentityCompare(item, victim)() is M.false_value:
                kept = Pair(item, kept)
            cursor = Tail(cursor)()
        self.result = M.Reverse(kept)()
        super().__init__(inputs=Pair(chain, Pair(victim, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ChainHolds(Edge):
    """Machine truth: some element of the chain is identical to the item."""

    def __init__(self, chain, item):
        self.result = M.false_value
        cursor = chain
        while IdentityCompare(cursor, EmptyList)() is M.false_value:
            if IdentityCompare(Head(cursor)(), item)() is M.truth_value:
                self.result = M.truth_value
                cursor = EmptyList
            else:
                cursor = Tail(cursor)()
        super().__init__(inputs=Pair(chain, Pair(item, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FiredRules(Edge):
    """The distinct rules appearing in a firing chain, in firing order."""

    def __init__(self, fired):
        seen = EmptyList
        cursor = fired
        while IdentityCompare(cursor, EmptyList)() is M.false_value:
            rule = Head(Head(cursor)())()
            if ChainHolds(seen, rule)() is M.false_value:
                seen = Pair(rule, seen)
            cursor = Tail(cursor)()
        self.result = M.Reverse(seen)()
        super().__init__(inputs=Pair(fired, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SubstituteTerm(Edge):
    """One variable replaced by one value throughout a term."""

    def __init__(self, term, var, value):
        self.result = self._walk(term, var, value)
        super().__init__(
            inputs=Pair(term, Pair(var, Pair(value, EmptyList))), results=self.result
        )

    def _walk(self, term, var, value):
        if IdentityCompare(term, var)() is M.truth_value:
            return value
        if M.IsPair(term)() is M.false_value:
            return term
        return Pair(
            self._walk(Head(term)(), var, value),
            self._walk(Tail(term)(), var, value),
        )

    def __call__(self):
        return self.result


class InstantiateTerm(Edge):
    """A term under a firing's binding chain.

    Bindings are Pair(var, Pair(value, ...)) entries. Anything unrecognised
    passes through unchanged: this is a ranking measurement over an already
    validated proof, so an imprecise substitution costs ordering, never
    soundness.
    """

    def __init__(self, term, bindings):
        out = term
        cursor = bindings
        while IdentityCompare(cursor, EmptyList)() is M.false_value:
            entry = Head(cursor)()
            if M.IsPair(entry)() is M.truth_value:
                rest = Tail(entry)()
                if M.IsPair(rest)() is M.truth_value:
                    out = SubstituteTerm(out, Head(entry)(), Head(rest)())()
            cursor = Tail(cursor)()
        self.result = out
        super().__init__(inputs=Pair(term, Pair(bindings, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ConsumesAny(Edge):
    """Machine truth: an instantiated premise equals an already-produced fact.

    Structural equality (`Compare`), not identity: the consumer's premise is
    a freshly built term, never the same object the producer emitted.
    """

    def __init__(self, premises, bindings, produced):
        self.result = M.false_value
        cursor = premises
        while IdentityCompare(cursor, EmptyList)() is M.false_value:
            fact = InstantiateTerm(Head(cursor)(), bindings)()
            inner = produced
            while IdentityCompare(inner, EmptyList)() is M.false_value:
                if M.Compare(fact, Head(inner)())() is M.truth_value:
                    self.result = M.truth_value
                    inner = EmptyList
                else:
                    inner = Tail(inner)()
            if self.result is M.truth_value:
                cursor = EmptyList
            else:
                cursor = Tail(cursor)()
        super().__init__(
            inputs=Pair(premises, Pair(bindings, Pair(produced, EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RuleFanout(Edge):
    """A mark chain counting later firings that depend on this rule.

    Dataflow linkage, same shape as the trace miner's: a firing depends on
    this rule when one of its instantiated premises is a conclusion this
    rule's own earlier firings emitted. Walked in firing order, so only
    genuinely later consumers count.

    TWO SHAPE TRAPS, both found by measurement, both of which silently
    produced an empty fanout before they were fixed:

    1. `RuleIsUnary` means "one PREMISE", not "one conclusion", so
       `invariance.ReplacementFacts` wraps a conclusion in a chain only for
       single-premise rules. Reading its output as a fact chain splits a
       two-premise rule's conclusion `(tag ?x)` into the two junk "facts"
       `tag` and `?x`. The conclusion is always the single term
       `RuleReplacement(rule)`; that is what a firing produces.

    2. A firing entry's bindings are variable->ATOM pairs (?y -> b), not the
       premise facts. Comparing binding values against produced facts
       therefore never matches. Consumption has to be tested by
       instantiating the consumer's PREMISES under its bindings and
       comparing those whole facts against what earlier firings emitted.
    """

    def __init__(self, fired, rule):
        from .proof import RulePremises, RuleReplacement

        produced = EmptyList
        marks = EmptyList
        cursor = fired
        while IdentityCompare(cursor, EmptyList)() is M.false_value:
            entry = Head(cursor)()
            entry_rule = Head(entry)()
            bindings = Head(Tail(entry)())()
            if IdentityCompare(entry_rule, rule)() is M.truth_value:
                produced = Pair(
                    InstantiateTerm(RuleReplacement(entry_rule)(), bindings)(),
                    produced,
                )
            else:
                premises = RulePremises(entry_rule)()
                if ConsumesAny(premises, bindings, produced)() is M.truth_value:
                    marks = Pair(EmptyList, marks)
            cursor = Tail(cursor)()
        self.result = marks
        super().__init__(inputs=Pair(fired, Pair(rule, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class HighestFanoutStep(Edge):
    """The spine step the most of the proof hangs off -- the 'aha'.

    Ties break toward the earliest step, so the answer is deterministic
    across runs. Determinism matters here for the same reason it mattered
    for reset-remine: an explanation that reorders itself between runs
    cannot be regression-tested.
    """

    def __init__(self, spine):
        from .research import ChainShorter

        best = EmptyList
        best_fanout = EmptyList
        cursor = SpineSteps(spine)()
        while IdentityCompare(cursor, EmptyList)() is M.false_value:
            step = Head(cursor)()
            fanout = SpineStepFanout(step)()
            if IdentityCompare(best, EmptyList)() is M.truth_value:
                best = step
                best_fanout = fanout
            elif ChainShorter(best_fanout, fanout)() is M.truth_value:
                best = step
                best_fanout = fanout
            cursor = Tail(cursor)()
        self.result = best
        super().__init__(inputs=Pair(spine, EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Spine extraction by rule ablation.
# ---------------------------------------------------------------------------


class ExtractSpine(Edge):
    """Measure which rules are load-bearing for this closure.

    Result: Pair(spine, Pair(baseline_closed, EmptyList)).

    The baseline must close for the measurement to mean anything: a spine
    over a proof that never closed is not a smaller proof, it is noise.
    When the baseline does not close the spine comes back empty and the
    flag says so, rather than reporting every rule as essential.

    Only rules that actually FIRED are candidates. An unfired rule is
    trivially non-load-bearing and ablating it would burn a search for a
    foregone answer.
    """

    def __init__(self, start_facts, goal_facts, rules, fuel=None):
        from . import research as Rmod

        if fuel is None:
            fuel = Rmod.DEFAULT_SEARCH_FUEL

        baseline = Head(Rmod.evaluated_search(start_facts, goal_facts, rules, fuel))()
        baseline_closed = Rmod.ForwardSearchClosed(baseline)()
        baseline_cost = Rmod.ForwardSearchCost(baseline)()

        if baseline_closed is M.false_value:
            spine = ExplanationSpine(goal_facts, EmptyList, baseline_cost)()
            self.result = Pair(spine, Pair(M.false_value, EmptyList))
        else:
            fired = Rmod.ForwardSearchFired(baseline)()
            steps = EmptyList
            candidates = FiredRules(fired)()
            while IdentityCompare(candidates, EmptyList)() is M.false_value:
                rule = Head(candidates)()
                reduced = ChainWithout(rules, rule)()
                ablated = Head(
                    Rmod.evaluated_search(start_facts, goal_facts, reduced, fuel)
                )()
                still_closed = Rmod.ForwardSearchClosed(ablated)()
                # Load-bearing exactly when withholding it breaks closure.
                if still_closed is M.false_value:
                    steps = Pair(
                        SpineStep(rule, M.truth_value, RuleFanout(fired, rule)())(),
                        steps,
                    )
                candidates = Tail(candidates)()
            spine = ExplanationSpine(goal_facts, M.Reverse(steps)(), baseline_cost)()
            self.result = Pair(spine, Pair(M.truth_value, EmptyList))

        super().__init__(
            inputs=Pair(start_facts, Pair(goal_facts, Pair(rules, EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BuildPlan(Edge):
    """Spine, then classify, then plan. EmptyList when nothing closed.

    The plan is a rendering choice over a measured spine. It never becomes
    the stored proof and carries no authority to close anything.
    """

    def __init__(self, start_facts, goal_facts, rules, audience, fuel=None):
        pair = ExtractSpine(start_facts, goal_facts, rules, fuel)()
        spine = Head(pair)()
        closed = Head(Tail(pair)())()
        self.result = EmptyList
        if closed is M.truth_value:
            core = EmptyList
            top = HighestFanoutStep(spine)()
            if IdentityCompare(top, EmptyList)() is M.false_value:
                shape = ClassifyIdeaShape(SpineStepRule(top)())()
                if IdentityCompare(shape, IDEA_UNCLASSIFIED)() is M.false_value:
                    core = CoreIdea(goal_facts, shape)()
            self.result = ExplanationPlan(audience, goal_facts, spine, core, EmptyList)()
        super().__init__(
            inputs=Pair(start_facts, Pair(goal_facts, Pair(rules, EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Render laws.
#
# A render law is an Edge keyed on a term shape. It answers either EmptyList
# -- declining -- or one RenderedSentence. The library is a closed, ordered
# set walked by RenderPlan.
#
# A sentence is a chain of pieces: word atoms and EMBEDDED MACHINE TERMS. A
# law that names an invariant embeds the invariant term itself, never a
# printed copy of it, so the sentence remains connected to the object it is
# about. There is no fallback sentence: a fallback is precisely where
# unbacked prose would enter.
# ---------------------------------------------------------------------------

InvariantCoreLawName = M.Char("invariant_core_law")
SpineSizeLawName = M.Char("spine_size_law")
PreservesStepLawName = M.Char("preserves_step_law")


class RenderedSentence(Edge):
    """One sentence, plus the law and the term that produced it.

    The provenance is not decoration. An explanation whose sentences cannot
    each name their law is exactly the fluent-but-unauditable output this
    substrate exists to avoid.
    """

    def __init__(self, pieces, law_name, source_term):
        args = Pair(pieces, Pair(law_name, Pair(source_term, EmptyList)))
        self.result = Pair(Lmod.RenderLawLabel, args)
        super().__init__(inputs=args, results=self.result)

    def __call__(self):
        return self.result


class SentencePieces(Edge):
    def __init__(self, sentence):
        args = TaggedArgs(sentence, Lmod.RenderLawLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(args)()
        super().__init__(inputs=Pair(sentence, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SentenceLaw(Edge):
    def __init__(self, sentence):
        args = TaggedArgs(sentence, Lmod.RenderLawLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(args)())()
        super().__init__(inputs=Pair(sentence, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SentenceSource(Edge):
    def __init__(self, sentence):
        args = TaggedArgs(sentence, Lmod.RenderLawLabel)()
        self.result = EmptyList
        if IdentityCompare(args, EmptyList)() is M.false_value:
            self.result = Head(Tail(Tail(args)())())()
        super().__init__(inputs=Pair(sentence, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SentenceMentions(Edge):
    """Machine truth: a sentence embeds this exact term among its pieces."""

    def __init__(self, sentence, term):
        self.result = ChainHolds(SentencePieces(sentence)(), term)()
        super().__init__(inputs=Pair(sentence, Pair(term, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PreservesObservable(Edge):
    """The observable a Preserves-shaped term is about, or EmptyList."""

    def __init__(self, term):
        from . import invariance as Imod

        self.result = EmptyList
        if Imod.IsPreserves(term)() is M.truth_value:
            self.result = Head(Tail(Tail(term)())())()
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InvariantCoreLaw(Edge):
    """CoreIdea(goal, Invariant) -> the governing-idea sentence."""

    def __init__(self, plan):
        self.result = EmptyList
        core = PlanCoreIdea(plan)()
        if IdentityCompare(core, EmptyList)() is M.false_value:
            shape = CoreIdeaShape(core)()
            if IdentityCompare(shape, IDEA_INVARIANT)() is M.truth_value:
                pieces = Pair(
                    M.Char("The"),
                    Pair(
                        M.Char("key"),
                        Pair(
                            M.Char("idea"),
                            Pair(
                                M.Char("is"),
                                Pair(
                                    M.Char("that"),
                                    Pair(
                                        M.Char("something"),
                                        Pair(
                                            M.Char("does"),
                                            Pair(
                                                M.Char("not"),
                                                Pair(M.Char("change"), EmptyList),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
                self.result = RenderedSentence(pieces, InvariantCoreLawName, core)()
        super().__init__(inputs=Pair(plan, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SpineSizeLaw(Edge):
    """The spine's size, stated as a selection rather than a proof claim.

    The count is embedded as the mark chain itself, so the sentence carries
    the measurement rather than a rendered numeral.
    """

    def __init__(self, plan):
        self.result = EmptyList
        spine = PlanSpine(plan)()
        steps = SpineSteps(spine)()
        if IdentityCompare(steps, EmptyList)() is M.false_value:
            marks = EmptyList
            cursor = steps
            while IdentityCompare(cursor, EmptyList)() is M.false_value:
                marks = Pair(EmptyList, marks)
                cursor = Tail(cursor)()
            pieces = Pair(
                M.Char("Load-bearing"),
                Pair(
                    M.Char("steps:"),
                    Pair(
                        marks,
                        Pair(
                            M.Char("--"),
                            Pair(
                                M.Char("removing"),
                                Pair(
                                    M.Char("any"),
                                    Pair(
                                        M.Char("one,"),
                                        Pair(
                                            M.Char("the"),
                                            Pair(
                                                M.Char("goal"),
                                                Pair(
                                                    M.Char("no"),
                                                    Pair(
                                                        M.Char("longer"),
                                                        Pair(
                                                            M.Char("follows"),
                                                            EmptyList,
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            )
            self.result = RenderedSentence(pieces, SpineSizeLawName, spine)()
        super().__init__(inputs=Pair(plan, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PreservesStepLaw(Edge):
    """A Preserves-shaped spine step -> the 'every step preserves' sentence.

    The observable is embedded as the term itself. A step whose rule is not
    Preserves-shaped has no observable to name, and the law declines rather
    than emitting a placeholder such as "the invariant".
    """

    def __init__(self, step):
        self.result = EmptyList
        observable = PreservesObservable(SpineStepRule(step)())()
        if IdentityCompare(observable, EmptyList)() is M.false_value:
            pieces = Pair(
                M.Char("Every"),
                Pair(
                    M.Char("step"),
                    Pair(
                        M.Char("preserves"),
                        Pair(
                            observable,
                            Pair(
                                M.Char("--"),
                                Pair(
                                    M.Char("the"),
                                    Pair(
                                        M.Char("same"),
                                        Pair(
                                            M.Char("at"),
                                            Pair(
                                                M.Char("the"),
                                                Pair(
                                                    M.Char("end"),
                                                    Pair(
                                                        M.Char("as"),
                                                        Pair(
                                                            M.Char("at"),
                                                            Pair(
                                                                M.Char("the"),
                                                                Pair(
                                                                    M.Char("start"),
                                                                    EmptyList,
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            )
            self.result = RenderedSentence(pieces, PreservesStepLawName, step)()
        super().__init__(inputs=Pair(step, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RenderPlan(Edge):
    """Render a plan into a chain of RenderedSentence terms.

    The plan-level laws run in order, then each spine step's laws in spine
    order. A law that declines contributes nothing. An unrenderable plan
    renders as an empty chain, and the caller is expected to say so plainly
    rather than to improvise.
    """

    def __init__(self, plan):
        out = EmptyList

        sentence = InvariantCoreLaw(plan)()
        if IdentityCompare(sentence, EmptyList)() is M.false_value:
            out = Pair(sentence, out)

        sentence = SpineSizeLaw(plan)()
        if IdentityCompare(sentence, EmptyList)() is M.false_value:
            out = Pair(sentence, out)

        cursor = SpineSteps(PlanSpine(plan)())()
        while IdentityCompare(cursor, EmptyList)() is M.false_value:
            sentence = PreservesStepLaw(Head(cursor)())()
            if IdentityCompare(sentence, EmptyList)() is M.false_value:
                out = Pair(sentence, out)
            cursor = Tail(cursor)()

        self.result = M.Reverse(out)()
        super().__init__(inputs=Pair(plan, EmptyList), results=self.result)

    def __call__(self):
        return self.result
