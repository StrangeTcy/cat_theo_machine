"""Citation content-check for process-agents-plan.md.

A range check (does line N exist in file F) accepts off-by-one drift, which is the common
failure after any edit to a cited file. This asserts the cited symbol appears on the cited
line. Default mode is exact (window 0); --window N widens the search for triage only.

Measured on this plan's own history: the exact mode catches all three citation errors made
while writing the plan (compare_subprocess.py:281 vs :280, main.py:1305 vs :1232,
planner.py:494 vs :485) and two more that a +/-2 window passed. A window of 2 is therefore
not safe as a default: it accepts the off-by-one it exists to catch.

Usage:  python3 tools/check_plan_citations.py [--window N]
Exit 0 = every citation verified. Exit 1 = at least one citation failed.
"""

import os
import re
import sys

WINDOW = 0

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(REPO_ROOT, "process-agents-plan.md")

# (file, line, symbol) triples lifted from process-agents-plan.md.
# Update this list whenever a citation in the plan changes.
CITATIONS = [
    ("gmprep.py", 3, "import gmpy2"),
    ("packs.py", 334, "import yaml"),
    ("main.py", 24, "subprocess.run"),
    ("main.py", 703, "def _search_worker_checkpoint"),
    ("main.py", 749, "def run_search_worker_mode"),
    ("main.py", 1117, "def run_test_mode"),
    ("main.py", 1232, "def _terminate_active_children"),
    ("main.py", 1292, "search-worker"),
    ("main.py", 1303, "_terminate_active_children()"),
    ("main.py", 1308, "freeze_support"),
    ("planner.py", 413, "class PlannerAlternative"),
    ("planner.py", 423, "def __init__(self, parent_obligation_id"),
    ("planner.py", 449, "class PlannerAlternativeParent"),
    ("planner.py", 485, "class PlannerAlternativeEvidence"),
    ("planner.py", 458, "class PlannerAlternativeMethod"),
    ("planner.py", 467, "class PlannerAlternativeChildren"),
    ("planner.py", 476, "class PlannerAlternativeStatus"),
    ("persistence.py", 420, "class SnapshotCodec"),
    ("persistence.py", 421, "ROOT_NAMES"),
    ("persistence.py", 562, 'get_context("spawn")'),
    ("persistence.py", 565, "ctx.Process"),
    ("persistence.py", 647, 'get_context("spawn")'),
    ("persistence.py", 658, "ctx.Process"),
    ("runtime.py", 1708, "def boot_from_snapshot"),
    ("runtime.py", 1790, "def save_runtime"),
    ("search/compare.py", 201, 'get_context("spawn")'),
    ("search/compare.py", 251, 'get_context("spawn")'),
    ("search/compare_executors.py", 265, "def _spawn_parallel_executor"),
    ("search/compare_executors.py", 271, "mp_context.Process"),
    ("search/compare_executors.py", 293, "def _await_parallel_executor_ready"),
    ("search/compare_executors.py", 656, "def _fill_parallel_workers"),
    ("search/compare_executors.py", 662, "_comparison_states_need_shared_root_wave"),
    ("search/compare_executors.py", 689, "launchable_workers"),
    ("search/compare_packets.py", 1393, "def _comparison_cache_shared_root_candidates"),
    ("search/compare_packets.py", 1410, "_comparison_shared_root_candidates_ready = M.truth_value"),
    ("search/compare_packets.py", 1429, "def _comparison_prepare_shared_root_wave"),
    ("search/compare_packets.py", 1436, "_comparison_state_status"),
    ("search/compare_packets.py", 1440, "_comparison_is_fresh_root_job"),
    ("search/compare_packets.py", 1455, "_comparison_cache_shared_root_candidates"),
    ("search/compare_subprocess.py", 267, "HYGE_SEARCH_WORKER_RESUME_DERIVATION"),
    ("search/compare_subprocess.py", 268, "subprocess.Popen"),
    ("search/compare_subprocess.py", 278, "threading.Thread"),
    ("search/compare_subprocess.py", 280, "exit_code = process.wait()"),
    ("search/compare_subprocess.py", 281, "thread.join"),
    ("search/compare_subprocess.py", 283, "_load_search_worker_snapshot"),
    ("search/compare_subprocess.py", 461, "HYGE_SEARCH_WORKER_DEFER_DERIVATION"),
    ("search/compare_subprocess.py", 462, "subprocess.Popen"),
    ("search/compare_subprocess.py", 472, "threading.Thread"),
    ("search/engine.py", 646, "def _theorem_applicable_rules_sharded"),
    ("search/engine.py", 793, "def _theorem_applicable_rules_for"),
    ("search/engine.py", 868, "def _theorem_cursor_for"),
    ("search/engine.py", 649, 'get_start_method() == "spawn"'),
    ("search/engine.py", 651, "FilterApplicableRulesWithIndex"),
    ("search/engine.py", 654, 'get_context("fork")'),
    ("search/engine.py", 656, 'get_context("spawn")'),
    ("search/engine.py", 657, 'mp_context.get_start_method()'),
    ("search/engine.py", 659, "FilterApplicableRulesWithIndex"),
    ("search/engine.py", 666, "worker_capacity = multiprocessing.cpu_count()"),
    ("search/engine.py", 671, "if worker_capacity < 2:"),
    ("search/engine.py", 702, "mp_context.Process"),
    ("search/engine.py", 823, "_theorem_applicable_rules_sharded"),
    ("search/engine.py", 945, "_theorem_applicable_rules_sharded"),
    ("search/serialization.py", 328, "def _install_search_worker_pickle_support"),
    ("search/serialization.py", 340, "def sync_from_namespace"),
    ("search/ui.py", 96, "def start"),
    ("search/ui.py", 101, "hyge-search-input"),
    ("search/ui.py", 131, "queue.Queue"),
    ("search/model.py", 606, "class SearchWorkerLaunch"),
    ("search/model.py", 607, "launch_slot"),
    ("search/model.py", 1169, "class SearchWorkerResult"),
    ("testsuite.py", 1105, "class HeuristicCanonicalKnowledgeAgreementTest"),
    ("testsuite.py", 1331, "class CompareSearchModesFindsReusableWorkerSnapshotDirTest"),
    ("testsuite.py", 1371, "_search_worker_result_manifest_path"),
    ("testsuite.py", 1375, "SearchBFS"),
    ("testsuite.py", 1626, "class _WarmRootWaveCompareProbe"),
    ("testsuite.py", 1636, "self.spawned"),
    ("testsuite.py", 1736, "class CompareSearchModesFillWarmsResidentPoolBeforeRootWaveTest"),
    ("testsuite.py", 2290, "class TreeInsertDeepPairLookupAvoidsRecursionTest"),
    ("testsuite.py", 6039, "def _register_test"),
]


