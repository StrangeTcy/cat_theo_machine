# Research protocol index

Wave 1 base tag: **none** (preflight blocked).

INT remote tip before this gate: `d3de45a179cc76b6c157473a3ca8d684dcf91294`

Charters: `protocol/CHARTER-v1.md`, `protocol/CHARTER-v2.md` @ `6002caf`.

Two-pipeline: `protocol/TWO-PIPELINE.md` @ `d3de45a`.

D11: `protocol/D11-PORT.md` — equality-head vocabulary alignment only.

Second pack: paused.

Agents do not run A1–A3 or Experiment 4.

## Preflight

Status: **blocked at step 3** (`DECOY REDESIGN REQUIRED`).

Details: `protocol/preflight/ledger.md`

## Interface ownership (inspected on this tip)

Owner = INT. Change path = [SHARED] proposal.

| Surface | File | Symbol |
|---|---|---|
| Planner alternative term | planner.py | `PlannerAlternative(parent_obligation_id, method, child_obligation_ids, status, evidence)` |
| Planner alternative accessors | planner.py | `PlannerAlternativeParent`, `PlannerAlternativeMethod`, `PlannerAlternativeChildren`, `PlannerAlternativeStatus`, `PlannerAlternativeEvidence` |
| Test registration | testsuite.py | `_register_test(graph, name, input_nodes, computation_edge, expected)` — constructs `Test`, updates registry, `graph.add_hypergraph(test)` |
| Default suite install | testsuite.py | `install_default_tests` gated by `TestShardAccept` |
| Graph version / stores | graph.py | `GraphVersion`, `GraphNodes`, `GraphEdges` |
| Persistence I/O | persistence.py | snapshot load/save (no `save checkpoint <name>` talk verbs found) |
| Provenance / learned-memory mask | (absent as named API) | no `LearnedMemoryCheckpointTest`; no named mask module |
| Rent / counterfactual | (absent as named API) | no rent-gate module on this tip |
| Contract system | graph.py | `Contract`, `CompileHandleToLaws` (Step-39 handle contracts) |
| MultiRule | proof.py | `MultiRule` |
| Pack load | packs.py | `PackLoader.load_pack_dict` |

Marked-block partition (`# --- [S] ---` etc.): **not inserted**. Partition
commit waits on a complete preflight tag.
