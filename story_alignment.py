"""Layer 3 — Alignment / "connecting" and Layer 4 — Reasoning.

This implements:
- Entity resolution via thresholded unification (soft unification)
- Event alignment via role structure matching
- Cross-story same-as edges as proposals (never auto-merged)
- Analogy / structural mapping via compound substitution (reusing unifier)
- Path search over relation layer
- Schema induction (recurring subgraph) as story-schema

Reuses existing machinery:
- Patricia-tree indexing to find candidate matches cheaply (we simulate with dict index)
- Unification / renamed-variable replay -> fuzzy generalization for entity resolution
- Common subterm across frontier -> event frame alignment
- Lemma composition -> structure mapping
- Search/frontier machinery -> path search
- InventedLemma utility tracking -> schema utility counter
"""

from __future__ import annotations

import re
from typing import List, Dict, Tuple, Set
from collections import defaultdict, deque

from . import machine as M
from . import labels as L
from . import graph as G
from . import story_schema as SS
from . import story_parser as SP


# ----------------------------------------------------------------------
# Similarity and soft unification
# ----------------------------------------------------------------------

def _char_symbol(atom) -> str:
    sym = getattr(atom, "symbol", None)
    if sym is not None:
        return sym
    try:
        v = atom()
        if isinstance(v, str):
            return v
        return str(v)
    except Exception:
        return ""


def entity_name_similarity(name_a: str, name_b: str) -> float:
    """Simple similarity: exact case-insensitive =1.0, substring=0.8, token overlap, else 0."""
    a = name_a.lower()
    b = name_b.lower()
    if a == b:
        return 1.0
    # Handle "the wolf" vs "wolf" vs "King Roland" vs "king"
    # Strip leading "the "
    a_stripped = a[4:] if a.startswith("the ") else a
    b_stripped = b[4:] if b.startswith("the ") else b
    if a_stripped == b_stripped:
        return 0.95
    if a_stripped in b_stripped or b_stripped in a_stripped:
        return 0.8
    # Token overlap
    a_tokens = set(a.split())
    b_tokens = set(b.split())
    if a_tokens & b_tokens:
        # Jaccard
        inter = len(a_tokens & b_tokens)
        union = len(a_tokens | b_tokens)
        return 0.5 + 0.3 * (inter / union)
    return 0.0


def is_same_entity_candidate(entity_a, entity_b, threshold: float = 0.8) -> Tuple[bool, float]:
    """Decide if two Entity terms are same individual via thresholded unification."""
    name_a = SS.get_entity_name(entity_a)
    name_b = SS.get_entity_name(entity_b)
    sim = entity_name_similarity(name_a, name_b)
    return (sim >= threshold), sim


# ----------------------------------------------------------------------
# Patricia-like indexing for cheap candidate matching
# ----------------------------------------------------------------------

class EntityIndex:
    """Simple index mimicking Patricia-tree indexing for entity resolution."""

    def __init__(self):
        # Map from lowercased token -> list of entity terms
        self.token_to_entities: Dict[str, List] = defaultdict(list)
        self.id_to_entity: Dict[str, object] = {}
        self.all_entities: List = []

    def add(self, entity_term):
        eid_atom = SS.EntityId(entity_term)()
        eid = _char_symbol(eid_atom)
        cname = SS.get_entity_name(entity_term)
        self.id_to_entity[eid] = entity_term
        self.all_entities.append(entity_term)
        # Index by tokens of canonical name
        for tok in cname.lower().split():
            # Strip "the"
            if tok == "the":
                continue
            self.token_to_entities[tok].append(entity_term)
            # Also prefix index for patricia-like behavior
            for i in range(1, len(tok)+1):
                prefix = tok[:i]
                # We could index prefixes but for simplicity just token index
                pass

    def candidates_for(self, entity_term) -> List:
        cname = SS.get_entity_name(entity_term)
        cands = set()
        for tok in cname.lower().split():
            if tok == "the":
                continue
            for cand in self.token_to_entities.get(tok, []):
                # Use id of atom for identity set
                cands.add(id(cand))
        # Retrieve actual terms
        # Since we stored by id, we need mapping id->term
        id_to_term = {id(t): t for t in self.all_entities}
        return [id_to_term[i] for i in cands]

    def all_pairs(self):
        return self.all_entities


def build_entity_index(entity_terms: List) -> EntityIndex:
    idx = EntityIndex()
    for et in entity_terms:
        idx.add(et)
    return idx


