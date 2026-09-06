# Distributing five tracks across agents without breaking the discipline

The constraint that makes this hard is not compute. It is that the project's evidence standard depends on **one frozen build** for measurements, while five tracks want to change code at once. So the split is not "one agent per track." It is **two kinds of agent, on two kinds of artifact**:

```text
ENGINEERS  change code on track branches     → produce the NEXT frozen cut
OPERATORS  run sessions on the CURRENT cut    → produce measurements
INTEGRATOR merges, runs the full suite, cuts tags, owns the protocol index
```

Engineers never cut tags. Operators never edit code. The integrator never writes track features. Everything parallel that respects that split is safe; everything that violates it re-creates the contamination and drift problems this programme spent months eliminating.

## Roster (7 agents, or fewer if you double up)

| Agent | Kind | Owns | Blind to |
|---|---|---|---|
| **INT** integrator | integrator | merges, tag cuts, full two-shard suite, `research_protocol.md` index, shared fixes (swallowed exception, registry defect) | nothing |
| **S-eng** | engineer | predicate-head anti-unification, negative control, ablation test | FLT reference graph |
| **E-eng** | engineer | Phase 4 transfer test, presentation graph, render laws | FLT reference graph |
| **G-eng** | engineer | planner-alternative wiring for the five methods, recognition-policy data (not dispatch) | FLT reference graph |
| **G/I-op** | operator | authors Engel `TrainingRecord`s, runs curriculum sessions, runs IMO held-out exam sessions | FLT reference graph, S/E internals |
| **S/E-op** | operator | runs mining / rent / far-transfer / explanation-transfer sessions on frozen cut | curriculum answers for IMO held-out set |
| **F-op** | operator | decoy negative control, the one-shot, teaching only on concrete residuals | **everything**: fresh context, no reference graph, no curriculum, no other track's logs |

F-op is the human operator. The coding agent has seen the reference graph; every engineer above has.

If you have fewer agents: merge S-eng+E-eng (both are small), merge S/E-op into G/I-op. Never merge an engineer with an operator, and never merge INT with anything.

## The parallelism model

Two pipelines run concurrently, offset by one cut:

```text
cut N (frozen)  ──── operators run sessions ────▶ measurements, ledgers

track branches  ──── engineers build ───▶ INT merges ──▶ full suite ──▶ cut N+1
```

Operators are always one cut behind engineers. That is correct: a measurement is only valid against a frozen build, and the build engineers are changing is by definition not frozen. When cut N+1 lands, operators re-baseline (rerun blank controls) and continue.

Engineering on S, E, G proceeds in parallel with G/I sessions on the existing cut, in parallel with F's decoy control. Nothing waits on anything except tag cuts, which are batched.

## Branch and merge discipline

```text
master / arena tip          ← INT only pushes here
experiment-N-frozen (tags)  ← INT only
track/S, track/E, track/G   ← engineers, rebased on latest cut, pushed often
                              (sandbox resets: small commits, push every green step)
```

Rules:
- Engineers branch from the **current frozen tag**, not from each other.
- Engineers never rebase a pushed branch; open `work/<T>/<newtag>/r1` and note the relationship.
- INT merges in a fixed order per batch: SHARED → S → E → G → F-tools. Conflicts are resolved by INT, never by silently taking one side; a conflict in a shared file is reported to both engineers.
- Full two-shard suite runs **once per batch**, by INT. Engineers run only their track's test block plus any test touching files they changed.

## Conflict hotspots and how to defuse them before they happen

Four files will be fought over. Pre-partition them now so merges are mechanical:

| File | Rule |
|---|---|
| `labels.py` | Per-track marked blocks: `# --- [S] ---`, `# --- [E] ---`, `# --- [G] ---`, `# --- [F] ---`. Append-only inside your block. No edits outside your block. |
| `testsuite.py` | Same marked blocks for test classes and for `_register_test` calls. The shard-guard pattern is preserved; register inside the guard like every existing site. |
| `research.py` / `main.py` dispatch | New verbs and new edges go in a per-track block. Do not touch another track's block. If you need a shared primitive, request it from INT as a `[SHARED]` change; do not fork it locally. |
| `research_protocol.md` | Split it: INT owns `research_protocol.md` as an index; each track gets `protocol/S.md`, `protocol/E.md`, `protocol/G.md`, `protocol/I.md`, `protocol/F.md`. Operators write ledgers into their track's file. INT links them. |

