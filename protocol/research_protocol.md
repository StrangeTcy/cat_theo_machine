# Research protocol index

Operational plan: `protocol/LAUNCH-PLAN.md` (unified launch + per-agent
instructions + single-session mode).

Engineering base tags:

- Wave-1 engineering base (code): `eng-base-0-partition@7c62ca2`
  @ `7c62ca2c6b9f12f3f49e44ae1f7b89d6d2c99ced`.
  **Engineers branch `work/<T>/eng-base-0-partition@7c62ca2/r1` from this.**
- Original pre-partition base: `eng-base-0@1374464` @ `137446435362a9727c2f7c181c663adab9d4c357`.
- INT session tip (index + plan, not a code cut): `361f250df4289fd97f7521db851becd7f0dbf1bf` on
  `arena/01a0731d-cat-theo-machine`.

## Merge batch 1 (withdrawn, being redone)

- Candidate SHA (exact): `f9ed7fdb561579578146080254eb096cc77ee667`.
- Item: `[S] s1: relation contract terms for Divides and Congruent`.
- Engineer evidence: `relation_contract_required_test` 1/1 green.
- **TAG WITHDRAWN.** The first report claimed the failure set matched the
  baseline while shard 1 was unmeasured (install abort). The two lines cannot
  coexist: an install abort is the presence of no shard-1 measurement, so the
  comparison was between two non-measurements. The tag `cut-1-f9ed7fd` was
  local/unpushed and is deleted; no remote tag exists. Grounds: charter defect
  class #1 (shard aborts during install) and the preflight-e73d748 precedent.
- Corrected sequence in progress: port D1 (below), rerun both shards, record
  the first complete two-shard measurement on this lineage, then cut and push
  the replacement tag.

Wave 1 measurement tag: none (batch 1 withdrawn until D1 port lands and shard
1 completes). F-op still gated by `protocol/F.md`.

## Merge batch 1, corrected (cut-1 complete)

- Candidate SHA (exact): `bf9da23f71b9b178b7c42983fd053b8c2d50f605`.
- Items:
  - `[S] s1: relation contract terms for Divides and Congruent` @ `f9ed7fd`.
  - `[preflight] ConversePropositionTest guards Understood before navigating
    outcome tails` (D1 port) @ `bf9da23`, cited from
    `arena/01a064d5@3cac74c`.
- D1 port: the three `UnderstoodLabel` guards now run before any outcome
  tail navigation; a non-Understood outcome fails the test instead of
  aborting install. Non-semantic; no matcher/search/planner path changed,
  no new constructors.
- Two-shard rerun on the post-fix candidate (isolated boots, `.venv` Python
  3.11 + gmpy2):
  - shard 0: completed 30.04s, report `converse_default_mode_test`.
  - shard 1: **completed** 30.63s, report
    `heuristic_canonical_knowledge_agreement_test`.
  - `SUITE_DONE`, exit 0. No install abort.
- First complete two-shard measurement on this lineage; baseline hereby
  established:
  1. `converse_default_mode_test` (shard 0)
  2. `heuristic_canonical_knowledge_agreement_test` (shard 1)
- Cross-file touch accepted by S1 rule: `persistence.py` touched to register
  new labels in `SNAPSHOT_SYMBOL_NAMES`, paired with `sync_from_namespace`
  registration in the same commit.
- Measurement tag: **`cut-1-bf9da23` @ `bf9da23f71b9b178b7c42983fd053b8c2d50f605`**.
  Authorizes measurements on the post-fix candidate. Sessions begin from it;
  after any later semantic cut, operators rerun blank controls first.
- S2 base: `cut-1-bf9da23@bf9da23`. S2 remains blocked on the `research.py`
  surface re-map (`[SHARED]` #1).

Wave 1 measurement tag: `cut-1-bf9da23`. F-op still gated by `protocol/F.md`.

INT remote tip before this gate: `d3de45a179cc76b6c157473a3ca8d684dcf91294`.

Charters: `protocol/CHARTER-v1.md`, `protocol/CHARTER-v2.md` @ `6002caf`.

Two-pipeline: `protocol/TWO-PIPELINE.md` @ `d3de45a`.

D11: `protocol/D11-PORT.md` — equality-head vocabulary alignment only.

Second pack: paused.

Agents do not run A1–A3 or Experiment 4.

## Preflight

Status: **engineering unblocked**. Items 1 and 2 closed. Item 3 decoupled
to F-op. Two-shard suite recorded.

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

## Marked-block partition

Inserted (module scope, at end of each file):

- `labels.py`: `# --- [S] ---`, `# --- [E] ---`, `# --- [G] ---`, `# --- [F] ---`
- `testsuite.py`: `# --- [S] ---`, `# --- [E] ---`, `# --- [G] ---`, `# --- [F] ---`
- `main.py`: `# --- [S] ---`, `# --- [E] ---`, `# --- [G] ---`, `# --- [F] ---`
- `research.py`: **absent at this lineage**. No `research.py` exists on the
  `eng-base-0@1374464` tree. Phases that list `research.py` among allowed
  surfaces must re-map onto actually-present files before the track starts;
  open the re-map as a [SHARED] request for the affected phase.

Boundary rule: the four markers are empty. A track may append below its own
marker only. The marker itself and the code above it are owned by INT.

`py_compile` green on the three inserted files. Full two-shard rerun was
blocked in this sandbox: `hyge` package import requires `gmpy2`, which the
system Python here does not provide and the protocol forbids running conda
without operator consent.

Open `[SHARED]` requests carried by this index (do not implement in a track):

1. `research.py` absent — re-map S/G surfaces onto present files.
2. `explanation.py`/`provenance.py` absent — re-map E surfaces; entry point
   is `Runtime.explain` (`runtime.py`) / `ExplainDerivation` (`proof.py`).
3. Planner method-set divergence — tree already has `Extremal`, `Induction`,
   `Symmetry`, `Pigeonhole`, `Divide`, `Bijection`, `DoubleCount`;
   `labels.py` has `InvarianceLabel`. G must not silently delete extras.
4. `protocol/D11-PORT.md` referenced but not present in the pulled set.
