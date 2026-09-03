"""Is D3 global or E-only?

D3 is the finding that the blackboard `preserves` obligation does not
survive a snapshot round trip: the first divergence sits at
`<root>.tail.head` on atoms that match none of the 1,477 entries in the
runtime namespace, so they are value atoms rather than named symbols. The
scope of that decides whether `experiment-5-frozen` can be cut at all, so
this script runs the same method against state that has nothing to do with
the explanation substrate:

    stage 1   a graph booted from packs, every serialized root compared
              before and after one save/load
    stage 2   the Set B cumulative checkpoint -- the artifact F and S
              depend on -- through the same comparison
    stage 3   four probes in one capture: a chain of registered labels,
              a chain of Nat and numeral atoms, a taught MultiRule with
              numeral arguments, and the explanation obligation

Comparison is save-then-boot, not capture-then-load. The first version of
this script compared a raw restored root against the live field and
reported ten of nineteen Set B roots as differing; that comparison was
wrong. Restore rebuilds tree-shaped roots from entry chains and the live
field holds the trie, so shape alone accounts for the difference. Booting
puts the upgrade on both sides.

Stage 3 carries both controls: the label chain is known to survive and the
obligation is known to fail. If the Nat atoms and the MultiRule survive
alongside the label chain, D3 is E-only. If they fail too, or if any root
of a real checkpoint fails, D3 is global.

Outcomes: D3_GLOBAL, D3_E_ONLY, or INCONCLUSIVE when a control did not
behave as recorded.

Usage, from anywhere:

    python tools/repro_d3_scope.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from cat_theo_machine import labels as Lmod  # noqa: E402
from cat_theo_machine import machine as M  # noqa: E402
from cat_theo_machine import proof as P  # noqa: E402
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace  # noqa: E402
from cat_theo_machine.persistence import SnapshotCodec  # noqa: E402
from cat_theo_machine.runtime import boot_from_packs, boot_from_snapshot  # noqa: E402

SET_B = "snapshots/set-b-cumulative.json"

ROOT_FIELDS = (
    "all_rules",
    "rule_order",
    "derivations",
    "search_history",
    "search_memo",
    "nat_value_index",
    "dependency_requests",
    "dependency_graph",
    "generator_metrics",
    "last_proof",
    "research_residuals",
    "provenance_map",
    "generator_policy",
    "last_residuals",
    "counterfactual_results",
    "research_mode",
    "research_attempts",
    "intervention_episodes",
    "dependency_policies",
)


def _nat(count, registry):
    """The machine's Nat for `count`, built the way the machine builds them."""
    value = M.Zero
    index = 0
    while index < count:
        pair = M.Succ(value, registry)()
        value = M.Head(pair)()
        registry = M.Head(M.Tail(pair)())()
        index = index + 1
    return value


def _round_trip_roots(graph, ns):
    """Save, boot, and compare every root against the live graph field."""
    tmpdir = tempfile.mkdtemp()
    snap_path = os.path.join(tmpdir, "snapshot.json")
    try:
        codec = SnapshotCodec(ns)
        codec.save(graph, snap_path, progress=M.false_value)
        graph2 = boot_from_snapshot(snap_path, ns).graph
        differing = ()
        for name in ROOT_FIELDS:
            live = getattr(graph, name, M.EmptyList)
            restored = getattr(graph2, name, M.EmptyList)
            if M.TermEqual(live, restored)() is M.false_value:
                differing = differing + (name,)
        return differing
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass


