# Track S ledger

Base: `eng-base-0-partition@7c62ca2` (`7c62ca2c6b9f12f3f49e44ae1f7b89d6d2c99ced`).
Branch: `work/S/eng-base-0-partition@7c62ca2/r1` (single-session mode).

## S1 — relation contracts

Status: **green** (targeted `[S]` test).

What landed in the `[S]` blocks:

- `labels.py`: added `RelationArityLabel`, `ExtensionalAtLabel`,
  `CongruentLabel` (classes + instances), and registered them in
  `sync_from_namespace`.
- `persistence.py`: added the three names to `SNAPSHOT_SYMBOL_NAMES`.
- `testsuite.py`: added machine terms `RelationArity(R, n)` and
  `ExtensionalAt(R, position)` as Step-39 contract-port terms, and added
  `RelationContractRequiredTest` registered inside the shard guard.
- `protocol/S.md`: this file.

Acceptance:
- `RelationArity` and `ExtensionalAt` compile as contract terms for
  `DividesLabel` and `CongruentLabel`.
- The contract protects the extensional port through `ContractViolation`.
- Same arity and shape without `ExtensionalAt` does not protect that port
  (negative control inside S1).

Test result (host script, `.venv` Python 3.11 + gmpy2):
`relation_contract_required_test` 1/1 green; registered report:
`All the tests have passed.`

## Ground-truth notes for later S phases

- `Congruent` as a relation head is now a label but has no pack rules yet;
  teaching it through the `rule:`/`fact:` path is a later S-phase item and
  needs a congruence pack or training record.
- `research.py` is absent at this lineage. S2/S3 surfaces that name it are
  still open `[SHARED]` re-maps (recorded in `protocol/research_protocol.md`).

## Open [SHARED] for S

1. `research.py` re-map (blocks S2/S3 surface assignment).
2. `Congruent` pack/record source for rule/fact teaching (blocks the "teach
   Congruent via existing path" half beyond the contract-term proof).
