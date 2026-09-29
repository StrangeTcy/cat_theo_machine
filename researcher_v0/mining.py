"""Researcher-v0 G4 MINING condition.

The search condition is intentionally the G3 search with the same 34
canonical tasks, budgets, one worker, and no pruning.  After each fixed batch
of completed attempts, INV-0 observes legal transitions reconstructed from the
run journal's attempted rows.  Trace survival emits
``CandidateInvariant(observer, ruleset_version)``; a differing reading retains
a concrete ``BrokenOn`` witness.  The independent checker in
``mining_checker`` then recomputes every exact rule body.  Proved invariants
are archived for G5 but are never passed back to the G4 search.
"""

from __future__ import annotations

from .. import invariance as I
from .. import machine as M
from . import checker as C
from . import laboratory as L
from . import mining_checker as MC
from . import ruleset_digest as RD
from . import task_generation as G
from . import token_domain as D
from .chains import ChainAppend, IsEmptyTerm




class ObserverSpec(M.Edge):
    def __init__(self, display, pattern):
        self.result = M.Pair(display, M.Pair(pattern, M.EmptyList))
        super().__init__(
            inputs=M.Pair(display, M.Pair(pattern, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class ObserverDisplay(M.Edge):
    def __init__(self, observer_spec):
        self.result = D.HeadAt(observer_spec, 0)()
        super().__init__(inputs=M.Pair(observer_spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObserverPattern(M.Edge):
    def __init__(self, observer_spec):
        self.result = D.HeadAt(observer_spec, 1)()
        super().__init__(inputs=M.Pair(observer_spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LengthObserverSpec(M.Edge):
    """Length observer: the structural pair-count fact ``Tokens(k)``."""

    def __init__(self):
        pattern = M.Pair(
            D.TokensTag()(), M.Pair(D.RuleVar("observed-length")(), M.EmptyList)
        )
        self.result = ObserverSpec(M.Char("Length"), I.Phi(pattern)())()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ParityLengthObserverSpec(M.Edge):
    """Parity(Length): the carried and transition-checked ``Parity(p)`` fact."""

    def __init__(self):
        pattern = M.Pair(
            D.ParityTag()(), M.Pair(D.RuleVar("observed-parity")(), M.EmptyList)
        )
        self.result = ObserverSpec(M.Char("Parity(Length)"), I.Phi(pattern)())()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ObserverGrammar(M.Edge):
    def __init__(self):
        self.result = M.Pair(
            LengthObserverSpec()(), M.Pair(ParityLengthObserverSpec()(), M.EmptyList)
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result




class ObservedTransition(M.Edge):
    """Source task, ruleset, exact rule, and a legal before/after transition."""

    def __init__(
        self, source_task, ruleset_digest, rule_digest, rule_display, before, after
    ):
        self.result = M.Pair(
            source_task,
            M.Pair(
                ruleset_digest,
                M.Pair(
                    rule_digest,
                    M.Pair(
                        rule_display,
                        M.Pair(before, M.Pair(after, M.EmptyList)),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(before, M.Pair(after, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TransitionSourceTask(M.Edge):
    def __init__(self, transition):
        self.result = D.HeadAt(transition, 0)()
        super().__init__(inputs=M.Pair(transition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TransitionRulesetDigest(M.Edge):
    def __init__(self, transition):
        self.result = D.HeadAt(transition, 1)()
        super().__init__(inputs=M.Pair(transition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TransitionRuleDigest(M.Edge):
    def __init__(self, transition):
        self.result = D.HeadAt(transition, 2)()
        super().__init__(inputs=M.Pair(transition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TransitionRuleDisplay(M.Edge):
    def __init__(self, transition):
        self.result = D.HeadAt(transition, 3)()
        super().__init__(inputs=M.Pair(transition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TransitionBefore(M.Edge):
    def __init__(self, transition):
        self.result = D.HeadAt(transition, 4)()
        super().__init__(inputs=M.Pair(transition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TransitionAfter(M.Edge):
    def __init__(self, transition):
        self.result = D.HeadAt(transition, 5)()
        super().__init__(inputs=M.Pair(transition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TransitionsAtState(M.Edge):
    def __init__(self, task_id, digest, specs, state):
        self.result = self._walk(task_id, digest, specs, state, M.EmptyList)
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def _walk(self, task_id, digest, specs, state, built):
        if IsEmptyTerm(specs)() is M.truth_value:
            return built
        spec = M.Head(specs)()
        move = D.ApplyRule(spec, state)()
        if D.IsAppliedOutcome(move)() is M.truth_value:
            built = ChainAppend(
                built,
                ObservedTransition(
                    task_id,
                    digest,
                    D.RuleFingerprintOfSpec(spec)(),
                    D.RuleDisplay(spec)(),
                    state,
                    D.OutcomeAfter(move)(),
                )(),
            )()
        return self._walk(task_id, digest, M.Tail(specs)(), state, built)

    def __call__(self):
        return self.result


class ObservedTransitions(M.Edge):
    """Legal outgoing transitions from each completed task's start and goal.

    Both endpoints belong to the delivered journal row and every successor is
    recomputed with the G1 exact-rule applier.  Scope-break rows have no new
    task binding and therefore add no fabricated trace.
    """

    def __init__(self, attempts):
        self.result = self._walk(attempts, M.EmptyList)
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _walk(self, attempts, built):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return built
        attempt = M.Head(attempts)()
        binding = L.AttemptBindingShell(attempt)()
        if IsEmptyTerm(binding)() is M.false_value:
            row = L.AttemptRow(attempt)()
            record = G.RowRecord(row)()
            specs = G.TaskSpecs(record)()
            digest = D.RulesetVersionOfSpecs(specs)()
            task_id = M.Char(L.AttemptTaskIdText(attempt)())
            built = self._append(
                built,
                TransitionsAtState(
                    task_id, digest, specs, G.TaskStart(record)()
                )(),
            )
            built = self._append(
                built,
                TransitionsAtState(
                    task_id, digest, specs, G.TaskGoal(record)()
                )(),
            )
        return self._walk(M.Tail(attempts)(), built)

    def _append(self, built, additions):
        if IsEmptyTerm(additions)() is M.truth_value:
            return built
        return self._append(
            ChainAppend(built, M.Head(additions)())(), M.Tail(additions)()
        )

    def __call__(self):
        return self.result




class TraceSurvivedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("TRACE_SURVIVED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class TraceBrokenTag(M.Edge):
    def __init__(self):
        self.result = M.Char("TRACE_BROKEN")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class TraceUnsupportedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("TRACE_UNSUPPORTED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class CounterexampleId(M.Edge):
    def __init__(self, observer_spec, digest, transition, pre, post):
        self.result = M.Char(
            "broken-"
            + ObserverDisplay(observer_spec)()()
            + "-"
            + digest()
            + "-"
            + TransitionRuleDigest(transition)()()
            + "-"
            + TransitionSourceTask(transition)()()
        )
        super().__init__(inputs=M.Pair(transition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BrokenOn(M.Edge):
    """Concrete transition on which an observer has two differing readings."""

    def __init__(self, observer_spec, digest, transition, pre, post):
        identifier = CounterexampleId(observer_spec, digest, transition, pre, post)()
        self.result = M.Pair(
            identifier,
            M.Pair(
                observer_spec,
                M.Pair(
                    digest,
                    M.Pair(
                        transition,
                        M.Pair(
                            pre,
                            M.Pair(
                                post,
                                M.Pair(
                                    M.Char("both readings are present and differ"),
                                    M.EmptyList,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(transition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BrokenId(M.Edge):
    def __init__(self, broken):
        self.result = D.HeadAt(broken, 0)()
        super().__init__(inputs=M.Pair(broken, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BrokenObserverSpec(M.Edge):
    def __init__(self, broken):
        self.result = D.HeadAt(broken, 1)()
        super().__init__(inputs=M.Pair(broken, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BrokenDigest(M.Edge):
    def __init__(self, broken):
        self.result = D.HeadAt(broken, 2)()
        super().__init__(inputs=M.Pair(broken, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BrokenTransition(M.Edge):
    def __init__(self, broken):
        self.result = D.HeadAt(broken, 3)()
        super().__init__(inputs=M.Pair(broken, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BrokenPreReading(M.Edge):
    def __init__(self, broken):
        self.result = D.HeadAt(broken, 4)()
        super().__init__(inputs=M.Pair(broken, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BrokenPostReading(M.Edge):
    def __init__(self, broken):
        self.result = D.HeadAt(broken, 5)()
        super().__init__(inputs=M.Pair(broken, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TraceAssessment(M.Edge):
    def __init__(self, status, transition_count, broken_shell, reason):
        self.result = M.Pair(
            status,
            M.Pair(
                transition_count,
                M.Pair(broken_shell, M.Pair(M.Char(reason), M.EmptyList)),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class TraceStatus(M.Edge):
    def __init__(self, assessment):
        self.result = D.HeadAt(assessment, 0)()
        super().__init__(inputs=M.Pair(assessment, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TraceCountTerm(M.Edge):
    def __init__(self, assessment):
        self.result = D.HeadAt(assessment, 1)()
        super().__init__(inputs=M.Pair(assessment, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TraceCount(M.Edge):
    def __init__(self, assessment):
        self.result = D.StructuralCount(TraceCountTerm(assessment)())()
        super().__init__(inputs=M.Pair(assessment, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TraceBrokenShell(M.Edge):
    def __init__(self, assessment):
        self.result = D.HeadAt(assessment, 2)()
        super().__init__(inputs=M.Pair(assessment, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TraceReason(M.Edge):
    def __init__(self, assessment):
        self.result = D.HeadAt(assessment, 3)()
        super().__init__(inputs=M.Pair(assessment, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AssessTrace(M.Edge):
    def __init__(self, observer_spec, digest, transitions):
        scanned = self._walk(
            observer_spec,
            ObserverPattern(observer_spec)(),
            digest,
            transitions,
            D.PeanoZero()(),
            M.EmptyList,
            M.false_value,
            M.false_value,
        )
        count = D.HeadAt(scanned, 0)()
        broken_shell = D.HeadAt(scanned, 1)()
        missing = D.HeadAt(scanned, 2)()
        seen = D.HeadAt(scanned, 3)()
        if IsEmptyTerm(broken_shell)() is M.false_value:
            self.result = TraceAssessment(
                TraceBrokenTag()(),
                count,
                broken_shell,
                "a retained BrokenOn transition has present, differing readings",
            )()
        elif M.IdentityCompare(seen, M.false_value)() is M.truth_value:
            self.result = TraceAssessment(
                TraceUnsupportedTag()(),
                count,
                M.EmptyList,
                "no observed transition belongs to this exact ruleset",
            )()
        elif M.IdentityCompare(missing, M.truth_value)() is M.truth_value:
            self.result = TraceAssessment(
                TraceUnsupportedTag()(),
                count,
                M.EmptyList,
                "an observed transition lacks a required observer reading",
            )()
        else:
            self.result = TraceAssessment(
                TraceSurvivedTag()(),
                count,
                M.EmptyList,
                "observer survived every observed transition",
            )()
        super().__init__(inputs=M.Pair(observer_spec, M.EmptyList), results=self.result)

    def _walk(
        self,
        observer_spec,
        observer,
        digest,
        transitions,
        count,
        broken_shell,
        missing,
        seen,
    ):
        if IsEmptyTerm(transitions)() is M.truth_value:
            return M.Pair(
                count,
                M.Pair(
                    broken_shell,
                    M.Pair(missing, M.Pair(seen, M.EmptyList)),
                ),
            )
        transition = M.Head(transitions)()
        if M.Compare(TransitionRulesetDigest(transition)(), digest)() is M.truth_value:
            count = D.PeanoSucc(count)()
            seen = M.truth_value
            pre = I.PhiReading(TransitionBefore(transition)(), observer)()
            post = I.PhiReading(TransitionAfter(transition)(), observer)()
            if IsEmptyTerm(pre)() is M.truth_value:
                missing = M.truth_value
            elif IsEmptyTerm(post)() is M.truth_value:
                missing = M.truth_value
            elif M.Compare(pre, post)() is M.false_value:
                if IsEmptyTerm(broken_shell)() is M.truth_value:
                    broken_shell = M.Pair(
                        BrokenOn(
                            observer_spec, digest, transition, pre, post
                        )(),
                        M.EmptyList,
                    )
        return self._walk(
            observer_spec,
            observer,
            digest,
            M.Tail(transitions)(),
            count,
            broken_shell,
            missing,
            seen,
        )

    def __call__(self):
        return self.result


class CandidateId(M.Edge):
    def __init__(self, observer_spec, digest):
        self.result = M.Char(
            "candidate-" + ObserverDisplay(observer_spec)()() + "-" + digest()
        )
        super().__init__(inputs=M.Pair(observer_spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateInvariant(M.Edge):
    """CandidateInvariant(observer, ruleset_version), with trace provenance."""

    def __init__(
        self,
        observer_spec,
        digest,
        first_seen_seq,
        trace_count,
        source_task,
        checker_verdict,
    ):
        self.result = M.Pair(
            CandidateId(observer_spec, digest)(),
            M.Pair(
                observer_spec,
                M.Pair(
                    digest,
                    M.Pair(
                        M.Pair(first_seen_seq, M.EmptyList),
                        M.Pair(
                            trace_count,
                            M.Pair(source_task, M.Pair(checker_verdict, M.EmptyList)),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(observer_spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateIdOf(M.Edge):
    def __init__(self, candidate):
        self.result = D.HeadAt(candidate, 0)()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateObserverSpec(M.Edge):
    def __init__(self, candidate):
        self.result = D.HeadAt(candidate, 1)()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateDigest(M.Edge):
    def __init__(self, candidate):
        self.result = D.HeadAt(candidate, 2)()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateFirstSeen(M.Edge):
    def __init__(self, candidate):
        self.result = M.Head(D.HeadAt(candidate, 3)())()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateTraceCountTerm(M.Edge):
    def __init__(self, candidate):
        self.result = D.HeadAt(candidate, 4)()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateTraceCount(M.Edge):
    def __init__(self, candidate):
        self.result = D.StructuralCount(CandidateTraceCountTerm(candidate)())()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateSourceTask(M.Edge):
    def __init__(self, candidate):
        self.result = D.HeadAt(candidate, 5)()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateCheckerVerdict(M.Edge):
    def __init__(self, candidate):
        self.result = D.HeadAt(candidate, 6)()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result




class RulesetEntry(M.Edge):
    def __init__(self, digest, specs, source_task):
        self.result = M.Pair(digest, M.Pair(specs, M.Pair(source_task, M.EmptyList)))
        super().__init__(inputs=M.Pair(specs, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntryDigest(M.Edge):
    def __init__(self, entry):
        self.result = D.HeadAt(entry, 0)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntrySpecs(M.Edge):
    def __init__(self, entry):
        self.result = D.HeadAt(entry, 1)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntrySourceTask(M.Edge):
    def __init__(self, entry):
        self.result = D.HeadAt(entry, 2)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntriesContainDigest(M.Edge):
    def __init__(self, entries, digest):
        self.result = self._scan(entries, digest)
        super().__init__(inputs=M.Pair(entries, M.EmptyList), results=self.result)

    def _scan(self, entries, digest):
        if IsEmptyTerm(entries)() is M.truth_value:
            return M.false_value
        if M.Compare(EntryDigest(M.Head(entries)())(), digest)() is M.truth_value:
            return M.truth_value
        return self._scan(M.Tail(entries)(), digest)

    def __call__(self):
        return self.result


class RulesetEntries(M.Edge):
    """One exact spec chain per ruleset version seen in completed attempts."""

    def __init__(self, attempts):
        self.result = self._walk(attempts, M.EmptyList)
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _walk(self, attempts, built):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return built
        attempt = M.Head(attempts)()
        binding = L.AttemptBindingShell(attempt)()
        if IsEmptyTerm(binding)() is M.false_value:
            record = G.RowRecord(L.AttemptRow(attempt)())()
            specs = G.TaskSpecs(record)()
            digest = D.RulesetVersionOfSpecs(specs)()
            if EntriesContainDigest(built, digest)() is M.false_value:
                built = ChainAppend(
                    built,
                    RulesetEntry(
                        digest, specs, M.Char(L.AttemptTaskIdText(attempt)())
                    )(),
                )()
        return self._walk(M.Tail(attempts)(), built)

    def __call__(self):
        return self.result


class AssessmentKey(M.Edge):
    def __init__(self, observer_spec, digest):
        self.result = M.Pair(
            ObserverDisplay(observer_spec)(), M.Pair(digest, M.EmptyList)
        )
        super().__init__(inputs=M.Pair(observer_spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AssessedContains(M.Edge):
    def __init__(self, assessed, key):
        self.result = self._scan(assessed, key)
        super().__init__(inputs=M.Pair(assessed, M.EmptyList), results=self.result)

    def _scan(self, assessed, key):
        if IsEmptyTerm(assessed)() is M.truth_value:
            return M.false_value
        if M.Compare(M.Head(assessed)(), key)() is M.truth_value:
            return M.truth_value
        return self._scan(M.Tail(assessed)(), key)

    def __call__(self):
        return self.result


class ProvedInvariant(M.Edge):
    def __init__(self, candidate, certificate, replay):
        self.result = M.Pair(
            candidate, M.Pair(certificate, M.Pair(replay, M.EmptyList))
        )
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProvedCandidate(M.Edge):
    def __init__(self, proved):
        self.result = D.HeadAt(proved, 0)()
        super().__init__(inputs=M.Pair(proved, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProvedCertificate(M.Edge):
    def __init__(self, proved):
        self.result = D.HeadAt(proved, 1)()
        super().__init__(inputs=M.Pair(proved, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProvedReplay(M.Edge):
    def __init__(self, proved):
        self.result = D.HeadAt(proved, 2)()
        super().__init__(inputs=M.Pair(proved, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutationId(M.Edge):
    def __init__(self, observer_spec, digest, trace):
        shell = TraceBrokenShell(trace)()
        if IsEmptyTerm(shell)() is M.false_value:
            self.result = BrokenId(M.Head(shell)())()
        else:
            self.result = M.Char(
                "assessment-"
                + ObserverDisplay(observer_spec)()()
                + "-"
                + digest()
                + "-"
                + TraceStatus(trace)()()
            )
        super().__init__(inputs=M.Pair(observer_spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutedCandidate(M.Edge):
    def __init__(
        self, observer_spec, digest, first_seen_seq, source_task, trace, checker_verdict
    ):
        self.result = M.Pair(
            RefutationId(observer_spec, digest, trace)(),
            M.Pair(
                observer_spec,
                M.Pair(
                    digest,
                    M.Pair(
                        M.Pair(first_seen_seq, M.EmptyList),
                        M.Pair(
                            source_task,
                            M.Pair(trace, M.Pair(checker_verdict, M.EmptyList)),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(observer_spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutationIdOf(M.Edge):
    def __init__(self, refutation):
        self.result = D.HeadAt(refutation, 0)()
        super().__init__(inputs=M.Pair(refutation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutationObserverSpec(M.Edge):
    def __init__(self, refutation):
        self.result = D.HeadAt(refutation, 1)()
        super().__init__(inputs=M.Pair(refutation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutationDigest(M.Edge):
    def __init__(self, refutation):
        self.result = D.HeadAt(refutation, 2)()
        super().__init__(inputs=M.Pair(refutation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutationFirstSeen(M.Edge):
    def __init__(self, refutation):
        self.result = M.Head(D.HeadAt(refutation, 3)())()
        super().__init__(inputs=M.Pair(refutation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutationSourceTask(M.Edge):
    def __init__(self, refutation):
        self.result = D.HeadAt(refutation, 4)()
        super().__init__(inputs=M.Pair(refutation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutationTrace(M.Edge):
    def __init__(self, refutation):
        self.result = D.HeadAt(refutation, 5)()
        super().__init__(inputs=M.Pair(refutation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutationCheckerVerdict(M.Edge):
    def __init__(self, refutation):
        self.result = D.HeadAt(refutation, 6)()
        super().__init__(inputs=M.Pair(refutation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalResult(M.Edge):
    def __init__(self, candidate_shell, proved_shell, refuted_shell):
        self.result = M.Pair(
            candidate_shell, M.Pair(proved_shell, M.Pair(refuted_shell, M.EmptyList))
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class AssessProposal(M.Edge):
    """Trace-mine one grammar observer, then independently check every rule."""

    def __init__(self, observer_spec, entry, transitions, sweep_seq):
        digest = EntryDigest(entry)()
        observer = ObserverPattern(observer_spec)()
        trace = AssessTrace(observer_spec, digest, transitions)()
        checked = MC.CheckObserverPreservation(observer, EntrySpecs(entry)())()
        if M.Compare(TraceStatus(trace)(), TraceSurvivedTag()())() is M.truth_value:
            candidate = CandidateInvariant(
                observer_spec,
                digest,
                sweep_seq,
                TraceCountTerm(trace)(),
                EntrySourceTask(entry)(),
                checked,
            )()
            candidate_shell = M.Pair(candidate, M.EmptyList)
            if M.Compare(MC.VerdictStatus(checked)(), MC.ProvedTag()())() is M.truth_value:
                certificate = M.Head(MC.VerdictCertificateShell(checked)())()
                replay = MC.ReplayInvariantCertificate(
                    certificate, observer, EntrySpecs(entry)()
                )()
                proved_shell = M.Pair(
                    ProvedInvariant(candidate, certificate, replay)(), M.EmptyList
                )
                refuted_shell = M.EmptyList
            else:
                proved_shell = M.EmptyList
                refuted_shell = M.Pair(
                    RefutedCandidate(
                        observer_spec,
                        digest,
                        sweep_seq,
                        EntrySourceTask(entry)(),
                        trace,
                        checked,
                    )(),
                    M.EmptyList,
                )
        else:
            candidate_shell = M.EmptyList
            proved_shell = M.EmptyList
            refuted_shell = M.Pair(
                RefutedCandidate(
                    observer_spec,
                    digest,
                    sweep_seq,
                    EntrySourceTask(entry)(),
                    trace,
                    checked,
                )(),
                M.EmptyList,
            )
        self.result = ProposalResult(
            candidate_shell, proved_shell, refuted_shell
        )()
        super().__init__(inputs=M.Pair(observer_spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result




class SweepResult(M.Edge):
    def __init__(self, assessed, candidates, proved, refuted):
        self.result = M.Pair(
            assessed,
            M.Pair(candidates, M.Pair(proved, M.Pair(refuted, M.EmptyList))),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SweepAssessed(M.Edge):
    def __init__(self, sweep):
        self.result = D.HeadAt(sweep, 0)()
        super().__init__(inputs=M.Pair(sweep, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SweepCandidates(M.Edge):
    def __init__(self, sweep):
        self.result = D.HeadAt(sweep, 1)()
        super().__init__(inputs=M.Pair(sweep, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SweepProved(M.Edge):
    def __init__(self, sweep):
        self.result = D.HeadAt(sweep, 2)()
        super().__init__(inputs=M.Pair(sweep, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SweepRefuted(M.Edge):
    def __init__(self, sweep):
        self.result = D.HeadAt(sweep, 3)()
        super().__init__(inputs=M.Pair(sweep, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MiningSweep(M.Edge):
    def __init__(
        self, attempts, sweep_seq, assessed, candidates, proved, refuted
    ):
        transitions = ObservedTransitions(attempts)()
        entries = RulesetEntries(attempts)()
        self.result = self._entries(
            entries,
            ObserverGrammar()(),
            transitions,
            sweep_seq,
            assessed,
            candidates,
            proved,
            refuted,
        )
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _entries(
        self,
        entries,
        grammar,
        transitions,
        sweep_seq,
        assessed,
        candidates,
        proved,
        refuted,
    ):
        if IsEmptyTerm(entries)() is M.truth_value:
            return SweepResult(assessed, candidates, proved, refuted)()
        swept = self._observers(
            grammar,
            M.Head(entries)(),
            transitions,
            sweep_seq,
            assessed,
            candidates,
            proved,
            refuted,
        )
        return self._entries(
            M.Tail(entries)(),
            grammar,
            transitions,
            sweep_seq,
            SweepAssessed(swept)(),
            SweepCandidates(swept)(),
            SweepProved(swept)(),
            SweepRefuted(swept)(),
        )

    def _observers(
        self,
        observers,
        entry,
        transitions,
        sweep_seq,
        assessed,
        candidates,
        proved,
        refuted,
    ):
        if IsEmptyTerm(observers)() is M.truth_value:
            return SweepResult(assessed, candidates, proved, refuted)()
        observer_spec = M.Head(observers)()
        key = AssessmentKey(observer_spec, EntryDigest(entry)())()
        if AssessedContains(assessed, key)() is M.false_value:
            proposal = AssessProposal(observer_spec, entry, transitions, sweep_seq)()
            assessed = ChainAppend(assessed, key)()
            candidate_shell = D.HeadAt(proposal, 0)()
            proved_shell = D.HeadAt(proposal, 1)()
            refuted_shell = D.HeadAt(proposal, 2)()
            if IsEmptyTerm(candidate_shell)() is M.false_value:
                candidates = ChainAppend(candidates, M.Head(candidate_shell)())()
            if IsEmptyTerm(proved_shell)() is M.false_value:
                proved = ChainAppend(proved, M.Head(proved_shell)())()
            if IsEmptyTerm(refuted_shell)() is M.false_value:
                refuted = ChainAppend(refuted, M.Head(refuted_shell)())()
        return self._observers(
            M.Tail(observers)(),
            entry,
            transitions,
            sweep_seq,
            assessed,
            candidates,
            proved,
            refuted,
        )

    def __call__(self):
        return self.result


class MiningRunRecord(M.Edge):
    def __init__(
        self, attempts, path_archive, candidates, proved, refuted, sweep_seqs
    ):
        self.result = M.Pair(
            attempts,
            M.Pair(
                path_archive,
                M.Pair(
                    candidates,
                    M.Pair(proved, M.Pair(refuted, M.Pair(sweep_seqs, M.EmptyList))),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RunAttempts(M.Edge):
    def __init__(self, run):
        self.result = D.HeadAt(run, 0)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RunPathArchive(M.Edge):
    def __init__(self, run):
        self.result = D.HeadAt(run, 1)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RunCandidates(M.Edge):
    def __init__(self, run):
        self.result = D.HeadAt(run, 2)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RunProved(M.Edge):
    def __init__(self, run):
        self.result = D.HeadAt(run, 3)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RunRefuted(M.Edge):
    def __init__(self, run):
        self.result = D.HeadAt(run, 4)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RunSweepSeqs(M.Edge):
    def __init__(self, run):
        self.result = D.HeadAt(run, 5)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MiningCadence(M.Edge):
    """Five structural ticks: the declared fixed INV-0 cadence."""

    def __init__(self):
        tick = M.Char("completed-task")
        self.result = M.Pair(
            tick,
            M.Pair(tick, M.Pair(tick, M.Pair(tick, M.Pair(tick, M.EmptyList)))),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class MiningRun(M.Edge):
    """Attempt tasks in order and run INV-0 after every five completions.

    Sequence and cadence are structural. Only the G3 path archive is supplied
    to each attempt; candidate and proved archives remain separate, so they
    cannot prune or change any G4 search outcome.
    """

    def __init__(self, representatives, budget, wall_ms):
        self.result = self._walk(
            representatives,
            D.PeanoSucc(D.PeanoZero()())(),
            MiningCadence()(),
            M.EmptyList,
            M.EmptyList,
            M.EmptyList,
            M.EmptyList,
            M.EmptyList,
            M.EmptyList,
            M.EmptyList,
            M.truth_value,
            budget,
            wall_ms,
        )
        super().__init__(inputs=M.Pair(representatives, M.EmptyList), results=self.result)

    def _walk(
        self,
        remaining,
        sequence,
        cadence,
        attempts,
        path_archive,
        assessed,
        candidates,
        proved,
        refuted,
        sweep_seqs,
        swept_last,
        budget,
        wall_ms,
    ):
        if IsEmptyTerm(remaining)() is M.truth_value:
            if IsEmptyTerm(attempts)() is M.false_value:
                if M.IdentityCompare(swept_last, M.false_value)() is M.truth_value:
                    sweep_seq = L.LastSeq(attempts)()
                    swept = MiningSweep(
                        attempts,
                        sweep_seq,
                        assessed,
                        candidates,
                        proved,
                        refuted,
                    )()
                    candidates = SweepCandidates(swept)()
                    proved = SweepProved(swept)()
                    refuted = SweepRefuted(swept)()
                    sweep_seqs = ChainAppend(
                        sweep_seqs, M.Pair(sweep_seq, M.EmptyList)
                    )()
            return MiningRunRecord(
                attempts, path_archive, candidates, proved, refuted, sweep_seqs
            )()
        attempt = L.BaselineAttempt(
            D.StructuralCount(sequence)(),
            M.Head(remaining)(),
            path_archive,
            budget,
            wall_ms,
        )()
        certificate_shell = L.AttemptCertificateShell(attempt)()
        if IsEmptyTerm(certificate_shell)() is M.false_value:
            certificate = M.Head(M.Head(certificate_shell)())()
            path_archive = ChainAppend(
                path_archive,
                C.ArchiveEntry(
                    C.CertificateId(certificate)(),
                    certificate,
                    M.Char(L.AttemptTaskIdText(attempt)()),
                )(),
            )()
        attempts = ChainAppend(attempts, attempt)()
        cadence = M.Tail(cadence)()
        swept_last = M.false_value
        if IsEmptyTerm(cadence)() is M.truth_value:
            sweep_seq = L.AttemptSeq(attempt)()
            swept = MiningSweep(
                attempts, sweep_seq, assessed, candidates, proved, refuted
            )()
            assessed = SweepAssessed(swept)()
            candidates = SweepCandidates(swept)()
            proved = SweepProved(swept)()
            refuted = SweepRefuted(swept)()
            sweep_seqs = ChainAppend(
                sweep_seqs, M.Pair(sweep_seq, M.EmptyList)
            )()
            cadence = MiningCadence()()
            swept_last = M.truth_value
        return self._walk(
            M.Tail(remaining)(),
            D.PeanoSucc(sequence)(),
            cadence,
            attempts,
            path_archive,
            assessed,
            candidates,
            proved,
            refuted,
            sweep_seqs,
            swept_last,
            budget,
            wall_ms,
        )

    def __call__(self):
        return self.result




class TermText(M.Edge):
    def __init__(self, term):
        self.result = M.Head(RD.TermText(term, M.EmptyList)())()()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ClassificationText(M.Edge):
    def __init__(self, status):
        if M.Compare(status, MC.ProvedTag()())() is M.truth_value:
            self.result = "proved"
        elif M.Compare(status, MC.RefutedTag()())() is M.truth_value:
            self.result = "refuted"
        else:
            self.result = "unsupported"
        super().__init__(inputs=M.Pair(status, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ChainCount(M.Edge):
    def __init__(self, chain):
        counted = self._count(chain, D.PeanoZero()())
        self.result = D.StructuralCount(counted)()
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def _count(self, chain, count):
        if IsEmptyTerm(chain)() is M.truth_value:
            return count
        return self._count(M.Tail(chain)(), D.PeanoSucc(count)())

    def __call__(self):
        return self.result


class ReportingCountEquals(M.Edge):
    def __init__(self, left, right):
        self.result = M.Compare(M.Char(str(left)), M.Char(str(right)))()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result



class EvidenceJson(M.Edge):
    def __init__(self, evidence):
        self.result = "[" + self._lines(evidence) + "]"
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=self.result)

    def _lines(self, evidence):
        if IsEmptyTerm(evidence)() is M.truth_value:
            return ""
        step = M.Head(evidence)()
        item = (
            '{"rule_digest":"'
            + MC.StepRuleDigest(step)()()
            + '","rule":"'
            + L.JsonSafeText(MC.StepRuleDisplay(step)()())()
            + '","status":"'
            + MC.StepStatus(step)()()
            + '","pre":"'
            + L.JsonSafeText(TermText(MC.StepPreReading(step)())())()
            + '","post":"'
            + L.JsonSafeText(TermText(MC.StepPostReading(step)())())()
            + '","reason":"'
            + L.JsonSafeText(MC.StepReason(step)()())()
            + '"}'
        )
        if IsEmptyTerm(M.Tail(evidence)())() is M.truth_value:
            return item
        return item + "," + self._lines(M.Tail(evidence)())

    def __call__(self):
        return self.result


class CandidateJson(M.Edge):
    def __init__(self, candidate):
        checked = CandidateCheckerVerdict(candidate)()
        self.result = (
            '{"record":"CandidateInvariant","candidate_id":"'
            + CandidateIdOf(candidate)()()
            + '","observer":"'
            + ObserverDisplay(CandidateObserverSpec(candidate)())()()
            + '","ruleset_version":"'
            + CandidateDigest(candidate)()()
            + '","first_seen_after_tasks":'
            + str(CandidateFirstSeen(candidate)())
            + ',"observed_transitions":'
            + str(CandidateTraceCount(candidate)())
            + ',"source_task":"'
            + CandidateSourceTask(candidate)()()
            + '","classification":"'
            + ClassificationText(MC.VerdictStatus(checked)())()
            + '","checker_reason":"'
            + L.JsonSafeText(MC.VerdictReason(checked)()())()
            + '"}'
        )
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidatesText(M.Edge):
    def __init__(self, candidates):
        self.result = self._lines(candidates)
        super().__init__(inputs=M.Pair(candidates, M.EmptyList), results=self.result)

    def _lines(self, candidates):
        if IsEmptyTerm(candidates)() is M.truth_value:
            return ""
        return (
            CandidateJson(M.Head(candidates)())()
            + "\n"
            + self._lines(M.Tail(candidates)())
        )

    def __call__(self):
        return self.result


class ProvedJson(M.Edge):
    def __init__(self, proved):
        candidate = ProvedCandidate(proved)()
        certificate = ProvedCertificate(proved)()
        replay = ProvedReplay(proved)()
        evidence = C.CertificateEvidence(certificate)()
        self.result = (
            '{"record":"proved-invariant","certificate_id":"'
            + MC.InvariantCertificateId(certificate)()()
            + '","candidate_id":"'
            + CandidateIdOf(candidate)()()
            + '","kind":"'
            + C.CertificateKind(certificate)()()
            + '","observer":"'
            + ObserverDisplay(CandidateObserverSpec(candidate)())()()
            + '","ruleset_version":"'
            + C.CertificateDigest(certificate)()()
            + '","checker_version":"'
            + C.CertificateVersion(certificate)()()
            + '","source_task":"'
            + CandidateSourceTask(candidate)()()
            + '","rules_checked":'
            + str(MC.EvidenceCount(evidence)())
            + ',"classification":"proved","preservation":'
            + EvidenceJson(evidence)()
            + ',"replay":"'
            + C.VerdictTag(replay)()()
            + '","replayed_rules":'
            + str(C.VerdictSteps(replay)())
            + ',"replay_reason":"'
            + L.JsonSafeText(C.VerdictReason(replay)()())()
            + '"}'
        )
        super().__init__(inputs=M.Pair(proved, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProvedText(M.Edge):
    def __init__(self, proved):
        self.result = self._lines(proved)
        super().__init__(inputs=M.Pair(proved, M.EmptyList), results=self.result)

    def _lines(self, proved):
        if IsEmptyTerm(proved)() is M.truth_value:
            return ""
        return ProvedJson(M.Head(proved)())() + "\n" + self._lines(M.Tail(proved)())

    def __call__(self):
        return self.result


class RefutationClassification(M.Edge):
    def __init__(self, refutation):
        trace = RefutationTrace(refutation)()
        checked = RefutationCheckerVerdict(refutation)()
        if M.Compare(TraceStatus(trace)(), TraceBrokenTag()())() is M.truth_value:
            self.result = "refuted"
        elif M.Compare(MC.VerdictStatus(checked)(), MC.RefutedTag()())() is M.truth_value:
            self.result = "refuted"
        else:
            self.result = "unsupported"
        super().__init__(inputs=M.Pair(refutation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutedJson(M.Edge):
    def __init__(self, refutation):
        trace = RefutationTrace(refutation)()
        checked = RefutationCheckerVerdict(refutation)()
        shell = TraceBrokenShell(trace)()
        if IsEmptyTerm(shell)() is M.truth_value:
            counterexample_id = ""
            source_task = RefutationSourceTask(refutation)()()
            rule_digest = ""
            rule_display = ""
            before = ""
            after = ""
            pre = ""
            post = ""
        else:
            broken = M.Head(shell)()
            transition = BrokenTransition(broken)()
            counterexample_id = BrokenId(broken)()()
            source_task = TransitionSourceTask(transition)()()
            rule_digest = TransitionRuleDigest(transition)()()
            rule_display = TransitionRuleDisplay(transition)()()
            before = C.StateText(TransitionBefore(transition)())()()
            after = C.StateText(TransitionAfter(transition)())()()
            pre = TermText(BrokenPreReading(broken)())()
            post = TermText(BrokenPostReading(broken)())()
        self.result = (
            '{"record":"proposal-classification","refutation_id":"'
            + RefutationIdOf(refutation)()()
            + '","observer":"'
            + ObserverDisplay(RefutationObserverSpec(refutation)())()()
            + '","ruleset_version":"'
            + RefutationDigest(refutation)()()
            + '","first_seen_after_tasks":'
            + str(RefutationFirstSeen(refutation)())
            + ',"classification":"'
            + RefutationClassification(refutation)()
            + '","trace_status":"'
            + TraceStatus(trace)()()
            + '","trace_reason":"'
            + L.JsonSafeText(TraceReason(trace)()())()
            + '","counterexample_id":"'
            + counterexample_id
            + '","source_task":"'
            + source_task
            + '","rule_digest":"'
            + rule_digest
            + '","rule":"'
            + L.JsonSafeText(rule_display)()
            + '","before":"'
            + L.JsonSafeText(before)()
            + '","after":"'
            + L.JsonSafeText(after)()
            + '","pre_reading":"'
            + L.JsonSafeText(pre)()
            + '","post_reading":"'
            + L.JsonSafeText(post)()
            + '","checker_classification":"'
            + ClassificationText(MC.VerdictStatus(checked)())()
            + '","checker_reason":"'
            + L.JsonSafeText(MC.VerdictReason(checked)()())()
            + '","preservation":'
            + EvidenceJson(MC.VerdictEvidence(checked)())()
            + "}"
        )
        super().__init__(inputs=M.Pair(refutation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutedText(M.Edge):
    def __init__(self, refuted):
        self.result = self._lines(refuted)
        super().__init__(inputs=M.Pair(refuted, M.EmptyList), results=self.result)

    def _lines(self, refuted):
        if IsEmptyTerm(refuted)() is M.truth_value:
            return ""
        return RefutedJson(M.Head(refuted)())() + "\n" + self._lines(M.Tail(refuted)())

    def __call__(self):
        return self.result


class SweepSeqText(M.Edge):
    def __init__(self, sweep_seqs):
        self.result = self._walk(sweep_seqs)
        super().__init__(inputs=M.Pair(sweep_seqs, M.EmptyList), results=self.result)

    def _walk(self, sweep_seqs):
        if IsEmptyTerm(sweep_seqs)() is M.truth_value:
            return ""
        head = str(M.Head(M.Head(sweep_seqs)())())
        if IsEmptyTerm(M.Tail(sweep_seqs)())() is M.truth_value:
            return head
        return head + "," + self._walk(M.Tail(sweep_seqs)())

    def __call__(self):
        return self.result


class CounterexampleForTask(M.Edge):
    def __init__(self, refuted, task_id):
        self.result = self._scan(refuted, task_id)
        super().__init__(inputs=M.Pair(refuted, M.EmptyList), results=self.result)

    def _scan(self, refuted, task_id):
        if IsEmptyTerm(refuted)() is M.truth_value:
            return M.EmptyList
        shell = TraceBrokenShell(RefutationTrace(M.Head(refuted)())())()
        if IsEmptyTerm(shell)() is M.false_value:
            broken = M.Head(shell)()
            transition = BrokenTransition(broken)()
            if M.Compare(TransitionSourceTask(transition)(), task_id)() is M.truth_value:
                return M.Pair(BrokenId(broken)(), M.EmptyList)
        return self._scan(M.Tail(refuted)(), task_id)

    def __call__(self):
        return self.result


class MiningAttemptJson(M.Edge):
    def __init__(self, attempt, refuted):
        row = L.AttemptRow(attempt)()
        record = G.RowRecord(row)()
        task_id = L.AttemptTaskIdText(attempt)()
        binding_shell = L.AttemptBindingShell(attempt)()
        if IsEmptyTerm(binding_shell)() is M.truth_value:
            version = ""
            start_count = "null"
            goal_count = "null"
            start_text = ""
            goal_text = ""
        else:
            binding = M.Head(binding_shell)()
            version = D.HeadAt(binding, 0)()()
            start_count = str(M.Head(D.HeadAt(binding, 1)())())
            goal_count = str(M.Head(D.HeadAt(binding, 2)())())
            start_text = D.HeadAt(binding, 3)()()
            goal_text = D.HeadAt(binding, 4)()()
        pending_shell = L.AttemptPendingShell(attempt)()
        if IsEmptyTerm(pending_shell)() is M.truth_value:
            pending_ref = ""
            resolution_text = ""
            rejected_text = ""
            reason_text = L.AttemptReason(attempt)()()
        else:
            pending = M.Head(pending_shell)()
            pending_ref = M.Head(pending)()()
            resolution = D.HeadAt(pending, 1)()
            resolved = M.Head(resolution)()
            if IsEmptyTerm(resolved)() is M.truth_value:
                resolution_text = "unresolved"
                reason_text = (
                    "typed PENDING-REF remained unresolved during no-pruning G4 search; "
                    "proved mining archives are retained for G5 and were not supplied to this attempt"
                )
            else:
                resolution_text = "resolved:" + M.Head(resolved)()()
                reason_text = (
                    "typed PENDING-REF resolved only against the search archive; "
                    "proved mining archives were not supplied to G4 search"
                )
            rejected_text = L.RejectedText(D.HeadAt(resolution, 1)())()
        counterexample_shell = CounterexampleForTask(
            refuted, M.Char(task_id)
        )()
        if IsEmptyTerm(counterexample_shell)() is M.truth_value:
            counterexample_id = ""
        else:
            counterexample_id = M.Head(counterexample_shell)()()
        self.result = (
            '{"record": "attempt", "seq": '
            + str(L.AttemptSeq(attempt)())
            + ', "condition": "MINING", "task_id": "'
            + task_id
            + '", "canonical_id": "'
            + G.RowCanonicalId(row)()
            + '", "members": "'
            + L.AttemptMembers(attempt)()()
            + '", "kind": "'
            + G.TaskKindOf(record)()()
            + '", "ruleset_version": "'
            + version
            + '", "ruleset_recipe": "'
            + G.RowRecipe(row)()
            + '", "start_count": '
            + start_count
            + ', "goal_count": '
            + goal_count
            + ', "start": "'
            + start_text
            + '", "goal": "'
            + goal_text
            + '", "worker_id": "worker-0", "attempt_id": "MINING:'
            + task_id
            + ':1", "outcome": "'
            + L.AttemptOutcome(attempt)()()
            + '", "expansions": '
            + str(L.AttemptExpansions(attempt)())
            + ', "elapsed_ms": '
            + str(L.AttemptElapsed(attempt)())
            + ', "certificate_id": "'
            + L.AttemptCertificateIdText(attempt)()
            + '", "counterexample_id": "'
            + counterexample_id
            + '", "pending_ref": "'
            + pending_ref
            + '", "pending_resolution": "'
            + resolution_text
            + '", "rejected_by_type": "'
            + L.JsonSafeText(rejected_text)()
            + '", "reason": "'
            + L.JsonSafeText(reason_text)()
            + '"}'
        )
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MiningJournalText(M.Edge):
    def __init__(
        self,
        run,
        task_set_digest,
        delivered_rows,
        canonical_count,
        budget,
        wall_ms,
        interval,
    ):
        attempts = RunAttempts(run)()
        candidates = RunCandidates(run)()
        proved = RunProved(run)()
        refuted = RunRefuted(run)()
        sweeps = RunSweepSeqs(run)()
        totals = L.AttemptTotals(attempts)()
        header = (
            '{"record":"header","journal_layout":"researcher-v0-mining-journal/1",'
            '"attempt_layout":"researcher-v0-attempt/1","laboratory_version":"researcher-v0-laboratory/1",'
            '"checker_version":"researcher-v0-checker/1","condition":"MINING","mining":"on",'
            '"pruning":"off","task_set":"researcher_v0/tasks/tasks.jsonl","task_set_blake2b":"'
            + task_set_digest
            + '","delivered_rows":'
            + str(delivered_rows)
            + ',"canonical_tasks":'
            + str(canonical_count)
            + ',"search":"breadth-first","expansion_budget":'
            + str(budget)
            + ',"wall_clock_budget_ms_per_task":'
            + str(wall_ms)
            + ',"max_workers":1,"worker_id":"worker-0","seed":"deterministic-no-rng",'
            '"mining_interval_completed_tasks":'
            + str(interval)
            + ',"mining_sweeps":"'
            + SweepSeqText(sweeps)()
            + '","observer_grammar":"Length|Parity(Length)"}'
        )
        footer = (
            '{"record":"footer","condition":"MINING","attempts":'
            + str(L.OutcomeCountAll(attempts)())
            + ',"last_seq":'
            + str(L.LastSeq(attempts)())
            + ',"outcome_CHECKED_REACHABLE":'
            + str(L.OutcomeCount(attempts, L.CheckedReachableTag()())())
            + ',"outcome_OPEN_RESIDUAL":'
            + str(L.OutcomeCount(attempts, L.OpenResidualTag()())())
            + ',"outcome_UNSUPPORTED":'
            + str(L.OutcomeCount(attempts, L.UnsupportedTag()())())
            + ',"outcome_BUDGET_EXHAUSTED":'
            + str(L.OutcomeCount(attempts, L.BudgetExhaustedTag()())())
            + ',"outcome_EXECUTION_FAILURE":'
            + str(L.OutcomeCount(attempts, L.ExecutionFailureTag()())())
            + ',"path_certificates":'
            + str(M.Head(D.HeadAt(totals, 2)())())
            + ',"candidate_invariants":'
            + str(ChainCount(candidates)())
            + ',"proved_invariants":'
            + str(ChainCount(proved)())
            + ',"refuted_or_unsupported_proposals":'
            + str(ChainCount(refuted)())
            + ',"total_expansions":'
            + str(M.Head(D.HeadAt(totals, 0)())())
            + ',"elapsed_ms_total":'
            + str(M.Head(D.HeadAt(totals, 1)())())
            + "}"
        )
        self.result = header + "\n" + self._attempts(attempts, refuted) + footer + "\n"
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def _attempts(self, attempts, refuted):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return ""
        return (
            MiningAttemptJson(M.Head(attempts)(), refuted)()
            + "\n"
            + self._attempts(M.Tail(attempts)(), refuted)
        )

    def __call__(self):
        return self.result
