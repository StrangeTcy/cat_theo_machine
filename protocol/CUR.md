# CUR — content-ledger notes

A note ledger for content review follow-ups. Per `protocol/README.md`, an entry with no artifact is
a **note**, not a ledger entry, and is marked as such. `CUR` is not a track (the tracks are
E/F/G/I/S); this file holds content-review notes that the reviewer asked to record.

---

## Note (2026-09-04) — §0 banned-word violation in the E7 doc line

The superseded `CUR-ENGEL-E7` "honest negative" note (commit subject `38d4e58`, and the narration
that produced it) used a **banned word from §0 of the v1 charter**: the word **"honest"** applied to
a machine classification ("honest negative"). §0 prohibits human-normative / anthropomorphic words
for machine outputs; a machine classification is a measured verdict, not an "honest" one. The commit
history is not rewritten, so `38d4e58` stands as-is; this note records the violation.

Do not repeat it in successors of `3e7237e` (the corrected E7 inventory). The corrected doc
(`CUR-ENGEL-E7.md`), `CUR-ENGEL-E3.md`, `CUR-ENGEL-E4.md`, and this note avoid the banned word.

Remote tip recorded before work: `b7e6c90f739509271585c780684663c5c54f4eff`.
