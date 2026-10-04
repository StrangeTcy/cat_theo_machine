from __future__ import annotations

from . import labels as L
from . import machine as M
from . import proof as P


class VerifyProofStep(M.Edge):
    """
    Independently verifies a single inference step against declared premises
    and a trusted rule without calling search or candidate generators.
    """

    def __init__(self, step, trusted_rules, premises, computed_steps, registry):
        self.registry = registry
        self.result = self._verify(step, trusted_rules, premises, computed_steps)
        super().__init__(
            inputs=M.Pair(
                step,
                M.Pair(
                    trusted_rules,
                    M.Pair(
                        premises,
                        M.Pair(
                            computed_steps,
                            M.Pair(registry, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _verify(self, step, trusted_rules, premises, computed_steps):
        action = P.StepAction(step, self.registry)()
        rule = P.ActionRule(action)()
        current = P.StepCurrent(step, self.registry)()
        next_term = P.StepNext(step, self.registry)()

        # 1. Check rule exists in trusted_rules via IdentityCompare
        in_ruleset = self._rule_in_ruleset(rule, trusted_rules)
        if in_ruleset is M.false_value:
            return M.Pair(L.UnknownRuleLabel, M.Pair(rule, M.EmptyList))

        # 2. Check that applying rule with action to current derives next_term
        derived = self._apply_action(action, current, self.registry)
        if M.Compare(derived, next_term)() is M.false_value:
            return M.Pair(
                L.ConclusionMutationLabel,
                M.Pair(derived, M.Pair(next_term, M.EmptyList)),
            )

        return M.Pair(L.StepVerifiedLabel, M.Pair(next_term, M.EmptyList))

    def _apply_action(self, action, current, registry):
        if P.IsTheoremAction(action)() is M.truth_value:
            rule = P.ActionRule(action)()
            bindings = P.ActionBindings(action)()
            if P.RuleIsUnary(rule)() is M.truth_value:
                pattern = P.RulePattern(rule)()
                replacement = P.RuleReplacement(rule)()
                match = M.Match(pattern, current)()
                flag = M.Head(match)()
                binds = M.Tail(match)()
                if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
                    merged = M.MergeBindings(bindings, binds)()
                    if (
                        M.IdentityCompare(M.Head(merged)(), M.truth_value)()
                        is M.truth_value
                    ):
                        inst = M.Instantiate(replacement, M.Tail(merged)())()
                        return M.CanonicalArithmeticTerm(
                            M.Head(inst)(), registry
                        )()
            return current
        if P.IsRewriteAction(action)() is M.truth_value:
            rule = P.ActionRule(action)()
            path = P.ActionPath(action)()
            return P.RewriteAtPath(rule, current, path, registry)()
        return current

    def _rule_in_ruleset(self, target_rule, rules):
        cur = rules
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            rule = M.Head(cur)()
            if M.IdentityCompare(rule, target_rule)() is M.truth_value:
                return M.truth_value
            cur = M.Tail(cur)()
        return M.false_value

    def __call__(self):
        return self.result


class VerifyDerivation(M.Edge):
    """
    Sequentially checks every step in a derivation chain against trusted rules
    and declared premises, confirming the final step reaches the goal.
    """

    def __init__(self, derivation, start, goal, trusted_rules, registry):
        self.registry = registry
        self.result = self._check(derivation, start, goal, trusted_rules)
        super().__init__(
            inputs=M.Pair(
                derivation,
                M.Pair(
                    start,
                    M.Pair(
                        goal,
                        M.Pair(
                            trusted_rules,
                            M.Pair(registry, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _check(self, derivation, start, goal, trusted_rules):
        steps = P.DerivationSteps(derivation, self.registry)()
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            if M.Compare(start, goal)() is M.truth_value:
                return M.Pair(L.DerivationVerifiedLabel, M.EmptyList)
            return M.Pair(L.GoalMismatchLabel, M.Pair(start, M.Pair(goal, M.EmptyList)))

        cur_steps = steps
        computed = M.Pair(start, M.EmptyList)
        last_term = start

        while M.IdentityCompare(cur_steps, M.EmptyList)() is M.false_value:
            step = M.Head(cur_steps)()
            step_current = P.StepCurrent(step, self.registry)()
            if M.Compare(step_current, last_term)() is M.false_value:
                return M.Pair(
                    L.StepDiscontinuityLabel,
                    M.Pair(step_current, M.Pair(last_term, M.EmptyList)),
                )

            step_res = VerifyProofStep(
                step, trusted_rules, computed, computed, self.registry
            )()
            tag = M.Head(step_res)()

            if M.IdentityCompare(tag, L.StepVerifiedLabel)() is M.false_value:
                return step_res  # Bubble up exact rejection reason

            last_term = M.Head(M.Tail(step_res)())()
            computed = M.Pair(last_term, computed)
            cur_steps = M.Tail(cur_steps)()

        # Final goal check
        if M.Compare(last_term, goal)() is M.false_value:
            return M.Pair(
                L.GoalMismatchLabel, M.Pair(last_term, M.Pair(goal, M.EmptyList))
            )

        return M.Pair(L.DerivationVerifiedLabel, M.Pair(goal, M.EmptyList))

    def __call__(self):
        return self.result


class VerifyProofReceipt(M.Edge):
    """
    Verifies a full proof receipt (Pair(ProofReceiptLabel, ...)) against policy
    and trusted rules snapshot.
    """

    def __init__(self, receipt, policy, trusted_rules, registry):
        self.registry = registry
        self.result = self._verify_receipt(receipt, policy, trusted_rules)
        super().__init__(
            inputs=M.Pair(
                receipt,
                M.Pair(
                    policy,
                    M.Pair(
                        trusted_rules,
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _verify_receipt(self, receipt, policy, trusted_rules):
        # Receipt: Pair(ProofReceiptLabel, Pair(session_id, Pair(start, Pair(goal, Pair(derivation, EmptyList)))))
        # Policy: Pair(CheckPolicyLabel, Pair(session_id, Pair(start, Pair(goal, EmptyList))))
        rec_fields = M.Tail(receipt)()
        rec_session = M.Head(rec_fields)()
        rec_start = M.Head(M.Tail(rec_fields)())()
        rec_goal = M.Head(M.Tail(M.Tail(rec_fields)())())()
        rec_derivation = M.Head(M.Tail(M.Tail(M.Tail(rec_fields)())())())()

        pol_fields = M.Tail(policy)()
        pol_session = M.Head(pol_fields)()
        pol_start = M.Head(M.Tail(pol_fields)())()
        pol_goal = M.Head(M.Tail(M.Tail(pol_fields)())())()

        # Session match
        if M.Compare(rec_session, pol_session)() is M.false_value:
            return M.Pair(
                L.CandidateScopeMismatchLabel,
                M.Pair(rec_session, M.Pair(pol_session, M.EmptyList)),
            )

        # Start match
        if M.Compare(rec_start, pol_start)() is M.false_value:
            return M.Pair(
                L.PremiseMismatchLabel,
                M.Pair(rec_start, M.Pair(pol_start, M.EmptyList)),
            )

        # Goal match
        if M.Compare(rec_goal, pol_goal)() is M.false_value:
            return M.Pair(
                L.GoalMismatchLabel, M.Pair(rec_goal, M.Pair(pol_goal, M.EmptyList))
            )

        # Verify derivation steps
        return VerifyDerivation(
            rec_derivation, rec_start, rec_goal, trusted_rules, self.registry
        )()

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
    "VerifyProofStep",
    "VerifyDerivation",
    "VerifyProofReceipt",
]
