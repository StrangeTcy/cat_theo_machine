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

print("Graph edge dependency regressions passed.")
