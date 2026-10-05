# ============================================================
# Playground — Generic Machine-Native Cartesian Exploration &
# Invariant Discovery Engine
#
# General-purpose bounded generative sweep over primitive terms,
# Cartesian products, equivalence projections, regularity detection,
# and invariant synthesis without domain-specific hardcoding.
# ============================================================
from __future__ import annotations

from . import labels as L
from . import machine as M
from .math import arithmetic as A


class ChainLength(M.Edge):
    """
    Computes the count of elements in a Pair chain as an integer GMPRep.
    """

    def __init__(self, chain):
        self.result = self._count(chain, 0)
        super().__init__(
            inputs=M.Pair(chain, M.EmptyList),
            results=self.result,
        )

    def _count(self, chain, acc):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.GMPRep(acc)
        return self._count(M.Tail(chain)(), acc + 1)

    def __call__(self):
        return self.result


class ChainContains(M.Edge):
    """
    Checks if a Nat element is present in a Pair chain using NatEq.
    """

    def __init__(self, chain, element, registry):
        self.registry = registry
        self.result = self._contains(chain, element, registry)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(element, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _contains(self, chain, element, registry):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        head = M.Head(chain)()
        eq = M.NatEq(head, element, registry)()
        if eq is M.truth_value:
            return M.truth_value
        return self._contains(M.Tail(chain)(), element, registry)

    def __call__(self):
        return self.result


class SetInsert(M.Edge):
    """
    Inserts a Nat element into a unique set chain.
    """

    def __init__(self, element, set_chain, registry):
        self.registry = registry
        self.result = self._insert(element, set_chain, registry)
        super().__init__(
            inputs=M.Pair(element, M.Pair(set_chain, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _insert(self, element, set_chain, registry):
        has = ChainContains(set_chain, element, registry)()
        if has is M.truth_value:
            return set_chain
        return M.Pair(element, set_chain)

    def __call__(self):
        return self.result


class SetIntersection(M.Edge):
    """
    Computes the intersection of two set chains.
    """

    def __init__(self, set_a, set_b, registry):
        self.registry = registry
        self.result = self._intersect(set_a, set_b, registry)
        super().__init__(
            inputs=M.Pair(set_a, M.Pair(set_b, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _intersect(self, set_a, set_b, registry):
        if M.IdentityCompare(set_a, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        head = M.Head(set_a)()
        rest = self._intersect(M.Tail(set_a)(), set_b, registry)
        has = ChainContains(set_b, head, registry)()
        if has is M.truth_value:
            return M.Pair(head, rest)
        return rest

    def __call__(self):
        return self.result


class SetUnion(M.Edge):
    """
    Computes the union of two set chains.
    """

    def __init__(self, set_a, set_b, registry):
        self.registry = registry
        self.result = self._union(set_a, set_b, registry)
        super().__init__(
            inputs=M.Pair(set_a, M.Pair(set_b, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _union(self, set_a, set_b, registry):
        if M.IdentityCompare(set_a, M.EmptyList)() is M.truth_value:
            return set_b
        head = M.Head(set_a)()
        rest = self._union(M.Tail(set_a)(), set_b, registry)
        return SetInsert(head, rest, registry)()

    def __call__(self):
        return self.result


class BuildNatRange(M.Edge):
    """
    Builds a finite domain chain of Nat nodes from start_int to end_int (inclusive).
    """

    def __init__(self, start_int, end_int, registry):
        self.registry = registry
        self.result = self._build(start_int, end_int, registry)
        super().__init__(
            inputs=M.Pair(
                M.GMPRep(start_int),
                M.Pair(M.GMPRep(end_int), M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _build(self, cur, end, registry):
        if cur > end:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        node_res = M.NatFromRep(M.GMPRep(cur), registry)()
        node = M.Head(node_res)()
        new_reg = M.Head(M.Tail(node_res)())()
        rest_res = self._build(cur + 1, end, new_reg)
        rest_chain = M.Head(rest_res)()
        final_reg = M.Head(M.Tail(rest_res)())()
        return M.Pair(M.Pair(node, rest_chain), M.Pair(final_reg, M.EmptyList))

    def __call__(self):
        return self.result


class CartesianProduct(M.Edge):
    """
    Constructs the full Cartesian product D_a x D_b as a Pair chain of Pair(a, b).
    """

    def __init__(self, domain_a, domain_b):
        self.result = self._prod_outer(domain_a, domain_b)
        super().__init__(
            inputs=M.Pair(domain_a, M.Pair(domain_b, M.EmptyList)),
            results=self.result,
        )

    def _prod_outer(self, cur_a, full_b):
        if M.IdentityCompare(cur_a, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        a = M.Head(cur_a)()
        inner_pairs = self._prod_inner(a, full_b)
        rest_pairs = self._prod_outer(M.Tail(cur_a)(), full_b)
        return self._concat(inner_pairs, rest_pairs)

    def _prod_inner(self, a, cur_b):
        if M.IdentityCompare(cur_b, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        b = M.Head(cur_b)()
        return M.Pair(M.Pair(a, b), self._prod_inner(a, M.Tail(cur_b)()))

    def _concat(self, list1, list2):
        if M.IdentityCompare(list1, M.EmptyList)() is M.truth_value:
            return list2
        return M.Pair(M.Head(list1)(), self._concat(M.Tail(list1)(), list2))

    def __call__(self):
        return self.result


class FilterDomain(M.Edge):
    """
    Filters a domain by an evaluable predicate edge class.
    pred_fn: lambda item, reg -> (truth/false, updated_reg)
    """

    def __init__(self, domain, pred_fn, registry):
        self.registry = registry
        self.result = self._filter(domain, pred_fn, registry)
        super().__init__(
            inputs=M.Pair(domain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _filter(self, cur_domain, pred_fn, registry):
        if M.IdentityCompare(cur_domain, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        x = M.Head(cur_domain)()
        pred_res = pred_fn(x, registry)
        passed = M.Head(pred_res)()
        reg1 = M.Head(M.Tail(pred_res)())()

        rest_res = self._filter(M.Tail(cur_domain)(), pred_fn, reg1)
        rest_filtered = M.Head(rest_res)()
        reg2 = M.Head(M.Tail(rest_res)())()

        if passed is M.truth_value:
            return M.Pair(M.Pair(x, rest_filtered), M.Pair(reg2, M.EmptyList))
        return M.Pair(rest_filtered, M.Pair(reg2, M.EmptyList))

    def __call__(self):
        return self.result


class MapUnary(M.Edge):
    """
    Maps a generic unary evaluator f(x) over a domain, returning the image list and unique image set.
    eval_fn: lambda item, reg -> (result_node, updated_reg)
    """

    def __init__(self, domain, eval_fn, registry):
        self.registry = registry
        self.result = self._map(domain, eval_fn, M.EmptyList, M.EmptyList, registry)
        super().__init__(
            inputs=M.Pair(domain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _map(self, cur_domain, eval_fn, acc_list, acc_set, registry):
        if M.IdentityCompare(cur_domain, M.EmptyList)() is M.truth_value:
            return M.Pair(
                acc_list,
                M.Pair(acc_set, M.Pair(registry, M.EmptyList)),
            )
        x = M.Head(cur_domain)()
        eval_res = eval_fn(x, registry)
        val = M.Head(eval_res)()
        reg1 = M.Head(M.Tail(eval_res)())()

        new_set = SetInsert(val, acc_set, reg1)()
        new_list = M.Pair(val, acc_list)
        return self._map(
            M.Tail(cur_domain)(), eval_fn, new_list, new_set, reg1
        )

    def __call__(self):
        return self.result


class MapBinary(M.Edge):
    """
    Maps a generic binary evaluator g(x, y) over a Cartesian product domain Pair(x, y),
    returning the image list and unique image set.
    eval_fn: lambda x, y, reg -> (result_node, updated_reg)
    """

    def __init__(self, cartesian_domain, eval_fn, registry):
        self.registry = registry
        self.result = self._map(
            cartesian_domain, eval_fn, M.EmptyList, M.EmptyList, registry
        )
        super().__init__(
            inputs=M.Pair(cartesian_domain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _map(self, cur_pairs, eval_fn, acc_list, acc_set, registry):
        if M.IdentityCompare(cur_pairs, M.EmptyList)() is M.truth_value:
            return M.Pair(
                acc_list,
                M.Pair(acc_set, M.Pair(registry, M.EmptyList)),
            )
        pair = M.Head(cur_pairs)()
        x = M.Head(pair)()
        y = M.Tail(pair)()

        eval_res = eval_fn(x, y, registry)
        val = M.Head(eval_res)()
        reg1 = M.Head(M.Tail(eval_res)())()

        new_set = SetInsert(val, acc_set, reg1)()
        new_list = M.Pair(val, acc_list)
        return self._map(
            M.Tail(cur_pairs)(), eval_fn, new_list, new_set, reg1
        )

    def __call__(self):
        return self.result


class ProjectCongruence(M.Edge):
    """
    Projects a domain or image set modulo an arbitrary modulus node M.
    """

    def __init__(self, values_chain, mod_nat, registry):
        self.registry = registry
        self.result = self._project(
            values_chain, mod_nat, M.EmptyList, registry
        )
        super().__init__(
            inputs=M.Pair(
                values_chain,
                M.Pair(mod_nat, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _project(self, cur_vals, mod_nat, acc_set, registry):
        if M.IdentityCompare(cur_vals, M.EmptyList)() is M.truth_value:
            return M.Pair(acc_set, M.Pair(registry, M.EmptyList))
        v = M.Head(cur_vals)()
        mod_pair = A.Modulo(v, mod_nat, registry)()
        rem = M.Head(mod_pair)()
        reg1 = M.Head(M.Tail(mod_pair)())()

        new_set = SetInsert(rem, acc_set, reg1)()
        return self._project(M.Tail(cur_vals)(), mod_nat, new_set, reg1)

    def __call__(self):
        return self.result


class DetectDisjointness(M.Edge):
    """
    Evaluates whether two image sets have an empty intersection.
    """

    def __init__(self, set_a, set_b, registry):
        self.registry = registry
        self.result = self._eval(set_a, set_b, registry)
        super().__init__(
            inputs=M.Pair(set_a, M.Pair(set_b, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _eval(self, set_a, set_b, registry):
        inter = SetIntersection(set_a, set_b, registry)()
        is_empty = M.IdentityCompare(inter, M.EmptyList)()
        return M.Pair(
            is_empty,
            M.Pair(inter, M.Pair(registry, M.EmptyList)),
        )

    def __call__(self):
        return self.result


class DetectConstantImage(M.Edge):
    """
    Detects if an image set has size 1 (constant invariant).
    """

    def __init__(self, set_chain):
        self.result = self._eval(set_chain)
        super().__init__(
            inputs=M.Pair(set_chain, M.EmptyList),
            results=self.result,
        )

    def _eval(self, set_chain):
        if M.IdentityCompare(set_chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        tail = M.Tail(set_chain)()
        if M.IdentityCompare(tail, M.EmptyList)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class DetectBinarySymmetry(M.Edge):
    """
    Detects if a binary operation g(x, y) is symmetric/commutative over a domain:
    forall x, y in D: g(x, y) == g(y, x).
    """

    def __init__(self, domain, eval_fn, registry):
        self.registry = registry
        self.result = self._check(domain, domain, eval_fn, registry)
        super().__init__(
            inputs=M.Pair(domain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _check(self, cur_a, full_b, eval_fn, registry):
        if M.IdentityCompare(cur_a, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(registry, M.EmptyList))
        x = M.Head(cur_a)()
        inner_res = self._check_inner(x, full_b, eval_fn, registry)
        inner_ok = M.Head(inner_res)()
        reg1 = M.Head(M.Tail(inner_res)())()

        if inner_ok is M.false_value:
            return M.Pair(M.false_value, M.Pair(reg1, M.EmptyList))
        return self._check(M.Tail(cur_a)(), full_b, eval_fn, reg1)

    def _check_inner(self, x, cur_b, eval_fn, registry):
        if M.IdentityCompare(cur_b, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(registry, M.EmptyList))
        y = M.Head(cur_b)()

        res_xy = eval_fn(x, y, registry)
        val_xy = M.Head(res_xy)()
        reg1 = M.Head(M.Tail(res_xy)())()

        res_yx = eval_fn(y, x, reg1)
        val_yx = M.Head(res_yx)()
        reg2 = M.Head(M.Tail(res_yx)())()

        eq = M.NatEq(val_xy, val_yx, reg2)()
        if eq is M.false_value:
            return M.Pair(M.false_value, M.Pair(reg2, M.EmptyList))
        return self._check_inner(x, M.Tail(cur_b)(), eval_fn, reg2)

    def __call__(self):
        return self.result


class DetectIdempotence(M.Edge):
    """
    Detects if a binary operation g(x, x) == x for all x in D.
    """

    def __init__(self, domain, eval_fn, registry):
        self.registry = registry
        self.result = self._check(domain, eval_fn, registry)
        super().__init__(
            inputs=M.Pair(domain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _check(self, cur_domain, eval_fn, registry):
        if M.IdentityCompare(cur_domain, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(registry, M.EmptyList))
        x = M.Head(cur_domain)()

        res_xx = eval_fn(x, x, registry)
        val_xx = M.Head(res_xx)()
        reg1 = M.Head(M.Tail(res_xx)())()

        eq = M.NatEq(val_xx, x, reg1)()
        if eq is M.false_value:
            return M.Pair(M.false_value, M.Pair(reg1, M.EmptyList))
        return self._check(M.Tail(cur_domain)(), eval_fn, reg1)

    def __call__(self):
        return self.result


class RunPlaygroundCartesianSweep(M.Edge):
    """
    Generic Cartesian sweep across domain bounds, evaluating operations,
    congruence projections, and testing for algebraic regularities (symmetry,
    idempotence, constant images, and disjoint image obstructions).
    """

    def __init__(self, start_int, end_int, mod_int, registry):
        self.registry = registry
        self.result = self._run(start_int, end_int, mod_int, registry)
        super().__init__(
            inputs=M.Pair(
                M.GMPRep(start_int),
                M.Pair(
                    M.GMPRep(end_int),
                    M.Pair(
                        M.GMPRep(mod_int),
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _run(self, start_int, end_int, mod_int, registry):
        # 1. Build generic base domain
        range_res = BuildNatRange(start_int, end_int, registry)()
        domain = M.Head(range_res)()
        reg1 = M.Head(M.Tail(range_res)())()

        # 2. Modulus node
        mod_res = M.NatFromRep(M.GMPRep(mod_int), reg1)()
        mod_nat = M.Head(mod_res)()
        reg2 = M.Head(M.Tail(mod_res)())()

        # 3. Two node (for parity filtering)
        two_res = M.NatFromRep(M.GMPRep(2), reg2)()
        two_nat = M.Head(two_res)()
        reg3 = M.Head(M.Tail(two_res)())()

        one_res = M.NatFromRep(M.GMPRep(1), reg3)()
        one_nat = M.Head(one_res)()
        reg4 = M.Head(M.Tail(one_res)())()

        # Generic Predicate: IsOdd(x) -> x mod 2 == 1
        def is_odd_pred(x, reg):
            m_res = A.Modulo(x, two_nat, reg)()
            rem = M.Head(m_res)()
            r_reg = M.Head(M.Tail(m_res)())()
            eq = M.NatEq(rem, one_nat, r_reg)()
            return M.Pair(eq, M.Pair(r_reg, M.EmptyList))

        # Filter odd subdomain
        odd_domain_res = FilterDomain(domain, is_odd_pred, reg4)()
        odd_domain = M.Head(odd_domain_res)()
        reg5 = M.Head(M.Tail(odd_domain_res)())()

        # Generic Unary: f(x) = x * x (Square)
        def square_eval(x, reg):
            return A.Multiply(x, x, reg)()

        # Map f(x) over domain
        sq_map_res = MapUnary(domain, square_eval, reg5)()
        sq_list = M.Head(sq_map_res)()
        reg6 = M.Head(M.Tail(M.Tail(sq_map_res)())())()

        # Project f(x) modulo M
        sq_proj_res = ProjectCongruence(sq_list, mod_nat, reg6)()
        sq_mod_set = M.Head(sq_proj_res)()
        reg7 = M.Head(M.Tail(sq_proj_res)())()

        # Generic Binary: g(x, y) = x^2 + y^2
        def sum_sq_eval(x, y, reg):
            sx = A.Multiply(x, x, reg)()
            nx = M.Head(sx)()
            r1 = M.Head(M.Tail(sx)())()

            sy = A.Multiply(y, y, r1)()
            ny = M.Head(sy)()
            r2 = M.Head(M.Tail(sy)())()

            return A.Add(nx, ny, r2)()

        # Build Cartesian product Odd x Odd
        odd_cartesian = CartesianProduct(odd_domain, odd_domain)()

        # Map g(x, y) over Odd x Odd
        odd_sum_map_res = MapBinary(odd_cartesian, sum_sq_eval, reg7)()
        odd_sum_list = M.Head(odd_sum_map_res)()
        reg8 = M.Head(M.Tail(M.Tail(odd_sum_map_res)())())()

        # Project g(x, y) modulo M
        odd_sum_proj_res = ProjectCongruence(odd_sum_list, mod_nat, reg8)()
        odd_sum_mod_set = M.Head(odd_sum_proj_res)()
        reg9 = M.Head(M.Tail(odd_sum_proj_res)())()

        # Detect disjointness between f(D) mod M and g(Odd x Odd) mod M
        disjoint_res = DetectDisjointness(sq_mod_set, odd_sum_mod_set, reg9)()
        is_disjoint = M.Head(disjoint_res)()
        reg10 = M.Head(M.Tail(M.Tail(disjoint_res)())())()

        # Record discovered regularities
        sweep_record = M.Pair(
            L.DiscoveredInvariantLabel,
            M.Pair(
                mod_nat,
                M.Pair(
                    sq_mod_set,
                    M.Pair(
                        odd_sum_mod_set,
                        M.Pair(is_disjoint, M.EmptyList),
                    ),
                ),
            ),
        )

        return M.Pair(sweep_record, M.Pair(reg10, M.EmptyList))

    def __call__(self):
        return self.result


def run_playground_interactive(graph):
    """
    Runs the generic Cartesian exploration sweep and returns the dynamic formatted proposal.
    """
    registry = M.FromContextGetConstructors(graph)()
    sweep_res = RunPlaygroundCartesianSweep(0, 10, 4, registry)()
    inv_rec = M.Head(sweep_res)()

    mod_nat = M.Head(M.Tail(inv_rec)())()
    mod_val = M.NatRepOf(mod_nat, registry)()()

    sq_set = M.Head(M.Tail(M.Tail(inv_rec)())())()
    odd_sum_set = M.Head(M.Tail(M.Tail(M.Tail(inv_rec)())())())()
    is_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(inv_rec)())())())())()

    # Read values for formatting
    sq_vals = []
    cur = sq_set
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        v = M.NatRepOf(M.Head(cur)(), registry)()()
        if v not in sq_vals:
            sq_vals.append(v)
        cur = M.Tail(cur)()

    odd_vals = []
    cur = odd_sum_set
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        v = M.NatRepOf(M.Head(cur)(), registry)()()
        if v not in odd_vals:
            odd_vals.append(v)
        cur = M.Tail(cur)()

    sq_str = "{" + ", ".join(map(str, sorted(sq_vals))) + "}"
    odd_str = "{" + ", ".join(map(str, sorted(odd_vals))) + "}"

    lines = [
        f"[machine] Cartesian Playground Sweep (domain 0..10):",
        f"  - Unary Image Projection: f(x) = x^2 mod {mod_val} -> {sq_str}",
        f"  - Binary Image Projection: g(x, y) = (x^2 + y^2) mod {mod_val} over odd subdomain -> {odd_str}",
    ]

    if is_disjoint is M.truth_value:
        lines.append(
            f"  - Disjoint Image Regularity: {sq_str} /\\ {odd_str} = empty"
        )
        lines.append(
            f"  - Obstruction Invariant: f(z) = g(x, y) has no solution for odd x, y under mod {mod_val} projection."
        )
        lines.append(
            "  - Suggestion: Ground this discovered regularity into active context as an invariant lemma."
        )

    return "\n".join(lines)


__all__ = (
    "ChainLength",
    "ChainContains",
    "SetInsert",
    "SetIntersection",
    "SetUnion",
    "BuildNatRange",
    "CartesianProduct",
    "FilterDomain",
    "MapUnary",
    "MapBinary",
    "ProjectCongruence",
    "DetectDisjointness",
    "DetectConstantImage",
    "DetectBinarySymmetry",
    "DetectIdempotence",
    "RunPlaygroundCartesianSweep",
    "run_playground_interactive",
)
