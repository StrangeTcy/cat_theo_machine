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


class EvaluateOperationTensor(M.Edge):
    """
    Evaluates an arithmetic operation across all tuples in a k-ary domain product,
    generating a ground EvaluationTensor record.
    inputs: [op_name, op_func, tuples_chain, registry]
    results: Pair(EvaluationTensorLabel, Pair(op_name, Pair(entry_chain, Pair(registry, EmptyList))))
    """

    def __init__(self, op_name, op_func, tuples_chain, registry):
        self.registry = registry
        self.result = self._eval_tensor(op_name, op_func, tuples_chain, registry)
        super().__init__(
            inputs=M.Pair(
                op_name,
                M.Pair(tuples_chain, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _eval_tensor(self, op_name, op_func, cur_tuples, reg):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            tensor_node = M.Pair(
                L.EvaluationTensorLabel,
                M.Pair(op_name, M.Pair(M.EmptyList, M.EmptyList)),
            )
            return M.Pair(tensor_node, M.Pair(reg, M.EmptyList))

        head_tuple = M.Head(cur_tuples)()
        tail_tuples = M.Tail(cur_tuples)()

        call_res = op_func(head_tuple, reg)
        out_val = M.Head(call_res)()
        r1 = M.Head(M.Tail(call_res)())()

        rest_res = self._eval_tensor(op_name, op_func, tail_tuples, r1)
        rest_tensor = M.Head(rest_res)()
        r2 = M.Head(M.Tail(rest_res)())()

        rest_entries = M.Head(M.Tail(M.Tail(rest_tensor)())())()

        entry = M.Pair(
            L.EvaluationEntryLabel,
            M.Pair(head_tuple, M.Pair(out_val, M.EmptyList)),
        )

        tensor_node = M.Pair(
            L.EvaluationTensorLabel,
            M.Pair(op_name, M.Pair(M.Pair(entry, rest_entries), M.EmptyList)),
        )
        return M.Pair(tensor_node, M.Pair(r2, M.EmptyList))

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


class RunPlaygroundFilteredPowerSweep(M.Edge):
    """
    Parameterized Cartesian sweep, generalizing RunPlaygroundCartesianSweep.

    The original sweep is fixed to squares over an odd-pair filter. This one
    takes the exponent and both domain filters as parameters, so one piece of
    machinery runs any power-image / filtered-sum-image disjointness test:

        unary image    = { x^k mod m : x in domain, unary_pred(x) }
        pair-sum image = { (x^k + y^k) mod m : x, y in domain, pair_pred(x, y) }

    Predicates are host-layer callables over machine values and return a
    machine truth value directly: unary_pred(x_nat, registry) and
    pair_pred(x_nat, y_nat, registry). The exponent enters only as a loop
    count; every arithmetic step stays a machine operation.

    The record has the same shape as RunPlaygroundCartesianSweep's:
        Pair(DiscoveredInvariantLabel,
             Pair(modulus,
                  Pair(unary_image,
                       Pair(pair_sum_image, Pair(disjoint, EmptyList)))))
    """

    def __init__(self, bound_nat, mod_nat, power_nat, unary_pred, pair_pred, registry):
        self.registry = registry
        self.result = self._run(bound_nat, mod_nat, power_nat, unary_pred, pair_pred, registry)
        super().__init__(
            inputs=M.Pair(
                bound_nat,
                M.Pair(
                    mod_nat,
                    M.Pair(
                        power_nat,
                        M.Pair(unary_pred, M.Pair(pair_pred, M.Pair(registry, M.EmptyList))),
                    ),
                ),
            ),
            results=self.result,
        )

    def _run(self, bound_nat, mod_nat, power_nat, unary_pred, pair_pred, registry):
        # The exponent is read once, as a loop count only.
        power_rep = M.NatRepOf(power_nat, registry)()
        if M.IdentityCompare(power_rep, M.EmptyList)() is M.truth_value:
            raise TypeError("FilteredPowerSweep expects a Nat exponent")
        power_count = power_rep()

        # 1. Base domain: Zero for bound_nat steps.
        range_res = BuildNatRange(M.Zero, bound_nat, registry)()
        domain = M.Head(range_res)()
        reg1 = M.Head(M.Tail(range_res)())()

        one_res = M.NatFromRep(M.GMPRep(1), reg1)()
        one_nat = M.Head(one_res)()
        reg2 = M.Head(M.Tail(one_res)())()

        # Host-level memo of machine power computations, keyed on the element's
        # rep value: the same pattern as the kernel's NatValueIndex. Every
        # arithmetic step below is still a machine operation; only repeated
        # evaluation of x^k for a repeated x is avoided.
        power_memo = {}

        def power_value(x, reg):
            rep = M.NatRepOf(x, reg)()
            memo_key = None
            if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
                memo_key = rep()
            if memo_key is not None and memo_key in power_memo:
                return M.Pair(power_memo[memo_key], M.Pair(reg, M.EmptyList))
            # x^k by generic repeated multiplication, k a machine quantity.
            acc = one_nat
            cur_reg = reg
            for _ in range(power_count):
                mul_pair = A.Multiply(acc, x, cur_reg)()
                acc = M.Head(mul_pair)()
                cur_reg = M.Head(M.Tail(mul_pair)())()
            if memo_key is not None:
                power_memo[memo_key] = acc
            return M.Pair(acc, M.Pair(cur_reg, M.EmptyList))

        def power_of_head(tuple_args, reg):
            x = M.Head(tuple_args)()
            return power_value(x, reg)

        def power_sum(tuple_args, reg):
            x = M.Head(tuple_args)()
            y = M.Head(M.Tail(tuple_args)())()
            px_pair = power_value(x, reg)
            px = M.Head(px_pair)()
            r1 = M.Head(M.Tail(px_pair)())()
            py_pair = power_value(y, r1)
            py = M.Head(py_pair)()
            r2 = M.Head(M.Tail(py_pair)())()
            add_pair = A.Add(px, py, r2)()
            return M.Pair(M.Head(add_pair)(), M.Pair(M.Head(M.Tail(add_pair)())(), M.EmptyList))

        def unary_wrapper(tuple_args, reg):
            x = M.Head(tuple_args)()
            holds = unary_pred(x, reg)
            return M.Pair(holds, M.Pair(reg, M.EmptyList))

        def pair_wrapper(tuple_args, reg):
            x = M.Head(tuple_args)()
            y = M.Head(M.Tail(tuple_args)())()
            holds = pair_pred(x, y, reg)
            return M.Pair(holds, M.Pair(reg, M.EmptyList))

        # 2. Unary image over the filtered 1-ary domain.
        dom1 = ProductOfDomains(M.Pair(domain, M.EmptyList))()
        unary_tuples_res = FilterTuples(dom1, unary_wrapper, reg2)()
        unary_tuples = M.Head(unary_tuples_res)()
        reg3 = M.Head(M.Tail(unary_tuples_res)())()
        unary_map_res = MapDomain(unary_tuples, power_of_head, reg3)()
        unary_vals = M.Head(unary_map_res)()
        reg4 = M.Head(M.Tail(M.Tail(unary_map_res)())())()
        unary_proj_res = ProjectCongruence(unary_vals, mod_nat, reg4)()
        unary_image = M.Head(unary_proj_res)()
        reg5 = M.Head(M.Tail(unary_proj_res)())()

        # 3. Pair-sum image over the filtered 2-ary domain.
        dom2 = ProductOfDomains(M.Pair(domain, M.Pair(domain, M.EmptyList)))()
        pair_tuples_res = FilterTuples(dom2, pair_wrapper, reg5)()
        pair_tuples = M.Head(pair_tuples_res)()
        reg6 = M.Head(M.Tail(pair_tuples_res)())()
        pair_map_res = MapDomain(pair_tuples, power_sum, reg6)()
        pair_vals = M.Head(pair_map_res)()
        reg7 = M.Head(M.Tail(M.Tail(pair_map_res)())())()
        pair_proj_res = ProjectCongruence(pair_vals, mod_nat, reg7)()
        pair_image = M.Head(pair_proj_res)()
        reg8 = M.Head(M.Tail(pair_proj_res)())()

        # 4. Disjointness of the two images.
        disjoint_res = EvaluateSetRelation(unary_image, pair_image, reg8)()
        is_disjoint = M.Head(disjoint_res)()
        reg9 = M.Head(M.Tail(M.Tail(disjoint_res)())())()

        sweep_record = M.Pair(
            L.DiscoveredInvariantLabel,
            M.Pair(
                mod_nat,
                M.Pair(
                    unary_image,
                    M.Pair(pair_image, M.Pair(is_disjoint, M.EmptyList)),
                ),
            ),
        )
        return M.Pair(sweep_record, M.Pair(reg9, M.EmptyList))

    def __call__(self):
        return self.result


class DiscoverSeparatingModulus(M.Edge):
    """
    Run RunPlaygroundFilteredPowerSweep over an ordered chain of candidate
    moduli and return the record of the FIRST modulus whose unary and
    pair-sum images are disjoint, or EmptyList when none separates. The
    separating modulus is therefore a sweep result, never a constant a
    caller chose. Returns Pair(record_or_EmptyList, Pair(registry, EmptyList)).
    """

    def __init__(self, bound_nat, power_nat, unary_pred, pair_pred, moduli_chain, registry):
        self.registry = registry
        self.result = self._search(bound_nat, power_nat, unary_pred, pair_pred, moduli_chain, registry)
        super().__init__(
            inputs=M.Pair(
                bound_nat,
                M.Pair(
                    power_nat,
                    M.Pair(
                        unary_pred,
                        M.Pair(pair_pred, M.Pair(moduli_chain, M.Pair(registry, M.EmptyList))),
                    ),
                ),
            ),
            results=self.result,
        )

    def _search(self, bound_nat, power_nat, unary_pred, pair_pred, moduli_chain, registry):
        if M.IdentityCompare(moduli_chain, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        candidate = M.Head(moduli_chain)()
        sweep_res = RunPlaygroundFilteredPowerSweep(
            bound_nat, candidate, power_nat, unary_pred, pair_pred, registry
        )()
        record = M.Head(sweep_res)()
        reg1 = M.Head(M.Tail(sweep_res)())()
        disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
        if disjoint is M.truth_value:
            return M.Pair(record, M.Pair(reg1, M.EmptyList))
        return self._search(
            bound_nat, power_nat, unary_pred, pair_pred, M.Tail(moduli_chain)(), reg1
        )

    def __call__(self):
        return self.result


# ============================================================
# Polynomial identities and congruences, decided by evaluation
#
# Two generic decision procedures over the machine's own arithmetic. Neither
# names a theorem; each is parameterised by the expression terms it is handed
# and returns a record of exactly what was evaluated.
#
# Admitted expression fragment: a Char is a variable, a Nat is a constant,
# ExprInt(n) wraps a constant, ExprAdd(a, b), ExprMul(a, b), ExprPow(a, k)
# with k a Nat. Nothing else -- ExprNeg, ExprFrac and ExprDiv are refused,
# so every admitted term denotes a polynomial with natural coefficients and
# every claim below is a claim about polynomials over Z.
#
# PolynomialIdentityByGrid decides lhs = rhs as polynomials. It is sound by
# the finite-grid identity lemma: D = lhs - rhs has degree at most d_i in
# x_i (d_i read structurally from the terms); if D vanishes on a product
# S_1 x ... x S_k with |S_i| = d_i + 1 then D is the zero polynomial
# (induction on k: a nonzero univariate polynomial of degree <= d has at
# most d roots). So truth here is a proof of the identity for every natural
# (and integer) assignment, not evidence on a sample -- and the grid size is
# load-bearing: a smaller grid would prove nothing.
#
# ResidueTable / CongruenceClasses run an exhaustive residue case analysis.
# They are sound because reduction modulo m is a ring homomorphism, so a
# polynomial's residue at x_1..x_k depends only on the residues of the x_i;
# the m^k residue tuples decide the congruence for every natural assignment.
# ============================================================


def _expr_head_args(term):
    """Head and argument chain of an expression Pair, or (EmptyList, EmptyList)."""
    if M.IsPair(term)() is M.false_value:
        return M.EmptyList, M.EmptyList
    return M.Head(term)(), M.Tail(term)()


def _env_lookup(environment, variable):
    """Value bound to `variable` in a chain of Pair(var, Pair(value, [])), or EmptyList."""
    remaining = environment
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        entry = M.Head(remaining)()
        if M.Compare(M.Head(entry)(), variable)() is M.truth_value:
            return M.Head(M.Tail(entry)())()
        remaining = M.Tail(remaining)()
    return M.EmptyList


def _zip_environment(variables, values):
    """Chain of Pair(var, Pair(value, [])) from parallel chains."""
    if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    if M.IdentityCompare(values, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    entry = M.Pair(M.Head(variables)(), M.Pair(M.Head(values)(), M.EmptyList))
    return M.Pair(entry, _zip_environment(M.Tail(variables)(), M.Tail(values)()))


class ExprDegreeBound(M.Edge):
    """
    Structural upper bound on the degree of an admitted expression term in
    one variable: the variable itself has degree 1, any other atom 0,
    ExprAdd takes the larger bound, ExprMul the sum, ExprPow(a, k) k times
    the bound of a. The bound may exceed the true degree (cancellation is
    not tracked); it is never below it, which is all the grid needs.
    Result: Pair(degree_nat, Pair(registry, [])), or Pair([], ...) when the
    term lies outside the admitted fragment.
    """

    def __init__(self, term, variable, registry):
        self.registry = registry
        self.result = self._bound(term, variable, registry)
        super().__init__(
            inputs=M.Pair(term, M.Pair(variable, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _refuse(self, registry):
        return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

    def _bound(self, term, variable, registry):
        head, args = _expr_head_args(term)
        if M.IdentityCompare(head, M.EmptyList)() is M.truth_value:
            if A.IsNat(term, registry)() is M.truth_value:
                return M.Pair(M.Zero, M.Pair(registry, M.EmptyList))
            if M.Compare(term, variable)() is M.truth_value:
                return M.Pair(M.one, M.Pair(registry, M.EmptyList))
            return M.Pair(M.Zero, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            return M.Pair(M.Zero, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
            base_res = self._bound(M.Head(args)(), variable, registry)
            base_deg = M.Head(base_res)()
            reg1 = M.Head(M.Tail(base_res)())()
            exponent = M.Head(M.Tail(args)())()
            if M.IdentityCompare(base_deg, M.EmptyList)() is M.truth_value:
                return self._refuse(reg1)
            if A.IsNat(exponent, reg1)() is M.false_value:
                return self._refuse(reg1)
            return A.Multiply(exponent, base_deg, reg1)()
        is_add = M.IdentityCompare(head, L.ExprAddLabel)()
        is_mul = M.IdentityCompare(head, L.ExprMulLabel)()
        if M.OrAtom(is_add, is_mul)() is M.false_value:
            return self._refuse(registry)
        left_res = self._bound(M.Head(args)(), variable, registry)
        left_deg = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        if M.IdentityCompare(left_deg, M.EmptyList)() is M.truth_value:
            return self._refuse(reg1)
        right_res = self._bound(M.Head(M.Tail(args)())(), variable, reg1)
        right_deg = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        if M.IdentityCompare(right_deg, M.EmptyList)() is M.truth_value:
            return self._refuse(reg2)
        if is_mul is M.truth_value:
            return A.Add(left_deg, right_deg, reg2)()
        if M.NatLess(left_deg, right_deg, reg2)() is M.truth_value:
            return M.Pair(right_deg, M.Pair(reg2, M.EmptyList))
        return M.Pair(left_deg, M.Pair(reg2, M.EmptyList))

    def __call__(self):
        return self.result


class EvaluateNatExpr(M.Edge):
    """
    Evaluates an admitted expression term at an environment (a chain of
    Pair(variable, Pair(nat, []))) with the machine's own Add and Multiply;
    a power is repeated multiplication, its exponent read once as a loop
    count. Result: Pair(nat, Pair(registry, [])), or Pair([], ...) when the
    term is outside the fragment or a variable is unbound.
    """

    def __init__(self, term, environment, registry):
        self.registry = registry
        self.result = self._eval(term, environment, registry)
        super().__init__(
            inputs=M.Pair(term, M.Pair(environment, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _refuse(self, registry):
        return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

    def _eval(self, term, environment, registry):
        head, args = _expr_head_args(term)
        if M.IdentityCompare(head, M.EmptyList)() is M.truth_value:
            if A.IsNat(term, registry)() is M.truth_value:
                return M.Pair(term, M.Pair(registry, M.EmptyList))
            value = _env_lookup(environment, term)
            if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                return self._refuse(registry)
            return M.Pair(value, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            constant = M.Head(args)()
            if A.IsNat(constant, registry)() is M.false_value:
                return self._refuse(registry)
            return M.Pair(constant, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
            base_res = self._eval(M.Head(args)(), environment, registry)
            base = M.Head(base_res)()
            reg1 = M.Head(M.Tail(base_res)())()
            exponent = M.Head(M.Tail(args)())()
            if M.IdentityCompare(base, M.EmptyList)() is M.truth_value:
                return self._refuse(reg1)
            exponent_rep = M.NatRepOf(exponent, reg1)()
            if M.IdentityCompare(exponent_rep, M.EmptyList)() is M.truth_value:
                return self._refuse(reg1)
            count = exponent_rep()
            if count == 0:
                return M.Pair(M.one, M.Pair(reg1, M.EmptyList))
            acc = base
            cur_reg = reg1
            for _ in range(count - 1):
                mul_res = A.Multiply(acc, base, cur_reg)()
                acc = M.Head(mul_res)()
                cur_reg = M.Head(M.Tail(mul_res)())()
            return M.Pair(acc, M.Pair(cur_reg, M.EmptyList))
        is_add = M.IdentityCompare(head, L.ExprAddLabel)()
        is_mul = M.IdentityCompare(head, L.ExprMulLabel)()
        if M.OrAtom(is_add, is_mul)() is M.false_value:
            return self._refuse(registry)
        left_res = self._eval(M.Head(args)(), environment, registry)
        left = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return self._refuse(reg1)
        right_res = self._eval(M.Head(M.Tail(args)())(), environment, reg1)
        right = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            return self._refuse(reg2)
        if is_add is M.truth_value:
            return A.Add(left, right, reg2)()
        return A.Multiply(left, right, reg2)()

    def __call__(self):
        return self.result


class PolynomialIdentityByGrid(M.Edge):
    """
    Decides whether two admitted expression terms are equal as polynomials in
    the given variables, by evaluating both on the grid {0..d_1} x ... x
    {0..d_k}, d_i the larger structural degree bound of the two sides in
    x_i. Sound by the finite-grid identity lemma (see the section comment):
    verdict truth is a proof of the identity for all naturals, verdict false
    comes with every grid point where the sides differ -- the first is a
    counterexample. Verdict [] means a side was outside the fragment.

    Result: Pair(record, Pair(registry, [])) with
      record = Pair(PolynomialIdentityLabel,
                 Pair(lhs, Pair(rhs, Pair(variables, Pair(degree_chain,
                   Pair(grid_count, Pair(verdict, Pair(witness, []))))))))
      witness = the first grid point where the sides differ, else []
    """

    def __init__(self, lhs, rhs, variables, registry):
        self.registry = registry
        self.result = self._decide(lhs, rhs, variables, registry)
        super().__init__(
            inputs=M.Pair(lhs, M.Pair(rhs, M.Pair(variables, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _record(self, lhs, rhs, variables, degrees, grid_count, verdict, witness, registry):
        record = M.Pair(
            L.PolynomialIdentityLabel,
            M.Pair(lhs, M.Pair(rhs, M.Pair(variables, M.Pair(degrees, M.Pair(grid_count, M.Pair(verdict, M.Pair(witness, M.EmptyList))))))),
        )
        return M.Pair(record, M.Pair(registry, M.EmptyList))

    def _degrees(self, lhs, rhs, variables, registry):
        """Per-variable bounds (the larger of the two sides) and the matching
        grid domains {0..d}; refused (EmptyList flag) if a side lies outside
        the admitted fragment."""
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, M.truth_value, registry
        variable = M.Head(variables)()
        left_res = ExprDegreeBound(lhs, variable, registry)()
        left_deg = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        right_res = ExprDegreeBound(rhs, variable, reg1)()
        right_deg = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        if M.IdentityCompare(left_deg, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, M.false_value, reg2
        if M.IdentityCompare(right_deg, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, M.false_value, reg2
        degree = right_deg if M.NatLess(left_deg, right_deg, reg2)() is M.truth_value else left_deg
        count_res = A.Add(degree, M.one, reg2)()
        count = M.Head(count_res)()
        reg3 = M.Head(M.Tail(count_res)())()
        domain_res = BuildNatRange(M.Zero, count, reg3)()
        domain = M.Head(domain_res)()
        reg4 = M.Head(M.Tail(domain_res)())()
        rest_degrees, rest_domains, admitted, reg5 = self._degrees(lhs, rhs, M.Tail(variables)(), reg4)
        if admitted is M.false_value:
            return M.EmptyList, M.EmptyList, M.false_value, reg5
        return M.Pair(degree, rest_degrees), M.Pair(domain, rest_domains), M.truth_value, reg5

    def _decide(self, lhs, rhs, variables, registry):
        degrees, domains, admitted, reg1 = self._degrees(lhs, rhs, variables, registry)
        if admitted is M.false_value:
            return self._record(lhs, rhs, variables, M.EmptyList, M.Zero, M.EmptyList, M.EmptyList, reg1)
        tuples = ProductOfDomains(domains)()
        count_res = ChainLength(tuples, reg1)()
        grid_count = M.Head(count_res)()
        reg2 = M.Head(M.Tail(count_res)())()
        witness, reg3 = self._first_difference(lhs, rhs, variables, tuples, reg2)
        verdict = M.truth_value if M.IdentityCompare(witness, M.EmptyList)() is M.truth_value else M.false_value
        return self._record(lhs, rhs, variables, degrees, grid_count, verdict, witness, reg3)

    def _first_difference(self, lhs, rhs, variables, tuples, registry):
        """The first grid point where the sides differ (or a side fails to
        evaluate), or EmptyList when they agree everywhere. Stops at the
        first difference: one point refutes."""
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return M.EmptyList, registry
        point = M.Head(tuples)()
        environment = _zip_environment(variables, point)
        left_res = EvaluateNatExpr(lhs, environment, registry)()
        left = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        right_res = EvaluateNatExpr(rhs, environment, reg1)()
        right = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return point, reg2
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            return point, reg2
        if M.NatEq(left, right, reg2)() is M.false_value:
            return point, reg2
        return self._first_difference(lhs, rhs, variables, M.Tail(tuples)(), reg2)

    def __call__(self):
        return self.result


def _residue_domains(variables, modulus, registry):
    """One copy of {0..m-1} per variable."""
    if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
        return M.EmptyList, registry
    domain_res = BuildNatRange(M.Zero, modulus, registry)()
    domain = M.Head(domain_res)()
    reg1 = M.Head(M.Tail(domain_res)())()
    rest, reg2 = _residue_domains(M.Tail(variables)(), modulus, reg1)
    return M.Pair(domain, rest), reg2


class ResidueTable(M.Edge):
    """
    Exhaustive residue case analysis of one admitted expression term: for
    every residue tuple in {0..m-1}^k, the term's value modulo m (machine
    Modulo over machine evaluation). Sound for every natural assignment
    because reduction modulo m is a ring homomorphism.

    Result: Pair(record, Pair(registry, [])) with
      record = Pair(ResidueTableLabel,
                 Pair(term, Pair(variables, Pair(modulus,
                   Pair(rows, Pair(image, []))))))
      rows   = chain of Pair(residue_tuple, Pair(residue, [])), grid order
      image  = the set of residues that occur
    """

    def __init__(self, term, variables, modulus, registry):
        self.registry = registry
        self.result = self._table(term, variables, modulus, registry)
        super().__init__(
            inputs=M.Pair(term, M.Pair(variables, M.Pair(modulus, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _rows(self, term, variables, modulus, tuples, registry):
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, registry
        point = M.Head(tuples)()
        value_res = EvaluateNatExpr(term, _zip_environment(variables, point), registry)()
        value = M.Head(value_res)()
        reg1 = M.Head(M.Tail(value_res)())()
        if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
            residue = M.EmptyList
            reg2 = reg1
        else:
            residue_res = A.Modulo(value, modulus, reg1)()
            residue = M.Head(residue_res)()
            reg2 = M.Head(M.Tail(residue_res)())()
        rest_rows, rest_image, reg3 = self._rows(term, variables, modulus, M.Tail(tuples)(), reg2)
        image = rest_image if M.IdentityCompare(residue, M.EmptyList)() is M.truth_value else SetInsert(residue, rest_image, reg3)()
        return M.Pair(M.Pair(point, M.Pair(residue, M.EmptyList)), rest_rows), image, reg3

    def _table(self, term, variables, modulus, registry):
        domains, reg1 = _residue_domains(variables, modulus, registry)
        tuples = ProductOfDomains(domains)()
        rows, image, reg2 = self._rows(term, variables, modulus, tuples, reg1)
        record = M.Pair(
            L.ResidueTableLabel,
            M.Pair(term, M.Pair(variables, M.Pair(modulus, M.Pair(rows, M.Pair(image, M.EmptyList))))),
        )
        return M.Pair(record, M.Pair(reg2, M.EmptyList))

    def __call__(self):
        return self.result


class CongruenceClasses(M.Edge):
    """
    Exhaustive residue case analysis of a polynomial congruence
    lhs = rhs (mod m): the residue tuples in {0..m-1}^k at which the two
    sides agree modulo m, and those at which they differ. Sound and complete
    for every natural assignment, for the same reason as ResidueTable; the
    holding chain is therefore the full solution set of the congruence
    described class by class, and an empty holding chain refutes it.

    Result: Pair(record, Pair(registry, [])) with
      record = Pair(CongruenceClassesLabel,
                 Pair(lhs, Pair(rhs, Pair(variables, Pair(modulus,
                   Pair(holding, Pair(failing, [])))))))
    """

    def __init__(self, lhs, rhs, variables, modulus, registry):
        self.registry = registry
        self.result = self._classes(lhs, rhs, variables, modulus, registry)
        super().__init__(
            inputs=M.Pair(lhs, M.Pair(rhs, M.Pair(variables, M.Pair(modulus, M.Pair(registry, M.EmptyList))))),
            results=self.result,
        )

    def _classes(self, lhs, rhs, variables, modulus, registry):
        domains, reg1 = _residue_domains(variables, modulus, registry)
        tuples = ProductOfDomains(domains)()
        holding, failing, reg2 = self._partition(lhs, rhs, variables, modulus, tuples, reg1)
        record = M.Pair(
            L.CongruenceClassesLabel,
            M.Pair(lhs, M.Pair(rhs, M.Pair(variables, M.Pair(modulus, M.Pair(holding, M.Pair(failing, M.EmptyList)))))),
        )
        return M.Pair(record, M.Pair(reg2, M.EmptyList))

    def _partition(self, lhs, rhs, variables, modulus, tuples, registry):
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, registry
        point = M.Head(tuples)()
        environment = _zip_environment(variables, point)
        left_res = EvaluateNatExpr(lhs, environment, registry)()
        left = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        right_res = EvaluateNatExpr(rhs, environment, reg1)()
        right = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        holds = M.false_value
        if M.IdentityCompare(left, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(right, M.EmptyList)() is M.false_value:
                left_mod = A.Modulo(left, modulus, reg2)()
                reg2 = M.Head(M.Tail(left_mod)())()
                right_mod = A.Modulo(right, modulus, reg2)()
                reg2 = M.Head(M.Tail(right_mod)())()
                holds = M.NatEq(M.Head(left_mod)(), M.Head(right_mod)(), reg2)()
        rest_holding, rest_failing, reg3 = self._partition(lhs, rhs, variables, modulus, M.Tail(tuples)(), reg2)
        if holds is M.truth_value:
            return M.Pair(point, rest_holding), rest_failing, reg3
        return rest_holding, M.Pair(point, rest_failing), reg3

    def __call__(self):
        return self.result


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
    "RunPlaygroundFilteredPowerSweep",
    "DiscoverSeparatingModulus",
    "EvaluateOperationTensor",
    "ExprDegreeBound",
    "EvaluateNatExpr",
    "PolynomialIdentityByGrid",
    "ResidueTable",
    "CongruenceClasses",
    "run_playground_interactive",
)
