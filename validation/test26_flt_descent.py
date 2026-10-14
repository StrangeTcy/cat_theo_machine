# ============================================================
# TEST 26: FLT n = 4, the descent half -- what the machine can and cannot do
#
# Slot 26 is the one `delegation/README.md` pre-allocates to the W6 remainder
# (`delegation/W06-flt-n4-descent.md`). The brief's done-definition has three
# rungs; this suite reaches the second, **partial**, with a demonstrated
# negative account of what is missing, and says so in [9].
#
# No pack here carries a quartic rule, a Pythagorean parametrisation, a
# solution constant or a lemma about squares. The only authored schema is a
# strategy axiom (infinite descent, `packs/infinite-descent.pack.yaml`), and
# it is named as authored, not derived. Everything else is one of:
#
#   DERIVED    -- decided by a generic machine procedure that is sound by a
#                 stated theorem about polynomials (grid identity lemma;
#                 residues respect the ring operations), or a Checker-B
#                 verified knowledge-rewrite derivation;
#   EVIDENCED  -- checked by the machine's own arithmetic on a bounded sweep,
#                 which proves nothing about the general case and is treated
#                 as such: the promotion ledger refuses it;
#   MISSING    -- shown not to be reachable with the current machinery, with
#                 the absent constructor named.
#
# Sections:
#   [1] boot, the two strategy packs, the separating modulus re-discovered by
#       the sweep (so the modulus used in [4] is the machine's, not a constant)
#   [2] PolynomialIdentityByGrid on controls: a true identity, a false one
#       (witness), the degree-bound trap (a 2-point grid would have passed a
#       non-identity; the structural bound forces 3 points), a refused term
#   [3] the descent's identities, DERIVED: the Pythagorean square identity in
#       additive form and x^4 = (x^2)^2
#   [4] the residue step, DERIVED: odd squares are 1 mod 4, and the classes
#       of 1 + n^2 = m^2 (mod 4) are exactly m odd, n even
#   [5] the parametrised family on data, EVIDENCED: every primitive triple
#       with an even leg below the bound is hit by some coprime opposite-
#       parity (m, n); coprime factors of a square are squares on the sweep
#       (and the coprimality hypothesis is load-bearing: a non-coprime
#       counterexample); the measure of the would-be smaller solution drops
#   [6] the descent skeleton, DERIVED conditionally: a 2-step derivation
#       (monovariant_terminates, infinite_descent) from four hypotheses to
#       NoStates, Checker-B verified, rejected against the wrong goal, and not
#       findable without EveryStateMoves
#   [7] the ledger: the three sweep-evidenced candidates are refused (no
#       receipt), the conditional derivation is not submitted, version stays 0
#   [8] the obstruction, demonstrated: no loaded rule can introduce a witness
#       (every replacement variable is bound by a premise), the symbolic
#       rewrite walker is stuck on the identity the grid decided, and the
#       arithmetic layer has no factorisation, root or subtraction edge
#   [9] the account: which done-definition rung was reached and why
#
# Host layer: paths, timing, counting, printing. Assertions about machine
# content are IdentityCompare / Compare / NatEq / NatLess on machine terms.

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
P = importlib.import_module(PACKAGE + ".proof")
L = importlib.import_module(PACKAGE + ".labels")
CB = importlib.import_module(PACKAGE + ".checker_b")
PL = importlib.import_module(PACKAGE + ".promotion_ledger")
Eval = importlib.import_module(PACKAGE + ".evaluator")
PG = importlib.import_module(PACKAGE + ".playground")
A = importlib.import_module(PACKAGE + ".math.arithmetic")
Inv = importlib.import_module(PACKAGE + ".invariance")
RR = importlib.import_module(PACKAGE + ".rewrite_rules")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
main_mod = importlib.import_module(PACKAGE + ".main")
D = importlib.import_module(PACKAGE + ".dialogue")

T0 = time.time()
EMPTY = M.EmptyList
TRUE = M.truth_value
FALSE = M.false_value

print("=== TEST 26: FLT n = 4, the descent half ===")
print()

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    line = "    PASS  " if ok else "    FAIL  "
    print(line + name + (("  -- " + detail) if (detail and not ok) else ""))
    return bool(ok)


