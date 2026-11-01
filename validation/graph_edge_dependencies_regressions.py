"""Insertion resolves new edge dependencies without declaration-order effects."""

from hyge import machine as M
from hyge import graph as G
from hyge import labels as L


empty = M.EmptyList
kind = M.Char("dependent-edge")
k_node = M.Thingy()
left_node = M.Thingy()
right_node = M.Thingy()
host_node = M.Thingy()
interface = G.GraphVersion(M.Pair(k_node, empty), empty, empty)()
left = G.GraphVersion(M.Pair(left_node, empty), empty, empty)()
host = G.GraphVersion(M.Pair(host_node, empty), empty, empty)()
first_edge = M.Pair(kind, M.Pair(right_node, empty))
second_edge = M.Pair(kind, M.Pair(first_edge, empty))
third_edge = M.Pair(kind, M.Pair(second_edge, M.Pair(first_edge, M.Pair(right_node, empty))))
reverse_order = M.Pair(third_edge, M.Pair(second_edge, M.Pair(first_edge, empty)))
right = G.GraphVersion(M.Pair(right_node, empty), reverse_order, empty)()
k_left = G.Map(interface, left, M.Pair(G.Send(k_node, left_node)(), empty))()
k_right = G.Map(interface, right, M.Pair(G.Send(k_node, right_node)(), empty))()
mapping = G.Map(left, host, M.Pair(G.Send(left_node, host_node)(), empty))()
law = G.Law(left, interface, right, k_left, k_right, empty)()
fired = G.FireLaw(host, law, mapping, G.DanglingForbid()())()
result = M.Head(fired)()
assert result is not empty, "new-edge dependencies were refused despite a finite acyclic construction"
result_edges = G.GraphEdges(result)()
new_third = M.Head(result_edges)()
new_second = M.Head(M.Tail(result_edges)())()
new_first = M.Head(M.Tail(M.Tail(result_edges)())())()
assert M.Tail(M.Tail(M.Tail(result_edges)())())() is empty
assert M.Head(G.EdgeEndpoints(new_third)())() is new_second
assert M.Head(M.Tail(G.EdgeEndpoints(new_third)())())() is new_first
assert M.Head(M.Tail(M.Tail(G.EdgeEndpoints(new_third)())())())() is host_node
assert M.Head(G.EdgeEndpoints(new_second)())() is new_first
assert M.Head(G.EdgeEndpoints(new_first)())() is host_node
assert new_first is not first_edge
assert new_second is not second_edge
assert new_third is not third_edge
assert G.SurgeryGraphValid(result)() is M.truth_value
assert G.GraphEdges(host)() is empty
assert G.GraphEdges(right)() is reverse_order
assert M.Head(G.EdgeEndpoints(second_edge)())() is first_edge
print("PASS reversed three-edge dependency chain preserves sharing and R order")

trace = M.Head(M.Tail(fired)())()
insertion = M.Head(M.Tail(M.Tail(M.Tail(trace)())())())()
assert M.Head(insertion)() is L.InsertionPreparedLabel
bindings = M.Head(M.Tail(M.Tail(M.Tail(insertion)())())())()
assert M.Tail(G.MappedHostForPat(bindings, first_edge)())() is new_first
assert M.Tail(G.MappedHostForPat(bindings, second_edge)())() is new_second
assert M.Tail(G.MappedHostForPat(bindings, third_edge)())() is new_third
print("PASS insertion provenance binds every source edge to its fresh result")

again = M.Head(G.FireLaw(host, law, mapping, G.DanglingForbid()())())()
again_edges = G.GraphEdges(again)()
again_third = M.Head(again_edges)()
again_second = M.Head(M.Tail(again_edges)())()
again_first = M.Head(M.Tail(M.Tail(again_edges)())())()
assert again_third is not new_third
assert again_second is not new_second
assert again_first is not new_first
assert M.Head(G.EdgeEndpoints(again_third)())() is again_second
assert M.Head(G.EdgeEndpoints(again_second)())() is again_first
assert M.Head(G.EdgeEndpoints(again_first)())() is host_node
print("PASS separate firings allocate separate edges with shared internal dependencies")

forward_order = M.Pair(first_edge, M.Pair(second_edge, M.Pair(third_edge, empty)))
forward_right = G.GraphVersion(M.Pair(right_node, empty), forward_order, empty)()
forward_k = G.Map(interface, forward_right, M.Pair(G.Send(k_node, right_node)(), empty))()
forward_law = G.Law(left, interface, forward_right, k_left, forward_k, empty)()
forward_result = M.Head(G.FireLaw(host, forward_law, mapping, G.DanglingForbid()())())()
assert forward_result is not empty
forward_edges = G.GraphEdges(forward_result)()
forward_first = M.Head(forward_edges)()
forward_second = M.Head(M.Tail(forward_edges)())()
forward_third = M.Head(M.Tail(M.Tail(forward_edges)())())()
assert M.Head(G.EdgeEndpoints(forward_second)())() is forward_first
assert M.Head(G.EdgeEndpoints(forward_third)())() is forward_second
assert M.Head(M.Tail(G.EdgeEndpoints(forward_third)())())() is forward_first
assert G.SurgeryGraphValid(forward_result)() is M.truth_value
print("PASS forward and reverse declaration orders both resolve")

missing = M.Thingy()
blocked_edge = M.Pair(kind, M.Pair(missing, empty))
initial_bindings = M.Pair(G.Send(right_node, host_node)(), empty)
blocked = G.GluedInsertionEdges(M.Pair(first_edge, M.Pair(blocked_edge, empty)), initial_bindings)()
assert M.Head(blocked)() is M.false_value
assert M.Tail(blocked)() is empty
assert M.Tail(initial_bindings)() is empty
assert M.Head(G.EdgeEndpoints(first_edge)())() is right_node
assert M.Head(G.EdgeEndpoints(blocked_edge)())() is missing
assert G.GraphEdges(host)() is empty
print("PASS a stalled dependency remainder refuses the whole insertion without partial output")

