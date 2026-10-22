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


class BuildStandardCorrespondences(M.Edge):
    """
    Builds the standard machine-native declarative correspondence grammar table.
    """

    def __init__(self, registry):
        self.registry = registry
        self.result = self._build_rules()
        super().__init__(
            inputs=M.Pair(registry, M.EmptyList),
            results=self.result,
        )

    def _build_token_stream(self, words):
        if not words:
            return M.EmptyList
        tok = SurfaceToken(M.Char(words[0]))()
        return M.Pair(tok, self._build_token_stream(words[1:]))

    def _build_rules(self):
        # 1. Tao Problem 1.1
        pat_tao = self._build_token_stream(["solve", "the", "tao", "triangle", "problem"])
        task_tao = GT.GraphTaskRecord(
            M.Atom(),
            L.TaoProblem11TriangleLabel,
            M.EmptyList,
            M.Pair(L.TaoProblem11AreaValueLabel, M.Atom()),
            M.Atom(),
            M.EmptyList,
            M.Atom(),
        )()
        corr_tao = SurfaceCorrespondence(
            M.Atom(), pat_tao, task_tao, pat_tao
        )()

        # 2. Engel E1
        pat_e1 = self._build_token_stream(["solve", "engel", "e1"])
        task_e1 = GT.GraphTaskRecord(
            M.Atom(),
            L.Rung4DerivationLabel,
            M.EmptyList,
            M.Pair(L.InvariantLabel, M.Atom()),
            M.Atom(),
            M.EmptyList,
            M.Atom(),
        )()
        corr_e1 = SurfaceCorrespondence(
            M.Atom(), pat_e1, task_e1, pat_e1
        )()

        # 3. Engel E2
        pat_e2 = self._build_token_stream(["solve", "engel", "e2"])
        task_e2 = GT.GraphTaskRecord(
            M.Atom(),
            L.ParityLabel,
            M.EmptyList,
            M.Pair(L.OddLabel, M.Atom()),
            M.Atom(),
            M.EmptyList,
            M.Atom(),
        )()
        corr_e2 = SurfaceCorrespondence(
            M.Atom(), pat_e2, task_e2, pat_e2
        )()

        # 4. Engel Coins
        pat_coins = self._build_token_stream(["solve", "the", "coin", "problem"])
        task_coins = GT.GraphTaskRecord(
            M.Atom(),
            L.UnreachableLabel,
            M.EmptyList,
            M.Pair(L.InvariantLabel, M.Atom()),
            M.Atom(),
            M.EmptyList,
            M.Atom(),
        )()
        corr_coins = SurfaceCorrespondence(
            M.Atom(), pat_coins, task_coins, pat_coins
        )()

        # 5. Sqrt Real
        pat_sqrt = self._build_token_stream(["prove", "square", "roots", "are", "real"])
        task_sqrt = GT.GraphTaskRecord(
            M.Atom(),
            L.IsRealLabel,
            M.EmptyList,
            M.Pair(L.IsRealLabel, M.Atom()),
            M.Atom(),
            M.EmptyList,
            M.Atom(),
        )()
        corr_sqrt = SurfaceCorrespondence(
            M.Atom(), pat_sqrt, task_sqrt, pat_sqrt
        )()

        rules = M.Pair(
            corr_tao,
            M.Pair(
                corr_e1,
                M.Pair(
                    corr_e2,
                    M.Pair(corr_coins, M.Pair(corr_sqrt, M.EmptyList)),
                ),
            ),
        )
        return rules

    def __call__(self):
        return self.result


