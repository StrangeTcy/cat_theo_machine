from pathlib import Path
from cat_theo_machine.training import ObligationSkeletonConclusionGoal, TrainingRecordLoader
from cat_theo_machine import machine as M
from cat_theo_machine.main import _runtime_namespace

loader = TrainingRecordLoader(_runtime_namespace())
record, unused = loader.load_records_file(str(Path(__file__).with_name("d21-distinct-final.yaml")))[0]
skeleton = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
selected = ObligationSkeletonConclusionGoal(skeleton)()
rendered = M.PrettyTerm(selected, _runtime_namespace())()
assert rendered == "Knowledge([Q])", rendered
print("distinct_final_goal_selected_test: PASS")
