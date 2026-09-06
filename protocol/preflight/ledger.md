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
status: recorded
artifact: verification/2026-09-06-preflight-two-shard.txt
interpreter: /tmp/hyge-venv/bin/python
PYTHONPATH: /home/user
command: tools/shard_suite.py 0 2  and  tools/shard_suite.py 1 2
         concurrent
shard 0 exit: 0
shard 1 exit: 1
```

Failure names and the shard-1 abort are in the artifact.

## step 5 — commit/tag

```text
commit: preflight (this cut)
tag: preflight-<shortsha> on this commit
wave 1 base tag: preflight-<shortsha>@<hash>
[F] block: labels.py, testsuite.py
blocked on operator: none
```

Wave 1 engineers do not branch until INT reports `preflight: complete`.
INT does not write track features. INT does not spawn Wave 1.
