#!/usr/bin/env bash
# tools/suite_attempt.sh — record one shard-suite attempt as durable evidence.
#
# INT-SUPPORT host tooling. Wraps a shard command without changing its
# execution semantics: stdout+stderr are preserved in full, the child's exit
# status is recorded, and the completion record is published atomically only
# after the child exits and output capture finishes.
#
# Usage:
#   tools/suite_attempt.sh [--tested-commit <sha>] [--run-id <id>] [--shard <n>]
#                          [--count <k>] [--attempts-dir <dir>] -- <child command...>
#
# If --shard/--count are omitted they are inferred from a trailing "<n> <k>"
# integer pair on the child command (the tools/shard_suite.py convention).
#
# Layout produced (never overwritten; a restart gets a new run id):
#   <attempts-dir>/<run-id>/shard-<n>/meta.env          pre-launch metadata
#   <attempts-dir>/<run-id>/shard-<n>/raw.log           full stdout+stderr
#   <attempts-dir>/<run-id>/shard-<n>/completion.json   child exit (atomic rename)
#   <attempts-dir>/<run-id>/shard-<n>/completion.json.sha  raw-log sha256
#
# The wrapper exits with the child's exit status. If the wrapper is killed
# mid-run, raw.log survives with no completion record: interrupted-run
# evidence, which collectors must refuse.
set -u

die() { echo "suite_attempt: $*" >&2; exit 2; }

TESTED_COMMIT=""
RUN_ID=""
SHARD=""
COUNT=""
ATTEMPTS_DIR="${SUITE_ATTEMPTS_DIR:-logs/suite-attempts}"
CMD=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --tested-commit) TESTED_COMMIT="${2:-}"; shift 2 ;;
    --run-id)        RUN_ID="${2:-}"; shift 2 ;;
    --shard)         SHARD="${2:-}"; shift 2 ;;
    --count)         COUNT="${2:-}"; shift 2 ;;
    --attempts-dir)  ATTEMPTS_DIR="${2:-}"; shift 2 ;;
    --)              shift; CMD=("$@"); break ;;
    *)               CMD+=("$1"); shift ;;
  esac
done

[ "${#CMD[@]}" -gt 0 ] || die "no child command given"

# infer shard index/count from a trailing "N K" integer pair (shard_suite style)
if [ -z "$SHARD" ] || [ -z "$COUNT" ]; then
  nargs="${#CMD[@]}"
  if [ "$nargs" -ge 2 ]; then
    la="${CMD[$((nargs-1))]}"; lb="${CMD[$((nargs-2))]}"
    case "$la" in ''|*[!0-9]*) la="" ;; esac
    case "$lb" in ''|*[!0-9]*) lb="" ;; esac
    if [ -n "$la" ] && [ -n "$lb" ]; then
      [ -n "$SHARD" ] || SHARD="$lb"
      [ -n "$COUNT" ] || COUNT="$la"
    fi
  fi
fi
[ -n "$SHARD" ] || die "shard index unknown (pass --shard)"
[ -n "$COUNT" ] || die "shard count unknown (pass --count)"
case "$SHARD$COUNT" in *[!0-9]*) die "shard/count must be integers" ;; esac

if [ ! -d "$ATTEMPTS_DIR" ]; then
  mkdir -p "$ATTEMPTS_DIR" || die "cannot create $ATTEMPTS_DIR"
fi

if [ -z "$RUN_ID" ]; then
  while :; do
    RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$-${RANDOM}"
    [ ! -e "$ATTEMPTS_DIR/$RUN_ID" ] && break
  done
fi
DIR="$ATTEMPTS_DIR/$RUN_ID/shard-$SHARD"
if [ -e "$DIR" ]; then
  die "attempt dir exists: $DIR — restarts get a new run id; never overwrite an earlier attempt"
fi
mkdir -p "$DIR" || die "cannot create $DIR"

# ---- record BEFORE launch ----
[ -n "$TESTED_COMMIT" ] || TESTED_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
TESTED_TREE="unknown"
if [ "$TESTED_COMMIT" != "unknown" ]; then
  TESTED_TREE="$(git rev-parse "${TESTED_COMMIT}^{tree}" 2>/dev/null || echo unknown)"
fi
WORKTREE_DIRTY="unknown"
if git rev-parse --git-dir >/dev/null 2>&1; then
  if [ -n "$(git status --porcelain 2>/dev/null | head -1)" ]; then
    WORKTREE_DIRTY="yes"
  else
    WORKTREE_DIRTY="no"
  fi
fi
PYEXEC="$(command -v python3)"
PYVERS="$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo unknown)"
UTC0="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

{
  echo "RUN_ID=$RUN_ID"
  echo "STARTED_UTC=$UTC0"
  echo "TESTED_COMMIT=$TESTED_COMMIT"
  echo "TESTED_TREE=$TESTED_TREE"
  echo "WORKTREE_DIRTY=$WORKTREE_DIRTY"
  echo "SHARD_INDEX=$SHARD"
  echo "SHARD_COUNT=$COUNT"
  echo "COMMAND=${CMD[*]}"
  echo "CWD=$(pwd)"
  echo "PYEXEC=$PYEXEC"
  echo "PYVERS=$PYVERS"
  echo "PYTHONPATH=${PYTHONPATH:-}"
} > "$DIR/meta.env"

# serialize the child command for the runner
SUITE_ATTEMPT_CMD="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${CMD[@]}")"
export SUITE_ATTEMPT_CMD

# ---- run child: full stdout+stderr preserved, completion published atomically ----
python3 - "$DIR" <<'PYEOF'
import hashlib, json, os, subprocess, sys, time
from datetime import datetime, timezone

d = sys.argv[1]
cmd = json.loads(os.environ["SUITE_ATTEMPT_CMD"])
t0 = time.time()
with open(os.path.join(d, "raw.log"), "wb") as raw:
    proc = subprocess.Popen(cmd, stdout=raw, stderr=subprocess.STDOUT)
    status = proc.wait()
dur = round(time.time() - t0, 3)
finished = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

part = os.path.join(d, "completion.json.part")
comp = os.path.join(d, "completion.json")
with open(part, "w") as f:
    f.write(json.dumps({
        "child_exit_status": status,
        "duration_seconds": dur,
        "finished_utc": finished,
        "wrapper": "suite_attempt.sh",
    }, sort_keys=True) + "\n")

sha_part = os.path.join(d, "completion.json.sha.part")
with open(os.path.join(d, "raw.log"), "rb") as f:
    digest = hashlib.sha256(f.read()).hexdigest()
with open(sha_part, "w") as f:
    f.write("%s raw.log\n" % digest)

os.replace(sha_part, os.path.join(d, "completion.json.sha"))  # capture finished
os.replace(part, comp)                                          # publish completion
sys.exit(status)
PYEOF
rc=$?
echo "suite_attempt: run $RUN_ID shard $SHARD exit=$rc dir=$DIR" >&2
exit $rc
