# Distribution: five tracks, one integrator

INT-owned index for the multi-agent programme. Written against
`5361a87b60159cd295ce622a72dd4ee3c9c3f9fe`, six commits past the frozen tag
`experiment-4-frozen` → `06c0e52ffd5a9206125ccdb207bffc4a14185636`.
It supersedes the draft of this file written at `06c0e52`, which described a
tree that was one commit behind and had no `explanation.py` and no `protocol/`.

Standing constraints (§0 of the v1 charter) are unchanged and apply to every
worker named here.

---

## 0. Inventory at the integration tip

Measured from the tree, not assumed:

| Fact | Value |
|---|---|
| integration tip | `5361a87`, **untagged**, 6 commits past `experiment-4-frozen` |
| frozen tag | `experiment-4-frozen` → `06c0e52` |
| `explanation.py` | exists, 1,012 lines; 6 tests registered at `testsuite.py:17912–17926` |
| `research.py` / `provenance.py` | 4,021 / 1,518 lines |
| `research_protocol.md` | 119 lines; the cross-track index |
| `protocol/` | `README.md` + `S.md`, `E.md`, `F.md`, `G.md`, `I.md`, all stubs |
| `labels.py` | 3,174 lines; partition blocks at 3,158–3,171 |
| `testsuite.py` | 18,407 lines; class blocks at 16,249–16,262; registration blocks at 18,389–18,402; `install_default_tests` at 16,264 |
| `main.py` / `persistence.py` | 5,062 / 2,106 lines; **no partition blocks in either** |
| shard cursor | 295 `TestShardAccept` guards, 295 registrations; `learned_memory_checkpoint_test` sits at cursor index 218 → shard 0 |
| cursor-pinning sentinel | **not landed.** Both `[SHARED]` blocks in `testsuite.py` are empty; no shard or cursor test exists in the tree |
| pre-flight item 1 | closed at `da33a45`: the learned-memory checkpoint failure is nondeterministic under load — not contamination, not volume |
| subset test runner | absent. No name-based selection anywhere in the tree |
| checkpoints | `snapshots/library-only-control.json`, `snapshots/set-b-cumulative.json`, both named in `research_protocol.md` |
| checkpoint verbs | none. No `save checkpoint` / `load checkpoint`, no content-addressed ids |

Withdrawn from the `06c0e52` draft: T2 ("E has no home module") and the claim
that S and E must share one engineer. Both were artifacts of the stale tip.

---

## 1. The integrator rule

**One integration branch. Every worker branches from its tip, pushes to its own
arena branch, and files a merge request in its report. Only the integrator
merges, re-runs the two-shard suite, and cuts tags.**

Proposed integration branch: `arena/01a06274-cat-theo-machine`. It is the
furthest ahead, it carries the partition blocks and the pre-flight closure, and
the suite baseline is being run against it. **Awaiting operator confirmation**;
a different designation is fine, but one has to exist before a third worker is
staffed.

Consequences that follow from the rule and bind today:

- **Workers never cut tags.** That includes the `experiment-5` naming question:
  it is decided at integration, after the suite number, not in a worker's plan
  document. This file names no future tag.
- **No operator session may run on the integration tip as it stands.** It is
  six commits past the frozen tag and untagged, and `research_protocol.md`
  makes a log spanning two tags inadmissible. Sessions run on a cut, after the
  integrator re-cuts and re-baselines.
- **A worker's branch is disposable.** Push every green step; a sandbox reset
  costs the unpushed commit and nothing else.

---

## 2. Where a worker may write

The partition that landed covers the two files that were fought over. It covers
one of the four registration points a new label needs.

