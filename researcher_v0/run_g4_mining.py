"""Run the bounded Researcher-v0 G4 MINING condition.

    cd /home/user
    /home/user/.venv/bin/python -m cat_theo_machine.researcher_v0.run_g4_mining

The delivered task bytes are rebound before execution.  The run uses the same
34 canonical representatives and 32-expansion / 60000-ms / one-worker budget
as G3.  INV-0 runs every five completed tasks and at the final remainder.
No candidate or proved invariant is supplied to search, so this gate performs
no pruning.
"""

from __future__ import annotations

import os
import sys

from .. import machine as M
from . import laboratory as L
from . import mining as X
from . import task_generation as G
from . import token_domain as D


if M.Compare(M.Char(__name__), M.Char("__main__"))() is M.truth_value:
    here = os.path.dirname(os.path.abspath(__file__))
    task_path = os.path.join(here, "tasks", "tasks.jsonl")
    handle = open(task_path)
    delivered = handle.read()
    handle.close()

    kept = M.Head(G.DropExactDuplicates(G.GenerateAllRows()())())()
    if M.Compare(M.Char(G.RowsToJsonl(kept)()), M.Char(delivered))() is M.false_value:
        print("HALT: regenerated rows do not reproduce tasks/tasks.jsonl;")
        print("      nothing run, nothing written.")
        sys.exit(1)
    digest = "b89ac1f5742ea7bbb03bffa59fc10efab7a4ab27b522edbc014d3448882ec90c"
    representatives = L.CanonicalRepresentatives(kept)()
    print("binding: regenerated rows reproduce tasks/tasks.jsonl byte for byte")
    print("         G3 task-set binding " + digest)
    print("running MINING: K=5, pruning off")

    run = X.MiningRun(
        representatives, L.EXPANSION_BUDGET, L.WALL_CLOCK_BUDGET_MS
    )()
    attempts = X.RunAttempts(run)()
    journal = X.MiningJournalText(
        run,
        digest,
        G.CountRows(kept)(),
        G.CountDistinctCanonical(kept)(),
        L.EXPANSION_BUDGET,
        L.WALL_CLOCK_BUDGET_MS,
        5,
    )()
    candidates = X.CandidatesText(X.RunCandidates(run)())()
    proved = X.ProvedText(X.RunProved(run)())()
    refuted = X.RefutedText(X.RunRefuted(run)())()

    journals_dir = os.path.join(here, "journals")
    candidates_dir = os.path.join(here, "candidates")
    try:
        os.makedirs(journals_dir)
    except FileExistsError:
        pass
    try:
        os.makedirs(candidates_dir)
    except FileExistsError:
        pass
    L.WriteArtifact(os.path.join(journals_dir, "mining.jsonl"), journal)()
    L.WriteArtifact(os.path.join(candidates_dir, "candidates.jsonl"), candidates)()
    L.WriteArtifact(
        os.path.join(candidates_dir, "proved_invariants.jsonl"), proved
    )()
    L.WriteArtifact(
        os.path.join(candidates_dir, "refuted_candidates.jsonl"), refuted
    )()

    totals = L.AttemptTotals(attempts)()
    print(
        "completed="
        + str(L.OutcomeCountAll(attempts)())
        + " expansions="
        + str(M.Head(D.HeadAt(totals, 0)())())
    )
    print(
        "outcomes checked_reachable="
        + str(L.OutcomeCount(attempts, L.CheckedReachableTag()())())
        + " open_residual="
        + str(L.OutcomeCount(attempts, L.OpenResidualTag()())())
        + " budget="
        + str(L.OutcomeCount(attempts, L.BudgetExhaustedTag()())())
        + " unsupported="
        + str(L.OutcomeCount(attempts, L.UnsupportedTag()())())
        + " execution_failure="
        + str(L.OutcomeCount(attempts, L.ExecutionFailureTag()())())
    )
    print(
        "sweeps="
        + X.SweepSeqText(X.RunSweepSeqs(run)())()
        + " candidates="
        + str(X.ChainCount(X.RunCandidates(run)())())
        + " proved="
        + str(X.ChainCount(X.RunProved(run)())())
        + " refuted_or_unsupported="
        + str(X.ChainCount(X.RunRefuted(run)())())
    )
    print("wrote researcher_v0/journals/mining.jsonl")
    print("wrote researcher_v0/candidates/candidates.jsonl")
    print("wrote researcher_v0/candidates/proved_invariants.jsonl")
    print("wrote researcher_v0/candidates/refuted_candidates.jsonl")
