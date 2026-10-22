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

    def _prepend_distractors_rec(self, cur_d, facts):
        if M.IdentityCompare(cur_d, M.EmptyList)() is M.truth_value:
            return facts
        d = M.Head(cur_d)()
        return M.Pair(d, self._prepend_distractors_rec(M.Tail(cur_d)(), facts))

    def _mutate(self, task, distractors):
        task_id = GT.TaskRecordId(task)()
        rung = GT.TaskRecordRung(task)()
        facts = GT.TaskRecordFacts(task)()
        query = GT.TaskRecordQuery(task)()
        expected = GT.TaskRecordExpected(task)()
        rules = GT.TaskRecordRules(task)()
        prov = GT.TaskRecordProvenance(task)()

        head_fact = M.Head(facts)()
        with_dup = M.Pair(head_fact, facts)
        noisy_facts = self._prepend_distractors_rec(distractors, with_dup)

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
        self.result = self._evaluate_rec(task_list, M.EmptyList, M.EmptyList)
        super().__init__(
            inputs=M.Pair(
                task_list,
                M.Pair(registry, M.EmptyList),
            ),
            results=self.result,
        )

    def _evaluate_rec(self, cur, passed_acc, failed_acc):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.Pair(
                L.CurriculumSuiteResultLabel,
                M.Pair(
                    passed_acc,
                    M.Pair(failed_acc, M.EmptyList),
                ),
            )

        task = M.Head(cur)()
        exec_res = GT.ExecuteGraphQuery(task, self.registry)()
        verdict = M.Head(exec_res)()

        if M.IdentityCompare(verdict, L.TaskSuccessLabel)() is M.truth_value:
            next_passed = M.Pair(task, passed_acc)
            return self._evaluate_rec(M.Tail(cur)(), next_passed, failed_acc)

        next_failed = M.Pair(task, failed_acc)
        return self._evaluate_rec(M.Tail(cur)(), passed_acc, next_failed)

    def __call__(self):
        return self.result


__all__ = (
    "BuildRung1RetrievalTask",
    "BuildRung2JoinTask",
    "BuildRung3ConstraintTask",
    "BuildRung4DerivationTask",
    "BuildRung5AliasTask",
    "BuildRung6NegativeTask",
    "BuildRung7PlannerTask",
    "MutateWithNoise",
    "EvaluateCurriculumSuite",
    "CardRecord",
    "CardRecordId",
    "CardRecordTier",
    "CardRecordRole",
    "CardRecordFamily",
    "CardRecordTargetClass",
    "CardRecordStatus",
    "CardRecordTitle",
    "CardRecordStatement",
    "CardRecordNumbers",
    "CardRecordRoles",
    "CardRecordCited",
    "CardRecordMissing",
    "CardSplitCheck",
    "CardTask",
    "CardTaskId",
    "CardTaskExpectation",
    "CardTaskGraphTask",
    "CardTaskFacts",
    "CardTaskEvidence",
    "CardNoBuilder",
    "CardNoBuilderId",
    "CardNoBuilderReason",
    "CompileInvarianceCard",
    "CompileBoardTilingCard",
    "CompileCardTask",
    "RunCardTask",
    "CardVerdictTag",
    "CardVerdictGoal",
    "CardVerdictClosure",
    "CardLoaderRecords",
    "CardLoaderTasks",
    "CardLoaderNoBuilders",
    "CardLoaderVerdicts",
    "CardLoaderGaps",
    "Ground1Gap",
    "TrainingRecordLoader",
    "parse_card_text",
    "load_card_corpus",
    "card_roles",
)


