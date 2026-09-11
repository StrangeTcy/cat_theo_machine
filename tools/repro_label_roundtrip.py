"""Round-trip an explanation label through the snapshot codec.

Host-side diagnostic for the label-registration gap. Thirteen labels added
with `explanation.py`, and five older ones, appear in neither
`labels.sync_from_namespace` nor `persistence.SNAPSHOT_SYMBOL_NAMES`.
Whether that omission does anything is the open question: the capture path
may not need those names, in which case the missing entries are dead debt,
or it may need them, in which case a saved explanation does not come back.

Two facts about the codec shape this experiment, and both were established
by running earlier versions of this script:

- `SnapshotCodec` serializes named roots only. A term parked with
  `graph.add_node` is not reachable from any root, so it never reaches the
  snapshot: a registered control atom vanished too. Probes therefore ride
  in as `extra_roots`, which the capture path supports and `load_snapshot`
  returns in `state.roots`.
- Restore resolves symbols through the runtime namespace, not through
  `SNAPSHOT_SYMBOL_NAMES`, so the interesting question is entirely on the
  capture side: what does the encoder do with an atom it has no name for.

The probe is one term carrying both atoms, registered and unregistered, so
both ride through identical conditions:

    Pair(InvariantLabel, Pair(ExplanationPlanLabel, EmptyList))

`InvariantLabel` is registered in both tables; `ExplanationPlanLabel` is in
neither. A second root carries a whole `ExplanationPlan`.

Outcomes:

    D1_LIVE          the registered atom came back and the unregistered one
                     did not, or the term is no longer structurally equal
    D1_INERT         both atoms came back with identity intact -- the
                     missing entries are debt, not a live defect
    INCONCLUSIVE     the registered control failed too -- the experiment
                     says nothing about registration
    SAVE_FAILED      the capture path raised

Usage, from anywhere:

    python tools/repro_label_roundtrip.py
"""

import os
import sys
import traceback

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
    marks = M.Pair(empty, M.Pair(empty, empty))
    step = Emod.SpineStep(preserves, M.truth_value, marks)()
    spine = Emod.ExplanationSpine(empty, M.Pair(step, empty), empty)()
    core = Emod.CoreIdea(empty, Emod.IDEA_INVARIANT)()
    plan = Emod.ExplanationPlan(
        Emod.AudienceLevel(M.Char("student"))(), empty, spine, core, empty
    )()
    return plan


def main():
    P.SetDebugTrace(M.false_value)()
    runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    runtime.graph._search_disable_console = M.truth_value
    graph = runtime.graph

    control_atom = Lmod.InvariantLabel
    test_atom = Lmod.ExplanationPlanLabel
    probe = M.Pair(control_atom, M.Pair(test_atom, M.EmptyList))
    plan = _build_plan(graph)

    codec = SnapshotCodec(_runtime_namespace())
    try:
        snapshot = codec.capture(graph, extra_roots={"d1_probe": probe, "d1_plan": plan})
    except Exception:
        print("SAVE_FAILED")
        traceback.print_exc()
        return 3

    state = codec.load_snapshot(snapshot)
    restored_probe = state.roots["d1_probe"]
    restored_plan = state.roots["d1_plan"]

    structural = M.TermEqual(probe, restored_probe)()
    control_identity = M.IdentityCompare(M.Head(restored_probe)(), control_atom)()
    test_identity = M.IdentityCompare(
        M.Head(M.Tail(restored_probe)())(), test_atom
    )()
    plan_present = _subterm_holds(restored_plan, plan)

    print("probe structural equality :", structural is M.truth_value)
    print("control atom identity     :", control_identity is M.truth_value, "(InvariantLabel, both tables)")
    print("test atom identity        :", test_identity is M.truth_value, "(ExplanationPlanLabel, neither table)")
    print("whole plan survived       :", plan_present is M.truth_value)

    if control_identity is M.false_value:
        print()
        print("INCONCLUSIVE")
        print("the registered control did not survive capture, so this probe")
        print("says nothing about label registration")
        return 4
    if structural is M.false_value or test_identity is M.false_value:
        print()
        print("D1_LIVE")
        print("the registered atom survived and the unregistered one did not")
        return 1
    print()
    print("D1_INERT")
    print("the unregistered label round-tripped with identity intact: the")
    print("missing entries are debt, not a live defect")
    return 0


if __name__ == "__main__":
    sys.exit(main())
