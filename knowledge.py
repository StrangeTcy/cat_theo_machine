from __future__ import annotations

from . import machine as M


class HeadBucketKey(M.Edge):
    """Identity-stable head key for bucket indexing.

    Every fact is Pair(label, args); the head label is Head(fact).
    A non-pair atom has no concrete head and maps to EmptyList (the
    residual/non-bucketable key).

    The key atom is memoised on the registry via a cache trie so that
    the same source term always returns the same atom by IdentityCompare.
    Both the write side (KnowledgeHeadIndexInsert) and the read side
    (KnowledgeHeadIndexBucket, _match_premises) use THIS edge and only
    this edge, eliminating the FactHead-vs-TermHead divergence."""

    _CACHE_LABEL = M.Atom()

    def __init__(self, term, registry):
        self.registry = registry
        self.result = self._compute(term, registry)
        super().__init__(inputs=M.Pair(term, M.Pair(registry, M.EmptyList)), results=self.result)

    def _compute(self, term, registry):
        if M.IsPair(term)() is M.truth_value:
            raw = M.Head(term)()
            return self._memoise(raw, registry)
        return M.EmptyList

    def _memoise(self, atom, registry):
        key = M.ExactKey(atom, registry)()
        cached = M.TreeLookup(HeadBucketKey._CACHE_LABEL, key, registry)()
        if M.IdentityCompare(cached, M.EmptyList)() is M.false_value:
            return cached
        fresh = M.Atom()
        HeadBucketKey._CACHE_LABEL = M.TreeInsert(HeadBucketKey._CACHE_LABEL, key, fresh, registry)()
        return fresh

    def __call__(self):
        return self.result


