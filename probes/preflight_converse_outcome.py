"""Pre-flight 2026-09-04: Converse outcome shape on the canonical equality query.

Drives DefaultCorrespondenceVocabulary + Converse on "is two plus two equal
to four" and prints the outcome label, the structured reason label, and the
reason payload head. Evidence for defect ledger entries D1/D2 (see
verification/preflight_2026-09-04.md): the outcome is NotUnderstood with
ReasonNoCorrespondence -- a three-slot term -- while ConversePropositionTest
historically read four tails off it during suite install.

Run: PYTHONPATH=/home/user python3 probes/preflight_converse_outcome.py
"""
import sys

sys.path.insert(0, "/home/user")

import cat_theo_machine.machine as M
import cat_theo_machine.graph as Gmod
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
from cat_theo_machine.runtime import boot_from_packs


def main():
    runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    graph = runtime.graph
    graph._search_disable_console = M.truth_value
    registry = M.FromContextGetConstructors(graph)()
    empty = M.EmptyList
    vocabulary = Gmod.DefaultCorrespondenceVocabulary()()
    surface = Gmod.Surface(M.Pair(M.Char("is"), M.Pair(M.Char("two"), M.Pair(M.Char("plus"),
        M.Pair(M.Char("two"), M.Pair(M.Char("equal"), M.Pair(M.Char("to"),
        M.Pair(M.Char("four"), empty))))))))()
    unknown = Gmod.SurfaceUnknownWords(vocabulary, surface, registry)()
    print("unknown words empty:", M.IdentityCompare(unknown, empty)() is M.truth_value)
    pair = Gmod.Converse(vocabulary, surface, registry)()
    outcome = M.Head(pair)()
    print("outcome label:", type(M.Head(outcome)()).__name__)
    reason = M.Head(M.Tail(M.Tail(outcome)())())()
    print("reason label:", type(M.Head(reason)()).__name__)


if __name__ == "__main__":
    main()
