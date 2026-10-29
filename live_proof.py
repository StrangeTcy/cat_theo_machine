"""Persist live proof requests and replay bounded, checked equality proofs.

The original text and complete GoalSpec remain attached to every outcome.
Operation discovery does not change the meaning or status of the request.
"""

from . import checker_b as CB
from . import heuristics as H
from . import labels as L
from . import machine as M
from . import playground as PG
from . import proof as P
from . import search as S


class LiveProofRecordField(M.Edge):
    def __init__(self, record, index):
        positions = M.Pair(
            M.Zero,
            M.Pair(
                M.one,
                M.Pair(
                    M.two,
                    M.Pair(
                        M.three,
                        M.Pair(M.four, M.Pair(M.five, M.Pair(M.six, M.Pair(M.seven, M.EmptyList)))),
                    ),
                ),
            ),
        )
        self.result = self._field(record, index, positions)
        super().__init__(
            inputs=M.Pair(record, M.Pair(index, M.EmptyList)), results=self.result
        )

    def _field(self, record, index, positions):
        if M.IsPair(record)() is M.false_value:
            return M.EmptyList
        if M.IsPair(positions)() is M.false_value:
            return M.EmptyList
        if M.IdentityCompare(index, M.Head(positions)())() is M.truth_value:
            return M.Head(record)()
        return self._field(M.Tail(record)(), index, M.Tail(positions)())

    def __call__(self):
        return self.result


class LiveProofRequestText(LiveProofRecordField):
    def __init__(self, request):
        super().__init__(request, M.one)


class LiveProofRequestSpec(LiveProofRecordField):
    def __init__(self, request):
        super().__init__(request, M.two)


class LiveProofOutcomeRequest(LiveProofRecordField):
    def __init__(self, outcome):
        super().__init__(outcome, M.one)


class LiveProofOutcomeStatus(LiveProofRecordField):
    def __init__(self, outcome):
        super().__init__(outcome, M.two)


class LiveProofOutcomeReason(LiveProofRecordField):
    def __init__(self, outcome):
        super().__init__(outcome, M.three)


class LiveProofOutcomeReceipt(LiveProofRecordField):
    def __init__(self, outcome):
        super().__init__(outcome, M.four)


class LiveProofOutcomeVerification(LiveProofRecordField):
    def __init__(self, outcome):
        super().__init__(outcome, M.five)


class LiveProofOutcomeRegistry(LiveProofRecordField):
    def __init__(self, outcome):
        super().__init__(outcome, M.six)


class LiveProofOutcomeSearchJob(LiveProofRecordField):
    def __init__(self, outcome):
        super().__init__(outcome, M.seven)


class LatestLiveProofRequest(M.Edge):
    def __init__(self, nodes):
        self.result = self._find(nodes)
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def _find(self, nodes):
        if M.IsPair(nodes)() is M.false_value:
            return M.EmptyList
        record = M.Head(nodes)()
        if M.IsPair(record)() is M.truth_value:
            if M.Compare(M.Head(record)(), M.Char("live-proof-request-v1"))() is M.truth_value:
                return record
        return self._find(M.Tail(nodes)())

    def __call__(self):
        return self.result


class LatestLiveProofOutcome(M.Edge):
    def __init__(self, nodes, request=M.EmptyList):
        self.result = self._find(nodes, request)
        super().__init__(
            inputs=M.Pair(nodes, M.Pair(request, M.EmptyList)), results=self.result
        )

    def _find(self, nodes, request):
        if M.IsPair(nodes)() is M.false_value:
            return M.EmptyList
        record = M.Head(nodes)()
        if M.IsPair(record)() is M.truth_value:
            if M.Compare(M.Head(record)(), M.Char("live-proof-outcome-v1"))() is M.truth_value:
                if M.IdentityCompare(request, M.EmptyList)() is M.truth_value:
                    return record
                if M.Compare(LiveProofOutcomeRequest(record)(), request)() is M.truth_value:
                    return record
        return self._find(M.Tail(nodes)(), request)

    def __call__(self):
        return self.result


