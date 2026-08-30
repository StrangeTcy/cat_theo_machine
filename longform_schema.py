from . import machine as M
from . import labels as L

# Long-form narrative schema: persistent story model vs prose
# All pair-only Edge subclasses, recursion-based, substrate compliant

def _pair_chain(items):
    # items is python list of M terms, build nested Pair chain ending with EmptyList
    # General helper, not part of substrate, used at construction time (I/O boundary)
    chain = M.EmptyList
    for item in reversed(items):
        chain = M.Pair(item, chain)
    return chain

class StoryModel(M.Edge):
    def __init__(self, model_id, goal, entities_chain, facts_chain, connections_chain, threads_chain, questions_chain, explaining_chain, passage_refs_chain, motifs_chain, chronology_chain, causal_chain, position, provenance):
        inner = _pair_chain([model_id, goal, entities_chain, facts_chain, connections_chain, threads_chain, questions_chain, explaining_chain, passage_refs_chain, motifs_chain, chronology_chain, causal_chain, position, provenance])
        self.result = M.Pair(L.StoryModelLabel, inner)
        super().__init__(inputs=_pair_chain([model_id, goal, entities_chain, facts_chain, connections_chain, threads_chain, questions_chain, explaining_chain, passage_refs_chain, motifs_chain, chronology_chain, causal_chain, position, provenance]), results=self.result)
    def __call__(self):
        return self.result