def is_label(term, label):
    return M.IdentityCompare(term, label)() is TRUE


def head_is(term, label):
    return M.IsPair(term)() is TRUE and is_label(M.Head(term)(), label)


def chain(items):
    out = EMPTY
    for item in reversed(items):
        out = M.Pair(item, out)
    return out


def to_list(c):
    out = []
    while M.IdentityCompare(c, EMPTY)() is FALSE:
        out.append(M.Head(c)())
        c = M.Tail(c)()
    return out


def fact(label, *args):
    return M.Pair(label, chain(list(args)))


def add(a, b):
    return M.Pair(L.ExprAddLabel, M.Pair(a, M.Pair(b, EMPTY)))


def mul(a, b):
    return M.Pair(L.ExprMulLabel, M.Pair(a, M.Pair(b, EMPTY)))


def pw(a, k):
    return M.Pair(L.ExprPowLabel, M.Pair(a, M.Pair(k, EMPTY)))


def ledger_section(t1):
    print("      [%.1fs]" % (time.time() - t1))
    print()


# ---------------------------------------------------------------------------
# [1] boot
# ---------------------------------------------------------------------------

print("[1] Fresh runtime; the two strategy packs; the separating modulus re-discovered")
t1 = time.time()
runtime = runtime_mod.make_fresh_runtime()
namespace = main_mod._runtime_namespace()
pack_engel = runtime.load_pack(os.path.join(REPO, "packs", "engel-strategies.pack.yaml"), namespace)
pack_descent = runtime.load_pack(os.path.join(REPO, "packs", "infinite-descent.pack.yaml"), namespace)
graph = runtime.graph
graph._search_disable_console = TRUE
graph._search_disable_progress_ticker = TRUE
reg = M.FromContextGetConstructors(graph)()


def nat(n):
    """Host int -> machine nat, threading the suite's registry."""
    global reg
    res = M.NatFromRep(M.GMPRep(str(n)), reg)()
    reg = M.Head(M.Tail(res)())()
    return M.Head(res)()


def nv(x):
    rep = M.NatRepOf(x, reg)()
    if M.IdentityCompare(rep, EMPTY)() is TRUE:
        return None
    return int(rep())


def tuple_values(t):
    return [nv(v) for v in to_list(t)]


ZERO = M.Zero
ONE = M.one
TWO = M.two
FOUR = nat(4)

descent_rule_ids = [rid for rid, _ in pack_descent.rule_map.entries]
check("infinite-descent pack carries exactly one schema, infinite_descent", descent_rule_ids == ["infinite_descent"], str(descent_rule_ids))
descent_src = open(os.path.join(REPO, "packs", "infinite-descent.pack.yaml"), encoding="utf-8").read().lower()
check("the pack names no quartic, no parametrisation, no square lemma",
      all(w not in descent_src for w in ("quartic", "fourth", "pythag", "coprime", "square", "x^4", "m^2", "2mn")))
check("the pack states that its schema is authored, not derived", "authored axiom" in descent_src)

# The modulus: the sweep's, not a constant. Same call test18 makes, smaller bound.
bound11 = nat(11)
moduli = chain([TWO, nat(3), FOUR, nat(5)])


def is_odd(x, r):
    return M.NotAtom(A.Divides(TWO, x, r)())()


def every_x(x, r):
    return TRUE


def pair_odd(x, y, r):
    return M.AndAtom(is_odd(x, r), is_odd(y, r))()


# squares of every x against sums of two odd squares -- test18's sweep, bound 11
disc = PG.DiscoverSeparatingModulus(bound11, TWO, every_x, pair_odd, moduli, reg)()
disc_record = M.Head(disc)()
reg = M.Head(M.Tail(disc)())()
check("the sweep finds a separating modulus for squares vs odd square sums", M.IdentityCompare(disc_record, EMPTY)() is FALSE)
MODULUS = M.Head(M.Tail(disc_record)())()
check("  ... and it is 4 (read back from the record, used from here on)", nv(MODULUS) == 4, str(nv(MODULUS)))
ledger_section(t1)

