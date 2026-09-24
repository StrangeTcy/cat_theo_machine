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
def _search_pickled_singleton(name):
    if name == "EmptyList":
        return M.EmptyList
    if name == "Zero":
        return M.Zero
    if name == "VarTag":
        return M.VarTag
    if name == "truth_value":
        return M.truth_value
    if name == "false_value":
        return M.false_value
    if name == "LPAREN":
        return M.LPAREN
    if name == "RPAREN":
        return M.RPAREN
    if name == "COMMA":
        return M.COMMA
    if name == "SPACE":
        return M.SPACE
    if name == "LBRACK":
        return M.LBRACK
    if name == "RBRACK":
        return M.RBRACK
    if name == "one":
        return M.one
    if name == "two":
        return M.two
    if name == "three":
        return M.three
    if name == "four":
        return M.four
    if name == "five":
        return M.five
    if name == "six":
        return M.six
    if name == "seven":
        return M.seven
    if name == "eight":
        return M.eight
    if name == "nine":
        return M.nine
    if name == "TreeLabel":
        return Lmod.TreeLabel
    if name == "ZeroLabel":
        return Lmod.ZeroLabel
    if name == "SuccLabel":
        return Lmod.SuccLabel
    if name == "PairLabel":
        return Lmod.PairLabel
    if name == "ThingyLabel":
        return Lmod.ThingyLabel
    if name == "HypergraphLabel":
        return Lmod.HypergraphLabel
    if name == "TestLabel":
        return Lmod.TestLabel
    if name == "TestOKLabel":
        return Lmod.TestOKLabel
    if name == "TestFailLabel":
        return Lmod.TestFailLabel
    if name == "TestNameLabel":
        return Lmod.TestNameLabel
    if name == "SequenceLabel":
        return Lmod.SequenceLabel
    if name == "LimitLabel":
        return Lmod.LimitLabel
    if name == "IsCauchyLabel":
        return Lmod.IsCauchyLabel
    if name == "RealNumLabel":
        return Lmod.RealNumLabel
    if name == "IsRealLabel":
        return Lmod.IsRealLabel
    if name == "SqrtLabel":
        return Lmod.SqrtLabel
    if name == "SqrtSeqTermLabel":
        return Lmod.SqrtSeqTermLabel
    if name == "NewtonStepTermLabel":
        return Lmod.NewtonStepTermLabel
    if name == "NewtonPositiveLabel":
        return Lmod.NewtonPositiveLabel
    if name == "NewtonErrorIdentityLabel":
        return Lmod.NewtonErrorIdentityLabel
    if name == "NewtonErrorShrinksLabel":
        return Lmod.NewtonErrorShrinksLabel
    if name == "SqrtSeqCauchyLabel":
        return Lmod.SqrtSeqCauchyLabel
    if name == "FractionLabel":
        return Lmod.FractionLabel
    if name == "WholeLabel":
        return Lmod.WholeLabel
    if name == "ExprAddLabel":
        return Lmod.ExprAddLabel
    if name == "ExprMulLabel":
        return Lmod.ExprMulLabel
    if name == "ExprFracLabel":
        return Lmod.ExprFracLabel
    if name == "ExprDivLabel":
        return Lmod.ExprDivLabel
    if name == "ExprPowLabel":
        return Lmod.ExprPowLabel
    if name == "ExprIntLabel":
        return Lmod.ExprIntLabel
    if name == "ExprNegLabel":
        return Lmod.ExprNegLabel
    if name == "ExprEqLabel":
        return Lmod.ExprEqLabel
    if name == "ExprLtLabel":
        return Lmod.ExprLtLabel
    if name == "ExprLeLabel":
        return Lmod.ExprLeLabel
    if name == "DFSLabel":
        return Lmod.DFSLabel
    if name == "BFSLabel":
        return Lmod.BFSLabel
    if name == "BeamLabel":
        return Lmod.BeamLabel
    if name == "AStarLabel":
        return Lmod.AStarLabel
    if name == "RewriteDFSLabel":
        return Lmod.RewriteDFSLabel
    if name == "InsertionOrderLabel":
        return Lmod.InsertionOrderLabel
    if name == "GoalHeadOrderLabel":
        return Lmod.GoalHeadOrderLabel
    if name == "KnowledgeLabel":
        return Lmod.KnowledgeLabel
    if name == "StepLabel":
        return Lmod.StepLabel
    if name == "DerivationLabel":
        return Lmod.DerivationLabel
    if name == "TheoremActionLabel":
        return Lmod.TheoremActionLabel
    if name == "RewriteActionLabel":
        return Lmod.RewriteActionLabel
    if name == "MachineContextLabel":
        return Lmod.MachineContextLabel
    if name == "ContextConstructorsLabel":
        return Lmod.ContextConstructorsLabel
    if name == "ContextNodesLabel":
        return Lmod.ContextNodesLabel
    if name == "ContextEdgesLabel":
        return Lmod.ContextEdgesLabel
    if name == "ContextTestsLabel":
        return Lmod.ContextTestsLabel
    if name == "ContextTestResultsLabel":
        return Lmod.ContextTestResultsLabel
    if name == "ContextAllRulesLabel":
        return Lmod.ContextAllRulesLabel
    if name == "ContextNextRuleIndexLabel":
        return Lmod.ContextNextRuleIndexLabel
    if name == "ContextRuleOrderLabel":
        return Lmod.ContextRuleOrderLabel
    if name == "ContextDerivationsLabel":
        return Lmod.ContextDerivationsLabel
    if name == "ContextDerivationSchemataLabel":
        return Lmod.ContextDerivationSchemataLabel
    if name == "ContextSearchHistoryLabel":
        return Lmod.ContextSearchHistoryLabel
    if name == "ContextSearchComparisonsLabel":
        return Lmod.ContextSearchComparisonsLabel
    if name == "ContextSearchJobsLabel":
        return Lmod.ContextSearchJobsLabel
    if name == "ContextSearchComparisonJobsLabel":
        return Lmod.ContextSearchComparisonJobsLabel
    if name == "ContextSearchMemoLabel":
        return Lmod.ContextSearchMemoLabel
    if name == "ProofCostLabel":
        return Lmod.ProofCostLabel
    if name == "SearchCostLabel":
        return Lmod.SearchCostLabel
    if name == "TotalCostLabel":
        return Lmod.TotalCostLabel
    if name == "SearchAttemptLabel":
        return Lmod.SearchAttemptLabel
    if name == "SearchSignatureLabel":
        return Lmod.SearchSignatureLabel
    if name == "SearchComparisonLabel":
        return Lmod.SearchComparisonLabel
    if name == "SearchComparisonJobLabel":
        return Lmod.SearchComparisonJobLabel
    if name == "SearchJobLabel":
        return Lmod.SearchJobLabel
    if name == "SearchStateLabel":
        return Lmod.SearchStateLabel
    if name == "SearchTheoremCursorLabel":
        return Lmod.SearchTheoremCursorLabel
    if name == "SearchRewriteCursorLabel":
        return Lmod.SearchRewriteCursorLabel
    if name == "SearchRewritePathFrameLabel":
        return Lmod.SearchRewritePathFrameLabel
    if name == "SearchRewriteRuleBundleLabel":
        return Lmod.SearchRewriteRuleBundleLabel
    if name == "SearchPairKeyLabel":
        return Lmod.SearchPairKeyLabel
    if name == "SearchCtorKeyLabel":
        return Lmod.SearchCtorKeyLabel
    if name == "SearchSuccessLabel":
        return Lmod.SearchSuccessLabel
    if name == "SearchFailureLabel":
        return Lmod.SearchFailureLabel
    if name == "SearchRunningLabel":
        return Lmod.SearchRunningLabel
    if name == "SearchPausedLabel":
        return Lmod.SearchPausedLabel
    if name == "SearchTimedOutLabel":
        return Lmod.SearchTimedOutLabel
    if name == "SearchAbortedByUserLabel":
        return Lmod.SearchAbortedByUserLabel
    if name == "SearchRootFastPathPhaseLabel":
        return Lmod.SearchRootFastPathPhaseLabel
    if name == "SearchPacketSearchPhaseLabel":
        return Lmod.SearchPacketSearchPhaseLabel
    if name == "SearchNoRootFastPathLabel":
        return Lmod.SearchNoRootFastPathLabel
    if name == "SearchRootCacheResultLabel":
        return Lmod.SearchRootCacheResultLabel
    if name == "SearchRootSchemaResultLabel":
        return Lmod.SearchRootSchemaResultLabel
    if name == "SearchRootGoalResultLabel":
        return Lmod.SearchRootGoalResultLabel
    if name == "SearchRootImmediateResultLabel":
        return Lmod.SearchRootImmediateResultLabel
    try:
        return getattr(Lmod, name)
    except AttributeError:
        pass
    raise RuntimeError("Unknown worker singleton: " + name)


