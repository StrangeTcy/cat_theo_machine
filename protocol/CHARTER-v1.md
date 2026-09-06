# Unified Arena-Agent Charter v1: Three Tracks, One Instrument

> Operator-pasted text, committed 2026-09-06 as the track/track-F ruling
> source. Where this file's prose names a surface that does not exist in
> the tree, protocol/LAUNCH-PLAN.md §3 (R1–R11) carries the ruling; the
> rulings amend, they do not erase.

## 0. Standing constraints (apply to every track)

- No `core.py` edits. No `isinstance`, `hasattr`, `type`, `__class__`, `__new__`,
  `getattr`, `callable`. No Python lists, dicts, or booleans as machine values.
  No helper functions, module globals, monkeypatching, `dataclass`, typing
  checks, `.results[0]`, `is_var` fields, named `Var` fields.
- No LLM, embeddings, statistical parsing, or host string templates for
  machine utterances.
- Every failure is a machine term. Every claim of "passed" cites a dated artifact.
- Record remote tip before work; never force-push; new tag per code change
  on the frozen line.
- Do not run Python in conda without asking. Do not run Experiment 4.
  Do not explain FLT.
- Banned phrases in prose and commits: "If you want", "matters", "but
  wait", "actually", "honest", "Let me".

## 1. Pre-flight (do this first, one commit, before any track work)

1. **Surface the swallowed exception.** In `LearnedMemoryCheckpointTest`,
   temporarily replace `except Exception: self.result = M.false_value` with a
   re-raise. Rerun the exact 109-predecessor `_register_test` repro. Record
   the traceback. Revert the swap. Ledger the true mechanism (size threshold,
   codec type gap, or other) as a named defect. If it is a real defect, fix
   it in a separate commit and re-cut the tag.
2. **Verify the A1 producer/consumer pair compiles and is selectable.**
   Construct the proposed `nosolutions` producer rule and a consumer rule;
   confirm both compile to `MultiRule`, and confirm at least one is a
   candidate partial match on the toy goal (`x + 1 = x`). Parsing is not
   evidence; selection is.
3. **Verify the negative-control decoy is shape-matched.** Print the parsed
   FLT goal term and the decoy goal term side by side. Confirm same predicate
   arity, same case-split shape, same exponent position. If they differ,
   redesign the decoy.
4. Full two-shard suite. Record the failure set. Commit `preflight`.

## 2. Track isolation rules

Three tracks share one branch and one tag line. To keep them from
contaminating each other:

| Track | Kind of work | Touches | Must not touch |
|---|---|---|---|
| **S** — self-improvement | code + tests | `research.py` mining/schema, `provenance.py`, `testsuite.py` | `main.py` talk dispatch, packs, explanation |
| **E** — explanation | code + tests + curriculum pairs | `explanation.py`, render laws, `testsuite.py` | mining, research residual compiler, packs |
| **F** — FLT | tooling + audit only | checkpoint tooling, grading script, protocol doc | any generator, any theorem pack, any parser branch |

- One commit per track per turn, labeled `[S]`, `[E]`, `[F]`.
- Track F never adds domain content to code. All mathematics enters through
  operator live sessions.
- Induced laws from S are `INVENTED_LEMMA`; they may be present in F
  sessions only under `full-audited` profile, listed in the audit, and
  ablatable. They are never `LIBRARY_THEOREM`.
- E may explain any proof from curriculum sessions or from S's test
  fixtures. E never touches an FLT-shaped goal.

## 3. Track S — contracted relation schemas (narrow option 2)

Goal: cross the predicate-identity wall without freeing predicate heads.

**S1 — contracts.** Reuse the Step-39 contract system. Express
`RelationArity(R, n)` and `ExtensionalAt(R, position)` as contract terms.
Teach them for `Divides` and `Congruent` via the existing `rule:`/`fact:`
path.

**S2 — schema candidates.** Add a second mining stage that fires only when
two or more *already-adopted* concrete macro-laws have different relation
heads, alpha-equivalent dataflow, matching contracts, and at least two
distinct source goals. Output
`RelationSchema(relation_var, contract, premises, conclusion, evidence)`.
Schemas never enter `FireAny`.

**S3 — instantiation.** For a target relation with the required contract,
instantiate schema → `ProposedMacroLaw`. That concrete law passes the
existing held-out validation, rent gate, human approval, learned-memory
lifecycle. No new activation path. Test: `SchemaInstantiatesConcreteLawTest`.

**S4 — tests.** `PredicateHeadNotGeneralizedFromOneFamilyTest`,
`PredicateSchemaRequiresTwoDistinctHeadsTest`, `RelationContractRequiredTest`,
`SchemaDoesNotFireDirectlyTest`, `SchemaInstantiatesConcreteLawTest`,
`PredicateSchemaAblationTest`, `PredicateSchemaResetRemineTest`. The key
negative: same arity, same argument shape, no `ExtensionalAt` → no
instantiation.

**S5 — near-transfer rerun, live.** Train `Divides` and `Congruent`
transport motifs; hold out a third contracted relation. Full cycle: absent
→ long route; enabled → short route; disabled → long; reset → gone;
re-mine → returns. Record step counts.

