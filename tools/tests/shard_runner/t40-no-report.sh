#!/bin/sh
# No-report: exit 0 with no tally line is exited-without-report, never
# presented as completed. Exit zero alone must never read as a finished run.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t40.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=1
export DUMMY_SLEEP=1 DUMMY_EXIT=0
unset DUMMY_TALLY

. "$HERE/lib.sh"

OUT=$TEST_TMP/launch.txt
sh "$RUNNER" > "$OUT" 2>&1
ATTEMPT=$(grep '^attempt: ' "$OUT" | cut -d' ' -f2)
[ -n "$ATTEMPT" ] || fail "launcher printed no attempt id"
ADIR="$TEST_TMP/runs/$ATTEMPT"

wait_status "$RUNNER" "$ATTEMPT" 0 "exited-without-report" 20 \
    || fail "shard 0 never exited-without-report"
C="$ADIR/shard-0.completion"
grep -q '^exit_code=0$' "$C" || fail "completion lacks exit_code=0"
grep -q '^state=exited-without-report$' "$C" \
    || fail "completion state wrong"

LINE=$(status_line "$ATTEMPT" 0)
echo "$LINE" | grep -q "completed-with-report" \
    && fail "exit 0 with no tally reads as completed: $LINE"
echo "$LINE" | grep -q "exited-without-report" \
    || fail "status lacks exited-without-report: $LINE"

rm -rf "$TEST_TMP"
echo "PASS: no-report"
