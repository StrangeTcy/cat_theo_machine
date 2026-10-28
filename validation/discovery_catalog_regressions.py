"""Operation availability follows registered machine evidence."""

from hyge import labels as L
from hyge import machine as M
from hyge import operation_catalog as OC
from hyge import playground as PG
from hyge.persistence import SnapshotCodec, _runtime_namespace_for_restore
from hyge.runtime import make_fresh_runtime


runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
empty_registry = M.Tree(M.EmptyList)
empty = PG.BuildNatOperationRegister(empty_registry)()
assert M.Head(empty)() is M.EmptyList
assert M.Head(M.Tail(empty)())() is empty_registry

x = M.Char("x")
y = M.Char("y")
addition = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
addition_only = M.Head(PG.BuildNatOperationRegister(
    empty_registry, M.Pair(addition, M.EmptyList),
)())()
assert M.Tail(addition_only)() is M.EmptyList
assert M.Compare(M.Head(addition_only)(), OC.NatOperationDescription(L.ExprAddLabel)())() is M.truth_value
assert PG.LookupOperationByLabel(L.ExprGcdLabel, addition_only)() is M.EmptyList

operations = M.Head(PG.BuildNatOperationRegister(registry)())()
stored = OC.RegisteredNatOperationCatalog(registry)()
assert operations is stored
count = M.Count(operations, registry)()
fifteen = M.NatFromRep(M.GMPRep(15), M.Head(M.Tail(count)())())()
assert M.NatEq(M.Head(count)(), M.Head(fifteen)(), M.Head(M.Tail(fifteen)())())() is M.truth_value
assert OC.RegisterNatOperationCatalog(registry)() is registry
assert PG.LookupOperationByLabel(L.NatModEqLabel, operations)() is not M.EmptyList
assert PG.LookupOperationByLabel(L.DividesLabel, operations)() is not M.EmptyList
assert PG.LookupOperationByLabel(L.ImpliesLabel, operations)() is not M.EmptyList

# Explicit constructor evidence is read independently of its arity.
unary_evidence = M.ConstructedBy(
    M.Atom(), L.ExprNegLabel, M.Pair(M.one, M.EmptyList), empty_registry,
)()
unary_registry = M.Head(M.Tail(unary_evidence)())()
unary_operations = M.Head(PG.BuildNatOperationRegister(unary_registry)())()
assert M.Tail(unary_operations)() is M.EmptyList
assert PG.LookupOperationByLabel(L.ExprNegLabel, unary_operations)() is not M.EmptyList

ternary_evidence = M.ConstructedBy(
    M.Atom(), L.NatModEqLabel,
    M.Pair(M.one, M.Pair(M.two, M.Pair(M.one, M.EmptyList))), empty_registry,
)()
ternary_registry = M.Head(M.Tail(ternary_evidence)())()
ternary_operations = M.Head(PG.BuildNatOperationRegister(ternary_registry)())()
assert M.Tail(ternary_operations)() is M.EmptyList
assert PG.LookupOperationByLabel(L.NatModEqLabel, ternary_operations)() is not M.EmptyList

# The catalog crosses the existing snapshot codec as ordinary machine terms.
codec = SnapshotCodec(_runtime_namespace_for_restore())
state = codec.load_snapshot(codec.capture(runtime.graph))
restored_registry = codec._restore_tree_root(state, "constructor_registry", registry)
restored = OC.RegisteredNatOperationCatalog(restored_registry)()
assert M.Compare(restored, stored)() is M.truth_value
assert OC.RegisterNatOperationCatalog(restored_registry)() is restored_registry
assert M.Compare(M.Head(PG.BuildNatOperationRegister(restored_registry)())(), stored)() is M.truth_value

print("Operation catalog regressions passed.")
