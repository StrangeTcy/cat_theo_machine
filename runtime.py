from __future__ import annotations

import json
import os
import time
import traceback

"""Runtime bundle and boot paths for the active HYGE machine.

Cold start:
    fresh graph + packs
Warm start:
    restored snapshot only
"""

from . import core as Core
from . import context as Ctxmod
from . import machine as M
from . import constructors as C
from . import gmprep as Gmpmod
from . import heuristics as H
from . import labels as L
from . import logic as Logicmod
from .math import peano as Peanomod
from .math import arithmetic as Arithmod
from . import prettyprinting as Prettymod
from . import proof as Pmod
from . import planner as Plannermod
from . import search as Searchmod
from . import trees as T
from .graph import Hypergraph, Reverse, RunTests, TestResultsReport
from .packs import PackLoader, PackTreeMap
from .persistence import SnapshotCodec
from .proof import CollectRules, ExplainDerivation, Prove


class MachineRuntime:
    def __init__(self, graph, theorem_heuristic, rewrite_heuristic, loaded_packs=None):
        self.graph = graph
        self.theorem_heuristic = theorem_heuristic
        self.rewrite_heuristic = rewrite_heuristic
        self.loaded_packs = loaded_packs if loaded_packs is not None else ()
        self.snapshot_upgraded = M.false_value
        self._compiled_ordered_rules = None

    def ordered_rules(self):
        if self._compiled_ordered_rules is None:
            raw_rules = Reverse(M.FromContextGetRuleOrder(self.graph)())()
            self._compiled_ordered_rules = Pmod.CompileRuleChain(raw_rules, M.FromContextGetConstructors(self.graph)())()
        return self._compiled_ordered_rules

    def flat_rules(self):
        return CollectRules(M.FromContextGetAllRules(self.graph)())()

    def load_pack(self, path, namespace):
        namespace = _sync_live_namespace(namespace)
        loader = PackLoader(namespace)
        pack = loader.load_pack_file(path, self.graph)
        self.loaded_packs = self.loaded_packs + (pack,)
        self._compiled_ordered_rules = None
        return pack

    def save_snapshot(self, path, namespace):
        namespace = _sync_live_namespace(namespace)
        codec = SnapshotCodec(namespace)
        codec.save(self.graph, path)
        return path

    def run_tests(self):
        return RunTests(self.graph)()

    def run_tests_pretty(self):
        results = self.run_tests()
        return M.PrettyPair(results, M.FromContextGetConstructors(self.graph)())()

    def run_tests_report(self):
        self.run_tests()
        return TestResultsReport(self.graph)()

    def prove(self, start, goal, rules=None, heuristic=None, phi=None):
        if rules is None:
            rules = self.ordered_rules()
        else:
            rules = Pmod.CompileRuleChain(rules, M.FromContextGetConstructors(self.graph)())()
        if heuristic is None:
            heuristic = self.theorem_heuristic
        if phi is None:
            phi = M.EmptyList

        pair = Prove(
            self.graph,
            start,
            goal,
            rules,
            heuristic,
            M.FromContextGetConstructors(self.graph)(),
            phi,
        )()
        return M.Head(pair)()

    def evaluate(self, start, goal, rules=None, heuristic=None, step_budget=None):
        if rules is None:
            rules = self.ordered_rules()
        if heuristic is None:
            heuristic = self.theorem_heuristic
        if step_budget is None:
            step_budget = M.nine
        problem = Plannermod.PlannerProblem(start, goal, rules, heuristic)()
        state = Plannermod.PlannerState(problem, M.FromContextGetConstructors(self.graph)())()
        return Plannermod.PlannerRun(self.graph, state, step_budget)()

    def explain(self, derivation, goal):
        return ExplainDerivation(derivation, goal, M.FromContextGetConstructors(self.graph)())()

    def pack_summaries(self):
        return tuple(
            {
                "name": pack.name,
                "description": pack.description,
                "requires": tuple(pack.requires),
                "rule_count": len(pack.rule_map),
                "schema_count": len(pack.schema_map),
                "example_count": len(pack.examples),
            }
            for pack in self.loaded_packs
        )

    def _count_chain(self, chain):
        pair = M.Count(chain, M.FromContextGetConstructors(self.graph)())()
        n = M.Head(pair)()
        reg = M.Head(M.Tail(pair)())()
        return M.PrettyTerm(n, reg)()

    def summary(self):
        # Keep boot summaries responsive: counting rules via `M.Count(...)` can
        # be very slow on cold boots. When packs are available, use their
        # already-materialized metadata instead.
        if self.loaded_packs:
            rule_count = sum(len(pack.rule_map) for pack in self.loaded_packs)
            schema_count = sum(len(pack.schema_map) for pack in self.loaded_packs)
            example_count = sum(len(pack.examples) for pack in self.loaded_packs)
            return {
                "rule_count": rule_count,
                "schema_count": schema_count,
                "example_count": example_count,
                "loaded_packs": tuple(pack.name for pack in self.loaded_packs),
            }

        return {
            "rule_count": self._count_chain(self.ordered_rules()),
            "stored_rule_count": self._count_chain(self.flat_rules()),
            "loaded_packs": tuple(pack.name for pack in self.loaded_packs),
        }

    def _registry(self):
        return M.FromContextGetConstructors(self.graph)()

    def _pretty_term(self, term, registry=None):
        if registry is None:
            registry = self._registry()
        try:
            return M.PrettyTerm(term, registry)()
        except Exception:
            constructor = M.GetConstructor(term, registry)()
            if M.IdentityCompare(constructor, M.EmptyList)() is M.false_value:
                try:
                    return M.PrettyTerm(M.Head(constructor)(), registry)() + "(...)"
                except Exception:
                    return "<constructed-term>"
            return str(term)

    def _constructor_text(self, term, registry):
        constructor = M.GetConstructor(term, registry)()
        if M.IdentityCompare(constructor, M.EmptyList)() is M.truth_value:
            return ""
        return self._pretty_term(M.Head(constructor)(), registry)

    def _chain_items(self, chain):
        items = ()
        current = chain
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            items = items + (M.Head(current)(),)
            current = M.Tail(current)()
        return items

    def _reverse_chain(self, chain):
        acc = M.EmptyList
        current = chain
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            acc = M.Pair(M.Head(current)(), acc)
            current = M.Tail(current)()
        return acc

    def _tree_entries(self, tree):
        return T.TreeEntries(tree)()

    def _proof_cost_view(self, cost):
        return {
            "value": self._pretty_term(Pmod.ProofCostValue(cost)()),
            "steps": self._pretty_term(Pmod.ProofCostSteps(cost)()),
            "theorem_steps": self._pretty_term(Pmod.ProofCostTheoremSteps(cost)()),
            "rewrite_steps": self._pretty_term(Pmod.ProofCostRewriteSteps(cost)()),
        }

    def _search_cost_view(self, cost):
        return {
            "value": self._pretty_term(Searchmod.SearchCostValue(cost)()),
            "expanded": self._pretty_term(Searchmod.SearchCostExpanded(cost)()),
            "generated": self._pretty_term(Searchmod.SearchCostGenerated(cost)()),
            "frontier_peak": self._pretty_term(Searchmod.SearchCostFrontierPeak(cost)()),
            "found_depth": self._pretty_term(Searchmod.SearchCostFoundDepth(cost)()),
            "outcome": self._pretty_term(Searchmod.SearchCostOutcome(cost)()),
        }

    def _total_cost_view(self, cost):
        return {
            "value": self._pretty_term(Pmod.TotalCostValue(cost)()),
            "alpha": self._pretty_term(Pmod.TotalCostAlpha(cost)()),
            "beta": self._pretty_term(Pmod.TotalCostBeta(cost)()),
            "proof_value": self._pretty_term(Pmod.TotalCostProofValue(cost)()),
            "search_value": self._pretty_term(Pmod.TotalCostSearchValue(cost)()),
        }

    def _find_term_node_id(self, term, registry, term_refs):
        for known_term, known_id in term_refs:
            if M.CompareIn(known_term, term, registry)() is M.truth_value:
                return known_id
        raise KeyError("term not found")

    def _ensure_term_element(self, term, registry, term_refs, nodes):
        term_text = self._pretty_term(term, registry)
        try:
            known_id = self._find_term_node_id(term, registry, term_refs)
            return known_id, term_refs, nodes
        except KeyError:
            pass
        term_id = "term:" + str(len(term_refs) + 1)
        term_refs = term_refs + ((term, term_id),)
        nodes = nodes + (
            {
                "data": {
                    "id": term_id,
                    "label": term_text,
                    "kind": "term",
                    "constructor": self._constructor_text(term, registry),
                    "term": term_text,
                }
            },
        )
        return term_id, term_refs, nodes

    def cytoscape_view(self, max_rule_edges=None):
        registry = self._registry()
        term_refs = ()
        nodes = ()
        edges = ()
        graph_nodes = self._chain_items(self.graph.nodes)
        graph_edges = self._chain_items(self.graph.edges)
        rule_edges = self._chain_items(self.ordered_rules())
        visible_rule_edges = rule_edges if max_rule_edges is None else rule_edges[:max_rule_edges]

        for node in graph_nodes:
            _, term_refs, nodes = self._ensure_term_element(node, registry, term_refs, nodes)

        for edge_index, edge in enumerate(graph_edges, 1):
            hyperedge_id = "graph-edge:" + str(edge_index)
            edge_text = self._pretty_term(edge, registry)
            inputs = self._chain_items(M.EdgeInputs(edge)())
            results = self._chain_items(M.EdgeResults(edge)())
            nodes = nodes + (
                {
                    "data": {
                        "id": hyperedge_id,
                        "label": edge_text,
                        "kind": "graph_hyperedge",
                        "constructor": self._constructor_text(edge, registry),
                        "term": edge_text,
                    }
                },
            )
            for input_index, input_term in enumerate(inputs, 1):
                source_id, term_refs, nodes = self._ensure_term_element(input_term, registry, term_refs, nodes)
                edges = edges + (
                    {
                        "data": {
                            "id": "incidence:in:" + str(edge_index) + ":" + str(input_index),
                            "source": source_id,
                            "target": hyperedge_id,
                            "kind": "incidence_in",
                            "label": "input",
                        }
                    },
                )
            for result_index, result_term in enumerate(results, 1):
                target_id, term_refs, nodes = self._ensure_term_element(result_term, registry, term_refs, nodes)
                edges = edges + (
                    {
                        "data": {
                            "id": "incidence:out:" + str(edge_index) + ":" + str(result_index),
                            "source": hyperedge_id,
                            "target": target_id,
                            "kind": "incidence_out",
                            "label": "result",
                        }
                    },
                )

        for rule_index, rule in enumerate(visible_rule_edges, 1):
            hyperedge_id = "rule-edge:" + str(rule_index)
            rule_text = Pmod.PrettyRule(rule, registry)()
            inputs = self._chain_items(Pmod.RulePremises(rule)())
            results = (Pmod.RuleReplacement(rule)(),)
            nodes = nodes + (
                {
                    "data": {
                        "id": hyperedge_id,
                        "label": rule_text,
                        "kind": "rule_hyperedge",
                        "constructor": self._constructor_text(rule, registry),
                        "term": rule_text,
                    }
                },
            )
            for input_index, input_term in enumerate(inputs, 1):
                source_id, term_refs, nodes = self._ensure_term_element(input_term, registry, term_refs, nodes)
                edges = edges + (
                    {
                        "data": {
                            "id": "rule-incidence:in:" + str(rule_index) + ":" + str(input_index),
                            "source": source_id,
                            "target": hyperedge_id,
                            "kind": "rule_incidence_in",
                            "label": "premise",
                        }
                    },
                )
            for result_index, result_term in enumerate(results, 1):
                target_id, term_refs, nodes = self._ensure_term_element(result_term, registry, term_refs, nodes)
                edges = edges + (
                    {
                        "data": {
                            "id": "rule-incidence:out:" + str(rule_index) + ":" + str(result_index),
                            "source": hyperedge_id,
                            "target": target_id,
                            "kind": "rule_incidence_out",
                            "label": "result",
                        }
                    },
                )

        return {
            "elements": {
                "nodes": nodes,
                "edges": edges,
            },
            "counts": {
                "context_nodes": len(graph_nodes),
                "context_edges": len(graph_edges),
                "rule_edges": len(rule_edges),
                "visible_rule_edges": len(visible_rule_edges),
                "cy_nodes": len(nodes),
                "cy_edges": len(edges),
            },
        }

    def hypergraph_view(self, max_rule_edges=None):
        derivation_entries = self._tree_entries(self.graph.derivations)
        cytoscape = self.cytoscape_view(max_rule_edges=max_rule_edges)
        return {
            "kind": "hypergraph",
            "counts": {
                "nodes": len(self._chain_items(self.graph.nodes)),
                "edges": len(self._chain_items(self.graph.edges)),
                "rules": cytoscape["counts"]["rule_edges"],
                "derivations": self._chain_count(derivation_entries),
                "search_history": len(self._chain_items(self.graph.search_history)),
                "search_comparisons": len(self._chain_items(self.graph.search_comparisons)),
                "search_jobs": len(self._chain_items(self.graph.search_jobs)),
                "search_comparison_jobs": len(self._chain_items(self.graph.search_comparison_jobs)),
            },
            "cytoscape": cytoscape,
        }

    def _comparison_state_unpack(self, state):
        mode = M.Head(state)()
        fields = M.Tail(state)()
        job = M.Head(fields)()
        fields = M.Tail(fields)()
        search_memo = M.Head(fields)()
        fields = M.Tail(fields)()
        active_packets = M.Head(fields)()
        fields = M.Tail(fields)()
        pending_packets = M.Head(fields)()
        fields = M.Tail(fields)()
        pending_packets_count = M.Head(fields)()
        fields = M.Tail(fields)()
        phase = M.Head(fields)()
        fields = M.Tail(fields)()
        completed_packets = M.Head(fields)()
        fields = M.Tail(fields)()
        root_fast_path_result = M.Head(fields)()
        fields = M.Tail(fields)()
        stop_reason = M.Head(fields)()
        return (
            mode,
            job,
            search_memo,
            active_packets,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        )

    def _comparison_state_status(self, state, registry):
        (
            mode,
            job,
            search_memo,
            active_packets,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        ) = self._comparison_state_unpack(state)
        if M.Compare(stop_reason, M.EmptyList)() is M.false_value:
            return stop_reason
        job_status = Searchmod.SearchJobStatus(job)()
        if M.IdentityCompare(job_status, M.SearchSuccessLabel)() is M.truth_value:
            return M.SearchSuccessLabel
        if M.IdentityCompare(job_status, M.SearchPausedLabel)() is M.truth_value:
            return M.SearchPausedLabel
        if (
            M.IdentityCompare(Searchmod.SearchJobFrontier(job)(), M.EmptyList)() is M.truth_value
            and M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value
            and M.NatEq(active_packets, M.Zero, registry)() is M.truth_value
        ):
            return M.SearchFailureLabel
        return M.SearchRunningLabel

    def _cursor_next_action_text(self, cursor, registry):
        if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
            return None
        if M.IsPair(cursor)() is M.truth_value:
            cursor_label = M.Head(cursor)()
            if M.IdentityCompare(cursor_label, M.SearchTheoremCursorLabel)() is M.truth_value:
                rules = Searchmod.SearchTheoremCursorRules(cursor)()
                if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
                    return None
                return "apply " + Pmod.PrettyRule(M.Head(rules)(), registry)()
            if M.IdentityCompare(cursor_label, M.SearchRewriteCursorLabel)() is M.truth_value:
                return "rewrite " + Pmod.PrettyRule(Searchmod.SearchRewriteCursorRule(cursor)(), registry)()
        return self._pretty_term(cursor, registry)

    def _packet_record(self, source, mode, packet, start, goal, registry, packet_id):
        packet_kind = "root_rule"
        current_text = self._pretty_term(start, registry)
        prefix_text = "[]"
        steps_remaining = None
        next_action = None
        target_term = None
        state = M.EmptyList
        packet_term = packet

        if M.IsPair(packet)() is M.truth_value:
            if M.IdentityCompare(M.Head(packet)(), Searchmod.SearchFrontierStatePacketLabel)() is M.truth_value:
                state = Searchmod.SearchFrontierStatePacketState(packet)()
            elif M.IdentityCompare(M.Head(packet)(), Searchmod.SearchStateLabel)() is M.truth_value:
                state = packet
            elif M.IdentityCompare(M.Head(packet)(), Searchmod.SearchJobLabel)() is M.truth_value:
                packet_frontier = Searchmod.SearchJobFrontier(packet)()
                packet_kind = "job"
                if M.IdentityCompare(packet_frontier, M.EmptyList)() is M.false_value:
                    state = M.Head(packet_frontier)()
            elif M.IdentityCompare(M.Head(packet)(), Searchmod.SearchRootRulePacketLabel)() is M.truth_value:
                packet_term = Searchmod.SearchRootRulePacketRule(packet)()

        if M.Compare(state, M.EmptyList)() is M.false_value:
            packet_kind = "state"
            current_text = self._pretty_term(Searchmod.SearchStateCurrent(state)(), registry)
            prefix_text = Pmod.PrettyPlanChain(self._reverse_chain(Searchmod.SearchStatePlan(state)()), registry)()
            steps_remaining = self._pretty_term(Searchmod.SearchStateStepsRemaining(state)(), registry)
            next_action = self._cursor_next_action_text(Searchmod.SearchStateCursor(state)(), registry)
        else:
            target_term = self._pretty_term(packet_term, registry)
            if M.IsEdge(packet_term, registry)() is M.truth_value:
                next_action = "apply " + Pmod.PrettyRule(packet_term, registry)()
            else:
                next_action = self._pretty_term(packet_term, registry)

        return {
            "id": packet_id,
            "source": source,
            "mode": Searchmod.SearchModeText(mode)(),
            "kind": packet_kind,
            "current": current_text,
            "goal": self._pretty_term(goal, registry),
            "prefix": prefix_text,
            "steps_remaining": steps_remaining,
            "next_action": next_action,
            "target_term": target_term,
        }

    def search_packets_view(self):
        registry = self._registry()
        packets = ()
        live_states = self.graph._search_compare_live_states
        live_workers = self.graph._search_compare_live_workers
        live_start = self.graph._search_compare_live_start
        live_goal = self.graph._search_compare_live_goal

        for worker_index, entry in enumerate(self._chain_items(live_workers), 1):
            mode = M.Head(entry)()
            packet = M.Head(M.Tail(M.Tail(entry)())())()
            packets = packets + (
                self._packet_record(
                    "active_worker",
                    mode,
                    packet,
                    live_start,
                    live_goal,
                    registry,
                    "active:" + str(worker_index),
                ),
            )

        for state_index, state in enumerate(self._chain_items(live_states), 1):
            mode, job, _, _, pending_packets, _, _, _, _, _ = self._comparison_state_unpack(state)
            start = Searchmod.SearchJobStart(job)()
            goal = Searchmod.SearchJobGoal(job)()
            for packet_index, packet in enumerate(self._chain_items(pending_packets), 1):
                packets = packets + (
                    self._packet_record(
                        "comparison_pending",
                        mode,
                        packet,
                        start,
                        goal,
                        registry,
                        "pending:" + str(state_index) + ":" + str(packet_index),
                    ),
                )

        for job_index, job in enumerate(self._chain_items(self.graph.search_jobs), 1):
            mode = H.HeuristicSearchMode(Searchmod.SearchJobHeuristic(job)())()
            start = Searchmod.SearchJobStart(job)()
            goal = Searchmod.SearchJobGoal(job)()
            for packet_index, state in enumerate(self._chain_items(Searchmod.SearchJobFrontier(job)()), 1):
                packets = packets + (
                    self._packet_record(
                        "stored_search_job",
                        mode,
                        M.Pair(M.one, M.Pair(state, M.EmptyList)),
                        start,
                        goal,
                        registry,
                        "job:" + str(job_index) + ":" + str(packet_index),
                    ),
                )

        for job_index, comparison_job in enumerate(self._chain_items(self.graph.search_comparison_jobs), 1):
            start = Searchmod.SearchComparisonJobStart(comparison_job)()
            goal = Searchmod.SearchComparisonJobGoal(comparison_job)()
            for state_index, state in enumerate(self._chain_items(Searchmod.SearchComparisonJobStates(comparison_job)()), 1):
                mode, _, _, _, pending_packets, _, _, _, _, _ = self._comparison_state_unpack(state)
                for packet_index, packet in enumerate(self._chain_items(pending_packets), 1):
                    packets = packets + (
                        self._packet_record(
                            "paused_comparison",
                            mode,
                            packet,
                            start,
                            goal,
                            registry,
                            "paused:" + str(job_index) + ":" + str(state_index) + ":" + str(packet_index),
                        ),
                    )

        return packets

    def active_workers_view(self):
        registry = self._registry()
        workers = ()
        live_start = self.graph._search_compare_live_start
        live_goal = self.graph._search_compare_live_goal
        for worker_index, entry in enumerate(self._chain_items(self.graph._search_compare_live_workers), 1):
            mode = M.Head(entry)()
            executor = M.Head(M.Tail(entry)())()
            packet = M.Head(M.Tail(M.Tail(entry)())())()
            slot = M.Head(executor)()
            process = M.Head(M.Tail(executor)())()
            workers = workers + (
                {
                    "id": "worker:" + str(worker_index),
                    "mode": Searchmod.SearchModeText(mode)(),
                    "slot": self._pretty_term(slot, registry),
                    "pid": process.pid,
                    "alive": process.is_alive(),
                    "packet": self._packet_record(
                        "active_worker",
                        mode,
                        packet,
                        live_start,
                        live_goal,
                        registry,
                        "active:" + str(worker_index),
                    ),
                },
            )
        return workers

    def _comparison_state_record(self, state, registry):
        (
            mode,
            job,
            search_memo,
            active_packets,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        ) = self._comparison_state_unpack(state)
        frontier = Searchmod.SearchJobFrontier(job)()
        frontier_preview = None
        if M.IdentityCompare(frontier, M.EmptyList)() is M.false_value:
            frontier_preview = self._packet_record(
                "job_frontier",
                mode,
                M.Pair(M.one, M.Pair(M.Head(frontier)(), M.EmptyList)),
                Searchmod.SearchJobStart(job)(),
                Searchmod.SearchJobGoal(job)(),
                registry,
                "frontier:" + Searchmod.SearchModeText(mode)(),
            )
        return {
            "mode": Searchmod.SearchModeText(mode)(),
            "status": Searchmod.SearchStatusText(self._comparison_state_status(state, registry))(),
            "phase": self._pretty_term(phase, registry),
            "active_packets": self._pretty_term(active_packets, registry),
            "pending_packets": self._pretty_term(pending_packets_count, registry),
            "completed_packets": self._pretty_term(completed_packets, registry),
            "root_fast_path": self._pretty_term(root_fast_path_result, registry),
            "stop_reason": None if M.Compare(stop_reason, M.EmptyList)() is M.truth_value else self._pretty_term(stop_reason, registry),
            "job_status": Searchmod.SearchStatusText(Searchmod.SearchJobStatus(job)())(),
            "expanded": self._pretty_term(Searchmod.SearchJobExpanded(job)(), registry),
            "generated": self._pretty_term(Searchmod.SearchJobGenerated(job)(), registry),
            "frontier_peak": self._pretty_term(Searchmod.SearchJobFrontierPeak(job)(), registry),
            "result_plan": Pmod.PrettyPlanChain(Searchmod.SearchJobResultPlan(job)(), registry)(),
            "frontier_preview": frontier_preview,
        }

    def comparison_state_view(self):
        registry = self._registry()
        live_states = self._chain_items(self.graph._search_compare_live_states)
        paused_jobs = self._chain_items(self.graph.search_comparison_jobs)
        completed = self._chain_items(self.graph.search_comparisons)

        live_view = None
        if live_states:
            live_view = {
                "signature": None
                if M.Compare(self.graph._search_compare_live_signature, M.EmptyList)() is M.truth_value
                else self._pretty_term(self.graph._search_compare_live_signature, registry),
                "start": self._pretty_term(self.graph._search_compare_live_start, registry),
                "goal": self._pretty_term(self.graph._search_compare_live_goal, registry),
                "active_workers": len(self._chain_items(self.graph._search_compare_live_workers)),
                "idle_executors": len(self._chain_items(self.graph._search_compare_live_idle_executors)),
                "states": tuple(self._comparison_state_record(state, registry) for state in live_states),
            }

        paused_view = ()
        for paused_index, comparison_job in enumerate(paused_jobs, 1):
            paused_view = paused_view + (
                {
                    "id": "paused:" + str(paused_index),
                    "signature": self._pretty_term(Searchmod.SearchComparisonJobSignature(comparison_job)(), registry),
                    "start": self._pretty_term(Searchmod.SearchComparisonJobStart(comparison_job)(), registry),
                    "goal": self._pretty_term(Searchmod.SearchComparisonJobGoal(comparison_job)(), registry),
                    "outcome": self._pretty_term(Searchmod.SearchComparisonJobOutcome(comparison_job)(), registry),
                    "states": tuple(
                        self._comparison_state_record(state, registry)
                        for state in self._chain_items(Searchmod.SearchComparisonJobStates(comparison_job)())
                    ),
                },
            )

        completed_view = ()
        for comparison_index, comparison in enumerate(completed, 1):
            best_attempt = Searchmod.SearchComparisonBestAttempt(comparison)()
            best_mode = None
            best_status = None
            if M.Compare(best_attempt, M.EmptyList)() is M.false_value:
                best_mode = Searchmod.SearchModeText(H.HeuristicSearchMode(Pmod.SearchAttemptHeuristic(best_attempt)())())()
                best_status = Searchmod.SearchStatusText(Pmod.SearchAttemptStatus(best_attempt)())()
            completed_view = completed_view + (
                {
                    "id": "comparison:" + str(comparison_index),
                    "signature": self._pretty_term(Searchmod.SearchComparisonSignature(comparison)(), registry),
                    "outcome": self._pretty_term(Searchmod.SearchComparisonOutcome(comparison)(), registry),
                    "attempt_count": len(self._chain_items(Searchmod.SearchComparisonAttempts(comparison)())),
                    "best_mode": best_mode,
                    "best_status": best_status,
                },
            )

        return {
            "live": live_view,
            "paused": paused_view,
            "completed": completed_view,
        }

    def _derivation_step_record(self, step, registry, step_index):
        return {
            "index": step_index,
            "current": self._pretty_term(Pmod.StepCurrent(step, registry)(), registry),
            "action": Pmod.PrettyAction(Pmod.StepAction(step, registry)(), registry)(),
            "next": self._pretty_term(Pmod.StepNext(step, registry)(), registry),
        }

    def _derivation_fragment_record(self, derivation, registry, fragment_id, start=None, goal=None):
        derivation_cost_pair = Pmod.DerivationCost(derivation, registry)()
        cost = M.Head(derivation_cost_pair)()
        reg2 = M.Head(M.Tail(derivation_cost_pair)())()
        steps = self._chain_items(Pmod.DerivationSteps(derivation, reg2)())
        preview_steps = ()
        for step_index, step in enumerate(steps[:8], 1):
            preview_steps = preview_steps + (self._derivation_step_record(step, reg2, step_index),)
        return {
            "id": fragment_id,
            "start": self._pretty_term(start if start is not None else Pmod.DerivationStart(derivation, reg2)(), reg2),
            "goal": None if goal is None else self._pretty_term(goal, reg2),
            "end": self._pretty_term(Pmod.DerivationEnd(derivation, reg2)(), reg2),
            "step_count": len(steps),
            "cost": self._proof_cost_view(cost),
            "preview_steps": preview_steps,
        }

    def derivation_fragments_view(self):
        registry = self._registry()
        fragments = ()
        derivation_entries = self._tree_entries(self.graph.derivations)
        entry_index = 0
        current_entries = derivation_entries
        while M.IdentityCompare(current_entries, M.EmptyList)() is M.false_value:
            entry_index += 1
            entry = M.Head(current_entries)()
            derivation = M.Head(M.Tail(entry)())()
            fragments = fragments + (
                self._derivation_fragment_record(
                    Pmod.DerivationEntryProof(derivation)(),
                    registry,
                    "stored:" + str(entry_index),
                    Pmod.DerivationEntryStart(derivation)(),
                    Pmod.DerivationEntryGoal(derivation)(),
                ),
            )
            current_entries = M.Tail(current_entries)()

        for attempt_index, attempt in enumerate(self._chain_items(self.graph.search_history), 1):
            derivation = Pmod.SearchAttemptDerivation(attempt)()
            if M.Compare(derivation, M.EmptyList)() is M.truth_value:
                continue
            fragments = fragments + (
                self._derivation_fragment_record(
                    derivation,
                    registry,
                    "attempt:" + str(attempt_index),
                    Pmod.SearchAttemptStart(attempt)(),
                    Pmod.SearchAttemptGoal(attempt)(),
                ),
            )

        return fragments

    def introspection_view(self, max_rule_edges=None):
        return {
            "hypergraph": self.hypergraph_view(max_rule_edges=max_rule_edges),
            "search_packets": self.search_packets_view(),
            "active_workers": self.active_workers_view(),
            "comparison_state": self.comparison_state_view(),
            "derivation_fragments": self.derivation_fragments_view(),
        }

    def introspection_json(self, max_rule_edges=None):
        return self._json_object(
            self._json_pair("hypergraph", self._hypergraph_json(max_rule_edges))
            + ", "
            + self._json_pair("search_packets", self._search_packets_json())
            + ", "
            + self._json_pair("active_workers", self._active_workers_json())
            + ", "
            + self._json_pair("comparison_state", self._comparison_state_json())
            + ", "
            + self._json_pair("derivation_fragments", self._derivation_fragments_json())
        )

    def inspector_payload_json(self, source_text, max_rule_edges=None):
        return self._json_object(
            self._json_pair("source", self._json_string(source_text))
            + ", "
            + self._json_pair("introspection", self.introspection_json(max_rule_edges=max_rule_edges))
        )

    def _json_string(self, text):
        escaped = str(text)
        escaped = escaped.replace("\\", "\\\\")
        escaped = escaped.replace("\"", "\\\"")
        escaped = escaped.replace("\b", "\\b")
        escaped = escaped.replace("\f", "\\f")
        escaped = escaped.replace("\n", "\\n")
        escaped = escaped.replace("\r", "\\r")
        escaped = escaped.replace("\t", "\\t")
        return "\"" + escaped + "\""

    def _json_pair(self, key, value_text):
        return self._json_string(key) + ": " + value_text

    def _json_object(self, body_text):
        return "{ " + body_text + " }"

    def _json_array(self, body_text):
        return "[ " + body_text + " ]"

    def _json_null_or_string(self, text):
        if text is None:
            return "null"
        return self._json_string(text)

    def _json_bool(self, value):
        if value:
            return "true"
        return "false"

    def _json_append(self, body_text, item_text):
        if body_text:
            return body_text + ", " + item_text
        return item_text

    def _chain_count(self, chain):
        count = 0
        current = chain
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            count += 1
            current = M.Tail(current)()
        return count

    def _context_term_id(self, term, registry):
        current = self.graph.nodes
        index = 1
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            if M.CompareIn(M.Head(current)(), term, registry)() is M.EQ:
                return "term:context:" + str(index)
            index += 1
            current = M.Tail(current)()
        return None

    def _term_node_json(self, node_id, term, registry):
        term_text = self._pretty_term(term, registry)
        return self._json_object(
            self._json_pair(
                "data",
                self._json_object(
                    self._json_pair("id", self._json_string(node_id))
                    + ", "
                    + self._json_pair("label", self._json_string(term_text))
                    + ", "
                    + self._json_pair("kind", self._json_string("term"))
                    + ", "
                    + self._json_pair("constructor", self._json_string(self._constructor_text(term, registry)))
                    + ", "
                    + self._json_pair("term", self._json_string(term_text))
                ),
            )
        )

    def _hyperedge_node_json(self, node_id, label_text, kind_text, constructor_text):
        return self._json_object(
            self._json_pair(
                "data",
                self._json_object(
                    self._json_pair("id", self._json_string(node_id))
                    + ", "
                    + self._json_pair("label", self._json_string(label_text))
                    + ", "
                    + self._json_pair("kind", self._json_string(kind_text))
                    + ", "
                    + self._json_pair("constructor", self._json_string(constructor_text))
                    + ", "
                    + self._json_pair("term", self._json_string(label_text))
                ),
            )
        )

    def _incidence_edge_json(self, edge_id, source_id, target_id, kind_text, label_text):
        return self._json_object(
            self._json_pair(
                "data",
                self._json_object(
                    self._json_pair("id", self._json_string(edge_id))
                    + ", "
                    + self._json_pair("source", self._json_string(source_id))
                    + ", "
                    + self._json_pair("target", self._json_string(target_id))
                    + ", "
                    + self._json_pair("kind", self._json_string(kind_text))
                    + ", "
                    + self._json_pair("label", self._json_string(label_text))
                ),
            )
        )

    def _hypergraph_json(self, max_rule_edges=None):
        registry = self._registry()
        nodes_body = ""
        edges_body = ""
        context_nodes = 0
        context_edges = 0
        rule_edges_total = 0
        visible_rule_edges = 0
        cy_nodes = 0
        cy_edges = 0

        current_nodes = self.graph.nodes
        while M.IdentityCompare(current_nodes, M.EmptyList)() is M.false_value:
            context_nodes += 1
            nodes_body = self._json_append(
                nodes_body,
                self._term_node_json("term:context:" + str(context_nodes), M.Head(current_nodes)(), registry),
            )
            cy_nodes += 1
            current_nodes = M.Tail(current_nodes)()

        current_edges = self.graph.edges
        while M.IdentityCompare(current_edges, M.EmptyList)() is M.false_value:
            context_edges += 1
            edge = M.Head(current_edges)()
            edge_id = "graph-edge:" + str(context_edges)
            nodes_body = self._json_append(
                nodes_body,
                self._hyperedge_node_json(
                    edge_id,
                    self._pretty_term(edge, registry),
                    "graph_hyperedge",
                    self._constructor_text(edge, registry),
                ),
            )
            cy_nodes += 1

            input_index = 0
            inputs = M.EdgeInputs(edge)()
            while M.IdentityCompare(inputs, M.EmptyList)() is M.false_value:
                input_index += 1
                input_term = M.Head(inputs)()
                source_id = self._context_term_id(input_term, registry)
                if source_id is None:
                    source_id = "term:graph-in:" + str(context_edges) + ":" + str(input_index)
                    nodes_body = self._json_append(nodes_body, self._term_node_json(source_id, input_term, registry))
                    cy_nodes += 1
                edges_body = self._json_append(
                    edges_body,
                    self._incidence_edge_json(
                        "incidence:in:" + str(context_edges) + ":" + str(input_index),
                        source_id,
                        edge_id,
                        "incidence_in",
                        "input",
                    ),
                )
                cy_edges += 1
                inputs = M.Tail(inputs)()

            result_index = 0
            results = M.EdgeResults(edge)()
            while M.IdentityCompare(results, M.EmptyList)() is M.false_value:
                result_index += 1
                result_term = M.Head(results)()
                target_id = self._context_term_id(result_term, registry)
                if target_id is None:
                    target_id = "term:graph-out:" + str(context_edges) + ":" + str(result_index)
                    nodes_body = self._json_append(nodes_body, self._term_node_json(target_id, result_term, registry))
                    cy_nodes += 1
                edges_body = self._json_append(
                    edges_body,
                    self._incidence_edge_json(
                        "incidence:out:" + str(context_edges) + ":" + str(result_index),
                        edge_id,
                        target_id,
                        "incidence_out",
                        "result",
                    ),
                )
                cy_edges += 1
                results = M.Tail(results)()

            current_edges = M.Tail(current_edges)()

        current_rules = self.ordered_rules()
        while M.IdentityCompare(current_rules, M.EmptyList)() is M.false_value:
            rule_edges_total += 1
            if max_rule_edges is None or visible_rule_edges < max_rule_edges:
                visible_rule_edges += 1
                rule = M.Head(current_rules)()
                edge_id = "rule-edge:" + str(visible_rule_edges)
                nodes_body = self._json_append(
                    nodes_body,
                    self._hyperedge_node_json(
                        edge_id,
                        Pmod.PrettyRule(rule, registry)(),
                        "rule_hyperedge",
                        self._constructor_text(rule, registry),
                    ),
                )
                cy_nodes += 1

                input_index = 0
                inputs = Pmod.RulePremises(rule)()
                while M.IdentityCompare(inputs, M.EmptyList)() is M.false_value:
                    input_index += 1
                    input_term = M.Head(inputs)()
                    source_id = self._context_term_id(input_term, registry)
                    if source_id is None:
                        source_id = "term:rule-in:" + str(visible_rule_edges) + ":" + str(input_index)
                        nodes_body = self._json_append(nodes_body, self._term_node_json(source_id, input_term, registry))
                        cy_nodes += 1
                    edges_body = self._json_append(
                        edges_body,
                        self._incidence_edge_json(
                            "rule-incidence:in:" + str(visible_rule_edges) + ":" + str(input_index),
                            source_id,
                            edge_id,
                            "rule_incidence_in",
                            "premise",
                        ),
                    )
                    cy_edges += 1
                    inputs = M.Tail(inputs)()

                result_index = 0
                results = M.Pair(Pmod.RuleReplacement(rule)(), M.EmptyList)
                while M.IdentityCompare(results, M.EmptyList)() is M.false_value:
                    result_index += 1
                    result_term = M.Head(results)()
                    target_id = self._context_term_id(result_term, registry)
                    if target_id is None:
                        target_id = "term:rule-out:" + str(visible_rule_edges) + ":" + str(result_index)
                        nodes_body = self._json_append(nodes_body, self._term_node_json(target_id, result_term, registry))
                        cy_nodes += 1
                    edges_body = self._json_append(
                        edges_body,
                        self._incidence_edge_json(
                            "rule-incidence:out:" + str(visible_rule_edges) + ":" + str(result_index),
                            edge_id,
                            target_id,
                            "rule_incidence_out",
                            "result",
                        ),
                    )
                    cy_edges += 1
                    results = M.Tail(results)()

            current_rules = M.Tail(current_rules)()

        return self._json_object(
            self._json_pair("kind", self._json_string("hypergraph"))
            + ", "
            + self._json_pair(
                "counts",
                self._json_object(
                    self._json_pair("nodes", str(context_nodes))
                    + ", "
                    + self._json_pair("edges", str(context_edges))
                    + ", "
                    + self._json_pair("rules", str(rule_edges_total))
                    + ", "
                    + self._json_pair("derivations", str(self._chain_count(self._tree_entries(self.graph.derivations))))
                    + ", "
                    + self._json_pair("search_history", str(self._chain_count(self.graph.search_history)))
                    + ", "
                    + self._json_pair("search_comparisons", str(self._chain_count(self.graph.search_comparisons)))
                    + ", "
                    + self._json_pair("search_jobs", str(self._chain_count(self.graph.search_jobs)))
                    + ", "
                    + self._json_pair("search_comparison_jobs", str(self._chain_count(self.graph.search_comparison_jobs)))
                ),
            )
            + ", "
            + self._json_pair(
                "cytoscape",
                self._json_object(
                    self._json_pair(
                        "elements",
                        self._json_object(
                            self._json_pair("nodes", self._json_array(nodes_body))
                            + ", "
                            + self._json_pair("edges", self._json_array(edges_body))
                        ),
                    )
                    + ", "
                    + self._json_pair(
                        "counts",
                        self._json_object(
                            self._json_pair("context_nodes", str(context_nodes))
                            + ", "
                            + self._json_pair("context_edges", str(context_edges))
                            + ", "
                            + self._json_pair("rule_edges", str(rule_edges_total))
                            + ", "
                            + self._json_pair("visible_rule_edges", str(visible_rule_edges))
                            + ", "
                            + self._json_pair("cy_nodes", str(cy_nodes))
                            + ", "
                            + self._json_pair("cy_edges", str(cy_edges))
                        ),
                    )
                ),
            )
        )

    def _packet_json(self, source, mode, packet, start, goal, registry, packet_id):
        packet_kind = "root_rule"
        current_text = self._pretty_term(start, registry)
        prefix_text = "[]"
        steps_remaining = None
        next_action = None
        target_term = None
        state = M.EmptyList
        packet_term = packet

        if M.IsPair(packet)() is M.truth_value:
            if M.IdentityCompare(M.Head(packet)(), Searchmod.SearchFrontierStatePacketLabel)() is M.truth_value:
                state = Searchmod.SearchFrontierStatePacketState(packet)()
            elif M.IdentityCompare(M.Head(packet)(), Searchmod.SearchStateLabel)() is M.truth_value:
                state = packet
            elif M.IdentityCompare(M.Head(packet)(), Searchmod.SearchJobLabel)() is M.truth_value:
                packet_frontier = Searchmod.SearchJobFrontier(packet)()
                packet_kind = "job"
                if M.IdentityCompare(packet_frontier, M.EmptyList)() is M.false_value:
                    state = M.Head(packet_frontier)()
            elif M.IdentityCompare(M.Head(packet)(), Searchmod.SearchRootRulePacketLabel)() is M.truth_value:
                packet_term = Searchmod.SearchRootRulePacketRule(packet)()

        if M.Compare(state, M.EmptyList)() is M.false_value:
            packet_kind = "state"
            current_text = self._pretty_term(Searchmod.SearchStateCurrent(state)(), registry)
            prefix_text = Pmod.PrettyPlanChain(self._reverse_chain(Searchmod.SearchStatePlan(state)()), registry)()
            steps_remaining = self._pretty_term(Searchmod.SearchStateStepsRemaining(state)(), registry)
            next_action = self._cursor_next_action_text(Searchmod.SearchStateCursor(state)(), registry)
        else:
            target_term = self._pretty_term(packet_term, registry)
            if M.IsEdge(packet_term, registry)() is M.truth_value:
                next_action = "apply " + Pmod.PrettyRule(packet_term, registry)()
            else:
                next_action = self._pretty_term(packet_term, registry)

        return self._json_object(
            self._json_pair("id", self._json_string(packet_id))
            + ", "
            + self._json_pair("source", self._json_string(source))
            + ", "
            + self._json_pair("mode", self._json_string(Searchmod.SearchModeText(mode)()))
            + ", "
            + self._json_pair("kind", self._json_string(packet_kind))
            + ", "
            + self._json_pair("current", self._json_string(current_text))
            + ", "
            + self._json_pair("goal", self._json_string(self._pretty_term(goal, registry)))
            + ", "
            + self._json_pair("prefix", self._json_string(prefix_text))
            + ", "
            + self._json_pair("steps_remaining", self._json_null_or_string(steps_remaining))
            + ", "
            + self._json_pair("next_action", self._json_null_or_string(next_action))
            + ", "
            + self._json_pair("target_term", self._json_null_or_string(target_term))
        )

    def _search_packets_json(self):
        registry = self._registry()
        body = ""
        live_start = self.graph._search_compare_live_start
        live_goal = self.graph._search_compare_live_goal

        worker_index = 0
        current_workers = self.graph._search_compare_live_workers
        while M.IdentityCompare(current_workers, M.EmptyList)() is M.false_value:
            worker_index += 1
            entry = M.Head(current_workers)()
            mode = M.Head(entry)()
            packet = M.Head(M.Tail(M.Tail(entry)())())()
            body = self._json_append(
                body,
                self._packet_json("active_worker", mode, packet, live_start, live_goal, registry, "active:" + str(worker_index)),
            )
            current_workers = M.Tail(current_workers)()

        state_index = 0
        current_states = self.graph._search_compare_live_states
        while M.IdentityCompare(current_states, M.EmptyList)() is M.false_value:
            state_index += 1
            state = M.Head(current_states)()
            mode, job, _, _, pending_packets, _, _, _, _, _ = self._comparison_state_unpack(state)
            start = Searchmod.SearchJobStart(job)()
            goal = Searchmod.SearchJobGoal(job)()
            packet_index = 0
            current_packets = pending_packets
            while M.IdentityCompare(current_packets, M.EmptyList)() is M.false_value:
                packet_index += 1
                body = self._json_append(
                    body,
                    self._packet_json(
                        "comparison_pending",
                        mode,
                        M.Head(current_packets)(),
                        start,
                        goal,
                        registry,
                        "pending:" + str(state_index) + ":" + str(packet_index),
                    ),
                )
                current_packets = M.Tail(current_packets)()
            current_states = M.Tail(current_states)()

        job_index = 0
        current_jobs = self.graph.search_jobs
        while M.IdentityCompare(current_jobs, M.EmptyList)() is M.false_value:
            job_index += 1
            job = M.Head(current_jobs)()
            mode = H.HeuristicSearchMode(Searchmod.SearchJobHeuristic(job)())()
            start = Searchmod.SearchJobStart(job)()
            goal = Searchmod.SearchJobGoal(job)()
            packet_index = 0
            current_frontier = Searchmod.SearchJobFrontier(job)()
            while M.IdentityCompare(current_frontier, M.EmptyList)() is M.false_value:
                packet_index += 1
                body = self._json_append(
                    body,
                    self._packet_json(
                        "stored_search_job",
                        mode,
                        M.Pair(M.one, M.Pair(M.Head(current_frontier)(), M.EmptyList)),
                        start,
                        goal,
                        registry,
                        "job:" + str(job_index) + ":" + str(packet_index),
                    ),
                )
                current_frontier = M.Tail(current_frontier)()
            current_jobs = M.Tail(current_jobs)()

        comparison_index = 0
        current_comparison_jobs = self.graph.search_comparison_jobs
        while M.IdentityCompare(current_comparison_jobs, M.EmptyList)() is M.false_value:
            comparison_index += 1
            comparison_job = M.Head(current_comparison_jobs)()
            start = Searchmod.SearchComparisonJobStart(comparison_job)()
            goal = Searchmod.SearchComparisonJobGoal(comparison_job)()
            paused_state_index = 0
            current_paused_states = Searchmod.SearchComparisonJobStates(comparison_job)()
            while M.IdentityCompare(current_paused_states, M.EmptyList)() is M.false_value:
                paused_state_index += 1
                state = M.Head(current_paused_states)()
                mode, _, _, _, pending_packets, _, _, _, _, _ = self._comparison_state_unpack(state)
                packet_index = 0
                current_packets = pending_packets
                while M.IdentityCompare(current_packets, M.EmptyList)() is M.false_value:
                    packet_index += 1
                    body = self._json_append(
                        body,
                        self._packet_json(
                            "paused_comparison",
                            mode,
                            M.Head(current_packets)(),
                            start,
                            goal,
                            registry,
                            "paused:" + str(comparison_index) + ":" + str(paused_state_index) + ":" + str(packet_index),
                        ),
                    )
                    current_packets = M.Tail(current_packets)()
                current_paused_states = M.Tail(current_paused_states)()
            current_comparison_jobs = M.Tail(current_comparison_jobs)()

        return self._json_array(body)

    def _active_workers_json(self):
        registry = self._registry()
        body = ""
        worker_index = 0
        live_start = self.graph._search_compare_live_start
        live_goal = self.graph._search_compare_live_goal
        current_workers = self.graph._search_compare_live_workers
        while M.IdentityCompare(current_workers, M.EmptyList)() is M.false_value:
            worker_index += 1
            entry = M.Head(current_workers)()
            mode = M.Head(entry)()
            executor = M.Head(M.Tail(entry)())()
            packet = M.Head(M.Tail(M.Tail(entry)())())()
            slot = M.Head(executor)()
            process = M.Head(M.Tail(executor)())()
            body = self._json_append(
                body,
                self._json_object(
                    self._json_pair("id", self._json_string("worker:" + str(worker_index)))
                    + ", "
                    + self._json_pair("mode", self._json_string(Searchmod.SearchModeText(mode)()))
                    + ", "
                    + self._json_pair("slot", self._json_string(self._pretty_term(slot, registry)))
                    + ", "
                    + self._json_pair("pid", str(process.pid))
                    + ", "
                    + self._json_pair("alive", self._json_bool(process.is_alive()))
                    + ", "
                    + self._json_pair(
                        "packet",
                        self._packet_json("active_worker", mode, packet, live_start, live_goal, registry, "active:" + str(worker_index)),
                    )
                ),
            )
            current_workers = M.Tail(current_workers)()
        return self._json_array(body)

    def _comparison_frontier_preview_json(self, mode, job, frontier, registry):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return "null"
        return self._packet_json(
            "job_frontier",
            mode,
            M.Pair(M.one, M.Pair(M.Head(frontier)(), M.EmptyList)),
            Searchmod.SearchJobStart(job)(),
            Searchmod.SearchJobGoal(job)(),
            registry,
            "frontier:" + Searchmod.SearchModeText(mode)(),
        )

    def _comparison_state_json_record(self, state, registry):
        (
            mode,
            job,
            _search_memo,
            active_packets,
            _pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        ) = self._comparison_state_unpack(state)
        frontier = Searchmod.SearchJobFrontier(job)()
        stop_reason_text = "null"
        if M.Compare(stop_reason, M.EmptyList)() is M.false_value:
            stop_reason_text = self._json_string(self._pretty_term(stop_reason, registry))
        return self._json_object(
            self._json_pair("mode", self._json_string(Searchmod.SearchModeText(mode)()))
            + ", "
            + self._json_pair("status", self._json_string(Searchmod.SearchStatusText(self._comparison_state_status(state, registry))()))
            + ", "
            + self._json_pair("phase", self._json_string(self._pretty_term(phase, registry)))
            + ", "
            + self._json_pair("active_packets", self._json_string(self._pretty_term(active_packets, registry)))
            + ", "
            + self._json_pair("pending_packets", self._json_string(self._pretty_term(pending_packets_count, registry)))
            + ", "
            + self._json_pair("completed_packets", self._json_string(self._pretty_term(completed_packets, registry)))
            + ", "
            + self._json_pair("root_fast_path", self._json_string(self._pretty_term(root_fast_path_result, registry)))
            + ", "
            + self._json_pair("stop_reason", stop_reason_text)
            + ", "
            + self._json_pair("job_status", self._json_string(Searchmod.SearchStatusText(Searchmod.SearchJobStatus(job)())()))
            + ", "
            + self._json_pair("expanded", self._json_string(self._pretty_term(Searchmod.SearchJobExpanded(job)(), registry)))
            + ", "
            + self._json_pair("generated", self._json_string(self._pretty_term(Searchmod.SearchJobGenerated(job)(), registry)))
            + ", "
            + self._json_pair("frontier_peak", self._json_string(self._pretty_term(Searchmod.SearchJobFrontierPeak(job)(), registry)))
            + ", "
            + self._json_pair("result_plan", self._json_string(Pmod.PrettyPlanChain(Searchmod.SearchJobResultPlan(job)(), registry)()))
            + ", "
            + self._json_pair("frontier_preview", self._comparison_frontier_preview_json(mode, job, frontier, registry))
        )

    def _comparison_state_json(self):
        registry = self._registry()
        live_body = "null"
        if M.IdentityCompare(self.graph._search_compare_live_states, M.EmptyList)() is M.false_value:
            states_body = ""
            current_states = self.graph._search_compare_live_states
            while M.IdentityCompare(current_states, M.EmptyList)() is M.false_value:
                states_body = self._json_append(states_body, self._comparison_state_json_record(M.Head(current_states)(), registry))
                current_states = M.Tail(current_states)()
            signature_text = "null"
            if M.Compare(self.graph._search_compare_live_signature, M.EmptyList)() is M.false_value:
                signature_text = self._json_string(self._pretty_term(self.graph._search_compare_live_signature, registry))
            live_body = self._json_object(
                self._json_pair("signature", signature_text)
                + ", "
                + self._json_pair("start", self._json_string(self._pretty_term(self.graph._search_compare_live_start, registry)))
                + ", "
                + self._json_pair("goal", self._json_string(self._pretty_term(self.graph._search_compare_live_goal, registry)))
                + ", "
                + self._json_pair("active_workers", str(self._chain_count(self.graph._search_compare_live_workers)))
                + ", "
                + self._json_pair("idle_executors", str(self._chain_count(self.graph._search_compare_live_idle_executors)))
                + ", "
                + self._json_pair("states", self._json_array(states_body))
            )

        paused_body = ""
        paused_index = 0
        current_paused = self.graph.search_comparison_jobs
        while M.IdentityCompare(current_paused, M.EmptyList)() is M.false_value:
            paused_index += 1
            comparison_job = M.Head(current_paused)()
            states_body = ""
            current_states = Searchmod.SearchComparisonJobStates(comparison_job)()
            while M.IdentityCompare(current_states, M.EmptyList)() is M.false_value:
                states_body = self._json_append(states_body, self._comparison_state_json_record(M.Head(current_states)(), registry))
                current_states = M.Tail(current_states)()
            paused_body = self._json_append(
                paused_body,
                self._json_object(
                    self._json_pair("id", self._json_string("paused:" + str(paused_index)))
                    + ", "
                    + self._json_pair("signature", self._json_string(self._pretty_term(Searchmod.SearchComparisonJobSignature(comparison_job)(), registry)))
                    + ", "
                    + self._json_pair("start", self._json_string(self._pretty_term(Searchmod.SearchComparisonJobStart(comparison_job)(), registry)))
                    + ", "
                    + self._json_pair("goal", self._json_string(self._pretty_term(Searchmod.SearchComparisonJobGoal(comparison_job)(), registry)))
                    + ", "
                    + self._json_pair("outcome", self._json_string(self._pretty_term(Searchmod.SearchComparisonJobOutcome(comparison_job)(), registry)))
                    + ", "
                    + self._json_pair("states", self._json_array(states_body))
                ),
            )
            current_paused = M.Tail(current_paused)()

        completed_body = ""
        comparison_index = 0
        current_completed = self.graph.search_comparisons
        while M.IdentityCompare(current_completed, M.EmptyList)() is M.false_value:
            comparison_index += 1
            comparison = M.Head(current_completed)()
            best_attempt = Searchmod.SearchComparisonBestAttempt(comparison)()
            best_mode_text = "null"
            best_status_text = "null"
            if M.Compare(best_attempt, M.EmptyList)() is M.false_value:
                best_mode_text = self._json_string(Searchmod.SearchModeText(H.HeuristicSearchMode(Pmod.SearchAttemptHeuristic(best_attempt)())())())
                best_status_text = self._json_string(Searchmod.SearchStatusText(Pmod.SearchAttemptStatus(best_attempt)())())
            completed_body = self._json_append(
                completed_body,
                self._json_object(
                    self._json_pair("id", self._json_string("comparison:" + str(comparison_index)))
                    + ", "
                    + self._json_pair("signature", self._json_string(self._pretty_term(Searchmod.SearchComparisonSignature(comparison)(), registry)))
                    + ", "
                    + self._json_pair("outcome", self._json_string(self._pretty_term(Searchmod.SearchComparisonOutcome(comparison)(), registry)))
                    + ", "
                    + self._json_pair("attempt_count", str(self._chain_count(Searchmod.SearchComparisonAttempts(comparison)())))
                    + ", "
                    + self._json_pair("best_mode", best_mode_text)
                    + ", "
                    + self._json_pair("best_status", best_status_text)
                ),
            )
            current_completed = M.Tail(current_completed)()

        return self._json_object(
            self._json_pair("live", live_body)
            + ", "
            + self._json_pair("paused", self._json_array(paused_body))
            + ", "
            + self._json_pair("completed", self._json_array(completed_body))
        )

    def _derivation_step_json(self, step, registry, step_index):
        return self._json_object(
            self._json_pair("index", str(step_index))
            + ", "
            + self._json_pair("current", self._json_string(self._pretty_term(Pmod.StepCurrent(step, registry)(), registry)))
            + ", "
            + self._json_pair("action", self._json_string(Pmod.PrettyAction(Pmod.StepAction(step, registry)(), registry)()))
            + ", "
            + self._json_pair("next", self._json_string(self._pretty_term(Pmod.StepNext(step, registry)(), registry)))
        )

    def _derivation_fragment_json(self, derivation, registry, fragment_id, start=None, goal=None):
        derivation_cost_pair = Pmod.DerivationCost(derivation, registry)()
        cost = M.Head(derivation_cost_pair)()
        reg2 = M.Head(M.Tail(derivation_cost_pair)())()
        step_count = 0
        preview_body = ""
        current_steps = Pmod.DerivationSteps(derivation, reg2)()
        while M.IdentityCompare(current_steps, M.EmptyList)() is M.false_value:
            step_count += 1
            if step_count <= 8:
                preview_body = self._json_append(preview_body, self._derivation_step_json(M.Head(current_steps)(), reg2, step_count))
            current_steps = M.Tail(current_steps)()
        goal_text = "null"
        if goal is not None:
            goal_text = self._json_string(self._pretty_term(goal, reg2))
        cost_view = self._proof_cost_view(cost)
        return self._json_object(
            self._json_pair("id", self._json_string(fragment_id))
            + ", "
            + self._json_pair("start", self._json_string(self._pretty_term(start if start is not None else Pmod.DerivationStart(derivation, reg2)(), reg2)))
            + ", "
            + self._json_pair("goal", goal_text)
            + ", "
            + self._json_pair("end", self._json_string(self._pretty_term(Pmod.DerivationEnd(derivation, reg2)(), reg2)))
            + ", "
            + self._json_pair("step_count", str(step_count))
            + ", "
            + self._json_pair(
                "cost",
                self._json_object(
                    self._json_pair("value", self._json_string(str(cost_view["value"])))
                    + ", "
                    + self._json_pair("text", self._json_string(str(cost_view["text"])))
                ),
            )
            + ", "
            + self._json_pair("preview_steps", self._json_array(preview_body))
        )

    def _derivation_fragments_json(self):
        registry = self._registry()
        body = ""

        entry_index = 0
        current_entries = self._tree_entries(self.graph.derivations)
        while M.IdentityCompare(current_entries, M.EmptyList)() is M.false_value:
            entry = M.Head(current_entries)()
            derivation = M.Head(M.Tail(entry)())()
            body = self._json_append(
                body,
                self._derivation_fragment_json(
                    Pmod.DerivationEntryProof(derivation)(),
                    registry,
                    "stored:" + str(entry_index + 1),
                    Pmod.DerivationEntryStart(derivation)(),
                    Pmod.DerivationEntryGoal(derivation)(),
                ),
            )
            entry_index += 1
            current_entries = M.Tail(current_entries)()

        attempt_index = 0
        current_attempts = self.graph.search_history
        while M.IdentityCompare(current_attempts, M.EmptyList)() is M.false_value:
            attempt_index += 1
            attempt = M.Head(current_attempts)()
            derivation = Pmod.SearchAttemptDerivation(attempt)()
            if M.Compare(derivation, M.EmptyList)() is M.false_value:
                body = self._json_append(
                    body,
                    self._derivation_fragment_json(
                        derivation,
                        registry,
                        "attempt:" + str(attempt_index),
                        Pmod.SearchAttemptStart(attempt)(),
                        Pmod.SearchAttemptGoal(attempt)(),
                    ),
                )
            current_attempts = M.Tail(current_attempts)()

        return self._json_array(body)


