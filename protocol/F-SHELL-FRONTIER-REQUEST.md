# F-SHELL-FRONTIER-REQUEST — shell-level content request for INT/D11-eng
# session: FPS-20260905-A1
# date: 2026-09-09
# authorizing instruction: protocol owner review channel ("Do not hold. Write
#   the shell-frontier request now."), received after matrix ratification 5237605
# authored by: F-PROVER operator lane (docs only; this request adds no code,
#   no theorem content, and no machine vocabulary through this lane; any
#   implementation is engineer work on a track branch per the charter, never
#   an operator action)
# evidence basis: logs/2026-09-09-F-PROVER-reachability-matrix-bfd4bd2.log
#   (UNTAGGED diagnostic on INT tip bfd4bd28de5765adbdabd1d152200fa67f11e5a2,
#   ratified by the review channel)

## 1. Request class

Minimal shell-level rules needed for the `forall`/`implies` and
`nosolutions` shells to produce a genuine partial match on toy goals.
This is NOT a request to port FLT-adjacent content: the rules below
carry no programme-specific vocabulary and close no programme-shaped
goal (see section 6).

## 2. Evidence basis

From logs/2026-09-09-F-PROVER-reachability-matrix-bfd4bd2.log (machine
values verbatim, one fresh cold process per probe):

- bare eq goal `(eq (plus a a) (plus a a))`: FAILED, cost=334, genuine
  partial matches 1 (residual "missing (eq (plus a a) (plus a a)) (rule
  origin primitive)").
- nosolutions shell over eq `(nosolutions positive-integers (unknowns a
  b) (eq (plus a b) (plus b a)))`: FAILED, cost=334, genuine partial
  matches 0, residual record (zero-successor-root (...)).
- forall/implies shell over eq `(forall n (implies (greater n 1) (eq
  (plus a a) (plus a a))))`: FAILED, cost=334, genuine partial matches
  0, residual record (zero-successor-root (...)).

Two independent enclosing constructors produce the identical live-to-
silent transition. The stall is at the shell layer, not the leaf layer:
bare eq is matchable at this tip, and the stall precedes any
arithmetic-position match, so arithmetic-level surface mappings move
this wall by exactly zero. The missing rules are shell-level, not
leaf-level.

## 3. Toy goals (non-FLT, non-target)

- Goal A:
  nosolutions positive-integers (unknowns x) (eq (plus x 1) x)
- Goal B:
  (forall n (implies (greater n 1) (eq (plus a a) (plus a a))))

Phrasing constraint (parser-surface finding, machine-reported):
symbolic atoms compile; word-form arithmetic followed by '=' is refused
at compile ("cannot read the sentence past 'plus'"); numeric literals
are exhibited by the machine's own parsed-goal echo (e.g. the 1 in
(greater n 1) of the ratified decoy capture). Any probe or acceptance
run must phrase goals accordingly, one fresh cold process per probe
(probe-isolation rule, protocol/F.md section 16).

## 4. Required rule heads

- NosolutionsIntroduction:
  converts a nosolutions goal into a universally-quantified negation
  obligation or a contradiction-from-assumed-solution skeleton.
- ForallImpliesDecomposition:
  strips the forall/implies wrapper and discharges the antecedent,
  leaving the consequent as the active obligation.

These are request specifications for the owning engineers, not
implementations; the machine-term form, label registration, completeness
tables, and shard-guard placement are governed by the charter's
standing constraints and the partition.

## 5. Acceptance criteria for the content port

After the port, on a TAGGED build (gating fact per protocol/F.md
section 16 — the build must be owner-tagged; runs obey the probe-
isolation rule and the D12 header requirement DEF-2026-09-09-10):

- Goal A: genuine partial matches > 0, at least one unmatched formal
  premise concrete, goal remains unclosed.
- Goal B: same.

Negative control: an unrelated shell goal of the same structural depth
remains at 0 genuine partial matches (the port is targeted, not
global).

Baseline to beat (two-part, from the ratified matrix): the shell goal
stalls at cost 334 / partial 0 / zero-successor-root, AND the stall is
provably at the outer shell (bare-eq liveness at the same tip).

## 6. Scope constraint

- These rules introduce no FLT-specific vocabulary.
- They do not close FLT-shaped goals.
- They move the F residual from zero-successor-root to a characterized
  stall with concrete unmatched premises.
- That characterized stall is the precondition for any teaching to be
  admissible under the F protocol: a teach requires a concrete residual
  and a genuinely partially matched rule, and on the current lineage
  the shell stall yields neither (0 partial matches, no concrete
  unmatched premises). Conditional classification for tagged builds
  after this port routes per protocol/F.md section 16 item 3.

## 7. Routing

- Owner: INT / D11-eng
- Evidence: logs/2026-09-09-F-PROVER-reachability-matrix-bfd4bd2.log
- Priority: this request must be satisfied before any F one-shot
  session can produce a non-vacuous result on this lineage.
- Companion facts already INT-routed: D-G3-FPROBE (protocol/F.md
  section 16, complete form) and DEF-2026-09-09-10
  (D12-HEADER-INCOMPLETE). Tooling involved in any acceptance run is
  accepted under the identity-currency sequence of protocol/F.md
  section 13 (exact supplied SHA, remote-ref resolution, manifest
  identity, session-tag compatibility — all four must pass).
