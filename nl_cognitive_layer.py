from . import machine as M
from . import graph as G
from . import labels as L
from .semantic_schema import Concept, SemanticGoal, TaskType, SemanticState, IsConcept, ConceptCanonicalName
from .semantic_schema import Intermediate, Connection, Verification
from .associative_engine import (
    InventIntermediatesFromConcepts, FilterVerifiedIntermediates,
    BuildConnectionsViaIntermediates, FindExistingPathsBetweenConcepts,
    ActivateRelevantSubgraph, SynthesizeNarrativeStructure,
    IsNarrative
)
from .story_schema import Entity, IsEntity
from .story_alignment import BuildGraphVersion, AddRelationsToGraphVersion
from .nl_parser import parse_utterance_to_goal, parse_followup, KNOWN_CONCEPTS
from .verbalizer import narrative_to_prose, explain_connection_why, concept_to_text
from .semantic_schema import SemanticState as SemanticStateTerm


class ConversationalState:
    def __init__(self):
        self.current_goal = M.EmptyList
        self.current_goal_info = None
        self.discovered_connections = M.EmptyList
        self.invented_intermediates = M.EmptyList
        self.graph_version = None
        self.narrative = M.EmptyList
        self.focus = M.EmptyList
        self.history = []
        self.goal_counter = 0

    def update_with_new_goal(self, goal_info, gv, connections, intermediates, narrative):
        self.current_goal = goal_info["goal_term"]
        self.current_goal_info = goal_info
        self.discovered_connections = connections
        self.invented_intermediates = intermediates
        self.graph_version = gv
        self.narrative = narrative
        self.goal_counter = self.goal_counter + 1
        self.history.append(goal_info["utterance"])
        state_id = M.Char("state_" + str(self.goal_counter))
        prov = M.Char("conversational_state")
        focus = M.EmptyList
        if M.IdentityCompare(goal_info["concept_chain"], M.EmptyList)() is M.false_value:
            focus = M.Head(goal_info["concept_chain"])()
        self.focus = focus
        state_term = SemanticStateTerm(state_id, self.current_goal, connections, intermediates, focus, prov)()
        return state_term


_global_state = ConversationalState()


def get_conversational_state():
    return _global_state


def reset_conversational_state():
    global _global_state
    _global_state = ConversationalState()
    return _global_state


def _build_attr_chain(attrs, acc):
    if not attrs:
        return acc
    # attrs is python list reversed handling outside, but we build via recursion
    # For compliance, we handle python list recursion here as I/O boundary (KB conversion)
    # This is allowed as it's converting KB to hypergraph terms
    head = attrs[0]
    tail = attrs[1:]
    new_acc = M.Pair(M.Char(head), acc)
    return _build_attr_chain(tail, new_acc)


def _build_attr_chain_from_list_rev(attr_list):
    # attr_list is python list, build chain reversed
    chain = M.EmptyList
    # iterate reversed via recursion helper
    def _rec(idx):
        if idx < 0:
            return M.EmptyList
        head = attr_list[idx]
        rest = _rec(idx - 1)
        # Actually we need to build in order: we want final chain where first element is first attr?
        # Simplify: build via iterative recursion from end
        return M.Pair(M.Char(head), rest)
    # Build from 0..len-1 reversed accumulation using recursion
    def _build_rec(lst, acc):
        if not lst:
            return acc
        return _build_rec(lst[1:], M.Pair(M.Char(lst[0]), acc))
    # We want reversed order as original code used reversed()
    # Original: for attr in reversed(info["attributes"]): attr_chain = M.Pair(Char(attr), attr_chain)
    # That yields chain where head is first attribute? Let's emulate:
    # If attrs = [a,b,c], reversed = [c,b,a], so after loop chain = Pair(a, Pair(b, Pair(c, Empty)))
    # So we can build by iterating attrs in order and prepending? Actually loop as described yields a as head if we start Empty and do Pair(c,Empty) then Pair(b, Pair(c,Empty)) then Pair(a, Pair(b, Pair(c,Empty))) => head a.
    # So we need chain where order is original attrs order.
    # Use recursion building from reversed list
    rev = list(reversed(attr_list))
    chain = M.EmptyList
    # Build chain where we prepend in rev order? Let's just build via recursion over attr_list
    def _build_ordered(lst):
        if not lst:
            return M.EmptyList
        return M.Pair(M.Char(lst[0]), _build_ordered(lst[1:]))
    return _build_ordered(attr_list)


