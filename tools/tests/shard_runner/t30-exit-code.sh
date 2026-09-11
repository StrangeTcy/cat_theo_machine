#!/bin/sh
# Exit codes: a nonzero child exit is recorded in the completion record
# and surfaced by status, together with the tally it did print.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t30.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=1
export DUMMY_SLEEP=1 DUMMY_EXIT=3
export DUMMY_TALLY="passed: 1 failed: 1 open: 0"

. "$HERE/lib.sh"

OUT=$TEST_TMP/launch.txt
sh "$RUNNER" > "$OUT" 2>&1
ATTEMPT=$(grep '^attempt: ' "$OUT" | cut -d' ' -f2)
[ -n "$ATTEMPT" ] || fail "launcher printed no attempt id"
ADIR="$TEST_TMP/runs/$ATTEMPT"

wait_status "$RUNNER" "$ATTEMPT" 0 "completed-with-report" 20 \
    || fail "shard 0 never completed-with-report"
C="$ADIR/shard-0.completion"
[ -f "$C" ] || fail "completion record missing"
grep -q '^exit_code=3$' "$C" || fail "completion lacks exit_code=3"
grep -q '^state=completed-with-report$' "$C" || fail "completion state wrong"
grep -q '^tally=passed: 1 failed: 1 open: 0$' "$C" \
    || fail "completion tally wrong"

LINE=$(status_line "$ATTEMPT" 0)
echo "$LINE" | grep -q "exit=3" || fail "status hides exit 3: $LINE"
echo "$LINE" | grep -q "tally: passed: 1 failed: 1 open: 0" \
    || fail "status hides tally: $LINE"

rm -rf "$TEST_TMP"
echo "PASS: exit-code"
