from __future__ import annotations

from .core import Edge, EmptyList, Head, IdentityCompare, Pair, Tail, false_value, truth_value
from .logic import AndAtom
from .labels import TreePatriciaTokenLabel


class TreePatriciaTokenPayload(Edge):
    def __init__(self, token):
        self.result = EmptyList
        if IdentityCompare(token, EmptyList)() is false_value:
            self.result = Head(Tail(token)())()
        super().__init__(inputs=Pair(token, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreePatriciaTokenEqual(Edge):
    def __init__(self, left, right):
        self.result = false_value
        if IdentityCompare(left, EmptyList)() is truth_value:
            if IdentityCompare(right, EmptyList)() is truth_value:
                self.result = truth_value
        elif IdentityCompare(right, EmptyList)() is false_value:
            if IdentityCompare(Head(left)(), Head(right)())() is truth_value:
                if IdentityCompare(TreePatriciaTokenPayload(left)(), TreePatriciaTokenPayload(right)())() is truth_value:
                    self.result = truth_value
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TreePatriciaPathEqual(Edge):
    def __init__(self, left, right):
        self.result = self._equal(left, right)
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def _equal(self, left, right):
        current_left = left
        current_right = right
        while IdentityCompare(current_left, EmptyList)() is false_value:
            if IdentityCompare(current_right, EmptyList)() is truth_value:
                return false_value
            if TreePatriciaTokenEqual(Head(current_left)(), Head(current_right)())() is false_value:
                return false_value
            current_left = Tail(current_left)()
            current_right = Tail(current_right)()
        if IdentityCompare(current_right, EmptyList)() is false_value:
            return false_value
        return truth_value

    def __call__(self):
        return self.result


class TreePatriciaStripPrefix(Edge):
    def __init__(self, path, prefix):
        self.result = self._strip(path, prefix)
        super().__init__(inputs=Pair(path, Pair(prefix, EmptyList)), results=self.result)

    def _strip(self, path, prefix):
        current_path = path
        current_prefix = prefix
        while IdentityCompare(current_prefix, EmptyList)() is false_value:
            if IdentityCompare(current_path, EmptyList)() is truth_value:
                return Pair(false_value, Pair(EmptyList, EmptyList))
            if TreePatriciaTokenEqual(Head(current_path)(), Head(current_prefix)())() is false_value:
                return Pair(false_value, Pair(EmptyList, EmptyList))
            current_path = Tail(current_path)()
            current_prefix = Tail(current_prefix)()
        return Pair(truth_value, Pair(current_path, EmptyList))

    def __call__(self):
        return self.result


class TreePatriciaLongestCommonPrefix(Edge):
    def __init__(self, left, right):
        self.result = self._walk(left, right)
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def _reverse(self, chain):
        current = chain
        out = EmptyList
        while IdentityCompare(current, EmptyList)() is false_value:
            out = Pair(Head(current)(), out)
            current = Tail(current)()
        return out

    def _walk(self, left, right):
        common_rev = EmptyList
        current_left = left
        current_right = right
        while IdentityCompare(current_left, EmptyList)() is false_value:
            if IdentityCompare(current_right, EmptyList)() is truth_value:
                return Pair(self._reverse(common_rev), Pair(current_left, Pair(current_right, EmptyList)))
            if TreePatriciaTokenEqual(Head(current_left)(), Head(current_right)())() is false_value:
                return Pair(self._reverse(common_rev), Pair(current_left, Pair(current_right, EmptyList)))
            common_rev = Pair(Head(current_left)(), common_rev)
            current_left = Tail(current_left)()
            current_right = Tail(current_right)()
        return Pair(self._reverse(common_rev), Pair(current_left, Pair(current_right, EmptyList)))

    def __call__(self):
        return self.result
