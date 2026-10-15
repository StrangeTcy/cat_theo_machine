"""Split what `apoc.export.csv.all` writes into the node and relationship files the importers read.

The importers (`csv_to_hypergraph`, `sharded_import`) take two files: nodes and
relationships. A restored Neo4j dump, exported with
`CALL apoc.export.csv.all("all.csv", {})`, gives **one** file whose header is the
union of everything:

    _id,_labels,<every node property>,_start,_end,_type,<every relationship property>

Node rows fill `_id`/`_labels` and leave `_start`/`_end`/`_type` blank;
relationship rows do the reverse. Properties absent on a particular object are
empty strings. With `{bulkImport: true}` apoc instead writes one file per label
and per relationship type, with `neo4j-admin import` headers
(`:ID`, `:LABEL`, `:START_ID`, `:END_ID`, `:TYPE`, and `name:string`-style
property columns). This module accepts either shape, or a mixture, and writes:

    OUTDIR/nodes.csv    header  _id,_labels,<node properties seen non-empty>
    OUTDIR/edges.csv    header  _start,_end,_type,<relationship properties seen non-empty>
    OUTDIR/split.json   counts, columns, first-label histogram (one shard per
                        first label is what `sharded_import` will produce), warnings

Two passes, both streaming: the first learns which columns actually carry a
value for nodes and for relationships (the union header makes most cells empty),
the second writes. Nothing is held per row, so the file may be larger than
memory.

What is deliberately *not* interpreted: property values. apoc writes arrays as
`["a","b"]` and numbers as text; both stay whole strings, because the importers
put a whole property string into one `Char` (see `csv_to_hypergraph`), and that
is the representation the rest of the machine reasons over. Type qualifiers in
headers (`age:long`, `tags:string[]`) are stripped from the *name* only.

Usage:
    python -m cat_theo_machine.importers.split_apoc_export OUTDIR EXPORT.csv [MORE.csv ...]
"""

from __future__ import annotations

import csv
import json
import os
import sys

# apoc's combined-export names, lower-cased; the importers accept exactly these.
ID_COLUMN = "_id"
LABELS_COLUMN = "_labels"
START_COLUMN = "_start"
END_COLUMN = "_end"
TYPE_COLUMN = "_type"
STRUCTURAL = (ID_COLUMN, LABELS_COLUMN, START_COLUMN, END_COLUMN, TYPE_COLUMN)

# `neo4j-admin import` qualifiers (what `bulkImport: true` writes), upper-cased.
QUALIFIERS = {
    "ID": ID_COLUMN,
    "LABEL": LABELS_COLUMN,
    "START_ID": START_COLUMN,
    "END_ID": END_COLUMN,
    "TYPE": TYPE_COLUMN,
}

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))  # a long note is one field


def normalise_header(name):
    """Map one header to the importer's name for it, or None to drop the column.

    `_id`, `_labels`, `_start`, `_end`, `_type` pass through (case-insensitively).
    `:ID`, `id:ID`, `_id:ID(Person)` all mean `_id`; likewise LABEL, START_ID,
    END_ID, TYPE. `name:string`, `tags:string[]`, `age:long` are property columns
    named `name`, `tags`, `age`. `:IGNORE` columns are dropped.
    """
    text = (name or "").strip().lstrip("\ufeff")
    lowered = text.lower()
    if lowered in STRUCTURAL:
        return lowered
    if ":" not in text:
        return text
    base, qualifier = text.split(":", 1)
    qualifier = qualifier.strip()
    if "(" in qualifier:
        qualifier = qualifier.split("(", 1)[0]
    upper = qualifier.strip().upper()
    if upper == "IGNORE":
        return None
    if upper in QUALIFIERS:
        return QUALIFIERS[upper]
    if base.strip().lower() in STRUCTURAL:
        return base.strip().lower()
    return base.strip() or text


def _open(path):
    return open(path, "r", encoding="utf-8-sig", newline="")


def _header_map(path):
    """[(original, normalised)] for a file's header, with duplicate targets dropped."""
    with _open(path) as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return []
    mapping = []
    seen = set()
    for original in header:
        target = normalise_header(original)
        if target is None or target == "":
            continue
        if target in seen:
            mapping.append((original, None))  # second column for the same name: ignored
            continue
        seen.add(target)
        mapping.append((original, target))
    return mapping


def _rows(path, mapping):
    """Yield rows as dicts keyed by normalised column name (dropped columns omitted)."""
    targets = [target for _original, target in mapping]
    with _open(path) as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for raw in reader:
            if not raw or all(cell == "" for cell in raw):
                continue
            row = {}
            for index, target in enumerate(targets):
                if target is None:
                    continue
                row[target] = raw[index] if index < len(raw) else ""
            yield row


def classify(row):
    """'node', 'relationship', or '' for a row that is neither."""
    if row.get(START_COLUMN, "") != "" and row.get(END_COLUMN, "") != "":
        return "relationship"
    if row.get(ID_COLUMN, "") != "":
        return "node"
    return ""


