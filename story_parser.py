"""Layer 2 — Extraction: controlled-language parser for stories.

This is the hard 80% made tractable by restricting input grammar.
We keep messy NLP outside core.py, as recommended.

Grammar (controlled subset):

Story input is:
  title: first line or provided separately
  sentences: separated by '.' or newline

Sentence templates (case-insensitive for keywords, but entity names preserve case):

1. Simple SVO:
   "<Subject> <Verb> <Object>"
   Example: "Alice meets Bob"
   -> Event with agent=Subject, patient=Object, predicate=Verb

2. SVO with prepositional recipient:
   "<Subject> <Verb> <Object> to <Recipient>"
   Example: "Bob gives book to Alice"
   -> roles: agent=Subject, patient=Object, recipient=Recipient

3. SVO with location:
   "<Subject> <Verb> <Object> in <Location>"
   Example: "Alice reads book in library"
   -> roles: agent, patient, location

4. SVO with instrument:
   "<Subject> <Verb> <Object> with <Instrument>"
   Example: "Alice hits wolf with stick"

5. Copular location:
   "<Subject> is in <Location>"
   Example: "Bob is in forest"
   -> predicate "is_in", roles agent=Subject, location=Location

6. Temporal connector:
   "then <Sentence>"
   Example: "then Alice reads book"
   -> parse inner sentence, add Relation kind "before" from previous event to current

7. Causal connector:
   "<Effect> because <Cause>"
   Example: "Alice reads book because Bob gives book to Alice"
   -> parse both clauses as separate events, add Relation kind "because" or "causes" from cause -> effect
   Also supports "because" as standalone: "Alice runs because wolf appears"

The parser never writes directly into GraphVersion; it emits candidate nodes
that must pass through a validation gate, exactly like suggest lemmas -> yes.

For milestone 1, we implement:
- tokenization preserving entity case
- entity canonicalization (lowercased id, original canonical_name)
- event generation with incremental ids
- before/because relation generation
- provenance tracking (story_ref on every node)

We deliberately avoid external NLP or LLM for milestone 1.
"""

from __future__ import annotations

import re
from typing import List, Tuple, Dict

from . import machine as M
from . import story_schema as SS


# ----------------------------------------------------------------------
# Tokenization and lexicon
# ----------------------------------------------------------------------

# Known role prepositions
_PREP_TO = "to"
_PREP_IN = "in"
_PREP_WITH = "with"

# Connectors
_CONNECTOR_THEN = "then"
_CONNECTOR_BECAUSE = "because"
_CONNECTOR_AND = "and"

# Copular
_COPULAR_IS = "is"

# Simple verb list for controlled subset - extensible
# We don't enforce closed verb list; any middle token can be verb.
# But we handle "is" specially.

def _tokenize(sentence: str) -> List[str]:
    # Keep words, drop punctuation except we keep sentence split elsewhere
    # Split on whitespace, strip .,!?;:
    # Preserve case for entity detection
    raw = sentence.strip()
    # Remove trailing period
    raw = raw.rstrip(".!?")
    # Split
    tokens = re.findall(r"[A-Za-z0-9_]+", raw)
    return tokens


def _is_capitalized(word: str) -> bool:
    return len(word) > 0 and word[0].isupper()


def _lower_id(name: str) -> str:
    return name.lower().replace(" ", "_")


# ----------------------------------------------------------------------
# Controlled parser
# ----------------------------------------------------------------------

class ParsedEvent:
    def __init__(self, predicate: str, roles: List[Tuple[str, str]], raw_text: str):
        self.predicate = predicate
        self.roles = roles  # list of (role_name, entity_name)
        self.raw_text = raw_text

    def __repr__(self):
        return f"ParsedEvent(pred={self.predicate}, roles={self.roles}, raw={self.raw_text!r})"


class ParsedStory:
    def __init__(self, story_id: str, title: str):
        self.story_id = story_id
        self.title = title
        self.entities: Dict[str, str] = {}  # lower_id -> canonical_name
        self.entity_attributes: Dict[str, List[str]] = {}  # lower_id -> attrs
        self.parsed_events: List[ParsedEvent] = []
        self.temporal_links: List[Tuple[int, int]] = []  # (before_idx, after_idx)
        self.causal_links: List[Tuple[int, int]] = []  # (cause_idx, effect_idx)

    def _register_entity(self, name: str):
        lid = _lower_id(name)
        if lid not in self.entities:
            self.entities[lid] = name
            self.entity_attributes[lid] = []
        return lid

    def add_event(self, pe: ParsedEvent) -> int:
        # Register all entity refs
        for role_name, entity_name in pe.roles:
            self._register_entity(entity_name)
        idx = len(self.parsed_events)
        self.parsed_events.append(pe)
        return idx