| Registration point | File | Partitioned | Rule for a worker |
|---|---|---|---|
| label class definition | `labels.py` (E's are at 3,055+) | no | append at the tail of the class region, before the singleton region |
| label singleton | `labels.py` 3,158–3,171 | **yes** | append inside your own track block only |
| `sync_from_namespace` tuple | `labels.py` 2,473+ | no | **unmarked shared append point** — see D1 |
| `SNAPSHOT_SYMBOL_NAMES` | `persistence.py` 202+ | no | **unmarked shared append point, different file** — see D1 |
| test class | `testsuite.py` 16,249–16,262 | **yes** | your block only |
| test registration | `testsuite.py` 18,389–18,402 | **yes** | your block only, guard every registration |
| talk verb dispatch | `main.py` | no | adjacent-line hazard; request a `[SHARED]` verb table |
| track ledger | `protocol/<T>.md` | **yes** | one file per track; never edit another track's ledger |
| cross-track claims | `research_protocol.md` | integrator | a claim spanning tracks is written once, in the index |

Unpartitioned points are not free-for-all: they are `[SHARED]` requests to the
integrator, never local forks.

---

## 3. Defects found by reading this tree

**D1 — thirteen E labels are missing from both snapshot registration lists.**
`ExplanationPlanLabel`, `CoreIdeaLabel`, `RepresentationShiftLabel`,
`KeyInvariantLabel`, `NaiveFailureLabel`, `BridgeLemmaLabel`, `NeededForLabel`,
`ImportedBecauseLabel`, `OmittedDetailLabel`, `AudienceLevelLabel`,
`ExplanationSpineLabel`, `SpineStepLabel`, `RenderLawLabel` each have a class
(`labels.py:3055+`) and a singleton (`labels.py:3129+`), and none appears in
`labels.sync_from_namespace` (2,473+) or in `persistence.SNAPSHOT_SYMBOL_NAMES`
(202+, 352 entries). The block header the partition commit added says so
explicitly: a new label must reach both or it will not survive a snapshot
round-trip.

Whether that fails loudly or silently is for the integrator to settle by
running the six E tests after a save/load round-trip; this document reports the
omission, not a measured failure. The reason it belongs in a distribution
document is that it is the exact failure mode five tracks will reproduce: the
partition makes one of four registration points safe and leaves three
unmarked, and a worker following the blocks correctly still misses them.

Suggested `[SHARED]` fix, integrator's call: partition `sync_from_namespace`
and `SNAPSHOT_SYMBOL_NAMES` the same way the singletons are partitioned —
per-track tuples concatenated at one point each — so a label added in a track
block cannot be omitted from the other two lists.

**D2 — the cursor-pinning sentinel did not land.** The registration block
header asserts that registering after every existing test keeps
`learned_memory_checkpoint_test` at its current cursor index; nothing in the
tree checks that assertion. Both `[SHARED]` blocks are empty. Until a test pins
the index, the guarantee the partition depends on is a comment.

**D3 — root debris** (T0, below).

---

## 4. Roster

S and E are separable now: separate home modules (`research.py` +
`provenance.py` versus `explanation.py`), separate test blocks, separate
ledgers. What keeps them from colliding is the partition, not a shared
engineer.

| Worker | Kind | Owns | Blind to | Starts when |
|---|---|---|---|---|
| **INT** | integrator | merges, two-shard suite, tag cuts, `research_protocol.md`, this file, `[SHARED]` primitives, D1/D2 | nothing | now |
| **G-eng** | engineer | `planner.py` alternatives, strategy-obligation terms, `packs/engel-*.pack.yaml`, `[G]` blocks, `protocol/G.md` | F content, S mining internals | after the operator names the integration branch |
| **S-eng** | engineer | `research.py` mining/schema, `provenance.py`, `[S]` blocks, `protocol/S.md` | F content | same |
| **E-eng** | engineer | `explanation.py`, render laws, `[E]` blocks, `protocol/E.md` | F content | same |
| **G/I-op** | operator | authors `TrainingRecord`s, curriculum sessions, held-out exam sessions, `protocol/I.md` | F content, the sealed exam list until reveal | after G-eng lands one method |
| **F-op** | operator | decoy control, the one-shot, teaching only on concrete residuals, `protocol/F.md` | everything (§6) | after the decoy and a re-cut |

---

## 5. Staffing order

```text
INT: name integration branch, re-cut, re-baseline
        |
        ├─ G-eng methods ──── G/I-op curriculum records ──┐
        │                                                 ├─► exam sessions
        ├─ S-eng: unblocked now (research.py, provenance, │        │
        │   mining verbs, learned policies all live)      │        ▼
        │                                          derivation volume
        ├─ E-eng: unblocked now (explanation.py Phases 1–3,├──► S rent
        │   six pinned tests) but fixture-starved         └──► E fixtures
        │
        └─ F-op: decoy ──► one-shot   (independent chain, isolated)
```

- **G-eng is on the critical path.** Every derivation S mines and every proof
  E explains comes from a G method closing an I problem.
- **S-eng and E-eng both have real work today** and neither needs the other's
  output, which is the whole argument for separating them.
- **E-eng is starved of fixtures, not of work.** Six tests exist; a held-out
  proof to explain does not. The Phase 4 transfer test waits on G/I-op.

---

## 6. Session parallelism and the F firewall

**Parallel-safe** — different workers, different sandboxes, same cut, each from
its own cold declared checkpoint, each with a contamination-ledger header and a
pre-declared prediction: G/I curriculum sessions; S and E mining, rent, and
explanation-transfer sessions; the F decoy.

**Serial by nature** — cumulative episodes (Regime C), and the IMO exam after
the curriculum completes. One operator, in order, cumulative checkpoint named
in each audit.

**Isolated** — the F one-shot. Blindness is built, not promised: a redacted
clone of the cut, rebuilt per cut.

```bash
git clone --no-local --branch <cut-tag> <remote> f-blind
cd f-blind
rm -rf packs/engel-*.pack.yaml training_records/ logs/ protocol/
rm -f snapshots/set-b-cumulative.json
git commit -am "F-blind: curriculum, records, other-track ledgers, Set-B removed"
git tag f-blind-<cut-tag>
```

Only `snapshots/library-only-control.json` survives. When the one-shot is done,
INT ports `protocol/F.md` back and nothing else. Checkpoints are read-only
published artifacts; two operators never write the same one.

---

## 7. Open items

**T0 — root debris.** `graph.py.txt` (748 KB), `firing.py.txt` (76 KB),
`mining.py.txt`, `language.py.txt`, `deduction.py.txt`, `grammar.py.txt`,
`session.txt`, and `hyge.py`. Five agents grepping this tree will open
`mining.py.txt` and edit a dead file. Move them to `archive/`, do not delete:
they are the Aug 25 uploads and may be the only record of a divergent stack.
`hyge.py` is the string-rewrite session engine from the sieve demo, not
production runtime — quarantine it in `archive/` with a README line saying so,
and leave deletion to the operator. One commit, integration branch, before a
third worker is staffed.

**Runner gap — no name-based test selection.** Still the top throughput item:
every worker pays a full suite run to verify one class. Constraint on the fix,
as specified by the integrator: a name filter must bypass the cursor for
targeted runs while leaving the full-suite cursor path byte-identical, and the
cursor-pinning sentinel must pass in both modes. A filter that perturbs
registration order invalidates the baseline it was meant to speed up. D2 says
the sentinel does not exist yet, so the runner and the sentinel land together
or the runner lands unguarded.

**F1 — no `save checkpoint` / `load checkpoint`, no content-addressed ids.**
Noted only. It is F-tooling, owned by whoever takes F.

---

## 8. Worker report block

Every worker ends every turn with:

```text
agent: <name>
branch: <own arena branch> @ <hash>   branched from: <integration tip> @ <hash>
touched: <files, with the block or module named>
tests: <block/module> N/N green; full suite: run by INT / not run
ready to merge: yes/no   blocked on: <none | SHARED: X | worker Y | re-cut>
measurement produced: none / <session id, classification>
merge request: <files> -> <integration branch>
```

A track with no cross-track flow in either direction for two consecutive turns
is reported as stalled, with the reason.
