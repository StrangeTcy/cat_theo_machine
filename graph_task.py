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
        self.result = self._normalize(facts, alias_rules)
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

    def _has_fact(self, fact_list, target):
        cur = fact_list
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            f = M.Head(cur)()
            if M.Compare(f, target)() is M.truth_value:
                return M.truth_value
            cur = M.Tail(cur)()
        return M.false_value

    def _apply_aliases_to_term(self, term, alias_rules):
        cur_rules = alias_rules
        res = term
        while M.IdentityCompare(cur_rules, M.EmptyList)() is M.false_value:
            rule = M.Head(cur_rules)()
            # Attempt rewrite
            rw = M.Rewrite(rule, res, self.registry)()
            if M.IdentityCompare(rw, M.EmptyList)() is M.false_value:
                res = M.Head(rw)()
            cur_rules = M.Tail(cur_rules)()
        return res

    def _normalize(self, facts, alias_rules):
        deduped = M.EmptyList
        cur = facts
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            fact = M.Head(cur)()
            norm_fact = self._apply_aliases_to_term(fact, alias_rules)
            if self._has_fact(deduped, norm_fact) is M.false_value:
                deduped = M.Pair(norm_fact, deduped)
            cur = M.Tail(cur)()

        # Reverse to maintain original order
        rev = M.EmptyList
        cur_d = deduped
        while M.IdentityCompare(cur_d, M.EmptyList)() is M.false_value:
            rev = M.Pair(M.Head(cur_d)(), rev)
            cur_d = M.Tail(cur_d)()
        return rev

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

    def _match_conjunction(self, queries, facts, current_bindings):
        if M.IdentityCompare(queries, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, current_bindings)

        q_head = M.Head(queries)()
        q_tail = M.Tail(queries)()

        # Try to match q_head against each fact in facts
        cur_f = facts
        while M.IdentityCompare(cur_f, M.EmptyList)() is M.false_value:
            fact = M.Head(cur_f)()
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
                        q_tail, facts, next_bindings
                    )
                    if (
                        M.IdentityCompare(
                            M.Head(sub_res)(), M.truth_value
                        )()
                        is M.truth_value
                    ):
                        return sub_res

            cur_f = M.Tail(cur_f)()

        return M.Pair(M.false_value, M.EmptyList)

    def __call__(self):
        return self.result


class ForwardDeriveFacts(M.Edge):
    """
    Applies forward rules up to a fixed depth to derive new facts from existing facts.
    """

    def __init__(self, facts, rules, depth, registry):
        self.registry = registry
        self.result = self._derive(facts, rules, depth)
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

    def _has_fact(self, facts, target):
        cur = facts
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            f = M.Head(cur)()
            if M.Compare(f, target)() is M.truth_value:
                return M.truth_value
            cur = M.Tail(cur)()
        return M.false_value

    def _apply_one_rule(self, rule, facts):
        premise = P.RulePattern(rule)()
        replacement = P.RuleReplacement(rule)()

        new_facts = M.EmptyList
        cur = facts
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            f = M.Head(cur)()
            match_res = M.Match(premise, f)()
            if (
                M.IdentityCompare(M.Head(match_res)(), M.truth_value)()
                is M.truth_value
            ):
                bindings = M.Tail(match_res)()
                inst_res = M.Instantiate(replacement, bindings)()
                derived = M.Head(inst_res)()
                if self._has_fact(facts, derived) is M.false_value:
                    new_facts = M.Pair(derived, new_facts)
            cur = M.Tail(cur)()
        return new_facts

    def _derive(self, facts, rules, depth):
        cur_facts = facts
        cur_d = depth

        while M.IdentityCompare(cur_d, M.Zero)() is M.false_value:
            r_cur = rules
            any_new = M.false_value
            while M.IdentityCompare(r_cur, M.EmptyList)() is M.false_value:
                r = M.Head(r_cur)()
                derived = self._apply_one_rule(r, cur_facts)
                d_cur = derived
                while M.IdentityCompare(d_cur, M.EmptyList)() is M.false_value:
                    dfact = M.Head(d_cur)()
                    if (
                        self._has_fact(cur_facts, dfact)
                        is M.false_value
                    ):
                        cur_facts = M.Pair(dfact, cur_facts)
                        any_new = M.truth_value
                    d_cur = M.Tail(d_cur)()
                r_cur = M.Tail(r_cur)()

            if any_new is M.false_value:
                break
            # decrement depth
            pred_res = M.Pred(cur_d, self.registry)()
            cur_d = M.Head(pred_res)()

        return cur_facts

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

        # Normalize facts
        norm_facts = NormalizeGraphFacts(facts, rules, self.registry)()

        # Forward derive facts (depth 3)
        depth_3 = M.Succ(
            M.Head(M.Succ(M.Head(M.Succ(M.Zero, self.registry)())() , self.registry)())()
            , self.registry
        )()
        depth_val = M.Head(depth_3)()
        extended_facts = ForwardDeriveFacts(
            norm_facts, rules, depth_val, self.registry
        )()

        # Check if query is a list of patterns or single pattern
        is_pair_query = M.IsPair(query)()
        if is_pair_query is M.truth_value:
            # Check if query is wrapped in TaskQueryLabel or is raw pattern list
            q_head = M.Head(query)()
            if (
                M.IdentityCompare(q_head, L.TaskQueryLabel)()
                is M.truth_value
            ):
                query_list = M.Tail(query)()
            else:
                # Could be a single relation (e.g. Pair(Tag, Args)) or a list of queries
                # If first element is a relation term, treat as [query]
                query_list = M.Pair(query, M.EmptyList)
        else:
            query_list = M.Pair(query, M.EmptyList)

        # Match query conjunction
        match_res = MatchQueryConjunction(
            query_list, extended_facts, M.EmptyList, self.registry
        )()
        is_matched = M.Head(match_res)()

        if is_matched is M.truth_value:
            bindings = M.Tail(match_res)()
            # Check if expected is Negative / false_value
            if (
                M.IdentityCompare(expected, M.false_value)()
                is M.truth_value
                or M.IdentityCompare(expected, L.Rung6NegativeLabel)()
                is M.truth_value
            ):
                # Expected failure, but succeeded -> Failure!
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
            # Query did not match
            if (
                M.IdentityCompare(expected, M.false_value)()
                is M.truth_value
                or M.IdentityCompare(expected, L.Rung6NegativeLabel)()
                is M.truth_value
            ):
                # Expected failure, and failed -> Success!
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


def sync_from_namespace(namespace):
    for name in (
        "EmptyList",
        "truth_value",
        "false_value",
        "Zero",
        "Succ",
        "Pred",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [
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
]