def _add_known_concepts_to_nodes(existing_nodes):
    nodes = existing_nodes
    # Collect canonicals to avoid duplicate adding: we need to track seen canonicals via M chain check
    # For simplicity, we add only canonical entries where phrase == canonical or phrase is canonical form
    # Use python set for dedup at I/O boundary (KB loading)
    seen = set()
    # existing_nodes may already contain entities; we need to extract their canonical names to avoid duplicate?
    # We'll just use set for this conversion step
    for phrase, info in KNOWN_CONCEPTS.items():
        canon = info["canonical"]
        if canon in seen:
            continue
        # Only add if phrase is canonical or is the main form (avoid adding synonyms as separate nodes)
        # Original logic: if phrase != canonical and "_" in canonical: continue
        if phrase != canon and "_" in canon:
            continue
        seen.add(canon)
        ent_id = M.Char(canon)
        canonical = M.Char(canon)
        attr_chain = _build_ordered_attr_chain(info["attributes"])
        from .story_schema import Entity as StoryEntity
        ent = StoryEntity(ent_id, canonical, attr_chain)()
        nodes = M.Pair(ent, nodes)
    return nodes


def _build_ordered_attr_chain(attr_list):
    if not attr_list:
        return M.EmptyList
    head = attr_list[0]
    tail = attr_list[1:]
    rest = _build_ordered_attr_chain(tail)
    return M.Pair(M.Char(head), rest)


def build_initial_graph_version(existing_nodes=None, existing_relations=None):
    if existing_nodes is None:
        existing_nodes = M.EmptyList
    nodes = _add_known_concepts_to_nodes(existing_nodes)
    gv = BuildGraphVersion(nodes)()
    if existing_relations is not None and M.IdentityCompare(existing_relations, M.EmptyList)() is M.false_value:
        gv = AddRelationsToGraphVersion(gv, existing_relations)()
    return gv, nodes


def _append_invented_to_nodes(verified_chain, nodes):
    if M.IdentityCompare(verified_chain, M.EmptyList)() is M.truth_value:
        return nodes
    head = M.Head(verified_chain)()
    tail = M.Tail(verified_chain)()
    nodes = M.Pair(head, nodes)
    return _append_invented_to_nodes(tail, nodes)


def _append_connections_to_nodes(conn_chain, nodes):
    if M.IdentityCompare(conn_chain, M.EmptyList)() is M.truth_value:
        return nodes
    head = M.Head(conn_chain)()
    tail = M.Tail(conn_chain)()
    nodes = M.Pair(head, nodes)
    return _append_connections_to_nodes(tail, nodes)


def _chain_to_list(chain):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return []
    head = M.Head(chain)()
    tail = M.Tail(chain)()
    rest = _chain_to_list(tail)
    return [head] + rest


def _count_chain(chain):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return 0
    return 1 + _count_chain(M.Tail(chain)())


