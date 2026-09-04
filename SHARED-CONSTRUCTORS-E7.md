# [SHARED] Request — E7 observable constructors

Status: **request** (unpartitioned shared append points → [SHARED] to the integrator, not a local
fork). Per `protocol/DISTRIBUTION.md` §2, unpartitioned points are [SHARED] requests to the
integrator, never local forks. This is routed to INT because the requested items are **term
constructors**, not planner methods — G1 owns `Invariance(observable, moveset)` as a planner
alternative and does not own new observable vocabulary.

Author: CUR lane. Branch: `arena/01a066cf-cat-theo-machine`. Commit base for this request:
`c10011bfabc73b55c7a3de80c4ff14a78234f17b`. Integration tip observed during work:
`feb457ec2878fa75bd42dd46dc7ccb28343b23de`.

---

## What is being requested

Four new observable term constructors (plus the `ResidueMod` family) that E7's inventory
(`CUR-ENGEL-E7.md`, item 3 and Status) identifies as absent:

| constructor | signature | purpose |
|---|---|---|
| `ResidueMod` | `ResidueMod(observable, modulus, value)` | generic modular-residue observable (mod 4; not just parity/mod 2) |
| `FlipSign` | `FlipSign(state, position)` | sign-flip legal-move primitive on one element |
| `CyclicWindowProduct` | `CyclicWindowProduct(sequence, width, offset)` | sliding-window 4-product over a cycle, cyclic boundary conditions |
| `SumOfProducts` | `SumOfProducts(state)` | sums the window products around the cycle → the observable `S` |

These are the vocabulary E7 needs for `Invariance` over `ResidueMod(SumOfProducts, 4)` under
`FlipSign`.

## Registration points the integrator must touch (unpartitioned / shared)

| Registration point | Location | Partitioned | Action |
|---|---|---|---|
| label class definition | `labels.py` class region (currently ~2,455–2,500) | no | append classes at the tail of the class region, before the singleton region |
| label singleton | `labels.py` singleton region (~3,158–3,171 at tip) | **yes** | append inside a single track block (or the shared block, integrator's call), not a worker fork |
| `sync_from_namespace` tuple | `labels.py` ~2,473+ | no | **unmarked shared append point** (see D1) — add the new names |
| `SNAPSHOT_SYMBOL_NAMES` | `persistence.py` ~202+ | no | **unmarked shared append point** — add the new names |
| `class Foo(Edge)` constructors | new module (e.g. `invariance.py` or a dedicated observable module) | — | the edges that apply `ResidueMod`/`SumOfProducts`/`CyclicWindowProduct`/`FlipSign` |

## Dependencies / acceptance for the request

- The four constructors must resolve from the pack loader and be reachable under the filters
  `blackboard`/`e2`/`engel-blackboard`/`all` (same convention as `engel-blackboard.pack.yaml`).
- Generic, not E7-hardcoded: no `Parity(BoardSumObservable)`-style special-case; the observables are
  reusable across the invariance engine.
- `label_registration_completeness_test` should stay green after the registration-point updates.
- No regression to the existing invariance test suite.

## Not requested

- No planner-method change (`Invariance(observable, moveset)` stays G1's). The constructors are
  vocabulary, not planner logic.
- No E7 pack authoring in this request; the pack is a separate content decision.

## Note on absence (measured)

At the request base, `labels.py` and `invariance.py` contain **no** `ResidueMod`, `FlipSign`,
`CyclicWindowProduct`, or `SumOfProducts` symbols (confirmed by grep). The request fills that gap
at the vocabulary layer only.
