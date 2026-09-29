"""Executable acceptance tests for Researcher-v0 G4 MINING."""

from __future__ import annotations

import os

from ... import invariance as I
from ... import machine as M
from .. import checker as C
from .. import laboratory as L
from .. import mining as X
from .. import mining_checker as MC
from .. import task_generation as G
from .. import token_domain as D
from ..chains import ChainAppend, IsEmptyTerm


class FileText(M.Edge):
    def __init__(self, path):
        handle = open(path)
        self.result = handle.read()
        handle.close()
        super().__init__(inputs=M.Pair(M.Char(path), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FileLines(M.Edge):
    def __init__(self, path):
        handle = open(path)
        self.result = self._read(handle, M.EmptyList)
        handle.close()
        super().__init__(inputs=M.Pair(M.Char(path), M.EmptyList), results=self.result)

    def _read(self, handle, built):
        line = handle.readline()
        if M.Compare(M.Char(line), M.Char(""))() is M.truth_value:
            return built
        return self._read(handle, ChainAppend(built, M.Char(line))())

    def __call__(self):
        return self.result


class ChainHasCount(M.Edge):
    def __init__(self, chain, expected):
        self.result = X.ReportingCountEquals(X.ChainCount(chain)(), expected)()
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DeliveredSetAndCanonicalIds(M.Edge):
    def __init__(self, kept, representatives, here):
        delivered = FileText(os.path.join(here, "tasks", "tasks.jsonl"))()
        if M.Compare(M.Char(G.RowsToJsonl(kept)()), M.Char(delivered))() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(G.CountRows(kept)(), 42)() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            G.CountDistinctCanonical(kept)(), 34
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            X.ChainCount(representatives)(), 34
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(kept, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptsBindRepresentatives(M.Edge):
    def __init__(self, attempts, representatives):
        self.result = self._walk(attempts, representatives)
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _walk(self, attempts, representatives):
        if IsEmptyTerm(attempts)() is M.truth_value:
            if IsEmptyTerm(representatives)() is M.truth_value:
                return M.truth_value
            return M.false_value
        if IsEmptyTerm(representatives)() is M.truth_value:
            return M.false_value
        attempt = M.Head(attempts)()
        representative = M.Head(M.Head(representatives)())()
        if X.ReportingCountEquals(
            G.RowSerial(L.AttemptRow(attempt)())(), G.RowSerial(representative)()
        )() is M.false_value:
            return M.false_value
        if M.Compare(
            M.Char(G.RowCanonicalId(L.AttemptRow(attempt)())()),
            M.Char(G.RowCanonicalId(representative)()),
        )() is M.false_value:
            return M.false_value
        return self._walk(M.Tail(attempts)(), M.Tail(representatives)())

    def __call__(self):
        return self.result


class SameBudgetedSearchResults(M.Edge):
    def __init__(self, attempts):
        totals = L.AttemptTotals(attempts)()
        expansions = M.Head(D.HeadAt(totals, 0)())()
        if X.ReportingCountEquals(L.OutcomeCountAll(attempts)(), 34)() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.CheckedReachableTag()())(), 21
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.BudgetExhaustedTag()())(), 10
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.UnsupportedTag()())(), 3
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
        elif X.ReportingCountEquals(expansions, 361)() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CadenceIsFixed(M.Edge):
    def __init__(self, run):
        actual = X.SweepSeqText(X.RunSweepSeqs(run)())()
        self.result = M.Compare(M.Char(actual), M.Char("5,10,15,20,25,30,34"))()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GrammarIsDeclared(M.Edge):
    def __init__(self):
        grammar = X.ObserverGrammar()()
        if X.ReportingCountEquals(X.ChainCount(grammar)(), 2)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            X.ObserverDisplay(M.Head(grammar)())(), M.Char("Length")
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            X.ObserverDisplay(M.Head(M.Tail(grammar)())())(), M.Char("Parity(Length)")
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class FindRefutation(M.Edge):
    def __init__(self, refuted, observer_name, digest):
        self.result = self._scan(refuted, observer_name, digest)
        super().__init__(inputs=M.Pair(refuted, M.EmptyList), results=self.result)

    def _scan(self, refuted, observer_name, digest):
        if IsEmptyTerm(refuted)() is M.truth_value:
            return M.EmptyList
        item = M.Head(refuted)()
        observer = X.ObserverDisplay(X.RefutationObserverSpec(item)())()
        if M.Compare(observer, observer_name)() is M.truth_value:
            if M.Compare(X.RefutationDigest(item)(), digest)() is M.truth_value:
                return M.Pair(item, M.EmptyList)
        return self._scan(M.Tail(refuted)(), observer_name, digest)

    def __call__(self):
        return self.result


