#!/bin/sh
# Run every t*.sh test under this directory, in sorted order.
# Raw stdout is the test record; the prologue identifies the tested code.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
RUNNER="$HERE/../../run_shards_detached.sh"

echo "shard-runner tests"
echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
if git -C "$HERE/../../.." rev-parse HEAD >/dev/null 2>&1; then
    echo "repo_head: $(git -C "$HERE/../../.." rev-parse HEAD)"
else
    echo "repo_head: unknown (git unavailable)"
fi
echo "runner_sha256: $(sha256sum "$RUNNER" | awk '{print $1}')"
echo "runner_path: tools/run_shards_detached.sh"
echo ""

PASS=0
FAIL=0
for T in "$HERE"/t*.sh; do
    NAME=$(basename "$T")
    echo "--- $NAME ---"
    if sh "$T"; then
        PASS=$((PASS + 1))
    else
        echo "FAIL: $NAME"
        FAIL=$((FAIL + 1))
    fi
    echo ""
done

echo "runner tests passed: $PASS failed: $FAIL"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
