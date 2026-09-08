#!/usr/bin/env python3
"""Rehearsal runner — Action 1: Tier0 conversion path against the shadow
A1 union vocabulary.

What this decides (operator-sanctioned rehearsal, 2026-09-08):
  1. do the two first-convert Tier0 cards (extremal-longest-path,
     pigeonhole-residue-classes) author into TrainingRecord YAML that the
     REAL loader accepts once the A1 union vocabulary exists;
  2. do their meaning structures, strategy hints and obligation goals
     compile term-by-term;
  3. what the per-record attempt cycle does with no rules pack (the
     honest pre-A1 library state);
  4. do terms built from the shadow vocabulary survive a SnapshotCodec
     round-trip (symbol registration + value equality via M.Compare).

Scratch discipline: the YAMLs are written under /tmp, never into the
repository; this runner and its outputs are evidence only. The shadow
vocabulary lives in the rehearsal clone this script is pointed at; the
real A1 patch is INT's deliverable.

Usage: python3 <this-file> <repo-root>
  <repo-root> = a checkout of the G/I-op base (fb7a9b3) with the two
  rehearsal patches applied (shadow-A1-union, shadow-ground3-labels).
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
PKG_PARENT = "/tmp/rehearsal-action1-pkg"
os.makedirs(PKG_PARENT, exist_ok=True)
link = os.path.join(PKG_PARENT, "cat_theo_machine")
if not os.path.lexists(link):
    os.symlink(ROOT, link)
sys.path.insert(0, PKG_PARENT)

A1_UNION = ["GraphLabel", "VertexLabel", "EdgeLabel", "PathLabel", "CycleLabel",
            "DegreeLabel", "IntegerLabel", "IntegersLabel", "RemainderLabel",
            "ResidueLabel", "ResidueClassLabel", "CongruentLabel", "WordLabel",
            "BinaryWordLabel", "AdjacentLabel", "ColoringLabel", "RotationLabel",
            "RotateLabel"]

EXTREMAL_YAML = """format: hyge-training-records
version: 1
records:
  - id: tier0_extremal_longest_path_rehearsal
    problem_statement:
      text: >-
        In a finite graph G = (V, E), every vertex has degree at least 2.
        Prove that there exists a cycle.
    meaning_structure:
      start:
        call:
          head: {sym: KnowledgeLabel}
          args:
            - list:
                - call: {head: {sym: GraphLabel}, args: [{var: g}]}
                - call: {head: {sym: VertexLabel}, args: [{var: v}]}
                - call: {head: {sym: EdgeLabel}, args: [{var: e}]}
                - call:
                    head: {sym: NatLessLabel}
                    args:
                      - {sym: one}
                      - call: {head: {sym: DegreeLabel}, args: [{var: v}]}
    strategy_hint:
      rules_pack: null
      method:
        call:
          head: {sym: ExtremalLabel}
          args:
            - call: {head: {sym: PathLabel}, args: [{var: p}]}
    obligation_skeleton:
      - id: degree-fact
        text: every vertex has degree at least 2
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call:
                      head: {sym: NatLessLabel}
                      args:
                        - {sym: one}
                        - call: {head: {sym: DegreeLabel}, args: [{var: v}]}
      - id: longest-path
        text: choose a longest path in G
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call: {head: {sym: PathLabel}, args: [{var: p}]}
      - id: endpoint-neighbors
        text: the endpoint of the longest path has two neighbors on it
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call: {head: {sym: AdjacentLabel}, args: [{var: v}, {var: w}]}
      - id: conclusion
        text: a cycle exists in G
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call: {head: {sym: CycleLabel}, args: [{var: c}]}
    test_instances:
      - id: k3
        description: "triangle K3: min degree 2, one 3-cycle"
        moves: ""
        final_number: ""
        expected_parity: ""
"""

PIGEONHOLE_YAML = """format: hyge-training-records
version: 1
records:
  - id: tier0_pigeonhole_residue_classes_rehearsal
    problem_statement:
      text: >-
        Prove that among any n+1 integers, there exist two whose
        difference is divisible by n.
    meaning_structure:
      start:
        call:
          head: {sym: KnowledgeLabel}
          args:
            - list:
                - call: {head: {sym: IntegersLabel}, args: [{var: s}]}
                - call: {head: {sym: IntegerLabel}, args: [{var: n}]}
                - call: {head: {sym: RemainderLabel}, args: [{var: r}, {var: n}]}
                - call: {head: {sym: ResidueClassLabel}, args: [{var: r}, {var: n}]}
    strategy_hint:
      rules_pack: null
      method:
        call:
          head: {sym: PigeonholeLabel}
          args:
            - call: {head: {sym: IntegersLabel}, args: [{var: s}]}
    obligation_skeleton:
      - id: residue-partition
        text: the n residue classes partition the integers
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call: {head: {sym: ResidueClassLabel}, args: [{var: r}, {var: n}]}
      - id: pigeonhole-step
        text: n+1 integers, n classes, two share a class
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call: {head: {sym: CongruentLabel}, args: [{var: a}, {var: b}]}
      - id: conclusion
        text: the difference of the congruent pair is divisible by n
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call: {head: {sym: DividesLabel}, args: [{var: d}, {var: n}]}
                  - call: {head: {sym: CongruentLabel}, args: [{var: a}, {var: b}]}
    test_instances:
      - id: n3
        description: "n=3, integers 0,1,2,3: 0 and 3 share residue class 0"
        moves: ""
        final_number: ""
        expected_parity: ""
