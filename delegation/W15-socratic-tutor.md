# W15 — Conversational Socratic tutor & concept explorer

**Dimension 5 · Phase 2 · Suite slot `test24` · Prereqs W5 ✅ W12 ✅ (done)**

Read `delegation/README.md` first — shared invariants, environment facts and pitfalls are
binding here. This is the only Phase-2 worker still open, and both of its prerequisites are
done, so it can start immediately.

## What already exists

- `surface_bridge.py` — the declarative surface↔graph bridge, verified by
  `test11_surface_language_bridge.py`. It already has `SurfaceToken`, tokenizer/render
  machinery, `RenderConceptExplanation`, and `QueryConceptDefinition`. The newer lineage
  refactored its token→string path into a `_tokens_to_string` helper — reuse it, do not
  rewrite the loop.
- `story_renderer.py` — `RenderProofStory`, `FormatStoryToMarkdown`; verified by
  `test14_proof_story_narrative.py`. Prose about a derivation is already solved; **do not
  duplicate it**. A tutor narrates *questions and concepts*, a storyteller narrates *proofs*.
- `main.py` — the REPL, and a `_check_concept_definition_query(words, std_definitions)` hook
  the newer lineage added, plus `_words_to_token_chain`. Wire into these rather than adding a
  second entry point.
- `promotion_ledger.py` — the shadow ledger of candidate lemmas, with
  `PromotionLedgerSearchPolicies` / `LedgerEntryCandidate` accessors. A tutor should be able
  to show a user what the machine has *proposed but not yet promoted*, and why.
- `evaluator.py`, `invariant_miner.py` — for "what did the machine discover here?" questions.
- `MATHEMATICAL_APPRENTICESHIP_LADDER.md` — the curriculum ladder document; the tutor's
  notion of difficulty should align with it and with `curriculum.py`'s tiers.

`dialogue.py` **does not exist** — the DAG names it as your deliverable.

## Goal

Build `dialogue.py`: an interactive, stateful Socratic layer over the existing bridge.

1. **Concept inspection** — "what is a monovariant?", "what does the machine know about
   parity?" Answered from the machine's own definitions and facts
   (`QueryConceptDefinition`, `RenderConceptExplanation`), never from a prose table you wrote.
   If the machine has no definition, say so — an honest "not represented" is correct behaviour.
2. **Counterexample REPL** — the user proposes a statement; the machine either verifies it
   (Checker B), refutes it by exhibiting a counterexample found through `playground.py`
   sweeps, or reports that it could decide neither. The third answer must be distinguishable
   from the first two; conflating them is the classic failure mode here.
3. **Socratic progression** — rather than stating a result, ask the next question: which
   quantity is preserved, what happens at the extremal element, which box has two pigeons.
   Questions must be generated from the *structure* of the current graph state (goal shape,
   available rules, discovered invariants), not from a scripted list.
4. **Ledger transparency** — explain the promotion status of a candidate: what receipt it
   lacks, what would earn one.

## Done-definition

- `dialogue.py` drives a full scripted conversation in the suite: concept question answered
  from machine definitions, a counterexample found by sweep for a false claim, a true claim
  verified rather than refuted, and an undecidable-in-scope claim reported as such.
- **Bidirectional paraphrase equivalence** holds: surface → graph → surface round-trips to an
  equivalent statement (`test11` establishes the idiom for this).
- No prose is hardcoded per concept: the suite must include a concept that appears nowhere in
  your source, answered from the machine's own representation.
- The tutor's answers are reproducible — same state in, same answer out. No wall-clock, no
  randomness without a seed.
- The suite states which question classes are handled and which fall through.

## Files

- New: `dialogue.py`, `validation/test24_socratic_dialogue.py`.
- Extend: `main.py` (REPL wiring via the existing hooks), `labels.py` (append-only),
  `surface_bridge.py` (only if a bridge primitive is genuinely missing).
- Do not edit `core.py`. Do not weaken `checker_b.py`.
- Machine purity applies inside `dialogue.py`'s machine-facing code: `Pair`/`EmptyList`/
  `truth_value`, Peano counting, no `isinstance`/`hasattr`/`type` on machine values. Plain
  Python string handling at the I/O boundary is fine — keep the boundary explicit.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test24_socratic_dialogue.py` green, plus
all 19 existing suites green. Highest regression risk: `test11` (surface bridge), `test14`
(story renderer), `test1`/`test4` (planner, if you touch REPL flow), and `main.py`'s
`run self-diagnostics` path, which counts suites and will need its number updated from 14 to
whatever the total is when you land (it currently prints a hardcoded count).

## Non-goals

Proof narration (W14, done), natural-language *proof generation*, any networked or LLM-backed
dialogue (no external hosts are reachable from this sandbox), and `core.py` edits.
