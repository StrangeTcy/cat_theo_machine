"""Exercise interface gluing, graph identity, and refusal without mutation."""

from hyge import machine as M
from hyge import graph as G
from hyge import labels as L


empty = M.EmptyList
kind = M.Char("edge")
k_node = M.Thingy()
left_node = M.Thingy()
right_node = M.Thingy()
created_node = M.Thingy()
host_node = M.Thingy()
left = G.GraphVersion(M.Pair(left_node, empty), empty, empty)()
interface = G.GraphVersion(M.Pair(k_node, empty), empty, empty)()
right_edge = M.Pair(kind, M.Pair(right_node, M.Pair(created_node, empty)))
right = G.GraphVersion(
    M.Pair(right_node, M.Pair(created_node, empty)), M.Pair(right_edge, empty), empty,
)()
k_left = G.Map(interface, left, M.Pair(G.Send(k_node, left_node)(), empty))()
k_right = G.Map(interface, right, M.Pair(G.Send(k_node, right_node)(), empty))()
law = G.Law(left, interface, right, k_left, k_right, empty)()
host = G.GraphVersion(M.Pair(host_node, empty), empty, empty)()
mapping = G.Map(left, host, M.Pair(G.Send(left_node, host_node)(), empty))()
firing = G.FireLaw(host, law, mapping, G.DanglingForbid()())()
result = M.Head(firing)()
assert result is not empty, "valid interface rewrite was refused"
inserted_edge = M.Head(G.GraphEdges(result)())()
assert M.Head(G.EdgeEndpoints(inserted_edge)())() is host_node, "inserted edge retained the rule endpoint instead of the host endpoint"
assert M.Head(M.Tail(G.EdgeEndpoints(inserted_edge)())())() is created_node
assert inserted_edge is not right_edge, "insertion reused the rule edge object"
assert G.GraphNodes(host)() is M.Head(M.Tail(host)())()
assert M.Tail(G.GraphNodes(host)())() is empty
assert G.GraphEdges(host)() is empty
assert M.Head(G.EdgeEndpoints(right_edge)())() is right_node
assert M.Head(G.GraphEdges(right)())() is right_edge
print("PASS: distinct K/L/R/host identities are glued; old graph and rule stay unchanged")

# Replaying over the original snapshot creates a separate inserted edge.
again = M.Head(G.FireLaw(host, law, mapping, G.DanglingForbid()())())()
assert M.Head(G.GraphEdges(again)())() is not inserted_edge
# R\K nodes currently name explicit admissions. Reusing one within a host
# must be refused instead of silently inserting the same graph node twice.
next_mapping = G.Map(left, result, M.Pair(G.Send(left_node, host_node)(), empty))()
collision = G.FireLaw(result, law, next_mapping, G.DanglingForbid()())()
assert M.Head(collision)() is empty
print("PASS: repeated insertion cannot duplicate an admitted node")

# A graph element's identity controls membership, removal, and boundaries.
node_shape = M.Char("same-node-shape")
distinct_a = M.Pair(node_shape, empty)
distinct_b = M.Pair(node_shape, empty)
assert M.TermEqual(distinct_a, distinct_b)() is M.truth_value
kept = G.ChainWithout(M.Pair(distinct_a, M.Pair(distinct_b, empty)), M.Pair(distinct_a, empty))()
assert M.Head(kept)() is distinct_b
assert M.Tail(kept)() is empty
touches_b = M.Pair(kind, M.Pair(distinct_b, empty))
distinct_host = G.GraphVersion(
    M.Pair(distinct_a, M.Pair(distinct_b, empty)), M.Pair(touches_b, empty), empty,
)()
assert G.DanglingEdges(distinct_host, M.Pair(distinct_a, empty))() is empty
assert M.Head(G.DanglingEdges(distinct_host, M.Pair(distinct_b, empty))())() is touches_b
print("PASS: structurally equal nodes remain distinct during deletion and boundary scans")

