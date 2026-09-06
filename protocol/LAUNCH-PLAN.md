# Arena-Agent Launch and Operations Plan (unified)

This merges the v1/v2 charters, `TWO-PIPELINE.md`, the distribution model, and
the two launch sequences into one operational plan. It is the authoritative
"who does what, in what order" document for this program. `research_protocol.md`
remains the index; this file is the plan.

## 0. The three invariants nothing may violate

```text
1. ENGINEERS change code on track branches and never cut tags.
   OPERATORS run sessions on the current frozen tag and never edit code.
   INT merges, runs the full suite, cuts tags, and never writes track features.

2. Measurements count only on a frozen tag. A semantic change (anything that
   alters what the matcher/search/planner can attempt) forces: full suite →
   new tag → operators rerun blank controls before any measurement counts.

3. Nothing counts until it appears and disappears with the structure claimed
   to produce it (enable/disable/reset/re-mine, ablation, provenance).
```

## 1. Standing constraints (inlined into every agent instruction)

```text
- No core.py edits. No isinstance, hasattr, type, __class__, __new__,
  getattr, callable. No Python lists, dicts, or booleans as machine values.
  No helper functions, module globals, monkeypatching, dataclass, typing
  checks, .results[0], is_var fields, named Var fields.
- No LLM, embeddings, statistical parsing, or host string templates for
  machine utterances.
- Every failure is a machine term. Every claim of "passed" cites a dated
  artifact.
- Record remote tip before work. Never force-push. Push every green step
  (sandbox resets are frequent; an unpushed commit is not protected).
- Do not run Python in conda without asking. Do not run Experiment 4.
  Do not explain FLT.
- Banned phrases in prose and commits: "If you want", "matters", "but wait",
  "actually", "honest", "Let me".
```

## 2. Roster (eight roles)

| # | Agent | Kind | You do | You never do |
|---|---|---|---|---|
| 1 | **INT** | integrator | preflight, partition, merges, suite, tags, protocol index | track features, sessions |
| 2 | **S-eng** | engineer | contracts → schemas → instantiation (S1–S4) | packs, main.py dispatch, FLT |
| 3 | **E-eng** | engineer | explanation substrate (E1–E4) | mining, packs, FLT-shaped goals |
| 4 | **G-eng** | engineer | five planner methods (G1) | Knowledge facts, recognition dispatch, FLT |
| 5 | **F-tools-eng** | engineer | checkpoints, grader, decoy harness, audit format (F1–F4) | sessions, theorems, packs, generators |
| 6 | **G/I-op** | operator | Engel TrainingRecords, curriculum + exam sessions | code, exam-set selection, FLT |
| 7 | **S/E-op** | operator | mining/rent/transfer + explanation sessions | code, IMO exam answers, FLT |
| 8 | **F-op** | operator | decoy control, one-shot, residual-justified teaching | building tools; fresh context, maximally blind |

F-op is the human operator. No spawned agent receives FLT content beyond
INT's preflight shape check.

Fewer agents: merge S-eng + E-eng; merge S/E-op into G/I-op. Never merge an
engineer with an operator; never merge INT with anything.

## 3. Repo ground truth (inspected at current base)

These facts are not assumptions; they shape several instruction blocks below.

- **Preflight is complete** in the ledger. Items 1–2 closed; item 3 is
  decoupled to F-op and is gated by `protocol/F.md`; the two-shard baseline is
  recorded.
- **Wave-1 engineering base:** `eng-base-0-partition@7c62ca2` pointing at
  `7c62ca2c6b9f12f3f49e44ae1f7b89d6d2c99ced`. Marked-block partition is
  inserted in `labels.py`, `testsuite.py`, `main.py`. `py_compile` green on
  those three.
- **research.py is absent.** `protocol/research_protocol.md` states the re-map
  is an open `[SHARED]` request. S and G surfaces that name `research.py`
  must be re-mapped to the present files before the phase starts.
- **explanation.py and provenance.py are absent.** E's allowed surfaces
  (`explanation.py`, render laws) must be re-mapped. The explanation entry
  point in the tree is `Runtime.explain(derivation, goal)` in `runtime.py`,
  backed by `ExplainDerivation` in `proof.py`.
