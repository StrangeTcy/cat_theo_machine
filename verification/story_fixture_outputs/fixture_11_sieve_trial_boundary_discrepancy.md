# Fixture 11: Sieve vs Trial Agreement Scope and Boundary Discrepancy

**Fixture ID:** `fixture-11-sieve-trial-boundary-discrepancy`  
**Source Locus:** `hyge.py:500-530`  
**Engineering Base:** `428ecdc`  
**Pipeline Run:** Cut L-S-4 Certified  

---

## 1. Before (Observed Baseline Defect)

```text
Merger claims AgreeOnSpan on composites while concealing prime/excluded disagreement at 1.
```

---

## 2. After (Surface Realization & Audience Cuts)

### Operator Cut (1 cut behind, decision/blocker focused):
```text
Section2_Evidence:
  • sieve_trial_comparison (composite_classification): completed
Section3_Blockers:
  • integer_1_classification (sieve_excluded_vs_trial_prime): held
  [Clause] Agreement confirmed under projection=composite; boundary discrepancy (excluded_boundary=1) explicitly surfaced in fixture-11-discrepancy
  [Clause] integer_1_classification (sieve_excluded_vs_trial_prime) completed; however, sieve_trial_comparison carries discrepancy or hold.
```

### Engineer Cut (full telemetry, exact loci, singular/plural agreement):
```text
Section2_Evidence:
  • sieve_trial_comparison (composite_classification): completed
Section3_Blockers:
  • integer_1_classification (sieve_excluded_vs_trial_prime): held
  [Clause] Agreement confirmed under projection=composite; boundary discrepancy (excluded_boundary=1) explicitly surfaced in fixture-11-discrepancy
  [Clause] integer_1_classification (sieve_excluded_vs_trial_prime) completed; however, sieve_trial_comparison carries discrepancy or hold.
```

---

## 3. Reference Human Target

```text
Sieve and Trial agree on composites (4, 6, 8, 9); however, integer 1 carries a boundary discrepancy (sieve excluded vs trial prime).
```

---

## 4. Invariant & Provenance Checklist

- [x] **Zero State Mutation:** Read-only projection over machine terms.
- [x] **Evidence Fidelity:** Structural term identity preserved without lossy textual equality.
- [x] **Provenance Certified:** Rendered clauses trace to machine-native `StoryFragment` IDs.
- [x] **Conflict-Checked:** Validated against conflict predicate contract.
