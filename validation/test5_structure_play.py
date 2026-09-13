# ============================================================
# TEST 5: STRUCTURE-PLAY-ENG — bounded finite-operation laboratory
#
#  1. Triangle transformation group fixture: table, exploration,
#     serial admission, certification, group recognition.
#  2. Transfer: certified shortcut, disabled shortcut.
#  3. Nonassociative decoy: rejected with a concrete counterexample.
#  4. Semigroup-without-identity decoy: no monoid certification.
#  5. Renamed-carrier invariance: same recognized abstraction.
#  6. Certification lifecycle: disable removes recognition,
#     restore brings it back.
#  7. Exploration budget guard.
# ============================================================
import sys
import os
import time

IMPORT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_ROOT = os.path.dirname(IMPORT_ROOT)
for path_root in (IMPORT_ROOT, PARENT_ROOT):
    if path_root not in sys.path:
        sys.path.insert(0, path_root)

from cat_theo_machine import machine as M
from cat_theo_machine import labels as L
from cat_theo_machine import structure_play as SP
from cat_theo_machine import structure_recognizer as SR

t0 = time.time()
print("=== TEST 5: Structure Play Laboratory ===")
print()

failures = 0

print("[1] Declaring the triangle composition operation...")
triangle_op = SP.DirectTriangleOperation()()
triangle_elements = SP.DeclaredOperationElements(triangle_op)()
op_name = SP.DeclaredOperationName(triangle_op)()
print("    name kind:", "TriangleComposeOperation" if M.IdentityCompare(op_name, L.TriangleComposeOperationLabel)() is M.truth_value else "UNEXPECTED")
print()

print("[2] Complete operation table (row-major)...")
table = SP.DeclaredTableEntries(triangle_op)()
cell_count = 0
walk = table
while M.IdentityCompare(walk, M.EmptyList)() is M.false_value:
    cell_count += 1
    walk = M.Tail(walk)()
expected_cells = 36
print("    table cells:", cell_count, "(expected", expected_cells, ")")
if cell_count != expected_cells:
    failures += 1
    print("    FAILED: unexpected table size")

rotation = SP.TriangleTransform(L.TriangleRotationKindLabel)()
reflection_a = SP.TriangleTransform(M.Pair(L.TriangleReflectionKindLabel, M.Pair(L.DecoyAlphaLabel, M.EmptyList)))()
identity_element = SP.TriangleTransform(L.TriangleIdentityKindLabel)()
cell_e_r1 = SP.OperationCell(triangle_op, identity_element, rotation)()
print("    cell (e, r1) is r1:", M.TermEqual(cell_e_r1, rotation)() is M.truth_value)
if M.TermEqual(cell_e_r1, rotation)() is not M.truth_value:
    failures += 1
    print("    FAILED: identity cell wrong")
cell_s_s = SP.OperationCell(triangle_op, reflection_a, reflection_a)()
print("    cell (s_a, s_a) is e:", M.TermEqual(cell_s_s, identity_element)() is M.truth_value)
if M.TermEqual(cell_s_s, identity_element)() is not M.truth_value:
    failures += 1
    print("    FAILED: reflection-involution cell wrong")
rotation_right_of_reflection = SP.OperationCell(triangle_op, reflection_a, rotation)()
rotation_left_of_reflection = SP.OperationCell(triangle_op, rotation, reflection_a)()
noncommuting_pair = M.NotAtom(M.TermEqual(rotation_right_of_reflection, rotation_left_of_reflection)())()
print("    noncommutativity witnessed at (r1, s_a):", noncommuting_pair is M.truth_value)
if noncommuting_pair is not M.truth_value:
    failures += 1
    print("    FAILED: noncommutativity witness missing")
print()

