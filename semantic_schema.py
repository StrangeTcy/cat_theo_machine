from . import machine as M
from . import labels as L

# General semantic layer: Goal, TaskType, Concept, Intermediate, Connection, etc.
# All pair-only Edge subclasses, compliant with substrate rules.

class Concept(M.Edge):
    def __init__(self, concept_id, canonical_name, concept_type, attributes, provenance):
        self.result = M.Pair(L.ConceptLabel, M.Pair(concept_id, M.Pair(canonical_name, M.Pair(concept_type, M.Pair(attributes, M.Pair(provenance, M.EmptyList))))))
        super().__init__(inputs=M.Pair(concept_id, M.Pair(canonical_name, M.Pair(concept_type, M.Pair(attributes, M.Pair(provenance, M.EmptyList))))), results=self.result)
    def __call__(self):
        return self.result

class IsConcept(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.ConceptLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ConceptId(M.Edge):
    def __init__(self, concept):
        self.result = M.Head(M.Tail(concept)())()
        super().__init__(inputs=M.Pair(concept, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ConceptCanonicalName(M.Edge):
    def __init__(self, concept):
        self.result = M.Head(M.Tail(M.Tail(concept)())())()
        super().__init__(inputs=M.Pair(concept, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ConceptType(M.Edge):
    def __init__(self, concept):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(concept)())())())()
        super().__init__(inputs=M.Pair(concept, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ConceptAttributes(M.Edge):
    def __init__(self, concept):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(concept)())())())())()
        super().__init__(inputs=M.Pair(concept, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class Intermediate(M.Edge):
    def __init__(self, inter_id, canonical_name, connects, verification, confidence, provenance):
        self.result = M.Pair(L.IntermediateLabel, M.Pair(inter_id, M.Pair(canonical_name, M.Pair(connects, M.Pair(verification, M.Pair(confidence, M.Pair(provenance, M.EmptyList)))))))
        super().__init__(inputs=M.Pair(inter_id, M.Pair(canonical_name, M.Pair(connects, M.Pair(verification, M.Pair(confidence, M.Pair(provenance, M.EmptyList)))))), results=self.result)
    def __call__(self):
        return self.result

class IsIntermediate(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.IntermediateLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class IntermediateId(M.Edge):
    def __init__(self, inter):
        self.result = M.Head(M.Tail(inter)())()
        super().__init__(inputs=M.Pair(inter, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class IntermediateCanonicalName(M.Edge):
    def __init__(self, inter):
        self.result = M.Head(M.Tail(M.Tail(inter)())())()
        super().__init__(inputs=M.Pair(inter, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class IntermediateConnects(M.Edge):
    def __init__(self, inter):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(inter)())())())()
        super().__init__(inputs=M.Pair(inter, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class IntermediateVerification(M.Edge):
    def __init__(self, inter):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(inter)())())())())()
        super().__init__(inputs=M.Pair(inter, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class IntermediateConfidence(M.Edge):
    def __init__(self, inter):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(inter)())())())())())()
        super().__init__(inputs=M.Pair(inter, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SemanticGoal(M.Edge):
    def __init__(self, goal_id, task_type, concepts, raw_utterance, provenance):
        self.result = M.Pair(L.SemanticGoalLabel, M.Pair(goal_id, M.Pair(task_type, M.Pair(concepts, M.Pair(raw_utterance, M.Pair(provenance, M.EmptyList))))))
        super().__init__(inputs=M.Pair(goal_id, M.Pair(task_type, M.Pair(concepts, M.Pair(raw_utterance, M.Pair(provenance, M.EmptyList))))), results=self.result)
    def __call__(self):
        return self.result

class IsSemanticGoal(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.SemanticGoalLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SemanticGoalId(M.Edge):
    def __init__(self, goal):
        self.result = M.Head(M.Tail(goal)())()
        super().__init__(inputs=M.Pair(goal, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SemanticGoalTaskType(M.Edge):
    def __init__(self, goal):
        self.result = M.Head(M.Tail(M.Tail(goal)())())()
        super().__init__(inputs=M.Pair(goal, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SemanticGoalConcepts(M.Edge):
    def __init__(self, goal):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(goal)())())())()
        super().__init__(inputs=M.Pair(goal, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class TaskType(M.Edge):
    def __init__(self, type_name):
        self.result = M.Pair(L.TaskTypeLabel, M.Pair(type_name, M.EmptyList))
        super().__init__(inputs=M.Pair(type_name, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class IsTaskType(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.TaskTypeLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class TaskTypeName(M.Edge):
    def __init__(self, task_type):
        self.result = M.Head(M.Tail(task_type)())()
        super().__init__(inputs=M.Pair(task_type, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class Connection(M.Edge):
    def __init__(self, conn_id, source, target, via, verification, confidence):
        self.result = M.Pair(L.ConnectionLabel, M.Pair(conn_id, M.Pair(source, M.Pair(target, M.Pair(via, M.Pair(verification, M.Pair(confidence, M.EmptyList)))))))
        super().__init__(inputs=M.Pair(conn_id, M.Pair(source, M.Pair(target, M.Pair(via, M.Pair(verification, M.Pair(confidence, M.EmptyList)))))), results=self.result)
    def __call__(self):
        return self.result

class IsConnection(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.ConnectionLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ConnectionSource(M.Edge):
    def __init__(self, conn):
        self.result = M.Head(M.Tail(M.Tail(conn)())())()
        super().__init__(inputs=M.Pair(conn, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ConnectionTarget(M.Edge):
    def __init__(self, conn):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(conn)())())())()
        super().__init__(inputs=M.Pair(conn, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ConnectionVia(M.Edge):
    def __init__(self, conn):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(conn)())())())())()
        super().__init__(inputs=M.Pair(conn, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ConnectionVerification(M.Edge):
    def __init__(self, conn):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(conn)())())())())())()
        super().__init__(inputs=M.Pair(conn, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ConnectionConfidence(M.Edge):
    def __init__(self, conn):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(conn)())())())())())())()
        super().__init__(inputs=M.Pair(conn, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class Verification(M.Edge):
    def __init__(self, ver_id, status, evidence):
        self.result = M.Pair(L.VerificationLabel, M.Pair(ver_id, M.Pair(status, M.Pair(evidence, M.EmptyList))))
        super().__init__(inputs=M.Pair(ver_id, M.Pair(status, M.Pair(evidence, M.EmptyList))), results=self.result)
    def __call__(self):
        return self.result

class IsVerification(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.VerificationLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class VerificationStatus(M.Edge):
    def __init__(self, ver):
        self.result = M.Head(M.Tail(M.Tail(ver)())())()
        super().__init__(inputs=M.Pair(ver, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SemanticState(M.Edge):
    def __init__(self, state_id, current_goal, discovered_connections, invented_intermediates, narrative_focus, provenance):
        self.result = M.Pair(L.SemanticStateLabel, M.Pair(state_id, M.Pair(current_goal, M.Pair(discovered_connections, M.Pair(invented_intermediates, M.Pair(narrative_focus, M.Pair(provenance, M.EmptyList)))))))
        super().__init__(inputs=M.Pair(state_id, M.Pair(current_goal, M.Pair(discovered_connections, M.Pair(invented_intermediates, M.Pair(narrative_focus, M.Pair(provenance, M.EmptyList)))))), results=self.result)
    def __call__(self):
        return self.result

class IsSemanticState(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.SemanticStateLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SemanticStateGoal(M.Edge):
    def __init__(self, state):
        self.result = M.Head(M.Tail(M.Tail(state)())())()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SemanticStateConnections(M.Edge):
    def __init__(self, state):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(state)())())())()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SemanticStateIntermediates(M.Edge):
    def __init__(self, state):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(state)())())())())()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SemanticStateFocus(M.Edge):
    def __init__(self, state):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(state)())())())())())()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

# Utility: extract chain helpers as Edge classes for graph reasoning

class ExtractConceptsFromNodes(M.Edge):
    def __init__(self, nodes):
        self.result = self._extract(nodes)
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)
    def _extract(self, nodes):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        head = M.Head(nodes)()
        tail_result = self._extract(M.Tail(nodes)())
        if IsConcept(head)() is M.truth_value:
            return M.Pair(head, tail_result)
        if IsIntermediate(head)() is M.truth_value:
            return M.Pair(head, tail_result)
        return tail_result
    def __call__(self):
        return self.result

class ExtractConnectionsFromNodes(M.Edge):
    def __init__(self, nodes):
        self.result = self._extract(nodes)
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)
    def _extract(self, nodes):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        head = M.Head(nodes)()
        tail_result = self._extract(M.Tail(nodes)())
        if IsConnection(head)() is M.truth_value:
            return M.Pair(head, tail_result)
        return tail_result
    def __call__(self):
        return self.result
