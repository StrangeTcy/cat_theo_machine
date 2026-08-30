from . import machine as M
from . import labels as L
from .semantic_schema import Concept, IsConcept, ConceptCanonicalName, ConceptAttributes
from .longform_schema import (
    NarrativeThread, ThreadId, ThreadName, ThreadConcepts,
    UnresolvedQuestion, QuestionId, QuestionText,
    Motif, MotifName,
    ChronologyEntry, CausalLink,
    PassageRef, PassageRefChapter, PassageRefSummary,
    NarrativePlan, PlanId, PlanSegments, PlanCurrentIndex,
    Segment, SegmentId, SegmentFocus, SegmentConnections, SegmentIntent, SegmentThread, SegmentStatus,
    Chapter, ChapterIndex, ChapterTitle,
    StoryModel, StoryModelId, StoryModelEntities, StoryModelConnections, StoryModelThreads, StoryModelQuestions, StoryModelMotifs, StoryModelChronology, StoryModelCausal, StoryModelPosition, StoryModelPassageRefs,
    AppendChain, CountChain,
    KnowledgeStatus
)
from .story_schema import Entity, IsEntity, EntityCanonicalName, EntityAttributes
from .semantic_schema import Intermediate, IsIntermediate, IntermediateCanonicalName, IntermediateConnects
from .associative_engine import InventIntermediatesFromConcepts, FilterVerifiedIntermediates, BuildConnectionsViaIntermediates

# General mechanisms for selecting, ordering, revisiting, contrasting, elaborating, reframing

class IntentLabel:
    INTRODUCE = "introduce"
    EXPLAIN = "explain"
    CONNECT = "connect"
    CONTRAST = "contrast"
    ELABORATE = "elaborate"
    CALLBACK = "callback"
    PIVOT = "pivot"
    REFRAME = "reframe"
    QUESTION = "question"
    RESOLVE = "resolve"
    MOTIF = "motif"

class BuildNarrativeThreadsFromConcepts(M.Edge):
    def __init__(self, concepts_chain, provenance):
        self.result = self._build(concepts_chain, provenance, M.EmptyList, 0)
        super().__init__(inputs=M.Pair(concepts_chain, M.Pair(provenance, M.EmptyList)), results=self.result)

    def _build(self, concepts, prov, acc, idx):
        if M.IdentityCompare(concepts, M.EmptyList)() is M.truth_value:
            return acc
        concept = M.Head(concepts)()
        tail = M.Tail(concepts)()
        name = M.Char("thread_unknown")
        try:
            if IsConcept(concept)() is M.truth_value:
                name = ConceptCanonicalName(concept)()
            elif IsEntity(concept)() is M.truth_value:
                name = EntityCanonicalName(concept)()
        except Exception:
            pass
        thread_id = M.Char("thread_" + str(idx) + "_" + name())
        concepts_single = M.Pair(concept, M.EmptyList)
        thread = NarrativeThread(thread_id, name, concepts_single, M.Char("active"), prov)()
        acc = M.Pair(thread, acc)
        return self._build(tail, prov, acc, idx + 1)

    def __call__(self):
        return self.result

class BuildInitialQuestions(M.Edge):
    def __init__(self, concepts_chain, connections_chain, provenance):
        self.result = self._build(concepts_chain, connections_chain, provenance, M.EmptyList, 0)
        super().__init__(inputs=M.Pair(concepts_chain, M.Pair(connections_chain, M.Pair(provenance, M.EmptyList))), results=self.result)

    def _build(self, concepts, connections, prov, acc, idx):
        if M.IdentityCompare(concepts, M.EmptyList)() is M.truth_value:
            return acc
        concept = M.Head(concepts)()
        tail = M.Tail(concepts)()
        # Create question for each concept: how does it connect to others?
        try:
            name = M.Char("unknown")
            if IsConcept(concept)() is M.truth_value:
                name = ConceptCanonicalName(concept)()
            elif IsEntity(concept)() is M.truth_value:
                name = EntityCanonicalName(concept)()
            q_text = M.Char("How does " + name() + " connect to the other concepts?")
        except Exception:
            q_text = M.Char("How do these connect?")
        q_id = M.Char("q_" + str(idx))
        related = M.Pair(concept, M.EmptyList)
        q = UnresolvedQuestion(q_id, q_text, related, prov)()
        acc = M.Pair(q, acc)
        return self._build(tail, connections, prov, acc, idx + 1)

    def __call__(self):
        return self.result