The label/test block partition is the single highest-leverage thing to do first. Without it, every batch merge is a hand-resolved conflict.

## Interfaces frozen across tracks

Engineers build against these; nobody changes them without a `[SHARED]` proposal through INT:

- Planner-alternative interface — G adds methods; S/E consume alternatives. Inspect the tree; do not assume a signature.
- Provenance classes (`HUMAN_SUPPLIED_TRUSTED_THEOREM`, `INVENTED_LEMMA`, `LIBRARY_THEOREM`, …) — S adds nothing new without INT sign-off.
- Learned-memory mask semantics (disable/enable/reset) — every learned artifact from every track rides it.
- `TrainingRecord` shape — G/I-op authors against it; G-eng may extend only by appending optional fields.
- Rent gate / counterfactual fork — one implementation, INT-owned.

## Where sessions can and cannot run in parallel

Sessions are cheap to parallelize because each starts cold from a declared checkpoint:

- **Parallel-safe:** G/I curriculum sessions, S/E mining sessions, F decoy — different operators, different sandboxes, same frozen cut, each with its own cold checkpoint and ledger header.
- **Serial by nature:** cumulative sessions that build on a prior session's learned memory (Regime C episodes, IMO exam after curriculum). Those run in one operator's hands, in order, with the cumulative checkpoint named in each audit.
- **Isolated by design:** the F one-shot. One process, one operator, one cut, once.

Operators must never share a mutable checkpoint. If two operators need the same cumulative state, INT publishes it as a named checkpoint artifact and both load it read-only.

## The G ↔ I firewall

The IMO held-out set is the exam. **G/I-op authors Engel curriculum and runs the exam, so G/I-op cannot also choose the exam problems.** Fix: the human or INT selects the IMO held-out set from a sealed list *before* curriculum sessions begin, commit only its hash to the protocol, and reveal problems to G/I-op one at a time only when the exam session runs.

## Dependency graph (what actually blocks what)

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

## Reporting so INT can integrate without reading everything

Every agent, every turn, ends with one block:

```text
agent: S-eng
branch: track/S @ <hash>   rebased on: experiment-6-frozen
touched: labels.py [S block], research.py [S block], testsuite.py [S block]
tests: track block N/N green; suite not run (INT)
ready to merge: yes/no   blocked on: <none | SHARED: X | agent Y>
measurement produced this turn: none / <session id, classification>
```

INT maintains one status table in `research_protocol.md` and cuts a tag when a batch is merged and the full suite matches the declared baseline.

## Cadence

- **Engineers:** push every green step. Sandbox resets are frequent; a commit not pushed is a commit lost.
- **INT:** one merge batch per day-equivalent; one tag per batch; one full suite per tag.
- **Operators:** one session per turn, one measurement per session, ledger written before the next session.
- **Re-baseline rule:** after any cut that changes matcher/search/planner semantics, operators rerun the three blank controls before any measurement session counts.

## Instruction template for a track engineer

```text
You are <TRACK>-eng. Branch track/<TRACK> from the current frozen tag.
You may edit only inside your marked blocks in labels.py, testsuite.py,
research.py, main.py, and your file protocol/<TRACK>.md. Shared primitives
are requested from INT, never forked. All standing constraints apply.
Run only your track's test block plus tests touching files you changed.
Push every green step. Never rebase a pushed branch. End every turn
with the status block. Do not run measurement sessions. Do not cut tags.
Your track's work items and stop conditions are in protocol/<TRACK>.md.
```

## Instruction template for an operator

```text
You are <TRACK>-op. You do not edit code. You run sessions on the current
frozen tag only, one per turn, each from a declared checkpoint (library-only
control or a named cumulative checkpoint), each with a contamination-ledger
header and a pre-declared prediction. Teach only in response to a concrete
residual, one theorem per reason. Write the ledger entry to
protocol/<TRACK>.md before ending the turn. After any new tag, rerun blank
controls before the next measurement. A computable request, a silent
failure, or a cache answer without provenance voids the session: stop,
report to INT as a defect. End every turn with the status block.
```

## What this does not solve

Distribution multiplies engineering and session throughput. It does not shorten the serial chains inside a track — S3 still waits on S2, the exam still waits on the curriculum, the one-shot still waits on the decoy. And it adds one real cost: INT becomes the bottleneck for tag cuts, so INT must be the most disciplined agent, not the most ambitious one. Give INT the shared fix, the merge order, the suite, and nothing creative.
