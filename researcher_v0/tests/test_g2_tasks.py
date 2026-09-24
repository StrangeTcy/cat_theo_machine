"""Researcher-v0 / G2 tests — generation, canonicalization, bindings.

Every test is an `Edge` class whose `result` is `truth_value` or
`false_value`; the list of tests is itself a chain (`G2Tests`), so no Python
container is used anywhere. Run:

    python3 -m cat_theo_machine.researcher_v0.tests.run_g2_tests

from the workspace root (the repository's parent directory). The runner first
writes `researcher_v0/tasks/tasks.jsonl` from the generator, then runs this
chain.

Coverage, against the G2 task text and the G1 review hold-points:

* minimums: >= 30 generated tasks, >= 10 non-isomorphic canonical tasks,
  delivered rows >= 30;
* zero outcome fields in tasks.jsonl (a populated outcome at G2 is a scope
  breach, not progress: tasks generated is not tasks run);
* every row records parent task id and perturbation reason (seeds record
  `none` / `seed` explicitly);
* display renaming collapses to the parent's canonical id and preserves the
  ruleset digest (brief acceptance test 2, A1.2) — without widening the G1
  semantic/display partition;
* exact duplicates are dropped with the drop recorded, and delivered rows are
  pairwise non-exact;
* goal perturbations change the canonical id and keep the ruleset digest;
  rule-content perturbations change both;
* ruleset_version is bound to the G1 content digest of the row's exact ruleset
  (R_even / R_plus values quoted from G1 report §4), never to a display name;
* task ids and counts stay at the reporting boundary: shells ride as
  `Pair(value, EmptyList)`, record terms hold no integer payload, and no task
  id appears in canonical content;
* scope-break rows name PENDING certificate references only — no certificate
  is produced at G2;
* inertness: the generation module holds no checker and no outcome vocabulary.
"""

from __future__ import annotations

import os

from ... import machine as M
from .. import ruleset_digest as RD
from .. import token_domain as D
from .. import task_generation as G
from ..chains import ChainAppend, IsEmptyTerm

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = os.path.dirname(HERE)

G1_R_EVEN_VERSION_TEXT = "15f5467c985c4dd9710e87b59b69788f3e2b23fb25f5320015589da844d2d68f"
G1_R_PLUS_VERSION_TEXT = "533cb46bd134cd0c1bcaf87d03ba6b4a1a5395c331f1ba0f391921ed500d2b8d"