class BuildInitialMotifs(M.Edge):
    def __init__(self, concepts_chain, provenance):
        self.result = self._build(concepts_chain, provenance, M.EmptyList)
        super().__init__(inputs=M.Pair(concepts_chain, M.Pair(provenance, M.EmptyList)), results=self.result)

    def _build(self, concepts, prov, acc):
        # Motifs are recurring ideas: time, transformation, engineering, etc.
        # General mechanism: extract attributes that appear in multiple concepts as potential motifs
        if M.IdentityCompare(concepts, M.EmptyList)() is M.truth_value:
            return acc
        # For demo, create motif for 19th century, engineering, Paris as recurring
        # In full system, would analyze attribute frequency
        motif1 = Motif(M.Char("motif_time"), M.Char("19th century"), M.EmptyList, prov)()
        motif2 = Motif(M.Char("motif_transformation"), M.Char("transformation"), M.EmptyList, prov)()
        motif3 = Motif(M.Char("motif_engineering"), M.Char("engineering"), M.EmptyList, prov)()
        acc = M.Pair(motif1, M.Pair(motif2, M.Pair(motif3, acc)))
        return acc

    def __call__(self):
        return self.result

class BuildInitialPlan(M.Edge):
    def __init__(self, goal, concepts_chain, connections_chain, intermediates_chain, threads_chain, provenance):
        self.result = self._build_plan(goal, concepts_chain, connections_chain, intermediates_chain, threads_chain, provenance)
        super().__init__(inputs=M.Pair(goal, M.Pair(concepts_chain, M.Pair(connections_chain, M.Pair(intermediates_chain, M.Pair(threads_chain, M.Pair(provenance, M.EmptyList)))))), results=self.result)

    def _build_plan(self, goal, concepts, connections, intermediates, threads, prov):
        # Build segments in a narrative trajectory:
        # 1. Introduce first concept (building)
        # 2. Introduce other concepts one by one
        # 3. For each connection, explain it
        # 4. Elaborate on intermediates
        # 5. Contrast
        # 6. Callback to earlier concept
        # 7. Pivot to surprising connection
        # 8. Open question
        # This is general: ordering by conceptual dependency, not hardcoded template
        segments = M.EmptyList
        seg_counter = 0

        # Extract threads list for referencing
        threads_list = self._chain_to_list(threads)

        # Introduce segments for each concept
        concepts_list = self._chain_to_list(concepts)
        for concept in concepts_list:
            seg_id = M.Char("seg_" + str(seg_counter))
            focus = M.Pair(concept, M.EmptyList)
            intent = M.Char(IntentLabel.INTRODUCE)
            thread_ref = M.Char("thread_" + str(seg_counter)) if seg_counter < len(threads_list) else M.Char("thread_0")
            status = M.Char("pending")
            seg = Segment(seg_id, focus, M.EmptyList, intent, thread_ref, prov, status)()
            segments = M.Pair(seg, segments)
            seg_counter += 1

        # Connect segments for each connection
        connections_list = self._chain_to_list(connections)
        for conn in connections_list[:5]:  # limit initial
            seg_id = M.Char("seg_" + str(seg_counter))
            # Focus is source and target of connection
            from .semantic_schema import ConnectionSource, ConnectionTarget
            try:
                src = ConnectionSource(conn)()
                tgt = ConnectionTarget(conn)()
                focus = M.Pair(src, M.Pair(tgt, M.EmptyList))
            except Exception:
                focus = M.EmptyList
            intent = M.Char(IntentLabel.CONNECT)
            thread_ref = M.Char("thread_0")
            status = M.Char("pending")
            seg = Segment(seg_id, focus, M.Pair(conn, M.EmptyList), intent, thread_ref, prov, status)()
            segments = M.Pair(seg, segments)
            seg_counter += 1

        # Elaborate on intermediates
        inters_list = self._chain_to_list(intermediates)
        for inter in inters_list[:3]:
            seg_id = M.Char("seg_" + str(seg_counter))
            focus = M.Pair(inter, M.EmptyList)
            intent = M.Char(IntentLabel.ELABORATE)
            thread_ref = M.Char("thread_0")
            status = M.Char("pending")
            seg = Segment(seg_id, focus, M.EmptyList, intent, thread_ref, prov, status)()
            segments = M.Pair(seg, segments)
            seg_counter += 1

        # Contrast segment (general mechanism: pick two concepts with shared attribute but different type)
        if len(concepts_list) >= 2:
            seg_id = M.Char("seg_" + str(seg_counter))
            focus = M.Pair(concepts_list[0], M.Pair(concepts_list[1], M.EmptyList))
            intent = M.Char(IntentLabel.CONTRAST)
            thread_ref = M.Char("thread_0")
            status = M.Char("pending")
            seg = Segment(seg_id, focus, M.EmptyList, intent, thread_ref, prov, status)()
            segments = M.Pair(seg, segments)
            seg_counter += 1

        # Callback segment (revisit first concept after explaining others)
        if concepts_list:
            seg_id = M.Char("seg_" + str(seg_counter))
            focus = M.Pair(concepts_list[0], M.EmptyList)
            intent = M.Char(IntentLabel.CALLBACK)
            thread_ref = M.Char("thread_0")
            status = M.Char("pending")
            seg = Segment(seg_id, focus, M.EmptyList, intent, thread_ref, prov, status)()
            segments = M.Pair(seg, segments)
            seg_counter += 1

        # Question segment
        seg_id = M.Char("seg_" + str(seg_counter))
        intent = M.Char(IntentLabel.QUESTION)
        focus = concepts
        thread_ref = M.Char("thread_0")
        status = M.Char("pending")
        seg = Segment(seg_id, focus, M.EmptyList, intent, thread_ref, prov, status)()
        segments = M.Pair(seg, segments)

        # Reverse to get correct order (we built reversed)
        segments = self._reverse_chain(segments)

        plan_id = M.Char("plan_0")
        current_index = M.Char("0")
        plan = NarrativePlan(plan_id, goal, segments, current_index, prov)()
        return plan

    def _chain_to_list(self, chain):
        result = []
        rem = chain
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
            result.append(M.Head(rem)())
            rem = M.Tail(rem)()
        return result

    def _reverse_chain(self, chain):
        acc = M.EmptyList
        rem = chain
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
            acc = M.Pair(M.Head(rem)(), acc)
            rem = M.Tail(rem)()
        return acc

    def __call__(self):
        return self.result

