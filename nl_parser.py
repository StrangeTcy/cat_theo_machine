from . import machine as M
from . import labels as L
from .semantic_schema import Concept, TaskType, SemanticGoal

KNOWN_CONCEPTS = {
    "building": {"type": "architecture", "attributes": ["19th century", "Paris", "engineering", "Haussmann"], "canonical": "building"},
    "steam engine": {"type": "engineering", "attributes": ["18th century", "19th century", "industrial revolution", "Britain", "France", "engineering"], "canonical": "steam_engine"},
    "steam": {"type": "engineering", "attributes": ["18th century", "19th century", "industrial revolution", "engineering"], "canonical": "steam_engine"},
    "complex analysis": {"type": "mathematics", "attributes": ["19th century", "France", "Germany", "mathematics", "Cauchy", "Riemann"], "canonical": "complex_analysis"},
    "complex": {"type": "mathematics", "attributes": ["19th century", "mathematics"], "canonical": "complex_analysis"},
    "napoleon": {"type": "politics", "attributes": ["19th century", "Paris", "France", "Second Empire", "Haussmann", "politics"], "canonical": "napoleon_iii"},
    "napoleon iii": {"type": "politics", "attributes": ["19th century", "Paris", "France", "Second Empire", "Haussmann", "politics"], "canonical": "napoleon_iii"},
    "napoleon III": {"type": "politics", "attributes": ["19th century", "Paris", "France", "Second Empire", "Haussmann", "politics"], "canonical": "napoleon_iii"},
    "physics": {"type": "physics", "attributes": ["20th century", "quantum", "relativity", "physics"], "canonical": "physics_20th"},
    "20th-century physics": {"type": "physics", "attributes": ["20th century", "physics"], "canonical": "physics_20th"},
    "alice": {"type": "person", "attributes": ["story", "person"], "canonical": "alice"},
    "bob": {"type": "person", "attributes": ["story", "person"], "canonical": "bob"},
    "wolf": {"type": "animal", "attributes": ["story", "animal"], "canonical": "wolf"},
    "paris": {"type": "location", "attributes": ["France", "19th century", "Haussmann"], "canonical": "paris"},
    "haussmann": {"type": "person", "attributes": ["19th century", "Paris", "architecture", "Second Empire"], "canonical": "haussmann"},
    "cauchy": {"type": "mathematics", "attributes": ["19th century", "France", "complex analysis"], "canonical": "cauchy"},
    "riemann": {"type": "mathematics", "attributes": ["19th century", "Germany", "complex analysis"], "canonical": "riemann"},
    "industrial revolution": {"type": "history", "attributes": ["18th century", "19th century", "engineering", "Britain"], "canonical": "industrial_revolution"},
    "second empire": {"type": "history", "attributes": ["19th century", "Paris", "France", "Napoleon III"], "canonical": "second_empire"},
}

TASK_KEYWORDS = {
    "story": ["story", "tell me a story", "narrate", "tale"],
    "connection": ["connect", "connection", "link", "relate", "relationship"],
    "explanation": ["explain", "why", "how", "what is"],
    "comparison": ["compare", "comparison", "difference", "similar"],
    "exploration": ["explore", "discover", "find", "search"],
    "transformation": ["transform", "change", "from perspective", "perspective"],
    "continuation": ["continue", "continue from", "more"],
    "refinement": ["forget", "remove", "instead", "stranger", "weirder", "different"],
}

# Stoplist for generic capitalized words that should not become entities
STOP_WORDS = {
    "tell", "connect", "history", "advances", "biography", "building", "steam", "engine",
    "complex", "analysis", "napoleon", "iii", "ii", "the", "and", "or", "about", "this",
    "that", "these", "those", "with", "from", "into", "to", "of", "a", "an", "in", "on",
    "why", "how", "what", "find", "stranger", "continue", "forget", "same", "perspective",
    "20th-century", "20th", "century", "physics", "story", "via", "engineering",
}

def _build_attr_chain(attr_list):
    chain = M.EmptyList
    for attr in reversed(attr_list):
        chain = M.Pair(M.Char(attr), chain)
    return chain

