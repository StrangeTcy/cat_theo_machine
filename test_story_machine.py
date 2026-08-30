"""Unit tests for story machine milestone 1."""

from __future__ import annotations

import os
import json
import tempfile

from . import machine as M
from . import graph as G
from . import labels as L
from . import persistence as Pers
from . import story_schema as SS
from . import story_parser as SP
from . import story_alignment as SA


def test_pair_schemas():
    # Entity schema
    ent = SS.make_entity("story1:alice", "Alice", ["brave"])
    assert SS.IsEntity(ent)() is M.truth_value
    eid = SS.EntityId(ent)()
    assert getattr(eid, "symbol", None) == "story1:alice"
    cname = SS.get_entity_name(ent)
    assert cname == "Alice"

    # Role
    role = SS.make_role("agent", "story1:alice")
    assert SS.IsRole(role)() is M.truth_value

    # Event with roles
    ev = SS.make_event("story1_e0", "meets", [("agent", "story1:alice"), ("patient", "story1:bob")], "story1")
    assert SS.IsEvent(ev)() is M.truth_value
    pred = SS.get_event_predicate(ev)
    assert pred == "meets"
    story_ref = SS.EventStoryRef(ev)()
    assert getattr(story_ref, "symbol", None) == "story1"

    # Relation with provenance and confidence
    rel = SS.make_relation("before", "story1_e0", "story1_e1", provenance_str="story1", confidence_str="1.0")
    assert SS.IsRelation(rel)() is M.truth_value
    kind = getattr(SS.RelationKind(rel)(), "symbol", None)
    assert kind == "before"
    prov = getattr(SS.RelationProvenance(rel)(), "symbol", None)
    assert prov == "story1"
    conf = getattr(SS.RelationConfidence(rel)(), "symbol", None)
    assert conf == "1.0"

    # Story
    story = SS.make_story("story1", "Test", ["story1_e0", "story1_e1"])
    assert SS.IsStory(story)() is M.truth_value

    print("test_pair_schemas PASSED")


def test_controlled_parser():
    text = "Alice meets Bob. then Bob gives book to Alice. Alice reads book because Bob gives book to Alice."
    parsed = SP.parse_controlled_story("s1", "Test", text)
    assert len(parsed.parsed_events) == 4  # meets, gives, reads, gives (cause)
    assert len(parsed.temporal_links) == 1
    assert len(parsed.causal_links) == 1
    assert "alice" in parsed.entities
    assert "bob" in parsed.entities

    terms = SP.parsed_story_to_terms(parsed)
    valid, errors = SP.validate_candidate_terms(terms)
    assert valid, f"validation failed: {errors}"

    print("test_controlled_parser PASSED")


def test_ingest_two_stories_and_link():
    story1_text = "Alice meets Bob. Bob gives book to Alice."
    story2_text = "Alice meets wolf in forest. Bob is in forest."

    p1 = SP.parse_controlled_story("story1", "S1", story1_text)
    p2 = SP.parse_controlled_story("story2", "S2", story2_text)

    t1 = SP.parsed_story_to_terms(p1)
    t2 = SP.parsed_story_to_terms(p2)

    gv = SA.build_graph_version(t1["entities"] + t2["entities"], t1["events"] + t2["events"], t1["relations"] + t2["relations"], [t1["story"], t2["story"]])

    proposals = SA.propose_entity_links(t1["entities"], t2["entities"], threshold=0.8)
    # Should find Alice and Bob
    assert len(proposals) >= 2, f"expected >=2 proposals, got {proposals}"
    names = [(p.name_a, p.name_b) for p in proposals]
    # Check Alice<->Alice present
    assert any("Alice" in a and "Alice" in b for a, b in names)

    approved = SA.approve_same_as_proposals(proposals, min_confidence=0.8)
    same_as_terms = SA.proposals_to_relation_terms(approved)
    gv_linked = SA.add_relations_to_graph_version(gv, same_as_terms)

    rels = SA.extract_relations_from_graph_version(gv_linked)
    same_as_rels = [r for r in rels if getattr(SS.RelationKind(r)(), "symbol", None) == "same-as"]
    assert len(same_as_rels) == len(approved)

    print("test_ingest_two_stories_and_link PASSED")


