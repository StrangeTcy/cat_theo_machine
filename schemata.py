from __future__ import annotations

from . import machine as M


class DerivationSchemaStart(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(entry)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DerivationSchemaGoal(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DerivationSchemaPlan(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LookupDerivationSchema(M.Edge):
    def __init__(self, start, goal, tree):
        self.result = self._lookup(M.TreeEntries(tree)(), start, goal)
        super().__init__(inputs=M.Pair(start, M.Pair(goal, M.Pair(tree, M.EmptyList))), results=self.result)

    def _lookup(self, entries, start, goal):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        item = M.Head(entries)()
        entry = M.Head(M.Tail(item)())()
        start_pattern = DerivationSchemaStart(entry)()
        goal_pattern = DerivationSchemaGoal(entry)()
        plan = DerivationSchemaPlan(entry)()
        start_match = M.Match(start_pattern, start)()
        start_flag = M.Head(start_match)()
        start_bindings = M.Tail(start_match)()
        if M.IdentityCompare(start_flag, M.truth_value)() is M.truth_value:
            goal_match = M.Match(goal_pattern, goal)()
            goal_flag = M.Head(goal_match)()
            goal_bindings = M.Tail(goal_match)()
            if M.IdentityCompare(goal_flag, M.truth_value)() is M.truth_value:
                merged = M.MergeBindings(start_bindings, goal_bindings)()
                merged_flag = M.Head(merged)()
                merged_bindings = M.Tail(merged)()
                if M.IdentityCompare(merged_flag, M.truth_value)() is M.truth_value:
                    return M.Pair(plan, M.Pair(merged_bindings, M.EmptyList))
        return self._lookup(M.Tail(entries)(), start, goal)

    def __call__(self):
        return self.result


class StoreDerivationSchema(M.Edge):
    def __init__(self, start_pattern, goal_pattern, plan, tree, registry):
        entry = M.Pair(start_pattern, M.Pair(goal_pattern, M.Pair(plan, M.EmptyList)))
        key = M.Atom()
        new_tree = M.TreeInsert(tree, key, entry, registry)()
        self.result = M.Pair(new_tree, M.EmptyList)
        super().__init__(
            inputs=M.Pair(
                start_pattern,
                M.Pair(goal_pattern, M.Pair(plan, M.Pair(tree, M.Pair(registry, M.EmptyList)))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
