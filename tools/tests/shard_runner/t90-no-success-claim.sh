#!/bin/sh
# No success claims: a failing tally is reported verbatim, and neither
# status output nor the runner itself ever frames a tally or an exit
# status of zero as success.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t90.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=1
export DUMMY_SLEEP=1 DUMMY_EXIT=0
export DUMMY_TALLY="passed: 1 failed: 4 open: 0"

. "$HERE/lib.sh"

sh "$RUNNER" > "$TEST_TMP/launch.txt" 2>&1
ATTEMPT=$(grep '^attempt: ' "$TEST_TMP/launch.txt" | cut -d' ' -f2)
[ -n "$ATTEMPT" ] || fail "launcher printed no attempt id"

wait_status "$RUNNER" "$ATTEMPT" 0 "completed-with-report" 20 \
    || fail "failing-tally shard never completed-with-report"

STATUS_OUT=$TEST_TMP/status.txt
sh "$RUNNER" --status "$ATTEMPT" > "$STATUS_OUT" 2>&1
grep -q "tally: passed: 1 failed: 4 open: 0" "$STATUS_OUT" \
    || fail "status does not carry the failing tally verbatim"
if grep -qi 'success\|all .*pass\|passed all\|no failures' "$STATUS_OUT"; then
    fail "status frames the run as success"
fi
# The runner's emitted lines (echo statements) must never frame a tally or
# an exit status as success. (Comments may use the word to forbid it.)
if grep '^[^#]*echo' "$RUNNER" \
    | grep -qi 'success\|all .*pass\|passed all\|no failures'; then
    fail "runner output frames runs as success"
fi

rm -rf "$TEST_TMP"
echo "PASS: no-success-claim"
