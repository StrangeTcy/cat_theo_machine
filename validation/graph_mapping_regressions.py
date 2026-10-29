"""Identity, monomorphism, and persistent exploration regressions."""

from pathlib import Path
from tempfile import TemporaryDirectory

from hyge import machine as M
from hyge import graph as G
from hyge import labels as L
from hyge import persistence as Persist
from hyge.runtime import make_fresh_runtime


if __name__ == "__main__":
    runtime = make_fresh_runtime()
    empty = M.EmptyList
    pattern_marker = M.Atom()
    host_marker = M.Atom()
    p_left = M.Pair(pattern_marker, empty)
    p_right = M.Pair(pattern_marker, empty)
    p_third = M.Atom()
    h_left = M.Pair(host_marker, empty)
    h_right = M.Pair(host_marker, empty)
    h_third = M.Atom()
    pattern = G.GraphVersion(M.Pair(p_left, M.Pair(p_right, M.Pair(p_third, empty))), empty, empty)()
    host = G.GraphVersion(M.Pair(h_left, M.Pair(h_right, M.Pair(h_third, empty))), empty, empty)()
    base = G.Map(pattern, host, M.Pair(G.Send(p_left, h_left)(), empty))()

    assert M.TermEqual(p_left, p_right)() is M.truth_value
    assert M.IdentityCompare(p_left, p_right)() is M.false_value
    assert M.Head(G.MappedHostForPat(G.MapRoot(base)(), p_right)())() is M.false_value
    extended = G.MapExtendOneStep(base, p_right, h_right)()
    assert G.IsMap(extended)() is M.truth_value
    assert M.Tail(G.MappedHostForPat(G.MapRoot(extended)(), p_right)())() is h_right
    collision = G.MapExtendOneStep(base, p_right, h_left)()
    assert M.Head(collision)() is L.MissLabel
    assert M.Head(M.Head(M.Tail(M.Tail(collision)())())())() is L.ReasonApartLabel
    stranger = M.Pair(pattern_marker, empty)
    assert M.Head(G.MapExtendOneStep(base, stranger, h_right)())() is L.MissLabel
    host_stranger = M.Pair(host_marker, empty)
    assert M.Head(G.MapExtendOneStep(base, p_right, host_stranger)())() is L.MissLabel
    complete = G.MapExtendOneStep(extended, p_third, h_third)()
    assert G.MapSendsEveryElement(complete, pattern)() is M.truth_value
    wrong_source = G.GraphVersion(G.GraphNodes(pattern)(), empty, empty)()
    assert G.MapSendsEveryElement(complete, wrong_source)() is M.false_value
    collapsed = G.Map(pattern, host, M.Pair(G.Send(p_left, h_left)(),
        M.Pair(G.Send(p_right, h_left)(), M.Pair(G.Send(p_third, h_third)(), empty))))()
    assert G.MapSendsEveryElement(collapsed, pattern)() is M.false_value
    print("PASS identity-safe membership, lookup, and injectivity")

    # Edge-first matching must recheck incidence when an endpoint is committed later.
    edge_label = M.Atom()
    pattern_edge = M.Pair(edge_label, M.Pair(p_left, M.Pair(p_right, empty)))
    host_edge = M.Pair(edge_label, M.Pair(h_left, M.Pair(h_right, empty)))
    edge_pattern = G.GraphVersion(M.Pair(p_left, M.Pair(p_right, empty)), M.Pair(pattern_edge, empty), empty)()
    edge_host = G.GraphVersion(M.Pair(h_left, M.Pair(h_right, empty)), M.Pair(host_edge, empty), empty)()
    edge_first = G.Map(edge_pattern, edge_host, M.Pair(G.Send(pattern_edge, host_edge)(), empty))()
    crossed = G.MapExtendOneStep(edge_first, p_left, h_right)()
    assert M.Head(crossed)() is L.MissLabel
    assert M.Head(M.Head(M.Tail(M.Tail(crossed)())())())() is L.ReasonPositionalLabel
    aligned = G.MapExtendOneStep(edge_first, p_left, h_left)()
    assert G.IsMap(aligned)() is M.truth_value
    assert M.Head(G.MapExtendOneStep(G.Map(edge_pattern, edge_host, empty)(), p_left, host_edge)())() is L.MissLabel
    edge_complete = G.MapExtendOneStep(aligned, p_right, h_right)()
    assert G.MapSendsEveryElement(edge_complete, edge_pattern)() is M.truth_value
    other_relation = M.Pair(M.Atom(), M.Pair(h_left, M.Pair(h_right, empty)))
    assert G.EdgeSendConsistent(G.MapRoot(edge_complete)(), pattern_edge, other_relation)() is M.false_value
    textual_pattern_edge = M.Pair(M.Char("relation"), M.Pair(p_left, empty))
    textual_host_edge = M.Pair(M.Char("relation"), M.Pair(h_left, empty))
    different_text_edge = M.Pair(M.Char("other relation"), M.Pair(h_left, empty))
    assert G.EdgeSendConsistent(G.MapRoot(edge_complete)(), textual_pattern_edge, textual_host_edge)() is M.truth_value
    assert G.EdgeSendConsistent(G.MapRoot(edge_complete)(), textual_pattern_edge, different_text_edge)() is M.false_value
    legacy_pattern = M.Pair(M.HypergraphLabel, M.Pair(M.Pair(p_left, empty), M.Pair(empty, empty)))
    legacy_host = M.Pair(M.HypergraphLabel, M.Pair(M.Pair(h_left, empty), M.Pair(empty, empty)))
    legacy_mapping = G.Map(legacy_pattern, legacy_host, M.Pair(G.Send(p_left, h_left)(), empty))()
    assert G.MapSendsEveryElement(legacy_mapping, legacy_pattern)() is M.truth_value
    print("PASS graph roles and endpoint extension after edge matching")

    exploration = G.MapExtensionExploration(base, p_right, empty)()
    history = G.MapExplorationAttempts(exploration)()
    rejected_attempt = G.MapFindAttempt(history, base, p_right, h_left)()
    assert G.IsMapAttempt(rejected_attempt)() is M.truth_value
    assert M.Head(G.MapAttemptOutcome(rejected_attempt)())() is L.MissLabel
    assert G.IsMap(G.MapAttemptOutcome(G.MapFindAttempt(history, base, p_right, h_right)())())() is M.truth_value
    assert G.IsMap(G.MapAttemptOutcome(G.MapFindAttempt(history, base, p_right, h_third)())())() is M.truth_value
    accepted = M.Head(G.MapExplorationAlternatives(exploration)())()
    assert G.GraphChainHasIdentity(G.MapAttemptHistory(G.MapRoot(accepted)())(), rejected_attempt)() is M.truth_value
    legacy_continuation = G.MapExtendOneStep(accepted, p_third, h_third)()
    assert G.IsMap(legacy_continuation)() is M.truth_value
    assert G.GraphChainHasIdentity(G.MapAttemptHistory(G.MapRoot(legacy_continuation)())(), rejected_attempt)() is M.truth_value
    assert G.MapSendsEveryElement(legacy_continuation, pattern)() is M.truth_value

    failed = G.MapExtensionExploration(base, p_left, empty)()
    assert G.MapExplorationAlternatives(failed)() is empty
    failed_history = G.MapExplorationAttempts(failed)()
    left_failure = G.MapFindAttempt(failed_history, base, p_left, h_left)()
    right_failure = G.MapFindAttempt(failed_history, base, p_left, h_right)()
    third_failure = G.MapFindAttempt(failed_history, base, p_left, h_third)()
    assert M.Head(G.MapAttemptOutcome(left_failure)())() is L.MissLabel
    assert M.Head(G.MapAttemptOutcome(right_failure)())() is L.MissLabel
    assert M.Head(G.MapAttemptOutcome(third_failure)())() is L.MissLabel
    retried = G.MapExtensionExploration(base, p_left, empty, failed)()
    assert G.MapExplorationAttempts(retried)() is failed_history
    assert G.MapFindAttempt(G.MapExplorationAttempts(retried)(), base, p_left, h_left)() is left_failure
    print("PASS retained mixed/all-rejected attempts, inherited history, and repeated-attempt reuse")

    forged_attempt = G.MapAttempt(base, p_left, h_left, complete)()
    forged_previous = G.MapExploration(base, empty, M.Pair(forged_attempt, empty))()
    rechecked = G.MapExtensionExploration(base, p_left, empty, forged_previous)()
    assert G.MapExplorationAlternatives(rechecked)() is empty
    corrected_attempt = G.MapFindAttempt(G.MapExplorationAttempts(rechecked)(), base, p_left, h_left)()
    assert M.Head(G.MapAttemptOutcome(corrected_attempt)())() is L.MissLabel
    assert M.IdentityCompare(corrected_attempt, forged_attempt)() is M.false_value
    false_failure = G.MapAttempt(base, p_right, h_right, collision)()
    false_failure_previous = G.MapExploration(base, empty, M.Pair(false_failure, empty))()
    rechecked_success = G.MapExtensionExploration(base, p_right, empty, false_failure_previous)()
    assert M.IsPair(G.MapExplorationAlternatives(rechecked_success)())() is M.truth_value
    corrected_success = G.MapFindAttempt(G.MapExplorationAttempts(rechecked_success)(), base, p_right, h_right)()
    assert G.IsMap(G.MapAttemptOutcome(corrected_success)())() is M.truth_value

    malformed_previous = M.Pair(L.MapExplorationLabel, empty)
    assert G.IsMapExploration(malformed_previous)() is M.false_value
    assert G.MapExplorationAlternatives(G.MapExtensionExploration(base, p_left, empty, malformed_previous)())() is empty
    malformed_history = G.MapExploration(base, empty, M.Atom())()
    assert G.MapExplorationAlternatives(G.MapExtensionExploration(base, p_left, empty, malformed_history)())() is empty
    malformed_send = M.Pair(L.SendLabel, empty)
    malformed_apart = M.Pair(L.ApartLabel, empty)
    assert G.MapRootValid(M.Pair(malformed_send, empty), pattern, host)() is M.false_value
    assert G.MapRootValid(M.Pair(malformed_apart, empty), pattern, host)() is M.false_value
    malformed_law = M.Pair(L.LawLabel, empty)
    assert G.LawMapsComplete(malformed_law)() is M.false_value
    malformed_version = M.Pair(L.GraphVersionLabel, empty)
    assert G.IsGraphVersion(malformed_version)() is M.false_value
    assert G.GraphNodes(malformed_version)() is empty
    assert G.GraphEdges(malformed_version)() is empty
    assert G.MapSendsEveryElement(G.Map(malformed_version, host, empty)(), malformed_version)() is M.false_value
    print("PASS forged cached outcomes and malformed mapping evidence are rechecked or refused")

    runtime.graph.add_node(failed)
    codec = Persist.SnapshotCodec(Persist._runtime_namespace_for_restore())
    with TemporaryDirectory(prefix="hyge-mapping-") as snapshot_directory:
        snapshot_path = str(Path(snapshot_directory) / "mapping.json")
        codec.save(runtime.graph, snapshot_path)
        state = codec.load(snapshot_path)
        codec.activate(state, runtime.graph)
        restored = M.Head(M.FromContextGetNodes(runtime.graph)())()
        assert G.IsMapExploration(restored)() is M.truth_value
        restored_mapping = G.MapExplorationMapping(restored)()
        restored_pat = M.Head(G.GraphNodes(G.MapPattern(restored_mapping)())())()
        restored_host = M.Head(G.GraphNodes(G.MapHost(restored_mapping)())())()
        restored_attempt = G.MapFindAttempt(
            G.MapExplorationAttempts(restored)(), restored_mapping, restored_pat, restored_host
        )()
        assert G.IsMapAttempt(restored_attempt)() is M.truth_value
        assert G.MapAttemptMapping(restored_attempt)() is restored_mapping
        assert M.Head(G.MapAttemptOutcome(restored_attempt)())() is L.MissLabel
        replayed = G.MapExtensionExploration(restored_mapping, restored_pat, empty, restored)()
        assert G.MapExplorationAlternatives(replayed)() is empty
        assert G.MapExplorationAttempts(replayed)() is G.MapExplorationAttempts(restored)()
    print("PASS file-backed exploration snapshot and failure reuse after restore")
