from __future__ import annotations

import importlib


_MISSING = object()
_SEARCH_MODULES = (
    "serialization",
    "ui",
    "chain_utils",
    "model",
    "patricia",
    "engine",
    "runtime",
    "compare_console",
    "compare_nat",
    "compare_trees",
    "compare_state",
    "compare_attempts",
    "compare_rules",
    "compare_semantics",
    "compare",
    "api",
)


def __getattr__(name):
    for module_name in _SEARCH_MODULES:
        module = importlib.import_module("." + module_name, __name__)
        value = getattr(module, name, _MISSING)
        if value is not _MISSING:
            globals()[name] = value
            return value
    raise AttributeError("module " + __name__ + " has no attribute " + repr(name))


def sync_from_namespace(namespace):
    for module_name in _SEARCH_MODULES:
        module = importlib.import_module("." + module_name, __name__)
        module.sync_from_namespace(namespace)
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
        "SearchComparisonJobProblemLabel",
        "SearchComparisonJobRuntimeLabel",
        "SearchComparisonSummaryLabel",
        "SearchCostLabel",
        "SearchJobLabel",
        "SearchJobProgressLabel",
        "SearchJobStoresLabel",
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
        "SearchRootImmediateResultLabel",
        "SearchWorkerBaselineProblemLabel",
        "SearchWorkerPacketStoresLabel",
        "SearchWorkerPacketControlsLabel",
        "SearchWorkerLaunchDispatchLabel",
        "SearchWorkerMetricsLabel",
        "SearchWorkerPayloadLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = ()