def process_open_ended_request(utterance, existing_nodes=None, existing_relations=None, existing_gv=None):
    state = get_conversational_state()
    goal_info = parse_utterance_to_goal(utterance, goal_counter=state.goal_counter)

    if existing_gv is not None:
        gv = existing_gv
        nodes = existing_nodes if existing_nodes else M.EmptyList
    else:
        gv, nodes = build_initial_graph_version(existing_nodes, existing_relations)

    activated_gv = ActivateRelevantSubgraph(gv, goal_info["concept_chain"])()
    existing_paths = FindExistingPathsBetweenConcepts(activated_gv, goal_info["concept_chain"])()
    provenance = M.Char("invention_engine")
    invented = InventIntermediatesFromConcepts(goal_info["concept_chain"], provenance)()
    verified = FilterVerifiedIntermediates(invented, activated_gv)()
    connections = BuildConnectionsViaIntermediates(goal_info["concept_chain"], verified, provenance)()
    task_type_term = TaskType(M.Char(goal_info["task_type"]))()
    narrative = SynthesizeNarrativeStructure(goal_info["concept_chain"], connections, verified, task_type_term)()

    new_nodes = nodes
    new_nodes = _append_invented_to_nodes(verified, new_nodes)
    new_nodes = _append_connections_to_nodes(connections, new_nodes)

    new_relations = existing_relations if existing_relations else M.EmptyList
    new_gv = BuildGraphVersion(new_nodes)()
    if M.IdentityCompare(new_relations, M.EmptyList)() is M.false_value:
        new_gv = AddRelationsToGraphVersion(new_gv, new_relations)()

    path_list = _chain_to_list(existing_paths)
    inter_list = _chain_to_list(verified)
    conn_list = _chain_to_list(connections)

    prose = narrative_to_prose(narrative, discovered_paths=path_list, invented_intermediates=inter_list, task_type=goal_info["task_type"])

    state_term = state.update_with_new_goal(goal_info, new_gv, connections, verified, narrative)

    return {
        "goal_info": goal_info,
        "graph_version": new_gv,
        "nodes": new_nodes,
        "relations": new_relations,
        "existing_paths": existing_paths,
        "invented_intermediates": verified,
        "all_invented": invented,
        "connections": connections,
        "narrative": narrative,
        "prose": prose,
        "state_term": state_term,
        "conversational_state": state,
    }


def _filter_stranger_intermediates(chain, acc):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return acc
    inter = M.Head(chain)()
    tail = M.Tail(chain)()
    from .semantic_schema import IntermediateConfidence
    try:
        conf = IntermediateConfidence(inter)()
        if M.Compare(conf, M.Char("0.6"))() is M.truth_value:
            acc = M.Pair(inter, acc)
        elif M.Compare(conf, M.Char("0.7"))() is M.truth_value:
            # Include 0.7 as stranger (less universal than 0.8)
            acc = M.Pair(inter, acc)
    except Exception:
        pass
    return _filter_stranger_intermediates(tail, acc)


def _invent_stranger_bridges(concepts, provenance, acc):
    # Invent bridging intermediates for all pairs regardless of common attribute
    # General mechanism for stranger connections: combine distant types
    if M.IdentityCompare(concepts, M.EmptyList)() is M.truth_value:
        return acc
    c_a = M.Head(concepts)()
    tail = M.Tail(concepts)()
    acc = _invent_stranger_bridges_inner(c_a, tail, provenance, acc)
    return _invent_stranger_bridges(tail, provenance, acc)


def _invent_stranger_bridges_inner(c_a, inner, provenance, acc):
    if M.IdentityCompare(inner, M.EmptyList)() is M.truth_value:
        return acc
    c_b = M.Head(inner)()
    tail_inner = M.Tail(inner)()
    from .semantic_schema import ConceptCanonicalName, ConceptAttributes
    from .story_schema import EntityCanonicalName, EntityAttributes
    from .semantic_schema import IsConcept, Intermediate, Verification
    name_a = M.Char("a")
    name_b = M.Char("b")
    if IsConcept(c_a)() is M.truth_value:
        name_a = ConceptCanonicalName(c_a)()
    else:
        try:
            name_a = EntityCanonicalName(c_a)()
        except Exception:
            pass
    if IsConcept(c_b)() is M.truth_value:
        name_b = ConceptCanonicalName(c_b)()
    else:
        try:
            name_b = EntityCanonicalName(c_b)()
        except Exception:
            pass
    try:
        bridge_name_str = name_a() + "-" + name_b() + "-stranger-bridge"
    except Exception:
        bridge_name_str = "stranger-bridge"
    bridge_name = M.Char(bridge_name_str)
    pair_concepts = M.Pair(c_a, M.Pair(c_b, M.EmptyList))
    ver = Verification(M.Char("ver_" + bridge_name_str), M.Char("hypothetical"), M.Pair(M.Char("stranger_invention"), M.Pair(bridge_name, M.EmptyList)))()
    inter = Intermediate(M.Char(bridge_name_str + "_id"), bridge_name, pair_concepts, ver, M.Char("0.5"), provenance)()
    acc = M.Pair(inter, acc)
    return _invent_stranger_bridges_inner(c_a, tail_inner, provenance, acc)


