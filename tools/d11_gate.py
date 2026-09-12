#!/usr/bin/env python3
"""D11 diagnostic-isolation gate, version 2.

Re-runnable from a fresh clone:

    python3 tools/d11_gate.py              # all gated conditions
    python3 tools/d11_gate.py --baseline   # (re)record the shipped-167 digest
    python3 tools/d11_gate.py --safety-probe
    python3 tools/d11_gate.py --live-ingress-probe

Version 2 preserves the arithmetic surface-port checks, but supersedes the
old executable B/C partial-match expectation. The shell pack contributes two
diagnostic records and zero fireable proof rules: B/C have one diagnostic
candidate, zero proof-rule candidates, and an empty returned derivation.
The gate also rejects supplied Need facts, empty-premise taught Need rules,
restored supplied facts, and replayed taught Need rules as paths to either
shell conclusion. The live toy verifies parsed -> submitted -> received goal
identity before recording its diagnostic-only result.

Exit status is 0 only if every gated condition passes.
"""

import hashlib
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for candidate in (ROOT, os.path.dirname(ROOT)):
    if os.path.isdir(os.path.join(candidate, "cat_theo_machine")):
        PKG_ROOT = candidate
        break
else:
    PKG_ROOT = os.path.dirname(ROOT)

if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

from cat_theo_machine import machine as M  # noqa: E402
from cat_theo_machine import research as Rmod  # noqa: E402
from cat_theo_machine import runtime as RT  # noqa: E402
from cat_theo_machine.main import (  # noqa: E402
    PACK_PATHS,
    _research_nat_text,
    _research_parse,
    _runtime_namespace,
    _term_text,
)
from cat_theo_machine.proof import CollectRules  # noqa: E402
from cat_theo_machine import proof_ingress as Ingress  # noqa: E402

SPIKE_DIR = os.path.join(ROOT, "protocol", "d11-spike")
DIGEST_PATH = os.path.join(SPIKE_DIR, "shipped-167-rules.sha256")
PACK_DIGEST_PATH = os.path.join(SPIKE_DIR, "shipped-pack-digests.txt")

# The D11 content port: which shipped packs declare a surface: header, and
# the probe the port is meant to win.
PORTED_PACKS = ("arithmetic",)
PORT_PROBE = "(eq (pow t 6) (pow (pow t 2) 3))"

PROBE_GOAL = "(divides k (plus p q))"
UNRELATED_GOAL = "(cornersum t whole)"

LABEL_FIXTURE = os.path.join(SPIKE_DIR, "d11-spike-label.pack.yaml")
MAPPED_FIXTURE = os.path.join(SPIKE_DIR, "d11-spike-mapped.pack.yaml")
CHAR_FIXTURE = os.path.join(SPIKE_DIR, "d11-spike-char.pack.yaml")

results = []


def kind_text(term, depth=0):
    """Kind-sensitive structural text: the class name of every atom.

    PrettyTerm cannot render a ConstructorLabel -- it prints "?" -- so the
    digest built on it alone cannot see a Label re-keyed to a Char. This
    walk can: the two are different classes. Pair shape is preserved, so a
    head moved from one position to another also changes the digest.
    """
    if depth > 80:
        return "..."
    try:
        if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
            return type(term).__name__
    except Exception:
        return type(term).__name__
    if isinstance(term, M.Pair):
        return "P(%s,%s)" % (
            kind_text(M.Head(term)(), depth + 1),
            kind_text(M.Tail(term)(), depth + 1),
        )
    return type(term).__name__


def pretty_text(term, graph):
    try:
        text = _term_text(term, graph)
    except Exception:
        text = None
    if text and text != "?":
        return text
    return _structural_text(term)


def render(rule, graph):
    """Fingerprint for one compiled rule: kind walk + rendered content.

    A rule is a host Edge, not a machine term -- rendering it directly
    yields its repr with a memory address, which would make every run look
    like drift. EdgeInputs is the machine term underneath.
    """
    try:
        inputs = M.EdgeInputs(rule)()
    except Exception:
        inputs = rule
    return kind_text(inputs) + "||" + pretty_text(inputs, graph)


def _structural_text(term, depth=0):
    if depth > 64:
        return "..."
    if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
        return "()"
    try:
        head = M.Head(term)()
        tail = M.Tail(term)()
    except Exception:
        return type(term).__name__
    return "(%s . %s)" % (_structural_text(head, depth + 1),
                          _structural_text(tail, depth + 1))


def pack_digests(packs, graph):
    """One digest per loaded pack, over its own rules."""
    out = []
    for pack in packs:
        rules = walk(getattr(pack, "rule_chain", M.EmptyList))
        body = "\n".join(render(r, graph) for r in rules)
        out.append((pack.name, len(rules),
                    hashlib.sha256(body.encode("utf-8")).hexdigest()))
    return out


def rule_id_index(packs):
    """(rule object) -> "pack/rule_id", for attributing a match."""
    index = {}
    for pack in packs:
        rule_map = getattr(pack, "rule_map", None)
        entries = getattr(rule_map, "entries", ())
        for name, value in entries:
            index[id(value)] = "%s/%s" % (pack.name, name)
    return index


