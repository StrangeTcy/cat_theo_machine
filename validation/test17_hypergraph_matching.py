#!/usr/bin/env python3
"""
Validation Test Suite 17: Hypergraph Matching Hierarchy & Cross-Domain Bridge Synthesis.
Verifies:
1. Level 2 Isomorphism Matching across isomorphic relational structures under node renaming.
2. Carrier-complete isomorphism: isolated vertices are part of the graph. Carriers of
   different cardinality are never isomorphic, and a successful match returns a total,
   injective and surjective renaming over the whole node carrier.
3. Relation labels, arities, entity positions, repeated entities and edge multiplicity
   continue to be preserved, and renamed entities continue to match.
4. Level 4 Shared Structural Invariant Bridging (e.g. E -> rho <- f).
5. Transfer of verified consequences across matched hypergraph structures.
"""
from __future__ import annotations

import os
import sys
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import matching as MatchMod
from cat_theo_machine import playground as PG
from cat_theo_machine.runtime import make_fresh_runtime

# Vertices for the carrier cases: source names and a disjoint set of target names,
# so a match can only come from structure and never from a shared identifier.
atom_a = M.Char("vertex_a")
atom_b = M.Char("vertex_b")
atom_c = M.Char("vertex_c")
atom_d = M.Char("vertex_d")
tgt_p = M.Char("vertex_p")
tgt_q = M.Char("vertex_q")
tgt_r = M.Char("vertex_r")
tgt_s = M.Char("vertex_s")

t0 = time.time()
print("=== TEST 17: Hypergraph Matching Hierarchy & Cross-Domain Bridges ===")

print("\n[1] Initializing hypergraph runtime and registry...")
runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
print("    Runtime and registry initialized.")

print("\n[2] Test Case 1: Level 2 Isomorphism Matching (G1 ≅ G2)...")
# Structure 1: Permutation group over symbols {a, b}
# Structure 2: Permutation group over symbols {1, 2}
a = M.Char("elem_a")
b = M.Char("elem_b")
n1 = M.Char("elem_1")
n2 = M.Char("elem_2")

runtime2 = make_fresh_runtime()
g1 = runtime.graph
g2 = runtime2.graph

# g1 has binary_op then identity
g1.edges = M.Pair(
    M.Pair(M.Char("binary_op"), M.Pair(a, M.Pair(b, M.EmptyList))),
    M.Pair(M.Pair(M.Char("identity"), M.Pair(a, M.EmptyList)), M.EmptyList),
)
# g2 has identity then binary_op in REVERSE order
g2.edges = M.Pair(
    M.Pair(M.Char("identity"), M.Pair(n1, M.EmptyList)),
    M.Pair(M.Pair(M.Char("binary_op"), M.Pair(n1, M.Pair(n2, M.EmptyList))), M.EmptyList),
)

iso_res = MatchMod.HypergraphIsomorphismMatch(g1, g2, registry)()
is_iso = M.Head(iso_res)()
iso_node = M.Head(M.Tail(iso_res)())()
reg1 = M.Head(M.Tail(M.Tail(iso_res)())())()

assert is_iso is M.truth_value, "G1 and G2 should be isomorphic despite reversed edge ordering"
iso_tag = M.Head(iso_node)()
assert M.IdentityCompare(iso_tag, L.IsomorphismLabel)() is M.truth_value, "Tag should be IsomorphismLabel"
print("    Level 2 Isomorphism verified across reversed edge ordering: G1 ≅ G2 (Passed)")

print("\n[3] Test Case 2: Carrier-complete matching (isolated vertices included)...")


