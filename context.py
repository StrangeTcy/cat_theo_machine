from __future__ import annotations

from .core import Edge, EmptyList, Head, IdentityCompare, Pair, Tail, false_value, truth_value
from .labels import (
    ContextAllRulesLabel,
    ContextConstructorsLabel,
    ContextDerivationsLabel,
    ContextDerivationSchemataLabel,
    ContextEdgesLabel,
    ContextNextRuleIndexLabel,
    ContextNodesLabel,
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
):
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
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_")]
