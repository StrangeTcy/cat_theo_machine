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
| M5 | `test_milestone_m5_network_distributed_cycles` | skipped — criterion unmet |
| M6 | `test_milestone_m6_network_handle_lifecycle` | skipped — criterion unmet |
| M7 | `test_milestone_m7_coordinator_recovery_equivalence` | skipped — criterion unmet |
| M8 | `test_milestone_m8_remote_policy_cycle` | skipped — criterion unmet |

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

## M5 — 100 consecutive network distributed cycles

**Criterion.** 100 consecutive `net_distributed_cycle`s on 3 loopback nodes,
zero safety refusals, heads identical every cycle.

**Met when** coordinator and two workers execute 100 consecutive network
cycles without safety refusal, all nodes maintaining hash-identical heads
at each cycle.

**Why it is unmet.** Seeded corpora reach quiescence before 100 cycles.
The check verifies loopback mTLS convergence and invariant safety.

## M6 — distributed handle lifecycle

**Criterion.** The full M2 lifecycle (mine -> promote -> retire -> migrate)
executed with generation happening on worker nodes and every activation on
the coordinator, reconstructible from the coordinator chain alone.

**Met when** all 4 stages are completed across the network boundary and
provably recorded in the coordinator Next chain.

**Why it is unmet.** Individual stages exist across network boundaries,
but no single handle has been driven end-to-end through all four stages
in a single networked run.

## M7 — coordinator kill-and-resume equivalence

**Criterion.** A coordinator kill-and-resume inside an M5-style run, with
the final chain equal to an uninterrupted control.

**Met when** resuming from checkpoint after coordinator termination produces
a chain byte-identical to a control run.

**Why it is unmet.** Recovery verification and hash-chain validation are
verified, but full multi-cycle scripted equivalence across the corpus
remains to be benchmarked.

## M8 — remote policy loosening and tightening

**Criterion.** A remote countersigned policy loosening (Step 62) and its
later remote tightening.

**Met when** remote ANNOTATE frames from distinct certificate authorities
loosen a policy class and subsequent remote annotation reverses the change.

**Why it is unmet.** The remote mTLS annotation interface is verified;
end-to-end execution of two-human policy reversal on a live corpus is
deferred.

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

---

## Observed on LAN

Measurements recorded on a three-node local network testbed (`desktop` 192.168.1.10, `laptop-a` 192.168.1.11, `laptop-b` 192.168.1.12):

- Protocol version: `1`
- Cycles completed: `10`
- Final head hash (`desktop`): `5b40e53a3ff6d0c11107cb5b5c98a58a74e5ce6c3217b7b137d5789f2858b1ab`
- Final head hash (`laptop-a`): `5b40e53a3ff6d0c11107cb5b5c98a58a74e5ce6c3217b7b137d5789f2858b1ab`
- Final head hash (`laptop-b`): `5b40e53a3ff6d0c11107cb5b5c98a58a74e5ce6c3217b7b137d5789f2858b1ab`
- Convergence: 10/10 cycles hash-identical across all nodes.
- Disconnect recovery: 1 worker killed at cycle 4, reconnected at cycle 5, converged to coordinator head within 1 round.
- Curator report records contributions from `desktop`, `laptop-a`, and `laptop-b`.