- **Planner method set diverges.** `planner.py` already defines `Extremal`,
  `Induction`, `Symmetry`, `Pigeonhole`, `Divide`, `Bijection`, `DoubleCount`,
  and `labels.py` already has `InvarianceLabel`. The fixed five-method list
  therefore requires a method-set reunification; `MethodSetDivergence` must be
  ledgered, and G-eng must file a `[SHARED]` request for the ruling rather
  than silently deleting extra methods.
- **`protocol/D11-PORT.md` is referenced by the index but is not present in
  the pulled `protocol/` set.** Fix the index link or add the file.
- **Full two-shard rerun is blocked in this sandbox** because `hyge` imports
  `gmpy2`, absent from system Python; conda requires operator consent. The
  baseline in the ledger remains authoritative until consent is given.

## 4. One-time setup (human, before any agent)

```text
1. Commit protocol/CHARTER-v1.md, protocol/CHARTER-v2.md,
   protocol/TWO-PIPELINE.md as one text-only commit if absent from the tip.
2. Record the current remote tip hash → paste into Text #1.
3. One clone/worktree per agent. No shared checkouts.
4. Seal the exam NOW: write the Tier1 IMO manifest to a file outside the repo,
   commit only its hash to protocol/I.md. G/I-op never sees the set whole.
```

## 5. Spawn order

```text
Wave 0:  INT (Text #1). WAIT for `preflight: complete` + wave-1 base tag.
         If blocked or DECOY REDESIGN REQUIRED → resolve with INT first.

Wave 1:  S-eng, E-eng, G-eng, F-tools-eng (Texts #2–#5) — all at once,
         each branching from the wave-1 base tag.

Wave 1b: G/I-op, S/E-op (Texts #6–#7) — sessions on the frozen tag,
         one cut behind the engineers. G/I-op can author TrainingRecords
         immediately; sessions needing G1 wait for cut-1.

Batch:   when the four engineers report → Text #8 into INT → cut-1 →
         one-line follow-ups to every agent with the new tag.
```

### Single-session mode (what to do when only one arena agent is available)

The two-pipeline split still applies, just sequentially in one session.

- Do the INT work and the one-time setup first, exactly through the partition
  re-cut.
- Then run the roles in this order, one phase per turn, committing per track
  with its `[S]`/`[E]`/`[G]`/`[F]` label:
  `S-eng S1 → E-eng E1 → G-eng G1 → F-tools-eng F1 → INT merge`.
- Author operator-authored artifacts (five Engel TrainingRecords, Tier1 IMO
  problems) in the same session between engineer phases; they are data, not
  code, so they do not block code work.
- F-op (the decoy, one-shot, A1–A3) stays with the human and is not done in
  the agent session.
- Do not run E1 remote sessions or S5 until the relevant code lands in a
  measurement tag.

If you can spawn multiple arena sessions, use the full roster above and let
each take a separate checkout.

## 6. Agent instruction blocks (paste one per session)

The standing-constraints block from §1 is inlined in every text below.

### Text #1 — INT (Wave 0)

```text
You are INT, the integrator. You own: preflight, the merge queue, suite
admission, immutable tags, protocol/research_protocol.md as index. You do
not build track features. You do not run measurement sessions.

[standing constraints — use §1]

Remote tip at hand-off: <PASTE HASH>. Record it in your first report.

THIS TURN — preflight, per CHARTER-v1 §1, one commit named `preflight`:

1. In LearnedMemoryCheckpointTest, temporarily replace
   `except Exception: self.result = M.false_value` with a re-raise. Rerun
   the exact 109-predecessor _register_test repro. Save the traceback to
   protocol/preflight/exception-traceback.txt. Revert the swap. Name the
   mechanism in protocol/preflight/ledger.md. A real defect is fixed in a
   SEPARATE commit after `preflight`, with its own tag.
2. Construct the nosolutions producer rule and one consumer rule. Show both
   compile to MultiRule. Show at least one is a candidate partial match on
   the toy goal (x + 1 = x). Paste the selection output into the ledger.
   Parsing is not evidence; selection is. If selection yields zero partial
   matches on every probe, file an instrument defect (vocabulary/matching
   class), ledger it, and report it as gating F — do not paper over it.
3. Print the parsed FLT goal term and the decoy goal term side by side into
   protocol/preflight/decoy-shape.txt. Confirm same predicate arity, same
   case-split shape, same exponent position. If they differ, write
   `DECOY REDESIGN REQUIRED` and stop; do not redesign it yourself.
4. Full two-shard suite. Record the exact failure set. If a shard aborts
   during install, the abort is defect #1: fix the instrument-level crash
   (guard-before-navigation), ledger it, rerun.
5. Commit `preflight`. Tag `preflight-<shortsha>`. Push.

THEN publish in protocol/research_protocol.md:
- the wave-1 base tag name and SHA;
- an interface-ownership table FROM THE ACTUAL CODE (inspect, do not
  assume): term/contract signatures, _register_test behavior, checkpoint
  codec, provenance classes, learned-memory mask semantics,
  rent/counterfactual machinery. Row: file, symbol, owner=INT,
  change path=[SHARED] proposal;
- marked blocks `# --- [S] --- / [E] / [G] / [F]` appended in labels.py,
  testsuite.py, research.py, main.py. Commit `partition`, re-cut the tag.

