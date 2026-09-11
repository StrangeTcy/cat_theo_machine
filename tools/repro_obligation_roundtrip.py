"""Round-trip the blackboard obligation through the snapshot codec.

A separate finding from the label-registration question, kept in its own
script because it is a different defect with a different owner.

The label probe (tools/repro_label_roundtrip.py) came back D1_INERT: an
unregistered label atom survives capture and restore with identity intact.
The assembled `ExplanationPlan` did not survive, and this script shows why
it is not the labels. Probes, all captured in one pass:

    shape        a three-long chain of registered labels only -- survives
    label_<name> Pair(InvariantLabel, Pair(<one E label>, EmptyList))
                 -- all thirteen survive, identity intact
    embedded     Pair(InvariantLabel, preserves)  -- does NOT survive
    plan         the assembled ExplanationPlan    -- does NOT survive

So the loss is in the embedded obligation, not in the labels. Walking the
obligation and its restoration side by side puts the first divergence at
<root>.tail.head, where both sides are atoms: not pairs, not EmptyList,
and matching none of the 1,477 entries in the runtime namespace, so they
are value atoms rather than named symbols. Whether the restored atom
carries the same value or a lost one is unresolved -- PrettyTerm on it
does not terminate.

Four outcomes, printed:

    OBLIGATION_LOST   the embedded term is not structurally equal after
                      restore, while the label chain control survives
    CONTROL_LOST      the label chain control failed too, so this run says
                      nothing
    ROUND_TRIPS       both survived, and the earlier finding is fixed

Usage, from anywhere:

    python tools/repro_obligation_roundtrip.py
"""

import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from cat_theo_machine import labels as Lmod  # noqa: E402
from cat_theo_machine import machine as M  # noqa: E402
from cat_theo_machine import proof as P  # noqa: E402
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace  # noqa: E402
from cat_theo_machine.persistence import SnapshotCodec  # noqa: E402
from cat_theo_machine.runtime import boot_from_packs  # noqa: E402

E_LABELS = (
    "ExplanationPlanLabel",
    "CoreIdeaLabel",
    "RepresentationShiftLabel",
    "KeyInvariantLabel",
    "NaiveFailureLabel",
    "BridgeLemmaLabel",
    "NeededForLabel",
    "ImportedBecauseLabel",
    "OmittedDetailLabel",
    "AudienceLevelLabel",
    "ExplanationSpineLabel",
    "SpineStepLabel",
    "RenderLawLabel",
)


def main():
    P.SetDebugTrace(M.false_value)()
    runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    runtime.graph._search_disable_console = M.truth_value
    graph = runtime.graph

    from cat_theo_machine import explanation as Emod
    from cat_theo_machine.testsuite import _ExplanationToy

    toy = _ExplanationToy
    empty = M.EmptyList
    preserves = toy.blackboard_preserves(graph)
    marks = M.Pair(empty, M.Pair(empty, empty))
    step = Emod.SpineStep(preserves, M.truth_value, marks)()
    spine = Emod.ExplanationSpine(empty, M.Pair(step, empty), empty)()
    core = Emod.CoreIdea(empty, Emod.IDEA_INVARIANT)()
    plan = Emod.ExplanationPlan(
        Emod.AudienceLevel(M.Char("student"))(), empty, spine, core, empty
    )()

    ns = _runtime_namespace()
    shape = M.Pair(
        Lmod.InvariantLabel,
        M.Pair(Lmod.PreservesLabel, M.Pair(Lmod.InvariantLabel, empty)),
    )

    extra = {
        "shape": shape,
        "embedded": M.Pair(Lmod.InvariantLabel, preserves),
        "plan": plan,
    }
    for name in E_LABELS:
        extra["label_" + name] = M.Pair(Lmod.InvariantLabel, M.Pair(ns[name], empty))

    codec = SnapshotCodec(ns)
    state = codec.load_snapshot(codec.capture(graph, extra_roots=extra))

    shape_ok = M.TermEqual(shape, state.roots["shape"])() is M.truth_value
    embedded_ok = M.TermEqual(extra["embedded"], state.roots["embedded"])() is M.truth_value
    plan_ok = M.TermEqual(plan, state.roots["plan"])() is M.truth_value

    print("label chain of registered labels :", shape_ok)
    print("chain embedding the obligation   :", embedded_ok)
    print("assembled ExplanationPlan        :", plan_ok)
    print()
    print("unregistered E labels in nested position:")
    for name in E_LABELS:
        restored = state.roots["label_" + name]
        inner = M.Head(M.Tail(restored)())()
        print("    %-32s %s" % (name, "identical" if M.IdentityCompare(inner, ns[name])() is M.truth_value else "DIFFERENT"))

    if not shape_ok:
        print()
        print("CONTROL_LOST")
        return 4
    if embedded_ok and plan_ok:
        print()
        print("ROUND_TRIPS")
        return 0
    print()
    print("OBLIGATION_LOST")
    return 1


if __name__ == "__main__":
    sys.exit(main())
