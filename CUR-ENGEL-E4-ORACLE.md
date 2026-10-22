# CUR-ENGEL-E4-ORACLE

> **Reclassification (canonical path):** independent verification variant of the canonical `CUR-ENGEL-E4-oracle.md` on `arena/01a066cf`; notation `V ≡ H`, `d−2s ≡ e_out−e_in`; agreement verified 2026-09-04. Per Ruling 1 this sibling is **preserved, not deleted, not merged** — it is cross-verification evidence (the strongest kind this program produces), cited in the seal manifest as corroborating evidence with its own content-id. The seal request covers the canonical card on `arena/01a066cf`; this variant corroborates it.

**Date:** September 5, 2026
**Status:** source-pinned oracle text; not sealed, not machine training input.
**Format:** oracle card, items 1–9 (item 9 carries the ordering/structural contrast requested by the operator).
**Source pin:** the E4 statement is Engel, Chapter 1, printed page 2; the reconstructed inventory omitted a necessary hypothesis and is repaired here.

The formalization and the descent correction were independently verified this session with exhaustive/enumerated checks against the definitions (not transcribed from a runtime log).

---

## 1. Statement

Let a finite simple undirected "enemy graph" be given. Each vertex is a member; an edge between two vertices means they are enemies. The hypotheses are load-bearing and are stated explicitly:

- **maximum degree ≤ 3** (each member has at most three enemies);
- **exactly two houses** — the vertices are partitioned into exactly two houses (the descent formula of item 6 requires exactly two, see the note there).

Prove the members can be divided into the two houses so that **each member has at most one enemy in its own house** (equivalently, no member has two same-house enemies).

> Why the degree bound is load-bearing: it is exactly the hypothesis the reconstructed inventory omitted. Without it the descent argument fails (see item 6).

---

## 2. Initial-state family

Any finite simple graph of maximum degree ≤ 3 together with **any** partition of its vertices into **exactly two houses**.

There is no prescribed special initial configuration. The descent argument is required to work from an arbitrary starting partition.

---

## 3. Legal moves

A **legal move** relocates one vertex to the other house, permitted only when that vertex has **at least two same-house neighbors** (that is, at least two of its neighbors are currently in the same house as it).

This requires **exactly two houses**: with exactly two, the alternative house is unique, so "relocate to the other house" is well-defined. Such a relocation is exactly the operation that can reduce the number of adversary pairs inside a house.

> With more than two houses, moving to a selected target house containing \(t\) enemy neighbors gives \(\Delta V = t - s\), not \(d - 2s\). The two-house assumption is what makes the descent formula of item 6 valid. If the pinned source permits more than two houses, the current descent argument does not follow.

---

## 4. Proof target and reachability

The target is a partition in which **no vertex has two same-house neighbors** — equivalently, a terminal partition. The proof obligation is to show such a partition is reachable by a finite sequence of legal moves.

Unlike E3 and E7, there is **no single canonical target state**. The reachability argument here is a termination argument: the potential of item 5 strictly decreases with every legal move, so the process must stop after finitely many moves, and at that stopping point the required partition is achieved.

---

## 5. Reference measure (potential)

Define

\[
V = \text{number of undirected enemy edges internal to either house}
\]

i.e. the number of edges of the graph whose two endpoints lie in the same house.

The three facts that make the descent well-founded:

1. **Bounded below:** \(V \ge 0\) for every partition (it counts a subset of edges).
2. **Integer-valued:** \(V \in \mathbb{Z}\).
3. **Strictly decreasing under every legal move** — established in item 6.

These three facts together make \((V,\mathbb{Z}_{\ge0},\text{strict-decrease})\) a well-founded order, so the descent must terminate.

---

## 6. Descent calculation

Let \(d\) be the degree of the moved vertex and \(s\) the number of its same-house neighbors. Relocating the vertex removes \(s\) internal edges (it was in the same house as \(s\) neighbors) and creates \(d-s\) new internal edges (it is now in the other house, so its remaining \(d-s\) neighbors are in that house). Hence

\[
\Delta V = (d-s) - s = d - 2s.
\]

Under the legal-move condition \(s \ge 2\) and the hypothesis \(d \le 3\), the verified case table is:

| \((d,s)\) | \(\Delta V = d-2s\) |
|---|---|
| \((2,2)\) | \(-2\) |
| \((3,2)\) | \(-1\) |
| \((3,3)\) | \(-3\) |

Every case gives \(\Delta V \le -1\). Therefore every legal move strictly decreases \(V\), and the number of moves is bounded by the initial value \(V_0\) (termination in at most \(V_0\) moves).

**Without the degree bound the claim fails:** \((d,s)=(4,2)\) gives \(\Delta V = 0\) (a stall), and \((d,s)=(5,2)\) gives \(\Delta V = +1\) (an increase). This is precisely the omission in the reconstructed inventory; the bound is what makes the descent strict.

---

## 7. Candidate grading (reasoning-failure matrix)

Unlike E3 and E7, the false candidates for E4 are **reasoning failures**, not observable failures. They concern the shape of the argument rather than the value of a particular quantity.

