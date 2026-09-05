# TWO-PIPELINE — REQUIRED, NEVER SUPPLIED

> **This file contains no pipeline description. It exists to stop an agent
> from proceeding on the assumption that it does.**

Status as of 2026-09-05: the operator referenced this document as
`protocol/TWO-PIPELINE.md` with the note `(d3de45a)`. Two findings:

1. No file of this name exists in the working tree, and no file of this name
   has ever existed in any commit in this clone.
2. `d3de45a` is not a valid object in this repository. `git cat-file -t
   d3de45a` fails.

So the citation could not be resolved and the content could not be recovered.

## What the name implies, and what INT will not assume

Every engineer text opens with "Read `protocol/CHARTER-v1.md` §0 and §3,
`protocol/CHARTER-v2.md`, `protocol/TWO-PIPELINE.md`". The name implies the
repository runs two pipelines and that agents must know which one their work
lives in — most plausibly a split between the machine's own reduction path and
a host-side or second-substrate path, or between the instrument pipeline and
the measurement pipeline.

**INT will not guess which.** Getting the pipeline split wrong misroutes every
track's artifacts and every tag.

## Standing instruction to any agent reading this

```text
STOP. You were told to read protocol/TWO-PIPELINE.md. It was never written
and the commit cited for it (d3de45a) is not an object in this repository.

Report `blocked on operator: TWO-PIPELINE.md not supplied; d3de45a
unresolvable`, and stop before starting work items.
```

## What INT needs

Either the text of `TWO-PIPELINE.md`, or the correct commit hash if it lives
in a clone this one has not fetched. With the hash, INT can restore it from
history; without either, INT cannot reconstruct it — the packets quote nothing
from it.

## Provenance

```text
created by:  INT, 2026-09-05, as a gating placeholder
reason:      required reading for every wave-1 agent; absent and unrecoverable
not:         a pipeline description. It states no rules.
```
