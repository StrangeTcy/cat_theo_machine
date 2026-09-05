"""Pre-flight 2026-09-04: MultiRule compile path and search-pool admission.

Builds a two-premise producer (Eq(a,b) & IsReal(b) |- Eq(b,a)) and a
two-premise consumer (Eq(a,b) & Eq(b,c) |- Eq(a,c)), compiles both through
CompileMultiRuleToLaw, then hands the raw rule edges to SearchDFS as the
entire rule pool over ground instances of the x+1=x shape. The protocol's
nosolutions producer/consumer pair is not reconstructable on this lineage
(no protocol document, no NoSolutions vocabulary); these are stand-ins.

Compile half of pre-flight item 2: verified by this probe. Selection half:
the pool is admitted and compiled into the search job and the start state
is expanded; no successor was generated from the states tried, so the
candidate-partial-match witness remains open.

Run: PYTHONPATH=/home/user python3 probes/preflight_item2_multirule.py
"""
import sys
import time

sys.path.insert(0, "/home/user")

import cat_theo_machine.labels as Lmod
import cat_theo_machine.machine as M
import cat_theo_machine.proof as Pmod
import cat_theo_machine.search as Smod
import cat_theo_machine.graph as Gmod
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
from cat_theo_machine.runtime import boot_from_packs


def _var(name):
    return M.Pair(M.VarTag, M.Pair(M.Char(name), M.EmptyList))


def _expr(label, *args):
    chain = M.EmptyList
    for a in reversed(args):
        chain = M.Pair(a, chain)
    return M.Pair(label, chain)


def main():
    runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    graph = runtime.graph
    graph._search_disable_console = M.truth_value
    registry = M.FromContextGetConstructors(graph)()
    empty = M.EmptyList
    a = _var("?a")
    b = _var("?b")
    c = _var("?c")
    x = _var("?x")
    toy_goal = _expr(Lmod.ExprEqLabel, _expr(Lmod.ExprAddLabel, x, M.one), x)
    print("toy goal head label:", type(M.Head(toy_goal)()).__name__)

    producer_edge = Pmod.MultiRule(
        M.Pair(_expr(Lmod.ExprEqLabel, a, b), M.Pair(_expr(Lmod.IsRealLabel, b), empty)),
        _expr(Lmod.ExprEqLabel, b, a),
    )
    producer_law = Gmod.CompileMultiRuleToLaw(producer_edge)()
    print("producer compiles:", M.IdentityCompare(producer_law, empty)() is M.false_value)

    consumer_edge = Pmod.MultiRule(
        M.Pair(_expr(Lmod.ExprEqLabel, a, b), M.Pair(_expr(Lmod.ExprEqLabel, b, c), empty)),
        _expr(Lmod.ExprEqLabel, a, c),
    )
    consumer_law = Gmod.CompileMultiRuleToLaw(consumer_edge)()
    print("consumer compiles:", M.IdentityCompare(consumer_law, empty)() is M.false_value)

    start = M.Pair(_expr(Lmod.ExprEqLabel, _expr(Lmod.ExprAddLabel, M.two, M.one), M.two),
                   M.Pair(_expr(Lmod.IsRealLabel, M.one), empty))
    goal = _expr(Lmod.ExprEqLabel, M.one, _expr(Lmod.ExprAddLabel, M.two, M.one))
    pool = M.Pair(producer_edge, M.Pair(consumer_edge, empty))
    begin = time.time()
    pair = Smod.SearchDFS(graph, start, goal, pool, runtime.theorem_heuristic, registry)()
    cost = M.Head(M.Tail(pair)())()
    print("expanded:", M.PrettyTerm(Smod.SearchCostExpanded(cost)(), registry)())
    print("generated:", M.PrettyTerm(Smod.SearchCostGenerated(cost)(), registry)())
    print("elapsed:", round(time.time() - begin, 1))


if __name__ == "__main__":
    main()
