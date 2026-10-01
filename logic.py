from __future__ import annotations

from .core import Atom, Edge, EmptyList, Pair, Thingy, false_value, truth_value


class TrueAtom(Atom):
    def __call__(self):
        return truth_value


class FalseAtom(Atom):
    def __call__(self):
        return false_value


class NandAtom(Edge):
    """The boolean primitive every other connective is built from.

    These four edges each allocated a Thingy for a result that __call__
    immediately overwrote, plus a Pair chain of inputs that nothing ever
    read -- the same defect as IdentityCompare, and costlier here because
    the connectives call each other: OrAtom is two NotAtoms and a
    NandAtom, so one boolean cost 131us and seven allocations.

    Results are now assigned directly and inputs left empty. Every call
    site in the codebase is Atom(...)(); none binds an edge or reads
    .result before calling it.
    """

    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.result = false_value
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        if self.a is truth_value and self.b is truth_value:
            self.result = false_value
        else:
            self.result = truth_value
        return self.result


class AndAtom(Edge):
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.result = false_value
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        temp = NandAtom(self.a, self.b)()
        self.result = NandAtom(temp, temp)()
        return self.result


class NotAtom(Edge):
    def __init__(self, a):
        self.a = a
        self.result = false_value
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        self.result = NandAtom(self.a, self.a)()
        return self.result


class OrAtom(Edge):
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.result = false_value
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        na = NotAtom(self.a)()
        nb = NotAtom(self.b)()
        self.result = NandAtom(na, nb)()
        return self.result


def sync_from_namespace(namespace):
    for name in (
        "truth_value",
        "false_value",
        "EmptyList",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_")]
