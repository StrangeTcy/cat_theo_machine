"""Registered composite Nat operations: execution, refusal, tensors, and persistence."""

import os
import tempfile

from hyge import defined_operations as DO
from hyge import labels as L
from hyge import machine as M
from hyge import operation_catalog as OC
from hyge import persistence
from hyge import playground as PG
from hyge import runtime
from hyge import template_matching as TM


class CheckDefinitionRefused(M.Edge):
    def __init__(self, label, formals, body, registry):
        checked = DO.RegisterDefinedNatOperation(label, formals, body, registry)()
        assert M.Head(checked)() is M.false_value
        assert M.Head(M.Tail(checked)())() is registry
        assert M.Head(M.Tail(M.Tail(checked)())())() is M.EmptyList
        super().__init__(inputs=M.Pair(label, M.Pair(formals, body)), results=registry)


class CheckDefinedTensorCells(M.Edge):
    def __init__(self, label, domain, left_axis, right_axis, tensor, registry, operations):
        active = registry
        if M.IsPair(left_axis)() is M.truth_value:
            if M.IsPair(right_axis)() is M.truth_value:
                call = M.Pair(label, M.Pair(M.Head(left_axis)(), M.Pair(M.Head(right_axis)(), M.EmptyList)))
                cached = PG.TensorOperationValue(tensor, call, M.EmptyList, active)()
                assert M.Head(cached)() is not M.EmptyList
                direct = PG.EvaluateNatExpr(call, M.EmptyList, active, operations)()
                active = M.Head(M.Tail(direct)())()
                assert M.NatEq(M.Head(cached)(), M.Head(direct)(), active)() is M.truth_value
                active = CheckDefinedTensorCells(label, domain, left_axis, M.Tail(right_axis)(),
                    tensor, active, operations)()
            else:
                active = CheckDefinedTensorCells(label, domain, M.Tail(left_axis)(), domain,
                    tensor, active, operations)()
        super().__init__(inputs=M.Pair(label, M.Pair(left_axis, right_axis)), results=active)


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
    registry = M.FromContextGetConstructors(rt.graph)()
    original_rules = M.FromContextGetRuleOrder(rt.graph)()
    label = M.Atom()
    a = M.Atom()
    b = M.Atom()
    c = M.Atom()
    d = M.Atom()
    formals = M.Pair(a, M.Pair(b, M.EmptyList))
    square = M.Pair(L.ExprPowLabel, M.Pair(a, M.Pair(M.two, M.EmptyList)))
    body = M.Pair(L.ExprAddLabel, M.Pair(square, M.Pair(b, M.EmptyList)))
    arguments = M.Pair(M.two, M.Pair(M.three, M.EmptyList))
    call = M.Pair(label, arguments)
    before = PG.BuildNatOperationRegister(registry, M.Pair(call, M.EmptyList))()
    assert PG.LookupOperationByLabel(label, M.Head(before)())() is M.EmptyList
    assert M.Head(PG.EvaluateNatExpr(call, M.EmptyList, registry)())() is M.EmptyList
    assert DO.RegisteredDefinedNatOperation(label, registry)() is M.EmptyList
    print("PASS an inert expression and fresh operation label remain unavailable before explicit registration")

    registered = DO.RegisterDefinedNatOperation(label, formals, body, registry)()
    assert M.Head(registered)() is M.truth_value
    registry = M.Head(M.Tail(registered)())()
    descriptor = M.Head(M.Tail(M.Tail(registered)())())()
    assert DO.DefinedBody(body, formals, registry)() is M.truth_value
    definition_key = M.Pair(L.NatOperationCatalogLabel, M.Pair(label, M.EmptyList))
    stored_definition = M.TreeLookup(registry, definition_key, registry)()
    assert PG.ExactArity(stored_definition, M.four, registry)() is M.truth_value
    assert M.IdentityCompare(M.Head(M.Tail(stored_definition)())(), label)() is M.truth_value
    assert DO.DefinedSymbol(label, registry)() is M.truth_value
    assert DO.DefinedFormals(formals, registry)() is M.truth_value
    assert M.Compare(PG.LookupOperationByLabel(label, OC.RegisteredNatOperationCatalog(registry)())(),
        DO.DefinedNatOperationDescription(label, formals)())() is M.truth_value
    assert M.IsPair(DO.RegisteredDefinedNatOperation(label, registry)())() is M.truth_value
    operations = M.Head(PG.BuildNatOperationRegister(registry)())()
    assert M.Compare(PG.LookupOperationByLabel(label, operations)(), descriptor)() is M.truth_value
    assert PG.AdmittedPolynomial(call, M.EmptyList, registry, operations)() is M.false_value
    actual = PG.EvaluateNatExpr(call, M.EmptyList, registry, operations)()
    registry = M.Head(M.Tail(actual)())()
    expected = PG.EvaluateNatExpr(body, PG.ZipEnvironment(formals, arguments)(), registry, operations)()
    registry = M.Head(M.Tail(expected)())()
    print("Composite result:", PG.RenderOperationValue(M.Head(actual)(), registry)(),
        "direct result:", PG.RenderOperationValue(M.Head(expected)(), registry)())
    assert M.NatEq(M.Head(actual)(), M.Head(expected)(), registry)() is M.truth_value
    assert M.NatEq(M.Head(actual)(), M.seven, registry)() is M.truth_value
    swapped = PG.EvaluateNatExpr(M.Pair(label, M.Pair(b, M.Pair(a, M.EmptyList))),
        PG.ZipEnvironment(formals, arguments)(), registry, operations)()
    registry = M.Head(M.Tail(swapped)())()
    direct_swapped = PG.EvaluateNatExpr(body,
        PG.ZipEnvironment(formals, M.Pair(M.three, M.Pair(M.two, M.EmptyList)))(), registry, operations)()
    registry = M.Head(M.Tail(direct_swapped)())()
    assert M.NatEq(M.Head(swapped)(), M.Head(direct_swapped)(), registry)() is M.truth_value
    assert M.NatEq(M.Head(swapped)(), M.Head(actual)(), registry)() is M.false_value
    print("PASS one registered body executes through primitive expansion and binds anonymous formals without capture")

    domain = M.Pair(M.Zero, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
    built = PG.BuildOperationTensorState(domain, M.Pair(descriptor, M.EmptyList), registry, operations)()
    tensor = M.Head(built)()
    registry = M.Head(M.Tail(built)())()
    registry = CheckDefinedTensorCells(label, domain, domain, domain, tensor, registry, operations)()
    print("PASS every cell of the registered operation tensor agrees with direct evaluation")

    four_label = M.Atom()
    four_formals = M.Pair(a, M.Pair(b, M.Pair(c, M.Pair(d, M.EmptyList))))
    sum_left = M.Pair(L.ExprAddLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
    sum_right = M.Pair(L.ExprAddLabel, M.Pair(c, M.Pair(d, M.EmptyList)))
    four_body = M.Pair(L.ExprMulLabel, M.Pair(sum_left, M.Pair(sum_right, M.EmptyList)))
    registered_four = DO.RegisterDefinedNatOperation(four_label, four_formals, four_body, registry)()
    assert M.Head(registered_four)() is M.truth_value
    registry = M.Head(M.Tail(registered_four)())()
    operations = M.Head(PG.BuildNatOperationRegister(registry)())()
    four_call = M.Pair(four_label, M.Pair(M.one, M.Pair(M.two, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))))
    four_value = PG.EvaluateNatExpr(four_call, M.EmptyList, registry, operations)()
    registry = M.Head(M.Tail(four_value)())()
    assert M.NatEq(M.Head(four_value)(), M.nine, registry)() is M.truth_value
    print("PASS explicit formal chains support composite operations beyond builtin unary/binary/ternary dispatch")

    CheckDefinitionRefused(label, formals, body, registry)()
    CheckDefinitionRefused(label, formals, M.one, registry)()
    CheckDefinitionRefused(L.ExprAddLabel, formals, body, registry)()
    CheckDefinitionRefused(L.ExprIntLabel, formals, body, registry)()
    CheckDefinitionRefused(M.Atom(), M.Pair(a, M.Pair(a, M.EmptyList)), body, registry)()
    CheckDefinitionRefused(M.Atom(), M.Pair(a, b), body, registry)()
    CheckDefinitionRefused(M.Atom(), M.EmptyList, body, registry)()
    CheckDefinitionRefused(M.Atom(), formals, c, registry)()
    CheckDefinitionRefused(M.Atom(), formals, M.Pair(L.ExprGcdLabel, formals), registry)()
    CheckDefinitionRefused(M.Atom(), formals, M.Pair(label, formals), registry)()
    CheckDefinitionRefused(M.Atom(), formals, M.Pair(L.ExprPowLabel, formals), registry)()
    CheckDefinitionRefused(M.Atom(), formals, M.Pair(L.ExprAddLabel, M.Pair(a, M.EmptyList)), registry)()
    self_label = M.Atom()
    CheckDefinitionRefused(self_label, formals, M.Pair(self_label, formals), registry)()
    CheckDefinitionRefused(a, formals, body, registry)()
    assert M.Head(PG.EvaluateNatExpr(M.Pair(label, M.Pair(M.one, M.EmptyList)), M.EmptyList, registry, operations)())() is M.EmptyList
    assert M.Head(PG.EvaluateNatExpr(M.Pair(label, M.Pair(M.one, M.Pair(M.two, M.Pair(M.three, M.EmptyList)))),
        M.EmptyList, registry, operations)())() is M.EmptyList
    assert M.Head(PG.EvaluateNatExpr(M.Pair(label, M.Pair(c, M.Pair(M.one, M.EmptyList))),
        M.EmptyList, registry, operations)())() is M.EmptyList
    assert M.Head(PG.EvaluateNatExpr(M.Pair(label, M.Pair(M.truth_value, M.Pair(M.one, M.EmptyList))),
        M.EmptyList, registry, operations)())() is M.EmptyList
    print("PASS duplicate, conflicting, builtin, malformed, unbound, cyclic, unsupported, and wrong-arity definitions or calls are refused")

    key = M.Pair(L.NatOperationCatalogLabel, M.Pair(label, M.EmptyList))
    forged_body = M.Pair(L.ExprGcdLabel, formals)
    forged_record = M.Pair(M.Char("defined-nat-operation-v1"),
        M.Pair(label, M.Pair(formals, M.Pair(forged_body, M.EmptyList))))
    forged_registry = M.TreeInsert(registry, key, forged_record, registry)()
    assert DO.RegisteredDefinedNatOperation(label, forged_registry)() is M.EmptyList
    assert M.Head(PG.EvaluateNatExpr(call, M.EmptyList, forged_registry, operations)())() is M.EmptyList
    empty_registry = M.Tree(M.EmptyList)
    descriptor_only = OC.ExtendNatOperationCatalog(descriptor, empty_registry)()
    assert M.Head(PG.EvaluateNatExpr(call, M.EmptyList, descriptor_only)())() is M.EmptyList
    empty_template = M.Pair(L.AlgebraicTemplateLabel,
        M.Pair(domain, M.Pair(M.Pair(descriptor, M.EmptyList), M.Pair(M.EmptyList, M.EmptyList))))
    finite = TM.CheckFiniteTemplate(empty_template, formals, M.Pair(label, formals), domain, registry)()
    assert M.Head(M.Tail(M.Tail(M.Head(finite)())())())() is M.false_value
    source_domain = M.Pair(M.one, M.EmptyList)
    power_left = M.Pair(L.ExprPowLabel, formals)
    power_right = M.Pair(L.ExprPowLabel, M.Pair(b, M.Pair(a, M.EmptyList)))
    equation = M.Pair(L.DiscoveredEquationLabel,
        M.Pair(formals, M.Pair(power_left, M.Pair(power_right, M.EmptyList))))
    requirement = M.Pair(L.NamedRegularityLabel, M.Pair(M.Char("finite exchange"),
        M.Pair(M.Char("pow"), M.Pair(equation, M.Pair(source_domain, M.Pair(M.EmptyList, M.EmptyList))))))
    builtin_template = M.Pair(L.AlgebraicTemplateLabel,
        M.Pair(source_domain, M.Pair(operations, M.Pair(M.Pair(requirement, M.EmptyList), M.EmptyList))))
    finite = TM.CheckFiniteTemplate(builtin_template, formals, M.Pair(L.ExprGcdLabel, formals), domain, registry)()
    assert M.Head(M.Tail(M.Tail(M.Head(finite)())())())() is M.truth_value
    finite = TM.CheckFiniteTemplate(builtin_template, formals, M.Pair(label, formals), domain, registry)()
    assert M.Head(M.Tail(M.Tail(M.Head(finite)())())())() is M.false_value
    print("PASS forged bodies and descriptor-only entries cannot execute; custom finite template roles receive no authority")

    rt.graph._replace_context(constructors=registry)
    saved_catalog_label = L.NatOperationCatalogLabel
    scope = M.Pair(M.Char("defined-operation-snapshot-check"), M.Pair(label, M.Pair(call, M.EmptyList)))
    rt.graph.add_node(scope)
    assert M.FromContextGetRuleOrder(rt.graph)() is original_rules
    codec = persistence.SnapshotCodec(persistence._runtime_namespace_for_restore())
    with tempfile.TemporaryDirectory(prefix="hyge-defined-operation-") as snapshot_directory:
        snapshot_path = os.path.join(snapshot_directory, "registered-operation.json")
        codec.save(rt.graph, snapshot_path)
        restored = codec.load(snapshot_path)
        loaded_registry = codec._restore_tree_root(restored, "constructor_registry", registry)
        resumed = runtime.make_fresh_runtime()
        codec.activate(restored, resumed.graph)
    restored_scope = M.Head(M.FromContextGetNodes(resumed.graph)())()
    restored_label = M.Head(M.Tail(restored_scope)())()
    restored_call = M.Head(M.Tail(M.Tail(restored_scope)())())()
    restored_registry = M.FromContextGetConstructors(resumed.graph)()
    assert M.IdentityCompare(restored_label, restored_label)() is M.truth_value
    assert M.IdentityCompare(saved_catalog_label, L.NatOperationCatalogLabel)() is M.truth_value
    assert M.IdentityCompare(loaded_registry, restored_registry)() is M.truth_value
    restored_definition = M.TreeLookup(restored_registry,
        M.Pair(L.NatOperationCatalogLabel, M.Pair(restored_label, M.EmptyList)), restored_registry)()
    assert PG.ExactArity(restored_definition, M.four, restored_registry)() is M.truth_value
    restored_formals = M.Head(M.Tail(M.Tail(restored_definition)())())()
    restored_body = M.Head(M.Tail(M.Tail(M.Tail(restored_definition)())())())()
    assert DO.DefinedSymbol(restored_label, restored_registry)() is M.truth_value
    assert DO.DefinedFormals(restored_formals, restored_registry)() is M.truth_value
    assert DO.DefinedBody(restored_body, restored_formals, restored_registry)() is M.truth_value
    assert M.Compare(PG.LookupOperationByLabel(restored_label, OC.RegisteredNatOperationCatalog(restored_registry)())(),
        DO.DefinedNatOperationDescription(restored_label, restored_formals)())() is M.truth_value
    assert M.IsPair(DO.RegisteredDefinedNatOperation(restored_label, restored_registry)())() is M.truth_value
    restored_result = PG.EvaluateNatExpr(restored_call, M.EmptyList, restored_registry)()
    restored_registry = M.Head(M.Tail(restored_result)())()
    assert M.NatEq(M.Head(restored_result)(), M.seven, restored_registry)() is M.truth_value
    assert M.FromContextGetRuleOrder(resumed.graph)() is M.EmptyList
    print("PASS file-backed snapshot restoration retains the definition, opaque label, and executable behavior without graph rules")
    print("Defined operation regressions passed.")