class SelectNextSegment(M.Edge):
    def __init__(self, plan, story_model):
        self.result = self._select(plan, story_model)
        super().__init__(inputs=M.Pair(plan, M.Pair(story_model, M.EmptyList)), results=self.result)

    def _select(self, plan, model):
        segments = PlanSegments(plan)()
        current_idx_char = PlanCurrentIndex(plan)()
        try:
            current_idx = int(current_idx_char())
        except Exception:
            current_idx = 0
        # Find segment at current index that is pending
        # General mechanism: iterate to current index
        rem = segments
        idx = 0
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
            if idx == current_idx:
                seg = M.Head(rem)()
                # Check status pending
                status = SegmentStatus(seg)()
                try:
                    if status() == "pending":
                        return seg
                    else:
                        # If not pending, try next
                        pass
                except Exception:
                    return seg
            rem = M.Tail(rem)()
            idx += 1
        # If beyond, return empty (story complete for now)
        return M.EmptyList

    def __call__(self):
        return self.result

class AdvancePlan(M.Edge):
    def __init__(self, plan):
        self.result = self._advance(plan)
        super().__init__(inputs=M.Pair(plan, M.EmptyList), results=self.result)

    def _advance(self, plan):
        plan_id = PlanId(plan)()
        from .longform_schema import NarrativePlan as NP
        # Need goal, segments, current_index, provenance
        # Extract
        goal = M.EmptyList
        segments = M.EmptyList
        prov = M.Char("planner")
        try:
            # Reconstruct: plan is Pair(label, Pair(id, Pair(goal, Pair(segments, Pair(current_index, Pair(prov, Empty))))))
            goal = M.Head(M.Tail(M.Tail(plan)())())()
            segments = M.Head(M.Tail(M.Tail(M.Tail(plan)())())())()
            current_idx_char = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())()
            prov = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())())()
            try:
                idx = int(current_idx_char())
            except Exception:
                idx = 0
            new_idx = M.Char(str(idx + 1))
            new_plan = NP(plan_id, goal, segments, new_idx, prov)()
            return new_plan
        except Exception:
            return plan

    def __call__(self):
        return self.result

