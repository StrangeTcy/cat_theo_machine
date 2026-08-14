import sys, os
sys.path.insert(0, r"Q:\")
from hyge.runtime import boot_from_packs
from hyge import machine as M
pack_dir = r"Q:\hyge\packs"
names = ["order-sign","sqrt-real","algebra-distribute","real-closure","arithmetic","geometry-ontology","trigonometry","geometry"]
paths = [os.path.join(pack_dir, n + ".pack.yaml") for n in names]
import yaml
for p in paths:
    with open(p, encoding="utf-8") as f:
        d = yaml.safe_load(f)
    assert d.get("format") == "hyge-pack", ("BAD FORMAT", p)
    print("PARSE_OK", os.path.basename(p), "rules:", len(d.get("rules", ())))
namespace = {}
runtime, loaded = boot_from_packs(paths, namespace)
print("LOADED_PACKS", len(loaded))
assert len(loaded) == 8, len(loaded)
total = sum(len(pk.rule_map) for pk in loaded)
print("RULE_MAP_TOTAL", total)
graph = runtime.graph
all_rules = M.FromContextGetAllRules(graph)()
cnt = 0
cur = all_rules
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    cnt += 1
    cur = M.Tail(cur)()
print("GRAPH_RULES", cnt)
assert total == 74 and cnt == 74, (total, cnt)
print("PACK_LOAD_ASSERTS_OK")
