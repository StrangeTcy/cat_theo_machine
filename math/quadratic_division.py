"""Check one division with norm decrease in a generic quadratic ring.

The relation is omega**2 = p + q*omega. Elements are exact two-coordinate
Pair chains of Wholes. A successful result certifies only the supplied
arithmetic witness; it supplies neither a universal division theorem nor
Checker B authority, unique factorisation, or an infinite descent.
"""

from .. import machine as M
from . import arithmetic as A


class QuadraticWholeSort(M.Edge):
    """Refuse malformed Whole constructors before the arithmetic boundary."""

    def __init__(self, value, registry):
        verdict = M.false_value
        try:
            verdict = M.IsWhole(value, registry)()
            if verdict is M.truth_value:
                left = M.WholeLeft(value, registry)()
                right = M.WholeRight(value, registry)()
                verdict = M.AndAtom(M.IsNat(left, registry)(), M.IsNat(right, registry)())()
                if verdict is M.truth_value:
                    verdict = M.AndAtom(
                        M.NotAtom(M.NatLess(left, M.Zero, registry)())(),
                        M.NotAtom(M.NatLess(right, M.Zero, registry)())(),
                    )()
        except Exception:
            # Native sort access may reject an improper registered constructor.
            verdict = M.false_value
        super().__init__(inputs=M.Pair(value, M.Pair(registry, M.EmptyList)), results=verdict)


class QuadraticElementSort(M.Edge):
    """Require exactly two Whole coordinates, including the terminal EmptyList."""

    def __init__(self, value, registry):
        verdict = M.false_value
        if M.IsPair(value)() is M.truth_value:
            rest = M.Tail(value)()
            if M.IsPair(rest)() is M.truth_value:
                if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.truth_value:
                    verdict = M.AndAtom(
                        QuadraticWholeSort(M.Head(value)(), registry)(),
                        QuadraticWholeSort(M.Head(rest)(), registry)(),
                    )()
        super().__init__(inputs=M.Pair(value, M.Pair(registry, M.EmptyList)), results=verdict)


class VerifyQuadraticDivision(M.Edge):
    """Return Pair(verdict, Pair(registry, EmptyList)) after exact replay.

    Acceptance requires alpha = beta*quotient + remainder, beta != 0,
    scalar N(beta) > 0 and 0 <= N(remainder) < N(beta). Norms are derived
    afresh, including verification of their vanishing omega coordinates.
    Invalid inputs return false_value with the incoming registry.
    """

    def __init__(self, alpha, beta, quotient, remainder, p, q, registry):
        inputs = M.Pair(alpha, M.Pair(beta, M.Pair(quotient, M.Pair(remainder,
            M.Pair(p, M.Pair(q, M.Pair(registry, M.EmptyList)))))))
        verdict = M.false_value
        sorts = M.AndAtom(
            M.AndAtom(QuadraticElementSort(alpha, registry)(),
                QuadraticElementSort(beta, registry)())(),
            M.AndAtom(
                M.AndAtom(QuadraticElementSort(quotient, registry)(),
                    QuadraticElementSort(remainder, registry)())(),
                M.AndAtom(QuadraticWholeSort(p, registry)(),
                    QuadraticWholeSort(q, registry)())(),
            )(),
        )()
        if sorts is M.truth_value:
            beta_zero = M.AndAtom(
                A.WholeIsZero(M.Head(beta)(), registry)(),
                A.WholeIsZero(M.Head(M.Tail(beta)())(), registry)(),
            )()
            if beta_zero is M.false_value:
                multiplied = A.RingMultiply(beta, quotient, p, q, registry)()
                product = M.Head(multiplied)()
                registry = M.Head(M.Tail(multiplied)())()
                added = A.RingAdd(product, remainder, registry)()
                reconstructed = M.Head(added)()
                registry = M.Head(M.Tail(added)())()

                constant_check = A.WholeSubtract(
                    M.Head(alpha)(), M.Head(reconstructed)(), registry,
                )()
                constant_difference = M.Head(constant_check)()
                registry = M.Head(M.Tail(constant_check)())()
                omega_check = A.WholeSubtract(
                    M.Head(M.Tail(alpha)())(),
                    M.Head(M.Tail(reconstructed)())(), registry,
                )()
                omega_difference = M.Head(omega_check)()
                registry = M.Head(M.Tail(omega_check)())()
                equation = M.AndAtom(
                    A.WholeIsZero(constant_difference, registry)(),
                    A.WholeIsZero(omega_difference, registry)(),
                )()
                if equation is M.truth_value:
                    beta_norm_result = A.RingNorm(beta, p, q, registry)()
                    beta_norm_pair = M.Head(beta_norm_result)()
                    registry = M.Head(M.Tail(beta_norm_result)())()
                    remainder_norm_result = A.RingNorm(remainder, p, q, registry)()
                    remainder_norm_pair = M.Head(remainder_norm_result)()
                    registry = M.Head(M.Tail(remainder_norm_result)())()
                    scalar_norms = M.AndAtom(
                        A.WholeIsZero(M.Head(M.Tail(beta_norm_pair)())(), registry)(),
                        A.WholeIsZero(M.Head(M.Tail(remainder_norm_pair)())(), registry)(),
                    )()
                    if scalar_norms is M.truth_value:
                        beta_norm = M.Head(beta_norm_pair)()
                        remainder_norm = M.Head(remainder_norm_pair)()
                        signs = M.AndAtom(
                            M.NatLess(M.WholeRight(beta_norm, registry)(),
                                M.WholeLeft(beta_norm, registry)(), registry)(),
                            M.NotAtom(M.NatLess(
                                M.WholeLeft(remainder_norm, registry)(),
                                M.WholeRight(remainder_norm, registry)(), registry,
                            )())(),
                        )()
                        if signs is M.truth_value:
                            decreased = A.WholeSubtract(beta_norm, remainder_norm, registry)()
                            norm_difference = M.Head(decreased)()
                            registry = M.Head(M.Tail(decreased)())()
                            verdict = M.NatLess(
                                M.WholeRight(norm_difference, registry)(),
                                M.WholeLeft(norm_difference, registry)(), registry,
                            )()
        super().__init__(inputs=inputs,
            results=M.Pair(verdict, M.Pair(registry, M.EmptyList)))
