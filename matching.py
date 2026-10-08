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

    def _eq(self, left, right):
        if M.IdentityCompare(left, right)() is M.truth_value:
            return M.truth_value

        x_is_pair = M.IsPair(left)()
        y_is_pair = M.IsPair(right)()
        if M.AndAtom(x_is_pair, y_is_pair)() is M.truth_value:
            head_eq = self._eq(M.Head(left)(), M.Head(right)())
            if head_eq is M.false_value:
                return M.false_value
            return self._eq(M.Tail(left)(), M.Tail(right)())

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
        return self._eq(M.Tail(cx)(), M.Tail(cy)())

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
        self.result = self._match_hypergraphs(g1.edges, g2.edges, M.EmptyList, registry)
        super().__init__(
            inputs=M.Pair(g1, M.Pair(g2, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _match_hypergraphs(self, remaining_e1, pool_e2, mapping, reg):
        # Base case: All edges in G1 matched
        if M.IdentityCompare(remaining_e1, M.EmptyList)() is M.truth_value:
            # G2 must also have no unmatched edges left (bijective edge count)
            if M.IdentityCompare(pool_e2, M.EmptyList)() is M.truth_value:
                iso_node = M.Pair(L.IsomorphismLabel, M.Pair(mapping, M.EmptyList))
                return M.Pair(M.truth_value, M.Pair(iso_node, M.Pair(reg, M.EmptyList)))
            return M.Pair(M.false_value, M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList)))

        target_e1 = M.Head(remaining_e1)()
        rest_e1 = M.Tail(remaining_e1)()

        # Search through pool_e2 for an edge matching target_e1
        return self._search_candidate_e2(target_e1, rest_e1, pool_e2, M.EmptyList, mapping, reg)

    def _search_candidate_e2(self, target_e1, rest_e1, current_pool, skipped_pool, mapping, reg):
        if M.IdentityCompare(current_pool, M.EmptyList)() is M.truth_value:
            # No edge in G2 matches target_e1 under current mapping
            return M.Pair(M.false_value, M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList)))

        candidate_e2 = M.Head(current_pool)()
        other_candidates = M.Tail(current_pool)()

        # Try to unify target_e1 with candidate_e2
        unify_res = self._unify_edges(target_e1, candidate_e2, mapping)
        can_unify = M.Head(unify_res)()
        extended_mapping = M.Head(M.Tail(unify_res)())()

        if can_unify is M.truth_value:
            # Candidate matched: remove candidate_e2 from pool
            new_pool = self._concat_chains(skipped_pool, other_candidates)
            sub_res = self._match_hypergraphs(rest_e1, new_pool, extended_mapping, reg)
            if M.Head(sub_res)() is M.truth_value:
                return sub_res

        # Backtrack: skip this candidate edge and try the rest of pool_e2
        new_skipped = M.Pair(candidate_e2, skipped_pool)
        return self._search_candidate_e2(target_e1, rest_e1, other_candidates, new_skipped, mapping, reg)

    def _unify_edges(self, edge1, edge2, mapping):
        rel1 = M.Head(edge1)()
        rel2 = M.Head(edge2)()
        if M.Compare(rel1, rel2)() is M.false_value:
            return M.Pair(M.false_value, M.Pair(mapping, M.EmptyList))

        args1 = M.Tail(edge1)()
        args2 = M.Tail(edge2)()
        return self._unify_args(args1, args2, mapping)

    def _unify_args(self, args1, args2, mapping):
        if M.IdentityCompare(args1, M.EmptyList)() is M.truth_value and M.IdentityCompare(args2, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(mapping, M.EmptyList))
        if M.IdentityCompare(args1, M.EmptyList)() is M.truth_value or M.IdentityCompare(args2, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(mapping, M.EmptyList))

        a1 = M.Head(args1)()
        a2 = M.Head(args2)()

        # Check bijective mapping consistency
        bind_res = self._extend_bijection(a1, a2, mapping)
        is_consistent = M.Head(bind_res)()
        if is_consistent is M.false_value:
            return M.Pair(M.false_value, M.Pair(mapping, M.EmptyList))

        new_map = M.Head(M.Tail(bind_res)())()
        return self._unify_args(M.Tail(args1)(), M.Tail(args2)(), new_map)

    def _extend_bijection(self, x, y, cur_map):
        # 1. Forward lookup: has x been mapped?
        forward_val = self._lookup_forward(x, cur_map)
        if M.IdentityCompare(forward_val, M.EmptyList)() is M.false_value:
            if M.Compare(forward_val, y)() is M.truth_value:
                return M.Pair(M.truth_value, M.Pair(cur_map, M.EmptyList))
            return M.Pair(M.false_value, M.Pair(cur_map, M.EmptyList))

        # 2. Reverse lookup: has y already been mapped to something other than x?
        reverse_val = self._lookup_reverse(y, cur_map)
        if M.IdentityCompare(reverse_val, M.EmptyList)() is M.false_value:
            return M.Pair(M.false_value, M.Pair(cur_map, M.EmptyList))

        # 3. Fresh pair: extend bijective mapping
        extended = M.Pair(M.Pair(x, y), cur_map)
        return M.Pair(M.truth_value, M.Pair(extended, M.EmptyList))

    def _lookup_forward(self, key, cur_map):
        if M.IdentityCompare(cur_map, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(cur_map)()
        if M.Compare(M.Head(entry)(), key)() is M.truth_value:
            return M.Tail(entry)()
        return self._lookup_forward(key, M.Tail(cur_map)())

    def _lookup_reverse(self, val, cur_map):
        if M.IdentityCompare(cur_map, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(cur_map)()
        if M.Compare(M.Tail(entry)(), val)() is M.truth_value:
            return M.Head(entry)()
        return self._lookup_reverse(val, M.Tail(cur_map)())

    def _concat_chains(self, list1, list2):
        if M.IdentityCompare(list1, M.EmptyList)() is M.truth_value:
            return list2
        return M.Pair(M.Head(list1)(), self._concat_chains(M.Tail(list1)(), list2))

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