| Candidate reasoning | Verdict | Witness |
|---|---|---|
| Descent without the degree bound | **REFUTED** | \((d,s)=(4,2) \Rightarrow \Delta V = 0\) (stall, not strict descent) |
| Terminal partition = global minimum (optimality) | **REFUTED** | 4-cycle: two genuine terminal partitions have \(V=0\) and \(V=2\) (see item 8), so termination does not imply minimality |
| Descent on vertex count | **REFUTED** | vertex count is invariant (constant at \(n\)) under every move — preserved, but it never descends, so it cannot certify progress toward a target |
| Descent on signed house-size difference \(|H_0|-|H_1|\) | **REFUTED** | changes by \(+2\) or by \(-2\) depending on move direction, so it is not monotone |
| Descent on absolute house-size difference \(\bigl||H_0|-|H_1|\bigr|\) | **REFUTED** | it can increase (e.g. \(3/3 \to 2/4\) makes the absolute difference \(0 \to 2\)) and can decrease — not monotone |
| \(V\) strictly decreasing, \(V\ge0\), \(V\in\mathbb{Z}\) | **CORRECT** | well-founded descent ⇒ termination in at most \(V_0\) moves |

---

## 8. Negative controls

The two independently verified counter-facts are the negative controls. A synthesizer or grader that accepts descent without checking the degree hypothesis, or that claims minimality from termination, must fail these controls.

**Control 1 — degree-bound necessity.** The configuration \(d=4,\,s=2\) is a legal move that yields \(\Delta V = 0\), not a strict decrease. Any reconstruction that asserts "every permitted relocation decreases the measure" without the maximum-degree-≤3 hypothesis must be rejected here, because a degree-4 vertex relocating with two same-house neighbors gives zero change.

**Control 2 — termination ≠ optimality.** On a 4-cycle (each vertex degree 2, exactly two houses), enumerate all 16 partitions with the corrected legal-move predicate (a vertex may move iff it has at least two same-house neighbors). The terminal partitions (no legal move) are exactly six, with values \(V \in \{0, 2\}\):

- alternating partition \(0101\): \(V = 0\), each vertex has 0 same-house neighbors — terminal;
- adjacent-pairs partition \(0011\): \(V = 2\), each vertex has 1 same-house neighbor — terminal.

The single-house partition \(0000\) is **not** terminal: \(V = 4\), and every vertex has 2 same-house neighbors, so legal moves remain. Two genuine terminal configurations still have different \(V\) (0 and 2), so termination certifies "no legal move" and neither a unique partition nor a unique terminal value.

> Enumerated result: terminal partitions of the 4-cycle have \(V \in \{0, 2\}\) (not \(\{0,2,4\}\)). An earlier census used a faulty legal-move predicate that wrongly admitted the single-house \(V=4\) partition as terminal; it is corrected here. Termination is not a unique-minimum certificate.

---

## 9. Structural difference and ordering (E3 → E4 → E7)

E4 is the opposite case from E7: it is **termination reasoning** (well-founded descent on a bounded potential), with **no modular invariant anywhere**. The contrast with the neighboring problems in the ordering is pedagogical:

```text
E3: exact-linear invariant, unreachability          (invariance, linear family)
E4: bounded potential, strict descent, termination  (extremal/descent, no invariant)
E7: modular invariant + reachability certificate    (invariance, modular family)
```

The E4 note from the E7 verification — "modular preservation + reachability, not termination reasoning" — does **not** apply here. E4 is that termination reasoning itself. The descent idea shape is also E4's tie-in to Track E's charter item E4 ("well-ordering + strictly decreasing measure"): the explanation substrate's second idea shape is precisely this proof's skeleton. This makes E4 the natural first fixture when the E-track reaches that phase.

---

## 10. Routing-caution resolution (INT reconciliation)

**Ancestry (verified against remote, not the operator-supplied hash):**

```text
ancestry:
  arena/01a068c2 contains / does not contain 34208cc
  => DOES NOT CONTAIN. 34208cc is only in arena/01a066cf's DAG.
  fork base of arena/01a068c2 and arena/01a066cf = 41e8078 (worktree base).
  arena/01a066cf: only commits unique = 7; arena/01a068c2: only commits unique = 1.
  remote tips: arena/01a066cf = cf0d13d, arena/01a068c2 = ad15811.
```

**Fork finding.** `arena/01a066cf` already carries a corrected E4 oracle card at `CUR-ENGEL-E4-oracle.md` (lowercase), using `H`, `ΔH = e_out − e_in`. This card (`CUR-ENGEL-E4-ORACLE.md`, uppercase) uses `V`, `ΔV = d − 2s`. Both state the same corrected facts: max-degree ≤ 3 given, exactly two houses, strict descent ≤ −1, degree-4 break control, 4-cycle dual-terminal control. They are **notation variants, not a conflict**. INT must merge or cherry-pick in a declared order so the E4/CUR docs do not fork (this is the exact risk the operator flagged).

**Merge-request decision (not settled):** the deliverable is a docs-only batch, but it is **not yet ready for a single INT merge** because two parallel `CUR-ENGEL-E4` oracle cards exist on sibling branches (see above). INT must first choose the canonical path (which card is authoritative, or merge one into the other). Until INT resolves that, submitting this card alone would fork doc content.



---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: E4 descent case table; degree-4 counterexample (d=4,s=2 -> 0); corrected
      C4 terminal census (V ∈ {0,2}, single-house V=4 not terminal); vertex-count invariance;
      signed/absolute house-size witnesses (Δ = ±2 each, neither monotone); ancestry + fork finding
  files changed: CUR-ENGEL-E4-ORACLE.md; verification/2026-09-04-CUR-ENGEL-E4-check.txt
  tests run: source-only verification (exhaustive enumeration), no runtime machine tests
  merge request: NOT READY for INT as-is — two parallel CUR-ENGEL-E4 oracle cards exist on
      sibling branches (01a066cf lowercase, 01a068c2 uppercase); INT must pick/meld canonical first
  blocked on: INT decision on canonical E4 card path; sealing of E3/E4/E7 is INT's job
```