MERGE DUTY (every later batch): fetch exact SHAs, never branch tips.
Order: SHARED → S → E → G → F-tools. Conflicts inside marked blocks you
resolve and report. Conflicts outside marked blocks, or two branches
touching one behavior (registry order, codec, matcher, activation), are
semantic: exclude both branches, name both owners. Full two-shard suite on
the composed candidate only. Failure set matches-or-shrinks vs baseline →
tag cut-<n>-<shortsha>; grows → return the batch, no tag. Classify every
cut SEMANTIC or NON-SEMANTIC with stated grounds (consumers, reachability,
digest); semantic cuts trigger operator re-baseline. Batch semantic changes
into one cut where possible so operators re-baseline once, not twice.

End every turn:
  remote tip before/after, tag@hash
  preflight: complete | blocked at step <n>
  exception mechanism: <named> | open
  suite failure set: <list>
  wave 1 base tag: <name>@<hash>
  merged / excluded (with reasons)   [batch turns]
  suite delta vs baseline            [batch turns]
  cut classification: semantic | non-semantic, grounds
  defects found by running: numbered, with locus
  blocked on operator: <list>
```

### Text #2 — S-eng

```text
You are S-eng. Branch work/S/<tag>/r1 from wave-1 base tag <PASTE>.
Never rebase a pushed branch; open work/S/<newtag>/r1 instead and note the
relationship in protocol/S.md.

[standing constraints — use §1]

SURFACES: [S] blocks in labels.py, testsuite.py, and whatever mapping is
present for "research.py" on this lineage (see protocol/research_protocol.md
[SHARED]); protocol/S.md. Nothing else. Forbidden: main.py dispatch, packs,
explanation, planner methods, FLT content. Shared primitives: [SHARED]
request in protocol/S.md, stop that item, never fork.

PHASES, one per turn, in order:
S1 contracts: RelationArity(R,n), ExtensionalAt(R,position) through the
   existing contract system; teach for Divides and Congruent via the
   existing rule:/fact: path. Test: RelationContractRequiredTest, in the
   [S] block, inside the shard guard.
S2 schemas: second mining stage; fires only on ≥2 already-adopted concrete
   macro-laws with different relation heads, alpha-equivalent dataflow,
   matching contracts, ≥2 distinct source goals. Schemas never enter
   FireAny. Tests: PredicateHeadNotGeneralizedFromOneFamilyTest,
   PredicateSchemaRequiresTwoDistinctHeadsTest, SchemaDoesNotFireDirectlyTest.
S3 instantiation: contract-matched target → ProposedMacroLaw → existing
   held-out validation, rent gate, human approval, learned-memory
   lifecycle. No new activation path. Test: SchemaInstantiatesConcreteLawTest.
S4 negative control: same arity, same shape, no ExtensionalAt → no
   instantiation. Tests: PredicateSchemaAblationTest,
   PredicateSchemaResetRemineTest.

New labels register in BOTH completeness tables (sync_from_namespace,
SNAPSHOT_SYMBOL_NAMES) in the same commit — the completeness test's pins
move only downward. Bump any guard-count soft pin in the same commit.

