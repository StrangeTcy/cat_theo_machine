# ============================================================
# TEST 20: FLT n = 3 residue obstruction over the Eisenstein
# structure, discovered live
#
# No pack, no cubic rules, no solution written anywhere. This
# suite loads nothing and hand-writes no mathematics:
#
#   [2] A parameterized sweep - the exponent and both domain
#       filters are parameters, not constants - is run for every
#       candidate modulus in 2..9 over the domain of integers
#       coprime to 3. The machine's own flags show that no
#       modulus below 9 separates the cube image from the image
#       of sums of two such cubes, and that 9 does: the
#       discovered separating modulus is read off those flags.
#       The same machinery, instantiated with power 2 and an
#       oddness filter, rediscovers the modulus-4 square
#       obstruction of TEST 18, so the sweep is specific to no
#       exponent.
#   [3] The machine's own arithmetic runs the complete residue
#       case analysis modulo 9: all nine classes are cubed, the
#       unit classes are separated, and the unit cube image is
#       disjoint from the unit pair-sum image. The first case of
#       the n = 3 problem is closed by that computation alone.
#   [4] The Eisenstein ring is built as generic structure:
#       elements are pairs of signed coordinates, multiplication
#       reduces through the relation omega^2 + omega + 1 = 0
#       taken as parameters, and the norm is DERIVED as the
#       product of an element with its conjugate. The machine
#       verifies that the omega-coordinate of that product
#       vanishes and that the norm is multiplicative on a
#       witness set spanning the coordinate range. The same
#       machinery under a different relation derives the
#       Gaussian norm, so nothing here is specific to cubes.
#   [5] The machine links its own two discoveries: the norm of
#       1 - omega comes out 3, and 3 * 3 = 9 is exactly the
#       modulus the sweep found.
#   [6] The discovery record names its own candidate lemma and
#       the promotion ledger is asked to promote it. It refuses,
#       because a ledger entry needs a Checker B receipt over a
#       machine-verified derivation, and a sweep discovery
#       carries none.
#
# What is NOT derived and not claimed here: unique factorization
# in the Eisenstein ring, the infinite descent, and the full
# n = 3 theorem.
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
from cat_theo_machine.prettyprinting import WholeText
from cat_theo_machine.runtime import make_fresh_runtime
from cat_theo_machine import evaluator as Eval
from cat_theo_machine import promotion_ledger as Ledger
from cat_theo_machine import proof as P

t0 = time.time()
section_t = t0

def mark(label):
    global section_t
    now = time.time()
    print("    [%s: %.1fs]" % (label, now - section_t))
    section_t = now

print("=== TEST 20: FLT n = 3 residue obstruction over the Eisenstein structure, discovered live ===")
print()

