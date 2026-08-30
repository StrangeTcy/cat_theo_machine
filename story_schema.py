"""Layer 1 — Representation: pair-only story ontology.

Design follows the existing InventedLemma / StallRecord discipline:
fixed pair schemas with explicit provenance.

Schemas (all Pair-only terms):

Entity   = Pair(EntityLabel,   Pair(id, Pair(canonical_name, Pair(attributes, Empty))))
Role     = Pair(RoleLabel,     Pair(role_name, Pair(entity_ref, Empty)))
Event    = Pair(EventLabel,    Pair(id, Pair(predicate, Pair(roles, Pair(story_ref, Empty)))))
Relation = Pair(RelationLabel, Pair(kind, Pair(source_id, Pair(target_id, Pair(provenance, Pair(confidence, Empty))))))
Story    = Pair(StoryLabel,    Pair(id, Pair(title, Pair(event_chain, Empty))))

- id, canonical_name, role_name, entity_ref, predicate, kind, source_id, target_id,
  provenance, title are all Char atoms (Char(symbol)) so Compare/TermEqual
  can decide structural equality without host strings leaking into the graph.
- attributes, roles, event_chain are Pair chains (possibly EmptyList).
- Relation carries provenance (story_ref or Char describing origin) and confidence
  (Char holding a numeric string like "0.95") to budget for defeasible alignment,
  per the honest caution about losing verified-identity.

This mirrors how invented lemmas keep origin_stall_goal.
"""

from __future__ import annotations

from . import labels as L
from . import machine as M


def _char(s: str) -> M.Char:
    return M.Char(s)


def _chain_from_strs(strs):
    """Build Pair chain from list of Python strings as Char atoms."""
    chain = M.EmptyList
    for s in reversed(strs):
        chain = M.Pair(_char(s), chain)
    return chain


def _chain_from_terms(terms):
    """Build Pair chain from list of already-built terms."""
    chain = M.EmptyList
    for t in reversed(terms):
        chain = M.Pair(t, chain)
    return chain


def _iter_chain(chain):
    """Yield elements of a Pair chain (host-side iteration)."""
    cur = chain
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        try:
            head = M.Head(cur)()
        except Exception:
            break
        yield head
        try:
            cur = M.Tail(cur)()
        except Exception:
            break


# ----------------------------------------------------------------------
# Constructors (Edge subclasses returning pair terms)
# ----------------------------------------------------------------------