class SurfaceDefinition(M.Edge):
    """
    Machine-native concept definition record.
    inputs: [concept_name_atom, explanation_tokens]
    results: Pair(SurfaceDefinitionLabel, Pair(concept_name_atom, Pair(explanation_tokens, EmptyList)))
    """

    def __init__(self, concept_name_atom, explanation_tokens):
        self.concept_name_atom = concept_name_atom
        self.explanation_tokens = explanation_tokens
        self.result = M.Pair(
            L.SurfaceDefinitionLabel,
            M.Pair(
                concept_name_atom,
                M.Pair(explanation_tokens, M.EmptyList),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                concept_name_atom,
                M.Pair(explanation_tokens, M.EmptyList),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BuildStandardDefinitions(M.Edge):
    """
    Constructs canonical machine-native concept definition hyperedges.
    """

    def __init__(self, registry):
        self.registry = registry
        self.result = self._build()
        super().__init__(
            inputs=M.Pair(registry, M.EmptyList),
            results=self.result,
        )

    def _build_tokens(self, words):
        if not words:
            return M.EmptyList
        tok = SurfaceToken(M.Char(words[0]))()
        rest = self._build_tokens(words[1:])
        return M.Pair(tok, rest)

    def _build(self):
        # 1. subdomain
        d_subdomain = SurfaceDefinition(
            M.Char("subdomain"),
            self._build_tokens([
                "a", "subdomain", "is", "a", "subset", "of", "a", "base", "domain",
                "filtered", "by", "a", "predicate", "or", "condition"
            ]),
        )()

        # 2. projection
        d_proj = SurfaceDefinition(
            M.Char("projection"),
            self._build_tokens([
                "an", "image", "projection", "is", "the", "set", "of", "remainder", "values",
                "obtained", "under", "an", "equivalence", "modulus"
            ]),
        )()

        # 3. disjoint
        d_disjoint = SurfaceDefinition(
            M.Char("disjoint"),
            self._build_tokens([
                "two", "sets", "are", "disjoint", "when", "their", "intersection", "is", "empty",
                "sharing", "no", "elements"
            ]),
        )()

        # 4. obstruction
        d_obstruction = SurfaceDefinition(
            M.Char("obstruction"),
            self._build_tokens([
                "an", "obstruction", "is", "a", "structural", "invariant", "conflict",
                "proving", "an", "equation", "or", "goal", "has", "no", "solutions"
            ]),
        )()

        # 5. parity
        d_parity = SurfaceDefinition(
            M.Char("parity"),
            self._build_tokens([
                "parity", "is", "the", "integer", "property", "of", "being", "even", "or", "odd"
            ]),
        )()

        # 6. invariant
        d_invariant = SurfaceDefinition(
            M.Char("invariant"),
            self._build_tokens([
                "an", "invariant", "is", "a", "property", "or", "relation", "that", "remains",
                "constant", "under", "all", "state", "transitions"
            ]),
        )()

        # 7. monovariant
        d_monovariant = SurfaceDefinition(
            M.Char("monovariant"),
            self._build_tokens([
                "a", "monovariant", "is", "a", "semi-invariant", "that", "strictly", "decreases",
                "at", "each", "step", "proving", "termination"
            ]),
        )()

        # 8. cartesian
        d_cartesian = SurfaceDefinition(
            M.Char("cartesian"),
            self._build_tokens([
                "a", "cartesian", "product", "is", "the", "set", "of", "all", "ordered",
                "tuples", "formed", "across", "input", "domains"
            ]),
        )()

        # 9. flt
        d_flt = SurfaceDefinition(
            M.Char("flt"),
            self._build_tokens([
                "fermat", "last", "theorem", "states", "that", "x^n", "+", "y^n", "=", "z^n",
                "has", "no", "positive", "integer", "solutions", "for", "n", ">", "2"
            ]),
        )()

        # 10. engel
        d_engel = SurfaceDefinition(
            M.Char("engel"),
            self._build_tokens([
                "arthur", "engel", "problem", "solving", "strategies", "formalize",
                "invariance", "monovariants", "coloring", "and", "extremal", "principles"
            ]),
        )()

        # 11. ledger
        d_ledger = SurfaceDefinition(
            M.Char("ledger"),
            self._build_tokens([
                "the", "promotion", "ledger", "is", "a", "dual-ledger", "state", "machine",
                "separating", "candidate", "lemmas", "from", "certified", "active", "rules"
            ]),
        )()

        defs = M.Pair(
            d_subdomain,
            M.Pair(
                d_proj,
                M.Pair(
                    d_disjoint,
                    M.Pair(
                        d_obstruction,
                        M.Pair(
                            d_parity,
                            M.Pair(
                                d_invariant,
                                M.Pair(
                                    d_monovariant,
                                    M.Pair(
                                        d_cartesian,
                                        M.Pair(
                                            d_flt,
                                            M.Pair(
                                                d_engel,
                                                M.Pair(d_ledger, M.EmptyList),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        return defs

    def __call__(self):
        return self.result


class QueryConceptDefinition(M.Edge):
    """
    Queries a concept definition from a Pair chain of SurfaceDefinition hyperedges.
    """

    def __init__(self, concept_char_atom, definitions_chain):
        self.result = self._lookup(concept_char_atom, definitions_chain)
        super().__init__(
            inputs=M.Pair(concept_char_atom, M.Pair(definitions_chain, M.EmptyList)),
            results=self.result,
        )

    def _lookup(self, target_atom, cur_defs):
        if M.IdentityCompare(cur_defs, M.EmptyList)() is M.truth_value:
            return M.Pair(L.DefinitionNotFoundLabel, M.EmptyList)
        d = M.Head(cur_defs)()
        concept_atom = M.Head(M.Tail(d)())()
        match_res = M.Match(concept_atom, target_atom)()
        if M.IdentityCompare(M.Head(match_res)(), M.truth_value)() is M.truth_value:
            return M.Pair(L.SurfaceParseSuccessLabel, M.Pair(d, M.EmptyList))
        return self._lookup(target_atom, M.Tail(cur_defs)())

    def __call__(self):
        return self.result


class RenderConceptExplanation(M.Edge):
    """
    Renders a SurfaceDefinition hyperedge into a natural surface explanation text.
    """

    def __init__(self, def_node):
        self.result = self._render(def_node)
        super().__init__(
            inputs=M.Pair(def_node, M.EmptyList),
            results=self.result,
        )

    def _render(self, def_node):
        tag = M.Head(def_node)()
        if M.IdentityCompare(tag, L.SurfaceDefinitionLabel)() is M.false_value:
            return M.EmptyList
        tokens = M.Head(M.Tail(M.Tail(def_node)())())()
        return M.Char(self._tokens_to_string(tokens))

    def _tokens_to_string(self, cur):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return ""
        tok = M.Head(cur)()
        atom = M.Head(M.Tail(tok)())()
        val = str(atom())
        rest_str = self._tokens_to_string(M.Tail(cur)())
        if rest_str:
            return val + " " + rest_str
        return val

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
    "BuildStandardCorrespondences",
    "SurfaceDefinition",
    "BuildStandardDefinitions",
    "QueryConceptDefinition",
    "RenderConceptExplanation",
)
