from hyge.runtime import boot_from_packs
from hyge.main import PACK_PATHS, _runtime_namespace
from hyge import machine as M
from hyge import proof as Pmod
from hyge import knowledge as K

runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
registry = M.FromContextGetConstructors(runtime.graph)()
example = packs.by_name('geometry').examples['tao_problem_1_1_triangle']
start = Pmod.NormalizeKnowledge(example[0], registry)()
facts = Pmod.KnowledgeFacts(start)()
rules = runtime.ordered_rules()
filterer = Pmod.FilterApplicableRules(rules, start, registry)
remaining = rules
count = 0
found = M.false_value
while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
    rule = M.Head(remaining)()
    anchor = filterer._rule_anchor(rule)
    ok = K.KnowledgeAnchorBucketAgreement(anchor, facts, registry)()
    if M.IdentityCompare(ok, M.false_value)() is M.truth_value:
        print('MISMATCH_AT', count)
        print('ANCHOR', M.PrettyTerm(anchor, registry)())
        print('RULE', Pmod.PrettyRule(rule, registry)())
        found = M.truth_value
        break
    remaining = M.Tail(remaining)()
    count = count + 1
print('FOUND', M.IdentityCompare(found, M.truth_value)() is M.truth_value)
