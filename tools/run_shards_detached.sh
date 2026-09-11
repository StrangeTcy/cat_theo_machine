#!/bin/sh
# Run the default-suite shards detached, with output on disk.
#
# A sandbox reset kills running processes, and a killed shard run leaves
# nothing behind: `shard_suite.py` prints its tally only at the end, so an
# hour of compute interrupted is an hour of compute with no record of how
# far it got. Launching detached with the log on disk means a reset
# costs the run, not the evidence.
#
# It does not make a run survive a sandbox restart -- nothing does -- and
# it is not a substitute for `tools/recover.sh`, which protects the tree
# rather than the measurement.
#
# Every launch creates one unique attempt directory; previous attempts are
# never overwritten, cleaned, or otherwise touched. Each shard of an
# attempt gets its own state directory (passed as its HYGE_SNAPSHOT_DIR),
# its own log, its own pid record, and its own completion record. A
# per-shard supervisor process launches the shard child, waits for it, and
# writes the completion record after the child exits, with the true exit
# status and the log digest.
#
# Shard states, and only these:
#   running                  child alive and owned by this attempt
#   completed-with-report    child exited and the log holds a tally line
#   exited-without-report    child exited and the log holds no tally line
#   interrupted-or-unknown   child gone (or never launched) with no
#                            completion record; nothing may be concluded
# A tally line or an exit status of zero is reported verbatim and is never
# presented as success: a tally can carry failures, and an exit without a
# tally is not a completed run.
#
# Layout of one attempt directory:
#   attempt.meta           interpreter, suite, tested commit, shards, start
#   token                  attempt ownership token (child process check)
#   shard-<i>.log          child stdout/stderr
#   shard-<i>.pid          child pid
#   shard-<i>.supervisor.pid  supervisor pid
#   shard-<i>.env          recorded per-shard environment
#   shard-<i>.state/       this shard's HYGE_SNAPSHOT_DIR
#   shard-<i>.completion   written by the supervisor after the child exits
#   supervisor-<i>.log     the supervisor's own log
#
#   sh tools/run_shards_detached.sh              launch every shard
#   sh tools/run_shards_detached.sh --status     status of the latest attempt
#   sh tools/run_shards_detached.sh --status ID  status of attempt ID
#
# Environment:
#   VENV               interpreter home (default $HOME/.venv); skipped in
#                      test-command mode
#   SHARDS             shard count (default 2)
#   SHARD_RUNS_DIR     attempt root; absolute, or relative to the repo root
#                      (default logs/shard-runs)
#   SHARD_SUITE        suite script (default tools/shard_suite.py)
#   SHARD_PYTHONPATH   PYTHONPATH for the child (default /home/user)
#   SHARD_SUITE_CMD    test-only override: an executable run INSTEAD OF the
#                      interpreter plus suite, with the same <index> <shards>
#                      arguments. Used by the runner's own short tests with
#                      dummy commands; never for admission.

set -e

# The supervisor re-enters this script, already detached, with a fixed
# working directory; everything it needs arrives absolute via the
# environment so no path is ever resolved against the wrong directory.
if [ -n "${REPO_ROOT:-}" ]; then
    :
else
    REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
fi
SCRIPT_PATH="$REPO_ROOT/tools/run_shards_detached.sh"
SHARDS="${SHARDS:-2}"
SHARD_SUITE="${SHARD_SUITE:-tools/shard_suite.py}"
SHARD_PYTHONPATH="${SHARD_PYTHONPATH:-/home/user}"

