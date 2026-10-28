"""Finite template matching from an observed equation, with adversarial replay."""

import os
import tempfile

from hyge import discovered_laws as DL
from hyge import invariant_miner as IM
from hyge import labels as L
from hyge import machine as M
from hyge import main as Main
from hyge import persistence
from hyge import playground as PG
from hyge import runtime
from hyge import template_matching as TM


class CheckFiniteMatchCase(M.Edge):
    def __init__(self, template, variables, operation, carrier, registry, expected):
        self.result = TM.CheckFiniteTemplate(template, variables, operation, carrier, registry)()
        instance = M.Head(self.result)()
        assert M.Head(instance)() is L.TemplateInstanceLabel
        assert M.Head(M.Tail(M.Tail(instance)())())() is expected
        super().__init__(
            inputs=M.Pair(template, M.Pair(variables, M.Pair(operation,
                M.Pair(carrier, M.Pair(expected, M.EmptyList))))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CheckFiniteReplayCase(M.Edge):
    def __init__(self, instance, template, variables, operation, carrier, registry, expected):
        checked = TM.VerifyFiniteTemplateInstance(instance, template, variables, operation, carrier, registry)()
        assert M.Head(checked)() is expected
        self.result = M.Head(M.Tail(checked)())()
        super().__init__(
            inputs=M.Pair(instance, M.Pair(template, M.Pair(variables,
                M.Pair(operation, M.Pair(carrier, M.Pair(expected, M.EmptyList)))))),
            results=self.result,
        )

    def __call__(self):
        return self.result


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
    registry = M.FromContextGetConstructors(rt.graph)()
    built = PG.BuildNatOperationRegister(registry)()
    catalog = M.Head(built)()
    registry = M.Head(M.Tail(built)())()
    power_entry = PG.LookupOperationByLabel(L.ExprPowLabel, catalog)()
    gcd_entry = PG.LookupOperationByLabel(L.ExprGcdLabel, catalog)()
    powers = M.Pair(power_entry, M.EmptyList)
    source_carrier = M.Pair(M.one, M.EmptyList)
    carrier = M.Pair(M.one, M.Pair(M.two, M.Pair(M.three, M.EmptyList)))
    binary_carrier = M.Pair(M.Zero, M.Pair(M.one, M.EmptyList))

    # The positive requirement comes only from the actual operation miner.
    proposal = IM.ProposeNextRegularityOrStructure(powers, source_carrier, M.EmptyList, registry)()
    assert M.Head(proposal)() is L.ObservedRegularityLabel
    finding = M.Head(M.Tail(proposal)())()
    registry = M.Head(M.Tail(M.Tail(proposal)())())()
    finding_body = M.Tail(finding)()
    source_name = M.Head(finding_body)()
    equation_body = M.Tail(finding_body)()
    equation = M.Head(equation_body)()
    witnesses = M.Head(M.Tail(M.Tail(equation_body)())())()
    named_law = M.Pair(L.NamedRegularityLabel,
        M.Pair(M.Char("sampled exchange"), M.Pair(source_name,
            M.Pair(equation, M.Pair(source_carrier, M.Pair(witnesses, M.EmptyList))))))
    rt.graph._replace_context(constructors=registry)
    recorded = DL.RecordNamedDiscoveredLaw(rt, named_law, M.EmptyList)()
    assert M.Head(recorded)() is M.EmptyList
    assert M.Head(M.Tail(recorded)())() is M.EmptyList
    registry = M.Head(M.Tail(M.Tail(M.Tail(recorded)())())())()
    assert M.FromContextGetRuleOrder(rt.graph)() is M.EmptyList
    proposal = IM.ProposeNextRegularityOrStructure(
        powers, source_carrier, M.FromContextGetNodes(rt.graph)(), registry,
    )()
    assert M.Head(proposal)() is L.AlgebraicTemplateLabel
    template = M.Head(M.Tail(proposal)())()
    registry = M.Head(M.Tail(M.Tail(proposal)())())()
    named_structure = M.Pair(L.NamedStructureLabel,
        M.Pair(M.Char("sampled exchange profile"), M.Pair(template, M.EmptyList)))
    rt.graph._replace_context(constructors=registry)
    rt.graph.add_node(named_structure)
    print("PASS a mined observation becomes a template without activating a rule or receiving proof authority")

    a = M.Char("a")
    b = M.Char("b")
    variables = M.Pair(a, M.Pair(b, M.EmptyList))
    gcd_operation = M.Pair(L.ExprGcdLabel, variables)
    power_operation = M.Pair(L.ExprPowLabel, variables)
    addition_operation = M.Pair(L.ExprAddLabel, variables)
    matched = CheckFiniteMatchCase(template, variables, gcd_operation, carrier, registry, M.truth_value)()
    receipt = M.Head(matched)()
    registry = M.Head(M.Tail(matched)())()
    registry = CheckFiniteReplayCase(receipt, template, variables, gcd_operation, carrier, registry, M.truth_value)()
    wrapped_check = IM.CheckTemplateSatisfaction(template, variables, gcd_operation, carrier, registry)()
    assert M.Head(M.Tail(M.Tail(M.Head(wrapped_check)())())())() is M.truth_value
    registry = M.Head(M.Tail(wrapped_check)())()
    rt.graph._replace_context(constructors=registry)
    assert M.FromContextGetRuleOrder(rt.graph)() is M.EmptyList
    print("PASS the discovered operation role rebinds to gcd with renamed candidate variables and replays on the new carrier")

    rejected = CheckFiniteMatchCase(template, variables, power_operation, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    rejected = CheckFiniteMatchCase(template, variables, power_operation, binary_carrier, registry, M.false_value)()
    refuted_receipt = M.Head(rejected)()
    registry = M.Head(M.Tail(rejected)())()
    fields = M.Tail(refuted_receipt)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    refuted_evidence = M.Head(M.Tail(fields)())()
    closure = M.Head(refuted_evidence)()
    assert M.Head(M.Tail(closure)())() is M.truth_value
    failed_laws = M.Head(M.Tail(refuted_evidence)())()
    assert M.IsPair(failed_laws)() is M.truth_value
    failed_law = M.Head(failed_laws)()
    assert M.Head(M.Tail(M.Tail(failed_law)())())() is M.false_value
    rejected = CheckFiniteMatchCase(template, variables, addition_operation, binary_carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    fields = M.Tail(M.Head(rejected)())()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    nonclosed_evidence = M.Head(M.Tail(fields)())()
    assert M.Head(M.Tail(M.Head(nonclosed_evidence)())())() is M.false_value
    assert M.Head(M.Tail(nonclosed_evidence)())() is M.EmptyList
    print("PASS a closed operation with a false equation and an equation-preserving nonclosed operation fail independently")

    requirements = M.Head(M.Tail(M.Tail(M.Tail(template)())())())()
    textual = M.Pair(L.AlgebraicTemplateLabel,
        M.Pair(M.Char("text-only profile"), M.Pair(M.Pair(M.Char("commutativity"), M.EmptyList), M.EmptyList)))
    rejected = CheckFiniteMatchCase(textual, variables, gcd_operation, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    rejected = CheckFiniteMatchCase(named_structure, variables, gcd_operation, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    empty_requirements = M.Pair(L.AlgebraicTemplateLabel,
        M.Pair(source_carrier, M.Pair(powers, M.Pair(M.EmptyList, M.EmptyList))))
    rejected = CheckFiniteMatchCase(empty_requirements, variables, gcd_operation, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    textual_requirement = M.Pair(L.AlgebraicTemplateLabel,
        M.Pair(source_carrier, M.Pair(powers, M.Pair(M.Pair(M.Char("a property"), M.EmptyList), M.EmptyList))))
    rejected = CheckFiniteMatchCase(textual_requirement, variables, gcd_operation, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    substituted_source = M.Pair(L.AlgebraicTemplateLabel,
        M.Pair(source_carrier, M.Pair(M.Pair(gcd_entry, M.EmptyList), M.Pair(requirements, M.EmptyList))))
    rejected = CheckFiniteMatchCase(substituted_source, variables, gcd_operation, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    equation_fields = M.Tail(equation)()
    law_variables = M.Head(equation_fields)()
    lhs = M.Head(M.Tail(equation_fields)())()
    rhs = M.Head(M.Tail(M.Tail(equation_fields)())())()
    foreign_lhs = M.Pair(L.ExprGcdLabel, M.Tail(lhs)())
    foreign_equation = M.Pair(L.DiscoveredEquationLabel,
        M.Pair(law_variables, M.Pair(foreign_lhs, M.Pair(rhs, M.EmptyList))))
    foreign_requirement = M.Pair(L.NamedRegularityLabel,
        M.Pair(M.Char("mutated requirement"), M.Pair(source_name,
            M.Pair(foreign_equation, M.Pair(source_carrier, M.Pair(witnesses, M.EmptyList))))))
    foreign_template = M.Pair(L.AlgebraicTemplateLabel,
        M.Pair(source_carrier, M.Pair(powers, M.Pair(M.Pair(foreign_requirement, M.EmptyList), M.EmptyList))))
    rejected = CheckFiniteMatchCase(foreign_template, variables, gcd_operation, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    print("PASS textual, vacuous, wrapped, substituted-source, and foreign-operation requirements cannot impersonate an explicit template")

    repeated_variables = M.Pair(a, M.Pair(a, M.EmptyList))
    repeated_body = M.Pair(L.ExprGcdLabel, repeated_variables)
    rejected = CheckFiniteMatchCase(template, variables, repeated_body, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    rejected = CheckFiniteMatchCase(template, repeated_variables, repeated_body, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    unknown_body = M.Pair(M.Char("opaque operation"), variables)
    rejected = CheckFiniteMatchCase(template, variables, unknown_body, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    rejected = CheckFiniteMatchCase(template, variables, gcd_operation, M.EmptyList, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    rejected = CheckFiniteMatchCase(template, variables, gcd_operation,
        M.Pair(M.one, M.Char("improper carrier")), registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    rejected = CheckFiniteMatchCase(template, variables, gcd_operation,
        M.Pair(M.truth_value, M.EmptyList), registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    rejected = CheckFiniteMatchCase(template, variables, gcd_operation,
        M.Pair(M.one, M.Pair(M.one, M.EmptyList)), registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    empty_source = M.Pair(L.AlgebraicTemplateLabel,
        M.Pair(M.EmptyList, M.Pair(powers, M.Pair(requirements, M.EmptyList))))
    rejected = CheckFiniteMatchCase(empty_source, variables, gcd_operation, carrier, registry, M.false_value)()
    registry = M.Head(M.Tail(rejected)())()
    print("PASS malformed candidate bodies, repeated formals, unknown operations, and empty or malformed finite scopes are refused")

    fields = M.Tail(receipt)()
    receipt_name = M.Head(fields)()
    fields = M.Tail(fields)()
    scope_fields = M.Tail(fields)()
    fields = M.Tail(scope_fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    fields = M.Tail(fields)()
    method = M.Head(fields)()
    evidence = M.Head(M.Tail(fields)())()
    flipped_verdict = M.Pair(L.TemplateInstanceLabel,
        M.Pair(receipt_name, M.Pair(M.false_value, scope_fields)))
    registry = CheckFiniteReplayCase(flipped_verdict, template, variables, gcd_operation, carrier, registry, M.truth_value)()
    forged_success = M.Pair(L.TemplateInstanceLabel,
        M.Pair(M.Head(M.Tail(refuted_receipt)())(),
            M.Pair(M.truth_value, M.Tail(M.Tail(M.Tail(refuted_receipt)())())())))
    registry = CheckFiniteReplayCase(forged_success, template, variables, power_operation, binary_carrier, registry, M.false_value)()
    altered_method = M.Pair(L.TemplateInstanceLabel,
        M.Pair(receipt_name, M.Pair(M.truth_value, M.Pair(template, M.Pair(variables,
            M.Pair(gcd_operation, M.Pair(carrier, M.Pair(M.Char("unchecked"), M.Pair(evidence, M.EmptyList)))))))))
    registry = CheckFiniteReplayCase(altered_method, template, variables, gcd_operation, carrier, registry, M.false_value)()
    altered_evidence = M.Pair(L.TemplateInstanceLabel,
        M.Pair(receipt_name, M.Pair(M.truth_value, M.Pair(template, M.Pair(variables,
            M.Pair(gcd_operation, M.Pair(carrier, M.Pair(method, M.Pair(M.EmptyList, M.EmptyList)))))))))
    registry = CheckFiniteReplayCase(altered_evidence, template, variables, gcd_operation, carrier, registry, M.false_value)()
    registry = CheckFiniteReplayCase(receipt, substituted_source, variables, gcd_operation, carrier, registry, M.false_value)()
    other_variables = M.Pair(M.Char("u"), M.Pair(M.Char("v"), M.EmptyList))
    registry = CheckFiniteReplayCase(receipt, template, other_variables, gcd_operation, carrier, registry, M.false_value)()
    registry = CheckFiniteReplayCase(receipt, template, variables, power_operation, carrier, registry, M.false_value)()
    registry = CheckFiniteReplayCase(receipt, template, variables, gcd_operation, source_carrier, registry, M.false_value)()
    registry = CheckFiniteReplayCase(M.EmptyList, template, variables, gcd_operation, carrier, registry, M.false_value)()
    print("PASS replay ignores claimed verdicts and rejects forged evidence, method changes, malformed receipts, and every changed scope input")

    rt.graph._replace_context(constructors=registry)
    expected_scope = M.Pair(M.Char("expected-finite-template-scope"),
        M.Pair(template, M.Pair(variables, M.Pair(gcd_operation, M.Pair(carrier, M.EmptyList)))))
    rt.graph.add_node(expected_scope)
    rt.graph.add_node(receipt)
    assert M.FromContextGetRuleOrder(rt.graph)() is M.EmptyList
    codec = persistence.SnapshotCodec(Main._runtime_namespace())
    with tempfile.TemporaryDirectory(prefix="hyge-finite-template-") as snapshot_dir:
        snapshot_path = os.path.join(snapshot_dir, "finite-template.json")
        codec.save(rt.graph, snapshot_path)
        restored = codec.load(snapshot_path)
        resumed = runtime.make_fresh_runtime()
        codec.activate(restored, resumed.graph)
    nodes = M.FromContextGetNodes(resumed.graph)()
    restored_receipt = M.Head(nodes)()
    restored_scope = M.Head(M.Tail(nodes)())()
    assert M.Compare(M.Head(restored_scope)(), M.Char("expected-finite-template-scope"))() is M.truth_value
    fields = M.Tail(restored_scope)()
    restored_template = M.Head(fields)()
    fields = M.Tail(fields)()
    restored_variables = M.Head(fields)()
    fields = M.Tail(fields)()
    restored_operation = M.Head(fields)()
    restored_carrier = M.Head(M.Tail(fields)())()
    registry = CheckFiniteReplayCase(restored_receipt, restored_template, restored_variables,
        restored_operation, restored_carrier, M.FromContextGetConstructors(resumed.graph)(), M.truth_value)()
    resumed.graph._replace_context(constructors=registry)
    assert M.FromContextGetRuleOrder(resumed.graph)() is M.EmptyList
    print("PASS snapshot roundtrip preserves independent expected scope and replayable finite evidence without activating graph rules")
    print("Finite template matching regressions passed.")
