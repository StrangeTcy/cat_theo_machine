"""Scale ladder for the ingest path: where does importing a large graph break?

The acceptance criteria are proven at 20,000 relations. A real Neo4j dump of
heterogeneous notes is plausibly a million objects, and "prohibitive at millions"
was an extrapolation from one data point rather than a measurement. This probe
walks a ladder of relation counts through the actual ingest path -- build terms,
save, reload -- and reports time, snapshot size and peak resident set at each
rung, so the wall is located rather than guessed at.

Peak RSS is reported because the terms are live Python objects: a snapshot that
fits on disk may not fit in memory twice, and the reload phase holds the decoded
graph and the restored graph at once.

Boot happens once; each rung replaces the graph context, so the ladder measures
the codec and not the packs.

Usage:
    python probes/ingest_scale_probe.py [RELATIONS,RELATIONS,...]
"""

import gc
import os
import resource
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


def count_of(chain, registry):
    return M.Head(M.NatFromRep(M.CountRep(chain)(), registry)())()


def text_of(nat, registry):
    return M.GMPRepText(M.NatRepOf(nat, registry)())()


def peak_rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def rows_for(relations):
    nodes = relations // 10
    node_rows = []
    index = 0
    while index < nodes:
        node_rows.append({"id": "n%d" % index, "label": "Person",
                          "note": "note-%d" % index})
        index += 1
    edge_rows = []
    index = 0
    while index < relations:
        edge_rows.append({"src": "n%d" % (index % nodes), "rel": "lives_in",
                          "dst": "n%d" % ((index * 7) % nodes)})
        index += 1
    return node_rows, edge_rows


def main():
    argv = sys.argv
    ladder = (20000, 60000, 150000)
    if len(argv) > 1:
        ladder = tuple(int(part) for part in argv[1].split(","))

    work = tempfile.mkdtemp(prefix="scale-probe-")
    started = time.monotonic()
    runtime, _packs = _Runtime.boot_from_packs(
        _Main.PACK_PATHS, _Main._runtime_namespace()
    )
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    namespace = _Main._runtime_namespace()
    print("boot %.2fs peak_rss=%.0fMB" % (time.monotonic() - started, peak_rss_mb()),
          flush=True)

    for relations in ladder:
        snapshot = os.path.join(work, "scale_%d.json" % relations)
        node_rows, edge_rows = rows_for(relations)
        phase = time.monotonic()
        nodes, edges = _Importer.build_terms(node_rows, edge_rows)
        graph._replace_context(nodes=nodes, edges=edges)
        built = time.monotonic()
        edge_count = text_of(count_of(edges, registry), registry)
        del nodes, edges, node_rows, edge_rows
        print("  phase build=%.2fs edges=%s peak_rss=%.0fMB"
              % (built - phase, edge_count, peak_rss_mb()), flush=True)
        _Runtime.save_runtime(runtime, snapshot, namespace)
        saved = time.monotonic()
        print("  phase save=%.2fs MB=%.1f peak_rss=%.0fMB"
              % (saved - built, os.path.getsize(snapshot) / 1048576.0,
                 peak_rss_mb()), flush=True)
        reloaded = _Runtime.boot_from_snapshot(snapshot, namespace)
        loaded = time.monotonic()
        print("  phase load=%.2fs peak_rss=%.0fMB"
              % (loaded - saved, peak_rss_mb()), flush=True)
        reloaded_registry = M.FromContextGetConstructors(reloaded.graph)()
        reloaded_edges = text_of(
            count_of(reloaded.graph.edges, reloaded_registry), reloaded_registry
        )
        print(
            "SCALE relations=%d edges=%s reloaded=%s build=%.2fs save=%.2fs "
            "load=%.2fs MB=%.1f peak_rss=%.0fMB"
            % (
                relations, edge_count, reloaded_edges,
                built - phase, saved - built, loaded - saved,
                os.path.getsize(snapshot) / 1048576.0, peak_rss_mb(),
            ),
            flush=True,
        )
        del reloaded
        os.remove(snapshot)
        gc.collect()

    print("total %.2fs peak_rss=%.0fMB" % (
        time.monotonic() - started, peak_rss_mb()), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
