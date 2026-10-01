"""Researcher-v0 G3 — laboratory execution gate, BASELINE condition (mining off).

Authorization (G2 report §11, recorded there as an explicit override of the
brief's G3 wording): G3 runs the delivered canonical task set under BASELINE
only. MINING stays for G4/G5, on the same canonical ids and the same budgets.

Scope of this module:

* bind the run to the delivered task set: the runner reruns the G2 generator
  and requires its JSONL rendering to reproduce `tasks/tasks.jsonl` byte for
  byte before any task runs;
* select one representative per canonical id — the first delivered row of
  that id, in delivered order — and record every delivered row sharing it
  (`members`): 34 canonical ids, each attempted exactly once;
* attempt each representative in one in-process worker under a fixed budget:
  breadth-first search in declared rule order, states deduplicated with
  `machine.Compare`, goal tested when a state is generated;
* classify every attempt into the BASELINE vocabulary:

      CHECKED_REACHABLE   the goal was reached and the path certificate
                          replayed in the experiment checker (`checker`)
      BUDGET_EXHAUSTED    the expansion budget or the wall-clock budget was
                          spent before the goal was reached
      OPEN_RESIDUAL       the search closed, or evidence failed replay,
                          without a certificate: never a proof (A1.1)
      UNSUPPORTED         a scope_break_test row whose pending slot is not
                          resolved under typed PENDING-REF (G2 report §7)
      EXECUTION_FAILURE   a crash: never a refutation

  The BASELINE executor has no route to an unreachability outcome. With mining
  off no invariant certificate exists, so zero unreachability results is the
  expected reading (A2.3), not a defect of the comparison;
* render the journal (`journals/baseline.jsonl`: a header binding, one attempt
  line per canonical id, a footer with counts) and the path-certificate
  archive (`certificates/baseline_path_certificates.jsonl`).

A timeout is not a counterexample, a crash is not a refutation, and
UNSUPPORTED is a label distinct from BUDGET_EXHAUSTED. No attempt here
produces a counterexample of any kind: counterexamples are mining artifacts
(G4), so `counterexample_id` is empty on every BASELINE line.

Attempt layout (version `researcher-v0-attempt/1`):

    Pair(Pair(seq, EmptyList), Pair(row, Pair(Pair(members, EmptyList),
         Pair(body, Pair(Pair(elapsed_ms, EmptyList), EmptyList)))))

Body layout:

    Pair(outcome, Pair(reason, Pair(Pair(expansions, EmptyList),
         Pair(certificate-shell, Pair(pending-shell, Pair(binding-shell,
         EmptyList))))))

A shell is `Pair(value, EmptyList)` when present and `EmptyList` when absent,
so no slot holds a value-or-nothing union. The certificate shell's value is
`Pair(certificate, Pair(replay-verdict, EmptyList))`; the pending shell's value
is `Pair(pending-ref, Pair(resolution, EmptyList))` with the resolution from
`checker.ResolvePendingRef`; the binding shell's value is
`Pair(ruleset-version, Pair(Pair(start_count, EmptyList), Pair(Pair(goal_count,
EmptyList), Pair(start-text, Pair(goal-text, EmptyList)))))`.

House idiom as G1/G2: each operation is an `Edge` class called as
`Class(args)()`; no module-level function, no Python container, no module-level
mutable state; `core.py` untouched; nothing monkeypatched.
"""

from __future__ import annotations

import time

from .. import machine as M
from . import checker as C
from . import task_generation as G
from . import token_domain as D
from .chains import ChainAppend, ChainHas, IsEmptyTerm

LABORATORY_VERSION_TEXT = "researcher-v0-laboratory/1"
JOURNAL_LAYOUT_VERSION_TEXT = "researcher-v0-journal/1"
ATTEMPT_LAYOUT_VERSION_TEXT = "researcher-v0-attempt/1"
CONDITION_TEXT = "BASELINE"
MINING_TEXT = "off"
EXPANSION_BUDGET = 32
WALL_CLOCK_BUDGET_MS = 60000
MAX_WORKERS = 1
WORKER_ID_TEXT = "worker-0"
SEED_TEXT = "none"
SEARCH_TEXT = (
    "breadth-first; declared rule order; states deduplicated with machine.Compare;"
    " goal tested on generation"
)
TASK_SET_PATH_TEXT = "researcher_v0/tasks/tasks.jsonl"


# --------------------------------------------------------------------------
# outcome labels (BASELINE vocabulary: five members)
# --------------------------------------------------------------------------