# ----------------------------------------------------------------------
# Entity resolution: propose same-as edges
# ----------------------------------------------------------------------

class ProposedSameAs:
    def __init__(self, source_id: str, target_id: str, confidence: float, provenance: str, name_a: str, name_b: str):
        self.source_id = source_id
        self.target_id = target_id
        self.confidence = confidence
        self.provenance = provenance
        self.name_a = name_a
        self.name_b = name_b

    def __repr__(self):
        return f"ProposedSameAs({self.source_id}({self.name_a}) <-> {self.target_id}({self.name_b}) conf={self.confidence:.2f} prov={self.provenance})"


def propose_entity_links(entities_a: List, entities_b: List, threshold: float = 0.8, provenance: str = "cross-story") -> List[ProposedSameAs]:
    """
    Find candidate same-as links between two entity lists.
    Uses index to cheaply find candidates, then thresholded unification.
    Returns list of ProposedSameAs (not yet installed).
    """
    # Build index over B
    index_b = build_entity_index(entities_b)

    proposals = []

    for ent_a in entities_a:
        eid_a = _char_symbol(SS.EntityId(ent_a)())
        name_a = SS.get_entity_name(ent_a)

        # Find candidates in B via index
        # If index yields none, fallback to all (for small corpora)
        cands = index_b.candidates_for(ent_a)
        if not cands:
            cands = entities_b

        for ent_b in cands:
            eid_b = _char_symbol(SS.EntityId(ent_b)())
            # Avoid self-link if same id
            if eid_a == eid_b:
                continue
            is_same, sim = is_same_entity_candidate(ent_a, ent_b, threshold=threshold)
            if is_same:
                proposals.append(ProposedSameAs(
                    source_id=eid_a,
                    target_id=eid_b,
                    confidence=sim,
                    provenance=provenance,
                    name_a=name_a,
                    name_b=SS.get_entity_name(ent_b),
                ))

    return proposals


def proposals_to_relation_terms(proposals: List[ProposedSameAs]) -> List:
    """Convert ProposedSameAs to Relation terms (same-as) with confidence and provenance."""
    terms = []
    for p in proposals:
        # Use SameAsLabel? Actually kind is Char("same-as")
        # Provenance and confidence as Char
        term = SS.make_relation("same-as", p.source_id, p.target_id, provenance_str=p.provenance, confidence_str=str(p.confidence))
        terms.append(term)
    return terms


# ----------------------------------------------------------------------
# Validation gate for proposals (approve/reject discipline)
# ----------------------------------------------------------------------

def approve_same_as_proposals(proposals: List[ProposedSameAs], min_confidence: float = 0.8) -> List[ProposedSameAs]:
    """Approve proposals meeting confidence threshold and non-trivial checks."""
    approved = []
    for p in proposals:
        if p.confidence >= min_confidence:
            # Additional check: not approving if names are too generic? For milestone, approve all above threshold.
            approved.append(p)
    return approved


# ----------------------------------------------------------------------
# Event alignment (common subterm across frontier states analogy)
# ----------------------------------------------------------------------

def event_role_signature(event_term) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
    """
    Return (predicate, tuple of (role_name, entity_ref)) for alignment.
    This is the frame structure used for matching.
    """
    pred = _char_symbol(SS.EventPredicate(event_term)())
    roles_chain = SS.EventRoles(event_term)()
    roles = []
    for role_term in SS._iter_chain(roles_chain):
        rname = _char_symbol(SS.RoleName(role_term)())
        eref = _char_symbol(SS.RoleEntityRef(role_term)())
        roles.append((rname, eref))
    # Sort roles by name for canonical comparison
    roles_sorted = tuple(sorted(roles))
    return (pred.lower(), roles_sorted)


