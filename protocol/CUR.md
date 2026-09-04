# CUR — content-ledger notes

A note ledger for content review follow-ups. Per `protocol/README.md`, an entry with no artifact is
a **note**, not a ledger entry, and is marked as such. `CUR` is not a track (the tracks are
E/F/G/I/S); this file holds content-review notes that the reviewer asked to record.

---

## Note (2026-09-04) — §0 banned-word violation in the E7 doc line

```
source of prohibition: standing charter as supplied to the session;
in-tree status: referenced by protocol/DISTRIBUTION.md but not present verbatim;
violated token: "honest";
locus: prior E7 classification prose / superseded commit message;
repair: removed from current artifact; violation recorded; history not rewritten.
```

Details:

- The superseded `CUR-ENGEL-E7` note (commit subject `38d4e58`, and the narration that produced it)
  used the token **"honest"** applied to a machine classification ("honest negative"). The standing
  charter (the §0 list referenced by `protocol/DISTRIBUTION.md:9`) prohibits human-normative /
  anthropomorphic words for machine outputs; a machine classification is a measured verdict, not an
  "honest" one.
- **In-tree status of the §0 list:** the prohibition is referenced by `protocol/DISTRIBUTION.md` but
  is **not present verbatim** in the current tree. This note therefore records the prohibition as the
  standing charter supplied to the session, not as a list found verbatim in the working tree.
- The commit history is not rewritten, so `38d4e58` stands as-is; this note records the violation and
  does not claim to restore the superseded commit's wording.
- Do not repeat the token in successors. The current artifact (`CUR-ENGEL-E7.md`),
  `CUR-ENGEL-E3.md`, `CUR-ENGEL-E4.md`, and this note avoid it.

Remote tip recorded before work: `b7e6c90f739509271585c780684663c5c54f4eff`.
