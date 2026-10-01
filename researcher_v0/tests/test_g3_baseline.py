"""Researcher-v0 / G3 tests — BASELINE laboratory run, checker, typed PENDING-REF.

Every test is an `Edge` class whose `result` is `truth_value` or
`false_value`; the list of tests is itself a chain (`G3Tests`), so no Python
container is used anywhere. Run, after the BASELINE run has written its
artifacts:

    python3 -m cat_theo_machine.researcher_v0.run_g3_baseline
    python3 -m cat_theo_machine.researcher_v0.tests.run_g3_tests

from the workspace root (the repository's parent directory). The test runner
writes nothing: it reads the journal and the certificate archive, and
recomputes in memory whatever it checks.

Coverage, against the brief's G3 text, A1/A2, and the G2 report §7 / §11:

* the journal header binds condition BASELINE (mining off), the budget, the
  worker count, the seed and the exact delivered task set;
* 34 canonical ids, each attempted exactly once; the members of every attempt
  cover all 42 delivered rows;
* every attempt records the brief's G3 fields;
* outcomes come from the BASELINE vocabulary only, and no unreachability
  result exists (A2.3: the expected baseline reading);
* every CHECKED_REACHABLE line cites a certificate that is re-minted with the
  same content-addressed id and replays in the experiment checker; the archive
  holds reachable-path certificates only;
* a timeout is not a counterexample, a crash is not a refutation, and
  UNSUPPORTED is distinct from budget exhaustion;
* typed PENDING-REF: T0043 (= T0044), T0045 and T0046 are UNSUPPORTED and
  unresolved, a parent's path certificate is refused by type, and each of the
  slot's four typed fields is checked;
* the standing acceptance item A2.1-R, `MissingPhiReadingIsNotChecked`;
* replay recomputes: scope mismatch comes first, a display rename keeps scope,
  tampered evidence fails;
* a full in-memory rerun reproduces the journal (timing masked) and the
  archive (byte for byte);
* inertness: the G3 modules hold no unreachability route; the G2 corpus is
  untouched.
"""

from __future__ import annotations

import hashlib
import os
import time

from ... import invariance as I
from ... import machine as M
from ... import proof as P
from .. import checker as C
from .. import laboratory as LAB
from .. import task_generation as G
from .. import token_domain as D
from ..chains import ChainAppend, IsEmptyTerm

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = os.path.dirname(HERE)

G1_R_PLUS_VERSION_TEXT = "533cb46bd134cd0c1bcaf87d03ba6b4a1a5395c331f1ba0f391921ed500d2b8d"


# --------------------------------------------------------------------------
# evidence readers (text at the reporting boundary)
# --------------------------------------------------------------------------


