# CHARTER-v1

> **RECONSTRUCTED. NOT OPERATOR TEXT.**
>
> Written by INT on 2026-09-05. The operator never supplied this document. It
> was assembled only from material quoted inside the two launch-sequence
> packets (fable 5.1 and the qwen 3.8 spawn instructions). Every section below
> is labelled:
>
> - `VERBATIM` — the text appears inside a packet and is reproduced as given.
> - `RECONSTRUCTED` — assembled from fragments quoted across the packets;
>   the ordering and phrasing are INT's.
> - `UNKNOWN` — the packets reference the section but quote nothing.
>
> No agent may treat a `RECONSTRUCTED` or `UNKNOWN` line as settled operator
> law. Where a `RECONSTRUCTED` line and the operator's own instruction
> disagree, the operator's instruction wins. Replace this file wholesale when
> the operator supplies the real text.

Referenced sections in the launch sequence: §0, §1, §3 (S), §4 (E), §5
(F-tools). §2 belongs to CHARTER-v2 and is not in this file.

---

## §0 — Standing constraints (`VERBATIM`)

Both packets state this list identically. It binds every line written in this
repository.

```text
- No core.py edits. No isinstance, hasattr, type, __class__, __new__,
  getattr, callable. No Python lists, dicts, or booleans as machine values.
  No helper functions, module globals, monkeypatching, dataclass, typing
  checks, .results[0], is_var fields, named Var fields.
- No LLM, embeddings, statistical parsing, or host string templates for
  machine utterances.
- Every failure is a machine term. Every claim of "passed" cites a dated
  artifact.
- Record remote tip before work. Never force-push. New tag per code change
  on the frozen line.
- Do not run Python in conda without asking. Do not run Experiment 4.
  Do not explain FLT.
- Banned phrases in prose and commits: "If you want", "matters", "but
  wait", "actually", "honest", "Let me".
```

Two clarifications INT records because the packets are silent and agents will
otherwise diverge:

- **`Every failure is a machine term.`** A test that fails reports a machine
  term naming the failure, not a Python exception and not a host string.
- **`New tag per code change on the frozen line.`** This is stronger than
  "tag when convenient". A commit that changes matcher, search, or planner
  semantics gets its own tag, and operators re-baseline after it.

---

## §1 — Preflight (`VERBATIM`)

INT's first job, one commit named `preflight`, then a tag. Five items, all
recorded before the tag is cut.

```text
1. Surface the swallowed exception.
   In LearnedMemoryCheckpointTest, temporarily replace
   `except Exception: self.result = M.false_value` with a re-raise.
   Rerun the exact 109-predecessor _register_test repro.
   Record the full traceback in protocol/preflight.md (fable 5.1 names the
   path protocol/preflight/exception-traceback.txt).
   Revert the swap.
   Ledger the true mechanism (size threshold, codec type gap, or other)
   as a named defect in protocol/preflight.md.
   If it is a real defect, fix it in a separate commit and re-cut the tag.

2. Verify the A1 producer/consumer pair.
   Construct the proposed nosolutions producer rule and a consumer rule.
   Confirm both compile to MultiRule.
   Confirm at least one is a candidate partial match on the toy goal
   (x + 1 = x).
   Parsing is not evidence. Selection is.
   Record the selection trace in protocol/preflight.md.

3. Verify the negative-control decoy is shape-matched.
   Print the parsed FLT goal term and the decoy goal term side by side.
   Confirm same predicate arity, same case-split shape, same exponent
   position.
   If they differ, write `DECOY REDESIGN REQUIRED` and stop; do not
   redesign it yourself.

4. Full two-shard suite. Record the failure set.

5. Commit as `preflight`. Tag as `preflight-<shortsha>`.
```

After the tag, INT publishes in `protocol/research_protocol.md`:

- the tag name and SHA that Wave 1 engineers branch from;
- an interface-ownership table — file, symbol, owner = INT, change path =
  `[SHARED]` proposal — covering term/contract signatures, `_register_test`
  behavior, the checkpoint codec, provenance classes and learned-memory mask
  semantics, and the rent/counterfactual machinery, **inspected from the code,
  not assumed**;
