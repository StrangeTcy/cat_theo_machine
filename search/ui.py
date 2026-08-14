from __future__ import annotations

import copyreg
import multiprocessing
import queue
import sys
import threading
import time

from .. import machine as M
from .. import heuristics as Hmod
from .. import labels as Lmod
from .. import proof as Pmod
from .. import context as Ctxmod
from .. import schemata as Smod
from .. import gmprep as Gmpmod
from .. import trees as Tmod
from .. import logic as Logicmod
from ..heuristics import *
from ..labels import *
from ..proof import *
from ..proof import _debug, _debug_term
class _SearchProgressTicker:
    def __init__(self, mode_text, progress_owner=None):
        self.mode_text = mode_text
        self.progress_owner = progress_owner
        self.started_at = time.time()
        self._pause_event = threading.Event()
        self._paused_at = None

    def _elapsed_seconds(self):
        elapsed = int(time.time() - self.started_at)
        if elapsed < 0:
            return 0
        return elapsed

    def start(self):
        self.started_at = time.time()
        _debug("trying " + self.mode_text + " now")

    def stop(self):
        return self._elapsed_seconds()

    def pause(self):
        if self._pause_event.is_set():
            return
        self._paused_at = time.time()
        self._pause_event.set()

    def resume(self):
        pause_requested = M.truth_value if self._pause_event.is_set() else M.false_value
        if pause_requested is M.false_value:
            return
        if self._paused_at is not None:
            self.started_at += time.time() - self._paused_at
            self._paused_at = None
        self._pause_event.clear()


class _SearchConsoleInput:
    def __init__(self):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._started = M.false_value
        self._thread = None
        self._prompt_queue = None
        self._search_control = None

    def _available(self):
        if sys.stdin is None:
            return M.false_value
        if sys.stdin.isatty():
            return M.truth_value
        return M.false_value

    def _run(self):
        while True:
            stop_requested = M.truth_value if self._stop_event.is_set() else M.false_value
            if stop_requested is M.truth_value:
                return
            try:
                line = sys.stdin.readline()
            except Exception:
                return
            if line == "":
                return
            with self._lock:
                prompt_queue = self._prompt_queue
                search_control = None if prompt_queue is not None else self._search_control
            if prompt_queue is not None:
                prompt_queue.put(line)
                continue
            if search_control is not None:
                search_control.handle_line(line)

    def start(self):
        if self._started is M.truth_value:
            return M.truth_value
        if self._available() is M.false_value:
            return M.false_value
        self._thread = threading.Thread(target=self._run, name="hyge-search-input", daemon=True)
        self._thread.start()
        self._started = M.truth_value
        return M.truth_value

    def stop(self):
        self._stop_event.set()
        prompt_queue = None
        with self._lock:
            self._search_control = None
            prompt_queue = self._prompt_queue
            self._prompt_queue = None
        if prompt_queue is not None:
            prompt_queue.put("")

    def register_search_control(self, control):
        if self.start() is M.false_value:
            return M.false_value
        with self._lock:
            self._search_control = control
        return M.truth_value

    def unregister_search_control(self, control):
        with self._lock:
            if self._search_control is control:
                self._search_control = None

    def read_prompt(self, prompt_text):
        if self.start() is M.false_value:
            return ""
        prompt_queue = queue.Queue(maxsize=1)
        with self._lock:
            self._prompt_queue = prompt_queue
        try:
            sys.stdout.write(prompt_text + " ")
            sys.stdout.flush()
            return prompt_queue.get()
        finally:
            with self._lock:
                if self._prompt_queue is prompt_queue:
                    self._prompt_queue = None


class _SearchStopConsole:
    def __init__(self, console_input):
        self._console_input = console_input
        self._pause_event = threading.Event()
        self._requested_stop = threading.Event()
        self._command_lock = threading.Lock()
        self._requested_command = ""

    def start(self):
        return self._console_input.register_search_control(self)

    def handle_line(self, line):
        if self._pause_event.is_set():
            return
        command = line.strip().lower()
        if command == "":
            return
        with self._command_lock:
            self._requested_command = command
        if command == "stop" or command == "pause":
            self._requested_stop.set()
            _debug("search: " + command + " requested; handling at next checkpoint")
        else:
            _debug("search: queued console command '" + command + "'")

    def stop(self):
        self._pause_event.set()
        self._console_input.unregister_search_control(self)

    def pause(self):
        self._pause_event.set()

    def resume(self):
        stop_requested = M.truth_value if self._requested_stop.is_set() else M.false_value
        if stop_requested is M.truth_value:
            return
        self._pause_event.clear()

    def requested(self):
        if self._requested_stop.is_set():
            return M.truth_value
        return M.false_value

    def take_command(self):
        with self._command_lock:
            command = self._requested_command
            self._requested_command = ""
        if command == "stop" or command == "pause":
            self._requested_stop.clear()
        return command