class LoadedRuntimePacks:
    def __init__(self, packs, string_table):
        self.packs = packs
        self._by_name = PackTreeMap(string_table)
        for pack in packs:
            self._by_name.store(pack.name, pack)

    def by_name(self, name):
        return self._by_name[name]


def _sync_live_namespace(namespace, deadline=None):
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    M.__dict__.update(namespace)
    live_namespace = M.__dict__
    Core.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    Ctxmod.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    L.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    T.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    Logicmod.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    C.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    Gmpmod.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    Peanomod.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    Arithmod.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    Prettymod.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    Pmod.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    Searchmod.sync_from_namespace(live_namespace)
    if deadline is not None:
        deadline.require_remaining("namespace synchronization")
    live_namespace["AllConstructors"] = C.AllConstructors
    M.AllConstructors = C.AllConstructors
    return live_namespace


def make_fresh_runtime():
    base_registry = M.Tree(M.EmptyList)
    C.set_all_constructors(base_registry)
    M.AllConstructors = base_registry

    one_pair = M.Succ(M.Zero, M.AllConstructors)()
    M.one = M.Head(one_pair)()
    M.AllConstructors = C.set_all_constructors(M.Head(M.Tail(one_pair)())())

    two_pair = M.Succ(M.one, M.AllConstructors)()
    M.two = M.Head(two_pair)()
    M.AllConstructors = C.set_all_constructors(M.Head(M.Tail(two_pair)())())

    three_pair = M.Succ(M.two, M.AllConstructors)()
    M.three = M.Head(three_pair)()
    M.AllConstructors = C.set_all_constructors(M.Head(M.Tail(three_pair)())())

    four_pair = M.Succ(M.three, M.AllConstructors)()
    M.four = M.Head(four_pair)()
    M.AllConstructors = C.set_all_constructors(M.Head(M.Tail(four_pair)())())

    five_pair = M.Succ(M.four, M.AllConstructors)()
    M.five = M.Head(five_pair)()
    M.AllConstructors = C.set_all_constructors(M.Head(M.Tail(five_pair)())())

    six_pair = M.Succ(M.five, M.AllConstructors)()
    M.six = M.Head(six_pair)()
    M.AllConstructors = C.set_all_constructors(M.Head(M.Tail(six_pair)())())

    seven_pair = M.Succ(M.six, M.AllConstructors)()
    M.seven = M.Head(seven_pair)()
    M.AllConstructors = C.set_all_constructors(M.Head(M.Tail(seven_pair)())())

    eight_pair = M.Succ(M.seven, M.AllConstructors)()
    M.eight = M.Head(eight_pair)()
    M.AllConstructors = C.set_all_constructors(M.Head(M.Tail(eight_pair)())())

    nine_pair = M.Succ(M.eight, M.AllConstructors)()
    M.nine = M.Head(nine_pair)()
    M.AllConstructors = C.set_all_constructors(M.Head(M.Tail(nine_pair)())())
    base_registry = M.AllConstructors

    C.set_all_constructors(base_registry)
    C.one = M.one
    C.two = M.two
    C.three = M.three
    C.four = M.four
    C.five = M.five
    C.six = M.six
    C.seven = M.seven
    C.eight = M.eight
    C.nine = M.nine
    M.AllConstructors = base_registry

    graph = Hypergraph(base_registry)
    current_registry = M.FromContextGetConstructors(graph)()
    C.set_all_constructors(current_registry)
    M.AllConstructors = current_registry

    theorem_heuristic = H.Heuristic(
        M.DFSLabel,
        M.GoalHeadOrderLabel,
        M.Zero,
        M.one,
        M.one,
        M.one,
    )()

    rewrite_heuristic = H.Heuristic(
        M.RewriteDFSLabel,
        M.GoalHeadOrderLabel,
        M.Zero,
        M.one,
        M.one,
        M.one,
    )()

    return MachineRuntime(graph, theorem_heuristic, rewrite_heuristic)


