"""
Long-form generative narrator over its own discovered world-model.

Architecture:
WORLD MODEL -> DISCOVERED CONNECTIONS -> STORY STATE (compact StoryModel) -> NARRATIVE PLAN (revisable) -> PROSE (incremental, indefinite)

Key: story model remains small structured, prose can become millions of words, retrieval via graph not context window.

Behaves like:
story state -> retrieve relevant knowledge -> decide what should happen next -> generate passage -> update story state -> continue
"""

from . import machine as M
from . import graph as G
from . import labels as L
from .semantic_schema import Concept, IsConcept, ConceptCanonicalName
from .longform_schema import (
    StoryModel, StoryModelId, StoryModelEntities, StoryModelConnections, StoryModelThreads, StoryModelQuestions, StoryModelMotifs, StoryModelPassageRefs, StoryModelPosition,
    NarrativeThread, ThreadId,
    UnresolvedQuestion,
    Motif,
    ChronologyEntry, CausalLink,
    PassageRef,
    NarrativePlan, PlanId, PlanSegments, PlanCurrentIndex,
    Segment, SegmentId, SegmentFocus, SegmentConnections, SegmentIntent, SegmentStatus,
    Chapter, ChapterIndex,
    KnowledgeStatus
)
from .story_memory import BuildInitialStoryModel, UpdateStoryModelAfterPassage, RetrieveRelevantState, BuildChapterFromSegment
from .narrative_planner import (
    BuildNarrativeThreadsFromConcepts, BuildInitialQuestions, BuildInitialMotifs, BuildInitialPlan,
    SelectNextSegment, AdvancePlan, RevisePlanWithNewConnection, RevisePlanWithSteering,
    IntentLabel
)
from .longform_verbalizer import generate_passage_from_segment, generate_steered_passage
from .associative_engine import InventIntermediatesFromConcepts, FilterVerifiedIntermediates, BuildConnectionsViaIntermediates, FindExistingPathsBetweenConcepts, ActivateRelevantSubgraph
from .nl_parser import parse_utterance_to_goal, parse_followup, KNOWN_CONCEPTS
from .nl_cognitive_layer import get_conversational_state, build_initial_graph_version
from .semantic_schema import TaskType
from .story_alignment import BuildGraphVersion, AddRelationsToGraphVersion

# Global long-form state (persists across calls, like ConversationalState but more structured)
class LongformState:
    def __init__(self):
        self.story_model = M.EmptyList
        self.narrative_plan = M.EmptyList
        self.graph_version = None
        self.nodes = M.EmptyList
        self.relations = M.EmptyList
        self.chapters = M.EmptyList
        self.chapter_counter = 0
        self.prose_chain = M.EmptyList  # chain of prose texts (Char) for persistence, but not loaded into active context for generation
        self.goal_info = None

    def reset(self):
        self.story_model = M.EmptyList
        self.narrative_plan = M.EmptyList
        self.graph_version = None
        self.nodes = M.EmptyList
        self.relations = M.EmptyList
        self.chapters = M.EmptyList
        self.chapter_counter = 0
        self.prose_chain = M.EmptyList
        self.goal_info = None

_global_longform = LongformState()

def get_longform_state():
    return _global_longform

def reset_longform_state():
    global _global_longform
    _global_longform = LongformState()
    return _global_longform

def _chain_to_list(chain):
    result = []
    rem = chain
    while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
        result.append(M.Head(rem)())
        rem = M.Tail(rem)()
    return result

def _count_chain(chain):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return 0
    return 1 + _count_chain(M.Tail(chain)())

def _append_chain(a, b):
    if M.IdentityCompare(a, M.EmptyList)() is M.truth_value:
        return b
    head = M.Head(a)()
    tail = M.Tail(a)()
    rest = _append_chain(tail, b)
    return M.Pair(head, rest)

