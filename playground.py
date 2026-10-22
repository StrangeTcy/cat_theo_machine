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


def _chain_has_var(chain, var_atom):
    cur = chain
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        if M.Compare(M.Head(cur)(), var_atom)() is M.truth_value:
            return M.truth_value
        cur = M.Tail(cur)()
    return M.false_value


def _chain_append_end(chain, elem):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return M.Pair(elem, M.EmptyList)
    return M.Pair(M.Head(chain)(), _chain_append_end(M.Tail(chain)(), elem))


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


def _chains_disjoint_vars(chain_a, chain_b):
    cur = chain_a
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        if _chain_has_var(chain_b, M.Head(cur)()) is M.truth_value:
            return M.false_value
        cur = M.Tail(cur)()
    return M.truth_value


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


def _split_independent_summands(term, registry):
    """
    Splits ExprAdd(left, right) into a chain of summands when left and right
    each contain at least one variable and their variable sets are disjoint.
    """
    if M.IsPair(term)() is M.false_value:
        return M.Pair(term, M.EmptyList)
    head, args = _expr_head_args(term)
    if M.IdentityCompare(head, L.ExprAddLabel)() is M.false_value:
        return M.Pair(term, M.EmptyList)
    if _exact_arity(args, 2) is M.false_value:
        return M.Pair(term, M.EmptyList)
    left = M.Head(args)()
    right = M.Head(M.Tail(args)())()
    left_vars = M.Head(ExtractExprVariables(left, registry)())()
    right_vars = M.Head(ExtractExprVariables(right, registry)())()
    if M.IdentityCompare(left_vars, M.EmptyList)() is M.truth_value:
        return M.Pair(term, M.EmptyList)
    if M.IdentityCompare(right_vars, M.EmptyList)() is M.truth_value:
        return M.Pair(term, M.EmptyList)
    if _chains_disjoint_vars(left_vars, right_vars) is M.false_value:
        return M.Pair(term, M.EmptyList)
    left_parts = _split_independent_summands(left, registry)
    right_parts = _split_independent_summands(right, registry)
    cur = right_parts
    out = left_parts
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        out = _chain_append_end(out, M.Head(cur)())
        cur = M.Tail(cur)()
    return out


def _is_prime_in_domain(n_nat, domain_chain, registry):
    cur = M.Tail(M.Tail(domain_chain)())()
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        d = M.Head(cur)()
        if M.NatLess(d, n_nat, registry)() is M.false_value:
            break
        if A.Divides(d, n_nat, registry)() is M.truth_value:
            return M.false_value
        cur = M.Tail(cur)()
    return M.truth_value


def _prime_divisors_of_mod(m_nat, domain_chain, registry):
    out = M.EmptyList
    cur = M.Tail(M.Tail(domain_chain)())()
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        d = M.Head(cur)()
        if M.NatLess(m_nat, d, registry)() is M.truth_value:
            break
        if (
            A.Divides(d, m_nat, registry)() is M.truth_value
            and _is_prime_in_domain(d, domain_chain, registry) is M.truth_value
        ):
            out = _chain_append_end(out, d)
        cur = M.Tail(cur)()
    if _is_prime_in_domain(m_nat, domain_chain, registry) is M.truth_value:
        if ChainContains(out, m_nat, registry)() is M.false_value:
            out = _chain_append_end(out, m_nat)
    return out


