"""Symbolic sieve lesson and induction hand-off.

This module contains no numeric sieve evaluator. It builds the same machine
terms that the live lesson teaches and hands the universal claim to the
existing planner and derivation-schema store.
"""

from . import labels as L
from . import machine as M
from . import planner as P


class SieveStepDefinition(M.Edge):
    def __init__(self, variable):
        candidate = M.Pair(M.VarTag, M.Pair(M.Char("candidate"), M.EmptyList))
        survivor = M.Pair(M.VarTag, M.Pair(M.Char("survivor"), M.EmptyList))
        least = M.Pair(
            L.NatLessLabel,
            M.Pair(survivor, M.Pair(candidate, M.EmptyList)),
        )
        removal = M.Pair(
            L.DividesLabel,
            M.Pair(survivor, M.Pair(candidate, M.EmptyList)),
        )
        self.result = M.Pair(
            L.SieveStepLabel,
            M.Pair(
                variable,
                M.Pair(M.two, M.Pair(least, M.Pair(removal, M.EmptyList))),
            ),
        )
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SqrtTrialDefinition(M.Edge):
    def __init__(self, variable):
        divisor = M.Pair(M.VarTag, M.Pair(M.Char("divisor"), M.EmptyList))
        bound = M.Pair(
            L.NatLessLabel,
            M.Pair(
                divisor,
                M.Pair(
                    M.Pair(L.SuccLabel, M.Pair(M.Pair(L.SqrtLabel, M.Pair(variable, M.EmptyList)), M.EmptyList)),
                    M.EmptyList,
                ),
            ),
        )
        divides = M.Pair(
            L.DividesLabel,
            M.Pair(divisor, M.Pair(variable, M.EmptyList)),
        )
        self.result = M.Pair(
            L.SqrtTrialLabel,
            M.Pair(
                variable,
                M.Pair(M.two, M.Pair(bound, M.Pair(divides, M.EmptyList))),
            ),
        )
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SieveEquivalenceTheorem(M.Edge):
    def __init__(self, variable):
        step = SieveStepDefinition(variable)()
        trial = SqrtTrialDefinition(variable)()
        step_member = M.Pair(L.SieveMemberLabel, M.Pair(step, M.EmptyList))
        trial_member = M.Pair(L.SieveMemberLabel, M.Pair(trial, M.EmptyList))
        equivalence = M.Pair(
            L.ExtensionalEquivalentLabel,
            M.Pair(step_member, M.Pair(trial_member, M.EmptyList)),
        )
        self.result = M.Pair(L.ForAllLabel, M.Pair(variable, M.Pair(equivalence, M.EmptyList)))
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SieveInductionPlan(M.Edge):
    def __init__(self, variable):
        theorem = SieveEquivalenceTheorem(variable)()
        property_term = M.Head(M.Tail(theorem)())()
        method = P.Induction(variable, M.Zero, property_term)()
        obligations = P.InductionObligations(method, M.Char("k"))()
        self.result = M.Pair(method, M.Pair(obligations, M.Pair(theorem, M.EmptyList)))
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TeachSieveLesson(M.Edge):
    def __init__(self, graph, variable):
        step = SieveStepDefinition(variable)()
        trial = SqrtTrialDefinition(variable)()
        plan = SieveInductionPlan(variable)()
        theorem = M.Head(M.Tail(M.Tail(plan)())())()
        graph.add_derivation_schema(step, trial, M.EmptyList)
        graph.add_derivation_schema(trial, theorem, M.EmptyList)
        self.result = M.Pair(step, M.Pair(trial, M.Pair(theorem, M.EmptyList)))
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result
