"""Checked signed-polynomial identities through exact positive/negative parts.

A lowered pair denotes a formal polynomial difference, including at negative
integer assignments. Its variables remain the original indeterminates. Equal
cross-sum polynomials therefore establish equality over all integer assignments,
using the existing degree-complete grid identity procedure. This is an equality
bridge, not an inequality, division, factorisation, or descent theorem.
"""

from . import labels as L
from . import machine as M
from . import playground as PG
from . import proof as P
from .math import arithmetic as A


class PolynomialNatTerm(M.Edge):
    """Build an addition or product, eliminating structural zero/one units."""

    def __init__(self, operation, left, right):
        term = M.Pair(operation, M.Pair(left, M.Pair(right, M.EmptyList)))
        if M.IdentityCompare(operation, L.ExprAddLabel)() is M.truth_value:
            if M.IdentityCompare(left, M.Zero)() is M.truth_value:
                term = right
            elif M.IdentityCompare(right, M.Zero)() is M.truth_value:
                term = left
        elif M.IdentityCompare(operation, L.ExprMulLabel)() is M.truth_value:
            if M.OrAtom(M.IdentityCompare(left, M.Zero)(), M.IdentityCompare(right, M.Zero)())() is M.truth_value:
                term = M.Zero
            elif M.IdentityCompare(left, M.one)() is M.truth_value:
                term = right
            elif M.IdentityCompare(right, M.one)() is M.truth_value:
                term = left
        super().__init__(inputs=M.Pair(operation, M.Pair(left, M.Pair(right, M.EmptyList))), results=term)


class MultiplySignedPolynomialParts(M.Edge):
    """Multiply formal differences: (a-b)(c-d) = (ac+bd)-(ad+bc)."""

    def __init__(self, left, right):
        a = M.Head(left)()
        b = M.Head(M.Tail(left)())()
        c = M.Head(right)()
        d = M.Head(M.Tail(right)())()
        positive = PolynomialNatTerm(L.ExprAddLabel,
            PolynomialNatTerm(L.ExprMulLabel, a, c)(),
            PolynomialNatTerm(L.ExprMulLabel, b, d)())()
        negative = PolynomialNatTerm(L.ExprAddLabel,
            PolynomialNatTerm(L.ExprMulLabel, a, d)(),
            PolynomialNatTerm(L.ExprMulLabel, b, c)())()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)),
            results=M.Pair(positive, M.Pair(negative, M.EmptyList)))


class SignedPolynomialPower(M.Edge):
    """Raise formal positive/negative parts to a fixed natural exponent."""

    def __init__(self, parts, exponent, registry):
        active = registry
        if M.NatEq(exponent, M.Zero, registry)() is M.truth_value:
            result = M.Pair(M.one, M.Pair(M.Zero, M.EmptyList))
        elif M.IdentityCompare(M.Head(M.Tail(parts)())(), M.Zero)() is M.truth_value:
            result = M.Pair(
                M.Pair(L.ExprPowLabel, M.Pair(M.Head(parts)(), M.Pair(exponent, M.EmptyList))),
                M.Pair(M.Zero, M.EmptyList),
            )
        else:
            predecessor = M.NatPred(exponent, registry)()
            active = M.Head(M.Tail(predecessor)())()
            previous = SignedPolynomialPower(parts, M.Head(predecessor)(), active)()
            active = M.Head(M.Tail(previous)())()
            result = MultiplySignedPolynomialParts(parts, M.Head(previous)())()
        super().__init__(inputs=M.Pair(parts, M.Pair(exponent, M.Pair(registry, M.EmptyList))),
            results=M.Pair(result, M.Pair(active, M.EmptyList)))


class SignedPolynomialVariables(M.Edge):
    """Admit distinct nonconstant atomic indeterminates, including anonymous Vars."""

    def __init__(self, variables, registry, seen=M.EmptyList):
        verdict = M.false_value
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            verdict = M.truth_value
        elif M.IsPair(variables)() is M.truth_value:
            variable = M.Head(variables)()
            if M.IsPair(variable)() is M.false_value:
                if M.IdentityCompare(variable, M.EmptyList)() is M.false_value:
                    if A.IsNat(variable, registry)() is M.false_value:
                        if M.IsWhole(variable, registry)() is M.false_value:
                            if PG.ChainHasTerm(seen, variable)() is M.false_value:
                                verdict = SignedPolynomialVariables(
                                    M.Tail(variables)(), registry, M.Pair(variable, seen),
                                )()
        super().__init__(inputs=M.Pair(variables, M.Pair(registry, M.Pair(seen, M.EmptyList))), results=verdict)


