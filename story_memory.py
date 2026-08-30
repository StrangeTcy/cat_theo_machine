from . import machine as M
from . import labels as L
from .longform_schema import (
    StoryModel, StoryModelId, StoryModelGoal, StoryModelEntities, StoryModelFacts, StoryModelExplaining, StoryModelConnections, StoryModelThreads,
    StoryModelQuestions, StoryModelMotifs, StoryModelChronology, StoryModelCausal, StoryModelPosition, StoryModelPassageRefs,
    NarrativeThread, ThreadId, ThreadName, ThreadConcepts,
    UnresolvedQuestion, QuestionId, QuestionText,
    Motif, MotifName,
    ChronologyEntry, CausalLink,
    PassageRef, PassageRefChapter, PassageRefSummary,
    NarrativePlan, PlanId, PlanSegments, PlanCurrentIndex,
    Segment, SegmentId, SegmentFocus, SegmentConnections, SegmentIntent, SegmentThread, SegmentStatus,
    Chapter, ChapterIndex, ChapterTitle,
    KnowledgeStatus,
    AppendChain
)
from .semantic_schema import Concept, IsConcept, ConceptCanonicalName
from .story_schema import Entity, IsEntity, EntityCanonicalName

# Persistent story model vs prose: compact structured state

def _pair_chain(items):
    chain = M.EmptyList
    for item in reversed(items):
        chain = M.Pair(item, chain)
    return chain

class BuildInitialStoryModel(M.Edge):
    def __init__(self, model_id, goal, concepts_chain, connections_chain, threads_chain, questions_chain, motifs_chain, provenance):
        self.result = self._build(model_id, goal, concepts_chain, connections_chain, threads_chain, questions_chain, motifs_chain, provenance)
        super().__init__(inputs=_pair_chain([model_id, goal, concepts_chain, connections_chain, threads_chain, questions_chain, motifs_chain, provenance]), results=self.result)

    def _build(self, model_id, goal, concepts, connections, threads, questions, motifs, prov):
        entities = concepts
        facts = M.EmptyList
        explaining = M.EmptyList
        passage_refs = M.EmptyList
        chronology = M.EmptyList
        causal = M.EmptyList
        position = M.Char("0")
        model = StoryModel(model_id, goal, entities, facts, connections, threads, questions, explaining, passage_refs, motifs, chronology, causal, position, prov)()
        return model

    def __call__(self):
        return self.result