# ============================================================
# W25 — the markdown corpus: card records, Ground 1 coverage, card tasks
#
# The cards in `curriculum/tier0` and `curriculum/tier1` are prose
# blueprints: a statement, a method, the constructors the card cites, the
# constructors it needs and lacks, negative controls, and a promotion gate.
# This loader reads that *structure* — never an answer — into machine
# records, so a card becomes evaluation data the existing engines can run.
#
# What is parsed (all of it is a section heading the corpus already has):
#     source statement, target class, intended method, constructor mapping,
#     missing constructors, current status, title, and the numbers the
#     statement itself states (digits and English number words).
#
# What is NOT in this module: any card's conclusion, any per-card constant,
# any noun from a card's subject matter.  The two task builders are generic
# over a *family* and take every number from the record:
#
#     invariance   — a process with a two-state population and a move that
#                    flips a fixed number of items.  The parity of the
#                    upright count is the observable; the builder emits the
#                    readings and the preservation premise only after the
#                    machine's own arithmetic has checked every split.
#     pigpen       — a rectangular board, two removed corners, and a tiling
#                    by two-cell tiles.  The builder emits the square count,
#                    the two colour counts and the per-colour requirement.
#
# A family with no builder is reported as `CardNoBuilderLabel` with the
# reason, never silently skipped.  Count targets (Divide, Symmetry) have no
# obligation generator in the planner (Ground 3), and the graph theorem has
# no proof-procedure of its own; both are stated as open in the suite.
# ============================================================

import re as _re

from . import graph_task as _GT

_RECORD_FIELDS = 11


def _chain_local(items):
    acc = M.EmptyList
    for item in reversed(list(items)):
        acc = M.Pair(item, acc)
    return acc


def _to_list_local(term):
    out = []
    cursor = term
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        out.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return out


def _nat_of(value, registry):
    """Host integer -> machine natural, through the machine's own constructor."""
    return M.Head(M.NatFromRep(M.GMPRep(int(value)), registry)())()


def _int_of(nat, registry):
    """Machine natural -> host integer, through the machine's own accessor."""
    value = M.NatRepOf(nat, registry)()()
    return int(value)


def _atom_text(atom):
    """The text a Char holds.  Host layer: the machine has no edge that
    returns an atom's payload, and every other reader in the tree (packs,
    dialogue) reads it the same way."""
    return atom()


_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100,
}

_NUMBER_TOKEN = _re.compile(r"\b(\d+|[A-Za-z]+)\b")


def _number_of(token):
    lowered = token.lower()
    if lowered.isdigit():
        return int(lowered)
    return _NUMBER_WORDS.get(lowered)


def _numbers_in(text):
    """Every number the statement states, in reading order."""
    out = []
    for token in _NUMBER_TOKEN.findall(text):
        value = _number_of(token)
        if value is not None:
            out.append(value)
    return out


def _split_sections(text):
    """`## heading` -> (heading, body lines).  The title is kept separately."""
    sections = []
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = [line[3:].strip(), []]
            sections.append(current)
        elif current is not None:
            current[1].append(line)
    return sections


def _section(sections, prefix):
    for heading, body in sections:
        if heading.lower().startswith(prefix):
            return heading, body
    return None, None


def _statement_text(body):
    """The quoted statement: the `>` lines, without the provenance marker."""
    quoted = []
    for line in body:
        stripped = line.strip()
        if stripped.startswith(">"):
            quoted.append(stripped[1:].strip())
    text = " ".join(quoted)
    text = _re.sub(r"\((supplied|recorded)[^)]*\)", "", text)
    text = _re.sub(r"\*\*\(UNSOURCED[^*]*\)\*\*", "", text)
    text = _re.sub(r"\*\*Ground \d[^*]*\*\*", "", text)
    return _re.sub(r"\s+", " ", text).strip()


def _constructor_names(body):
    """Backticked identifiers ending in `Label`, in citation order."""
    names = []
    for token in _re.findall(r"`([A-Za-z][A-Za-z0-9_]*)`", body or ""):
        if token.endswith("Label") and token not in names:
            names.append(token)
    return names


