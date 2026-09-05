#!/bin/sh
# F-tools acceptance battery runner.
#
# Regenerates the acceptance artifact from this tree: relative paths
# only, deterministic output -- no timestamps, no absolute paths -- so
# a rerun from a fresh copy of the tree is byte-identical. Run from
# the repository root:
#   tools/f-tools-battery.sh > logs/f-tools-acceptance-battery-<date>.txt
#
# The name-check pattern is assembled from fragments so that this
# file, the checker, carries none of the tokens it checks for.

set -u

FIXTURES="logs/fixtures/toy-live-protocol.log logs/fixtures/ground-evaluation.log logs/fixtures/blind-geometry-dependencies.log logs/fixtures/incident-misattributed-teaching.log"
TRANSCRIPTS=$(ls logs/2*-F-RUNNER-decoy.log logs/2*-F-RUNNER-target.log 2>/dev/null | sort)

echo "F-tools acceptance battery"
echo "runner: tools/f-tools-battery.sh (this tree)"
echo "grader: tools/f2_grader.sh; oracle: tools/f2-grading-fixtures.spec.md (T4 as amended)"
echo
echo "== name-token grep over the grading scripts (five tokens, case-insensitive) =="
pattern='fe''rmat|fl''t|noso''lutions|wil''es|fr''ey'
namehits=0
for s in tools/f2_grader.sh tools/f3-residual-diff.sh tools/f3_batch_diff.sh tools/f4_auditor.sh tools/f2-outcome-class.sh; do
    n=$(grep -c -i -E "$pattern" "$s")
    if [ "$n" != "0" ]; then
        echo "$s: $n hits"
        namehits=1
    fi
done
if [ "$namehits" = "0" ]; then
    echo "zero hits in every grading script"
else
    echo "NAME-TOKEN HIT -- battery fails"
fi
echo
echo "== F2: script versus oracle, four fixtures =="
for f in $FIXTURES; do
    echo "-- $(basename "$f")"
    tools/f2_grader.sh "$f"
done
echo "oracle: T1 3/2/0/0 cite 2-1 ; T2 2/0/0/0 ; T3 1/0/0/0 ; T4 (amended) 1/1/0/0 cite 0-1"
echo
echo "== F3 batch identity matrix: four fixtures plus the F-RUNNER transcripts of this branch =="
tools/f3_batch_diff.sh $FIXTURES $TRANSCRIPTS
echo "batch exit=$?"
echo
echo "== F4 auditor sheets, four fixtures =="
for f in $FIXTURES; do
    tools/f4_auditor.sh "$f"
    echo "--"
done
