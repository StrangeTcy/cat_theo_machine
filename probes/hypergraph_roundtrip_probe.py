"""Round-trip probe for imported (non-mathematical) hypergraph content.

Question it answers: if foreign data (city-house facts, personal notes, anything
that is not a proof) is poured into the graph as Machine terms, does a snapshot
save/restore keep it?  Historically no: SnapshotCodec.capture() had no root for
graph.nodes / graph.edges, so the hypergraph came back empty while the kernel
(rules, schemata, derivations, search memo) round-tripped fine.

The probe also exercises the text encoding used for long strings: a whole note
is carried by a single Char atom instead of one atom per character.

Usage (either form works):
    python -m <pkg>.probes.hypergraph_roundtrip_probe build [path]
    python probes/hypergraph_roundtrip_probe.py check [path]

build -- boots the arithmetic pack, adds house/person/note facts, saves snapshot.
check -- boots that snapshot in a fresh process and reports what survived.
"""

import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_NAME = os.path.basename(os.path.dirname(_HERE))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)


def _load(name):
    return __import__(_PKG_NAME + "." + name, fromlist=[name])


M = _load("machine")
_Runtime = _load("runtime")
_Main = _load("main")

NOTE_TEXT = (
    "Canal house rebuilt after the fire of 1763; deed in the city archive. "
    "Café — голландский перевод; 100% legible."
)


def chain_len(x, M):
    count = 0
    while M.IdentityCompare(x, M.EmptyList)() is M.false_value and M.IsPair(x)() is M.truth_value:
        count += 1
        x = M.Tail(x)()
    return count


def build(path):
    runtime, packs = _Runtime.boot_from_packs([_Main.PACK_PATHS[6]], _Main._runtime_namespace())
    graph = runtime.graph
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
        M.Pair(note_symbol, M.Pair(M.Char("house-0"), M.Pair(M.Char(NOTE_TEXT), M.EmptyList))),
        edges,
    )
    graph._replace_context(nodes=nodes, edges=edges)
    started = time.monotonic()
    _Runtime.save_runtime(runtime, path, _Main._runtime_namespace())
    print(
        "BUILD nodes=%d edges=%d rules=%d save=%.2fs size=%.1fMB"
        % (
            chain_len(nodes, M),
            chain_len(edges, M),
            chain_len(graph.rule_order, M),
            time.monotonic() - started,
            os.path.getsize(path) / 1e6,
        ),
        flush=True,
    )


def check(path):
    started = time.monotonic()
    runtime = _Runtime.boot_from_snapshot(path, _Main._runtime_namespace())
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    edges = graph.edges
    note = None
    cursor = edges
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value and M.IsPair(cursor)() is M.truth_value:
        candidate = M.Head(cursor)()
        symbol = getattr(M.Head(candidate)(), "symbol", None)
        if symbol == "house_note":
            note = M.Head(M.Tail(M.Tail(candidate)())())()
        cursor = M.Tail(cursor)()
    print(
        "CHECK nodes=%d edges=%d rules=%d load=%.2fs"
        % (
            chain_len(graph.nodes, M),
            chain_len(graph.edges, M),
            chain_len(graph.rule_order, M),
            time.monotonic() - started,
        ),
        flush=True,
    )
    print("CHECK note type=%s len=%d intact=%s" % (
        type(note).__name__,
        len(note.symbol) if note is not None else -1,
        note is not None and note.symbol == NOTE_TEXT,
    ), flush=True)
    if chain_len(graph.nodes, M) == 0:
        print("CHECK FAILED: hypergraph content did not survive the snapshot", flush=True)
        raise SystemExit(1)
    sample = M.Head(graph.edges)()
    print("CHECK sample=%s" % M.PrettyTerm(sample, registry)(), flush=True)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/hypergraph_roundtrip.json"
    if mode == "build":
        build(path)
    elif mode == "check":
        check(path)
    else:
        raise SystemExit("usage: hypergraph_roundtrip_probe.py [build|check] [path]")


if __name__ == "__main__":
    main()
