# Track F -- FLT programme tooling and audit

Ledger entries for this track. Newest last. See protocol/README.md for the
rules governing entries, and research_protocol.md for cross-track discipline.

## Decided: the grading script may consume `ImportedBecause`

Ruled yes. Counting human-supplied information is provenance accounting, not
explanation generation, and `ImportedBecause` is exactly what that term
encodes. The grading script reads it to attribute each piece of information
in a closed proof to the teach that introduced it.

The boundary this does not cross: the script reads provenance terms and
counts them. It does not read rendered sentences, and it does not call the
explanation renderer. If grading ever needs prose, that is a defect in the
provenance terms, not a reason to widen the script.

## Standing limit: fresh context is not a blind agent

Every engineer on this project has read the human reference decomposition.
The operator who runs the blind session must therefore be a different agent
with fresh context, no reference graph, no curriculum answers, and no other
track's logs.

That fix removes conversational contamination: the reference graph, the
layered list, the role table. It does not remove training contamination. A
fresh-context agent of the same model family still carries knowledge of this
theorem and its standard proof route in weights, and no context hygiene
reaches that.

So the claim this programme can support is bounded, and the bound is recorded
here so nobody upgrades it later. What a clean transcript demonstrates is
that the apparatus characterizes its own gaps, that each teach was justified
by a concrete residual, and that each unlock was measured. It is a
development demonstration, not blind discovery. The genuinely blind test is a
second theorem withheld from every agent in the loop, and this programme is
not that test.

## Sealed exam ordering, to be checked mechanically

A seal nobody verifies is decoration. The commit that seals the held-out set
must predate the first curriculum session commit in history, and the grading
script verifies that ordering rather than trusting it. A seal committed after
curriculum work began is void, and the exam it governs is inadmissible.
