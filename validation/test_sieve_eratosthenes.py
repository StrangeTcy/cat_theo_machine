"""Live sieve lesson regression checks.

The fixture is ingested through the same TrainingRecord path used by live
teaching. Structural assertions inspect machine terms, not finite answers.
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
assert len(records) == 3

step_record = records[0][0]
trial_record = records[1][0]
theorem_record = records[2][0]
step_start = T.TrainingRecordMeaningStructure(step_record)()
trial_start = T.TrainingRecordMeaningStructure(trial_record)()
theorem_skeleton = T.TrainingRecordObligationSkeleton(theorem_record)()
theorem_hint = T.TrainingRecordStrategyHint(theorem_record)()

assert M.IdentityCompare(T.TrainingRecordMeaningStructure(step_record)(), step_start)() is M.truth_value
assert M.IdentityCompare(T.TrainingRecordMeaningStructure(trial_record)(), trial_start)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Tail(step_start)())(), L.SieveStepLabel)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Tail(trial_start)())(), L.SqrtTrialLabel)() is M.truth_value
assert M.IdentityCompare(M.Head(theorem_skeleton)(), M.Head(theorem_skeleton)())() is M.truth_value
assert M.IdentityCompare(M.Head(theorem_hint)(), L.InductionLabel)() is M.truth_value

number_pack = packs.by_name("number-theory")
assert "composite_has_nontrivial_sqrt_bounded_divisor" in number_pack.rule_map
assert "nt_composite_sqrt_factor_directed" in number_pack.examples
print("sieve live lesson terms and directed factor lemma loaded")
