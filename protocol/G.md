# Track G -- Engel strategies as planner methods

Ledger entries for this track. Newest last. See protocol/README.md for
the rules governing entries, and research_protocol.md for cross-track
discipline.

No entries before 2026-09-05.

## 2026-09-05 — G0: the cold-E2 blocker, reproduced and localized

**Predicted.** `protocol/DISTRIBUTION.md` lists
`cold_e2_reaches_snapshot_save_test` as OPEN and says it "blocks G and E":
a cold E2 that never reaches snapshot save is the instrument the
linear-observable work depends on. Prediction before running: the failure
is in the snapshot-save instrumentation, since that is what the test name
asserts and the test passes `snapshot_save_timeout_seconds=0.0`.

**Ran.** Base `768ea6f`, the integration tip, taken into the session branch
by merge `066777f` (clean, zero conflicts; the deletions are `__pycache__`
bytecode and stale search-compare snapshots that the tip's `.gitignore`
removes). Environment is the house recipe — `tools/recover.sh:173-177`
builds `$HOME/.venv` with `pyyaml` and `gmpy2`; this sandbox has python
3.11.2 where `environment.yml` pins 3.12.13, and that mismatch is recorded
rather than repaired. `sh tools/recover.sh --check` reported `AHEAD - HEAD
is past the integration tip`, and the cursor pins re-derived `305 / 218 / 0
PASS`.

    /home/user/.venv/bin/python tools/run_named_tests.py cold_e2_reaches_snapshot_save_test
    PYTHONPATH=/home/user /home/user/.venv/bin/python probes/gtrack_cold_e2.py

**Came back.** Failed, 1 of 1, in 69.9 s (boot 15.3 s, install 53.4 s).
The prediction was wrong and the refutation is the useful part: the
snapshot-save instrumentation works. Of the four markers the test requires,
the third is present at index 4889 and `SnapshotSaveTimeout` propagates.
Markers one and two are absent at `-1`, because the theorem never proves:

    engel_e2: not proved after 24.587838888168335 seconds
    proved 0 / 1 theorem cases during cold boot

The test's first gate (`proved_index == -1`, `testsuite.py:10554`) is what
trips. Gates two, three and four are never reached. So this is not an
instrument defect in the save path and not a `[SHARED]` repair to the
snapshot code; it is a proving failure upstream of everything the test
asserts about saving.

**Mechanism.** `_run_theorem_agenda` (`main.py:478`) calls
`runtime.prove(start, goal, rules, None, phi)` and gets `EmptyList` — not
`Unreachable`, so search exhausts rather than refutes. The machine-rendered
terms, from the probe:

    start: Knowledge([InitialBoard(n), Parity(n, Odd), Terminal(final),
                      Invariant(BlackboardProblem, Parity(BoardSumObservable))])
    goal:  Knowledge([Parity(FinalNumber, Odd)])

Exactly one rule in the pack can conclude the goal:
`invariant_carries_parity_to_final_number`
(`packs/engel-blackboard.pack.yaml:375-393`). Its premises are
`Invariant(BlackboardProblem, Parity(BoardSumObservable))`,
`Parity(BoardSumObservable, p)` and `Terminal(state)`. The start supplies
the first and the third. It does not supply the second: the start asserts
parity of the Char `n`, and the rule demands parity of
`BoardSumObservable`. No rule in the pack takes `InitialBoard(n)` to
`Parity(BoardSumObservable, p)`, so the observable's initial parity is
established nowhere and the bridge rule can never fire.

**Two candidate readings, not yet separated.**

1. *Content gap.* The pack is missing the rule that computes the initial
   board sum's parity from `InitialBoard(n)` and `Parity(n, Odd)`. Under
   this reading the fix is pack content, and pack content is not a G
   surface — `packs/` is outside every track's allowed surface in
   `protocol/DISTRIBUTION.md` §2, so this is a `[SHARED]` request.
