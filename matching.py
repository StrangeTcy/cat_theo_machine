from __future__ import annotations

from . import labels as L
from . import machine as M
from . import proof as P


class Rewrite(M.Edge):
    def __init__(self, rule, target, registry):
        self.rule = rule
        self.target = target
        self.registry = registry
        result_atom = self._rewrite(rule, target)
        self.result = M.Pair(result_atom, M.EmptyList)
        super().__init__(
            inputs=M.Pair(rule, M.Pair(target, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _rewrite(self, rule, target):
        pattern = P.RulePattern(rule)()
        replacement = P.RuleReplacement(rule)()
        match = M.Match(pattern, target)()

        flag = M.Head(match)()
        binds = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            inst = M.Instantiate(replacement, binds)()
            return M.Head(inst)()

        if M.IsPair(target)() is M.truth_value:
            new_h = self._rewrite(rule, M.Head(target)())
            new_t = self._rewrite(rule, M.Tail(target)())
            return M.Pair(new_h, new_t)

        return target

    def __call__(self):
        return self.result


class TermEqual(M.Edge):
    def __init__(self, x, y):
        self.result = self._eq(x, y)
        super().__init__(inputs=M.Pair(x, M.Pair(y, M.EmptyList)), results=self.result)

    def _eq(self, x, y):
        stack = M.Pair(M.Pair(x, y), M.EmptyList)
        while M.IdentityCompare(stack, M.EmptyList)() is M.false_value:
            top = M.Head(stack)()
            stack = M.Tail(stack)()
            left = M.Head(top)()
            right = M.Tail(top)()

            if M.IdentityCompare(left, right)() is M.truth_value:
                continue

            x_is_pair = M.IsPair(left)()
            y_is_pair = M.IsPair(right)()
            if M.AndAtom(x_is_pair, y_is_pair)() is M.truth_value:
                stack = M.Pair(M.Pair(M.Head(left)(), M.Head(right)()), stack)
                stack = M.Pair(M.Pair(M.Tail(left)(), M.Tail(right)()), stack)
                continue

            if M.OrAtom(x_is_pair, y_is_pair)() is M.truth_value:
                return M.false_value

            cx = M.GetConstructor(left)()
            cy = M.GetConstructor(right)()
            cx_empty = M.IdentityCompare(cx, M.EmptyList)()
            cy_empty = M.IdentityCompare(cy, M.EmptyList)()
            if M.AndAtom(cx_empty, cy_empty)() is M.truth_value:
                return M.false_value
            if M.OrAtom(cx_empty, cy_empty)() is M.truth_value:
                return M.false_value

            lx = M.Head(cx)()
            ly = M.Head(cy)()
            if M.IdentityCompare(lx, ly)() is M.false_value:
                return M.false_value
            stack = M.Pair(M.Pair(M.Tail(cx)(), M.Tail(cy)()), stack)
        return M.truth_value

    def __call__(self):
        return self.result


class HypergraphIsomorphismMatch(M.Edge):
    """
    Level 2 Matching: Determines if two Hypergraph instances G1 and G2 are isomorphic
    under a consistent bijective renaming of entity carrier nodes across their hyperedges.
    inputs: [hypergraph_1, hypergraph_2, registry]
    results: Pair(is_isomorphic, Pair(renaming_map, Pair(registry, EmptyList)))
    """

    def __init__(self, g1, g2, registry):
        self.registry = registry
        # Extract edge chains from Hypergraph instances or Pair chains
        edges_1 = getattr(g1, "edges", g1)
        edges_2 = getattr(g2, "edges", g2)
        self.result = self._check_isomorphism(edges_1, edges_2, M.EmptyList, registry)
        super().__init__(
            inputs=M.Pair(g1, M.Pair(g2, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _check_isomorphism(self, e1_chain, e2_chain, mapping, reg):
        if M.IdentityCompare(e1_chain, M.EmptyList)() is M.truth_value and M.IdentityCompare(e2_chain, M.EmptyList)() is M.truth_value:
            iso_node = M.Pair(L.IsomorphismLabel, M.Pair(mapping, M.EmptyList))
            return M.Pair(M.truth_value, M.Pair(iso_node, M.Pair(reg, M.EmptyList)))

        if M.IdentityCompare(e1_chain, M.EmptyList)() is M.truth_value or M.IdentityCompare(e2_chain, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList)))

        h1 = M.Head(e1_chain)()
        t1 = M.Tail(e1_chain)()

        h2 = M.Head(e2_chain)()
        t2 = M.Tail(e2_chain)()

        # Relational edge compatibility
        rel1 = M.Head(h1)()
        rel2 = M.Head(h2)()

        if M.Compare(rel1, rel2)() is M.false_value:
            return M.Pair(M.false_value, M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList)))

        # Update bijective renaming mapping
        arg1 = M.Head(M.Tail(h1)())()
        arg2 = M.Head(M.Tail(h2)())()
        new_mapping = M.Pair(M.Pair(arg1, arg2), mapping)

        return self._check_isomorphism(t1, t2, new_mapping, reg)

    def __call__(self):
        return self.result


class HypergraphSharedInvariantBridge(M.Edge):
    """
    Level 4 Matching: Detects when two non-isomorphic parent graphs G1 and G2
    both produce isomorphic or matching intermediate invariant representations (e.g. E -> rho <- f).
    inputs: [entity_1, invariant_getter_1, entity_2, invariant_getter_2, registry]
    results: Pair(SharedInvariantBridgeLabel, Pair(bridge_node, Pair(registry, EmptyList)))
    """

    def __init__(self, e1, get_inv_1, e2, get_inv_2, registry):
        self.registry = registry
        self.result = self._bridge(e1, get_inv_1, e2, get_inv_2, registry)
        super().__init__(
            inputs=M.Pair(e1, M.Pair(e2, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _bridge(self, e1, get_inv_1, e2, get_inv_2, reg):
        res1 = get_inv_1(e1, reg)
        inv1 = M.Head(res1)()
        r1 = M.Head(M.Tail(res1)())()

        res2 = get_inv_2(e2, r1)
        inv2 = M.Head(res2)()
        r2 = M.Head(M.Tail(res2)())()

        # Check equivalence between intermediate invariants
        eq_res = M.Compare(inv1, inv2)()

        if eq_res is M.truth_value:
            bridge_node = M.Pair(
                L.SharedInvariantBridgeLabel,
                M.Pair(
                    e1,
                    M.Pair(
                        e2,
                        M.Pair(inv1, M.EmptyList),
                    ),
                ),
            )
            return M.Pair(M.truth_value, M.Pair(bridge_node, M.Pair(r2, M.EmptyList)))

        return M.Pair(M.false_value, M.Pair(M.EmptyList, M.Pair(r2, M.EmptyList)))

    def __call__(self):
        return self.result


FindBinding = M.FindBinding
MergeBindings = M.MergeBindings
Match = M.Match
Instantiate = M.Instantiate
IsPair = M.IsPair
IsEdge = M.IsEdge
IsAtom = M.IsAtom
ContainsVar = P.ContainsVar
IsVarPattern = P.IsVarPattern
TermHead = P.TermHead
RulePattern = P.RulePattern
RuleReplacement = P.RuleReplacement

__all__ = [name for name in globals() if not name.startswith("_")]
