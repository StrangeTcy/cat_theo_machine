"""Composition of registered definitions with frozen primitive expansion."""

import os
import tempfile

from hyge import machine as M
from hyge import defined_operations as DO
from hyge import labels as L
from hyge import operation_catalog as OC
from hyge import persistence
from hyge import playground as PG
from hyge import runtime
from hyge.validation.defined_operation_regressions import CheckDefinedTensorCells, CheckDefinitionRefused


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
    registry = M.FromContextGetConstructors(rt.graph)()
    f = M.Atom()
    f_arg = M.Atom()
    f_formals = M.Pair(f_arg, M.EmptyList)
    square = M.Pair(L.ExprPowLabel, M.Pair(f_arg, M.Pair(M.two, M.EmptyList)))
    f_body = M.Pair(L.ExprAddLabel, M.Pair(square, M.Pair(M.one, M.EmptyList)))
    registered = DO.RegisterDefinedNatOperation(f, f_formals, f_body, registry)()
    assert M.Head(registered)() is M.truth_value
    registry = M.Head(M.Tail(registered)())()
    g = M.Atom()
    x = M.Atom()
    y = M.Atom()
    formals = M.Pair(x, M.Pair(y, M.EmptyList))
    f_call = M.Pair(f, M.Pair(x, M.EmptyList))
    source = M.Pair(L.ExprMulLabel, M.Pair(f_call, M.Pair(y, M.EmptyList)))
    composed = DO.RegisterDefinedNatOperation(g, formals, source, registry)()
    assert M.Head(composed)() is M.truth_value, "an operation cannot yet depend on an earlier registered definition"
    registry = M.Head(M.Tail(composed)())()
    g_descriptor = M.Head(M.Tail(M.Tail(composed)())())()
    f_record = DO.RegisteredDefinedNatOperation(f, registry)()
    g_record = DO.RegisteredDefinedNatOperation(g, registry)()
    assert PG.ExactArity(f_record, M.four, registry)() is M.truth_value
    assert PG.ExactArity(g_record, M.six, registry)() is M.truth_value
    assert M.Compare(M.Head(g_record)(), M.Char("defined-nat-operation-v2"))() is M.truth_value
    g_expansion = DO.DefinedOperationExpansion(g_record)()
    assert DO.DefinedBody(g_expansion, formals, registry)() is M.truth_value
    dependencies = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(g_record)())())())())())()
    assert M.Head(dependencies)() is f_record
    assert M.Tail(dependencies)() is M.EmptyList
    executable = DO.ExecutableNatOperationDescriptor(g, registry)()
    assert M.Compare(M.Head(executable)(), g_descriptor)() is M.truth_value
    assert M.Head(M.Tail(executable)())() is g_record
    builtin = DO.ExecutableNatOperationDescriptor(L.ExprMulLabel, registry)()
    assert M.Compare(M.Head(builtin)(), OC.NatOperationDescription(L.ExprMulLabel)())() is M.truth_value
    assert M.Head(M.Tail(builtin)())() is M.EmptyList
    assert M.Head(DO.ExecutableNatOperationDescriptor(M.Atom(), registry)())() is M.EmptyList
    operations = M.Head(PG.BuildNatOperationRegister(registry)())()
    call = M.Pair(g, M.Pair(M.two, M.Pair(M.three, M.EmptyList)))
    actual = PG.EvaluateNatExpr(call, M.EmptyList, registry, operations)()
    registry = M.Head(M.Tail(actual)())()
    expected = PG.EvaluateNatExpr(g_expansion,
        PG.ZipEnvironment(formals, M.Tail(call)())(), registry, operations)()
    registry = M.Head(M.Tail(expected)())()
    assert M.NatEq(M.Head(actual)(), M.Head(expected)(), registry)() is M.truth_value
    assert PG.RenderOperationValue(M.Head(actual)(), registry)() == "15"
    assert PG.AdmittedPolynomial(call, M.EmptyList, registry, operations)() is M.false_value
    print("PASS g(x,y)=f(x)*y, f(x)=x^2+1 gives g(2,3)=15 through a pinned primitive expansion")

    h = M.Atom()
    h_formals = M.Pair(f_arg, M.Pair(y, M.EmptyList))
    h_source = M.Pair(L.ExprMulLabel,
        M.Pair(M.Pair(f, M.Pair(y, M.EmptyList)), M.Pair(f_arg, M.EmptyList)))
    capture = DO.RegisterDefinedNatOperation(h, h_formals, h_source, registry)()
    assert M.Head(capture)() is M.truth_value
    registry = M.Head(M.Tail(capture)())()
    operations = M.Head(PG.BuildNatOperationRegister(registry)())()
    h_call = M.Pair(h, M.Pair(M.three, M.Pair(M.two, M.EmptyList)))
    captured = PG.EvaluateNatExpr(h_call, M.EmptyList, registry, operations)()
    registry = M.Head(M.Tail(captured)())()
    assert M.NatEq(M.Head(captured)(), M.Head(actual)(), registry)() is M.truth_value
    print("PASS overlapping formal identities across definitions do not capture substituted arguments")

    k = M.Atom()
    k_source = M.Pair(L.ExprAddLabel, M.Pair(M.Pair(g, formals),
        M.Pair(M.Pair(f, M.Pair(y, M.EmptyList)), M.EmptyList)))
    nested = DO.RegisterDefinedNatOperation(k, formals, k_source, registry)()
    assert M.Head(nested)() is M.truth_value
    registry = M.Head(M.Tail(nested)())()
    operations = M.Head(PG.BuildNatOperationRegister(registry)())()
    k_call = M.Pair(k, M.Tail(call)())
    nested_value = PG.EvaluateNatExpr(k_call, M.EmptyList, registry, operations)()
    registry = M.Head(M.Tail(nested_value)())()
    assert PG.RenderOperationValue(M.Head(nested_value)(), registry)() == "25"
    print("PASS a third definition composes multiple dependencies and evaluates k(2,3)=25")

    domain = M.Pair(M.Zero, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
    built = PG.BuildOperationTensorState(domain, M.Pair(g_descriptor, M.EmptyList), registry, operations)()
    registry = M.Head(M.Tail(built)())()
    registry = CheckDefinedTensorCells(g, domain, domain, domain, M.Head(built)(), registry, operations)()
    print("PASS all nine composed-operation tensor cells agree with direct execution")

    CheckDefinitionRefused(g, formals, source, registry)()
    CheckDefinitionRefused(M.Atom(), formals, M.Pair(f, formals), registry)()
    CheckDefinitionRefused(M.Atom(), formals, M.Pair(f, M.Pair(M.Atom(), M.EmptyList)), registry)()
    CheckDefinitionRefused(M.Atom(), formals, M.Pair(M.Atom(), formals), registry)()
    self_label = M.Atom()
    CheckDefinitionRefused(self_label, formals, M.Pair(self_label, formals), registry)()
    wrong_call = M.Pair(g, M.Pair(M.two, M.EmptyList))
    assert M.Head(PG.EvaluateNatExpr(wrong_call, M.EmptyList, registry, operations)())() is M.EmptyList
    print("PASS redefinition, missing and self dependencies, undeclared formals, and wrong arities are refused")

    g_key = M.Pair(L.NatOperationCatalogLabel, M.Pair(g, M.EmptyList))
    f_key = M.Pair(L.NatOperationCatalogLabel, M.Pair(f, M.EmptyList))
    bad_expansion = M.Pair(M.Char("defined-nat-operation-v2"), M.Pair(g, M.Pair(formals,
        M.Pair(source, M.Pair(M.one, M.Pair(dependencies, M.EmptyList))))))
    tampered = M.TreeInsert(registry, g_key, bad_expansion, registry)()
    assert DO.RegisteredDefinedNatOperation(g, tampered)() is M.EmptyList
    assert M.Head(PG.EvaluateNatExpr(call, M.EmptyList, tampered, operations)())() is M.EmptyList
    bad_dependencies = M.Pair(M.Char("defined-nat-operation-v2"), M.Pair(g, M.Pair(formals,
        M.Pair(source, M.Pair(g_expansion, M.Pair(M.EmptyList, M.EmptyList))))))
    tampered = M.TreeInsert(registry, g_key, bad_dependencies, registry)()
    assert DO.RegisteredDefinedNatOperation(g, tampered)() is M.EmptyList
    assert M.Head(DO.ExecutableNatOperationDescriptor(g, tampered)())() is M.EmptyList
    bad_source = M.Pair(M.Char("defined-nat-operation-v2"), M.Pair(g, M.Pair(formals,
        M.Pair(M.Pair(f, M.Pair(y, M.EmptyList)), M.Pair(g_expansion, M.Pair(dependencies, M.EmptyList))))))
    tampered = M.TreeInsert(registry, g_key, bad_source, registry)()
    assert DO.RegisteredDefinedNatOperation(g, tampered)() is M.EmptyList
    replaced_f = M.Pair(M.Char("defined-nat-operation-v1"),
        M.Pair(f, M.Pair(f_formals, M.Pair(f_body, M.EmptyList))))
    tampered = M.TreeInsert(registry, f_key, replaced_f, registry)()
    assert M.IsPair(DO.RegisteredDefinedNatOperation(f, tampered)())() is M.truth_value
    assert DO.RegisteredDefinedNatOperation(g, tampered)() is M.EmptyList
    assert DO.RegisteredDefinedNatOperation(k, tampered)() is M.EmptyList
    assert M.Head(PG.EvaluateNatExpr(k_call, M.EmptyList, tampered, operations)())() is M.EmptyList
    print("PASS changed source, forged expansion, omitted dependency evidence, and replaced dependency records invalidate use")

    f_cycle_source = M.Pair(g, M.Pair(f_arg, M.Pair(M.one, M.EmptyList)))
    f_cycle = M.Pair(M.Char("defined-nat-operation-v2"), M.Pair(f, M.Pair(f_formals,
        M.Pair(f_cycle_source, M.Pair(f_body, M.Pair(M.Pair(g_record, M.EmptyList), M.EmptyList))))))
    cyclic = M.TreeInsert(registry, f_key, f_cycle, registry)()
    assert DO.RegisteredDefinedNatOperation(f, cyclic)() is M.EmptyList
    assert DO.RegisteredDefinedNatOperation(g, cyclic)() is M.EmptyList
    assert M.Head(PG.EvaluateNatExpr(call, M.EmptyList, cyclic, operations)())() is M.EmptyList
    print("PASS cyclic dependency records are refused without executing their primitive caches")

    descriptor_label = M.Atom()
    descriptor_formal = M.Char("argument identity regression")
    descriptor_formals = M.Pair(descriptor_formal, M.EmptyList)
    descriptor_registration = DO.RegisterDefinedNatOperation(descriptor_label, descriptor_formals, descriptor_formal, registry)()
    assert M.Head(descriptor_registration)() is M.truth_value
    descriptor_registry = M.Head(M.Tail(descriptor_registration)())()
    expected_descriptor = M.Head(M.Tail(M.Tail(descriptor_registration)())())()
    copied_formal = M.Char("argument identity regression")
    forged_descriptor = M.Pair(M.Head(expected_descriptor)(), M.Pair(descriptor_formals,
        M.Pair(M.Pair(descriptor_label, M.Pair(copied_formal, M.EmptyList)),
            M.Tail(M.Tail(M.Tail(expected_descriptor)())())())))
    assert M.Compare(forged_descriptor, expected_descriptor)() is M.truth_value
    catalog_key = M.Pair(L.NatOperationCatalogLabel, M.EmptyList)
    forged_catalog = M.Pair(L.NatOperationCatalogLabel, M.Pair(forged_descriptor, M.EmptyList))
    descriptor_registry = M.TreeInsert(descriptor_registry, catalog_key, forged_catalog, descriptor_registry)()
    assert DO.RegisteredDefinedNatOperation(descriptor_label, descriptor_registry)() is M.EmptyList
    assert M.Head(DO.ExecutableNatOperationDescriptor(descriptor_label, descriptor_registry)())() is M.EmptyList
    print("PASS a descriptor call cannot use an equal-valued copied argument in place of its formal identity")

    rt.graph._replace_context(constructors=registry)
    scope = M.Pair(M.Char("defined-composition-snapshot-check"), M.Pair(call, M.Pair(k_call, M.EmptyList)))
    rt.graph.add_node(scope)
    codec = persistence.SnapshotCodec(persistence._runtime_namespace_for_restore())
    with tempfile.TemporaryDirectory(prefix="hyge-defined-composition-") as snapshot_directory:
        snapshot_path = os.path.join(snapshot_directory, "composed-operation.json")
        codec.save(rt.graph, snapshot_path)
        restored = codec.load(snapshot_path)
        resumed = runtime.make_fresh_runtime()
        codec.activate(restored, resumed.graph)
    restored_scope = M.Head(M.FromContextGetNodes(resumed.graph)())()
    restored_call = M.Head(M.Tail(restored_scope)())()
    restored_nested = M.Head(M.Tail(M.Tail(restored_scope)())())()
    restored_registry = M.FromContextGetConstructors(resumed.graph)()
    restored_result = PG.EvaluateNatExpr(restored_call, M.EmptyList, restored_registry)()
    restored_registry = M.Head(M.Tail(restored_result)())()
    assert PG.RenderOperationValue(M.Head(restored_result)(), restored_registry)() == "15"
    restored_result = PG.EvaluateNatExpr(restored_nested, M.EmptyList, restored_registry)()
    restored_registry = M.Head(M.Tail(restored_result)())()
    assert PG.RenderOperationValue(M.Head(restored_result)(), restored_registry)() == "25"
    assert M.FromContextGetRuleOrder(resumed.graph)() is M.EmptyList
    print("PASS file-backed restoration preserves composed definitions, exact dependency identities, and execution")
    print("Defined composition regressions passed.")
