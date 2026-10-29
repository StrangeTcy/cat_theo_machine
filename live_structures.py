"""Persist and explain finite observation bundles without naming or promotion."""

from . import labels as L
from . import live_proof as LP
from . import machine as M
from . import observed_structures as OS
from . import playground as PG


class LatestObservedStructureBundle(M.Edge):
    def __init__(self, nodes, registry, domain=M.EmptyList):
        result = M.EmptyList
        if M.IsPair(nodes)() is M.truth_value:
            node = M.Head(nodes)()
            if PG.ExactArity(node, M.six, registry)() is M.truth_value:
                if M.Compare(M.Head(node)(), M.Char("observed-structure-bundle-v1"))() is M.truth_value:
                    if M.OrAtom(
                        M.IdentityCompare(domain, M.EmptyList)(),
                        M.Compare(LP.LiveProofRecordField(node, M.one)(), domain)(),
                    )() is M.truth_value:
                        result = node
            if M.IdentityCompare(result, M.EmptyList)() is M.truth_value:
                result = LatestObservedStructureBundle(M.Tail(nodes)(), registry, domain)()
        super().__init__(inputs=M.Pair(nodes, M.Pair(domain, M.EmptyList)), results=result)


class RecordObservedStructureBundle(M.Edge):
    """Extend a compatible finite bundle; preserve incompatible prior records."""

    def __init__(self, graph, finding, domain, operations):
        registry = M.FromContextGetConstructors(graph)()
        nodes = M.FromContextGetNodes(graph)()
        previous = LatestObservedStructureBundle(nodes, registry, domain)()
        findings = M.Pair(finding, M.EmptyList)
        if M.IsPair(previous)() is M.truth_value:
            saved = LP.LiveProofRecordField(previous, M.three)()
            if PG.ChainHasTerm(saved, finding)() is M.truth_value:
                findings = saved
            else:
                findings = M.Pair(finding, saved)
        built = OS.BuildObservedStructureBundle(findings, domain, operations, registry)()
        bundle = M.Head(built)()
        registry = M.Head(M.Tail(built)())()
        graph._replace_context(constructors=registry)
        RecordObservedStructureAttempt(graph, findings, domain, operations, previous, bundle)()
        if M.AndAtom(M.IdentityCompare(bundle, M.EmptyList)(), M.IsPair(previous)())() is M.truth_value:
            built = OS.BuildObservedStructureBundle(M.Pair(finding, M.EmptyList), domain, operations, registry)()
            bundle = M.Head(built)()
            registry = M.Head(M.Tail(built)())()
            graph._replace_context(constructors=registry)
            RecordObservedStructureAttempt(graph, M.Pair(finding, M.EmptyList), domain, operations, previous, bundle)()
        graph._replace_context(constructors=registry)
        if M.IsPair(bundle)() is M.truth_value:
            if PG.ChainHasTerm(nodes, bundle)() is M.false_value:
                graph.add_node(bundle)
        super().__init__(inputs=M.Pair(finding, M.Pair(domain, M.Pair(operations, M.EmptyList))), results=built)


class RecordObservedStructureAttempt(M.Edge):
    """Keep candidate ancestry and unsuccessful input sets available for replay."""

    def __init__(self, graph, findings, domain, operations, previous, bundle):
        status = L.FailedLabel
        if M.IsPair(bundle)() is M.truth_value:
            status = L.PendingLabel
        result = M.Pair(
            M.Char("observed-structure-attempt-v1"),
            M.Pair(findings, M.Pair(domain, M.Pair(operations,
                M.Pair(previous, M.Pair(bundle, M.Pair(status, M.EmptyList)))))),
        )
        graph.add_node(result)
        super().__init__(inputs=M.Pair(findings, M.Pair(previous, M.EmptyList)), results=result)


class RenderObservedEquations(M.Edge):
    def __init__(self, findings, registry):
        result = ""
        if M.IsPair(findings)() is M.truth_value:
            finding = M.Head(findings)()
            equation = LP.LiveProofRecordField(finding, M.two)()
            result = "  " + PG.RenderDiscoveredEquation(equation, registry)() + "\n"
            result = result + RenderObservedEquations(M.Tail(findings)(), registry)()
        self.result = result
        super().__init__(inputs=M.Pair(findings, M.EmptyList), results=M.EmptyList)

    def __call__(self):
        return self.result


class ExplainObservedStructureBundle(M.Edge):
    """Replay a saved candidate before describing its exact finite evidence."""

    def __init__(self, graph):
        registry = M.FromContextGetConstructors(graph)()
        bundle = LatestObservedStructureBundle(M.FromContextGetNodes(graph)(), registry)()
        result = "No observed structure candidate is saved."
        if M.IsPair(bundle)() is M.truth_value:
            domain = LP.LiveProofRecordField(bundle, M.one)()
            operations = LP.LiveProofRecordField(bundle, M.two)()
            findings = LP.LiveProofRecordField(bundle, M.three)()
            checked = OS.VerifyObservedStructureBundle(bundle, findings, domain, operations, registry)()
            registry = M.Head(M.Tail(checked)())()
            result = "The saved candidate failed finite replay; no structural claim was accepted."
            if M.Head(checked)() is M.truth_value:
                result = (
                    "Observed structure candidate on finite carrier " + PG.FormatSetChain(domain, registry)() + ".\n"
                    + "Operations used: " + PG.FormatDiscoveredOperationNames(operations)() + ".\n"
                    + "Observed equations:\n" + RenderObservedEquations(findings, registry)()
                    + "Each equation and its source witnesses were checked again on this carrier.\n"
                    + "Carrier closure, universal laws and theorem transfer remain unchecked."
                )
        graph._replace_context(constructors=registry)
        self.result = result
        super().__init__(inputs=M.Pair(bundle, M.EmptyList), results=M.EmptyList)

    def __call__(self):
        return self.result
