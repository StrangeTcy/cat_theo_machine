from __future__ import annotations

from .. import machine as M
from .. import labels as L


class IsNat(M.Edge):
    def __init__(self, x, registry):
        self.result = self._check(x, registry)
        super().__init__(inputs=M.Pair(x, M.Pair(registry, M.EmptyList)), results=self.result)

    def _check(self, x, registry):
        rep = M.NatRepOf(x, registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class Add(M.Edge):
    def __init__(self, a, b, registry):
        nat_a = IsNat(a, registry)()
        nat_b = IsNat(b, registry)()
        if M.AndAtom(nat_a, nat_b)() is M.truth_value:
            atom_result = self._add(a, b, registry)
        else:
            atom_result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

        self.result = atom_result
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def _add(self, a, b, registry):
        rep_a = M.NatRepOf(a, registry)()
        rep_b = M.NatRepOf(b, registry)()
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(rep_b, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        sum_rep = M.GMPRep(rep_a() + rep_b())
        return M.NatFromRep(sum_rep, registry)()

    def __call__(self):
        return self.result


class Multiply(M.Edge):
    def __init__(self, a, b, registry):
        nat_a = IsNat(a, registry)()
        nat_b = IsNat(b, registry)()
        if M.AndAtom(nat_a, nat_b)() is M.truth_value:
            atom_result = self._mul(a, b, registry)
        else:
            atom_result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

        self.result = atom_result
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def _mul(self, a, b, registry):
        rep_a = M.NatRepOf(a, registry)()
        rep_b = M.NatRepOf(b, registry)()
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(rep_b, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        product_rep = M.GMPRep(rep_a() * rep_b())
        return M.NatFromRep(product_rep, registry)()

    def __call__(self):
        return self.result


def _natural_rep(value, registry):
    """The existing NatRepOf boundary, with negative cached reps refused.

    NatFromRep clamps negatives to Zero, so partial natural operations must
    reject underflow before interning, not silently inherit that saturation.
    """
    rep = M.NatRepOf(value, registry)()
    if M.IdentityCompare(rep, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    if rep() < 0:
        return M.EmptyList
    return rep


class NatSubtract(M.Edge):
    """Partial a-b on naturals. Underflow or non-Nat -> Pair([], [registry])."""

    def __init__(self, a, b, registry):
        rep_a = _natural_rep(a, registry)
        rep_b = _natural_rep(b, registry)
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        elif M.IdentityCompare(rep_b, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        elif rep_a() < rep_b():
            self.result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        else:
            self.result = M.NatFromRep(M.GMPRep(rep_a() - rep_b()), registry)()
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class ExactNatQuotient(M.Edge):
    """Return a/b only for a natural a and a positive natural divisor b.

    Delegates divisibility to the existing Divides edge. No rounding,
    truncation or 0/0 convention is introduced. Return shape matches Add.
    """

    def __init__(self, a, b, registry):
        rep_a = _natural_rep(a, registry)
        rep_b = _natural_rep(b, registry)
        self.result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(rep_b, M.EmptyList)() is M.false_value:
                if rep_b() > 0:
                    if Divides(b, a, registry)() is M.truth_value:
                        self.result = M.NatFromRep(M.GMPRep(rep_a() // rep_b()), registry)()
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class CoprimeCofactors(M.Edge):
    """Compute a=g*u, b=g*v, gcd(u,v)=1 using Gcd and ExactNatQuotient.

    Result Pair(record-or-[], Pair(registry, [])); record is
    Pair(CoprimeCofactorsLabel, [a,b,g,u,v]). Both-zero is refused (g=0).
    One-zero is allowed: its cofactors are (0,1) or (1,0).
    The record certifies the *reduced* pair, not that the inputs are coprime.
    This is gcd extraction, not prime factorisation or a square-factor lemma.
    """

    def __init__(self, a, b, registry):
        self.result = self._compute(a, b, registry)
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def _compute(self, a, b, registry):
        if M.IdentityCompare(_natural_rep(a, registry), M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(_natural_rep(b, registry), M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        gcd_res = Gcd(a, b, registry)()
        gcd = M.Head(gcd_res)()
        reg1 = M.Head(M.Tail(gcd_res)())()
        if M.NatEq(gcd, M.Zero, reg1)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg1, M.EmptyList))
        left = ExactNatQuotient(a, gcd, reg1)()
        u = M.Head(left)()
        reg2 = M.Head(M.Tail(left)())()
        right = ExactNatQuotient(b, gcd, reg2)()
        v = M.Head(right)()
        reg3 = M.Head(M.Tail(right)())()
        if IsCoprime(u, v, reg3)() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(reg3, M.EmptyList))
        record = M.Pair(L.CoprimeCofactorsLabel, M.Pair(a, M.Pair(b,
            M.Pair(gcd, M.Pair(u, M.Pair(v, M.EmptyList))))))
        return M.Pair(record, M.Pair(reg3, M.EmptyList))

    def __call__(self):
        return self.result


class NatPredecessorFact(M.Edge):
    """Guarded arithmetic-to-fact adapter for the Peano order pack.

    For a positive natural n compute p=NatPred(n), check Succ(p)=n, and
    return Pair(NatSuccessor(p,n), Pair(registry, [])). Zero and invalid
    sorts return no fact: NatPred's saturated predecessor at zero must NOT
    license NatLess(0,0). This is a computed premise, not an order verdict.
    """

    def __init__(self, n, registry):
        self.result = self._compute(n, registry)
        super().__init__(inputs=M.Pair(n, M.Pair(registry, M.EmptyList)), results=self.result)

    def _compute(self, n, registry):
        rep = _natural_rep(n, registry)
        if M.IdentityCompare(rep, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if rep() == 0:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        pred = M.NatPred(n, registry)()
        p = M.Head(pred)()
        reg1 = M.Head(M.Tail(pred)())()
        successor = M.Succ(p, reg1)()
        reg2 = M.Head(M.Tail(successor)())()
        if M.NatEq(M.Head(successor)(), n, reg2)() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(reg2, M.EmptyList))
        fact = M.Pair(L.NatSuccessorLabel, M.Pair(p, M.Pair(n, M.EmptyList)))
        return M.Pair(fact, M.Pair(reg2, M.EmptyList))

    def __call__(self):
        return self.result


class Divides(M.Edge):
    def __init__(self, a, b, registry):
        nat_a = IsNat(a, registry)()
        nat_b = IsNat(b, registry)()
        if M.AndAtom(nat_a, nat_b)() is M.truth_value:
            atom_result = self._divides(a, b, registry)
        else:
            atom_result = M.false_value

        self.result = atom_result
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def _divides(self, a, b, registry):
        rep_a = M.NatRepOf(a, registry)()
        rep_b = M.NatRepOf(b, registry)()
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.truth_value or M.IdentityCompare(rep_b, M.EmptyList)() is M.truth_value:
            return M.false_value
        val_a = rep_a()
        val_b = rep_b()
        if val_a is None or val_b is None:
            return M.false_value
        if val_a == 0:
            return M.truth_value if val_b == 0 else M.false_value
        return M.truth_value if (val_b % val_a == 0) else M.false_value

    def __call__(self):
        return self.result


Divisible = Divides


class Gcd(M.Edge):
    def __init__(self, a, b, registry):
        nat_a = IsNat(a, registry)()
        nat_b = IsNat(b, registry)()
        if M.AndAtom(nat_a, nat_b)() is M.truth_value:
            atom_result = self._gcd(a, b, registry)
        else:
            atom_result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

        self.result = atom_result
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def _gcd(self, a, b, registry):
        rep_a = M.NatRepOf(a, registry)()
        rep_b = M.NatRepOf(b, registry)()
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.truth_value or M.IdentityCompare(rep_b, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        val_a = rep_a()
        val_b = rep_b()
        if val_a is None or val_b is None:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        import math
        val_gcd = math.gcd(val_a, val_b)
        return M.NatFromRep(M.GMPRep(val_gcd), registry)()

    def __call__(self):
        return self.result


class Modulo(M.Edge):
    def __init__(self, a, b, registry):
        nat_a = IsNat(a, registry)()
        nat_b = IsNat(b, registry)()
        if M.AndAtom(nat_a, nat_b)() is M.truth_value:
            atom_result = self._mod(a, b, registry)
        else:
            atom_result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

        self.result = atom_result
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def _mod(self, a, b, registry):
        rep_a = M.NatRepOf(a, registry)()
        rep_b = M.NatRepOf(b, registry)()
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.truth_value or M.IdentityCompare(rep_b, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        val_a = rep_a()
        val_b = rep_b()
        if val_a is None or val_b is None or val_b == 0:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        val_mod = val_a % val_b
        return M.NatFromRep(M.GMPRep(val_mod), registry)()

    def __call__(self):
        return self.result


class IsCoprime(M.Edge):
    def __init__(self, a, b, registry):
        rep_a = M.NatRepOf(a, registry)()
        rep_b = M.NatRepOf(b, registry)()
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.truth_value or M.IdentityCompare(rep_b, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            import math
            val_a = rep_a()
            val_b = rep_b()
            if val_a is None or val_b is None:
                self.result = M.false_value
            else:
                self.result = M.truth_value if math.gcd(val_a, val_b) == 1 else M.false_value
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


# ============================================================
# Generic signed-integer accessors and quadratic-ring scaffolding
#
# Signed integers are the kernel's Whole(a, b) = a - b difference
# pairs; only the accessors a pair form already fixes are added
# here (negation, zero test, canonical equality). The ring layer
# is parameterized by the reduction relation
# omega^2 = p + q*omega with Whole coefficients p and q, so one
# piece of machinery instantiates any order-2 extension. Every
# quantity read back (a norm, a coefficient) is computed from the
# relation through RingMultiply / RingConjugate; no closed form
# is asserted anywhere in this module.
# ============================================================


class WholeNegate(M.Edge):
    """Negate a Whole: -(a - b) = b - a."""

    def __init__(self, x, registry):
        left = M.WholeLeft(x, registry)()
        right = M.WholeRight(x, registry)()
        self.result = M.Whole(right, left, registry)()
        super().__init__(
            inputs=M.Pair(x, M.Pair(registry, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class WholeSubtract(M.Edge):
    """x-y over the existing Whole difference-pair sort, via add-of-negate.

    Invalid sorts return Pair([], Pair(registry, [])), as NatSubtract does.
    No second signed representation or integer-normalisation engine is added.
    """

    def __init__(self, x, y, registry):
        if M.AndAtom(M.IsWhole(x, registry)(), M.IsWhole(y, registry)())() is M.false_value:
            self.result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        else:
            neg = WholeNegate(y, registry)()
            reg1 = M.Head(M.Tail(neg)())()
            self.result = M.WholeAdd(x, M.Head(neg)(), reg1)()
        super().__init__(inputs=M.Pair(x, M.Pair(y, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class WholeIsZero(M.Edge):
    """A Whole is zero exactly when its two nat coordinates agree."""

    def __init__(self, x, registry):
        left = M.WholeLeft(x, registry)()
        right = M.WholeRight(x, registry)()
        self.result = M.NatEq(left, right, registry)()
        super().__init__(
            inputs=M.Pair(x, M.Pair(registry, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class WholeEqual(M.Edge):
    """Canonical Whole equality: a - b == c - d iff a + d == b + c."""

    def __init__(self, x, y, registry):
        ax = M.WholeLeft(x, registry)()
        bx = M.WholeRight(x, registry)()
        ay = M.WholeLeft(y, registry)()
        by = M.WholeRight(y, registry)()
        left_pair = M.Add(ax, by, registry)()
        left = M.Head(left_pair)()
        reg1 = M.Head(M.Tail(left_pair)())()
        right_pair = M.Add(bx, ay, reg1)()
        right = M.Head(right_pair)()
        reg2 = M.Head(M.Tail(right_pair)())()
        self.result = M.NatEq(left, right, reg2)()
        super().__init__(
            inputs=M.Pair(x, M.Pair(y, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WholeFromSignedNat(M.Edge):
    """
    Build a Whole from a sign tag and a nat magnitude. The sign tag is a
    machine nat: Zero means non-negative, one means negative. This is the
    only place a sign convention is fixed, and it is a representation
    convention, not a mathematical fact.
    """

    def __init__(self, sign_nat, magnitude_nat, registry):
        if M.NatEq(sign_nat, M.one, registry)() is M.truth_value:
            self.result = M.Whole(M.Zero, magnitude_nat, registry)()
        else:
            self.result = M.Whole(magnitude_nat, M.Zero, registry)()
        super().__init__(
            inputs=M.Pair(sign_nat, M.Pair(magnitude_nat, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RingAdd(M.Edge):
    """
    Add two elements of Z[omega]/(omega^2 = p + q*omega). An element is a
    Pair of Wholes (constant coordinate, omega coordinate); addition is
    coordinatewise. Returns Pair(element, Pair(registry, EmptyList)).
    """

    def __init__(self, x, y, registry):
        a = M.Head(x)()
        b = M.Head(M.Tail(x)())()
        c = M.Head(y)()
        d = M.Head(M.Tail(y)())()
        const_pair = M.WholeAdd(a, c, registry)()
        const = M.Head(const_pair)()
        reg1 = M.Head(M.Tail(const_pair)())()
        omega_pair = M.WholeAdd(b, d, reg1)()
        omega = M.Head(omega_pair)()
        reg2 = M.Head(M.Tail(omega_pair)())()
        element = M.Pair(const, M.Pair(omega, M.EmptyList))
        self.result = M.Pair(element, M.Pair(reg2, M.EmptyList))
        super().__init__(
            inputs=M.Pair(x, M.Pair(y, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RingMultiply(M.Edge):
    """
    Multiply two elements of Z[omega]/(omega^2 = p + q*omega) with Whole
    coefficients p, q:

        (a + b*w)(c + d*w) = ac + (ad + bc)w + bd*w^2
                           = (ac + p*bd) + (ad + bc + q*bd)w

    The reduction is applied structurally from p and q; no product formula
    for any particular ring is written down. Returns
    Pair(element, Pair(registry, EmptyList)).
    """

    def __init__(self, x, y, p, q, registry):
        a = M.Head(x)()
        b = M.Head(M.Tail(x)())()
        c = M.Head(y)()
        d = M.Head(M.Tail(y)())()

        ac_pair = M.WholeMultiply(a, c, registry)()
        ac = M.Head(ac_pair)()
        reg1 = M.Head(M.Tail(ac_pair)())()

        bd_pair = M.WholeMultiply(b, d, reg1)()
        bd = M.Head(bd_pair)()
        reg2 = M.Head(M.Tail(bd_pair)())()

        ad_pair = M.WholeMultiply(a, d, reg2)()
        ad = M.Head(ad_pair)()
        reg3 = M.Head(M.Tail(ad_pair)())()

        bc_pair = M.WholeMultiply(b, c, reg3)()
        bc = M.Head(bc_pair)()
        reg4 = M.Head(M.Tail(bc_pair)())()

        pbd_pair = M.WholeMultiply(p, bd, reg4)()
        pbd = M.Head(pbd_pair)()
        reg5 = M.Head(M.Tail(pbd_pair)())()

        qbd_pair = M.WholeMultiply(q, bd, reg5)()
        qbd = M.Head(qbd_pair)()
        reg6 = M.Head(M.Tail(qbd_pair)())()

        adbc_pair = M.WholeAdd(ad, bc, reg6)()
        adbc = M.Head(adbc_pair)()
        reg7 = M.Head(M.Tail(adbc_pair)())()

        const_pair = M.WholeAdd(ac, pbd, reg7)()
        const = M.Head(const_pair)()
        reg8 = M.Head(M.Tail(const_pair)())()

        omega_pair = M.WholeAdd(adbc, qbd, reg8)()
        omega = M.Head(omega_pair)()
        reg9 = M.Head(M.Tail(omega_pair)())()

        element = M.Pair(const, M.Pair(omega, M.EmptyList))
        self.result = M.Pair(element, M.Pair(reg9, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                x, M.Pair(y, M.Pair(p, M.Pair(q, M.Pair(registry, M.EmptyList))))
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RingConjugate(M.Edge):
    """
    Conjugation in Z[omega]/(omega^2 = p + q*omega): the conjugate of omega
    is the other root of t^2 - q*t - p, namely q - omega, so

        conjugate(a + b*w) = (a + q*b) - b*w

    For any instantiation of the relation this is an involution that fixes
    the rational coordinates; callers verify those properties, they are not
    assumed here. Returns Pair(element, Pair(registry, EmptyList)).
    """

    def __init__(self, x, q, registry):
        a = M.Head(x)()
        b = M.Head(M.Tail(x)())()
        qb_pair = M.WholeMultiply(q, b, registry)()
        qb = M.Head(qb_pair)()
        reg1 = M.Head(M.Tail(qb_pair)())()
        new_a_pair = M.WholeAdd(a, qb, reg1)()
        new_a = M.Head(new_a_pair)()
        reg2 = M.Head(M.Tail(new_a_pair)())()
        neg_pair = WholeNegate(b, reg2)()
        neg_b = M.Head(neg_pair)()
        reg3 = M.Head(M.Tail(neg_pair)())()
        element = M.Pair(new_a, M.Pair(neg_b, M.EmptyList))
        self.result = M.Pair(element, M.Pair(reg3, M.EmptyList))
        super().__init__(
            inputs=M.Pair(x, M.Pair(q, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RingNorm(M.Edge):
    """
    The norm of an element, derived as the product of the element with its
    conjugate: N(x) = x * conjugate(x). In the quadratic case the omega
    coordinate of that product vanishes identically and the constant
    coordinate is the norm. The vanishing coordinate is NOT checked here;
    the caller checks it, and that check is the evidence the norm was
    derived from the relation rather than asserted. Returns
    Pair(Pair(const_coordinate, omega_coordinate), Pair(registry, EmptyList)).
    """

    def __init__(self, x, p, q, registry):
        conj_res = RingConjugate(x, q, registry)()
        conj = M.Head(conj_res)()
        reg1 = M.Head(M.Tail(conj_res)())()
        prod_res = RingMultiply(x, conj, p, q, reg1)()
        prod = M.Head(prod_res)()
        reg2 = M.Head(M.Tail(prod_res)())()
        self.result = M.Pair(prod, M.Pair(reg2, M.EmptyList))
        super().__init__(
            inputs=M.Pair(x, M.Pair(p, M.Pair(q, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


Succ = M.Succ
NatPred = M.NatPred
Count = M.Count
NatEq = M.NatEq
NatLess = M.NatLess
FractionLabel = M.FractionLabel
Fraction = M.Fraction
FractionLeft = M.FractionLeft
FractionRight = M.FractionRight
IsFraction = M.IsFraction
WholeLabel = M.WholeLabel
Whole = M.Whole
WholeLeft = M.WholeLeft
WholeRight = M.WholeRight
IsWhole = M.IsWhole
WholeAdd = M.WholeAdd
WholeMultiply = M.WholeMultiply
NatText = M.NatText
FractionText = M.FractionText
WholeText = M.WholeText

one = M.one
two = M.two
three = M.three
four = M.four
five = M.five
six = M.six
seven = M.seven
eight = M.eight
nine = M.nine

__all__ = [
    "IsNat",
    "Add",
    "Multiply",
    "NatSubtract",
    "WholeSubtract",
    "ExactNatQuotient",
    "CoprimeCofactors",
    "NatPredecessorFact",
    "Succ",
    "NatPred",
    "Count",
    "NatEq",
    "NatLess",
    "FractionLabel",
    "Fraction",
    "FractionLeft",
    "FractionRight",
    "IsFraction",
    "WholeLabel",
    "Whole",
    "WholeLeft",
    "WholeRight",
    "IsWhole",
    "WholeAdd",
    "WholeMultiply",
    "NatText",
    "FractionText",
    "WholeText",
    "Divides",
    "Divisible",
    "Gcd",
    "Modulo",
    "IsCoprime",
    "WholeNegate",
    "WholeIsZero",
    "WholeEqual",
    "WholeFromSignedNat",
    "RingAdd",
    "RingMultiply",
    "RingConjugate",
    "RingNorm",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]


def sync_from_namespace(namespace):
    for name in (
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
    ):
        if name in namespace:
            globals()[name] = namespace[name]
