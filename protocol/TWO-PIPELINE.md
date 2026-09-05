# Two-pipeline operation (corrected launch plan)

Engineers build the next cut while operators measure a frozen cut.
**Do not dispatch the earlier agent-distribution prompts unchanged.**
Several of those assignments widened the charter; some workflow rules conflicted.

Useful principle: **parallelize implementation and independent sessions;
serialize interface changes, release admission, and evidence promotion.**

This file is the plan. It does **not** claim a repository inspection, test run,
commit, or tag beyond recording the plan. **D11 remains the narrow
head-vocabulary-alignment label. The second pack stays paused.**

---

## 1. Corrections to the distribution proposal

| Issue | Required correction |
|---|---|
| G-eng gets Bijection and DoubleCount; Invariance and Symmetry disappear. | Keep exactly the five v2 methods: **Invariance, Extremal, Pigeonhole, Divide, Symmetry**. |
| G-eng owns recognition-policy learning. | **S owns policy induction** through the existing intervention machinery. G supplies method payloads, obligation skeletons, and episodes. |
| S/E-op runs far-transfer sessions. | S remains **contracted near-transfer only**. No free predicate heads or far-transfer work. |
| Generic engineer prompt permits edits throughout `research.py` and `main.py`. | Each engineer gets an explicit **track-specific allowlist**. Marked blocks do not override the isolation table. |
| Nobody clearly owns F tooling. | Assign an **F-tooling engineer** (may rotate). The blind F operator never builds those tools. |
| Shared defect supposedly does not block track work. | Charter: **preflight comes first**. Do not downgrade that gate to “blocks the next tag.” |
| Engineers must rebase published branches but must never force-push. | **Append-only branches** or new cut-qualified names. Do not rewrite published history. |
| One tag per batch replaces the earlier tagging rule. | Make that an **explicit concurrency amendment**; do not say freeze discipline is unchanged. |

INT cannot both “never write track features” and invent glue for semantic
integration gaps. **Textual merge conflicts stay with INT. Semantic conflicts
return to the owners as a coordinated change.**

---

## 2. Ownership split

Permissions and responsibilities — not necessarily seven continuously active agents.

| Role | Owns | First assignment after preflight |
|---|---|---|
| **INT** | Shared-change coordination, merge queue, suite admission, immutable tags, protocol index | Publish the verified baseline and interface ownership map |
| **S-eng** | Contracts, schema mining/instantiation, learned-policy induction, lifecycle tests | S1 contracts |
| **E-eng** | Explanation substrate, traceable rendering, explanation tests | E1 held-out transfer test; respect its stop condition |
| **G-eng** | The five permitted planner methods and their obligation skeletons | G1 against the inspected planner interface |
| **F-tools** | Generic checkpoint, grading, and negative-control tooling | F1 checkpoint tooling |
| **RUN** | Read-only execution of nonblind curriculum, rent, ablation, and explanation sessions | Run only sessions supported by the frozen cut |
| **Human operators/curators** | Mathematical formalizations, approvals, sealed exam curation, authorized live sessions | Supply and seal the required records |

F-tools may rotate among engineers between assignments. Suite execution can be
automated; INT owns **admission**, not watching a terminal.

**The blind F operator remains separately qualified. Agents do not run A1–A3 or Experiment 4.**

---

## 3. Release workflow

Use **separate worktrees or clones**, not multiple agents editing one checkout.

```text
release cut N ───── read-only session sandboxes ───── dated evidence
      │
      ├── work/S/N/r1 ──┐
      ├── work/E/N/r1 ──┤
      ├── work/G/N/r1 ──┼── integration candidate ── suite ── cut N+1
      └── work/F/N/r1 ──┘
```

### Branch rules

- Every submission names its **base tag and exact commit SHA**.
- Published branches are append-only.
- To move unfinished work onto a newer cut, create a **new branch name** and
  record its relationship to the old submission.
- INT merges **reviewed SHAs**, not moving branch tips.
- Each track retains its separately labeled commit and evidence.

### Freeze amendment (explicit)

> Development and integration-staging commits do not authorize measurements.
> INT publishes an immutable measurement tag only after the exact candidate SHA
> has completed the required suite and controls. Sessions remain pinned to their
> starting tag and checkpoint.

That permits batching without weakening measurement identity.

Run two shards concurrently **in isolated environments**, provided neither
shares mutable state with the other. Run the **full suite on the composed
candidate**, not merely on its individual branches. Any candidate change
requires renewed validation.

A newly published tag does **not** force an ongoing session to migrate. Finish
that session on its original cut. Re-baseline before starting admissible
sessions on the new cut.

---

## 4. Protect evidence, not just files

### Shared-file blocks are merge aids, not isolation

Two agents can edit different blocks and still change the same matcher
behavior, registry ordering, codec, or activation semantics.

Before concurrent implementation, assign ownership of:

- term and contract signatures;
- test registration behavior;
- checkpoint codec compatibility;
- provenance and learned-memory masks;
- rent and counterfactual machinery.

Inspect the existing implementation first. A proposed `PlannerAlternative`
signature is not evidence that this interface already exists in the form needed.

### Seal the formalized exam, not only its problem names

The committed exam manifest should cover statements, formal goals, givens,
partitions, and evaluation policy. Otherwise formalization choices become an
undeclared source of hints.

Keep exam curation outside curriculum development. Once an exam derivation is
released to S or E for training, **retire it from future held-out claims for
the affected component**. It remains useful as a regression fixture.

That retirement rule is essential because v2 requires exam results to feed
learning.

### Define F blinding by permitted information

“Fresh context” is not a complete firewall.

- An operator who knows forbidden reference material is not blinded by launching a clean process.
- A fresh agent context is insufficient when workspace or repository history exposes that material.
- F needs an explicit **information allowlist** consistent with its declared profile — not “blind to everything.”
- Engineers should receive instrument-defect reports without sealed target content wherever that separation is possible.

Do not assume the human operator is eligible merely because the coding agent is not.

### Publish immutable checkpoints

Each session gets a private working copy of a declared checkpoint. Its output
is a **new artifact with a parent checkpoint identifier**; it never overwrites
the shared input.

Cross-track imports occur only through an explicit, audited checkpoint release.
No automatic pickup of another agent’s latest learned memory.

---

## 5. Launch in two waves

### Wave 0: preflight only

INT owns the gate:

1. Capture the swallowed exception’s traceback using the exact repro.
2. Restore the temporary diagnostic change.
3. Ledger the mechanism; make any repair separately.
4. Verify producer/consumer compilation **and candidate selection**.
5. Verify the decoy’s formal shape.
6. Run both suite shards and record the failure set.

Other engineers may inspect and prepare interface questions **read-only**.
They must **not** start speculative implementations around an unresolved
checkpoint defect.

### Wave 1: bounded parallel work

After the gate:

- S: S1.
- E: E1.
- G: G1.
- F-tools: F1.
- Operators: prepare the declared curriculum and sealed exam artifacts.
- RUN: execute only currently supported sessions on the published cut.

Do not assign entire tracks as open-ended mandates. Assign **one phase, one
allowed surface, one evidence requirement, one stop condition**.

The proposed critical path — G wiring → curriculum → I exam — is plausible,
but remains **conditional on preflight and the existing planner**. D11’s
reported head-vocabulary alignment does **not** establish that broader
readiness.

---

## Bottom line

This can scale without five agents racing on one branch. Speedup comes from
isolated engineering, pinned session execution, and a narrow merge queue — not
from relaxing gates or expanding everyone’s permissions.
