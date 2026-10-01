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
    swapped = call2(M.ExprEqLabel, x, add)
    producer = P.MultiRule(M.Pair(goal, M.EmptyList), goal)
    consumer = P.MultiRule(M.Pair(goal, M.EmptyList), swapped)
    print("producer_class", producer.__class__.__name__)
    print("consumer_class", consumer.__class__.__name__)
    producer_flag = M.Head(M.Match(P.RulePattern(producer)(), goal)())()
    consumer_flag = M.Head(M.Match(P.RulePattern(consumer)(), goal)())()
    producer_hit = M.IdentityCompare(producer_flag, M.truth_value)() is M.truth_value
    consumer_hit = M.IdentityCompare(consumer_flag, M.truth_value)() is M.truth_value
    print("toy_nosolutions_producer_partial_match", producer_hit)
    print("toy_nosolutions_consumer_partial_match", consumer_hit)
    arithmetic = packs.by_name("arithmetic")
    pack_rule = arithmetic.rule_map["arithmetic_equation_is_symmetric"]
    pack_flag = M.Head(M.Match(P.RulePattern(pack_rule)(), goal)())()
    pack_hit = M.IdentityCompare(pack_flag, M.truth_value)() is M.truth_value
    print("pack_rule", "arithmetic_equation_is_symmetric")
    print("pack_rule_partial_match", pack_hit)
    print("item2_closed", producer_hit or consumer_hit)


if __name__ == "__main__":
    main()
