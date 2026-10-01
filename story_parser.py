from . import labels as L
from . import machine as M
from .story_schema import Entity, Role, Event, Relation, Story


class WordIsThen(M.Edge):
    def __init__(self, word):
        self.result = self._check(word)
        super().__init__(inputs=M.Pair(word, M.EmptyList), results=self.result)

    def _check(self, word):
        if M.Compare(word, M.Char("then"))() is M.truth_value:
            return M.truth_value
        if M.Compare(word, M.Char("Then"))() is M.truth_value:
            return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class WordIsBecause(M.Edge):
    def __init__(self, word):
        self.result = self._check(word)
        super().__init__(inputs=M.Pair(word, M.EmptyList), results=self.result)

    def _check(self, word):
        if M.Compare(word, M.Char("because"))() is M.truth_value:
            return M.truth_value
        if M.Compare(word, M.Char("Because"))() is M.truth_value:
            return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class ParseSVOToRoles(M.Edge):
    def __init__(self, word_chain):
        self.result = self._parse(word_chain)
        super().__init__(inputs=M.Pair(word_chain, M.EmptyList), results=self.result)

    def _parse(self, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        subj = M.Head(chain)()
        rest1 = M.Tail(chain)()
        if M.IdentityCompare(rest1, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        verb = M.Head(rest1)()
        rest2 = M.Tail(rest1)()
        if M.IdentityCompare(rest2, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        obj = M.Head(rest2)()
        agent_role = Role(M.Char("agent"), subj)()
        patient_role = Role(M.Char("patient"), obj)()
        return M.Pair(agent_role, M.Pair(patient_role, M.EmptyList))

    def __call__(self):
        return self.result


class ParseSVOToPredicate(M.Edge):
    def __init__(self, word_chain):
        self.result = self._extract(word_chain)
        super().__init__(inputs=M.Pair(word_chain, M.EmptyList), results=self.result)

    def _extract(self, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rest1 = M.Tail(chain)()
        if M.IdentityCompare(rest1, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        verb = M.Head(rest1)()
        return verb

    def __call__(self):
        return self.result


class ParseSVOToSubject(M.Edge):
    def __init__(self, word_chain):
        self.result = M.Head(word_chain)()
        super().__init__(inputs=M.Pair(word_chain, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ParseSVOToObject(M.Edge):
    def __init__(self, word_chain):
        self.result = M.Head(M.Tail(M.Tail(word_chain)())())()
        super().__init__(inputs=M.Pair(word_chain, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SVOToEvent(M.Edge):
    def __init__(self, event_id, word_chain, story_ref):
        self.result = self._make(event_id, word_chain, story_ref)
        super().__init__(inputs=M.Pair(event_id, M.Pair(word_chain, M.Pair(story_ref, M.EmptyList))), results=self.result)

    def _make(self, event_id, word_chain, story_ref):
        roles = ParseSVOToRoles(word_chain)()
        pred = ParseSVOToPredicate(word_chain)()
        return Event(event_id, pred, roles, story_ref)()

    def __call__(self):
        return self.result


class EntityFromWord(M.Edge):
    def __init__(self, word):
        self.result = Entity(word, word, M.EmptyList)()
        super().__init__(inputs=M.Pair(word, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BeforeRelation(M.Edge):
    def __init__(self, before_id, after_id, provenance, confidence):
        self.result = Relation(M.Char("before"), before_id, after_id, provenance, confidence)()
        super().__init__(inputs=M.Pair(before_id, M.Pair(after_id, M.Pair(provenance, M.Pair(confidence, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class AfterRelation(M.Edge):
    def __init__(self, before_id, after_id, provenance, confidence):
        self.result = Relation(M.Char("after"), after_id, before_id, provenance, confidence)()
        super().__init__(inputs=M.Pair(before_id, M.Pair(after_id, M.Pair(provenance, M.Pair(confidence, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class BecauseRelation(M.Edge):
    def __init__(self, effect_id, cause_id, provenance, confidence):
        self.result = Relation(M.Char("because"), effect_id, cause_id, provenance, confidence)()
        super().__init__(inputs=M.Pair(effect_id, M.Pair(cause_id, M.Pair(provenance, M.Pair(confidence, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class CausesRelation(M.Edge):
    def __init__(self, cause_id, effect_id, provenance, confidence):
        self.result = Relation(M.Char("causes"), cause_id, effect_id, provenance, confidence)()
        super().__init__(inputs=M.Pair(cause_id, M.Pair(effect_id, M.Pair(provenance, M.Pair(confidence, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class StoryFromEventChain(M.Edge):
    def __init__(self, story_id, title, event_chain):
        self.result = Story(story_id, title, event_chain)()
        super().__init__(inputs=M.Pair(story_id, M.Pair(title, M.Pair(event_chain, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class ValidateEntity(M.Edge):
    def __init__(self, entity):
        self.result = self._check(entity)
        super().__init__(inputs=M.Pair(entity, M.EmptyList), results=self.result)

    def _check(self, entity):
        if M.IsPair(entity)() is M.truth_value:
            if M.TermEqual(M.Head(entity)(), L.EntityLabel)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class ValidateEvent(M.Edge):
    def __init__(self, event):
        self.result = self._check(event)
        super().__init__(inputs=M.Pair(event, M.EmptyList), results=self.result)

    def _check(self, event):
        if M.IsPair(event)() is M.truth_value:
            if M.TermEqual(M.Head(event)(), L.EventLabel)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result