def init_longform_story(utterance, existing_nodes=None, existing_relations=None, existing_gv=None):
    """
    1. Interpret request
    2. Identify relevant entities
    3. Search graph for interesting connections
    4. Invent intermediate concepts
    5. Evaluate and verify
    6. Construct narrative trajectory
    7. Generate first passage
    8. Store narrative state
    """
    state = get_longform_state()
    # 1-2) Interpret
    goal_info = parse_utterance_to_goal(utterance, goal_counter=state.chapter_counter)
    # 3) World model activation
    if existing_gv is not None:
        gv = existing_gv
        nodes = existing_nodes if existing_nodes else M.EmptyList
    else:
        gv, nodes = build_initial_graph_version(existing_nodes, existing_relations)
    activated_gv = ActivateRelevantSubgraph(gv, goal_info["concept_chain"])()
    existing_paths = FindExistingPathsBetweenConcepts(activated_gv, goal_info["concept_chain"])()
    # 4-5) Invent and verify
    provenance = M.Char("longform_invention")
    invented = InventIntermediatesFromConcepts(goal_info["concept_chain"], provenance)()
    verified = FilterVerifiedIntermediates(invented, activated_gv)()
    connections = BuildConnectionsViaIntermediates(goal_info["concept_chain"], verified, provenance)()

    # Build story state layers
    threads = BuildNarrativeThreadsFromConcepts(goal_info["concept_chain"], provenance)()
    questions = BuildInitialQuestions(goal_info["concept_chain"], connections, provenance)()
    motifs = BuildInitialMotifs(goal_info["concept_chain"], provenance)()

    model_id = M.Char("story_model_" + str(state.chapter_counter))
    story_model = BuildInitialStoryModel(model_id, goal_info["goal_term"], goal_info["concept_chain"], connections, threads, questions, motifs, provenance)()

    # Narrative plan (dynamically maintained, revisable)
    plan = BuildInitialPlan(goal_info["goal_term"], goal_info["concept_chain"], connections, verified, threads, provenance)()

    # Select first segment and generate passage (without requiring whole story in memory)
    next_seg = SelectNextSegment(plan, story_model)()
    if M.IdentityCompare(next_seg, M.EmptyList)() is M.truth_value:
        # No segment, create default
        prose = "The story begins, but the planner found no next segment."
    else:
        relevant = RetrieveRelevantState(story_model, SegmentFocus(next_seg)())()
        prose = generate_passage_from_segment(next_seg, story_model, relevant, chapter_index=state.chapter_counter)

    # Update story state and store
    # Build passage ref
    ref_id = M.Char("passage_" + str(state.chapter_counter))
    chapter_idx = M.Char(str(state.chapter_counter))
    summary = M.Char(prose[:200])  # compact summary, not full prose in model
    focus = SegmentFocus(next_seg)() if M.IdentityCompare(next_seg, M.EmptyList)() is M.false_value else M.EmptyList
    passage_ref = PassageRef(ref_id, chapter_idx, summary, focus, provenance)()

    # Update model
    new_model = UpdateStoryModelAfterPassage(story_model, M.EmptyList, M.EmptyList, connections, passage_ref, M.EmptyList, M.EmptyList, provenance)()
    # Advance plan
    new_plan = AdvancePlan(plan)()

    # Build chapter
    chapter_id = M.Char("chapter_" + str(state.chapter_counter))
    title = M.Char("Chapter " + str(state.chapter_counter + 1))
    prose_char = M.Char(prose)
    chapter = BuildChapterFromSegment(chapter_id, chapter_idx, title, next_seg, prose_char, new_model, provenance)()

    # Update global state (compact model, not full prose in active context)
    state.story_model = new_model
    state.narrative_plan = new_plan
    state.graph_version = gv
    state.nodes = nodes
    state.relations = existing_relations if existing_relations else M.EmptyList
    state.chapters = M.Pair(chapter, state.chapters)
    state.prose_chain = M.Pair(prose_char, state.prose_chain)
    state.chapter_counter += 1
    state.goal_info = goal_info

    # Also update nodes with invented
    new_nodes = nodes
    rem = verified
    while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
        new_nodes = M.Pair(M.Head(rem)(), new_nodes)
        rem = M.Tail(rem)()
    rem = connections
    while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
        new_nodes = M.Pair(M.Head(rem)(), new_nodes)
        rem = M.Tail(rem)()
    state.nodes = new_nodes
    state.graph_version = BuildGraphVersion(new_nodes)()
    if M.IdentityCompare(state.relations, M.EmptyList)() is M.false_value:
        state.graph_version = AddRelationsToGraphVersion(state.graph_version, state.relations)()

    return {
        "goal_info": goal_info,
        "story_model": new_model,
        "narrative_plan": new_plan,
        "chapter": chapter,
        "prose": prose,
        "graph_version": state.graph_version,
        "nodes": new_nodes,
        "invented_intermediates": verified,
        "connections": connections,
        "threads": threads,
        "questions": questions,
        "motifs": motifs,
    }

