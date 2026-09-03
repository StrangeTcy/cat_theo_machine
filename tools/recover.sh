#!/bin/sh
# Recover a sandbox after a reset.
#
# A reset keeps working files and drops git objects, so a session can wake
# up with a full tree and a HEAD that no longer descends from the
# integration tip. Committing in that state produces an enormous diff
# against the wrong base -- 190 files and 359k lines, repeatedly -- and
# the only thing that catches it is a rejected push.
#
# This script checks and repairs in one command. It is host-side tooling
# and touches no machine code.
#
#   sh tools/recover.sh              check and repair
#   sh tools/recover.sh --check      report only, change nothing
#
# The descent check runs first and always prints, because it is the whole
# question. The repair then diffs the WORKING TREE AGAINST THE TIP, not
# against HEAD: against HEAD the diff is the phantom one, every commit
# the reset lost, and re-applying it after the reset would undo the
# programme. Against the tip the diff is the local edits and nothing
# else, which is the only thing worth carrying over.

set -e

BRANCH="${INTEGRATION_BRANCH:-arena/01a06542-cat-theo-machine}"
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
VENV="${VENV:-$HOME/.venv}"
CHECK_ONLY=""
FORCE=""

for arg in "$@"; do
    case "$arg" in
        --check) CHECK_ONLY="yes" ;;
        --force) FORCE="yes" ;;
    esac
done

cd "$REPO_ROOT"

echo "integration branch: $BRANCH"
echo "local HEAD:         $(git rev-parse HEAD)"

git fetch origin "$BRANCH" 2>/dev/null
TIP=$(git rev-parse FETCH_HEAD)

echo "integration tip:    $TIP"

# 1. The descent check. Printed first, always: everything else is detail.
if git merge-base --is-ancestor "$TIP" HEAD; then
    echo "descent:            OK - HEAD descends from the integration tip"
else
    echo "descent:            BROKEN - HEAD does not descend from the integration tip"
fi

# 2. The phantom signature. Files persist, git objects do not, so a reset
#    shows up as the whole tree differing against an old HEAD.
CHANGED=$(git status --porcelain | wc -l | tr -d " ")
echo "paths vs HEAD:      $CHANGED"
if [ "$CHANGED" -gt 50 ]; then
    echo "                    ^ phantom: this is the reset signature, not work."
    echo "                      The tree is right and HEAD is wrong; diffing the"
    echo "                      tree against HEAD measures the commits that were"
    echo "                      lost, which is why the repair diffs against the tip."
fi

if git merge-base --is-ancestor "$TIP" HEAD; then
    DESCENT_OK="yes"
else
    DESCENT_OK="no"
fi

if [ "$DESCENT_OK" = "yes" ]; then
    if [ -n "$CHECK_ONLY" ]; then
        echo "--check given, changing nothing"
    fi
else
    if [ -n "$CHECK_ONLY" ]; then
        echo "--check given, changing nothing"
        exit 1
    fi

    PATCH=$(mktemp /tmp/recover.XXXXXX.patch)
    # Local edits only: the working tree measured against the tip.
    git diff "$TIP" > "$PATCH"
    LINES=$(wc -l < "$PATCH" | tr -d " ")

    # Refuse to carry a diff that is not local edits. A few hundred lines is
    # a session's work; tens of thousands means the tree is not the tip's
    # content and resetting would destroy something this script cannot see.
    if [ "$LINES" -gt 20000 ] && [ -z "$FORCE" ]; then
        echo ""
        echo "REFUSING to reset: the working tree differs from the tip in $LINES lines."
        echo "That is not local work, so this is not the reset case. Inspect"
        echo "  $PATCH"
        echo "and rerun with --force only once you know what those lines are."
        exit 1
    fi

    echo "carrying local edits: $PATCH ($LINES lines)"
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

echo "re-deriving the shard-cursor pins (no boot needed):"
python3 tools/check_pins.py || true
