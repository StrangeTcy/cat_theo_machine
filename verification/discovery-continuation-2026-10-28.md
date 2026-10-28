# Discovery continuation — 2026-10-28

Continued the interrupted operation-catalog, tensor, and named-law work. The
scope follows `SWARM_EVOLUTION_DAG.md` §7.5: finite observations alone do not
authorize proof promotion. No changes were made to `core.py`.

## Repairs

- `operation_tensor.py` stores each operation as nested machine axes. A cell
  is reached by consuming the complete argument chain and declared variable
  chain. Construction no longer inserts every coordinate tuple into a generic
  structural tree. Distinct Nat atoms representing the same value still match
  through `NatEq`; truth values match by identity. Missing cells, improper
  argument chains, and wrong arities return `EmptyList`.
- `playground.py` checks natural arguments before applying arithmetic
  predicates, checks the residue argument of `compare_modulo`, and admits only
  machine truth values as implication operands. Previously invalid nested
  predicates could return `false_value`, making two invalid expressions appear
  equal during mining. They now return `EmptyList`.
- `validation/test48_named_discovered_laws.py` uses the real file-backed
  snapshot save/load path and guards execution during Windows process spawn.
  The previous in-memory activation failed because parallel root restoration
  requires a snapshot path.
- The live `ground lemma` command and its four aliases no longer fabricate a
  derivation from descriptive strings, install an active ledger entry, reset
  its version to 1, or claim unexecuted verification and evaluation gates.
  Missing observations are handled directly; available residue observations
  remain unproved until the required evidence exists.
- `validation/run_discovery_checks.cmd` now runs the six focused discovery
  suites through the existing Anaconda environment and stops on the first
  failure. The playground edge suite imports the current `hyge` package.

## Verification record

All six focused suites completed with exit code 0 on 2026-10-28, run
individually through the Anaconda environment with the same commands as the
runner. Their dated logs are beside this report. The miner reached its final
`Discovery miner regressions passed.` marker after all 1,000 assignments.

| Check | Result | Evidence covered |
| --- | --- | --- |
| `discovery_catalog_regressions` | PASS | Empty register, goal evidence, all 15 registered operations, unary/ternary evidence, snapshot preservation |
| `discovery_tensor_axes_regressions` | PASS | All 52 cells in a small unary/binary/ternary/truth-valued corpus agree with direct evaluation; Nat aliases, environment bindings, nested reads, malformed and missing cells, invalid predicates cannot support an equation |
| `discovery_regressions` | PASS | Arithmetic results, false versus undefined values, implication composition, complete 1,000-cell ternary construction |
| `discovery_miner_regressions` | PASS | Named candidates skipped before evaluation, finite-domain scope, skipped nonbinary equation grammars, empty carrier refusal, divisibility propagation, 1,000-assignment associativity check |
| `test48_named_discovered_laws` | PASS | Independent polynomial certification, shared variable bindings, rewrite reuse outside the sampled domain, file save/load and proof replay, authority refusal, finite singleton and unsupported-equation refusals |
| `playground_edge_regressions` | PASS | Mixed constraints, quantifiers, parser/arity refusals, undefined witnesses, parameter filters and reports |

The real live console also accepted all five promotion aliases, reported that
no residue observation was available, showed an empty promotion ledger, and
exited normally. Input and output are retained as
`discovery-live-promotion-input-2026-10-28.txt` and
`discovery-live-promotion-2026-10-28.log`. This console check covers the empty
observation case; the populated observation branch now only reports the
missing proof/evaluation requirements.

## Remaining scope

- Arbitrary tensor arity does not imply arbitrary law synthesis. The current
  candidate grammar covers binary term permutations, a mixed-operation
  template, and an authored divisibility-propagation template. Nonbinary
  operation descriptions are supported by tensor evaluation and skipped by
  the binary equation grammar.
- Named polynomial laws enter the graph's active rewrite chain only after
  universal polynomial proof and Checker B replay. This is separate from
  demonstrating an evaluator/ablation/holdout-backed dual-ledger promotion.
- Named finite-domain structure bundles do not establish universal algebraic
  structures. Carrier closure, operation substitution, proof-backed template
  matching and abstract-theorem transfer remain to be implemented and checked.
- Tensor construction and lookup still recurse along each finite axis. The
  1,000-cell check demonstrates bounded Cartesian traversal, not unlimited
  axis length or a general scalability result.
- The miner still compares many equivalent permutation-generated equations.
  Its full candidate sweep remains costly even after the tensor storage fix;
  no general mining speedup is claimed.
- The complete legacy validation suite was not run. No new numbered suite
  slot or completion claim for W28, W31, or W32 was made.
