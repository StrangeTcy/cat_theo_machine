# Fixture 8: Tao 1.1 Budget Exhaustion vs Refutation

**Fixture ID:** `fixture-08-budget-exhaustion`  
**Source Locus:** `main.py:441`  
**Engineering Base:** `428ecdc`  
**Pipeline Run:** Cut L-S-4 Certified  

---

## 1. Before (Observed Baseline Defect)

```text
Conflates budget exhaustion with refutation; hides initialization bottleneck.
```

---

## 2. After (Surface Realization & Audience Cuts)

### Operator Cut (1 cut behind, decision/blocker focused):
```text
Section3_Blockers:
  • tao_problem_1_1 (goal_evaluation): inconclusive — budget exhausted without refutation
```

### Engineer Cut (full telemetry, exact loci, singular/plural agreement):
```text
Section3_Blockers:
  • tao_problem_1_1 (goal_evaluation): inconclusive — budget exhausted without refutation
```

---

## 3. Reference Human Target

```text
Proof search inconclusive: goal undischarged after 600.00s timeout (0 nodes expanded).
```

---

## 4. Invariant & Provenance Checklist

- [x] **Zero State Mutation:** Read-only projection over machine terms.
- [x] **Evidence Fidelity:** Structural term identity preserved without lossy textual equality.
- [x] **Provenance Certified:** Rendered clauses trace to machine-native `StoryFragment` IDs.
- [x] **Conflict-Checked:** Validated against conflict predicate contract.
