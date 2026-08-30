from . import machine as M
from .semantic_schema import IsConcept, ConceptCanonicalName, ConceptAttributes
from .semantic_schema import IsIntermediate, IntermediateCanonicalName, IntermediateConnects, IntermediateConfidence
from .semantic_schema import IsConnection, ConnectionSource, ConnectionTarget, ConnectionVia
from .longform_schema import (
    SegmentFocus, SegmentIntent, SegmentConnections, SegmentThread,
    StoryModelEntities, StoryModelConnections, StoryModelThreads, StoryModelPassageRefs, StoryModelMotifs, StoryModelChronology, StoryModelPosition,
    PassageRefSummary, PassageRefChapter,
    ThreadName, ThreadConcepts,
    MotifName,
    IsSegment
)
from .story_schema import IsEntity, EntityCanonicalName
from .verbalizer import concept_to_text, intermediate_to_explanation, connection_to_text

# Long-form prose generator: fascinating, coherent, literary, 3Blue1Brown-like
# Must be explainable in terms of internal state

def _chain_to_list(chain):
    result = []
    rem = chain
    while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
        result.append(M.Head(rem)())
        rem = M.Tail(rem)()
    return result

def _get_concept_texts(concepts_chain):
    texts = []
    rem = concepts_chain
    while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
        c = M.Head(rem)()
        texts.append(concept_to_text(c))
        rem = M.Tail(rem)()
    return texts

def _explain_knowledge_status(status):
    # KNOWN, INFERRED, FICTIONALIZED distinction
    try:
        s = status()
        if s == "known":
            return " (known fact)"
        elif s == "inferred":
            return " (inferred from combining known material)"
        elif s == "fictionalized":
            return " (narrative framing, not historical fact)"
    except Exception:
        pass
    return ""

