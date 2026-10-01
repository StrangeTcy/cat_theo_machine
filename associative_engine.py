from . import machine as M
from . import labels as L
from . import graph as G
from .semantic_schema import Concept, IsConcept, ConceptId, ConceptCanonicalName, ConceptAttributes, ConceptType
from .semantic_schema import Intermediate, IsIntermediate, IntermediateId, IntermediateCanonicalName, IntermediateConnects
from .semantic_schema import Connection, IsConnection, ConnectionSource, ConnectionTarget, ConnectionVia, ConnectionVerification, ConnectionConfidence
from .semantic_schema import Verification, VerificationStatus
from .story_schema import Entity, IsEntity, EntityId, EntityCanonicalName, EntityAttributes
from .story_schema import Relation, IsRelation, RelationSource, RelationTarget, RelationConfidence
from .story_alignment import BuildGraphVersion, AddRelationsToGraphVersion, FindConnectionPath


class ConceptAttributeChainHas(M.Edge):
    def __init__(self, attr_chain, value):
        self.result = self._has(attr_chain, value)
        super().__init__(inputs=M.Pair(attr_chain, M.Pair(value, M.EmptyList)), results=self.result)

    def _has(self, chain, value):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        head = M.Head(chain)()
        tail = M.Tail(chain)()
        if M.Compare(head, value)() is M.truth_value:
            return M.truth_value
        return self._has(tail, value)

    def __call__(self):
        return self.result


class CommonAttributes(M.Edge):
    def __init__(self, attrs_a, attrs_b):
        self.result = self._common(attrs_a, attrs_b, M.EmptyList)
        super().__init__(inputs=M.Pair(attrs_a, M.Pair(attrs_b, M.EmptyList)), results=self.result)

    def _common(self, a_chain, b_chain, acc):
        if M.IdentityCompare(a_chain, M.EmptyList)() is M.truth_value:
            return acc
        head = M.Head(a_chain)()
        tail = M.Tail(a_chain)()
        if ConceptAttributeChainHas(b_chain, head)() is M.truth_value:
            if ConceptAttributeChainHas(acc, head)() is M.false_value:
                acc = M.Pair(head, acc)
        return self._common(tail, b_chain, acc)

    def __call__(self):
        return self.result


