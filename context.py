from __future__ import annotations

from .core import Edge, EmptyList, Head, IdentityCompare, Pair, Tail, false_value, truth_value
from .labels import (
    ContextAllRulesLabel,
    ContextConstructorsLabel,
    ContextCounterfactualResultsLabel,
    ContextDependencyGraphLabel,
    ContextDependencyRequestsLabel,
    ContextDerivationsLabel,
    ContextDerivationSchemataLabel,
    ContextEdgesLabel,
    ContextGeneratorMetricsLabel,
    ContextInterventionEpisodesLabel,
    ContextDependencyPoliciesLabel,
    ContextGeneratorPolicyLabel,
    ContextLastProofLabel,
    ContextLastResidualsLabel,
    ContextNextRuleIndexLabel,
    ContextNodesLabel,
    ContextProvenanceMapLabel,
    ContextResearchModeLabel,
    ContextResearchAttemptsLabel,
    ContextResearchResidualsLabel,
    ContextRuleOrderLabel,
    ContextSearchComparisonsLabel,
    ContextSearchComparisonJobsLabel,
    ContextSearchHistoryLabel,
    ContextSearchJobsLabel,
    ContextSearchMemoLabel,
    ContextNatValueIndexLabel,
    ContextTestResultsLabel,
    ContextTestsLabel,
    MachineContextLabel,
)
from .trees import Tree, TreeInsert, TreeLookup


def Context(
    constructors,
    nodes,
    edges,
    tests,
    test_results,
    all_rules,
    next_rule_index,
    rule_order,
    derivations,
    derivation_schemata,
    search_history,
    search_comparisons,
    search_comparison_jobs,
    search_jobs,
    search_memo,
    nat_value_index,
    dependency_requests=None,
    dependency_graph=None,
    generator_metrics=None,
    last_proof=None,
    research_residuals=None,
    provenance_map=None,
    generator_policy=None,
    last_residuals=None,
    counterfactual_results=None,
    research_mode=None,
    research_attempts=None,
    intervention_episodes=None,
    dependency_policies=None,
):
    if dependency_requests is None:
        dependency_requests = EmptyList
    if dependency_graph is None:
        dependency_graph = EmptyList
    if generator_metrics is None:
        generator_metrics = EmptyList
    if last_proof is None:
        last_proof = EmptyList
    if research_residuals is None:
        research_residuals = EmptyList
    if provenance_map is None:
        provenance_map = EmptyList
    if generator_policy is None:
        generator_policy = EmptyList
    if last_residuals is None:
        last_residuals = EmptyList
    if counterfactual_results is None:
        counterfactual_results = EmptyList
    if research_mode is None:
        research_mode = EmptyList
    if research_attempts is None:
        research_attempts = EmptyList
    if intervention_episodes is None:
        intervention_episodes = EmptyList
    if dependency_policies is None:
        dependency_policies = EmptyList
    tree = Tree(EmptyList)
    tree = TreeInsert(tree, ContextConstructorsLabel, constructors, constructors)()
    tree = TreeInsert(tree, ContextNodesLabel, nodes, constructors)()
    tree = TreeInsert(tree, ContextEdgesLabel, edges, constructors)()
    tree = TreeInsert(tree, ContextTestsLabel, tests, constructors)()
    tree = TreeInsert(tree, ContextTestResultsLabel, test_results, constructors)()
    tree = TreeInsert(tree, ContextAllRulesLabel, all_rules, constructors)()
    tree = TreeInsert(tree, ContextNextRuleIndexLabel, next_rule_index, constructors)()
    tree = TreeInsert(tree, ContextRuleOrderLabel, rule_order, constructors)()
    tree = TreeInsert(tree, ContextDerivationsLabel, derivations, constructors)()
    tree = TreeInsert(tree, ContextDerivationSchemataLabel, derivation_schemata, constructors)()
    tree = TreeInsert(tree, ContextSearchHistoryLabel, search_history, constructors)()
    tree = TreeInsert(tree, ContextSearchComparisonsLabel, search_comparisons, constructors)()
    tree = TreeInsert(tree, ContextSearchComparisonJobsLabel, search_comparison_jobs, constructors)()
    tree = TreeInsert(tree, ContextSearchJobsLabel, search_jobs, constructors)()
    tree = TreeInsert(tree, ContextSearchMemoLabel, search_memo, constructors)()
    tree = TreeInsert(tree, ContextNatValueIndexLabel, nat_value_index, constructors)()
    tree = TreeInsert(tree, ContextDependencyRequestsLabel, dependency_requests, constructors)()
    tree = TreeInsert(tree, ContextDependencyGraphLabel, dependency_graph, constructors)()
    tree = TreeInsert(tree, ContextGeneratorMetricsLabel, generator_metrics, constructors)()
    tree = TreeInsert(tree, ContextLastProofLabel, last_proof, constructors)()
    tree = TreeInsert(tree, ContextResearchResidualsLabel, research_residuals, constructors)()
    tree = TreeInsert(tree, ContextProvenanceMapLabel, provenance_map, constructors)()
    tree = TreeInsert(tree, ContextGeneratorPolicyLabel, generator_policy, constructors)()
    tree = TreeInsert(tree, ContextLastResidualsLabel, last_residuals, constructors)()
    tree = TreeInsert(tree, ContextCounterfactualResultsLabel, counterfactual_results, constructors)()
    tree = TreeInsert(tree, ContextResearchModeLabel, research_mode, constructors)()
    tree = TreeInsert(tree, ContextResearchAttemptsLabel, research_attempts, constructors)()
    tree = TreeInsert(tree, ContextInterventionEpisodesLabel, intervention_episodes, constructors)()
    tree = TreeInsert(tree, ContextDependencyPoliciesLabel, dependency_policies, constructors)()
    return Pair(MachineContextLabel, Pair(tree, EmptyList))


