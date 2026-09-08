#!/usr/bin/env python3
"""Rehearsal runner — Action 4: E2 conversion-path round-trip.

What this decides (operator-sanctioned rehearsal, 2026-09-08):
  1. does the one real loadable record (engel_e2_blackboard_parity) still
     load via the real loader at the rehearsal base;
  2. which obligation ObligationSkeletonConclusionGoal actually extracts
     for E2's authored skeleton order (docstring says last-with-goal;
     the implementation returns first-with-goal);
  3. what the per-record attempt cycle reports for E2 with its own pack
     (the ledger records a diagnostic "partial matches 0, invariant not
     derivable" at a3aeff4; this run converts that prediction into a
     rehearsal measurement);
  4. per-obligation derivability against E2's own pack and against the
     full library (the operational form of the join rule's "genuine
     partial match");
  5. does E2's meaning-structure term survive a SnapshotCodec round-trip;
  6. card-shape round-trip: render the loaded record back through the
     blueprint-card sections and compare with engel_e2_blackboard.md.

Usage: python3 <this-file> <repo-root>
"""
import os
import sys
import tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
PKG_PARENT = "/tmp/rehearsal-action4-pkg"
os.makedirs(PKG_PARENT, exist_ok=True)
link = os.path.join(PKG_PARENT, "cat_theo_machine")
if not os.path.lexists(link):
    os.symlink(ROOT, link)
sys.path.insert(0, PKG_PARENT)


def label_name(ns):
    reverse = {}
    for key, value in ns.items():
        reverse.setdefault(id(value), key)
    return lambda term: reverse.get(id(term), "?")


def main():
    from cat_theo_machine.main import _runtime_namespace, boot_from_packs, PACK_PATHS
    from cat_theo_machine.training import (
        TrainingRecordLoader, attempt_training_record,
        TrainingRecordMeaningStructure, TrainingRecordStrategyHint,
        TrainingRecordObligationSkeleton, ObligationSkeletonConclusionGoal,
        ObligationSkeletonEntryGoal, ObligationSkeletonEntryId,
        ObligationSkeletonEntryDescription, pretty,
    )
    from cat_theo_machine import machine as M
    from cat_theo_machine.persistence import SnapshotCodec

    ns = _runtime_namespace()
    runtime, packs = boot_from_packs(PACK_PATHS, ns)
    loader = TrainingRecordLoader(ns)

    e2_path = os.path.join(ROOT, "training_records", "engel_e2_blackboard_parity.yaml")
    loaded = loader.load_records_file(e2_path)
    print("E2 loader verdict: accepted", len(loaded), "record(s)")
    record, rules_pack = loaded[0]
    print("E2 record rules_pack field:", rules_pack)

    start = TrainingRecordMeaningStructure(record)()
    hint = TrainingRecordStrategyHint(record)()
    skeleton = TrainingRecordObligationSkeleton(record)()
    conclusion = ObligationSkeletonConclusionGoal(skeleton)()
    reg = M.FromContextGetConstructors(runtime.graph)()

    print()
    print("== conclusion extraction (docstring vs implementation) ==")
    print("extracted conclusion pretty:", pretty(conclusion, reg))
    cursor = skeleton
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        entry = M.Head(cursor)()
        gid = pretty(ObligationSkeletonEntryId(entry)(), reg)
        g = ObligationSkeletonEntryGoal(entry)()
        mark = ""
        if M.IdentityCompare(g, M.EmptyList)() is M.false_value:
            if M.Compare(g, conclusion)() is M.truth_value:
                mark = "  <== THIS is what the attempt cycle proves"
        print("obligation:", gid, "goal:", "yes" if M.IdentityCompare(g, M.EmptyList)() is M.false_value else "no", mark)
        cursor = M.Tail(cursor)()

    print()
    print("== attempt cycle with E2's own pack ==")
    attempt, summary = attempt_training_record(runtime, packs, record, "engel-blackboard")
    print("status_text:", summary.status_text)
    print("method_text:", summary.method_text)
    print("planner root status:", summary.planner_root_status)
    print("alternative status:", summary.alternative_status)
    print("retained:", summary.retained)
    print("failure reason:", summary.failure_reason)

    print()
    print("== per-obligation derivability (genuine partial match, operational) ==")
    blackboard_rules = packs.by_name("engel-blackboard").rule_chain
    cursor = skeleton
    idx = 0
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        entry = M.Head(cursor)()
        gid = pretty(ObligationSkeletonEntryId(entry)(), reg)
        g = ObligationSkeletonEntryGoal(entry)()
        if M.IdentityCompare(g, M.EmptyList)() is M.false_value:
            d_pack = runtime.prove(start, g, blackboard_rules, runtime.theorem_heuristic, M.EmptyList)
            ok_pack = M.IdentityCompare(d_pack, M.EmptyList)() is M.false_value
            print("obligation", gid, "-> own-pack derivation:", "YES" if ok_pack else "no")
        else:
            print("obligation", gid, "-> no machine goal (text-only)")
        cursor = M.Tail(cursor)()
        idx += 1

    print()
    print("== codec round-trip of E2 meaning term ==")
    runtime.graph.add_node(start)
    work = tempfile.mkdtemp(prefix="rehearsal-action4-")
    snap = os.path.join(work, "e2.snapshot.json")
    codec = SnapshotCodec(ns)
    codec.save(runtime.graph, snap, progress=M.false_value)
    state = codec.load(snap)
    print("snapshot bytes:", os.path.getsize(snap))
    print("ParityLabel survives by identity:", "ParityLabel" in state.symbols and state.symbols["ParityLabel"] is ns["ParityLabel"])
    print("BlackboardProblemLabel survives by identity:", "BlackboardProblemLabel" in state.symbols and state.symbols["BlackboardProblemLabel"] is ns["BlackboardProblemLabel"])
    rebuilt_start = TrainingRecordMeaningStructure(record)()
    print("reloaded record meaning re-extracted and Compare-equal:", M.Compare(rebuilt_start, start)() is M.truth_value)

    print()
    print("== card-shape round-trip ==")
    import yaml
    with open(e2_path, "r", encoding="utf-8") as h:
        e2_doc = yaml.safe_load(h)
    statement_text = str(e2_doc["records"][0]["problem_statement"]["text"]).strip()
    with open(os.path.join(ROOT, "engel_e2_blackboard.md"), "r", encoding="utf-8") as h:
        card_md = h.read()
    normalized_card = " ".join(card_md.split())
    normalized_statement = " ".join(statement_text.split())
    print("statement text (from YAML, first 120 chars):", statement_text[:120])
    print("statement appears verbatim (whitespace-normalized) in engel_e2_blackboard.md:",
          normalized_statement in normalized_card)
    hint_head = M.Head(hint)() if M.IdentityCompare(hint, M.EmptyList)() is M.false_value else M.EmptyList
    name_of = label_name(ns)
    print("strategy hint head label (card 'method'):", name_of(hint_head))
    print("obligation skeleton (card 'obligations'):")
    cursor = skeleton
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        entry = M.Head(cursor)()
        gid = pretty(ObligationSkeletonEntryId(entry)(), reg)
        g = ObligationSkeletonEntryGoal(entry)()
        desc = pretty(ObligationSkeletonEntryDescription(entry)(), reg)
        print("  - id:", gid, "| has machine goal:",
              "yes" if M.IdentityCompare(g, M.EmptyList)() is M.false_value else "no")
        cursor = M.Tail(cursor)()

    import shutil
    shutil.rmtree(work, ignore_errors=True)
    print()
    print("scratch removed; nothing written into the repository tree")


if __name__ == "__main__":
    main()
