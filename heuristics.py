from __future__ import annotations

from .core import Edge, EmptyList, Head, Pair, Tail
from . import machine as M
from . import proof as Pmod
from . import trees as Tmod


class HeuristicGoalHeadIndex(Edge):
    """Collect a Tree/set of all TermHead labels appearing in `goal`.

    This is a search heuristic utility used for goal-directed rewrite-site pruning.
    The returned `index` is a Patricia-tree-like map where each head label is both
    key and fact.
    """

    def __init__(self, goal, registry):
        index = Tmod.Tree(M.EmptyList)
        stack = M.Pair(goal, M.EmptyList)
        while M.IdentityCompare(stack, M.EmptyList)() is M.false_value:
            current = M.Head(stack)()
            stack = M.Tail(stack)()
            head = Pmod.TermHead(current, registry)()
            if M.IdentityCompare(head, M.EmptyList)() is M.false_value:
                index = Tmod.TreeInsert(index, head, head, registry)()
            if M.IsPair(current)() is M.truth_value:
                stack = M.Pair(M.Head(current)(), M.Pair(M.Tail(current)(), stack))

        self.result = index
        super().__init__(inputs=Pair(goal, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class HeuristicGoalHeadNeighborhood(Edge):
    """Backward closure of goal heads through unary rewrite rules."""

    def __init__(self, goal, rules, registry):
        self.registry = registry
        current = HeuristicGoalHeadIndex(goal, registry)()
        changed = M.truth_value
        while changed is M.truth_value:
            pass_result = self._pass(rules, current)
            current = Head(pass_result)()
            changed = Head(Tail(pass_result)())()
        self.result = current
        super().__init__(inputs=Pair(goal, Pair(rules, Pair(registry, EmptyList))), results=self.result)

    def _pass(self, rules, index):
        current_rules = rules
        current_index = index
        changed = M.false_value
        while M.IdentityCompare(current_rules, EmptyList)() is M.false_value:
            rule = Head(current_rules)()
            current_rules = Tail(current_rules)()
            if Pmod.RuleIsUnary(rule)() is M.false_value:
                continue
            replacement_head = Pmod.TermHead(Pmod.RuleReplacement(rule)(), self.registry)()
            if M.IdentityCompare(replacement_head, EmptyList)() is M.truth_value:
                continue
            replacement_found = Tmod.TreeLookup(current_index, replacement_head, self.registry)()
            if M.IdentityCompare(replacement_found, EmptyList)() is M.truth_value:
                continue
            pattern = Pmod.RulePattern(rule)()
            if Pmod.IsVarPattern(pattern)() is M.truth_value:
                continue
            pattern_head = Pmod.TermHead(pattern, self.registry)()
            if M.IdentityCompare(pattern_head, EmptyList)() is M.truth_value:
                continue
            pattern_found = Tmod.TreeLookup(current_index, pattern_head, self.registry)()
            if M.IdentityCompare(pattern_found, EmptyList)() is M.false_value:
                continue
            current_index = Tmod.TreeInsert(current_index, pattern_head, pattern_head, self.registry)()
            changed = M.truth_value
        return Pair(current_index, Pair(changed, EmptyList))

    def __call__(self):
        return self.result


class HeuristicGoalHeadAllowsSubterm(Edge):
    """Predicate: subterm's head is present in goal-head index."""

    def __init__(self, goal_head_index, subterm, registry):
        head = Pmod.TermHead(subterm, registry)()
        if M.IdentityCompare(head, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            found = Tmod.TreeLookup(goal_head_index, head, registry)()
            self.result = M.false_value if M.IdentityCompare(found, M.EmptyList)() is M.truth_value else M.truth_value
        super().__init__(inputs=Pair(goal_head_index, Pair(subterm, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class Heuristic(Edge):
    def __init__(self, search_mode, rule_order_mode, beam_width, alpha, beta, canonical_strength):
        self.result = Pair(
            search_mode,
            Pair(rule_order_mode, Pair(beam_width, Pair(alpha, Pair(beta, Pair(canonical_strength, EmptyList))))),
        )
        super().__init__(
            inputs=Pair(
                search_mode,
                Pair(rule_order_mode, Pair(beam_width, Pair(alpha, Pair(beta, Pair(canonical_strength, EmptyList))))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class HeuristicSearchMode(Edge):
    def __init__(self, h):
        self.result = Head(h)()
        super().__init__(inputs=Pair(h, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HeuristicRuleOrder(Edge):
    def __init__(self, h):
        self.result = Head(Tail(h)())()
        super().__init__(inputs=Pair(h, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HeuristicBeamWidth(Edge):
    def __init__(self, h):
        self.result = Head(Tail(Tail(h)())())()
        super().__init__(inputs=Pair(h, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HeuristicAlpha(Edge):
    def __init__(self, h):
        self.result = Head(Tail(Tail(Tail(h)())())())()
        super().__init__(inputs=Pair(h, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HeuristicBeta(Edge):
    def __init__(self, h):
        self.result = Head(Tail(Tail(Tail(Tail(h)())())())())()
        super().__init__(inputs=Pair(h, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HeuristicCanonicalStrength(Edge):
    def __init__(self, h):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(h)())())())())())()
        super().__init__(inputs=Pair(h, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HeuristicCanonicalTerm(Edge):
    def __init__(self, term, registry):
        self.registry = registry
        self.result = self._canonical(term)
        super().__init__(inputs=Pair(term, Pair(registry, EmptyList)), results=self.result)

    def _canonical_facts(self, facts):
        if M.IdentityCompare(facts, EmptyList)() is M.truth_value:
            return EmptyList
        here = self._canonical(Head(facts)())
        rest = self._canonical_facts(Tail(facts)())
        return Pair(here, rest)

    def _canonical(self, term):
        if Pmod.IsKnowledge(term)() is M.truth_value:
            facts = self._canonical_facts(Pmod.KnowledgeFacts(term)())
            return Pmod.NormalizeKnowledge(Pmod.Knowledge(facts)(), self.registry)()
        if M.IsPair(term)() is M.truth_value:
            return Pair(self._canonical(Head(term)()), self._canonical(Tail(term)()))
        return term

    def __call__(self):
        return self.result


class HeuristicCanonicalize(Edge):
    def __init__(self, term, h, registry):
        # Normalization is deterministic/idempotent for our current canonicalizer.
        # So "strength" is treated as an enable/disable flag:
        # - 0: off
        # - nonzero: on (one pass)
        strength = HeuristicCanonicalStrength(h)()
        if M.NatEq(strength, M.Zero, registry)() is M.truth_value:
            self.result = term
        else:
            self.result = HeuristicCanonicalTerm(term, registry)()
        super().__init__(inputs=Pair(term, Pair(h, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
