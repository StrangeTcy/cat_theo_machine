from . import labels as L
from . import machine as M


class Entity(M.Edge):
    def __init__(self, id_atom, canonical_name_atom, attributes_chain):
        self.result = M.Pair(
            L.EntityLabel,
            M.Pair(id_atom, M.Pair(canonical_name_atom, M.Pair(attributes_chain, M.EmptyList)))
        )
        super().__init__(
            inputs=M.Pair(id_atom, M.Pair(canonical_name_atom, M.Pair(attributes_chain, M.EmptyList))),
            results=self.result
        )

    def __call__(self):
        return self.result


class Role(M.Edge):
    def __init__(self, role_name_atom, entity_ref_atom):
        self.result = M.Pair(
            L.RoleLabel,
            M.Pair(role_name_atom, M.Pair(entity_ref_atom, M.EmptyList))
        )
        super().__init__(
            inputs=M.Pair(role_name_atom, M.Pair(entity_ref_atom, M.EmptyList)),
            results=self.result
        )

    def __call__(self):
        return self.result


class Event(M.Edge):
    def __init__(self, id_atom, predicate_atom, roles_chain, story_ref_atom):
        self.result = M.Pair(
            L.EventLabel,
            M.Pair(id_atom, M.Pair(predicate_atom, M.Pair(roles_chain, M.Pair(story_ref_atom, M.EmptyList))))
        )
        super().__init__(
            inputs=M.Pair(id_atom, M.Pair(predicate_atom, M.Pair(roles_chain, M.Pair(story_ref_atom, M.EmptyList)))),
            results=self.result
        )

    def __call__(self):
        return self.result


class Relation(M.Edge):
    def __init__(self, kind_atom, source_id_atom, target_id_atom, provenance_atom, confidence_atom):
        self.result = M.Pair(
            L.RelationLabel,
            M.Pair(
                kind_atom,
                M.Pair(
                    source_id_atom,
                    M.Pair(target_id_atom, M.Pair(provenance_atom, M.Pair(confidence_atom, M.EmptyList)))
                )
            )
        )
        super().__init__(
            inputs=M.Pair(
                kind_atom,
                M.Pair(source_id_atom, M.Pair(target_id_atom, M.Pair(provenance_atom, M.Pair(confidence_atom, M.EmptyList))))
            ),
            results=self.result
        )

    def __call__(self):
        return self.result


class Story(M.Edge):
    def __init__(self, id_atom, title_atom, event_chain):
        self.result = M.Pair(
            L.StoryLabel,
            M.Pair(id_atom, M.Pair(title_atom, M.Pair(event_chain, M.EmptyList)))
        )
        super().__init__(
            inputs=M.Pair(id_atom, M.Pair(title_atom, M.Pair(event_chain, M.EmptyList))),
            results=self.result
        )

    def __call__(self):
        return self.result


class IsEntity(M.Edge):
    def __init__(self, term):
        self.result = self._check(term)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def _check(self, term):
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.EntityLabel)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class IsRole(M.Edge):
    def __init__(self, term):
        self.result = self._check(term)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def _check(self, term):
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.RoleLabel)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class IsEvent(M.Edge):
    def __init__(self, term):
        self.result = self._check(term)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def _check(self, term):
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.EventLabel)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class IsRelation(M.Edge):
    def __init__(self, term):
        self.result = self._check(term)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def _check(self, term):
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.RelationLabel)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class IsStory(M.Edge):
    def __init__(self, term):
        self.result = self._check(term)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def _check(self, term):
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.StoryLabel)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class EntityId(M.Edge):
    def __init__(self, entity):
        self.result = M.Head(M.Tail(entity)())()
        super().__init__(inputs=M.Pair(entity, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntityCanonicalName(M.Edge):
    def __init__(self, entity):
        self.result = M.Head(M.Tail(M.Tail(entity)())())()
        super().__init__(inputs=M.Pair(entity, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EntityAttributes(M.Edge):
    def __init__(self, entity):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(entity)())())())()
        super().__init__(inputs=M.Pair(entity, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RoleName(M.Edge):
    def __init__(self, role):
        self.result = M.Head(M.Tail(role)())()
        super().__init__(inputs=M.Pair(role, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RoleEntityRef(M.Edge):
    def __init__(self, role):
        self.result = M.Head(M.Tail(M.Tail(role)())())()
        super().__init__(inputs=M.Pair(role, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventId(M.Edge):
    def __init__(self, event):
        self.result = M.Head(M.Tail(event)())()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventPredicate(M.Edge):
    def __init__(self, event):
        self.result = M.Head(M.Tail(M.Tail(event)())())()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventRoles(M.Edge):
    def __init__(self, event):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(event)())())())()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EventStoryRef(M.Edge):
    def __init__(self, event):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(event)())())())())()
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RelationKind(M.Edge):
    def __init__(self, relation):
        self.result = M.Head(M.Tail(relation)())()
        super().__init__(inputs=M.Pair(relation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RelationSource(M.Edge):
    def __init__(self, relation):
        self.result = M.Head(M.Tail(M.Tail(relation)())())()
        super().__init__(inputs=M.Pair(relation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RelationTarget(M.Edge):
    def __init__(self, relation):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(relation)())())())()
        super().__init__(inputs=M.Pair(relation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RelationProvenance(M.Edge):
    def __init__(self, relation):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(relation)())())())())()
        super().__init__(inputs=M.Pair(relation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RelationConfidence(M.Edge):
    def __init__(self, relation):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(relation)())())())())())()
        super().__init__(inputs=M.Pair(relation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryId(M.Edge):
    def __init__(self, story):
        self.result = M.Head(M.Tail(story)())()
        super().__init__(inputs=M.Pair(story, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryTitle(M.Edge):
    def __init__(self, story):
        self.result = M.Head(M.Tail(M.Tail(story)())())()
        super().__init__(inputs=M.Pair(story, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryEventChain(M.Edge):
    def __init__(self, story):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(story)())())())()
        super().__init__(inputs=M.Pair(story, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result
