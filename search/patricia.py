from __future__ import annotations

import copyreg
import multiprocessing
import queue
import sys
import threading
import time

from .. import machine as M
from .. import heuristics as Hmod
from .. import labels as Lmod
from .. import proof as Pmod
from .. import context as Ctxmod
from .. import schemata as Smod
from .. import gmprep as Gmpmod
from .. import trees as Tmod
from .. import logic as Logicmod
from ..heuristics import *
from ..labels import *
from ..proof import *
from ..proof import _debug, _debug_term
class SearchTreeDelta(M.Edge):
    def __init__(self, final_tree, base_tree, registry):
        self.registry = registry
        self._delta_prefers_patricia = M.OrAtom(
            SearchPatriciaIsTree(final_tree)(),
            SearchPatriciaIsTree(base_tree)(),
        )()
        self.result = self._delta_tree(final_tree, base_tree)
        super().__init__(
            inputs=M.Pair(final_tree, M.Pair(base_tree, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _is_search_patricia_tree(self, tree):
        return SearchPatriciaIsTree(tree)()

    def _terms_equal(self, left, right):
        if M.TermEqual(left, right)() is M.truth_value:
            return M.truth_value
        return M.CompareIn(left, right, self.registry)()

    def _append(self, left, right):
        reversed_left = M.EmptyList
        current = left
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            reversed_left = M.Pair(M.Head(current)(), reversed_left)
            current = M.Tail(current)()
        result = right
        current = reversed_left
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            result = M.Pair(M.Head(current)(), result)
            current = M.Tail(current)()
        return result

    def _legacy_entries(self, tree):
        return Tmod.TreeEntries(tree)()

    def _collect_entries(self, tree):
        if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if self._is_search_patricia_tree(tree) is M.truth_value:
            return SearchPatriciaEntries(tree)()
        return self._legacy_entries(tree)

    def _lookup_fact(self, tree, key):
        if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if self._is_search_patricia_tree(tree) is M.truth_value:
            return SearchPatriciaLookupByKey(tree, key, self.registry)()
        return Tmod.TreeLookup(tree, key, self.registry)()

    def _empty_like(self, final_tree, base_tree):
        if self._delta_prefers_patricia is M.truth_value:
            return M.EmptyList
        return M.Tree(M.EmptyList)

    def _insert_like(self, delta_tree, key, fact):
        if self._delta_prefers_patricia is M.truth_value:
            return SearchPatriciaInsertByKey(delta_tree, key, fact, self.registry)()
        if M.IdentityCompare(delta_tree, M.EmptyList)() is M.truth_value:
            delta_tree = M.Tree(M.EmptyList)
        return M.TreeInsert(delta_tree, key, fact, self.registry)()

    def _delta_entries(self, entries, base_tree, delta_tree):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return delta_tree
        entry = M.Head(entries)()
        key = M.Head(entry)()
        fact = M.Head(M.Tail(entry)())()
        base_fact = self._lookup_fact(base_tree, key)
        if M.IdentityCompare(base_fact, M.EmptyList)() is M.truth_value:
            delta_tree = self._insert_like(delta_tree, key, fact)
        elif self._terms_equal(fact, base_fact) is M.false_value:
            delta_tree = self._insert_like(delta_tree, key, fact)
        return self._delta_entries(M.Tail(entries)(), base_tree, delta_tree)

    def _delta_tree(self, final_tree, base_tree):
        delta_tree = self._empty_like(final_tree, base_tree)
        return self._delta_entries(self._collect_entries(final_tree), base_tree, delta_tree)

    def __call__(self):
        return self.result



class SearchStructuralKey(M.Edge):
    def __init__(self, term, registry):
        self.result = Tmod.ExactKey(term, registry)()
        super().__init__(inputs=M.Pair(term, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchPatriciaToken(M.Edge):
    def __init__(self, payload):
        self.result = M.Pair(SearchPatriciaTokenLabel, M.Pair(payload, M.EmptyList))
        super().__init__(inputs=M.Pair(payload, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchPatriciaLeaf(M.Edge):
    def __init__(self, suffix, exact_key, key, fact):
        self.result = M.Pair(
            SearchPatriciaLeafLabel,
            M.Pair(suffix, M.Pair(exact_key, M.Pair(key, M.Pair(fact, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(suffix, M.Pair(exact_key, M.Pair(key, M.Pair(fact, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchPatriciaBranch(M.Edge):
    def __init__(self, prefix, choices):
        self.result = M.Pair(SearchPatriciaBranchLabel, M.Pair(prefix, M.Pair(choices, M.EmptyList)))
        super().__init__(inputs=M.Pair(prefix, M.Pair(choices, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchPatriciaChoice(M.Edge):
    def __init__(self, token, subtree):
        self.result = M.Pair(SearchPatriciaChoiceLabel, M.Pair(token, M.Pair(subtree, M.EmptyList)))
        super().__init__(inputs=M.Pair(token, M.Pair(subtree, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchPatriciaIsTree(M.Edge):
    def __init__(self, tree):
        if M.IsPair(tree)() is M.false_value:
            self.result = M.false_value
        else:
            label = M.Head(tree)()
            self.result = Logicmod.OrAtom(
                M.IdentityCompare(label, SearchPatriciaLeafLabel)(),
                M.IdentityCompare(label, SearchPatriciaBranchLabel)(),
            )()
        super().__init__(inputs=M.Pair(tree, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchPatriciaPath(M.Edge):
    def __init__(self, structural_key):
        self.result = self._tokens(structural_key)
        super().__init__(inputs=M.Pair(structural_key, M.EmptyList), results=self.result)

    def _append(self, left, right):
        reversed_left = M.EmptyList
        current = left
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            reversed_left = M.Pair(M.Head(current)(), reversed_left)
            current = M.Tail(current)()
        result = right
        current = reversed_left
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            result = M.Pair(M.Head(current)(), result)
            current = M.Tail(current)()
        return result

    def _single(self, payload):
        return M.Pair(SearchPatriciaToken(payload)(), M.EmptyList)

    def _tokens(self, term):
        if M.IsPair(term)() is M.truth_value:
            return self._append(
                self._single(SearchPatriciaPairTokenLabel),
                self._append(
                    self._tokens(M.Head(term)()),
                    self._append(
                        self._tokens(M.Tail(term)()),
                        self._single(SearchPatriciaStopTokenLabel),
                    ),
                ),
            )
        return self._single(term)

    def __call__(self):
        return self.result


class SearchPatriciaLookup(M.Edge):
    def __init__(self, tree, path, exact_key):
        self.result = self._lookup(tree, path, exact_key)
        super().__init__(inputs=M.Pair(tree, M.Pair(path, M.Pair(exact_key, M.EmptyList))), results=self.result)

    def _is_leaf(self, tree):
        if M.IsPair(tree)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(tree)(), SearchPatriciaLeafLabel)()

    def _is_branch(self, tree):
        if M.IsPair(tree)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(tree)(), SearchPatriciaBranchLabel)()

    def _leaf_suffix(self, leaf):
        return M.Head(M.Tail(leaf)())()

    def _leaf_key(self, leaf):
        return M.Head(M.Tail(M.Tail(M.Tail(leaf)())())())()

    def _leaf_exact_key(self, leaf):
        return M.Head(M.Tail(M.Tail(leaf)())())()

    def _leaf_fact(self, leaf):
        return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(leaf)())())())())()

    def _branch_prefix(self, branch):
        return M.Head(M.Tail(branch)())()

    def _branch_choices(self, branch):
        return M.Head(M.Tail(M.Tail(branch)())())()

    def _choice_token(self, choice):
        return M.Head(M.Tail(choice)())()

    def _choice_subtree(self, choice):
        return M.Head(M.Tail(M.Tail(choice)())())()

    def _strip_prefix(self, path, prefix):
        if M.IdentityCompare(prefix, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(path, M.EmptyList))
        if M.IdentityCompare(path, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(M.EmptyList, M.EmptyList))
        if M.TermEqual(M.Head(path)(), M.Head(prefix)())() is M.false_value:
            return M.Pair(M.false_value, M.Pair(M.EmptyList, M.EmptyList))
        return self._strip_prefix(M.Tail(path)(), M.Tail(prefix)())

    def _find_choice(self, choices, token):
        if M.IdentityCompare(choices, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        choice = M.Head(choices)()
        if M.TermEqual(self._choice_token(choice), token)() is M.truth_value:
            return self._choice_subtree(choice)
        return self._find_choice(M.Tail(choices)(), token)

    def _lookup(self, tree, path, exact_key):
        if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if self._is_leaf(tree) is M.truth_value:
            if M.TermEqual(self._leaf_suffix(tree), path)() is M.false_value:
                return M.EmptyList
            if M.TermEqual(self._leaf_exact_key(tree), exact_key)() is M.false_value:
                return M.EmptyList
            return self._leaf_fact(tree)
        if self._is_branch(tree) is M.false_value:
            return M.EmptyList
        stripped = self._strip_prefix(path, self._branch_prefix(tree))
        if M.Head(stripped)() is M.false_value:
            return M.EmptyList
        remainder = M.Head(M.Tail(stripped)())()
        if M.IdentityCompare(remainder, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        token = M.Head(remainder)()
        child = self._find_choice(self._branch_choices(tree), token)
        if M.IdentityCompare(child, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return self._lookup(child, M.Tail(remainder)(), exact_key)

    def __call__(self):
        return self.result


class SearchPatriciaInsert(M.Edge):
    def __init__(self, tree, path, exact_key, key, fact):
        self.result = self._insert(tree, path, exact_key, key, fact)
        super().__init__(
            inputs=M.Pair(tree, M.Pair(path, M.Pair(exact_key, M.Pair(key, M.Pair(fact, M.EmptyList))))),
            results=self.result,
        )

    def _is_leaf(self, tree):
        if M.IsPair(tree)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(tree)(), SearchPatriciaLeafLabel)()

    def _is_branch(self, tree):
        if M.IsPair(tree)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(tree)(), SearchPatriciaBranchLabel)()

    def _leaf_suffix(self, leaf):
        return M.Head(M.Tail(leaf)())()

    def _leaf_key(self, leaf):
        return M.Head(M.Tail(M.Tail(M.Tail(leaf)())())())()

    def _leaf_exact_key(self, leaf):
        return M.Head(M.Tail(M.Tail(leaf)())())()

    def _leaf_fact(self, leaf):
        return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(leaf)())())())())()

    def _branch_prefix(self, branch):
        return M.Head(M.Tail(branch)())()

    def _branch_choices(self, branch):
        return M.Head(M.Tail(M.Tail(branch)())())()

    def _choice_token(self, choice):
        return M.Head(M.Tail(choice)())()

    def _choice_subtree(self, choice):
        return M.Head(M.Tail(M.Tail(choice)())())()

    def _longest_common_prefix(self, left, right):
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(left, M.Pair(right, M.EmptyList)))
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(left, M.Pair(right, M.EmptyList)))
        if M.TermEqual(M.Head(left)(), M.Head(right)())() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(left, M.Pair(right, M.EmptyList)))
        rest = self._longest_common_prefix(M.Tail(left)(), M.Tail(right)())
        return M.Pair(
            M.Pair(M.Head(left)(), M.Head(rest)()),
            M.Pair(M.Head(M.Tail(rest)())(), M.Pair(M.Head(M.Tail(M.Tail(rest)())())(), M.EmptyList)),
        )

    def _find_choice(self, choices, token):
        if M.IdentityCompare(choices, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        choice = M.Head(choices)()
        if M.TermEqual(self._choice_token(choice), token)() is M.truth_value:
            return self._choice_subtree(choice)
        return self._find_choice(M.Tail(choices)(), token)

    def _upsert_choice(self, choices, token, subtree):
        if M.IdentityCompare(choices, M.EmptyList)() is M.truth_value:
            return M.Pair(SearchPatriciaChoice(token, subtree)(), M.EmptyList)
        choice = M.Head(choices)()
        rest = M.Tail(choices)()
        if M.TermEqual(self._choice_token(choice), token)() is M.truth_value:
            return M.Pair(SearchPatriciaChoice(token, subtree)(), rest)
        return M.Pair(choice, self._upsert_choice(rest, token, subtree))

    def _insert_into_leaf(self, tree, path, exact_key, key, fact):
        leaf_suffix = self._leaf_suffix(tree)
        if M.TermEqual(leaf_suffix, path)() is M.truth_value:
            return SearchPatriciaLeaf(path, exact_key, key, fact)()
        split = self._longest_common_prefix(path, leaf_suffix)
        common = M.Head(split)()
        path_rest = M.Head(M.Tail(split)())()
        leaf_rest = M.Head(M.Tail(M.Tail(split)())())()
        leaf_token = M.Head(leaf_rest)()
        leaf_child = SearchPatriciaLeaf(
            M.Tail(leaf_rest)(),
            self._leaf_exact_key(tree),
            self._leaf_key(tree),
            self._leaf_fact(tree),
        )()
        new_token = M.Head(path_rest)()
        new_child = SearchPatriciaLeaf(M.Tail(path_rest)(), exact_key, key, fact)()
        return SearchPatriciaBranch(
            common,
            M.Pair(
                SearchPatriciaChoice(leaf_token, leaf_child)(),
                M.Pair(SearchPatriciaChoice(new_token, new_child)(), M.EmptyList),
            ),
        )()

    def _insert_into_branch(self, tree, path, exact_key, key, fact):
        prefix = self._branch_prefix(tree)
        split = self._longest_common_prefix(path, prefix)
        common = M.Head(split)()
        path_rest = M.Head(M.Tail(split)())()
        prefix_rest = M.Head(M.Tail(M.Tail(split)())())()
        if M.IdentityCompare(prefix_rest, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(path_rest, M.EmptyList)() is M.truth_value:
                return tree
            token = M.Head(path_rest)()
            suffix = M.Tail(path_rest)()
            choices = self._branch_choices(tree)
            child = self._find_choice(choices, token)
            if M.IdentityCompare(child, M.EmptyList)() is M.truth_value:
                next_child = SearchPatriciaLeaf(suffix, exact_key, key, fact)()
            else:
                next_child = self._insert(child, suffix, exact_key, key, fact)
            return SearchPatriciaBranch(prefix, self._upsert_choice(choices, token, next_child))()
        old_token = M.Head(prefix_rest)()
        old_child = SearchPatriciaBranch(M.Tail(prefix_rest)(), self._branch_choices(tree))()
        new_token = M.Head(path_rest)()
        new_child = SearchPatriciaLeaf(M.Tail(path_rest)(), exact_key, key, fact)()
        return SearchPatriciaBranch(
            common,
            M.Pair(
                SearchPatriciaChoice(old_token, old_child)(),
                M.Pair(SearchPatriciaChoice(new_token, new_child)(), M.EmptyList),
            ),
        )()

    def _insert(self, tree, path, exact_key, key, fact):
        if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
            return SearchPatriciaLeaf(path, exact_key, key, fact)()
        if self._is_leaf(tree) is M.truth_value:
            return self._insert_into_leaf(tree, path, exact_key, key, fact)
        if self._is_branch(tree) is M.truth_value:
            return self._insert_into_branch(tree, path, exact_key, key, fact)
        return SearchPatriciaLeaf(path, exact_key, key, fact)()

    def __call__(self):
        return self.result


class SearchPatriciaEntries(M.Edge):
    def __init__(self, tree):
        self.result = self._entries(tree)
        super().__init__(inputs=M.Pair(tree, M.EmptyList), results=self.result)

    def _is_leaf(self, tree):
        if M.IsPair(tree)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(tree)(), SearchPatriciaLeafLabel)()

    def _is_branch(self, tree):
        if M.IsPair(tree)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(tree)(), SearchPatriciaBranchLabel)()

    def _leaf_key(self, leaf):
        return M.Head(M.Tail(M.Tail(M.Tail(leaf)())())())()

    def _leaf_fact(self, leaf):
        return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(leaf)())())())())()

    def _branch_choices(self, branch):
        return M.Head(M.Tail(M.Tail(branch)())())()

    def _choice_subtree(self, choice):
        return M.Head(M.Tail(M.Tail(choice)())())()

    def _append(self, left, right):
        reversed_left = M.EmptyList
        current = left
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            reversed_left = M.Pair(M.Head(current)(), reversed_left)
            current = M.Tail(current)()
        result = right
        current = reversed_left
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            result = M.Pair(M.Head(current)(), result)
            current = M.Tail(current)()
        return result

    def _choice_entries(self, choices):
        if M.IdentityCompare(choices, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        choice = M.Head(choices)()
        return self._append(self._entries(self._choice_subtree(choice)), self._choice_entries(M.Tail(choices)()))

    def _entries(self, tree):
        if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if self._is_leaf(tree) is M.truth_value:
            entry = M.Pair(self._leaf_key(tree), M.Pair(self._leaf_fact(tree), M.EmptyList))
            return M.Pair(entry, M.EmptyList)
        if self._is_branch(tree) is M.truth_value:
            return self._choice_entries(self._branch_choices(tree))
        return M.EmptyList

    def __call__(self):
        return self.result


class SearchPatriciaLookupByKey(M.Edge):
    def __init__(self, tree, key, registry):
        self.registry = registry
        self.result = self._lookup(tree, key)
        super().__init__(inputs=M.Pair(tree, M.Pair(key, M.Pair(registry, M.EmptyList))), results=self.result)

    def _lookup(self, tree, key):
        exact_key = Tmod.ExactKey(key, self.registry)()
        if SearchPatriciaIsTree(tree)() is M.truth_value:
            path = SearchPatriciaPath(exact_key)()
            return SearchPatriciaLookup(tree, path, exact_key)()
        return Tmod.TreeLookup(tree, key, self.registry)()

    def __call__(self):
        return self.result


class SearchPatriciaInsertByKey(M.Edge):
    def __init__(self, tree, key, fact, registry):
        self.registry = registry
        self.result = self._insert(tree, key, fact)
        super().__init__(inputs=M.Pair(tree, M.Pair(key, M.Pair(fact, M.Pair(registry, M.EmptyList)))), results=self.result)

    def _legacy_entries(self, tree):
        if SearchPatriciaIsTree(tree)() is M.truth_value:
            return SearchPatriciaEntries(tree)()
        return Tmod.TreeEntries(tree)()

    def _insert_entries(self, entries, tree):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return tree
        entry = M.Head(entries)()
        next_tree = Tmod.TreeInsert(tree, M.Head(entry)(), M.Head(M.Tail(entry)())(), self.registry)()
        return self._insert_entries(M.Tail(entries)(), next_tree)

    def _insert(self, tree, key, fact):
        if SearchPatriciaIsTree(tree)() is M.truth_value:
            base_tree = self._insert_entries(self._legacy_entries(tree), M.Tree(M.EmptyList))
            return Tmod.TreeInsert(base_tree, key, fact, self.registry)()
        return Tmod.TreeInsert(tree, key, fact, self.registry)()

    def __call__(self):
        return self.result



def sync_from_namespace(namespace):
    for name in (
        "DFSLabel",
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
        "RewriteDFSLabel",
        "GoalHeadOrderLabel",
        "KnowledgeLabel",
        "ContextSearchComparisonJobsLabel",
        "ContextSearchJobsLabel",
        "SearchSignatureLabel",
        "SearchComparisonLabel",
        "SearchComparisonJobLabel",
        "SearchCostLabel",
        "SearchJobLabel",
        "SearchStateLabel",
        "SearchTheoremCursorLabel",
        "SearchRewriteCursorLabel",
        "SearchRewritePathFrameLabel",
        "SearchRewriteRuleBundleLabel",
        "SearchPairKeyLabel",
        "SearchCtorKeyLabel",
        "SearchPatriciaTokenLabel",
        "SearchPatriciaPairTokenLabel",
        "SearchPatriciaStopTokenLabel",
        "SearchPatriciaLeafLabel",
        "SearchPatriciaBranchLabel",
        "SearchPatriciaChoiceLabel",
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchRunningLabel",
        "SearchPausedLabel",
        "SearchTimedOutLabel",
        "SearchAbortedByUserLabel",
        "SearchRootFastPathPhaseLabel",
        "SearchPacketSearchPhaseLabel",
        "SearchNoRootFastPathLabel",
        "SearchRootCacheResultLabel",
        "SearchRootSchemaResultLabel",
        "SearchRootGoalResultLabel",
        "SearchRootImmediateResultLabel"
    ):
        if name in namespace:
            globals()[name] = namespace[name]
