#!/bin/sh
# F-tools acceptance battery runner -- fail-closed.
#
# Relocates to its own tree before running, so the caller's working
# directory is irrelevant. Usage, from anywhere:
#   tools/f-tools-battery.sh [metadata-file] > <deterministic-artifact>
#
# The deterministic core on stdout carries no timestamps, no absolute
# paths, no host state: byte-identical across reruns of one tree. Run
# metadata (UTC, commit, tree state, invocation, resolved tree, and
# the sha256 of every graded input) is written to the companion file
# named by the first argument, when given, and never mixes into the
# deterministic core. A relative companion path resolves against the
# caller's directory, not the tree. A companion that cannot be
# written completely fails the run.
#
# Exit 0 only when every enforced check is green:
#   - the five grading scripts exist and are executable
#   - the four fixtures exist and are readable
#   - the F2 grader exits 0 for every fixture: correct-looking output
#     with a nonzero exit is a failure, not a pass
#   - every required F2 field equals the recorded oracle
#   - the name-token grep is zero across the grading scripts
#   - the F3 batch completes with zero incomparable pairs
#   - the F4 auditor exits 0 for every fixture: its findings remain
#     informational, an execution error does not
#   - a requested metadata companion is written completely
# F3 pair verdicts identical / silence-class / distinct are outcomes
# of the measurement, not failures. Any CHECK FAILED line forces a
# nonzero exit.

set -u

RUNDIR=$(pwd)
TREE=$(cd "$(dirname "$0")/.." && pwd) || exit 2
cd "$TREE" || exit 2

