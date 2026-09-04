#!/usr/bin/env python3
"""Apply deltas 3 (label registration) and 4 (guard count) to a rehearsal tree.

Delta 3 (SHARED, same port commit): register the five S labels in both
labels.sync_from_namespace and persistence.SNAPSHOT_SYMBOL_NAMES. The
label_registration_completeness_test pins stay UNCHANGED at 40 / 198 / 18
(registering keeps them put; the pins move only downward).

Delta 4 (same port commit): TestShardCursorPinTest.EXPECTED_GUARD_COUNT
305 -> 310. The hard pin (EXPECTED_CURSOR_INDEX 218, EXPECTED_SHARD 0)
holds unchanged because the registrations land after every existing test.
"""
import os

BASE = os.environ.get("REHEARSE_BASE", "/tmp/cat_theo_machine")

# --- delta 3a: sync_from_namespace ---
p = os.path.join(BASE, "labels.py")
s = open(p).read()
anchor = '        "InvarianceLabel",\n    ):'
assert anchor in s, "sync tuple anchor not found"
add = ('        "InvarianceLabel",\n'
       '        "TraceLabel",\n'
       '        "MotifLabel",\n'
       '        "CompressedLawLabel",\n'
       '        "RefusedLabel",\n'
       '        "CandidateObservableLabel",\n'
       '    ):')
s = s.replace(anchor, add, 1)
open(p, "w").write(s)
print("labels.py sync tuple updated")

# --- delta 3b: SNAPSHOT_SYMBOL_NAMES ---
p = os.path.join(BASE, "persistence.py")
s = open(p).read()
anchor = '    "CorrespondenceLawLabel",\n    "ZeroLabel",\n'
assert anchor in s, "snapshot list anchor not found"
add = ('    "CorrespondenceLawLabel",\n'
       '    "ZeroLabel",\n'
       '    "TraceLabel",\n'
       '    "MotifLabel",\n'
       '    "CompressedLawLabel",\n'
       '    "RefusedLabel",\n'
       '    "CandidateObservableLabel",\n')
s = s.replace(anchor, add, 1)
open(p, "w").write(s)
print("persistence.py snapshot list updated")

# --- delta 4: guard count ---
p = os.path.join(BASE, "testsuite.py")
s = open(p).read()
anchor = "    EXPECTED_GUARD_COUNT = 305\n"
assert anchor in s, "guard count anchor not found"
s = s.replace(anchor, "    EXPECTED_GUARD_COUNT = 310\n", 1)
open(p, "w").write(s)
print("testsuite.py guard count 305 -> 310")
