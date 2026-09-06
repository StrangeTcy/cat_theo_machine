#!/bin/sh
# Preflight item 1 repro — pinned.
#
#   sh tools/preflight_item1_repro.sh <N> [--no-swap]
#
# Runs the N tests registered immediately before
# `learned_memory_checkpoint_test` (cursor index 218) plus that test, in
# registration order, in one process. The name filter is applied at
# registration (tools/run_named_tests.py), so an unselected test is never
# constructed: N is the only variable between runs.
#
# Predecessor selection: cursor indices [218-N, 217] from
# `tools/shard_map.py`, which walks the AST in source order and is the same
# static assignment the shard pins are computed against.
#
# The swap. With `--no-swap` the run uses the tree as it stands. Without it
# the script applies the preflight re-raise itself — replacing the
# `self.result = M.false_value` at testsuite.py:14957 with `raise` — and
# restores it on exit, including on SIGTERM/SIGINT. The point of doing the
# edit inside the script is that a run killed mid-flight cannot leave the
# re-raise behind: the tree is only ever dirty while this process is alive.
# The edit is asserted against the surrounding `except Exception:` line, so
# a drifted line number fails loudly instead of editing the wrong site.
#
# This is not a baseline and does not move the shard cursor.

set -u

N="${1:?usage: sh tools/preflight_item1_repro.sh <N predecessors> [--no-swap]}"
DO_SWAP=yes
for arg in "$@"; do [ "$arg" = "--no-swap" ] && DO_SWAP=no; done

TESTSUITE=testsuite.py
LINE=14957
ORIG='            self.result = M.false_value'
NEW='            raise'

_swap () {  # _swap <want> <expect>
    python3 -c '
import sys
path, line, want, expect = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
lines = open(path, encoding="utf-8").read().split("\n")
i = line - 1
if lines[i-1].strip() != "except Exception:":
    sys.exit("line %d is not inside an except Exception: handler (%r)"
             % (line, lines[i-1]))
if lines[i] != expect:
    sys.exit("unexpected content at %s:%d: %r" % (path, line, lines[i]))
lines[i] = want
open(path, "w", encoding="utf-8").write("\n".join(lines))
' "$TESTSUITE" "$LINE" "$1" "$2"
}

if [ "$DO_SWAP" = yes ]; then
    _swap "$NEW" "$ORIG" || exit 1
    trap '_swap "$ORIG" "$NEW"' EXIT INT TERM
    echo "swap applied at $TESTSUITE:$LINE (re-raise)"
fi

MAP="$(mktemp)"
trap 'rm -f "$MAP"; _swap "$ORIG" "$NEW"' EXIT INT TERM

python3 tools/shard_map.py > "$MAP" || exit 1

NAMES="$(awk -v n="$N" '$1+0 >= 218-n && $1+0 <= 217 {print $3}' "$MAP")"
COUNT="$(printf '%s\n' "$NAMES" | grep -c .)"

echo "predecessors requested: $N"
echo "predecessors selected:  $COUNT  (cursor indices 218-$N .. 217)"
echo "target:                 learned_memory_checkpoint_test (index 218)"
echo

PYTHONPATH=/home/user /home/user/.venv/bin/python \
    tools/run_named_tests.py $NAMES learned_memory_checkpoint_test
STATUS=$?

echo
echo "run exit: $STATUS"
exit $STATUS
