# ============================================================
# TEST 13: Cartesian Playground & Invariant Sweep Verification
# ============================================================
import os
import sys
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import playground as PG
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 13: Cartesian Playground & Invariant Sweep ===")
print()

print("[1] Initializing runtime, hypergraph, and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

print("[2] Test Case 1: Building Nat range 0..10...")
range_res = PG.BuildNatRange(0, 10, registry)()
nats_chain = M.Head(range_res)()
reg1 = M.Head(M.Tail(range_res)())()

# Check length of nats_chain is 11
count = 0
cur = nats_chain
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    count += 1
    cur = M.Tail(cur)()

print(f"    Range elements generated: {count} (Expected: 11)")
assert count == 11, f"Expected 11 elements, got {count}"

print("[3] Test Case 2: Squares Modulo 4 Sweep...")
n4_res = M.NatFromRep(M.GMPRep(4), reg1)()
n4 = M.Head(n4_res)()
reg2 = M.Head(M.Tail(n4_res)())()

sq_res = PG.ComputeSquaresMod(nats_chain, n4, reg2)()
sq_set = M.Head(sq_res)()
reg3 = M.Head(M.Tail(sq_res)())()

sq_vals = []
cur = sq_set
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    v = M.NatRepOf(M.Head(cur)(), reg3)()()
    if v not in sq_vals:
        sq_vals.append(v)
    cur = M.Tail(cur)()

print(f"    Squares mod 4 set: {sorted(sq_vals)} (Expected: [0, 1])")
assert sorted(sq_vals) == [0, 1], f"Expected [0, 1], got {sq_vals}"

print("[4] Test Case 3: Odd Sums of Squares Modulo 4 Sweep...")
n2_res = M.NatFromRep(M.GMPRep(2), reg3)()
n2 = M.Head(n2_res)()
reg4 = M.Head(M.Tail(n2_res)())()

n1_res = M.NatFromRep(M.GMPRep(1), reg4)()
n1 = M.Head(n1_res)()
reg5 = M.Head(M.Tail(n1_res)())()

odd_sum_res = PG.ComputeOddSumOfSquaresMod(nats_chain, n4, n2, n1, reg5)()
odd_sum_set = M.Head(odd_sum_res)()
reg6 = M.Head(M.Tail(odd_sum_res)())()

odd_vals = []
cur = odd_sum_set
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    v = M.NatRepOf(M.Head(cur)(), reg6)()()
    if v not in odd_vals:
        odd_vals.append(v)
    cur = M.Tail(cur)()

print(f"    Odd sum of squares mod 4 set: {sorted(odd_vals)} (Expected: [2])")
assert sorted(odd_vals) == [2], f"Expected [2], got {odd_vals}"

print("[5] Test Case 4: Disjoint Intersection & Invariant Detection...")
inter = PG.SetIntersection(sq_set, odd_sum_set, reg6)()
is_disjoint = (
    M.IdentityCompare(inter, M.EmptyList)() is M.truth_value
)
print(f"    Intersection is empty: {is_disjoint} (Expected: True)")
assert is_disjoint, "Expected empty intersection between squares and odd sums mod 4!"

print("[6] Test Case 5: Full RunPlaygroundCartesianSweep Edge...")
sweep_res = PG.RunPlaygroundCartesianSweep(registry)()
inv_rec = M.Head(sweep_res)()
rec_tag = M.Head(inv_rec)()
is_rec_ok = (
    M.IdentityCompare(rec_tag, L.DiscoveredInvariantLabel)() is M.truth_value
)
print(f"    Invariant record label: {rec_tag} (Passed: {is_rec_ok})")
assert is_rec_ok, "Expected DiscoveredInvariantLabel record!"

print("[7] Test Case 6: Interactive Proposal Output...")
output_str = PG.run_playground_interactive(graph)
print(f"    Proposal Output generated:\n{output_str}")
assert "ParityMod4Lemma" in output_str, "Expected ParityMod4Lemma proposal in output!"

print()
print(
    f"=== ALL TEST 13 CARTESIAN PLAYGROUND CHECKS PASSED in {time.time() - t0:.3f}s ==="
)
