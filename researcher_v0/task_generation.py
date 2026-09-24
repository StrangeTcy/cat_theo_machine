"""Researcher-v0 G2 — inert task generation and canonicalization.

Scope of this module (G2 only):

* generate a task set over the G1 token-count domain. Task kinds are
  `reachability`, `perturbed_reachability` and `scope_break_test`; the
  perturbations are goal +1, goal +2, remove a rule, add Add1, and display
  rename;
* every generated row records its parent serial and its perturbation reason
  (the brief's parent-task and reason fields, rendered at the reporting
  boundary);
* every generated row binds `ruleset_version` to the G1 content digest of its
  exact ruleset (`RulesetVersionOfSpecs`, recomputed from the specs the row
  carries) — never to a display name;
* canonicalize: display renaming collapses to one canonical id under the
  semantic/display partition G1 declared (see `ruleset_digest` module
  docstring and G1 report §4); an exact duplicate — same canonical content and
  same display signature as an earlier row — is dropped, and the drop is
  recorded with its parent and reason; a perturbation that changes rule
  content yields a different canonical id and a different ruleset digest.

Canonical content is built from G1's own encoders (`ruleset_digest.TermText`
and `ruleset_digest.RulesetVersionText`) and widens nothing: the partition
there hashes rule content, variable sharing and state structure, and refuses
display atoms and variable names.

What this module deliberately does NOT do (the G2 boundary):

* it runs no task, mines nothing, proves nothing, prunes nothing, issues no
  outcome of any kind and produces no certificate. A scope-break row names a
  PENDING certificate reference (`pending:<parent task id>`) — no certificate
  exists at G2 and none is claimed;
* it writes no checker code: `invariance` is not imported and no observer is
  evaluated. The scope-break observer slot carries the parity pattern as inert
  data for the later checker to consume;
* it touches no live path. Nothing imports this package.

Comparison discipline (inherited from G1 unchanged): terms are compared with
`machine.Compare`, emptiness of `EmptyList` with `machine.IdentityCompare`,
predicate results by identity to `machine.truth_value` / `false_value`. Python
identity is not used on a term. Task ids and counts are host reporting values:
they never occupy a semantic term slot; a reported value rides inside a term
as `Pair(value, EmptyList)` and is read at payload level only, exactly as
`token_domain.FirstPremiseWithoutMatch` carries a position. The record layout
holds no int-or-atom union: every shell head is one payload kind throughout.

Row layout (version `researcher-v0-task-row/1`), outermost first:

    Pair(Pair(serial, EmptyList),
      Pair(Pair(parent-serial, EmptyList),
        Pair(Pair(reason, EmptyList),
          Pair(Pair(canonical-id, EmptyList),
            Pair(Pair(ruleset-recipe, EmptyList),
              Pair(Pair(display-signature, EmptyList),
                Pair(Pair(old-ruleset-version, EmptyList),
                  Pair(record, EmptyList))))))))

Task record layout (version `researcher-v0-task-record/1`):

    Pair(kind, Pair(start, Pair(goal, Pair(specs, Pair(old_specs,
         Pair(observers, EmptyList))))))

`old_specs` and `observers` are chains (`EmptyList` is the empty chain, the
substrate convention). Accessors below are the only readers of these layouts.
"""

from __future__ import annotations

import hashlib

from .. import machine as M
from .chains import ChainAppend, ChainHas, ChainJoin, ChainLength, IsEmptyTerm
from . import ruleset_digest as RD
from . import token_domain as D

TASK_RECORD_LAYOUT_VERSION_TEXT = "researcher-v0-task-record/1"
TASK_ROW_LAYOUT_VERSION_TEXT = "researcher-v0-task-row/1"
CANONICAL_TAG_TEXT = "researcher-v0-task/1"

KIND_REACHABILITY_TEXT = "reachability"
KIND_PERTURBED_TEXT = "perturbed_reachability"
KIND_SCOPE_BREAK_TEXT = "scope_break_test"

REASON_SEED_TEXT = "seed"
REASON_GOAL_ONE_TEXT = "goal +1"
REASON_GOAL_TWO_TEXT = "goal +2"
REASON_ADD_ONE_TEXT = "add Add1"
REASON_RENAME_TEXT = "display rename"
REASON_PREFIX_REMOVE_TEXT = "remove rule "
REASON_PREFIX_SCOPE_TEXT = "scope break: "

PENDING_PREFIX_TEXT = "pending:"
OBSERVER_DISPLAY_TEXT = "Parity(observed)"


# --------------------------------------------------------------------------
# kind markers
# --------------------------------------------------------------------------

