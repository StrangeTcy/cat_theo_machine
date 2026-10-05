# ============================================================
# TEST 13: Generic Cartesian Playground & Invariant Sweep Verification
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
from cat_theo_machine.math import arithmetic as A
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 13: Generic Cartesian Playground & Invariant Sweep ===")
print()

print("[1] Initializing runtime, hypergraph, and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

print("[2] Test Case 1: Generic BuildNatRange Domain Generator...")
range_res = PG.BuildNatRange(0, 10, registry)()
nats_chain = M.Head(range_res)()
reg1 = M.Head(M.Tail(range_res)())()

count = 0
cur = nats_chain
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    count += 1
    cur = M.Tail(cur)()

print(f"    Domain elements generated: {count} (Expected: 11)")
assert count == 11, f"Expected 11 elements, got {count}"

print("[3] Test Case 2: Generic CartesianProduct Generator...")
range_3_res = PG.BuildNatRange(0, 2, reg1)()
domain_3 = M.Head(range_3_res)()
reg2 = M.Head(M.Tail(range_3_res)())()

cart_prod = PG.CartesianProduct(domain_3, domain_3)()
cart_count = 0
cur = cart_prod
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    cart_count += 1
    cur = M.Tail(cur)()

print(f"    Cartesian product 3x3 elements: {cart_count} (Expected: 9)")
assert cart_count == 9, f"Expected 9 pairs, got {cart_count}"

print("[4] Test Case 3: Generic MapUnary & ProjectCongruence...")
n4_res = M.NatFromRep(M.GMPRep(4), reg2)()
n4 = M.Head(n4_res)()
reg3 = M.Head(M.Tail(n4_res)())()

map_unary_res = PG.MapUnary(
    nats_chain, lambda x, reg: A.Multiply(x, x, reg)(), reg3
)()
sq_list = M.Head(map_unary_res)()
reg4 = M.Head(M.Tail(M.Tail(map_unary_res)())())()

proj_res = PG.ProjectCongruence(sq_list, n4, reg4)()
sq_mod_set = M.Head(proj_res)()
reg5 = M.Head(M.Tail(proj_res)())()

sq_vals = []
cur = sq_mod_set
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    v = M.NatRepOf(M.Head(cur)(), reg5)()()
    if v not in sq_vals:
        sq_vals.append(v)
    cur = M.Tail(cur)()

print(f"    Squares mod 4 image set: {sorted(sq_vals)} (Expected: [0, 1])")
assert sorted(sq_vals) == [0, 1], f"Expected [0, 1], got {sq_vals}"

print("[5] Test Case 4: Generic FilterDomain & MapBinary...")
n2_res = M.NatFromRep(M.GMPRep(2), reg5)()
n2 = M.Head(n2_res)()
reg6 = M.Head(M.Tail(n2_res)())()

n1_res = M.NatFromRep(M.GMPRep(1), reg6)()
n1 = M.Head(n1_res)()
reg7 = M.Head(M.Tail(n1_res)())()

def is_odd_pred(x, reg):
    m_res = A.Modulo(x, n2, reg)()
    rem = M.Head(m_res)()
    r_reg = M.Head(M.Tail(m_res)())()
    eq = M.NatEq(rem, n1, r_reg)()
    return M.Pair(eq, M.Pair(r_reg, M.EmptyList))

odd_domain_res = PG.FilterDomain(nats_chain, is_odd_pred, reg7)()
odd_domain = M.Head(odd_domain_res)()
reg8 = M.Head(M.Tail(odd_domain_res)())()

odd_cart = PG.CartesianProduct(odd_domain, odd_domain)()

def sum_sq_fn(x, y, reg):
    sx = A.Multiply(x, x, reg)()
    nx = M.Head(sx)()
    r1 = M.Head(M.Tail(sx)())()
    sy = A.Multiply(y, y, r1)()
    ny = M.Head(sy)()
    r2 = M.Head(M.Tail(sy)())()
    return A.Add(nx, ny, r2)()

odd_sum_map_res = PG.MapBinary(odd_cart, sum_sq_fn, reg8)()
odd_sum_list = M.Head(odd_sum_map_res)()
reg9 = M.Head(M.Tail(M.Tail(odd_sum_map_res)())())()

odd_sum_proj_res = PG.ProjectCongruence(odd_sum_list, n4, reg9)()
odd_sum_mod_set = M.Head(odd_sum_proj_res)()
reg10 = M.Head(M.Tail(odd_sum_proj_res)())()

odd_vals = []
cur = odd_sum_mod_set
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    v = M.NatRepOf(M.Head(cur)(), reg10)()()
    if v not in odd_vals:
        odd_vals.append(v)
    cur = M.Tail(cur)()

print(f"    Odd sum of squares mod 4 set: {sorted(odd_vals)} (Expected: [2])")
assert sorted(odd_vals) == [2], f"Expected [2], got {odd_vals}"

print("[6] Test Case 5: Generic DetectDisjointness...")
disjoint_res = PG.DetectDisjointness(sq_mod_set, odd_sum_mod_set, reg10)()
is_disjoint = M.Head(disjoint_res)()
reg11 = M.Head(M.Tail(M.Tail(disjoint_res)())())()
is_empty = is_disjoint is M.truth_value

print(f"    Intersection is empty: {is_empty} (Expected: True)")
assert is_empty, "Expected disjoint images!"

print("[7] Test Case 6: Generic DetectBinarySymmetry & DetectIdempotence...")
sym_add_res = PG.DetectBinarySymmetry(
    domain_3, lambda x, y, r: A.Add(x, y, r)(), reg11
)()
sym_add = M.Head(sym_add_res)() is M.truth_value
reg12 = M.Head(M.Tail(sym_add_res)())()

sym_mul_res = PG.DetectBinarySymmetry(
    domain_3, lambda x, y, r: A.Multiply(x, y, r)(), reg12
)()
sym_mul = M.Head(sym_mul_res)() is M.truth_value
reg13 = M.Head(M.Tail(sym_mul_res)())()

idem_gcd_res = PG.DetectIdempotence(
    odd_domain, lambda x, y, r: A.Gcd(x, y, r)(), reg13
)()
idem_gcd = M.Head(idem_gcd_res)() is M.truth_value
reg14 = M.Head(M.Tail(idem_gcd_res)())()

print(f"    Addition Symmetry: {sym_add} (Expected: True)")
print(f"    Multiplication Symmetry: {sym_mul} (Expected: True)")
print(f"    Gcd Idempotence: {idem_gcd} (Expected: True)")
assert sym_add and sym_mul and idem_gcd, "Expected symmetries and idempotence to hold!"

print("[8] Test Case 7: Generic RunPlaygroundCartesianSweep Pipeline...")
sweep_res = PG.RunPlaygroundCartesianSweep(0, 10, 4, registry)()
inv_rec = M.Head(sweep_res)()
rec_tag = M.Head(inv_rec)()
is_rec_ok = (
    M.IdentityCompare(rec_tag, L.DiscoveredInvariantLabel)() is M.truth_value
)
print(f"    Invariant record label: {rec_tag} (Passed: {is_rec_ok})")
assert is_rec_ok, "Expected DiscoveredInvariantLabel record!"

print("[9] Test Case 8: Interactive Proposal Output...")
output_str = PG.run_playground_interactive(graph)
print(f"    Proposal Output generated:\n{output_str}")
assert "Disjoint Image Regularity" in output_str, "Expected disjoint image regularity in output!"

print()
print(
    f"=== ALL TEST 13 GENERIC CARTESIAN PLAYGROUND CHECKS PASSED in {time.time() - t0:.3f}s ==="
)
