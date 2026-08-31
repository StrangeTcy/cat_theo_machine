from __future__ import annotations

from . import machine as M
from . import labels as Lmod
from .core import Edge, EmptyList, Pair, Head, Tail, IdentityCompare

_research_enabled = M.false_value

def EnableResearchMode(graph=None):
    global _research_enabled
    _research_enabled = M.truth_value
    return M.truth_value

def DisableResearchMode(graph=None):
    global _research_enabled
    _research_enabled = M.false_value
    if graph is not None:
        graph._replace_context(research_mode=M.EmptyList)
    return M.false_value

def IsResearchMode(graph=None):
    if IdentityCompare(_research_enabled, M.truth_value)() is M.truth_value:
        return M.truth_value is M.truth_value
    if graph is not None:
        try:
            rm = graph.research_mode
            if IdentityCompare(rm, M.EmptyList)() is M.false_value:
                return M.truth_value is M.truth_value
        except Exception:
            pass
    return M.truth_value is M.false_value

def IsResearchModeEdgeValue(graph=None):
    if IsResearchMode(graph):
        return M.truth_value
    return M.false_value

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
        return ()

    def _make_request(self, parent_goal, residuals, blocking_condition, kind, formal_stmt, bridge_plan, assumptions, dep_id=None):
        ev = CounterfactualEvidence(M.Zero, M.Zero, M.EmptyList, M.EmptyList, M.EmptyList, M.false_value)()
        req = DependencyRequest(parent_goal, residuals, blocking_condition, kind, formal_stmt, bridge_plan, ev, assumptions, DependencyStatus.PENDING, Lmod.DependencyRequestProvenanceLabel, dep_id)()
        self.proposed = self.proposed + 1
        return req

class GenMissingOperation(GenBase):
    def __init__(self):
        super().__init__(Lmod.GenMissingOperationLabel)
    def propose(self, parent_goal, residuals, blocking_condition, graph):
        formal = M.Pair(Lmod.FormalStatementLabel, M.Pair(M.Atom(), M.EmptyList))
        bridge = M.Pair(Lmod.BridgePlanLabel, M.Pair(M.Atom(), M.EmptyList))
        assumptions = M.EmptyList
        req = self._make_request(parent_goal, residuals, blocking_condition, DependencyKind.DOMAIN_PROPERTY, formal, bridge, assumptions)
        return (req,)

class GenProperExponentReduction(GenBase):
    def __init__(self):
        super().__init__(Lmod.GenProperExponentReductionLabel)
    def propose(self, parent_goal, residuals, blocking_condition, graph):
        formal = M.Pair(Lmod.FormalStatementLabel, M.Pair(M.Pair(Lmod.ExprPowLabel, M.Pair(M.Atom(), M.EmptyList)), M.EmptyList))
        bridge = M.Pair(Lmod.BridgePlanLabel, M.Pair(M.Atom(), M.EmptyList))
        req = self._make_request(parent_goal, residuals, blocking_condition, DependencyKind.THEOREM, formal, bridge, M.EmptyList)
        return (req,)

class GenRepresentationShift(GenBase):
    def __init__(self):
        super().__init__(Lmod.GenRepresentationShiftLabel)
    def propose(self, parent_goal, residuals, blocking_condition, graph):
        formal = M.Pair(Lmod.FormalStatementLabel, M.Pair(M.Atom(), M.EmptyList))
        bridge = M.Pair(Lmod.BridgePlanLabel, M.Pair(M.Atom(), M.EmptyList))
        req = self._make_request(parent_goal, residuals, blocking_condition, DependencyKind.REPRESENTATION, formal, bridge, M.EmptyList)
        return (req,)

class GenAuxiliaryObject(GenBase):
    def __init__(self):
        super().__init__(Lmod.GenAuxiliaryObjectLabel)
    def propose(self, parent_goal, residuals, blocking_condition, graph):
        formal = M.Pair(Lmod.FormalStatementLabel, M.Pair(M.Atom(), M.EmptyList))
        bridge = M.Pair(Lmod.BridgePlanLabel, M.Pair(M.Atom(), M.EmptyList))
        req = self._make_request(parent_goal, residuals, blocking_condition, DependencyKind.OBJECT, formal, bridge, M.EmptyList)
        return (req,)

