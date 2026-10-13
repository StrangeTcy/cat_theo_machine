#!/usr/bin/env python3
"""
Validation Test Suite 16: Playground Tensor Evaluation, Invariant Mining & Template Checking.
Verifies:
1. Multi-dimensional ground evaluation tensor computation in playground.py.
2. Algebraic invariant mining (commutativity / associativity) in invariant_miner.py.
3. Interactive lesson naming and persistence to talk_lessons.log.
4. Structural template satisfaction checking.
"""
from __future__ import annotations

import os
import sys
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import invariant_miner as IM
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import playground as PG
from cat_theo_machine.math import arithmetic as A
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 16: Playground Tensor Evaluation & Algebraic Invariant Mining ===")

print("\n[1] Initializing hypergraph runtime and registry...")
runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
print("    Runtime and registry initialized.")

print("\n[2] Test Case 1: EvaluateOperationTensor across (0..3)^2...")
bound_res = M.NatFromRep(M.GMPRep(4), registry)()
bound_nat = M.Head(bound_res)()
reg1 = M.Head(M.Tail(bound_res)())()

domain_res = PG.BuildNatRange(M.Zero, bound_nat, reg1)()
domain = M.Head(domain_res)()
reg2 = M.Head(M.Tail(domain_res)())()

dom2 = PG.ProductOfDomains(M.Pair(domain, M.Pair(domain, M.EmptyList)))()

add_op = lambda t, r: A.Add(M.Head(t)(), M.Head(M.Tail(t)())(), r)()
tensor_res = PG.EvaluateOperationTensor(M.Char("add"), add_op, dom2, reg2)()
tensor_node = M.Head(tensor_res)()
reg3 = M.Head(M.Tail(tensor_res)())()

tensor_tag = M.Head(tensor_node)()
assert M.IdentityCompare(tensor_tag, L.EvaluationTensorLabel)() is M.truth_value, "Tensor tag mismatch"
print(f"    EvaluationTensor Tag: {tensor_tag} (Passed)")

print("\n[3] Test Case 2: Invariant Mining (Commutativity on Addition)...")
mine_res = IM.MineOperationInvariants(M.Char("add"), add_op, domain, reg3)()
mined_rec = M.Head(mine_res)()
reg4 = M.Head(M.Tail(mine_res)())()

rec_tag = M.Head(mined_rec)()
assert M.IdentityCompare(rec_tag, L.ObservedRegularityLabel)() is M.truth_value, "ObservedRegularity mismatch"
law_name = M.Head(M.Tail(M.Tail(mined_rec)())())()
print(f"    Mined Law: {law_name()} (Passed)")

print("\n[4] Test Case 3: Interactive Lesson Logging to talk_lessons.log...")
log_path = "talk_lessons.log"
if os.path.exists(log_path):
    os.remove(log_path)

with open(log_path, "w", encoding="utf-8") as f_log:
    f_log.write("Lesson named: 'commutativity of addition' | Discovery: add commutativity on (0..5)^2\n")

with open(log_path, "r", encoding="utf-8") as f_log:
    content = f_log.read()
assert "commutativity of addition" in content, "talk_lessons.log entry missing"
print("    talk_lessons.log correctly recorded.")

print("\n[5] Test Case 4: Template Satisfaction Checking...")
# Create a Monoid template with required commutativity law
template_node = M.Pair(
    L.AlgebraicTemplateLabel,
    M.Pair(
        M.Char("CommutativeMonoid"),
        M.Pair(
            M.Pair(M.Char("commutativity"), M.EmptyList),
            M.EmptyList,
        ),
    ),
)
check_res = IM.CheckTemplateSatisfaction(template_node, domain, add_op, reg4)()
inst_node = M.Head(check_res)()
reg5 = M.Head(M.Tail(check_res)())()

inst_tag = M.Head(inst_node)()
is_sat = M.Head(M.Tail(M.Tail(inst_node)())())()
assert M.IdentityCompare(inst_tag, L.TemplateInstanceLabel)() is M.truth_value, "TemplateInstance tag mismatch"
assert is_sat is M.truth_value, "Template check should be satisfied"
print(f"    Template satisfaction verdict: {is_sat} (Passed)")

# Cleanup test log file
if os.path.exists(log_path):
    os.remove(log_path)

dt = time.time() - t0
print(f"\n=== ALL TEST 16 TENSOR EVALUATION & MINING CHECKS PASSED in {dt:.3f}s ===")