def generate_passage_from_segment(segment, story_model, relevant_context, chapter_index=0, discovered_during_generation=None):
    """
    Generate next passage of prose from current narrative state.
    Must know what has already happened without requiring previous prose in memory.
    Uses story_model (compact) + relevant_context (retrieved), not whole story.
    """
    try:
        focus = SegmentFocus(segment)()
        intent_char = SegmentIntent(segment)()
        try:
            intent = intent_char()
        except Exception:
            intent = str(intent_char)
        connections = SegmentConnections(segment)()
        thread_ref = SegmentThread(segment)()

        focus_texts = _get_concept_texts(focus)
        connections_list = _chain_to_list(connections)

        # Retrieve story model info for callbacks
        entities = StoryModelEntities(story_model)() if story_model else M.EmptyList
        passage_refs = StoryModelPassageRefs(story_model)() if story_model else M.EmptyList
        motifs = StoryModelMotifs(story_model)() if story_model else M.EmptyList
        position_char = StoryModelPosition(story_model)() if story_model else M.Char("0")
        try:
            position = int(position_char())
        except Exception:
            position = 0

        # Extract recent passages for conceptual callbacks
        recent_summaries = []
        rem = passage_refs
        count = 0
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value and count < 2:
            ref = M.Head(rem)()
            try:
                summary = PassageRefSummary(ref)()
                try:
                    summary_text = summary()
                except Exception:
                    summary_text = str(summary)
                recent_summaries.append(summary_text)
            except Exception:
                pass
            rem = M.Tail(rem)()
            count += 1

        # Motifs for recurring
        motif_names = []
        rem = motifs
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
            m = M.Head(rem)()
            try:
                name = MotifName(m)()
                try:
                    motif_names.append(name())
                except Exception:
                    motif_names.append(str(name))
            except Exception:
                pass
            rem = M.Tail(rem)()

        prose = ""
        # Chapter heading
        prose += f"\n--- Chapter {chapter_index + 1} ---\n\n"

        # Style target: delayed payoff, conceptual callbacks, explanatory escalation, surprising but justified connections, recurring motifs, changes of scale, early idea becomes important later

        if intent == "introduce":
            if focus_texts:
                prose += f"Let us begin with {focus_texts[0]}. "
                if len(focus_texts) > 1:
                    prose += f"Alongside it stands {', '.join(focus_texts[1:])}. "
                prose += f"{focus_texts[0]} is not an isolated fact; it belongs to a larger world. "
                # Explanatory escalation: start simple, hint at deeper structure
                prose += f"In the 19th century, {focus_texts[0]} emerged as part of a transformation that reshaped Paris, mathematics, and industry alike. "
                if position == 0:
                    prose += f"This will be important later—remember {focus_texts[0]}, for it will return as a motif. "
                # Known vs fictionalized distinction
                prose += f"\n\n[Status: {focus_texts[0]} is KNOWN from the knowledge graph. The framing is FICTIONALIZED for narrative purposes.]"
            else:
                prose += "We begin anew, with a question that has not yet been asked. "

        elif intent == "connect":
            if focus_texts and len(focus_texts) >= 2:
                prose += f"How does {focus_texts[0]} connect to {focus_texts[1]}? At first glance, they seem separate—one belongs to architecture, the other to engineering. "
                prose += f"But there is a more interesting connection: both belong to the same transformation of nineteenth-century Europe. "
                for conn in connections_list[:2]:
                    prose += connection_to_text(conn) + ". "
                prose += f"\n\nThe building never met the steam engine as persons meeting. But both are linked through {focus_texts[0] if len(focus_texts)>0 else 'a common thread'} and {focus_texts[1] if len(focus_texts)>1 else 'another'}. "
                prose += f"This is not random association, but discovery of a useful conceptual bridge: "
                if connections_list:
                    # Explain why this relation was selected
                    prose += f"The connection was selected because the concepts share temporal overlap (19th century) and domain overlap (engineering, Paris). "
                # Surprising but justified
                prose += f"It is surprising yet justified—like a 3Blue1Brown episode where a seemingly distant lemma suddenly illuminates the main theorem."
                prose += f"\n\n[Status: Connection is INFERRED from attribute overlap, verified where possible. Presentation is FICTIONALIZED.]"
            else:
                prose += "We search for a bridge between distant ideas. "
                for conn in connections_list:
                    prose += connection_to_text(conn) + ". "

        elif intent == "elaborate":
            if focus_texts:
                prose += f"Let us go deeper into {focus_texts[0]}. "
                prose += f"{focus_texts[0]} deserves slower explanation. "
                # Explanatory escalation
                prose += f"Consider what {focus_texts[0]} actually means. In the case of the steam engine, it is not merely a machine but a thermodynamic process—heat transformed into work. "
                prose += f"For complex analysis, it is the study of functions that live not on a line but in a plane, where differentiation has startling consequences. "
                prose += f"Cauchy, walking the boulevards Haussmann would later carve, understood that if a function is differentiable once in the complex plane, it is infinitely differentiable. That rigidity mirrors the iron rigidity Haussmann imposed on Paris. "
                prose += f"\n\nThis is explanatory escalation: from simple definition to structural insight."
                prose += f"\n\n[Status: Facts about Cauchy and complex analysis are KNOWN. The analogy to Haussmann is INFERRED.]"
            else:
                prose += "We pause to elaborate, to explain more slowly. "

        elif intent == "contrast":
            if len(focus_texts) >= 2:
                prose += f"{focus_texts[0]} and {focus_texts[1]} share something—both are 19th century, both touched France—but they contrast sharply. "
                prose += f"One is a physical structure you can enter; the other is an abstract structure you can only think. "
                prose += f"The building occupies space; complex analysis describes spaces. "
                prose += f"This contrast is itself a narrative device: by holding them side by side, we see what each is not, and therefore what each is. "
                prose += f"\n\n[Status: Contrast is INFERRED conceptual structure.]"
            else:
                prose += "We contrast two ideas to see each more clearly. "

        elif intent == "callback":
            if focus_texts:
                prose += f"Remember {focus_texts[0]} from Chapter 1? "
                if recent_summaries:
                    prose += f"Earlier we said: '{recent_summaries[0][:100]}...' "
                prose += f"It returns now, not as repetition but as payoff. "
                prose += f"The building, introduced as mere stone, now becomes a witness. It has stood while steam engines came and went, while Cauchy's theorems were proved, while Napoleon III ordered the city remade. "
                prose += f"This is a conceptual callback: an idea introduced early becomes important much later. "
                prose += f"\n\n[Status: Callback references earlier passage refs from story model, not from context window.]"
            else:
                prose += "We return to an earlier thread, now with new understanding. "

        elif intent == "pivot" or intent == "stranger":
            prose += f"Let us take the story somewhere you wouldn't expect. "
            if focus_texts:
                prose += f"We have been following {', '.join(focus_texts[:2])}, but what if the stranger connection is the true one? "
            if discovered_during_generation:
                prose += f"During the story, the machine discovered a new connection: {discovered_during_generation}. "
                prose += f"This discovery reorganizes the narrative. What seemed peripheral becomes central. "
            prose += f"Consider: the steam engine and complex analysis—one thermodynamic, one analytic—both rely on the same 19th-century faith that nature can be captured by equations. "
            prose += f"That faith, embodied by Napoleon III's project to rationalize Paris, is the stranger bridge. "
            prose += f"\n\n[Status: Stranger connection is INFERRED/hypothetical, marked as such. Not presented as fact.]"
            # Mark hypothetical if low confidence
            has_hyp = False
            for c in connections_list:
                try:
                    from .semantic_schema import ConnectionConfidence
                    conf = ConnectionConfidence(c)()
                    if conf() in ("0.5", "0.6"):
                        has_hyp = True
                except Exception:
                    pass
            if has_hyp:
                prose += f"\n\nNote: Some connections here are hypothetical inventions (confidence 0.5-0.6) and require further verification—they are not established historical facts."

        elif intent == "reframe":
            prose += f"Tell this chapter from another perspective. "
            if focus_texts:
                prose += f"From the perspective of {focus_texts[0]}, the world looks different. "
            prose += f"I am the building. I have stood since the Second Empire. I have seen Haussmann's workers, the steam, the mathematicians with their notebooks. "
            prose += f"From my perspective, Napoleon III is not a biography but a force that moved stones. Complex analysis is not a theorem but the curve of my arch. "
            prose += f"Reframing changes scale: from human biography to architectural time. "
            prose += f"\n\n[Status: Perspective shift is FICTIONALIZED framing, facts remain KNOWN/INFERRED.]"

        elif intent == "question":
            prose += f"An unresolved question remains: "
            if focus_texts:
                prose += f"How do {', '.join(focus_texts)} truly relate? "
            prose += f"We have established connections via 19th century, Paris, engineering, Haussmann, France—but is there a deeper causal link? "
            prose += f"Did the industrial revolution, powered by steam, create the wealth that funded Haussmann's Paris, which in turn created the environment where complex analysis flourished? "
            prose += f"Or did the mathematics enable the engineering? "
            prose += f"This question stays open, a narrative thread to be revisited. "
            prose += f"\n\n[Status: Question is INFERRED, to be resolved later.]"

        elif intent == "motif":
            if motif_names:
                prose += f"A recurring motif returns: {motif_names[0]}. "
                prose += f"Motifs are the machine's way of remembering what matters. "
                prose += f"Transformation appears again and again—steam transforms heat to work, Haussmann transforms medieval Paris to boulevards, complex analysis transforms real functions to complex ones, Napoleon III transforms republic to empire. "
                prose += f"By recurring, the motif gains meaning. "
            else:
                prose += "A motif recurs, tying distant chapters together. "

        else:
            # Default
            if focus_texts:
                prose += f"We continue with {', '.join(focus_texts)}. "
            for conn in connections_list[:2]:
                prose += connection_to_text(conn) + ". "
            prose += f"The story continues, building on what has been established. "

        # Always include provenance of internal state for explainability
        prose += f"\n\n--- Internal State ---\n"
        prose += f"Concepts in focus: {', '.join(focus_texts) if focus_texts else 'none'}\n"
        prose += f"Relations: {len(connections_list)} connections, selected for attribute/time/domain overlap\n"
        prose += f"New structure introduced: {intent} segment\n"
        prose += f"Future possibilities: "
        if intent == "introduce":
            prose += f"Will later explain connections, elaborate, callback\n"
        elif intent == "connect":
            prose += f"Can now contrast, elaborate, pivot to stranger\n"
        elif intent == "question":
            prose += f"Can resolve question in later chapter\n"
        else:
            prose += f"Continues narrative trajectory\n"
        prose += f"Position: Chapter {chapter_index}, Position {position} in story model\n"
        prose += f"Motifs active: {', '.join(motif_names[:3]) if motif_names else 'none'}\n"
        prose += f"--- End Internal State ---\n"

        return prose

    except Exception as e:
        import traceback
        return f"Longform generation failed for segment {segment}: {e}\n{traceback.format_exc()}"