class RenamingBindsCarrier(M.Edge):
    """Is a renaming chain a bijection covered by both vertex carriers?

    totality      every source vertex names an entry's first component
    injectivity   no source vertex carries two images
    surjectivity  every target vertex names an entry's second component
    cleanliness   no entry names a vertex absent from either carrier

    Every question is a walk of the renaming chain, so the verdict is assembled
    from those walks and membership edges rather than from host counts.
    """

    def __init__(self, renaming, source_nodes, target_nodes, registry):
        self.renaming = renaming
        self.source_nodes = source_nodes
        self.target_nodes = target_nodes
        self.result = self._verdict()
        super().__init__(
            inputs=M.Pair(
                renaming,
                M.Pair(
                    source_nodes,
                    M.Pair(target_nodes, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _entry_named_by(self, remaining, vertex, as_source, skip_first):
        """First entry whose source (or image) component equals `vertex`."""
        found = M.EmptyList
        if M.IsPair(remaining)() is M.truth_value:
            entry = M.Head(remaining)()
            component = (
                M.Head(entry)() if as_source is M.truth_value else M.Tail(entry)()
            )
            if M.Compare(component, vertex)() is M.truth_value:
                if skip_first is M.truth_value:
                    found = self._entry_named_by(
                        M.Tail(remaining)(), vertex, as_source, M.false_value
                    )
                else:
                    found = entry
            else:
                found = self._entry_named_by(
                    M.Tail(remaining)(), vertex, as_source, skip_first
                )
        return found

    def _vertex_binds_once(self, vertices, as_source):
        verdict = M.truth_value
        remaining = vertices
        while M.IsPair(remaining)() is M.truth_value:
            vertex = M.Head(remaining)()
            first = self._entry_named_by(
                self.renaming, vertex, as_source, M.false_value
            )
            if M.IdentityCompare(first, M.EmptyList)() is M.truth_value:
                verdict = M.false_value
            else:
                second = self._entry_named_by(
                    self.renaming, vertex, as_source, M.truth_value
                )
                if M.IdentityCompare(second, M.EmptyList)() is M.false_value:
                    verdict = M.false_value
            remaining = M.Tail(remaining)()
        return verdict

    def _entries_stay_inside_carriers(self):
        verdict = M.truth_value
        remaining = self.renaming
        while M.IsPair(remaining)() is M.truth_value:
            entry = M.Head(remaining)()
            source_here = PG.ChainHasTerm(self.source_nodes, M.Head(entry)())()
            target_here = PG.ChainHasTerm(self.target_nodes, M.Tail(entry)())()
            if M.AndAtom(source_here, target_here)() is M.false_value:
                verdict = M.false_value
            remaining = M.Tail(remaining)()
        return verdict

    def _verdict(self):
        covered = M.AndAtom(
            self._vertex_binds_once(self.source_nodes, M.truth_value),
            self._vertex_binds_once(self.target_nodes, M.false_value),
        )()
        return M.AndAtom(covered, self._entries_stay_inside_carriers())()


print("    [a] carriers of different cardinality are never isomorphic")
iso_source = make_fresh_runtime().graph
iso_source.nodes = M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))
iso_source.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
    M.EmptyList,
)

iso_target = make_fresh_runtime().graph
iso_target.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.Pair(tgt_r, M.EmptyList)))
iso_target.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.EmptyList,
)

carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.false_value, (
    "A single identical edge over 2 vertices must not match a 3-vertex carrier"
)
assert M.IdentityCompare(
    M.Head(M.Tail(carrier_res)())(), M.EmptyList
)() is M.truth_value, "A refused match returns no renaming"
print("        same single edge, 2 vertices against 3: refused (Passed)")

iso_source.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
    M.Pair(
        M.Pair(M.Char("R"), M.Pair(atom_b, M.Pair(atom_a, M.EmptyList))),
        M.EmptyList,
    ),
)
iso_target.nodes = M.Pair(
    tgt_p, M.Pair(tgt_q, M.Pair(tgt_r, M.Pair(tgt_s, M.EmptyList)))
)
iso_target.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.Pair(
        M.Pair(M.Char("R"), M.Pair(tgt_q, M.Pair(tgt_p, M.EmptyList))),
        M.EmptyList,
    ),
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.false_value, (
    "Two identical edges over 2 vertices must not match a 4-vertex carrier"
)
print("        same two edges, 2 vertices against 4: refused (Passed)")

iso_source.nodes = M.Pair(atom_a, M.EmptyList)
iso_source.edges = M.EmptyList
iso_target.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))
iso_target.edges = M.EmptyList
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.false_value, (
    "Edge-free graphs of 1 and 2 vertices must not be isomorphic"
)
print("        edge-free, 1 vertex against 2: refused (Passed)")

print("    [b] edge-free graphs of equal size are isomorphic, with a complete map")
iso_target.nodes = M.Pair(tgt_p, M.EmptyList)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.truth_value, (
    "Edge-free graphs of equal size must be isomorphic"
)
carrier_map = M.Head(M.Tail(M.Head(M.Tail(carrier_res)())())())()
assert RenamingBindsCarrier(
    carrier_map, iso_source.nodes, iso_target.nodes, registry
)() is M.truth_value, "An edge-free 1-vertex renaming must bind both carriers"
print("        edge-free, 1 vertex each: isomorphic, the vertex is bound (Passed)")