class LowerSignedPolynomial(M.Edge):
    """Return Pair(parts_or_EmptyList, Pair(registry, EmptyList)).

    Parts are Pair(positive_polynomial, Pair(negative_polynomial, EmptyList)).
    Signed constants use the existing Whole(a,b)=a-b representation, either
    directly or inside ExprInt. Only fixed natural exponents are admitted.
    """

    def __init__(self, term, variables, registry):
        parts = M.EmptyList
        active = registry
        try:
            if A.IsNat(term, registry)() is M.truth_value:
                if M.NatLess(term, M.Zero, registry)() is M.false_value:
                    parts = M.Pair(term, M.Pair(M.Zero, M.EmptyList))
            elif M.IsWhole(term, registry)() is M.truth_value:
                positive = M.WholeLeft(term, registry)()
                negative = M.WholeRight(term, registry)()
                if M.OrAtom(M.NatLess(positive, M.Zero, registry)(), M.NatLess(negative, M.Zero, registry)())() is M.false_value:
                    parts = M.Pair(positive, M.Pair(negative, M.EmptyList))
            elif M.IsPair(term)() is M.false_value:
                if PG.ChainHasTerm(variables, term)() is M.truth_value:
                    parts = M.Pair(term, M.Pair(M.Zero, M.EmptyList))
            else:
                operation = M.Head(term)()
                args = M.Tail(term)()
                if M.IdentityCompare(operation, L.ExprIntLabel)() is M.truth_value:
                    if PG.ExactArity(args, M.one, registry)() is M.truth_value:
                        constant = M.Head(args)()
                        if M.OrAtom(A.IsNat(constant, registry)(), M.IsWhole(constant, registry)())() is M.truth_value:
                            lowered = LowerSignedPolynomial(constant, M.EmptyList, registry)()
                            parts = M.Head(lowered)()
                            active = M.Head(M.Tail(lowered)())()
                elif M.IdentityCompare(operation, L.ExprNegLabel)() is M.truth_value:
                    if PG.ExactArity(args, M.one, registry)() is M.truth_value:
                        lowered = LowerSignedPolynomial(M.Head(args)(), variables, registry)()
                        child = M.Head(lowered)()
                        active = M.Head(M.Tail(lowered)())()
                        if M.IsPair(child)() is M.truth_value:
                            parts = M.Pair(M.Head(M.Tail(child)())(), M.Pair(M.Head(child)(), M.EmptyList))
                elif M.IdentityCompare(operation, L.ExprPowLabel)() is M.truth_value:
                    if PG.ExactArity(args, M.two, registry)() is M.truth_value:
                        exponent = M.Head(M.Tail(args)())()
                        if A.IsNat(exponent, registry)() is M.truth_value:
                            if M.NatLess(exponent, M.Zero, registry)() is M.false_value:
                                lowered = LowerSignedPolynomial(M.Head(args)(), variables, registry)()
                                child = M.Head(lowered)()
                                active = M.Head(M.Tail(lowered)())()
                                if M.IsPair(child)() is M.truth_value:
                                    powered = SignedPolynomialPower(child, exponent, active)()
                                    parts = M.Head(powered)()
                                    active = M.Head(M.Tail(powered)())()
                elif M.OrAtom(M.IdentityCompare(operation, L.ExprAddLabel)(), M.IdentityCompare(operation, L.ExprMulLabel)())() is M.truth_value:
                    if PG.ExactArity(args, M.two, registry)() is M.truth_value:
                        left = LowerSignedPolynomial(M.Head(args)(), variables, registry)()
                        active = M.Head(M.Tail(left)())()
                        right = LowerSignedPolynomial(M.Head(M.Tail(args)())(), variables, active)()
                        active = M.Head(M.Tail(right)())()
                        left_parts = M.Head(left)()
                        right_parts = M.Head(right)()
                        if M.AndAtom(M.IsPair(left_parts)(), M.IsPair(right_parts)())() is M.truth_value:
                            if M.IdentityCompare(operation, L.ExprMulLabel)() is M.truth_value:
                                parts = MultiplySignedPolynomialParts(left_parts, right_parts)()
                            else:
                                positive = PolynomialNatTerm(L.ExprAddLabel, M.Head(left_parts)(), M.Head(right_parts)())()
                                negative = PolynomialNatTerm(L.ExprAddLabel,
                                    M.Head(M.Tail(left_parts)())(), M.Head(M.Tail(right_parts)())())()
                                parts = M.Pair(positive, M.Pair(negative, M.EmptyList))
        except Exception:
            parts = M.EmptyList
            active = registry
        super().__init__(inputs=M.Pair(term, M.Pair(variables, M.Pair(registry, M.EmptyList))),
            results=M.Pair(parts, M.Pair(active, M.EmptyList)))