FAILURES=0
METADATA=${1:-}
if [ "$METADATA" != "" ]; then
    case "$METADATA" in
        /*) ;;
        *) METADATA="$RUNDIR/$METADATA" ;;
    esac
    {
        echo "battery run metadata"
        echo "utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "commit: $(git rev-parse HEAD 2>/dev/null || echo unknown)"
        if git rev-parse --git-dir > /dev/null 2>&1; then
            if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
                echo "tree-state: clean"
            else
                echo "tree-state: dirty"
            fi
        else
            echo "tree-state: no-git"
        fi
        echo "invoked-as: $0"
        echo "invoked-from: $RUNDIR"
        echo "resolved-tree: $TREE"
        echo "input-sha256:"
        for f in tools/f-tools-battery.sh tools/f-tools-battery-selftest.sh \
                 tools/f2_grader.sh tools/f3-residual-diff.sh \
                 tools/f3_batch_diff.sh tools/f4_auditor.sh \
                 tools/f2-outcome-class.sh \
                 logs/fixtures/toy-live-protocol.log \
                 logs/fixtures/ground-evaluation.log \
                 logs/fixtures/blind-geometry-dependencies.log \
                 logs/fixtures/incident-misattributed-teaching.log; do
            if command -v sha256sum > /dev/null 2>&1; then
                sha256sum "$f" | sed 's/^/  /'
            else
                echo "  (sha256sum unavailable) $f"
            fi
        done
    } > "$METADATA" 2>/dev/null
    meta_status=$?
    if [ "$meta_status" -ne 0 ] || ! tail -n 1 "$METADATA" 2>/dev/null | grep -q "incident-misattributed-teaching.log$"; then
        echo "CHECK FAILED: metadata companion write ($METADATA)"
        FAILURES=$((FAILURES + 1))
    fi
fi

FIXTURES="toy-live-protocol ground-evaluation blind-geometry-dependencies incident-misattributed-teaching"
SCRIPTS="tools/f2_grader.sh tools/f3-residual-diff.sh tools/f3_batch_diff.sh tools/f4_auditor.sh tools/f2-outcome-class.sh"
FIXTURE_PATHS=""
for name in $FIXTURES; do
    FIXTURE_PATHS="$FIXTURE_PATHS logs/fixtures/$name.log"
done
TRANSCRIPTS=$(ls logs/2*-F-RUNNER-decoy.log logs/2*-F-RUNNER-target.log 2>/dev/null | sort)

echo "F-tools acceptance battery (fail-closed)"
echo "runner: tools/f-tools-battery.sh (this tree)"
echo "grader: tools/f2_grader.sh; oracle: tools/f2-grading-fixtures.spec.md (T4 as amended)"
echo

echo "== availability =="
for s in $SCRIPTS; do
    if [ ! -x "$s" ]; then
        echo "CHECK FAILED: grading script missing or not executable: $s"
        FAILURES=$((FAILURES + 1))
    else
        echo "ok: $s"
    fi
done
for name in $FIXTURES; do
    if [ ! -r "logs/fixtures/$name.log" ]; then
        echo "CHECK FAILED: fixture missing or unreadable: logs/fixtures/$name.log"
        FAILURES=$((FAILURES + 1))
    else
        echo "ok: logs/fixtures/$name.log"
    fi
done
if [ "$TRANSCRIPTS" = "" ]; then
    echo "note: no F-RUNNER transcripts in this tree; the matrix runs on fixtures alone"
fi
echo

echo "== name-token grep over the grading scripts (five tokens, case-insensitive) =="
pattern='fe''rmat|fl''t|noso''lutions|wil''es|fr''ey'
for s in $SCRIPTS; do
    if [ -r "$s" ]; then
        n=$(grep -c -i -E "$pattern" "$s")
        if [ "$n" = "0" ]; then
            echo "ok: $s (zero hits)"
        else
            echo "CHECK FAILED: name-token hit in $s ($n)"
            FAILURES=$((FAILURES + 1))
        fi
    fi
done
echo

echo "== F2: script versus recorded oracle, four fixtures =="
echo "oracle fields: taught / unlock / circular / computable / cited / uncited"
echo
while IFS='|' read -r name e_taught e_unlock e_circular e_computable e_cited e_uncited; do
    if [ -z "$name" ]; then
        continue
    fi
    out=$(tools/f2_grader.sh "logs/fixtures/$name.log" 2>&1)
    g_status=$?
    echo "-- $name.log"
    printf '%s\n' "$out"
    if [ "$g_status" -ne 0 ]; then
        echo "CHECK FAILED: f2-grader execution status ($name): expected 0, got $g_status"
        FAILURES=$((FAILURES + 1))
    fi
    g_taught=$(printf '%s\n' "$out" | sed -n 's/^taught-theorem count: *\([0-9][0-9]*\)$/\1/p')
    g_unlock=$(printf '%s\n' "$out" | sed -n 's/^unlock-evidence count: *\([0-9][0-9]*\)$/\1/p')
    g_circular=$(printf '%s\n' "$out" | sed -n 's/^circular-request count: *\([0-9][0-9]*\)$/\1/p')
    g_computable=$(printf '%s\n' "$out" | sed -n 's/^computable-request count: *\([0-9][0-9]*\)$/\1/p')
    g_cited=$(printf '%s\n' "$out" | sed -n 's/^cite-coverage cited: *\([0-9][0-9]*\)$/\1/p')
    g_uncited=$(printf '%s\n' "$out" | sed -n 's/^cite-coverage uncited: *\([0-9][0-9]*\)$/\1/p')
    match=yes
    if [ "$g_taught" != "$e_taught" ]; then
        echo "CHECK FAILED: $name taught-theorem: expected $e_taught, got ${g_taught:-none}"
        match=no
        FAILURES=$((FAILURES + 1))
    fi
    if [ "$g_unlock" != "$e_unlock" ]; then
        echo "CHECK FAILED: $name unlock-evidence: expected $e_unlock, got ${g_unlock:-none}"
        match=no
        FAILURES=$((FAILURES + 1))
    fi
    if [ "$g_circular" != "$e_circular" ]; then
        echo "CHECK FAILED: $name circular-request: expected $e_circular, got ${g_circular:-none}"
        match=no
        FAILURES=$((FAILURES + 1))
    fi
    if [ "$g_computable" != "$e_computable" ]; then
        echo "CHECK FAILED: $name computable-request: expected $e_computable, got ${g_computable:-none}"
        match=no
        FAILURES=$((FAILURES + 1))
    fi
    if [ "$g_cited" != "$e_cited" ]; then
        echo "CHECK FAILED: $name cite-coverage cited: expected $e_cited, got ${g_cited:-none}"
        match=no
        FAILURES=$((FAILURES + 1))
    fi
    if [ "$g_uncited" != "$e_uncited" ]; then
        echo "CHECK FAILED: $name cite-coverage uncited: expected $e_uncited, got ${g_uncited:-none}"
        match=no
        FAILURES=$((FAILURES + 1))
    fi
    echo "oracle ($e_taught/$e_unlock/$e_circular/$e_computable/$e_cited/$e_uncited): $match"
done <<'EOF'
toy-live-protocol|3|2|0|0|2|1
ground-evaluation|2|0|0|0|0|2
blind-geometry-dependencies|1|0|0|0|1|0
incident-misattributed-teaching|1|1|0|0|0|1
EOF
echo

echo "== F3 batch identity matrix: four fixtures plus the F-RUNNER transcripts of this branch =="
batch_out=$(tools/f3_batch_diff.sh $FIXTURE_PATHS $TRANSCRIPTS 2>&1)
batch_code=$?
printf '%s\n' "$batch_out"
echo "batch exit=$batch_code"
if [ "$batch_code" -eq 0 ]; then
    echo "f3 check: pass (every pair comparable; verdicts are measurement outcomes)"
elif [ "$batch_code" -eq 2 ]; then
    echo "CHECK FAILED: f3 batch reported an incomparable pair or a missing tool"
    FAILURES=$((FAILURES + 1))
else
    echo "CHECK FAILED: f3 batch exited $batch_code (tool error)"
    FAILURES=$((FAILURES + 1))
fi
echo

echo "== F4 auditor sheets, four fixtures (informational; no numeric oracle) =="
for name in $FIXTURES; do
    a_out=$(tools/f4_auditor.sh "logs/fixtures/$name.log" 2>&1)
    a_status=$?
    printf '%s\n' "$a_out"
    if [ "$a_status" -ne 0 ]; then
        echo "CHECK FAILED: f4-auditor execution status ($name): expected 0, got $a_status"
        FAILURES=$((FAILURES + 1))
    fi
    echo "--"
done
echo

if [ "$FAILURES" -gt 0 ]; then
    echo "BATTERY FAILED: $FAILURES check(s) failed"
    exit 1
fi
echo "BATTERY PASSED: all enforced checks green"
exit 0
