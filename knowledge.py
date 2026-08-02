from __future__ import annotations

from . import labels as L
from . import machine as M


class HeadBucketKey(M.Edge):
    def __init__(self, term, registry):
        self.registry = registry
        if M.IsPair(term)() is M.truth_value:
            basis = M.Head(term)()
        else:
            basis = term
        self.result = M.Pair(L.HeadBucketKeyLabel, M.Pair(basis, M.EmptyList))
        super().__init__(inputs=M.Pair(term, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeHeadIndexConsistent(M.Edge):
    def __init__(self, index, facts, registry):
        self.registry = registry
        self.result = self._check(index, facts)
        super().__init__(inputs=M.Pair(index, M.Pair(facts, M.Pair(registry, M.EmptyList))), results=self.result)

    def _bucket_has_fact(self, bucket, fact):
        if M.IdentityCompare(bucket, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(M.Head(bucket)(), fact)() is M.truth_value:
            return M.truth_value
        return self._bucket_has_fact(M.Tail(bucket)(), fact)

    def _check(self, index, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.truth_value
        fact = M.Head(facts)()
        bucket = KnowledgeHeadIndexBucket(index, fact, self.registry)()
        if self._bucket_has_fact(bucket, fact) is M.false_value:
            return M.false_value
        return self._check(index, M.Tail(facts)())

    def __call__(self):
        return self.result


class KnowledgeAnchorBucketAgreement(M.Edge):
    def __init__(self, anchor, facts, registry):
        self.registry = registry
        index = KnowledgeHeadIndexInsertChain(M.EmptyTree, facts, registry)()
        bucket = KnowledgeHeadIndexBucket(index, anchor, registry)()
        full = self._matches(anchor, facts)
        narrowed = self._matches(anchor, bucket)
        if M.IdentityCompare(full, narrowed)() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(anchor, M.Pair(facts, M.Pair(registry, M.EmptyList))), results=self.result)

    def _matches(self, anchor, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        match = M.Match(anchor, M.Head(facts)())()
        if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
            return M.truth_value
        return self._matches(anchor, M.Tail(facts)())

    def __call__(self):
        return self.result


class FactKey(M.Edge):
    def __init__(self, fact, registry):
        self.result = M.ExactKey(fact, registry)()
        super().__init__(inputs=M.Pair(fact, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeTrieInsert(M.Edge):
    def __init__(self, knowledge, fact, registry):
        self.registry = registry
        key = FactKey(fact, registry)()
        self.result = M.TreeInsert(knowledge, key, fact, registry)()
        super().__init__(inputs=M.Pair(knowledge, M.Pair(fact, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeTrieInsertChain(M.Edge):
    def __init__(self, knowledge, facts, registry):
        self.registry = registry
        self.result = self._insert_chain(knowledge, facts)
        super().__init__(inputs=M.Pair(knowledge, M.Pair(facts, M.Pair(registry, M.EmptyList))), results=self.result)

    def _insert_chain(self, knowledge, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return knowledge
        next_knowledge = KnowledgeTrieInsert(knowledge, M.Head(facts)(), self.registry)()
        return self._insert_chain(next_knowledge, M.Tail(facts)())

    def __call__(self):
        return self.result


class KnowledgeTrieLookup(M.Edge):
    def __init__(self, knowledge, fact, registry):
        self.registry = registry
        key = FactKey(fact, registry)()
        self.result = M.TreeLookup(knowledge, key, registry)()
        super().__init__(inputs=M.Pair(knowledge, M.Pair(fact, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeTrieHasFact(M.Edge):
    def __init__(self, knowledge, fact, registry):
        found = KnowledgeTrieLookup(knowledge, fact, registry)()
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(knowledge, M.Pair(fact, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeTrieFacts(M.Edge):
    def __init__(self, knowledge, registry):
        entries = M.TreeEntries(knowledge)()
        self.result = self._collect(entries)
        super().__init__(inputs=M.Pair(knowledge, M.Pair(registry, M.EmptyList)), results=self.result)

    def _collect(self, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(entries)()
        fact = M.Head(M.Tail(entry)())()
        return M.Pair(fact, self._collect(M.Tail(entries)()))

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
    def __init__(self, index, fact, registry):
        self.registry = registry
        head = HeadBucketKey(fact, registry)()
        existing = M.TreeLookup(index, head, registry)()
        if M.IdentityCompare(existing, M.EmptyList)() is M.truth_value:
            bucket = M.Pair(fact, M.EmptyList)
        else:
            bucket = M.Pair(fact, existing)
        self.result = M.TreeInsert(index, head, bucket, registry)()
        super().__init__(inputs=M.Pair(index, M.Pair(fact, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeHeadIndexInsertChain(M.Edge):
    def __init__(self, index, facts, registry):
        self.registry = registry
        self.result = self._insert_chain(index, facts)
        super().__init__(inputs=M.Pair(index, M.Pair(facts, M.Pair(registry, M.EmptyList))), results=self.result)

    def _insert_chain(self, index, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return index
        next_index = KnowledgeHeadIndexInsert(index, M.Head(facts)(), self.registry)()
        return self._insert_chain(next_index, M.Tail(facts)())

    def __call__(self):
        return self.result


class KnowledgeHeadIndexBucket(M.Edge):
    def __init__(self, index, term, registry):
        self.registry = registry
        key = HeadBucketKey(term, registry)()
        found = M.TreeLookup(index, key, registry)()
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            self.result = found
        super().__init__(inputs=M.Pair(index, M.Pair(term, M.Pair(registry, M.EmptyList))), results=self.result)

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
        super().__init__(inputs=M.Pair(index, M.Pair(rule, M.Pair(head, M.Pair(registry, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class RulesByHeadInsertChain(M.Edge):
    def __init__(self, index, rules, registry, by_replacement):
        self.registry = registry
        self._by_replacement = by_replacement
        self.result = self._insert_chain(index, rules)
        super().__init__(inputs=M.Pair(index, M.Pair(rules, M.Pair(registry, M.EmptyList))), results=self.result)

    def _insert_chain(self, index, rules):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return index
        rule = M.Head(rules)()
        if self._by_replacement is M.truth_value:
            head = HeadBucketKey(M.Head(M.Tail(M.EdgeInputs(rule)())())(), self.registry)()
        else:
            premises = M.Head(M.EdgeInputs(rule)())()
            if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
                head = HeadBucketKey(M.EmptyList, self.registry)()
            else:
                head = HeadBucketKey(M.Head(premises)(), self.registry)()
        next_index = RulesByHeadInsert(index, rule, head, self.registry)()
        return self._insert_chain(next_index, M.Tail(rules)())

    def __call__(self):
        return self.result


class RulesByReplacementHeadInsertChain(M.Edge):
    def __init__(self, index, rules, registry):
        inner = RulesByHeadInsertChain(index, rules, registry, M.truth_value)
        self.result = inner()
        super().__init__(inputs=M.Pair(index, M.Pair(rules, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class RulesByPremiseHeadInsertChain(M.Edge):
    def __init__(self, index, rules, registry):
        inner = RulesByHeadInsertChain(index, rules, registry, M.false_value)
        self.result = inner()
        super().__init__(inputs=M.Pair(index, M.Pair(rules, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class RulesByHeadBucket(M.Edge):
    def __init__(self, index, term, registry):
        key = HeadBucketKey(term, registry)()
        found = M.TreeLookup(index, key, registry)()
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            self.result = found
        super().__init__(inputs=M.Pair(index, M.Pair(term, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class MatchMemoKey(M.Edge):
    def __init__(self, rule, remaining_premises, bucket_root, registry):
        bucket_key = M.ExactKey(bucket_root, registry)()
        self.result = M.Pair(rule, M.Pair(remaining_premises, M.Pair(bucket_key, M.EmptyList)))
        super().__init__(inputs=M.Pair(rule, M.Pair(remaining_premises, M.Pair(bucket_root, M.Pair(registry, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class MatchMemoLookup(M.Edge):
    def __init__(self, memo, rule, remaining_premises, bucket_root, registry):
        key = MatchMemoKey(rule, remaining_premises, bucket_root, registry)()
        self.result = M.TreeLookup(memo, key, registry)()
        super().__init__(inputs=M.Pair(memo, M.Pair(rule, M.Pair(remaining_premises, M.Pair(bucket_root, M.Pair(registry, M.EmptyList))))), results=self.result)

    def __call__(self):
        return self.result


class MatchMemoStore(M.Edge):
    def __init__(self, memo, rule, remaining_premises, bucket_root, bindings, registry):
        key = MatchMemoKey(rule, remaining_premises, bucket_root, registry)()
        self.result = M.TreeInsert(memo, key, bindings, registry)()
        super().__init__(inputs=M.Pair(memo, M.Pair(rule, M.Pair(remaining_premises, M.Pair(bucket_root, M.Pair(bindings, M.Pair(registry, M.EmptyList)))))), results=self.result)

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_") and name not in ("L", "M")]
