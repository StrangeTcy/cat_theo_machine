# ============================================================
# Gate H — Declarative Surface-Language Bridge
# Reversible correspondence mappings between surface token streams
# and canonical graph invariants, paraphrase normalization, and
# proof summary rendering without bypassing graph-native solving.
# ============================================================
from . import graph_task as GT
from . import labels as L
from . import machine as M
from . import proof as P


class SurfaceToken(M.Edge):
    """
    Machine-native surface language token.
    inputs: [token_atom]
    results: Pair(SurfaceTokenLabel, Pair(token_atom, EmptyList))
    """

    def __init__(self, token_atom):
        self.token_atom = token_atom
        self.result = M.Pair(
            L.SurfaceTokenLabel,
            M.Pair(token_atom, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(token_atom, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceStatement(M.Edge):
    """
    Machine-native surface language statement (Pair chain of tokens).
    inputs: [tokens]
    results: Pair(SurfaceStatementLabel, Pair(tokens, EmptyList))
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.result = M.Pair(
            L.SurfaceStatementLabel,
            M.Pair(tokens, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(tokens, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceCorrespondence(M.Edge):
    """
    Bidirectional correspondence rule relating a surface token pattern to a graph template.
    inputs: [rule_id, surface_tokens_pattern, graph_template, render_template]
    results: Pair(SurfaceCorrespondenceLabel, Pair(rule_id, ...))
    """

    def __init__(
        self,
        rule_id,
        surface_tokens_pattern,
        graph_template,
        render_template,
    ):
        self.rule_id = rule_id
        self.surface_tokens_pattern = surface_tokens_pattern
        self.graph_template = graph_template
        self.render_template = render_template
        self.result = M.Pair(
            L.SurfaceCorrespondenceLabel,
            M.Pair(
                rule_id,
                M.Pair(
                    surface_tokens_pattern,
                    M.Pair(
                        graph_template,
                        M.Pair(render_template, M.EmptyList),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                rule_id,
                M.Pair(
                    surface_tokens_pattern,
                    M.Pair(
                        graph_template,
                        M.Pair(render_template, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MatchSurfaceTokenStream(M.Edge):
    """
    Recursively matches a surface statement against a token pattern template,
    extracting unified variable bindings.
    """

    def __init__(self, pattern_stream, token_stream, bindings, registry):
        self.registry = registry
        self.result = self._match_stream_rec(
            pattern_stream, token_stream, bindings
        )
        super().__init__(
            inputs=M.Pair(
                pattern_stream,
                M.Pair(
                    token_stream,
                    M.Pair(
                        bindings,
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _match_stream_rec(self, pat, tokens, cur_bindings):
        pat_is_empty = M.IdentityCompare(pat, M.EmptyList)()
        tokens_is_empty = M.IdentityCompare(tokens, M.EmptyList)()

        if pat_is_empty is M.truth_value:
            if tokens_is_empty is M.truth_value:
                return M.Pair(M.truth_value, cur_bindings)
            return M.Pair(M.false_value, M.EmptyList)

        if tokens_is_empty is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)

        pat_head = M.Head(pat)()
        token_head = M.Head(tokens)()

        match_res = M.Match(pat_head, token_head)()
        is_matched = M.Head(match_res)()

        if is_matched is M.truth_value:
            bound = M.Tail(match_res)()
            merged_res = M.MergeBindings(cur_bindings, bound)()
            if (
                M.IdentityCompare(M.Head(merged_res)(), M.truth_value)()
                is M.truth_value
            ):
                next_bindings = M.Tail(merged_res)()
                return self._match_stream_rec(
                    M.Tail(pat)(), M.Tail(tokens)(), next_bindings
                )

        return M.Pair(M.false_value, M.EmptyList)

    def __call__(self):
        return self.result


class ParseSurfaceToGraphTask(M.Edge):
    """
    Parses a surface statement into a canonical GraphTaskRecord using grammar rules.
    Detects ambiguities and unsupported phrasing.
    """

    def __init__(self, surface_statement, grammar_rules, registry):
        self.registry = registry
        self.result = self._parse(surface_statement, grammar_rules)
        super().__init__(
            inputs=M.Pair(
                surface_statement,
                M.Pair(
                    grammar_rules,
                    M.Pair(registry, M.EmptyList),
                ),
            ),
            results=self.result,
        )

    def _find_matches_rec(self, tokens, cur_rules):
        if M.IdentityCompare(cur_rules, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        rule = M.Head(cur_rules)()
        rule_body = M.Tail(rule)()
        pat_stream = M.Head(M.Tail(rule_body)())()
        graph_tmpl = M.Head(M.Tail(M.Tail(rule_body)())())()

        match_res = MatchSurfaceTokenStream(
            pat_stream, tokens, M.EmptyList, self.registry
        )()
        is_matched = M.Head(match_res)()
        rest_matches = self._find_matches_rec(tokens, M.Tail(cur_rules)())

        if is_matched is M.truth_value:
            bindings = M.Tail(match_res)()
            inst_res = M.Instantiate(graph_tmpl, bindings)()
            task_record = M.Head(inst_res)()
            return M.Pair(task_record, rest_matches)

        return rest_matches

    def _parse(self, statement, rules):
        # Extract token sequence
        is_statement = (
            M.IdentityCompare(
                M.Head(statement)(), L.SurfaceStatementLabel
            )()
        )
        if is_statement is M.truth_value:
            tokens = M.Head(M.Tail(statement)())()
        else:
            tokens = statement

        matches = self._find_matches_rec(tokens, rules)

        if M.IdentityCompare(matches, M.EmptyList)() is M.truth_value:
            return M.Pair(L.SurfaceParseFailureLabel, M.EmptyList)

        first_match = M.Head(matches)()
        has_multiple = M.IdentityCompare(M.Tail(matches)(), M.EmptyList)()

        if has_multiple is M.false_value:
            # Ambiguity detected: multiple parse trees
            return M.Pair(
                L.SurfaceAmbiguityLabel,
                matches,
            )

        return M.Pair(
            L.SurfaceParseSuccessLabel,
            M.Pair(first_match, M.EmptyList),
        )

    def __call__(self):
        return self.result


class CheckParaphraseEquivalence(M.Edge):
    """
    Evaluates whether two distinct surface statements map to identical
    underlying graph invariants and produce identical graph query results.
    """

    def __init__(
        self, statement_1, statement_2, grammar_rules, registry
    ):
        self.registry = registry
        self.result = self._check(statement_1, statement_2, grammar_rules)
        super().__init__(
            inputs=M.Pair(
                statement_1,
                M.Pair(
                    statement_2,
                    M.Pair(
                        grammar_rules,
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _check(self, s1, s2, rules):
        p1_res = ParseSurfaceToGraphTask(s1, rules, self.registry)()
        p2_res = ParseSurfaceToGraphTask(s2, rules, self.registry)()

        if (
            M.IdentityCompare(
                M.Head(p1_res)(), L.SurfaceParseSuccessLabel
            )()
            is M.false_value
        ):
            return M.false_value

        if (
            M.IdentityCompare(
                M.Head(p2_res)(), L.SurfaceParseSuccessLabel
            )()
            is M.false_value
        ):
            return M.false_value

        task1 = M.Head(M.Tail(p1_res)())()
        task2 = M.Head(M.Tail(p2_res)())()

        # Compare graph facts and query structures
        facts1 = GT.TaskRecordFacts(task1)()
        facts2 = GT.TaskRecordFacts(task2)()
        query1 = GT.TaskRecordQuery(task1)()
        query2 = GT.TaskRecordQuery(task2)()

        norm1 = GT.NormalizeGraphFacts(facts1, M.EmptyList, self.registry)()
        norm2 = GT.NormalizeGraphFacts(facts2, M.EmptyList, self.registry)()

        facts_equal = M.Compare(norm1, norm2)()
        query_equal = M.Compare(query1, query2)()

        if (
            M.IdentityCompare(facts_equal, M.truth_value)()
            is M.truth_value
            and M.IdentityCompare(query_equal, M.truth_value)()
            is M.truth_value
        ):
            # Execute both in graph space and verify identical bindings
            exec1 = GT.ExecuteGraphQuery(task1, self.registry)()
            exec2 = GT.ExecuteGraphQuery(task2, self.registry)()

            tag1 = M.Head(exec1)()
            tag2 = M.Head(exec2)()

            if (
                M.IdentityCompare(tag1, L.TaskSuccessLabel)()
                is M.truth_value
                and M.IdentityCompare(tag2, L.TaskSuccessLabel)()
                is M.truth_value
            ):
                bind1 = M.Tail(exec1)()
                bind2 = M.Tail(exec2)()
                return M.Compare(bind1, bind2)()

        return M.false_value

    def __call__(self):
        return self.result


class RenderGraphResultToSurface(M.Edge):
    """
    Renders graph query bindings back to a surface language statement.
    """

    def __init__(self, query_result, render_template, registry):
        self.registry = registry
        self.result = self._render(query_result, render_template)
        super().__init__(
            inputs=M.Pair(
                query_result,
                M.Pair(
                    render_template,
                    M.Pair(registry, M.EmptyList),
                ),
            ),
            results=self.result,
        )

    def _render(self, result, template):
        tag = M.Head(result)()
        if M.IdentityCompare(tag, L.TaskSuccessLabel)() is M.false_value:
            return M.Pair(L.SurfaceParseFailureLabel, M.EmptyList)

        bindings = M.Head(M.Tail(M.Tail(result)())())()
        inst_res = M.Instantiate(template, bindings)()
        rendered_tokens = M.Head(inst_res)()

        return M.Pair(
            L.SurfaceRenderSuccessLabel,
            M.Pair(rendered_tokens, M.EmptyList),
        )

    def __call__(self):
        return self.result


class RenderDerivationSummary(M.Edge):
    """
    Renders a derivation chain into a chronological surface summary statement.
    """

    def __init__(self, derivation, rule_render_table, registry):
        self.registry = registry
        self.result = self._render_summary(derivation, rule_render_table)
        super().__init__(
            inputs=M.Pair(
                derivation,
                M.Pair(
                    rule_render_table,
                    M.Pair(registry, M.EmptyList),
                ),
            ),
            results=self.result,
        )

    def _render_steps_rec(self, cur_steps, render_table):
        if M.IdentityCompare(cur_steps, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        step = M.Head(cur_steps)()
        action = P.StepAction(step, self.registry)()
        rule = P.ActionRule(action)()
        current = P.StepCurrent(step, self.registry)()
        next_term = P.StepNext(step, self.registry)()

        step_statement = M.Pair(
            current, M.Pair(rule, M.Pair(next_term, M.EmptyList))
        )
        rest = self._render_steps_rec(M.Tail(cur_steps)(), render_table)

        return M.Pair(step_statement, rest)

    def _render_summary(self, derivation, render_table):
        steps = P.DerivationSteps(derivation, self.registry)()
        rendered_chain = self._render_steps_rec(steps, render_table)

        return M.Pair(
            L.SurfaceRenderSuccessLabel,
            M.Pair(rendered_chain, M.EmptyList),
        )

    def __call__(self):
        return self.result


__all__ = (
    "SurfaceToken",
    "SurfaceStatement",
    "SurfaceCorrespondence",
    "MatchSurfaceTokenStream",
    "ParseSurfaceToGraphTask",
    "CheckParaphraseEquivalence",
    "RenderGraphResultToSurface",
    "RenderDerivationSummary",
)