def first_label(labels_text):
    """`:Person:Author` -> `Person`; `Person;Author` (bulk form) -> `Person`."""
    text = (labels_text or "").replace(";", ":").strip()
    while text.startswith(":"):
        text = text[1:]
    return text.split(":", 1)[0]


def _normalise_labels(text):
    """Bulk files write `A;B` (or a bare `A`); the importers expect apoc's `:A:B`."""
    text = (text or "").strip()
    if text == "" or text.startswith(":"):
        return text
    return ":" + ":".join(part for part in text.replace(";", ":").split(":") if part)


def split(paths, outdir):
    """Write nodes.csv / edges.csv / split.json under `outdir`; return the summary."""
    os.makedirs(outdir, exist_ok=True)
    plans = [(path, _header_map(path)) for path in paths]
    warnings = []
    node_columns = []       # property columns, in order of first non-empty sighting
    rel_columns = []
    node_seen = set()
    rel_seen = set()
    counts = {"node": 0, "relationship": 0, "skipped": 0}
    labels = {}
    types = {}
    for path, mapping in plans:
        if not mapping:
            warnings.append("%s: empty or headerless; ignored" % path)
            continue
        names = {target for _original, target in mapping if target}
        if ID_COLUMN not in names and START_COLUMN not in names:
            warnings.append("%s: no identity or start column after normalisation; every row will be skipped" % path)
        for original, target in mapping:
            if target is None:
                warnings.append("%s: column %r duplicates an earlier column; ignored" % (path, original))
        for row in _rows(path, mapping):
            kind = classify(row)
            if kind == "":
                counts["skipped"] += 1
                continue
            counts[kind] += 1
            if kind == "node":
                label = first_label(row.get(LABELS_COLUMN, ""))
                labels[label] = labels.get(label, 0) + 1
                for key, value in row.items():
                    if key in STRUCTURAL or value == "" or key in node_seen:
                        continue
                    node_seen.add(key)
                    node_columns.append(key)
            else:
                rel_type = row.get(TYPE_COLUMN, "")
                types[rel_type] = types.get(rel_type, 0) + 1
                for key, value in row.items():
                    if key in STRUCTURAL or value == "" or key in rel_seen:
                        continue
                    rel_seen.add(key)
                    rel_columns.append(key)
    if "" in labels:
        warnings.append("%d node(s) carry no label; sharded_import puts them in `%s`" % (labels[""], "unlabelled"))
    if "" in types:
        warnings.append("%d relationship(s) carry no type" % types[""])

    node_header = [ID_COLUMN, LABELS_COLUMN] + node_columns
    rel_header = [START_COLUMN, END_COLUMN, TYPE_COLUMN] + rel_columns
    nodes_path = os.path.join(outdir, "nodes.csv")
    edges_path = os.path.join(outdir, "edges.csv")
    with open(nodes_path, "w", encoding="utf-8", newline="") as nodes_handle, open(edges_path, "w", encoding="utf-8", newline="") as edges_handle:
        node_writer = csv.DictWriter(nodes_handle, fieldnames=node_header, extrasaction="ignore")
        edge_writer = csv.DictWriter(edges_handle, fieldnames=rel_header, extrasaction="ignore")
        node_writer.writeheader()
        edge_writer.writeheader()
        for path, mapping in plans:
            if not mapping:
                continue
            for row in _rows(path, mapping):
                kind = classify(row)
                if kind == "node":
                    row[LABELS_COLUMN] = _normalise_labels(row.get(LABELS_COLUMN, ""))
                    node_writer.writerow(row)
                elif kind == "relationship":
                    edge_writer.writerow(row)
    summary = {
        "inputs": [path for path, _mapping in plans],
        "nodes_csv": nodes_path,
        "edges_csv": edges_path,
        "node_rows": counts["node"],
        "relationship_rows": counts["relationship"],
        "skipped_rows": counts["skipped"],
        "node_property_columns": node_columns,
        "relationship_property_columns": rel_columns,
        "first_labels": dict(sorted(labels.items(), key=lambda item: (-item[1], item[0]))),
        "relationship_types": dict(sorted(types.items(), key=lambda item: (-item[1], item[0]))),
        "warnings": warnings,
    }
    with open(os.path.join(outdir, "split.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return summary


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print("usage: split_apoc_export OUTDIR EXPORT.csv [MORE.csv ...]")
        return 1
    outdir, paths = argv[0], argv[1:]
    missing = [path for path in paths if not os.path.exists(path)]
    if missing:
        print("missing input(s): %s" % ", ".join(missing))
        return 1
    summary = split(paths, outdir)
    print(
        "SPLIT nodes=%d relationships=%d skipped=%d first_labels=%d relationship_types=%d -> %s, %s"
        % (
            summary["node_rows"],
            summary["relationship_rows"],
            summary["skipped_rows"],
            len(summary["first_labels"]),
            len(summary["relationship_types"]),
            summary["nodes_csv"],
            summary["edges_csv"],
        ),
        flush=True,
    )
    for warning in summary["warnings"]:
        print("WARNING " + warning, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
