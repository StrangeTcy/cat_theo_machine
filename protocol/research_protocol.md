# Protocol index (INT)

Wave-1 engineers branch from the tag named below. This file is the index.
Track ledgers: protocol/S.md, protocol/E.md, protocol/G.md, protocol/I.md,
protocol/F.md.

## wave-1 base tag

Named at the preflight tag cut. The git tag on this commit is
`preflight-<shortsha>`. Wave 1 branches from that tag. The earlier tag
`preflight-e73d748` stands and is not the wave-1 base.

```text
wave 1 base tag: preflight-<shortsha>@<hash>
```

## interface ownership (from this tree)

| file | symbol | owner | change path |
|---|---|---|---|
| planner.py | PlannerAlternative(parent_obligation_id, method, child_obligation_ids, status, evidence) | INT | [SHARED] proposal |
| planner.py | Extremal, Pigeonhole, Divide, Symmetry, Induction, Bijection, DoubleCount | INT | [SHARED] proposal |
| testsuite.py | _register_test(graph, name, input_nodes, computation_edge, expected) | INT | [SHARED] proposal |
| graph.py | Test, TestShardAccept, TestShardConfigure | INT | [SHARED] proposal |
| persistence.py | SnapshotCodec | INT | [SHARED] proposal |
| packs.py | PackLoader.load_pack_file | INT | [SHARED] proposal |
| labels.py | ConstructorLabel instances; SNAPSHOT_SYMBOL_NAMES | INT | [SHARED] proposal |
| research.py | absent on this lineage | INT | [SHARED] proposal |
| provenance classes | not a separate module on this tree | INT | [SHARED] proposal |

Learned-memory mask and rent/counterfactual machinery are not present as
named modules here. They enter only by [SHARED] proposal.

## marked blocks

Empty `# --- [S] ---`, `# --- [E] ---`, `# --- [G] ---`, `# --- [F] ---`
appended in labels.py and testsuite.py. research.py is absent. main.py
dispatch is not partitioned this cut (no research verbs on this tree).
