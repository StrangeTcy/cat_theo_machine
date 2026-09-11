#!/bin/sh
# Recover a sandbox after a reset.
#
# A reset keeps working files and drops git objects, so a session can wake
# up with a full tree and a HEAD that no longer descends from the
# integration tip. Committing in that state produces an enormous diff
# against the wrong base -- 190 files and 359k lines, repeatedly -- and
# the only thing that catches it is a rejected push.
#
# THREE STATES, and the direction of the test matters:
#
#   `git merge-base --is-ancestor A B` asks "is A an ancestor of B".
#
#   clean       HEAD == TIP. Safe to commit.
#
#   behind      HEAD is an ancestor of TIP. This is the reset: a fresh
#               clone leaves HEAD below the tip while the working tree
#               still holds the newer files, so no commit points at the
#               work that is sitting in them. Repair by moving HEAD to
#               the tip with `reset --mixed`, which leaves the tree
#               alone -- the work is in the files, not in a patch.
#
#   divergent   neither is an ancestor of the other. A topic branch, a
#               rebase gone wrong, a checkout of the wrong line. The
#               edits have to be carried across, so the repair saves
#               them as a patch first.
#
# Calling "behind" a descent failure is what makes this confusing: HEAD
# does descend from the tip in the everyday sense of the word, just not
# in the direction `merge-base` tests. The script names the state
# instead, and says what it is going to do about it.
#
# This script checks and repairs in one command. It is host-side tooling
# and touches no machine code.
#
#   sh tools/recover.sh              check and repair
#   sh tools/recover.sh --check      report only, change nothing
#
# The phantom diff is measured AGAINST THE TIP, not against HEAD: against
# HEAD the diff is the phantom one, every commit the reset lost, and
# re-applying it after a reset would undo the programme.

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
echo ""

# 1. Which of the three states is this?
STATE="divergent"
if [ "$(git rev-parse HEAD)" = "$TIP" ]; then
    STATE="clean"
elif git merge-base --is-ancestor HEAD "$TIP"; then
    STATE="behind"
elif git merge-base --is-ancestor "$TIP" HEAD; then
    STATE="ahead"
fi

case "$STATE" in
    clean)
        echo "base state:         CLEAN - HEAD is the integration tip"
        ;;
    ahead)
        echo "base state:         AHEAD - HEAD is past the integration tip"
        echo "                      unpushed commits, or a local branch that"
        echo "                      was never pushed. Not the reset case."
        ;;
    behind)
        echo "base state:         BEHIND - HEAD is an ancestor of the integration tip"
        echo "                      this is the reset signature: the tree holds work"
        echo "                      that no commit points at"
        ;;
    divergent)
        echo "base state:         DIVERGENT - HEAD and the tip share no line"
        ;;
esac

# 2. The phantom signature. Files persist, git objects do not, so a reset
#    shows up as the whole tree differing against an old HEAD.
CHANGED=$(git status --porcelain | wc -l | tr -d " ")
echo "paths vs HEAD:      $CHANGED"
if [ "$CHANGED" -gt 50 ]; then
    echo "                    ^ phantom: the tree is right and HEAD is wrong."
    echo "                      Diffing the tree against HEAD measures the commits"
    echo "                      that were lost, which is why the repair below"
    echo "                      measures against the tip instead."
fi
echo ""

if [ "$STATE" = "clean" ]; then
    echo "Safe to commit."
else
    if [ "$STATE" = "behind" ]; then
        echo "=============================================================="
        echo "BEHIND THE TIP - reset signature"
        echo "local checkout is a stale ancestor of the integration tip"
        echo "files may contain recovered work from a newer tree"
        echo "do not commit before moving HEAD to the tip"
        echo "=============================================================="
        echo ""
    fi

    if [ -n "$CHECK_ONLY" ]; then
        echo "--check given, changing nothing"
        exit 1
    fi

    PATCH=$(mktemp /tmp/recover.XXXXXX.patch)
    # Local edits only: the working tree measured against the tip.
    git diff "$TIP" > "$PATCH" || true
    LINES=$(wc -l < "$PATCH" | tr -d " ")

    if [ "$STATE" = "behind" ]; then
        # The tree is newer than the base and already holds the work, so
        # move HEAD and the index to the tip and touch nothing else. No
        # `reset --hard` here: it would delete the surviving files and
        # trust a patch to put them back.
        git reset --mixed "$TIP"
        FILES=$(git diff --name-only | wc -l | tr -d " ")
        echo "HEAD moved to the tip; the working tree was not touched."
        echo "surviving work, measured against the tip: $FILES paths"
        git diff --stat | tail -1
        echo "the same diff is saved at $PATCH"
        if [ "$FILES" -gt 50 ] && [ -z "$FORCE" ]; then
            echo ""
            echo "WARNING: $FILES paths differ from the tip. A recovered session"
            echo "shows its own files here -- four, the last two times. Tens of"
            echo "paths means the tree is not the tip's content. Inspect before"
            echo "committing rather than assuming the recovery worked."
        fi
    else
        # Divergent or ahead: the edits have to be carried across, and the
        # patch is the only copy of them, so refuse to move if it is not
        # local work. Tens of thousands of lines means the tree is not the
        # tip's content and a reset would destroy something unseen.
        if [ "$LINES" -gt 20000 ] && [ -z "$FORCE" ]; then
            echo "REFUSING to reset: the working tree differs from the tip in $LINES lines."
            echo "That is not local work, so this is not a case this script can"
            echo "repair safely. Inspect"
            echo "  $PATCH"
            echo "and rerun with --force only once you know what those lines are."
            exit 1
        fi
        echo "carrying local edits: $PATCH ($LINES lines)"
        git reset --hard "$TIP"
        if [ -s "$PATCH" ]; then
            git apply "$PATCH" || echo "WARNING: patch did not apply cleanly; it is saved at $PATCH"
        fi
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
