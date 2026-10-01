"""Researcher-v0 G4 independent preservation checker.

This module is deliberately separate from the trace miner.  A trace survivor
is only a candidate; this checker recomputes the exact ruleset fingerprint,
reads both sides of every exact rule body, invokes ``invariance.Preserves`` on
every rule, and only then mints a proved-invariant certificate.  Missing
readings are UNSUPPORTED, never a false comparison.  Invariant certificates
reuse G3's common certificate record and checker version, but have their own
content encoder because their evidence is a chain of preservation steps rather
than a path.
"""

from __future__ import annotations

from .. import invariance as I
from .. import machine as M
from .. import proof as P
from . import checker as C
from . import ruleset_digest as RD
from . import token_domain as D
from .chains import ChainAppend, IsEmptyTerm


class PreservedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("PRESERVED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ProvedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("PROVED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RefutedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("REFUTED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class UnsupportedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("UNSUPPORTED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PreservationStep(M.Edge):
    """Independent result for one exact rule body.

    Layout: rule digest, display text, status, pre reading, post reading,
    result returned by ``Preserves``, and a reason text.
    """

    def __init__(self, spec, observer):
        rule = D.RuleContent(spec)()
        pre = I.PhiReading(P.Knowledge(D.PremisesOfRule(rule)())(), observer)()
        post = I.PhiReading(P.Knowledge(I.ReplacementFacts(rule)())(), observer)()
        checked = I.Preserves(rule, observer, M.EmptyList)()
        status = PreservedTag()()
        reason = "both rule-side readings are present and Preserves discharged"
        if IsEmptyTerm(pre)() is M.truth_value:
            status = UnsupportedTag()()
            reason = "premise-side observer reading is missing"
        elif IsEmptyTerm(post)() is M.truth_value:
            status = UnsupportedTag()()
            reason = "replacement-side observer reading is missing"
        elif I.IsPreserves(checked)() is M.false_value:
            if I.IsInvariantRefuted(checked)() is M.truth_value:
                status = RefutedTag()()
                reason = "present rule-side readings differ"
            else:
                status = UnsupportedTag()()
                reason = "Preserves returned neither preservation nor refutation"
        self.result = M.Pair(
            D.RuleFingerprintOfSpec(spec)(),
            M.Pair(
                D.RuleDisplay(spec)(),
                M.Pair(
                    status,
                    M.Pair(
                        pre,
                        M.Pair(
                            post,
                            M.Pair(checked, M.Pair(M.Char(reason), M.EmptyList)),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(spec, M.Pair(observer, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class StepRuleDigest(M.Edge):
    def __init__(self, step):
        self.result = D.HeadAt(step, 0)()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StepRuleDisplay(M.Edge):
    def __init__(self, step):
        self.result = D.HeadAt(step, 1)()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StepStatus(M.Edge):
    def __init__(self, step):
        self.result = D.HeadAt(step, 2)()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StepPreReading(M.Edge):
    def __init__(self, step):
        self.result = D.HeadAt(step, 3)()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StepPostReading(M.Edge):
    def __init__(self, step):
        self.result = D.HeadAt(step, 4)()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StepPreservesResult(M.Edge):
    def __init__(self, step):
        self.result = D.HeadAt(step, 5)()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StepReason(M.Edge):
    def __init__(self, step):
        self.result = D.HeadAt(step, 6)()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PreservationEvidence(M.Edge):
    """A preservation step for every rule, in exact delivered spec order."""

    def __init__(self, specs, observer):
        self.result = self._walk(specs, observer, M.EmptyList)
        super().__init__(
            inputs=M.Pair(specs, M.Pair(observer, M.EmptyList)), results=self.result
        )

    def _walk(self, specs, observer, built):
        if IsEmptyTerm(specs)() is M.truth_value:
            return built
        return self._walk(
            M.Tail(specs)(),
            observer,
            ChainAppend(built, PreservationStep(M.Head(specs)(), observer)())(),
        )

    def __call__(self):
        return self.result


class EvidenceHasStatus(M.Edge):
    def __init__(self, evidence, status):
        self.result = self._scan(evidence, status)
        super().__init__(
            inputs=M.Pair(evidence, M.Pair(status, M.EmptyList)), results=self.result
        )

    def _scan(self, evidence, status):
        if IsEmptyTerm(evidence)() is M.truth_value:
            return M.false_value
        if M.Compare(StepStatus(M.Head(evidence)())(), status)() is M.truth_value:
            return M.truth_value
        return self._scan(M.Tail(evidence)(), status)

    def __call__(self):
        return self.result


class EvidenceCount(M.Edge):
    def __init__(self, evidence):
        counted = self._count(evidence, D.PeanoZero()())
        self.result = D.StructuralCount(counted)()
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=self.result)

    def _count(self, evidence, count):
        if IsEmptyTerm(evidence)() is M.truth_value:
            return count
        return self._count(M.Tail(evidence)(), D.PeanoSucc(count)())

    def __call__(self):
        return self.result


class PreservationVerdict(M.Edge):
    """Status, digest, observer, evidence, optional certificate, and reason."""

    def __init__(self, status, digest, observer, evidence, certificate_shell, reason):
        self.result = M.Pair(
            status,
            M.Pair(
                digest,
                M.Pair(
                    observer,
                    M.Pair(
                        evidence,
                        M.Pair(certificate_shell, M.Pair(M.Char(reason), M.EmptyList)),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class VerdictStatus(M.Edge):
    def __init__(self, verdict):
        self.result = D.HeadAt(verdict, 0)()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerdictDigest(M.Edge):
    def __init__(self, verdict):
        self.result = D.HeadAt(verdict, 1)()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerdictObserver(M.Edge):
    def __init__(self, verdict):
        self.result = D.HeadAt(verdict, 2)()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerdictEvidence(M.Edge):
    def __init__(self, verdict):
        self.result = D.HeadAt(verdict, 3)()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerdictCertificateShell(M.Edge):
    def __init__(self, verdict):
        self.result = D.HeadAt(verdict, 4)()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerdictReason(M.Edge):
    def __init__(self, verdict):
        self.result = D.HeadAt(verdict, 5)()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CheckObserverPreservation(M.Edge):
    """Classify an observer against every rule of one exact ruleset."""

    def __init__(self, observer, specs):
        digest = D.RulesetVersionOfSpecs(specs)()
        evidence = PreservationEvidence(specs, observer)()
        if EvidenceHasStatus(evidence, RefutedTag()())() is M.truth_value:
            self.result = PreservationVerdict(
                RefutedTag()(),
                digest,
                observer,
                evidence,
                M.EmptyList,
                "at least one exact rule has present, differing observer readings",
            )()
        elif EvidenceHasStatus(evidence, UnsupportedTag()())() is M.truth_value:
            self.result = PreservationVerdict(
                UnsupportedTag()(),
                digest,
                observer,
                evidence,
                M.EmptyList,
                "at least one exact rule lacks the two readings required for checking",
            )()
        else:
            certificate = C.CertificateRecord(
                C.InvariantSlotKind()(),
                observer,
                M.EmptyList,
                M.EmptyList,
                digest,
                C.CheckerVersion()(),
                evidence,
            )()
            self.result = PreservationVerdict(
                ProvedTag()(),
                digest,
                observer,
                evidence,
                M.Pair(certificate, M.EmptyList),
                "Preserves discharged independently for every exact rule",
            )()
        super().__init__(
            inputs=M.Pair(observer, M.Pair(specs, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class InvariantEvidenceText(M.Edge):
    def __init__(self, evidence):
        self.result = M.Char("(preservation" + self._steps(evidence) + ")")
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=self.result)

    def _steps(self, evidence):
        if IsEmptyTerm(evidence)() is M.truth_value:
            return ""
        step = M.Head(evidence)()
        pre = M.Head(RD.TermText(StepPreReading(step)(), M.EmptyList)())()()
        post = M.Head(RD.TermText(StepPostReading(step)(), M.EmptyList)())()()
        return (
            " (rule "
            + StepRuleDigest(step)()()
            + " status "
            + StepStatus(step)()()
            + " pre "
            + pre
            + " post "
            + post
            + ")"
            + self._steps(M.Tail(evidence)())
        )

    def __call__(self):
        return self.result


class InvariantCertificateText(M.Edge):
    def __init__(self, certificate):
        observer = M.Head(
            RD.TermText(C.CertificateObserver(certificate)(), M.EmptyList)()
        )()()
        self.result = M.Char(
            "(certificate researcher-v0-certificate/1 kind "
            + C.CertificateKind(certificate)()()
            + " observer "
            + observer
            + " start () goal () ruleset "
            + C.CertificateDigest(certificate)()()
            + " checker "
            + C.CertificateVersion(certificate)()()
            + " evidence "
            + InvariantEvidenceText(C.CertificateEvidence(certificate)())()()
            + ")"
        )
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InvariantCertificateId(M.Edge):
    def __init__(self, certificate):
        observer = M.Head(
            RD.TermText(C.CertificateObserver(certificate)(), M.EmptyList)()
        )()()
        self.result = M.Char(
            "cert-invariant-"
            + C.CertificateDigest(certificate)()()
            + "-"
            + C.CertificateVersion(certificate)()()
            + "-"
            + observer
        )
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplayInvariantCertificate(M.Edge):
    """Recompute an invariant certificate; fingerprint scope is checked first."""

    def __init__(self, certificate, observer, specs):
        self.result = self._replay(certificate, observer, specs)
        super().__init__(
            inputs=M.Pair(
                certificate, M.Pair(observer, M.Pair(specs, M.EmptyList))
            ),
            results=self.result,
        )

    def _replay(self, certificate, observer, specs):
        digest = D.RulesetVersionOfSpecs(specs)()
        if M.Compare(digest, C.CertificateDigest(certificate)())() is M.false_value:
            return C.ReplayVerdict(
                C.ScopeMismatchTag()(),
                "ruleset digest differs; nothing else compared and nothing claimed",
                0,
            )()
        if M.Compare(C.CertificateKind(certificate)(), C.InvariantSlotKind()())() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "certificate kind is not proved-invariant", 0
            )()
        if M.Compare(C.CertificateObserver(certificate)(), observer)() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "certificate observer differs", 0
            )()
        if IsEmptyTerm(C.CertificateStart(certificate)())() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "invariant certificate start slot is not empty", 0
            )()
        if IsEmptyTerm(C.CertificateGoal(certificate)())() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "invariant certificate goal slot is not empty", 0
            )()
        if M.Compare(C.CertificateVersion(certificate)(), C.CheckerVersion()())() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(), "checker version differs", 0
            )()
        recomputed = CheckObserverPreservation(observer, specs)()
        if M.Compare(VerdictStatus(recomputed)(), ProvedTag()())() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "independent preservation recomputation is not PROVED",
                EvidenceCount(VerdictEvidence(recomputed)())(),
            )()
        if M.Compare(
            C.CertificateEvidence(certificate)(), VerdictEvidence(recomputed)()
        )() is M.false_value:
            return C.ReplayVerdict(
                C.ReplayFailedTag()(),
                "recorded preservation evidence differs from recomputation",
                EvidenceCount(VerdictEvidence(recomputed)())(),
            )()
        return C.ReplayVerdict(
            C.ReplayedTag()(),
            "fingerprint, observer and every per-rule preservation step recomputed",
            EvidenceCount(VerdictEvidence(recomputed)())(),
        )()

    def __call__(self):
        return self.result