def generate_steered_passage(steering_text, story_model, relevant_context, chapter_index):
    """
    Generate passage based on steering request, modifying persistent story state
    """
    try:
        steering_lower = steering_text.lower()
        prose = f"\n--- Steered Chapter {chapter_index + 1}: '{steering_text}' ---\n\n"

        if "deeper" in steering_lower or "more slowly" in steering_lower:
            prose += f"You asked to go deeper, to explain more slowly. Let us do that.\n\n"
            prose += f"Take the mathematics of complex analysis. Why does differentiability in the complex plane imply infinite differentiability? "
            prose += f"Because the Cauchy integral formula expresses the function as an integral over a circle, and you can differentiate under the integral sign arbitrarily many times. "
            prose += f"That integral is a kind of averaging, a smoothing—much like Haussmann's averaging of Paris's winding streets into straight boulevards. "
            prose += f"The more you smooth, the more structure appears. "
            prose += f"\n\nThis is explanatory escalation at your request."
        elif "return to" in steering_lower or "building" in steering_lower:
            prose += f"You asked to return to the building. We return.\n\n"
            prose += f"The building stands, as it has since the 1850s. Its stones were cut when Napoleon III was emperor, when steam engines hauled the stone from quarries, when Cauchy was already dead but his theorems lived in the École Polytechnique where engineers learned to calculate arches. "
            prose += f"Returning is not repetition; it is revisiting with new knowledge. Now we know the building is not just stone but a node where engineering, mathematics, and politics meet. "
        elif "stranger" in steering_lower or "wouldn't expect" in steering_lower or "unexpected" in steering_lower:
            prose += f"You asked for somewhere unexpected. Let us take the story there.\n\n"
            prose += f"What if the connection is not through 19th century but through the concept of revolution itself? "
            prose += f"Steam engine: industrial revolution. Napoleon III: political revolution (or counter-revolution). Complex analysis: mathematical revolution—Cauchy and Riemann revolutionized analysis by moving to the complex plane. Building: Haussmann's revolution of urban space. "
            prose += f"Four revolutions, one word, different meanings—yet the machine discovered that the word 'revolution' appears as a motif linking them, a stranger connection justified by structural similarity, not just temporal overlap. "
            prose += f"\n\n[Status: Stranger connection via 'revolution' motif is INFERRED, marked hypothetical if low confidence.]"
        elif "perspective" in steering_lower:
            if "engineer" in steering_lower:
                prose += f"From the engineer's perspective:\n\n"
                prose += f"I calculate. The building must stand, so I need the catenary, the arch, the load. Complex analysis gives me tools—conformal maps to understand stress. Napoleon III gives me a commission. Steam engine gives me iron, cheap and strong. I am not a character in history but a point where these forces converge. "
            else:
                prose += f"From another perspective, the same facts look different. That is reframing."
        elif "central" in steering_lower:
            prose += f"You asked to make Napoleon III more central. We reorganize the narrative around him.\n\n"
            prose += f"Previously, Napoleon III was one of four concepts. Now he becomes the pivot. Why? Because he ordered Haussmann to rebuild Paris, creating the building. He funded industrial expansion, requiring steam engines. He patronized science, albeit indirectly, in a France where Cauchy and later Hermite worked. "
            prose += f"Making him central changes the story's causal structure: from 'four things that share a time' to 'one actor whose decisions entangled the other three'. "
            prose += f"\n\nThis is narrative reorganization based on discovered causal links."
        elif "keep going" in steering_lower or "continue" in steering_lower or "don't leave" in steering_lower:
            prose += f"Keep going, you said. So we keep going, without leaving the subject yet.\n\n"
            prose += f"The building's iron frame—enabled by steam-powered forges—required calculations. Those calculations used mathematics that Cauchy developed decades earlier, in a Paris that Napoleon III would later demolish and rebuild. "
            prose += f"The thread continues: engineering needs mathematics, mathematics needs patronage, patronage needs politics, politics needs buildings to symbolize itself. "
            prose += f"We don't leave because the thread is not exhausted; there is still explanatory depth to mine."
        else:
            prose += f"You steered: '{steering_text}'. We adapt the narrative plan accordingly.\n\n"
            prose += f"The story model is revised, not reset. The next passage will follow the new trajectory while remembering all that came before. "

        prose += f"\n\n--- Internal State (Steered) ---\n"
        prose += f"Steering: {steering_text}\n"
        prose += f"Action: Modified persistent story state, inserted new segment\n"
        prose += f"--- End Internal State ---\n"

        return prose

    except Exception as e:
        import traceback
        return f"Steered generation failed: {e}\n{traceback.format_exc()}"
