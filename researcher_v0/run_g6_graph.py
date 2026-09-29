"""Build the bounded Researcher-v0 G6 inert discovery graph.

    cd /home/user
    PYTHONPATH=/home/user /home/user/.venv/bin/python \
      -m cat_theo_machine.researcher_v0.run_g6_graph

All deterministic cited artifacts are rebound byte for byte and the elapsed-time
MINING journal is required to be present before the two G6-only reporting files
are written. The graph has no activation or live-write path.
"""

from __future__ import annotations

import os
import sys

from .. import machine as M
from . import discovery_graph as DG
from . import in_run_use as U
from . import laboratory as L
from . import mining as X
from . import task_generation as G


if M.Compare(M.Char(__name__), M.Char("__main__"))() is M.truth_value:
    here = os.path.dirname(os.path.abspath(__file__))
    task_handle = open(os.path.join(here, "tasks", "tasks.jsonl"))
    delivered_tasks = task_handle.read()
    task_handle.close()
    journal_handle = open(os.path.join(here, "journals", "mining.jsonl"))
    delivered_journal = journal_handle.read()
    journal_handle.close()
    path_handle = open(
        os.path.join(here, "certificates", "baseline_path_certificates.jsonl")
    )
    delivered_paths = path_handle.read()
    path_handle.close()
    candidate_handle = open(os.path.join(here, "candidates", "candidates.jsonl"))
    delivered_candidates = candidate_handle.read()
    candidate_handle.close()
    proved_handle = open(
        os.path.join(here, "candidates", "proved_invariants.jsonl")
    )
    delivered_proved = proved_handle.read()
    proved_handle.close()
    refuted_handle = open(
        os.path.join(here, "candidates", "refuted_candidates.jsonl")
    )
    delivered_refuted = refuted_handle.read()
    refuted_handle.close()
    prune_handle = open(
        os.path.join(here, "certificates", "prune_events.jsonl")
    )
    delivered_prunes = prune_handle.read()
    prune_handle.close()

    kept = M.Head(G.DropExactDuplicates(G.GenerateAllRows()())())()
    if M.Compare(
        M.Char(G.RowsToJsonl(kept)()), M.Char(delivered_tasks)
    )() is M.false_value:
        print("HALT: tasks/tasks.jsonl did not rebind; nothing written")
        sys.exit(1)
    representatives = L.CanonicalRepresentatives(kept)()
    mining_run = X.MiningRun(
        representatives, L.EXPANSION_BUDGET, L.WALL_CLOCK_BUDGET_MS
    )()
    if M.Compare(M.Char(delivered_journal), M.Char(""))() is M.truth_value:
        print("HALT: journals/mining.jsonl is missing; nothing written")
        sys.exit(1)
    if M.Compare(
        M.Char(L.CertificatesText(X.RunAttempts(mining_run)())()),
        M.Char(delivered_paths),
    )() is M.false_value:
        print("HALT: baseline path certificates did not rebind; nothing written")
        sys.exit(1)
    if M.Compare(
        M.Char(X.CandidatesText(X.RunCandidates(mining_run)())()),
        M.Char(delivered_candidates),
    )() is M.false_value:
        print("HALT: candidates/candidates.jsonl did not rebind; nothing written")
        sys.exit(1)
    if M.Compare(
        M.Char(X.ProvedText(X.RunProved(mining_run)())()), M.Char(delivered_proved)
    )() is M.false_value:
        print("HALT: candidates/proved_invariants.jsonl did not rebind; nothing written")
        sys.exit(1)
    if M.Compare(
        M.Char(X.RefutedText(X.RunRefuted(mining_run)())()),
        M.Char(delivered_refuted),
    )() is M.false_value:
        print("HALT: candidates/refuted_candidates.jsonl did not rebind; nothing written")
        sys.exit(1)

    use_run = U.InRunUse(
        representatives, L.EXPANSION_BUDGET, L.WALL_CLOCK_BUDGET_MS
    )()
    if M.Compare(
        M.Char(U.PruneEventsText(U.RunEvents(use_run)())()),
        M.Char(delivered_prunes),
    )() is M.false_value:
        print("HALT: certificates/prune_events.jsonl did not rebind; nothing written")
        sys.exit(1)

    graph = DG.DiscoveryGraph(kept, mining_run, use_run)()
    graph_text = DG.DiscoveryGraphJson(graph)()
    summary_text = DG.DiscoveryGraphSummary(graph)()
    L.WriteArtifact(os.path.join(here, "discovery_graph.json"), graph_text)()
    L.WriteArtifact(
        os.path.join(here, "discovery_graph_summary.md"), summary_text
    )()
    print("binding: deterministic source artifacts reproduce; MINING journal present")
    print(
        "graph nodes="
        + str(X.ChainCount(DG.PartNodes(graph)())())
        + " edges="
        + str(X.ChainCount(DG.PartEdges(graph)())())
    )
    print("status: inert reporting graph; no activation or live write")
    print("wrote researcher_v0/discovery_graph.json")
    print("wrote researcher_v0/discovery_graph_summary.md")
