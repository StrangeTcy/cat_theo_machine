# ============================================================
# TEST 47: Machine-Native Playground Projections & Auto Lemma Suggestion
# ============================================================
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PARENT = os.path.dirname(REPO)
PACKAGE = os.path.basename(REPO)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import playground as PG
from cat_theo_machine.runtime import make_fresh_runtime

T0 = time.time()
RESULTS = []


def check(name, cond, detail=""):
    ok = bool(cond)
    RESULTS.append((name, ok, detail))
    status = "PASS" if ok else "FAIL"
    suffix = f" ({detail})" if detail and not ok else ""
    print(f"    {status}  {name}{suffix}")


print("=== TEST 47: Machine-Native Playground Projections & Auto Lemma Suggestion ===")
print()

# ---------------------------------------------------------------------------
# [1] Pure-machine coordinate & set edges (SetDifference, SortNatChain,
#     TupleElementAt, ProjectCoordinate, ProjectAllCoordinates)
# ---------------------------------------------------------------------------
print("[1] Pure-machine set & coordinate projection edges")
rt = make_fresh_runtime()
reg = M.FromContextGetConstructors(rt.graph)()

unsorted_chain = M.Pair(M.three, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
sorted_chain = PG.SortNatChain(unsorted_chain, reg)()
check(
    "SortNatChain orders Nat chain as {1, 2, 3}",
    PG._format_set_chain(sorted_chain, reg) == "{1, 2, 3}",
)

diff_chain = PG.SetDifference(
    sorted_chain, M.Pair(M.two, M.EmptyList), reg
)()
check(
    "SetDifference({1, 2, 3}, {2}) == {1, 3}",
    PG._format_set_chain(diff_chain, reg) == "{1, 3}",
)

elem_res = PG.TupleElementAt(sorted_chain, M.one, reg)()
check(
    "TupleElementAt([1, 2, 3], 1) == 2",
    M.NatEq(M.Head(elem_res)(), M.two, reg)() is M.truth_value,
)
print()

# ---------------------------------------------------------------------------
# [2] Machine-native expression extraction, substitution, and Pair spec record
# ---------------------------------------------------------------------------
print("[2] Machine-native expression edges and Pair goal specification")
spec_rec = PG.parse_surface_goal_spec(
    "prove that for all positive integers x, y, z and for n > 2 x^n + y^n = z^n has no solutions",
    reg,
)
check(
    "parse_surface_goal_spec returns a machine Pair record",
    M.IsPair(spec_rec)() is M.truth_value,
)
(
    lhs,
    rhs,
    base_vars,
    exp_vars,
    param_constraints,
    no_solutions,
    positive_only,
    reg,
) = PG._unpack_goal_spec(spec_rec)

check(
    "base_vars chain formatted as 'x, y, z'",
    PG._format_vars_chain(base_vars) == "x, y, z",
)
check(
    "exp_vars chain formatted as 'n'",
    PG._format_vars_chain(exp_vars) == "n",
)
check(
    "param_constraints contains ExprLt(2, n)",
    M.IsPair(param_constraints)() is M.truth_value
    and M.IdentityCompare(M.Head(M.Head(param_constraints)())(), L.ExprLtLabel)()
    is M.truth_value,
)
check("no_solutions flag is M.truth_value", no_solutions is M.truth_value)
check("positive_only flag is M.truth_value", positive_only is M.truth_value)

exp_var = M.Head(exp_vars)()
filtered_exps, reg = PG._filter_candidate_parameters(
    exp_var, param_constraints, reg
)
check(
    "FilterTuples + _evaluate_nat_constraints selects n in {3, 4}",
    PG._format_set_chain(filtered_exps, reg) == "{3, 4}",
)

lhs_3 = M.Head(PG.SubstituteExprVar(lhs, exp_var, M.three, reg)())()
rhs_3 = M.Head(PG.SubstituteExprVar(rhs, exp_var, M.three, reg)())()
check(
    "SubstituteExprVar instantiates lhs to x^3 + y^3",
    PG.RenderNatExpr(lhs_3, reg) == "x^3 + y^3",
)
check(
    "SubstituteExprVar instantiates rhs to z^3",
    PG.RenderNatExpr(rhs_3, reg) == "z^3",
)
print()

# ---------------------------------------------------------------------------
# [3] Pure-machine ResidueTable, CongruenceClasses, and Coordinate Projections
# ---------------------------------------------------------------------------
print("[3] Goal-directed sweeps via ResidueTable, CongruenceClasses, and ProjectAllCoordinates")

g_flt = make_fresh_runtime().graph
out_flt = PG.run_playground_interactive(
    g_flt,
    goal_text="prove that for all positive integers x, y, z and for n > 2 x^n + y^n = z^n has no solutions",
)
check(
    "parametric sweep instantiates n = 3 and n = 4",
    "[Instance n = 3: x^3 + y^3 = z^3]" in out_flt
    and "[Instance n = 4: x^4 + y^4 = z^4]" in out_flt,
)
check(
    "n = 3 reports ResidueTable((z^3) mod 4) -> image {0, 1, 3} (excluded: {2})",
    "ResidueTable((z^3) mod 4) -> image {0, 1, 3} (excluded: {2})" in out_flt,
)
check(
    "n = 4 reports ResidueTable((x^4 + y^4) mod 4) -> image {0, 1, 2} and CongruenceClasses |holding| = 24, |failing| = 40",
    "ResidueTable((x^4 + y^4) mod 4) -> image {0, 1, 2} (excluded: {3})" in out_flt
    and "CongruenceClasses((x^4 + y^4) = (z^4) mod 4) -> |holding| = 24, |failing| = 40" in out_flt,
)

g_disj = make_fresh_runtime().graph
out_disj = PG.run_playground_interactive(
    g_disj,
    goal_text="prove that for all integers x, y, z x^2 + y^2 = 4*z + 3 has no solutions",
)
check(
    "x^2 + y^2 = 4*z + 3 discovers Disjoint Image Regularity at m = 4 ({3} /\\ {0, 1, 2} = empty, |holding| = 0)",
    "Disjoint Image Regularity: {3} /\\ {0, 1, 2} = empty (|holding| = 0)" in out_disj,
)

g_coord = make_fresh_runtime().graph
out_coord = PG.run_playground_interactive(
    g_coord,
    goal_text="prove that for all integers x, y x^2 = 4*y + 1 has no solutions",
)
check(
    "x^2 = 4*y + 1 projects Coordinate Projection proj(x, holding) = {1, 3} (excluded mod 4: {0, 2})",
    "Coordinate Projection: proj(x, holding) = {1, 3} (excluded mod 4: {0, 2})" in out_coord,
)
check(
    "x^2 = 4*y + 1 projects Coordinate Projection proj(y, holding) = {0, 2} (excluded mod 3: {1})",
    "Coordinate Projection: proj(y, holding) = {0, 2} (excluded mod 3: {1})" in out_coord,
)

g_pyth = make_fresh_runtime().graph
out_pyth = PG.run_playground_interactive(
    g_pyth,
    goal_text="prove that for all positive integers x, y, z x^2 + y^2 = z^2 has no solutions",
)
check(
    "x^2 + y^2 = z^2 finds ground tensor witness (x = 3, y = 4, z = 5)",
    "x = 3, y = 4, z = 5" in out_pyth,
)

g_id = make_fresh_runtime().graph
out_id = PG.run_playground_interactive(
    g_id,
    goal_text="prove that for all naturals x, y (x + y)^2 = x^2 + 2*x*y + y^2",
)
check(
    "(x + y)^2 = x^2 + 2*x*y + y^2 verified by PolynomialIdentityByGrid",
    "PolynomialIdentityByGrid verified (x + y)^2 = x^2 + 2*x*y + y^2 across all 9 degree-bounded grid points" in out_id,
)

g_refute = make_fresh_runtime().graph
out_refute = PG.run_playground_interactive(
    g_refute,
    goal_text="prove that for all naturals x, y (x + y)^2 = x^2 + y^2",
)
check(
    "(x + y)^2 = x^2 + y^2 refuted by counterexample (x = 1, y = 1)",
    "Counterexample Witness Found: (x = 1, y = 1)" in out_refute,
)
print()

# ---------------------------------------------------------------------------
# [4] Automatic lemma suggestion in `main.py live` without typing `suggest lemmas`
# ---------------------------------------------------------------------------
print("[4] main.py live automatically suggests lemmas when a proof goal cannot be proved")
script = "\n".join(
    [
        "suggest lemmas",
        "commutativity of add()",
        "prove that for all positive integers x, y, z and for n > 2 x^n + y^n = z^n has no solutions",
        "ground lemma",
        "load pack funceq-nt",
        "if a is even then a + 1 is odd",
        "quit",
        "",
    ]
)
env = dict(os.environ)
env["PYTHONPATH"] = PARENT
t_repl = time.time()
proc = subprocess.run(
    [sys.executable, "-m", PACKAGE + ".main", "live"],
    input=script,
    capture_output=True,
    text=True,
    cwd=PARENT,
    env=env,
    timeout=600,
)
out_live = proc.stdout + proc.stderr
print(f"    live mode round trip {time.time() - t_repl:.1f}s")

check(
    "direct reply 'commutativity of add()' after 'Would you care to give it a name?' is accepted",
    "Rule 'commutativity of add()' is now active." in out_live,
)
for _log_cand in (
    os.path.join(PARENT, "talk_lessons.log"),
    os.path.join(REPO, "talk_lessons.log"),
):
    if os.path.exists(_log_cand):
        os.remove(_log_cand)
check(
    "live mode prints \"no, I can't prove that\"",
    "[machine] no, I can't prove that" in out_live,
)
check(
    "live mode automatically runs playground sweep without 'suggest lemmas'",
    "[machine] Running internal introspection and Cartesian playground sweep..." in out_live,
)
check(
    "live mode emits [debug: cartesian_playground process <pid>] natural tensor trace",
    "[debug: cartesian_playground process " in out_live
    and "constructing the natural tensor" in out_live,
)
check(
    "live mode auto-suggestion analyzes x^n + y^n = z^n (n = 3 and n = 4)",
    "[Instance n = 3: x^3 + y^3 = z^3]" in out_live
    and "[Instance n = 4: x^4 + y^4 = z^4]" in out_live,
)
check(
    "undecided tutor claim ('if a is even then a + 1 is odd') auto-suggests backward obligation Odd(1)",
    "Backward Rule Candidate: 'sum_even_odd' concludes Odd(a+1) given missing premise(s): Odd(1)" in out_live,
)
print()

print("=== TEST 47 RESULTS ===")
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = len(RESULTS) - passed
for name, ok, detail in RESULTS:
    if not ok:
        print("  FAILED: " + name + (" -- " + detail if detail else ""))
print(f"  Checks passed: {passed}/{len(RESULTS)}")
print(f"  Total time:    {time.time() - T0:.3f}s")
print()
if failed:
    print("=== TEST 47 FAILED ===")
    sys.exit(1)
print("=== TEST 47 COMPLETE ===")
