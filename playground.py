# ============================================================
# Playground — Machine-Native Irreducible Cartesian Engine
#
# Foundational arity-agnostic Cartesian product generator,
# Peano-native sequence counting, tuple operations, universal
# relational quantifiers, and congruence projections.
# ============================================================
from __future__ import annotations

from . import constructors as C
from . import labels as L
from . import machine as M
from .math import arithmetic as A


class ChainLength(M.Edge):
    """
    Computes the length of a Pair chain as a native Peano Nat node (Zero/Succ).
    """

    def __init__(self, chain, registry):
        self.registry = registry
        self.result = self._count(chain, registry)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _count(self, chain, registry):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.Pair(M.Zero, M.Pair(registry, M.EmptyList))
        tail = M.Tail(chain)()
        tail_res = self._count(tail, registry)
        tail_len = M.Head(tail_res)()
        reg1 = M.Head(M.Tail(tail_res)())()

        succ_atom = M.Atom()
        constructed = C.ConstructedBy(
            succ_atom, L.SuccLabel, M.Pair(tail_len, M.EmptyList), reg1
        )()
        succ_node = M.Head(constructed)()
        reg2 = M.Head(M.Tail(constructed)())()
        return M.Pair(succ_node, M.Pair(reg2, M.EmptyList))

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
    Builds a finite domain of Nat nodes stepping from start_nat for count_nat steps.
    """

    def __init__(self, start_nat, count_nat, registry):
        self.registry = registry
        self.result = self._build(start_nat, count_nat, registry)
        super().__init__(
            inputs=M.Pair(
                start_nat,
                M.Pair(count_nat, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _build(self, cur_start, cur_count, registry):
        is_zero = M.NatEq(cur_count, M.Zero, registry)()
        if is_zero is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

        pred_res = M.NatPred(cur_count, registry)()
        pred_count = M.Head(pred_res)()
        reg1 = M.Head(M.Tail(pred_res)())()

        # Construct successor of start for next iteration
        succ_atom = M.Atom()
        constructed = C.ConstructedBy(
            succ_atom, L.SuccLabel, M.Pair(cur_start, M.EmptyList), reg1
        )()
        next_start = M.Head(constructed)()
        reg2 = M.Head(M.Tail(constructed)())()

        rest_res = self._build(next_start, pred_count, reg2)
        rest_chain = M.Head(rest_res)()
        reg3 = M.Head(M.Tail(rest_res)())()

        return M.Pair(
            M.Pair(cur_start, rest_chain),
            M.Pair(reg3, M.EmptyList),
        )

    def __call__(self):
        return self.result


class ProductOfDomains(M.Edge):
    """
    Irreducible k-ary Cartesian product builder.
    Takes a Pair chain of domains [D_1, D_2, ..., D_k] and produces
    the product of tuples [[x_1, x_2, ..., x_k] for x_i in D_i].
    """

    def __init__(self, domains_chain):
        self.result = self._prod(domains_chain)
        super().__init__(
            inputs=M.Pair(domains_chain, M.EmptyList),
            results=self.result,
        )

    def _prod(self, domains):
        if M.IdentityCompare(domains, M.EmptyList)() is M.truth_value:
            # Base case: 0-ary product is a single empty tuple [[]]
            return M.Pair(M.EmptyList, M.EmptyList)
        head_dom = M.Head(domains)()
        tail_doms = M.Tail(domains)()
        rest_prod = self._prod(tail_doms)
        return self._distribute_outer(head_dom, rest_prod)

    def _distribute_outer(self, cur_head, rest_prod):
        if M.IdentityCompare(cur_head, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        x = M.Head(cur_head)()
        with_x = self._distribute_inner(x, rest_prod)
        rest = self._distribute_outer(M.Tail(cur_head)(), rest_prod)
        return self._concat(with_x, rest)

    def _distribute_inner(self, x, cur_tuples):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        t = M.Head(cur_tuples)()
        new_tuple = M.Pair(x, t)
        return M.Pair(new_tuple, self._distribute_inner(x, M.Tail(cur_tuples)()))

    def _concat(self, list1, list2):
        if M.IdentityCompare(list1, M.EmptyList)() is M.truth_value:
            return list2
        return M.Pair(M.Head(list1)(), self._concat(M.Tail(list1)(), list2))

    def __call__(self):
        return self.result


class FilterTuples(M.Edge):
    """
    Filters a k-tuple domain by an evaluable predicate.
    pred_fn: lambda tuple_chain, reg -> (truth/false, updated_reg)
    """

    def __init__(self, tuples_chain, pred_fn, registry):
        self.registry = registry
        self.result = self._filter(tuples_chain, pred_fn, registry)
        super().__init__(
            inputs=M.Pair(tuples_chain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _filter(self, cur_tuples, pred_fn, registry):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        t = M.Head(cur_tuples)()
        pred_res = pred_fn(t, registry)
        passed = M.Head(pred_res)()
        reg1 = M.Head(M.Tail(pred_res)())()

        rest_res = self._filter(M.Tail(cur_tuples)(), pred_fn, reg1)
        rest_filtered = M.Head(rest_res)()
        reg2 = M.Head(M.Tail(rest_res)())()

        if passed is M.truth_value:
            return M.Pair(M.Pair(t, rest_filtered), M.Pair(reg2, M.EmptyList))
        return M.Pair(rest_filtered, M.Pair(reg2, M.EmptyList))

    def __call__(self):
        return self.result


class MapDomain(M.Edge):
    """
    Uniform k-ary domain evaluator.
    Takes a domain of k-tuples and an operation evaluator f(args_tuple, reg).
    Produces the evaluation list and unique image set.
    """

    def __init__(self, tuples_chain, eval_fn, registry):
        self.registry = registry
        self.result = self._map(
            tuples_chain, eval_fn, M.EmptyList, M.EmptyList, registry
        )
        super().__init__(
            inputs=M.Pair(tuples_chain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _map(self, cur_tuples, eval_fn, acc_list, acc_set, registry):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(
                acc_list,
                M.Pair(acc_set, M.Pair(registry, M.EmptyList)),
            )
        t = M.Head(cur_tuples)()
        eval_res = eval_fn(t, registry)
        val = M.Head(eval_res)()
        reg1 = M.Head(M.Tail(eval_res)())()

        new_set = SetInsert(val, acc_set, reg1)()
        new_list = M.Pair(val, acc_list)
        return self._map(
            M.Tail(cur_tuples)(), eval_fn, new_list, new_set, reg1
        )

    def __call__(self):
        return self.result


class UniversalQuantify(M.Edge):
    """
    Universal Relational Quantifier (forall t in D^k : R(t)).
    rel_fn: lambda tuple_chain, reg -> (truth/false, updated_reg)
    """

    def __init__(self, tuples_chain, rel_fn, registry):
        self.registry = registry
        self.result = self._eval(tuples_chain, rel_fn, registry)
        super().__init__(
            inputs=M.Pair(tuples_chain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _eval(self, cur_tuples, rel_fn, registry):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(registry, M.EmptyList))
        t = M.Head(cur_tuples)()
        rel_res = rel_fn(t, registry)
        holds = M.Head(rel_res)()
        reg1 = M.Head(M.Tail(rel_res)())()

        if holds is M.false_value:
            return M.Pair(M.false_value, M.Pair(reg1, M.EmptyList))
        return self._eval(M.Tail(cur_tuples)(), rel_fn, reg1)

    def __call__(self):
        return self.result


class ExistentialQuantify(M.Edge):
    """
    Existential Relational Quantifier (exists t in D^k : R(t)).
    rel_fn: lambda tuple_chain, reg -> (truth/false, updated_reg)
    """

    def __init__(self, tuples_chain, rel_fn, registry):
        self.registry = registry
        self.result = self._eval(tuples_chain, rel_fn, registry)
        super().__init__(
            inputs=M.Pair(tuples_chain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _eval(self, cur_tuples, rel_fn, registry):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(registry, M.EmptyList))
        t = M.Head(cur_tuples)()
        rel_res = rel_fn(t, registry)
        holds = M.Head(rel_res)()
        reg1 = M.Head(M.Tail(rel_res)())()

        if holds is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(reg1, M.EmptyList))
        return self._eval(M.Tail(cur_tuples)(), rel_fn, reg1)

    def __call__(self):
        return self.result


class ProjectCongruence(M.Edge):
    """
    Projects a set of values under an equivalence modulus M.
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


