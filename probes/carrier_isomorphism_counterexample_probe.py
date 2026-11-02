"""Counterexamples for carrier-complete hypergraph isomorphism (commit 2d612b2).

Question it answers: where does the shipped matcher's verdict, or the renaming it
returns, disagree with the definition printed in its docstring? Three cases are
pinned here:

  A1  an accept with no edge-preserving bijection behind it (EmptyList entity)
  A2  a refusal of a pair whose edges do admit a bijection over the carriers
  A3  the same graph pair flipping its verdict when only the edge order changes
  B   the same node set read differently for a Patricia store and a bare chain

Each case ends in an assertion that pins the behaviour observed on 2d612b2. The
assertions are expected to fail once the matcher is repaired; that is their point,
so a green run means the defect is present, not that the matcher is correct.

Machine-native: every measurement is a module-level M.Edge, every walk is a
`while M.IsPair(...)` step, and no host list, helper function or type test appears.
TermText renders terms for the report only; no verdict reads a rendered string.

Usage:
    python probes/carrier_isomorphism_counterexample_probe.py
"""
import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from cat_theo_machine import machine as M
from cat_theo_machine import matching as MatchMod
from cat_theo_machine.runtime import make_fresh_runtime
from cat_theo_machine import graph as GraphMod
from cat_theo_machine.search.patricia import (
    SearchPatriciaBranch,
    SearchPatriciaChoice,
    SearchPatriciaLeaf,
)

registry = M.FromContextGetConstructors(make_fresh_runtime().graph)()


class ChainLength(M.Edge):
    """Number of Pair cells in a chain, for reporting only."""

    def __init__(self, chain):
        count = 0
        remaining = chain
        while M.IsPair(remaining)() is M.truth_value:
            count = count + 1
            remaining = M.Tail(remaining)()
        self.result = count
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=count)

    def __call__(self):
        return self.result


class ChainReverse(M.Edge):
    """Right-to-left copy of a chain."""

    def __init__(self, chain, accumulated=M.EmptyList):
        verdict = accumulated
        if M.IsPair(chain)() is M.truth_value:
            verdict = ChainReverse(
                M.Tail(chain)(), M.Pair(M.Head(chain)(), accumulated)
            )()
        self.result = verdict
        super().__init__(
            inputs=M.Pair(chain, M.Pair(accumulated, M.EmptyList)), results=verdict
        )

    def __call__(self):
        return self.result


class ChainHasTerm(M.Edge):
    """Membership by Compare, the equality the matcher itself uses."""

    def __init__(self, chain, term):
        verdict = M.false_value
        remaining = chain
        while M.IsPair(remaining)() is M.truth_value:
            if M.Compare(M.Head(remaining)(), term)() is M.truth_value:
                verdict = M.truth_value
            remaining = M.Tail(remaining)()
        self.result = verdict
        super().__init__(
            inputs=M.Pair(chain, M.Pair(term, M.EmptyList)), results=verdict
        )

    def __call__(self):
        return self.result


class TermText(M.Edge):
    """Symbol text for a Char, "[]" for EmptyList, "<term>" otherwise."""

    def __init__(self, term):
        text = "<term>"
        if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
            text = "[]"
        elif M.IsPair(term)() is M.false_value:
            text = str(term())
        self.result = text
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=text)

    def __call__(self):
        return self.result


class RenamingImageOf(M.Edge):
    """Image of a vertex under a renaming chain, else EmptyList."""

    def __init__(self, renaming, vertex):
        image = M.EmptyList
        remaining = renaming
        while M.IsPair(remaining)() is M.truth_value:
            entry = M.Head(remaining)()
            if M.Compare(M.Head(entry)(), vertex)() is M.truth_value:
                image = M.Tail(entry)()
            remaining = M.Tail(remaining)()
        self.result = image
        super().__init__(
            inputs=M.Pair(renaming, M.Pair(vertex, M.EmptyList)), results=image
        )

    def __call__(self):
        return self.result


