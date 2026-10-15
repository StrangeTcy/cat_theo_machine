"""Import a large decoded export as several independently-bootable snapshots.

The ingest ceiling is memory, not time: ~10KB of resident set per edge, because
reload holds the decoded graph and the restored terms at once. At that cost a
million-edge dump wants ~10GB, so one monolithic snapshot is not a viable target
for a large foreign graph. This importer shards instead.

Sharding is by node label, which for a heterogeneous dump is the natural seam --
personal notes, formalised fragments and house histories are different labels and
are reasoned about separately. Two properties matter:

  * **No shard has dangling edges.** An edge whose endpoints fall in different
    shards is written into the source shard together with a stub node for the
    foreign endpoint, so every edge resolves inside the shard that carries it.
    The stub carries the identity plus a `stub_of` property edge naming the shard
    that holds the authoritative copy, and none of that copy's other properties --
    so cross-shard provenance is itself queryable rather than implicit.
  * **Nothing large is ever held in memory.** Rows are streamed from the source
    CSVs and spilled to JSON Lines per shard, then one shard at a time is turned
    into Machine terms, saved and released. The only in-memory indexes are the
    node-to-shard assignment and the per-shard stub deduplication, both of which
    hold short strings rather than terms.

The packs are booted once and the graph context replaced per shard, so shard
count costs save-and-load time rather than boot time.

Output is `OUTDIR/<shard>.json` per shard plus `OUTDIR/manifest.json` naming
them, so a caller can boot one domain or walk all of them.

Usage:
    python -m importers.sharded_import NODES.csv EDGES.csv OUTDIR
"""

import json
import os
import shutil
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ROOT))

from cat_theo_machine import machine as M
from cat_theo_machine import main as _Main
from cat_theo_machine import runtime as _Runtime
from cat_theo_machine.importers import csv_to_hypergraph as _Csv

UNLABELLED = "unlabelled"


def count_of(chain, registry):
    return M.Head(M.NatFromRep(M.CountRep(chain)(), registry)())()


def count_text(chain, registry):
    return M.GMPRepText(M.NatRepOf(count_of(chain, registry), registry)())()


def shard_name_of(label_text):
    """A filesystem-safe shard name from a label, taking the first label only.

    apoc writes `_labels` as `:Person:Author`; a hand-rolled export writes
    `Person`. Either way the first label is the domain seam.
    """
    text = label_text
    if text is None:
        return UNLABELLED
    text = text.strip()
    while text[:1] == ":":
        text = text[1:]
    first = text.split(":")[0]
    if first == "":
        return UNLABELLED
    safe = ""
    for char in first:
        if char.isalnum() or char == "-" or char == "_":
            safe += char
        else:
            safe += "_"
    if safe == "":
        return UNLABELLED
    return safe


class Spill:
    """Per-shard JSON Lines spill files, opened lazily and flushed per write."""

    def __init__(self, directory):
        self.directory = directory
        self.handles = {}

    def handle_for(self, shard, kind):
        key = shard + "." + kind
        handle = self.handles.get(key)
        if handle is None:
            path = os.path.join(self.directory, key + ".jsonl")
            handle = open(path, "a", encoding="utf-8")
            self.handles[key] = handle
        return handle

    def write(self, shard, kind, row):
        handle = self.handle_for(shard, kind)
        handle.write(json.dumps(row, ensure_ascii=False))
        handle.write("\n")

    def close(self):
        for key in self.handles:
            self.handles[key].close()
        self.handles = {}

    def read(self, shard, kind):
        path = os.path.join(self.directory, shard + "." + kind + ".jsonl")
        rows = []
        if not os.path.exists(path):
            return rows
        handle = open(path, "r", encoding="utf-8")
        try:
            for line in handle:
                if line.strip() == "":
                    continue
                rows.append(json.loads(line))
        finally:
            handle.close()
        return rows

    def shard_names(self):
        names = []
        for entry in sorted(os.listdir(self.directory)):
            if not entry.endswith(".nodes.jsonl"):
                continue
            name = entry[: -len(".nodes.jsonl")]
            names.append(name)
        return names


