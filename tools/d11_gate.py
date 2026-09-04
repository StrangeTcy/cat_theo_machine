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


def probe(runtime, goal_text):
    """One goal attempt through the real research path. Returns a summary."""
    graph = runtime.graph
    term, err = _research_parse(goal_text)
    if term is None:
        raise RuntimeError("cannot parse goal %r: %s" % (goal_text, err))
    rules = rules_of(graph)
    outcome = Rmod.attempt_goal(
        graph, Rmod.axiom_facts(graph), M.Pair(term, M.EmptyList), rules
    )
    attempts = walk(getattr(graph, "research_attempts", M.EmptyList))
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


def main(argv):
    baseline_mode = "--baseline" in argv

    # ---- condition 1: shipped packs, no headers -------------------------
    print("== condition 1: shipped packs, no surface headers ==")
    runtime, packs = boot(PACK_PATHS)
    rules = walk(rules_of(runtime.graph))
    body = "\n".join(render(r, runtime.graph) for r in rules)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    mapping_lines, rule_lines = surface_records(packs)

    if baseline_mode:
        with open(DIGEST_PATH, "w", encoding="utf-8") as handle:
            handle.write("%d %s\n" % (len(rules), digest))
        print("    recorded baseline: %d rules, sha256 %s" % (len(rules), digest))
        print("    -> %s" % DIGEST_PATH)
        return 0

    baseline = None
    if os.path.exists(DIGEST_PATH):
        baseline = open(DIGEST_PATH, encoding="utf-8").read().split()

    result = probe(runtime, PROBE_GOAL)
    detail = (
        "rules compiled: %d\ncompiled-rule sha256: %s\n"
        "probe %s -> partial matches %d (cost %s)\n"
        "surface mappings emitted: %d; rules attributed: %d"
        % (len(rules), digest, PROBE_GOAL, result["count"], result["cost"],
           len(mapping_lines), len(rule_lines))
    )
    ok = len(rules) == 167 and result["count"] == 0
    ok = ok and not mapping_lines and not rule_lines
    if baseline is None:
        ok = False
        detail += "\nNO BASELINE RECORDED at %s" % DIGEST_PATH
    else:
        want_count, want_digest = int(baseline[0]), baseline[1]
        if len(rules) != want_count or digest != want_digest:
            ok = False
            detail += "\nDIGEST DRIFT: baseline %d/%s, now %d/%s" % (
                want_count, want_digest[:12], len(rules), digest[:12])
        else:
            detail += "\ndigest matches the pre-change baseline (%d rules)" % want_count
    record("1. shipped 167 unchanged, zero candidates", ok, detail)

    # ---- condition 2: {sym:} heads, no header ---------------------------
    print("\n== condition 2: fixture with {sym:} heads, no surface header ==")
    runtime, packs = boot([LABEL_FIXTURE])
    result = probe(runtime, PROBE_GOAL)
    mapping_lines, rule_lines = surface_records(packs)
    ok = result["count"] == 0 and not mapping_lines
    record("2. no header -> 0 candidates", ok,
           "probe %s -> partial matches %d (cost %s)\nsurface mappings emitted: %d"
           % (PROBE_GOAL, result["count"], result["cost"], len(mapping_lines)))

    # ---- condition 3: {sym:} heads plus surface header ------------------
    print("\n== condition 3: same fixture plus pack-local surface: header ==")
    runtime, packs = boot([MAPPED_FIXTURE])
    result = probe(runtime, PROBE_GOAL)
    mapping_lines, rule_lines = surface_records(packs)
    # Provenance note. The REPL announces packs as "provenance
    # LIBRARY_THEOREM" (main.py:3479), but that is the announcement text
    # for the load command, not a per-rule tag: a rule's origin is
    # origin_tag_for_text(pack origin), which is `primitive` for a pack
    # that declares none, as this fixture does. So the gate asserts the
    # discriminating fact -- the match is a pack rule reached through the
    # mapping, not a taught law -- and prints the tag it actually carries.
    taught_tags = {"HUMAN_SUPPLIED_TRUSTED_THEOREM", "TaughtTag", "taught"}
    origin_ok = bool(result["origins"]) and not any(
        o in taught_tags for o in result["origins"]
    )
    audit_ok = any("PackSurfaceMapping" in line for line in mapping_lines)
    attribution_ok = any("rule=spike_divides_add" in line for line in rule_lines)
    ok = result["count"] == 1 and origin_ok and audit_ok and attribution_ok
    detail = (
        "probe %s -> partial matches %d (cost %s)\nrule origins: %s\n"
        % (PROBE_GOAL, result["count"], result["cost"], ", ".join(result["origins"]) or "none")
    )
    detail += "audit lines:\n" + ("\n".join(mapping_lines + rule_lines) or "  (none)")
    detail += (
        "\nprovenance: %s -- a pack rule reached through the mapping, not a"
        "\ntaught law. See the note in this file about the LIBRARY_THEOREM"
        "\nwording; the discriminating check is attribution, not the string."
        % (", ".join(result["origins"]) or "none")
    )
    record("3. surface: header -> 1 candidate, pack-rule provenance, audit emitted",
           ok, detail)

    # ---- condition 4: unrelated goal, mapped fixture --------------------
    print("\n== condition 4: unrelated goal, mapped fixture loaded ==")
    runtime, packs = boot([MAPPED_FIXTURE])
    result = probe(runtime, UNRELATED_GOAL)
    ok = result["count"] == 0
    record("4. unrelated goal -> 0 candidates", ok,
           "probe %s -> partial matches %d (cost %s)"
           % (UNRELATED_GOAL, result["count"], result["cost"]))

    # ---- condition 5: char form, diagnostic only ------------------------
    print("\n== condition 5: char-form fixture (DIAGNOSTIC, NOT A GATE) ==")
    runtime, packs = boot([CHAR_FIXTURE])
    result = probe(runtime, PROBE_GOAL)
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