# ---------------------------------------------------------------------------
# [2] the identity procedure on controls
# ---------------------------------------------------------------------------

print("[2] PolynomialIdentityByGrid on controls")
t1 = time.time()
a = M.Char("a")
b = M.Char("b")


def identity(lhs, rhs, variables):
    global reg
    res = PG.PolynomialIdentityByGrid(lhs, rhs, chain(variables), reg)()
    reg = M.Head(M.Tail(res)())()
    record = M.Head(res)()
    parts = to_list(M.Tail(record)())
    return {
        "record": record,
        "degrees": [nv(d) for d in to_list(parts[3])],
        "grid": nv(parts[4]),
        "verdict": parts[5],
        "witness": parts[6],
    }


square_sum = identity(pw(add(a, b), TWO), add(add(pw(a, TWO), mul(TWO, mul(a, b))), pw(b, TWO)), [a, b])
check("(a+b)^2 = a^2 + 2ab + b^2: verdict truth", square_sum["verdict"] is TRUE)
check("  ... record is a PolynomialIdentity record", head_is(square_sum["record"], L.PolynomialIdentityLabel))
check("  ... degree bounds (2, 2) read structurally, grid 3 x 3 = 9 points", square_sum["degrees"] == [2, 2] and square_sum["grid"] == 9, str(square_sum["degrees"]) + " " + str(square_sum["grid"]))

not_identity = identity(pw(add(a, b), TWO), add(pw(a, TWO), pw(b, TWO)), [a, b])
check("(a+b)^2 = a^2 + b^2: verdict false", not_identity["verdict"] is FALSE)
witness = tuple_values(not_identity["witness"])
check("  ... with a witness point where the sides differ: " + str(witness), witness == [1, 1], str(witness))

# The degree-bound trap: a^2 + a and 2a agree at 0 and 1 and differ at 2.
trap = identity(add(pw(a, TWO), a), mul(TWO, a), [a])
check("a^2 + a = 2a: verdict false, witness a = 2", trap["verdict"] is FALSE and tuple_values(trap["witness"]) == [2], str(tuple_values(trap["witness"])))
check("  ... grid had 3 points because the structural bound is 2", trap["degrees"] == [2] and trap["grid"] == 3)
agree = []
for v in (ZERO, ONE):
    env = chain([M.Pair(a, M.Pair(v, EMPTY))])
    lres = PG.EvaluateNatExpr(add(pw(a, TWO), a), env, reg)()
    rres = PG.EvaluateNatExpr(mul(TWO, a), env, M.Head(M.Tail(lres)())())()
    reg = M.Head(M.Tail(rres)())()
    agree.append(M.NatEq(M.Head(lres)(), M.Head(rres)(), reg)() is TRUE)
check("  ... a 2-point grid {0, 1} would have passed it: the grid size is load-bearing", agree == [True, True], str(agree))

refused = identity(M.Pair(L.ExprNegLabel, M.Pair(a, EMPTY)), a, [a])
check("a term outside the fragment (ExprNeg) is refused, verdict []", refused["verdict"] is EMPTY)
ledger_section(t1)

# ---------------------------------------------------------------------------
# [3] the descent's identities, DERIVED
# ---------------------------------------------------------------------------

print("[3] The descent's identities, decided by the grid")
t1 = time.time()
p = M.Char("p")
n = M.Char("n")
x = M.Char("x")

# With m^2 = p + n^2 (p the odd leg squared), the Pythagorean identity
# (m^2 - n^2)^2 + (2mn)^2 = (m^2 + n^2)^2 reads, without subtraction,
#     p^2 + 4 (p + n^2) n^2 = (p + 2 n^2)^2.
pyth_lhs = add(pw(p, TWO), mul(mul(FOUR, add(p, pw(n, TWO))), pw(n, TWO)))
pyth_rhs = pw(add(p, mul(TWO, pw(n, TWO))), TWO)
pyth = identity(pyth_lhs, pyth_rhs, [p, n])
check("p^2 + 4(p + n^2)n^2 = (p + 2n^2)^2 (the Pythagorean square identity, additive form): DERIVED",
      pyth["verdict"] is TRUE)
