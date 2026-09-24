from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time

from .. import gmprep as Gmpmod
from .. import machine as M
from ..proof import *
from ..proof import _debug, _debug_term
from .model import *


class _ComparisonSubprocessMixin:
    def _comparison_main_script_path(self):
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")

    def _search_worker_result_manifest_path(self, result_path):
        return result_path + ".manifest.json"

    def _write_search_worker_manifest(self, result_path):
        manifest = {
            "start_text": _debug_term(self.start, self.registry),
            "goal_text": _debug_term(self.goal, self.registry),
        }
        with open(self._search_worker_result_manifest_path(result_path), "w", encoding="utf-8") as handle:
            json.dump(manifest, handle)

    def _mode_worker_token(self, mode):
        if M.IdentityCompare(mode, DFSLabel)() is M.truth_value:
            return "dfs"
        if M.IdentityCompare(mode, BFSLabel)() is M.truth_value:
            return "bfs"
        if M.IdentityCompare(mode, AStarLabel)() is M.truth_value:
            return "astar"
        if M.IdentityCompare(mode, BeamLabel)() is M.truth_value:
            return "beam"
        if M.IdentityCompare(mode, RewriteDFSLabel)() is M.truth_value:
            return "rewritedfs"
        return "search"

    def _gmp_atom(self, text):
        atom = M.Atom()
        atom.value = Gmpmod.GMPRep(text)
        return atom

    def _reason_atom(self, text):
        atom = M.Atom()
        atom.value = text
        return atom

    def _fabricate_worker_failure_attempt(self, heuristic, status, elapsed_seconds, reason_text, search_cost=None, worker_pid_text="0"):
        if search_cost is None:
            search_cost = self._zero_search_cost(status)
        proof_cost = self._zero_proof_cost()
        total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, self.registry)()
        total_cost = M.Head(total_cost_pair)()
        self.registry = M.Head(M.Tail(total_cost_pair)())()
        attempt = SearchAttempt(
            self.start,
            self.goal,
            heuristic,
            status,
            M.EmptyList,
            proof_cost,
            search_cost,
            total_cost,
        )()
        elapsed_milliseconds = int(round(elapsed_seconds * 1000.0))
        if elapsed_milliseconds < 0:
            elapsed_milliseconds = 0
        performance = HeuristicPerformance(
            attempt,
            self._gmp_atom(str(elapsed_milliseconds)),
            self._gmp_atom(worker_pid_text),
            self._reason_atom(reason_text),
        )()
        return attempt, performance

    def _performance_elapsed_seconds(self, performance):
        elapsed = HeuristicPerformanceElapsedMilliseconds(performance)()
        try:
            return float(Gmpmod.GMPRepText(elapsed())()) / 1000.0
        except Exception:
            return 0.0

    def _performance_reason_text(self, performance):
        reason = HeuristicPerformanceCompletionReason(performance)()
        if M.IsPair(reason)() is M.truth_value:
            status_text = SearchStatusText(reason)()
            if status_text != "unknown":
                return status_text
        try:
            return str(reason())
        except Exception:
            return _debug_term(reason, self.registry)

    def _is_heuristic_performance(self, value):
        if M.IsPair(value)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(value)(), HeuristicPerformanceLabel)()

    def _loaded_worker_attempt_is_final(self, attempt):
        status = SearchAttemptStatus(attempt)()
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
            if M.Compare(SearchAttemptDerivation(attempt)(), M.EmptyList)() is M.false_value:
                return M.truth_value
            return M.false_value
        if M.IdentityCompare(status, SearchFailureLabel)() is M.truth_value:
            return M.truth_value
        if M.IdentityCompare(status, SearchTimedOutLabel)() is M.truth_value:
            return M.truth_value
        if M.IdentityCompare(status, SearchAbortedByUserLabel)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _worker_failure_from_partial_attempt(self, heuristic, attempt, performance, elapsed_seconds, worker_pid_text, exit_code_text):
        search_cost = SearchAttemptSearchCost(attempt)()
        reason_text = self._performance_reason_text(performance)
        failure_reason = "abnormal-exit-during-search exit=" + exit_code_text
        if reason_text == "success-plan-found":
            failure_reason = "abnormal-exit-after-plan-found exit=" + exit_code_text
        if reason_text == "running-derivation":
            failure_reason = "abnormal-exit-during-derivation exit=" + exit_code_text
        return self._fabricate_worker_failure_attempt(
            heuristic,
            SearchFailureLabel,
            elapsed_seconds,
            failure_reason,
            search_cost,
            worker_pid_text,
        )

    def _partial_worker_attempt_is_resume_ready(self, attempt, performance, result_path=None):
        if M.IdentityCompare(SearchAttemptStatus(attempt)(), SearchSuccessLabel)() is M.false_value:
            return M.false_value
        reason_text = self._performance_reason_text(performance)
        if (reason_text == "success-plan-found") is False:
            if (reason_text == "running-derivation") is False:
                return M.false_value
        if result_path == None:
            return M.truth_value
        from ..main import _runtime_namespace
        from ..persistence import SnapshotCodec
        try:
            state = SnapshotCodec(_runtime_namespace()).load(result_path)
            worker_plan = state.roots.get("worker_plan", M.EmptyList)
            if M.Compare(worker_plan, M.EmptyList)() is M.truth_value:
                return M.false_value
        except Exception:
            return M.false_value
        return M.truth_value

    def _load_search_worker_snapshot(self, mode, heuristic, result_path):
        from ..main import _runtime_namespace
        from ..persistence import SnapshotCodec

        if os.path.exists(result_path) is False:
            return self._fabricate_worker_failure_attempt(heuristic, SearchFailureLabel, 0.0, "launch-error")
        codec = SnapshotCodec(_runtime_namespace())
        state = codec.load(result_path)
        child_registry = state.roots.get("constructor_registry", M.EmptyList)
        if codec._is_entry_chain(child_registry) is M.truth_value:
            # Snapshot format 4 stores the registry as its entry chain.
            child_registry = codec._rebuild_tree_from_entry_chain(child_registry)
        if M.Compare(child_registry, M.EmptyList)() is M.false_value:
            self.registry = self._merge_tree(self.registry, child_registry)
            self.graph._replace_context(constructors=self.registry)
        attempts = state.roots.get("search_history", M.EmptyList)
        attempt = M.EmptyList
        if M.IdentityCompare(attempts, M.EmptyList)() is M.false_value:
            attempt = M.Head(attempts)()
        performances = state.roots.get("search_comparisons", M.EmptyList)
        performance = M.EmptyList
        if M.IdentityCompare(performances, M.EmptyList)() is M.false_value:
            candidate = M.Head(performances)()
            if self._is_heuristic_performance(candidate) is M.truth_value:
                performance = candidate
        if M.Compare(attempt, M.EmptyList)() is M.truth_value:
            return self._fabricate_worker_failure_attempt(heuristic, SearchFailureLabel, 0.0, "missing-attempt")
        if M.Compare(performance, M.EmptyList)() is M.truth_value:
            return self._fabricate_worker_failure_attempt(
                heuristic,
                SearchAttemptStatus(attempt)(),
                0.0,
                "missing-performance",
            )
        return attempt, performance

    def _relay_search_worker_output(self, mode_text, stdout_pipe):
        if stdout_pipe is None:
            return
        for line in stdout_pipe:
            text = line.rstrip()
            if text == "":
                continue
            if text.startswith("DEBUG: "):
                text = text[7:]
            if "build-derivation:" in text:
                continue
            if text.startswith(mode_text + ":") is False:
                text = mode_text + ": " + text
            _debug(text)
        try:
            stdout_pipe.close()
        except Exception:
            pass

    def _log_independent_mode_finish(self, mode, status, elapsed_seconds, search_cost, reason_text=""):
        mode_text = SearchModeText(mode)()
        _debug(
            "SearchComparison: "
            + mode_text
            + " finished status="
            + SearchStatusText(status)()
            + " elapsed="
            + "{:.3f}".format(elapsed_seconds)
            + " expanded="
            + self._nat_text(SearchCostExpanded(search_cost)())
            + " generated="
            + self._nat_text(SearchCostGenerated(search_cost)())
            + " frontier_peak="
            + self._nat_text(SearchCostFrontierPeak(search_cost)())
            + " total="
            + self._nat_text(SearchCostValue(search_cost)())
            + " reason="
            + reason_text
        )

    def _approval_to_materialize_best_attempt(self, best_attempt, performances_by_mode, result_path_by_mode):
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return best_attempt, performances_by_mode
        if M.IdentityCompare(SearchAttemptStatus(best_attempt)(), SearchSuccessLabel)() is M.false_value:
            return best_attempt, performances_by_mode
        if M.Compare(SearchAttemptDerivation(best_attempt)(), M.EmptyList)() is M.false_value:
            return best_attempt, performances_by_mode
        if M.IdentityCompare(self.graph._search_disable_console, M.truth_value)() is M.truth_value:
            _debug("SearchComparison: console disabled; leaving derivation replay deferred")
            return best_attempt, performances_by_mode
        mode = HeuristicSearchMode(SearchAttemptHeuristic(best_attempt)())()
        mode_text = SearchModeText(mode)()
        result_path = result_path_by_mode[mode_text]
        package_root = os.path.dirname(os.path.dirname(__file__))
        display_path = result_path
        try:
            display_path = os.path.relpath(result_path, package_root)
        except Exception:
            display_path = result_path
        prompt = mode_text + " found a plan. Proceed to derivation replay/save for " + display_path + "?"
        _debug("SearchComparison: approval requested for " + mode_text + " result=" + display_path)
        print(prompt, flush=True)
        try:
            response = input("> ")
        except Exception:
            response = ""
        answer = response.strip().lower()
        if answer not in ("y", "yes", "continue", "proceed"):
            _debug("SearchComparison: derivation replay declined for " + mode_text)
            return best_attempt, performances_by_mode
        package_name = os.path.basename(package_root)
        import_root = os.path.dirname(package_root)
        mode_token = self._mode_worker_token(mode)
        timeout_text = os.environ.get("HYGE_SEARCH_WORKER_TIMEOUT", "6000")
        child_env = os.environ.copy()
        child_env["PYTHONPATH"] = import_root
        if "HYGE_SEARCH_WORKER_DEFER_DERIVATION" in child_env:
            del child_env["HYGE_SEARCH_WORKER_DEFER_DERIVATION"]
        child_env["HYGE_SEARCH_WORKER_RESUME_DERIVATION"] = "1"
        if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
            child_env["HYGE_SEARCH_WORKER_DEBUG"] = "1"
        process = subprocess.Popen(
            [sys.executable, "-m", package_name + ".main", "search-worker", mode_token, result_path, timeout_text],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=import_root,
            env=child_env,
        )
        _debug("SearchComparison: resumed search-worker mode=" + mode_text + " pid=" + str(process.pid))
        thread = threading.Thread(target=self._relay_search_worker_output, args=(mode_text, process.stdout), daemon=True)
        thread.start()
        exit_code = process.wait()
        thread.join(timeout=1.0)
        heuristic = SearchAttemptHeuristic(best_attempt)()
        attempt, performance = self._load_search_worker_snapshot(mode, heuristic, result_path)
        reason_text = self._performance_reason_text(performance)
        if exit_code != 0:
            if M.IdentityCompare(SearchAttemptStatus(attempt)(), SearchSuccessLabel)() is M.truth_value:
                if M.Compare(SearchAttemptDerivation(attempt)(), M.EmptyList)() is M.false_value:
                    if reason_text != "success-derivation-built":
                        attempt, performance = self._fabricate_worker_failure_attempt(
                            heuristic,
                            SearchFailureLabel,
                            self._performance_elapsed_seconds(performance),
                            "abnormal-exit-after-stale-success exit=" + str(exit_code),
                            SearchAttemptSearchCost(attempt)(),
                            str(process.pid),
                        )
                else:
                    attempt, performance = self._fabricate_worker_failure_attempt(
                        heuristic,
                        SearchFailureLabel,
                        self._performance_elapsed_seconds(performance),
                        "abnormal-exit-during-derivation exit=" + str(exit_code),
                        SearchAttemptSearchCost(attempt)(),
                        str(process.pid),
                    )
        performances_by_mode[mode_text] = performance
        _debug("SearchComparison: resumed worker exited mode=" + mode_text + " exit_code=" + str(exit_code))
        return attempt, performances_by_mode

    def _search_compare_result_root(self, package_root):
        return os.path.join(package_root, "snapshots", "search_compare")

    def _search_worker_snapshot_matches_current_problem(self, mode, heuristic, result_path):
        attempt, performance = self._load_search_worker_snapshot(mode, heuristic, result_path)
        if M.TermEqual(SearchAttemptStart(attempt)(), self.start)() is M.false_value:
            return M.Pair(M.false_value, M.Pair(attempt, M.Pair(performance, M.EmptyList)))
        if M.TermEqual(SearchAttemptGoal(attempt)(), self.goal)() is M.false_value:
            return M.Pair(M.false_value, M.Pair(attempt, M.Pair(performance, M.EmptyList)))
        if M.TermEqual(SearchAttemptHeuristic(attempt)(), heuristic)() is M.false_value:
            return M.Pair(M.false_value, M.Pair(attempt, M.Pair(performance, M.EmptyList)))
        return M.Pair(M.truth_value, M.Pair(attempt, M.Pair(performance, M.EmptyList)))

    def _search_worker_resume_stage_rank(self, reason_text):
        if reason_text == "success-derivation-built":
            return 3
        if reason_text == "running-derivation":
            return 2
        if reason_text == "success-plan-found":
            return 1
        return 0

    def _reusable_search_worker_result_paths(self, package_root):
        result_root = self._search_compare_result_root(package_root)
        reusable_paths = {}
        if os.path.isdir(result_root) is False:
            return reusable_paths
        run_names = os.listdir(result_root)
        run_names.sort(reverse=True)
        remaining_modes = self._mode_chain()
        while M.IdentityCompare(remaining_modes, M.EmptyList)() is M.false_value:
            mode = M.Head(remaining_modes)()
            remaining_modes = M.Tail(remaining_modes)()
            mode_text = SearchModeText(mode)()
            heuristic = self._heuristic_for_mode(mode)
            best_path = ""
            best_rank = -1
            run_index = 0
            while run_index != len(run_names):
                run_name = run_names[run_index]
                run_index = run_index + 1
                run_dir = os.path.join(result_root, run_name)
                if os.path.isdir(run_dir) is False:
                    continue
                result_path = os.path.join(run_dir, self._mode_worker_token(mode) + ".snapshot.json")
                if os.path.exists(result_path) is False:
                    continue
                try:
                    matched_pair = self._search_worker_snapshot_matches_current_problem(mode, heuristic, result_path)
                except Exception:
                    continue
                if M.IdentityCompare(M.Head(matched_pair)(), M.truth_value)() is M.false_value:
                    continue
                attempt = M.Head(M.Tail(matched_pair)())()
                performance = M.Head(M.Tail(M.Tail(matched_pair)())())()
                if self._loaded_worker_attempt_is_final(attempt) is M.truth_value:
                    reason_text = self._performance_reason_text(performance)
                    if M.IdentityCompare(SearchAttemptStatus(attempt)(), SearchSuccessLabel)() is M.false_value:
                        continue
                    rank = self._search_worker_resume_stage_rank(reason_text)
                    if rank < 3:
                        rank = 3
                elif self._partial_worker_attempt_is_resume_ready(attempt, performance, result_path) is M.truth_value:
                    reason_text = self._performance_reason_text(performance)
                    rank = self._search_worker_resume_stage_rank(reason_text)
                else:
                    continue
                if rank > best_rank:
                    best_rank = rank
                    best_path = result_path
            if best_path != "":
                reusable_paths[mode_text] = best_path
        return reusable_paths

    def _finalize_independent_mode_attempts(self, attempts, best_attempt, performances):
        comparison_outcome = SearchFailureLabel
        if M.Compare(best_attempt, M.EmptyList)() is M.false_value:
            comparison_outcome = SearchAttemptStatus(best_attempt)()
        self.graph._replace_context(constructors=self.registry)
        attempts_cursor = attempts
        while M.IdentityCompare(attempts_cursor, M.EmptyList)() is M.false_value:
            self.graph.add_search_attempt(M.Head(attempts_cursor)())
            attempts_cursor = M.Tail(attempts_cursor)()
        comparison = SearchComparison(self.signature, attempts, best_attempt, comparison_outcome, performances)()
        self.graph.add_search_comparison(comparison)
        self.graph._last_search_comparison_outcome = comparison_outcome
        best_mode_text = "none"
        if M.Compare(best_attempt, M.EmptyList)() is M.false_value:
            best_mode_text = SearchModeText(HeuristicSearchMode(SearchAttemptHeuristic(best_attempt)())())()
        _debug("SearchComparison: best mode=" + best_mode_text)
        _debug("SearchComparison: provenance recorded")
        return M.Pair(comparison, M.Pair(best_attempt, M.EmptyList))

    def _compare_all_modes_independent_parallel(self, paused_job=M.EmptyList):
        if M.Compare(paused_job, M.EmptyList)() is M.false_value:
            _debug("SearchComparison: paused legacy comparison ignored; restarting independent mode attempts")
        _debug("SearchComparison: starting independent mode attempts")
        self.graph.remove_search_comparison_job(self.signature)
        package_root = os.path.dirname(os.path.dirname(__file__))
        package_name = os.path.basename(package_root)
        import_root = os.path.dirname(package_root)
        result_dir = os.path.join(self._search_compare_result_root(package_root), "run-" + str(int(time.time() * 1000.0)))
        os.makedirs(result_dir, exist_ok=True)
        reusable_result_paths = self._reusable_search_worker_result_paths(package_root)
        timeout_text = os.environ.get("HYGE_SEARCH_WORKER_TIMEOUT", "6000")
        timeout_units = 6000
        try:
            timeout_units = int(timeout_text)
        except Exception:
            timeout_units = 6000
        comparison_timeout_seconds = timeout_units + 120
        comparison_started_at = time.time()
        workers = ()
        reader_threads = ()
        result_path_by_mode = {}
        attempts_by_mode = {}
        performances_by_mode = {}
        best_attempt = M.EmptyList
        best_elapsed_seconds = None
        modes = self._mode_chain()
        remaining_modes = modes
        while M.IdentityCompare(remaining_modes, M.EmptyList)() is M.false_value:
            mode = M.Head(remaining_modes)()
            mode_text = SearchModeText(mode)()
            mode_token = self._mode_worker_token(mode)
            heuristic = self._heuristic_for_mode(mode)
            result_path = os.path.join(result_dir, mode_token + ".snapshot.json")
            if mode_text in reusable_result_paths:
                reusable_result_path = reusable_result_paths[mode_text]
                try:
                    attempt, performance = self._load_search_worker_snapshot(mode, heuristic, reusable_result_path)
                    if M.OrAtom(
                        self._loaded_worker_attempt_is_final(attempt),
                        self._partial_worker_attempt_is_resume_ready(attempt, performance, reusable_result_path),
                    )() is M.truth_value:
                        attempts_by_mode[mode_text] = attempt
                        performances_by_mode[mode_text] = performance
                        result_path_by_mode[mode_text] = reusable_result_path
                        elapsed_seconds = self._performance_elapsed_seconds(performance)
                        if self._attempt_better_with_elapsed(attempt, elapsed_seconds, best_attempt, best_elapsed_seconds) is M.truth_value:
                            best_attempt = attempt
                            best_elapsed_seconds = elapsed_seconds
                        _debug("SearchComparison: reusing saved worker snapshot mode=" + mode_text + " result=" + os.path.relpath(reusable_result_path, package_root) + " stage=" + self._performance_reason_text(performance))
                        remaining_modes = M.Tail(remaining_modes)()
                        continue
                except Exception as error:
                    _debug("SearchComparison: saved worker snapshot reuse failed mode=" + mode_text + " error=" + str(error))
            self._write_search_worker_manifest(result_path)
            cmd = [sys.executable, "-m", package_name + ".main", "search-worker", mode_token, result_path, timeout_text]
            child_env = os.environ.copy()
            child_env["PYTHONPATH"] = import_root
            child_env["HYGE_SEARCH_WORKER_DEFER_DERIVATION"] = "1"
            if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                child_env["HYGE_SEARCH_WORKER_DEBUG"] = "1"
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=import_root,
                env=child_env,
            )
            _debug("SearchComparison: launched search-worker mode=" + mode_text + " pid=" + str(process.pid))
            thread = threading.Thread(target=self._relay_search_worker_output, args=(mode_text, process.stdout), daemon=True)
            thread.start()
            workers = workers + ((mode, heuristic, process, result_path, time.time()),)
            result_path_by_mode[mode_text] = result_path
            reader_threads = reader_threads + (thread,)
            remaining_modes = M.Tail(remaining_modes)()
        worker_total = len(workers)
        finished_count = 0
        while finished_count != worker_total:
            if time.time() - comparison_started_at > comparison_timeout_seconds:
                worker_index = 0
                while worker_index != worker_total:
                    mode, heuristic, process, result_path, launch_started_at = workers[worker_index]
                    worker_index = worker_index + 1
                    mode_text = SearchModeText(mode)()
                    if mode_text in attempts_by_mode:
                        continue
                    if process.poll() is None:
                        _debug("SearchComparison: worker timeout mode=" + mode_text + " pid=" + str(process.pid))
                        try:
                            process.terminate()
                        except Exception:
                            pass
                        deadline = time.time() + 2.0
                        while process.poll() is None:
                            if time.time() > deadline:
                                break
                            time.sleep(0.1)
                        if process.poll() is None:
                            try:
                                process.kill()
                            except Exception:
                                pass
                    elapsed_seconds = time.time() - launch_started_at
                    attempt, performance = self._fabricate_worker_failure_attempt(
                        heuristic,
                        SearchTimedOutLabel,
                        elapsed_seconds,
                        "comparison-timeout",
                        None,
                        str(process.pid),
                    )
                    attempts_by_mode[mode_text] = attempt
                    performances_by_mode[mode_text] = performance
                    self._log_independent_mode_finish(mode, SearchAttemptStatus(attempt)(), elapsed_seconds, SearchAttemptSearchCost(attempt)(), "comparison-timeout")
                    if self._attempt_better_with_elapsed(attempt, elapsed_seconds, best_attempt, best_elapsed_seconds) is M.truth_value:
                        best_attempt = attempt
                        best_elapsed_seconds = elapsed_seconds
                    finished_count = finished_count + 1
                break
            saw_update = M.false_value
            worker_index = 0
            while worker_index != worker_total:
                mode, heuristic, process, result_path, launch_started_at = workers[worker_index]
                worker_index = worker_index + 1
                mode_text = SearchModeText(mode)()
                if mode_text in attempts_by_mode:
                    continue
                exit_code = process.poll()
                if exit_code is None:
                    continue
                saw_update = M.truth_value
                elapsed_seconds = time.time() - launch_started_at
                _debug(
                    "SearchComparison: worker exited mode="
                    + mode_text
                    + " pid="
                    + str(process.pid)
                    + " exit_code="
                    + str(exit_code)
                    + " elapsed="
                    + "{:.3f}".format(elapsed_seconds)
                )
                load_ok = M.false_value
                attempt = M.EmptyList
                performance = M.EmptyList
                if os.path.exists(result_path) is False:
                    time.sleep(0.2)
                if os.path.exists(result_path) is True:
                    try:
                        attempt, performance = self._load_search_worker_snapshot(mode, heuristic, result_path)
                        load_ok = M.truth_value
                    except Exception as error:
                        _debug("SearchComparison: load retry mode=" + mode_text + " error=" + str(error))
                        time.sleep(0.2)
                        try:
                            attempt, performance = self._load_search_worker_snapshot(mode, heuristic, result_path)
                            load_ok = M.truth_value
                        except Exception as second_error:
                            _debug("SearchComparison: load failed mode=" + mode_text + " error=" + str(second_error))
                if load_ok is M.truth_value:
                    stored_elapsed_seconds = self._performance_elapsed_seconds(performance)
                    if stored_elapsed_seconds > 0.0:
                        elapsed_seconds = stored_elapsed_seconds
                if load_ok is M.false_value:
                    attempt, performance = self._fabricate_worker_failure_attempt(
                        heuristic,
                        SearchFailureLabel,
                        elapsed_seconds,
                        "abnormal-exit-missing-result exit=" + str(exit_code),
                        None,
                        str(process.pid),
                    )
                else:
                    if self._loaded_worker_attempt_is_final(attempt) is M.false_value:
                        if self._partial_worker_attempt_is_resume_ready(attempt, performance) is M.false_value:
                            attempt, performance = self._worker_failure_from_partial_attempt(
                                heuristic,
                                attempt,
                                performance,
                                elapsed_seconds,
                                str(process.pid),
                                str(exit_code),
                            )
                    else:
                        if exit_code == 2:
                            if M.IdentityCompare(SearchAttemptStatus(attempt)(), SearchTimedOutLabel)() is M.false_value:
                                attempt, performance = self._fabricate_worker_failure_attempt(
                                    heuristic,
                                    SearchTimedOutLabel,
                                    elapsed_seconds,
                                    "worker-timeout exit=2",
                                    SearchAttemptSearchCost(attempt)(),
                                    str(process.pid),
                                )
                attempts_by_mode[mode_text] = attempt
                performances_by_mode[mode_text] = performance
                self._log_independent_mode_finish(mode, SearchAttemptStatus(attempt)(), elapsed_seconds, SearchAttemptSearchCost(attempt)(), self._performance_reason_text(performance))
                if self._attempt_better_with_elapsed(attempt, elapsed_seconds, best_attempt, best_elapsed_seconds) is M.truth_value:
                    best_attempt = attempt
                    best_elapsed_seconds = elapsed_seconds
                finished_count = finished_count + 1
            if saw_update is M.false_value:
                time.sleep(0.2)
        thread_index = 0
        while thread_index != len(reader_threads):
            reader_threads[thread_index].join(timeout=1.0)
            thread_index = thread_index + 1
        attempts_rev = M.EmptyList
        performances_rev = M.EmptyList
        remaining_modes = modes
        while M.IdentityCompare(remaining_modes, M.EmptyList)() is M.false_value:
            mode = M.Head(remaining_modes)()
            mode_text = SearchModeText(mode)()
            attempts_rev = M.Pair(attempts_by_mode[mode_text], attempts_rev)
            performances_rev = M.Pair(performances_by_mode[mode_text], performances_rev)
            remaining_modes = M.Tail(remaining_modes)()
        attempts = self._reverse(attempts_rev, M.EmptyList)
        performances = self._reverse(performances_rev, M.EmptyList)
        perf_cursor = performances
        while M.IdentityCompare(perf_cursor, M.EmptyList)() is M.false_value:
            perf = M.Head(perf_cursor)()
            attempt = HeuristicPerformanceAttempt(perf)()
            _debug(
                "SearchComparison: summary "
                + SearchModeText(HeuristicSearchMode(SearchAttemptHeuristic(attempt)())())()
                + " status="
                + SearchStatusText(SearchAttemptStatus(attempt)())()
                + " elapsed="
                + "{:.3f}".format(self._performance_elapsed_seconds(perf))
                + " expanded="
                + self._nat_text(SearchCostExpanded(SearchAttemptSearchCost(attempt)())())
                + " cost="
                + self._nat_text(self._attempt_total_value(attempt))
            )
            perf_cursor = M.Tail(perf_cursor)()
        best_attempt, performances_by_mode = self._approval_to_materialize_best_attempt(best_attempt, performances_by_mode, result_path_by_mode)
        attempts_rev = M.EmptyList
        performances_rev = M.EmptyList
        remaining_modes = modes
        while M.IdentityCompare(remaining_modes, M.EmptyList)() is M.false_value:
            mode = M.Head(remaining_modes)()
            mode_text = SearchModeText(mode)()
            if M.TermEqual(SearchAttemptHeuristic(best_attempt)(), self._heuristic_for_mode(mode))() is M.truth_value:
                attempts_by_mode[mode_text] = best_attempt
            attempts_rev = M.Pair(attempts_by_mode[mode_text], attempts_rev)
            performances_rev = M.Pair(performances_by_mode[mode_text], performances_rev)
            remaining_modes = M.Tail(remaining_modes)()
        attempts = self._reverse(attempts_rev, M.EmptyList)
        performances = self._reverse(performances_rev, M.EmptyList)
        if M.OrAtom(
            M.Compare(best_attempt, M.EmptyList),
            M.IdentityCompare(SearchAttemptStatus(best_attempt)(), SearchFailureLabel),
        )() is M.truth_value:
            best_attempt = self._best_attempt_in_performances(performances, M.EmptyList, None)
        return self._finalize_independent_mode_attempts(attempts, best_attempt, performances)

    def _compare_all_modes_independent(self, paused_job=M.EmptyList):
        return self._compare_all_modes_independent_parallel(paused_job)

    def _mode_chain(self):
        return M.Pair(
            DFSLabel,
            M.Pair(
                BFSLabel,
                M.Pair(AStarLabel, M.Pair(BeamLabel, M.Pair(RewriteDFSLabel, M.EmptyList))),
            ),
        )

    def _mode_chain_text(self, modes):
        if M.IdentityCompare(modes, M.EmptyList)() is M.truth_value:
            return ""
        here = SearchModeText(M.Head(modes)())()
        rest = self._mode_chain_text(M.Tail(modes)())
        if rest == "":
            return here
        return here + ", " + rest

    def _selected_modes_text(self, modes):
        return self._mode_chain_text(modes)

    def _fresh_independent_mode_runtime(self):
        from .runtime import _SearchWorkerRuntime

        runtime = _SearchWorkerRuntime(M.FromContextGetConstructors(self.graph)(), M.EmptyList)
        runtime._search_disable_console = M.truth_value
        runtime._search_disable_progress_ticker = M.truth_value
        runtime._search_stop_help_shown = M.truth_value
        runtime._search_compare_enable_shared_root_fast_paths = M.false_value
        runtime._search_compare_ignore_root_fast_paths = M.truth_value
        runtime._search_compare_root_start = self.start
        runtime._search_compare_root_goal = self.goal
        runtime._search_compare_discovery_mode = M.false_value
        runtime._last_search_comparison_outcome = SearchSuccessLabel
        return runtime

    def _independent_mode_attempt(self, mode):
        from .api import Search as SearchAPI

        heuristic = self._heuristic_for_mode(mode)
        mode_text = SearchModeText(mode)()
        _debug("SearchComparison: " + mode_text + " started")
        started_at = time.time()
        try:
            mode_runtime = self._fresh_independent_mode_runtime()
            search_pair = SearchAPI(
                mode_runtime,
                self.start,
                self.goal,
                self.rules,
                heuristic,
                mode_runtime.constructor_registry,
            )()
            plan = M.Head(search_pair)()
            search_cost = M.Head(M.Tail(search_pair)())()
            status = SearchCostOutcome(search_cost)()

            derivation = M.EmptyList
            proof_cost = self._zero_proof_cost()
            if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
                derivation_pair = BuildDerivation(self.start, plan, mode_runtime.constructor_registry)()
                derivation = M.Head(derivation_pair)()
                mode_runtime._replace_context(constructors=M.Head(M.Tail(derivation_pair)())())
                if M.Compare(derivation, M.EmptyList)() is M.false_value:
                    proof_cost_pair = DerivationCost(derivation, mode_runtime.constructor_registry)()
                    proof_cost = M.Head(proof_cost_pair)()
                    mode_runtime._replace_context(constructors=M.Head(M.Tail(proof_cost_pair)())())

            total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, mode_runtime.constructor_registry)()
            total_cost = M.Head(total_cost_pair)()
            mode_runtime._replace_context(constructors=M.Head(M.Tail(total_cost_pair)())())

            attempt = SearchAttempt(self.start, self.goal, heuristic, status, derivation, proof_cost, search_cost, total_cost)()

            elapsed_seconds = time.time() - started_at
            _debug(
                "SearchComparison: "
                + mode_text
                + " finished status="
                + SearchStatusText(status)()
                + " elapsed="
                + "{:.3f}".format(elapsed_seconds)
                + " expanded="
                + self._nat_text(SearchCostExpanded(search_cost)())
                + " generated="
                + self._nat_text(SearchCostGenerated(search_cost)())
                + " frontier_peak="
                + self._nat_text(SearchCostFrontierPeak(search_cost)())
            )
            return attempt, elapsed_seconds
        except Exception as error:
            import traceback

            elapsed_seconds = time.time() - started_at
            _debug(
                "SearchComparison: "
                + mode_text
                + " finished status=error elapsed="
                + "{:.3f}".format(elapsed_seconds)
                + " error="
                + str(error)
            )
            traceback.print_exc()
            failed_attempt = SearchAttempt(
                self.start,
                self.goal,
                heuristic,
                SearchFailureLabel,
                M.EmptyList,
                self._zero_proof_cost(),
                self._zero_search_cost(SearchFailureLabel),
                M.EmptyList,
            )()
            return failed_attempt, elapsed_seconds



def sync_from_namespace(namespace):
    for name in (
        "DFSLabel",
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
        "RewriteDFSLabel",
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchTimedOutLabel",
        "SearchAbortedByUserLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonSubprocessMixin")]
