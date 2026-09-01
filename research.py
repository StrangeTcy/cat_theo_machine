from __future__ import annotations

from . import machine as M
from . import labels as Lmod
from . import context as Ctx
from .core import Edge, EmptyList, Pair, Head, Tail, IdentityCompare

def EnableResearchMode(graph=None):
    """Turn research mode on for one graph.

    Mode lives in the graph context, never in module state: a fresh process
    reading a cold checkpoint must not inherit a switch.
    """
    if graph is not None:
        graph.set_research_mode(M.truth_value)
    return M.truth_value

def DisableResearchMode(graph=None):
    if graph is not None:
        graph.set_research_mode(M.false_value)
    return M.false_value

def IsResearchMode(graph=None):
    """Machine truth value answering whether research mode is on.

    A graph with no research-mode marker answers false_value.
    """
    if graph is not None:
        marker = Ctx.ContextResearchMode(graph.context)()
        return M.IdentityCompare(
            M.IdentityCompare(marker, M.EmptyList)(),
            M.false_value,
        )()
    return M.false_value

def IsResearchModeEdgeValue(graph=None):
    return IsResearchMode(graph)

class Provenance:
    DOMAIN_AXIOM = Lmod.DomainAxiomLabel
    LIBRARY_THEOREM = Lmod.LibraryTheoremLabel
    HUMAN_SUPPLIED_TRUSTED_THEOREM = Lmod.HumanSuppliedTrustedTheoremLabel
    PREWRITTEN_PROOF_LADDER = Lmod.PrewrittenProofLadderLabel
    DERIVATION_CACHE_HIT = Lmod.DerivationCacheHitLabel
    SCHEMA_REPLAY = Lmod.SchemaReplayLabel
    SEARCH_DERIVED = Lmod.SearchDerivedLabel
    INVENTED_LEMMA = Lmod.InventedLemmaLabel
    INVENTED_OBJECT = Lmod.InventedObjectLabel
    INVENTED_TRANSFORMATION = Lmod.InventedTransformationLabel
    DEPENDENCY_REQUEST = Lmod.DependencyRequestProvenanceLabel
    COUNTEREXAMPLE = Lmod.CounterexampleLabel
    FAILURE = Lmod.FailureLabel

class DependencyKind:
    THEOREM = Lmod.TheoremKindLabel
    OBJECT = Lmod.ObjectKindLabel
    REPRESENTATION = Lmod.RepresentationKindLabel
    TRANSFORMATION = Lmod.TransformationKindLabel
    TACTIC = Lmod.TacticKindLabel
    DOMAIN_PROPERTY = Lmod.DomainPropertyKindLabel

class DependencyStatus:
    PENDING = Lmod.PendingStatusLabel
    APPROVED = Lmod.ApprovedStatusLabel
    REJECTED = Lmod.RejectedStatusLabel
    REFINED = Lmod.RefinedStatusLabel
    # Spec section 5: observation, hypothesis and demonstration are distinct.
    OBSERVED_MISSING_PREMISE = Lmod.ObservedMissingPremiseLabel
    SPECULATIVE = Lmod.SpeculativeDependencyLabel
    HUMAN_SUPPLIED_STRATEGY_PRIOR = Lmod.HumanSuppliedStrategyPriorLabel
    HUMAN_SUPPLIED_TRUSTED_THEOREM = Lmod.HumanSuppliedTrustedTheoremLabel
    HUMAN_SUPPLIED_WITHOUT_UNLOCK = Lmod.HumanSuppliedTrustedTheoremWithoutUnlockLabel
    DEMONSTRATED_USEFUL = Lmod.DemonstratedUsefulDependencyLabel
    LEARNED_POLICY = Lmod.LearnedDependencyPolicyLabel

