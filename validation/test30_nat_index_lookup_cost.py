# ============================================================
# TEST 30: W18 — kernel: `NatValueIndex` lookup cost
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test30_nat_index_lookup_cost.py
#
# Suite slot 30 is pre-allocated to W18 (`delegation/W18-nat-index-lookup-cost.md`).
#
# What W18 changed, in one breath: `IndexAtomKey` used to collapse every
# indexed atom to EmptyList, so all keys of equal cons shape -- for
# `NatValueKey`, all values with the same digit count -- shared one Patricia
# leaf bucket, and `TreeLookup` compounded that with a full linear scan of
# every interned entry whenever the Patricia walk missed (which for
# `NatFromRep` is every new value). Interning a value therefore cost time
# proportional to everything ever interned: measured ~0.2 s per fresh value
# on a fresh runtime and ~1.5 s at three hundred entries. Now:
#
#   1. `IndexAtomKey` carries the atom. This is completeness-preserving:
#      atoms are `TreeTermEqual` only when they are the same object, so
#      equal exact keys still produce equal index keys and land in the same
#      bucket, while distinct values diverge in the path at their first
#      differing digit. Buckets shrink to same-value duplicates, of which
#      upsert leaves at most one.
#   2. On a Patricia root of the current layout, a Patricia miss IS absence;
#      the linear fallback is gone from that path. The O(entries)
#      `_is_bucketed_root` walk is replaced by an O(1) root-label check
#      (Patricia roots are bucketed by construction).
#   3. Trees stored by earlier versions keep their old collapsed layout.
#      A layout probe reads the first leaf's stored path and routes lookups
#      through the legacy index key plus the linear fallback (correct, and
#      only taken until the first insert); the first insert rebuilds such a
#      tree entry by entry under the current index keys, exactly like the
#      legacy-BST migration that already existed. Snapshots therefore stay
#      readable and writable across the change.
#
# What is measured here: the brief's schedule -- intern 50 new values, then
# 300 more, then 50 more -- must have a FLAT per-call cost (third batch
# within 1.5x of the first; before the fix the same schedule degraded about
# 24x). Wall-clock timing is harness business (§5.2 sanctions Python
# measurement in harnesses); every value that goes in must round-trip back
# through `NatRepOf`, hits must return the same node, and distinct values
# must never alias.
#
# Machine purity: trees.py gained no forbidden constructs (checked in [6]);
# the fix uses only Pair/Head/Tail/IdentityCompare/IsPair and label atoms.

import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PARENT = os.path.dirname(REPO)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

PACKAGE = os.path.basename(REPO)

M = importlib.import_module(PACKAGE + ".machine")
T = importlib.import_module(PACKAGE + ".trees")
peano = importlib.import_module(PACKAGE + ".math.peano")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")

T0 = time.time()

print("=== TEST 30: W18 NatValueIndex lookup cost ===")
print()

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    line = "    PASS  " if ok else "    FAIL  "
    line = line + name + ("  -- " + detail if detail else "")
    print(line)


# ---------------------------------------------------------------------------
# [1] the brief's schedule on a fresh runtime
# ---------------------------------------------------------------------------

print("[1] Flat cost across interned-entry growth")

runtime = runtime_mod.make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()


def nat(n):
    """Host int -> machine nat, threading the suite's registry."""
    global registry
    res = M.NatFromRep(M.GMPRep(str(n)), registry)()
    registry = M.Head(M.Tail(res)())()
    return M.Head(res)()


def rep_of(n):
    rep = peano.NatRepOf(nat(n), registry)()
    if rep is M.EmptyList:
        return None
    return int(str(rep()))


BATCHES = []


def intern_range(lo, hi, label):
    start = time.perf_counter()
    for n in range(lo, hi):
        nat(n)
    elapsed = time.perf_counter() - start
    count = hi - lo
    per_call = elapsed / count
    BATCHES.append((label, elapsed, per_call, count))
    print("    %-30s %8.3f s  (%.4f s/call)" % (label, elapsed, per_call))
    return per_call


