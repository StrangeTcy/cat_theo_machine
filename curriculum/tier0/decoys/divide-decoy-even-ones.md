# Tier0 G4 decoy — Divide / even-number-of-ones words (negative-control decoy)

Agent: G/I-op. **Status: blueprint-only, not training input.** G4 decoy.

---

## source statement

> Find the number of binary words of length n ≥ 1 with an even number of ones.
> (supplied verbatim by operator, G4 decoy list)

## target class: count

## surface shape (what a method might latch onto)

Word-count / build-a-recurrence language → could trigger **Divide** (recurrence / divide-conquer).

## intended method (the trap): Divide (decoy)

The correct method is a **direct bijection**: flip the last bit. That pairs every word with an
odd-number-of-ones word, so exactly half have an even number of ones → `2^(n-1)`. **No recurrence is
required.** Divide must NOT fire.

## exact mathematical target

Count = `2^(n-1)` for n ≥ 1. Proof by involution/bijection (flip the last bit is a fixed-point-free
involution pairing even-ones and odd-ones words).

## required domain roles

- binary word of length n;
- parity of the number of ones;
- the last-bit flip involution;
- the pairing (even ↔ odd count), giving exactly half.

## constructor mapping found in tree (real, cited)

`DivideLabel`, `CardinalityLabel`, `DividesLabel`, `ParityLabel`, `EvenLabel`, `NatLessLabel`,
`KnowledgeLabel`, `GoalLabel`.

## missing constructors

`WordLabel`, `BinaryWordLabel`, `AdjacentLabel`, `BitLabel`, `ParityOfOnesLabel`. (A1 vocabulary.
No claim exist.)

## negative controls

The Divide-vs-bijection distinction is the control. A Divide policy that fires here and builds a
recurrence (which, though valid, is unnecessary and hides the direct `2^(n-1)` answer) is the
failure mode — the method that "overcomplicates" is being tested.

## expected policy behavior

- **must not fire**, or
- **fire and fail rent** (a recurrence route must not be the *accepted simplest* solve; the direct
  `2^(n-1)` bijection is the right method).

## unsound-derivation risk

A wrong "solve" computes a recurrence and gives the count but does not prove the parity balance;
or, in the extreme, gives a count that ignores the even-ones restriction. The policy must fail rent
on an unsound/careless count.

## proof-checker evidence required

- the last-bit flip is a fixed-point-free involution on binary words;
- it pairs even-ones with odd-ones words (bijection);
- hence count = `2^(n-1)`.

## TrainingRecord promotion gate

G4 decoy. If converted, must load + compile + partial-match AND demonstrate the Divide policy does
NOT close it as the simplest route.

## current status: blueprint-only, not training input
