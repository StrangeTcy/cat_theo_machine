import sys

sys.path.insert(0, "/home/user")

from hyge.runtime import boot_from_packs
from hyge.main import PACK_PATHS, _runtime_namespace
from hyge import machine as M
from hyge import proof as P


def call2(head, a, b):
    return M.Pair(head, M.Pair(a, M.Pair(b, M.EmptyList)))


def main():
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    x = M.Pair(M.VarTag, M.Pair(M.Char("x"), M.EmptyList))
    add = call2(M.ExprAddLabel, x, M.one)
    goal = call2(M.ExprEqLabel, add, x)
    producer = P.MultiRule(M.Pair(goal, M.EmptyList), goal)
    consumer = P.MultiRule(M.Pair(goal, M.EmptyList), call2(M.ExprEqLabel, x, add))
    print("producer_class", producer.__class__.__name__)
    print("consumer_class", consumer.__class__.__name__)
    arithmetic = packs.by_name("arithmetic")
    rule = arithmetic.rule_map["arithmetic_equation_is_symmetric"]
    flag = M.Head(M.Match(P.RulePattern(rule)(), goal)())()
    selected = M.IdentityCompare(flag, M.truth_value)() is M.truth_value
    print("candidate_rule", "arithmetic_equation_is_symmetric")
    print("partial_match_on_x_plus_1_eq_x", selected)


if __name__ == "__main__":
    main()
