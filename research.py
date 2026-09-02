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
    """The subchain of attempts able to support a request."""

    def __init__(self, attempts):
        self.result = M.Reverse(self._walk(attempts, EmptyList))()
        super().__init__(inputs=M.Pair(attempts, EmptyList), results=self.result)

    def _walk(self, attempts, acc):
        if IdentityCompare(attempts, EmptyList)() is M.truth_value:
            return acc
        attempt = Head(attempts)()
        rest = Tail(attempts)()
        if HasNameableUnmatchedPremise(attempt)() is M.truth_value:
            unmatched = AttemptedRuleUnmatched(attempt)()
            if IdentityCompare(EvaluateGround(unmatched)(), EmptyList)() is M.truth_value:
                return self._walk(rest, M.Pair(attempt, acc))
        return self._walk(rest, acc)

    def __call__(self):
        return self.result


class BindingValue(Edge):
    """The value carried by one binding entry.

    Accepts both shapes in use: Pair(var, Pair(value, EmptyList)) -- the
    matcher's own shape -- and the bare Pair(var, value).
    """

    def __init__(self, entry):
        payload = Tail(entry)()
        if M.IsPair(payload)() is M.truth_value:
            if IdentityCompare(Tail(payload)(), EmptyList)() is M.truth_value:
                self.result = Head(payload)()
            else:
                self.result = payload
        else:
            self.result = payload
        super().__init__(inputs=M.Pair(entry, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsVarPatternTerm(Edge):
    """True for Pair(VarTag, Pair(anything, EmptyList)) -- the matcher's variable."""

    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if IdentityCompare(Head(term)(), M.VarTag)() is M.truth_value:
                rest = Tail(term)()
                if M.IsPair(rest)() is M.truth_value:
                    if IdentityCompare(Tail(rest)(), EmptyList)() is M.truth_value:
                        self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ApplyBindings(Edge):
    """Substitute bound variables, preserving unbound variables by identity.

    Unlike Instantiate, an unbound variable is returned as the same object,
    so a later match against another premise still recognizes it. Nothing
    here consults a constructor registry: the walk is pure pairs.
    """

    def __init__(self, term, bindings):
        self.result = self._walk(term, bindings)
        super().__init__(inputs=M.Pair(term, M.Pair(bindings, EmptyList)), results=self.result)

    def _walk(self, term, bindings):
        if IdentityCompare(term, EmptyList)() is M.truth_value:
            return term
        if IsVarPatternTerm(term)() is M.truth_value:
            found = M.FindBinding(bindings, term)()
            flag = Head(found)()
            if IdentityCompare(flag, M.truth_value)() is M.truth_value:
                return Tail(found)()
            return term
        if M.IsPair(term)() is M.truth_value:
            return M.Pair(self._walk(Head(term)(), bindings), self._walk(Tail(term)(), bindings))
        return term

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
            return BindingValue(entry)()
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

    def _rename(self, term, env, next_index):
        """One renameable occurrence: reuse its placeholder or mint one."""
        seen = SubstLookup(term, env)()
        if IdentityCompare(seen, EmptyList)() is M.false_value:
            return M.Pair(seen, M.Pair(env, M.Pair(next_index, EmptyList)))
        placeholder = M.Pair(Lmod.AlphaPlaceholderLabel, next_index)
        new_env = M.Pair(M.Pair(term, M.Pair(placeholder, EmptyList)), env)
        next_pair = M.Succ(next_index, M.AllConstructors)()
        return M.Pair(
            placeholder,
            M.Pair(new_env, M.Pair(Head(next_pair)(), EmptyList)),
        )

    def _walk(self, term, substitution, env, next_index):
        if IdentityCompare(term, EmptyList)() is M.truth_value:
            return M.Pair(EmptyList, M.Pair(env, M.Pair(next_index, EmptyList)))
        if IsVarPatternTerm(term)() is M.truth_value:
            return self._rename(term, env, next_index)
        bound = SubstLookup(term, substitution)()
        if IdentityCompare(bound, EmptyList)() is M.false_value:
            # A subterm the substitution marks is renamed as one unit,
            # whether it is an atom or a compound value.
            return self._rename(term, env, next_index)
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
        return M.Pair(term, M.Pair(env, M.Pair(next_index, EmptyList)))

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
        concrete = ApplyBindings(unmatched, substitution)()
        formal = NeedStatement(AlphaNormalized(concrete, substitution)())()
        matched = AttemptedRuleMatched(attempt)()
        origin = AttemptedRuleOrigin(attempt)()
        provenance = Lmod.DependencyRequestProvenanceLabel
        if M.TermEqual(origin, Lmod.HumanSuppliedStrategyPriorLabel)() is M.truth_value:
            # Quarantine: a hole in a preinstalled strategy prior is a
            # suggestion from that prior, never a machine discovery.
            provenance = Lmod.HumanSuppliedStrategyPriorLabel
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
            provenance,
            dep_id,
        )()
        super().__init__(inputs=M.Pair(attempt, M.Pair(parent_goal, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GenBase:
    """A generator holds a label and nothing else.

    Every counter lives in the graph context as a machine term, so a fresh
    process reading a cold checkpoint sees the counters the checkpoint
    recorded, and no Python attribute can carry hidden state.
    """

    def __init__(self, gen_label):
        self.gen_label = gen_label

    def propose(self, parent_goal, residuals, blocking_condition, graph):
        return EmptyList

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
            bump_generator_metric(graph, Lmod.RejectedCountLabel)
            return self._walk(rest, parent_goal, graph)
        duplicate = FindRequestByFormal(
            graph.dependency_requests, DependencyRequestFormalStatement(record)()
        )()
        if IdentityCompare(duplicate, EmptyList)() is M.false_value:
            # The same alpha-normalized missing premise is one node, not two.
            return M.Pair(duplicate, self._walk(rest, parent_goal, graph))
        store_dependency_request(graph, record)
        bump_generator_metric(graph, Lmod.ProposedCountLabel)
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


class OrderFootholds(Edge):
    """Attempts with matched premises before conclusion-only footholds.

    Both are genuine; they are not equally strong. A rule that matched
    facts under the goal substitution ranks above one whose only
    evidence is the conclusion unification, so the request list leads
    with the deepest evidence instead of becoming a matcher-generated
    menu.
    """

    def __init__(self, attempts):
        strong = self._filter(attempts, M.truth_value)
        weak = self._filter(attempts, M.false_value)
        self.result = self._concat(strong, weak)
        super().__init__(inputs=M.Pair(attempts, EmptyList), results=self.result)

    def _filter(self, attempts, want_matched):
        if IdentityCompare(attempts, EmptyList)() is M.truth_value:
            return EmptyList
        attempt = Head(attempts)()
        rest = Tail(attempts)()
        has_matched = M.NotAtom(
            IdentityCompare(AttemptedRuleMatched(attempt)(), EmptyList)()
        )()
        if IdentityCompare(has_matched, want_matched)() is M.truth_value:
            return M.Pair(attempt, self._filter(rest, want_matched))
        return self._filter(rest, want_matched)

    def _concat(self, left, right):
        if IdentityCompare(left, EmptyList)() is M.truth_value:
            return right
        return M.Pair(Head(left)(), self._concat(Tail(left)(), right))

    def __call__(self):
        return self.result


def suggest_dependencies(parent_goal, attempts, blocking_condition, graph):
    """Propose from attempted-rule evidence, or report an uncharacterized stall.

    Returns a pair chain whose elements are either DependencyRequest terms
    or a single UncharacterizedStall term. Attempts are ordered deepest
    evidence first. With the generator disabled -- the ablation setting --
    nothing at all is proposed; if requests still appeared somewhere,
    another ladder would exist and would have to go.
    """
    if generator_enabled(graph) is M.false_value:
        return EmptyList
    ordered = OrderFootholds(attempts)()
    proposals = THE_GENERATOR.propose(parent_goal, ordered, blocking_condition, graph)
    return RegisterProposals(proposals, parent_goal, graph)()


class FindRequestByFormal(Edge):
    """The stored request carrying this formal statement, or EmptyList."""

    def __init__(self, chain, formal):
        self.result = self._walk(chain, formal)
        super().__init__(inputs=M.Pair(chain, M.Pair(formal, EmptyList)), results=self.result)

    def _walk(self, chain, formal):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return EmptyList
        req = Head(chain)()
        if M.TermEqual(DependencyRequestFormalStatement(req)(), formal)() is M.truth_value:
            return req
        return self._walk(Tail(chain)(), formal)

    def __call__(self):
        return self.result


class GeneratorEnabledFlag(Edge):
    """The ablation switch, read from the graph context.

    The generator_policy chain holds Pair(generator label, Pair(flag,
    EmptyList)) entries. Absent an entry, the generator is enabled: a cold
    checkpoint proposes from evidence, and ablation is an explicit act.
    """

    def __init__(self, graph):
        self.result = self._walk(graph.generator_policy)
        super().__init__(inputs=EmptyList, results=self.result)

    def _walk(self, chain):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return M.truth_value
        entry = Head(chain)()
        if M.IsPair(entry)() is M.truth_value:
            if IdentityCompare(Head(entry)(), Lmod.GenDependencyRequestFromResidualLabel)() is M.truth_value:
                payload = Tail(entry)()
                if M.IsPair(payload)() is M.truth_value:
                    return Head(payload)()
        return self._walk(Tail(chain)())

    def __call__(self):
        return self.result


def generator_enabled(graph):
    return GeneratorEnabledFlag(graph)()


def disable_generator(graph):
    entry = M.Pair(Lmod.GenDependencyRequestFromResidualLabel, M.Pair(M.false_value, EmptyList))
    graph._replace_context(generator_policy=M.Pair(entry, graph.generator_policy))
    return M.false_value


def enable_generator(graph):
    entry = M.Pair(Lmod.GenDependencyRequestFromResidualLabel, M.Pair(M.truth_value, EmptyList))
    graph._replace_context(generator_policy=M.Pair(entry, graph.generator_policy))
    return M.truth_value


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


class ChainShorter(Edge):
    """True when the left mark chain is strictly shorter than the right.

    Cost and fuel are chains of marks, not machine nats: incrementing a
    nat re-interns constructor trees against the global registry, which
    costs seconds once the theorem packs are loaded. A mark chain
    increments by one Pair and compares by one paired walk, touching no
    registry.
    """

    def __init__(self, left, right):
        self.result = self._walk(left, right)
        super().__init__(inputs=M.Pair(left, M.Pair(right, EmptyList)), results=self.result)

    def _walk(self, left, right):
        if IdentityCompare(right, EmptyList)() is M.truth_value:
            return M.false_value
        if IdentityCompare(left, EmptyList)() is M.truth_value:
            return M.truth_value
        return self._walk(Tail(left)(), Tail(right)())

    def __call__(self):
        return self.result


def _mark_chain(length):
    chain = EmptyList
    count = 0
    while count < length:
        chain = M.Pair(M.truth_value, chain)
        count += 1
    return chain


DEFAULT_SEARCH_FUEL = _mark_chain(12)


def counterfactual_evaluation(graph, start_facts, goal_facts, rules, taught_rule, fuel=None):
    """Fork, rerun bounded search, and measure -- never fabricate.

    baseline  = ContinueSearch(original stall, original rules, fuel)
    augmented = ContinueSearch(original stall, original rules + taught rule, same fuel)

    The taught rule must be a compiled executable rule. Evidence names the
    existing rules newly enabled, the residual obligations removed and
    added, the costs, and whether the goal closed. Nothing persists: the
    forward search below touches no graph context.
    """
    if fuel is None:
        fuel = DEFAULT_SEARCH_FUEL
    baseline = Head(evaluated_search(start_facts, goal_facts, rules, fuel))()
    augmented = Head(evaluated_search(start_facts, goal_facts, M.Pair(taught_rule, rules), fuel))()
    cost_before = ForwardSearchCost(baseline)()
    cost_after = ForwardSearchCost(augmented)()
    fired_before = ForwardSearchFired(baseline)()
    fired_after = ForwardSearchFired(augmented)()
    newly_enabled = FiredRuleDifference(fired_after, fired_before, taught_rule)()
    obligations_before = ResidualObligations(ForwardSearchFacts(baseline)(), rules)()
    obligations_after = ResidualObligations(
        ForwardSearchFacts(augmented)(), M.Pair(taught_rule, rules)
    )()
    removed_obligations = ObligationDifference(obligations_before, obligations_after)()
    new_obligations = ObligationDifference(obligations_after, obligations_before)()
    goal_closed = ForwardSearchClosed(augmented)()
    ev = CounterfactualEvidence(
        cost_before, cost_after, newly_enabled, removed_obligations, new_obligations, goal_closed
    )()
    graph.add_counterfactual_result(ev)
    cheaper = ChainShorter(cost_after, cost_before)()
    enabled_existing = M.NotAtom(IdentityCompare(newly_enabled, EmptyList)())()
    exposed_new = M.NotAtom(IdentityCompare(new_obligations, EmptyList)())()
    unlock = M.OrAtom(
        M.OrAtom(goal_closed, cheaper)(),
        M.OrAtom(enabled_existing, exposed_new)(),
    )()
    return ev, unlock


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
            graph.dependency_requests, dep_id, DependencyStatus.SPECULATIVE
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
        if IdentityCompare(Head(entry)(), Lmod.GoalDependsOnDependencyLabel)() is M.false_value:
            # Supplied-by and unlocked-by relations are rendered separately.
            return self._walk(rest, requests, seen_ids, acc)
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

    Shows only requests the machine itself produced and the knowledge it
    accepted. No reference graph is stored anywhere.
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

class GeneratorStatsRow(Edge):
    """The single metrics row for the generator, or a fresh all-zero row.

    Counters are structural only: proposed, approved, rejected, useful,
    used, mean residual-cost reduction, reuse. Nothing keys on a theorem
    name, constant, variable name or target identifier.
    """

    def __init__(self, graph):
        self.result = self._find(graph.generator_metrics)
        super().__init__(inputs=EmptyList, results=self.result)

    def _find(self, chain):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return GeneratorStats(
                Lmod.GenDependencyRequestFromResidualLabel,
                M.Zero, M.Zero, M.Zero, M.Zero, M.Zero, M.Zero, M.Zero,
            )()
        row = Head(chain)()
        if M.IsPair(row)() is M.truth_value:
            if IdentityCompare(Head(row)(), Lmod.GeneratorStatsLabel)() is M.truth_value:
                return row
        return self._find(Tail(chain)())

    def __call__(self):
        return self.result


class GeneratorStatsField(Edge):
    """One counter out of a stats row, selected by slot label."""

    def __init__(self, row, slot_label):
        body = Tail(Tail(row)())()
        proposed = Head(body)()
        approved = Head(Tail(body)())()
        rejected = Head(Tail(Tail(body)())())()
        useful = Head(Tail(Tail(Tail(body)())())())()
        used = Head(Tail(Tail(Tail(Tail(body)())())())())()
        mean = Head(Tail(Tail(Tail(Tail(Tail(body)())())())())())()
        reuse = Head(Tail(Tail(Tail(Tail(Tail(Tail(body)())())())())())())()
        self.result = proposed
        if IdentityCompare(slot_label, Lmod.ApprovedCountLabel)() is M.truth_value:
            self.result = approved
        if IdentityCompare(slot_label, Lmod.RejectedCountLabel)() is M.truth_value:
            self.result = rejected
        if IdentityCompare(slot_label, Lmod.UsefulCountLabel)() is M.truth_value:
            self.result = useful
        if IdentityCompare(slot_label, Lmod.UsedCountLabel)() is M.truth_value:
            self.result = used
        if IdentityCompare(slot_label, Lmod.MeanCostReductionLabel)() is M.truth_value:
            self.result = mean
        if IdentityCompare(slot_label, Lmod.ReuseCountLabel)() is M.truth_value:
            self.result = reuse
        super().__init__(inputs=M.Pair(row, M.Pair(slot_label, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BumpGeneratorStats(Edge):
    """A stats row with one counter advanced by one."""

    def __init__(self, row, slot_label):
        body = Tail(Tail(row)())()
        proposed = Head(body)()
        approved = Head(Tail(body)())()
        rejected = Head(Tail(Tail(body)())())()
        useful = Head(Tail(Tail(Tail(body)())())())()
        used = Head(Tail(Tail(Tail(Tail(body)())())())())()
        mean = Head(Tail(Tail(Tail(Tail(Tail(body)())())())())())()
        reuse = Head(Tail(Tail(Tail(Tail(Tail(Tail(body)())())())())())())()
        if IdentityCompare(slot_label, Lmod.ProposedCountLabel)() is M.truth_value:
            proposed = self._succ(proposed)
        if IdentityCompare(slot_label, Lmod.ApprovedCountLabel)() is M.truth_value:
            approved = self._succ(approved)
        if IdentityCompare(slot_label, Lmod.RejectedCountLabel)() is M.truth_value:
            rejected = self._succ(rejected)
        if IdentityCompare(slot_label, Lmod.UsefulCountLabel)() is M.truth_value:
            useful = self._succ(useful)
        if IdentityCompare(slot_label, Lmod.UsedCountLabel)() is M.truth_value:
            used = self._succ(used)
        if IdentityCompare(slot_label, Lmod.ReuseCountLabel)() is M.truth_value:
            reuse = self._succ(reuse)
        self.result = GeneratorStats(
            Lmod.GenDependencyRequestFromResidualLabel,
            proposed, approved, rejected, useful, used, mean, reuse,
        )()
        super().__init__(inputs=M.Pair(row, M.Pair(slot_label, EmptyList)), results=self.result)

    def _succ(self, n):
        return Head(M.Succ(n, M.AllConstructors)())()

    def __call__(self):
        return self.result


def bump_generator_metric(graph, slot_label):
    """Advance one structural counter. The row is a single node in context.

    Approval deliberately has no bump here at its call site: a score moves
    only when a dependency enables real progress or its learned theorem is
    used in a completed proof.
    """
    row = GeneratorStatsRow(graph)()
    graph._replace_context(generator_metrics=M.Pair(BumpGeneratorStats(row, slot_label)(), EmptyList))
    return graph.generator_metrics


def update_generator_metrics(graph, gen_label):
    """Keep one metrics row present for this generator label."""
    row = GeneratorStatsRow(graph)()
    if IdentityCompare(graph.generator_metrics, M.EmptyList)() is M.truth_value:
        graph._replace_context(generator_metrics=M.Pair(row, EmptyList))
    return graph.generator_metrics


def get_research_attempts(graph):
    """The attempted-rule chain recorded by search for this session."""
    return Ctx.ContextResearchAttempts(graph.context)()


def set_last_attempts(graph, attempts):
    """Publish the attempt chain as the current residuals."""
    graph._replace_context(last_residuals=attempts, research_residuals=attempts)
    return attempts


# ---------------------------------------------------------------------------
# Genuine failed-rule evidence.
#
# A dependency may be characterized only from a partial match of an
# operational rule: the substitution, the premises that matched, the facts
# that matched them, and the one concrete premise that failed after
# substitution. A rule none of whose premises matched contributes nothing,
# and a stall with no partial match is reported as uncharacterized.
# ---------------------------------------------------------------------------


class HeadsCompatible(Edge):
    """Cheap reject before an expensive Match.

    When both terms carry atom heads (a pair's head atom, or the atom
    itself) and the heads differ structurally, no match is possible --
    a variable head is a pair (VarTag ...) and passes through. This
    gate is what makes attempts affordable against a large library
    whose rule terms can be enormous: the walk is skipped unless the
    heads agree.
    """

    def __init__(self, left, right):
        self.result = M.truth_value
        left_head = left
        if M.IsPair(left)() is M.truth_value:
            left_head = Head(left)()
        right_head = right
        if M.IsPair(right)() is M.truth_value:
            right_head = Head(right)()
        if M.IsPair(left_head)() is M.false_value:
            if M.IsPair(right_head)() is M.false_value:
                if IdentityCompare(left_head, M.VarTag)() is M.false_value:
                    if IdentityCompare(right_head, M.VarTag)() is M.false_value:
                        if M.Compare(left_head, right_head)() is M.false_value:
                            self.result = M.false_value
        super().__init__(inputs=M.Pair(left, M.Pair(right, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PartialPremiseMatch(Edge):
    """The deepest genuine partial match of one rule's premises over facts.

    Returns EmptyList when no premise matched at all -- that is not a
    partial match, and it must not manufacture a request. Otherwise returns

        Pair(bindings,
             Pair(matched,             # Pair(premise instance, Pair(fact, EmptyList)) entries
                  Pair(unmatched,      # the concrete premise that failed, after substitution
                       EmptyList)))

    where an empty `unmatched` means every premise matched (the rule was
    blocked elsewhere), which also never becomes a request.
    """

    def __init__(self, premises, facts, seed=None, seeded=None):
        if seed is None:
            seed = EmptyList
        if seeded is None:
            seeded = M.false_value
        self.facts = facts
        best = self._best(premises, seed, EmptyList, M.Zero, EmptyList)
        depth = Head(best)()
        payload = Tail(best)()
        zero_matched = M.NatEq(depth, M.Zero, M.AllConstructors)()
        unmatched = Head(Tail(Tail(payload)())())()
        # The evidence gate. Unseeded, at least one premise must have
        # matched a fact -- otherwise nothing distinguishes this rule
        # from any other and recording it would manufacture a request.
        # Goal-seeded, the conclusion unified with the goal: that
        # unification is the foothold, and a single-premise rule blocked
        # on its only premise still names a concrete goal-grounded
        # obligation.
        no_foothold = zero_matched
        if IdentityCompare(seeded, M.truth_value)() is M.truth_value:
            no_foothold = M.false_value
        if IdentityCompare(no_foothold, M.truth_value)() is M.truth_value:
            self.result = EmptyList
        elif IdentityCompare(unmatched, EmptyList)() is M.truth_value:
            self.result = EmptyList
        else:
            self.result = payload
        super().__init__(inputs=M.Pair(premises, M.Pair(facts, EmptyList)), results=self.result)

    def _satisfiable(self, term):
        """True when some fact still matches this concrete premise."""
        remaining = self.facts
        found = M.false_value
        while IdentityCompare(remaining, EmptyList)() is M.false_value:
            match = M.Match(term, Head(remaining)())()
            if IdentityCompare(Head(match)(), M.truth_value)() is M.truth_value:
                found = M.truth_value
                remaining = EmptyList
            else:
                remaining = Tail(remaining)()
        return found

    def _sentinel(self):
        # A complete instantiation already fired -- its conclusion is in
        # the facts -- and a skipped premise the facts still satisfy is
        # not missing. Neither is a residual; both rank below any
        # genuine candidate and are rejected at the top level.
        return M.Pair(M.Zero, M.Pair(EmptyList, M.Pair(EmptyList, M.Pair(EmptyList, EmptyList))))

    def _candidate(self, depth, bindings, matched_rev, skipped):
        # The skipped premise is instantiated under the FINAL bindings of
        # this assignment, so matches made after the skip still ground it:
        # Coprime(?a,?b) skipped before a matched SquareSum(?a,?b,?c)
        # reports as the concrete Coprime(3,4), never a schematic hole.
        if IdentityCompare(skipped, EmptyList)() is M.truth_value:
            return self._sentinel()
        unmatched = ApplyBindings(skipped, bindings)()
        if self._satisfiable(unmatched) is M.truth_value:
            return self._sentinel()
        return M.Pair(
            depth,
            M.Pair(bindings, M.Pair(M.Reverse(matched_rev)(), M.Pair(unmatched, EmptyList))),
        )

    def _deeper(self, left, right):
        left_depth = Head(left)()
        right_depth = Head(right)()
        if M.NatLess(left_depth, right_depth, M.AllConstructors)() is M.truth_value:
            return right
        return left

    def _best(self, premises, bindings, matched_rev, depth, skipped):
        if IdentityCompare(premises, EmptyList)() is M.truth_value:
            return self._candidate(depth, bindings, matched_rev, skipped)
        premise = Head(premises)()
        rest = Tail(premises)()
        # Skip branch: a premise may fail while later premises still match
        # facts. The first skipped premise is the one the record names.
        next_skipped = skipped
        if IdentityCompare(next_skipped, EmptyList)() is M.truth_value:
            next_skipped = premise
        best = self._best(rest, bindings, matched_rev, depth, next_skipped)
        return self._try_facts(
            self.facts, premise, rest, bindings, matched_rev, depth, skipped, best
        )

    def _try_facts(self, remaining, premise, rest, bindings, matched_rev, depth, skipped, best):
        if IdentityCompare(remaining, EmptyList)() is M.truth_value:
            return best
        fact = Head(remaining)()
        if HeadsCompatible(premise, fact)() is M.false_value:
            return self._try_facts(
                Tail(remaining)(), premise, rest, bindings, matched_rev, depth, skipped, best
            )
        match = M.Match(premise, fact)()
        flag = Head(match)()
        if IdentityCompare(flag, M.truth_value)() is M.truth_value:
            merged = M.MergeBindings(bindings, Tail(match)())()
            merged_flag = Head(merged)()
            if IdentityCompare(merged_flag, M.truth_value)() is M.truth_value:
                new_bindings = Tail(merged)()
                entry = M.Pair(ApplyBindings(premise, new_bindings)(), M.Pair(fact, EmptyList))
                next_depth = Head(M.Succ(depth, M.AllConstructors)())()
                sub = self._best(rest, new_bindings, M.Pair(entry, matched_rev), next_depth, skipped)
                best = self._deeper(best, sub)
        return self._try_facts(
            Tail(remaining)(), premise, rest, bindings, matched_rev, depth, skipped, best
        )

    def __call__(self):
        return self.result


EVAL_EQ = M.Char("eq")
EVAL_TIMES = M.Char("times")
EVAL_PLUS = M.Char("plus")
EVAL_MINUS = M.Char("minus")
EVAL_POW = M.Char("pow")
EVAL_DIVIDES = M.Char("divides")
EVAL_COPRIME = M.Char("coprime")
EVAL_ODD = M.Char("odd")
EVAL_EVEN = M.Char("even")
EVAL_GREATER = M.Char("greater")
EVAL_GEQ = M.Char("geq")
EVAL_LESS = M.Char("less")
EVAL_LEQ = M.Char("leq")


class EvaluateGround(Edge):
    """Decide a fully ground arithmetic predicate, or decline.

    truth_value when the predicate holds, false_value when it is
    refuted, EmptyList when the term is not ground arithmetic this
    evaluator understands. The arithmetic itself is host-boundary
    computation over numeral symbols -- the same boundary the numeral
    parser already crosses -- and every discharge is provenance-tagged
    by the caller. Nothing here inspects goal shape: a predicate is
    evaluable or it is not, uniformly.
    """

    def __init__(self, term):
        self.result = self._decide(term)
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def _symbol(self, atom):
        try:
            value = atom()
        except Exception:
            return None
        if value is None:
            return None
        return str(value)

    def _number(self, term):
        if M.IsPair(term)() is M.truth_value:
            head = Head(term)()
            args = Tail(term)()
            if M.IsPair(args)() is M.false_value:
                return None
            left = self._number(Head(args)())
            rest = Tail(args)()
            if M.IsPair(rest)() is M.false_value:
                return None
            right = self._number(Head(rest)())
            if left is None or right is None:
                return None
            if M.Compare(head, EVAL_TIMES)() is M.truth_value:
                return left * right
            if M.Compare(head, EVAL_PLUS)() is M.truth_value:
                return left + right
            if M.Compare(head, EVAL_MINUS)() is M.truth_value:
                return left - right
            if M.Compare(head, EVAL_POW)() is M.truth_value:
                if right < 0 or right > 64:
                    return None
                return left ** right
            return None
        text = self._symbol(term)
        if text is None or not text.isdigit():
            return None
        return int(text)

    def _gcd(self, left, right):
        while right != 0:
            left, right = right, left % right
        return left

    def _decide(self, term):
        if M.IsPair(term)() is M.false_value:
            return EmptyList
        head = Head(term)()
        args = Tail(term)()
        if M.IsPair(args)() is M.false_value:
            return EmptyList
        first = Head(args)()
        rest = Tail(args)()
        second = None
        if M.IsPair(rest)() is M.truth_value:
            second = Head(rest)()
        if M.Compare(head, EVAL_EQ)() is M.truth_value and second is not None:
            left = self._number(first)
            right = self._number(second)
            if left is None or right is None:
                return EmptyList
            return M.truth_value if left == right else M.false_value
        if M.Compare(head, EVAL_DIVIDES)() is M.truth_value and second is not None:
            k = self._number(first)
            n = self._number(second)
            if k is None or n is None or k == 0:
                return EmptyList
            return M.truth_value if n % k == 0 else M.false_value
        if M.Compare(head, EVAL_COPRIME)() is M.truth_value and second is not None:
            a = self._number(first)
            b = self._number(second)
            if a is None or b is None:
                return EmptyList
            return M.truth_value if self._gcd(a, b) == 1 else M.false_value
        if M.Compare(head, EVAL_ODD)() is M.truth_value:
            n = self._number(first)
            if n is None:
                return EmptyList
            return M.truth_value if n % 2 == 1 else M.false_value
        if M.Compare(head, EVAL_EVEN)() is M.truth_value:
            n = self._number(first)
            if n is None:
                return EmptyList
            return M.truth_value if n % 2 == 0 else M.false_value
        comparisons = (
            (EVAL_GREATER, "gt"), (EVAL_GEQ, "ge"), (EVAL_LESS, "lt"), (EVAL_LEQ, "le"),
        )
        for label, mode in comparisons:
            if M.Compare(head, label)() is M.truth_value and second is not None:
                a = self._number(first)
                b = self._number(second)
                if a is None or b is None:
                    return EmptyList
                if mode == "gt":
                    return M.truth_value if a > b else M.false_value
                if mode == "ge":
                    return M.truth_value if a >= b else M.false_value
                if mode == "lt":
                    return M.truth_value if a < b else M.false_value
                return M.truth_value if a <= b else M.false_value
        return EmptyList

    def __call__(self):
        return self.result


class RulePartialMatch(Edge):
    """The genuine partial match of one rule, goal-seeded when possible.

    Pure: no recording. Returns the partial record or EmptyList, exactly
    as RecordPremisePartialMatch computes it.
    """

    def __init__(self, rule, facts, goal_facts):
        from .proof import RulePremises, RuleReplacement

        premises = RulePremises(rule)()
        conclusion = RuleReplacement(rule)()
        partial = EmptyList
        remaining_goals = goal_facts
        if IsVarPatternTerm(conclusion)() is M.truth_value:
            remaining_goals = EmptyList
        while IdentityCompare(remaining_goals, EmptyList)() is M.false_value:
            if HeadsCompatible(conclusion, Head(remaining_goals)())() is M.false_value:
                remaining_goals = Tail(remaining_goals)()
                continue
            goal_match = M.Match(conclusion, Head(remaining_goals)())()
            if IdentityCompare(Head(goal_match)(), M.truth_value)() is M.truth_value:
                seeded = PartialPremiseMatch(
                    premises, facts, Tail(goal_match)(), M.truth_value
                )()
                if IdentityCompare(seeded, EmptyList)() is M.false_value:
                    partial = seeded
                    remaining_goals = EmptyList
                    continue
            remaining_goals = Tail(remaining_goals)()
        if IdentityCompare(partial, EmptyList)() is M.truth_value:
            partial = PartialPremiseMatch(premises, facts)()
        self.result = partial
        super().__init__(inputs=M.Pair(rule, EmptyList), results=self.result)

    def __call__(self):
        return self.result


def evaluated_search(start_facts, goal_facts, rules, fuel):
    """Bounded search interleaved with ground evaluation of residuals.

    Loop: search; if open, evaluate the ground evaluable obligations --
    goal facts and unmatched premises. True ones become facts and the
    search reruns; false ones are collected as refutations and never
    requested. Ends at closure, refuted goal, or evaluation fixpoint.

    Returns Pair(outcome,
                 Pair(facts-with-evaluated,
                      Pair(evaluated-true chain,
                           Pair(refuted chain, Pair(goal-refuted flag, EmptyList)))))
    """
    facts = start_facts
    evaluated = EmptyList
    refuted = EmptyList
    goal_refuted = M.false_value
    rounds = 0
    outcome = BoundedForwardSearch(facts, goal_facts, rules, fuel)()
    while rounds < 8:
        rounds += 1
        if ForwardSearchClosed(outcome)() is M.truth_value:
            break
        progressed = False
        remaining_goals = goal_facts
        while IdentityCompare(remaining_goals, EmptyList)() is M.false_value:
            goal_fact = Head(remaining_goals)()
            remaining_goals = Tail(remaining_goals)()
            verdict = EvaluateGround(goal_fact)()
            if verdict is M.truth_value:
                from .proof import FactsCover
                if FactsCover(M.Pair(goal_fact, EmptyList), facts)() is M.false_value:
                    facts = M.Pair(goal_fact, facts)
                    evaluated = M.Pair(goal_fact, evaluated)
                    progressed = True
            elif verdict is M.false_value:
                refuted = M.Pair(goal_fact, refuted)
                goal_refuted = M.truth_value
        if goal_refuted is M.truth_value:
            break
        final_facts = ForwardSearchFacts(outcome)()
        remaining_rules = rules
        while IdentityCompare(remaining_rules, EmptyList)() is M.false_value:
            rule = Head(remaining_rules)()
            remaining_rules = Tail(remaining_rules)()
            partial = RulePartialMatch(rule, final_facts, goal_facts)()
            if IdentityCompare(partial, EmptyList)() is M.truth_value:
                continue
            unmatched = Head(Tail(Tail(partial)())())()
            verdict = EvaluateGround(unmatched)()
            if verdict is M.truth_value:
                from .proof import FactsCover
                if FactsCover(M.Pair(unmatched, EmptyList), facts)() is M.false_value:
                    facts = M.Pair(unmatched, facts)
                    evaluated = M.Pair(unmatched, evaluated)
                    progressed = True
            elif verdict is M.false_value:
                already = ObligationDifference(M.Pair(unmatched, EmptyList), refuted)()
                if IdentityCompare(already, EmptyList)() is M.false_value:
                    refuted = M.Pair(unmatched, refuted)
        if not progressed:
            break
        outcome = BoundedForwardSearch(facts, goal_facts, rules, fuel)()
    return M.Pair(
        outcome,
        M.Pair(facts, M.Pair(evaluated, M.Pair(refuted, M.Pair(goal_refuted, EmptyList)))),
    )


class RecordPremisePartialMatch(Edge):
    """Record one genuine partial match as an AttemptedRule, or nothing.

    Called by the search engine when a knowledge rule produced zero
    successors in research mode. The record carries the rule itself, its
    declared origin, the substitution built from the premises that did
    match, those matched premise/fact pairs, and the one concrete premise
    that failed. The failure kind is MissingPremiseFailure.
    """

    def __init__(self, graph, rule, facts, goal_facts=None):
        from .proof import RulePremises, RuleReplacement

        if goal_facts is None:
            goal_facts = EmptyList
        self.result = EmptyList
        premises = RulePremises(rule)()
        conclusion = RuleReplacement(rule)()
        # The goal-to-rule substitution: matching the rule's conclusion
        # against a goal fact grounds the record's variables the way the
        # rule would have to fire to serve this goal. Without it a rule
        # whose premises share no variables with the facts reports a
        # schematic hole instead of the concrete missing premise.
        partial = EmptyList
        remaining_goals = goal_facts
        if IsVarPatternTerm(conclusion)() is M.truth_value:
            # A bare-variable conclusion unifies with every goal and
            # discriminates nothing; it earns no foothold. Without this
            # gate a large library would turn the request list into a
            # menu generated by the matcher.
            remaining_goals = EmptyList
        while IdentityCompare(remaining_goals, EmptyList)() is M.false_value:
            if HeadsCompatible(conclusion, Head(remaining_goals)())() is M.false_value:
                remaining_goals = Tail(remaining_goals)()
                continue
            goal_match = M.Match(conclusion, Head(remaining_goals)())()
            if IdentityCompare(Head(goal_match)(), M.truth_value)() is M.truth_value:
                seeded = PartialPremiseMatch(
                    premises, facts, Tail(goal_match)(), M.truth_value
                )()
                if IdentityCompare(seeded, EmptyList)() is M.false_value:
                    partial = seeded
                    remaining_goals = EmptyList
                    continue
            remaining_goals = Tail(remaining_goals)()
        if IdentityCompare(partial, EmptyList)() is M.truth_value:
            partial = PartialPremiseMatch(premises, facts)()
        if IdentityCompare(partial, EmptyList)() is M.false_value:
            bindings = Head(partial)()
            matched = Head(Tail(partial)())()
            unmatched = Head(Tail(Tail(partial)())())()
            if IdentityCompare(EvaluateGround(unmatched)(), EmptyList)() is M.false_value:
                # A decidable ground premise is never a request: true ones
                # were discharged by evaluation, false ones refuted. If one
                # reaches this point undischarged, the evaluator loop and
                # the recorder disagree -- suppressing it here keeps the
                # request channel clean either way.
                super().__init__(inputs=M.Pair(rule, EmptyList), results=self.result)
                return
            origin = graph.rule_origin(rule)
            attempt = AttemptedRule(
                rule, origin, bindings, matched, unmatched, Lmod.MissingPremiseFailureLabel
            )()
            graph.record_research_attempt(attempt)
            self.result = attempt
        super().__init__(inputs=M.Pair(rule, EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# The bounded fork.
#
# Counterfactual evidence and retry measurement rerun bounded search from
# the originating stall state: same facts, same fuel, rules with or without
# the compiled taught theorem. The forward search below is that rerun. It
# fires real rules through the same premise-matching primitives the prover
# uses, counts every application attempt as cost, and records every firing
# with its substitution. It touches no graph context, so a fork is never
# persisted.
# ---------------------------------------------------------------------------


class BoundedForwardSearch(Edge):
    """Saturate facts under rules within a firing budget.

    Result:
        Pair(closed, Pair(cost, Pair(fired, Pair(final facts, EmptyList))))

    `fired` entries are Pair(rule, Pair(bindings, EmptyList)), newest first.
    `cost` counts rule application attempts. `fuel` bounds FIRINGS, not
    rounds: a generative rule that feeds its own conclusions back would
    otherwise blow up inside a single round, as the divisibility session
    that forced this rewrite demonstrated. The goal is checked after
    every firing, so a budget large enough to reach the goal closes even
    when junk derivations compete for it.
    """

    def __init__(self, facts, goal_facts, rules, fuel):
        self.goal_facts = goal_facts
        self.rules = rules
        self.result = self._run(facts, EmptyList, EmptyList, fuel)
        super().__init__(
            inputs=M.Pair(facts, M.Pair(goal_facts, M.Pair(rules, M.Pair(fuel, EmptyList)))),
            results=self.result,
        )

    def _finish(self, closed, cost, fired_rev, facts):
        return M.Pair(closed, M.Pair(cost, M.Pair(M.Reverse(fired_rev)(), M.Pair(facts, EmptyList))))

    def _closed(self, facts):
        from .proof import FactsCover

        return FactsCover(self.goal_facts, facts)()

    def _run(self, facts, fired_rev, cost, fuel):
        if self._closed(facts) is M.truth_value:
            return self._finish(M.truth_value, cost, fired_rev, facts)
        if IdentityCompare(fuel, EmptyList)() is M.truth_value:
            return self._finish(M.false_value, cost, fired_rev, facts)
        goal_result = self._goal_pass(self.rules, facts, fired_rev, cost, M.false_value, fuel)
        facts = Head(goal_result)()
        fired_rev = Head(Tail(goal_result)())()
        cost = Head(Tail(Tail(goal_result)())())()
        goal_progressed = Head(Tail(Tail(Tail(goal_result)())())())()
        fuel = Head(Tail(Tail(Tail(Tail(goal_result)())())())())()
        if self._closed(facts) is M.truth_value:
            return self._finish(M.truth_value, cost, fired_rev, facts)
        round_result = self._round(self.rules, facts, fired_rev, cost, goal_progressed, fuel)
        new_facts = Head(round_result)()
        new_fired = Head(Tail(round_result)())()
        new_cost = Head(Tail(Tail(round_result)())())()
        progressed = Head(Tail(Tail(Tail(round_result)())())())()
        new_fuel = Head(Tail(Tail(Tail(Tail(round_result)())())())())()
        if self._closed(new_facts) is M.truth_value:
            return self._finish(M.truth_value, new_cost, new_fired, new_facts)
        if IdentityCompare(progressed, M.false_value)() is M.truth_value:
            return self._finish(M.false_value, new_cost, new_fired, new_facts)
        return self._run(new_facts, new_fired, new_cost, new_fuel)

    def _goal_pass(self, rules, facts, fired_rev, cost, progressed, fuel):
        """Goal-directed firing: the backward half of the bounded search.

        A rule whose conclusion introduces variables its premises never
        bind -- (eq (pow ?t ?n) (pow (pow ?t ?k) ?d)) with ?t free --
        can never fire forward: asserting a schematic fact is refused.
        It fires toward a goal instead: when the conclusion unifies with
        a goal fact and the premises are jointly satisfiable under that
        seed, the goal instance itself is derived. The exponent session
        that could not close (eq (pow t 6) (pow (pow t 2) 3)) after
        being taught (eq 6 (times 2 3)) forced this pass.
        """
        from .proof import FactsCover, JoinPremises, RulePremises, RuleReplacement

        if IdentityCompare(rules, EmptyList)() is M.truth_value:
            return M.Pair(facts, M.Pair(fired_rev, M.Pair(cost, M.Pair(progressed, M.Pair(fuel, EmptyList)))))
        if IdentityCompare(fuel, EmptyList)() is M.truth_value:
            return M.Pair(facts, M.Pair(fired_rev, M.Pair(cost, M.Pair(progressed, M.Pair(fuel, EmptyList)))))
        rule = Head(rules)()
        cost = M.Pair(M.truth_value, cost)
        conclusion = RuleReplacement(rule)()
        premises = RulePremises(rule)()
        remaining_goals = self.goal_facts
        while IdentityCompare(remaining_goals, EmptyList)() is M.false_value:
            goal_fact = Head(remaining_goals)()
            remaining_goals = Tail(remaining_goals)()
            already = FactsCover(M.Pair(goal_fact, EmptyList), facts)()
            if IdentityCompare(already, M.truth_value)() is M.truth_value:
                continue
            if HeadsCompatible(conclusion, goal_fact)() is M.false_value:
                continue
            goal_match = M.Match(conclusion, goal_fact)()
            if IdentityCompare(Head(goal_match)(), M.truth_value)() is M.false_value:
                continue
            bindings_list = JoinPremises(premises, facts, Tail(goal_match)())()
            if IdentityCompare(bindings_list, EmptyList)() is M.truth_value:
                continue
            facts = M.Pair(goal_fact, facts)
            fired_rev = M.Pair(M.Pair(rule, M.Pair(Head(bindings_list)(), EmptyList)), fired_rev)
            fuel = Tail(fuel)()
            progressed = M.truth_value
            if IdentityCompare(fuel, EmptyList)() is M.truth_value:
                remaining_goals = EmptyList
        return self._goal_pass(Tail(rules)(), facts, fired_rev, cost, progressed, fuel)

    def _round(self, rules, facts, fired_rev, cost, progressed, fuel):
        from .proof import JoinPremises, RulePremises

        if IdentityCompare(rules, EmptyList)() is M.truth_value:
            return M.Pair(facts, M.Pair(fired_rev, M.Pair(cost, M.Pair(progressed, M.Pair(fuel, EmptyList)))))
        if IdentityCompare(fuel, EmptyList)() is M.truth_value:
            return M.Pair(facts, M.Pair(fired_rev, M.Pair(cost, M.Pair(progressed, M.Pair(fuel, EmptyList)))))
        if self._closed(facts) is M.truth_value:
            return M.Pair(facts, M.Pair(fired_rev, M.Pair(cost, M.Pair(progressed, M.Pair(fuel, EmptyList)))))
        rule = Head(rules)()
        cost = M.Pair(M.truth_value, cost)
        premises = RulePremises(rule)()
        bindings_list = JoinPremises(premises, facts, EmptyList)()
        applied = self._apply_all(rule, bindings_list, facts, fired_rev, progressed, fuel)
        facts = Head(applied)()
        fired_rev = Head(Tail(applied)())()
        progressed = Head(Tail(Tail(applied)())())()
        fuel = Head(Tail(Tail(Tail(applied)())())())()
        return self._round(Tail(rules)(), facts, fired_rev, cost, progressed, fuel)

    def _apply_all(self, rule, bindings_list, facts, fired_rev, progressed, fuel):
        from .proof import FactsCover, RuleReplacement

        if IdentityCompare(bindings_list, EmptyList)() is M.truth_value:
            return M.Pair(facts, M.Pair(fired_rev, M.Pair(progressed, M.Pair(fuel, EmptyList))))
        if IdentityCompare(fuel, EmptyList)() is M.truth_value:
            return M.Pair(facts, M.Pair(fired_rev, M.Pair(progressed, M.Pair(fuel, EmptyList))))
        if self._closed(facts) is M.truth_value:
            return M.Pair(facts, M.Pair(fired_rev, M.Pair(progressed, M.Pair(fuel, EmptyList))))
        bindings = Head(bindings_list)()
        rest = Tail(bindings_list)()
        conclusion = ApplyBindings(RuleReplacement(rule)(), bindings)()
        if ContainsVarPattern(conclusion)() is M.truth_value:
            return self._apply_all(rule, rest, facts, fired_rev, progressed, fuel)
        already = FactsCover(M.Pair(conclusion, EmptyList), facts)()
        if IdentityCompare(already, M.truth_value)() is M.truth_value:
            return self._apply_all(rule, rest, facts, fired_rev, progressed, fuel)
        facts = M.Pair(conclusion, facts)
        fired_rev = M.Pair(M.Pair(rule, M.Pair(bindings, EmptyList)), fired_rev)
        fuel = Tail(fuel)()
        return self._apply_all(rule, rest, facts, fired_rev, M.truth_value, fuel)


class ContainsVarPattern(Edge):
    """True when any subterm is a matcher variable."""

    def __init__(self, term):
        self.result = self._walk(term)
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def _walk(self, term):
        if IdentityCompare(term, EmptyList)() is M.truth_value:
            return M.false_value
        if IsVarPatternTerm(term)() is M.truth_value:
            return M.truth_value
        if M.IsPair(term)() is M.truth_value:
            if self._walk(Head(term)()) is M.truth_value:
                return M.truth_value
            return self._walk(Tail(term)())
        return M.false_value

    def __call__(self):
        return self.result


class ForwardSearchClosed(Edge):
    def __init__(self, outcome):
        self.result = Head(outcome)()
        super().__init__(inputs=M.Pair(outcome, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ForwardSearchCost(Edge):
    def __init__(self, outcome):
        self.result = Head(Tail(outcome)())()
        super().__init__(inputs=M.Pair(outcome, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ForwardSearchFired(Edge):
    def __init__(self, outcome):
        self.result = Head(Tail(Tail(outcome)())())()
        super().__init__(inputs=M.Pair(outcome, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ForwardSearchFacts(Edge):
    def __init__(self, outcome):
        self.result = Head(Tail(Tail(Tail(outcome)())())())()
        super().__init__(inputs=M.Pair(outcome, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleFiredIn(Edge):
    """True when this rule (by identity) appears in a fired chain."""

    def __init__(self, fired, rule):
        self.result = self._walk(fired, rule)
        super().__init__(inputs=M.Pair(fired, M.Pair(rule, EmptyList)), results=self.result)

    def _walk(self, fired, rule):
        if IdentityCompare(fired, EmptyList)() is M.truth_value:
            return M.false_value
        entry = Head(fired)()
        if IdentityCompare(Head(entry)(), rule)() is M.truth_value:
            return M.truth_value
        return self._walk(Tail(fired)(), rule)

    def __call__(self):
        return self.result


class FiredRuleDifference(Edge):
    """Firings present after and absent before, excluding the taught rule.

    These are the *existing* rules the taught theorem newly enabled -- the
    only admissible sense of `newly enabled firings`. The taught rule's own
    firing proves nothing and is excluded by identity.
    """

    def __init__(self, fired_after, fired_before, taught_rule):
        self.fired_before = fired_before
        self.taught_rule = taught_rule
        self.result = self._walk(fired_after)
        super().__init__(inputs=M.Pair(fired_after, M.Pair(fired_before, EmptyList)), results=self.result)

    def _walk(self, fired):
        if IdentityCompare(fired, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(fired)()
        rest = Tail(fired)()
        rule = Head(entry)()
        if IdentityCompare(rule, self.taught_rule)() is M.truth_value:
            return self._walk(rest)
        if RuleFiredIn(self.fired_before, rule)() is M.truth_value:
            return self._walk(rest)
        return M.Pair(entry, self._walk(rest))

    def __call__(self):
        return self.result


class ResidualObligations(Edge):
    """Alpha-normalized missing premises over a fact state, one per rule.

    A rule contributes only through a genuine partial match; rules with no
    matched premise contribute nothing.
    """

    def __init__(self, facts, rules):
        self.facts = facts
        self.result = self._walk(rules)
        super().__init__(inputs=M.Pair(facts, M.Pair(rules, EmptyList)), results=self.result)

    def _walk(self, rules):
        from .proof import RulePremises

        if IdentityCompare(rules, EmptyList)() is M.truth_value:
            return EmptyList
        rule = Head(rules)()
        rest = Tail(rules)()
        partial = PartialPremiseMatch(RulePremises(rule)(), self.facts)()
        if IdentityCompare(partial, EmptyList)() is M.truth_value:
            return self._walk(rest)
        bindings = Head(partial)()
        unmatched = Head(Tail(Tail(partial)())())()
        return M.Pair(AlphaNormalized(unmatched, bindings)(), self._walk(rest))

    def __call__(self):
        return self.result


class ObligationDifference(Edge):
    """Members of `left` with no structural equal in `right`."""

    def __init__(self, left, right):
        self.right = right
        self.result = self._walk(left)
        super().__init__(inputs=M.Pair(left, M.Pair(right, EmptyList)), results=self.result)

    def _member(self, chain, term):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return M.false_value
        if M.Compare(Head(chain)(), term)() is M.truth_value:
            return M.truth_value
        return self._member(Tail(chain)(), term)

    def _walk(self, left):
        if IdentityCompare(left, EmptyList)() is M.truth_value:
            return EmptyList
        term = Head(left)()
        rest = Tail(left)()
        if self._member(self.right, term) is M.truth_value:
            return self._walk(rest)
        return M.Pair(term, self._walk(rest))

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Formal rules and live teaching.
#
# A taught theorem is a formal term that compiles into an executable rule.
# Storing prose adds no mathematical capability, so prose is never stored
# as content: renderers may print it, the graph keeps terms.
# ---------------------------------------------------------------------------


class FormalRule(Edge):
    """Pair(FormalRuleLabel, Pair(premises chain, Pair(conclusion, EmptyList)))."""

    def __init__(self, premises, conclusion):
        self.result = M.Pair(
            Lmod.FormalRuleLabel, M.Pair(premises, M.Pair(conclusion, EmptyList))
        )
        super().__init__(inputs=M.Pair(premises, M.Pair(conclusion, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsFormalRule(Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if IdentityCompare(Head(term)(), Lmod.FormalRuleLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FormalRulePremises(Edge):
    def __init__(self, term):
        self.result = Head(Tail(term)())()
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FormalRuleConclusion(Edge):
    def __init__(self, term):
        self.result = Head(Tail(Tail(term)())())()
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


def compile_formal_rule(formal_term):
    """An executable rule from a formal rule term. This is the only door.

    Reload takes the same door: a checkpointed formal term is recompiled,
    so every reused certificate is reconstructed rather than replayed.
    """
    from .proof import MultiRule

    premises = FormalRulePremises(formal_term)()
    conclusion = FormalRuleConclusion(formal_term)()
    return MultiRule(premises, conclusion)()


class FormalRuleAlpha(Edge):
    """The alpha-normalized shape of a formal rule, for episodes and policies."""

    def __init__(self, formal_term):
        self.result = AlphaNormalized(formal_term, EmptyList)()
        super().__init__(inputs=M.Pair(formal_term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BindingValueMarks(Edge):
    """Self-keyed marks for every value a binding chain carries.

    AlphaNormalizeTerm renames any subterm its substitution marks; keying
    each bound value by itself marks exactly the objects the match was
    about, atoms and compounds alike.
    """

    def __init__(self, bindings):
        self.result = self._walk(bindings)
        super().__init__(inputs=M.Pair(bindings, EmptyList), results=self.result)

    def _walk(self, bindings):
        if IdentityCompare(bindings, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(bindings)()
        value = BindingValue(entry)()
        return M.Pair(M.Pair(value, M.Pair(value, EmptyList)), self._walk(Tail(bindings)()))

    def __call__(self):
        return self.result


class EpisodeFeatures(Edge):
    """Residual and rule shape normalized together, so they co-refer.

    The taught rule's conclusion is matched against the residual it
    discharged; the rule is instantiated under that match; residual and
    instance are alpha-normalized in one pass with the matched objects
    marked. The object the missing premise was about becomes one shared
    placeholder in both -- which is what lets a learned policy later
    instantiate a held-out constant into its predicted rule.

    Result: Pair(residual features, Pair(rule shape, EmptyList)). When
    the conclusion does not match the residual, the features fall back
    to the unlinked forms.
    """

    def __init__(self, formal_term, residual):
        match = M.Match(FormalRuleConclusion(formal_term)(), residual)()
        if IdentityCompare(Head(match)(), M.truth_value)() is M.truth_value:
            bindings = Tail(match)()
            instance = ApplyBindings(formal_term, bindings)()
            marks = BindingValueMarks(bindings)()
            combined = AlphaNormalized(M.Pair(residual, instance), marks)()
            self.result = M.Pair(Head(combined)(), M.Pair(Tail(combined)(), EmptyList))
        else:
            self.result = M.Pair(
                AlphaNormalized(residual, EmptyList)(),
                M.Pair(FormalRuleAlpha(formal_term)(), EmptyList),
            )
        super().__init__(inputs=M.Pair(formal_term, M.Pair(residual, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PremiseRestatesGoal(Edge):
    """True when any premise contains the parent goal: the proof would be circular."""

    def __init__(self, premises, parent_goal):
        self.result = self._walk(premises, parent_goal)
        super().__init__(inputs=M.Pair(premises, M.Pair(parent_goal, EmptyList)), results=self.result)

    def _walk(self, premises, parent_goal):
        if IdentityCompare(premises, EmptyList)() is M.truth_value:
            return M.false_value
        if RestatesGoal(Head(premises)(), parent_goal)() is M.truth_value:
            return M.truth_value
        return self._walk(Tail(premises)(), parent_goal)

    def __call__(self):
        return self.result


def validate_taught_rule(formal_term, parent_goal_fact):
    """Reject circular and vacuous taught rules.

    An empty-premise rule concluding the parent goal is the goal restated;
    a rule using the parent goal as a premise assumes what it must prove.
    Returns truth_value when the rule is admissible.
    """
    if IsFormalRule(formal_term)() is M.false_value:
        return M.false_value
    premises = FormalRulePremises(formal_term)()
    conclusion = FormalRuleConclusion(formal_term)()
    if IdentityCompare(parent_goal_fact, EmptyList)() is M.false_value:
        if PremiseRestatesGoal(premises, parent_goal_fact)() is M.truth_value:
            return M.false_value
        if IdentityCompare(premises, EmptyList)() is M.truth_value:
            if M.Compare(conclusion, parent_goal_fact)() is M.truth_value:
                return M.false_value
    return M.truth_value


def teach_trusted_theorem(graph, formal_term):
    """Store a human-supplied theorem with its provenance and compile it.

    The theorem is HUMAN_SUPPLIED_TRUSTED_THEOREM: not invented, not proved
    here. Returns the compiled rule, tagged with its origin.
    """
    graph.add_provenance(formal_term, Lmod.HumanSuppliedTrustedTheoremLabel)
    if IsFormalRule(formal_term)() is M.truth_value:
        rule = compile_formal_rule(formal_term)
        graph.tag_rule_origin(rule, Lmod.HumanSuppliedTrustedTheoremLabel)
        return rule
    return EmptyList


def teach_law(graph, formal_term):
    """A live-taught law: same trusted-human provenance, same compilation."""
    return teach_trusted_theorem(graph, formal_term)


def teach_strategy_prior(graph, formal_term):
    """Quarantine lane for strategy skeletons.

    A rule whose purpose is strategic is stored as a HUMAN-SUPPLIED
    STRATEGY PRIOR. Requests compiled from its partial matches inherit that
    provenance and are displayed as suggestions from a preinstalled prior,
    never as machine-discovered dependencies.
    """
    graph.add_provenance(formal_term, Lmod.HumanSuppliedStrategyPriorLabel)
    if IsFormalRule(formal_term)() is M.truth_value:
        rule = compile_formal_rule(formal_term)
        graph.tag_rule_origin(rule, Lmod.HumanSuppliedStrategyPriorLabel)
        return rule
    return EmptyList


def assume_axiom(graph, fact_term):
    """A domain axiom: allowed knowledge, listed by audit, labeled as such."""
    graph.add_provenance(fact_term, Lmod.DomainAxiomLabel)
    return fact_term


def define_symbolic_object(graph, signature_term):
    """A live-defined symbolic constructor, generically as atoms and pairs.

    No Python class exists for it; its behavior arrives through taught
    laws. The signature is recorded with domain-axiom provenance so audit
    lists it.
    """
    graph.add_provenance(signature_term, Lmod.DomainAxiomLabel)
    return signature_term


class ProvenanceEntriesFor(Edge):
    """All terms in the provenance map carrying one provenance label."""

    def __init__(self, provenance_map, label):
        self.label = label
        self.result = self._walk(provenance_map)
        super().__init__(inputs=M.Pair(provenance_map, M.Pair(label, EmptyList)), results=self.result)

    def _walk(self, chain):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(chain)()
        rest = Tail(chain)()
        if M.IsPair(entry)() is M.truth_value:
            payload = Tail(entry)()
            if M.IsPair(payload)() is M.truth_value:
                if IdentityCompare(Head(payload)(), self.label)() is M.truth_value:
                    return M.Pair(Head(entry)(), self._walk(rest))
        return self._walk(rest)

    def __call__(self):
        return self.result


def axiom_facts(graph):
    """The domain-axiom fact chain, rebuilt from provenance every time."""
    entries = ProvenanceEntriesFor(graph.provenance_map, Lmod.DomainAxiomLabel)()
    return NonRuleTerms(entries)()


class NonRuleTerms(Edge):
    """Entries that are facts rather than formal rules."""

    def __init__(self, entries):
        self.result = self._walk(entries)
        super().__init__(inputs=M.Pair(entries, EmptyList), results=self.result)

    def _walk(self, entries):
        if IdentityCompare(entries, EmptyList)() is M.truth_value:
            return EmptyList
        term = Head(entries)()
        rest = Tail(entries)()
        if IsFormalRule(term)() is M.truth_value:
            return self._walk(rest)
        return M.Pair(term, self._walk(rest))

    def __call__(self):
        return self.result


class TaughtFormalRules(Edge):
    """Formal rule terms taught this session or restored from a checkpoint.

    Restoration recompiles: the checkpoint stores formal terms, and every
    rule object is rebuilt through compile_formal_rule, so nothing replays
    a stale compiled certificate.
    """

    def __init__(self, provenance_map):
        trusted = ProvenanceEntriesFor(provenance_map, Lmod.HumanSuppliedTrustedTheoremLabel)()
        priors = ProvenanceEntriesFor(provenance_map, Lmod.HumanSuppliedStrategyPriorLabel)()
        invented = ProvenanceEntriesFor(provenance_map, Lmod.InventedLemmaLabel)()
        self.result = self._rules(
            trusted, self._rules(priors, self._rules(invented, EmptyList))
        )
        super().__init__(inputs=M.Pair(provenance_map, EmptyList), results=self.result)

    def _rules(self, entries, acc):
        if IdentityCompare(entries, EmptyList)() is M.truth_value:
            return acc
        term = Head(entries)()
        rest = Tail(entries)()
        if IsFormalRule(term)() is M.truth_value:
            return self._rules(rest, M.Pair(term, acc))
        return self._rules(rest, acc)

    def __call__(self):
        return self.result


def rebuild_taught_rules(graph):
    """Recompile and re-tag every checkpointed taught rule.

    Returns Pair(rule, Pair(formal term, EmptyList)) entries, newest last.
    """
    return RecompiledRules(graph, TaughtFormalRules(graph.provenance_map)())()


class RecompiledRules(Edge):
    def __init__(self, graph, formal_terms):
        self.graph = graph
        self.result = self._walk(formal_terms)
        super().__init__(inputs=M.Pair(formal_terms, EmptyList), results=self.result)

    def _origin_for(self, formal_term):
        priors = ProvenanceEntriesFor(self.graph.provenance_map, Lmod.HumanSuppliedStrategyPriorLabel)()
        if self._member(priors, formal_term) is M.truth_value:
            return Lmod.HumanSuppliedStrategyPriorLabel
        invented = ProvenanceEntriesFor(self.graph.provenance_map, Lmod.InventedLemmaLabel)()
        if self._member(invented, formal_term) is M.truth_value:
            return Lmod.InventedLemmaLabel
        return Lmod.HumanSuppliedTrustedTheoremLabel

    def _member(self, chain, term):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return M.false_value
        if IdentityCompare(Head(chain)(), term)() is M.truth_value:
            return M.truth_value
        return self._member(Tail(chain)(), term)

    def _walk(self, terms):
        if IdentityCompare(terms, EmptyList)() is M.truth_value:
            return EmptyList
        formal_term = Head(terms)()
        rule = compile_formal_rule(formal_term)
        self.graph.tag_rule_origin(rule, self._origin_for(formal_term))
        return M.Pair(M.Pair(rule, M.Pair(formal_term, EmptyList)), self._walk(Tail(terms)()))

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Intervention episodes and learned dependency policies.
#
# The machine learns dependency characterization from measured teaching
# episodes, never from preinstalled strategy templates. An episode exists
# only when a taught theorem produced a measured unlock; a policy exists
# only after at least two independent useful episodes anti-unify into a
# shape that still shares structure. Resetting learned memory removes
# both, and with them every policy-based prediction.
# ---------------------------------------------------------------------------


class InterventionEpisode(Edge):
    """One measured live-teaching outcome.

    Pair(InterventionEpisodeLabel,
         Pair(residual features,
              Pair(supplied rule shape,
                   Pair(newly enabled firings,
                        Pair(cost before,
                             Pair(cost after,
                                  Pair(outcome, EmptyList)))))))
    """

    def __init__(self, residual, rule_shape, newly_enabled, cost_before, cost_after, outcome):
        body = M.Pair(
            residual,
            M.Pair(
                rule_shape,
                M.Pair(
                    newly_enabled,
                    M.Pair(cost_before, M.Pair(cost_after, M.Pair(outcome, EmptyList))),
                ),
            ),
        )
        self.result = M.Pair(Lmod.InterventionEpisodeLabel, body)
        super().__init__(inputs=body, results=self.result)

    def __call__(self):
        return self.result


class EpisodeResidual(Edge):
    def __init__(self, episode):
        self.result = Head(Tail(episode)())()
        super().__init__(inputs=M.Pair(episode, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EpisodeRuleShape(Edge):
    def __init__(self, episode):
        self.result = Head(Tail(Tail(episode)())())()
        super().__init__(inputs=M.Pair(episode, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EpisodeOutcome(Edge):
    def __init__(self, episode):
        self.result = Head(
            Tail(Tail(Tail(Tail(Tail(Tail(episode)())())())())())()
        )()
        super().__init__(inputs=M.Pair(episode, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AntiUnify(Edge):
    """Structural anti-unification of two terms.

    Disagreements become alpha placeholders, interned by the disagreeing
    subterm pair so the same disagreement yields the same placeholder.
    Residual and rule shape are generalized in one call -- as the pair of
    both -- so shared disagreements co-refer across the two.

    Result: Pair(generalized, Pair(env, Pair(next index, EmptyList))).
    """

    def __init__(self, left, right):
        start = self._fresh_start(right, self._fresh_start(left, M.Zero))
        self.result = self._walk(left, right, EmptyList, start)
        super().__init__(inputs=M.Pair(left, M.Pair(right, EmptyList)), results=self.result)

    def _fresh_start(self, term, acc):
        """The first index above every placeholder already in the inputs.

        Without this, a generalization variable could collide with an
        alpha placeholder carried in from an episode, silently conflating
        two different variables in the learned pattern.
        """
        if IdentityCompare(term, EmptyList)() is M.truth_value:
            return acc
        if M.IsPair(term)() is M.truth_value:
            if IdentityCompare(Head(term)(), Lmod.AlphaPlaceholderLabel)() is M.truth_value:
                index = Tail(term)()
                above = Head(M.Succ(index, M.AllConstructors)())()
                if M.NatLess(acc, above, M.AllConstructors)() is M.truth_value:
                    return above
                return acc
            return self._fresh_start(Tail(term)(), self._fresh_start(Head(term)(), acc))
        return acc

    def _lookup(self, env, left, right):
        if IdentityCompare(env, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(env)()
        key = Head(entry)()
        if M.Compare(Head(key)(), left)() is M.truth_value:
            if M.Compare(Tail(key)(), right)() is M.truth_value:
                return Head(Tail(entry)())()
        return self._lookup(Tail(env)(), left, right)

    def _walk(self, left, right, env, next_index):
        if M.Compare(left, right)() is M.truth_value:
            return M.Pair(left, M.Pair(env, M.Pair(next_index, EmptyList)))
        both_pairs = M.AndAtom(M.IsPair(left)(), M.IsPair(right)())()
        neither_var = M.AndAtom(
            M.NotAtom(IsVarPatternTerm(left)())(),
            M.NotAtom(IsVarPatternTerm(right)())(),
        )()
        if M.AndAtom(both_pairs, neither_var)() is M.truth_value:
            head_result = self._walk(Head(left)(), Head(right)(), env, next_index)
            gen_head = Head(head_result)()
            env1 = Head(Tail(head_result)())()
            index1 = Head(Tail(Tail(head_result)())())()
            tail_result = self._walk(Tail(left)(), Tail(right)(), env1, index1)
            gen_tail = Head(tail_result)()
            env2 = Head(Tail(tail_result)())()
            index2 = Head(Tail(Tail(tail_result)())())()
            return M.Pair(M.Pair(gen_head, gen_tail), M.Pair(env2, M.Pair(index2, EmptyList)))
        seen = self._lookup(env, left, right)
        if IdentityCompare(seen, EmptyList)() is M.false_value:
            return M.Pair(seen, M.Pair(env, M.Pair(next_index, EmptyList)))
        placeholder = M.Pair(Lmod.AlphaPlaceholderLabel, next_index)
        entry = M.Pair(M.Pair(left, right), M.Pair(placeholder, EmptyList))
        next_pair = M.Succ(next_index, M.AllConstructors)()
        return M.Pair(
            placeholder,
            M.Pair(M.Pair(entry, env), M.Pair(Head(next_pair)(), EmptyList)),
        )

    def __call__(self):
        return self.result


class UsefulEpisodes(Edge):
    """The subchain of episodes whose outcome was a demonstrated unlock."""

    def __init__(self, episodes):
        self.result = self._walk(episodes)
        super().__init__(inputs=M.Pair(episodes, EmptyList), results=self.result)

    def _walk(self, episodes):
        if IdentityCompare(episodes, EmptyList)() is M.truth_value:
            return EmptyList
        episode = Head(episodes)()
        rest = Tail(episodes)()
        if IdentityCompare(
            EpisodeOutcome(episode)(), Lmod.DemonstratedUsefulDependencyLabel
        )() is M.truth_value:
            return M.Pair(episode, self._walk(rest))
        return self._walk(rest)

    def __call__(self):
        return self.result


class SharesStructure(Edge):
    """True when a generalized residual is still a pair with a concrete head.

    A generalization whose root or head collapsed into a placeholder says
    nothing; a policy is stored only when structure survived.
    """

    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if IdentityCompare(Head(term)(), Lmod.AlphaPlaceholderLabel)() is M.false_value:
                head = Head(term)()
                is_ph = M.false_value
                if M.IsPair(head)() is M.truth_value:
                    if IdentityCompare(Head(head)(), Lmod.AlphaPlaceholderLabel)() is M.truth_value:
                        is_ph = M.truth_value
                if IdentityCompare(is_ph, M.false_value)() is M.truth_value:
                    self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LearnedPolicy(Edge):
    """Pair(LearnedDependencyPolicyLabel,
            Pair(generalized residual,
                 Pair(generalized rule shape,
                      Pair(support count,
                           Pair(supporting episodes, EmptyList)))))"""

    def __init__(self, residual, rule_shape, support_count, episodes):
        body = M.Pair(
            residual,
            M.Pair(rule_shape, M.Pair(support_count, M.Pair(episodes, EmptyList))),
        )
        self.result = M.Pair(Lmod.LearnedDependencyPolicyLabel, body)
        super().__init__(inputs=body, results=self.result)

    def __call__(self):
        return self.result


class PolicyResidual(Edge):
    def __init__(self, policy):
        self.result = Head(Tail(policy)())()
        super().__init__(inputs=M.Pair(policy, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolicyRuleShape(Edge):
    def __init__(self, policy):
        self.result = Head(Tail(Tail(policy)())())()
        super().__init__(inputs=M.Pair(policy, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolicySupportCount(Edge):
    def __init__(self, policy):
        self.result = Head(Tail(Tail(Tail(policy)())())())()
        super().__init__(inputs=M.Pair(policy, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GeneralizeEpisodes(Edge):
    """Fold anti-unification over useful episodes' (residual, shape) pairs."""

    def __init__(self, episodes):
        self.result = EmptyList
        if IdentityCompare(episodes, EmptyList)() is M.false_value:
            rest = Tail(episodes)()
            if IdentityCompare(rest, EmptyList)() is M.false_value:
                first = Head(episodes)()
                seed = M.Pair(EpisodeResidual(first)(), EpisodeRuleShape(first)())
                folded = self._fold(rest, seed)
                count = self._count(episodes, M.Zero)
                residual = Head(folded)()
                shape = Tail(folded)()
                if SharesStructure(residual)() is M.truth_value:
                    self.result = LearnedPolicy(residual, shape, count, episodes)()
        super().__init__(inputs=M.Pair(episodes, EmptyList), results=self.result)

    def _count(self, chain, acc):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return acc
        return self._count(Tail(chain)(), Head(M.Succ(acc, M.AllConstructors)())())

    def _fold(self, episodes, acc):
        if IdentityCompare(episodes, EmptyList)() is M.truth_value:
            return acc
        episode = Head(episodes)()
        candidate = M.Pair(EpisodeResidual(episode)(), EpisodeRuleShape(episode)())
        generalized = Head(AntiUnify(acc, candidate)())()
        return self._fold(Tail(episodes)(), generalized)

    def __call__(self):
        return self.result


class NonPolicyEntries(Edge):
    """Learned-memory entries that are not anti-unified policies.

    Adopted invariants share the learned-memory chain so the mask and
    the reset govern them; policy relearning must not erase them.
    """

    def __init__(self, chain):
        self.result = self._walk(chain)
        super().__init__(inputs=M.Pair(chain, EmptyList), results=self.result)

    def _walk(self, chain):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(chain)()
        rest = Tail(chain)()
        if M.IsPair(entry)() is M.truth_value:
            if IdentityCompare(Head(entry)(), Lmod.LearnedDependencyPolicyLabel)() is M.truth_value:
                return self._walk(rest)
        return M.Pair(entry, self._walk(rest))

    def __call__(self):
        return self.result


def learn_policies(graph):
    """Regenerate the policy chain from the useful episodes on record.

    With fewer than two useful episodes there is no policy: one example is
    an anecdote, not a generalization. The result replaces the whole
    dependency_policies field, so resetting episodes resets policies.
    """
    useful = UsefulEpisodes(graph.intervention_episodes)()
    policy = GeneralizeEpisodes(useful)()
    kept = NonPolicyEntries(graph.dependency_policies)()
    if IdentityCompare(policy, EmptyList)() is M.truth_value:
        graph.set_dependency_policies(kept)
        return EmptyList
    chain = M.Pair(policy, kept)
    graph.set_dependency_policies(chain)
    return chain


def reset_learned_memory(graph):
    """Forget episodes and policies. Predictions must disappear with them."""
    return graph.reset_learned_memory()


class PlaceholdersToVars(Edge):
    """Alpha placeholders as matcher variables, interned by index.

    Converts Pair(residual, shape) in one pass so a placeholder shared
    between residual and shape becomes one variable object in both.
    Result: Pair(converted, Pair(env, EmptyList)).
    """

    def __init__(self, term):
        self.result = self._walk(term, EmptyList)
        super().__init__(inputs=M.Pair(term, EmptyList), results=self.result)

    def _is_placeholder(self, term):
        if M.IsPair(term)() is M.truth_value:
            if IdentityCompare(Head(term)(), Lmod.AlphaPlaceholderLabel)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def _lookup(self, env, index):
        if IdentityCompare(env, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(env)()
        if M.Compare(Head(entry)(), index)() is M.truth_value:
            return Head(Tail(entry)())()
        return self._lookup(Tail(env)(), index)

    def _walk(self, term, env):
        if self._is_placeholder(term) is M.truth_value:
            index = Tail(term)()
            seen = self._lookup(env, index)
            if IdentityCompare(seen, EmptyList)() is M.false_value:
                return M.Pair(seen, M.Pair(env, EmptyList))
            fresh = M.Pair(M.VarTag, M.Pair(M.Atom(), EmptyList))
            return M.Pair(fresh, M.Pair(M.Pair(M.Pair(index, M.Pair(fresh, EmptyList)), env), EmptyList))
        if M.IsPair(term)() is M.truth_value:
            head_result = self._walk(Head(term)(), env)
            tail_result = self._walk(Tail(term)(), Head(Tail(head_result)())())
            return M.Pair(
                M.Pair(Head(head_result)(), Head(tail_result)()),
                M.Pair(Head(Tail(tail_result)())(), EmptyList),
            )
        return M.Pair(term, M.Pair(env, EmptyList))

    def __call__(self):
        return self.result


class PolicyPrediction(Edge):
    """Pair(PolicyPredictionLabel, Pair(policy, Pair(predicted shape, EmptyList)))."""

    def __init__(self, policy, predicted_shape):
        self.result = M.Pair(
            Lmod.PolicyPredictionLabel, M.Pair(policy, M.Pair(predicted_shape, EmptyList))
        )
        super().__init__(inputs=M.Pair(policy, M.Pair(predicted_shape, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PolicyPredictionsFor(Edge):
    """Predictions from learned policies against one missing premise.

    A policy predicts only when its generalized residual pattern matches
    the request's missing premise; the predicted rule shape is the
    policy's generalized shape under that match's bindings. On a fresh
    checkpoint there are no policies and therefore no predictions.
    """

    def __init__(self, missing_term, policies):
        self.missing = missing_term
        self.result = self._walk(policies)
        super().__init__(inputs=M.Pair(missing_term, M.Pair(policies, EmptyList)), results=self.result)

    def _walk(self, policies):
        if IdentityCompare(policies, EmptyList)() is M.truth_value:
            return EmptyList
        policy = Head(policies)()
        rest = Tail(policies)()
        if M.IsPair(policy)() is M.false_value:
            return self._walk(rest)
        if IdentityCompare(Head(policy)(), Lmod.LearnedDependencyPolicyLabel)() is M.false_value:
            # invariants and other learned-memory entries are not predictors
            return self._walk(rest)
        converted = PlaceholdersToVars(
            M.Pair(PolicyResidual(policy)(), PolicyRuleShape(policy)())
        )()
        pattern_pair = Head(converted)()
        residual_pattern = Head(pattern_pair)()
        shape_pattern = Tail(pattern_pair)()
        match = M.Match(residual_pattern, self.missing)()
        if IdentityCompare(Head(match)(), M.truth_value)() is M.truth_value:
            predicted = ApplyBindings(shape_pattern, Tail(match)())()
            return M.Pair(PolicyPrediction(policy, predicted)(), self._walk(rest))
        return self._walk(rest)

    def __call__(self):
        return self.result


class LearnedMemoryEnabledFlag(Edge):
    """The reversible learned-memory mask, read from the graph context.

    generator_policy entries Pair(LearnedDependencyPolicyLabel, Pair(flag,
    EmptyList)) mask the policy store without erasing it. Absent an entry
    the store is enabled. Disabling must silence every policy prediction;
    re-enabling must bring the same predictions back -- the appear,
    disappear, reappear cycle a hardcoded suggestion cannot survive.
    """

    def __init__(self, graph):
        self.result = self._walk(graph.generator_policy)
        super().__init__(inputs=EmptyList, results=self.result)

    def _walk(self, chain):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return M.truth_value
        entry = Head(chain)()
        if M.IsPair(entry)() is M.truth_value:
            if IdentityCompare(Head(entry)(), Lmod.LearnedDependencyPolicyLabel)() is M.truth_value:
                payload = Tail(entry)()
                if M.IsPair(payload)() is M.truth_value:
                    return Head(payload)()
        return self._walk(Tail(chain)())

    def __call__(self):
        return self.result


def learned_memory_enabled(graph):
    return LearnedMemoryEnabledFlag(graph)()


def disable_learned_memory(graph):
    entry = M.Pair(Lmod.LearnedDependencyPolicyLabel, M.Pair(M.false_value, EmptyList))
    graph._replace_context(generator_policy=M.Pair(entry, graph.generator_policy))
    return M.false_value


def enable_learned_memory(graph):
    entry = M.Pair(Lmod.LearnedDependencyPolicyLabel, M.Pair(M.truth_value, EmptyList))
    graph._replace_context(generator_policy=M.Pair(entry, graph.generator_policy))
    return M.truth_value


def policy_predictions(graph, records):
    """Predictions for each stored request record, flattened.

    Empty when the learned-memory mask is off: a masked policy predicts
    nothing, and nothing else in the machine may produce a prediction.
    """
    if learned_memory_enabled(graph) is M.false_value:
        return EmptyList
    return RequestsPredictions(records, graph.dependency_policies)()


class RequestsPredictions(Edge):
    def __init__(self, records, policies):
        self.policies = policies
        self.result = self._walk(records)
        super().__init__(inputs=M.Pair(records, M.Pair(policies, EmptyList)), results=self.result)

    def _concat(self, left, right):
        if IdentityCompare(left, EmptyList)() is M.truth_value:
            return right
        return M.Pair(Head(left)(), self._concat(Tail(left)(), right))

    def _walk(self, records):
        if IdentityCompare(records, EmptyList)() is M.truth_value:
            return EmptyList
        record = Head(records)()
        rest = Tail(records)()
        if IsUncharacterizedStall(record)() is M.truth_value:
            return self._walk(rest)
        formal = DependencyRequestFormalStatement(record)()
        missing = Head(Tail(formal)())()
        predictions = PolicyPredictionsFor(missing, self.policies)()
        return self._concat(predictions, self._walk(rest))

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Teaching against a request, gated by measured counterfactual evidence.
# ---------------------------------------------------------------------------


class DependencySuppliedByTheorem(Edge):
    def __init__(self, dep_id, formal_term):
        self.result = M.Pair(
            Lmod.DependencySuppliedByTheoremLabel,
            M.Pair(dep_id, M.Pair(formal_term, EmptyList)),
        )
        super().__init__(inputs=M.Pair(dep_id, M.Pair(formal_term, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class DependencyUnlockedResidual(Edge):
    def __init__(self, dep_id, evidence):
        self.result = M.Pair(
            Lmod.DependencyUnlockedResidualLabel,
            M.Pair(dep_id, M.Pair(evidence, EmptyList)),
        )
        super().__init__(inputs=M.Pair(dep_id, M.Pair(evidence, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SetRequestCounterfactual(Edge):
    """Replace the counterfactual evidence of one request in place."""

    def __init__(self, chain, dep_id, evidence):
        self.result = self._walk(chain, dep_id, evidence, EmptyList)
        super().__init__(inputs=M.Pair(chain, M.Pair(dep_id, M.Pair(evidence, EmptyList))), results=self.result)

    def _walk(self, chain, dep_id, evidence, acc):
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
                DependencyRequestFormalStatement(req)(),
                DependencyRequestBridgePlan(req)(),
                evidence,
                DependencyRequestAssumptions(req)(),
                DependencyRequestStatus(req)(),
                DependencyRequestProvenance(req)(),
                DependencyRequestId(req)(),
            )()
            return self._walk(rest, dep_id, evidence, M.Pair(rebuilt, acc))
        return self._walk(rest, dep_id, evidence, M.Pair(req, acc))

    def __call__(self):
        return self.result


def teach_dependency(graph, dep_id, formal_term, start_facts, goal_facts, rules, fuel=None):
    """Teach a theorem against one approved request and measure it.

    The theorem is stored and compiled either way; what the measurement
    gates is the *status*. Only measured unlock evidence -- goal closed, an
    existing rule newly enabled, residual cost fallen, or new residuals
    exposed -- makes the node DemonstratedUsefulDependency and records an
    intervention episode. Without it the node stays speculative and the
    theorem's provenance says HUMAN_SUPPLIED_TRUSTED_THEOREM_WITHOUT_UNLOCK
    _EVIDENCE, not pretending validation.

    Returns Pair(status, Pair(evidence, Pair(rule, EmptyList))), or
    EmptyList when the request is unknown or the rule is inadmissible.
    """
    req = FindRequest(graph.dependency_requests, dep_id)()
    if IdentityCompare(req, EmptyList)() is M.truth_value:
        return EmptyList
    parent_goal_fact = EmptyList
    goal_walk = goal_facts
    if IdentityCompare(goal_walk, EmptyList)() is M.false_value:
        parent_goal_fact = Head(goal_walk)()
    if validate_taught_rule(formal_term, parent_goal_fact) is M.false_value:
        return EmptyList
    rule = teach_trusted_theorem(graph, formal_term)
    graph._replace_context(
        dependency_graph=M.Pair(
            DependencySuppliedByTheorem(dep_id, formal_term)(), graph.dependency_graph
        )
    )
    ev, unlock = counterfactual_evaluation(graph, start_facts, goal_facts, rules, rule, fuel)
    graph._replace_context(
        dependency_requests=SetRequestCounterfactual(graph.dependency_requests, dep_id, ev)()
    )
    if IdentityCompare(unlock, M.truth_value)() is M.truth_value:
        graph._replace_context(
            dependency_requests=SetRequestStatus(
                graph.dependency_requests, dep_id, DependencyStatus.DEMONSTRATED_USEFUL
            )(),
            dependency_graph=M.Pair(
                DependencyUnlockedResidual(dep_id, ev)(), graph.dependency_graph
            ),
        )
        bump_generator_metric(graph, Lmod.UsefulCountLabel)
        goal_closed = Head(
            Tail(Tail(Tail(Tail(Tail(Tail(ev)())())())())())()
        )()
        if IdentityCompare(goal_closed, M.truth_value)() is M.truth_value:
            bump_generator_metric(graph, Lmod.UsedCountLabel)
        formal = DependencyRequestFormalStatement(req)()
        residual = Head(Tail(formal)())()
        features = EpisodeFeatures(formal_term, residual)()
        cost_before = Head(Tail(ev)())()
        cost_after = Head(Tail(Tail(ev)())())()
        newly_enabled = Head(Tail(Tail(Tail(ev)())())())()
        episode = InterventionEpisode(
            Head(features)(),
            Head(Tail(features)())(),
            newly_enabled,
            cost_before,
            cost_after,
            Lmod.DemonstratedUsefulDependencyLabel,
        )()
        graph.record_intervention_episode(episode)
        learn_policies(graph)
        status = DependencyStatus.DEMONSTRATED_USEFUL
    else:
        graph.add_provenance(formal_term, Lmod.HumanSuppliedTrustedTheoremWithoutUnlockLabel)
        status = RequestStatusById(graph.dependency_requests, dep_id)()
    return M.Pair(status, M.Pair(ev, M.Pair(rule, EmptyList)))


# ---------------------------------------------------------------------------
# Retry measurement: five graded outcomes, never a bare pass/fail.
# ---------------------------------------------------------------------------


RETRY_GOAL_CLOSED = M.Char("goal closed")
RETRY_COST_DECREASED = M.Char("residual cost decreased")
RETRY_NEW_FIRINGS = M.Char("new firings enabled")
RETRY_NEW_RESIDUALS = M.Char("new residuals exposed")
RETRY_NO_PROGRESS = M.Char("no measurable progress")


def measure_retry(graph, start_facts, goal_facts, rules, baseline_outcome, fuel=None):
    """Rerun bounded search and grade progress against a recorded baseline.

    Returns Pair(grade, Pair(outcome, EmptyList)) where grade is one of the
    five retry chars above. A retry that reproduces the identical stall
    grades as no measurable progress -- the caller must then say that the
    taught theorem was stored but did not unlock the parent goal.
    """
    if fuel is None:
        fuel = DEFAULT_SEARCH_FUEL
    outcome = Head(evaluated_search(start_facts, goal_facts, rules, fuel))()
    if IdentityCompare(ForwardSearchClosed(outcome)(), M.truth_value)() is M.truth_value:
        return M.Pair(RETRY_GOAL_CLOSED, M.Pair(outcome, EmptyList))
    if IdentityCompare(baseline_outcome, EmptyList)() is M.false_value:
        base_cost = ForwardSearchCost(baseline_outcome)()
        new_cost = ForwardSearchCost(outcome)()
        if ChainShorter(new_cost, base_cost)() is M.truth_value:
            return M.Pair(RETRY_COST_DECREASED, M.Pair(outcome, EmptyList))
        new_firings = FiredRuleDifference(
            ForwardSearchFired(outcome)(), ForwardSearchFired(baseline_outcome)(), EmptyList
        )()
        if IdentityCompare(new_firings, EmptyList)() is M.false_value:
            return M.Pair(RETRY_NEW_FIRINGS, M.Pair(outcome, EmptyList))
        base_obligations = ResidualObligations(ForwardSearchFacts(baseline_outcome)(), rules)()
        new_obligations = ResidualObligations(ForwardSearchFacts(outcome)(), rules)()
        exposed = ObligationDifference(new_obligations, base_obligations)()
        if IdentityCompare(exposed, EmptyList)() is M.false_value:
            return M.Pair(RETRY_NEW_RESIDUALS, M.Pair(outcome, EmptyList))
    return M.Pair(RETRY_NO_PROGRESS, M.Pair(outcome, EmptyList))


# ---------------------------------------------------------------------------
# The live attempt: bounded search, residual preservation, zero-successor root.
# ---------------------------------------------------------------------------


class RecordAllPartialMatches(Edge):
    """Record the genuine partial match of every rule over a fact state."""

    def __init__(self, graph, rules, facts, goal_facts=None):
        if goal_facts is None:
            goal_facts = EmptyList
        self.graph = graph
        self.facts = facts
        self.goal_facts = goal_facts
        self.result = self._walk(rules)
        super().__init__(inputs=M.Pair(rules, EmptyList), results=self.result)

    def _walk(self, rules):
        if IdentityCompare(rules, EmptyList)() is M.truth_value:
            return EmptyList
        recorded = RecordPremisePartialMatch(
            self.graph, Head(rules)(), self.facts, self.goal_facts
        )()
        rest = self._walk(Tail(rules)())
        if IdentityCompare(recorded, EmptyList)() is M.truth_value:
            return rest
        return M.Pair(recorded, rest)

    def __call__(self):
        return self.result


def attempt_goal(graph, start_facts, goal_facts, rules, fuel=None):
    """One bounded attempt at a goal, preserving genuine residual states.

    On failure, every rule's genuine partial match over the final fact
    state is recorded as an AttemptedRule; when none exists the residual
    record still holds the root with zero successors, so the stall is
    never erased. On success a last-proof record is stored with
    SEARCH_DERIVED provenance and the firing chain as its derivation.
    """
    if fuel is None:
        fuel = DEFAULT_SEARCH_FUEL
    graph.clear_research_attempts()
    violated = invariant_prune(graph, goal_facts)
    if IdentityCompare(violated, EmptyList)() is M.false_value:
        # Conjectured unreachable: an adopted invariant disagrees with the
        # goal's observable. No search runs; the violated record is the
        # residual, and the learned-memory mask governs this path.
        pruned_root = M.Pair(
            Lmod.InvariantLabel, M.Pair(goal_facts, M.Pair(violated, EmptyList))
        )
        graph._replace_context(last_residuals=pruned_root, research_residuals=pruned_root)
        set_last_proof(
            graph,
            M.Pair(
                Lmod.LastProofLabel,
                M.Pair(goal_facts, M.Pair(Lmod.FailureLabel, M.Pair(EmptyList, M.Pair(EmptyList, EmptyList)))),
            ),
        )
        return M.Pair(M.false_value, M.Pair(EmptyList, M.Pair(EmptyList, M.Pair(start_facts, EmptyList))))
    cached = graph.lookup_derivation(start_facts, goal_facts)
    searched = evaluated_search(start_facts, goal_facts, rules, fuel)
    outcome = Head(searched)()
    start_facts = Head(Tail(searched)())()
    evaluated = Head(Tail(Tail(searched)())())()
    refuted = Head(Tail(Tail(Tail(searched)())())())()
    cur = evaluated
    while IdentityCompare(cur, EmptyList)() is M.false_value:
        known = ProvenanceEntriesFor(graph.provenance_map, Lmod.DomainAxiomLabel)()
        seen = ObligationDifference(M.Pair(Head(cur)(), EmptyList), known)()
        if IdentityCompare(seen, EmptyList)() is M.false_value:
            graph.add_provenance(Head(cur)(), Lmod.DomainAxiomLabel)
        cur = Tail(cur)()
    cur = refuted
    while IdentityCompare(cur, EmptyList)() is M.false_value:
        known = ProvenanceEntriesFor(graph.provenance_map, Lmod.CounterexampleLabel)()
        seen = ObligationDifference(M.Pair(Head(cur)(), EmptyList), known)()
        if IdentityCompare(seen, EmptyList)() is M.false_value:
            graph.add_provenance(Head(cur)(), Lmod.CounterexampleLabel)
        cur = Tail(cur)()
    closed = ForwardSearchClosed(outcome)()
    fired = ForwardSearchFired(outcome)()
    cost = ForwardSearchCost(outcome)()
    if IdentityCompare(closed, M.truth_value)() is M.truth_value:
        # A remembered derivation is not suppressed and not trusted: it is
        # reported as a cache hit only after the fresh bounded search just
        # revalidated the goal. Provenance says retrieved, never derived.
        provenance = Lmod.SearchDerivedLabel
        if IdentityCompare(cached, EmptyList)() is M.false_value:
            provenance = Lmod.DerivationCacheHitLabel
        graph.add_derivation(start_facts, goal_facts, fired)
        record_trace(graph, start_facts, goal_facts, fired)
        proof_term = M.Pair(
            Lmod.LastProofLabel,
            M.Pair(
                goal_facts,
                M.Pair(provenance, M.Pair(fired, M.Pair(cost, EmptyList))),
            ),
        )
        set_last_proof(graph, proof_term)
        graph._replace_context(last_residuals=EmptyList, research_residuals=EmptyList)
        return outcome
    RecordAllPartialMatches(graph, rules, ForwardSearchFacts(outcome)(), goal_facts)()
    attempts = graph.research_attempts
    if IdentityCompare(attempts, EmptyList)() is M.truth_value:
        root = M.Pair(Lmod.ZeroSuccessorResidualLabel, M.Pair(goal_facts, EmptyList))
        graph._replace_context(last_residuals=root, research_residuals=root)
    else:
        set_last_attempts(graph, attempts)
    failure_term = M.Pair(
        Lmod.LastProofLabel,
        M.Pair(
            goal_facts,
            M.Pair(Lmod.FailureLabel, M.Pair(fired, M.Pair(cost, EmptyList))),
        ),
    )
    set_last_proof(graph, failure_term)
    return outcome


# ---------------------------------------------------------------------------
# The self-improvement loop.
#
# Closing one arrow: activated structure feeds back into a miner that
# reads derivation traces. Phase 1 compresses repeated rule compositions
# into candidate laws, gated on measured rent. Phase 2 conjectures
# invariants of derived facts from a fixed, inspectable observable
# library -- no oracle proposes candidates. Phase 3 turns adopted
# invariants into unreachability prunes that ride the learned-memory
# mask, so the appear/disappear/reappear discipline covers them too.
# ---------------------------------------------------------------------------


def record_trace(graph, start_facts, goal_facts, fired):
    """One closed derivation, kept for the miner. Not learned memory."""
    trace = M.Pair(
        Lmod.DerivationLabel,
        M.Pair(start_facts, M.Pair(goal_facts, M.Pair(fired, EmptyList))),
    )
    graph._replace_context(generator_policy=M.Pair(trace, graph.generator_policy))
    return trace


class TracesOnRecord(Edge):
    """Every stored derivation trace, newest first."""

    def __init__(self, graph):
        self.result = self._walk(graph.generator_policy)
        super().__init__(inputs=EmptyList, results=self.result)

    def _walk(self, chain):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(chain)()
        rest = Tail(chain)()
        if M.IsPair(entry)() is M.truth_value:
            if IdentityCompare(Head(entry)(), Lmod.DerivationLabel)() is M.truth_value:
                return M.Pair(entry, self._walk(rest))
        return self._walk(rest)

    def __call__(self):
        return self.result


class StepInstances(Edge):
    """Fired steps as concrete instances: rule, premises, conclusion."""

    def __init__(self, fired):
        self.result = self._walk(fired)
        super().__init__(inputs=M.Pair(fired, EmptyList), results=self.result)

    def _walk(self, fired):
        from .proof import RulePremises, RuleReplacement

        if IdentityCompare(fired, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(fired)()
        rule = Head(entry)()
        bindings = Head(Tail(entry)())()
        premises = self._instantiate(RulePremises(rule)(), bindings)
        conclusion = ApplyBindings(RuleReplacement(rule)(), bindings)()
        record = M.Pair(rule, M.Pair(premises, M.Pair(conclusion, EmptyList)))
        return M.Pair(record, self._walk(Tail(fired)()))

    def _instantiate(self, premises, bindings):
        if IdentityCompare(premises, EmptyList)() is M.truth_value:
            return EmptyList
        return M.Pair(
            ApplyBindings(Head(premises)(), bindings)(),
            self._instantiate(Tail(premises)(), bindings),
        )

    def __call__(self):
        return self.result


class ComposedInstances(Edge):
    """Dataflow-linked step pairs of one trace, as composed law instances.

    When a later step consumed an earlier step's conclusion, the pair
    composes: premises are the earlier step's premises plus the later
    step's other premises; the conclusion is the later step's. Each
    record: Pair(Pair(ruleA, ruleB), Pair(premises, Pair(conclusion, EmptyList))).
    """

    def __init__(self, fired):
        steps = StepInstances(fired)()
        self.result = self._pairs(steps)
        super().__init__(inputs=M.Pair(fired, EmptyList), results=self.result)

    def _pairs(self, steps):
        if IdentityCompare(steps, EmptyList)() is M.truth_value:
            return EmptyList
        first = Head(steps)()
        rest = Tail(steps)()
        return self._concat(self._with_later(first, rest), self._pairs(rest))

    def _with_later(self, first, laters):
        if IdentityCompare(laters, EmptyList)() is M.truth_value:
            return EmptyList
        later = Head(laters)()
        rest = Tail(laters)()
        conclusion_a = Head(Tail(Tail(first)())())()
        premises_b = Head(Tail(later)())()
        linked = self._drop_linked(premises_b, conclusion_a)
        if IdentityCompare(Head(linked)(), M.truth_value)() is M.truth_value:
            other_premises = Tail(linked)()
            premises_a = Head(Tail(first)())()
            combined = self._concat(premises_a, other_premises)
            key = M.Pair(Head(first)(), Head(later)())
            record = M.Pair(
                key,
                M.Pair(combined, M.Pair(Head(Tail(Tail(later)())())(), EmptyList)),
            )
            return M.Pair(record, self._with_later(first, rest))
        return self._with_later(first, rest)

    def _drop_linked(self, premises, conclusion):
        if IdentityCompare(premises, EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, EmptyList)
        premise = Head(premises)()
        rest = Tail(premises)()
        if M.Compare(premise, conclusion)() is M.truth_value:
            return M.Pair(M.truth_value, rest)
        deeper = self._drop_linked(rest, conclusion)
        return M.Pair(Head(deeper)(), M.Pair(premise, Tail(deeper)()))

    def _concat(self, left, right):
        if IdentityCompare(left, EmptyList)() is M.truth_value:
            return right
        return M.Pair(Head(left)(), self._concat(Tail(left)(), right))

    def __call__(self):
        return self.result


def mine_compressed_laws(graph):
    """Candidate laws from motifs repeated across distinct traces.

    A rule-pair key occurring in two different traces yields the
    anti-unification of its two composed instances as a FormalRule
    candidate. The generalized conclusion must retain structure; a
    candidate alpha-equal to an already-adopted law is not re-proposed.
    Nothing here activates anything: adoption is a separate, human-gated,
    rent-measured step.
    """
    traces = TracesOnRecord(graph)()
    candidates = EmptyList
    outer = traces
    while IdentityCompare(outer, EmptyList)() is M.false_value:
        first_trace = Head(outer)()
        rest_traces = Tail(outer)()
        first_composed = ComposedInstances(Head(Tail(Tail(Tail(first_trace)())())())())()
        inner = rest_traces
        while IdentityCompare(inner, EmptyList)() is M.false_value:
            second_composed = ComposedInstances(
                Head(Tail(Tail(Tail(Head(inner)())())())())()
            )()
            walk_a = first_composed
            while IdentityCompare(walk_a, EmptyList)() is M.false_value:
                record_a = Head(walk_a)()
                walk_a = Tail(walk_a)()
                walk_b = second_composed
                while IdentityCompare(walk_b, EmptyList)() is M.false_value:
                    record_b = Head(walk_b)()
                    walk_b = Tail(walk_b)()
                    key_a = Head(record_a)()
                    key_b = Head(record_b)()
                    same_pair = M.AndAtom(
                        IdentityCompare(Head(key_a)(), Head(key_b)())(),
                        IdentityCompare(Tail(key_a)(), Tail(key_b)())(),
                    )()
                    if IdentityCompare(same_pair, M.truth_value)() is M.false_value:
                        continue
                    generalized = Head(AntiUnify(Tail(record_a)(), Tail(record_b)())())()
                    converted = Head(PlaceholdersToVars(generalized)())()
                    premises = Head(converted)()
                    conclusion = Head(Tail(converted)())()
                    if SharesStructure(conclusion)() is M.false_value:
                        continue
                    if M.IsPair(conclusion)() is M.false_value:
                        continue
                    candidate = FormalRule(premises, conclusion)()
                    already = ProvenanceEntriesFor(
                        graph.provenance_map, Lmod.InventedLemmaLabel
                    )()
                    duplicate = M.false_value
                    walk_known = already
                    while IdentityCompare(walk_known, EmptyList)() is M.false_value:
                        known = Head(walk_known)()
                        walk_known = Tail(walk_known)()
                        if M.Compare(
                            AlphaNormalized(known, EmptyList)(),
                            AlphaNormalized(candidate, EmptyList)(),
                        )() is M.truth_value:
                            duplicate = M.truth_value
                            walk_known = EmptyList
                    walk_seen = candidates
                    while IdentityCompare(walk_seen, EmptyList)() is M.false_value:
                        seen = Head(walk_seen)()
                        walk_seen = Tail(walk_seen)()
                        if M.Compare(
                            AlphaNormalized(seen, EmptyList)(),
                            AlphaNormalized(candidate, EmptyList)(),
                        )() is M.truth_value:
                            duplicate = M.truth_value
                            walk_seen = EmptyList
                    if IdentityCompare(duplicate, M.false_value)() is M.truth_value:
                        candidates = M.Pair(candidate, candidates)
            inner = Tail(inner)()
        outer = rest_traces
    return M.Reverse(candidates)()


def adopt_compressed_law(graph, candidate, start_facts, goal_facts, rules, fuel=None):
    """Rent gate: activate the candidate only if it pays.

    Rent is measured in the compression's own currency -- the fired
    chain of a held-out attempt must shorten, or an open attempt must
    close. On pass the candidate is stored INVENTED_LEMMA and compiles
    into the rule set like any taught law. On fail nothing activates
    and the measured lengths are returned either way:
    Pair(adopted flag, Pair(fired-before, Pair(fired-after, EmptyList))).
    """
    if fuel is None:
        fuel = DEFAULT_SEARCH_FUEL
    baseline = Head(evaluated_search(start_facts, goal_facts, rules, fuel))()
    compiled = compile_formal_rule(candidate)
    augmented = Head(
        evaluated_search(start_facts, goal_facts, M.Pair(compiled, rules), fuel)
    )()
    fired_before = ForwardSearchFired(baseline)()
    fired_after = ForwardSearchFired(augmented)()
    closed_now = M.AndAtom(
        M.NotAtom(ForwardSearchClosed(baseline)())(),
        ForwardSearchClosed(augmented)(),
    )()
    both_closed_shorter = M.AndAtom(
        ForwardSearchClosed(augmented)(),
        ChainShorter(fired_after, fired_before)(),
    )()
    pays = M.OrAtom(closed_now, both_closed_shorter)()
    if IdentityCompare(pays, M.truth_value)() is M.truth_value:
        graph.add_provenance(candidate, Lmod.InventedLemmaLabel)
        graph.tag_rule_origin(compiled, Lmod.InventedLemmaLabel)
        return M.Pair(M.truth_value, M.Pair(fired_before, M.Pair(fired_after, EmptyList)))
    return M.Pair(M.false_value, M.Pair(fired_before, M.Pair(fired_after, EmptyList)))


# --- Phase 2: invariant conjecture from a fixed observable library --------

OBSERVABLE_PARITY = M.Char("parity")
OBSERVABLE_RESIDUE = M.Char("residue")


class ObservableOnFact(Edge):
    """The value of one library observable on one fact, or EmptyList.

    Shapes: (parity <argindex>) and (residue <argindex> <k>). The
    argument must be a ground numeral; the value returns as a numeral
    Char. The library is finite and inspectable; nothing proposes
    shapes from outside it.
    """

    def __init__(self, shape, fact):
        self.result = self._value(shape, fact)
        super().__init__(inputs=M.Pair(shape, M.Pair(fact, EmptyList)), results=self.result)

    def _arg(self, fact, index):
        if M.IsPair(fact)() is M.false_value:
            return None
        walk = Tail(fact)()
        position = 1
        while M.IsPair(walk)() is M.truth_value:
            if position == index:
                atom = Head(walk)()
                try:
                    text = atom()
                except Exception:
                    return None
                if text is None or not str(text).isdigit():
                    return None
                return int(str(text))
            walk = Tail(walk)()
            position += 1
        return None

    def _shape_number(self, term):
        try:
            text = term()
        except Exception:
            return None
        if text is None or not str(text).isdigit():
            return None
        return int(str(text))

    def _value(self, shape, fact):
        if M.IsPair(shape)() is M.false_value:
            return EmptyList
        head = Head(shape)()
        args = Tail(shape)()
        if M.IsPair(args)() is M.false_value:
            return EmptyList
        index = self._shape_number(Head(args)())
        if index is None:
            return EmptyList
        value = self._arg(fact, index)
        if value is None:
            return EmptyList
        if M.Compare(head, OBSERVABLE_PARITY)() is M.truth_value:
            return M.Char(str(value % 2))
        if M.Compare(head, OBSERVABLE_RESIDUE)() is M.truth_value:
            rest = Tail(args)()
            if M.IsPair(rest)() is M.false_value:
                return EmptyList
            k = self._shape_number(Head(rest)())
            if k is None or k < 2:
                return EmptyList
            return M.Char(str(value % k))
        return EmptyList

    def __call__(self):
        return self.result


def _observable_library():
    shapes = EmptyList
    for k in (3, 2):
        for index in (2, 1):
            shapes = M.Pair(
                M.Pair(OBSERVABLE_RESIDUE, M.Pair(M.Char(str(index)), M.Pair(M.Char(str(k)), EmptyList))),
                shapes,
            )
    for index in (2, 1):
        shapes = M.Pair(
            M.Pair(OBSERVABLE_PARITY, M.Pair(M.Char(str(index)), EmptyList)),
            shapes,
        )
    return shapes


OBSERVABLE_LIBRARY = _observable_library()


def conjecture_invariants(graph):
    """Survivors of the library against every fact of every trace.

    For each fact head appearing across at least two traces, an
    observable that takes one identical value on every fact with that
    head, in every trace state -- start facts and derived conclusions
    alike -- is a conjectured invariant:
    Pair(InvariantLabel, Pair(head, Pair(shape, Pair(value, EmptyList)))).
    Conjecture only; adoption is human-gated.
    """
    traces = TracesOnRecord(graph)()
    heads = EmptyList
    walk = traces
    while IdentityCompare(walk, EmptyList)() is M.false_value:
        trace = Head(walk)()
        walk = Tail(walk)()
        facts = _trace_facts(trace)
        inner = facts
        while IdentityCompare(inner, EmptyList)() is M.false_value:
            fact = Head(inner)()
            inner = Tail(inner)()
            if M.IsPair(fact)() is M.false_value:
                continue
            head = Head(fact)()
            if M.IsPair(head)() is M.truth_value:
                continue
            present = M.false_value
            seen = heads
            while IdentityCompare(seen, EmptyList)() is M.false_value:
                if M.Compare(Head(seen)(), head)() is M.truth_value:
                    present = M.truth_value
                    seen = EmptyList
                else:
                    seen = Tail(seen)()
            if IdentityCompare(present, M.false_value)() is M.truth_value:
                heads = M.Pair(head, heads)
    conjectures = EmptyList
    walk_heads = heads
    while IdentityCompare(walk_heads, EmptyList)() is M.false_value:
        head = Head(walk_heads)()
        walk_heads = Tail(walk_heads)()
        shapes = OBSERVABLE_LIBRARY
        while IdentityCompare(shapes, EmptyList)() is M.false_value:
            shape = Head(shapes)()
            shapes = Tail(shapes)()
            verdict = _shape_survives(traces, head, shape)
            if verdict is not None:
                record = M.Pair(
                    Lmod.InvariantLabel,
                    M.Pair(head, M.Pair(shape, M.Pair(verdict, EmptyList))),
                )
                conjectures = M.Pair(record, conjectures)
    return M.Reverse(conjectures)()


def _trace_facts(trace):
    start = Head(Tail(trace)())()
    fired = Head(Tail(Tail(Tail(trace)())())())()
    facts = start
    steps = StepInstances(fired)()
    while IdentityCompare(steps, EmptyList)() is M.false_value:
        facts = M.Pair(Head(Tail(Tail(Head(steps)())())())(), facts)
        steps = Tail(steps)()
    return facts


def _shape_survives(traces, head, shape):
    """One identical value across every matching fact of >= 2 traces."""
    value = None
    supporting_traces = 0
    total_facts = 0
    walk = traces
    while IdentityCompare(walk, EmptyList)() is M.false_value:
        trace = Head(walk)()
        walk = Tail(walk)()
        facts = _trace_facts(trace)
        seen_here = 0
        while IdentityCompare(facts, EmptyList)() is M.false_value:
            fact = Head(facts)()
            facts = Tail(facts)()
            if M.IsPair(fact)() is M.false_value:
                continue
            if M.Compare(Head(fact)(), head)() is M.false_value:
                continue
            observed = ObservableOnFact(shape, fact)()
            if IdentityCompare(observed, EmptyList)() is M.truth_value:
                return None
            if value is None:
                value = observed
            elif M.Compare(value, observed)() is M.false_value:
                return None
            seen_here += 1
            total_facts += 1
        if seen_here:
            supporting_traces += 1
    if value is None or supporting_traces < 2 or total_facts < 3:
        return None
    return value


def adopt_invariant(graph, record):
    """Human-gated adoption into learned memory.

    Invariant records live in the dependency_policies chain, so the
    learned-memory mask silences their prunes, and reset erases them --
    the same appear/disappear/reappear cycle as policy predictions.
    """
    graph.set_dependency_policies(M.Pair(record, graph.dependency_policies))
    graph.add_provenance(record, Lmod.InventedLemmaLabel)
    return record


class InvariantsOnRecord(Edge):
    def __init__(self, graph):
        self.result = self._walk(graph.dependency_policies)
        super().__init__(inputs=EmptyList, results=self.result)

    def _walk(self, chain):
        if IdentityCompare(chain, EmptyList)() is M.truth_value:
            return EmptyList
        entry = Head(chain)()
        rest = Tail(chain)()
        if M.IsPair(entry)() is M.truth_value:
            if IdentityCompare(Head(entry)(), Lmod.InvariantLabel)() is M.truth_value:
                return M.Pair(entry, self._walk(rest))
        return self._walk(rest)

    def __call__(self):
        return self.result


def invariant_prune(graph, goal_facts):
    """The adopted invariant a goal fact violates, or EmptyList.

    A goal whose observable disagrees with an adopted invariant is
    conjectured unreachable: search is skipped and the violated record
    is reported. Masked learned memory disables the prune entirely.
    """
    if learned_memory_enabled(graph) is M.false_value:
        return EmptyList
    invariants = InvariantsOnRecord(graph)()
    while IdentityCompare(invariants, EmptyList)() is M.false_value:
        record = Head(invariants)()
        invariants = Tail(invariants)()
        head = Head(Tail(record)())()
        shape = Head(Tail(Tail(record)())())()
        value = Head(Tail(Tail(Tail(record)())())())()
        goals = goal_facts
        while IdentityCompare(goals, EmptyList)() is M.false_value:
            goal_fact = Head(goals)()
            goals = Tail(goals)()
            if M.IsPair(goal_fact)() is M.false_value:
                continue
            if M.Compare(Head(goal_fact)(), head)() is M.false_value:
                continue
            observed = ObservableOnFact(shape, goal_fact)()
            if IdentityCompare(observed, EmptyList)() is M.truth_value:
                continue
            if M.Compare(observed, value)() is M.false_value:
                return record
    return EmptyList
