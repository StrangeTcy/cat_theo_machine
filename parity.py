from __future__ import annotations

from . import machine as M
from . import labels as Lmod
from . import proof as Pmod
from .gmprep import GMPExactQuotientText, GMPEqualText
from .graph import (
    GraphNodes,
    InventedLemma,
    InventedLemmaCertificate,
    InventedLemmaGoal,
    InventedLemmaProposition,
    IsInventedLemma,
    ParsePolynomialExpressionText,
    TermsAlphaEquivalent,
)
from .mining import (
    AppendMachineChains,
    BoundedPolynomialVariables,
    CandidateValidation,
    CandidateValidationStatus,
    CanonicalMonomialCoefficient,
    CanonicalPolynomialEqual,
    CanonicalPolynomialScale,
    CanonicalExpressionEqual,
    NormalizeCanonicalPolynomial,
    MergeVariableChains,
    SubstituteExpression,
    SubstitutionEntry,
)


class WitnessedDivides(M.Edge):
    def __init__(self, divisor, dividend, witness):
        self.result = M.Pair(
            Lmod.DividesLabel,
            M.Pair(divisor, M.Pair(dividend, M.Pair(witness, M.EmptyList))),
        )
        super().__init__(inputs=M.Pair(divisor, M.Pair(dividend, M.Pair(witness, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class DividesDivisor(M.Edge):
    def __init__(self, fact):
        self.result = M.Head(M.Tail(fact)())()
        super().__init__(inputs=M.Pair(fact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DividesDividend(M.Edge):
    def __init__(self, fact):
        self.result = M.Head(M.Tail(M.Tail(fact)())())()
        super().__init__(inputs=M.Pair(fact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DividesWitness(M.Edge):
    def __init__(self, fact):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(fact)())())())()
        super().__init__(inputs=M.Pair(fact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IntegerTwo(M.Edge):
    def __init__(self):
        self.result = M.Pair(M.ExprIntLabel, M.Pair(M.two, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class IntegerOne(M.Edge):
    def __init__(self):
        self.result = M.Pair(M.ExprIntLabel, M.Pair(M.one, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EvenWitnessVariable(M.Edge):
    def __init__(self, expression):
        variables = BoundedPolynomialVariables(expression)()
        token = M.Char("value")
        if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
            variable = M.Head(variables)()
            token = M.Head(M.Tail(variable)())()
        self.result = M.Pair(
            M.VarTag,
            M.Pair(M.Char("even-witness-" + str(token())), M.EmptyList),
        )
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TwiceExpression(M.Edge):
    def __init__(self, expression):
        self.result = M.Pair(
            M.ExprMulLabel,
            M.Pair(IntegerTwo()(), M.Pair(expression, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SquareExpression(M.Edge):
    def __init__(self, expression):
        self.result = M.Pair(
            M.ExprPowLabel,
            M.Pair(
                expression,
                M.Pair(
                    M.Pair(M.ExprIntLabel, M.Pair(M.two, M.EmptyList)),
                    M.EmptyList,
                ),
            ),
        )
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ExpressionEquality(M.Edge):
    def __init__(self, left, right):
        self.result = M.Pair(
            M.ExprEqLabel, M.Pair(left, M.Pair(right, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class VerifyWitnessedDivisibility(M.Edge):
    def __init__(self, fact, substitutions, registry):
        self.result = M.false_value
        if M.IsPair(fact)() is M.truth_value:
            if M.IdentityCompare(M.Head(fact)(), Lmod.DividesLabel)() is M.truth_value:
                dividend = SubstituteExpression(
                    DividesDividend(fact)(), substitutions,
                )()
                product = M.Pair(
                    M.ExprMulLabel,
                    M.Pair(
                        DividesDivisor(fact)(),
                        M.Pair(DividesWitness(fact)(), M.EmptyList),
                    ),
                )
                product = SubstituteExpression(product, substitutions)()
                self.result = CanonicalExpressionEqual(
                    dividend, product, registry,
                )()
        super().__init__(inputs=M.Pair(fact, M.Pair(substitutions, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class DivisibilityAssumption(M.Edge):
    def __init__(self, fact, substitution, verification):
        self.result = M.Pair(
            M.Char("verified-divisibility-assumption"),
            M.Pair(fact, M.Pair(substitution, M.Pair(verification, M.EmptyList))),
        )
        super().__init__(inputs=M.Pair(fact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DivisibilityAssumptionFact(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(record)())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DivisibilityAssumptionSubstitution(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(record)())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MakeEvenAssumption(M.Edge):
    def __init__(self, expression, registry):
        witness = EvenWitnessVariable(expression)()
        fact = WitnessedDivides(IntegerTwo()(), expression, witness)()
        substitution = M.Pair(
            SubstitutionEntry(expression, TwiceExpression(witness)())(),
            M.EmptyList,
        )
        verified = VerifyWitnessedDivisibility(
            fact, substitution, registry,
        )()
        if verified is M.truth_value:
            self.result = DivisibilityAssumption(
                fact, substitution, M.Char("normalized-zero"),
            )()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PropagateEvenSquare(M.Edge):
    def __init__(self, target, assumptions, registry):
        if M.IdentityCompare(assumptions, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            record = M.Head(assumptions)()
            fact = DivisibilityAssumptionFact(record)()
            source = DividesDividend(fact)()
            source_square = SquareExpression(source)()
            if CanonicalExpressionEqual(source_square, target, registry)() is M.truth_value:
                witness = DividesWitness(fact)()
                target_witness = M.Pair(
                    M.ExprMulLabel,
                    M.Pair(
                        IntegerTwo()(),
                        M.Pair(SquareExpression(witness)(), M.EmptyList),
                    ),
                )
                result_fact = WitnessedDivides(
                    IntegerTwo()(), target, target_witness,
                )()
                substitution = DivisibilityAssumptionSubstitution(record)()
                verified = VerifyWitnessedDivisibility(
                    result_fact, substitution, registry,
                )()
                if verified is M.truth_value:
                    self.result = M.Pair(
                        M.Char("witness-propagation-derivation"),
                        M.Pair(
                            fact,
                            M.Pair(
                                result_fact,
                                M.Pair(
                                    target_witness,
                                    M.Pair(M.Char("proved"), M.EmptyList),
                                ),
                            ),
                        ),
                    )
                else:
                    self.result = M.EmptyList
            else:
                self.result = PropagateEvenSquare(
                    target, M.Tail(assumptions)(), registry,
                )()
        super().__init__(inputs=M.Pair(target, M.Pair(assumptions, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class EvenGoal(M.Edge):
    def __init__(self, expression):
        self.result = M.Pair(
            M.Char("even-goal"), M.Pair(expression, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EvenImplicationGoal(M.Edge):
    def __init__(self, variable):
        self.result = M.Pair(
            M.Char("even-square-implies-even"),
            M.Pair(variable, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ParityBranch(M.Edge):
    def __init__(self, name, substitution, evidence, status):
        self.result = M.Pair(
            M.Char(name),
            M.Pair(
                substitution,
                M.Pair(evidence, M.Pair(M.Char(status), M.EmptyList)),
            ),
        )
        super().__init__(inputs=M.Pair(substitution, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BuildParityCaseSplit(M.Edge):
    def __init__(self, variable, registry):
        even_witness = EvenWitnessVariable(variable)()
        even_replacement = TwiceExpression(even_witness)()
        even_substitution = M.Pair(
            SubstitutionEntry(variable, even_replacement)(), M.EmptyList,
        )
        even_fact = WitnessedDivides(
            IntegerTwo()(), variable, even_witness,
        )()
        even_verified = VerifyWitnessedDivisibility(
            even_fact, even_substitution, registry,
        )()
        odd_witness = M.Pair(
            M.VarTag,
            M.Pair(M.Char("odd-witness-" + str(M.Head(M.Tail(variable)())())), M.EmptyList),
        )
        odd_replacement = M.Pair(
            M.ExprAddLabel,
            M.Pair(
                TwiceExpression(odd_witness)(),
                M.Pair(IntegerOne()(), M.EmptyList),
            ),
        )
        odd_substitution = M.Pair(
            SubstitutionEntry(variable, odd_replacement)(), M.EmptyList,
        )
        odd_square = SquareExpression(odd_replacement)()
        odd_half = M.Pair(
            M.ExprAddLabel,
            M.Pair(
                M.Pair(
                    M.ExprMulLabel,
                    M.Pair(IntegerTwo()(), M.Pair(SquareExpression(odd_witness)(), M.EmptyList)),
                ),
                M.Pair(TwiceExpression(odd_witness)(), M.EmptyList),
            ),
        )
        odd_normal_form = M.Pair(
            M.ExprAddLabel,
            M.Pair(
                TwiceExpression(odd_half)(),
                M.Pair(IntegerOne()(), M.EmptyList),
            ),
        )
        odd_identity = ExpressionEquality(odd_square, odd_normal_form)()
        odd_verified = CanonicalExpressionEqual(
            odd_square, odd_normal_form, registry,
        )()
        if M.AndAtom(even_verified, odd_verified)() is M.truth_value:
            even_branch = ParityBranch(
                "parity-even-branch", even_substitution, even_fact, "proved",
            )()
            odd_branch = ParityBranch(
                "parity-odd-branch", odd_substitution, odd_identity, "contradiction-closed",
            )()
            self.result = M.Pair(
                M.Char("parity-case-split"),
                M.Pair(
                    variable,
                    M.Pair(
                        even_branch,
                        M.Pair(
                            odd_branch,
                            M.Pair(
                                M.Pair(
                                    M.Char("domain-axiom"),
                                    M.Pair(M.Char("parity-exhaustiveness"), M.EmptyList),
                                ),
                                M.Pair(M.Char("proved"), M.EmptyList),
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


class ParityCaseSplitLemma(M.Edge):
    def __init__(self, variable, registry):
        split = BuildParityCaseSplit(variable, registry)()
        goal = EvenImplicationGoal(variable)()
        certificate = M.Pair(
            M.Char("invention-evidence"),
            M.Pair(
                split,
                M.Pair(
                    M.Char("bounded-exhaustive-parity-split"),
                    M.Pair(M.Char("proved"), M.EmptyList),
                ),
            ),
        )
        self.result = InventedLemma(
            goal,
            goal,
            M.EmptyList,
            M.Char("verified-case-split"),
            M.Zero,
            certificate,
        )()
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FindParityLemma(M.Edge):
    def __init__(self, nodes):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            node = M.Head(nodes)()
            found = M.false_value
            if IsInventedLemma(node)() is M.truth_value:
                certificate = InventedLemmaCertificate(node)()
                if M.IsPair(certificate)() is M.truth_value:
                    structural = M.Head(M.Tail(certificate)())()
                    if M.IsPair(structural)() is M.truth_value:
                        found = M.Compare(
                            M.Head(structural)(), M.Char("parity-case-split"),
                        )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindParityLemma(M.Tail(nodes)())()
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplayParityLemma(M.Edge):
    def __init__(self, lemma, variable, square_even_fact, registry):
        self.result = M.EmptyList
        certificate = InventedLemmaCertificate(lemma)()
        structural = M.Head(M.Tail(certificate)())()
        rebuilt = BuildParityCaseSplit(variable, registry)()
        stored_valid = M.false_value
        if M.IsPair(structural)() is M.truth_value:
            if M.Compare(
                M.Head(structural)(), M.Char("parity-case-split"),
            )() is M.truth_value:
                stored_variable = M.Head(M.Tail(structural)())()
                stored_rebuilt = BuildParityCaseSplit(
                    stored_variable, registry,
                )()
                if M.IdentityCompare(
                    stored_rebuilt, M.EmptyList,
                )() is M.false_value:
                    stored_valid = TermsAlphaEquivalent(
                        structural, stored_rebuilt,
                    )()
        premise_ok = CanonicalExpressionEqual(
            DividesDividend(square_even_fact)(),
            SquareExpression(variable)(),
            registry,
        )()
        divisor_ok = CanonicalExpressionEqual(
            DividesDivisor(square_even_fact)(), IntegerTwo()(), registry,
        )()
        if M.AndAtom(
            stored_valid,
            M.AndAtom(
                M.AndAtom(premise_ok, divisor_ok)(),
                M.NotAtom(M.IdentityCompare(rebuilt, M.EmptyList)())(),
            )(),
        )() is M.truth_value:
            witness = EvenWitnessVariable(variable)()
            conclusion = WitnessedDivides(IntegerTwo()(), variable, witness)()
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
                                    square_even_fact,
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


class EquationResidual(M.Edge):
    def __init__(self, equation):
        self.result = M.Pair(
            M.ExprAddLabel,
            M.Pair(
                M.Head(M.Tail(equation)())(),
                M.Pair(
                    M.Pair(
                        M.ExprNegLabel,
                        M.Pair(M.Head(M.Tail(M.Tail(equation)())())(), M.EmptyList),
                    ),
                    M.EmptyList,
                ),
            ),
        )
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPolynomialScalarEqual(M.Edge):
    def __init__(self, left, right, variables):
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            self.result = M.IdentityCompare(right, M.EmptyList)()
        elif M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            scale = GMPExactQuotientText(
                CanonicalMonomialCoefficient(M.Head(left)())(),
                CanonicalMonomialCoefficient(M.Head(right)())(),
            )()
            if M.Compare(M.Char(scale), M.Char(""))() is M.truth_value:
                self.result = M.false_value
            else:
                self.result = CanonicalPolynomialEqual(
                    left,
                    CanonicalPolynomialScale(right, scale, variables)(),
                )()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

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
            M.Pair(
                M.ExprMulLabel,
                M.Pair(
                    DividesDivisor(fact)(),
                    M.Pair(DividesWitness(fact)(), M.EmptyList),
                ),
            ),
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


class CoupledParityGoal(M.Edge):
    def __init__(self, equation):
        self.result = M.Pair(
            M.Char("coupled-even-goal"), M.Pair(equation, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CoupledParityProof(M.Edge):
    def __init__(self, equation, parity_lemma, registry):
        self.result = M.EmptyList
        variables = BoundedPolynomialVariables(equation)()
        if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.false_value:
                first = M.Head(variables)()
                second = M.Head(M.Tail(variables)())()
                first_square_fact = WitnessedDivides(
                    IntegerTwo()(), SquareExpression(first)(), SquareExpression(second)(),
                )()
                first_even = EquationEntailsDivisibility(
                    equation, first_square_fact, M.EmptyList, registry,
                )()
                first_replay = ReplayParityLemma(
                    parity_lemma, first, first_square_fact, registry,
                )()
                first_witness = EvenWitnessVariable(first)()
                first_substitution = M.Pair(
                    SubstitutionEntry(first, TwiceExpression(first_witness)())(),
                    M.EmptyList,
                )
                second_square_fact = WitnessedDivides(
                    IntegerTwo()(), SquareExpression(second)(), SquareExpression(first_witness)(),
                )()
                second_even = EquationEntailsDivisibility(
                    equation, second_square_fact, first_substitution, registry,
                )()
                second_replay = ReplayParityLemma(
                    parity_lemma, second, second_square_fact, registry,
                )()
                if M.AndAtom(first_even, second_even)() is M.truth_value:
                    if M.AndAtom(
                        M.NotAtom(M.IdentityCompare(first_replay, M.EmptyList)())(),
                        M.NotAtom(M.IdentityCompare(second_replay, M.EmptyList)())(),
                    )() is M.truth_value:
                        goal = CoupledParityGoal(equation)()
                        self.result = M.Pair(
                            M.Char("coupled-parity-derivation"),
                            M.Pair(
                                goal,
                                M.Pair(
                                    first_replay,
                                    M.Pair(
                                        second_replay,
                                        M.Pair(
                                            first_substitution,
                                            M.Pair(M.Char("proved"), M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        )
        super().__init__(inputs=M.Pair(equation, M.Pair(parity_lemma, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CoupledParityLemma(M.Edge):
    def __init__(self, equation, parity_lemma, proof):
        goal = CoupledParityGoal(equation)()
        certificate = M.Pair(
            M.Char("coupled-parity-certificate"),
            M.Pair(
                equation,
                M.Pair(parity_lemma, M.Pair(proof, M.EmptyList)),
            ),
        )
        self.result = InventedLemma(
            goal, goal, proof, M.Char("proved"), M.Zero, certificate,
        )()
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FindCoupledParityLemma(M.Edge):
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
                        M.Head(certificate)(), M.Char("coupled-parity-certificate"),
                    )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindCoupledParityLemma(M.Tail(nodes)())()
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NoPositiveSolutionGoal(M.Edge):
    def __init__(self, equation):
        self.result = M.Pair(
            M.Char("no-positive-integer-solution"),
            M.Pair(equation, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VerifyPositiveSquareOrder(M.Edge):
    def __init__(self, equation, lesser, greater, positivity, registry):
        expected = ExpressionEquality(
            SquareExpression(greater)(),
            TwiceExpression(SquareExpression(lesser)())(),
        )()
        variables = MergeVariableChains(
            BoundedPolynomialVariables(equation)(),
            BoundedPolynomialVariables(expected)(),
        )()
        given_residual = NormalizeCanonicalPolynomial(
            EquationResidual(equation)(), variables, registry,
        )()
        expected_residual = NormalizeCanonicalPolynomial(
            EquationResidual(expected)(), variables, registry,
        )()
        same = CanonicalPolynomialScalarEqual(
            given_residual, expected_residual, variables,
        )()
        self.result = M.AndAtom(same, positivity)()
        super().__init__(inputs=M.Pair(equation, M.Pair(lesser, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GenDescentMap(M.Edge):
    def __init__(self, equation, coupled_lemma, parity_lemma, positivity, registry):
        self.result = M.EmptyList
        if positivity is M.truth_value:
            variables = BoundedPolynomialVariables(equation)()
            if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.false_value:
                    first = M.Head(variables)()
                    second = M.Head(M.Tail(variables)())()
                    witness = EvenWitnessVariable(first)()
                    witness_substitution = M.Pair(
                        SubstitutionEntry(first, TwiceExpression(witness)())(),
                        M.EmptyList,
                    )
                    map_variables = MergeVariableChains(
                        BoundedPolynomialVariables(equation)(),
                        M.Pair(witness, M.EmptyList),
                    )()
                    transformed = NormalizeCanonicalPolynomial(
                        SubstituteExpression(EquationResidual(equation)(), witness_substitution)(),
                        map_variables,
                        registry,
                    )()
                    map_substitution = M.Pair(
                        SubstitutionEntry(first, second)(),
                        M.Pair(SubstitutionEntry(second, witness)(), M.EmptyList),
                    )
                    reproduced = NormalizeCanonicalPolynomial(
                        SubstituteExpression(EquationResidual(equation)(), map_substitution)(),
                        map_variables,
                        registry,
                    )()
                    same_solution = CanonicalPolynomialScalarEqual(
                        transformed, reproduced, map_variables,
                    )()
                    strict_first_verified = VerifyPositiveSquareOrder(
                        equation, second, first, positivity, registry,
                    )()
                    strict_first = M.Pair(
                        M.Char("positive-square-order"),
                        M.Pair(
                            equation,
                            M.Pair(
                                M.Pair(M.ExprLtLabel, M.Pair(second, M.Pair(first, M.EmptyList))),
                                M.Pair(strict_first_verified, M.EmptyList),
                            ),
                        ),
                    )
                    descended_equation = SubstituteExpression(
                        equation, map_substitution,
                    )()
                    strict_second_verified = VerifyPositiveSquareOrder(
                        descended_equation, witness, second, positivity, registry,
                    )()
                    strict_second = M.Pair(
                        M.Char("positive-square-order"),
                        M.Pair(
                            descended_equation,
                            M.Pair(
                                M.Pair(M.ExprLtLabel, M.Pair(witness, M.Pair(second, M.EmptyList))),
                                M.Pair(strict_second_verified, M.EmptyList),
                            ),
                        ),
                    )
                    dependencies_present = M.AndAtom(
                        M.NotAtom(M.IdentityCompare(coupled_lemma, M.EmptyList)())(),
                        M.NotAtom(M.IdentityCompare(parity_lemma, M.EmptyList)())(),
                    )()
                    coupled_matches = M.false_value
                    parity_matches = M.false_value
                    if dependencies_present is M.truth_value:
                        coupled_matches = TermsAlphaEquivalent(
                            InventedLemmaGoal(coupled_lemma)(),
                            CoupledParityGoal(equation)(),
                        )()
                        parity_certificate = InventedLemmaCertificate(parity_lemma)()
                        if M.IsPair(parity_certificate)() is M.truth_value:
                            parity_structural = M.Head(M.Tail(parity_certificate)())()
                            if M.IsPair(parity_structural)() is M.truth_value:
                                parity_matches = M.Compare(
                                    M.Head(parity_structural)(),
                                    M.Char("parity-case-split"),
                                )()
                    dependencies = M.AndAtom(
                        dependencies_present,
                        M.AndAtom(coupled_matches, parity_matches)(),
                    )()
                    obligations = M.AndAtom(
                        strict_first_verified, strict_second_verified,
                    )()
                    if M.AndAtom(
                        same_solution,
                        M.AndAtom(dependencies, obligations)(),
                    )() is M.truth_value:
                        self.result = M.Pair(
                            M.Char("discovered-descent-map"),
                            M.Pair(
                                map_substitution,
                                M.Pair(
                                    descended_equation,
                                    M.Pair(
                                        strict_first,
                                        M.Pair(
                                            strict_second,
                                            M.Pair(
                                                coupled_lemma,
                                                M.Pair(parity_lemma, M.Pair(M.Char("proved"), M.EmptyList)),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        )
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DescentLemma(M.Edge):
    def __init__(self, equation, descent_map, coupled_lemma, parity_lemma):
        goal = NoPositiveSolutionGoal(equation)()
        certificate = M.Pair(
            M.Char("well-ordering-descent-certificate"),
            M.Pair(
                equation,
                M.Pair(
                    descent_map,
                    M.Pair(
                        coupled_lemma,
                        M.Pair(
                            parity_lemma,
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
            goal, goal, M.EmptyList, M.Char("verified-descent"), M.Zero, certificate,
        )()
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FindDescentLemma(M.Edge):
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
                        M.Head(certificate)(), M.Char("well-ordering-descent-certificate"),
                    )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindDescentLemma(M.Tail(nodes)())()
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplayDescentLemma(M.Edge):
    def __init__(self, lemma, equation, nodes, positivity, registry):
        self.result = M.EmptyList
        parity_lemma = FindParityLemma(nodes)()
        coupled_lemma = FindCoupledParityLemma(nodes)()
        if M.IdentityCompare(parity_lemma, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(
                M.Char("descent-replay-failure"),
                M.Pair(M.Char("missing-parity-dependency"), M.EmptyList),
            )
        elif M.IdentityCompare(coupled_lemma, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(
                M.Char("descent-replay-failure"),
                M.Pair(M.Char("missing-coupled-parity-dependency"), M.EmptyList),
            )
        else:
            certificate = InventedLemmaCertificate(lemma)()
            expected_coupled = M.Head(
                M.Tail(M.Tail(M.Tail(certificate)())())(),
            )()
            expected_parity = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(certificate)())())())(),
            )()
            coupled_identity = M.AndAtom(
                TermsAlphaEquivalent(
                    InventedLemmaGoal(expected_coupled)(),
                    InventedLemmaGoal(coupled_lemma)(),
                )(),
                TermsAlphaEquivalent(
                    InventedLemmaProposition(expected_coupled)(),
                    InventedLemmaProposition(coupled_lemma)(),
                )(),
            )()
            parity_identity = M.AndAtom(
                TermsAlphaEquivalent(
                    InventedLemmaGoal(expected_parity)(),
                    InventedLemmaGoal(parity_lemma)(),
                )(),
                TermsAlphaEquivalent(
                    InventedLemmaProposition(expected_parity)(),
                    InventedLemmaProposition(parity_lemma)(),
                )(),
            )()
            regenerated = M.EmptyList
            if M.AndAtom(coupled_identity, parity_identity)() is M.truth_value:
                regenerated = GenDescentMap(
                    equation, coupled_lemma, parity_lemma, positivity, registry,
                )()
            if M.IdentityCompare(regenerated, M.EmptyList)() is M.truth_value:
                self.result = M.Pair(
                    M.Char("descent-replay-failure"),
                    M.Pair(M.Char("strict-decrease-unresolved"), M.EmptyList),
                )
            else:
                self.result = M.Pair(
                    M.Char("invented-lemma-replay-derivation"),
                    M.Pair(
                        NoPositiveSolutionGoal(equation)(),
                        M.Pair(
                            lemma,
                            M.Pair(
                                regenerated,
                                M.Pair(
                                    coupled_lemma,
                                    M.Pair(
                                        parity_lemma,
                                        M.Pair(M.Char("proved"), M.EmptyList),
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
        super().__init__(inputs=M.Pair(lemma, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result
