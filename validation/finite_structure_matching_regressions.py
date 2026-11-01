"""Finite structures from mined mixed equations and exact operation bindings."""

import os
import tempfile

from hyge import defined_operations as DO
from hyge import finite_structure_matching as FS
from hyge import invariant_miner as IM
from hyge import labels as L
from hyge import machine as M
from hyge import persistence
from hyge import playground as PG
from hyge import runtime
from hyge import template_matching as TM


class MixedStructureFinding(M.Edge):
    """Select the miner's two-role equation through its structural dependencies."""

    def __init__(self, findings, domain, catalog, registry):
        result = M.EmptyList
        if M.IsPair(findings)() is M.truth_value:
            finding = M.Head(findings)()
            fields = M.Tail(finding)()
            name = M.Head(fields)()
            equation = M.Head(M.Tail(fields)())()
            witnesses = M.Head(M.Tail(M.Tail(M.Tail(fields)())())())()
            requirement = M.Pair(L.NamedRegularityLabel,
                M.Pair(M.Char("mined mixed structure"), M.Pair(name,
                    M.Pair(equation, M.Pair(domain, M.Pair(witnesses, M.EmptyList))))))
            dependencies = TM.FiniteTemplateDependencies(
                M.Pair(requirement, M.EmptyList), domain, catalog, registry)()
            if M.Head(dependencies)() is M.truth_value:
                used = M.Head(M.Tail(dependencies)())()
                if PG.ExactArity(used, M.two, registry)() is M.truth_value:
                    result = requirement
            if M.IdentityCompare(result, M.EmptyList)() is M.truth_value:
                result = MixedStructureFinding(M.Tail(findings)(), domain, catalog, registry)()
        super().__init__(inputs=M.Pair(findings, M.Pair(domain, M.Pair(catalog, M.EmptyList))), results=result)


class CheckStructureCase(M.Edge):
    def __init__(self, template, bindings, carrier, registry, expected):
        checked = FS.CheckFiniteStructure(template, bindings, carrier, registry)()
        instance = M.Head(checked)()
        assert M.Head(instance)() is L.TemplateInstanceLabel
        assert M.Head(M.Tail(M.Tail(instance)())())() is expected
        super().__init__(inputs=M.Pair(template, M.Pair(bindings, M.Pair(carrier, M.EmptyList))), results=checked)


