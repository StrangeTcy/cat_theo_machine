"""Inspect stored gap machinery records in the persisted talk state.

Walks the learned graph of the last talk checkpoint and prints every
gap record, missing-render-law record, ranked-gap chain, and asked
question as machine terms. Pure machine-term walking: no host-side
type inspection.
"""

from __future__ import annotations

import os
import sys

if __package__ in (None, ""):
    IMPORT_ROOT = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    PACKAGE_NAME = os.path.basename(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    CHILD_ARGS = [sys.executable, "-m", PACKAGE_NAME + ".probes.gap_probe"]
    CHILD_ENV = os.environ.copy()
    CHILD_ENV["PYTHONPATH"] = IMPORT_ROOT
    CHILD = __import__("subprocess").run(
        CHILD_ARGS, cwd=IMPORT_ROOT, env=CHILD_ENV,
    )
    raise SystemExit(CHILD.returncode)

from cat_theo_machine import machine as M  # must load first: machine pulls graph in
from cat_theo_machine import graph as G
from cat_theo_machine import labels as Lmod
from cat_theo_machine import machine as M
from cat_theo_machine import wire as W

CHECKPOINT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "snapshots",
    "talk_state.wire",
)

restored = W.load_checkpoint(CHECKPOINT)
version = M.Head(restored)()

gap_records = M.EmptyList
missing_law_records = M.EmptyList
ranked_records = M.EmptyList
asked_records = M.EmptyList

gap_reversed = M.EmptyList
missing_reversed = M.EmptyList
ranked_reversed = M.EmptyList
asked_reversed = M.EmptyList

agenda = G.GraphNodes(version)()
while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
    node = M.Head(agenda)()
    agenda = M.Tail(agenda)()
    if M.IsPair(node)() is M.truth_value:
        node_head = M.Head(node)()
        if M.Compare(node_head, Lmod.GapRecordLabel)() is M.truth_value:
            gap_reversed = M.Pair(node, gap_reversed)
        elif M.Compare(
            node_head, Lmod.MissingRenderLawLabel,
        )() is M.truth_value:
            missing_reversed = M.Pair(node, missing_reversed)
        elif M.Compare(node_head, Lmod.RankedGapsLabel)() is M.truth_value:
            ranked_reversed = M.Pair(node, ranked_reversed)
        elif M.Compare(node_head, Lmod.AskedQuestionLabel)() is M.truth_value:
            asked_reversed = M.Pair(node, asked_reversed)

gap_records = M.Reverse(gap_reversed)()
missing_law_records = M.Reverse(missing_reversed)()
ranked_records = M.Reverse(ranked_reversed)()
asked_records = M.Reverse(asked_reversed)()

print("== gap records ==")
scan = gap_records
while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
    print(M.PrettyTerm(M.Head(scan)(), M.AllConstructors)())
    scan = M.Tail(scan)()

print("== missing render law records ==")
scan = missing_law_records
while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
    print(M.PrettyTerm(M.Head(scan)(), M.AllConstructors)())
    scan = M.Tail(scan)()

print("== ranked gap chains ==")
scan = ranked_records
while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
    print(M.PrettyTerm(M.Head(scan)(), M.AllConstructors)())
    scan = M.Tail(scan)()

print("== asked questions ==")
scan = asked_records
while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
    print(M.PrettyTerm(M.Head(scan)(), M.AllConstructors)())
    scan = M.Tail(scan)()

print(
    "OPEN_DANGLING",
    M.IdentityCompare(
        G.GapOpen(
            M.Pair(
                Lmod.DanglingReferenceLabel,
                M.Pair(M.Char("cold"), M.EmptyList),
            ),
            version,
        )(),
        M.truth_value,
    )() is M.truth_value,
)
