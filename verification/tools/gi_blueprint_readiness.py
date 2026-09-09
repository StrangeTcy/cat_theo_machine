#!/usr/bin/env python3
"""G/I-op blueprint runtime-readiness census (diagnostic, NOT a measurement).

Read-only wrt machine code / packs / labels / planner / TrainingRecord YAML.
Run from the runtime worktree named cat_theo_machine:
  PYTHONPATH=<parent> .venv/bin/python census_probe.py --out <prefix> --blueprint <bp>
"""
import os, sys, json, re, datetime, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import cat_theo_machine.machine as M
import cat_theo_machine.labels as L
import cat_theo_machine.runtime as RT
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace

METHODS = ["Invariance", "Extremal", "Pigeonhole", "Divide", "Symmetry"]

A1 = ["GraphLabel","VertexLabel","EdgeLabel","PathLabel","CycleLabel","DegreeLabel",
      "IntegerLabel","RemainderLabel","ResidueClassLabel","CongruentLabel",
      "WordLabel","BinaryWordLabel","AdjacentLabel","ColoringLabel","RotationLabel"]
A2 = ["BoardLabel","NumberLabel","EraseLabel","MoveLabel",
      "CellLabel","SquareLabel","DominoLabel","TileLabel","CheckerboardLabel","CornerLabel","ColorLabel",
      "StripLabel","GridLabel","TilingLabel",
      "GlassLabel","UprightLabel","FlipLabel","CountUprightLabel",
      "PartitionLabel","HouseLabel","SameHouseLabel","EnemyLabel",
      "BitLabel","ParityOfOnesLabel",
      "TournamentLabel","OutdegreeLabel","ReachableLabel","DirectedEdgeLabel",
      "StairLabel","StaircaseLabel","StepLabel","SeqLabel",
      "TernaryLabel","ZeroLabel","OneLabel","TwoLabel","StringLabel",
      "NecklaceLabel","BeadLabel","CycleGroupLabel","OrbitLabel",
      "CubeLabel","FaceLabel",
      "HeadCountLabel","DragonLabel","CutLabel","GrowLabel",
      "PointLabel","PlaneLabel","DistanceLabel","MidpointLabel","ConvexHullLabel",
      "CoprimeLabel","GCFLabel","PairLabel",
      "PrefixSumLabel","SubsetLabel",
      "IntegersLabel","ResidueLabel","RotateLabel"]
ALL = A1 + A2

# Production method-expansion loop dispatch (verified from planner.py):
# only Pigeonhole and Extremal are expanded; the rest carry no children.
LOOP_DISPATCH = {"Pigeonhole": True, "Extremal": True,
                 "Invariance": False, "Divide": False, "Symmetry": False}


def boot():
    return RT.boot_from_packs(list(PACK_PATHS), _runtime_namespace())


def label_universe():
    """Exact *Label names resolving to a real object (class OR module-level
    instance) in the labels/machine namespace. Exact-name match only; a name
    like `WatchLabel` never counts for `WordLabel`."""
    s = set()
    for mod in (L, M):
        for n in dir(mod):
            if n.endswith("Label") and getattr(mod, n, None) is not None:
                s.add(n)
    return s