class SourceText(M.Edge):
    """Contents of a file that ships with this package (evidence and guards)."""

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
        super().__init__(
            inputs=M.Pair(M.Char(needle), M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class TextCount(M.Edge):
    """Occurrences of `needle` in `text` (reporting)."""

    def __init__(self, text, needle):
        self.result = text.count(needle)
        super().__init__(
            inputs=M.Pair(M.Char(needle), M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class DeliveredText(M.Edge):
    """The delivered tasks.jsonl text."""

    def __init__(self):
        self.result = SourceText(os.path.join("tasks", "tasks.jsonl"))()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class FreshRows(M.Edge):
    """A fresh generation pass (deterministic)."""

    def __init__(self):
        self.result = G.GenerateAllRows()()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class FreshSplit(M.Edge):
    """`Pair(survivors, Pair(drops, EmptyList))` of a fresh generation pass."""

    def __init__(self):
        self.result = G.DropExactDuplicates(FreshRows()())()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class FreshKept(M.Edge):
    def __init__(self):
        self.result = M.Head(FreshSplit()())()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class FreshDrops(M.Edge):
    def __init__(self):
        self.result = M.Head(M.Tail(FreshSplit()())())()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RowParent(M.Edge):
    """The delivered parent row of a row (EmptyList when there is none)."""

    def __init__(self, row):
        self.result = G.RowBySerial(FreshKept()(), G.RowParentSerial(row)())()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GeneratedMinimums(M.Edge):
    """At least 30 generated tasks and at least 10 non-isomorphic canonical tasks."""

    def __init__(self):
        rows = FreshRows()()
        kept = FreshKept()()
        self.result = M.truth_value
        if G.CountRows(rows)() < 30:
            self.result = M.false_value
        if G.CountDistinctCanonical(kept)() < 10:
            self.result = M.false_value

    def __call__(self):
        return self.result


class DeliveredRowMinimum(M.Edge):
    """tasks.jsonl carries at least 30 rows."""

    def __init__(self):
        if TextCount(DeliveredText()(), "\n")() < 30:
            self.result = M.false_value
        else:
            self.result = M.truth_value

    def __call__(self):
        return self.result


class ZeroOutcomeFields(M.Edge):
    """tasks.jsonl holds no outcome field and no outcome vocabulary.

    G2 generates tasks and runs none. Any of these tokens in the deliverable
    would be a populated or expressible outcome at G2 — a scope breach.
    """

    def __init__(self):
        self.result = self._scan(
            DeliveredText()(),
            M.Pair(
                M.Char("outcome"),
                M.Pair(
                    M.Char("CHECKED"),
                    M.Pair(
                        M.Char("OPEN_RESIDUAL"),
                        M.Pair(
                            M.Char("BUDGET_EXHAUSTED"),
                            M.Pair(
                                M.Char("EXECUTION_FAILURE"),
                                M.Pair(
                                    M.Char("UNSUPPORTED"),
                                    M.Pair(
                                        M.Char("SCOPE_MISMATCH"),
                                        M.Pair(
                                            M.Char('"status"'),
                                            M.Pair(
                                                M.Char('"result"'),
                                                M.Pair(
                                                    M.Char("certificate_id"),
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

    def _scan(self, text, needles):
        if IsEmptyTerm(needles)() is M.truth_value:
            return M.truth_value
        if TextContains(text, M.Head(needles)()())() is M.truth_value:
            return M.false_value
        return self._scan(text, M.Tail(needles)())

    def __call__(self):
        return self.result


class ParentAndReasonRecorded(M.Edge):
    """Every delivered row records a parent task id and a perturbation reason."""

    def __init__(self):
        text = DeliveredText()()
        lines = TextCount(text, "\n")()
        self.result = M.truth_value
        if TextCount(text, '"parent_task_id": "')() != lines:
            self.result = M.false_value
        if TextCount(text, '"perturbation_reason": "')() != lines:
            self.result = M.false_value
        if TextCount(text, '"parent_task_id": "none"')() < 1:
            self.result = M.false_value
        if TextCount(text, '"perturbation_reason": "seed"')() < 1:
            self.result = M.false_value

    def __call__(self):
        return self.result


class RenameCollapsesCanonicalId(M.Edge):
    """Every display-renamed row collapses onto an unrenamed twin's canonical id.

    Brief acceptance test 2. The rename touches only the display slot G1
    declared cosmetic, so the canonical id cannot change and the ruleset
    digest cannot change: the renamed row shares the canonical id of the row
    carrying the same content with plain labels (its parent, for the family
    renames). No new canonical id is created by a rename.
    """

    def __init__(self):
        rows = FreshKept()()
        self.result = self._scan(rows, rows)

    def _scan(self, rows, all_rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.truth_value
        row = M.Head(rows)()
        if G.RowRecipe(row)().endswith("-display-renamed"):
            if self._twin_exists(all_rows, row) is M.false_value:
                return M.false_value
        return self._scan(M.Tail(rows)(), all_rows)

    def _twin_exists(self, rows, row):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.false_value
        other = M.Head(rows)()
        if G.RowSerial(other)() != G.RowSerial(row)():
            if G.RowRecipe(other)()[-len("-display-renamed"):] != "-display-renamed":
                if G.RowCanonicalId(other)() == G.RowCanonicalId(row)():
                    if G.RowRulesetVersion(other)()() == G.RowRulesetVersion(row)()():
                        return M.truth_value
        return self._twin_exists(M.Tail(rows)(), row)

    def __call__(self):
        return self.result


class ExactDuplicatesDropped(M.Edge):
    """Every drop is a recorded exact duplicate; delivered rows are pairwise non-exact."""

    def __init__(self):
        kept = FreshKept()()
        drops = FreshDrops()()
        if self._drops_ok(drops) is M.false_value:
            self.result = M.false_value
        elif self._distinct(kept) is M.false_value:
            self.result = M.false_value
        elif G.CountRows(drops)() < 1:
            self.result = M.false_value
        else:
            self.result = M.truth_value

    def _drops_ok(self, drops):
        if IsEmptyTerm(drops)() is M.truth_value:
            return M.truth_value
        entry = M.Head(drops)()
        dropped = M.Head(entry)()
        survivor = M.Head(M.Tail(entry)())()
        if G.RowsAreDuplicates(survivor, dropped)() is M.false_value:
            return M.false_value
        if G.RowReason(dropped)() == "":
            return M.false_value
        return self._drops_ok(M.Tail(drops)())

    def _distinct(self, rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.truth_value
        row = M.Head(rows)()
        if IsEmptyTerm(G.FirstDuplicateOf(M.Tail(rows)(), row)())() is M.false_value:
            return M.false_value
        return self._distinct(M.Tail(rows)())

    def __call__(self):
        return self.result


class GoalPerturbationChangesId(M.Edge):
    """A goal +1 / +2 row gets a new canonical id and keeps the ruleset digest."""

    def __init__(self):
        self.result = self._scan(FreshKept()())

    def _scan(self, rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.truth_value
        row = M.Head(rows)()
        reason = G.RowReason(row)()
        if reason == G.REASON_GOAL_ONE_TEXT or reason == G.REASON_GOAL_TWO_TEXT:
            parent = RowParent(row)()
            if IsEmptyTerm(parent)() is M.truth_value:
                return M.false_value
            if G.RowCanonicalId(row)() == G.RowCanonicalId(parent)():
                return M.false_value
            if G.RowRulesetVersion(row)()() != G.RowRulesetVersion(parent)()():
                return M.false_value
        return self._scan(M.Tail(rows)())

    def __call__(self):
        return self.result


class RulePerturbationChangesIdAndDigest(M.Edge):
    """A rule-content perturbation yields a new canonical id and a new digest."""

    def __init__(self):
        self.result = self._scan(FreshKept()())

    def _scan(self, rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.truth_value
        row = M.Head(rows)()
        reason = G.RowReason(row)()
        if reason == G.REASON_ADD_ONE_TEXT or reason.startswith(
            G.REASON_PREFIX_REMOVE_TEXT
        ):
            parent = RowParent(row)()
            if IsEmptyTerm(parent)() is M.truth_value:
                return M.false_value
            if G.RowCanonicalId(row)() == G.RowCanonicalId(parent)():
                return M.false_value
            if G.RowRulesetVersion(row)()() == G.RowRulesetVersion(parent)()():
                return M.false_value
        return self._scan(M.Tail(rows)())

    def __call__(self):
        return self.result


class ScopeBreakChangesDigest(M.Edge):
    """A scope-break row's new ruleset digest differs from its old ruleset digest."""

    def __init__(self):
        self.result = self._scan(FreshKept()())

    def _scan(self, rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.truth_value
        row = M.Head(rows)()
        if G.RowReason(row)().startswith(G.REASON_PREFIX_SCOPE_TEXT):
            if G.RowOldRulesetVersion(row)() == G.RowRulesetVersion(row)()():
                return M.false_value
        return self._scan(M.Tail(rows)())

    def __call__(self):
        return self.result


class G1DigestsBound(M.Edge):
    """R_even rows carry G1's R_even digest and R_plus rows G1's R_plus digest.

    The binding is the G1 content digest of the row's exact ruleset, quoted
    from G1 report §4 — a display name is never a binding.
    """

    def __init__(self):
        self.result = self._scan(FreshKept()())

    def _scan(self, rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.truth_value
        row = M.Head(rows)()
        recipe = G.RowRecipe(row)()
        version = G.RowRulesetVersion(row)()
        if recipe == "R_even" or recipe == "R_even-display-renamed":
            if version() != G1_R_EVEN_VERSION_TEXT:
                return M.false_value
        if recipe == "R_plus" or recipe == "R_plus-display-renamed":
            if version() != G1_R_PLUS_VERSION_TEXT:
                return M.false_value
        return self._scan(M.Tail(rows)())

    def __call__(self):
        return self.result


class VersionIsContentNotDisplay(M.Edge):
    """Every binding is 64 hex of content; no display text is a binding or an id."""

    def __init__(self):
        self.result = self._scan(FreshKept()())

    def _scan(self, rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.truth_value
        row = M.Head(rows)()
        version = G.RowRulesetVersion(row)()
        if RD.TextIsHex(version())() is M.false_value:
            return M.false_value
        if version() == G.RowRecipe(row)():
            return M.false_value
        if version() == G.RowDisplaySignature(row)():
            return M.false_value
        text = G.CanonicalTextOfRecord(G.RowRecord(row)())()
        if TextContains(text, "Add2")() is M.truth_value:
            return M.false_value
        if TextContains(text, "Remove2")() is M.truth_value:
            return M.false_value
        if TextContains(text, "Swap")() is M.truth_value:
            return M.false_value
        if TextContains(text, "rule-0")() is M.truth_value:
            return M.false_value
        return self._scan(M.Tail(rows)())

    def __call__(self):
        return self.result


class IdsAndCountsOutsideTerms(M.Edge):
    """Reporting values ride as `Pair(value, EmptyList)` and stay out of content.

    Each shell is exactly that shape; every state-fact, rule and observer atom
    is a declared singleton or text payload (an integer payload fails
    `PayloadIsText`); and no task id appears in any canonical content text.
    """

    def __init__(self):
        self.result = self._scan(FreshKept()())

    def _scan(self, rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.truth_value
        row = M.Head(rows)()
        if self._shells_ok(row, 0) is M.false_value:
            return M.false_value
        record = G.RowRecord(row)()
        if self._record_inert(record) is M.false_value:
            return M.false_value
        text = G.CanonicalTextOfRecord(record)()
        if TextContains(text, "T0")() is M.truth_value:
            return M.false_value
        return self._scan(M.Tail(rows)())

    def _record_inert(self, record):
        if RD.AtomsAreDeclaredOrText(D.FactsOfState(G.TaskStart(record)())())() is (
            M.false_value
        ):
            return M.false_value
        if RD.AtomsAreDeclaredOrText(D.FactsOfState(G.TaskGoal(record)())())() is (
            M.false_value
        ):
            return M.false_value
        if self._specs_inert(G.TaskSpecs(record)()) is M.false_value:
            return M.false_value
        if self._specs_inert(G.TaskOldSpecs(record)()) is M.false_value:
            return M.false_value
        return RD.AtomsAreDeclaredOrText(G.TaskObservers(record)())()

    def _specs_inert(self, specs):
        if IsEmptyTerm(specs)() is M.truth_value:
            return M.truth_value
        content = D.RuleContent(M.Head(specs)())()
        if RD.AtomsAreDeclaredOrText(D.PremisesOfRule(content)())() is M.false_value:
            return M.false_value
        if RD.AtomsAreDeclaredOrText(D.ReplacementOfRule(content)())() is M.false_value:
            return M.false_value
        return self._specs_inert(M.Tail(specs)())

    def _shells_ok(self, row, position):
        if position == 7:
            return M.truth_value
        shell = D.HeadAt(row, position)()
        if M.IsPair(shell)() is M.false_value:
            return M.false_value
        if IsEmptyTerm(M.Tail(shell)())() is M.false_value:
            return M.false_value
        return self._shells_ok(row, position + 1)

    def __call__(self):
        return self.result


class ScopeBreakPendingOnly(M.Edge):
    """Scope-break rows name a PENDING certificate reference — none exists."""

    def __init__(self):
        self.result = self._scan(FreshKept()(), 0)

    def _scan(self, rows, seen):
        if IsEmptyTerm(rows)() is M.truth_value:
            if seen < 1:
                return M.false_value
            return M.truth_value
        row = M.Head(rows)()
        if G.RowReason(row)().startswith(G.REASON_PREFIX_SCOPE_TEXT):
            text = G.OldCertificateText(row, G.RowRecord(row)())()
            if text[:len(G.PENDING_PREFIX_TEXT)] != G.PENDING_PREFIX_TEXT:
                return M.false_value
            seen = seen + 1
        return self._scan(M.Tail(rows)(), seen)

    def __call__(self):
        return self.result


class InertnessGuard(M.Edge):
    """The generation module holds no checker and no outcome vocabulary."""

    def __init__(self):
        self.result = self._forbidden(
            SourceText("task_generation.py")(),
            M.Pair(
                M.Char("import invariance"),
                M.Pair(
                    M.Char("ReachabilityPrune("),
                    M.Pair(
                        M.Char("IsUnreachable("),
                        M.Pair(
                            M.Char("UnreachableLabel"),
                            M.Pair(
                                M.Char("PhiReading"),
                                M.Pair(
                                    M.Char("PhiHolds("),
                                    M.Pair(
                                        M.Char("IsPreserves("),
                                        M.Pair(
                                            M.Char("Preserves("),
                                            M.Pair(
                                                M.Char("CHECKED_"),
                                                M.Pair(
                                                    M.Char("IsInvariant("),
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

    def _forbidden(self, text, needles):
        if IsEmptyTerm(needles)() is M.truth_value:
            return M.truth_value
        if TextContains(text, M.Head(needles)()())() is M.truth_value:
            return M.false_value
        return self._forbidden(text, M.Tail(needles)())

    def __call__(self):
        return self.result


class RerunReproducesFile(M.Edge):
    """A fresh pass reproduces tasks.jsonl byte for byte (deterministic)."""

    def __init__(self):
        kept = FreshKept()()
        if G.RowsToJsonl(kept)() == DeliveredText()():
            self.result = M.truth_value
        else:
            self.result = M.false_value

    def __call__(self):
        return self.result


class G2Tests(M.Edge):
    """The G2 test chain: `Pair(name, test class)` in run order."""

    def __init__(self):
        built = M.EmptyList
        built = ChainAppend(built, M.Pair(M.Char("minimums: generated >= 30, canonical >= 10"), GeneratedMinimums))()
        built = ChainAppend(built, M.Pair(M.Char("tasks.jsonl: delivered rows >= 30"), DeliveredRowMinimum))()
        built = ChainAppend(built, M.Pair(M.Char("tasks.jsonl: zero outcome fields"), ZeroOutcomeFields))()
        built = ChainAppend(built, M.Pair(M.Char("rows: parent task id and perturbation reason recorded"), ParentAndReasonRecorded))()
        built = ChainAppend(built, M.Pair(M.Char("canonical: display rename collapses (acceptance #2)"), RenameCollapsesCanonicalId))()
        built = ChainAppend(built, M.Pair(M.Char("canonical: exact duplicates dropped and recorded"), ExactDuplicatesDropped))()
        built = ChainAppend(built, M.Pair(M.Char("canonical: goal perturbation changes id, keeps digest"), GoalPerturbationChangesId))()
        built = ChainAppend(built, M.Pair(M.Char("canonical: rule-content perturbation changes id and digest"), RulePerturbationChangesIdAndDigest))()
        built = ChainAppend(built, M.Pair(M.Char("canonical: scope break changes ruleset digest"), ScopeBreakChangesDigest))()
        built = ChainAppend(built, M.Pair(M.Char("binding: G1 ruleset digests bound"), G1DigestsBound))()
        built = ChainAppend(built, M.Pair(M.Char("binding: version is content, never display name"), VersionIsContentNotDisplay))()
        built = ChainAppend(built, M.Pair(M.Char("discipline: ids and counts outside semantic terms"), IdsAndCountsOutsideTerms))()
        built = ChainAppend(built, M.Pair(M.Char("scope break: pending certificate references only"), ScopeBreakPendingOnly))()
        built = ChainAppend(built, M.Pair(M.Char("inertness: no checker or outcome vocabulary"), InertnessGuard))()
        built = ChainAppend(built, M.Pair(M.Char("generation: rerun reproduces tasks.jsonl"), RerunReproducesFile))()
        self.result = built
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result
