# CUR — content-ledger notes

A note ledger for content review follow-ups. Per `protocol/README.md`, an entry with no artifact is
a **note**, not a ledger entry, and is marked as such. `CUR` is not a track (the tracks are
E/F/G/I/S); this file holds content-review notes that the reviewer asked to record.

---

## Note (2026-09-04) — §0 banned-phrase violation in the E7 doc line

```
source: session-supplied charter §0;
in-tree status: referenced by protocol/DISTRIBUTION.md, not present verbatim;
violated entry: §0 banned-phrase item 5;
exact UTF-8 bytes: 68 6f 6e 65 73 74;
locus: superseded commit 38d4e58 subject and prior E7 classification prose;
repair: removed from the current E7 artifact; prior history retained.
```

Details:

- The superseded `CUR-ENGEL-E7` note (commit subject `38d4e58`, and the narration that produced it)
  used the §0 banned phrase item 5 (`0x686f6e657374`) applied to a machine classification. The
  standing charter (the §0 list referenced by `protocol/DISTRIBUTION.md:9`) bans **six exact
  phrases**, not every human-normative adjective; this note refers to the phrase by its item
  number and byte encoding above, and does not restate it verbatim.
- **In-tree status of the §0 list:** the prohibition is referenced by `protocol/DISTRIBUTION.md`
  but is **not present verbatim** in the current tree. This note records the prohibition as the
  standing charter supplied to the session, not as a list found verbatim in the working tree.
- The commit history is not rewritten, so `38d4e58` and `bb9681a` stand as-is. The `bb9681a` commit
  message and the preceding ledger entry carried the phrase verbatim; this successor entry replaces
  the ledger text with the nonliteral encoding above and does not claim prior history was edited.
- **This note itself does not assert that the E3/E4/E7 files avoid the phrase.** The E7 artifact was
  amended to remove it; the E3/E4 artifacts never contained it. This ledger note uses the nonliteral
  encoding so it does not restate the phrase.

Remote tip recorded before work: `d76f7814a5a886d26248b52b95a3dfa1699fd491`.