# A preserved interface edge is reused by identity and is available as an
# explicit endpoint to an inserted edge.
k_edge = M.Pair(kind, M.Pair(k_node, empty))
left_edge = M.Pair(kind, M.Pair(left_node, empty))
kept_right_edge = M.Pair(kind, M.Pair(right_node, empty))
kept_host_edge = M.Pair(kind, M.Pair(host_node, empty))
shared_interface = G.GraphVersion(M.Pair(k_node, empty), M.Pair(k_edge, empty), empty)()
shared_left = G.GraphVersion(M.Pair(left_node, empty), M.Pair(left_edge, empty), empty)()
new_shared_edge = M.Pair(kind, M.Pair(kept_right_edge, M.Pair(right_node, empty)))
shared_right = G.GraphVersion(
    M.Pair(right_node, empty), M.Pair(kept_right_edge, M.Pair(new_shared_edge, empty)), empty,
)()
shared_host = G.GraphVersion(M.Pair(host_node, empty), M.Pair(kept_host_edge, empty), empty)()
shared_k_left = G.Map(shared_interface, shared_left,
    M.Pair(G.Send(k_node, left_node)(), M.Pair(G.Send(k_edge, left_edge)(), empty)))()
shared_k_right = G.Map(shared_interface, shared_right,
    M.Pair(G.Send(k_node, right_node)(), M.Pair(G.Send(k_edge, kept_right_edge)(), empty)))()
shared_law = G.Law(shared_left, shared_interface, shared_right, shared_k_left, shared_k_right, empty)()
shared_mapping = G.Map(shared_left, shared_host,
    M.Pair(G.Send(left_node, host_node)(), M.Pair(G.Send(left_edge, kept_host_edge)(), empty)))()
shared_result = M.Head(G.FireLaw(shared_host, shared_law, shared_mapping, G.DanglingForbid()())())()
assert shared_result is not empty
shared_insert = M.Head(G.GraphEdges(shared_result)())()
assert M.Head(G.EdgeEndpoints(shared_insert)())() is kept_host_edge
assert M.Head(M.Tail(G.EdgeEndpoints(shared_insert)())())() is host_node
assert M.Head(M.Tail(G.GraphEdges(shared_result)())())() is kept_host_edge
assert M.Tail(M.Tail(G.GraphEdges(shared_result)())())() is empty
print("PASS: a preserved interface edge remains shared and usable as an endpoint")

# The same-shaped host is not the particular host certified by a mapping.
other_host = G.GraphVersion(M.Pair(host_node, empty), empty, empty)()
assert M.Head(G.FireLaw(other_host, law, mapping, G.DanglingForbid()())())() is empty
assert M.Head(G.FireLaw(host, law, mapping, M.Char("unknown-mode"))())() is empty
missing_node = M.Thingy()
unbound_edge = M.Pair(kind, M.Pair(right_node, M.Pair(missing_node, empty)))
malformed_right = G.GraphVersion(M.Pair(right_node, empty), M.Pair(unbound_edge, empty), empty)()
malformed_k_right = G.Map(interface, malformed_right, M.Pair(G.Send(k_node, right_node)(), empty))()
malformed_law = G.Law(left, interface, malformed_right, k_left, malformed_k_right, empty)()
assert M.Head(G.FireLaw(host, malformed_law, mapping, G.DanglingForbid()())())() is empty
unsupported = G.Law(left, interface, right, k_left, k_right,
    M.Pair(G.KObligation(M.Char("unproved"), left_node)(), empty))()
assert M.Head(G.FireLaw(host, unsupported, mapping, G.DanglingForbid()())())() is empty
print("PASS: stale host scope, unknown dangling policy, and unbound endpoints are refused")