2. *D11.* `protocol/D11-REPAIR-SCOPE.md` holds that pack rules compile as
   `premises -> replacement` and that a pack entry compiles its heads to
   `Label` atoms where a session goal carries `Char` atoms, and the two
   never unify. The `Parity(n, Odd)` / `Parity(BoardSumObservable, p)`
   mismatch above is a Char-versus-Label mismatch in exactly that shape.
   DISTRIBUTION.md already records pre-flight item 2 as BLOCKED ON D11,
   with the content port not started.

Reading 2 subsumes reading 1 if it holds, because under D11 no pack rule
could fire on this start state whatever its content. Separating them needs
a run with the D11 surface mapping enabled for this pack, which is D11
work and not G work. Recorded as open, not resolved by assertion.

**Consequence for G1.** The Invariance method is the one method with a live
execution route — `training.py:621`, `StrategyHintObservable(hint)` feeding
`runtime.prove(..., phi)` — and this E2 problem is its only worked example.
The same failure appears on the ingest path, independently:

    1. engel_e2_blackboard_parity: PARTIAL via none in 27.70s
       (planner root Failed, method alternative Failed, derivation retained False)
       reason: obligation [o1, invariant], (Invariant(BlackboardProblem,
       Parity(BoardSum, Odd))), not discharged: Knowledge([Invariant(
       BlackboardProblem, Parity(BoardSumObservable))],) not derivable from
       the meaning structure

That second failure is the mirror image and is worth its own note: the
meaning structure at `training_records/engel_e2_blackboard_parity.yaml:22-34`
*does* carry `Invariant(BlackboardProblem, Parity(BoardSumObservable))` as
its fourth fact, yet the obligation reporting that same atom is refused as
not derivable from it. An atom present in the start state and refused by a
goal naming it is an identity or unification failure, not a missing
premise, and it points at reading 2. Not investigated further this turn.

So extending Divide and Symmetry at `planner.py:1236-1251` would add two
methods to a planner whose only working example cannot close. Building the
expansion on top of an unproven instrument is how a green test gets written
against a route that never runs. G1 is held until this is separated.

**Artifacts.** `logs/gtrack-cold-e2-2026-09-05.log` (full transcript,
marker indices, rendered terms), `probes/gtrack_cold_e2.py` (rerunnable;
read-only, boots the packs and changes nothing).

**Interface inspection, same turn.** `PlannerAlternative` is real and
positional: `PlannerAlternative(parent_obligation_id, method,
child_obligation_ids, status, evidence)` at `planner.py:508`, with
`PlannerAlternativeParent/Method/Children/Status/Evidence` at
`planner.py:544/553/562/571/580`. Methods enter through
`PlannerProblem(mathematical_state, goal, rules, heuristic, methods=None)`
at `planner.py:19`, and `planner.py:15` records that there is no automatic
strategy recognition. No `[SHARED]` request is needed for that interface.
Four of the five G1 method terms already exist with the named arities —
`Extremal` `planner.py:127`, `Symmetry` `:244`, `Pigeonhole` `:258`,
`Divide` `:275` — and `Invariance` has a label (`labels.py:1414`) but no
constructor. `planner.py:1211` states the coverage: "Only Pigeonhole and
Extremal are expanded so far; other method terms are carried but generate
no children." `planner.py` is a byte-identical blob on both lineages, so
none of this changes with the base. The `[G]` partition blocks exist and
are empty: `labels.py:3167`, `testsuite.py:16992` and `:19181`.

**Not built, deliberately.** `DivideObligations`, `SymmetryObligations`,
the two expansion branches, `engel-strategies.pack.yaml`, any G2-G5
content. `Bijection` (`planner.py:288`) and `DoubleCount` (`:303`) already
exist in the tree and G1 excludes both; they were not touched and not
removed. `InductionObligations` (`planner.py:177`) is reached only from
`tools/rung2_gate.py`, never from the expansion site; whether Induction is
a sixth method is the operator's call.