def continue_story(steering_utterance=None):
    """
    Generate next passage from persistent state, without requiring previous prose in memory.
    Story state -> retrieve relevant knowledge -> decide what next -> generate passage -> update story state -> continue
    Supports indefinite continuation.
    """
    state = get_longform_state()
    if M.IdentityCompare(state.story_model, M.EmptyList)() is M.truth_value:
        return {"type": "error", "prose": "No existing story to continue. Start with 'Tell me a story about...'"}

    provenance = M.Char("longform_continue")

    # If steering, revise plan (modify persistent story state rather than reset)
    if steering_utterance:
        lower = steering_utterance.lower()
        # Check if steering is a new discovery request or a steering command
        if any(k in lower for k in ["keep going", "continue", "deeper", "return to", "stranger", "unexpected", "perspective", "central", "don't leave", "more slowly", "explain"]):
            # Revise plan with steering
            steering_char = M.Char(steering_utterance)
            new_plan = RevisePlanWithSteering(state.narrative_plan, steering_char, provenance)()
            state.narrative_plan = new_plan
            # Generate steered passage using compact model retrieval, not full prose
            relevant = RetrieveRelevantState(state.story_model, M.EmptyList)()
            prose = generate_steered_passage(steering_utterance, state.story_model, relevant, state.chapter_counter)

            # Update model with steered passage
            ref_id = M.Char("passage_" + str(state.chapter_counter))
            chapter_idx = M.Char(str(state.chapter_counter))
            summary = M.Char(prose[:200])
            passage_ref = PassageRef(ref_id, chapter_idx, summary, M.EmptyList, provenance)()
            new_model = UpdateStoryModelAfterPassage(state.story_model, M.EmptyList, M.EmptyList, M.EmptyList, passage_ref, M.EmptyList, M.EmptyList, provenance)()
            state.story_model = new_model

            chapter_id = M.Char("chapter_" + str(state.chapter_counter))
            title = M.Char("Steered Chapter " + str(state.chapter_counter + 1))
            prose_char = M.Char(prose)
            # For steered, we create a chapter with empty segment placeholder
            empty_seg = M.EmptyList
            chapter = BuildChapterFromSegment(chapter_id, chapter_idx, title, empty_seg, prose_char, new_model, provenance)()
            state.chapters = M.Pair(chapter, state.chapters)
            state.prose_chain = M.Pair(prose_char, state.prose_chain)
            state.chapter_counter += 1

            return {
                "type": "steered_continuation",
                "prose": prose,
                "story_model": new_model,
                "narrative_plan": new_plan,
                "chapter": chapter,
            }
        else:
            # Treat as new discovery during story: search for new connections and reorganize narrative around it
            # This demonstrates: machine can discover new connection during story and reorganize narrative around it
            goal_info = parse_utterance_to_goal(steering_utterance, goal_counter=state.chapter_counter)
            # Invent new intermediates from new concepts + old concepts
            combined_concepts = _append_chain(state.goal_info["concept_chain"] if state.goal_info else M.EmptyList, goal_info["concept_chain"])
            invented = InventIntermediatesFromConcepts(combined_concepts, provenance)()
            verified = FilterVerifiedIntermediates(invented, state.graph_version)()
            connections = BuildConnectionsViaIntermediates(combined_concepts, verified, provenance)()
            if _count_chain(verified) > 0:
                # Pick first new intermediate as discovery
                new_inter = M.Head(verified)()
                new_conn = M.Head(connections)() if _count_chain(connections) > 0 else M.EmptyList
                if M.IdentityCompare(new_conn, M.EmptyList)() is M.false_value:
                    new_plan = RevisePlanWithNewConnection(state.narrative_plan, new_conn, new_inter, provenance)()
                    state.narrative_plan = new_plan
                    # Generate passage about discovery
                    next_seg = SelectNextSegment(new_plan, state.story_model)()
                    relevant = RetrieveRelevantState(state.story_model, SegmentFocus(next_seg)() if M.IdentityCompare(next_seg, M.EmptyList)() is M.false_value else M.EmptyList)()
                    # Explain discovery
                    from .verbalizer import intermediate_to_explanation
                    discovery_text = intermediate_to_explanation(new_inter)
                    prose = generate_passage_from_segment(next_seg, state.story_model, relevant, chapter_index=state.chapter_counter, discovered_during_generation=discovery_text)

                    ref_id = M.Char("passage_" + str(state.chapter_counter))
                    chapter_idx = M.Char(str(state.chapter_counter))
                    summary = M.Char(prose[:200])
                    passage_ref = PassageRef(ref_id, chapter_idx, summary, M.Pair(new_inter, M.EmptyList), provenance)()
                    new_model = UpdateStoryModelAfterPassage(state.story_model, M.Pair(new_inter, M.EmptyList), M.EmptyList, M.Pair(new_conn, M.EmptyList), passage_ref, M.EmptyList, M.EmptyList, provenance)()
                    state.story_model = new_model

                    chapter_id = M.Char("chapter_" + str(state.chapter_counter))
                    title = M.Char("Discovery Chapter " + str(state.chapter_counter + 1))
                    prose_char = M.Char(prose)
                    chapter = BuildChapterFromSegment(chapter_id, chapter_idx, title, next_seg, prose_char, new_model, provenance)()
                    state.chapters = M.Pair(chapter, state.chapters)
                    state.prose_chain = M.Pair(prose_char, state.prose_chain)
                    state.chapter_counter += 1

                    return {
                        "type": "discovery_reorganization",
                        "prose": prose,
                        "new_intermediate": new_inter,
                        "new_connection": new_conn,
                        "story_model": new_model,
                        "narrative_plan": new_plan,
                    }

    # Normal continuation: retrieve relevant state, decide next, generate, update
    next_seg = SelectNextSegment(state.narrative_plan, state.story_model)()
    if M.IdentityCompare(next_seg, M.EmptyList)() is M.truth_value:
        # If plan exhausted, build new plan from current model (indefinite continuation)
        # This demonstrates indefinite continuation without storing entire previous story in active context
        # Retrieve all entities from model and invent new connections
        try:
            entities = StoryModelEntities(state.story_model)()
            invented = InventIntermediatesFromConcepts(entities, provenance)()
            verified = FilterVerifiedIntermediates(invented, state.graph_version)()
            connections = BuildConnectionsViaIntermediates(entities, verified, provenance)()
            threads = StoryModelThreads(state.story_model)()
            # Build new plan with new discoveries
            goal = M.EmptyList
            try:
                from .longform_schema import StoryModelGoal
                goal = StoryModelGoal(state.story_model)()
            except Exception:
                pass
            new_plan = BuildInitialPlan(goal, entities, connections, verified, threads, provenance)()
            state.narrative_plan = new_plan
            next_seg = SelectNextSegment(new_plan, state.story_model)()
        except Exception:
            return {"type": "error", "prose": "Story plan exhausted and could not build new plan. The story has reached a natural pause, but can be steered to continue."}

    if M.IdentityCompare(next_seg, M.EmptyList)() is M.truth_value:
        return {"type": "complete", "prose": "The narrative plan is complete. You can steer it to continue: 'Keep going', 'Go deeper into...', 'Find a stranger connection', etc."}

    relevant = RetrieveRelevantState(state.story_model, SegmentFocus(next_seg)())()
    prose = generate_passage_from_segment(next_seg, state.story_model, relevant, chapter_index=state.chapter_counter)

    # Update story state
    ref_id = M.Char("passage_" + str(state.chapter_counter))
    chapter_idx = M.Char(str(state.chapter_counter))
    summary = M.Char(prose[:200])
    focus = SegmentFocus(next_seg)()
    passage_ref = PassageRef(ref_id, chapter_idx, summary, focus, provenance)()

    new_model = UpdateStoryModelAfterPassage(state.story_model, M.EmptyList, M.EmptyList, SegmentConnections(next_seg)(), passage_ref, M.EmptyList, M.EmptyList, provenance)()
    new_plan = AdvancePlan(state.narrative_plan)()

    chapter_id = M.Char("chapter_" + str(state.chapter_counter))
    title = M.Char("Chapter " + str(state.chapter_counter + 1))
    prose_char = M.Char(prose)
    chapter = BuildChapterFromSegment(chapter_id, chapter_idx, title, next_seg, prose_char, new_model, provenance)()

    state.story_model = new_model
    state.narrative_plan = new_plan
    state.chapters = M.Pair(chapter, state.chapters)
    state.prose_chain = M.Pair(prose_char, state.prose_chain)
    state.chapter_counter += 1

    return {
        "type": "continuation",
        "prose": prose,
        "story_model": new_model,
        "narrative_plan": new_plan,
        "chapter": chapter,
    }

