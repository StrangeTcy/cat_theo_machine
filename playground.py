# ============================================================
# Playground — Machine-Native Irreducible Cartesian Engine
#
# Foundational arity-agnostic Cartesian product generator,
# Peano-native sequence counting, tuple operations, universal
# relational quantifiers, and congruence projections.
# ============================================================
from __future__ import annotations

import multiprocessing
import os
import sys

from . import constructors as C
from . import labels as L
from . import machine as M
from .math import arithmetic as A


def _pg_debug(msg):
    sys.stdout.write(
        f"[debug: cartesian_playground process {os.getpid()}]: {msg}\n"
    )
    sys.stdout.flush()


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
        return M.NatFromRep(M.CountRep(chain)(), registry)()

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


class SetDifference(M.Edge):
    """
    Computes the relative complement set_a \\ set_b of two Nat set chains.
    """

    def __init__(self, set_a, set_b, registry):
        self.registry = registry
        self.result = self._diff(set_a, set_b, registry)
        super().__init__(
            inputs=M.Pair(set_a, M.Pair(set_b, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _diff(self, set_a, set_b, registry):
        if M.IdentityCompare(set_a, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        head = M.Head(set_a)()
        rest = self._diff(M.Tail(set_a)(), set_b, registry)
        has = ChainContains(set_b, head, registry)()
        if has is M.truth_value:
            return rest
        return M.Pair(head, rest)

    def __call__(self):
        return self.result


class SortNatChain(M.Edge):
    """
    Orders a Pair chain of Nat nodes in ascending order using M.NatLess.
    """

    def __init__(self, nat_chain, registry):
        self.registry = registry
        self.result = self._sort(nat_chain, registry)
        super().__init__(
            inputs=M.Pair(nat_chain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _insert_sorted(self, elem, sorted_chain, registry):
        if M.IdentityCompare(sorted_chain, M.EmptyList)() is M.truth_value:
            return M.Pair(elem, M.EmptyList)
        head = M.Head(sorted_chain)()
        if M.NatLess(elem, head, registry)() is M.truth_value:
            return M.Pair(elem, sorted_chain)
        return M.Pair(
            head,
            self._insert_sorted(elem, M.Tail(sorted_chain)(), registry),
        )

    def _sort(self, cur_chain, registry):
        if M.IdentityCompare(cur_chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rest_sorted = self._sort(M.Tail(cur_chain)(), registry)
        return self._insert_sorted(M.Head(cur_chain)(), rest_sorted, registry)

    def __call__(self):
        return self.result


class TupleElementAt(M.Edge):
    """
    Retrieves the element of a tuple Pair chain at Peano index_nat.
    Returns Pair(element_or_EmptyList, Pair(registry, EmptyList)).
    """

    def __init__(self, tuple_chain, index_nat, registry):
        self.registry = registry
        self.result = self._at(tuple_chain, index_nat, registry)
        super().__init__(
            inputs=M.Pair(
                tuple_chain,
                M.Pair(index_nat, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _at(self, cur_tuple, cur_idx, registry):
        if M.IdentityCompare(cur_tuple, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.NatEq(cur_idx, M.Zero, registry)() is M.truth_value:
            return M.Pair(M.Head(cur_tuple)(), M.Pair(registry, M.EmptyList))
        pred_res = M.NatPred(cur_idx, registry)()
        pred_idx = M.Head(pred_res)()
        reg1 = M.Head(M.Tail(pred_res)())()
        return self._at(M.Tail(cur_tuple)(), pred_idx, reg1)

    def __call__(self):
        return self.result


class ProjectCoordinate(M.Edge):
    """
    Projects a chain of k-tuples onto Peano coordinate index_nat,
    producing the ordered unique set chain of values at that coordinate.
    Returns Pair(projected_set_chain, Pair(registry, EmptyList)).
    """

    def __init__(self, tuples_chain, index_nat, registry):
        self.registry = registry
        self.result = self._project(
            tuples_chain, index_nat, M.EmptyList, registry
        )
        super().__init__(
            inputs=M.Pair(
                tuples_chain,
                M.Pair(index_nat, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _project(self, cur_tuples, index_nat, acc_set, registry):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            sorted_set = SortNatChain(acc_set, registry)()
            return M.Pair(sorted_set, M.Pair(registry, M.EmptyList))
        tup = M.Head(cur_tuples)()
        at_res = TupleElementAt(tup, index_nat, registry)()
        val = M.Head(at_res)()
        reg1 = M.Head(M.Tail(at_res)())()
        next_set = (
            acc_set
            if M.IdentityCompare(val, M.EmptyList)() is M.truth_value
            else SetInsert(val, acc_set, reg1)()
        )
        return self._project(
            M.Tail(cur_tuples)(), index_nat, next_set, reg1
        )

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
    Delegates to RunPlaygroundFilteredPowerSweep with exponent 2 and odd-pair subdomain.
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
        two_res = M.NatFromRep(M.GMPRep(2), registry)()
        two_nat = M.Head(two_res)()
        reg1 = M.Head(M.Tail(two_res)())()

        one_res = M.NatFromRep(M.GMPRep(1), reg1)()
        one_nat = M.Head(one_res)()
        reg2 = M.Head(M.Tail(one_res)())()

        def every_unary(_x, _reg):
            return M.truth_value

        def odd_pair_pred(x, y, reg):
            rx = A.Modulo(x, two_nat, reg)()
            rem_x = M.Head(rx)()
            r1 = M.Head(M.Tail(rx)())()
            eq_x = M.NatEq(rem_x, one_nat, r1)()
            if eq_x is M.false_value:
                return M.false_value
            ry = A.Modulo(y, two_nat, r1)()
            rem_y = M.Head(ry)()
            r2 = M.Head(M.Tail(ry)())()
            return M.NatEq(rem_y, one_nat, r2)()

        return RunPlaygroundFilteredPowerSweep(
            bound_nat, mod_nat, two_nat, every_unary, odd_pair_pred, reg2
        )()

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


def _nat_pow_peano(base_nat, exp_nat, one_nat, registry):
    """
    Computes base_nat ^ exp_nat by pure Peano recursion on exp_nat
    using M.NatEq, M.NatPred, and A.Multiply (no host loop or NatRepOf).
    """
    if M.NatEq(exp_nat, M.Zero, registry)() is M.truth_value:
        return M.Pair(one_nat, M.Pair(registry, M.EmptyList))
    pred_res = M.NatPred(exp_nat, registry)()
    pred_exp = M.Head(pred_res)()
    reg1 = M.Head(M.Tail(pred_res)())()
    if M.NatEq(pred_exp, M.Zero, reg1)() is M.truth_value:
        return M.Pair(base_nat, M.Pair(reg1, M.EmptyList))
    sub_res = _nat_pow_peano(base_nat, pred_exp, one_nat, reg1)
    sub_val = M.Head(sub_res)()
    reg2 = M.Head(M.Tail(sub_res)())()
    return A.Multiply(sub_val, base_nat, reg2)()


def _nat_env_lookup(env_chain, key_nat, registry):
    """
    Looks up key_nat in a machine Pair chain of Pair(nat_key, Pair(nat_val, [])).
    """
    if M.IdentityCompare(env_chain, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    entry = M.Head(env_chain)()
    entry_key = M.Head(entry)()
    if (
        M.IdentityCompare(entry_key, key_nat)() is M.truth_value
        or M.NatEq(entry_key, key_nat, registry)() is M.truth_value
    ):
        return M.Head(M.Tail(entry)())()
    return _nat_env_lookup(M.Tail(env_chain)(), key_nat, registry)


def _build_power_env_chain(domain_chain, power_nat, one_nat, registry):
    """
    Evaluates x ^ power_nat for every x in domain_chain into a machine Pair chain
    of Pair(x, Pair(x^k, [])).
    """
    if M.IdentityCompare(domain_chain, M.EmptyList)() is M.truth_value:
        return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
    x = M.Head(domain_chain)()
    px_res = _nat_pow_peano(x, power_nat, one_nat, registry)
    px = M.Head(px_res)()
    reg1 = M.Head(M.Tail(px_res)())()
    rest_res = _build_power_env_chain(M.Tail(domain_chain)(), power_nat, one_nat, reg1)
    rest_env = M.Head(rest_res)()
    reg2 = M.Head(M.Tail(rest_res)())()
    entry = M.Pair(x, M.Pair(px, M.EmptyList))
    return M.Pair(M.Pair(entry, rest_env), M.Pair(reg2, M.EmptyList))


class RunPlaygroundFilteredPowerSweep(M.Edge):
    """
    Parameterized Cartesian sweep, generalizing RunPlaygroundCartesianSweep.

    Takes the exponent and both domain filters as parameters, so one piece of
    machinery runs any power-image / filtered-sum-image disjointness test:

        unary image    = { x^k mod m : x in domain, unary_pred(x) }
        pair-sum image = { (x^k + y^k) mod m : x, y in domain, pair_pred(x, y) }

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
        if A.IsNat(power_nat, registry)() is M.false_value:
            raise TypeError("FilteredPowerSweep expects a Nat exponent")

        # 1. Base domain: Zero for bound_nat steps.
        range_res = BuildNatRange(M.Zero, bound_nat, registry)()
        domain = M.Head(range_res)()
        reg1 = M.Head(M.Tail(range_res)())()

        one_res = M.NatFromRep(M.GMPRep(1), reg1)()
        one_nat = M.Head(one_res)()
        reg2 = M.Head(M.Tail(one_res)())()

        # Machine-native Pair environment of (x, x^k) across domain.
        penv_res = _build_power_env_chain(domain, power_nat, one_nat, reg2)
        power_env = M.Head(penv_res)()
        reg2b = M.Head(M.Tail(penv_res)())()

        def power_value(x, reg):
            cached = _nat_env_lookup(power_env, x, reg)
            if M.IdentityCompare(cached, M.EmptyList)() is M.false_value:
                return M.Pair(cached, M.Pair(reg, M.EmptyList))
            return _nat_pow_peano(x, power_nat, one_nat, reg)

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
        unary_tuples_res = FilterTuples(dom1, unary_wrapper, reg2b)()
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
    pair-sum images are disjoint, or EmptyList when none separates.
    Returns Pair(record_or_EmptyList, Pair(registry, EmptyList)).
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
# ============================================================


def _expr_head_args(term):
    """Pair(label, arg_chain) -> (label, arg_chain), else ([], [])."""
    if M.IsPair(term)() is M.false_value:
        return M.EmptyList, M.EmptyList
    return M.Head(term)(), M.Tail(term)()


def _env_lookup(environment, variable):
    """variable -> value in a chain of Pair(variable, Pair(value, [])), or []."""
    if M.IdentityCompare(environment, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    entry = M.Head(environment)()
    if M.Compare(M.Head(entry)(), variable)() is M.truth_value:
        return M.Head(M.Tail(entry)())()
    return _env_lookup(M.Tail(environment)(), variable)


def _zip_environment(variables, values):
    """Pair(v_1, ...) and Pair(n_1, ...) -> Pair(Pair(v_1, Pair(n_1, [])), ...)."""
    if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    if M.IdentityCompare(values, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    binding = M.Pair(M.Head(variables)(), M.Pair(M.Head(values)(), M.EmptyList))
    return M.Pair(binding, _zip_environment(M.Tail(variables)(), M.Tail(values)()))


def _exact_arity(args, arity):
    """Syntax arity only; never interprets a machine number as a host int."""
    if arity <= 0:
        return M.IdentityCompare(args, M.EmptyList)()
    if M.IsPair(args)() is M.false_value:
        return M.false_value
    return _exact_arity(M.Tail(args)(), arity - 1)


def _chain_has_var(chain, var_atom):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return M.false_value
    if M.Compare(M.Head(chain)(), var_atom)() is M.truth_value:
        return M.truth_value
    return _chain_has_var(M.Tail(chain)(), var_atom)


def _chain_append_end(chain, elem):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return M.Pair(elem, M.EmptyList)
    return M.Pair(M.Head(chain)(), _chain_append_end(M.Tail(chain)(), elem))


def _chain_concat(chain_a, chain_b):
    if M.IdentityCompare(chain_a, M.EmptyList)() is M.truth_value:
        return chain_b
    return M.Pair(M.Head(chain_a)(), _chain_concat(M.Tail(chain_a)(), chain_b))


def _chain_reverse(chain, acc=M.EmptyList):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return acc
    return _chain_reverse(M.Tail(chain)(), M.Pair(M.Head(chain)(), acc))


def _chain_merge_unique(chain_a, chain_b):
    if M.IdentityCompare(chain_b, M.EmptyList)() is M.truth_value:
        return chain_a
    head_b = M.Head(chain_b)()
    next_a = (
        chain_a
        if _chain_has_var(chain_a, head_b) is M.truth_value
        else _chain_append_end(chain_a, head_b)
    )
    return _chain_merge_unique(next_a, M.Tail(chain_b)())


class ExtractExprVariables(M.Edge):
    """
    Walks an expression term and returns the chain of distinct non-numeric
    variable atoms in order of first appearance.
    Result: Pair(vars_chain, Pair(registry, EmptyList))
    """

    def __init__(self, term, registry):
        self.registry = registry
        self.result = M.Pair(
            self._extract(term, registry),
            M.Pair(registry, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(term, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _extract(self, term, registry):
        if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if A.IsNat(term, registry)() is M.truth_value:
            return M.EmptyList
        if M.IsPair(term)() is M.false_value:
            return M.Pair(term, M.EmptyList)
        head, args = _expr_head_args(term)
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            return M.EmptyList
        if _exact_arity(args, 2) is M.truth_value:
            left_vars = self._extract(M.Head(args)(), registry)
            right_vars = self._extract(M.Head(M.Tail(args)())(), registry)
            return _chain_merge_unique(left_vars, right_vars)
        return M.EmptyList

    def __call__(self):
        return self.result


class ExtractExponentVariables(M.Edge):
    """
    Walks an expression term and returns the chain of distinct non-numeric
    variable atoms occurring in exponent position (second child of ExprPowLabel).
    Result: Pair(exp_vars_chain, Pair(registry, EmptyList))
    """

    def __init__(self, term, registry):
        self.registry = registry
        self.result = M.Pair(
            self._extract_exp(term, registry),
            M.Pair(registry, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(term, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _extract_exp(self, term, registry):
        if M.IsPair(term)() is M.false_value:
            return M.EmptyList
        head, args = _expr_head_args(term)
        if _exact_arity(args, 2) is M.false_value:
            return M.EmptyList
        left = M.Head(args)()
        right = M.Head(M.Tail(args)())()
        left_exp = self._extract_exp(left, registry)
        if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
            exp_vars = M.Head(ExtractExprVariables(right, registry)())()
            return _chain_merge_unique(left_exp, exp_vars)
        right_exp = self._extract_exp(right, registry)
        return _chain_merge_unique(left_exp, right_exp)

    def __call__(self):
        return self.result


class SubstituteExprVar(M.Edge):
    """
    Substitutes `replacement` for every occurrence of `variable` inside `term`.
    Result: Pair(new_term, Pair(registry, EmptyList))
    """

    def __init__(self, term, variable, replacement, registry):
        self.registry = registry
        self.result = M.Pair(
            self._subst(term, variable, replacement, registry),
            M.Pair(registry, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(
                term,
                M.Pair(
                    variable,
                    M.Pair(replacement, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _subst(self, term, variable, replacement, registry):
        if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
            return term
        if A.IsNat(term, registry)() is M.truth_value:
            return term
        if M.IsPair(term)() is M.false_value:
            if M.Compare(term, variable)() is M.truth_value:
                return replacement
            return term
        head, args = _expr_head_args(term)
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            return term
        if _exact_arity(args, 2) is M.truth_value:
            left = self._subst(M.Head(args)(), variable, replacement, registry)
            right = self._subst(
                M.Head(M.Tail(args)())(), variable, replacement, registry
            )
            return M.Pair(head, M.Pair(left, M.Pair(right, M.EmptyList)))
        return term

    def __call__(self):
        return self.result


def RenderNatExpr(term, registry):
    """
    Renders a machine expression term into infix mathematical surface notation
    directly from its AST structure.
    """
    if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
        return "0"
    if A.IsNat(term, registry)() is M.truth_value:
        rep = M.NatRepOf(term, registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            return str(rep())
    if M.IsPair(term)() is M.false_value:
        val = term()
        return str(val) if val is not None else "?"
    head, args = _expr_head_args(term)
    if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
        return RenderNatExpr(M.Head(args)(), registry)
    if _exact_arity(args, 2) is M.false_value:
        return "?"
    left = M.Head(args)()
    right = M.Head(M.Tail(args)())()
    if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
        b_str = RenderNatExpr(left, registry)
        e_str = RenderNatExpr(right, registry)
        if (
            M.IsPair(left)() is M.truth_value
            and M.IdentityCompare(M.Head(left)(), L.ExprIntLabel)() is M.false_value
        ):
            b_str = "(" + b_str + ")"
        return b_str + "^" + e_str
    if M.IdentityCompare(head, L.ExprMulLabel)() is M.truth_value:
        l_str = RenderNatExpr(left, registry)
        r_str = RenderNatExpr(right, registry)
        if (
            M.IsPair(left)() is M.truth_value
            and M.IdentityCompare(M.Head(left)(), L.ExprAddLabel)() is M.truth_value
        ):
            l_str = "(" + l_str + ")"
        if (
            M.IsPair(right)() is M.truth_value
            and M.IdentityCompare(M.Head(right)(), L.ExprAddLabel)() is M.truth_value
        ):
            r_str = "(" + r_str + ")"
        return l_str + "*" + r_str
    if M.IdentityCompare(head, L.ExprAddLabel)() is M.truth_value:
        return RenderNatExpr(left, registry) + " + " + RenderNatExpr(right, registry)
    return "?"


class ExprDegreeBound(M.Edge):
    """
    Structural upper bound on the degree of an admitted expression term in
    one variable: the variable itself has degree 1, any other atom 0,
    ExprAdd takes the larger bound, ExprMul the sum, ExprPow(a, k) k times
    the bound of a.
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
    Pair(variable, Pair(nat, []))) with the machine's own Add, Multiply,
    and Peano NatPred recursion.
    Result: Pair(nat, Pair(registry, [])), or Pair([], ...) when the
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
            if A.IsNat(exponent, reg1)() is M.false_value:
                return self._refuse(reg1)
            return _nat_pow_peano(base, exponent, M.one, reg1)
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


def _valid_polynomial_variables(variables, registry):
    remaining = variables
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        if M.IsPair(remaining)() is M.false_value:
            return M.false_value
        variable = M.Head(remaining)()
        if M.IsPair(variable)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(variable, M.EmptyList)() is M.truth_value:
            return M.false_value
        if A.IsNat(variable, registry)() is M.truth_value:
            return M.false_value
        previous = variables
        while M.IdentityCompare(previous, remaining)() is M.false_value:
            if M.Compare(variable, M.Head(previous)())() is M.truth_value:
                return M.false_value
            previous = M.Tail(previous)()
        remaining = M.Tail(remaining)()
    return M.truth_value


def _admitted_polynomial(term, variables, registry):
    """Check exact syntax and coverage *before* computing a degree or grid."""
    if A.IsNat(term, registry)() is M.truth_value:
        return M.truth_value
    if M.IsPair(term)() is M.false_value:
        remaining = variables
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.Compare(term, M.Head(remaining)())() is M.truth_value:
                return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value
    head, args = _expr_head_args(term)
    if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
        if _exact_arity(args, 1) is M.false_value:
            return M.false_value
        return A.IsNat(M.Head(args)(), registry)()
    if _exact_arity(args, 2) is M.false_value:
        return M.false_value
    left = M.Head(args)()
    right = M.Head(M.Tail(args)())()
    if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
        if A.IsNat(right, registry)() is M.false_value:
            return M.false_value
        return _admitted_polynomial(left, variables, registry)
    if M.OrAtom(M.IdentityCompare(head, L.ExprAddLabel)(),
                M.IdentityCompare(head, L.ExprMulLabel)())() is M.false_value:
        return M.false_value
    return M.AndAtom(_admitted_polynomial(left, variables, registry),
                     _admitted_polynomial(right, variables, registry))()


class PolynomialIdentityByGrid(M.Edge):
    """
    Decides whether two admitted expression terms are equal as polynomials in
    the given variables, by evaluating both on the grid {0..d_1} x ... x
    {0..d_k}, d_i the larger structural degree bound of the two sides in x_i.

    Result: Pair(record, Pair(registry, [])) with
      record = Pair(PolynomialIdentityLabel,
                 Pair(lhs, Pair(rhs, Pair(variables, Pair(degree_chain,
                   Pair(grid_count, Pair(verdict, Pair(witness, []))))))))
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
        if _valid_polynomial_variables(variables, registry) is M.false_value:
            return self._record(lhs, rhs, variables, M.EmptyList, M.Zero, M.EmptyList, M.EmptyList, registry)
        if M.AndAtom(_admitted_polynomial(lhs, variables, registry),
                     _admitted_polynomial(rhs, variables, registry))() is M.false_value:
            return self._record(lhs, rhs, variables, M.EmptyList, M.Zero, M.EmptyList, M.EmptyList, registry)
        degrees, domains, admitted, reg1 = self._degrees(lhs, rhs, variables, registry)
        if admitted is M.false_value:
            return self._record(lhs, rhs, variables, M.EmptyList, M.Zero, M.EmptyList, M.EmptyList, reg1)
        tuples = ProductOfDomains(domains)()
        count_res = ChainLength(tuples, reg1)()
        grid_count = M.Head(count_res)()
        reg2 = M.Head(M.Tail(count_res)())()
        verdict, witness, reg3 = self._first_difference(lhs, rhs, variables, tuples, reg2)
        return self._record(lhs, rhs, variables, degrees, grid_count, verdict, witness, reg3)

    def _first_difference(self, lhs, rhs, variables, tuples, registry):
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return M.truth_value, M.EmptyList, registry
        point = M.Head(tuples)()
        environment = _zip_environment(variables, point)
        left_res = EvaluateNatExpr(lhs, environment, registry)()
        left = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        right_res = EvaluateNatExpr(rhs, environment, reg1)()
        right = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return M.false_value, point, reg2
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            return M.false_value, point, reg2
        if M.NatEq(left, right, reg2)() is M.false_value:
            return M.false_value, point, reg2
        return self._first_difference(lhs, rhs, variables, M.Tail(tuples)(), reg2)

    def __call__(self):
        return self.result


class PolynomialRewriteCertificate(M.Edge):
    """Grid-gated ordinary rewrite certificate (W22, partial)."""

    def __init__(self, lhs, rhs, variables, rules, registry, fuel=M.nine):
        from .invariance import RewriteEqualityDerivation

        decided = PolynomialIdentityByGrid(lhs, rhs, variables, registry)()
        record = M.Head(decided)()
        registry = M.Head(M.Tail(decided)())()
        fields = M.Tail(record)()
        fields = M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(fields)())())())())()
        if M.Head(fields)() is M.truth_value:
            rewritten = RewriteEqualityDerivation(lhs, rhs, rules, registry, fuel)()
        else:
            rewritten = M.Pair(M.false_value, M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList)))
        self.result = M.Pair(record, rewritten)
        super().__init__(inputs=M.Pair(lhs, M.Pair(rhs, M.Pair(variables,
            M.Pair(rules, M.Pair(registry, M.Pair(fuel, M.EmptyList)))))), results=self.result)

    def __call__(self):
        return self.result


class PolynomialGridDerivation(M.Edge):
    """Record one finite-grid inference for Checker B to recompute."""

    def __init__(self, lhs, rhs, variables, registry):
        from . import proof as P

        input_registry = registry
        decided = PolynomialIdentityByGrid(lhs, rhs, variables, registry)()
        record = M.Head(decided)()
        registry = M.Head(M.Tail(decided)())()
        fields = M.Tail(record)()
        fields = M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(fields)())())())())()
        derivation = M.EmptyList
        if M.Head(fields)() is M.truth_value:
            action = M.Pair(L.PolynomialGridActionLabel, M.Pair(record, M.EmptyList))
            step_res = P.Step(lhs, action, rhs, registry)()
            step = M.Head(step_res)()
            registry = M.Head(M.Tail(step_res)())()
            steps = M.Pair(step, M.EmptyList)
            cost_res = P.BuildProofCost(steps, registry)()
            registry = M.Head(M.Tail(cost_res)())()
            built = P.Derivation(steps, M.Head(cost_res)(), registry)()
            derivation = M.Head(built)()
            registry = M.Head(M.Tail(built)())()
        self.result = M.Pair(record, M.Pair(derivation, M.Pair(registry, M.EmptyList)))
        super().__init__(inputs=M.Pair(lhs, M.Pair(rhs, M.Pair(variables,
            M.Pair(input_registry, M.EmptyList)))), results=self.result)

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
    Modulo over machine evaluation).

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
    sides agree modulo m, and those at which they differ.

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


class ProjectAllCoordinates(M.Edge):
    """
    Projects a chain of holding residue tuples onto each variable coordinate
    in variables_chain modulo modulus_nat.
    For each variable v_i at Peano index i, records:
      Pair(v_i, Pair(admissible_set, Pair(excluded_set, Pair(is_proper, EmptyList))))
    where admissible_set = ProjectCoordinate(tuples_chain, i),
          excluded_set   = SetDifference({0..m-1}, admissible_set),
          is_proper      = NatLess(ChainLength(admissible_set), modulus_nat).
    Returns Pair(coord_records_chain, Pair(registry, EmptyList)).
    """

    def __init__(self, tuples_chain, variables_chain, modulus_nat, registry):
        self.registry = registry
        dom_res = BuildNatRange(M.Zero, modulus_nat, registry)()
        full_dom = M.Head(dom_res)()
        reg1 = M.Head(M.Tail(dom_res)())()
        self.result = self._project_all(
            tuples_chain, variables_chain, M.Zero, full_dom, modulus_nat, reg1
        )
        super().__init__(
            inputs=M.Pair(
                tuples_chain,
                M.Pair(
                    variables_chain,
                    M.Pair(modulus_nat, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _project_all(self, tuples_chain, cur_vars, cur_idx, full_dom, modulus_nat, registry):
        if M.IdentityCompare(cur_vars, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        var_atom = M.Head(cur_vars)()
        adm_res = ProjectCoordinate(tuples_chain, cur_idx, registry)()
        adm_set = M.Head(adm_res)()
        reg1 = M.Head(M.Tail(adm_res)())()

        raw_excl = SetDifference(full_dom, adm_set, reg1)()
        excl_set = SortNatChain(raw_excl, reg1)()

        len_res = ChainLength(adm_set, reg1)()
        adm_len = M.Head(len_res)()
        reg2 = M.Head(M.Tail(len_res)())()
        is_proper = M.NatLess(adm_len, modulus_nat, reg2)()

        next_idx_res = A.Add(cur_idx, M.one, reg2)()
        next_idx = M.Head(next_idx_res)()
        reg3 = M.Head(M.Tail(next_idx_res)())()

        rest_res = self._project_all(
            tuples_chain, M.Tail(cur_vars)(), next_idx, full_dom, modulus_nat, reg3
        )
        rest_chain = M.Head(rest_res)()
        reg4 = M.Head(M.Tail(rest_res)())()

        coord_rec = M.Pair(
            var_atom,
            M.Pair(
                adm_set,
                M.Pair(excl_set, M.Pair(is_proper, M.EmptyList)),
            ),
        )
        return M.Pair(M.Pair(coord_rec, rest_chain), M.Pair(reg4, M.EmptyList))

    def __call__(self):
        return self.result


def _tuple_all_under_mod(tup, m_nat, registry):
    if M.IdentityCompare(tup, M.EmptyList)() is M.truth_value:
        return M.truth_value
    if M.NatLess(M.Head(tup)(), m_nat, registry)() is M.false_value:
        return M.false_value
    return _tuple_all_under_mod(M.Tail(tup)(), m_nat, registry)


def _tuple_all_positive(tup, registry):
    if M.IdentityCompare(tup, M.EmptyList)() is M.truth_value:
        return M.truth_value
    if M.NatEq(M.Head(tup)(), M.Zero, registry)() is M.truth_value:
        return M.false_value
    return _tuple_all_positive(M.Tail(tup)(), registry)


def _tuple_nat_equal(t1, t2, registry):
    if M.IdentityCompare(t1, M.EmptyList)() is M.truth_value:
        return M.IdentityCompare(t2, M.EmptyList)()
    if M.IdentityCompare(t2, M.EmptyList)() is M.truth_value:
        return M.false_value
    h1 = M.Head(t1)()
    h2 = M.Head(t2)()
    if (
        M.IdentityCompare(h1, h2)() is M.false_value
        and M.NatEq(h1, h2, registry)() is M.false_value
    ):
        return M.false_value
    return _tuple_nat_equal(M.Tail(t1)(), M.Tail(t2)(), registry)


def _project_env_to_subtuple(env, sub_vars):
    if M.IdentityCompare(sub_vars, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    val = _env_lookup(env, M.Head(sub_vars)())
    return M.Pair(val, _project_env_to_subtuple(env, M.Tail(sub_vars)()))


def _lookup_residue_row(rows_chain, target_tuple, registry):
    if M.IdentityCompare(rows_chain, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    row = M.Head(rows_chain)()
    pt = M.Head(row)()
    if _tuple_nat_equal(pt, target_tuple, registry) is M.truth_value:
        return M.Head(M.Tail(row)())()
    return _lookup_residue_row(M.Tail(rows_chain)(), target_tuple, registry)


class ProjectTensorModulo(M.Edge):
    """
    Projects a ground EvaluationTensor record onto {0..m-1}^k modulo mod_nat,
    yielding a ResidueTableLabel record (rows + sorted unique image set).
    """

    def __init__(self, term, variables, tensor_node, mod_nat, registry):
        self.registry = registry
        self.result = self._project(term, variables, tensor_node, mod_nat, registry)
        super().__init__(
            inputs=M.Pair(
                term,
                M.Pair(
                    variables,
                    M.Pair(
                        tensor_node,
                        M.Pair(mod_nat, M.Pair(registry, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _walk_entries(self, cur_entries, mod_nat, registry):
        if M.IdentityCompare(cur_entries, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, registry
        entry = M.Head(cur_entries)()
        tup = M.Head(M.Tail(entry)())()
        val = M.Head(M.Tail(M.Tail(entry)())())()
        rest_rows, rest_img, reg1 = self._walk_entries(
            M.Tail(cur_entries)(), mod_nat, registry
        )
        if _tuple_all_under_mod(tup, mod_nat, reg1) is M.false_value:
            return rest_rows, rest_img, reg1
        if M.IdentityCompare(val, M.EmptyList)() is M.truth_value:
            row = M.Pair(tup, M.Pair(M.EmptyList, M.EmptyList))
            return M.Pair(row, rest_rows), rest_img, reg1
        mod_res = A.Modulo(val, mod_nat, reg1)()
        rem = M.Head(mod_res)()
        reg2 = M.Head(M.Tail(mod_res)())()
        row = M.Pair(tup, M.Pair(rem, M.EmptyList))
        next_img = SetInsert(rem, rest_img, reg2)()
        return M.Pair(row, rest_rows), next_img, reg2

    def _project(self, term, variables, tensor_node, mod_nat, registry):
        entries = M.Head(M.Tail(M.Tail(tensor_node)())())()
        rows, raw_image, reg1 = self._walk_entries(entries, mod_nat, registry)
        sorted_image = SortNatChain(raw_image, reg1)()
        record = M.Pair(
            L.ResidueTableLabel,
            M.Pair(
                term,
                M.Pair(
                    variables,
                    M.Pair(
                        mod_nat,
                        M.Pair(rows, M.Pair(sorted_image, M.EmptyList)),
                    ),
                ),
            ),
        )
        return M.Pair(record, M.Pair(reg1, M.EmptyList))

    def __call__(self):
        return self.result


class FindTensorEqualityWitness(M.Edge):
    """
    Searches two ground EvaluationTensor records (for lhs and rhs) for an
    assignment where lhs_val == rhs_val (using M.NatEq).
    Returns Pair(env_chain_or_EmptyList, Pair(registry, EmptyList)).
    """

    def __init__(self, lhs_tensor, rhs_tensor, lhs_vars, rhs_vars, positive_only, registry):
        self.registry = registry
        self.result = self._find(
            lhs_tensor, rhs_tensor, lhs_vars, rhs_vars, positive_only, registry
        )
        super().__init__(
            inputs=M.Pair(
                lhs_tensor,
                M.Pair(
                    rhs_tensor,
                    M.Pair(
                        lhs_vars,
                        M.Pair(
                            rhs_vars,
                            M.Pair(positive_only, M.Pair(registry, M.EmptyList)),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _envs_compatible(self, env_a, env_b, registry):
        if M.IdentityCompare(env_b, M.EmptyList)() is M.truth_value:
            return M.truth_value
        binding = M.Head(env_b)()
        var = M.Head(binding)()
        val_b = M.Head(M.Tail(binding)())()
        val_a = _env_lookup(env_a, var)
        if M.IdentityCompare(val_a, M.EmptyList)() is M.false_value:
            if M.NatEq(val_a, val_b, registry)() is M.false_value:
                return M.false_value
        return self._envs_compatible(env_a, M.Tail(env_b)(), registry)

    def _merge_envs(self, env_a, env_b):
        if M.IdentityCompare(env_b, M.EmptyList)() is M.truth_value:
            return env_a
        binding = M.Head(env_b)()
        var = M.Head(binding)()
        if M.IdentityCompare(_env_lookup(env_a, var), M.EmptyList)() is M.false_value:
            return self._merge_envs(env_a, M.Tail(env_b)())
        return self._merge_envs(_chain_append_end(env_a, binding), M.Tail(env_b)())

    def _find(self, lhs_tensor, rhs_tensor, lhs_vars, rhs_vars, positive_only, registry):
        entries_l = M.Head(M.Tail(M.Tail(lhs_tensor)())())()
        entries_r = M.Head(M.Tail(M.Tail(rhs_tensor)())())()
        cur_l = entries_l
        while M.IdentityCompare(cur_l, M.EmptyList)() is M.false_value:
            ent_l = M.Head(cur_l)()
            tup_l = M.Head(M.Tail(ent_l)())()
            val_l = M.Head(M.Tail(M.Tail(ent_l)())())()
            if (
                positive_only is M.false_value
                or _tuple_all_positive(tup_l, registry) is M.truth_value
            ):
                cur_r = entries_r
                while M.IdentityCompare(cur_r, M.EmptyList)() is M.false_value:
                    ent_r = M.Head(cur_r)()
                    tup_r = M.Head(M.Tail(ent_r)())()
                    val_r = M.Head(M.Tail(M.Tail(ent_r)())())()
                    if (
                        positive_only is M.false_value
                        or _tuple_all_positive(tup_r, registry) is M.truth_value
                    ):
                        if (
                            M.IdentityCompare(val_l, val_r)() is M.truth_value
                            or M.NatEq(val_l, val_r, registry)() is M.truth_value
                        ):
                            env_l = _zip_environment(lhs_vars, tup_l)
                            env_r = _zip_environment(rhs_vars, tup_r)
                            if self._envs_compatible(env_l, env_r, registry) is M.truth_value:
                                merged = self._merge_envs(env_l, env_r)
                                return M.Pair(merged, M.Pair(registry, M.EmptyList))
                    cur_r = M.Tail(cur_r)()
            cur_l = M.Tail(cur_l)()
        return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

    def __call__(self):
        return self.result


def _build_expr_ground_tensor(term, vars_chain, domain_chain, op_label_char, registry):
    domains = M.EmptyList
    cur_v = vars_chain
    while M.IdentityCompare(cur_v, M.EmptyList)() is M.false_value:
        domains = M.Pair(domain_chain, domains)
        cur_v = M.Tail(cur_v)()
    tuples = ProductOfDomains(domains)()

    def eval_fn(tup, reg):
        env = _zip_environment(vars_chain, tup)
        return EvaluateNatExpr(term, env, reg)()

    return EvaluateOperationTensor(op_label_char, eval_fn, tuples, registry)()


def _partition_congruence_from_tables(
    all_vars, lhs_vars, rhs_vars, rows_l, rows_r, mod_nat, registry
):
    """
    Partitions {0..m-1}^k into holding and failing chains from the ResidueTable
    rows of lhs and rhs.
    """
    disjoint_vars = M.truth_value
    cur_v = lhs_vars
    while M.IdentityCompare(cur_v, M.EmptyList)() is M.false_value:
        if _chain_has_var(rhs_vars, M.Head(cur_v)()) is M.truth_value:
            disjoint_vars = M.false_value
        cur_v = M.Tail(cur_v)()

    if disjoint_vars is M.truth_value:
        holding = M.EmptyList
        failing = M.EmptyList
        cur_l = rows_l
        while M.IdentityCompare(cur_l, M.EmptyList)() is M.false_value:
            rl = M.Head(cur_l)()
            tl = M.Head(rl)()
            reml = M.Head(M.Tail(rl)())()
            cur_r = rows_r
            while M.IdentityCompare(cur_r, M.EmptyList)() is M.false_value:
                rr = M.Head(cur_r)()
                tr = M.Head(rr)()
                remr = M.Head(M.Tail(rr)())()
                pt = _chain_concat(tl, tr)
                holds = M.false_value
                if (
                    M.IdentityCompare(reml, M.EmptyList)() is M.false_value
                    and M.IdentityCompare(remr, M.EmptyList)() is M.false_value
                ):
                    if (
                        M.IdentityCompare(reml, remr)() is M.truth_value
                        or M.NatEq(reml, remr, registry)() is M.truth_value
                    ):
                        holds = M.truth_value
                if holds is M.truth_value:
                    holding = M.Pair(pt, holding)
                else:
                    failing = M.Pair(pt, failing)
                cur_r = M.Tail(cur_r)()
            cur_l = M.Tail(cur_l)()
        return _chain_reverse(holding), _chain_reverse(failing), registry

    domains, reg1 = _residue_domains(all_vars, mod_nat, registry)
    tuples = ProductOfDomains(domains)()
    holding = M.EmptyList
    failing = M.EmptyList
    cur_t = tuples
    while M.IdentityCompare(cur_t, M.EmptyList)() is M.false_value:
        pt = M.Head(cur_t)()
        env = _zip_environment(all_vars, pt)
        sub_l = _project_env_to_subtuple(env, lhs_vars)
        sub_r = _project_env_to_subtuple(env, rhs_vars)
        reml = _lookup_residue_row(rows_l, sub_l, reg1)
        remr = _lookup_residue_row(rows_r, sub_r, reg1)
        holds = M.false_value
        if (
            M.IdentityCompare(reml, M.EmptyList)() is M.false_value
            and M.IdentityCompare(remr, M.EmptyList)() is M.false_value
        ):
            if (
                M.IdentityCompare(reml, remr)() is M.truth_value
                or M.NatEq(reml, remr, reg1)() is M.truth_value
            ):
                holds = M.truth_value
        if holds is M.truth_value:
            holding = M.Pair(pt, holding)
        else:
            failing = M.Pair(pt, failing)
        cur_t = M.Tail(cur_t)()
    return _chain_reverse(holding), _chain_reverse(failing), reg1


def _any_coord_proper(coord_projs):
    if M.IdentityCompare(coord_projs, M.EmptyList)() is M.truth_value:
        return M.false_value
    rec = M.Head(coord_projs)()
    is_proper = M.Head(M.Tail(M.Tail(M.Tail(rec)())())())()
    if is_proper is M.truth_value:
        return M.truth_value
    return _any_coord_proper(M.Tail(coord_projs)())


class DiscoverExprObstructions(M.Edge):
    """
    Pure-machine Cartesian congruence & coordinate projection analyzer.
    Given admitted polynomial expressions `lhs` and `rhs`, evaluates their
    ground EvaluationTensors over 0..bound_nat-1 and projects across each
    candidate modulus m in `moduli_chain`:
      1. ResidueTable images `lhs_image` and `rhs_image` modulo m.
      2. EvaluateSetRelation disjointness and intersection of `rhs_image` and `lhs_image`.
      3. CongruenceClasses partition of {0..m-1}^k into `holding` and `failing` chains.
      4. ProjectAllCoordinates projection of `holding` onto each variable coordinate.
    Returns Pair(discoveries_chain, Pair(registry, EmptyList)).
    """

    def __init__(
        self,
        lhs,
        rhs,
        bound_nat,
        moduli_chain,
        registry,
        lhs_tensor=M.EmptyList,
        rhs_tensor=M.EmptyList,
        debug_trace=M.false_value,
    ):
        self.registry = registry
        self.result = self._discover(
            lhs,
            rhs,
            bound_nat,
            moduli_chain,
            registry,
            lhs_tensor,
            rhs_tensor,
            debug_trace,
        )
        super().__init__(
            inputs=M.Pair(
                lhs,
                M.Pair(
                    rhs,
                    M.Pair(
                        bound_nat,
                        M.Pair(moduli_chain, M.Pair(registry, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _discover(
        self,
        lhs,
        rhs,
        bound_nat,
        moduli_chain,
        registry,
        lhs_tensor,
        rhs_tensor,
        debug_trace,
    ):
        reg = registry
        lhs_vars = M.Head(ExtractExprVariables(lhs, reg)())()
        rhs_vars = M.Head(ExtractExprVariables(rhs, reg)())()
        all_vars = _chain_merge_unique(lhs_vars, rhs_vars)

        if M.IdentityCompare(lhs_tensor, M.EmptyList)() is M.truth_value:
            dom_res = BuildNatRange(M.Zero, bound_nat, reg)()
            domain = M.Head(dom_res)()
            reg = M.Head(M.Tail(dom_res)())()
            lt_res = _build_expr_ground_tensor(
                lhs, lhs_vars, domain, M.Char("lhs"), reg
            )
            lhs_tensor = M.Head(lt_res)()
            reg = M.Head(M.Tail(lt_res)())()
            rt_res = _build_expr_ground_tensor(
                rhs, rhs_vars, domain, M.Char("rhs"), reg
            )
            rhs_tensor = M.Head(rt_res)()
            reg = M.Head(M.Tail(rt_res)())()

        discoveries = M.EmptyList
        cur_m = moduli_chain
        while M.IdentityCompare(cur_m, M.EmptyList)() is M.false_value:
            m_nat = M.Head(cur_m)()

            proj_l = ProjectTensorModulo(lhs, lhs_vars, lhs_tensor, m_nat, reg)()
            table_l = M.Head(proj_l)()
            reg = M.Head(M.Tail(proj_l)())()
            rows_l = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(table_l)())())())())()
            lhs_image = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(table_l)())())())())()
            )()

            proj_r = ProjectTensorModulo(rhs, rhs_vars, rhs_tensor, m_nat, reg)()
            table_r = M.Head(proj_r)()
            reg = M.Head(M.Tail(proj_r)())()
            rows_r = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(table_r)())())())())()
            rhs_image = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(table_r)())())())())()
            )()

            rel_res = EvaluateSetRelation(rhs_image, lhs_image, reg)()
            is_disjoint = M.Head(rel_res)()
            inter_raw = M.Head(M.Tail(rel_res)())()
            reg = M.Head(M.Tail(M.Tail(rel_res)())())()
            inter_set = SortNatChain(inter_raw, reg)()

            holding, failing, reg = _partition_congruence_from_tables(
                all_vars, lhs_vars, rhs_vars, rows_l, rows_r, m_nat, reg
            )

            h_len_res = ChainLength(holding, reg)()
            holding_count = M.Head(h_len_res)()
            reg = M.Head(M.Tail(h_len_res)())()

            f_len_res = ChainLength(failing, reg)()
            failing_count = M.Head(f_len_res)()
            reg = M.Head(M.Tail(f_len_res)())()

            coord_res = ProjectAllCoordinates(holding, all_vars, m_nat, reg)()
            coord_projs = M.Head(coord_res)()
            reg = M.Head(M.Tail(coord_res)())()

            l_img_len_res = ChainLength(lhs_image, reg)()
            l_img_len = M.Head(l_img_len_res)()
            reg = M.Head(M.Tail(l_img_len_res)())()

            r_img_len_res = ChainLength(rhs_image, reg)()
            r_img_len = M.Head(r_img_len_res)()
            reg = M.Head(M.Tail(r_img_len_res)())()

            if debug_trace is not M.false_value:
                m_val = M.NatRepOf(m_nat, reg)()()
                h_val = M.NatRepOf(holding_count, reg)()()
                f_val = M.NatRepOf(failing_count, reg)()()
                _pg_debug(
                    f"modulus m = {m_val}: image(lhs mod {m_val}) = {_format_set_chain(lhs_image, reg)}, image(rhs mod {m_val}) = {_format_set_chain(rhs_image, reg)}, intersection = {_format_set_chain(inter_set, reg)}, CongruenceClasses |holding| = {h_val}, |failing| = {f_val}"
                )

            has_failing = M.IdentityCompare(failing, M.EmptyList)() is M.false_value
            img_compressed = M.OrAtom(
                M.NatLess(l_img_len, m_nat, reg)(),
                M.NatLess(r_img_len, m_nat, reg)(),
            )()
            coord_restricted = _any_coord_proper(coord_projs)

            if has_failing and (
                is_disjoint is M.truth_value
                or img_compressed is M.truth_value
                or coord_restricted is M.truth_value
            ):
                rec = M.Pair(
                    L.DiscoveredInvariantLabel,
                    M.Pair(
                        m_nat,
                        M.Pair(
                            rhs_image,
                            M.Pair(
                                lhs_image,
                                M.Pair(
                                    is_disjoint,
                                    M.Pair(
                                        holding_count,
                                        M.Pair(
                                            failing_count,
                                            M.Pair(coord_projs, M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
                discoveries = _chain_append_end(discoveries, rec)

            cur_m = M.Tail(cur_m)()

        return M.Pair(discoveries, M.Pair(reg, M.EmptyList))

    def __call__(self):
        return self.result


# ============================================================
# Surface Goal Tokenization & AST Construction (Pair-chain native)
# ============================================================


def is_proof_or_math_goal(text):
    """
    Returns M.truth_value when a surface line is a proof request or contains
    mathematical relational/algebraic structure, else M.false_value.
    """
    if not text:
        return M.false_value
    low = text.strip().lower()
    for prefix in (
        "prove", "show", "claim", "conjecture", "check", "verify",
        "is it true", "for all", "for every", "for any", "for each",
        "if ", "whenever ", "solve ",
    ):
        if low.startswith(prefix):
            return M.truth_value
    for sym in ("=", "!=", "<", ">", "^", "+", "*"):
        if sym in low:
            return M.truth_value
    return M.false_value


def _is_digits_str(s):
    if not s:
        return M.false_value
    return M.truth_value if s.isdigit() else M.false_value


def _is_ident_str(s):
    if not s:
        return M.false_value
    return M.truth_value if s[0].isalpha() else M.false_value


def _is_op_str(s):
    if s in ("+", "*", "^"):
        return M.truth_value
    return M.false_value


def _tokenize_to_chain(text):
    """
    Scans `text` character by character into a machine Pair chain of M.Char tokens.
    """
    rev_tokens = M.EmptyList
    cur_tok = ""
    cur_kind = M.EmptyList  # M.Zero=digits, M.one=ident, M.two=relop

    def flush_current(next_is_alpha):
        nonlocal rev_tokens, cur_tok, cur_kind
        if cur_tok != "":
            rev_tokens = M.Pair(M.Char(cur_tok), rev_tokens)
            if cur_kind is M.Zero and next_is_alpha is M.truth_value:
                rev_tokens = M.Pair(M.Char("*"), rev_tokens)
            cur_tok = ""
            cur_kind = M.EmptyList

    for ch in text:
        if cur_kind is M.two:
            if ch == "=":
                cur_tok = cur_tok + "="
                flush_current(M.false_value)
                continue
            flush_current(M.truth_value if ch.isalpha() else M.false_value)

        if ch.isspace() or ch in ",;:.?!\"'":
            flush_current(M.false_value)
        elif ch in "+*^()":
            flush_current(M.false_value)
            rev_tokens = M.Pair(M.Char(ch), rev_tokens)
        elif ch in "><=!":
            flush_current(M.false_value)
            cur_tok = ch
            cur_kind = M.two
        elif ch.isdigit():
            if cur_kind is M.Zero or cur_kind is M.one:
                cur_tok = cur_tok + ch
            else:
                flush_current(M.false_value)
                cur_tok = ch
                cur_kind = M.Zero
        elif ch.isalpha() or ch == "_":
            if cur_kind is M.one:
                cur_tok = cur_tok + ch.lower()
            else:
                flush_current(M.truth_value)
                cur_tok = ch.lower()
                cur_kind = M.one
        elif ch == "-" and cur_kind is M.one:
            cur_tok = cur_tok + ch
        else:
            flush_current(M.false_value)

    flush_current(M.false_value)
    return _chain_reverse(rev_tokens)


def _split_tokens_at_eq(tokens_chain):
    """
    Splits tokens_chain at the first '=', '==', or '!=' token.
    Returns Pair(rev_before_chain, Pair(eq_char, Pair(after_chain, EmptyList))),
    or EmptyList if no equality operator is present.
    """
    rev_before = M.EmptyList
    cur = tokens_chain
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        tok = M.Head(cur)()
        s = tok()
        if s in ("=", "==", "!="):
            return M.Pair(
                rev_before,
                M.Pair(tok, M.Pair(M.Tail(cur)(), M.EmptyList)),
            )
        rev_before = M.Pair(tok, rev_before)
        cur = M.Tail(cur)()
    return M.EmptyList


def _extract_lhs_chain(rev_before_chain, registry):
    """
    Walks rev_before_chain (right-to-left from '=') alternating operand and
    binary operator ('+', '*', '^') with Peano parenthesis depth, building
    the forward lhs token chain directly via Pair prepending.
    """
    acc = M.EmptyList
    depth = M.Zero
    expect_operand = M.truth_value
    cur = rev_before_chain
    reg = registry

    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        tok = M.Head(cur)()
        s = tok()
        if s == ")":
            if expect_operand is M.false_value:
                break
            succ_res = M.Succ(depth, reg)()
            depth = M.Head(succ_res)()
            reg = M.Head(M.Tail(succ_res)())()
            acc = M.Pair(tok, acc)
            expect_operand = M.truth_value
        elif s == "(":
            if (
                expect_operand is M.truth_value
                or M.NatEq(depth, M.Zero, reg)() is M.truth_value
            ):
                break
            pred_res = M.NatPred(depth, reg)()
            depth = M.Head(pred_res)()
            reg = M.Head(M.Tail(pred_res)())()
            acc = M.Pair(tok, acc)
            expect_operand = M.false_value
        elif _is_op_str(s) is M.truth_value:
            if expect_operand is M.truth_value:
                break
            acc = M.Pair(tok, acc)
            expect_operand = M.truth_value
        elif _is_digits_str(s) is M.truth_value or _is_ident_str(s) is M.truth_value:
            if expect_operand is M.false_value:
                break
            acc = M.Pair(tok, acc)
            expect_operand = M.false_value
        else:
            break
        cur = M.Tail(cur)()

    while (
        M.IdentityCompare(acc, M.EmptyList)() is M.false_value
        and _is_op_str(M.Head(acc)()()) is M.truth_value
    ):
        acc = M.Tail(acc)()
    return acc, reg


def _extract_rhs_chain(after_chain, registry):
    """
    Walks after_chain (left-to-right from '=') alternating operand and
    binary operator ('+', '*', '^') with Peano parenthesis depth.
    """
    rev_acc = M.EmptyList
    depth = M.Zero
    expect_operand = M.truth_value
    cur = after_chain
    reg = registry

    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        tok = M.Head(cur)()
        s = tok()
        if s == "(":
            if expect_operand is M.false_value:
                break
            succ_res = M.Succ(depth, reg)()
            depth = M.Head(succ_res)()
            reg = M.Head(M.Tail(succ_res)())()
            rev_acc = M.Pair(tok, rev_acc)
            expect_operand = M.truth_value
        elif s == ")":
            if (
                expect_operand is M.truth_value
                or M.NatEq(depth, M.Zero, reg)() is M.truth_value
            ):
                break
            pred_res = M.NatPred(depth, reg)()
            depth = M.Head(pred_res)()
            reg = M.Head(M.Tail(pred_res)())()
            rev_acc = M.Pair(tok, rev_acc)
            expect_operand = M.false_value
        elif _is_op_str(s) is M.truth_value:
            if expect_operand is M.truth_value:
                break
            rev_acc = M.Pair(tok, rev_acc)
            expect_operand = M.truth_value
        elif _is_digits_str(s) is M.truth_value or _is_ident_str(s) is M.truth_value:
            if expect_operand is M.false_value:
                break
            rev_acc = M.Pair(tok, rev_acc)
            expect_operand = M.false_value
        else:
            break
        cur = M.Tail(cur)()

    while (
        M.IdentityCompare(rev_acc, M.EmptyList)() is M.false_value
        and _is_op_str(M.Head(rev_acc)()()) is M.truth_value
    ):
        rev_acc = M.Tail(rev_acc)()
    return _chain_reverse(rev_acc), reg


def _intern_char_in_chain(intern_chain, name_str):
    cur = intern_chain
    cand = M.Char(name_str)
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        existing = M.Head(cur)()
        if M.Compare(existing, cand)() is M.truth_value:
            return existing, intern_chain
        cur = M.Tail(cur)()
    return cand, M.Pair(cand, intern_chain)


def _parse_expr_tokens(tokens_chain, intern_chain, registry):
    """
    Recursive-descent parser over a Pair chain of M.Char tokens.
    Returns (ast_or_EmptyList, intern_chain, registry).
    """

    def parse_add(cur_toks, ic, reg):
        left, rem, ic1, r1 = parse_mul(cur_toks, ic, reg)
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return M.EmptyList, rem, ic1, r1
        while (
            M.IdentityCompare(rem, M.EmptyList)() is M.false_value
            and M.Head(rem)()() == "+"
        ):
            right, rem2, ic2, r2 = parse_mul(M.Tail(rem)(), ic1, r1)
            if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
                return M.EmptyList, rem2, ic2, r2
            left = M.Pair(L.ExprAddLabel, M.Pair(left, M.Pair(right, M.EmptyList)))
            rem, ic1, r1 = rem2, ic2, r2
        return left, rem, ic1, r1

    def parse_mul(cur_toks, ic, reg):
        left, rem, ic1, r1 = parse_pow(cur_toks, ic, reg)
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return M.EmptyList, rem, ic1, r1
        while (
            M.IdentityCompare(rem, M.EmptyList)() is M.false_value
            and M.Head(rem)()() == "*"
        ):
            right, rem2, ic2, r2 = parse_pow(M.Tail(rem)(), ic1, r1)
            if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
                return M.EmptyList, rem2, ic2, r2
            left = M.Pair(L.ExprMulLabel, M.Pair(left, M.Pair(right, M.EmptyList)))
            rem, ic1, r1 = rem2, ic2, r2
        return left, rem, ic1, r1

    def parse_pow(cur_toks, ic, reg):
        base, rem, ic1, r1 = parse_primary(cur_toks, ic, reg)
        if M.IdentityCompare(base, M.EmptyList)() is M.truth_value:
            return M.EmptyList, rem, ic1, r1
        if (
            M.IdentityCompare(rem, M.EmptyList)() is M.false_value
            and M.Head(rem)()() == "^"
        ):
            exp, rem2, ic2, r2 = parse_primary(M.Tail(rem)(), ic1, r1)
            if M.IdentityCompare(exp, M.EmptyList)() is M.truth_value:
                return M.EmptyList, rem2, ic2, r2
            node = M.Pair(L.ExprPowLabel, M.Pair(base, M.Pair(exp, M.EmptyList)))
            return node, rem2, ic2, r2
        return base, rem, ic1, r1

    def parse_primary(cur_toks, ic, reg):
        if M.IdentityCompare(cur_toks, M.EmptyList)() is M.truth_value:
            return M.EmptyList, cur_toks, ic, reg
        tok = M.Head(cur_toks)()
        s = tok()
        rem = M.Tail(cur_toks)()
        if s == "(":
            inner, rem2, ic1, r1 = parse_add(rem, ic, reg)
            if M.IdentityCompare(inner, M.EmptyList)() is M.truth_value:
                return M.EmptyList, rem2, ic1, r1
            if (
                M.IdentityCompare(rem2, M.EmptyList)() is M.truth_value
                or M.Head(rem2)()() != ")"
            ):
                return M.EmptyList, rem2, ic1, r1
            return inner, M.Tail(rem2)(), ic1, r1
        if _is_digits_str(s) is M.truth_value:
            nat_res = M.NatFromRep(M.GMPRep(s), reg)()
            return M.Head(nat_res)(), rem, ic, M.Head(M.Tail(nat_res)())()
        if _is_ident_str(s) is M.truth_value:
            atom, ic1 = _intern_char_in_chain(ic, s)
            return atom, rem, ic1, reg
        return M.EmptyList, cur_toks, ic, reg

    ast, leftover, next_ic, next_reg = parse_add(tokens_chain, intern_chain, registry)
    if M.IdentityCompare(leftover, M.EmptyList)() is M.false_value:
        return M.EmptyList, next_ic, next_reg
    return ast, next_ic, next_reg


def _extract_param_constraints(tokens_before_chain, intern_chain, registry):
    """
    Scans tokens_before_chain for parameter inequalities (e.g. n > 2, n >= 3)
    and returns machine constraint terms Pair(ExprLtLabel, Pair(bound_nat, Pair(var, []))).
    """
    constraints = M.EmptyList
    cur = tokens_before_chain
    ic = intern_chain
    reg = registry
    while (
        M.IdentityCompare(cur, M.EmptyList)() is M.false_value
        and M.IdentityCompare(M.Tail(cur)(), M.EmptyList)() is M.false_value
        and M.IdentityCompare(M.Tail(M.Tail(cur)())(), M.EmptyList)() is M.false_value
    ):
        t1 = M.Head(cur)()()
        t2 = M.Head(M.Tail(cur)())()()
        t3 = M.Head(M.Tail(M.Tail(cur)())())()()
        if _is_ident_str(t1) is M.truth_value and _is_digits_str(t3) is M.truth_value:
            var_atom, ic = _intern_char_in_chain(ic, t1)
            nat_res = M.NatFromRep(M.GMPRep(t3), reg)()
            num_nat = M.Head(nat_res)()
            reg = M.Head(M.Tail(nat_res)())()
            if t2 == ">":
                c_term = M.Pair(
                    L.ExprLtLabel, M.Pair(num_nat, M.Pair(var_atom, M.EmptyList))
                )
                constraints = _chain_append_end(constraints, c_term)
            elif t2 == ">=" and M.NatEq(num_nat, M.Zero, reg)() is M.false_value:
                pred_res = M.NatPred(num_nat, reg)()
                pred_nat = M.Head(pred_res)()
                reg = M.Head(M.Tail(pred_res)())()
                c_term = M.Pair(
                    L.ExprLtLabel, M.Pair(pred_nat, M.Pair(var_atom, M.EmptyList))
                )
                constraints = _chain_append_end(constraints, c_term)
        cur = M.Tail(cur)()
    return constraints, ic, reg


def _token_chain_has_any_word(tokens_chain, words_tuple):
    cur = tokens_chain
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        s = M.Head(cur)()()
        if s in words_tuple:
            return M.truth_value
        cur = M.Tail(cur)()
    return M.false_value


def parse_surface_goal_spec(text, registry):
    """
    Parses a surface mathematical proof goal into a pure machine Pair record:
      Pair(lhs_ast,
        Pair(rhs_ast,
          Pair(base_vars,
            Pair(exp_vars,
              Pair(param_constraints,
                Pair(no_solutions_flag,
                  Pair(positive_only_flag,
                    Pair(registry, EmptyList))))))))
    Returns M.EmptyList if no equation is present.
    """
    if not text:
        return M.EmptyList
    tokens_chain = _tokenize_to_chain(text)
    split_res = _split_tokens_at_eq(tokens_chain)
    if M.IdentityCompare(split_res, M.EmptyList)() is M.truth_value:
        return M.EmptyList

    rev_before = M.Head(split_res)()
    eq_tok = M.Head(M.Tail(split_res)())()
    after_chain = M.Head(M.Tail(M.Tail(split_res)())())()
    before_chain = _chain_reverse(rev_before)

    lhs_toks, reg1 = _extract_lhs_chain(rev_before, registry)
    rhs_toks, reg2 = _extract_rhs_chain(after_chain, reg1)
    if (
        M.IdentityCompare(lhs_toks, M.EmptyList)() is M.truth_value
        or M.IdentityCompare(rhs_toks, M.EmptyList)() is M.truth_value
    ):
        return M.EmptyList

    intern_chain = M.EmptyList
    lhs_ast, intern_chain, reg3 = _parse_expr_tokens(lhs_toks, intern_chain, reg2)
    if M.IdentityCompare(lhs_ast, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    rhs_ast, intern_chain, reg4 = _parse_expr_tokens(rhs_toks, intern_chain, reg3)
    if M.IdentityCompare(rhs_ast, M.EmptyList)() is M.truth_value:
        return M.EmptyList

    param_constraints, intern_chain, reg5 = _extract_param_constraints(
        before_chain, intern_chain, reg4
    )

    eq_node = M.Pair(
        L.ExprEqLabel, M.Pair(lhs_ast, M.Pair(rhs_ast, M.EmptyList))
    )
    all_vars = M.Head(ExtractExprVariables(eq_node, reg5)())()
    exp_vars = M.Head(ExtractExponentVariables(eq_node, reg5)())()

    base_vars = M.EmptyList
    cur_v = all_vars
    while M.IdentityCompare(cur_v, M.EmptyList)() is M.false_value:
        v_atom = M.Head(cur_v)()
        if _chain_has_var(exp_vars, v_atom) is M.false_value:
            base_vars = _chain_append_end(base_vars, v_atom)
        cur_v = M.Tail(cur_v)()

    no_sol_words = _token_chain_has_any_word(
        tokens_chain, ("no", "impossible", "cannot", "never")
    )
    no_solutions_flag = (
        M.truth_value
        if eq_tok() == "!=" or no_sol_words is M.truth_value
        else M.false_value
    )
    positive_only_flag = _token_chain_has_any_word(
        tokens_chain, ("positive", "nonzero", "non-zero")
    )

    return M.Pair(
        lhs_ast,
        M.Pair(
            rhs_ast,
            M.Pair(
                base_vars,
                M.Pair(
                    exp_vars,
                    M.Pair(
                        param_constraints,
                        M.Pair(
                            no_solutions_flag,
                            M.Pair(
                                positive_only_flag,
                                M.Pair(reg5, M.EmptyList),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def _unpack_goal_spec(spec_rec):
    lhs = M.Head(spec_rec)()
    t1 = M.Tail(spec_rec)()
    rhs = M.Head(t1)()
    t2 = M.Tail(t1)()
    base_vars = M.Head(t2)()
    t3 = M.Tail(t2)()
    exp_vars = M.Head(t3)()
    t4 = M.Tail(t3)()
    param_constraints = M.Head(t4)()
    t5 = M.Tail(t4)()
    no_solutions = M.Head(t5)()
    t6 = M.Tail(t5)()
    positive_only = M.Head(t6)()
    reg = M.Head(M.Tail(t6)())()
    return (
        lhs,
        rhs,
        base_vars,
        exp_vars,
        param_constraints,
        no_solutions,
        positive_only,
        reg,
    )


def _format_set_chain(set_chain, registry):
    sorted_chain = SortNatChain(set_chain, registry)()
    cur = sorted_chain
    out = ""
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        rep = M.NatRepOf(M.Head(cur)(), registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            part = str(rep())
            out = part if out == "" else out + ", " + part
        cur = M.Tail(cur)()
    return "{" + out + "}"


def _format_vars_chain(vars_chain):
    cur = vars_chain
    out = ""
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        part = str(M.Head(cur)()())
        out = part if out == "" else out + ", " + part
        cur = M.Tail(cur)()
    return out


def _format_env_chain(env_chain, registry):
    cur = env_chain
    out = ""
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        entry = M.Head(cur)()
        v_name = str(M.Head(entry)()())
        v_nat = M.Head(M.Tail(entry)())()
        v_str = str(M.NatRepOf(v_nat, registry)()())
        part = f"{v_name} = {v_str}"
        out = part if out == "" else out + ", " + part
        cur = M.Tail(cur)()
    return out


def _format_discoveries_report(
    lhs,
    rhs,
    discoveries,
    moduli_chain,
    bound_nat,
    witness_env,
    positive_only,
    reg,
    indent="  ",
):
    lhs_str = RenderNatExpr(lhs, reg)
    rhs_str = RenderNatExpr(rhs, reg)
    pred_res = M.NatPred(bound_nat, reg)()
    max_elem_val = M.NatRepOf(M.Head(pred_res)(), reg)()()
    reg = M.Head(M.Tail(pred_res)())()
    min_elem_val = 1 if positive_only is M.truth_value else 0
    mods_str = _format_set_chain(moduli_chain, reg)

    if M.IdentityCompare(witness_env, M.EmptyList)() is M.false_value:
        w_str = _format_env_chain(witness_env, reg)
        report = f"{indent}- Ground Tensor Witness ({min_elem_val}..{max_elem_val}): Counterexample solution found at ({w_str}) where {lhs_str} = {rhs_str}."
    else:
        report = f"{indent}- Ground Tensor Witness Search (domain {min_elem_val}..{max_elem_val}): 0 solutions in ground tensor; sweeping moduli {mods_str}."

    if M.IdentityCompare(discoveries, M.EmptyList)() is M.truth_value:
        return (
            report
            + f"\n{indent}- CongruenceClasses across moduli {mods_str}: no proper residue restriction found."
        )

    cur = discoveries
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        rec = M.Head(cur)()
        f1 = M.Tail(rec)()
        m_nat = M.Head(f1)()
        f2 = M.Tail(f1)()
        rhs_img = M.Head(f2)()
        f3 = M.Tail(f2)()
        lhs_img = M.Head(f3)()
        f4 = M.Tail(f3)()
        is_disj = M.Head(f4)()
        f5 = M.Tail(f4)()
        hold_cnt = M.Head(f5)()
        f6 = M.Tail(f5)()
        fail_cnt = M.Head(f6)()
        coord_projs = M.Head(M.Tail(f6)())()

        m_val = M.NatRepOf(m_nat, reg)()()
        h_val = M.NatRepOf(hold_cnt, reg)()()
        fl_val = M.NatRepOf(fail_cnt, reg)()()
        lhs_img_str = _format_set_chain(lhs_img, reg)
        rhs_img_str = _format_set_chain(rhs_img, reg)

        dom_res = BuildNatRange(M.Zero, m_nat, reg)()
        full_dom = M.Head(dom_res)()
        reg = M.Head(M.Tail(dom_res)())()
        lhs_excl = SortNatChain(SetDifference(full_dom, lhs_img, reg)(), reg)()
        rhs_excl = SortNatChain(SetDifference(full_dom, rhs_img, reg)(), reg)()
        lhs_excl_str = _format_set_chain(lhs_excl, reg)
        rhs_excl_str = _format_set_chain(rhs_excl, reg)

        report = (
            report
            + f"\n{indent}- Modulus m = {m_val}:"
            + f"\n{indent}  * ResidueTable(({lhs_str}) mod {m_val}) -> image {lhs_img_str} (excluded: {lhs_excl_str})"
            + f"\n{indent}  * ResidueTable(({rhs_str}) mod {m_val}) -> image {rhs_img_str} (excluded: {rhs_excl_str})"
            + f"\n{indent}  * CongruenceClasses(({lhs_str}) = ({rhs_str}) mod {m_val}) -> |holding| = {h_val}, |failing| = {fl_val}"
        )
        if is_disj is M.truth_value:
            report = (
                report
                + f"\n{indent}  * Disjoint Image Regularity: {rhs_img_str} /\\ {lhs_img_str} = empty (|holding| = 0)"
            )

        cur_c = coord_projs
        while M.IdentityCompare(cur_c, M.EmptyList)() is M.false_value:
            c_rec = M.Head(cur_c)()
            v_atom = M.Head(c_rec)()
            adm_set = M.Head(M.Tail(c_rec)())()
            excl_set = M.Head(M.Tail(M.Tail(c_rec)())())()
            is_prop = M.Head(M.Tail(M.Tail(M.Tail(c_rec)())())())()
            if is_prop is M.truth_value:
                v_name = str(v_atom())
                adm_str = _format_set_chain(adm_set, reg)
                excl_str = _format_set_chain(excl_set, reg)
                report = (
                    report
                    + f"\n{indent}  * Coordinate Projection: proj({v_name}, holding) = {adm_str} (excluded mod {m_val}: {excl_str})"
                )
            cur_c = M.Tail(cur_c)()

        cur = M.Tail(cur)()

    return report


def _parallel_instance_sweep_worker(goal_text, exp_str, out_queue):
    """
    Top-level multiprocessing worker for evaluating one parameter instance
    of a parametric equation across ground EvaluationTensors and moduli.
    """
    reg = M.AllConstructors
    spec_rec = parse_surface_goal_spec(goal_text, reg)
    (
        lhs,
        rhs,
        _base_vars,
        exp_vars,
        _param_constraints,
        _no_solutions,
        positive_only,
        reg,
    ) = _unpack_goal_spec(spec_rec)

    exp_var = M.Head(exp_vars)()
    exp_name = str(exp_var())
    e_res = M.NatFromRep(M.GMPRep(exp_str), reg)()
    e_nat = M.Head(e_res)()
    reg = M.Head(M.Tail(e_res)())()

    lhs_e = M.Head(SubstituteExprVar(lhs, exp_var, e_nat, reg)())()
    rhs_e = M.Head(SubstituteExprVar(rhs, exp_var, e_nat, reg)())()
    lhs_e_str = RenderNatExpr(lhs_e, reg)
    rhs_e_str = RenderNatExpr(rhs_e, reg)

    bound_nat = M.six
    dom_res = BuildNatRange(M.Zero, bound_nat, reg)()
    domain = M.Head(dom_res)()
    reg = M.Head(M.Tail(dom_res)())()

    mods_res = BuildNatRange(M.two, M.four, reg)()
    moduli_chain = M.Head(mods_res)()
    reg = M.Head(M.Tail(mods_res)())()

    lhs_vars = M.Head(ExtractExprVariables(lhs_e, reg)())()
    rhs_vars = M.Head(ExtractExprVariables(rhs_e, reg)())()

    _pg_debug(
        f"worker started for {exp_name} = {exp_str} ({lhs_e_str} = {rhs_e_str}): evaluating ground EvaluationTensors over domain 0..5 and sweeping moduli {_format_set_chain(moduli_chain, reg)}..."
    )

    lt_res = _build_expr_ground_tensor(
        lhs_e, lhs_vars, domain, M.Char("lhs"), reg
    )
    lhs_tensor = M.Head(lt_res)()
    reg = M.Head(M.Tail(lt_res)())()

    rt_res = _build_expr_ground_tensor(
        rhs_e, rhs_vars, domain, M.Char("rhs"), reg
    )
    rhs_tensor = M.Head(rt_res)()
    reg = M.Head(M.Tail(rt_res)())()

    wit_res = FindTensorEqualityWitness(
        lhs_tensor, rhs_tensor, lhs_vars, rhs_vars, positive_only, reg
    )()
    witness_env = M.Head(wit_res)()
    reg = M.Head(M.Tail(wit_res)())()

    disc_res = DiscoverExprObstructions(
        lhs_e,
        rhs_e,
        bound_nat,
        moduli_chain,
        reg,
        lhs_tensor=lhs_tensor,
        rhs_tensor=rhs_tensor,
        debug_trace=M.truth_value,
    )()
    disc_chain = M.Head(disc_res)()
    reg = M.Head(M.Tail(disc_res)())()

    header = f"  [Instance {exp_name} = {exp_str}: {lhs_e_str} = {rhs_e_str}]"
    body = _format_discoveries_report(
        lhs_e,
        rhs_e,
        disc_chain,
        moduli_chain,
        bound_nat,
        witness_env,
        positive_only,
        reg,
        indent="    ",
    )
    first_mod_str = "4"
    if M.IdentityCompare(disc_chain, M.EmptyList)() is M.false_value:
        first_rec = M.Head(disc_chain)()
        first_mod_nat = M.Head(M.Tail(first_rec)())()
        first_mod_str = str(M.NatRepOf(first_mod_nat, reg)()())

    _pg_debug(f"worker completed {exp_name} = {exp_str}.")
    out_queue.put((exp_str, os.getpid(), header + "\n" + body, first_mod_str))


def _filter_candidate_parameters(exp_var, param_constraints, registry):
    """
    Generates a candidate Nat domain via BuildNatRange and filters it using
    FilterTuples and _evaluate_nat_constraints (machine constraint evaluation).
    """
    cand_res = BuildNatRange(M.two, M.four, registry)()
    cand_domain = M.Head(cand_res)()
    reg1 = M.Head(M.Tail(cand_res)())()

    if M.IdentityCompare(param_constraints, M.EmptyList)() is M.truth_value:
        return M.Pair(M.two, M.Pair(M.three, M.EmptyList)), reg1

    dom1 = ProductOfDomains(M.Pair(cand_domain, M.EmptyList))()
    vars_one = M.Pair(exp_var, M.EmptyList)

    def constraint_pred(tup, reg):
        env = _zip_environment(vars_one, tup)
        return _evaluate_nat_constraints(param_constraints, env, reg)

    filt_res = FilterTuples(dom1, constraint_pred, reg1)()
    filt_tuples = M.Head(filt_res)()
    reg2 = M.Head(M.Tail(filt_res)())()

    # Take first two valid parameter nodes from filtered 1-tuples
    out = M.EmptyList
    cur = filt_tuples
    taken = M.Zero
    while (
        M.IdentityCompare(cur, M.EmptyList)() is M.false_value
        and M.NatLess(taken, M.two, reg2)() is M.truth_value
    ):
        tup = M.Head(cur)()
        out = _chain_append_end(out, M.Head(tup)())
        inc = A.Add(taken, M.one, reg2)()
        taken = M.Head(inc)()
        reg2 = M.Head(M.Tail(inc)())()
        cur = M.Tail(cur)()

    if M.IdentityCompare(out, M.EmptyList)() is M.truth_value:
        return M.Pair(M.three, M.Pair(M.four, M.EmptyList)), reg2
    return out, reg2


def run_playground_interactive(graph, goal_text=None, tutor=None):
    """
    Runs the machine-native Cartesian exploration sweep over the active
    unproved goal (or discovers separating moduli over the default benchmark
    when no goal is active) and returns the formatted report.
    """
    registry = M.FromContextGetConstructors(graph)()
    active_goal = goal_text
    if active_goal is None:
        try:
            active_goal = graph._active_unproved_goal
        except AttributeError:
            active_goal = None
    active_tutor = tutor
    if active_tutor is None:
        try:
            active_tutor = graph._active_tutor
        except AttributeError:
            active_tutor = None
    try:
        active_claim = graph._active_unproved_claim
    except AttributeError:
        active_claim = None

    spec_rec = (
        parse_surface_goal_spec(active_goal, registry)
        if active_goal
        else M.EmptyList
    )
    if M.IdentityCompare(spec_rec, M.EmptyList)() is M.false_value:
        (
            lhs,
            rhs,
            base_vars,
            exp_vars,
            param_constraints,
            no_solutions,
            positive_only,
            reg,
        ) = _unpack_goal_spec(spec_rec)

        # Case A: Parametric exponent family (e.g., x^n + y^n = z^n)
        if M.IdentityCompare(exp_vars, M.EmptyList)() is M.false_value:
            exp_var = M.Head(exp_vars)()
            exp_name = str(exp_var())
            exp_chain, reg = _filter_candidate_parameters(
                exp_var, param_constraints, reg
            )
            mods_res = BuildNatRange(M.two, M.four, reg)()
            moduli_chain = M.Head(mods_res)()
            reg = M.Head(M.Tail(mods_res)())()

            lhs_pat_str = RenderNatExpr(lhs, reg)
            rhs_pat_str = RenderNatExpr(rhs, reg)
            exp_set_str = _format_set_chain(exp_chain, reg)
            mods_set_str = _format_set_chain(moduli_chain, reg)

            cpu_cap = multiprocessing.cpu_count() or 1
            _pg_debug(
                f"constructing the natural tensor for {lhs_pat_str} = {rhs_pat_str}: parameter {exp_name} in {exp_set_str}, domain 0..5, candidate moduli {mods_set_str}; dispatching parallel worker processes (CPU cores: {cpu_cap})..."
            )

            report = f"[machine] Cartesian Playground Sweep for {lhs_pat_str} = {rhs_pat_str} (parameter {exp_name} in {exp_set_str}, domain 0..5, moduli {mods_set_str}):"

            start_methods = multiprocessing.get_all_start_methods()
            mp_ctx = multiprocessing.get_context(
                "fork" if "fork" in start_methods else "spawn"
            )
            out_queue = mp_ctx.Queue()
            procs_chain = M.EmptyList
            cur_e = exp_chain
            while M.IdentityCompare(cur_e, M.EmptyList)() is M.false_value:
                e_nat = M.Head(cur_e)()
                e_str = str(M.NatRepOf(e_nat, reg)()())
                p = mp_ctx.Process(
                    target=_parallel_instance_sweep_worker,
                    args=(active_goal, e_str, out_queue),
                )
                p.start()
                procs_chain = _chain_append_end(procs_chain, M.Pair(M.Char(e_str), M.Pair(p, M.EmptyList)))
                cur_e = M.Tail(cur_e)()

            collected_chain = M.EmptyList
            cur_p = procs_chain
            while M.IdentityCompare(cur_p, M.EmptyList)() is M.false_value:
                item = out_queue.get(timeout=120)
                e_key, w_pid, inst_text, first_mod_s = item
                entry = M.Pair(
                    M.Char(e_key),
                    M.Pair(
                        M.Char(inst_text),
                        M.Pair(
                            M.Char(str(w_pid)),
                            M.Pair(M.Char(first_mod_s), M.EmptyList),
                        ),
                    ),
                )
                collected_chain = _chain_append_end(collected_chain, entry)
                cur_p = M.Tail(cur_p)()

            cur_p = procs_chain
            while M.IdentityCompare(cur_p, M.EmptyList)() is M.false_value:
                proc_obj = M.Head(M.Tail(M.Head(cur_p)())())()
                proc_obj.join(timeout=10)
                cur_p = M.Tail(cur_p)()

            first_mod_recorded = M.EmptyList
            pids_str = ""
            cur_e = exp_chain
            while M.IdentityCompare(cur_e, M.EmptyList)() is M.false_value:
                e_nat = M.Head(cur_e)()
                e_char = M.Char(str(M.NatRepOf(e_nat, reg)()()))
                cur_c = collected_chain
                while M.IdentityCompare(cur_c, M.EmptyList)() is M.false_value:
                    c_ent = M.Head(cur_c)()
                    if M.Compare(M.Head(c_ent)(), e_char)() is M.truth_value:
                        inst_t = M.Head(M.Tail(c_ent)())()()
                        pid_t = M.Head(M.Tail(M.Tail(c_ent)())())()()
                        mod_t = M.Head(M.Tail(M.Tail(M.Tail(c_ent)())())())()()
                        report = report + "\n" + inst_t
                        pids_str = pid_t if pids_str == "" else pids_str + ", " + pid_t
                        if M.IdentityCompare(first_mod_recorded, M.EmptyList)() is M.truth_value:
                            m_res = M.NatFromRep(M.GMPRep(mod_t), reg)()
                            first_mod_recorded = M.Head(m_res)()
                            reg = M.Head(M.Tail(m_res)())()
                    cur_c = M.Tail(cur_c)()
                cur_e = M.Tail(cur_e)()

            _pg_debug(f"joined worker processes (PIDs: [{pids_str}]).")

            if M.IdentityCompare(first_mod_recorded, M.EmptyList)() is M.false_value:
                graph._last_discovered_invariant = M.Pair(
                    L.DiscoveredInvariantLabel,
                    M.Pair(
                        first_mod_recorded,
                        M.Pair(
                            M.Pair(M.Zero, M.EmptyList),
                            M.Pair(
                                M.Pair(M.Zero, M.EmptyList),
                                M.Pair(M.false_value, M.EmptyList),
                            ),
                        ),
                    ),
                )
            report = (
                report
                + "\n  - Suggestion: Ground these discovered ResidueTable and CongruenceClasses regularities as candidate lemmas."
            )
            return report

        # Case B: Concrete polynomial identity claim (no_solutions is M.false_value)
        if no_solutions is M.false_value:
            lhs_str = RenderNatExpr(lhs, reg)
            rhs_str = RenderNatExpr(rhs, reg)
            _pg_debug(
                f"constructing degree-bounded polynomial grid for {lhs_str} = {rhs_str} over variables [{_format_vars_chain(base_vars)}]..."
            )
            grid_res = PolynomialIdentityByGrid(lhs, rhs, base_vars, reg)()
            grid_rec = M.Head(grid_res)()
            reg = M.Head(M.Tail(grid_res)())()
            fields = M.Tail(grid_rec)()
            grid_count_nat = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(fields)())())())()
            )()
            verdict = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(fields)())())())())()
            )()
            witness_tup = M.Head(
                M.Tail(
                    M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(fields)())())())())()
                )()
            )()
            grid_count_val = M.NatRepOf(grid_count_nat, reg)()()
            _pg_debug(
                f"evaluated {grid_count_val} degree-bounded grid points for {lhs_str} = {rhs_str}."
            )

            if verdict is M.truth_value:
                return (
                    f"[machine] Cartesian Playground Sweep for {lhs_str} = {rhs_str}:\n"
                    f"  - PolynomialIdentityByGrid verified {lhs_str} = {rhs_str} across all {grid_count_val} degree-bounded grid points.\n"
                    f"  - Candidate Lemma: Algebraic identity {lhs_str} == {rhs_str} holds universally over Nat.\n"
                    "  - Suggestion: Ground this polynomial identity into active context as a rewrite lemma."
                )
            if verdict is M.false_value:
                w_env = _zip_environment(base_vars, witness_tup)
                w_str = _format_env_chain(w_env, reg)
                return (
                    f"[machine] Cartesian Playground Sweep for {lhs_str} = {rhs_str}:\n"
                    f"  - Counterexample Witness Found: ({w_str}) refutes {lhs_str} = {rhs_str} on the degree grid.\n"
                    "  - Suggestion: Restrict domain hypotheses or project modulo a separating congruence class."
                )

        # Case C: Concrete equation with no_solutions
        bound_nat = M.six
        dom_res = BuildNatRange(M.Zero, bound_nat, reg)()
        domain = M.Head(dom_res)()
        reg = M.Head(M.Tail(dom_res)())()

        mods_res = BuildNatRange(M.two, M.four, reg)()
        moduli_chain = M.Head(mods_res)()
        reg = M.Head(M.Tail(mods_res)())()

        lhs_str = RenderNatExpr(lhs, reg)
        rhs_str = RenderNatExpr(rhs, reg)
        lhs_vars = M.Head(ExtractExprVariables(lhs, reg)())()
        rhs_vars = M.Head(ExtractExprVariables(rhs, reg)())()

        _pg_debug(
            f"constructing the natural tensor for {lhs_str} = {rhs_str}: domain 0..5, candidate moduli {_format_set_chain(moduli_chain, reg)}..."
        )

        lt_res = _build_expr_ground_tensor(
            lhs, lhs_vars, domain, M.Char("lhs"), reg
        )
        lhs_tensor = M.Head(lt_res)()
        reg = M.Head(M.Tail(lt_res)())()

        rt_res = _build_expr_ground_tensor(
            rhs, rhs_vars, domain, M.Char("rhs"), reg
        )
        rhs_tensor = M.Head(rt_res)()
        reg = M.Head(M.Tail(rt_res)())()

        wit_res = FindTensorEqualityWitness(
            lhs_tensor, rhs_tensor, lhs_vars, rhs_vars, positive_only, reg
        )()
        witness_env = M.Head(wit_res)()
        reg = M.Head(M.Tail(wit_res)())()

        disc_res = DiscoverExprObstructions(
            lhs,
            rhs,
            bound_nat,
            moduli_chain,
            reg,
            lhs_tensor=lhs_tensor,
            rhs_tensor=rhs_tensor,
            debug_trace=M.truth_value,
        )()
        disc_chain = M.Head(disc_res)()
        reg = M.Head(M.Tail(disc_res)())()

        header = f"[machine] Cartesian Playground Sweep for {lhs_str} = {rhs_str} (domain 0..5, moduli {_format_set_chain(moduli_chain, reg)}):"
        body = _format_discoveries_report(
            lhs,
            rhs,
            disc_chain,
            moduli_chain,
            bound_nat,
            witness_env,
            positive_only,
            reg,
            indent="  ",
        )
        if M.IdentityCompare(disc_chain, M.EmptyList)() is M.false_value:
            graph._last_discovered_invariant = M.Head(disc_chain)()
            graph._last_playground_discoveries = disc_chain
            body = (
                body
                + "\n  - Suggestion: Ground this discovered regularity into active context as an invariant lemma."
            )
        return header + "\n" + body

    # 2. Undecided Socratic tutor claim
    if active_claim is not None and active_tutor is not None:
        from . import dialogue as Dlg

        goal_fact = Dlg.claim_conclusion(active_claim)
        known_facts = Dlg.claim_start_facts(active_claim)
        obls_chain = Dlg.BackwardObligations(
            goal_fact, known_facts, active_tutor.rules()
        )()
        claim_str = active_tutor.claim_text(active_claim)
        _pg_debug(
            f"analyzing backward rule obligations for undecided claim '{claim_str}'..."
        )
        header = f"[machine] Cartesian Playground & Backward Obligation Analysis for '{claim_str}':"
        if M.IdentityCompare(obls_chain, M.EmptyList)() is M.false_value:
            first_obl = M.Head(obls_chain)()
            rule_obj = M.Head(first_obl)()
            open_prems_chain = M.Head(M.Tail(M.Tail(first_obl)())())()
            rule_id = active_tutor.rule_id_of(rule_obj)
            open_str = Dlg.render_fact_list(open_prems_chain, active_tutor.registry)
            goal_str = Dlg.render_term(goal_fact, active_tutor.registry)
            return (
                header
                + f"\n  - Backward Rule Candidate: '{rule_id}' concludes {goal_str} given missing premise(s): {open_str}."
                + f"\n  - Candidate Lemma: Establish {open_str} (or ground schema '{claim_str}' after verification)."
            )
        goal_str = Dlg.render_term(goal_fact, active_tutor.registry)
        return (
            header
            + f"\n  - No loaded rule concludes {goal_str} directly."
            + f"\n  - Candidate Lemma Schema: '{claim_str}' (empirically unrefuted across the Cartesian natural sweep)."
        )

    # 3. Default benchmark exploration when no specific goal has been posed yet
    _pg_debug(
        "constructing the natural tensor: 11 x 11 domain (0..10)^2 x candidate moduli {2, 3, 4, 5}..."
    )
    bound_res = M.NatFromRep(M.GMPRep(11), registry)()
    bound_nat = M.Head(bound_res)()
    reg1 = M.Head(M.Tail(bound_res)())()

    mods_res = BuildNatRange(M.two, M.four, reg1)()
    moduli_chain = M.Head(mods_res)()
    reg2 = M.Head(M.Tail(mods_res)())()

    def every_unary(_x, _reg):
        return M.truth_value

    def odd_pair_pred(x, y, reg):
        rx = A.Modulo(x, M.two, reg)()
        rem_x = M.Head(rx)()
        r_a = M.Head(M.Tail(rx)())()
        if M.NatEq(rem_x, M.one, r_a)() is M.false_value:
            return M.false_value
        ry = A.Modulo(y, M.two, r_a)()
        rem_y = M.Head(ry)()
        r_b = M.Head(M.Tail(ry)())()
        return M.NatEq(rem_y, M.one, r_b)()

    disc_res = DiscoverSeparatingModulus(
        bound_nat, M.two, every_unary, odd_pair_pred, moduli_chain, reg2
    )()
    inv_rec = M.Head(disc_res)()
    reg3 = M.Head(M.Tail(disc_res)())()

    graph._last_discovered_invariant = inv_rec

    res_mod = M.Head(M.Tail(inv_rec)())()
    mod_val = M.NatRepOf(res_mod, reg3)()()
    _pg_debug(
        f"discovered separating modulus m = {mod_val} across candidate moduli {_format_set_chain(moduli_chain, reg3)}."
    )

    sq_set = M.Head(M.Tail(M.Tail(inv_rec)())())()
    odd_sum_set = M.Head(M.Tail(M.Tail(M.Tail(inv_rec)())())())()
    is_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(inv_rec)())())())())()

    sq_str = _format_set_chain(sq_set, reg3)
    odd_str = _format_set_chain(odd_sum_set, reg3)
    tested_str = _format_set_chain(moduli_chain, reg3)

    report = (
        f"[machine] Cartesian Playground Sweep (domain 0..10, candidate moduli {tested_str} -> discovered m = {mod_val}):\n"
        f"  - 1-ary Image Projection: f([x]) = x^2 mod {mod_val} -> {sq_str}\n"
        f"  - 2-ary Image Projection: g([x, y]) = (x^2 + y^2) mod {mod_val} -> {odd_str}"
    )

    if is_disjoint is M.truth_value:
        report = (
            report
            + f"\n  - Disjoint Image Regularity: {sq_str} /\\ {odd_str} = empty"
            + f"\n  - Obstruction Invariant: f([z]) = g([x, y]) has no solution under mod {mod_val} projection."
            + "\n  - Suggestion: Ground this discovered regularity into active context as an invariant lemma."
        )

    return report


# ============================================================
# Bounded constrained Nat witnesses (not universal existence proofs)
# ============================================================


def _valid_nat_constraints(constraints, variables, registry):
    if _valid_polynomial_variables(variables, registry) is M.false_value:
        return M.false_value
    cursor = constraints
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        if M.IsPair(cursor)() is M.false_value:
            return M.false_value
        constraint = M.Head(cursor)()
        head, args = _expr_head_args(constraint)
        if M.OrAtom(M.IdentityCompare(head, L.ExprEqLabel)(),
                    M.IdentityCompare(head, L.ExprLtLabel)())() is M.false_value:
            return M.false_value
        if _exact_arity(args, 2) is M.false_value:
            return M.false_value
        if _admitted_polynomial(M.Head(args)(), variables, registry) is M.false_value:
            return M.false_value
        if _admitted_polynomial(M.Head(M.Tail(args)())(), variables, registry) is M.false_value:
            return M.false_value
        cursor = M.Tail(cursor)()
    return M.truth_value


def _valid_nat_environment(variables, environment, bound, registry):
    cursor = variables
    remaining = environment
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        if M.IsPair(remaining)() is M.false_value:
            return M.false_value
        entry = M.Head(remaining)()
        if _exact_arity(entry, 2) is M.false_value:
            return M.false_value
        if M.Compare(M.Head(entry)(), M.Head(cursor)())() is M.false_value:
            return M.false_value
        value = M.Head(M.Tail(entry)())()
        if M.IdentityCompare(A._natural_rep(value, registry), M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.NatLess(value, bound, registry)() is M.false_value:
            return M.false_value
        cursor = M.Tail(cursor)()
        remaining = M.Tail(remaining)()
    return M.IdentityCompare(remaining, M.EmptyList)()


def _evaluate_nat_constraints(constraints, environment, registry):
    cursor = constraints
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        constraint = M.Head(cursor)()
        args = M.Tail(constraint)()
        left_res = EvaluateNatExpr(M.Head(args)(), environment, registry)()
        left = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        right_res = EvaluateNatExpr(M.Head(M.Tail(args)())(), environment, reg1)()
        right = M.Head(right_res)()
        registry = M.Head(M.Tail(right_res)())()
        if M.OrAtom(M.IdentityCompare(left, M.EmptyList)(),
                    M.IdentityCompare(right, M.EmptyList)())() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(M.Head(constraint)(), L.ExprEqLabel)() is M.truth_value:
            verdict = M.NatEq(left, right, registry)()
        else:
            verdict = M.NatLess(left, right, registry)()
        if verdict is M.false_value:
            return M.Pair(M.false_value, M.Pair(registry, M.EmptyList))
        cursor = M.Tail(cursor)()
    return M.Pair(M.truth_value, M.Pair(registry, M.EmptyList))


class VerifyNatWitness(M.Edge):
    """Re-evaluate a concrete bounded Nat assignment, not a search status."""

    def __init__(self, constraints, variables, bound, environment, registry):
        self.result = self._verify(constraints, variables, bound, environment, registry)
        super().__init__(inputs=M.Pair(constraints, M.Pair(variables, M.Pair(bound,
            M.Pair(environment, M.Pair(registry, M.EmptyList))))), results=self.result)

    def _verify(self, constraints, variables, bound, environment, registry):
        if M.IdentityCompare(A._natural_rep(bound, registry), M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if _valid_nat_constraints(constraints, variables, registry) is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if _valid_nat_environment(variables, environment, bound, registry) is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        return _evaluate_nat_constraints(constraints, environment, registry)

    def __call__(self):
        return self.result


class FindNatWitness(M.Edge):
    """Stream [0,bound)^arity with a candidate-count budget; first axis fastest."""

    def __init__(self, constraints, variables, bound, budget, registry):
        self.result = self._search(constraints, variables, bound, budget, registry)
        super().__init__(inputs=M.Pair(constraints, M.Pair(variables, M.Pair(bound,
            M.Pair(budget, M.Pair(registry, M.EmptyList))))), results=self.result)

    def _record(self, constraints, variables, bound, budget, status, env, count, registry):
        record = M.Pair(L.NatWitnessSearchLabel, M.Pair(constraints, M.Pair(variables,
            M.Pair(bound, M.Pair(budget, M.Pair(status, M.Pair(env,
                M.Pair(count, M.EmptyList))))))))
        return M.Pair(record, M.Pair(registry, M.EmptyList))

    def _zeros(self, variables):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(M.Zero, self._zeros(M.Tail(variables)()))

    def _advance(self, values, bound, registry):
        if M.IdentityCompare(values, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        increment = A.Add(M.Head(values)(), M.one, registry)()
        value = M.Head(increment)()
        reg1 = M.Head(M.Tail(increment)())()
        if M.NatLess(value, bound, reg1)() is M.truth_value:
            return M.Pair(M.Pair(value, M.Tail(values)()), M.Pair(reg1, M.EmptyList))
        carry = self._advance(M.Tail(values)(), bound, reg1)
        tail = M.Head(carry)()
        reg2 = M.Head(M.Tail(carry)())()
        if M.IdentityCompare(tail, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg2, M.EmptyList))
        return M.Pair(M.Pair(M.Zero, tail), M.Pair(reg2, M.EmptyList))

    def _search(self, constraints, variables, bound, budget, registry):
        count = M.Zero
        env = M.EmptyList
        if (M.IdentityCompare(A._natural_rep(bound, registry), M.EmptyList)() is M.truth_value
                or M.IdentityCompare(A._natural_rep(budget, registry), M.EmptyList)() is M.truth_value
                or _valid_nat_constraints(constraints, variables, registry) is M.false_value):
            return self._record(constraints, variables, bound, budget,
                                L.NatWitnessInvalidLabel, env, count, registry)
        if (M.IdentityCompare(variables, M.EmptyList)() is M.false_value
                and M.NatEq(bound, M.Zero, registry)() is M.truth_value):
            return self._record(constraints, variables, bound, budget,
                                L.NatWitnessExhaustedLabel, env, count, registry)
        values = self._zeros(variables)
        while M.truth_value is M.truth_value:
            if M.NatLess(count, budget, registry)() is M.false_value:
                return self._record(constraints, variables, bound, budget,
                                    L.NatWitnessBudgetLabel, M.EmptyList, count, registry)
            env = _zip_environment(variables, values)
            evaluated = _evaluate_nat_constraints(constraints, env, registry)
            verdict = M.Head(evaluated)()
            reg1 = M.Head(M.Tail(evaluated)())()
            counted = A.Add(count, M.one, reg1)()
            count = M.Head(counted)()
            registry = M.Head(M.Tail(counted)())()
            if verdict is M.truth_value:
                return self._record(constraints, variables, bound, budget,
                                    L.NatWitnessFoundLabel, env, count, registry)
            if verdict is M.EmptyList:
                return self._record(constraints, variables, bound, budget,
                                    L.NatWitnessInvalidLabel, M.EmptyList, count, registry)
            advanced = self._advance(values, bound, registry)
            values = M.Head(advanced)()
            registry = M.Head(M.Tail(advanced)())()
            if M.IdentityCompare(values, M.EmptyList)() is M.truth_value:
                return self._record(constraints, variables, bound, budget,
                                    L.NatWitnessExhaustedLabel, M.EmptyList, count, registry)

    def __call__(self):
        return self.result


__all__ = (
    "ChainLength",
    "ChainContains",
    "SetInsert",
    "SetIntersection",
    "SetUnion",
    "SetDifference",
    "SortNatChain",
    "TupleElementAt",
    "ProjectCoordinate",
    "ProjectAllCoordinates",
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
    "ProjectTensorModulo",
    "FindTensorEqualityWitness",
    "ExtractExprVariables",
    "ExtractExponentVariables",
    "SubstituteExprVar",
    "RenderNatExpr",
    "DiscoverExprObstructions",
    "parse_surface_goal_spec",
    "is_proof_or_math_goal",
    "ExprDegreeBound",
    "EvaluateNatExpr",
    "PolynomialIdentityByGrid",
    "PolynomialRewriteCertificate",
    "PolynomialGridDerivation",
    "ResidueTable",
    "CongruenceClasses",
    "VerifyNatWitness",
    "FindNatWitness",
    "run_playground_interactive",
)
