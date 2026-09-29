# Researcher-v0 — G6 Inert discovery graph gate report

Status: **G6 complete.** A reporting-only discovery graph now connects delivered task provenance, G4 attempts and outcomes, retained counterexamples, invariant proposals and proofs, G5 certificate use, prune events, and exact-scope invalidations. Every edge carries source artifact path and record-id references. No graph record is admitted, activated, or written to live knowledge.

## 1. Run identity

```text
agent:            Researcher-v0
branch:           arena/01a0eca3-cat-theo-machine
base:             91ddcd5f80d2d138394fc408c4785532864ba8d0
gate:             G6 — inert discovery graph
source tasks:     42 delivered rows, 34 G4 canonical attempts
G4 budget:        32 expansions and 60000 ms per task
G5 prune events:  8
live activation:  none
```

The runner regenerated the bounded machine-term records, rebound every deterministic source artifact byte for byte, required the elapsed-time MINING journal to be present, and wrote only the two G6 reporting artifacts.

## 2. Files added

| File | Purpose |
|---|---|
| `researcher_v0/discovery_graph.py` | Machine-term graph records, source references, bounded builders, JSON renderer, and summary renderer |
| `researcher_v0/run_g6_graph.py` | Bound runner; validates cited G1–G5 artifacts and writes only G6 outputs |
| `researcher_v0/discovery_graph.json` | Inert graph artifact using schema `researcher-v0-discovery-graph/1` |
| `researcher_v0/discovery_graph_summary.md` | Compact node, edge, and coverage summary |
| `researcher_v0/tests/test_g6_graph.py` | Seventeen structural and artifact acceptance tests |
| `researcher_v0/tests/run_g6_tests.py` | Recursive machine-term test runner |
| `researcher_v0/g6_report.md` | This bounded gate report |

No G1–G5 file or artifact was edited.

## 3. Graph model

Nodes and edges are represented as machine `Pair` chains built and traversed by `M.Edge` classes. The serializer is downstream of that term graph and emits JSON with top-level schema, gate, inert marker, counts, nodes, and edges.

Each node contains:

```text
id
kind
label
status
ruleset_version
subject_id
sources
```

Each edge contains:

```text
id
kind
from
to
sources = [{artifact, record_id}, ...]
```

The relation directions are:

```text
child Task          generated_from  parent Task
Task                attempted       Attempt
Attempt             produced        Outcome or reachable-path Certificate
Transition          broke           CandidateInvariant
Transition          produced        BrokenOn
CandidateInvariant  proposed_from   Attempt
CandidateInvariant  proved_by       proved-invariant Certificate
Certificate         used_by         PruneEvent
PruneEvent          produced        endpoint Certificate
endpoint Certificate used_by        later Task
old Certificate     invalidated_by  ScopeMismatch
```

All 173 edges have nonempty source-reference chains. All source and target ids resolve to one of the 172 unique nodes, and all edge ids are unique.

## 4. Source artifacts

The graph cites only delivered Researcher-v0 artifacts:

```text
researcher_v0/tasks/tasks.jsonl
researcher_v0/journals/mining.jsonl
researcher_v0/certificates/baseline_path_certificates.jsonl
researcher_v0/candidates/candidates.jsonl
researcher_v0/candidates/proved_invariants.jsonl
researcher_v0/candidates/refuted_candidates.jsonl
researcher_v0/certificates/prune_events.jsonl
```

A task-parent edge cites both task records. A task-attempt edge cites both the task record and the journal attempt id. Proposal, proof, prune, and invalidation edges cite both sides when those sides occupy separate artifacts. Endpoint certificates cite their containing prune-event records.

The graph neither treats its own output as proof nor replaces archived evidence. It reports links to the records whose checkers and replay procedures were established at G3–G5.

## 5. Graph counts

```text
nodes                 172
edges                 173

Task                   42
Attempt                34
Transition              5
Outcome                 34
CandidateInvariant      8
BrokenOn                 5
Certificate             32
PruneEvent               8
ScopeMismatch            4

generated_from          35
attempted               34
produced                68
broke                    5
proposed_from            8
proved_by                3
used_by                 16
invalidated_by           4
```

The 32 certificate nodes comprise 21 G4 path certificates, three proved invariant certificates, and eight G5 endpoint certificates.

The four `ScopeMismatch` nodes correspond to delivered scope-break rows T0043–T0046. Each row cites an old R_even certificate while carrying changed rule content. The graph records invalidation of that old certificate even where an independently proved certificate for the new exact scope is available. T0044 remains a delivered task node although it shares a canonical id with T0043.

## 6. Required discovery chains

The graph supplies every requested chain:

1. The 35 non-seed tasks link to delivered parent tasks with `generated_from`.
2. Each of 34 canonical tasks links through `attempted` to one MINING attempt, then through `produced` to its journal outcome.
3. Each of five retained transitions links by `broke` to the refuted proposal and by `produced` to its `BrokenOn` witness.
4. Each of three surviving candidates links by `proved_by` to the independent checker certificate.
5. Each proved certificate use links to a G5 `PruneEvent`; that event produces an endpoint certificate used by the later task.
6. Each of four changed-scope task records supplies a `ScopeMismatch` reached from the old certificate by `invalidated_by`.

## 7. Inertness boundary

```text
core.py                         untouched
Programme C                     untouched and not imported
Programme L                     untouched and not imported
admission / activation / rent   not called
live knowledge                  not written
tags                            unmodified
prior-gate files                unmodified
monkeypatching                  none
new general graph substrate     none
```

`discovery_graph.py` is imported only by the G6 runner and G6 test module. No search, checker, admission, or live package imports it. The runner writes only `discovery_graph.json` and `discovery_graph_summary.md` through the existing Researcher-v0 artifact writer.

## 8. Execution and tests

Commands and final results:

```text
cd /home/user
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.run_g6_graph
  graph nodes=172 edges=173
  status: inert reporting graph; no activation or live write

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g6_tests
  passed: 17  failed: 0

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g5_tests
  passed: 17  failed: 0

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g4_tests
  passed: 16  failed: 0

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g3_tests
  passed: 17  failed: 0

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g2_tests
  passed: 16  failed: 0

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g1_tests
  passed: 23  failed: 0

/home/user/.venv/bin/python -m json.tool \
  researcher_v0/discovery_graph.json
  parse: success
```

The G6 suite verifies exact node and edge counts, all required kinds, unique ids, complete endpoint resolution, nonempty source artifact ids, the allowed artifact set, every required relation topology, prior artifact bindings, and byte-exact regeneration of both G6 outputs.

## 9. Constraint verification

The G6-only strict scan returned no code hits for module-level functions, reflection, dynamic hashing, protected imports, monkeypatching, host boolean literals, `while`, line comments, direct comparison operators, direct `EmptyList` identity, or host text search/transformation.

The package-wide scans returned no code hits for module-level functions, reflection, protected imports, or monkeypatch operations. Standing deny-list hits remain confined to `CONSTRAINTS.md`; direct `EmptyList` identity hits remain documentation prose. Generated Python 3.11 caches were removed.

## 10. Artifact result

```text
researcher_v0/discovery_graph.json
schema:      researcher-v0-discovery-graph/1
inert:       true
size:        136121 bytes
JSON parse:  success

researcher_v0/discovery_graph_summary.md
lines:       39
```

G6 is complete and leaves the source tree ready for the separate G7 evaluation gate.
