from __future__ import annotations

from . import labels as L
from . import machine as M
from . import proof as P
from . import search as S


class Phi(M.Edge):
    def __init__(self, pattern):
        self.result = pattern
        super().__init__(inputs=M.Pair(pattern, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PhiPattern(M.Edge):
    def __init__(self, phi):
        self.result = phi
        super().__init__(inputs=M.Pair(phi, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StateFacts(M.Edge):
    def __init__(self, state):
        if P.IsKnowledge(state)() is M.truth_value:
            self.result = P.KnowledgeFacts(state)()
        else:
            self.result = state
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MatchPhiOnFacts(M.Edge):
    def __init__(self, phi, facts):
        self.pattern = PhiPattern(phi)()
        self.result = self._first(facts)
        super().__init__(inputs=M.Pair(phi, M.Pair(facts, M.EmptyList)), results=self.result)

    def _first(self, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)
        fact = M.Head(facts)()
        match = M.Match(self.pattern, fact)()
        if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(M.Tail(match)(), M.Pair(fact, M.EmptyList)))
        return self._first(M.Tail(facts)())

    def __call__(self):
        return self.result


class PhiReading(M.Edge):
    def __init__(self, state, phi):
        facts = StateFacts(state)()
        hit = MatchPhiOnFacts(phi, facts)()
        if M.IdentityCompare(M.Head(hit)(), M.truth_value)() is M.truth_value:
            bindings = M.Head(M.Tail(hit)())()
            inst = M.Instantiate(PhiPattern(phi)(), bindings)()
            self.result = M.Head(inst)()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(state, M.Pair(phi, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PhiHolds(M.Edge):
    def __init__(self, state, phi):
        facts = StateFacts(state)()
        hit = MatchPhiOnFacts(phi, facts)()
        self.result = M.Head(hit)()
        super().__init__(inputs=M.Pair(state, M.Pair(phi, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ReplacementFacts(M.Edge):
    def __init__(self, rule):
        replacement = P.RuleReplacement(rule)()
        if P.RuleIsUnary(rule)() is M.truth_value:
            self.result = M.Pair(replacement, M.EmptyList)
        else:
            self.result = replacement
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Preserves(M.Edge):
    def __init__(self, rule, phi, registry):
        pre = P.Knowledge(P.RulePremises(rule)())()
        post = P.Knowledge(ReplacementFacts(rule)())()
        pre_reading = PhiReading(pre, phi)()
        post_reading = PhiReading(post, phi)()
        if M.IdentityCompare(pre_reading, M.EmptyList)() is M.truth_value:
            discharged = M.false_value
        elif M.Compare(pre_reading, post_reading)() is M.truth_value:
            discharged = M.truth_value
        else:
            discharged = M.false_value
        if discharged is M.truth_value:
            self.result = M.Pair(L.PreservesLabel, M.Pair(rule, M.Pair(phi, M.EmptyList)))
        else:
            reason = M.Pair(pre_reading, M.Pair(post_reading, M.EmptyList))
            self.result = M.Pair(
                L.InvariantRefutedLabel,
                M.Pair(phi, M.Pair(rule, M.Pair(reason, M.EmptyList))),
            )
        super().__init__(inputs=M.Pair(rule, M.Pair(phi, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class IsPreserves(M.Edge):
    def __init__(self, term):
        atom_result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), L.PreservesLabel)() is M.truth_value:
                atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsInvariantRefuted(M.Edge):
    def __init__(self, term):
        atom_result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), L.InvariantRefutedLabel)() is M.truth_value:
                atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Invariant(M.Edge):
    def __init__(self, phi, ruleset, registry):
        self.phi = phi
        self.registry = registry
        self.result = self._walk(ruleset)
        super().__init__(inputs=M.Pair(phi, M.Pair(ruleset, M.Pair(registry, M.EmptyList))), results=self.result)

    def _walk(self, ruleset):
        if M.IdentityCompare(ruleset, M.EmptyList)() is M.truth_value:
            return M.Pair(L.InvariantLabel, M.Pair(self.phi, M.Pair(M.EmptyList, M.EmptyList)))
        rule = M.Head(ruleset)()
        rest = M.Tail(ruleset)()
        obligation = Preserves(rule, self.phi, self.registry)()
        if IsPreserves(obligation)() is M.false_value:
            return obligation
        rest_result = self._walk(rest)
        if IsInvariantRefuted(rest_result)() is M.truth_value:
            return rest_result
        return M.Pair(L.InvariantLabel, M.Pair(self.phi, M.Pair(ruleset, M.EmptyList)))

    def __call__(self):
        return self.result


class IsInvariant(M.Edge):
    def __init__(self, term):
        atom_result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), L.InvariantLabel)() is M.truth_value:
                atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Unreachable(M.Edge):
    def __init__(self, start, goal, invariant, witness):
        self.result = M.Pair(
            L.UnreachableLabel,
            M.Pair(start, M.Pair(goal, M.Pair(invariant, M.Pair(witness, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(start, M.Pair(goal, M.Pair(invariant, M.Pair(witness, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsUnreachable(M.Edge):
    def __init__(self, term):
        atom_result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), L.UnreachableLabel)() is M.truth_value:
                atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReachabilityPrune(M.Edge):
    def __init__(self, start, goal, invariant, phi, registry):
        atom_result = M.EmptyList
        if IsInvariant(invariant)() is M.truth_value:
            if PhiHolds(start, phi)() is M.truth_value:
                start_value = PhiReading(start, phi)()
                goal_value = PhiReading(goal, phi)()
                if M.IdentityCompare(start_value, goal_value)() is M.false_value:
                    witness = M.Pair(start_value, M.Pair(goal_value, M.EmptyList))
                    atom_result = Unreachable(start, goal, invariant, witness)()
        self.result = atom_result
        super().__init__(
            inputs=M.Pair(start, M.Pair(goal, M.Pair(invariant, M.Pair(phi, M.Pair(registry, M.EmptyList))))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DropMatchedFacts(M.Edge):
    def __init__(self, facts, matched):
        self.result = self._drop(facts, matched)
        super().__init__(inputs=M.Pair(facts, M.Pair(matched, M.EmptyList)), results=self.result)

    def _drop_one(self, facts, target, kept):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return kept
        fact = M.Head(facts)()
        rest = M.Tail(facts)()
        if M.Compare(fact, target)() is M.truth_value:
            acc = rest
            while M.IdentityCompare(kept, M.EmptyList)() is M.false_value:
                acc = M.Pair(M.Head(kept)(), acc)
                kept = M.Tail(kept)()
            return acc
        return self._drop_one(rest, target, M.Pair(fact, kept))

    def _drop(self, facts, matched):
        remaining = facts
        targets = matched
        while M.IdentityCompare(targets, M.EmptyList)() is M.false_value:
            remaining = self._drop_one(remaining, M.Head(targets)(), M.EmptyList)
            targets = M.Tail(targets)()
        return remaining

    def __call__(self):
        return self.result


class InstantiateFactList(M.Edge):
    def __init__(self, terms, bindings):
        self.bindings = bindings
        self.result = self._walk(terms)
        super().__init__(inputs=M.Pair(terms, M.Pair(bindings, M.EmptyList)), results=self.result)

    def _walk(self, terms):
        if M.IdentityCompare(terms, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        inst = M.Instantiate(M.Head(terms)(), self.bindings)()
        return M.Pair(M.Head(inst)(), self._walk(M.Tail(terms)()))

    def __call__(self):
        return self.result


class JoinPremises(M.Edge):
    def __init__(self, premises, facts, bindings):
        self.facts = facts
        self.result = self._join(premises, bindings)
        super().__init__(inputs=M.Pair(premises, M.Pair(facts, M.Pair(bindings, M.EmptyList))), results=self.result)

    def _join(self, premises, bindings):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.Pair(bindings, M.EmptyList)
        premise = M.Head(premises)()
        rest = M.Tail(premises)()
        acc = M.EmptyList
        remaining = self.facts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            fact = M.Head(remaining)()
            match = M.Match(premise, fact)()
            if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
                merged = M.MergeBindings(bindings, M.Tail(match)())()
                if M.IdentityCompare(M.Head(merged)(), M.truth_value)() is M.truth_value:
                    deeper = self._join(rest, M.Tail(merged)())
                    while M.IdentityCompare(deeper, M.EmptyList)() is M.false_value:
                        acc = M.Pair(M.Head(deeper)(), acc)
                        deeper = M.Tail(deeper)()
            remaining = M.Tail(remaining)()
        return acc

    def __call__(self):
        return self.result


class RewriteKnowledgeByRule(M.Edge):
    def __init__(self, state, rule):
        facts = StateFacts(state)()
        premises = P.RulePremises(rule)()
        replacement = ReplacementFacts(rule)()
        bindings_list = JoinPremises(premises, facts, M.EmptyList)()
        self.result = self._successors(facts, premises, replacement, bindings_list, rule)
        super().__init__(inputs=M.Pair(state, M.Pair(rule, M.EmptyList)), results=self.result)

    def _successors(self, facts, premises, replacement, bindings_list, rule):
        if M.IdentityCompare(bindings_list, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        bindings = M.Head(bindings_list)()
        consumed = InstantiateFactList(premises, bindings)()
        leftover = DropMatchedFacts(facts, consumed)()
        added = InstantiateFactList(replacement, bindings)()
        next_facts = leftover
        extra = added
        while M.IdentityCompare(extra, M.EmptyList)() is M.false_value:
            next_facts = M.Pair(M.Head(extra)(), next_facts)
            extra = M.Tail(extra)()
        nxt = P.Knowledge(next_facts)()
        action = P.TheoremAction(rule, bindings)()
        rest = self._successors(facts, premises, replacement, M.Tail(bindings_list)(), rule)
        return M.Pair(M.Pair(action, M.Pair(nxt, M.EmptyList)), rest)

    def __call__(self):
        return self.result


class FactsCover(M.Edge):
    def __init__(self, left, right):
        self.right = right
        self.result = self._cover(left)
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def _has(self, facts, target):
        remaining = facts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(remaining)(), target)() is M.truth_value:
                return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value

    def _cover(self, left):
        remaining = left
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if self._has(self.right, M.Head(remaining)()) is M.false_value:
                return M.false_value
            remaining = M.Tail(remaining)()
        return M.truth_value

    def __call__(self):
        return self.result


class SameBoard(M.Edge):
    def __init__(self, left, right):
        left_facts = StateFacts(left)()
        right_facts = StateFacts(right)()
        if FactsCover(left_facts, right_facts)() is M.truth_value:
            if FactsCover(right_facts, left_facts)() is M.truth_value:
                self.result = M.truth_value
            else:
                self.result = M.false_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class RewriteSearch(M.Edge):
    def __init__(self, start, goal, rules, registry):
        self.registry = registry
        self.goal = goal
        self.rules = rules
        self.result = self._dfs(start, M.EmptyList, M.Pair(start, M.EmptyList))
        super().__init__(
            inputs=M.Pair(start, M.Pair(goal, M.Pair(rules, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _seen(self, term, seen):
        remaining = seen
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if SameBoard(M.Head(remaining)(), term)() is M.truth_value:
                return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value

    def _try_moves(self, moves, plan, seen):
        remaining = moves
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            move = M.Head(remaining)()
            action = M.Head(move)()
            nxt = M.Head(M.Tail(move)())()
            if self._seen(nxt, seen) is M.false_value:
                found = self._dfs(nxt, M.Pair(action, plan), M.Pair(nxt, seen))
                if M.IdentityCompare(found, M.EmptyList)() is M.false_value:
                    return found
            remaining = M.Tail(remaining)()
        return M.EmptyList

    def _dfs(self, current, plan, seen):
        if M.Compare(current, self.goal)() is M.truth_value:
            acc = M.EmptyList
            remaining = plan
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                acc = M.Pair(M.Head(remaining)(), acc)
                remaining = M.Tail(remaining)()
            return acc
        rules = self.rules
        while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
            found = self._try_moves(RewriteKnowledgeByRule(current, M.Head(rules)())(), plan, seen)
            if M.IdentityCompare(found, M.EmptyList)() is M.false_value:
                return found
            rules = M.Tail(rules)()
        return M.EmptyList

    def __call__(self):
        return self.result


class SearchWithInvariant(M.Edge):
    def __init__(self, graph, start, goal, rules, heuristic, registry, phi):
        invariant = Invariant(phi, rules, registry)()
        prune = ReachabilityPrune(start, goal, invariant, phi, registry)()
        if IsUnreachable(prune)() is M.truth_value:
            cost_pair = S.BuildSearchCost(
                M.EmptyList,
                M.Zero,
                M.Zero,
                M.Zero,
                S.SearchFailureLabel,
                registry,
            )()
            search_cost = M.Head(cost_pair)()
            self.result = M.Pair(M.EmptyList, M.Pair(search_cost, M.Pair(prune, M.EmptyList)))
        else:
            plan = RewriteSearch(start, goal, rules, registry)()
            outcome = S.SearchFailureLabel
            if M.IdentityCompare(plan, M.EmptyList)() is M.false_value:
                outcome = S.SearchSuccessLabel
            cost_pair = S.BuildSearchCost(
                plan,
                M.Zero,
                M.Zero,
                M.Zero,
                outcome,
                registry,
            )()
            search_cost = M.Head(cost_pair)()
            self.result = M.Pair(plan, M.Pair(search_cost, M.Pair(M.EmptyList, M.EmptyList)))
        super().__init__(
            inputs=M.Pair(
                graph,
                M.Pair(start, M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.Pair(registry, M.Pair(phi, M.EmptyList)))))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InvariantCandidate(M.Edge):
    def __init__(self, phi, ruleset):
        self.result = M.Pair(L.InvariantCandidateLabel, M.Pair(phi, M.Pair(ruleset, M.EmptyList)))
        super().__init__(inputs=M.Pair(phi, M.Pair(ruleset, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