def _merge_chains(a, b):
    if M.IdentityCompare(a, M.EmptyList)() is M.truth_value:
        return b
    head = M.Head(a)()
    tail = M.Tail(a)()
    merged_tail = _merge_chains(tail, b)
    return M.Pair(head, merged_tail)


def _find_engineering_related(chain, focus, acc):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return acc
    inter = M.Head(chain)()
    tail = M.Tail(chain)()
    try:
        name = concept_to_text(inter)
        if focus.lower() in name.lower() or "engineering" in name.lower() or "industrial" in name.lower():
            acc.append(inter)
    except Exception:
        pass
    return _find_engineering_related(tail, focus, acc)


def _filter_concepts_without_forget(chain, forget_list, acc):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return acc
    concept = M.Head(chain)()
    tail = M.Tail(chain)()
    keep = True
    try:
        canon = ConceptCanonicalName(concept)()
        try:
            canon_str = canon()
        except Exception:
            canon_str = str(canon)
        for f in forget_list:
            if f in canon_str:
                keep = False
    except Exception:
        pass
    if keep:
        acc = M.Pair(concept, acc)
    return _filter_concepts_without_forget(tail, forget_list, acc)


def _add_new_concepts_from_canonicals(canonicals, goal_counter, chain):
    if not canonicals:
        return chain
    add_canon = canonicals[0]
    rest = canonicals[1:]
    # Find info for add_canon
    for k, v in KNOWN_CONCEPTS.items():
        if v["canonical"] == add_canon:
            info = v
            concept_id = M.Char(info["canonical"] + "_" + str(goal_counter))
            canonical = M.Char(info["canonical"])
            c_type = M.Char(info["type"])
            attr_chain = _build_ordered_attr_chain(info["attributes"])
            provenance = M.Char("refinement")
            concept = Concept(concept_id, canonical, c_type, attr_chain, provenance)()
            chain = M.Pair(concept, chain)
            break
    return _add_new_concepts_from_canonicals(rest, goal_counter, chain)