class DependencyRequest(Edge):
    def __init__(self, parent_goal, residuals, blocking_condition, kind, formal_statement, bridge_plan, counterfactual_evidence, assumptions, status, provenance, dep_id=None):
        if dep_id is None:
            dep_id = M.Atom()
        chain = M.EmptyList
        chain = M.Pair(dep_id, chain)
        chain = M.Pair(provenance, chain)
        chain = M.Pair(status, chain)
        chain = M.Pair(assumptions, chain)
        chain = M.Pair(counterfactual_evidence, chain)
        chain = M.Pair(bridge_plan, chain)
        chain = M.Pair(formal_statement, chain)
        chain = M.Pair(kind, chain)
        chain = M.Pair(blocking_condition, chain)
        chain = M.Pair(residuals, chain)
        chain = M.Pair(parent_goal, chain)
        self.result = M.Pair(Lmod.DependencyRequestLabel, chain)
        super().__init__(inputs=M.Pair(parent_goal, M.Pair(residuals, M.EmptyList)), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestParentGoal(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestResiduals(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestBlockingCondition(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestKind(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestFormalStatement(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestBridgePlan(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestCounterfactual(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestAssumptions(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestStatus(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestProvenance(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class DependencyRequestId(Edge):
    def __init__(self, dep_req):
        chain = M.Tail(dep_req)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        chain = M.Tail(chain)()
        self.result = M.Head(chain)()
        super().__init__(inputs=M.Pair(dep_req, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class GoalDependsOnDependency(Edge):
    def __init__(self, goal, dep_id):
        self.result = M.Pair(Lmod.GoalDependsOnDependencyLabel, M.Pair(goal, M.Pair(dep_id, M.EmptyList)))
        super().__init__(inputs=M.Pair(goal, M.Pair(dep_id, M.EmptyList)), results=self.result)
    def __call__(self):
        return self.result

class CounterfactualEvidence(Edge):
    def __init__(self, cost_before, cost_after, newly_enabled_firings, removed_obligations, new_obligations, goal_closed):
        chain = M.EmptyList
        chain = M.Pair(goal_closed, chain)
        chain = M.Pair(new_obligations, chain)
        chain = M.Pair(removed_obligations, chain)
        chain = M.Pair(newly_enabled_firings, chain)
        chain = M.Pair(cost_after, chain)
        chain = M.Pair(cost_before, chain)
        self.result = M.Pair(Lmod.CounterfactualEvidenceLabel, chain)
        super().__init__(inputs=M.Pair(cost_before, M.Pair(cost_after, M.EmptyList)), results=self.result)
    def __call__(self):
        return self.result

class GeneratorStats(Edge):
    def __init__(self, gen_id, proposed, approved, rejected, useful, used, mean_cost_reduction, reuse):
        chain = M.EmptyList
        chain = M.Pair(reuse, chain)
        chain = M.Pair(mean_cost_reduction, chain)
        chain = M.Pair(used, chain)
        chain = M.Pair(useful, chain)
        chain = M.Pair(rejected, chain)
        chain = M.Pair(approved, chain)
        chain = M.Pair(proposed, chain)
        chain = M.Pair(gen_id, chain)
        self.result = M.Pair(Lmod.GeneratorStatsLabel, chain)
        super().__init__(inputs=M.Pair(gen_id, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class IsAttemptedRule(Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.AttemptedRuleLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptedRule(Edge):
    """One operational rule that was tried against a stall state and failed.

    Fields in order: rule id, rule origin, substitution, matched premises,
    unmatched premise, failure kind. Only the unmatched premise may become
    the content of a dependency request, and it is a formal term: there is
    no field here that can carry a strategy sentence.
    """

    def __init__(self, rule_id, origin, substitution, matched_premises, unmatched_premise, failure):
        body = M.Pair(
            rule_id,
            M.Pair(
                origin,
                M.Pair(
                    substitution,
                    M.Pair(matched_premises, M.Pair(unmatched_premise, M.Pair(failure, EmptyList))),
                ),
            ),
        )
        self.result = M.Pair(Lmod.AttemptedRuleLabel, body)
        super().__init__(inputs=body, results=self.result)

    def __call__(self):
        return self.result


class AttemptedRuleId(Edge):
    def __init__(self, attempt):
        self.result = Head(Tail(attempt)())()
        super().__init__(inputs=M.Pair(attempt, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptedRuleOrigin(Edge):
    def __init__(self, attempt):
        self.result = Head(Tail(Tail(attempt)())())()
        super().__init__(inputs=M.Pair(attempt, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptedRuleSubstitution(Edge):
    def __init__(self, attempt):
        self.result = Head(Tail(Tail(Tail(attempt)())())())()
        super().__init__(inputs=M.Pair(attempt, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptedRuleMatched(Edge):
    def __init__(self, attempt):
        self.result = Head(Tail(Tail(Tail(Tail(attempt)())())())())()
        super().__init__(inputs=M.Pair(attempt, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptedRuleUnmatched(Edge):
    def __init__(self, attempt):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(attempt)())())())())())()
        super().__init__(inputs=M.Pair(attempt, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptedRuleFailure(Edge):
    def __init__(self, attempt):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(attempt)())())())())())())()
        super().__init__(inputs=M.Pair(attempt, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HasNameableUnmatchedPremise(Edge):
    """True only when the attempt left a concrete formal premise unmatched."""

    def __init__(self, attempt):
        self.result = M.false_value
        if IsAttemptedRule(attempt)() is M.truth_value:
            if IdentityCompare(AttemptedRuleUnmatched(attempt)(), EmptyList)() is M.false_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(attempt, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CharacterizedAttempts(Edge):
    """The subchain of attempts that can actually support a request."""

    def __init__(self, attempts):
        self.result = M.Reverse(self._walk(attempts, EmptyList))()
        super().__init__(inputs=M.Pair(attempts, EmptyList), results=self.result)

    def _walk(self, attempts, acc):
        if IdentityCompare(attempts, EmptyList)() is M.truth_value:
            return acc
        attempt = Head(attempts)()
        rest = Tail(attempts)()
        if HasNameableUnmatchedPremise(attempt)() is M.truth_value:
            return self._walk(rest, M.Pair(attempt, acc))
        return self._walk(rest, acc)

    def __call__(self):
        return self.result


class SubstLookup(Edge):
    """Look one variable up in a Pair(variable, value) chain."""

    def __init__(self, variable, chain):
        self.result = self._walk(variable, chain)
        super().__init__(inputs=M.Pair(variable, M.Pair(chain, EmptyList)), results=self.result)

    def _walk(self, variable, chain):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(chain)()
        if M.TermEqual(Head(entry)(), variable)() is M.truth_value:
            return Head(Tail(entry)())()
        return self._walk(variable, Tail(chain)())

    def __call__(self):
        return self.result


class AlphaNormalizeTerm(Edge):
    """Rename substitution-bound atoms to positional placeholders.

    Returns Pair(normalized, Pair(environment, Pair(next_index, EmptyList))).
    An atom is treated as a variable only when the substitution binds it, so
    constants and constructors are left alone and no atom needs a name field.
    """

    def __init__(self, term, substitution):
        self.result = self._walk(term, substitution, EmptyList, M.Zero)
        super().__init__(inputs=M.Pair(term, M.Pair(substitution, EmptyList)), results=self.result)

    def _walk(self, term, substitution, env, next_index):
        if IdentityCompare(term, EmptyList)() is M.truth_value:
            return M.Pair(EmptyList, M.Pair(env, M.Pair(next_index, EmptyList)))
        if M.IsPair(term)() is M.truth_value:
            head_result = self._walk(Head(term)(), substitution, env, next_index)
            norm_head = Head(head_result)()
            env1 = Head(Tail(head_result)())()
            index1 = Head(Tail(Tail(head_result)())())()
            tail_result = self._walk(Tail(term)(), substitution, env1, index1)
            norm_tail = Head(tail_result)()
            env2 = Head(Tail(tail_result)())()
            index2 = Head(Tail(Tail(tail_result)())())()
            return M.Pair(M.Pair(norm_head, norm_tail), M.Pair(env2, M.Pair(index2, EmptyList)))
        bound = SubstLookup(term, substitution)()
        if IdentityCompare(bound, EmptyList)() is M.truth_value:
            return M.Pair(term, M.Pair(env, M.Pair(next_index, EmptyList)))
        seen = SubstLookup(term, env)()
        if IdentityCompare(seen, EmptyList)() is M.false_value:
            return M.Pair(seen, M.Pair(env, M.Pair(next_index, EmptyList)))
        placeholder = M.Pair(Lmod.AlphaPlaceholderLabel, next_index)
        new_env = M.Pair(M.Pair(term, placeholder), env)
        next_pair = M.Succ(next_index, M.AllConstructors)()
        return M.Pair(
            placeholder,
            M.Pair(new_env, M.Pair(Head(next_pair)(), EmptyList)),
        )

    def __call__(self):
        return self.result


class AlphaNormalized(Edge):
    """Just the normalized term, environment discarded."""

    def __init__(self, term, substitution):
        self.result = Head(AlphaNormalizeTerm(term, substitution)())()
        super().__init__(inputs=M.Pair(term, M.Pair(substitution, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class NeedStatement(Edge):
    """The formal content of a request: Need(unmatched_premise)."""

    def __init__(self, premise):
        self.result = M.Pair(Lmod.NeedLabel, M.Pair(premise, EmptyList))
        super().__init__(inputs=M.Pair(premise, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsUncharacterizedStall(Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.UncharacterizedStallLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class UncharacterizedStall(Edge):
    """What the machine reports when it cannot name a missing premise.

    Fields: goal, applicable rules, attempted operational rules, unmatched
    formal premises, dependency-characterized.
    """

    def __init__(self, goal, attempts, applicable_rules):
        body = M.Pair(
            goal,
            M.Pair(
                applicable_rules,
                M.Pair(attempts, M.Pair(EmptyList, M.Pair(M.false_value, EmptyList))),
            ),
        )
        self.result = M.Pair(Lmod.UncharacterizedStallLabel, body)
        super().__init__(inputs=body, results=self.result)

    def __call__(self):
        return self.result


class StallGoal(Edge):
    def __init__(self, stall):
        self.result = Head(Tail(stall)())()
        super().__init__(inputs=M.Pair(stall, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StallApplicableRules(Edge):
    def __init__(self, stall):
        self.result = Head(Tail(Tail(stall)())())()
        super().__init__(inputs=M.Pair(stall, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StallAttempts(Edge):
    def __init__(self, stall):
        self.result = Head(Tail(Tail(Tail(stall)())())())()
        super().__init__(inputs=M.Pair(stall, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DependencyRequestFromAttempt(Edge):
    """Compile one attempt into a request.

    The whole content of the request is the alpha-normalized unmatched
    premise of a rule that really was tried. Nothing here inspects the
    surface shape of the goal, and there is no table mapping failure kinds
    or domains to prose.
    """

    def __init__(self, attempt, parent_goal, blocking_condition, dep_id=None):
        if dep_id is None:
            dep_id = M.Atom()
        substitution = AttemptedRuleSubstitution(attempt)()
        unmatched = AttemptedRuleUnmatched(attempt)()
        formal = NeedStatement(AlphaNormalized(unmatched, substitution)())()
        matched = AttemptedRuleMatched(attempt)()
        evidence = CounterfactualEvidence(M.Zero, M.Zero, EmptyList, EmptyList, EmptyList, M.false_value)()
        self.result = DependencyRequest(
            parent_goal,
            M.Pair(attempt, EmptyList),
            blocking_condition,
            DependencyKind.THEOREM,
            formal,
            EmptyList,
            evidence,
            matched,
            DependencyStatus.OBSERVED_MISSING_PREMISE,
            Lmod.DependencyRequestProvenanceLabel,
            dep_id,
        )()
        super().__init__(inputs=M.Pair(attempt, M.Pair(parent_goal, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GenBase:
    def __init__(self, gen_label):
        self.gen_label = gen_label
        self.proposed = 0
        self.approved = 0
        self.rejected = 0
        self.useful = 0
        self.used = 0
        self.mean_cost_reduction = 0
        self.reuse = 0

    def propose(self, parent_goal, residuals, blocking_condition, graph):
        return EmptyList

    def _make_request(self, parent_goal, residuals, blocking_condition, kind, formal_stmt, bridge_plan, assumptions, dep_id=None):
        if dep_id is None:
            # Identity, not a name: two requests are the same node only when
            # they are the same atom. No target-derived text lives here.
            dep_id = M.Atom()
        ev = CounterfactualEvidence(M.Zero, M.Zero, M.EmptyList, M.EmptyList, M.EmptyList, M.false_value)()
        req = DependencyRequest(parent_goal, residuals, blocking_condition, kind, formal_stmt, bridge_plan, ev, assumptions, DependencyStatus.PENDING, Lmod.DependencyRequestProvenanceLabel, dep_id)()
        self.proposed = self.proposed + 1
        return req

class ChainLength(Edge):
    """Length of a pair chain as a machine Nat."""

    def __init__(self, chain):
        self.result = self._walk(chain, M.Zero)
        super().__init__(inputs=M.Pair(chain, EmptyList), results=self.result)

    def _walk(self, chain, acc):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return acc
        return self._walk(Tail(chain)(), Head(M.Succ(acc, M.AllConstructors)())())

    def __call__(self):
        return self.result


class GenDependencyRequestFromResidual(GenBase):
    """The only generator.

    It proposes exclusively from AttemptedRule records: a rule that was
    really tried against the stalled state and left one concrete formal
    premise unmatched. It never inspects the surface shape of the goal, and
    it holds no table from failure kind or domain to prose.

    When no attempt carries a nameable unmatched premise it returns an
    UncharacterizedStall record rather than a request. Saying that the gap
    cannot be characterized is the correct output; a guess dressed up as a
    discovery is not.
    """

    def __init__(self):
        super().__init__(Lmod.GenDependencyRequestFromResidualLabel)

    def propose(self, parent_goal, attempts, blocking_condition, graph):
        characterized = CharacterizedAttempts(attempts)()
        if IdentityCompare(characterized, EmptyList)() is M.truth_value:
            applicable = ChainLength(attempts)()
            return M.Pair(UncharacterizedStall(parent_goal, attempts, applicable)(), EmptyList)
        return self._compile(characterized, parent_goal, blocking_condition, EmptyList)

    def _compile(self, attempts, parent_goal, blocking_condition, acc):
        if IdentityCompare(attempts, EmptyList)() is M.truth_value:
            return M.Reverse(acc)()
        attempt = Head(attempts)()
        rest = Tail(attempts)()
        request = DependencyRequestFromAttempt(attempt, parent_goal, blocking_condition)()
        self.proposed = self.proposed + 1
        return self._compile(rest, parent_goal, blocking_condition, M.Pair(request, acc))


THE_GENERATOR = GenDependencyRequestFromResidual()


def get_generator_by_label(label):
    if IdentityCompare(THE_GENERATOR.gen_label, label)() is M.truth_value:
        return THE_GENERATOR
    return M.EmptyList


class RegisterProposals(Edge):
    """Store admissible requests and grow the dependency graph.

    A stall record is passed straight through: it is a report, not a
    proposal, and it is never stored as a dependency.
    """

    def __init__(self, proposals, parent_goal, graph):
        self.result = self._walk(proposals, parent_goal, graph)
        super().__init__(inputs=M.Pair(proposals, M.Pair(parent_goal, EmptyList)), results=self.result)

    def _walk(self, proposals, parent_goal, graph):
        if IdentityCompare(proposals, EmptyList)() is M.truth_value:
            return EmptyList
        record = Head(proposals)()
        rest = Tail(proposals)()
        if IsUncharacterizedStall(record)() is M.truth_value:
            return M.Pair(record, self._walk(rest, parent_goal, graph))
        verdict = ValidateDependencyRequest(record, parent_goal)()
        if IdentityCompare(verdict, M.truth_value)() is M.false_value:
            THE_GENERATOR.rejected = THE_GENERATOR.rejected + 1
            return self._walk(rest, parent_goal, graph)
        store_dependency_request(graph, record)
        dep_id = DependencyRequestId(record)()
        graph._replace_context(
            dependency_graph=M.Pair(
                GoalDependsOnDependency(parent_goal, dep_id)(),
                graph.dependency_graph,
            )
        )
        return M.Pair(record, self._walk(rest, parent_goal, graph))

    def __call__(self):
        return self.result


def suggest_dependencies(parent_goal, attempts, blocking_condition, graph):
    """Propose from attempted-rule evidence, or report an honest stall.

    Returns a pair chain whose elements are either DependencyRequest terms
    or a single UncharacterizedStall term.
    """
    proposals = THE_GENERATOR.propose(parent_goal, attempts, blocking_condition, graph)
    return RegisterProposals(proposals, parent_goal, graph)()


class RestatesGoal(Edge):
    """True when the parent goal occurs anywhere inside the term."""

    def __init__(self, term, parent_goal):
        self.result = self._walk(term, parent_goal)
        super().__init__(inputs=M.Pair(term, M.Pair(parent_goal, EmptyList)), results=self.result)

    def _walk(self, term, parent_goal):
        if M.TermEqual(term, parent_goal)() is M.truth_value:
            return M.truth_value
        if M.IsPair(term)() is M.truth_value:
            if self._walk(Head(term)(), parent_goal) is M.truth_value:
                return M.truth_value
            return self._walk(Tail(term)(), parent_goal)
        return M.false_value

    def __call__(self):
        return self.result


class AssertsBlockingContradiction(Edge):
    """True when the request simply asserts the contradiction it must bridge."""

    def __init__(self, formal, blocking):
        self.result = M.false_value
        if M.IsPair(blocking)() is M.truth_value:
            if M.TermEqual(M.Head(blocking)(), Lmod.ContradictionLabel)() is M.truth_value:
                if M.TermEqual(formal, blocking)() is M.truth_value:
                    self.result = M.truth_value
        super().__init__(inputs=M.Pair(formal, M.Pair(blocking, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ValidateDependencyRequest(Edge):
    """Reject circular and vacuous requests.

    Rejects a request that restates the parent goal, asserts the blocking
    contradiction, or claims a speculative dependency without a replayable
    bridge. An observed missing premise carries no bridge by construction
    and makes no discovery claim, so the bridge rule does not apply to it.
    """

    def __init__(self, req, parent_goal):
        formal = DependencyRequestFormalStatement(req)()
        status = DependencyRequestStatus(req)()
        bridge = DependencyRequestBridgePlan(req)()
        blocking = DependencyRequestBlockingCondition(req)()
        self.result = M.truth_value
        if RestatesGoal(formal, parent_goal)() is M.truth_value:
            self.result = M.false_value
        if AssertsBlockingContradiction(formal, blocking)() is M.truth_value:
            self.result = M.false_value
        not_observed = M.NotAtom(
            IdentityCompare(status, DependencyStatus.OBSERVED_MISSING_PREMISE)()
        )()
        claims_bridge = M.AndAtom(IdentityCompare(bridge, EmptyList)(), not_observed)()
        if IdentityCompare(claims_bridge, M.truth_value)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(req, M.Pair(parent_goal, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


def validate_dependency_request(req, parent_goal):
    return ValidateDependencyRequest(req, parent_goal)()


def counterfactual_evaluation(graph, parent_goal, residuals, dependency_term, bounded_search_steps=50):
    try:
        from .graph import Hypergraph
        fork = Hypergraph(graph.constructor_registry)
        fork._replace_context(nodes=graph.nodes, edges=graph.edges, all_rules=graph.all_rules, rule_order=graph.rule_order, derivations=graph.derivations, derivation_schemata=graph.derivation_schemata, search_memo=graph.search_memo, nat_value_index=graph.nat_value_index)
        fork._replace_context(nodes=M.Pair(dependency_term, fork.nodes))
        goal_closed = M.false_value
        try:
            from . import proof as Pmod
            prover = Pmod.Prove(fork, parent_goal, M.EmptyList)
            result = None
            try:
                result = prover._prove()
            except Exception:
                result = None
            if result is not None:
                goal_closed = M.truth_value
        except Exception:
            goal_closed = M.false_value
        ev = CounterfactualEvidence(M.Zero, M.Zero, M.EmptyList, M.EmptyList, M.EmptyList, goal_closed)()
        return ev, goal_closed
    except Exception:
        ev = CounterfactualEvidence(M.Zero, M.Zero, M.EmptyList, M.EmptyList, M.EmptyList, M.false_value)()
        return ev, M.false_value

class EvaluateUnlock(Edge):
    """Useful only on measured evidence.

    A dependency is demonstrated useful when the goal closed, when an
    existing rule was newly enabled, or when residual cost fell. Approval
    by a human is not evidence, and neither is the request existing.
    """

    def __init__(self, useful_condition, goal_closed, cost_before, cost_after):
        self.result = M.false_value
        if IdentityCompare(goal_closed, M.truth_value)() is M.truth_value:
            self.result = M.truth_value
        if IdentityCompare(useful_condition, M.truth_value)() is M.truth_value:
            self.result = M.truth_value
        cheaper = M.NatLess(cost_after, cost_before, M.AllConstructors)()
        if IdentityCompare(cheaper, M.truth_value)() is M.truth_value:
            self.result = M.truth_value
        super().__init__(
            inputs=M.Pair(useful_condition, M.Pair(goal_closed, M.Pair(cost_before, M.Pair(cost_after, EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


def evaluate_unlock(useful_condition, goal_closed, cost_before, cost_after):
    return EvaluateUnlock(useful_condition, goal_closed, cost_before, cost_after)()

def store_dependency_request(graph, req):
    graph._replace_context(dependency_requests=M.Pair(req, graph.dependency_requests))
    return req

class FindRequest(Edge):
    """The request carrying this id, or EmptyList."""

    def __init__(self, chain, dep_id):
        self.result = self._walk(chain, dep_id)
        super().__init__(inputs=M.Pair(chain, M.Pair(dep_id, EmptyList)), results=self.result)

    def _walk(self, chain, dep_id):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return EmptyList
        req = Head(chain)()
        if M.TermEqual(DependencyRequestId(req)(), dep_id)() is M.truth_value:
            return req
        return self._walk(Tail(chain)(), dep_id)

    def __call__(self):
        return self.result


class RebuildRequest(Edge):
    """One request rebuilt with a new status, same identity."""

    def __init__(self, req, status):
        self.result = DependencyRequest(
            DependencyRequestParentGoal(req)(),
            DependencyRequestResiduals(req)(),
            DependencyRequestBlockingCondition(req)(),
            DependencyRequestKind(req)(),
            DependencyRequestFormalStatement(req)(),
            DependencyRequestBridgePlan(req)(),
            DependencyRequestCounterfactual(req)(),
            DependencyRequestAssumptions(req)(),
            status,
            DependencyRequestProvenance(req)(),
            DependencyRequestId(req)(),
        )()
        super().__init__(inputs=M.Pair(req, M.Pair(status, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SetRequestStatus(Edge):
    """Replace the status of one request in place. The node keeps its id.

    Status is a field of a single node that changes: Pending -> Approved ->
    Taught -> Useful, or Pending -> Rejected. No second copy is created, so
    the graph can never show one request as both pending and approved.
    """

    def __init__(self, chain, dep_id, status):
        self.result = self._walk(chain, dep_id, status, EmptyList)
        super().__init__(inputs=M.Pair(chain, M.Pair(dep_id, M.Pair(status, EmptyList))), results=self.result)

    def _walk(self, chain, dep_id, status, acc):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return M.Reverse(acc)()
        req = Head(chain)()
        rest = Tail(chain)()
        if M.TermEqual(DependencyRequestId(req)(), dep_id)() is M.truth_value:
            return self._walk(rest, dep_id, status, M.Pair(RebuildRequest(req, status)(), acc))
        return self._walk(rest, dep_id, status, M.Pair(req, acc))

    def __call__(self):
        return self.result


class SetRequestFormal(Edge):
    """Replace the formal statement of one request in place."""

    def __init__(self, chain, dep_id, formal):
        self.result = self._walk(chain, dep_id, formal, EmptyList)
        super().__init__(inputs=M.Pair(chain, M.Pair(dep_id, M.Pair(formal, EmptyList))), results=self.result)

    def _walk(self, chain, dep_id, formal, acc):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return M.Reverse(acc)()
        req = Head(chain)()
        rest = Tail(chain)()
        if M.TermEqual(DependencyRequestId(req)(), dep_id)() is M.truth_value:
            rebuilt = DependencyRequest(
                DependencyRequestParentGoal(req)(),
                DependencyRequestResiduals(req)(),
                DependencyRequestBlockingCondition(req)(),
                DependencyRequestKind(req)(),
                formal,
                DependencyRequestBridgePlan(req)(),
                DependencyRequestCounterfactual(req)(),
                DependencyRequestAssumptions(req)(),
                DependencyStatus.REFINED,
                DependencyRequestProvenance(req)(),
                DependencyRequestId(req)(),
            )()
            return self._walk(rest, dep_id, formal, M.Pair(rebuilt, acc))
        return self._walk(rest, dep_id, formal, M.Pair(req, acc))

    def __call__(self):
        return self.result


def approve_dependency(graph, dep_id):
    """Mark one request approved.

    Approval is a status change and nothing else. It does not teach the
    formal statement, and it does not make the request useful: usefulness
    is demonstrated by counterfactual evidence, not by approval.
    """
    graph._replace_context(
        dependency_requests=SetRequestStatus(
            graph.dependency_requests, dep_id, DependencyStatus.APPROVED
        )()
    )
    return FindRequest(graph.dependency_requests, dep_id)()


def reject_dependency(graph, dep_id):
    graph._replace_context(
        dependency_requests=SetRequestStatus(
            graph.dependency_requests, dep_id, DependencyStatus.REJECTED
        )()
    )
    return FindRequest(graph.dependency_requests, dep_id)()


def refine_dependency(graph, dep_id, new_formal):
    graph._replace_context(
        dependency_requests=SetRequestFormal(graph.dependency_requests, dep_id, new_formal)()
    )
    return FindRequest(graph.dependency_requests, dep_id)()


class ChainHasId(Edge):
    """True when a dep id already occurs in a chain of ids."""

    def __init__(self, ids, dep_id):
        self.result = self._walk(ids, dep_id)
        super().__init__(inputs=M.Pair(ids, M.Pair(dep_id, EmptyList)), results=self.result)

    def _walk(self, ids, dep_id):
        if IdentityCompare(ids, EmptyList)() is M.truth_value:
            return M.false_value
        if M.TermEqual(Head(ids)(), dep_id)() is M.truth_value:
            return M.truth_value
        return self._walk(Tail(ids)(), dep_id)

    def __call__(self):
        return self.result


class RequestStatusById(Edge):
    """Current status of a request, or EmptyList when it is unknown."""

    def __init__(self, requests, dep_id):
        self.result = self._walk(requests, dep_id)
        super().__init__(inputs=M.Pair(requests, M.Pair(dep_id, EmptyList)), results=self.result)

    def _walk(self, requests, dep_id):
        if IdentityCompare(requests, EmptyList)() is M.truth_value:
            return EmptyList
        req = Head(requests)()
        if M.TermEqual(DependencyRequestId(req)(), dep_id)() is M.truth_value:
            return DependencyRequestStatus(req)()
        return self._walk(Tail(requests)(), dep_id)

    def __call__(self):
        return self.result


class DependencyGraphView(Edge):
    """One entry per request, showing the status the node currently holds.

    Entries are deduplicated by request id, so a request that has moved
    from pending to approved appears once, as approved.
    """

    def __init__(self, graph):
        self.result = self._walk(graph.dependency_graph, graph.dependency_requests, EmptyList, EmptyList)
        super().__init__(inputs=M.Pair(graph.dependency_graph, EmptyList), results=self.result)

    def _walk(self, edges, requests, seen_ids, acc):
        if IdentityCompare(edges, EmptyList)() is M.truth_value:
            return M.Reverse(acc)()
        entry = Head(edges)()
        rest = Tail(edges)()
        dep_id = Head(Tail(Tail(entry)())())()
        goal = Head(Tail(entry)())()
        if ChainHasId(seen_ids, dep_id)() is M.truth_value:
            return self._walk(rest, requests, seen_ids, acc)
        status = RequestStatusById(requests, dep_id)()
        row = M.Pair(goal, M.Pair(dep_id, M.Pair(status, EmptyList)))
        return self._walk(rest, requests, M.Pair(dep_id, seen_ids), M.Pair(row, acc))

    def __call__(self):
        return self.result


def show_dependency_graph(graph):
    """Pair chain of Pair(goal, Pair(dep id, Pair(status, EmptyList))).

    Shows only requests the machine actually produced and the knowledge it
    actually accepted. No reference graph is stored anywhere.
    """
    return DependencyGraphView(graph)()


class AuditEntries(Edge):
    """Pair chain of Pair(term, Pair(provenance, EmptyList)) over provenance_map.

    Malformed rows are skipped rather than raising, so an audit never fails
    halfway through.
    """

    def __init__(self, provenance_map):
        self.result = self._walk(provenance_map, EmptyList)
        super().__init__(inputs=M.Pair(provenance_map, EmptyList), results=self.result)

    def _walk(self, chain, acc):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return M.Reverse(acc)()
        entry = Head(chain)()
        rest = Tail(chain)()
        if M.IsPair(entry)() is M.false_value:
            return self._walk(rest, acc)
        tail = Tail(entry)()
        if M.IsPair(tail)() is M.false_value:
            return self._walk(rest, acc)
        row = M.Pair(Head(entry)(), M.Pair(Head(tail)(), EmptyList))
        return self._walk(rest, M.Pair(row, acc))

    def __call__(self):
        return self.result


def audit_knowledge(graph):
    """Everything the machine currently holds, with its provenance class."""
    return AuditEntries(graph.provenance_map)()


def explain_last_proof(graph):
    return graph.last_proof

def set_last_proof(graph, proof_term):
    graph._replace_context(last_proof=proof_term)

def set_last_residuals(graph, residuals):
    if IdentityCompare(residuals, M.EmptyList)() is M.truth_value:
        placeholder = M.Pair(M.Char("root"), M.EmptyList)
        residuals = M.Pair(Lmod.ZeroSuccessorResidualLabel, M.Pair(placeholder, M.EmptyList))
    else:
        if M.IsPair(residuals)() is M.truth_value:
            if IdentityCompare(M.Head(residuals)(), Lmod.ZeroSuccessorResidualLabel)() is M.false_value:
                residuals = M.Pair(Lmod.ZeroSuccessorResidualLabel, M.Pair(residuals, M.EmptyList))
        else:
            placeholder = M.Pair(M.Char("root"), M.EmptyList)
            residuals = M.Pair(Lmod.ZeroSuccessorResidualLabel, M.Pair(placeholder, M.EmptyList))
    graph._replace_context(last_residuals=residuals, research_residuals=residuals)

def get_last_residuals(graph):
    return graph.last_residuals

class ZeroSuccessorResidual(Edge):
    def __init__(self, goal):
        self.result = M.Pair(Lmod.ZeroSuccessorResidualLabel, M.Pair(goal, M.EmptyList))
        super().__init__(inputs=M.Pair(goal, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class HasStatsLabel(Edge):
    """True when a metrics row already exists for this generator label."""

    def __init__(self, chain, gen_label):
        self.result = self._walk(chain, gen_label)
        super().__init__(inputs=M.Pair(chain, M.Pair(gen_label, EmptyList)), results=self.result)

    def _walk(self, chain, gen_label):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return M.false_value
        stats = Head(chain)()
        label = Head(Tail(stats)())()
        if M.TermEqual(label, gen_label)() is M.truth_value:
            return M.truth_value
        return self._walk(Tail(chain)(), gen_label)

    def __call__(self):
        return self.result


class StatsForLabel(Edge):
    """A metrics row for one generator, or EmptyList if it is unknown."""

    def __init__(self, gen_label):
        gen = get_generator_by_label(gen_label)
        self.result = EmptyList
        if IdentityCompare(gen, M.EmptyList)() is M.false_value:
            self.result = GeneratorStats(
                gen_label,
                M.GMPRep(str(gen.proposed)),
                M.GMPRep(str(gen.approved)),
                M.GMPRep(str(gen.rejected)),
                M.GMPRep(str(gen.useful)),
                M.GMPRep(str(gen.used)),
                M.GMPRep(str(gen.mean_cost_reduction)),
                M.GMPRep(str(gen.reuse)),
            )()
        super().__init__(inputs=M.Pair(gen_label, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EnsureGeneratorStats(Edge):
    """Make sure one metrics row exists for this generator label.

    Counters are structural only: proposed, approved, rejected, useful,
    used, mean residual-cost reduction, reuse. Nothing here keys on a
    theorem name, constant, variable name or target identifier.
    """

    def __init__(self, chain, gen_label):
        self.result = chain
        if HasStatsLabel(chain, gen_label)() is M.false_value:
            row = StatsForLabel(gen_label)()
            if IdentityCompare(row, EmptyList)() is M.false_value:
                self.result = M.Pair(row, chain)
        super().__init__(inputs=M.Pair(chain, M.Pair(gen_label, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


def update_generator_metrics(graph, gen_label):
    graph._replace_context(
        generator_metrics=EnsureGeneratorStats(graph.generator_metrics, gen_label)()
    )
    return graph.generator_metrics


def get_research_attempts(graph):
    """The attempted-rule chain recorded by search for this session."""
    return Ctx.ContextResearchAttempts(graph.context)()


def set_last_attempts(graph, attempts):
    """Publish the attempt chain as the current residuals."""
    graph._replace_context(last_residuals=attempts, research_residuals=attempts)
    return attempts
