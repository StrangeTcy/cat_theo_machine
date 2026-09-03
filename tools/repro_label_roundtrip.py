"""Round-trip one explanation-plan term through a snapshot.

Host-side diagnostic for the label-registration gap. Thirteen labels added
with `explanation.py` appear in neither `labels.sync_from_namespace` nor
`persistence.SNAPSHOT_SYMBOL_NAMES`, and five older labels are missing from
both as well. Whether that omission does anything is the open question: the
sync path may not need those names, in which case the missing entries are
dead debt, or it may need them, in which case a saved explanation does not
come back.

This script decides it. It builds one `ExplanationPlan`, stores it in the
booted graph, snapshots, reloads, and looks for the term in the reloaded
graph. Four outcomes, printed and exit-coded:

    FOUND_IDENTICAL   the term survived and its head is identical to the
                      in-process label singleton -- the omission is inert
                      for this path
    FOUND_DRIFTED     the term survived but its head is not identical to
                      the singleton -- identity comparisons against E terms
                      silently fail after a restore
    ABSENT            the term did not come back at all
    SAVE_FAILED       the codec refused or raised while writing

Usage, from the parent of the package directory:

    python tools/repro_label_roundtrip.py
"""

import os
import shutil
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cat_theo_machine import machine as M  # noqa: E402
from cat_theo_machine import proof as P  # noqa: E402
from cat_theo_machine.graph import GraphNodes  # noqa: E402
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace  # noqa: E402
from cat_theo_machine.persistence import SnapshotCodec  # noqa: E402
from cat_theo_machine.runtime import boot_from_packs, boot_from_snapshot  # noqa: E402


def _subterm_holds(term, wanted):
    """True when `wanted` occurs anywhere inside `term`."""
    if M.TermEqual(term, wanted)() is M.truth_value:
        return M.truth_value
    if M.IsPair(term)() is M.false_value:
        return M.false_value
    if _subterm_holds(M.Head(term)(), wanted) is M.truth_value:
        return M.truth_value
    return _subterm_holds(M.Tail(term)(), wanted)


def _build_plan(graph):
    from cat_theo_machine import explanation as Emod
    from cat_theo_machine.testsuite import _ExplanationToy

    toy = _ExplanationToy
    empty = M.EmptyList
    preserves = toy.blackboard_preserves(graph)
    observable = Emod.PreservesObservable(preserves)()
    marks = M.Pair(empty, M.Pair(empty, empty))
    step = Emod.SpineStep(preserves, M.truth_value, marks)()
    spine = Emod.ExplanationSpine(empty, M.Pair(step, empty), empty)()
    core = Emod.CoreIdea(empty, Emod.IDEA_INVARIANT)()
    plan_edge = Emod.ExplanationPlan(
        Emod.AudienceLevel(M.Char("student"))(), empty, spine, core, empty
    )
    return plan_edge, plan_edge(), observable


def main():
    P.SetDebugTrace(M.false_value)()
    runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    runtime.graph._search_disable_console = M.truth_value
    graph = runtime.graph

    plan_edge, plan_term, _observable = _build_plan(graph)

    stored = M.false_value
    try:
        graph.add_node(plan_edge)
        stored = M.truth_value
    except Exception:
        pass
    if stored is M.false_value:
        graph.add_node(plan_term)

    tmpdir = tempfile.mkdtemp()
    snap_path = os.path.join(tmpdir, "snapshot.json")
    try:
        try:
            codec = SnapshotCodec(_runtime_namespace())
            codec.save(graph, snap_path, progress=M.false_value)
        except Exception:
            print("SAVE_FAILED")
            traceback.print_exc()
            return 3

        graph2 = boot_from_snapshot(snap_path, _runtime_namespace()).graph

        found = M.EmptyList
        walker = GraphNodes(graph2)()
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            node = M.Head(walker)()
            if _subterm_holds(node, plan_term) is M.truth_value:
                found = node
            walker = M.Tail(walker)()

        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            print("ABSENT")
            print("the plan term did not come back through the snapshot")
            return 2

        from cat_theo_machine import labels as Lmod

        head_identical = M.IdentityCompare(
            M.Head(plan_term)(), Lmod.ExplanationPlanLabel
        )()
        if head_identical is M.truth_value:
            print("FOUND_IDENTICAL")
            print("head is identical to the in-process singleton")
            return 0
        print("FOUND_DRIFTED")
        print("head is NOT identical to the in-process singleton")
        return 1
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
