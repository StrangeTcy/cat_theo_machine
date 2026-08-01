from __future__ import annotations

import hyge.machine as M
from hyge import labels as L
from hyge import knowledge as K
from hyge import proof as P


def main():
    registry = M.AllConstructors

    def _fact(label, *args):
        arg_chain = M.EmptyList
        for a in reversed(args):
            arg_chain = M.Pair(a, arg_chain)
        return M.Pair(label, arg_chain)

    # ---- 1. HeadBucketKey identity memoisation ----
    f1 = _fact(L.IsRealLabel, M.Zero)
    key1a = K.HeadBucketKey(f1, registry)()
    key1b = K.HeadBucketKey(f1, registry)()
    assert M.IdentityCompare(key1a, key1b)() is M.truth_value, \
        "same term -> same head key atom by IdentityCompare"
    print("1 OK: identity memoisation")

    f2 = _fact(L.IsRealLabel, M.one())
    key2 = K.HeadBucketKey(f2, registry)()
    assert M.IdentityCompare(key1a, key2)() is M.truth_value, \
        "same label -> same head key atom"
    print("2 OK: same label identity stable")

    f3 = _fact(L.SuccLabel, M.Zero)
    key3 = K.HeadBucketKey(f3, registry)()
    assert M.IdentityCompare(key1a, key3)() is M.false_value, \
        "different label -> different head key atom"
    print("3 OK: different label -> different key")

    bare = M.Atom()
    bare_key = K.HeadBucketKey(bare, registry)()
    assert M.IdentityCompare(bare_key, M.EmptyList)() is M.truth_value, \
        "non-pair bare atom -> EmptyList"
    print("4 OK: bare atom -> EmptyList (residual)")

    # ---- 2. IsBucketable ----
    assert K.IsBucketable(f1, registry)() is M.truth_value, "pair fact is bucketable"
    assert K.IsBucketable(bare, registry)() is M.false_value, "bare atom is not bucketable"
    print("5 OK: IsBucketable")

    # ---- 3. Knowledge trie basics ----
    facts = M.Pair(f1, M.Pair(f2, M.Pair(f3, M.EmptyList)))
    trie = K.KnowledgeTrieInsertChain(M.EmptyTree, facts, registry)()
    found = K.KnowledgeTrieLookup(trie, f2, registry)()
    assert M.IdentityCompare(found, M.EmptyList)() is M.false_value
    missing = _fact(L.IsRealLabel, M.two())
    assert K.KnowledgeTrieHasFact(trie, missing, registry)() is M.false_value
    assert K.KnowledgeTrieHasFact(trie, f1, registry)() is M.truth_value
    print("6 OK: knowledge trie")

    # ---- 4. Head index with residual ----
    pair = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, M.EmptyList, facts, registry)()
    index = K.KnowledgeHeadIndexTrie(pair)()
    residual = K.KnowledgeHeadIndexResidual(pair)()
    assert M.IdentityCompare(residual, M.EmptyList)() is M.truth_value, \
        "no non-bucketable facts in input"
    print("7 OK: empty residual for pair-only facts")

    isreal_key = K.HeadBucketKey(f1, registry)()
    isreal_bucket = K.KnowledgeHeadIndexBucket(index, residual, isreal_key, registry)()
    isreal_trie = K.KnowledgeTrieInsertChain(M.EmptyTree, isreal_bucket, registry)()
    assert K.KnowledgeTrieHasFact(isreal_trie, f1, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(isreal_trie, f2, registry)() is M.truth_value
    print("8 OK: IsReal bucket has f1 and f2")

    succ_key = K.HeadBucketKey(f3, registry)()
    succ_bucket = K.KnowledgeHeadIndexBucket(index, residual, succ_key, registry)()
    succ_trie = K.KnowledgeTrieInsertChain(M.EmptyTree, succ_bucket, registry)()
    assert K.KnowledgeTrieHasFact(succ_trie, f3, registry)() is M.truth_value
    assert K.KnowledgeTrieHasFact(succ_trie, f1, registry)() is M.false_value
    print("9 OK: Succ bucket has f3 only")

    # ---- 5. Non-bucketable goes to residual ----
    pair2 = K.KnowledgeHeadIndexInsert(index, residual, bare, registry)()
    index2 = K.KnowledgeHeadIndexTrie(pair2)()
    residual2 = K.KnowledgeHeadIndexResidual(pair2)()
    assert M.IdentityCompare(residual2, M.EmptyList)() is M.false_value, \
        "residual non-empty after inserting bare atom"
    print("10 OK: non-bucketable -> residual")

    bucket_with_residual = K.KnowledgeHeadIndexBucket(index2, residual2, isreal_key, registry)()
    bucket_trie = K.KnowledgeTrieInsertChain(M.EmptyTree, bucket_with_residual, registry)()
    assert K.KnowledgeTrieHasFact(bucket_trie, bare, registry)() is M.truth_value, \
        "bucket includes residual bare atom"
    print("11 OK: residual included in every bucket")

    # ---- 6. Consistency probe ----
    all_facts = M.Pair(f1, M.Pair(f2, M.Pair(f3, M.Pair(bare, M.EmptyList))))
    fresh_pair = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, M.EmptyList, all_facts, registry)()
    fresh_index = K.KnowledgeHeadIndexTrie(fresh_pair)()
    fresh_residual = K.KnowledgeHeadIndexResidual(fresh_pair)()
    consistent = K.KnowledgeHeadIndexConsistent(fresh_index, fresh_residual, all_facts, registry)()
    assert consistent is M.truth_value, "consistency probe passes for all facts"
    print("12 OK: consistency probe")

    # ---- 7. Verify FactHead-vs-TermHead divergence is fixed ----
    term_head_bare = P.TermHead(bare, registry)()
    hbk_bare = K.HeadBucketKey(bare, registry)()
    assert M.IdentityCompare(term_head_bare, hbk_bare)() is M.truth_value, \
        "TermHead and HeadBucketKey agree on bare atom"
    print("13 OK: TermHead / HeadBucketKey agree")

    # ---- 8. Memo basics ----
    memo = M.EmptyTree
    bindings_fake = M.Pair(M.truth_value, M.EmptyList)
    miss = K.MatchMemoLookup(memo, M.Zero, isreal_bucket, registry)()
    assert M.IdentityCompare(miss, M.EmptyList)() is M.truth_value, "memo miss before store"
    memo = K.MatchMemoStore(memo, M.Zero, isreal_bucket, bindings_fake, registry)()
    hit = K.MatchMemoLookup(memo, M.Zero, isreal_bucket, registry)()
    assert M.IdentityCompare(hit, M.EmptyList)() is M.false_value, "memo hit after store"
    print("14 OK: match memo")

    # ---- 9. Cycle guard ----
    rebuilt = K.KnowledgeTrieInsertChain(M.EmptyTree, facts, registry)()
    assert K.KnowledgeTrieSameRoot(trie, rebuilt)() is M.truth_value
    print("15 OK: cycle guard (same facts -> TermEqual roots)")

    print("ALL OK")


if __name__ == "__main__":
    main()
