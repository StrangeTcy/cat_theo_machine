from __future__ import annotations

from .. import machine as M
from ..labels import *
from ..proof import _debug
from .ui import _SearchConsoleInput, _SearchStopConsole


class _ComparisonConsoleMixin:
    def _comparison_console_input(self):
        console_input = self.graph._search_console_input
        if console_input is None:
            console_input = _SearchConsoleInput()
            self.graph._search_console_input = console_input
        return console_input

    def _start_stop_listener(self):
        if M.IdentityCompare(self.graph._search_disable_console, M.truth_value)() is M.truth_value:
            self._stop_listener = None
            return
        self._stop_listener = _SearchStopConsole(self._comparison_console_input())
        if M.IdentityCompare(self._stop_listener.start(), M.truth_value)() is M.false_value:
            self._stop_listener = None
            _debug("search-compare: console control unavailable in this environment")
            return
        if M.IdentityCompare(self.graph._search_stop_help_shown, M.truth_value)() is M.false_value:
            print("Type 'pause', 'stop', 'stop <mode>', or 'only <modes>' and press Enter in the console to control the current comparison or search.")
            self.graph._search_stop_help_shown = M.truth_value
        _debug("search-compare: console control ready")

    def _stop_stop_listener(self):
        if self._stop_listener is None:
            return
        self._stop_listener.stop()
        self._stop_listener = None

    def _pause_requested(self):
        if self._stop_listener is None:
            return M.false_value
        if M.IdentityCompare(self._stop_listener.requested(), M.truth_value)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _consume_console_action(self):
        if self._stop_listener is None:
            return "none", M.EmptyList
        command = self._stop_listener.take_command()
        if command == "":
            return "none", M.EmptyList
        action, modes = self._comparison_prompt_action(command)
        if action == "help" or action == "unknown":
            _debug("search-compare: commands are continue | extend | stop | pause | stop <mode> | only <modes>")
            return "none", M.EmptyList
        return action, modes

    def _read_console_line(self, prompt_text):
        return self._comparison_console_input().read_prompt(prompt_text)

    def _mode_from_token(self, token):
        if token in ("dfs", "searchdfs"):
            return DFSLabel
        if token in ("bfs", "searchbfs"):
            return BFSLabel
        if token in ("astar", "a*", "searchastar"):
            return AStarLabel
        if token in ("beam", "searchbeam"):
            return BeamLabel
        if token in ("rewritedfs", "rewrite-dfs", "searchrewritedfs"):
            return RewriteDFSLabel
        return M.EmptyList

    def _mode_selected(self, modes, mode):
        if M.IdentityCompare(modes, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(M.Head(modes)(), mode)() is M.truth_value:
            return M.truth_value
        return self._mode_selected(M.Tail(modes)(), mode)

    def _selected_modes_from_tokens(self, tokens, index):
        if index >= len(tokens):
            return M.EmptyList
        mode = self._mode_from_token(tokens[index])
        rest = self._selected_modes_from_tokens(tokens, index + 1)
        if M.Compare(mode, M.EmptyList)() is M.truth_value:
            return rest
        if self._mode_selected(rest, mode) is M.truth_value:
            return rest
        return M.Pair(mode, rest)

    def _comparison_prompt_action(self, response):
        answer = response.strip().lower()
        if answer in ("", "y", "yes", "continue", "continue all", "proceed"):
            return "continue", M.EmptyList
        if answer in ("extend", "more", "continue longer"):
            return "extend", M.EmptyList
        if answer in ("stop", "abort", "quit", "stop comparison"):
            return "stop", M.EmptyList
        if answer == "pause":
            return "pause", M.EmptyList
        if answer in ("help", "?"):
            return "help", M.EmptyList
        tokens = answer.split()
        if len(tokens) >= 2 and tokens[0] in ("stop", "kill"):
            mode = self._mode_from_token(tokens[1])
            if M.Compare(mode, M.EmptyList)() is M.false_value:
                return "stop_mode", mode
        if len(tokens) >= 2 and tokens[0] == "only":
            modes = self._selected_modes_from_tokens(tokens, 1)
            if M.IdentityCompare(modes, M.EmptyList)() is M.false_value:
                return "only_modes", modes
        return "unknown", M.EmptyList

    def _comparison_read_action(self, summary_text):
        prompt_text = summary_text + "; actions: continue | extend | stop | pause | stop <mode> | only <modes>"
        while M.IdentityCompare(M.truth_value, M.truth_value)() is M.truth_value:
            try:
                response = self._read_console_line(prompt_text)
            except (EOFError, KeyboardInterrupt):
                response = "stop"
            action, modes = self._comparison_prompt_action(response)
            if action == "help" or action == "unknown":
                _debug("search-compare: commands are continue | extend | stop | pause | stop <mode> | only <modes>")
                continue
            return action, modes



def sync_from_namespace(namespace):
    for name in (
        "DFSLabel",
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
        "RewriteDFSLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonConsoleMixin")]
