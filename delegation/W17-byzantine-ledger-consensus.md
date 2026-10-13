# W17 — Byzantine ledger consensus & monotonic snapshot broadcast

**Swarm · Phase 3 · Suite slot `test28` · Prereqs: W2 ⬜ (open) · W12 ✅ · W1 ✅**

Read `delegation/README.md` first — shared invariants, environment facts and pitfalls are
binding here.

**Sequencing:** W2 (`delegation/W02-rpc-mtls-mesh.md`) is not implemented — `networking/` and
`mesh.py` do not exist. The consensus *algorithm and its verification* can be built now
against in-process peers; the broadcast-over-mesh half waits for W2. Do not reimplement W2's
transport.

## What already exists

- `promotion_ledger.py` — the dual-ledger promotion loop, verified by
  `test9_autonomous_promotion_loop.py`. Two properties are load-bearing and must not be
  weakened: a ledger entry **requires an Independent Checker B receipt** over a
  machine-verified derivation, and **ledger version is monotonic**. Accessors include
  `PromotionLedgerSearchPolicies` and `LedgerEntryCandidate`.
- `checker_b.py` — the receipt verifier, including knowledge-rewrite (fact-list) steps and
  `FactsCover`-style knowledge goals (`test5`, `test19`). In a Byzantine setting this is your
  only trustworthy oracle: a peer's *claim* is worthless, its *receipt* is checkable locally.
- `persistence.py` — the snapshot codec. `promotion_ledger` is already a captured root
  (alongside `planner_state`, `graph_tasks`, `invariant_catalog`, and now hypergraph
  `nodes`/`edges`), so ledger state survives cold resume. `test12` probe 6 is literally
  "Promotion Ledger Round-Trip & Version Monotonicity".
- `graph.py` — `GraphVersion` and version handling; this is the monotonic clock you will
  broadcast.
- `evaluator.py` — ablation trials and holdout regression gates (`test7`): the evidence layer
  that decides whether a promoted macro actually helps.
- `invariant_miner.py` — produces the candidates the ledger judges (`test8`).

`consensus/ledger_sync.py` **does not exist** — the DAG names it as your deliverable.

## Goal

1. **Agreement on ledger state** across peers that may be faulty or malicious: every honest
   peer ends with the same ledger version and the same ordered entry list.
2. **Monotonic snapshot broadcast**: a version never goes backwards, and a peer that receives
   a snapshot older than its own rejects it. This is the property `test12` probe 6 checks for
   one process; you are generalizing it to N.
3. **Byzantine resistance by verification, not by voting count.** The strong version of this
   design — and the one that fits this machine — is that an entry is acceptable iff its
   Checker B receipt verifies *locally* and its ablation evidence satisfies `evaluator.py`.
   A quorum of peers asserting an unverifiable entry must **not** promote it. Build that rule
   first; classical BFT/Raft machinery then only has to order what is already admissible.
   Say clearly in the suite which faults you tolerate (crash, omission, duplicate, reorder,
   forged entry, stale snapshot, split view) and how many.
4. **Rollback**: the DAG calls this a "dual-ledger" with rollback. Define and test what
   rollback means here — an entry retracted without rewriting history (a tombstone at a higher
   version) is the only version-compatible-with-monotonicity option. A ledger that goes back to
   a lower version contradicts §4/W12 and `test12` probe 6.

## Done-definition

- `consensus/ledger_sync.py` reaches agreement among in-process peers under an adversarial
  schedule you control: at least one crashing peer, one delivering out of order, one
  delivering duplicates, and one submitting a **forged entry with no valid receipt**.
- The forged entry is rejected by every honest peer, and the rejection is because the receipt
  failed local verification — assert that reason explicitly, not just the outcome.
- Version monotonicity asserted after every round; no honest peer ever observes a decrease.
- Stale-snapshot rejection demonstrated (a peer handed an older snapshot keeps its newer
  state).
- Rollback via tombstone demonstrated, with history preserved.
- Determinism: same fault schedule → same final ledger. No wall-clock dependence, no
  unseeded randomness.
- Machine purity: ledger entries, versions and receipts are machine terms; §5.2 applies to
  anything in the machine's runtime path. Plain Python for message scheduling is fine — keep
  the boundary explicit.

## Files

- New: `consensus/__init__.py`, `consensus/ledger_sync.py`,
  `validation/test28_byzantine_ledger_consensus.py`.
- Extend: `promotion_ledger.py` (only additively — `test9` must stay green), `persistence.py`
  (only if a consensus root must be captured; remember §5.5, unregistered state evaporates on
  reload), `main.py` (a consensus CLI mode).
- Do not edit `core.py`. **Do not weaken `checker_b.py` or the ledger's receipt requirement** —
  the receipt requirement is the whole security model of Dim 4, and W6's history shows the
  ledger refusing an unreceipted discovery is correct behaviour, not a bug to fix.
- Keep run artifacts out of git.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test28_byzantine_ledger_consensus.py`
green, plus all existing suites green (19 at the time of writing; check `validation/` for the
current highest slot). Highest regression risk: `test9` (promotion loop), `test12`
(persistence cold resume — 7 probes, and it needs the committed fixture
`snapshots/hyge_snapshot_current.json` to exist), `test5`/`test19` (Checker B), `test7`
(evaluator/ablation). Bind any sockets to port 0. Keep the suite under ~150 s.

## Non-goals

Internet-scale consensus, cross-host deployment, the RPC/mTLS transport (W2's brief), search
partitioning (W16's brief), cryptocurrency-style incentive design, and `core.py` edits.