class DiscoverExprObstructions(M.Edge):
    """
    Generic, expression-driven Cartesian playground sweep over candidate moduli.
    Given any two admitted polynomial expressions `lhs` and `rhs`, evaluates
    their component images over the ground domain 0..bound_nat-1 and tests
    for disjoint residue images across `moduli_chain`:
      1. Unrestricted domain: Image(lhs mod m) /\\ Image(rhs mod m) == empty
      2. Prime-divisor unit subdomains (for prime p | m, subdomain p does not divide v):
         - One-sided (`lhs_not_divisible`): Image(lhs mod m | p does not divide lhs_vars)
           disjoint from unrestricted Image(rhs mod m)
         - Two-sided (`all_not_divisible`): Image(lhs mod m | p does not divide lhs_vars)
           disjoint from Image(rhs mod m | p does not divide rhs_vars)
    Returns Pair(discoveries_chain, Pair(registry, EmptyList)).
    """

    def __init__(
        self,
        lhs,
        rhs,
        bound_nat,
        moduli_chain,
        registry,
        eval_cache=None,
        max_discoveries=2,
    ):
        self.registry = registry
        self.result = self._discover(
            lhs, rhs, bound_nat, moduli_chain, registry, eval_cache, max_discoveries
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
        self, lhs, rhs, bound_nat, moduli_chain, registry, eval_cache, max_discoveries
    ):
        range_res = BuildNatRange(M.Zero, bound_nat, registry)()
        domain = M.Head(range_res)()
        reg = M.Head(M.Tail(range_res)())()

        lhs_parts = _split_independent_summands(lhs, reg)
        rhs_parts = _split_independent_summands(rhs, reg)

        canon_var = M.Char("_pg_v0")
        unary_cache = eval_cache if eval_cache is not None else []

        def prepare_component_table(comp_term, cur_reg):
            comp_vars = M.Head(ExtractExprVariables(comp_term, cur_reg)())()
            len_res = ChainLength(comp_vars, cur_reg)()
            arity_nat = M.Head(len_res)()
            r1 = M.Head(M.Tail(len_res)())()
            arity_val = M.NatRepOf(arity_nat, r1)()()

            if arity_val == 0:
                ev = EvaluateNatExpr(comp_term, M.EmptyList, r1)()
                val = M.Head(ev)()
                r2 = M.Head(M.Tail(ev)())()
                t_id = ("const", len(unary_cache))
                state = {"rows": [(M.EmptyList, val)], "rem_domain": M.EmptyList, "term": comp_term}
                unary_cache.append((comp_term, state, t_id))
                return state, 0, t_id, r2

            if arity_val == 1:
                v_atom = M.Head(comp_vars)()
                canon_term = M.Head(
                    SubstituteExprVar(comp_term, v_atom, canon_var, r1)()
                )()
                for cached_term, cached_state, cached_id in unary_cache:
                    if M.Compare(cached_term, canon_term)() is M.truth_value:
                        return cached_state, 1, cached_id, r1
                t_id = ("unary", len(unary_cache))
                state = {
                    "rows": [],
                    "rem_domain": domain,
                    "term": canon_term,
                    "var": canon_var,
                }
                unary_cache.append((canon_term, state, t_id))
                return state, 1, t_id, r1

            # Multi-variable non-separable component: evaluate over ProductOfDomains
            dom_chains = M.EmptyList
            for _ in range(arity_val):
                dom_chains = M.Pair(domain, dom_chains)
            tuples = ProductOfDomains(dom_chains)()
            rows = []
            cur_t = tuples
            r_cur = r1
            while M.IdentityCompare(cur_t, M.EmptyList)() is M.false_value:
                tup = M.Head(cur_t)()
                env = _zip_environment(comp_vars, tup)
                ev = EvaluateNatExpr(comp_term, env, r_cur)()
                out_val = M.Head(ev)()
                r_cur = M.Head(M.Tail(ev)())()
                rows.append((tup, out_val))
                cur_t = M.Tail(cur_t)()
            t_id = ("multi", len(unary_cache))
            state = {"rows": rows, "rem_domain": M.EmptyList, "term": comp_term}
            unary_cache.append((comp_term, state, t_id))
            return state, arity_val, t_id, r_cur

        def ensure_rows_up_to(state, arity_val, m_nat, cur_reg):
            if arity_val != 1:
                return state["rows"], cur_reg
            cur_d = state["rem_domain"]
            r_c = cur_reg
            v_atom = state["var"]
            c_term = state["term"]
            while M.IdentityCompare(cur_d, M.EmptyList)() is M.false_value:
                d_val = M.Head(cur_d)()
                if M.NatLess(d_val, m_nat, r_c)() is M.false_value:
                    break
                env = M.Pair(
                    M.Pair(v_atom, M.Pair(d_val, M.EmptyList)), M.EmptyList
                )
                ev = EvaluateNatExpr(c_term, env, r_c)()
                out_val = M.Head(ev)()
                r_c = M.Head(M.Tail(ev)())()
                state["rows"].append((M.Pair(d_val, M.EmptyList), out_val))
                cur_d = M.Tail(cur_d)()
            state["rem_domain"] = cur_d
            return state["rows"], r_c

        lhs_tables = []
        cur_p = lhs_parts
        while M.IdentityCompare(cur_p, M.EmptyList)() is M.false_value:
            part = M.Head(cur_p)()
            state, arity_val, t_id, reg = prepare_component_table(part, reg)
            lhs_tables.append((part, state, arity_val, t_id))
            cur_p = M.Tail(cur_p)()

        rhs_tables = []
        cur_p = rhs_parts
        while M.IdentityCompare(cur_p, M.EmptyList)() is M.false_value:
            part = M.Head(cur_p)()
            state, arity_val, t_id, reg = prepare_component_table(part, reg)
            rhs_tables.append((part, state, arity_val, t_id))
            cur_p = M.Tail(cur_p)()

        def tuple_all_under_mod(tup, m_nat, cur_reg):
            cur_v = tup
            while M.IdentityCompare(cur_v, M.EmptyList)() is M.false_value:
                v_nat = M.Head(cur_v)()
                if M.NatLess(v_nat, m_nat, cur_reg)() is M.false_value:
                    return M.false_value
                cur_v = M.Tail(cur_v)()
            return M.truth_value

        def tuple_none_divisible(tup, div_nat, cur_reg):
            if M.IdentityCompare(div_nat, M.Zero)() is M.truth_value:
                return M.truth_value
            cur_v = tup
            while M.IdentityCompare(cur_v, M.EmptyList)() is M.false_value:
                v_nat = M.Head(cur_v)()
                if A.Divides(div_nat, v_nat, cur_reg)() is M.truth_value:
                    return M.false_value
                cur_v = M.Tail(cur_v)()
            return M.truth_value

        discoveries = M.EmptyList
        disc_count = 0
        cur_m = moduli_chain
        while M.IdentityCompare(cur_m, M.EmptyList)() is M.false_value:
            if max_discoveries is not None and disc_count >= max_discoveries:
                break
            m_nat = M.Head(cur_m)()

            # Pre-reduce each unique component table modulo m_nat once
            mod_table_cache = {}
            proj_div_cache = {}

            def get_mod_rows(t_id, state, arity_val, cur_reg):
                if t_id in mod_table_cache:
                    return mod_table_cache[t_id], cur_reg
                rows, r_c = ensure_rows_up_to(state, arity_val, m_nat, cur_reg)
                m_rows = []
                for tup, out_val in rows:
                    if arity_val <= 1 or tuple_all_under_mod(tup, m_nat, r_c) is M.truth_value:
                        mod_res = A.Modulo(out_val, m_nat, r_c)()
                        rem_val = M.Head(mod_res)()
                        r_c = M.Head(M.Tail(mod_res)())()
                        m_rows.append((tup, rem_val))
                mod_table_cache[t_id] = m_rows
                return m_rows, r_c

            def project_one_table(t_id, state, arity_val, div_key, div_nat, cur_reg):
                cache_key = (t_id, div_key)
                if cache_key in proj_div_cache:
                    img_set, comp_flag = proj_div_cache[cache_key]
                    return img_set, comp_flag, cur_reg
                m_rows, r_c = get_mod_rows(t_id, state, arity_val, cur_reg)
                img_set = M.EmptyList
                kept_count = 0
                for tup, rem_val in m_rows:
                    if arity_val == 0 or tuple_none_divisible(tup, div_nat, r_c) is M.truth_value:
                        img_set = SetInsert(rem_val, img_set, r_c)()
                        kept_count += 1
                comp_flag = M.false_value
                if arity_val >= 1 and kept_count > 0:
                    len_res = ChainLength(img_set, r_c)()
                    img_len = M.Head(len_res)()
                    r_c = M.Head(M.Tail(len_res)())()
                    kept_res = M.NatFromRep(M.GMPRep(kept_count), r_c)()
                    kept_nat = M.Head(kept_res)()
                    r_c = M.Head(M.Tail(kept_res)())()
                    if M.NatLess(img_len, kept_nat, r_c)() is M.truth_value:
                        comp_flag = M.truth_value
                proj_div_cache[cache_key] = (img_set, comp_flag)
                return img_set, comp_flag, r_c

            def project_tables_mod(tables, div_key, div_nat, cur_reg):
                comp_sets = []
                any_compressed = M.false_value
                r_c = cur_reg
                for _part, state, arity_val, t_id in tables:
                    img_set, comp_flag, r_c = project_one_table(
                        t_id, state, arity_val, div_key, div_nat, r_c
                    )
                    if comp_flag is M.truth_value:
                        any_compressed = M.truth_value
                    comp_sets.append(img_set)

                if not comp_sets:
                    return M.EmptyList, M.false_value, r_c

                acc_set = comp_sets[0]
                for next_set in comp_sets[1:]:
                    if (
                        M.IdentityCompare(acc_set, M.EmptyList)() is M.truth_value
                        or M.IdentityCompare(next_set, M.EmptyList)() is M.truth_value
                    ):
                        return M.EmptyList, any_compressed, r_c
                    prod_pairs = ProductOfDomains(
                        M.Pair(acc_set, M.Pair(next_set, M.EmptyList))
                    )()

                    def add_pair_fn(pair_tup, reg_inner):
                        u = M.Head(pair_tup)()
                        v = M.Head(M.Tail(pair_tup)())()
                        return A.Add(u, v, reg_inner)()

                    sum_map = MapDomain(prod_pairs, add_pair_fn, r_c)()
                    sum_vals = M.Head(sum_map)()
                    r_c = M.Head(M.Tail(M.Tail(sum_map)())())()
                    proj_sum = ProjectCongruence(sum_vals, m_nat, r_c)()
                    acc_set = M.Head(proj_sum)()
                    r_c = M.Head(M.Tail(proj_sum)())()

                return acc_set, any_compressed, r_c

            lhs_all, _lhs_comp, reg = project_tables_mod(
                lhs_tables, 0, M.Zero, reg
            )
            rhs_all, rhs_all_comp, reg = project_tables_mod(
                rhs_tables, 0, M.Zero, reg
            )

            # Clause 1: Unrestricted domain disjointness
            if (
                M.IdentityCompare(lhs_all, M.EmptyList)() is M.false_value
                and M.IdentityCompare(rhs_all, M.EmptyList)() is M.false_value
            ):
                rel_all = EvaluateSetRelation(rhs_all, lhs_all, reg)()
                disj_all = M.Head(rel_all)()
                reg = M.Head(M.Tail(M.Tail(rel_all)())())()
                if disj_all is M.truth_value:
                    rec = M.Pair(
                        L.DiscoveredInvariantLabel,
                        M.Pair(
                            m_nat,
                            M.Pair(
                                rhs_all,
                                M.Pair(
                                    lhs_all,
                                    M.Pair(
                                        M.truth_value,
                                        M.Pair(
                                            M.Char("unrestricted"),
                                            M.Pair(M.Zero, M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    )
                    discoveries = _chain_append_end(discoveries, rec)
                    disc_count += 1
                    break

            # Clauses 2 & 3: Prime-divisor unit subdomains (p | m, p does not divide v)
            p_divs = _prime_divisors_of_mod(m_nat, domain, reg)
            cur_p = p_divs
            while M.IdentityCompare(cur_p, M.EmptyList)() is M.false_value:
                p_nat = M.Head(cur_p)()
                p_key = M.NatRepOf(p_nat, reg)()()
                lhs_p, lhs_p_comp, reg = project_tables_mod(
                    lhs_tables, p_key, p_nat, reg
                )
                if (
                    M.IdentityCompare(lhs_p, M.EmptyList)() is M.false_value
                    and lhs_p_comp is M.truth_value
                ):
                    clause2_hit = M.false_value
                    if rhs_all_comp is M.truth_value:
                        rel_c2 = EvaluateSetRelation(rhs_all, lhs_p, reg)()
                        disj_c2 = M.Head(rel_c2)()
                        reg = M.Head(M.Tail(M.Tail(rel_c2)())())()
                        if disj_c2 is M.truth_value:
                            clause2_hit = M.truth_value
                            rec = M.Pair(
                                L.DiscoveredInvariantLabel,
                                M.Pair(
                                    m_nat,
                                    M.Pair(
                                        rhs_all,
                                        M.Pair(
                                            lhs_p,
                                            M.Pair(
                                                M.truth_value,
                                                M.Pair(
                                                    M.Char("lhs_not_divisible"),
                                                    M.Pair(p_nat, M.EmptyList),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            )
                            discoveries = _chain_append_end(discoveries, rec)
                            disc_count += 1

                    if clause2_hit is M.false_value:
                        rhs_p, rhs_p_comp, reg = project_tables_mod(
                            rhs_tables, p_key, p_nat, reg
                        )
                        if (
                            M.IdentityCompare(rhs_p, M.EmptyList)() is M.false_value
                            and rhs_p_comp is M.truth_value
                        ):
                            rel_c3 = EvaluateSetRelation(rhs_p, lhs_p, reg)()
                            disj_c3 = M.Head(rel_c3)()
                            reg = M.Head(M.Tail(M.Tail(rel_c3)())())()
                            if disj_c3 is M.truth_value:
                                rec = M.Pair(
                                    L.DiscoveredInvariantLabel,
                                    M.Pair(
                                        m_nat,
                                        M.Pair(
                                            rhs_p,
                                            M.Pair(
                                                lhs_p,
                                                M.Pair(
                                                    M.truth_value,
                                                    M.Pair(
                                                        M.Char("all_not_divisible"),
                                                        M.Pair(p_nat, M.EmptyList),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                )
                                discoveries = _chain_append_end(discoveries, rec)
                                disc_count += 1
                cur_p = M.Tail(cur_p)()

            cur_m = M.Tail(cur_m)()

        return M.Pair(discoveries, M.Pair(reg, M.EmptyList))

    def __call__(self):
        return self.result


_STOP_WORDS = {
    "prove", "that", "for", "all", "every", "any", "each", "positive", "nonzero",
    "non-zero", "natural", "naturals", "integer", "integers", "number", "numbers",
    "and", "or", "if", "then", "when", "where", "with", "has", "have", "no",
    "solution", "solutions", "is", "are", "in", "of", "the", "a", "an", "to",
    "show", "claim", "conjecture", "check", "verify", "true", "false", "hold",
    "holds", "there", "exist", "exists", "cannot", "never", "impossible",
}


def is_proof_or_math_goal(text):
    """
    Returns True when a surface line is a proof request or contains mathematical
    relational/algebraic structure suitable for lemma exploration.
    """
    if not text:
        return False
    low = text.strip().lower()
    for prefix in (
        "prove", "show", "claim", "conjecture", "check", "verify",
        "is it true", "for all", "for every", "for any", "for each",
        "if ", "whenever ", "solve ",
    ):
        if low.startswith(prefix):
            return True
    for sym in ("=", "!=", "<", ">", "^", "+", "*"):
        if sym in low:
            return True
    return False


def _tokenize_math_surface(text):
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace() or ch in ",;:.?!\"'":
            i += 1
            continue
        if i + 1 < n and text[i : i + 2] in (">=", "<=", "!=", "=="):
            tokens.append(text[i : i + 2])
            i += 2
            continue
        if ch in "+*^()=<>":
            tokens.append(ch)
            i += 1
            continue
        if ch.isdigit():
            j = i
            while j < n and text[j].isdigit():
                j += 1
            tokens.append(text[i:j])
            # Support implicit multiplication like 4z -> 4 * z
            if j < n and text[j].isalpha():
                tokens.append("*")
            i = j
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] in "_-"):
                j += 1
            tokens.append(text[i:j].lower())
            i = j
            continue
        i += 1
    return tokens


def _is_expr_ident(tok):
    return tok.isalpha() and tok not in _STOP_WORDS and len(tok) <= 4


def _extract_contiguous_lhs(tokens_before_eq):
    """
    Walks left from `=` to extract the contiguous infix algebraic expression
    immediately preceding `=`.
    """
    if not tokens_before_eq:
        return []
    out = []
    depth = 0
    expect_operand = True
    i = len(tokens_before_eq) - 1
    while i >= 0:
        tok = tokens_before_eq[i]
        if tok == ")":
            if not expect_operand:
                break
            depth += 1
            out.append(tok)
            expect_operand = True
        elif tok == "(":
            if expect_operand or depth <= 0:
                break
            depth -= 1
            out.append(tok)
            expect_operand = False
        elif tok in ("+", "*", "^"):
            if expect_operand:
                break
            out.append(tok)
            expect_operand = True
        elif tok.isdigit() or _is_expr_ident(tok):
            if not expect_operand:
                break
            out.append(tok)
            expect_operand = False
        else:
            break
        i -= 1
    out.reverse()
    while out and out[0] in ("+", "*", "^"):
        out.pop(0)
    return out


def _extract_contiguous_rhs(tokens_after_eq):
    """
    Walks right from `=` to extract the contiguous infix algebraic expression
    immediately following `=`.
    """
    if not tokens_after_eq:
        return []
    out = []
    depth = 0
    expect_operand = True
    for tok in tokens_after_eq:
        if tok == "(":
            if not expect_operand:
                break
            depth += 1
            out.append(tok)
            expect_operand = True
        elif tok == ")":
            if expect_operand or depth <= 0:
                break
            depth -= 1
            out.append(tok)
            expect_operand = False
        elif tok in ("+", "*", "^"):
            if expect_operand:
                break
            out.append(tok)
            expect_operand = True
        elif tok.isdigit() or _is_expr_ident(tok):
            if not expect_operand:
                break
            out.append(tok)
            expect_operand = False
        else:
            break
    while out and out[-1] in ("+", "*", "^"):
        out.pop()
    return out


def parse_surface_goal_spec(text, registry):
    """
    Parses a surface mathematical proof goal into a machine-native specification:
      - lhs, rhs: machine Expr* ASTs
      - base_vars: chain of base polynomial variable Char atoms
      - exp_vars: chain of parametric exponent variable Char atoms
      - param_min: dict mapping exponent variable name -> minimum integer value
      - no_solutions: bool (True for obstruction / non-existence goals)
      - positive_only: bool (True when positive / nonzero integers specified)
      - registry: updated constructor registry
    Returns None if no equation is present.
    """
    if not text:
        return None
    tokens = _tokenize_math_surface(text)
    eq_idx = None
    eq_op = None
    for idx, tok in enumerate(tokens):
        if tok in ("=", "==", "!="):
            eq_idx = idx
            eq_op = tok
            break
    if eq_idx is None:
        return None

    before = tokens[:eq_idx]
    after = tokens[eq_idx + 1 :]

    # Scan for parameter bounds before `=`, e.g. `n > 2` or `n >= 3`
    param_min = {}
    for idx in range(len(before) - 2):
        v_tok, op_tok, num_tok = before[idx], before[idx + 1], before[idx + 2]
        if _is_expr_ident(v_tok) and num_tok.isdigit():
            if op_tok == ">":
                param_min[v_tok] = int(num_tok) + 1
            elif op_tok == ">=":
                param_min[v_tok] = int(num_tok)

    lhs_tokens = _extract_contiguous_lhs(before)
    rhs_tokens = _extract_contiguous_rhs(after)
    if not lhs_tokens or not rhs_tokens:
        return None

    char_map = {}
    cur_reg = registry

    def get_char(name):
        if name not in char_map:
            char_map[name] = M.Char(name)
        return char_map[name]

    def get_nat(val):
        nonlocal cur_reg
        res = M.NatFromRep(M.GMPRep(int(val)), cur_reg)()
        cur_reg = M.Head(M.Tail(res)())()
        return M.Head(res)()

    def parse_tokens(tok_list):
        pos = [0]

        def parse_add():
            node = parse_mul()
            if node is None:
                return None
            while pos[0] < len(tok_list) and tok_list[pos[0]] == "+":
                pos[0] += 1
                right = parse_mul()
                if right is None:
                    return None
                node = M.Pair(
                    L.ExprAddLabel, M.Pair(node, M.Pair(right, M.EmptyList))
                )
            return node

        def parse_mul():
            node = parse_pow()
            if node is None:
                return None
            while pos[0] < len(tok_list) and tok_list[pos[0]] == "*":
                pos[0] += 1
                right = parse_pow()
                if right is None:
                    return None
                node = M.Pair(
                    L.ExprMulLabel, M.Pair(node, M.Pair(right, M.EmptyList))
                )
            return node

        def parse_pow():
            base = parse_primary()
            if base is None:
                return None
            if pos[0] < len(tok_list) and tok_list[pos[0]] == "^":
                pos[0] += 1
                exp = parse_primary()
                if exp is None:
                    return None
                return M.Pair(
                    L.ExprPowLabel, M.Pair(base, M.Pair(exp, M.EmptyList))
                )
            return base

        def parse_primary():
            if pos[0] >= len(tok_list):
                return None
            tok = tok_list[pos[0]]
            if tok == "(":
                pos[0] += 1
                inner = parse_add()
                if pos[0] >= len(tok_list) or tok_list[pos[0]] != ")":
                    return None
                pos[0] += 1
                return inner
            if tok.isdigit():
                pos[0] += 1
                return get_nat(int(tok))
            if _is_expr_ident(tok):
                pos[0] += 1
                return get_char(tok)
            return None

        parsed = parse_add()
        if parsed is None or pos[0] != len(tok_list):
            return None
        return parsed

    lhs_ast = parse_tokens(lhs_tokens)
    rhs_ast = parse_tokens(rhs_tokens)
    if lhs_ast is None or rhs_ast is None:
        return None

    eq_node = M.Pair(
        L.ExprEqLabel, M.Pair(lhs_ast, M.Pair(rhs_ast, M.EmptyList))
    )
    all_vars = M.Head(ExtractExprVariables(eq_node, cur_reg)())()
    exp_vars = M.Head(ExtractExponentVariables(eq_node, cur_reg)())()

    base_vars = M.EmptyList
    cur_v = all_vars
    while M.IdentityCompare(cur_v, M.EmptyList)() is M.false_value:
        v_atom = M.Head(cur_v)()
        if _chain_has_var(exp_vars, v_atom) is M.false_value:
            base_vars = _chain_append_end(base_vars, v_atom)
        cur_v = M.Tail(cur_v)()

    no_solutions = eq_op == "!=" or any(
        w in tokens for w in ("no", "impossible", "cannot", "never")
    )
    positive_only = any(w in tokens for w in ("positive", "nonzero", "non-zero"))

    return {
        "lhs": lhs_ast,
        "rhs": rhs_ast,
        "base_vars": base_vars,
        "exp_vars": exp_vars,
        "param_min": param_min,
        "no_solutions": no_solutions,
        "positive_only": positive_only,
        "registry": cur_reg,
    }


def _set_chain_to_sorted_ints(set_chain, registry):
    vals = []
    cur = set_chain
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        rep = M.NatRepOf(M.Head(cur)(), registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            v = rep()
            if v not in vals:
                vals.append(v)
        cur = M.Tail(cur)()
    return sorted(vals)


def _format_set_chain(set_chain, registry):
    return "{" + ", ".join(map(str, _set_chain_to_sorted_ints(set_chain, registry))) + "}"


def _vars_chain_to_names(vars_chain):
    names = []
    cur = vars_chain
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        v = M.Head(cur)()
        names.append(str(v()))
        cur = M.Tail(cur)()
    return names


def _find_concrete_witness_from_tables(
    lhs, rhs, base_vars, bound_nat, positive_only, registry, eval_cache=None
):
    """
    Evaluates whether a concrete solution to lhs = rhs exists in the bounded
    ground domain [1..5] (if positive_only) or [0..5] using the machine's
    EvaluateNatExpr (or precomputed eval_cache) and NatEq.
    """
    var_names = _vars_chain_to_names(base_vars)
    if not var_names:
        return None, registry

    lhs_parts = _split_independent_summands(lhs, registry)
    rhs_parts = _split_independent_summands(rhs, registry)

    six_res = M.NatFromRep(M.GMPRep(6), registry)()
    six_nat = M.Head(six_res)()
    reg = M.Head(M.Tail(six_res)())()
    w_bound = (
        bound_nat
        if M.NatLess(bound_nat, six_nat, reg)() is M.truth_value
        else six_nat
    )

    canon_var = M.Char("_pg_v0")

    def eval_unary_part(part_term, cur_reg):
        p_vars = M.Head(ExtractExprVariables(part_term, cur_reg)())()
        if M.IdentityCompare(p_vars, M.EmptyList)() is M.truth_value:
            return None, None, cur_reg
        if M.IdentityCompare(M.Tail(p_vars)(), M.EmptyList)() is M.false_value:
            return None, None, cur_reg
        v_atom = M.Head(p_vars)()
        r_c = cur_reg
        if eval_cache is not None:
            canon_term = M.Head(
                SubstituteExprVar(part_term, v_atom, canon_var, r_c)()
            )()
            for item in eval_cache:
                cached_term, cached_state = item[0], item[1]
                if M.Compare(cached_term, canon_term)() is M.truth_value:
                    cur_d = cached_state["rem_domain"]
                    while M.IdentityCompare(cur_d, M.EmptyList)() is M.false_value:
                        d_val = M.Head(cur_d)()
                        if M.NatLess(d_val, w_bound, r_c)() is M.false_value:
                            break
                        env = M.Pair(
                            M.Pair(canon_var, M.Pair(d_val, M.EmptyList)),
                            M.EmptyList,
                        )
                        ev = EvaluateNatExpr(canon_term, env, r_c)()
                        out_val = M.Head(ev)()
                        r_c = M.Head(M.Tail(ev)())()
                        cached_state["rows"].append(
                            (M.Pair(d_val, M.EmptyList), out_val)
                        )
                        cur_d = M.Tail(cur_d)()
                    cached_state["rem_domain"] = cur_d
                    entries = []
                    for tup, val_nat in cached_state["rows"]:
                        d_nat = M.Head(tup)()
                        if positive_only and M.IdentityCompare(d_nat, M.Zero)() is M.truth_value:
                            continue
                        if M.NatLess(d_nat, w_bound, r_c)() is M.false_value:
                            break
                        entries.append((d_nat, val_nat))
                    return v_atom, entries, r_c

        range_res = BuildNatRange(M.Zero, w_bound, r_c)()
        domain = M.Head(range_res)()
        r_c = M.Head(M.Tail(range_res)())()
        if positive_only and M.IdentityCompare(domain, M.EmptyList)() is M.false_value:
            domain = M.Tail(domain)()
        entries = []
        cur_d = domain
        while M.IdentityCompare(cur_d, M.EmptyList)() is M.false_value:
            d_nat = M.Head(cur_d)()
            env = M.Pair(M.Pair(v_atom, M.Pair(d_nat, M.EmptyList)), M.EmptyList)
            ev = EvaluateNatExpr(part_term, env, r_c)()
            val_nat = M.Head(ev)()
            r_c = M.Head(M.Tail(ev)())()
            entries.append((d_nat, val_nat))
            cur_d = M.Tail(cur_d)()
        return v_atom, entries, r_c

    lhs_u = []
    cur_p = lhs_parts
    all_unary = True
    while M.IdentityCompare(cur_p, M.EmptyList)() is M.false_value:
        v_atom, entries, reg = eval_unary_part(M.Head(cur_p)(), reg)
        if v_atom is None:
            all_unary = False
            break
        lhs_u.append((v_atom, entries))
        cur_p = M.Tail(cur_p)()

    rhs_u = []
    if all_unary and M.IdentityCompare(M.Tail(rhs_parts)(), M.EmptyList)() is M.truth_value:
        v_atom, entries, reg = eval_unary_part(M.Head(rhs_parts)(), reg)
        if v_atom is not None:
            rhs_u.append((v_atom, entries))
        else:
            all_unary = False
    else:
        all_unary = False

    if all_unary and len(lhs_u) == 2 and len(rhs_u) == 1:
        vx, x_entries = lhs_u[0]
        vy, y_entries = lhs_u[1]
        vz, z_entries = rhs_u[0]
        for i_x, (dx, val_x) in enumerate(x_entries):
            for dy, val_y in y_entries[i_x:]:
                sum_res = A.Add(val_x, val_y, reg)()
                sum_xy = M.Head(sum_res)()
                reg = M.Head(M.Tail(sum_res)())()
                for dz, val_z in z_entries:
                    if M.NatEq(sum_xy, val_z, reg)() is M.truth_value:
                        return [
                            (str(vx()), M.NatRepOf(dx, reg)()()),
                            (str(vy()), M.NatRepOf(dy, reg)()()),
                            (str(vz()), M.NatRepOf(dz, reg)()()),
                        ], reg
        return None, reg

    return None, reg


def _format_discoveries_for_equation(
    lhs,
    rhs,
    discoveries,
    moduli_chain,
    bound_val,
    witness,
    reg,
    indent="  ",
):
    lhs_str = RenderNatExpr(lhs, reg)
    rhs_str = RenderNatExpr(rhs, reg)
    lhs_vars = M.Head(ExtractExprVariables(lhs, reg)())()
    rhs_vars = M.Head(ExtractExprVariables(rhs, reg)())()
    lhs_var_names = _vars_chain_to_names(lhs_vars)
    rhs_var_names = _vars_chain_to_names(rhs_vars)
    all_var_names = _vars_chain_to_names(_chain_merge_unique(lhs_vars, rhs_vars))

    tested_mods = _set_chain_to_sorted_ints(moduli_chain, reg)
    lines = []
    if witness is not None:
        w_str = ", ".join(f"{k} = {v}" for k, v in witness)
        lines.append(
            f"{indent}- Bounded Witness Search (1..{bound_val - 1}): Counterexample solution found at ({w_str}) where {lhs_str} = {rhs_str}."
        )
    else:
        lines.append(
            f"{indent}- Bounded Witness Search (domain 1..{bound_val - 1}): 0 solutions found; sweeping moduli {tested_mods} for structural invariants."
        )

    if M.IdentityCompare(discoveries, M.EmptyList)() is M.truth_value:
        lines.append(
            f"{indent}- No single-modulus residue obstruction found in moduli {tested_mods}."
        )
        return lines

    cur = discoveries
    shown = 0
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value and shown < 2:
        rec = M.Head(cur)()
        mod_nat = M.Head(M.Tail(rec)())()
        rhs_set = M.Head(M.Tail(M.Tail(rec)())())()
        lhs_set = M.Head(M.Tail(M.Tail(M.Tail(rec)())())())()
        tail_meta = M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(rec)())())())())()
        filter_kind = "lhs_not_divisible"
        div_val = 2
        if M.IdentityCompare(tail_meta, M.EmptyList)() is M.false_value:
            filter_kind = str(M.Head(tail_meta)()())
            div_nat = M.Head(M.Tail(tail_meta)())()
            if M.IdentityCompare(div_nat, M.Zero)() is M.false_value:
                div_val = M.NatRepOf(div_nat, reg)()()

        mod_val = M.NatRepOf(mod_nat, reg)()()
        rhs_img_str = _format_set_chain(rhs_set, reg)
        lhs_img_str = _format_set_chain(lhs_set, reg)

        rhs_arity = len(rhs_var_names)
        lhs_arity = len(lhs_var_names)
        rhs_args_str = ", ".join(rhs_var_names)
        lhs_args_str = ", ".join(lhs_var_names)

        if filter_kind == "unrestricted":
            lines.append(
                f"{indent}- Separating Modulus m = {mod_val} (unrestricted domain):"
            )
            lines.append(
                f"{indent}  * {rhs_arity}-ary Image Projection: f([{rhs_args_str}]) = ({rhs_str}) mod {mod_val} -> {rhs_img_str}"
            )
            lines.append(
                f"{indent}  * {lhs_arity}-ary Image Projection: g([{lhs_args_str}]) = ({lhs_str}) mod {mod_val} -> {lhs_img_str}"
            )
            lines.append(
                f"{indent}  * Disjoint Image Regularity: {rhs_img_str} /\\ {lhs_img_str} = empty"
            )
            lines.append(
                f"{indent}  * Candidate Lemma (mod_{mod_val}_global_obstruction): {lhs_str} = {rhs_str} has no integer solutions since ({lhs_str}) mod {mod_val} in {lhs_img_str} and ({rhs_str}) mod {mod_val} in {rhs_img_str} are disjoint."
            )
        elif filter_kind == "lhs_not_divisible":
            sub_desc = (
                "odd subdomain"
                if div_val == 2
                else f"subdomain ({div_val} does not divide {lhs_args_str})"
            )
            cond_desc = (
                f"odd {lhs_args_str}"
                if div_val == 2
                else f"{div_val} dividing neither " + " nor ".join(lhs_var_names)
            )
            prod_lhs = "*".join(lhs_var_names)
            lines.append(
                f"{indent}- Separating Modulus m = {mod_val} ({sub_desc}):"
            )
            lines.append(
                f"{indent}  * {rhs_arity}-ary Image Projection: f([{rhs_args_str}]) = {rhs_str} mod {mod_val} -> {rhs_img_str}"
            )
            lines.append(
                f"{indent}  * {lhs_arity}-ary Image Projection: g([{lhs_args_str}]) = ({lhs_str}) mod {mod_val} over {sub_desc} -> {lhs_img_str}"
            )
            lines.append(
                f"{indent}  * Disjoint Image Regularity: {rhs_img_str} /\\ {lhs_img_str} = empty"
            )
            lines.append(
                f"{indent}  * Obstruction Invariant: {lhs_str} = {rhs_str} has no solution for {cond_desc} under mod {mod_val} projection ({div_val} divides {prod_lhs})."
            )
        else:
            all_args_str = ", ".join(all_var_names)
            prod_all = "*".join(all_var_names)
            sub_desc = f"subdomain ({div_val} does not divide {all_args_str})"
            lines.append(
                f"{indent}- Separating Modulus m = {mod_val} ({sub_desc}):"
            )
            lines.append(
                f"{indent}  * {rhs_arity}-ary Image Projection: f([{rhs_args_str}]) = {rhs_str} mod {mod_val} over ({div_val} does not divide {rhs_args_str}) -> {rhs_img_str}"
            )
            lines.append(
                f"{indent}  * {lhs_arity}-ary Image Projection: g([{lhs_args_str}]) = ({lhs_str}) mod {mod_val} over ({div_val} does not divide {lhs_args_str}) -> {lhs_img_str}"
            )
            lines.append(
                f"{indent}  * Disjoint Image Regularity: {rhs_img_str} /\\ {lhs_img_str} = empty"
            )
            lines.append(
                f"{indent}  * Obstruction Invariant: In any solution to {lhs_str} = {rhs_str}, {div_val} divides {prod_all} ({all_args_str} cannot all be coprime to {div_val} under mod {mod_val} projection)."
            )

        shown += 1
        cur = M.Tail(cur)()

    return lines


def run_playground_interactive(graph, goal_text=None, tutor=None):
    """
    Runs the dynamic, goal-directed Cartesian exploration sweep over the active
    unproved goal (or discovers separating moduli over the default benchmark
    when no goal is active) and returns the formatted lemma proposal.
    """
    registry = M.FromContextGetConstructors(graph)()
    active_goal = (
        goal_text
        if goal_text is not None
        else getattr(graph, "_active_unproved_goal", None)
    )
    active_tutor = (
        tutor if tutor is not None else getattr(graph, "_active_tutor", None)
    )
    active_claim = getattr(graph, "_active_unproved_claim", None)

    # 1. If a parsed equation goal is present, run goal-directed expression sweep
    spec = parse_surface_goal_spec(active_goal, registry) if active_goal else None
    if spec is not None:
        lhs = spec["lhs"]
        rhs = spec["rhs"]
        base_vars = spec["base_vars"]
        exp_vars = spec["exp_vars"]
        param_min = spec["param_min"]
        no_solutions = spec["no_solutions"]
        positive_only = spec["positive_only"]
        reg = spec["registry"]

        # Case A: Parametric exponent family (e.g., x^n + y^n = z^n for n > 2)
        if M.IdentityCompare(exp_vars, M.EmptyList)() is M.false_value:
            exp_var = M.Head(exp_vars)()
            exp_name = str(exp_var())
            start_exp = param_min.get(exp_name, 2)
            max_exp = start_exp + 1
            max_mod = max(9, 2 * max_exp + 1)

            bound_res = M.NatFromRep(M.GMPRep(max_mod), reg)()
            bound_nat = M.Head(bound_res)()
            reg = M.Head(M.Tail(bound_res)())()

            dom_res = BuildNatRange(M.Zero, bound_nat, reg)()
            domain = M.Head(dom_res)()
            reg = M.Head(M.Tail(dom_res)())()
            moduli_chain = _chain_append_end(
                M.Tail(M.Tail(domain)())(), bound_nat
            )

            start_res = M.NatFromRep(M.GMPRep(start_exp), reg)()
            start_nat = M.Head(start_res)()
            reg = M.Head(M.Tail(start_res)())()

            count_res = M.NatFromRep(M.GMPRep(2), reg)()
            count_nat = M.Head(count_res)()
            reg = M.Head(M.Tail(count_res)())()

            exp_range_res = BuildNatRange(start_nat, count_nat, reg)()
            exp_chain = M.Head(exp_range_res)()
            reg = M.Head(M.Tail(exp_range_res)())()

            exp_ints = _set_chain_to_sorted_ints(exp_chain, reg)
            lhs_pat_str = RenderNatExpr(lhs, reg)
            rhs_pat_str = RenderNatExpr(rhs, reg)

            lines = [
                f"[machine] Cartesian Playground Sweep for {lhs_pat_str} = {rhs_pat_str} (parameter {exp_name} >= {start_exp}, testing {exp_name} in {exp_ints} over domain 0..{max_mod - 1}):"
            ]

            eval_cache = []
            all_discoveries = M.EmptyList
            cur_e = exp_chain
            while M.IdentityCompare(cur_e, M.EmptyList)() is M.false_value:
                e_nat = M.Head(cur_e)()
                e_val = M.NatRepOf(e_nat, reg)()()
                lhs_e = M.Head(SubstituteExprVar(lhs, exp_var, e_nat, reg)())()
                rhs_e = M.Head(SubstituteExprVar(rhs, exp_var, e_nat, reg)())()

                disc_res = DiscoverExprObstructions(
                    lhs_e, rhs_e, bound_nat, moduli_chain, reg, eval_cache=eval_cache
                )()
                disc_chain = M.Head(disc_res)()
                reg = M.Head(M.Tail(disc_res)())()
                witness, reg = _find_concrete_witness_from_tables(
                    lhs_e, rhs_e, base_vars, bound_nat, positive_only, reg, eval_cache=eval_cache
                )

                cur_d = disc_chain
                while M.IdentityCompare(cur_d, M.EmptyList)() is M.false_value:
                    all_discoveries = _chain_append_end(
                        all_discoveries, M.Head(cur_d)()
                    )
                    cur_d = M.Tail(cur_d)()

                lines.append(
                    f"  [Instance {exp_name} = {e_val}: {RenderNatExpr(lhs_e, reg)} = {RenderNatExpr(rhs_e, reg)}]"
                )
                lines.extend(
                    _format_discoveries_for_equation(
                        lhs_e,
                        rhs_e,
                        disc_chain,
                        moduli_chain,
                        max_mod,
                        witness,
                        reg,
                        indent="    ",
                    )
                )
                cur_e = M.Tail(cur_e)()

            if M.IdentityCompare(all_discoveries, M.EmptyList)() is M.false_value:
                graph._last_discovered_invariant = M.Head(all_discoveries)()
                graph._last_playground_discoveries = all_discoveries
                lines.append(
                    "  - Suggestion: Ground these discovered modular/divisibility invariants as candidate lemmas for each exponent case."
                )
            return "\n".join(lines)

        # Case B: Concrete polynomial identity claim (no_solutions is False)
        if not no_solutions:
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
            lhs_str = RenderNatExpr(lhs, reg)
            rhs_str = RenderNatExpr(rhs, reg)
            grid_count_val = M.NatRepOf(grid_count_nat, reg)()()

            if verdict is M.truth_value:
                return "\n".join(
                    [
                        f"[machine] Cartesian Playground Sweep for {lhs_str} = {rhs_str}:",
                        f"  - PolynomialIdentityByGrid verified {lhs_str} = {rhs_str} across all {grid_count_val} degree-bounded grid points.",
                        f"  - Candidate Lemma: Algebraic identity {lhs_str} == {rhs_str} holds universally over Nat.",
                        "  - Suggestion: Ground this polynomial identity into active context as a rewrite lemma.",
                    ]
                )
            if verdict is M.false_value:
                var_names = _vars_chain_to_names(base_vars)
                w_vals = _set_chain_to_sorted_ints(M.EmptyList, reg)
                w_cur = witness_tup
                w_pairs = []
                idx = 0
                while M.IdentityCompare(w_cur, M.EmptyList)() is M.false_value:
                    v_int = M.NatRepOf(M.Head(w_cur)(), reg)()()
                    v_name = var_names[idx] if idx < len(var_names) else f"v{idx}"
                    w_pairs.append(f"{v_name} = {v_int}")
                    idx += 1
                    w_cur = M.Tail(w_cur)()
                return "\n".join(
                    [
                        f"[machine] Cartesian Playground Sweep for {lhs_str} = {rhs_str}:",
                        f"  - Counterexample Witness Found: ({', '.join(w_pairs)}) refutes {lhs_str} = {rhs_str} on the degree grid.",
                        "  - Suggestion: Restrict domain hypotheses or project modulo a separating congruence class.",
                    ]
                )

        # Case C: Concrete equation with no_solutions (e.g. x^3 + y^3 = z^3, x^2 + y^2 = 4*z + 3)
        bound_res = M.NatFromRep(M.GMPRep(10), reg)()
        bound_nat = M.Head(bound_res)()
        reg = M.Head(M.Tail(bound_res)())()

        dom_res = BuildNatRange(M.Zero, bound_nat, reg)()
        domain = M.Head(dom_res)()
        reg = M.Head(M.Tail(dom_res)())()
        moduli_chain = M.Tail(M.Tail(domain)())()  # 2..9

        eval_cache = []
        disc_res = DiscoverExprObstructions(
            lhs, rhs, bound_nat, moduli_chain, reg, eval_cache=eval_cache
        )()
        disc_chain = M.Head(disc_res)()
        reg = M.Head(M.Tail(disc_res)())()
        witness, reg = _find_concrete_witness_from_tables(
            lhs, rhs, base_vars, bound_nat, positive_only, reg, eval_cache=eval_cache
        )

        lhs_str = RenderNatExpr(lhs, reg)
        rhs_str = RenderNatExpr(rhs, reg)
        lines = [
            f"[machine] Cartesian Playground Sweep for {lhs_str} = {rhs_str} (domain 0..9):"
        ]
        lines.extend(
            _format_discoveries_for_equation(
                lhs, rhs, disc_chain, moduli_chain, 10, witness, reg, indent="  "
            )
        )
        if M.IdentityCompare(disc_chain, M.EmptyList)() is M.false_value:
            graph._last_discovered_invariant = M.Head(disc_chain)()
            graph._last_playground_discoveries = disc_chain
            lines.append(
                "  - Suggestion: Ground this discovered regularity into active context as an invariant lemma."
            )
        return "\n".join(lines)

    # 2. If an undecided Socratic tutor claim is active, suggest backward premises & schema
    if active_claim is not None and active_tutor is not None:
        from . import dialogue as Dlg

        goal_fact = Dlg.claim_conclusion(active_claim)
        known_facts = Dlg.claim_start_facts(active_claim)
        obls = Dlg.to_list(
            Dlg.BackwardObligations(goal_fact, known_facts, active_tutor.rules())()
        )
        claim_str = active_tutor.claim_text(active_claim)
        lines = [
            f"[machine] Cartesian Playground & Backward Obligation Analysis for '{claim_str}':"
        ]
        if obls:
            first_obl = obls[0]
            rule_obj = M.Head(first_obl)()
            open_prems = Dlg.to_list(M.Head(M.Tail(M.Tail(first_obl)())())())
            rule_id = active_tutor.rule_id_of(rule_obj)
            open_strs = [
                Dlg.render_term(p, active_tutor.registry) for p in open_prems
            ]
            lines.append(
                f"  - Backward Rule Candidate: '{rule_id}' concludes {Dlg.render_term(goal_fact, active_tutor.registry)} given missing premise(s): {', '.join(open_strs)}."
            )
            lines.append(
                f"  - Candidate Lemma: Establish {', '.join(open_strs)} (or ground schema '{claim_str}' after verification)."
            )
        else:
            lines.append(
                f"  - No loaded rule concludes {Dlg.render_term(goal_fact, active_tutor.registry)} directly."
            )
            lines.append(
                f"  - Candidate Lemma Schema: '{claim_str}' (empirically unrefuted across the Cartesian natural sweep)."
            )
        return "\n".join(lines)

    # 3. Default benchmark exploration when no specific goal has been posed yet:
    #    dynamically discovers the separating modulus across candidate moduli 2..5
    #    via DiscoverSeparatingModulus (never hardcoded to modulus 4).
    bound_res = M.NatFromRep(M.GMPRep(11), registry)()
    bound_nat = M.Head(bound_res)()
    reg1 = M.Head(M.Tail(bound_res)())()

    two_res = M.NatFromRep(M.GMPRep(2), reg1)()
    two_nat = M.Head(two_res)()
    reg2 = M.Head(M.Tail(two_res)())()

    one_res = M.NatFromRep(M.GMPRep(1), reg2)()
    one_nat = M.Head(one_res)()
    reg3 = M.Head(M.Tail(one_res)())()

    four_res = M.NatFromRep(M.GMPRep(4), reg3)()
    four_nat = M.Head(four_res)()
    reg4 = M.Head(M.Tail(four_res)())()

    mods_res = BuildNatRange(two_nat, four_nat, reg4)()
    moduli_chain = M.Head(mods_res)()
    reg5 = M.Head(M.Tail(mods_res)())()

    def every_unary(_x, _reg):
        return M.truth_value

    def odd_pair_pred(x, y, reg):
        rx = A.Modulo(x, two_nat, reg)()
        rem_x = M.Head(rx)()
        r_a = M.Head(M.Tail(rx)())()
        if M.NatEq(rem_x, one_nat, r_a)() is M.false_value:
            return M.false_value
        ry = A.Modulo(y, two_nat, r_a)()
        rem_y = M.Head(ry)()
        r_b = M.Head(M.Tail(ry)())()
        return M.NatEq(rem_y, one_nat, r_b)()

    disc_res = DiscoverSeparatingModulus(
        bound_nat, two_nat, every_unary, odd_pair_pred, moduli_chain, reg5
    )()
    inv_rec = M.Head(disc_res)()
    reg6 = M.Head(M.Tail(disc_res)())()

    graph._last_discovered_invariant = inv_rec

    res_mod = M.Head(M.Tail(inv_rec)())()
    mod_val = M.NatRepOf(res_mod, reg6)()()

    sq_set = M.Head(M.Tail(M.Tail(inv_rec)())())()
    odd_sum_set = M.Head(M.Tail(M.Tail(M.Tail(inv_rec)())())())()
    is_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(inv_rec)())())())())()

    sq_str = _format_set_chain(sq_set, reg6)
    odd_str = _format_set_chain(odd_sum_set, reg6)
    tested_str = ", ".join(map(str, _set_chain_to_sorted_ints(moduli_chain, reg6)))

    lines = [
        f"[machine] Cartesian Playground Sweep (domain 0..10, candidate moduli [{tested_str}] -> discovered m = {mod_val}):",
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


def _exact_arity(args, arity):
    """Syntax arity only; never interprets a machine number as a host int."""
    for _ in range(arity):
        if M.IsPair(args)() is M.false_value:
            return M.false_value
        args = M.Tail(args)()
    return M.IdentityCompare(args, M.EmptyList)()


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
    """Check exact syntax and coverage *before* computing a degree or grid.

    Non-numeric atoms declared in variables are formal indeterminates. A
    missing variable is not a degree-zero constant. Duplicate variables are
    refused: a diagonal grid is not a Cartesian grid of independent variables.
    """
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
    {0..d_k}, d_i the larger structural degree bound of the two sides in
    x_i. Sound by the finite-grid identity lemma (see the section comment):
    verdict truth is a proof of the identity for all naturals, verdict false
    records the first grid point where the sides differ. For a false constant
    identity this is the empty tuple, so inspect the verdict, not the witness's
    emptiness. Verdict [] means malformed/uncovered syntax or an unsupported
    fragment. Variables must be distinct formal atoms and cover both terms.

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
        """Return (verdict, first differing tuple, registry).

        The verdict is separate: the empty tuple is a valid counterexample
        for a constant polynomial with no variables, not evidence of equality.
        """
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
    """Grid-gated ordinary rewrite certificate (W22, partial).

    Returns Pair(grid_record, Pair(success, Pair(derivation-or-[],
    Pair(registry, [])))). Only a grid-true admitted identity is searched.
    No grid verdict becomes a trusted rewrite rule: Checker B must replay the
    returned derivation using the caller's rules. Power expansion, coefficient
    collection and commutative-ring normalisation remain missing from the
    default rules; success is deliberately not promised for every grid truth.
    """

    def __init__(self, lhs, rhs, variables, rules, registry, fuel=M.nine):
        from .invariance import RewriteEqualityDerivation

        decided = PolynomialIdentityByGrid(lhs, rhs, variables, registry)()
        record = M.Head(decided)()
        registry = M.Head(M.Tail(decided)())()
        fields = M.Tail(record)()
        # lhs, rhs, variables, degrees, grid_count, verdict, witness
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
    """Record one finite-grid inference for Checker B to recompute.

    Result Pair(grid_record, Pair(derivation-or-[], Pair(registry, []))).
    This is a decision-procedure certificate, NOT a RewriteHere path.
    Verifiers must explicitly trust PolynomialGridRuleLabel to admit this
    action; the record's verdict, bounds and count are never trusted as facts.
    """

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
    """Re-evaluate a concrete bounded Nat assignment, not a search status.

    constraints: chain of ExprEq(lhs,rhs) / ExprLt(lhs,rhs), using the same
    admitted natural polynomial syntax as PolynomialIdentityByGrid.
    environment: exactly one Pair(variable, Pair(Nat, [])) per declared
    variable, in declaration order, with values in [0,bound).
    Result Pair(verdict, Pair(registry, [])): true/false for valid assignments,
    [] for malformed syntax/coverage/sorts/bounds. An empty assignment can be
    valid (zero variables). This is a computed arithmetic check, NOT a Checker-B
    derivation, existential theorem, trusted premise, or ledger receipt.
    """

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
    """Stream [0,bound)^arity with a candidate-count budget; first axis fastest.

    Result Pair(record, Pair(registry, [])), where record is
      NatWitnessSearchLabel(constraints, variables, bound, budget, status,
                            environment, examined).
    Status: NatWitnessFoundLabel / NatWitnessExhaustedLabel /
    NatWitnessBudgetLabel / NatWitnessInvalidLabel. Only Found carries an
    environment (which may itself be [] for zero variables). Exhausted means
    this FINITE box only, never no natural solution. Budget is assignment checks,
    not a bound on expression size, exponent size, arithmetic cost or wall time.
    No full Cartesian product or host-language numerical search is materialised.
    """

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
        while True:
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