check("  ... degree bounds (2, 4), grid 3 x 5 = 15 points", pyth["degrees"] == [2, 4] and pyth["grid"] == 15, str(pyth["degrees"]) + " " + str(pyth["grid"]))
print("      every coprime opposite-parity (m, n) therefore yields a Pythagorean triple -- the")
print("      *soundness* direction of the parametrisation is a theorem the machine decided.")

quartic_as_square = identity(pw(x, FOUR), pw(pw(x, TWO), TWO), [x])
check("x^4 = (x^2)^2: DERIVED (so u^4 + v^4 = w^2 is (u^2)^2 + (v^2)^2 = w^2, by substitution)", quartic_as_square["verdict"] is TRUE)
check("  ... degree bound 4, grid 5 points", quartic_as_square["degrees"] == [4] and quartic_as_square["grid"] == 5)
ledger_section(t1)

# ---------------------------------------------------------------------------
# [4] the residue step, DERIVED
# ---------------------------------------------------------------------------

print("[4] The residue step, by exhaustive case analysis modulo the discovered modulus")
t1 = time.time()
m = M.Char("m")

sq_res = PG.ResidueTable(pw(x, TWO), chain([x]), MODULUS, reg)()
reg = M.Head(M.Tail(sq_res)())()
sq_record = M.Head(sq_res)()
sq_parts = to_list(M.Tail(sq_record)())
rows = [(tuple_values(M.Head(row)()), nv(M.Head(M.Tail(row)())())) for row in to_list(sq_parts[3])]
check("ResidueTable of x^2 mod 4 has the four classes", head_is(sq_record, L.ResidueTableLabel) and len(rows) == 4, str(rows))
odd_rows = [r for cls, r in rows if cls[0] % 2 == 1]
check("  ... every odd class squares to 1: odd squares are 1 mod 4 -- DERIVED", odd_rows == [1, 1], str(rows))
check("  ... the image is {0, 1}", sorted(nv(v) for v in to_list(sq_parts[4])) == [0, 1])

# p = x^2 with x odd, so p = 1 (mod 4); the equation p + n^2 = m^2 forces
cong_res = PG.CongruenceClasses(add(ONE, pw(n, TWO)), pw(m, TWO), chain([m, n]), MODULUS, reg)()
reg = M.Head(M.Tail(cong_res)())()
cong_record = M.Head(cong_res)()
cong_parts = to_list(M.Tail(cong_record)())
holding = sorted(tuple_values(t) for t in to_list(cong_parts[4]))
failing = to_list(cong_parts[5])
check("CongruenceClasses of 1 + n^2 = m^2 (mod 4): 16 classes partitioned", head_is(cong_record, L.CongruenceClassesLabel) and len(holding) + len(failing) == 16)
check("  ... the holding classes are exactly m odd, n even: " + str(holding) + " -- DERIVED",
      holding == [[1, 0], [1, 2], [3, 0], [3, 2]], str(holding))
check("  ... so in x^2 + n^2 = m^2 with x odd, m is odd and n is even (the parity split the descent needs)",
      all(cls[0] % 2 == 1 and cls[1] % 2 == 0 for cls in holding))
ledger_section(t1)

# ---------------------------------------------------------------------------
# [5] the parametrised family on data, EVIDENCED
# ---------------------------------------------------------------------------

print("[5] The parametrised family on data (evidence, not proof)")
t1 = time.time()
ODD_LEG_BOUND = 21   # legs of the triples enumerated (odd leg <= 21, even leg <= 24)
EVEN_LEG_BOUND = 24
ROOT_BOUND = 32      # 32^2 > 21^2 + 24^2: every hypotenuse below is in the square table
FAMILY_BOUND = 5     # m <= 5: m^2 + n^2 up to 41 > 32, every such triple is in reach
FACTOR_BOUND = 16    # (a, b) for the coprime-square-factors sweep
# Bounds are small on purpose: every machine addition or product interns a
# new nat, and NatFromRep's index lookup grows with the number of nats
# interned (measured ~0.2 s per operation on a fresh runtime, ~0.6 s after
# two hundred more), so a sweep's cost is quadratic in its size.

