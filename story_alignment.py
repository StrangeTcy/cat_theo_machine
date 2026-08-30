from . import labels as L
from . import machine as M
from . import graph as G
from .story_schema import Entity, Role, Event, Relation, Story, IsEntity, IsRelation, IsEvent, EntityId, EntityCanonicalName, EventId, EventPredicate, EventRoles, RelationKind, RelationSource, RelationTarget, RoleName, RoleEntityRef


class IsSameEntityCandidate(M.Edge):
    def __init__(self, entity_a, entity_b):
        self.result = self._check(entity_a, entity_b)
        super().__init__(inputs=M.Pair(entity_a, M.Pair(entity_b, M.EmptyList)), results=self.result)

    def _check(self, a, b):
        name_a = EntityCanonicalName(a)()
        name_b = EntityCanonicalName(b)()
        if M.TermEqual(name_a, name_b)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class SameAsRelation(M.Edge):
    def __init__(self, source_id, target_id, provenance, confidence):
        self.result = Relation(M.Char("same-as"), source_id, target_id, provenance, confidence)()
        super().__init__(inputs=M.Pair(source_id, M.Pair(target_id, M.Pair(provenance, M.Pair(confidence, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class ProposeEntityLink(M.Edge):
    def __init__(self, entity_a, entity_b, provenance, confidence):
        self.result = self._propose(entity_a, entity_b, provenance, confidence)
        super().__init__(inputs=M.Pair(entity_a, M.Pair(entity_b, M.Pair(provenance, M.Pair(confidence, M.EmptyList)))), results=self.result)

    def _propose(self, a, b, prov, conf):
        if IsSameEntityCandidate(a, b)() is M.truth_value:
            id_a = EntityId(a)()
            id_b = EntityId(b)()
            return SameAsRelation(id_a, id_b, prov, conf)()
        return M.EmptyList

    def __call__(self):
        return self.result


class ExtractEntitiesFromNodes(M.Edge):
    def __init__(self, node_chain):
        self.result = self._extract(node_chain, M.EmptyList)
        super().__init__(inputs=M.Pair(node_chain, M.EmptyList), results=self.result)

    def _extract(self, remaining, acc):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return acc
        term = M.Head(remaining)()
        rest = M.Tail(remaining)()
        if IsEntity(term)() is M.truth_value:
            acc = M.Pair(term, acc)
        return self._extract(rest, acc)

    def __call__(self):
        return self.result


class ExtractEventsFromNodes(M.Edge):
    def __init__(self, node_chain):
        self.result = self._extract(node_chain, M.EmptyList)
        super().__init__(inputs=M.Pair(node_chain, M.EmptyList), results=self.result)

    def _extract(self, remaining, acc):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return acc
        term = M.Head(remaining)()
        rest = M.Tail(remaining)()
        if IsEvent(term)() is M.truth_value:
            acc = M.Pair(term, acc)
        return self._extract(rest, acc)

    def __call__(self):
        return self.result


class ExtractRelationsFromNodes(M.Edge):
    def __init__(self, node_chain):
        self.result = self._extract(node_chain, M.EmptyList)
        super().__init__(inputs=M.Pair(node_chain, M.EmptyList), results=self.result)

    def _extract(self, remaining, acc):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return acc
        term = M.Head(remaining)()
        rest = M.Tail(remaining)()
        if IsRelation(term)() is M.truth_value:
            acc = M.Pair(term, acc)
        return self._extract(rest, acc)

    def __call__(self):
        return self.result


class BuildGraphVersion(M.Edge):
    def __init__(self, node_chain):
        self.result = G.GraphVersion(node_chain, M.EmptyList, M.EmptyList)()
        super().__init__(inputs=M.Pair(node_chain, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AddRelationsToGraphVersion(M.Edge):
    def __init__(self, graph_version, new_relations_chain):
        self.result = self._add(graph_version, new_relations_chain)
        super().__init__(inputs=M.Pair(graph_version, M.Pair(new_relations_chain, M.EmptyList)), results=self.result)

    def _add(self, gv, new_rels):
        nodes = G.GraphNodes(gv)()
        combined = self._append_chain(new_rels, nodes)
        return G.GraphVersion(combined, G.GraphEdges(gv)(), G.GraphVersionInvariants(gv)())()

    def _append_chain(self, a_chain, b_chain):
        if M.IdentityCompare(a_chain, M.EmptyList)() is M.truth_value:
            return b_chain
        head = M.Head(a_chain)()
        tail = M.Tail(a_chain)()
        rest_appended = self._append_chain(tail, b_chain)
        return M.Pair(head, rest_appended)

    def __call__(self):
        return self.result


class DirectRelationExists(M.Edge):
    def __init__(self, relation_chain, source_id, target_id):
        self.result = self._check(relation_chain, source_id, target_id)
        super().__init__(inputs=M.Pair(relation_chain, M.Pair(source_id, M.Pair(target_id, M.EmptyList))), results=self.result)

    def _check(self, chain, src, tgt):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        rel = M.Head(chain)()
        rest = M.Tail(chain)()
        rel_src = RelationSource(rel)()
        rel_tgt = RelationTarget(rel)()
        if M.TermEqual(rel_src, src)() is M.truth_value:
            if M.TermEqual(rel_tgt, tgt)() is M.truth_value:
                return M.truth_value
        if M.TermEqual(rel_src, tgt)() is M.truth_value:
            if M.TermEqual(rel_tgt, src)() is M.truth_value:
                return M.truth_value
        return self._check(rest, src, tgt)

    def __call__(self):
        return self.result


class EventRoleSignatureMatch(M.Edge):
    def __init__(self, event_a, event_b):
        self.result = self._match(event_a, event_b)
        super().__init__(inputs=M.Pair(event_a, M.Pair(event_b, M.EmptyList)), results=self.result)

    def _match(self, a, b):
        pred_a = EventPredicate(a)()
        pred_b = EventPredicate(b)()
        if M.TermEqual(pred_a, pred_b)() is M.false_value:
            return M.false_value
        roles_a = EventRoles(a)()
        roles_b = EventRoles(b)()
        return self._roles_match(roles_a, roles_b)

    def _roles_match(self, ra, rb):
        if M.IdentityCompare(ra, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(rb, M.EmptyList)() is M.truth_value:
                return M.truth_value
            return M.false_value
        if M.IdentityCompare(rb, M.EmptyList)() is M.truth_value:
            return M.false_value
        role_a = M.Head(ra)()
        role_b = M.Head(rb)()
        name_a = RoleName(role_a)()
        name_b = RoleName(role_b)()
        if M.TermEqual(name_a, name_b)() is M.false_value:
            return M.false_value
        return self._roles_match(M.Tail(ra)(), M.Tail(rb)())

    def __call__(self):
        return self.result


class FindAnalogyMapping(M.Edge):
    def __init__(self, event_chain_a, event_chain_b):
        self.result = self._compare(event_chain_a, event_chain_b)
        super().__init__(inputs=M.Pair(event_chain_a, M.Pair(event_chain_b, M.EmptyList)), results=self.result)

    def _compare(self, chain_a, chain_b):
        if M.IdentityCompare(chain_a, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(chain_b, M.EmptyList)() is M.truth_value:
                return M.truth_value
            return M.false_value
        if M.IdentityCompare(chain_b, M.EmptyList)() is M.truth_value:
            return M.false_value
        ev_a = M.Head(chain_a)()
        ev_b = M.Head(chain_b)()
        if EventRoleSignatureMatch(ev_a, ev_b)() is M.false_value:
            return M.false_value
        return self._compare(M.Tail(chain_a)(), M.Tail(chain_b)())

    def __call__(self):
        return self.result


class FindConnectionPath(M.Edge):
    def __init__(self, graph_version, source_id, target_id):
        self.result = self._search(graph_version, source_id, target_id, M.EmptyList)
        super().__init__(inputs=M.Pair(graph_version, M.Pair(source_id, M.Pair(target_id, M.EmptyList))), results=self.result)

    def _search(self, gv, current, target, visited):
        if M.TermEqual(current, target)() is M.truth_value:
            return M.Pair(current, M.EmptyList)
        if self._is_visited(visited, current) is M.truth_value:
            return M.EmptyList
        new_visited = M.Pair(current, visited)
        neighbors = self._neighbors(gv, current)
        return self._search_neighbors(gv, neighbors, target, new_visited, current)

    def _is_visited(self, visited_chain, node_id):
        if M.IdentityCompare(visited_chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        head = M.Head(visited_chain)()
        if M.TermEqual(head, node_id)() is M.truth_value:
            return M.truth_value
        return self._is_visited(M.Tail(visited_chain)(), node_id)

    def _neighbors(self, gv, node_id):
        nodes = G.GraphNodes(gv)()
        rels = ExtractRelationsFromNodes(nodes)()
        return self._collect_neighbors(rels, node_id, M.EmptyList)

    def _collect_neighbors(self, rel_chain, node_id, acc):
        if M.IdentityCompare(rel_chain, M.EmptyList)() is M.truth_value:
            return acc
        rel = M.Head(rel_chain)()
        rest = M.Tail(rel_chain)()
        src = RelationSource(rel)()
        tgt = RelationTarget(rel)()
        if M.TermEqual(src, node_id)() is M.truth_value:
            acc = M.Pair(tgt, acc)
        if M.TermEqual(tgt, node_id)() is M.truth_value:
            acc = M.Pair(src, acc)
        return self._collect_neighbors(rest, node_id, acc)

    def _search_neighbors(self, gv, neighbor_chain, target, visited, current):
        if M.IdentityCompare(neighbor_chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        neighbor = M.Head(neighbor_chain)()
        rest = M.Tail(neighbor_chain)()
        path = self._search(gv, neighbor, target, visited)
        if M.IdentityCompare(path, M.EmptyList)() is M.false_value:
            return M.Pair(current, path)
        return self._search_neighbors(gv, rest, target, visited, current)

    def __call__(self):
        return self.result


class InduceSchema(M.Edge):
    def __init__(self, event_chain_a, event_chain_b):
        self.result = self._induce(event_chain_a, event_chain_b)
        super().__init__(inputs=M.Pair(event_chain_a, M.Pair(event_chain_b, M.EmptyList)), results=self.result)

    def _induce(self, chain_a, chain_b):
        if FindAnalogyMapping(chain_a, chain_b)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result