resolve_runs_dir() {
    case "${SHARD_RUNS_DIR:-logs/shard-runs}" in
        /*) printf '%s\n' "$SHARD_RUNS_DIR" ;;
        *) printf '%s\n' "$REPO_ROOT/logs/shard-runs" ;;
    esac
}

utc_now() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

# True when $1 names a live process carrying this attempt's token.
# The token is passed in the child's environment, so an unrelated or
# recycled pid can never satisfy the check while /proc is readable.
# This probes only (signal 0); the script sends no signal anywhere.
child_owned_alive() {
    pid=$1
    token=$2
    case "$pid" in
        ''|*[!0-9]*) return 1 ;;
    esac
    if kill -0 "$pid" 2>/dev/null; then
        :
    else
        return 1
    fi
    if [ -r "/proc/$pid/environ" ]; then
        if tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | grep -qx "SHARD_RUN_TOKEN=$token"; then
            return 0
        fi
        return 1
    fi
    return 0
}

if [ "${1:-}" = "__supervise" ]; then
    # Internal: one detached supervisor per shard. Never invoked by hand.
    # Args: __supervise <attempt-dir> <index> <shards>
    ATTEMPT_DIR=$2
    INDEX=$3
    TOTAL=$4
    cd "$REPO_ROOT"
    TOKEN=$(cat "$ATTEMPT_DIR/token")
    LOG="$ATTEMPT_DIR/shard-$INDEX.log"
    STATE="$ATTEMPT_DIR/shard-$INDEX.state"
    echo "$$" > "$ATTEMPT_DIR/shard-$INDEX.supervisor.pid"
    {
        echo "HYGE_SNAPSHOT_DIR=$STATE"
        echo "SHARD_RUN_TOKEN=$TOKEN"
        echo "PYTHONPATH=$SHARD_PYTHONPATH"
    } > "$ATTEMPT_DIR/shard-$INDEX.env"
    if [ -n "${SHARD_SUITE_CMD:-}" ]; then
        HYGE_SNAPSHOT_DIR="$STATE" SHARD_RUN_TOKEN="$TOKEN" \
            PYTHONPATH="$SHARD_PYTHONPATH" \
            "$SHARD_SUITE_CMD" "$INDEX" "$TOTAL" >> "$LOG" 2>&1 &
    else
        HYGE_SNAPSHOT_DIR="$STATE" SHARD_RUN_TOKEN="$TOKEN" \
            PYTHONPATH="$SHARD_PYTHONPATH" \
            "$VENV/bin/python" -u "$SHARD_SUITE" "$INDEX" "$TOTAL" >> "$LOG" 2>&1 &
    fi
    CHILD=$!
    echo "$CHILD" > "$ATTEMPT_DIR/shard-$INDEX.pid"
    CHILD_EC=0
    wait "$CHILD" || CHILD_EC=$?
    # Completion is written only here: after the child has exited, with
    # the exit status wait(2) reported and the digest of the log as it
    # stands. Written via rename so a concurrent reader never sees half.
    DIGEST=$(sha256sum "$LOG" | awk '{print $1}')
    TALLY=$(grep -m1 '^passed:' "$LOG" 2>/dev/null || true)
    if [ -n "$TALLY" ]; then
        STATE_WORD="completed-with-report"
    else
        STATE_WORD="exited-without-report"
    fi
    {
        echo "state=$STATE_WORD"
        echo "exit_code=$CHILD_EC"
        echo "child_pid=$CHILD"
        echo "log_sha256=$DIGEST"
        echo "finished_utc=$(utc_now)"
        if [ -n "$TALLY" ]; then
            echo "tally=$TALLY"
        fi
    } > "$ATTEMPT_DIR/shard-$INDEX.completion.tmp"
    mv "$ATTEMPT_DIR/shard-$INDEX.completion.tmp" \
        "$ATTEMPT_DIR/shard-$INDEX.completion"
    exit 0
fi

if [ "${1:-}" = "--status" ]; then
    RUNS_DIR=$(resolve_runs_dir)
    if [ -n "${2:-}" ]; then
        ATTEMPT_DIR="$RUNS_DIR/$2"
        if [ ! -f "$ATTEMPT_DIR/attempt.meta" ]; then
            echo "no such attempt: $2" >&2
            exit 1
        fi
    else
        ATTEMPT_DIR=""
        for META in "$RUNS_DIR"/*/attempt.meta; do
            if [ -f "$META" ]; then
                ATTEMPT_DIR=$(dirname "$META")
            fi
        done
        if [ -z "$ATTEMPT_DIR" ]; then
            echo "no attempts yet under $RUNS_DIR"
            exit 0
        fi
    fi
    ATTEMPT_ID=$(basename "$ATTEMPT_DIR")
    echo "attempt: $ATTEMPT_ID"
    echo "attempt-dir: $ATTEMPT_DIR"
    cat "$ATTEMPT_DIR/attempt.meta"
    TOKEN=$(cat "$ATTEMPT_DIR/token")
    N=0
    SHARD_TOTAL=$(grep '^shards=' "$ATTEMPT_DIR/attempt.meta" | cut -d= -f2)
    while [ "$N" -lt "$SHARD_TOTAL" ]; do
        LOG="$ATTEMPT_DIR/shard-$N.log"
        if [ -f "$ATTEMPT_DIR/shard-$N.completion" ]; then
            C_STATE=$(grep '^state=' "$ATTEMPT_DIR/shard-$N.completion" | cut -d= -f2)
            C_EXIT=$(grep '^exit_code=' "$ATTEMPT_DIR/shard-$N.completion" | cut -d= -f2)
            C_TALLY=$(grep '^tally=' "$ATTEMPT_DIR/shard-$N.completion" | cut -d= -f2- || true)
            LINE="shard $N: $C_STATE exit=$C_EXIT log=$LOG"
            if [ -n "$C_TALLY" ]; then
                LINE="$LINE tally: $C_TALLY"
            fi
            echo "$LINE"
        else
            PID=""
            if [ -f "$ATTEMPT_DIR/shard-$N.pid" ]; then
                PID=$(cat "$ATTEMPT_DIR/shard-$N.pid")
            fi
            if [ -n "$PID" ] && child_owned_alive "$PID" "$TOKEN"; then
                LINES=0
                if [ -f "$LOG" ]; then
                    LINES=$(wc -l < "$LOG")
                fi
                echo "shard $N: running pid=$PID log_lines=$LINES log=$LOG"
            else
                SUP_ALIVE="no"
                if [ -f "$ATTEMPT_DIR/shard-$N.supervisor.pid" ]; then
                    SUP_PID=$(cat "$ATTEMPT_DIR/shard-$N.supervisor.pid")
                    if [ -n "$SUP_PID" ] && child_owned_alive "$SUP_PID" "$TOKEN"; then
                        SUP_ALIVE="yes"
                    fi
                fi
                if [ "$SUP_ALIVE" = "yes" ]; then
                    echo "shard $N: running (starting) log=$LOG"
                else
                    echo "shard $N: interrupted-or-unknown (no completion record) log=$LOG"
                fi
            fi
        fi
        N=$((N + 1))
    done
    exit 0
fi

# Launch mode.
RUNS_DIR=$(resolve_runs_dir)
mkdir -p "$RUNS_DIR"
export REPO_ROOT
export RUNS_DIR
export SHARDS
export SHARD_SUITE
export SHARD_PYTHONPATH
export VENV="${VENV:-$HOME/.venv}"
export SHARD_SUITE_CMD="${SHARD_SUITE_CMD:-}"

if [ -z "$SHARD_SUITE_CMD" ] && [ ! -x "$VENV/bin/python" ]; then
    echo "no venv at $VENV -- run 'sh tools/recover.sh' first" >&2
    exit 1
fi
if [ -n "$SHARD_SUITE_CMD" ] && [ ! -x "$SHARD_SUITE_CMD" ]; then
    echo "test command not executable: $SHARD_SUITE_CMD" >&2
    exit 1
fi

# Atomic mkdir is the uniqueness gate: two concurrent launchers can never
# share an attempt directory, whatever the clock says.
STAMP=$(date -u +%Y%m%d-%H%M%S)-$$
ATTEMPT_ID="$STAMP"
ATTEMPT_DIR="$RUNS_DIR/$ATTEMPT_ID"
SUFFIX=0
while ! mkdir "$ATTEMPT_DIR" 2>/dev/null; do
    SUFFIX=$((SUFFIX + 1))
    ATTEMPT_ID="$STAMP-$SUFFIX"
    ATTEMPT_DIR="$RUNS_DIR/$ATTEMPT_ID"
done
echo "$ATTEMPT_ID" > "$ATTEMPT_DIR/token"

cd "$REPO_ROOT"
TESTED_COMMIT="unknown (git unavailable)"
if git rev-parse HEAD >/dev/null 2>&1; then
    TESTED_COMMIT=$(git rev-parse HEAD)
fi
if [ -n "$SHARD_SUITE_CMD" ]; then
    INTERPRETER="test-command: $SHARD_SUITE_CMD"
else
    INTERPRETER="$VENV/bin/python"
    if "$INTERPRETER" -V >/dev/null 2>&1; then
        INTERPRETER="$INTERPRETER ($("$INTERPRETER" -V 2>&1))"
    fi
fi
{
    echo "started_utc=$(utc_now)"
    echo "interpreter=$INTERPRETER"
    echo "suite=$SHARD_SUITE"
    echo "tested_commit=$TESTED_COMMIT"
    echo "shards=$SHARDS"
    echo "launcher_pid=$$"
} > "$ATTEMPT_DIR/attempt.meta"

INDEX=0
while [ "$INDEX" -lt "$SHARDS" ]; do
    mkdir -p "$ATTEMPT_DIR/shard-$INDEX.state"
    touch "$ATTEMPT_DIR/shard-$INDEX.log"
    setsid sh "$SCRIPT_PATH" __supervise "$ATTEMPT_DIR" "$INDEX" "$SHARDS" \
        >> "$ATTEMPT_DIR/supervisor-$INDEX.log" 2>&1 < /dev/null &
    echo "shard $INDEX of $SHARDS -> $ATTEMPT_DIR/shard-$INDEX.log"
    INDEX=$((INDEX + 1))
done

echo "attempt: $ATTEMPT_ID"
echo "attempt-dir: $ATTEMPT_DIR"
echo "follow with:  tail -f $ATTEMPT_DIR/shard-*.log"
echo "or:           sh tools/run_shards_detached.sh --status $ATTEMPT_ID"