- the marked-block partition for `labels.py`, `testsuite.py`, `research.py`,
  `main.py`: empty blocks `# --- [S] ---`, `# --- [E] ---`, `# --- [G] ---`,
  `# --- [F] ---` at the end of each relevant section. Commit `partition`,
  re-cut the tag.

**Stop conditions.** Do not begin track work. Do not cut the tag until all
four preflight items are recorded. Do not run Experiment 4. If the swallowed
exception is a real defect, the fix is a separate commit before the preflight
tag, and the preflight tag includes the fix.

---

## §3 — S track (`RECONSTRUCTED`)

Assembled from fable Text #2 and the qwen S text.

**Allowed surfaces.** The `# --- [S] ---` blocks in `labels.py`,
`testsuite.py`, `research.py`; `provenance.py`; `protocol/S.md`. Nothing else.
`main.py` talk dispatch, packs, explanation, planner methods, any FLT content:
forbidden. Shared primitives: write a `[SHARED]` request in `protocol/S.md`
and stop that item; do not fork the primitive.

**Track isolation.** S touches mining/schema, `provenance.py`,
`testsuite.py`. S does not touch `main.py` talk dispatch, packs, explanation,
problem packs, or FLT-adjacent content. S is contracted near-transfer only:
no far transfer, no second-order premises, no cross-domain schemas. S owns
policy induction; G supplies payloads, skeletons, and episodes. S consumes
method payloads; it does not add them.

**Work items, one per turn.**

```text
S1 — Contracts. Reuse the Step-39 contract system. Express
     RelationArity(R, n) and ExtensionalAt(R, position) as contract terms.
     Teach them for Divides and Congruent via the existing rule:/fact: path.
     Test: RelationContractRequiredTest.

S2 — Schema candidates. A second mining stage that fires only when two or
     more already-adopted concrete macro-laws have different relation heads,
     alpha-equivalent dataflow, matching contracts, and at least two distinct
     source goals. Output RelationSchema(relation_var, contract, premises,
     conclusion, evidence). Schemas never enter FireAny.
     Tests: PredicateHeadNotGeneralizedFromOneFamilyTest,
     PredicateSchemaRequiresTwoDistinctHeadsTest, SchemaDoesNotFireDirectlyTest.

S3 — Instantiation. For a target relation with the required contract,
     instantiate a schema to ProposedMacroLaw. The concrete law passes the
     existing held-out validation, rent gate, human approval, and
     learned-memory lifecycle. No new activation path.
     Test: SchemaInstantiatesConcreteLawTest.

S4 — Negative control. Same arity, same argument shape, no ExtensionalAt,
     no instantiation.
     Tests: PredicateSchemaAblationTest, PredicateSchemaResetRemineTest.

S5 — Near-transfer rerun (live, after S1-S4 green). Train Divides and
     Congruent transport motifs. Hold out a third contracted relation. Full
     cycle: absent to long route; enabled to short route; disabled to long;
     reset to gone; re-mine to returns. Record step counts.
```

**Stop.** No far transfer. No second-order premises. No cross-domain schemas.

---

## §4 — E track (`RECONSTRUCTED`)

Assembled from fable Text #3 and the qwen E text.

**Allowed surfaces.** `explanation.py`; render laws; the `# --- [E] ---`
blocks in `labels.py` and `testsuite.py`; `protocol/E.md`. Mining, the
residual compiler, packs, any FLT-shaped goal: forbidden.

**Track isolation.** E touches `explanation.py`, render laws, `testsuite.py`.
E does not touch mining, the research residual compiler, packs, or FLT-adjacent
content. E never touches an FLT-shaped goal. E may explain any proof from
curriculum sessions or from S's test fixtures.

**Work items, one per turn.**

