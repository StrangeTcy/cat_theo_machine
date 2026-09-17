# Fixture 9: Applicability Scan Bottleneck Causal Chain

**Fixture ID:** `fixture-09-applicability-bottleneck`  
**Source Locus:** `08August2026 -- opus 5 answer.md:7`  
**Engineering Base:** `428ecdc`  
**Pipeline Run:** Cut L-S-4 Certified  

---

## 1. Before (Observed Baseline Defect)

```text
Critical initialization bottleneck (245.057s scan consuming 40.8% of budget) buried in debug trace.
```

---

## 2. After (Surface Realization & Audience Cuts)

### Operator Cut (1 cut behind, decision/blocker focused):
```text
Section3_Blockers:
  • initial_cursor_applicability (applicability_scan_duration): held
```

### Engineer Cut (full telemetry, exact loci, singular/plural agreement):
```text
Section3_Blockers:
  • initial_cursor_applicability (applicability_scan_duration): held
```

---

## 3. Reference Human Target

```text
Applicability scan required 245.057s (40.8% of budget), causing subsequent search timeout.
```

---

## 4. Invariant & Provenance Checklist

- [x] **Zero State Mutation:** Read-only projection over machine terms.
- [x] **Evidence Fidelity:** Structural term identity preserved without lossy textual equality.
- [x] **Provenance Certified:** Rendered clauses trace to machine-native `StoryFragment` IDs.
- [x] **Conflict-Checked:** Validated against conflict predicate contract.
