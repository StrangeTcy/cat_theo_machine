from __future__ import annotations

from . import machine as M
from .gmprep import (
    GMPAddText,
    GMPEqualText,
    GMPFloorQuotientText,
    GMPModuloText,
    GMPMulText,
    GMPSuccText,
)
from .graph import (
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
    MergeVariableChains,
    MachineChainCardinalityText,
    MineNatFromGMPRep,
    NormalizeCanonicalPolynomial,
    SubstituteExpression,
    SubstitutionEntry,
)
from .parity import (
    CanonicalPolynomialScalarEqual,
    DividesDividend,
    DividesDivisor,
    EquationResidual,
    ExpressionEquality,
    SquareExpression,
    VerifyWitnessedDivisibility,
    WitnessedDivides,
)
from .residue import ProductExpression, SumExpression


class IntegerFromText(M.Edge):
    def __init__(self, text):
        self.result = M.Pair(
            M.ExprIntLabel,
            M.Pair(MineNatFromGMPRep(M.GMPRep(text))(), M.EmptyList),
        )
        super().__init__(inputs=M.Pair(M.Char(text), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IntegerText(M.Edge):
    def __init__(self, expression):
        numeral = M.Head(M.Tail(expression)())()
        self.result = M.GMPRepText(M.NatRepOf(numeral, M.AllConstructors)())()
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result


class ModulusWitnessVariable(M.Edge):
    def __init__(self, modulus, expression):
        variables = BoundedPolynomialVariables(expression)()
        token = M.Char("value")
        if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
            token = M.Head(M.Tail(M.Head(variables)())())()
        self.result = M.Pair(
            M.VarTag,
            M.Pair(
                M.Char(
                    "mod-" + IntegerText(modulus)() + "-witness-" + str(token()),
                ),
                M.EmptyList,
            ),
        )
        super().__init__(inputs=M.Pair(modulus, M.Pair(expression, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ModulusReplacement(M.Edge):
    def __init__(self, modulus, witness, residue_text):
        base = ProductExpression(modulus, witness)()
        if GMPEqualText(residue_text, "0")() is M.truth_value:
            self.result = base
        else:
            self.result = SumExpression(
                base, IntegerFromText(residue_text)(),
            )()
        super().__init__(inputs=M.Pair(modulus, M.Pair(witness, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ModulusSquareNormalForm(M.Edge):
    def __init__(self, modulus, witness, residue_text):
        modulus_text = IntegerText(modulus)()
        residue_square = GMPMulText(residue_text, residue_text)()
        remainder_text = GMPModuloText(residue_square, modulus_text)()
        constant_text = GMPFloorQuotientText(residue_square, modulus_text)()
        twice_residue_text = GMPAddText(residue_text, residue_text)()
        quotient = SumExpression(
            ProductExpression(modulus, SquareExpression(witness)())(),
            ProductExpression(IntegerFromText(twice_residue_text)(), witness)(),
        )()
        if GMPEqualText(constant_text, "0")() is M.false_value:
            quotient = SumExpression(
                quotient, IntegerFromText(constant_text)(),
            )()
        self.result = M.Pair(
            M.Char("modulus-square-normal-form"),
            M.Pair(
                SumExpression(
                    ProductExpression(modulus, quotient)(),
                    IntegerFromText(remainder_text)(),
                )(),
                M.Pair(M.Char(remainder_text), M.EmptyList),
            ),
        )
        super().__init__(inputs=M.Pair(modulus, M.Pair(witness, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BoundedResidueBranch(M.Edge):
    def __init__(self, modulus, variable, witness, residue_text, registry):
        replacement = ModulusReplacement(modulus, witness, residue_text)()
        substitution = M.Pair(
            SubstitutionEntry(variable, replacement)(), M.EmptyList,
        )
        if GMPEqualText(residue_text, "0")() is M.truth_value:
            evidence = WitnessedDivides(modulus, variable, witness)()
            verified = VerifyWitnessedDivisibility(
                evidence, substitution, registry,
            )()
            status = M.Char("proved")
        else:
            normal_form = ModulusSquareNormalForm(
                modulus, witness, residue_text,
            )()
            right = M.Head(M.Tail(normal_form)())()
            remainder_text = M.Head(M.Tail(M.Tail(normal_form)())())()()
            evidence = ExpressionEquality(
                SquareExpression(replacement)(), right,
            )()
            identity = CanonicalExpressionEqual(
                M.Head(M.Tail(evidence)())(),
                M.Head(M.Tail(M.Tail(evidence)())())(),
                registry,
            )()
            nonzero_remainder = M.NotAtom(
                M.Compare(M.Char(remainder_text), M.Char("0"))(),
            )()
            verified = M.AndAtom(identity, nonzero_remainder)()
            status = M.Char("contradiction-closed")
            if verified is M.false_value:
                status = M.Char("unclosed-residue-branch")
        self.result = M.Pair(
            M.Char("bounded-residue-branch"),
            M.Pair(
                M.Char(residue_text),
                M.Pair(
                    substitution,
                    M.Pair(
                        evidence,
                        M.Pair(status, M.Pair(verified, M.EmptyList)),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(modulus, M.Pair(variable, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BoundedResidueBranches(M.Edge):
    def __init__(self, modulus, variable, witness, residue_text, registry):
        modulus_text = IntegerText(modulus)()
        if GMPEqualText(residue_text, modulus_text)() is M.truth_value:
            self.result = M.Pair(
                M.EmptyList, M.Pair(M.truth_value, M.EmptyList),
            )
        else:
            branch = BoundedResidueBranch(
                modulus, variable, witness, residue_text, registry,
            )()
            tail = BoundedResidueBranches(
                modulus,
                variable,
                witness,
                GMPSuccText(residue_text)(),
                registry,
            )()
            branches = M.Pair(branch, M.Head(tail)())
            branch_verified = M.Head(
                M.Tail(
                    M.Tail(M.Tail(M.Tail(M.Tail(branch)())())())(),
                )(),
            )()
            all_verified = M.AndAtom(
                branch_verified,
                M.Head(M.Tail(tail)())(),
            )()
            self.result = M.Pair(
                branches, M.Pair(all_verified, M.EmptyList),
            )
        super().__init__(inputs=M.Pair(modulus, M.Pair(variable, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BuildBoundedResidueCaseSplit(M.Edge):
    def __init__(self, modulus, variable, registry):
        modulus_text = IntegerText(modulus)()
        witness = ModulusWitnessVariable(modulus, variable)()
        built = BoundedResidueBranches(
            modulus, variable, witness, "0", registry,
        )()
        branches = M.Head(built)()
        all_verified = M.Head(M.Tail(built)())()
        bounded = M.AndAtom(
            M.NotAtom(M.Compare(M.Char(modulus_text), M.Char("0"))())(),
            M.NotAtom(M.Compare(M.Char(modulus_text), M.Char("1"))())(),
        )()
        if M.AndAtom(all_verified, bounded)() is M.truth_value:
            self.result = M.Pair(
                M.Char("bounded-residue-case-split"),
                M.Pair(
                    modulus,
                    M.Pair(
                        variable,
                        M.Pair(
                            branches,
                            M.Pair(
                                M.Pair(
                                    M.Char("domain-axiom"),
                                    M.Pair(M.Char("finite-residue-exhaustiveness"), M.EmptyList),
                                ),
                                M.Pair(M.Char("proved"), M.EmptyList),
                            ),
                        ),
                    ),
                ),
            )
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(modulus, M.Pair(variable, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BoundedResidueImplicationGoal(M.Edge):
    def __init__(self, modulus, variable):
        self.result = M.Pair(
            M.Char("modulus-divides-square-implies-base"),
            M.Pair(modulus, M.Pair(variable, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(modulus, M.Pair(variable, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BoundedResidueCaseLemma(M.Edge):
    def __init__(self, modulus, variable, registry):
        split = BuildBoundedResidueCaseSplit(modulus, variable, registry)()
        if M.IdentityCompare(split, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            goal = BoundedResidueImplicationGoal(modulus, variable)()
            certificate = M.Pair(
                M.Char("invention-evidence"),
                M.Pair(
                    split,
                    M.Pair(
                        M.Char("bounded-modulus-residue-split"),
                        M.Pair(M.Char("proved"), M.EmptyList),
                    ),
                ),
            )
            self.result = InventedLemma(
                goal, goal, M.EmptyList,
                M.Char("verified-bounded-residue-case-split"),
                M.Zero,
                certificate,
            )()
        super().__init__(inputs=M.Pair(modulus, M.Pair(variable, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FindBoundedResidueLemma(M.Edge):
    def __init__(self, nodes, modulus, registry):
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
                            if M.Compare(
                                M.Head(structural)(),
                                M.Char("bounded-residue-case-split"),
                            )() is M.truth_value:
                                found = CanonicalExpressionEqual(
                                    M.Head(M.Tail(structural)())(),
                                    modulus,
                                    registry,
                                )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindBoundedResidueLemma(
                    M.Tail(nodes)(), modulus, registry,
                )()
        super().__init__(inputs=M.Pair(nodes, M.Pair(modulus, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class StoredResidueBranchesVerified(M.Edge):
    def __init__(self, branches):
        if M.IdentityCompare(branches, M.EmptyList)() is M.truth_value:
            self.result = M.truth_value
        else:
            branch = M.Head(branches)()
            verified = M.Head(
                M.Tail(
                    M.Tail(M.Tail(M.Tail(M.Tail(branch)())())())(),
                )(),
            )()
            self.result = M.AndAtom(
                verified,
                StoredResidueBranchesVerified(M.Tail(branches)())(),
            )()
        super().__init__(inputs=M.Pair(branches, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplayBoundedResidueLemma(M.Edge):
    def __init__(self, lemma, modulus, variable, premise, registry):
        self.result = M.EmptyList
        certificate = InventedLemmaCertificate(lemma)()
        structural = M.Head(M.Tail(certificate)())()
        stored_modulus = M.Head(M.Tail(structural)())()
        stored_variable = M.Head(M.Tail(M.Tail(structural)())())()
        rebuilt_stored = BuildBoundedResidueCaseSplit(
            stored_modulus, stored_variable, registry,
        )()
        rebuilt = BuildBoundedResidueCaseSplit(
            modulus, variable, registry,
        )()
        stored_branches = M.Head(
            M.Tail(M.Tail(M.Tail(structural)())())(),
        )()
        branch_count = MachineChainCardinalityText(stored_branches)()
        stored_valid = M.AndAtom(
            M.NotAtom(M.IdentityCompare(rebuilt_stored, M.EmptyList)())(),
            M.AndAtom(
                M.Compare(
                    M.Char(branch_count), M.Char(IntegerText(stored_modulus)()),
                )(),
                StoredResidueBranchesVerified(stored_branches)(),
            )(),
        )()
        premise_modulus = CanonicalExpressionEqual(
            DividesDivisor(premise)(), modulus, registry,
        )()
        premise_square = CanonicalExpressionEqual(
            DividesDividend(premise)(), SquareExpression(variable)(), registry,
        )()
        if M.AndAtom(
            stored_valid,
            M.AndAtom(
                M.AndAtom(premise_modulus, premise_square)(),
                M.NotAtom(M.IdentityCompare(rebuilt, M.EmptyList)())(),
            )(),
        )() is M.truth_value:
            conclusion = WitnessedDivides(
                modulus, variable, ModulusWitnessVariable(modulus, variable)(),
            )()
            self.result = M.Pair(
                M.Char("invented-lemma-replay-derivation"),
                M.Pair(
                    conclusion,
                    M.Pair(
                        lemma,
                        M.Pair(
                            rebuilt,
                            M.Pair(
                                premise,
                                M.Pair(
                                    M.Char("finite-residue-exhaustiveness"),
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
                BoundedPolynomialVariables(M.Head(M.Tail(M.Tail(M.Tail(fact)())())())())(),
            )(),
        )()
        premise = NormalizeCanonicalPolynomial(
            SubstituteExpression(EquationResidual(equation)(), substitutions)(),
            variables,
            registry,
        )()
        fact_equation = ExpressionEquality(
            DividesDividend(fact)(),
            ProductExpression(
                DividesDivisor(fact)(),
                M.Head(M.Tail(M.Tail(M.Tail(fact)())())())(),
            )(),
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


class CoupledBoundedResidueGoal(M.Edge):
    def __init__(self, modulus, equation):
        self.result = M.Pair(
            M.Char("coupled-bounded-residue-goal"),
            M.Pair(modulus, M.Pair(equation, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(modulus, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CoupledBoundedResidueProof(M.Edge):
    def __init__(self, modulus, equation, case_lemma, registry):
        self.result = M.EmptyList
        variables = BoundedPolynomialVariables(equation)()
        if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.false_value:
                first = M.Head(variables)()
                second = M.Head(M.Tail(variables)())()
                first_fact = WitnessedDivides(
                    modulus, SquareExpression(first)(), SquareExpression(second)(),
                )()
                first_ok = EquationEntailsDivisibility(
                    equation, first_fact, M.EmptyList, registry,
                )()
                first_replay = ReplayBoundedResidueLemma(
                    case_lemma, modulus, first, first_fact, registry,
                )()
                witness = ModulusWitnessVariable(modulus, first)()
                substitution = M.Pair(
                    SubstitutionEntry(
                        first, ProductExpression(modulus, witness)(),
                    )(),
                    M.EmptyList,
                )
                second_fact = WitnessedDivides(
                    modulus, SquareExpression(second)(), SquareExpression(witness)(),
                )()
                second_ok = EquationEntailsDivisibility(
                    equation, second_fact, substitution, registry,
                )()
                second_replay = ReplayBoundedResidueLemma(
                    case_lemma, modulus, second, second_fact, registry,
                )()
                if M.AndAtom(first_ok, second_ok)() is M.truth_value:
                    if M.AndAtom(
                        M.NotAtom(M.IdentityCompare(first_replay, M.EmptyList)())(),
                        M.NotAtom(M.IdentityCompare(second_replay, M.EmptyList)())(),
                    )() is M.truth_value:
                        self.result = M.Pair(
                            M.Char("coupled-bounded-residue-derivation"),
                            M.Pair(
                                CoupledBoundedResidueGoal(modulus, equation)(),
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


class CoupledBoundedResidueLemma(M.Edge):
    def __init__(self, modulus, equation, case_lemma, proof):
        goal = CoupledBoundedResidueGoal(modulus, equation)()
        certificate = M.Pair(
            M.Char("coupled-bounded-residue-certificate"),
            M.Pair(
                modulus,
                M.Pair(equation, M.Pair(case_lemma, M.Pair(proof, M.EmptyList))),
            ),
        )
        self.result = InventedLemma(
            goal, goal, proof, M.Char("proved"), M.Zero, certificate,
        )()
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FindCoupledBoundedResidueLemma(M.Edge):
    def __init__(self, nodes, modulus, registry):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            node = M.Head(nodes)()
            found = M.false_value
            if IsInventedLemma(node)() is M.truth_value:
                certificate = InventedLemmaCertificate(node)()
                if M.IsPair(certificate)() is M.truth_value:
                    if M.Compare(
                        M.Head(certificate)(),
                        M.Char("coupled-bounded-residue-certificate"),
                    )() is M.truth_value:
                        found = CanonicalExpressionEqual(
                            M.Head(M.Tail(certificate)())(), modulus, registry,
                        )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindCoupledBoundedResidueLemma(
                    M.Tail(nodes)(), modulus, registry,
                )()
        super().__init__(inputs=M.Pair(nodes, M.Pair(modulus, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class VerifyModulusPositiveSquareOrder(M.Edge):
    def __init__(self, modulus, equation, lesser, greater, positivity, registry):
        expected = ExpressionEquality(
            SquareExpression(greater)(),
            ProductExpression(modulus, SquareExpression(lesser)())(),
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
        self.result = M.AndAtom(
            CanonicalPolynomialScalarEqual(
                given, expected_polynomial, variables,
            )(),
            positivity,
        )()
        super().__init__(inputs=M.Pair(equation, M.Pair(lesser, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsModulusSquareEquation(M.Edge):
    def __init__(self, modulus, equation, registry):
        variables = BoundedPolynomialVariables(equation)()
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            expected = ExpressionEquality(
                SquareExpression(M.Head(variables)())(),
                ProductExpression(
                    modulus,
                    SquareExpression(M.Head(M.Tail(variables)())())(),
                )(),
            )()
            given = NormalizeCanonicalPolynomial(
                EquationResidual(equation)(), variables, registry,
            )()
            expected_polynomial = NormalizeCanonicalPolynomial(
                EquationResidual(expected)(), variables, registry,
            )()
            self.result = CanonicalPolynomialScalarEqual(
                given, expected_polynomial, variables,
            )()
        super().__init__(inputs=M.Pair(modulus, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsSquaredModulusSquareEquation(M.Edge):
    def __init__(self, modulus, equation, registry):
        variables = BoundedPolynomialVariables(equation)()
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            squared_modulus = ProductExpression(modulus, modulus)()
            expected = ExpressionEquality(
                SquareExpression(M.Head(variables)())(),
                ProductExpression(
                    squared_modulus,
                    SquareExpression(M.Head(M.Tail(variables)())())(),
                )(),
            )()
            given = NormalizeCanonicalPolynomial(
                EquationResidual(equation)(), variables, registry,
            )()
            expected_polynomial = NormalizeCanonicalPolynomial(
                EquationResidual(expected)(), variables, registry,
            )()
            self.result = CanonicalPolynomialScalarEqual(
                given, expected_polynomial, variables,
            )()
        super().__init__(inputs=M.Pair(modulus, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FindBoundedResidueModulusForEquation(M.Edge):
    def __init__(self, nodes, equation, registry):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            node = M.Head(nodes)()
            modulus = M.EmptyList
            if IsInventedLemma(node)() is M.truth_value:
                certificate = InventedLemmaCertificate(node)()
                if M.IsPair(certificate)() is M.truth_value:
                    if M.Compare(
                        M.Head(certificate)(), M.Char("invention-evidence"),
                    )() is M.truth_value:
                        structural = M.Head(M.Tail(certificate)())()
                        if M.IsPair(structural)() is M.truth_value:
                            if M.Compare(
                                M.Head(structural)(),
                                M.Char("bounded-residue-case-split"),
                            )() is M.truth_value:
                                candidate = M.Head(M.Tail(structural)())()
                                family = M.OrAtom(
                                    IsModulusSquareEquation(candidate, equation, registry)(),
                                    IsSquaredModulusSquareEquation(candidate, equation, registry)(),
                                )()
                                if family is M.truth_value:
                                    modulus = candidate
            if M.IdentityCompare(modulus, M.EmptyList)() is M.false_value:
                self.result = modulus
            else:
                self.result = FindBoundedResidueModulusForEquation(
                    M.Tail(nodes)(), equation, registry,
                )()
        super().__init__(inputs=M.Pair(nodes, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GenBoundedModulusDescentMap(M.Edge):
    def __init__(self, modulus, equation, coupled_lemma, case_lemma, positivity, registry):
        self.result = M.EmptyList
        variables = BoundedPolynomialVariables(equation)()
        if positivity is M.truth_value:
            if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.false_value:
                    first = M.Head(variables)()
                    second = M.Head(M.Tail(variables)())()
                    witness = ModulusWitnessVariable(modulus, first)()
                    witness_substitution = M.Pair(
                        SubstitutionEntry(
                            first, ProductExpression(modulus, witness)(),
                        )(),
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
                    reproduction = CanonicalPolynomialScalarEqual(
                        transformed, reproduced, map_variables,
                    )()
                    first_order = VerifyModulusPositiveSquareOrder(
                        modulus, equation, second, first, positivity, registry,
                    )()
                    descended = SubstituteExpression(equation, map_substitution)()
                    second_order = VerifyModulusPositiveSquareOrder(
                        modulus, descended, witness, second, positivity, registry,
                    )()
                    dependencies = M.false_value
                    if M.AndAtom(
                        M.NotAtom(M.IdentityCompare(coupled_lemma, M.EmptyList)())(),
                        M.NotAtom(M.IdentityCompare(case_lemma, M.EmptyList)())(),
                    )() is M.truth_value:
                        coupled_ok = TermsAlphaEquivalent(
                            InventedLemmaGoal(coupled_lemma)(),
                            CoupledBoundedResidueGoal(modulus, equation)(),
                        )()
                        case_ok = CanonicalExpressionEqual(
                            M.Head(M.Tail(InventedLemmaGoal(case_lemma)())())(),
                            modulus,
                            registry,
                        )()
                        dependencies = M.AndAtom(coupled_ok, case_ok)()
                    if M.AndAtom(
                        reproduction,
                        M.AndAtom(
                            dependencies,
                            M.AndAtom(first_order, second_order)(),
                        )(),
                    )() is M.truth_value:
                        self.result = M.Pair(
                            M.Char("discovered-bounded-modulus-descent-map"),
                            M.Pair(
                                modulus,
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
                            ),
                        )
        super().__init__(inputs=M.Pair(modulus, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class NoPositiveModulusSolutionGoal(M.Edge):
    def __init__(self, modulus, equation):
        self.result = M.Pair(
            M.Char("no-positive-modulus-solution"),
            M.Pair(modulus, M.Pair(equation, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(modulus, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BoundedModulusDescentLemma(M.Edge):
    def __init__(self, modulus, equation, descent_map, coupled_lemma, case_lemma):
        goal = NoPositiveModulusSolutionGoal(modulus, equation)()
        certificate = M.Pair(
            M.Char("bounded-modulus-descent-certificate"),
            M.Pair(
                modulus,
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
            ),
        )
        self.result = InventedLemma(
            goal, goal, M.EmptyList,
            M.Char("verified-bounded-modulus-descent"), M.Zero, certificate,
        )()
        super().__init__(inputs=M.Pair(modulus, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FindBoundedModulusDescentLemma(M.Edge):
    def __init__(self, nodes, modulus, registry):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            node = M.Head(nodes)()
            found = M.false_value
            if IsInventedLemma(node)() is M.truth_value:
                certificate = InventedLemmaCertificate(node)()
                if M.IsPair(certificate)() is M.truth_value:
                    if M.Compare(
                        M.Head(certificate)(),
                        M.Char("bounded-modulus-descent-certificate"),
                    )() is M.truth_value:
                        found = CanonicalExpressionEqual(
                            M.Head(M.Tail(certificate)())(), modulus, registry,
                        )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindBoundedModulusDescentLemma(
                    M.Tail(nodes)(), modulus, registry,
                )()
        super().__init__(inputs=M.Pair(nodes, M.Pair(modulus, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ReplayBoundedModulusDescentLemma(M.Edge):
    def __init__(self, lemma, modulus, equation, nodes, positivity, registry):
        case_lemma = FindBoundedResidueLemma(nodes, modulus, registry)()
        coupled_lemma = FindCoupledBoundedResidueLemma(nodes, modulus, registry)()
        status = M.Char("proved")
        regenerated = M.EmptyList
        if M.IdentityCompare(case_lemma, M.EmptyList)() is M.truth_value:
            status = M.Char("missing-bounded-residue-dependency")
        elif M.IdentityCompare(coupled_lemma, M.EmptyList)() is M.truth_value:
            status = M.Char("missing-coupled-residue-dependency")
        else:
            certificate = InventedLemmaCertificate(lemma)()
            expected_coupled = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(certificate)())())())(),
            )()
            expected_case = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(certificate)())())())())(),
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
                regenerated = GenBoundedModulusDescentMap(
                    modulus, equation, coupled_lemma, case_lemma,
                    positivity, registry,
                )()
            if M.IdentityCompare(regenerated, M.EmptyList)() is M.truth_value:
                status = M.Char("strict-decrease-unresolved")
        if M.Compare(status, M.Char("proved"))() is M.truth_value:
            self.result = M.Pair(
                M.Char("invented-lemma-replay-derivation"),
                M.Pair(
                    NoPositiveModulusSolutionGoal(modulus, equation)(),
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
                M.Char("bounded-modulus-descent-replay-failure"),
                M.Pair(status, M.EmptyList),
            )
        super().__init__(inputs=M.Pair(lemma, M.Pair(equation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result
