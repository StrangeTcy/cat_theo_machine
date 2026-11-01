# Machine continuation — 30 October 2026

## Naming now blocks the live flow

The live session displays the observed equation and examples, then blocks at
`[you] Name this property:`. No name recording, structure replay or next scan
runs before a nonempty name is entered. Empty replies and empty naming
phrases return to the same prompt. Bare commands stay at this prompt without
being executed or recorded as names; an explicit naming phrase can still
use that text as a name. EOF or interruption exits the input boundary.

The name is recorded before optional structure replay. A failed replay keeps
the named observation and does not prevent snapshot saving. The first
`suggest lemmas` scan also retains the effective operation catalogue for
the subsequent replay.

This was checked with real live subprocesses whose stdin remained open:
stdout stayed unchanged at the prompt, including after blank input. The
test then supplied a name and verified that recording preceded replay.
The playground entry path was also stopped at its prompt and tested with
EOF. Existing `call this ...` input remains supported.

The running live process must be restarted to load the changed code.

## Additional demonstrated capabilities

| Capability | Previously | Verified now |
| --- | --- | --- |
| Registered operation composition | Registering an expression calling an earlier custom definition was refused. | With `f(x)=x²+1`, `g(x,y)=f(x)y` evaluates `g(2,3)=15`; a further nested definition evaluates to 25. Anonymous substitution, all nine tensor cells, dependency checks and restoration pass. |
| Several operation roles | The single-operation matcher refuses a mixed equation template. | A miner-generated multiplication-over-gcd equation matches with two explicit bindings. Both registered and composed targets work, as do custom source roles. Closure and all eight assignments on `{0,1}` are checked. |
| Edges depending on inserted edges | A reversed acyclic edge declaration failed insertion. | Three dependent edges are constructed with shared endpoints and the requested insertion order. Preserved interface edges retain identity. Separate firings create fresh edges. Cycles and unresolved endpoints refuse the entire insertion. |
| Custom operations in observations | Mining succeeded, but building the observation bundle returned empty. | Bundle creation, replay, live recording, explanation and file-backed restoration succeed for a registered operation. |
| Larger observation replay | A diagnostic for addition commutativity on `{1…10}` returned an empty bundle. | The same finite scope with the full default catalogue builds and verifies. A cursor follows matching witness order and retains the original membership check for reordered or repeated witnesses. |

Primitive-only records retain the v1 format. Composed v2 records retain the
source expression, primitive expansion and exact dependency records. Every
use validates their agreement. Changed dependencies, forged expansions,
cycles, wrong arities and descriptor argument identity substitutions are
refused. Custom metadata grants no polynomial proof authority.

Multiple-operation receipts bind the template, complete correspondence,
carrier, executable definitions and replay evidence. Changing a definition
invalidates the receipt even when its values still agree on the tested
carrier. These checks do not establish a universal law or isomorphism.

The 100-point observation run measured 18.61 seconds for replay and 19.42
seconds for bundle creation. No comparable exact before timing was captured,
so there is no measured speed multiplier.

## Verification records

The previous report and logs remain available in
`machine-repairs-2026-10-29.md`. Failing-before cases are retained in
`defined-composition-before.log`, `graph-edge-dependencies-before.log` and
`defined-discovery-before.log`.

The continuation runner is `validation/run_machine_continuation_checks.cmd`.
The separate live input test is also reproducible through
`validation/run_live_naming_gate_checks.cmd`.

Fifteen focused suites passed with exit code 0: graph mapping, surgery,
graph integration, existing defined operations, operation catalogue, tensor
axes, single-operation finite templates, named-law certification, live proof
and restoration, dependent-edge insertion, operation composition,
multiple-operation finite structures, custom-operation discovery, witness
replay, and the blocking live name prompt. The first thirteen ran together;
witness replay and live input ran separately. The runner now contains all
fifteen for reproduction.

An additional broad batch-miner regression was stopped before completion
after the focused checks had passed. It has no pass result and is excluded
from the fifteen-suite count. Its partial output remains in
`continuation-discovery_miner_regressions-2026-10-30.log`.

The named-input transcripts are `live-naming-gate-suggest-2026-10-30.log` and
`live-naming-gate-playground-eof-2026-10-30.log`. The continuation runner writes
one dated log per suite. The witness regression includes the full-catalogue
100-point reproduction and adversarial witness membership cases.

`core.py` remains unchanged, with SHA-256
`8F06854B7C4828A1C94005A7036AFD60450FC5522E1E7D3BAD549AD6A1B1FDE1`.

## Boundaries

The input gate is a synchronous text boundary. This does not introduce a
background worker or live code reload. Composite operations still expand
into the admitted Nat primitive grammar. Mixed structure checks remain
finite and require explicit bindings. Arbitrary node payload cloning and
cyclic inserted-edge construction remain unsupported. Candidate generation
uses the existing supplied grammar; no harder-theorem benchmark was run.
