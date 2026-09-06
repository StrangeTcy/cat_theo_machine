# Preflight ledger

Remote tip at hand-off: 12d2d46519fd7a45ae283bff60c277ac309d8150
Step-1 record: 364795343d9043f5bea3d19a2716b420bf664ab9

## step 1 — swallowed exception

```text
status: CLOSED
classification: PreflightTargetAbsent(item_1, LearnedMemoryCheckpointTest, lineage)
named defect: none (target absent; no swap site)
locus: testsuite.py has no LearnedMemoryCheckpointTest;
       research.py is absent on this tree
traceback: protocol/preflight/exception-traceback.txt (none produced)
```

The charter names a class and a 109-predecessor `_register_test` repro.
Neither is on this cut. Absence is recorded as LINEAGE VARIANCE.
This tree is the lineage being baselined. Waiting on a SHARED cut
carrying research.py is rejected.

## step 2 — producer/consumer pair

```text
status: recorded
probe: protocol/preflight/a1_select.py
interpreter: /tmp/hyge-venv/bin/python
PYTHONPATH: /home/user
A1Compile: yes
A1Selection: 0 — content absence, not instrument defect
A1Defect: none
```

MultiRule producer/consumer constructed off-pack. Selection on toy
`x+1=x` is 0. D11 repaired at 768ea6f in ancestry. No nosolutions
pack content added.

## step 3 — decoy shape

```text
status: recorded
file: protocol/preflight/decoy-shape.txt
talk: F-RUNNER 2026-09-05 transcripts
      logs/F-OP-BLIND-FLT-RETRY-decoy.log
      logs/F-OP-BLIND-FLT-RETRY-flt.log
live research mode: not used (research.py absent; no talk verb)
DECOY SHAPE-MATCH: yes
```

## step 4 — two-shard suite

```text
status: recorded — both shards complete
artifact: verification/2026-09-06-preflight-two-shard.txt
interpreter: /tmp/hyge-venv/bin/python
PYTHONPATH: /home/user
command: tools/shard_suite.py 0 2  and  tools/shard_suite.py 1 2
         concurrent, post defect-#1 fix
shard 0 exit: 0
shard 1 exit: 0
```

### defect #1 (repaired)

```text
ShardInstallAbort(ConversePropositionTest, testsuite.py:7448,
guard-after-navigation; AttributeError no-tail on NotUnderstood outcome)
fix commit: b28df32 — hoist three UnderstoodLabel guards above Tail^4
```

First run: shard 1 exit 1, install abort, shard-1 set unmeasured.
Post-fix rerun: both shards complete. Crash became recorded red test
`converse_proposition_test`. Shard 0 set unchanged.

### shard 0 failure set (unchanged)

```text
converse_default_mode_test
tree_insert_deep_pair_lookup_avoids_recursion_test
compare_search_modes_fill_warms_resident_pool_before_root_wave_test
```

### shard 1 failure set (first measured)

```text
heuristic_canonical_knowledge_agreement_test
converse_proposition_test
curator_report_test
compare_search_modes_finds_reusable_worker_snapshot_dir_test
```

### combined failure set

```text
converse_default_mode_test
tree_insert_deep_pair_lookup_avoids_recursion_test
compare_search_modes_fill_warms_resident_pool_before_root_wave_test
heuristic_canonical_knowledge_agreement_test
converse_proposition_test
curator_report_test
compare_search_modes_finds_reusable_worker_snapshot_dir_test
```

## step 5 — commit/tag

```text
commit: preflight (this cut)
tag: preflight-<shortsha> on this commit — this is the wave-1 base
tag preflight-e73d748: premature; stands; not the wave-1 base
[F] block: labels.py, testsuite.py
blocked on operator: none
```

Wave 1 engineers branch from the tag on this commit. INT does not write
track features. INT does not spawn Wave 1 in this cut.
