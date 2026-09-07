#!/bin/sh
# Acceptance tests for the fail-closed battery.
#
# Each case builds a throwaway copy of this tree, applies one mutation,
# runs the battery (or the batch tool directly), and asserts the exit
# code and, where named, the failure locus. Disposable copies only;
# this tree is never mutated. Exit 0 only when every case passes.
#
# The work directory is unique per invocation (mktemp), so concurrent
# selftests on one host cannot delete each other's state; case 12
# exercises exactly that. Case 12 runs child selftests, which set
# F_TOOLS_SELFTEST_CHILD and run cases 1-11 only (a child running
# case 12 again would recurse forever).

set -u
TREE=$(cd "$(dirname "$0")/.." && pwd) || exit 2
WORK=$(mktemp -d "${TMPDIR:-/tmp}/f-battery-selftest.XXXXXXXX") || {
    echo "selftest: cannot create work directory" >&2
    exit 2
}
TOTAL=12
if [ -n "${F_TOOLS_SELFTEST_CHILD:-}" ]; then
    TOTAL=11
fi
TOTAL_FAIL=0

# --- case 1: the unchanged tree passes ------------------------------
C1="$WORK/case1"
mkdir -p "$C1"
tar -C "$TREE" -cf - --exclude=.git --exclude=__pycache__ --exclude='snapshots/research_snapshot.json' --exclude='snapshots/talk_state.*' --exclude='snapshots/talk_lessons.log' . | tar -xf - -C "$C1"
sh "$C1/tools/f-tools-battery.sh" > "$WORK/case1.out" 2>&1
c1=$?
if [ "$c1" = "0" ] && grep -q "BATTERY PASSED" "$WORK/case1.out"; then
    echo "case 1 unchanged tree passes: PASS"
else
    echo "case 1 unchanged tree passes: FAIL (exit $c1)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 2: one altered F2 count is rejected -----------------------
C2="$WORK/case2"
mkdir -p "$C2"
tar -C "$TREE" -cf - --exclude=.git --exclude=__pycache__ --exclude='snapshots/research_snapshot.json' --exclude='snapshots/talk_state.*' --exclude='snapshots/talk_lessons.log' . | tar -xf - -C "$C2"
sed -i '18d' "$C2/logs/fixtures/toy-live-protocol.log"
sh "$C2/tools/f-tools-battery.sh" > "$WORK/case2.out" 2>&1
c2=$?
if [ "$c2" != "0" ] && grep -q "CHECK FAILED: toy-live-protocol taught-theorem" "$WORK/case2.out"; then
    echo "case 2 altered F2 count rejected: PASS"
else
    echo "case 2 altered F2 count rejected: FAIL (exit $c2)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 3: a missing fixture is rejected --------------------------
C3="$WORK/case3"
mkdir -p "$C3"
tar -C "$TREE" -cf - --exclude=.git --exclude=__pycache__ --exclude='snapshots/research_snapshot.json' --exclude='snapshots/talk_state.*' --exclude='snapshots/talk_lessons.log' . | tar -xf - -C "$C3"
rm "$C3/logs/fixtures/ground-evaluation.log"
sh "$C3/tools/f-tools-battery.sh" > "$WORK/case3.out" 2>&1
c3=$?
if [ "$c3" != "0" ] && grep -q "CHECK FAILED: fixture missing" "$WORK/case3.out"; then
    echo "case 3 missing fixture rejected: PASS"
else
    echo "case 3 missing fixture rejected: FAIL (exit $c3)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 4: a missing grader is rejected ---------------------------
C4="$WORK/case4"
mkdir -p "$C4"
tar -C "$TREE" -cf - --exclude=.git --exclude=__pycache__ --exclude='snapshots/research_snapshot.json' --exclude='snapshots/talk_state.*' --exclude='snapshots/talk_lessons.log' . | tar -xf - -C "$C4"
rm "$C4/tools/f2_grader.sh"
sh "$C4/tools/f-tools-battery.sh" > "$WORK/case4.out" 2>&1
c4=$?
if [ "$c4" != "0" ] && grep -q "CHECK FAILED: grading script missing" "$WORK/case4.out"; then
    echo "case 4 missing grader rejected: PASS"
