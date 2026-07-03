from __future__ import annotations


import multiprocessing
import queue
import threading
import time

from .. import machine as M
from .. import heuristics as Hmod
from .. import labels as Lmod
from .. import proof as Pmod
from .. import context as Ctxmod
from .. import schemata as Smod
from .. import gmprep as Gmpmod
from .. import trees as Tmod
from .. import logic as Logicmod
from ..heuristics import *
from ..labels import *
from ..proof import *
from ..proof import _debug, _debug_term











class SearchCost(M.Edge):
    def __init__(self, value, expanded, generated, frontier_peak, found_depth, outcome):
        self.result = M.Pair(
            SearchCostLabel,
            M.Pair(
                value,
                M.Pair(
                    expanded,
                    M.Pair(generated, M.Pair(frontier_peak, M.Pair(found_depth, M.Pair(outcome, M.EmptyList)))),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                value,
                M.Pair(
                    expanded,
                    M.Pair(generated, M.Pair(frontier_peak, M.Pair(found_depth, M.Pair(outcome, M.EmptyList)))),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchArgs(M.Edge):
    def __init__(self, term):
        if M.IsPair(term)() is M.truth_value:
            self.result = M.Tail(term)()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchChainDrop(M.Edge):
    def __init__(self, chain, count):
        remaining_chain = chain
        remaining_count = count
        while M.IsPair(remaining_chain)() is M.truth_value:
            if M.NatEq(remaining_count, M.Zero, M.AllConstructors)() is M.truth_value:
                break
            next_count_pair = M.NatPred(remaining_count, M.AllConstructors)()
            remaining_count = M.Head(next_count_pair)()
            remaining_chain = M.Tail(remaining_chain)()
        if M.IsPair(remaining_chain)() is M.truth_value:
            if M.NatEq(remaining_count, M.Zero, M.AllConstructors)() is M.truth_value:
                self.result = remaining_chain
            else:
                self.result = M.EmptyList
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(chain, M.Pair(count, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchChainHead(M.Edge):
    def __init__(self, chain):
        if M.IsPair(chain)() is M.truth_value:
            self.result = M.Head(chain)()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchChainAt(M.Edge):
    def __init__(self, chain, index):
        self.result = SearchChainHead(SearchChainDrop(chain, index)())()
        super().__init__(inputs=M.Pair(chain, M.Pair(index, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchChainHasAt(M.Edge):
    def __init__(self, chain, index):
        dropped = SearchChainDrop(chain, index)()
        if M.IsPair(dropped)() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(chain, M.Pair(index, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchArgAt(M.Edge):
    def __init__(self, term, index):
        self.result = SearchChainAt(SearchArgs(term)(), index)()
        super().__init__(inputs=M.Pair(term, M.Pair(index, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchArgsFrom(M.Edge):
    def __init__(self, term, index):
        self.result = SearchChainDrop(SearchArgs(term)(), index)()
        super().__init__(inputs=M.Pair(term, M.Pair(index, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result

def sync_from_namespace(namespace):
    for name in (
        "DFSLabel",
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
        "RewriteDFSLabel",
        "GoalHeadOrderLabel",
        "KnowledgeLabel",
        "ContextSearchComparisonJobsLabel",
        "ContextSearchJobsLabel",
        "SearchSignatureLabel",
        "SearchComparisonLabel",
        "SearchComparisonJobLabel",
        "SearchCostLabel",
        "SearchJobLabel",
        "SearchStateLabel",
        "SearchTheoremCursorLabel",
        "SearchRewriteCursorLabel",
        "SearchRewritePathFrameLabel",
        "SearchRewriteRuleBundleLabel",
        "SearchPairKeyLabel",
        "SearchCtorKeyLabel",
        "SearchPatriciaTokenLabel",
        "SearchPatriciaPairTokenLabel",
        "SearchPatriciaStopTokenLabel",
        "SearchPatriciaLeafLabel",
        "SearchPatriciaBranchLabel",
        "SearchPatriciaChoiceLabel",
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchRunningLabel",
        "SearchPausedLabel",
        "SearchTimedOutLabel",
        "SearchAbortedByUserLabel",
        "SearchRootFastPathPhaseLabel",
        "SearchPacketSearchPhaseLabel",
        "SearchNoRootFastPathLabel",
        "SearchRootCacheResultLabel",
        "SearchRootSchemaResultLabel",
        "SearchRootGoalResultLabel",
        "SearchRootImmediateResultLabel"
    ):
        if name in namespace:
            globals()[name] = namespace[name]
