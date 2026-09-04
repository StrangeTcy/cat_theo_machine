#!/bin/sh
# F2 outcome-class grader -- companion to tools/f2_grader.sh.
#
# tools/f2_grader.sh (ported from arena/01a06da9-cat-theo-machine)
# counts operator compliance: taught theorems, unlock evidence,
# circular and computable requests, cite coverage. This script grades
# the other half: the machine's outcome class per transcript, by the
# A/B/C/D scheme fixed in research_protocol.md:
#   D  goal closed -- the attempt reply begins "goal closed. cost="
#   C  policy-predicted -- a "[learned policy, support N episodes]"
#      line predicts a helpful rule shape
#   B  blocked but characterized -- "dependency requests from attempted
#      rules:" names concrete formal premises
#   A  uncharacterized stall -- "dependency characterized: no"
# The strongest class present wins; the markers are the machine's own
# reply strings, so the grader reads text and edits nothing. It does
# not score semantic roles -- that is the F4 sheet, whose roles are
# fixed in research_protocol.md.
#
# Usage: tools/f2_grader.sh <transcript>
# Exit 0 graded; 2 usage error, missing file, or no class marker found.

set -u

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <transcript>" >&2
    exit 2
fi

if [ ! -f "$1" ]; then
    echo "F2: no such transcript: $1" >&2
    exit 2
fi

if grep -q 'goal closed\. cost=' "$1"; then
    echo "F2: class D -- closed"
    echo "F2 evidence: $(grep -m1 'goal closed\. cost=' "$1")"
    exit 0
fi

if grep -q '\[learned policy, support' "$1"; then
    echo "F2: class C -- policy-predicted"
    echo "F2 evidence: $(grep -m1 '\[learned policy, support' "$1")"
    exit 0
fi

if grep -q 'dependency requests from attempted rules:' "$1"; then
    echo "F2: class B -- blocked, characterized"
    echo "F2 evidence: $(grep -m1 'dependency requests from attempted rules:' "$1")"
    exit 0
fi

if grep -q 'dependency characterized: no' "$1"; then
    echo "F2: class A -- uncharacterized stall"
    echo "F2 evidence: $(grep -m1 'dependency characterized: no' "$1" | sed 's/^ *//')"
    echo "F2 attempt: $(grep -m1 '^FAILED\. cost=' "$1")"
    exit 0
fi

echo "F2: no class marker found in $1" >&2
exit 2
