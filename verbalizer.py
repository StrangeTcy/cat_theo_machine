from . import machine as M
from .semantic_schema import IsConcept, ConceptCanonicalName, ConceptAttributes
from .semantic_schema import IsIntermediate, IntermediateCanonicalName, IntermediateConnects, IntermediateConfidence
from .semantic_schema import IsConnection, ConnectionSource, ConnectionTarget, ConnectionVia
from .associative_engine import NarrativeChain, NarrativeTaskType, IsNarrative
from .story_schema import IsEntity, EntityCanonicalName


def concept_to_text(concept):
    try:
        if IsConcept(concept)() is M.truth_value:
            name = ConceptCanonicalName(concept)()
            try:
                return name()
            except Exception:
                return str(name)
        if IsEntity(concept)() is M.truth_value:
            name = EntityCanonicalName(concept)()
            try:
                return name()
            except Exception:
                return str(name)
        if IsIntermediate(concept)() is M.truth_value:
            name = IntermediateCanonicalName(concept)()
            try:
                return name()
            except Exception:
                return str(name)
    except Exception:
        return "unknown_concept"
    return "concept"


def _collect_connected_names(connects_chain, acc):
    if M.IdentityCompare(connects_chain, M.EmptyList)() is M.truth_value:
        return acc
    c = M.Head(connects_chain)()
    tail = M.Tail(connects_chain)()
    name = concept_to_text(c)
    # Build python string chain via recursion, but accumulate in M chain then convert
    # For simplicity, use recursion to build list-like chain in python via nested calls
    # We will collect names via recursion returning string list
    # Instead, build via recursion that returns python list built from tail first
    rest_names = _collect_connected_names(tail, acc)
    # rest_names is python list
    return [name] + rest_names


def intermediate_to_explanation(intermediate):
    try:
        name = IntermediateCanonicalName(intermediate)()
        try:
            name_str = name()
        except Exception:
            name_str = str(name)
        connects = IntermediateConnects(intermediate)()
        connected_names = _collect_connected_names(connects, [])
        conf_str = "0.8"
        try:
            if IsIntermediate(intermediate)() is M.truth_value:
                from .semantic_schema import IntermediateConfidence as IC
                conf_char = IC(intermediate)()
                try:
                    conf_str = conf_char()
                except Exception:
                    pass
        except Exception:
            pass
        if conf_str == "0.6" or conf_str == "0.5":
            return "Possibly, " + ", ".join(connected_names) + " are linked through " + name_str + " (hypothetical, confidence " + conf_str + ")"
        else:
            return ", ".join(connected_names) + " are connected via " + name_str + " (confidence " + conf_str + ")"
    except Exception:
        return "Intermediate connection via " + concept_to_text(intermediate)


def connection_to_text(connection):
    try:
        src = ConnectionSource(connection)()
        tgt = ConnectionTarget(connection)()
        via = ConnectionVia(connection)()
        src_text = concept_to_text(src)
        tgt_text = concept_to_text(tgt)
        via_text = concept_to_text(via)
        return src_text + " -> " + via_text + " -> " + tgt_text
    except Exception:
        return "connection"


def _collect_chain_items(chain, concepts_acc, inters_acc, conns_acc):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return concepts_acc, inters_acc, conns_acc
    item = M.Head(chain)()
    tail = M.Tail(chain)()
    if IsConcept(item)() is M.truth_value or IsEntity(item)() is M.truth_value:
        concepts_acc = M.Pair(item, concepts_acc)
    elif IsIntermediate(item)() is M.truth_value:
        inters_acc = M.Pair(item, inters_acc)
    elif IsConnection(item)() is M.truth_value:
        conns_acc = M.Pair(item, conns_acc)
    return _collect_chain_items(tail, concepts_acc, inters_acc, conns_acc)


def _chain_to_python_list(chain):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return []
    head = M.Head(chain)()
    tail = M.Tail(chain)()
    rest = _chain_to_python_list(tail)
    return [head] + rest


