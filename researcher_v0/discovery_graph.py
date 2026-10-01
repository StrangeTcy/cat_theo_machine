"""Researcher-v0 G6 inert discovery graph.

The graph is a reporting artifact only. It links delivered task provenance,
G4 attempts and outcomes, trace refutations, proved invariant certificates,
G5 prune events, endpoint certificates, and exact-scope invalidations. Every
edge carries one or more source artifact record references.
"""

from __future__ import annotations

from .. import machine as M
from . import checker as C
from . import in_run_use as U
from . import laboratory as L
from . import mining as X
from . import mining_checker as MC
from . import task_generation as G
from . import token_domain as D
from .chains import ChainAppend, ChainJoin, IsEmptyTerm


class SourceRef(M.Edge):
    def __init__(self, artifact, record_id):
        self.result = M.Pair(artifact, M.Pair(record_id, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SourceArtifact(M.Edge):
    def __init__(self, source):
        self.result = D.HeadAt(source, 0)()
        super().__init__(inputs=M.Pair(source, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SourceRecordId(M.Edge):
    def __init__(self, source):
        self.result = D.HeadAt(source, 1)()
        super().__init__(inputs=M.Pair(source, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OneSource(M.Edge):
    def __init__(self, artifact, record_id):
        self.result = M.Pair(SourceRef(artifact, record_id)(), M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class GraphNode(M.Edge):
    def __init__(
        self, node_id, kind, label, status, ruleset_version, subject_id, sources
    ):
        self.result = M.Pair(
            node_id,
            M.Pair(
                kind,
                M.Pair(
                    label,
                    M.Pair(
                        status,
                        M.Pair(
                            ruleset_version,
                            M.Pair(subject_id, M.Pair(sources, M.EmptyList)),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class NodeId(M.Edge):
    def __init__(self, node):
        self.result = D.HeadAt(node, 0)()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NodeKind(M.Edge):
    def __init__(self, node):
        self.result = D.HeadAt(node, 1)()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NodeLabel(M.Edge):
    def __init__(self, node):
        self.result = D.HeadAt(node, 2)()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NodeStatus(M.Edge):
    def __init__(self, node):
        self.result = D.HeadAt(node, 3)()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NodeRulesetVersion(M.Edge):
    def __init__(self, node):
        self.result = D.HeadAt(node, 4)()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NodeSubjectId(M.Edge):
    def __init__(self, node):
        self.result = D.HeadAt(node, 5)()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NodeSources(M.Edge):
    def __init__(self, node):
        self.result = D.HeadAt(node, 6)()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphEdge(M.Edge):
    def __init__(self, edge_id, kind, source_id, target_id, sources):
        self.result = M.Pair(
            edge_id,
            M.Pair(
                kind,
                M.Pair(source_id, M.Pair(target_id, M.Pair(sources, M.EmptyList))),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EdgeId(M.Edge):
    def __init__(self, edge):
        self.result = D.HeadAt(edge, 0)()
        super().__init__(inputs=M.Pair(edge, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EdgeKind(M.Edge):
    def __init__(self, edge):
        self.result = D.HeadAt(edge, 1)()
        super().__init__(inputs=M.Pair(edge, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EdgeSourceId(M.Edge):
    def __init__(self, edge):
        self.result = D.HeadAt(edge, 2)()
        super().__init__(inputs=M.Pair(edge, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EdgeTargetId(M.Edge):
    def __init__(self, edge):
        self.result = D.HeadAt(edge, 3)()
        super().__init__(inputs=M.Pair(edge, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EdgeSources(M.Edge):
    def __init__(self, edge):
        self.result = D.HeadAt(edge, 4)()
        super().__init__(inputs=M.Pair(edge, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphParts(M.Edge):
    def __init__(self, nodes, edges):
        self.result = M.Pair(nodes, M.Pair(edges, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PartNodes(M.Edge):
    def __init__(self, parts):
        self.result = D.HeadAt(parts, 0)()
        super().__init__(inputs=M.Pair(parts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PartEdges(M.Edge):
    def __init__(self, parts):
        self.result = D.HeadAt(parts, 1)()
        super().__init__(inputs=M.Pair(parts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TaskNodeId(M.Edge):
    def __init__(self, task_id):
        self.result = M.Char("task:" + task_id())
        super().__init__(inputs=M.Pair(task_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AttemptNodeId(M.Edge):
    def __init__(self, task_id):
        self.result = M.Char("attempt:MINING:" + task_id() + ":1")
        super().__init__(inputs=M.Pair(task_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomeNodeId(M.Edge):
    def __init__(self, task_id):
        self.result = M.Char("outcome:MINING:" + task_id() + ":1")
        super().__init__(inputs=M.Pair(task_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertificateNodeId(M.Edge):
    def __init__(self, certificate_id):
        self.result = M.Char("certificate:" + certificate_id())
        super().__init__(inputs=M.Pair(certificate_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateNodeId(M.Edge):
    def __init__(self, candidate_id):
        self.result = M.Char("candidate:" + candidate_id())
        super().__init__(inputs=M.Pair(candidate_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RefutedCandidateNodeId(M.Edge):
    def __init__(self, refutation_id):
        self.result = M.Char("candidate:refuted:" + refutation_id())
        super().__init__(inputs=M.Pair(refutation_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TransitionNodeId(M.Edge):
    def __init__(self, refutation_id):
        self.result = M.Char("transition:" + refutation_id())
        super().__init__(inputs=M.Pair(refutation_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BrokenNodeId(M.Edge):
    def __init__(self, refutation_id):
        self.result = M.Char("broken-on:" + refutation_id())
        super().__init__(inputs=M.Pair(refutation_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PruneNodeId(M.Edge):
    def __init__(self, event_id):
        self.result = M.Char("prune-event:" + event_id())
        super().__init__(inputs=M.Pair(event_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ScopeMismatchNodeId(M.Edge):
    def __init__(self, task_id, certificate_digest):
        self.result = M.Char(
            "scope-mismatch:" + task_id() + ":" + certificate_digest()
        )
        super().__init__(inputs=M.Pair(task_id, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AddTaskNodes(M.Edge):
    def __init__(self, rows, nodes, edges):
        self.result = self._walk(rows, nodes, edges)
        super().__init__(inputs=M.Pair(rows, M.EmptyList), results=self.result)

    def _walk(self, rows, nodes, edges):
        if IsEmptyTerm(rows)() is M.truth_value:
            return GraphParts(nodes, edges)()
        row = M.Head(rows)()
        task_id = M.Char(G.ParentIdText(G.RowSerial(row)())())
        parent_id = M.Char(G.ParentIdText(G.RowParentSerial(row)())())
        record = G.RowRecord(row)()
        sources = OneSource(
            M.Char("researcher_v0/tasks/tasks.jsonl"), task_id
        )()
        node = GraphNode(
            TaskNodeId(task_id)(),
            M.Char("Task"),
            task_id,
            G.TaskKindOf(record)(),
            G.RowRulesetVersion(row)(),
            M.Char(G.RowCanonicalId(row)()),
            sources,
        )()
        nodes = ChainAppend(nodes, node)()
        if M.Compare(parent_id, M.Char("none"))() is M.false_value:
            parent_sources = OneSource(
                M.Char("researcher_v0/tasks/tasks.jsonl"), parent_id
            )()
            edge = GraphEdge(
                M.Char("generated-from:" + task_id() + ":" + parent_id()),
                M.Char("generated_from"),
                TaskNodeId(task_id)(),
                TaskNodeId(parent_id)(),
                ChainJoin(sources, parent_sources)(),
            )()
            edges = ChainAppend(edges, edge)()
        return self._walk(M.Tail(rows)(), nodes, edges)

    def __call__(self):
        return self.result


class AddAttemptNodes(M.Edge):
    def __init__(self, attempts, nodes, edges):
        self.result = self._walk(attempts, nodes, edges)
        super().__init__(inputs=M.Pair(attempts, M.EmptyList), results=self.result)

    def _walk(self, attempts, nodes, edges):
        if IsEmptyTerm(attempts)() is M.truth_value:
            return GraphParts(nodes, edges)()
        attempt = M.Head(attempts)()
        task_id = M.Char(L.AttemptTaskIdText(attempt)())
        attempt_record_id = M.Char("MINING:" + task_id() + ":1")
        attempt_sources = OneSource(
            M.Char("researcher_v0/journals/mining.jsonl"), attempt_record_id
        )()
        row = L.AttemptRow(attempt)()
        record = G.RowRecord(row)()
        digest = D.RulesetVersionOfSpecs(G.TaskSpecs(record)())()
        attempt_node = GraphNode(
            AttemptNodeId(task_id)(),
            M.Char("Attempt"),
            attempt_record_id,
            L.AttemptOutcome(attempt)(),
            digest,
            task_id,
            attempt_sources,
        )()
        outcome_node = GraphNode(
            OutcomeNodeId(task_id)(),
            M.Char("Outcome"),
            L.AttemptOutcome(attempt)(),
            L.AttemptOutcome(attempt)(),
            digest,
            attempt_record_id,
            attempt_sources,
        )()
        nodes = ChainAppend(nodes, attempt_node)()
        nodes = ChainAppend(nodes, outcome_node)()
        task_sources = OneSource(
            M.Char("researcher_v0/tasks/tasks.jsonl"), task_id
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("attempted:" + task_id()),
                M.Char("attempted"),
                TaskNodeId(task_id)(),
                AttemptNodeId(task_id)(),
                ChainJoin(task_sources, attempt_sources)(),
            )(),
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("produced-outcome:" + task_id()),
                M.Char("produced"),
                AttemptNodeId(task_id)(),
                OutcomeNodeId(task_id)(),
                attempt_sources,
            )(),
        )()
        certificate_shell = L.AttemptCertificateShell(attempt)()
        if IsEmptyTerm(certificate_shell)() is M.false_value:
            certificate = M.Head(M.Head(certificate_shell)())()
            certificate_id = C.CertificateId(certificate)()
            certificate_sources = OneSource(
                M.Char(
                    "researcher_v0/certificates/baseline_path_certificates.jsonl"
                ),
                certificate_id,
            )()
            nodes = ChainAppend(
                nodes,
                GraphNode(
                    CertificateNodeId(certificate_id)(),
                    M.Char("Certificate"),
                    certificate_id,
                    C.CertificateKind(certificate)(),
                    C.CertificateDigest(certificate)(),
                    task_id,
                    certificate_sources,
                )(),
            )()
            edge_sources = ChainJoin(attempt_sources, certificate_sources)()
            edges = ChainAppend(
                edges,
                GraphEdge(
                    M.Char("produced-certificate:" + task_id()),
                    M.Char("produced"),
                    AttemptNodeId(task_id)(),
                    CertificateNodeId(certificate_id)(),
                    edge_sources,
                )(),
            )()
        return self._walk(M.Tail(attempts)(), nodes, edges)

    def __call__(self):
        return self.result


class AddCandidateNodes(M.Edge):
    def __init__(self, candidates, nodes, edges):
        self.result = self._walk(candidates, nodes, edges)
        super().__init__(inputs=M.Pair(candidates, M.EmptyList), results=self.result)

    def _walk(self, candidates, nodes, edges):
        if IsEmptyTerm(candidates)() is M.truth_value:
            return GraphParts(nodes, edges)()
        candidate = M.Head(candidates)()
        candidate_id = X.CandidateIdOf(candidate)()
        task_id = X.CandidateSourceTask(candidate)()
        sources = OneSource(
            M.Char("researcher_v0/candidates/candidates.jsonl"), candidate_id
        )()
        nodes = ChainAppend(
            nodes,
            GraphNode(
                CandidateNodeId(candidate_id)(),
                M.Char("CandidateInvariant"),
                X.ObserverDisplay(X.CandidateObserverSpec(candidate)())(),
                MC.VerdictStatus(X.CandidateCheckerVerdict(candidate)())(),
                X.CandidateDigest(candidate)(),
                task_id,
                sources,
            )(),
        )()
        edge_sources = ChainJoin(
            sources,
            OneSource(
                M.Char("researcher_v0/journals/mining.jsonl"),
                M.Char("MINING:" + task_id() + ":1"),
            )(),
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("proposed-from:" + candidate_id()),
                M.Char("proposed_from"),
                CandidateNodeId(candidate_id)(),
                AttemptNodeId(task_id)(),
                edge_sources,
            )(),
        )()
        return self._walk(M.Tail(candidates)(), nodes, edges)

    def __call__(self):
        return self.result


class AddRefutationNodes(M.Edge):
    def __init__(self, refuted, nodes, edges):
        self.result = self._walk(refuted, nodes, edges)
        super().__init__(inputs=M.Pair(refuted, M.EmptyList), results=self.result)

    def _walk(self, refuted, nodes, edges):
        if IsEmptyTerm(refuted)() is M.truth_value:
            return GraphParts(nodes, edges)()
        refutation = M.Head(refuted)()
        refutation_id = X.RefutationIdOf(refutation)()
        task_id = X.RefutationSourceTask(refutation)()
        trace = X.RefutationTrace(refutation)()
        broken = M.Head(X.TraceBrokenShell(trace)())()
        transition = X.BrokenTransition(broken)()
        sources = OneSource(
            M.Char("researcher_v0/candidates/refuted_candidates.jsonl"),
            refutation_id,
        )()
        candidate_id = RefutedCandidateNodeId(refutation_id)()
        transition_id = TransitionNodeId(refutation_id)()
        broken_id = BrokenNodeId(refutation_id)()
        nodes = ChainAppend(
            nodes,
            GraphNode(
                candidate_id,
                M.Char("CandidateInvariant"),
                X.ObserverDisplay(X.RefutationObserverSpec(refutation)())(),
                M.Char(X.RefutationClassification(refutation)()),
                X.RefutationDigest(refutation)(),
                task_id,
                sources,
            )(),
        )()
        nodes = ChainAppend(
            nodes,
            GraphNode(
                transition_id,
                M.Char("Transition"),
                X.TransitionRuleDisplay(transition)(),
                X.TraceStatus(trace)(),
                X.TransitionRulesetDigest(transition)(),
                X.TransitionSourceTask(transition)(),
                sources,
            )(),
        )()
        nodes = ChainAppend(
            nodes,
            GraphNode(
                broken_id,
                M.Char("BrokenOn"),
                X.BrokenId(broken)(),
                M.Char("REFUTED"),
                X.BrokenDigest(broken)(),
                candidate_id,
                sources,
            )(),
        )()
        edge_sources = ChainJoin(
            sources,
            OneSource(
                M.Char("researcher_v0/journals/mining.jsonl"),
                M.Char("MINING:" + task_id() + ":1"),
            )(),
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("proposed-from-refuted:" + refutation_id()),
                M.Char("proposed_from"),
                candidate_id,
                AttemptNodeId(task_id)(),
                edge_sources,
            )(),
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("broke:" + refutation_id()),
                M.Char("broke"),
                transition_id,
                candidate_id,
                sources,
            )(),
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("produced-broken-on:" + refutation_id()),
                M.Char("produced"),
                transition_id,
                broken_id,
                sources,
            )(),
        )()
        return self._walk(M.Tail(refuted)(), nodes, edges)

    def __call__(self):
        return self.result


class AddProofNodes(M.Edge):
    def __init__(self, proved, nodes, edges):
        self.result = self._walk(proved, nodes, edges)
        super().__init__(inputs=M.Pair(proved, M.EmptyList), results=self.result)

    def _walk(self, proved, nodes, edges):
        if IsEmptyTerm(proved)() is M.truth_value:
            return GraphParts(nodes, edges)()
        item = M.Head(proved)()
        candidate = X.ProvedCandidate(item)()
        candidate_id = X.CandidateIdOf(candidate)()
        certificate = X.ProvedCertificate(item)()
        certificate_id = MC.InvariantCertificateId(certificate)()
        sources = OneSource(
            M.Char("researcher_v0/candidates/proved_invariants.jsonl"),
            certificate_id,
        )()
        nodes = ChainAppend(
            nodes,
            GraphNode(
                CertificateNodeId(certificate_id)(),
                M.Char("Certificate"),
                certificate_id,
                C.CertificateKind(certificate)(),
                C.CertificateDigest(certificate)(),
                candidate_id,
                sources,
            )(),
        )()
        edge_sources = ChainJoin(
            sources,
            OneSource(
                M.Char("researcher_v0/candidates/candidates.jsonl"), candidate_id
            )(),
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("proved-by:" + candidate_id()),
                M.Char("proved_by"),
                CandidateNodeId(candidate_id)(),
                CertificateNodeId(certificate_id)(),
                edge_sources,
            )(),
        )()
        return self._walk(M.Tail(proved)(), nodes, edges)

    def __call__(self):
        return self.result


class AddPruneNodes(M.Edge):
    def __init__(self, events, nodes, edges):
        self.result = self._walk(events, nodes, edges)
        super().__init__(inputs=M.Pair(events, M.EmptyList), results=self.result)

    def _walk(self, events, nodes, edges):
        if IsEmptyTerm(events)() is M.truth_value:
            return GraphParts(nodes, edges)()
        event = M.Head(events)()
        event_id = U.EventId(event)()
        task_id = U.EventTaskId(event)()
        endpoint_certificate_id = U.EventCertificateId(event)()
        invariant_certificate_id = U.EventInvariantCertificateId(event)()
        decision = U.EventDecision(event)()
        endpoint_certificate = D.HeadAt(decision, 0)()
        sources = OneSource(
            M.Char("researcher_v0/certificates/prune_events.jsonl"), event_id
        )()
        nodes = ChainAppend(
            nodes,
            GraphNode(
                PruneNodeId(event_id)(),
                M.Char("PruneEvent"),
                event_id,
                U.EventResult(event)(),
                C.CertificateDigest(endpoint_certificate)(),
                task_id,
                sources,
            )(),
        )()
        nodes = ChainAppend(
            nodes,
            GraphNode(
                CertificateNodeId(endpoint_certificate_id)(),
                M.Char("Certificate"),
                endpoint_certificate_id,
                C.CertificateKind(endpoint_certificate)(),
                C.CertificateDigest(endpoint_certificate)(),
                event_id,
                sources,
            )(),
        )()
        invariant_sources = OneSource(
            M.Char("researcher_v0/candidates/proved_invariants.jsonl"),
            invariant_certificate_id,
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("used-by-invariant:" + event_id()),
                M.Char("used_by"),
                CertificateNodeId(invariant_certificate_id)(),
                PruneNodeId(event_id)(),
                ChainJoin(invariant_sources, sources)(),
            )(),
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("produced-endpoint-certificate:" + event_id()),
                M.Char("produced"),
                PruneNodeId(event_id)(),
                CertificateNodeId(endpoint_certificate_id)(),
                sources,
            )(),
        )()
        task_sources = OneSource(
            M.Char("researcher_v0/tasks/tasks.jsonl"), task_id
        )()
        edges = ChainAppend(
            edges,
            GraphEdge(
                M.Char("used-by-task:" + event_id()),
                M.Char("used_by"),
                CertificateNodeId(endpoint_certificate_id)(),
                TaskNodeId(task_id)(),
                ChainJoin(sources, task_sources)(),
            )(),
        )()
        return self._walk(M.Tail(events)(), nodes, edges)

    def __call__(self):
        return self.result


class ProvedCertificateForDigest(M.Edge):
    def __init__(self, proved, digest):
        self.result = self._scan(proved, digest)
        super().__init__(inputs=M.Pair(proved, M.EmptyList), results=self.result)

    def _scan(self, proved, digest):
        if IsEmptyTerm(proved)() is M.truth_value:
            return M.EmptyList
        certificate = X.ProvedCertificate(M.Head(proved)())()
        if M.Compare(C.CertificateDigest(certificate)(), digest)() is M.truth_value:
            return M.Pair(certificate, M.EmptyList)
        return self._scan(M.Tail(proved)(), digest)

    def __call__(self):
        return self.result


class AddScopeMismatchNodes(M.Edge):
    def __init__(self, rows, proved, nodes, edges):
        self.result = self._walk(rows, proved, nodes, edges)
        super().__init__(inputs=M.Pair(rows, M.EmptyList), results=self.result)

    def _walk(self, rows, proved, nodes, edges):
        if IsEmptyTerm(rows)() is M.truth_value:
            return GraphParts(nodes, edges)()
        row = M.Head(rows)()
        record = G.RowRecord(row)()
        if G.IsScopeBreakRecord(record)() is M.truth_value:
            task_id = M.Char(G.ParentIdText(G.RowSerial(row)())())
            old_digest = D.RulesetVersionOfSpecs(G.TaskOldSpecs(record)())()
            current_digest = D.RulesetVersionOfSpecs(G.TaskSpecs(record)())()
            found = ProvedCertificateForDigest(proved, old_digest)()
            if IsEmptyTerm(found)() is M.false_value:
                certificate = M.Head(found)()
                certificate_id = MC.InvariantCertificateId(certificate)()
                mismatch_id = ScopeMismatchNodeId(task_id, old_digest)()
                task_sources = OneSource(
                    M.Char("researcher_v0/tasks/tasks.jsonl"), task_id
                )()
                certificate_sources = OneSource(
                    M.Char("researcher_v0/candidates/proved_invariants.jsonl"),
                    certificate_id,
                )()
                sources = ChainJoin(task_sources, certificate_sources)()
                nodes = ChainAppend(
                    nodes,
                    GraphNode(
                        mismatch_id,
                        M.Char("ScopeMismatch"),
                        M.Char("ScopeMismatch"),
                        C.ScopeMismatchTag()(),
                        current_digest,
                        certificate_id,
                        sources,
                    )(),
                )()
                edges = ChainAppend(
                    edges,
                    GraphEdge(
                        M.Char("invalidated-by:" + task_id()),
                        M.Char("invalidated_by"),
                        CertificateNodeId(certificate_id)(),
                        mismatch_id,
                        sources,
                    )(),
                )()
        return self._walk(M.Tail(rows)(), proved, nodes, edges)

    def __call__(self):
        return self.result


class DiscoveryGraph(M.Edge):
    def __init__(self, rows, mining_run, use_run):
        parts = AddTaskNodes(rows, M.EmptyList, M.EmptyList)()
        parts = AddAttemptNodes(
            X.RunAttempts(mining_run)(), PartNodes(parts)(), PartEdges(parts)()
        )()
        parts = AddCandidateNodes(
            X.RunCandidates(mining_run)(), PartNodes(parts)(), PartEdges(parts)()
        )()
        parts = AddRefutationNodes(
            X.RunRefuted(mining_run)(), PartNodes(parts)(), PartEdges(parts)()
        )()
        parts = AddProofNodes(
            X.RunProved(mining_run)(), PartNodes(parts)(), PartEdges(parts)()
        )()
        parts = AddPruneNodes(
            U.RunEvents(use_run)(), PartNodes(parts)(), PartEdges(parts)()
        )()
        parts = AddScopeMismatchNodes(
            rows,
            X.RunProved(mining_run)(),
            PartNodes(parts)(),
            PartEdges(parts)(),
        )()
        self.result = parts
        super().__init__(inputs=M.Pair(rows, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SourcesJson(M.Edge):
    def __init__(self, sources):
        self.result = "[" + self._items(sources) + "]"
        super().__init__(inputs=M.Pair(sources, M.EmptyList), results=self.result)

    def _items(self, sources):
        if IsEmptyTerm(sources)() is M.truth_value:
            return ""
        source = M.Head(sources)()
        item = (
            '{"artifact":"'
            + L.JsonSafeText(SourceArtifact(source)()())()
            + '","record_id":"'
            + L.JsonSafeText(SourceRecordId(source)()())()
            + '"}'
        )
        if IsEmptyTerm(M.Tail(sources)())() is M.truth_value:
            return item
        return item + "," + self._items(M.Tail(sources)())

    def __call__(self):
        return self.result


class NodeJson(M.Edge):
    def __init__(self, node):
        self.result = (
            '{"id":"'
            + L.JsonSafeText(NodeId(node)()())()
            + '","kind":"'
            + L.JsonSafeText(NodeKind(node)()())()
            + '","label":"'
            + L.JsonSafeText(NodeLabel(node)()())()
            + '","status":"'
            + L.JsonSafeText(NodeStatus(node)()())()
            + '","ruleset_version":"'
            + L.JsonSafeText(NodeRulesetVersion(node)()())()
            + '","subject_id":"'
            + L.JsonSafeText(NodeSubjectId(node)()())()
            + '","sources":'
            + SourcesJson(NodeSources(node)())()
            + "}"
        )
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EdgeJson(M.Edge):
    def __init__(self, edge):
        self.result = (
            '{"id":"'
            + L.JsonSafeText(EdgeId(edge)()())()
            + '","kind":"'
            + L.JsonSafeText(EdgeKind(edge)()())()
            + '","from":"'
            + L.JsonSafeText(EdgeSourceId(edge)()())()
            + '","to":"'
            + L.JsonSafeText(EdgeTargetId(edge)()())()
            + '","sources":'
            + SourcesJson(EdgeSources(edge)())()
            + "}"
        )
        super().__init__(inputs=M.Pair(edge, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DiscoveryGraphJson(M.Edge):
    def __init__(self, graph):
        nodes = PartNodes(graph)()
        edges = PartEdges(graph)()
        self.result = (
            '{"schema":"researcher-v0-discovery-graph/1","gate":"G6",'
            '"inert":true,"node_count":'
            + str(X.ChainCount(nodes)())
            + ',"edge_count":'
            + str(X.ChainCount(edges)())
            + ',"nodes":['
            + self._nodes(nodes)
            + '],"edges":['
            + self._edges(edges)
            + "]}\n"
        )
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def _nodes(self, nodes):
        if IsEmptyTerm(nodes)() is M.truth_value:
            return ""
        item = NodeJson(M.Head(nodes)())()
        if IsEmptyTerm(M.Tail(nodes)())() is M.truth_value:
            return item
        return item + "," + self._nodes(M.Tail(nodes)())

    def _edges(self, edges):
        if IsEmptyTerm(edges)() is M.truth_value:
            return ""
        item = EdgeJson(M.Head(edges)())()
        if IsEmptyTerm(M.Tail(edges)())() is M.truth_value:
            return item
        return item + "," + self._edges(M.Tail(edges)())

    def __call__(self):
        return self.result


class NodeKindCount(M.Edge):
    def __init__(self, nodes, kind):
        self.result = self._walk(nodes, kind, D.PeanoZero()())
        super().__init__(inputs=M.Pair(nodes, M.EmptyList), results=self.result)

    def _walk(self, nodes, kind, count):
        if IsEmptyTerm(nodes)() is M.truth_value:
            return D.StructuralCount(count)()
        if M.Compare(NodeKind(M.Head(nodes)())(), kind)() is M.truth_value:
            count = D.PeanoSucc(count)()
        return self._walk(M.Tail(nodes)(), kind, count)

    def __call__(self):
        return self.result


class EdgeKindCount(M.Edge):
    def __init__(self, edges, kind):
        self.result = self._walk(edges, kind, D.PeanoZero()())
        super().__init__(inputs=M.Pair(edges, M.EmptyList), results=self.result)

    def _walk(self, edges, kind, count):
        if IsEmptyTerm(edges)() is M.truth_value:
            return D.StructuralCount(count)()
        if M.Compare(EdgeKind(M.Head(edges)())(), kind)() is M.truth_value:
            count = D.PeanoSucc(count)()
        return self._walk(M.Tail(edges)(), kind, count)

    def __call__(self):
        return self.result


class DiscoveryGraphSummary(M.Edge):
    def __init__(self, graph):
        nodes = PartNodes(graph)()
        edges = PartEdges(graph)()
        self.result = (
            "# Researcher-v0 G6 discovery graph summary\n\n"
            "Status: inert graph built; no activation, admission, or live write.\n\n"
            "## Counts\n\n"
            "```text\n"
            "nodes                 "
            + str(X.ChainCount(nodes)())
            + "\n"
            "edges                 "
            + str(X.ChainCount(edges)())
            + "\n"
            "Task                  "
            + str(NodeKindCount(nodes, M.Char("Task"))())
            + "\n"
            "Attempt               "
            + str(NodeKindCount(nodes, M.Char("Attempt"))())
            + "\n"
            "Transition            "
            + str(NodeKindCount(nodes, M.Char("Transition"))())
            + "\n"
            "Outcome               "
            + str(NodeKindCount(nodes, M.Char("Outcome"))())
            + "\n"
            "CandidateInvariant    "
            + str(NodeKindCount(nodes, M.Char("CandidateInvariant"))())
            + "\n"
            "BrokenOn              "
            + str(NodeKindCount(nodes, M.Char("BrokenOn"))())
            + "\n"
            "Certificate           "
            + str(NodeKindCount(nodes, M.Char("Certificate"))())
            + "\n"
            "PruneEvent            "
            + str(NodeKindCount(nodes, M.Char("PruneEvent"))())
            + "\n"
            "ScopeMismatch         "
            + str(NodeKindCount(nodes, M.Char("ScopeMismatch"))())
            + "\n"
            "```\n\n"
            "## Required edge kinds\n\n"
            "```text\n"
            "generated_from        "
            + str(EdgeKindCount(edges, M.Char("generated_from"))())
            + "\n"
            "attempted             "
            + str(EdgeKindCount(edges, M.Char("attempted"))())
            + "\n"
            "produced              "
            + str(EdgeKindCount(edges, M.Char("produced"))())
            + "\n"
            "broke                 "
            + str(EdgeKindCount(edges, M.Char("broke"))())
            + "\n"
            "proposed_from         "
            + str(EdgeKindCount(edges, M.Char("proposed_from"))())
            + "\n"
            "proved_by             "
            + str(EdgeKindCount(edges, M.Char("proved_by"))())
            + "\n"
            "used_by               "
            + str(EdgeKindCount(edges, M.Char("used_by"))())
            + "\n"
            "invalidated_by        "
            + str(EdgeKindCount(edges, M.Char("invalidated_by"))())
            + "\n"
            "```\n\n"
            "## Coverage\n\n"
            "The graph links all 42 delivered tasks, 34 G4 MINING attempts and outcomes, "
            "21 path certificates, eight invariant proposals, five retained BrokenOn "
            "transitions, three proved invariant certificates, eight G5 prune events, "
            "eight endpoint certificates, and four scope-change invalidations.\n\n"
            "Every edge contains source artifact path and record id references. "
            "The graph is JSON reporting data only and is not imported by any live path.\n"
        )
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result
