"""Test 32 -- W19: a Neo4j export, as APOC writes it, becomes bootable Machine shards.

Run:
    PYTHONPATH=/home/user .venv/bin/python -u validation/test32_neo4j_export_to_shards.py

What this suite is for
----------------------
`delegation/W19-neo4j-dump-to-shards.md`. The decode path for a Neo4j `.dump` is:
load it into Neo4j (on Colab, `colab/neo4j_dump_to_shards.ipynb`), export with
`apoc.export.csv.all`, split that single union-header CSV into the node and
relationship files the importers read (`importers/split_apoc_export.py`, new), and
shard by label (`importers/sharded_import.py`). Neo4j itself cannot run here, so
what this suite drives is everything downstream of the export, against a
synthetic export shaped exactly as APOC's documentation describes -- including
the parts that break naive CSV handling: multi-label nodes, unlabelled nodes,
array-valued and type-qualified properties, quoted multi-line text, non-ASCII
names, and the `bulkImport` variant with `neo4j-admin` headers.

Phases 1-3 cost under a second. Phase 4 runs the real `sharded_import` (one pack
boot, ~20 s) and then boots one shard on its own to count it with the machine.
Phase 5 checks the two notebooks and the runbook are well-formed and point at
things that exist -- and that no key material is anywhere near the tree.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_PARENT = os.path.dirname(PACKAGE_ROOT)
if PACKAGE_PARENT not in sys.path:
    sys.path.insert(0, PACKAGE_PARENT)

from cat_theo_machine import machine as M
from cat_theo_machine.importers import csv_to_hypergraph as Csv
from cat_theo_machine.importers import split_apoc_export as Split

MULTILINE = 'first line\nsecond line, with "quotes" and a, comma'
UNICODE_NAME = "Boštjan Žnidaršič — 数学"
ARRAY_VALUE = '["math","music"]'


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def check(self, label, condition, detail=""):
        if condition:
            self.passed += 1
            print("  PASS  %-62s %s" % (label, detail))
        else:
            self.failed += 1
            print("  FAIL  %-62s %s" % (label, detail))
        return bool(condition)

    def note(self, text):
        print("  note  %s" % text)


# ------------------------------------------------------------------- fixtures


def write_combined_export(path):
    """One file the way `apoc.export.csv.all("all.csv", {useTypes: true})` lays it out."""
    header = ["_id", "_labels", "name", "born:long", "tags:string[]", "_start", "_end", "_type", "since:long", "weight:double"]
    nodes = [
        ("0", ":Person:Author", "Ana Novak", "1980", ARRAY_VALUE),
        ("1", ":Person", UNICODE_NAME, "", ""),
        ("2", ":House", "Hiša pri Lipi", "1843", ""),
        ("3", ":Note", MULTILINE, "", ""),
        ("4", "", "orphan", "", ""),
        ("5", ":Person", "Cene", "", ARRAY_VALUE),
    ]
    rels = [
        ("0", "2", "LIVES_IN", "1999", ""),
        ("1", "0", "KNOWS", "", "0.5"),
        ("3", "2", "ABOUT", "", ""),
        ("5", "1", "KNOWS", "2001", ""),
        ("4", "3", "WROTE", "", ""),
    ]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for node_id, labels, name, born, tags in nodes:
            writer.writerow([node_id, labels, name, born, tags, "", "", "", "", ""])
        for start, end, rel_type, since, weight in rels:
            writer.writerow(["", "", "", "", "", start, end, rel_type, since, weight])
    return {"nodes": len(nodes), "relationships": len(rels), "labels": {"Person": 3, "House": 1, "Note": 1, "": 1}}


def write_bulk_export(directory):
    """The `bulkImport: true` shape: one file per label and per type, neo4j-admin headers."""
    person = os.path.join(directory, "all.nodes.Person.csv")
    house = os.path.join(directory, "all.nodes.House.csv")
    knows = os.path.join(directory, "all.relationships.KNOWS.csv")
    with open(person, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([":ID", ":LABEL", "name:string", "born:long", "secret:IGNORE"])
        writer.writerow(["p1", "Person;Author", "Ana Novak", "1980", "drop-me"])
        writer.writerow(["p2", "Person", UNICODE_NAME, "", "drop-me"])
    with open(house, "w", encoding="utf-8-sig", newline="") as handle:  # a BOM, as spreadsheets leave
        writer = csv.writer(handle)
        writer.writerow(["id:ID(House)", ":LABEL", "name:string"])
        writer.writerow(["h1", "House", "Hiša pri Lipi"])
    with open(knows, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([":START_ID", ":END_ID", ":TYPE", "since:long"])
        writer.writerow(["p1", "p2", "KNOWS", "1999"])
        writer.writerow(["p2", "h1", "LIVES_IN", ""])
    return [person, house, knows]


def read_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


# ----------------------------------------------------------------- phase one


def phase_headers(results):
    print("\n[1] header normalisation: apoc's names, neo4j-admin's qualifiers, type suffixes")
    cases = [
        ("_id", "_id"), ("_ID", "_id"), ("_labels", "_labels"), ("_start", "_start"), ("_end", "_end"), ("_type", "_type"),
        (":ID", "_id"), ("id:ID", "_id"), ("id:ID(Person)", "_id"), ("_id:ID", "_id"),
        (":LABEL", "_labels"), (":START_ID", "_start"), (":END_ID", "_end"), (":TYPE", "_type"),
        ("name:string", "name"), ("tags:string[]", "tags"), ("age:long", "age"), ("ok:boolean", "ok"),
        ("name", "name"), ("\ufeff_id", "_id"), (" name ", "name"), (":IGNORE", None), ("secret:IGNORE", None),
    ]
    wrong = [(given, Split.normalise_header(given), wanted) for given, wanted in cases if Split.normalise_header(given) != wanted]
    results.check("every documented header form maps to the importer's name", not wrong, "%s" % wrong if wrong else "%d forms" % len(cases))
    results.check("first_label reads apoc's `:A:B` and bulk's `A;B` alike", Split.first_label(":Person:Author") == "Person" and Split.first_label("Person;Author") == "Person" and Split.first_label("") == "")
    results.check(
        "classification: a row is a relationship by endpoints, a node by identity, else nothing",
        Split.classify({"_id": "", "_start": "1", "_end": "2"}) == "relationship" and Split.classify({"_id": "7", "_start": "", "_end": ""}) == "node" and Split.classify({"_id": "", "_start": "", "_end": ""}) == "",
    )


# ----------------------------------------------------------------- phase two


def phase_combined(results, directory):
    print("\n[2] a combined apoc export splits into the two files the importers read")
    export = os.path.join(directory, "all.csv")
    expected = write_combined_export(export)
    out = os.path.join(directory, "split")
    summary = Split.split([export], out)
    results.check(
        "row classification matches what was written",
        summary["node_rows"] == expected["nodes"] and summary["relationship_rows"] == expected["relationships"] and summary["skipped_rows"] == 0,
        "nodes=%d relationships=%d skipped=%d" % (summary["node_rows"], summary["relationship_rows"], summary["skipped_rows"]),
    )
    results.check("the first-label histogram is the shard plan", summary["first_labels"] == expected["labels"], "%s" % summary["first_labels"])
    node_header, node_rows = read_csv(summary["nodes_csv"])
    edge_header, edge_rows = read_csv(summary["edges_csv"])
    results.check(
        "nodes.csv carries identity, labels and only node properties, type suffixes stripped",
        node_header == ["_id", "_labels", "name", "born", "tags"],
        "%s" % node_header,
    )
    results.check(
        "edges.csv carries endpoints, type and only relationship properties",
        edge_header == ["_start", "_end", "_type", "since", "weight"],
        "%s" % edge_header,
    )
    by_id = {row["_id"]: row for row in node_rows}
    results.check("quoted multi-line text survives the round trip byte for byte", by_id.get("3", {}).get("name") == MULTILINE)
    results.check("non-ASCII names survive", by_id.get("1", {}).get("name") == UNICODE_NAME)
    results.check("array properties stay whole strings (one Char each, downstream)", by_id.get("0", {}).get("tags") == ARRAY_VALUE and by_id.get("5", {}).get("tags") == ARRAY_VALUE)
    results.check("the unlabelled node is kept and flagged", by_id.get("4", {}).get("_labels") == "" and any("no label" in warning for warning in summary["warnings"]), "; ".join(summary["warnings"]))
    knows = [row for row in edge_rows if row["_type"] == "KNOWS"]
    results.check(
        "relationship properties land on the relationship rows",
        len(knows) == 2 and {row["since"] for row in knows} == {"", "2001"} and {row["weight"] for row in knows} == {"0.5", ""},
        "%s" % knows,
    )
    # The importers' own canonicalisation sees exactly the roles it expects.
    canon_node = Csv.canonical_node_row(by_id["0"])
    canon_edges = Csv.canonical_edge_rows(edge_rows[0])
    results.check(
        "csv_to_hypergraph recognises the split's headers natively",
        canon_node.get("id") == "0" and canon_node.get("label") == ":Person:Author" and canon_edges[0] == {"src": "0", "dst": "2", "rel": "LIVES_IN"} and {"src": "0", "rel": "LIVES_IN:since", "dst": "1999"} in canon_edges,
        "%s / %s" % (canon_node, canon_edges),
    )
    results.check("split.json is written and self-describing", os.path.exists(os.path.join(out, "split.json")) and json.load(open(os.path.join(out, "split.json")))["node_rows"] == expected["nodes"])
    return summary


# --------------------------------------------------------------- phase three


def _chain_items(chain):
    items = []
    cursor = chain
    while M.IsPair(cursor)() is M.truth_value:
        items.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return items


def _edge_triple(edge):
    """(rel, a, b) as host strings, for a `Pair(rel, Pair(a, Pair(b, EmptyList)))` edge."""
    rel = M.Head(edge)()
    rest = M.Tail(edge)()
    a = M.Head(rest)()
    b = M.Head(M.Tail(rest)())()
    return (M.CharText(rel)(), M.CharText(a)(), M.CharText(b)()) if hasattr(M, "CharText") else (rel, a, b)


def phase_bulk(results, directory):
    print("\n[3] the bulkImport variant: several files, neo4j-admin headers, a BOM, an :IGNORE column")
    bulk_dir = os.path.join(directory, "bulk")
    os.makedirs(bulk_dir, exist_ok=True)
    files = write_bulk_export(bulk_dir)
    out = os.path.join(directory, "bulk-split")
    summary = Split.split(files, out)
    results.check("rows from every file are classified by their headers", summary["node_rows"] == 3 and summary["relationship_rows"] == 2 and summary["skipped_rows"] == 0, "nodes=%d relationships=%d" % (summary["node_rows"], summary["relationship_rows"]))
    node_header, node_rows = read_csv(summary["nodes_csv"])
    results.check("the :IGNORE column is gone and the BOM did not become part of a name", "secret" not in node_header and node_header[0] == "_id", "%s" % node_header)
    by_id = {row["_id"]: row for row in node_rows}
    results.check("bulk's `Person;Author` becomes apoc's `:Person:Author` for the sharder", by_id.get("p1", {}).get("_labels") == ":Person:Author" and by_id.get("h1", {}).get("_labels") == ":House", "%s" % {k: v.get("_labels") for k, v in by_id.items()})
    _edge_header, edge_rows = read_csv(summary["edges_csv"])
    node_terms, edge_terms = Csv.build_terms([Csv.canonical_node_row(row) for row in node_rows], [entry for row in edge_rows for entry in Csv.canonical_edge_rows(row)])
    nodes = _chain_items(node_terms)
    edges = _chain_items(edge_terms)
    # 3 nodes; edges = 2 relationships + 1 relationship property + node properties (label x3, name x3, born x1) = 10
    results.check("build_terms makes one node per row and one hyperedge per fact", len(nodes) == 3 and len(edges) == 10, "nodes=%d edges=%d" % (len(nodes), len(edges)))
    wanted = M.Pair(M.Char("KNOWS:since"), M.Pair(M.Char("p1"), M.Pair(M.Char("1999"), M.EmptyList)))
    found = any(M.Compare(edge, wanted)() is M.truth_value for edge in edges)
    results.check("a relationship property is a `TYPE:prop` hyperedge the machine can Compare", found)
    name_edge = M.Pair(M.Char("name"), M.Pair(M.Char("p2"), M.Pair(M.Char(UNICODE_NAME), M.EmptyList)))
    results.check("a non-ASCII property value is one Char, matched whole", any(M.Compare(edge, name_edge)() is M.truth_value for edge in edges))


# ---------------------------------------------------------------- phase four


def phase_shards(results, directory, split_summary):
    print("\n[4] the real sharder on the split output, and one shard booted alone")
    out = os.path.join(directory, "shards")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = PACKAGE_PARENT
    started = time.time()
    proc = subprocess.run(
        [sys.executable, "-m", "cat_theo_machine.importers.sharded_import", split_summary["nodes_csv"], split_summary["edges_csv"], out],
        cwd=PACKAGE_PARENT, env=environment, capture_output=True, text=True, timeout=900,
    )
    lines = [line for line in proc.stdout.splitlines() if line.startswith(("SHARD", "SHARDED"))]
    if not results.check("sharded_import runs to completion on the split files", proc.returncode == 0, "rc=%d in %.0fs" % (proc.returncode, time.time() - started)):
        results.note(proc.stdout[-2000:])
        results.note(proc.stderr[-2000:])
        return
    for line in lines:
        results.note(line)
    manifest = json.load(open(os.path.join(out, "manifest.json"), encoding="utf-8"))
    shards = {entry["shard"]: entry for entry in manifest["shards"]}
    results.check("one shard per first label, plus `unlabelled`", set(shards) == {"Person", "House", "Note", "unlabelled"}, "%s" % sorted(shards))
    results.check("the manifest's source counts are the split's", manifest["source_nodes"] == split_summary["node_rows"] and manifest["cross_shard_edges"] > 0 and manifest["edges_with_undeclared_source"] == 0, "nodes=%s crossing=%s undeclared=%s" % (manifest["source_nodes"], manifest["cross_shard_edges"], manifest["edges_with_undeclared_source"]))

    from cat_theo_machine import main as MA
    from cat_theo_machine import runtime as RT

    entry = shards.get("Note")
    if entry is None:
        return
    booted = time.time()
    runtime = RT.boot_from_snapshot(os.path.join(out, entry["file"]), MA._runtime_namespace())
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()

    def count_text(chain):
        return M.GMPRepText(M.NatRepOf(M.Head(M.NatFromRep(M.CountRep(chain)(), registry)())(), registry)())()

    results.check(
        "a shard boots alone and the machine's own count agrees with the manifest",
        count_text(graph.nodes) == entry["nodes"] and count_text(graph.edges) == entry["edges"],
        "nodes=%s/%s edges=%s/%s in %.0fs" % (count_text(graph.nodes), entry["nodes"], count_text(graph.edges), entry["edges"], time.time() - booted),
    )
    multiline_edge = M.Pair(M.Char("name"), M.Pair(M.Char("3"), M.Pair(M.Char(MULTILINE), M.EmptyList)))
    edges = _chain_items(graph.edges)
    results.check("the multi-line property arrived in the shard intact, as one Char", any(M.Compare(edge, multiline_edge)() is M.truth_value for edge in edges))
    stub_edge = M.Pair(M.Char("stub_of"), M.Pair(M.Char("2"), M.Pair(M.Char("House"), M.EmptyList)))
    results.check("the ABOUT edge's foreign endpoint is a stub naming its home shard", any(M.Compare(edge, stub_edge)() is M.truth_value for edge in edges))
    nodes = _chain_items(graph.nodes)
    about = M.Pair(M.Char("ABOUT"), M.Pair(M.Char("3"), M.Pair(M.Char("2"), M.EmptyList)))
    has_about = any(M.Compare(edge, about)() is M.truth_value for edge in edges)
    has_both = all(any(M.Compare(node, M.Char(name))() is M.truth_value for node in nodes) for name in ("3", "2"))
    results.check("no dangling edge: both endpoints of the cross-shard relationship are nodes here", has_about and has_both)


# ---------------------------------------------------------------- phase five


def phase_notebooks(results):
    print("\n[5] the notebooks and the runbook: well-formed, pointing at things that exist, no keys")
    colab = os.path.join(PACKAGE_ROOT, "colab")
    notebooks = {}
    for name in ("neo4j_dump_to_shards.ipynb", "mesh_worker.ipynb"):
        path = os.path.join(colab, name)
        try:
            with open(path, encoding="utf-8") as handle:
                notebooks[name] = json.load(handle)
        except (OSError, ValueError) as error:
            results.check("%s is valid JSON" % name, False, repr(error))
            continue
        document = notebooks[name]
        compiled = True
        for cell in document.get("cells", []):
            if cell.get("cell_type") == "code":
                try:
                    compile("".join(cell["source"]), name, "exec")
                except SyntaxError as error:
                    compiled = False
                    results.note("%s: %r" % (name, error))
        results.check("%s is nbformat 4 and every code cell compiles" % name, document.get("nbformat") == 4 and compiled, "%d cells" % len(document.get("cells", [])))

    def text_of(name):
        return "".join("".join(cell["source"]) for cell in notebooks.get(name, {}).get("cells", []))

    w19 = text_of("neo4j_dump_to_shards.ipynb")
    w20 = text_of("mesh_worker.ipynb")
    results.check(
        "the dump notebook drives the modules by their real import paths",
        "cat_theo_machine.importers.split_apoc_export" in w19 and "cat_theo_machine.importers.sharded_import" in w19 and "apoc.export.csv.all" in w19 and os.path.exists(os.path.join(PACKAGE_ROOT, "importers", "split_apoc_export.py")),
    )
    results.check(
        "the worker notebook runs the W20 switches the CLI actually has",
        all(flag in w20 for flag in ("--no-inbound", "--verify", "identity", "--artifacts", "wire", "--artifact-dir", "--expect", "--cert-name")),
    )
    main_help = subprocess.run([sys.executable, os.path.join(PACKAGE_ROOT, "main.py"), "mesh", "--help"], cwd=PACKAGE_PARENT, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=PACKAGE_PARENT))
    results.check("those switches are in `main.py mesh --help`", all(flag in main_help.stdout for flag in ("--no-inbound", "--verify", "--artifacts", "--artifact-dir", "--expect", "--advertise", "--bundle-dir")), "rc=%d" % main_help.returncode)
    results.check("the worker notebook keeps key material outside the repository tree and refuses a CA key", "/content/hyge-pki" in w20 and 'assert "ca.key" not in present' in w20)
    runbook = os.path.join(colab, "README.md")
    runbook_text = open(runbook, encoding="utf-8").read() if os.path.exists(runbook) else ""
    referenced = ["validation/test31_wan_mesh_artifacts.py", "validation/test32_neo4j_export_to_shards.py", "importers/split_apoc_export.py", "importers/sharded_import.py", "networking/README.md"]
    results.check("the runbook names files that exist", bool(runbook_text) and all(ref in runbook_text and os.path.exists(os.path.join(PACKAGE_ROOT, ref)) for ref in referenced))
    tracked = subprocess.run(["git", "ls-files"], cwd=PACKAGE_ROOT, capture_output=True, text=True).stdout.splitlines()
    keys = [path for path in tracked if path.endswith((".key", ".pem", ".crt")) or os.path.basename(path) in ("ca.key", "bundle.json")]
    results.check("no certificate or key file is tracked by git", not keys, "%s" % keys)


# ------------------------------------------------------------------------ main


def main():
    print("=== TEST 32: W19 Neo4j export -> split -> shards (and the notebooks that carry it) ===")
    started = time.time()
    results = Results()
    directory = tempfile.mkdtemp(prefix="hyge-w19-")
    timings = []
    try:
        phases = [("phase_headers", lambda: phase_headers(results)), ("phase_combined", None), ("phase_bulk", lambda: phase_bulk(results, directory)), ("phase_shards", None), ("phase_notebooks", lambda: phase_notebooks(results))]
        split_summary = None
        for name, phase in phases:
            phase_started = time.time()
            if name == "phase_combined":
                split_summary = phase_combined(results, directory)
            elif name == "phase_shards":
                if os.environ.get("T32_SKIP_SHARDS") == "1":
                    results.note("phase_shards skipped (T32_SKIP_SHARDS=1)")
                    continue
                phase_shards(results, directory, split_summary)
            else:
                phase()
            timings.append((name, round(time.time() - phase_started, 1)))
    finally:
        shutil.rmtree(directory, ignore_errors=True)
        print("\n  artifacts: %s (removed)" % directory)
    elapsed = time.time() - started
    print("\n  phase wall clock: %s" % ("  ".join("%s=%.1fs" % item for item in timings)))
    print("\n=== TEST 32 COMPLETE: %d passed, %d failed in %.1fs ===" % (results.passed, results.failed, elapsed))
    return 1 if results.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
