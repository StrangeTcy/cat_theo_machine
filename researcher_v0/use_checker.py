"""Researcher-v0 G5 checker for endpoint-bound invariant use.

A proved ruleset invariant is not itself an unreachability result. This module
checks its scope first, independently replays preservation for every exact
rule, requires present start and goal readings, requires separation, binds an
endpoint certificate, and replays that certificate before returning a prune
decision. Candidate and trace records are not accepted by this interface.
"""

from __future__ import annotations

from .. import machine as M
from . import checker as C
from . import mining as X
from . import mining_checker as MC
from . import ruleset_digest as RD
from . import task_generation as G
from . import token_domain as D
from .chains import ChainAppend, IsEmptyTerm


class CheckedUnreachableTag(M.Edge):
    def __init__(self):
        self.result = M.Char("CHECKED_UNREACHABLE")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class UnreachabilityKind(M.Edge):
    def __init__(self):
        self.result = M.Char("invariant-unreachability")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EndpointEvidence(M.Edge):
    def __init__(
        self,
        invariant_certificate,
        preservation_evidence,
        start_reading,
        goal_reading,
    ):
        self.result = M.Pair(
            invariant_certificate,
            M.Pair(
                preservation_evidence,
                M.Pair(start_reading, M.Pair(goal_reading, M.EmptyList)),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EvidenceInvariantCertificate(M.Edge):
    def __init__(self, evidence):
        self.result = D.HeadAt(evidence, 0)()
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EvidencePreservation(M.Edge):
    def __init__(self, evidence):
        self.result = D.HeadAt(evidence, 1)()
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EvidenceStartReading(M.Edge):
    def __init__(self, evidence):
        self.result = D.HeadAt(evidence, 2)()
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EvidenceGoalReading(M.Edge):
    def __init__(self, evidence):
        self.result = D.HeadAt(evidence, 3)()
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EndpointCertificate(M.Edge):
    def __init__(
        self,
        observer,
        start,
        goal,
        specs,
        invariant_certificate,
        preservation_evidence,
        start_reading,
        goal_reading,
    ):
        evidence = EndpointEvidence(
            invariant_certificate,
            preservation_evidence,
            start_reading,
            goal_reading,
        )()
        self.result = C.CertificateRecord(
            UnreachabilityKind()(),
            observer,
            start,
            goal,
            D.RulesetVersionOfSpecs(specs)(),
            C.CheckerVersion()(),
            evidence,
        )()
        super().__init__(inputs=M.Pair(observer, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EndpointCertificateId(M.Edge):
    def __init__(self, certificate, task_id):
        self.result = M.Char(
            "unreach-" + task_id() + "-" + C.CertificateDigest(certificate)()()
        )
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalTermMatches(M.Edge):
    def __init__(self, left, right):
        left_text = M.Head(RD.TermText(left, M.EmptyList)())()
        right_text = M.Head(RD.TermText(right, M.EmptyList)())()
        self.result = M.Compare(left_text, right_text)()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class EvidenceStepWithDigest(M.Edge):
    def __init__(self, evidence, digest):
        self.result = self._scan(evidence, digest)
        super().__init__(inputs=M.Pair(evidence, M.Pair(digest, M.EmptyList)), results=self.result)

    def _scan(self, evidence, digest):
        if IsEmptyTerm(evidence)() is M.truth_value:
            return M.EmptyList
        step = M.Head(evidence)()
        if M.Compare(MC.StepRuleDigest(step)(), digest)() is M.truth_value:
            return M.Pair(step, M.EmptyList)
        return self._scan(M.Tail(evidence)(), digest)

    def __call__(self):
        return self.result


class EvidenceStepMatches(M.Edge):
    def __init__(self, recorded, recomputed):
        if M.Compare(
            MC.StepRuleDigest(recorded)(), MC.StepRuleDigest(recomputed)()
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            MC.StepStatus(recorded)(), MC.StepStatus(recomputed)()
        )() is M.false_value:
            self.result = M.false_value
        elif CanonicalTermMatches(
            MC.StepPreReading(recorded)(), MC.StepPreReading(recomputed)()
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = CanonicalTermMatches(
                MC.StepPostReading(recorded)(), MC.StepPostReading(recomputed)()
            )()
        super().__init__(
            inputs=M.Pair(recorded, M.Pair(recomputed, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class EvidenceIsEquivalent(M.Edge):
    def __init__(self, recorded, recomputed):
        self.result = self._both(recorded, recomputed)
        super().__init__(
            inputs=M.Pair(recorded, M.Pair(recomputed, M.EmptyList)),
            results=self.result,
        )

    def _contains_all(self, source, target):
        if IsEmptyTerm(source)() is M.truth_value:
            return M.truth_value
        step = M.Head(source)()
        found = EvidenceStepWithDigest(target, MC.StepRuleDigest(step)())()
        if IsEmptyTerm(found)() is M.truth_value:
            return M.false_value
        if EvidenceStepMatches(step, M.Head(found)())() is M.false_value:
            return M.false_value
        return self._contains_all(M.Tail(source)(), target)

    def _both(self, recorded, recomputed):
        if self._contains_all(recorded, recomputed) is M.false_value:
            return M.false_value
        return self._contains_all(recomputed, recorded)

    def __call__(self):
        return self.result


class ReplayInvariantForUse(M.Edge):
    def __init__(self, certificate, observer, specs):
        self.result = self._replay(certificate, observer, specs)
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def _replay(self, certificate, observer, specs):
        digest = D.RulesetVersionOfSpecs(specs)()
        if M.Compare(digest, C.CertificateDigest(certificate)())() is M.false_value:
            return C.ReplayVerdict(
                C.ScopeMismatchTag()(),
                "ruleset digest differs; nothing else compared and nothing claimed",
                0,
            )()
        if M.Compare(
            C.CertificateKind(certificate)(), C.InvariantSlotKind()()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "certificate kind is not proved-invariant", 0
            )()
        if M.Compare(C.CertificateObserver(certificate)(), observer)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "certificate observer differs", 0
            )()
        if IsEmptyTerm(C.CertificateStart(certificate)())() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "invariant start slot is not empty", 0
            )()
        if IsEmptyTerm(C.CertificateGoal(certificate)())() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "invariant goal slot is not empty", 0
            )()
        if M.Compare(
            C.CertificateVersion(certificate)(), C.CheckerVersion()()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "checker version differs", 0
            )()
        recomputed = MC.CheckObserverPreservation(observer, specs)()
        if M.Compare(
            MC.VerdictStatus(recomputed)(), MC.ProvedTag()()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "exact-ruleset preservation recomputation is not PROVED",
                MC.EvidenceCount(MC.VerdictEvidence(recomputed)())(),
            )()
        if M.Compare(MC.VerdictObserver(recomputed)(), observer)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "preservation verdict names a different observer",
                MC.EvidenceCount(MC.VerdictEvidence(recomputed)())(),
            )()
        if M.Compare(MC.VerdictDigest(recomputed)(), digest)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "preservation verdict names a different ruleset",
                MC.EvidenceCount(MC.VerdictEvidence(recomputed)())(),
            )()
        if EvidenceIsEquivalent(
            C.CertificateEvidence(certificate)(), MC.VerdictEvidence(recomputed)()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "recorded semantic preservation evidence differs from recomputation",
                MC.EvidenceCount(MC.VerdictEvidence(recomputed)())(),
            )()
        return C.ReplayVerdict(
            C.ReplayedTag()(),
            "scope and every semantic preservation step recomputed",
            MC.EvidenceCount(MC.VerdictEvidence(recomputed)())(),
        )()

    def __call__(self):
        return self.result


class ReplayEndpointCertificate(M.Edge):
    def __init__(self, certificate, observer, specs, start, goal):
        self.result = self._replay(certificate, observer, specs, start, goal)
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def _replay(self, certificate, observer, specs, start, goal):
        digest = D.RulesetVersionOfSpecs(specs)()
        if M.Compare(digest, C.CertificateDigest(certificate)())() is M.false_value:
            return C.ReplayVerdict(
                C.ScopeMismatchTag()(),
                "task ruleset digest differs; no endpoint or observer was compared",
                0,
            )()
        if M.Compare(
            C.CertificateKind(certificate)(), UnreachabilityKind()()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "certificate kind is not invariant-unreachability",
                0,
            )()
        if M.Compare(C.CertificateObserver(certificate)(), observer)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "certificate observer differs", 0
            )()
        if M.Compare(C.CertificateStart(certificate)(), start)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "certificate start differs", 0
            )()
        if M.Compare(C.CertificateGoal(certificate)(), goal)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "certificate goal differs", 0
            )()
        if M.Compare(
            C.CertificateVersion(certificate)(), C.CheckerVersion()()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "checker version differs", 0
            )()
        evidence = C.CertificateEvidence(certificate)()
        invariant_certificate = EvidenceInvariantCertificate(evidence)()
        invariant_replay = ReplayInvariantForUse(
            invariant_certificate, observer, specs
        )()
        if C.IsReplayed(invariant_replay)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "the cited invariant certificate did not replay",
                C.VerdictSteps(invariant_replay)(),
            )()
        preservation = MC.CheckObserverPreservation(observer, specs)()
        if M.Compare(
            MC.VerdictStatus(preservation)(), MC.ProvedTag()()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "exact-ruleset preservation recomputation is not PROVED",
                MC.EvidenceCount(MC.VerdictEvidence(preservation)())(),
            )()
        if M.Compare(MC.VerdictObserver(preservation)(), observer)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "preservation verdict names a different observer",
                MC.EvidenceCount(MC.VerdictEvidence(preservation)())(),
            )()
        if M.Compare(MC.VerdictDigest(preservation)(), digest)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "preservation verdict names a different ruleset",
                MC.EvidenceCount(MC.VerdictEvidence(preservation)())(),
            )()
        if M.Compare(
            EvidencePreservation(evidence)(), MC.VerdictEvidence(preservation)()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "recorded preservation evidence differs from recomputation",
                MC.EvidenceCount(MC.VerdictEvidence(preservation)())(),
            )()
        readings = C.ObserverReadings(start, goal, observer)()
        if M.Compare(M.Head(readings)(), C.ReadingsPresentTag()())() is M.false_value:
            return C.ReplayVerdict(
                C.NotCheckedTag()(),
                "both endpoint readings are not present",
                MC.EvidenceCount(MC.VerdictEvidence(preservation)())(),
            )()
        if M.Compare(C.ReadingsVerdict(readings)(), C.SeparatesTag()())() is M.false_value:
            return C.ReplayVerdict(
                C.NotCheckedTag()(),
                "present endpoint readings do not separate",
                MC.EvidenceCount(MC.VerdictEvidence(preservation)())(),
            )()
        if M.Compare(
            EvidenceStartReading(evidence)(), D.HeadAt(readings, 1)()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "recorded start reading differs from recomputation",
                MC.EvidenceCount(MC.VerdictEvidence(preservation)())(),
            )()
        if M.Compare(
            EvidenceGoalReading(evidence)(), D.HeadAt(readings, 2)()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "recorded goal reading differs from recomputation",
                MC.EvidenceCount(MC.VerdictEvidence(preservation)())(),
            )()
        return C.ReplayVerdict(
            C.ReplayedTag()(),
            "scope, every rule, both endpoint readings, and separation recomputed",
            MC.EvidenceCount(MC.VerdictEvidence(preservation)())(),
        )()

    def __call__(self):
        return self.result


