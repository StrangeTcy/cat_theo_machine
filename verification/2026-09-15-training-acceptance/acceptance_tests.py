from pathlib import Path
from cat_theo_machine.training import ObligationSkeletonConclusionGoal, TrainingRecordLoader
from cat_theo_machine import machine as M
from cat_theo_machine.main import _runtime_namespace

fixture = Path(__file__).resolve().parents[2] / "training_records" / "engel_e2_blackboard_parity.yaml"
loader = TrainingRecordLoader(_runtime_namespace())
records = loader.load_records_file(str(fixture))
record = records[0][0]
skeleton = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
selected = ObligationSkeletonConclusionGoal(skeleton)()
assert M.IdentityCompare(selected, M.EmptyList)() is M.false_value
print("skeleton_final_goal_selected_test: PASS")
print("training_record_fixture_load_test: PASS")
print("registered: 2")
