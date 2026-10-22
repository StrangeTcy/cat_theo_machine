# Coordination bundle validation

- JSON parses: PASS (task manifest and baseline receipt).
- Unique task IDs: PASS (20).
- Acceptance references: PASS (37 probe IDs).
- Launch dependency DAG: PASS (topological sort; no unknown IDs or self-edges).
- Worker path ownership: PASS (no duplicate/overlapping write surfaces or forbidden paths).
- Both checkers required; generators independent and not on integration-only readiness path: PASS.
- Base SHA/tree and fixed session branch: PASS.
- Measured source and evidence hashes: PASS.
- Local Markdown links/code fences and both reproduction snippets parse: PASS.
- Documented cold-save/load reproducer executed: PASS as a reproducer of the expected baseline failure (save 0; load 1; two missing derivation constructors).
- Machine/runtime source changes: NONE.

Dependency-ready waves (tasks within a wave may start in parallel; real input acceptance is later):

1. `CL0`
2. `F1`, `F2`
3. `CL0R`
4. `CL1`, `CLT`
5. `CONTRACT`
6. `CL2A`, `CL2B`, `CL3A`, `CL3B`, `CL4`, `CL5`, `CL6`, `CL7`, `CL8`, `CL9`
7. `CL10`
8. `CL9F`
9. `REL`

**These checks validate the specification/data bundle, not the unimplemented experimental harness or a Machine release.**
Known runtime results remain: five focused passes, bounded trace pass, cold semantic restore failure, full suite incomplete.
Real-input cross-check references intentionally describe wired integration tests, not launch edges; they may be mutual between stub-developed modules.
