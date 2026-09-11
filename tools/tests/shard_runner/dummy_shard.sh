#!/bin/sh
# Dummy shard child for the runner tests. Same CLI as shard_suite.py:
# dummy_shard.sh <index> <shards>. Short sleeps only; never the suite.
#
#   DUMMY_SLEEP   seconds to sleep mid-run (default 0)
#   DUMMY_MARKER  when set, write "shard-<index>" to
#                 $HYGE_SNAPSHOT_DIR/marker.txt before sleeping
#   DUMMY_EXIT    exit status (default 0)
#   DUMMY_TALLY   when set, printed verbatim as the final line (the
#                 runner treats a '^passed:' line as the tally)

set -e

INDEX=$1
TOTAL=$2

echo "dummy shard $INDEX of $TOTAL pid=$$"

if [ -n "${DUMMY_MARKER:-}" ]; then
    if [ -z "${HYGE_SNAPSHOT_DIR:-}" ]; then
        echo "HYGE_SNAPSHOT_DIR unset" >&2
        exit 99
    fi
    echo "shard-$INDEX" > "$HYGE_SNAPSHOT_DIR/marker.txt"
fi

if [ "${DUMMY_SLEEP:-0}" -gt 0 ]; then
    sleep "$DUMMY_SLEEP"
fi

if [ -n "${DUMMY_TALLY:-}" ]; then
    echo "$DUMMY_TALLY"
fi

exit "${DUMMY_EXIT:-0}"