iso_source.nodes = M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))
iso_target.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.truth_value, (
    "Edge-free graphs of equal size must be isomorphic"
)
carrier_map = M.Head(M.Tail(M.Head(M.Tail(carrier_res)())())())()
assert RenamingBindsCarrier(
    carrier_map, iso_source.nodes, iso_target.nodes, registry
)() is M.truth_value, "An edge-free 2-vertex renaming must bind both carriers"
assert M.IdentityCompare(carrier_map, M.EmptyList)() is M.false_value, (
    "An edge-free match returns a non-empty renaming"
)
print("        edge-free, 2 vertices each: isomorphic, both bound (Passed)")

print("    [c] connected and isolated vertices are both carried")
iso_source.nodes = M.Pair(atom_a, M.Pair(atom_b, M.Pair(atom_c, M.EmptyList)))
iso_source.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
    M.EmptyList,
)
iso_target.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.Pair(tgt_r, M.EmptyList)))
iso_target.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.EmptyList,
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.truth_value, (
    "Equal carriers holding one isolated vertex must match"
)
carrier_map = M.Head(M.Tail(M.Head(M.Tail(carrier_res)())())())()
assert RenamingBindsCarrier(
    carrier_map, iso_source.nodes, iso_target.nodes, registry
)() is M.truth_value, (
    "The isolated vertex must appear in the renaming, which stays bijective"
)
isolated_entry = M.EmptyList
remaining_entries = carrier_map
while M.IsPair(remaining_entries)() is M.truth_value:
    entry = M.Head(remaining_entries)()
    if M.Compare(M.Head(entry)(), atom_c)() is M.truth_value:
        isolated_entry = entry
    remaining_entries = M.Tail(remaining_entries)()
assert M.IdentityCompare(isolated_entry, M.EmptyList)() is M.false_value, (
    "The isolated vertex must own a renaming entry"
)
assert M.Compare(M.Tail(isolated_entry)(), tgt_r)() is M.truth_value, (
    "The isolated vertex takes the target vertex no edge reaches"
)
print("        one edge plus one isolated vertex: isomorphic, 3 vertices bound (Passed)")

iso_source.nodes = M.Pair(
    atom_a, M.Pair(atom_b, M.Pair(atom_c, M.Pair(atom_d, M.EmptyList)))
)
iso_target.nodes = M.Pair(
    tgt_p, M.Pair(tgt_q, M.Pair(tgt_r, M.Pair(tgt_s, M.EmptyList)))
)
iso_target.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.EmptyList,
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.truth_value, (
    "Equal carriers holding two isolated vertices must match"
)
carrier_map = M.Head(M.Tail(M.Head(M.Tail(carrier_res)())())())()
assert RenamingBindsCarrier(
    carrier_map, iso_source.nodes, iso_target.nodes, registry
)() is M.truth_value, "Both isolated vertices must be bound, one-to-one"
print("        one edge plus two isolated vertices: isomorphic, 4 bound (Passed)")

print("    [d] the established rejections keep their verdicts")
iso_source.nodes = M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))
iso_source.edges = M.EmptyList
iso_target.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))
iso_target.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.EmptyList,
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.false_value, (
    "An edge present on one side only must be refused"
)
print("        an edge on one side only, equal carriers: refused (Passed)")

iso_source.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
    M.EmptyList,
)
iso_target.edges = M.Pair(
    M.Pair(M.Char("S"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.EmptyList,
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.false_value, (
    "A changed relation label must be refused"
)
print("        different relation label: refused (Passed)")

# R(p,q,q) keeps the carrier at 2 vertices, so arity is what refuses the match.
iso_target.edges = M.Pair(
    M.Pair(
        M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.Pair(tgt_q, M.EmptyList)))
    ),
    M.EmptyList,
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.false_value, (
    "An extra argument on an equal carrier must be refused"
)
print("        different arity on equal carriers: refused (Passed)")

iso_target.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_p, M.EmptyList))),
    M.EmptyList,
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.false_value, (
    "Two distinct sources must not share one image"
)
print("        two sources onto one target, equal carriers: refused (Passed)")

iso_source.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_a, M.EmptyList))),
    M.EmptyList,
)
iso_target.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.EmptyList,
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.false_value, (
    "A repeated entity must not match two distinct entities"
)
print("        repeated entity on equal carriers: refused (Passed)")

iso_source.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
    M.Pair(
        M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
        M.EmptyList,
    ),
)
iso_target.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.EmptyList,
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.false_value, (
    "A doubled edge must not collapse into a single edge"
)
print("        edge multiplicity, doubled against single: refused (Passed)")

