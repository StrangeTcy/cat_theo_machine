from __future__ import annotations

import time

from . import invariance as Imod
from . import labels as L
from . import machine as M
from . import planner as Plannermod
from . import proof as P
from .packs import PackLoader


def char_chain(text):
    """Encode a python string as a machine Char chain (Pair chain of Char atoms)."""
    encoded = M.EmptyList
    index = len(text)
    while index > 0:
        index = index - 1
        encoded = M.Pair(M.Char(text[index]), encoded)
    return encoded


def _chain_text(chain):
    """Decode a machine Char chain back to a python string (for reporting only)."""
    text = ""
    remaining = chain
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        item = M.Head(remaining)()
        if M.IsPair(item)() is M.truth_value:
            text = text + ""
        else:
            # A Char answers its own symbol when applied. Anything that is not
            # a Char contributes nothing, which keeps the caller's
            # pretty-print fallback reachable for chains that are not text.
            try:
                text = text + str(item() + "")
            except (TypeError, AttributeError):
                text = text + ""
        remaining = M.Tail(remaining)()
    return text


def pretty(term, registry):
    return M.PrettyTerm(term, registry)()


def _status_text(status, registry):
    if M.IdentityCompare(status, L.ProvedLabel)() is M.truth_value:
        return "Proved"
    if M.IdentityCompare(status, L.FailedLabel)() is M.truth_value:
        return "Failed"
    if M.IdentityCompare(status, L.PendingLabel)() is M.truth_value:
        return "Pending"
    if M.IdentityCompare(status, M.EmptyList)() is M.truth_value:
        return "none"
    return pretty(status, registry)


# ---------------------------------------------------------------------------
# TrainingRecord term shape.
#
# TrainingRecord(
#     problem_statement,   -- ProblemStatement(id, surface text)  [surface chain]
#     meaning_structure,   -- Knowledge term with the initial facts
#     strategy_hint,       -- method term, e.g. Invariance(Parity(BoardSumObservable, ?p))
#     obligation_skeleton, -- Pair chain of ObligationSkeletonEntry terms
#     test_instances       -- Pair chain of TestInstance terms
# )
# ---------------------------------------------------------------------------


