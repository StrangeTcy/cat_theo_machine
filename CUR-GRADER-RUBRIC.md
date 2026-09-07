# CUR-GRADER-RUBRIC — verdict-derivation rubric for the E3/E4/E7 grader contracts

Docs-only, evaluator-side, CUR branch. Agent: CUR-ORACLE. **training-visible: no.** This is the
**how** the contract's **what** (the C–check assertions) becomes a machine verdict on a real G-ENG
blind-output artifact. It exists because the contracts say *what each check asserts* but not *how
an evaluator decides PASS / FAIL / cannot-determine*. Without it the first real grading would be
improvised.

**Operating model (routed, default): (a) evaluator grades by hand against this rubric.** The rubric
is the tool. Model (b) — an executable grader — is a separate E-track / `[SHARED]` build, not CUR's
to build; CUR files the request if (b) is wanted. Default is (a) until someone asks for (b).

## Decision rule (three outcomes, never two)

For each check a grader must emit exactly one of:
- **PASS** — the artifact's cited evidence fully satisfies the check (see each check's PASS test).
- **FAIL** — the artifact's evidence contradicts the check, or the check is demonstrably violated.
- **CANNOT-DETERMINE** — the artifact contains **no evidence either way**. This is **not** a PASS.
  A check with no supporting evidence in the artifact is CANNOT-DETERMINE and the overall verdict is
  FAIL-with-CANNOT-DETERMINE (record the check). It is also not a lazy FAIL: only use FAIL when the
  evidence is present but wrong; use CANNOT-DETERMINE when it is absent.

Overall verdict: **PASS only if all six checks are PASS.** Any FAIL or CANNOT-DETERMINE →
the overall verdict is FAIL (name the unmet checks and, per check, whether it is FAIL or
CANNOT-DETERMINE). No partial verdict. Classification agreement (the sealed oracle matrix) is a
separate note, not folded into the six checks.

## Per-contract, per-check rubric

Evidence is judged from the frozen artifact's stated derivation and cited support. "Cited" means the
artifact names the premise/step it relies on; it does not require the grader to re-derive, only to
check the supporting evidence is present and not contradicted.

### E4 (descent, max degree ≤ 3)

| check | PASS evidence (must be present) | FAIL evidence (present but wrong) | CANNOT-DETERMINE (absent) |
|---|---|---|---|
| C1 max-degree ≤ 3 | candidate states the max-degree ≤ 3 bound as load-bearing for the descent | descent argued from `e_in ≥ 2` alone, no degree bound | no statement about an upper bound on enemies |
| C2 exactly two houses | candidate states exactly two houses, so target is unique and `ΔH = e_out − e_in` | houses not bounded to two, or relocation target ambiguous | no mention of the number of houses |
| C3 descent `ΔH ≤ −1` | candidate shows `e_in ≥ 2` + `e_in + e_out ≤ 3` ⇒ `e_out ≤ 1` ⇒ `ΔH = e_out − e_in ≤ −1` for every legal move | asserts strict descent without the `e_out ≤ 1` bound (e.g. deg-4 `ΔH = 0`) | no per-move ΔH bound derived |
| C4 well-founded termination | candidate notes `H` bounded below by 0 and integer-valued, so strict decrease ⇒ termination in ≤ `H_0` moves | claims termination with no lower bound / well-founded order | no statement that `H` is bounded below |
| C5 termination ≠ global min | candidate says termination yields "no legal move", not a global minimum | concludes minimality (the conflated 4-cycle dual-terminal claim) | no statement about whether termination is a minimum |
| C6 no constant injection | candidate measure is derived; not supplied as input/hard-coded | E4 monovariant (or equivalent) present as an input constant | no evidence about how the measure was obtained |

### E7 (width-4 mod-4 residue)

| check | PASS evidence | FAIL evidence | CANNOT-DETERMINE |
|---|---|---|---|
| C1 derived from move constraints | cites `FlipSign` family and derives `O = ResidueMod(SumOfProducts(CyclicWindowProduct(...)),4,0)` from the width-4 structure | observable invented without the move set | no reference to how the observable was derived |
| C2 preservation (mod-4) | shows `ΔS = −2(p1+p2+p3+p4)` with the four-product sum even, so `ΔS ∈ {−8,−4,0,4,8}` ⇒ `ResidueMod(S,4)` unchanged | preservation claimed without the even-window argument, or asserted at odd width | no preservation argument |
| C3 separation | start residue `0` differs from target `n mod 4` whenever `4 ∤ n` | observable cannot separate `4|n` from `4∤n` | no start/target reading comparison |
| C4 odd-width control | emits the width-3 failure (`ΔS ≡ 2 (mod 4)`, not preserved) as a negative control | width-3 control omitted, or mod-4 preservation claimed for all widths | no mention of odd width |
| C5 rejected candidates classified | classifies `Σ a_i` and `∏ a_i` as not invariant, `Parity(S)` as preserved-but-non-separating | any rejected candidate asserted invariant, or `Parity(S)` claimed separating | no rejected-candidate classification |
| C6 no constant injection | observable derived, not supplied | E7 reference weights present as input constant | no evidence about derivation |

### E3 (six-sector alternating sum, invariance)

| check | PASS evidence | FAIL evidence | CANNOT-DETERMINE |
|---|---|---|---|
| C1 derived from move constraints | candidate derives `w` from the six move constraints, i.e. `w_i + w_{i+1} = 0` cyclically (in the kernel of the move matrix) | weight stated without the move family, or not in the kernel | no derivation from move constraints |
| C2 preservation `w_i + w_{i+1} = 0` | shows the reading is unchanged under all six moves (`w_i + w_{i+1} = 0` for each pair) | any single move changes the reading | no per-move preservation check |
| C3 start/target separation | start reading (`2` for the reference `w`) differs from every all-equal reading (`0`) | start and target readings coincide, so unreachability does not follow | no start vs target comparison |
| C4 odd-cycle control | emits `NoNonzeroExactLinearObservable(move_family)` for the 5-sector control | yields a nonzero candidate on the odd cycle (false invariant), or silently omits the control | no odd-cycle control present |
| C5 removing generation removes candidate | with the weighted generator disabled, the candidate is absent | candidate survives removal (hard-coded constant or a second path) | no evidence from disabling the generator |
| C6 no constant injection | weight derived, not supplied | E3 weights present as an input/constant | no evidence about derivation |

## Notes

- The "separation-unsupported" case folds into **overclaim** for all three contracts (E4 C5, E7
  C3/C5, E3 C3/C4) — a candidate that cannot separate but asserts the target is unreachable / the
  residue forces `4|n` is an overclaim, not a separate category.
- `CANNOT-DETERMINE` must be recorded per-check in the output, not folded into a single strict-scored
  FAIL, so the artifact's *omission* is distinguishable from its *error*.
- This rubric is evaluator-side and grades against the sealed oracle; it is NOT clean-room blind
  evaluation. The clean-room blind-evaluator role is disallowed for a contaminated context.

Docs-only; evaluator-side; training-visible: no. No production code.
