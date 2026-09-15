from pathlib import Path
from cat_theo_machine.training import ObligationSkeletonEntryGoal, ObligationSkeletonConclusionGoal, TrainingRecordLoader
from cat_theo_machine import machine as M
from cat_theo_machine.main import _runtime_namespace

loader = TrainingRecordLoader(_runtime_namespace())
fixture = Path(__file__).with_name("d22-vacuous-success.yaml")
record, unused_rules = loader.load_records_file(str(fixture))[0]
skeleton = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
selected = ObligationSkeletonConclusionGoal(skeleton)()

# D21: the final goal-bearing entry is the conclusion, not the initial restatement.
initial = M.Head(skeleton)()
selected_text = M.PrettyTerm(selected, _runtime_namespace())()
initial_text = M.PrettyTerm(ObligationSkeletonEntryGoal(initial)(), _runtime_namespace())()
assert selected_text == initial_text
assert selected_text == "Knowledge([Parity(2, Odd)])"
print("vacuous_two_obligation_fixture_test: PASS")
print("initial_restatement_not_conclusion_test: PASS")

# D22 structural regression: the underivable middle entry is present before the
# final conclusion and therefore cannot be silently treated as the conclusion.
middle = M.Head(M.Tail(skeleton)())()
assert M.IdentityCompare(ObligationSkeletonEntryGoal(middle)(), M.EmptyList)() is M.false_value
assert M.TermEqual(ObligationSkeletonEntryGoal(middle)(), selected)() is M.false_value
print("failed_intermediate_blocks_retention_test: PASS (audit target identified)")
print("registered: 3")
