from __future__ import annotations

import gmpy2

from .core import (
    Atom,
    DIGIT_0,
    DIGIT_1,
    DIGIT_2,
    DIGIT_3,
    DIGIT_4,
    DIGIT_5,
    DIGIT_6,
    DIGIT_7,
    DIGIT_8,
    DIGIT_9,
    Edge,
    EmptyList,
    Pair,
    false_value,
    truth_value,
)


class GMPRepTag(Atom):
    pass


GMPRepTag = GMPRepTag()


class GMPHostMath:
    def _mpz_value(self, value):
        if value == "":
            return gmpy2.mpz("0")
        return gmpy2.mpz(value)

    def _zero_value(self):
        return gmpy2.mpz("0")

    def _one_value(self):
        return gmpy2.mpz("1")


class GMPRep(Atom, GMPHostMath):
    def __init__(self, value):
        super().__init__()
        self.value = self._mpz_value(value)


class GMPRepText(Edge):
    def __init__(self, rep):
        self.result = str(rep())
        super().__init__(inputs=Pair(rep, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NormalizeGMPText(Edge, GMPHostMath):
    def __init__(self, text):
        self.result = str(self._mpz_value(text))
        super().__init__(inputs=Pair(text, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GMPSuccText(Edge, GMPHostMath):
    def __init__(self, text):
        self.result = str(self._mpz_value(text) + self._one_value())
        super().__init__(inputs=Pair(text, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GMPPredText(Edge, GMPHostMath):
    def __init__(self, text):
        value = self._mpz_value(text)
        if value <= self._zero_value():
            self.result = "0"
        else:
            self.result = str(value - self._one_value())
        super().__init__(inputs=Pair(text, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GMPEqualText(Edge, GMPHostMath):
    def __init__(self, left, right):
        if self._mpz_value(left) == self._mpz_value(right):
            self.result = truth_value
        else:
            self.result = false_value
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GMPLessText(Edge, GMPHostMath):
    def __init__(self, left, right):
        if self._mpz_value(left) < self._mpz_value(right):
            self.result = truth_value
        else:
            self.result = false_value
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GMPAddText(Edge, GMPHostMath):
    def __init__(self, left, right):
        self.result = str(self._mpz_value(left) + self._mpz_value(right))
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GMPSubText(Edge, GMPHostMath):
    def __init__(self, left, right):
        self.result = str(self._mpz_value(left) - self._mpz_value(right))
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GMPMulByDigitText(Edge, GMPHostMath):
    def __init__(self, text, digit):
        self.result = str(self._mpz_value(text) * self._mpz_value(digit))
        super().__init__(inputs=Pair(text, Pair(digit, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GMPMulText(Edge, GMPHostMath):
    def __init__(self, left, right):
        self.result = str(self._mpz_value(left) * self._mpz_value(right))
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GMPAbsText(Edge, GMPHostMath):
    def __init__(self, text):
        value = self._mpz_value(text)
        if value < self._zero_value():
            value = -value
        self.result = str(value)
        super().__init__(inputs=Pair(text, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GMPIsNegativeText(Edge, GMPHostMath):
    def __init__(self, text):
        if self._mpz_value(text) < self._zero_value():
            self.result = truth_value
        else:
            self.result = false_value
        super().__init__(inputs=Pair(text, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GMPQuadraticPSDText(Edge, GMPHostMath):
    """Decide a*x^2 + b*x*y + c*y^2 >= 0 over the reals."""

    def __init__(self, a_text, b_text, c_text):
        a = self._mpz_value(a_text)
        b = self._mpz_value(b_text)
        c = self._mpz_value(c_text)
        if a < 0:
            self.result = false_value
        elif c < 0:
            self.result = false_value
        elif b * b <= 4 * a * c:
            self.result = truth_value
        else:
            self.result = false_value
        super().__init__(
            inputs=Pair(a_text, Pair(b_text, Pair(c_text, EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GMPExactQuotientText(Edge, GMPHostMath):
    def __init__(self, dividend, divisor):
        divisor_value = self._mpz_value(divisor)
        dividend_value = self._mpz_value(dividend)
        if divisor_value == self._zero_value():
            self.result = ""
        elif dividend_value % divisor_value != self._zero_value():
            self.result = ""
        else:
            self.result = str(dividend_value // divisor_value)
        super().__init__(
            inputs=Pair(dividend, Pair(divisor, EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GMPRepDigitList(Edge):
    def __init__(self, rep):
        self.result = self._digits(rep)
        super().__init__(inputs=Pair(rep, EmptyList), results=self.result)

    def _digit_atom(self, ch):
        if ch == "0":
            return DIGIT_0
        if ch == "1":
            return DIGIT_1
        if ch == "2":
            return DIGIT_2
        if ch == "3":
            return DIGIT_3
        if ch == "4":
            return DIGIT_4
        if ch == "5":
            return DIGIT_5
        if ch == "6":
            return DIGIT_6
        if ch == "7":
            return DIGIT_7
        if ch == "8":
            return DIGIT_8
        if ch == "9":
            return DIGIT_9
        return DIGIT_0

    def _digits(self, rep):
        text = str(rep())
        out = EmptyList
        idx = len(text)
        while idx > 0:
            idx = idx - 1
            ch = text[idx]
            if ch != "-":
                out = Pair(self._digit_atom(ch), out)
        if out is EmptyList:
            return Pair(DIGIT_0, EmptyList)
        return out

    def __call__(self):
        return self.result


def sync_from_namespace(namespace):
    for name in (
        "EmptyList",
        "truth_value",
        "false_value",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [
    "GMPRepTag",
    "GMPHostMath",
    "GMPRep",
    "GMPRepText",
    "NormalizeGMPText",
    "GMPSuccText",
    "GMPPredText",
    "GMPEqualText",
    "GMPLessText",
    "GMPAddText",
    "GMPSubText",
    "GMPMulByDigitText",
    "GMPMulText",
    "GMPAbsText",
    "GMPIsNegativeText",
    "GMPQuadraticPSDText",
    "GMPExactQuotientText",
    "GMPRepDigitList",
]
