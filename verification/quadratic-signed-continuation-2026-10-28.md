# Authored strategy withdrawn; signed verification retained — 2026-10-28

The user rejected the authored conjugate-and-round quotient strategy as
hardcoding. The assistant had chosen the strategy and encoded it; the Machine
had not discovered it. A parameterized API did not change that provenance.
This report replaces the earlier claims of delivered quotient/FLT progress.

## Withdrawal and dimensions

The following files have been removed:

- `math/whole_rounding.py`
- `math/quadratic_quotient.py`
- `validation/whole_rounding_regressions.py`
- `validation/quadratic_quotient_regressions.py`

The old 39-case rounding and 19-case quotient logs remain only as historical
evidence of withdrawn code. They support no current discovery, Engel-strategy
or FLT claim. A source search found no remaining Python or command-script
references to the removed modules or their quotient constructors.

| Retained intervention | Dimension improved | Scope |
| --- | --- | --- |
| Remove the authored strategy and correct the DAG/report | Self-improvement; storytelling/explanations | Discovery claims now reflect how the work was produced. The proposed human-selected norm-bound/factorization route is superseded. |
| Generic signed-polynomial verification | Self-improvement, with reusable verification for future FLT/IMO work | Checks supplied identities; chooses no target identity, question or proof strategy. No new IMO solution or FLT proof. |
| Direct-call authority and recorded-action binding | Self-improvement | A valid certificate cannot authorize a different recorded step, and direct calls cannot omit signed authority. |

No new law or strategy was activated in the live graph. The earlier
`math/quadratic_division.py` remains an independent verifier of supplied
division witnesses; it does not construct a quotient.

A fresh session after withdrawal completed through the real `hyge.main live`
entry point (exit 0): `live-flt-after-withdrawal-2026-10-28.log`. Given the full
FLT no-solutions request, it entered the operation-law playground on the
supplied carrier {1,2}, observed addition symmetry, and retained the original
FLT claim as pending. The observation was left unnamed. The session created
no FLT proof and invoked no quotient strategy.

## Retained signed proof boundary

`SignedPolynomialDerivation(lhs, rhs, variables, registry)` returns a machine
chain containing a certificate, a derivation over the original signed
endpoints, and the registry. The supported grammar is addition,
multiplication, unary negation, fixed natural powers, and Nat/Whole constants,
directly or in an `ExprInt`. Subtraction is expressed as addition of a negation;
`ExprSubtract` is refused.

Each supplied signed expression is lowered to two formal polynomials denoting
their difference. Equality becomes equality of the two cross sums. The
existing degree-complete grid procedure establishes a polynomial identity,
valid over integer assignments including negative values. Arbitrary finite
sampling would not establish this claim.

Checker B independently reconstructs the translation, pins the original
signed endpoints, checks translated endpoints and variables, and replays the
grid verifier. Both `SignedPolynomialRuleLabel` and `PolynomialGridRuleLabel`
must be explicitly trusted. `VerifySignedPolynomialStep` enforces signed
authority even when called directly, and compares its supplied action with
`P.StepAction(step, registry)()` before replay.

The focused cases include a supplied difference-of-squares identity,
constants/powers, altered endpoints and certificates, false identities,
unsupported syntax, missing authorities, recorded-action substitution, and a
file snapshot roundtrip. This API is not connected to signed live-text parsing
or the Nat playground evaluator. It is verification infrastructure, not a
demonstration of autonomous discovery.

## Verification evidence

| Check | Status | Log |
| --- | --- | --- |
| `signed_polynomial_regressions` | PASS after both integrity fixes; final line includes recorded-action binding and snapshot roundtrip | `signed-polynomial-2026-10-28.log` |
| Existing `test48_named_discovered_laws` | PASS after checker extension | `signed-bridge-named-laws-2026-10-28.log` |
| Existing `checked_story_regressions` | PASS after checker extension | `signed-bridge-stories-2026-10-28.log` |
| Removed `whole_rounding_regressions` | Historical 39-case pass; implementation and suite withdrawn | `whole-rounding-2026-10-28.log` |
| Removed `quadratic_quotient_regressions` | Historical 19-case pass; implementation and suite withdrawn | `quadratic-quotient-2026-10-28.log` |

The retained semantics and focused tests use explicit native Edge classes,
machine Pair chains and truth atoms. `core.py` is unchanged. No numbered suite
slot was consumed. Documentation corrections do not require rerunning these
already-completed controls; the full legacy suite was not rerun.

## Governing next direction

The apprenticeship specification states: “The Machine must discover the
question itself, not merely discover the answer to a question we secretly
planted.” Next work must improve the general discovery -> certification ->
structural matching -> transfer loop. Supplying another authored FLT route
under a generic class name would repeat the same error.

FLT and W28 remain open. Universal Euclideanity, unique factorization, cubic
descent, the quartic movement obligation and remaining prime-exponent cases
have not been discharged by this continuation.