class LengthRetainsBrokenOn(M.Edge):
    def __init__(self, run):
        digest = D.RulesetVersionOfSpecs(D.REvenSpecs()())()
        found = FindRefutation(X.RunRefuted(run)(), M.Char("Length"), digest)()
        if IsEmptyTerm(found)() is M.truth_value:
            self.result = M.false_value
        else:
            refutation = M.Head(found)()
            broken_shell = X.TraceBrokenShell(X.RefutationTrace(refutation)())()
            if IsEmptyTerm(broken_shell)() is M.truth_value:
                self.result = M.false_value
            else:
                broken = M.Head(broken_shell)()
                transition = X.BrokenTransition(broken)()
                specs = D.REvenSpecs()()
                spec_shell = C.SpecWithDigest(
                    specs, X.TransitionRuleDigest(transition)()
                )()
                if IsEmptyTerm(spec_shell)() is M.truth_value:
                    self.result = M.false_value
                else:
                    move = D.ApplyRule(
                        M.Head(spec_shell)(), X.TransitionBefore(transition)()
                    )()
                    if D.IsAppliedOutcome(move)() is M.false_value:
                        self.result = M.false_value
                    elif M.Compare(
                        D.OutcomeAfter(move)(), X.TransitionAfter(transition)()
                    )() is M.false_value:
                        self.result = M.false_value
                    elif M.Compare(
                        X.BrokenPreReading(broken)(), X.BrokenPostReading(broken)()
                    )() is M.truth_value:
                        self.result = M.false_value
                    else:
                        self.result = M.truth_value
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AllCandidatesAreProvedParity(M.Edge):
    def __init__(self, candidates):
        self.result = self._walk(candidates)
        super().__init__(inputs=M.Pair(candidates, M.EmptyList), results=self.result)

    def _walk(self, candidates):
        if IsEmptyTerm(candidates)() is M.truth_value:
            return M.truth_value
        candidate = M.Head(candidates)()
        if M.Compare(
            X.ObserverDisplay(X.CandidateObserverSpec(candidate)())(),
            M.Char("Parity(Length)"),
        )() is M.false_value:
            return M.false_value
        if M.Compare(
            MC.VerdictStatus(X.CandidateCheckerVerdict(candidate)())(), MC.ProvedTag()()
        )() is M.false_value:
            return M.false_value
        return self._walk(M.Tail(candidates)())

    def __call__(self):
        return self.result


class ParityCandidatesAndProofs(M.Edge):
    def __init__(self, run):
        candidates = X.RunCandidates(run)()
        proved = X.RunProved(run)()
        if X.ReportingCountEquals(X.ChainCount(candidates)(), 3)() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(X.ChainCount(proved)(), 3)() is M.false_value:
            self.result = M.false_value
        else:
            self.result = AllCandidatesAreProvedParity(candidates)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EveryStepHasStatus(M.Edge):
    def __init__(self, evidence, status):
        self.result = self._walk(evidence, status)
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=self.result)

    def _walk(self, evidence, status):
        if IsEmptyTerm(evidence)() is M.truth_value:
            return M.truth_value
        if M.Compare(MC.StepStatus(M.Head(evidence)())(), status)() is M.false_value:
            return M.false_value
        return self._walk(M.Tail(evidence)(), status)

    def __call__(self):
        return self.result


class REvenParityChecksEveryRule(M.Edge):
    def __init__(self):
        observer = X.ObserverPattern(X.ParityLengthObserverSpec()())()
        verdict = MC.CheckObserverPreservation(observer, D.REvenSpecs()())()
        evidence = MC.VerdictEvidence(verdict)()
        if M.Compare(MC.VerdictStatus(verdict)(), MC.ProvedTag()())() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            MC.EvidenceCount(evidence)(), 3
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = EveryStepHasStatus(evidence, MC.PreservedTag()())()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EvidenceHasRefutedDisplay(M.Edge):
    def __init__(self, evidence, display):
        self.result = self._scan(evidence, display)
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=self.result)

    def _scan(self, evidence, display):
        if IsEmptyTerm(evidence)() is M.truth_value:
            return M.false_value
        step = M.Head(evidence)()
        if M.Compare(MC.StepRuleDisplay(step)(), display)() is M.truth_value:
            if M.Compare(MC.StepStatus(step)(), MC.RefutedTag()())() is M.truth_value:
                return M.truth_value
        return self._scan(M.Tail(evidence)(), display)

    def __call__(self):
        return self.result


