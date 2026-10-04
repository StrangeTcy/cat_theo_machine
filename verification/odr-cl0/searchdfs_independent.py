"""Run the geometry SearchDFS examples independently.

This replaces the invalid aggregate fixture for diagnosis. Each child process
gets one example's own start and goal, so a failure cannot be caused by sharing
the first example's one-fact start across fifteen goals.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time


EXAMPLES = (
    "tao_problem_1_1_triangle",
    "tao_side_beta",
    "tao_side_gamma",
    "tao_angle_alpha",
    "tao_angle_beta",
    "tao_angle_gamma",
    "tao_perimeter_identity",
    "tao_area_identity",
    "tao_positive_alpha_side",
    "tao_positive_beta_side",
    "tao_positive_gamma_side",
    "tao_strict_triangle_inequality",
    "tao_cosine_alpha_identity",
    "tao_cosine_beta_identity",
    "tao_cosine_gamma_identity",
)

RULE_IDS = (
    "tao_side_alpha_from_area_perimeter",
    "tao_side_beta_from_area_perimeter",
    "tao_side_gamma_from_area_perimeter",
    "tao_angle_from_sides",
    "tao_angle_from_sides",
    "tao_angle_from_sides",
    "tao_verify_perimeter",
    "tao_verify_area",
    "tao_verify_positive_alpha_side",
    "tao_verify_positive_beta_side",
    "tao_verify_positive_gamma_side",
    "tao_verify_strict_triangle_inequality",
    "tao_expand_alpha_angle_value",
    "tao_expand_beta_angle_value",
    "tao_expand_gamma_angle_value",
)


def run_one(index: int) -> None:
    from cat_theo_machine.runtime import boot_from_packs
    from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
    from cat_theo_machine import machine as M
    from cat_theo_machine import proof as P
    from cat_theo_machine import search as S

    P.SetDebugTrace(M.false_value)()
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    registry = M.FromContextGetConstructors(runtime.graph)()
    pack = packs.by_name("geometry")
    start, goal_raw = pack.examples[EXAMPLES[index]]
    goal = P.NormalizeKnowledge(goal_raw, registry)()

    rules = M.EmptyList
    for rule_id in reversed(RULE_IDS):
        rules = M.Pair(pack.rule_map[rule_id], rules)

    runtime.graph._search_disable_console = M.truth_value
    runtime.graph._search_disable_progress_ticker = M.truth_value
    heuristic = M.Heuristic(
        M.DFSLabel,
        M.InsertionOrderLabel,
        M.Zero,
        M.one,
        M.one,
        M.Zero,
    )()

    started = time.time()
    result = S.SearchDFS(runtime.graph, start, goal, rules, heuristic, registry)()
    elapsed = round(time.time() - started, 3)
    cost = M.Head(M.Tail(result)())()
    outcome = S.SearchCostOutcome(cost)()
    if outcome is S.SearchSuccessLabel:
        status = "SUCCESS"
    elif outcome is S.SearchFailureLabel:
        status = "FAILURE"
    elif outcome is S.SearchTimedOutLabel:
        status = "TIMED_OUT"
    elif outcome is S.SearchPausedLabel:
        status = "PAUSED"
    else:
        status = "OTHER"

    print(
        "RESULT "
        + json.dumps(
            {
                "index": index + 1,
                "example": EXAMPLES[index],
                "status": status,
                "outcome_class": type(outcome).__name__,
                "elapsed_seconds": elapsed,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def _tail_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[-2000:]
    return str(value)[-2000:]


def run_all(timeout_seconds: int) -> int:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    parent = os.path.dirname(root)
    env = os.environ.copy()
    env["PYTHONPATH"] = parent + os.pathsep + env.get("PYTHONPATH", "")
    rows = []

    for index, example in enumerate(EXAMPLES):
        started = time.time()
        try:
            completed = subprocess.run(
                [sys.executable, __file__, "--index", str(index)],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            result_line = next(
                (line for line in completed.stdout.splitlines() if line.startswith("RESULT ")),
                None,
            )
            if result_line is None:
                rows.append(
                    {
                        "index": index + 1,
                        "example": example,
                        "status": "ERROR",
                        "elapsed_seconds": round(time.time() - started, 3),
                        "exit_code": completed.returncode,
                        "stdout_tail": _tail_text(completed.stdout),
                        "stderr_tail": _tail_text(completed.stderr),
                    }
                )
            else:
                row = json.loads(result_line[len("RESULT ") :])
                row["exit_code"] = completed.returncode
                rows.append(row)
        except subprocess.TimeoutExpired as error:
            rows.append(
                {
                    "index": index + 1,
                    "example": example,
                    "status": "TIMEOUT",
                    "timeout_seconds": timeout_seconds,
                    "elapsed_seconds": round(time.time() - started, 3),
                    "stdout_tail": _tail_text(error.stdout),
                    "stderr_tail": _tail_text(error.stderr),
                }
            )
        print(json.dumps(rows[-1], sort_keys=True), flush=True)

    output = {
        "fixture": "geometry examples, independent starts/goals",
        "rule_ids": RULE_IDS,
        "timeout_seconds_per_example": timeout_seconds,
        "results": rows,
        "all_success": all(row["status"] == "SUCCESS" for row in rows),
    }
    output_path = os.path.join(root, "verification", "odr-cl0", "searchdfs-independent-results.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return 0 if output["all_success"] else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    if args.index is not None:
        run_one(args.index)
        return 0
    return run_all(args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
