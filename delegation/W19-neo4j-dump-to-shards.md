# W19 — A Neo4j `.dump` becomes machine-ingestible shards, with the decoding done on Colab

**Infra / ingest · Phase 0 (late) · Suite slot `test32` · Prereqs: the ingest work of
§6.8 (`importers/csv_to_hypergraph.py`, `importers/sharded_import.py`) ✅ · Owner: any session**

> **Status: landed 2026-10-15** on `arena/717c9822` (`8571449`): `importers/split_apoc_export.py`,
> `colab/neo4j_dump_to_shards.ipynb`, `colab/README.md` §B, `validation/test32_neo4j_export_to_shards.py`
> (35/35, ~38 s). **What is verified is the pipeline from an APOC export onward**; the notebook's
> first two cells — install Neo4j on a Colab runtime, `neo4j-admin database load`, `apoc.export.csv.all`
> — could not be executed in the sandbox that wrote them (no route to neo4j.com) and are marked
> unexecuted in the notebook itself. The first real run is the user's; what to look for is in the runbook.

Read `delegation/README.md` first. Invariant 2 applies in the usual host-layer form: the
splitter is a CSV-to-CSV tool and never touches a machine term; the sharder and the importer
it feeds already keep nodes, labels, property names and values as `Char`s and hyperedges.

## The problem

The ingest branch (§6.8) taught `importers/csv_to_hypergraph.py` to read APOC's CSV headers
natively and `importers/sharded_import.py` to split a nodes/edges pair into per-label shards
that each fit in memory (~10 KB resident per edge; 60k relations at 951 MB). What it did not
have was a way *from a Neo4j `.dump`* to that nodes/edges pair. A dump is Neo4j's private
store format; nothing but Neo4j decodes it, and running a JVM database on the laptop that is
also supposed to run the machine is the wrong place for it.

## What landed

1. **`importers/split_apoc_export.py`** — takes what `apoc.export.csv.all` writes and produces
   the two files the importers read, in either of APOC's two layouts:
   * the **combined** file (`_id,_labels,<node props>,_start,_end,_type,<rel props>`): a row is
     a relationship if it has endpoints, a node if it has an identity, otherwise skipped and
     counted (`classify`);
   * the **bulkImport** layout (`bulkImport:true`: one file per label and per type, neo4j-admin
     headers `name:ID`, `:LABEL`, `:START_ID`, `:END_ID`, `:TYPE`, `prop:type`, `:IGNORE`):
     `normalise_header` maps each qualifier back to the combined names, drops type suffixes
     and `:IGNORE` columns, and strips a BOM; `A;B` label lists become APOC's `:A:B`.
   Output: `nodes.csv` (`_id,_labels,<props>`), `edges.csv` (`_start,_end,_type,<props>`), and
   `split.json` with row counts, the property columns on each side, the **first-label
   histogram (which is the shard plan)**, the relationship types and any warnings
   (e.g. unlabelled nodes, which `sharded_import` files under `unlabelled`). Quoted multi-line
   text, non-ASCII and JSON-array properties survive byte for byte; arrays stay one `Char`.
2. **`colab/neo4j_dump_to_shards.ipynb`** — the decode, in the place where a JVM is free:
   mount Drive, fetch the Neo4j tarball matching the dump's major version, copy the APOC core
   jar from `labs/` to `plugins/`, `neo4j-admin database load` (5.x) or `neo4j-admin load`
   (4.4), start, `CALL apoc.export.csv.all('all.csv', {})`, stop; then `split_apoc_export` →
   `sharded_import` → the shards directory back on Drive, with the manifest printed. The
   machine does the sharding, so the notebook's Python is orchestration only.
3. **`colab/README.md` §B** — the runbook: which Neo4j version to pick, where the export lands
   (`$NEO4J_HOME/import/all.csv`), memory settings for Colab's 12 GB, and how to boot one shard
   on the laptop afterwards (`RT.boot_from_snapshot(path, MA._runtime_namespace())`).
4. **`validation/test32_neo4j_export_to_shards.py`** — five phases: header normalisation; a
   combined export split and re-read by `csv_to_hypergraph` (quoting, BOM, non-ASCII, arrays,
   unlabelled, relationship properties); the bulk variant across several files with
   `build_terms` chain checks (one node per row, one hyperedge per fact, a relationship
   property as a `TYPE:prop` hyperedge the machine can `Compare`); the **real** `sharded_import`
   as a subprocess on the split output and one shard (`Note`) booted alone, its nodes and
   edges counted *by the machine* and its cross-shard stubs checked; and the notebooks + runbook
   (nbformat 4, every code cell compiles, the import paths and CLI switches they use exist,
   `git ls-files` carries no key material). `T32_SKIP_SHARDS=1` skips the 36 s sharding phase.

## Known quirk, documented rather than fixed

`csv_to_hypergraph.canonical_edge_rows` renders a relationship property as a second edge row
`src → (TYPE:prop) → value`, so `sharded_import` sees `1999` (the value of `LIVES_IN.since`)
as a *destination node* and makes a stub for it in the `unlabelled` shard. It is harmless —
the fact is still one hyperedge the machine can match on — and it is the importer's
convention, not the splitter's; changing it would change what `probes/importer_roundtrip_probe.py`
round-trips. Recorded in `colab/README.md`; a future ingest worker may want values as leaves.

## What to look for on the first real run

* The histogram in `split.json` tells you the shard count *before* sharding; a graph with
  one giant label will give one giant shard, and the memory ceiling in §6.8 applies to it —
  a second split key (property, or id range) is the next piece of work if that happens.
* `sharded_import` boots a fresh runtime per shard (~5 s each on 2 vCPU) and writes ~3.5 MB
  of baseline snapshot per shard before any content; a thousand tiny shards is the wrong
  shape, a dozen large ones is the right one.
* The notebook never writes under the repository tree and never needs a certificate; it is
  the *mesh* notebook (`colab/mesh_worker.ipynb`, W20) that carries a bundle.
