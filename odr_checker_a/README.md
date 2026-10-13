# ODR checker A

Checker A is an independent verifier for fully expanded, first-order proof
receipts. It is intentionally an inert, standard-library-only package: it does
not import CTM search, planner, proof generation, packs, invariant mining, or
candidate generation.

## Trust boundary

The checker accepts three values:

1. a `ProofReceipt` containing declared premises, expanded steps, and a goal;
2. an exact `TrustedRuleSet` snapshot supplied by the integrating authority;
3. an evaluator-owned `CheckPolicy` fixing the admitted task and candidates.

A step names a trusted rule and references only declared premises (`pN`) or
previous steps (`sN`). Checker A infers substitutions by matching the trusted
rule patterns itself. Producers do not supply bindings. Candidate macros are
never rules in this snapshot: candidate use must be expanded into trusted-rule
steps before checking.

The canonical SHA-256 ruleset digest binds the receipt and optional candidate
scope to the exact trusted snapshot. Every proof also requires an evaluator-owned `CheckPolicy` fixing the admitted
session, goal, and premises. Candidate-bearing policies additionally name the
admitted candidate IDs. The proof producer therefore cannot fabricate a task
premise, change the goal, or self-admit a candidate. The resulting
`CheckerReceipt` binds the verdict to the goal and complete proof receipt.

## Rejection coverage

Checker A rejects malformed or unsafe rulesets, stale ruleset digests, unknown
rules, fabricated/future references, premise-count and pattern mismatches,
wrong repeated-variable bindings, conclusion mutations, unbound variables,
foreign goals, and candidate session/ruleset mismatches.

## Integration contract

The package deliberately does not translate live CTM objects. INT should own a
thin adapter with this shape:

```text
frozen CTM rule snapshot + expanded derivation receipt
    -> inert Atom/Application/Variable records
    -> evaluator-owned CheckPolicy
    -> check_proof(receipt, trusted_rules, policy)
    -> immutable CheckerReceipt
```

The adapter must snapshot only authority-approved rule IDs and must reject CTM
terms it cannot represent. It must not place a candidate-generated macro in the
trusted snapshot. Keeping the adapter outside this package lets CL1 change wire
record names without coupling checker semantics to proof production.

## Cold-process wire boundary

Checker A also defines three strict, versioned JSON inputs:

```text
ctm.odr.checker-a.task-policy.v1
ctm.odr.checker-a.trusted-rules.v1
ctm.odr.checker-a.proof-receipt.v1
```

Unknown, missing, or duplicate fields are rejected. Decoding enforces limits on
file bytes, strings, term depth/node count, rules, premises, steps, and admitted
candidates. Concrete task/proof terms cannot contain variables.

Run a check in a fresh process:

```bash
python -m odr_checker_a.cli \
  --policy task-policy.json \
  --rules trusted-rules.json \
  --proof proof-receipt.json \
  --output-dir artifacts
```

The CLI writes a canonical, content-addressed
`sha256-….checker-receipt.json`. Exit status is `0` for an accepted proof, `1`
for a well-formed rejected proof, and `2` for malformed input or artifact I/O
failure. It does not load CTM runtime or proof-producing modules.

## Run tests

From the repository root:

```bash
python -m unittest -v odr_checker_a.test_checker odr_checker_a.test_wire
```