class IsStoryModel(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.StoryModelLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelId(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(model)())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelGoal(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(model)())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelEntities(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(model)())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelFacts(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelConnections(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelThreads(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelQuestions(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelExplaining(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelPassageRefs(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())())())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelMotifs(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())())())())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelChronology(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())())())())())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelCausal(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())())())())())())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class StoryModelPosition(M.Edge):
    def __init__(self, model):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(model)())())())())())())())())())())())())())()
        super().__init__(inputs=M.Pair(model, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class NarrativeThread(M.Edge):
    def __init__(self, thread_id, name, concepts_chain, status, provenance):
        inner = _pair_chain([thread_id, name, concepts_chain, status, provenance])
        self.result = M.Pair(L.NarrativeThreadLabel, inner)
        super().__init__(inputs=_pair_chain([thread_id, name, concepts_chain, status, provenance]), results=self.result)
    def __call__(self):
        return self.result

class IsNarrativeThread(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.NarrativeThreadLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ThreadId(M.Edge):
    def __init__(self, thread):
        self.result = M.Head(M.Tail(thread)())()
        super().__init__(inputs=M.Pair(thread, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ThreadName(M.Edge):
    def __init__(self, thread):
        self.result = M.Head(M.Tail(M.Tail(thread)())())()
        super().__init__(inputs=M.Pair(thread, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ThreadConcepts(M.Edge):
    def __init__(self, thread):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(thread)())())())()
        super().__init__(inputs=M.Pair(thread, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class UnresolvedQuestion(M.Edge):
    def __init__(self, q_id, question_text, related_concepts, provenance):
        inner = _pair_chain([q_id, question_text, related_concepts, provenance])
        self.result = M.Pair(L.UnresolvedQuestionLabel, inner)
        super().__init__(inputs=_pair_chain([q_id, question_text, related_concepts, provenance]), results=self.result)
    def __call__(self):
        return self.result

class IsUnresolvedQuestion(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.UnresolvedQuestionLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class QuestionId(M.Edge):
    def __init__(self, q):
        self.result = M.Head(M.Tail(q)())()
        super().__init__(inputs=M.Pair(q, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class QuestionText(M.Edge):
    def __init__(self, q):
        self.result = M.Head(M.Tail(M.Tail(q)())())()
        super().__init__(inputs=M.Pair(q, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class Motif(M.Edge):
    def __init__(self, motif_id, name, occurrences_chain, provenance):
        inner = _pair_chain([motif_id, name, occurrences_chain, provenance])
        self.result = M.Pair(L.MotifLabel, inner)
        super().__init__(inputs=_pair_chain([motif_id, name, occurrences_chain, provenance]), results=self.result)
    def __call__(self):
        return self.result

class IsMotif(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.MotifLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class MotifName(M.Edge):
    def __init__(self, motif):
        self.result = M.Head(M.Tail(M.Tail(motif)())())()
        super().__init__(inputs=M.Pair(motif, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ChronologyEntry(M.Edge):
    def __init__(self, entry_id, event, time_atom, provenance):
        inner = _pair_chain([entry_id, event, time_atom, provenance])
        self.result = M.Pair(L.ChronologyEntryLabel, inner)
        super().__init__(inputs=_pair_chain([entry_id, event, time_atom, provenance]), results=self.result)
    def __call__(self):
        return self.result

class IsChronologyEntry(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.ChronologyEntryLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class CausalLink(M.Edge):
    def __init__(self, link_id, cause, effect, provenance):
        inner = _pair_chain([link_id, cause, effect, provenance])
        self.result = M.Pair(L.CausalLinkLabel, inner)
        super().__init__(inputs=_pair_chain([link_id, cause, effect, provenance]), results=self.result)
    def __call__(self):
        return self.result

class IsCausalLink(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.CausalLinkLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class PassageRef(M.Edge):
    def __init__(self, ref_id, chapter_index, summary, concepts_chain, provenance):
        inner = _pair_chain([ref_id, chapter_index, summary, concepts_chain, provenance])
        self.result = M.Pair(L.PassageRefLabel, inner)
        super().__init__(inputs=_pair_chain([ref_id, chapter_index, summary, concepts_chain, provenance]), results=self.result)
    def __call__(self):
        return self.result

class IsPassageRef(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.PassageRefLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class PassageRefChapter(M.Edge):
    def __init__(self, ref):
        self.result = M.Head(M.Tail(M.Tail(ref)())())()
        super().__init__(inputs=M.Pair(ref, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class PassageRefSummary(M.Edge):
    def __init__(self, ref):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(ref)())())())()
        super().__init__(inputs=M.Pair(ref, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class NarrativePlan(M.Edge):
    def __init__(self, plan_id, goal, segments_chain, current_index, provenance):
        inner = _pair_chain([plan_id, goal, segments_chain, current_index, provenance])
        self.result = M.Pair(L.NarrativePlanLabel, inner)
        super().__init__(inputs=_pair_chain([plan_id, goal, segments_chain, current_index, provenance]), results=self.result)
    def __call__(self):
        return self.result

class IsNarrativePlan(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.NarrativePlanLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class PlanId(M.Edge):
    def __init__(self, plan):
        self.result = M.Head(M.Tail(plan)())()
        super().__init__(inputs=M.Pair(plan, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class PlanSegments(M.Edge):
    def __init__(self, plan):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(plan)())())())()
        super().__init__(inputs=M.Pair(plan, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class PlanCurrentIndex(M.Edge):
    def __init__(self, plan):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())()
        super().__init__(inputs=M.Pair(plan, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class Segment(M.Edge):
    def __init__(self, seg_id, focus_concepts, connections_chain, intent, thread_ref, provenance, status):
        inner = _pair_chain([seg_id, focus_concepts, connections_chain, intent, thread_ref, provenance, status])
        self.result = M.Pair(L.SegmentLabel, inner)
        super().__init__(inputs=_pair_chain([seg_id, focus_concepts, connections_chain, intent, thread_ref, provenance, status]), results=self.result)
    def __call__(self):
        return self.result

class IsSegment(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.SegmentLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SegmentId(M.Edge):
    def __init__(self, seg):
        self.result = M.Head(M.Tail(seg)())()
        super().__init__(inputs=M.Pair(seg, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SegmentFocus(M.Edge):
    def __init__(self, seg):
        self.result = M.Head(M.Tail(M.Tail(seg)())())()
        super().__init__(inputs=M.Pair(seg, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SegmentConnections(M.Edge):
    def __init__(self, seg):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(seg)())())())()
        super().__init__(inputs=M.Pair(seg, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SegmentIntent(M.Edge):
    def __init__(self, seg):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(seg)())())())())()
        super().__init__(inputs=M.Pair(seg, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SegmentThread(M.Edge):
    def __init__(self, seg):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(seg)())())())())())()
        super().__init__(inputs=M.Pair(seg, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SegmentProvenance(M.Edge):
    def __init__(self, seg):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(seg)())())())())())())()
        super().__init__(inputs=M.Pair(seg, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class SegmentStatus(M.Edge):
    def __init__(self, seg):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(seg)())())())())())())())()
        super().__init__(inputs=M.Pair(seg, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class Chapter(M.Edge):
    def __init__(self, chapter_id, index, title, segments_chain, prose_ref, story_model_ref, provenance):
        inner = _pair_chain([chapter_id, index, title, segments_chain, prose_ref, story_model_ref, provenance])
        self.result = M.Pair(L.ChapterLabel, inner)
        super().__init__(inputs=_pair_chain([chapter_id, index, title, segments_chain, prose_ref, story_model_ref, provenance]), results=self.result)
    def __call__(self):
        return self.result

class IsChapter(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.ChapterLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ChapterIndex(M.Edge):
    def __init__(self, chapter):
        self.result = M.Head(M.Tail(M.Tail(chapter)())())()
        super().__init__(inputs=M.Pair(chapter, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class ChapterTitle(M.Edge):
    def __init__(self, chapter):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(chapter)())())())()
        super().__init__(inputs=M.Pair(chapter, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class KnowledgeStatus(M.Edge):
    def __init__(self, status_name):
        self.result = M.Pair(L.KnowledgeStatusLabel, M.Pair(status_name, M.EmptyList))
        super().__init__(inputs=M.Pair(status_name, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

class IsKnowledgeStatus(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.KnowledgeStatusLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)
    def __call__(self):
        return self.result

# Helpers for chain operations (Edge-based)

class AppendChain(M.Edge):
    def __init__(self, a_chain, b_chain):
        self.result = self._append(a_chain, b_chain)
        super().__init__(inputs=M.Pair(a_chain, M.Pair(b_chain, M.EmptyList)), results=self.result)
    def _append(self, a, b):
        if M.IdentityCompare(a, M.EmptyList)() is M.truth_value:
            return b
        head = M.Head(a)()
        tail = M.Tail(a)()
        rest = self._append(tail, b)
        return M.Pair(head, rest)
    def __call__(self):
        return self.result

class CountChain(M.Edge):
    def __init__(self, chain):
        self.result = self._count(chain, 0)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)
    def _count(self, chain, acc):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return acc
        return self._count(M.Tail(chain)(), acc + 1)
    def __call__(self):
        return self.result

class ExtractThreads(M.Edge):
    def __init__(self, chain):
        self.result = self._extract(chain, M.EmptyList)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)
    def _extract(self, remaining, acc):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return acc
        term = M.Head(remaining)()
        rest = M.Tail(remaining)()
        if IsNarrativeThread(term)() is M.truth_value:
            acc = M.Pair(term, acc)
        return self._extract(rest, acc)
    def __call__(self):
        return self.result

class ExtractSegments(M.Edge):
    def __init__(self, chain):
        self.result = self._extract(chain, M.EmptyList)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)
    def _extract(self, remaining, acc):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return acc
        term = M.Head(remaining)()
        rest = M.Tail(remaining)()
        if IsSegment(term)() is M.truth_value:
            acc = M.Pair(term, acc)
        return self._extract(rest, acc)
    def __call__(self):
        return self.result

class ExtractQuestions(M.Edge):
    def __init__(self, chain):
        self.result = self._extract(chain, M.EmptyList)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)
    def _extract(self, remaining, acc):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return acc
        term = M.Head(remaining)()
        rest = M.Tail(remaining)()
        if IsUnresolvedQuestion(term)() is M.truth_value:
            acc = M.Pair(term, acc)
        return self._extract(rest, acc)
    def __call__(self):
        return self.result