class ScopeCheck(M.Edge):
    def __init__(self, task_id, invariant_certificate, replay):
        self.result = M.Pair(
            task_id,
            M.Pair(
                MC.InvariantCertificateId(invariant_certificate)(),
                M.Pair(
                    C.CertificateDigest(invariant_certificate)(),
                    M.Pair(
                        C.VerdictTag(replay)(),
                        M.Pair(C.VerdictReason(replay)(), M.EmptyList),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ScopeCheckTaskId(M.Edge):
    def __init__(self, scope_check):
        self.result = D.HeadAt(scope_check, 0)()
        super().__init__(inputs=M.Pair(scope_check, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ScopeCheckCertificateId(M.Edge):
    def __init__(self, scope_check):
        self.result = D.HeadAt(scope_check, 1)()
        super().__init__(inputs=M.Pair(scope_check, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ScopeCheckCertificateDigest(M.Edge):
    def __init__(self, scope_check):
        self.result = D.HeadAt(scope_check, 2)()
        super().__init__(inputs=M.Pair(scope_check, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ScopeCheckTag(M.Edge):
    def __init__(self, scope_check):
        self.result = D.HeadAt(scope_check, 3)()
        super().__init__(inputs=M.Pair(scope_check, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ScopeCheckReason(M.Edge):
    def __init__(self, scope_check):
        self.result = D.HeadAt(scope_check, 4)()
        super().__init__(inputs=M.Pair(scope_check, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class UseDecision(M.Edge):
    def __init__(
        self,
        endpoint_certificate,
        invariant_certificate,
        observer,
        start_reading,
        goal_reading,
        replay,
    ):
        self.result = M.Pair(
            endpoint_certificate,
            M.Pair(
                invariant_certificate,
                M.Pair(
                    observer,
                    M.Pair(
                        start_reading,
                        M.Pair(goal_reading, M.Pair(replay, M.EmptyList)),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DecisionEndpointCertificate(M.Edge):
    def __init__(self, decision):
        self.result = D.HeadAt(decision, 0)()
        super().__init__(inputs=M.Pair(decision, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DecisionInvariantCertificate(M.Edge):
    def __init__(self, decision):
        self.result = D.HeadAt(decision, 1)()
        super().__init__(inputs=M.Pair(decision, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DecisionObserver(M.Edge):
    def __init__(self, decision):
        self.result = D.HeadAt(decision, 2)()
        super().__init__(inputs=M.Pair(decision, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DecisionStartReading(M.Edge):
    def __init__(self, decision):
        self.result = D.HeadAt(decision, 3)()
        super().__init__(inputs=M.Pair(decision, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DecisionGoalReading(M.Edge):
    def __init__(self, decision):
        self.result = D.HeadAt(decision, 4)()
        super().__init__(inputs=M.Pair(decision, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DecisionReplay(M.Edge):
    def __init__(self, decision):
        self.result = D.HeadAt(decision, 5)()
        super().__init__(inputs=M.Pair(decision, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class UseCheckResult(M.Edge):
    def __init__(self, decision_shell, scope_checks):
        self.result = M.Pair(
            decision_shell, M.Pair(scope_checks, M.EmptyList)
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class UseDecisionShell(M.Edge):
    def __init__(self, use_result):
        self.result = D.HeadAt(use_result, 0)()
        super().__init__(inputs=M.Pair(use_result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class UseScopeChecks(M.Edge):
    def __init__(self, use_result):
        self.result = D.HeadAt(use_result, 1)()
        super().__init__(inputs=M.Pair(use_result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TaskIdOfRow(M.Edge):
    def __init__(self, row):
        self.result = M.Char(G.ParentIdText(G.RowSerial(row)())())
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CheckForPrune(M.Edge):
    """Try proved certificates only, in archive order, against one exact task."""

    def __init__(self, row, proved_archive):
        self.result = self._scan(row, proved_archive, M.EmptyList)
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def _scan(self, row, proved_archive, scope_checks):
        if IsEmptyTerm(proved_archive)() is M.truth_value:
            return UseCheckResult(M.EmptyList, scope_checks)()
        invariant_certificate = X.ProvedCertificate(M.Head(proved_archive)())()
        record = G.RowRecord(row)()
        specs = G.TaskSpecs(record)()
        start = G.TaskStart(record)()
        goal = G.TaskGoal(record)()
        observer = C.CertificateObserver(invariant_certificate)()
        invariant_replay = ReplayInvariantForUse(
            invariant_certificate, observer, specs
        )()
        scope_checks = ChainAppend(
            scope_checks,
            ScopeCheck(TaskIdOfRow(row)(), invariant_certificate, invariant_replay)(),
        )()
        if C.IsReplayed(invariant_replay)() is M.truth_value:
            preservation = MC.CheckObserverPreservation(observer, specs)()
            readings = C.ObserverReadings(start, goal, observer)()
            if M.Compare(
                MC.VerdictStatus(preservation)(), MC.ProvedTag()()
            )() is M.truth_value:
                if M.Compare(
                    M.Head(readings)(), C.ReadingsPresentTag()()
                )() is M.truth_value:
                    if M.Compare(
                        C.ReadingsVerdict(readings)(), C.SeparatesTag()()
                    )() is M.truth_value:
                        endpoint_certificate = EndpointCertificate(
                            observer,
                            start,
                            goal,
                            specs,
                            invariant_certificate,
                            MC.VerdictEvidence(preservation)(),
                            D.HeadAt(readings, 1)(),
                            D.HeadAt(readings, 2)(),
                        )()
                        replay = ReplayEndpointCertificate(
                            endpoint_certificate, observer, specs, start, goal
                        )()
                        if C.IsReplayed(replay)() is M.truth_value:
                            decision = UseDecision(
                                endpoint_certificate,
                                invariant_certificate,
                                observer,
                                D.HeadAt(readings, 1)(),
                                D.HeadAt(readings, 2)(),
                                replay,
                            )()
                            return UseCheckResult(
                                M.Pair(decision, M.EmptyList), scope_checks
                            )()
        return self._scan(row, M.Tail(proved_archive)(), scope_checks)

    def __call__(self):
        return self.result