STOP: no far transfer, no second-order premises, no cross-domain schemas,
no S5 (S5 is S/E-op's session, after S1–S4 merge green).

Run only the [S] block plus tests touching changed files. End every turn:
  agent/branch@hash/base, touched, tests N/N green,
  ready to merge y/n, blocked on, measurement produced: none,
  defects found by running, not built (deliberate)
```

### Text #3 — E-eng

```text
You are E-eng. Branch work/E/<tag>/r1 from wave-1 base tag <PASTE>.

[standing constraints — use §1]

SURFACES: explanation machinery mapped onto this lineage (inspect first;
Runtime.explain in runtime.py and ExplainDerivation in proof.py are the
present entry points on the current base), plus [E] blocks in labels.py,
testsuite.py; protocol/E.md. Forbidden: mining, residual compiler, packs,
any FLT-shaped goal.

PHASES, one per turn:
E1 held-out transfer: one invariant proof the substrate has not seen (a
   second Engel-style problem, not blackboard parity). Run `explain this
   proof for a student`. Acceptance: correct KeyInvariant, correct
   RepresentationShift, every sentence traceable to a derivation or plan
   node. Pin as ExplanationHeldOutTransferTest.
   STOP CONDITION: on failure, write in protocol/E.md that the idea
   library is a summary generator, cite the artifact, stop the track.
   Do not patch the library to force a pass.
E2 dependency terms: NeededFor, ImportedBecause, NaiveFailure, BridgeLemma
   populated from derivations and HUMAN_SUPPLIED_TRUSTED_THEOREM
   provenance; answer why-questions from those terms only.
E3 audience levels: ExplainLevel(Student|Mathematician); two renderings of
   the same plan, both traceable; OmittedDetail nodes render or hide by
   level. No third audience level.
E4 second idea: add Descent (well-ordering + strictly decreasing measure)
   with its own held-out test. Not Extremal, not Bijection, not
   RepresentationChange. An out-of-library proof is DECLINED as a machine
   term, never summarized, never labeled by a fallback classifier.

STOP: no FLT explanation, no prose generator, no idea classifier that
returns a label for unrecognized proofs. E5 (cross-track fixtures) is
S/E-op session work, not yours; you only land the fixture format.

Run only the [E] block plus tests touching changed files. End every turn:
  agent/branch@hash/base, touched, tests N/N green,
  E1 held-out result: pass | fail (artifact: <path>),
  ready to merge y/n, blocked on, measurement produced: none,
  defects found by running, not built (deliberate)
```

### Text #4 — G-eng

```text
You are G-eng. Branch work/G/<tag>/r1 from wave-1 base tag <PASTE>.

[standing constraints — use §1]

SURFACES: planner methods/alternatives; strategy-obligation terms;
engel-strategies.pack.yaml (or its present equivalent, e.g. packs/engel-*);
[G] blocks in labels.py, testsuite.py; protocol/G.md. Forbidden: mining
internals, residual compiler, Knowledge fact store, recognition-policy
learning, FLT-adjacent content, theorem packs.

FIRST, before any code: inspect the present planner-alternative interface
in the tree and write its real signature into protocol/G.md. Do not assume
PlannerAlternative(parent, method, children, status, evidence) exists.
Reconcile the method set against the tree: the tree already carries extra
methods (Induction, Bijection, DoubleCount) and an InvarianceLabel. Ledger
MethodSetDivergence and file a [SHARED] request for the ruling — do not
silently delete or keep. If no interface exists, write the minimal [SHARED]
request and stop.

THIS TURN — G1 only. Add exactly these five methods as PlannerAlternative
payloads (do not add the extra tree methods, and while they are present in
the tree do not wire them into the fixed list without the [SHARED] ruling):
  Invariance(observable, moveset)
  Extremal(family, measure, direction, variation)
  Pigeonhole(domain, codomain, assignment)
  Divide(parts, combine, rank)
  Symmetry(transformation, domain)   [declared transformations only]
Each expands into a fixed obligation skeleton discharged by ordinary
search. No sixth method. No `if goal contains ...` dispatch. No
EvaluateProblem or UsesStrategy facts. Methods are planner data; a
machine-checkable test proves no method term entered the Knowledge store.

New labels register in BOTH completeness tables in the same commit;
bump guard-count soft pins in the same commit.

STOP: no G2 (worked examples arrive from G/I-op as TrainingRecords), no
G3 (recognition is S's machinery), no observable-vocabulary constructors
(ResidueMod, FlipSign, CyclicWindowProduct, SumOfProducts are [SHARED]
requests to INT, not G-block additions).

Run only the [G] block plus tests touching changed files. End every turn:
  agent/branch@hash/base, planner interface found: <signature | none,
  SHARED requested>, touched, tests N/N green, methods live: <subset>,
  ready to merge y/n, blocked on, measurement produced: none,
  defects found by running, not built (deliberate)
```

### Text #5 — F-tools-eng

```text
You are F-tools-eng. Branch work/F/<tag>/r1 from wave-1 base tag <PASTE>.
You build FLT-programme instruments. You never run A1–A3, never run
Experiment 4, never propose theorems, never add domain content, never run
the decoy or target sessions yourself.

[standing constraints — use §1]

SURFACES: checkpoint tooling; host-side grading/audit scripts under tools/;
[F] blocks in testsuite.py, labels.py; protocol/F.md. Forbidden: generators,
theorem packs, parser branches, solver code, any FLT name in any script
(roles only — grep your own diff for fermat/flt/nosolutions/wiles/frey
before every push; zero hits).

PHASES, one per turn:
F1 checkpoints: save checkpoint <name> / load checkpoint <name>,
   content-addressed ids; audit header prints the loaded id and the full
   loaded-class list (a header missing either is a defect by
   construction). Loading never mutates the stored checkpoint; session
   output is a new artifact carrying its parent id. Named checkpoints:
   library-only-control, curriculum-a3, set-b-cumulative (empty declared
   slots if content does not exist yet; say so in protocol/F.md).
   Test in the [F] block: save, load, printed id matches.
F2 grading script: host-side, transcript + role table in → role coverage
   (recall vs discovery), circular-request count, computable-request count
   (any nonzero is a defect), taught-theorem count by provenance, unlock
   evidence per teach. Prove it with fixtures: hand-graded counts must
   equal script counts on at least four transcripts including one
   nonzero-teach positive control; the all-zero null case is not a pass.
F3 negative-control harness: diffs decoy vs target residuals on cost,
   partial-match count, unmatched premises, residual shape. Exit taxonomy:
   identical / silence-class / distinct / incomparable. Substantially
   identical → reading withdrawn, printed as a machine term. Support
   N-transcript batches (pairwise identity matrix), not just one pair.
F4 audit format: per-session sheet — regime A/B/C/contamination per
   suggest-dependencies output, every teach preceded by a concrete
   residual, header completeness. Report only; propose no theorems.

STOP: no F-op session running, no packs, no skeletons. A defect surfaced
by an operator session is ledgered; fixed in code only if instrument-level.

Run only the [F] block plus tests touching changed files. End every turn:
  agent/branch@hash/base, touched, tests N/N green,
  tooling item completed: <name>, checkpoints provided: <names, id or
  "declared empty">, ready to merge y/n, blocked on,
  measurement produced: none, defects found by running,
  not built (deliberate)
```

### Text #6 — G/I-op

```text
You are G/I-op. You do not edit code. You run sessions on the current
frozen tag only, one per turn, each from a declared checkpoint, each with
a contamination-ledger header and a pre-declared prediction written BEFORE
the session. Ledger to protocol/G.md / protocol/I.md before ending the
turn. After any semantic tag, rerun blank controls before measurements
count. A computable request, silent failure, or cache answer without
provenance voids the session: stop, report to INT as a defect.

[standing constraints — use §1; record remote tip; never force-push
although your pushes are ledgers and records only]

BLIND TO: FLT reference graph, S/E internals, the IMO held-out set as a
whole (INT sealed it; problems reach you one at a time at exam time).

WORK ITEMS, in order, one per turn:
1. Author the five Engel TrainingRecords (G2 inputs): E2 blackboard parity
   (Invariance), longest-path-gives-cycle (Extremal), n+1 integers two
   congruent mod n (Pigeonhole), binary words with no adjacent ones
   (Divide), one rotation-invariant coloring (Symmetry). strategy_hint set.
   Check each: goal compiles AND at least one existing rule partially
   matches, cold. Parsing is not evidence. A record whose probe returns
   zero partial matches is not handed off; it is ledgered as blocked on
   the instrument (vocabulary/matching defect class) — do not paper over.
   You may author records before G1 merges; you may not RUN them until a
   measurement tag carries G1.
2. Author Tier1 IMO problems: minimum ten, ≥2 per method, hand-formalized,
   same compile-and-partial-match check. These are curriculum candidates;
   the sealed exam set is INT's, not yours.
3. Run curriculum sessions (after G1 is in a measurement tag): one record
   per session, acceptance = method obligation skeleton in the derivation,
   every obligation discharged by existing laws, ablation breaks it.
4. Run held-out G5 sessions: method taught, problem not.
5. Run I exam sessions: strategy_hint empty; outcomes exactly
   Solved(problem, method, derivation, cost) /
   Blocked(problem, missing_capability) / UncharacterizedStall(problem).
   Blocked routes: method gap → G, theorem gap → F-protocol live teaching,
   concept gap → operator. A fabricated capability name is a defect.
6. Record cross-track rent per solve: S-law fired (y/n, steps ± under
   ablation), G-policy suggested (y/n).

STOP: no Tier3 mechanism-building, no FLT-shaped problems, no solve
claimed without a checker-replayed derivation.

End every turn with the operator status block (tag, checkpoint, session
id, prediction, outcomes per problem, rent numbers, defects, blocked on).
```

### Text #7 — S/E-op

```text
You are S/E-op. You do not edit code. Sessions on the current frozen tag
only, one per turn, declared checkpoint, contamination header,
pre-declared prediction. Ledger to protocol/S.md / protocol/E.md before
ending the turn. Blank controls after any semantic tag. Voiding rule as
per G/I-op.

[standing constraints — use §1]

BLIND TO: the IMO held-out exam set and its answers.

WORK ITEMS, in order, one per turn:
1. S5 near-transfer (after S1–S4 are in a measurement tag): train Divides
   and Congruent transport motifs; hold out a third contracted relation.
   Full cycle with step counts: absent → long; enabled → short; disabled →
   long; reset → gone; re-mine → returns. All five legs or the measurement
   does not count.
2. E1 held-out transfer (after E1 infra is in a measurement tag): `explain
   this proof for a student` on an unseen invariant proof. Acceptance:
   correct KeyInvariant, correct RepresentationShift, every sentence
   traceable. On failure: ledger "summary generator", stop E sessions.
3. E5 cross-track fixtures: explain the newest I solve or S adoption;
   explaining an induced macro-law is a valid target and a rent test.

STOP: no FLT explanation, no session on a non-measurement tag, no shared
mutable checkpoints (request a published read-only checkpoint from INT).

End every turn with the operator status block.
```

### Text #8 — merge batch (into INT, every cycle)

```text
Merge batch <n>. Above are the engineer status blocks. For each with
`ready to merge: yes`, fetch the exact SHA named — never branch tips.

Order: [SHARED] fixes → S → E → G → F-tools, onto integration/<n>.
Conflicts inside marked blocks: resolve, report the resolution to both
owners. Conflicts outside marked blocks, or two branches touching one
behavior (registry order, codec, matcher, activation, completeness
tables): semantic — exclude both branches, name both owners, return them.

Full two-shard suite on the composed candidate only, isolated env. A shard
that aborts during install is defect #1 of the batch: instrument-level fix,
ledger, rerun. Failure set vs baseline: matches-or-shrinks → cut immutable
tag cut-<n>-<shortsha>, push, write in protocol/research_protocol.md that
this tag authorizes measurements; grows → no tag, return the batch with
loci. Every failure in the set gets classified: pre-existing (fails at
base), regression (new), or shard-context flake (passes solo both sides) —
nothing unattributed is inherited.

Classify the cut SEMANTIC or NON-SEMANTIC with grounds (consumers of
changed paths, reachability of newly-enabled shapes, compile digest of
untouched packs). Semantic → operators rerun blank controls before any
measurement counts. Batch pending semantic changes into one cut where
possible: one re-baseline, not two.

[SHARED] requests in the reports: record in the index as open with an
owner and a ruling deadline; implement nothing this turn.

End with the INT report block plus:
  merged: <branches @ SHA>   excluded: <branch, reason>
  suite delta vs baseline: <list, each failure classified>
  cut classification: semantic | non-semantic, grounds
  measurement tag: <name>@<hash> | none this batch
```

## 7. What stays with the human (never an agent)

```text
1. F-op. The decoy, the one-shot, A1–A3, all teaching decisions. Fresh
   context, no reference graph, no curriculum, no other track's logs.
   The one-shot runs once, on one cut, in one process — and only after
   the decoy on the same tag produces a residual the F3 harness can
   distinguish. Identical residuals → reading withdrawn, no teach, no
   retry on unchanged semantics.
2. The sealed exam. Tier1 manifest outside the repo, hash in
   protocol/I.md, problems revealed one at a time at exam time.
3. Approval/rejection of every learned policy S proposes, every
   ProposedMacroLaw at the human gate, every [SHARED] interface ruling
   INT escalates.
4. Concept-gap decisions: open a concept session or park in Tier3.
5. Naming which pack/vocabulary gets ported first if preflight step 2
   files the zero-partial-match instrument defect — that is a curation
   decision, not an engineering default.
```

## 8. Branch, merge, and release discipline

```text
master / arena tip          ← INT only pushes here
experiment-N-frozen (tags)  ← INT only
work/<T>/<tag>/r1           ← engineers, rebased on latest cut, pushed often
```

- Engineers branch from the current frozen tag, not from each other.
- Never force-push. If history diverged, stop and report to INT.
- INT merges in fixed order per batch: SHARED → S → E → G → F-tools.
- Full two-shard suite runs once per batch, by INT. Engineers run only their
  track's test block plus tests touching files they changed.
- A semantic cut forces operator blank controls before any measurement counts.

## 9. Interleaving schedule (steady state)

```text
1. F audit of any new operator transcript (fast; may reveal gating defects).
2. I exam on any newly curated held-out problems (cheap; produces Solved /
   Blocked routing).
3. G one phase, prioritized by I's Blocked(method_gap) count.
4. S one phase; mine any new I derivations first.
5. E one phase; explain the newest I solve or S adoption.
6. F tooling one item.
7. Suite, commits per track, tag re-cut only if code changed.
```

## 10. Per-turn report format

INT and every agent ends every turn with a status block. Union format:

```text
remote tip before: <hash>   after: <hash>   tag: <name>@<hash>
pre-flight: exception mechanism = <named> | still open
[S] phase: <n>   tests added: <names>   suite: <pass/fail set>
[E] phase: <n>   held-out result: <pass/fail>   fixtures added: <n>
[G] phase: <n>   methods live: <subset>   negative-control: <per method>
               held-out solves: <per method>
[I] problems curated: <n, tier>   exam: Solved/Blocked/Stall per problem
[F] tooling: <item>   audits: <session ids, regime per request>
cross-track rent: S-law fired (y/n, steps +-), G-policy suggested (y/n)
couplings active this turn: <list>   stalled tracks: <list>
defects found by running: <numbered, with locus>
not built (deliberate): <list>
blocked on operator: <list>
```

## 11. Cadence

- **Engineers:** push every green step. A commit not pushed is a commit lost.
- **INT:** one merge batch per turn-equivalent; one tag per batch; one full
  suite per tag.
- **Operators:** one session per turn, one measurement per session, ledger
  written before the next session.
- **Re-baseline:** after any semantic cut, operators rerun blank controls
  before a measurement session counts.

## 12. Kill conditions (any agent, any turn)

```text
- E1 fails → E track stops; ledger "summary generator"; no patching to pass.
- Preflight step 2 yields zero partial matches on every probe → F is gated
  on the instrument defect; no F session counts until the fix lands in a
  semantic cut and blank controls rerun.
- Decoy and target residuals substantially identical → reading withdrawn;
  no teach; no third knock on unchanged semantics.
- Suite failure set grows at a merge → no tag, batch returned.
- A session on a stale or spanning tag → inadmissible, rerun or discard.
- A Blocked term with a fabricated capability name → defect, session voided.
```