"""

work = tempfile.mkdtemp(prefix="rehearsal-action1-")


def label_name(ns):
    reverse = {}
    for key, value in ns.items():
        reverse.setdefault(id(value), key)
    return lambda term: reverse.get(id(term), "?")


def main():
    from cat_theo_machine.main import _runtime_namespace, boot_from_packs, PACK_PATHS
    from cat_theo_machine.training import TrainingRecordLoader, attempt_training_record
    from cat_theo_machine import machine as M
    from cat_theo_machine.persistence import SnapshotCodec

    ns = _runtime_namespace()
    print("namespace entries:", len(ns))
    missing = [n for n in A1_UNION if n not in ns]
    print("A1 union labels resolving in namespace:", len(A1_UNION) - len(missing), "/", len(A1_UNION))
    if missing:
        print("MISSING:", missing)
        return

    runtime, packs = boot_from_packs(PACK_PATHS, ns)
    name_of = label_name(ns)
    packs_field = getattr(packs, "packs", None)
    print("runtime booted; packs loaded:", len(packs_field) if packs_field is not None else "n/a")

    loader = TrainingRecordLoader(ns)
    for name, text in (("extremal", EXTREMAL_YAML), ("pigeonhole", PIGEONHOLE_YAML)):
        path = os.path.join(work, "tier0-" + name + ".rehearsal.yaml")
        with open(path, "w", encoding="utf-8") as h:
            h.write(text)
        print()
        print("==== record:", name, "====")
        try:
            loaded = loader.load_records_file(path)
        except Exception as exc:
            print("LOADER FAILED:", repr(exc))
            continue
        print("loader accepted:", len(loaded), "record(s)")
        record, rules_pack = loaded[0]
        print("record rules_pack field:", rules_pack)
        meaning = None
        from cat_theo_machine.training import (
            TrainingRecordMeaningStructure,
            TrainingRecordStrategyHint,
            TrainingRecordObligationSkeleton,
        )
        meaning = TrainingRecordMeaningStructure(record)()
        hint = TrainingRecordStrategyHint(record)()
        skeleton = TrainingRecordObligationSkeleton(record)()
        print("meaning structure term head label:", name_of(M.Head(meaning)()))
        print("strategy hint head label:", name_of(M.Head(hint)()) if M.IdentityCompare(hint, M.EmptyList)() is M.false_value else "none")
        obligations = 0
        cursor = skeleton
        while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
            obligations += 1
            cursor = M.Tail(cursor)()
        print("obligation skeleton entries:", obligations)

        try:
            attempt, summary = attempt_training_record(runtime, packs, record, None)
            print("attempt status_text:", summary.status_text)
            print("attempt method_text:", summary.method_text)
            print("planner root status:", summary.planner_root_status)
            print("alternative status:", summary.alternative_status)
            print("retained:", summary.retained)
            print("failure reason:", summary.failure_reason)
        except Exception as exc:
            print("ATTEMPT CYCLE RAISED:", repr(exc))

    print()
    print("==== codec round-trip (shadow vocabulary terms) ====")
    from cat_theo_machine import labels as L
    term = M.Pair(
        L.GraphLabel,
        M.Pair(M.Char("g"), M.Pair(L.VertexLabel, M.Pair(M.Char("v"), M.EmptyList))),
    )
    runtime.graph.add_node(term)
    snap_path = os.path.join(work, "rehearsal-roundtrip.snapshot.json")
    codec = SnapshotCodec(ns)
    codec.save(runtime.graph, snap_path, progress=M.false_value)
    state = codec.load(snap_path)
    survived = "GraphLabel" in state.symbols and state.symbols["GraphLabel"] is L.GraphLabel
    print("GraphLabel singleton survives round-trip by identity:", survived)
    rebuilt = M.Pair(
        L.GraphLabel,
        M.Pair(M.Char("g"), M.Pair(L.VertexLabel, M.Pair(M.Char("v"), M.EmptyList))),
    )
    print("value equality of rebuilt term via M.Compare:", M.Compare(rebuilt, term)() is M.truth_value)
    print("round-trip snapshot bytes:", os.path.getsize(snap_path))

    shutil.rmtree(work, ignore_errors=True)
    print()
    print("scratch dir removed; nothing written into the repository tree")


if __name__ == "__main__":
    main()
