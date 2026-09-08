#!/usr/bin/env python3
"""Rehearsal runner — Action 2: Ground-3 count-target generator rehearsal.

What this decides (operator-sanctioned rehearsal, 2026-09-08):
  1. are the RECORDED fixed skeleton shapes (protocol/G.md, Ground-3
     ruling) emittable as machine terms — Divide: PartitionExhaustive,
     PartitionDisjoint, PartCount per part, Recurrence, BaseCase,
     ClosedForm; Symmetry: GroupDeclared, ActionWellDefined,
     FixedPointCount per g, OrbitCountByAveraging, ClosedForm;
  2. does a count-target record whose obligation goals reference those
     emission labels compile via the real loader (with the shadow
     obligation labels present);
  3. does the planner accept the emitted ClosedForm obligation as a
     goal without crashing (planner acceptance);
  4. discharge is NOT tested: discharging a count obligation needs pack
     content (G-eng G1-completion deliverable; D11-content-pending).

The generator logic lives in THIS SCRIPT (scratch); the shadow labels
live in the rehearsal clone. Neither lands. The emission names are the
RECORDED ones (protocol/G.md fixed skeleton shapes) — the proposal's
CountEqualsObligation / RecurrenceEvaluationObligation /
GroupActionObligation names appear nowhere in the record and are not
used.

Usage: python3 <this-file> <repo-root>
"""
import os
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
PKG_PARENT = "/tmp/rehearsal-action2-pkg"
os.makedirs(PKG_PARENT, exist_ok=True)
link = os.path.join(PKG_PARENT, "cat_theo_machine")
if not os.path.lexists(link):
    os.symlink(ROOT, link)
sys.path.insert(0, PKG_PARENT)

DIVIDE_ORDER = ["PartitionExhaustiveLabel", "PartitionDisjointLabel", "PartCountLabel",
                "PartCountLabel", "RecurrenceLabel", "BaseCaseLabel", "ClosedFormLabel"]
SYMMETRY_ORDER = ["GroupDeclaredLabel", "ActionWellDefinedLabel", "FixedPointCountLabel",
                  "FixedPointCountLabel", "FixedPointCountLabel", "FixedPointCountLabel",
                  "OrbitCountByAveragingLabel", "ClosedFormLabel"]


def label_name(ns):
    reverse = {}
    for key, value in ns.items():
        reverse.setdefault(id(value), key)
    return lambda term: reverse.get(id(term), "?")


