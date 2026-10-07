from __future__ import annotations

from .. import constructors as C
from .. import gmprep as G
from .. import machine as Mmod
from ..core import (
    Atom,
    DIGITS,
    DIGIT_0,
    Edge,
    EmptyList,
    Head,
    IdentityCompare,
    Pair,
    Tail,
    Zero,
    false_value,
    truth_value,
)
from ..labels import SuccLabel, ZeroLabel
from ..trees import TreeEntries, TreeInsert, TreeLookup


C.set_all_constructors(Head(Tail(C.ConstructedBy(Zero, ZeroLabel, EmptyList, C.AllConstructors)())())())
Zero.value = G.GMPRep("0")


class NatRepOf(Edge, G.GMPHostMath):
    def __init__(self, x, registry):
        self.registry = registry
        self.result = self._rep(x)
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def _rep(self, x):
        current = x
        successors = EmptyList
        base_rep = EmptyList

        while IdentityCompare(base_rep, EmptyList)() is truth_value:
            cached = current()
            if cached is not None:
                try:
                    G.GMPRepText(cached)()
                    base_rep = cached
                    continue
                except Exception:
                    pass
            if C.CompareIn(current, Zero, self.registry)() is truth_value:
                base_rep = G.GMPRep("0")
                Zero.value = base_rep
            else:
                constructor = C.GetConstructor(current, self.registry)()
                if IdentityCompare(constructor, EmptyList)() is truth_value:
                    return EmptyList

                label = Head(constructor)()
                if IdentityCompare(label, SuccLabel)() is false_value:
                    return EmptyList

                cached = current()
                if cached is not None:
                    base_rep = cached
                else:
                    successors = Pair(current, successors)
                    args = Tail(constructor)()
                    current = Head(args)()

        current_rep = base_rep
        remaining_successors = successors
        while IdentityCompare(remaining_successors, EmptyList)() is false_value:
            current_rep = G.GMPRep(current_rep() + self._one_value())
            Head(remaining_successors)().value = current_rep
            remaining_successors = Tail(remaining_successors)()
        return current_rep

    def __call__(self):
        return self.result


class NatFromRep(Edge, G.GMPHostMath):
    def __init__(self, rep, registry):
        self.registry = registry
        self.result = self._from_value(rep())
        super().__init__(inputs=Pair(rep, Pair(registry, EmptyList)), results=self.result)

    def _discover(self, value, entries):
        remaining_entries = entries
        while IdentityCompare(remaining_entries, EmptyList)() is false_value:
            entry = Head(remaining_entries)()
            fact = Head(Tail(entry)())()
            fact_rep = NatRepOf(fact, self.registry)()
            if IdentityCompare(fact_rep, EmptyList)() is false_value:
                if fact_rep() == value:
                    return fact
            remaining_entries = Tail(remaining_entries)()
        return EmptyList

    def _from_value(self, value):
        if value <= self._zero_value():
            Zero.value = G.GMPRep("0")
            return Pair(Zero, Pair(self.registry, EmptyList))

        # Fast path: consult the NatValueIndex (value -> nat node).
        try:
            index_tree = Mmod.NatValueIndex
        except Exception:
            index_tree = EmptyList
        if IdentityCompare(index_tree, EmptyList)() is false_value:
            key = NatValueKey(G.GMPRep(value))()
            found = TreeLookup(index_tree, key, self.registry)()
            if IdentityCompare(found, EmptyList)() is false_value:
                found.value = G.GMPRep(value)
                return Pair(found, Pair(self.registry, EmptyList))

        # When NatValueIndex is missing/empty, scanning the entire constructor
        # registry to "discover" an existing nat node is extremely expensive.
        # For small values, it's much faster (and semantically fine) to build
        # the nat chain from Zero directly.
        if value <= 256:
            current_node = Zero
            current_registry = self.registry
            current_value = self._zero_value()
            Zero.value = G.GMPRep("0")
            while current_value < value:
                next_value = current_value + self._one_value()
                node = Atom()
                constructed = C.ConstructedBy(node, SuccLabel, Pair(current_node, EmptyList), current_registry)()
                current_node = Head(constructed)()
                current_registry = Head(Tail(constructed)())()
                current_node.value = G.GMPRep(next_value)
                if IdentityCompare(index_tree, EmptyList)() is false_value:
                    _nat_value_index_store(index_tree, NatValueKey(G.GMPRep(next_value))(), current_node, current_registry)
                current_value = next_value
            return Pair(current_node, Pair(current_registry, EmptyList))

        discovered = self._discover(value, TreeEntries(self.registry)())
        if IdentityCompare(discovered, EmptyList)() is false_value:
            discovered.value = G.GMPRep(value)
            if IdentityCompare(index_tree, EmptyList)() is false_value:
                _nat_value_index_store(index_tree, NatValueKey(G.GMPRep(value))(), discovered, self.registry)
            return Pair(discovered, Pair(self.registry, EmptyList))

        best_node = Zero
        best_value = self._zero_value()
        current_registry = self.registry
        remaining_entries = TreeEntries(current_registry)()
        Zero.value = G.GMPRep("0")
        while IdentityCompare(remaining_entries, EmptyList)() is false_value:
            entry = Head(remaining_entries)()
            fact = Head(Tail(entry)())()
            fact_rep = NatRepOf(fact, current_registry)()
            if IdentityCompare(fact_rep, EmptyList)() is false_value:
                fact_value = fact_rep()
                if fact_value <= value and fact_value >= best_value:
                    best_node = fact
                    best_value = fact_value
            remaining_entries = Tail(remaining_entries)()

        current_node = best_node
        current_value = best_value
        while current_value < value:
            next_value = current_value + self._one_value()
            node = Atom()
            constructed = C.ConstructedBy(node, SuccLabel, Pair(current_node, EmptyList), current_registry)()
            current_node = Head(constructed)()
            current_registry = Head(Tail(constructed)())()
            current_node.value = G.GMPRep(next_value)
            if IdentityCompare(index_tree, EmptyList)() is false_value:
                _nat_value_index_store(index_tree, NatValueKey(G.GMPRep(next_value))(), current_node, current_registry)
            current_value = next_value
        return Pair(current_node, Pair(current_registry, EmptyList))

    def __call__(self):
        return self.result