class GenLemmaIntroduction(GenBase):
    def __init__(self):
        super().__init__(Lmod.GenLemmaIntroductionLabel)
    def propose(self, parent_goal, residuals, blocking_condition, graph):
        formal = M.Pair(Lmod.FormalStatementLabel, M.Pair(M.Atom(), M.EmptyList))
        bridge = M.Pair(Lmod.BridgePlanLabel, M.Pair(M.Atom(), M.EmptyList))
        req = self._make_request(parent_goal, residuals, blocking_condition, DependencyKind.THEOREM, formal, bridge, M.EmptyList)
        return (req,)

class GenTransformationSearch(GenBase):
    def __init__(self):
        super().__init__(Lmod.GenTransformationSearchLabel)
    def propose(self, parent_goal, residuals, blocking_condition, graph):
        formal = M.Pair(Lmod.FormalStatementLabel, M.Pair(M.Atom(), M.EmptyList))
        bridge = M.Pair(Lmod.BridgePlanLabel, M.Pair(M.Atom(), M.EmptyList))
        req = self._make_request(parent_goal, residuals, blocking_condition, DependencyKind.TRANSFORMATION, formal, bridge, M.EmptyList)
        return (req,)

class GenTacticEnhancement(GenBase):
    def __init__(self):
        super().__init__(Lmod.GenTacticEnhancementLabel)
    def propose(self, parent_goal, residuals, blocking_condition, graph):
        formal = M.Pair(Lmod.FormalStatementLabel, M.Pair(M.Atom(), M.EmptyList))
        bridge = M.Pair(Lmod.BridgePlanLabel, M.Pair(M.Atom(), M.EmptyList))
        req = self._make_request(parent_goal, residuals, blocking_condition, DependencyKind.TACTIC, formal, bridge, M.EmptyList)
        return (req,)

ALL_GENERATORS = (
    GenMissingOperation(),
    GenProperExponentReduction(),
    GenRepresentationShift(),
    GenAuxiliaryObject(),
    GenLemmaIntroduction(),
    GenTransformationSearch(),
    GenTacticEnhancement(),
)

def get_generator_by_label(label):
    idx = 0
    while idx != 100:
        try:
            g = ALL_GENERATORS[idx]
        except Exception:
            break
        if IdentityCompare(g.gen_label, label)() is M.truth_value:
            return g
        idx = idx + 1
    return M.EmptyList

def _append_pair_to_chain(chain, elem):
    return M.Pair(elem, chain)

def _reverse_chain(chain):
    acc = M.EmptyList
    cur = chain
    while IdentityCompare(cur, M.EmptyList)() is M.false_value:
        acc = M.Pair(M.Head(cur)(), acc)
        cur = M.Tail(cur)()
    return acc

def _count_chain(chain):
    cnt = 0
    cur = chain
    while IdentityCompare(cur, M.EmptyList)() is M.false_value:
        cnt = cnt + 1
        cur = M.Tail(cur)()
        if cnt > 10000:
            break
    return cnt

def suggest_dependencies(parent_goal, residuals, blocking_condition, graph):
    results_chain = M.EmptyList
    idx = 0
    while idx != 100:
        try:
            gen = ALL_GENERATORS[idx]
        except Exception:
            break
        try:
            props = gen.propose(parent_goal, residuals, blocking_condition, graph)
            p_idx = 0
            p_len = 0
            counting = 1
            while counting == 1:
                try:
                    _ = props[p_len]
                    p_len = p_len + 1
                    if p_len > 100:
                        counting = 0
                except Exception:
                    counting = 0
            while p_idx != p_len:
                r = props[p_idx]
                if validate_dependency_request(r, parent_goal) is (M.truth_value is M.false_value):
                    gen.rejected = gen.rejected + 1
                else:
                    results_chain = M.Pair(M.Pair(gen, M.Pair(r, M.EmptyList)), results_chain)
                p_idx = p_idx + 1
        except Exception:
            pass
        idx = idx + 1
    results_chain = _reverse_chain(results_chain)
    py_results = []
    cur = results_chain
    while IdentityCompare(cur, M.EmptyList)() is M.false_value:
        pair = M.Head(cur)()
        gen = M.Head(pair)()
        req = M.Head(M.Tail(pair)())()
        py_results.append((gen, req))
        try:
            graph._replace_context(dependency_requests=M.Pair(req, graph.dependency_requests))
            dep_id = DependencyRequestId(req)()
            gdd = GoalDependsOnDependency(parent_goal, dep_id)()
            graph._replace_context(dependency_graph=M.Pair(gdd, graph.dependency_graph))
        except Exception:
            pass
        cur = M.Tail(cur)()
    return py_results