def test_connection_query():
    story1_text = "Alice meets Bob."
    story2_text = "Alice meets wolf in forest."

    p1 = SP.parse_controlled_story("story1", "S1", story1_text)
    p2 = SP.parse_controlled_story("story2", "S2", story2_text)
    t1 = SP.parsed_story_to_terms(p1)
    t2 = SP.parsed_story_to_terms(p2)

    gv = SA.build_graph_version(t1["entities"] + t2["entities"], t1["events"] + t2["events"], t1["relations"] + t2["relations"], [t1["story"], t2["story"]])
    proposals = SA.propose_entity_links(t1["entities"], t2["entities"], threshold=0.8)
    approved = SA.approve_same_as_proposals(proposals)
    gv_linked = SA.add_relations_to_graph_version(gv, SA.proposals_to_relation_terms(approved))

    # Find ids
    entities = SA.extract_entities_from_graph_version(gv_linked)
    def find_id(substr):
        for e in entities:
            if substr.lower() in SS.get_entity_name(e).lower():
                return getattr(SS.EntityId(e)(), "symbol", None)
        return None

    alice_id = find_id("alice")
    # There are two alices, pick first
    alice_ids = [getattr(SS.EntityId(e)(), "symbol", None) for e in entities if "alice" in SS.get_entity_name(e).lower()]
    wolf_id = find_id("wolf")

    assert alice_ids, "no alice found"
    assert wolf_id, "no wolf found"

    path = SA.find_connection_path(gv_linked, alice_ids[0], wolf_id)
    assert path is not None, f"no path from {alice_ids[0]} to {wolf_id}"
    assert len(path) >= 2

    print("test_connection_query PASSED")


def test_persistence():
    story1_text = "Alice meets Bob."
    story2_text = "Alice meets wolf."

    p1 = SP.parse_controlled_story("story1", "S1", story1_text)
    p2 = SP.parse_controlled_story("story2", "S2", story2_text)
    t1 = SP.parsed_story_to_terms(p1)
    t2 = SP.parsed_story_to_terms(p2)

    gv = SA.build_graph_version(t1["entities"] + t2["entities"], t1["events"] + t2["events"], [], [t1["story"], t2["story"]])
    proposals = SA.propose_entity_links(t1["entities"], t2["entities"], threshold=0.8)
    gv_linked = SA.add_relations_to_graph_version(gv, SA.proposals_to_relation_terms(proposals))

    import cat_theo_machine.machine as MachineModule
    import cat_theo_machine.labels as LabelsModule
    namespace = dict(vars(MachineModule))
    namespace.update(vars(LabelsModule))
    codec = Pers.SnapshotCodec(namespace)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "snap.json")
        snapshot = codec.capture_objects({"story_graph": gv_linked}, progress=M.false_value)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f)

        state = codec.load(path)
        loaded_gv = state.roots["story_graph"]

        # Reinstall symbols for accessor use
        for name in state.symbols:
            namespace[name] = state.symbols[name]
        from . import core as Core
        Core.sync_from_namespace(namespace)

        rels = []
        nodes = G.GraphNodes(loaded_gv)()
        cur = nodes
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            term = M.Head(cur)()
            if SS.IsRelation(term)() is M.truth_value:
                kind = getattr(SS.RelationKind(term)(), "symbol", None)
                src = getattr(SS.RelationSource(term)(), "symbol", None)
                tgt = getattr(SS.RelationTarget(term)(), "symbol", None)
                rels.append((kind, src, tgt))
            cur = M.Tail(cur)()

        same_as = [r for r in rels if r[0] == "same-as"]
        assert len(same_as) == len(proposals), f"expected {len(proposals)} same-as after reload, got {len(same_as)}"

    print("test_persistence PASSED")


def test_analogy_and_schema():
    # Analogous stories
    text_a = "Alice meets Bob. Bob gives book to Alice."
    text_b = "Carol meets Dave. Dave gives pen to Carol."

    p_a = SP.parse_controlled_story("storyA", "A", text_a)
    p_b = SP.parse_controlled_story("storyB", "B", text_b)
    t_a = SP.parsed_story_to_terms(p_a)
    t_b = SP.parsed_story_to_terms(p_b)

    mapping = SA.find_analogy_mapping(t_a["events"], t_b["events"], None, None)
    assert mapping is not None, "analogy mapping should be found"
    assert len(mapping) == 3  # alice->carol, bob->dave, book->pen

    gv_a = SA.build_graph_version(t_a["entities"], t_a["events"], t_a["relations"], [t_a["story"]])
    gv_b = SA.build_graph_version(t_b["entities"], t_b["events"], t_b["relations"], [t_b["story"]])

    schemas = SA.induce_schemas_from_graph_versions([gv_a, gv_b], min_support=2)
    assert len(schemas) >= 1
    # Should have meets,gives pattern
    assert any("meets" in s.pattern_events and "gives" in s.pattern_events for s in schemas)

    print("test_analogy_and_schema PASSED")


def run_all():
    test_pair_schemas()
    test_controlled_parser()
    test_ingest_two_stories_and_link()
    test_connection_query()
    test_persistence()
    test_analogy_and_schema()
    print("\nAll story machine tests PASSED")


if __name__ == "__main__":
    run_all()
