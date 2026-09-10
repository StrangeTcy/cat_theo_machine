#!/bin/sh
# Preflight item 1 repro — pinned.
#
#   sh tools/preflight_item1_repro.sh exact [--no-swap]
#   sh tools/preflight_item1_repro.sh <N>  [--no-swap]
#
# Runs a predecessor set plus `learned_memory_checkpoint_test` (cursor index
# 218) in one process, in registration order. The name filter is applied at
# registration (tools/run_named_tests.py), so an unselected test is never
# constructed: the predecessor set is the only variable between runs.
#
# Two selection modes:
#
#   exact   every registration before cursor 218 accepted by shard 0 of 2.
#           That set is 109 tests -- the historical context of the swallowed
#           exception. This is the decisive mode.
#   <N>     a trailing window, cursor indices [218-N, 217]. Exploratory
#           threshold probing only; it does not reproduce the exact context
#           and never substitutes for it.
#
# Either way the ordered set of selected names and a digest of it are
# printed, so two runs can be compared instead of assumed equal. Names come
# from `tools/shard_map.py`, which walks the AST in source order and is the
# same static assignment the shard pins are computed against.
#
# The swap. With `--no-swap` the run uses the tree as it stands. Without it
# the script applies the preflight re-raise itself — replacing the
# `self.result = M.false_value` at testsuite.py:14962 with `raise` — and
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
LINE=14962
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

if [ "$N" = exact ]; then
    # The exact historical context: every registration before cursor 218
    # accepted by shard 0 of 2, in source registration order. This is where
    # 109 comes from -- it is not a trailing window of the last N.
    NAMES="$(awk '$2+0 == 0 && $1+0 < 218 {print $3}' "$MAP")"
    RULE="cursor index < 218 AND shard == 0 of 2"
else
    NAMES="$(awk -v n="$N" '$1+0 >= 218-n && $1+0 <= 217 {print $3}' "$MAP")"
    RULE="trailing window, cursor indices 218-$N .. 217"
fi
COUNT="$(printf '%s\n' "$NAMES" | grep -c .)"
DIGEST="$(printf '%s\n' "$NAMES" | sha256sum | cut -c1-64)"

echo "predecessors requested: $N"
echo "selection rule:         $RULE"
echo "predecessors selected:  $COUNT"
echo "target:                 learned_memory_checkpoint_test (index 218, shard 0)"
echo "ordered set digest:     $DIGEST"
echo
echo "--- selected predecessors, registration order ---"
printf '%s\n' "$NAMES"
echo "--- end selected predecessors ---"
echo

PYTHONPATH=/home/user /home/user/.venv/bin/python \
    tools/run_named_tests.py $NAMES learned_memory_checkpoint_test
STATUS=$?

echo
echo "run exit: $STATUS"
exit $STATUS
