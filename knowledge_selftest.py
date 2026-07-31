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

    # ---- Knowledge trie: insert + lookup + has + ordered facts ----
    f1 = _fact(L.IsRealLabel, M.Zero)              # IsReal(0)
    f2 = _fact(L.IsRealLabel, M.one())             # IsReal(1)
    f3 = _fact(L.SuccLabel, M.Zero)                 # Succ(0)
    facts = M.Pair(f1, M.Pair(f2, M.Pair(f3, M.EmptyList)))

    trie = M.EmptyTree
    trie = K.KnowledgeTrieInsertChain(trie, facts, registry)()

    # lookup an existing fact
    found = K.KnowledgeTrieLookup(trie, f2, registry)()
    assert M.IdentityCompare(found, M.EmptyList)() is M.false_value, "IsReal(1) should be present"

    # lookup a missing fact
    missing = _fact(L.IsRealLabel, M.two())
    notfound = K.KnowledgeTrieLookup(trie, missing, registry)()
    assert M.IdentityCompare(notfound, M.EmptyList)() is M.truth_value, "IsReal(2) should be absent"

    # has-fact
    has = K.KnowledgeTrieHasFact(trie, f1, registry)()
    assert has is M.truth_value, "HasFact IsReal(0) -> truth"
    hasnot = K.KnowledgeTrieHasFact(trie, missing, registry)()
    assert hasnot is M.false_value, "HasFact IsReal(2) -> false"

    # ordered facts out == deterministic; rebuild from trie must contain exactly f1,f2,f3
    out = K.KnowledgeTrieFacts(trie, registry)()
    count_pair = M.Count(out, registry)()
    n = M.Head(count_pair)()
    print("trie fact count (PrettyTerm):", M.PrettyTerm(n, M.Head(M.Tail(count_pair)())())())
    # each of f1,f2,f3 must be retrievable from the rebuilt trie
    assert K.KnowledgeTrieHasFact(trie, f1, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(trie, f2, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(trie, f3, registry)() is M.truth_value

    # ---- Incremental insert gives a NEW root (structural sharing) ----
    trie2 = K.KnowledgeTrieInsert(trie, missing, registry)()
    same = K.KnowledgeTrieSameRoot(trie, trie2)()
    assert same is M.false_value, "adding a fact must change the root"
    # original trie must still NOT contain the new fact (persistence / sharing)
    assert K.KnowledgeTrieHasFact(trie, missing, registry)() is M.false_value
    assert K.KnowledgeTrieHasFact(trie2, missing, registry)() is M.truth_value

    # ---- Cycle guard: same facts -> same root (identity), no compare needed ----
    trie_again = K.KnowledgeTrieInsertChain(M.EmptyTree, facts, registry)()
    assert K.KnowledgeTrieSameRoot(trie, trie_again)() is M.truth_value, \
        "rebuilding the same facts must yield the same root atom (interning)"

    # ---- Head index: bucket by label ----
    head_index = M.EmptyTree
    head_index = K.KnowledgeHeadIndexInsertChain(head_index, facts, registry)()

    isreal_bucket = K.KnowledgeHeadIndexBucket(head_index, L.IsRealLabel, registry)()
    succ_bucket = K.KnowledgeHeadIndexBucket(head_index, L.SuccLabel, registry)()
    empty_bucket = K.KnowledgeHeadIndexBucket(head_index, L.NonNegativeLabel, registry)()

    # IsReal bucket has f1 and f2, not f3
    assert K.KnowledgeTrieHasFact(
        K.KnowledgeTrieInsertChain(M.EmptyTree, isreal_bucket, registry)(), f1, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(
        K.KnowledgeTrieInsertChain(M.EmptyTree, isreal_bucket, registry)(), f2, registry)() is M.truth_value
    # Succ bucket has f3 only
    assert K.KnowledgeTrieHasFact(
        K.KnowledgeTrieInsertChain(M.EmptyTree, succ_bucket, registry)(), f3, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(
        K.KnowledgeTrieInsertChain(M.EmptyTree, succ_bucket, registry)(), f1, registry)() is M.false_value
    # NonNegative bucket empty
    assert M.IdentityCompare(empty_bucket, M.EmptyList)() is M.truth_value

    # ---- Rule indices: by replacement head and by premise head ----
    r1 = _rule(L.IsRealLabel, (M.Zero,), L.NonNegativeLabel, (M.Zero,))   # IsReal(0) -> NonNegative(0)
    r2 = _rule(L.SuccLabel, (M.Zero,), L.IsRealLabel, (M.one(),))         # Succ(0) -> IsReal(1)
    r3 = _multirule([_fact(L.IsRealLabel, M.Zero), _fact(L.NonNegativeLabel, M.Zero)],
                    L.NonNegativeLabel, (M.one(),))                       # IsReal(0) & NonNegative(0) -> NonNegative(1)
    rules = M.Pair(r1, M.Pair(r2, M.Pair(r3, M.EmptyList)))

    by_rep = K.RulesByReplacementHeadInsertChain(M.EmptyTree, rules, registry)()
    by_prem = K.RulesByPremiseHeadInsertChain(M.EmptyTree, rules, registry)()

    # rules whose replacement head is NonNegativeLabel: r1 and r3
    rep_nn = K.RulesByHeadBucket(by_rep, L.NonNegativeLabel, registry)()
    # rules whose replacement head is IsRealLabel: r2
    rep_real = K.RulesByHeadBucket(by_rep, L.IsRealLabel, registry)()
    # rules whose first premise head is IsRealLabel: r1 (unary) and r3 (multi)
    prem_real = K.RulesByHeadBucket(by_prem, L.IsRealLabel, registry)()
    # rules whose first premise head is SuccLabel: r2
    prem_succ = K.RulesByHeadBucket(by_prem, L.SuccLabel, registry)()

    # sanity: each bucket is non-empty where expected
    assert M.IdentityCompare(rep_nn, M.EmptyList)() is M.false_value, "replacement NonNegative bucket non-empty"
    assert M.IdentityCompare(rep_real, M.EmptyList)() is M.false_value, "replacement IsReal bucket non-empty"
    assert M.IdentityCompare(prem_real, M.EmptyList)() is M.false_value, "premise IsReal bucket non-empty"
    assert M.IdentityCompare(prem_succ, M.EmptyList)() is M.false_value, "premise Succ bucket non-empty"
    # a label with no rules -> empty bucket
    assert M.IdentityCompare(
        K.RulesByHeadBucket(by_rep, L.SuccLabel, registry)(), M.EmptyList)() is M.truth_value

    # ---- Match memo: store + lookup, keyed on (rule, ExactKey(bucket chain)) ----
    memo = M.EmptyTree
    # the head bucket is the chain of facts stored under the label key; its
    # structural ExactKey is the stable memo sub-key.
    isreal_bucket = K.KnowledgeHeadIndexBucket(head_index, L.IsRealLabel, registry)()
    bindings_fake = M.Pair(M.truth_value, M.EmptyList)  # stand-in for a computed binding chain

    # before store: miss
    miss = K.MatchMemoLookup(memo, r1, isreal_bucket, registry)()
    assert M.IdentityCompare(miss, M.EmptyList)() is M.truth_value, "memo miss before store"

    # store, then lookup hits
    memo = K.MatchMemoStore(memo, r1, isreal_bucket, bindings_fake, registry)()
    hit = K.MatchMemoLookup(memo, r1, isreal_bucket, registry)()
    assert M.IdentityCompare(hit, M.EmptyList)() is M.false_value, "memo hit after store"
    assert M.IdentityCompare(hit, bindings_fake)() is M.truth_value, "memo returns the stored bindings"

    # a different rule on the same bucket -> still a miss (key includes rule atom)
    miss2 = K.MatchMemoLookup(memo, r2, isreal_bucket, registry)()
    assert M.IdentityCompare(miss2, M.EmptyList)() is M.truth_value, "different rule -> miss"

    # ---- Memo validity under structural sharing: adding a fact to a DIFFERENT
    # head bucket must NOT change the IsReal bucket chain, so the memo entry for
    # (r1, IsReal bucket) is still a hit with zero invalidation logic. ----
    f4 = _fact(L.SuccLabel, M.one())  # goes under Succ bucket, not IsReal
    head_index2 = K.KnowledgeHeadIndexInsert(head_index, f4, registry)()
    isreal_bucket2 = K.KnowledgeHeadIndexBucket(head_index2, L.IsRealLabel, registry)()
    assert M.TermEqual(isreal_bucket, isreal_bucket2)() is M.truth_value, \
        "adding to a different bucket must keep the IsReal bucket chain structurally equal"
    hit2 = K.MatchMemoLookup(memo, r1, isreal_bucket2, registry)()
    assert M.IdentityCompare(hit2, bindings_fake)() is M.truth_value, \
        "memo entry still valid for unchanged bucket, no invalidation needed"

    print("ALL OK")


if __name__ == "__main__":
    main()
