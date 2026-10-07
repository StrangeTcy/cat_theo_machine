# ============================================================
# TEST 13: Irreducible Machine-Native Cartesian Playground Verification
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
print("=== TEST 13: Irreducible Machine-Native Cartesian Playground ===")
print()

print("[1] Initializing runtime, hypergraph, and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

print("[2] Test Case 1: Machine-Native ChainLength & Peano Counting...")
# Make a 3-element test list
n1_res = M.NatFromRep(M.GMPRep(1), registry)()
n1 = M.Head(n1_res)()
reg1 = M.Head(M.Tail(n1_res)())()

n2_res = M.NatFromRep(M.GMPRep(2), reg1)()
n2 = M.Head(n2_res)()
reg2 = M.Head(M.Tail(n2_res)())()

n3_res = M.NatFromRep(M.GMPRep(3), reg2)()
n3 = M.Head(n3_res)()
reg3 = M.Head(M.Tail(n3_res)())()

test_chain = M.Pair(n1, M.Pair(n2, M.Pair(n3, M.EmptyList)))
len_res = PG.ChainLength(test_chain, reg3)()
len_node = M.Head(len_res)()
reg4 = M.Head(M.Tail(len_res)())()

len_val = M.NatRepOf(len_node, reg4)()()
print(f"    Chain length: {len_val} (Expected: 3)")
assert len_val == 3, f"Expected length 3, got {len_val}"

print("[3] Test Case 2: Machine-Native BuildNatRange...")
n11_res = M.NatFromRep(M.GMPRep(11), reg4)()
n11 = M.Head(n11_res)()
reg5 = M.Head(M.Tail(n11_res)())()

range_res = PG.BuildNatRange(M.Zero, n11, reg5)()
domain_11 = M.Head(range_res)()
reg6 = M.Head(M.Tail(range_res)())()

dom_len_res = PG.ChainLength(domain_11, reg6)()
dom_len_node = M.Head(dom_len_res)()
reg7 = M.Head(M.Tail(dom_len_res)())()
dom_len_val = M.NatRepOf(dom_len_node, reg7)()()

print(f"    Generated domain elements: {dom_len_val} (Expected: 11)")
assert dom_len_val == 11, f"Expected 11 elements, got {dom_len_val}"

print("[4] Test Case 3: Irreducible ProductOfDomains (k-ary Cartesian Products)...")
range_3_res = PG.BuildNatRange(M.Zero, n3, reg7)()
domain_3 = M.Head(range_3_res)()
reg8 = M.Head(M.Tail(range_3_res)())()

# 2-ary product: ProductOfDomains([domain_3, domain_3])
prod_2 = PG.ProductOfDomains(M.Pair(domain_3, M.Pair(domain_3, M.EmptyList)))()
prod_len_res = PG.ChainLength(prod_2, reg8)()
prod_len_node = M.Head(prod_len_res)()
reg9 = M.Head(M.Tail(prod_len_res)())()
prod_len_val = M.NatRepOf(prod_len_node, reg9)()()

print(f"    Product 3x3 tuple count: {prod_len_val} (Expected: 9)")
assert prod_len_val == 9, f"Expected 9 pairs, got {prod_len_val}"

print("[5] Test Case 4: MapDomain with 1-ary & 2-ary Tuples...")
n4_res = M.NatFromRep(M.GMPRep(4), reg9)()
n4 = M.Head(n4_res)()
reg10 = M.Head(M.Tail(n4_res)())()

# 1-ary domain: ProductOfDomains([domain_11])
dom1 = PG.ProductOfDomains(M.Pair(domain_11, M.EmptyList))()

def square_fn(tuple_args, reg):
    x = M.Head(tuple_args)()
    return A.Multiply(x, x, reg)()

sq_map_res = PG.MapDomain(dom1, square_fn, reg10)()
sq_list = M.Head(sq_map_res)()
reg11 = M.Head(M.Tail(M.Tail(sq_map_res)())())()

sq_proj_res = PG.ProjectCongruence(sq_list, n4, reg11)()
sq_mod_set = M.Head(sq_proj_res)()
reg12 = M.Head(M.Tail(sq_proj_res)())()

sq_vals = []
cur = sq_mod_set
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    v = M.NatRepOf(M.Head(cur)(), reg12)()()
    if v not in sq_vals:
        sq_vals.append(v)
    cur = M.Tail(cur)()

print(f"    Squares mod 4 set: {sorted(sq_vals)} (Expected: [0, 1])")
assert sorted(sq_vals) == [0, 1], f"Expected [0, 1], got {sq_vals}"

print("[6] Test Case 5: FilterTuples & 2-ary Sum of Squares...")
dom2 = PG.ProductOfDomains(M.Pair(domain_11, M.Pair(domain_11, M.EmptyList)))()

def odd_pair_pred(tuple_args, reg):
    x = M.Head(tuple_args)()
    y = M.Head(M.Tail(tuple_args)())()

    rx = A.Modulo(x, n2, reg)()
    rem_x = M.Head(rx)()
    r1 = M.Head(M.Tail(rx)())()
    eq_x = M.NatEq(rem_x, n1, r1)()

    ry = A.Modulo(y, n2, r1)()
    rem_y = M.Head(ry)()
    r2 = M.Head(M.Tail(ry)())()
    eq_y = M.NatEq(rem_y, n1, r2)()

    if eq_x is M.truth_value and eq_y is M.truth_value:
        return M.Pair(M.truth_value, M.Pair(r2, M.EmptyList))
    return M.Pair(M.false_value, M.Pair(r2, M.EmptyList))

odd_tuples_res = PG.FilterTuples(dom2, odd_pair_pred, reg12)()
odd_tuples = M.Head(odd_tuples_res)()
reg13 = M.Head(M.Tail(odd_tuples_res)())()

def sum_sq_fn(tuple_args, reg):
    x = M.Head(tuple_args)()
    y = M.Head(M.Tail(tuple_args)())()

    sx = A.Multiply(x, x, reg)()
    nx = M.Head(sx)()
    r1 = M.Head(M.Tail(sx)())()

    sy = A.Multiply(y, y, r1)()
    ny = M.Head(sy)()
    r2 = M.Head(M.Tail(sy)())()

    return A.Add(nx, ny, r2)()

odd_sum_map_res = PG.MapDomain(odd_tuples, sum_sq_fn, reg13)()
odd_sum_list = M.Head(odd_sum_map_res)()
reg14 = M.Head(M.Tail(M.Tail(odd_sum_map_res)())())()

odd_sum_proj_res = PG.ProjectCongruence(odd_sum_list, n4, reg14)()
odd_sum_mod_set = M.Head(odd_sum_proj_res)()
reg15 = M.Head(M.Tail(odd_sum_proj_res)())()

odd_vals = []
cur = odd_sum_mod_set
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    v = M.NatRepOf(M.Head(cur)(), reg15)()()
    if v not in odd_vals:
        odd_vals.append(v)
    cur = M.Tail(cur)()

print(f"    Odd sum of squares mod 4 set: {sorted(odd_vals)} (Expected: [2])")
assert sorted(odd_vals) == [2], f"Expected [2], got {odd_vals}"

print("[7] Test Case 6: EvaluateSetRelation Disjointness...")
disjoint_res = PG.EvaluateSetRelation(sq_mod_set, odd_sum_mod_set, reg15)()
is_disjoint = M.Head(disjoint_res)() is M.truth_value
reg16 = M.Head(M.Tail(M.Tail(disjoint_res)())())()

print(f"    Disjoint images: {is_disjoint} (Expected: True)")
assert is_disjoint, "Expected disjoint images!"

print("[8] Test Case 7: UniversalQuantify for Commutativity...")
def add_comm_rel(tuple_args, reg):
    x = M.Head(tuple_args)()
    y = M.Head(M.Tail(tuple_args)())()

    r_xy = A.Add(x, y, reg)()
    v_xy = M.Head(r_xy)()
    r1 = M.Head(M.Tail(r_xy)())()

    r_yx = A.Add(y, x, r1)()
    v_yx = M.Head(r_yx)()
    r2 = M.Head(M.Tail(r_yx)())()

    eq = M.NatEq(v_xy, v_yx, r2)()
    return M.Pair(eq, M.Pair(r2, M.EmptyList))

quant_res = PG.UniversalQuantify(prod_2, add_comm_rel, reg16)()
is_comm = M.Head(quant_res)() is M.truth_value
reg17 = M.Head(M.Tail(quant_res)())()

print(f"    Addition Commutativity Universal Invariant: {is_comm} (Expected: True)")
assert is_comm, "Expected addition commutativity to hold universally!"

print("[9] Test Case 8: RunPlaygroundCartesianSweep Pipeline...")
sweep_res = PG.RunPlaygroundCartesianSweep(n11, n4, registry)()
inv_rec = M.Head(sweep_res)()
rec_tag = M.Head(inv_rec)()
is_rec_ok = (
    M.IdentityCompare(rec_tag, L.DiscoveredInvariantLabel)() is M.truth_value
)
print(f"    Invariant record label: {rec_tag} (Passed: {is_rec_ok})")
assert is_rec_ok, "Expected DiscoveredInvariantLabel record!"

print("[10] Test Case 9: Interactive Proposal Output...")
output_str = PG.run_playground_interactive(graph)
print(f"    Proposal Output generated:\n{output_str}")
assert "Disjoint Image Regularity" in output_str, "Expected disjoint image regularity in output!"

print()
print(
    f"=== ALL TEST 13 IRREDUCIBLE CARTESIAN PLAYGROUND CHECKS PASSED in {time.time() - t0:.3f}s ==="
)
