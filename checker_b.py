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

        in_ruleset = self._rule_in_ruleset(rule, trusted_rules)
        if in_ruleset is M.false_value:
            return M.Pair(L.UnknownRuleLabel, M.Pair(rule, M.EmptyList))

        derived = self._apply_action(action, current, self.registry)
        if M.Compare(derived, next_term)() is M.false_value:
            if (
                self._knowledge_reproduces(rule, current, next_term)()
                is M.truth_value
            ):
                return M.Pair(L.StepVerifiedLabel, M.Pair(next_term, M.EmptyList))
            return M.Pair(
                L.ConclusionMutationLabel,
                M.Pair(derived, M.Pair(next_term, M.EmptyList)),
            )

        return M.Pair(L.StepVerifiedLabel, M.Pair(next_term, M.EmptyList))

    def _apply_knowledge_rule(self, rule, current):
        facts = P.KnowledgeFacts(current)()
        bindings_list = P.JoinPremises(P.RulePremises(rule)(), facts, M.EmptyList)()
        if M.IdentityCompare(bindings_list, M.EmptyList)() is M.truth_value:
            return current
        bindings = M.Head(bindings_list)()
        if P.ReplacementIsFactList(rule)() is M.truth_value:
            return P.ApplyKnowledgeRewrite(current, rule, bindings)()
        inst = M.Instantiate(P.RuleReplacement(rule)(), bindings)()
        conclusion = M.CanonicalArithmeticTerm(M.Head(inst)(), self.registry)()
        return P.Knowledge(M.Pair(conclusion, facts))()

    def _knowledge_reproduces(self, rule, current, next_term):
        if P.IsKnowledge(current)() is M.false_value:
            return M.false_value
        if M.Compare(current, next_term)() is M.truth_value:
            return M.truth_value
        facts = P.KnowledgeFacts(current)()
        premises = P.RulePremises(rule)()
        bindings_list = P.JoinPremises(premises, facts, M.EmptyList)()
        remaining = bindings_list
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            bindings = M.Head(remaining)()
            if P.ReplacementIsFactList(rule)() is M.truth_value:
                candidate = P.ApplyKnowledgeRewrite(current, rule, bindings)()
                if M.Compare(candidate, next_term)() is M.truth_value:
                    return M.truth_value
            else:
                inst = M.Instantiate(P.RuleReplacement(rule)(), bindings)()
                conclusion = M.CanonicalArithmeticTerm(
                    M.Head(inst)(), self.registry
                )()
                plain = P.Knowledge(M.Pair(conclusion, facts))()
                if M.Compare(plain, next_term)() is M.truth_value:
                    return M.truth_value
                normalized = P.NormalizeKnowledge(plain, self.registry)()
                if M.Compare(normalized, next_term)() is M.truth_value:
                    return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value

    def _apply_action(self, action, current, registry):
        if P.IsTheoremAction(action)() is M.truth_value:
            rule = P.ActionRule(action)()
            if P.IsKnowledge(current)() is M.truth_value:
                return self._apply_knowledge_rule(rule, current)
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
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return M.false_value
        rule = M.Head(rules)()
        if M.IdentityCompare(rule, target_rule)() is M.truth_value:
            return M.truth_value
        return self._rule_in_ruleset(target_rule, M.Tail(rules)())

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

    def _reaches(self, last_term, goal):
        if P.IsKnowledge(goal)() is M.truth_value:
            if P.IsKnowledge(last_term)() is M.truth_value:
                return P.FactsCover(
                    P.KnowledgeFacts(goal)(), P.KnowledgeFacts(last_term)()
                )()
        return M.Compare(last_term, goal)()

    def _check_steps(self, cur_steps, last_term, computed, goal, trusted_rules):
        if M.IdentityCompare(cur_steps, M.EmptyList)() is M.truth_value:
            if self._reaches(last_term, goal) is M.false_value:
                return M.Pair(
                    L.GoalMismatchLabel,
                    M.Pair(last_term, M.Pair(goal, M.EmptyList)),
                )
            return M.Pair(L.DerivationVerifiedLabel, M.Pair(goal, M.EmptyList))

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
            return step_res

        next_last = M.Head(M.Tail(step_res)())()
        next_computed = M.Pair(next_last, computed)
        return self._check_steps(
            M.Tail(cur_steps)(),
            next_last,
            next_computed,
            goal,
            trusted_rules,
        )

    def _check(self, derivation, start, goal, trusted_rules):
        steps = P.DerivationSteps(derivation, self.registry)()
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            if self._reaches(start, goal) is M.truth_value:
                return M.Pair(L.DerivationVerifiedLabel, M.EmptyList)
            return M.Pair(
                L.GoalMismatchLabel,
                M.Pair(start, M.Pair(goal, M.EmptyList)),
            )

        computed = M.Pair(start, M.EmptyList)
        return self._check_steps(steps, start, computed, goal, trusted_rules)

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
        rec_fields = M.Tail(receipt)()
        rec_session = M.Head(rec_fields)()
        rec_start = M.Head(M.Tail(rec_fields)())()
        rec_goal = M.Head(M.Tail(M.Tail(rec_fields)())())()
        rec_derivation = M.Head(M.Tail(M.Tail(M.Tail(rec_fields)())())())()

        pol_fields = M.Tail(policy)()
        pol_session = M.Head(pol_fields)()
        pol_start = M.Head(M.Tail(pol_fields)())()
        pol_goal = M.Head(M.Tail(M.Tail(pol_fields)())())()

        if M.Compare(rec_session, pol_session)() is M.false_value:
            return M.Pair(
                L.CandidateScopeMismatchLabel,
                M.Pair(rec_session, M.Pair(pol_session, M.EmptyList)),
            )

        if M.Compare(rec_start, pol_start)() is M.false_value:
            return M.Pair(
                L.PremiseMismatchLabel,
                M.Pair(rec_start, M.Pair(pol_start, M.EmptyList)),
            )

        if M.Compare(rec_goal, pol_goal)() is M.false_value:
            return M.Pair(
                L.GoalMismatchLabel,
                M.Pair(rec_goal, M.Pair(pol_goal, M.EmptyList)),
            )

        return VerifyDerivation(
            rec_derivation, rec_start, rec_goal, trusted_rules, self.registry
        )()

    def __call__(self):
        return self.result


__all__ = (
    "VerifyProofStep",
    "VerifyDerivation",
    "VerifyProofReceipt",
)