def resolve(rel_path):
    target = os.path.join(REPO_ROOT, rel_path)
    if os.path.isfile(target):
        return target
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".venv")]
        if os.path.basename(rel_path) in files and root.endswith(os.path.dirname(rel_path) or "."):
            return os.path.join(root, os.path.basename(rel_path))
    return None


def main():
    window = WINDOW
    argv = sys.argv[1:]
    if "--window" in argv:
        window = int(argv[argv.index("--window") + 1])
    text = open(PLAN, encoding="utf-8").read()
    if not re.search(r"process-agents-plan", os.path.basename(PLAN)):
        print("plan file missing")
        return 1
    failures = []
    cache = {}
    for rel_path, line, symbol in CITATIONS:
        path = cache.get(rel_path)
        if path is None:
            path = resolve(rel_path)
            cache[rel_path] = path
        if path is None:
            failures.append("%s:%d  FILE NOT FOUND" % (rel_path, line))
            continue
        lines = open(path, encoding="utf-8").read().splitlines()
        if line > len(lines):
            failures.append("%s:%d  line beyond EOF (%d lines)" % (rel_path, line, len(lines)))
            continue
        low = max(0, line - 1 - window)
        high = min(len(lines), line + window)
        found = lines[low:high]
        if not any(symbol in entry for entry in found):
            failures.append(
                "%s:%d  symbol %r absent from lines %d-%d"
                % (rel_path, line, symbol, low + 1, high)
            )
    print("citations checked: %d   window: +/-%d lines" % (len(CITATIONS), window))
    if failures:
        print("FAILED %d:" % len(failures))
        for entry in failures:
            print("  " + entry)
        return 1
    print("all citations verified (file, line, and symbol)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
