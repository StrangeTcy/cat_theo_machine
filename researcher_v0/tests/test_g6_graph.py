"""Executable acceptance tests for Researcher-v0 G6 inert discovery graph."""

from __future__ import annotations

import os

from ... import machine as M
from .. import discovery_graph as DG
from .. import in_run_use as U
from .. import laboratory as L
from .. import mining as X
from .. import task_generation as G
from .. import token_domain as D
from ..chains import ChainAppend, IsEmptyTerm


class FileText(M.Edge):
    def __init__(self, path):
        handle = open(path)
        self.result = handle.read()
        handle.close()
        super().__init__(inputs=M.Pair(M.Char(path), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CountIs(M.Edge):
    def __init__(self, chain, expected):
        self.result = X.ReportingCountEquals(X.ChainCount(chain)(), expected)()
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ExactGraphCounts(M.Edge):
    def __init__(self, graph):
        if CountIs(DG.PartNodes(graph)(), 172)() is M.false_value:
            self.result = M.false_value
        else:
            self.result = CountIs(DG.PartEdges(graph)(), 173)()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ExactNodeKinds(M.Edge):
    def __init__(self, graph):
        nodes = DG.PartNodes(graph)()
        if X.ReportingCountEquals(
            DG.NodeKindCount(nodes, M.Char("Task"))(), 42
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.NodeKindCount(nodes, M.Char("Attempt"))(), 34
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.NodeKindCount(nodes, M.Char("Transition"))(), 5
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.NodeKindCount(nodes, M.Char("Outcome"))(), 34
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.NodeKindCount(nodes, M.Char("CandidateInvariant"))(), 8
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.NodeKindCount(nodes, M.Char("BrokenOn"))(), 5
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.NodeKindCount(nodes, M.Char("Certificate"))(), 32
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.NodeKindCount(nodes, M.Char("PruneEvent"))(), 8
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = X.ReportingCountEquals(
                DG.NodeKindCount(nodes, M.Char("ScopeMismatch"))(), 4
            )()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ExactEdgeKinds(M.Edge):
    def __init__(self, graph):
        edges = DG.PartEdges(graph)()
        if X.ReportingCountEquals(
            DG.EdgeKindCount(edges, M.Char("generated_from"))(), 35
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.EdgeKindCount(edges, M.Char("attempted"))(), 34
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.EdgeKindCount(edges, M.Char("produced"))(), 68
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.EdgeKindCount(edges, M.Char("broke"))(), 5
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.EdgeKindCount(edges, M.Char("proposed_from"))(), 8
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.EdgeKindCount(edges, M.Char("proved_by"))(), 3
        )() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(
            DG.EdgeKindCount(edges, M.Char("used_by"))(), 16
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = X.ReportingCountEquals(
                DG.EdgeKindCount(edges, M.Char("invalidated_by"))(), 4
            )()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NodeIdAbsent(M.Edge):
    def __init__(self, nodes, node_id):
        self.result = self._walk(nodes, node_id)
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def _walk(self, nodes, node_id):
        if IsEmptyTerm(nodes)() is M.truth_value:
            return M.truth_value
        if M.Compare(DG.NodeId(M.Head(nodes)())(), node_id)() is M.truth_value:
            return M.false_value
        return self._walk(M.Tail(nodes)(), node_id)

    def __call__(self):
        return self.result


class UniqueNodeIds(M.Edge):
    def __init__(self, nodes):
        self.result = self._walk(nodes)
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def _walk(self, nodes):
        if IsEmptyTerm(nodes)() is M.truth_value:
            return M.truth_value
        rest = M.Tail(nodes)()
        if NodeIdAbsent(rest, DG.NodeId(M.Head(nodes)())())() is M.false_value:
            return M.false_value
        return self._walk(rest)

    def __call__(self):
        return self.result


class EdgeIdAbsent(M.Edge):
    def __init__(self, edges, edge_id):
        self.result = self._walk(edges, edge_id)
        super().__init__(inputs=M.Pair(edges, M.EmptyList), results=self.result)

    def _walk(self, edges, edge_id):
        if IsEmptyTerm(edges)() is M.truth_value:
            return M.truth_value
        if M.Compare(DG.EdgeId(M.Head(edges)())(), edge_id)() is M.truth_value:
            return M.false_value
        return self._walk(M.Tail(edges)(), edge_id)

    def __call__(self):
        return self.result


class UniqueEdgeIds(M.Edge):
    def __init__(self, edges):
        self.result = self._walk(edges)
        super().__init__(inputs=M.Pair(edges, M.EmptyList), results=self.result)

    def _walk(self, edges):
        if IsEmptyTerm(edges)() is M.truth_value:
            return M.truth_value
        rest = M.Tail(edges)()
        if EdgeIdAbsent(rest, DG.EdgeId(M.Head(edges)())())() is M.false_value:
            return M.false_value
        return self._walk(rest)

    def __call__(self):
        return self.result


class FindNode(M.Edge):
    def __init__(self, nodes, node_id):
        self.result = self._walk(nodes, node_id)
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def _walk(self, nodes, node_id):
        if IsEmptyTerm(nodes)() is M.truth_value:
            return M.EmptyList
        node = M.Head(nodes)()
        if M.Compare(DG.NodeId(node)(), node_id)() is M.truth_value:
            return M.Pair(node, M.EmptyList)
        return self._walk(M.Tail(nodes)(), node_id)

    def __call__(self):
        return self.result


class AllEndpointsResolve(M.Edge):
    def __init__(self, nodes, edges):
        self.result = self._walk(nodes, edges)
        super().__init__(inputs=M.Pair(edges, M.EmptyList), results=self.result)

    def _walk(self, nodes, edges):
        if IsEmptyTerm(edges)() is M.truth_value:
            return M.truth_value
        edge = M.Head(edges)()
        if IsEmptyTerm(FindNode(nodes, DG.EdgeSourceId(edge)())())() is M.truth_value:
            return M.false_value
        if IsEmptyTerm(FindNode(nodes, DG.EdgeTargetId(edge)())())() is M.truth_value:
            return M.false_value
        return self._walk(nodes, M.Tail(edges)())

    def __call__(self):
        return self.result


class SourceRefsComplete(M.Edge):
    def __init__(self, edges):
        self.result = self._edges(edges)
        super().__init__(inputs=M.Pair(edges, M.EmptyList), results=self.result)

    def _sources(self, sources):
        if IsEmptyTerm(sources)() is M.truth_value:
            return M.false_value
        return self._source_items(sources)

    def _source_items(self, sources):
        if IsEmptyTerm(sources)() is M.truth_value:
            return M.truth_value
        source = M.Head(sources)()
        if M.Compare(
            DG.SourceArtifact(source)(), M.Char("")
        )() is M.truth_value:
            return M.false_value
        if M.Compare(
            DG.SourceRecordId(source)(), M.Char("")
        )() is M.truth_value:
            return M.false_value
        return self._source_items(M.Tail(sources)())

    def _edges(self, edges):
        if IsEmptyTerm(edges)() is M.truth_value:
            return M.truth_value
        if self._sources(DG.EdgeSources(M.Head(edges)())()) is M.false_value:
            return M.false_value
        return self._edges(M.Tail(edges)())

    def __call__(self):
        return self.result


class AllowedArtifact(M.Edge):
    def __init__(self, artifact):
        if M.Compare(
            artifact, M.Char("researcher_v0/tasks/tasks.jsonl")
        )() is M.truth_value:
            self.result = M.truth_value
        elif M.Compare(
            artifact, M.Char("researcher_v0/journals/mining.jsonl")
        )() is M.truth_value:
            self.result = M.truth_value
        elif M.Compare(
            artifact,
            M.Char("researcher_v0/certificates/baseline_path_certificates.jsonl"),
        )() is M.truth_value:
            self.result = M.truth_value
        elif M.Compare(
            artifact, M.Char("researcher_v0/candidates/candidates.jsonl")
        )() is M.truth_value:
            self.result = M.truth_value
        elif M.Compare(
            artifact, M.Char("researcher_v0/candidates/proved_invariants.jsonl")
        )() is M.truth_value:
            self.result = M.truth_value
        elif M.Compare(
            artifact, M.Char("researcher_v0/candidates/refuted_candidates.jsonl")
        )() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.Compare(
                artifact, M.Char("researcher_v0/certificates/prune_events.jsonl")
            )()
        super().__init__(inputs=M.Pair(artifact, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SourcesUseDeliveredArtifacts(M.Edge):
    def __init__(self, edges):
        self.result = self._edges(edges)
        super().__init__(inputs=M.Pair(edges, M.EmptyList), results=self.result)

    def _sources(self, sources):
        if IsEmptyTerm(sources)() is M.truth_value:
            return M.truth_value
        if AllowedArtifact(
            DG.SourceArtifact(M.Head(sources)())()
        )() is M.false_value:
            return M.false_value
        return self._sources(M.Tail(sources)())

    def _edges(self, edges):
        if IsEmptyTerm(edges)() is M.truth_value:
            return M.truth_value
        if self._sources(DG.EdgeSources(M.Head(edges)())()) is M.false_value:
            return M.false_value
        return self._edges(M.Tail(edges)())

    def __call__(self):
        return self.result


class EdgeKindTopology(M.Edge):
    def __init__(self, graph, edge_kind, source_kind, target_kind):
        self.result = self._walk(
            DG.PartNodes(graph)(),
            DG.PartEdges(graph)(),
            edge_kind,
            source_kind,
            target_kind,
        )
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def _walk(self, nodes, edges, edge_kind, source_kind, target_kind):
        if IsEmptyTerm(edges)() is M.truth_value:
            return M.truth_value
        edge = M.Head(edges)()
        if M.Compare(DG.EdgeKind(edge)(), edge_kind)() is M.truth_value:
            source = FindNode(nodes, DG.EdgeSourceId(edge)())()
            target = FindNode(nodes, DG.EdgeTargetId(edge)())()
            if IsEmptyTerm(source)() is M.truth_value:
                return M.false_value
            if IsEmptyTerm(target)() is M.truth_value:
                return M.false_value
            if M.Compare(
                DG.NodeKind(M.Head(source)())(), source_kind
            )() is M.false_value:
                return M.false_value
            if M.Compare(
                DG.NodeKind(M.Head(target)())(), target_kind
            )() is M.false_value:
                return M.false_value
        return self._walk(
            nodes, M.Tail(edges)(), edge_kind, source_kind, target_kind
        )

    def __call__(self):
        return self.result


class EdgePatternCount(M.Edge):
    def __init__(self, graph, edge_kind, source_kind, target_kind):
        self.result = self._walk(
            DG.PartNodes(graph)(),
            DG.PartEdges(graph)(),
            edge_kind,
            source_kind,
            target_kind,
            D.PeanoZero()(),
        )
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def _walk(
        self, nodes, edges, edge_kind, source_kind, target_kind, count
    ):
        if IsEmptyTerm(edges)() is M.truth_value:
            return D.StructuralCount(count)()
        edge = M.Head(edges)()
        if M.Compare(DG.EdgeKind(edge)(), edge_kind)() is M.truth_value:
            source = FindNode(nodes, DG.EdgeSourceId(edge)())()
            target = FindNode(nodes, DG.EdgeTargetId(edge)())()
            if IsEmptyTerm(source)() is M.false_value:
                if IsEmptyTerm(target)() is M.false_value:
                    if M.Compare(
                        DG.NodeKind(M.Head(source)())(), source_kind
                    )() is M.truth_value:
                        if M.Compare(
                            DG.NodeKind(M.Head(target)())(), target_kind
                        )() is M.truth_value:
                            count = D.PeanoSucc(count)()
        return self._walk(
            nodes,
            M.Tail(edges)(),
            edge_kind,
            source_kind,
            target_kind,
            count,
        )

    def __call__(self):
        return self.result


class AttemptOutcomeTopology(M.Edge):
    def __init__(self, graph):
        count = EdgePatternCount(
            graph, M.Char("produced"), M.Char("Attempt"), M.Char("Outcome")
        )()
        self.result = X.ReportingCountEquals(count, 34)()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BrokenTransitionTopology(M.Edge):
    def __init__(self, graph):
        if EdgeKindTopology(
            graph,
            M.Char("broke"),
            M.Char("Transition"),
            M.Char("CandidateInvariant"),
        )() is M.false_value:
            self.result = M.false_value
        else:
            count = EdgePatternCount(
                graph,
                M.Char("produced"),
                M.Char("Transition"),
                M.Char("BrokenOn"),
            )()
            self.result = X.ReportingCountEquals(count, 5)()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalAndProofTopology(M.Edge):
    def __init__(self, graph):
        if EdgeKindTopology(
            graph,
            M.Char("proposed_from"),
            M.Char("CandidateInvariant"),
            M.Char("Attempt"),
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = EdgeKindTopology(
                graph,
                M.Char("proved_by"),
                M.Char("CandidateInvariant"),
                M.Char("Certificate"),
            )()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PruneUseTopology(M.Edge):
    def __init__(self, graph):
        invariant_uses = EdgePatternCount(
            graph,
            M.Char("used_by"),
            M.Char("Certificate"),
            M.Char("PruneEvent"),
        )()
        task_uses = EdgePatternCount(
            graph, M.Char("used_by"), M.Char("Certificate"), M.Char("Task")
        )()
        endpoint_proofs = EdgePatternCount(
            graph,
            M.Char("produced"),
            M.Char("PruneEvent"),
            M.Char("Certificate"),
        )()
        if X.ReportingCountEquals(invariant_uses, 8)() is M.false_value:
            self.result = M.false_value
        elif X.ReportingCountEquals(task_uses, 8)() is M.false_value:
            self.result = M.false_value
        else:
            self.result = X.ReportingCountEquals(endpoint_proofs, 8)()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ScopeMismatchTopology(M.Edge):
    def __init__(self, graph):
        self.result = EdgeKindTopology(
            graph,
            M.Char("invalidated_by"),
            M.Char("Certificate"),
            M.Char("ScopeMismatch"),
        )()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SourceArtifactsBound(M.Edge):
    def __init__(self, kept, mining_run, use_run, here):
        if M.Compare(
            M.Char(G.RowsToJsonl(kept)()),
            M.Char(FileText(os.path.join(here, "tasks", "tasks.jsonl"))()),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Char(FileText(os.path.join(here, "journals", "mining.jsonl"))()),
            M.Char(""),
        )() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(
            M.Char(L.CertificatesText(X.RunAttempts(mining_run)())()),
            M.Char(
                FileText(
                    os.path.join(
                        here,
                        "certificates",
                        "baseline_path_certificates.jsonl",
                    )
                )()
            ),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Char(X.CandidatesText(X.RunCandidates(mining_run)())()),
            M.Char(
                FileText(os.path.join(here, "candidates", "candidates.jsonl"))()
            ),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Char(X.ProvedText(X.RunProved(mining_run)())()),
            M.Char(
                FileText(
                    os.path.join(here, "candidates", "proved_invariants.jsonl")
                )()
            ),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Char(X.RefutedText(X.RunRefuted(mining_run)())()),
            M.Char(
                FileText(
                    os.path.join(here, "candidates", "refuted_candidates.jsonl")
                )()
            ),
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.Compare(
                M.Char(U.PruneEventsText(U.RunEvents(use_run)())()),
                M.Char(
                    FileText(
                        os.path.join(here, "certificates", "prune_events.jsonl")
                    )()
                ),
            )()
        super().__init__(inputs=M.Pair(kept, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphArtifactsReproduce(M.Edge):
    def __init__(self, graph, here):
        if M.Compare(
            M.Char(DG.DiscoveryGraphJson(graph)()),
            M.Char(FileText(os.path.join(here, "discovery_graph.json"))()),
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.Compare(
                M.Char(DG.DiscoveryGraphSummary(graph)()),
                M.Char(
                    FileText(os.path.join(here, "discovery_graph_summary.md"))()
                ),
            )()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class G6Tests(M.Edge):
    def __init__(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kept = M.Head(G.DropExactDuplicates(G.GenerateAllRows()())())()
        representatives = L.CanonicalRepresentatives(kept)()
        mining_run = X.MiningRun(
            representatives, L.EXPANSION_BUDGET, L.WALL_CLOCK_BUDGET_MS
        )()
        use_run = U.InRunUse(
            representatives, L.EXPANSION_BUDGET, L.WALL_CLOCK_BUDGET_MS
        )()
        graph = DG.DiscoveryGraph(kept, mining_run, use_run)()
        nodes = DG.PartNodes(graph)()
        edges = DG.PartEdges(graph)()
        built = M.EmptyList
        built = ChainAppend(
            built,
            M.Pair(M.Char("graph node and edge totals are exact"), ExactGraphCounts(graph)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("all nine required node kinds have exact counts"), ExactNodeKinds(graph)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("all eight required edge kinds have exact counts"), ExactEdgeKinds(graph)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("node ids are unique"), UniqueNodeIds(nodes)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("edge ids are unique"), UniqueEdgeIds(edges)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("every edge endpoint resolves"), AllEndpointsResolve(nodes, edges)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("every edge has complete source artifact ids"), SourceRefsComplete(edges)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("edge sources name only delivered artifacts"), SourcesUseDeliveredArtifacts(edges)),
        )()
        built = ChainAppend(
            built,
            M.Pair(
                M.Char("generated_from links child tasks to parent tasks"),
                EdgeKindTopology(
                    graph,
                    M.Char("generated_from"),
                    M.Char("Task"),
                    M.Char("Task"),
                ),
            ),
        )()
        built = ChainAppend(
            built,
            M.Pair(
                M.Char("attempted links tasks to attempts"),
                EdgeKindTopology(
                    graph,
                    M.Char("attempted"),
                    M.Char("Task"),
                    M.Char("Attempt"),
                ),
            ),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("attempts produce all journal outcomes"), AttemptOutcomeTopology(graph)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("transitions break proposals with retained BrokenOn"), BrokenTransitionTopology(graph)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("proposals and checker proofs are linked"), ProposalAndProofTopology(graph)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("certificates and prune events link later tasks"), PruneUseTopology(graph)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("ruleset changes invalidate old certificates"), ScopeMismatchTopology(graph)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("cited artifacts are present and deterministic sources rebind"), SourceArtifactsBound(kept, mining_run, use_run, here)),
        )()
        built = ChainAppend(
            built,
            M.Pair(M.Char("graph and summary artifacts reproduce byte exact"), GraphArtifactsReproduce(graph, here)),
        )()
        self.result = built
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result
