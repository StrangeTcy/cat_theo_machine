"""Researcher-v0 G5 in-run use gate.

The run keeps G4's fixed mining cadence and introduces one new route before a
later task enters search: proved certificates only are checked by
``use_checker``. A replayed endpoint-bound proof yields CHECKED_UNREACHABLE at
zero expansions and a prune event. Candidate and trace archives are never
accepted by the use checker. The proved archive remains local to this run.
"""

from __future__ import annotations

from .. import machine as M
from . import checker as C
from . import laboratory as L
from . import mining as X
from . import mining_checker as MC
from . import task_generation as G
from . import token_domain as D
from . import use_checker as U
from .chains import ChainAppend, ChainJoin, IsEmptyTerm


class ObserverName(M.Edge):
    def __init__(self, observer):
        parity = X.ObserverPattern(X.ParityLengthObserverSpec()())()
        length = X.ObserverPattern(X.LengthObserverSpec()())()
        if M.Compare(observer, parity)() is M.truth_value:
            self.result = M.Char("Parity(Length)")
        elif M.Compare(observer, length)() is M.truth_value:
            self.result = M.Char("Length")
        else:
            self.result = M.Char(X.TermText(observer)())
        super().__init__(inputs=M.Pair(observer, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PrunedAttempt(M.Edge):
    def __init__(self, sequence, entry, decision):
        row = M.Head(entry)()
        members = D.HeadAt(entry, 1)()
        certificate = U.DecisionEndpointCertificate(decision)()
        replay = U.DecisionReplay(decision)()
        body = L.AttemptBody(
            U.CheckedUnreachableTag()(),
            "proved invariant replayed for the exact ruleset; both endpoint readings are present and separate",
            0,
            M.Pair(
                M.Pair(certificate, M.Pair(replay, M.EmptyList)), M.EmptyList
            ),
            M.EmptyList,
            M.Pair(L.TaskBinding(row)(), M.EmptyList),
        )()
        self.result = M.Pair(
            M.Pair(sequence, M.EmptyList),
            M.Pair(
                row,
                M.Pair(
                    M.Pair(members, M.EmptyList),
                    M.Pair(body, M.Pair(M.Pair(0, M.EmptyList), M.EmptyList)),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PruneEvent(M.Edge):
    def __init__(self, row, decision, expansion_estimate):
        task_id = U.TaskIdOfRow(row)()
        endpoint_certificate = U.DecisionEndpointCertificate(decision)()
        invariant_certificate = U.DecisionInvariantCertificate(decision)()
        observer = U.DecisionObserver(decision)()
        event_id = M.Char(
            "prune-" + task_id() + "-" + C.CertificateDigest(endpoint_certificate)()()
        )
        self.result = M.Pair(
            event_id,
            M.Pair(
                task_id,
                M.Pair(
                    M.Char(G.RowCanonicalId(row)()),
                    M.Pair(
                        U.EndpointCertificateId(endpoint_certificate, task_id)(),
                        M.Pair(
                            MC.InvariantCertificateId(invariant_certificate)(),
                            M.Pair(
                                ObserverName(observer)(),
                                M.Pair(
                                    U.DecisionStartReading(decision)(),
                                    M.Pair(
                                        U.DecisionGoalReading(decision)(),
                                        M.Pair(
                                            U.CheckedUnreachableTag()(),
                                            M.Pair(
                                                M.Pair(
                                                    expansion_estimate, M.EmptyList
                                                ),
                                                M.Pair(decision, M.EmptyList),
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
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventId(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 0)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventTaskId(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 1)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventCanonicalId(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 2)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventCertificateId(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 3)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventInvariantCertificateId(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 4)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventObserverName(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 5)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventStartReading(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 6)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventGoalReading(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 7)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventResult(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 8)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventExpansionEstimate(M.Edge):
    def __init__(self, event):
        self.result = M.Head(D.HeadAt(event, 9)())()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventDecision(M.Edge):
    def __init__(self, event):
        self.result = D.HeadAt(event, 10)()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class UseRunRecord(M.Edge):
    def __init__(
        self,
        attempts,
        path_archive,
        candidates,
        proved,
        refuted,
        events,
        scope_checks,
        sweep_seqs,
    ):
        self.result = M.Pair(
            attempts,
            M.Pair(
                path_archive,
                M.Pair(
                    candidates,
                    M.Pair(
                        proved,
                        M.Pair(
                            refuted,
                            M.Pair(
                                events,
                                M.Pair(
                                    scope_checks,
                                    M.Pair(sweep_seqs, M.EmptyList),
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


class RunEvents(M.Edge):
    def __init__(self, run):
        self.result = D.HeadAt(run, 5)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RunScopeChecks(M.Edge):
    def __init__(self, run):
        self.result = D.HeadAt(run, 6)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RunSweepSeqs(M.Edge):
    def __init__(self, run):
        self.result = D.HeadAt(run, 7)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InRunUse(M.Edge):
    def __init__(self, representatives, budget, wall_ms):
        self.result = self._walk(
            representatives,
            D.PeanoSucc(D.PeanoZero()())(),
            X.MiningCadence()(),
            M.EmptyList,
            M.EmptyList,
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
        events,
        scope_checks,
        sweep_seqs,
        swept_last,
        budget,
        wall_ms,
    ):
        if IsEmptyTerm(remaining)() is M.truth_value:
            if IsEmptyTerm(attempts)() is M.false_value:
                if M.IdentityCompare(swept_last, M.false_value)() is M.truth_value:
                    sweep_seq = L.LastSeq(attempts)()
                    swept = X.MiningSweep(
                        attempts,
                        sweep_seq,
                        assessed,
                        candidates,
                        proved,
                        refuted,
                    )()
                    candidates = X.SweepCandidates(swept)()
                    proved = X.SweepProved(swept)()
                    refuted = X.SweepRefuted(swept)()
                    sweep_seqs = ChainAppend(
                        sweep_seqs, M.Pair(sweep_seq, M.EmptyList)
                    )()
            return UseRunRecord(
                attempts,
                path_archive,
                candidates,
                proved,
                refuted,
                events,
                scope_checks,
                sweep_seqs,
            )()
        entry = M.Head(remaining)()
        row = M.Head(entry)()
        use_result = U.CheckForPrune(row, proved)()
        scope_checks = ChainJoin(
            scope_checks, U.UseScopeChecks(use_result)()
        )()
        decision_shell = U.UseDecisionShell(use_result)()
        if IsEmptyTerm(decision_shell)() is M.false_value:
            decision = M.Head(decision_shell)()
            attempt = PrunedAttempt(
                D.StructuralCount(sequence)(), entry, decision
            )()
            record = G.RowRecord(row)()
            if G.IsScopeBreakRecord(record)() is M.truth_value:
                estimate = 0
            else:
                estimate = budget
            events = ChainAppend(
                events, PruneEvent(row, decision, estimate)()
            )()
        else:
            attempt = L.BaselineAttempt(
                D.StructuralCount(sequence)(),
                entry,
                path_archive,
                budget,
                wall_ms,
            )()
        if M.Compare(
            L.AttemptOutcome(attempt)(), L.CheckedReachableTag()()
        )() is M.truth_value:
            certificate_shell = L.AttemptCertificateShell(attempt)()
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
            swept = X.MiningSweep(
                attempts, sweep_seq, assessed, candidates, proved, refuted
            )()
            assessed = X.SweepAssessed(swept)()
            candidates = X.SweepCandidates(swept)()
            proved = X.SweepProved(swept)()
            refuted = X.SweepRefuted(swept)()
            sweep_seqs = ChainAppend(
                sweep_seqs, M.Pair(sweep_seq, M.EmptyList)
            )()
            cadence = X.MiningCadence()()
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
            events,
            scope_checks,
            sweep_seqs,
            swept_last,
            budget,
            wall_ms,
        )

    def __call__(self):
        return self.result


class EventJson(M.Edge):
    def __init__(self, event):
        decision = EventDecision(event)()
        endpoint_certificate = U.DecisionEndpointCertificate(decision)()
        evidence = C.CertificateEvidence(endpoint_certificate)()
        replay = U.DecisionReplay(decision)()
        self.result = (
            '{"prune_event_id":"'
            + EventId(event)()()
            + '","task_id":"'
            + EventTaskId(event)()()
            + '","canonical_id":"'
            + EventCanonicalId(event)()()
            + '","certificate_id":"'
            + EventCertificateId(event)()()
            + '","invariant_certificate_id":"'
            + EventInvariantCertificateId(event)()()
            + '","observer":"'
            + EventObserverName(event)()()
            + '","ruleset_version":"'
            + C.CertificateDigest(endpoint_certificate)()()
            + '","start_value":"'
            + L.JsonSafeText(X.TermText(EventStartReading(event)())())()
            + '","goal_value":"'
            + L.JsonSafeText(X.TermText(EventGoalReading(event)())())()
            + '","result":"'
            + EventResult(event)()()
            + '","expansions_saved_estimate":'
            + str(EventExpansionEstimate(event)())
            + ',"checker_version":"'
            + C.CertificateVersion(endpoint_certificate)()()
            + '","rules_checked":'
            + str(MC.EvidenceCount(U.EvidencePreservation(evidence)())())
            + ',"preservation":'
            + X.EvidenceJson(U.EvidencePreservation(evidence)())()
            + ',"replay":"'
            + C.VerdictTag(replay)()()
            + '","replay_reason":"'
            + L.JsonSafeText(C.VerdictReason(replay)()())()
            + '"}'
        )
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PruneEventsText(M.Edge):
    def __init__(self, events):
        self.result = self._lines(events)
        super().__init__(inputs=M.Pair(events, M.EmptyList), results=self.result)

    def _lines(self, events):
        if IsEmptyTerm(events)() is M.truth_value:
            return ""
        return EventJson(M.Head(events)())() + "\n" + self._lines(M.Tail(events)())

    def __call__(self):
        return self.result
