#!/bin/sh
# F3 residual diff, per fable 5.1 step 3.
#
# Compares two F-RUNNER transcripts on the three axes the fable names:
# the attempt cost, the count of rules with a genuine partial match,
# and the residual record root. Text extraction only; it edits nothing
# and decides nothing beyond equality of those three numbers. The
# embedded goal term inside the residual record is not an axis -- the
# two logs hold two different sentences by design.
#
# Usage: tools/f3-residual-diff.sh <decoy-log> <target-log>
# Exit 0  residuals identical on all three axes
#       1  distinct (the differing axes are named)
#       2  usage error, missing file, or unreadable numbers

set -u

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <decoy-log> <target-log>" >&2
    exit 2
fi

for path in "$1" "$2"; do
    if [ ! -f "$path" ]; then
        echo "F3: no such transcript: $path" >&2
        exit 2
    fi
done

decoy_cost=$(grep -m1 '^FAILED\. cost=' "$1" | sed 's/^FAILED\. cost=\([0-9][0-9]*\);.*$/\1/')
decoy_partial=$(grep -m1 'rules with a genuine partial match:' "$1" | sed 's/^.*genuine partial match: \([0-9][0-9]*\).*$/\1/')
decoy_root=$(grep -m1 '^residual record:' "$1" | sed 's/^residual record: (\([a-z-][a-z-]*\).*$/\1/')

target_cost=$(grep -m1 '^FAILED\. cost=' "$2" | sed 's/^FAILED\. cost=\([0-9][0-9]*\);.*$/\1/')
target_partial=$(grep -m1 'rules with a genuine partial match:' "$2" | sed 's/^.*genuine partial match: \([0-9][0-9]*\).*$/\1/')
target_root=$(grep -m1 '^residual record:' "$2" | sed 's/^residual record: (\([a-z-][a-z-]*\).*$/\1/')

if [ -z "${decoy_cost:-}" ] || [ -z "${decoy_partial:-}" ] || [ -z "${decoy_root:-}" ]; then
    echo "F3: cannot read cost/partial/root from $1" >&2
    exit 2
fi
if [ -z "${target_cost:-}" ] || [ -z "${target_partial:-}" ] || [ -z "${target_root:-}" ]; then
    echo "F3: cannot read cost/partial/root from $2" >&2
    exit 2
fi

echo "F3 decoy : cost=$decoy_cost partial=$decoy_partial root=$decoy_root"
echo "F3 target: cost=$target_cost partial=$target_partial root=$target_root"

verdict="identical"
if [ "$decoy_cost" != "$target_cost" ]; then
    echo "F3: cost differs ($decoy_cost vs $target_cost)"
    verdict="distinct"
fi
if [ "$decoy_partial" != "$target_partial" ]; then
    echo "F3: partial matches differ ($decoy_partial vs $target_partial)"
    verdict="distinct"
fi
if [ "$decoy_root" != "$target_root" ]; then
    echo "F3: residual root differs ($decoy_root vs $target_root)"
    verdict="distinct"
fi

echo "F3: $verdict"
if [ "$verdict" = "identical" ]; then
    exit 0
fi
exit 1
