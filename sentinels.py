"""Sentinels a test returns for a known-open defect.

An unmet milestone, or a defect pinned by a test, returns one of these and
registers the same sentinel as its expectation, so the suite reports OK
while the defect is open. That is only honest if the runner prints them
apart from the pass column: `TestResultsSummary` reads `OPEN_SENTINELS`
to do exactly that, and the convention is the one `MILESTONES.md` sets for
unmet criteria.

This module exists because `graph.py` cannot import `testsuite` —
`testsuite` imports `graph` — and the summary has to recognise the
sentinels without pulling in the test module.

Adding a sentinel here is a `[SHARED]` act: the suite's open count is a
standing claim about the build, and a sentinel invented inside a track
block would be invisible to the count.
"""

from . import machine as M

MILESTONE_SKIPPED = M.Char("milestone-skipped")
VALUE_ATOM_IDENTITY_OPEN = M.Char("value-atom-identity-open")

OPEN_SENTINELS = (
    MILESTONE_SKIPPED,
    VALUE_ATOM_IDENTITY_OPEN,
)

__all__ = [
    "MILESTONE_SKIPPED",
    "VALUE_ATOM_IDENTITY_OPEN",
    "OPEN_SENTINELS",
]
