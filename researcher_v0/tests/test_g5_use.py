"""Executable acceptance tests for Researcher-v0 G5 in-run use."""

from __future__ import annotations

import os

from ... import invariance as I
from ... import machine as M
from ... import proof as P
from .. import checker as C
from .. import in_run_use as U
from .. import laboratory as L
from .. import mining as X
from .. import mining_checker as MC
from .. import task_generation as G
from .. import token_domain as D
from .. import use_checker as K
from ..chains import ChainAppend, IsEmptyTerm


class FileText(M.Edge):
    def __init__(self, path):
        handle = open(path)
        self.result = handle.read()
        handle.close()
        super().__init__(inputs=M.Pair(M.Char(path), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FindAttempt(M.Edge):
    def __init__(self, attempts, task_id):
        self.result = self._scan(attempts, task_id)
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _scan(self, attempts, task_id):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return M.EmptyList
        attempt = M.Head(attempts)()
        if M.Compare(
            M.Char(L.AttemptTaskIdText(attempt)()), task_id
        )() is M.truth_value:
            return M.Pair(attempt, M.EmptyList)
        return self._scan(M.Tail(attempts)(), task_id)

    def __call__(self):
        return self.result


class DeliveredOrderAndBudget(M.Edge):
    def __init__(self, run, representatives):
        self.result = self._walk(U.RunAttempts(run)(), representatives)
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def _walk(self, attempts, representatives):
        if IsEmptyTerm(attempts)() is M.truth_value:
            if IsEmptyTerm(representatives)() is M.truth_value:
                return M.truth_value
            return M.false_value
        if IsEmptyTerm(representatives)() is M.truth_value:
            return M.false_value
        attempt = M.Head(attempts)()
        row = M.Head(M.Head(representatives)())()
        if X.ReportingCountEquals(
            G.RowSerial(L.AttemptRow(attempt)())(), G.RowSerial(row)()
        )() is M.false_value:
            return M.false_value
        if M.Compare(
            M.Char(G.RowCanonicalId(L.AttemptRow(attempt)())()),
            M.Char(G.RowCanonicalId(row)()),
        )() is M.false_value:
            return M.false_value
        return self._walk(M.Tail(attempts)(), M.Tail(representatives)())

    def __call__(self):
        return self.result


class ExpectedPruneTasks(M.Edge):
    def __init__(self):
        self.result = M.Pair(
            M.Char("T0013"),
            M.Pair(
                M.Char("T0020"),
                M.Pair(
                    M.Char("T0023"),
                    M.Pair(
                        M.Char("T0029"),
                        M.Pair(
                            M.Char("T0030"),
                            M.Pair(
                                M.Char("T0033"),
                                M.Pair(
                                    M.Char("T0038"),
                                    M.Pair(M.Char("T0046"), M.EmptyList),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EventTasksMatch(M.Edge):
    def __init__(self, events, expected):
        self.result = self._walk(events, expected)
        super().__init__(inputs=M.Pair(events, M.EmptyList), results=self.result)

    def _walk(self, events, expected):
        if IsEmptyTerm(events)() is M.truth_value:
            if IsEmptyTerm(expected)() is M.truth_value:
                return M.truth_value
            return M.false_value
        if IsEmptyTerm(expected)() is M.truth_value:
            return M.false_value
        if M.Compare(
            U.EventTaskId(M.Head(events)())(), M.Head(expected)()
        )() is M.false_value:
            return M.false_value
        return self._walk(M.Tail(events)(), M.Tail(expected)())

    def __call__(self):
        return self.result


class EightLaterTasksPruned(M.Edge):
    def __init__(self, run):
        events = U.RunEvents(run)()
        if X.ReportingCountEquals(X.ChainCount(events)(), 8)() is M.false_value:
            self.result = M.false_value
        else:
            self.result = EventTasksMatch(events, ExpectedPruneTasks()())()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomeTotals(M.Edge):
    def __init__(self, run):
        attempts = U.RunAttempts(run)()
        totals = L.AttemptTotals(attempts)()
        expansions = M.Head(D.HeadAt(totals, 0)())()
        if X.ReportingCountEquals(L.OutcomeCountAll(attempts)(), 34)() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.CheckedReachableTag()())(), 21
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, K.CheckedUnreachableTag()())(), 8
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.BudgetExhaustedTag()())(), 3
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.UnsupportedTag()())(), 2
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.OpenResidualTag()())(), 0
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.ExecutionFailureTag()())(), 0
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = X.ReportingCountEquals(expansions, 137)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CadenceAndProofsRemainBound(M.Edge):
    def __init__(self, run):
        sweeps = X.SweepSeqText(U.RunSweepSeqs(run)())()
        if M.Compare(
            M.Char(sweeps), M.Char("5,10,15,20,25,30,34")
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            X.ChainCount(U.RunCandidates(run)())(), 3
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            X.ChainCount(U.RunProved(run)())(), 3
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = X.ReportingCountEquals(
                X.ChainCount(U.RunRefuted(run)())(), 5
            )()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FindTaskEntry(M.Edge):
    def __init__(self, representatives, task_id):
        self.result = self._scan(representatives, task_id)
        super().__init__(inputs=M.Pair(representatives, M.EmptyList), results=self.result)

    def _scan(self, representatives, task_id):
        if IsEmptyTerm(representatives)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(representatives)()
        row = M.Head(entry)()
        if M.Compare(K.TaskIdOfRow(row)(), task_id)() is M.truth_value:
            return M.Pair(entry, M.EmptyList)
        return self._scan(M.Tail(representatives)(), task_id)

    def __call__(self):
        return self.result


class EveryEventReplays(M.Edge):
    def __init__(self, events, attempts):
        self.result = self._walk(events, attempts)
        super().__init__(inputs=M.Pair(events, M.EmptyList), results=self.result)

    def _walk(self, events, attempts):
        if IsEmptyTerm(events)() is M.truth_value:
            return M.truth_value
        event = M.Head(events)()
        found = FindAttempt(attempts, U.EventTaskId(event)())()
        if IsEmptyTerm(found)() is M.truth_value:
            return M.false_value
        attempt = M.Head(found)()
        row = L.AttemptRow(attempt)()
        record = G.RowRecord(row)()
        decision = U.EventDecision(event)()
        endpoint = K.DecisionEndpointCertificate(decision)()
        invariant = K.DecisionInvariantCertificate(decision)()
        observer = K.DecisionObserver(decision)()
        invariant_replay = K.ReplayInvariantForUse(
            invariant, observer, G.TaskSpecs(record)()
        )()
        endpoint_replay = K.ReplayEndpointCertificate(
            endpoint,
            observer,
            G.TaskSpecs(record)(),
            G.TaskStart(record)(),
            G.TaskGoal(record)(),
        )()
        readings = C.ObserverReadings(
            G.TaskStart(record)(), G.TaskGoal(record)(), observer
        )()
        if C.IsReplayed(invariant_replay)() is M.false_value:
            return M.false_value
        if C.IsReplayed(endpoint_replay)() is M.false_value:
            return M.false_value
        if M.Compare(
            C.ReadingsVerdict(readings)(), C.SeparatesTag()()
        )() is M.false_value:
            return M.false_value
        if M.Compare(
            U.EventStartReading(event)(), D.HeadAt(readings, 1)()
        )() is M.false_value:
            return M.false_value
        if M.Compare(
            U.EventGoalReading(event)(), D.HeadAt(readings, 2)()
        )() is M.false_value:
            return M.false_value
        if M.Compare(
            C.CertificateDigest(endpoint)(),
            D.RulesetVersionOfSpecs(G.TaskSpecs(record)())(),
        )() is M.false_value:
            return M.false_value
        if M.Compare(
            U.EventResult(event)(), K.CheckedUnreachableTag()()
        )() is M.false_value:
            return M.false_value
        return self._walk(M.Tail(events)(), attempts)

    def __call__(self):
        return self.result


class AllPruneProofsReplay(M.Edge):
    def __init__(self, run):
        self.result = EveryEventReplays(
            U.RunEvents(run)(), U.RunAttempts(run)()
        )()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ExpansionEstimatesRecorded(M.Edge):
    def __init__(self, events):
        self.result = self._walk(events)
        super().__init__(inputs=M.Pair(events, M.EmptyList), results=self.result)

    def _walk(self, events):
        if IsEmptyTerm(events)() is M.truth_value:
            return M.truth_value
        event = M.Head(events)()
        if M.Compare(
            U.EventTaskId(event)(), M.Char("T0046")
        )() is M.truth_value:
            expected = 0
        else:
            expected = 32
        if X.ReportingCountEquals(
            U.EventExpansionEstimate(event)(), expected
        )() is M.false_value:
            return M.false_value
        return self._walk(M.Tail(events)())

    def __call__(self):
        return self.result


class ScopeMismatchExists(M.Edge):
    def __init__(self, checks, task_id, digest):
        self.result = self._scan(checks, task_id, digest)
        super().__init__(inputs=M.Pair(checks, M.EmptyList), results=self.result)

    def _scan(self, checks, task_id, digest):
        if IsEmptyTerm(checks)() is M.truth_value:
            return M.false_value
        check = M.Head(checks)()
        if M.Compare(K.ScopeCheckTaskId(check)(), task_id)() is M.truth_value:
            if M.Compare(
                K.ScopeCheckCertificateDigest(check)(), digest
            )() is M.truth_value:
                if M.Compare(
                    K.ScopeCheckTag(check)(), C.ScopeMismatchTag()()
                )() is M.truth_value:
                    return M.truth_value
        return self._scan(M.Tail(checks)(), task_id, digest)

    def __call__(self):
        return self.result


class RPlusReturnsScopeMismatch(M.Edge):
    def __init__(self, run):
        even_digest = D.RulesetVersionOfSpecs(D.REvenSpecs()())()
        self.result = ScopeMismatchExists(
            U.RunScopeChecks(run)(), M.Char("T0011"), even_digest
        )()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NoRPlusPrune(M.Edge):
    def __init__(self, events):
        self.result = self._walk(events, D.RulesetVersionOfSpecs(D.RPlusSpecs()())())
        super().__init__(inputs=M.Pair(events, M.EmptyList), results=self.result)

    def _walk(self, events, plus_digest):
        if IsEmptyTerm(events)() is M.truth_value:
            return M.truth_value
        endpoint = K.DecisionEndpointCertificate(
            U.EventDecision(M.Head(events)())()
        )()
        if M.Compare(
            C.CertificateDigest(endpoint)(), plus_digest
        )() is M.truth_value:
            return M.false_value
        return self._walk(M.Tail(events)(), plus_digest)

    def __call__(self):
        return self.result


class CandidateOnlyCannotPrune(M.Edge):
    def __init__(self, run, representatives):
        found = FindTaskEntry(representatives, M.Char("T0013"))()
        row = M.Head(M.Head(found)())()
        use = K.CheckForPrune(row, M.EmptyList)()
        if IsEmptyTerm(U.RunCandidates(run)())() is M.truth_value:
            self.result = M.false_value
        else:
            self.result = IsEmptyTerm(K.UseDecisionShell(use)())()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TraceOnlyCannotPrune(M.Edge):
    def __init__(self, run, representatives):
        found = FindTaskEntry(representatives, M.Char("T0011"))()
        row = M.Head(M.Head(found)())()
        use = K.CheckForPrune(row, M.EmptyList)()
        if IsEmptyTerm(U.RunRefuted(run)())() is M.truth_value:
            self.result = M.false_value
        else:
            self.result = IsEmptyTerm(K.UseDecisionShell(use)())()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EarlyTasksAreNotRetroactivelyPruned(M.Edge):
    def __init__(self, attempts):
        first = FindAttempt(attempts, M.Char("T0003"))()
        second = FindAttempt(attempts, M.Char("T0005"))()
        if IsEmptyTerm(first)() is M.truth_value:
            self.result = M.false_value
        elif IsEmptyTerm(second)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(
            L.AttemptOutcome(M.Head(first)())(), L.BudgetExhaustedTag()()
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.Compare(
                L.AttemptOutcome(M.Head(second)())(), L.BudgetExhaustedTag()()
            )()
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SameReadingDoesNotPrune(M.Edge):
    def __init__(self, attempts):
        found = FindAttempt(attempts, M.Char("T0014"))()
        if IsEmptyTerm(found)() is M.truth_value:
            self.result = M.false_value
        else:
            self.result = M.Compare(
                L.AttemptOutcome(M.Head(found)())(), L.CheckedReachableTag()()
            )()
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MissingReadingIsNotChecked(M.Edge):
    def __init__(self, run):
        proved = M.Head(U.RunProved(run)())()
        invariant = X.ProvedCertificate(proved)()
        observer = C.CertificateObserver(invariant)()
        specs = D.REvenSpecs()()
        start = D.TokenState(D.PeanoZero()(), D.EvenTag()())()
        goal = P.Knowledge(
            M.Pair(D.TokensFact(D.PeanoZero()())(), M.EmptyList)
        )()
        preservation = MC.CheckObserverPreservation(observer, specs)()
        start_reading = I.PhiReading(start, observer)()
        endpoint = K.EndpointCertificate(
            observer,
            start,
            goal,
            specs,
            invariant,
            MC.VerdictEvidence(preservation)(),
            start_reading,
            M.EmptyList,
        )()
        replay = K.ReplayEndpointCertificate(
            endpoint, observer, specs, start, goal
        )()
        self.result = M.Compare(C.VerdictTag(replay)(), C.NotCheckedTag()())()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TamperedEndpointFails(M.Edge):
    def __init__(self, run):
        event = M.Head(U.RunEvents(run)())()
        decision = U.EventDecision(event)()
        certificate = K.DecisionEndpointCertificate(decision)()
        found = FindAttempt(U.RunAttempts(run)(), U.EventTaskId(event)())()
        record = G.RowRecord(L.AttemptRow(M.Head(found)())())()
        tampered = C.CertificateRecord(
            C.CertificateKind(certificate)(),
            C.CertificateObserver(certificate)(),
            C.CertificateGoal(certificate)(),
            C.CertificateGoal(certificate)(),
            C.CertificateDigest(certificate)(),
            C.CertificateVersion(certificate)(),
            C.CertificateEvidence(certificate)(),
        )()
        replay = K.ReplayEndpointCertificate(
            tampered,
            K.DecisionObserver(decision)(),
            G.TaskSpecs(record)(),
            G.TaskStart(record)(),
            G.TaskGoal(record)(),
        )()
        self.result = M.Compare(C.VerdictTag(replay)(), C.ReplayFailedTag()())()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ScopeBreakOutcomes(M.Edge):
    def __init__(self, attempts):
        first = FindAttempt(attempts, M.Char("T0043"))()
        second = FindAttempt(attempts, M.Char("T0045"))()
        third = FindAttempt(attempts, M.Char("T0046"))()
        if M.Compare(
            L.AttemptOutcome(M.Head(first)())(), L.UnsupportedTag()()
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            L.AttemptOutcome(M.Head(second)())(), L.UnsupportedTag()()
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.Compare(
                L.AttemptOutcome(M.Head(third)())(), K.CheckedUnreachableTag()()
            )()
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class G4ArchivesRemainExact(M.Edge):
    def __init__(self, run, here):
        candidates = FileText(
            os.path.join(here, "candidates", "candidates.jsonl")
        )()
        proved = FileText(
            os.path.join(here, "candidates", "proved_invariants.jsonl")
        )()
        refuted = FileText(
            os.path.join(here, "candidates", "refuted_candidates.jsonl")
        )()
        if M.Compare(
            M.Char(candidates), M.Char(X.CandidatesText(U.RunCandidates(run)())())
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Char(proved), M.Char(X.ProvedText(U.RunProved(run)())())
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.Compare(
                M.Char(refuted), M.Char(X.RefutedText(U.RunRefuted(run)())())
            )()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ArtifactReproduces(M.Edge):
    def __init__(self, run, here):
        written = FileText(
            os.path.join(here, "certificates", "prune_events.jsonl")
        )()
        rendered = U.PruneEventsText(U.RunEvents(run)())()
        self.result = M.Compare(M.Char(written), M.Char(rendered))()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class G5Tests(M.Edge):
    def __init__(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kept = M.Head(G.DropExactDuplicates(G.GenerateAllRows()())())()
        representatives = L.CanonicalRepresentatives(kept)()
        run = U.InRunUse(
            representatives, L.EXPANSION_BUDGET, L.WALL_CLOCK_BUDGET_MS
        )()
        built = M.EmptyList
        built = ChainAppend(
            built,
            M.Pair(M.Char("same 34 representatives and budgets"), DeliveredOrderAndBudget(run, representatives)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("cadence and three proved invariants remain bound"), CadenceAndProofsRemainBound(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("exactly eight later tasks are pruned"), EightLaterTasksPruned(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("G5 outcome and expansion totals are exact"), OutcomeTotals(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("every endpoint proof independently replays"), AllPruneProofsReplay(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("expansion saved estimates are recorded"), ExpansionEstimatesRecorded(U.RunEvents(run)())),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("R_plus returns ScopeMismatch for the old certificate"), RPlusReturnsScopeMismatch(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("R_plus never prunes"), NoRPlusPrune(U.RunEvents(run)())),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("candidate-only evidence cannot prune"), CandidateOnlyCannotPrune(run, representatives)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("trace-only evidence cannot prune"), TraceOnlyCannotPrune(run, representatives)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("pre-proof tasks are not retroactively pruned"), EarlyTasksAreNotRetroactivelyPruned(U.RunAttempts(run)())),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("same endpoint reading does not prune"), SameReadingDoesNotPrune(U.RunAttempts(run)())),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("missing endpoint reading is NOT_CHECKED"), MissingReadingIsNotChecked(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("tampered endpoint binding fails replay"), TamperedEndpointFails(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("scope-break outcomes respect exact new scope"), ScopeBreakOutcomes(U.RunAttempts(run)())),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("G4 candidate archives remain byte exact"), G4ArchivesRemainExact(run, here)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("prune event artifact reproduces byte for byte"), ArtifactReproduces(run, here)),
        )()
        self.result = built
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result