class SignedPolynomialTranslation(M.Edge):
    """Translate signed equality to the exact cross-sum polynomial equality."""

    def __init__(self, lhs, rhs, variables, registry):
        translation = M.EmptyList
        active = registry
        try:
            if SignedPolynomialVariables(variables, registry)() is M.truth_value:
                left = LowerSignedPolynomial(lhs, variables, registry)()
                active = M.Head(M.Tail(left)())()
                right = LowerSignedPolynomial(rhs, variables, active)()
                active = M.Head(M.Tail(right)())()
                left_parts = M.Head(left)()
                right_parts = M.Head(right)()
                if M.AndAtom(M.IsPair(left_parts)(), M.IsPair(right_parts)())() is M.truth_value:
                    positive = PolynomialNatTerm(L.ExprAddLabel,
                        M.Head(left_parts)(), M.Head(M.Tail(right_parts)())())()
                    negative = PolynomialNatTerm(L.ExprAddLabel,
                        M.Head(right_parts)(), M.Head(M.Tail(left_parts)())())()
                    translation = M.Pair(positive, M.Pair(negative, M.EmptyList))
        except Exception:
            translation = M.EmptyList
            active = registry
        super().__init__(inputs=M.Pair(lhs, M.Pair(rhs, M.Pair(variables, M.Pair(registry, M.EmptyList)))),
            results=M.Pair(translation, M.Pair(active, M.EmptyList)))


class SignedPolynomialDerivation(M.Edge):
    """Return certificate, signed-endpoint derivation, and updated registry.

    Checker B requires both SignedPolynomialRuleLabel and
    PolynomialGridRuleLabel in the caller's trusted rule chain.
    Invalid syntax has no certificate; a refuted identity has no derivation.
    """

    def __init__(self, lhs, rhs, variables, registry):
        translated = SignedPolynomialTranslation(lhs, rhs, variables, registry)()
        sides = M.Head(translated)()
        active = M.Head(M.Tail(translated)())()
        certificate = M.EmptyList
        derivation = M.EmptyList
        if M.IsPair(sides)() is M.truth_value:
            nat_lhs = M.Head(sides)()
            nat_rhs = M.Head(M.Tail(sides)())()
            decided = PG.PolynomialIdentityByGrid(nat_lhs, nat_rhs, variables, active)()
            grid_record = M.Head(decided)()
            active = M.Head(M.Tail(decided)())()
            certificate = M.Pair(L.SignedPolynomialCertificateLabel,
                M.Pair(lhs, M.Pair(rhs, M.Pair(variables,
                    M.Pair(nat_lhs, M.Pair(nat_rhs, M.Pair(grid_record, M.EmptyList)))))))
            fields = M.Tail(grid_record)()
            verdict_fields = M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(fields)())())())())()
            if M.Head(verdict_fields)() is M.truth_value:
                action = M.Pair(L.SignedPolynomialActionLabel, M.Pair(certificate, M.EmptyList))
                built = P.Step(lhs, action, rhs, active)()
                active = M.Head(M.Tail(built)())()
                steps = M.Pair(M.Head(built)(), M.EmptyList)
                cost = P.BuildProofCost(steps, active)()
                active = M.Head(M.Tail(cost)())()
                built = P.Derivation(steps, M.Head(cost)(), active)()
                derivation = M.Head(built)()
                active = M.Head(M.Tail(built)())()
        super().__init__(inputs=M.Pair(lhs, M.Pair(rhs, M.Pair(variables, M.Pair(registry, M.EmptyList)))),
            results=M.Pair(certificate, M.Pair(derivation, M.Pair(active, M.EmptyList))))


