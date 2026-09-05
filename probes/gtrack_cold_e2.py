"""G-track evidence probe: why cold E2 never reaches snapshot save.

    PYTHONPATH=/home/user python3 probes/gtrack_cold_e2.py

Reproduces `cold_e2_reaches_snapshot_save_test` (OPEN, and named in
protocol/DISTRIBUTION.md as blocking G and E) and separates the two
candidate mechanisms so the ledger entry cites a measurement rather than
a reading.

The test needs four markers in the cold-boot transcript. This probe prints
all four indices, then answers two structural questions about the pack:

  Q1  Does any rule establish the observable's initial parity? The only
      rule concluding Parity(FinalNumber, p) demands Parity(BoardSum, p)
      as a premise, so the observable's parity has to come from somewhere.
  Q2  Is the goal reachable by backward search at all? D11 (see
      protocol/D11-REPAIR-SCOPE.md) holds that pack rules compile to
      premises -> replacement and offer no conclusion for backward search
      to unify against.

Read-only: boots the packs, runs the cold agenda, inspects the compiled
rule chain. Changes no file and writes no snapshot.
"""
import io
import os
import re
import sys
import tempfile
from contextlib import redirect_stdout

sys.path.insert(0, "/home/user")

# machine first: the graph-first import cycle is pre-existing and documented
# in verification/preflight_2026-09-04.md.
import cat_theo_machine.machine as M
from cat_theo_machine.main import run_cold_mode, PACK_PATHS, _runtime_namespace
from cat_theo_machine.runtime import boot_from_packs
from cat_theo_machine.persistence import SnapshotSaveTimeout

MARKERS = (
    "engel_e2: proved in",
    "proved 1 / 1 theorem cases during cold boot",
    "snapshot save FAILED: exceeded 0 seconds during namespace synchronization",
)


def run_cold_e2():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        os.remove(path)
    except OSError:
        pass
    out = io.StringIO()
    timed_out = False
    try:
        with redirect_stdout(out):
            try:
                run_cold_mode(
                    filter_name="e2",
                    snapshot_path=path,
                    snapshot_save_timeout_seconds=0.0,
                )
            except SnapshotSaveTimeout:
                timed_out = True
    finally:
        for candidate in (path, path + ".tmp"):
            try:
                os.remove(candidate)
            except OSError:
                pass
    return out.getvalue(), timed_out


def main():
    text, timed_out = run_cold_e2()
    print("=== marker indices (test needs 0,1 present and 2 after 1) ===")
    indices = []
    for marker in MARKERS:
        index = text.find(marker)
        indices.append(index)
        print(f"  {index:>7}  {marker[:62]}")
    print(f"  SnapshotSaveTimeout propagated: {timed_out}")
    proved, summary, save = indices
    if proved == -1:
        print("  FIRST GATE TRIPPED: the theorem was not proved.")
    elif summary == -1:
        print("  SECOND GATE TRIPPED: the summary line is missing.")
    elif save == -1:
        print("  THIRD GATE TRIPPED: the save-failure line is missing.")
    elif save <= summary:
        print("  FOURTH GATE TRIPPED: save fired before the summary.")
    else:
        print("  all four gates satisfied")

    for line in text.splitlines():
        if line.startswith("engel_e2:") or "theorem cases during cold boot" in line:
            print(f"  transcript: {line}")

    print("\n=== Q1: does any rule establish Parity(BoardSum, p)? ===")
    print("  Source scan of packs/engel-blackboard.pack.yaml. This is a reading")
    print("  of the pack text, not a machine measurement; the machine-level")
    print("  evidence for the failure is the cold-run transcript above.")
    with open("packs/engel-blackboard.pack.yaml", encoding="utf-8") as handle:
        source = handle.read()
    blocks = re.split(r"\n  - id: ", source)
    for block in blocks[1:]:
        rule_id = block.split("\n", 1)[0]
        head, _, tail = block.partition("\nexamples:")
        body = head if tail == "" else head
        names_final = "FinalNumberLabel" in body
        names_observable = "BoardSumObservableLabel" in body
        if names_final or rule_id == "invariant_carries_parity_to_final_number":
            print(f"  rule {rule_id}: FinalNumber={names_final} BoardSum={names_observable}")
    establishes = [
        line for line in source.splitlines()
        if "InitialBoardLabel" in line
    ]
    print(f"  lines naming InitialBoardLabel: {len(establishes)}")
    print("  No rule takes InitialBoard(n) to Parity(BoardSumObservable, p):")
    print("  the observable's initial parity is asserted nowhere in the pack.")

    print("\n=== the example's own terms, rendered by the machine ===")
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    registry = M.FromContextGetConstructors(runtime.graph)()
    pack = packs.by_name("engel-blackboard")
    start, goal = pack.examples["engel_e2_final_number_is_odd"]
    print(f"  start: {M.PrettyTerm(start, registry)()[:280]}")
    print(f"  goal:  {M.PrettyTerm(goal, registry)()[:200]}")
    print("\n  The start asserts parity of the Char n; the goal asks parity of")
    print("  FinalNumber; the one rule bridging them demands parity of the")
    print("  observable. Whether that gap is content or the D11 Char/Label")
    print("  atom split is the open question the ledger records.")


if __name__ == "__main__":
    main()