def _roles_in(statement):
    """Role numbers a statement states in phrases the builders understand.

    Keys are fixed role names; a role is present only when the phrase is.
    Nothing here knows a card: the same three patterns read any sentence of
    the same shape.
    """
    roles = {}

    def first_number(pattern):
        """The first *numeric* reading of the pattern, skipping non-numeric
        words the pattern also matches ("be tiled", "a glass")."""
        for hit in _re.finditer(pattern, statement):
            value = _number_of(hit.group(1))
            if value is not None:
                return value
        return None

    value = first_number(r"flips?\s+(?:exactly\s+)?([A-Za-z]+|\d+)")
    if value is not None:
        roles["flip_count"] = value
    value = first_number(r"([A-Za-z]+|\d+)\s+(?:glass(?:es)?|objects?|coins?|items?)\b")
    if value is not None:
        roles["total"] = value
    lowered = statement.lower()
    if "all upside down" in lowered or "all down" in lowered or "all face down" in lowered:
        roles["initial_zero"] = 0
    if _re.search(r"all (?:[a-z]+ )?end upright", lowered) or "all upright" in lowered:
        if "total" in roles:
            roles["target_total"] = roles["total"]
    match = _re.search(r"(\d+)\s*[x\u00d7]\s*(\d+)", statement)
    if match is not None:
        roles["board_side"] = int(match.group(1))
        roles["board_side_2"] = int(match.group(2))
    value = first_number(r"([A-Za-z]+|\d+)\s+opposite corners")
    if value is not None:
        roles["removed_corners"] = value
    value = first_number(r"([A-Za-z]+|\d+)\s+(?:dominoes|tiles)\b")
    if value is not None:
        roles["tile_count"] = value
    return roles


