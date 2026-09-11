#!/bin/sh
# Killed processes, two scenarios.
# A: the shard child is killed mid-run. The supervisor survives, reaps it,
#    and writes exited-without-report with the true (nonzero) exit status.
# B: the supervisor itself is killed, then its child. No completion record
#    can be written; status must read interrupted-or-unknown, and no stale
#    record may appear afterwards.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"
TEST_TMP=$(mktemp -d "${TMPDIR:-/tmp}/shard-runner-t50.XXXXXXXX")
export SHARD_RUNS_DIR="$TEST_TMP/runs"
export SHARD_SUITE_CMD="$HERE/dummy_shard.sh"
export SHARDS=1
export DUMMY_SLEEP=30
unset DUMMY_TALLY

. "$HERE/lib.sh"

cleanup_pids() {
    for P in "$TEST_TMP/runs/$1"/shard-0.pid \
             "$TEST_TMP/runs/$1"/shard-0.supervisor.pid; do
        if [ -f "$P" ]; then
            kill -9 "$(cat "$P")" 2>/dev/null || true
        fi
    done
}

# --- scenario A: kill the child ---
sh "$RUNNER" > "$TEST_TMP/a.txt" 2>&1
A=$(grep '^attempt: ' "$TEST_TMP/a.txt" | cut -d' ' -f2)
[ -n "$A" ] || fail "scenario A: no attempt id"
ADIR="$TEST_TMP/runs/$A"
wait_file "$ADIR/shard-0.pid" 10 || fail "scenario A: no child pid"
wait_file "$ADIR/shard-0.supervisor.pid" 10 || fail "scenario A: no sup pid"
CHILD=$(cat "$ADIR/shard-0.pid")
kill -0 "$CHILD" 2>/dev/null || fail "scenario A: child not alive pre-kill"
kill -9 "$CHILD"
wait_status "$RUNNER" "$A" 0 "exited-without-report" 20 \
    || fail "scenario A: killed child never exited-without-report"
C_EC=$(grep '^exit_code=' "$ADIR/shard-0.completion" | cut -d= -f2)
[ "$C_EC" != "0" ] || fail "scenario A: killed child recorded exit 0"

# --- scenario B: kill the supervisor, then the child ---
sh "$RUNNER" > "$TEST_TMP/b.txt" 2>&1
B=$(grep '^attempt: ' "$TEST_TMP/b.txt" | cut -d' ' -f2)
[ -n "$B" ] || fail "scenario B: no attempt id"
[ "$B" != "$A" ] || fail "scenario B: attempt id reused"
BDIR="$TEST_TMP/runs/$B"
wait_file "$BDIR/shard-0.pid" 10 || fail "scenario B: no child pid"
wait_file "$BDIR/shard-0.supervisor.pid" 10 \
    || fail "scenario B: no supervisor pid"
SUP=$(cat "$BDIR/shard-0.supervisor.pid")
kill -9 "$SUP"
sleep 2
# Child still owned and alive: still running.
status_line "$B" 0 | grep -q ": running" \
    || fail "scenario B: orphaned live child not running"
BCHILD=$(cat "$BDIR/shard-0.pid")
kill -9 "$BCHILD"
sleep 3
status_line "$B" 0 | grep -q "interrupted-or-unknown" \
    || fail "scenario B: dead child with dead supervisor not interrupted"
[ ! -f "$BDIR/shard-0.completion" ] \
    || fail "scenario B: completion appeared with no supervisor"
sleep 3
[ ! -f "$BDIR/shard-0.completion" ] \
    || fail "scenario B: stale completion appeared late"

cleanup_pids "$A"
cleanup_pids "$B"
rm -rf "$TEST_TMP"
echo "PASS: killed"