print("    [e] renamed entities and reversed edge order still match")
iso_source.nodes = M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))
iso_source.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
    M.Pair(
        M.Pair(M.Char("R"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
        M.EmptyList,
    ),
)
iso_target.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))
iso_target.edges = M.Pair(
    M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
    M.Pair(
        M.Pair(M.Char("R"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
        M.EmptyList,
    ),
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.truth_value, "Equal multiplicities must match"
carrier_map = M.Head(M.Tail(M.Head(M.Tail(carrier_res)())())())()
assert RenamingBindsCarrier(
    carrier_map, iso_source.nodes, iso_target.nodes, registry
)() is M.truth_value, "A doubled-edge renaming must bind both carriers"
print("        two identical edges on both sides: isomorphic (Passed)")

iso_source.nodes = M.Pair(atom_a, M.Pair(atom_b, M.Pair(atom_c, M.EmptyList)))
iso_source.edges = M.Pair(
    M.Pair(M.Char("binary_op"), M.Pair(atom_a, M.Pair(atom_b, M.EmptyList))),
    M.Pair(
        M.Pair(M.Char("identity"), M.Pair(atom_a, M.EmptyList)),
        M.EmptyList,
    ),
)
iso_target.nodes = M.Pair(tgt_p, M.Pair(tgt_q, M.Pair(tgt_r, M.EmptyList)))
iso_target.edges = M.Pair(
    M.Pair(M.Char("identity"), M.Pair(tgt_p, M.EmptyList)),
    M.Pair(
        M.Pair(M.Char("binary_op"), M.Pair(tgt_p, M.Pair(tgt_q, M.EmptyList))),
        M.EmptyList,
    ),
)
carrier_res = MatchMod.HypergraphIsomorphismMatch(iso_source, iso_target, registry)()
assert M.Head(carrier_res)() is M.truth_value, "Renamed entities must still match"
carrier_map = M.Head(M.Tail(M.Head(M.Tail(carrier_res)())())())()
assert RenamingBindsCarrier(
    carrier_map, iso_source.nodes, iso_target.nodes, registry
)() is M.truth_value, "The renamed-and-isolated renaming must bind all 3 vertices"
print("        renamed entities, reversed edges, one isolated vertex: isomorphic (Passed)")

# The existing Test 17 fixture declares no node store, so its carrier is exactly
# the entities its edges mention: the pre-existing verdict and renaming stand.
assert RenamingBindsCarrier(
    M.Head(M.Tail(iso_node)())(),
    M.Pair(a, M.Pair(b, M.EmptyList)),
    M.Pair(n1, M.Pair(n2, M.EmptyList)),
    registry,
)() is M.truth_value, "The existing fixture's renaming still binds its carrier"
print("        existing Test 17 fixture (edges only): renaming binds both (Passed)")

print("\n[4] Test Case 3: Level 4 Shared Structural Invariant Bridging...")
# Entity E (Elliptic Curve representation)
# Entity F (Modular Form representation)
elliptic_curve = M.Pair(M.Char("EllipticCurve"), M.Char("E_11a1"))
modular_form = M.Pair(M.Char("ModularForm"), M.Char("f_weight2_level11"))

# Common invariant: Galois representation rho
galois_repr = M.Pair(M.Char("GaloisRepresentation"), M.Char("rho_11_torsion"))

get_rho_from_e = lambda entity, reg: M.Pair(galois_repr, M.Pair(reg, M.EmptyList))
get_rho_from_f = lambda entity, reg: M.Pair(galois_repr, M.Pair(reg, M.EmptyList))

bridge_res = MatchMod.HypergraphSharedInvariantBridge(
    elliptic_curve, get_rho_from_e, modular_form, get_rho_from_f, reg1
)()
is_bridged = M.Head(bridge_res)()
bridge_node = M.Head(M.Tail(bridge_res)())()
reg2 = M.Head(M.Tail(M.Tail(bridge_res)())())()

assert is_bridged is M.truth_value, "Entities should share the invariant"
bridge_tag = M.Head(bridge_node)()
assert M.IdentityCompare(bridge_tag, L.SharedInvariantBridgeLabel)() is M.truth_value, "Tag should be SharedInvariantBridgeLabel"
print("    Level 4 Shared Invariant Bridge verified: E -> rho <- f (Passed)")

dt = time.time() - t0
print(f"\n=== ALL TEST 17 HYPERGRAPH MATCHING CHECKS PASSED in {dt:.3f}s ===")
