# CTM → ODR checker-A adapter

This package is the deliberately narrow integration side of Checker A. It may
inspect live CTM terms and trusted `Rule`/`MultiRule` objects; the independent
`odr_checker_a` package still imports no CTM runtime or proof-producing code.

## Responsibilities

- Convert CTM pair structures into an inert, lossless `ctm.Pair` term tree.
- Convert CTM variables to deterministic first-occurrence names (`v0`, `v1`, …)
  while preserving repeated-variable identity across a complete rule.
- Convert trusted CTM rules to Checker A `RuleSpec` records.
- Convert evaluator-owned CTM goals/premises to `CheckPolicy` records.
- Convert already-expanded CTM step envelopes to `ProofReceipt` records.
- Reject cycles, improper machine lists, over-budget terms, anonymous opaque
  atoms, variables in concrete terms, and unsupported multi-conclusion rules.

The adapter does **not** run search, choose bindings, infer a candidate, extract
an allegedly valid proof from a transcript, or decide which rules are trusted.
Its `ExpandedCTMStep` input must come from the evaluator/expander and Checker A
re-verifies every resulting inference.

## Stable symbol authority

Most CTM labels and constants are identity-sensitive atoms. UUIDs, object IDs,
and memory addresses are unsuitable for a cold-replay digest. Every such atom
must therefore receive an authority-controlled stable name.

For a frozen runtime namespace:

```python
authority = SymbolAuthority.from_namespace(frozen_namespace)
adapter = CTMAdapter(authority)
```

Aliases are resolved deterministically by public-name ordering. For smaller
fixtures, `SymbolAuthority.from_mapping` requires a one-to-one explicit map and
rejects ambiguity. Unnamed identity-sensitive atoms fail closed.

`Char` and `GMPRep` atoms use their CTM value semantics and are encoded by
value. Pair cells are encoded structurally. Constructed atoms are represented
through their constructor record.

## Integration status

This is an isolated adapter prototype against Checker A wire contract v1. INT
must still freeze and approve:

1. the exact source of the trusted rule-ID/object map;
2. the frozen namespace used as symbol authority;
3. the evaluator-owned expanded-step envelope;
4. whether any active CTM rules legitimately have multiple conclusions;
5. the final CL1 receipt field mapping.

No existing runtime, planner, pack, proof, or persistence file is modified.

## Tests

The adapter tests require the repository dependencies declared by
`environment.yml` (`gmpy2` and PyYAML). From the repository parent:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v \
  cat_theo_machine.odr_ctm_adapter.test_adapter
```

Tests cover real CTM `Rule` and `MultiRule` objects, repeated bindings,
deterministic rule digests, fail-closed symbol handling, malformed machine
lists, and a rule loaded from the shipped arithmetic pack.
