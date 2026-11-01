"""Registered operations participate in mined finite observations and live replay."""

import os
import tempfile

from hyge import defined_operations as DO
from hyge import invariant_miner as IM
from hyge import labels as L
from hyge import live_proof as LP
from hyge import live_structures as LS
from hyge import machine as M
from hyge import observed_structures as OS
from hyge import operation_catalog as OC
from hyge import persistence
from hyge import playground as PG
from hyge import runtime


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
    registry = M.FromContextGetConstructors(rt.graph)()
    original_rules = M.FromContextGetRuleOrder(rt.graph)()
    label = M.Atom()
    a = M.Atom()
    b = M.Atom()
    formals = M.Pair(a, M.Pair(b, M.EmptyList))
    body = M.Pair(L.ExprMulLabel, formals)
    registered = DO.RegisterDefinedNatOperation(label, formals, body, registry)()
    assert M.Head(registered)() is M.truth_value
    registry = M.Head(M.Tail(registered)())()
    descriptor = M.Head(M.Tail(M.Tail(registered)())())()
    operations = M.Pair(descriptor, M.EmptyList)
    domain = M.Pair(M.Zero, M.Pair(M.one, M.EmptyList))
    mined = IM.MineOperationInvariantsAcrossRegister(
        domain, registry, operations, stop_after_first=M.truth_value,
    )()
    findings = M.Head(mined)()
    registry = M.Head(M.Tail(mined)())()
    assert M.IsPair(findings)() is M.truth_value
    finding = M.Head(findings)()
    assert M.Tail(findings)() is M.EmptyList
    built = OS.BuildObservedStructureBundle(findings, domain, operations, registry)()
    bundle = M.Head(built)()
    registry = M.Head(M.Tail(built)())()
    assert M.IsPair(bundle)() is M.truth_value, "mined custom operations cannot yet enter observation bundles"
    assert LP.LiveProofRecordField(bundle, M.five)() is L.PendingLabel
    verified = OS.VerifyObservedStructureBundle(bundle, findings, domain, operations, registry)()
    assert M.Head(verified)() is M.truth_value
    registry = M.Head(M.Tail(verified)())()
    print("PASS the existing miner discovers and replays a finite equation of a registered operation")

    widened = M.Pair(M.Zero, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
    assert M.Head(OS.VerifyObservedStructureBundle(bundle, findings, widened, operations, registry)())() is M.false_value
    forged = M.Pair(M.Head(bundle)(), M.Pair(domain, M.Pair(operations,
        M.Pair(findings, M.Pair(M.EmptyList, M.Pair(L.PendingLabel, M.EmptyList))))))
    assert M.Head(OS.VerifyObservedStructureBundle(forged, findings, domain, operations, registry)())() is M.false_value
    assert M.Head(OS.BuildObservedStructureBundle(findings, domain,
        M.Pair(descriptor, operations), registry)())() is M.EmptyList
    metadata = M.Tail(M.Tail(M.Tail(descriptor)())())()
    swapped_descriptor = M.Pair(M.Head(descriptor)(), M.Pair(formals,
        M.Pair(M.Pair(label, M.Pair(b, M.Pair(a, M.EmptyList))), metadata)))
    assert M.Head(OS.BuildObservedStructureBundle(findings, domain,
        M.Pair(swapped_descriptor, M.EmptyList), registry)())() is M.EmptyList
    key = M.Pair(L.NatOperationCatalogLabel, M.Pair(label, M.EmptyList))
    corrupt = M.Pair(M.Char("defined-nat-operation-v1"), M.Pair(label,
        M.Pair(formals, M.Pair(M.Pair(L.ExprGcdLabel, formals), M.EmptyList))))
    corrupt_registry = M.TreeInsert(registry, key, corrupt, registry)()
    assert M.Head(OS.VerifyObservedStructureBundle(bundle, findings, domain,
        operations, corrupt_registry)())() is M.false_value
    descriptor_registry = OC.ExtendNatOperationCatalog(descriptor, M.Tree(M.EmptyList))()
    assert M.Head(OS.BuildObservedStructureBundle(findings, domain,
        operations, descriptor_registry)())() is M.EmptyList
    identity_label = M.Atom()
    identity_formal = M.Char("anonymous formal identity fixture")
    identity_formals = M.Pair(identity_formal, M.EmptyList)
    identity_registered = DO.RegisterDefinedNatOperation(
        identity_label, identity_formals, identity_formal, registry,
    )()
    assert M.Head(identity_registered)() is M.truth_value
    identity_registry = M.Head(M.Tail(identity_registered)())()
    identity_descriptor = M.Head(M.Tail(M.Tail(identity_registered)())())()
    assert M.Head(OS.ObservedExecutableOperations(
        M.Pair(identity_descriptor, M.EmptyList), identity_registry,
    )())() is M.truth_value
    copied_formal = M.Char("anonymous formal identity fixture")
    assert M.Compare(copied_formal, identity_formal)() is M.truth_value
    assert M.IdentityCompare(copied_formal, identity_formal)() is M.false_value
    copied_call = M.Pair(identity_label, M.Pair(copied_formal, M.EmptyList))
    copied_descriptor = M.Pair(M.Head(identity_descriptor)(), M.Pair(identity_formals,
        M.Pair(copied_call, M.Tail(M.Tail(M.Tail(identity_descriptor)())())())))
    assert M.Head(OS.ObservedExecutableOperations(
        M.Pair(copied_descriptor, M.EmptyList), identity_registry,
    )())() is M.false_value
    print("PASS replay refuses changed scope, forged evidence, duplicate or misbound descriptors, and invalid definitions")

    rt.graph._replace_context(constructors=registry)
    recorded = LS.RecordObservedStructureBundle(rt.graph, finding, domain, operations)()
    assert M.IsPair(M.Head(recorded)())() is M.truth_value
    explanation = LS.ExplainObservedStructureBundle(rt.graph)()
    saved_bundle = LS.LatestObservedStructureBundle(
        M.FromContextGetNodes(rt.graph)(), M.FromContextGetConstructors(rt.graph)(), domain,
    )()
    assert M.Compare(saved_bundle, M.Head(recorded)())() is M.truth_value
    assert M.FromContextGetRuleOrder(rt.graph)() is original_rules
    print(explanation)
    codec = persistence.SnapshotCodec(persistence._runtime_namespace_for_restore())
    with tempfile.TemporaryDirectory(prefix="hyge-defined-discovery-") as snapshot_directory:
        snapshot_path = os.path.join(snapshot_directory, "observed-operation.json")
        codec.save(rt.graph, snapshot_path)
        restored = codec.load(snapshot_path)
        resumed = runtime.make_fresh_runtime()
        codec.activate(restored, resumed.graph)
    restored_registry = M.FromContextGetConstructors(resumed.graph)()
    restored_bundle = LS.LatestObservedStructureBundle(
        M.FromContextGetNodes(resumed.graph)(), restored_registry,
    )()
    restored_domain = LP.LiveProofRecordField(restored_bundle, M.one)()
    restored_operations = LP.LiveProofRecordField(restored_bundle, M.two)()
    restored_findings = LP.LiveProofRecordField(restored_bundle, M.three)()
    assert M.Head(OS.VerifyObservedStructureBundle(restored_bundle, restored_findings,
        restored_domain, restored_operations, restored_registry)())() is M.truth_value
    print(LS.ExplainObservedStructureBundle(resumed.graph)())
    assert M.FromContextGetRuleOrder(resumed.graph)() is M.EmptyList
    print("PASS live recording, explanation and file-backed restoration retain custom finite observations without adding proof rules")
    print("Defined discovery integration passed.")