def _debug_log(debug_flag, *args, **kwargs):
    if M.IdentityCompare(debug_flag, M.truth_value)() is M.truth_value:
        print(*args, **kwargs)


def boot_from_packs(pack_paths, namespace, debug=M.false_value):
    namespace = _sync_live_namespace(namespace)
    _debug_log(debug, "DEBUG: boot_from_packs: namespace synced")
    _debug_log(debug, "DEBUG: boot_from_packs: creating fresh runtime")
    runtime = make_fresh_runtime()
    _debug_log(debug, "DEBUG: boot_from_packs: fresh runtime created")
    loader = PackLoader(namespace)
    _debug_log(debug, "DEBUG: boot_from_packs: pack loader initialized")

    loaded_packs = ()
    for path in pack_paths:
        _debug_log(debug, f"DEBUG: boot_from_packs: loading pack file {os.path.basename(path)}")
        loaded_packs = loaded_packs + (loader.load_pack_file(path, runtime.graph),)

    runtime.loaded_packs = loaded_packs
    return runtime, LoadedRuntimePacks(loaded_packs, loader.string_table)


def boot_from_snapshot(
    snapshot_path,
    namespace,
    debug=M.false_value,
    save_upgraded_snapshot=M.truth_value,
):
    namespace = _sync_live_namespace(namespace)
    _debug_log(debug, f"DEBUG: boot_from_snapshot: loading snapshot {snapshot_path}")
    codec = SnapshotCodec(namespace)
    state = codec.load(snapshot_path)

    runtime = make_fresh_runtime()
    _debug_log(debug, "DEBUG: boot_from_snapshot: activating snapshot state")
    _debug_log(debug, "DEBUG: boot_from_snapshot: restored snapshot roots, rebuilding graph context")
    codec.activate(
        state,
        runtime.graph,
        debug=debug,
        save_upgraded_snapshot=save_upgraded_snapshot,
    )
    M.AllConstructors = M.set_all_constructors(runtime.graph.constructor_registry)
    _sync_live_namespace(namespace)
    _debug_log(debug, "DEBUG: boot_from_snapshot: snapshot state activated")
    if M.AndAtom(
        M.Compare(state.needs_upgrade, M.truth_value)(),
        M.IdentityCompare(save_upgraded_snapshot, M.truth_value)(),
    )() is M.truth_value:
        _debug_log(debug, "DEBUG: snapshot needs upgrade, saving new snapshot")
        try:
            upgrade_roots = state.upgrade_roots
        except Exception:
            upgrade_roots = ()
        if upgrade_roots:
            print("snapshot upgrade reason: legacy TreeNode roots:", upgrade_roots, flush=True)
        root, ext = os.path.splitext(snapshot_path)
        upgraded_root = root
        underscore_v = root.rfind("_v")
        if underscore_v != -1 and underscore_v + 2 < len(root):
            suffix = root[underscore_v + 2 :]
            if suffix.isdigit():
                upgraded_root = root[:underscore_v] + "_v9"
        if upgraded_root == root:
            upgraded_root = root + "_v9"
        upgraded_snapshot_path = upgraded_root + ext
        temp_snapshot_path = upgraded_snapshot_path + ".tmp"
        upgrade_t0 = time.time()
        print("upgrading snapshot ->", upgraded_snapshot_path, flush=True)
        try:
            t_save0 = time.time()
            print("upgrade step: writing upgraded snapshot JSON...", flush=True)
            SnapshotCodec(namespace).save(runtime.graph, temp_snapshot_path)
            t_save1 = time.time()
            try:
                tmp_size = os.path.getsize(temp_snapshot_path)
            except OSError:
                tmp_size = None
            if tmp_size is None:
                print(f"upgrade step: write complete ({t_save1 - t_save0:.2f}s), atomically replacing...", flush=True)
            else:
                print(f"upgrade step: write complete ({t_save1 - t_save0:.2f}s, {tmp_size} bytes), atomically replacing...", flush=True)
            os.replace(temp_snapshot_path, upgraded_snapshot_path)
            t_rep = time.time()
            runtime.snapshot_upgraded = M.truth_value
            print("saved upgraded snapshot to", upgraded_snapshot_path, flush=True)
            print("upgrade source snapshot was", snapshot_path, flush=True)
            print(f"upgrade timing: save={t_save1 - t_save0:.2f}s replace={t_rep - t_save1:.2f}s total={t_rep - upgrade_t0:.2f}s", flush=True)
        except OSError as exc:
            print(
                "WARNING: failed to save upgraded snapshot to "
                + upgraded_snapshot_path
                + " ("
                + "".join(traceback.format_exception_only(exc)).strip()
                + ")",
                flush=True,
            )
            print("upgrade temp path was " + temp_snapshot_path, flush=True)
            try:
                if os.path.exists(temp_snapshot_path):
                    try:
                        tmp_size = os.path.getsize(temp_snapshot_path)
                    except OSError:
                        tmp_size = None
                    if tmp_size is None:
                        print("upgrade cleanup: removing temp snapshot", flush=True)
                    else:
                        print(f"upgrade cleanup: removing temp snapshot ({tmp_size} bytes)", flush=True)
                    os.remove(temp_snapshot_path)
            except OSError:
                pass

    return runtime


def save_runtime(runtime, snapshot_path, namespace, deadline=None, progress=M.false_value):
    sync_started_at = time.monotonic()
    if deadline is not None:
        print(
            "snapshot save: namespace synchronization starting ("
            + format(deadline.require_remaining("namespace synchronization"), ".1f")
            + "s remaining)",
            flush=True,
        )
    namespace = _sync_live_namespace(namespace, deadline)
    if deadline is not None:
        print(
            "snapshot save: namespace synchronization complete in "
            + format(time.monotonic() - sync_started_at, ".2f")
            + "s ("
            + format(deadline.require_remaining("namespace synchronization"), ".1f")
            + "s remaining)",
            flush=True,
        )
    codec = SnapshotCodec(namespace)
    codec.save(runtime.graph, snapshot_path, progress=progress, deadline=deadline)
    return snapshot_path


__all__ = tuple(name for name in globals() if not name.startswith("_"))