class ReachabilityKind(M.Edge):
    def __init__(self):
        self.result = M.Char(KIND_REACHABILITY_TEXT)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PerturbedKind(M.Edge):
    def __init__(self):
        self.result = M.Char(KIND_PERTURBED_TEXT)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ScopeBreakKind(M.Edge):
    def __init__(self):
        self.result = M.Char(KIND_SCOPE_BREAK_TEXT)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class IsScopeBreakRecord(M.Edge):
    def __init__(self, record):
        if M.Compare(TaskKindOf(record)(), ScopeBreakKind()())() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ParityObserverPattern(M.Edge):
    """The parity observer as inert pattern data — no observer is evaluated.

    The pattern term is `Parity(observed)` with the variable read the way
    `machine.Match` reads one. It rides the record's observers chain so a
    scope-break row names the reading its later checker must guard; G2 never
    calls a reading function on it.
    """

    def __init__(self):
        self.result = M.Pair(
            D.ParityTag()(), M.Pair(D.RuleVar("observed")(), M.EmptyList)
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# task record (layout version 1)
# --------------------------------------------------------------------------

class TaskRecord(M.Edge):
    """Build a task record: kind, start, goal, specs, old_specs, observers."""

    def __init__(self, kind, start, goal, specs, old_specs, observers):
        self.result = M.Pair(
            kind,
            M.Pair(
                start,
                M.Pair(
                    goal,
                    M.Pair(specs, M.Pair(old_specs, M.Pair(observers, M.EmptyList))),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class TaskKindOf(M.Edge):
    def __init__(self, record):
        self.result = M.Head(record)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TaskStart(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(record)())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TaskGoal(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(record)())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TaskSpecs(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(record)())())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TaskOldSpecs(M.Edge):
    def __init__(self, record):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(record)())())())()
        )()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TaskObservers(M.Edge):
    def __init__(self, record):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
        )()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# task row (layout version 1) — reporting shells around a record
# --------------------------------------------------------------------------