def get_full_prose():
    # Returns all prose in order (for persistence, not for active generation)
    state = get_longform_state()
    # prose_chain is reverse order (newest first), need reverse
    acc = []
    rem = state.prose_chain
    while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
        acc.append(M.Head(rem)())
        rem = M.Tail(rem)()
    # acc is newest first, reverse to oldest first
    acc.reverse()
    full = []
    for p in acc:
        try:
            full.append(p())
        except Exception:
            full.append(str(p))
    return "\n\n".join(full)

def get_story_model_summary():
    state = get_longform_state()
    if M.IdentityCompare(state.story_model, M.EmptyList)() is M.truth_value:
        return "No story model"
    try:
        entities = StoryModelEntities(state.story_model)()
        connections = StoryModelConnections(state.story_model)()
        threads = StoryModelThreads(state.story_model)()
        passage_refs = StoryModelPassageRefs(state.story_model)()
        position = StoryModelPosition(state.story_model)()
        ent_count = _count_chain(entities)
        conn_count = _count_chain(connections)
        thread_count = _count_chain(threads)
        passage_count = _count_chain(passage_refs)
        try:
            pos = position()
        except Exception:
            pos = "0"
        return f"StoryModel: {ent_count} entities, {conn_count} connections, {thread_count} threads, {passage_count} passages, position {pos}, chapter_counter {state.chapter_counter} (compact model, prose is separate)"
    except Exception as e:
        return f"StoryModel summary failed: {e}"


