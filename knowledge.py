from __future__ import annotations

from . import machine as M


class FactHead(M.Edge):
    """Head label of a fact.  A fact is Pair(label, args); the head is Head(fact).
    A non-pair atom is its own head (it is a bare symbol/constant)."""

    def __init__(self, fact):
        if M.IsPair(fact)() is M.truth_value:
            self.result = M.Head(fact)()
        else:
            self.result = fact
        super().__init__(inputs=M.Pair(fact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FactKey(M.Edge):
    """Structural key of a fact under a registry.  Same notion of equality the
    prover already uses (ExactKey), so two facts that are TermEqual share a key."""

    def __init__(self, fact, registry):
        self.result = M.ExactKey(fact, registry)()
        super().__init__(inputs=M.Pair(fact, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeTrieInsert(M.Edge):
    """Insert one fact into a knowledge trie.

    The trie is a plain M.Tree (the existing Patricia index) keyed on the
    fact's structural ExactKey.  Insertion is incremental: O(key depth), with
    structural sharing of every un-touched subtrie.  The trie IS the sorted
    order, so there is no separate normalisation pass."""

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
    """Insert a chain of facts into a knowledge trie, one insert per fact.
    Replaces NormalizeKnowledgeFacts: the same inputs produce a deterministically
    ordered structure, but by construction rather than by an O(n^2) sort."""

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
    """Look a fact up by its structural key.  O(key depth), not O(n)."""

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
    """Membership test.  Empty result means absent."""

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
    """All facts in deterministic order, as a chain.  The trie's intrinsic key
    ordering is the order, so this is the replacement for the sorted cons-list
    the prover used to carry around.  Rebuilds the chain by walking TreeEntries
    (already an ordered walk)."""

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
    """Two knowledge tries hold the same facts iff their stored roots are
    structurally equal.  TreeInsert produces a fresh Tree wrapper per insert, so
    the guard is TermEqual on the roots, not IdentityCompare.  TermEqual on two
    Patricia roots is O(shared-prefix): for a state that recurs (a->b->a) the
    re-derived trie is TermEqual to a prior one, so the visited-set keyed on this
    predicate catches the cycle with no numbers and no depth limit.  This is the
    structural guardrail: same facts -> same root (by TermEqual), once and
    without paying for a full rescan."""

    def __init__(self, left, right):
        left_root = M.TreeRoot(left)()
        right_root = M.TreeRoot(right)()
        self.result = M.TermEqual(left_root, right_root)()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeHeadIndexInsert(M.Edge):
    """Insert one fact into a head-label index.

    The index is a trie keyed on FactHead(fact) (the head label).  The value
    stored at that key is a chain of all facts sharing that head, so a second
    fact with the same label extends the chain instead of overwriting it.  A
    premise whose pattern head is a concrete label looks up exactly its bucket
    -- O(label key depth) -- instead of scanning every fact.

    A non-pair fact (bare atom/constant) is keyed on itself; that bucket holds
    the bare-atom facts."""

    def __init__(self, index, fact, registry):
        self.registry = registry
        head = FactHead(fact)()
        existing = M.TreeLookup(index, head, registry)()
        if M.IdentityCompare(existing, M.EmptyList)() is M.truth_value:
            bucket = M.Pair(fact, M.EmptyList)
        else:
            bucket = M.Pair(fact, existing)
        self.result = M.TreeInsert(index, head, bucket, registry)()
        super().__init__(
            inputs=M.Pair(index, M.Pair(fact, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class KnowledgeHeadIndexInsertChain(M.Edge):
    def __init__(self, index, facts, registry):
        self.registry = registry
        self.result = self._insert_chain(index, facts)
        super().__init__(
            inputs=M.Pair(index, M.Pair(facts, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _insert_chain(self, index, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return index
        fact = M.Head(facts)()
        next_index = KnowledgeHeadIndexInsert(index, fact, self.registry)()
        return self._insert_chain(next_index, M.Tail(facts)())

    def __call__(self):
        return self.result


class KnowledgeHeadIndexBucket(M.Edge):
    """All facts whose head label equals the given label, as a chain.

    This is the premise-match candidate set.  For a concrete-head premise it is
    exactly the facts that can possibly match; the O(n^k) full scan collapses to
    O(bucket_size^k)."""

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


class RuleReplacementHead(M.Edge):
    """Head label of a rule's replacement (conclusion).  For a unary Rule the
    replacement is the whole RHS; for a MultiRule it is the second input cell.
    A non-pair replacement is its own head."""

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
    """Head label of a rule's first premise.  For a unary Rule the premise is
    the whole LHS pattern; for a MultiRule it is the head of the premise chain.
    A non-pair premise is its own head.  EmptyList when the rule has no
    premises (a fact-rule)."""

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
    """Insert a rule into a trie keyed on a rule's head label (replacement or
    premise).  The bucket at that label is a chain of rules.  Used to build
    RulesByReplacementHead and RulesByPremiseHead at pack-load time, once."""

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
    """All rules whose (replacement or premise) head equals the given label, as
    a chain.  This is the rule-ordering bucket: a label compare gave us the
    candidate rules with zero unification."""

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
    """Key for the match memo: Pair(rule_atom, ExactKey(bucket_root)).

    The bucket root is the root atom of a head-index bucket.  TreeInsert returns
    a fresh wrapper per insert, so identity is not stable across independent
    rebuilds; we key on the structural ExactKey of the bucket root instead.
    Within a search lineage the head bucket for a label changes identity only
    when a fact with that head is added -- otherwise the bucket root is
    TermEqual to its predecessor, hence the same ExactKey, hence the memo entry
    keyed on (rule, ExactKey(bucket_root)) stays valid with no invalidation
    logic: an unchanged bucket yields the same key, hence a hit."""

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
    """Look up a previously computed binding chain for (rule, bucket_root).
    EmptyList means 'not yet computed'."""

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
    """Record a computed binding chain for (rule, bucket_root).  Idempotent:
    storing the same key twice keeps the latest value."""

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