# One square table, built once by the machine's Multiply; everything below
# tests squareness by membership (NatEq), never by a root.
root_range = PG.BuildNatRange(ZERO, nat(ROOT_BOUND + 1), reg)()
roots = M.Head(root_range)()
reg = M.Head(M.Tail(root_range)())()
root_list = to_list(roots)
square_of = {}
square_chain = EMPTY
for k in root_list:
    res = A.Multiply(k, k, reg)()
    reg = M.Head(M.Tail(res)())()
    square_of[nv(k)] = M.Head(res)()
    square_chain = M.Pair(M.Head(res)(), square_chain)


def is_square(v):
    return PG.ChainContains(square_chain, v, reg)() is TRUE


def coprime(u, v):
    return A.IsCoprime(u, v, reg)() is TRUE


def even(v):
    return A.Divides(TWO, v, reg)() is TRUE


# -- primitive triples with an even leg, legs <= LEG_BOUND --------------------
odd_legs = [k for k in root_list if 1 <= nv(k) <= ODD_LEG_BOUND and not even(k)]
even_legs = [k for k in root_list if 1 <= nv(k) <= EVEN_LEG_BOUND and even(k)]
triples = []
adds = 0
for odd_leg in odd_legs:
    for even_leg in even_legs:
        if not coprime(odd_leg, even_leg):
            continue
        res = A.Add(square_of[nv(odd_leg)], square_of[nv(even_leg)], reg)()
        reg = M.Head(M.Tail(res)())()
        adds = adds + 1
        s = M.Head(res)()
        if is_square(s):
            hyp = [k for k in root_list if M.NatEq(square_of[nv(k)], s, reg)() is TRUE][0]
            triples.append((odd_leg, even_leg, hyp))
triple_values = sorted((nv(o), nv(e), nv(h)) for o, e, h in triples)
print("      primitive triples with an even leg, odd leg <= %d, even leg <= %d (%d machine additions): %s" % (ODD_LEG_BOUND, EVEN_LEG_BOUND, adds, triple_values))
check("the sweep finds the five primitive triples in range", len(triples) == 5 and (3, 4, 5) in triple_values and (21, 20, 29) in triple_values, str(triple_values))

# -- the family: coprime, opposite parity, n < m <= FAMILY_BOUND --------------
family = []
for mm in root_list:
    if not 1 <= nv(mm) <= FAMILY_BOUND:
        continue
    for nn in root_list:
        if not 1 <= nv(nn) < nv(mm):
            continue
        if not coprime(mm, nn) or even(mm) == even(nn):
            continue
        prod = A.Multiply(mm, nn, reg)()
        reg = M.Head(M.Tail(prod)())()
        twice = A.Add(M.Head(prod)(), M.Head(prod)(), reg)()
        reg = M.Head(M.Tail(twice)())()
        hyp = A.Add(square_of[nv(mm)], square_of[nv(nn)], reg)()
        reg = M.Head(M.Tail(hyp)())()
        family.append({"m": mm, "n": nn, "even_leg": M.Head(twice)(), "hyp": M.Head(hyp)()})
print("      family pairs (m, n), m <= %d: %s" % (FAMILY_BOUND, [(nv(f["m"]), nv(f["n"])) for f in family]))
check("the family has the 6 coprime opposite-parity pairs with m <= 5", len(family) == 6, str(len(family)))

# -- completeness evidence: every triple is hit by a family pair --------------
hits = []
for odd_leg, even_leg, hyp in triples:
    hit = None
    for f in family:
        if M.NatEq(f["hyp"], hyp, reg)() is FALSE or M.NatEq(f["even_leg"], even_leg, reg)() is FALSE:
            continue
        # the odd leg: x + n^2 = m^2, one machine addition
        res = A.Add(odd_leg, square_of[nv(f["n"])], reg)()
        reg = M.Head(M.Tail(res)())()
        if M.NatEq(M.Head(res)(), square_of[nv(f["m"])], reg)() is TRUE:
            hit = f
            break
    hits.append((nv(odd_leg), nv(even_leg), nv(hyp), None if hit is None else (nv(hit["m"]), nv(hit["n"]))))
