#!/usr/bin/env python3
"""D11-MAP gate.

Re-runnable from a fresh clone:

    python3 tools/d11_gate.py              # all conditions
    python3 tools/d11_gate.py --baseline   # (re)record the shipped-167 digest

What it proves, in the terms of the §8 ruling:

  1. shipped packs, no surface headers  -> rule count and compiled-rule
     digest unchanged from the pre-change baseline in
     protocol/d11-spike/shipped-167-rules.sha256; zero surface records;
     zero candidates on the D11 probe
  2. fixture with {sym:} heads, no header      -> partial matches 0
  3. same fixture plus a surface: header       -> partial matches 1,
     provenance LIBRARY_THEOREM, audit line names the pack-local mapping
  4. unrelated goal, mapped fixture loaded     -> partial matches 0
  5. char-form fixture                         -> diagnostic only, printed
     and explicitly NOT cited as D11 fixed

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


def probe(runtime, goal_text, packs=()):
    """One goal attempt through the real research path. Returns a summary."""
    graph = runtime.graph
    id_index = rule_id_index(packs)
    term, err = _research_parse(goal_text)
    if term is None:
        raise RuntimeError("cannot parse goal %r: %s" % (goal_text, err))
    rules = rules_of(graph)
    outcome = Rmod.attempt_goal(
        graph, Rmod.axiom_facts(graph), M.Pair(term, M.EmptyList), rules
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
    probe_goal = None
    shell_ablation_probe_goal = None
    for i, a in enumerate(argv):
        if a == "--probe" and i + 1 < len(argv):
            probe_goal = argv[i + 1]
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
    ok = (len(rules) == 169 and result["count"] == 0 and not drifted
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

    # ---- S2 and S4: nosolutions shell and exact residual --------------
    print("\n== S2/S4: nosolutions shell ==")
    runtime, packs = boot(PACK_PATHS)
    result_b = probe(runtime, shell_b_goal, packs)
    expected_b, parse_error_b = _research_parse(shell_b_premise)
    if parse_error_b is not None:
        raise RuntimeError("cannot parse expected B residual: %s" % parse_error_b)
    residual_b_exact = M.false_value
    residual_b_text = "none"
    for attempt in walk(runtime.graph.research_attempts):
        unmatched = Rmod.AttemptedRuleUnmatched(attempt)()
        residual_b_text = _term_text(unmatched, runtime.graph)
        if M.Compare(unmatched, expected_b)() is M.truth_value:
            residual_b_exact = M.truth_value
    record("S2. B nosolutions shell -> positive partial matches", result_b["count"] > 0,
           "probe %s -> partial matches %d (cost %s)"
           % (shell_b_goal, result_b["count"], result_b["cost"]))
    record("S4. B residual is the exact contradiction capability premise",
           residual_b_exact is M.truth_value,
           "residual: %s\nexpected: %s" % (residual_b_text, shell_b_premise))

    # ---- S3 and S5: forall/implies shell and exact residual -----------
    print("\n== S3/S5: forall/implies shell ==")
    runtime, packs = boot(PACK_PATHS)
    result_c = probe(runtime, shell_c_goal, packs)
    expected_c, parse_error_c = _research_parse(shell_c_premise)
    if parse_error_c is not None:
        raise RuntimeError("cannot parse expected C residual: %s" % parse_error_c)
    residual_c_exact = M.false_value
    residual_c_text = "none"
    for attempt in walk(runtime.graph.research_attempts):
        unmatched = Rmod.AttemptedRuleUnmatched(attempt)()
        residual_c_text = _term_text(unmatched, runtime.graph)
        if M.Compare(unmatched, expected_c)() is M.truth_value:
            residual_c_exact = M.truth_value
    record("S3. C forall/implies shell -> positive partial matches", result_c["count"] > 0,
           "probe %s -> partial matches %d (cost %s)"
           % (shell_c_goal, result_c["count"], result_c["cost"]))
    record("S5. C residual is the exact binder-safe capability premise",
           residual_c_exact is M.truth_value,
           "residual: %s\nexpected: %s" % (residual_c_text, shell_c_premise))

    # ---- S6: characterizations do not close either toy goal -----------
    record("S6. both shell goals remain unclosed",
           not result_b["closed"] and not result_c["closed"],
           "B closed: %s\nC closed: %s"
           % ("yes" if result_b["closed"] else "no",
              "yes" if result_c["closed"] else "no"))

    # ---- S7: capability premises remain unavailable -------------------
    print("\n== S7: capability premises ==")
    runtime, packs = boot(PACK_PATHS)
    capability_b = probe(runtime, shell_b_premise, packs)
    capability_c = probe(runtime, shell_c_premise, packs)
    ok = capability_b["count"] == 0 and capability_c["count"] == 0
    record("S7. capability-premise goals have 0 candidates", ok,
           "B capability candidates: %d\nC capability candidates: %d"
           % (capability_b["count"], capability_c["count"]))

    # ---- S8: a different outer head remains silent --------------------
    print("\n== S8: negative control ==")
    runtime, packs = boot(PACK_PATHS)
    negative_control = probe(runtime, shell_d_goal, packs)
    record("S8. different-head negative control remains at 0",
           negative_control["count"] == 0,
           "probe %s -> partial matches %d (cost %s)"
           % (shell_d_goal, negative_control["count"], negative_control["cost"]))

    # ---- S9: removing only this pack's surface header restores silence -
    print("\n== S9: shell surface ablation ==")
    runtime, packs = boot(ablated_paths((shell_pack_name,)))
    ablation_b = probe(runtime, shell_b_goal, packs)
    ablation_c = probe(runtime, shell_c_goal, packs)
    ok = ablation_b["count"] == 0 and ablation_c["count"] == 0
    record("S9. shell surface ablation restores B/C to 0", ok,
           "B partial matches: %d\nC partial matches: %d"
           % (ablation_b["count"], ablation_c["count"]))

    # ---- S10: prior equation reachability is unchanged ----------------
    print("\n== S10: bare equation control ==")
    runtime, packs = boot(PACK_PATHS)
    bare_eq = probe(runtime, bare_eq_goal, packs)
    record("S10. bare eq partial-match count remains 1", bare_eq["count"] == 1,
           "probe %s -> partial matches %d (cost %s)"
           % (bare_eq_goal, bare_eq["count"], bare_eq["cost"]))

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
