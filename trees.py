from __future__ import annotations

from .labels import (
    ExactAtomKeyLabel,
    ExactCtorKeyLabel,
    ExactPairKeyLabel,
    IndexAtomKeyLabel,
    IndexCtorKeyLabel,
    IndexPairKeyLabel,
    TreeBucketEntryLabel,
    TreeBucketLabel,
    TreeCtorKeyLabel,
    TreeLabel,
    TreePairKeyLabel,
    TreePatriciaBranchLabel,
    TreePatriciaChoiceLabel,
    TreePatriciaLeafLabel,
    TreePatriciaPairTokenLabel,
    TreePatriciaStopTokenLabel,
    TreePatriciaTokenLabel,
)
from .core import Atom, Edge, EmptyList, Head, IdentityCompare, IdentityLess, Pair, Tail, false_value, truth_value
from .logic import AndAtom, OrAtom
from .tree_patricia import (
    TreePatriciaLongestCommonPrefix,
    TreePatriciaPathEqual,
    TreePatriciaStripPrefix,
    TreePatriciaTokenEqual,
)


class IsPair(Edge):
    def __init__(self, x):
        try:
            Head(x)()
            Tail(x)()
            atom_result = truth_value
        except Exception:
            atom_result = false_value
        self.result = atom_result
        super().__init__(inputs=Pair(x, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreeTermEqual(Edge):
    def __init__(self, left, right):
        self.result = self._equal(left, right)
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def _equal(self, left, right):
        if IdentityCompare(left, right)() is truth_value:
            return truth_value
        left_is_pair = IsPair(left)()
        right_is_pair = IsPair(right)()
        if AndAtom(left_is_pair, right_is_pair)() is truth_value:
            head_equal = self._equal(Head(left)(), Head(right)())
            if head_equal is false_value:
                return false_value
            return self._equal(Tail(left)(), Tail(right)())
        if OrAtom(left_is_pair, right_is_pair)() is truth_value:
            return false_value
        return false_value

    def __call__(self):
        return self.result


class IdentityRedBlackLeftCopyPair(Pair):
    """Immutable Pair node copy sharing an unchanged right branch holder."""

    def __init__(self, original, left):
        Atom.__init__(self)
        self.head = Atom()
        self.head.value = left
        self.tail = original.tail
        self.value = original.value


class IdentityRedBlackRightCopyPair(Pair):
    """Immutable Pair node copy sharing an unchanged left branch holder."""

    def __init__(self, original, right):
        Atom.__init__(self)
        self.head = original.head
        self.tail = Atom()
        self.tail.value = right
        self.value = original.value


class IdentityRedBlackLookup(Edge):
    """Look up an object by machine identity in an immutable red-black tree.

    The tree is EmptyList or a Pair node whose head and tail hold its left and
    right subtrees and whose value directly holds the identity entry Pair.  The
    entry's inherited value slot holds its colour: truth_value denotes red and
    false_value denotes black.  The result is (found, value).
    """

    def __init__(self, tree, key):
        self.result = self._lookup(tree, key)
        super().__init__(inputs=Pair(tree, Pair(key, EmptyList)), results=self.result)

    def _left(self, tree):
        return tree.head.value

    def _key(self, tree):
        return tree.value.head.value

    def _value(self, tree):
        return tree.value.tail.value

    def _right(self, tree):
        return tree.tail.value

    def _same(self, left, right):
        if IdentityLess(left, right)() is truth_value:
            return false_value
        if IdentityLess(right, left)() is truth_value:
            return false_value
        return truth_value

    def _lookup(self, tree, key):
        if tree is EmptyList:
            return Pair(false_value, Pair(EmptyList, EmptyList))
        node_key = self._key(tree)
        if key is node_key:
            return Pair(truth_value, Pair(self._value(tree), EmptyList))
        if IdentityLess(key, node_key)() is truth_value:
            return self._lookup(self._left(tree), key)
        if IdentityLess(node_key, key)() is truth_value:
            return self._lookup(self._right(tree), key)
        return Pair(truth_value, Pair(self._value(tree), EmptyList))

    def __call__(self):
        return self.result


class IdentityRedBlackLookupValue(IdentityRedBlackLookup):
    """Return an identity-associated value directly, or EmptyList if absent."""

    def __init__(self, tree, key):
        self.result = self._lookup_value(tree, key)

    def _lookup_value(self, tree, key):
        current = tree
        while current is not EmptyList:
            entry = current.value
            node_key = entry.head.value
            if key is node_key:
                return entry.tail.value
            if IdentityLess(key, node_key)() is truth_value:
                current = current.head.value
                continue
            if IdentityLess(node_key, key)() is truth_value:
                current = current.tail.value
                continue
            return entry.tail.value
        return EmptyList


class IdentityRedBlackInsert(Edge):
    """Immutably associate an identity key with a value in a red-black tree."""

    def __init__(self, tree, key, value):
        inserted = self._insert(tree, key, value)
        if self._colour(inserted) is false_value:
            self.result = inserted
        else:
            self.result = self._rebuild(
                false_value,
                self._left(inserted),
                self._entry(inserted),
                self._right(inserted),
            )
        super().__init__(
            inputs=Pair(tree, Pair(key, Pair(value, EmptyList))),
            results=self.result,
        )

    def _node(self, colour, left, key, value, right):
        entry = Pair(key, value)
        entry.value = colour
        rebuilt = Pair(left, right)
        rebuilt.value = entry
        return rebuilt

    def _rebuild(self, colour, left, entry, right):
        next_entry = entry
        if entry.value is not colour:
            next_entry = Pair(entry.head.value, entry.tail.value)
            next_entry.value = colour
        rebuilt = Pair(left, right)
        rebuilt.value = next_entry
        return rebuilt

    def _entry(self, tree):
        return tree.value

    def _colour(self, tree):
        return tree.value.value

    def _left(self, tree):
        return tree.head.value

    def _key(self, tree):
        return tree.value.head.value

    def _value(self, tree):
        return tree.value.tail.value

    def _right(self, tree):
        return tree.tail.value

    def _same(self, left, right):
        if IdentityLess(left, right)() is truth_value:
            return false_value
        if IdentityLess(right, left)() is truth_value:
            return false_value
        return truth_value

    def _red(self, tree):
        if tree is EmptyList:
            return false_value
        if self._colour(tree) is truth_value:
            return truth_value
        return false_value

    def _balance(self, colour, left, right, original, changed_side):
        if colour is false_value:
            if changed_side is truth_value:
                if self._red(left) is truth_value:
                    left_left = self._left(left)
                    if self._red(left_left) is truth_value:
                        return self._rebuild(
                            truth_value,
                            self._rebuild(
                                false_value,
                                self._left(left_left),
                                self._entry(left_left),
                                self._right(left_left),
                            ),
                            self._entry(left),
                            self._rebuild(
                                false_value,
                                self._right(left),
                                self._entry(original),
                                right,
                            ),
                        )
                    left_right = self._right(left)
                    if self._red(left_right) is truth_value:
                        return self._rebuild(
                            truth_value,
                            self._rebuild(
                                false_value,
                                self._left(left),
                                self._entry(left),
                                self._left(left_right),
                            ),
                            self._entry(left_right),
                            self._rebuild(
                                false_value,
                                self._right(left_right),
                                self._entry(original),
                                right,
                            ),
                        )
            elif self._red(right) is truth_value:
                right_left = self._left(right)
                if self._red(right_left) is truth_value:
                    return self._rebuild(
                        truth_value,
                        self._rebuild(
                            false_value,
                            left,
                            self._entry(original),
                            self._left(right_left),
                        ),
                        self._entry(right_left),
                        self._rebuild(
                            false_value,
                            self._right(right_left),
                            self._entry(right),
                            self._right(right),
                        ),
                    )
                right_right = self._right(right)
                if self._red(right_right) is truth_value:
                    return self._rebuild(
                        truth_value,
                        self._rebuild(
                            false_value,
                            left,
                            self._entry(original),
                            self._left(right),
                        ),
                        self._entry(right),
                        self._rebuild(
                            false_value,
                            self._left(right_right),
                            self._entry(right_right),
                            self._right(right_right),
                        ),
                    )
        if changed_side is truth_value:
            return IdentityRedBlackLeftCopyPair(original, left)
        return IdentityRedBlackRightCopyPair(original, right)

    def _insert(self, tree, key, value):
        if tree is EmptyList:
            return self._node(
                truth_value,
                EmptyList,
                key,
                value,
                EmptyList,
            )
        node_key = self._key(tree)
        if key is node_key:
            return self._node(
                self._colour(tree),
                self._left(tree),
                node_key,
                value,
                self._right(tree),
            )
        if IdentityLess(key, node_key)() is truth_value:
            return self._balance(
                self._colour(tree),
                self._insert(self._left(tree), key, value),
                self._right(tree),
                tree,
                truth_value,
            )
        if IdentityLess(node_key, key)() is truth_value:
            return self._balance(
                self._colour(tree),
                self._left(tree),
                self._insert(self._right(tree), key, value),
                tree,
                false_value,
            )
        return self._node(
            self._colour(tree),
            self._left(tree),
            node_key,
            value,
            self._right(tree),
        )

    def __call__(self):
        return self.result


class IdentityRedBlackInsertMissing(IdentityRedBlackInsert):
    """Insert only when an identity key is absent and expose machine insertion truth."""

    def __init__(self, tree, key, value):
        self.inserted = false_value
        inserted_tree = self._insert_missing(tree, key, value)
        if self.inserted is truth_value:
            if self._colour(inserted_tree) is false_value:
                self.result = inserted_tree
            else:
                self.result = self._rebuild(
                    false_value,
                    self._left(inserted_tree),
                    self._entry(inserted_tree),
                    self._right(inserted_tree),
                )
        else:
            self.result = tree

    def _insert_missing(self, tree, key, value):
        if tree is EmptyList:
            self.inserted = truth_value
            return self._node(
                truth_value,
                EmptyList,
                key,
                value,
                EmptyList,
            )
        node_key = self._key(tree)
        if key is node_key:
            return tree
        if IdentityLess(key, node_key)() is truth_value:
            next_left = self._insert_missing(self._left(tree), key, value)
            if self.inserted is false_value:
                return tree
            return self._balance(
                self._colour(tree),
                next_left,
                self._right(tree),
                tree,
                truth_value,
            )
        if IdentityLess(node_key, key)() is truth_value:
            next_right = self._insert_missing(self._right(tree), key, value)
            if self.inserted is false_value:
                return tree
            return self._balance(
                self._colour(tree),
                self._left(tree),
                next_right,
                tree,
                false_value,
            )
        return tree


class IdentityRedBlackValid(Edge):
    """Check ordering, colour, red-parent, and black-height invariants."""

    def __init__(self, tree):
        if IdentityCompare(tree, EmptyList)() is truth_value:
            self.result = truth_value
        elif IdentityCompare(self._colour(tree), false_value)() is false_value:
            self.result = false_value
        else:
            checked = self._validate(
                tree,
                false_value,
                EmptyList,
                false_value,
                EmptyList,
            )
            self.result = Head(checked)()
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def _colour(self, tree):
        return tree.value.value

    def _left(self, tree):
        return tree.head.value

    def _key(self, tree):
        return tree.value.head.value

    def _right(self, tree):
        return tree.tail.value

    def _red(self, tree):
        if IdentityCompare(tree, EmptyList)() is truth_value:
            return false_value
        return IdentityCompare(self._colour(tree), truth_value)()

    def _invalid(self):
        return Pair(false_value, Pair(EmptyList, EmptyList))

    def _validate(self, tree, has_lower, lower, has_upper, upper):
        if IdentityCompare(tree, EmptyList)() is truth_value:
            return Pair(truth_value, Pair(EmptyList, EmptyList))

        colour = self._colour(tree)
        if IdentityCompare(colour, truth_value)() is false_value:
            if IdentityCompare(colour, false_value)() is false_value:
                return self._invalid()

        key = self._key(tree)
        if IdentityCompare(has_lower, truth_value)() is truth_value:
            if IdentityLess(lower, key)() is false_value:
                return self._invalid()
        if IdentityCompare(has_upper, truth_value)() is truth_value:
            if IdentityLess(key, upper)() is false_value:
                return self._invalid()

        left = self._left(tree)
        right = self._right(tree)
        if IdentityCompare(colour, truth_value)() is truth_value:
            if self._red(left) is truth_value:
                return self._invalid()
            if self._red(right) is truth_value:
                return self._invalid()

        left_checked = self._validate(
            left,
            has_lower,
            lower,
            truth_value,
            key,
        )
        if Head(left_checked)() is false_value:
            return self._invalid()
        right_checked = self._validate(
            right,
            truth_value,
            key,
            has_upper,
            upper,
        )
        if Head(right_checked)() is false_value:
            return self._invalid()

        left_height = Head(Tail(left_checked)())()
        right_height = Head(Tail(right_checked)())()
        if TreeTermEqual(left_height, right_height)() is false_value:
            return self._invalid()
        if IdentityCompare(colour, false_value)() is truth_value:
            left_height = Pair(truth_value, left_height)
        return Pair(truth_value, Pair(left_height, EmptyList))

    def __call__(self):
        return self.result


class Tree(Atom):
    def __init__(self, root, key_store=EmptyList):
        super().__init__()
        self.value = Pair(TreeLabel, Pair(root, Pair(key_store, EmptyList)))


class TreeRoot(Edge):
    def __init__(self, tree):
        pair = tree()
        payload = Tail(pair)()
        self.result = Head(payload)()
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsTree(Edge):
    def __init__(self, tree):
        pair = tree()
        if pair is None:
            self.result = false_value
        else:
            self.result = IdentityCompare(Head(pair)(), TreeLabel)()
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreeKeyStore(Edge):
    def __init__(self, tree):
        if IsTree(tree)() is truth_value:
            pair = tree()
            payload = Tail(pair)()
            tail = Tail(payload)()
            if IdentityCompare(tail, EmptyList)() is truth_value:
                self.result = EmptyList
            else:
                self.result = Head(tail)()
        else:
            self.result = EmptyList
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreeNode(Atom):
    """Legacy BST node retained for old snapshots and migration shims."""

    def __init__(self, key, fact, left, right, registry=None):
        super().__init__()
        self.value = Pair(key, Pair(fact, Pair(left, Pair(right, EmptyList))))


class TreeKey(Edge):
    def __init__(self, tree):
        pair = tree()
        self.result = Head(pair)()
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreeFact(Edge):
    def __init__(self, tree):
        pair = tree()
        self.result = Head(Tail(pair)())()
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreeLeft(Edge):
    def __init__(self, tree):
        pair = tree()
        self.result = Head(Tail(Tail(pair)())())()
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreeRight(Edge):
    def __init__(self, tree):
        pair = tree()
        self.result = Head(Tail(Tail(Tail(pair)())())())()
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreeStoredRoot(Edge):
    def __init__(self, tree):
        self.result = self._root(tree)
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def _root(self, tree):
        if IdentityCompare(tree, EmptyList)() is truth_value:
            return EmptyList
        if IsTree(tree)() is truth_value:
            return TreeRoot(tree)()
        return tree

    def __call__(self):
        return self.result


class ExactAtomKey(Edge):
    def __init__(self, atom):
        self.result = Pair(ExactAtomKeyLabel, Pair(atom, EmptyList))
        super().__init__(inputs=Pair(atom, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ExactPairKey(Edge):
    def __init__(self, head_key, tail_key):
        self.result = Pair(ExactPairKeyLabel, Pair(head_key, Pair(tail_key, EmptyList)))
        super().__init__(inputs=Pair(head_key, Pair(tail_key, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ExactCtorKey(Edge):
    def __init__(self, label, arg_keys):
        self.result = Pair(ExactCtorKeyLabel, Pair(label, Pair(arg_keys, EmptyList)))
        super().__init__(inputs=Pair(label, Pair(arg_keys, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ExactKeyArgs(Edge):
    def __init__(self, args, registry):
        self.registry = registry
        self.result = self._walk(args)
        super().__init__(
            inputs=Pair(args, Pair(registry, EmptyList)),
            results=self.result,
        )

    def _walk(self, args):
        if IdentityCompare(args, EmptyList)() is truth_value:
            return EmptyList
        head_key = ExactKey(
            Head(args)(),
            self.registry,
        )()
        tail_keys = self._walk(Tail(args)())
        return Pair(head_key, tail_keys)

    def __call__(self):
        return self.result


class ExactKey(Edge):
    def __init__(self, term, registry):
        self.registry = registry
        self.result = self._key(term)
        super().__init__(
            inputs=Pair(term, Pair(registry, EmptyList)),
            results=self.result,
        )

    def _key(self, term):
        if IsPair(term)() is truth_value:
            head_key = self._key(Head(term)())
            tail_key = self._key(Tail(term)())
            return ExactPairKey(head_key, tail_key)()

        from .constructors import GetConstructor

        constructor = GetConstructor(term, self.registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            return ExactAtomKey(term)()
        label = Head(constructor)()
        args = Tail(constructor)()
        arg_keys = ExactKeyArgs(args, self.registry)()
        return ExactCtorKey(label, arg_keys)()

    def __call__(self):
        return self.result


class ExactKeyOf(Edge):
    def __init__(self, term, registry):
        self.result = ExactKey(term, registry)()
        super().__init__(
            inputs=Pair(term, Pair(registry, EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IndexAtomKey(Edge):
    def __init__(self, exact_key):
        self.result = Pair(IndexAtomKeyLabel, EmptyList)
        super().__init__(inputs=Pair(exact_key, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IndexPairKey(Edge):
    def __init__(self, head_key, tail_key):
        self.result = Pair(IndexPairKeyLabel, Pair(head_key, Pair(tail_key, EmptyList)))
        super().__init__(inputs=Pair(head_key, Pair(tail_key, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IndexCtorKey(Edge):
    def __init__(self, label, arg_keys):
        self.result = Pair(IndexCtorKeyLabel, Pair(label, Pair(arg_keys, EmptyList)))
        super().__init__(inputs=Pair(label, Pair(arg_keys, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IndexKeyArgs(Edge):
    def __init__(self, args):
        self.result = self._walk(args)
        super().__init__(inputs=Pair(args, EmptyList), results=self.result)

    def _walk(self, args):
        if IdentityCompare(args, EmptyList)() is truth_value:
            return EmptyList
        head_key = IndexKey(Head(args)())()
        tail_keys = self._walk(Tail(args)())
        return Pair(head_key, tail_keys)

    def __call__(self):
        return self.result


class IndexKey(Edge):
    def __init__(self, exact_key):
        self.result = self._index(exact_key)
        super().__init__(inputs=Pair(exact_key, EmptyList), results=self.result)

    def _payload_head(self, term):
        return Head(Tail(term)())()

    def _payload_tail_head(self, term):
        return Head(Tail(Tail(term)())())()

    def _index(self, exact_key):
        if IsPair(exact_key)() is false_value:
            return IndexAtomKey(exact_key)()
        label = Head(exact_key)()
        if IdentityCompare(label, ExactAtomKeyLabel)() is truth_value:
            return IndexAtomKey(exact_key)()
        if IdentityCompare(label, ExactPairKeyLabel)() is truth_value:
            head_key = IndexKey(self._payload_head(exact_key))()
            tail_key = IndexKey(self._payload_tail_head(exact_key))()
            return IndexPairKey(head_key, tail_key)()
        if IdentityCompare(label, ExactCtorKeyLabel)() is truth_value:
            ctor_label = self._payload_head(exact_key)
            arg_keys = IndexKeyArgs(self._payload_tail_head(exact_key))()
            return IndexCtorKey(ctor_label, arg_keys)()
        return IndexAtomKey(exact_key)()

    def __call__(self):
        return self.result


class TreePairKey(Edge):
    def __init__(self, head_key, tail_key):
        self.result = ExactPairKey(head_key, tail_key)()
        super().__init__(inputs=Pair(head_key, Pair(tail_key, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TreeCtorKey(Edge):
    def __init__(self, label, arg_keys):
        self.result = ExactCtorKey(label, arg_keys)()
        super().__init__(inputs=Pair(label, Pair(arg_keys, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TreeStructuralKeyArgs(Edge):
    def __init__(self, args, registry):
        self.result = ExactKeyArgs(args, registry)()
        super().__init__(inputs=Pair(args, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TreeStructuralKey(Edge):
    def __init__(self, term, registry):
        self.result = ExactKey(term, registry)()
        super().__init__(inputs=Pair(term, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TreeBucketEntry(Edge):
    def __init__(self, exact_key, key, fact):
        self.result = Pair(
            TreeBucketEntryLabel,
            Pair(exact_key, Pair(key, Pair(fact, EmptyList))),
        )
        super().__init__(
            inputs=Pair(exact_key, Pair(key, Pair(fact, EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TreeBucket(Edge):
    def __init__(self, entries):
        self.result = Pair(TreeBucketLabel, Pair(entries, EmptyList))
        super().__init__(inputs=Pair(entries, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreePatriciaToken(Edge):
    def __init__(self, payload):
        self.result = Pair(TreePatriciaTokenLabel, Pair(payload, EmptyList))
        super().__init__(inputs=Pair(payload, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TreePatriciaLeaf(Edge):
    def __init__(self, suffix, bucket):
        self.result = Pair(
            TreePatriciaLeafLabel,
            Pair(suffix, Pair(bucket, EmptyList)),
        )
        super().__init__(
            inputs=Pair(suffix, Pair(bucket, EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TreePatriciaBranch(Edge):
    def __init__(self, prefix, choices):
        self.result = Pair(TreePatriciaBranchLabel, Pair(prefix, Pair(choices, EmptyList)))
        super().__init__(inputs=Pair(prefix, Pair(choices, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TreePatriciaChoice(Edge):
    def __init__(self, token, subtree):
        self.result = Pair(TreePatriciaChoiceLabel, Pair(token, Pair(subtree, EmptyList)))
        super().__init__(inputs=Pair(token, Pair(subtree, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TreePatriciaPath(Edge):
    def __init__(self, exact_key):
        self.result = self._tokens(exact_key, EmptyList)
        super().__init__(inputs=Pair(exact_key, EmptyList), results=self.result)

    def _tokens(self, term, acc):
        # Build the token list in one O(depth) pass by consing each
        # contribution onto the suffix accumulator. The emitted order matches
        # the original _append-based version exactly:
        #   pair-token, head-tokens, tail-tokens, stop-token, acc
        # No reverse, no left-fold append -> O(depth) instead of O(depth^2).
        if IsPair(term)() is truth_value:
            stop_suffix = Pair(TreePatriciaToken(TreePatriciaStopTokenLabel)(), acc)
            tail_tokens = self._tokens(Tail(term)(), stop_suffix)
            head_tokens = self._tokens(Head(term)(), tail_tokens)
            return Pair(TreePatriciaToken(TreePatriciaPairTokenLabel)(), head_tokens)
        return Pair(TreePatriciaToken(term)(), acc)

    def __call__(self):
        return self.result


class TreePatriciaLookup(Edge):
    def __init__(self, tree, path, exact_key):
        self.result = self._lookup(tree, path, exact_key)
        super().__init__(inputs=Pair(tree, Pair(path, Pair(exact_key, EmptyList))), results=self.result)

    def _is_leaf(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaLeafLabel)()

    def _is_branch(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaBranchLabel)()

    def _leaf_suffix(self, leaf):
        return Head(Tail(leaf)())()

    def _leaf_payload(self, leaf):
        return Head(Tail(Tail(leaf)())())()

    def _leaf_is_bucketed(self, leaf):
        payload = self._leaf_payload(leaf)
        if IsPair(payload)() is false_value:
            return false_value
        return IdentityCompare(Head(payload)(), TreeBucketLabel)()

    def _bucket_entries(self, bucket):
        return Head(Tail(bucket)())()

    def _bucket_entry_exact_key(self, entry):
        return Head(Tail(entry)())()

    def _bucket_entry_fact(self, entry):
        return Head(Tail(Tail(Tail(entry)())())())()

    def _leaf_exact_key(self, leaf):
        return self._leaf_payload(leaf)

    def _leaf_fact(self, leaf):
        return Head(Tail(Tail(Tail(Tail(leaf)())())())())()

    def _branch_prefix(self, branch):
        return Head(Tail(branch)())()

    def _branch_choices(self, branch):
        return Head(Tail(Tail(branch)())())()

    def _choice_token(self, choice):
        return Head(Tail(choice)())()

    def _choice_subtree(self, choice):
        return Head(Tail(Tail(choice)())())()

    def _strip_prefix(self, path, prefix):
        return TreePatriciaStripPrefix(path, prefix)()

    def _find_choice(self, choices, token):
        if IdentityCompare(choices, EmptyList)() is truth_value:
            return EmptyList
        choice = Head(choices)()
        if TreePatriciaTokenEqual(self._choice_token(choice), token)() is truth_value:
            return self._choice_subtree(choice)
        return self._find_choice(Tail(choices)(), token)

    def _lookup_bucket(self, bucket, exact_key):
        return self._lookup_bucket_entries(self._bucket_entries(bucket), exact_key)

    def _lookup_bucket_entries(self, entries, exact_key):
        if IdentityCompare(entries, EmptyList)() is truth_value:
            return EmptyList
        entry = Head(entries)()
        if IdentityCompare(self._bucket_entry_exact_key(entry), exact_key)() is truth_value:
            return self._bucket_entry_fact(entry)
        if TreeTermEqual(self._bucket_entry_exact_key(entry), exact_key)() is truth_value:
            return self._bucket_entry_fact(entry)
        return self._lookup_bucket_entries(Tail(entries)(), exact_key)

    def _lookup(self, tree, path, exact_key):
        if IdentityCompare(tree, EmptyList)() is truth_value:
            return EmptyList
        if self._is_leaf(tree) is truth_value:
            if TreePatriciaPathEqual(self._leaf_suffix(tree), path)() is false_value:
                return EmptyList
            if self._leaf_is_bucketed(tree) is truth_value:
                return self._lookup_bucket(self._leaf_payload(tree), exact_key)
            if IdentityCompare(self._leaf_exact_key(tree), exact_key)() is truth_value:
                return self._leaf_fact(tree)
            if TreeTermEqual(self._leaf_exact_key(tree), exact_key)() is false_value:
                return EmptyList
            return self._leaf_fact(tree)
        if self._is_branch(tree) is false_value:
            return EmptyList
        stripped = self._strip_prefix(path, self._branch_prefix(tree))
        if Head(stripped)() is false_value:
            return EmptyList
        remainder = Head(Tail(stripped)())()
        if IdentityCompare(remainder, EmptyList)() is truth_value:
            return EmptyList
        token = Head(remainder)()
        child = self._find_choice(self._branch_choices(tree), token)
        if IdentityCompare(child, EmptyList)() is truth_value:
            return EmptyList
        return self._lookup(child, Tail(remainder)(), exact_key)

    def __call__(self):
        return self.result


class TreePatriciaInsert(Edge):
    def __init__(self, tree, path, exact_key, key, fact):
        self.result = self._insert(tree, path, exact_key, key, fact)
        super().__init__(
            inputs=Pair(tree, Pair(path, Pair(exact_key, Pair(key, Pair(fact, EmptyList))))),
            results=self.result,
        )

    def _is_leaf(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaLeafLabel)()

    def _is_branch(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaBranchLabel)()

    def _leaf_suffix(self, leaf):
        return Head(Tail(leaf)())()

    def _leaf_payload(self, leaf):
        return Head(Tail(Tail(leaf)())())()

    def _leaf_is_bucketed(self, leaf):
        payload = self._leaf_payload(leaf)
        if IsPair(payload)() is false_value:
            return false_value
        return IdentityCompare(Head(payload)(), TreeBucketLabel)()

    def _bucket_entries(self, bucket):
        return Head(Tail(bucket)())()

    def _bucket_entry_exact_key(self, entry):
        return Head(Tail(entry)())()

    def _bucket_entry_key(self, entry):
        return Head(Tail(Tail(entry)())())()

    def _bucket_entry_fact(self, entry):
        return Head(Tail(Tail(Tail(entry)())())())()

    def _leaf_exact_key(self, leaf):
        return self._leaf_payload(leaf)

    def _leaf_key(self, leaf):
        return Head(Tail(Tail(Tail(leaf)())())())()

    def _leaf_fact(self, leaf):
        return Head(Tail(Tail(Tail(Tail(leaf)())())())())()

    def _branch_prefix(self, branch):
        return Head(Tail(branch)())()

    def _branch_choices(self, branch):
        return Head(Tail(Tail(branch)())())()

    def _choice_token(self, choice):
        return Head(Tail(choice)())()

    def _choice_subtree(self, choice):
        return Head(Tail(Tail(choice)())())()

    def _longest_common_prefix(self, left, right):
        return TreePatriciaLongestCommonPrefix(left, right)()

    def _find_choice(self, choices, token):
        if IdentityCompare(choices, EmptyList)() is truth_value:
            return EmptyList
        choice = Head(choices)()
        if TreePatriciaTokenEqual(self._choice_token(choice), token)() is truth_value:
            return self._choice_subtree(choice)
        return self._find_choice(Tail(choices)(), token)

    def _upsert_choice(self, choices, token, subtree):
        if IdentityCompare(choices, EmptyList)() is truth_value:
            return Pair(TreePatriciaChoice(token, subtree)(), EmptyList)
        choice = Head(choices)()
        rest = Tail(choices)()
        if TreePatriciaTokenEqual(self._choice_token(choice), token)() is truth_value:
            return Pair(TreePatriciaChoice(token, subtree)(), rest)
        return Pair(choice, self._upsert_choice(rest, token, subtree))

    def _single_bucket(self, exact_key, key, fact):
        entry = TreeBucketEntry(exact_key, key, fact)()
        return TreeBucket(Pair(entry, EmptyList))()

    def _legacy_bucket(self, leaf):
        return self._single_bucket(self._leaf_exact_key(leaf), self._leaf_key(leaf), self._leaf_fact(leaf))

    def _leaf_bucket(self, leaf):
        if self._leaf_is_bucketed(leaf) is truth_value:
            return self._leaf_payload(leaf)
        return self._legacy_bucket(leaf)

    def _upsert_bucket(self, bucket, exact_key, key, fact):
        return TreeBucket(self._upsert_bucket_entries(self._bucket_entries(bucket), exact_key, key, fact))()

    def _upsert_bucket_entries(self, entries, exact_key, key, fact):
        next_entry = TreeBucketEntry(exact_key, key, fact)()
        if IdentityCompare(entries, EmptyList)() is truth_value:
            return Pair(next_entry, EmptyList)
        entry = Head(entries)()
        if IdentityCompare(self._bucket_entry_exact_key(entry), exact_key)() is truth_value:
            return Pair(next_entry, Tail(entries)())
        if TreeTermEqual(self._bucket_entry_exact_key(entry), exact_key)() is truth_value:
            return Pair(next_entry, Tail(entries)())
        return Pair(entry, self._upsert_bucket_entries(Tail(entries)(), exact_key, key, fact))

    def _insert_into_leaf(self, tree, path, exact_key, key, fact):
        leaf_suffix = self._leaf_suffix(tree)
        if TreePatriciaPathEqual(leaf_suffix, path)() is truth_value:
            next_bucket = self._upsert_bucket(self._leaf_bucket(tree), exact_key, key, fact)
            return TreePatriciaLeaf(path, next_bucket)()
        split = self._longest_common_prefix(path, leaf_suffix)
        common = Head(split)()
        path_rest = Head(Tail(split)())()
        leaf_rest = Head(Tail(Tail(split)())())()
        leaf_token = Head(leaf_rest)()
        leaf_child = TreePatriciaLeaf(
            Tail(leaf_rest)(),
            self._leaf_bucket(tree),
        )()
        new_token = Head(path_rest)()
        new_child = TreePatriciaLeaf(Tail(path_rest)(), self._single_bucket(exact_key, key, fact))()
        return TreePatriciaBranch(
            common,
            Pair(
                TreePatriciaChoice(leaf_token, leaf_child)(),
                Pair(TreePatriciaChoice(new_token, new_child)(), EmptyList),
            ),
        )()

    def _insert_into_branch(self, tree, path, exact_key, key, fact):
        prefix = self._branch_prefix(tree)
        split = self._longest_common_prefix(path, prefix)
        common = Head(split)()
        path_rest = Head(Tail(split)())()
        prefix_rest = Head(Tail(Tail(split)())())()
        if IdentityCompare(prefix_rest, EmptyList)() is truth_value:
            if IdentityCompare(path_rest, EmptyList)() is truth_value:
                return tree
            token = Head(path_rest)()
            suffix = Tail(path_rest)()
            choices = self._branch_choices(tree)
            child = self._find_choice(choices, token)
            if IdentityCompare(child, EmptyList)() is truth_value:
                next_child = TreePatriciaLeaf(suffix, self._single_bucket(exact_key, key, fact))()
            else:
                next_child = self._insert(child, suffix, exact_key, key, fact)
            return TreePatriciaBranch(prefix, self._upsert_choice(choices, token, next_child))()
        old_token = Head(prefix_rest)()
        old_child = TreePatriciaBranch(Tail(prefix_rest)(), self._branch_choices(tree))()
        new_token = Head(path_rest)()
        new_child = TreePatriciaLeaf(Tail(path_rest)(), self._single_bucket(exact_key, key, fact))()
        return TreePatriciaBranch(
            common,
            Pair(
                TreePatriciaChoice(old_token, old_child)(),
                Pair(TreePatriciaChoice(new_token, new_child)(), EmptyList),
            ),
        )()

    def _insert(self, tree, path, exact_key, key, fact):
        if IdentityCompare(tree, EmptyList)() is truth_value:
            return TreePatriciaLeaf(path, self._single_bucket(exact_key, key, fact))()
        if self._is_leaf(tree) is truth_value:
            return self._insert_into_leaf(tree, path, exact_key, key, fact)
        if self._is_branch(tree) is truth_value:
            return self._insert_into_branch(tree, path, exact_key, key, fact)
        return TreePatriciaLeaf(path, self._single_bucket(exact_key, key, fact))()

    def __call__(self):
        return self.result


class TreeEntries(Edge):
    def __init__(self, tree):
        self.result = self._entries(TreeStoredRoot(tree)())
        super().__init__(inputs=Pair(tree, EmptyList), results=self.result)

    def _append(self, left, right):
        reversed_left = EmptyList
        current = left
        while IdentityCompare(current, EmptyList)() is false_value:
            reversed_left = Pair(Head(current)(), reversed_left)
            current = Tail(current)()
        result = right
        current = reversed_left
        while IdentityCompare(current, EmptyList)() is false_value:
            result = Pair(Head(current)(), result)
            current = Tail(current)()
        return result

    def _is_leaf(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaLeafLabel)()

    def _is_branch(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaBranchLabel)()

    def _leaf_payload(self, leaf):
        return Head(Tail(Tail(leaf)())())()

    def _leaf_is_bucketed(self, leaf):
        payload = self._leaf_payload(leaf)
        if IsPair(payload)() is false_value:
            return false_value
        return IdentityCompare(Head(payload)(), TreeBucketLabel)()

    def _bucket_entries(self, bucket):
        return Head(Tail(bucket)())()

    def _bucket_entry_key(self, entry):
        return Head(Tail(Tail(entry)())())()

    def _bucket_entry_fact(self, entry):
        return Head(Tail(Tail(Tail(entry)())())())()

    def _leaf_key(self, leaf):
        return Head(Tail(Tail(Tail(leaf)())())())()

    def _leaf_fact(self, leaf):
        return Head(Tail(Tail(Tail(Tail(leaf)())())())())()

    def _branch_choices(self, branch):
        return Head(Tail(Tail(branch)())())()

    def _choice_subtree(self, choice):
        return Head(Tail(Tail(choice)())())()

    def _choice_entries(self, choices):
        if IdentityCompare(choices, EmptyList)() is truth_value:
            return EmptyList
        choice = Head(choices)()
        return self._append(self._entries(self._choice_subtree(choice)), self._choice_entries(Tail(choices)()))

    def _bucket_as_entries(self, bucket_entries):
        if IdentityCompare(bucket_entries, EmptyList)() is truth_value:
            return EmptyList
        entry = Head(bucket_entries)()
        next_entry = Pair(self._bucket_entry_key(entry), Pair(self._bucket_entry_fact(entry), EmptyList))
        return Pair(next_entry, self._bucket_as_entries(Tail(bucket_entries)()))

    def _legacy_entries(self, node):
        if IdentityCompare(node, EmptyList)() is truth_value:
            return EmptyList
        try:
            left = TreeLeft(node)()
            key = TreeKey(node)()
            fact = TreeFact(node)()
            right = TreeRight(node)()
        except Exception:
            return EmptyList
        left_entries = self._legacy_entries(left)
        here = Pair(Pair(key, Pair(fact, EmptyList)), EmptyList)
        right_entries = self._legacy_entries(right)
        return self._append(left_entries, self._append(here, right_entries))

    def _entries(self, tree):
        if IdentityCompare(tree, EmptyList)() is truth_value:
            return EmptyList
        if self._is_leaf(tree) is truth_value:
            if self._leaf_is_bucketed(tree) is truth_value:
                return self._bucket_as_entries(self._bucket_entries(self._leaf_payload(tree)))
            entry = Pair(self._leaf_key(tree), Pair(self._leaf_fact(tree), EmptyList))
            return Pair(entry, EmptyList)
        if self._is_branch(tree) is truth_value:
            return self._choice_entries(self._branch_choices(tree))
        return self._legacy_entries(tree)

    def __call__(self):
        return self.result


class TreeInsert(Edge):
    def __init__(self, tree, key, fact, registry):
        self.registry = registry
        root, key_store = self._insert_tree(tree, key, fact)
        self.result = Tree(root, key_store)
        super().__init__(inputs=Pair(tree, Pair(key, Pair(fact, EmptyList))), results=self.result)

    def _is_leaf(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaLeafLabel)()

    def _is_branch(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaBranchLabel)()

    def _leaf_payload(self, leaf):
        return Head(Tail(Tail(leaf)())())()

    def _leaf_is_bucketed(self, leaf):
        payload = self._leaf_payload(leaf)
        if IsPair(payload)() is false_value:
            return false_value
        return IdentityCompare(Head(payload)(), TreeBucketLabel)()

    def _branch_choices(self, branch):
        return Head(Tail(Tail(branch)())())()

    def _choice_subtree(self, choice):
        return Head(Tail(Tail(choice)())())()

    def _choices_are_bucketed(self, choices):
        if IdentityCompare(choices, EmptyList)() is truth_value:
            return truth_value
        choice = Head(choices)()
        subtree_ok = self._is_bucketed_root(self._choice_subtree(choice))
        if subtree_ok is false_value:
            return false_value
        return self._choices_are_bucketed(Tail(choices)())

    def _is_bucketed_root(self, tree):
        if IdentityCompare(tree, EmptyList)() is truth_value:
            return truth_value
        if self._is_leaf(tree) is truth_value:
            return self._leaf_is_bucketed(tree)
        if self._is_branch(tree) is truth_value:
            return self._choices_are_bucketed(self._branch_choices(tree))
        return false_value

    def _insert_entries(self, entries, root):
        if IdentityCompare(entries, EmptyList)() is truth_value:
            return root
        entry = Head(entries)()
        next_root, self._key_store = self._insert_root(root, Head(entry)(), Head(Tail(entry)())())
        return self._insert_entries(Tail(entries)(), next_root)

    def _insert_root(self, root, key, fact):
        exact_key = ExactKey(key, self.registry)()
        interned_key, key_store = self._intern_exact_key(self._key_store, exact_key)
        index_key = IndexKey(interned_key)()
        path = TreePatriciaPath(index_key)()
        next_root = TreePatriciaInsert(root, path, interned_key, key, fact)()
        return next_root, key_store

    def _intern_exact_key(self, key_store, exact_key):
        path = TreePatriciaPath(exact_key)()
        existing = TreePatriciaLookup(key_store, path, exact_key)()
        if IdentityCompare(existing, EmptyList)() is false_value:
            return existing, key_store
        next_store = TreePatriciaInsert(key_store, path, exact_key, exact_key, exact_key)()
        return exact_key, next_store

    def _insert_tree(self, tree, key, fact):
        root = TreeStoredRoot(tree)()
        self._key_store = TreeKeyStore(tree)()
        if IdentityCompare(root, EmptyList)() is truth_value:
            return self._insert_root(EmptyList, key, fact)
        if self._is_bucketed_root(root) is truth_value:
            return self._insert_root(root, key, fact)
        migrated = self._insert_entries(TreeEntries(tree)(), EmptyList)
        return self._insert_root(migrated, key, fact)

    def __call__(self):
        return self.result


class TreeLookup(Edge):
    def __init__(self, tree, key, registry=None):
        self.registry = self._effective_registry(registry, tree)
        self.result = self._lookup_tree(tree, key)
        if registry is None:
            inputs = Pair(tree, Pair(key, EmptyList))
        else:
            inputs = Pair(tree, Pair(key, Pair(registry, EmptyList)))
        super().__init__(inputs=inputs, results=self.result)

    def _effective_registry(self, registry, tree):
        if registry is not None:
            return registry
        if AllConstructors is not None:
            return AllConstructors
        return tree

    def _is_leaf(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaLeafLabel)()

    def _is_branch(self, tree):
        if IsPair(tree)() is false_value:
            return false_value
        return IdentityCompare(Head(tree)(), TreePatriciaBranchLabel)()

    def _leaf_payload(self, leaf):
        return Head(Tail(Tail(leaf)())())()

    def _leaf_is_bucketed(self, leaf):
        payload = self._leaf_payload(leaf)
        if IsPair(payload)() is false_value:
            return false_value
        return IdentityCompare(Head(payload)(), TreeBucketLabel)()

    def _branch_choices(self, branch):
        return Head(Tail(Tail(branch)())())()

    def _choice_subtree(self, choice):
        return Head(Tail(Tail(choice)())())()

    def _choices_are_bucketed(self, choices):
        if IdentityCompare(choices, EmptyList)() is truth_value:
            return truth_value
        choice = Head(choices)()
        subtree_ok = self._is_bucketed_root(self._choice_subtree(choice))
        if subtree_ok is false_value:
            return false_value
        return self._choices_are_bucketed(Tail(choices)())

    def _is_bucketed_root(self, tree):
        if IdentityCompare(tree, EmptyList)() is truth_value:
            return truth_value
        if self._is_leaf(tree) is truth_value:
            return self._leaf_is_bucketed(tree)
        if self._is_branch(tree) is truth_value:
            return self._choices_are_bucketed(self._branch_choices(tree))
        return false_value

    def _lookup_entries(self, entries, exact_key):
        if IdentityCompare(entries, EmptyList)() is truth_value:
            return EmptyList
        entry = Head(entries)()
        entry_key = Head(entry)()
        entry_exact_key = ExactKey(entry_key, self.registry)()
        if TreeTermEqual(entry_exact_key, exact_key)() is truth_value:
            return Head(Tail(entry)())()
        return self._lookup_entries(Tail(entries)(), exact_key)

    def _lookup_tree(self, tree, key):
        exact_key = self._interned_key(tree, key)
        root = TreeStoredRoot(tree)()
        if IdentityCompare(root, EmptyList)() is truth_value:
            return EmptyList
        if self._is_bucketed_root(root) is truth_value:
            path = TreePatriciaPath(IndexKey(exact_key)())()
            found = TreePatriciaLookup(root, path, exact_key)()
            if IdentityCompare(found, EmptyList)() is false_value:
                return found
        return self._lookup_entries(TreeEntries(tree)(), exact_key)

    def _interned_key(self, tree, key):
        exact_key = ExactKey(key, self.registry)()
        key_store = TreeKeyStore(tree)()
        if IdentityCompare(key_store, EmptyList)() is truth_value:
            return exact_key
        path = TreePatriciaPath(exact_key)()
        existing = TreePatriciaLookup(key_store, path, exact_key)()
        if IdentityCompare(existing, EmptyList)() is truth_value:
            return exact_key
        return existing

    def __call__(self):
        return self.result


EmptyTree = Tree(EmptyList)
AllConstructors = EmptyTree


def sync_from_namespace(namespace):
    for name in (
        "AllConstructors",
        "EmptyList",
        "TreeLabel",
        "ExactAtomKeyLabel",
        "ExactPairKeyLabel",
        "ExactCtorKeyLabel",
        "IndexAtomKeyLabel",
        "IndexPairKeyLabel",
        "IndexCtorKeyLabel",
        "TreePairKeyLabel",
        "TreeCtorKeyLabel",
        "TreeBucketLabel",
        "TreeBucketEntryLabel",
        "TreePatriciaTokenLabel",
        "TreePatriciaPairTokenLabel",
        "TreePatriciaStopTokenLabel",
        "TreePatriciaLeafLabel",
        "TreePatriciaBranchLabel",
        "TreePatriciaChoiceLabel",
        "truth_value",
        "false_value",
    ):
        if name in namespace:
            globals()[name] = namespace[name]
    globals()["EmptyTree"] = Tree(EmptyList)


__all__ = [name for name in globals() if not name.startswith("_")]
