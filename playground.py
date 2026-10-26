# ============================================================
# Playground — Machine-Native Irreducible Cartesian Engine
#
# Foundational arity-agnostic Cartesian product generator,
# Peano-native sequence counting, tuple operations, universal
# relational quantifiers, and congruence projections.
# ============================================================
from __future__ import annotations

import os
import sys

from . import constructors as C
from . import graph_task as GT
from . import labels as L
from . import machine as M
from . import proof as P
from .math import arithmetic as A
from .trees import TreeEntries


class PlaygroundDebugEmit(M.Edge):
    """
    Emits one live debug line for the Cartesian playground. The message is
    a machine Char; the write is the playground's only host output channel.
    """

    def __init__(self, message):
        self.result = M.Pair(message, M.EmptyList)
        print(
            f"[debug: cartesian_playground]: {message()}"
        )
        super().__init__(
            inputs=M.Pair(message, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class NaturalPlaygroundDebugEmit(M.Edge):
    """Emits process-tagged progress from the operation-law playground."""

    def __init__(self, message):
        self.result = M.Pair(message, M.EmptyList)
        print(
            "[debug natural_playground process ",
            os.getpid(),
            "]: ",
            message(),
            sep="",
        )
        sys.stdout.flush()
        super().__init__(
            inputs=M.Pair(message, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


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
        """Build the Cartesian product iteratively.

        The recursive shape walked one chain per domain and then concatenated
        the pieces, which spent a stack frame per element and made the
        concatenation quadratic in the number of tuples. Extending an
        accumulator in a loop allocates once per tuple and keeps the depth
        constant. Domains are consumed right to left because a tuple is built
        by prepending, so the leftmost domain still varies slowest and still
        leads each tuple, exactly as before.
        """
        acc = M.Pair(M.EmptyList, M.EmptyList)
        cur = self._reverse(domains)
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            acc = self._extend(M.Head(cur)(), acc)
            cur = M.Tail(cur)()
        return acc

    def _extend(self, domain, acc):
        """Prepend every element of domain onto every tuple of acc."""
        built = M.EmptyList
        cur_x = domain
        while M.IdentityCompare(cur_x, M.EmptyList)() is M.false_value:
            x = M.Head(cur_x)()
            cur_t = acc
            while M.IdentityCompare(cur_t, M.EmptyList)() is M.false_value:
                built = M.Pair(M.Pair(x, M.Head(cur_t)()), built)
                cur_t = M.Tail(cur_t)()
            cur_x = M.Tail(cur_x)()
        return self._reverse(built)

    def _reverse(self, chain):
        out = M.EmptyList
        cur = chain
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            out = M.Pair(M.Head(cur)(), out)
            cur = M.Tail(cur)()
        return out

    def __call__(self):
        return self.result


class FilterTuples(M.Edge):
    """
    Filters a k-tuple domain by a machine constraint chain.

    `variables` is the chain of variable atoms the constraints are written
    over. Each tuple is zipped with it by ZipEnvironment and the constraint
    chain is evaluated by EvaluateNatConstraints over the machine's own
    arithmetic; a tuple whose constraints cannot be evaluated does not
    pass. No host callable participates in the decision.
    """

    def __init__(self, tuples_chain, variables, constraints, registry):
        self.registry = registry
        self.result = self._filter(
            tuples_chain, variables, constraints, registry
        )
        super().__init__(
            inputs=M.Pair(
                tuples_chain,
                M.Pair(
                    variables,
                    M.Pair(constraints, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _filter(self, cur_tuples, variables, constraints, registry):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        t = M.Head(cur_tuples)()
        environment = ZipEnvironment(variables, t)()
        pred_res = EvaluateNatConstraints(constraints, environment, registry)()
        passed = M.Head(pred_res)()
        reg1 = M.Head(M.Tail(pred_res)())()

        rest_res = self._filter(
            M.Tail(cur_tuples)(), variables, constraints, reg1
        )
        rest_filtered = M.Head(rest_res)()
        reg2 = M.Head(M.Tail(rest_res)())()

        if passed is M.truth_value:
            return M.Pair(M.Pair(t, rest_filtered), M.Pair(reg2, M.EmptyList))
        return M.Pair(rest_filtered, M.Pair(reg2, M.EmptyList))

    def __call__(self):
        return self.result


class MapDomain(M.Edge):
    """
    Uniform k-ary domain evaluator over a machine operation term.

    `variables` is the chain of variable atoms the operation term is
    written over. Each tuple is zipped with it by ZipEnvironment and the
    operation term is evaluated by EvaluateNatExpr with the machine's own
    Add, Multiply and Peano recursion. Produces the evaluation list and the
    unique image set; a tuple whose operation term cannot be evaluated
    contributes to neither.
    """

    def __init__(self, tuples_chain, variables, operation, registry,
                 operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, M.Pair(operation, M.EmptyList)
            )()
            ops = M.Head(built)()
        self.result = self._map(
            tuples_chain,
            variables,
            operation,
            M.EmptyList,
            M.EmptyList,
            registry,
            ops,
        )
        super().__init__(
            inputs=M.Pair(
                tuples_chain,
                M.Pair(
                    variables,
                    M.Pair(operation, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _map(
        self, cur_tuples, variables, operation, acc_list, acc_set, registry, ops
    ):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(
                acc_list,
                M.Pair(acc_set, M.Pair(registry, M.EmptyList)),
            )
        t = M.Head(cur_tuples)()
        environment = ZipEnvironment(variables, t)()
        eval_res = EvaluateNatExpr(operation, environment, registry, ops)()
        val = M.Head(eval_res)()
        reg1 = M.Head(M.Tail(eval_res)())()

        if M.IdentityCompare(val, M.EmptyList)() is M.truth_value:
            return self._map(
                M.Tail(cur_tuples)(),
                variables,
                operation,
                acc_list,
                acc_set,
                reg1,
                ops,
            )

        new_set = SetInsert(val, acc_set, reg1)()
        new_list = M.Pair(val, acc_list)
        return self._map(
            M.Tail(cur_tuples)(), variables, operation, new_list, new_set, reg1, ops
        )

    def __call__(self):
        return self.result


class UniversalQuantify(M.Edge):
    """
    Universal relational quantifier. The relation is machine data in one of
    two forms:

      * a constraint chain (ExprEq / ExprLt / NatModEq / Divides /
        Coprime terms over `variables`), or
      * a derivation relation record
        Pair(DerivationRelationLabel,
             Pair(theory, Pair(config_templates,
                  Pair(goal_template, Pair(fuel, Pair(refuse_flag, EmptyList)))))
        whose optional refuse_flag, when truth_value, makes the relation
        hold exactly when the instantiated goal is NOT in the closure.

    In the derivation form every tuple is zipped with `variables`, each
    config template is instantiated with the bindings, the rules of
    `theory` are applied by the machine's own ForwardDeriveFacts edge, and
    the relation holds exactly when the instantiated goal_template is in
    the derived closure. An unevaluable constraint fails the universal.
    """

    def __init__(self, tuples_chain, variables, relation, registry,
                 operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            terms = relation
            if self._is_derivation_relation(relation) is M.truth_value:
                terms = M.EmptyList
            built = BuildNatOperationRegister(
                registry, terms
            )()
            ops = M.Head(built)()
        self.result = self._eval(
            tuples_chain, variables, relation, registry, ops
        )
        super().__init__(
            inputs=M.Pair(
                tuples_chain,
                M.Pair(
                    variables,
                    M.Pair(relation, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _is_derivation_relation(self, relation):
        if M.IsPair(relation)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(relation)(), L.DerivationRelationLabel)()

    def _derivation_holds(
        self, relation, environment, registry, ops,
        remaining=M.EmptyList, config=M.EmptyList,
        initialized=M.false_value,
    ):
        fields = M.Tail(relation)()
        theory = M.Head(fields)()
        rest = M.Tail(fields)()
        config_templates = M.Head(rest)()
        rest = M.Tail(rest)()
        goal_template = M.Head(rest)()
        rest = M.Tail(rest)()
        fuel = M.Head(rest)()
        rest = M.Tail(rest)()
        refuse_flag = M.false_value
        if M.IsPair(rest)() is M.truth_value:
            refuse_flag = M.Head(rest)()

        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            remaining = config_templates
            initialized = M.truth_value
        if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            inst_res = M.Instantiate(M.Head(remaining)(), environment)()
            config_fact = M.Head(inst_res)()
            return self._derivation_holds(
                relation,
                environment,
                registry,
                ops,
                M.Tail(remaining)(),
                ChainAppendEnd(config, config_fact)(),
                initialized,
            )

        closure = GT.ForwardDeriveFacts(config, theory, fuel, registry)()

        goal_res = M.Instantiate(goal_template, environment)()
        goal = M.Head(goal_res)()
        derived = ChainHasTerm(closure, goal)()
        if (
            M.IdentityCompare(refuse_flag, M.truth_value)()
            is M.truth_value
        ):
            derived = M.NotAtom(derived)()
        return M.Pair(
            derived,
            M.Pair(registry, M.EmptyList),
        )

    def _relation_holds(self, relation, environment, registry, ops):
        if (
            self._is_derivation_relation(relation)
            is M.truth_value
        ):
            return self._derivation_holds(relation, environment, registry, ops)
        return EvaluateNatConstraints(relation, environment, registry, ops)()

    def _eval(self, cur_tuples, variables, relation, registry, ops):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(registry, M.EmptyList))
        t = M.Head(cur_tuples)()
        environment = ZipEnvironment(variables, t)()
        rel_res = self._relation_holds(relation, environment, registry, ops)
        holds = M.Head(rel_res)()
        reg1 = M.Head(M.Tail(rel_res)())()

        if M.IdentityCompare(holds, M.truth_value)() is M.false_value:
            return M.Pair(M.false_value, M.Pair(reg1, M.EmptyList))
        return self._eval(
            M.Tail(cur_tuples)(), variables, relation, reg1, ops
        )

    def __call__(self):
        return self.result


class ExistentialQuantify(M.Edge):
    """
    Existential relational quantifier with the same two machine relation
    forms as UniversalQuantify: a constraint chain, or a derivation
    relation record evaluated by the machine's own ForwardDeriveFacts.
    """

    def __init__(self, tuples_chain, variables, relation, registry,
                 operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            terms = relation
            if self._is_derivation_relation(relation) is M.truth_value:
                terms = M.EmptyList
            built = BuildNatOperationRegister(
                registry, terms
            )()
            ops = M.Head(built)()
        self.result = self._eval(
            tuples_chain, variables, relation, registry, ops
        )
        super().__init__(
            inputs=M.Pair(
                tuples_chain,
                M.Pair(
                    variables,
                    M.Pair(relation, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _is_derivation_relation(self, relation):
        if M.IsPair(relation)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(relation)(), L.DerivationRelationLabel)()

    def _derivation_holds(
        self, relation, environment, registry, ops,
        remaining=M.EmptyList, config=M.EmptyList,
        initialized=M.false_value,
    ):
        fields = M.Tail(relation)()
        theory = M.Head(fields)()
        rest = M.Tail(fields)()
        config_templates = M.Head(rest)()
        rest = M.Tail(rest)()
        goal_template = M.Head(rest)()
        rest = M.Tail(rest)()
        fuel = M.Head(rest)()
        rest = M.Tail(rest)()
        refuse_flag = M.false_value
        if M.IsPair(rest)() is M.truth_value:
            refuse_flag = M.Head(rest)()

        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            remaining = config_templates
            initialized = M.truth_value
        if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            inst_res = M.Instantiate(M.Head(remaining)(), environment)()
            config_fact = M.Head(inst_res)()
            return self._derivation_holds(
                relation,
                environment,
                registry,
                ops,
                M.Tail(remaining)(),
                ChainAppendEnd(config, config_fact)(),
                initialized,
            )

        closure = GT.ForwardDeriveFacts(config, theory, fuel, registry)()

        goal_res = M.Instantiate(goal_template, environment)()
        goal = M.Head(goal_res)()
        derived = ChainHasTerm(closure, goal)()
        if (
            M.IdentityCompare(refuse_flag, M.truth_value)()
            is M.truth_value
        ):
            derived = M.NotAtom(derived)()
        return M.Pair(
            derived,
            M.Pair(registry, M.EmptyList),
        )

    def _relation_holds(self, relation, environment, registry, ops):
        if (
            self._is_derivation_relation(relation)
            is M.truth_value
        ):
            return self._derivation_holds(relation, environment, registry, ops)
        return EvaluateNatConstraints(relation, environment, registry, ops)()

    def _eval(self, cur_tuples, variables, relation, registry, ops):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(registry, M.EmptyList))
        t = M.Head(cur_tuples)()
        environment = ZipEnvironment(variables, t)()
        rel_res = self._relation_holds(relation, environment, registry, ops)
        holds = M.Head(rel_res)()
        reg1 = M.Head(M.Tail(rel_res)())()

        if holds is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(reg1, M.EmptyList))
        return self._eval(
            M.Tail(cur_tuples)(), variables, relation, reg1, ops
        )

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

        # The default subdomain, as machine data: x is odd and y is odd.
        x_atom = M.Char("x")
        y_atom = M.Char("y")
        odd_x = M.Pair(
            L.NatModEqLabel,
            M.Pair(x_atom, M.Pair(two_nat, M.Pair(one_nat, M.EmptyList))),
        )
        odd_y = M.Pair(
            L.NatModEqLabel,
            M.Pair(y_atom, M.Pair(two_nat, M.Pair(one_nat, M.EmptyList))),
        )
        odd_pair_constraints = M.Pair(odd_x, M.Pair(odd_y, M.EmptyList))
        unary_variables = M.Pair(x_atom, M.EmptyList)
        pair_variables = M.Pair(x_atom, M.Pair(y_atom, M.EmptyList))

        return RunPlaygroundFilteredPowerSweep(
            bound_nat,
            mod_nat,
            two_nat,
            unary_variables,
            M.EmptyList,
            pair_variables,
            odd_pair_constraints,
            reg2,
        )()

    def __call__(self):
        return self.result


class EvaluateOperationTensor(M.Edge):
    """
    Evaluates a machine operation term across all tuples in a k-ary domain
    product, generating a ground EvaluationTensor record.

    `variables` is the chain of variable atoms the operation term is written
    over; each tuple is zipped with it and the operation term is evaluated
    by EvaluateNatExpr with the machine's own arithmetic. No host callable
    participates in the evaluation.

    inputs: [op_name, variables, operation, tuples_chain, registry]
    results: Pair(EvaluationTensorLabel, Pair(op_name, Pair(entry_chain, Pair(registry, EmptyList))))
    """

    def __init__(self, op_name, variables, operation, tuples_chain, registry,
                 operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, M.Pair(operation, M.EmptyList)
            )()
            ops = M.Head(built)()
        self.result = self._eval_tensor(
            op_name, variables, operation, tuples_chain, registry, ops
        )
        super().__init__(
            inputs=M.Pair(
                op_name,
                M.Pair(
                    variables,
                    M.Pair(
                        operation,
                        M.Pair(tuples_chain, M.Pair(registry, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _eval_tensor(
        self, op_name, variables, operation, cur_tuples, reg, ops
    ):
        if M.IdentityCompare(cur_tuples, M.EmptyList)() is M.truth_value:
            tensor_node = M.Pair(
                L.EvaluationTensorLabel,
                M.Pair(op_name, M.Pair(M.EmptyList, M.EmptyList)),
            )
            return M.Pair(tensor_node, M.Pair(reg, M.EmptyList))

        head_tuple = M.Head(cur_tuples)()
        tail_tuples = M.Tail(cur_tuples)()

        environment = ZipEnvironment(variables, head_tuple)()
        call_res = EvaluateNatExpr(operation, environment, reg, ops)()
        out_val = M.Head(call_res)()
        r1 = M.Head(M.Tail(call_res)())()

        rest_res = self._eval_tensor(
            op_name, variables, operation, tail_tuples, r1, ops
        )
        rest_tensor = M.Head(rest_res)()
        r2 = M.Head(M.Tail(rest_res)())()

        rest_entries = M.Head(M.Tail(M.Tail(rest_tensor)())())()

        entry = M.Pair(
            L.EvaluationEntryLabel,
            M.Pair(head_tuple, M.Pair(out_val, M.EmptyList)),
        )

        tensor_node = M.Pair(
            L.EvaluationTensorLabel,
            M.Pair(
                op_name, M.Pair(M.Pair(entry, rest_entries), M.EmptyList)
            ),
        )
        return M.Pair(tensor_node, M.Pair(r2, M.EmptyList))

    def __call__(self):
        return self.result


class NatPowPeano(M.Edge):
    """
    Computes base_nat ^ exp_nat by pure Peano recursion on exp_nat, using
    M.NatEq, M.NatPred and A.Multiply (no host loop and no host int).
    Result: Pair(result_nat, Pair(registry, EmptyList)).
    """

    def __init__(self, base_nat, exp_nat, registry):
        self.registry = registry
        self.result = self._pow(base_nat, exp_nat, registry)
        super().__init__(
            inputs=M.Pair(
                base_nat,
                M.Pair(exp_nat, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _pow(self, base_nat, exp_nat, registry):
        if M.NatEq(exp_nat, M.Zero, registry)() is M.truth_value:
            return M.Pair(M.one, M.Pair(registry, M.EmptyList))
        pred_res = M.NatPred(exp_nat, registry)()
        pred_exp = M.Head(pred_res)()
        reg1 = M.Head(M.Tail(pred_res)())()
        if M.NatEq(pred_exp, M.Zero, reg1)() is M.truth_value:
            return M.Pair(base_nat, M.Pair(reg1, M.EmptyList))
        sub_res = self._pow(base_nat, pred_exp, reg1)
        sub_val = M.Head(sub_res)()
        reg2 = M.Head(M.Tail(sub_res)())()
        return A.Multiply(sub_val, base_nat, reg2)()

    def __call__(self):
        return self.result


class RunPlaygroundFilteredPowerSweep(M.Edge):
    """
    Parameterized Cartesian sweep over machine data.

    Takes the exponent, both subdomain filters and the variable vocabulary
    the filters are written over, so one piece of machinery runs any
    power-image / filtered-sum-image disjointness test:

        unary image    = { x^k mod m : x in domain, unary_constraints hold }
        pair-sum image = { (x^k + y^k) mod m : x, y in domain, pair_constraints hold }

    The record has the same shape as RunPlaygroundCartesianSweep's:
        Pair(DiscoveredInvariantLabel,
             Pair(modulus,
                  Pair(unary_image,
                       Pair(pair_sum_image, Pair(disjoint, EmptyList)))))
    """

    def __init__(
        self,
        bound_nat,
        mod_nat,
        power_nat,
        unary_variables,
        unary_constraints,
        pair_variables,
        pair_constraints,
        registry,
    ):
        self.registry = registry
        self.result = self._run(
            bound_nat,
            mod_nat,
            power_nat,
            unary_variables,
            unary_constraints,
            pair_variables,
            pair_constraints,
            registry,
        )
        super().__init__(
            inputs=M.Pair(
                bound_nat,
                M.Pair(
                    mod_nat,
                    M.Pair(
                        power_nat,
                        M.Pair(
                            unary_variables,
                            M.Pair(
                                unary_constraints,
                                M.Pair(
                                    pair_variables,
                                    M.Pair(
                                        pair_constraints,
                                        M.Pair(registry, M.EmptyList),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _pow_term(self, variable, power_nat):
        return M.Pair(
            L.ExprPowLabel,
            M.Pair(variable, M.Pair(power_nat, M.EmptyList)),
        )

    def _run(
        self,
        bound_nat,
        mod_nat,
        power_nat,
        unary_variables,
        unary_constraints,
        pair_variables,
        pair_constraints,
        registry,
    ):
        if A.IsNat(power_nat, registry)() is M.false_value:
            raise TypeError("FilteredPowerSweep expects a Nat exponent")

        # 1. Base domain: Zero for bound_nat steps.
        range_res = BuildNatRange(M.Zero, bound_nat, registry)()
        domain = M.Head(range_res)()
        reg1 = M.Head(M.Tail(range_res)())()

        unary_var = M.Head(unary_variables)()
        pair_x = M.Head(pair_variables)()
        pair_y = M.Head(M.Tail(pair_variables)())()

        unary_op = self._pow_term(unary_var, power_nat)
        pair_op = M.Pair(
            L.ExprAddLabel,
            M.Pair(
                self._pow_term(pair_x, power_nat),
                M.Pair(self._pow_term(pair_y, power_nat), M.EmptyList),
            ),
        )

        # 2. Unary image over the filtered 1-ary domain.
        dom1 = ProductOfDomains(M.Pair(domain, M.EmptyList))()
        unary_tuples_res = FilterTuples(
            dom1, unary_variables, unary_constraints, reg1
        )()
        unary_tuples = M.Head(unary_tuples_res)()
        reg2 = M.Head(M.Tail(unary_tuples_res)())()
        unary_map_res = MapDomain(
            unary_tuples, unary_variables, unary_op, reg2
        )()
        unary_vals = M.Head(unary_map_res)()
        reg3 = M.Head(M.Tail(M.Tail(unary_map_res)())())()
        unary_proj_res = ProjectCongruence(unary_vals, mod_nat, reg3)()
        unary_image = M.Head(unary_proj_res)()
        reg4 = M.Head(M.Tail(unary_proj_res)())()

        # 3. Pair-sum image over the filtered 2-ary domain.
        dom2 = ProductOfDomains(M.Pair(domain, M.Pair(domain, M.EmptyList)))()
        pair_tuples_res = FilterTuples(
            dom2, pair_variables, pair_constraints, reg4
        )()
        pair_tuples = M.Head(pair_tuples_res)()
        reg5 = M.Head(M.Tail(pair_tuples_res)())()
        pair_map_res = MapDomain(pair_tuples, pair_variables, pair_op, reg5)()
        pair_vals = M.Head(pair_map_res)()
        reg6 = M.Head(M.Tail(M.Tail(pair_map_res)())())()
        pair_proj_res = ProjectCongruence(pair_vals, mod_nat, reg6)()
        pair_image = M.Head(pair_proj_res)()
        reg7 = M.Head(M.Tail(pair_proj_res)())()

        # 4. Disjointness of the two images.
        disjoint_res = EvaluateSetRelation(unary_image, pair_image, reg7)()
        is_disjoint = M.Head(disjoint_res)()
        reg8 = M.Head(M.Tail(M.Tail(disjoint_res)())())()

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
        return M.Pair(sweep_record, M.Pair(reg8, M.EmptyList))

    def __call__(self):
        return self.result


class DiscoverSeparatingModulus(M.Edge):
    """
    Run RunPlaygroundFilteredPowerSweep over an ordered chain of candidate
    moduli and return the record of the FIRST modulus whose unary and
    pair-sum images are disjoint, or EmptyList when none separates.
    Returns Pair(record_or_EmptyList, Pair(registry, EmptyList)).
    """

    def __init__(
        self,
        bound_nat,
        power_nat,
        unary_variables,
        unary_constraints,
        pair_variables,
        pair_constraints,
        moduli_chain,
        registry,
    ):
        self.registry = registry
        self.result = self._search(
            bound_nat,
            power_nat,
            unary_variables,
            unary_constraints,
            pair_variables,
            pair_constraints,
            moduli_chain,
            registry,
        )
        super().__init__(
            inputs=M.Pair(
                bound_nat,
                M.Pair(
                    power_nat,
                    M.Pair(
                        unary_variables,
                        M.Pair(
                            unary_constraints,
                            M.Pair(
                                pair_variables,
                                M.Pair(
                                    pair_constraints,
                                    M.Pair(
                                        moduli_chain,
                                        M.Pair(registry, M.EmptyList),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _search(
        self,
        bound_nat,
        power_nat,
        unary_variables,
        unary_constraints,
        pair_variables,
        pair_constraints,
        moduli_chain,
        registry,
    ):
        if M.IdentityCompare(moduli_chain, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        candidate = M.Head(moduli_chain)()
        sweep_res = RunPlaygroundFilteredPowerSweep(
            bound_nat,
            candidate,
            power_nat,
            unary_variables,
            unary_constraints,
            pair_variables,
            pair_constraints,
            registry,
        )()
        record = M.Head(sweep_res)()
        reg1 = M.Head(M.Tail(sweep_res)())()
        disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
        if disjoint is M.truth_value:
            return M.Pair(record, M.Pair(reg1, M.EmptyList))
        return self._search(
            bound_nat,
            power_nat,
            unary_variables,
            unary_constraints,
            pair_variables,
            pair_constraints,
            M.Tail(moduli_chain)(),
            reg1,
        )

    def __call__(self):
        return self.result


# ============================================================
# Polynomial identities and congruences, decided by evaluation
# ============================================================


class ExprHeadArgs(M.Edge):
    """
    Structural accessor: a Pair(label, arg_chain) term yields
    Pair(label, Pair(arg_chain, EmptyList)); any other term yields
    Pair(EmptyList, EmptyList).
    """

    def __init__(self, term):
        self.result = self._head_args(term)
        super().__init__(
            inputs=M.Pair(term, M.EmptyList),
            results=self.result,
        )

    def _head_args(self, term):
        if M.IsPair(term)() is M.false_value:
            return M.Pair(M.EmptyList, M.EmptyList)
        return M.Pair(
            M.Head(term)(),
            M.Pair(M.Tail(term)(), M.EmptyList),
        )

    def __call__(self):
        return self.result


class EnvLookup(M.Edge):
    """
    Looks a variable up in an environment (a chain of
    Pair(variable, Pair(value, EmptyList))); EmptyList when unbound.
    """

    def __init__(self, environment, variable):
        self.result = self._lookup(environment, variable)
        super().__init__(
            inputs=M.Pair(environment, M.Pair(variable, M.EmptyList)),
            results=self.result,
        )

    def _lookup(self, environment, variable):
        if M.IdentityCompare(environment, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(environment)()
        if M.Compare(M.Head(entry)(), variable)() is M.truth_value:
            return M.Head(M.Tail(entry)())()
        return self._lookup(M.Tail(environment)(), variable)

    def __call__(self):
        return self.result


class ZipEnvironment(M.Edge):
    """
    Zips a variable chain and a value chain into an environment (a chain of
    Pair(variable, Pair(value, EmptyList))).
    """

    def __init__(self, variables, values):
        self.result = self._zip(variables, values)
        super().__init__(
            inputs=M.Pair(variables, M.Pair(values, M.EmptyList)),
            results=self.result,
        )

    def _zip(self, variables, values):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(values, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        binding = M.Pair(
            M.Head(variables)(),
            M.Pair(M.Head(values)(), M.EmptyList),
        )
        return M.Pair(
            binding,
            self._zip(M.Tail(variables)(), M.Tail(values)()),
        )

    def __call__(self):
        return self.result


class ExactArity(M.Edge):
    """
    Syntax arity only: true iff the argument chain carries exactly
    `arity_nat` Pair cells. Never interprets a machine number as a host int.
    """

    def __init__(self, args, arity_nat, registry):
        self.registry = registry
        self.result = self._exact(args, arity_nat, registry)
        super().__init__(
            inputs=M.Pair(
                args,
                M.Pair(arity_nat, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _exact(self, args, arity_nat, registry):
        if M.NatEq(arity_nat, M.Zero, registry)() is M.truth_value:
            return M.IdentityCompare(args, M.EmptyList)()
        if M.IsPair(args)() is M.false_value:
            return M.false_value
        pred_res = M.NatPred(arity_nat, registry)()
        pred_arity = M.Head(pred_res)()
        reg1 = M.Head(M.Tail(pred_res)())()
        return self._exact(M.Tail(args)(), pred_arity, reg1)

    def __call__(self):
        return self.result


class ChainHasTerm(M.Edge):
    """
    Compare-based membership of a term in a chain (never IdentityCompare on
    Chars): true iff some element compares equal to `element`.
    """

    def __init__(self, chain, element):
        self.result = self._has(chain, element)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(element, M.EmptyList)),
            results=self.result,
        )

    def _has(self, chain, element):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.Compare(M.Head(chain)(), element)() is M.truth_value:
            return M.truth_value
        return self._has(M.Tail(chain)(), element)

    def __call__(self):
        return self.result


class ChainStartsWith(M.Edge):
    """
    Machine test: chain is non-empty and its first element is `element`.
    Guards the head read so an empty chain yields false instead of a
    host-level structural error.
    """

    def __init__(self, chain, element):
        self.result = self._check(chain, element)

    def _check(self, chain, element):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        return M.Compare(M.Head(chain)(), element)()

    def __call__(self):
        return self.result


class ChainAppendEnd(M.Edge):
    """
    Appends one element at the end of a machine chain.
    """

    def __init__(self, chain, element):
        self.result = self._append(chain, element)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(element, M.EmptyList)),
            results=self.result,
        )

    def _append(self, chain, element):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.Pair(element, M.EmptyList)
        return M.Pair(
            M.Head(chain)(),
            self._append(M.Tail(chain)(), element),
        )

    def __call__(self):
        return self.result


class ChainConcat(M.Edge):
    """
    Concatenates two machine chains.
    """

    def __init__(self, chain_a, chain_b):
        self.result = self._concat(chain_a, chain_b)
        super().__init__(
            inputs=M.Pair(chain_a, M.Pair(chain_b, M.EmptyList)),
            results=self.result,
        )

    def _concat(self, chain_a, chain_b):
        if M.IdentityCompare(chain_a, M.EmptyList)() is M.truth_value:
            return chain_b
        return M.Pair(
            M.Head(chain_a)(),
            self._concat(M.Tail(chain_a)(), chain_b),
        )

    def __call__(self):
        return self.result


class ChainReverse(M.Edge):
    """
    Reverses a machine chain.
    """

    def __init__(self, chain):
        self.result = self._reverse(chain, M.EmptyList)
        super().__init__(
            inputs=M.Pair(chain, M.EmptyList),
            results=self.result,
        )

    def _reverse(self, chain, acc):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return acc
        return self._reverse(
            M.Tail(chain)(),
            M.Pair(M.Head(chain)(), acc),
        )

    def __call__(self):
        return self.result


class ChainMergeUnique(M.Edge):
    """
    Merges chain_b into chain_a, appending every element of chain_b that
    chain_a does not already compare-equal to (chain_a's order is kept).
    """

    def __init__(self, chain_a, chain_b):
        self.result = self._merge(chain_a, chain_b)
        super().__init__(
            inputs=M.Pair(chain_a, M.Pair(chain_b, M.EmptyList)),
            results=self.result,
        )

    def _merge(self, chain_a, chain_b):
        if M.IdentityCompare(chain_b, M.EmptyList)() is M.truth_value:
            return chain_a
        head_b = M.Head(chain_b)()
        next_a = (
            chain_a
            if ChainHasTerm(chain_a, head_b)() is M.truth_value
            else ChainAppendEnd(chain_a, head_b)()
        )
        return self._merge(next_a, M.Tail(chain_b)())

    def __call__(self):
        return self.result


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
        head_args = ExprHeadArgs(term)()
        head = M.Head(head_args)()
        args = M.Head(M.Tail(head_args)())()
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            return M.EmptyList
        if ExactArity(args, M.two, registry)() is M.truth_value:
            left_vars = self._extract(M.Head(args)(), registry)
            right_vars = self._extract(M.Head(M.Tail(args)())(), registry)
            return ChainMergeUnique(left_vars, right_vars)()
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
        head_args = ExprHeadArgs(term)()
        head = M.Head(head_args)()
        args = M.Head(M.Tail(head_args)())()
        if ExactArity(args, M.two, registry)() is M.false_value:
            return M.EmptyList
        left = M.Head(args)()
        right = M.Head(M.Tail(args)())()
        left_exp = self._extract_exp(left, registry)
        if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
            exp_vars = M.Head(ExtractExprVariables(right, registry)())()
            return ChainMergeUnique(left_exp, exp_vars)()
        right_exp = self._extract_exp(right, registry)
        return ChainMergeUnique(left_exp, right_exp)()

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
        head_args = ExprHeadArgs(term)()
        head = M.Head(head_args)()
        args = M.Head(M.Tail(head_args)())()
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            return term
        if ExactArity(args, M.two, registry)() is M.truth_value:
            left = self._subst(M.Head(args)(), variable, replacement, registry)
            right = self._subst(
                M.Head(M.Tail(args)())(), variable, replacement, registry
            )
            return M.Pair(head, M.Pair(left, M.Pair(right, M.EmptyList)))
        return term

    def __call__(self):
        return self.result


class RenderNatExpr(M.Edge):
    """
    Renders a machine expression term into infix mathematical surface
    notation directly from its AST structure. Rendering is the playground's
    host output boundary; the result is the rendered string.
    """

    def __init__(self, term, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, M.Pair(term, M.EmptyList)
            )()
            ops = M.Head(built)()
        self.result = self._render(term, registry, ops)
        super().__init__(
            inputs=M.Pair(term, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _pair_with_head(self, term, label):
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Head(term)(), label)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _needs_parens(self, operand, outer_precedence, ops, registry, is_right):
        # Left-associative infix rule: the left operand keeps its own grouping
        # only when it binds at least as tightly as the parent, while the
        # right operand must bind strictly tighter. `mod` is loosest, so
        # `x + y mod z` is exactly `(x + y) mod z` and stays bare.
        if M.IsPair(operand)() is M.false_value:
            return M.false_value
        operand_head = M.Head(operand)()
        inner = LookupOperationByLabel(operand_head, ops)()
        if M.IdentityCompare(inner, M.EmptyList)() is M.truth_value:
            return M.false_value
        inner_prec = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(inner)())())())())()
        if M.NatLess(inner_prec, outer_precedence, registry)() is M.truth_value:
            return M.truth_value
        if is_right is M.truth_value:
            if M.NatLess(outer_precedence, inner_prec, registry)() is M.false_value:
                return M.truth_value
        return M.false_value

    def _pair_not_head(self, term, label):
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Head(term)(), label)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def _render(self, term, registry, ops):
        if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
            return "0"
        if A.IsNat(term, registry)() is M.truth_value:
            rep = M.NatRepOf(term, registry)()
            if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
                return M.GMPRepText(rep)()
        if M.IsPair(term)() is M.false_value:
            val = term()
            if val is None:
                return "?"
            return M.GMPRepText(term)()
        head_args = ExprHeadArgs(term)()
        head = M.Head(head_args)()
        args = M.Head(M.Tail(head_args)())()
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            if ExactArity(args, M.one, registry)() is M.false_value:
                return "?"
            return self._render(M.Head(args)(), registry, ops)
        if ExactArity(args, M.two, registry)() is M.false_value:
            return "?"
        left = M.Head(args)()
        right = M.Head(M.Tail(args)())()
        if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
            b_str = self._render(left, registry, ops)
            e_str = self._render(right, registry, ops)
            if (
                self._pair_not_head(left, L.ExprIntLabel)
                is M.truth_value
            ):
                b_str = "(" + b_str + ")"
            if self._pair_not_head(right, L.ExprIntLabel) is M.truth_value:
                e_str = "(" + e_str + ")"
            return b_str + "^" + e_str
        entry = LookupOperationByLabel(head, ops)()
        if M.IdentityCompare(entry, M.EmptyList)() is M.truth_value:
            return "?"
        print_form = M.Head(M.Tail(M.Tail(M.Tail(entry)())())())()()
        precedence = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(entry)())())())())()
        l_str = self._render(left, registry, ops)
        r_str = self._render(right, registry, ops)
        if self._needs_parens(
            left, precedence, ops, registry, M.false_value
        ) is M.truth_value:
            l_str = "(" + l_str + ")"
        if self._needs_parens(
            right, precedence, ops, registry, M.truth_value
        ) is M.truth_value:
            r_str = "(" + r_str + ")"
        return l_str + print_form + r_str

    def __call__(self):
        return self.result


class RenderDiscoveredEquation(M.Edge):
    """Render an equation record retained by the finite law miner."""

    def __init__(self, equation, registry):
        self.result = self._render(equation, registry)
        super().__init__(
            inputs=M.Pair(equation, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _render(self, equation, registry):
        if M.IdentityCompare(M.Head(equation)(), L.DiscoveredEquationLabel)() is M.false_value:
            return "? = ?"
        body = M.Tail(equation)()
        lhs = M.Head(M.Tail(body)())()
        rhs = M.Head(M.Tail(M.Tail(body)())())()
        left_text = RenderNatExpr(lhs, registry)()
        right_text = RenderNatExpr(rhs, registry)()
        return left_text + " = " + right_text

    def __call__(self):
        return self.result


class RenderOperationValue(M.Edge):
    """Surface text for a ground evaluation, including an undefined cell."""

    def __init__(self, value, registry):
        self.result = "undefined"
        if M.IdentityCompare(value, M.truth_value)() is M.truth_value:
            self.result = "truth_value"
        elif M.IdentityCompare(value, M.false_value)() is M.truth_value:
            self.result = "false_value"
        elif A.IsNat(value, registry)() is M.truth_value:
            self.result = M.GMPRepText(M.NatRepOf(value, registry)())()
        super().__init__(inputs=M.Pair(value, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class RenderOperationCall(M.Edge):
    """Render the supplied term and assignment without evaluating it."""

    def __init__(self, term, environment, operations, registry):
        self.result = "operation(?)"
        if A.IsNat(term, registry)() is M.truth_value:
            self.result = RenderOperationValue(term, registry)()
        elif M.IsPair(term)() is M.truth_value:
            head_args = ExprHeadArgs(term)()
            label = M.Head(head_args)()
            args = M.Head(M.Tail(head_args)())()
            if M.IdentityCompare(label, L.ExprIntLabel)() is M.truth_value:
                self.result = RenderOperationCall(M.Head(args)(), environment, operations, registry)()
            else:
                entry = LookupOperationByLabel(label, operations)()
                if M.IdentityCompare(entry, M.EmptyList)() is M.false_value:
                    if ExactArity(args, M.two, registry)() is M.truth_value:
                        left = RenderOperationCall(M.Head(args)(), environment, operations, registry)()
                        right = RenderOperationCall(M.Head(M.Tail(args)())(), environment, operations, registry)()
                        self.result = M.Head(entry)()() + "(" + left + ", " + right + ")"
        else:
            value = EnvLookup(environment, term)()
            if M.IdentityCompare(value, M.EmptyList)() is M.false_value:
                self.result = RenderOperationValue(value, registry)()
            elif M.IdentityCompare(term, M.EmptyList)() is M.false_value:
                self.result = term()
        super().__init__(
            inputs=M.Pair(term, M.Pair(environment, M.Pair(operations, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormatOperationLawExamples(M.Edge):
    """Render a few ground witnesses as operation calls."""

    def __init__(
        self, equation, witnesses, operations, registry,
        include_trivial=M.false_value,
    ):
        body = M.Tail(equation)()
        variables = M.Head(body)()
        lhs = M.Head(M.Tail(body)())()
        rhs = M.Head(M.Tail(M.Tail(body)())())()
        self.result = self._format(
            lhs, rhs, variables, witnesses, operations,
            registry, M.three, "", include_trivial,
        )
        if M.Compare(M.Char(self.result), M.Char(""))() is M.truth_value:
            if include_trivial is M.false_value:
                self.result = self._format(
                    lhs, rhs, variables, witnesses, operations,
                    registry, M.three, "", M.truth_value,
                )
        super().__init__(
            inputs=M.Pair(
                equation,
                M.Pair(
                    witnesses,
                    M.Pair(
                        operations,
                        M.Pair(registry, M.Pair(include_trivial, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _format(self, lhs, rhs, variables, witnesses, operations, registry,
                remaining, out, include_trivial):
        if M.IdentityCompare(witnesses, M.EmptyList)() is M.truth_value:
            return out
        if M.NatEq(remaining, M.Zero, registry)() is M.truth_value:
            return out
        witness = M.Head(witnesses)()
        assignment = M.Head(witness)()
        first_arg = M.Head(assignment)()
        second_arg = M.Head(M.Tail(assignment)())()
        first_is_zero = M.NatEq(first_arg, M.Zero, registry)()
        second_is_zero = M.NatEq(second_arg, M.Zero, registry)()
        args_are_equal = M.NatEq(first_arg, second_arg, registry)()
        trivial_pair = M.OrAtom(
            first_is_zero,
            M.OrAtom(second_is_zero, args_are_equal)(),
        )()
        if M.AndAtom(M.IdentityCompare(include_trivial, M.false_value)(), trivial_pair)() is M.truth_value:
            return self._format(
                lhs, rhs, variables, M.Tail(witnesses)(), operations,
                registry, remaining, out, include_trivial,
            )
        environment = ZipEnvironment(variables, assignment)()
        left_text = RenderOperationCall(lhs, environment, operations, registry)()
        right_text = RenderOperationCall(rhs, environment, operations, registry)()
        example = left_text + " == " + right_text
        if M.Compare(M.Char(out), M.Char(""))() is M.truth_value:
            next_out = example
        else:
            next_out = out + "; " + example
        pred = M.NatPred(remaining, registry)()
        next_remaining = M.Head(pred)()
        next_registry = M.Head(M.Tail(pred)())()
        return self._format(
            lhs, rhs, variables, M.Tail(witnesses)(), operations,
            next_registry, next_remaining, next_out, include_trivial,
        )

    def __call__(self):
        return self.result


class ExprDegreeBound(M.Edge):
    """
    Structural upper bound on the degree of an admitted expression term in
    one variable: the variable itself has degree 1, any other atom 0,
    ExprAdd takes the larger bound, ExprMul the sum, ExprPow(a, k) k times
    the bound of a.
    Result: Pair(degree_nat, Pair(registry, EmptyList)), or Pair(EmptyList, ...) when the
    term lies outside the admitted fragment.
    """

    def __init__(self, term, variable, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, M.Pair(term, M.EmptyList)
            )()
            ops = M.Head(built)()
        self.result = self._bound(term, variable, registry, ops)
        super().__init__(
            inputs=M.Pair(term, M.Pair(variable, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _refuse(self, registry):
        return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

    def _bound(self, term, variable, registry, ops):
        if M.IsPair(term)() is M.false_value:
            if A.IsNat(term, registry)() is M.truth_value:
                return M.Pair(M.Zero, M.Pair(registry, M.EmptyList))
            if M.Compare(term, variable)() is M.truth_value:
                return M.Pair(M.one, M.Pair(registry, M.EmptyList))
            return M.Pair(M.Zero, M.Pair(registry, M.EmptyList))
        head_args = ExprHeadArgs(term)()
        head = M.Head(head_args)()
        args = M.Head(M.Tail(head_args)())()
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            return M.Pair(M.Zero, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
            base_res = self._bound(M.Head(args)(), variable, registry, ops)
            base_deg = M.Head(base_res)()
            reg1 = M.Head(M.Tail(base_res)())()
            exponent = M.Head(M.Tail(args)())()
            if M.IdentityCompare(base_deg, M.EmptyList)() is M.truth_value:
                return self._refuse(reg1)
            if A.IsNat(exponent, reg1)() is M.false_value:
                return self._refuse(reg1)
            return A.Multiply(exponent, base_deg, reg1)()
        entry = LookupOperationByLabel(head, ops)()
        if M.IdentityCompare(entry, M.EmptyList)() is M.truth_value:
            return self._refuse(registry)
        rule = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(entry)())())())())())())()
        if M.Compare(rule, M.Char("refuse"))() is M.truth_value:
            return self._refuse(registry)
        left_res = self._bound(M.Head(args)(), variable, registry, ops)
        left_deg = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        if M.IdentityCompare(left_deg, M.EmptyList)() is M.truth_value:
            return self._refuse(reg1)
        right_res = self._bound(M.Head(M.Tail(args)())(), variable, reg1, ops)
        right_deg = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        if M.IdentityCompare(right_deg, M.EmptyList)() is M.truth_value:
            return self._refuse(reg2)
        if M.Compare(rule, M.Char("sum"))() is M.truth_value:
            return A.Add(left_deg, right_deg, reg2)()
        if M.NatLess(left_deg, right_deg, reg2)() is M.truth_value:
            return M.Pair(right_deg, M.Pair(reg2, M.EmptyList))
        return M.Pair(left_deg, M.Pair(reg2, M.EmptyList))

    def __call__(self):
        return self.result


class EvaluateNatExpr(M.Edge):
    """
    Evaluates an admitted expression term at an environment (a chain of
    Pair(variable, Pair(nat, EmptyList))) with the machine's own Add, Multiply,
    and Peano NatPred recursion.
    Result: Pair(nat, Pair(registry, EmptyList)), or Pair(EmptyList, ...) when the
    term is outside the fragment or a variable is unbound.
    """

    def __init__(self, term, environment, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, M.Pair(term, M.EmptyList)
            )()
            ops = M.Head(built)()
        self.result = self._eval(term, environment, registry, ops)
        super().__init__(
            inputs=M.Pair(term, M.Pair(environment, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _refuse(self, registry):
        return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

    def _eval(self, term, environment, registry, ops):
        if M.IsPair(term)() is M.false_value:
            if A.IsNat(term, registry)() is M.truth_value:
                return M.Pair(term, M.Pair(registry, M.EmptyList))
            value = EnvLookup(environment, term)()
            if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                return self._refuse(registry)
            return M.Pair(value, M.Pair(registry, M.EmptyList))
        head_args = ExprHeadArgs(term)()
        head = M.Head(head_args)()
        args = M.Head(M.Tail(head_args)())()
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            if ExactArity(args, M.one, registry)() is M.false_value:
                return self._refuse(registry)
            constant = M.Head(args)()
            if A.IsNat(constant, registry)() is M.false_value:
                return self._refuse(registry)
            return M.Pair(constant, M.Pair(registry, M.EmptyList))
        if ExactArity(args, M.two, registry)() is M.false_value:
            return self._refuse(registry)
        if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
            base_res = self._eval(M.Head(args)(), environment, registry, ops)
            base = M.Head(base_res)()
            reg1 = M.Head(M.Tail(base_res)())()
            if M.IdentityCompare(base, M.EmptyList)() is M.truth_value:
                return self._refuse(reg1)
            exponent_res = self._eval(
                M.Head(M.Tail(args)())(), environment, reg1, ops
            )
            exponent = M.Head(exponent_res)()
            reg2 = M.Head(M.Tail(exponent_res)())()
            if M.IdentityCompare(exponent, M.EmptyList)() is M.truth_value:
                return self._refuse(reg2)
            if A.IsNat(exponent, reg2)() is M.false_value:
                return self._refuse(reg2)
            return NatPowPeano(base, exponent, reg2)()
        entry = LookupOperationByLabel(head, ops)()
        if M.IdentityCompare(entry, M.EmptyList)() is M.truth_value:
            return self._refuse(registry)
        left_res = self._eval(M.Head(args)(), environment, registry, ops)
        left = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return self._refuse(reg1)
        right_res = self._eval(M.Head(M.Tail(args)())(), environment, reg1, ops)
        right = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            return self._refuse(reg2)
        # The operation is chosen by the label the term carries, and every
        # branch names one of the machine's arithmetic edges directly. No
        # class is read out of machine data and called: that is a host
        # callable as a machine parameter (CTM-ODR-5 3.3). The register above
        # still decides which labels are admitted and what metadata they
        # carry -- it describes operations, it does not execute them.
        # The operation is chosen by the label the term carries, and every
        # branch names one of the machine's arithmetic edges directly. No
        # class is read out of machine data and called: that is a host
        # callable as a machine parameter (CTM-ODR-5 3.3). The register above
        # still decides which labels are admitted and what metadata they
        # carry -- it describes operations, it does not execute them.
        #
        # Nothing is entered into the constructor registry here. An applied
        # edge would be registered under a label the register has already
        # admitted and described, so it adds no operation the scan could not
        # already find, while costing an atom allocation -- and therefore a
        # uuid4 -- on every single evaluation.
        computed = M.EmptyList
        if M.IdentityCompare(head, L.ExprAddLabel)() is M.truth_value:
            computed = A.Add(left, right, reg2)()
        if M.IdentityCompare(head, L.ExprMulLabel)() is M.truth_value:
            computed = A.Multiply(left, right, reg2)()
        if M.IdentityCompare(head, L.ExprModuloLabel)() is M.truth_value:
            computed = A.Modulo(left, right, reg2)()
        if M.IdentityCompare(head, L.ExprSubtractLabel)() is M.truth_value:
            computed = A.NatSubtract(left, right, reg2)()
        if M.IdentityCompare(head, L.ExprGcdLabel)() is M.truth_value:
            computed = A.Gcd(left, right, reg2)()
        if M.IsPair(computed)() is M.false_value:
            return self._refuse(reg2)
        if A.IsNat(M.Head(computed)(), reg2)() is M.false_value:
            return self._refuse(reg2)
        return computed

    def __call__(self):
        return self.result


class ValidPolynomialVariables(M.Edge):
    """
    True iff `variables` is a chain of distinct, non-numeric, non-pair
    atoms (the admitted variable vocabulary of the polynomial fragment).
    """

    def __init__(self, variables, registry):
        self.registry = registry
        self.result = self._valid(variables, registry)
        super().__init__(
            inputs=M.Pair(variables, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _valid(self, variables, registry, seen=M.EmptyList):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            return M.truth_value
        if M.IsPair(variables)() is M.false_value:
            return M.false_value
        variable = M.Head(variables)()
        if M.IsPair(variable)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(variable, M.EmptyList)() is M.truth_value:
            return M.false_value
        if A.IsNat(variable, registry)() is M.truth_value:
            return M.false_value
        if ChainHasTerm(seen, variable)() is M.truth_value:
            return M.false_value
        return self._valid(
            M.Tail(variables)(), registry, M.Pair(variable, seen)
        )

    def __call__(self):
        return self.result


class AdmittedPolynomial(M.Edge):
    """
    Checks exact syntax and coverage of a term against the admitted
    polynomial fragment in `variables`: Nats, the variables themselves,
    ExprInt of a Nat, and binary ExprAdd / ExprMul / ExprPow with admitted
    children (an ExprPow exponent must be a Nat).
    """

    def __init__(self, term, variables, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, M.Pair(term, M.EmptyList)
            )()
            ops = M.Head(built)()
        self.result = self._admitted(term, variables, registry, ops)
        super().__init__(
            inputs=M.Pair(
                term,
                M.Pair(variables, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _admitted(self, term, variables, registry, ops):
        if A.IsNat(term, registry)() is M.truth_value:
            return M.truth_value
        if M.IsPair(term)() is M.false_value:
            return ChainHasTerm(variables, term)()
        head_args = ExprHeadArgs(term)()
        head = M.Head(head_args)()
        args = M.Head(M.Tail(head_args)())()
        if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
            if ExactArity(args, M.one, registry)() is M.false_value:
                return M.false_value
            return A.IsNat(M.Head(args)(), registry)()
        if ExactArity(args, M.two, registry)() is M.false_value:
            return M.false_value
        left = M.Head(args)()
        right = M.Head(M.Tail(args)())()
        if M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
            if A.IsNat(right, registry)() is M.false_value:
                return M.false_value
            return self._admitted(left, variables, registry, ops)
        entry = LookupOperationByLabel(head, ops)()
        if M.IdentityCompare(entry, M.EmptyList)() is M.truth_value:
            return M.false_value
        polynomial = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(entry)())())())())())()
        if M.IdentityCompare(polynomial, M.false_value)() is M.truth_value:
            return M.false_value
        return M.AndAtom(
            self._admitted(left, variables, registry, ops),
            self._admitted(right, variables, registry, ops),
        )()

    def __call__(self):
        return self.result


class PolynomialIdentityByGrid(M.Edge):
    """
    Decides whether two admitted expression terms are equal as polynomials in
    the given variables, by evaluating both on the grid {0..d_1} x ... x
    {0..d_k}, d_i the larger structural degree bound of the two sides in x_i.

    Result: Pair(record, Pair(registry, EmptyList)) with
      record = Pair(PolynomialIdentityLabel,
                 Pair(lhs, Pair(rhs, Pair(variables, Pair(degree_chain,
                   Pair(grid_count, Pair(verdict, Pair(witness, EmptyList))))))))
    """

    def __init__(self, lhs, rhs, variables, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, M.Pair(lhs, M.Pair(rhs, M.EmptyList))
            )()
            ops = M.Head(built)()
        self.result = self._decide(lhs, rhs, variables, registry, ops)
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

    def _degrees(self, lhs, rhs, variables, registry, ops):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, M.truth_value, registry
        variable = M.Head(variables)()
        left_res = ExprDegreeBound(lhs, variable, registry, ops)()
        left_deg = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        right_res = ExprDegreeBound(rhs, variable, reg1, ops)()
        right_deg = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        if M.IdentityCompare(left_deg, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, M.false_value, reg2
        if M.IdentityCompare(right_deg, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, M.false_value, reg2
        degree = left_deg
        if M.NatLess(left_deg, right_deg, reg2)() is M.truth_value:
            degree = right_deg
        count_res = A.Add(degree, M.one, reg2)()
        count = M.Head(count_res)()
        reg3 = M.Head(M.Tail(count_res)())()
        domain_res = BuildNatRange(M.Zero, count, reg3)()
        domain = M.Head(domain_res)()
        reg4 = M.Head(M.Tail(domain_res)())()
        rest_degrees, rest_domains, admitted, reg5 = self._degrees(
            lhs, rhs, M.Tail(variables)(), reg4, ops
        )
        if admitted is M.false_value:
            return M.EmptyList, M.EmptyList, M.false_value, reg5
        return M.Pair(degree, rest_degrees), M.Pair(domain, rest_domains), M.truth_value, reg5

    def _decide(self, lhs, rhs, variables, registry, ops):
        if ValidPolynomialVariables(variables, registry)() is M.false_value:
            return self._record(
                lhs, rhs, variables, M.EmptyList, M.Zero, M.EmptyList,
                M.EmptyList, registry,
            )
        if (
            M.AndAtom(
                AdmittedPolynomial(lhs, variables, registry, ops)(),
                AdmittedPolynomial(rhs, variables, registry, ops)(),
            )()
            is M.false_value
        ):
            return self._record(
                lhs, rhs, variables, M.EmptyList, M.Zero, M.EmptyList,
                M.EmptyList, registry,
            )
        degrees, domains, admitted, reg1 = self._degrees(lhs, rhs, variables, registry, ops)
        if admitted is M.false_value:
            return self._record(lhs, rhs, variables, M.EmptyList, M.Zero, M.EmptyList, M.EmptyList, reg1)
        tuples = ProductOfDomains(domains)()
        count_res = ChainLength(tuples, reg1)()
        grid_count = M.Head(count_res)()
        reg2 = M.Head(M.Tail(count_res)())()
        verdict, witness, reg3 = self._first_difference(lhs, rhs, variables, tuples, reg2, ops)
        return self._record(lhs, rhs, variables, degrees, grid_count, verdict, witness, reg3)

    def _first_difference(self, lhs, rhs, variables, tuples, registry, ops):
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return M.truth_value, M.EmptyList, registry
        point = M.Head(tuples)()
        environment = ZipEnvironment(variables, point)()
        left_res = EvaluateNatExpr(lhs, environment, registry, ops)()
        left = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        right_res = EvaluateNatExpr(rhs, environment, reg1, ops)()
        right = M.Head(right_res)()
        reg2 = M.Head(M.Tail(right_res)())()
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return M.false_value, point, reg2
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            return M.false_value, point, reg2
        if M.NatEq(left, right, reg2)() is M.false_value:
            return M.false_value, point, reg2
        return self._first_difference(
            lhs, rhs, variables, M.Tail(tuples)(), reg2, ops
        )

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


class ResidueDomains(M.Edge):
    """
    One copy of the residue domain {0..m-1} per variable.
    Result: Pair(domains_chain, Pair(registry, EmptyList)).
    """

    def __init__(self, variables, modulus, registry):
        self.registry = registry
        self.result = self._domains(variables, modulus, registry)
        super().__init__(
            inputs=M.Pair(
                variables,
                M.Pair(modulus, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _domains(self, variables, modulus, registry):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        domain_res = BuildNatRange(M.Zero, modulus, registry)()
        domain = M.Head(domain_res)()
        reg1 = M.Head(M.Tail(domain_res)())()
        rest_res = self._domains(M.Tail(variables)(), modulus, reg1)
        rest = M.Head(rest_res)()
        reg2 = M.Head(M.Tail(rest_res)())()
        return M.Pair(
            M.Pair(domain, rest),
            M.Pair(reg2, M.EmptyList),
        )

    def __call__(self):
        return self.result


class ResidueTable(M.Edge):
    """
    Exhaustive residue case analysis of one admitted expression term: for
    every residue tuple in {0..m-1}^k, the term's value modulo m (machine
    Modulo over machine evaluation).

    Result: Pair(rows, Pair(image, Pair(registry, EmptyList))) with
      rows   = chain of Pair(residue_tuple, Pair(residue, EmptyList)), grid order
      image  = the set of residues that occur
    """

    def __init__(self, term, variables, modulus, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, M.Pair(term, M.EmptyList)
            )()
            ops = M.Head(built)()
        self.result = self._table(term, variables, modulus, registry, ops)
        super().__init__(
            inputs=M.Pair(term, M.Pair(variables, M.Pair(modulus, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _rows(self, term, variables, modulus, tuples, registry, ops):
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, registry
        point = M.Head(tuples)()
        value_res = EvaluateNatExpr(
            term, ZipEnvironment(variables, point)(), registry, ops
        )()
        value = M.Head(value_res)()
        reg1 = M.Head(M.Tail(value_res)())()
        if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
            residue = M.EmptyList
            reg2 = reg1
        else:
            residue_res = A.Modulo(value, modulus, reg1)()
            residue = M.Head(residue_res)()
            reg2 = M.Head(M.Tail(residue_res)())()
        rest_rows, rest_image, reg3 = self._rows(
            term, variables, modulus, M.Tail(tuples)(), reg2, ops
        )
        image = rest_image
        if M.IdentityCompare(residue, M.EmptyList)() is M.false_value:
            image = SetInsert(residue, rest_image, reg3)()
        return M.Pair(M.Pair(point, M.Pair(residue, M.EmptyList)), rest_rows), image, reg3

    def _table(self, term, variables, modulus, registry, ops):
        domains_res = ResidueDomains(variables, modulus, registry)()
        domains = M.Head(domains_res)()
        reg1 = M.Head(M.Tail(domains_res)())()
        tuples = ProductOfDomains(domains)()
        rows, image, reg2 = self._rows(term, variables, modulus, tuples, reg1, ops)
        return M.Pair(rows, M.Pair(image, M.Pair(reg2, M.EmptyList)))

    def __call__(self):
        return self.result


class CongruenceClasses(M.Edge):
    """
    Exhaustive residue case analysis of a polynomial congruence
    lhs = rhs (mod m): the residue tuples in {0..m-1}^k at which the two
    sides agree modulo m, and those at which they differ.

    Result: Pair(holding, Pair(failing, Pair(registry, EmptyList))).
    """

    def __init__(self, lhs, rhs, variables, modulus, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, M.Pair(lhs, M.Pair(rhs, M.EmptyList))
            )()
            ops = M.Head(built)()
        self.result = self._classes(lhs, rhs, variables, modulus, registry, ops)
        super().__init__(
            inputs=M.Pair(lhs, M.Pair(rhs, M.Pair(variables, M.Pair(modulus, M.Pair(registry, M.EmptyList))))),
            results=self.result,
        )

    def _classes(self, lhs, rhs, variables, modulus, registry, ops):
        domains_res = ResidueDomains(variables, modulus, registry)()
        domains = M.Head(domains_res)()
        reg1 = M.Head(M.Tail(domains_res)())()
        tuples = ProductOfDomains(domains)()
        holding, failing, reg2 = self._partition(
            lhs, rhs, variables, modulus, tuples, reg1, ops
        )
        return M.Pair(holding, M.Pair(failing, M.Pair(reg2, M.EmptyList)))

    def _partition(self, lhs, rhs, variables, modulus, tuples, registry, ops):
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return M.EmptyList, M.EmptyList, registry
        point = M.Head(tuples)()
        environment = ZipEnvironment(variables, point)()
        left_res = EvaluateNatExpr(lhs, environment, registry, ops)()
        left = M.Head(left_res)()
        reg1 = M.Head(M.Tail(left_res)())()
        right_res = EvaluateNatExpr(rhs, environment, reg1, ops)()
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
        rest_holding, rest_failing, reg3 = self._partition(
            lhs, rhs, variables, modulus, M.Tail(tuples)(), reg2, ops
        )
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


class TupleAllUnderMod(M.Edge):
    """
    True iff every coordinate of a tuple chain is a Nat below modulus_nat.
    """

    def __init__(self, tuple_chain, modulus_nat, registry):
        self.registry = registry
        self.result = self._all(tuple_chain, modulus_nat, registry)
        super().__init__(
            inputs=M.Pair(
                tuple_chain,
                M.Pair(modulus_nat, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _all(self, tuple_chain, modulus_nat, registry):
        if M.IdentityCompare(tuple_chain, M.EmptyList)() is M.truth_value:
            return M.truth_value
        if M.NatLess(M.Head(tuple_chain)(), modulus_nat, registry)() is M.false_value:
            return M.false_value
        return self._all(M.Tail(tuple_chain)(), modulus_nat, registry)

    def __call__(self):
        return self.result


class TupleAllPositive(M.Edge):
    """
    True iff every coordinate of a tuple chain is a positive Nat.
    """

    def __init__(self, tuple_chain, registry):
        self.registry = registry
        self.result = self._all(tuple_chain, registry)
        super().__init__(
            inputs=M.Pair(
                tuple_chain,
                M.Pair(registry, M.EmptyList),
            ),
            results=self.result,
        )

    def _all(self, tuple_chain, registry):
        if M.IdentityCompare(tuple_chain, M.EmptyList)() is M.truth_value:
            return M.truth_value
        if M.NatEq(M.Head(tuple_chain)(), M.Zero, registry)() is M.truth_value:
            return M.false_value
        return self._all(M.Tail(tuple_chain)(), registry)

    def __call__(self):
        return self.result


class TupleNatEqual(M.Edge):
    """
    Coordinate-wise Nat equality of two tuple chains.
    """

    def __init__(self, tuple_a, tuple_b, registry):
        self.registry = registry
        self.result = self._equal(tuple_a, tuple_b, registry)
        super().__init__(
            inputs=M.Pair(
                tuple_a,
                M.Pair(tuple_b, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _equal(self, tuple_a, tuple_b, registry):
        if M.IdentityCompare(tuple_a, M.EmptyList)() is M.truth_value:
            return M.IdentityCompare(tuple_b, M.EmptyList)()
        if M.IdentityCompare(tuple_b, M.EmptyList)() is M.truth_value:
            return M.false_value
        h1 = M.Head(tuple_a)()
        h2 = M.Head(tuple_b)()
        heads_differ = M.AndAtom(
            M.NotAtom(M.IdentityCompare(h1, h2)())(),
            M.NotAtom(M.NatEq(h1, h2, registry)())(),
        )()
        if (
            M.IdentityCompare(heads_differ, M.truth_value)()
            is M.truth_value
        ):
            return M.false_value
        return self._equal(M.Tail(tuple_a)(), M.Tail(tuple_b)(), registry)

    def __call__(self):
        return self.result


class ProjectEnvToSubtuple(M.Edge):
    """
    Projects an environment onto a sub-variable chain: the chain of the
    values bound to sub_vars, in order (EmptyList for an unbound variable).
    """

    def __init__(self, environment, sub_vars):
        self.result = self._project(environment, sub_vars)
        super().__init__(
            inputs=M.Pair(environment, M.Pair(sub_vars, M.EmptyList)),
            results=self.result,
        )

    def _project(self, environment, sub_vars):
        if M.IdentityCompare(sub_vars, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        val = EnvLookup(environment, M.Head(sub_vars)())()
        return M.Pair(
            val,
            self._project(environment, M.Tail(sub_vars)()),
        )

    def __call__(self):
        return self.result


class LookupResidueRow(M.Edge):
    """
    Looks a residue tuple up in a residue row chain (a chain of
    Pair(tuple, Pair(residue, EmptyList))); EmptyList when absent.
    """

    def __init__(self, rows_chain, target_tuple, registry):
        self.registry = registry
        self.result = self._lookup(rows_chain, target_tuple, registry)
        super().__init__(
            inputs=M.Pair(
                rows_chain,
                M.Pair(target_tuple, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _lookup(self, rows_chain, target_tuple, registry):
        if M.IdentityCompare(rows_chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        row = M.Head(rows_chain)()
        pt = M.Head(row)()
        if TupleNatEqual(pt, target_tuple, registry)() is M.truth_value:
            return M.Head(M.Tail(row)())()
        return self._lookup(M.Tail(rows_chain)(), target_tuple, registry)

    def __call__(self):
        return self.result


class ProjectTensorModulo(M.Edge):
    """
    Projects a ground EvaluationTensor record onto {0..m-1}^k modulo mod_nat,
    yielding the residue rows paired with the sorted unique image set, in the
    MapDomain result shape: Pair(rows, Pair(image, Pair(registry, EmptyList))).
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
        if TupleAllUnderMod(tup, mod_nat, reg1)() is M.false_value:
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
        return M.Pair(rows, M.Pair(sorted_image, M.Pair(reg1, M.EmptyList)))

    def __call__(self):
        return self.result


class BuildNatOperationRegister(M.Edge):
    """
    Discovers supported arithmetic operations present in expression terms.

    Each entry carries the metadata the term-level edges share, so that
    rendering, admission, degree bounding and evaluation all read one
    description of an operation instead of each re-listing its label:

        Pair(name, Pair(variables, Pair(operation_term,
              Pair(print_form, Pair(precedence,
                Pair(polynomial, Pair(degree_rule,
                  Pair(law_depth, EmptyList)))))))

      print_form   the infix rendering, e.g. " + " or " mod "
      precedence   binding tightness; an operand that is itself a registered
                   operation of lower precedence is parenthesised when
                   rendered inside this one
      polynomial   whether the operation belongs to the polynomial fragment
      degree_rule  how the operation combines operand degrees: "max", "sum",
                   or "refuse" when the result is not a polynomial
      law_depth    whether nested candidate terms are bounded or expensive

    The returned register contains only operations found by the machine-term
    walk. An empty input term chain produces an empty register.
    """

    def __init__(self, registry, terms=M.EmptyList):
        self.registry = registry
        entries = self._scan_registry(M.EmptyList)
        entries = self._scan_terms(terms, entries)
        self.result = M.Pair(entries, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(registry, M.Pair(terms, M.EmptyList)),
            results=self.result,
        )

    def _entry(self, label):
        variables = M.Pair(M.Char("x"), M.Pair(M.Char("y"), M.EmptyList))
        name = M.Char("operation")
        print_form = M.Char(" ? ")
        precedence = M.two
        polynomial = M.false_value
        degree_rule = M.Char("refuse")
        law_depth = M.Char("bounded")
        if M.IdentityCompare(label, L.ExprAddLabel)() is M.truth_value:
            name = M.Char("add")
            print_form = M.Char(" + ")
            polynomial = M.truth_value
            degree_rule = M.Char("max")
        elif M.IdentityCompare(label, L.ExprMulLabel)() is M.truth_value:
            name = M.Char("mul")
            print_form = M.Char("*")
            precedence = M.three
            polynomial = M.truth_value
            degree_rule = M.Char("sum")
        elif M.IdentityCompare(label, L.ExprPowLabel)() is M.truth_value:
            name = M.Char("pow")
            print_form = M.Char("^")
            precedence = M.four
            law_depth = M.Char("expensive")
        elif M.IdentityCompare(label, L.ExprModuloLabel)() is M.truth_value:
            name = M.Char("modulo")
            print_form = M.Char(" mod ")
            precedence = M.one
        elif M.IdentityCompare(label, L.ExprSubtractLabel)() is M.truth_value:
            name = M.Char("natural subtraction")
            print_form = M.Char(" - ")
        elif M.IdentityCompare(label, L.ExprGcdLabel)() is M.truth_value:
            name = M.Char("gcd")
            print_form = M.Char(" gcd ")
            precedence = M.three
        else:
            return M.EmptyList
        operation = M.Pair(label, variables)
        return M.Pair(
            name,
            M.Pair(
                variables,
                M.Pair(
                    operation,
                    M.Pair(
                        print_form,
                        M.Pair(
                            precedence,
                            M.Pair(
                                polynomial,
                                M.Pair(degree_rule, M.Pair(law_depth, M.EmptyList)),
                            ),
                        ),
                    ),
                ),
            ),
        )

    def _scan_registry(self, entries):
        """Scan the machine's own edge registry for the arithmetic it has run.

        TreeEntries walks the constructor registry, and every operation the
        machine has applied is entered there under the label the term carried.
        An entry is an operation when it is an edge whose label names one, so
        the catalog is what the machine has actually run rather than a list
        written out by hand. This is the scan that finds the whole operation
        set; the term walk below only adds operations named by the terms it
        is handed.
        """
        registered = TreeEntries(self.registry)()
        return self._scan_entries(registered, entries)

    def _scan_entries(self, remaining, entries):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return entries
        if M.IsPair(remaining)() is M.false_value:
            return entries
        entry = M.Head(remaining)()
        fact = M.Head(M.Tail(entry)())()
        entries = self._scan_registered(fact, entries)
        return self._scan_entries(M.Tail(remaining)(), entries)

    def _scan_registered(self, fact, entries):
        if M.IsEdge(fact, self.registry)() is M.false_value:
            return entries
        constructor = M.GetConstructor(fact, self.registry)()
        if M.IdentityCompare(constructor, M.EmptyList)() is M.truth_value:
            return entries
        label = M.Head(constructor)()
        found = self._entry(label)
        if M.IdentityCompare(found, M.EmptyList)() is M.false_value:
            prior = LookupOperationByLabel(label, entries)()
            if M.IdentityCompare(prior, M.EmptyList)() is M.truth_value:
                entries = ChainAppendEnd(entries, found)()
        return entries

    def _scan_terms(self, terms, entries):
        """Walk the chain of supplied terms looking for operations.

        A malformed term chain has a tail that is a bare atom rather than a
        chain, and taking its head crashes. Stopping at the first non-pair
        tail lets the register come back with whatever it did find and leaves
        the caller's own admission to refuse the malformed term.
        """
        if M.IdentityCompare(terms, M.EmptyList)() is M.truth_value:
            return entries
        if M.IsPair(terms)() is M.false_value:
            return entries
        entries = self._scan(M.Head(terms)(), entries)
        return self._scan_terms(M.Tail(terms)(), entries)

    def _scan(self, term, entries):
        if M.IsPair(term)() is M.false_value:
            return entries
        label = M.Head(term)()
        args = M.Tail(term)()
        if M.IdentityCompare(label, L.ExprIntLabel)() is M.truth_value:
            return entries
        if ExactArity(args, M.two, self.registry)() is M.truth_value:
            found = self._entry(label)
            if M.IdentityCompare(found, M.EmptyList)() is M.false_value:
                prior = LookupOperationByLabel(label, entries)()
                if M.IdentityCompare(prior, M.EmptyList)() is M.truth_value:
                    entries = ChainAppendEnd(entries, found)()
        return self._scan_args(args, entries)

    def _scan_args(self, args, entries):
        """Walk the argument chain of a term looking for nested operations.

        A malformed term such as Pair(label, Pair(x, x)) has a tail that is a
        bare atom rather than a chain, and taking the head of that tail
        crashes. Stopping at the first non-pair tail lets the walk end and
        the caller's own admission decide whether the term was well formed,
        instead of the register raising before it can.
        """
        if M.IdentityCompare(args, M.EmptyList)() is M.truth_value:
            return entries
        if M.IsPair(args)() is M.false_value:
            return entries
        entries = self._scan(M.Head(args)(), entries)
        return self._scan_args(M.Tail(args)(), entries)

    def __call__(self):
        return self.result


class BuildOperationTensor(M.Edge):
    """Precomputes every admitted operation's result over the tested domain.

    Mining a law currently re-evaluates the same operation cells once per
    candidate law and once per assignment, which is the bulk of the work: a
    two-variable domain needs 121 cells per operation, and each candidate
    touches many of them again. Building the grid once and reading it makes
    the cost of testing a law proportional to the lookups it needs rather
    than to fresh evaluations.

    Layout is a chain of Pair(operation_label, rows), where rows is a chain
    of Pair(a, cells) and cells is a chain of Pair(b, result). The nesting
    keeps a lookup proportional to the operation count plus the domain size
    instead of to the whole tensor, and it lets a nested term such as
    op(op(x, y), z) be answered by two lookups.
    """

    def __init__(self, domain, operation_register, registry):
        self.registry = registry
        self.result = self._build(domain, operation_register, registry)
        super().__init__(
            inputs=M.Pair(
                domain,
                M.Pair(operation_register, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _build(self, domain, ops, registry):
        acc = M.EmptyList
        cur = ops
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            entry = M.Head(cur)()
            label = M.Head(M.Head(M.Tail(M.Tail(entry)())())())()
            acc = M.Pair(M.Pair(label, self._rows(domain, domain, label, registry, ops)), acc)
            cur = M.Tail(cur)()
        return self._reverse(acc)

    def _rows(self, domain, values, label, registry, ops):
        acc = M.EmptyList
        cur = domain
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            a = M.Head(cur)()
            entry = LookupOperationByLabel(label, ops)()
            row_message = "Evaluating tensor row: "
            if M.IdentityCompare(cur, domain)() is M.truth_value:
                row_message = "Evaluating the first row of the tensor: "
            NaturalPlaygroundDebugEmit(M.Char(
                row_message + M.Head(entry)()() + " with first argument "
                + RenderOperationValue(a, registry)()
            ))()
            acc = M.Pair(M.Pair(a, self._cells(values, a, label, registry, ops)), acc)
            cur = M.Tail(cur)()
        return self._reverse(acc)

    def _cells(self, values, a, label, registry, ops):
        acc = M.EmptyList
        cur = values
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            b = M.Head(cur)()
            term = M.Pair(label, M.Pair(a, M.Pair(b, M.EmptyList)))
            call_text = RenderOperationCall(term, M.EmptyList, ops, registry)()
            NaturalPlaygroundDebugEmit(M.Char("Evaluating tensor cell: " + call_text))()
            evaluated = EvaluateNatExpr(term, M.EmptyList, registry, ops)()
            NaturalPlaygroundDebugEmit(M.Char(
                "Evaluated tensor cell: " + call_text + " -> "
                + RenderOperationValue(M.Head(evaluated)(), M.Head(M.Tail(evaluated)())())()
            ))()
            acc = M.Pair(M.Pair(b, M.Head(evaluated)()), acc)
            cur = M.Tail(cur)()
        return self._reverse(acc)

    def _reverse(self, chain):
        out = M.EmptyList
        cur = chain
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            out = M.Pair(M.Head(cur)(), out)
            cur = M.Tail(cur)()
        return out


class TensorOperationValue(M.Edge):
    """Evaluates an expression term by reading the operation result tensor.

    A bare natural is itself; an operation application reads its two operands
    from the tensor and then the cell for the pair. Recursing on the operands
    is what lets a nested term such as op(op(x, y), z) be answered by two
    lookups instead of a fresh evaluation of the whole term.
    """

    def __init__(self, tensor, term, environment, registry):
        self.registry = registry
        self.result = self._value(tensor, term, environment, registry)
        super().__init__(
            inputs=M.Pair(
                tensor,
                M.Pair(term, M.Pair(environment, M.Pair(registry, M.EmptyList))),
            ),
            results=self.result,
        )

    def _value(self, tensor, term, environment, registry):
        if M.IsPair(term)() is M.false_value:
            # A leaf is either a natural standing for itself or a variable
            # that has to be read out of the environment before it can index
            # a cell; skipping that lookup would make every variable read as
            # undefined.
            if A.IsNat(term, registry)() is M.truth_value:
                return M.Pair(term, M.Pair(registry, M.EmptyList))
            value = EnvLookup(environment, term)()
            if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
            return M.Pair(value, M.Pair(registry, M.EmptyList))
        args = M.Tail(term)()
        label = M.Head(term)()
        left_res = self._value(tensor, M.Head(args)(), environment, registry)
        left_value = M.Head(left_res)()
        if M.IdentityCompare(left_value, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        right_res = self._value(
            tensor, M.Head(M.Tail(args)())(), environment, registry
        )
        right_value = M.Head(right_res)()
        if M.IdentityCompare(right_value, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        cell = self._cell(tensor, label, left_value, right_value)
        return M.Pair(cell, M.Pair(registry, M.EmptyList))

    def _cell(self, tensor, label, a, b):
        rows = self._operation(tensor, label)
        if M.IdentityCompare(rows, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        cells = self._row(rows, a)
        if M.IdentityCompare(cells, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return self._value_of(cells, b)

    def _operation(self, tensor, label):
        cur = tensor
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            entry = M.Head(cur)()
            if M.IdentityCompare(M.Head(entry)(), label)() is M.truth_value:
                return M.Tail(entry)()
            cur = M.Tail(cur)()
        return M.EmptyList

    def _row(self, rows, a):
        cur = rows
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            entry = M.Head(cur)()
            if M.IdentityCompare(M.Head(entry)(), a)() is M.truth_value:
                return M.Tail(entry)()
            cur = M.Tail(cur)()
        return M.EmptyList

    def _value_of(self, cells, b):
        cur = cells
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            entry = M.Head(cur)()
            if M.IdentityCompare(M.Head(entry)(), b)() is M.truth_value:
                return M.Tail(entry)()
            cur = M.Tail(cur)()
        return M.EmptyList


class LookupOperationByLabel(M.Edge):
    """
    Finds the register entry whose operation term carries `label`.
    Returns the entry, or EmptyList when the label names no registered
    operation. This is the single lookup the term-level edges share, so an
    operation's rendering, admission and degree rule are read from one
    description rather than re-listed in each edge.
    """

    def __init__(self, label, operation_register):
        self.result = self._seek(label, operation_register)
        super().__init__(
            inputs=M.Pair(label, M.Pair(operation_register, M.EmptyList)),
            results=self.result,
        )

    def _seek(self, label, cur):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(cur)()
        operation = M.Head(M.Tail(M.Tail(entry)())())()
        entry_label = M.Head(operation)()
        if M.IdentityCompare(entry_label, label)() is M.truth_value:
            return entry
        return self._seek(label, M.Tail(cur)())

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
        val_a = EnvLookup(env_a, var)()
        if M.IdentityCompare(val_a, M.EmptyList)() is M.false_value:
            if M.NatEq(val_a, val_b, registry)() is M.false_value:
                return M.false_value
        return self._envs_compatible(env_a, M.Tail(env_b)(), registry)

    def _merge_envs(self, env_a, env_b):
        if M.IdentityCompare(env_b, M.EmptyList)() is M.truth_value:
            return env_a
        binding = M.Head(env_b)()
        var = M.Head(binding)()
        if M.IdentityCompare(EnvLookup(env_a, var)(), M.EmptyList)() is M.false_value:
            return self._merge_envs(env_a, M.Tail(env_b)())
        return self._merge_envs(ChainAppendEnd(env_a, binding)(), M.Tail(env_b)())

    def _admits_tuple(self, positive_only, tuple_chain, registry):
        admits = M.OrAtom(
            M.IdentityCompare(positive_only, M.false_value)(),
            TupleAllPositive(tuple_chain, registry)(),
        )()
        if M.IdentityCompare(admits, M.truth_value)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _values_agree(self, val_l, val_r, registry):
        if A.IsNat(val_l, registry)() is M.false_value:
            return M.false_value
        if A.IsNat(val_r, registry)() is M.false_value:
            return M.false_value
        agrees = M.OrAtom(
            M.IdentityCompare(val_l, val_r)(),
            M.NatEq(val_l, val_r, registry)(),
        )()
        if M.IdentityCompare(agrees, M.truth_value)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _find(
        self, lhs_tensor, rhs_tensor, lhs_vars, rhs_vars, positive_only,
        registry, cur_l=M.EmptyList, cur_r=M.EmptyList,
        initialized=M.false_value, scanning_rhs=M.false_value,
    ):
        entries_l = M.Head(M.Tail(M.Tail(lhs_tensor)())())()
        entries_r = M.Head(M.Tail(M.Tail(rhs_tensor)())())()
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur_l = entries_l
            initialized = M.truth_value
        if M.IdentityCompare(cur_l, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

        ent_l = M.Head(cur_l)()
        tup_l = M.Head(M.Tail(ent_l)())()
        val_l = M.Head(M.Tail(M.Tail(ent_l)())())()
        if self._admits_tuple(positive_only, tup_l, registry) is M.false_value:
            return self._find(
                lhs_tensor, rhs_tensor, lhs_vars, rhs_vars, positive_only,
                registry, M.Tail(cur_l)(), M.EmptyList, initialized,
                M.false_value,
            )
        if M.IdentityCompare(scanning_rhs, M.false_value)() is M.truth_value:
            cur_r = entries_r
            scanning_rhs = M.truth_value
        if M.IdentityCompare(cur_r, M.EmptyList)() is M.truth_value:
            return self._find(
                lhs_tensor, rhs_tensor, lhs_vars, rhs_vars, positive_only,
                registry, M.Tail(cur_l)(), M.EmptyList, initialized,
                M.false_value,
            )

        ent_r = M.Head(cur_r)()
        tup_r = M.Head(M.Tail(ent_r)())()
        val_r = M.Head(M.Tail(M.Tail(ent_r)())())()
        if self._admits_tuple(positive_only, tup_r, registry) is M.truth_value:
            if self._values_agree(val_l, val_r, registry) is M.truth_value:
                env_l = ZipEnvironment(lhs_vars, tup_l)()
                env_r = ZipEnvironment(rhs_vars, tup_r)()
                if self._envs_compatible(env_l, env_r, registry) is M.truth_value:
                    merged = self._merge_envs(env_l, env_r)
                    return M.Pair(merged, M.Pair(registry, M.EmptyList))
        return self._find(
            lhs_tensor, rhs_tensor, lhs_vars, rhs_vars, positive_only,
            registry, cur_l, M.Tail(cur_r)(), initialized, scanning_rhs,
        )

    def __call__(self):
        return self.result


class BuildExprGroundTensor(M.Edge):
    """
    Builds the ground EvaluationTensor of one admitted expression term over
    one shared domain copy per variable, using the machine's own
    ProductOfDomains, ZipEnvironment and EvaluateNatExpr.
    Result: Pair(tensor_node, Pair(registry, EmptyList)).
    """

    def __init__(
        self, term, vars_chain, domain_chain, op_label_char, registry
    ):
        self.registry = registry
        self.result = self._build(
            term, vars_chain, domain_chain, op_label_char, registry
        )
        super().__init__(
            inputs=M.Pair(
                term,
                M.Pair(
                    vars_chain,
                    M.Pair(
                        domain_chain,
                        M.Pair(
                            op_label_char,
                            M.Pair(registry, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _build(
        self, term, vars_chain, domain_chain, op_label_char, registry,
        remaining=M.EmptyList, domains=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            remaining = vars_chain
            initialized = M.truth_value
        if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            return self._build(
                term, vars_chain, domain_chain, op_label_char, registry,
                M.Tail(remaining)(), M.Pair(domain_chain, domains), initialized,
            )
        tuples = ProductOfDomains(domains)()
        return EvaluateOperationTensor(
            op_label_char, vars_chain, term, tuples, registry
        )()

    def __call__(self):
        return self.result


class DiscoverExprObstructions(M.Edge):
    """
    Pure-machine Cartesian congruence & coordinate projection analyzer.
    Given admitted polynomial expressions `lhs` and `rhs`, evaluates their
    ground EvaluationTensors over 0..bound_nat-1 and projects across each
    candidate modulus m in `moduli_chain`:
      1. the images of `lhs` and `rhs` modulo m.
      2. EvaluateSetRelation disjointness and intersection of `rhs_image` and `lhs_image`.
      3. the partition of {0..m-1}^k into `holding` and `failing` chains.
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
        domain_chain=M.EmptyList,
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
            domain_chain,
        )
        super().__init__(
            inputs=M.Pair(
                lhs,
                M.Pair(
                    rhs,
                    M.Pair(
                        bound_nat,
                        M.Pair(
                            moduli_chain,
                            M.Pair(registry, M.Pair(domain_chain, M.EmptyList)),
                        ),
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
        domain_chain=M.EmptyList,
        scan_cursor=M.EmptyList,
        scan_discoveries=M.EmptyList,
        scan_registry=M.EmptyList,
        scan_initialized=M.false_value,
    ):
        reg = registry
        lhs_vars = M.Head(ExtractExprVariables(lhs, reg)())()
        rhs_vars = M.Head(ExtractExprVariables(rhs, reg)())()
        all_vars = ChainMergeUnique(lhs_vars, rhs_vars)()

        if M.IdentityCompare(lhs_tensor, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(domain_chain, M.EmptyList)() is M.false_value:
                domain = domain_chain
            else:
                dom_res = BuildNatRange(M.Zero, bound_nat, reg)()
                domain = M.Head(dom_res)()
                reg = M.Head(M.Tail(dom_res)())()
            lt_res = BuildExprGroundTensor(
                lhs, lhs_vars, domain, M.Char("lhs"), reg
            )()
            lhs_tensor = M.Head(lt_res)()
            reg = M.Head(M.Tail(lt_res)())()
            rt_res = BuildExprGroundTensor(
                rhs, rhs_vars, domain, M.Char("rhs"), reg
            )()
            rhs_tensor = M.Head(rt_res)()
            reg = M.Head(M.Tail(rt_res)())()

        if M.IdentityCompare(scan_initialized, M.false_value)() is M.truth_value:
            discoveries = M.EmptyList
            cur_m = moduli_chain
        else:
            discoveries = scan_discoveries
            cur_m = scan_cursor
            reg = scan_registry
        if M.IdentityCompare(cur_m, M.EmptyList)() is M.truth_value:
            return M.Pair(discoveries, M.Pair(reg, M.EmptyList))
        if M.IdentityCompare(cur_m, M.EmptyList)() is M.false_value:
            m_nat = M.Head(cur_m)()

            proj_l = ProjectTensorModulo(lhs, lhs_vars, lhs_tensor, m_nat, reg)()
            rows_l = M.Head(proj_l)()
            lhs_image = M.Head(M.Tail(proj_l)())()
            reg = M.Head(M.Tail(M.Tail(proj_l)())())()

            proj_r = ProjectTensorModulo(rhs, rhs_vars, rhs_tensor, m_nat, reg)()
            rows_r = M.Head(proj_r)()
            rhs_image = M.Head(M.Tail(proj_r)())()
            reg = M.Head(M.Tail(M.Tail(proj_r)())())()

            rel_res = EvaluateSetRelation(rhs_image, lhs_image, reg)()
            is_disjoint = M.Head(rel_res)()
            inter_raw = M.Head(M.Tail(rel_res)())()
            reg = M.Head(M.Tail(M.Tail(rel_res)())())()
            inter_set = SortNatChain(inter_raw, reg)()

            holding, failing, reg = self._partition_congruence(
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

            if (
                M.IdentityCompare(debug_trace, M.false_value)()
                is M.false_value
            ):
                m_val = M.NatRepOf(m_nat, reg)()()
                h_val = M.NatRepOf(holding_count, reg)()()
                f_val = M.NatRepOf(failing_count, reg)()()
                PlaygroundDebugEmit(M.Char(
                    f"modulus m = {m_val}: image(lhs mod {m_val}) = {FormatSetChain(lhs_image, reg)()}, image(rhs mod {m_val}) = {FormatSetChain(rhs_image, reg)()}, intersection = {FormatSetChain(inter_set, reg)()}, holding = {h_val}, failing = {f_val}"
                ))()

            has_failing = M.NotAtom(
                M.IdentityCompare(failing, M.EmptyList)()
            )()
            img_compressed = M.OrAtom(
                M.NatLess(l_img_len, m_nat, reg)(),
                M.NatLess(r_img_len, m_nat, reg)(),
            )()
            coord_restricted = self._any_coord_proper(coord_projs)
            reports_regularity = M.OrAtom(
                M.OrAtom(is_disjoint, img_compressed)(),
                coord_restricted,
            )()

            if (
                M.IdentityCompare(
                    M.AndAtom(
                        M.IdentityCompare(has_failing, M.truth_value)(),
                        M.IdentityCompare(
                            reports_regularity, M.truth_value
                        )(),
                    )(),
                    M.truth_value,
                )()
                is M.truth_value
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
                discoveries = ChainAppendEnd(discoveries, rec)()

        return self._discover(
            lhs,
            rhs,
            bound_nat,
            moduli_chain,
            reg,
            lhs_tensor,
            rhs_tensor,
            debug_trace,
            domain_chain,
            M.Tail(cur_m)(),
            discoveries,
            reg,
            M.truth_value,
        )

    def _residues_agree(self, reml, remr, registry):
        absent = M.OrAtom(
            M.IdentityCompare(reml, M.EmptyList)(),
            M.IdentityCompare(remr, M.EmptyList)(),
        )()
        if M.IdentityCompare(absent, M.truth_value)() is M.truth_value:
            return M.false_value
        return M.OrAtom(
            M.IdentityCompare(reml, remr)(),
            M.NatEq(reml, remr, registry)(),
        )()

    def _partition_congruence(
        self, all_vars, lhs_vars, rhs_vars, rows_l, rows_r, mod_nat, registry
    ):
        """
        Partitions {0..m-1}^k into holding and failing chains from the
        residue rows of lhs and rhs.
        """
        disjoint_vars = self._has_shared_var(lhs_vars, rhs_vars)
        if disjoint_vars is M.false_value:
            return self._partition_disjoint_rows(
                rows_l, rows_r, registry,
                rows_l, rows_r, M.EmptyList, M.EmptyList,
            )

        domains_res = ResidueDomains(all_vars, mod_nat, registry)()
        domains = M.Head(domains_res)()
        reg1 = M.Head(M.Tail(domains_res)())()
        tuples = ProductOfDomains(domains)()
        return self._partition_tuples(
            tuples, all_vars, lhs_vars, rhs_vars, rows_l, rows_r,
            reg1, M.EmptyList, M.EmptyList,
        )

    def _has_shared_var(self, lhs_vars, rhs_vars):
        if M.IdentityCompare(lhs_vars, M.EmptyList)() is M.truth_value:
            return M.false_value
        if ChainHasTerm(rhs_vars, M.Head(lhs_vars)())() is M.truth_value:
            return M.truth_value
        return self._has_shared_var(M.Tail(lhs_vars)(), rhs_vars)

    def _partition_disjoint_rows(
        self, rows_l, rows_r, registry, cur_l, cur_r, holding, failing
    ):
        if M.IdentityCompare(cur_l, M.EmptyList)() is M.truth_value:
            return ChainReverse(holding)(), ChainReverse(failing)(), registry
        rl = M.Head(cur_l)()
        tl = M.Head(rl)()
        reml = M.Head(M.Tail(rl)())()
        if M.IdentityCompare(cur_r, M.EmptyList)() is M.truth_value:
            return self._partition_disjoint_rows(
                rows_l, rows_r, registry, M.Tail(cur_l)(), rows_r,
                holding, failing,
            )
        rr = M.Head(cur_r)()
        tr = M.Head(rr)()
        remr = M.Head(M.Tail(rr)())()
        pt = ChainConcat(tl, tr)()
        holds = self._residues_agree(reml, remr, registry)
        if holds is M.truth_value:
            return self._partition_disjoint_rows(
                rows_l, rows_r, registry, cur_l, M.Tail(cur_r)(),
                M.Pair(pt, holding), failing,
            )
        return self._partition_disjoint_rows(
            rows_l, rows_r, registry, cur_l, M.Tail(cur_r)(),
            holding, M.Pair(pt, failing),
        )

    def _partition_tuples(
        self, tuples, all_vars, lhs_vars, rhs_vars, rows_l, rows_r,
        registry, holding, failing,
    ):
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return ChainReverse(holding)(), ChainReverse(failing)(), registry
        pt = M.Head(tuples)()
        env = ZipEnvironment(all_vars, pt)()
        sub_l = ProjectEnvToSubtuple(env, lhs_vars)()
        sub_r = ProjectEnvToSubtuple(env, rhs_vars)()
        reml = LookupResidueRow(rows_l, sub_l, registry)()
        remr = LookupResidueRow(rows_r, sub_r, registry)()
        holds = self._residues_agree(reml, remr, registry)
        if holds is M.truth_value:
            return self._partition_tuples(
                M.Tail(tuples)(), all_vars, lhs_vars, rhs_vars,
                rows_l, rows_r, registry, M.Pair(pt, holding), failing,
            )
        return self._partition_tuples(
            M.Tail(tuples)(), all_vars, lhs_vars, rhs_vars,
            rows_l, rows_r, registry, holding, M.Pair(pt, failing),
        )

    def _any_coord_proper(self, coord_projs):
        if M.IdentityCompare(coord_projs, M.EmptyList)() is M.truth_value:
            return M.false_value
        rec = M.Head(coord_projs)()
        is_proper = M.Head(M.Tail(M.Tail(M.Tail(rec)())())())()
        if is_proper is M.truth_value:
            return M.truth_value
        return self._any_coord_proper(M.Tail(coord_projs)())

    def __call__(self):
        return self.result


# ============================================================
# Surface Goal Tokenization & AST Construction (Pair-chain native)
# ============================================================


class IsProofOrMathGoal(M.Edge):
    """
    True when a surface line is a proof request or carries mathematical
    relational/algebraic structure. The request prefixes and the algebraic
    symbols are machine data (chains of Char atoms) built by this edge;
    reading the line itself is the host input boundary.
    """

    def __init__(self, text_char):
        self.result = self._is_goal(text_char)
        super().__init__(
            inputs=M.Pair(text_char, M.EmptyList),
            results=self.result,
        )

    def _request_prefixes(self):
        return M.Pair(
            M.Char("prove"),
            M.Pair(
                M.Char("show"),
                M.Pair(
                    M.Char("claim"),
                    M.Pair(
                        M.Char("conjecture"),
                        M.Pair(
                            M.Char("check"),
                            M.Pair(
                                M.Char("verify"),
                                M.Pair(
                                    M.Char("is it true"),
                                    M.Pair(
                                        M.Char("for all"),
                                        M.Pair(
                                            M.Char("for every"),
                                            M.Pair(
                                                M.Char("for any"),
                                                M.Pair(
                                                    M.Char("for each"),
                                                    M.Pair(
                                                        M.Char("if "),
                                                        M.Pair(
                                                            M.Char("whenever "),
                                                            M.Pair(
                                                                M.Char("solve "),
                                                                M.EmptyList,
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

    def _algebraic_symbols(self):
        return M.Pair(
            M.Char("="),
            M.Pair(
                M.Char("!="),
                M.Pair(
                    M.Char("<"),
                    M.Pair(
                        M.Char(">"),
                        M.Pair(
                            M.Char("^"),
                            M.Pair(
                                M.Char("+"),
                                M.Pair(M.Char("*"), M.EmptyList),
                            ),
                        ),
                    ),
                ),
            ),
        )

    def _string_chars(
        self, text, cursor=M.EmptyList, reversed_chars=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cursor = iter(text)
            initialized = M.truth_value
        char_text = next(cursor, "")
        if M.Compare(M.Char(char_text), M.Char(""))() is M.truth_value:
            return ChainReverse(reversed_chars)()
        return self._string_chars(
            text, cursor, M.Pair(M.Char(char_text), reversed_chars), initialized
        )

    def _starts_with_any(
        self, text_chars, prefixes, prefix_chars=M.EmptyList,
        remaining_chars=M.EmptyList, initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            if M.IdentityCompare(prefixes, M.EmptyList)() is M.truth_value:
                return M.false_value
            prefix_text = M.Head(prefixes)()()
            prefix_chars = self._string_chars(prefix_text)
            remaining_chars = text_chars
            initialized = M.truth_value
        if M.IdentityCompare(prefix_chars, M.EmptyList)() is M.truth_value:
            return M.truth_value
        if M.IdentityCompare(remaining_chars, M.EmptyList)() is M.truth_value:
            return self._starts_with_any(
                text_chars, M.Tail(prefixes)(), M.EmptyList,
                M.EmptyList, M.false_value,
            )
        same_char = M.Compare(
            M.Head(remaining_chars)(), M.Head(prefix_chars)()
        )()
        if M.IdentityCompare(same_char, M.truth_value)() is M.false_value:
            return self._starts_with_any(
                text_chars, M.Tail(prefixes)(), M.EmptyList,
                M.EmptyList, M.false_value,
            )
        return self._starts_with_any(
            text_chars, prefixes, M.Tail(prefix_chars)(),
            M.Tail(remaining_chars)(), initialized,
        )

    def _contains_any(
        self, text_chars, symbols, remaining_chars=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(symbols, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            remaining_chars = text_chars
            initialized = M.truth_value
        if M.IdentityCompare(remaining_chars, M.EmptyList)() is M.truth_value:
            return self._contains_any(
                text_chars, M.Tail(symbols)(), M.EmptyList, M.false_value
            )
        one_symbol = M.Pair(M.Head(symbols)(), M.EmptyList)
        if self._starts_with_any(remaining_chars, one_symbol) is M.truth_value:
            return M.truth_value
        return self._contains_any(
            text_chars, symbols, M.Tail(remaining_chars)(), initialized
        )

    def _is_goal(self, text_char):
        text = text_char()
        if M.Compare(M.Char(text), M.Char(""))() is M.truth_value:
            return M.false_value
        text_chars = self._string_chars(text)
        if (
            self._starts_with_any(text_chars, self._request_prefixes())
            is M.truth_value
        ):
            return M.truth_value
        return self._contains_any(text_chars, self._algebraic_symbols())

    def __call__(self):
        return self.result


class ParseSurfaceGoalSpec(M.Edge):
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
    The result is M.EmptyList when the line carries no equation.

    The tokenizer, the split at the equality token, the two operand-side
    walks, the recursive-descent expression parser and the parameter
    constraint scan are private methods of this edge. Reading and writing
    surface text is the host I/O boundary; every intermediate value the
    parse produces is a machine term, and the word vocabularies are machine
    chains of Char atoms.
    """

    def __init__(self, text_char, registry):
        self.registry = registry
        self.result = self._parse(text_char, registry)
        super().__init__(
            inputs=M.Pair(text_char, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    # --- token classification (host boundary string reads) -----------------

    _letter_symbols = M.Pair(M.Char("z"), M.EmptyList)
    _letter_symbols = M.Pair(M.Char("y"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("x"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("w"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("v"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("u"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("t"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("s"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("r"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("q"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("p"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("o"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("n"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("m"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("l"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("k"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("j"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("i"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("h"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("g"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("f"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("e"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("d"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("c"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("b"), _letter_symbols)
    _letter_symbols = M.Pair(M.Char("a"), _letter_symbols)
    _digit_symbols = M.Pair(M.Char("9"), M.EmptyList)
    _digit_symbols = M.Pair(M.Char("8"), _digit_symbols)
    _digit_symbols = M.Pair(M.Char("7"), _digit_symbols)
    _digit_symbols = M.Pair(M.Char("6"), _digit_symbols)
    _digit_symbols = M.Pair(M.Char("5"), _digit_symbols)
    _digit_symbols = M.Pair(M.Char("4"), _digit_symbols)
    _digit_symbols = M.Pair(M.Char("3"), _digit_symbols)
    _digit_symbols = M.Pair(M.Char("2"), _digit_symbols)
    _digit_symbols = M.Pair(M.Char("1"), _digit_symbols)
    _digit_symbols = M.Pair(M.Char("0"), _digit_symbols)
    _space_symbols = M.Pair(
        M.Char(" "), M.Pair(M.Char("\t"), M.Pair(M.Char("\n"), M.Pair(M.Char("\r"), M.EmptyList)))
    )

    def _string_chars(
        self, text, cursor=M.EmptyList, reversed_chars=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cursor = iter(text)
            initialized = M.truth_value
        char_text = next(cursor, "")
        if M.Compare(M.Char(char_text), M.Char(""))() is M.truth_value:
            return ChainReverse(reversed_chars)()
        return self._string_chars(
            text, cursor, M.Pair(M.Char(char_text), reversed_chars), initialized
        )

    def _is_digits(
        self, text, char_chain=M.EmptyList, initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            char_chain = self._string_chars(text)
            if M.IdentityCompare(char_chain, M.EmptyList)() is M.truth_value:
                return M.false_value
            initialized = M.truth_value
        if M.IdentityCompare(char_chain, M.EmptyList)() is M.truth_value:
            return M.truth_value
        is_digit = ChainHasTerm(self._digit_symbols, M.Head(char_chain)())()
        remaining_digits = self._is_digits(
            text, M.Tail(char_chain)(), initialized
        )
        return M.AndAtom(is_digit, remaining_digits)()

    def _is_ident(self, text, char_chain=M.EmptyList, initialized=M.false_value):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            char_chain = self._string_chars(text)
            initialized = M.truth_value
        if M.IdentityCompare(char_chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        is_letter = ChainHasTerm(self._letter_symbols, M.Head(char_chain)())()
        rest_is_ident = self._is_ident(
            text, M.Tail(char_chain)(), initialized
        )
        return M.OrAtom(is_letter, rest_is_ident)()

    def _is_op(self, s):
        symbol = M.Char(s)
        is_add = M.Compare(symbol, M.Char("+"))()
        is_multiply = M.Compare(symbol, M.Char("*"))()
        is_power = M.Compare(symbol, M.Char("^"))()
        return M.OrAtom(
            is_add, M.OrAtom(is_multiply, is_power)()
        )()

    # --- tokenizer ----------------------------------------------------------

    def _flush_current(self, rev_tokens, cur_tok, cur_kind, next_is_alpha):
        if M.Compare(M.Char(cur_tok), M.Char(""))() is M.truth_value:
            return rev_tokens, cur_tok, cur_kind
        rev_tokens = M.Pair(M.Char(cur_tok), rev_tokens)
        implicit_product = M.AndAtom(
            M.IdentityCompare(cur_kind, M.Zero)(),
            M.IdentityCompare(next_is_alpha, M.truth_value)(),
        )()
        if (
            M.IdentityCompare(implicit_product, M.truth_value)()
            is M.truth_value
        ):
            rev_tokens = M.Pair(M.Char("*"), rev_tokens)
        return rev_tokens, "", M.EmptyList

    def _tokenize(
        self, text_chars, rev_tokens=M.EmptyList, cur_tok="",
        cur_kind=M.EmptyList,
    ):
        """
        Scans `text` character by character into a machine Pair chain of
        M.Char tokens. All scanner state is threaded through the flush
        helper; no host container holds a machine term.
        """
        if M.IdentityCompare(text_chars, M.EmptyList)() is M.truth_value:
            flushed, unused_tok, unused_kind = self._flush_current(
                rev_tokens, cur_tok, cur_kind, M.false_value
            )
            return ChainReverse(flushed)()

        char_term = M.Head(text_chars)()
        ch = char_term()
        remaining_chars = M.Tail(text_chars)()
        if M.IdentityCompare(cur_kind, M.two)() is M.truth_value:
            if M.Compare(char_term, M.Char("="))() is M.truth_value:
                flushed, next_tok, next_kind = self._flush_current(
                    rev_tokens, cur_tok + "=", cur_kind, M.false_value
                )
                return self._tokenize(remaining_chars, flushed, next_tok, next_kind)
            next_is_alpha = M.false_value
            next_is_alpha = ChainHasTerm(
                self._letter_symbols, char_term
            )()
            rev_tokens, cur_tok, cur_kind = self._flush_current(
                rev_tokens, cur_tok, cur_kind, next_is_alpha
            )

        separators = M.Pair(
            M.Char(","),
            M.Pair(
                M.Char(";"),
                M.Pair(
                    M.Char(":"),
                    M.Pair(
                        M.Char("."),
                        M.Pair(
                            M.Char("?"),
                            M.Pair(M.Char("\""), M.Pair(M.Char("'"), M.EmptyList)),
                        ),
                    ),
                ),
            ),
        )
        operators = M.Pair(
            M.Char("+"),
            M.Pair(M.Char("*"), M.Pair(M.Char("^"), M.Pair(M.Char("("), M.Pair(M.Char(")"), M.EmptyList)))),
        )
        relational = M.Pair(
            M.Char(">"),
            M.Pair(M.Char("<"), M.Pair(M.Char("="), M.Pair(M.Char("!"), M.EmptyList))),
        )
        is_space = ChainHasTerm(self._space_symbols, char_term)()
        is_separator = ChainHasTerm(separators, char_term)()
        is_operator = ChainHasTerm(operators, char_term)()
        is_relational = ChainHasTerm(relational, char_term)()
        if M.OrAtom(is_space, is_separator)() is M.truth_value:
            rev_tokens, cur_tok, cur_kind = self._flush_current(
                rev_tokens, cur_tok, cur_kind, M.false_value
            )
        elif is_operator is M.truth_value:
            rev_tokens, cur_tok, cur_kind = self._flush_current(
                rev_tokens, cur_tok, cur_kind, M.false_value
            )
            rev_tokens = M.Pair(char_term, rev_tokens)
        elif is_relational is M.truth_value:
            rev_tokens, cur_tok, cur_kind = self._flush_current(
                rev_tokens, cur_tok, cur_kind, M.false_value
            )
            cur_tok = ch
            cur_kind = M.two
        elif ChainHasTerm(self._digit_symbols, char_term)() is M.truth_value:
            run_continues = M.OrAtom(
                M.IdentityCompare(cur_kind, M.Zero)(),
                M.IdentityCompare(cur_kind, M.one)(),
            )()
            if M.IdentityCompare(run_continues, M.truth_value)() is M.truth_value:
                cur_tok = cur_tok + ch
            else:
                rev_tokens, cur_tok, cur_kind = self._flush_current(
                    rev_tokens, cur_tok, cur_kind, M.false_value
                )
                cur_tok = ch
                cur_kind = M.Zero
        else:
            is_letter = ChainHasTerm(self._letter_symbols, char_term)()
            is_underscore = M.Compare(char_term, M.Char("_"))()
            is_identifier_char = M.OrAtom(is_letter, is_underscore)()
            if M.IdentityCompare(is_identifier_char, M.truth_value)() is M.truth_value:
                if M.IdentityCompare(cur_kind, M.one)() is M.truth_value:
                    cur_tok = cur_tok + ch
                else:
                    rev_tokens, cur_tok, cur_kind = self._flush_current(
                        rev_tokens, cur_tok, cur_kind, M.truth_value
                    )
                    cur_tok = ch
                    cur_kind = M.one
            elif M.IdentityCompare(cur_kind, M.one)() is M.truth_value:
                if M.Compare(char_term, M.Char("-"))() is M.truth_value:
                    cur_tok = cur_tok + ch
                else:
                    rev_tokens, cur_tok, cur_kind = self._flush_current(
                        rev_tokens, cur_tok, cur_kind, M.false_value
                    )
            else:
                rev_tokens, cur_tok, cur_kind = self._flush_current(
                    rev_tokens, cur_tok, cur_kind, M.false_value
                )
        return self._tokenize(remaining_chars, rev_tokens, cur_tok, cur_kind)

    # --- split at the equality token ----------------------------------------

    def _split_at_eq(self, tokens_chain, rev_before=M.EmptyList):
        """
        Splits tokens_chain at the first '=', '==' or '!=' token. Returns
        Pair(rev_before_chain, Pair(eq_char, Pair(after_chain, EmptyList))),
        or EmptyList if no equality operator is present.
        """
        if M.IdentityCompare(tokens_chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        tok = M.Head(tokens_chain)()
        s = tok()
        is_equal = M.Compare(M.Char(s), M.Char("="))()
        is_double_equal = M.Compare(M.Char(s), M.Char("=="))()
        is_not_equal = M.Compare(M.Char(s), M.Char("!="))()
        is_relation = M.OrAtom(
            is_equal, M.OrAtom(is_double_equal, is_not_equal)()
        )()
        if M.IdentityCompare(is_relation, M.truth_value)() is M.truth_value:
            return M.Pair(
                rev_before,
                M.Pair(tok, M.Pair(M.Tail(tokens_chain)(), M.EmptyList)),
            )
        return self._split_at_eq(
            M.Tail(tokens_chain)(), M.Pair(tok, rev_before)
        )

    # --- operand-side walks ---------------------------------------------------

    def _trim_leading_ops(self, tokens):
        if M.IdentityCompare(tokens, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if self._is_op(M.Head(tokens)()()) is M.truth_value:
            return self._trim_leading_ops(M.Tail(tokens)())
        return tokens

    def _extract_lhs(
        self, rev_before_chain, registry, cur=M.EmptyList, acc=M.EmptyList,
        depth=M.Zero, expect_operand=M.truth_value, current_reg=M.EmptyList,
        initialized=M.false_value,
    ):
        """
        Walks rev_before_chain (right-to-left from '=') alternating operand
        and binary operator ('+', '*', '^') with Peano parenthesis depth,
        building the forward lhs token chain directly via Pair prepending.
        """
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur = rev_before_chain
            current_reg = registry
            initialized = M.truth_value
        reg = current_reg
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return self._trim_leading_ops(acc), reg
        tok = M.Head(cur)()
        s = tok()
        if M.Compare(tok, M.Char(")"))() is M.truth_value:
            if expect_operand is M.truth_value:
                succ_res = M.Succ(depth, reg)()
                depth = M.Head(succ_res)()
                reg = M.Head(M.Tail(succ_res)())()
                acc = M.Pair(tok, acc)
                expect_operand = M.truth_value
            else:
                return self._trim_leading_ops(acc), reg
        elif M.Compare(tok, M.Char("("))() is M.truth_value:
            open_rejects = M.OrAtom(
                expect_operand, M.NatEq(depth, M.Zero, reg)()
            )()
            if open_rejects is M.truth_value:
                return self._trim_leading_ops(acc), reg
            pred_res = M.NatPred(depth, reg)()
            depth = M.Head(pred_res)()
            reg = M.Head(M.Tail(pred_res)())()
            acc = M.Pair(tok, acc)
            expect_operand = M.false_value
        elif self._is_op(s) is M.truth_value:
            if expect_operand is M.truth_value:
                return self._trim_leading_ops(acc), reg
            acc = M.Pair(tok, acc)
            expect_operand = M.truth_value
        elif M.OrAtom(self._is_digits(s), self._is_ident(s))() is M.truth_value:
            if expect_operand is M.false_value:
                return self._trim_leading_ops(acc), reg
            acc = M.Pair(tok, acc)
            expect_operand = M.false_value
        else:
            return self._trim_leading_ops(acc), reg
        return self._extract_lhs(
            rev_before_chain, reg, M.Tail(cur)(), acc, depth,
            expect_operand, reg, initialized,
        )

    def _extract_rhs(
        self, after_chain, registry, cur=M.EmptyList, rev_acc=M.EmptyList,
        depth=M.Zero, expect_operand=M.truth_value, current_reg=M.EmptyList,
        initialized=M.false_value,
    ):
        """
        Walks after_chain (left-to-right from '=') alternating operand and
        binary operator ('+', '*', '^') with Peano parenthesis depth.
        """
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur = after_chain
            current_reg = registry
            initialized = M.truth_value
        reg = current_reg
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return ChainReverse(self._trim_leading_ops(rev_acc))(), reg
        tok = M.Head(cur)()
        s = tok()
        if M.Compare(tok, M.Char("("))() is M.truth_value:
            if expect_operand is M.false_value:
                return ChainReverse(self._trim_leading_ops(rev_acc))(), reg
            succ_res = M.Succ(depth, reg)()
            depth = M.Head(succ_res)()
            reg = M.Head(M.Tail(succ_res)())()
            rev_acc = M.Pair(tok, rev_acc)
            expect_operand = M.truth_value
        elif M.Compare(tok, M.Char(")"))() is M.truth_value:
            close_rejects = M.OrAtom(
                expect_operand, M.NatEq(depth, M.Zero, reg)()
            )()
            if close_rejects is M.truth_value:
                return ChainReverse(self._trim_leading_ops(rev_acc))(), reg
            pred_res = M.NatPred(depth, reg)()
            depth = M.Head(pred_res)()
            reg = M.Head(M.Tail(pred_res)())()
            rev_acc = M.Pair(tok, rev_acc)
            expect_operand = M.false_value
        elif self._is_op(s) is M.truth_value:
            if expect_operand is M.truth_value:
                return ChainReverse(self._trim_leading_ops(rev_acc))(), reg
            rev_acc = M.Pair(tok, rev_acc)
            expect_operand = M.truth_value
        elif M.OrAtom(self._is_digits(s), self._is_ident(s))() is M.truth_value:
            if expect_operand is M.false_value:
                return ChainReverse(self._trim_leading_ops(rev_acc))(), reg
            rev_acc = M.Pair(tok, rev_acc)
            expect_operand = M.false_value
        else:
            return ChainReverse(self._trim_leading_ops(rev_acc))(), reg
        return self._extract_rhs(
            after_chain, reg, M.Tail(cur)(), rev_acc, depth,
            expect_operand, reg, initialized,
        )

    # --- variable interning -----------------------------------------------------

    def _intern_char(
        self, intern_chain, name_str, cur=M.EmptyList, cand=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur = intern_chain
            cand = M.Char(name_str)
            initialized = M.truth_value
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return cand, M.Pair(cand, intern_chain)
        existing = M.Head(cur)()
        if M.Compare(existing, cand)() is M.truth_value:
            return existing, intern_chain
        return self._intern_char(
            intern_chain, name_str, M.Tail(cur)(), cand, initialized
        )

    # --- recursive-descent expression parser -------------------------------------

    def _parse_primary(self, cur_toks, ic, reg):
        if M.IdentityCompare(cur_toks, M.EmptyList)() is M.truth_value:
            return M.EmptyList, cur_toks, ic, reg
        tok = M.Head(cur_toks)()
        s = tok()
        rem = M.Tail(cur_toks)()
        if M.Compare(M.Char(s), M.Char("("))() is M.truth_value:
            inner, rem2, ic1, r1 = self._parse_add(rem, ic, reg)
            if M.IdentityCompare(inner, M.EmptyList)() is M.truth_value:
                return M.EmptyList, rem2, ic1, r1
            has_close = ChainStartsWith(rem2, M.Char(")"))()
            if (
                M.IdentityCompare(has_close, M.false_value)()
                is M.truth_value
            ):
                return M.EmptyList, rem2, ic1, r1
            return inner, M.Tail(rem2)(), ic1, r1
        if self._is_digits(s) is M.truth_value:
            nat_res = M.NatFromRep(M.GMPRep(s), reg)()
            return (
                M.Head(nat_res)(),
                rem,
                ic,
                M.Head(M.Tail(nat_res)())(),
            )
        if self._is_ident(s) is M.truth_value:
            atom, ic1 = self._intern_char(ic, s)
            return atom, rem, ic1, reg
        return M.EmptyList, cur_toks, ic, reg

    def _parse_pow(self, cur_toks, ic, reg):
        base, rem, ic1, r1 = self._parse_primary(cur_toks, ic, reg)
        if M.IdentityCompare(base, M.EmptyList)() is M.truth_value:
            return M.EmptyList, rem, ic1, r1
        at_pow = ChainStartsWith(rem, M.Char("^"))()
        if (
            M.IdentityCompare(at_pow, M.truth_value)()
            is M.truth_value
        ):
            exp, rem2, ic2, r2 = self._parse_primary(
                M.Tail(rem)(), ic1, r1
            )
            if M.IdentityCompare(exp, M.EmptyList)() is M.truth_value:
                return M.EmptyList, rem2, ic2, r2
            node = M.Pair(
                L.ExprPowLabel, M.Pair(base, M.Pair(exp, M.EmptyList))
            )
            return node, rem2, ic2, r2
        return base, rem, ic1, r1

    def _parse_mul(
        self, cur_toks, ic, reg, left=M.EmptyList, rem=M.EmptyList,
        next_ic=M.EmptyList, next_reg=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            left, rem, next_ic, next_reg = self._parse_pow(cur_toks, ic, reg)
            initialized = M.truth_value
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return M.EmptyList, rem, next_ic, next_reg
        at_mul = ChainStartsWith(rem, M.Char("*"))()
        if M.IdentityCompare(at_mul, M.false_value)() is M.truth_value:
            return left, rem, next_ic, next_reg
        right, rem2, ic2, r2 = self._parse_pow(
            M.Tail(rem)(), next_ic, next_reg
        )
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            return M.EmptyList, rem2, ic2, r2
        next_left = M.Pair(
            L.ExprMulLabel, M.Pair(left, M.Pair(right, M.EmptyList))
        )
        return self._parse_mul(
            cur_toks, next_ic, next_reg, next_left, rem2, ic2, r2,
            initialized,
        )

    def _parse_add(
        self, cur_toks, ic, reg, left=M.EmptyList, rem=M.EmptyList,
        next_ic=M.EmptyList, next_reg=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            left, rem, next_ic, next_reg = self._parse_mul(cur_toks, ic, reg)
            initialized = M.truth_value
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return M.EmptyList, rem, next_ic, next_reg
        at_add = ChainStartsWith(rem, M.Char("+"))()
        if M.IdentityCompare(at_add, M.false_value)() is M.truth_value:
            return left, rem, next_ic, next_reg
        right, rem2, ic2, r2 = self._parse_mul(
            M.Tail(rem)(), next_ic, next_reg
        )
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            return M.EmptyList, rem2, ic2, r2
        next_left = M.Pair(
            L.ExprAddLabel, M.Pair(left, M.Pair(right, M.EmptyList))
        )
        return self._parse_add(
            cur_toks, next_ic, next_reg, next_left, rem2, ic2, r2,
            initialized,
        )

    def _parse_expr(self, tokens_chain, intern_chain, registry):
        ast, leftover, next_ic, next_reg = self._parse_add(
            tokens_chain, intern_chain, registry
        )
        if M.IdentityCompare(leftover, M.EmptyList)() is M.false_value:
            return M.EmptyList, next_ic, next_reg
        return ast, next_ic, next_reg

    # --- parameter constraints -----------------------------------------------------

    def _extract_param_constraints(
        self, tokens_before_chain, intern_chain, registry,
        cur=M.EmptyList, constraints=M.EmptyList, current_ic=M.EmptyList,
        current_reg=M.EmptyList, initialized=M.false_value,
    ):
        """
        Scans tokens_before_chain for parameter inequalities (e.g. n > 2,
        n >= 3) and returns machine constraint terms
        Pair(ExprLtLabel, Pair(bound_nat, Pair(var, EmptyList))).
        """
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur = tokens_before_chain
            current_ic = intern_chain
            current_reg = registry
            initialized = M.truth_value
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return constraints, current_ic, current_reg
        after_first = M.Tail(cur)()
        if M.IdentityCompare(after_first, M.EmptyList)() is M.truth_value:
            return constraints, current_ic, current_reg
        after_second = M.Tail(after_first)()
        if M.IdentityCompare(after_second, M.EmptyList)() is M.truth_value:
            return constraints, current_ic, current_reg
        t1 = M.Head(cur)()()
        t2 = M.Head(after_first)()()
        t3 = M.Head(after_second)()()
        inequality_shape = M.AndAtom(
            self._is_ident(t1), self._is_digits(t3)
        )()
        if inequality_shape is M.truth_value:
            var_atom, current_ic = self._intern_char(current_ic, t1)
            nat_res = M.NatFromRep(M.GMPRep(t3), current_reg)()
            num_nat = M.Head(nat_res)()
            current_reg = M.Head(M.Tail(nat_res)())()
            if M.Compare(M.Char(t2), M.Char(">"))() is M.truth_value:
                c_term = M.Pair(
                    L.ExprLtLabel,
                    M.Pair(num_nat, M.Pair(var_atom, M.EmptyList)),
                )
                constraints = ChainAppendEnd(constraints, c_term)()
            elif M.Compare(M.Char(t2), M.Char(">="))() is M.truth_value:
                if M.NatEq(num_nat, M.Zero, current_reg)() is M.false_value:
                    pred_res = M.NatPred(num_nat, current_reg)()
                    pred_nat = M.Head(pred_res)()
                    current_reg = M.Head(M.Tail(pred_res)())()
                    c_term = M.Pair(
                        L.ExprLtLabel,
                        M.Pair(pred_nat, M.Pair(var_atom, M.EmptyList)),
                    )
                    constraints = ChainAppendEnd(constraints, c_term)()
        return self._extract_param_constraints(
            tokens_before_chain, intern_chain, current_reg,
            M.Tail(cur)(), constraints, current_ic, current_reg, initialized,
        )

    # --- word vocabularies -----------------------------------------------------------

    def _no_solution_words(self):
        return M.Pair(
            M.Char("no"),
            M.Pair(
                M.Char("impossible"),
                M.Pair(
                    M.Char("cannot"),
                    M.Pair(M.Char("never"), M.EmptyList),
                ),
            ),
        )

    def _positive_words(self):
        return M.Pair(
            M.Char("positive"),
            M.Pair(
                M.Char("nonzero"),
                M.Pair(M.Char("non-zero"), M.EmptyList),
            ),
        )

    def _token_chain_has_any_word(
        self, tokens_chain, words_chain, cur=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur = tokens_chain
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.false_value
        s = M.Head(cur)()()
        if ChainHasTerm(words_chain, M.Char(s))() is M.truth_value:
            return M.truth_value
        return self._token_chain_has_any_word(
            tokens_chain, words_chain, M.Tail(cur)(), M.truth_value
        )

    def _base_vars_of(
        self, all_vars, exp_vars, cur=M.EmptyList,
        base_vars=M.EmptyList, initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur = all_vars
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return base_vars
        v_atom = M.Head(cur)()
        if ChainHasTerm(exp_vars, v_atom)() is M.false_value:
            base_vars = ChainAppendEnd(base_vars, v_atom)()
        return self._base_vars_of(
            all_vars, exp_vars, M.Tail(cur)(), base_vars, M.truth_value
        )

    # --- the parse ----------------------------------------------------------------------

    def _parse(self, text_char, registry):
        text = text_char()
        if M.Compare(M.Char(text), M.Char(""))() is M.truth_value:
            return M.EmptyList
        text_chars = self._string_chars(text)
        tokens_chain = self._tokenize(text_chars)
        split_res = self._split_at_eq(tokens_chain)
        if M.IdentityCompare(split_res, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        rev_before = M.Head(split_res)()
        eq_tok = M.Head(M.Tail(split_res)())()
        after_chain = M.Head(M.Tail(M.Tail(split_res)())())()
        before_chain = ChainReverse(rev_before)()

        lhs_toks, reg1 = self._extract_lhs(rev_before, registry)
        rhs_toks, reg2 = self._extract_rhs(after_chain, reg1)
        if (
            M.OrAtom(
                M.IdentityCompare(lhs_toks, M.EmptyList)(),
                M.IdentityCompare(rhs_toks, M.EmptyList)(),
            )()
            is M.truth_value
        ):
            return M.EmptyList

        intern_chain = M.EmptyList
        lhs_ast, intern_chain, reg3 = self._parse_expr(
            lhs_toks, intern_chain, reg2
        )
        if M.IdentityCompare(lhs_ast, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rhs_ast, intern_chain, reg4 = self._parse_expr(
            rhs_toks, intern_chain, reg3
        )
        if M.IdentityCompare(rhs_ast, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        param_constraints, intern_chain, reg5 = (
            self._extract_param_constraints(
                before_chain, intern_chain, reg4
            )
        )

        eq_node = M.Pair(
            L.ExprEqLabel, M.Pair(lhs_ast, M.Pair(rhs_ast, M.EmptyList))
        )
        all_vars = M.Head(ExtractExprVariables(eq_node, reg5)())()
        exp_vars = M.Head(ExtractExponentVariables(eq_node, reg5)())()
        base_vars = self._base_vars_of(all_vars, exp_vars)

        no_sol_words = self._token_chain_has_any_word(
            tokens_chain, self._no_solution_words()
        )
        no_solutions_flag = M.OrAtom(
            M.Compare(eq_tok, M.Char("!="))(),
            no_sol_words,
        )()
        positive_only_flag = self._token_chain_has_any_word(
            tokens_chain, self._positive_words()
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

    def __call__(self):
        return self.result


class GoalSpecLhs(M.Edge):
    """The left-hand side AST of a parsed surface goal spec record."""

    def __init__(self, spec_rec):
        self.result = M.Head(spec_rec)()
        super().__init__(
            inputs=M.Pair(spec_rec, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalSpecRhs(M.Edge):
    """The right-hand side AST of a parsed surface goal spec record."""

    def __init__(self, spec_rec):
        self.result = M.Head(M.Tail(spec_rec)())()
        super().__init__(
            inputs=M.Pair(spec_rec, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalSpecBaseVars(M.Edge):
    """The base-variable chain of a parsed surface goal spec record."""

    def __init__(self, spec_rec):
        self.result = M.Head(M.Tail(M.Tail(spec_rec)())())()
        super().__init__(
            inputs=M.Pair(spec_rec, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalSpecExpVars(M.Edge):
    """The exponent-variable chain of a parsed surface goal spec record."""

    def __init__(self, spec_rec):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(spec_rec)())())()
        )()
        super().__init__(
            inputs=M.Pair(spec_rec, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalSpecParamConstraints(M.Edge):
    """The parameter-constraint chain of a parsed surface goal spec record."""

    def __init__(self, spec_rec):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(spec_rec)())())())()
        )()
        super().__init__(
            inputs=M.Pair(spec_rec, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalSpecNoSolutions(M.Edge):
    """The no-solutions flag of a parsed surface goal spec record."""

    def __init__(self, spec_rec):
        self.result = M.Head(
            M.Tail(
                M.Tail(
                    M.Tail(M.Tail(M.Tail(spec_rec)())())()
                )()
            )()
        )()
        super().__init__(
            inputs=M.Pair(spec_rec, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalSpecPositiveOnly(M.Edge):
    """The positive-only flag of a parsed surface goal spec record."""

    def __init__(self, spec_rec):
        self.result = M.Head(
            M.Tail(
                M.Tail(
                    M.Tail(
                        M.Tail(M.Tail(M.Tail(spec_rec)())())()
                    )()
                )()
            )()
        )()
        super().__init__(
            inputs=M.Pair(spec_rec, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalSpecRegistry(M.Edge):
    """The registry threaded through a parsed surface goal spec record."""

    def __init__(self, spec_rec):
        self.result = M.Head(
            M.Tail(
                M.Tail(
                    M.Tail(
                        M.Tail(
                            M.Tail(M.Tail(M.Tail(spec_rec)())())()
                        )()
                    )()
                )()
            )()
        )()
        super().__init__(
            inputs=M.Pair(spec_rec, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormatSetChain(M.Edge):
    """
    Renders a Nat set chain as sorted brace text, e.g. "{1, 2, 3}".
    Rendering is the playground's host output boundary.
    """

    def __init__(self, set_chain, registry):
        self.registry = registry
        self.result = self._format(set_chain, registry)
        super().__init__(
            inputs=M.Pair(set_chain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _format(
        self, set_chain, registry, cur=M.EmptyList, out="",
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur = SortNatChain(set_chain, registry)()
            initialized = M.truth_value
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return "{" + out + "}"
        rep = M.NatRepOf(M.Head(cur)(), registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            part = M.GMPRepText(rep)()
            if M.Compare(M.Char(out), M.Char(""))() is M.truth_value:
                out = part
            else:
                out = out + ", " + part
        return self._format(
            set_chain, registry, M.Tail(cur)(), out, initialized
        )

    def __call__(self):
        return self.result


class FormatVarsChain(M.Edge):
    """
    Renders a variable chain as comma-separated surface text, e.g. "x, y, z".
    Rendering is the playground's host output boundary.
    """

    def __init__(self, vars_chain):
        self.result = self._format(vars_chain)
        super().__init__(
            inputs=M.Pair(vars_chain, M.EmptyList),
            results=self.result,
        )

    def _format(
        self, vars_chain, cur=M.EmptyList, out="",
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur = vars_chain
            initialized = M.truth_value
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return out
        part = M.Head(cur)()()
        if M.Compare(M.Char(out), M.Char(""))() is M.truth_value:
            out = part
        else:
            out = out + ", " + part
        return self._format(vars_chain, M.Tail(cur)(), out, initialized)

    def __call__(self):
        return self.result


class FormatDiscoveredOperationNames(M.Edge):
    """Renders the names carried by a discovered operation register."""

    def __init__(self, operations):
        self.result = self._format(operations)
        super().__init__(inputs=M.Pair(operations, M.EmptyList), results=self.result)

    def _format(self, operations):
        if M.IdentityCompare(operations, M.EmptyList)() is M.truth_value:
            return ""
        name = M.Head(M.Head(operations)())()() + "()"
        rest = M.Tail(operations)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return name
        return name + ", " + self._format(rest)

    def __call__(self):
        return self.result


class FormatEnvChain(M.Edge):
    """
    Renders an environment (a chain of Pair(variable, Pair(nat, EmptyList)))
    as comma-separated "v = n" text. Rendering is the playground's host
    output boundary.
    """

    def __init__(self, env_chain, registry):
        self.registry = registry
        self.result = self._format(env_chain, registry)
        super().__init__(
            inputs=M.Pair(env_chain, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _format(
        self, env_chain, registry, cur=M.EmptyList, out="",
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cur = env_chain
            initialized = M.truth_value
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return out
        entry = M.Head(cur)()
        v_name = M.Head(entry)()()
        v_nat = M.Head(M.Tail(entry)())()
        v_str = M.GMPRepText(M.NatRepOf(v_nat, registry)())()
        part = v_name + " = " + v_str
        if M.Compare(M.Char(out), M.Char(""))() is M.truth_value:
            out = part
        else:
            out = out + ", " + part
        return self._format(
            env_chain, registry, M.Tail(cur)(), out, initialized
        )

    def __call__(self):
        return self.result


class FormatDiscoveriesReport(M.Edge):
    """
    Renders the DiscoverExprObstructions discoveries for one equation
    instance into the playground's surface report. Rendering is the host
    output boundary; every value rendered is read out of machine records.
    """

    def __init__(
        self,
        lhs,
        rhs,
        discoveries,
        moduli_chain,
        bound_nat,
        witness_env,
        positive_only,
        registry,
        indent="  ",
        domain_chain=M.EmptyList,
    ):
        self.registry = registry
        self.result = self._report(
            lhs,
            rhs,
            discoveries,
            moduli_chain,
            bound_nat,
            witness_env,
            positive_only,
            registry,
            indent,
            domain_chain,
        )
        super().__init__(
            inputs=M.Pair(
                lhs,
                M.Pair(
                    rhs,
                    M.Pair(
                        discoveries,
                        M.Pair(
                            moduli_chain,
                            M.Pair(
                                bound_nat,
                                M.Pair(
                                    witness_env,
                                    M.Pair(
                                        positive_only,
                                        M.Pair(registry, M.EmptyList),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _report(
        self,
        lhs,
        rhs,
        discoveries,
        moduli_chain,
        bound_nat,
        witness_env,
        positive_only,
        reg,
        indent,
        domain_chain,
    ):
        lhs_str = RenderNatExpr(lhs, reg)()
        rhs_str = RenderNatExpr(rhs, reg)()
        mods_str = FormatSetChain(moduli_chain, reg)()
        if M.IdentityCompare(domain_chain, M.EmptyList)() is M.false_value:
            domain_text = FormatSetChain(domain_chain, reg)()
            if M.IdentityCompare(witness_env, M.EmptyList)() is M.false_value:
                w_str = FormatEnvChain(witness_env, reg)()
                report_text = f"{indent}- Ground Tensor Witness (domain {domain_text}): Counterexample solution found at ({w_str}) where {lhs_str} = {rhs_str}."
            else:
                report_text = f"{indent}- Ground Tensor Witness Search (domain {domain_text}): 0 solutions in ground tensor; sweeping moduli {mods_str}."
        else:
            pred_res = M.NatPred(bound_nat, reg)()
            max_elem_val = M.NatRepOf(M.Head(pred_res)(), reg)()()
            reg = M.Head(M.Tail(pred_res)())()
            min_elem_val = 0
            if positive_only is M.truth_value:
                min_elem_val = 1
            if M.IdentityCompare(witness_env, M.EmptyList)() is M.false_value:
                w_str = FormatEnvChain(witness_env, reg)()
                report_text = f"{indent}- Ground Tensor Witness ({min_elem_val}..{max_elem_val}): Counterexample solution found at ({w_str}) where {lhs_str} = {rhs_str}."
            else:
                report_text = f"{indent}- Ground Tensor Witness Search (domain {min_elem_val}..{max_elem_val}): 0 solutions in ground tensor; sweeping moduli {mods_str}."
        if M.IdentityCompare(discoveries, M.EmptyList)() is M.truth_value:
            return report_text + f"\n{indent}- across moduli {mods_str}: no proper residue restriction found."
        return self._report_discoveries(
            discoveries, discoveries, report_text, lhs_str, rhs_str,
            indent, reg,
        )

    def _report_discoveries(
        self, cursor, discoveries, report_text, lhs_str, rhs_str, indent, reg
    ):
        if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
            return report_text
        rec = M.Head(cursor)()
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
        lhs_img_str = FormatSetChain(lhs_img, reg)()
        rhs_img_str = FormatSetChain(rhs_img, reg)()
        dom_res = BuildNatRange(M.Zero, m_nat, reg)()
        full_dom = M.Head(dom_res)()
        reg = M.Head(M.Tail(dom_res)())()
        lhs_excl = SortNatChain(SetDifference(full_dom, lhs_img, reg)(), reg)()
        rhs_excl = SortNatChain(SetDifference(full_dom, rhs_img, reg)(), reg)()
        lhs_excl_str = FormatSetChain(lhs_excl, reg)()
        rhs_excl_str = FormatSetChain(rhs_excl, reg)()
        report_text = (
            report_text
            + f"\n{indent}- Modulus m = {m_val}:"
            + f"\n{indent}  * image of ({lhs_str}) mod {m_val} = {lhs_img_str} (excluded: {lhs_excl_str})"
            + f"\n{indent}  * image of ({rhs_str}) mod {m_val} = {rhs_img_str} (excluded: {rhs_excl_str})"
            + f"\n{indent}  * ({lhs_str}) = ({rhs_str}) mod {m_val}: |holding| = {h_val}, |failing| = {fl_val}"
        )
        if is_disj is M.truth_value:
            report_text = report_text + (
                f"\n{indent}  * Disjoint Image Regularity: {rhs_img_str} /\\ {lhs_img_str} = empty (|holding| = 0)"
            )
        report_text = self._append_coordinate_reports(
            coord_projs, report_text, indent, m_val, reg
        )
        return self._report_discoveries(
            M.Tail(cursor)(), discoveries, report_text, lhs_str, rhs_str,
            indent, reg,
        )

    def _append_coordinate_reports(self, cursor, report_text, indent, m_val, reg):
        if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
            return report_text
        record = M.Head(cursor)()
        variable = M.Head(record)()
        admitted = M.Head(M.Tail(record)())()
        excluded = M.Head(M.Tail(M.Tail(record)())())()
        is_proper = M.Head(M.Tail(M.Tail(M.Tail(record)())())())()
        if is_proper is M.truth_value:
            admitted_text = FormatSetChain(admitted, reg)()
            excluded_text = FormatSetChain(excluded, reg)()
            report_text = (
                report_text
                + f"\n{indent}  * Coordinate Projection: proj({variable()}, holding) = {admitted_text} (excluded mod {m_val}: {excluded_text})"
            )
        return self._append_coordinate_reports(
            M.Tail(cursor)(), report_text, indent, m_val, reg
        )

    def __call__(self):
        return self.result


class ParameterInstanceSweep(M.Edge):
    """Evaluates one parameter instance across ground tensors and moduli."""

    def __init__(
        self, goal_char, exp_char, registry,
        domain_start=M.Zero, domain_count=M.six,
    ):
        self.goal_char = goal_char
        self.exp_char = exp_char
        self.registry = registry
        self.domain_start = domain_start
        self.domain_count = domain_count
        self.result = M.EmptyList
        super().__init__(
            inputs=M.Pair(
                goal_char,
                M.Pair(
                    exp_char,
                    M.Pair(
                        registry,
                        M.Pair(domain_start, M.Pair(domain_count, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        exp_str = self.exp_char()
        reg = self.registry
        spec_rec = ParseSurfaceGoalSpec(self.goal_char, reg)()
        lhs = GoalSpecLhs(spec_rec)()
        rhs = GoalSpecRhs(spec_rec)()
        exp_vars = GoalSpecExpVars(spec_rec)()
        positive_only = GoalSpecPositiveOnly(spec_rec)()
        reg = GoalSpecRegistry(spec_rec)()

        exp_var = M.Head(exp_vars)()
        exp_name = exp_var()
        e_res = M.NatFromRep(M.GMPRep(exp_str), reg)()
        e_nat = M.Head(e_res)()
        reg = M.Head(M.Tail(e_res)())()

        lhs_e = M.Head(SubstituteExprVar(lhs, exp_var, e_nat, reg)())()
        rhs_e = M.Head(SubstituteExprVar(rhs, exp_var, e_nat, reg)())()
        lhs_e_str = RenderNatExpr(lhs_e, reg)()
        rhs_e_str = RenderNatExpr(rhs_e, reg)()

        bound_nat = self.domain_count
        dom_res = BuildNatRange(self.domain_start, bound_nat, reg)()
        domain = M.Head(dom_res)()
        reg = M.Head(M.Tail(dom_res)())()

        mods_res = BuildNatRange(M.two, M.four, reg)()
        moduli_chain = M.Head(mods_res)()
        reg = M.Head(M.Tail(mods_res)())()

        lhs_vars = M.Head(ExtractExprVariables(lhs_e, reg)())()
        rhs_vars = M.Head(ExtractExprVariables(rhs_e, reg)())()

        PlaygroundDebugEmit(M.Char(
            f"instance sweep started for {exp_name} = {exp_str} ({lhs_e_str} = {rhs_e_str}): evaluating ground EvaluationTensors over {FormatSetChain(domain, reg)()} and sweeping moduli {FormatSetChain(moduli_chain, reg)()}..."
        ))()

        lt_res = BuildExprGroundTensor(
            lhs_e, lhs_vars, domain, M.Char("lhs"), reg
        )()
        lhs_tensor = M.Head(lt_res)()
        reg = M.Head(M.Tail(lt_res)())()

        rt_res = BuildExprGroundTensor(
            rhs_e, rhs_vars, domain, M.Char("rhs"), reg
        )()
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
            domain_chain=domain,
        )()
        disc_chain = M.Head(disc_res)()
        reg = M.Head(M.Tail(disc_res)())()

        header = f"  [Instance {exp_name} = {exp_str}: {lhs_e_str} = {rhs_e_str}]"
        body = FormatDiscoveriesReport(
            lhs_e,
            rhs_e,
            disc_chain,
            moduli_chain,
            bound_nat,
            witness_env,
            positive_only,
            reg,
            indent="    ",
            domain_chain=domain,
        )()
        first_mod_str = "4"
        if M.IdentityCompare(disc_chain, M.EmptyList)() is M.false_value:
            first_rec = M.Head(disc_chain)()
            first_mod_nat = M.Head(M.Tail(first_rec)())()
            first_mod_str = M.GMPRepText(M.NatRepOf(first_mod_nat, reg)())()

        PlaygroundDebugEmit(M.Char(f"instance sweep completed for {exp_name} = {exp_str}."))()
        report_record = M.Pair(
            M.Char(header + "\n" + body),
            M.Pair(M.Char(first_mod_str), M.EmptyList),
        )
        self.result = report_record
        return report_record


class FilterCandidateParameters(M.Edge):
    """
    Generates the candidate exponent domain for a parametric goal and keeps
    the candidates admitted by the parsed machine parameter constraints:
    candidates are 1-tuples over [exp_var] and FilterTuples evaluates the
    constraint chain itself, with no host callable. The first two admitted
    candidates are returned; no admitted candidate yields an empty chain.
    Result: Pair(candidates_chain, Pair(registry, EmptyList)).
    """

    def __init__(self, exp_var, param_constraints, registry):
        self.registry = registry
        self.result = self._filter(exp_var, param_constraints, registry)
        super().__init__(
            inputs=M.Pair(
                exp_var,
                M.Pair(param_constraints, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _filter(self, exp_var, param_constraints, registry):
        cand_res = BuildNatRange(M.two, M.four, registry)()
        cand_domain = M.Head(cand_res)()
        reg1 = M.Head(M.Tail(cand_res)())()

        if (
            M.IdentityCompare(param_constraints, M.EmptyList)()
            is M.truth_value
        ):
            return M.Pair(
                M.Pair(M.two, M.Pair(M.three, M.EmptyList)),
                M.Pair(reg1, M.EmptyList),
            )

        dom1 = ProductOfDomains(M.Pair(cand_domain, M.EmptyList))()
        vars_one = M.Pair(exp_var, M.EmptyList)

        filt_res = FilterTuples(dom1, vars_one, param_constraints, reg1)()
        filt_tuples = M.Head(filt_res)()
        reg2 = M.Head(M.Tail(filt_res)())()

        return self._take_candidates(
            filt_tuples, reg2, M.EmptyList, M.Zero
        )

    def _take_candidates(self, cur, registry, out, taken):
        take_more = M.AndAtom(
            M.NotAtom(M.IdentityCompare(cur, M.EmptyList)())(),
            M.NatLess(taken, M.two, registry)(),
        )()
        if M.IdentityCompare(take_more, M.false_value)() is M.truth_value:
            return M.Pair(out, M.Pair(registry, M.EmptyList))
        tup = M.Head(cur)()
        out = ChainAppendEnd(out, M.Head(tup)())()
        inc = A.Add(taken, M.one, registry)()
        taken = M.Head(inc)()
        registry = M.Head(M.Tail(inc)())()
        return self._take_candidates(
            M.Tail(cur)(), registry, out, taken
        )


class RunPlaygroundInteractive(M.Edge):
    """
    Runs the machine-native Cartesian exploration sweep over the active
    unproved goal (or discovers separating moduli over the default benchmark
    when no goal is active) and returns the formatted report. The report is
    the playground's host output boundary.
    """

    def __init__(
        self, graph, goal_text="", tutor=M.EmptyList,
        interactive=M.false_value,
    ):
        self.result = self._run(graph, goal_text, tutor, interactive)
        super().__init__(
            inputs=M.Pair(graph, M.EmptyList),
            results=self.result,
        )

    def _run_parameter_instances(
        self, cursor, active_goal, registry, report_text,
        first_modulus=M.EmptyList, graph=None,
        domain_start=M.Zero, domain_count=M.six,
    ):
        if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(first_modulus, M.EmptyList)() is M.false_value:
                graph._last_discovered_invariant = M.Pair(
                    L.DiscoveredInvariantLabel,
                    M.Pair(
                        first_modulus,
                        M.Pair(
                            M.Pair(M.Zero, M.EmptyList),
                            M.Pair(
                                M.Pair(M.Zero, M.EmptyList),
                                M.Pair(M.false_value, M.EmptyList),
                            ),
                        ),
                    ),
                )
            PlaygroundDebugEmit(M.Char("finished sequential parameter sweep."))()
            return report_text + (
                "\n  - Suggestion: Ground these discovered residue regularities as candidate lemmas."
            )
        e_nat = M.Head(cursor)()
        e_str = M.GMPRepText(M.NatRepOf(e_nat, registry)())()
        record = ParameterInstanceSweep(
            M.Char(active_goal), M.Char(e_str), registry,
            domain_start, domain_count,
        )()
        instance_text = M.Head(record)()()
        modulus_text = M.Head(M.Tail(record)())()()
        report_text = report_text + "\n" + instance_text
        if M.IdentityCompare(first_modulus, M.EmptyList)() is M.truth_value:
            modulus_result = M.NatFromRep(M.GMPRep(modulus_text), registry)()
            first_modulus = M.Head(modulus_result)()
            registry = M.Head(M.Tail(modulus_result)())()
        return self._run_parameter_instances(
            M.Tail(cursor)(), active_goal, registry, report_text,
            first_modulus, graph, domain_start, domain_count,
        )

    def _ask_domain(self, registry):
        try:
            reply = input(
                "[you] Run the Cartesian playground? Reply 'no', 'yes' (then enter bounds), 'yes, 0 to 10', or 'try on positive integers from 1 to 10': "
            )
        except EOFError:
            return M.EmptyList
        if M.Compare(M.Char(reply), M.Char("no"))() is M.truth_value:
            return M.EmptyList
        if M.Compare(
            M.Char(reply), M.Char("yes, 0 to 10")
        )() is M.truth_value:
            lower_text = "0"
            upper_text = "10"
        elif M.Compare(
            M.Char(reply), M.Char("yes, 1 to 10")
        )() is M.truth_value:
            lower_text = "1"
            upper_text = "10"
        elif M.Compare(
            M.Char(reply),
            M.Char("try on positive integers from 1 to 10"),
        )() is M.truth_value:
            lower_text = "1"
            upper_text = "10"
        elif M.Compare(M.Char(reply), M.Char("yes"))() is M.truth_value:
            try:
                lower_text = input("[you] Natural-domain lower bound: ")
                upper_text = input("[you] Natural-domain upper bound: ")
            except EOFError:
                return M.EmptyList
        else:
            print("[machine] Reply 'no', 'yes', 'yes, 0 to 10', or give a natural-number range.")
            return M.EmptyList
        try:
            lower_rep = M.GMPRep(lower_text)
            upper_rep = M.GMPRep(upper_text)
        except (ValueError, TypeError):
            print("[machine] Bounds must be natural-number numerals.")
            return M.EmptyList
        lower_res = M.NatFromRep(lower_rep, registry)()
        lower = M.Head(lower_res)()
        reg1 = M.Head(M.Tail(lower_res)())()
        upper_res = M.NatFromRep(upper_rep, reg1)()
        upper = M.Head(upper_res)()
        reg2 = M.Head(M.Tail(upper_res)())()
        if M.NatLess(upper, lower, reg2)() is M.truth_value:
            print("[machine] Bounds must be natural numbers with upper at least lower.")
            return M.EmptyList
        difference = A.NatSubtract(upper, lower, reg2)()
        span = M.Head(difference)()
        reg3 = M.Head(M.Tail(difference)())()
        count_res = A.Add(span, M.one, reg3)()
        count = M.Head(count_res)()
        reg4 = M.Head(M.Tail(count_res)())()
        domain_res = BuildNatRange(lower, count, reg4)()
        domain = M.Head(domain_res)()
        reg5 = M.Head(M.Tail(domain_res)())()
        return M.Pair(domain, M.Pair(lower, M.Pair(count, M.Pair(reg5, M.EmptyList))))

    def _offer_operation_law(self, graph, operations, domain, registry, report):
        if M.IdentityCompare(operations, M.EmptyList)() is M.truth_value:
            graph._pending_discovery = M.EmptyList
            return report + "\n[machine] No Nat-valued expression operations were available for law mining."
        from . import invariant_miner as Miner

        known_nodes = M.FromContextGetNodes(graph)()
        proposal = Miner.ProposeNextRegularityOrStructure(
            operations, domain, known_nodes, registry
        )()
        status = M.Head(proposal)()
        payload = M.Head(M.Tail(proposal)())()
        registry = M.Head(M.Tail(M.Tail(proposal)())())()
        graph._replace_context(constructors=registry)
        if M.IdentityCompare(status, L.ObservedRegularityLabel)() is M.truth_value:
            graph._pending_discovery = M.Pair(
                status, M.Pair(payload, M.EmptyList)
            )
            finding_body = M.Tail(payload)()
            operation_name = M.Head(finding_body)()
            law_body = M.Tail(finding_body)()
            law_type = M.Head(law_body)()
            verdict_body = M.Tail(law_body)()
            witness_body = M.Tail(verdict_body)()
            scope = M.Head(M.Tail(witness_body)())()
            found_domain = M.Head(M.Tail(scope)())()
            witnesses = M.Head(witness_body)()
            examples = FormatOperationLawExamples(
                law_type, witnesses, operations, registry
            )()
            NaturalPlaygroundDebugEmit(M.Char(
                "Proposing the observed regularity: ["
                + examples
                + "]; please provide a name for "
                "the property of "
                + operation_name()
                + "(); the name and tested-domain examples will be stored in talk_lessons.log."
            ))()
            return report + (
                "\n[machine] Observed on tested domain "
                + FormatSetChain(found_domain, registry)()
                + ": "
                + operation_name()
                + " satisfies "
                + RenderDiscoveredEquation(law_type, registry)()
                + ". Supporting examples: "
                + examples
                + ". Please provide a name for this property."
            )
        if M.IdentityCompare(status, L.AlgebraicTemplateLabel)() is M.truth_value:
            graph._pending_discovery = M.Pair(
                status, M.Pair(payload, M.EmptyList)
            )
            return report + "\n[machine] Discovered a structure from the recorded laws. Name this structure?"
        graph._pending_discovery = M.EmptyList
        return report + "\n[machine] No new operation law was found on this finite domain."

    def _run(
        self, graph, goal_text="", tutor=M.EmptyList,
        interactive=M.false_value,
    ):
        registry = M.FromContextGetConstructors(graph)()
        active_goal = goal_text
        active_tutor = tutor
        active_claim = M.EmptyList

        spec_rec = (
            ParseSurfaceGoalSpec(M.Char(active_goal), registry)()
            if M.Compare(M.Char(active_goal), M.Char(""))() is M.false_value
            else M.EmptyList
        )
        if M.IdentityCompare(spec_rec, M.EmptyList)() is M.false_value:
            lhs = GoalSpecLhs(spec_rec)()
            rhs = GoalSpecRhs(spec_rec)()
            base_vars = GoalSpecBaseVars(spec_rec)()
            exp_vars = GoalSpecExpVars(spec_rec)()
            param_constraints = GoalSpecParamConstraints(spec_rec)()
            no_solutions = GoalSpecNoSolutions(spec_rec)()
            positive_only = GoalSpecPositiveOnly(spec_rec)()
            reg = GoalSpecRegistry(spec_rec)()
            operation_terms = M.Pair(lhs, M.Pair(rhs, M.EmptyList))
            operation_result = BuildNatOperationRegister(reg, operation_terms)()
            operation_register = M.Head(operation_result)()
            reg = M.Head(M.Tail(operation_result)())()
            graph._last_playground_operation_register = operation_register
            graph._last_playground_goal = M.Char(active_goal)
            graph._last_playground_domain = M.EmptyList
            domain_start = M.Zero
            domain_count = M.six
            domain = M.EmptyList
            if M.IdentityCompare(interactive, M.truth_value)() is M.truth_value:
                operation_names = FormatDiscoveredOperationNames(operation_register)()
                if M.Compare(M.Char(operation_names), M.Char(""))() is M.truth_value:
                    operation_names = "no Nat-valued operations"
                print(
                    "[machine] Expression operations detected: "
                    + operation_names
                    + ", compare_equality()."
                )
                chosen_domain = self._ask_domain(reg)
                if M.IdentityCompare(chosen_domain, M.EmptyList)() is M.truth_value:
                    graph._pending_discovery = M.EmptyList
                    return "[machine] Playground run declined or no valid domain was supplied."
                domain = M.Head(chosen_domain)()
                domain_start = M.Head(M.Tail(chosen_domain)())()
                domain_count = M.Head(M.Tail(M.Tail(chosen_domain)())())()
                reg = M.Head(M.Tail(M.Tail(M.Tail(chosen_domain)())())())()
            if M.IdentityCompare(domain, M.EmptyList)() is M.truth_value:
                domain_result = BuildNatRange(domain_start, domain_count, reg)()
                domain = M.Head(domain_result)()
                reg = M.Head(M.Tail(domain_result)())()
            graph._last_playground_domain = domain

            if M.IdentityCompare(interactive, M.truth_value)() is M.truth_value:
                domain_text = FormatSetChain(domain, reg)()
                PlaygroundDebugEmit(M.Char(
                    "evaluating discovered arithmetic operations over domain "
                    + domain_text
                    + " and mining operation laws..."
                ))()
                operation_report = (
                    "[machine] Operation-law scan over tested domain "
                    + domain_text
                    + "."
                )
                return self._offer_operation_law(
                    graph, operation_register, domain, reg, operation_report
                )

            # Case A: Parametric exponent family (e.g., x^n + y^n = z^n)
            if M.IdentityCompare(exp_vars, M.EmptyList)() is M.false_value:
                exp_var = M.Head(exp_vars)()
                exp_name = exp_var()
                exp_chain_res = FilterCandidateParameters(
                    exp_var, param_constraints, reg
                )()
                exp_chain = M.Head(exp_chain_res)()
                reg = M.Head(M.Tail(exp_chain_res)())()
                mods_res = BuildNatRange(M.two, M.four, reg)()
                moduli_chain = M.Head(mods_res)()
                reg = M.Head(M.Tail(mods_res)())()

                lhs_pat_str = RenderNatExpr(lhs, reg)()
                rhs_pat_str = RenderNatExpr(rhs, reg)()
                exp_set_str = FormatSetChain(exp_chain, reg)()
                mods_set_str = FormatSetChain(moduli_chain, reg)()
                domain_set_str = FormatSetChain(domain, reg)()

                PlaygroundDebugEmit(M.Char(
                    f"constructing the natural tensor for {lhs_pat_str} = {rhs_pat_str}: parameter {exp_name} in {exp_set_str}, domain {domain_set_str}, candidate moduli {mods_set_str}; evaluating parameter instances sequentially..."
                ))()

                report = f"[machine] Cartesian Playground Sweep for {lhs_pat_str} = {rhs_pat_str} (parameter {exp_name} in {exp_set_str}, domain {domain_set_str}, moduli {mods_set_str}):"
                instance_report = self._run_parameter_instances(
                    exp_chain, active_goal, reg, report, M.EmptyList, graph,
                    domain_start, domain_count,
                )
                if M.IdentityCompare(interactive, M.truth_value)() is M.truth_value:
                    return self._offer_operation_law(
                        graph, operation_register, domain, reg, instance_report
                    )
                return instance_report

            # Case B: Concrete polynomial identity claim (no_solutions is M.false_value)
            if no_solutions is M.false_value:
                lhs_str = RenderNatExpr(lhs, reg)()
                rhs_str = RenderNatExpr(rhs, reg)()
                PlaygroundDebugEmit(M.Char(
                    f"constructing degree-bounded polynomial grid for {lhs_str} = {rhs_str} over variables [{FormatVarsChain(base_vars)()}]..."
                ))()
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
                PlaygroundDebugEmit(M.Char(
                    f"evaluated {grid_count_val} degree-bounded grid points for {lhs_str} = {rhs_str}."
                ))()

                if verdict is M.truth_value:
                    report = (
                        f"[machine] Cartesian Playground Sweep for {lhs_str} = {rhs_str}:\n"
                        f"  - PolynomialIdentityByGrid verified {lhs_str} = {rhs_str} across all {grid_count_val} degree-bounded grid points.\n"
                        f"  - Candidate Lemma: Algebraic identity {lhs_str} == {rhs_str} holds universally over Nat.\n"
                        "  - Suggestion: Ground this polynomial identity into active context as a rewrite lemma."
                    )
                    if M.IdentityCompare(interactive, M.truth_value)() is M.truth_value:
                        return self._offer_operation_law(
                            graph, operation_register, domain, reg, report
                        )
                    return report
                if verdict is M.false_value:
                    w_env = ZipEnvironment(base_vars, witness_tup)()
                    w_str = FormatEnvChain(w_env, reg)()
                    report = (
                        f"[machine] Cartesian Playground Sweep for {lhs_str} = {rhs_str}:\n"
                        f"  - Counterexample Witness Found: ({w_str}) refutes {lhs_str} = {rhs_str} on the degree grid.\n"
                        "  - Suggestion: Restrict domain hypotheses or project modulo a separating congruence class."
                    )
                    if M.IdentityCompare(interactive, M.truth_value)() is M.truth_value:
                        return self._offer_operation_law(
                            graph, operation_register, domain, reg, report
                        )
                    return report

            # Case C: Concrete equation with no_solutions
            bound_nat = domain_count

            mods_res = BuildNatRange(M.two, M.four, reg)()
            moduli_chain = M.Head(mods_res)()
            reg = M.Head(M.Tail(mods_res)())()

            lhs_str = RenderNatExpr(lhs, reg)()
            rhs_str = RenderNatExpr(rhs, reg)()
            domain_set_str = FormatSetChain(domain, reg)()
            lhs_vars = M.Head(ExtractExprVariables(lhs, reg)())()
            rhs_vars = M.Head(ExtractExprVariables(rhs, reg)())()

            PlaygroundDebugEmit(M.Char(
                f"constructing the natural tensor for {lhs_str} = {rhs_str}: domain {domain_set_str}, candidate moduli {FormatSetChain(moduli_chain, reg)()}..."
            ))()

            lt_res = BuildExprGroundTensor(
                lhs, lhs_vars, domain, M.Char("lhs"), reg
            )()
            lhs_tensor = M.Head(lt_res)()
            reg = M.Head(M.Tail(lt_res)())()

            rt_res = BuildExprGroundTensor(
                rhs, rhs_vars, domain, M.Char("rhs"), reg
            )()
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
                domain_chain=domain,
            )()
            disc_chain = M.Head(disc_res)()
            reg = M.Head(M.Tail(disc_res)())()

            header = f"[machine] Cartesian Playground Sweep for {lhs_str} = {rhs_str} (domain {domain_set_str}, moduli {FormatSetChain(moduli_chain, reg)()}):"
            body = FormatDiscoveriesReport(
                lhs,
                rhs,
                disc_chain,
                moduli_chain,
                bound_nat,
                witness_env,
                positive_only,
                reg,
                indent="  ",
                domain_chain=domain,
            )()
            if M.IdentityCompare(disc_chain, M.EmptyList)() is M.false_value:
                graph._last_discovered_invariant = M.Head(disc_chain)()
                graph._last_playground_discoveries = disc_chain
                body = (
                    body
                    + "\n  - Suggestion: Ground this discovered regularity into active context as an invariant lemma."
                )
            report = header + "\n" + body
            if M.IdentityCompare(interactive, M.truth_value)() is M.truth_value:
                return self._offer_operation_law(
                    graph, operation_register, domain, reg, report
                )
            return report

        # 2. Undecided Socratic tutor claim
        claim_ready = M.false_value
        if M.IdentityCompare(active_claim, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(active_tutor, M.EmptyList)() is M.false_value:
                claim_ready = M.truth_value
        if claim_ready is M.truth_value:
            from . import dialogue as Dlg

            goal_fact = Dlg.claim_conclusion(active_claim)
            known_facts = Dlg.claim_start_facts(active_claim)
            obls_chain = Dlg.BackwardObligations(
                goal_fact, known_facts, active_tutor.rules()
            )()
            claim_str = active_tutor.claim_text(active_claim)
            PlaygroundDebugEmit(M.Char(
                f"analyzing backward rule obligations for undecided claim '{claim_str}'..."
            ))()
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
        PlaygroundDebugEmit(M.Char(
            "constructing the natural tensor: 11 x 11 domain (0..10)^2 x candidate moduli {2, 3, 4, 5}..."
        ))()
        bound_res = M.NatFromRep(M.GMPRep(11), registry)()
        bound_nat = M.Head(bound_res)()
        reg1 = M.Head(M.Tail(bound_res)())()

        mods_res = BuildNatRange(M.two, M.four, reg1)()
        moduli_chain = M.Head(mods_res)()
        reg2 = M.Head(M.Tail(mods_res)())()

        bench_x = M.Char("x")
        bench_y = M.Char("y")
        bench_odd_x = M.Pair(
            L.NatModEqLabel,
            M.Pair(bench_x, M.Pair(M.two, M.Pair(M.one, M.EmptyList))),
        )
        bench_odd_y = M.Pair(
            L.NatModEqLabel,
            M.Pair(bench_y, M.Pair(M.two, M.Pair(M.one, M.EmptyList))),
        )
        bench_odd_pair = M.Pair(bench_odd_x, M.Pair(bench_odd_y, M.EmptyList))
        bench_unary_vars = M.Pair(bench_x, M.EmptyList)
        bench_pair_vars = M.Pair(bench_x, M.Pair(bench_y, M.EmptyList))

        disc_res = DiscoverSeparatingModulus(
            bound_nat,
            M.two,
            bench_unary_vars,
            M.EmptyList,
            bench_pair_vars,
            bench_odd_pair,
            moduli_chain,
            reg2,
        )()
        inv_rec = M.Head(disc_res)()
        reg3 = M.Head(M.Tail(disc_res)())()

        graph._last_discovered_invariant = inv_rec

        res_mod = M.Head(M.Tail(inv_rec)())()
        mod_val = M.NatRepOf(res_mod, reg3)()()
        PlaygroundDebugEmit(M.Char(
            f"discovered separating modulus m = {mod_val} across candidate moduli {FormatSetChain(moduli_chain, reg3)()}."
        ))()

        sq_set = M.Head(M.Tail(M.Tail(inv_rec)())())()
        odd_sum_set = M.Head(M.Tail(M.Tail(M.Tail(inv_rec)())())())()
        is_disjoint = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(inv_rec)())())())())()

        sq_str = FormatSetChain(sq_set, reg3)()
        odd_str = FormatSetChain(odd_sum_set, reg3)()
        tested_str = FormatSetChain(moduli_chain, reg3)()

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

    def __call__(self):
        return self.result


# ============================================================
# Bounded constrained Nat witnesses (not universal existence proofs)
# ============================================================


class ValidNatConstraints(M.Edge):
    """
    True iff `constraints` is a chain of admitted constraint terms over
    `variables`. The admitted constraint vocabulary is machine data:

        ExprEq(lhs, rhs)      binary, polynomial equality
        ExprLt(lhs, rhs)      binary, polynomial order
        Divides(a, b)         binary, machine divisibility
        Coprime(a, b)         binary, machine coprimality
        NotCoprime(a, b)      binary, complement of machine coprimality
        NatModEq(term, m, r)  ternary, residue equality

    Every expression argument must be admitted by AdmittedPolynomial over
    `variables`.
    """

    def __init__(self, constraints, variables, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, constraints
            )()
            ops = M.Head(built)()
        self.result = self._valid(constraints, variables, registry, ops)
        super().__init__(
            inputs=M.Pair(
                constraints,
                M.Pair(variables, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _args_admitted(
        self, args, variables, registry, ops, remaining=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            remaining = args
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.truth_value
        if AdmittedPolynomial(
            M.Head(remaining)(), variables, registry, ops
        )() is M.false_value:
            return M.false_value
        return self._args_admitted(
            args, variables, registry, ops, M.Tail(remaining)(),
            M.truth_value,
        )

    def _valid(
        self, constraints, variables, registry, ops, cursor=M.EmptyList,
        initialized=M.false_value,
    ):
        if ValidPolynomialVariables(variables, registry)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cursor = constraints
        if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
            return M.truth_value
        if M.IsPair(cursor)() is M.false_value:
            return M.false_value
        constraint = M.Head(cursor)()
        if M.IsPair(constraint)() is M.false_value:
            return M.false_value
        head_args = ExprHeadArgs(constraint)()
        head = M.Head(head_args)()
        args = M.Head(M.Tail(head_args)())()
        if M.IdentityCompare(head, L.NatModEqLabel)() is M.truth_value:
            if ExactArity(args, M.three, registry)() is M.false_value:
                return M.false_value
        else:
            known_head = M.OrAtom(
                M.OrAtom(
                    M.IdentityCompare(head, L.ExprEqLabel)(),
                    M.IdentityCompare(head, L.ExprLtLabel)(),
                )(),
                M.OrAtom(
                    M.IdentityCompare(head, L.DividesLabel)(),
                    M.OrAtom(
                        M.IdentityCompare(head, L.CoprimeLabel)(),
                        M.IdentityCompare(head, L.NotCoprimeLabel)(),
                    )(),
                )(),
            )()
            if known_head is M.false_value:
                return M.false_value
            if ExactArity(args, M.two, registry)() is M.false_value:
                return M.false_value
        if self._args_admitted(args, variables, registry, ops) is M.false_value:
            return M.false_value
        return self._valid(
            constraints, variables, registry, ops, M.Tail(cursor)(),
            M.truth_value,
        )

    def __call__(self):
        return self.result


class ValidNatEnvironment(M.Edge):
    """
    True iff `environment` binds exactly the variables in `variables`, in
    order, to in-bound Nats.
    """

    def __init__(self, variables, environment, bound, registry):
        self.registry = registry
        self.result = self._valid(variables, environment, bound, registry)
        super().__init__(
            inputs=M.Pair(
                variables,
                M.Pair(
                    environment,
                    M.Pair(bound, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _valid(
        self, variables, environment, bound, registry,
        cursor=M.EmptyList, remaining=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cursor = variables
            remaining = environment
        if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
            return M.IdentityCompare(remaining, M.EmptyList)()
        if M.IsPair(remaining)() is M.false_value:
            return M.false_value
        entry = M.Head(remaining)()
        if ExactArity(entry, M.two, registry)() is M.false_value:
            return M.false_value
        if M.Compare(M.Head(entry)(), M.Head(cursor)())() is M.false_value:
            return M.false_value
        value = M.Head(M.Tail(entry)())()
        if A.IsNat(value, registry)() is M.false_value:
            return M.false_value
        if M.NatLess(value, bound, registry)() is M.false_value:
            return M.false_value
        return self._valid(
            variables, environment, bound, registry,
            M.Tail(cursor)(), M.Tail(remaining)(), M.truth_value,
        )

    def __call__(self):
        return self.result


class EvaluateNatConstraints(M.Edge):
    """
    Evaluates a machine constraint chain over an environment with the
    machine's own arithmetic. Every constraint argument is an admitted
    expression evaluated by EvaluateNatExpr; the label then selects the
    machine comparison:

        ExprEq      -> NatEq
        ExprLt      -> NatLess
        NatModEq    -> Modulo(term, modulus) equals residue
        Divides     -> the machine's Divides edge
        Coprime     -> the machine's IsCoprime edge

    Result: Pair(truth_value, Pair(registry, EmptyList)) when every
    constraint holds, Pair(false_value, ...) at the first failure, and
    Pair(EmptyList, ...) when a constraint cannot be evaluated.
    """

    def __init__(self, constraints, environment, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = BuildNatOperationRegister(
                registry, constraints
            )()
            ops = M.Head(built)()
        self.result = self._evaluate(constraints, environment, registry, ops)
        super().__init__(
            inputs=M.Pair(
                constraints,
                M.Pair(environment, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _value(self, term, environment, registry, ops):
        evaluated = EvaluateNatExpr(term, environment, registry, ops)()
        return M.Head(evaluated)(), M.Head(M.Tail(evaluated)())()

    def _refuse(self, registry):
        return M.EmptyList, registry

    def _mod_eq(self, args, environment, registry, ops):
        term_val, reg1 = self._value(M.Head(args)(), environment, registry, ops)
        if M.IdentityCompare(term_val, M.EmptyList)() is M.truth_value:
            return M.EmptyList, reg1
        modulus_val, reg2 = self._value(
            M.Head(M.Tail(args)())(), environment, reg1, ops
        )
        if M.IdentityCompare(modulus_val, M.EmptyList)() is M.truth_value:
            return M.EmptyList, reg2
        residue_val, reg3 = self._value(
            M.Head(M.Tail(M.Tail(args)())())(), environment, reg2, ops
        )
        if M.IdentityCompare(residue_val, M.EmptyList)() is M.truth_value:
            return M.EmptyList, reg3
        mod_res = A.Modulo(term_val, modulus_val, reg3)()
        rem = M.Head(mod_res)()
        reg4 = M.Head(M.Tail(mod_res)())()
        if M.IdentityCompare(rem, M.EmptyList)() is M.truth_value:
            return M.EmptyList, reg4
        return M.NatEq(rem, residue_val, reg4)(), reg4

    def _binary(self, head, args, environment, registry, ops):
        first, reg1 = self._value(M.Head(args)(), environment, registry, ops)
        if M.IdentityCompare(first, M.EmptyList)() is M.truth_value:
            return M.EmptyList, reg1
        second, reg2 = self._value(
            M.Head(M.Tail(args)())(), environment, reg1, ops
        )
        if M.IdentityCompare(second, M.EmptyList)() is M.truth_value:
            return M.EmptyList, reg2
        return self._compare(head, first, second, reg2), reg2

    def _evaluate(
        self, constraints, environment, registry, ops,
        cursor=M.EmptyList, initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            cursor = constraints
        if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(registry, M.EmptyList))
        if M.IsPair(cursor)() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        constraint = M.Head(cursor)()
        if M.IsPair(constraint)() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        head = M.Head(constraint)()
        args = M.Tail(constraint)()
        if M.IdentityCompare(head, L.NatModEqLabel)() is M.truth_value:
            if ExactArity(args, M.three, registry)() is M.false_value:
                return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
            verdict, registry = self._mod_eq(args, environment, registry, ops)
        else:
            if ExactArity(args, M.two, registry)() is M.false_value:
                return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
            verdict, registry = self._binary(head, args, environment, registry, ops)
        if M.IdentityCompare(verdict, M.false_value)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(verdict, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        return self._evaluate(
            constraints, environment, registry, ops,
            M.Tail(cursor)(), M.truth_value,
        )

    def _compare(self, head, first, second, registry):
        if M.IdentityCompare(head, L.ExprEqLabel)() is M.truth_value:
            return M.NatEq(first, second, registry)()
        if M.IdentityCompare(head, L.ExprLtLabel)() is M.truth_value:
            return M.NatLess(first, second, registry)()
        if M.IdentityCompare(head, L.DividesLabel)() is M.truth_value:
            return A.Divides(first, second, registry)()
        if M.IdentityCompare(head, L.CoprimeLabel)() is M.truth_value:
            return A.IsCoprime(first, second, registry)()
        if M.IdentityCompare(head, L.NotCoprimeLabel)() is M.truth_value:
            return M.NotAtom(A.IsCoprime(first, second, registry)())()
        return M.EmptyList

    def __call__(self):
        return self.result


class VerifyNatWitness(M.Edge):
    """Re-evaluate a concrete bounded Nat assignment, not a search status."""

    def __init__(self, constraints, variables, bound, environment, registry):
        self.result = self._verify(constraints, variables, bound, environment, registry)
        super().__init__(inputs=M.Pair(constraints, M.Pair(variables, M.Pair(bound,
            M.Pair(environment, M.Pair(registry, M.EmptyList))))), results=self.result)

    def _verify(self, constraints, variables, bound, environment, registry):
        if A.IsNat(bound, registry)() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if ValidNatConstraints(constraints, variables, registry)() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if ValidNatEnvironment(variables, environment, bound, registry)() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        return EvaluateNatConstraints(constraints, environment, registry)()

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

    def _search(
        self, constraints, variables, bound, budget, registry,
        count=M.EmptyList, values=M.EmptyList,
        initialized=M.false_value,
    ):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            count = M.Zero
            env = M.EmptyList
            bound_is_nat = A.IsNat(bound, registry)()
            budget_is_nat = A.IsNat(budget, registry)()
            valid_inputs = M.AndAtom(
                M.AndAtom(bound_is_nat, budget_is_nat)(),
                ValidNatConstraints(constraints, variables, registry)(),
            )()
            if M.IdentityCompare(valid_inputs, M.false_value)() is M.truth_value:
                return self._record(
                    constraints, variables, bound, budget,
                    L.NatWitnessInvalidLabel, env, count, registry,
                )
            zero_bound_with_vars = M.AndAtom(
                M.NotAtom(M.IdentityCompare(variables, M.EmptyList)())(),
                M.NatEq(bound, M.Zero, registry)(),
            )()
            if M.IdentityCompare(zero_bound_with_vars, M.truth_value)() is M.truth_value:
                return self._record(
                    constraints, variables, bound, budget,
                    L.NatWitnessExhaustedLabel, env, count, registry,
                )
            values = self._zeros(variables)
            initialized = M.truth_value
        if M.NatLess(count, budget, registry)() is M.false_value:
            return self._record(
                constraints, variables, bound, budget,
                L.NatWitnessBudgetLabel, M.EmptyList, count, registry,
            )
        env = ZipEnvironment(variables, values)()
        evaluated = EvaluateNatConstraints(constraints, env, registry)()
        verdict = M.Head(evaluated)()
        reg1 = M.Head(M.Tail(evaluated)())()
        counted = A.Add(count, M.one, reg1)()
        count = M.Head(counted)()
        registry = M.Head(M.Tail(counted)())()
        if verdict is M.truth_value:
            return self._record(
                constraints, variables, bound, budget,
                L.NatWitnessFoundLabel, env, count, registry,
            )
        if verdict is M.EmptyList:
            return self._record(
                constraints, variables, bound, budget,
                L.NatWitnessInvalidLabel, M.EmptyList, count, registry,
            )
        advanced = self._advance(values, bound, registry)
        values = M.Head(advanced)()
        registry = M.Head(M.Tail(advanced)())()
        if M.IdentityCompare(values, M.EmptyList)() is M.truth_value:
            return self._record(
                constraints, variables, bound, budget,
                L.NatWitnessExhaustedLabel, M.EmptyList, count, registry,
            )
        return self._search(
            constraints, variables, bound, budget, registry,
            count, values, initialized,
        )

    def __call__(self):
        return self.result


__all__ = (
    "PlaygroundDebugEmit",
    "NaturalPlaygroundDebugEmit",
    "RenderOperationValue",
    "RenderOperationCall",
    "FormatOperationLawExamples",
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
    "NatPowPeano",
    "ProjectTensorModulo",
    "FindTensorEqualityWitness",
    "BuildExprGroundTensor",
    "ExtractExprVariables",
    "ExtractExponentVariables",
    "SubstituteExprVar",
    "RenderNatExpr",
    "DiscoverExprObstructions",
    "ParseSurfaceGoalSpec",
    "IsProofOrMathGoal",
    "ExprHeadArgs",
    "EnvLookup",
    "ZipEnvironment",
    "ExactArity",
    "ChainHasTerm",
    "ChainAppendEnd",
    "ChainConcat",
    "ChainReverse",
    "ChainMergeUnique",
    "ValidPolynomialVariables",
    "AdmittedPolynomial",
    "ResidueDomains",
    "TupleAllUnderMod",
    "TupleAllPositive",
    "TupleNatEqual",
    "ProjectEnvToSubtuple",
    "LookupResidueRow",
    "GoalSpecLhs",
    "GoalSpecRhs",
    "GoalSpecBaseVars",
    "GoalSpecExpVars",
    "GoalSpecParamConstraints",
    "GoalSpecNoSolutions",
    "GoalSpecPositiveOnly",
    "GoalSpecRegistry",
    "FormatSetChain",
    "FormatVarsChain",
    "FormatEnvChain",
    "FormatDiscoveriesReport",
    "ParameterInstanceSweep",
    "FilterCandidateParameters",
    "RunPlaygroundInteractive",
    "ExprDegreeBound",
    "EvaluateNatExpr",
    "PolynomialIdentityByGrid",
    "PolynomialRewriteCertificate",
    "PolynomialGridDerivation",
    "ResidueTable",
    "CongruenceClasses",
    "ValidNatConstraints",
    "ValidNatEnvironment",
    "EvaluateNatConstraints",
    "VerifyNatWitness",
    "FindNatWitness",
)
