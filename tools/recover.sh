#!/bin/sh
# Recover a sandbox after a reset.
#
# A reset keeps working files and drops git objects, so a session can wake
# up with a full tree and a HEAD that no longer descends from the
# integration tip. Committing in that state produces an enormous diff
# against the wrong base -- 190 files and 359k lines, once -- and the only
# thing that catches it is a rejected push.
#
# This script makes the check and the recovery one command. It is
# host-side tooling and touches no machine code.
#
#   sh tools/recover.sh              check and repair
#   sh tools/recover.sh --check      report only, change nothing
#
# What it does:
#   1. fetch the integration branch
#   2. if HEAD does not descend from it, save the work tree diff against
#      the current HEAD, reset --hard to the integration tip, re-apply
#   3. rebuild the throwaway venv the probes need (gmpy2, pyyaml)
#   4. re-run the label pins, which need no boot and prove the tree

set -e

BRANCH="${INTEGRATION_BRANCH:-arena/01a06542-cat-theo-machine}"
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
VENV="${VENV:-$HOME/.venv}"
CHECK_ONLY=""

if [ "$1" = "--check" ]; then
    CHECK_ONLY="yes"
fi

cd "$REPO_ROOT"

echo "integration branch: $BRANCH"
echo "local HEAD:         $(git rev-parse HEAD)"

git fetch origin "$BRANCH" 2>/dev/null
TIP=$(git rev-parse FETCH_HEAD)

echo "integration tip:    $TIP"

if git merge-base --is-ancestor "$TIP" HEAD; then
    echo "OK: HEAD descends from the integration tip"
else
    echo "BROKEN: HEAD does not descend from the integration tip"
    if [ -n "$CHECK_ONLY" ]; then
        echo "--check given, changing nothing"
        exit 1
    fi
    PATCH=$(mktemp /tmp/recover.XXXXXX.patch)
    git diff "$TIP" HEAD > "$PATCH"
    echo "saved work-tree diff: $PATCH ($(wc -l < "$PATCH") lines)"
    git reset --hard "$TIP"
    if [ -s "$PATCH" ]; then
        git apply "$PATCH" || echo "WARNING: patch did not apply cleanly; it is saved at $PATCH"
    fi
    echo "HEAD is now $(git rev-parse HEAD)"
fi

if [ ! -x "$VENV/bin/python" ]; then
    echo "rebuilding $VENV"
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet pyyaml gmpy2
else
    echo "venv present: $VENV"
fi

echo "re-deriving the label pins (no boot needed):"
python3 tools/check_pins.py || true
