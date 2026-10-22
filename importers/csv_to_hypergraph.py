"""Import a decoded Neo4j export (CSV) into a Machine hypergraph snapshot.

Input is the shape `apoc.export.csv.all` produces once a dump has been
restored: a node file and a relationship file. This module turns them into
Machine terms -- named `Char` nodes, `Pair(rel, Pair(a, Pair(b, EmptyList)))`
hyperedges -- stores them under the `nodes`/`edges` roots, and persists the
result with `save_runtime`, so the output restores exactly like any other
snapshot.

Node properties become hyperedges rather than nested structure: a whole
property string goes into one `Char`, keyed `(label:prop, node, value)`. That
keeps every property reasoning-accessible to `Compare` without inventing a
record shape the Machine has no predicate for.

Usage:
    python -m importers.csv_to_hypergraph NODES.csv EDGES.csv OUT.json
"""

import csv
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_PARENT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _PACKAGE_PARENT)

from cat_theo_machine import machine as M
from cat_theo_machine import main as _Main
from cat_theo_machine import runtime as _Runtime


def count_text(chain, registry):
    """Render a chain length as printable text using machine counting."""
    rep = M.CountRep(chain)()
    nat = M.NatFromRep(rep, registry)()
    return M.GMPRepText(M.NatRepOf(M.Head(nat)(), registry)())()


def read_rows(path):
    handle = open(path, "r", encoding="utf-8", newline="")
    try:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(row)
        return rows
    finally:
        handle.close()


# Header names accepted for each role. apoc.export.csv.all emits the `_id:ID` /
# `_labels` / `_start:START_ID` / `_end:END_ID` / `_type` family; the plain
# `id` / `label` / `src` / `rel` / `dst` names are kept because they are what a
# hand-rolled or cypher-shell-derived export uses, and because guessing one
# convention silently breaks the other. Comparison is case-insensitive: apoc
# writes the `:ID` and `:START_ID` qualifiers in upper case.
IDENTITY_HEADERS = ("id", "_id", "_id:id", "id:id", "_id:rel", "id:rel")
LABEL_HEADERS = ("label", "labels", "_labels", "_label", "_labels:label")
START_HEADERS = ("src", "start", "_start", "_start:start_id", "start_id", "from")
END_HEADERS = ("dst", "end", "_end", "_end:end_id", "end_id", "to")
TYPE_HEADERS = ("rel", "type", "_type", "rel_type", "_type:type", "relationship")


def role_of(name, wanted):
    lowered = name.lower()
    for candidate in wanted:
        if lowered == candidate:
            return True
    return False


def iter_rows(path):
    """Yield raw CSV rows one at a time, so callers never hold the file.

    A million-object export does not fit in memory as a list of dicts -- the
    measured ceiling is ~10KB of resident set per edge, and that is before the
    Machine terms exist. Everything downstream that has to scale streams from
    here.
    """
    handle = open(path, "r", encoding="utf-8", newline="")
    try:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row
    finally:
        handle.close()


def canonical_node_row(row):
    """One raw node row with identity and label columns canonicalised."""
    entry = {}
    for key in row:
        value = row[key]
        if role_of(key, IDENTITY_HEADERS):
            entry["id"] = value
            continue
        if role_of(key, LABEL_HEADERS):
            entry["label"] = value
            continue
        entry[key] = value
    return entry


def canonical_edge_rows(row):
    """One raw relationship row as a relationship plus one row per property.

    A relationship property column becomes its own hyperedge keyed
    `TYPE:column`, which is the same representation the cypher importer uses for
    `[:LIVES_IN {since: 1843}]`, so both decoded shapes land identically.
    """
    entry = {}
    properties = []
    for key in row:
        value = row[key]
        if role_of(key, START_HEADERS):
            entry["src"] = value
            continue
        if role_of(key, END_HEADERS):
            entry["dst"] = value
            continue
        if role_of(key, TYPE_HEADERS):
            entry["rel"] = value
            continue
        if role_of(key, IDENTITY_HEADERS):
            continue
        properties.append((key, value))
    rows = [entry]
    for key, value in properties:
        if value is None:
            continue
        if value == "":
            continue
        rows.append({
            "src": entry["src"],
            "rel": entry["rel"] + ":" + key,
            "dst": value,
        })
    return rows


def read_node_rows(path):
    """All node rows, canonicalised. Convenient, but holds the whole file."""
    rows = []
    for row in iter_rows(path):
        rows.append(canonical_node_row(row))
    return rows


def read_edge_rows(path):
    """All relationship rows, canonicalised and property-expanded."""
    rows = []
    for row in iter_rows(path):
        for expanded in canonical_edge_rows(row):
            rows.append(expanded)
    return rows


def build_terms(node_rows, edge_rows):
    """Fold CSV rows into the nodes chain and the edges chain."""
    nodes = M.EmptyList
    edges = M.EmptyList
    for row in node_rows:
        node_id = row["id"]
        symbol = M.Char(node_id)
        nodes = M.Pair(symbol, nodes)
        for key in row:
            if key == "id":
                continue
            value = row[key]
            if value is None:
                continue
            if value == "":
                continue
            edges = M.Pair(
                M.Pair(
                    M.Char(key),
                    M.Pair(symbol, M.Pair(M.Char(value), M.EmptyList)),
                ),
                edges,
            )
    for row in edge_rows:
        edges = M.Pair(
            M.Pair(
                M.Char(row["rel"]),
                M.Pair(
                    M.Char(row["src"]),
                    M.Pair(M.Char(row["dst"]), M.EmptyList),
                ),
            ),
            edges,
        )
    return nodes, edges


def main():
    argv = sys.argv
    if len(argv) != 4:
        print("usage: csv_to_hypergraph NODES.csv EDGES.csv OUT.json")
        return 1
    node_rows = read_node_rows(argv[1])
    edge_rows = read_edge_rows(argv[2])
    started = time.monotonic()
    runtime, _packs = _Runtime.boot_from_packs(
        _Main.PACK_PATHS, _Main._runtime_namespace()
    )
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    nodes, edges = build_terms(node_rows, edge_rows)
    graph._replace_context(nodes=nodes, edges=edges)
    built = time.monotonic()
    _Runtime.save_runtime(runtime, argv[3], _Main._runtime_namespace())
    saved = time.monotonic()
    print(
        "IMPORT nodes=%s edges=%s bytes=%d build=%.2fs save=%.2fs"
        % (
            count_text(nodes, registry),
            count_text(edges, registry),
            os.path.getsize(argv[3]),
            built - started,
            saved - built,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
