"""Run the bounded Researcher-v0 G5 in-run use gate.

    cd /home/user
    PYTHONPATH=/home/user /home/user/.venv/bin/python \
      -m cat_theo_machine.researcher_v0.run_g5_use
"""

from __future__ import annotations

import os
import sys

from .. import machine as M
from . import in_run_use as U
from . import laboratory as L
from . import mining as X
from . import task_generation as G
from . import token_domain as D
from . import use_checker as C


if M.Compare(M.Char(__name__), M.Char("__main__"))() is M.truth_value:
    here = os.path.dirname(os.path.abspath(__file__))
    handle = open(os.path.join(here, "tasks", "tasks.jsonl"))
    delivered = handle.read()
    handle.close()
    kept = M.Head(G.DropExactDuplicates(G.GenerateAllRows()())())()
    if M.Compare(M.Char(G.RowsToJsonl(kept)()), M.Char(delivered))() is M.false_value:
        print("HALT: regenerated rows do not reproduce tasks/tasks.jsonl")
        sys.exit(1)
    representatives = L.CanonicalRepresentatives(kept)()
    print("binding: regenerated rows reproduce tasks/tasks.jsonl byte for byte")
    print("running G5 MINING with in-run use: K=5, exact-scope pruning on")
    run = U.InRunUse(
        representatives, L.EXPANSION_BUDGET, L.WALL_CLOCK_BUDGET_MS
    )()
    attempts = U.RunAttempts(run)()
    events = U.RunEvents(run)()
    event_text = U.PruneEventsText(events)()
    certificates_dir = os.path.join(here, "certificates")
    try:
        os.makedirs(certificates_dir)
    except FileExistsError:
        pass
    L.WriteArtifact(
        os.path.join(certificates_dir, "prune_events.jsonl"), event_text
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
        + " checked_unreachable="
        + str(L.OutcomeCount(attempts, C.CheckedUnreachableTag()())())
        + " budget="
        + str(L.OutcomeCount(attempts, L.BudgetExhaustedTag()())())
        + " unsupported="
        + str(L.OutcomeCount(attempts, L.UnsupportedTag()())())
        + " open_residual="
        + str(L.OutcomeCount(attempts, L.OpenResidualTag()())())
        + " execution_failure="
        + str(L.OutcomeCount(attempts, L.ExecutionFailureTag()())())
    )
    print(
        "sweeps="
        + X.SweepSeqText(U.RunSweepSeqs(run)())()
        + " candidates="
        + str(X.ChainCount(U.RunCandidates(run)())())
        + " proved="
        + str(X.ChainCount(U.RunProved(run)())())
        + " prune_events="
        + str(X.ChainCount(events)())
        + " scope_checks="
        + str(X.ChainCount(U.RunScopeChecks(run)())())
    )
    print("wrote researcher_v0/certificates/prune_events.jsonl")
