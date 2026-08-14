from __future__ import annotations

from .. import machine as M
from .. import trees as Tmod
from ..labels import *
from .model import *
from .patricia import *


class _ComparisonTreeMixin:
    def _search_mode_uses_global_visited(self, mode):
        return M.OrAtom(
            M.OrAtom(M.IdentityCompare(mode, BFSLabel)(), M.IdentityCompare(mode, BeamLabel)())(),
            M.IdentityCompare(mode, AStarLabel)(),
        )()

    def _initial_compare_job_visited(self, mode):
        if self._search_mode_uses_global_visited(mode) is M.false_value:
            return M.EmptyList
        return self._tree_insert(M.EmptyList, self.start)

    def _mode_uses_global_visited(self, mode):
        return M.OrAtom(
            M.OrAtom(M.IdentityCompare(mode, BFSLabel)(), M.IdentityCompare(mode, BeamLabel)())(),
            M.IdentityCompare(mode, AStarLabel)(),
        )()

    def _tree_contains(self, tree, key):
        if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
            return M.false_value
        found = self._tree_lookup_fact(tree, key)
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def _tree_lookup_fact(self, tree, key):
        return SearchPatriciaLookupByKey(tree, key, self.registry)()

    def _tree_insert(self, tree, key):
        return SearchPatriciaInsertByKey(tree, key, M.Pair(key, M.EmptyList), self.registry)()

    def _comparison_filter_new_child(self, child, visited):
        if M.IdentityCompare(child, M.EmptyList)() is M.truth_value:
            return child, visited
        child_current = SearchStateCurrent(child)()
        if self._tree_contains(visited, child_current) is M.truth_value:
            return M.EmptyList, visited
        next_visited = self._tree_insert(visited, child_current)
        return child, next_visited

    def _collect_map_entries(self, tree):
        if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if SearchPatriciaIsTree(tree)() is M.truth_value:
            return SearchPatriciaEntries(tree)()
        return self._collect_legacy_map_entries(tree)

    def _collect_legacy_map_entries(self, tree):
        return Tmod.TreeEntries(tree)()

    def _merge_tree_entries_legacy(self, dst_tree, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return dst_tree
        entry = M.Head(entries)()
        key = M.Head(entry)()
        fact = M.Head(M.Tail(entry)())()
        if M.IdentityCompare(dst_tree, M.EmptyList)() is M.truth_value:
            next_tree = M.TreeInsert(M.Tree(M.EmptyList), key, fact, self.registry)()
        else:
            next_tree = M.TreeInsert(dst_tree, key, fact, self.registry)()
        return self._merge_tree_entries_legacy(next_tree, M.Tail(entries)())

    def _merge_tree_entries_patricia(self, dst_tree, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return dst_tree
        entry = M.Head(entries)()
        key = M.Head(entry)()
        fact = M.Head(M.Tail(entry)())()
        next_tree = SearchPatriciaInsertByKey(dst_tree, key, fact, self.registry)()
        return self._merge_tree_entries_patricia(next_tree, M.Tail(entries)())

    def _merge_legacy_entries_to_patricia(self, dst_tree, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return dst_tree
        entry = M.Head(entries)()
        key = M.Head(entry)()
        fact = M.Head(M.Tail(entry)())()
        next_tree = SearchPatriciaInsertByKey(dst_tree, key, fact, self.registry)()
        return self._merge_legacy_entries_to_patricia(next_tree, M.Tail(entries)())

    def _merge_tree(self, left_tree, right_tree):
        if M.IdentityCompare(right_tree, M.EmptyList)() is M.truth_value:
            return left_tree
        if SearchPatriciaIsTree(right_tree)() is M.truth_value:
            base_tree = left_tree
            if M.IdentityCompare(base_tree, M.EmptyList)() is M.truth_value:
                return self._merge_tree_entries_patricia(M.EmptyList, SearchPatriciaEntries(right_tree)())
            if SearchPatriciaIsTree(base_tree)() is M.truth_value:
                return self._merge_tree_entries_patricia(base_tree, SearchPatriciaEntries(right_tree)())
            base_tree = self._merge_legacy_entries_to_patricia(M.EmptyList, self._collect_legacy_map_entries(base_tree))
            return self._merge_tree_entries_patricia(base_tree, SearchPatriciaEntries(right_tree)())
        if M.IdentityCompare(left_tree, M.EmptyList)() is M.truth_value:
            left_tree = M.Tree(M.EmptyList)
        return self._merge_tree_entries_legacy(left_tree, self._collect_legacy_map_entries(right_tree))



def sync_from_namespace(namespace):
    for name in (
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonTreeMixin")]