print("      triple -> (m, n): " + str(hits))
check("every primitive triple with an even leg in range is some (m^2 - n^2, 2mn, m^2 + n^2): EVIDENCED on 5 instances",
      len(hits) == 5 and all(h[3] is not None for h in hits))
beyond = [h for h in hits if h[2] > 17]
check("  ... including the %d instances beyond the bound (r <= 17) the first three were drawn from" % len(beyond),
      len(beyond) == 2 and all(h[3] is not None for h in beyond))
print("      (the parametrisation is a human-stated candidate here; the machine neither discovered")
print("       nor derived it -- its completeness direction is what [8] shows to be out of reach)")

# -- coprime factors of a square are squares, on the sweep ---------------------
factor_pairs = [k for k in root_list if 1 <= nv(k) <= FACTOR_BOUND]
square_products = []
mults = 0
for u in factor_pairs:
    for v in factor_pairs:
        if nv(v) < nv(u):
            continue
        res = A.Multiply(u, v, reg)()
        reg = M.Head(M.Tail(res)())()
        mults = mults + 1
        if is_square(M.Head(res)()):
            square_products.append((u, v))
coprime_cases = [(u, v) for u, v in square_products if coprime(u, v)]
coprime_ok = all(is_square(u) and is_square(v) for u, v in coprime_cases)
non_coprime_counter = [(nv(u), nv(v)) for u, v in square_products if not coprime(u, v) and not (is_square(u) and is_square(v))]
print("      %d machine products; %d square products, %d of them coprime pairs" % (mults, len(square_products), len(coprime_cases)))
check("coprime a, b with ab a square are both squares: EVIDENCED on %d instances" % len(coprime_cases), coprime_ok and len(coprime_cases) >= 6)
check("  ... and coprimality is load-bearing: non-coprime counterexamples exist, e.g. " + str(non_coprime_counter[:3]),
      len(non_coprime_counter) > 0 and (2, 8) in non_coprime_counter)

# -- the measure drops along the would-be descent -----------------------------
# A solution with parameters (a, b) has z = (a^2 + b^2)^2 + (2ab)^2; the smaller
# solution it yields has w^2 = a^2 + b^2. On every family pair, a^2 + b^2 < z.
drops = []
for f in family:
    m_sq = A.Multiply(f["hyp"], f["hyp"], reg)()          # (a^2 + b^2)^2
    reg = M.Head(M.Tail(m_sq)())()
    n_sq = A.Multiply(f["even_leg"], f["even_leg"], reg)()  # (2ab)^2
    reg = M.Head(M.Tail(n_sq)())()
    z = A.Add(M.Head(m_sq)(), M.Head(n_sq)(), reg)()
    reg = M.Head(M.Tail(z)())()
    drops.append(M.NatLess(f["hyp"], M.Head(z)(), reg)() is TRUE)
check("the measure of the would-be smaller solution is below z on every family pair: EVIDENCED (6 instances)", all(drops) and len(drops) == 6)
ledger_section(t1)

# ---------------------------------------------------------------------------
# [6] the descent skeleton, DERIVED conditionally
# ---------------------------------------------------------------------------

print("[6] The descent skeleton: a Checker-B verified derivation from four hypotheses")
t1 = time.time()
proc = M.Char("descent")   # the process whose states are the primitive solutions
meas = M.Char("z")
hyps = [
    fact(L.MonovariantLabel, proc, meas),
    fact(L.AllMovesDecreaseLabel, proc, meas),
    fact(L.BoundedBelowLabel, meas, ZERO),
    fact(L.EveryStateMovesLabel, proc),
]
start = P.Knowledge(chain(hyps))()
goal = P.Knowledge(chain([fact(L.NoStatesLabel, proc)]))()
rules = runtime.flat_rules()
depth = nat(3)
search = D.SearchKnowledgeDerivation(start, goal, rules, depth, reg)()
derivation = M.Head(search)()
reg = M.Head(M.Tail(search)())()
check("a derivation from the four hypotheses to NoStates(descent) is found", M.IdentityCompare(derivation, EMPTY)() is FALSE)
steps = to_list(P.DerivationSteps(derivation, reg)())
step_ids = []
for step in steps:
    rule = P.ActionRule(P.StepAction(step, reg)())()
    rid = "?"
    for pk in (pack_engel, pack_descent):
        for r, ro in pk.rule_map.entries:
            if ro() is rule:
                rid = r
    step_ids.append(rid)
    print("      step " + str(len(step_ids)) + ": " + rid + "  =>  " + D.render_fact_list(P.KnowledgeFacts(P.StepNext(step, reg)())(), reg))
