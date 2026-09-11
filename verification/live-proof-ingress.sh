#!/usr/bin/env bash
# Sandbox counterpart of the Anaconda fixture. No interpreter discovery.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
package=$(basename "$root")
PYTHON=${PYTHON:-python3}
state=$(mktemp -d "${TMPDIR:-/tmp}/hyge-live-ingress.XXXXXXXX")
export HYGE_SNAPSHOT_DIR="$state"
export HYGE_SEARCH_WORKER_TIMEOUT=5
export PYTHONDONTWRITEBYTECODE=1
artifacts="$root/verification"
transcript="$artifacts/live-proof-ingress-live-transcript.txt"
tests="$artifacts/live-proof-ingress-tests.txt"
after="$artifacts/live-proof-ingress-after.txt"
cd "$root"
commit=$(git rev-parse HEAD)
printf 'Candidate: %s\nExecution: sandbox Bash, explicitly authorized by user\nState: %s\n' "$commit" "$state" > "$tests"
"$PYTHON" -V >> "$tests" 2>&1
find "$root/snapshots" -type f -print0 | sort -z | xargs -0 sha256sum > "$state/shared-before.sha256"
(cd "$root/.."; "$PYTHON" -u -m "$package.ingress_tests") >> "$tests" 2>&1
"$PYTHON" -u "$root/main.py" live --workers 1 < "$artifacts/live-proof-ingress.inputs.txt" > "$transcript" 2>&1
printf 'LIVE_EXIT_CODE=0\n' >> "$tests"
test "$(grep -c 'submitting parsed goal to foreground prover' "$transcript")" -eq 3
test "$(grep -c 'foreground coordinator goal preserved' "$transcript")" -eq 3
test "$(grep -c 'semantic-clarification at input span' "$transcript")" -eq 1
test "$(grep -c 'parse-failure at input span' "$transcript")" -eq 1
grep -F 'forall(n, implies(lt(2, bound-variable(n)), nosolutions(positive-integers, unknowns(a, b, c)' "$transcript" > /dev/null
grep -F 'forall(k, implies(lt(3, bound-variable(k)), nosolutions(positive-integers, unknowns(x, y, z)' "$transcript" > /dev/null
grep -F 'forall(t, implies(lt(0, bound-variable(t)), eq(add(bound-variable(t), 0), bound-variable(t))))' "$transcript" > /dev/null
grep -F 'there is nothing to explain' "$transcript" > /dev/null
grep -F 'hyge> four' "$transcript" > /dev/null
grep -F "daemon: cycling shared state at $state/talk_state.wire with 1 worker(s)" "$transcript" > /dev/null
grep -F 'live mode: daemon stopped.' "$transcript" > /dev/null
if grep -E 'Traceback|expected-left-parenthesis|Use Predicate\(constant\)' "$transcript"; then exit 1; fi
awk '
/semantic-clarification/ { phase="clarification" }
/parsed goal:/ { phase="parsed" }
/parse-failure/ { phase="failed" }
/submitting parsed goal/ { if (phase != "parsed") exit 1; count++ }
END { if (count != 3) exit 1 }
' "$transcript"
(cd "$root/.."; "$PYTHON" -u -m "$package.ingress_receipts" "$artifacts/live-proof-ingress.inputs.txt") >> "$tests" 2>&1
test ! -e "$state/talk_daemon.live"
mkdir "$state/ownership"
printf 'unrelated-owner\n' > "$state/ownership/talk_daemon.live"
if HYGE_SNAPSHOT_DIR="$state/ownership" "$PYTHON" "$root/main.py" live --workers 1 < /dev/null > "$state/ownership-refusal.txt" 2>&1; then exit 1; fi
grep -F 'Live state already has a daemon marker' "$state/ownership-refusal.txt" > /dev/null
test "$(cat "$state/ownership/talk_daemon.live")" = unrelated-owner
find "$root/snapshots" -type f -print0 | sort -z | xargs -0 sha256sum > "$state/shared-after.sha256"
cmp "$state/shared-before.sha256" "$state/shared-after.sha256"
if test -n "${HYGE_PARENT_FORMAL:-}"; then
    grep -x 'four' "$HYGE_PARENT_FORMAL" > /dev/null
    printf 'PASS: parent formal query returns four; live formal query returns four\n' >> "$tests"
else
    printf 'Parent formal comparison not supplied; cannot close acceptance\n' >> "$tests"
    exit 1
fi
printf 'PASS: 8/8 live acceptance groups\nForeground requests: 3/3\nNatural clarification submissions: 0\nMalformed submissions: 0\nComparison-worker receipts: 15/15\nShared state hashes unchanged\nForeign daemon marker preserved\nEXIT_CODE=0\n' >> "$tests"
printf 'Candidate: %s\nScope: new ingress on 41e8078; original transcript not reproduced\nEnvironment: sandbox Bash (authorized), not Anaconda\nAcceptance groups: 8/8\nForeground submissions: 3 expected, 3 observed\nComparison-worker receipts: 15 expected, 15 structurally equal\nNatural clarification submissions: 0\nMalformed submissions: 0\nFormal regression: parent and candidate return four\nDaemon routing, isolated state, ownership: pass\nSearch results: stalls; no theorem asserted\nEXIT_CODE=0\nRaw transcript: verification/live-proof-ingress-live-transcript.txt\nState and worker receipt evidence: %s\n' "$commit" "$state" > "$after"
cat "$after"