def propose_event_alignments(events_a: List, events_b: List, entity_same_as_map: Dict[str, str], threshold: float = 0.8) -> List[Tuple[str, str, float]]:
    """
    Propose alignment between events with matching role structure.
    entity_same_as_map: mapping from entity id in A to canonical id (or to B's id) for unification.
    Returns list of (event_id_a, event_id_b, confidence)
    """
    # Build signature index for B
    sig_to_events_b = defaultdict(list)
    for ev_b in events_b:
        sig = event_role_signature(ev_b)
        sig_to_events_b[sig[0]].append((sig, ev_b))

    proposals = []

    for ev_a in events_a:
        sig_a = event_role_signature(ev_a)
        pred_a, roles_a = sig_a
        # Candidates with same predicate
        for sig_b, ev_b in sig_to_events_b.get(pred_a, []):
            pred_b, roles_b = sig_b
            # Check role structure unification with entity same-as map
            # Roles must have same role names and entity refs that are either equal or linked via same-as
            if len(roles_a) != len(roles_b):
                continue
            # Compare role by role (sorted)
            match = True
            for (rname_a, eref_a), (rname_b, eref_b) in zip(roles_a, roles_b):
                if rname_a != rname_b:
                    match = False
                    break
                # Check if entity refs are same or linked
                if eref_a == eref_b:
                    continue
                # Check if eref_a maps to eref_b via same-as
                # entity_same_as_map maps A->B, but we also need reverse
                if entity_same_as_map.get(eref_a) == eref_b or entity_same_as_map.get(eref_b) == eref_a:
                    continue
                # Check if both map to same canonical
                # For simplicity, if eref_a and eref_b are linked transitively, we consider match
                # Here we just check if they are in same connected component via map
                # For milestone, we do simple check: if names similar? We'll use similarity of entity ids? Actually need entity names.
                # We'll require exact or mapped; otherwise no match.
                match = False
                break
            if match:
                # Confidence based on predicate match + role match
                conf = 0.9
                proposals.append((_char_symbol(SS.EventId(ev_a)()), _char_symbol(SS.EventId(ev_b)()), conf))

    return proposals


# ----------------------------------------------------------------------
# Structural mapping / analogy (compound substitution machinery)
# ----------------------------------------------------------------------

def find_analogy_mapping(event_chain_a: List, event_chain_b: List, entity_index_a, entity_index_b) -> Dict[str, str] | None:
    """
    Find consistent variable mapping under which event chain A maps onto B.
    This is the structure-mapping engine analogous to SOS-lemma renamed instance.

    For milestone, we implement simple consistent mapping:
    - Both chains have same length
    - Predicates match in order
    - Roles structure matches with a consistent entity mapping

    Returns dict mapping entity_id in A -> entity_id in B if found, else None.
    """
    if len(event_chain_a) != len(event_chain_b):
        return None

    mapping: Dict[str, str] = {}
    reverse_mapping: Dict[str, str] = {}

    for ev_a, ev_b in zip(event_chain_a, event_chain_b):
        sig_a = event_role_signature(ev_a)
        sig_b = event_role_signature(ev_b)
        pred_a, roles_a = sig_a
        pred_b, roles_b = sig_b
        if pred_a != pred_b:
            return None
        if len(roles_a) != len(roles_b):
            return None
        for (rname_a, eref_a), (rname_b, eref_b) in zip(roles_a, roles_b):
            if rname_a != rname_b:
                return None
            # Check consistency
            if eref_a in mapping:
                if mapping[eref_a] != eref_b:
                    return None
            else:
                # Check reverse consistency (injective mapping)
                if eref_b in reverse_mapping:
                    if reverse_mapping[eref_b] != eref_a:
                        return None
                mapping[eref_a] = eref_b
                reverse_mapping[eref_b] = eref_a

    return mapping


# ----------------------------------------------------------------------
# GraphVersion handling and persistence
# ----------------------------------------------------------------------

def build_graph_version(entities, events, relations, story_terms) -> M.Pair:
    """
    Build a GraphVersion term containing all story nodes.
    node_store = chain of all Entity, Event, Relation, Story terms
    edge_store = EmptyList (for now)
    invariant_store = EmptyList
    """
    all_nodes = []
    all_nodes.extend(entities)
    all_nodes.extend(events)
    all_nodes.extend(relations)
    all_nodes.extend(story_terms)

    node_chain = M.EmptyList
    for node in reversed(all_nodes):
        node_chain = M.Pair(node, node_chain)

    gv = G.GraphVersion(node_chain, M.EmptyList, M.EmptyList)()
    return gv


def extract_entities_from_graph_version(gv) -> List:
    """Extract Entity terms from GraphVersion node store."""
    nodes = G.GraphNodes(gv)()
    entities = []
    for term in SS._iter_chain(nodes):
        if SS.IsEntity(term)() is M.truth_value:
            entities.append(term)
    return entities


def extract_events_from_graph_version(gv) -> List:
    nodes = G.GraphNodes(gv)()
    events = []
    for term in SS._iter_chain(nodes):
        if SS.IsEvent(term)() is M.truth_value:
            events.append(term)
    return events


