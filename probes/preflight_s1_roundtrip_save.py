import sys, pickle
sys.path.insert(0, '/home/user')
import cat_theo_machine.machine as M
from cat_theo_machine import labels as Lmod
from cat_theo_machine import graph as Gmod
from cat_theo_machine.persistence import SnapshotCodec

registry = M.AllConstructors
name = M.Char("divides")
arity_atom = Gmod.RelationContractArity(name, M.two)()
ext_atom = Gmod.RelationContractExtensionalAt(name, M.one)()
record = Gmod.RelationContracts(
    M.Pair(arity_atom, M.Pair(ext_atom, M.EmptyList)),
    M.Char("operator-session-2026-09-05"),
)()
trie = Gmod.RelationContractsInsert(M.EmptyTree, record, registry)()

namespace = dict(vars(M))
namespace.update(vars(Lmod))
codec = SnapshotCodec(namespace)
snapshot = codec.capture_objects({"trie": trie, "arity_atom": arity_atom, "ext_atom": ext_atom})
with open("/tmp/probe/s1_snapshot.pkl", "wb") as fh:
    pickle.dump(snapshot, fh)
print("SAVE OK: objects in snapshot:", len(snapshot["objects"]),
      "| relation labels in symbols table:",
      sum(1 for n in snapshot["symbols"] if "Relation" in n or "Extensional" in n or "Contract" in n))