def narrative_to_prose(narrative, discovered_paths=None, invented_intermediates=None, task_type="story"):
    if IsNarrative(narrative)() is not M.truth_value:
        return "I could not construct a coherent narrative from the given concepts."

    chain = NarrativeChain(narrative)()
    concepts_chain, inters_chain, conns_chain = _collect_chain_items(chain, M.EmptyList, M.EmptyList, M.EmptyList)

    concepts = _chain_to_python_list(concepts_chain)
    intermediates = _chain_to_python_list(inters_chain)
    connections = _chain_to_python_list(conns_chain)

    # If explicit lists passed, use those for counts
    if invented_intermediates is not None:
        intermediates_for_display = invented_intermediates
    else:
        intermediates_for_display = intermediates

    prose = ""

    if task_type == "story":
        prose += "Let me tell you a story weaving these together:\n\n"
        if concepts:
            prose += "It begins with " + concept_to_text(concepts[0]) + ". "
        for inter in intermediates_for_display:
            prose += intermediate_to_explanation(inter) + ". "
        # limit connections for readability
        limited = connections[:3] if len(connections) > 3 else connections
        for conn in limited:
            prose += connection_to_text(conn) + ". "
        if len(concepts) > 1:
            all_names = [concept_to_text(c) for c in concepts]
            prose += "\nThus, " + ", ".join(all_names[:-1]) + " and " + all_names[-1] + " are not isolated—they meet through the threads of time, place, and invention."
    elif task_type == "explanation":
        prose += "Here's how these concepts connect:\n\n"
        for inter in intermediates_for_display:
            prose += "- " + intermediate_to_explanation(inter) + "\n"
        for conn in connections:
            prose += "- " + connection_to_text(conn) + "\n"
        if not intermediates_for_display and not connections:
            prose += "No direct verified connection was found. I will not present an unverified link as fact."
    elif task_type == "connection":
        prose += "Searching for connections between your concepts:\n\n"
        if discovered_paths:
            prose += "Found " + str(len(discovered_paths)) + " existing paths in knowledge graph. "
        if intermediates_for_display:
            prose += "Invented " + str(len(intermediates_for_display)) + " intermediate concepts to bridge gaps:\n"
            for inter in intermediates_for_display:
                prose += "- " + intermediate_to_explanation(inter) + "\n"
        if connections:
            prose += "\nConnection structure:\n"
            for conn in connections:
                prose += "- " + connection_to_text(conn) + "\n"
        if not intermediates_for_display and not connections and not discovered_paths:
            prose += "No verified connection could be established. I do not present unsupported connections as facts."
    elif task_type == "exploration":
        prose += "Exploring the landscape around your concepts:\n\n"
        for inter in intermediates_for_display:
            prose += intermediate_to_explanation(inter) + ". "
        if concepts:
            prose += "\nStarting from " + ", ".join([concept_to_text(c) for c in concepts]) + ", we can traverse through these intermediate ideas."
    else:
        prose += "Task: " + task_type + "\n"
        for inter in intermediates_for_display:
            prose += intermediate_to_explanation(inter) + ". "
        for conn in connections:
            prose += connection_to_text(conn) + ". "

    # Mark hypothetical
    has_hyp = False
    for i in intermediates_for_display:
        txt = intermediate_to_explanation(i)
        if "hypothetical" in txt:
            has_hyp = True
    if has_hyp:
        prose += "\n\nNote: Some connections are hypothetical inventions (marked as such) and require further verification—they are not presented as established facts."

    return prose


def _count_chain(chain):
    if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
        return 0
    return 1 + _count_chain(M.Tail(chain)())


def explain_connection_why(connection_chain, intermediate_chain):
    explanation = "I connected them because:\n"
    inters = _chain_to_python_list(intermediate_chain)
    for inter in inters:
        explanation += "- " + intermediate_to_explanation(inter) + "\n"
    explanation += "\nThe connections were discovered via associative search over the knowledge graph, and intermediate concepts were invented where no direct path existed, then verified for temporal/spatial/domain overlap."
    return explanation


def verbalize_state(state):
    from .semantic_schema import SemanticStateGoal, SemanticStateConnections, SemanticStateIntermediates, SemanticStateFocus
    try:
        conns = SemanticStateConnections(state)()
        inters = SemanticStateIntermediates(state)()
        focus = SemanticStateFocus(state)()
        conn_count = _count_chain(conns)
        inter_count = _count_chain(inters)
        focus_text = concept_to_text(focus) if M.IdentityCompare(focus, M.EmptyList)() is M.false_value else "none"
        return "Current state: " + str(conn_count) + " connections, " + str(inter_count) + " invented intermediates, focus: " + focus_text
    except Exception as e:
        return "State: " + str(e)
