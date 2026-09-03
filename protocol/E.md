# Track E -- explanation substrate

Ledger entries for this track. Newest last. See protocol/README.md for the
rules governing entries, and research_protocol.md for cross-track discipline.

## E1 split declaration -- written before any fixture touches the substrate

The E1 acceptance test is held-out transfer: the substrate must explain an
invariant proof it has not seen. If the candidates are built first and the
held-out one chosen afterward, the choice is contaminated by knowing which
proofs the substrate already handles well. So the split is declared here,
first, and this entry predates every fixture commit on this track.

Candidate proofs, all invariant-shaped, all from packs already loaded:

    C1  blackboard parity            -- already seen; training
    C2  six-sector alternating sum   -- training
    C3  coin-move weighted sum       -- training
    C4  modular residue invariant    -- HELD OUT FOR E1
    C5  descent-flavoured measure    -- reserved for E4, not used in E1

Chosen for a stated reason rather than convenience. C4's invariant is a
residue class rather than a numeric quantity, and its representation shift
runs from a configuration to a residue, so it differs from the trained set on
both axes the acceptance criteria score. C2 and C3 both shift to a numeric
sum, which is closer to C1's parity bit; holding one of those out would be an
easier test, and an easier test here is a worthless one.

C4 must not be rendered, inspected through the substrate, or used to tune a
render law before the E1 run. Building its fixture is permitted; reading its
output is not.

## Acceptance, and what a failure is allowed to mean

E1 passes when the plan names the invariant the derivation actually
preserves, names the representation shift, and every rendered sentence
carries a law name and a source term that occurs in the spine. A sentence
with no source term is a summary.

If E1 fails, the recorded result is that the current idea library summarizes
rather than explains. That is a negative result, written as one, and it gates
E2 through E4 until fixed.

The failure must not be repaired by widening the idea library until C4
passes. That is fitting the test set. A library extension after a failure is
tested against a new held-out proof, never against a retry on C4 -- once
C4's output has been read, C4 is a training fixture forever.

## Coupling: which future exam problems these fixtures serve

Recorded now so the E-to-I coupling exists on paper from the first commit
rather than being asserted later.

    C2, C3  -> Tier1 invariance problems; explanation target after solve
    C4      -> Tier1 modular-obstruction problems
    C5      -> Tier1 descent problems, once E4 adds the descent idea shape

Every solved Tier1 problem becomes an explanation fixture in turn, and its
held-out explanation must name the method and the invariant.