def extract_entities(utterance):
    lower = utterance.lower()
    found = []
    sorted_concepts = sorted(KNOWN_CONCEPTS.keys(), key=lambda x: len(x), reverse=True)
    matched_canonical = set()
    matched_spans = []
    for phrase in sorted_concepts:
        phrase_lower = phrase.lower()
        idx = lower.find(phrase_lower)
        if idx != -1:
            canon = KNOWN_CONCEPTS[phrase]["canonical"]
            if canon not in matched_canonical:
                # Check overlap with already matched longer phrases
                overlapping = False
                for (s, e) in matched_spans:
                    if not (idx + len(phrase_lower) <= s or idx >= e):
                        # overlap, but if canonical already matched, skip
                        pass
                found.append((phrase, KNOWN_CONCEPTS[phrase]))
                matched_canonical.add(canon)
                matched_spans.append((idx, idx + len(phrase_lower)))
    # Extract capitalized words as potential new entities only if not in stoplist and not part of already matched span
    # Require at least 4 chars and not common verb
    words = utterance.split()
    for w in words:
        stripped = w.strip(",.!?;:()\"'")
        if len(stripped) < 4:
            continue
        if stripped.lower() in STOP_WORDS:
            continue
        if not stripped[0].isupper():
            continue
        if stripped.lower() in [k.lower() for k in KNOWN_CONCEPTS]:
            continue
        if stripped.lower() in matched_canonical:
            continue
        # Check if this word is inside an already matched phrase
        # Find its position roughly
        # For simplicity, skip if its lower appears inside any matched phrase's lower
        is_inside = False
        for (phrase, _) in found:
            if stripped.lower() in phrase.lower():
                is_inside = True
                break
        if is_inside:
            continue
        found.append((stripped, {"type": "unknown", "attributes": [], "canonical": stripped.lower()}))
        matched_canonical.add(stripped.lower())
    return found

def determine_task_type(utterance):
    lower = utterance.lower()
    scores = {k: 0 for k in TASK_KEYWORDS}
    for task, keywords in TASK_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[task] += 1
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "exploration"
    return best

def parse_utterance_to_goal(utterance, goal_counter=0):
    entities = extract_entities(utterance)
    task_type_str = determine_task_type(utterance)
    concept_chain = M.EmptyList
    for phrase, info in reversed(entities):
        concept_id = M.Char(info["canonical"] + "_" + str(goal_counter))
        canonical = M.Char(info["canonical"])
        c_type = M.Char(info["type"])
        attr_chain = _build_attr_chain(info["attributes"])
        provenance = M.Char("nl_parser")
        concept = Concept(concept_id, canonical, c_type, attr_chain, provenance)()
        concept_chain = M.Pair(concept, concept_chain)
    task_type = TaskType(M.Char(task_type_str))()
    goal_id = M.Char("goal_" + str(goal_counter))
    raw = M.Char(utterance[:200])
    prov = M.Char("nl_parser")
    goal = SemanticGoal(goal_id, task_type, concept_chain, raw, prov)()
    return {
        "goal_term": goal,
        "task_type": task_type_str,
        "entities": entities,
        "concept_chain": concept_chain,
        "utterance": utterance,
    }

def parse_followup(utterance, current_state):
    lower = utterance.lower()
    if "why did you connect" in lower or "why did you" in lower:
        return {"type": "why", "focus": "explanation"}
    if "stranger" in lower or "weirder" in lower or "different connection" in lower:
        return {"type": "refinement", "intent": "stranger"}
    if "continue from" in lower:
        parts = lower.split("continue from")
        focus = parts[1].strip() if len(parts) > 1 else "engineering"
        return {"type": "continuation", "focus": focus}
    if "perspective" in lower:
        if "building" in lower:
            return {"type": "transformation", "perspective": "building"}
        return {"type": "transformation", "perspective": "unknown"}
    if "forget" in lower:
        to_forget = []
        to_add = []
        if "napoleon" in lower:
            to_forget.append("napoleon_iii")
        if "physics" in lower:
            to_add.append("physics_20th")
        return {"type": "refinement", "forget": to_forget, "add": to_add}
    return {"type": "new", "parsed": parse_utterance_to_goal(utterance)}
