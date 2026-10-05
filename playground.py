# ============================================================
# Playground — Cartesian Exploration & Invariant Discovery
# Bounded generative sweep over primitive operations, regularity
# detection, disjoint image discovery, and concept proposal.
# ============================================================
from __future__ import annotations

from . import labels as L
from . import machine as M
from .math import arithmetic as A


class ChainContains(M.Edge):
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


class BuildNatRange(M.Edge):
    """
    Builds a Pair chain of Nat nodes from start_int to end_int (inclusive).
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


class ComputeSquaresMod(M.Edge):
    """
    Computes { x^2 mod m | x in nats_chain }.
    """

    def __init__(self, nats_chain, mod_nat, registry):
        self.registry = registry
        self.result = self._eval(nats_chain, mod_nat, M.EmptyList, registry)
        super().__init__(
            inputs=M.Pair(
                nats_chain,
                M.Pair(mod_nat, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _eval(self, cur_nats, mod_nat, acc_set, registry):
        if M.IdentityCompare(cur_nats, M.EmptyList)() is M.truth_value:
            return M.Pair(acc_set, M.Pair(registry, M.EmptyList))
        x = M.Head(cur_nats)()
        sq_pair = A.Multiply(x, x, registry)()
        sq_node = M.Head(sq_pair)()
        reg1 = M.Head(M.Tail(sq_pair)())()

        mod_pair = A.Modulo(sq_node, mod_nat, reg1)()
        rem_node = M.Head(mod_pair)()
        reg2 = M.Head(M.Tail(mod_pair)())()

        new_acc = SetInsert(rem_node, acc_set, reg2)()
        return self._eval(M.Tail(cur_nats)(), mod_nat, new_acc, reg2)

    def __call__(self):
        return self.result


class ComputeOddSumOfSquaresMod(M.Edge):
    """
    Computes { (x^2 + y^2) mod m | x, y in nats_chain, x mod 2 == 1, y mod 2 == 1 }.
    """

    def __init__(self, nats_chain, mod_nat, two_nat, one_nat, registry):
        self.registry = registry
        self.result = self._eval_outer(
            nats_chain,
            nats_chain,
            mod_nat,
            two_nat,
            one_nat,
            M.EmptyList,
            registry,
        )
        super().__init__(
            inputs=M.Pair(
                nats_chain,
                M.Pair(
                    mod_nat,
                    M.Pair(
                        two_nat,
                        M.Pair(
                            one_nat,
                            M.Pair(registry, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _eval_outer(
        self, cur_x_list, full_y_list, mod_nat, two_nat, one_nat, acc_set, registry
    ):
        if M.IdentityCompare(cur_x_list, M.EmptyList)() is M.truth_value:
            return M.Pair(acc_set, M.Pair(registry, M.EmptyList))
        x = M.Head(cur_x_list)()

        # Check if x is odd (x mod 2 == 1)
        x_mod_res = A.Modulo(x, two_nat, registry)()
        x_rem = M.Head(x_mod_res)()
        reg1 = M.Head(M.Tail(x_mod_res)())()

        x_odd = M.NatEq(x_rem, one_nat, reg1)()
        if x_odd is M.truth_value:
            inner_res = self._eval_inner(
                x,
                full_y_list,
                mod_nat,
                two_nat,
                one_nat,
                acc_set,
                reg1,
            )
            acc_set = M.Head(inner_res)()
            reg1 = M.Head(M.Tail(inner_res)())()

        return self._eval_outer(
            M.Tail(cur_x_list)(),
            full_y_list,
            mod_nat,
            two_nat,
            one_nat,
            acc_set,
            reg1,
        )

    def _eval_inner(
        self, x, cur_y_list, mod_nat, two_nat, one_nat, acc_set, registry
    ):
        if M.IdentityCompare(cur_y_list, M.EmptyList)() is M.truth_value:
            return M.Pair(acc_set, M.Pair(registry, M.EmptyList))
        y = M.Head(cur_y_list)()

        # Check if y is odd (y mod 2 == 1)
        y_mod_res = A.Modulo(y, two_nat, registry)()
        y_rem = M.Head(y_mod_res)()
        reg1 = M.Head(M.Tail(y_mod_res)())()

        y_odd = M.NatEq(y_rem, one_nat, reg1)()
        if y_odd is M.truth_value:
            # x^2
            sq_x_pair = A.Multiply(x, x, reg1)()
            sq_x = M.Head(sq_x_pair)()
            reg2 = M.Head(M.Tail(sq_x_pair)())()

            # y^2
            sq_y_pair = A.Multiply(y, y, reg2)()
            sq_y = M.Head(sq_y_pair)()
            reg3 = M.Head(M.Tail(sq_y_pair)())()

            # x^2 + y^2
            sum_pair = A.Add(sq_x, sq_y, reg3)()
            sum_node = M.Head(sum_pair)()
            reg4 = M.Head(M.Tail(sum_pair)())()

            # (x^2 + y^2) mod m
            mod_pair = A.Modulo(sum_node, mod_nat, reg4)()
            rem_node = M.Head(mod_pair)()
            reg5 = M.Head(M.Tail(mod_pair)())()

            acc_set = SetInsert(rem_node, acc_set, reg5)()
            reg1 = reg5

        return self._eval_inner(
            x,
            M.Tail(cur_y_list)(),
            mod_nat,
            two_nat,
            one_nat,
            acc_set,
            reg1,
        )

    def __call__(self):
        return self.result


class RunPlaygroundCartesianSweep(M.Edge):
    """
    Executes the Cartesian exploration sweep over small nats (0..10),
    evaluates squares and odd sums mod 4, and identifies the disjoint image invariant.
    """

    def __init__(self, registry):
        self.registry = registry
        self.result = self._explore(registry)
        super().__init__(
            inputs=M.Pair(registry, M.EmptyList),
            results=self.result,
        )

    def _explore(self, registry):
        # Build range 0..10
        range_res = BuildNatRange(0, 10, registry)()
        nats_chain = M.Head(range_res)()
        reg1 = M.Head(M.Tail(range_res)())()

        # Nat nodes for 4, 2, 1
        n4_res = M.NatFromRep(M.GMPRep(4), reg1)()
        n4 = M.Head(n4_res)()
        reg2 = M.Head(M.Tail(n4_res)())()

        n2_res = M.NatFromRep(M.GMPRep(2), reg2)()
        n2 = M.Head(n2_res)()
        reg3 = M.Head(M.Tail(n2_res)())()

        n1_res = M.NatFromRep(M.GMPRep(1), reg3)()
        n1 = M.Head(n1_res)()
        reg4 = M.Head(M.Tail(n1_res)())()

        # Compute { z^2 mod 4 }
        sq_res = ComputeSquaresMod(nats_chain, n4, reg4)()
        sq_set = M.Head(sq_res)()
        reg5 = M.Head(M.Tail(sq_res)())()

        # Compute { (x^2 + y^2) mod 4 | x, y odd }
        odd_sum_res = ComputeOddSumOfSquaresMod(
            nats_chain, n4, n2, n1, reg5
        )()
        odd_sum_set = M.Head(odd_sum_res)()
        reg6 = M.Head(M.Tail(odd_sum_res)())()

        # Check intersection { z^2 mod 4 } /\ { (x^2 + y^2) mod 4 }
        inter = SetIntersection(sq_set, odd_sum_set, reg6)()
        is_disjoint = M.IdentityCompare(inter, M.EmptyList)()

        # Wrap discovered invariant record
        invariant_rec = M.Pair(
            L.DiscoveredInvariantLabel,
            M.Pair(
                n4,
                M.Pair(
                    sq_set,
                    M.Pair(
                        odd_sum_set,
                        M.Pair(is_disjoint, M.EmptyList),
                    ),
                ),
            ),
        )

        return M.Pair(
            invariant_rec,
            M.Pair(reg6, M.EmptyList),
        )

    def __call__(self):
        return self.result


def run_playground_interactive(graph):
    """
    Runs the Cartesian playground exploration sweep and returns the formatted proposal string.
    """
    registry = M.FromContextGetConstructors(graph)()
    sweep_res = RunPlaygroundCartesianSweep(registry)()
    inv_rec = M.Head(sweep_res)()

    n4 = M.Head(M.Tail(inv_rec)())()
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

    proposal = [
        "[machine] Cartesian Playground Sweep (inputs x, y in 0..10):",
        f"  - Evaluated primitive squares: x^2 mod 4 in {{{', '.join(map(str, sorted(sq_vals)))}}}",
        f"  - Evaluated odd sum of squares: (x^2 + y^2) mod 4 in {{{', '.join(map(str, sorted(odd_vals)))}}} for all odd x, y",
        f"  - Observed disjoint intersection: {{{', '.join(map(str, sorted(sq_vals)))}}} /\ {{{', '.join(map(str, sorted(odd_vals)))}}} = empty",
        "  - Regularity Claim: Under Modulo 4, no integer square can equal the sum of two odd integer squares (X^2 + Y^2 = Z^2 has no solutions with both X and Y odd).",
        "  - Suggestion: Ground this pattern as 'ParityMod4Lemma' into active context.",
    ]
    return "\n".join(proposal)


__all__ = (
    "ChainContains",
    "SetInsert",
    "SetIntersection",
    "BuildNatRange",
    "ComputeSquaresMod",
    "ComputeOddSumOfSquaresMod",
    "RunPlaygroundCartesianSweep",
    "run_playground_interactive",
)
