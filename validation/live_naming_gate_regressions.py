"""Exercise the real live process with stdin held open at the naming boundary.

Run through run_live_naming_gate_checks.cmd to retain the package import root
when the child writes its session files inside a temporary directory.
"""

import os
import subprocess
import sys
import tempfile
import time

from hyge import live_naming as LN
from hyge import machine as M
from hyge import runtime
from hyge.math import arithmetic as A


class AwaitNamingTranscript(M.Edge):
    def __init__(self, path, marker, remaining, registry):
        with open(path, encoding="utf-8") as transcript_file:
            transcript = transcript_file.read()
        before, separator, after = transcript.partition(marker)
        if M.Compare(M.Char(separator), M.Char(marker))() is M.truth_value:
            result = M.Char(transcript)
        else:
            assert M.NatEq(remaining, M.Zero, registry)() is M.false_value, transcript[-2000:]
            time.sleep(0.1)
            reduced = A.NatSubtract(remaining, M.one, registry)()
            result = AwaitNamingTranscript(path, marker, M.Head(reduced)(),
                M.Head(M.Tail(reduced)())())()
        super().__init__(inputs=M.Pair(M.Char(path), M.Char(marker)), results=result)


class CheckNamingInputPaused(M.Edge):
    def __init__(self, process, path, expected_transcript):
        waiting = M.false_value
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            waiting = M.truth_value
        assert waiting is M.truth_value
        with open(path, encoding="utf-8") as transcript_file:
            transcript = transcript_file.read()
        assert M.Compare(M.Char(transcript), expected_transcript)() is M.truth_value
        super().__init__(inputs=M.Pair(M.Char(path), expected_transcript), results=M.truth_value)


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
    registry = M.FromContextGetConstructors(rt.graph)()
    budget_result = M.NatFromRep(M.GMPRep("600"), registry)()
    budget = M.Head(budget_result)()
    registry = M.Head(M.Tail(budget_result)())()
    assert M.Compare(LN.DiscoveryNameText(M.Char("Call this symmetry"))(), M.Char("symmetry"))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("yes, call this symmetry"))(), M.Char("symmetry"))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("call this "))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("  "))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("proof story"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("continue"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("go on"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("judge"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("candidates"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("why that"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("status of claim x"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("let us work on x"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("call this proof story"))(), M.Char("proof story"))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("commutativity"))(), M.Char("commutativity"))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("show structure"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("suggest lemmas"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("prove x=x"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("solve tao"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("run self-diagnostics"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("next"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("quit"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("skip"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("no"))(), M.Char(""))() is M.truth_value
    assert M.Compare(LN.DiscoveryNameText(M.Char("call this show structure"))(), M.Char("show structure"))() is M.truth_value
    evidence_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "verification")

    with tempfile.TemporaryDirectory(prefix="hyge-naming-gate-") as session_directory:
        transcript_path = os.path.join(session_directory, "session.log")
        snapshot_path = os.path.join(session_directory, "session.json")
        with open(transcript_path, "w", encoding="utf-8") as child_output:
            child = subprocess.Popen((sys.executable, "-B", "-u", "-m", "hyge.main", "live",
                "--live-snapshot", snapshot_path), cwd=session_directory,
                stdin=subprocess.PIPE, stdout=child_output, stderr=subprocess.STDOUT, encoding="utf-8")
            try:
                child.stdin.write("suggest lemmas\n")
                child.stdin.flush()
                paused = AwaitNamingTranscript(transcript_path, "[you] Name this property: ", budget, registry)()
                before, observed, following = paused().partition("[machine] Observed:")
                assert M.Compare(M.Char(observed), M.Char("[machine] Observed:"))() is M.truth_value
                report, prompt, rest = following.partition("[you] Name this property: ")
                assert M.Compare(M.Char(prompt), M.Char("[you] Name this property: "))() is M.truth_value
                assert M.Compare(M.Char(rest), M.Char(""))() is M.truth_value
                assert M.Compare(M.Char(paused().replace("Saved finite structure evidence", "")), paused)() is M.truth_value
                assert M.Compare(M.Char(paused().replace("Recorded '", "")), paused)() is M.truth_value
                CheckNamingInputPaused(child, transcript_path, paused)()
                print("PASS the real suggest-lemmas process stops at the name input after displaying its equation and examples")

                child.stdin.write("\n")
                child.stdin.flush()
                blank_paused = AwaitNamingTranscript(transcript_path,
                    "A nonempty name is required before continuing.\n[you] Name this property: ", budget, registry)()
                CheckNamingInputPaused(child, transcript_path, blank_paused)()
                child.stdin.write("call this \n")
                child.stdin.flush()
                empty_phrase_paused = AwaitNamingTranscript(transcript_path,
                    "[you] Name this property: [machine] A nonempty name is required before continuing.\n[you] Name this property: [machine] A nonempty name is required before continuing.\n[you] Name this property: ",
                    budget, registry)()
                CheckNamingInputPaused(child, transcript_path, empty_phrase_paused)()
                print("PASS blank input and an empty naming phrase stay gated with no replay, structure work or next scan")

                child.stdin.write("show structure\n")
                child.stdin.flush()
                command_paused = AwaitNamingTranscript(transcript_path,
                    "Name this discovery before using other commands.\n[you] Name this property: ", budget, registry)()
                CheckNamingInputPaused(child, transcript_path, command_paused)()
                assert M.Compare(M.Char(command_paused().replace("Recorded '", "")), command_paused)() is M.truth_value
                assert M.Compare(M.Char(command_paused().replace("Observed structure candidate on finite carrier", "")), command_paused)() is M.truth_value
                print("PASS a bare show-structure command stays gated without naming or command execution")
                child.stdin.write("call this show structure\n")
                child.stdin.flush()
                finished = AwaitNamingTranscript(transcript_path,
                    "[machine] Named discovery is available to the next warm playground run.\nyou> ", budget, registry)()
                before_record, record, after_record = finished().partition("[machine] Yes, recorded to talk_lessons.log.")
                assert M.Compare(M.Char(record), M.Char("[machine] Yes, recorded to talk_lessons.log."))() is M.truth_value
                before_replay, replay, after_replay = after_record.partition("[machine] Saved finite structure evidence.")
                assert M.Compare(M.Char(replay), M.Char("[machine] Saved finite structure evidence."))() is M.truth_value
                assert M.Compare(M.Char(before_record.replace("Saved finite structure evidence", "")), M.Char(before_record))() is M.truth_value
                with open(os.path.join(session_directory, "talk_lessons.log"), encoding="utf-8") as lesson_file:
                    lessons = lesson_file.read()
                before_name, name, after_name = lessons.partition("Lesson named: 'show structure'")
                assert M.Compare(M.Char(name), M.Char("Lesson named: 'show structure'"))() is M.truth_value
                child.stdin.write("quit\n")
                child.stdin.flush()
                assert M.Compare(M.Char(str(child.wait(timeout=30))), M.Char("0"))() is M.truth_value
                print("PASS an explicit naming phrase records the name before finite structure replay")
            finally:
                child.stdin.close()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=10)
        with open(transcript_path, encoding="utf-8") as transcript_file:
            with open(os.path.join(evidence_directory, "live-naming-gate-suggest-2026-10-30.log"), "w", encoding="utf-8") as evidence_file:
                evidence_file.write(transcript_file.read())

    with tempfile.TemporaryDirectory(prefix="hyge-naming-eof-") as session_directory:
        transcript_path = os.path.join(session_directory, "session.log")
        snapshot_path = os.path.join(session_directory, "session.json")
        with open(transcript_path, "w", encoding="utf-8") as child_output:
            child = subprocess.Popen((sys.executable, "-B", "-u", "-m", "hyge.main", "live",
                "--live-snapshot", snapshot_path), cwd=session_directory,
                stdin=subprocess.PIPE, stdout=child_output, stderr=subprocess.STDOUT, encoding="utf-8")
            try:
                child.stdin.write("prove x+y=y+x\nyes, 0 to 1\n")
                child.stdin.flush()
                paused = AwaitNamingTranscript(transcript_path, "[you] Name this property: ", budget, registry)()
                before, observed, following = paused().partition("[machine] Observed on tested domain")
                assert M.Compare(M.Char(observed), M.Char("[machine] Observed on tested domain"))() is M.truth_value
                CheckNamingInputPaused(child, transcript_path, paused)()
                child.stdin.close()
                assert M.Compare(M.Char(str(child.wait(timeout=30))), M.Char("0"))() is M.truth_value
            finally:
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=10)
        with open(transcript_path, encoding="utf-8") as transcript_file:
            transcript = transcript_file.read()
        before, prompt, after = transcript.partition("[you] Name this property: ")
        assert M.Compare(M.Char(after.replace("Recorded '", "")), M.Char(after))() is M.truth_value
        assert M.Compare(M.Char(after.replace("Saved finite structure evidence", "")), M.Char(after))() is M.truth_value
        assert M.Compare(M.Char(after.replace("Pairwise comparing operation results", "")), M.Char(after))() is M.truth_value
        with open(os.path.join(evidence_directory, "live-naming-gate-playground-eof-2026-10-30.log"), "w", encoding="utf-8") as evidence_file:
            evidence_file.write(transcript)
        print("PASS the playground path also blocks immediately; EOF exits without recording a name or replaying a structure")

    with tempfile.TemporaryDirectory(prefix="hyge-naming-compatibility-") as session_directory:
        snapshot_path = os.path.join(session_directory, "session.json")
        completed = subprocess.run((sys.executable, "-B", "-u", "-m", "hyge.main", "live",
            "--live-snapshot", snapshot_path), cwd=session_directory,
            input="prove x+y=y+x\nyes, 0 to 1\ncall this compatibility symmetry\nshow goal\nquit\n",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", timeout=90)
        assert M.Compare(M.Char(str(completed.returncode)), M.Char("0"))() is M.truth_value
        before_name, named, after_name = completed.stdout.partition("Recorded 'compatibility symmetry'")
        assert M.Compare(M.Char(named), M.Char("Recorded 'compatibility symmetry'"))() is M.truth_value
        before_replay, replay, after_replay = after_name.partition("Saved finite structure evidence.")
        assert M.Compare(M.Char(replay), M.Char("Saved finite structure evidence."))() is M.truth_value
        with open(os.path.join(evidence_directory, "live-naming-gate-compatibility-2026-10-30.log"), "w", encoding="utf-8") as evidence_file:
            evidence_file.write(completed.stdout)
        print("PASS existing call-this input scripts still name the playground discovery and resume afterward")
    print("Live naming gate regressions passed.")
