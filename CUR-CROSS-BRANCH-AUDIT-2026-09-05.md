# CUR Cross-Branch Consistency Audit — E4 oracle cards (2026-09-05)

Docs-only audit, CUR branch. Agent: CUR-ORACLE on `arena/01a066cf-cat-theo-machine`.

Audit targets:
- **Canonical branch** `arena/01a066cf-cat-theo-machine` @ `cf0d13dd3d20326f50654466358700c82b076f25` —
  carries `CUR-ENGEL-E4-oracle.md` (lowercase, monovariant `H`, `ΔH = e_out − e_in`).
- **Sibling branch** `arena/01a068c2-cat-theo-machine` @ `9fb8870561f0a34f5fd0eb32a06486b8a4e91625`
  (tip advanced past the `ad15811` recorded in that branch's own card) — carries
  `CUR-ENGEL-E4-ORACLE.md` (uppercase, monovariant `V`, `ΔV = d − 2s`).
- Fork base of the two branches: `41e80785d4de090337a9dfc08439f2fcb45915dc`.
- Integration tip (ls-remote): `e0853a915baf260b7d1e9d3678c8f9d78300655b`.

---

## Verdict

**The two E4 oracle cards are notation-equivalent, not divergent.** Both state the same corrected
facts: max-degree ≤ 3 given, exactly two houses, strict descent ≤ −1 per legal move, degree-4 break
control, 4-cycle dual-terminal control, and the same E3/E4/E7 ordering contrast. They differ only in
symbols (`H` vs `V`, and `e_out − e_in` vs `d − 2s`), and the two formulas are provably identical.
There is one residual divergence that INT must reconcile at merge time (the duplicate filename/route),
and one optional completeness gap on the canonical card (the sibling card is slightly denser on the
reasoning-failure witnesses).

Independent verification (this session, brute-force/exhaustive — not transcribed from a runtime log):

## Claim 1 — Descent-formula equivalence

```
ΔH = e_out − e_in          (card A, canonical)
ΔV = d − 2s                (card B, sibling)
```

Under exactly-two-houses: `d = e_in + e_out` and `s = e_in`, so `d − 2s = (e_in+e_out) − 2·e_in =
e_out − e_in`. Verified by **exhaustive enumeration** over n = 2..5, all simple graphs, all
partitions, all vertices: **0 mismatches**. The monovariants are the same quantity.

## Claim 2 — 4-cycle dual-terminal census

Both cards assert the 4-cycle (each vertex degree 2, two houses) has terminal partitions with
`V ∈ {0, 2}`, and that the single-house partition (`V = 4`) is **not** terminal. Verified:
- terminal partitions: `0011, 0101, 0110, 1001, 1010, 1100` (six);
- terminal `V` values: `{0, 2}`;
- single-house `0000`: `V = 4`, every vertex has 2 same-house neighbors → legal moves exist → **not
  terminal**.

So termination certifies "no legal move", not a unique partition or a unique minimum — the
"termination ≠ optimality" control holds on both cards.

## Claim 3 — House-size-difference rejected candidates (non-monotone)

Both cards reject house-size-difference measures. Verified with real legal moves (degree-bounded
graph, n = 6):
- absolute house-size difference can **increase**: `000111`, move m1 → `0 → 2`;
- absolute house-size difference can **decrease**: `000000`, move m0 → `6 → 4`;
- signed difference changes by exactly `±2` per relocation.
Neither is monotone ⇒ neither is a descent measure ⇒ both rejected on both cards.

---

## Residual divergence for INT to reconcile at merge time

1. **Duplicate route / two E4 card files.** Canonical has `CUR-ENGEL-E4-oracle.md` (lowercase);
   sibling has `CUR-ENGEL-E4-ORACLE.md` (uppercase). They are content-equivalent. INT must choose a
   canonical path and merge/meld one into the other (or keep both with an explicit cross-reference and
   a single canonical hash in the seal manifest). Do **not** merge both as-is into the integration line
   without resolving the fork, or the E4 doc content forks.
2. **Notation.** Canonical uses `H`; sibling uses `V`. Both are correct and equivalent (Claim 1).
   Either is acceptable as canonical; the seal manifest must name the one it seals.
3. **Density (optional, non-blocking).** The sibling card lists more distinct reasoning-failure
   witnesses (vertex-count invariance, signed and absolute house-size difference with concrete
   `±2`/`0→2` values). The canonical card's grading matrix is slightly sparser. This is a completeness
   difference, not an inconsistency; INT may fold the extra witnesses into the canonical card if a
   single dense card is wanted.

## No conflict

Both cards agree on: the load-bearing degree bound; exactly-two-houses necessity; strict descent
`Δ ≤ −1`; degree-4 break control; 4-cycle dual-terminal control; and the E3/E4/E7 ordering. The two
cards are the same mathematical content in two notations — the strongest form of corroboration, not a
dispute.

---

## §0 sweep (three confirmed phrases) across both branches

Swept every CUR-/protocol file on both branch tips for the three confirmed §0 banned items: item 5
(byte encoding `0x686f6e657374`), plus the two enumerated verbatim at
`verification/verification_report_tao_spec.md:35` (referenced by artifact path, not restated):

- `arena/01a066cf-cat-theo-machine` — **0 occurrences** in every CUR/protocol file.
- `arena/01a068c2-cat-theo-machine` — **0 occurrences** in every CUR/protocol file.

No violations; no ledger entry required. (Only the three in-tree-confirmed phrases were swept; the
remaining three of the six are session-supplied and not recoverable in-tree, per `protocol/CUR.md`.)

---

## Sealing dry-run — canonical oracle card content-ids (SHA-256)

Dry-run manifest (content-ids computed against the branch-tip file contents; not yet sealed — sealing
is INT's job):

| path | branch | sha256 |
|---|---|---|
| `CUR-ENGEL-E3-oracle.md` | `arena/01a068c2` | `31a8026d6e59de537d21533d96a0d0050b7bb9a3bbe6c181e138d150fa544b11` |
| `CUR-ENGEL-E4-oracle.md` | `arena/01a066cf` (canonical) | `a11ca451e52dbeb7dc3b65854a2ccc500c33dad5647e108510042a3617af9353` |
| `CUR-ENGEL-E4-ORACLE.md` | `arena/01a068c2` (variant) | `0ff055a6f6dc5c81848daa8135cc15efca4ae568c444982ed153e7e75c23c328` |
| `CUR-ENGEL-E7-oracle.md` | `arena/01a066cf` (canonical) | `bd4942a6040b80f825bc25c40dbca4c7db450f5cf1f416643024d9fe9a60ef60` |

> INT note: the seal manifest should record the single canonical E4 content-id. Since cards A and B
> are content-equivalent, INT may pick `a11ca451…` (canonical `H` form) as the sealed E4 content and
> list `0ff055a6…` as corroborating evidence, matching the recommendation in the sibling card's
> routing-caution section.

---

## Summary

- Cross-branch E4 audit: **PASS** (notation-equivalent; one duplicate-route fork to reconcile at merge).
- §0 sweep: **PASS** (0 occurrences on both tips for the three confirmed phrases).
- Sealing dry-run: computed hashes for the three canonical cards + the sibling E4 variant.

Docs-only; no production code, labels, Edge classes, packs, or G implementation touched.
