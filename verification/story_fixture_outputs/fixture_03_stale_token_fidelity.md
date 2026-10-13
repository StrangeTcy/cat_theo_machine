# Fixture 3: Stale Token Lossless Fidelity

**Fixture ID:** `fixture-03-stale-token-fidelity`  
**Source Locus:** `search/compare_packets.py:257-266`  
**Engineering Base:** `428ecdc`  
**Pipeline Run:** Cut L-S-4 Certified  

---

## 1. Before (Observed Baseline Defect)

```text
Unexplained rejection caused by printer lossiness: token=10 vs expected=10 displayed as identical.
```

---

## 2. After (Surface Realization & Audience Cuts)

### Operator Cut (1 cut behind, decision/blocker focused):
```text
Section3_Blockers:
  • search_bfs_packet_result (token_generation_match): rejected
```

### Engineer Cut (full telemetry, exact loci, singular/plural agreement):
```text
Section3_Blockers:
  • search_bfs_packet_result (token_generation_match): rejected
```

---

## 3. Reference Human Target

```text
SearchBFS packet rejected: returned token (10:gen-1) does not match expected token (10:gen-2).
```

---

## 4. Invariant & Provenance Checklist

- [x] **Zero State Mutation:** Read-only projection over machine terms.
- [x] **Evidence Fidelity:** Structural term identity preserved without lossy textual equality.
- [x] **Provenance Certified:** Rendered clauses trace to machine-native `StoryFragment` IDs.
- [x] **Conflict-Checked:** Validated against conflict predicate contract.
