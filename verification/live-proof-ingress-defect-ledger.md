# Live proof ingress — instrument defect ledger and INT handoff

## Scope and provenance

- Classification: **SEMANTIC** — parser dispatch, worker goal transport, normalization.
- Fork base: `41e80785d4de090337a9dfc08439f2fcb45915dc`.
- Verified cumulative runtime candidate: `033491542b2b4769bca3261e7df9982bd6084873`.
- Original evidence commit: `155e444efcd58fc5c02161673636e8c9faed1fc7`.
- Original `expected-left-parenthesis` instance: **not reproduced**. Its emitting commit is unrecorded; see `live-proof-ingress-before.txt`.
- The entries below are separate pre-existing instrument defects exposed by ingress verification, not three additional parser bugs.

## D-WORKER-GOAL-SUBSTITUTION

**Severity: severe. Status: fixed in the verified cumulative candidate.**

The comparison-worker launcher wrote only pretty-printed start/goal text. The worker matched that text against bundled theorem examples. An unmatched goal fell back to the first example, substituting a different problem for the requested one.

**Measurement impact:** prior `compare_search_modes` results on non-bundled goals are suspect until the requested and received goals are independently established. Do not infer performance or correctness for the requested problem from those results. The parked subsystem and its REVIVE-LATER ruling require review in light of this defect; this ledger does not itself revise that ruling or assert that every historical result was wrong.

**Fix:** start and goal machine terms are transported through the existing wire codec. The worker records the decoded request and search goal. Missing or unmatched legacy requests refuse a substitute theorem. The active path no longer selects a problem by display text.

- Implementation: `1e8aab6d59fd2e7903f7c030fdf4fc870a94c3c0`.
- Verified with the subsequent scope fix in: `033491542b2b4769bca3261e7df9982bd6084873`.
- Evidence: 15/15 automated and 5/5 independent-session worker receipts matched by machine structural equality; the automated receipt files are retained under `live-proof-ingress-receipts/search_compare/`.
- Required review recipients: **INT, C-eng, Layer-D**. Their worker-result validation assumptions must be revisited. Routing is recorded here as the handoff requirement; no separate lane notification is claimed.

## D-HEURISTIC-REORDER-CROSS-PROCESS

Alias in the operator summary: **D-HEURISTIC-REORDER**.

**Status: fixed for quantified goal trees in the verified cumulative candidate.**

Heuristic arithmetic normalization reordered symbolic operands using runtime identities. The resulting goal structure could differ across processes, so quantified goal trees did not remain structurally identical between parsing, comparison coordination, and worker search.

**Measurement impact:** cross-process goal identity was not stable. Structurally different receipts cannot be accepted as evidence of identical requested problems without an independently justified equivalence check.

**Fix:** heuristic normalization leaves the explicit quantified goal tree intact. This preserves the scope-bearing syntax; it does not weaken a proof checker or add an axiom. It is not a claim that all other symbolic normalization is now process-independent.

- Implementation and verified candidate: `033491542b2b4769bca3261e7df9982bd6084873`.
- Evidence: direct parser, dispatcher, foreground coordinator, worker request, decoded receipt, and search-goal structural checks; 15/15 automated plus 5/5 independent worker receipts.
- Required review recipients: **INT, C-eng, Layer-D**.

## D-ISOLATED-STATE-RESULT-DIR

**Status: fixed in the verified cumulative candidate.**

The comparison search-result directory ignored the isolated-state setting and used the checkout's shared `snapshots/search_compare` directory.

**Measurement impact:** an ostensibly isolated run could write search evidence into shared state and inspect shared cached worker results. Isolating only the conversation/daemon checkpoint directory was insufficient.

**Fix:** the comparison result root honors `HYGE_SNAPSHOT_DIR`, consistent with the live conversation and daemon. Verification used fresh isolated directories, checked shared-state content hashes before and after, and checked preservation of a foreign daemon marker.

- Implementation: `1e8aab6d59fd2e7903f7c030fdf4fc870a94c3c0`.
- Verified cumulative candidate: `033491542b2b4769bca3261e7df9982bd6084873`.
- Evidence: `live-proof-ingress-tests.txt`, `live-proof-ingress-after.txt`, and the raw live transcripts.
- Required review recipients: **INT, C-eng, Layer-D**.

## Lineage and import gate

`41e8078` is this lane's fork base, **not** the `ef571b6`-descended INT line. INT must rehearse-import the candidate onto the current INT tip by exact SHA; **do not merge this branch**. This lane has not performed that import.

The candidate is cumulative, not a standalone final-commit patch. Its implementation sequence, in dependency order, is:

1. `41bcbf4f9fac4ee7b5ae5ab117724f0040a3e7df` — ingress parser, dispatch, submission, diagnostics and regressions.
2. `a5c4efdf27c2beff1aeb5fc8462ab115f47f8c6a` — daemon package routing and isolated live state.
3. `1e8aab6d59fd2e7903f7c030fdf4fc870a94c3c0` — worker goal transport and isolated comparison result directory.
4. `033491542b2b4769bca3261e7df9982bd6084873` — quantified normalization boundary and real worker-receipt verification.

This checkout lacks `research.py`. After import, re-verify the parser route against the INT research-mode grammar it is supposed to share. Passing this lane's live tests does not establish that integration.

Required INT gates:

- Rehearse-import onto the current `ef571b6`-descended INT tip.
- Focused acceptance rerun, including exact positive-domain submission, zero submissions for clarification/malformed input, and structural worker receipts.
- Both test shards.
- Operator blank controls.
- Successor tag under INT authority, after its gates pass. No tag was cut by this lane.

## Lane disposition

Parser-ingress ticket: closed within its verified scope, with the before-state caveat recorded. The authorized sandbox acceptance run passed 8/8 groups with exit 0; the Windows Anaconda fixture was not executed here. Proof searches stalled and no theorem was asserted.

Ready for INT: **yes, by rehearse-import**, not direct branch merge. The INT gates above remain pending. Next owner: **INT**.
