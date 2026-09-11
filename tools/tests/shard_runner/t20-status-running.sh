#!/bin/sh
# Running detection: a live owned child reads as running with a live pid.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t20.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=2
export DUMMY_SLEEP=6 DUMMY_TALLY="passed: 2 failed: 0 open: 0"

. "$HERE/lib.sh"

OUT=$TEST_TMP/launch.txt
sh "$RUNNER" > "$OUT" 2>&1
ATTEMPT=$(grep '^attempt: ' "$OUT" | cut -d' ' -f2)
[ -n "$ATTEMPT" ] || fail "launcher printed no attempt id"
ADIR="$TEST_TMP/runs/$ATTEMPT"

for I in 0 1; do
    wait_file "$ADIR/shard-$I.pid" 10 \
        || fail "shard-$I.pid never appeared"
done
sleep 1

for I in 0 1; do
    LINE=$(status_line "$ATTEMPT" "$I")
    echo "$LINE" | grep -q ": running" || fail "shard $I not running: $LINE"
    PID=$(echo "$LINE" | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p')
    [ -n "$PID" ] || fail "shard $I line carries no pid: $LINE"
    [ "$PID" = "$(cat "$ADIR/shard-$I.pid")" ] \
        || fail "shard $I pid $PID != pidfile $(cat "$ADIR/shard-$I.pid")"
    kill -0 "$PID" 2>/dev/null || fail "shard $I pid $PID not alive"
done

for I in 0 1; do
    wait_status "$RUNNER" "$ATTEMPT" "$I" "completed-with-report" 20 \
        || fail "shard $I never completed"
done

rm -rf "$TEST_TMP"
echo "PASS: status-running"
