# Live FLT audit — 2026-10-28

The Machine does not currently prove FLT. A fresh execution of the real
`hyge.main live` entry point returned `Pending` for the full no-solutions
claim before exploration, after exploration, on retry, and after restart.
No FLT proof receipt or new active law was produced.

## Interventions and dimensions

| Intervention | Dimension improved and reason | Limit |
| --- | --- | --- |
| Run the full FLT claim through a fresh session and restart | Proving FLT: establish the current proof boundary against the actual entry point. Self-improvement: retain reproducible evidence. | This is verification of capability, not an additional mathematical proof step. |
| Render all retained scope fields in `live_proof.py` | Storytelling/explanations in a natural language: show positivity, exponent parameters and parameter restrictions together with the original claim and remaining obligation. | It reports the parsed scope; the original wording remains authoritative. No new search or trusted rule. |
| Replace fixed range shortcuts with `ParsePlaygroundDomain` | Self-improvement: permit arbitrary user-selected finite discovery domains. Storytelling/explanations in a natural language: make the range prompt match its accepted grammar. | A finite operation-law scan does not establish FLT. |
| Mark the old quartic account as superseded | Storytelling/explanations in a natural language; self-improvement: prevent withdrawn authored rules from being treated as current proof evidence. | Historical text is preserved under an explicit notice. |
| Update DAG G0 and add the replay command | Self-improvement: mark only the verified node complete and make its evidence reproducible. | G1-G5, cubic descent and quartic universal movement remain open. |

No new IMO solution or learned Engel strategy is claimed. `core.py` was
not edited. New semantic code uses native Edge constructors, Pair chains
and machine truth atoms; no new helper functions or monkeypatches were added.

## Actual live output

```text
Pending: prove there are no positive integers x, y, z and n > 2 such that x^n + y^n = z^n
Parsed relation: x^n + y^n = z^n.
Claim: no solutions in the stated scope.
Base variables: x, y, z.
Domain restriction: positive variables.
Exponent parameters: n.
Parameter restrictions: 2 < n.
Required proof: exclude every assignment satisfying the original request. Finite observations alone do not establish this.
The no-solutions claim is preserved. A universal exclusion or descent proof is still required.
```

Answering `yes, 1 to 2` now runs the operation-law playground on `{1,2}`.
It observes addition symmetry. The observation was left unnamed. This
does not check all FLT assignments or construct a descent.

## Evidence and reproduction

- `live-flt-audit-2026-10-28.log`: fresh live request, range acceptance,
  operation-law observation, show, retry, explanation and save.
- `live-flt-audit-resume-2026-10-28.log`: restore, show, retry, explanation
  and save of the unchanged pending claim.
- `live-flt-audit-29697-12375.json`: saved graph from this run.
- `live_proof_regressions`: passed; learned equality reuse, nested and
  multistep replay, scoped/malformed refusals, reflexivity and snapshot reuse.
- `live_domain_regressions`: passed; arbitrary inclusive ranges,
  multi-digit and singleton bounds, zero and positive scopes, malformed,
  negative and reversed-bound refusals.
- `playground_edge_regressions`: passed; existing playground parser,
  expression and witness-boundary controls.

The commands ran through the repository's established Anaconda `hyge`
environment. Run `validation\run_flt_live_audit.cmd` from `X:\hyge` to
repeat the recorded fresh-session and restart sequence with a new snapshot.

The unresolved quartic obligation is `EveryStateMoves(descent)`: construct
a smaller valid solution from every hypothetical primitive solution. The
cubic branch still lacks universal division, unique factorization and
descent. Exponents 3 and 4 alone would also leave the other odd primes.
