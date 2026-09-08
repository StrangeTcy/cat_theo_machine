# Tier0 G4 decoy — Invariance / Sikinia parliament (negative-control decoy)

Agent: G/I-op. **Status: blueprint-only, not training input.** G4 decoy (must not fire, or fire and fail rent).

---

## source statement

> Sikinia parliament: each member has at most 3 enemies; split the members into two houses so each
> has at most 1 enemy in its own house.
> (supplied verbatim by operator, G4 decoy list)

## target class: proposition (existence of a partition)

## surface shape (what a method might latch onto)

Repeated-move / reach-a-state language → could trigger **Invariance** (a conserved quantity).

## intended method (the trap): Invariance (decoy)

There is **no conserved quantity**. The correct method is a **strictly decreasing monovariant**
(Descent/Extremal on the same-house-enemy-edge count), NOT a preserved invariant. Invariance must
NOT fire here.

> **Citation:** CUR holds an **E4 oracle card** for this problem on `arena/01a066cf`
> (`CUR-ENGEL-E4-oracle.md`, two-house partition, descent under max degree ≤ 3). Cite, do not
> re-derive the math. The E4 oracle records `H = same-house enemy edges`, `ΔH = e_out − e_in ≤ −1`
> under max degree ≤ 3 — a monovariant (descent), not an invariant (preservation).

## exact mathematical target

A partition into two houses such that every member has ≤ 1 enemy in its own house. The descent:
`H` (same-house enemy edges) strictly decreases under each legal move and is bounded below by 0.

## required domain roles

- enemy graph, max degree ≤ 3;
- two-house partition;
- same-house enemy-edge count `H`;
- legal move (relocate a member with ≥ 2 same-house enemies);
- descent `ΔH = e_out − e_in ≤ −1`.

## constructor mapping found in tree (real, cited)

`ExtremalLabel`, `ExtremalAtLabel`, `ExtremalMaxLabel`, `ExtremalMinLabel`, `HypergraphLabel`,
`VerticesLabel`, `EdgesLabel`, `NatLessLabel`, `BoundedBelowLabel`, `DecreasingLabel`,
`KnowledgeLabel`, `GoalLabel`.

## missing constructors

For a *faithful* record: `GraphLabel`, `VertexLabel`, `EdgeLabel`, `PartitionLabel`,
`HouseLabel`, `SameHouseLabel`, `EnemyLabel`, `DegreeLabel`. (The E4 oracle already names the
descent maths; the *constructors* to express it in-machine are absent — this is the A1
`[SHARED]`-A1 row for graph/partition vocabulary. No claim these exist.)

## negative controls

The invariant-versus-descent distinction IS the control for the Invariance method. A learned
Invariance policy that fires on this decoy and produces a conserved-quantity "solution" is the
failure mode being tested.

## expected policy behavior

- **must not fire**, or
- **fire and fail rent** (the Invariance attempt must not close; the correct Descent route is
  recorded as the right method).

## governance (negative-control framing)

This decoy is inert until a `LearnedMethodPolicy` exists for its target method (Invariance). It
grades the POLICY, not the method payload. A session run against this decoy before S lands policy
machinery measures nothing — there is no policy to fire. Do not record a "the policy did not fire"
as evidence until the policy machinery is landed.

## unsound-derivation risk

A wrong "solve" would **assert a conserved quantity** (e.g. "the number of enemy pairs is
invariant") and then claim the partition exists by preservation. That is unsound — the quantity
is a **monovariant** (decreasing), not invariant. Such a derivation would be a defect, not a
success; the learned policy must fail rent on it.

## proof-checker evidence required

- descent proof: `ΔH ≤ −1` for every legal move, `H` bounded below by 0;
- termination at a partition where no member has ≥ 2 same-house enemies;
- an explicit rejection of the "invariant/preservation" route.

## TrainingRecord promotion gate

G4 decoy — not a curriculum TrainingRecord. It is a negative-control *card* for the learned-policy
rent test. If it is ever converted, it must load + compile + obtain a genuine partial match AND
demonstrate that the Invariance policy does NOT close it.

## current status: blueprint-only, not training input
