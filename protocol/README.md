# Track protocol files

`research_protocol.md` is the index and holds cross-track discipline: session
rules, request regimes, rent and ablation semantics, checkpoint discipline,
and the shared ledger entries that predate the track split.

Each track writes its own ledgers here. Operators write measurement ledgers;
engineers write design decisions and stop conditions. One file per track
means two agents never edit the same ledger, so merges stay mechanical.

    protocol/S.md   self-improvement: contracted relation schemas
    protocol/E.md   explanation substrate
    protocol/F.md   FLT programme tooling and audit
    protocol/G.md   Engel strategies as planner methods
    protocol/I.md   IMO problems as the held-out exam

Rules that apply to every file here:

- An entry states what was predicted, what was run, and what came back. An
  entry with no artifact is a note, not a ledger entry, and is marked as one.
- A refuted hypothesis stays in the file. Deleting a wrong turn destroys the
  record of why the current answer is believed.
- Cross-track claims go in the index, not here. A claim that S paid rent on
  an I problem belongs in both tracks by reference, written once.
