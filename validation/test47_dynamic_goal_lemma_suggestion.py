# ============================================================
# TEST 47: Dynamic Goal-Directed Playground Sweep & Automatic Lemma Suggestion
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


print("=== TEST 47: Dynamic Goal-Directed Playground Sweep & Auto Lemma Suggestion ===")
print()

# ---------------------------------------------------------------------------
# [1] Machine-native expression extraction, substitution, and rendering edges
# ---------------------------------------------------------------------------
print("[1] Machine-native expression edges (ExtractExprVariables, ExtractExponentVariables, SubstituteExprVar)")
rt = make_fresh_runtime()
reg = M.FromContextGetConstructors(rt.graph)()

spec = PG.parse_surface_goal_spec(
    "prove that for all positive integers x, y, z and for n > 2 x^n + y^n = z^n has no solutions",
    reg,
)
check("surface goal parses into lhs/rhs ASTs", spec is not None)
reg = spec["registry"]
base_names = PG._vars_chain_to_names(spec["base_vars"])
exp_names = PG._vars_chain_to_names(spec["exp_vars"])
check("base variables extracted as ['x', 'y', 'z']", base_names == ["x", "y", "z"], str(base_names))
check("exponent variable extracted as ['n']", exp_names == ["n"], str(exp_names))
check("parameter lower bound n > 2 parsed as n >= 3", spec["param_min"].get("n") == 3, str(spec["param_min"]))
check("no_solutions flag is True", spec["no_solutions"] is True)
check("positive_only flag is True", spec["positive_only"] is True)

n3_res = M.NatFromRep(M.GMPRep(3), reg)()
n3 = M.Head(n3_res)()
reg = M.Head(M.Tail(n3_res)())()
exp_var = M.Head(spec["exp_vars"])()
lhs_3 = M.Head(PG.SubstituteExprVar(spec["lhs"], exp_var, n3, reg)())()
rhs_3 = M.Head(PG.SubstituteExprVar(spec["rhs"], exp_var, n3, reg)())()
check("SubstituteExprVar instantiates lhs to x^3 + y^3", PG.RenderNatExpr(lhs_3, reg) == "x^3 + y^3")
check("SubstituteExprVar instantiates rhs to z^3", PG.RenderNatExpr(rhs_3, reg) == "z^3")
print()

# ---------------------------------------------------------------------------
# [2] Non-hardcoded goal-directed sweeps produce distinct invariants per goal
# ---------------------------------------------------------------------------
print("[2] Dynamic Cartesian sweeps across distinct equations and exponents")

g_flt = make_fresh_runtime().graph
out_flt = PG.run_playground_interactive(
    g_flt,
    goal_text="prove that for all positive integers x, y, z and for n > 2 x^n + y^n = z^n has no solutions",
)
check("FLT n > 2 sweep instantiates n = 3 (x^3 + y^3 = z^3)", "Instance n = 3: x^3 + y^3 = z^3" in out_flt)
check("FLT n > 2 sweep instantiates n = 4 (x^4 + y^4 = z^4)", "Instance n = 4: x^4 + y^4 = z^4" in out_flt)
check("n = 3 discovers separating modulus m = 7 ({1, 6} /\\ {0, 2, 5} = empty)", "Separating Modulus m = 7" in out_flt and "{1, 6} /\\ {0, 2, 5} = empty" in out_flt)
check("n = 3 discovers separating modulus m = 9 ({1, 8} /\\ {0, 2, 7} = empty)", "Separating Modulus m = 9" in out_flt and "{1, 8} /\\ {0, 2, 7} = empty" in out_flt)
check("n = 4 discovers separating moduli m = 3 and m = 4", "Separating Modulus m = 3" in out_flt and "Separating Modulus m = 4" in out_flt)
check("FLT n > 2 output never emits hardcoded 'f([x]) = x^2 mod 4'", "f([x]) = x^2 mod 4" not in out_flt)

g_global = make_fresh_runtime().graph
out_global = PG.run_playground_interactive(
    g_global,
    goal_text="prove that for all integers x, y, z x^2 + y^2 = 4*z + 3 has no solutions",
)
check("x^2 + y^2 = 4*z + 3 discovers unrestricted modulus m = 4", "Separating Modulus m = 4 (unrestricted domain)" in out_global)
check("x^2 + y^2 = 4*z + 3 projects {3} /\\ {0, 1, 2} = empty", "{3} /\\ {0, 1, 2} = empty" in out_global)

g_pyth = make_fresh_runtime().graph
out_pyth = PG.run_playground_interactive(
    g_pyth,
    goal_text="prove that for all positive integers x, y, z x^2 + y^2 = z^2 has no solutions",
)
check("x^2 + y^2 = z^2 finds Pythagorean counterexample (x = 3, y = 4, z = 5)", "x = 3, y = 4, z = 5" in out_pyth)

g_id = make_fresh_runtime().graph
out_id = PG.run_playground_interactive(
    g_id,
    goal_text="prove that for all naturals x, y (x + y)^2 = x^2 + 2*x*y + y^2",
)
check("(x + y)^2 = x^2 + 2*x*y + y^2 verified by PolynomialIdentityByGrid", "PolynomialIdentityByGrid verified (x + y)^2 = x^2 + 2*x*y + y^2 across all 9 degree-bounded grid points" in out_id)

g_refute = make_fresh_runtime().graph
out_refute = PG.run_playground_interactive(
    g_refute,
    goal_text="prove that for all naturals x, y (x + y)^2 = x^2 + y^2",
)
check("(x + y)^2 = x^2 + y^2 refuted by counterexample (x = 1, y = 1)", "Counterexample Witness Found: (x = 1, y = 1)" in out_refute)
print()

# ---------------------------------------------------------------------------
# [3] Automatic lemma suggestion in `main.py live` without typing `suggest lemmas`
# ---------------------------------------------------------------------------
print("[3] main.py live automatically suggests lemmas when a proof goal cannot be proved")
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

check("direct reply 'commutativity of add()' after 'Would you care to give it a name?' is accepted without 'call this'", "Rule 'commutativity of add()' is now active." in out_live)
for _log_cand in (os.path.join(PARENT, "talk_lessons.log"), os.path.join(REPO, "talk_lessons.log")):
    if os.path.exists(_log_cand):
        os.remove(_log_cand)
check("live mode prints \"no, I can't prove that\"", "[machine] no, I can't prove that" in out_live)
check("live mode automatically runs playground sweep without 'suggest lemmas'", "[machine] Running internal introspection and Cartesian playground sweep..." in out_live)
check("live mode emits [debug: cartesian_playground process <pid>] natural tensor trace", "[debug: cartesian_playground process " in out_live and "constructing the natural tensor:" in out_live)
check("live mode auto-suggestion analyzes x^n + y^n = z^n (n = 3 and n = 4)", "Instance n = 3: x^3 + y^3 = z^3" in out_live and "Instance n = 4: x^4 + y^4 = z^4" in out_live)
check("subsequent 'ground lemma' promotes the dynamically discovered mod_7 invariant (not hardcoded mod_4)", "Promoted: mod_7_disjoint_image_obstruction -> Active Certified Ledger" in out_live)
check("undecided tutor claim ('if a is even then a + 1 is odd') also auto-suggests backward obligation Odd(1)", "Backward Rule Candidate: 'sum_even_odd' concludes Odd(a+1) given missing premise(s): Odd(1)" in out_live)
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
