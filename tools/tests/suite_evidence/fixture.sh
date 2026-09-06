#!/usr/bin/env bash
# Shared helpers for the suite-evidence acceptance tests (host-tooling tests).
# Fixtures are SYNTHETIC and labeled so they can never file as machine-suite
# results. Sourced by the case scripts; do not execute directly.
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COLLECT="$REPO_ROOT/tools/suite_collect.sh"
ATTEMPT="$REPO_ROOT/tools/suite_attempt.sh"

wmeta() { # dir run commit tree idx count
  printf 'RUN_ID=%s\nSTARTED_UTC=2026-01-01T00:00:00Z\nTESTED_COMMIT=%s\nTESTED_TREE=%s\nWORKTREE_DIRTY=no\nSHARD_INDEX=%s\nSHARD_COUNT=%s\nCOMMAND=synthetic\ncwd=/tmp\nPYEXEC=/usr/bin/python3\nPYVERS=3.11.0\nPYTHONPATH=\nSYNTHETIC=yes\n' "$2" "$3" "$4" "$5" "$6" > "$1/meta.env"
}

# raw log: pack noise, the runner's final marker, then the report block.
# Format inspected from tools/shard_suite.py + graph.py TestResultsReport:
#   "SHARD <idx> elapsed <float>"   then   "All the tests have passed."  or failure names
mklog() { # dir idx  (report lines on stdin)
  local d="$1" i="$2"
  { echo "Reading pack order-sign..."; echo "SHARD $i elapsed 1.25"; cat; } > "$d/raw.log"
}

finish() { # dir [exit]
  local d="$1" ex="${2:-0}"
  printf '{"child_exit_status": %s, "duration_seconds": 1.0, "finished_utc": "2026-01-01T00:00:02Z", "wrapper": "fixture"}\n' "$ex" > "$d/completion.json"
  ( cd "$d" && sha256sum raw.log | awk '{print $1" raw.log"}' > completion.json.sha )
}

expect_collect_ok() {  # evidence-file dirs...
  local out="$1"; shift
  bash "$COLLECT" --out "$out" "$@" > "$out.stdout" 2> "$out.stderr"; rc=$?
  [ "$rc" -eq 0 ] || fail "collector exited $rc: $(cat "$out.stderr")"
  grep -q "SUITE EVIDENCE REPORT" "$out" || fail "no evidence header"
  grep -q "SYNTHETIC" "$out" || fail "synthetic labeling missing"
}

expect_collect_refuse() { # error-code dirs...
  local code="$1"; shift
  local errf; errf="$(mktemp)"
  bash "$COLLECT" "$@" > /dev/null 2> "$errf"; rc=$?
  [ "$rc" -ne 0 ] || fail "collector exited 0, expected refusal $code"
  grep -qE "$code" "$errf" || fail "expected $code, got: $(cat "$errf")"
  rm -f "$errf"
}

fail() { echo "FAIL: $*"; exit 1; }
ok()   { echo "PASS: ${1:-}"; }