def _search_rebuild_plain_atom(value):
    atom = M.Atom()
    atom.value = value
    return atom


def _search_reduce_plain_atom(atom):
    if atom is M.Zero:
        return _search_pickled_singleton, ("Zero",)
    if atom is M.one:
        return _search_pickled_singleton, ("one",)
    if atom is M.two:
        return _search_pickled_singleton, ("two",)
    if atom is M.three:
        return _search_pickled_singleton, ("three",)
    if atom is M.four:
        return _search_pickled_singleton, ("four",)
    if atom is M.five:
        return _search_pickled_singleton, ("five",)
    if atom is M.six:
        return _search_pickled_singleton, ("six",)
    if atom is M.seven:
        return _search_pickled_singleton, ("seven",)
    if atom is M.eight:
        return _search_pickled_singleton, ("eight",)
    if atom is M.nine:
        return _search_pickled_singleton, ("nine",)
    return _search_rebuild_plain_atom, (atom.value,)


def _search_rebuild_plain_thingy(value):
    atom = M.Thingy()
    atom.value = value
    return atom


def _search_reduce_plain_thingy(atom):
    if atom is M.EmptyList:
        return _search_pickled_singleton, ("EmptyList",)
    return _search_rebuild_plain_thingy, (atom.value,)


def _search_reduce_truth_value(_atom):
    return _search_pickled_singleton, ("truth_value",)


