# Fixture 7: Repeated Negative Rule Probes Aggregation

**Fixture ID:** `fixture-07-repeated-rule-filters`  
**Source Locus:** `engel_e1_prove.debug.log:12-28`  
**Engineering Base:** `428ecdc`  
**Pipeline Run:** Cut L-S-4 Certified  

---

## 1. Before (Observed Baseline Defect)

```text
15 identical negative rule probe lines repeated consecutively without aggregation.
```

---

## 2. After (Surface Realization & Audience Cuts)

### Operator Cut (1 cut behind, decision/blocker focused):
```text

```

### Engineer Cut (full telemetry, exact loci, singular/plural agreement):
```text
Section2_Evidence:
  • rule_filter_probes (replacement_mismatch): held
```

---

## 3. Reference Human Target

```text
Goal filter checked 15 candidate rule heads; zero matched target NonNegative(x).
```

---

## 4. Invariant & Provenance Checklist

- [x] **Zero State Mutation:** Read-only projection over machine terms.
- [x] **Evidence Fidelity:** Structural term identity preserved without lossy textual equality.
- [x] **Provenance Certified:** Rendered clauses trace to machine-native `StoryFragment` IDs.
- [x] **Conflict-Checked:** Validated against conflict predicate contract.
