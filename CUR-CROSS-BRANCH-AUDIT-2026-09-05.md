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
There was one residual divergence that INT must reconcile at merge time (the duplicate filename/route)
and one optional completeness gap (the sibling card was slightly denser on the reasoning-failure
witnesses). **Both are now resolved on the canonical card** (see "Reconciliation applied" below): the
canonical `CUR-ENGEL-E4-oracle.md` now carries the full reasoning-failure matrix (the sibling's
vertex-count and house-size-difference witnesses melded in) and declares itself canonical with an INT
merge directive. Only the duplicate-route/filename choice remains, which this audit resolves by naming
`CUR-ENGEL-E4-oracle.md` (lowercase, canonical) as the single canonical path.

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
   sibling has `CUR-ENGEL-E4-ORACLE.md` (uppercase). They are content-equivalent. **Resolution (this
   audit):** adopt **`CUR-ENGEL-E4-oracle.md`** (lowercase) as the single canonical E4 doc. The
   sibling uppercase file is corroboration, not a second authoritative doc. Do **not** merge both
   `E4` oracle cards as-is into the integration line without naming a canonical path — the two
   filenames differ only in case, so Git-on-case-insensitive would collide; pick one.
2. **Notation.** Canonical uses `H`; sibling uses `V`. Both are correct and equivalent (Claim 1). The
   seal manifest names the canonical one it seals.
3. **Density (resolved).** The canonical card now carries the full reasoning-failure matrix — the
   sibling's vertex-count and signed/absolute house-size-difference witnesses are melded in, with a
   note that they came from the sibling variant. The completeness gap is closed.

## Reconciliation applied (canonical card, this turn)

- `CUR-ENGEL-E4-oracle.md` now opens with a **Canonical / route directive (INT merge)** block naming
  itself canonical, cross-referencing the sibling uppercase variant, and stating they are
  notation-equivalent.
- Item 7 grading matrix expanded to include the sibling's extra reasoning-failure witnesses
  (vertex-count invariance; signed house-size difference `±2`; absolute house-size difference
  `0 → 2`).
- Canonical content-id updated accordingly (see sealing table).

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
| `CUR-ENGEL-E4-oracle.md` | `arena/01a066cf` (canonical, reconciled) | `841a97b74c90985abf7af4e63a291b4872e3d4156961b51c861751f6a5b0099a` |
| `CUR-ENGEL-E4-ORACLE.md` | `arena/01a068c2` (variant, corroboration) | `0ff055a6f6dc5c81848daa8135cc15efca4ae568c444982ed153e7e75c23c328` |
| `CUR-ENGEL-E7-oracle.md` | `arena/01a066cf` (canonical) | `bd4942a6040b80f825bc25c40dbca4c7db450f5cf1f416643024d9fe9a60ef60` |

> INT note: the seal manifest records the canonical E4 content-id `841a97b7…` (the reconciled
> lowercase card, canonical `H` form) as the sealed E4 content and lists `0ff055a6…` as corroborating
> evidence. `841a97b7…` supersedes `a11ca451…` — the card was reconciled (density melded, canonical
> directive added) so its content-id changed.

---

## Summary

- Cross-branch E4 audit: **PASS** (notation-equivalent; one duplicate-route fork to reconcile at merge).
- §0 sweep: **PASS** (0 occurrences on both tips for the three confirmed phrases).
- Sealing dry-run: computed hashes for the three canonical cards + the sibling E4 variant.

Docs-only; no production code, labels, Edge classes, packs, or G implementation touched.
