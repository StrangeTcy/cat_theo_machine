"""Structural regression for the symbolic live sieve lesson.

The test discovers lesson records by their machine constructor heads. It does
not supply answers for numbers, enumerate survivors, or compare a finite
result table.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hyge import labels as L
from hyge import machine as M
from hyge import main
from hyge import training as T
from hyge.runtime import boot_from_packs

runtime, packs = boot_from_packs(main.PACK_PATHS, main._runtime_namespace())
loader = T.TrainingRecordLoader(main._runtime_namespace())
records = loader.load_records_file(
    os.path.join(ROOT, "training_records", "sieve_eratosthenes_live.yaml"),
)

saw_step = M.false_value
saw_trial = M.false_value
saw_induction = M.false_value
saw_forall = M.false_value

for record_pair in records:
    record = record_pair[0]
    start = T.TrainingRecordMeaningStructure(record)()
    facts = M.Tail(start)()
    if M.IdentityCompare(facts, M.EmptyList)() is M.false_value:
        head = M.Head(M.Head(facts)())()
        if M.IdentityCompare(head, L.SieveStepLabel)() is M.truth_value:
            saw_step = M.truth_value
        if M.IdentityCompare(head, L.SqrtTrialLabel)() is M.truth_value:
            saw_trial = M.truth_value

    hint = T.TrainingRecordStrategyHint(record)()
    if M.IdentityCompare(hint, M.EmptyList)() is M.false_value:
        if M.IdentityCompare(M.Head(hint)(), L.InductionLabel)() is M.truth_value:
            saw_induction = M.truth_value

    skeleton = T.TrainingRecordObligationSkeleton(record)()
    remaining = skeleton
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        goal = T.ObligationSkeletonEntryGoal(M.Head(remaining)())()
        if M.IdentityCompare(goal, M.EmptyList)() is M.false_value:
            goal_facts = M.Head(M.Tail(goal)())()
            if M.IdentityCompare(M.Head(goal_facts)(), L.ForAllLabel)() is M.truth_value:
                saw_forall = M.truth_value
        remaining = M.Tail(remaining)()

assert M.IdentityCompare(saw_step, M.truth_value)() is M.truth_value
assert M.IdentityCompare(saw_trial, M.truth_value)() is M.truth_value
assert M.IdentityCompare(saw_induction, M.truth_value)() is M.truth_value
assert M.IdentityCompare(saw_forall, M.truth_value)() is M.truth_value

number_pack = packs.by_name("number-theory")
assert "composite_has_nontrivial_sqrt_bounded_divisor" in number_pack.rule_map
assert "sieve_extensional_equivalence_induction" in number_pack.schema_map
print("symbolic sieve lesson and induction theorem schema loaded")