class _SearchComparisonPromptGuard:
    def __init__(self, prompt_text="okay, this has gone on for long enough, proceed?"):
        self.prompt_text = prompt_text
        self.started_at = time.time()
        self._paused_at = None
        self.comparison_aborted = M.false_value
        self.time_prompt_step_seconds = 60
        self.next_time_prompt_seconds = self.time_prompt_step_seconds
        self.cost_prompt_step_units = 25
        self.next_cost_prompt_units = self.cost_prompt_step_units
        self.completed_cost_units = 0

    def _elapsed_seconds(self):
        elapsed = int(time.time() - self.started_at)
        if elapsed < 0:
            return 0
        return elapsed

    def _combined_cost_units(self, active_cost_units):
        return self.completed_cost_units + active_cost_units

    def _threshold_reached(self, active_cost_units):
        if self._elapsed_seconds() >= self.next_time_prompt_seconds:
            return M.truth_value
        if self._combined_cost_units(active_cost_units) >= self.next_cost_prompt_units:
            return M.truth_value
        return M.false_value

    def _advance_thresholds(self, active_cost_units):
        elapsed = self._elapsed_seconds()
        combined_cost_units = self._combined_cost_units(active_cost_units)
        while elapsed >= self.next_time_prompt_seconds:
            self.next_time_prompt_seconds += self.time_prompt_step_seconds
        while combined_cost_units >= self.next_cost_prompt_units:
            self.next_cost_prompt_units += self.cost_prompt_step_units

    def pause(self):
        if self._paused_at is not None:
            return
        self._paused_at = time.time()

    def resume(self):
        if self._paused_at is None:
            return
        self.started_at += time.time() - self._paused_at
        self._paused_at = None

    def maybe_prompt(self, search):
        active_cost_units = search._current_total_cost_units()
        if self._threshold_reached(active_cost_units) is M.false_value:
            return

        if M.IdentityCompare(search.graph._search_disable_console, M.truth_value)() is M.truth_value:
            self._advance_thresholds(active_cost_units)
            return

        search._pause_stop_listener()
        search._pause_progress_ticker()
        self.pause()
        proceed = M.false_value
        try:
            response = search._read_console_line(self.prompt_text)
            answer = response.strip().lower()
            if answer in ("y", "yes", "proceed"):
                proceed = M.truth_value
        finally:
            self.resume()
            search._resume_stop_listener()
            search._resume_progress_ticker()

        self._advance_thresholds(active_cost_units)
        if proceed is M.false_value:
            self.comparison_aborted = M.truth_value
            search.search_aborted = M.truth_value
            search.search_outcome_on_abort = SearchFailureLabel

    def record_completed_cost(self, cost_units):
        self.completed_cost_units += cost_units



def sync_from_namespace(namespace):
    for name in (
        "DFSLabel",
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
        "RewriteDFSLabel",
        "GoalHeadOrderLabel",
        "KnowledgeLabel",
        "ContextSearchComparisonJobsLabel",
        "ContextSearchJobsLabel",
        "SearchSignatureLabel",
        "SearchComparisonLabel",
        "SearchComparisonJobLabel",
        "SearchCostLabel",
        "SearchJobLabel",
        "SearchStateLabel",
        "SearchTheoremCursorLabel",
        "SearchRewriteCursorLabel",
        "SearchRewritePathFrameLabel",
        "SearchRewriteRuleBundleLabel",
        "SearchPairKeyLabel",
        "SearchCtorKeyLabel",
        "SearchPatriciaTokenLabel",
        "SearchPatriciaPairTokenLabel",
        "SearchPatriciaStopTokenLabel",
        "SearchPatriciaLeafLabel",
        "SearchPatriciaBranchLabel",
        "SearchPatriciaChoiceLabel",
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchRunningLabel",
        "SearchPausedLabel",
        "SearchTimedOutLabel",
        "SearchAbortedByUserLabel",
        "SearchRootFastPathPhaseLabel",
        "SearchPacketSearchPhaseLabel",
        "SearchNoRootFastPathLabel",
        "SearchRootCacheResultLabel",
        "SearchRootSchemaResultLabel",
        "SearchRootGoalResultLabel",
        "SearchRootImmediateResultLabel"
    ):
        if name in namespace:
            globals()[name] = namespace[name]
