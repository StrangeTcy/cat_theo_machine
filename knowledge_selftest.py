from __future__ import annotations

import hyge.machine as M
from hyge import labels as L
from hyge import knowledge as K
from hyge import proof as P


def _fact(label, *args):
    arg_chain = M.EmptyList
    for a in reversed(args):
        arg_chain = M.Pair(a, arg_chain)
    return M.Pair(label, arg_chain)


def _rule(pattern_label, pattern_args, replacement_label, replacement_args):
    pat = _fact(pattern_label, *pattern_args)
    rep = _fact(replacement_label, *replacement_args)
    return P.Rule(pat, rep)()


def _multirule(premises_list, replacement_label, replacement_args):
    prem_chain = M.EmptyList
    for pm in reversed(premises_list):
        prem_chain = M.Pair(pm, prem_chain)
    rep = _fact(replacement_label, *replacement_args)
    return P.MultiRule(prem_chain, rep)()


def main():
    registry = M.AllConstructors

    f1 = _fact(L.IsRealLabel, M.Zero)
    f2 = _fact(L.IsRealLabel, M.one())
    f3 = _fact(L.SuccLabel, M.Zero)
    facts = M.Pair(f1, M.Pair(f2, M.Pair(f3, M.EmptyList)))

    trie = M.EmptyTree
    trie = K.KnowledgeTrieInsertChain(trie, facts, registry)()

    found = K.KnowledgeTrieLookup(trie, f2, registry)()
    assert M.IdentityCompare(found, M.EmptyList)() is M.false_value

    missing = _fact(L.IsRealLabel, M.two())
    notfound = K.KnowledgeTrieLookup(trie, missing, registry)()
    assert M.IdentityCompare(notfound, M.EmptyList)() is M.truth_value

    has = K.KnowledgeTrieHasFact(trie, f1, registry)()
    assert has is M.truth_value
    hasnot = K.KnowledgeTrieHasFact(trie, missing, registry)()
    assert hasnot is M.false_value

    out = K.KnowledgeTrieFacts(trie, registry)()
    count_pair = M.Count(out, registry)()
    n = M.Head(count_pair)()
    print("trie fact count (PrettyTerm):", M.PrettyTerm(n, M.Head(M.Tail(count_pair)())())())
    assert K.KnowledgeTrieHasFact(trie, f1, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(trie, f2, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(trie, f3, registry)() is M.truth_value

    trie2 = K.KnowledgeTrieInsert(trie, missing, registry)()
    same = K.KnowledgeTrieSameRoot(trie, trie2)()
    assert same is M.false_value
    assert K.KnowledgeTrieHasFact(trie, missing, registry)() is M.false_value
    assert K.KnowledgeTrieHasFact(trie2, missing, registry)() is M.truth_value

    rebuilt = K.KnowledgeTrieInsertChain(M.EmptyTree, facts, registry)()
    assert K.KnowledgeTrieSameRoot(trie, rebuilt)() is M.truth_value

    head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, facts, registry)()
    assert K.KnowledgeHeadIndexConsistent(head_index, facts, registry)() is M.truth_value

    isreal_bucket = K.KnowledgeHeadIndexBucket(head_index, f1, registry)()
    succ_bucket = K.KnowledgeHeadIndexBucket(head_index, f3, registry)()
    empty_bucket = K.KnowledgeHeadIndexBucket(head_index, _fact(L.NonNegativeLabel, M.Zero), registry)()

    assert K.KnowledgeTrieHasFact(K.KnowledgeTrieInsertChain(M.EmptyTree, isreal_bucket, registry)(), f1, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(K.KnowledgeTrieInsertChain(M.EmptyTree, isreal_bucket, registry)(), f2, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(K.KnowledgeTrieInsertChain(M.EmptyTree, succ_bucket, registry)(), f3, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(K.KnowledgeTrieInsertChain(M.EmptyTree, succ_bucket, registry)(), f1, registry)() is M.false_value
    assert M.IdentityCompare(empty_bucket, M.EmptyList)() is M.truth_value

    r1 = _rule(L.IsRealLabel, (M.Zero,), L.NonNegativeLabel, (M.Zero,))
    r2 = _rule(L.SuccLabel, (M.Zero,), L.IsRealLabel, (M.one(),))
    r3 = _multirule([_fact(L.IsRealLabel, M.Zero), _fact(L.NonNegativeLabel, M.Zero)], L.NonNegativeLabel, (M.one(),))
    rules = M.Pair(r1, M.Pair(r2, M.Pair(r3, M.EmptyList)))

    by_rep = K.RulesByReplacementHeadInsertChain(M.EmptyTree, rules, registry)()
    by_prem = K.RulesByPremiseHeadInsertChain(M.EmptyTree, rules, registry)()

    rep_nn = K.RulesByHeadBucket(by_rep, _fact(L.NonNegativeLabel, M.Zero), registry)()
    rep_real = K.RulesByHeadBucket(by_rep, _fact(L.IsRealLabel, M.one()), registry)()
    prem_real = K.RulesByHeadBucket(by_prem, _fact(L.IsRealLabel, M.Zero), registry)()
    prem_succ = K.RulesByHeadBucket(by_prem, _fact(L.SuccLabel, M.Zero), registry)()

    assert M.IdentityCompare(rep_nn, M.EmptyList)() is M.false_value
    assert M.IdentityCompare(rep_real, M.EmptyList)() is M.false_value
    assert M.IdentityCompare(prem_real, M.EmptyList)() is M.false_value
    assert M.IdentityCompare(prem_succ, M.EmptyList)() is M.false_value
    assert M.IdentityCompare(K.RulesByHeadBucket(by_rep, _fact(L.SuccLabel, M.Zero), registry)(), M.EmptyList)() is M.truth_value

    memo = M.EmptyTree
    isreal_bucket = K.KnowledgeHeadIndexBucket(head_index, f1, registry)()
    bindings_fake = M.Pair(M.truth_value, M.EmptyList)
    memo_premises = M.Pair(P.RulePattern(r1)(), M.EmptyList)

    miss = K.MatchMemoLookup(memo, r1, memo_premises, isreal_bucket, registry)()
    assert M.IdentityCompare(miss, M.EmptyList)() is M.truth_value

    memo = K.MatchMemoStore(memo, r1, memo_premises, isreal_bucket, bindings_fake, registry)()
    hit = K.MatchMemoLookup(memo, r1, memo_premises, isreal_bucket, registry)()
    assert M.IdentityCompare(hit, M.EmptyList)() is M.false_value

    miss2 = K.MatchMemoLookup(memo, r2, memo_premises, isreal_bucket, registry)()
    assert M.IdentityCompare(miss2, M.EmptyList)() is M.truth_value

    f4 = _fact(L.SuccLabel, M.one())
    head_index2 = K.KnowledgeHeadIndexInsert(head_index, f4, registry)()
    isreal_bucket2 = K.KnowledgeHeadIndexBucket(head_index2, f1, registry)()
    assert M.TermEqual(isreal_bucket, isreal_bucket2)() is M.truth_value
    hit2 = K.MatchMemoLookup(memo, r1, memo_premises, isreal_bucket2, registry)()
    assert M.IdentityCompare(hit2, bindings_fake)() is M.truth_value

    print("ALL OK")


if __name__ == "__main__":
    main()