```text
E1 — Held-out transfer test. Take an invariant proof the substrate has not
     seen (a second Engel-style problem, not blackboard parity). Run
     "explain this proof for a student". Acceptance: correct KeyInvariant,
     correct RepresentationShift, every sentence traceable to a derivation
     node or explanation-plan node. Pin as ExplanationHeldOutTransferTest.
     If it fails, the current idea library is a summary generator: ledger
     that and stop the track until fixed. Do not patch the library to make
     E1 pass.

E2 — Dependency explanation. Add NeededFor, ImportedBecause, NaiveFailure,
     BridgeLemma as machine terms populated from derivations and from
     HUMAN_SUPPLIED_TRUSTED_THEOREM provenance. Answer "why did you need
     this lemma?" and "why did direct search fail?" from those terms only.

E3 — Audience levels. ExplainLevel(Student | Mathematician) selects spine
     depth and which OmittedDetail nodes render. Two renderings of the same
     plan, both traceable.

E4 — Second idea. Add exactly one more idea shape (Descent: well-ordering
     plus strictly decreasing measure) with its own held-out test. Not
     Extremal, not Bijection, not RepresentationChange.

E5 — Feed S and F. Every curriculum proof from F's A-sessions and every
     rent-paid macro from S becomes an explanation fixture. Explaining an
     induced macro-law is a valid E target and a cross-track rent test.
```

**Stop.** No FLT explanation. No prose generator. No idea classifier that
returns a label for unrecognized proofs.

---

## §5 — F-tools track (`RECONSTRUCTED`)

Assembled from fable Text #5 and the qwen F-tools text.

**Allowed surfaces.** Checkpoint tooling; the `# --- [F] ---` blocks in
`labels.py` and `testsuite.py`; the grading script; `protocol/F-tools.md`.
Generators, theorem packs, parser branches, any solver code: forbidden.

**Track isolation.** F-tools is a separate engineering role. The blind F
operator (F-op) does not build tools; F-tools does not run sessions. No FLT
names in the grading script; roles only.

**Work items, one per turn.**

```text
F1 — Checkpoint tooling. save checkpoint <name> / load checkpoint <name>
     with content-addressed ids. The audit header must print which
     checkpoint is loaded. Loading never mutates the stored checkpoint; a
     session's output is a new artifact carrying its parent checkpoint id.
     Provide named checkpoints library-only-control, curriculum-a3,
     set-b-cumulative (the latter two as empty declared slots if their
     content does not yet exist; say so in protocol/F.md). Add a test in
     the [F] block that saves, loads, and confirms the printed id matches.

F2 — Grading script. A host-side tool, outside the machine, taking a
     session transcript and the role table from research_protocol.md.
     Emits: role coverage (recall vs discovery); circular-request count;
     computable-request count (must be zero; any nonzero is a defect);
     taught-theorem count by provenance; unlock evidence per teach.
     No FLT names in the script; roles only.

F3 — Negative-control harness. Runs the decoy from preflight through the
     same stall-and-suggest loop and diffs residuals against the target
     session. Substantially identical means the reading is withdrawn.

F4 — Audit of operator sessions. After each A-session and after
     Experiment 4, classify every suggest dependencies output as Regime
     A/B/C or contamination. Verify every teach was preceded by a concrete
     residual. Verify the audit header lists every loaded class. Report
     only; propose no theorems.
```

**Stop.** No generators, no skeletons, no parser branches, no packs. If an
operator session surfaces a defect, ledger it, fix in code only if the defect
is instrument-level, re-cut the tag, and mark the session inadmissible.

---

## Not in this file (`UNKNOWN`)

- **§2, and the G track surfaces.** The launch packets send G-eng to
  `CHARTER-v2.md` §2 and §3, not to this file. Nothing from v2 was quoted.
  See `protocol/CHARTER-v2.md`.
- **The two-pipeline model.** See `protocol/TWO-PIPELINE.md`.
- **The FLT programme's own protocol (A1-A3, Experiment 4, the decoy
  protocol).** Referenced repeatedly, quoted nowhere.

## Provenance of this file

```text
written by:      INT (integrator session, branch-locked to the integration branch)
date:            2026-09-05
source material: fable 5.1 launch sequence; qwen 3.8 spawn instructions
operator text:   none — the operator supplied no charter text in this thread
status:          provisional; replace wholesale when the real text arrives
```
