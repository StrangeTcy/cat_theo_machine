"""Regression for the live symbolic sieve lesson."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hyge import labels as L
from hyge import machine as M
from hyge import main
from hyge.runtime import boot_from_packs
from hyge.sieve_theory import SieveInductionPlan, TeachSieveLesson

runtime, packs = boot_from_packs(main.PACK_PATHS, main._runtime_namespace())
variable = M.Pair(M.VarTag, M.Pair(M.Char("n"), M.EmptyList))
lesson = TeachSieveLesson(runtime.graph, variable)()
step = M.Head(lesson)()
trial = M.Head(M.Tail(lesson)())()
theorem = M.Head(M.Tail(M.Tail(lesson)())())()

assert M.IdentityCompare(M.Head(step)(), L.SieveStepLabel)() is M.truth_value
assert M.IdentityCompare(M.Head(trial)(), L.SqrtTrialLabel)() is M.truth_value
assert M.IdentityCompare(M.Head(theorem)(), L.ForAllLabel)() is M.truth_value

step_fields = M.Tail(step)()
trial_fields = M.Tail(trial)()
assert M.IdentityCompare(M.Head(step_fields)(), variable)() is M.truth_value
assert M.IdentityCompare(M.Head(trial_fields)(), variable)() is M.truth_value

step_tail = M.Tail(M.Tail(step_fields)())()
trial_tail = M.Tail(M.Tail(trial_fields)())()
assert M.IdentityCompare(M.Head(step_tail)(), M.two)() is M.truth_value
assert M.IdentityCompare(M.Head(trial_tail)(), M.two)() is M.truth_value

induction = SieveInductionPlan(variable)()
obligations = M.Head(M.Tail(induction)())()
assert M.IdentityCompare(obligations, M.EmptyList)() is M.false_value

pack = packs.by_name("number-theory")
assert "composite_has_nontrivial_sqrt_bounded_divisor" in pack.rule_map
assert M.IdentityCompare(
    M.Head(M.Tail(M.Tail(induction)())())(),
    theorem,
)() is M.truth_value
print("live sieve lesson, induction obligations, and theorem registration passed")
