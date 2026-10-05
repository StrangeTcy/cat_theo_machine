# ============================================================
# CL4 — Candidate Macro Expander & Independent Evaluator
# Unrolls untrusted macro candidate definitions into primitive
# derivation steps and evaluates them with Checker B.
# ============================================================
from . import checker_b as CheckerB
from . import labels as L
from . import machine as M
from . import proof as P


class CandidateMacro(M.Edge):
    """
    Structured envelope for an untrusted candidate derivation macro.
    inputs: [macro_id, start_pattern, goal_pattern, plan]
    results: Pair(CandidateMacroLabel, Pair(macro_id, Pair(start_pattern, Pair(goal_pattern, Pair(plan, EmptyList)))))
    """

    def __init__(self, macro_id, start_pattern, goal_pattern, plan):
        self.macro_id = macro_id
        self.start_pattern = start_pattern
        self.goal_pattern = goal_pattern
        self.plan = plan
        self.result = M.Pair(
            L.CandidateMacroLabel,
            M.Pair(
                macro_id,
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
                macro_id,
                M.Pair(
                    start_pattern,
                    M.Pair(
                        goal_pattern,
                        M.Pair(plan, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CandidateMacroID(M.Edge):
    def __init__(self, macro):
        self.result = M.Head(M.Tail(macro)())()
        super().__init__(inputs=M.Pair(macro, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateMacroStartPattern(M.Edge):
    def __init__(self, macro):
        self.result = M.Head(M.Tail(M.Tail(macro)())())()
        super().__init__(inputs=M.Pair(macro, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateMacroGoalPattern(M.Edge):
    def __init__(self, macro):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(macro)())())())()
        super().__init__(inputs=M.Pair(macro, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateMacroPlan(M.Edge):
    def __init__(self, macro):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(macro)())())())()
        )()
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
    Full validation pipeline: Expands candidate macro on instance, checks
    validity with independent Checker B, and returns a verified ProofReceipt.
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
        exp_res = ExpandCandidateMacro(
            macro, instance_start, instance_goal, self.registry
        )()
        exp_tag = M.Head(exp_res)()

        if M.IdentityCompare(exp_tag, L.CandidateExpandedLabel)() is M.false_value:
            return exp_res

        derivation = M.Head(M.Tail(exp_res)())()
        new_reg = M.Head(M.Tail(M.Tail(exp_res)())())()

        verify_res = CheckerB.VerifyDerivation(
            derivation, instance_start, instance_goal, trusted_rules, new_reg
        )()
        verify_tag = M.Head(verify_res)()

        if (
            M.IdentityCompare(verify_tag, L.DerivationVerifiedLabel)()
            is M.false_value
        ):
            return verify_res

        session_id = CandidateMacroID(macro)()
        receipt = M.Pair(
            L.ProofReceiptLabel,
            M.Pair(
                session_id,
                M.Pair(
                    instance_start,
                    M.Pair(
                        instance_goal,
                        M.Pair(
                            derivation,
                            M.Pair(trusted_rules, M.EmptyList),
                        ),
                    ),
                ),
            ),
        )

        return M.Pair(
            L.CandidateEvaluatedLabel,
            M.Pair(receipt, M.Pair(new_reg, M.EmptyList)),
        )

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

    def _eval_suite_rec(
        self, cur, macro, trusted_rules, reg, passed_list, failed_list
    ):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.Pair(
                L.HoldoutSuiteResultLabel,
                M.Pair(
                    passed_list,
                    M.Pair(failed_list, M.EmptyList),
                ),
            )

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
                next_passed = M.Pair(item, passed_list)
                next_reg = M.Head(M.Tail(M.Tail(eval_res)())())()
                return self._eval_suite_rec(
                    M.Tail(cur)(),
                    macro,
                    trusted_rules,
                    next_reg,
                    next_passed,
                    failed_list,
                )
            next_failed = M.Pair(item, failed_list)
            return self._eval_suite_rec(
                M.Tail(cur)(),
                macro,
                trusted_rules,
                reg,
                passed_list,
                next_failed,
            )

        if is_passed is M.false_value:
            next_passed = M.Pair(item, passed_list)
            return self._eval_suite_rec(
                M.Tail(cur)(),
                macro,
                trusted_rules,
                reg,
                next_passed,
                failed_list,
            )
        next_failed = M.Pair(item, failed_list)
        return self._eval_suite_rec(
            M.Tail(cur)(),
            macro,
            trusted_rules,
            reg,
            passed_list,
            next_failed,
        )

    def _evaluate_suite(self, macro, holdouts, trusted_rules):
        return self._eval_suite_rec(
            holdouts,
            macro,
            trusted_rules,
            self.registry,
            M.EmptyList,
            M.EmptyList,
        )

    def __call__(self):
        return self.result


__all__ = (
    "CandidateMacro",
    "CandidateMacroID",
    "CandidateMacroStartPattern",
    "CandidateMacroGoalPattern",
    "CandidateMacroPlan",
    "ExpandCandidateMacro",
    "EvaluateCandidateProof",
    "AblationTrial",
    "EvaluateHoldoutSuite",
)