check("  ... in two steps: monovariant_terminates (Engel), then infinite_descent", step_ids == ["monovariant_terminates", "infinite_descent"], str(step_ids))
verdict = CB.VerifyDerivation(derivation, start, goal, rules, reg)()
check("Checker B verifies it (DerivationVerifiedLabel)", head_is(verdict, L.DerivationVerifiedLabel))
wrong_goal = P.Knowledge(chain([fact(L.NoStatesLabel, meas)]))()
wrong = CB.VerifyDerivation(derivation, start, wrong_goal, rules, reg)()
check("  ... and rejects the same derivation against a different goal (GoalMismatchLabel)", head_is(wrong, L.GoalMismatchLabel))
start_without = P.Knowledge(chain(hyps[:3]))()
search_without = D.SearchKnowledgeDerivation(start_without, goal, rules, depth, reg)()
check("without EveryStateMoves(descent) no derivation exists: the conclusion rests on that hypothesis",
      M.IdentityCompare(M.Head(search_without)(), EMPTY)() is TRUE)
print("      EveryStateMoves(descent) says: from every primitive solution of x^4 + y^4 = z^2 a smaller one")
print("      can be built. That is the parametrisation (completeness direction) plus coprime-square-")
print("      factors plus the coprimality bookkeeping -- the three EVIDENCED items of [5]. None is derived.")
ledger_section(t1)

# ---------------------------------------------------------------------------
# [7] the ledger
# ---------------------------------------------------------------------------

print("[7] The promotion ledger")
t1 = time.time()
ledger = PL.EmptyPromotionLedger(reg)()
check("a fresh ledger is at version 0", M.IdentityCompare(PL.PromotionLedgerVersion(ledger)(), ZERO)() is TRUE)
baseline_cost = P.ProofCost(ZERO, ZERO, ZERO, ZERO)()
refusals = []
for name in ("pythagorean_parametrisation_completeness", "coprime_square_factors_are_squares", "descent_measure_decreases"):
    cand_start = M.Atom()
    cand_goal = M.Atom()
    candidate = Eval.CandidateMacro(M.Char(name), cand_start, cand_goal, EMPTY)()
    evidence = Eval.EvaluateCandidateProof(candidate, cand_start, cand_goal, EMPTY, reg)()
    promotion = PL.SubmitCandidateForPromotion(ledger, candidate, L.ProofSchemaPromotionLabel, cand_start, cand_goal, baseline_cost, EMPTY, EMPTY, EMPTY, reg)()
    refusals.append((name, head_is(evidence, L.GoalMismatchLabel), head_is(promotion, L.PromotionRejectedLabel)))
    print("      " + name + ": evaluator " + ("GoalMismatch" if refusals[-1][1] else "?") + ", ledger " + ("PromotionRejected" if refusals[-1][2] else "?"))
check("the three sweep-evidenced candidates carry no derivation and are refused by the gate", all(r[1] and r[2] for r in refusals))
print("      the skeleton derivation of [6] is not submitted: its receipt certifies the implication")
print("      (four hypotheses => NoStates), not the theorem; one hypothesis is the theorem's content.")
check("ledger version stays 0", M.NatEq(PL.PromotionLedgerVersion(ledger)(), ZERO, reg)() is TRUE)
ledger_section(t1)

# ---------------------------------------------------------------------------
# [8] the obstruction, demonstrated
# ---------------------------------------------------------------------------

print("[8] The obstruction: what the machinery cannot express")
t1 = time.time()


def pattern_variables(term, acc):
    if P.IsVarPattern(term)() is TRUE:
        name = M.Head(M.Tail(term)())()
        if not any(M.Compare(name, seen)() is TRUE for seen in acc):
            acc.append(name)
        return acc
    if M.IsPair(term)() is TRUE:
        pattern_variables(M.Head(term)(), acc)
        pattern_variables(M.Tail(term)(), acc)
    return acc