# --- [1] a bare machine; nothing is loaded -------------------------------
print("[1] Fresh runtime, no packs loaded, no cubic rules...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
graph._search_disable_console = M.truth_value
graph._search_disable_progress_ticker = M.truth_value
print("    Machine is bare; every number below is computed, none is written in.")
print()

# --- machine-value conveniences (representation conventions only) --------
def nat(text, reg):
    pair = M.NatFromRep(M.GMPRep(text), reg)()
    return M.Head(pair)(), M.Head(M.Tail(pair)())()

def whole_pair(a_sign, a_mag, b_sign, b_mag, reg):
    """Build Pair(Whole, Whole) from sign tags (Zero = non-negative, one = negative)."""
    left_pair = A.WholeFromSignedNat(a_sign, a_mag, reg)()
    left = M.Head(left_pair)()
    reg1 = M.Head(M.Tail(left_pair)())()
    right_pair = A.WholeFromSignedNat(b_sign, b_mag, reg1)()
    right = M.Head(right_pair)()
    reg2 = M.Head(M.Tail(right_pair)())()
    return M.Pair(left, M.Pair(right, M.EmptyList)), reg2

def whole_text(x, reg):
    return M.Head(WholeText(x, reg)())()

def whole_value(x, reg):
    """Reporting-only canonical value of a Whole as a Python int (display use
    only; every assertion in this suite compares machine values)."""
    left = M.NatRepOf(M.WholeLeft(x, reg)(), reg)()
    right = M.NatRepOf(M.WholeRight(x, reg)(), reg)()
    lv = int(left()) if M.IdentityCompare(left, M.EmptyList)() is M.false_value else 0
    rv = int(right()) if M.IdentityCompare(right, M.EmptyList)() is M.false_value else 0
    return lv - rv

def record_disjoint(record):
    return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()

def record_modulus(record):
    return M.Head(M.Tail(record)())()

def record_unary_image(record):
    return M.Head(M.Tail(M.Tail(record)())())()

def record_pair_image(record):
    return M.Head(M.Tail(M.Tail(M.Tail(record)())())())()

# --- [2] the parameterized sweep discovers the separating modulus --------
print("[2] Parameterized sweep: cubes over the coprime-to-3 domain, moduli 2..9...")

bound, reg = nat("9", registry)
power, reg = nat("3", reg)
filter_prime, reg = nat("3", reg)

def coprime_unary(x, reg):
    return A.IsCoprime(x, filter_prime, reg)()

def coprime_pair(x, y, reg):
    ok_x = A.IsCoprime(x, filter_prime, reg)()
    ok_y = A.IsCoprime(y, filter_prime, reg)()
    return M.AndAtom(ok_x, ok_y)()

# One sweep per candidate modulus; the disjointness flag is the machine's.
flags = []
records = []
for k in range(2, 10):
    m_k, reg = nat(str(k), reg)
    sweep_res = PG.RunPlaygroundFilteredPowerSweep(
        bound, m_k, power, coprime_unary, coprime_pair, reg
    )()
    record_k = M.Head(sweep_res)()
    reg = M.Head(M.Tail(sweep_res)())()
    records.append((k, m_k, record_k))
    flags.append(record_disjoint(record_k))

for idx, k in enumerate(range(2, 10)):
    if k < 9:
        assert flags[idx] is M.false_value, "modulus %d must not separate the cube images" % k
    else:
        assert flags[idx] is M.truth_value, "modulus 9 must separate the cube images"
print("    Every modulus in 2..9 swept; only 9 separates the images.")

# The discovered modulus is the first flag that came out true, read off the
# machine's own sweep flags - not a constant chosen here.
discovered_index = None
for idx in range(len(flags)):
    if flags[idx] is M.truth_value:
        discovered_index = idx
        break
assert discovered_index == 7, "the first separating modulus must sit at index 7 (modulus 9)"
discovered_modulus = records[discovered_index][1]
discovered_record = records[discovered_index][2]
discovered_modulus_value = M.NatRepOf(discovered_modulus, reg)()()
assert M.NatEq(discovered_modulus, M.nine, reg)() is M.truth_value, (
    "the discovered separating modulus must be 9, the machine found %d" % discovered_modulus_value
)
unary_image = record_unary_image(discovered_record)
pair_image = record_pair_image(discovered_record)
print("    Discovered separating modulus: %d" % discovered_modulus_value)

# The discovered images, read back as machine-checked set facts.
len_res = PG.ChainLength(unary_image, reg)()
unary_size = M.Head(len_res)()
reg = M.Head(M.Tail(len_res)())()
len_res = PG.ChainLength(pair_image, reg)()
pair_size = M.Head(len_res)()
reg = M.Head(M.Tail(len_res)())()
assert M.NatEq(unary_size, M.two, reg)() is M.truth_value, "the unit cube image must hold two classes"
assert M.NatEq(pair_size, M.three, reg)() is M.truth_value, "the unit pair-sum image must hold three classes"

for text in ("1", "8"):
    residue, reg = nat(text, reg)
    assert PG.ChainContains(unary_image, residue, reg)() is M.truth_value, (
        "the unit cube image must contain %s" % text
    )
for text in ("0", "2", "7"):
    residue, reg = nat(text, reg)
    assert PG.ChainContains(pair_image, residue, reg)() is M.truth_value, (
        "the unit pair-sum image must contain %s" % text
    )
for text in ("0", "2", "3", "4", "5", "6", "7"):
    residue, reg = nat(text, reg)
    assert PG.ChainContains(unary_image, residue, reg)() is M.false_value, (
        "the unit cube image must not contain %s" % text
    )
print("    Unit cube image: {1, 8}; unit pair-sum image: {0, 2, 7}; disjoint.")
print()

mark("[2] sweep+discovery")
# --- [2b] the same machinery, power 2, oddness filter: TEST 18's modulus -
print("[2b] Same sweep with power 2 and an odd-pair filter (TEST 18's instance)...")

def always_unary(x, reg):
    return M.truth_value

odd_two_nat, reg = nat("2", reg)
odd_one_nat, reg = nat("1", reg)

def odd_pair_pred(x, y, reg):
    rx = A.Modulo(x, odd_two_nat, reg)()
    rem_x = M.Head(rx)()
    r1 = M.Head(M.Tail(rx)())()
    ry = A.Modulo(y, odd_two_nat, r1)()
    rem_y = M.Head(ry)()
    r2 = M.Head(M.Tail(ry)())()
    return M.AndAtom(
        M.NatEq(rem_x, odd_one_nat, r2)(), M.NatEq(rem_y, odd_one_nat, r2)()
    )()

power_two, reg = nat("2", reg)

def chain_of_nats(texts, reg):
    out = M.EmptyList
    cur_reg = reg
    for text in reversed(texts):
        value, cur_reg = nat(text, cur_reg)
        out = M.Pair(value, out)
    return out, cur_reg

moduli_small, reg = chain_of_nats([str(k) for k in range(2, 6)], reg)
redisc_res = PG.DiscoverSeparatingModulus(
    bound, power_two, always_unary, odd_pair_pred, moduli_small, reg
)()
redisc_record = M.Head(redisc_res)()
reg = M.Head(M.Tail(redisc_res)())()
assert M.IdentityCompare(redisc_record, M.EmptyList)() is M.false_value, (
    "some modulus in 2..5 must separate the square images"
)
redisc_modulus = record_modulus(redisc_record)
redisc_value = M.NatRepOf(redisc_modulus, reg)()()
assert redisc_value == 4, "the parameterized sweep must rediscover modulus 4, found %d" % redisc_value
redisc_unary = record_unary_image(redisc_record)
redisc_pair = record_pair_image(redisc_record)
for text in ("0", "1"):
    residue, reg = nat(text, reg)
    assert PG.ChainContains(redisc_unary, residue, reg)() is M.truth_value
for text in ("2",):
    residue, reg = nat(text, reg)
    assert PG.ChainContains(redisc_pair, residue, reg)() is M.truth_value
for text in ("0", "1", "3"):
    residue, reg = nat(text, reg)
    assert PG.ChainContains(redisc_pair, residue, reg)() is M.false_value
print("    Rediscovered modulus 4 with square image {0,1} vs odd pair-sum image {2}:")
print("    the sweep is generic in the exponent, not written for cubes.")
print()

mark("[2b] generality")
# --- [3] the complete residue case analysis, run by machine arithmetic ---
print("[3] Cube residues modulo 9, all nine residue classes, machine arithmetic...")

residue_nats = {}
for r in range(9):
    r_nat, reg = nat(str(r), reg)
    residue_nats[r] = r_nat
nine_nat, reg = nat("9", reg)
three_nat, reg = nat("3", reg)

def cube_mod(x, mod_nat, reg):
    sq_pair = A.Multiply(x, x, reg)()
    sq = M.Head(sq_pair)()
    r1 = M.Head(M.Tail(sq_pair)())()
    cu_pair = A.Multiply(sq, x, r1)()
    cu = M.Head(cu_pair)()
    r2 = M.Head(M.Tail(cu_pair)())()
    mod_pair = A.Modulo(cu, mod_nat, r2)()
    return M.Head(mod_pair)(), M.Head(M.Tail(mod_pair)())()

unit_classes = []
nonunit_classes = []
for r in range(9):
    r_nat = residue_nats[r]
    cube, reg = cube_mod(r_nat, nine_nat, reg)
    if A.IsCoprime(r_nat, three_nat, reg)() is M.truth_value:
        unit_classes.append((r_nat, cube))
    else:
        nonunit_classes.append((r_nat, cube))

assert len(unit_classes) == 6, "exactly six residue classes are coprime to 3"
assert len(nonunit_classes) == 3, "exactly three residue classes are divisible by 3"
for r_nat, cube in nonunit_classes:
    assert M.NatEq(cube, M.Zero, reg)() is M.truth_value, (
        "a class divisible by 3 must cube to 0 mod 9"
    )
one_residue = residue_nats[1]
eight_residue = residue_nats[8]
for r_nat, cube in unit_classes:
    assert M.OrAtom(
        M.NatEq(cube, one_residue, reg)(), M.NatEq(cube, eight_residue, reg)()
    )() is M.truth_value, "a unit class must cube to 1 or 8 mod 9"

# Every sum of two unit cubes, machine-computed, is 0, 2 or 7 - and all three
# classes occur.
sum_witnesses = {"0": False, "2": False, "7": False}
for r_nat, cube_r in unit_classes:
    for s_nat, cube_s in unit_classes:
        add_pair = A.Add(cube_r, cube_s, reg)()
        s = M.Head(add_pair)()
        reg = M.Head(M.Tail(add_pair)())()
        s_mod_pair = A.Modulo(s, nine_nat, reg)()
        s_mod = M.Head(s_mod_pair)()
        reg = M.Head(M.Tail(s_mod_pair)())()
        for text in ("0", "2", "7"):
            if M.NatEq(s_mod, residue_nats[int(text)], reg)() is M.truth_value:
                sum_witnesses[text] = True
        for text in ("1", "3", "4", "5", "6", "8"):
            assert M.NatEq(s_mod, residue_nats[int(text)], reg)() is M.false_value, (
                "a unit pair-sum may not be %s mod 9" % text
            )
assert all(sum_witnesses.values()), "all three unit pair-sum classes must occur: %s" % sum_witnesses

# Disjointness, machine-checked over the cross product of the two images.
for u_text in ("1", "8"):
    u = residue_nats[int(u_text)]
    for s_text in ("0", "2", "7"):
        s = residue_nats[int(s_text)]
        assert M.NatEq(u, s, reg)() is M.false_value, (
            "unit cube %s may not equal a unit pair-sum %s" % (u_text, s_text)
        )
print("    All nine classes analysed: unit cubes are 1 or 8, unit pair-sums are")
print("    0, 2 or 7, and the two images are disjoint. In a supposed solution")
print("    x^3 + y^3 = z^3 with all of x, y, z coprime to 3, the left side is a")
print("    unit pair-sum and the right side a unit cube, and no residue class")
print("    is both. The first case is closed by the machine's own arithmetic.")
print()

mark("[3] residue analysis")
# --- [4] the Eisenstein ring as generic structure -------------------------
print("[4] The ring, generically: relation as parameters, norm derived...")

# Relation omega^2 = p + q*omega with Whole coefficients. The integers -1
# are built from machine nats through the sign convention; the relation is
# the ontology of the structure, not a conclusion about any problem.
neg_one_pair = A.WholeFromSignedNat(M.one, M.one, registry)()
p_coeff = M.Head(neg_one_pair)()
reg = M.Head(M.Tail(neg_one_pair)())()
neg_one_pair = A.WholeFromSignedNat(M.one, M.one, reg)()
q_coeff = M.Head(neg_one_pair)()
reg = M.Head(M.Tail(neg_one_pair)())()

zero_whole_pair = M.Whole(M.Zero, M.Zero, reg)()
zero_whole = M.Head(zero_whole_pair)()
reg = M.Head(M.Tail(zero_whole_pair)())()
one_whole_pair = M.Whole(odd_one_nat, M.Zero, reg)()
one_whole = M.Head(one_whole_pair)()
reg = M.Head(M.Tail(one_whole_pair)())()
neg_one_whole_pair = A.WholeNegate(one_whole, reg)()
neg_one_whole = M.Head(neg_one_whole_pair)()
reg = M.Head(M.Tail(neg_one_whole_pair)())()

# omega itself: (0, 1).
omega, reg = whole_pair(M.Zero, M.Zero, M.Zero, odd_one_nat, reg)

# omega^2, computed by the generic multiplication, must reduce to -1 - omega.
omega_sq_res = A.RingMultiply(omega, omega, p_coeff, q_coeff, reg)()
omega_sq = M.Head(omega_sq_res)()
reg = M.Head(M.Tail(omega_sq_res)())()
omega_sq_const = M.Head(omega_sq)()
omega_sq_omega = M.Head(M.Tail(omega_sq)())()
assert A.WholeEqual(omega_sq_const, neg_one_whole, reg)() is M.truth_value, (
    "omega^2 must reduce to constant coordinate -1"
)
assert A.WholeEqual(omega_sq_omega, neg_one_whole, reg)() is M.truth_value, (
    "omega^2 must reduce to omega coordinate -1"
)

# And the relation itself, verified: omega^2 + omega + 1 = 0.
rel_res = A.RingAdd(omega_sq, omega, reg)()
rel_partial = M.Head(rel_res)()
reg = M.Head(M.Tail(rel_res)())()
one_element, reg = whole_pair(M.Zero, odd_one_nat, M.Zero, M.Zero, reg)
rel_res = A.RingAdd(rel_partial, one_element, reg)()
rel_total = M.Head(rel_res)()
reg = M.Head(M.Tail(rel_res)())()
assert A.WholeIsZero(M.Head(rel_total)(), reg)() is M.truth_value, (
    "omega^2 + omega + 1 must have zero constant coordinate"
)
assert A.WholeIsZero(M.Head(M.Tail(rel_total)())(), reg)() is M.truth_value, (
    "omega^2 + omega + 1 must have zero omega coordinate"
)
print("    Machine computed omega^2 = %s and verified omega^2 + omega + 1 = 0."
      % whole_text(omega_sq_const, reg))

# Norm via conjugate product; the vanishing omega coordinate is checked here.
# Norms are memoized on the element's coordinate reps so repeated elements
# are not re-derived; every derivation below is a machine computation.
norm_memo = {}

def derived_norm(element, reg):
    a = M.Head(element)()
    b = M.Head(M.Tail(element)())()
    rep_a = M.NatRepOf(M.WholeLeft(a, reg)(), reg)()
    rep_b = M.NatRepOf(M.WholeRight(a, reg)(), reg)()
    key_a = (rep_a(), rep_b())
    rep_c = M.NatRepOf(M.WholeLeft(b, reg)(), reg)()
    rep_d = M.NatRepOf(M.WholeRight(b, reg)(), reg)()
    key = (key_a, (rep_c(), rep_d()))
    if key in norm_memo:
        return norm_memo[key], reg
    norm_res = A.RingNorm(element, p_coeff, q_coeff, reg)()
    product = M.Head(norm_res)()
    reg1 = M.Head(M.Tail(norm_res)())()
    const = M.Head(product)()
    omega_coord = M.Head(M.Tail(product)())()
    assert A.WholeIsZero(omega_coord, reg1)() is M.truth_value, (
        "the omega coordinate of x * conjugate(x) must vanish"
    )
    norm_memo[key] = const
    return const, reg1

# N(1 + omega): a unit of the ring.
unit_element, reg = whole_pair(M.Zero, odd_one_nat, M.Zero, odd_one_nat, reg)
norm_unit, reg = derived_norm(unit_element, reg)
assert A.WholeEqual(norm_unit, one_whole, reg)() is M.truth_value, (
    "the derived norm of 1 + omega must be 1"
)

# N(1 - omega): the prime over 3. This value is computed, never written in.
lambda_element, reg = whole_pair(M.Zero, odd_one_nat, M.one, odd_one_nat, reg)
norm_lambda, reg = derived_norm(lambda_element, reg)
three_whole_pair = M.Whole(three_nat, M.Zero, reg)()
three_whole = M.Head(three_whole_pair)()
reg = M.Head(M.Tail(three_whole_pair)())()
assert A.WholeEqual(norm_lambda, three_whole, reg)() is M.truth_value, (
    "the derived norm of 1 - omega must be 3, machine computed %s"
    % whole_text(norm_lambda, reg)
)
print("    Derived norm of 1 - omega: %s (via conjugate product, no formula written)."
      % whole_text(norm_lambda, reg))

# (1 - omega)^2 = -3*omega, computed by the generic multiplication.
lambda_sq_res = A.RingMultiply(lambda_element, lambda_element, p_coeff, q_coeff, reg)()
lambda_sq = M.Head(lambda_sq_res)()
reg = M.Head(M.Tail(lambda_sq_res)())()
lambda_sq_const = M.Head(lambda_sq)()
lambda_sq_omega = M.Head(M.Tail(lambda_sq)())()
assert A.WholeIsZero(lambda_sq_const, reg)() is M.truth_value, (
    "(1 - omega)^2 must have zero constant coordinate"
)
neg_three_pair = A.WholeFromSignedNat(M.one, three_nat, reg)()
neg_three = M.Head(neg_three_pair)()
reg = M.Head(M.Tail(neg_three_pair)())()
assert A.WholeEqual(lambda_sq_omega, neg_three, reg)() is M.truth_value, (
    "(1 - omega)^2 must have omega coordinate -3"
)
norm_lambda_sq, reg = derived_norm(lambda_sq, reg)
nine_whole_pair = M.Whole(nine_nat, M.Zero, reg)()
nine_whole = M.Head(nine_whole_pair)()
reg = M.Head(M.Tail(nine_whole_pair)())()
assert A.WholeEqual(norm_lambda_sq, nine_whole, reg)() is M.truth_value, (
    "the derived norm of (1 - omega)^2 must be 9"
)
print("    Machine computed (1 - omega)^2 with omega coordinate %d and norm %d."
      % (whole_value(lambda_sq_omega, reg), whole_value(norm_lambda_sq, reg)))

# Multiplicativity of the derived norm, machine-verified on a witness set
# spanning the coordinate range -2..2 (zero, units, negatives, the prime,
# and mixed-coordinate elements), as ordered pairs.
def coord(sign, mag_text, reg):
    mag, reg = nat(mag_text, reg)
    w_pair = A.WholeFromSignedNat(sign, mag, reg)()
    return M.Head(w_pair)(), M.Head(M.Tail(w_pair)())()

E = {}
E["0"], reg = coord(M.Zero, "0", reg)
E["1"], reg = coord(M.Zero, "1", reg)
E["-1"], reg = coord(M.one, "1", reg)
E["2"], reg = coord(M.Zero, "2", reg)
E["-2"], reg = coord(M.one, "2", reg)

def element(a_key, b_key):
    return M.Pair(E[a_key], M.Pair(E[b_key], M.EmptyList))

witness_pairs = [
    (("1", "0"), ("1", "0")),
    (("1", "0"), ("-1", "0")),
    (("-1", "0"), ("-1", "0")),
    (("0", "1"), ("0", "1")),
    (("0", "1"), ("0", "-1")),
    (("1", "-1"), ("1", "-1")),
    (("1", "-1"), ("0", "1")),
    (("0", "1"), ("1", "-1")),
    (("2", "0"), ("2", "0")),
    (("-2", "0"), ("-2", "0")),
    (("1", "1"), ("1", "1")),
    (("2", "1"), ("-1", "2")),
    (("-2", "-1"), ("1", "2")),
]

checked = 0
for (a_key, b_key), (c_key, d_key) in witness_pairs:
    x = element(a_key, b_key)
    y = element(c_key, d_key)
    prod_res = A.RingMultiply(x, y, p_coeff, q_coeff, reg)()
    prod = M.Head(prod_res)()
    reg = M.Head(M.Tail(prod_res)())()
    norm_xy, reg = derived_norm(prod, reg)
    norm_x, reg = derived_norm(x, reg)
    norm_y, reg = derived_norm(y, reg)
    prod_norms_pair = M.WholeMultiply(norm_x, norm_y, reg)()
    prod_norms = M.Head(prod_norms_pair)()
    reg = M.Head(M.Tail(prod_norms_pair)())()
    assert A.WholeEqual(norm_xy, prod_norms, reg)() is M.truth_value, (
        "the derived norm must be multiplicative on every witness pair"
    )
    checked += 1
print("    Multiplicativity N(x*y) = N(x)*N(y) machine-verified on %d ordered pairs" % checked)
print("    spanning the coordinate range -2..2.")

# The same machinery under a different relation derives that ring's norm,
# so the scaffolding is specific to no ring.
gauss_p_pair = A.WholeFromSignedNat(M.one, odd_one_nat, reg)()
gauss_p = M.Head(gauss_p_pair)()
reg = M.Head(M.Tail(gauss_p_pair)())()
gauss_q_pair = M.Whole(M.Zero, M.Zero, reg)()
gauss_q = M.Head(gauss_q_pair)()
reg = M.Head(M.Tail(gauss_q_pair)())()
two_nat, reg = nat("2", reg)
gauss_element, reg = whole_pair(M.Zero, two_nat, M.Zero, three_nat, reg)
gauss_conj_res = A.RingConjugate(gauss_element, gauss_q, reg)()
gauss_conj = M.Head(gauss_conj_res)()
reg1 = M.Head(M.Tail(gauss_conj_res)())()
gauss_prod_res = A.RingMultiply(gauss_element, gauss_conj, gauss_p, gauss_q, reg1)()
gauss_prod = M.Head(gauss_prod_res)()
reg = M.Head(M.Tail(gauss_prod_res)())()
gauss_const = M.Head(gauss_prod)()
gauss_omega = M.Head(M.Tail(gauss_prod)())()
assert A.WholeIsZero(gauss_omega, reg)() is M.truth_value, (
    "the omega coordinate must vanish in the second ring too"
)
thirteen_nat, reg = nat("13", reg)
thirteen_whole_pair = M.Whole(thirteen_nat, M.Zero, reg)()
thirteen_whole = M.Head(thirteen_whole_pair)()
reg = M.Head(M.Tail(thirteen_whole_pair)())()
assert A.WholeEqual(gauss_const, thirteen_whole, reg)() is M.truth_value, (
    "the second ring's derived norm must come out 13, machine computed %s"
    % whole_text(gauss_const, reg)
)
print("    Same machinery under a second relation derives that ring's norm: %s."
      % whole_text(gauss_const, reg))
print()

mark("[4] ring and norms")
# --- [5] the machine links its own discoveries ----------------------------
print("[5] Linking the sweep discovery to the derived norm...")

norm_lambda_value = whole_text(norm_lambda, reg)
sq_pair = A.Multiply(three_nat, three_nat, reg)()
norm_product = M.Head(sq_pair)()
reg = M.Head(M.Tail(sq_pair)())()
assert M.NatEq(norm_product, M.nine, reg)() is M.truth_value, (
    "3 * 3 must be 9 by the machine's own multiplication"
)
assert A.WholeEqual(norm_lambda, nine_whole, reg)() is M.false_value, (
    "the norm itself is 3, not 9; the link is through the square"
)
print("    Derived norm of 1 - omega: %s; machine multiplication gives %s;"
      % (norm_lambda_value, M.NatRepOf(norm_product, reg)()()))
print("    the discovered separating modulus is %d = N(1 - omega) * N(1 - omega)."
      % discovered_modulus_value)
print("    The modulus the sweep found is the square of the norm of the prime over 3.")
print()

mark("[5] discovery link")
# --- [6] the gate refuses discovery without a derivation ------------------
print("[6] The sweep record names its candidate lemma; the ledger is asked...")

candidate_name = M.Char(
    "mod_%d_power_%d_coprime_%d_disjoint_image_obstruction"
    % (
        discovered_modulus_value,
        M.NatRepOf(power, reg)()(),
        M.NatRepOf(filter_prime, reg)()(),
    )
)
ledger = Ledger.EmptyPromotionLedger(reg)()
assert M.IdentityCompare(Ledger.PromotionLedgerVersion(ledger)(), M.Zero)() is M.truth_value, (
    "a fresh ledger starts at version zero"
)
print("    Candidate lemma synthesized from machine data: %s" % candidate_name.symbol)

discovery_start = M.Atom()
discovery_goal = M.Atom()
discovery_candidate = Eval.CandidateMacro(
    candidate_name, discovery_start, discovery_goal, M.EmptyList
)()
evidence = Eval.EvaluateCandidateProof(
    discovery_candidate, discovery_start, discovery_goal, M.EmptyList, reg
)()
assert M.IdentityCompare(M.Head(evidence)(), L.CandidateEvaluatedLabel)() is M.false_value, (
    "a sweep discovery is not a proof and must not be certified as one"
)
assert M.IdentityCompare(M.Head(evidence)(), L.GoalMismatchLabel)() is M.truth_value, (
    "the refusal reason must be that no derivation reaches the goal"
)
baseline_cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
promotion = Ledger.SubmitCandidateForPromotion(
    ledger,
    discovery_candidate,
    L.ProofSchemaPromotionLabel,
    discovery_start,
    discovery_goal,
    baseline_cost,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    reg,
)()
assert M.IdentityCompare(M.Head(promotion)(), L.PromotionRejectedLabel)() is M.truth_value, (
    "the promotion gate must reject a discovery with no Checker B receipt"
)
assert M.NatEq(Ledger.PromotionLedgerVersion(ledger)(), M.Zero, reg)() is M.truth_value, (
    "the ledger must not move on a rejected candidate"
)
print("    Rejected, exactly as it must be: no receipt, no ledger entry.")
print()

mark("[6] ledger gate")
print("=== ALL TEST 20 EISENSTEIN DISCOVERY CHECKS PASSED in %.3fs ===" % (time.time() - t0))
print("Derived by the machine, with nothing cubic written by hand:")
print("  - modulus 9 discovered by the parameterized sweep as the first separator")
print("    of the unit cube image {1, 8} from the unit pair-sum image {0, 2, 7};")
print("  - the complete residue case analysis modulo 9 run by machine arithmetic;")
print("  - the Eisenstein ring built from the relation as parameters, with the")
print("    norm of 1 - omega derived as 3 and its square equal to the discovered")
print("    modulus, and multiplicativity verified on a witness set.")
print("Boundary: unique factorization in the ring, the infinite descent, and the")
print("full n = 3 theorem are not derived by the current machinery and are not")
print("claimed here.")