**Stop:** no far transfer, no second-order premises, no cross-domain schemas.

## 4. Track E — explanation substrate, Phase 4 onward

Goal: prove the substrate explains rather than summarizes.

**E1 — held-out transfer test.** Take an invariant proof the substrate has
not seen (a second Engel-style problem, not blackboard parity). Run
`explain this proof for a student`. Acceptance: correct `KeyInvariant`,
correct `RepresentationShift`, every sentence traceable to a derivation node
or explanation-plan node. Pin as `ExplanationHeldOutTransferTest`. If it
fails, the current idea library is a summary generator; ledger that and stop
the track until fixed.

**E2 — dependency explanation.** Add `NeededFor`, `ImportedBecause`,
`NaiveFailure`, `BridgeLemma` as machine terms populated from derivations and
from `HUMAN_SUPPLIED_TRUSTED_THEOREM` provenance. Answer
`why did you need this lemma?` and `why did direct search fail?` from those
terms only.

**E3 — audience levels.** `ExplainLevel(Student | Mathematician)` selects
spine depth and which `OmittedDetail` nodes render. Two renderings of the
same plan, both traceable.

**E4 — second idea.** Add exactly one more idea shape (Descent:
well-ordering + strictly decreasing measure), with its own held-out test. Do
not add Extremal, Bijection, or RepresentationChange yet.

**E5 — feed S and F.** Every curriculum proof from F's A-sessions and every
rent-paid macro from S becomes an explanation fixture. Explaining an induced
macro-law ("this shortcut exists because these three steps always
co-occur") is a valid E target and a cross-track rent test.

**Stop:** no FLT explanation, no prose generator, no idea classifier that
returns a label for unrecognized proofs.

## 5. Track F — FLT programme tooling and audit (agent builds tools; operator runs sessions)

The agent does not run A1–A3 or Experiment 4. The agent makes them runnable
and auditable.

**F1 — checkpoint tooling.** `save checkpoint <name>` / `load checkpoint <name>`
with content-addressed ids; audit must print which checkpoint is loaded.
Provide `library-only-control`, `curriculum-a3`, `set-b-cumulative` as named
checkpoints.

**F2 — grading script.** A host-side tool (outside the machine) that takes a
session transcript and the role table from `research_protocol.md` and emits:
role coverage (recall vs discovery), circular-request count,
computable-request count (must be zero — any nonzero is a defect),
taught-theorem count by provenance, unlock evidence per teach. No FLT names
in the script; roles only.

**F3 — negative-control harness.** Runs the decoy from pre-flight through
the same stall-and-suggest loop and diffs residuals against the target
session. Substantially identical → reading withdrawn.

**F4 — audit of operator sessions.** After each A-session and after
Experiment 4, classify every `suggest dependencies` output as Regime A/B/C
or contamination; verify every teach was preceded by a concrete residual;
verify the audit header lists every loaded class. Report only; propose no
theorems.

**Stop:** no generators, no skeletons, no parser branches, no packs. If an
operator session surfaces a defect, ledger it, fix in code only if it is
instrument-level, re-cut the tag, and mark the session inadmissible.

## 6. Interleaving schedule

Per turn, in this order, skipping a track only if it is blocked on the
operator:

1. **F audit** of any new operator transcript (fast; may reveal defects that
   gate everything).
2. **S** one phase.
3. **E** one phase.
4. **F tooling** one item.
5. Full suite; commit per track; record failure set; re-cut tag only if code
   changed.

Cross-feeds are mandatory, not optional: S mines traces from curriculum
session checkpoints (declared, ablatable); E explains S's adopted macros and
F's curriculum proofs; F's grading script consumes E's `ImportedBecause`
terms to count human-supplied information.

## 7. Report format (every turn)

```text
remote tip before: <hash>   after: <hash>   tag: <name>@<hash>
pre-flight: exception mechanism = <named> | still open
[S] phase: <n>  tests added: <names>  suite: <pass/fail set>
[E] phase: <n>  held-out result: <pass/fail>  fixtures added: <n>
[F] tooling: <item>  audits: <session ids, regime per request>
defects found by running: <numbered list, each with locus>
not built (deliberate): <list>
blocked on operator: <list>
```

## 8. Freeze discipline

- Any code commit re-cuts the tag; sessions log the tag they ran on; a
  session spanning two tags is inadmissible.
- Rent, ablation, reset, re-mine, provenance, and human gating are the shared
  acceptance machinery for all three tracks. No track gets a private
  promotion path.
- The single acceptance sentence for each track:
  - **S:** a held-out proof closes in fewer steps by a law the machine wrote,
    and the speedup vanishes on reset and returns on restore.
  - **E:** a held-out proof's explanation names the right invariant and shift
    with every sentence traceable, and a proof outside the idea library is
    declined, not summarized.
  - **F:** a blind session produces a discovery-eligible request with
    measured unlock, zero computable requests, and residuals distinguishable
    from the decoy's.
