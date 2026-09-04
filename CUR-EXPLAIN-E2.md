# CUR-EXPLAIN-E2 — Expected Explanation Structure for E2

Scope: **Option B follow-up (read-only).** This is a **target spec** for `E-CODE-EXPLAIN-FROM-PLAN`
to match against — a concrete, machine-grounded expectation, written without redesigning the
explanation substrate and without inventing E2 labels. It is the deliverable of this session's
read-only follow-up; no production code changed.

Grounding: the E2 proof and its rules come from the authoring spec `engel_e2_blackboard.md`
(tip `ef571b688bcfb581bd3e65ec28a18f438ca32595`) and the measured `RewriteSearch` plan
(5 steps, probed from the tree and reported below). All panel constructors named here are the
**real** substrate constructors in `explanation.py` (verified signatures), not new labels.

---

## Ground truth used to build this target

- Proof driver: `RewriteSearch(start, goal, rules, registry)` — closes E2 in **5 steps**
  (measured: `step count: 5`).
- `start = BlackboardStart(OddLabel)`, `goal = Knowledge(Pair(ParityFact(FinalNumberLabel, OddLabel), EmptyList))`.
- Phi (observable) = `Parity(BoardSum, ?p)`.
- Move = `EraseAndReplaceRule`: erases two numbers `a, b`, writes `|a - b|`.
- Invariant discharged once over arbitrary `a, b` by `Preserves(EraseAndReplace, Parity(BoardSum))`.
- Initial parity: `InitialBoardSumRule` (`1+...+2n = n(2n+1)`) → `TwoKPlusOneIsOddRule`
  → `ParityOfProductRule(Odd, Odd, Odd)` → `Parity(n(2n+1), Odd)`.
- Terminal: `TerminalReadoutRule` fires when `Invariant(...)`, current reading `Parity(BoardSum, p)`,
  and `Terminal(state)` are present, and concludes `Parity(FinalNumber, p)`. No bypass path.

### Measured 5-step plan (rule bindings as returned by RewriteSearch)

| step | binding evidence | maps to |
|---|---|---|
| 1 | `[?p, Odd], [?n, n]` | initial parity: `Parity(2n+1, Odd)` |
| 2 | `[?p, Odd], [?k, n], [?x, n], [?state, InitialBoard(n)]` | `ParityOfProductRule` |
| 3 | `[?y, ((2*n)+1)], [?x, n], [?state, InitialBoard(n)]` | `TwoKPlusOneIsOddRule` |
| 4 | `[?p, Odd], [?v, (n*((2*n)+1))], [?state, InitialBoard(n)]` | `ParityOfProductRule` conclusion |
| 5 | `[?state, final], [?p, Odd]` | `TerminalReadoutRule` → `Parity(FinalNumber, Odd)` |

Each step is a `MultiRule` application record (the note in Task A: these are `TheoremActionLabel`
steps, which is exactly why the miner/`BuildPlan` could not consume them).

---

## Expected `ExplanationPlan`

An `E-CODE-EXPLAIN-FROM-PLAN` result for E2 should construct an `ExplanationPlan` matching the
substrate constructor:

```
ExplanationPlan(audience, goal, spine, core_idea, key_invariant)
```

where each field is **non-empty** (a partial plan is allowed by the substrate, but E2 should be
fully characterizable, so all five panels resolve). Concretely:

```
ExplanationPlan(
  audience  = AudienceLevel(Char("student")),
  goal      = Knowledge(Pair(ParityFact(FinalNumberLabel, OddLabel), EmptyList)),
  spine     = ExplanationSpine(goal, steps, baseline_cost),
  core_idea = CoreIdea(goal, idea),
  key_invariant = KeyInvariant(problem, invariant),
)
```

The five human-facing panels are the operator's five slots; each maps to a real constructor and
must be filled with the real E2 content:

### 1. CoreIdea — `CoreIdea(goal, idea)`
- `goal` = `Parity(FinalNumber, Odd)`.
- `idea` = **"Follow the sum, not the individual numbers."** The parity of the board sum is
  unchanged by a move; the last number's parity is read off that single quantity.

### 2. KeyInvariant — `KeyInvariant(problem, invariant)`
- `problem` = `Invariant(BlackboardProblem, Parity(BoardSum))` (the subject of the E2 invariant claim).
- `invariant` = `Parity(BoardSum, p)` — the parity of the board sum is preserved by `EraseAndReplaceRule`.

### 3. RepresentationShift — `RepresentationShift(source, target, reason)`
- `source` = the board as a multiset of individual numbers (the state the move actually changes).
- `target` = `BoardSum(state, value)` — a single scalar carrying the parity.
- `reason` = the move does **not** change the parity of the sum (it subtracts `2*Min(a,b)`), so
  reasoning about the multiset is replaced by reasoning about the scalar sum.

### 4. BridgeLemma — `BridgeLemma(lemma, role)`
- `lemma` = the algebraic identity tying the move's effect to a parity-neutral change:
  `(a + b) - |a - b| = 2*Min(a, b)`, equivalently the rewrite chain
  `S - a - b + AbsDiff(a, b) -> S - 2*Min(a, b)` (via `AbsDiffRewriteRule` + `CancelErasedNumbersRule`).
- `role` = converts the move's delta on the sum into an even quantity `2*Min(a,b)`, so that
  `S -> S - 2*Min(a,b)` preserves parity.

### 5. NaiveFailure — `NaiveFailure(goal, obstacle)`
- `goal` = `Parity(FinalNumber, Odd)`.
- `obstacle` = **tracking the board values themselves.** Each move erases two numbers and writes
  `|a-b|`; no individual value is conserved and the multiset changes arbitrarily, so tracking the
  numbers directly never closes.

---

## Spine (load-bearing rules)

Each of the 5 measured steps should map to a `SpineStep(rule, verdict, fanout)` with
`verdict = truth_value` (withholding breaks closure) and a non-empty `fanout` chain. Load-bearing
rules for E2:

1. `InitialBoardSumRule` — the named sum lemma `1+...+2n = n(2n+1)`.
2. `TwoKPlusOneIsOddRule` — `Parity(2n+1, Odd)`.
3. `ParityOfProductRule(Odd, Odd, Odd)` — `Parity(n(2n+1), Odd)`.
4. `Preserves(EraseAndReplace, Parity(BoardSum))` — the invariant obligation.
5. `TerminalReadoutRule` — concludes `Parity(FinalNumber, Odd)` from invariant + terminal.

`baseline_cost` should be non-zero (the measured cost of the derivation); the spine is the load-bearing
subset that still closes.

---

## What `E-CODE-EXPLAIN-FROM-PLAN` must satisfy (acceptance from operator)

- E2 retained plan → non-empty `ExplanationPlan`.
- zero-step successful proof → valid plan with zero steps.
- non-closing plan → explicit refusal (not an empty-silent `EmptyList`).
- `RenderPlan` → at least one sentence.
- **No call into `evaluated_search`** on this path.

The target above is the concrete matching expectation: all five panels populated with the real E2
content, spine carrying the five load-bearing rules.

---

## Session record (one line for the record, per operator)

```
The machine can prove E2,
cannot yet explain that proof,
cannot yet mine that proof,
and cannot yet propose the observable from raw move semantics.
```

Follow-up taken: **Option B (CUR-EXPLAIN-E2)** — read-only target spec, grounded in the measured
5-step plan and the real substrate constructors. No production code touched.
