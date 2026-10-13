# F1 implementation checklist

Docs-only. No code on this base. Run against a SHARED cut that
carries `research.py`.

## files expected to change

```text
research.py     verb handlers, audit header, checkpoint store
```

`core.py` is not in this list. Packs and the parser are not in this
list.

## audit-header fields (exact)

After `research mode on`, after `load checkpoint`, after `load theorem
packs`, the first `audit knowledge` prints:

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

A first audit without this list is D12. The verbs are not accepted
until this header is the first audit of every session.

## checkpoint id

```text
content-id = hash of the checkpoint body bytes
name       = operator label, not the store key
equal body => equal content-id
load by name resolves label, then content-id
missing name prints the miss; does not invent an empty graph
tamper (body hash != stored id) is a refusal; graph unchanged
```

## inadmissible verbs

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

## inadmissible sessions

```text
first audit omits the loaded-class list          D12; not a measurement
load checkpoint of another session's body
  without printing content-id                    provenance break
research mode off during save or load            verbs do not run
```