class ReplayStructureCase(M.Edge):
    def __init__(self, instance, template, bindings, carrier, registry, expected):
        checked = FS.VerifyFiniteStructureInstance(instance, template, bindings, carrier, registry)()
        assert M.Head(checked)() is expected
        super().__init__(inputs=M.Pair(instance, M.Pair(template, M.Pair(bindings, M.Pair(carrier, M.EmptyList)))),
            results=M.Head(M.Tail(checked)())())


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
    registry = M.FromContextGetConstructors(rt.graph)()
    built = PG.BuildNatOperationRegister(registry)()
    catalog = M.Head(built)()
    registry = M.Head(M.Tail(built)())()
    multiplication = PG.LookupOperationByLabel(L.ExprMulLabel, catalog)()
    gcd = PG.LookupOperationByLabel(L.ExprGcdLabel, catalog)()
    source_operations = M.Pair(multiplication, M.Pair(gcd, M.EmptyList))
    domain = M.Pair(M.Zero, M.Pair(M.one, M.EmptyList))
    miner = IM.MineOperationInvariantsAcrossRegister(domain, registry,
        source_operations, stop_after_first=M.truth_value)
    registry = M.Head(M.Tail(miner())())()
    # Exercise the existing miner's mixed-candidate generation and exhaustive check.
    # The requirement is selected from its findings, never supplied as an equation.
    mixed = miner._mixed_laws_for(multiplication, domain, registry, source_operations)
    registry = M.Head(M.Tail(mixed)())()
    requirement = MixedStructureFinding(M.Head(mixed)(), domain, catalog, registry)()
    assert M.IsPair(requirement)() is M.truth_value
    template = M.Pair(L.AlgebraicTemplateLabel,
        M.Pair(domain, M.Pair(catalog, M.Pair(M.Pair(requirement, M.EmptyList), M.EmptyList))))
    a = M.Atom()
    b = M.Atom()
    formals = M.Pair(a, M.Pair(b, M.EmptyList))
    product_call = M.Pair(L.ExprMulLabel, formals)
    gcd_call = M.Pair(L.ExprGcdLabel, formals)
    product_binding = FS.StructureOperationBinding(L.ExprMulLabel, formals, product_call)()
    gcd_binding = FS.StructureOperationBinding(L.ExprGcdLabel, formals, gcd_call)()
    bindings = M.Pair(product_binding, M.Pair(gcd_binding, M.EmptyList))
    legacy = TM.CheckFiniteTemplate(template, formals, gcd_call, domain, registry)()
    assert M.Head(M.Tail(M.Tail(M.Head(legacy)())())())() is M.false_value
    checked = CheckStructureCase(template, bindings, domain, registry, M.truth_value)()
    receipt = M.Head(checked)()
    registry = M.Head(M.Tail(checked)())()
    registry = ReplayStructureCase(receipt, template, bindings, domain, registry, M.truth_value)()
    print("PASS a miner-generated multiplication-over-gcd equation needs two explicit roles and now matches and replays")

    custom = M.Atom()
    registered = DO.RegisterDefinedNatOperation(custom, formals, product_call, registry)()
    assert M.Head(registered)() is M.truth_value
    registry = M.Head(M.Tail(registered)())()
    custom_call = M.Pair(custom, formals)
    custom_binding = FS.StructureOperationBinding(L.ExprMulLabel, formals, custom_call)()
    custom_bindings = M.Pair(custom_binding, M.Pair(gcd_binding, M.EmptyList))
    checked = CheckStructureCase(template, custom_bindings, domain, registry, M.truth_value)()
    custom_receipt = M.Head(checked)()
    registry = M.Head(M.Tail(checked)())()
    registry = ReplayStructureCase(custom_receipt, template, custom_bindings, domain, registry, M.truth_value)()
    assert M.FromContextGetRuleOrder(rt.graph)() is M.EmptyList
    print("PASS a registered product definition fills one role with checked closure and all eight mixed-law assignments")

    composed = M.Atom()
    registered = DO.RegisterDefinedNatOperation(composed, formals, custom_call, registry)()
    assert M.Head(registered)() is M.truth_value
    registry = M.Head(M.Tail(registered)())()
    composed_record = DO.RegisteredDefinedNatOperation(composed, registry)()
    assert M.Compare(M.Head(composed_record)(), M.Char("defined-nat-operation-v2"))() is M.truth_value
    composed_call = M.Pair(composed, formals)
    composed_binding = FS.StructureOperationBinding(L.ExprMulLabel, formals, composed_call)()
    composed_bindings = M.Pair(composed_binding, M.Pair(gcd_binding, M.EmptyList))
    checked = CheckStructureCase(template, composed_bindings, domain, registry, M.truth_value)()
    composed_receipt = M.Head(checked)()
    registry = M.Head(M.Tail(checked)())()
    registry = ReplayStructureCase(composed_receipt, template, composed_bindings, domain, registry, M.truth_value)()

    equation = M.Head(M.Tail(M.Tail(M.Tail(requirement)())())())()
    equation_fields = M.Tail(equation)()
    law_variables = M.Head(equation_fields)()
    source_lhs = FS.RebindStructureTerm(M.Head(M.Tail(equation_fields)())(), law_variables,
        custom_bindings, domain, domain, registry)()
    source_rhs = FS.RebindStructureTerm(M.Head(M.Tail(M.Tail(equation_fields)())())(), law_variables,
        custom_bindings, domain, domain, registry)()
    custom_equation = M.Pair(L.DiscoveredEquationLabel,
        M.Pair(law_variables, M.Pair(source_lhs, M.Pair(source_rhs, M.EmptyList))))
    custom_requirement = M.Pair(L.NamedRegularityLabel, M.Pair(M.Char("rebound mined structure"),
        M.Pair(M.Char("custom product over gcd"), M.Pair(custom_equation,
            M.Pair(domain, M.Pair(M.EmptyList, M.EmptyList))))))
    source_catalog = M.Head(PG.BuildNatOperationRegister(registry)())()
    custom_template = M.Pair(L.AlgebraicTemplateLabel, M.Pair(domain, M.Pair(source_catalog,
        M.Pair(M.Pair(custom_requirement, M.EmptyList), M.EmptyList))))
    custom_source_binding = FS.StructureOperationBinding(custom, formals, product_call)()
    custom_source_bindings = M.Pair(custom_source_binding, M.Pair(gcd_binding, M.EmptyList))
    checked = CheckStructureCase(custom_template, custom_source_bindings, domain, registry, M.truth_value)()
    custom_source_receipt = M.Head(checked)()
    registry = M.Head(M.Tail(checked)())()
    registry = ReplayStructureCase(custom_source_receipt, custom_template, custom_source_bindings,
        domain, registry, M.truth_value)()
    print("PASS composed v2 definitions fill target roles and registered custom source roles bind back to builtin operations")

    CheckStructureCase(template, M.Pair(product_binding, M.EmptyList), domain, registry, M.false_value)()
    CheckStructureCase(template, M.Pair(gcd_binding, M.EmptyList), domain, registry, M.false_value)()
    CheckStructureCase(template, M.Pair(product_binding, bindings), domain, registry, M.false_value)()
    conflicting = FS.StructureOperationBinding(L.ExprMulLabel, formals, gcd_call)()
    CheckStructureCase(template, M.Pair(conflicting, bindings), domain, registry, M.false_value)()
    unused = FS.StructureOperationBinding(L.ExprAddLabel, formals, product_call)()
    CheckStructureCase(template, M.Pair(unused, bindings), domain, registry, M.false_value)()
    unary = M.Pair(a, M.EmptyList)
    wrong_arity = FS.StructureOperationBinding(L.ExprMulLabel, unary, M.Pair(L.ExprMulLabel, unary))()
    CheckStructureCase(template, M.Pair(wrong_arity, M.Pair(gcd_binding, M.EmptyList)), domain, registry, M.false_value)()
    repeated = M.Pair(a, M.Pair(a, M.EmptyList))
    repeated_binding = FS.StructureOperationBinding(L.ExprMulLabel, repeated, M.Pair(custom, repeated))()
    CheckStructureCase(template, M.Pair(repeated_binding, M.Pair(gcd_binding, M.EmptyList)), domain, registry, M.false_value)()
    reordered = FS.StructureOperationBinding(L.ExprMulLabel, formals, M.Pair(custom, M.Pair(b, M.Pair(a, M.EmptyList))))()
    CheckStructureCase(template, M.Pair(reordered, M.Pair(gcd_binding, M.EmptyList)), domain, registry, M.false_value)()
    unknown = FS.StructureOperationBinding(L.ExprMulLabel, formals, M.Pair(M.Atom(), formals))()
    CheckStructureCase(template, M.Pair(unknown, M.Pair(gcd_binding, M.EmptyList)), domain, registry, M.false_value)()
    CheckStructureCase(template, M.Pair(product_binding, M.Atom()), domain, registry, M.false_value)()
    CheckStructureCase(template, bindings, M.EmptyList, registry, M.false_value)()
    CheckStructureCase(template, bindings, M.Pair(M.one, M.Pair(M.one, M.EmptyList)), registry, M.false_value)()
    print("PASS missing, duplicate, conflicting, unused, malformed and wrong-arity bindings and malformed carriers are refused")

    addition_binding = FS.StructureOperationBinding(L.ExprMulLabel, formals, M.Pair(L.ExprAddLabel, formals))()
    CheckStructureCase(template, M.Pair(addition_binding, M.Pair(gcd_binding, M.EmptyList)), domain, registry, M.false_value)()
    power_binding = FS.StructureOperationBinding(L.ExprMulLabel, formals, M.Pair(L.ExprPowLabel, formals))()
    power_bindings = M.Pair(power_binding, M.Pair(gcd_binding, M.EmptyList))
    rejected = CheckStructureCase(template, power_bindings, domain, registry, M.false_value)()
    refuted = M.Head(rejected)()
    forged = M.Pair(L.TemplateInstanceLabel, M.Pair(M.Char("finite-operation-structure-v1"),
        M.Pair(M.truth_value, M.Tail(M.Tail(M.Tail(refuted)())())())))
    ReplayStructureCase(forged, template, power_bindings, domain, registry, M.false_value)()
    print("PASS nonclosed addition and closed exponentiation with a false mixed equation fail independently")

    empty_evidence_scope = M.Pair(template,
        M.Pair(custom_bindings, M.Pair(domain, M.Pair(M.EmptyList, M.EmptyList))))
    missing_evidence = M.Pair(L.TemplateInstanceLabel,
        M.Pair(M.Char("finite-operation-structure-v1"), M.Pair(M.truth_value, empty_evidence_scope)))
    ReplayStructureCase(missing_evidence, template, custom_bindings, domain, registry, M.false_value)()
    ReplayStructureCase(custom_receipt, template, bindings, domain, registry, M.false_value)()
    ReplayStructureCase(custom_receipt, template, custom_bindings, M.Pair(M.one, M.EmptyList), registry, M.false_value)()
    widened = M.Pair(M.Zero, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
    ReplayStructureCase(custom_receipt, template, custom_bindings, widened, registry, M.false_value)()
    ReplayStructureCase(M.EmptyList, template, custom_bindings, domain, registry, M.false_value)()
    key = M.Pair(L.NatOperationCatalogLabel, M.Pair(custom, M.EmptyList))
    # A different valid definition still agrees on {0,1}; its semantics must be pinned.
    squared_product = M.Pair(L.ExprPowLabel, M.Pair(product_call, M.Pair(M.two, M.EmptyList)))
    changed_definition = M.Pair(M.Char("defined-nat-operation-v1"),
        M.Pair(custom, M.Pair(formals, M.Pair(squared_product, M.EmptyList))))
    changed_registry = M.TreeInsert(registry, key, changed_definition, registry)()
    assert M.IsPair(DO.RegisteredDefinedNatOperation(custom, changed_registry)())() is M.truth_value
    CheckStructureCase(template, custom_bindings, domain, changed_registry, M.truth_value)()
    ReplayStructureCase(custom_receipt, template, custom_bindings, domain, changed_registry, M.false_value)()
    CheckStructureCase(custom_template, custom_source_bindings, domain, changed_registry, M.truth_value)()
    ReplayStructureCase(custom_source_receipt, custom_template, custom_source_bindings,
        domain, changed_registry, M.false_value)()
    ReplayStructureCase(composed_receipt, template, composed_bindings, domain, changed_registry, M.false_value)()
    print("PASS receipt replay rejects forged evidence, scope changes and a changed definition even when every finite value agrees")

    # Required roles are collected across every equation, including later requirements.
    equation = M.Head(M.Tail(M.Tail(M.Tail(requirement)())())())()
    law_variables = M.Head(M.Tail(equation)())()
    extra_call = M.Pair(L.ExprPowLabel, M.Pair(M.Head(law_variables)(), M.Pair(M.one, M.EmptyList)))
    extra_equation = M.Pair(L.DiscoveredEquationLabel,
        M.Pair(law_variables, M.Pair(extra_call, M.Pair(extra_call, M.EmptyList))))
    extra_requirement = M.Pair(L.NamedRegularityLabel, M.Pair(M.Char("additional role"),
        M.Pair(M.Char("pow"), M.Pair(extra_equation, M.Pair(domain, M.Pair(M.EmptyList, M.EmptyList))))))
    extended_template = M.Pair(L.AlgebraicTemplateLabel, M.Pair(domain, M.Pair(catalog,
        M.Pair(M.Pair(requirement, M.Pair(extra_requirement, M.EmptyList)), M.EmptyList))))
    CheckStructureCase(extended_template, bindings, domain, registry, M.false_value)()
    extra_binding = FS.StructureOperationBinding(L.ExprPowLabel, formals, product_call)()
    CheckStructureCase(extended_template, M.Pair(extra_binding, bindings), domain, registry, M.truth_value)()
    ReplayStructureCase(receipt, extended_template, bindings, domain, registry, M.false_value)()
    print("PASS operation roles in later equations also require bindings and cannot widen an earlier receipt")

    rt.graph._replace_context(constructors=registry)
    scope = M.Pair(M.Char("finite-structure-replay-scope"),
        M.Pair(template, M.Pair(composed_bindings, M.Pair(domain, M.EmptyList))))
    rt.graph.add_node(scope)
    rt.graph.add_node(composed_receipt)
    codec = persistence.SnapshotCodec(persistence._runtime_namespace_for_restore())
    with tempfile.TemporaryDirectory(prefix="hyge-finite-structure-") as snapshot_directory:
        snapshot_path = os.path.join(snapshot_directory, "finite-structure.json")
        codec.save(rt.graph, snapshot_path)
        restored = codec.load(snapshot_path)
        resumed = runtime.make_fresh_runtime()
        codec.activate(restored, resumed.graph)
    nodes = M.FromContextGetNodes(resumed.graph)()
    restored_receipt = M.Head(nodes)()
    restored_scope = M.Head(M.Tail(nodes)())()
    fields = M.Tail(restored_scope)()
    restored_template = M.Head(fields)()
    restored_bindings = M.Head(M.Tail(fields)())()
    restored_domain = M.Head(M.Tail(M.Tail(fields)())())()
    ReplayStructureCase(restored_receipt, restored_template, restored_bindings,
        restored_domain, M.FromContextGetConstructors(resumed.graph)(), M.truth_value)()
    assert M.FromContextGetRuleOrder(resumed.graph)() is M.EmptyList
    print("PASS file-backed restoration retains multiple operation roles, custom semantics and replay without activating rules")
    print("Finite structure matching regressions passed.")
