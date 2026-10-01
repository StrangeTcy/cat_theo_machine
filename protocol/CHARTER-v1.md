# CHARTER v1

## §0 Constraints (bind every agent)

- No `core.py` edits.
- No `isinstance`, `hasattr`, `type`, `__class__`, `__new__`, `getattr`, `callable` as machine-type tests.
- No Python lists, dicts, or booleans as machine values.
- No helper functions, module globals, monkeypatching, dataclass, typing checks, `.results[0]`, `is_var` fields, named Var fields, as substitutes for machine terms.
- No LLM, embeddings, statistical parsing, or host string templates for machine utterances.
- Every failure is a machine term. Every claim of “passed” cites a dated artifact.
- Record remote tip before work. Never force-push. Published branches are append-only.
- Do not run Python in conda without asking.
- Do not run Experiment 4.
- Do not explain FLT.
- Agents do not run A1–A3.
- Banned in prose and commits: “If you want”, “matters”, “but wait”, “actually”, “honest”, “Let me”.
- D11 remains head-vocabulary alignment only. Second pack stays paused.

INT owns: preflight gate, merge queue, suite admission, immutable tags, `protocol/research_protocol.md` as index. INT does not build track features. INT does not run measurement sessions.

Textual merge conflicts stay with INT. Semantic conflicts return to owners as a coordinated change.

## §1 Preflight (INT first job)

1. In `LearnedMemoryCheckpointTest`, replace `except Exception: self.result = M.false_value` with a re-raise. Rerun the exact 109-predecessor `_register_test` repro. Save the full traceback to `protocol/preflight/exception-traceback.txt`. Revert the swap. Name the mechanism in `protocol/preflight/ledger.md`. If it is a defect, fix it in a separate commit after `preflight`, with its own tag.
2. Construct the `nosolutions` producer rule and one consumer rule. Show both compile to `MultiRule`. Show at least one is a candidate partial match on `x + 1 = x`. Paste the selection output into the ledger. Parsing alone is not evidence.
3. Print the parsed FLT goal term and the decoy goal term side by side into `protocol/preflight/decoy-shape.txt`. Confirm same predicate arity, same case-split shape, same exponent position. If they differ, write `DECOY REDESIGN REQUIRED` and stop; do not redesign it.
4. Run the full two-shard suite. Record the exact failure set in the ledger.
5. Commit `preflight`. Cut tag `preflight-<shortsha>`. Push. Never force-push.

Do not begin S, E, G, F tooling, or measurement sessions until this gate reports complete.

## §3 S (near-transfer contracts)

S is contracted near-transfer only. No free predicate heads. No far transfer. S owns learned-policy induction through existing intervention machinery. First phase after preflight: S1 contracts.

## §4 E (explanation)

E owns explanation substrate and held-out transfer. E1 stop condition: if held-out fails, the idea library is a summary generator; stop. No FLT-shaped goals.

## §5 F (instruments)

F-tools builds checkpoint, grading, and negative-control tooling. The blind F operator never builds those tools. Agents do not run A1–A3 or Experiment 4. F blinding is defined by an information allowlist, not “fresh context.”
