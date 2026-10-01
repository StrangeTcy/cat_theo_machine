"""Researcher-v0 G3 — experiment checker: path replay, reading guard, typed PENDING-REF.

Scope of this module (G3, BASELINE condition only):

* the certificate record layout every v0 certificate kind shares, and the
  content-addressed certificate id;
* replay of a reachable-path certificate by recomputation over the task's
  exact rule content. The order follows `g1_replay_procedure.md`, adapted to a
  path: (1) fingerprint the task ruleset and compare it with the certificate's
  digest — a mismatch is SCOPE_MISMATCH and nothing else is compared; (2) the
  certificate kind, observer slot and checker version; (3) the endpoints the
  certificate names, against the task's start and goal; (4) every step
  re-applied from rule content with the G1 applier, each recomputed successor
  compared with the recorded one; (5) the final state compared with the goal.
  An archived certificate is never evidence by itself: the verdict is
  recomputed every time it is asked for;
* the A2.1 reading guard (step 4 of `g1_replay_procedure.md`): both observer
  readings present, or NOT_CHECKED. A missing reading is never a differing
  value and never `false_value` — the standing acceptance item
  `MissingPhiReadingIsNotChecked` (G2 report §7, item A2.1-R);
* typed PENDING-REF resolution (G2 report §7, points 1–3): a `pending:*` slot
  resolves only to a same-run certificate whose kind, observer, old ruleset
  digest and checker version all match the slot. A reachable-path certificate
  never fills a slot typed for a proved invariant.

What this module deliberately does NOT do (the G3 BASELINE boundary): it
proves no invariant and runs no preservation check; it builds no
unreachability certificate; it has no route to an unreachability outcome. The
reading guard is the one A2.1 replay step G3 carries, because the standing
acceptance item binds the checker gates from G3 on; the preservation steps
belong to G4, where a candidate first exists.

Comparison discipline (inherited from G1/G2 unchanged): terms with
`machine.Compare`, emptiness of `EmptyList` with `machine.IdentityCompare`
(through `chains.IsEmptyTerm`), predicate results by identity to
`machine.truth_value` / `false_value`. Digests and version texts are text
atoms compared with `Compare`, which equates constructor-less atoms with equal
payloads. Counts ride inside terms as `Pair(count, EmptyList)`.

Certificate layout (version `researcher-v0-certificate/1`):

    Pair(kind, Pair(observer, Pair(start, Pair(goal, Pair(ruleset-digest,
         Pair(checker-version, Pair(evidence, EmptyList)))))))

A reachable-path certificate has observer `EmptyList` and, as evidence, the
chain of its steps `Pair(rule-digest, Pair(state-after, EmptyList))` in path
order. The rule digest is the G1 per-rule content digest, so a step names rule
CONTENT and never a display label or a position.
"""

from __future__ import annotations

import hashlib

from .. import invariance as I
from .. import machine as M
from . import ruleset_digest as RD
from . import task_generation as G
from . import token_domain as D
from .chains import ChainAppend, IsEmptyTerm

CHECKER_VERSION_TEXT = "researcher-v0-checker/1"
CERTIFICATE_LAYOUT_VERSION_TEXT = "researcher-v0-certificate/1"
CERTIFICATE_ID_PREFIX_TEXT = "cert-"
PATH_KIND_TEXT = "reachable-path"
INVARIANT_SLOT_KIND_TEXT = "proved-invariant"


# --------------------------------------------------------------------------
# tags
# --------------------------------------------------------------------------


