"""Regression probe: CSV import to snapshot and back, at scale.

Proves the importer's output restores with every node, every relationship and
every property edge intact -- the evidence that previously lived only in a
throwaway harness under /tmp, which sandbox rebuilds wipe.

Usage:
    python probes/importer_roundtrip_probe.py [RELATIONS]
"""

import os
import subprocess
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ROOT))

from cat_theo_machine import machine as M
from cat_theo_machine import main as _Main
from cat_theo_machine import runtime as _Runtime
from cat_theo_machine.importers import csv_to_hypergraph as _Importer

IMPORTER = os.path.join(_ROOT, "importers", "csv_to_hypergraph.py")


def nat_from_host(value, registry):
    """A machine nat for a host integer, unwrapped from NatFromRep's Pair."""
    return M.Head(M.NatFromRep(M.GMPRep(value), registry)())()


def count_of(chain, registry):
    return M.Head(M.NatFromRep(M.CountRep(chain)(), registry)())()


def write_csv(path, header, rows):
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(header)
        for row in rows:
            handle.write(row)
    finally:
        handle.close()


def main():
    argv = sys.argv
    relations = 20000
    if len(argv) > 1:
        relations = int(argv[1])
    nodes = relations // 10

    node_rows = []
    for index in range(nodes):
        node_rows.append("n%d,Person,note-%d\n" % (index, index))
    edge_rows = []
    for index in range(relations):
        edge_rows.append("n%d,lives_in,n%d\n" % (index % nodes, (index * 7) % nodes))

    work = tempfile.mkdtemp(prefix="importer-probe-")
    failures = 0

    # Both header conventions must canonicalise to the same roles, and this is
    # checked before the expensive part: apoc.export.csv.all writes _id:ID,
    # _labels, _start:START_ID, _end:END_ID and _type, while a hand-rolled export
    # writes id, label, src, rel and dst. Guessing one convention silently breaks
    # the other -- and a header mismatch does not fail loudly, it imports a graph
    # whose edges name nodes that were never registered.
    apoc_nodes = os.path.join(work, "apoc_nodes.csv")
    apoc_edges = os.path.join(work, "apoc_edges.csv")
    write_csv(apoc_nodes, "_id:ID,_labels,name\n", ["7,:Person:Author,Ada\n"])
    write_csv(
        apoc_edges,
        "_id:REL,_start:START_ID,_end:END_ID,_type,since\n",
        ["99,7,3,LIVES_IN,1843\n"],
    )
    mapped_nodes = _Importer.read_node_rows(apoc_nodes)
    mapped_edges = _Importer.read_edge_rows(apoc_edges)
    header_checks = (
        ("node_identity", mapped_nodes[0].get("id"), "7"),
        ("node_label", mapped_nodes[0].get("label"), ":Person:Author"),
        ("node_property_kept", mapped_nodes[0].get("name"), "Ada"),
        ("edge_start", mapped_edges[0].get("src"), "7"),
        ("edge_end", mapped_edges[0].get("dst"), "3"),
        ("edge_type", mapped_edges[0].get("rel"), "LIVES_IN"),
        ("edge_property_expanded", mapped_edges[1].get("rel"), "LIVES_IN:since"),
        ("edge_property_value", mapped_edges[1].get("dst"), "1843"),
    )
    for name, actual, expected in header_checks:
        if actual == expected:
            print("PASS header_%s" % name)
        else:
            failures += 1
            print("FAIL header_%s expected %s got %s" % (name, expected, actual))

    node_csv = os.path.join(work, "nodes.csv")
    edge_csv = os.path.join(work, "edges.csv")
    snapshot = os.path.join(work, "imported.json")
    write_csv(node_csv, "id,label,note\n", node_rows)
    write_csv(edge_csv, "src,rel,dst\n", edge_rows)

    started = time.monotonic()
    proc = subprocess.run(
        [sys.executable, IMPORTER, node_csv, edge_csv, snapshot],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        print("IMPORT FAILED rc=%d" % proc.returncode)
        print(proc.stdout)
        return 1
    imported = time.monotonic()

    runtime = _Runtime.boot_from_snapshot(snapshot, _Main._runtime_namespace())
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    loaded = time.monotonic()

    relation_symbol = M.Char("lives_in")
    label_symbol = M.Char("label")
    relations_found = M.EmptyList
    properties_found = M.EmptyList
    cursor = graph.edges
    while (
        M.IdentityCompare(cursor, M.EmptyList)() is M.false_value
        and M.IsPair(cursor)() is M.truth_value
    ):
        candidate = M.Head(cursor)()
        head = M.Head(candidate)()
        if M.Compare(head, relation_symbol)() is M.truth_value:
            relations_found = M.Pair(candidate, relations_found)
        if M.Compare(head, label_symbol)() is M.truth_value:
            properties_found = M.Pair(candidate, properties_found)
        cursor = M.Tail(cursor)()

    checks = (
        ("nodes", count_of(graph.nodes, registry), nodes),
        ("edges", count_of(graph.edges, registry), relations + nodes + nodes),
        ("lives_in", count_of(relations_found, registry), relations),
        ("label_props", count_of(properties_found, registry), nodes),
    )
    for name, counted, expected in checks:
        agreed = M.NatEq(counted, nat_from_host(expected, registry), registry)()
        if agreed is M.truth_value:
            print("PASS %s=%s" % (name, M.GMPRepText(M.NatRepOf(counted, registry)())()))
        else:
            failures += 1
            print("FAIL %s expected %d" % (name, expected))

    print(
        "import %.2fs load %.2fs bytes=%d failures=%d"
        % (imported - started, loaded - imported, os.path.getsize(snapshot), failures),
        flush=True,
    )
    return failures


if __name__ == "__main__":
    sys.exit(main())