def validate_dependency_request(req, parent_goal):
    try:
        formal = DependencyRequestFormalStatement(req)()
        if M.TermEqual(formal, parent_goal)() is M.truth_value:
            return M.truth_value is M.false_value
        cur = formal
        while IdentityCompare(cur, M.EmptyList)() is M.false_value:
            h = Head(cur)()
            if M.TermEqual(h, parent_goal)() is M.truth_value:
                return M.truth_value is M.false_value
            if M.IsPair(h)() is M.truth_value:
                try:
                    inner = Head(h)()
                    if M.TermEqual(inner, parent_goal)() is M.truth_value:
                        return M.truth_value is M.false_value
                except Exception:
                    pass
            cur = Tail(cur)()
        bridge = DependencyRequestBridgePlan(req)()
        if IdentityCompare(bridge, M.EmptyList)() is M.truth_value:
            return M.truth_value is M.false_value
        blocking = DependencyRequestBlockingCondition(req)()
        if M.IsPair(blocking)() is M.truth_value:
            if M.TermEqual(M.Head(blocking)(), Lmod.ContradictionLabel)() is M.truth_value:
                if M.TermEqual(formal, blocking)() is M.truth_value:
                    return M.truth_value is M.false_value
        return M.truth_value is M.truth_value
    except Exception:
        return M.truth_value is M.truth_value

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

def evaluate_unlock(useful_condition, goal_closed, cost_before, cost_after):
    if goal_closed is M.truth_value:
        return M.truth_value is M.truth_value
    return M.truth_value is M.false_value

def store_dependency_request(graph, req):
    graph._replace_context(dependency_requests=M.Pair(req, graph.dependency_requests))
    return req

def approve_dependency(graph, dep_id):
    new_chain = M.EmptyList
    cur = graph.dependency_requests
    approved_req = M.EmptyList
    while IdentityCompare(cur, M.EmptyList)() is M.false_value:
        req = Head(cur)()
        rid = DependencyRequestId(req)()
        if M.TermEqual(rid, dep_id)() is M.truth_value:
            parent = DependencyRequestParentGoal(req)()
            residuals = DependencyRequestResiduals(req)()
            blocking = DependencyRequestBlockingCondition(req)()
            kind = DependencyRequestKind(req)()
            formal = DependencyRequestFormalStatement(req)()
            bridge = DependencyRequestBridgePlan(req)()
            counter = DependencyRequestCounterfactual(req)()
            assumptions = DependencyRequestAssumptions(req)()
            prov = DependencyRequestProvenance(req)()
            new_req = DependencyRequest(parent, residuals, blocking, kind, formal, bridge, counter, assumptions, DependencyStatus.APPROVED, prov, dep_id)()
            new_chain = M.Pair(new_req, new_chain)
            approved_req = new_req
        else:
            new_chain = M.Pair(req, new_chain)
        cur = Tail(cur)()
    graph._replace_context(dependency_requests=_reverse_chain(new_chain))
    return approved_req

def reject_dependency(graph, dep_id):
    new_chain = M.EmptyList
    cur = graph.dependency_requests
    while IdentityCompare(cur, M.EmptyList)() is M.false_value:
        req = Head(cur)()
        rid = DependencyRequestId(req)()
        if M.TermEqual(rid, dep_id)() is M.truth_value:
            parent = DependencyRequestParentGoal(req)()
            residuals = DependencyRequestResiduals(req)()
            blocking = DependencyRequestBlockingCondition(req)()
            kind = DependencyRequestKind(req)()
            formal = DependencyRequestFormalStatement(req)()
            bridge = DependencyRequestBridgePlan(req)()
            counter = DependencyRequestCounterfactual(req)()
            assumptions = DependencyRequestAssumptions(req)()
            prov = DependencyRequestProvenance(req)()
            new_req = DependencyRequest(parent, residuals, blocking, kind, formal, bridge, counter, assumptions, DependencyStatus.REJECTED, prov, dep_id)()
            new_chain = M.Pair(new_req, new_chain)
        else:
            new_chain = M.Pair(req, new_chain)
        cur = Tail(cur)()
    graph._replace_context(dependency_requests=_reverse_chain(new_chain))

