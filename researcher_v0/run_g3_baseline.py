"""Runner for the Researcher-v0 G3 BASELINE laboratory run.

    python3 -m cat_theo_machine.researcher_v0.run_g3_baseline

Run it from the directory that contains the repository (`/home/user`), the
same place the G1/G2 runners are run from.

Order, and nothing else:

1. binding — regenerate the G2 rows and require their JSONL rendering to
   reproduce `tasks/tasks.jsonl` byte for byte. On any difference the run
   halts before a task runs and nothing is written (exit 1);
2. selection — one representative per canonical id, in delivered order;
3. BASELINE — each representative attempted once, mining off, under the
   budget declared in `laboratory`;
4. artifacts — `journals/baseline.jsonl` and
   `certificates/baseline_path_certificates.jsonl`;
5. summary — one line per attempt and the footer counts, printed.

MINING is not run (G4/G5). No invariant is proved, nothing is pruned, and this
code path cannot issue an unreachability result.
"""

from __future__ import annotations

import hashlib
import os
import sys

from .. import machine as M
from . import laboratory as LAB
from . import task_generation as G


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    handle = open(os.path.join(here, "tasks", "tasks.jsonl"))
    delivered = handle.read()
    handle.close()

    kept = M.Head(G.DropExactDuplicates(G.GenerateAllRows()())())()
    if G.RowsToJsonl(kept)() != delivered:
        print("HALT: regenerated rows do not reproduce tasks/tasks.jsonl;")
        print("      nothing run, nothing written.")
        sys.exit(1)
    digest = hashlib.blake2b(delivered.encode("utf-8"), digest_size=32).hexdigest()
    print("binding: regenerated rows reproduce tasks/tasks.jsonl byte for byte")
    print("         blake2b-256 " + digest)

    representatives = LAB.CanonicalRepresentatives(kept)()
    run = LAB.BaselineRun(
        representatives, LAB.EXPANSION_BUDGET, LAB.WALL_CLOCK_BUDGET_MS
    )()
    attempts = M.Head(run)()

    journal = LAB.JournalText(
        attempts,
        digest,
        G.CountRows(kept)(),
        G.CountDistinctCanonical(kept)(),
        LAB.EXPANSION_BUDGET,
        LAB.WALL_CLOCK_BUDGET_MS,
    )()
    certificates = LAB.CertificatesText(attempts)()

    journals_dir = os.path.join(here, "journals")
    certificates_dir = os.path.join(here, "certificates")
    if not os.path.isdir(journals_dir):
        os.makedirs(journals_dir)
    if not os.path.isdir(certificates_dir):
        os.makedirs(certificates_dir)
    LAB.WriteArtifact(os.path.join(journals_dir, "baseline.jsonl"), journal)()
    LAB.WriteArtifact(
        os.path.join(certificates_dir, "baseline_path_certificates.jsonl"), certificates
    )()

    print("")
    print("G3 BASELINE (mining off), budget " + str(LAB.EXPANSION_BUDGET)
          + " expansions / " + str(LAB.WALL_CLOCK_BUDGET_MS) + " ms per task, workers "
          + str(LAB.MAX_WORKERS) + ", seed " + LAB.SEED_TEXT)
    remaining = attempts
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        attempt = M.Head(remaining)()
        cited = LAB.AttemptCertificateIdText(attempt)()
        if cited != "":
            cited = cited[:21]
        print(
            "  " + LAB.AttemptTaskIdText(attempt)()
            + "  " + LAB.AttemptOutcome(attempt)()().ljust(18)
            + "  expansions " + str(LAB.AttemptExpansions(attempt)()).rjust(2)
            + "  " + str(LAB.AttemptElapsed(attempt)()).rjust(6) + " ms"
            + "  " + LAB.AttemptMembers(attempt)()().ljust(12)
            + "  " + cited
        )
        remaining = M.Tail(remaining)()
    print("")
    print(LAB.JournalFooterJson(attempts)())
    print("")
    print("wrote researcher_v0/journals/baseline.jsonl")
    print("wrote researcher_v0/certificates/baseline_path_certificates.jsonl")
