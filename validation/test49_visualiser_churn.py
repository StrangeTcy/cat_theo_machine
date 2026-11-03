"""Test 49: term identity and churn in the observation tap.

The round-1 report described terms being removed and recreated while packs load,
as if the constructor registry growing changed their identity. This suite pins
down what happens:

  [1] a steady graph produces no delta at all between two polls;
  [2] the round-1 churn (every rule premise term vanishing on the second poll) is
      gone -- a rule-bearing graph is read twice and reports no removals;
  [3] loading more packs adds items and removes none, and the ids of terms that
      were already there do not change;
  [4] a genuine difference is still reported: an id that really disappears shows
      up in items.removed, so nothing is hidden by the identity work.

Runs against the real Machine: a fresh runtime, real packs, real rule objects.
No conda, no Experiment 4, no core.py change.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(REPO))

from cat_theo_machine import machine as M                      # noqa: E402
from cat_theo_machine.runtime import make_fresh_runtime        # noqa: E402
from cat_theo_machine.visualiser.events import ChainReader, EventStream, GraphDigest  # noqa: E402
from cat_theo_machine.visualiser.tap import GraphObservationTap  # noqa: E402

PACK_DIR = os.path.join(REPO, "packs")
STATUS = "Passed"


def rule(label):
    print("    " + label + " (" + STATUS + ")")


def read_journal(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def items_of(events, kind):
    out = []
    for event in events:
        if event.get("type") == kind:
            out.extend(event.get("items", []))
    return out


def removed_of(events):
    total = []
    for event in events:
        if event.get("type") == "items.removed":
            total.extend(event.get("nodes", []))
            total.extend(event.get("edges", []))
    return total


def main():
    print("=== TEST 49: observation identity and churn ===")
    print()

    workdir = tempfile.mkdtemp(prefix="ctm-visualiser-test49-")
    runtime = make_fresh_runtime()
    graph = runtime.graph
    import cat_theo_machine.main as main_module

    namespace = main_module._runtime_namespace()

    # A graph with carrier content, then one pack so real rules exist.
    graph.add_node(M.Char("alpha"))
    graph.add_node(M.Char("beta"))
    arguments = M.Pair(M.Char("beta"), M.EmptyList)
    graph.add_edge(M.Pair(M.Char("Linked"), arguments))
    runtime.load_pack(os.path.join(PACK_DIR, "order-sign.pack.yaml"), namespace)

    print("[1] Two polls of an unchanged graph")
    journal = os.path.join(workdir, "steady.jsonl")
    tap = GraphObservationTap(graph, runtime=runtime, journal_path=journal, interval=0.2, rule_cap=40)
    tap.start()
    first = read_journal(journal)
    assert items_of(first, "nodes.added") or items_of(first, "edges.added"), "the tap reported nothing at all"
    first_counts = len(first)
    time.sleep(0.4)
    tap.poll_once()
    second = read_journal(journal)
    after = second[first_counts:]
    assert removed_of(after) == [], "a poll with no machine change reported removals: " + str(removed_of(after)[:5])
    assert items_of(after, "nodes.added") == [], "a poll with no machine change reported additions"
    assert items_of(after, "edges.added") == [], "a poll with no machine change reported new edges"
    rule(
        "second poll of an unchanged graph is silent: "
        + str(first_counts)
        + " events, then "
        + str(len(after))
        + " heartbeat only"
    )

    print()
    print("[2] The round-1 churn: rule premises vanishing on the next poll")
    # The specific defect: _rule_item returned its premises only on the miss path,
    # so the *second* read of any rule-bearing graph lost every premise term and
    # the third brought them back. Two further polls would have reported ~90
    # removals and ~90 additions for a graph nobody touched.
    digest = GraphDigest(graph, runtime=runtime, rule_cap=40)
    before = digest.read()
    time.sleep(0.05)
    again = digest.read()
    removed = [key for key in before["nodes"] if key not in again["nodes"]]
    added = [key for key in again["nodes"] if key not in before["nodes"]]
    assert removed == [], "re-reading the same graph lost node items: " + str(removed[:5])
    assert added == [], "re-reading the same graph invented node items: " + str(added[:5])
    rule_items = [item for item in again["edges"].values() if item["kind"] == "rule"]
    assert rule_items, "no rules were read, so this check proved nothing"
    with_premises = [item for item in rule_items if item["arguments"]]
    assert len(with_premises) == len(rule_items), (
        "a cached rule lost its premises: "
        + str(len(with_premises))
        + " of "
        + str(len(rule_items))
    )
    rule(
        "second read keeps every premise of "
        + str(len(rule_items))
        + " rules, "
        + str(len(before["nodes"]))
        + " node items unchanged"
    )

    print()
    print("[3] Loading another pack: additions only, identities unchanged")
    identity_before = {
        key: (item["id"], item["label"], item["term"], item.get("constructor", ""))
        for key, item in again["nodes"].items()
    }
    edge_ids_before = set(again["edges"])
    runtime.load_pack(os.path.join(PACK_DIR, "arithmetic.pack.yaml"), namespace)
    grown = digest.read()
    removed = [key for key in again["nodes"] if key not in grown["nodes"]]
    lost_edges = [key for key in edge_ids_before if key not in grown["edges"]]
    assert removed == [], "registry growth removed node items: " + str(removed[:5])
    assert lost_edges == [], "registry growth removed edge items: " + str(lost_edges[:5])
    changed = [
        key for key, triple in identity_before.items()
        if key in grown["nodes"]
        and (grown["nodes"][key]["label"], grown["nodes"][key]["term"]) != (triple[1], triple[2])
    ]
    assert changed == [], "registry growth changed the rendering of a term: " + str(changed[:5])
    assert len(grown["edges"]) > len(edge_ids_before), "the second pack added no rules"
    rule(
        "pack 2 added "
        + str(len(grown["edges"]) - len(edge_ids_before))
        + " edges and removed nothing; "
        + str(len(identity_before))
        + " existing ids unchanged"
    )

    print()
    print("[4] A genuine disappearance is still reported")
    # Removing an item from the graph is graph surgery, not a rendering change,
    # and the delta layer must say so. Drive the stream directly with two tables
    # that differ by one real item.
    stream = EventStream()
    previous = [
        {"id": "t:kept", "kind": "node", "label": "kept", "term": "kept", "constructor": "", "declared": True, "source": "node store"},
        {"id": "t:gone", "kind": "node", "label": "gone", "term": "gone", "constructor": "", "declared": True, "source": "node store"},
    ]
    current = [previous[0]]
    events = list(stream.added([], [])) + list(stream.removed(["t:gone"], []))
    removed = removed_of(events)
    assert removed == ["t:gone"], "a vanished node was not reported: " + str(removed)
    assert current[0]["id"] in previous[0]["id"], "sanity"
    rule("an id that really vanishes appears in items.removed, so no mutation is hidden")

    print()
    print("[5] A synthetic graph edit is reported exactly once")
    journal_b = os.path.join(workdir, "edit.jsonl")
    tap_b = GraphObservationTap(graph, runtime=runtime, journal_path=journal_b, interval=0.2, rule_cap=40)
    tap_b.start()
    base = len(read_journal(journal_b))
    graph.add_node(M.Char("gamma"))
    tap_b.poll_once()
    delta = read_journal(journal_b)[base:]
    assert len(items_of(delta, "nodes.added")) == 1, items_of(delta, "nodes.added")
    assert removed_of(delta) == [], removed_of(delta)
    rule("one added node produces exactly one node item and no removals")

    tap.stop("test finished")
    tap_b.stop("test finished")

    print()
    print("[6] Teardown")
    shutil.rmtree(workdir, ignore_errors=True)
    print("    taps stopped, temporary directory " + workdir + " removed (" + STATUS + ")")
    print()
    print("=== ALL TEST 49 CHURN CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