class RPlusParityIsRefutedByAdd1(M.Edge):
    def __init__(self):
        observer = X.ObserverPattern(X.ParityLengthObserverSpec()())()
        verdict = MC.CheckObserverPreservation(observer, D.RPlusSpecs()())()
        evidence = MC.VerdictEvidence(verdict)()
        if M.Compare(MC.VerdictStatus(verdict)(), MC.RefutedTag()())() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            MC.EvidenceCount(evidence)(), 5
        )() is M.false_value:
            self.result = M.false_value
        elif EvidenceHasRefutedDisplay(evidence, M.Char("Add1Even"))() is M.false_value:
            self.result = M.false_value
        else:
            self.result = EvidenceHasRefutedDisplay(evidence, M.Char("Add1Odd"))()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class MissingObserverIsUnsupported(M.Edge):
    def __init__(self):
        absent = I.Phi(
            M.Pair(M.Char("AbsentObserver"), M.Pair(D.RuleVar("missing")(), M.EmptyList))
        )()
        verdict = MC.CheckObserverPreservation(absent, D.REvenSpecs()())()
        self.result = M.Compare(MC.VerdictStatus(verdict)(), MC.UnsupportedTag()())()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class FirstProved(M.Edge):
    def __init__(self, run):
        self.result = M.Head(X.RunProved(run)())()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ScopeMismatchIsFirst(M.Edge):
    def __init__(self, run):
        proved = FirstProved(run)()
        candidate = X.ProvedCandidate(proved)()
        certificate = X.ProvedCertificate(proved)()
        replay = MC.ReplayInvariantCertificate(
            certificate,
            X.ObserverPattern(X.CandidateObserverSpec(candidate)())(),
            D.RPlusSpecs()(),
        )()
        self.result = M.Compare(C.VerdictTag(replay)(), C.ScopeMismatchTag()())()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TamperedEvidenceFailsReplay(M.Edge):
    def __init__(self, run):
        proved = FirstProved(run)()
        candidate = X.ProvedCandidate(proved)()
        certificate = X.ProvedCertificate(proved)()
        tampered = C.CertificateRecord(
            C.CertificateKind(certificate)(),
            C.CertificateObserver(certificate)(),
            C.CertificateStart(certificate)(),
            C.CertificateGoal(certificate)(),
            C.CertificateDigest(certificate)(),
            C.CertificateVersion(certificate)(),
            M.EmptyList,
        )()
        replay = MC.ReplayInvariantCertificate(
            tampered,
            X.ObserverPattern(X.CandidateObserverSpec(candidate)())(),
            D.REvenSpecs()(),
        )()
        self.result = M.Compare(C.VerdictTag(replay)(), C.ReplayFailedTag()())()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AllProofsReplay(M.Edge):
    def __init__(self, proved, entries):
        self.result = self._walk(proved, entries)
        super().__init__(inputs=M.Pair(proved, M.EmptyList), results=self.result)

    def _entry(self, entries, digest):
        if IsEmptyTerm(entries)() is M.truth_value:
            return M.EmptyList
        if M.Compare(X.EntryDigest(M.Head(entries)())(), digest)() is M.truth_value:
            return M.Pair(M.Head(entries)(), M.EmptyList)
        return self._entry(M.Tail(entries)(), digest)

    def _walk(self, proved, entries):
        if IsEmptyTerm(proved)() is M.truth_value:
            return M.truth_value
        item = M.Head(proved)()
        candidate = X.ProvedCandidate(item)()
        found = self._entry(entries, X.CandidateDigest(candidate)())
        if IsEmptyTerm(found)() is M.truth_value:
            return M.false_value
        replay = MC.ReplayInvariantCertificate(
            X.ProvedCertificate(item)(),
            X.ObserverPattern(X.CandidateObserverSpec(candidate)())(),
            X.EntrySpecs(M.Head(found)())(),
        )()
        if C.IsReplayed(replay)() is M.false_value:
            return M.false_value
        return self._walk(M.Tail(proved)(), entries)

    def __call__(self):
        return self.result


