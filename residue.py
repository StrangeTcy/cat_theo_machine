from __future__ import annotations

from . import machine as M
from . import labels as Lmod
from .graph import (
    GraphNodes,
    InventedLemma,
    InventedLemmaCertificate,
    InventedLemmaGoal,
    InventedLemmaProposition,
    IsInventedLemma,
    TermsAlphaEquivalent,
)
from .mining import (
    BoundedPolynomialVariables,
    CanonicalExpressionEqual,
    CanonicalPolynomialEqual,
    MergeVariableChains,
    NormalizeCanonicalPolynomial,
    SubstituteExpression,
    SubstitutionEntry,
)
from .parity import (
    CanonicalPolynomialScalarEqual,
    DividesDividend,
    DividesDivisor,
    DividesWitness,
    EquationResidual,
    ExpressionEquality,
    SquareExpression,
    VerifyWitnessedDivisibility,
    WitnessedDivides,
)


class IntegerZero(M.Edge):
    def __init__(self):
        self.result = M.Pair(M.ExprIntLabel, M.Pair(M.Zero, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class IntegerOne(M.Edge):
    def __init__(self):
        self.result = M.Pair(M.ExprIntLabel, M.Pair(M.one, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class IntegerTwo(M.Edge):
    def __init__(self):
        self.result = M.Pair(M.ExprIntLabel, M.Pair(M.two, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class IntegerThree(M.Edge):
    def __init__(self):
        self.result = M.Pair(M.ExprIntLabel, M.Pair(M.three, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class IntegerFour(M.Edge):
    def __init__(self):
        self.result = M.Pair(M.ExprIntLabel, M.Pair(M.four, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ProductExpression(M.Edge):
    def __init__(self, left, right):
        self.result = M.Pair(
            M.ExprMulLabel, M.Pair(left, M.Pair(right, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SumExpression(M.Edge):
    def __init__(self, left, right):
        self.result = M.Pair(
            M.ExprAddLabel, M.Pair(left, M.Pair(right, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TripleExpression(M.Edge):
    def __init__(self, expression):
        self.result = ProductExpression(IntegerThree()(), expression)()
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ResidueWitnessVariable(M.Edge):
    def __init__(self, expression):
        variables = BoundedPolynomialVariables(expression)()
        token = M.Char("value")
        if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
            token = M.Head(M.Tail(M.Head(variables)())())()
        self.result = M.Pair(
            M.VarTag,
            M.Pair(M.Char("mod-three-witness-" + str(token())), M.EmptyList),
        )
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class WitnessedCongruence(M.Edge):
    def __init__(self, modulus, left, right, witness):
        self.result = M.Pair(
            Lmod.ModuloLabel,
            M.Pair(
                modulus,
                M.Pair(left, M.Pair(right, M.Pair(witness, M.EmptyList))),
            ),
        )
        super().__init__(inputs=M.Pair(modulus, M.Pair(left, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CongruenceModulus(M.Edge):
    def __init__(self, fact):
        self.result = M.Head(M.Tail(fact)())()
        super().__init__(inputs=M.Pair(fact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CongruenceLeft(M.Edge):
    def __init__(self, fact):
        self.result = M.Head(M.Tail(M.Tail(fact)())())()
        super().__init__(inputs=M.Pair(fact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CongruenceRight(M.Edge):
    def __init__(self, fact):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(fact)())())())()
        super().__init__(inputs=M.Pair(fact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CongruenceWitness(M.Edge):
    def __init__(self, fact):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(fact)())())())())()
        super().__init__(inputs=M.Pair(fact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerifyWitnessedCongruence(M.Edge):
    def __init__(self, fact, substitutions, registry):
        left = SubstituteExpression(CongruenceLeft(fact)(), substitutions)()
        right = SubstituteExpression(CongruenceRight(fact)(), substitutions)()
        witness_product = ProductExpression(
            CongruenceModulus(fact)(), CongruenceWitness(fact)(),
        )()
        expected = SubstituteExpression(
            SumExpression(right, witness_product)(), substitutions,
        )()
        self.result = CanonicalExpressionEqual(left, expected, registry)()
        super().__init__(inputs=M.Pair(fact, M.Pair(substitutions, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ModThreeBranch(M.Edge):
    def __init__(self, residue, substitution, evidence, status):
        self.result = M.Pair(
            M.Char("mod-three-branch"),
            M.Pair(
                residue,
                M.Pair(
                    substitution,
                    M.Pair(evidence, M.Pair(M.Char(status), M.EmptyList)),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(substitution, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ModThreeReplacement(M.Edge):
    def __init__(self, witness, residue):
        base = TripleExpression(witness)()
        if M.IdentityCompare(residue, M.Zero)() is M.truth_value:
            self.result = base
        else:
            self.result = SumExpression(
                base,
                M.Pair(M.ExprIntLabel, M.Pair(residue, M.EmptyList)),
            )()
        super().__init__(inputs=M.Pair(witness, M.Pair(residue, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ModThreeSquareNormalForm(M.Edge):
    def __init__(self, witness, residue):
        if M.IdentityCompare(residue, M.one)() is M.truth_value:
            quotient = SumExpression(
                TripleExpression(SquareExpression(witness)())(),
                ProductExpression(IntegerTwo()(), witness)(),
            )()
        else:
            quotient = SumExpression(
                SumExpression(
                    TripleExpression(SquareExpression(witness)())(),
                    ProductExpression(IntegerFour()(), witness)(),
                )(),
                IntegerOne()(),
            )()
        self.result = SumExpression(
            TripleExpression(quotient)(), IntegerOne()(),
        )()
        super().__init__(inputs=M.Pair(witness, M.Pair(residue, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BuildModThreeCaseSplit(M.Edge):
    def __init__(self, variable, registry):
        witness = ResidueWitnessVariable(variable)()
        zero_replacement = ModThreeReplacement(witness, M.Zero)()
        zero_substitution = M.Pair(
            SubstitutionEntry(variable, zero_replacement)(), M.EmptyList,
        )
        zero_fact = WitnessedDivides(IntegerThree()(), variable, witness)()
        zero_verified = VerifyWitnessedDivisibility(
            zero_fact, zero_substitution, registry,
        )()
        one_replacement = ModThreeReplacement(witness, M.one)()
        one_identity = ExpressionEquality(
            SquareExpression(one_replacement)(),
            ModThreeSquareNormalForm(witness, M.one)(),
        )()
        one_verified = CanonicalExpressionEqual(
            M.Head(M.Tail(one_identity)())(),
            M.Head(M.Tail(M.Tail(one_identity)())())(),
            registry,
        )()
        two_replacement = ModThreeReplacement(witness, M.two)()
        two_identity = ExpressionEquality(
            SquareExpression(two_replacement)(),
            ModThreeSquareNormalForm(witness, M.two)(),
        )()
        two_verified = CanonicalExpressionEqual(
            M.Head(M.Tail(two_identity)())(),
            M.Head(M.Tail(M.Tail(two_identity)())())(),
            registry,
        )()
        all_verified = M.AndAtom(
            zero_verified, M.AndAtom(one_verified, two_verified)(),
        )()
        if all_verified is M.truth_value:
            zero_branch = ModThreeBranch(
                M.Zero, zero_substitution, zero_fact, "proved",
            )()
            one_branch = ModThreeBranch(
                M.one,
                M.Pair(SubstitutionEntry(variable, one_replacement)(), M.EmptyList),
                one_identity,
                "contradiction-closed",
            )()
            two_branch = ModThreeBranch(
                M.two,
                M.Pair(SubstitutionEntry(variable, two_replacement)(), M.EmptyList),
                two_identity,
                "contradiction-closed",
            )()
            self.result = M.Pair(
                M.Char("mod-three-case-split"),
                M.Pair(
                    variable,
                    M.Pair(
                        zero_branch,
                        M.Pair(
                            one_branch,
                            M.Pair(
                                two_branch,
                                M.Pair(
                                    M.Pair(
                                        M.Char("domain-axiom"),
                                        M.Pair(M.Char("mod-three-exhaustiveness"), M.EmptyList),
                                    ),
                                    M.Pair(M.Char("proved"), M.EmptyList),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ModThreeImplicationGoal(M.Edge):
    def __init__(self, variable):
        self.result = M.Pair(
            M.Char("three-divides-square-implies-base"),
            M.Pair(variable, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ModThreeCaseLemma(M.Edge):
    def __init__(self, variable, registry):
        split = BuildModThreeCaseSplit(variable, registry)()
        goal = ModThreeImplicationGoal(variable)()
        certificate = M.Pair(
            M.Char("invention-evidence"),
            M.Pair(
                split,
                M.Pair(
                    M.Char("bounded-exhaustive-mod-three-split"),
                    M.Pair(M.Char("proved"), M.EmptyList),
                ),
            ),
        )
        self.result = InventedLemma(
            goal, goal, M.EmptyList,
            M.Char("verified-residue-case-split"), M.Zero, certificate,
        )()
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FindModThreeLemma(M.Edge):
    def __init__(self, nodes):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            node = M.Head(nodes)()
            found = M.false_value
            if IsInventedLemma(node)() is M.truth_value:
                certificate = InventedLemmaCertificate(node)()
                if M.IsPair(certificate)() is M.truth_value:
                    if M.Compare(
                        M.Head(certificate)(), M.Char("invention-evidence"),
                    )() is M.truth_value:
                        structural = M.Head(M.Tail(certificate)())()
                        if M.IsPair(structural)() is M.truth_value:
                            found = M.Compare(
                                M.Head(structural)(), M.Char("mod-three-case-split"),
                            )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindModThreeLemma(M.Tail(nodes)())()
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplayModThreeLemma(M.Edge):
    def __init__(self, lemma, variable, square_divisible, registry):
        self.result = M.EmptyList
        certificate = InventedLemmaCertificate(lemma)()
        structural = M.Head(M.Tail(certificate)())()
        stored_valid = M.false_value
        if M.IsPair(structural)() is M.truth_value:
            stored_variable = M.Head(M.Tail(structural)())()
            rebuilt_stored = BuildModThreeCaseSplit(stored_variable, registry)()
            if M.IdentityCompare(rebuilt_stored, M.EmptyList)() is M.false_value:
                stored_valid = TermsAlphaEquivalent(structural, rebuilt_stored)()
        rebuilt = BuildModThreeCaseSplit(variable, registry)()
        divisor_ok = CanonicalExpressionEqual(
            DividesDivisor(square_divisible)(), IntegerThree()(), registry,
        )()
        dividend_ok = CanonicalExpressionEqual(
            DividesDividend(square_divisible)(), SquareExpression(variable)(), registry,
        )()
        if M.AndAtom(
            stored_valid,
            M.AndAtom(
                M.AndAtom(divisor_ok, dividend_ok)(),
                M.NotAtom(M.IdentityCompare(rebuilt, M.EmptyList)())(),
            )(),
        )() is M.truth_value:
            conclusion = WitnessedDivides(
                IntegerThree()(), variable, ResidueWitnessVariable(variable)(),
            )()
            self.result = M.Pair(
                M.Char("invented-lemma-replay-derivation"),
                M.Pair(
                    conclusion,
                    M.Pair(
                        lemma,
                        M.Pair(
                            M.Head(M.Tail(M.Tail(structural)())())(),
                            M.Pair(
                                M.Head(M.Tail(M.Tail(M.Tail(structural)())())())(),
                                M.Pair(
                                    M.Head(M.Tail(M.Tail(M.Tail(M.Tail(structural)())())())())(),
                                    M.Pair(M.Char("proved"), M.EmptyList),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        super().__init__(inputs=M.Pair(lemma, M.Pair(variable, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class EquationEntailsDivisibility(M.Edge):
    def __init__(self, equation, fact, substitutions, registry):
        variables = MergeVariableChains(
            BoundedPolynomialVariables(equation)(),
            MergeVariableChains(
                BoundedPolynomialVariables(DividesDividend(fact)())(),
                BoundedPolynomialVariables(DividesWitness(fact)())(),
            )(),
        )()
        premise = NormalizeCanonicalPolynomial(
            SubstituteExpression(EquationResidual(equation)(), substitutions)(),
            variables,
            registry,
        )()
        fact_equation = ExpressionEquality(
            DividesDividend(fact)(),
            ProductExpression(DividesDivisor(fact)(), DividesWitness(fact)())(),
        )()
        conclusion = NormalizeCanonicalPolynomial(
            SubstituteExpression(EquationResidual(fact_equation)(), substitutions)(),
            variables,
            registry,
        )()
        self.result = CanonicalPolynomialScalarEqual(
            premise, conclusion, variables,
        )()
        super().__init__(inputs=M.Pair(equation, M.Pair(fact, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CoupledModThreeGoal(M.Edge):
    def __init__(self, equation):
        self.result = M.Pair(
            M.Char("coupled-mod-three-goal"), M.Pair(equation, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CoupledModThreeProof(M.Edge):
    def __init__(self, equation, case_lemma, registry):
        self.result = M.EmptyList
        variables = BoundedPolynomialVariables(equation)()
        if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.false_value:
                first = M.Head(variables)()
                second = M.Head(M.Tail(variables)())()
                first_square = WitnessedDivides(
                    IntegerThree()(), SquareExpression(first)(), SquareExpression(second)(),
                )()
                first_entails = EquationEntailsDivisibility(
                    equation, first_square, M.EmptyList, registry,
                )()
                first_replay = ReplayModThreeLemma(
                    case_lemma, first, first_square, registry,
                )()
                witness = ResidueWitnessVariable(first)()
                substitution = M.Pair(
                    SubstitutionEntry(first, TripleExpression(witness)())(),
                    M.EmptyList,
                )
                second_square = WitnessedDivides(
                    IntegerThree()(), SquareExpression(second)(), SquareExpression(witness)(),
                )()
                second_entails = EquationEntailsDivisibility(
                    equation, second_square, substitution, registry,
                )()
                second_replay = ReplayModThreeLemma(
                    case_lemma, second, second_square, registry,
                )()
                if M.AndAtom(first_entails, second_entails)() is M.truth_value:
                    if M.AndAtom(
                        M.NotAtom(M.IdentityCompare(first_replay, M.EmptyList)())(),
                        M.NotAtom(M.IdentityCompare(second_replay, M.EmptyList)())(),
                    )() is M.truth_value:
                        self.result = M.Pair(
                            M.Char("coupled-mod-three-derivation"),
                            M.Pair(
                                CoupledModThreeGoal(equation)(),
                                M.Pair(
                                    first_replay,
                                    M.Pair(
                                        second_replay,
                                        M.Pair(
                                            substitution,
                                            M.Pair(M.Char("proved"), M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        )
        super().__init__(inputs=M.Pair(equation, M.Pair(case_lemma, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CoupledModThreeLemma(M.Edge):
    def __init__(self, equation, case_lemma, proof):
        goal = CoupledModThreeGoal(equation)()
        certificate = M.Pair(
            M.Char("coupled-mod-three-certificate"),
            M.Pair(equation, M.Pair(case_lemma, M.Pair(proof, M.EmptyList))),
        )
        self.result = InventedLemma(
            goal, goal, proof, M.Char("proved"), M.Zero, certificate,
        )()
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FindCoupledModThreeLemma(M.Edge):
    def __init__(self, nodes):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            node = M.Head(nodes)()
            found = M.false_value
            if IsInventedLemma(node)() is M.truth_value:
                certificate = InventedLemmaCertificate(node)()
                if M.IsPair(certificate)() is M.truth_value:
                    found = M.Compare(
                        M.Head(certificate)(), M.Char("coupled-mod-three-certificate"),
                    )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindCoupledModThreeLemma(M.Tail(nodes)())()
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerifyPositiveSquareOrder(M.Edge):
    def __init__(self, equation, lesser, greater, positivity, registry):
        expected = ExpressionEquality(
            SquareExpression(greater)(),
            TripleExpression(SquareExpression(lesser)())(),
        )()
        variables = MergeVariableChains(
            BoundedPolynomialVariables(equation)(),
            BoundedPolynomialVariables(expected)(),
        )()
        given = NormalizeCanonicalPolynomial(
            EquationResidual(equation)(), variables, registry,
        )()
        expected_polynomial = NormalizeCanonicalPolynomial(
            EquationResidual(expected)(), variables, registry,
        )()
        same = CanonicalPolynomialScalarEqual(
            given, expected_polynomial, variables,
        )()
        self.result = M.AndAtom(same, positivity)()
        super().__init__(inputs=M.Pair(equation, M.Pair(lesser, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsModThreeSquareEquation(M.Edge):
    def __init__(self, equation, registry):
        variables = BoundedPolynomialVariables(equation)()
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            first = M.Head(variables)()
            second = M.Head(M.Tail(variables)())()
            expected = ExpressionEquality(
                SquareExpression(first)(),
                TripleExpression(SquareExpression(second)())(),
            )()
            given_polynomial = NormalizeCanonicalPolynomial(
                EquationResidual(equation)(), variables, registry,
            )()
            expected_polynomial = NormalizeCanonicalPolynomial(
                EquationResidual(expected)(), variables, registry,
            )()
            self.result = CanonicalPolynomialScalarEqual(
                given_polynomial, expected_polynomial, variables,
            )()
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsModNineSquareEquation(M.Edge):
    def __init__(self, equation, registry):
        variables = BoundedPolynomialVariables(equation)()
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            first = M.Head(variables)()
            second = M.Head(M.Tail(variables)())()
            nine = ProductExpression(IntegerThree()(), IntegerThree()())()
            expected = ExpressionEquality(
                SquareExpression(first)(),
                ProductExpression(nine, SquareExpression(second)())(),
            )()
            given_polynomial = NormalizeCanonicalPolynomial(
                EquationResidual(equation)(), variables, registry,
            )()
            expected_polynomial = NormalizeCanonicalPolynomial(
                EquationResidual(expected)(), variables, registry,
            )()
            self.result = CanonicalPolynomialScalarEqual(
                given_polynomial, expected_polynomial, variables,
            )()
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GenModThreeDescentMap(M.Edge):
    def __init__(self, equation, coupled_lemma, case_lemma, positivity, registry):
        self.result = M.EmptyList
        variables = BoundedPolynomialVariables(equation)()
        if positivity is M.truth_value:
            if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.false_value:
                    first = M.Head(variables)()
                    second = M.Head(M.Tail(variables)())()
                    witness = ResidueWitnessVariable(first)()
                    witness_substitution = M.Pair(
                        SubstitutionEntry(first, TripleExpression(witness)())(),
                        M.EmptyList,
                    )
                    map_substitution = M.Pair(
                        SubstitutionEntry(first, second)(),
                        M.Pair(SubstitutionEntry(second, witness)(), M.EmptyList),
                    )
                    map_variables = MergeVariableChains(
                        variables, M.Pair(witness, M.EmptyList),
                    )()
                    transformed = NormalizeCanonicalPolynomial(
                        SubstituteExpression(EquationResidual(equation)(), witness_substitution)(),
                        map_variables,
                        registry,
                    )()
                    reproduced = NormalizeCanonicalPolynomial(
                        SubstituteExpression(EquationResidual(equation)(), map_substitution)(),
                        map_variables,
                        registry,
                    )()
                    reproduced_ok = CanonicalPolynomialScalarEqual(
                        transformed, reproduced, map_variables,
                    )()
                    first_order = VerifyPositiveSquareOrder(
                        equation, second, first, positivity, registry,
                    )()
                    descended = SubstituteExpression(equation, map_substitution)()
                    second_order = VerifyPositiveSquareOrder(
                        descended, witness, second, positivity, registry,
                    )()
                    dependencies = M.false_value
                    if M.AndAtom(
                        M.NotAtom(M.IdentityCompare(coupled_lemma, M.EmptyList)())(),
                        M.NotAtom(M.IdentityCompare(case_lemma, M.EmptyList)())(),
                    )() is M.truth_value:
                        coupled_ok = TermsAlphaEquivalent(
                            InventedLemmaGoal(coupled_lemma)(),
                            CoupledModThreeGoal(equation)(),
                        )()
                        case_certificate = InventedLemmaCertificate(case_lemma)()
                        case_structural = M.Head(M.Tail(case_certificate)())()
                        case_ok = M.Compare(
                            M.Head(case_structural)(), M.Char("mod-three-case-split"),
                        )()
                        dependencies = M.AndAtom(coupled_ok, case_ok)()
                    if M.AndAtom(
                        reproduced_ok,
                        M.AndAtom(
                            dependencies,
                            M.AndAtom(first_order, second_order)(),
                        )(),
                    )() is M.truth_value:
                        self.result = M.Pair(
                            M.Char("discovered-mod-three-descent-map"),
                            M.Pair(
                                map_substitution,
                                M.Pair(
                                    descended,
                                    M.Pair(
                                        first_order,
                                        M.Pair(
                                            second_order,
                                            M.Pair(
                                                coupled_lemma,
                                                M.Pair(case_lemma, M.Pair(M.Char("proved"), M.EmptyList)),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        )
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NoPositiveModThreeSolutionGoal(M.Edge):
    def __init__(self, equation):
        self.result = M.Pair(
            M.Char("no-positive-mod-three-solution"),
            M.Pair(equation, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ModThreeDescentLemma(M.Edge):
    def __init__(self, equation, descent_map, coupled_lemma, case_lemma):
        goal = NoPositiveModThreeSolutionGoal(equation)()
        certificate = M.Pair(
            M.Char("mod-three-well-ordering-descent-certificate"),
            M.Pair(
                equation,
                M.Pair(
                    descent_map,
                    M.Pair(
                        coupled_lemma,
                        M.Pair(
                            case_lemma,
                            M.Pair(
                                M.Pair(
                                    M.Char("domain-axiom"),
                                    M.Pair(M.Char("well-ordering"), M.EmptyList),
                                ),
                                M.Pair(M.Char("proved"), M.EmptyList),
                            ),
                        ),
                    ),
                ),
            ),
        )
        self.result = InventedLemma(
            goal, goal, M.EmptyList,
            M.Char("verified-mod-three-descent"), M.Zero, certificate,
        )()
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FindModThreeDescentLemma(M.Edge):
    def __init__(self, nodes):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            node = M.Head(nodes)()
            found = M.false_value
            if IsInventedLemma(node)() is M.truth_value:
                certificate = InventedLemmaCertificate(node)()
                if M.IsPair(certificate)() is M.truth_value:
                    found = M.Compare(
                        M.Head(certificate)(),
                        M.Char("mod-three-well-ordering-descent-certificate"),
                    )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindModThreeDescentLemma(M.Tail(nodes)())()
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplayModThreeDescentLemma(M.Edge):
    def __init__(self, lemma, equation, nodes, positivity, registry):
        case_lemma = FindModThreeLemma(nodes)()
        coupled_lemma = FindCoupledModThreeLemma(nodes)()
        status = M.Char("proved")
        regenerated = M.EmptyList
        if M.IdentityCompare(case_lemma, M.EmptyList)() is M.truth_value:
            status = M.Char("missing-mod-three-case-dependency")
        elif M.IdentityCompare(coupled_lemma, M.EmptyList)() is M.truth_value:
            status = M.Char("missing-coupled-mod-three-dependency")
        else:
            certificate = InventedLemmaCertificate(lemma)()
            expected_coupled = M.Head(
                M.Tail(M.Tail(M.Tail(certificate)())())(),
            )()
            expected_case = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(certificate)())())())(),
            )()
            identities = M.AndAtom(
                TermsAlphaEquivalent(
                    InventedLemmaProposition(expected_coupled)(),
                    InventedLemmaProposition(coupled_lemma)(),
                )(),
                TermsAlphaEquivalent(
                    InventedLemmaProposition(expected_case)(),
                    InventedLemmaProposition(case_lemma)(),
                )(),
            )()
            if identities is M.truth_value:
                regenerated = GenModThreeDescentMap(
                    equation, coupled_lemma, case_lemma, positivity, registry,
                )()
            if M.IdentityCompare(regenerated, M.EmptyList)() is M.truth_value:
                status = M.Char("strict-decrease-unresolved")
        if M.Compare(status, M.Char("proved"))() is M.truth_value:
            self.result = M.Pair(
                M.Char("invented-lemma-replay-derivation"),
                M.Pair(
                    NoPositiveModThreeSolutionGoal(equation)(),
                    M.Pair(
                        lemma,
                        M.Pair(
                            regenerated,
                            M.Pair(
                                coupled_lemma,
                                M.Pair(case_lemma, M.Pair(status, M.EmptyList)),
                            ),
                        ),
                    ),
                ),
            )
        else:
            self.result = M.Pair(
                M.Char("mod-three-descent-replay-failure"),
                M.Pair(status, M.EmptyList),
            )
        super().__init__(inputs=M.Pair(lemma, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result