def _build_probes(graph):
    from cat_theo_machine.testsuite import _ExplanationToy, _ResearchToy

    empty = M.EmptyList
    registry = M.FromContextGetConstructors(graph)()
    zero = M.Zero
    one_pair = M.Succ(zero, registry)()
    one = M.Head(one_pair)()
    registry = M.Head(M.Tail(one_pair)())()
    two_pair = M.Succ(one, registry)()
    two = M.Head(two_pair)()

    label_chain = M.Pair(
        Lmod.InvariantLabel,
        M.Pair(Lmod.PreservesLabel, M.Pair(Lmod.InvariantLabel, empty)),
    )
    nat_chain = M.Pair(
        zero,
        M.Pair(one, M.Pair(two, M.Pair(M.GMPRep("42"), M.Pair(M.GMPRep("7"), empty)))),
    )
    rule = _ResearchToy.two_premise_rule("rel", "miss", "conc")
    numeral_rule = _ResearchToy.term(
        _ResearchToy.sym("rel"),
        M.GMPRep("3"),
        _ResearchToy.term(_ResearchToy.sym("inner"), M.GMPRep("5")),
    )
    obligation = _ExplanationToy.blackboard_preserves(graph)
    probes = {
        "label_chain": label_chain,
        "nat_atoms": nat_chain,
        "multi_rule": M.Pair(rule, M.Pair(numeral_rule, empty)),
        "e_obligation": obligation,
    }
    # Component probes: the verdict uses the aggregates above, but knowing
    # which value atom loses fidelity is most of the work of fixing it.
    probes.update(
        {
            "detail_zero": zero,
            "detail_one": one,
            "detail_two": two,
            "detail_gmp42": M.GMPRep("42"),
            "detail_gmp7": M.GMPRep("7"),
            "detail_numeral_pair": M.Pair(M.GMPRep("3"), M.Pair(M.GMPRep("5"), empty)),
            "detail_rule": rule,
            "detail_numeral_term": numeral_rule,
        }
    )
    return probes


def main():
    P.SetDebugTrace(M.false_value)()
    ns = _runtime_namespace()

    runtime, _packs = boot_from_packs(PACK_PATHS, ns)
    runtime.graph._search_disable_console = M.truth_value
    fresh_differing = _round_trip_roots(runtime.graph, ns)
    print("stage 1 -- graph booted from packs")
    print("    roots compared:", len(ROOT_FIELDS))
    print("    differing     :", fresh_differing if fresh_differing else "none")

    set_b_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), SET_B
    )
    set_b_differing = ()
    if os.path.exists(set_b_path):
        set_b_graph = boot_from_snapshot(set_b_path, ns).graph
        set_b_graph._search_disable_console = M.truth_value
        set_b_differing = _round_trip_roots(set_b_graph, ns)
        print()
        print("stage 2 -- Set B cumulative checkpoint")
        print("    differing     :", set_b_differing if set_b_differing else "none")
    else:
        print()
        print("stage 2 -- SKIPPED,", SET_B, "not present")

    probes = _build_probes(runtime.graph)
    codec = SnapshotCodec(ns)
    state = codec.load_snapshot(codec.capture(runtime.graph, extra_roots=probes))
    results = {}
    for name, term in probes.items():
        results[name] = M.TermEqual(term, state.roots[name])() is M.truth_value

    print()
    print("stage 3 -- probes, one capture")
    for name in ("label_chain", "nat_atoms", "multi_rule", "e_obligation"):
        print("    %-22s %s" % (name, "survives" if results[name] else "LOST"))
    print("    components:")
    for name in sorted(n for n in results if n.startswith("detail_")):
        print("        %-18s %s" % (name[7:], "survives" if results[name] else "LOST"))

    print()
    print("stage 4 -- are the values lost, or only their identity?")
    restored_two = state.roots["detail_two"]
    reg = M.FromContextGetConstructors(runtime.graph)()
    nat_eq_two = M.NatEq(restored_two, _nat(2, reg), reg)()
    nat_eq_three = M.NatEq(restored_two, _nat(3, reg), reg)()
    print("    NatEq(restored two, fresh two)  :", nat_eq_two is M.truth_value)
    print("    NatEq(restored two, fresh three):", nat_eq_three is M.truth_value)
    print("    TermEqual(restored two, two)    :", results["detail_two"])
    if nat_eq_two is M.truth_value and nat_eq_three is M.false_value:
        print("    verdict: values survive; identity and TermEqual do not")
    else:
        print("    verdict: values do not survive")

    print()
    if not results["label_chain"] or results["e_obligation"]:
        print("INCONCLUSIVE")
        print("a control did not behave as recorded: the label chain must")
        print("survive and the obligation must fail, or the run says nothing")
        return 4
    if not results["nat_atoms"] or not results["multi_rule"] or fresh_differing or set_b_differing:
        print("D3_GLOBAL")
        print("state outside the explanation substrate loses fidelity too")
        return 1
    print("D3_E_ONLY")
    print("Nat atoms and taught rules survive; only the explanation")
    print("obligation fails to round-trip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