class CheckedReachableTag(M.Edge):
    def __init__(self):
        self.result = M.Char("CHECKED_REACHABLE")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class OpenResidualTag(M.Edge):
    def __init__(self):
        self.result = M.Char("OPEN_RESIDUAL")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class UnsupportedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("UNSUPPORTED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class BudgetExhaustedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("BUDGET_EXHAUSTED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ExecutionFailureTag(M.Edge):
    def __init__(self):
        self.result = M.Char("EXECUTION_FAILURE")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class GoalReachedTag(M.Edge):
    """Search-level marker, never an outcome: the checker decides the outcome."""

    def __init__(self):
        self.result = M.Char("goal_reached")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class BaselineOutcomes(M.Edge):
    """The BASELINE outcome vocabulary as a chain, in reporting order."""

    def __init__(self):
        self.result = M.Pair(
            CheckedReachableTag()(),
            M.Pair(
                OpenResidualTag()(),
                M.Pair(
                    UnsupportedTag()(),
                    M.Pair(
                        BudgetExhaustedTag()(),
                        M.Pair(ExecutionFailureTag()(), M.EmptyList),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class IsBaselineOutcome(M.Edge):
    """Is this atom one of the five BASELINE outcome labels?"""

    def __init__(self, atom):
        self.result = ChainHas(BaselineOutcomes()(), atom)()
        super().__init__(inputs=M.Pair(atom, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# canonical representatives
# --------------------------------------------------------------------------


class MembersText(M.Edge):
    """Comma-joined serials of every row carrying `canonical_id` (reporting)."""

    def __init__(self, rows, canonical_id):
        self.result = self._join(rows, canonical_id, "")
        super().__init__(
            inputs=M.Pair(rows, M.Pair(M.Char(canonical_id), M.EmptyList)),
            results=self.result,
        )

    def _join(self, rows, canonical_id, built):
        if IsEmptyTerm(rows)() is M.truth_value:
            return built
        row = M.Head(rows)()
        if G.RowCanonicalId(row)() == canonical_id:
            serial = "T" + "%04d" % G.RowSerial(row)()
            if built == "":
                built = serial
            else:
                built = built + "," + serial
        return self._join(M.Tail(rows)(), canonical_id, built)

    def __call__(self):
        return self.result


class CanonicalRepresentatives(M.Edge):
    """The first delivered row of each canonical id, in delivered order.

    Result: a chain of `Pair(row, Pair(members, EmptyList))`, members as a
    text atom. A display-rename collapse group is attempted once, through its
    first row; its other rows are recorded as members, never re-run.
    """

    def __init__(self, rows):
        self.result = self._walk(rows, rows, M.EmptyList, M.EmptyList)
        super().__init__(inputs=M.Pair(rows, M.EmptyList), results=self.result)

    def _walk(self, remaining, all_rows, seen, built):
        if IsEmptyTerm(remaining)() is M.truth_value:
            return built
        row = M.Head(remaining)()
        canonical = M.Char(G.RowCanonicalId(row)())
        if ChainHas(seen, canonical)() is M.truth_value:
            return self._walk(M.Tail(remaining)(), all_rows, seen, built)
        members = M.Char(MembersText(all_rows, G.RowCanonicalId(row)())())
        return self._walk(
            M.Tail(remaining)(),
            all_rows,
            ChainAppend(seen, canonical)(),
            ChainAppend(built, M.Pair(row, M.Pair(members, M.EmptyList)))(),
        )

    def __call__(self):
        return self.result


class RepresentativeBySerial(M.Edge):
    """The representative entry whose row serial matches, else EmptyList."""

    def __init__(self, representatives, serial):
        self.result = self._scan(representatives, serial)
        super().__init__(
            inputs=M.Pair(representatives, M.Pair(M.Pair(serial, M.EmptyList), M.EmptyList)),
            results=self.result,
        )

    def _scan(self, representatives, serial):
        if IsEmptyTerm(representatives)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(representatives)()
        if G.RowSerial(M.Head(entry)())() == serial:
            return entry
        return self._scan(M.Tail(representatives)(), serial)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# budgeted breadth-first search
# --------------------------------------------------------------------------


class ElapsedMs(M.Edge):
    """Milliseconds since `started` (a `time.perf_counter` reading; reporting int)."""

    def __init__(self, started):
        self.result = int((time.perf_counter() - started) * 1000)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SpecDigests(M.Edge):
    """`Pair(spec, Pair(content-digest, EmptyList))` per spec, declared order."""

    def __init__(self, specs):
        self.result = self._collect(specs, M.EmptyList)
        super().__init__(inputs=M.Pair(specs, M.EmptyList), results=self.result)

    def _collect(self, specs, built):
        if IsEmptyTerm(specs)() is M.truth_value:
            return built
        spec = M.Head(specs)()
        return self._collect(
            M.Tail(specs)(),
            ChainAppend(
                built, M.Pair(spec, M.Pair(D.RuleFingerprintOfSpec(spec)(), M.EmptyList))
            )(),
        )

    def __call__(self):
        return self.result


class SearchNode(M.Edge):
    """`Pair(state, Pair(steps, EmptyList))` — a frontier entry and its path."""

    def __init__(self, state, steps):
        self.result = M.Pair(state, M.Pair(steps, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SearchResult(M.Edge):
    """`Pair(tag, Pair(reason, Pair(Pair(expansions, EmptyList), Pair(path-shell, EmptyList))))`.

    The path shell is `Pair(steps, EmptyList)` when the goal was reached
    (steps may be `EmptyList` when start equals goal), `EmptyList` otherwise.
    """

    def __init__(self, tag, reason_text, expansions, path_shell):
        self.result = M.Pair(
            tag,
            M.Pair(
                M.Char(reason_text),
                M.Pair(M.Pair(expansions, M.EmptyList), M.Pair(path_shell, M.EmptyList)),
            ),
        )
        super().__init__(inputs=M.Pair(tag, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BaselineSearch(M.Edge):
    """Breadth-first search from the task start toward its goal, within budget.

    One expansion takes the oldest frontier state and applies every rule of the
    task's exact ruleset, in declared order, through the G1 applier. An applied
    move whose successor is `Compare`-equal to the goal ends the search with its
    path; any other new successor joins the frontier once. The search stops,
    in this order, when the frontier is empty (OPEN_RESIDUAL: bounded
    exhaustion is never a proof, A1.1), when the expansion budget is spent, or
    when the wall-clock budget is spent (both BUDGET_EXHAUSTED).
    """

    def __init__(self, record, budget, wall_ms, started):
        self.result = self._search(record, budget, wall_ms, started)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def _search(self, record, budget, wall_ms, started):
        start = G.TaskStart(record)()
        goal = G.TaskGoal(record)()
        if M.Compare(start, goal)() is M.truth_value:
            return SearchResult(
                GoalReachedTag()(),
                "start equals goal; zero steps",
                0,
                M.Pair(M.EmptyList, M.EmptyList),
            )()
        rules = SpecDigests(G.TaskSpecs(record)())()
        frontier = M.Pair(SearchNode(start, M.EmptyList)(), M.EmptyList)
        visited = M.Pair(start, M.EmptyList)
        expansions = 0
        while M.IdentityCompare(frontier, M.EmptyList)() is M.false_value:
            if expansions >= budget:
                return SearchResult(
                    BudgetExhaustedTag()(),
                    "expansion budget spent ("
                    + str(expansions)
                    + " of "
                    + str(budget)
                    + ") before the goal was reached; exhaustion is not unreachability (A1.1)",
                    expansions,
                    M.EmptyList,
                )()
            if ElapsedMs(started)() >= wall_ms:
                return SearchResult(
                    BudgetExhaustedTag()(),
                    "wall-clock budget spent ("
                    + str(wall_ms)
                    + " ms) before the goal was reached; a timeout is not a counterexample",
                    expansions,
                    M.EmptyList,
                )()
            node = M.Head(frontier)()
            expansions = expansions + 1
            grown = self._expand(rules, goal, node, M.Tail(frontier)(), visited)
            if IsEmptyTerm(M.Head(grown)())() is M.false_value:
                return SearchResult(
                    GoalReachedTag()(),
                    "goal generated during expansion " + str(expansions),
                    expansions,
                    M.Head(grown)(),
                )()
            frontier = D.HeadAt(grown, 1)()
            visited = D.HeadAt(grown, 2)()
        return SearchResult(
            OpenResidualTag()(),
            "search frontier closed before the goal was reached; bounded exhaustion is never a proof (A1.1)",
            expansions,
            M.EmptyList,
        )()

    def _expand(self, rules, goal, node, frontier, visited):
        """`Pair(path-shell, Pair(frontier, Pair(visited, EmptyList)))`."""
        if IsEmptyTerm(rules)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(frontier, M.Pair(visited, M.EmptyList)))
        entry = M.Head(rules)()
        move = D.ApplyRule(M.Head(entry)(), M.Head(node)())()
        if D.IsAppliedOutcome(move)() is M.truth_value:
            after = D.OutcomeAfter(move)()
            steps = ChainAppend(
                D.HeadAt(node, 1)(), C.PathStep(D.HeadAt(entry, 1)(), after)()
            )()
            if M.Compare(after, goal)() is M.truth_value:
                return M.Pair(
                    M.Pair(steps, M.EmptyList),
                    M.Pair(frontier, M.Pair(visited, M.EmptyList)),
                )
            if ChainHas(visited, after)() is M.false_value:
                return self._expand(
                    M.Tail(rules)(),
                    goal,
                    node,
                    ChainAppend(frontier, SearchNode(after, steps)())(),
                    ChainAppend(visited, after)(),
                )
        return self._expand(M.Tail(rules)(), goal, node, frontier, visited)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# attempts
# --------------------------------------------------------------------------


class JsonSafeText(M.Edge):
    """Text safe inside a JSON string: quotes, backslashes and newlines replaced."""

    def __init__(self, text):
        self.result = (
            text.replace("\\", "/").replace('"', "'").replace("\n", " ").replace("\r", " ")
        )
        super().__init__(inputs=M.Pair(M.Char(text), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptBody(M.Edge):
    """Build an attempt body (see the module docstring for the layout)."""

    def __init__(self, outcome, reason_text, expansions, certificate_shell, pending_shell, binding_shell):
        self.result = M.Pair(
            outcome,
            M.Pair(
                M.Char(reason_text),
                M.Pair(
                    M.Pair(expansions, M.EmptyList),
                    M.Pair(
                        certificate_shell,
                        M.Pair(pending_shell, M.Pair(binding_shell, M.EmptyList)),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(outcome, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TaskBinding(M.Edge):
    """What the attempt is bound to, recomputed from the row's record.

    `Pair(ruleset-version, Pair(Pair(start_count, EmptyList), Pair(Pair(goal_count,
    EmptyList), Pair(start-text, Pair(goal-text, EmptyList)))))`. Raises on
    malformed task content, which the attempt classifies as EXECUTION_FAILURE.
    """

    def __init__(self, row):
        record = G.RowRecord(row)()
        start = G.TaskStart(record)()
        goal = G.TaskGoal(record)()
        self.result = M.Pair(
            D.RulesetVersionOfSpecs(G.TaskSpecs(record)())(),
            M.Pair(
                M.Pair(D.CountOfState(start)(), M.EmptyList),
                M.Pair(
                    M.Pair(D.CountOfState(goal)(), M.EmptyList),
                    M.Pair(
                        C.StateText(start)(),
                        M.Pair(C.StateText(goal)(), M.EmptyList),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(row, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RejectedText(M.Edge):
    """`<id>: <reason>; ...` over a rejected-by-type chain (reporting text)."""

    def __init__(self, rejected):
        self.result = self._join(rejected)
        super().__init__(inputs=M.Pair(rejected, M.EmptyList), results=self.result)

    def _join(self, rejected):
        if IsEmptyTerm(rejected)() is M.truth_value:
            return ""
        entry = M.Head(rejected)()
        text = M.Head(entry)()() + ": " + D.HeadAt(entry, 1)()()
        if IsEmptyTerm(M.Tail(rejected)())() is M.truth_value:
            return text
        return text + "; " + self._join(M.Tail(rejected)())

    def __call__(self):
        return self.result


class BaselineAttempt(M.Edge):
    """One BASELINE attempt on one canonical representative.

    Everything that touches the task's terms runs inside one guarded block: an
    exception is classified EXECUTION_FAILURE with its text recorded, and it
    carries no certificate and no counterexample (a crash is not a refutation).
    Result: an attempt record, layout `researcher-v0-attempt/1`.
    """

    def __init__(self, seq, entry, archive, budget, wall_ms):
        row = M.Head(entry)()
        members = D.HeadAt(entry, 1)()
        started = time.perf_counter()
        try:
            body = self._run(row, archive, budget, wall_ms, started)
        except Exception as failure:
            body = AttemptBody(
                ExecutionFailureTag()(),
                "crash, not a refutation: " + JsonSafeText(repr(failure))(),
                0,
                M.EmptyList,
                M.EmptyList,
                M.EmptyList,
            )()
        elapsed = ElapsedMs(started)()
        self.result = M.Pair(
            M.Pair(seq, M.EmptyList),
            M.Pair(
                row,
                M.Pair(
                    M.Pair(members, M.EmptyList),
                    M.Pair(body, M.Pair(M.Pair(elapsed, M.EmptyList), M.EmptyList)),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def _run(self, row, archive, budget, wall_ms, started):
        record = G.RowRecord(row)()
        binding = M.Pair(TaskBinding(row)(), M.EmptyList)
        if G.IsScopeBreakRecord(record)() is M.truth_value:
            return self._scope_break(row, archive, binding)
        search = BaselineSearch(record, budget, wall_ms, started)()
        tag = M.Head(search)()
        reason = D.HeadAt(search, 1)()()
        expansions = M.Head(D.HeadAt(search, 2)())()
        path_shell = D.HeadAt(search, 3)()
        if M.Compare(tag, GoalReachedTag()())() is M.false_value:
            return AttemptBody(tag, reason, expansions, M.EmptyList, M.EmptyList, binding)()
        certificate = C.PathCertificate(record, M.Head(path_shell)())()
        verdict = C.ReplayPathCertificate(certificate, record)()
        if C.IsReplayed(verdict)() is M.false_value:
            return AttemptBody(
                OpenResidualTag()(),
                "path evidence failed replay, and malformed evidence is never a result: "
                + C.VerdictReason(verdict)()(),
                expansions,
                M.EmptyList,
                M.EmptyList,
                binding,
            )()
        return AttemptBody(
            CheckedReachableTag()(),
            reason
            + "; path certificate replayed by the experiment checker"
            + " (steps re-applied from rule content: "
            + str(C.VerdictSteps(verdict)())
            + ")",
            expansions,
            M.Pair(M.Pair(certificate, M.Pair(verdict, M.EmptyList)), M.EmptyList),
            M.EmptyList,
            binding,
        )()

    def _scope_break(self, row, archive, binding):
        pending = C.PendingRefText(row)()
        resolution = C.ResolvePendingRef(row, archive)()
        resolved = M.Head(resolution)()
        rejected_text = RejectedText(D.HeadAt(resolution, 1)())()
        if IsEmptyTerm(resolved)() is M.false_value:
            reason = (
                "typed PENDING-REF: "
                + pending
                + " resolved to "
                + M.Head(resolved)()()
                + "; the scope-break evaluation is not part of BASELINE (G5)"
            )
        else:
            reason = (
                "typed PENDING-REF: "
                + pending
                + " unresolved; BASELINE mints no proved-invariant certificate"
            )
            if rejected_text != "":
                reason = reason + "; refused by type: " + rejected_text
        return AttemptBody(
            UnsupportedTag()(),
            reason,
            0,
            M.EmptyList,
            M.Pair(M.Pair(M.Char(pending), M.Pair(resolution, M.EmptyList)), M.EmptyList),
            binding,
        )()

    def __call__(self):
        return self.result


class AttemptSeq(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(D.HeadAt(attempt, 0)())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptRow(M.Edge):
    def __init__(self, attempt):
        self.result = D.HeadAt(attempt, 1)()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptMembers(M.Edge):
    """Members text atom of an attempt."""

    def __init__(self, attempt):
        self.result = M.Head(D.HeadAt(attempt, 2)())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptBodyOf(M.Edge):
    def __init__(self, attempt):
        self.result = D.HeadAt(attempt, 3)()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptElapsed(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(D.HeadAt(attempt, 4)())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptOutcome(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(AttemptBodyOf(attempt)())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptReason(M.Edge):
    """Reason text atom of an attempt."""

    def __init__(self, attempt):
        self.result = D.HeadAt(AttemptBodyOf(attempt)(), 1)()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptExpansions(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(D.HeadAt(AttemptBodyOf(attempt)(), 2)())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptCertificateShell(M.Edge):
    def __init__(self, attempt):
        self.result = D.HeadAt(AttemptBodyOf(attempt)(), 3)()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptPendingShell(M.Edge):
    def __init__(self, attempt):
        self.result = D.HeadAt(AttemptBodyOf(attempt)(), 4)()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptBindingShell(M.Edge):
    def __init__(self, attempt):
        self.result = D.HeadAt(AttemptBodyOf(attempt)(), 5)()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptTaskIdText(M.Edge):
    """`T<serial>` of the attempted row (reporting text)."""

    def __init__(self, attempt):
        self.result = "T" + "%04d" % G.RowSerial(AttemptRow(attempt)())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptCertificateIdText(M.Edge):
    """The cited certificate id, or empty text when the attempt cites none."""

    def __init__(self, attempt):
        shell = AttemptCertificateShell(attempt)()
        if IsEmptyTerm(shell)() is M.truth_value:
            self.result = ""
        else:
            self.result = C.CertificateId(M.Head(M.Head(shell)())())()()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------


class BaselineRun(M.Edge):
    """Every canonical representative attempted once, in delivered order.

    Result: `Pair(attempts, Pair(archive, EmptyList))`. The archive holds the
    run's replayed certificates as `checker.ArchiveEntry` terms in minting
    order; a scope-break row later in the order resolves (or not) against it.
    """

    def __init__(self, representatives, budget, wall_ms):
        self.result = self._walk(
            representatives, 1, M.EmptyList, M.EmptyList, budget, wall_ms
        )
        super().__init__(inputs=M.Pair(representatives, M.EmptyList), results=self.result)

    def _walk(self, remaining, seq, attempts, archive, budget, wall_ms):
        if IsEmptyTerm(remaining)() is M.truth_value:
            return M.Pair(attempts, M.Pair(archive, M.EmptyList))
        attempt = BaselineAttempt(seq, M.Head(remaining)(), archive, budget, wall_ms)()
        shell = AttemptCertificateShell(attempt)()
        if IsEmptyTerm(shell)() is M.false_value:
            certificate = M.Head(M.Head(shell)())()
            archive = ChainAppend(
                archive,
                C.ArchiveEntry(
                    C.CertificateId(certificate)(),
                    certificate,
                    M.Char(AttemptTaskIdText(attempt)()),
                )(),
            )()
        return self._walk(
            M.Tail(remaining)(),
            seq + 1,
            ChainAppend(attempts, attempt)(),
            archive,
            budget,
            wall_ms,
        )

    def __call__(self):
        return self.result


class OutcomeCount(M.Edge):
    """How many attempts carry the given outcome label (reporting)."""

    def __init__(self, attempts, tag):
        self.result = self._count(attempts, tag, 0)
        super().__init__(
            inputs=M.Pair(attempts, M.Pair(tag, M.EmptyList)), results=self.result
        )

    def _count(self, attempts, tag, so_far):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return so_far
        if M.Compare(AttemptOutcome(M.Head(attempts)())(), tag)() is M.truth_value:
            return self._count(M.Tail(attempts)(), tag, so_far + 1)
        return self._count(M.Tail(attempts)(), tag, so_far)

    def __call__(self):
        return self.result


class AttemptTotals(M.Edge):
    """`Pair(Pair(total_expansions, EmptyList), Pair(Pair(total_elapsed_ms,
    EmptyList), Pair(Pair(certificates, EmptyList), EmptyList)))` (reporting)."""

    def __init__(self, attempts):
        self.result = self._sum(attempts, 0, 0, 0)
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _sum(self, attempts, expansions, elapsed, certificates):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return M.Pair(
                M.Pair(expansions, M.EmptyList),
                M.Pair(
                    M.Pair(elapsed, M.EmptyList),
                    M.Pair(M.Pair(certificates, M.EmptyList), M.EmptyList),
                ),
            )
        attempt = M.Head(attempts)()
        cited = 0
        if IsEmptyTerm(AttemptCertificateShell(attempt)())() is M.false_value:
            cited = 1
        return self._sum(
            M.Tail(attempts)(),
            expansions + AttemptExpansions(attempt)(),
            elapsed + AttemptElapsed(attempt)(),
            certificates + cited,
        )

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# journal and certificate archive (host reporting boundary)
# --------------------------------------------------------------------------


class JournalHeaderJson(M.Edge):
    """The journal's header binding line."""

    def __init__(self, task_set_digest, delivered_rows, canonical_count, budget, wall_ms):
        self.result = (
            '{"record": "header", "journal_layout": "'
            + JOURNAL_LAYOUT_VERSION_TEXT
            + '", "attempt_layout": "'
            + ATTEMPT_LAYOUT_VERSION_TEXT
            + '", "laboratory_version": "'
            + LABORATORY_VERSION_TEXT
            + '", "checker_version": "'
            + C.CHECKER_VERSION_TEXT
            + '", "condition": "'
            + CONDITION_TEXT
            + '", "mining": "'
            + MINING_TEXT
            + '", "task_set": "'
            + TASK_SET_PATH_TEXT
            + '", "task_set_blake2b": "'
            + task_set_digest
            + '", "delivered_rows": '
            + str(delivered_rows)
            + ', "canonical_tasks": '
            + str(canonical_count)
            + ', "search": "'
            + SEARCH_TEXT
            + '", "expansion_budget": '
            + str(budget)
            + ', "wall_clock_budget_ms_per_task": '
            + str(wall_ms)
            + ', "max_workers": '
            + str(MAX_WORKERS)
            + ', "worker_id": "'
            + WORKER_ID_TEXT
            + '", "seed": "'
            + SEED_TEXT
            + '"}'
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class AttemptJson(M.Edge):
    """One attempt line: the brief's G3 fields plus provenance and reason."""

    def __init__(self, attempt):
        row = AttemptRow(attempt)()
        record = G.RowRecord(row)()
        task_id = AttemptTaskIdText(attempt)()
        binding_shell = AttemptBindingShell(attempt)()
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
        pending_shell = AttemptPendingShell(attempt)()
        if IsEmptyTerm(pending_shell)() is M.truth_value:
            pending_ref = ""
            resolution_text = ""
            rejected_text = ""
        else:
            pending = M.Head(pending_shell)()
            pending_ref = M.Head(pending)()()
            resolution = D.HeadAt(pending, 1)()
            resolved = M.Head(resolution)()
            if IsEmptyTerm(resolved)() is M.truth_value:
                resolution_text = "unresolved"
            else:
                resolution_text = "resolved:" + M.Head(resolved)()()
            rejected_text = RejectedText(D.HeadAt(resolution, 1)())()
        self.result = (
            '{"record": "attempt", "seq": '
            + str(AttemptSeq(attempt)())
            + ', "condition": "'
            + CONDITION_TEXT
            + '", "task_id": "'
            + task_id
            + '", "canonical_id": "'
            + G.RowCanonicalId(row)()
            + '", "members": "'
            + AttemptMembers(attempt)()()
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
            + '", "worker_id": "'
            + WORKER_ID_TEXT
            + '", "attempt_id": "'
            + CONDITION_TEXT
            + ":"
            + task_id
            + ':1", "outcome": "'
            + AttemptOutcome(attempt)()()
            + '", "expansions": '
            + str(AttemptExpansions(attempt)())
            + ', "elapsed_ms": '
            + str(AttemptElapsed(attempt)())
            + ', "certificate_id": "'
            + AttemptCertificateIdText(attempt)()
            + '", "counterexample_id": "", "pending_ref": "'
            + pending_ref
            + '", "pending_resolution": "'
            + resolution_text
            + '", "rejected_by_type": "'
            + JsonSafeText(rejected_text)()
            + '", "reason": "'
            + JsonSafeText(AttemptReason(attempt)()())()
            + '"}'
        )
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class JournalFooterJson(M.Edge):
    """The journal's footer: attempt count, last seq, per-outcome counts, totals."""

    def __init__(self, attempts):
        totals = AttemptTotals(attempts)()
        self.result = (
            '{"record": "footer", "condition": "'
            + CONDITION_TEXT
            + '", "attempts": '
            + str(OutcomeCountAll(attempts)())
            + ', "last_seq": '
            + str(LastSeq(attempts)())
            + self._counts(BaselineOutcomes()(), attempts)
            + ', "certificates": '
            + str(M.Head(D.HeadAt(totals, 2)())())
            + ', "counterexamples": 0, "total_expansions": '
            + str(M.Head(D.HeadAt(totals, 0)())())
            + ', "elapsed_ms_total": '
            + str(M.Head(D.HeadAt(totals, 1)())())
            + "}"
        )
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _counts(self, tags, attempts):
        if IsEmptyTerm(tags)() is M.truth_value:
            return ""
        tag = M.Head(tags)()
        return (
            ', "outcome_'
            + tag()
            + '": '
            + str(OutcomeCount(attempts, tag)())
            + self._counts(M.Tail(tags)(), attempts)
        )

    def __call__(self):
        return self.result


class OutcomeCountAll(M.Edge):
    """Number of attempts (reporting)."""

    def __init__(self, attempts):
        self.result = self._count(attempts, 0)
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _count(self, attempts, so_far):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return so_far
        return self._count(M.Tail(attempts)(), so_far + 1)

    def __call__(self):
        return self.result


class LastSeq(M.Edge):
    """Seq of the last attempt, 0 when there is none (reporting)."""

    def __init__(self, attempts):
        self.result = self._last(attempts, 0)
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _last(self, attempts, so_far):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return so_far
        return self._last(M.Tail(attempts)(), AttemptSeq(M.Head(attempts)())())

    def __call__(self):
        return self.result


class JournalText(M.Edge):
    """The whole journal: header, one line per attempt in seq order, footer."""

    def __init__(self, attempts, task_set_digest, delivered_rows, canonical_count, budget, wall_ms):
        self.result = (
            JournalHeaderJson(
                task_set_digest, delivered_rows, canonical_count, budget, wall_ms
            )()
            + "\n"
            + self._lines(attempts)
            + JournalFooterJson(attempts)()
            + "\n"
        )
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _lines(self, attempts):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return ""
        return AttemptJson(M.Head(attempts)())() + "\n" + self._lines(M.Tail(attempts)())

    def __call__(self):
        return self.result


class StepRulesText(M.Edge):
    """Display names of a path's rules, comma-joined (reporting only).

    Looked up by content digest in the task's specs: the certificate itself
    names rule content, never a display label.
    """

    def __init__(self, specs, steps):
        self.result = self._join(specs, steps)
        super().__init__(
            inputs=M.Pair(specs, M.Pair(steps, M.EmptyList)), results=self.result
        )

    def _join(self, specs, steps):
        if IsEmptyTerm(steps)() is M.truth_value:
            return ""
        found = C.SpecWithDigest(specs, C.StepRuleDigest(M.Head(steps)())())()
        name = D.RuleDisplay(M.Head(found)())()()
        if IsEmptyTerm(M.Tail(steps)())() is M.truth_value:
            return name
        return name + "," + self._join(specs, M.Tail(steps)())

    def __call__(self):
        return self.result


class StepDigestsText(M.Edge):
    """Per-rule content digests of a path's steps, comma-joined."""

    def __init__(self, steps):
        self.result = self._join(steps)
        super().__init__(inputs=M.Pair(steps, M.EmptyList), results=self.result)

    def _join(self, steps):
        if IsEmptyTerm(steps)() is M.truth_value:
            return ""
        digest = C.StepRuleDigest(M.Head(steps)())()()
        if IsEmptyTerm(M.Tail(steps)())() is M.truth_value:
            return digest
        return digest + "," + self._join(M.Tail(steps)())

    def __call__(self):
        return self.result


class PathCountsText(M.Edge):
    """Token counts along a path, start first (reporting only)."""

    def __init__(self, start, steps):
        self.result = str(D.CountOfState(start)()) + self._join(steps)
        super().__init__(
            inputs=M.Pair(start, M.Pair(steps, M.EmptyList)), results=self.result
        )

    def _join(self, steps):
        if IsEmptyTerm(steps)() is M.truth_value:
            return ""
        return "," + str(D.CountOfState(C.StepAfter(M.Head(steps)())())()) + self._join(
            M.Tail(steps)()
        )

    def __call__(self):
        return self.result


class StepCount(M.Edge):
    """Number of steps in a path (reporting)."""

    def __init__(self, steps):
        self.result = self._count(steps, 0)
        super().__init__(inputs=M.Pair(steps, M.EmptyList), results=self.result)

    def _count(self, steps, so_far):
        if IsEmptyTerm(steps)() is M.truth_value:
            return so_far
        return self._count(M.Tail(steps)(), so_far + 1)

    def __call__(self):
        return self.result


class CertificateJson(M.Edge):
    """One archive line: the certificate binding, its path, and its replay log."""

    def __init__(self, attempt):
        row = AttemptRow(attempt)()
        record = G.RowRecord(row)()
        shell_value = M.Head(AttemptCertificateShell(attempt)())()
        certificate = M.Head(shell_value)()
        verdict = D.HeadAt(shell_value, 1)()
        steps = C.CertificateEvidence(certificate)()
        self.result = (
            '{"certificate_id": "'
            + C.CertificateId(certificate)()()
            + '", "layout": "'
            + C.CERTIFICATE_LAYOUT_VERSION_TEXT
            + '", "kind": "'
            + C.CertificateKind(certificate)()()
            + '", "task_id": "'
            + AttemptTaskIdText(attempt)()
            + '", "canonical_id": "'
            + G.RowCanonicalId(row)()
            + '", "ruleset_version": "'
            + C.CertificateDigest(certificate)()()
            + '", "observer": "", "start_count": '
            + str(D.CountOfState(C.CertificateStart(certificate)())())
            + ', "goal_count": '
            + str(D.CountOfState(C.CertificateGoal(certificate)())())
            + ', "checker_version": "'
            + C.CertificateVersion(certificate)()()
            + '", "step_count": '
            + str(StepCount(steps)())
            + ', "step_rules": "'
            + StepRulesText(G.TaskSpecs(record)(), steps)()
            + '", "step_rule_digests": "'
            + StepDigestsText(steps)()
            + '", "path_counts": "'
            + PathCountsText(C.CertificateStart(certificate)(), steps)()
            + '", "replay": "'
            + C.VerdictTag(verdict)()()
            + '", "replayed_steps": '
            + str(C.VerdictSteps(verdict)())
            + ', "replay_reason": "'
            + JsonSafeText(C.VerdictReason(verdict)()())()
            + '"}'
        )
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertificatesText(M.Edge):
    """The archive text: one line per cited certificate, in seq order."""

    def __init__(self, attempts):
        self.result = self._lines(attempts)
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _lines(self, attempts):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return ""
        attempt = M.Head(attempts)()
        rest = self._lines(M.Tail(attempts)())
        if IsEmptyTerm(AttemptCertificateShell(attempt)())() is M.truth_value:
            return rest
        return CertificateJson(attempt)() + "\n" + rest

    def __call__(self):
        return self.result


class WriteArtifact(M.Edge):
    """Write a text artifact to its path (host reporting boundary)."""

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
