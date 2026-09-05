"""D3 probe: how many restored Nats are the Nat the machine builds for their value.

Quarantined tooling, like the other repro_* scripts: it measures, it is not
part of the suite, and it is kept because the measurement is expensive to
rediscover.

It saves a snapshot of the booted graph, boots it back, then walks the
restored payload -- all_rules, rule_order, derivations, derivation_schemata
-- and for every atom that reads as a Nat asks the restored machine for the
Nat of that value (`NatFromRep`, which is the interning entry point) and
compares identity. Mismatches are the D3 count.

    python3 tools/repro_d3_interning.py            measure the tree as it is
    python3 tools/repro_d3_interning.py --no-fix   disable the interning pass
    python3 tools/repro_d3_interning.py --debug    boot with codec debug on

It visits ~17k terms on a packs-booted graph and reports

    visited 16696 terms, nats checked 5, mismatched 5

which is the number the D3 fix has to take to zero.
"""
import sys, os, time, shutil, tempfile
sys.path.insert(0, "/home/user")

STATS = {}
G2 = None

ROOTS = ("all_rules", "rule_order", "derivations", "derivation_schemata",
         "search_memo", "dependency_graph", "dependency_requests",
         "intervention_episodes", "last_proof", "generator_metrics")

def census(g2, limit=200000):
    """value text -> how many distinct restored atoms carry it."""
    import cat_theo_machine.machine as M
    empty = M.EmptyList
    registry = M.FromContextGetConstructors(g2)()
    seen = set()
    stack = [getattr(g2, n) for n in ("all_rules", "rule_order", "derivations", "derivation_schemata")]
    per_value = {}
    while stack and len(seen) < limit:
        term = stack.pop()
        if term is None or id(term) in seen:
            continue
        seen.add(id(term))
        if M.IsPair(term)() is M.truth_value:
            stack.append(M.Head(term)()); stack.append(M.Tail(term)()); continue
        v = getattr(term, "value", None)
        if v is not None and M.IsPair(v)() is M.truth_value:
            stack.append(v)
        for f in ("inputs", "results"):
            x = getattr(term, f, None)
            if x is not None:
                stack.append(x)
        if v is None:
            continue
        text = str(v)
        if not text.isdigit():
            try: text = str(v())
            except Exception: continue
        if not text.isdigit() or len(text) > 6:
            continue
        ctor = M.GetConstructor(term, registry)()
        if M.IdentityCompare(ctor, empty)() is M.truth_value:
            continue
        if M.IdentityCompare(M.Head(ctor)(), M.SuccLabel)() is M.false_value:
            continue
        per_value.setdefault(text, set()).add(id(term))
    return per_value


def count(g2, limit_checked=16, limit_seen=200000):
    global G2
    G2 = g2
    import cat_theo_machine.machine as M
    empty = M.EmptyList
    registry = M.FromContextGetConstructors(g2)()
    seen = set()
    stack = []
    for name in ROOTS:
        root = getattr(g2, name, None)
        if root is not None:
            stack.append(root)
    checked = 0
    bad = 0
    while stack and len(seen) < limit_seen:
        term = stack.pop()
        if term is None or id(term) in seen:
            continue
        seen.add(id(term))
        if M.IsPair(term)() is M.truth_value:
            stack.append(M.Head(term)())
            stack.append(M.Tail(term)())
            continue
        value = getattr(term, "value", None)
        if value is not None and M.IsPair(value)() is M.truth_value:
            stack.append(value)
        inputs = getattr(term, "inputs", None)
        if inputs is not None:
            stack.append(inputs)
        results = getattr(term, "results", None)
        if results is not None:
            stack.append(results)
        if value is None:
            continue
        text = str(value)
        if not text.isdigit():
            try:
                text = str(value())
            except Exception:
                continue
        if not text.isdigit() or len(text) > 6:
            continue
        STATS["digits"] = STATS.get("digits", 0) + 1
        constructor = M.GetConstructor(term, registry)()
        if M.IdentityCompare(constructor, empty)() is M.truth_value:
            STATS["no_ctor"] = STATS.get("no_ctor", 0) + 1
            continue
        STATS["ctor"] = STATS.get("ctor", 0) + 1
        if M.IdentityCompare(M.Head(constructor)(), M.SuccLabel)() is M.false_value:
            continue
        pair = M.NatFromRep(M.GMPRep(text), registry)()
        interned = M.Head(pair)()
        registry = M.Head(M.Tail(pair)())()
        checked += 1
        if M.IdentityCompare(term, interned)() is M.false_value:
            bad += 1
            if bad <= 6:
                from cat_theo_machine import trees as Tmod
                w = Tmod.TreeEntries(g2.nat_value_index)()
                texts = []
                nn = 0
                while M.IdentityCompare(w, M.EmptyList)() is M.false_value and nn < 40:
                    e = M.Head(w)()
                    f = M.Head(M.Tail(e)())()
                    w = M.Tail(w)()
                    nn += 1
                    try:
                        texts.append(str(getattr(f, "value", None)()))
                    except Exception:
                        texts.append("?")
                print("   mismatch at value %s" % text, flush=True)
    return checked, bad, len(seen)

def main():
    import cat_theo_machine.machine as M
    from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
    from cat_theo_machine.runtime import boot_from_packs, boot_from_snapshot
    from cat_theo_machine.persistence import SnapshotCodec

    disable = "--no-fix" in sys.argv
    from cat_theo_machine.persistence import SnapshotCodec
    if disable:
        SnapshotCodec._canonicalize_restored_nats = lambda self, state, graph, debug=False: 0

    rt, _ = boot_from_packs(PACK_PATHS, _runtime_namespace())
    g = rt.graph
    tmp = tempfile.mkdtemp(); path = os.path.join(tmp, "s.json")
    codec = SnapshotCodec(_runtime_namespace())
    codec.save(g, path, progress=M.false_value)
    t0 = time.time()
    dbg = M.truth_value if "--debug" in sys.argv else M.false_value
    rt2 = boot_from_snapshot(path, _runtime_namespace(), debug=dbg)
    g2 = rt2.graph
    print("booted snapshot in %.1fs" % (time.time() - t0), flush=True)
    shutil.rmtree(tmp, ignore_errors=True)
    t0 = time.time()
    checked, bad, seen = count(g2)
    state_text = "absent" if not hasattr(SnapshotCodec, "_canonicalize_restored_nats") else (
        "disabled" if "--no-fix" in sys.argv else "active")
    per_value = census(g2)
    dupes = {k: len(v) for k, v in sorted(per_value.items()) if len(v) > 1}
    print("values in payload: %d   values with more than one atom: %r" % (len(per_value), dupes), flush=True)
    print("interning pass %s: visited %d terms, nats checked %d, mismatched %d  (%.1fs)" % (
        state_text, seen, checked, bad, time.time() - t0), flush=True)

if __name__ == "__main__":
    main()