def _search_reduce_false_value(_atom):
    return _search_pickled_singleton, ("false_value",)


def _search_reduce_var_tag(_atom):
    return _search_pickled_singleton, ("VarTag",)


def _search_rebuild_char(symbol):
    return M.Char(symbol)


def _search_reduce_char(atom):
    symbol = atom.symbol
    if symbol == "(":
        return _search_pickled_singleton, ("LPAREN",)
    if symbol == ")":
        return _search_pickled_singleton, ("RPAREN",)
    if symbol == ",":
        return _search_pickled_singleton, ("COMMA",)
    if symbol == " ":
        return _search_pickled_singleton, ("SPACE",)
    if symbol == "[":
        return _search_pickled_singleton, ("LBRACK",)
    if symbol == "]":
        return _search_pickled_singleton, ("RBRACK",)
    return _search_rebuild_char, (symbol,)


def _search_reduce_constructor_label(atom):
    return _search_pickled_singleton, (atom.__class__.__name__,)


def _install_search_worker_pickle_support():
    Lmod.ConstructorLabel.__reduce__ = _search_reduce_constructor_label
    copyreg.pickle(M.Atom, _search_reduce_plain_atom)
    copyreg.pickle(M.Thingy, _search_reduce_plain_thingy)
    copyreg.pickle(M.Same, _search_reduce_truth_value)
    copyreg.pickle(M.Diff, _search_reduce_false_value)
    copyreg.pickle(M.VarTag.__class__, _search_reduce_var_tag)
    copyreg.pickle(M.Char, _search_reduce_char)


_install_search_worker_pickle_support()

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