# Deleting a node distinguishes forbid from an explicitly selected sweep.
delete_left = G.GraphVersion(M.Pair(left_node, empty), empty, empty)()
delete_interface = G.GraphVersion(empty, empty, empty)()
delete_right = G.GraphVersion(empty, empty, empty)()
delete_k_left = G.Map(delete_interface, delete_left, empty)()
delete_k_right = G.Map(delete_interface, delete_right, empty)()
delete_law = G.Law(delete_left, delete_interface, delete_right, delete_k_left, delete_k_right, empty)()
outside = M.Thingy()
stranded_edge = M.Pair(kind, M.Pair(host_node, M.Pair(outside, empty)))
delete_host = G.GraphVersion(M.Pair(host_node, M.Pair(outside, empty)), M.Pair(stranded_edge, empty), empty)()
delete_mapping = G.Map(delete_left, delete_host, M.Pair(G.Send(left_node, host_node)(), empty))()
assert M.Head(G.FireLaw(delete_host, delete_law, delete_mapping, G.DanglingForbid()())())() is empty
deleted = M.Head(G.FireLaw(delete_host, delete_law, delete_mapping, G.DanglingDelete()())())()
assert deleted is not empty
assert M.Head(G.GraphNodes(deleted)())() is outside
assert M.Tail(G.GraphNodes(deleted)())() is empty
assert G.GraphEdges(deleted)() is empty
assert M.Head(G.GraphEdges(delete_host)())() is stranded_edge
print("PASS: dangling refusal and explicit deletion preserve the old snapshot")

# An edge can itself be an endpoint, so an explicit sweep must follow the
# whole dependency chain rather than leave an edge attached to a removed edge.
dependent_edge = M.Pair(kind, M.Pair(stranded_edge, empty))
dependent_host = G.GraphVersion(
    M.Pair(host_node, M.Pair(outside, empty)),
    M.Pair(stranded_edge, M.Pair(dependent_edge, empty)), empty,
)()
dependent_mapping = G.Map(delete_left, dependent_host, M.Pair(G.Send(left_node, host_node)(), empty))()
dependent_result = M.Head(G.FireLaw(dependent_host, delete_law, dependent_mapping, G.DanglingDelete()())())()
assert dependent_result is not empty
assert G.GraphEdges(dependent_result)() is empty
assert M.Head(M.Tail(G.GraphEdges(dependent_host)())())() is dependent_edge
print("PASS: deletion closes over dependent edges and unproved obligations cannot fire")

# An empty pattern still requires a well-formed host store.
empty_graph = G.GraphVersion(empty, empty, empty)()
empty_map = G.Map(empty_graph, empty_graph, empty)()
empty_law = G.Law(empty_graph, empty_graph, empty_graph, empty_map, empty_map, empty)()
broken_store = G.GraphVersion(M.Atom(), empty, empty)()
broken_mapping = G.Map(empty_graph, broken_store, empty)()
assert M.Head(G.FireLaw(broken_store, empty_law, broken_mapping, G.DanglingForbid()())())() is empty
improper_store = G.GraphVersion(M.Pair(host_node, M.Atom()), empty, empty)()
improper_mapping = G.Map(empty_graph, improper_store, empty)()
assert M.Head(G.FireLaw(improper_store, empty_law, improper_mapping, G.DanglingForbid()())())() is empty

# An interface edge cannot refer outside its own interface, even when a
# partial endpoint matcher would otherwise find no commitment to contradict.
outside_k = M.Thingy()
orphan_k_edge = M.Pair(kind, M.Pair(outside_k, empty))
orphan_interface = G.GraphVersion(empty, M.Pair(orphan_k_edge, empty), empty)()
orphan_left_map = G.Map(orphan_interface, shared_left, M.Pair(G.Send(orphan_k_edge, left_edge)(), empty))()
orphan_right_map = G.Map(orphan_interface, shared_right, M.Pair(G.Send(orphan_k_edge, kept_right_edge)(), empty))()
orphan_law = G.Law(shared_left, orphan_interface, shared_right, orphan_left_map, orphan_right_map, empty)()
assert M.Head(G.FireLaw(shared_host, orphan_law, shared_mapping, G.DanglingForbid()())())() is empty
print("PASS: malformed stores and interface incidence cannot authorize surgery")

print("Graph surgery regressions passed.")