class ProvedArchiveRecomputes(M.Edge):
    def __init__(self, run):
        entries = X.RulesetEntries(X.RunAttempts(run)())()
        self.result = AllProofsReplay(X.RunProved(run)(), entries)()
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NoG4Pruning(M.Edge):
    def __init__(self, run, here):
        lines = FileLines(os.path.join(here, "journals", "mining.jsonl"))()
        expected = M.Char(
            '{"record":"header","journal_layout":"researcher-v0-mining-journal/1",'
            '"attempt_layout":"researcher-v0-attempt/1","laboratory_version":"researcher-v0-laboratory/1",'
            '"checker_version":"researcher-v0-checker/1","condition":"MINING","mining":"on",'
            '"pruning":"off","task_set":"researcher_v0/tasks/tasks.jsonl",'
            '"task_set_blake2b":"b89ac1f5742ea7bbb03bffa59fc10efab7a4ab27b522edbc014d3448882ec90c",'
            '"delivered_rows":42,"canonical_tasks":34,"search":"breadth-first",'
            '"expansion_budget":32,"wall_clock_budget_ms_per_task":60000,"max_workers":1,'
            '"worker_id":"worker-0","seed":"deterministic-no-rng",'
            '"mining_interval_completed_tasks":5,"mining_sweeps":"5,10,15,20,25,30,34",'
            '"observer_grammar":"Length|Parity(Length)"}\n'
        )
        attempts = X.RunAttempts(run)()
        if IsEmptyTerm(lines)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(lines)(), expected)() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.UnsupportedTag()())(), 3
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            L.OutcomeCount(attempts, L.OpenResidualTag()())(), 0
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ArtifactLineCounts(M.Edge):
    def __init__(self, here):
        journal = FileLines(os.path.join(here, "journals", "mining.jsonl"))()
        candidates = FileLines(os.path.join(here, "candidates", "candidates.jsonl"))()
        proved = FileLines(
            os.path.join(here, "candidates", "proved_invariants.jsonl")
        )()
        refuted = FileLines(
            os.path.join(here, "candidates", "refuted_candidates.jsonl")
        )()
        if X.ReportingCountEquals(X.ChainCount(journal)(), 36)() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(X.ChainCount(candidates)(), 3)() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(X.ChainCount(proved)(), 3)() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(X.ChainCount(refuted)(), 5)() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ArtifactsCarryTraceableReasons(M.Edge):
    def __init__(self, run, here):
        candidates = FileText(os.path.join(here, "candidates", "candidates.jsonl"))()
        proved = FileText(
            os.path.join(here, "candidates", "proved_invariants.jsonl")
        )()
        refuted = FileText(
            os.path.join(here, "candidates", "refuted_candidates.jsonl")
        )()
        if M.Compare(
            M.Char(candidates), M.Char(X.CandidatesText(X.RunCandidates(run)())())
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Char(proved), M.Char(X.ProvedText(X.RunProved(run)())())
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Char(refuted), M.Char(X.RefutedText(X.RunRefuted(run)())())
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(run, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class G4Tests(M.Edge):
    def __init__(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kept = M.Head(G.DropExactDuplicates(G.GenerateAllRows()())())()
        representatives = L.CanonicalRepresentatives(kept)()
        run = X.MiningRun(
            representatives, L.EXPANSION_BUDGET, L.WALL_CLOCK_BUDGET_MS
        )()
        built = M.EmptyList
        built = ChainAppend(
            built,
            M.Pair(
                M.Char("delivered set and 34 canonical ids rebound"),
                DeliveredSetAndCanonicalIds(kept, representatives, here),
            ),
        )()
        built = ChainAppend(
            built,
            M.Pair(
                M.Char("every attempt binds the delivered representative order"),
                AttemptsBindRepresentatives(X.RunAttempts(run)(), representatives),
            ),
        )()
        built = ChainAppend(
            built,
            M.Pair(
                M.Char("MINING keeps BASELINE search totals"),
                SameBudgetedSearchResults(X.RunAttempts(run)()),
            ),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("miner cadence is fixed K=5 plus final tail"), CadenceIsFixed(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("observer grammar declares Length and Parity(Length)"), GrammarIsDeclared()),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("Length retains a replayable BrokenOn transition"), LengthRetainsBrokenOn(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("three parity trace survivors are proved candidates"), ParityCandidatesAndProofs(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("R_even parity checks all three exact rules"), REvenParityChecksEveryRule()),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("R_plus parity is refuted by both Add1 rules"), RPlusParityIsRefutedByAdd1()),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("missing observer readings classify UNSUPPORTED"), MissingObserverIsUnsupported()),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("invariant replay checks ruleset scope first"), ScopeMismatchIsFirst(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("tampered preservation evidence fails replay"), TamperedEvidenceFailsReplay(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("all proved archive entries recompute and replay"), ProvedArchiveRecomputes(run)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("G4 performs no invariant pruning"), NoG4Pruning(run, here)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("all four G4 JSONL archives have bounded counts"), ArtifactLineCounts(here)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("archives retain classifications and traceable reasons"), ArtifactsCarryTraceableReasons(run, here)),
        )()
        self.result = built
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result
