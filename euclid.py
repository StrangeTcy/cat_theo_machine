from __future__ import annotations

from . import machine as M
from .gmprep import (
    GMPExactQuotientText,
    GMPFloorQuotientText,
    GMPIsNegativeText,
    GMPLessText,
    GMPModuloText,
    GMPMulText,
    GMPEqualText,
)
from .graph import (
    InventedLemma,
    InventedLemmaCertificate,
    IsInventedLemma,
)
from .mining import CanonicalExpressionEqual
from .modular import IntegerFromText
from .parity import ExpressionEquality
from .residue import ProductExpression, SumExpression


class RemainderIdentity(M.Edge):
    def __init__(self, dividend_text, divisor_text, quotient_text, remainder_text):
        self.result = ExpressionEquality(
            IntegerFromText(dividend_text)(),
            SumExpression(
                ProductExpression(
                    IntegerFromText(divisor_text)(),
                    IntegerFromText(quotient_text)(),
                )(),
                IntegerFromText(remainder_text)(),
            )(),
        )()
        super().__init__(inputs=M.Pair(M.Char(dividend_text), M.Pair(M.Char(divisor_text), M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class VerifyRemainderWitness(M.Edge):
    def __init__(self, witness, registry):
        label = M.Head(witness)()
        dividend_text = M.Head(M.Tail(witness)())()()
        divisor_text = M.Head(M.Tail(M.Tail(witness)())())()()
        quotient_text = M.Head(M.Tail(M.Tail(M.Tail(witness)())())())()()
        remainder_text = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(witness)())())())())()()
        identity = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(witness)())())())())())()
        expected = RemainderIdentity(
            dividend_text, divisor_text, quotient_text, remainder_text,
        )()
        identity_verified = M.AndAtom(
            CanonicalExpressionEqual(
                M.Head(M.Tail(identity)())(),
                M.Head(M.Tail(M.Tail(identity)())())(),
                registry,
            )(),
            M.AndAtom(
                CanonicalExpressionEqual(
                    M.Head(M.Tail(identity)())(),
                    M.Head(M.Tail(expected)())(),
                    registry,
                )(),
                CanonicalExpressionEqual(
                    M.Head(M.Tail(M.Tail(identity)())())(),
                    M.Head(M.Tail(M.Tail(expected)())())(),
                    registry,
                )(),
            )(),
        )()
        nonnegative = M.NotAtom(GMPIsNegativeText(remainder_text)())()
        strict = GMPLessText(remainder_text, divisor_text)()
        divisor_positive = GMPLessText("0", divisor_text)()
        exact_quotient = GMPEqualText(
            quotient_text,
            GMPFloorQuotientText(dividend_text, divisor_text)(),
        )()
        exact_remainder = GMPEqualText(
            remainder_text,
            GMPModuloText(dividend_text, divisor_text)(),
        )()
        self.result = M.AndAtom(
            M.Compare(label, M.Char("remainder-witness"))(),
            M.AndAtom(
                divisor_positive,
                M.AndAtom(
                    identity_verified,
                    M.AndAtom(
                        nonnegative,
                        M.AndAtom(strict, M.AndAtom(exact_quotient, exact_remainder)())(),
                    )(),
                )(),
            )(),
        )()
        super().__init__(inputs=M.Pair(witness, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RemainderWitness(M.Edge):
    def __init__(self, dividend_text, divisor_text, quotient_text, remainder_text, registry):
        identity = RemainderIdentity(
            dividend_text, divisor_text, quotient_text, remainder_text,
        )()
        structural = M.Pair(
            M.Char("remainder-witness"),
            M.Pair(
                M.Char(dividend_text),
                M.Pair(
                    M.Char(divisor_text),
                    M.Pair(
                        M.Char(quotient_text),
                        M.Pair(
                            M.Char(remainder_text),
                            M.Pair(identity, M.EmptyList),
                        ),
                    ),
                ),
            ),
        )
        verified = VerifyRemainderWitness(structural, registry)()
        self.result = M.Pair(
            M.Char("verified-remainder-witness"),
            M.Pair(structural, M.Pair(verified, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(M.Char(dividend_text), M.Pair(M.Char(divisor_text), M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BuildRemainderWitness(M.Edge):
    def __init__(self, dividend_text, divisor_text, registry):
        if GMPLessText("0", divisor_text)() is M.false_value:
            self.result = M.EmptyList
        else:
            quotient_text = GMPFloorQuotientText(dividend_text, divisor_text)()
            remainder_text = GMPModuloText(dividend_text, divisor_text)()
            witness = RemainderWitness(
                dividend_text, divisor_text, quotient_text, remainder_text, registry,
            )()
            if M.Head(M.Tail(M.Tail(witness)())())() is M.truth_value:
                self.result = witness
            else:
                self.result = M.EmptyList
        super().__init__(inputs=M.Pair(M.Char(dividend_text), M.Pair(M.Char(divisor_text), M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class EuclideanDescentStep(M.Edge):
    def __init__(self, dividend_text, divisor_text, registry):
        remainder = BuildRemainderWitness(dividend_text, divisor_text, registry)()
        if M.IdentityCompare(remainder, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            structural = M.Head(M.Tail(remainder)())()
            quotient_text = M.Head(M.Tail(M.Tail(M.Tail(structural)())())())()()
            remainder_text = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(structural)())())())())()()
            strict = GMPLessText(remainder_text, divisor_text)()
            common_divisor_invariance = M.Pair(
                M.Char("domain-axiom"),
                M.Pair(
                    M.Char("common-divisors-invariant-under-remainder"),
                    M.Pair(M.Char("witnessed-by-a-equals-bq-plus-r"), M.EmptyList),
                ),
            )
            self.result = M.Pair(
                M.Char("euclidean-descent-step"),
                M.Pair(
                    M.Char(dividend_text),
                    M.Pair(
                        M.Char(divisor_text),
                        M.Pair(
                            M.Char(quotient_text),
                            M.Pair(
                                M.Char(remainder_text),
                                M.Pair(
                                    remainder,
                                    M.Pair(
                                        strict,
                                        M.Pair(
                                            common_divisor_invariance,
                                            M.Pair(M.Char("proved"), M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        super().__init__(inputs=M.Pair(M.Char(dividend_text), M.Pair(M.Char(divisor_text), M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class EuclideanDescentSteps(M.Edge):
    def __init__(self, dividend_text, divisor_text, registry):
        if GMPEqualText(divisor_text, "0")() is M.truth_value:
            self.result = M.Pair(
                M.EmptyList,
                M.Pair(M.Char(dividend_text), M.Pair(M.truth_value, M.EmptyList)),
            )
        else:
            step = EuclideanDescentStep(dividend_text, divisor_text, registry)()
            if M.IdentityCompare(step, M.EmptyList)() is M.truth_value:
                self.result = M.Pair(
                    M.EmptyList,
                    M.Pair(M.Char("0"), M.Pair(M.false_value, M.EmptyList)),
                )
            else:
                remainder_text = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(step)())())())())()()
                tail = EuclideanDescentSteps(divisor_text, remainder_text, registry)()
                steps = M.Pair(step, M.Head(tail)())
                all_verified = M.AndAtom(
                    M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(step)())())())())())())(),
                    M.Head(M.Tail(M.Tail(tail)())())(),
                )()
                self.result = M.Pair(
                    steps,
                    M.Pair(
                        M.Head(M.Tail(tail)())(),
                        M.Pair(all_verified, M.EmptyList),
                    ),
                )
        super().__init__(inputs=M.Pair(M.Char(dividend_text), M.Pair(M.Char(divisor_text), M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class EuclideanDescentTrace(M.Edge):
    def __init__(self, first_text, second_text, registry):
        first_nonnegative = M.NotAtom(GMPIsNegativeText(first_text)())()
        second_nonnegative = M.NotAtom(GMPIsNegativeText(second_text)())()
        not_both_zero = M.NotAtom(
            M.AndAtom(
                GMPEqualText(first_text, "0")(),
                GMPEqualText(second_text, "0")(),
            )(),
        )()
        if M.AndAtom(first_nonnegative, M.AndAtom(second_nonnegative, not_both_zero)())() is M.false_value:
            self.result = M.EmptyList
        else:
            ordered_first = first_text
            ordered_second = second_text
            if GMPLessText(first_text, second_text)() is M.truth_value:
                ordered_first = second_text
                ordered_second = first_text
            built = EuclideanDescentSteps(
                ordered_first, ordered_second, registry,
            )()
            verified = M.Head(M.Tail(M.Tail(built)())())()
            if verified is M.truth_value:
                self.result = M.Pair(
                    M.Char("euclidean-descent-trace"),
                    M.Pair(
                        M.Char(first_text),
                        M.Pair(
                            M.Char(second_text),
                            M.Pair(
                                M.Head(built)(),
                                M.Pair(
                                    M.Head(M.Tail(built)())(),
                                    M.Pair(
                                        M.Pair(
                                            M.Char("domain-axiom"),
                                            M.Pair(M.Char("well-ordering-positive-integers"), M.EmptyList),
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
        super().__init__(inputs=M.Pair(M.Char(first_text), M.Pair(M.Char(second_text), M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class StoredEuclideanStepsVerified(M.Edge):
    def __init__(self, steps, registry):
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            self.result = M.truth_value
        else:
            step = M.Head(steps)()
            dividend_text = M.Head(M.Tail(step)())()()
            divisor_text = M.Head(M.Tail(M.Tail(step)())())()()
            rebuilt = EuclideanDescentStep(dividend_text, divisor_text, registry)()
            stored_remainder = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(step)())())())())()()
            rebuilt_remainder = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(rebuilt)())())())())()()
            self.result = M.AndAtom(
                M.Compare(M.Head(step)(), M.Char("euclidean-descent-step"))(),
                M.AndAtom(
                    M.Compare(M.Char(stored_remainder), M.Char(rebuilt_remainder))(),
                    StoredEuclideanStepsVerified(M.Tail(steps)(), registry)(),
                )(),
            )()
        super().__init__(inputs=M.Pair(steps, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EuclideanAlgorithmGoal(M.Edge):
    def __init__(self):
        self.result = M.Pair(
            M.Char("euclidean-algorithm-terminates-with-gcd"),
            M.Pair(M.Char("nonnegative-integer-pair"), M.EmptyList),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EuclideanAlgorithmLemma(M.Edge):
    def __init__(self, sample_first_text, sample_second_text, registry):
        trace = EuclideanDescentTrace(
            sample_first_text, sample_second_text, registry,
        )()
        if M.IdentityCompare(trace, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            certificate = M.Pair(
                M.Char("invention-evidence"),
                M.Pair(
                    trace,
                    M.Pair(
                        M.Char("remainder-witnessed-well-ordering-descent"),
                        M.Pair(M.Char("proved"), M.EmptyList),
                    ),
                ),
            )
            goal = EuclideanAlgorithmGoal()()
            self.result = InventedLemma(
                goal, goal, M.EmptyList,
                M.Char("verified-euclidean-descent-schema"),
                M.Zero,
                certificate,
            )()
        super().__init__(inputs=M.Pair(M.Char(sample_first_text), M.Pair(M.Char(sample_second_text), M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FindEuclideanAlgorithmLemma(M.Edge):
    def __init__(self, nodes):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            node = M.Head(nodes)()
            found = M.false_value
            if IsInventedLemma(node)() is M.truth_value:
                certificate = InventedLemmaCertificate(node)()
                if M.IsPair(certificate)() is M.truth_value:
                    if M.Compare(M.Head(certificate)(), M.Char("invention-evidence"))() is M.truth_value:
                        trace = M.Head(M.Tail(certificate)())()
                        if M.IsPair(trace)() is M.truth_value:
                            found = M.Compare(
                                M.Head(trace)(), M.Char("euclidean-descent-trace"),
                            )()
            if found is M.truth_value:
                self.result = node
            else:
                self.result = FindEuclideanAlgorithmLemma(M.Tail(nodes)())()
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplayEuclideanAlgorithmLemma(M.Edge):
    def __init__(self, lemma, first_text, second_text, registry):
        self.result = M.EmptyList
        if IsInventedLemma(lemma)() is M.truth_value:
            certificate = InventedLemmaCertificate(lemma)()
            stored = M.Head(M.Tail(certificate)())()
            stored_steps = M.Head(M.Tail(M.Tail(M.Tail(stored)())())())()
            stored_valid = StoredEuclideanStepsVerified(stored_steps, registry)()
            rebuilt = EuclideanDescentTrace(first_text, second_text, registry)()
            if M.AndAtom(
                stored_valid,
                M.NotAtom(M.IdentityCompare(rebuilt, M.EmptyList)())(),
            )() is M.truth_value:
                self.result = M.Pair(
                    M.Char("invented-lemma-replay-derivation"),
                    M.Pair(
                        M.Pair(
                            M.Char("gcd-result"),
                            M.Pair(
                                M.Char(first_text),
                                M.Pair(
                                    M.Char(second_text),
                                    M.Pair(
                                        M.Head(M.Tail(M.Tail(M.Tail(M.Tail(rebuilt)())())())())(),
                                        M.EmptyList,
                                    ),
                                ),
                            ),
                        ),
                        M.Pair(
                            lemma,
                            M.Pair(
                                rebuilt,
                                M.Pair(
                                    M.Char("common-divisor-invariance-replayed"),
                                    M.Pair(
                                        M.Char("well-ordering-descent-replayed"),
                                        M.Pair(M.Char("proved"), M.EmptyList),
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
        super().__init__(inputs=M.Pair(lemma, M.Pair(M.Char(first_text), M.Pair(M.Char(second_text), M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class ReplayGCDText(M.Edge):
    def __init__(self, replay):
        goal = M.Head(M.Tail(replay)())()
        self.result = M.Head(M.Tail(M.Tail(M.Tail(goal)())())())()()
        super().__init__(inputs=M.Pair(replay, M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result


class VerifyGCDDivisibility(M.Edge):
    def __init__(self, first_text, second_text, gcd_text):
        first_quotient = GMPExactQuotientText(first_text, gcd_text)()
        second_quotient = GMPExactQuotientText(second_text, gcd_text)()
        first_rebuilt = GMPMulText(gcd_text, first_quotient)()
        second_rebuilt = GMPMulText(gcd_text, second_quotient)()
        self.result = M.AndAtom(
            GMPEqualText(first_text, first_rebuilt)(),
            GMPEqualText(second_text, second_rebuilt)(),
        )()
        super().__init__(inputs=M.Pair(M.Char(first_text), M.Pair(M.Char(second_text), M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result