class Entity(M.Edge):
    """Pair(EntityLabel, Pair(id, Pair(canonical_name, Pair(attributes, Empty))))"""

    def __init__(self, id_atom, canonical_name_atom, attributes_chain):
        self.result = M.Pair(
            L.EntityLabel,
            M.Pair(id_atom, M.Pair(canonical_name_atom, M.Pair(attributes_chain, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(id_atom, M.Pair(canonical_name_atom, M.Pair(attributes_chain, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Role(M.Edge):
    """Pair(RoleLabel, Pair(role_name, Pair(entity_ref, Empty)))"""

    def __init__(self, role_name_atom, entity_ref_atom):
        self.result = M.Pair(
            L.RoleLabel,
            M.Pair(role_name_atom, M.Pair(entity_ref_atom, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(role_name_atom, M.Pair(entity_ref_atom, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Event(M.Edge):
    """Pair(EventLabel, Pair(id, Pair(predicate, Pair(roles, Pair(story_ref, Empty)))))"""

    def __init__(self, id_atom, predicate_atom, roles_chain, story_ref_atom):
        self.result = M.Pair(
            L.EventLabel,
            M.Pair(id_atom, M.Pair(predicate_atom, M.Pair(roles_chain, M.Pair(story_ref_atom, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(id_atom, M.Pair(predicate_atom, M.Pair(roles_chain, M.Pair(story_ref_atom, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Relation(M.Edge):
    """Pair(RelationLabel, Pair(kind, Pair(source_id, Pair(target_id, Pair(provenance, Pair(confidence, Empty))))))"""

    def __init__(self, kind_atom, source_id_atom, target_id_atom, provenance_atom, confidence_atom):
        self.result = M.Pair(
            L.RelationLabel,
            M.Pair(
                kind_atom,
                M.Pair(
                    source_id_atom,
                    M.Pair(target_id_atom, M.Pair(provenance_atom, M.Pair(confidence_atom, M.EmptyList))),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                kind_atom,
                M.Pair(source_id_atom, M.Pair(target_id_atom, M.Pair(provenance_atom, M.Pair(confidence_atom, M.EmptyList)))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Story(M.Edge):
    """Pair(StoryLabel, Pair(id, Pair(title, Pair(event_chain, Empty))))"""

    def __init__(self, id_atom, title_atom, event_chain):
        self.result = M.Pair(
            L.StoryLabel,
            M.Pair(id_atom, M.Pair(title_atom, M.Pair(event_chain, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(id_atom, M.Pair(title_atom, M.Pair(event_chain, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


# ----------------------------------------------------------------------
# Type predicates and accessors (pure structural, no host guessing)
# ----------------------------------------------------------------------

class IsEntity(M.Edge):
    def __init__(self, term):
        res = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.EntityLabel)() is M.truth_value:
                res = M.truth_value
        self.result = res
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsRole(M.Edge):
    def __init__(self, term):
        res = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.RoleLabel)() is M.truth_value:
                res = M.truth_value
        self.result = res
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsEvent(M.Edge):
    def __init__(self, term):
        res = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.EventLabel)() is M.truth_value:
                res = M.truth_value
        self.result = res
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsRelation(M.Edge):
    def __init__(self, term):
        res = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.RelationLabel)() is M.truth_value:
                res = M.truth_value
        self.result = res
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsStory(M.Edge):
    def __init__(self, term):
        res = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.StoryLabel)() is M.truth_value:
                res = M.truth_value
        self.result = res
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# Entity accessors
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


# Role accessors
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


# Event accessors
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


# Relation accessors
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
        # Tail chain: kind, source, target, provenance, confidence
        # provenance is 4th slot
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


# Story accessors
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


# ----------------------------------------------------------------------
# Convenience host-side helpers (not machine terms, but produce them)
# ----------------------------------------------------------------------

def make_entity(id_str: str, canonical_name_str: str, attributes_strs=None):
    """Host helper to build Entity term."""
    if attributes_strs is None:
        attributes_strs = []
    attrs_chain = _chain_from_strs(attributes_strs)
    return Entity(_char(id_str), _char(canonical_name_str), attrs_chain)()


def make_role(role_name_str: str, entity_ref_str: str):
    return Role(_char(role_name_str), _char(entity_ref_str))()


def make_event(id_str: str, predicate_str: str, roles_list, story_ref_str: str):
    """
    roles_list: list of (role_name_str, entity_ref_str)
    """
    role_terms = [make_role(rn, er) for rn, er in roles_list]
    roles_chain = _chain_from_terms(role_terms)
    return Event(_char(id_str), _char(predicate_str), roles_chain, _char(story_ref_str))()


def make_relation(kind_str: str, source_id_str: str, target_id_str: str, provenance_str: str = "unknown", confidence_str: str = "1.0"):
    return Relation(_char(kind_str), _char(source_id_str), _char(target_id_str), _char(provenance_str), _char(confidence_str))()


def make_story(id_str: str, title_str: str, event_ids_list):
    chain = _chain_from_strs(event_ids_list)
    return Story(_char(id_str), _char(title_str), chain)()


def term_to_str(term):
    """Best-effort conversion of Char or Pair chain to Python string for debugging."""
    try:
        # If term is Char, it has .symbol
        sym = getattr(term, "symbol", None)
        if sym is not None:
            return sym
        # If it's a Pair chain of Chars, decode
        # Check if head is Char
        if M.IsPair(term)() is M.truth_value:
            # Could be Entity etc - return pretty via AtomName
            try:
                return M.AtomName(term)()
            except Exception:
                pass
            # Try to iterate
            parts = []
            for el in _iter_chain(term):
                parts.append(term_to_str(el))
            return "(" + " ".join(parts) + ")"
        # Fallback: try calling term() if it's Atom with value
        v = term()
        if isinstance(v, str):
            return v
        return str(v)
    except Exception as e:
        return f"<{type(term).__name__}>"


def get_entity_name(entity_term) -> str:
    try:
        cn = EntityCanonicalName(entity_term)()
        sym = getattr(cn, "symbol", None)
        if sym is not None:
            return sym
        return str(cn())
    except Exception:
        return ""


def get_event_predicate(event_term) -> str:
    try:
        p = EventPredicate(event_term)()
        sym = getattr(p, "symbol", None)
        if sym is not None:
            return sym
        return str(p())
    except Exception:
        return ""


__all__ = [
    "Entity",
    "Role",
    "Event",
    "Relation",
    "Story",
    "IsEntity",
    "IsRole",
    "IsEvent",
    "IsRelation",
    "IsStory",
    "EntityId",
    "EntityCanonicalName",
    "EntityAttributes",
    "RoleName",
    "RoleEntityRef",
    "EventId",
    "EventPredicate",
    "EventRoles",
    "EventStoryRef",
    "RelationKind",
    "RelationSource",
    "RelationTarget",
    "RelationProvenance",
    "RelationConfidence",
    "StoryId",
    "StoryTitle",
    "StoryEventChain",
    "make_entity",
    "make_role",
    "make_event",
    "make_relation",
    "make_story",
    "term_to_str",
    "get_entity_name",
    "get_event_predicate",
]