class EvaluateSetRelation(M.Edge):
    """
    Evaluates relations between image sets:
    - Disjointness (intersection is empty)
    - Constant image (singleton set)
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
        is_disjoint = M.IdentityCompare(inter, M.EmptyList)()
        return M.Pair(
            is_disjoint,
            M.Pair(inter, M.Pair(registry, M.EmptyList)),
        )

    def __call__(self):
        return self.result


class RunPlaygroundCartesianSweep(M.Edge):
    """
    Generic Cartesian sweep using pure irreducible primitives:
    - ProductOfDomains builds arbitrary k-ary domain products.
    - MapDomain evaluates k-ary operations over tuples.
    - ProjectCongruence evaluates equivalence projections.
    - EvaluateSetRelation evaluates image regularities.
    """

    def __init__(self, bound_nat, mod_nat, registry):
        self.registry = registry
        self.result = self._run(bound_nat, mod_nat, registry)
        super().__init__(
            inputs=M.Pair(
                bound_nat,
                M.Pair(mod_nat, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _run(self, bound_nat, mod_nat, registry):
        # 1. Base primitive domain: start from Zero for bound_nat steps
        range_res = BuildNatRange(M.Zero, bound_nat, registry)()
        domain = M.Head(range_res)()
        reg1 = M.Head(M.Tail(range_res)())()

        # 2. Parity constants (2 and 1)
        two_res = M.NatFromRep(M.GMPRep(2), reg1)()
        two_nat = M.Head(two_res)()
        reg2 = M.Head(M.Tail(two_res)())()

        one_res = M.NatFromRep(M.GMPRep(1), reg2)()
        one_nat = M.Head(one_res)()
        reg3 = M.Head(M.Tail(one_res)())()

        # 3. 1-ary domain: ProductOfDomains([domain])
        dom1 = ProductOfDomains(M.Pair(domain, M.EmptyList))()

        # 1-ary operation over 1-tuple [x]: f([x]) = x * x
        def square_fn(tuple_args, reg):
            x = M.Head(tuple_args)()
            return A.Multiply(x, x, reg)()

        sq_map_res = MapDomain(dom1, square_fn, reg3)()
        sq_list = M.Head(sq_map_res)()
        reg4 = M.Head(M.Tail(M.Tail(sq_map_res)())())()

        # Project 1-ary image modulo M
        sq_proj_res = ProjectCongruence(sq_list, mod_nat, reg4)()
        sq_mod_set = M.Head(sq_proj_res)()
        reg5 = M.Head(M.Tail(sq_proj_res)())()

        # 4. 2-ary domain: ProductOfDomains([domain, domain])
        dom2 = ProductOfDomains(M.Pair(domain, M.Pair(domain, M.EmptyList)))()

        # Filter 2-tuples by parity: x mod 2 == 1 and y mod 2 == 1
        def odd_pair_pred(tuple_args, reg):
            x = M.Head(tuple_args)()
            y = M.Head(M.Tail(tuple_args)())()

            rx = A.Modulo(x, two_nat, reg)()
            rem_x = M.Head(rx)()
            r1 = M.Head(M.Tail(rx)())()
            eq_x = M.NatEq(rem_x, one_nat, r1)()

            ry = A.Modulo(y, two_nat, r1)()
            rem_y = M.Head(ry)()
            r2 = M.Head(M.Tail(ry)())()
            eq_y = M.NatEq(rem_y, one_nat, r2)()

            if eq_x is M.truth_value and eq_y is M.truth_value:
                return M.Pair(M.truth_value, M.Pair(r2, M.EmptyList))
            return M.Pair(M.false_value, M.Pair(r2, M.EmptyList))

        odd_tuples_res = FilterTuples(dom2, odd_pair_pred, reg5)()
        odd_tuples = M.Head(odd_tuples_res)()
        reg6 = M.Head(M.Tail(odd_tuples_res)())()

        # 2-ary operation over 2-tuple [x, y]: g([x, y]) = x^2 + y^2
        def sum_sq_fn(tuple_args, reg):
            x = M.Head(tuple_args)()
            y = M.Head(M.Tail(tuple_args)())()

            sx = A.Multiply(x, x, reg)()
            nx = M.Head(sx)()
            r1 = M.Head(M.Tail(sx)())()

            sy = A.Multiply(y, y, r1)()
            ny = M.Head(sy)()
            r2 = M.Head(M.Tail(sy)())()

            return A.Add(nx, ny, r2)()

        odd_sum_map_res = MapDomain(odd_tuples, sum_sq_fn, reg6)()
        odd_sum_list = M.Head(odd_sum_map_res)()
        reg7 = M.Head(M.Tail(M.Tail(odd_sum_map_res)())())()

        # Project 2-ary image modulo M
        odd_sum_proj_res = ProjectCongruence(odd_sum_list, mod_nat, reg7)()
        odd_sum_mod_set = M.Head(odd_sum_proj_res)()
        reg8 = M.Head(M.Tail(odd_sum_proj_res)())()

        # 5. Evaluate relation between image sets (disjointness)
        disjoint_res = EvaluateSetRelation(sq_mod_set, odd_sum_mod_set, reg8)()
        is_disjoint = M.Head(disjoint_res)()
        reg9 = M.Head(M.Tail(M.Tail(disjoint_res)())())()

        # Wrap discovered invariant record
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

        return M.Pair(sweep_record, M.Pair(reg9, M.EmptyList))

    def __call__(self):
        return self.result


def run_playground_interactive(graph):
    """
    Runs the irreducible Cartesian exploration sweep and returns the dynamic formatted proposal.
    """
    registry = M.FromContextGetConstructors(graph)()

    bound_res = M.NatFromRep(M.GMPRep(11), registry)()
    bound_nat = M.Head(bound_res)()
    reg1 = M.Head(M.Tail(bound_res)())()

    mod_res = M.NatFromRep(M.GMPRep(4), reg1)()
    mod_nat = M.Head(mod_res)()
    reg2 = M.Head(M.Tail(mod_res)())()

    sweep_res = RunPlaygroundCartesianSweep(bound_nat, mod_nat, reg2)()
    inv_rec = M.Head(sweep_res)()

    res_mod = M.Head(M.Tail(inv_rec)())()
    mod_val = M.NatRepOf(res_mod, reg2)()()

    sq_set = M.Head(M.Tail(M.Tail(inv_rec)())())()
    odd_sum_set = M.Head(M.Tail(M.Tail(M.Tail(inv_rec)())())())()
    is_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(inv_rec)())())())())()

    # Read values for formatting
    sq_vals = []
    cur = sq_set
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        v = M.NatRepOf(M.Head(cur)(), reg2)()()
        if v not in sq_vals:
            sq_vals.append(v)
        cur = M.Tail(cur)()

    odd_vals = []
    cur = odd_sum_set
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        v = M.NatRepOf(M.Head(cur)(), reg2)()()
        if v not in odd_vals:
            odd_vals.append(v)
        cur = M.Tail(cur)()

    sq_str = "{" + ", ".join(map(str, sorted(sq_vals))) + "}"
    odd_str = "{" + ", ".join(map(str, sorted(odd_vals))) + "}"

    lines = [
        f"[machine] Cartesian Playground Sweep (domain 0..10):",
        f"  - 1-ary Image Projection: f([x]) = x^2 mod {mod_val} -> {sq_str}",
        f"  - 2-ary Image Projection: g([x, y]) = (x^2 + y^2) mod {mod_val} over odd subdomain -> {odd_str}",
    ]

    if is_disjoint is M.truth_value:
        lines.append(
            f"  - Disjoint Image Regularity: {sq_str} /\\ {odd_str} = empty"
        )
        lines.append(
            f"  - Obstruction Invariant: f([z]) = g([x, y]) has no solution for odd x, y under mod {mod_val} projection."
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
    "ProductOfDomains",
    "FilterTuples",
    "MapDomain",
    "UniversalQuantify",
    "ExistentialQuantify",
    "ProjectCongruence",
    "EvaluateSetRelation",
    "RunPlaygroundCartesianSweep",
    "run_playground_interactive",
)