else
    echo "case 4 missing grader rejected: FAIL (exit $c4)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 5: a missing adjacent pair tool cannot fall back ----------
C5="$WORK/case5"
mkdir -p "$C5"
tar -C "$TREE" -cf - --exclude=.git --exclude=__pycache__ --exclude='snapshots/research_snapshot.json' --exclude='snapshots/talk_state.*' --exclude='snapshots/talk_lessons.log' . | tar -xf - -C "$C5"
rm "$C5/tools/f3-residual-diff.sh"
(cd "$C5" && sh tools/f3_batch_diff.sh logs/fixtures/toy-live-protocol.log logs/fixtures/ground-evaluation.log) > "$WORK/case5-batch.out" 2>&1
c5b=$?
sh "$C5/tools/f-tools-battery.sh" > "$WORK/case5.out" 2>&1
c5=$?
if [ "$c5b" = "2" ] && grep -q "tree-local pair tool missing" "$WORK/case5-batch.out" && ! grep -q " identical " "$WORK/case5-batch.out" && [ "$c5" != "0" ]; then
    echo "case 5 missing pair tool cannot fall back: PASS"
else
    echo "case 5 missing pair tool cannot fall back: FAIL (batch exit $c5b, battery exit $c5)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 6: valid F3 verdicts keep their meaning -------------------
if [ "$c1" = "0" ] && grep -q " identical " "$WORK/case1.out" && grep -q " silence-class " "$WORK/case1.out" && grep -q " distinct " "$WORK/case1.out" && grep -q "f3 check: pass" "$WORK/case1.out"; then
    echo "case 6 valid F3 verdicts keep meaning: PASS"
else
    echo "case 6 valid F3 verdicts keep meaning: FAIL"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 7: one failed component fails the battery -----------------
C7="$WORK/case7"
mkdir -p "$C7"
tar -C "$TREE" -cf - --exclude=.git --exclude=__pycache__ --exclude='snapshots/research_snapshot.json' --exclude='snapshots/talk_state.*' --exclude='snapshots/talk_lessons.log' . | tar -xf - -C "$C7"
echo "# selftest marker fermat" >> "$C7/tools/f2_grader.sh"
sh "$C7/tools/f-tools-battery.sh" > "$WORK/case7.out" 2>&1
c7=$?
if [ "$c7" != "0" ] && grep -q "CHECK FAILED: name-token hit" "$WORK/case7.out"; then
    echo "case 7 one failed component fails the battery: PASS"
else
    echo "case 7 one failed component fails the battery: FAIL (exit $c7)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 8: an unrelated cwd still uses the intended tree ----------
C8="$WORK/case8"
mkdir -p "$C8"
tar -C "$TREE" -cf - --exclude=.git --exclude=__pycache__ --exclude='snapshots/research_snapshot.json' --exclude='snapshots/talk_state.*' --exclude='snapshots/talk_lessons.log' . | tar -xf - -C "$C8"
(cd "$WORK" && sh "$C8/tools/f-tools-battery.sh") > "$WORK/case8.out" 2>&1
c8=$?
if [ "$c8" = "0" ] && cmp -s "$WORK/case8.out" "$WORK/case1.out"; then
    echo "case 8 unrelated cwd uses the intended tree: PASS"
else
    echo "case 8 unrelated cwd uses the intended tree: FAIL (exit $c8)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 9: F2 output correct but exit nonzero is a failure --------