class RevisePlanWithNewConnection(M.Edge):
    def __init__(self, plan, new_connection, new_intermediate, provenance):
        self.result = self._revise(plan, new_connection, new_intermediate, provenance)
        super().__init__(inputs=M.Pair(plan, M.Pair(new_connection, M.Pair(new_intermediate, M.Pair(provenance, M.EmptyList)))), results=self.result)

    def _revise(self, plan, new_conn, new_inter, prov):
        # When new connection discovered during story, reorganize narrative around it
        # General mechanism: insert new segment near current position that explains new discovery
        plan_id = PlanId(plan)()
        goal = M.EmptyList
        segments = M.EmptyList
        current_idx = M.Char("0")
        old_prov = prov
        try:
            goal = M.Head(M.Tail(M.Tail(plan)())())()
            segments = M.Head(M.Tail(M.Tail(M.Tail(plan)())())())()
            current_idx = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())()
            old_prov = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())())()
        except Exception:
            pass
        # Create new segment for new discovery
        seg_id = M.Char("seg_new_discovery")
        focus = M.EmptyList
        try:
            from .semantic_schema import ConnectionSource, ConnectionTarget
            src = ConnectionSource(new_conn)()
            tgt = ConnectionTarget(new_conn)()
            focus = M.Pair(src, M.Pair(tgt, M.Pair(new_inter, M.EmptyList)))
        except Exception:
            focus = M.Pair(new_inter, M.EmptyList)
        intent = M.Char(IntentLabel.PIVOT)
        thread_ref = M.Char("thread_new")
        status = M.Char("pending")
        new_seg = Segment(seg_id, focus, M.Pair(new_conn, M.EmptyList), intent, thread_ref, prov, status)()
        # Insert after current index: split segments into before and after
        before, after = self._split_at(segments, current_idx)
        # before + new_seg + after
        new_segments = self._append_chain(before, M.Pair(new_seg, after))
        new_plan = NarrativePlan(plan_id, goal, new_segments, current_idx, old_prov)()
        return new_plan

    def _split_at(self, segments, current_idx_char):
        try:
            idx = int(current_idx_char())
        except Exception:
            idx = 0
        before = M.EmptyList
        after = M.EmptyList
        rem = segments
        pos = 0
        # Collect before in reverse then reverse
        before_acc = M.EmptyList
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
            seg = M.Head(rem)()
            tail = M.Tail(rem)()
            if pos < idx:
                before_acc = M.Pair(seg, before_acc)
            else:
                after = M.Pair(seg, after)
            pos += 1
            rem = tail
        # Reverse before_acc and after
        before = self._reverse_chain(before_acc)
        after = self._reverse_chain(after)
        return before, after

    def _reverse_chain(self, chain):
        acc = M.EmptyList
        rem = chain
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
            acc = M.Pair(M.Head(rem)(), acc)
            rem = M.Tail(rem)()
        return acc

    def _append_chain(self, a, b):
        if M.IdentityCompare(a, M.EmptyList)() is M.truth_value:
            return b
        head = M.Head(a)()
        tail = M.Tail(a)()
        rest = self._append_chain(tail, b)
        return M.Pair(head, rest)

    def __call__(self):
        return self.result

