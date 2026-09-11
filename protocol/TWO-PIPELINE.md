# TWO-PIPELINE — the two-pipeline model

> **Provenance note.** No standalone document named `TWO-PIPELINE` was ever
> supplied, and the launch-sequence citation `d3de45a` is not a valid object
> in this repository. What follows is the two-pipeline model **as stated in
> the operator's distribution section** ("Distributing five tracks across
> agents without breaking the discipline"), reproduced here so that every
> agent reads the same description of the split. It is operator text, not INT
> inference, with the exception of the closing note marked `INT note`.

## The split is not one agent per track

The constraint that makes this hard is not compute. It is that the project's evidence standard depends on **one frozen build** for measurements, while five tracks want to change code at once. So the split is not "one agent per track." It is **two kinds of agent, on two kinds of artifact**:

```text
ENGINEERS  change code on track branches     → produce the NEXT frozen cut
OPERATORS  run sessions on the CURRENT cut    → produce measurements
INTEGRATOR merges, runs the full suite, cuts tags, owns the protocol index
```

Engineers never cut tags. Operators never edit code. The integrator never writes track features. Everything parallel that respects that split is safe; everything that violates it re-creates the contamination and drift problems the project has spent months eliminating.

## The parallelism model

Two pipelines run concurrently, offset by one cut:

```text
cut N (frozen)  ──── operators run sessions ────▶ measurements, ledgers

track branches  ──── engineers build ───▶ INT merges ──▶ full suite ──▶ cut N+1
```

Operators are always one cut behind engineers. That is correct: a measurement is only valid against a frozen build, and the build engineers are changing is by definition not frozen. When cut N+1 lands, operators re-baseline (rerun blank controls — the ladder's standing rule after any semantic change) and continue.

**What this buys you:** engineering on S, E, G proceeds in parallel with G/I sessions on the existing cut, in parallel with F's decoy control. Nothing waits on anything except tag cuts, which are batched.

## Branch and merge discipline

```text
master / arena tip          ← INT only pushes here
experiment-N-frozen (tags)  ← INT only
track/S, track/E, track/G   ← engineers, rebased on latest cut, pushed often
                              (sandbox resets: small commits, push every green step)
```

Rules:

- Engineers branch from the **current frozen tag**, not from each other.
- Engineers rebase onto the new tag after each cut. Never force-push; if history diverged, stop and report to INT.
- INT merges in a fixed order per batch: SHARED → S → E → G. Conflicts are resolved by INT, never by silently taking one side; a conflict in a shared file is reported to both engineers.
- Full two-shard suite runs **once per batch**, by INT. Engineers run only their track's test block plus any test touching files they changed. This is what makes the 25-min shard affordable.

## Conflict hotspots, pre-partitioned

Four files will be fought over. Pre-partition them so merges are mechanical:

| File | Rule |
|---|---|
| `labels.py` | Per-track marked blocks: `# --- [S] ---`, `# --- [E] ---`, `# --- [G] ---`. Append-only inside your block. No edits outside your block. |
| `testsuite.py` | Same marked blocks for test classes and for `_register_test` calls. The shard-guard pattern is preserved; register inside the guard like every existing site. |
| `research.py` / `main.py` dispatch | New verbs and new edges go in a per-track block. Do not touch another track's block. If you need a shared primitive, request it from INT as a `[SHARED]` change; do not fork it locally. |
| `research_protocol.md` | Split it: INT owns `research_protocol.md` as an index; each track gets `protocol/S.md`, `protocol/E.md`, `protocol/G.md`, `protocol/I.md`, `protocol/F.md`. Operators write ledgers into their track's file. INT links them. |

The label/test block partition is the single highest-leverage thing to do first. Without it, every batch merge is a hand-resolved conflict.

## Interfaces frozen across tracks

Engineers build against these; nobody changes them without a `[SHARED]` proposal through INT:

- `PlannerAlternative(parent, method, children, status, evidence)` — G adds methods; S/E consume alternatives.
- Provenance classes (`HUMAN_SUPPLIED_TRUSTED_THEOREM`, `INVENTED_LEMMA`, `LIBRARY_THEOREM`, …) — S adds nothing new without INT sign-off.
- Learned-memory mask semantics (disable/enable/reset) — every learned artifact from every track rides it. S's schema-laws, G's recognition policies, E's adopted render preferences all must pass appear/disappear.
- `TrainingRecord` shape — G/I-op authors against it; G-eng may extend only by appending optional fields.
- Rent gate / counterfactual fork — one implementation, INT-owned.

## Where sessions can and cannot run in parallel

Sessions are cheap to parallelize because each starts cold from a declared checkpoint:

- **Parallel-safe:** G/I curriculum sessions, S/E mining sessions, F decoy — different operators, different sandboxes, same frozen cut, each with its own cold checkpoint and ledger header.
- **Serial by nature:** cumulative sessions that build on a prior session's learned memory (Regime C episodes, IMO exam after curriculum). Those run in one operator's hands, in order, with the cumulative checkpoint named in each audit.
- **Isolated by design:** the F one-shot. One process, one operator, one cut, once.

Operators must never share a mutable checkpoint. If two operators need the same cumulative state, INT publishes it as a named checkpoint artifact and both load it read-only.

## Dependency graph (what blocks what)

```text
SHARED fix (swallowed exception, clean baseline)
   blocks: tag cut N+1 and every "suite is green" claim
   does NOT block: engineering on track branches, sessions on cut N

G-eng planner wiring        blocks: G/I-op curriculum sessions for those strategies
G/I-op curriculum complete  blocks: I exam sessions
S1+S2 (schema + neg control) blocks: S3 far-transfer session
E Phase 4 infra             blocks: E transfer sessions
F decoy                     blocks: F one-shot
any closed proof from G/I   unblocks: E sessions on real proofs, S mining volume
```

The critical path is **G-eng → G/I-op curriculum → I exam**, because that is where proof volume for S and E comes from. Prioritize G-eng staffing.

## Cadence

- **Engineers:** push every green step. Sandbox resets are frequent; a commit not pushed is a commit lost.
- **INT:** one merge batch per day-equivalent; one tag per batch; one full suite per tag.
- **Operators:** one session per turn, one measurement per session, ledger written before the next session.
- **Re-baseline rule:** after any cut that changes matcher/search/planner semantics, operators rerun the three blank controls before any measurement session counts.

## What distribution does not solve

Distribution multiplies engineering and session throughput. It does not shorten the serial chains inside a track — S3 still waits on S2, the exam still waits on the curriculum, the one-shot still waits on the decoy. And it adds one real cost: INT becomes the bottleneck for tag cuts, so INT must be the most disciplined agent, not the most ambitious one. Give INT the shared fix, the merge order, the suite, and nothing creative.

---

## INT note (INT's words, not the operator's)

Two things an agent relying on this file must know about *this* repository:

1. The branch names above are the plan's naming. This integration line is
   `arena/01a06542-cat-theo-machine`, and frozen-line tags are named
   `experiment-N-frozen` (and `experiment-5-frozen-r1`). INT reconciles the
   two when handing out base tags.
2. The parallel-safe/serial classification above assumes each agent has its
   own checkout. Where that is not possible, INT serialises the affected
   work rather than let two roles share a tree.
