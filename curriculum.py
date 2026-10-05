# ============================================================
# Gate F — Graph Curriculum & Robustness Verification Suite
# 7 curriculum rungs (Retrieval, Join, Constraint, Derivation,
# Alias Normalization, Negative/Failure, Planner Decomposition)
# and noise robustness variants (duplicates, distractors, order permutation).
# ============================================================
from . import graph_task as GT
from . import labels as L
from . import machine as M
from . import proof as P


class BuildRung1RetrievalTask(M.Edge):
    """
    Rung 1: Single-edge structural retrieval.
    Fact: E(src, dst)
    Query: E(src, ?x) -> binds ?x = dst
    """

    def __init__(self, task_id, edge_tag, src_node, dst_node, var_x, registry):
        self.registry = registry
        var_pat = M.Pair(M.VarTag, M.Pair(var_x, M.EmptyList))
        fact = M.Pair(edge_tag, M.Pair(src_node, M.Pair(dst_node, M.EmptyList)))
        query = M.Pair(edge_tag, M.Pair(src_node, M.Pair(var_pat, M.EmptyList)))

        facts = M.Pair(fact, M.EmptyList)
        expected_binding = dst_node

        self.result = GT.GraphTaskRecord(
            task_id,
            L.Rung1RetrievalLabel,
            facts,
            query,
            expected_binding,
            M.EmptyList,
            M.EmptyList,
        )()
        super().__init__(
            inputs=M.Pair(
                task_id,
                M.Pair(
                    edge_tag,
                    M.Pair(
                        src_node,
                        M.Pair(
                            dst_node,
                            M.Pair(var_x, M.Pair(registry, M.EmptyList)),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BuildRung2JoinTask(M.Edge):
    """
    Rung 2: Two-edge relational join.
    Facts: [E(a, b), E(b, c)]
    Query: [E(a, ?x), E(?x, ?y)] -> binds ?x = b, ?y = c
    """

    def __init__(
        self,
        task_id,
        edge_tag,
        node_a,
        node_b,
        node_c,
        var_x,
        var_y,
        registry,
    ):
        self.registry = registry
        var_pat_x = M.Pair(M.VarTag, M.Pair(var_x, M.EmptyList))
        var_pat_y = M.Pair(M.VarTag, M.Pair(var_y, M.EmptyList))

        fact_1 = M.Pair(
            edge_tag, M.Pair(node_a, M.Pair(node_b, M.EmptyList))
        )
        fact_2 = M.Pair(
            edge_tag, M.Pair(node_b, M.Pair(node_c, M.EmptyList))
        )
        facts = M.Pair(fact_1, M.Pair(fact_2, M.EmptyList))

        q1 = M.Pair(
            edge_tag, M.Pair(node_a, M.Pair(var_pat_x, M.EmptyList))
        )
        q2 = M.Pair(
            edge_tag, M.Pair(var_pat_x, M.Pair(var_pat_y, M.EmptyList))
        )
        query_conjunction = M.Pair(
            L.TaskQueryLabel, M.Pair(q1, M.Pair(q2, M.EmptyList))
        )

        self.result = GT.GraphTaskRecord(
            task_id,
            L.Rung2JoinLabel,
            facts,
            query_conjunction,
            node_c,
            M.EmptyList,
            M.EmptyList,
        )()
        super().__init__(
            inputs=M.Pair(
                task_id,
                M.Pair(
                    edge_tag,
                    M.Pair(
                        node_a,
                        M.Pair(
                            node_b,
                            M.Pair(
                                node_c,
                                M.Pair(
                                    var_x,
                                    M.Pair(
                                        var_y,
                                        M.Pair(registry, M.EmptyList),
                                    ),
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


class BuildRung3ConstraintTask(M.Edge):
    """
    Rung 3: Variable binding & repeated-variable constraint satisfaction.
    Facts: [R(a, b), R(a, a)]
    Query: R(?x, ?x) -> must unify to R(a, a), binding ?x = a
    """

    def __init__(
        self, task_id, rel_tag, node_a, node_b, var_x, registry
    ):
        self.registry = registry
        var_pat_x = M.Pair(M.VarTag, M.Pair(var_x, M.EmptyList))

        fact_1 = M.Pair(
            rel_tag, M.Pair(node_a, M.Pair(node_b, M.EmptyList))
        )
        fact_2 = M.Pair(
            rel_tag, M.Pair(node_a, M.Pair(node_a, M.EmptyList))
        )
        facts = M.Pair(fact_1, M.Pair(fact_2, M.EmptyList))

        query = M.Pair(
            rel_tag, M.Pair(var_pat_x, M.Pair(var_pat_x, M.EmptyList))
        )

        self.result = GT.GraphTaskRecord(
            task_id,
            L.Rung3ConstraintLabel,
            facts,
            query,
            node_a,
            M.EmptyList,
            M.EmptyList,
        )()
        super().__init__(
            inputs=M.Pair(
                task_id,
                M.Pair(
                    rel_tag,
                    M.Pair(
                        node_a,
                        M.Pair(
                            node_b,
                            M.Pair(var_x, M.Pair(registry, M.EmptyList)),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BuildRung4DerivationTask(M.Edge):
    """
    Rung 4: Two-hop rule derivation.
    Fact: A
    Rules: [A -> B, B -> C]
    Query: C -> derived via forward expansion
    """

    def __init__(
        self,
        task_id,
        fact_a,
        fact_b,
        fact_c,
        registry,
    ):
        self.registry = registry
        rule_1 = P.Rule(fact_a, fact_b)()
        rule_2 = P.Rule(fact_b, fact_c)()
        rules = M.Pair(rule_1, M.Pair(rule_2, M.EmptyList))
        facts = M.Pair(fact_a, M.EmptyList)

        self.result = GT.GraphTaskRecord(
            task_id,
            L.Rung4DerivationLabel,
            facts,
            fact_c,
            fact_c,
            rules,
            M.EmptyList,
        )()
        super().__init__(
            inputs=M.Pair(
                task_id,
                M.Pair(
                    fact_a,
                    M.Pair(
                        fact_b,
                        M.Pair(
                            fact_c,
                            M.Pair(registry, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BuildRung5AliasTask(M.Edge):
    """
    Rung 5: Identity and alias normalization.
    Facts: [E(alias_node, target)]
    Alias Rules: [alias_node -> canonical_node]
    Query: E(canonical_node, ?x) -> binds ?x = target after alias normalization
    """

    def __init__(
        self,
        task_id,
        edge_tag,
        alias_node,
        canonical_node,
        target_node,
        var_x,
        registry,
    ):
        self.registry = registry
        var_pat_x = M.Pair(M.VarTag, M.Pair(var_x, M.EmptyList))

        fact_raw = M.Pair(
            edge_tag, M.Pair(alias_node, M.Pair(target_node, M.EmptyList))
        )
        facts = M.Pair(fact_raw, M.EmptyList)

        alias_rule = P.Rule(alias_node, canonical_node)()
        rules = M.Pair(alias_rule, M.EmptyList)

        query = M.Pair(
            edge_tag,
            M.Pair(canonical_node, M.Pair(var_pat_x, M.EmptyList)),
        )

        self.result = GT.GraphTaskRecord(
            task_id,
            L.Rung5AliasLabel,
            facts,
            query,
            target_node,
            rules,
            M.EmptyList,
        )()
        super().__init__(
            inputs=M.Pair(
                task_id,
                M.Pair(
                    edge_tag,
                    M.Pair(
                        alias_node,
                        M.Pair(
                            canonical_node,
                            M.Pair(
                                target_node,
                                M.Pair(
                                    var_x,
                                    M.Pair(registry, M.EmptyList),
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


class BuildRung6NegativeTask(M.Edge):
    """
    Rung 6: Explicit negative / failure detection.
    Fact: E(a, b)
    Query: E(a, c) (absent target) -> explicitly fails with Rung6NegativeLabel
    """

    def __init__(
        self,
        task_id,
        edge_tag,
        node_a,
        node_b,
        node_c,
        registry,
    ):
        self.registry = registry
        fact = M.Pair(
            edge_tag, M.Pair(node_a, M.Pair(node_b, M.EmptyList))
        )
        facts = M.Pair(fact, M.EmptyList)

        query = M.Pair(
            edge_tag, M.Pair(node_a, M.Pair(node_c, M.EmptyList))
        )

        self.result = GT.GraphTaskRecord(
            task_id,
            L.Rung6NegativeLabel,
            facts,
            query,
            L.Rung6NegativeLabel,
            M.EmptyList,
            M.EmptyList,
        )()
        super().__init__(
            inputs=M.Pair(
                task_id,
                M.Pair(
                    edge_tag,
                    M.Pair(
                        node_a,
                        M.Pair(
                            node_b,
                            M.Pair(
                                node_c,
                                M.Pair(registry, M.EmptyList),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BuildRung7PlannerTask(M.Edge):
    """
    Rung 7: Multi-stage planner decomposition across dependent queries.
    Facts: [E(a, b), E(b, c), F(c, goal)]
    Query: [E(a, ?x), E(?x, ?y), F(?y, ?z)] -> binds ?z = goal
    """

    def __init__(
        self,
        task_id,
        edge_e,
        edge_f,
        node_a,
        node_b,
        node_c,
        goal_node,
        var_x,
        var_y,
        var_z,
        registry,
    ):
        self.registry = registry
        var_pat_x = M.Pair(M.VarTag, M.Pair(var_x, M.EmptyList))
        var_pat_y = M.Pair(M.VarTag, M.Pair(var_y, M.EmptyList))
        var_pat_z = M.Pair(M.VarTag, M.Pair(var_z, M.EmptyList))

        f1 = M.Pair(edge_e, M.Pair(node_a, M.Pair(node_b, M.EmptyList)))
        f2 = M.Pair(edge_e, M.Pair(node_b, M.Pair(node_c, M.EmptyList)))
        f3 = M.Pair(edge_f, M.Pair(node_c, M.Pair(goal_node, M.EmptyList)))
        facts = M.Pair(f1, M.Pair(f2, M.Pair(f3, M.EmptyList)))

        q1 = M.Pair(
            edge_e, M.Pair(node_a, M.Pair(var_pat_x, M.EmptyList))
        )
        q2 = M.Pair(
            edge_e, M.Pair(var_pat_x, M.Pair(var_pat_y, M.EmptyList))
        )
        q3 = M.Pair(
            edge_f, M.Pair(var_pat_y, M.Pair(var_pat_z, M.EmptyList))
        )
        query = M.Pair(
            L.TaskQueryLabel,
            M.Pair(q1, M.Pair(q2, M.Pair(q3, M.EmptyList))),
        )

        self.result = GT.GraphTaskRecord(
            task_id,
            L.Rung7PlannerLabel,
            facts,
            query,
            goal_node,
            M.EmptyList,
            M.EmptyList,
        )()
        super().__init__(
            inputs=M.Pair(
                task_id,
                M.Pair(
                    edge_e,
                    M.Pair(
                        edge_f,
                        M.Pair(
                            node_a,
                            M.Pair(
                                node_b,
                                M.Pair(
                                    node_c,
                                    M.Pair(
                                        goal_node,
                                        M.Pair(
                                            var_x,
                                            M.Pair(
                                                var_y,
                                                M.Pair(
                                                    var_z,
                                                    M.Pair(
                                                        registry,
                                                        M.EmptyList,
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
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


class MutateWithNoise(M.Edge):
    """
    Applies controlled noise mutations to a task's graph facts:
    - Injects duplicates
    - Injects irrelevant distractors
    - Permutes edge order
    """

    def __init__(self, task_record, distractor_facts, registry):
        self.registry = registry
        self.result = self._mutate(task_record, distractor_facts)
        super().__init__(
            inputs=M.Pair(
                task_record,
                M.Pair(
                    distractor_facts,
                    M.Pair(registry, M.EmptyList),
                ),
            ),
            results=self.result,
        )

    def _mutate(self, task, distractors):
        task_id = GT.TaskRecordId(task)()
        rung = GT.TaskRecordRung(task)()
        facts = GT.TaskRecordFacts(task)()
        query = GT.TaskRecordQuery(task)()
        expected = GT.TaskRecordExpected(task)()
        rules = GT.TaskRecordRules(task)()
        prov = GT.TaskRecordProvenance(task)()

        # Add duplicate of head fact
        head_fact = M.Head(facts)()
        with_dup = M.Pair(head_fact, facts)

        # Prepend distractors
        noisy_facts = with_dup
        cur_d = distractors
        while M.IdentityCompare(cur_d, M.EmptyList)() is M.false_value:
            d = M.Head(cur_d)()
            noisy_facts = M.Pair(d, noisy_facts)
            cur_d = M.Tail(cur_d)()

        # Return mutated task record
        return GT.GraphTaskRecord(
            task_id,
            rung,
            noisy_facts,
            query,
            expected,
            rules,
            prov,
        )()

    def __call__(self):
        return self.result


class EvaluateCurriculumSuite(M.Edge):
    """
    Executes and grades a suite of graph curriculum tasks.
    Returns: Pair(CurriculumSuiteResultLabel, Pair(passed_tasks, Pair(failed_tasks, EmptyList)))
    """

    def __init__(self, task_list, registry):
        self.registry = registry
        self.result = self._evaluate(task_list)
        super().__init__(
            inputs=M.Pair(
                task_list,
                M.Pair(registry, M.EmptyList),
            ),
            results=self.result,
        )

    def _evaluate(self, tasks):
        passed_acc = M.EmptyList
        failed_acc = M.EmptyList

        cur = tasks
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            task = M.Head(cur)()
            exec_res = GT.ExecuteGraphQuery(task, self.registry)()
            verdict = M.Head(exec_res)()

            if (
                M.IdentityCompare(verdict, L.TaskSuccessLabel)()
                is M.truth_value
            ):
                passed_acc = M.Pair(task, passed_acc)
            else:
                failed_acc = M.Pair(task, failed_acc)

            cur = M.Tail(cur)()

        return M.Pair(
            L.CurriculumSuiteResultLabel,
            M.Pair(
                passed_acc,
                M.Pair(failed_acc, M.EmptyList),
            ),
        )

    def __call__(self):
        return self.result


def sync_from_namespace(namespace):
    for name in (
        "EmptyList",
        "truth_value",
        "false_value",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [
    "BuildRung1RetrievalTask",
    "BuildRung2JoinTask",
    "BuildRung3ConstraintTask",
    "BuildRung4DerivationTask",
    "BuildRung5AliasTask",
    "BuildRung6NegativeTask",
    "BuildRung7PlannerTask",
    "MutateWithNoise",
    "EvaluateCurriculumSuite",
]