def extract_relations_from_graph_version(gv) -> List:
    nodes = G.GraphNodes(gv)()
    rels = []
    for term in SS._iter_chain(nodes):
        if SS.IsRelation(term)() is M.truth_value:
            rels.append(term)
    return rels


def extract_stories_from_graph_version(gv) -> List:
    nodes = G.GraphNodes(gv)()
    stories = []
    for term in SS._iter_chain(nodes):
        if SS.IsStory(term)() is M.truth_value:
            stories.append(term)
    return stories


def add_relations_to_graph_version(gv, new_relations) -> M.Pair:
    """Return new GraphVersion with additional relations appended to node store."""
    nodes = G.GraphNodes(gv)()
    # Build chain of new relations
    # Prepend to existing nodes (order doesn't matter)
    new_nodes = nodes
    for rel in reversed(new_relations):
        new_nodes = M.Pair(rel, new_nodes)

    # Preserve edge and invariant stores
    edge_store = G.GraphEdges(gv)()
    inv_store = G.GraphVersionInvariants(gv)()
    new_gv = G.GraphVersion(new_nodes, edge_store, inv_store)()
    return new_gv


# ----------------------------------------------------------------------
# Reasoning: path search over relation layer
# ----------------------------------------------------------------------

def build_adjacency(gv) -> Dict[str, Set[str]]:
    """
    Build adjacency map for BFS:
    - Nodes are entity ids and event ids (as strings)
    - Edges:
      * entity <-> event if entity participates in event (via roles)
      * relation source <-> target for each Relation
    """
    adj: Dict[str, Set[str]] = defaultdict(set)

    entities = extract_entities_from_graph_version(gv)
    events = extract_events_from_graph_version(gv)
    relations = extract_relations_from_graph_version(gv)

    # entity id set for quick lookup
    entity_ids = set(_char_symbol(SS.EntityId(e)()) for e in entities)
    event_ids = set(_char_symbol(SS.EventId(ev)()) for ev in events)

    # entity <-> event via roles
    for ev in events:
        ev_id = _char_symbol(SS.EventId(ev)())
        roles_chain = SS.EventRoles(ev)()
        for role_term in SS._iter_chain(roles_chain):
            eref = _char_symbol(SS.RoleEntityRef(role_term)())
            # Add edge both ways
            adj[ev_id].add(eref)
            adj[eref].add(ev_id)

    # relation edges
    for rel in relations:
        kind = _char_symbol(SS.RelationKind(rel)())
        src = _char_symbol(SS.RelationSource(rel)())
        tgt = _char_symbol(SS.RelationTarget(rel)())
        # For same-as, before, after, because, causes etc, add undirected edge for path search
        # But keep kind info for explanation
        adj[src].add(tgt)
        adj[tgt].add(src)

    return adj


def find_connection_path(gv, source_id: str, target_id: str) -> List[str] | None:
    """
    BFS path search: "How is character X connected to Y?"
    Returns list of ids representing path, or None if not connected.
    """
    adj = build_adjacency(gv)
    if source_id not in adj or target_id not in adj:
        # If source/target not in adj (isolated), still try
        # Build adj may not contain isolated entities, so add them
        if source_id not in adj:
            adj[source_id] = set()
        if target_id not in adj:
            adj[target_id] = set()

    visited = set()
    queue = deque()
    queue.append((source_id, [source_id]))
    visited.add(source_id)

    while queue:
        current, path = queue.popleft()
        if current == target_id:
            return path
        for neighbor in adj.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None


def explain_path(gv, path: List[str]) -> List[str]:
    """
    Explain path in human-readable form, using entity names and event predicates.
    """
    # Build lookup for entity names and event predicates
    entity_name_map = {}
    for ent in extract_entities_from_graph_version(gv):
        eid = _char_symbol(SS.EntityId(ent)())
        entity_name_map[eid] = SS.get_entity_name(ent)

    event_pred_map = {}
    for ev in extract_events_from_graph_version(gv):
        eid = _char_symbol(SS.EventId(ev)())
        event_pred_map[eid] = SS.get_event_predicate(ev)

    relation_map = {}  # (src,tgt) -> kind
    for rel in extract_relations_from_graph_version(gv):
        src = _char_symbol(SS.RelationSource(rel)())
        tgt = _char_symbol(SS.RelationTarget(rel)())
        kind = _char_symbol(SS.RelationKind(rel)())
        relation_map[(src, tgt)] = kind
        relation_map[(tgt, src)] = kind  # undirected for explanation, but kind may be directional

    explanations = []
    for i in range(len(path)-1):
        a = path[i]
        b = path[i+1]
        kind = relation_map.get((a, b), "related")
        # Determine if a and b are entity/event
        a_name = entity_name_map.get(a) or event_pred_map.get(a) or a
        b_name = entity_name_map.get(b) or event_pred_map.get(b) or b
        # If both are entities and intermediate is event? Actually path includes events as nodes.
        # For simplicity, explain each hop
        explanations.append(f"{a_name} --[{kind}]--> {b_name}")

    return explanations


