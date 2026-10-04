"""Run geometry SearchDFS examples with explicit per-example manifests.

The original aggregate fixture used one example's start and one mixed rule list
for fifteen goals. This runner gives each example its own start, goal, and rule
manifest. Examples with no sound manifest on the current pack are reported as
BLOCKED instead of being padded with synthetic premises.
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

# Each rule reference is (pack name, rule id). A BLOCKED entry is deliberate:
# its current example start lacks a premise required by every available rule
# that could produce the goal, so the runner must not fabricate that premise.
RULE_MANIFESTS = {
    "tao_problem_1_1_triangle": {
        "status": "RUN",
        "rules": (("geometry", "tao_side_alpha_from_area_perimeter"),),
    },
    "tao_side_beta": {
        "status": "RUN",
        "rules": (("geometry", "tao_side_beta_from_area_perimeter"),),
    },
    "tao_side_gamma": {
        "status": "RUN",
        "rules": (("geometry", "tao_side_gamma_from_area_perimeter"),),
    },
    "tao_angle_alpha": {
        "status": "BLOCKED",
        "reason": "start lacks Triangle and Distinct premises required by tao_angle_from_sides",
    },
    "tao_angle_beta": {
        "status": "BLOCKED",
        "reason": "start lacks Triangle and Distinct premises required by tao_angle_from_sides",
    },
    "tao_angle_gamma": {
        "status": "BLOCKED",
        "reason": "start lacks Triangle and Distinct premises required by tao_angle_from_sides",
    },
    "tao_perimeter_identity": {
        "status": "RUN",
        "rules": (
            ("geometry", "tao_side_alpha_from_area_perimeter"),
            ("geometry", "tao_side_beta_from_area_perimeter"),
            ("geometry", "tao_side_gamma_from_area_perimeter"),
            ("geometry", "tao_verify_perimeter"),
        ),
    },
    "tao_area_identity": {
        "status": "RUN",
        "rules": (("geometry", "tao_verify_area"),),
    },
    "tao_positive_alpha_side": {
        "status": "RUN",
        "rules": (
            ("geometry", "tao_perimeter_third_positive"),
            ("geometry", "tao_verify_positive_alpha_side"),
        ),
    },
    "tao_positive_beta_side": {
        "status": "RUN",
        "rules": (
            ("geometry", "tao_perimeter_third_positive"),
            ("geometry", "tao_verify_positive_beta_side"),
        ),
    },
    "tao_positive_gamma_side": {
        "status": "RUN",
        "rules": (
            ("geometry", "tao_perimeter_third_positive"),
            ("geometry", "tao_verify_positive_gamma_side"),
        ),
    },
    "tao_strict_triangle_inequality": {
        "status": "RUN",
        "rules": (("geometry", "tao_verify_strict_triangle_inequality"),),
    },
    "tao_cosine_alpha_identity": {
        "status": "RUN",
        "rules": (
            ("geometry", "tao_side_alpha_from_area_perimeter"),
            ("geometry", "tao_side_beta_from_area_perimeter"),
            ("geometry", "tao_side_gamma_from_area_perimeter"),
            ("geometry", "tao_angle_from_sides"),
            ("trigonometry", "triangle_yields_generic_cosine_relation"),
        ),
    },
    "tao_cosine_beta_identity": {
        "status": "RUN",
        "rules": (
            ("geometry", "tao_side_alpha_from_area_perimeter"),
            ("geometry", "tao_side_beta_from_area_perimeter"),
            ("geometry", "tao_side_gamma_from_area_perimeter"),
            ("geometry", "tao_angle_from_sides"),
            ("trigonometry", "triangle_yields_generic_cosine_relation"),
        ),
    },
    "tao_cosine_gamma_identity": {
        "status": "RUN",
        "rules": (
            ("geometry", "tao_side_alpha_from_area_perimeter"),
            ("geometry", "tao_side_beta_from_area_perimeter"),
            ("geometry", "tao_side_gamma_from_area_perimeter"),
            ("geometry", "tao_angle_from_sides"),
            ("trigonometry", "triangle_yields_generic_cosine_relation"),
        ),
    },
}


def run_one(index: int) -> None:
    from cat_theo_machine.runtime import boot_from_packs
    from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
    from cat_theo_machine import machine as M
    from cat_theo_machine import proof as P
    from cat_theo_machine import search as S

    example = EXAMPLES[index]
    manifest = RULE_MANIFESTS[example]
    if manifest["status"] == "BLOCKED":
        print(
            "RESULT "
            + json.dumps(
                {
                    "index": index + 1,
                    "example": example,
                    "status": "BLOCKED",
                    "reason": manifest["reason"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return

    P.SetDebugTrace(M.false_value)()
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    registry = M.FromContextGetConstructors(runtime.graph)()
    geometry = packs.by_name("geometry")
    start, goal_raw = geometry.examples[example]
    goal = P.NormalizeKnowledge(goal_raw, registry)()

    rules = M.EmptyList
    for pack_name, rule_id in reversed(manifest["rules"]):
        rules = M.Pair(packs.by_name(pack_name).rule_map[rule_id], rules)

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
                "example": example,
                "status": status,
                "outcome_class": type(outcome).__name__,
                "elapsed_seconds": elapsed,
                "rules": manifest["rules"],
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
        manifest = RULE_MANIFESTS[example]
        if manifest["status"] == "BLOCKED":
            row = {
                "index": index + 1,
                "example": example,
                "status": "BLOCKED",
                "reason": manifest["reason"],
            }
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
            continue
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
                row = {
                    "index": index + 1,
                    "example": example,
                    "status": "ERROR",
                    "elapsed_seconds": round(time.time() - started, 3),
                    "exit_code": completed.returncode,
                    "stdout_tail": _tail_text(completed.stdout),
                    "stderr_tail": _tail_text(completed.stderr),
                }
            else:
                row = json.loads(result_line[len("RESULT ") :])
                row["exit_code"] = completed.returncode
        except subprocess.TimeoutExpired as error:
            row = {
                "index": index + 1,
                "example": example,
                "status": "TIMEOUT",
                "timeout_seconds": timeout_seconds,
                "elapsed_seconds": round(time.time() - started, 3),
                "stdout_tail": _tail_text(error.stdout),
                "stderr_tail": _tail_text(error.stderr),
            }
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    runnable = [row for row in rows if row["status"] != "BLOCKED"]
    output = {
        "fixture": "geometry examples, independent starts/goals with per-example manifests",
        "manifests": RULE_MANIFESTS,
        "timeout_seconds_per_example": timeout_seconds,
        "results": rows,
        "runnable_all_success": all(row["status"] == "SUCCESS" for row in runnable),
        "blocked_examples": sum(row["status"] == "BLOCKED" for row in rows),
    }
    output_path = os.path.join(root, "verification", "odr-cl0", "searchdfs-independent-results.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return 0 if output["runnable_all_success"] else 1


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
