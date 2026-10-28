"""Concrete quadratic division witnesses, with independent refusal controls.

Run through the activated environment: python -B -u -m hyge.validation.quadratic_division_regressions
This checks arithmetic substrate only; no UFD or descent theorem is claimed.
"""

from hyge import labels as L
from hyge import machine as M
from hyge import trees as T
from hyge.math.quadratic_division import VerifyQuadraticDivision
from hyge.runtime import make_fresh_runtime


class CheckQuadraticDivision(M.Edge):
    def __init__(self, alpha, beta, quotient, remainder, p, q, registry, expected):
        checked = VerifyQuadraticDivision(alpha, beta, quotient, remainder, p, q, registry)()
        assert M.IsPair(checked)() is M.truth_value
        assert M.Head(checked)() is expected
        assert M.IsPair(M.Tail(checked)())() is M.truth_value
        assert M.Tail(M.Tail(checked)())() is M.EmptyList
        updated = M.Head(M.Tail(checked)())()
        assert T.IsTree(updated)() is M.truth_value
        super().__init__(inputs=M.Pair(checked, M.Pair(expected, M.EmptyList)), results=updated)


runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
built = M.Whole(M.Zero, M.Zero, registry)()
zero = M.Head(built)()
registry = M.Head(M.Tail(built)())()
built = M.Whole(M.one, M.Zero, registry)()
one = M.Head(built)()
registry = M.Head(M.Tail(built)())()
built = M.Whole(M.Zero, M.one, registry)()
minus_one = M.Head(built)()
registry = M.Head(M.Tail(built)())()
built = M.Whole(M.two, M.Zero, registry)()
two = M.Head(built)()
registry = M.Head(M.Tail(built)())()
built = M.Whole(M.three, M.Zero, registry)()
three = M.Head(built)()
registry = M.Head(M.Tail(built)())()

zero_element = M.Pair(zero, M.Pair(zero, M.EmptyList))
unit = M.Pair(one, M.Pair(zero, M.EmptyList))
omega = M.Pair(zero, M.Pair(one, M.EmptyList))
two_element = M.Pair(two, M.Pair(zero, M.EmptyList))
alpha = M.Pair(three, M.Pair(one, M.EmptyList))
beta = M.Pair(one, M.Pair(minus_one, M.EmptyList))
quotient = M.Pair(one, M.Pair(one, M.EmptyList))
exact_alpha = M.Pair(two, M.Pair(one, M.EmptyList))

# Eisenstein: (3+w) = (1-w)(1+w)+1, with norms 3 and 1.
registry = CheckQuadraticDivision(alpha, beta, quotient, unit,
    minus_one, minus_one, registry, M.truth_value)()
registry = CheckQuadraticDivision(exact_alpha, beta, quotient, zero_element,
    minus_one, minus_one, registry, M.truth_value)()
registry = CheckQuadraticDivision(zero_element, beta, zero_element, zero_element,
    minus_one, minus_one, registry, M.truth_value)()
print("PASS Eisenstein division, exact division and zero dividend")

# Change each component independently; no search result or claimed norm is trusted.
registry = CheckQuadraticDivision(exact_alpha, beta, quotient, unit,
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, unit, quotient, unit,
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, unit, unit,
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, quotient, zero_element,
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, quotient, unit,
    zero, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, quotient, unit,
    minus_one, zero, registry, M.false_value)()
print("PASS changed dividend, divisor, quotient, remainder and relation are refused")