def parse_svo(tokens: List[str], raw_text: str) -> ParsedEvent | None:
    """
    Attempt to parse tokens as SVO with optional prep.
    Returns ParsedEvent or None.
    Templates:
      Subj Verb Obj
      Subj Verb Obj to Recipient
      Subj Verb Obj in Location
      Subj Verb Obj with Instrument
      Subj is in Location
    """
    if not tokens:
        return None

    # Copular: "X is in Y" or "X is Y" (treat Y as location or attribute?)
    # We handle "X is in Y"
    if len(tokens) >= 4 and tokens[1].lower() == _COPULAR_IS and tokens[2].lower() == _PREP_IN:
        subj = tokens[0]
        loc = tokens[3]
        # If more tokens after location, join? For controlled subset, single word location.
        # But allow multi-word location as last token chain? We'll take token[3] as location, rest as extra?
        # For simplicity, location is token[3], if there are more, they are part of location phrase (join with space)
        if len(tokens) > 4:
            loc = " ".join(tokens[3:])
        return ParsedEvent(predicate="is_in", roles=[("agent", subj), ("location", loc)], raw_text=raw_text)

    # General SVO
    if len(tokens) < 3:
        return None

    subj = tokens[0]
    verb = tokens[1]
    obj = tokens[2]

    roles = [("agent", subj), ("patient", obj)]

    # Check for prepositional extension
    if len(tokens) >= 5:
        prep = tokens[3].lower()
        prep_obj = tokens[4]
        if len(tokens) > 5:
            # Join remaining as part of prep_obj phrase? For simplicity, join rest
            prep_obj = " ".join(tokens[4:])
        if prep == _PREP_TO:
            roles.append(("recipient", prep_obj))
        elif prep == _PREP_IN:
            roles.append(("location", prep_obj))
        elif prep == _PREP_WITH:
            roles.append(("instrument", prep_obj))
        else:
            # Unknown prep, treat as additional role with prep as name
            roles.append((prep, prep_obj))

    return ParsedEvent(predicate=verb, roles=roles, raw_text=raw_text)


def parse_sentence(sentence: str) -> List[ParsedEvent] | Tuple[List[ParsedEvent], str]:
    """
    Parse one sentence, handling then/because connectors.
    Returns (events, link_type) where link_type indicates temporal/causal relation to previous.
    For simplicity, this function returns list of events produced by this sentence,
    plus metadata about how they link.

    For "then X", returns ([event], "then")
    For "A because B", returns ([effect_event, cause_event], "because")
    Otherwise returns ([event], "none")
    """
    s = sentence.strip()
    if not s:
        return [], "none"

    lower = s.lower()

    # Handle "then"
    if lower.startswith(_CONNECTOR_THEN + " "):
        inner = s[len(_CONNECTOR_THEN):].strip()
        inner_tokens = _tokenize(inner)
        ev = parse_svo(inner_tokens, inner)
        if ev is None:
            return [], "none"
        return [ev], "then"

    # Handle "because"
    # Split on " because "
    # We want case-insensitive split, but preserve original case for entity names.
    # Use regex split
    m = re.split(r'\s+because\s+', s, flags=re.IGNORECASE)
    if len(m) == 2:
        effect_text, cause_text = m[0].strip(), m[1].strip()
        effect_tokens = _tokenize(effect_text)
        cause_tokens = _tokenize(cause_text)
        effect_ev = parse_svo(effect_tokens, effect_text)
        cause_ev = parse_svo(cause_tokens, cause_text)
        events = []
        if effect_ev:
            events.append(effect_ev)
        if cause_ev:
            events.append(cause_ev)
        # If both present, causal link from cause (last) to effect (first)
        # We'll return in order [effect, cause] and indicate because link
        return events, "because"

    # Simple sentence
    tokens = _tokenize(s)
    ev = parse_svo(tokens, s)
    if ev is None:
        return [], "none"
    return [ev], "none"


def parse_controlled_story(story_id: str, title: str, text: str) -> ParsedStory:
    """
    Parse a controlled-language story text into ParsedStory.
    text: multiple sentences separated by '.' or newline.
    """
    ps = ParsedStory(story_id=story_id, title=title)

    # Split into sentences: by '.' or newline
    # First split by newline, then by '.'
    raw_sentences = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Split by '.'
        parts = [p.strip() for p in line.split(".") if p.strip()]
        raw_sentences.extend(parts)

    prev_event_idx = None

    for sent in raw_sentences:
        events, link_type = parse_sentence(sent)
        if not events:
            continue

        if link_type == "then":
            # Single event, temporal link from prev to current
            idx = ps.add_event(events[0])
            if prev_event_idx is not None:
                ps.temporal_links.append((prev_event_idx, idx))
            prev_event_idx = idx
        elif link_type == "because":
            # events = [effect, cause] (if both parsed)
            if len(events) == 2:
                effect_idx = ps.add_event(events[0])
                cause_idx = ps.add_event(events[1])
                ps.causal_links.append((cause_idx, effect_idx))
                # For temporal ordering, consider effect as latest
                prev_event_idx = effect_idx
            elif len(events) == 1:
                idx = ps.add_event(events[0])
                prev_event_idx = idx
        else:
            # Simple
            idx = ps.add_event(events[0])
            prev_event_idx = idx

    return ps


