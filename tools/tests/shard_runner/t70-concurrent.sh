#!/bin/sh
# Concurrent launchers: two invocations at once get distinct attempt dirs
# with independent per-shard records, and both finish.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t70.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=2
export DUMMY_SLEEP=5 DUMMY_MARKER=1 DUMMY_TALLY="passed: 2 failed: 0 open: 0"

. "$HERE/lib.sh"

sh "$RUNNER" > "$TEST_TMP/one.txt" 2>&1 &
sh "$RUNNER" > "$TEST_TMP/two.txt" 2>&1 &
wait

ONE=$(grep '^attempt: ' "$TEST_TMP/one.txt" | cut -d' ' -f2)
TWO=$(grep '^attempt: ' "$TEST_TMP/two.txt" | cut -d' ' -f2)
[ -n "$ONE" ] || fail "first launcher printed no attempt id"
[ -n "$TWO" ] || fail "second launcher printed no attempt id"
[ "$ONE" != "$TWO" ] || fail "concurrent launchers shared attempt $ONE"
[ -d "$TEST_TMP/runs/$ONE" ] || fail "attempt dir missing: $ONE"
[ -d "$TEST_TMP/runs/$TWO" ] || fail "attempt dir missing: $TWO"

# Independent tokens.
[ "$(cat "$TEST_TMP/runs/$ONE/token")" != \
    "$(cat "$TEST_TMP/runs/$TWO/token")" ] || fail "tokens identical"

# Both attempts show both shards running mid-run.
sleep 1
for A in "$ONE" "$TWO"; do
    for I in 0 1; do
        status_line "$A" "$I" | grep -q ": running" \
            || fail "attempt $A shard $I not running"
    done
done

# Each shard's marker carries its own index, in its own attempt's dir.
for A in "$ONE" "$TWO"; do
    for I in 0 1; do
        M="$TEST_TMP/runs/$A/shard-$I.state/marker.txt"
        wait_file "$M" 15 || fail "attempt $A shard $I marker missing"
        [ "$(cat "$M")" = "shard-$I" ] \
            || fail "attempt $A shard $I marker wrong"
    done
done

for A in "$ONE" "$TWO"; do
    for I in 0 1; do
        wait_status "$RUNNER" "$A" "$I" "completed-with-report" 20 \
            || fail "attempt $A shard $I never completed"
    done
done

rm -rf "$TEST_TMP"
echo "PASS: concurrent"