class FindCommonAttributeAmongConcepts(M.Edge):
    def __init__(self, concepts):
        self.result = self._find(concepts)
        super().__init__(inputs=M.Pair(concepts, M.EmptyList), results=self.result)

    def _find(self, concepts):
        if M.IdentityCompare(concepts, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(M.Tail(concepts)(), M.EmptyList)() is M.truth_value:
            only = M.Head(concepts)()
            if IsConcept(only)() is M.truth_value:
                return ConceptAttributes(only)()
            if IsEntity(only)() is M.truth_value:
                return EntityAttributes(only)()
            return M.EmptyList
        first = M.Head(concepts)()
        rest = M.Tail(concepts)()
        first_attrs = M.EmptyList
        if IsConcept(first)() is M.truth_value:
            first_attrs = ConceptAttributes(first)()
        elif IsEntity(first)() is M.truth_value:
            first_attrs = EntityAttributes(first)()
        rest_common = self._find(rest)
        if M.IdentityCompare(rest_common, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return CommonAttributes(first_attrs, rest_common)()

    def __call__(self):
        return self.result


class ProposeIntermediateFromCommonAttribute(M.Edge):
    def __init__(self, common_attr, concepts, provenance, confidence):
        inter_id = M.Char(common_attr() + "_intermediate")
        connects = concepts
        ver = Verification(M.Char("ver_" + common_attr() + "_intermediate"), M.Char("verified"), M.Pair(M.Char("attribute_overlap"), M.Pair(common_attr, M.EmptyList)))()
        inter = Intermediate(inter_id, common_attr, connects, ver, confidence, provenance)()
        self.result = inter
        super().__init__(inputs=M.Pair(common_attr, M.Pair(concepts, M.Pair(provenance, M.Pair(confidence, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class InventIntermediatesFromConcepts(M.Edge):
    def __init__(self, concepts, provenance):
        self.result = self._invent(concepts, provenance)
        super().__init__(inputs=M.Pair(concepts, M.Pair(provenance, M.EmptyList)), results=self.result)

    def _invent(self, concepts, provenance):
        common = FindCommonAttributeAmongConcepts(concepts)()
        invented = M.EmptyList
        conf = M.Char("0.8")
        invented = self._invent_from_common(common, concepts, provenance, conf, invented)
        invented = self._invent_pairwise(concepts, concepts, provenance, invented)
        return invented

    def _invent_from_common(self, common_chain, concepts, provenance, conf, acc):
        if M.IdentityCompare(common_chain, M.EmptyList)() is M.truth_value:
            return acc
        attr = M.Head(common_chain)()
        tail = M.Tail(common_chain)()
        inter = ProposeIntermediateFromCommonAttribute(attr, concepts, provenance, conf)()
        acc = M.Pair(inter, acc)
        return self._invent_from_common(tail, concepts, provenance, conf, acc)

    def _invent_pairwise(self, outer, all_concepts, provenance, acc):
        if M.IdentityCompare(outer, M.EmptyList)() is M.truth_value:
            return acc
        c_a = M.Head(outer)()
        tail_outer = M.Tail(outer)()
        acc = self._invent_pairwise_inner(c_a, M.Tail(outer)(), provenance, acc)
        return self._invent_pairwise(tail_outer, all_concepts, provenance, acc)

    def _invent_pairwise_inner(self, c_a, inner, provenance, acc):
        if M.IdentityCompare(inner, M.EmptyList)() is M.truth_value:
            return acc
        c_b = M.Head(inner)()
        tail_inner = M.Tail(inner)()
        attrs_a = M.EmptyList
        attrs_b = M.EmptyList
        name_a = M.Char("a")
        name_b = M.Char("b")
        if IsConcept(c_a)() is M.truth_value:
            attrs_a = ConceptAttributes(c_a)()
            name_a = ConceptCanonicalName(c_a)()
        elif IsEntity(c_a)() is M.truth_value:
            attrs_a = EntityAttributes(c_a)()
            name_a = EntityCanonicalName(c_a)()
        if IsConcept(c_b)() is M.truth_value:
            attrs_b = ConceptAttributes(c_b)()
            name_b = ConceptCanonicalName(c_b)()
        elif IsEntity(c_b)() is M.truth_value:
            attrs_b = EntityAttributes(c_b)()
            name_b = EntityCanonicalName(c_b)()
        common_ab = CommonAttributes(attrs_a, attrs_b)()
        if M.IdentityCompare(common_ab, M.EmptyList)() is M.truth_value:
            bridge_name = M.Char(name_a() + "-" + name_b() + "-bridge")
            pair_concepts = M.Pair(c_a, M.Pair(c_b, M.EmptyList))
            ver = Verification(M.Char("ver_" + bridge_name() + "_id"), M.Char("hypothetical"), M.Pair(M.Char("invention_by_combination"), M.Pair(bridge_name, M.EmptyList)))()
            inter = Intermediate(M.Char(bridge_name() + "_id"), bridge_name, pair_concepts, ver, M.Char("0.6"), provenance)()
            acc = M.Pair(inter, acc)
        else:
            # Also invent intermediates for pairwise common attributes (not just universal)
            # This provides more candidates for stranger connections
            acc = self._invent_from_common_pair(common_ab, M.Pair(c_a, M.Pair(c_b, M.EmptyList)), provenance, M.Char("0.7"), acc)
        return self._invent_pairwise_inner(c_a, tail_inner, provenance, acc)

    def _invent_from_common_pair(self, common_chain, pair_concepts, provenance, conf, acc):
        if M.IdentityCompare(common_chain, M.EmptyList)() is M.truth_value:
            return acc
        attr = M.Head(common_chain)()
        tail = M.Tail(common_chain)()
        inter = ProposeIntermediateFromCommonAttribute(attr, pair_concepts, provenance, conf)()
        acc = M.Pair(inter, acc)
        return self._invent_from_common_pair(tail, pair_concepts, provenance, conf, acc)

    def __call__(self):
        return self.result


class VerifyIntermediate(M.Edge):
    def __init__(self, intermediate, graph_version):
        connects = IntermediateConnects(intermediate)()
        from .semantic_schema import IntermediateVerification
        ver_term = IntermediateVerification(intermediate)()
        status = M.Char("unknown")
        if M.IsPair(ver_term)() is M.truth_value:
            status = VerificationStatus(ver_term)()
        if M.Compare(status, M.Char("verified"))() is M.truth_value:
            self.result = M.truth_value
        else:
            if M.Compare(status, M.Char("hypothetical"))() is M.truth_value:
                self.result = M.truth_value
            else:
                self.result = M.false_value
        super().__init__(inputs=M.Pair(intermediate, M.Pair(graph_version, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FilterVerifiedIntermediates(M.Edge):
    def __init__(self, intermediates, graph_version):
        self.result = self._filter(intermediates, graph_version, M.EmptyList)
        super().__init__(inputs=M.Pair(intermediates, M.Pair(graph_version, M.EmptyList)), results=self.result)

    def _filter(self, intermediates, gv, acc):
        if M.IdentityCompare(intermediates, M.EmptyList)() is M.truth_value:
            return acc
        head = M.Head(intermediates)()
        tail = M.Tail(intermediates)()
        if VerifyIntermediate(head, gv)() is M.truth_value:
            acc = M.Pair(head, acc)
        return self._filter(tail, gv, acc)

    def __call__(self):
        return self.result


class BuildConnectionsViaIntermediates(M.Edge):
    def __init__(self, concepts, intermediates, provenance):
        self.result = self._build_outer(concepts, intermediates, provenance, M.EmptyList)
        super().__init__(inputs=M.Pair(concepts, M.Pair(intermediates, M.Pair(provenance, M.EmptyList))), results=self.result)

    def _build_outer(self, concepts, intermediates, provenance, acc):
        if M.IdentityCompare(concepts, M.EmptyList)() is M.truth_value:
            return acc
        if M.IdentityCompare(intermediates, M.EmptyList)() is M.truth_value:
            return acc
        c_head = M.Head(concepts)()
        c_tail = M.Tail(concepts)()
        acc = self._build_inner(c_head, intermediates, acc)
        return self._build_outer(c_tail, intermediates, provenance, acc)

    def _build_inner(self, c_head, inter_chain, acc):
        if M.IdentityCompare(inter_chain, M.EmptyList)() is M.truth_value:
            return acc
        inter = M.Head(inter_chain)()
        tail = M.Tail(inter_chain)()
        acc = self._build_for_one_intermediate(c_head, inter, IntermediateConnects(inter)(), acc)
        return self._build_inner(c_head, tail, acc)

    def _build_for_one_intermediate(self, c_head, inter, other_chain, acc):
        if M.IdentityCompare(other_chain, M.EmptyList)() is M.truth_value:
            return acc
        other = M.Head(other_chain)()
        rest = M.Tail(other_chain)()
        if M.IdentityCompare(other, c_head)() is M.false_value:
            try:
                src_name = M.Char("src")
                tgt_name = M.Char("tgt")
                if IsConcept(c_head)() is M.truth_value:
                    src_name = ConceptCanonicalName(c_head)()
                elif IsEntity(c_head)() is M.truth_value:
                    src_name = EntityCanonicalName(c_head)()
                if IsConcept(other)() is M.truth_value:
                    tgt_name = ConceptCanonicalName(other)()
                elif IsEntity(other)() is M.truth_value:
                    tgt_name = EntityCanonicalName(other)()
                conn_id = M.Char(src_name() + "_to_" + tgt_name() + "_via_" + IntermediateId(inter)()())
            except Exception:
                conn_id = M.Char("conn")
            ver = Verification(M.Char("ver_conn"), M.Char("verified"), M.Pair(inter, M.EmptyList))()
            conf = M.Char("0.8")
            conn = Connection(conn_id, c_head, other, inter, ver, conf)()
            acc = M.Pair(conn, acc)
        return self._build_for_one_intermediate(c_head, inter, rest, acc)

    def __call__(self):
        return self.result


class FindExistingPathsBetweenConcepts(M.Edge):
    def __init__(self, graph_version, concepts):
        self.result = self._find_paths(graph_version, concepts, M.EmptyList)
        super().__init__(inputs=M.Pair(graph_version, M.Pair(concepts, M.EmptyList)), results=self.result)

    def _find_paths(self, gv, concepts, acc):
        if M.IdentityCompare(concepts, M.EmptyList)() is M.truth_value:
            return acc
        head = M.Head(concepts)()
        tail = M.Tail(concepts)()
        name_head = M.Char("unknown")
        if IsConcept(head)() is M.truth_value:
            name_head = ConceptCanonicalName(head)()
        elif IsEntity(head)() is M.truth_value:
            name_head = EntityCanonicalName(head)()
        acc = self._find_paths_for_one(gv, name_head, tail, acc)
        return self._find_paths(gv, tail, acc)

    def _find_paths_for_one(self, gv, name_head, other_chain, acc):
        if M.IdentityCompare(other_chain, M.EmptyList)() is M.truth_value:
            return acc
        other = M.Head(other_chain)()
        rest = M.Tail(other_chain)()
        name_other = M.Char("unknown")
        if IsConcept(other)() is M.truth_value:
            name_other = ConceptCanonicalName(other)()
        elif IsEntity(other)() is M.truth_value:
            name_other = EntityCanonicalName(other)()
        path = FindConnectionPath(gv, name_head, name_other)()
        if M.IdentityCompare(path, M.EmptyList)() is M.false_value:
            acc = M.Pair(path, acc)
        return self._find_paths_for_one(gv, name_head, rest, acc)

    def __call__(self):
        return self.result


class ActivateRelevantSubgraph(M.Edge):
    def __init__(self, graph_version, concepts):
        self.result = graph_version
        super().__init__(inputs=M.Pair(graph_version, M.Pair(concepts, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SynthesizeNarrativeStructure(M.Edge):
    def __init__(self, concepts, connections, intermediates, task_type):
        chain = M.EmptyList
        chain = self._append_chain(concepts, chain)
        chain = self._append_chain(intermediates, chain)
        chain = self._append_chain(connections, chain)
        self.result = M.Pair(L.NarrativeLabel, M.Pair(task_type, M.Pair(chain, M.EmptyList)))
        super().__init__(inputs=M.Pair(concepts, M.Pair(connections, M.Pair(intermediates, M.Pair(task_type, M.EmptyList)))), results=self.result)

    def _append_chain(self, src, dest):
        if M.IdentityCompare(src, M.EmptyList)() is M.truth_value:
            return dest
        head = M.Head(src)()
        tail = M.Tail(src)()
        dest = M.Pair(head, dest)
        return self._append_chain(tail, dest)

    def __call__(self):
        return self.result


class IsNarrative(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), L.NarrativeLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NarrativeTaskType(M.Edge):
    def __init__(self, narrative):
        self.result = M.Head(M.Tail(narrative)())()
        super().__init__(inputs=M.Pair(narrative, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NarrativeChain(M.Edge):
    def __init__(self, narrative):
        self.result = M.Head(M.Tail(M.Tail(narrative)())())()
        super().__init__(inputs=M.Pair(narrative, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result
