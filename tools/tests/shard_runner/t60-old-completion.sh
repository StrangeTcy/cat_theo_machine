#!/bin/sh
# Old completions: a finished attempt keeps its own record; a newer
# attempt starts from running and never inherits the older one's state.
# Bare --status follows the latest attempt.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t60.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=1

. "$HERE/lib.sh"

export DUMMY_SLEEP=1 DUMMY_TALLY="passed: 1 failed: 0 open: 0" DUMMY_EXIT=0
sh "$RUNNER" > "$TEST_TMP/old.txt" 2>&1
OLD=$(grep '^attempt: ' "$TEST_TMP/old.txt" | cut -d' ' -f2)
[ -n "$OLD" ] || fail "old attempt: no attempt id"
wait_status "$RUNNER" "$OLD" 0 "completed-with-report" 20 \
    || fail "old attempt never completed"

export DUMMY_SLEEP=8
unset DUMMY_TALLY
sh "$RUNNER" > "$TEST_TMP/new.txt" 2>&1
NEW=$(grep '^attempt: ' "$TEST_TMP/new.txt" | cut -d' ' -f2)
[ -n "$NEW" ] || fail "new attempt: no attempt id"
[ "$NEW" != "$OLD" ] || fail "new attempt reused old id"

# New attempt must read as running, never as the old attempt's completion.
sleep 2
status_line "$NEW" 0 | grep -q ": running" \
    || fail "new attempt not running: $(status_line "$NEW" 0)"
status_line "$NEW" 0 | grep -q "completed-with-report" \
    && fail "new attempt inherited old completion"

# Old record intact where it was.
status_line "$OLD" 0 | grep -q "completed-with-report" \
    || fail "old attempt record disturbed"

# Bare --status follows the latest attempt.
sh "$RUNNER" --status 2>/dev/null | grep -q "^attempt: $NEW$" \
    || fail "bare --status does not follow the latest attempt"

wait_status "$RUNNER" "$NEW" 0 "exited-without-report" 20 \
    || fail "new attempt never exited-without-report"

rm -rf "$TEST_TMP"
echo "PASS: old-completion"
