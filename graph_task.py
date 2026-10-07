# ============================================================
# Gate E — Canonical Graph Tasks & Machine-Native Ingestion
# Canonical task records, graph fact normalization, multi-goal
# structural joins, and explicit variable binding query execution.
# ============================================================
from . import labels as L
from . import machine as M
from . import proof as P


class GraphTaskRecord(M.Edge):
    """
    Canonical machine-native graph task representation.
    inputs: [task_id, rung_label, graph_facts, query_pattern, expected_bindings, permitted_rules, provenance]
    results: Pair(GraphTaskRecordLabel, Pair(task_id, ...))
    """

    def __init__(
        self,
        task_id,
        rung_label,
        graph_facts,
        query_pattern,
        expected_bindings,
        permitted_rules,
        provenance,
    ):
        self.task_id = task_id
        self.rung_label = rung_label
        self.graph_facts = graph_facts
        self.query_pattern = query_pattern
        self.expected_bindings = expected_bindings
        self.permitted_rules = permitted_rules
        self.provenance = provenance
        self.result = M.Pair(
            L.GraphTaskRecordLabel,
            M.Pair(
                task_id,
                M.Pair(
                    rung_label,
                    M.Pair(
                        graph_facts,
                        M.Pair(
                            query_pattern,
                            M.Pair(
                                expected_bindings,
                                M.Pair(
                                    permitted_rules,
                                    M.Pair(provenance, M.EmptyList),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                task_id,
                M.Pair(
                    rung_label,
                    M.Pair(
                        graph_facts,
                        M.Pair(
                            query_pattern,
                            M.Pair(
                                expected_bindings,
                                M.Pair(
                                    permitted_rules,
                                    M.Pair(provenance, M.EmptyList),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TaskRecordId(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(record)())()
        super().__init__(
            inputs=M.Pair(record, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class TaskRecordRung(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(record)())())()
        super().__init__(
            inputs=M.Pair(record, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class TaskRecordFacts(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(record)())())())()
        super().__init__(
            inputs=M.Pair(record, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class TaskRecordQuery(M.Edge):
    def __init__(self, record):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(record)())())())()
        )()
        super().__init__(
            inputs=M.Pair(record, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class TaskRecordExpected(M.Edge):
    def __init__(self, record):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
        )()
        super().__init__(
            inputs=M.Pair(record, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class TaskRecordRules(M.Edge):
    def __init__(self, record):
        self.result = M.Head(
            M.Tail(
                M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
            )()
        )()
        super().__init__(
            inputs=M.Pair(record, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class TaskRecordProvenance(M.Edge):
    def __init__(self, record):
        self.result = M.Head(
            M.Tail(
                M.Tail(
                    M.Tail(
                        M.Tail(M.Tail(M.Tail(M.Tail(record)())())())()
                    )()
                )()
            )()
        )()
        super().__init__(
            inputs=M.Pair(record, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class NormalizeGraphFacts(M.Edge):
    """
    Normalizes a graph fact list:
    1. Removes duplicate facts (exact structural equality).
    2. Applies alias/equality rewrites if present.
    """

    def __init__(self, facts, alias_rules, registry):
        self.registry = registry
        self.result = self._normalize_rec(facts, alias_rules, M.EmptyList)
        super().__init__(
            inputs=M.Pair(
                facts,
                M.Pair(
                    alias_rules,
                    M.Pair(registry, M.EmptyList),
                ),
            ),
            results=self.result,
        )

    def _has_fact_rec(self, cur, target):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.false_value
        f = M.Head(cur)()
        if M.Compare(f, target)() is M.truth_value:
            return M.truth_value
        return self._has_fact_rec(M.Tail(cur)(), target)

    def _apply_aliases_rec(self, term, cur_rules):
        if M.IdentityCompare(cur_rules, M.EmptyList)() is M.truth_value:
            return term
        rule = M.Head(cur_rules)()
        rw = M.Rewrite(rule, term, self.registry)()
        if M.IdentityCompare(rw, M.EmptyList)() is M.false_value:
            next_term = M.Head(rw)()
        else:
            next_term = term
        return self._apply_aliases_rec(next_term, M.Tail(cur_rules)())

    def _normalize_rec(self, cur, alias_rules, deduped_acc):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return deduped_acc

        fact = M.Head(cur)()
        norm_fact = self._apply_aliases_rec(fact, alias_rules)

        if self._has_fact_rec(deduped_acc, norm_fact) is M.truth_value:
            return self._normalize_rec(M.Tail(cur)(), alias_rules, deduped_acc)

        next_acc = M.Pair(norm_fact, deduped_acc)
        return self._normalize_rec(M.Tail(cur)(), alias_rules, next_acc)

    def __call__(self):
        return self.result


class MatchQueryConjunction(M.Edge):
    """
    Matches a conjunction of query patterns [Q1, Q2, ..., Qk] against a fact list,
    finding consistent unified variable bindings across all query goals.
    """

    def __init__(self, query_patterns, facts, initial_bindings, registry):
        self.registry = registry
        self.result = self._match_conjunction(
            query_patterns, facts, initial_bindings
        )
        super().__init__(
            inputs=M.Pair(
                query_patterns,
                M.Pair(
                    facts,
                    M.Pair(
                        initial_bindings,
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _match_first_fact_rec(
        self, queries, q_head, q_tail, cur_facts, all_facts, current_bindings
    ):
        if M.IdentityCompare(cur_facts, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)

        fact = M.Head(cur_facts)()
        match_res = M.Match(q_head, fact)()
        is_match = M.Head(match_res)()

        if is_match is M.truth_value:
            fact_bindings = M.Tail(match_res)()
            merged_res = M.MergeBindings(
                current_bindings, fact_bindings
            )()
            is_merged = M.Head(merged_res)()

            if is_merged is M.truth_value:
                next_bindings = M.Tail(merged_res)()
                sub_res = self._match_conjunction(
                    q_tail, all_facts, next_bindings
                )
                if (
                    M.IdentityCompare(
                        M.Head(sub_res)(), M.truth_value
                    )()
                    is M.truth_value
                ):
                    return sub_res

        return self._match_first_fact_rec(
            queries, q_head, q_tail, M.Tail(cur_facts)(), all_facts, current_bindings
        )

    def _match_conjunction(self, queries, facts, current_bindings):
        if M.IdentityCompare(queries, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, current_bindings)

        q_head = M.Head(queries)()
        q_tail = M.Tail(queries)()

        return self._match_first_fact_rec(
            queries, q_head, q_tail, facts, facts, current_bindings
        )

    def __call__(self):
        return self.result


class ForwardDeriveFacts(M.Edge):
    """
    Applies forward rules up to a fixed depth to derive new facts from existing facts.
    """

    def __init__(self, facts, rules, depth, registry):
        self.registry = registry
        self.result = self._derive_rec(facts, rules, depth)
        super().__init__(
            inputs=M.Pair(
                facts,
                M.Pair(
                    rules,
                    M.Pair(
                        depth,
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _has_fact_rec(self, cur, target):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.false_value
        f = M.Head(cur)()
        if M.Compare(f, target)() is M.truth_value:
            return M.truth_value
        return self._has_fact_rec(M.Tail(cur)(), target)

    def _apply_rule_to_facts_rec(self, premise, replacement, cur_facts, existing_facts):
        if M.IdentityCompare(cur_facts, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        f = M.Head(cur_facts)()
        match_res = M.Match(premise, f)()
        rest = self._apply_rule_to_facts_rec(
            premise, replacement, M.Tail(cur_facts)(), existing_facts
        )

        if (
            M.IdentityCompare(M.Head(match_res)(), M.truth_value)()
            is M.truth_value
        ):
            bindings = M.Tail(match_res)()
            inst_res = M.Instantiate(replacement, bindings)()
            derived = M.Head(inst_res)()
            if self._has_fact_rec(existing_facts, derived) is M.false_value:
                return M.Pair(derived, rest)

        return rest

    def _apply_all_rules_rec(self, cur_rules, current_facts):
        if M.IdentityCompare(cur_rules, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        r = M.Head(cur_rules)()
        premise = P.RulePattern(r)()
        replacement = P.RuleReplacement(r)()
        new_from_r = self._apply_rule_to_facts_rec(
            premise, replacement, current_facts, current_facts
        )
        rest_new = self._apply_all_rules_rec(M.Tail(cur_rules)(), current_facts)

        return self._merge_facts_rec(new_from_r, rest_new, current_facts)

    def _merge_facts_rec(self, l1, l2, existing):
        if M.IdentityCompare(l1, M.EmptyList)() is M.truth_value:
            return l2
        h = M.Head(l1)()
        t = M.Tail(l1)()
        if self._has_fact_rec(existing, h) is M.false_value:
            return M.Pair(h, self._merge_facts_rec(t, l2, existing))
        return self._merge_facts_rec(t, l2, existing)

    def _derive_rec(self, facts, rules, cur_depth):
        if M.IdentityCompare(cur_depth, M.Zero)() is M.truth_value:
            return facts

        new_facts = self._apply_all_rules_rec(rules, facts)
        if M.IdentityCompare(new_facts, M.EmptyList)() is M.truth_value:
            return facts

        combined_facts = self._merge_facts_rec(new_facts, facts, M.EmptyList)
        pred_res = M.Pred(cur_depth, self.registry)()
        next_depth = M.Head(pred_res)()

        return self._derive_rec(combined_facts, rules, next_depth)

    def __call__(self):
        return self.result


class ExecuteGraphQuery(M.Edge):
    """
    Executes a query against a canonical GraphTaskRecord:
    1. Normalizes graph facts and applies alias rewrites.
    2. Forward-derives facts using permitted rules.
    3. Solves query conjunction and extracts unified bindings.
    4. Evaluates result against expected bindings.
    """

    def __init__(self, task_record, registry):
        self.registry = registry
        self.result = self._execute(task_record)
        super().__init__(
            inputs=M.Pair(
                task_record,
                M.Pair(registry, M.EmptyList),
            ),
            results=self.result,
        )

    def _execute(self, task):
        task_id = TaskRecordId(task)()
        facts = TaskRecordFacts(task)()
        query = TaskRecordQuery(task)()
        expected = TaskRecordExpected(task)()
        rules = TaskRecordRules(task)()

        norm_facts = NormalizeGraphFacts(facts, rules, self.registry)()

        r1 = M.Succ(M.Zero, self.registry)()
        c1 = M.Head(r1)()
        reg1 = M.Head(M.Tail(r1)())()

        r2 = M.Succ(c1, reg1)()
        c2 = M.Head(r2)()
        reg2 = M.Head(M.Tail(r2)())()

        r3 = M.Succ(c2, reg2)()
        c3 = M.Head(r3)()
        reg3 = M.Head(M.Tail(r3)())()

        extended_facts = ForwardDeriveFacts(
            norm_facts, rules, c3, reg3
        )()

        is_pair_query = M.IsPair(query)()
        if is_pair_query is M.truth_value:
            q_head = M.Head(query)()
            if (
                M.IdentityCompare(q_head, L.TaskQueryLabel)()
                is M.truth_value
            ):
                query_list = M.Tail(query)()
            else:
                query_list = M.Pair(query, M.EmptyList)
        else:
            query_list = M.Pair(query, M.EmptyList)

        match_res = MatchQueryConjunction(
            query_list, extended_facts, M.EmptyList, self.registry
        )()
        is_matched = M.Head(match_res)()

        if is_matched is M.truth_value:
            bindings = M.Tail(match_res)()
            if (
                M.IdentityCompare(expected, M.false_value)()
                is M.truth_value
                or M.IdentityCompare(expected, L.Rung6NegativeLabel)()
                is M.truth_value
            ):
                return M.Pair(
                    L.TaskFailureLabel,
                    M.Pair(
                        task_id,
                        M.Pair(
                            L.Rung6NegativeLabel,
                            M.Pair(bindings, M.EmptyList),
                        ),
                    ),
                )
            return M.Pair(
                L.TaskSuccessLabel,
                M.Pair(
                    task_id,
                    M.Pair(bindings, M.EmptyList),
                ),
            )
        else:
            if (
                M.IdentityCompare(expected, M.false_value)()
                is M.truth_value
                or M.IdentityCompare(expected, L.Rung6NegativeLabel)()
                is M.truth_value
            ):
                return M.Pair(
                    L.TaskSuccessLabel,
                    M.Pair(
                        task_id,
                        M.Pair(
                            L.Rung6NegativeLabel,
                            M.EmptyList,
                        ),
                    ),
                )
            return M.Pair(
                L.TaskFailureLabel,
                M.Pair(
                    task_id,
                    M.Pair(
                        L.TaskFailureLabel,
                        M.EmptyList,
                    ),
                ),
            )

    def __call__(self):
        return self.result


__all__ = (
    "GraphTaskRecord",
    "TaskRecordId",
    "TaskRecordRung",
    "TaskRecordFacts",
    "TaskRecordQuery",
    "TaskRecordExpected",
    "TaskRecordRules",
    "TaskRecordProvenance",
    "NormalizeGraphFacts",
    "MatchQueryConjunction",
    "ForwardDeriveFacts",
    "ExecuteGraphQuery",
)