# ----------------------------------------------------------------------
# Conversion to pair-only terms (candidate nodes, not yet installed)
# ----------------------------------------------------------------------

def parsed_story_to_terms(parsed: ParsedStory):
    """
    Convert ParsedStory to pair-only terms (Entity, Event, Relation, Story).
    Returns dict with keys: entities, events, relations, story, plus raw lists.

    This is the untrusted front-end: it only proposes nodes, subject to
    validation gate.

    Provenance: entity ids are story-prefixed (story_id:lower_id) to keep
    per-story provenance, while canonical_name preserves original surface.
    Cross-story same-as edges will link them.
    """
    # Entities - story-prefixed ids for provenance
    entity_terms = []
    entity_id_map = {}  # lower_id -> story_prefixed_id
    for eid, canonical in parsed.entities.items():
        prefixed_id = f"{parsed.story_id}:{eid}"
        entity_id_map[eid] = prefixed_id
        attrs = parsed.entity_attributes.get(eid, [])
        term = SS.make_entity(prefixed_id, canonical, attrs)
        entity_terms.append(term)

    # Events
    event_terms = []
    event_id_map = {}  # index -> event_id_str
    for idx, pe in enumerate(parsed.parsed_events):
        ev_id = f"{parsed.story_id}_e{idx}"
        event_id_map[idx] = ev_id
        roles = []
        for rname, ename in pe.roles:
            lower = _lower_id(ename)
            # Use story-prefixed entity ref if we have it, else fallback to lower
            eref = entity_id_map.get(lower, f"{parsed.story_id}:{lower}")
            roles.append((rname, eref))
        # roles as list of (role_name, entity_ref_id)
        ev_term = SS.make_event(ev_id, pe.predicate.lower(), roles, parsed.story_id)
        event_terms.append(ev_term)

    # Relations: before/after/because
    relation_terms = []

    # Temporal: before
    for before_idx, after_idx in parsed.temporal_links:
        before_id = event_id_map.get(before_idx)
        after_id = event_id_map.get(after_idx)
        if before_id and after_id:
            # before relation: before -> after, kind "before"
            rel = SS.make_relation("before", before_id, after_id, provenance_str=parsed.story_id, confidence_str="1.0")
            relation_terms.append(rel)
            # Also after relation for symmetry (optional)
            rel2 = SS.make_relation("after", after_id, before_id, provenance_str=parsed.story_id, confidence_str="1.0")
            relation_terms.append(rel2)

    # Causal: because / causes
    for cause_idx, effect_idx in parsed.causal_links:
        cause_id = event_id_map.get(cause_idx)
        effect_id = event_id_map.get(effect_idx)
        if cause_id and effect_id:
            rel = SS.make_relation("because", effect_id, cause_id, provenance_str=parsed.story_id, confidence_str="1.0")
            relation_terms.append(rel)
            rel2 = SS.make_relation("causes", cause_id, effect_id, provenance_str=parsed.story_id, confidence_str="1.0")
            relation_terms.append(rel2)

    # Story term
    event_ids = [event_id_map[i] for i in range(len(parsed.parsed_events))]
    story_term = SS.make_story(parsed.story_id, parsed.title, event_ids)

    return {
        "entities": entity_terms,
        "events": event_terms,
        "relations": relation_terms,
        "story": story_term,
        "parsed": parsed,
        "event_id_map": event_id_map,
    }


# ----------------------------------------------------------------------
# Validation gate (mirrors suggest lemmas -> yes discipline)
# ----------------------------------------------------------------------