def refine_dependency(graph, dep_id, new_formal):
    new_chain = M.EmptyList
    cur = graph.dependency_requests
    refined_req = M.EmptyList
    while IdentityCompare(cur, M.EmptyList)() is M.false_value:
        req = Head(cur)()
        rid = DependencyRequestId(req)()
        if M.TermEqual(rid, dep_id)() is M.truth_value:
            parent = DependencyRequestParentGoal(req)()
            residuals = DependencyRequestResiduals(req)()
            blocking = DependencyRequestBlockingCondition(req)()
            kind = DependencyRequestKind(req)()
            bridge = DependencyRequestBridgePlan(req)()
            counter = DependencyRequestCounterfactual(req)()
            assumptions = DependencyRequestAssumptions(req)()
            prov = DependencyRequestProvenance(req)()
            new_req = DependencyRequest(parent, residuals, blocking, kind, new_formal, bridge, counter, assumptions, DependencyStatus.REFINED, prov, dep_id)()
            new_chain = M.Pair(new_req, new_chain)
            refined_req = new_req
        else:
            new_chain = M.Pair(req, new_chain)
        cur = Tail(cur)()
    graph._replace_context(dependency_requests=_reverse_chain(new_chain))
    return refined_req

def teach_trusted_theorem(graph, theorem_term):
    graph._replace_context(nodes=M.Pair(theorem_term, graph.nodes))
    entry = M.Pair(theorem_term, M.Pair(Lmod.HumanSuppliedTrustedTheoremLabel, M.EmptyList))
    graph._replace_context(provenance_map=M.Pair(entry, graph.provenance_map))
    return theorem_term

def define_symbolic_object(graph, object_term):
    graph._replace_context(nodes=M.Pair(object_term, graph.nodes))
    entry = M.Pair(object_term, M.Pair(Lmod.InventedObjectLabel, M.EmptyList))
    graph._replace_context(provenance_map=M.Pair(entry, graph.provenance_map))
    return object_term

def teach_law(graph, law_term):
    graph._replace_context(edges=M.Pair(law_term, graph.edges))
    entry = M.Pair(law_term, M.Pair(Lmod.HumanSuppliedTrustedTheoremLabel, M.EmptyList))
    graph._replace_context(provenance_map=M.Pair(entry, graph.provenance_map))
    return law_term

def show_dependency_graph(graph):
    result = []
    cur = graph.dependency_graph
    while IdentityCompare(cur, M.EmptyList)() is M.false_value:
        entry = Head(cur)()
        try:
            goal = Head(Tail(entry)())()
            dep_id = Head(Tail(Tail(entry)())())()
            status = Lmod.PendingStatusLabel
            req_cur = graph.dependency_requests
            while IdentityCompare(req_cur, M.EmptyList)() is M.false_value:
                req = Head(req_cur)()
                rid = DependencyRequestId(req)()
                if M.TermEqual(rid, dep_id)() is M.truth_value:
                    status = DependencyRequestStatus(req)()
                    break
                req_cur = Tail(req_cur)()
            result.append((goal, dep_id, status))
        except Exception:
            pass
        cur = Tail(cur)()
    return result

def audit_knowledge(graph):
    result = []
    cur = graph.provenance_map
    while IdentityCompare(cur, M.EmptyList)() is M.false_value:
        entry = Head(cur)()
        try:
            term = Head(entry)()
            prov = Head(Tail(entry)())()
            result.append((term, prov))
        except Exception:
            pass
        cur = Tail(cur)()
    return result

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

def update_generator_metrics(graph, gen_label, approved=0, useful=0, used=0, cost_reduction=0):
    new_chain = M.EmptyList
    found = 0
    cur = graph.generator_metrics
    while IdentityCompare(cur, M.EmptyList)() is M.false_value:
        stats = Head(cur)()
        try:
            gid = Head(Tail(stats)())()
            if IdentityCompare(gid, gen_label)() is M.truth_value:
                found = 1
                new_chain = M.Pair(stats, new_chain)
            else:
                new_chain = M.Pair(stats, new_chain)
        except Exception:
            new_chain = M.Pair(stats, new_chain)
        cur = Tail(cur)()
    if found == 0:
        gen = get_generator_by_label(gen_label)
        is_empty = 0
        if gen is M.EmptyList:
            is_empty = 1
        if is_empty == 0:
            try:
                proposed = M.GMPRep(str(gen.proposed))
                approved_v = M.GMPRep(str(gen.approved))
                rejected_v = M.GMPRep(str(gen.rejected))
                useful_v = M.GMPRep(str(gen.useful))
                used_v = M.GMPRep(str(gen.used))
                mean_v = M.GMPRep(str(int(gen.mean_cost_reduction)))
                reuse_v = M.GMPRep(str(gen.reuse))
                stats = GeneratorStats(gen_label, proposed, approved_v, rejected_v, useful_v, used_v, mean_v, reuse_v)()
                new_chain = M.Pair(stats, new_chain)
            except Exception:
                pass
    graph._replace_context(generator_metrics=_reverse_chain(new_chain))