# These satisfy the division equation but fail an independent norm obligation.
registry = CheckQuadraticDivision(unit, zero_element, zero_element, unit,
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(beta, beta, zero_element, beta,
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, zero_element, alpha,
    minus_one, minus_one, registry, M.false_value)()
# In w*w=1, w has negative norm and 1+w has zero norm despite being nonzero.
registry = CheckQuadraticDivision(omega, omega, unit, zero_element,
    one, zero, registry, M.false_value)()
registry = CheckQuadraticDivision(quotient, quotient, unit, zero_element,
    one, zero, registry, M.false_value)()
registry = CheckQuadraticDivision(omega, two_element, zero_element, omega,
    one, zero, registry, M.false_value)()
print("PASS zero divisor, equal or larger norms, nonpositive divisor norms and negative remainder norm are refused")

# Gaussian: (2+i) = (1+i)*1+1, with norms 2 and 1.
registry = CheckQuadraticDivision(exact_alpha, quotient, unit, unit,
    minus_one, zero, registry, M.truth_value)()
registry = CheckQuadraticDivision(quotient, quotient, unit, zero_element,
    minus_one, zero, registry, M.truth_value)()
print("PASS Gaussian division and exact division under a different relation")

before_malformed = registry
registry = CheckQuadraticDivision(M.EmptyList, beta, quotient, unit,
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, M.Atom(), quotient, unit,
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, M.Pair(one, M.EmptyList), unit,
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, quotient, M.Pair(one, zero),
    minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(M.Pair(three, M.Pair(one, M.Pair(zero, M.EmptyList))),
    beta, quotient, unit, minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(M.Pair(M.three, M.Pair(one, M.EmptyList)),
    beta, quotient, unit, minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, quotient, unit,
    M.one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, quotient, unit,
    minus_one, M.EmptyList, registry, M.false_value)()
assert registry is before_malformed
print("PASS malformed element shapes and wrong coordinate or relation sorts are refused before arithmetic")

# Even a registered Whole label is insufficient when its constructor is malformed.
malformed = M.ConstructedBy(M.Atom(), L.WholeLabel, M.Pair(M.one, M.EmptyList), registry)()
bad_whole = M.Head(malformed)()
registry = M.Head(M.Tail(malformed)())()
before_malformed = registry
registry = CheckQuadraticDivision(M.Pair(bad_whole, M.Pair(one, M.EmptyList)),
    beta, quotient, unit, minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, quotient, unit,
    bad_whole, minus_one, registry, M.false_value)()
assert registry is before_malformed
malformed = M.ConstructedBy(M.Atom(), L.WholeLabel,
    M.Pair(M.truth_value, M.Pair(M.Zero, M.EmptyList)), registry)()
bad_coordinate = M.Head(malformed)()
registry = M.Head(M.Tail(malformed)())()
before_malformed = registry
registry = CheckQuadraticDivision(M.Pair(bad_coordinate, M.Pair(one, M.EmptyList)),
    beta, quotient, unit, minus_one, minus_one, registry, M.false_value)()
registry = CheckQuadraticDivision(alpha, beta, quotient, unit,
    minus_one, bad_coordinate, registry, M.false_value)()
assert registry is before_malformed
print("PASS malformed registered Whole constructors and non-Nat coordinates are refused")

# Whole coordinates denote differences, so a different representation must replay.
built = M.Whole(M.one, M.one, registry)()
alias_zero = M.Head(built)()
registry = M.Head(M.Tail(built)())()
built = M.Whole(M.two, M.one, registry)()
alias_one = M.Head(built)()
registry = M.Head(M.Tail(built)())()
built = M.Whole(M.one, M.two, registry)()
alias_minus_one = M.Head(built)()
registry = M.Head(M.Tail(built)())()
built = M.Whole(M.four, M.one, registry)()
alias_three = M.Head(built)()
registry = M.Head(M.Tail(built)())()
alias_alpha = M.Pair(alias_three, M.Pair(alias_one, M.EmptyList))
alias_beta = M.Pair(alias_one, M.Pair(alias_minus_one, M.EmptyList))
alias_quotient = M.Pair(alias_one, M.Pair(alias_one, M.EmptyList))
alias_remainder = M.Pair(alias_one, M.Pair(alias_zero, M.EmptyList))
registry = CheckQuadraticDivision(alias_alpha, alias_beta, alias_quotient, alias_remainder,
    alias_minus_one, alias_minus_one, registry, M.truth_value)()
print("PASS equivalent noncanonical Whole coordinates and relation coefficients")
print("Quadratic division regressions passed.")
