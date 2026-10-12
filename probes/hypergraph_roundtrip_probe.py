"""Round-trip probe for imported (non-mathematical) hypergraph content.

Question it answers: if foreign data (city-house facts, personal notes, anything
that is not a proof) is poured into the graph as Machine terms, does a snapshot
save/restore keep it?  Historically no: SnapshotCodec.capture() had no root for
graph.nodes / graph.edges, so the hypergraph came back empty while the kernel
(rules, schemata, derivations, search memo) round-tripped fine.

The probe also exercises the text encoding used for long strings: a whole note
is carried by a single Char atom instead of one atom per character.

Chain lengths are counted with Peano Succ and rendered through the machine's own
GMPRep/NatRepOf/GMPRepText path, and edges are found with Compare rather than by
reading a payload attribute, per SWARM_EVOLUTION_DAG.md 5.2: the host layer may
use Python natives only where the machine has no analogue, and here it has one.

Usage (either form works):
    python -m cat_theo_machine.probes.hypergraph_roundtrip_probe build [path]
    python probes/hypergraph_roundtrip_probe.py check [path]

build -- boots the packs, adds house/person/note facts, saves a snapshot.
check -- boots that snapshot in a fresh process and reports what survived.
"""

import os
import sys
import time

PROBE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_PARENT = os.path.dirname(os.path.dirname(PROBE_DIR))
if PACKAGE_PARENT not in sys.path:
    sys.path.insert(0, PACKAGE_PARENT)

from cat_theo_machine import machine as M
from cat_theo_machine import main as _Main
from cat_theo_machine import runtime as _Runtime

NOTE_TEXT = (
    "Canal house rebuilt after the fire of 1763; deed in the city archive. "
    "Café — голландский перевод; 100% legible."
)
DEFAULT_PATH = "/tmp/hypergraph_roundtrip.json"


def count_chain(chain, registry):
    """Length of a machine pair chain as a Peano natural."""
    count = M.Zero
    cursor = chain
    while (
        M.IdentityCompare(cursor, M.EmptyList)() is M.false_value
        and M.IsPair(cursor)() is M.truth_value
    ):
        count = M.Head(M.Succ(count, registry)())()
        cursor = M.Tail(cursor)()
    return count


def count_text(chain, registry):
    """The same length as printable text, via the machine's own rep rendering."""
    rep = M.NatRepOf(count_chain(chain, registry), registry)()
    return M.GMPRepText(rep)()


def nat_at(value, registry):
    """Build a Peano natural from a host integer, via the machine's own
    NatFromRep rather than a Python loop over Succ. NatFromRep returns
    Pair(nat, Pair(registry, EmptyList)) -- the same wrapper convention as
    Succ -- so the nat itself is the Head."""
    return M.Head(M.NatFromRep(M.GMPRep(value), registry)())()


def report(graph, registry, label, started):
    print(
        "%s nodes=%s edges=%s rules=%s elapsed=%.2fs"
        % (
            label,
            count_text(graph.nodes, registry),
            count_text(graph.edges, registry),
            count_text(graph.rule_order, registry),
            time.monotonic() - started,
        ),
        flush=True,
    )


def build(path):
    started = time.monotonic()
    runtime, packs = _Runtime.boot_from_packs(
        _Main.PACK_PATHS, _Main._runtime_namespace()
    )
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    edge_symbol = M.Char("lives_in")
    note_symbol = M.Char("house_note")
    nodes = M.EmptyList
    edges = M.EmptyList
    for index in range(3):
        person = M.Char("person-%d" % index)
        house = M.Char("house-%d" % index)
        nodes = M.Pair(person, M.Pair(house, nodes))
        edges = M.Pair(
            M.Pair(edge_symbol, M.Pair(person, M.Pair(house, M.EmptyList))),
            edges,
        )
    edges = M.Pair(
        M.Pair(
            note_symbol,
            M.Pair(M.Char("house-0"), M.Pair(M.Char(NOTE_TEXT), M.EmptyList)),
        ),
        edges,
    )
    graph._replace_context(nodes=nodes, edges=edges)
    _Runtime.save_runtime(runtime, path, _Main._runtime_namespace())
    report(graph, registry, "BUILD", started)
    print(
        "BUILD snapshot bytes=%d" % os.path.getsize(path),
        flush=True,
    )


def check(path):
    started = time.monotonic()
    runtime = _Runtime.boot_from_snapshot(path, _Main._runtime_namespace())
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    report(graph, registry, "CHECK", started)

    # Find the note edge with Compare: it is structural, so it matches the
    # interned Char. IdentityCompare against a freshly built Char never does,
    # and reading .symbol would bypass a predicate the machine provides.
    note = M.EmptyList
    found_note = M.false_value
    cursor = graph.edges
    while (
        M.IdentityCompare(cursor, M.EmptyList)() is M.false_value
        and M.IsPair(cursor)() is M.truth_value
    ):
        candidate = M.Head(cursor)()
        if M.Compare(M.Head(candidate)(), note_symbol_of())() is M.truth_value:
            note = M.Head(M.Tail(M.Tail(candidate)())())()
            found_note = M.truth_value
        cursor = M.Tail(cursor)()

    note_is_atom = M.false_value
    if found_note is M.truth_value:
        note_is_atom = M.IsAtom(note, registry)()
    note_intact = M.false_value
    if found_note is M.truth_value:
        note_intact = M.Compare(note, M.Char(NOTE_TEXT))()
    print(
        "CHECK note found=%s atom=%s intact=%s"
        % (
            found_note is M.truth_value,
            note_is_atom is M.truth_value,
            note_intact is M.truth_value,
        ),
        flush=True,
    )

    nodes_expected = nat_at(6, registry)
    edges_expected = nat_at(4, registry)
    nodes_ok = M.NatEq(count_chain(graph.nodes, registry), nodes_expected, registry)()
    edges_ok = M.NatEq(count_chain(graph.edges, registry), edges_expected, registry)()
    print(
        "CHECK counts nodes_expected=%s edges_expected=%s both_ok=%s"
        % (
            M.GMPRepText(M.NatRepOf(nodes_expected, registry)())(),
            M.GMPRepText(M.NatRepOf(edges_expected, registry)())(),
            nodes_ok is M.truth_value and edges_ok is M.truth_value,
        ),
        flush=True,
    )
    if nodes_ok is M.false_value or edges_ok is M.false_value:
        print(
            "CHECK FAILED: hypergraph content did not survive the snapshot",
            flush=True,
        )
        raise SystemExit(1)
    sample = M.Head(graph.edges)()
    print("CHECK sample=%s" % M.PrettyTerm(sample, registry)(), flush=True)


def note_symbol_of():
    return M.Char("house_note")


def main():
    mode = "build"
    path = DEFAULT_PATH
    index = 0
    for arg in sys.argv:
        if index == 1:
            mode = arg
        if index == 2:
            path = arg
        index = index + 1
    if mode == "build":
        build(path)
    elif mode == "check":
        check(path)
    else:
        raise SystemExit(
            "usage: hypergraph_roundtrip_probe.py [build|check] [path]"
        )


if __name__ == "__main__":
    main()
