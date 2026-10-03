# CL0 repository map

**Date:** 2026-10-03  
**Cut:** `f5078d5c200aa8a397a4bda165596495fdbf3450`  
**Tree:** `ea16afed7a05e66c4da326b499b572b8b55465b0`  
**Branch:** `arena/01a0fe4e-cat-theo-machine`

## Current cut

The current cut contains the task specification at `protocol/ODR-FINAL.md`, but not the remote protocol ledgers or the remote `researcher_v0` implementation.

### Active runtime and research surfaces

```text
core.py
constructors.py
context.py
graph.py
heuristics.py
invariance.py
knowledge.py
labels.py
logic.py
machine.py
main.py
matching.py
persistence.py
planner.py
proof.py
runtime.py
schemata.py
search/
testsuite.py
test_actual_searchdfs.py
validation/
```

### Parked designs, not active Python modules

```text
deduction.py.txt
firing.py.txt
grammar.py.txt
graph.py.txt
language.py.txt
mining.py.txt
```

### Active invariant substrate

`invariance.py` contains live implementations for:

```text
Preserves
Invariant
InvariantCandidate
ReachabilityPrune
SearchWithInvariant
```

The current `testsuite.py` contains invariant/pruning coverage.

### Current schema substrate

`schemata.py` contains derivation-schema storage and lookup classes:

```text
DerivationSchemaStart
DerivationSchemaGoal
DerivationSchemaPlan
LookupDerivationSchema
StoreDerivationSchema
```

The current cut does not contain the protocol S2 names/contract surface `RelationSchema`, `RelationContract`, or `FireAny`.

## Remote protocol inputs inspected

```text
origin/arena/01a05cb0-cat-theo-machine
    protocol/README.md
    protocol/TWO-PIPELINE.md
    protocol/CHARTER-v2.md
    protocol/S.md
    protocol/E.md
    protocol/F.md
    protocol/G.md
    protocol/I.md

origin/arena/01a0eca3-cat-theo-machine
    researcher_v0/
```

The remote branches are evidence/design inputs for reconciliation. They are not silently treated as active code on the current cut.

## Environment

The repository `environment.yml` requests a Conda environment named `hyge` containing Python 3.12.13, `gmpy2=2.3.0`, and `pyyaml=6.0.3`. The sandbox default is Python 3.11.2 and did not have `gmpy2` or `yaml` installed.

A disposable validation environment at `/tmp/ctm-venv` was created for the probes with Python 3.11.2, `gmpy2 2.3.1`, and PyYAML. It is not a repository artifact and must be replaced by a documented reproducible environment before release.
