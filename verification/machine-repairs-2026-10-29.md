# Machine repair results — 29 October 2026

The completed changes repair graph identity, failed-match history, interface
gluing, and finite-template operation selection. They also add explicit
composite Nat operations represented as Machine data.

## Demonstrated improvements

| Area | Earlier behavior | Verified behavior after repair |
| --- | --- | --- |
| Graph surgery | The new regression failed because an inserted edge retained the rule's endpoint. | The same assertion passes with distinct K, L, R and host identities. New edges attach to the matched host interface; the old graph and rule remain unchanged. |
| Mapping identity | Source inspection showed structural comparisons used for graph-element membership and mapping keys. | Separately allocated elements with identical structure remain distinct. Injectivity, relation labels and positional endpoints are checked, including endpoint extensions after an edge was mapped. |
| Failed alternatives | Rejected extensions were discarded by the alternatives path. | An explicit exploration records accepted and rejected attempts, including an all-rejected result. Accepted maps inherit the history. File-backed restoration preserves identity links. Stored outcomes are rechecked before reuse. |
| Finite templates | The new full-catalog regression failed even though its equations used one operation role. | The matcher derives the role from equation bodies. Unrelated catalog entries and display names do not choose it. Finite closure, equation replay and receipt scope remain required. |
| Composite operations | A fresh operation label and expression body were unavailable to evaluation before registration. | Registering the body x²+y enables f(2,3)=7. All nine tensor cells on {0,1,2}² agree with direct evaluation. A four-argument composite and save/reload also pass. No operation-specific Python class is added. |

The combined graph test enumerates a complete mapping, retains rejected
alternatives and fires a correctly glued rewrite. The existing live-proof
tests still close a pending equality after learning a checked law and retain
that behavior after restart.

The surgery and template failures were executed before their fixes. Mapping
and history deficiencies were established by source inspection; their repaired
behavior was executed afterward. No search-speed comparison or harder-theorem
benchmark was performed.

## Verification

`validation/run_machine_repair_checks.cmd` completed with exit code 0 through
the existing Anaconda environment. All nine suites passed:

- graph mapping regressions;
- graph surgery regressions;
- ten existing graph fixtures and the combined mapping-to-rewrite case;
- defined-operation regressions;
- existing operation-catalog regressions;
- existing tensor-axis regressions;
- finite-template matching regressions;
- named discovered-law certification and reuse;
- live proof, scope and snapshot restoration.

The runner saves separate logs beside this report. The original template
failure and initial successful repair are also retained in
`finite-template-catalog-before.log` and `finite-template-catalog-after.log`.

`core.py` was unchanged. Its SHA-256 before and after was
`8F06854B7C4828A1C94005A7036AFD60450FC5522E1E7D3BAD549AD6A1B1FDE1`.

## Remaining limits

Composite definitions contain only declared formals, nonnegative Nat
constants, addition, multiplication and literal natural powers. They cannot
redefine primitives or call other custom definitions. Each use revalidates
the stored body. Definition metadata grants no polynomial proof authority,
and custom finite-template roles remain unsupported. Candidate generation
still uses its existing supplied grammar.

The finite-template matcher supports one operation role, derived from an
ambient catalog. A true multiple-operation correspondence needs a separate
explicit binding contract.

Graph insertion retains the existing explicit-admission convention for R\K
nodes and refuses identity collisions. Fresh copying of arbitrary node
payloads, new-edge dependency cycles and unproved nonempty rule obligations
remain unsupported; these cases are refused. The legacy alternatives-only
projection retains history in accepted maps; an all-rejected history must be
retained through the explicit exploration result.