class TaskRow(M.Edge):
    """Build a task row. Reporting values ride as `Pair(value, EmptyList)`."""

    def __init__(
        self,
        serial,
        parent_serial,
        reason,
        canonical_id,
        recipe,
        display_signature,
        old_ruleset_version,
        record,
    ):
        self.result = M.Pair(
            M.Pair(serial, M.EmptyList),
            M.Pair(
                M.Pair(parent_serial, M.EmptyList),
                M.Pair(
                    M.Pair(reason, M.EmptyList),
                    M.Pair(
                        M.Pair(canonical_id, M.EmptyList),
                        M.Pair(
                            M.Pair(recipe, M.EmptyList),
                            M.Pair(
                                M.Pair(display_signature, M.EmptyList),
                                M.Pair(
                                    M.Pair(old_ruleset_version, M.EmptyList),
                                    M.Pair(record, M.EmptyList),
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


class RowShellValue(M.Edge):
    """Payload of reporting shell `position` of a row (payload-level read)."""

    def __init__(self, row, position):
        shell = D.HeadAt(row, position)()
        self.result = M.Head(shell)()
        super().__init__(
            inputs=M.Pair(row, M.Pair(position, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class RowSerial(M.Edge):
    def __init__(self, row):
        self.result = RowShellValue(row, 0)()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowParentSerial(M.Edge):
    def __init__(self, row):
        self.result = RowShellValue(row, 1)()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowReason(M.Edge):
    def __init__(self, row):
        self.result = RowShellValue(row, 2)()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowCanonicalId(M.Edge):
    def __init__(self, row):
        self.result = RowShellValue(row, 3)()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowRecipe(M.Edge):
    def __init__(self, row):
        self.result = RowShellValue(row, 4)()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowDisplaySignature(M.Edge):
    def __init__(self, row):
        self.result = RowShellValue(row, 5)()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowOldRulesetVersion(M.Edge):
    def __init__(self, row):
        self.result = RowShellValue(row, 6)()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowRecord(M.Edge):
    def __init__(self, row):
        self.result = D.HeadAt(row, 7)()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowRulesetVersion(M.Edge):
    """The G1 content digest of the row's exact ruleset — the row's binding."""

    def __init__(self, row):
        self.result = D.RulesetVersionOfSpecs(TaskSpecs(RowRecord(row)())())()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowBySerial(M.Edge):
    """The row of a chain whose serial matches, else EmptyList."""

    def __init__(self, rows, serial):
        self.result = self._scan(rows, serial)
        super().__init__(
            inputs=M.Pair(rows, M.Pair(serial, M.EmptyList)), results=self.result
        )

    def _scan(self, rows, serial):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.EmptyList
        if RowSerial(M.Head(rows)())() == serial:
            return M.Head(rows)()
        return self._scan(M.Tail(rows)(), serial)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# specs construction (G1 contents, perturbed by rule content or display)
# --------------------------------------------------------------------------

class SpecsWithoutDisplay(M.Edge):
    """The spec chain with the spec whose display equals `display` removed."""

    def __init__(self, specs, display):
        self.result = self._collect(specs, display, M.EmptyList)
        super().__init__(
            inputs=M.Pair(specs, M.Pair(M.Char(display), M.EmptyList)),
            results=self.result,
        )

    def _collect(self, specs, display, built):
        if IsEmptyTerm(specs)() is M.truth_value:
            return built
        spec = M.Head(specs)()
        if M.Compare(D.RuleDisplay(spec)(), M.Char(display))() is M.false_value:
            built = ChainAppend(built, spec)()
        return self._collect(M.Tail(specs)(), display, built)

    def __call__(self):
        return self.result


class RenamedSpecs(M.Edge):
    """Same rule contents, display-only names replaced (`display-<i>`)."""

    def __init__(self, specs):
        self.result = D.SpecsOfContentChain(D.RuleChainOf(specs)(), 0)()
        super().__init__(inputs=M.Pair(specs, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DisplaySignatureOfSpecs(M.Edge):
    """Comma-joined display names of a spec chain (reporting text)."""

    def __init__(self, specs):
        self.result = self._join(specs)
        super().__init__(inputs=M.Pair(specs, M.EmptyList), results=self.result)

    def _join(self, specs):
        if IsEmptyTerm(specs)() is M.truth_value:
            return ""
        head = D.RuleDisplay(M.Head(specs)())()()
        if IsEmptyTerm(M.Tail(specs)())() is M.truth_value:
            return head
        return head + "," + self._join(M.Tail(specs)())

    def __call__(self):
        return self.result


class DisplaySignatureOfRecord(M.Edge):
    """`<new specs displays>|<old specs displays>` — the row's display face.

    Display text is reporting only. It never enters a canonical id and it is
    never a ruleset binding; it exists so an exact duplicate (same content and
    same display) can be told apart from a display-rename collapse (same
    content, different display).
    """

    def __init__(self, record):
        self.result = (
            DisplaySignatureOfSpecs(TaskSpecs(record)())()
            + "|"
            + DisplaySignatureOfSpecs(TaskOldSpecs(record)())()
        )
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# canonicalization (G1 partition, not widened)
# --------------------------------------------------------------------------

class CanonicalTextOfRecord(M.Edge):
    """Canonical content text of a task record.

    Query rows encode `(query reachability start S goal G ruleset V)` where V
    is the sorted per-rule digest document (rule order and display invisible,
    variable names invisible, variable sharing visible — G1 §4). Scope-break
    rows encode `(query scope-break start S goal G observer P old-ruleset A
    new-ruleset B)` over the same encoders. `S` and `G` are the state FACT
    chains — the semantic content the later checker reads — because the
    `Knowledge` wrapper is a fixed container marker outside the fingerprint's
    declared singleton list and is refused by `TermText` rather than hashed by
    identity. Nothing else is excluded.
    """

    def __init__(self, record):
        start_text = M.Head(
            RD.TermText(D.FactsOfState(TaskStart(record)())(), M.EmptyList)()
        )()()
        goal_text = M.Head(
            RD.TermText(D.FactsOfState(TaskGoal(record)())(), M.EmptyList)()
        )()()
        new_text = RD.RulesetVersionText(D.RuleChainOf(TaskSpecs(record)())())()()
        if IsScopeBreakRecord(record)() is M.truth_value:
            observer = M.Head(TaskObservers(record)())()
            observer_text = M.Head(RD.TermText(observer, M.EmptyList)())()()
            old_text = RD.RulesetVersionText(
                D.RuleChainOf(TaskOldSpecs(record)())()
            )()()
            self.result = (
                "(task "
                + CANONICAL_TAG_TEXT
                + " query scope-break start "
                + start_text
                + " goal "
                + goal_text
                + " observer "
                + observer_text
                + " old-ruleset "
                + old_text
                + " new-ruleset "
                + new_text
                + ")"
            )
        else:
            self.result = (
                "(task "
                + CANONICAL_TAG_TEXT
                + " query reachability start "
                + start_text
                + " goal "
                + goal_text
                + " ruleset "
                + new_text
                + ")"
            )
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalIdOfRecord(M.Edge):
    """64-hex canonical id: the digest of the canonical content text."""

    def __init__(self, record):
        text = CanonicalTextOfRecord(record)()
        self.result = M.Char(
            hashlib.blake2b(text.encode("utf-8"), digest_size=32).hexdigest()
        )
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowsAreDuplicates(M.Edge):
    """Exact duplicates: same canonical id and same display signature.

    Canonical id equality is payload equality of two digests the same encoder
    minted; display signature equality is payload equality of reporting text.
    A row pair with equal canonical id and different display signature is a
    display-rename collapse, not a duplicate.
    """

    def __init__(self, first_row, second_row):
        if RowCanonicalId(first_row)() == RowCanonicalId(second_row)():
            if RowDisplaySignature(first_row)() == RowDisplaySignature(second_row)():
                self.result = M.truth_value
            else:
                self.result = M.false_value
        else:
            self.result = M.false_value
        super().__init__(
            inputs=M.Pair(first_row, M.Pair(second_row, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FirstDuplicateOf(M.Edge):
    """`Pair(survivor, EmptyList)` of the first duplicate of `row`, else EmptyList."""

    def __init__(self, kept, row):
        self.result = self._scan(kept, row)
        super().__init__(
            inputs=M.Pair(kept, M.Pair(row, M.EmptyList)), results=self.result
        )

    def _scan(self, kept, row):
        if IsEmptyTerm(kept)() is M.truth_value:
            return M.EmptyList
        if RowsAreDuplicates(M.Head(kept)(), row)() is M.truth_value:
            return M.Pair(M.Head(kept)(), M.EmptyList)
        return self._scan(M.Tail(kept)(), row)

    def __call__(self):
        return self.result


class DropExactDuplicates(M.Edge):
    """`Pair(survivors, Pair(drops, EmptyList))` over a generation-order chain.

    First occurrence survives; a later exact duplicate is dropped. Each drop
    is recorded as `Pair(dropped, Pair(survivor, EmptyList))` — the dropped
    row keeps its serial, parent and perturbation reason, so the drop record
    is the provenance record the brief requires.
    """

    def __init__(self, rows):
        self.result = self._walk(rows, M.EmptyList, M.EmptyList)
        super().__init__(inputs=M.Pair(rows, M.EmptyList), results=self.result)

    def _walk(self, rows, kept, drops):
        if IsEmptyTerm(rows)() is M.truth_value:
            return M.Pair(kept, M.Pair(drops, M.EmptyList))
        row = M.Head(rows)()
        matched = FirstDuplicateOf(kept, row)()
        if IsEmptyTerm(matched)() is M.truth_value:
            return self._walk(
                M.Tail(rows)(), ChainAppend(kept, row)(), drops
            )
        return self._walk(
            M.Tail(rows)(),
            kept,
            ChainAppend(drops, M.Pair(row, M.Pair(M.Head(matched)(), M.EmptyList)))(),
        )

    def __call__(self):
        return self.result


class RowsWithCanonicalCount(M.Edge):
    """How many rows of the chain carry the given canonical id (reporting)."""

    def __init__(self, rows, canonical_id):
        self.result = self._count(rows, canonical_id, 0)
        super().__init__(
            inputs=M.Pair(rows, M.Pair(M.Char(canonical_id), M.EmptyList)),
            results=self.result,
        )

    def _count(self, rows, canonical_id, so_far):
        if IsEmptyTerm(rows)() is M.truth_value:
            return so_far
        if RowCanonicalId(M.Head(rows)())() == canonical_id:
            return self._count(M.Tail(rows)(), canonical_id, so_far + 1)
        return self._count(M.Tail(rows)(), canonical_id, so_far)

    def __call__(self):
        return self.result


class CountDistinctCanonical(M.Edge):
    """Count of distinct canonical ids in the chain (reporting)."""

    def __init__(self, rows):
        self.result = self._count(rows, M.EmptyList, 0)
        super().__init__(inputs=M.Pair(rows, M.EmptyList), results=self.result)

    def _count(self, rows, seen, so_far):
        if IsEmptyTerm(rows)() is M.truth_value:
            return so_far
        cid = RowCanonicalId(M.Head(rows)())()
        if ChainHas(seen, M.Char(cid))() is M.truth_value:
            return self._count(M.Tail(rows)(), seen, so_far)
        return self._count(
            M.Tail(rows)(), ChainAppend(seen, M.Char(cid))(), so_far + 1
        )

    def __call__(self):
        return self.result


class CountCollapseGroups(M.Edge):
    """Count of canonical ids shared by two or more rows (reporting)."""

    def __init__(self, rows):
        self.result = self._count(rows, rows, M.EmptyList, 0)
        super().__init__(inputs=M.Pair(rows, M.EmptyList), results=self.result)

    def _count(self, remaining, all_rows, seen, so_far):
        if IsEmptyTerm(remaining)() is M.truth_value:
            return so_far
        cid = RowCanonicalId(M.Head(remaining)())()
        if ChainHas(seen, M.Char(cid))() is M.truth_value:
            return self._count(M.Tail(remaining)(), all_rows, seen, so_far)
        seen = ChainAppend(seen, M.Char(cid))()
        if RowsWithCanonicalCount(all_rows, cid)() > 1:
            return self._count(M.Tail(remaining)(), all_rows, seen, so_far + 1)
        return self._count(M.Tail(remaining)(), all_rows, seen, so_far)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# reporting (host values at the JSONL boundary)
# --------------------------------------------------------------------------

class ParentIdText(M.Edge):
    """`T<serial>` for a parent, `none` for a seed (parent serial 0)."""

    def __init__(self, parent_serial):
        if parent_serial == 0:
            self.result = "none"
        else:
            self.result = "T" + "%04d" % parent_serial
        super().__init__(
            inputs=M.Pair(parent_serial, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class ChangedRuleText(M.Edge):
    """What the perturbation changed (reporting text)."""

    def __init__(self, reason):
        if reason == REASON_SEED_TEXT:
            self.result = "none"
        elif reason == REASON_GOAL_ONE_TEXT or reason == REASON_GOAL_TWO_TEXT:
            self.result = "goal"
        elif reason == REASON_ADD_ONE_TEXT:
            self.result = "Add1"
        elif reason == REASON_RENAME_TEXT:
            self.result = "display-only"
        elif reason.startswith(REASON_PREFIX_REMOVE_TEXT):
            self.result = reason[len(REASON_PREFIX_REMOVE_TEXT):]
        else:
            self.result = "none"
        super().__init__(inputs=M.Pair(M.Char(reason), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObserverText(M.Edge):
    """Display text of the record's bound observer, empty when none is bound."""

    def __init__(self, record):
        if IsEmptyTerm(TaskObservers(record)())() is M.truth_value:
            self.result = ""
        else:
            self.result = OBSERVER_DISPLAY_TEXT
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OldCertificateText(M.Edge):
    """The scope-break certificate slot: a PENDING reference, never a certificate."""

    def __init__(self, row, record):
        if IsScopeBreakRecord(record)() is M.truth_value:
            self.result = PENDING_PREFIX_TEXT + "T" + "%04d" % RowParentSerial(row)()
        else:
            self.result = ""
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowJson(M.Edge):
    """The JSONL reporting line of one task row.

    Every field is a host reporting value. There is no outcome field and no
    status field: a populated outcome at G2 is a scope breach, and the row
    vocabulary cannot express one.
    """

    def __init__(self, row):
        record = RowRecord(row)()
        kind_text = TaskKindOf(record)()()
        reason = RowReason(row)()
        serial = RowSerial(row)()
        version = RowRulesetVersion(row)()
        self.result = (
            '{"task_id": "T'
            + "%04d" % serial
            + '", "kind": "'
            + kind_text
            + '", "parent_task_id": "'
            + ParentIdText(RowParentSerial(row)())()
            + '", "perturbation_reason": "'
            + reason
            + '", "changed_rule": "'
            + ChangedRuleText(reason)()
            + '", "ruleset_version": "'
            + version()
            + '", "ruleset_recipe": "'
            + RowRecipe(row)()
            + '", "old_ruleset_version": "'
            + RowOldRulesetVersion(row)()
            + '", "canonical_id": "'
            + RowCanonicalId(row)()
            + '", "display_signature": "'
            + RowDisplaySignature(row)()
            + '", "start_count": '
            + str(D.CountOfState(TaskStart(record)())())
            + ', "goal_count": '
            + str(D.CountOfState(TaskGoal(record)())())
            + ', "observer": "'
            + ObserverText(record)()
            + '", "old_certificate": "'
            + OldCertificateText(row, record)()
            + '"}'
        )
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RowsToJsonl(M.Edge):
    """The whole tasks.jsonl text: one JSON line per row, generation order."""

    def __init__(self, rows):
        self.result = self._build(rows)
        super().__init__(inputs=M.Pair(rows, M.EmptyList), results=self.result)

    def _build(self, rows):
        if IsEmptyTerm(rows)() is M.truth_value:
            return ""
        line = RowJson(M.Head(rows)())()
        rest = self._build(M.Tail(rows)())
        if rest == "":
            return line + "\n"
        return line + "\n" + rest

    def __call__(self):
        return self.result


class WriteTasksFile(M.Edge):
    """Write the tasks text to its deliverable path (host reporting boundary)."""

    def __init__(self, path_text, text):
        handle = open(path_text, "w")
        handle.write(text)
        handle.close()
        self.result = M.Char(path_text)
        super().__init__(
            inputs=M.Pair(M.Char(path_text), M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class CountRows(M.Edge):
    """Number of rows in a chain (reporting)."""

    def __init__(self, rows):
        self.result = ChainLength(rows)()
        super().__init__(inputs=M.Pair(rows, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# generation plan and generation
# --------------------------------------------------------------------------

class PlanEntry(M.Edge):
    """A seed plan entry: `Pair(Pair(start_count, EmptyList), Pair(Pair(goal_count, EmptyList), EmptyList))`."""

    def __init__(self, start_count, goal_count):
        self.result = M.Pair(
            M.Pair(start_count, M.EmptyList),
            M.Pair(M.Pair(goal_count, M.EmptyList), M.EmptyList),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PlanStartCount(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Head(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PlanGoalCount(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Head(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SeedPlan(M.Edge):
    """The seven seed queries, in declaration order.

    The overlap with perturbation children is planned: goal +1 of seed 1 and
    goal +2 of seed 1 land on seed 3 and seed 2, so exact duplicates arise
    from the lattice itself and the drop path is exercised by construction.
    """

    def __init__(self):
        built = M.EmptyList
        built = ChainAppend(built, PlanEntry(0, 2)())()
        built = ChainAppend(built, PlanEntry(0, 4)())()
        built = ChainAppend(built, PlanEntry(0, 3)())()
        built = ChainAppend(built, PlanEntry(1, 3)())()
        built = ChainAppend(built, PlanEntry(2, 5)())()
        built = ChainAppend(built, PlanEntry(4, 2)())()
        built = ChainAppend(built, PlanEntry(6, 0)())()
        self.result = built
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SeedRow(M.Edge):
    """A `reachability` seed row over R_even."""

    def __init__(self, serial, start_count, goal_count):
        record = TaskRecord(
            ReachabilityKind()(),
            D.StateOfCount(start_count)(),
            D.StateOfCount(goal_count)(),
            D.REvenSpecs()(),
            M.EmptyList,
            M.EmptyList,
        )()
        self.result = TaskRow(
            serial,
            0,
            REASON_SEED_TEXT,
            CanonicalIdOfRecord(record)()(),
            "R_even",
            DisplaySignatureOfRecord(record)(),
            "",
            record,
        )()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class GoalPlusOneRow(M.Edge):
    """`perturbed_reachability` with the goal moved +1 (ruleset unchanged)."""

    def __init__(self, serial, parent_row):
        parent = RowRecord(parent_row)()
        record = TaskRecord(
            PerturbedKind()(),
            TaskStart(parent)(),
            D.StateOfCount(D.CountOfState(TaskGoal(parent)())() + 1)(),
            TaskSpecs(parent)(),
            M.EmptyList,
            M.EmptyList,
        )()
        self.result = TaskRow(
            serial,
            RowSerial(parent_row)(),
            REASON_GOAL_ONE_TEXT,
            CanonicalIdOfRecord(record)()(),
            RowRecipe(parent_row)(),
            DisplaySignatureOfRecord(record)(),
            "",
            record,
        )()
        super().__init__(
            inputs=M.Pair(M.Pair(serial, M.EmptyList), M.Pair(parent_row, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalPlusTwoRow(M.Edge):
    """`perturbed_reachability` with the goal moved +2 (ruleset unchanged)."""

    def __init__(self, serial, parent_row):
        parent = RowRecord(parent_row)()
        record = TaskRecord(
            PerturbedKind()(),
            TaskStart(parent)(),
            D.StateOfCount(D.CountOfState(TaskGoal(parent)())() + 2)(),
            TaskSpecs(parent)(),
            M.EmptyList,
            M.EmptyList,
        )()
        self.result = TaskRow(
            serial,
            RowSerial(parent_row)(),
            REASON_GOAL_TWO_TEXT,
            CanonicalIdOfRecord(record)()(),
            RowRecipe(parent_row)(),
            DisplaySignatureOfRecord(record)(),
            "",
            record,
        )()
        super().__init__(
            inputs=M.Pair(M.Pair(serial, M.EmptyList), M.Pair(parent_row, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RemoveRuleRow(M.Edge):
    """`perturbed_reachability` with one rule removed from the ruleset."""

    def __init__(self, serial, parent_row, removed_display):
        parent = RowRecord(parent_row)()
        specs = SpecsWithoutDisplay(TaskSpecs(parent)(), removed_display)()
        record = TaskRecord(
            PerturbedKind()(),
            TaskStart(parent)(),
            TaskGoal(parent)(),
            specs,
            M.EmptyList,
            M.EmptyList,
        )()
        self.result = TaskRow(
            serial,
            RowSerial(parent_row)(),
            REASON_PREFIX_REMOVE_TEXT + removed_display,
            CanonicalIdOfRecord(record)()(),
            "R_even-minus-" + removed_display,
            DisplaySignatureOfRecord(record)(),
            "",
            record,
        )()
        super().__init__(
            inputs=M.Pair(M.Pair(serial, M.EmptyList), M.Pair(parent_row, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class AddAddOneRow(M.Edge):
    """`perturbed_reachability` with the Add1 rules added (R_plus)."""

    def __init__(self, serial, parent_row):
        parent = RowRecord(parent_row)()
        record = TaskRecord(
            PerturbedKind()(),
            TaskStart(parent)(),
            TaskGoal(parent)(),
            D.RPlusSpecs()(),
            M.EmptyList,
            M.EmptyList,
        )()
        self.result = TaskRow(
            serial,
            RowSerial(parent_row)(),
            REASON_ADD_ONE_TEXT,
            CanonicalIdOfRecord(record)()(),
            "R_plus",
            DisplaySignatureOfRecord(record)(),
            "",
            record,
        )()
        super().__init__(
            inputs=M.Pair(M.Pair(serial, M.EmptyList), M.Pair(parent_row, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DisplayRenameRow(M.Edge):
    """`perturbed_reachability` with display-only labels renamed.

    Same rule contents, same states: the canonical id collapses onto the
    parent's and the ruleset digest is unchanged — the acceptance shape of
    brief acceptance test 2 and A1.2.
    """

    def __init__(self, serial, parent_row):
        parent = RowRecord(parent_row)()
        record = TaskRecord(
            PerturbedKind()(),
            TaskStart(parent)(),
            TaskGoal(parent)(),
            RenamedSpecs(TaskSpecs(parent)())(),
            M.EmptyList,
            M.EmptyList,
        )()
        self.result = TaskRow(
            serial,
            RowSerial(parent_row)(),
            REASON_RENAME_TEXT,
            CanonicalIdOfRecord(record)()(),
            RowRecipe(parent_row)() + "-display-renamed",
            DisplaySignatureOfRecord(record)(),
            "",
            record,
        )()
        super().__init__(
            inputs=M.Pair(M.Pair(serial, M.EmptyList), M.Pair(parent_row, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ScopeBreakRow(M.Edge):
    """`scope_break_test` over a parent's pending certificate slot.

    `old_certificate` is a PENDING reference to the certificate a later run
    may mint for the parent task under `old_specs`; G2 mints no certificate
    and runs no check. The row binds `ruleset_version` to the NEW ruleset's G1
    digest and records the old ruleset digest beside it.
    """

    def __init__(self, serial, parent_row, old_specs, new_specs, recipe, reason):
        record = TaskRecord(
            ScopeBreakKind()(),
            TaskStart(RowRecord(parent_row)())(),
            TaskGoal(RowRecord(parent_row)())(),
            new_specs,
            old_specs,
            M.Pair(ParityObserverPattern()(), M.EmptyList),
        )()
        old_version = D.RulesetVersionOfSpecs(old_specs)()
        self.result = TaskRow(
            serial,
            RowSerial(parent_row)(),
            reason,
            CanonicalIdOfRecord(record)()(),
            recipe,
            DisplaySignatureOfRecord(record)(),
            old_version(),
            record,
        )()
        super().__init__(
            inputs=M.Pair(M.Pair(serial, M.EmptyList), M.Pair(parent_row, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SeedRows(M.Edge):
    """`Pair(next_serial, rows)` — the seed rows over the plan."""

    def __init__(self, plan, serial, built):
        self.result = self._build(plan, serial, built)
        super().__init__(
            inputs=M.Pair(plan, M.Pair(serial, M.EmptyList)), results=self.result
        )

    def _build(self, plan, serial, built):
        if IsEmptyTerm(plan)() is M.truth_value:
            return M.Pair(serial, built)
        entry = M.Head(plan)()
        row = SeedRow(serial, PlanStartCount(entry)(), PlanGoalCount(entry)())()
        return self._build(
            M.Tail(plan)(), serial + 1, ChainAppend(built, row)()
        )

    def __call__(self):
        return self.result


class FamilyRows(M.Edge):
    """`Pair(next_serial, rows)` — the five perturbation rows of each seed.

    The removed rule alternates: `Remove2` for seed indices 0, 2, 4, 6 and
    `Swap` for seed indices 1, 3, 5, so both rule-removal perturbations occur.
    """

    def __init__(self, seeds, remaining, index, serial, built):
        self.result = self._build(seeds, remaining, index, serial, built)
        super().__init__(
            inputs=M.Pair(remaining, M.Pair(serial, M.EmptyList)), results=self.result
        )

    def _build(self, seeds, remaining, index, serial, built):
        if IsEmptyTerm(remaining)() is M.truth_value:
            return M.Pair(serial, built)
        seed = M.Head(remaining)()
        if index % 2 == 0:
            removed_display = "Remove2"
        else:
            removed_display = "Swap"
        built = ChainAppend(built, GoalPlusOneRow(serial, seed)())()
        built = ChainAppend(built, GoalPlusTwoRow(serial + 1, seed)())()
        built = ChainAppend(built, RemoveRuleRow(serial + 2, seed, removed_display)())()
        built = ChainAppend(built, AddAddOneRow(serial + 3, seed)())()
        built = ChainAppend(built, DisplayRenameRow(serial + 4, seed)())()
        return self._build(seeds, M.Tail(remaining)(), index + 1, serial + 5, built)

    def __call__(self):
        return self.result


class ScopeBreakRows(M.Edge):
    """`Pair(next_serial, rows)` — four scope-break rows over the seeds.

    Two exercise the Add1 scope break (one on plainly named specs, one on
    display-renamed specs — the canonical id collapses across the rename);
    two exercise rule removal as a scope break.
    """

    def __init__(self, seeds, serial, built):
        self.result = self._build(seeds, serial, built)
        super().__init__(
            inputs=M.Pair(seeds, M.Pair(serial, M.EmptyList)), results=self.result
        )

    def _build(self, seeds, serial, built):
        first = RowBySerial(seeds, 1)()
        second = RowBySerial(seeds, 2)()
        fourth = RowBySerial(seeds, 4)()
        fifth = RowBySerial(seeds, 5)()
        built = ChainAppend(
            built,
            ScopeBreakRow(
                serial,
                first,
                D.REvenSpecs()(),
                D.RPlusSpecs()(),
                "R_plus",
                REASON_PREFIX_SCOPE_TEXT + "add Add1",
            )(),
        )()
        built = ChainAppend(
            built,
            ScopeBreakRow(
                serial + 1,
                first,
                D.REvenSpecs()(),
                RenamedSpecs(D.RPlusSpecs()())(),
                "R_plus-display-renamed",
                REASON_PREFIX_SCOPE_TEXT + "add Add1",
            )(),
        )()
        built = ChainAppend(
            built,
            ScopeBreakRow(
                serial + 2,
                fourth,
                D.REvenSpecs()(),
                SpecsWithoutDisplay(D.REvenSpecs()(), "Swap")(),
                "R_even-minus-Swap",
                REASON_PREFIX_SCOPE_TEXT + "remove rule Swap",
            )(),
        )()
        built = ChainAppend(
            built,
            ScopeBreakRow(
                serial + 3,
                fifth,
                D.REvenSpecs()(),
                SpecsWithoutDisplay(D.REvenSpecs()(), "Remove2")(),
                "R_even-minus-Remove2",
                REASON_PREFIX_SCOPE_TEXT + "remove rule Remove2",
            )(),
        )()
        return M.Pair(serial + 4, built)

    def __call__(self):
        return self.result


class GenerateAllRows(M.Edge):
    """Every generated task row, in generation order: seeds, families, scope.

    Serials are assigned at generation: seeds first, then each seed's five
    perturbation rows, then the scope-break rows. Exact duplicates are still
    present here; `DropExactDuplicates` separates them and records each drop.
    """

    def __init__(self):
        seed_pair = SeedRows(SeedPlan()(), 1, M.EmptyList)()
        seeds = M.Tail(seed_pair)()
        family_pair = FamilyRows(seeds, seeds, 0, M.Head(seed_pair)(), M.EmptyList)()
        scope_pair = ScopeBreakRows(
            seeds, M.Head(family_pair)(), M.EmptyList
        )()
        self.result = ChainJoin(
            ChainJoin(seeds, M.Tail(family_pair)())(), M.Tail(scope_pair)()
        )()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result
