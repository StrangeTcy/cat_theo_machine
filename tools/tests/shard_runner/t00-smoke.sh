#!/bin/sh
# Smoke: one attempt launches, exposes per-shard records, and finishes.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t00.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=2
export DUMMY_SLEEP=3 DUMMY_TALLY="passed: 2 failed: 0 open: 0"

. "$HERE/lib.sh"

OUT=$TEST_TMP/launch.txt
sh "$RUNNER" > "$OUT" 2>&1
ATTEMPT=$(grep '^attempt: ' "$OUT" | cut -d' ' -f2)
[ -n "$ATTEMPT" ] || fail "launcher printed no attempt id"
ADIR="$TEST_TMP/runs/$ATTEMPT"
[ -d "$ADIR" ] || fail "attempt dir missing: $ADIR"
[ -f "$ADIR/attempt.meta" ] || fail "attempt.meta missing"
grep -q '^interpreter=' "$ADIR/attempt.meta" || fail "meta lacks interpreter"
grep -q '^tested_commit=' "$ADIR/attempt.meta" || fail "meta lacks tested_commit"
grep -q '^shards=2$' "$ADIR/attempt.meta" || fail "meta lacks shards=2"
[ -f "$ADIR/token" ] || fail "token missing"

for I in 0 1; do
    [ -f "$ADIR/shard-$I.log" ] || fail "shard-$I.log missing"
    [ -d "$ADIR/shard-$I.state" ] || fail "shard-$I.state missing"
    [ -f "$ADIR/shard-$I.env" ] || fail "shard-$I.env missing"
    grep -q "HYGE_SNAPSHOT_DIR=$ADIR/shard-$I.state" "$ADIR/shard-$I.env" \
        || fail "shard-$I.env records wrong state dir"
done

for I in 0 1; do
    wait_file "$ADIR/shard-$I.pid" 10 \
        || fail "shard-$I.pid never appeared"
    wait_file "$ADIR/shard-$I.supervisor.pid" 10 \
        || fail "shard-$I.supervisor.pid never appeared"
done

# Mid-run both shards must read as running.
sleep 1
for I in 0 1; do
    status_line "$ATTEMPT" "$I" | grep -q ": running" \
        || fail "shard $I not reported running mid-run"
done

for I in 0 1; do
    wait_status "$RUNNER" "$ATTEMPT" "$I" "completed-with-report" 20 \
        || fail "shard $I never completed-with-report"
done

rm -rf "$TEST_TMP"
echo "PASS: smoke"
