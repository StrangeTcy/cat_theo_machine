#!/bin/sh
# Untouched bystanders: an unrelated live process and an unrelated file
# survive a full attempt; and the runner sends no signals -- every use of
# kill in it is a signal-0 liveness probe.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t80.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=2
export DUMMY_SLEEP=3 DUMMY_TALLY="passed: 2 failed: 0 open: 0"

. "$HERE/lib.sh"

sleep 60 &
BYSTANDER=$!
echo "bystander-content" > "$TEST_TMP/bystander.txt"

sh "$RUNNER" > "$TEST_TMP/launch.txt" 2>&1
ATTEMPT=$(grep '^attempt: ' "$TEST_TMP/launch.txt" | cut -d' ' -f2)
[ -n "$ATTEMPT" ] || fail "launcher printed no attempt id"

for I in 0 1; do
    wait_status "$RUNNER" "$ATTEMPT" "$I" "completed-with-report" 20 \
        || fail "shard $I never completed"
done
sh "$RUNNER" --status "$ATTEMPT" > /dev/null 2>&1
sh "$RUNNER" --status > /dev/null 2>&1

kill -0 "$BYSTANDER" 2>/dev/null \
    || fail "unrelated process $BYSTANDER died during the attempt"
[ "$(cat "$TEST_TMP/bystander.txt")" = "bystander-content" ] \
    || fail "unrelated file changed during the attempt"

# No signal-sending kill: allow only `kill -0` probes and comments.
if grep -n 'kill' "$RUNNER" | grep -v 'kill -0' | grep -qv '^.*#'; then
    fail "runner sends signals: $(grep -n 'kill' "$RUNNER" \
        | grep -v 'kill -0' | grep -v '#')"
fi

kill -9 "$BYSTANDER" 2>/dev/null || true
rm -rf "$TEST_TMP"
echo "PASS: untouched"