# ----------------------------------------------------------------------
# Schema induction (narrative schema = recurring subgraph)
# ----------------------------------------------------------------------

class StorySchema:
    """Recurring subgraph across many stories, analogous to InventedLemma with utility counter."""

    def __init__(self, schema_id: str, pattern_events: List, utility: int = 1):
        self.schema_id = schema_id
        self.pattern_events = pattern_events  # list of event signatures
        self.utility = utility

    def __repr__(self):
        return f"StorySchema(id={self.schema_id}, utility={self.utility}, pattern={self.pattern_events})"


def induce_schemas_from_graph_versions(graph_versions: List, min_support: int = 2) -> List[StorySchema]:
    """
    Find recurring event patterns across stories.
    For milestone, we look for common predicate sequences.

    Returns list of StorySchema with utility counter growing on reuse.
    """
    # Collect event chains per story
    # For each GV, extract events grouped by story_ref
    story_to_events = defaultdict(list)  # story_ref -> list of events

    for gv in graph_versions:
        for ev in extract_events_from_graph_version(gv):
            sref = _char_symbol(SS.EventStoryRef(ev)())
            story_to_events[sref].append(ev)

    # For each story, sort events by id (which encodes order) or by before relations?
    # For simplicity, sort by event id string (which includes index)
    for sref in story_to_events:
        story_to_events[sref] = sorted(story_to_events[sref], key=lambda ev: _char_symbol(SS.EventId(ev)()))

    # Extract predicate sequences
    seq_to_stories = defaultdict(list)  # tuple of predicates -> list of story_refs
    for sref, evs in story_to_events.items():
        pred_seq = tuple(_char_symbol(SS.EventPredicate(ev)()).lower() for ev in evs)
        seq_to_stories[pred_seq].append(sref)

    schemas = []
    schema_id = 0
    for pred_seq, srefs in seq_to_stories.items():
        if len(srefs) >= min_support:
            # This is a recurring pattern
            schema = StorySchema(
                schema_id=f"schema_{schema_id}",
                pattern_events=list(pred_seq),
                utility=len(srefs),
            )
            schemas.append(schema)
            schema_id += 1

    # Also look for common sub-sequences of length 2
    # For more interesting induction
    subseq_to_stories = defaultdict(set)
    for sref, evs in story_to_events.items():
        preds = [_char_symbol(SS.EventPredicate(ev)()).lower() for ev in evs]
        for i in range(len(preds)):
            for j in range(i+2, len(preds)+1):  # subseq length >=2
                subseq = tuple(preds[i:j])
                subseq_to_stories[subseq].add(sref)

    for subseq, sref_set in subseq_to_stories.items():
        if len(sref_set) >= min_support:
            # Avoid duplicates already counted as full sequences
            if subseq not in seq_to_stories:
                schema = StorySchema(
                    schema_id=f"schema_{schema_id}",
                    pattern_events=list(subseq),
                    utility=len(sref_set),
                )
                schemas.append(schema)
                schema_id += 1

    return schemas


__all__ = [
    "entity_name_similarity",
    "is_same_entity_candidate",
    "EntityIndex",
    "build_entity_index",
    "ProposedSameAs",
    "propose_entity_links",
    "proposals_to_relation_terms",
    "approve_same_as_proposals",
    "event_role_signature",
    "propose_event_alignments",
    "find_analogy_mapping",
    "build_graph_version",
    "extract_entities_from_graph_version",
    "extract_events_from_graph_version",
    "extract_relations_from_graph_version",
    "extract_stories_from_graph_version",
    "add_relations_to_graph_version",
    "build_adjacency",
    "find_connection_path",
    "explain_path",
    "StorySchema",
    "induce_schemas_from_graph_versions",
]
