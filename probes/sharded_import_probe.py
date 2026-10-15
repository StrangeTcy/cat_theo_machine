"""Regression probe: a sharded import yields shards that each stand alone.

The scale ladder located the ingest ceiling in memory, roughly 10KB of resident
set per edge, so a large foreign graph has to arrive as several snapshots rather
than one. Sharding is only correct if each shard is self-sufficient, and that is
not something a count can show: the first sharded run produced plausible counts
per shard while the interesting question -- whether an edge whose endpoints were
declared under different labels still resolves -- was untested.

So this probe builds a fixture whose 300 relationships deliberately cross all
three labels, imports it, and then for every shard, separately:

  * boots the shard snapshot on its own, with no other shard present;
  * checks the machine-counted nodes and edges against the manifest's own text;
  * walks every `links` edge and confirms BOTH endpoints occur in that shard's
    nodes chain, counting any that do not as dangling.

A shard with a dangling edge would boot happily and simply contain a relationship
naming a node that is not there, which is exactly the silent failure the cypher
importer's `id` collision produced.

Usage:
    python probes/sharded_import_probe.py [MAX_NODES_PER_SHARD]

With no argument the fixture shards by label alone into three shards. With a cap
each label is bucketed, which is the mode a real dump needs: a heterogeneous
export is usually dominated by one label, and one shard holding nearly
everything meets the same cliff the monolith did.
"""

import json
import os
import shutil
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

IMPORTER = os.path.join(_ROOT, "importers", "sharded_import.py")
PER_LABEL = 20
LABELS = ("Person", "House", "Note")
PREFIXES = ("p", "h", "t")
RELATIONS = 300


def count_of(chain, registry):
    return M.Head(M.NatFromRep(M.CountRep(chain)(), registry)())()


def count_text(chain, registry):
    return M.GMPRepText(M.NatRepOf(count_of(chain, registry), registry)())()


def nat_from_host(value, registry):
    return M.Head(M.NatFromRep(M.GMPRep(value), registry)())()


def write_fixture(directory):
    references = []
    for prefix in PREFIXES:
        index = 0
        while index < PER_LABEL:
            references.append(prefix + str(index))
            index += 1

    node_path = os.path.join(directory, "nodes.csv")
    handle = open(node_path, "w", encoding="utf-8")
    try:
        handle.write("id,label,note\n")
        label_index = 0
        while label_index < len(LABELS):
            index = 0
            while index < PER_LABEL:
                handle.write("%s%d,%s,%s-note-%d\n" % (
                    PREFIXES[label_index], index, LABELS[label_index],
                    PREFIXES[label_index], index))
                index += 1
            label_index += 1
    finally:
        handle.close()

    edge_path = os.path.join(directory, "edges.csv")
    handle = open(edge_path, "w", encoding="utf-8")
    try:
        handle.write("src,rel,dst\n")
        index = 0
        total = len(references)
        while index < RELATIONS:
            handle.write("%s,links,%s\n" % (
                references[index % total],
                references[(index * 13) % total]))
            index += 1
    finally:
        handle.close()
    return node_path, edge_path


def main():
    argv = sys.argv
    cap = 0
    if len(argv) > 1:
        cap = int(argv[1])
    failures = 0
    work = tempfile.mkdtemp(prefix="shard-probe-")
    node_csv, edge_csv = write_fixture(work)
    outdir = os.path.join(work, "shards")

    command = [sys.executable, IMPORTER, node_csv, edge_csv, outdir]
    if cap > 0:
        command.append(str(cap))
    started = time.monotonic()
    proc = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        print("IMPORT FAILED rc=%d" % proc.returncode)
        print(proc.stdout)
        return 1
    imported = time.monotonic()

    handle = open(os.path.join(outdir, "manifest.json"), encoding="utf-8")
    try:
        manifest = json.load(handle)
    finally:
        handle.close()

    expected_shards = len(LABELS)
    if cap > 0:
        buckets = (PER_LABEL + cap - 1) // cap
        expected_shards = len(LABELS) * buckets
    expected_nodes = PER_LABEL * len(LABELS)
    manifest_checks = (
        ("shards", len(manifest["shards"]), expected_shards),
        ("source_nodes", manifest["source_nodes"], expected_nodes),
        ("source_edges", manifest["source_edges"], RELATIONS),
        ("undeclared_sources", manifest["edges_with_undeclared_source"], 0),
    )
    for name, actual, expected in manifest_checks:
        if actual == expected:
            print("PASS manifest_%s=%d" % (name, actual))
        else:
            failures += 1
            print("FAIL manifest_%s expected %d got %d" % (name, expected, actual))
    if manifest["cross_shard_edges"] > 0:
        print("PASS manifest_cross_shard_edges=%d" % manifest["cross_shard_edges"])
    else:
        failures += 1
        print("FAIL manifest_cross_shard_edges: fixture produced no crossing edges")

    links_symbol = M.Char("links")
    verified = time.monotonic()
    for entry in manifest["shards"]:
        runtime = _Runtime.boot_from_snapshot(
            os.path.join(outdir, entry["file"]), _Main._runtime_namespace()
        )
        graph = runtime.graph
        registry = M.FromContextGetConstructors(graph)()

        link_edges = M.EmptyList
        dangling = M.EmptyList
        cursor = graph.edges
        while (
            M.IdentityCompare(cursor, M.EmptyList)() is M.false_value
            and M.IsPair(cursor)() is M.truth_value
        ):
            candidate = M.Head(cursor)()
            if M.Compare(M.Head(candidate)(), links_symbol)() is M.truth_value:
                link_edges = M.Pair(candidate, link_edges)
                first = M.Head(M.Tail(candidate)())()
                second = M.Head(M.Tail(M.Tail(candidate)())())()
                have_first = M.false_value
                have_second = M.false_value
                node_cursor = graph.nodes
                while (
                    M.IdentityCompare(node_cursor, M.EmptyList)() is M.false_value
                    and M.IsPair(node_cursor)() is M.truth_value
                ):
                    node = M.Head(node_cursor)()
                    if M.Compare(node, first)() is M.truth_value:
                        have_first = M.truth_value
                    if M.Compare(node, second)() is M.truth_value:
                        have_second = M.truth_value
                    node_cursor = M.Tail(node_cursor)()
                if have_first is M.false_value or have_second is M.false_value:
                    dangling = M.Pair(candidate, dangling)
            cursor = M.Tail(cursor)()

        shard_nodes = count_text(graph.nodes, registry)
        shard_edges = count_text(graph.edges, registry)
        if shard_nodes == entry["nodes"] and shard_edges == entry["edges"]:
            print("PASS shard_%s_manifest_agrees nodes=%s edges=%s"
                  % (entry["shard"], shard_nodes, shard_edges))
        else:
            failures += 1
            print("FAIL shard_%s_manifest_agrees nodes=%s/%s edges=%s/%s" % (
                entry["shard"], shard_nodes, entry["nodes"],
                shard_edges, entry["edges"]))

        if M.IdentityCompare(dangling, M.EmptyList)() is M.truth_value:
            print("PASS shard_%s_no_dangling links=%s"
                  % (entry["shard"], count_text(link_edges, registry)))
        else:
            failures += 1
            print("FAIL shard_%s_no_dangling dangling=%s links=%s" % (
                entry["shard"], count_text(dangling, registry),
                count_text(link_edges, registry)))
        del runtime

    shutil.rmtree(work, ignore_errors=True)
    print(
        "import %.2fs verify %.2fs failures=%d"
        % (imported - started, time.monotonic() - verified, failures),
        flush=True,
    )
    return failures


if __name__ == "__main__":
    sys.exit(main())
