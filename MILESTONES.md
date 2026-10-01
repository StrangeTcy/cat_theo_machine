# Open-ended operation: the measured criteria

Part 4 of the work plan ends here, at Step 52. This file records what
"open-ended" means for this machine in terms that a test can decide, and
nothing else. Reaching these criteria is not a step on the ladder; it is
the instrument for finding out whether the ladder's hypothesis holds.

Each milestone below is backed by an executable check in `testsuite.py`,
named `test_milestone_*`. A milestone that is not yet met **runs and
reports skipped** — it does not fail the suite, and it is never deleted.
A milestone whose checkable portion regresses returns `false_value` and
fails against its registered expectation.

The distinction is deliberate. "Skipped" means the criterion has not been
demonstrated. It does not mean the criterion has been weakened, and no
milestone here may be re-specified to make it pass.

---

## Status at Step 52

| Milestone | Check | Status |
|---|---|---|
| M1 | `test_milestone_m1_cycles_without_refusal` | skipped — criterion unmet |
| M2 | `test_milestone_m2_handle_lifecycle` | skipped — criterion unmet |
| M3 | `test_milestone_m3_meta_handle_reorders` | skipped — criterion unmet |
| M4 | `test_milestone_m4_policy_loosen_then_tighten` | skipped — criterion unmet |

None of the four is met. That is the honest reading of the machine at
the end of Part 4: every mechanism the milestones depend on exists and
is separately tested, but none of the four end-to-end narratives has
been demonstrated on a corpus.

---

## M1 — sustained operation without refusal

**Criterion.** 100 consecutive `distributed_cycle`s on a seeded corpus
with zero safety refusals and zero regressions, auto-classes only.

**Met when** the cycle loop runs to the cycle cap rather than stopping
early, the Step-49 floor never reports a violation, and no auto-class
result changes across the run.

**Why it is unmet.** The seeded corpora available reach quiescence in a
single cycle — they run out of work before they can demonstrate
sustained operation. A corpus that stops having anything to do cannot
evidence M1, and counting its early stop as success would make the
milestone meaningless. What the check does verify today is that the
floor is clear at the outset.

**What it needs.** A corpus large enough to keep generating work for 100
cycles. This is a fixture problem, not a mechanism problem.

## M2 — a complete handle lifecycle

**Criterion.** At least one mined handle promoted, later retired, then
migrated, entirely through proposals, with the full lifecycle
reconstructible from the `Next` chain alone.

**Met when** a single handle can be traced through all four stages in
one provenance chain, with no stage performed by host code.

**Why it is unmet.** Each stage exists and is tested individually —
mining (Step 27/28), promotion, retirement (Step 33), migration (Step
41) — but no run has carried one handle through all four. The
reconstructible-from-`Next`-alone requirement is the strict part: it
forbids reading the outcome from a ledger or a report.

## M3 — a meta-handle that measurably biases generation

**Criterion.** At least one meta-handle whose prior measurably reorders
generation, asserted on report ordering, with the meta-handle itself
visible in the self-model.

**Met when** a generator's output *order* changes under the prior while
its output *set* does not, and the same meta-handle appears in
`SelfModelVersion`.

**Why it is unmet.** `OrderByPriors` is built and verified — the check
confirms that a prior moves a matching candidate to the front while
leaving the candidate set intact — but the optional `prior_handles`
argument has not been threaded into the generators. Doing so requires
showing that Step 43's sliced union stays byte-identical to an unsliced
run, which has not been demonstrated.

## M4 — policy loosened, then tightened back

**Criterion.** A policy loosening executed via the countersigned path,
and later reversed via the single-approval tightening path.

**Met when** both directions run through `activate_proposal`'s
`policy_change` gate, the loosening refused without a second independent
authority and the tightening accepted with one approval.

**Why it is unmet.** The gate exists (Step 37) and the safety floor's
precedence over it is verified — the check confirms an approved proposal
is refused while a bound is violated and activates once the bound is
raised — but no session has driven a real loosening and its reversal
end to end.

---

## What Part 4 does not do

The following are explicitly out of scope and were not implemented:

- removing or bypassing the safety floor;
- worker-side activation of any kind;
- non-determinism anywhere;
- formula changes disguised as weight changes — the scheduler's formula
  is fixed host code, and only its two Nat weights are machine-visible;
- network transport — the Step-42 wire format is ready and is the
  portability boundary, but sockets and consensus are an infrastructure
  project to be specified only after M1–M4 hold;
- rehosting off CPython, for the same reason.

## One measured defect, carried forward

`NatFromRep` builds a unary Peano chain, one allocation per unit, and
its cost grows worse than quadratically: n=10 takes 0.67 s, n=20 2.2 s,
n=40 8.0 s, n=80 33.7 s. `PatternCensusMatchCount` converts
`CENSUS_MATCH_CAP` this way on every call, which is 53 of the 63 seconds
a single census over a 24-node self-model costs — spent before any match
is attempted. The cached `MineNatFromGMPRep` is flat at roughly 20 µs at
any magnitude.

This is not a constant-factor complaint. Raising any `*_SCAN_CAP`
currently makes the machine dramatically slower without it doing more
work, and it is the reason M1 and M3 are expensive to demonstrate. The
substitution has not been made: the census compares the cap with
`M.NatEq`, and whether a cached atom is interchangeable there needs a
probe rather than a reading.
