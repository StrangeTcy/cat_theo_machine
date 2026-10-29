"""Run existing graph fixtures against the repaired mapping and surgery path."""

from hyge import machine as M
from hyge import graph as G
from hyge import labels as L
from hyge import testsuite as T
from hyge.runtime import make_fresh_runtime


if __name__ == "__main__":
    runtime = make_fresh_runtime()
    graph = runtime.graph
    assert T.FireLawSurgeryTest(graph)() is M.truth_value
    assert T.FireLawDanglingModeTest(graph)() is M.truth_value
    assert T.LawMapsCompleteTest(graph)() is M.truth_value
    assert T.DanglingEdgesTest(graph)() is M.truth_value
    assert T.MapExtensionAlternativesTest(graph)() is M.truth_value
    assert T.StructuredMissReasonTest(graph)() is M.truth_value
    assert T.EdgeSendPositionalConsistencyTest(graph)() is M.truth_value
    assert T.GraphCurrentVersionTest(graph)() is M.truth_value
    assert T.MinimalGraphOneStepMapExtensionTest(graph)() is M.truth_value
    assert T.MinimalGraphSourceConstraintTest(graph)() is M.truth_value
    print("PASS: all ten existing graph rewriting fixtures")

    empty = M.EmptyList
    relation = M.Char("source relation")
    replacement_relation = M.Char("replacement relation")
    p_a = M.Thingy()
    p_b = M.Thingy()
    k_a = M.Thingy()
    r_a = M.Thingy()
    r_c = M.Thingy()
    h_a = M.Thingy()
    h_b = M.Thingy()
    p_edge = M.Pair(relation, M.Pair(p_a, M.Pair(p_b, empty)))
    h_edge = M.Pair(relation, M.Pair(h_a, M.Pair(h_b, empty)))
    distractor = M.Pair(replacement_relation, M.Pair(h_a, M.Pair(h_b, empty)))
    r_edge = M.Pair(replacement_relation, M.Pair(r_a, M.Pair(r_c, empty)))
    left = G.GraphVersion(M.Pair(p_a, M.Pair(p_b, empty)), M.Pair(p_edge, empty), empty)()
    interface = G.GraphVersion(M.Pair(k_a, empty), empty, empty)()
    right = G.GraphVersion(M.Pair(r_a, M.Pair(r_c, empty)), M.Pair(r_edge, empty), empty)()
    host = G.GraphVersion(M.Pair(h_a, M.Pair(h_b, empty)), M.Pair(h_edge, M.Pair(distractor, empty)), empty)()
    k_left = G.Map(interface, left, M.Pair(G.Send(k_a, p_a)(), empty))()
    k_right = G.Map(interface, right, M.Pair(G.Send(k_a, r_a)(), empty))()
    law = G.Law(left, interface, right, k_left, k_right, empty)()
    initial = G.Map(left, host, empty)()
    first = G.MapExtensionExploration(initial, p_a, empty)()
    first_attempt = M.Head(G.MapExplorationAttempts(first)())()
    first_map = M.Head(G.MapExplorationAlternatives(first)())()
    second = G.MapExtensionExploration(first_map, p_b, empty)()
    assert M.Tail(G.MapExplorationAlternatives(second)())() is empty
    second_map = M.Head(G.MapExplorationAlternatives(second)())()
    third = G.MapExtensionExploration(second_map, p_edge, empty)()
    assert M.Tail(G.MapExplorationAlternatives(third)())() is empty
    completed = M.Head(G.MapExplorationAlternatives(third)())()
    assert G.MapSendsEveryElement(completed, left)() is M.truth_value
    history = G.MapAttemptHistory(G.MapRoot(completed)())()
    assert G.GraphChainHasIdentity(history, first_attempt)() is M.truth_value
    last_attempt = M.Head(G.MapExplorationAttempts(third)())()
    assert M.Head(G.MapAttemptOutcome(last_attempt)())() is L.MissLabel
    assert G.MapAttemptHost(last_attempt)() is distractor
    rewritten = G.FireLaw(host, law, completed, G.DanglingDelete()())()
    child = M.Head(rewritten)()
    assert child is not empty
    child_edge = M.Head(G.GraphEdges(child)())()
    assert M.Head(G.EdgeEndpoints(child_edge)())() is h_a
    assert M.Head(M.Tail(G.EdgeEndpoints(child_edge)())())() is r_c
    assert M.Tail(G.GraphEdges(child)())() is empty
    assert G.GraphHasElement(child, h_b)() is M.false_value
    assert G.GraphHasElement(host, h_edge)() is M.truth_value
    assert G.GraphHasElement(host, distractor)() is M.truth_value
    print("PASS: enumerated mapping retains rejected alternatives and fires a correctly glued rewrite")