NODES = {}


def intern_range(lo, hi, label):
    start = time.perf_counter()
    for n in range(lo, hi):
        NODES[n] = nat(n)
    elapsed = time.perf_counter() - start
    count = hi - lo
    per_call = elapsed / count
    BATCHES.append((label, elapsed, per_call, count))
    print("    %-30s %8.3f s  (%.4f s/call)" % (label, elapsed, per_call))
    return per_call


first = intern_range(1000, 1050, "50 new values ~1000")
intern_range(2000, 2300, "300 more values")
third = intern_range(2500, 2550, "50 more values at ~350")

check("third batch within 1.5x of first batch's per-call cost",
      third <= first * 1.5,
      "first %.4f s/call, third %.4f s/call (ratio %.2f)" % (first, third, third / first))
check("no batch degrades past 2x the first (monotonicity guard)",
      all(b[2] <= first * 2.0 for b in BATCHES),
      "ratios: " + ", ".join("%.2f" % (b[2] / first) for b in BATCHES))

print()

# ---------------------------------------------------------------------------
# [2] round-trip, identity, aliasing
# ---------------------------------------------------------------------------

print("[2] Semantics: round-trip, hit identity, no aliasing")

interned = list(range(1000, 1050)) + list(range(2000, 2300)) + list(range(2500, 2550))
bad_rt = [n for n in interned if rep_of(n) != n]
check("every interned value round-trips through NatRepOf", not bad_rt,
      "%d mismatches: %s" % (len(bad_rt), bad_rt[:5]))

print()

# ---------------------------------------------------------------------------
# [3] hit identity and aliasing (machine IdentityCompare on sampled pairs,
#     host id() for the full-set aliasing count -- identity of objects is a
#     Python-level fact, the same one §5.2 sanctions for persistence)
# ---------------------------------------------------------------------------

print("[3] Hits return the same node; distinct values never alias")

hit_same = all(
    M.IdentityCompare(nat(n), NODES[n])() is M.truth_value for n in interned[::7]
)
check("re-lookup returns the identical node", hit_same)

alias_free = len({id(NODES[n]) for n in interned}) == len(interned)
check("no two distinct values share a nat node", alias_free)

zero = nat(0)
check("Zero is still the boot-chain Zero",
      M.IdentityCompare(zero, peano.Zero)() is M.truth_value)
one = nat(1)
ctor = M.GetConstructor(one, registry)()
check("small values keep the Succ constructor chain",
      M.IdentityCompare(M.Head(ctor)(), M.SuccLabel)() is M.truth_value
      and rep_of(1) == 1)
seven_pred = peano.NatPred(nat(7), registry)()
check("NatPred(7) is the node NatFromRep(6) returns",
      M.IdentityCompare(M.Head(seven_pred)(), nat(6))() is M.truth_value)

print()

# ---------------------------------------------------------------------------
# [4] legacy-layout compatibility: a tree stored by an earlier version
# ---------------------------------------------------------------------------

print("[4] Legacy-layout tree: lookups, miss, insert-and-migrate")


def legacy_index_key(exact_key):
    """The pre-W18 index key, rebuilt here by hand: every atom collapses."""
    if M.IsPair(exact_key)() is M.false_value:
        return M.Pair(T.IndexAtomKeyLabel, M.EmptyList)
    label = M.Head(exact_key)()
    if M.IdentityCompare(label, T.ExactAtomKeyLabel)() is M.truth_value:
        return M.Pair(T.IndexAtomKeyLabel, M.EmptyList)
    if M.IdentityCompare(label, T.ExactPairKeyLabel)() is M.truth_value:
        head_key = legacy_index_key(M.Head(M.Tail(exact_key)())())
        tail_key = legacy_index_key(M.Head(M.Tail(M.Tail(exact_key)())())())
        return T.IndexPairKey(head_key, tail_key).result
    raise RuntimeError("fixture covers pair/atom keys only")


