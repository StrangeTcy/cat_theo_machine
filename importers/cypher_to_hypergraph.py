"""Import a decoded Neo4j cypher export into a Machine hypergraph snapshot.

The other decoded shape `neo4j-admin` dumps land in, once restored, is
`apoc.export.cypher.all(..., {format:"cypher-shell"})`: a script of CREATE and
MERGE statements rather than node and relationship tables. This module parses
that subset and hands the result to `csv_to_hypergraph.build_terms`, so there is
exactly one path from decoded export to Machine terms -- the two importers
cannot drift apart in how they represent a node or an edge.

Parsing is host-layer text handling over a file, where the Machine has no
analogue, so regular expressions are the right tool here and purity is not
engaged. Term construction is delegated, and that is where purity binds.

Supported statement shapes, which is what apoc emits for a whole database:

    CREATE (n42:Person:Author {id: 42, name: 'Ada'});
    MERGE (n42:Person {id: 42});
    MATCH (n42:Person {id: 42}), (n7:House {id: 7})
      CREATE (n42)-[:LIVES_IN {since: 1843}]->(n7);

A node's Machine symbol is its variable reference (`n42`), which apoc keeps
stable across the whole script, so relationship endpoints resolve without a
second pass. Labels and properties become hyperedges exactly as in the CSV
importer: `(label, node, value)` and `(key, node, value)`, one whole string per
`Char`, so every property stays `Compare`-accessible.

Caveat worth stating plainly: this was written and tested against apoc's
documented output shape, not against a real export, because this sandbox has no
route to neo4j.com and no Neo4j to run one. Validate it on the first few
thousand lines of a real export before trusting a full run, and expect to extend
`_split_statements` if the export uses `:begin`/`:commit` batching, which
cypher-shell format does emit and which is skipped here as a comment line.

Usage:
    python -m importers.cypher_to_hypergraph EXPORT.cypher OUT.json
"""

import os
import re
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ROOT))

from cat_theo_machine import machine as M
from cat_theo_machine import main as _Main
from cat_theo_machine import runtime as _Runtime
from cat_theo_machine.importers import csv_to_hypergraph as _Csv

NODE_HEAD = re.compile(r"\(\s*([A-Za-z_][A-Za-z0-9_]*)((?::[A-Za-z_][A-Za-z0-9_]*)*)\s*(\{[^}]*\})?\s*\)")
RELATION = re.compile(
    r"\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*-\s*\[\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*(\{[^}]*\})?\s*\]\s*->\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)"
)
PROPERTY = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|-?[0-9][0-9.]*)")


def unquote(text):
    if len(text) < 2:
        return text
    first = text[0]
    last = text[len(text) - 1]
    if first != last:
        return text
    if first != "'" and first != '"':
        return text
    return text[1:len(text) - 1]


def properties_of(blob):
    """A property map from a `{k: v, ...}` blob, values as plain strings."""
    rows = []
    if blob is None:
        return rows
    for match in PROPERTY.finditer(blob):
        rows.append((match.group(1), unquote(match.group(2))))
    return rows


def split_statements(text):
    """Split a cypher script on semicolons that are not inside a quoted string."""
    statements = []
    current = ""
    quote = ""
    index = 0
    limit = len(text)
    while index < limit:
        char = text[index]
        if quote == "":
            if char == "'" or char == '"':
                quote = char
            elif char == ";":
                statements.append(current)
                current = ""
                index += 1
                continue
            elif char == "/" and index + 1 < limit and text[index + 1] == "/":
                while index < limit and text[index] != "\n":
                    index += 1
                continue
        else:
            if char == "\\":
                current += char
                index += 1
                if index < limit:
                    current += text[index]
                    index += 1
                continue
            if char == quote:
                quote = ""
        current += char
        index += 1
    if current.strip() != "":
        statements.append(current)
    return statements


def parse(text):
    """Parse a cypher script into the CSV importer's row shapes.

    A statement may carry both a relationship and the node heads that introduce
    its endpoints -- apoc emits `MATCH (a:X {..}), (b:Y {..}) CREATE (a)-[..]->(b)`
    -- so both are parsed from the same statement. Skipping the node heads there
    would leave every such endpoint dangling: an edge naming a node the nodes
    chain never contains.
    """
    node_rows = []
    edge_rows = []
    seen_nodes = {}
    for statement in split_statements(text):
        upper = statement.upper()
        relation = RELATION.search(statement)
        if relation is not None:
            source = relation.group(1)
            target = relation.group(4)
            edge_rows.append({
                "src": source,
                "rel": relation.group(2),
                "dst": target,
            })
            for key, value in properties_of(relation.group(3)):
                edge_rows.append({
                    "src": source,
                    "rel": relation.group(2) + ":" + key,
                    "dst": value,
                })
        elif upper.find("CREATE") == -1 and upper.find("MERGE") == -1:
            continue
        for match in NODE_HEAD.finditer(statement):
            reference = match.group(1)
            if reference in seen_nodes:
                continue
            labels = match.group(2)
            row = {"id": reference}
            first_label = ""
            if labels != "":
                first_label = labels.split(":")[1]
            row["label"] = first_label
            for key, value in properties_of(match.group(3)):
                # `id` is the node identity key the CSV importer's contract
                # reserves for the reference. Letting apoc's own `id: 42`
                # property occupy it silently renames every node to a number
                # while relationship endpoints keep naming the reference, which
                # disconnects the graph without any error. Keep it, renamed.
                if key == "id":
                    row["neo4j_id"] = value
                    continue
                row[key] = value
            seen_nodes[reference] = row
            node_rows.append(row)
    return node_rows, edge_rows


def main():
    argv = sys.argv
    if len(argv) != 3:
        print("usage: cypher_to_hypergraph EXPORT.cypher OUT.json")
        return 1
    handle = open(argv[1], "r", encoding="utf-8")
    try:
        text = handle.read()
    finally:
        handle.close()

    node_rows, edge_rows = parse(text)
    started = time.monotonic()
    runtime, _packs = _Runtime.boot_from_packs(
        _Main.PACK_PATHS, _Main._runtime_namespace()
    )
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    nodes, edges = _Csv.build_terms(node_rows, edge_rows)
    graph._replace_context(nodes=nodes, edges=edges)
    built = time.monotonic()
    _Runtime.save_runtime(runtime, argv[2], _Main._runtime_namespace())
    saved = time.monotonic()
    print(
        "IMPORT-CYPHER statements=%d nodes=%s edges=%s bytes=%d build=%.2fs save=%.2fs"
        % (
            len(split_statements(text)),
            _Csv.count_text(nodes, registry),
            _Csv.count_text(edges, registry),
            os.path.getsize(argv[2]),
            built - started,
            saved - built,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
