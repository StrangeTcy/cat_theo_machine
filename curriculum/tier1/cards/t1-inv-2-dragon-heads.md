# Tier1 card — T1-INV-2 (Invariance, dragon heads)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice — UNSOURCED (agent-authored statement; not convertible until operator supplies). Proof-target.

---

## source statement

> A dragon has 100 heads. A knight may cut off 15, 17, 20 or 5 heads, after which 24, 2, 14 or 17
> heads respectively grow back. The dragon dies only if all heads are cut. Prove it cannot die.
> **(UNSOURCED: agent-authored statement, NOT operator-supplied.)**

## target class: proposition

## intended method: Invariance

Method payload signature (verified): `Invariance(observable, moveset)`. Method head
`InvarianceLabel`.

## exact mathematical target

Impossibility. Let h = heads; a move changes h by a net amount. Net changes: cut15/grow24 = **+9**;
cut17/grow2 = **−15**; cut20/grow14 = **−6**; cut5/grow17 = **+12**. Each is divisible by 3. So
`h mod 3` is invariant. Start `h = 100 ≡ 1 (mod 3)`; reachable h always ≡ 1 (mod 3), never 0 — the
dragon (0 heads) is unreachable.

## required domain roles

- the head-count h;
- the four move options (cut/grow pairs);
- the net change per move (the invariant-preserving step);
- `h mod 3` (the invariant observable).

## constructor mapping found in tree (real, cited)

`InvarianceLabel`, `ParityLabel`, `ModuloLabel`, `CardinalityLabel`, `NatLessLabel`, `ExprAddLabel`,
`ExprMulLabel`, `KnowledgeLabel`, `GoalLabel`.

## missing constructors

`HeadCountLabel`, `DragonLabel`, `CutLabel`, `GrowLabel`, `MoveLabel`. (A2 vocabulary. No claim
exist.)

## intended obligation sequence

Invariance proof-closing shape:
1. initial reading (h = 100 ≡ 1 mod 3);
2. preservation (each move's net change is a multiple of 3, so h mod 3 is invariant);
3. target reading (h = 0 ≡ 0 mod 3) — separated;
4. conclusion (unreachable).

## negative controls

- If a move had a net change not divisible by 3, the mod-3 invariant would fail;
- the start 100 mod 3 = 1 (not 0) is what makes 0 unreachable.

## proof-checker evidence required

- net changes +9, −15, −6, +12 all ≡ 0 mod 3;
- h mod 3 invariant; 100 ≡ 1, 0 ≡ 0; unreachability replayed.

## TrainingRecord promotion gate

Convert when Ground 1 clears (head-count/dragon/cut/grow constructors present) AND record loads +
compiles + genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input
