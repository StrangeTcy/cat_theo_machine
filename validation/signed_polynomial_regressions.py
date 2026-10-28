"""Signed endpoints remain bound to independently replayed polynomial proofs."""

import os
import tempfile

from hyge import checker_b as CB
from hyge import labels as L
from hyge import machine as M
from hyge import main as Main
from hyge import persistence
from hyge import playground as PG
from hyge import proof as P
from hyge import signed_polynomial as SP
from hyge.runtime import make_fresh_runtime


if __name__ == "__main__":
    runtime = make_fresh_runtime()
    registry = M.FromContextGetConstructors(runtime.graph)()
    x = M.Var()
    y = M.Var()
    variables = M.Pair(x, M.Pair(y, M.EmptyList))
    negative_y = M.Pair(L.ExprNegLabel, M.Pair(y, M.EmptyList))
    difference = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(negative_y, M.EmptyList)))
    summation = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
    lhs = M.Pair(L.ExprMulLabel, M.Pair(difference, M.Pair(summation, M.EmptyList)))
    x_squared = M.Pair(L.ExprPowLabel, M.Pair(x, M.Pair(M.two, M.EmptyList)))
    y_squared = M.Pair(L.ExprPowLabel, M.Pair(y, M.Pair(M.two, M.EmptyList)))
    rhs = M.Pair(L.ExprAddLabel,
        M.Pair(x_squared, M.Pair(M.Pair(L.ExprNegLabel, M.Pair(y_squared, M.EmptyList)), M.EmptyList)))
    trusted = M.Pair(L.SignedPolynomialRuleLabel, M.Pair(L.PolynomialGridRuleLabel, M.EmptyList))

    print("Checking signed difference-of-squares receipt.")
    built = SP.SignedPolynomialDerivation(lhs, rhs, variables, registry)()
    certificate = M.Head(built)()
    derivation = M.Head(M.Tail(built)())()
    registry = M.Head(M.Tail(M.Tail(built)())())()
    assert M.IsPair(certificate)() is M.truth_value
    assert P.IsDerivation(derivation, registry)() is M.truth_value
    step = M.Head(P.DerivationSteps(derivation, registry)())()
    assert M.Compare(P.StepCurrent(step, registry)(), lhs)() is M.truth_value
    assert M.Compare(P.StepNext(step, registry)(), rhs)() is M.truth_value
    assert M.Head(P.StepAction(step, registry)())() is L.SignedPolynomialActionLabel
    session = M.Char("signed polynomial identity")
    receipt = M.Pair(L.ProofReceiptLabel,
        M.Pair(session, M.Pair(lhs, M.Pair(rhs, M.Pair(derivation, M.EmptyList)))))
    policy = M.Pair(L.CheckPolicyLabel,
        M.Pair(session, M.Pair(lhs, M.Pair(rhs, M.EmptyList))))
    verified = CB.VerifyProofReceipt(receipt, policy, trusted, registry)()
    assert M.Head(verified)() is L.DerivationVerifiedLabel

    fields = M.Tail(certificate)()
    assert M.Compare(M.Head(fields)(), lhs)() is M.truth_value
    fields = M.Tail(fields)()
    assert M.Compare(M.Head(fields)(), rhs)() is M.truth_value
    fields = M.Tail(fields)()
    assert M.Compare(M.Head(fields)(), variables)() is M.truth_value
    fields = M.Tail(fields)()
    nat_lhs = M.Head(fields)()
    fields = M.Tail(fields)()
    nat_rhs = M.Head(fields)()
    grid_record = M.Head(M.Tail(fields)())()
    grid_fields = M.Tail(grid_record)()
    grid_count_fields = M.Tail(M.Tail(M.Tail(M.Tail(grid_fields)())())())()
    assert M.NatEq(M.Head(grid_count_fields)(), M.nine, registry)() is M.truth_value
    assert M.Head(M.Tail(grid_count_fields)())() is M.truth_value

    print("Checking both explicit authorities and original endpoint binding.")
    refused = CB.VerifyProofStep(step, M.Pair(L.PolynomialGridRuleLabel, M.EmptyList),
        M.EmptyList, M.EmptyList, registry)()
    assert M.Head(refused)() is L.UnknownRuleLabel
    assert M.Head(M.Tail(refused)())() is L.SignedPolynomialRuleLabel
    refused = SP.VerifySignedPolynomialStep(step, P.StepAction(step, registry)(),
        M.Pair(L.PolynomialGridRuleLabel, M.EmptyList), registry)()
    assert M.Head(refused)() is L.UnknownRuleLabel
    assert M.Head(M.Tail(refused)())() is L.SignedPolynomialRuleLabel
    wrong_recorded = P.Step(lhs, M.EmptyList, rhs, registry)()
    registry = M.Head(M.Tail(wrong_recorded)())()
    refused = SP.VerifySignedPolynomialStep(M.Head(wrong_recorded)(),
        P.StepAction(step, registry)(), trusted, registry)()
    assert M.Head(refused)() is L.ConclusionMutationLabel
    refused = CB.VerifyProofStep(step, M.Pair(L.SignedPolynomialRuleLabel, M.EmptyList),
        M.EmptyList, M.EmptyList, registry)()
    assert M.Head(refused)() is L.UnknownRuleLabel
    assert M.Head(M.Tail(refused)())() is L.PolynomialGridRuleLabel
    mutated = P.Step(lhs, P.StepAction(step, registry)(), M.Zero, registry)()
    registry = M.Head(M.Tail(mutated)())()
    refused = CB.VerifyProofStep(M.Head(mutated)(), trusted, M.EmptyList, M.EmptyList, registry)()
    assert M.Head(refused)() is L.ConclusionMutationLabel

    # A true zero-equals-zero grid cannot certify unrelated signed endpoints.
    zero_grid = PG.PolynomialIdentityByGrid(M.Zero, M.Zero, variables, registry)()
    registry = M.Head(M.Tail(zero_grid)())()
    unrelated = M.Pair(L.SignedPolynomialCertificateLabel,
        M.Pair(lhs, M.Pair(rhs, M.Pair(variables,
            M.Pair(M.Zero, M.Pair(M.Zero, M.Pair(M.Head(zero_grid)(), M.EmptyList)))))))
    mutated_action = M.Pair(L.SignedPolynomialActionLabel, M.Pair(unrelated, M.EmptyList))
    mutated = P.Step(lhs, mutated_action, rhs, registry)()
    registry = M.Head(M.Tail(mutated)())()
    refused = CB.VerifyProofStep(M.Head(mutated)(), trusted, M.EmptyList, M.EmptyList, registry)()
    assert M.Head(refused)() is L.ConclusionMutationLabel

    # Mutating the nested grid endpoint is rejected by the existing grid checker.
    altered_grid = M.Pair(L.PolynomialIdentityLabel,
        M.Pair(M.Zero, M.Tail(M.Tail(grid_record)())()))
    altered_certificate = M.Pair(L.SignedPolynomialCertificateLabel,
        M.Pair(lhs, M.Pair(rhs, M.Pair(variables,
            M.Pair(nat_lhs, M.Pair(nat_rhs, M.Pair(altered_grid, M.EmptyList)))))))
    mutated_action = M.Pair(L.SignedPolynomialActionLabel, M.Pair(altered_certificate, M.EmptyList))
    mutated = P.Step(lhs, mutated_action, rhs, registry)()
    registry = M.Head(M.Tail(mutated)())()
    refused = CB.VerifyProofStep(M.Head(mutated)(), trusted, M.EmptyList, M.EmptyList, registry)()
    assert M.Head(refused)() is L.ConclusionMutationLabel

    print("Checking malformed action and certificate refusal.")
    mutated_action = M.Pair(L.SignedPolynomialActionLabel,
        M.Pair(certificate, M.Pair(M.Zero, M.EmptyList)))
    mutated = P.Step(lhs, mutated_action, rhs, registry)()
    registry = M.Head(M.Tail(mutated)())()
    refused = CB.VerifyProofStep(M.Head(mutated)(), trusted, M.EmptyList, M.EmptyList, registry)()
    assert M.Head(refused)() is L.ConclusionMutationLabel
    mutated_action = M.Pair(L.SignedPolynomialActionLabel,
        M.Pair(M.Pair(L.SignedPolynomialCertificateLabel, M.EmptyList), M.EmptyList))
    mutated = P.Step(lhs, mutated_action, rhs, registry)()
    registry = M.Head(M.Tail(mutated)())()
    refused = CB.VerifyProofStep(M.Head(mutated)(), trusted, M.EmptyList, M.EmptyList, registry)()
    assert M.Head(refused)() is L.ConclusionMutationLabel
    mutated_action = M.Pair(L.SignedPolynomialActionLabel,
        M.Pair(M.Pair(L.PolynomialIdentityLabel, M.Tail(certificate)()), M.EmptyList))
    mutated = P.Step(lhs, mutated_action, rhs, registry)()
    registry = M.Head(M.Tail(mutated)())()
    refused = CB.VerifyProofStep(M.Head(mutated)(), trusted, M.EmptyList, M.EmptyList, registry)()
    assert M.Head(refused)() is L.ConclusionMutationLabel

    print("Checking signed constants and a signed base under a fixed power.")
    whole = M.Whole(M.Zero, M.one, registry)()
    minus_one = M.Head(whole)()
    registry = M.Head(M.Tail(whole)())()
    whole = M.Whole(M.three, M.two, registry)()
    noncanonical_one = M.Head(whole)()
    registry = M.Head(M.Tail(whole)())()
    signed_constant_sum = M.Pair(L.ExprAddLabel,
        M.Pair(M.Pair(L.ExprIntLabel, M.Pair(minus_one, M.EmptyList)),
            M.Pair(noncanonical_one, M.EmptyList)))
    built = SP.SignedPolynomialDerivation(signed_constant_sum, M.Zero, M.EmptyList, registry)()
    constant_derivation = M.Head(M.Tail(built)())()
    registry = M.Head(M.Tail(M.Tail(built)())())()
    assert P.IsDerivation(constant_derivation, registry)() is M.truth_value
    verified = CB.VerifyDerivation(constant_derivation, signed_constant_sum, M.Zero, trusted, registry)()
    assert M.Head(verified)() is L.DerivationVerifiedLabel
    negative_x = M.Pair(L.ExprNegLabel, M.Pair(x, M.EmptyList))
    negative_square = M.Pair(L.ExprPowLabel, M.Pair(negative_x, M.Pair(M.two, M.EmptyList)))
    built = SP.SignedPolynomialDerivation(negative_square, x_squared, M.Pair(x, M.EmptyList), registry)()
    negative_derivation = M.Head(M.Tail(built)())()
    registry = M.Head(M.Tail(M.Tail(built)())())()
    verified = CB.VerifyDerivation(negative_derivation, negative_square, x_squared, trusted, registry)()
    assert M.Head(verified)() is L.DerivationVerifiedLabel

    print("Checking nonidentities and unsupported syntax.")
    wrong_rhs = M.Pair(L.ExprAddLabel, M.Pair(x_squared, M.Pair(y_squared, M.EmptyList)))
    built = SP.SignedPolynomialDerivation(lhs, wrong_rhs, variables, registry)()
    assert M.IsPair(M.Head(built)())() is M.truth_value
    assert M.Head(M.Tail(built)())() is M.EmptyList
    registry = M.Head(M.Tail(M.Tail(built)())())()
    malformed = M.Pair(L.ExprNegLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
    built = SP.SignedPolynomialDerivation(malformed, rhs, variables, registry)()
    assert M.Head(built)() is M.EmptyList
    assert M.Head(M.Tail(built)())() is M.EmptyList
    symbolic_exponent = M.Pair(L.ExprPowLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
    built = SP.SignedPolynomialDerivation(symbolic_exponent, rhs, variables, registry)()
    assert M.Head(built)() is M.EmptyList
    built = SP.SignedPolynomialDerivation(M.Pair(L.ExprIntLabel, M.Pair(x, M.EmptyList)), x, variables, registry)()
    assert M.Head(built)() is M.EmptyList
    built = SP.SignedPolynomialDerivation(lhs, rhs, M.Pair(x, M.Pair(x, M.EmptyList)), registry)()
    assert M.Head(built)() is M.EmptyList
    built = SP.SignedPolynomialDerivation(lhs, rhs, M.Pair(x, M.EmptyList), registry)()
    assert M.Head(built)() is M.EmptyList
    unsupported = M.Pair(L.ExprSubtractLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
    built = SP.SignedPolynomialDerivation(unsupported, difference, variables, registry)()
    assert M.Head(built)() is M.EmptyList
    built = SP.SignedPolynomialDerivation(M.Zero, M.Zero, M.Pair(minus_one, M.EmptyList), registry)()
    assert M.Head(built)() is M.EmptyList

    print("Checking a file snapshot roundtrip with the live runtime namespace.")
    runtime.graph._replace_context(constructors=registry,
        nodes=M.Pair(receipt, M.Pair(policy, M.Pair(trusted, M.EmptyList))))
    codec = persistence.SnapshotCodec(Main._runtime_namespace())
    with tempfile.TemporaryDirectory(prefix="hyge-signed-polynomial-") as snapshot_dir:
        snapshot_path = os.path.join(snapshot_dir, "signed-receipt.json")
        codec.save(runtime.graph, snapshot_path)
        restored = codec.load(snapshot_path)
        resumed = make_fresh_runtime()
        codec.activate(restored, resumed.graph)
    registry = M.FromContextGetConstructors(resumed.graph)()
    restored_nodes = M.FromContextGetNodes(resumed.graph)()
    restored_receipt = M.Head(restored_nodes)()
    restored_policy = M.Head(M.Tail(restored_nodes)())()
    restored_trusted = M.Head(M.Tail(M.Tail(restored_nodes)())())()
    assert M.Head(restored_trusted)() is L.SignedPolynomialRuleLabel
    restored_fields = M.Tail(restored_receipt)()
    restored_derivation = M.Head(M.Tail(M.Tail(M.Tail(restored_fields)())())())()
    restored_step = M.Head(P.DerivationSteps(restored_derivation, registry)())()
    restored_action = P.StepAction(restored_step, registry)()
    assert M.Head(restored_action)() is L.SignedPolynomialActionLabel
    assert M.Head(M.Head(M.Tail(restored_action)())())() is L.SignedPolynomialCertificateLabel
    verified = CB.VerifyProofReceipt(restored_receipt, restored_policy, restored_trusted, registry)()
    assert M.Head(verified)() is L.DerivationVerifiedLabel

    print("Signed polynomial regressions passed: signed-endpoint receipt, recorded-action binding, exact translation replay, explicit authorities, constants, powers, mutations, malformed records, nonidentity refusal, and snapshot roundtrip.")