class Succ(Edge, G.GMPHostMath):
    def __init__(self, a, registry):
        rep = NatRepOf(a, registry)()
        if IdentityCompare(rep, EmptyList)() is truth_value:
            node = Atom()
            constructed = C.ConstructedBy(node, SuccLabel, Pair(a, EmptyList), registry)()
            self.result = Pair(node, Pair(Head(Tail(constructed)())(), EmptyList))
        else:
            next_rep = G.GMPRep(rep() + self._one_value())
            self.result = NatFromRep(next_rep, registry)()
        super().__init__(inputs=Pair(a, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


one_pair = Succ(Zero, C.AllConstructors)()
one = Head(one_pair)()
C.set_all_constructors(Head(Tail(one_pair)())())

two_pair = Succ(one, C.AllConstructors)()
two = Head(two_pair)()
C.set_all_constructors(Head(Tail(two_pair)())())

three_pair = Succ(two, C.AllConstructors)()
three = Head(three_pair)()
C.set_all_constructors(Head(Tail(three_pair)())())


class Count(Edge, G.GMPHostMath):
    def __init__(self, pair_chain, registry):
        # Construct the nat structurally *and* keep GMP reps hot.
        current_registry = registry
        nat = Zero
        current_rep = G.GMPRep("0")
        Zero.value = current_rep

        remaining = pair_chain
        while IdentityCompare(remaining, EmptyList)() is false_value:
            node = Atom()
            constructed = C.ConstructedBy(node, SuccLabel, Pair(nat, EmptyList), current_registry)()
            nat = Head(constructed)()
            current_registry = Head(Tail(constructed)())()
            current_rep = G.GMPRep(current_rep() + self._one_value())
            nat.value = current_rep
            remaining = Tail(remaining)()

        self.result = Pair(nat, Pair(current_registry, EmptyList))
        super().__init__(inputs=Pair(pair_chain, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CountRep(Edge, G.GMPHostMath):
    def __init__(self, pair_chain):
        self.result = G.GMPRep(self._count_value(pair_chain))
        super().__init__(inputs=Pair(pair_chain, EmptyList), results=self.result)

    def _count_value(self, pair_chain):
        count_value = self._zero_value()
        remaining = pair_chain
        while IdentityCompare(remaining, EmptyList)() is false_value:
            count_value = count_value + self._one_value()
            remaining = Tail(remaining)()
        return count_value

    def __call__(self):
        return self.result


class NatValueKey(Edge):
    def __init__(self, rep):
        self.result = self._encode(rep)
        super().__init__(inputs=Pair(rep, EmptyList), results=self.result)

    def _encode(self, rep):
        # Key is a machine list of interned digit Char atoms.
        return G.GMPRepDigitList(rep)()

    def __call__(self):
        return self.result





def _nat_value_index_store(index_tree, key, nat_node, registry):
    # Keep the Tree object stable: mutate `.value` in-place after insertion.
    updated = TreeInsert(index_tree, key, nat_node, registry)()
    index_tree.value = updated.value


class NatPred(Edge, G.GMPHostMath):
    def __init__(self, n, registry):
        # Prefer structural predecessor when available, but fall back to the
        # nat's cached GMPRep when the Succ constructor isn't visible in the
        # provided registry (common across restored/worker registries).
        constructor = C.GetConstructor(n, registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            cached = n()
            if cached is None:
                atom_result = Pair(Zero, Pair(registry, EmptyList))
            else:
                try:
                    rep_text = G.GMPRepText(cached)()
                    pred_text = G.GMPPredText(rep_text)()
                    if G.GMPEqualText(pred_text, "0")() is truth_value:
                        atom_result = Pair(Zero, Pair(registry, EmptyList))
                    else:
                        pred_atom = Atom()
                        pred_atom.value = G.GMPRep(pred_text)
                        atom_result = Pair(pred_atom, Pair(registry, EmptyList))
                except Exception:
                    atom_result = Pair(Zero, Pair(registry, EmptyList))
        else:
            label = Head(constructor)()
            args = Tail(constructor)()
            if IdentityCompare(label, SuccLabel)() is truth_value:
                atom_result = Pair(Head(args)(), Pair(registry, EmptyList))
            else:
                cached = n()
                if cached is None:
                    atom_result = Pair(Zero, Pair(registry, EmptyList))
                else:
                    try:
                        rep_text = G.GMPRepText(cached)()
                        pred_text = G.GMPPredText(rep_text)()
                        if G.GMPEqualText(pred_text, "0")() is truth_value:
                            atom_result = Pair(Zero, Pair(registry, EmptyList))
                        else:
                            pred_atom = Atom()
                            pred_atom.value = G.GMPRep(pred_text)
                            atom_result = Pair(pred_atom, Pair(registry, EmptyList))
                    except Exception:
                        atom_result = Pair(Zero, Pair(registry, EmptyList))
        self.result = atom_result
        super().__init__(inputs=Pair(n, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class NatEq(Edge):
    def __init__(self, a, b, registry):
        if C.CompareIn(a, b, registry)() is truth_value:
            atom_result = truth_value
        else:
            rep_a = NatRepOf(a, registry)()
            rep_b = NatRepOf(b, registry)()
            if IdentityCompare(rep_a, EmptyList)() is truth_value:
                atom_result = false_value
            elif IdentityCompare(rep_b, EmptyList)() is truth_value:
                atom_result = false_value
            elif rep_a() == rep_b():
                atom_result = truth_value
            else:
                atom_result = false_value
        self.result = atom_result
        super().__init__(inputs=Pair(a, Pair(b, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class NatLess(Edge):
    def __init__(self, a, b, registry):
        rep_a = NatRepOf(a, registry)()
        rep_b = NatRepOf(b, registry)()
        if IdentityCompare(rep_a, EmptyList)() is truth_value:
            atom_result = false_value
        elif IdentityCompare(rep_b, EmptyList)() is truth_value:
            atom_result = false_value
        elif rep_a() < rep_b():
            atom_result = truth_value
        else:
            atom_result = false_value
        self.result = atom_result
        super().__init__(inputs=Pair(a, Pair(b, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


def sync_from_namespace(namespace):
    for name in (
        "truth_value",
        "false_value",
        "EmptyList",
        "Zero",
        "SuccLabel",
        "ZeroLabel",
        "NatValueIndex",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [
    "NatRepOf",
    "NatFromRep",
    "Succ",
    "Count",
    "CountRep",
    "NatPred",
    "NatEq",
    "NatLess",
    "one",
    "two",
    "three",
    "sync_from_namespace",
]