class UpdateStoryModelAfterPassage(M.Edge):
    def __init__(self, old_model, new_entities, new_facts, new_connections, new_passage_ref, new_chronology, new_causal, provenance):
        self.result = self._update(old_model, new_entities, new_facts, new_connections, new_passage_ref, new_chronology, new_causal, provenance)
        super().__init__(inputs=_pair_chain([old_model, new_entities, new_facts, new_connections, new_passage_ref, new_chronology, new_causal, provenance]), results=self.result)

    def _update(self, old_model, new_entities, new_facts, new_connections, new_passage_ref, new_chronology, new_causal, prov):
        # Retrieve old fields
        try:
            model_id = StoryModelId(old_model)()
            goal = M.EmptyList
            try:
                # goal extraction via chain
                from .longform_schema import StoryModel as SM
                # Actually StoryModelGoal
                from .longform_schema import StoryModel as SM2
                # Use direct accessor
                from .longform_schema import StoryModelId as SMId
                # For simplicity, reconstruct from old model parts
                # We'll extract via known positions using helpers
                from .longform_schema import StoryModel as StoryModelCls
                # Use helper edges
                # We have direct accessors for entities, connections, etc but need to reconstruct all
                # Let's extract each
                from .longform_schema import StoryModelEntities as SME, StoryModelConnections as SMC, StoryModelThreads as SMT, StoryModelQuestions as SMQ, StoryModelMotifs as SMM, StoryModelChronology as SMCh, StoryModelCausal as SMCa, StoryModelPosition as SMP, StoryModelPassageRefs as SMPR, StoryModelFacts as SMF, StoryModelExplaining as SME2
                # Actually need goal - we have accessor but not in this file? Use generic
                # For incremental, we will extract via manual Pair walking to avoid missing accessor
                # Let's use the Edge classes we have
                entities_old = SME(old_model)()
                facts_old = SMF(old_model)()
                connections_old = SMC(old_model)()
                threads_old = SMT(old_model)()
                questions_old = SMQ(old_model)()
                motifs_old = SMM(old_model)()
                chronology_old = SMCh(old_model)()
                causal_old = SMCa(old_model)()
                passage_refs_old = SMPR(old_model)()
                position_old = SMP(old_model)()
                # goal
                # Goal is second field after id: need to extract via raw Pair
                # Use StoryModelGoal accessor if available, else try manual
                try:
                    from .longform_schema import StoryModelGoal as SMG
                    goal = SMG(old_model)()
                except Exception:
                    goal = M.EmptyList
                # explaining
                explaining_old = SME2(old_model)()
            except Exception as e:
                # fallback
                model_id = M.Char("model_0")
                goal = M.EmptyList
                entities_old = M.EmptyList
                facts_old = M.EmptyList
                connections_old = M.EmptyList
                threads_old = M.EmptyList
                questions_old = M.EmptyList
                motifs_old = M.EmptyList
                chronology_old = M.EmptyList
                causal_old = M.EmptyList
                passage_refs_old = M.EmptyList
                position_old = M.Char("0")
                explaining_old = M.EmptyList

            # Merge chains
            entities_new = AppendChain(entities_old, new_entities)()
            facts_new = AppendChain(facts_old, new_facts)()
            connections_new = AppendChain(connections_old, new_connections)()
            passage_refs_new = AppendChain(passage_refs_old, M.Pair(new_passage_ref, M.EmptyList))()
            chronology_new = AppendChain(chronology_old, new_chronology)()
            causal_new = AppendChain(causal_old, new_causal)()
            # Increment position
            try:
                pos_int = int(position_old())
            except Exception:
                pos_int = 0
            new_position = M.Char(str(pos_int + 1))

            new_model = StoryModel(model_id, goal, entities_new, facts_new, connections_new, threads_old, questions_old, explaining_old, passage_refs_new, motifs_old, chronology_new, causal_new, new_position, prov)()
            return new_model
        except Exception as ex:
            return old_model

    def __call__(self):
        return self.result