def rules_of(graph):
    return CollectRules(M.FromContextGetAllRules(graph)())()


def walk(chain):
    items = ()
    while M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
        items = items + (M.Head(chain)(),)
        chain = M.Tail(chain)()
    return items


def boot(paths):
    """Boot a fresh runtime with these packs; return (runtime, loaded packs)."""
    runtime, _pack_bundle = RT.boot_from_packs(list(paths), _runtime_namespace())
    return runtime, getattr(runtime, "loaded_packs", ())


def probe(runtime, goal_text, packs=(), start_facts=None, rule_chain=None):
    """One goal attempt through the real research path. Returns a summary."""
    graph = runtime.graph
    id_index = rule_id_index(packs)
    term, err = _research_parse(goal_text)
    if term is None:
        raise RuntimeError("cannot parse goal %r: %s" % (goal_text, err))
    if start_facts is None:
        start_facts = Rmod.axiom_facts(graph)
    if rule_chain is None:
        rule_chain = rules_of(graph)
    outcome = Rmod.attempt_goal(
        graph, start_facts, M.Pair(term, M.EmptyList), rule_chain
    )
    attempts = walk(getattr(graph, "research_attempts", M.EmptyList))
    rule_ids = ()
    for attempt in attempts:
        # AttemptedRuleId hands back the rule object, not a printable id,
        # so resolve it against each pack's rule map by identity.
        label = "<unattributed>"
        try:
            rule_obj = Rmod.AttemptedRuleId(attempt)()
            if id(rule_obj) in id_index:
                label = id_index[id(rule_obj)]
            else:
                label = "unknown-rule@%x" % (id(rule_obj) & 0xFFFFFFFF)
        except Exception:
            label = "<unreadable>"
        rule_ids = rule_ids + (label,)
    origins = ()
    for attempt in attempts:
        try:
            origins = origins + (_term_text(Rmod.AttemptedRuleOrigin(attempt)(), graph),)
        except Exception:
            origins = origins + ("<unreadable>",)
    closed = Rmod.ForwardSearchClosed(outcome)()
    return {
        "count": len(attempts),
        "cost": _research_nat_text(Rmod.ForwardSearchCost(outcome)()),
        "closed": M.IdentityCompare(closed, M.truth_value)() is M.truth_value,
        "origins": origins,
        "rule_ids": rule_ids,
    }


def record(name, ok, detail):
    results.append((name, ok, detail))
    print("[%s] %s" % ("PASS" if ok else "FAIL", name))
    for line in detail.strip().splitlines():
        print("       " + line)
    return ok


def surface_records(packs):
    """Every PackSurfaceMapping / rule-attribution record the loader emitted."""
    mapping_lines = ()
    rule_lines = ()
    for pack in packs:
        mapping_lines = mapping_lines + tuple(getattr(pack, "surface_mapping_audit", ()))
        rule_lines = rule_lines + tuple(getattr(pack, "surface_mapped_rules", ()))
    return mapping_lines, rule_lines


def ablated_paths(pack_names=PORTED_PACKS):
    """Shipped paths with surface headers stripped from the selected packs."""
    import yaml
    tmpdir = tempfile.mkdtemp(prefix="d11-ablate-")
    out = ()
    for path in PACK_PATHS:
        doc = yaml.safe_load(open(path, encoding="utf-8"))
        if doc.get("name") in pack_names and "surface" in doc:
            del doc["surface"]
            target = os.path.join(tmpdir, os.path.basename(path))
            with open(target, "w", encoding="utf-8") as handle:
                yaml.safe_dump(doc, handle)
            out = out + (target,)
        else:
            out = out + (path,)
    return out


FLT_WORDS = ("fermat", "flt", "wiles", "frey")


