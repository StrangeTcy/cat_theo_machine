# Researcher-v0 G6 discovery graph summary

Status: inert graph built; no activation, admission, or live write.

## Counts

```text
nodes                 172
edges                 173
Task                  42
Attempt               34
Transition            5
Outcome               34
CandidateInvariant    8
BrokenOn              5
Certificate           32
PruneEvent            8
ScopeMismatch         4
```

## Required edge kinds

```text
generated_from        35
attempted             34
produced              68
broke                 5
proposed_from         8
proved_by             3
used_by               16
invalidated_by        4
```

## Coverage

The graph links all 42 delivered tasks, 34 G4 MINING attempts and outcomes, 21 path certificates, eight invariant proposals, five retained BrokenOn transitions, three proved invariant certificates, eight G5 prune events, eight endpoint certificates, and four scope-change invalidations.

Every edge contains source artifact path and record id references. The graph is JSON reporting data only and is not imported by any live path.
