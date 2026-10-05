from __future__ import annotations

from . import checker_b as CheckerB
from . import labels as L
from . import machine as M
from . import proof as P


class CandidateMacro(M.Edge):
    """
    An untrusted candidate macro / derivation schema.

    Shape: Pair(CandidateMacroLabel, Pair(candidate_id, Pair(start_pattern, Pair(goal_pattern, Pair(plan, EmptyList)))))
    """

    def __init__(self, candidate_id, start_pattern, goal_pattern, plan):
        self.result = M.Pair(
            L.CandidateMacroLabel,
            M.Pair(
                candidate_id,
                M.Pair(
                    start_pattern,
                    M.Pair(
                        goal_pattern,
                        M.Pair(plan, M.EmptyList),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                candidate_id,
                M.Pair(
                    start_pattern,
                    M.Pair(goal_pattern, M.Pair(plan, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CandidateMacroID(M.Edge):
    def __init__(self, macro):
        fields = M.Tail(macro)()
        self.result = M.Head(fields)()
        super().__init__(inputs=M.Pair(macro, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateMacroStartPattern(M.Edge):
    def __init__(self, macro):
        fields = M.Tail(macro)()
        self.result = M.Head(M.Tail(fields)())()
        super().__init__(inputs=M.Pair(macro, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateMacroGoalPattern(M.Edge):
    def __init__(self, macro):
        fields = M.Tail(macro)()
        self.result = M.Head(M.Tail(M.Tail(fields)())())()
        super().__init__(inputs=M.Pair(macro, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateMacroPlan(M.Edge):
    def __init__(self, macro):
        fields = M.Tail(macro)()
        self.result = M.Head(M.Tail(M.Tail(M.Tail(fields)())())())()
        super().__init__(inputs=M.Pair(macro, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ExpandCandidateMacro(M.Edge):
    """
    Expands / unrolls an untrusted candidate macro on concrete problem instances
    into a full primitive derivation chain.
    """

    def __init__(self, macro, instance_start, instance_goal, registry):
        self.registry = registry
        self.result = self._expand(macro, instance_start, instance_goal)
        super().__init__(
            inputs=M.Pair(
                macro,
                M.Pair(
                    instance_start,
                    M.Pair(
                        instance_goal,
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _expand(self, macro, instance_start, instance_goal):
        start_pattern = CandidateMacroStartPattern(macro)()
        goal_pattern = CandidateMacroGoalPattern(macro)()
        plan = CandidateMacroPlan(macro)()

        start_match = M.Match(start_pattern, instance_start)()
        if M.IdentityCompare(M.Head(start_match)(), M.truth_value)() is M.false_value:
            return M.Pair(L.CandidateMatchFailureLabel, M.EmptyList)

        goal_match = M.Match(goal_pattern, instance_goal)()
        if M.IdentityCompare(M.Head(goal_match)(), M.truth_value)() is M.false_value:
            return M.Pair(L.CandidateMatchFailureLabel, M.EmptyList)

        start_bindings = M.Tail(start_match)()
        goal_bindings = M.Tail(goal_match)()
        merged = M.MergeBindings(start_bindings, goal_bindings)()

        if M.IdentityCompare(M.Head(merged)(), M.truth_value)() is M.false_value:
            return M.Pair(L.CandidateMatchFailureLabel, M.EmptyList)

        merged_bindings = M.Tail(merged)()
        der_res = P.BuildDerivation(
            instance_start, plan, self.registry, merged_bindings
        )()
        derivation = M.Head(der_res)()
        new_registry = M.Head(M.Tail(der_res)())()

        return M.Pair(
            L.CandidateExpandedLabel,
            M.Pair(derivation, M.Pair(new_registry, M.EmptyList)),
        )

    def __call__(self):
        return self.result


class EvaluateCandidateProof(M.Edge):
    """
    Evaluates an untrusted candidate macro on a problem instance by expanding it
    into primitive steps and submitting the derivation to independent Checker B.
    """

    def __init__(
        self, macro, instance_start, instance_goal, trusted_rules, registry
    ):
        self.registry = registry
        self.result = self._evaluate(
            macro, instance_start, instance_goal, trusted_rules
        )
        super().__init__(
            inputs=M.Pair(
                macro,
                M.Pair(
                    instance_start,
                    M.Pair(
                        instance_goal,
                        M.Pair(
                            trusted_rules,
                            M.Pair(registry, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _evaluate(self, macro, instance_start, instance_goal, trusted_rules):
        expanded = ExpandCandidateMacro(
            macro, instance_start, instance_goal, self.registry
        )()
        tag = M.Head(expanded)()

        if M.IdentityCompare(tag, L.CandidateExpandedLabel)() is M.false_value:
            return expanded  # Expansion or matching failed

        derivation = M.Head(M.Tail(expanded)())()
        new_registry = M.Head(M.Tail(M.Tail(expanded)())())()

        # Submit expanded derivation to Checker B
        check_verdict = CheckerB.VerifyDerivation(
            derivation,
            instance_start,
            instance_goal,
            trusted_rules,
            new_registry,
        )()
        check_tag = M.Head(check_verdict)()

        if M.IdentityCompare(check_tag, L.DerivationVerifiedLabel)() is M.truth_value:
            return M.Pair(
                L.CandidateEvaluatedLabel,
                M.Pair(derivation, M.Pair(new_registry, M.EmptyList)),
            )

        return check_verdict  # Bubble up checker rejection reason

    def __call__(self):
        return self.result


class AblationTrial(M.Edge):
    """
    Performs an ablation check: verifies the candidate expands and passes
    independent checking, while verifying that the instance is not trivially
    closed without steps when start != goal.
    """

    def __init__(
        self, macro, instance_start, instance_goal, trusted_rules, registry
    ):
        self.registry = registry
        self.result = self._trial(
            macro, instance_start, instance_goal, trusted_rules
        )
        super().__init__(
            inputs=M.Pair(
                macro,
                M.Pair(
                    instance_start,
                    M.Pair(
                        instance_goal,
                        M.Pair(
                            trusted_rules,
                            M.Pair(registry, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _trial(self, macro, instance_start, instance_goal, trusted_rules):
        eval_res = EvaluateCandidateProof(
            macro, instance_start, instance_goal, trusted_rules, self.registry
        )()
        eval_tag = M.Head(eval_res)()

        if M.IdentityCompare(eval_tag, L.CandidateEvaluatedLabel)() is M.false_value:
            return eval_res

        # Ablation baseline check: start must not equal goal trivially
        is_trivially_closed = M.Compare(instance_start, instance_goal)()
        if is_trivially_closed is M.truth_value:
            ablation_status = L.FailedLabel
        else:
            ablation_status = L.ProvedLabel

        derivation = M.Head(M.Tail(eval_res)())()
        return M.Pair(
            L.AblationVerifiedLabel,
            M.Pair(
                derivation,
                M.Pair(ablation_status, M.EmptyList),
            ),
        )

    def __call__(self):
        return self.result


class EvaluateHoldoutSuite(M.Edge):
    """
    Evaluates a candidate macro against a suite of held-out positive and
    near-miss negative instances.

    Each instance is Pair(start, Pair(goal, Pair(expected_truth, EmptyList))).
    """

    def __init__(self, macro, holdouts, trusted_rules, registry):
        self.registry = registry
        self.result = self._evaluate_suite(macro, holdouts, trusted_rules)
        super().__init__(
            inputs=M.Pair(
                macro,
                M.Pair(
                    holdouts,
                    M.Pair(
                        trusted_rules,
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _evaluate_suite(self, macro, holdouts, trusted_rules):
        cur = holdouts
        passed_list = M.EmptyList
        failed_list = M.EmptyList
        reg = self.registry

        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            item = M.Head(cur)()
            inst_start = M.Head(item)()
            inst_goal = M.Head(M.Tail(item)())()
            expected = M.Head(M.Tail(M.Tail(item)())())()

            eval_res = EvaluateCandidateProof(
                macro, inst_start, inst_goal, trusted_rules, reg
            )()
            eval_tag = M.Head(eval_res)()
            is_passed = M.IdentityCompare(
                eval_tag, L.CandidateEvaluatedLabel
            )()
            is_expected_truth = M.IdentityCompare(expected, M.truth_value)()

            if is_expected_truth is M.truth_value:
                if is_passed is M.truth_value:
                    passed_list = M.Pair(item, passed_list)
                    reg = M.Head(M.Tail(M.Tail(eval_res)())())()
                else:
                    failed_list = M.Pair(item, failed_list)
            else:
                # Negative near-miss control: must be rejected
                if is_passed is M.false_value:
                    passed_list = M.Pair(item, passed_list)
                else:
                    failed_list = M.Pair(item, failed_list)

            cur = M.Tail(cur)()

        return M.Pair(
            L.HoldoutSuiteResultLabel,
            M.Pair(
                passed_list,
                M.Pair(failed_list, M.EmptyList),
            ),
        )

    def __call__(self):
        return self.result


def sync_from_namespace(namespace):
    for name in (
        "EmptyList",
        "truth_value",
        "false_value",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [
    "CandidateMacro",
    "CandidateMacroID",
    "CandidateMacroStartPattern",
    "CandidateMacroGoalPattern",
    "CandidateMacroPlan",
    "ExpandCandidateMacro",
    "EvaluateCandidateProof",
    "AblationTrial",
    "EvaluateHoldoutSuite",
]