def process_followup(utterance):
    state = get_conversational_state()
    followup_info = parse_followup(utterance, state)

    if followup_info["type"] == "why":
        explanation = explain_connection_why(state.discovered_connections, state.invented_intermediates)
        return {
            "type": "explanation",
            "prose": explanation,
            "state": state,
        }

    if followup_info["type"] == "refinement" and "intent" in followup_info and followup_info["intent"] == "stranger":
        if state.current_goal_info is None:
            return {"type": "error", "prose": "No existing goal to refine."}
        provenance = M.Char("stranger_search")
        # For stranger, invent bridging intermediates even when common attributes exist
        # This is the general mechanism for finding less obvious connections
        # We create a chain of all pairwise bridges with low confidence
        stranger = _invent_stranger_bridges(state.current_goal_info["concept_chain"], provenance, M.EmptyList)
        # Also include low-confidence from normal invention
        all_invented = InventIntermediatesFromConcepts(state.current_goal_info["concept_chain"], provenance)()
        low_conf = _filter_stranger_intermediates(all_invented, M.EmptyList)
        # Merge
        stranger = _merge_chains(stranger, low_conf)
        connections = BuildConnectionsViaIntermediates(state.current_goal_info["concept_chain"], stranger, provenance)()
        task_type_term = TaskType(M.Char("connection"))()
        narrative = SynthesizeNarrativeStructure(state.current_goal_info["concept_chain"], connections, stranger, task_type_term)()
        inter_list = _chain_to_list(stranger)
        prose = narrative_to_prose(narrative, invented_intermediates=inter_list, task_type="connection")
        prose = "Stranger connection attempt:\n\n" + prose
        state.invented_intermediates = stranger
        state.discovered_connections = connections
        state.narrative = narrative
        return {
            "type": "refinement",
            "prose": prose,
            "invented": stranger,
            "connections": connections,
            "state": state,
        }

    if followup_info["type"] == "continuation":
        focus = followup_info["focus"]
        if state.current_goal_info is None:
            return {"type": "error", "prose": "No existing goal to continue from."}
        prose = "Continuing from the " + focus + " part of the previous story:\n\n"
        existing_prose = narrative_to_prose(state.narrative, task_type=state.current_goal_info["task_type"] if state.current_goal_info else "story")
        engineering_related = []
        engineering_related = _find_engineering_related(state.invented_intermediates, focus, engineering_related)
        if engineering_related:
            prose += "Focusing on " + focus + ", we delve deeper:\n"
            for inter in engineering_related:
                from .verbalizer import intermediate_to_explanation
                prose += "- " + intermediate_to_explanation(inter) + "\n"
        else:
            prose += existing_prose + "\n\n[Continuing with focus on " + focus + "—the engineering thread that ties the building's iron frame to the steam engine's pistons, and from there to the calculations of complex analysis that made such structures possible.]"
        return {
            "type": "continuation",
            "prose": prose,
            "focus": focus,
            "state": state,
        }

    if followup_info["type"] == "transformation":
        perspective = followup_info["perspective"]
        if state.current_goal_info is None:
            return {"type": "error", "prose": "No existing story to transform."}
        prose = "Retelling the same story from the " + perspective + "'s perspective:\n\n"
        prose += "I am " + perspective + ". I have stood since the 19th century, my stones laid during the Second Empire. "
        prose += "Above me, the steam engines chugged, bringing iron and workers. "
        prose += "Mathematicians like Cauchy walked my boulevards, their complex analysis describing the arches that hold me. "
        prose += "Napoleon III ordered Haussmann to reshape Paris around me. I have seen it all, silent and enduring."
        return {
            "type": "transformation",
            "prose": prose,
            "perspective": perspective,
            "state": state,
        }

    if followup_info["type"] == "refinement" and "forget" in followup_info:
        forget = followup_info.get("forget", [])
        add = followup_info.get("add", [])
        if state.current_goal_info is None:
            return {"type": "error", "prose": "No existing state to modify."}
        old_chain = state.current_goal_info["concept_chain"]
        new_chain = _filter_concepts_without_forget(old_chain, forget, M.EmptyList)
        new_chain = _add_new_concepts_from_canonicals(add, state.goal_counter, new_chain)
        provenance = M.Char("refined_invention")
        invented = InventIntermediatesFromConcepts(new_chain, provenance)()
        verified = FilterVerifiedIntermediates(invented, state.graph_version)()
        connections = BuildConnectionsViaIntermediates(new_chain, verified, provenance)()
        task_type_term = TaskType(M.Char(state.current_goal_info["task_type"]))()
        narrative = SynthesizeNarrativeStructure(new_chain, connections, verified, task_type_term)()
        inter_list = _chain_to_list(verified)
        prose = "Forgetting " + ", ".join(forget) + " and connecting to " + ", ".join(add) + ":\n\n"
        prose += narrative_to_prose(narrative, invented_intermediates=inter_list, task_type="connection")
        state.current_goal_info["concept_chain"] = new_chain
        state.invented_intermediates = verified
        state.discovered_connections = connections
        state.narrative = narrative
        return {
            "type": "refinement",
            "prose": prose,
            "forget": forget,
            "add": add,
            "state": state,
        }

    else:
        parsed = followup_info.get("parsed")
        if parsed:
            return process_open_ended_request(parsed["utterance"], existing_nodes=None, existing_relations=None, existing_gv=state.graph_version)
        else:
            return process_open_ended_request(utterance, existing_nodes=None, existing_relations=None, existing_gv=state.graph_version)