introducing = []
rule_count = 0
for rule in to_list(rules):
    if P.ReplacementIsFactList(rule)() is FALSE:
        continue
    rule_count = rule_count + 1
    premise_vars = pattern_variables(P.RulePremises(rule)(), [])
    replacement_vars = pattern_variables(P.RuleReplacement(rule)(), [])
    fresh = [v for v in replacement_vars if not any(M.Compare(v, u)() is TRUE for u in premise_vars)]
    if fresh:
        introducing.append(rule)
check("no loaded schema (%d) has a replacement variable unbound by its premises: no rule can introduce a witness" % rule_count,
      rule_count >= 14 and not introducing, str(len(introducing)))
print("      so the m, n of a parametrisation and the u, v, w of a smaller solution cannot enter a derivation:")
print("      existential witness introduction is absent from the knowledge-rewrite format -- MISSING")

default_rules = RR.build_default_rewrite_rule_chain()
symbolic = Inv.RewriteEquals(pyth_lhs, pyth_rhs, default_rules, reg)()
check("the symbolic rewrite walker (distributivity + associativity, fuel 9) is stuck on the identity [3] decided",
      symbolic is FALSE)
print("      commutative-ring normalisation is absent; the grid procedure is the only route to identities -- stated")

absent = [name for name in ("Subtract", "Minus", "Sqrt", "IntegerSqrt", "Factor", "Factorise", "PrimeFactors", "Factorization") if getattr(A, name, None) is not None]
check("the arithmetic layer has no subtraction, root or factorisation edge", not absent, str(absent))
print("      coprime-square-factors needs unique factorisation; nothing here factors -- MISSING")
has_less_rule = any(
    any(head_is(f, L.NatLessLabel) for f in to_list(P.RuleReplacement(rule)()))
    for rule in to_list(rules) if P.ReplacementIsFactList(rule)() is TRUE
)
check("no loaded schema concludes a NatLess fact: the decrease of the measure cannot be derived here, only evidenced", not has_less_rule)
ledger_section(t1)

# ---------------------------------------------------------------------------
# [9] the account
# ---------------------------------------------------------------------------

print("[9] The account")
print("      DERIVED   : Pythagorean square identity (additive form); x^4 = (x^2)^2;")
print("                  odd squares are 1 mod 4; 1 + n^2 = m^2 (mod 4) forces m odd, n even;")
print("                  Terminates & EveryStateMoves => NoStates, 2 steps, Checker-B receipt (conditional)")
print("      EVIDENCED : parametrisation completeness (5 triples, 2 beyond the first bound);")
print("                  coprime factors of a square are squares (%d pairs; non-coprime counterexamples);" % len(coprime_cases))
print("                  the measure drops (6 family pairs)  -- all three refused by the ledger")
print("      AUTHORED  : the infinite-descent strategy schema (one rule, declared as an axiom)")
print("      MISSING   : witness introduction (rule format); unique factorisation (no factoring edge);")
print("                  ring normalisation (walker stuck); an inequality calculus (no schema concludes <)")
print("      Done-definition reached: 2 (partial) -- the theorem is reduced to EveryStateMoves(descent),")
print("      whose discharge needs exactly the MISSING items; ledger version 0; nothing promoted.")
print()

# ---------------------------------------------------------------------------

print("=== TEST 26 RESULTS ===")
passed = 0
for _name, ok, _detail in RESULTS:
    if ok:
        passed = passed + 1
failed = len(RESULTS) - passed
for name, ok, detail in RESULTS:
    if not ok:
        print("  FAILED: " + name + (("  -- " + detail) if detail else ""))
print("  Checks passed: " + str(passed) + "/" + str(len(RESULTS)))
print("  Total time:    %.3fs" % (time.time() - T0))
print()
if failed:
    print("=== TEST 26 FAILED ===")
    sys.exit(1)
print("=== TEST 26 COMPLETE ===")
print("Boundary: the n = 4 theorem is not claimed. What is claimed is the reduction above,")
print("each step labelled derived, evidenced, authored or missing.")