# Populate the cyclic fixture through the primitive Atom's mutable value slot.
# The rewrite operation must leave those slots untouched.
cycle_first = M.Pair(kind, empty)
cycle_second = M.Pair(kind, M.Pair(cycle_first, empty))
cycle_first.tail.value = M.Pair(cycle_second, empty)
cycle_order = M.Pair(first_edge, M.Pair(cycle_second, M.Pair(cycle_first, empty)))
cycle_right = G.GraphVersion(M.Pair(right_node, empty), cycle_order, empty)()
assert G.SurgeryGraphValid(cycle_right)() is M.truth_value
cycle_k = G.Map(interface, cycle_right, M.Pair(G.Send(k_node, right_node)(), empty))()
cycle_law = G.Law(left, interface, cycle_right, k_left, cycle_k, empty)()
cycle_firing = G.FireLaw(host, cycle_law, mapping, G.DanglingForbid()())()
assert M.Head(cycle_firing)() is empty
assert G.GraphEdges(host)() is empty
assert G.GraphEdges(cycle_right)() is cycle_order
assert M.Head(G.EdgeEndpoints(cycle_first)())() is cycle_second
assert M.Head(G.EdgeEndpoints(cycle_second)())() is cycle_first
cycle_result = G.GluedInsertionEdges(cycle_order, initial_bindings)()
assert M.Head(cycle_result)() is M.false_value
assert M.Tail(cycle_result)() is empty
self_edge = M.Pair(kind, empty)
self_edge.tail.value = M.Pair(self_edge, empty)
self_result = G.GluedInsertionEdges(M.Pair(self_edge, empty), initial_bindings)()
assert M.Head(self_result)() is M.false_value
assert M.Tail(self_result)() is empty
print("PASS two-edge and self cycles terminate with refusal, including after an independent edge resolves")

k_edge = M.Pair(kind, M.Pair(k_node, empty))
left_edge = M.Pair(kind, M.Pair(left_node, empty))
right_kept = M.Pair(kind, M.Pair(right_node, empty))
host_kept = M.Pair(kind, M.Pair(host_node, empty))
kept_interface = G.GraphVersion(M.Pair(k_node, empty), M.Pair(k_edge, empty), empty)()
kept_left = G.GraphVersion(M.Pair(left_node, empty), M.Pair(left_edge, empty), empty)()
kept_host = G.GraphVersion(M.Pair(host_node, empty), M.Pair(host_kept, empty), empty)()
kept_first = M.Pair(kind, M.Pair(right_kept, empty))
kept_second = M.Pair(kind, M.Pair(kept_first, M.Pair(right_kept, empty)))
kept_right = G.GraphVersion(M.Pair(right_node, empty),
    M.Pair(kept_second, M.Pair(right_kept, M.Pair(kept_first, empty))), empty)()
kept_k_left = G.Map(kept_interface, kept_left,
    M.Pair(G.Send(k_node, left_node)(), M.Pair(G.Send(k_edge, left_edge)(), empty)))()
kept_k_right = G.Map(kept_interface, kept_right,
    M.Pair(G.Send(k_node, right_node)(), M.Pair(G.Send(k_edge, right_kept)(), empty)))()
kept_mapping = G.Map(kept_left, kept_host,
    M.Pair(G.Send(left_node, host_node)(), M.Pair(G.Send(left_edge, host_kept)(), empty)))()
kept_law = G.Law(kept_left, kept_interface, kept_right, kept_k_left, kept_k_right, empty)()
kept_result = M.Head(G.FireLaw(kept_host, kept_law, kept_mapping, G.DanglingForbid()())())()
assert kept_result is not empty
kept_edges = G.GraphEdges(kept_result)()
kept_new_second = M.Head(kept_edges)()
kept_new_first = M.Head(M.Tail(kept_edges)())()
assert M.Head(G.EdgeEndpoints(kept_new_second)())() is kept_new_first
assert M.Head(M.Tail(G.EdgeEndpoints(kept_new_second)())())() is host_kept
assert M.Head(G.EdgeEndpoints(kept_new_first)())() is host_kept
assert M.Head(M.Tail(M.Tail(kept_edges)())())() is host_kept
assert M.Tail(M.Tail(M.Tail(kept_edges)())())() is empty
assert G.SurgeryGraphValid(kept_result)() is M.truth_value
assert M.Head(G.GraphEdges(kept_host)())() is host_kept
assert M.Tail(G.GraphEdges(kept_host)())() is empty
print("PASS new-edge dependencies preserve K edge identity and the host snapshot")

duplicate_result = G.GluedInsertionEdges(M.Pair(first_edge, M.Pair(first_edge, empty)), initial_bindings)()
assert M.Head(duplicate_result)() is M.false_value
assert M.Tail(duplicate_result)() is empty
malformed_result = G.GluedInsertionEdges(M.Pair(first_edge, M.Thingy()), initial_bindings)()
assert M.Head(malformed_result)() is M.false_value
assert M.Tail(malformed_result)() is empty
bound_result = G.GluedInsertionEdges(M.Pair(first_edge, empty),
    M.Pair(G.Send(first_edge, new_first)(), initial_bindings))()
assert M.Head(bound_result)() is M.false_value
assert M.Tail(bound_result)() is empty
print("PASS duplicate, malformed, and prebound insertion sources are refused")

print("Graph edge dependency regressions passed.")
