"""Read-only audit of carrier-complete hypergraph isomorphism (commit 2d612b2).

Question it answers: for the shipped carrier-complete matcher, are these six
claims true -- (1) every edge entity is in the carrier, (2) every declared node
is too even with no incident edge, (3) the edge phase binds every edge-involved
vertex, (4) anything left unbound at completion is isolated, (5) any bijection
between the leftovers preserves the edges, (6) neither store order nor store
representation can change the verdict?

It also measures the two boundaries where the answer is no: an edge argument
equal to EmptyList, and a Patricia-backed node store. The counterexamples and
their pinned behaviour live in `carrier_isomorphism_counterexample_probe.py`.

Machine-native: every check is a module-level M.Edge, every walk is a
`while M.IsPair(...)` step, and no host list, helper function or type test
appears. `AuditCase` is the single reporting edge, in the shape the repository
uses for debug emitters. TermText renders terms for the report only; no verdict
reads a rendered string.

Usage:
    python probes/carrier_isomorphism_audit_probe.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import matching as MatchMod
from cat_theo_machine import playground as PG
from cat_theo_machine import graph as GraphMod
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
registry = M.FromContextGetConstructors(make_fresh_runtime().graph)()


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


class ChainLength(M.Edge):
    """Chain length, a host count used only to report sizes."""

    def __init__(self, chain):
        count = 0
        remaining = chain
        while M.IsPair(remaining)() is M.truth_value:
            count += 1
            remaining = M.Tail(remaining)()
        self.result = count
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=count)

    def __call__(self):
        return self.result


class EdgeEntities(M.Edge):
    """Distinct entities any edge mentions, deduplicated by Compare."""

    def __init__(self, edges):
        entities = M.EmptyList
        remaining_edges = edges
        while M.IsPair(remaining_edges)() is M.truth_value:
            edge = M.Head(remaining_edges)()
            if M.IsPair(edge)() is M.truth_value:
                remaining_args = M.Tail(edge)()
                while M.IsPair(remaining_args)() is M.truth_value:
                    argument = M.Head(remaining_args)()
                    if ChainHasTerm(entities, argument)() is M.false_value:
                        entities = M.Pair(argument, entities)
                    remaining_args = M.Tail(remaining_args)()
            remaining_edges = M.Tail(remaining_edges)()
        self.result = entities
        super().__init__(inputs=M.Pair(edges, M.EmptyList), results=entities)

    def __call__(self):
        return self.result


class EntitiesMissingFromRenaming(M.Edge):
    """Edge entities with no image; non-empty means claim 3 fails."""

    def __init__(self, edges, renaming):
        missing = M.EmptyList
        remaining = EdgeEntities(edges)()
        while M.IsPair(remaining)() is M.truth_value:
            entity = M.Head(remaining)()
            if M.IdentityCompare(
                RenamingImageOf(renaming, entity)(), M.EmptyList
            )() is M.truth_value:
                missing = M.Pair(entity, missing)
            remaining = M.Tail(remaining)()
        self.result = missing
        super().__init__(
            inputs=M.Pair(edges, M.Pair(renaming, M.EmptyList)), results=missing
        )

    def __call__(self):
        return self.result


class RenamingSourcesOutsideEdges(M.Edge):
    """Renaming sources no edge mentions: the isolated half of the mapping."""

    def __init__(self, edges, renaming):
        outside = M.EmptyList
        entities = EdgeEntities(edges)()
        remaining = renaming
        while M.IsPair(remaining)() is M.truth_value:
            entry = M.Head(remaining)()
            if ChainHasTerm(entities, M.Head(entry)())() is M.false_value:
                outside = M.Pair(M.Head(entry)(), outside)
            remaining = M.Tail(remaining)()
        self.result = outside
        super().__init__(
            inputs=M.Pair(edges, M.Pair(renaming, M.EmptyList)), results=outside
        )

    def __call__(self):
        return self.result


class RenamingBindsCarrier(M.Edge):
    """Totality, injectivity, surjectivity and cleanliness over two carriers."""

    def __init__(self, renaming, source_nodes, target_nodes):
        totality = self._binds_once(renaming, source_nodes, M.truth_value)
        surjectivity = self._binds_once(renaming, target_nodes, M.false_value)
        self.result = M.AndAtom(
            M.AndAtom(totality, surjectivity)(),
            self._stays_inside(renaming, source_nodes, target_nodes),
        )()
        super().__init__(
            inputs=M.Pair(
                renaming, M.Pair(source_nodes, M.Pair(target_nodes, M.EmptyList))
            ),
            results=self.result,
        )

    def _occurrences(self, renaming, vertex, as_source):
        seen = 0
        remaining = renaming
        while M.IsPair(remaining)() is M.truth_value:
            entry = M.Head(remaining)()
            component = (
                M.Head(entry)() if as_source is M.truth_value else M.Tail(entry)()
            )
            if M.Compare(component, vertex)() is M.truth_value:
                seen += 1
            remaining = M.Tail(remaining)()
        return seen

    def _binds_once(self, renaming, vertices, as_source):
        verdict = M.truth_value
        remaining = vertices
        while M.IsPair(remaining)() is M.truth_value:
            vertex = M.Head(remaining)()
            if self._occurrences(renaming, vertex, as_source) != 1:
                verdict = M.false_value
            remaining = M.Tail(remaining)()
        return verdict

    def _stays_inside(self, renaming, source_nodes, target_nodes):
        verdict = M.truth_value
        remaining = renaming
        while M.IsPair(remaining)() is M.truth_value:
            entry = M.Head(remaining)()
            inside_source = ChainHasTerm(source_nodes, M.Head(entry)())()
            inside_target = ChainHasTerm(target_nodes, M.Tail(entry)())()
            if M.AndAtom(inside_source, inside_target)() is M.false_value:
                verdict = M.false_value
            remaining = M.Tail(remaining)()
        return verdict

    def __call__(self):
        return self.result


class AuditCase(M.Edge):
    """Run the matcher on two graphs and report verdict, sizes and mapping health.

    result: Pair(verdict, Pair(binds_both_carriers,
                  Pair(missing_edge_entities, Pair(isolated_sources, EmptyList))))
    """

    def __init__(self, label, g1, g2):
        matcher = MatchMod.HypergraphIsomorphismMatch(g1, g2, registry)
        matched = matcher.result
        verdict = M.Head(matched)()
        iso_node = M.Head(M.Tail(matched)())()
        renaming = M.EmptyList
        if M.IsPair(iso_node)() is M.truth_value:
            renaming = M.Head(M.Tail(iso_node)())()
        binds = RenamingBindsCarrier(
            renaming, matcher.carrier_1, matcher.carrier_2
        )()
        missing = EntitiesMissingFromRenaming(g1.edges, renaming)()
        isolated = RenamingSourcesOutsideEdges(g1.edges, renaming)()
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
            + "  map-binds-both="
            + ("yes" if binds is M.truth_value else "NO")
            + "  edge-entities-unmapped="
            + str(ChainLength(missing)())
            + "  isolated-sources="
            + str(ChainLength(isolated)()),
            flush=True,
        )
        self.verdict = verdict
        self.renaming = renaming
        self.carrier_1 = matcher.carrier_1
        self.carrier_2 = matcher.carrier_2
        self.result = M.Pair(
            verdict,
            M.Pair(
                binds,
                M.Pair(
                    missing,
                    M.Pair(isolated, M.EmptyList),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(g1, M.Pair(g2, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class PatriciaLeafTerm(M.Edge):
    """A SearchPatricia leaf in its literal term shape, carrying one fact."""

    def __init__(self, key, fact):
        self.result = M.Pair(
            L.SearchPatriciaLeafLabel,
            M.Pair(
                M.EmptyList,
                M.Pair(M.EmptyList, M.Pair(key, M.Pair(fact, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(key, M.Pair(fact, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class PatriciaChoiceTerm(M.Edge):
    def __init__(self, token, subtree):
        self.result = M.Pair(
            L.SearchPatriciaChoiceLabel, M.Pair(token, M.Pair(subtree, M.EmptyList))
        )
        super().__init__(
            inputs=M.Pair(token, M.Pair(subtree, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class PatriciaBranchTerm(M.Edge):
    def __init__(self, prefix, choices):
        self.result = M.Pair(
            L.SearchPatriciaBranchLabel, M.Pair(prefix, M.Pair(choices, M.EmptyList))
        )
        super().__init__(
            inputs=M.Pair(prefix, M.Pair(choices, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


print("=== AUDIT: carrier-complete hypergraph isomorphism (2d612b2) ===")
print()

atom_a = M.Char("vertex_a")
atom_b = M.Char("vertex_b")
atom_c = M.Char("vertex_c")
atom_d = M.Char("vertex_d")
atom_e = M.Char("vertex_e")
atom_f = M.Char("vertex_f")
tgt_p = M.Char("vertex_p")
tgt_q = M.Char("vertex_q")
tgt_r = M.Char("vertex_r")
tgt_s = M.Char("vertex_s")
tgt_t = M.Char("vertex_t")
tgt_u = M.Char("vertex_u")

print("[1] reversed node-store insertion order")
g1 = make_fresh_runtime().graph
g1.nodes = M.Pair(atom_a, M.Pair(atom_b, M.Pair(atom_c, M.EmptyList)))
g1.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))), M.EmptyList
)
g2 = make_fresh_runtime().graph
g2.nodes = M.Pair(tgt_r, M.Pair(tgt_q, M.Pair(tgt_p, M.EmptyList)))
g2.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))), M.EmptyList
)
case = AuditCase("store [a,b,c] against [r,q,p]", g1, g2)
assert M.Head(case())() is M.truth_value, "reversed store order must stay isomorphic"
assert M.Head(M.Tail(case())())() is M.truth_value, "renaming must bind both carriers"
print(
    "       images: a->"
    + TermText(RenamingImageOf(case.renaming, atom_a)())()
    + "  b->"
    + TermText(RenamingImageOf(case.renaming, atom_b)())()
    + "  c->"
    + TermText(RenamingImageOf(case.renaming, atom_c)())()
)
print()

print("[2] legacy edge-only fixture, no declared store")
g1 = make_fresh_runtime().graph
g1.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))), M.EmptyList
)
g2 = make_fresh_runtime().graph
g2.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))), M.EmptyList
)
case = AuditCase("no stores, carrier from edges", g1, g2)
assert M.Head(case())() is M.truth_value, "legacy fixture must stay isomorphic"
assert M.Head(M.Tail(case())())() is M.truth_value, "legacy renaming must bind both"
print()

print("[3] edge-free graphs of several sizes")
g1 = make_fresh_runtime().graph
g1.nodes = M.EmptyList
g1.edges = M.EmptyList
g2 = make_fresh_runtime().graph
g2.nodes = M.EmptyList
g2.edges = M.EmptyList
case = AuditCase("0 vertices against 0", g1, g2)
assert M.Head(case())() is M.truth_value, "two empty carriers must match"
g2.nodes = M.Pair(tgt_p, M.EmptyList)
case = AuditCase("0 vertices against 1", g1, g2)
assert M.Head(case())() is M.false_value, "0 and 1 vertices must not match"
g1.nodes = M.Pair(atom_a, M.EmptyList)
case = AuditCase("1 vertex against 1", g1, g2)
assert M.Head(case())() is M.truth_value, "single-vertex empty graphs must match"
g1.nodes = M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))
g2.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))
case = AuditCase("2 vertices against 2", g1, g2)
assert M.Head(case())() is M.truth_value, "2-vertex empty graphs must match"
g1.nodes = M.Pair(atom_a, M.Pair(atom_b, M.Pair(atom_c, M.EmptyList)))
g2.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.Pair(tgt_r, M.EmptyList)))
case = AuditCase("3 vertices against 3", g1, g2)
assert M.Head(case())() is M.truth_value, "3-vertex empty graphs must match"
print()

print("[4] equal carriers, isolated vertices interleaved differently")
g1 = make_fresh_runtime().graph
g1.nodes = M.Pair(
    atom_e,
    M.Pair(
        atom_f,
        M.Pair(atom_a, M.Pair(atom_b, M.Pair(atom_c, M.Pair(atom_d, M.EmptyList)))),
    ),
)
g1.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
    M.Pair(
        M.Pair(M.Char("S"), M.Pair(atom_c, M.Pair(atom_d, M.EmptyList))),
        M.EmptyList,
    ),
)
g2 = make_fresh_runtime().graph
g2.nodes = M.Pair(
    tgt_p,
    M.Pair(tgt_t, M.Pair(tgt_q, M.Pair(tgt_u, M.Pair(tgt_r, M.Pair(tgt_s, M.EmptyList))))),
)
g2.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.Pair(
        M.Pair(M.Char("S"), M.Pair(tgt_r, M.Pair(tgt_s, M.EmptyList))),
        M.EmptyList,
    ),
)
case = AuditCase("2 edges + 2 isolated, stores interleaved", g1, g2)
assert M.Head(case())() is M.truth_value, "interleaved isolated vertices must match"
assert M.Head(M.Tail(case())())() is M.truth_value, "renaming must bind all 6"
assert ChainLength(M.Head(M.Tail(M.Tail(M.Tail(case())())())())())() == 2, (
    "exactly the two isolated vertices appear as non-edge sources"
)
print()

print("[5] duplicate entries in the declared store")
g1 = make_fresh_runtime().graph
g1.nodes = M.Pair(atom_a, M.Pair(atom_b, M.Pair(atom_b, M.Pair(atom_c, M.EmptyList))))
g1.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))), M.EmptyList
)
g2 = make_fresh_runtime().graph
g2.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.Pair(tgt_r, M.EmptyList)))
g2.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))), M.EmptyList
)
case = AuditCase("store [a,b,b,c] against [p,q,r]", g1, g2)
g1.nodes = M.Pair(atom_a, M.Pair(atom_a, M.EmptyList))
g1.edges = M.EmptyList
g2.nodes = M.Pair(tgt_p, M.EmptyList)
g2.edges = M.EmptyList
case = AuditCase("store [a,a] against [p], no edges", g1, g2)
print()

print("[6] Patricia-backed node store")
g1 = make_fresh_runtime().graph
g1.nodes = PatriciaBranchTerm(
    M.EmptyList,
    M.Pair(
        PatriciaChoiceTerm(
            M.Char("tok_a"), PatriciaLeafTerm(M.Char("k_a"), atom_a)()
        )(),
        M.Pair(
            PatriciaChoiceTerm(
                M.Char("tok_b"), PatriciaLeafTerm(M.Char("k_b"), atom_b)()
            )(),
            M.EmptyList,
        ),
    ),
)()
g1.edges = M.EmptyList
g2 = make_fresh_runtime().graph
g2.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))
g2.edges = M.EmptyList
case = AuditCase("patricia store of 2 against chain of 2", g1, g2)
print(
    "       GraphStoreValues(patricia) yields "
    + str(ChainLength(GraphMod.GraphStoreValues(g1.nodes)())())
    + " values"
)
print()

print("[7] boundary: EmptyList as an edge argument")
g1 = make_fresh_runtime().graph
g1.nodes = M.Pair(atom_a, M.EmptyList)
g1.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(M.EmptyList, M.EmptyList))),
    M.EmptyList,
)
g2 = make_fresh_runtime().graph
g2.nodes = M.EmptyList
g2.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))), M.EmptyList
)
case = AuditCase("R(a, []) against R(p, q)", g1, g2)
print(
    "       image of EmptyList: "
    + TermText(RenamingImageOf(case.renaming, M.EmptyList)())()
)
print()

print("[8] verdict stability across store reorderings of one graph")
g1 = make_fresh_runtime().graph
g1.nodes = M.Pair(atom_a, M.Pair(atom_b, M.Pair(atom_c, M.EmptyList)))
g1.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))), M.EmptyList
)
g2 = make_fresh_runtime().graph
g2.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))), M.EmptyList
)
g2.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.Pair(tgt_r, M.EmptyList)))
first = AuditCase("store [p,q,r]", g1, g2)
g2.nodes = M.Pair(tgt_r, M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList)))
second = AuditCase("store [r,p,q]", g1, g2)
g2.nodes = M.Pair(tgt_q, M.Pair(tgt_r, M.Pair(tgt_p, M.EmptyList)))
third = AuditCase("store [q,r,p]", g1, g2)
assert M.Head(first())() is M.truth_value, "first ordering must match"
assert M.Head(second())() is M.truth_value, "second ordering must match"
assert M.Head(third())() is M.truth_value, "third ordering must match"
print(
    "       isolated image of c: "
    + TermText(RenamingImageOf(first.renaming, atom_c)())()
    + " / "
    + TermText(RenamingImageOf(second.renaming, atom_c)())()
    + " / "
    + TermText(RenamingImageOf(third.renaming, atom_c)())()
)
print()

print("=== audit run complete in " + str(round(time.time() - t0, 1)) + "s ===")