class IsBucketable(M.Edge):
    """A term is bucketable iff its HeadBucketKey is not EmptyList."""

    def __init__(self, term, registry):
        key = HeadBucketKey(term, registry)()
        if M.IdentityCompare(key, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FactKey(M.Edge):
    """Structural key of a fact under a registry."""

    def __init__(self, fact, registry):
        self.result = M.ExactKey(fact, registry)()
        super().__init__(inputs=M.Pair(fact, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeTrieInsert(M.Edge):
    """Insert one fact into a knowledge trie keyed on the fact's ExactKey."""

    def __init__(self, knowledge, fact, registry):
        self.registry = registry
        key = FactKey(fact, registry)()
        self.result = M.TreeInsert(knowledge, key, fact, registry)()
        super().__init__(
            inputs=M.Pair(knowledge, M.Pair(fact, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class KnowledgeTrieInsertChain(M.Edge):
    def __init__(self, knowledge, facts, registry):
        self.registry = registry
        self.result = self._insert_chain(knowledge, facts)
        super().__init__(
            inputs=M.Pair(knowledge, M.Pair(facts, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _insert_chain(self, knowledge, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return knowledge
        fact = M.Head(facts)()
        next_knowledge = KnowledgeTrieInsert(knowledge, fact, self.registry)()
        return self._insert_chain(next_knowledge, M.Tail(facts)())

    def __call__(self):
        return self.result


class KnowledgeTrieLookup(M.Edge):
    def __init__(self, knowledge, fact, registry):
        self.registry = registry
        key = FactKey(fact, registry)()
        self.result = M.TreeLookup(knowledge, key, registry)()
        super().__init__(
            inputs=M.Pair(knowledge, M.Pair(fact, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class KnowledgeTrieHasFact(M.Edge):
    def __init__(self, knowledge, fact, registry):
        self.registry = registry
        found = KnowledgeTrieLookup(knowledge, fact, registry)()
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(
            inputs=M.Pair(knowledge, M.Pair(fact, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class KnowledgeTrieFacts(M.Edge):
    def __init__(self, knowledge, registry):
        self.registry = registry
        entries = M.TreeEntries(knowledge)()
        self.result = self._collect(entries)
        super().__init__(inputs=M.Pair(knowledge, M.Pair(registry, M.EmptyList)), results=self.result)

    def _collect(self, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(entries)()
        fact = M.Head(M.Tail(entry)())()
        rest = self._collect(M.Tail(entries)())
        return M.Pair(fact, rest)

    def __call__(self):
        return self.result


class KnowledgeTrieSameRoot(M.Edge):
    def __init__(self, left, right):
        left_root = M.TreeRoot(left)()
        right_root = M.TreeRoot(right)()
        self.result = M.TermEqual(left_root, right_root)()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeHeadIndexInsert(M.Edge):
    """Insert one fact into a head-label index.

    Keyed on HeadBucketKey(fact).  If the fact is not bucketable (HeadBucketKey
    returns EmptyList), it goes into the residual bucket.  Every lookup ALWAYS
    includes the residual bucket, so narrowing is safe: it can over-match but
    never under-match.

    Returns Pair(index, Pair(residual, EmptyList))."""

    def __init__(self, index, residual, fact, registry):
        self.registry = registry
        head = HeadBucketKey(fact, registry)()
        if M.IdentityCompare(head, M.EmptyList)() is M.truth_value:
            next_residual = M.Pair(fact, residual)
            self.result = M.Pair(index, M.Pair(next_residual, M.EmptyList))
        else:
            existing = M.TreeLookup(index, head, registry)()
            if M.IdentityCompare(existing, M.EmptyList)() is M.truth_value:
                bucket = M.Pair(fact, M.EmptyList)
            else:
                bucket = M.Pair(fact, existing)
            next_index = M.TreeInsert(index, head, bucket, registry)()
            self.result = M.Pair(next_index, M.Pair(residual, M.EmptyList))
        super().__init__(
            inputs=M.Pair(index, M.Pair(residual, M.Pair(fact, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class KnowledgeHeadIndexInsertChain(M.Edge):
    def __init__(self, index, residual, facts, registry):
        self.registry = registry
        self.result = self._insert_chain(index, residual, facts)
        super().__init__(
            inputs=M.Pair(index, M.Pair(residual, M.Pair(facts, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _insert_chain(self, index, residual, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.Pair(index, M.Pair(residual, M.EmptyList))
        fact = M.Head(facts)()
        next_pair = KnowledgeHeadIndexInsert(index, residual, fact, self.registry)()
        next_index = M.Head(next_pair)()
        next_residual = M.Head(M.Tail(next_pair)())()
        return self._insert_chain(next_index, next_residual, M.Tail(facts)())

    def __call__(self):
        return self.result


class KnowledgeHeadIndexBucket(M.Edge):
    """All facts whose HeadBucketKey equals the given key, plus the residual
    bucket, as a chain.  The residual is always included so narrowing is safe.

    When key is EmptyList (not bucketable), returns EmptyList — the caller
    should fall back to the full fact chain in that case."""

    def __init__(self, index, residual, key, registry):
        self.registry = registry
        self.result = self._bucket(index, residual, key)
        super().__init__(
            inputs=M.Pair(index, M.Pair(residual, M.Pair(key, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _bucket(self, index, residual, key):
        if M.IdentityCompare(key, M.EmptyList)() is M.truth_value:
            return residual
        found = M.TreeLookup(index, key, self.registry)()
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            return residual
        return self._append(found, residual)

    def _append(self, left, right):
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return right
        return M.Pair(M.Head(left)(), self._append(M.Tail(left)(), right))

    def __call__(self):
        return self.result


class KnowledgeHeadIndexResidual(M.Edge):
    """Return the residual chain from Pair(index, Pair(residual, EmptyList))."""

    def __init__(self, pair):
        self.result = M.Head(M.Tail(pair)())()
        super().__init__(inputs=M.Pair(pair, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeHeadIndexTrie(M.Edge):
    """Return the index trie from Pair(index, Pair(residual, EmptyList))."""

    def __init__(self, pair):
        self.result = M.Head(pair)()
        super().__init__(inputs=M.Pair(pair, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeHeadIndexConsistent(M.Edge):
    """Consistency probe: for every fact, compute HeadBucketKey, fetch the
    bucket (including residual), and verify the fact is present.  Returns
    truth_value if all facts are accounted for, false_value otherwise."""

    def __init__(self, index, residual, facts, registry):
        self.registry = registry
        self.result = self._check(index, residual, facts)
        super().__init__(
            inputs=M.Pair(index, M.Pair(residual, M.Pair(facts, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _check(self, index, residual, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.truth_value
        fact = M.Head(facts)()
        key = HeadBucketKey(fact, self.registry)()
        bucket = KnowledgeHeadIndexBucket(index, residual, key, self.registry)()
        present = self._fact_in_chain(fact, bucket)
        if present is M.false_value:
            return M.false_value
        return self._check(index, residual, M.Tail(facts)())

    def _fact_in_chain(self, fact, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(M.Head(chain)(), fact)() is M.truth_value:
            return M.truth_value
        return self._fact_in_chain(fact, M.Tail(chain)())

    def __call__(self):
        return self.result


class RuleReplacementHead(M.Edge):
    def __init__(self, rule):
        replacement = M.Head(M.Tail(M.EdgeInputs(rule)())())()
        if M.IsPair(replacement)() is M.truth_value:
            self.result = M.Head(replacement)()
        else:
            self.result = replacement
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RulePremiseHead(M.Edge):
    def __init__(self, rule):
        premises = M.Head(M.EdgeInputs(rule)())()
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            premise = M.Head(premises)()
            if M.IsPair(premise)() is M.truth_value:
                self.result = M.Head(premise)()
            else:
                self.result = premise
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RulesByHeadInsert(M.Edge):
    def __init__(self, index, rule, head, registry):
        self.registry = registry
        found = M.TreeLookup(index, head, registry)()
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            bucket = M.Pair(rule, M.EmptyList)
        else:
            bucket = M.Pair(rule, found)
        self.result = M.TreeInsert(index, head, bucket, registry)()
        super().__init__(
            inputs=M.Pair(index, M.Pair(rule, M.Pair(head, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RulesByHeadInsertChain(M.Edge):
    def __init__(self, index, rules, registry, by_replacement):
        self.registry = registry
        self._by_replacement = by_replacement
        self.result = self._insert_chain(index, rules)
        super().__init__(
            inputs=M.Pair(index, M.Pair(rules, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _insert_chain(self, index, rules):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return index
        rule = M.Head(rules)()
        if self._by_replacement is M.truth_value:
            head = RuleReplacementHead(rule)()
        else:
            head = RulePremiseHead(rule)()
        next_index = RulesByHeadInsert(index, rule, head, self.registry)()
        return self._insert_chain(next_index, M.Tail(rules)())

    def __call__(self):
        return self.result


class RulesByReplacementHeadInsertChain(M.Edge):
    def __init__(self, index, rules, registry):
        self.registry = registry
        inner = RulesByHeadInsertChain(index, rules, registry, M.truth_value)
        self.result = inner()
        super().__init__(
            inputs=M.Pair(index, M.Pair(rules, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RulesByPremiseHeadInsertChain(M.Edge):
    def __init__(self, index, rules, registry):
        self.registry = registry
        inner = RulesByHeadInsertChain(index, rules, registry, M.false_value)
        self.result = inner()
        super().__init__(
            inputs=M.Pair(index, M.Pair(rules, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RulesByHeadBucket(M.Edge):
    def __init__(self, index, label, registry):
        self.registry = registry
        found = M.TreeLookup(index, label, registry)()
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            self.result = found
        super().__init__(
            inputs=M.Pair(index, M.Pair(label, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MatchMemoKey(M.Edge):
    def __init__(self, rule, bucket_root, registry):
        self.registry = registry
        bucket_key = M.ExactKey(bucket_root, registry)()
        self.result = M.Pair(rule, M.Pair(bucket_key, M.EmptyList))
        super().__init__(
            inputs=M.Pair(rule, M.Pair(bucket_root, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MatchMemoLookup(M.Edge):
    def __init__(self, memo, rule, bucket_root, registry):
        self.registry = registry
        key = MatchMemoKey(rule, bucket_root, registry)()
        self.result = M.TreeLookup(memo, key, registry)()
        super().__init__(
            inputs=M.Pair(
                memo,
                M.Pair(rule, M.Pair(bucket_root, M.Pair(registry, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MatchMemoStore(M.Edge):
    def __init__(self, memo, rule, bucket_root, bindings, registry):
        self.registry = registry
        key = MatchMemoKey(rule, bucket_root, registry)()
        self.result = M.TreeInsert(memo, key, bindings, registry)()
        super().__init__(
            inputs=M.Pair(
                memo,
                M.Pair(rule, M.Pair(bucket_root, M.Pair(bindings, M.Pair(registry, M.EmptyList)))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_") and name not in ("M",)]