# [SHARED] Request — E7 observable constructors

Status: **request** (unpartitioned shared append points → [SHARED] to the integrator, not a local
fork). Per `protocol/DISTRIBUTION.md` §2, unpartitioned points are [SHARED] requests to the
integrator, never local forks. This is routed to INT because the requested items are **term
constructors**, not planner methods — G1 owns `Invariance(observable, moveset)` as a planner
alternative and does not own new observable vocabulary.

Author: CUR lane. Branch: `arena/01a066cf-cat-theo-machine`.

Branch state:
- commit base for this request: `bb9681a16571f1503b62dd81dfdbd03b51ca5fec` (parent `c10011b`).
- integration tip observed during authoring: `feb457ec2878fa75bd42dd46dc7ccb28343b23de`.
- **latest visible integration base (landing-time tip): `d76f7814a5a886d26248b52b95a3dfa1699fd491`.**

---

## What is being requested

New observable term constructors absent from the tree (confirmed by grep: no `ResidueMod`,
`FlipSign`, `CyclicWindowProduct`, or `SumOfProducts` symbol at the request base). Signatures as
agreed (width kept explicit, no extra constructor):

| constructor | signature | purpose |
|---|---|---|
| `CyclicWindowProduct` | `CyclicWindowProduct(sequence, width, offset)` | the sliding 4-window product terms over the cycle, cyclic boundary conditions |
| `SumOfProducts` | `SumOfProducts(product_terms)` | sums the machine sequence of cyclic-window product terms → the observable `S` |
| `FlipSign` | `FlipSign(state, position)` | sign-flip legal-move primitive on one element |
| `ResidueMod` | `ResidueMod(reading, modulus, residue)` | generic modular-residue observable (mod 4; not just parity/mod 2) |

Here `product_terms` is the machine sequence of `CyclicWindowProduct` terms, so the window width
stays explicit without adding a fifth constructor. This is the vocabulary E7 needs for `Invariance`
over `ResidueMod(SumOfProducts, 4)` under `FlipSign`.

## Registration points the integrator must touch (unpartitioned / shared)

Semantic anchors, **not** line numbers (the integration tip's `labels.py` is 3,174 lines; exact lines
shift and must not be cited):

| Registration point | Semantic anchor | Partitioned | Action |
|---|---|---|---|
| label class definition | `labels.py`, adjacent to `InvariantCandidateLabel` / `InvariantRefutedLabel` (`labels.py:1446,1450` at the landing-time tip) | no | append classes at the tail of the class region, before the singleton region |
| label singleton | `labels.py`, adjacent to `InvariantCandidateLabel = …` / `InvariantRefutedLabel = …` (`labels.py:2139,2140` at the landing-time tip) | **yes** | append inside a single track block (or the shared block, integrator's call), not a worker fork |
| `sync_from_namespace` tuple | `labels.py`, adjacent to the observable-family names in the tuple (`BoardSumObservableLabel`, `BoardSumLabel`, `ParityLabel`, at `labels.py:2636–2638` at the landing-time tip) | no | **unmarked shared append point** (see D1) — add the new names near the observable family |
| `SNAPSHOT_SYMBOL_NAMES` | `persistence.py`, adjacent to `BoardSumObservableLabel` / `BoardSumLabel` / `ParityLabel` (`persistence.py:449–451`) | no | **unmarked shared append point** — add the new names |

These four constructors are **term heads represented by labels**. Executable evaluation / preservation
behavior (the `Edge` implementations that compute the reading) is a later implementation item, **not**
part of this label-registration request; no `Edge` class is requested here.

## Dependencies / acceptance for the request

- An **isolated, non-loaded fixture can compile all four requested heads through `{sym: ...}`**
  (the loader resolves `{sym: ...}` names; this proves the labels are registered end-to-end without
  any pack content).
- `label_registration_completeness_test` stays green after the registration-point updates.
- A snapshot containing each constructor round-trips (via `SNAPSHOT_SYMBOL_NAMES`).
- **No production pack, no pack filter, no E7 theorem content changes in this request.** Pack-filter
  reachability and `blackboard`/`e2`/`engel-blackboard`/`all` filter membership belong to the later E7
  content commit, not to constructor registration.

## Not requested

- No planner-method change (`Invariance(observable, moveset)` stays G1's). The constructors are
  vocabulary, not planner logic.
- No E7 pack, no pack filter, no `Edge` evaluation behavior, no theorem content in this request.

## Note on absence (measured)

At the request base the symbols `ResidueMod`, `FlipSign`, `CyclicWindowProduct`, `SumOfProducts` are
absent from `labels.py` and `invariance.py` (confirmed by grep). The request fills that gap at the
**vocabulary (label) layer only**. The label family is grouped with the existing observable family
(`BoardSumObservableLabel`, `BoardSumLabel`, `ParityLabel`) rather than given E7-specific names.