def save_longform_checkpoint(path):
    """Save compact story model + plan + graph_version + prose chain using wire serialization."""
    import os
    from . import wire as W
    state = get_longform_state()
    # Bundle: Pair(story_model, Pair(narrative_plan, Pair(graph_version, Pair(prose_chain, Pair(Char(chapter_counter), Empty)))))
    try:
        counter_char = M.Char(str(state.chapter_counter))
        bundle = M.Pair(state.story_model, M.Pair(state.narrative_plan, M.Pair(state.graph_version if state.graph_version else M.EmptyList, M.Pair(state.prose_chain, M.Pair(counter_char, M.EmptyList)))))
        blob = W.serialize_term(bundle)
        header = "WIRE1"
        payload = header + "\n" + blob.decode('utf-8') + "\n"
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, path)
        return path
    except Exception as e:
        print(f"save_longform_checkpoint failed: {e}")
        return None

def load_longform_checkpoint(path):
    """Load compact story model + plan + graph_version + prose chain."""
    from . import wire as W
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        if not lines or lines[0] != "WIRE1":
            return None
        blob = lines[1].encode('utf-8')
        bundle = W.deserialize_term(blob)
        story_model = M.Head(bundle)()
        narrative_plan = M.Head(M.Tail(bundle)())()
        graph_version = M.Head(M.Tail(M.Tail(bundle)())())()
        prose_chain = M.Head(M.Tail(M.Tail(M.Tail(bundle)())())())()
        counter_char = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())()
        state = get_longform_state()
        state.story_model = story_model
        state.narrative_plan = narrative_plan
        state.graph_version = graph_version
        state.prose_chain = prose_chain
        try:
            state.chapter_counter = int(counter_char())
        except Exception:
            state.chapter_counter = 0
        return state
    except Exception as e:
        print(f"load_longform_checkpoint failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_longform_prose_checkpoint(path):
    """Save full prose as Char for inspection, not used for active generation."""
    import os
    from . import wire as W
    try:
        full = get_full_prose()
        # Save as Pair(story_model, Char(prose))
        state = get_longform_state()
        prose_char = M.Char(full[:50000])  # limit for wire
        bundle = M.Pair(state.story_model, M.Pair(prose_char, M.EmptyList))
        blob = W.serialize_term(bundle)
        payload = "WIRE1\n" + blob.decode('utf-8') + "\n"
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, path)
        return path
    except Exception as e:
        print(f"save_longform_prose failed: {e}")
        return None

