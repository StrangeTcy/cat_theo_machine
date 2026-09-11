#!/bin/sh
# Isolation: each shard gets a distinct HYGE_SNAPSHOT_DIR, and a marker
# written by one shard is visible only in its own state dir.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t10.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=2
export DUMMY_SLEEP=4 DUMMY_MARKER=1 DUMMY_TALLY="passed: 2 failed: 0 open: 0"

. "$HERE/lib.sh"

OUT=$TEST_TMP/launch.txt
sh "$RUNNER" > "$OUT" 2>&1
ATTEMPT=$(grep '^attempt: ' "$OUT" | cut -d' ' -f2)
[ -n "$ATTEMPT" ] || fail "launcher printed no attempt id"
ADIR="$TEST_TMP/runs/$ATTEMPT"

S0="$ADIR/shard-0.state"
S1="$ADIR/shard-1.state"
[ "$S0" != "$S1" ] || fail "state dirs identical"

# Mid-run: shard 0's marker exists in its own dir, absent from shard 1's.
wait_file "$S0/marker.txt" 10 || fail "shard-0 marker never written"
[ "$(cat "$S0/marker.txt")" = "shard-0" ] || fail "shard-0 marker wrong"
# Shard 1 writes its marker at once too; check it landed in ITS dir.
wait_file "$S1/marker.txt" 10 || fail "shard-1 marker never written"
[ "$(cat "$S1/marker.txt")" = "shard-1" ] || fail "shard-1 marker wrong"
[ "$(cat "$S0/marker.txt")" != "$(cat "$S1/marker.txt")" ] \
    || fail "markers indistinguishable across shards"

for I in 0 1; do
    wait_status "$RUNNER" "$ATTEMPT" "$I" "completed-with-report" 20 \
        || fail "shard $I never completed"
done

rm -rf "$TEST_TMP"
echo "PASS: isolation"
