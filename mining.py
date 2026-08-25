from __future__ import annotations

from . import machine as M
from .gmprep import GMPSuccText

class MineNatFromGMPRep(M.Edge):
    """Convert a GMP machine value to a cached machine Nat."""

    def __init__(self, rep):
        result = M.Atom()
        result.value = rep
        self.result = result
        super().__init__(inputs=M.Pair(rep, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MineNatSuccessor(M.Edge):
    """Increment a mining Nat without materializing a deep successor key."""

    def __init__(self, number, registry):
        rep = M.NatRepOf(number, registry)()
        next_text = GMPSuccText(M.GMPRepText(rep)())()
        successor = MineNatFromGMPRep(M.GMPRep(next_text))()
        self.result = M.Pair(successor, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(number, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


__all__ = ("MineNatFromGMPRep", "MineNatSuccessor")
