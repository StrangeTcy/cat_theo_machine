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


class IsSequenceTerm(M.Edge):
    def __init__(self, term, registry):
        atom_result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), L.SequenceLabel)() is M.truth_value:
                atom_result = M.truth_value
        if atom_result is M.false_value:
            constructor = M.GetConstructor(term, registry)()
            if M.IdentityCompare(constructor, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(M.Head(constructor)(), L.SequenceLabel)() is M.truth_value:
                    atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(term, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SequenceTermArgs(M.Edge):
    def __init__(self, term, registry):
        args = M.EmptyList
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), L.SequenceLabel)() is M.truth_value:
                args = M.Tail(term)()
        if M.IdentityCompare(args, M.EmptyList)() is M.truth_value:
            constructor = M.GetConstructor(term, registry)()
            if M.IdentityCompare(constructor, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(M.Head(constructor)(), L.SequenceLabel)() is M.truth_value:
                    args = M.Tail(constructor)()
        self.result = args
        super().__init__(inputs=M.Pair(term, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CollectSequenceFacts(M.Edge):
    def __init__(self, facts, registry):
        self.registry = registry
        acc = M.EmptyList
        remaining = facts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            fact = M.Head(remaining)()
            if IsSequenceTerm(fact, registry)() is M.truth_value:
                acc = M.Pair(fact, acc)
            remaining = M.Tail(remaining)()
        rev = M.EmptyList
        while M.IdentityCompare(acc, M.EmptyList)() is M.false_value:
            rev = M.Pair(M.Head(acc)(), rev)
            acc = M.Tail(acc)()
        self.result = rev
        super().__init__(inputs=M.Pair(facts, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SequenceIndex(M.Edge):
    def __init__(self, seq, registry):
        args = SequenceTermArgs(seq, registry)()
        pattern = M.Head(M.Tail(M.Tail(args)())())()
        index = M.EmptyList
        if M.IsPair(pattern)() is M.truth_value:
            if M.IdentityCompare(M.Head(pattern)(), L.ApplyLabel)() is M.truth_value:
                apply_args = M.Tail(pattern)()
                if M.IsPair(M.Tail(apply_args)())() is M.truth_value:
                    step = M.Head(M.Tail(apply_args)())()
                    if M.IsPair(step)() is M.truth_value:
                        if M.IdentityCompare(M.Head(step)(), L.SuccLabel)() is M.truth_value:
                            index = M.Head(M.Tail(step)())()
                        else:
                            index = step
        self.result = index
        super().__init__(inputs=M.Pair(seq, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TransformLimit(M.Edge):
    def __init__(self, seq, limit_value, registry):
        limit_pair = M.Limit(seq, limit_value, registry)()
        self.result = M.Head(limit_pair)()
        super().__init__(
            inputs=M.Pair(seq, M.Pair(limit_value, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ApplyLimit(M.Edge):
    def __init__(self, seq, limit_value, registry):
        limit_term = TransformLimit(seq, limit_value, registry)()
        self.result = M.Pair(L.ApplyLabel, M.Pair(limit_term, M.EmptyList))
        super().__init__(
            inputs=M.Pair(seq, M.Pair(limit_value, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TransformLimitUnknown(M.Edge):
    def __init__(self):
        name = M.Thingy()
        self.result = M.Pair(M.VarTag, M.Pair(name, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SequenceNames(M.Edge):
    def __init__(self, sequences, registry):
        names = M.EmptyList
        remaining = sequences
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            seq = M.Head(remaining)()
            name = M.Head(SequenceTermArgs(seq, registry)())()
            names = M.Pair(name, names)
            remaining = M.Tail(remaining)()
        self.result = names
        super().__init__(inputs=M.Pair(sequences, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class NameAmong(M.Edge):
    def __init__(self, name, names):
        atom_result = M.false_value
        remaining = names
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.Head(remaining)(), name)() is M.truth_value:
                atom_result = M.truth_value
            remaining = M.Tail(remaining)()
        self.result = atom_result
        super().__init__(inputs=M.Pair(name, M.Pair(names, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SequenceNextTerm(M.Edge):
    def __init__(self, seq, registry):
        args = SequenceTermArgs(seq, registry)()
        nxt = M.EmptyList
        if M.IdentityCompare(args, M.EmptyList)() is M.false_value:
            rest = M.Tail(args)()
            if M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
                rest = M.Tail(rest)()
                if M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
                    rest = M.Tail(rest)()
                    if M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
                        nxt = M.Head(rest)()
        self.result = nxt
        super().__init__(inputs=M.Pair(seq, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ProductOfTerms(M.Edge):
    def __init__(self, terms):
        product = M.EmptyList
        remaining = terms
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            term = M.Head(remaining)()
            if M.IdentityCompare(product, M.EmptyList)() is M.truth_value:
                product = term
            else:
                product = M.Pair(L.ExprMulLabel, M.Pair(product, M.Pair(term, M.EmptyList)))
            remaining = M.Tail(remaining)()
        self.result = product
        super().__init__(inputs=M.Pair(terms, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProductOfCurrentTerms(M.Edge):
    def __init__(self, sequences, registry):
        terms = M.EmptyList
        remaining = sequences
        acc = M.EmptyList
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            seq = M.Head(remaining)()
            args = SequenceTermArgs(seq, registry)()
            name = M.Head(args)()
            index = SequenceIndex(seq, registry)()
            term = M.Pair(L.ApplyLabel, M.Pair(name, M.Pair(index, M.EmptyList)))
            acc = M.Pair(term, acc)
            remaining = M.Tail(remaining)()
        rev = M.EmptyList
        while M.IdentityCompare(acc, M.EmptyList)() is M.false_value:
            rev = M.Pair(M.Head(acc)(), rev)
            acc = M.Tail(acc)()
        self.result = ProductOfTerms(rev)()
        super().__init__(inputs=M.Pair(sequences, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ProductOfNextTerms(M.Edge):
    def __init__(self, sequences, registry):
        acc = M.EmptyList
        remaining = sequences
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            nxt = SequenceNextTerm(M.Head(remaining)(), registry)()
            if M.IdentityCompare(nxt, M.EmptyList)() is M.false_value:
                acc = M.Pair(nxt, acc)
            remaining = M.Tail(remaining)()
        rev = M.EmptyList
        while M.IdentityCompare(acc, M.EmptyList)() is M.false_value:
            rev = M.Pair(M.Head(acc)(), rev)
            acc = M.Tail(acc)()
        self.result = ProductOfTerms(rev)()
        super().__init__(inputs=M.Pair(sequences, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class AppendFactors(M.Edge):
    def __init__(self, left, right):
        acc = right
        remaining = left
        rev = M.EmptyList
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            rev = M.Pair(M.Head(remaining)(), rev)
            remaining = M.Tail(remaining)()
        while M.IdentityCompare(rev, M.EmptyList)() is M.false_value:
            acc = M.Pair(M.Head(rev)(), acc)
            rev = M.Tail(rev)()
        self.result = acc
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TermSeen(M.Edge):
    def __init__(self, term, seen):
        atom_result = M.false_value
        remaining = seen
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(remaining)(), term)() is M.truth_value:
                atom_result = M.truth_value
            remaining = M.Tail(remaining)()
        self.result = atom_result
        super().__init__(inputs=M.Pair(term, M.Pair(seen, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ReverseTermPath(M.Edge):
    def __init__(self, path):
        acc = M.EmptyList
        remaining = path
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            acc = M.Pair(M.Head(remaining)(), acc)
            remaining = M.Tail(remaining)()
        self.result = acc
        super().__init__(inputs=M.Pair(path, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LogTermPath(M.Edge):
    def __init__(self, tag, path, registry):
        remaining = ReverseTermPath(path)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            P._debug(tag + M.PrettyTerm(M.Head(remaining)(), registry)())
            remaining = M.Tail(remaining)()
        self.result = M.truth_value
        super().__init__(inputs=M.Pair(tag, M.Pair(path, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class AlgebraRewriteRule(M.Edge):
    def __init__(self, rule):
        atom_result = M.false_value
        if P.RuleIsUnary(rule)() is M.truth_value:
            pattern = P.RulePattern(rule)()
            if M.IsPair(pattern)() is M.truth_value:
                head = M.Head(pattern)()
                if M.IdentityCompare(head, L.ExprFracLabel)() is M.truth_value:
                    atom_result = M.truth_value
                if M.IdentityCompare(head, L.ExprNegLabel)() is M.truth_value:
                    atom_result = M.truth_value
                if M.IdentityCompare(head, L.ExprLtLabel)() is M.truth_value:
                    atom_result = M.truth_value
                if M.IdentityCompare(head, L.ExprMulLabel)() is M.truth_value:
                    args = M.Tail(pattern)()
                    left = M.Head(args)()
                    right = M.Head(M.Tail(args)())()
                    if M.IdentityCompare(left, M.two)() is M.false_value:
                        if P.IsVarPattern(left)() is M.false_value:
                            atom_result = M.truth_value
                        else:
                            if P.IsVarPattern(right)() is M.false_value:
                                if M.IsPair(right)() is M.truth_value:
                                    inner = M.Head(right)()
                                    if M.IdentityCompare(inner, L.ExprAddLabel)() is M.false_value:
                                        if M.IdentityCompare(inner, L.ExprMulLabel)() is M.false_value:
                                            atom_result = M.truth_value
                                        else:
                                            inner_args = M.Tail(right)()
                                            if P.IsVarPattern(M.Head(inner_args)())() is M.false_value:
                                                atom_result = M.truth_value
                                else:
                                    atom_result = M.truth_value
                if M.IdentityCompare(head, L.ExprAddLabel)() is M.truth_value:
                    args = M.Tail(pattern)()
                    left = M.Head(args)()
                    if P.IsVarPattern(left)() is M.false_value:
                        atom_result = M.truth_value
                    else:
                        right = M.Head(M.Tail(args)())()
                        if P.IsVarPattern(right)() is M.false_value:
                            atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RewriteEquals(M.Edge):
    def __init__(self, start, goal, rules, registry):
        self.goal = goal
        self.registry = registry
        kept = M.EmptyList
        remaining = rules
        want_lt = M.false_value
        if M.IsPair(start)() is M.truth_value:
            if M.IdentityCompare(M.Head(start)(), L.ExprLtLabel)() is M.truth_value:
                want_lt = M.truth_value
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            rule = M.Head(remaining)()
            if AlgebraRewriteRule(rule)() is M.truth_value:
                if want_lt is M.truth_value:
                    pattern = P.RulePattern(rule)()
                    if M.IsPair(pattern)() is M.truth_value:
                        ph = M.Head(pattern)()
                        if M.IdentityCompare(ph, L.ExprLtLabel)() is M.truth_value:
                            kept = M.Pair(rule, kept)
                        if M.IdentityCompare(ph, L.ExprMulLabel)() is M.truth_value:
                            args = M.Tail(pattern)()
                            left = M.Head(args)()
                            right = M.Head(M.Tail(args)())()
                            if M.IdentityCompare(right, M.two)() is M.truth_value:
                                kept = M.Pair(rule, kept)
                            if M.IsPair(right)() is M.truth_value:
                                if M.IdentityCompare(M.Head(right)(), L.ExprMulLabel)() is M.truth_value:
                                    if M.IdentityCompare(M.Head(M.Tail(right)())(), M.two)() is M.truth_value:
                                        kept = M.Pair(rule, kept)
                else:
                    kept = M.Pair(rule, kept)
            remaining = M.Tail(remaining)()
        self.rules = kept
        self.result = self._walk(start, M.Pair(start, M.EmptyList), M.nine)
        super().__init__(
            inputs=M.Pair(start, M.Pair(goal, M.Pair(rules, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _walk(self, current, path, fuel):
        if M.Compare(current, self.goal)() is M.truth_value:
            LogTermPath("identity: ", path, self.registry)()
            return M.truth_value
        if M.IdentityCompare(fuel, M.Zero)() is M.truth_value:
            P._debug("identity-stuck: " + M.PrettyTerm(current, self.registry)())
            return M.false_value
        nxt = current
        rules = self.rules
        while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
            here = P.RewriteHere(M.Head(rules)(), current)()
            if M.Compare(here, current)() is M.false_value:
                nxt = here
                rules = M.EmptyList
            else:
                rules = M.Tail(rules)()
        if M.Compare(nxt, current)() is M.truth_value:
            rules = self.rules
            while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
                deep = M.Head(M.Rewrite(M.Head(rules)(), current, self.registry)())()
                if M.Compare(deep, current)() is M.false_value:
                    nxt = deep
                    rules = M.EmptyList
                else:
                    rules = M.Tail(rules)()
        if M.Compare(nxt, current)() is M.truth_value:
            P._debug("identity-stuck: " + M.PrettyTerm(current, self.registry)())
            return M.false_value
        P._debug("identity: " + M.PrettyTerm(nxt, self.registry)())
        pred = M.NatPred(fuel, self.registry)()
        return self._walk(nxt, M.Pair(nxt, path), M.Head(pred)())

    def __call__(self):
        return self.result


class EquationRewriteEquals(M.Edge):
    def __init__(self, start, goal, rules, registry):
        self.goal = goal
        self.registry = registry
        self.rules = rules
        self.result = self._search(M.Pair(start, M.EmptyList), M.Pair(start, M.EmptyList), M.eight)
        super().__init__(
            inputs=M.Pair(start, M.Pair(goal, M.Pair(rules, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _search(self, frontier, seen, fuel):
        if M.IdentityCompare(fuel, M.Zero)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.false_value
        current = M.Head(frontier)()
        rest = M.Tail(frontier)()
        if M.Compare(current, self.goal)() is M.truth_value:
            P._debug("equation-rewrite: reached " + M.PrettyTerm(current, self.registry)())
            return M.truth_value
        nxt_frontier = rest
        nxt_seen = seen
        rules = self.rules
        while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
            rule = M.Head(rules)()
            rewritten = M.Head(M.Rewrite(rule, current, self.registry)())()
            if M.Compare(rewritten, current)() is M.false_value:
                if TermSeen(rewritten, nxt_seen)() is M.false_value:
                    P._debug(
                        "equation-rewrite: "
                        + M.PrettyTerm(current, self.registry)()
                        + " -> "
                        + M.PrettyTerm(rewritten, self.registry)()
                    )
                    nxt_frontier = M.Pair(rewritten, nxt_frontier)
                    nxt_seen = M.Pair(rewritten, nxt_seen)
            rules = M.Tail(rules)()
        pred = M.NatPred(fuel, self.registry)()
        less = M.Head(pred)()
        return self._search(nxt_frontier, nxt_seen, less)

    def __call__(self):
        return self.result


class SequenceBases(M.Edge):
    def __init__(self, sequences, registry):
        acc = M.EmptyList
        remaining = sequences
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            args = SequenceTermArgs(M.Head(remaining)(), registry)()
            base = M.Head(M.Tail(args)())()
            acc = M.Pair(base, acc)
            remaining = M.Tail(remaining)()
        rev = M.EmptyList
        while M.IdentityCompare(acc, M.EmptyList)() is M.false_value:
            rev = M.Pair(M.Head(acc)(), rev)
            acc = M.Tail(acc)()
        self.result = rev
        super().__init__(inputs=M.Pair(sequences, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BaseAmong(M.Edge):
    def __init__(self, term, bases):
        atom_result = M.false_value
        remaining = bases
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(remaining)(), term)() is M.truth_value:
                atom_result = M.truth_value
            remaining = M.Tail(remaining)()
        self.result = atom_result
        super().__init__(inputs=M.Pair(term, M.Pair(bases, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class OrderPremisesHold(M.Edge):
    def __init__(self, facts, sequences, registry):
        bases = SequenceBases(sequences, registry)()
        zero_lt_base = M.false_value
        base_lt_base = M.false_value
        self.witnesses = M.EmptyList
        remaining = facts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            fact = M.Head(remaining)()
            if M.IsPair(fact)() is M.truth_value:
                if M.IdentityCompare(M.Head(fact)(), L.ExprLtLabel)() is M.truth_value:
                    args = M.Tail(fact)()
                    if M.IsPair(args)() is M.truth_value:
                        left = M.Head(args)()
                        rest = M.Tail(args)()
                        if M.IsPair(rest)() is M.truth_value:
                            right = M.Head(rest)()
                            if M.Compare(left, M.Zero)() is M.truth_value:
                                if BaseAmong(right, bases)() is M.truth_value:
                                    zero_lt_base = M.truth_value
                                    self.witnesses = M.Pair(fact, self.witnesses)
                            if BaseAmong(left, bases)() is M.truth_value:
                                if BaseAmong(right, bases)() is M.truth_value:
                                    base_lt_base = M.truth_value
                                    self.witnesses = M.Pair(fact, self.witnesses)
            remaining = M.Tail(remaining)()
        if zero_lt_base is M.truth_value:
            if base_lt_base is M.truth_value:
                self.result = M.truth_value
            else:
                self.result = M.false_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(facts, M.Pair(sequences, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class LogOrderFacts(M.Edge):
    def __init__(self, facts, sequences, registry):
        held = OrderPremisesHold(facts, sequences, registry)
        remaining = held.witnesses
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            P._debug("order: " + M.PrettyTerm(M.Head(remaining)(), registry)())
            remaining = M.Tail(remaining)()
        self.result = held()
        super().__init__(inputs=M.Pair(facts, M.Pair(sequences, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class SubstituteApplies(M.Edge):
    def __init__(self, term, names, unknown):
        self.names = names
        self.unknown = unknown
        self.result = self._walk(term)
        super().__init__(inputs=M.Pair(term, M.Pair(names, M.Pair(unknown, M.EmptyList))), results=self.result)

    def _walk(self, term):
        if M.IsPair(term)() is M.false_value:
            return term
        if M.IdentityCompare(M.Head(term)(), L.ApplyLabel)() is M.truth_value:
            args = M.Tail(term)()
            if M.IsPair(args)() is M.truth_value:
                if NameAmong(M.Head(args)(), self.names)() is M.truth_value:
                    return self.unknown
        return M.Pair(self._walk(M.Head(term)()), self._walk(M.Tail(term)()))

    def __call__(self):
        return self.result


class TermContains(M.Edge):
    def __init__(self, term, needle):
        self.needle = needle
        self.result = self._walk(term)
        super().__init__(inputs=M.Pair(term, M.Pair(needle, M.EmptyList)), results=self.result)

    def _walk(self, term):
        if M.IdentityCompare(term, self.needle)() is M.truth_value:
            return M.truth_value
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if self._walk(M.Head(term)()) is M.truth_value:
            return M.truth_value
        return self._walk(M.Tail(term)())

    def __call__(self):
        return self.result


class SolveFor(M.Edge):
    def __init__(self, expr, value, unknown):
        self.unknown = unknown
        self.result = self._solve(expr, value)
        super().__init__(inputs=M.Pair(expr, M.Pair(value, M.Pair(unknown, M.EmptyList))), results=self.result)

    def _solve(self, expr, value):
        if M.IdentityCompare(expr, self.unknown)() is M.truth_value:
            if TermContains(value, self.unknown)() is M.false_value:
                return value
            return M.EmptyList
        if M.IdentityCompare(value, self.unknown)() is M.truth_value:
            return self._solve(value, expr)
        if M.IsPair(expr)() is M.false_value:
            return M.EmptyList
        head = M.Head(expr)()
        args = M.Tail(expr)()
        if M.IsPair(args)() is M.false_value:
            return M.EmptyList
        left = M.Head(args)()
        rest = M.Tail(args)()
        if M.IdentityCompare(head, L.SqrtLabel)() is M.truth_value:
            squared = M.Pair(L.ExprMulLabel, M.Pair(value, M.Pair(value, M.EmptyList)))
            return self._solve(left, squared)
        if M.IsPair(rest)() is M.false_value:
            return M.EmptyList
        right = M.Head(rest)()
        left_has = TermContains(left, self.unknown)()
        right_has = TermContains(right, self.unknown)()
        if M.IdentityCompare(head, L.ExprMulLabel)() is M.truth_value:
            if left_has is M.truth_value:
                if right_has is M.truth_value:
                    return M.EmptyList
                quotient = M.Pair(L.ExprFracLabel, M.Pair(value, M.Pair(right, M.EmptyList)))
                return self._solve(left, quotient)
            if right_has is M.truth_value:
                quotient = M.Pair(L.ExprFracLabel, M.Pair(value, M.Pair(left, M.EmptyList)))
                return self._solve(right, quotient)
            return M.EmptyList
        if M.IdentityCompare(head, L.ExprAddLabel)() is M.truth_value:
            if left_has is M.truth_value:
                if right_has is M.false_value:
                    neg = M.Pair(L.ExprNegLabel, M.Pair(right, M.EmptyList))
                    shifted = M.Pair(L.ExprAddLabel, M.Pair(value, M.Pair(neg, M.EmptyList)))
                    return self._solve(left, shifted)
            if right_has is M.truth_value:
                if left_has is M.false_value:
                    neg = M.Pair(L.ExprNegLabel, M.Pair(left, M.EmptyList))
                    shifted = M.Pair(L.ExprAddLabel, M.Pair(value, M.Pair(neg, M.EmptyList)))
                    return self._solve(right, shifted)
            return M.EmptyList
        if M.IdentityCompare(head, L.ExprFracLabel)() is M.truth_value:
            if left_has is M.truth_value:
                if right_has is M.false_value:
                    scaled = M.Pair(L.ExprMulLabel, M.Pair(value, M.Pair(right, M.EmptyList)))
                    return self._solve(left, scaled)
            if right_has is M.truth_value:
                if left_has is M.false_value:
                    if TermContains(value, self.unknown)() is M.false_value:
                        inv = M.Pair(L.ExprFracLabel, M.Pair(left, M.Pair(value, M.EmptyList)))
                        return self._solve(right, inv)
            return M.EmptyList
        return M.EmptyList

    def __call__(self):
        return self.result


class CurrentApply(M.Edge):
    def __init__(self, seq, registry):
        args = SequenceTermArgs(seq, registry)()
        name = M.Head(args)()
        index = SequenceIndex(seq, registry)()
        self.result = M.Pair(L.ApplyLabel, M.Pair(name, M.Pair(index, M.EmptyList)))
        super().__init__(inputs=M.Pair(seq, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SequenceStepApply(M.Edge):
    def __init__(self, seq, registry):
        args = SequenceTermArgs(seq, registry)()
        self.result = M.EmptyList
        if M.IdentityCompare(args, M.EmptyList)() is M.false_value:
            rest = M.Tail(args)()
            if M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
                rest = M.Tail(rest)()
                if M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
                    self.result = M.Head(rest)()
        super().__init__(inputs=M.Pair(seq, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SequenceNameOf(M.Edge):
    def __init__(self, seq, registry):
        args = SequenceTermArgs(seq, registry)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(seq, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TermGap(M.Edge):
    def __init__(self, left, right):
        neg = M.Pair(L.ExprNegLabel, M.Pair(right, M.EmptyList))
        self.result = M.Pair(L.ExprAddLabel, M.Pair(left, M.Pair(neg, M.EmptyList)))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ConclusionHeadAdmitted(M.Edge):
    def __init__(self, head):
        atom_result = M.false_value
        if M.IdentityCompare(head, L.ExprLtLabel)() is M.truth_value:
            atom_result = M.truth_value
        if M.IdentityCompare(head, L.GapContractsLabel)() is M.truth_value:
            atom_result = M.truth_value
        if M.IdentityCompare(head, L.DecreasingLabel)() is M.truth_value:
            atom_result = M.truth_value
        if M.IdentityCompare(head, L.IncreasingLabel)() is M.truth_value:
            atom_result = M.truth_value
        if M.IdentityCompare(head, L.BoundedBelowLabel)() is M.truth_value:
            atom_result = M.truth_value
        if M.IdentityCompare(head, L.BoundedAboveLabel)() is M.truth_value:
            atom_result = M.truth_value
        if M.IdentityCompare(head, L.ConvergesLabel)() is M.truth_value:
            atom_result = M.truth_value
        if M.IdentityCompare(head, L.ExprEqLabel)() is M.truth_value:
            atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(head, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ApplySequenceTheorems(M.Edge):
    def __init__(self, facts, rules, registry):
        self.registry = registry
        self.rules = rules
        self.result = self._saturate(facts, M.nine)

    def _has(self, facts, target):
        remaining = facts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(remaining)(), target)() is M.truth_value:
                return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value

    def _saturate(self, facts, fuel):
        if M.IdentityCompare(fuel, M.Zero)() is M.truth_value:
            return facts
        added = M.false_value
        acc = facts
        rules = self.rules
        while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
            rule = M.Head(rules)()
            if P.RuleIsUnary(rule)() is M.false_value:
                replacement = P.RuleReplacement(rule)()
                if M.IsPair(replacement)() is M.truth_value:
                    if ConclusionHeadAdmitted(M.Head(replacement)())() is M.truth_value:
                        hits = JoinPremises(P.RulePremises(rule)(), acc, M.EmptyList)()
                        if M.IdentityCompare(hits, M.EmptyList)() is M.false_value:
                            bindings = M.Head(hits)()
                            inst = M.Instantiate(replacement, bindings)()
                            conclusion = M.Head(inst)()
                            if self._has(acc, conclusion) is M.false_value:
                                action = P.TheoremAction(rule, bindings)()
                                P._debug("apply " + P.PrettyAction(action, self.registry)())
                                P._debug("apply conclusion: " + M.PrettyTerm(conclusion, self.registry)())
                                acc = M.Pair(conclusion, acc)
                                added = M.truth_value
            rules = M.Tail(rules)()
        if added is M.truth_value:
            pred = M.NatPred(fuel, self.registry)()
            return self._saturate(acc, M.Head(pred)())
        return acc

    def __call__(self):
        return self.result


class FindLimit(M.Edge):
    def __init__(self, sequences, product, registry, rewrite_rules, facts):
        self.result = M.EmptyList
        if M.IdentityCompare(sequences, M.EmptyList)() is M.false_value:
            first = M.Head(sequences)()
            rest = M.Tail(sequences)()
            if M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
                second = M.Head(rest)()
                x_name = SequenceNameOf(first, registry)()
                y_name = SequenceNameOf(second, registry)()
                x = CurrentApply(first, registry)()
                y = CurrentApply(second, registry)()
                nx = SequenceNextTerm(first, registry)()
                ny = SequenceNextTerm(second, registry)()
                current_gap = TermGap(x, y)()
                next_gap = TermGap(nx, ny)()
                sum_xy = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
                closed_num = M.Pair(L.ExprMulLabel, M.Pair(current_gap, M.Pair(current_gap, M.EmptyList)))
                closed_den = M.Pair(L.ExprMulLabel, M.Pair(M.two, M.Pair(sum_xy, M.EmptyList)))
                closed_gap = M.Pair(L.ExprFracLabel, M.Pair(closed_num, M.Pair(closed_den, M.EmptyList)))
                P._debug("chain-same-limit: current gap " + M.PrettyTerm(current_gap, registry)())
                P._debug("chain-same-limit: next gap " + M.PrettyTerm(next_gap, registry)())
                P._debug("chain-same-limit: exact gap " + M.PrettyTerm(closed_gap, registry)())
                seed = M.EmptyList
                if RewriteEquals(next_gap, closed_gap, rewrite_rules, registry)() is M.false_value:
                    P._debug("chain-same-limit: next-gap did not rewrite to exact gap")
                else:
                    gap_eq = M.Pair(L.ExprEqLabel, M.Pair(next_gap, M.Pair(closed_gap, M.EmptyList)))
                    P._debug("chain-same-limit: " + M.PrettyTerm(gap_eq, registry)())
                    half_gap = M.Pair(L.ExprFracLabel, M.Pair(current_gap, M.Pair(M.two, M.EmptyList)))
                    closed_lt_half = M.Pair(L.ExprLtLabel, M.Pair(closed_gap, M.Pair(half_gap, M.EmptyList)))
                    y_pos = M.Pair(L.ExprLtLabel, M.Pair(M.Zero, M.Pair(y, M.EmptyList)))
                    P._debug("chain-same-limit: rewrite " + M.PrettyTerm(closed_lt_half, registry)())
                    if RewriteEquals(closed_lt_half, y_pos, rewrite_rules, registry)() is M.false_value:
                        P._debug("chain-same-limit: closed < half did not rewrite to 0 < Y")
                        seed = M.EmptyList
                    else:
                        seed = M.Pair(closed_lt_half, M.Pair(gap_eq, facts))
                if M.IdentityCompare(seed, M.EmptyList)() is M.false_value:
                    derived = ApplySequenceTheorems(seed, rewrite_rules, registry)()
                    half = M.Pair(L.ExprFracLabel, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
                    contracts = M.Pair(L.GapContractsLabel, M.Pair(x_name, M.Pair(y_name, M.Pair(half, M.EmptyList))))
                    dec_x = M.Pair(L.DecreasingLabel, M.Pair(x_name, M.EmptyList))
                    inc_y = M.Pair(L.IncreasingLabel, M.Pair(y_name, M.EmptyList))
                    below_x = M.Pair(L.BoundedBelowLabel, M.Pair(x_name, M.Pair(y, M.EmptyList)))
                    above_y = M.Pair(L.BoundedAboveLabel, M.Pair(y_name, M.Pair(x, M.EmptyList)))
                    lx = M.Pair(L.LimitValueLabel, M.Pair(x_name, M.EmptyList))
                    ly = M.Pair(L.LimitValueLabel, M.Pair(y_name, M.EmptyList))
                    conv_x = M.Pair(L.ConvergesLabel, M.Pair(x_name, M.Pair(lx, M.EmptyList)))
                    conv_y = M.Pair(L.ConvergesLabel, M.Pair(y_name, M.Pair(ly, M.EmptyList)))
                    common = M.Pair(L.ExprEqLabel, M.Pair(lx, M.Pair(ly, M.EmptyList)))
                    needed = M.Pair(
                        contracts,
                        M.Pair(
                            dec_x,
                            M.Pair(
                                inc_y,
                                M.Pair(
                                    below_x,
                                    M.Pair(
                                        above_y,
                                        M.Pair(conv_x, M.Pair(conv_y, M.Pair(common, M.EmptyList))),
                                    ),
                                ),
                            ),
                        ),
                    )
                    if FactsCover(needed, derived)() is M.truth_value:
                        self.result = common
                    else:
                        P._debug("chain-same-limit: theorems did not discharge mono, bounds, Converges, GapContracts, Lx=Ly")
        super().__init__(
            inputs=M.Pair(sequences, M.Pair(product, M.Pair(registry, M.Pair(rewrite_rules, M.Pair(facts, M.EmptyList))))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ProductOfBases(M.Edge):
    def __init__(self, sequences, registry):
        self.registry = registry
        product = M.EmptyList
        remaining = sequences
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            seq = M.Head(remaining)()
            base = M.Head(M.Tail(SequenceTermArgs(seq, registry)())())()
            if M.IdentityCompare(product, M.EmptyList)() is M.truth_value:
                product = base
            else:
                product = M.Pair(L.ExprMulLabel, M.Pair(product, M.Pair(base, M.EmptyList)))
            remaining = M.Tail(remaining)()
        self.result = product
        super().__init__(inputs=M.Pair(sequences, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PhiFromProduct(M.Edge):
    def __init__(self, phi, product):
        pattern = PhiPattern(phi)()
        hit = M.Match(pattern, M.Pair(M.Head(pattern)(), M.Pair(product, M.EmptyList)))()
        if M.IdentityCompare(M.Head(hit)(), M.truth_value)() is M.truth_value:
            inst = M.Instantiate(pattern, M.Tail(hit)())()
            self.result = M.Head(inst)()
        else:
            self.result = M.Pair(M.Head(pattern)(), M.Pair(product, M.EmptyList))
        super().__init__(inputs=M.Pair(phi, M.Pair(product, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ExamineTransforms(M.Edge):
    def __init__(self, start, phi, registry, rewrite_rules):
        self.registry = registry
        self.phi = phi
        self.start = start
        self.rewrite_rules = rewrite_rules
        facts = StateFacts(start)()
        sequences = CollectSequenceFacts(facts, registry)()
        self.result = self._examine(sequences)
        super().__init__(inputs=M.Pair(start, M.Pair(phi, M.Pair(registry, M.Pair(rewrite_rules, M.EmptyList)))), results=self.result)

    def _examine(self, sequences):
        if M.IdentityCompare(sequences, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        facts = StateFacts(self.start)()
        if LogOrderFacts(facts, sequences, self.registry)() is M.false_value:
            P._debug("order: start does not give 0 < smaller base and smaller base < larger base")
            return M.EmptyList
        current = ProductOfCurrentTerms(sequences, self.registry)()
        nxt = ProductOfNextTerms(sequences, self.registry)()
        P._debug("chain-product: current " + M.PrettyTerm(current, self.registry)())
        P._debug("chain-product: next " + M.PrettyTerm(nxt, self.registry)())
        if RewriteEquals(nxt, current, self.rewrite_rules, self.registry)() is M.false_value:
            P._debug("chain-product: next did not rewrite to current")
            return M.EmptyList
        product = ProductOfBases(sequences, self.registry)()
        current_eq = M.Pair(L.ExprEqLabel, M.Pair(current, M.Pair(product, M.EmptyList)))
        P._debug("chain-product: " + M.PrettyTerm(current_eq, self.registry)())
        limit_value = FindLimit(sequences, product, self.registry, self.rewrite_rules, facts)()
        if M.IdentityCompare(limit_value, M.EmptyList)() is M.truth_value:
            P._debug("limit: sequences did not yield a common LimitValue")
            return M.EmptyList
        return self._check_invariant(sequences, product, limit_value)

    def _check_invariant(self, sequences, product, applied):
        reading = PhiFromProduct(self.phi, product)()
        if M.IdentityCompare(reading, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(
            L.PreservesLabel,
            M.Pair(sequences, M.Pair(self.phi, M.Pair(reading, M.Pair(applied, M.EmptyList)))),
        )

    def __call__(self):
        return self.result


class ReplaceTerm(M.Edge):
    def __init__(self, term, old, new):
        self.old = old
        self.new = new
        self.result = self._walk(term)
        super().__init__(inputs=M.Pair(term, M.Pair(old, M.Pair(new, M.EmptyList))), results=self.result)

    def _walk(self, term):
        if M.Compare(term, self.old)() is M.truth_value:
            return self.new
        if M.IsPair(term)() is M.false_value:
            return term
        return M.Pair(self._walk(M.Head(term)()), self._walk(M.Tail(term)()))

    def __call__(self):
        return self.result


class CombineMeetAndProduct(M.Edge):
    def __init__(self, sequences, product, common, registry):
        self.result = M.EmptyList
        if M.IdentityCompare(sequences, M.EmptyList)() is M.false_value:
            first = M.Head(sequences)()
            rest = M.Tail(sequences)()
            if M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
                x_name = SequenceNameOf(first, registry)()
                y_name = SequenceNameOf(M.Head(rest)(), registry)()
                lx = M.Pair(L.LimitValueLabel, M.Pair(x_name, M.EmptyList))
                ly = M.Pair(L.LimitValueLabel, M.Pair(y_name, M.EmptyList))
                if M.IsPair(common)() is M.truth_value:
                    if M.IdentityCompare(M.Head(common)(), L.ExprEqLabel)() is M.truth_value:
                        limit_product = M.Pair(L.ExprMulLabel, M.Pair(lx, M.Pair(ly, M.EmptyList)))
                        square = M.Pair(L.ExprMulLabel, M.Pair(lx, M.Pair(lx, M.EmptyList)))
                        after = ReplaceTerm(limit_product, ly, lx)()
                        P._debug("union: Limit(X*Y) is " + M.PrettyTerm(after, registry)())
                        square_eq = M.Pair(L.ExprEqLabel, M.Pair(square, M.Pair(product, M.EmptyList)))
                        P._debug("union: " + M.PrettyTerm(square_eq, registry)())
                        nn = M.Pair(L.NonNegativeLabel, M.Pair(lx, M.EmptyList))
                        P._debug("union: " + M.PrettyTerm(nn, registry)())
                        sqrt_term = M.Pair(L.SqrtLabel, M.Pair(product, M.EmptyList))
                        x = CurrentApply(first, registry)()
                        self.result = M.Pair(L.ExprEqLabel, M.Pair(x, M.Pair(sqrt_term, M.EmptyList)))
                        P._debug("union: " + M.PrettyTerm(self.result, registry)())
        super().__init__(
            inputs=M.Pair(sequences, M.Pair(product, M.Pair(common, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormulaFromFindings(M.Edge):
    def __init__(self, start, phi, registry, rewrite_rules):
        facts = StateFacts(start)()
        sequences = CollectSequenceFacts(facts, registry)()
        product = ProductOfBases(sequences, registry)()
        meet = FindLimit(sequences, product, registry, rewrite_rules, facts)()
        self.result = CombineMeetAndProduct(sequences, product, meet, registry)()
        super().__init__(
            inputs=M.Pair(start, M.Pair(phi, M.Pair(registry, M.Pair(rewrite_rules, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TransformFindings(M.Edge):
    def __init__(self, start, phi, registry, rewrite_rules):
        facts = StateFacts(start)()
        sequences = CollectSequenceFacts(facts, registry)()
        examined = ExamineTransforms(start, phi, registry, rewrite_rules)()
        if IsPreserves(examined)() is M.false_value:
            self.result = M.EmptyList
        elif M.IdentityCompare(sequences, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            product = ProductOfBases(sequences, registry)()
            common = FindLimit(sequences, product, registry, rewrite_rules)()
            formula = CombineMeetAndProduct(sequences, product, common, registry)()
            if M.IdentityCompare(common, M.EmptyList)() is M.truth_value:
                self.result = M.EmptyList
            elif M.IdentityCompare(formula, M.EmptyList)() is M.truth_value:
                self.result = M.EmptyList
            else:
                current = ProductOfCurrentTerms(sequences, registry)()
                current_eq = M.Pair(L.ExprEqLabel, M.Pair(current, M.Pair(product, M.EmptyList)))
                first = M.Head(sequences)()
                x_name = SequenceNameOf(first, registry)()
                lx = M.Pair(L.LimitValueLabel, M.Pair(x_name, M.EmptyList))
                nn = M.Pair(L.NonNegativeLabel, M.Pair(lx, M.EmptyList))
                self.result = M.Pair(current_eq, M.Pair(common, M.Pair(nn, M.EmptyList)))
        super().__init__(inputs=M.Pair(start, M.Pair(phi, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class AddFindings(M.Edge):
    def __init__(self, state, findings):
        facts = StateFacts(state)()
        extra = findings
        while M.IdentityCompare(extra, M.EmptyList)() is M.false_value:
            facts = M.Pair(M.Head(extra)(), facts)
            extra = M.Tail(extra)()
        self.result = P.Knowledge(facts)()
        super().__init__(inputs=M.Pair(state, M.Pair(findings, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Invariant(M.Edge):
    def __init__(self, phi, ruleset, registry, start, rewrite_rules):
        self.phi = phi
        self.registry = registry
        transform = ExamineTransforms(start, phi, registry, rewrite_rules)()
        walked = self._walk(ruleset)
        if IsInvariantRefuted(walked)() is M.truth_value:
            self.result = walked
        elif IsPreserves(transform)() is M.truth_value:
            self.result = M.Pair(L.InvariantLabel, M.Pair(self.phi, M.Pair(ruleset, M.Pair(transform, M.EmptyList))))
        elif M.IdentityCompare(ruleset, M.EmptyList)() is M.truth_value:
            self.result = InvariantCandidate(phi, ruleset)()
        else:
            self.result = walked
        super().__init__(
            inputs=M.Pair(phi, M.Pair(ruleset, M.Pair(registry, M.Pair(start, M.EmptyList)))),
            results=self.result,
        )

    def _walk(self, ruleset):
        if M.IdentityCompare(ruleset, M.EmptyList)() is M.truth_value:
            return InvariantCandidate(self.phi, ruleset)()
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
                if M.Compare(start_value, goal_value)() is M.false_value:
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
        if P.IsKnowledge(self.goal)() is M.truth_value:
            if P.IsKnowledge(current)() is M.truth_value:
                if FactsCover(P.KnowledgeFacts(self.goal)(), P.KnowledgeFacts(current)())() is M.truth_value:
                    acc = M.EmptyList
                    remaining = plan
                    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                        acc = M.Pair(M.Head(remaining)(), acc)
                        remaining = M.Tail(remaining)()
                    return acc
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
        invariant = Invariant(phi, rules, registry, start, rules)()
        board = start
        if IsInvariant(invariant)() is M.truth_value:
            findings = TransformFindings(start, phi, registry, rules)()
            if M.IdentityCompare(findings, M.EmptyList)() is M.false_value:
                board = AddFindings(start, findings)()
        prune = ReachabilityPrune(board, goal, invariant, phi, registry)()
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
            plan = RewriteSearch(board, goal, rules, registry)()
            outcome = S.SearchFailureLabel
            covered = M.false_value
            if P.IsKnowledge(goal)() is M.truth_value:
                if P.IsKnowledge(board)() is M.truth_value:
                    covered = FactsCover(P.KnowledgeFacts(goal)(), P.KnowledgeFacts(board)())()
            if M.IdentityCompare(plan, M.EmptyList)() is M.false_value:
                outcome = S.SearchSuccessLabel
            elif covered is M.truth_value:
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
