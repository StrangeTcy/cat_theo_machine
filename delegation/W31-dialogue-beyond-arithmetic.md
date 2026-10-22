# W31 — Tutor and storyteller beyond arithmetic

**Dimension 5 · Phase 6 · Suite slot `test43` · Prereqs W15 ✅ W14 ✅; richer if W30 has run**

Read `delegation/README.md` first. Read DAG §4 W14/W15, §7.4 and §8 (W31). Do not
re-execute `W15-socratic-tutor.md`.

## Where W15/W14 stopped

- Tutor claim grammar is arithmetic-only (`+`, `*`, even/odd/divides/coprime, `if…then`).
  Other goals enter through `Tutor.set_focus_goal` / `assume`.
- Ledger ablation/holdout gates are reported as not run, not simulated.
- Stories narrate whatever receipt they are handed; domain receipts from W8/W10/W6
  mostly do not exist.

## Goal

1. Extend the claim grammar (or the focus-goal path) so a scripted conversation can
   ask about a geometry, Engel, or (if present) FLT *concept that appears in a loaded
   pack*, answered from the machine's representation, not from prose you wrote.
2. Generate a proof story from a real domain receipt if W30 (or W26/W27) has one;
   otherwise from an Engel-pack `monovariant_terminates` step already in `test24`.
   Do not duplicate `story_renderer.py`.
3. Keep the three-way judgement (verified / refuted / undecided). Keep "not
   represented" as a legal answer.

## Done-definition

`validation/test43_dialogue_beyond_arithmetic.py` green. `test24` 85/85, `test14`,
`test11` still green. No per-concept prose in `dialogue.py` (the existing suite pin
must still hold, extended to the new vocabulary).

## Non-goals

LLM-backed dialogue, networked tutor, `core.py`, re-deriving FLT in conversation.