class TrainingRecord(M.Edge):
    def __init__(self, problem_statement, meaning_structure, strategy_hint, obligation_skeleton, test_instances):
        self.result = M.Pair(
            L.TrainingRecordLabel,
            M.Pair(
                problem_statement,
                M.Pair(
                    meaning_structure,
                    M.Pair(
                        strategy_hint,
                        M.Pair(
                            obligation_skeleton,
                            M.Pair(test_instances, M.EmptyList),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                problem_statement,
                M.Pair(
                    meaning_structure,
                    M.Pair(
                        strategy_hint,
                        M.Pair(
                            obligation_skeleton,
                            M.Pair(test_instances, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TrainingRecordProblemStatement(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(record)())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TrainingRecordMeaningStructure(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(record)())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TrainingRecordStrategyHint(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(record)())())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TrainingRecordObligationSkeleton(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TrainingRecordTestInstances(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProblemStatement(M.Edge):
    """ProblemStatement(id, surface_text): the problem identity plus its surface form."""

    def __init__(self, record_id, text):
        self.result = M.Pair(L.ProblemStatementLabel, M.Pair(record_id, M.Pair(text, M.EmptyList)))
        super().__init__(inputs=M.Pair(record_id, M.Pair(text, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ProblemStatementId(M.Edge):
    def __init__(self, problem_statement):
        self.result = M.Head(M.Tail(problem_statement)())()
        super().__init__(inputs=M.Pair(problem_statement, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProblemStatementText(M.Edge):
    def __init__(self, problem_statement):
        self.result = M.Head(M.Tail(M.Tail(problem_statement)())())()
        super().__init__(inputs=M.Pair(problem_statement, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StrategyHintObservable(M.Edge):
    """
    The observable pattern carried inside a strategy method term.

    A method term is Pair(method_head, args_chain); for Invariance the single
    argument is the observable, which doubles as the phi pattern of the
    invariance pipeline.
    """

    def __init__(self, hint):
        if M.IdentityCompare(hint, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            self.result = M.Head(M.Tail(hint)())()
        super().__init__(inputs=M.Pair(hint, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObligationSkeletonEntry(M.Edge):
    """ObligationSkeletonEntry(id, description, goal): one step of the curator's skeleton."""

    def __init__(self, obligation_id, description, goal):
        self.result = M.Pair(
            L.ObligationSkeletonLabel,
            M.Pair(obligation_id, M.Pair(description, M.Pair(goal, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(obligation_id, M.Pair(description, M.Pair(goal, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ObligationSkeletonEntryId(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObligationSkeletonEntryDescription(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObligationSkeletonEntryGoal(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(entry)())())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObligationSkeletonConclusionGoal(M.Edge):
    """The last skeleton entry that carries a goal term; that goal is the conclusion."""

    def __init__(self, skeleton):
        self.result = self._last_goal(skeleton)
        super().__init__(inputs=M.Pair(skeleton, M.EmptyList), results=self.result)

    def _last_goal(self, skeleton):
        if M.IdentityCompare(skeleton, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        goal = ObligationSkeletonEntryGoal(M.Head(skeleton)())()
        rest = self._last_goal(M.Tail(skeleton)())
        if M.IdentityCompare(goal, M.EmptyList)() is M.false_value:
            return goal
        return rest

    def __call__(self):
        return self.result


class TestInstance(M.Edge):
    """TestInstance(id, description, moves, final_number, expected_parity): one concrete run."""

    def __init__(self, instance_id, description, moves, final_number, expected_parity):
        self.result = M.Pair(
            L.TestInstanceLabel,
            M.Pair(
                instance_id,
                M.Pair(
                    description,
                    M.Pair(
                        moves,
                        M.Pair(final_number, M.Pair(expected_parity, M.EmptyList)),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                instance_id,
                M.Pair(
                    description,
                    M.Pair(
                        moves,
                        M.Pair(final_number, M.Pair(expected_parity, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TestInstanceId(M.Edge):
    def __init__(self, instance):
        self.result = M.Head(M.Tail(instance)())()
        super().__init__(inputs=M.Pair(instance, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TestInstanceDescription(M.Edge):
    def __init__(self, instance):
        self.result = M.Head(M.Tail(M.Tail(instance)())())()
        super().__init__(inputs=M.Pair(instance, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TestInstanceMoves(M.Edge):
    def __init__(self, instance):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(instance)())())())()
        super().__init__(inputs=M.Pair(instance, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TestInstanceFinalNumber(M.Edge):
    def __init__(self, instance):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(instance)())())())())()
        super().__init__(inputs=M.Pair(instance, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TestInstanceExpectedParity(M.Edge):
    def __init__(self, instance):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(instance)())())())())())()
        super().__init__(inputs=M.Pair(instance, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# AttemptResult term.
#
# AttemptResult(
#     record_id,          -- Char chain
#     status,             -- ProvedLabel | FailedLabel | PendingLabel (partial)
#     derivation,         -- derivation chain on success, EmptyList otherwise
#     failure_reason      -- Char chain on failure, EmptyList otherwise
# )
# ---------------------------------------------------------------------------


class AttemptResult(M.Edge):
    def __init__(self, record_id, status, derivation, failure_reason):
        self.result = M.Pair(
            L.AttemptResultLabel,
            M.Pair(
                record_id,
                M.Pair(status, M.Pair(derivation, M.Pair(failure_reason, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                record_id,
                M.Pair(status, M.Pair(derivation, M.Pair(failure_reason, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class AttemptResultRecordId(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(attempt)())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptResultStatus(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(M.Tail(attempt)())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptResultDerivation(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(attempt)())())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptResultFailureReason(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# YAML loading. Reuses PackLoader's term compiler so training records speak
# the same machine-native term language as packs.
# ---------------------------------------------------------------------------


class TrainingRecordLoader(PackLoader):
    def load_records_dict(self, data):
        if data.get("format") != "hyge-training-records":
            raise RuntimeError("Wrong training-records format")
        if data.get("version") != 1:
            raise RuntimeError("Unsupported training-records version")

        loaded = ()
        for entry in data.get("records", ()):
            loaded = loaded + (self._compile_record(entry),)
        return loaded

    def load_records_file(self, path):
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return self.load_records_dict(data)

    def _compile_record(self, entry):
        record_id = self.string_table.encode(str(entry["id"]))
        problem_statement = entry.get("problem_statement", {})
        surface_text = str(problem_statement.get("text", ""))
        problem_statement_term = ProblemStatement(record_id, self.string_table.encode(surface_text))()

        meaning = self._compile_term(entry["meaning_structure"]["start"], {})

        hint_spec = entry.get("strategy_hint")
        if hint_spec is None:
            strategy_hint = M.EmptyList
            rules_pack = None
        else:
            strategy_hint = self._compile_term(hint_spec["method"], {})
            rules_pack = hint_spec.get("rules_pack")

        skeleton_entries = ()
        for obl in entry.get("obligation_skeleton", ()):
            obl_id = self.string_table.encode(str(obl.get("id", "")))
            description = self.string_table.encode(str(obl.get("text", "")))
            goal = M.EmptyList
            if "goal" in obl:
                goal = self._compile_term(obl["goal"], {})
            skeleton_entries = skeleton_entries + (ObligationSkeletonEntry(obl_id, description, goal)(),)
        obligation_skeleton = self._chain(skeleton_entries)

        instance_entries = ()
        for inst in entry.get("test_instances", ()):
            instance_id = self.string_table.encode(str(inst.get("id", "")))
            description = self.string_table.encode(str(inst.get("description", "")))
            moves = self.string_table.encode(str(inst.get("moves", "")))
            final_number = self.string_table.encode(str(inst.get("final_number", "")))
            expected_parity = self.string_table.encode(str(inst.get("expected_parity", "")))
            instance_entries = instance_entries + (
                TestInstance(instance_id, description, moves, final_number, expected_parity)(),
            )
        test_instances = self._chain(instance_entries)

        record = TrainingRecord(
            problem_statement_term,
            meaning,
            strategy_hint,
            obligation_skeleton,
            test_instances,
        )()
        return record, rules_pack


# ---------------------------------------------------------------------------
# Per-record attempt cycle.
# ---------------------------------------------------------------------------


class AttemptSummary:
    def __init__(
        self,
        record_id,
        status_text,
        method_text,
        elapsed,
        planner_root_status,
        alternative_status,
        retained,
        failure_reason,
    ):
        self.record_id = record_id
        self.status_text = status_text
        self.method_text = method_text
        self.elapsed = elapsed
        self.planner_root_status = planner_root_status
        self.alternative_status = alternative_status
        self.retained = retained
        self.failure_reason = failure_reason


def _planner_root_status(final_state):
    fields = M.Tail(final_state)()
    obligations = M.Head(fields)()
    status = L.PendingLabel
    remaining = obligations
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        obligation_fields = M.Tail(M.Head(remaining)())()
        obligation_id = M.Head(obligation_fields)()
        if M.TermEqual(obligation_id, M.Zero)() is M.truth_value:
            status = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(obligation_fields)())())())())()
            break
        remaining = M.Tail(remaining)()
    return status


def _planner_alternative_status(final_state, hint):
    alternatives = Plannermod.PlannerStateAlternatives(final_state)()
    status = M.EmptyList
    remaining = alternatives
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        alternative = M.Head(remaining)()
        if M.TermEqual(Plannermod.PlannerAlternativeMethod(alternative)(), hint)() is M.truth_value:
            status = Plannermod.PlannerAlternativeStatus(alternative)()
            break
        remaining = M.Tail(remaining)()
    return status


def _first_undischarged_obligation(runtime, start, skeleton, conclusion_goal, rules, registry):
    """
    Audit the obligation skeleton. Returns (obligation_id_text, description_text,
    goal_text, discharged_count, total_with_goals) for the first obligation with
    a machine goal (other than the conclusion) that the rules cannot discharge.
    """
    total_with_goals = 0
    discharged_count = 0
    remaining = skeleton
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        entry = M.Head(remaining)()
        goal = ObligationSkeletonEntryGoal(entry)()
        if M.IdentityCompare(goal, M.EmptyList)() is M.false_value:
            total_with_goals = total_with_goals + 1
            if M.TermEqual(goal, conclusion_goal)() is M.truth_value:
                remaining = M.Tail(remaining)()
                continue
            plan = Imod.RewriteSearch(start, goal, rules, registry)()
            if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
                obligation_id = pretty(ObligationSkeletonEntryId(entry)(), registry)
                description = pretty(ObligationSkeletonEntryDescription(entry)(), registry)
                goal_text = pretty(goal, registry)
                return obligation_id, description, goal_text, discharged_count, total_with_goals
            discharged_count = discharged_count + 1
        remaining = M.Tail(remaining)()
    return None, None, None, discharged_count, total_with_goals


def attempt_training_record(runtime, packs, record, rules_pack_name, step_budget=20):
    registry = M.FromContextGetConstructors(runtime.graph)()
    problem_statement = TrainingRecordProblemStatement(record)()
    record_id_text = _record_id_text(problem_statement, registry)
    start = TrainingRecordMeaningStructure(record)()
    skeleton = TrainingRecordObligationSkeleton(record)()
    conclusion_goal = ObligationSkeletonConclusionGoal(skeleton)()
    hint = TrainingRecordStrategyHint(record)()
    heuristic = runtime.theorem_heuristic

    rules = None
    if rules_pack_name is not None:
        rules = packs.by_name(rules_pack_name).rule_chain

    if M.IdentityCompare(conclusion_goal, M.EmptyList)() is M.truth_value:
        reason = "obligation skeleton carries no conclusion goal; nothing to prove"
        attempt = AttemptResult(
            ProblemStatementId(problem_statement)(),
            L.FailedLabel,
            M.EmptyList,
            char_chain(reason),
        )()
        return attempt, AttemptSummary(
            record_id_text, "FAILURE", "none", 0.0, "n/a", "n/a", False, reason
        )

    # 1) Strategy-hinted planner run: the hint becomes a PlannerAlternative
    #    carrying the trainer-supplied method on the problem's root obligation.
    planner_root_status = L.PendingLabel
    alternative_status = M.EmptyList
    try:
        methods = M.EmptyList
        if M.IdentityCompare(hint, M.EmptyList)() is M.false_value:
            methods = M.Pair(hint, M.EmptyList)
        problem = Plannermod.PlannerProblem(start, conclusion_goal, rules, heuristic, methods)()
        state = Plannermod.PlannerState(problem, registry)()
        final_state = Plannermod.PlannerRun(runtime.graph, state, step_budget)()
        planner_root_status = _planner_root_status(final_state)
        if M.IdentityCompare(hint, M.EmptyList)() is M.false_value:
            alternative_status = _planner_alternative_status(final_state, hint)
    except Exception as exc:  # noqa: BLE001 - the attempt cycle must not die silently
        planner_root_status = L.FailedLabel
        alternative_status = L.FailedLabel

    # 2) Invariance-pipeline attempt from the strategy hint's observable.
    status = L.PendingLabel
    derivation = M.EmptyList
    method_text = "none"
    failure_reason = M.EmptyList
    elapsed = 0.0

    phi = M.EmptyList
    if M.IdentityCompare(hint, M.EmptyList)() is M.false_value:
        phi = StrategyHintObservable(hint)()

    started = time.time()
    if M.IdentityCompare(phi, M.EmptyList)() is M.false_value:
        derivation = runtime.prove(start, conclusion_goal, rules, heuristic, phi)
        elapsed = time.time() - started
        if Imod.IsUnreachable(derivation)() is M.truth_value:
            derivation = M.EmptyList
            reason = (
                "conclusion obligation unreachable via invariant: "
                + pretty(conclusion_goal, registry)
            )
            failure_reason = char_chain(reason)
        elif M.IdentityCompare(derivation, M.EmptyList)() is M.false_value:
            status = L.ProvedLabel
            method_text = "invariance pipeline (strategy hint Invariance)"
            failure_reason = M.EmptyList

    # 3) Fallback to brute search over the rule chain.
    if M.IdentityCompare(status, L.ProvedLabel)() is M.false_value:
        started = time.time()
        fallback = runtime.prove(start, conclusion_goal, rules, heuristic, M.EmptyList)
        elapsed = time.time() - started
        if M.IdentityCompare(fallback, M.EmptyList)() is M.false_value:
            derivation = fallback
            status = L.ProvedLabel
            method_text = "brute search fallback"
            failure_reason = M.EmptyList

    # 4) Failure: audit the skeleton so the reason names the obligation.
    discharged_count = 0
    if M.IdentityCompare(status, L.ProvedLabel)() is M.false_value:
        obligation_id, description, goal_text, discharged_count, total_with_goals = (
            _first_undischarged_obligation(
                runtime, start, skeleton, conclusion_goal, rules, registry
            )
        )
        if obligation_id is not None:
            reason = (
                "obligation "
                + obligation_id
                + " ("
                + description
                + ") not discharged: "
                + goal_text
                + " not derivable from the meaning structure"
            )
        else:
            reason = (
                "conclusion obligation not proved by search: "
                + pretty(conclusion_goal, registry)
            )
        failure_reason = char_chain(reason)
        if discharged_count > 0:
            status = L.PendingLabel

    # 5) Retain successful derivations in the graph's derivation store.
    retained = False
    if M.IdentityCompare(status, L.ProvedLabel)() is M.truth_value:
        runtime.graph.add_derivation(start, conclusion_goal, derivation)
        retained = True

    attempt = AttemptResult(
        ProblemStatementId(problem_statement)(),
        status,
        derivation,
        failure_reason,
    )()

    if M.IdentityCompare(status, L.ProvedLabel)() is M.truth_value:
        status_text = "SUCCESS"
    elif M.IdentityCompare(status, L.PendingLabel)() is M.truth_value:
        status_text = "PARTIAL"
    else:
        status_text = "FAILURE"

    reason_text = ""
    if M.IdentityCompare(failure_reason, M.EmptyList)() is M.false_value:
        reason_text = pretty(failure_reason, registry)

    return attempt, AttemptSummary(
        record_id_text,
        status_text,
        method_text,
        elapsed,
        _status_text(planner_root_status, registry),
        _status_text(alternative_status, registry),
        retained,
        reason_text,
    )


def _status_text(status, registry):
    if M.IdentityCompare(status, L.ProvedLabel)() is M.truth_value:
        return "Proved"
    if M.IdentityCompare(status, L.FailedLabel)() is M.truth_value:
        return "Failed"
    if M.IdentityCompare(status, L.PendingLabel)() is M.truth_value:
        return "Pending"
    if M.IdentityCompare(status, M.EmptyList)() is M.truth_value:
        return "none"
    return pretty(status, registry)


def _record_id_text(problem_statement, registry):
    """Problem id as text: from the machine id chain directly, falling back to pretty."""
    text = _chain_text(ProblemStatementId(problem_statement)())
    if text:
        return text
    return pretty(ProblemStatementId(problem_statement)(), registry)


__all__ = [
    name for name in globals() if not name.startswith("_")
]