def main(argv):
    baseline_mode = "--baseline" in argv
    safety_probe_mode = "--safety-probe" in argv
    live_ingress_probe_mode = "--live-ingress-probe" in argv
    probe_goal = None
    diagnostic_probe_goal = None
    shell_ablation_probe_goal = None
    for i, a in enumerate(argv):
        if a == "--probe" and i + 1 < len(argv):
            probe_goal = argv[i + 1]
        if a == "--diagnostic-probe" and i + 1 < len(argv):
            diagnostic_probe_goal = argv[i + 1]
        if a == "--shell-ablation-probe" and i + 1 < len(argv):
            shell_ablation_probe_goal = argv[i + 1]

    # ---- probe mode: one goal against the shipped packs --------------
    if probe_goal is not None:
        runtime, packs = boot(PACK_PATHS)
        result = probe(runtime, probe_goal, packs)
        print("probe:           %s" % probe_goal)
        print("cost:            %s" % result["cost"])
        print("partial matches: %d" % result["count"])
        print("rule ids:        %s" % (", ".join(result["rule_ids"]) or "none"))
        print("origins:         %s" % (", ".join(result["origins"]) or "none"))
        for attempt in walk(runtime.graph.research_attempts):
            print("unmatched:      %s" % _term_text(
                Rmod.AttemptedRuleUnmatched(attempt)(), runtime.graph
            ))
        return 0

    # ---- diagnostic probe: one goal against isolated shell diagnostics -
    if diagnostic_probe_goal is not None:
        runtime, _packs = boot(PACK_PATHS)
        goal, error = _research_parse(diagnostic_probe_goal)
        if error is not None:
            raise RuntimeError("cannot parse diagnostic goal %r: %s" % (diagnostic_probe_goal, error))
        derivation = runtime.prove(M.truth_value, goal)
        diagnostic = runtime.last_foreground_diagnostic
        count = 0
        if M.IdentityCompare(diagnostic, M.EmptyList)() is M.false_value:
            count = 1
        print("diagnostic probe: %s" % diagnostic_probe_goal)
        print("diagnostic candidates: %d" % count)
        if count == 1:
            print("capability requirement: %s" % _term_text(diagnostic, runtime.graph))
        print("proof result empty: %s" % (
            M.IdentityCompare(derivation, M.EmptyList)() is M.truth_value
        ))
        return 0

    # ---- shell ablation probe: one goal without the shell surface ----
    if shell_ablation_probe_goal is not None:
        runtime, packs = boot(ablated_paths(("shell-characterization",)))
        result = probe(runtime, shell_ablation_probe_goal, packs)
        print("probe:           %s" % shell_ablation_probe_goal)
        print("cost:            %s" % result["cost"])
        print("partial matches: %d" % result["count"])
        print("rule ids:        %s" % (", ".join(result["rule_ids"]) or "none"))
        print("origins:         %s" % (", ".join(result["origins"]) or "none"))
        return 0

    # ---- isolated live ingress diagnostic ---------------------------
    if live_ingress_probe_mode:
        text = "prove that for all n > 1 n + n = n + n"
        runtime, _packs = boot(PACK_PATHS)
        request = Ingress.LiveProofRequest(Ingress.ProofTokenStream(text)())
        direct = Ingress.MathematicalSentence(request.claim)
        submission = Ingress.SubmitForegroundGoal(runtime, request)
        returned = submission()
        received = runtime.last_foreground_goal
        diagnostic = runtime.last_foreground_diagnostic
        passed = (
            request.recognized is M.truth_value
            and request.goal is not M.EmptyList
            and M.Compare(direct.goal, request.goal)() is M.truth_value
            and M.Compare(submission.goal, request.goal)() is M.truth_value
            and M.Compare(received, request.goal)() is M.truth_value
            and M.IdentityCompare(returned, M.EmptyList)() is M.truth_value
            and M.IdentityCompare(diagnostic, M.EmptyList)() is M.false_value
        )
        print("live ingress text: " + text)
        print("parsed goal: " + Ingress.ProofGoalText(request.goal)())
        print("foreground submission: " + Ingress.ProofGoalText(submission.goal)())
        print("worker-received goal: " + Ingress.ProofGoalText(received)())
        print("returned diagnostic: " + _term_text(diagnostic, runtime.graph))
        print("returned derivation: empty")
        if passed:
            print("PASS: parsed goal == foreground submission == worker-received goal; diagnostic only")
            return 0
        print("FAIL: live ingress diagnostic identity or isolation")
        return 1

    # ---- adversarial capability-supply probe ------------------------
    if safety_probe_mode:
        shell_cases = (
            (
                "B",
                "(nosolutions positive-integers (unknowns x) (eq (plus x 1) x))",
                "(NeedContradictionFromArbitrarySolution positive-integers (unknowns x) (eq (plus x 1) x))",
            ),
            (
                "C",
                "(forall n (implies (greater n 1) (eq (plus a a) (plus a a))))",
                "(NeedBinderSafeImplication n (greater n 1) (eq (plus a a) (plus a a)))",
            ),
        )
        for name, goal_text, premise_text in shell_cases:
            premise, premise_error = _research_parse(premise_text)
            if premise_error is not None:
                raise RuntimeError("cannot parse capability premise: %s" % premise_error)

            runtime, packs = boot(PACK_PATHS)
            ordinary_fact = probe(
                runtime, goal_text, packs, M.Pair(premise, M.EmptyList)
            )
            print("%s ordinary capability fact: closed=%s proof-candidates=%d" % (
                name, ordinary_fact["closed"], ordinary_fact["count"]
            ))

            runtime, packs = boot(PACK_PATHS)
            formal = Rmod.FormalRule(M.EmptyList, premise)()
            taught = Rmod.teach_trusted_theorem(runtime.graph, formal)
            taught_rules = M.Pair(taught, rules_of(runtime.graph))
            taught_result = probe(runtime, goal_text, packs, M.EmptyList, taught_rules)
            print("%s empty-premise taught capability: closed=%s proof-candidates=%d" % (
                name, taught_result["closed"], taught_result["count"]
            ))

            directory = tempfile.mkdtemp(prefix="d11-shell-fact-")
            snapshot_path = os.path.join(directory, "state.json")
            runtime, packs = boot(PACK_PATHS)
            Rmod.assume_axiom(runtime.graph, premise)
            runtime.save_snapshot(snapshot_path, _runtime_namespace())
            restored = RT.boot_from_snapshot(
                snapshot_path, _runtime_namespace(), save_upgraded_snapshot=M.false_value
            )
            restored_fact = probe(
                restored, goal_text, (), Rmod.axiom_facts(restored.graph)
            )
            print("%s restored ordinary capability fact: closed=%s proof-candidates=%d" % (
                name, restored_fact["closed"], restored_fact["count"]
            ))
            os.remove(snapshot_path)
            os.rmdir(directory)

            directory = tempfile.mkdtemp(prefix="d11-shell-taught-")
            snapshot_path = os.path.join(directory, "state.json")
            runtime, packs = boot(PACK_PATHS)
            formal = Rmod.FormalRule(M.EmptyList, premise)()
            Rmod.teach_trusted_theorem(runtime.graph, formal)
            runtime.save_snapshot(snapshot_path, _runtime_namespace())
            restored = RT.boot_from_snapshot(
                snapshot_path, _runtime_namespace(), save_upgraded_snapshot=M.false_value
            )
            replayed = Rmod.rebuild_taught_rules(restored.graph)
            replayed_rules = rules_of(restored.graph)
            while M.IdentityCompare(replayed, M.EmptyList)() is M.false_value:
                replayed_rules = M.Pair(M.Head(M.Head(replayed)())(), replayed_rules)
                replayed = M.Tail(replayed)()
            restored_taught = probe(restored, goal_text, (), M.EmptyList, replayed_rules)
            print("%s restored empty-premise taught capability: closed=%s proof-candidates=%d" % (
                name, restored_taught["closed"], restored_taught["count"]
            ))
            os.remove(snapshot_path)
            os.rmdir(directory)
        return 0

    # ---- baseline ----------------------------------------------------
    if baseline_mode:
        runtime, packs = boot(PACK_PATHS)
        rules = walk(rules_of(runtime.graph))
        body = "\n".join(render(r, runtime.graph) for r in rules)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        with open(DIGEST_PATH, "w", encoding="utf-8") as handle:
            handle.write("%d %s\n" % (len(rules), digest))
        with open(PACK_DIGEST_PATH, "w", encoding="utf-8") as handle:
            for name, count, pdigest in pack_digests(packs, runtime.graph):
                handle.write("%s %d %s\n" % (name, count, pdigest))
        print("    recorded baseline: %d rules, sha256 %s" % (len(rules), digest))
        print("    per-pack digests -> %s" % PACK_DIGEST_PATH)
        return 0

    # ---- condition 1: shipped packs, per-pack digest -----------------
    print("== condition 1: shipped packs, unported ones byte-identical ==")
    runtime, packs = boot(PACK_PATHS)
    rules = walk(rules_of(runtime.graph))
    body = "\n".join(render(r, runtime.graph) for r in rules)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    mapping_lines, rule_lines = surface_records(packs)
    result = probe(runtime, PROBE_GOAL, packs)

    pack_base = {}
    if os.path.exists(PACK_DIGEST_PATH):
        for line in open(PACK_DIGEST_PATH, encoding="utf-8"):
            parts = line.split()
            if len(parts) == 3:
                pack_base[parts[0]] = (int(parts[1]), parts[2])
    shell_pack_name = "shell-characterization"
    per_pack = pack_digests(packs, runtime.graph)
    drifted, expected_drift, added_packs = (), (), ()
    for name, count, pdigest in per_pack:
        if name not in pack_base:
            added_packs = added_packs + (name,)
        elif pack_base[name][1] != pdigest:
            if name in PORTED_PACKS:
                expected_drift = expected_drift + (name,)
            else:
                drifted = drifted + (name,)

    detail = (
        "rules compiled: %d\ncompiled-rule sha256: %s\n"
        "probe %s -> partial matches %d (cost %s)\n"
        "mappings emitted: %d; rules attributed: %d\n"
        "new characterization packs: %s\n"
        % (len(rules), digest, PROBE_GOAL, result["count"], result["cost"],
           len(mapping_lines), len(rule_lines), ", ".join(added_packs) or "none")
    )
    if not pack_base:
        detail += "NO PER-PACK BASELINE at %s" % PACK_DIGEST_PATH
    else:
        detail += "unported packs drifting: %s\n" % (", ".join(drifted) or "none")
        detail += "ported packs (drift expected): %s" % (
            ", ".join("%s -> %s" % (n, "drifted" if n in expected_drift else "no change")
                      for n in PORTED_PACKS) or "none")
    ok = (len(rules) == 167 and result["count"] == 0 and not drifted
          and pack_base and all(n in expected_drift for n in PORTED_PACKS)
          and added_packs == (shell_pack_name,))
    record("1. unported packs unchanged; ported pack drifted as intended", ok, detail)

    # ---- condition 2: {sym:} heads, no header ------------------------
    print("\n== condition 2: fixture with {sym:} heads, no surface header ==")
    runtime, packs = boot([LABEL_FIXTURE])
    result = probe(runtime, PROBE_GOAL, packs)
    mapping_lines, rule_lines = surface_records(packs)
    ok = result["count"] == 0 and not mapping_lines
    record("2. no header -> 0 candidates", ok,
           "probe %s -> partial matches %d (cost %s)\nsurface mappings emitted: %d"
           % (PROBE_GOAL, result["count"], result["cost"], len(mapping_lines)))

    # ---- condition 3: {sym:} heads plus surface header ---------------
    print("\n== condition 3: same fixture plus pack-local surface: header ==")
    runtime, packs = boot([MAPPED_FIXTURE])
    result = probe(runtime, PROBE_GOAL, packs)
    mapping_lines, rule_lines = surface_records(packs)
    taught = {"HUMAN_SUPPLIED_TRUSTED_THEOREM", "TaughtTag", "taught"}
    origin_ok = bool(result["origins"]) and not any(o in taught for o in result["origins"])
    audit_ok = any("PackSurfaceMapping" in line for line in mapping_lines)
    attribution_ok = any("rule=spike_divides_add" in line for line in rule_lines)
    ok = result["count"] == 1 and origin_ok and audit_ok and attribution_ok
    record("3. surface: header -> 1 candidate, pack-rule provenance, audit emitted", ok,
           "probe %s -> partial matches %d (cost %s)\nrule origins: %s\n"
           "provenance: a pack rule reached through the mapping, not a taught law"
           % (PROBE_GOAL, result["count"], result["cost"],
              ", ".join(result["origins"]) or "none"))

    # ---- condition 4: unrelated goal ---------------------------------
    print("\n== condition 4: unrelated goal, mapped fixture loaded ==")
    runtime, packs = boot([MAPPED_FIXTURE])
    result = probe(runtime, UNRELATED_GOAL, packs)
    ok = result["count"] == 0
    record("4. unrelated goal -> 0 candidates", ok,
           "probe %s -> partial matches %d (cost %s)"
           % (UNRELATED_GOAL, result["count"], result["cost"]))

    # ---- P1: the ported probe ----------------------------------------
    print("\n== P1: ported probe ==")
    runtime, packs = boot(PACK_PATHS)
    result = probe(runtime, PORT_PROBE, packs)
    _m, rule_lines = surface_records(packs)
    attributed = [rid for rid in result["rule_ids"]
                  if any(("rule=%s," % rid.split("/")[-1]) in line
                         for line in rule_lines)]
    ok = result["count"] >= 1 and bool(attributed)
    record("P1. ported probe -> >=1 candidate, attributed to the port", ok,
           "probe %s -> partial matches %d (cost %s)\nmatched rule ids: %s\n"
           "attributed to the surface mapping: %s\norigins: %s"
           % (PORT_PROBE, result["count"], result["cost"],
              ", ".join(result["rule_ids"]) or "none",
              ", ".join(attributed) or "none",
              ", ".join(result["origins"]) or "none"))

    # ---- P2: ablation -------------------------------------------------
    print("\n== P2: ablation, surface: stripped from the ported pack ==")
    runtime, packs = boot(ablated_paths())
    result = probe(runtime, PORT_PROBE, packs)
    ok = result["count"] == 0
    record("P2. ablation -> matches return to 0", ok,
           "probe %s -> partial matches %d (cost %s)\nrule ids: %s"
           % (PORT_PROBE, result["count"], result["cost"],
              ", ".join(result["rule_ids"]) or "none"))

    # ---- P3: unported packs untouched --------------------------------
    print("\n== P3: unported packs untouched ==")
    ok = bool(pack_base) and not drifted and added_packs == (shell_pack_name,)
    record("P3. no unported pack digest drift", ok,
           "drifted: %s\nported (expected): %s\nnew characterization pack: %s"
           % (", ".join(drifted) or "none", ", ".join(PORTED_PACKS) or "none",
              ", ".join(added_packs) or "none"))

    # ---- P4: no FLT vocabulary ---------------------------------------
    print("\n== P4: no FLT vocabulary in the ported packs ==")
    hits = []
    for path in PACK_PATHS:
        try:
            text = open(path, encoding="utf-8").read().lower()
        except OSError:
            continue
        if ("surface:" in text) and any(w in text for w in FLT_WORDS):
            hits.append((os.path.basename(path),
                         ", ".join(w for w in FLT_WORDS if w in text)))
    ok = not hits
    record("P4. no fermat/flt/wiles/frey in any ported pack", ok,
           "hits: %s" % ("; ".join("%s: %s" % h for h in hits) or "none"))

    # ---- S1: recorded shell-free baseline -----------------------------
    shell_b_goal = "(nosolutions positive-integers (unknowns x) (eq (plus x 1) x))"
    shell_c_goal = "(forall n (implies (greater n 1) (eq (plus a a) (plus a a))))"
    shell_d_goal = "(shellcontrol positive-integers (unknowns x) (eq (plus x 1) x))"
    shell_b_premise = "(NeedContradictionFromArbitrarySolution positive-integers (unknowns x) (eq (plus x 1) x))"
    shell_c_premise = "(NeedBinderSafeImplication n (greater n 1) (eq (plus a a) (plus a a)))"
    bare_eq_goal = "(eq (plus a a) (plus a a))"
    before_path = os.path.join(
        ROOT, "verification", "2026-09-12-d11-shell-phase2", "before.txt"
    )
    before_text = ""
    if os.path.exists(before_path):
        before_text = open(before_path, encoding="utf-8").read()
    before_b_start = before_text.find("[B] nosolutions shell")
    before_c_start = before_text.find("[C] forall/implies shell")
    before_d_start = before_text.find("[D] negative control")
    before_b_section = before_text[before_b_start:before_c_start]
    before_c_section = before_text[before_c_start:before_d_start]
    ok = (before_b_start >= 0 and before_c_start >= 0 and before_d_start >= 0
          and "partial matches: 0" in before_b_section
          and "partial matches: 0" in before_c_section)
    record("S1. recorded shell-free baseline has B/C at 0", ok,
           "artifact: %s\nB recorded at 0: %s\nC recorded at 0: %s"
           % (before_path,
              "yes" if "partial matches: 0" in before_b_section else "no",
              "yes" if "partial matches: 0" in before_c_section else "no"))

    # ---- S2 and S4: isolated nosolutions diagnostic -------------------
    print("\n== S2/S4: nosolutions shell diagnostic ==")
    runtime, packs = boot(PACK_PATHS)
    result_b = probe(runtime, shell_b_goal, packs)
    goal_b, goal_error_b = _research_parse(shell_b_goal)
    expected_b, parse_error_b = _research_parse(shell_b_premise)
    if goal_error_b is not None or parse_error_b is not None:
        raise RuntimeError("cannot parse B shell diagnostic terms")
    derivation_b = runtime.prove(M.truth_value, goal_b)
    diagnostic_b = runtime.last_foreground_diagnostic
    b_no_requests = M.IdentityCompare(runtime.graph.dependency_requests, M.EmptyList)()
    b_no_interventions = M.IdentityCompare(runtime.graph.intervention_episodes, M.EmptyList)()
    diagnostic_b_count = 0
    if M.IdentityCompare(diagnostic_b, M.EmptyList)() is M.false_value:
        diagnostic_b_count = 1
    record("S2. B has one diagnostic candidate and 0 proof candidates",
           diagnostic_b_count == 1 and result_b["count"] == 0,
           "diagnostic candidates: %d\nproof candidates: %d"
           % (diagnostic_b_count, result_b["count"]))
    record("S4. B diagnostic is the exact contradiction capability premise",
           M.Compare(diagnostic_b, expected_b)() is M.truth_value,
           "diagnostic: %s\nexpected: %s"
           % (_term_text(diagnostic_b, runtime.graph), shell_b_premise))

    # ---- S3 and S5: isolated forall/implies diagnostic ----------------
    print("\n== S3/S5: forall/implies shell diagnostic ==")
    runtime, packs = boot(PACK_PATHS)
    result_c = probe(runtime, shell_c_goal, packs)
    goal_c, goal_error_c = _research_parse(shell_c_goal)
    expected_c, parse_error_c = _research_parse(shell_c_premise)
    if goal_error_c is not None or parse_error_c is not None:
        raise RuntimeError("cannot parse C shell diagnostic terms")
    derivation_c = runtime.prove(M.truth_value, goal_c)
    diagnostic_c = runtime.last_foreground_diagnostic
    c_no_requests = M.IdentityCompare(runtime.graph.dependency_requests, M.EmptyList)()
    c_no_interventions = M.IdentityCompare(runtime.graph.intervention_episodes, M.EmptyList)()
    diagnostic_c_count = 0
    if M.IdentityCompare(diagnostic_c, M.EmptyList)() is M.false_value:
        diagnostic_c_count = 1
    record("S3. C has one diagnostic candidate and 0 proof candidates",
           diagnostic_c_count == 1 and result_c["count"] == 0,
           "diagnostic candidates: %d\nproof candidates: %d"
           % (diagnostic_c_count, result_c["count"]))
    record("S5. C diagnostic is the exact binder-safe capability premise",
           M.Compare(diagnostic_c, expected_c)() is M.truth_value,
           "diagnostic: %s\nexpected: %s"
           % (_term_text(diagnostic_c, runtime.graph), shell_c_premise))

    # ---- S6: diagnostics are not derivations or theorem requests -------
    record("S6. both shell goals remain unclosed with no discharge or intervention credit",
           (not result_b["closed"] and not result_c["closed"]
            and M.IdentityCompare(derivation_b, M.EmptyList)() is M.truth_value
            and M.IdentityCompare(derivation_c, M.EmptyList)() is M.truth_value
            and b_no_requests is M.truth_value and c_no_requests is M.truth_value
            and b_no_interventions is M.truth_value and c_no_interventions is M.truth_value),
           "B/C proof closed: %s/%s\nforeground results empty: %s/%s\n"
           "dependency requests empty: %s/%s\nintervention episodes empty: %s/%s"
           % ("yes" if result_b["closed"] else "no",
              "yes" if result_c["closed"] else "no",
              M.IdentityCompare(derivation_b, M.EmptyList)() is M.truth_value,
              M.IdentityCompare(derivation_c, M.EmptyList)() is M.truth_value,
              b_no_requests is M.truth_value, c_no_requests is M.truth_value,
              b_no_interventions is M.truth_value, c_no_interventions is M.truth_value))

    # ---- S7: capability premises remain unavailable -------------------
    print("\n== S7: capability premises ==")
    runtime, packs = boot(PACK_PATHS)
    capability_b = probe(runtime, shell_b_premise, packs)
    capability_c = probe(runtime, shell_c_premise, packs)
    ok = capability_b["count"] == 0 and capability_c["count"] == 0
    record("S7. capability-premise goals have 0 proof candidates", ok,
           "B capability proof candidates: %d\nC capability proof candidates: %d"
           % (capability_b["count"], capability_c["count"]))

    # ---- S8: a different outer head has neither candidate kind ---------
    print("\n== S8: negative control ==")
    runtime, packs = boot(PACK_PATHS)
    negative_control = probe(runtime, shell_d_goal, packs)
    negative_goal, negative_error = _research_parse(shell_d_goal)
    if negative_error is not None:
        raise RuntimeError("cannot parse negative control")
    runtime.prove(M.truth_value, negative_goal)
    record("S8. different-head control has 0 diagnostic and proof candidates",
           (negative_control["count"] == 0
            and M.IdentityCompare(runtime.last_foreground_diagnostic, M.EmptyList)() is M.truth_value),
           "proof candidates: %d\ndiagnostic candidates: %d"
           % (negative_control["count"],
              0 if M.IdentityCompare(runtime.last_foreground_diagnostic, M.EmptyList)() is M.truth_value else 1))

    # ---- S9: removing this pack's surface header removes diagnostics ---
    print("\n== S9: shell surface ablation ==")
    runtime, packs = boot(ablated_paths((shell_pack_name,)))
    ablation_b = probe(runtime, shell_b_goal, packs)
    ablation_c = probe(runtime, shell_c_goal, packs)
    runtime.prove(M.truth_value, goal_b)
    ablation_diagnostic_b = runtime.last_foreground_diagnostic
    runtime.prove(M.truth_value, goal_c)
    ablation_diagnostic_c = runtime.last_foreground_diagnostic
    ok = (ablation_b["count"] == 0 and ablation_c["count"] == 0
          and M.IdentityCompare(ablation_diagnostic_b, M.EmptyList)() is M.truth_value
          and M.IdentityCompare(ablation_diagnostic_c, M.EmptyList)() is M.truth_value)
    record("S9. shell surface ablation removes B/C diagnostics", ok,
           "B proof/diagnostic candidates: %d/%d\nC proof/diagnostic candidates: %d/%d"
           % (ablation_b["count"],
              0 if M.IdentityCompare(ablation_diagnostic_b, M.EmptyList)() is M.truth_value else 1,
              ablation_c["count"],
              0 if M.IdentityCompare(ablation_diagnostic_c, M.EmptyList)() is M.truth_value else 1))

    # ---- S10: prior equation reachability is unchanged ----------------
    print("\n== S10: bare equation control ==")
    runtime, packs = boot(PACK_PATHS)
    bare_eq = probe(runtime, bare_eq_goal, packs)
    record("S10. bare eq proof partial-match count remains 1", bare_eq["count"] == 1,
           "probe %s -> proof candidates %d (cost %s)"
           % (bare_eq_goal, bare_eq["count"], bare_eq["cost"]))

    # ---- I1: diagnostic records never enter the fireable rule store ----
    shell_pack = ()
    for loaded_pack in packs:
        if loaded_pack.name == shell_pack_name:
            shell_pack = loaded_pack
    record("I1. shell pack stores diagnostics outside proof rules",
           len(shell_pack.rule_map) == 0 and len(shell_pack.diagnostic_rules) == 2,
           "proof rules: %d\ndiagnostic records: %d"
           % (len(shell_pack.rule_map), len(shell_pack.diagnostic_rules)))

    # ---- I2: direct capability facts cannot close shell goals ----------
    print("\n== I2: direct capability-fact adversary ==")
    runtime, packs = boot(PACK_PATHS)
    direct_b = probe(runtime, shell_b_goal, packs, M.Pair(expected_b, M.EmptyList))
    direct_c = probe(runtime, shell_c_goal, packs, M.Pair(expected_c, M.EmptyList))
    record("I2. supplied capability facts cannot close B/C",
           not direct_b["closed"] and not direct_c["closed"],
           "B closed: %s\nC closed: %s"
           % ("yes" if direct_b["closed"] else "no",
              "yes" if direct_c["closed"] else "no"))

    # ---- I3: empty-premise taught capability cannot close shell goals --
    print("\n== I3: taught capability adversary ==")
    runtime, packs = boot(PACK_PATHS)
    taught_b_formal = Rmod.FormalRule(M.EmptyList, expected_b)()
    taught_b = Rmod.teach_trusted_theorem(runtime.graph, taught_b_formal)
    taught_b_result = probe(
        runtime, shell_b_goal, packs, M.EmptyList,
        M.Pair(taught_b, rules_of(runtime.graph))
    )
    taught_c_formal = Rmod.FormalRule(M.EmptyList, expected_c)()
    taught_c = Rmod.teach_trusted_theorem(runtime.graph, taught_c_formal)
    taught_c_result = probe(
        runtime, shell_c_goal, packs, M.EmptyList,
        M.Pair(taught_c, rules_of(runtime.graph))
    )
    record("I3. empty-premise taught capabilities cannot close B/C",
           not taught_b_result["closed"] and not taught_c_result["closed"],
           "B closed: %s\nC closed: %s"
           % ("yes" if taught_b_result["closed"] else "no",
              "yes" if taught_c_result["closed"] else "no"))

    # ---- I4: restored facts and replayed teachings remain non-proving --
    print("\n== I4: restored-state adversary ==")
    directory = tempfile.mkdtemp(prefix="d11-shell-isolation-")
    snapshot_path = os.path.join(directory, "state.json")
    runtime, packs = boot(PACK_PATHS)
    Rmod.assume_axiom(runtime.graph, expected_b)
    Rmod.assume_axiom(runtime.graph, expected_c)
    runtime.save_snapshot(snapshot_path, _runtime_namespace())
    restored = RT.boot_from_snapshot(
        snapshot_path, _runtime_namespace(), save_upgraded_snapshot=M.false_value
    )
    restored_facts = Rmod.axiom_facts(restored.graph)
    restored_b = probe(restored, shell_b_goal, (), restored_facts)
    restored_c = probe(restored, shell_c_goal, (), restored_facts)
    os.remove(snapshot_path)
    os.rmdir(directory)

    directory = tempfile.mkdtemp(prefix="d11-shell-replay-")
    snapshot_path = os.path.join(directory, "state.json")
    runtime, packs = boot(PACK_PATHS)
    Rmod.teach_trusted_theorem(runtime.graph, Rmod.FormalRule(M.EmptyList, expected_b)())
    Rmod.teach_trusted_theorem(runtime.graph, Rmod.FormalRule(M.EmptyList, expected_c)())
    runtime.save_snapshot(snapshot_path, _runtime_namespace())
    restored = RT.boot_from_snapshot(
        snapshot_path, _runtime_namespace(), save_upgraded_snapshot=M.false_value
    )
    replayed = Rmod.rebuild_taught_rules(restored.graph)
    replay_rules = rules_of(restored.graph)
    while M.IdentityCompare(replayed, M.EmptyList)() is M.false_value:
        replay_rules = M.Pair(M.Head(M.Head(replayed)())(), replay_rules)
        replayed = M.Tail(replayed)()
    replayed_b = probe(restored, shell_b_goal, (), M.EmptyList, replay_rules)
    replayed_c = probe(restored, shell_c_goal, (), M.EmptyList, replay_rules)
    os.remove(snapshot_path)
    os.rmdir(directory)
    record("I4. restored facts and replayed teachings cannot close B/C",
           (not restored_b["closed"] and not restored_c["closed"]
            and not replayed_b["closed"] and not replayed_c["closed"]),
           "restored fact B/C closed: %s/%s\nreplayed teaching B/C closed: %s/%s"
           % ("yes" if restored_b["closed"] else "no",
              "yes" if restored_c["closed"] else "no",
              "yes" if replayed_b["closed"] else "no",
              "yes" if replayed_c["closed"] else "no"))

    # ---- I5: live ingress preserves the foreground object -------------
    print("\n== I5: live ingress diagnostic identity ==")
    text = "prove that for all n > 1 n + n = n + n"
    runtime, packs = boot(PACK_PATHS)
    request = Ingress.LiveProofRequest(Ingress.ProofTokenStream(text)())
    direct = Ingress.MathematicalSentence(request.claim)
    submission = Ingress.SubmitForegroundGoal(runtime, request)
    returned = submission()
    received = runtime.last_foreground_goal
    diagnostic = runtime.last_foreground_diagnostic
    record("I5. live toy preserves parsed/submitted/received goal and returns only a diagnostic",
           (request.recognized is M.truth_value
            and request.goal is not M.EmptyList
            and M.Compare(direct.goal, request.goal)() is M.truth_value
            and M.Compare(submission.goal, request.goal)() is M.truth_value
            and M.Compare(received, request.goal)() is M.truth_value
            and M.IdentityCompare(returned, M.EmptyList)() is M.truth_value
            and M.IdentityCompare(diagnostic, M.EmptyList)() is M.false_value),
           "parsed goal: %s\nforeground submission: %s\nworker-received goal: %s\nreturned diagnostic: %s\nreturned derivation: empty"
           % (Ingress.ProofGoalText(request.goal)(),
              Ingress.ProofGoalText(submission.goal)(),
              Ingress.ProofGoalText(received)(),
              _term_text(diagnostic, runtime.graph)))

    # ---- condition 5: char form, diagnostic only ---------------------
    print("\n== condition 5: char-form fixture (DIAGNOSTIC, NOT A GATE) ==")
    runtime, packs = boot([CHAR_FIXTURE])
    result = probe(runtime, PROBE_GOAL, packs)
    print("       probe %s -> partial matches %d (cost %s)"
          % (PROBE_GOAL, result["count"], result["cost"]))
    print("       This is the char shorthand. It worked before the D11 fix and")
    print("       proves nothing about it. It is never cited as D11 fixed.")

    failed = [name for name, ok, _ in results if not ok]
    print("\n%d/%d gated conditions passed."
          % (len(results) - len(failed), len(results)))
    if failed:
        for name in failed:
            print("  FAILED: %s" % name)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