class CheckerVersion(M.Edge):
    def __init__(self):
        self.result = M.Char(CHECKER_VERSION_TEXT)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PathKind(M.Edge):
    """Certificate kind of a replayable start-to-goal path."""

    def __init__(self):
        self.result = M.Char(PATH_KIND_TEXT)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class InvariantSlotKind(M.Edge):
    """The kind a scope-break slot is typed for: a proved invariant.

    No certificate of this kind exists in BASELINE; the tag exists so the
    typed PENDING-REF rule can say what a slot requires.
    """

    def __init__(self):
        self.result = M.Char(INVARIANT_SLOT_KIND_TEXT)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ReplayedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("REPLAYED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ScopeMismatchTag(M.Edge):
    def __init__(self):
        self.result = M.Char("SCOPE_MISMATCH")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ReplayFailedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("REPLAY_FAILED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class NotCheckedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("NOT_CHECKED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ReadingsPresentTag(M.Edge):
    def __init__(self):
        self.result = M.Char("READINGS_PRESENT")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SeparatesTag(M.Edge):
    def __init__(self):
        self.result = M.Char("SEPARATES")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SameReadingTag(M.Edge):
    def __init__(self):
        self.result = M.Char("SAME_READING")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# certificate record (layout version 1)
# --------------------------------------------------------------------------


class CertificateRecord(M.Edge):
    """Build a certificate: kind, observer, start, goal, digest, version, evidence."""

    def __init__(self, kind, observer, start, goal, digest, version, evidence):
        self.result = M.Pair(
            kind,
            M.Pair(
                observer,
                M.Pair(
                    start,
                    M.Pair(
                        goal,
                        M.Pair(digest, M.Pair(version, M.Pair(evidence, M.EmptyList))),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class CertificateKind(M.Edge):
    def __init__(self, certificate):
        self.result = D.HeadAt(certificate, 0)()
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertificateObserver(M.Edge):
    def __init__(self, certificate):
        self.result = D.HeadAt(certificate, 1)()
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertificateStart(M.Edge):
    def __init__(self, certificate):
        self.result = D.HeadAt(certificate, 2)()
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertificateGoal(M.Edge):
    def __init__(self, certificate):
        self.result = D.HeadAt(certificate, 3)()
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertificateDigest(M.Edge):
    def __init__(self, certificate):
        self.result = D.HeadAt(certificate, 4)()
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertificateVersion(M.Edge):
    def __init__(self, certificate):
        self.result = D.HeadAt(certificate, 5)()
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertificateEvidence(M.Edge):
    def __init__(self, certificate):
        self.result = D.HeadAt(certificate, 6)()
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# reachable-path certificates
# --------------------------------------------------------------------------


class PathStep(M.Edge):
    """One path step: `Pair(rule-digest, Pair(state-after, EmptyList))`."""

    def __init__(self, rule_digest, after):
        self.result = M.Pair(rule_digest, M.Pair(after, M.EmptyList))
        super().__init__(
            inputs=M.Pair(rule_digest, M.Pair(after, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class StepRuleDigest(M.Edge):
    def __init__(self, step):
        self.result = M.Head(step)()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StepAfter(M.Edge):
    def __init__(self, step):
        self.result = M.Head(M.Tail(step)())()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PathCertificate(M.Edge):
    """A reachable-path certificate for a task record and a chain of steps.

    Bound to (kind, observer = none, start, goal, ruleset digest recomputed
    from the task's specs, checker version) before it is returned.
    """

    def __init__(self, record, steps):
        self.result = CertificateRecord(
            PathKind()(),
            M.EmptyList,
            G.TaskStart(record)(),
            G.TaskGoal(record)(),
            D.RulesetVersionOfSpecs(G.TaskSpecs(record)())(),
            CheckerVersion()(),
            steps,
        )()
        super().__init__(
            inputs=M.Pair(record, M.Pair(steps, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class StateText(M.Edge):
    """Canonical text of a state's fact chain, with the G1 encoder.

    The `Knowledge` wrapper is a fixed container marker outside the G1
    singleton whitelist, so the fact chain is encoded (as G2 does for
    canonical ids). Result: a text atom.
    """

    def __init__(self, state):
        self.result = M.Head(RD.TermText(D.FactsOfState(state)(), M.EmptyList)())()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PathEvidenceText(M.Edge):
    """`(steps (step D S) ...)` over a chain of path steps (text atom)."""

    def __init__(self, steps):
        self.result = M.Char("(steps" + self._body(steps) + ")")
        super().__init__(inputs=M.Pair(steps, M.EmptyList), results=self.result)

    def _body(self, steps):
        if IsEmptyTerm(steps)() is M.truth_value:
            return ""
        step = M.Head(steps)()
        return (
            " (step "
            + StepRuleDigest(step)()()
            + " "
            + StateText(StepAfter(step)())()()
            + ")"
            + self._body(M.Tail(steps)())
        )

    def __call__(self):
        return self.result


class CertificateText(M.Edge):
    """Canonical content text of a certificate (the id is taken over it)."""

    def __init__(self, certificate):
        observer_text = M.Head(
            RD.TermText(CertificateObserver(certificate)(), M.EmptyList)()
        )()()
        self.result = M.Char(
            "(certificate "
            + CERTIFICATE_LAYOUT_VERSION_TEXT
            + " kind "
            + CertificateKind(certificate)()()
            + " observer "
            + observer_text
            + " start "
            + StateText(CertificateStart(certificate)())()()
            + " goal "
            + StateText(CertificateGoal(certificate)())()()
            + " ruleset "
            + CertificateDigest(certificate)()()
            + " checker "
            + CertificateVersion(certificate)()()
            + " evidence "
            + PathEvidenceText(CertificateEvidence(certificate)())()()
            + ")"
        )
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertificateId(M.Edge):
    """`cert-<blake2b-256 hex>` over the canonical content text.

    Content-addressed: the same certificate content minted in another process
    or another run has the same id.
    """

    def __init__(self, certificate):
        text = CertificateText(certificate)()()
        self.result = M.Char(
            CERTIFICATE_ID_PREFIX_TEXT
            + hashlib.blake2b(text.encode("utf-8"), digest_size=32).hexdigest()
        )
        super().__init__(inputs=M.Pair(certificate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# path replay (recomputation, never trust)
# --------------------------------------------------------------------------


class ReplayVerdict(M.Edge):
    """`Pair(tag, Pair(reason, Pair(Pair(steps_replayed, EmptyList), EmptyList)))`."""

    def __init__(self, tag, reason_text, replayed):
        self.result = M.Pair(
            tag,
            M.Pair(M.Char(reason_text), M.Pair(M.Pair(replayed, M.EmptyList), M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(tag, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerdictTag(M.Edge):
    def __init__(self, verdict):
        self.result = M.Head(verdict)()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerdictReason(M.Edge):
    def __init__(self, verdict):
        self.result = M.Head(M.Tail(verdict)())()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerdictSteps(M.Edge):
    """Steps replayed (reporting int, read from its shell)."""

    def __init__(self, verdict):
        self.result = M.Head(D.HeadAt(verdict, 2)())()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsReplayed(M.Edge):
    def __init__(self, verdict):
        if M.Compare(VerdictTag(verdict)(), ReplayedTag()())() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SpecWithDigest(M.Edge):
    """`Pair(spec, EmptyList)` of the first spec whose content digest matches, else EmptyList."""

    def __init__(self, specs, digest):
        self.result = self._scan(specs, digest)
        super().__init__(
            inputs=M.Pair(specs, M.Pair(digest, M.EmptyList)), results=self.result
        )

    def _scan(self, specs, digest):
        if IsEmptyTerm(specs)() is M.truth_value:
            return M.EmptyList
        spec = M.Head(specs)()
        if M.Compare(D.RuleFingerprintOfSpec(spec)(), digest)() is M.truth_value:
            return M.Pair(spec, M.EmptyList)
        return self._scan(M.Tail(specs)(), digest)

    def __call__(self):
        return self.result


class ReplayPathCertificate(M.Edge):
    """Replay a reachable-path certificate against a task record.

    Every check is recomputed from the task's exact rule content; nothing the
    certificate asserts is taken on trust. Scope is checked first: a digest
    mismatch returns SCOPE_MISMATCH before any state is compared. Any other
    failure is REPLAY_FAILED with its reason; only a complete recomputation
    that ends on the goal is REPLAYED.
    """

    def __init__(self, certificate, record):
        self.result = self._replay(certificate, record)
        super().__init__(
            inputs=M.Pair(certificate, M.Pair(record, M.EmptyList)), results=self.result
        )

    def _replay(self, certificate, record):
        specs = G.TaskSpecs(record)()
        task_digest = D.RulesetVersionOfSpecs(specs)()
        if M.Compare(task_digest, CertificateDigest(certificate)())() is M.false_value:
            return ReplayVerdict(
                ScopeMismatchTag()(),
                "task ruleset digest differs from the certificate digest; nothing compared, nothing claimed",
                0,
            )()
        if M.Compare(CertificateKind(certificate)(), PathKind()())() is M.false_value:
            return ReplayVerdict(
                ReplayFailedTag()(), "certificate kind is not reachable-path", 0
            )()
        if IsEmptyTerm(CertificateObserver(certificate)())() is M.false_value:
            return ReplayVerdict(
                ReplayFailedTag()(), "a reachable-path certificate binds no observer", 0
            )()
        if M.Compare(CertificateVersion(certificate)(), CheckerVersion()())() is M.false_value:
            return ReplayVerdict(
                ReplayFailedTag()(), "checker version differs from this checker", 0
            )()
        start = G.TaskStart(record)()
        goal = G.TaskGoal(record)()
        if M.Compare(CertificateStart(certificate)(), start)() is M.false_value:
            return ReplayVerdict(
                ReplayFailedTag()(), "certificate start differs from the task start", 0
            )()
        if M.Compare(CertificateGoal(certificate)(), goal)() is M.false_value:
            return ReplayVerdict(
                ReplayFailedTag()(), "certificate goal differs from the task goal", 0
            )()
        return self._steps(CertificateEvidence(certificate)(), specs, start, goal, 0)

    def _steps(self, steps, specs, state, goal, replayed):
        if IsEmptyTerm(steps)() is M.truth_value:
            if M.Compare(state, goal)() is M.truth_value:
                return ReplayVerdict(
                    ReplayedTag()(),
                    "every step re-applied from rule content; final state equals the goal",
                    replayed,
                )()
            return ReplayVerdict(
                ReplayFailedTag()(), "final recomputed state differs from the goal", replayed
            )()
        step = M.Head(steps)()
        found = SpecWithDigest(specs, StepRuleDigest(step)())()
        if IsEmptyTerm(found)() is M.truth_value:
            return ReplayVerdict(
                ReplayFailedTag()(), "a step names a rule outside the task ruleset", replayed
            )()
        move = D.ApplyRule(M.Head(found)(), state)()
        if D.IsAppliedOutcome(move)() is M.false_value:
            return ReplayVerdict(
                ReplayFailedTag()(), "a step rule is inapplicable at its state", replayed
            )()
        after = D.OutcomeAfter(move)()
        if M.Compare(after, StepAfter(step)())() is M.false_value:
            return ReplayVerdict(
                ReplayFailedTag()(),
                "a recomputed successor differs from the recorded state",
                replayed,
            )()
        return self._steps(M.Tail(steps)(), specs, after, goal, replayed + 1)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# A2.1 reading guard (replay step 4) — MissingPhiReadingIsNotChecked
# --------------------------------------------------------------------------


class NotCheckedReadings(M.Edge):
    """`Pair(NOT_CHECKED, Pair(reason, EmptyList))`."""

    def __init__(self, reason_text):
        self.result = M.Pair(NotCheckedTag()(), M.Pair(M.Char(reason_text), M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ObserverReadings(M.Edge):
    """Both observer readings, present, or NOT_CHECKED (A2.1 replay step 4).

    `invariance.PhiHolds` must be truth on BOTH sides and `invariance.PhiReading`
    must be non-empty on BOTH sides. `PhiReading` returns `EmptyList` on a miss,
    and a naive comparison would take that miss for a differing value — the
    hole A2.1 names in `ReachabilityPrune`, which never reads the goal side.
    Here a miss on either side ends the step with NOT_CHECKED.

    Result: `Pair(READINGS_PRESENT, Pair(start_reading, Pair(goal_reading,
    EmptyList)))` or `Pair(NOT_CHECKED, Pair(reason, EmptyList))`.
    """

    def __init__(self, start, goal, phi):
        self.result = self._read(start, goal, phi)
        super().__init__(
            inputs=M.Pair(start, M.Pair(goal, M.Pair(phi, M.EmptyList))),
            results=self.result,
        )

    def _read(self, start, goal, phi):
        if I.PhiHolds(start, phi)() is M.false_value:
            return NotCheckedReadings("start reading missing: observer matches no start fact")()
        if I.PhiHolds(goal, phi)() is M.false_value:
            return NotCheckedReadings("goal reading missing: observer matches no goal fact")()
        start_reading = I.PhiReading(start, phi)()
        goal_reading = I.PhiReading(goal, phi)()
        if IsEmptyTerm(start_reading)() is M.truth_value:
            return NotCheckedReadings("start reading empty")()
        if IsEmptyTerm(goal_reading)() is M.truth_value:
            return NotCheckedReadings("goal reading empty")()
        return M.Pair(
            ReadingsPresentTag()(),
            M.Pair(start_reading, M.Pair(goal_reading, M.EmptyList)),
        )

    def __call__(self):
        return self.result


class ReadingsVerdict(M.Edge):
    """SEPARATES, SAME_READING or NOT_CHECKED over an `ObserverReadings` result.

    Only two PRESENT readings are compared (A2.1 replay step 5). A NOT_CHECKED
    record yields NOT_CHECKED: a missing reading never separates the endpoints
    and is never reported as a false comparison.
    """

    def __init__(self, readings):
        if M.Compare(M.Head(readings)(), ReadingsPresentTag()())() is M.false_value:
            self.result = NotCheckedTag()()
        elif (
            M.Compare(D.HeadAt(readings, 1)(), D.HeadAt(readings, 2)())()
            is M.truth_value
        ):
            self.result = SameReadingTag()()
        else:
            self.result = SeparatesTag()()
        super().__init__(inputs=M.Pair(readings, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# typed PENDING-REF (G2 report §7)
# --------------------------------------------------------------------------


class ArchiveEntry(M.Edge):
    """A same-run archive entry: `Pair(id, Pair(certificate, Pair(task_id, EmptyList)))`."""

    def __init__(self, certificate_id, certificate, task_id):
        self.result = M.Pair(
            certificate_id, M.Pair(certificate, M.Pair(task_id, M.EmptyList))
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EntryId(M.Edge):
    def __init__(self, entry):
        self.result = D.HeadAt(entry, 0)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntryCertificate(M.Edge):
    def __init__(self, entry):
        self.result = D.HeadAt(entry, 1)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntryTaskId(M.Edge):
    def __init__(self, entry):
        self.result = D.HeadAt(entry, 2)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PendingRefText(M.Edge):
    """The row's pending reference, `pending:T<parent>` (reporting text)."""

    def __init__(self, row):
        self.result = G.OldCertificateText(row, G.RowRecord(row)())()
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PendingSlot(M.Edge):
    """The typed slot of a scope-break row.

    `Pair(kind, Pair(observer, Pair(old-digest, Pair(checker-version,
    EmptyList))))`: kind proved-invariant, the row's observer pattern, the old
    ruleset digest RECOMPUTED from the row's old specs (never read from the
    reporting shell), and this checker's version.
    """

    def __init__(self, row):
        record = G.RowRecord(row)()
        self.result = M.Pair(
            InvariantSlotKind()(),
            M.Pair(
                M.Head(G.TaskObservers(record)())(),
                M.Pair(
                    D.RulesetVersionOfSpecs(G.TaskOldSpecs(record)())(),
                    M.Pair(CheckerVersion()(), M.EmptyList),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SlotMismatch(M.Edge):
    """Why a certificate does not fill a typed slot.

    `EmptyList` when kind, observer, digest and checker version all match;
    otherwise `Pair(reason, EmptyList)` naming the first field that differs.
    """

    def __init__(self, slot, certificate):
        self.result = self._first(slot, certificate)
        super().__init__(
            inputs=M.Pair(slot, M.Pair(certificate, M.EmptyList)), results=self.result
        )

    def _first(self, slot, certificate):
        kind = CertificateKind(certificate)()
        if M.Compare(kind, D.HeadAt(slot, 0)())() is M.false_value:
            return M.Pair(
                M.Char("kind " + kind() + " is not " + D.HeadAt(slot, 0)()()),
                M.EmptyList,
            )
        if M.Compare(CertificateObserver(certificate)(), D.HeadAt(slot, 1)())() is M.false_value:
            return M.Pair(M.Char("observer differs from the slot observer"), M.EmptyList)
        if M.Compare(CertificateDigest(certificate)(), D.HeadAt(slot, 2)())() is M.false_value:
            return M.Pair(
                M.Char("ruleset digest differs from the slot old-ruleset digest"),
                M.EmptyList,
            )
        if M.Compare(CertificateVersion(certificate)(), D.HeadAt(slot, 3)())() is M.false_value:
            return M.Pair(M.Char("checker version differs from the slot"), M.EmptyList)
        return M.EmptyList

    def __call__(self):
        return self.result


class ResolvePendingRef(M.Edge):
    """Typed PENDING-REF resolution of a scope-break row against the run archive.

    Result: `Pair(resolution, Pair(rejected, EmptyList))` where

    * `resolution` is `Pair(certificate_id, EmptyList)` for the first archived
      certificate that fills the typed slot, else `EmptyList` (unresolved);
    * `rejected` is the chain of the parent task's archived certificates that do
      not fill it, each `Pair(certificate_id, Pair(reason, EmptyList))` — so the
      record shows which real certificate was refused and why.

    An unresolved reference is never an error, never a refutation and never a
    checked result (PENDING-REF point 2); a wrongly typed certificate is no
    better than none (point 3).
    """

    def __init__(self, row, archive):
        slot = PendingSlot(row)()
        parent = M.Char(G.ParentIdText(G.RowParentSerial(row)())())
        self.result = M.Pair(
            self._resolve(slot, archive),
            M.Pair(self._rejected(slot, archive, parent, M.EmptyList), M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(row, M.Pair(archive, M.EmptyList)), results=self.result
        )

    def _resolve(self, slot, archive):
        if IsEmptyTerm(archive)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(archive)()
        if IsEmptyTerm(SlotMismatch(slot, EntryCertificate(entry)())())() is M.truth_value:
            return M.Pair(EntryId(entry)(), M.EmptyList)
        return self._resolve(slot, M.Tail(archive)())

    def _rejected(self, slot, archive, parent, built):
        if IsEmptyTerm(archive)() is M.truth_value:
            return built
        entry = M.Head(archive)()
        if M.Compare(EntryTaskId(entry)(), parent)() is M.truth_value:
            mismatch = SlotMismatch(slot, EntryCertificate(entry)())()
            if IsEmptyTerm(mismatch)() is M.false_value:
                built = ChainAppend(
                    built, M.Pair(EntryId(entry)(), M.Pair(M.Head(mismatch)(), M.EmptyList))
                )()
        return self._rejected(slot, M.Tail(archive)(), parent, built)

    def __call__(self):
        return self.result
