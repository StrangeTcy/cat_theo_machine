"""Cold-load half of the S1 checkpoint round-trip (2026-09-05).

Run AFTER probes/preflight_s1_roundtrip_save.py in a FRESH interpreter:
loads /tmp/probe/s1_snapshot.pkl through SnapshotCodec with
_runtime_namespace_for_restore() and prints identity/structural/HasFact
verdicts for the restored contract atoms and trie. Evidence for
verification/2026-09-05-s1-checkpoint-roundtrip.txt.
"""
import sys
import pickle

sys.path.insert(0, "/home/user")

import cat_theo_machine.machine as M
from cat_theo_machine import labels as Lmod
from cat_theo_machine import knowledge as Kmod
from cat_theo_machine import graph as Gmod
from cat_theo_machine.persistence import SnapshotCodec, _runtime_namespace_for_restore

with open("/tmp/probe/s1_snapshot.pkl", "rb") as fh:
    snapshot = pickle.load(fh)

loaded = SnapshotCodec(_runtime_namespace_for_restore()).load_snapshot(snapshot).roots
arity_atom = loaded["arity_atom"]
ext_atom = loaded["ext_atom"]
trie = loaded["trie"]

label = M.Head(arity_atom)()
print("1. loaded head IS module RelationArityLabel:", label is Lmod.RelationArityLabel)
fresh = Gmod.RelationContractArity(M.Char("divides"), M.two)()
print("2. structural Compare(restored, fresh):", M.Compare(arity_atom, fresh)() is M.truth_value)
print("3. trie HasFact(restored arity atom):",
      Kmod.KnowledgeTrieHasFact(trie, arity_atom, M.AllConstructors)() is M.truth_value)
print("4. trie HasFact(restored ext atom):",
      Kmod.KnowledgeTrieHasFact(trie, ext_atom, M.AllConstructors)() is M.truth_value)
print("5. restored head type:", type(label).__name__)