legacy_facts = {}
legacy_root = M.EmptyList
for n in range(80, 90):
    key = peano.NatValueKey(M.GMPRep(str(n)))()
    legacy_facts[n] = nat(n)
    exact_key = T.ExactKey(key, registry)()
    legacy_root = T.TreePatriciaInsert(
        legacy_root, T.TreePatriciaPath(legacy_index_key(exact_key))(),
        exact_key, key, legacy_facts[n],
    )()
legacy_tree = M.Tree(legacy_root)


def lookup(tree, n):
    return T.TreeLookup(tree, peano.NatValueKey(M.GMPRep(str(n)))(), registry)()


found = all(
    M.IdentityCompare(lookup(legacy_tree, n), legacy_facts[n])() is M.truth_value
    for n in range(80, 90)
)
check("legacy-layout lookups still find every stored entry", found)
check("legacy-layout miss is absent, not a crash",
      M.IdentityCompare(lookup(legacy_tree, 999), M.EmptyList)() is M.truth_value)

legacy_facts[95] = nat(95)
updated = T.TreeInsert(legacy_tree, peano.NatValueKey(M.GMPRep("95"))(), legacy_facts[95], registry)()
legacy_tree.value = updated.value
survived = all(
    M.IdentityCompare(lookup(legacy_tree, n), legacy_facts[n])() is M.truth_value
    for n in range(80, 90)
)
check("the first insert migrates the tree; old entries survive it", survived)
check("the entry that triggered the migration is found",
      M.IdentityCompare(lookup(legacy_tree, 95), legacy_facts[95])() is M.truth_value)
check("post-migration miss is still absent",
      M.IdentityCompare(lookup(legacy_tree, 999), M.EmptyList)() is M.truth_value)

for n in range(96, 100):
    legacy_facts[n] = nat(n)
    upd = T.TreeInsert(legacy_tree, peano.NatValueKey(M.GMPRep(str(n)))(), legacy_facts[n], registry)()
    legacy_tree.value = upd.value
mixed = all(
    M.IdentityCompare(lookup(legacy_tree, n), legacy_facts[n])() is M.truth_value
    for n in range(95, 100)
)
check("post-migration inserts are found too", mixed)

print()

# ---------------------------------------------------------------------------
# [5] the fresh index still answers after all of the above
# ---------------------------------------------------------------------------

print("[5] The runtime's own index is unaffected by the fixture detour")

check("a fresh value lands in the runtime index",
      rep_of(4242) == 4242)
check("earlier values still hit the same nodes",
      all(M.IdentityCompare(nat(n), NODES[n])() is M.truth_value
          for n in (1000, 1049, 2299, 2549)))

print()

# ---------------------------------------------------------------------------
# [6] kernel purity of trees.py
# ---------------------------------------------------------------------------

print("[6] trees.py stays free of forbidden constructs")

with open(os.path.join(REPO, "trees.py"), "r", encoding="utf-8") as fh:
    source = fh.read()
banned = ["isinstance(", "hasattr(", "type(", "__class__"]
hits = [b for b in banned if b in source]
check("no isinstance/hasattr/type/__class__ in trees.py", not hits,
      "found: %s" % hits if hits else "")
check("no host-side dict cache in trees.py",
      "dict(" not in source and ".get(" not in source)

print()
print("=== TEST 30 RESULTS ===")
passed = 0
for _name, ok, _detail in RESULTS:
    if ok:
        passed = passed + 1
failed = len(RESULTS) - passed
for name, ok, detail in RESULTS:
    if not ok:
        print("  FAILED: " + name + ("  -- " + detail if detail else ""))
print("  Checks passed: " + str(passed) + "/" + str(len(RESULTS)))
print("  Total time:    %.3fs" % (time.time() - T0))
print()
if failed:
    print("=== TEST 30 FAILED ===")
    sys.exit(1)
print("=== TEST 30 COMPLETE ===")