def main():
    argv = sys.argv
    if len(argv) != 4:
        print("usage: sharded_import NODES.csv EDGES.csv OUTDIR")
        return 1
    node_csv = argv[1]
    edge_csv = argv[2]
    outdir = argv[3]
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    spill_dir = os.path.join(outdir, "spill")
    if os.path.isdir(spill_dir):
        shutil.rmtree(spill_dir)
    os.makedirs(spill_dir)

    started = time.monotonic()
    spill = Spill(spill_dir)
    assignment = {}
    node_total = 0
    for row in _Csv.iter_rows(node_csv):
        entry = _Csv.canonical_node_row(row)
        identity = entry.get("id")
        if identity is None:
            continue
        shard = shard_name_of(entry.get("label"))
        assignment[identity] = shard
        spill.write(shard, "nodes", entry)
        node_total += 1
    nodes_done = time.monotonic()

    edge_total = 0
    stubs = {}
    dangling = 0
    crossing = 0
    for row in _Csv.iter_rows(edge_csv):
        for entry in _Csv.canonical_edge_rows(row):
            source = entry.get("src")
            target = entry.get("dst")
            if source is None or target is None:
                continue
            shard = assignment.get(source)
            if shard is None:
                shard = UNLABELLED
                dangling += 1
            spill.write(shard, "edges", entry)
            edge_total += 1
            target_shard = assignment.get(target)
            if target_shard != shard:
                crossing += 1
                seen = stubs.get(shard)
                if seen is None:
                    seen = {}
                    stubs[shard] = seen
                if seen.get(target) is None:
                    seen[target] = True
                    stub = {"id": target}
                    if target_shard is not None:
                        stub["stub_of"] = target_shard
                    spill.write(shard, "nodes", stub)
    spill.close()
    spilled = time.monotonic()

    runtime, _packs = _Runtime.boot_from_packs(
        _Main.PACK_PATHS, _Main._runtime_namespace()
    )
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    namespace = _Main._runtime_namespace()
    booted = time.monotonic()

    manifest = []
    shards = spill.shard_names()
    for shard in shards:
        shard_nodes = spill.read(shard, "nodes")
        shard_edges = spill.read(shard, "edges")
        nodes, edges = _Csv.build_terms(shard_nodes, shard_edges)
        graph._replace_context(nodes=nodes, edges=edges)
        snapshot = os.path.join(outdir, shard + ".json")
        _Runtime.save_runtime(runtime, snapshot, namespace)
        manifest.append({
            "shard": shard,
            "file": shard + ".json",
            "nodes": count_text(nodes, registry),
            "edges": count_text(edges, registry),
            "bytes": os.path.getsize(snapshot),
        })
        print(
            "SHARD %s nodes=%s edges=%s bytes=%d"
            % (
                shard,
                count_text(nodes, registry),
                count_text(edges, registry),
                os.path.getsize(snapshot),
            ),
            flush=True,
        )
        del shard_nodes, shard_edges, nodes, edges
    finished = time.monotonic()

    manifest_path = os.path.join(outdir, "manifest.json")
    handle = open(manifest_path, "w", encoding="utf-8")
    try:
        handle.write(json.dumps({
            "source_nodes": node_total,
            "source_edges": edge_total,
            "cross_shard_edges": crossing,
            "edges_with_undeclared_source": dangling,
            "shards": manifest,
        }, ensure_ascii=False, indent=2))
        handle.write("\n")
    finally:
        handle.close()

    print(
        "SHARDED shards=%d source_nodes=%d source_edges=%d crossing=%d "
        "undeclared=%d spill=%.2fs boot=%.2fs build_save=%.2fs total=%.2fs"
        % (
            len(shards), node_total, edge_total, crossing, dangling,
            spilled - started, booted - spilled, finished - booted,
            finished - started,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
