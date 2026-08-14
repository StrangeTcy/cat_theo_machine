from __future__ import annotations

from . import machine as M
from .heuristics import HeuristicGoalHeadAllowsSubterm
from .labels import *


class GoalDemandRewriteStrategy(M.Edge):
    def __init__(self):
        self.result = M.Pair(GoalDemandRewriteStrategyLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PremiseUnlockRewriteStrategy(M.Edge):
    def __init__(self):
        self.result = M.Pair(PremiseUnlockRewriteStrategyLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RewriteStrategyAllowsSubterm(M.Edge):
    def __init__(self, strategy, goal_head_index, subterm, registry):
        self.result = M.false_value
        if M.IsPair(strategy)() is M.truth_value:
            strategy_label = M.Head(strategy)()
            if M.IdentityCompare(strategy_label, GoalDemandRewriteStrategyLabel)() is M.truth_value:
                self.result = HeuristicGoalHeadAllowsSubterm(goal_head_index, subterm, registry)()
            elif M.IdentityCompare(strategy_label, PremiseUnlockRewriteStrategyLabel)() is M.truth_value:
                self.result = M.false_value
        super().__init__(
            inputs=M.Pair(strategy, M.Pair(goal_head_index, M.Pair(subterm, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
