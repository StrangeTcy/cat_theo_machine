#!/bin/sh
# Run the default-suite shards detached, with output on disk.
#
# A sandbox reset kills running processes, and a killed shard run leaves
# nothing behind: `shard_suite.py` prints its tally only at the end, so an
# hour of compute interrupted is an hour of compute with no record of how
# far it got. Launching detached with the log in `logs/` means a reset
# costs the run, not the evidence.
#
# It does not make a run survive a sandbox restart -- nothing does -- and
# it is not a substitute for `tools/recover.sh`, which protects the tree
# rather than the measurement.
#
#   sh tools/run_shards_detached.sh           launch every shard
#   sh tools/run_shards_detached.sh --status  how far each log has got

set -e

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
VENV="${VENV:-$HOME/.venv}"
SHARDS="${SHARDS:-2}"

cd "$REPO_ROOT"

if [ "$1" = "--status" ]; then
    found=""
    for log in logs/shard-*.log; do
        [ -f "$log" ] || continue
        found="yes"
        if grep -q "^passed:" "$log" 2>/dev/null; then
            echo "$log: DONE  $(grep '^passed:' "$log")"
        elif pgrep -f "shard_suite.py ${log#logs/shard-}.log" >/dev/null 2>&1; then
            echo "$log: running"
        else
            echo "$log: $(wc -l < "$log") lines, no tally -- died or still starting"
        fi
    done
    [ -n "$found" ] || echo "no shard logs yet"
    exit 0
fi

if [ ! -x "$VENV/bin/python" ]; then
    echo "no venv at $VENV -- run 'sh tools/recover.sh' first" >&2
    exit 1
fi

mkdir -p logs

INDEX=0
while [ "$INDEX" -lt "$SHARDS" ]; do
    LOG="logs/shard-$INDEX.log"
    if [ -f "$LOG" ]; then
        mv "$LOG" "$LOG.prev"
    fi
    PYTHONPATH=/home/user setsid nohup "$VENV/bin/python" -u \
        tools/shard_suite.py "$INDEX" "$SHARDS" > "$LOG" 2>&1 &
    echo "shard $INDEX of $SHARDS -> $LOG (pid $!)"
    INDEX=$((INDEX + 1))
done

echo "follow with:  tail -f logs/shard-*.log"
echo "or:          sh tools/run_shards_detached.sh --status"
