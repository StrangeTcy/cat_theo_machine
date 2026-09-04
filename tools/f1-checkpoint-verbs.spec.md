# F1 checkpoint verbs (docs-only)

No code on this base. Lands on a `research.py`-bearing cut together
with D12, because both touch the audit surface.

## verb surface

```text
save checkpoint <name>
load checkpoint <name>
```

`<name>` is an operator token. The store key is not the name.

## content-addressed id

The bytes of the checkpoint body hash to a content-id. The name is a
label for that id. Two saves of equal body share an id. A load by
name resolves the label, then the id. A load of a missing name is
inadmissible and prints the miss; it does not invent an empty graph.

## audit header (closes D12 by construction)

After `research mode on`, after `load checkpoint`, after `load theorem
packs`, `audit knowledge` prints every loaded class that is present,
and prints `none` for every class that is absent:

```text
audit knowledge (research runtime):
  theorem packs: loaded | not loaded
  library rules: <n> (LIBRARY_THEOREM) | 0
  DOMAIN_AXIOM: <n>
  HUMAN_SUPPLIED_TRUSTED_THEOREM: <n>
  HUMAN_SUPPLIED_TRUSTED_THEOREM_WITHOUT_UNLOCK_EVIDENCE: <n>
  SEARCH_DERIVED: <n>
  loaded checkpoint: <name> content-id <id> | none
  taught rules: <n>
  intervention episodes: <n>
  learned policies: none | present
```

A first audit with no loaded-class list is D12. The verb surface is
not accepted until this header is the first audit of every session.

## inadmissible cases

```text
save checkpoint                 (no name)
load checkpoint                 (no name)
load checkpoint <name>          when no save binds that name
save checkpoint <name>          while research mode is off
load checkpoint <name>          while research mode is off
load checkpoint <name>          of a body whose content-id does not
                                match the stored id (tamper)
```

Each prints a refusal and changes no graph.

## not this cut

Implementation waits on SHARED re-cut carrying `research.py`. This
file is the contract. D12 routes with it.
