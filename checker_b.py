from __future__ import annotations

from . import graph_task as GT
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
        if M.IsPair(action)() is M.truth_value:
            if M.IdentityCompare(M.Head(action)(), L.PolynomialGridActionLabel)() is M.truth_value:
                return self._verify_polynomial_grid(step, action, trusted_rules)
            if M.IdentityCompare(M.Head(action)(), L.SignedPolynomialActionLabel)() is M.truth_value:
                if self._rule_in_ruleset(L.SignedPolynomialRuleLabel, trusted_rules) is M.false_value:
                    return M.Pair(L.UnknownRuleLabel, M.Pair(L.SignedPolynomialRuleLabel, M.EmptyList))
                from .signed_polynomial import VerifySignedPolynomialStep

                return VerifySignedPolynomialStep(step, action, trusted_rules, self.registry)()
        rule = P.ActionRule(action)()
        current = P.StepCurrent(step, self.registry)()
        next_term = P.StepNext(step, self.registry)()

        in_ruleset = self._rule_in_ruleset(rule, trusted_rules)
        if in_ruleset is M.false_value:
            return M.Pair(L.UnknownRuleLabel, M.Pair(rule, M.EmptyList))

        recorded = P.ActionBindings(action)()
        leftovers = self._replacement_leftovers(rule, current)
        if (
            M.IdentityCompare(leftovers, M.EmptyList)() is M.false_value
            and P.ContainsVar(next_term)() is M.truth_value
        ):
            return M.Pair(
                L.UnboundVariableLabel,
                M.Pair(next_term, M.EmptyList),
            )

        derived = self._apply_action(action, current, self.registry)
        if M.Compare(derived, next_term)() is M.false_value:
            if (
                self._knowledge_reproduces(
                    rule, current, next_term, recorded
                )
                is M.truth_value
            ):
                return M.Pair(L.StepVerifiedLabel, M.Pair(next_term, M.EmptyList))
            return M.Pair(
                L.ConclusionMutationLabel,
                M.Pair(derived, M.Pair(next_term, M.EmptyList)),
            )

        return M.Pair(L.StepVerifiedLabel, M.Pair(next_term, M.EmptyList))

    def _verify_polynomial_grid(self, step, action, trusted_rules):
        # Explicit decision-procedure authority, separate from rewrite rules.
        # Do not call the certificate generator or symbolic search here.
        from . import playground as PG

        if self._rule_in_ruleset(L.PolynomialGridRuleLabel, trusted_rules) is M.false_value:
            return M.Pair(L.UnknownRuleLabel, M.Pair(L.PolynomialGridRuleLabel, M.EmptyList))
        current = P.StepCurrent(step, self.registry)()
        nxt = P.StepNext(step, self.registry)()
        refusal = M.Pair(L.ConclusionMutationLabel, M.Pair(current, M.Pair(nxt, M.EmptyList)))
        if PG.ExactArity(M.Tail(action)(), M.one, self.registry)() is M.false_value:
            return refusal
        record = M.Head(M.Tail(action)())()
        if M.IsPair(record)() is M.false_value:
            return refusal
        if M.IdentityCompare(M.Head(record)(), L.PolynomialIdentityLabel)() is M.false_value:
            return refusal
        fields = M.Tail(record)()
        if PG.ExactArity(fields, M.seven, self.registry)() is M.false_value:
            return refusal
        lhs = M.Head(fields)()
        fields = M.Tail(fields)()
        rhs = M.Head(fields)()
        fields = M.Tail(fields)()
        variables = M.Head(fields)()
        fields = M.Tail(fields)()
        degrees = M.Head(fields)()
        fields = M.Tail(fields)()
        count = M.Head(fields)()
        fields = M.Tail(fields)()
        verdict = M.Head(fields)()
        witness = M.Head(M.Tail(fields)())()
        if M.AndAtom(M.Compare(lhs, current)(), M.Compare(rhs, nxt)())() is M.false_value:
            return refusal
        if M.IdentityCompare(verdict, M.truth_value)() is M.false_value:
            return refusal
        if M.IdentityCompare(witness, M.EmptyList)() is M.false_value:
            return refusal
        # Recompute exact syntax, variable coverage, degree bounds, full grid
        # and machine arithmetic. The submitted grid cannot choose its size.
        checked = PG.PolynomialIdentityByGrid(lhs, rhs, variables, self.registry)()
        registry = M.Head(M.Tail(checked)())()
        fresh_fields = M.Tail(M.Head(checked)())()
        fresh_fields = M.Tail(M.Tail(M.Tail(fresh_fields)())())()
        fresh_degrees = M.Head(fresh_fields)()
        fresh_fields = M.Tail(fresh_fields)()
        fresh_count = M.Head(fresh_fields)()
        fresh_verdict = M.Head(M.Tail(fresh_fields)())()
        if M.IdentityCompare(fresh_verdict, M.truth_value)() is M.false_value:
            return refusal
        if M.NatEq(count, fresh_count, registry)() is M.false_value:
            return refusal
        while M.IdentityCompare(fresh_degrees, M.EmptyList)() is M.false_value:
            if M.IsPair(degrees)() is M.false_value:
                return refusal
            if M.NatEq(M.Head(degrees)(), M.Head(fresh_degrees)(), registry)() is M.false_value:
                return refusal
            degrees = M.Tail(degrees)()
            fresh_degrees = M.Tail(fresh_degrees)()
        if M.IdentityCompare(degrees, M.EmptyList)() is M.false_value:
            return refusal
        return M.Pair(L.StepVerifiedLabel, M.Pair(nxt, M.EmptyList))

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

    def _vars_missing_from_bindings(self, vars_list, bindings):
        if M.IdentityCompare(vars_list, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        var = M.Head(vars_list)()
        rest = self._vars_missing_from_bindings(M.Tail(vars_list)(), bindings)
        found = M.FindBinding(bindings, var)()
        if M.IdentityCompare(M.Head(found)(), M.truth_value)() is M.truth_value:
            return rest
        return M.Pair(var, rest)

    def _replacement_leftovers(self, rule, current):
        if P.IsKnowledge(current)() is M.false_value:
            return M.EmptyList
        facts = P.KnowledgeFacts(current)()
        joins = P.JoinPremises(P.RulePremises(rule)(), facts, M.EmptyList)()
        if M.IdentityCompare(joins, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        bindings = M.Head(joins)()
        template_vars = GT.CollectUnboundVarPatterns(P.RuleReplacement(rule)())()
        return self._vars_missing_from_bindings(template_vars, bindings)

    def _fill_knowledge(self, candidate, recorded):
        facts = P.KnowledgeFacts(candidate)()
        filled = GT.FillUnboundWitnessesInList(facts, recorded)()
        if M.IdentityCompare(M.Head(filled)(), M.truth_value)() is M.false_value:
            return M.Pair(M.false_value, candidate)
        return M.Pair(M.truth_value, P.Knowledge(M.Tail(filled)())())

    def _knowledge_reproduces(self, rule, current, next_term, recorded):
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
                filled = self._fill_knowledge(candidate, recorded)
                if M.IdentityCompare(M.Head(filled)(), M.truth_value)() is M.truth_value:
                    if M.Compare(M.Tail(filled)(), next_term)() is M.truth_value:
                        return M.truth_value
            else:
                inst = M.Instantiate(P.RuleReplacement(rule)(), bindings)()
                raw = M.Head(inst)()
                filled_term = GT.FillUnboundWitnesses(raw, recorded)()
                if M.IdentityCompare(M.Head(filled_term)(), M.truth_value)() is M.truth_value:
                    raw = M.Tail(filled_term)()
                conclusion = M.CanonicalArithmeticTerm(raw, self.registry)()
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