class RecordLiveProofRequest(M.Edge):
    """Return a graph.nodes record containing original text and full GoalSpec."""

    def __init__(self, graph, text_char, spec=M.EmptyList):
        registry = M.FromContextGetConstructors(graph)()
        try:
            parsed = PG.ParseSurfaceGoalSpec(text_char, registry)()
        except (AttributeError, TypeError, ValueError, RecursionError):
            parsed = M.EmptyList
        if M.IdentityCompare(spec, M.EmptyList)() is M.truth_value:
            spec = parsed
        if PG.ExactArity(parsed, M.eight, registry)() is M.truth_value:
            registry = PG.GoalSpecRegistry(parsed)()
            graph._replace_context(constructors=registry)
        self.result = M.Pair(
            M.Char("live-proof-request-v1"),
            M.Pair(text_char, M.Pair(spec, M.EmptyList)),
        )
        graph.add_node(self.result)
        super().__init__(
            inputs=M.Pair(text_char, M.Pair(spec, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class LiveProofSurfaceMatches(M.Edge):
    """Require one complete arithmetic equality, with no discarded prose.

Only single-letter variables, natural numerals, +, *, ^, and parentheses
are admitted here. The surface parser's full-expression entry point must
consume both complete sides and reproduce the preserved request terms.
"""

    def __init__(self, text_char, spec, registry):
        self.result = M.false_value
        try:
            text = text_char().strip().removeprefix("prove ")
            parser = PG.ParseSurfaceGoalSpec(M.Char(text), registry)
            chars = parser._string_chars(text)
            if self._characters(chars, parser) is M.truth_value:
                tokens = parser._tokenize(chars)
                if self._tokens(tokens, parser) is M.truth_value:
                    split = parser._split_at_eq(tokens)
                    if M.IsPair(split)() is M.truth_value:
                        before = PG.ChainReverse(M.Head(split)())()
                        equality = M.Head(M.Tail(split)())()
                        after = M.Head(M.Tail(M.Tail(split)())())()
                        if M.Compare(equality, M.Char("="))() is M.truth_value:
                            lhs, interned, reg = parser._parse_expr(before, M.EmptyList, registry)
                            rhs, interned, reg = parser._parse_expr(after, interned, reg)
                            if M.IdentityCompare(lhs, M.EmptyList)() is M.false_value:
                                if M.IdentityCompare(rhs, M.EmptyList)() is M.false_value:
                                    self.result = M.AndAtom(
                                        M.AndAtom(
                                            M.Compare(lhs, PG.GoalSpecLhs(spec)())(),
                                            M.Compare(rhs, PG.GoalSpecRhs(spec)())(),
                                        )(),
                                        M.Compare(
                                            PG.GoalSpecBaseVars(parser())(),
                                            PG.GoalSpecBaseVars(spec)(),
                                        )(),
                                    )()
        except (AttributeError, TypeError, ValueError, RecursionError):
            self.result = M.false_value
        super().__init__(
            inputs=M.Pair(text_char, M.Pair(spec, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _symbols(self):
        return M.Pair(
            M.Char("+"),
            M.Pair(
                M.Char("*"),
                M.Pair(
                    M.Char("^"),
                    M.Pair(M.Char("("), M.Pair(M.Char(")"), M.Pair(M.Char("="), M.EmptyList))),
                ),
            ),
        )

    def _characters(self, chars, parser):
        if M.IdentityCompare(chars, M.EmptyList)() is M.truth_value:
            return M.truth_value
        char = M.Head(chars)()
        admitted = M.OrAtom(
            PG.ChainHasTerm(parser._letter_symbols, char)(),
            M.OrAtom(
                PG.ChainHasTerm(parser._digit_symbols, char)(),
                M.OrAtom(
                    PG.ChainHasTerm(parser._space_symbols, char)(),
                    PG.ChainHasTerm(self._symbols(), char)(),
                )(),
            )(),
        )()
        if admitted is M.false_value:
            return M.false_value
        return self._characters(M.Tail(chars)(), parser)

    def _tokens(self, tokens, parser):
        if M.IdentityCompare(tokens, M.EmptyList)() is M.truth_value:
            return M.truth_value
        token = M.Head(tokens)()
        admitted = M.OrAtom(
            PG.ChainHasTerm(parser._letter_symbols, token)(),
            M.OrAtom(
                parser._is_digits(token()),
                PG.ChainHasTerm(self._symbols(), token)(),
            )(),
        )()
        if admitted is M.false_value:
            return M.false_value
        return self._tokens(M.Tail(tokens)(), parser)

    def __call__(self):
        return self.result


class BoundedLiveEqualitySearch(M.Edge):
    """Visit every Pair position, with a finite budget of expanded expressions.

The existing search cursor prunes branches with no matching rule at their
root. This equality traversal also visits such branches, so a law inside
an otherwise unchanged expression can produce a checked rewrite plan.
"""

    def __init__(self, lhs, rhs, rules, step_budget, registry):
        self.registry = registry
        self.goal = rhs
        self.rules = rules
        self.frontier = M.Pair(S.SearchState(lhs, M.EmptyList, M.EmptyList, step_budget)(), M.EmptyList)
        self.pending = M.EmptyList
        self.visited = M.Pair(lhs, M.EmptyList)
        self.plan = M.EmptyList
        self.expanded = M.Zero
        self.generated = M.Zero
        self.frontier_size = M.one
        self.frontier_peak = M.one
        self._run(step_budget)
        status = S.SearchRunningLabel
        if M.IdentityCompare(self.plan, M.EmptyList)() is M.false_value:
            status = S.SearchSuccessLabel
        elif M.AndAtom(
            M.IdentityCompare(self.frontier, M.EmptyList)(),
            M.IdentityCompare(self.pending, M.EmptyList)(),
        )() is M.truth_value:
            status = S.SearchFailureLabel
        frontier = PG.ChainConcat(self.frontier, PG.ChainReverse(self.pending)())()
        heuristic = H.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.Zero, M.one, M.one, M.Zero)()
        job = S.SearchJob(
            lhs, rhs, rules, heuristic, status, frontier,
            self.expanded, self.generated, self.frontier_peak, self.plan,
            self.visited, M.EmptyList, rules, self.frontier_size,
        )()
        self.result = M.Pair(job, M.Pair(self.registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(lhs, M.Pair(rhs, M.Pair(rules, M.Pair(step_budget, M.Pair(registry, M.EmptyList))))),
            results=self.result,
        )

    def _increment(self, value):
        built = M.Succ(value, self.registry)()
        self.registry = M.Head(M.Tail(built)())()
        return M.Head(built)()

    def _decrement(self, value):
        built = M.NatPred(value, self.registry)()
        self.registry = M.Head(M.Tail(built)())()
        return M.Head(built)()

    def _run(self, remaining):
        if M.NatEq(remaining, M.Zero, self.registry)() is M.truth_value:
            return
        if M.IdentityCompare(self.frontier, M.EmptyList)() is M.truth_value:
            self.frontier = PG.ChainReverse(self.pending)()
            self.pending = M.EmptyList
        if M.IdentityCompare(self.frontier, M.EmptyList)() is M.truth_value:
            return
        state = M.Head(self.frontier)()
        self.frontier = M.Tail(self.frontier)()
        self.frontier_size = self._decrement(self.frontier_size)
        self.current = S.SearchStateCurrent(state)()
        self.current_plan = S.SearchStatePlan(state)()
        self.expanded = self._increment(self.expanded)
        self._visit(self.current, M.EmptyList)
        if M.IdentityCompare(self.plan, M.EmptyList)() is M.false_value:
            return
        self._run(self._decrement(remaining))

    def _visit(self, subterm, path):
        if M.IdentityCompare(self.plan, M.EmptyList)() is M.false_value:
            return
        self._apply(self.rules, subterm, path)
        if M.IsPair(subterm)() is M.truth_value:
            self._visit(M.Head(subterm)(), PG.ChainConcat(path, M.Pair(M.Zero, M.EmptyList))())
            self._visit(M.Tail(subterm)(), PG.ChainConcat(path, M.Pair(M.one, M.EmptyList))())

    def _apply(self, rules, subterm, path):
        if M.IdentityCompare(self.plan, M.EmptyList)() is M.false_value:
            return
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return
        rule = M.Head(rules)()
        if P.RuleIsUnary(rule)() is M.truth_value:
            rewritten = P.RewriteHere(rule, subterm)()
            if M.Compare(rewritten, subterm)() is M.false_value:
                following = P.RewriteAtPath(rule, self.current, path, self.registry)()
                if PG.ChainHasTerm(self.visited, following)() is M.false_value:
                    self.visited = M.Pair(following, self.visited)
                    self.generated = self._increment(self.generated)
                    plan = M.Pair(P.RewriteAction(rule, path)(), self.current_plan)
                    if M.Compare(following, self.goal)() is M.truth_value:
                        self.plan = PG.ChainReverse(plan)()
                        return
                    state = S.SearchState(following, plan, M.EmptyList, M.EmptyList)()
                    self.pending = M.Pair(state, self.pending)
                    self.frontier_size = self._increment(self.frontier_size)
                    if M.NatLess(self.frontier_peak, self.frontier_size, self.registry)() is M.truth_value:
                        self.frontier_peak = self.frontier_size
        self._apply(M.Tail(rules)(), subterm, path)

    def __call__(self):
        return self.result


class RetryLiveProofRequest(M.Edge):
    """Return a persisted outcome after one finite active-rule equality retry.

Outcome fields after the Char tag: request, status, reason, receipt,
verification, registry, search job. Pending is never a disproof.
"""

    def __init__(self, graph, request=M.EmptyList, step_budget=M.three):
        self.graph = graph
        self.registry = M.FromContextGetConstructors(graph)()
        if M.IdentityCompare(request, M.EmptyList)() is M.truth_value:
            request = LatestLiveProofRequest(M.FromContextGetNodes(graph)())()
        self.request = request
        self.result = self._retry(step_budget)
        self.graph._replace_context(constructors=self.registry)
        self.graph.add_node(self.result)
        super().__init__(
            inputs=M.Pair(request, M.Pair(step_budget, M.EmptyList)), results=self.result
        )

    def _outcome(self, reason, status=L.PendingLabel, receipt=M.EmptyList, verification=M.EmptyList, job=M.EmptyList):
        return M.Pair(
            M.Char("live-proof-outcome-v1"),
            M.Pair(
                self.request,
                M.Pair(
                    status,
                    M.Pair(
                        M.Char(reason),
                        M.Pair(
                            receipt,
                            M.Pair(verification, M.Pair(self.registry, M.Pair(job, M.EmptyList))),
                        ),
                    ),
                ),
            ),
        )

    def _retry(self, step_budget):
        if PG.ExactArity(self.request, M.three, self.registry)() is M.false_value:
            return self._outcome("No well-formed live proof request is available.")
        if M.Compare(M.Head(self.request)(), M.Char("live-proof-request-v1"))() is M.false_value:
            return self._outcome("The supplied record is not a live proof request.")
        spec = LiveProofRequestSpec(self.request)()
        if PG.ExactArity(spec, M.eight, self.registry)() is M.false_value:
            return self._outcome("The original goal has no complete parsed proof scope.")
        try:
            registry_record = PG.GoalSpecRegistry(spec)()()
        except (AttributeError, TypeError):
            return self._outcome("The supplied goal specification has no constructor registry.")
        if M.IsPair(registry_record)() is M.false_value:
            return self._outcome("The supplied goal specification has no constructor registry.")
        if M.IdentityCompare(M.Head(registry_record)(), M.TreeLabel)() is M.false_value:
            return self._outcome("The supplied goal specification has no constructor registry.")
        if PG.GoalSpecNoSolutions(spec)() is not M.false_value:
            return self._outcome("The no-solutions claim is preserved. A universal exclusion or descent proof is still required.")
        if M.IdentityCompare(PG.GoalSpecExpVars(spec)(), M.EmptyList)() is M.false_value:
            return self._outcome("The exponent family is preserved. Equality rewriting does not discharge its universal obligation.")
        if M.IdentityCompare(PG.GoalSpecParamConstraints(spec)(), M.EmptyList)() is M.false_value:
            return self._outcome("The parameter constraints are preserved. Their scoped proof obligations remain open.")
        if PG.GoalSpecPositiveOnly(spec)() is not M.false_value:
            return self._outcome("The positive-variable scope is preserved. A proof under that scope is still required.")
        if LiveProofSurfaceMatches(LiveProofRequestText(self.request)(), spec, self.registry)() is M.false_value:
            return self._outcome("The complete surface goal is not a supported bare arithmetic equality. No extracted equation was substituted for it.")
        lhs = PG.GoalSpecLhs(spec)()
        rhs = PG.GoalSpecRhs(spec)()
        variables = PG.GoalSpecBaseVars(spec)()
        if PG.AdmittedPolynomial(lhs, variables, self.registry)() is M.false_value:
            return self._outcome("The left side is outside the admitted polynomial equality fragment.")
        if PG.AdmittedPolynomial(rhs, variables, self.registry)() is M.false_value:
            return self._outcome("The right side is outside the admitted polynomial equality fragment.")
        if M.IsNat(step_budget, self.registry)() is M.false_value:
            return self._outcome("The retry requires a finite natural-number search budget.")
        if M.NatEq(step_budget, M.Zero, self.registry)() is M.truth_value:
            return self._outcome("The retry budget is zero; no proof search was performed.")
        trusted_rules = PG.ChainReverse(M.FromContextGetRuleOrder(self.graph)())()
        if M.Compare(lhs, rhs)() is M.truth_value:
            cost_pair = P.BuildProofCost(M.EmptyList, self.registry)()
            cost = M.Head(cost_pair)()
            self.registry = M.Head(M.Tail(cost_pair)())()
            built = P.Derivation(M.EmptyList, cost, self.registry)()
            return self._verify(built, lhs, rhs, trusted_rules, M.EmptyList)
        if M.IdentityCompare(trusted_rules, M.EmptyList)() is M.truth_value:
            return self._outcome("No active equality rule is available. A learned, checked law can be retried against this goal.")
        burst = BoundedLiveEqualitySearch(lhs, rhs, trusted_rules, step_budget, self.registry)()
        job = M.Head(burst)()
        self.registry = M.Head(M.Tail(burst)())()
        if M.IdentityCompare(S.SearchJobStatus(job)(), S.SearchSuccessLabel)() is M.false_value:
            return self._outcome(
                "The bounded retry produced no checked proof. The original goal remains open.", job=job
            )
        plan = S.SearchJobResultPlan(job)()
        built = P.BuildRewriteDerivation(lhs, plan, self.registry)()
        if M.IdentityCompare(M.Head(built)(), M.EmptyList)() is M.truth_value:
            self.registry = M.Head(M.Tail(built)())()
            return self._outcome("The search supplied no replayable derivation. The goal remains open.", job=job)
        return self._verify(built, lhs, rhs, trusted_rules, job)

    def _verify(self, built, lhs, rhs, trusted_rules, job):
        derivation = M.Head(built)()
        self.registry = M.Head(M.Tail(built)())()
        verification = CB.VerifyDerivation(derivation, lhs, rhs, trusted_rules, self.registry)()
        if M.IdentityCompare(M.Head(verification)(), L.DerivationVerifiedLabel)() is M.false_value:
            return self._outcome(
                "Checker B did not verify the candidate derivation. The goal remains open.",
                verification=verification, job=job,
            )
        receipt = M.Pair(
            L.ProofReceiptLabel,
            M.Pair(
                LiveProofRequestText(self.request)(),
                M.Pair(
                    lhs,
                    M.Pair(
                        rhs,
                        M.Pair(
                            derivation,
                            M.Pair(self.registry, M.Pair(trusted_rules, M.Pair(verification, M.EmptyList))),
                        ),
                    ),
                ),
            ),
        )
        self.graph._replace_context(constructors=self.registry)
        self.graph.add_derivation(lhs, rhs, derivation)
        self.graph.add_node(receipt)
        return self._outcome(
            "Checker B verified the derivation against the active rule snapshot.",
            L.ProvedLabel, receipt, verification, job,
        )

    def __call__(self):
        return self.result


class FormatLiveProofScopeItems(M.Edge):
    """Render a machine chain of retained variables or constraints."""

    def __init__(self, terms, registry):
        if M.IdentityCompare(terms, M.EmptyList)() is M.truth_value:
            self.result = ""
        elif M.IsPair(terms)() is M.truth_value:
            self.result = PG.RenderNatExpr(M.Head(terms)(), registry)()
            rest = M.Tail(terms)()
            if M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
                self.result = self.result + ", " + FormatLiveProofScopeItems(rest, registry)()
        else:
            self.result = "unavailable"
        super().__init__(inputs=M.Pair(terms, M.Pair(registry, M.EmptyList)), results=M.EmptyList)

    def __call__(self):
        return self.result


class FormatLiveProofScope(M.Edge):
    """Explain retained scope without searching, certifying, or changing it."""

    def __init__(self, request, registry):
        spec = LiveProofRequestSpec(request)()
        self.result = "Parsed scope unavailable; the original request remains pending."
        if PG.ExactArity(spec, M.eight, registry)() is M.truth_value:
            self.result = (
                "Parsed relation: " + PG.RenderNatExpr(PG.GoalSpecLhs(spec)(), registry)()
                + " = " + PG.RenderNatExpr(PG.GoalSpecRhs(spec)(), registry)() + "."
            )
            if PG.GoalSpecNoSolutions(spec)() is M.truth_value:
                self.result = self.result + "\nClaim: no solutions in the stated scope."
            elif PG.GoalSpecNoSolutions(spec)() is M.false_value:
                self.result = self.result + "\nClaim: equality in the stated scope."
            else:
                self.result = self.result + "\nClaim scope unavailable."
            variables = PG.GoalSpecBaseVars(spec)()
            if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
                self.result = self.result + "\nBase variables: " + FormatLiveProofScopeItems(variables, registry)() + "."
            if PG.GoalSpecPositiveOnly(spec)() is M.truth_value:
                self.result = self.result + "\nDomain restriction: positive variables."
            elif PG.GoalSpecPositiveOnly(spec)() is M.false_value:
                self.result = self.result + "\nArithmetic domain: natural numbers, including zero."
            else:
                self.result = self.result + "\nDomain restriction unavailable."
            exponents = PG.GoalSpecExpVars(spec)()
            if M.IdentityCompare(exponents, M.EmptyList)() is M.false_value:
                self.result = self.result + "\nExponent parameters: " + FormatLiveProofScopeItems(exponents, registry)() + "."
            constraints = PG.GoalSpecParamConstraints(spec)()
            if M.IdentityCompare(constraints, M.EmptyList)() is M.false_value:
                self.result = self.result + "\nParameter restrictions: " + FormatLiveProofScopeItems(constraints, registry)() + "."
            if PG.GoalSpecNoSolutions(spec)() is M.truth_value:
                self.result = self.result + (
                    "\nRequired proof: exclude every assignment satisfying the original request."
                    " Finite observations alone do not establish this."
                )
        super().__init__(inputs=M.Pair(request, M.Pair(registry, M.EmptyList)), results=M.EmptyList)

    def __call__(self):
        return self.result


class FormatLiveProofOutcome(M.Edge):
    def __init__(self, outcome, registry):
        self.registry = registry
        self.result = self._format(outcome)
        super().__init__(inputs=M.Pair(outcome, M.Pair(registry, M.EmptyList)), results=M.EmptyList)

    def _format(self, outcome):
        if M.IdentityCompare(outcome, M.EmptyList)() is M.truth_value:
            return "No live proof outcome has been recorded."
        request = LiveProofOutcomeRequest(outcome)()
        text = LiveProofRequestText(request)()
        try:
            goal_text = text().strip()
        except (AttributeError, TypeError):
            goal_text = "unavailable goal text"
        reason = LiveProofOutcomeReason(outcome)()()
        scope = FormatLiveProofScope(request, self.registry)()
        if M.IdentityCompare(LiveProofOutcomeStatus(outcome)(), L.ProvedLabel)() is M.false_value:
            return "Pending: " + goal_text + "\n" + scope + "\n" + reason
        receipt = LiveProofOutcomeReceipt(outcome)()
        derivation = LiveProofRecordField(receipt, M.four)()
        steps = P.DerivationSteps(derivation, self.registry)()
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            explanation = "Reflexivity: both sides are the same term."
        else:
            explanation = self._steps(steps)
        return "Proved: " + goal_text + "\n" + scope + "\n" + reason + "\nSaved proof receipt:\n" + explanation

    def _steps(self, steps):
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            return ""
        step = M.Head(steps)()
        current = P.StepCurrent(step, self.registry)()
        following = P.StepNext(step, self.registry)()
        return (
            "  " + PG.RenderNatExpr(current, self.registry)()
            + " = " + PG.RenderNatExpr(following, self.registry)() + "\n"
            + self._steps(M.Tail(steps)())
        )

    def __call__(self):
        return self.result