class RetrieveRelevantState(M.Edge):
    def __init__(self, story_model, focus_concepts_chain):
        self.result = self._retrieve(story_model, focus_concepts_chain)
        super().__init__(inputs=M.Pair(story_model, M.Pair(focus_concepts_chain, M.EmptyList)), results=self.result)

    def _retrieve(self, model, focus):
        # General mechanism: retrieve relevant knowledge without loading whole prose
        # Returns a structure containing:
        # - entities that overlap with focus
        # - connections that involve focus
        # - recent passage refs (last 2)
        # - active threads
        # - motifs
        # This is the key to indefinite generation without context window
        try:
            entities = StoryModelEntities(model)()
            connections = StoryModelConnections(model)()
            threads = StoryModelThreads(model)()
            passage_refs = StoryModelPassageRefs(model)()
            motifs = StoryModelMotifs(model)()
            chronology = StoryModelChronology(model)()
            # Filter entities that share attribute or canonical with focus
            relevant_entities = self._filter_relevant_entities(entities, focus, M.EmptyList)
            relevant_connections = self._filter_relevant_connections(connections, focus, M.EmptyList)
            recent_passages = self._get_recent_passages(passage_refs, 2)
            # Build compact context
            # For simplicity, return Pair of relevant entities, connections, threads, recent passages, motifs
            context = M.Pair(relevant_entities, M.Pair(relevant_connections, M.Pair(threads, M.Pair(recent_passages, M.Pair(motifs, M.Pair(chronology, M.EmptyList))))))
            return context
        except Exception:
            return M.EmptyList

    def _filter_relevant_entities(self, entities_chain, focus_chain, acc):
        if M.IdentityCompare(entities_chain, M.EmptyList)() is M.truth_value:
            return acc
        ent = M.Head(entities_chain)()
        tail = M.Tail(entities_chain)()
        if self._is_relevant(ent, focus_chain):
            acc = M.Pair(ent, acc)
        return self._filter_relevant_entities(tail, focus_chain, acc)

    def _is_relevant(self, entity, focus_chain):
        if M.IdentityCompare(focus_chain, M.EmptyList)() is M.truth_value:
            return False
        focus = M.Head(focus_chain)()
        tail = M.Tail(focus_chain)()
        # Check if canonical names match or share attribute
        try:
            ent_name = M.Char("unknown")
            focus_name = M.Char("unknown")
            if IsConcept(entity)() is M.truth_value:
                ent_name = ConceptCanonicalName(entity)()
            elif IsEntity(entity)() is M.truth_value:
                ent_name = EntityCanonicalName(entity)()
            if IsConcept(focus)() is M.truth_value:
                focus_name = ConceptCanonicalName(focus)()
            elif IsEntity(focus)() is M.truth_value:
                focus_name = EntityCanonicalName(focus)()
            if M.Compare(ent_name, focus_name)() is M.truth_value:
                return True
        except Exception:
            pass
        return self._is_relevant(entity, tail)

    def _filter_relevant_connections(self, connections_chain, focus_chain, acc):
        if M.IdentityCompare(connections_chain, M.EmptyList)() is M.truth_value:
            return acc
        conn = M.Head(connections_chain)()
        tail = M.Tail(connections_chain)()
        if self._connection_involves_focus(conn, focus_chain):
            acc = M.Pair(conn, acc)
        return self._filter_relevant_connections(tail, focus_chain, acc)

    def _connection_involves_focus(self, conn, focus_chain):
        if M.IdentityCompare(focus_chain, M.EmptyList)() is M.truth_value:
            return False
        focus = M.Head(focus_chain)()
        tail = M.Tail(focus_chain)()
        try:
            from .semantic_schema import ConnectionSource, ConnectionTarget
            src = ConnectionSource(conn)()
            tgt = ConnectionTarget(conn)()
            if M.IdentityCompare(src, focus)() is M.truth_value:
                return True
            if M.IdentityCompare(tgt, focus)() is M.truth_value:
                return True
            # Also check canonical name match
            src_name = M.Char("unknown")
            tgt_name = M.Char("unknown")
            focus_name = M.Char("unknown")
            if IsConcept(src)() is M.truth_value:
                src_name = ConceptCanonicalName(src)()
            elif IsEntity(src)() is M.truth_value:
                src_name = EntityCanonicalName(src)()
            if IsConcept(tgt)() is M.truth_value:
                tgt_name = ConceptCanonicalName(tgt)()
            elif IsEntity(tgt)() is M.truth_value:
                tgt_name = EntityCanonicalName(tgt)()
            if IsConcept(focus)() is M.truth_value:
                focus_name = ConceptCanonicalName(focus)()
            elif IsEntity(focus)() is M.truth_value:
                focus_name = EntityCanonicalName(focus)()
            if M.Compare(src_name, focus_name)() is M.truth_value:
                return True
            if M.Compare(tgt_name, focus_name)() is M.truth_value:
                return True
        except Exception:
            pass
        return self._connection_involves_focus(conn, tail)

    def _get_recent_passages(self, passage_refs_chain, n):
        # Get last n passage refs
        # First count
        count = self._count_chain(passage_refs_chain)
        # Then get from count-n
        start = count - n
        if start < 0:
            start = 0
        return self._get_from_index(passage_refs_chain, start, M.EmptyList)

    def _count_chain(self, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return 0
        return 1 + self._count_chain(M.Tail(chain)())

    def _get_from_index(self, chain, start_idx, acc):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return acc
        head = M.Head(chain)()
        tail = M.Tail(chain)()
        if start_idx <= 0:
            acc = M.Pair(head, acc)
            return self._get_from_index(tail, start_idx - 1, acc)
        else:
            return self._get_from_index(tail, start_idx - 1, acc)

    def __call__(self):
        return self.result

class BuildChapterFromSegment(M.Edge):
    def __init__(self, chapter_id, index, title, segment, prose_ref, story_model_ref, provenance):
        self.result = Chapter(chapter_id, index, title, M.Pair(segment, M.EmptyList), prose_ref, story_model_ref, provenance)()
        super().__init__(inputs=_pair_chain([chapter_id, index, title, segment, prose_ref, story_model_ref, provenance]), results=self.result)
    def __call__(self):
        return self.result

class ExtractChapters(M.Edge):
    def __init__(self, chain):
        self.result = self._extract(chain, M.EmptyList)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)
    def _extract(self, remaining, acc):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return acc
        term = M.Head(remaining)()
        rest = M.Tail(remaining)()
        from .longform_schema import IsChapter
        if IsChapter(term)() is M.truth_value:
            acc = M.Pair(term, acc)
        return self._extract(rest, acc)
    def __call__(self):
        return self.result