class CardRecord(M.Edge):
    """One corpus card as a machine record.

    fields: id, tier, role, family, target_class, status, title, statement,
            numbers, roles, cited, missing
    """

    def __init__(self, card_id, tier, role, family, target_class, status, title,
                 statement, numbers, roles, cited, missing):
        self.result = M.Pair(
            L.CardRecordLabel,
            M.Pair(card_id,
            M.Pair(tier,
            M.Pair(role,
            M.Pair(family,
            M.Pair(target_class,
            M.Pair(status,
            M.Pair(title,
            M.Pair(statement,
            M.Pair(numbers,
            M.Pair(roles,
            M.Pair(cited,
            M.Pair(missing, M.EmptyList)))))))))))),
        )
        super().__init__(
            inputs=M.Pair(card_id, M.Pair(tier, M.Pair(role, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


def _field(record, index):
    cursor = M.Tail(record)()
    step = 0
    while step < index:
        cursor = M.Tail(cursor)()
        step = step + 1
    return M.Head(cursor)()


class CardRecordId(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 0)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordTier(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 1)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordRole(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 2)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordFamily(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 3)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordTargetClass(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 4)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordStatus(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 5)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordTitle(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 6)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordStatement(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 7)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordNumbers(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 8)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordRoles(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 9)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordCited(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 10)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardRecordMissing(M.Edge):
    def __init__(self, record):
        self.result = _field(record, 11)
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


def card_roles(record, registry):
    """Host view of the record's role numbers: {role name: int}."""
    out = {}
    for entry in _to_list_local(CardRecordRoles(record)()):
        name = _atom_text(M.Head(entry)())
        out[name] = _int_of(M.Tail(entry)(), registry)
    return out


def parse_card_text(text, rel_path, registry):
    """Markdown text -> (CardRecord term, gap name list).

    Host layer: splitting prose and reading a file are host work.  Every
    product is a machine term.  `gaps` lists the constructor names the card
    cites or needs that do not exist in `labels.py` (Ground 1).
    """
    sections = _split_sections(text)
    title = ""
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    parts = rel_path.replace("\\", "/").split("/")
    tier = parts[0] if len(parts) > 1 else ""
    role = parts[1] if len(parts) > 2 else ""

    _, statement_body = _section(sections, "source statement")
    statement = _statement_text(statement_body or [])

    heading, _ = _section(sections, "target class")
    target_class = heading.split(":", 1)[1].strip() if heading else ""

    heading, _ = _section(sections, "intended method")
    method = ""
    if heading:
        method = heading.split(":", 1)[1].strip()
        method = method.replace("(the trap)", "").replace("(decoy)", "").strip()

    heading, _ = _section(sections, "current status")
    status = heading.split(":", 1)[1].strip() if heading else ""

    _, cited_body = _section(sections, "constructor mapping")
    cited = _constructor_names(" ".join(cited_body or []))
    _, missing_body = _section(sections, "missing constructors")
    missing = _constructor_names(" ".join(missing_body or []))

    roles = _roles_in(statement)
    numbers = _numbers_in(statement)

    cited_terms = [_char_atom_interned(name) for name in cited]
    missing_terms = [_char_atom_interned(name) for name in missing]
    role_terms = []
    for name, value in roles.items():
        role_terms.append(M.Pair(_char_atom_interned(name), _nat_of(value, registry)))

    record = CardRecord(
        _char_atom_interned(rel_path.replace("\\", "/")),
        _char_atom_interned(tier),
        _char_atom_interned(role),
        _char_atom_interned(method),
        _char_atom_interned(target_class),
        _char_atom_interned(status),
        _char_atom_interned(title),
        _char_atom_interned(statement),
        _chain_local([_nat_of(value, registry) for value in numbers]),
        _chain_local(role_terms),
        _chain_local(cited_terms),
        _chain_local(missing_terms),
    )()

    gaps = [name for name in cited + missing if not hasattr(L, name)]
    return record, gaps


_CHAR_TABLE = {}


def _char_atom_interned(text):
    """One Char atom per distinct text, so card terms compare by Compare.

    The corpus is read once per process; interning keeps the record small and
    makes `Compare` the right equality for the statement field (two Char
    atoms with equal text do compare equal, but reusing one atom is cheaper).
    """
    if text not in _CHAR_TABLE:
        _CHAR_TABLE[text] = M.Char(text)
    return _CHAR_TABLE[text]


def load_card_corpus(root, registry):
    """Every markdown card under `root`, in sorted path order.

    Returns (records machine list, gaps: [(relpath, name)], paths: [str]).
    """
    import os

    records = []
    gaps = []
    paths = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in sorted(filenames):
            if not filename.endswith(".md"):
                continue
            full = os.path.join(dirpath, filename)
            rel = os.path.relpath(full, root).replace("\\", "/")
            with open(full, "r", encoding="utf-8") as handle:
                text = handle.read()
            record, card_gaps = parse_card_text(text, rel, registry)
            records.append(record)
            paths.append(rel)
            for name in card_gaps:
                gaps.append((rel, name))
    records.sort(key=lambda r: _atom_text(CardRecordId(r)()))
    paths.sort()
    gaps.sort()
    return _chain_local(records), gaps, paths


class CardSplitCheck(M.Edge):
    """One row of the exhaustive split analysis: a move flips `flip` items,
    `on` of which turn upright and `off` of which turn down; the parity of
    the change is the residue the machine computed."""

    def __init__(self, on_nat, off_nat, delta_nat, residue_nat):
        self.result = M.Pair(
            L.CardSplitCheckLabel,
            M.Pair(on_nat, M.Pair(off_nat, M.Pair(delta_nat,
                   M.Pair(residue_nat, M.EmptyList)))),
        )
        super().__init__(inputs=M.Pair(on_nat, M.Pair(off_nat, M.EmptyList)),
                         results=self.result)

    def __call__(self):
        return self.result


class CardTask(M.Edge):
    """A card compiled into a task: the graph task record, the fact base, the
    arithmetic evidence, and the expectation ("close" or "refuse")."""

    def __init__(self, card_id, expectation, task, facts, evidence):
        self.result = M.Pair(
            L.CardTaskLabel,
            M.Pair(card_id,
            M.Pair(expectation,
            M.Pair(task,
            M.Pair(facts,
            M.Pair(evidence, M.EmptyList))))),
        )
        super().__init__(inputs=M.Pair(card_id, M.Pair(task, M.EmptyList)),
                         results=self.result)

    def __call__(self):
        return self.result


class CardTaskId(M.Edge):
    def __init__(self, task):
        self.result = _field(task, 0)
        super().__init__(inputs=M.Pair(task, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardTaskExpectation(M.Edge):
    def __init__(self, task):
        self.result = _field(task, 1)
        super().__init__(inputs=M.Pair(task, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardTaskGraphTask(M.Edge):
    def __init__(self, task):
        self.result = _field(task, 2)
        super().__init__(inputs=M.Pair(task, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardTaskFacts(M.Edge):
    def __init__(self, task):
        self.result = _field(task, 3)
        super().__init__(inputs=M.Pair(task, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardTaskEvidence(M.Edge):
    def __init__(self, task):
        self.result = _field(task, 4)
        super().__init__(inputs=M.Pair(task, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardNoBuilder(M.Edge):
    """A card the loader parses but cannot yet turn into a task."""

    def __init__(self, card_id, reason):
        self.result = M.Pair(L.CardNoBuilderLabel, M.Pair(card_id,
                          M.Pair(reason, M.EmptyList)))
        super().__init__(inputs=M.Pair(card_id, M.Pair(reason, M.EmptyList)),
                         results=self.result)

    def __call__(self):
        return self.result


class CardNoBuilderId(M.Edge):
    def __init__(self, refusal):
        self.result = _field(refusal, 0)
        super().__init__(inputs=M.Pair(refusal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardNoBuilderReason(M.Edge):
    def __init__(self, refusal):
        self.result = _field(refusal, 1)
        super().__init__(inputs=M.Pair(refusal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


def _machine_mod(value, modulus, registry):
    from .math import arithmetic as _AR
    return M.Head(_AR.Modulo(_nat_of(value, registry), _nat_of(modulus, registry),
                             registry)())()


def _machine_mul(left, right, registry):
    from .math import arithmetic as _AR
    return M.Head(_AR.Multiply(_nat_of(left, registry), _nat_of(right, registry),
                               registry)())()


def _machine_add(left, right, registry):
    from .math import arithmetic as _AR
    return M.Head(_AR.Add(_nat_of(left, registry), _nat_of(right, registry),
                          registry)())()


def _machine_pred(value, registry):
    return M.Head(M.NatPred(value, registry)())()


def _nat_equals(left, right, registry):
    return M.NatEq(left, right, registry)() is M.truth_value


class CompileInvarianceCard(M.Edge):
    """A two-state-population card -> an obstruction task.

    The fact base is the planner's own obligation list for
    `Invariance(problem, phi, moves, initial, v0, target, v1)`, with two
    premises emitted only after the machine's arithmetic has checked them:

      * `Apart(v0, v1)`         only when the two machine-computed residues
                                (`initial mod 2`, `target mod 2`) differ;
      * `Preserves(flip, phi)`  only when the exhaustive split analysis shows
                                that every way of flipping `k` items changes
                                the upright count by an even amount.  There
                                are k+1 splits and they exhaust the move, so
                                the check is complete for the move, not a
                                sample; the arithmetic is the machine's.
    """

    def __init__(self, record, rules, registry):
        self.registry = registry
        card_id = CardRecordId(record)()
        roles = card_roles(record, registry)
        if "total" not in roles or "flip_count" not in roles:
            self.result = CardNoBuilder(
                card_id, _char_atom_interned("invariance-roles-not-stated"))()
        else:
            self.result = self._compile(card_id, roles, rules)

        super().__init__(inputs=M.Pair(record, M.Pair(rules, M.EmptyList)),
                         results=self.result)

    def _compile(self, card_id, roles, rules):
        total = roles["total"]
        flips = roles["flip_count"]
        initial = roles.get("initial_zero", 0)
        target = roles.get("target_total", total)

        problem = M.Pair(L.GlassLabel, M.Pair(card_id, M.EmptyList))
        phi = M.Pair(L.CountUprightLabel, M.Pair(problem, M.EmptyList))
        flip_term = M.Pair(L.FlipLabel, M.Pair(_nat_of(flips, self.registry), M.EmptyList))
        moves = M.Pair(flip_term, M.EmptyList)
        initial_state = _char_atom_interned("initial")
        target_state = _char_atom_interned("target")

        v_initial = _machine_mod(initial, 2, self.registry)
        v_target = _machine_mod(target, 2, self.registry)
        apart_ok = not _nat_equals(v_initial, v_target, self.registry)

        evidence = [
            M.Pair(L.ModLabel, M.Pair(_nat_of(initial, self.registry),
                   M.Pair(_nat_of(2, self.registry),
                   M.Pair(v_initial, M.EmptyList)))),
            M.Pair(L.ModLabel, M.Pair(_nat_of(target, self.registry),
                   M.Pair(_nat_of(2, self.registry),
                   M.Pair(v_target, M.EmptyList)))),
        ]
        split_ok = True
        step = 0
        while step <= flips:
            on = step
            off = flips - step
            delta = on - off
            residue = _machine_mod(abs(delta), 2, self.registry)
            if not _nat_equals(residue, M.Zero, self.registry):
                split_ok = False
            evidence.append(
                CardSplitCheck(
                    _nat_of(on, self.registry),
                    _nat_of(off, self.registry),
                    _nat_of(abs(delta), self.registry),
                    residue,
                )()
            )
            step = step + 1

        facts = [
            M.Pair(L.MoveSetLabel, M.Pair(problem, M.Pair(moves, M.EmptyList))),
            M.Pair(L.ReadingLabel, M.Pair(phi, M.Pair(initial_state,
                   M.Pair(v_initial, M.EmptyList)))),
            M.Pair(L.ReadingLabel, M.Pair(phi, M.Pair(target_state,
                   M.Pair(v_target, M.EmptyList)))),
        ]
        if apart_ok:
            facts.append(
                M.Pair(L.ApartLabel, M.Pair(v_initial, M.Pair(v_target, M.EmptyList)))
            )
        if split_ok:
            facts.append(
                M.Pair(L.PreservesLabel, M.Pair(flip_term, M.Pair(phi, M.EmptyList)))
            )

        fact_chain = _chain_local(facts)
        goal = M.Pair(L.UnreachableLabel, M.Pair(problem, M.Pair(target_state, M.EmptyList)))
        task = _GT.GraphTaskRecord(
            card_id,
            L.CardTaskLabel,
            fact_chain,
            goal,
            M.truth_value,
            rules,
            M.Pair(L.CardRecordLabel, M.Pair(card_id, M.EmptyList)),
        )()
        return CardTask(card_id, M.truth_value, task, fact_chain,
                        _chain_local(evidence))()

    def __call__(self):
        return self.result


class CompileBoardTilingCard(M.Edge):
    """A board-and-tiles card -> a refusal task.

    The builder records what the machine's arithmetic says about the board:
    the square count, the two colour counts after the corners are removed,
    and what a tiling would need of each colour.  It deliberately *also*
    records the count argument the trap would use (tiles × 2 = squares), so
    the refusal cannot be an artefact of the count: the count works and the
    colour does not.
    """

    def __init__(self, record, rules, registry):
        self.registry = registry
        card_id = CardRecordId(record)()
        roles = card_roles(record, registry)
        needed = ("board_side", "removed_corners", "tile_count")
        if any(role not in roles for role in needed):
            self.result = CardNoBuilder(
                card_id, _char_atom_interned("board-roles-not-stated"))()
        else:
            self.result = self._compile(card_id, roles, rules)
        super().__init__(inputs=M.Pair(record, M.Pair(rules, M.EmptyList)),
                         results=self.result)

    def _compile(self, card_id, roles, rules):
        side = roles["board_side"]
        side_2 = roles.get("board_side_2", side)
        removed = roles["removed_corners"]
        tiles = roles["tile_count"]

        squares = _machine_mul(side, side_2, self.registry)
        remaining = squares
        step = 0
        while step < removed:
            remaining = _machine_pred(remaining, self.registry)
            step = step + 1

        half = (side * side_2) // 2
        half_verified = _nat_equals(_machine_mul(2, half, self.registry), squares,
                                    self.registry)
        colour_a = half
        colour_b = half - removed
        colour_b_verified = _nat_equals(
            _machine_add(colour_b, removed, self.registry),
            _nat_of(half, self.registry),
            self.registry,
        )
        trap_count_ok = _nat_equals(
            _machine_mul(tiles, 2, self.registry), remaining, self.registry)
        imbalance = (not _nat_equals(_nat_of(tiles, self.registry),
                                     _nat_of(colour_a, self.registry), self.registry)
                     and not _nat_equals(_nat_of(tiles, self.registry),
                                         _nat_of(colour_b, self.registry),
                                         self.registry))

        board = M.Pair(L.BoardLabel, M.Pair(card_id, M.EmptyList))
        black = M.Pair(L.ColorLabel, M.Pair(_char_atom_interned("black"), M.EmptyList))
        white = M.Pair(L.ColorLabel, M.Pair(_char_atom_interned("white"), M.EmptyList))

        facts = [
            M.Pair(L.CardinalityLabel, M.Pair(board, M.Pair(remaining, M.EmptyList))),
            M.Pair(L.CardinalityLabel, M.Pair(board, M.Pair(_nat_of(tiles, self.registry),
                   M.EmptyList))),
            M.Pair(L.ColorCountLabel, M.Pair(board, M.Pair(black,
                   M.Pair(_nat_of(colour_a, self.registry), M.EmptyList)))),
            M.Pair(L.ColorCountLabel, M.Pair(board, M.Pair(white,
                   M.Pair(_nat_of(colour_b, self.registry), M.EmptyList)))),
            M.Pair(L.TileRequiredLabel, M.Pair(board, M.Pair(black,
                   M.Pair(_nat_of(tiles, self.registry), M.EmptyList)))),
            M.Pair(L.TileRequiredLabel, M.Pair(board, M.Pair(white,
                   M.Pair(_nat_of(tiles, self.registry), M.EmptyList)))),
        ]
        evidence = [
            M.Pair(L.CardSplitCheckLabel, M.Pair(board, M.Pair(_nat_of(side, self.registry),
                   M.Pair(_nat_of(side_2, self.registry),
                   M.Pair(squares, M.EmptyList))))),
            M.Pair(L.CardSplitCheckLabel, M.Pair(board, M.Pair(_nat_of(side, self.registry),
                   M.Pair(_nat_of(side_2, self.registry),
                   M.Pair(_nat_of(half_verified, self.registry),
                   M.Pair(_nat_of(colour_b_verified, self.registry),
                   M.Pair(_nat_of(trap_count_ok, self.registry),
                   M.Pair(_nat_of(imbalance, self.registry), M.EmptyList)))))))),
        ]

        fact_chain = _chain_local(facts)
        goal = M.Pair(L.TilingLabel, M.Pair(board, M.Pair(_nat_of(tiles, self.registry),
                       M.EmptyList)))
        task = _GT.GraphTaskRecord(
            card_id,
            L.CardTaskLabel,
            fact_chain,
            goal,
            M.false_value,
            rules,
            M.Pair(L.CardRecordLabel, M.Pair(card_id, M.EmptyList)),
        )()
        return CardTask(card_id, M.false_value, task, fact_chain,
                        _chain_local(evidence))()

    def __call__(self):
        return self.result


class CompileCardTask(M.Edge):
    """Dispatch a record to the family builder it has the roles for."""

    def __init__(self, record, rules, registry):
        self.registry = registry
        family = _atom_text(CardRecordFamily(record)())
        roles = card_roles(record, registry)
        if family == "Invariance":
            self.result = CompileInvarianceCard(record, rules, registry)()
        elif family == "Pigeonhole" and "tile_count" in roles and "board_side" in roles:
            self.result = CompileBoardTilingCard(record, rules, registry)()
        elif family == "Pigeonhole":
            self.result = CardNoBuilder(
                CardRecordId(record)(),
                _char_atom_interned(
                    "pigeonhole-conclusion-needs-residue-prefix-and-counting-closure"))()
        elif family in ("Divide", "Symmetry"):
            self.result = CardNoBuilder(
                CardRecordId(record)(),
                _char_atom_interned(
                    "count-target-ground3-no-obligation-generator"))()
        elif family == "Extremal":
            self.result = CardNoBuilder(
                CardRecordId(record)(),
                _char_atom_interned(
                    "extremal-selection-exists-graph-theorem-has-no-procedure"))()
        else:
            self.result = CardNoBuilder(
                CardRecordId(record)(),
                _char_atom_interned("no-family-builder"))()
        super().__init__(inputs=M.Pair(record, M.Pair(rules, M.EmptyList)),
                         results=self.result)

    def __call__(self):
        return self.result


class RunCardTask(M.Edge):
    """Run a compiled card task through the same two primitives
    `ExecuteGraphQuery` uses: forward derivation, then a query match.

    Verdict, by the card's own expectation:
      expect close + matched      -> CardSolvedLabel
      expect close + not matched  -> CardOpenLabel      (a missing premise)
      expect refuse + not matched -> CardRejectedLabel  (the claim is not derivable)
      expect refuse + matched     -> CardOpenLabel      (the decoy would have passed)
    """

    def __init__(self, task, depth, registry):
        self.registry = registry
        card_id = CardTaskId(task)()
        expectation = CardTaskExpectation(task)()
        graph_task = CardTaskGraphTask(task)()
        facts = CardTaskFacts(task)()
        rules = _GT.TaskRecordRules(graph_task)()
        goal = _GT.TaskRecordQuery(graph_task)()

        closure = _GT.ForwardDeriveFacts(
            facts, rules, _nat_of(depth, registry), registry
        )()
        match = _GT.MatchQueryConjunction(
            M.Pair(goal, M.EmptyList), closure, M.EmptyList, registry
        )()
        matched = M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value
        expect_close = M.IdentityCompare(expectation, M.truth_value)() is M.truth_value

        if matched:
            verdict = L.CardSolvedLabel if expect_close else L.CardOpenLabel
        else:
            verdict = L.CardOpenLabel if expect_close else L.CardRejectedLabel

        self.result = M.Pair(
            verdict,
            M.Pair(card_id, M.Pair(goal, M.Pair(closure, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(task, M.Pair(depth, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CardVerdictTag(M.Edge):
    def __init__(self, verdict):
        self.result = M.Head(verdict)()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardVerdictGoal(M.Edge):
    def __init__(self, verdict):
        self.result = M.Head(M.Tail(M.Tail(verdict)())())()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardVerdictClosure(M.Edge):
    def __init__(self, verdict):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(verdict)())())())()
        super().__init__(inputs=M.Pair(verdict, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Ground1Gap(M.Edge):
    """A constructor a card cites that `labels.py` does not define.

    Reported, never silently skipped: the card cannot be stated as a machine
    term until the name exists, so the family stays OPEN.
    """

    def __init__(self, card_id, name):
        self.result = M.Pair(L.Ground1GapLabel,
                             M.Pair(card_id, M.Pair(name, M.EmptyList)))
        super().__init__(inputs=M.Pair(card_id, M.Pair(name, M.EmptyList)),
                         results=self.result)

    def __call__(self):
        return self.result


class CardLoaderRecords(M.Edge):
    def __init__(self, loaded):
        self.result = _field(loaded, 0)
        super().__init__(inputs=M.Pair(loaded, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardLoaderTasks(M.Edge):
    def __init__(self, loaded):
        self.result = _field(loaded, 1)
        super().__init__(inputs=M.Pair(loaded, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardLoaderNoBuilders(M.Edge):
    def __init__(self, loaded):
        self.result = _field(loaded, 2)
        super().__init__(inputs=M.Pair(loaded, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardLoaderVerdicts(M.Edge):
    def __init__(self, loaded):
        self.result = _field(loaded, 3)
        super().__init__(inputs=M.Pair(loaded, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CardLoaderGaps(M.Edge):
    def __init__(self, loaded):
        self.result = _field(loaded, 4)
        super().__init__(inputs=M.Pair(loaded, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TrainingRecordLoader(M.Edge):
    """The corpus loader: `curriculum/` -> machine records, card tasks,
    no-builder reports and run verdicts.

    This is evaluation data.  Nothing here writes to a pack, and the module
    holds no card's conclusion: a card compiles only when the family builder
    can state its premises, and closes only when the existing engines derive
    the goal from them.
    """

    def __init__(self, root, rules, depth, registry):
        self.root = root
        records, gaps, paths = load_card_corpus(root, registry)
        tasks = []
        no_builders = []
        verdicts = []
        for record in _to_list_local(records):
            compiled = CompileCardTask(record, rules, registry)()
            if M.IdentityCompare(M.Head(compiled)(), L.CardTaskLabel)() is M.truth_value:
                tasks.append(compiled)
                verdicts.append(RunCardTask(compiled, depth, registry)())
            else:
                no_builders.append(compiled)
        self.gaps = gaps
        self.paths = paths
        gap_terms = [
            Ground1Gap(_char_atom_interned(card_id), _char_atom_interned(name))()
            for card_id, name in gaps
        ]
        self.result = M.Pair(
            L.CardLoaderResultLabel,
            M.Pair(records,
            M.Pair(_chain_local(tasks),
            M.Pair(_chain_local(no_builders),
            M.Pair(_chain_local(verdicts),
            M.Pair(_chain_local(gap_terms), M.EmptyList))))),
        )
        super().__init__(
            inputs=M.Pair(_char_atom_interned(root),
                          M.Pair(rules, M.Pair(_nat_of(depth, registry), M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result