def validate_candidate_terms(terms_dict) -> Tuple[bool, List[str]]:
    """
    Validate candidate nodes from parser before installing into GraphVersion.
    Checks:
    - Entity ids unique, canonical_name non-empty
    - Event ids unique, predicate non-empty, roles reference known entities, story_ref matches
    - Relation source/target exist (entity or event ids), kind non-empty
    - Story id matches, event_chain references existing events

    Returns (is_valid, list_of_error_messages)
    """
    errors = []

    parsed = terms_dict.get("parsed")
    if parsed is None:
        errors.append("Missing parsed metadata")
        return False, errors

    # Collect ids - now entities are story-prefixed for provenance
    # parsed.entities keys are lower ids, but actual term ids are story_id:lower
    entity_ids_lower = set(parsed.entities.keys())
    entity_ids_prefixed = set(f"{parsed.story_id}:{eid}" for eid in entity_ids_lower)
    event_ids = set(terms_dict.get("event_id_map", {}).values())

    # Check entities
    for term in terms_dict.get("entities", []):
        try:
            eid_atom = SS.EntityId(term)()
            cname_atom = SS.EntityCanonicalName(term)()
            eid_sym = getattr(eid_atom, "symbol", None) or str(eid_atom())
            cname_sym = getattr(cname_atom, "symbol", None) or str(cname_atom())
            if not eid_sym:
                errors.append(f"Entity with empty id")
            if not cname_sym:
                errors.append(f"Entity {eid_sym} with empty canonical_name")
        except Exception as e:
            errors.append(f"Entity accessor failed: {e}")

    # Check events
    for term in terms_dict.get("events", []):
        try:
            ev_id_atom = SS.EventId(term)()
            pred_atom = SS.EventPredicate(term)()
            roles_chain = SS.EventRoles(term)()
            story_ref_atom = SS.EventStoryRef(term)()
            ev_id_sym = getattr(ev_id_atom, "symbol", None) or str(ev_id_atom())
            pred_sym = getattr(pred_atom, "symbol", None) or str(pred_atom())
            story_ref_sym = getattr(story_ref_atom, "symbol", None) or str(story_ref_atom())
            if not ev_id_sym:
                errors.append("Event with empty id")
            if not pred_sym:
                errors.append(f"Event {ev_id_sym} with empty predicate")
            if story_ref_sym != parsed.story_id:
                errors.append(f"Event {ev_id_sym} story_ref {story_ref_sym} != {parsed.story_id}")
            # Check roles reference known entities (prefixed ids)
            for role_term in SS._iter_chain(roles_chain):
                try:
                    ename_atom = SS.RoleEntityRef(role_term)()
                    ename_sym = getattr(ename_atom, "symbol", None) or str(ename_atom())
                    if ename_sym not in entity_ids_prefixed:
                        # Also allow lower id fallback for robustness
                        if ename_sym not in entity_ids_lower and ename_sym.lower() not in entity_ids_lower:
                            errors.append(f"Event {ev_id_sym} role references unknown entity {ename_sym} (known {entity_ids_prefixed})")
                except Exception as e:
                    errors.append(f"Role accessor failed in event {ev_id_sym}: {e}")
        except Exception as e:
            errors.append(f"Event accessor failed: {e}")

    # Check relations - allow both prefixed entity ids and event ids
    all_ids = entity_ids_prefixed.union(entity_ids_lower).union(event_ids)
    for term in terms_dict.get("relations", []):
        try:
            kind_atom = SS.RelationKind(term)()
            src_atom = SS.RelationSource(term)()
            tgt_atom = SS.RelationTarget(term)()
            kind_sym = getattr(kind_atom, "symbol", None) or str(kind_atom())
            src_sym = getattr(src_atom, "symbol", None) or str(src_atom())
            tgt_sym = getattr(tgt_atom, "symbol", None) or str(tgt_atom())
            if not kind_sym:
                errors.append("Relation with empty kind")
            if src_sym not in all_ids:
                errors.append(f"Relation {kind_sym} source {src_sym} not in entity/event ids")
            if tgt_sym not in all_ids:
                errors.append(f"Relation {kind_sym} target {tgt_sym} not in entity/event ids")
        except Exception as e:
            errors.append(f"Relation accessor failed: {e}")

    # Check story
    try:
        story_term = terms_dict.get("story")
        if story_term is not None:
            sid_atom = SS.StoryId(story_term)()
            sid_sym = getattr(sid_atom, "symbol", None) or str(sid_atom())
            if sid_sym != parsed.story_id:
                errors.append(f"Story id {sid_sym} != {parsed.story_id}")
            chain = SS.StoryEventChain(story_term)()
            for ev_id_atom in SS._iter_chain(chain):
                ev_id_sym = getattr(ev_id_atom, "symbol", None) or str(ev_id_atom())
                if ev_id_sym not in event_ids:
                    errors.append(f"Story event_chain references unknown event {ev_id_sym}")
    except Exception as e:
        errors.append(f"Story accessor failed: {e}")

    return (len(errors) == 0), errors


__all__ = [
    "ParsedEvent",
    "ParsedStory",
    "parse_svo",
    "parse_sentence",
    "parse_controlled_story",
    "parsed_story_to_terms",
    "validate_candidate_terms",
]