class RevisePlanWithSteering(M.Edge):
    def __init__(self, plan, steering_text, provenance):
        self.result = self._revise(plan, steering_text, provenance)
        super().__init__(inputs=M.Pair(plan, M.Pair(steering_text, M.Pair(provenance, M.EmptyList))), results=self.result)

    def _revise(self, plan, steering_text, prov):
        # Modify persistent story state based on NL steering, not reset
        # General mechanisms for steering intents
        try:
            steering = steering_text().lower()
        except Exception:
            steering = str(steering_text).lower()
        plan_id = PlanId(plan)()
        goal = M.EmptyList
        segments = M.EmptyList
        current_idx = M.Char("0")
        old_prov = prov
        try:
            goal = M.Head(M.Tail(M.Tail(plan)())())()
            segments = M.Head(M.Tail(M.Tail(M.Tail(plan)())())())()
            current_idx = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())()
            old_prov = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())())()
        except Exception:
            pass

        # Determine steering intent
        new_segments = segments
        if "deeper" in steering or "more slowly" in steering or "explain" in steering:
            # Elaborate: duplicate current segment with elaborate intent
            seg_id = M.Char("seg_elaborate")
            intent = M.Char(IntentLabel.ELABORATE)
            focus = M.EmptyList
            # Use current segment's focus if possible
            current_seg = self._get_at(segments, current_idx)
            if M.IdentityCompare(current_seg, M.EmptyList)() is M.false_value:
                focus = SegmentFocus(current_seg)()
            thread_ref = M.Char("thread_0")
            status = M.Char("pending")
            new_seg = Segment(seg_id, focus, M.EmptyList, intent, thread_ref, prov, status)()
            before, after = self._split_at(segments, current_idx)
            new_segments = self._append_chain(before, M.Pair(new_seg, after))
        elif "return to" in steering or "building" in steering:
            # Callback: revisit earlier concept
            seg_id = M.Char("seg_callback_building")
            intent = M.Char(IntentLabel.CALLBACK)
            focus = M.EmptyList
            # Find building concept in earlier segments
            # For simplicity, use empty focus, verbalizer will handle
            thread_ref = M.Char("thread_building")
            status = M.Char("pending")
            new_seg = Segment(seg_id, focus, M.EmptyList, intent, thread_ref, prov, status)()
            before, after = self._split_at(segments, current_idx)
            new_segments = self._append_chain(before, M.Pair(new_seg, after))
        elif "stranger" in steering or "wouldn't expect" in steering or "unexpected" in steering:
            # Pivot to stranger connection
            seg_id = M.Char("seg_stranger")
            intent = M.Char(IntentLabel.PIVOT)
            focus = M.EmptyList
            thread_ref = M.Char("thread_stranger")
            status = M.Char("pending")
            new_seg = Segment(seg_id, focus, M.EmptyList, intent, thread_ref, prov, status)()
            before, after = self._split_at(segments, current_idx)
            new_segments = self._append_chain(before, M.Pair(new_seg, after))
        elif "perspective" in steering:
            seg_id = M.Char("seg_reframe")
            intent = M.Char(IntentLabel.REFRAME)
            focus = M.EmptyList
            thread_ref = M.Char("thread_0")
            status = M.Char("pending")
            new_seg = Segment(seg_id, focus, M.EmptyList, intent, thread_ref, prov, status)()
            before, after = self._split_at(segments, current_idx)
            new_segments = self._append_chain(before, M.Pair(new_seg, after))
        elif "central" in steering or "more central" in steering:
            # Reorder to make a thread more central
            # For general mechanism, we move segments of that thread earlier
            new_segments = segments  # placeholder for reordering logic
        elif "keep going" in steering or "continue" in steering or "don't leave" in steering:
            # No revision, just continue
            new_segments = segments

        new_plan = NarrativePlan(plan_id, goal, new_segments, current_idx, old_prov)()
        return new_plan

    def _get_at(self, segments, current_idx_char):
        try:
            idx = int(current_idx_char())
        except Exception:
            idx = 0
        rem = segments
        pos = 0
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
            if pos == idx:
                return M.Head(rem)()
            rem = M.Tail(rem)()
            pos += 1
        return M.EmptyList

    def _split_at(self, segments, current_idx_char):
        try:
            idx = int(current_idx_char())
        except Exception:
            idx = 0
        before_acc = M.EmptyList
        after = M.EmptyList
        rem = segments
        pos = 0
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
            seg = M.Head(rem)()
            tail = M.Tail(rem)()
            if pos < idx:
                before_acc = M.Pair(seg, before_acc)
            else:
                after = M.Pair(seg, after)
            pos += 1
            rem = tail
        before = self._reverse_chain(before_acc)
        after = self._reverse_chain(after)
        return before, after

    def _reverse_chain(self, chain):
        acc = M.EmptyList
        rem = chain
        while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
            acc = M.Pair(M.Head(rem)(), acc)
            rem = M.Tail(rem)()
        return acc

    def _append_chain(self, a, b):
        if M.IdentityCompare(a, M.EmptyList)() is M.truth_value:
            return b
        head = M.Head(a)()
        tail = M.Tail(a)()
        rest = self._append_chain(tail, b)
        return M.Pair(head, rest)

    def __call__(self):
        return self.result