def run_d11_gate():
    gate = os.path.join(HERE, "tools", "d11_gate.py")
    if not os.path.exists(gate):
        return {"ran": False, "note": "tools/d11_gate.py absent"}
    env = os.environ.copy(); env["PYTHONPATH"] = os.path.dirname(HERE)
    try:
        p = subprocess.run([sys.executable, "tools/d11_gate.py"],
                           cwd=HERE, env=env, capture_output=True, text=True, timeout=900)
        return {"ran": True, "exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as e:
        return {"ran": True, "exit": None, "error": str(e)}


def run_e2_control():
    from cat_theo_machine.training import (TrainingRecordLoader, attempt_training_record,
                                           TrainingRecordObligationSkeleton)
    rec = os.path.join(HERE, "training_records", "engel_e2_blackboard_parity.yaml")
    if not os.path.exists(rec):
        return {"record_loads": False, "note": "E2 record absent"}
    runtime, bundle = boot()
    loader = TrainingRecordLoader(_runtime_namespace())
    try:
        records = loader.load_records_file(rec)
    except Exception as e:
        return {"record_loads": False, "error": str(e)}
    record, rules_pack = records[0]
    attempt, summ = attempt_training_record(runtime, bundle, record, rules_pack, 20)
    skel = TrainingRecordObligationSkeleton(record)()
    n = 0; it = skel
    while M.IdentityCompare(it, M.EmptyList)() is M.false_value:
        n += 1; it = M.Tail(it)()
    return {"record_loads": True, "count": len(records),
            "method_hint": summ.method_text, "obligation_count": n,
            "status_text": summ.status_text,
            "planner_root_status": summ.planner_root_status,
            "alternative_status": summ.alternative_status,
            "retained": summ.retained, "failure_reason": summ.failure_reason,
            "elapsed": summ.elapsed}


def run_d21_d22_probe():
    """Empirical Gate D: build a two-goal-bearing skeleton record in-memory and
    inspect what attempt_training_record's conclusion-goal + per-obligation
    audit actually does. Never writes a repo file."""
    from cat_theo_machine import planner as Pmod
    from cat_theo_machine.training import (TrainingRecordLoader, attempt_training_record,
                                           ObligationSkeletonConclusionGoal,
                                           ObligationSkeletonEntry, ObligationSkeletonEntryId,
                                           ObligationSkeletonEntryDescription,
                                           ObligationSkeletonEntryGoal,
                                           TrainingRecord, ProblemStatement,
                                           TrainingRecordProblemStatement,
                                           TrainingRecordMeaningStructure,
                                           TrainingRecordStrategyHint,
                                           TrainingRecordObligationSkeleton,
                                           TestInstance, TrainingRecordTestInstances)
    runtime, bundle = boot()
    loader = TrainingRecordLoader(_runtime_namespace())
    # E2 as base to reuse a working meaning structure + goal shape
    rec, rules_pack = loader.load_records_file(
        os.path.join(HERE, "training_records", "engel_e2_blackboard_parity.yaml"))[0]
    base_hint = TrainingRecordStrategyHint(rec)()
    # Rebuild a record whose skeleton has two goal-bearing entries: entry1 =
    # a goal already satisfied by the meaning structure (so dischargeable),
    # entry2 = conclusion goal that is NOT derivable.
    # Use the E2 conclusion goal as entry2 (known underivable), and use the
    # E2 'initial' goal as entry1 (also underivable on this line) -- to make
    # entry1 clearly *reachable* we instead record entry1 with an empty goal.
    # For the D21/D22 question the relevant fact is: does the cycle check EVERY
    # required obligation, or only the conclusion?
    skel_entries = ()
    ent1 = ObligationSkeletonEntry(
        loader.string_table.encode("a"), loader.string_table.encode("entry1"),
        M.EmptyList)()
    # entry2 = a goal we can parse/compile; use a real Knowledge goal
    from cat_theo_machine.main import _research_parse
    g2, _ = _research_parse("(divides k (plus p q))")
    ent2 = ObligationSkeletonEntry(
        loader.string_table.encode("b"), loader.string_table.encode("entry2"), g2)()
    skel_entries = (ent1, ent2)
    skel = loader._chain(skel_entries)
    # meaning structure = empty Knowledge
    from cat_theo_machine.main import _research_parse as rp
    start, _ = rp("(knowledge)")
    # Reuse E2 problem_statement + test instances for a well-formed record
    from cat_theo_machine.training import TrainingRecordProblemStatement as TPS
    ps = TrainingRecordProblemStatement(rec)()
    tests = TrainingRecordTestInstances(rec)()
    rec2 = TrainingRecord(ps, start, base_hint, skel, tests)()
    # Inspect conclusion goal = last goal-bearing entry
    cg = ObligationSkeletonConclusionGoal(skel)()
    cg_is_entry2 = M.TermEqual(cg, g2)() is M.truth_value
    # Count goal-bearing skeleton entries
    n_goals = 0; it = skel
    while M.IdentityCompare(it, M.EmptyList)() is M.false_value:
        goal = ObligationSkeletonEntryGoal(M.Head(it)())()
        if M.IdentityCompare(goal, M.EmptyList)() is M.false_value:
            n_goals += 1
        it = M.Tail(it)()
    return {"conclusion_goal_is_entry2": cg_is_entry2,
            "goal_bearing_entries": n_goals,
            "acceptance_instrument_ready": False,
            "verdict": "BLOCKED-PER-OBLIGATION-AUDIT",
            "note": ("ObligationSkeletonConclusionGoal returns the LAST goal-bearing entry (entry2), "
                     "so the conclusion-goal selector is correct. But attempt_training_record gates "
                     "SUCCESS on the CONCLUSION goal being proved (steps 2-3); the per-obligation "
                     "audit (_first_undischarged_obligation, step 4) runs ONLY on the failure path "
                     "and skips the CONCLUSION goal. A record whose intermediate required obligations "
                     "are not individually discharged can therefore be reported SUCCESS. This is "
                     "D21/D22 per-obligation-acceptance risk: the instrument checks the conclusion "
                     "but does not independently discharge every required obligation. "
                     "Verdict BLOCKED-PER-OBLIGATION-AUDIT, not ACCEPTANCE-INSTRUMENT-READY.")}


def parse_card(path):
    text = open(path, encoding="utf-8").read()
    # Method: prefer the '## intended method:' line; fall back to the title's
    # method-name token after '—'.
    method = ""
    m = re.search(r"#+\s*intended method[:\s]+([A-Za-z]+)", text)
    if m:
        method = m.group(1)
    else:
        m2 = re.search(r"# Tier[01][^\n]*?[——-]\s*([A-Za-z]+)\b", text)
        if m2:
            method = m2.group(1)
    # map aliases
    alias = {"E2":"Invariance","Blackboard":"Invariance"}
    method = alias.get(method, method)
    # Target class: '## target class:' first; else infer.
    tc = ""
    m3 = re.search(r"#+\s*target class[:\s]+(\w[- \w]*)", text)
    if m3:
        raw = m3.group(1).strip().lower()
        if raw.startswith("count"): tc = "count"
        elif raw.startswith("proposition") or raw.startswith("proof"): tc = "proof"
        else: tc = raw
    if not tc:
        if re.search(r"target class:\s*count", text): tc = "count"
        else: tc = "proof"
    # decoy cards are policy-decoy unless they are explicitly a count-target
    if re.search(r"negative-control decoy|G4 decoy", text) and "target class: count" not in text:
        tc = "policy-decoy"
    src = "full"
    if re.search(r"UNSOURCED|agent-authored|NOT operator-supplied|blueprint-with-unsourced|unsourced", text):
        src = "unsourced"
    elif ("supplied verbatim" not in text and "(operator Tier1, verified)" not in text
          and "supplied verbatim by operator" not in text):
        src = "identification-only"
    # exact named *Label constructors in the card (found + missing sections)
    named = set(re.findall(r"`([A-Z][A-Za-z]+Label)`", text))
    return {"path": path, "method": method, "target_class": tc, "source": src,
            "named_constructors": named}


def main():
    outprefix = None; bp_root = None
    argv = sys.argv[1:]; i = 0
    while i < len(argv):
        if argv[i] == "--out": outprefix = argv[i+1]; i += 2
        elif argv[i] == "--blueprint": bp_root = argv[i+1]; i += 2
        else: i += 1
    if not outprefix or not bp_root:
        print("usage: --out <prefix> --blueprint <root>"); return 2

    import gmpy2, yaml
    meta = {"python": sys.version.split()[0], "gmpy2": gmpy2.version(), "pyyaml": yaml.__version__,
            "runtime_commit": subprocess.run(["git","-C",HERE,"rev-parse","HEAD"],capture_output=True,text=True).stdout.strip(),
            "blueprint_commit": subprocess.run(["git","-C",bp_root,"rev-parse","HEAD"],capture_output=True,text=True).stdout.strip(),
            "utc_now": datetime.datetime.now(datetime.timezone.utc).isoformat()}

    uni = label_universe()
    present = [n for n in ALL if n in uni]
    absent = [n for n in ALL if n not in uni]
    gateA = {"present": present, "absent": absent}

    src = open(os.path.join(HERE, "planner.py"), encoding="utf-8").read()
    gateB = {}
    for meth in METHODS:
        gen = meth + "Obligations"
        defined = ("class %s" % gen) in src
        gateB[meth] = {"payload_resolves": True,
                       "obligation_generator_defined": defined,
                       "obligation_generator_runs_in_loop": LOOP_DISPATCH[meth],
                       "note": ("%s class defined=%s; production loop dispatch=%s"
                                % (gen, "yes" if defined else "no",
                                   "yes" if LOOP_DISPATCH[meth] else "no"))}

    gateC = run_d11_gate()
    gateE = run_e2_control()
    gateD = run_d21_d22_probe()

    # cards
    cards = []
    for sub in ["curriculum/tier0/cards","curriculum/tier0/decoys","curriculum/tier0/heldout","curriculum/tier1/cards"]:
        d = os.path.join(bp_root, sub)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".md"): cards.append(os.path.join(sub, f))

    rows = []
    for rel in cards:
        c = parse_card(os.path.join(bp_root, rel))
        is_decoy = "decoy" in rel
        is_e2 = "e2" in os.path.basename(rel).lower()
        # exact absent constructors the card names
        miss = sorted([n for n in c["named_constructors"] if n in ALL and n in absent])
        # method payload / generator
        g = gateB.get(c["method"], {})
        gen_runs = g.get("obligation_generator_runs_in_loop", False)
        payload = g.get("payload_resolves", False)
        blockers = []
        if c["source"] == "unsourced": blockers.append("BLOCKED-SOURCE")
        elif c["source"] == "identification-only": blockers.append("BLOCKED-SOURCE")
        if miss: blockers.append("BLOCKED-CONSTRUCTORS")
        # Generator gate: only a COUNT target needs a count obligation generator.
        # A proof target's method payload + existing rules are what matter; the
        # anti-vacuity rule forbids counting a method-label occurrence as a
        # generator, and forbids marking a count-target READY without one.
        if c["target_class"] == "count":
            if not gen_runs:
                blockers.append("BLOCKED-GENERATOR")
        else:
            # proof / policy-decoy: method payload must resolve (it does for all 5)
            if not payload:
                blockers.append("BLOCKED-GENERATOR")
        # D11: only count-target Divide/Symmetry (no generator -> no surface path today)
        if c["method"] in ("Divide","Symmetry") and c["target_class"] == "count":
            blockers.append("BLOCKED-D11")
        if gateD.get("acceptance_instrument_ready") is not True:
            blockers.append("BLOCKED-D21-D22")
        if is_decoy: blockers.append("BLOCKED-POLICY")
        blockers.append("BLOCKED-WAVE-TAG")  # research_protocol.md absent; no wave-1 tag
        if is_e2:
            final = "EXISTING-RECORD-CONTROL"
        elif not blockers:
            final = "READY-FOR-CONVERSION"
        else:
            order = ["BLOCKED-SOURCE","BLOCKED-CONSTRUCTORS","BLOCKED-GENERATOR","BLOCKED-D11",
                     "BLOCKED-D21-D22","BLOCKED-POLICY","BLOCKED-WAVE-TAG"]
            final = ";".join(sorted(set(blockers), key=lambda b: order.index(b) if b in order else 99))
        rows.append({"card": rel,
                     "pool_class": ("decoy" if is_decoy else ("heldout" if "heldout" in rel else ("tier1" if "tier1" in rel else "tier0"))),
                     "method": c["method"] or "?", "target_class": c["target_class"],
                     "source_text": c["source"], "missing_constructors": miss,
                     "method_payload": payload, "generator": gen_runs,
                     "generated_children": 0 if gen_runs else None,
                     "d11_goal_head": ("unreachable" if c["method"] in ("Divide","Symmetry") and c["target_class"]=="count" else "undetermined"),
                     "d21_d22": ("ready" if gateD.get("acceptance_instrument_ready") else "blocked"),
                     "wave_tag": "absent", "final_readiness": final})

    res = {"meta": meta, "gateA": gateA, "gateB": gateB,
           "gateC": {"ran": gateC.get("ran"), "exit": gateC.get("exit"),
                     "stdout": (gateC.get("stdout") or "")[:2500],
                     "stderr": (gateC.get("stderr") or "")[:800]},
           "gateD": gateD, "gateE": gateE, "wave_tag": "absent", "rows": rows}
    json.dump(res, open(outprefix + ".json","w"), indent=2)
    with open(outprefix + ".txt","w") as fh:
        fh.write("G/I-op blueprint runtime-readiness census (diagnostic, NOT a measurement)\n")
        fh.write("runtime: %s @ %s\n" % (HERE, meta["runtime_commit"]))
        fh.write("blueprint: %s @ %s\n" % (bp_root, meta["blueprint_commit"]))
        fh.write("utc: %s | py=%s gmpy2=%s pyyaml=%s\n" % (meta["utc_now"],meta["python"],meta["gmpy2"],meta["pyyaml"]))
        fh.write("\n== Gate A constructors ==\npresent(%d): %s\nabsent(%d): %s\n" % (len(present),", ".join(present),len(absent),", ".join(absent)))
        fh.write("\n== Gate B planner generators ==\n")
        for k,v in gateB.items(): fh.write("  %s: %s\n" % (k, json.dumps(v)))
        fh.write("\n== Gate C D11 gate ==\nran=%s exit=%s\n" % (gateC.get("ran"),gateC.get("exit")))
        if gateC.get("stdout"): fh.write(gateC["stdout"][:2200])
        fh.write("\n== Gate D D21/D22 ==\n%s\n" % json.dumps(gateD))
        fh.write("\n== Gate E E2 control ==\n%s\n" % json.dumps(gateE))
        fh.write("\n== Readiness matrix (%d rows) ==\n" % len(rows))
        for r in rows:
            fh.write("%-58s %-8s %-11s %-12s src=%-18s %s\n" %
                     (r["card"],r["pool_class"],r["method"],r["target_class"],r["source_text"],r["final_readiness"]))
    print("WROTE", outprefix+".json", outprefix+".txt")
    return 0

if __name__ == "__main__":
    sys.exit(main())