class IsContext(Edge):
    def __init__(self, x):
        if IdentityCompare(x, EmptyList)() is truth_value:
            atom_result = false_value
        else:
            head = Head(x)()
            atom_result = truth_value if IdentityCompare(head, MachineContextLabel)() is truth_value else false_value
        self.result = atom_result
        super().__init__(inputs=Pair(x, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextTree(Edge):
    def __init__(self, ctx):
        if IsContext(ctx)() is false_value:
            self.result = EmptyList
        else:
            payload = Tail(ctx)()
            tree = Head(payload)()
            rest = Tail(payload)()
            if IdentityCompare(rest, EmptyList)() is truth_value:
                self.result = tree
            else:
                self.result = EmptyList
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextConstructors(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            self.result = Head(args)() if IsPair(args)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextConstructorsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextNodes(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest = Tail(args)()
                self.result = Head(rest)() if IsPair(rest)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextNodesLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextEdges(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    self.result = Head(rest2)() if IsPair(rest2)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextEdgesLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextTests(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        self.result = Head(rest3)() if IsPair(rest3)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextTestsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextTestResults(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            self.result = Head(rest4)() if IsPair(rest4)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextTestResultsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextAllRules(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            if IsPair(rest4)() is false_value:
                                self.result = EmptyList
                            else:
                                rest5 = Tail(rest4)()
                                self.result = Head(rest5)() if IsPair(rest5)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextAllRulesLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextNextRuleIndex(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            if IsPair(rest4)() is false_value:
                                self.result = EmptyList
                            else:
                                rest5 = Tail(rest4)()
                                if IsPair(rest5)() is false_value:
                                    self.result = EmptyList
                                else:
                                    rest6 = Tail(rest5)()
                                    self.result = Head(rest6)() if IsPair(rest6)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextNextRuleIndexLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextRuleOrder(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            if IsPair(rest4)() is false_value:
                                self.result = EmptyList
                            else:
                                rest5 = Tail(rest4)()
                                if IsPair(rest5)() is false_value:
                                    self.result = EmptyList
                                else:
                                    rest6 = Tail(rest5)()
                                    if IsPair(rest6)() is false_value:
                                        self.result = EmptyList
                                    else:
                                        rest7 = Tail(rest6)()
                                        self.result = Head(rest7)() if IsPair(rest7)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextRuleOrderLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextDerivations(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            if IsPair(rest4)() is false_value:
                                self.result = EmptyList
                            else:
                                rest5 = Tail(rest4)()
                                if IsPair(rest5)() is false_value:
                                    self.result = EmptyList
                                else:
                                    rest6 = Tail(rest5)()
                                    if IsPair(rest6)() is false_value:
                                        self.result = EmptyList
                                    else:
                                        rest7 = Tail(rest6)()
                                        if IsPair(rest7)() is false_value:
                                            self.result = EmptyList
                                        else:
                                            rest8 = Tail(rest7)()
                                            self.result = Head(rest8)() if IsPair(rest8)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextDerivationsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextDerivationSchemata(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            if IsPair(rest4)() is false_value:
                                self.result = EmptyList
                            else:
                                rest5 = Tail(rest4)()
                                if IsPair(rest5)() is false_value:
                                    self.result = EmptyList
                                else:
                                    rest6 = Tail(rest5)()
                                    if IsPair(rest6)() is false_value:
                                        self.result = EmptyList
                                    else:
                                        rest7 = Tail(rest6)()
                                        if IsPair(rest7)() is false_value:
                                            self.result = EmptyList
                                        else:
                                            rest8 = Tail(rest7)()
                                            if IsPair(rest8)() is false_value:
                                                self.result = EmptyList
                                            else:
                                                rest9 = Tail(rest8)()
                                                self.result = Head(rest9)() if IsPair(rest9)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextDerivationSchemataLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextSearchHistory(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            if IsPair(rest4)() is false_value:
                                self.result = EmptyList
                            else:
                                rest5 = Tail(rest4)()
                                if IsPair(rest5)() is false_value:
                                    self.result = EmptyList
                                else:
                                    rest6 = Tail(rest5)()
                                    if IsPair(rest6)() is false_value:
                                        self.result = EmptyList
                                    else:
                                        rest7 = Tail(rest6)()
                                        if IsPair(rest7)() is false_value:
                                            self.result = EmptyList
                                        else:
                                            rest8 = Tail(rest7)()
                                            if IsPair(rest8)() is false_value:
                                                self.result = EmptyList
                                            else:
                                                rest9 = Tail(rest8)()
                                                if IsPair(rest9)() is false_value:
                                                    self.result = EmptyList
                                                else:
                                                    rest10 = Tail(rest9)()
                                                    self.result = Head(rest10)() if IsPair(rest10)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextSearchHistoryLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextSearchComparisons(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            if IsPair(rest4)() is false_value:
                                self.result = EmptyList
                            else:
                                rest5 = Tail(rest4)()
                                if IsPair(rest5)() is false_value:
                                    self.result = EmptyList
                                else:
                                    rest6 = Tail(rest5)()
                                    if IsPair(rest6)() is false_value:
                                        self.result = EmptyList
                                    else:
                                        rest7 = Tail(rest6)()
                                        if IsPair(rest7)() is false_value:
                                            self.result = EmptyList
                                        else:
                                            rest8 = Tail(rest7)()
                                            if IsPair(rest8)() is false_value:
                                                self.result = EmptyList
                                            else:
                                                rest9 = Tail(rest8)()
                                                if IsPair(rest9)() is false_value:
                                                    self.result = EmptyList
                                                else:
                                                    rest10 = Tail(rest9)()
                                                    if IsPair(rest10)() is false_value:
                                                        self.result = EmptyList
                                                    else:
                                                        rest11 = Tail(rest10)()
                                                        self.result = Head(rest11)() if IsPair(rest11)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextSearchComparisonsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextSearchJobs(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            if IsPair(rest4)() is false_value:
                                self.result = EmptyList
                            else:
                                rest5 = Tail(rest4)()
                                if IsPair(rest5)() is false_value:
                                    self.result = EmptyList
                                else:
                                    rest6 = Tail(rest5)()
                                    if IsPair(rest6)() is false_value:
                                        self.result = EmptyList
                                    else:
                                        rest7 = Tail(rest6)()
                                        if IsPair(rest7)() is false_value:
                                            self.result = EmptyList
                                        else:
                                            rest8 = Tail(rest7)()
                                            if IsPair(rest8)() is false_value:
                                                self.result = EmptyList
                                            else:
                                                rest9 = Tail(rest8)()
                                                if IsPair(rest9)() is false_value:
                                                    self.result = EmptyList
                                                else:
                                                    rest10 = Tail(rest9)()
                                                    if IsPair(rest10)() is false_value:
                                                        self.result = EmptyList
                                                    else:
                                                        rest11 = Tail(rest10)()
                                                        if IsPair(rest11)() is false_value:
                                                            self.result = EmptyList
                                                        else:
                                                            rest12 = Tail(rest11)()
                                                            if IsPair(rest12)() is false_value:
                                                                self.result = EmptyList
                                                            else:
                                                                rest13 = Tail(rest12)()
                                                                self.result = Head(rest13)() if IsPair(rest13)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextSearchJobsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextSearchComparisonJobs(Edge):
    def __init__(self, ctx):
        from .machine import IsPair

        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            args = Tail(ctx)()
            if IsPair(args)() is false_value:
                self.result = EmptyList
            else:
                rest1 = Tail(args)()
                if IsPair(rest1)() is false_value:
                    self.result = EmptyList
                else:
                    rest2 = Tail(rest1)()
                    if IsPair(rest2)() is false_value:
                        self.result = EmptyList
                    else:
                        rest3 = Tail(rest2)()
                        if IsPair(rest3)() is false_value:
                            self.result = EmptyList
                        else:
                            rest4 = Tail(rest3)()
                            if IsPair(rest4)() is false_value:
                                self.result = EmptyList
                            else:
                                rest5 = Tail(rest4)()
                                if IsPair(rest5)() is false_value:
                                    self.result = EmptyList
                                else:
                                    rest6 = Tail(rest5)()
                                    if IsPair(rest6)() is false_value:
                                        self.result = EmptyList
                                    else:
                                        rest7 = Tail(rest6)()
                                        if IsPair(rest7)() is false_value:
                                            self.result = EmptyList
                                        else:
                                            rest8 = Tail(rest7)()
                                            if IsPair(rest8)() is false_value:
                                                self.result = EmptyList
                                            else:
                                                rest9 = Tail(rest8)()
                                                if IsPair(rest9)() is false_value:
                                                    self.result = EmptyList
                                                else:
                                                    rest10 = Tail(rest9)()
                                                    if IsPair(rest10)() is false_value:
                                                        self.result = EmptyList
                                                    else:
                                                        rest11 = Tail(rest10)()
                                                        if IsPair(rest11)() is false_value:
                                                            self.result = EmptyList
                                                        else:
                                                            rest12 = Tail(rest11)()
                                                            self.result = Head(rest12)() if IsPair(rest12)() is truth_value else EmptyList
        else:
            self.result = TreeLookup(tree, ContextSearchComparisonJobsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextSearchMemo(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextSearchMemoLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextNatValueIndex(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextNatValueIndexLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextDependencyRequests(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextDependencyRequestsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextDependencyGraph(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextDependencyGraphLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextGeneratorMetrics(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextGeneratorMetricsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextLastProof(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextLastProofLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextResearchResiduals(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextResearchResidualsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextProvenanceMap(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextProvenanceMapLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextGeneratorPolicy(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextGeneratorPolicyLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextLastResiduals(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextLastResidualsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextCounterfactualResults(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextCounterfactualResultsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextResearchMode(Edge):
    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextResearchModeLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextResearchAttempts(Edge):
    """Attempted-rule records collected during search, newest first.

    EmptyList when nothing has been recorded, including for checkpoints
    written before this field existed.
    """

    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextResearchAttemptsLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextInterventionEpisodes(Edge):
    """Intervention episodes: measured live-teaching outcomes, newest first.

    Each entry records residual features, the human-supplied formal rule,
    the newly enabled firings, cost before, cost after and the outcome.
    EmptyList when no live teaching has been measured, including for
    checkpoints written before this field existed.
    """

    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextInterventionEpisodesLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextDependencyPolicies(Edge):
    """Learned dependency policies, generalized from intervention episodes.

    EmptyList on a cold checkpoint: a policy exists only after at least two
    independent useful episodes were anti-unified, and resetting learned
    memory returns this field to EmptyList.
    """

    def __init__(self, ctx):
        tree = ContextTree(ctx)()
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.result = TreeLookup(tree, ContextDependencyPoliciesLabel)()
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplaceContext(Edge):
    KEEP = object()

    def __init__(
        self,
        ctx,
        constructors=KEEP,
        nodes=KEEP,
        edges=KEEP,
        tests=KEEP,
        test_results=KEEP,
        all_rules=KEEP,
        next_rule_index=KEEP,
        rule_order=KEEP,
        derivations=KEEP,
        derivation_schemata=KEEP,
        search_history=KEEP,
        search_comparisons=KEEP,
        search_comparison_jobs=KEEP,
        search_jobs=KEEP,
        search_memo=KEEP,
        nat_value_index=KEEP,
        dependency_requests=KEEP,
        dependency_graph=KEEP,
        generator_metrics=KEEP,
        last_proof=KEEP,
        research_residuals=KEEP,
        provenance_map=KEEP,
        generator_policy=KEEP,
        last_residuals=KEEP,
        counterfactual_results=KEEP,
        research_mode=KEEP,
        research_attempts=KEEP,
        intervention_episodes=KEEP,
        dependency_policies=KEEP,
    ):
        current_constructors = ContextConstructors(ctx)()
        current_nodes = ContextNodes(ctx)()
        current_edges = ContextEdges(ctx)()
        current_tests = ContextTests(ctx)()
        current_test_results = ContextTestResults(ctx)()
        current_all_rules = ContextAllRules(ctx)()
        current_next_rule_index = ContextNextRuleIndex(ctx)()
        current_rule_order = ContextRuleOrder(ctx)()
        current_derivations = ContextDerivations(ctx)()
        current_derivation_schemata = ContextDerivationSchemata(ctx)()
        current_search_history = ContextSearchHistory(ctx)()
        current_search_comparisons = ContextSearchComparisons(ctx)()
        current_search_comparison_jobs = ContextSearchComparisonJobs(ctx)()
        current_search_jobs = ContextSearchJobs(ctx)()
        current_search_memo = ContextSearchMemo(ctx)()
        current_nat_value_index = ContextNatValueIndex(ctx)()
        current_dependency_requests = ContextDependencyRequests(ctx)()
        current_dependency_graph = ContextDependencyGraph(ctx)()
        current_generator_metrics = ContextGeneratorMetrics(ctx)()
        current_last_proof = ContextLastProof(ctx)()
        current_research_residuals = ContextResearchResiduals(ctx)()
        current_provenance_map = ContextProvenanceMap(ctx)()
        current_generator_policy = ContextGeneratorPolicy(ctx)()
        current_last_residuals = ContextLastResiduals(ctx)()
        current_counterfactual_results = ContextCounterfactualResults(ctx)()
        current_research_mode = ContextResearchMode(ctx)()
        current_research_attempts = ContextResearchAttempts(ctx)()
        current_intervention_episodes = ContextInterventionEpisodes(ctx)()
        current_dependency_policies = ContextDependencyPolicies(ctx)()
        self.result = Context(
            current_constructors if constructors is self.KEEP else constructors,
            current_nodes if nodes is self.KEEP else nodes,
            current_edges if edges is self.KEEP else edges,
            current_tests if tests is self.KEEP else tests,
            current_test_results if test_results is self.KEEP else test_results,
            current_all_rules if all_rules is self.KEEP else all_rules,
            current_next_rule_index if next_rule_index is self.KEEP else next_rule_index,
            current_rule_order if rule_order is self.KEEP else rule_order,
            current_derivations if derivations is self.KEEP else derivations,
            current_derivation_schemata if derivation_schemata is self.KEEP else derivation_schemata,
            current_search_history if search_history is self.KEEP else search_history,
            current_search_comparisons if search_comparisons is self.KEEP else search_comparisons,
            current_search_comparison_jobs if search_comparison_jobs is self.KEEP else search_comparison_jobs,
            current_search_jobs if search_jobs is self.KEEP else search_jobs,
            current_search_memo if search_memo is self.KEEP else search_memo,
            current_nat_value_index if nat_value_index is self.KEEP else nat_value_index,
            current_dependency_requests if dependency_requests is self.KEEP else dependency_requests,
            current_dependency_graph if dependency_graph is self.KEEP else dependency_graph,
            current_generator_metrics if generator_metrics is self.KEEP else generator_metrics,
            current_last_proof if last_proof is self.KEEP else last_proof,
            current_research_residuals if research_residuals is self.KEEP else research_residuals,
            current_provenance_map if provenance_map is self.KEEP else provenance_map,
            current_generator_policy if generator_policy is self.KEEP else generator_policy,
            current_last_residuals if last_residuals is self.KEEP else last_residuals,
            current_counterfactual_results if counterfactual_results is self.KEEP else counterfactual_results,
            current_research_mode if research_mode is self.KEEP else research_mode,
            current_research_attempts if research_attempts is self.KEEP else research_attempts,
            current_intervention_episodes if intervention_episodes is self.KEEP else intervention_episodes,
            current_dependency_policies if dependency_policies is self.KEEP else dependency_policies,
        )
        super().__init__(inputs=Pair(ctx, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContextWithConstructors(Edge):
    def __init__(self, ctx, constructors):
        self.result = ReplaceContext(ctx, constructors=constructors)()
        super().__init__(inputs=Pair(ctx, Pair(constructors, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithNodes(Edge):
    def __init__(self, ctx, nodes):
        self.result = ReplaceContext(ctx, nodes=nodes)()
        super().__init__(inputs=Pair(ctx, Pair(nodes, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithEdges(Edge):
    def __init__(self, ctx, edges):
        self.result = ReplaceContext(ctx, edges=edges)()
        super().__init__(inputs=Pair(ctx, Pair(edges, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithTests(Edge):
    def __init__(self, ctx, tests):
        self.result = ReplaceContext(ctx, tests=tests)()
        super().__init__(inputs=Pair(ctx, Pair(tests, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithTestResults(Edge):
    def __init__(self, ctx, test_results):
        self.result = ReplaceContext(ctx, test_results=test_results)()
        super().__init__(inputs=Pair(ctx, Pair(test_results, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithAllRules(Edge):
    def __init__(self, ctx, all_rules):
        self.result = ReplaceContext(ctx, all_rules=all_rules)()
        super().__init__(inputs=Pair(ctx, Pair(all_rules, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithNextRuleIndex(Edge):
    def __init__(self, ctx, next_rule_index):
        self.result = ReplaceContext(ctx, next_rule_index=next_rule_index)()
        super().__init__(inputs=Pair(ctx, Pair(next_rule_index, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithRuleOrder(Edge):
    def __init__(self, ctx, rule_order):
        self.result = ReplaceContext(ctx, rule_order=rule_order)()
        super().__init__(inputs=Pair(ctx, Pair(rule_order, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithDerivations(Edge):
    def __init__(self, ctx, derivations):
        self.result = ReplaceContext(ctx, derivations=derivations)()
        super().__init__(inputs=Pair(ctx, Pair(derivations, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithDerivationSchemata(Edge):
    def __init__(self, ctx, derivation_schemata):
        self.result = ReplaceContext(ctx, derivation_schemata=derivation_schemata)()
        super().__init__(inputs=Pair(ctx, Pair(derivation_schemata, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithSearchHistory(Edge):
    def __init__(self, ctx, search_history):
        self.result = ReplaceContext(ctx, search_history=search_history)()
        super().__init__(inputs=Pair(ctx, Pair(search_history, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithSearchComparisons(Edge):
    def __init__(self, ctx, search_comparisons):
        self.result = ReplaceContext(ctx, search_comparisons=search_comparisons)()
        super().__init__(inputs=Pair(ctx, Pair(search_comparisons, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithSearchJobs(Edge):
    def __init__(self, ctx, search_jobs):
        self.result = ReplaceContext(ctx, search_jobs=search_jobs)()
        super().__init__(inputs=Pair(ctx, Pair(search_jobs, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithSearchComparisonJobs(Edge):
    def __init__(self, ctx, search_comparison_jobs):
        self.result = ReplaceContext(ctx, search_comparison_jobs=search_comparison_jobs)()
        super().__init__(inputs=Pair(ctx, Pair(search_comparison_jobs, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContextWithSearchMemo(Edge):
    def __init__(self, ctx, search_memo):
        self.result = ReplaceContext(ctx, search_memo=search_memo)()
        super().__init__(inputs=Pair(ctx, Pair(search_memo, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class HypergraphContext(Edge):
    def __init__(self, graph):
        self.result = graph.context
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetConstructors(Edge):
    def __init__(self, graph):
        self.result = ContextConstructors(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetNodes(Edge):
    def __init__(self, graph):
        self.result = ContextNodes(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetEdges(Edge):
    def __init__(self, graph):
        self.result = ContextEdges(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetTests(Edge):
    def __init__(self, graph):
        self.result = ContextTests(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetTestResults(Edge):
    def __init__(self, graph):
        self.result = ContextTestResults(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetAllRules(Edge):
    def __init__(self, graph):
        self.result = ContextAllRules(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetRuleOrder(Edge):
    def __init__(self, graph):
        self.result = ContextRuleOrder(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetDerivations(Edge):
    def __init__(self, graph):
        self.result = ContextDerivations(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetDerivationSchemata(Edge):
    def __init__(self, graph):
        self.result = ContextDerivationSchemata(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetSearchHistory(Edge):
    def __init__(self, graph):
        self.result = ContextSearchHistory(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetSearchComparisons(Edge):
    def __init__(self, graph):
        self.result = ContextSearchComparisons(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetSearchJobs(Edge):
    def __init__(self, graph):
        self.result = ContextSearchJobs(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetSearchComparisonJobs(Edge):
    def __init__(self, graph):
        self.result = ContextSearchComparisonJobs(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetSearchMemo(Edge):
    def __init__(self, graph):
        self.result = ContextSearchMemo(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetNatValueIndex(Edge):
    def __init__(self, graph):
        self.result = ContextNatValueIndex(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetDependencyRequests(Edge):
    def __init__(self, graph):
        self.result = ContextDependencyRequests(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetDependencyGraph(Edge):
    def __init__(self, graph):
        self.result = ContextDependencyGraph(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetGeneratorMetrics(Edge):
    def __init__(self, graph):
        self.result = ContextGeneratorMetrics(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetLastProof(Edge):
    def __init__(self, graph):
        self.result = ContextLastProof(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetResearchResiduals(Edge):
    def __init__(self, graph):
        self.result = ContextResearchResiduals(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetProvenanceMap(Edge):
    def __init__(self, graph):
        self.result = ContextProvenanceMap(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetGeneratorPolicy(Edge):
    def __init__(self, graph):
        self.result = ContextGeneratorPolicy(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetLastResiduals(Edge):
    def __init__(self, graph):
        self.result = ContextLastResiduals(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetCounterfactualResults(Edge):
    def __init__(self, graph):
        self.result = ContextCounterfactualResults(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetInterventionEpisodes(Edge):
    def __init__(self, graph):
        self.result = ContextInterventionEpisodes(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetDependencyPolicies(Edge):
    def __init__(self, graph):
        self.result = ContextDependencyPolicies(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FromContextGetResearchMode(Edge):
    def __init__(self, graph):
        self.result = ContextResearchMode(HypergraphContext(graph)())()
        super().__init__(inputs=Pair(graph, EmptyList), results=self.result)

    def __call__(self):
        return self.result


def sync_from_namespace(namespace):
    for name in (
        "EmptyList",
        "truth_value",
        "false_value",
        "MachineContextLabel",
        "ContextConstructorsLabel",
        "ContextNodesLabel",
        "ContextEdgesLabel",
        "ContextTestsLabel",
        "ContextTestResultsLabel",
        "ContextAllRulesLabel",
        "ContextNextRuleIndexLabel",
        "ContextRuleOrderLabel",
        "ContextDerivationsLabel",
        "ContextDerivationSchemataLabel",
        "ContextSearchHistoryLabel",
        "ContextSearchComparisonsLabel",
        "ContextSearchComparisonJobsLabel",
        "ContextSearchJobsLabel",
        "ContextSearchMemoLabel",
        "ContextNatValueIndexLabel",
        "ContextDependencyRequestsLabel",
        "ContextDependencyGraphLabel",
        "ContextGeneratorMetricsLabel",
        "ContextLastProofLabel",
        "ContextResearchResidualsLabel",
        "ContextProvenanceMapLabel",
        "ContextGeneratorPolicyLabel",
        "ContextLastResidualsLabel",
        "ContextCounterfactualResultsLabel",
        "ContextResearchModeLabel",
        "ContextInterventionEpisodesLabel",
        "ContextDependencyPoliciesLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_")]