print("[3] Bounded exploration run over the triangle carrier...")
exploration = SP.ExplorationRun(triangle_op, M.five)()
exploration_verdict = SP.ExplorationVerdictOf(exploration)()
ledger = SP.ExplorationLedgerOf(exploration)()
print("    verdict:", "ExplorationComplete" if M.IdentityCompare(exploration_verdict, L.ExplorationCompleteLabel)() is M.truth_value else "UNEXPECTED")
if M.IdentityCompare(exploration_verdict, L.ExplorationCompleteLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: exploration did not complete")

entry_count = 0
conjecture_labels = M.EmptyList
counterexample_seen = M.false_value
closure_observation_ok = M.false_value
walk = SP.LedgerEntries(ledger)()
while M.IdentityCompare(walk, M.EmptyList)() is M.false_value:
    entry = M.Head(walk)()
    entry_count += 1
    if M.IsPair(entry)() is M.truth_value:
        kind = M.Head(entry)()
    else:
        kind = entry
    if M.IdentityCompare(kind, L.ConjecturedLawLabel)() is M.truth_value:
        law_label = M.Head(M.Tail(entry)())()
        conjecture_labels = M.Pair(law_label, conjecture_labels)
    if M.IdentityCompare(kind, L.CounterexampleLabel)() is M.truth_value:
        counterexample_seen = M.truth_value
    if M.IdentityCompare(kind, L.ClosureObservationLabel)() is M.truth_value:
        flag = M.Head(M.Tail(entry)())()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            closure_observation_ok = M.truth_value
    walk = M.Tail(walk)()
print("    ledger entries:", entry_count)
print("    closure observation positive:", closure_observation_ok is M.truth_value)
if closure_observation_ok is not M.truth_value:
    failures += 1
    print("    FAILED: closure observation missing or negative")

expected_conjectures = M.Pair(
    L.ClosureLawLabel,
    M.Pair(
        L.AssociativeLawLabel,
        M.Pair(L.IdentityLawLabel, M.Pair(L.InverseLawLabel, M.EmptyList)),
    ),
)
all_laws_conjectured = M.truth_value
walk = expected_conjectures
while M.IdentityCompare(walk, M.EmptyList)() is M.false_value:
    wanted = M.Head(walk)()
    found = M.false_value
    scan = conjecture_labels
    while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
        if M.IdentityCompare(M.Head(scan)(), wanted)() is M.truth_value:
            found = M.truth_value
        scan = M.Tail(scan)()
    if found is not M.truth_value:
        all_laws_conjectured = M.false_value
    walk = M.Tail(walk)()
print("    closure, associativity, identity, inverse conjectures proposed:", all_laws_conjectured is M.truth_value)
if all_laws_conjectured is not M.truth_value:
    failures += 1
    print("    FAILED: a law conjecture is missing from the ledger")
commutativity_conjectured = M.false_value
scan = conjecture_labels
while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
    if M.IdentityCompare(M.Head(scan)(), L.CommutativeLawLabel)() is M.truth_value:
        commutativity_conjectured = M.truth_value
    scan = M.Tail(scan)()
print("    refuted commutativity correctly left unconjectured:", commutativity_conjectured is M.false_value)
if commutativity_conjectured is not M.false_value:
    failures += 1
    print("    FAILED: a refuted law was conjectured anyway")
print()

print("[4] Serial proposal admission...")
admitted_count = 0
walk = SP.LedgerEntries(ledger)()
while M.IdentityCompare(walk, M.EmptyList)() is M.false_value:
    entry = M.Head(walk)()
    if M.IsPair(entry)() is M.truth_value:
        if M.IdentityCompare(M.Head(entry)(), L.ConjecturedLawLabel)() is M.truth_value:
            outcome = SP.AdmitProposal(entry, triangle_op)()
            verdict = M.Head(M.Tail(M.Tail(outcome)())())()
            if M.IdentityCompare(verdict, L.CandidateRecognizedLabel)() is M.truth_value:
                admitted_count += 1
            else:
                failures += 1
                print("    FAILED: a supported conjecture was not admitted")
    walk = M.Tail(walk)()
print("    conjectures admitted:", admitted_count, "(expected 4)")
if admitted_count != 4:
    failures += 1
    print("    FAILED: unexpected admission count")
print()

print("[5] Unnamed signature and certificates...")
signature = SP.SignatureForOperation(triangle_op)()
signature_label = SP.SignatureLabelOf(signature)()
print("    signature term:", "StructureSignature" if M.IdentityCompare(signature_label, L.StructureSignatureLabel)() is M.truth_value else "UNEXPECTED")
if M.IdentityCompare(signature_label, L.StructureSignatureLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: signature label wrong")

operation_for_replay = SP.SignatureOperationTerm(signature)()
slot_checks = M.Pair(
    M.Pair(SP.SignatureClosureOf(signature)(), M.Pair(L.ClosureLawLabel, M.EmptyList)),
    M.Pair(
        M.Pair(SP.SignatureAssociativityOf(signature)(), M.Pair(L.AssociativeLawLabel, M.EmptyList)),
        M.Pair(
            M.Pair(SP.SignatureIdentityOf(signature)(), M.Pair(L.IdentityLawLabel, M.EmptyList)),
            M.Pair(M.Pair(SP.SignatureInversesOf(signature)(), M.Pair(L.InverseLawLabel, M.EmptyList)), M.EmptyList),
        ),
    ),
)
all_slots_certified = M.truth_value
walk = slot_checks
while M.IdentityCompare(walk, M.EmptyList)() is M.false_value:
    pair = M.Head(walk)()
    law = M.Head(pair)()
    wanted = M.Head(M.Tail(pair)())()
    if M.IdentityCompare(law, M.EmptyList)() is M.truth_value:
        all_slots_certified = M.false_value
    else:
        label_ok = M.IdentityCompare(SP.CertifiedLawLabelOf(law)(), wanted)()
        replay_verdict = SP.CheckReplay(SP.CertifiedLawReplayOf(law)(), operation_for_replay)()
        replay_ok = M.IdentityCompare(replay_verdict, L.ReplayVerifiedLabel)()
        if M.AndAtom(label_ok, replay_ok)() is not M.truth_value:
            all_slots_certified = M.false_value
    walk = M.Tail(walk)()
print("    four group-relevant slots certified with verified replays:", all_slots_certified is M.truth_value)
if all_slots_certified is not M.truth_value:
    failures += 1
    print("    FAILED: a certified slot is missing or fails replay")
commutativity_slot_empty = M.IdentityCompare(SP.SignatureCommutativityOf(signature)(), M.EmptyList)()
print("    refuted commutativity left uncertified:", commutativity_slot_empty is M.truth_value)
if commutativity_slot_empty is not M.truth_value:
    failures += 1
    print("    FAILED: a refuted law reached a certified slot")
counterexample_slot = SP.SignatureCounterexamplesOf(signature)()
counterexamples_present = M.IdentityCompare(counterexample_slot, M.EmptyList)()
print("    counterexample slot carries the refutation evidence:", counterexamples_present is M.false_value)
if counterexamples_present is not M.false_value:
    failures += 1
    print("    FAILED: refuted law left no counterexample evidence")
print()

print("[6] Recognition against the catalogue...")
catalogue = SR.RecognizerCatalogue()()
candidate = SP.BuildStructureCandidate(signature, L.AbstractGroupLabel)()
recognition = SR.RecognizeStructure(candidate, catalogue)()
recognized_entry = SR.RecognizedEntryOf(recognition)()
recognition_verdict = SR.RecognizedVerdictOf(recognition)()
print("    verdict:", "CandidateRecognized" if M.IdentityCompare(recognition_verdict, L.CandidateRecognizedLabel)() is M.truth_value else "UNEXPECTED")
print("    recognized entry:", "AbstractGroup" if M.IdentityCompare(recognized_entry, L.AbstractGroupLabel)() is M.truth_value else "UNEXPECTED")
if M.IdentityCompare(recognition_verdict, L.CandidateRecognizedLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: triangle signature was not recognized")
if M.IdentityCompare(recognized_entry, L.AbstractGroupLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: recognized entry is not AbstractGroup")
group_entry = SR.CatalogueEntryNamed(catalogue, L.AbstractGroupLabel)()
group_gate = SR.CertificationGate(signature, SR.CatalogueEntryRequirements(group_entry)())()
group_gate_open = M.IdentityCompare(SR.GateVerdict(group_gate)(), M.truth_value)()
print("    group gate opens on the certified signature:", group_gate_open is M.truth_value)
if group_gate_open is not M.truth_value:
    failures += 1
    print("    FAILED: group gate did not open")
abelian_entry = SR.CatalogueEntryNamed(catalogue, L.AbstractAbelianGroupLabel)()
abelian_gate = SR.CertificationGate(signature, SR.CatalogueEntryRequirements(abelian_entry)())()
abelian_gate_closed = M.IdentityCompare(SR.GateVerdict(abelian_gate)(), M.false_value)()
abelian_blocking = SR.GateBlockingRequirement(abelian_gate)()
print("    abelian gate closed, blocking requirement commutativity:", abelian_gate_closed is M.truth_value and M.IdentityCompare(abelian_blocking, L.CommutativeLawLabel)() is M.truth_value)
if abelian_gate_closed is not M.truth_value or M.IdentityCompare(abelian_blocking, L.CommutativeLawLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: abelian gate state wrong")
print()

print("[7] Transfer: certified shortcut, then disabled...")
certified_laws = M.Pair(
    SP.SignatureClosureOf(signature)(),
    M.Pair(
        SP.SignatureAssociativityOf(signature)(),
        M.Pair(
            SP.SignatureIdentityOf(signature)(),
            M.Pair(SP.SignatureInversesOf(signature)(), M.EmptyList),
        ),
    ),
)
requested_chain = M.Pair(rotation, M.Pair(SP.TriangleTransform(M.Pair(L.TriangleRotationKindLabel, M.Pair(L.TriangleRotationKindLabel, M.EmptyList)))(), M.EmptyList))
prediction = SP.PredictTransfer(certified_laws, requested_chain)()
predicted = M.Head(M.Tail(M.Tail(M.Tail(prediction)())())())()
evaluation = SP.EvaluateTransferPrediction(prediction)()
print("    held-out prediction confirmed:", M.IdentityCompare(evaluation, L.TransferConfirmedLabel)() is M.truth_value)
print("    predicted element is the identity:", M.TermEqual(predicted, identity_element)() is M.truth_value)
if M.IdentityCompare(evaluation, L.TransferConfirmedLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: certified transfer shortcut did not confirm")
if M.TermEqual(predicted, identity_element)() is not M.truth_value:
    failures += 1
    print("    FAILED: prediction did not come from the certificate")

disabled_prediction = SP.PredictTransfer(M.EmptyList, requested_chain)()
disabled_value = M.Head(M.Tail(M.Tail(M.Tail(disabled_prediction)())())())()
print("    with certificates removed the shortcut is unavailable:", M.IdentityCompare(disabled_value, L.TransferUnavailableLabel)() is M.truth_value)
if M.IdentityCompare(disabled_value, L.TransferUnavailableLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: shortcut survived certificate removal")
print()

print("[8] Nonassociative decoy...")
nonassoc_op = SP.DecoyNonAssociativeOperation()()
nonassoc_elements = SP.DeclaredOperationElements(nonassoc_op)()
nonassoc_closure_probe = SP.DirectLawProbe(L.ClosureLawLabel, nonassoc_op)()
nonassoc_assoc_probe = SP.DirectLawProbe(L.AssociativeLawLabel, nonassoc_op)()
nonassoc_identity_probe = SP.DirectLawProbe(L.IdentityLawLabel, nonassoc_op)()
closure_holds = M.IdentityCompare(M.Head(nonassoc_closure_probe)(), L.LawHoldsLabel)()
assoc_violated = M.IdentityCompare(M.Head(nonassoc_assoc_probe)(), L.LawViolatedLabel)()
identity_violated = M.IdentityCompare(M.Head(nonassoc_identity_probe)(), L.LawViolatedLabel)()
print("    closure holds:", closure_holds is M.truth_value)
print("    associativity violated:", assoc_violated is M.truth_value)
print("    identity violated:", identity_violated is M.truth_value)
if closure_holds is not M.truth_value:
    failures += 1
    print("    FAILED: decoy closure state wrong")
if assoc_violated is not M.truth_value:
    failures += 1
    print("    FAILED: decoy associativity state wrong")
if identity_violated is not M.truth_value:
    failures += 1
    print("    FAILED: decoy identity state wrong")

assoc_findings = M.Head(M.Tail(nonassoc_assoc_probe)())()
first_refutation = M.Head(assoc_findings)()
refutation_left = M.Head(M.Tail(M.Tail(first_refutation)())())()
refutation_law = M.Head(M.Tail(first_refutation)())()
print("    concrete counterexample recorded:", M.IdentityCompare(refutation_law, L.AssociativeLawLabel)() is M.truth_value)
if M.IdentityCompare(refutation_law, L.AssociativeLawLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: counterexample not recorded under associativity")

nonassoc_exploration = SP.ExplorationRun(nonassoc_op, M.five)()
nonassoc_ledger = SP.ExplorationLedgerOf(nonassoc_exploration)()
nonassoc_counterexample = M.EmptyList
walk = SP.LedgerEntries(nonassoc_ledger)()
while M.IdentityCompare(walk, M.EmptyList)() is M.false_value:
    entry = M.Head(walk)()
    if M.IsPair(entry)() is M.truth_value:
        if M.IdentityCompare(M.Head(entry)(), L.CounterexampleLabel)() is M.truth_value:
            nonassoc_counterexample = entry
    walk = M.Tail(walk)()
print("    worker journal produced the refutation:", M.IdentityCompare(nonassoc_counterexample, M.EmptyList)() is M.false_value)
if M.IdentityCompare(nonassoc_counterexample, M.EmptyList)() is M.false_value:
    outcome = SP.AdmitProposal(nonassoc_counterexample, nonassoc_op)()
    verdict = M.Head(M.Tail(M.Tail(outcome)())())()
    print("    serial admission rejected the refutation as structure:", M.IdentityCompare(verdict, L.ProposalRejectedLabel)() is M.truth_value)
    if M.IdentityCompare(verdict, L.ProposalRejectedLabel)() is not M.truth_value:
        failures += 1
        print("    FAILED: refutation was not rejected at admission")
else:
    failures += 1
    print("    FAILED: no refutation in the worker journal")

nonassoc_signature = SP.SignatureForOperation(nonassoc_op)()
nonassoc_assoc_slot = SP.SignatureAssociativityOf(nonassoc_signature)()
nonassoc_counterexample_slot = SP.SignatureCounterexamplesOf(nonassoc_signature)()
print("    associativity slot withheld:", M.IdentityCompare(nonassoc_assoc_slot, M.EmptyList)() is M.truth_value)
print("    counterexample slot populated:", M.IdentityCompare(nonassoc_counterexample_slot, M.EmptyList)() is M.false_value)
if M.IdentityCompare(nonassoc_assoc_slot, M.EmptyList)() is not M.truth_value:
    failures += 1
    print("    FAILED: violated law reached a certified slot")
if M.IdentityCompare(nonassoc_counterexample_slot, M.EmptyList)() is M.false_value:
    nonassoc_candidate = SP.BuildStructureCandidate(nonassoc_signature, L.AbstractGroupLabel)()
    nonassoc_recognition = SR.RecognizeStructure(nonassoc_candidate, catalogue)()
    nonassoc_verdict = SR.RecognizedVerdictOf(nonassoc_recognition)()
    nonassoc_blocking = SR.RecognizedBlockingOf(nonassoc_recognition)()
    print("    recognition withheld:", M.IdentityCompare(nonassoc_verdict, L.WithheldStructureLabel)() is M.truth_value)
    print("    blocking requirement is associativity:", M.IdentityCompare(nonassoc_blocking, L.AssociativeLawLabel)() is M.truth_value)
    if M.IdentityCompare(nonassoc_verdict, L.WithheldStructureLabel)() is not M.truth_value:
        failures += 1
        print("    FAILED: nonassociative decoy was recognized")
    if M.IdentityCompare(nonassoc_blocking, L.AssociativeLawLabel)() is not M.truth_value:
        failures += 1
        print("    FAILED: blocking requirement is not associativity")
else:
    failures += 1
    print("    FAILED: counterexample slot empty for the decoy")
print()

print("[9] Semigroup-without-identity decoy...")
semigroup_op = SP.DecoyRightProjectionOperation()()
semigroup_signature = SP.SignatureForOperation(semigroup_op)()
semigroup_closure = SP.SignatureClosureOf(semigroup_signature)()
semigroup_assoc = SP.SignatureAssociativityOf(semigroup_signature)()
semigroup_identity = SP.SignatureIdentityOf(semigroup_signature)()
print("    closure certified:", M.IdentityCompare(semigroup_closure, M.EmptyList)() is M.false_value)
print("    associativity certified:", M.IdentityCompare(semigroup_assoc, M.EmptyList)() is M.false_value)
print("    identity slot empty:", M.IdentityCompare(semigroup_identity, M.EmptyList)() is M.truth_value)
if M.IdentityCompare(semigroup_closure, M.EmptyList)() is not M.false_value:
    failures += 1
    print("    FAILED: semigroup closure not certified")
if M.IdentityCompare(semigroup_assoc, M.EmptyList)() is not M.false_value:
    failures += 1
    print("    FAILED: semigroup associativity not certified")
if M.IdentityCompare(semigroup_identity, M.EmptyList)() is not M.truth_value:
    failures += 1
    print("    FAILED: semigroup identity unexpectedly certified")
semigroup_candidate = SP.BuildStructureCandidate(semigroup_signature, L.WithheldStructureLabel)()
semigroup_recognition = SR.RecognizeStructure(semigroup_candidate, catalogue)()
semigroup_entry = SR.RecognizedEntryOf(semigroup_recognition)()
semigroup_verdict = SR.RecognizedVerdictOf(semigroup_recognition)()
print("    recognized entry:", "AbstractSemigroup" if M.IdentityCompare(semigroup_entry, L.AbstractSemigroupLabel)() is M.truth_value else "UNEXPECTED")
if M.IdentityCompare(semigroup_entry, L.AbstractSemigroupLabel)() is not M.truth_value or M.IdentityCompare(semigroup_verdict, L.CandidateRecognizedLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: semigroup decoy did not recognize as AbstractSemigroup")
monoid_entry = SR.CatalogueEntryNamed(catalogue, L.AbstractMonoidLabel)()
monoid_gate = SR.CertificationGate(semigroup_signature, SR.CatalogueEntryRequirements(monoid_entry)())()
monoid_gate_closed = M.IdentityCompare(SR.GateVerdict(monoid_gate)(), M.false_value)()
monoid_blocking = SR.GateBlockingRequirement(monoid_gate)()
print("    monoid gate closed, blocking requirement identity:", monoid_gate_closed is M.truth_value and M.IdentityCompare(monoid_blocking, L.IdentityLawLabel)() is M.truth_value)
if monoid_gate_closed is not M.truth_value or M.IdentityCompare(monoid_blocking, L.IdentityLawLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: monoid gate state wrong for the semigroup decoy")
print()

print("[10] Renamed-carrier invariance...")
renamed_op = SP.RenamedTriangleOperation()()
renamed_elements = SP.DeclaredOperationElements(renamed_op)()
law_scan = M.Pair(
    L.ClosureLawLabel,
    M.Pair(
        L.AssociativeLawLabel,
        M.Pair(
            L.IdentityLawLabel,
            M.Pair(L.InverseLawLabel, M.Pair(L.CommutativeLawLabel, M.EmptyList)),
        ),
    ),
)
verdicts_agree = M.truth_value
while M.IdentityCompare(law_scan, M.EmptyList)() is M.false_value:
    law_label = M.Head(law_scan)()
    triangle_verdict = M.Head(SP.DirectLawProbe(law_label, triangle_op)())()
    renamed_verdict = M.Head(SP.DirectLawProbe(law_label, renamed_op)())()
    if M.TermEqual(triangle_verdict, renamed_verdict)() is not M.truth_value:
        verdicts_agree = M.false_value
    law_scan = M.Tail(law_scan)()
print("    all five probe verdicts agree under renaming:", verdicts_agree is M.truth_value)
if verdicts_agree is not M.truth_value:
    failures += 1
    print("    FAILED: law profile changed under renaming")
renamed_signature = SP.SignatureForOperation(renamed_op)()
renamed_candidate = SP.BuildStructureCandidate(renamed_signature, L.AbstractGroupLabel)()
renamed_recognition = SR.RecognizeStructure(renamed_candidate, catalogue)()
renamed_entry = SR.RecognizedEntryOf(renamed_recognition)()
renamed_verdict = SR.RecognizedVerdictOf(renamed_recognition)()
print("    renamed carrier recognizes:", "AbstractGroup" if M.IdentityCompare(renamed_entry, L.AbstractGroupLabel)() is M.truth_value else "UNEXPECTED")
if M.IdentityCompare(renamed_entry, L.AbstractGroupLabel)() is not M.truth_value or M.IdentityCompare(renamed_verdict, L.CandidateRecognizedLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: renaming changed the recognized abstraction")
renamed_certificates_replay = SP.CheckReplay(SP.CertifiedLawReplayOf(SP.SignatureClosureOf(renamed_signature)())(), renamed_op)()
print("    renamed closure certificate replays against the renamed table:", M.IdentityCompare(renamed_certificates_replay, L.ReplayVerifiedLabel)() is M.truth_value)
if M.IdentityCompare(renamed_certificates_replay, L.ReplayVerifiedLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: renamed certificate replay failed")
renamed_noncommutive = M.IdentityCompare(M.Head(SP.DirectLawProbe(L.CommutativeLawLabel, renamed_op)())(), L.LawViolatedLabel)()
print("    renamed carrier stays noncommutative:", renamed_noncommutive is M.truth_value)
if renamed_noncommutive is not M.truth_value:
    failures += 1
    print("    FAILED: renamed carrier lost noncommutativity")
print()

print("[11] Certification lifecycle: disable, verify blocked, restore...")
identity_law = SP.SignatureIdentityOf(signature)()
disabled_signature = SP.WithSignatureSlotWithheld(signature, L.IdentityLawLabel)()
disabled_identity_slot = SP.SignatureIdentityOf(disabled_signature)()
print("    identity slot removed:", M.IdentityCompare(disabled_identity_slot, M.EmptyList)() is M.truth_value)
if M.IdentityCompare(disabled_identity_slot, M.EmptyList)() is not M.truth_value:
    failures += 1
    print("    FAILED: disable did not empty the slot")
disabled_candidate = SP.BuildStructureCandidate(disabled_signature, L.AbstractGroupLabel)()
disabled_recognition = SR.RecognizeStructure(disabled_candidate, catalogue)()
disabled_entry = SR.RecognizedEntryOf(disabled_recognition)()
disabled_verdict = SR.RecognizedVerdictOf(disabled_recognition)()
group_recognition_gone = M.IdentityCompare(disabled_entry, L.AbstractGroupLabel)()
print("    group recognition gone while disabled:", group_recognition_gone is M.false_value)
print("    remaining certificates still support:", "AbstractSemigroup" if M.IdentityCompare(disabled_entry, L.AbstractSemigroupLabel)() is M.truth_value else "nothing")
if group_recognition_gone is not M.false_value:
    failures += 1
    print("    FAILED: group recognition survived certificate removal")
if M.IdentityCompare(disabled_verdict, L.CandidateRecognizedLabel)() is not M.truth_value or M.IdentityCompare(disabled_entry, L.AbstractSemigroupLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: remaining certificates did not degrade to the supported weaker structure")
disabled_group_gate = SR.CertificationGate(disabled_signature, SR.CatalogueEntryRequirements(group_entry)())()
disabled_group_blocking = SR.GateBlockingRequirement(disabled_group_gate)()
print("    group gate now blocked at identity:", M.IdentityCompare(disabled_group_blocking, L.IdentityLawLabel)() is M.truth_value)
if M.IdentityCompare(disabled_group_blocking, L.IdentityLawLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: group gate blocking requirement wrong after disable")
restored_signature = SP.WithCertificateRestored(disabled_signature, identity_law)()
restored_candidate = SP.BuildStructureCandidate(restored_signature, L.AbstractGroupLabel)()
restored_recognition = SR.RecognizeStructure(restored_candidate, catalogue)()
restored_entry = SR.RecognizedEntryOf(restored_recognition)()
restored_verdict = SR.RecognizedVerdictOf(restored_recognition)()
print("    recognition restored:", M.IdentityCompare(restored_verdict, L.CandidateRecognizedLabel)() is M.truth_value)
print("    restored entry:", "AbstractGroup" if M.IdentityCompare(restored_entry, L.AbstractGroupLabel)() is M.truth_value else "UNEXPECTED")
if M.IdentityCompare(restored_verdict, L.CandidateRecognizedLabel)() is not M.truth_value or M.IdentityCompare(restored_entry, L.AbstractGroupLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: restore did not reopen the gate")
print()

print("[12] Exploration budget guard...")
overbudget_exploration = SP.ExplorationRun(triangle_op, M.six)()
overbudget_verdict = SP.ExplorationVerdictOf(overbudget_exploration)()
print("    over-budget run refused:", M.IdentityCompare(overbudget_verdict, L.ExplorationBudgetExhaustedLabel)() is M.truth_value)
if M.IdentityCompare(overbudget_verdict, L.ExplorationBudgetExhaustedLabel)() is not M.truth_value:
    failures += 1
    print("    FAILED: budget guard did not fire")
overbudget_ledger_empty = M.IdentityCompare(SP.LedgerEntries(SP.ExplorationLedgerOf(overbudget_exploration)())(), M.EmptyList)()
print("    over-budget ledger empty:", overbudget_ledger_empty is M.truth_value)
if overbudget_ledger_empty is not M.truth_value:
    failures += 1
    print("    FAILED: refused run still wrote observations")
print()

print("=== TEST 5 RESULTS ===")
print("  failures:", failures)
if failures == 0:
    print("  STATUS: ALL STRUCTURE-PLAY SCENARIO CHECKS PASSED")
else:
    print("  STATUS: STRUCTURE-PLAY SCENARIO FAILURES PRESENT")
print("  total time: %.3fs" % (time.time() - t0))
print()
print("=== TEST 5 COMPLETE ===")

if failures != 0:
    sys.exit(1)