class RenamingImages(M.Edge):
    """The images of a renaming chain, in the same order."""

    def __init__(self, renaming):
        images = M.EmptyList
        remaining = renaming
        while M.IsPair(remaining)() is M.truth_value:
            images = M.Pair(RenamingImageOf(renaming, M.Head(M.Head(remaining)())())(), images)
            remaining = M.Tail(remaining)()
        self.result = ChainReverse(images)()
        super().__init__(inputs=M.Pair(renaming, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RenamingSources(M.Edge):
    """The sources of a renaming chain, in the same order."""

    def __init__(self, renaming):
        sources = M.EmptyList
        remaining = renaming
        while M.IsPair(remaining)() is M.truth_value:
            sources = M.Pair(M.Head(M.Head(remaining)())(), sources)
            remaining = M.Tail(remaining)()
        self.result = ChainReverse(sources)()
        super().__init__(inputs=M.Pair(renaming, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RepeatedTermCount(M.Edge):
    """How many terms in a chain Compare-equal an earlier term of the same chain."""

    def __init__(self, chain):
        count = 0
        remaining = chain
        seen = M.EmptyList
        while M.IsPair(remaining)() is M.truth_value:
            term = M.Head(remaining)()
            if ChainHasTerm(seen, term)() is M.truth_value:
                count = count + 1
            seen = M.Pair(term, seen)
            remaining = M.Tail(remaining)()
        self.result = count
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=count)

    def __call__(self):
        return self.result


class MappedEdge(M.Edge):
    """An edge with every argument replaced by its image, relation label kept."""

    def __init__(self, edge, renaming):
        args = M.Tail(edge)()
        mapped = M.EmptyList
        while M.IsPair(args)() is M.truth_value:
            mapped = M.Pair(
                RenamingImageOf(renaming, M.Head(args)())(), mapped
            )
            args = M.Tail(args)()
        self.result = M.Pair(M.Head(edge)(), ChainReverse(mapped)())
        super().__init__(
            inputs=M.Pair(edge, M.Pair(renaming, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class AllEdgesMappedInto(M.Edge):
    """Whether every source edge lands on a target edge under the renaming."""

    def __init__(self, edges, renaming, target_edges):
        verdict = M.truth_value
        remaining = edges
        while M.IsPair(remaining)() is M.truth_value:
            image = MappedEdge(M.Head(remaining)(), renaming)()
            if ChainHasTerm(target_edges, image)() is M.false_value:
                verdict = M.false_value
            remaining = M.Tail(remaining)()
        self.result = verdict
        super().__init__(
            inputs=M.Pair(edges, M.Pair(renaming, M.Pair(target_edges, M.EmptyList))),
            results=verdict,
        )

    def __call__(self):
        return self.result


class BijectionSearch(M.Edge):
    """Whether any edge-preserving bijection exists between two carriers.

    Exhaustive over carrier-to-carrier bijections: at each step an unused target
    is offered to the first unplaced source, and a complete renaming is accepted
    only if every source edge maps onto a target edge. Equal edge counts are
    checked by the membership test alone, since a bijection on vertices that sends
    each edge onto an edge of an equally sized edge set is edge-bijective.
    """

    def __init__(self, sources, targets, renaming, source_edges, target_edges):
        verdict = M.false_value
        if M.IsPair(sources)() is M.false_value:
            verdict = AllEdgesMappedInto(source_edges, renaming, target_edges)()
        else:
            remaining = targets
            while M.IsPair(remaining)() is M.truth_value:
                candidate = M.Head(remaining)()
                if ChainHasTerm(RenamingImages(renaming)(), candidate)() is M.false_value:
                    extended = M.Pair(
                        M.Pair(M.Head(sources)(), candidate), renaming
                    )
                    if (
                        BijectionSearch(
                            M.Tail(sources)(),
                            targets,
                            extended,
                            source_edges,
                            target_edges,
                        )()
                        is M.truth_value
                    ):
                        verdict = M.truth_value
                remaining = M.Tail(remaining)()
        self.result = verdict
        super().__init__(
            inputs=M.Pair(
                sources,
                M.Pair(
                    targets,
                    M.Pair(
                        renaming,
                        M.Pair(source_edges, M.Pair(target_edges, M.EmptyList)),
                    ),
                ),
            ),
            results=verdict,
        )

    def __call__(self):
        return self.result


class MatcherReport(M.Edge):
    """Run the matcher on two graphs and report verdict, map health and carriers.

    result: Pair(verdict, Pair(renaming, Pair(carrier_1, Pair(carrier_2, EmptyList))))
    """

    def __init__(self, label, g1, g2):
        matcher = MatchMod.HypergraphIsomorphismMatch(g1, g2, registry)
        matched = matcher.result
        verdict = M.Head(matched)()
        iso_node = M.Head(M.Tail(matched)())()
        renaming = M.EmptyList
        if M.IsPair(iso_node)() is M.truth_value:
            renaming = M.Head(M.Tail(iso_node)())()
        print(
            "  "
            + label
            + "  verdict="
            + ("iso" if verdict is M.truth_value else "not-iso")
            + "  |carrier1|="
            + str(ChainLength(matcher.carrier_1)())
            + "  |carrier2|="
            + str(ChainLength(matcher.carrier_2)())
            + "  |map|="
            + str(ChainLength(renaming)())
            + "  repeated-images="
            + str(RepeatedTermCount(RenamingImages(renaming)())())
            + "  repeated-sources="
            + str(RepeatedTermCount(RenamingSources(renaming)())()),
            flush=True,
        )
        self.result = M.Pair(
            verdict,
            M.Pair(renaming, M.Pair(matcher.carrier_1, M.Pair(matcher.carrier_2, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(g1, M.Pair(g2, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


def hypergraph(store, edge_chain):
    graph = make_fresh_runtime().graph
    graph.nodes = store
    graph.edges = edge_chain
    return graph


print("=== counterexamples for 2d612b2 (read-only) ===", flush=True)
print()

# ---- A1: an accept with no edge-preserving bijection behind it ----------------
print("[A1] EmptyList bound as an image, then bound again")
sym_r = M.Char("R")
sym_s = M.Char("S")
sym_t = M.Char("T")
v_b = M.Char("v_b")
v_y = M.Char("v_y")
v_z = M.Char("v_z")
v_w = M.Char("v_w")
v_v = M.Char("v_v")
v_q = M.Char("v_q")
v_z2 = M.Char("v_z2")
v_p = M.Char("v_p")

source_graph = hypergraph(
    M.Pair(v_b, M.Pair(v_y, M.Pair(v_z, M.Pair(v_w, M.EmptyList)))),
    M.Pair(
        M.Pair(sym_r, M.Pair(v_b, M.Pair(v_y, M.EmptyList))),
        M.Pair(
            M.Pair(sym_s, M.Pair(v_b, M.Pair(v_z, M.EmptyList))),
            M.Pair(M.Pair(sym_t, M.Pair(M.EmptyList, M.EmptyList)), M.EmptyList),
        ),
    ),
)
target_graph = hypergraph(
    M.Pair(v_q, M.Pair(v_z2, M.EmptyList)),
    M.Pair(
        M.Pair(sym_r, M.Pair(M.EmptyList, M.Pair(v_q, M.EmptyList))),
        M.Pair(
            M.Pair(sym_s, M.Pair(v_v, M.Pair(v_z2, M.EmptyList))),
            M.Pair(M.Pair(sym_t, M.Pair(v_p, M.EmptyList)), M.EmptyList),
        ),
    ),
)
a1 = MatcherReport("R(b,y) S(b,z) T([])  against  R([],q) S(v,z2) T(p)", source_graph, target_graph)
a1_result = M.Head(a1.result)()
a1_renaming = M.Head(M.Tail(a1.result)())()
a1_carrier_1 = M.Head(M.Tail(M.Tail(a1.result)())())()
a1_carrier_2 = M.Head(M.Tail(M.Tail(M.Tail(a1.result)())())())()
a1_bijection = BijectionSearch(
    a1_carrier_1, a1_carrier_2, M.EmptyList, source_graph.edges, target_graph.edges
)()
print("       edge-preserving bijection exists: " + ("yes" if a1_bijection is M.truth_value else "NO"))
print(
    "       map length "
    + str(ChainLength(a1_renaming)())
    + " over a carrier of "
    + str(ChainLength(a1_carrier_1)())
)
assert a1_result is M.truth_value, (
    "A1: 2d612b2 accepted this pair; the assertion records the unsound accept"
)
assert a1_bijection is M.false_value, (
    "A1: no edge-preserving bijection exists, so the accept is unsound"
)
assert ChainLength(a1_renaming)() > ChainLength(a1_carrier_1)(), (
    "A1: the accepted map holds more entries than the carrier has vertices"
)
print()

# ---- A2: a refusal of a pair whose edges do admit a bijection ----------------
print("[A2] an edge argument equal to EmptyList on the source side")
a2_source = hypergraph(
    M.Pair(v_b, M.EmptyList),
    M.Pair(M.Pair(sym_r, M.Pair(v_b, M.Pair(M.EmptyList, M.EmptyList))), M.EmptyList),
)
a2_target = hypergraph(
    M.EmptyList,
    M.Pair(M.Pair(sym_r, M.Pair(v_q, M.Pair(v_z2, M.EmptyList))), M.EmptyList),
)
a2 = MatcherReport("R(b,[]) against R(q,z2)", a2_source, a2_target)
a2_result = M.Head(a2.result)()
a2_carrier_1 = M.Head(M.Tail(M.Tail(a2.result)())())()
a2_carrier_2 = M.Head(M.Tail(M.Tail(M.Tail(a2.result)())())())()
a2_bijection = BijectionSearch(
    a2_carrier_1, a2_carrier_2, M.EmptyList, a2_source.edges, a2_target.edges
)()
print("       edge-preserving bijection exists: " + ("yes" if a2_bijection is M.truth_value else "NO"))
assert a2_bijection is M.truth_value, "A2: the pair does admit a bijection"
assert a2_result is M.false_value, (
    "A2: 2d612b2 refused this pair although a bijection exists; the assertion records it"
)
print()

# ---- A3: the same pair, edge order only changed ------------------------------
print("[A3] the A1 pair with the edge store written in the other order")
swapped_graph = hypergraph(
    M.Pair(v_b, M.Pair(v_y, M.Pair(v_z, M.Pair(v_w, M.EmptyList)))),
    M.Pair(
        M.Pair(sym_s, M.Pair(v_b, M.Pair(v_z, M.EmptyList))),
        M.Pair(
            M.Pair(sym_r, M.Pair(v_b, M.Pair(v_y, M.EmptyList))),
            M.Pair(M.Pair(sym_t, M.Pair(M.EmptyList, M.EmptyList)), M.EmptyList),
        ),
    ),
)
a3 = MatcherReport("S(b,z) R(b,y) T([])  against  S(v,z2) R([],q) T(p)", swapped_graph, target_graph)
assert M.Head(a3.result)() is M.false_value, (
    "A3: the same graph pair refused once the edge order changed; assertion records the flip"
)
print()

# ---- B: one node set, two store representations ------------------------------
print("[B] Patricia-backed node store against the same nodes as a bare chain")
node_a = M.Char("node_a")
node_b = M.Char("node_b")
node_c = M.Char("node_c")

patricia_store = SearchPatriciaBranch(
    M.EmptyList,
    M.Pair(
        SearchPatriciaChoice(
            M.Char("tok_a"),
            SearchPatriciaLeaf(M.EmptyList, node_a, node_a, node_a)(),
        )(),
        M.Pair(
            SearchPatriciaChoice(
                M.Char("tok_b"),
                SearchPatriciaLeaf(M.EmptyList, node_b, node_b, node_b)(),
            )(),
            M.EmptyList,
        ),
    ),
)()
chain_store = M.Pair(node_a, M.Pair(node_b, M.EmptyList))
other_chain = M.Pair(node_c, M.Pair(node_b, M.EmptyList))

print(
    "       GraphStoreValues(patricia) yields "
    + str(ChainLength(GraphMod.GraphStoreValues(patricia_store)())())
    + " node values"
)
b1 = MatcherReport(
    "patricia store of 2 against chain of the same 2",
    hypergraph(patricia_store, M.EmptyList),
    hypergraph(chain_store, M.EmptyList),
)
b2 = MatcherReport(
    "chain of 2 against chain of 2",
    hypergraph(chain_store, M.EmptyList),
    hypergraph(other_chain, M.EmptyList),
)
assert M.Head(b2.result)() is M.truth_value, "B: two bare chains of equal size match"
assert M.Head(b1.result)() is M.false_value, (
    "B: 2d612b2 refused the same node set stored as a Patricia; assertion records it"
)
print()
print("=== counterexample run complete; assertions pin observed 2d612b2 behaviour ===")
