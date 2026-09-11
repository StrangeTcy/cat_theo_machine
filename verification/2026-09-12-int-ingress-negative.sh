#!/usr/bin/env bash
# INT negative tests for live proof ingress + worker transport.
# Sandbox counterpart style: no interpreter discovery, isolated state only.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
package=$(basename "$root")
PYTHON=${PYTHON:-python3}
logdir=$(mktemp -d "${TMPDIR:-/tmp}/hyge-int-negative.XXXXXXXX")
echo "negative-test logs: $logdir"

# N3: failed parse clears pending foreground goal.
n3state=$(mktemp -d "${TMPDIR:-/tmp}/hyge-int-n3.XXXXXXXX")
export HYGE_SNAPSHOT_DIR="$n3state"
export HYGE_SEARCH_WORKER_TIMEOUT=5
export PYTHONDONTWRITEBYTECODE=1
printf '%s\n' \
  'prove that for all n > 2 a^n + b^n = c^n has no solutions in positive integers' \
  'prove that for all > 2 a^n + b^n = c^n has no solutions in positive integers' \
  'why' \
  'goodbye' > "$logdir/n3-inputs.txt"
(cd "$root/.."; HYGE_SNAPSHOT_DIR="$n3state" HYGE_SEARCH_WORKER_TIMEOUT=5 "$PYTHON" -u -m "$package.main" live --workers 1 < "$logdir/n3-inputs.txt" > "$logdir/n3-transcript.txt" 2>&1)
test "$(grep -c 'submitting parsed goal to foreground prover' "$logdir/n3-transcript.txt")" -eq 1
test "$(grep -c 'parse-failure at input span' "$logdir/n3-transcript.txt")" -eq 1
grep -F 'there is nothing to explain' "$logdir/n3-transcript.txt" > /dev/null
echo 'PASS N3: malformed input submits nothing and clears the pending goal'

# N4: worker with no request refuses a substitute theorem.
n4state=$(mktemp -d "${TMPDIR:-/tmp}/hyge-int-n4.XXXXXXXX")
if (cd "$root/.."; HYGE_SNAPSHOT_DIR="$n4state" "$PYTHON" -u -m "$package.main" search-worker dfs "$n4state/dfs.snapshot.json" 5 > "$logdir/n4.log" 2>&1); then
  echo 'FAIL N4: worker without a request exited zero' >&2
  exit 1
fi
grep -F 'search-worker request missing; refusing a substitute theorem' "$logdir/n4.log" > /dev/null
echo 'PASS N4: missing worker request refuses the bundled-example fallback'

# N5: worker with an unmatched legacy manifest refuses a substitute goal.
n5state=$(mktemp -d "${TMPDIR:-/tmp}/hyge-int-n5.XXXXXXXX")
printf '{"start_text": "no-such-start", "goal_text": "no-such-goal"}' > "$n5state/dfs.snapshot.json.manifest.json"
if (cd "$root/.."; HYGE_SNAPSHOT_DIR="$n5state" "$PYTHON" -u -m "$package.main" search-worker dfs "$n5state/dfs.snapshot.json" 5 > "$logdir/n5.log" 2>&1); then
  echo 'FAIL N5: worker with unmatched legacy manifest exited zero' >&2
  exit 1
fi
grep -F 'refusing a substitute goal' "$logdir/n5.log" > /dev/null
echo 'PASS N5: unmatched legacy request refuses a substitute goal'

# N5b: tampered worker receipt is rejected, never silently accepted.
n5bstate=$(mktemp -d "${TMPDIR:-/tmp}/hyge-int-n5b.XXXXXXXX")
cp -r /tmp/int-manual/search_compare "$n5bstate/search_compare"
tamper_target=$(find "$n5bstate/search_compare" -name '*.received.wire' | head -n 1)
printf 'X' | dd of="$tamper_target" bs=1 count=1 conv=notrunc status=none
if (cd "$root/.."; HYGE_SNAPSHOT_DIR="$n5bstate" "$PYTHON" -u -m "$package.ingress_receipts" "$root/verification/live-proof-ingress-manual-inputs.txt" > "$logdir/n5b.log" 2>&1); then
  echo 'FAIL N5b: tampered receipt accepted' >&2
  exit 1
fi
echo 'PASS N5b: tampered worker receipt fails closed'

# N7: comparison result root honors the isolated-state setting.
iso_probe=$(HYGE_SNAPSHOT_DIR=/tmp/iso-probe "$PYTHON" -c "import sys; sys.path.insert(0, '/home/user'); from cat_theo_machine.search import compare_subprocess as C; print(C._ComparisonSubprocessMixin._search_compare_result_root(None, '/pkg'))")
test "$iso_probe" = '/tmp/iso-probe/search_compare'
default_probe=$(env -u HYGE_SNAPSHOT_DIR "$PYTHON" -c "import sys; sys.path.insert(0, '/home/user'); from cat_theo_machine.search import compare_subprocess as C; print(C._ComparisonSubprocessMixin._search_compare_result_root(None, '/pkg'))")
test "$default_probe" = '/pkg/snapshots/search_compare'
echo 'PASS N7: result directory stays under the isolated-state root'

echo "NEGATIVE_EXIT_CODE=0"
echo "logs retained at: $logdir"