class SourceText(M.Edge):
    """Contents of a file that ships with this package."""

    def __init__(self, filename):
        handle = open(os.path.join(PACKAGE, filename))
        self.result = handle.read()
        handle.close()
        super().__init__(inputs=M.Pair(M.Char(filename), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TextContains(M.Edge):
    def __init__(self, text, needle):
        if needle in text:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(M.Char(needle), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TextCount(M.Edge):
    """Occurrences of `needle` in `text` (reporting)."""

    def __init__(self, text, needle):
        self.result = text.count(needle)
        super().__init__(inputs=M.Pair(M.Char(needle), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LineWith(M.Edge):
    """The first line of `text` containing `needle`, empty text when none does."""

    def __init__(self, text, needle):
        at = text.find(needle)
        if at < 0:
            self.result = ""
        else:
            begin = text.rfind("\n", 0, at) + 1
            end = text.find("\n", at)
            if end < 0:
                end = len(text)
            self.result = text[begin:end]
        super().__init__(inputs=M.Pair(M.Char(needle), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FieldText(M.Edge):
    """The JSON string value of `field` on one line, empty text when absent.

    The journal escapes nothing (its writer replaces quotes before writing), so
    the value ends at the next double quote.
    """

    def __init__(self, line, field):
        key = '"' + field + '": "'
        at = line.find(key)
        if at < 0:
            self.result = ""
        else:
            begin = at + len(key)
            self.result = line[begin:line.find('"', begin)]
        super().__init__(inputs=M.Pair(M.Char(field), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TaskLine(M.Edge):
    """The journal's attempt line for a task id text such as `T0043`."""

    def __init__(self, journal, task_id):
        self.result = LineWith(journal, '"task_id": "' + task_id + '"')()
        super().__init__(inputs=M.Pair(M.Char(task_id), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MaskTiming(M.Edge):
    """The text with every elapsed-milliseconds value replaced by `masked`."""

    def __init__(self, text):
        self.result = self._mask(self._mask(text, '"elapsed_ms": '), '"elapsed_ms_total": ')
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _mask(self, text, key):
        at = text.find(key)
        if at < 0:
            return text
        begin = at + len(key)
        end = begin
        while end < len(text) and text[end] in "0123456789":
            end = end + 1
        return text[:begin] + "masked" + self._mask(text[end:], key)

    def __call__(self):
        return self.result


class DiskJournal(M.Edge):
    def __init__(self):
        self.result = SourceText(os.path.join("journals", "baseline.jsonl"))()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DiskCertificates(M.Edge):
    def __init__(self):
        self.result = SourceText(
            os.path.join("certificates", "baseline_path_certificates.jsonl")
        )()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DeliveredText(M.Edge):
    def __init__(self):
        self.result = SourceText(os.path.join("tasks", "tasks.jsonl"))()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DeliveredDigest(M.Edge):
    """blake2b-256 hex of the delivered tasks.jsonl text."""

    def __init__(self):
        self.result = hashlib.blake2b(
            DeliveredText()().encode("utf-8"), digest_size=32
        ).hexdigest()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class FreshKept(M.Edge):
    """The delivered rows, regenerated (deterministic, G2 test 16)."""

    def __init__(self):
        self.result = M.Head(G.DropExactDuplicates(G.GenerateAllRows()())())()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Representative(M.Edge):
    """The representative entry of a serial within `representatives`."""

    def __init__(self, representatives, serial):
        self.result = LAB.RepresentativeBySerial(representatives, serial)()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class MintedCertificate(M.Edge):
    """Re-mint the path certificate of a query row: search, then bind."""

    def __init__(self, row):
        record = G.RowRecord(row)()
        search = LAB.BaselineSearch(
            record, LAB.EXPANSION_BUDGET, LAB.WALL_CLOCK_BUDGET_MS, time.perf_counter()
        )()
        path_shell = D.HeadAt(search, 3)()
        self.result = C.PathCertificate(record, M.Head(path_shell)())()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class WithSlot(M.Edge):
    """A copy of a certificate with the slot at `position` replaced."""

    def __init__(self, certificate, position, replacement):
        self.result = self._rebuild(certificate, position, replacement, 0)
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def _rebuild(self, chain, position, replacement, current):
        if IsEmptyTerm(chain)() is M.truth_value:
            return M.EmptyList
        if current == position:
            return M.Pair(replacement, M.Tail(chain)())
        return M.Pair(
            M.Head(chain)(),
            self._rebuild(M.Tail(chain)(), position, replacement, current + 1),
        )

    def __call__(self):
        return self.result


class VerdictIs(M.Edge):
    """Does a replay verdict carry the given tag?"""

    def __init__(self, verdict, tag):
        self.result = M.Compare(C.VerdictTag(verdict)(), tag)()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# tests
# --------------------------------------------------------------------------


class HeaderBindsRun(M.Edge):
    """The header binds BASELINE, mining off, budget, workers, seed and task set."""

    def __init__(self):
        header = LineWith(DiskJournal()(), '"record": "header"')()
        self.result = self._all(
            header,
            M.Pair(
                M.Char('"condition": "BASELINE"'),
                M.Pair(
                    M.Char('"mining": "off"'),
                    M.Pair(
                        M.Char('"expansion_budget": 32'),
                        M.Pair(
                            M.Char('"wall_clock_budget_ms_per_task": 60000'),
                            M.Pair(
                                M.Char('"max_workers": 1'),
                                M.Pair(
                                    M.Char('"seed": "none"'),
                                    M.Pair(
                                        M.Char('"checker_version": "researcher-v0-checker/1"'),
                                        M.Pair(
                                            M.Char('"delivered_rows": 42'),
                                            M.Pair(
                                                M.Char('"canonical_tasks": 34'),
                                                M.Pair(
                                                    M.Char(
                                                        '"task_set_blake2b": "'
                                                        + DeliveredDigest()()
                                                        + '"'
                                                    ),
                                                    M.EmptyList,
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
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _all(self, text, needles):
        if IsEmptyTerm(needles)() is M.truth_value:
            return M.truth_value
        if TextContains(text, M.Head(needles)()())() is M.false_value:
            return M.false_value
        return self._all(text, M.Tail(needles)())

    def __call__(self):
        return self.result


class CanonicalIdsOnceEach(M.Edge):
    """34 attempt lines; every delivered row's canonical id appears exactly once."""

    def __init__(self):
        journal = DiskJournal()()
        kept = FreshKept()()
        self.result = M.truth_value
        if TextCount(journal, '"record": "attempt"')() != 34:
            self.result = M.false_value
        if G.CountDistinctCanonical(kept)() != 34:
            self.result = M.false_value
        if self._each(journal, kept) is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _each(self, journal, rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.truth_value
        needle = '"canonical_id": "' + G.RowCanonicalId(M.Head(rows)())() + '"'
        if TextCount(journal, needle)() != 1:
            return M.false_value
        return self._each(journal, M.Tail(rows)())

    def __call__(self):
        return self.result


class MembersCoverDelivered(M.Edge):
    """Members of the 34 attempts cover the 42 delivered rows; 8 collapse groups."""

    def __init__(self):
        journal = DiskJournal()()
        kept = FreshKept()()
        representatives = LAB.CanonicalRepresentatives(kept)()
        walked = self._walk(journal, representatives, 0, 0)
        self.result = M.truth_value
        if M.Head(walked)() != G.CountRows(kept)():
            self.result = M.false_value
        if M.Head(M.Tail(walked)())() != 8:
            self.result = M.false_value
        if M.Head(M.Tail(M.Tail(walked)())())() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _walk(self, journal, representatives, members, groups):
        if IsEmptyTerm(representatives)() is M.truth_value:
            return M.Pair(members, M.Pair(groups, M.Pair(M.truth_value, M.EmptyList)))
        entry = M.Head(representatives)()
        text = D.HeadAt(entry, 1)()()
        task_id = "T" + "%04d" % G.RowSerial(M.Head(entry)())()
        line = TaskLine(journal, task_id)()
        if FieldText(line, "members")() != text:
            return M.Pair(members, M.Pair(groups, M.Pair(M.false_value, M.EmptyList)))
        grouped = 0
        if "," in text:
            grouped = 1
        return self._walk(
            journal,
            M.Tail(representatives)(),
            members + text.count(",") + 1,
            groups + grouped,
        )

    def __call__(self):
        return self.result


class AttemptFieldsRecorded(M.Edge):
    """Every attempt line records the brief's G3 fields; bindings recomputed."""

    def __init__(self):
        journal = DiskJournal()()
        names = M.Pair(M.Char("task_id"), M.Pair(M.Char("ruleset_version"), M.Pair(
            M.Char("start"), M.Pair(M.Char("goal"), M.Pair(M.Char("worker_id"),
            M.Pair(M.Char("attempt_id"), M.Pair(M.Char("outcome"), M.Pair(
                M.Char("expansions"), M.Pair(M.Char("elapsed_ms"), M.Pair(
                    M.Char("certificate_id"), M.Pair(
                        M.Char("counterexample_id"), M.EmptyList)))))))))))
        representatives = LAB.CanonicalRepresentatives(FreshKept()())()
        self.result = M.truth_value
        if TextCount(journal, '"ruleset_version": ""')() != 0:
            self.result = M.false_value
        if self._lines(journal, representatives, names) is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _lines(self, journal, representatives, names):
        if IsEmptyTerm(representatives)() is M.truth_value:
            return M.truth_value
        row = M.Head(M.Head(representatives)())()
        record = G.RowRecord(row)()
        task_id = "T" + "%04d" % G.RowSerial(row)()
        line = TaskLine(journal, task_id)()
        if self._fields(line, names) is M.false_value:
            return M.false_value
        if FieldText(line, "ruleset_version")() != G.RowRulesetVersion(row)()():
            return M.false_value
        if FieldText(line, "start")() != C.StateText(G.TaskStart(record)())()():
            return M.false_value
        if FieldText(line, "goal")() != C.StateText(G.TaskGoal(record)())()():
            return M.false_value
        if FieldText(line, "attempt_id")() != "BASELINE:" + task_id + ":1":
            return M.false_value
        if FieldText(line, "worker_id")() != "worker-0":
            return M.false_value
        return self._lines(journal, M.Tail(representatives)(), names)

    def _fields(self, line, names):
        if IsEmptyTerm(names)() is M.truth_value:
            return M.truth_value
        if TextContains(line, '"' + M.Head(names)()() + '": ')() is M.false_value:
            return M.false_value
        return self._fields(line, M.Tail(names)())

    def __call__(self):
        return self.result


class BaselineVocabularyOnly(M.Edge):
    """Five-label vocabulary; zero unreachability results (A2.3 reading)."""

    def __init__(self):
        journal = DiskJournal()()
        total = (
            TextCount(journal, '"outcome": "CHECKED_REACHABLE"')()
            + TextCount(journal, '"outcome": "OPEN_RESIDUAL"')()
            + TextCount(journal, '"outcome": "UNSUPPORTED"')()
            + TextCount(journal, '"outcome": "BUDGET_EXHAUSTED"')()
            + TextCount(journal, '"outcome": "EXECUTION_FAILURE"')()
        )
        self.result = M.truth_value
        if total != 34:
            self.result = M.false_value
        if TextCount(journal, '"outcome": "')() != 34:
            self.result = M.false_value
        if TextCount(journal, "CHECKED_UNREACHABLE")() != 0:
            self.result = M.false_value
        if LAB.IsBaselineOutcome(M.Char("CHECKED_UNREACHABLE"))() is M.truth_value:
            self.result = M.false_value
        if LAB.IsBaselineOutcome(LAB.UnsupportedTag()())() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ReachableCitesReplayedCertificate(M.Edge):
    """Each CHECKED_REACHABLE line cites a re-mintable, replaying certificate."""

    def __init__(self):
        journal = DiskJournal()()
        archive = DiskCertificates()()
        representatives = LAB.CanonicalRepresentatives(FreshKept()())()
        walked = self._walk(journal, archive, representatives, 0)
        self.result = M.Head(walked)()
        reachable = M.Head(M.Tail(walked)())()
        if reachable != TextCount(journal, '"outcome": "CHECKED_REACHABLE"')():
            self.result = M.false_value
        if TextCount(archive, "\n")() != reachable:
            self.result = M.false_value
        if TextCount(archive, '"replay": "REPLAYED"')() != reachable:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _walk(self, journal, archive, representatives, reachable):
        if IsEmptyTerm(representatives)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(reachable, M.EmptyList))
        row = M.Head(M.Head(representatives)())()
        line = TaskLine(journal, "T" + "%04d" % G.RowSerial(row)())()
        cited = FieldText(line, "certificate_id")()
        if FieldText(line, "outcome")() != "CHECKED_REACHABLE":
            if cited != "":
                return M.Pair(M.false_value, M.Pair(reachable, M.EmptyList))
            return self._walk(journal, archive, M.Tail(representatives)(), reachable)
        certificate = MintedCertificate(row)()
        if C.CertificateId(certificate)()() != cited:
            return M.Pair(M.false_value, M.Pair(reachable, M.EmptyList))
        verdict = C.ReplayPathCertificate(certificate, G.RowRecord(row)())()
        if C.IsReplayed(verdict)() is M.false_value:
            return M.Pair(M.false_value, M.Pair(reachable, M.EmptyList))
        if TextCount(archive, '"certificate_id": "' + cited + '"')() != 1:
            return M.Pair(M.false_value, M.Pair(reachable, M.EmptyList))
        entry_line = LineWith(archive, '"certificate_id": "' + cited + '"')()
        if FieldText(entry_line, "replay")() != "REPLAYED":
            return M.Pair(M.false_value, M.Pair(reachable, M.EmptyList))
        return self._walk(journal, archive, M.Tail(representatives)(), reachable + 1)

    def __call__(self):
        return self.result


class PathCertificatesOnly(M.Edge):
    """The archive holds reachable-path certificates only; none is of another kind."""

    def __init__(self):
        archive = DiskCertificates()()
        lines = TextCount(archive, "\n")()
        self.result = M.truth_value
        if lines != 21:
            self.result = M.false_value
        if TextCount(archive, '"kind": "reachable-path"')() != lines:
            self.result = M.false_value
        if TextCount(archive, '"observer": ""')() != lines:
            self.result = M.false_value
        if TextCount(archive, '"kind": "')() != lines:
            self.result = M.false_value
        if TextContains(archive, "proved-invariant")() is M.truth_value:
            self.result = M.false_value
        if TextContains(archive.lower(), "unreachab")() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class TimeoutIsNotCounterexample(M.Edge):
    """BUDGET_EXHAUSTED cites nothing; both budget dimensions exhaust cleanly."""

    def __init__(self):
        journal = DiskJournal()()
        self.result = M.truth_value
        if TextCount(journal, '"counterexample_id": ""')() != 34:
            self.result = M.false_value
        exhausted = TextCount(journal, '"outcome": "BUDGET_EXHAUSTED"')()
        if TextCount(
            journal,
            '"outcome": "BUDGET_EXHAUSTED", "expansions": 32',
        )() != exhausted:
            self.result = M.false_value
        representatives = LAB.CanonicalRepresentatives(FreshKept()())()
        entry = Representative(representatives, 7)()
        tight = LAB.BaselineAttempt(1, entry, M.EmptyList, 1, LAB.WALL_CLOCK_BUDGET_MS)()
        if self._clean(tight) is M.false_value:
            self.result = M.false_value
        if LAB.AttemptExpansions(tight)() != 1:
            self.result = M.false_value
        clock = LAB.BaselineAttempt(1, entry, M.EmptyList, LAB.EXPANSION_BUDGET, 0)()
        if self._clean(clock) is M.false_value:
            self.result = M.false_value
        if TextContains(LAB.AttemptReason(clock)()(), "wall-clock")() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _clean(self, attempt):
        if M.Compare(LAB.AttemptOutcome(attempt)(), LAB.BudgetExhaustedTag()())() is M.false_value:
            return M.false_value
        if IsEmptyTerm(LAB.AttemptCertificateShell(attempt)())() is M.false_value:
            return M.false_value
        if TextContains(LAB.AttemptJson(attempt)(), '"counterexample_id": ""')() is M.false_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class CrashIsNotRefutation(M.Edge):
    """A malformed task crashes into EXECUTION_FAILURE, citing nothing."""

    def __init__(self):
        record = G.TaskRecord(
            G.ReachabilityKind()(),
            D.StateOfCount(0)(),
            D.StateOfCount(2)(),
            M.Pair(M.Char("malformed spec"), M.EmptyList),
            M.EmptyList,
            M.EmptyList,
        )()
        row = G.TaskRow(99, 0, "fixture", "fixture", "fixture", "", "", record)()
        entry = M.Pair(row, M.Pair(M.Char("T0099"), M.EmptyList))
        attempt = LAB.BaselineAttempt(1, entry, M.EmptyList, LAB.EXPANSION_BUDGET, LAB.WALL_CLOCK_BUDGET_MS)()
        line = LAB.AttemptJson(attempt)()
        self.result = M.truth_value
        if M.Compare(LAB.AttemptOutcome(attempt)(), LAB.ExecutionFailureTag()())() is M.false_value:
            self.result = M.false_value
        if IsEmptyTerm(LAB.AttemptCertificateShell(attempt)())() is M.false_value:
            self.result = M.false_value
        if IsEmptyTerm(LAB.AttemptPendingShell(attempt)())() is M.false_value:
            self.result = M.false_value
        if TextContains(LAB.AttemptReason(attempt)()(), "crash, not a refutation")() is M.false_value:
            self.result = M.false_value
        if TextContains(line, '"certificate_id": "", "counterexample_id": ""')() is M.false_value:
            self.result = M.false_value
        if TextContains(line, "CHECKED")() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class UnsupportedDistinctFromBudget(M.Edge):
    """UNSUPPORTED rows are the scope-break rows, at zero expansions."""

    def __init__(self):
        journal = DiskJournal()()
        self.result = M.truth_value
        if M.Compare(LAB.UnsupportedTag()(), LAB.BudgetExhaustedTag()())() is M.truth_value:
            self.result = M.false_value
        unsupported = TextCount(journal, '"outcome": "UNSUPPORTED"')()
        if unsupported != 3:
            self.result = M.false_value
        if TextCount(journal, '"outcome": "UNSUPPORTED", "expansions": 0,')() != unsupported:
            self.result = M.false_value
        if TextCount(journal, '"kind": "scope_break_test"')() != unsupported:
            self.result = M.false_value
        if self._scope_rows(journal, M.Pair(M.Char("T0043"), M.Pair(M.Char("T0045"), M.Pair(M.Char("T0046"), M.EmptyList)))) is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _scope_rows(self, journal, ids):
        if IsEmptyTerm(ids)() is M.truth_value:
            return M.truth_value
        line = TaskLine(journal, M.Head(ids)()())()
        if FieldText(line, "kind")() != "scope_break_test":
            return M.false_value
        if FieldText(line, "outcome")() != "UNSUPPORTED":
            return M.false_value
        return self._scope_rows(journal, M.Tail(ids)())

    def __call__(self):
        return self.result


class PendingRefTypedInJournal(M.Edge):
    """T0043 (= T0044), T0045, T0046: UNSUPPORTED, unresolved, refusals recorded."""

    def __init__(self):
        journal = DiskJournal()()
        first = TaskLine(journal, "T0043")()
        fourth = TaskLine(journal, "T0045")()
        fifth = TaskLine(journal, "T0046")()
        parent_one = FieldText(TaskLine(journal, "T0001")(), "certificate_id")()
        parent_four = FieldText(TaskLine(journal, "T0004")(), "certificate_id")()
        self.result = M.truth_value
        if FieldText(first, "members")() != "T0043,T0044":
            self.result = M.false_value
        if TextCount(journal, '"task_id": "T0044"')() != 0:
            self.result = M.false_value
        if FieldText(first, "pending_ref")() != "pending:T0001":
            self.result = M.false_value
        if FieldText(fourth, "pending_ref")() != "pending:T0004":
            self.result = M.false_value
        if FieldText(fifth, "pending_ref")() != "pending:T0005":
            self.result = M.false_value
        if TextCount(journal, '"pending_resolution": "unresolved"')() != 3:
            self.result = M.false_value
        if TextCount(journal, '"pending_resolution": "resolved')() != 0:
            self.result = M.false_value
        if parent_one == "":
            self.result = M.false_value
        if parent_four == "":
            self.result = M.false_value
        if TextContains(FieldText(first, "rejected_by_type")(), parent_one + ": kind reachable-path is not proved-invariant")() is M.false_value:
            self.result = M.false_value
        if TextContains(FieldText(fourth, "rejected_by_type")(), parent_four + ": kind reachable-path is not proved-invariant")() is M.false_value:
            self.result = M.false_value
        if FieldText(fifth, "rejected_by_type")() != "":
            self.result = M.false_value
        if FieldText(TaskLine(journal, "T0005")(), "outcome")() != "BUDGET_EXHAUSTED":
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PendingRefTypedResolution(M.Edge):
    """A path certificate never fills the slot; each of the four fields is checked.

    The positive control is an in-memory fixture shaped like the slot. It is
    never archived, never written, and never replayed: it shows the four typed
    comparisons are live, so an unresolved slot is a finding, not a resolver
    that cannot say yes.
    """

    def __init__(self):
        kept = FreshKept()()
        representatives = LAB.CanonicalRepresentatives(kept)()
        scope_row = M.Head(Representative(representatives, 43)())()
        parent_row = M.Head(Representative(representatives, 1)())()
        slot = C.PendingSlot(scope_row)()
        path = MintedCertificate(parent_row)()
        record = G.RowRecord(scope_row)()
        fixture = C.CertificateRecord(
            C.InvariantSlotKind()(),
            D.HeadAt(slot, 1)(),
            G.TaskStart(record)(),
            G.TaskGoal(record)(),
            D.HeadAt(slot, 2)(),
            C.CheckerVersion()(),
            M.EmptyList,
        )()
        self.result = M.truth_value
        mismatch = C.SlotMismatch(slot, path)()
        if IsEmptyTerm(mismatch)() is M.truth_value:
            self.result = M.false_value
        elif M.Head(mismatch)()() != "kind reachable-path is not proved-invariant":
            self.result = M.false_value
        if IsEmptyTerm(C.SlotMismatch(slot, fixture)())() is M.false_value:
            self.result = M.false_value
        if self._each_field_checked(slot, fixture) is M.false_value:
            self.result = M.false_value
        path_entry = C.ArchiveEntry(C.CertificateId(path)(), path, M.Char("T0001"))()
        unresolved = C.ResolvePendingRef(scope_row, M.Pair(path_entry, M.EmptyList))()
        if IsEmptyTerm(M.Head(unresolved)())() is M.false_value:
            self.result = M.false_value
        rejected = D.HeadAt(unresolved, 1)()
        if IsEmptyTerm(rejected)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(M.Head(rejected)())(), C.CertificateId(path)())() is M.false_value:
            self.result = M.false_value
        fixture_entry = C.ArchiveEntry(C.CertificateId(fixture)(), fixture, M.Char("fixture"))()
        resolved = C.ResolvePendingRef(
            scope_row, M.Pair(path_entry, M.Pair(fixture_entry, M.EmptyList))
        )()
        if IsEmptyTerm(M.Head(resolved)())() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(M.Head(resolved)())(), C.CertificateId(fixture)())() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _each_field_checked(self, slot, fixture):
        if IsEmptyTerm(C.SlotMismatch(slot, WithSlot(fixture, 0, C.PathKind()())())())() is M.truth_value:
            return M.false_value
        if IsEmptyTerm(C.SlotMismatch(slot, WithSlot(fixture, 1, M.EmptyList)())())() is M.truth_value:
            return M.false_value
        if IsEmptyTerm(C.SlotMismatch(slot, WithSlot(fixture, 4, M.Char(G1_R_PLUS_VERSION_TEXT))())())() is M.truth_value:
            return M.false_value
        if IsEmptyTerm(C.SlotMismatch(slot, WithSlot(fixture, 5, M.Char("researcher-v0-checker/0"))())())() is M.truth_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class MissingPhiReadingIsNotChecked(M.Edge):
    """A2.1-R: a missing reading is NOT_CHECKED, never false, never a differing value.

    The goal state lacks the Parity fact, so `invariance.PhiReading` returns
    `EmptyList` there. A naive comparison of the two readings says "different"
    (shown below as evidence of the hole); the guard reports NOT_CHECKED on
    either side, and its verdict never separates the endpoints. Two present
    readings still compare: 0 -> 3 separates, 0 -> 2 reads the same.
    """

    def __init__(self):
        phi = G.ParityObserverPattern()()
        start = D.StateOfCount(0)()
        missing = P.Knowledge(
            M.Pair(D.TokensFact(D.PeanoFromInt(1)())(), M.EmptyList)
        )()
        self.result = M.truth_value
        if IsEmptyTerm(I.PhiReading(missing, phi)())() is M.false_value:
            self.result = M.false_value
        if M.Compare(I.PhiReading(start, phi)(), I.PhiReading(missing, phi)())() is M.truth_value:
            self.result = M.false_value
        goal_side = C.ObserverReadings(start, missing, phi)()
        start_side = C.ObserverReadings(missing, start, phi)()
        if self._not_checked(goal_side, I.PhiReading(start, phi)()) is M.false_value:
            self.result = M.false_value
        if self._not_checked(start_side, I.PhiReading(start, phi)()) is M.false_value:
            self.result = M.false_value
        present = C.ReadingsVerdict(C.ObserverReadings(start, D.StateOfCount(3)(), phi)())()
        if M.Compare(present, C.SeparatesTag()())() is M.false_value:
            self.result = M.false_value
        same = C.ReadingsVerdict(C.ObserverReadings(start, D.StateOfCount(2)(), phi)())()
        if M.Compare(same, C.SameReadingTag()())() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _not_checked(self, readings, present_reading):
        if M.Compare(M.Head(readings)(), C.NotCheckedTag()())() is M.false_value:
            return M.false_value
        if M.Compare(readings, M.false_value)() is M.truth_value:
            return M.false_value
        if M.Compare(readings, present_reading)() is M.truth_value:
            return M.false_value
        verdict = C.ReadingsVerdict(readings)()
        if M.Compare(verdict, C.NotCheckedTag()())() is M.false_value:
            return M.false_value
        if M.Compare(verdict, C.SeparatesTag()())() is M.truth_value:
            return M.false_value
        if M.Compare(verdict, M.false_value)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class ReplayRecomputes(M.Edge):
    """Scope first; display rename keeps scope; tampered evidence fails."""

    def __init__(self):
        kept = FreshKept()()
        representatives = LAB.CanonicalRepresentatives(kept)()
        seed_one = M.Head(Representative(representatives, 1)())()
        seed_two = M.Head(Representative(representatives, 2)())()
        certificate = MintedCertificate(seed_one)()
        two_steps = MintedCertificate(seed_two)()
        steps = C.CertificateEvidence(two_steps)()
        first = M.Head(steps)()
        self.result = M.truth_value
        if VerdictIs(C.ReplayPathCertificate(certificate, G.RowRecord(G.RowBySerial(kept, 10)())())(), C.ScopeMismatchTag()())() is M.false_value:
            self.result = M.false_value
        if VerdictIs(C.ReplayPathCertificate(certificate, G.RowRecord(G.RowBySerial(kept, 11)())())(), C.ScopeMismatchTag()())() is M.false_value:
            self.result = M.false_value
        if VerdictIs(C.ReplayPathCertificate(certificate, G.RowRecord(G.RowBySerial(kept, 12)())())(), C.ReplayedTag()())() is M.false_value:
            self.result = M.false_value
        if VerdictIs(C.ReplayPathCertificate(certificate, G.RowRecord(seed_two)())(), C.ReplayFailedTag()())() is M.false_value:
            self.result = M.false_value
        wrong_state = WithSlot(
            two_steps,
            6,
            M.Pair(C.PathStep(C.StepRuleDigest(first)(), D.StateOfCount(4)())(), M.Tail(steps)()),
        )()
        if VerdictIs(C.ReplayPathCertificate(wrong_state, G.RowRecord(seed_two)())(), C.ReplayFailedTag()())() is M.false_value:
            self.result = M.false_value
        foreign_rule = WithSlot(
            two_steps,
            6,
            M.Pair(
                C.PathStep(D.RuleFingerprintOfSpec(D.RuleSpec(M.Char("Add1Even"), D.Add1EvenRule()())())(), C.StepAfter(first)())(),
                M.Tail(steps)(),
            ),
        )()
        if VerdictIs(C.ReplayPathCertificate(foreign_rule, G.RowRecord(seed_two)())(), C.ReplayFailedTag()())() is M.false_value:
            self.result = M.false_value
        old_checker = WithSlot(two_steps, 5, M.Char("researcher-v0-checker/0"))()
        if VerdictIs(C.ReplayPathCertificate(old_checker, G.RowRecord(seed_two)())(), C.ReplayFailedTag()())() is M.false_value:
            self.result = M.false_value
        other_kind = WithSlot(two_steps, 0, C.InvariantSlotKind()())()
        if VerdictIs(C.ReplayPathCertificate(other_kind, G.RowRecord(seed_two)())(), C.ReplayFailedTag()())() is M.false_value:
            self.result = M.false_value
        if VerdictIs(C.ReplayPathCertificate(two_steps, G.RowRecord(seed_two)())(), C.ReplayedTag()())() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RerunReproducesArtifacts(M.Edge):
    """A full in-memory BASELINE rerun reproduces the journal and the archive.

    The journal comparison masks the elapsed-milliseconds values only; the
    archive holds no timing and must match byte for byte.
    """

    def __init__(self):
        kept = FreshKept()()
        run = LAB.BaselineRun(
            LAB.CanonicalRepresentatives(kept)(),
            LAB.EXPANSION_BUDGET,
            LAB.WALL_CLOCK_BUDGET_MS,
        )()
        attempts = M.Head(run)()
        journal = LAB.JournalText(
            attempts,
            DeliveredDigest()(),
            G.CountRows(kept)(),
            G.CountDistinctCanonical(kept)(),
            LAB.EXPANSION_BUDGET,
            LAB.WALL_CLOCK_BUDGET_MS,
        )()
        self.result = M.truth_value
        if MaskTiming(journal)() != MaskTiming(DiskJournal()())():
            self.result = M.false_value
        if LAB.CertificatesText(attempts)() != DiskCertificates()():
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class InertnessNoUnreachabilityRoute(M.Edge):
    """The G3 modules hold no unreachability route and touch no live path.

    Code tokens are guarded, not prose: the modules may say that they issue no
    such verdict, and may not contain one.
    """

    def __init__(self):
        self.result = self._file(
            M.Pair(M.Char("laboratory.py"), M.Pair(M.Char("checker.py"), M.Pair(M.Char("run_g3_baseline.py"), M.EmptyList)))
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _file(self, files):
        if IsEmptyTerm(files)() is M.truth_value:
            return M.truth_value
        text = SourceText(M.Head(files)()())()
        if self._forbidden(
            text,
            M.Pair(M.Char("CHECKED_UNREACHABLE"), M.Pair(M.Char("Unreachable("), M.Pair(
                M.Char("ReachabilityPrune("), M.Pair(M.Char("IsUnreachable("), M.Pair(
                    M.Char("UnreachableLabel"), M.Pair(M.Char("IsInvariant("), M.Pair(
                        M.Char("I.Invariant("), M.Pair(M.Char("Preserves("), M.Pair(
                            M.Char("programme_c"), M.Pair(M.Char("import graph"), M.Pair(
                                M.Char("import search"), M.EmptyList))))))))))),
        ) is M.false_value:
            return M.false_value
        return self._file(M.Tail(files)())

    def _forbidden(self, text, needles):
        if IsEmptyTerm(needles)() is M.truth_value:
            return M.truth_value
        if TextContains(text, M.Head(needles)()())() is M.truth_value:
            return M.false_value
        return self._forbidden(text, M.Tail(needles)())

    def __call__(self):
        return self.result


class TaskSetUntouched(M.Edge):
    """The delivered corpus is the one the journal binds, and still regenerates."""

    def __init__(self):
        delivered = DeliveredText()()
        self.result = M.truth_value
        if TextContains(DiskJournal()(), '"task_set_blake2b": "' + DeliveredDigest()() + '"')() is M.false_value:
            self.result = M.false_value
        if G.RowsToJsonl(FreshKept()())() != delivered:
            self.result = M.false_value
        if TextContains(delivered, "outcome")() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class G3Tests(M.Edge):
    """The G3 test chain: `Pair(name, test class)` in run order."""

    def __init__(self):
        built = M.EmptyList
        built = ChainAppend(built, M.Pair(M.Char("journal: header binds BASELINE, budget, workers, seed, task set"), HeaderBindsRun))()
        built = ChainAppend(built, M.Pair(M.Char("journal: 34 canonical ids, each attempted exactly once"), CanonicalIdsOnceEach))()
        built = ChainAppend(built, M.Pair(M.Char("journal: members cover the 42 delivered rows"), MembersCoverDelivered))()
        built = ChainAppend(built, M.Pair(M.Char("journal: every attempt records the G3 fields"), AttemptFieldsRecorded))()
        built = ChainAppend(built, M.Pair(M.Char("outcomes: BASELINE vocabulary, zero unreachability (A2.3)"), BaselineVocabularyOnly))()
        built = ChainAppend(built, M.Pair(M.Char("certificates: each CHECKED_REACHABLE cites a replaying certificate"), ReachableCitesReplayedCertificate))()
        built = ChainAppend(built, M.Pair(M.Char("certificates: reachable-path only"), PathCertificatesOnly))()
        built = ChainAppend(built, M.Pair(M.Char("budget: a timeout is not a counterexample"), TimeoutIsNotCounterexample))()
        built = ChainAppend(built, M.Pair(M.Char("failure: a crash is not a refutation"), CrashIsNotRefutation))()
        built = ChainAppend(built, M.Pair(M.Char("outcomes: UNSUPPORTED is distinct from BUDGET_EXHAUSTED"), UnsupportedDistinctFromBudget))()
        built = ChainAppend(built, M.Pair(M.Char("PENDING-REF: T0043=T0044, T0045, T0046 unresolved"), PendingRefTypedInJournal))()
        built = ChainAppend(built, M.Pair(M.Char("PENDING-REF: typed resolution, four fields checked"), PendingRefTypedResolution))()
        built = ChainAppend(built, M.Pair(M.Char("A2.1-R: MissingPhiReadingIsNotChecked"), MissingPhiReadingIsNotChecked))()
        built = ChainAppend(built, M.Pair(M.Char("replay: scope first, rename keeps scope, tampering fails"), ReplayRecomputes))()
        built = ChainAppend(built, M.Pair(M.Char("rerun: journal (timing masked) and archive reproduce"), RerunReproducesArtifacts))()
        built = ChainAppend(built, M.Pair(M.Char("inertness: no unreachability route in G3 modules"), InertnessNoUnreachabilityRoute))()
        built = ChainAppend(built, M.Pair(M.Char("corpus: tasks.jsonl bound and untouched"), TaskSetUntouched))()
        self.result = built
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result
