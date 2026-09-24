from __future__ import annotations

import copyreg
import multiprocessing
import queue
import sys
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
from .engine import SearchAStar, SearchBFS, SearchBeam, SearchDFS, SearchRewriteDFS
class Search(M.Edge):
    def __init__(self, graph, start, goal, rules, heuristic, registry):
        mode = HeuristicSearchMode(heuristic)()
        if M.IdentityCompare(mode, DFSLabel)() is M.truth_value:
            atom_result = SearchDFS(graph, start, goal, rules, heuristic, registry)()
        elif M.IdentityCompare(mode, BFSLabel)() is M.truth_value:
            atom_result = SearchBFS(graph, start, goal, rules, heuristic, registry)()
        elif M.IdentityCompare(mode, AStarLabel)() is M.truth_value:
            atom_result = SearchAStar(graph, start, goal, rules, heuristic, registry)()
        elif M.IdentityCompare(mode, BeamLabel)() is M.truth_value:
            atom_result = SearchBeam(graph, start, goal, rules, heuristic, registry)()
        elif M.IdentityCompare(mode, RewriteDFSLabel)() is M.truth_value:
            atom_result = SearchRewriteDFS(graph, start, goal, rules, heuristic, registry)()
        else:
            raise RuntimeError("Search mode not implemented")
        self.result = atom_result
        super().__init__(inputs=M.Pair(graph, M.Pair(start, M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.Pair(registry, M.EmptyList)))))), results=self.result)

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