def main():
    from cat_theo_machine.main import _runtime_namespace, boot_from_packs, PACK_PATHS
    from cat_theo_machine.training import TrainingRecordLoader, pretty
    from cat_theo_machine import machine as M
    from cat_theo_machine import labels as L

    ns = _runtime_namespace()
    needed = ["PartitionExhaustiveLabel", "PartitionDisjointLabel", "PartCountLabel",
              "RecurrenceLabel", "BaseCaseLabel", "ClosedFormLabel", "GroupDeclaredLabel",
              "ActionWellDefinedLabel", "FixedPointCountLabel", "OrbitCountByAveragingLabel"]
    missing = [n for n in needed if n not in ns]
    print("obligation labels resolving:", len(needed) - len(missing), "/", len(needed), ("MISSING: " + str(missing)) if missing else "")

    def obl(label, payload_text):
        char_chain = M.EmptyList
        for ch in reversed(payload_text):
            char_chain = M.Pair(M.Char(ch), char_chain)
        return M.Pair(getattr(L, label), M.Pair(char_chain, M.EmptyList))

    def chain(terms):
        out = M.EmptyList
        for t in reversed(terms):
            out = M.Pair(t, out)
        return out

    print()
    print("== Divide emission (binary words, no adjacent ones) ==")
    divide_terms = [
        obl("PartitionExhaustiveLabel", "parts: leading-0 | leading-1"),
        obl("PartitionDisjointLabel", "parts disjoint"),
        obl("PartCountLabel", "a(n-1) words leading-0"),
        obl("PartCountLabel", "a(n-2) words leading-10"),
        obl("RecurrenceLabel", "a(n)=a(n-1)+a(n-2)"),
        obl("BaseCaseLabel", "a(1)=2, a(2)=3"),
        obl("ClosedFormLabel", "F(n+2)"),
    ]
    name_of = label_name(ns)
    emitted = [name_of(M.Head(t)()) for t in divide_terms]
    print("emitted order:", emitted)
    print("matches recorded Divide skeleton order:", emitted == DIVIDE_ORDER)
    divide_chain = chain(divide_terms)
    print("chain length:", sum(1 for _ in iter_chain(divide_chain)))

    print()
    print("== Symmetry emission (square vertex colorings under C4) ==")
    symmetry_terms = [
        obl("GroupDeclaredLabel", "C4 rotations"),
        obl("ActionWellDefinedLabel", "rotation acts on colorings"),
        obl("FixedPointCountLabel", "identity: m^4"),
        obl("FixedPointCountLabel", "rot90: m"),
        obl("FixedPointCountLabel", "rot180: m^2"),
        obl("FixedPointCountLabel", "rot270: m"),
        obl("OrbitCountByAveragingLabel", "(m^4+m^2+2m)/4"),
        obl("ClosedFormLabel", "(m^4+m^2+2m)/4"),
    ]
    emitted_s = [name_of(M.Head(t)()) for t in symmetry_terms]
    print("emitted order:", emitted_s)
    print("matches recorded Symmetry skeleton order:", emitted_s == SYMMETRY_ORDER)

    print()
    print("== loader compile of a count-record referencing emission labels ==")
    yaml_text = """format: hyge-training-records
version: 1
records:
  - id: tier0_divide_binary_words_rehearsal
    problem_statement:
      text: >-
        Find the number of binary words of length n that do not contain
        two adjacent ones.
    meaning_structure:
      start:
        call:
          head: {sym: KnowledgeLabel}
          args:
            - list:
                - call: {head: {sym: BinaryWordLabel}, args: [{var: w}]}
                - call: {head: {sym: AdjacentLabel}, args: [{var: x}, {var: y}]}
                - call: {head: {sym: WordLabel}, args: [{var: w}]}
    strategy_hint:
      rules_pack: null
      method:
        call:
          head: {sym: DivideLabel}
          args:
            - call: {head: {sym: BinaryWordLabel}, args: [{var: w}]}
    obligation_skeleton:
      - id: partition-exhaustive
        text: parts cover all words
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call: {head: {sym: PartitionExhaustiveLabel}, args: [{var: parts}]}
      - id: recurrence
        text: the recurrence holds
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call: {head: {sym: RecurrenceLabel}, args: [{var: rec}]}
      - id: closed-form
        text: the count is F(n+2)
        goal:
          call:
            head: {sym: KnowledgeLabel}
            args:
              - list:
                  - call: {head: {sym: ClosedFormLabel}, args: [{var: formula}]}
    test_instances:
      - id: n3
        description: "n=3 -> 5 words"
        moves: ""
        final_number: "5"
        expected_parity: ""
"""
    path = "/tmp/rehearsal-action2-count.yaml"
    with open(path, "w", encoding="utf-8") as h:
        h.write(yaml_text)
    loader = TrainingRecordLoader(ns)
    loaded = loader.load_records_file(path)
    print("count-record loader verdict: accepted", len(loaded), "record(s)")
    from cat_theo_machine.training import (
        TrainingRecordMeaningStructure, TrainingRecordStrategyHint,
        TrainingRecordObligationSkeleton, ObligationSkeletonEntryGoal,
        ObligationSkeletonEntryId,
    )
    record, _ = loaded[0]
    skeleton = TrainingRecordObligationSkeleton(record)()
    reg = M.FromContextGetConstructors(boot.graph)() if False else None
    cursor = skeleton
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        entry = M.Head(cursor)()
        g = ObligationSkeletonEntryGoal(entry)()
        print("obligation goal head label:", name_of(M.Head(g)()))
        cursor = M.Tail(cursor)()

    print()
    print("== planner acceptance of the ClosedForm goal ==")
    print("note: PlannerProblem with rules=None crashes (IdentityCompare over None);")
    print("the attempt cycle hides that in its try/except. Below uses the ordered")
    print("library chain -- the same substitution runtime.prove performs.")
    from cat_theo_machine import planner as Plannermod
    runtime, packs = boot_from_packs(PACK_PATHS, ns)
    start = TrainingRecordMeaningStructure(record)()
    hint = TrainingRecordStrategyHint(record)()
    closed_goal = M.Pair(
        L.KnowledgeLabel,
        M.Pair(M.Pair(L.ClosedFormLabel, M.Pair(M.Char("F"), M.EmptyList)), M.EmptyList),
    )
    methods = M.Pair(hint, M.EmptyList) if M.IdentityCompare(hint, M.EmptyList)() is M.false_value else M.EmptyList
    problem = Plannermod.PlannerProblem(start, closed_goal, runtime.ordered_rules(), runtime.theorem_heuristic, methods)()
    state = Plannermod.PlannerState(problem, M.FromContextGetConstructors(runtime.graph)())()
    final_state = Plannermod.PlannerRun(runtime.graph, state, M.three)()
    alternatives = Plannermod.PlannerStateAlternatives(final_state)()
    print("planner ran without crash; alternatives:", "yes" if M.IdentityCompare(alternatives, M.EmptyList)() is M.false_value else "none")
    print("root status stays pending-shaped (no vacuous prove):",
          "checked by attempt cycle separately")

    print()
    print("== discharge-in-principle ==")
    print("NOT TESTED: discharging a count obligation needs pack content")
    print("(G-eng G1-completion deliverable; D11-content-pending). The")
    print("rehearsal covers emittability, loader compile, planner acceptance.")


def iter_chain(chain):
    from cat_theo_machine import machine as M
    cursor = chain
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        yield M.Head(cursor)()
        cursor = M.Tail(cursor)()


if __name__ == "__main__":
    main()