class SignedPolynomialAuthority(M.Edge):
    """Require identity membership of the signed translation authority."""

    def __init__(self, trusted_rules):
        verdict = M.false_value
        if M.IsPair(trusted_rules)() is M.truth_value:
            verdict = M.IdentityCompare(M.Head(trusted_rules)(), L.SignedPolynomialRuleLabel)()
            if verdict is M.false_value:
                verdict = SignedPolynomialAuthority(M.Tail(trusted_rules)())()
        super().__init__(inputs=M.Pair(trusted_rules, M.EmptyList), results=verdict)


class VerifySignedPolynomialStep(M.Edge):
    """Replay the recorded signed action and grid checker on exact endpoints."""

    def __init__(self, step, action, trusted_rules, registry):
        from . import checker_b as CB

        current = P.StepCurrent(step, registry)()
        nxt = P.StepNext(step, registry)()
        refusal = M.Pair(L.ConclusionMutationLabel, M.Pair(current, M.Pair(nxt, M.EmptyList)))
        verdict = refusal
        try:
            if SignedPolynomialAuthority(trusted_rules)() is M.false_value:
                verdict = M.Pair(L.UnknownRuleLabel, M.Pair(L.SignedPolynomialRuleLabel, M.EmptyList))
            elif M.Compare(action, P.StepAction(step, registry)())() is M.false_value:
                verdict = refusal
            elif M.IsPair(action)() is M.truth_value:
                if M.IdentityCompare(M.Head(action)(), L.SignedPolynomialActionLabel)() is M.truth_value:
                    if PG.ExactArity(M.Tail(action)(), M.one, registry)() is M.truth_value:
                        certificate = M.Head(M.Tail(action)())()
                        if M.IsPair(certificate)() is M.truth_value:
                            if M.IdentityCompare(M.Head(certificate)(), L.SignedPolynomialCertificateLabel)() is M.truth_value:
                                fields = M.Tail(certificate)()
                                if PG.ExactArity(fields, M.six, registry)() is M.truth_value:
                                    lhs = M.Head(fields)()
                                    fields = M.Tail(fields)()
                                    rhs = M.Head(fields)()
                                    fields = M.Tail(fields)()
                                    variables = M.Head(fields)()
                                    fields = M.Tail(fields)()
                                    nat_lhs = M.Head(fields)()
                                    fields = M.Tail(fields)()
                                    nat_rhs = M.Head(fields)()
                                    grid_record = M.Head(M.Tail(fields)())()
                                    if M.AndAtom(M.Compare(lhs, current)(), M.Compare(rhs, nxt)())() is M.truth_value:
                                        translated = SignedPolynomialTranslation(lhs, rhs, variables, registry)()
                                        sides = M.Head(translated)()
                                        active = M.Head(M.Tail(translated)())()
                                        if M.IsPair(sides)() is M.truth_value:
                                            if M.Compare(sides, M.Pair(nat_lhs, M.Pair(nat_rhs, M.EmptyList)))() is M.truth_value:
                                                if M.IsPair(grid_record)() is M.truth_value:
                                                    if PG.ExactArity(M.Tail(grid_record)(), M.seven, active)() is M.truth_value:
                                                        grid_variables = M.Head(M.Tail(M.Tail(M.Tail(grid_record)())())())()
                                                        if M.Compare(grid_variables, variables)() is M.truth_value:
                                                            grid_action = M.Pair(L.PolynomialGridActionLabel, M.Pair(grid_record, M.EmptyList))
                                                            built = P.Step(nat_lhs, grid_action, nat_rhs, active)()
                                                            active = M.Head(M.Tail(built)())()
                                                            checked = CB.VerifyProofStep(M.Head(built)(), trusted_rules,
                                                                M.EmptyList, M.EmptyList, active)()
                                                            verdict = checked
                                                            if M.Head(checked)() is L.StepVerifiedLabel:
                                                                verdict = M.Pair(L.StepVerifiedLabel, M.Pair(nxt, M.EmptyList))
        except Exception:
            verdict = refusal
        super().__init__(inputs=M.Pair(step, M.Pair(action, M.Pair(trusted_rules, M.Pair(registry, M.EmptyList)))), results=verdict)


__all__ = (
    "LowerSignedPolynomial",
    "SignedPolynomialVariables",
    "SignedPolynomialTranslation",
    "SignedPolynomialDerivation",
    "VerifySignedPolynomialStep",
)
