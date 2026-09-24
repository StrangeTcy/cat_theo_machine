"""Machine terms for supervised textbook ingestion.

The host supplies extracted passages and alignments.  This module stores those
alignments without parsing files or inferring unrestricted natural language.
Mathematical entries carry proof evidence; historical entries retain sources.
"""

from __future__ import annotations

from . import graph as G
from . import labels as L
from . import machine as M
from . import planner as P


class Source(M.Edge):
    def __init__(self, book, chapter, page):
        self.result = M.Pair(
            L.SourceLabel,
            M.Pair(book, M.Pair(chapter, M.Pair(page, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(book, M.Pair(chapter, M.Pair(page, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Surface(M.Edge):
    def __init__(self, text):
        self.result = M.Pair(L.SurfaceLabel, M.Pair(text, M.EmptyList))
        super().__init__(inputs=M.Pair(text, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Mathematics(M.Edge):
    def __init__(self):
        self.result = M.Pair(L.MathematicsLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class History(M.Edge):
    def __init__(self):
        self.result = M.Pair(L.HistoryLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Lesson(M.Edge):
    def __init__(self, title, entries):
        self.result = M.Pair(L.LessonLabel, M.Pair(title, M.Pair(entries, M.EmptyList)))
        super().__init__(inputs=M.Pair(title, M.Pair(entries, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class LessonTitle(M.Edge):
    def __init__(self, lesson):
        self.result = M.Head(M.Tail(lesson)())()
        super().__init__(inputs=M.Pair(lesson, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LessonEntries(M.Edge):
    def __init__(self, lesson):
        self.result = M.Head(M.Tail(M.Tail(lesson)())())()
        super().__init__(inputs=M.Pair(lesson, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Entry(M.Edge):
    def __init__(self, source, domain, surface, target, evidence):
        self.result = M.Pair(
            L.EntryLabel,
            M.Pair(
                source,
                M.Pair(domain, M.Pair(surface, M.Pair(target, M.Pair(evidence, M.EmptyList)))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                source,
                M.Pair(domain, M.Pair(surface, M.Pair(target, M.Pair(evidence, M.EmptyList)))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class EntrySource(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntryDomain(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntrySurface(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(entry)())())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntryTarget(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(entry)())())())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntryEvidence(M.Edge):
    def __init__(self, entry):
        fields = M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(entry)())())())())()
        self.result = M.Head(fields)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GroundedExample(M.Edge):
    def __init__(self, surface, target, evidence):
        self.result = M.Pair(
            L.GroundedExampleLabel,
            M.Pair(surface, M.Pair(target, M.Pair(evidence, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(surface, M.Pair(target, M.Pair(evidence, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class EntryGroundedExample(M.Edge):
    def __init__(self, entry):
        self.result = GroundedExample(
            EntrySurface(entry)(), EntryTarget(entry)(), EntryEvidence(entry)()
        )()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Problem(M.Edge):
    def __init__(self, statement, formal_goal, givens):
        self.result = M.Pair(
            L.ProblemLabel,
            M.Pair(statement, M.Pair(formal_goal, M.Pair(givens, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(statement, M.Pair(formal_goal, M.Pair(givens, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Hint(M.Edge):
    def __init__(self, surface, formal_hint):
        self.result = M.Pair(L.HintLabel, M.Pair(surface, M.Pair(formal_hint, M.EmptyList)))
        super().__init__(inputs=M.Pair(surface, M.Pair(formal_hint, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class UsesStrategy(M.Edge):
    def __init__(self, problem, strategy):
        self.result = M.Pair(
            L.UsesStrategyLabel, M.Pair(problem, M.Pair(strategy, M.EmptyList))
        )
        super().__init__(inputs=M.Pair(problem, M.Pair(strategy, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class DerivationFragment(M.Edge):
    def __init__(self, goal, steps):
        self.result = M.Pair(
            L.DerivationFragmentLabel, M.Pair(goal, M.Pair(steps, M.EmptyList))
        )
        super().__init__(inputs=M.Pair(goal, M.Pair(steps, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Goal(M.Edge):
    def __init__(self, proposition):
        self.result = M.Pair(L.GoalLabel, M.Pair(proposition, M.EmptyList))
        super().__init__(inputs=M.Pair(proposition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Claims(M.Edge):
    def __init__(self, source, proposition):
        self.result = M.Pair(
            L.ClaimsLabel, M.Pair(source, M.Pair(proposition, M.EmptyList))
        )
        super().__init__(inputs=M.Pair(source, M.Pair(proposition, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ClaimSource(M.Edge):
    def __init__(self, claim):
        self.result = M.Head(M.Tail(claim)())()
        super().__init__(inputs=M.Pair(claim, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ClaimProposition(M.Edge):
    def __init__(self, claim):
        self.result = M.Head(M.Tail(M.Tail(claim)())())()
        super().__init__(inputs=M.Pair(claim, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Supports(M.Edge):
    def __init__(self, source, proposition):
        self.result = M.Pair(
            L.SupportsLabel, M.Pair(source, M.Pair(proposition, M.EmptyList))
        )
        super().__init__(inputs=M.Pair(source, M.Pair(proposition, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Contradicts(M.Edge):
    def __init__(self, left_claim, right_claim):
        self.result = M.Pair(
            L.HistoricalContradictsLabel,
            M.Pair(left_claim, M.Pair(right_claim, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(left_claim, M.Pair(right_claim, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class OccursOn(M.Edge):
    def __init__(self, event, date):
        self.result = M.Pair(L.OccursOnLabel, M.Pair(event, M.Pair(date, M.EmptyList)))
        super().__init__(inputs=M.Pair(event, M.Pair(date, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Before(M.Edge):
    def __init__(self, earlier, later):
        self.result = M.Pair(L.BeforeLabel, M.Pair(earlier, M.Pair(later, M.EmptyList)))
        super().__init__(inputs=M.Pair(earlier, M.Pair(later, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Causes(M.Edge):
    def __init__(self, cause, effect):
        self.result = M.Pair(L.CausesLabel, M.Pair(cause, M.Pair(effect, M.EmptyList)))
        super().__init__(inputs=M.Pair(cause, M.Pair(effect, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ParticipatesIn(M.Edge):
    def __init__(self, actor, event):
        self.result = M.Pair(
            L.ParticipatesInLabel, M.Pair(actor, M.Pair(event, M.EmptyList))
        )
        super().__init__(inputs=M.Pair(actor, M.Pair(event, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class OccursAt(M.Edge):
    def __init__(self, event, place):
        self.result = M.Pair(L.OccursAtLabel, M.Pair(event, M.Pair(place, M.EmptyList)))
        super().__init__(inputs=M.Pair(event, M.Pair(place, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ClaimStore(M.Edge):
    def __init__(self, claims, contradictions):
        self.result = M.Pair(
            L.ClaimStoreLabel, M.Pair(claims, M.Pair(contradictions, M.EmptyList))
        )
        super().__init__(
            inputs=M.Pair(claims, M.Pair(contradictions, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class ClaimStoreClaims(M.Edge):
    def __init__(self, store):
        self.result = M.Head(M.Tail(store)())()
        super().__init__(inputs=M.Pair(store, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ClaimStoreContradictions(M.Edge):
    def __init__(self, store):
        self.result = M.Head(M.Tail(M.Tail(store)())())()
        super().__init__(inputs=M.Pair(store, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DateClaimsConflict(M.Edge):
    """Detect incompatible dates asserted for one event by distinct claims."""

    def __init__(self, left_claim, right_claim):
        result = M.false_value
        left = ClaimProposition(left_claim)()
        right = ClaimProposition(right_claim)()
        if M.IsPair(left)() is M.truth_value:
            if M.IsPair(right)() is M.truth_value:
                if M.TermEqual(M.Head(left)(), L.OccursOnLabel)() is M.truth_value:
                    if M.TermEqual(M.Head(right)(), L.OccursOnLabel)() is M.truth_value:
                        left_fields = M.Tail(left)()
                        right_fields = M.Tail(right)()
                        left_event = M.Head(left_fields)()
                        right_event = M.Head(right_fields)()
                        if M.TermEqual(left_event, right_event)() is M.truth_value:
                            left_date = M.Head(M.Tail(left_fields)())()
                            right_date = M.Head(M.Tail(right_fields)())()
                            if M.TermEqual(left_date, right_date)() is M.false_value:
                                result = M.truth_value
        self.result = result
        super().__init__(
            inputs=M.Pair(left_claim, M.Pair(right_claim, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class ClaimStoreAdd(M.Edge):
    """Append a sourced claim and retain every detected conflict."""

    def __init__(self, store, claim):
        claims = ClaimStoreClaims(store)()
        contradictions = ClaimStoreContradictions(store)()
        remaining = claims
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            prior = M.Head(remaining)()
            if DateClaimsConflict(prior, claim)() is M.truth_value:
                contradictions = M.Pair(Contradicts(prior, claim)(), contradictions)
            remaining = M.Tail(remaining)()
        self.result = ClaimStore(M.Pair(claim, claims), contradictions)()
        super().__init__(inputs=M.Pair(store, M.Pair(claim, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Why(M.Edge):
    """Retrieve evidence aligned to a surface passage or target term."""

    def __init__(self, lesson, query):
        result = M.EmptyList
        remaining = LessonEntries(lesson)()
        searching = M.truth_value
        while M.IdentityCompare(searching, M.truth_value)() is M.truth_value:
            if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
                searching = M.false_value
            else:
                entry = M.Head(remaining)()
                surface_match = M.TermEqual(EntrySurface(entry)(), query)()
                target_match = M.TermEqual(EntryTarget(entry)(), query)()
                if M.OrAtom(surface_match, target_match)() is M.truth_value:
                    result = EntryEvidence(entry)()
                    searching = M.false_value
                else:
                    remaining = M.Tail(remaining)()
        self.result = result
        super().__init__(inputs=M.Pair(lesson, M.Pair(query, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CorrespondenceLaw(M.Edge):
    def __init__(self, domain, surface_pattern, target_pattern):
        self.result = M.Pair(
            L.CorrespondenceLawLabel,
            M.Pair(domain, M.Pair(surface_pattern, M.Pair(target_pattern, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(
                domain, M.Pair(surface_pattern, M.Pair(target_pattern, M.EmptyList))
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InduceCorrespondences(M.Edge):
    """Submit paired alignments as inert proposals for curator approval."""

    def __init__(self, lesson):
        store = G.ProposalStore(M.EmptyList)()
        remaining = LessonEntries(lesson)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            law = CorrespondenceLaw(
                EntryDomain(entry)(), EntrySurface(entry)(), EntryTarget(entry)()
            )()
            proposal = G.Proposal(law, EntryGroundedExample(entry)())()
            store = G.ProposalStoreSubmit(store, proposal)()
            remaining = M.Tail(remaining)()
        self.result = store
        super().__init__(inputs=M.Pair(lesson, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IMOTinyCorpus(M.Edge):
    """Four controlled strategy alignments; no book text is parsed here."""

    def __init__(self):
        domain = Mathematics()()
        source = Source(M.Char("IMO strategy lessons"), M.Char("controlled"), M.Char("1"))()
        invariant_problem = M.Char("repeated-move reachability")
        extremal_problem = M.Char("finite-family existence")
        pigeon_problem = M.Char("finite assignment collision")
        counting_problem = M.Char("recursive counting identity")
        invariant_strategy = M.Pair(L.InvariantLabel, M.Pair(M.Char("parity"), M.EmptyList))
        extremal_strategy = P.Extremal(
            M.Char("paths"), M.Char("length"), P.ExtremalMax()(), M.Char("extend endpoint")
        )()
        pigeon_strategy = P.Pigeonhole(
            M.Char("objects"), M.Char("boxes"), M.Char("assignment")
        )()
        divide_strategy = P.Divide(
            M.Char("subinstances"), M.Char("combine counts"), M.Char("size")
        )()
        entries = M.Pair(
            Entry(
                source,
                domain,
                Surface(M.Char("Track parity through every move."))(),
                UsesStrategy(invariant_problem, invariant_strategy)(),
                DerivationFragment(
                    Goal(M.Char("unreachable target"))(), M.Char("all moves preserve parity")
                )(),
            )(),
            M.Pair(
                Entry(
                    source,
                    domain,
                    Surface(M.Char("Choose a longest path."))(),
                    UsesStrategy(extremal_problem, extremal_strategy)(),
                    DerivationFragment(
                        Goal(M.Char("endpoint property"))(), M.Char("extension contradicts maximality")
                    )(),
                )(),
                M.Pair(
                    Entry(
                        source,
                        domain,
                        Surface(M.Char("There are more objects than boxes."))(),
                        UsesStrategy(pigeon_problem, pigeon_strategy)(),
                        DerivationFragment(
                            Goal(M.Char("collision"))(), M.Char("finite total map and cardinality inequality")
                        )(),
                    )(),
                    M.Pair(
                        Entry(
                            source,
                            domain,
                            Surface(M.Char("Split the count into smaller instances."))(),
                            UsesStrategy(counting_problem, divide_strategy)(),
                            DerivationFragment(
                                Goal(M.Char("counting identity"))(), M.Char("rank decreases and counts combine")
                            )(),
                        )(),
                        M.EmptyList,
                    ),
                ),
            ),
        )
        self.result = Lesson(M.Char("Controlled IMO corpus"), entries)()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class HistoryTinyCorpus(M.Edge):
    """Controlled chronology with preserved disagreement between two sources."""

    def __init__(self):
        domain = History()()
        source_a = Source(M.Char("History text A"), M.Char("short section"), M.Char("10"))()
        source_b = Source(M.Char("History text B"), M.Char("short section"), M.Char("22"))()
        event_a = M.Char("assembly")
        event_b = M.Char("declaration")
        event_c = M.Char("settlement")
        date_a = OccursOn(event_a, M.Char("1789"))()
        date_b = OccursOn(event_b, M.Char("1790"))()
        date_c = OccursOn(event_c, M.Char("1791"))()
        disputed_date = OccursOn(event_a, M.Char("1790"))()
        claim_a = Claims(source_a, date_a)()
        claim_disputed = Claims(source_b, disputed_date)()
        entries = M.Pair(
            Entry(source_a, domain, Surface(M.Char("The assembly met in 1789."))(), claim_a, Supports(source_a, date_a)())(),
            M.Pair(
                Entry(source_a, domain, Surface(M.Char("The declaration followed in 1790."))(), Claims(source_a, date_b)(), Supports(source_a, date_b)())(),
                M.Pair(
                    Entry(source_a, domain, Surface(M.Char("The settlement occurred in 1791."))(), Claims(source_a, date_c)(), Supports(source_a, date_c)())(),
                    M.Pair(
                        Entry(source_a, domain, Surface(M.Char("The assembly preceded the declaration."))(), Claims(source_a, Before(event_a, event_b)())(), source_a)(),
                        M.Pair(
                            Entry(source_a, domain, Surface(M.Char("The declaration preceded the settlement."))(), Claims(source_a, Before(event_b, event_c)())(), source_a)(),
                            M.Pair(
                                Entry(source_a, domain, Surface(M.Char("The declaration contributed to the settlement."))(), Claims(source_a, Causes(event_b, event_c)())(), source_a)(),
                                M.Pair(
                                    Entry(source_b, domain, Surface(M.Char("Another account dates the assembly to 1790."))(), claim_disputed, Contradicts(claim_a, claim_disputed)())(),
                                    M.EmptyList,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        self.result = Lesson(M.Char("Controlled history corpus"), entries)()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


__all__ = (
    "Source",
    "Surface",
    "Mathematics",
    "History",
    "Lesson",
    "LessonTitle",
    "LessonEntries",
    "Entry",
    "EntrySource",
    "EntryDomain",
    "EntrySurface",
    "EntryTarget",
    "EntryEvidence",
    "GroundedExample",
    "EntryGroundedExample",
    "Problem",
    "Hint",
    "UsesStrategy",
    "DerivationFragment",
    "Goal",
    "Claims",
    "ClaimSource",
    "ClaimProposition",
    "Supports",
    "Contradicts",
    "OccursOn",
    "Before",
    "Causes",
    "ParticipatesIn",
    "OccursAt",
    "ClaimStore",
    "ClaimStoreClaims",
    "ClaimStoreContradictions",
    "DateClaimsConflict",
    "ClaimStoreAdd",
    "Why",
    "CorrespondenceLaw",
    "InduceCorrespondences",
    "IMOTinyCorpus",
    "HistoryTinyCorpus",
)