C9="$WORK/case9"
mkdir -p "$C9"
tar -C "$TREE" -cf - --exclude=.git --exclude=__pycache__ --exclude='snapshots/research_snapshot.json' --exclude='snapshots/talk_state.*' --exclude='snapshots/talk_lessons.log' . | tar -xf - -C "$C9"
printf '\nexit 7\n' >> "$C9/tools/f2_grader.sh"
sh "$C9/tools/f-tools-battery.sh" > "$WORK/case9.out" 2>&1
c9=$?
if [ "$c9" != "0" ] && grep -q "CHECK FAILED: f2-grader execution status" "$WORK/case9.out" && grep -q "oracle (3/2/0/0/2/1): yes" "$WORK/case9.out" && ! grep -q "BATTERY PASSED" "$WORK/case9.out"; then
    echo "case 9 F2 fields correct, exit 7, rejected: PASS"
else
    echo "case 9 F2 fields correct, exit 7, rejected: FAIL (exit $c9)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 10: an F4 execution failure is a failure ------------------
C10="$WORK/case10"
mkdir -p "$C10"
tar -C "$TREE" -cf - --exclude=.git --exclude=__pycache__ --exclude='snapshots/research_snapshot.json' --exclude='snapshots/talk_state.*' --exclude='snapshots/talk_lessons.log' . | tar -xf - -C "$C10"
printf '\nexit 9\n' >> "$C10/tools/f4_auditor.sh"
sh "$C10/tools/f-tools-battery.sh" > "$WORK/case10.out" 2>&1
c10=$?
if [ "$c10" != "0" ] && grep -q "CHECK FAILED: f4-auditor execution status" "$WORK/case10.out" && grep -q "session-id:" "$WORK/case10.out" && ! grep -q "BATTERY PASSED" "$WORK/case10.out"; then
    echo "case 10 F4 execution failure rejected: PASS"
else
    echo "case 10 F4 execution failure rejected: FAIL (exit $c10)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 11: a failed metadata-companion write is a failure --------
sh "$TREE/tools/f-tools-battery.sh" "$WORK/no-such-dir/meta.txt" > "$WORK/case11.out" 2>&1
c11=$?
if [ "$c11" != "0" ] && grep -q "CHECK FAILED: metadata companion" "$WORK/case11.out" && grep -q "BATTERY FAILED" "$WORK/case11.out" && [ ! -e "$WORK/no-such-dir/meta.txt" ]; then
    echo "case 11 metadata-write failure rejected: PASS"
else
    echo "case 11 metadata-write failure rejected: FAIL (exit $c11)"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
fi

# --- case 12: concurrent selftests do not interfere -----------------
# Runs only at top level: children (F_TOOLS_SELFTEST_CHILD set) would
# otherwise recurse. Two full selftests run at once; both must pass
# every one of their cases.
if [ -z "${F_TOOLS_SELFTEST_CHILD:-}" ]; then
    SELF="$TREE/tools/f-tools-battery-selftest.sh"
    F_TOOLS_SELFTEST_CHILD=1 sh "$SELF" > "$WORK/conc-a.out" 2>&1 &
    pa=$!
    F_TOOLS_SELFTEST_CHILD=1 sh "$SELF" > "$WORK/conc-b.out" 2>&1 &
    pb=$!
    wait $pa
    sa=$?
    wait $pb
    sb=$?
    if [ "$sa" = "0" ] && [ "$sb" = "0" ] && grep -q "SELFTEST PASSED: 11 of 11 cases green" "$WORK/conc-a.out" && grep -q "SELFTEST PASSED: 11 of 11 cases green" "$WORK/conc-b.out"; then
        echo "case 12 concurrent selftests do not interfere: PASS"
    else
        echo "case 12 concurrent selftests do not interfere: FAIL (child exits $sa/$sb)"
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
    fi
fi

echo
if [ "$TOTAL_FAIL" -gt 0 ]; then
    echo "SELFTEST FAILED: $TOTAL_FAIL case(s) failed"
    echo "workdir retained for inspection: $WORK"
    exit 1
fi
echo "SELFTEST PASSED: $TOTAL of $TOTAL cases green"
rm -rf "$WORK"
exit 0
