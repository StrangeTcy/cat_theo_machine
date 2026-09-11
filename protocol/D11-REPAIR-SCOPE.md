# D11 repair scope — option 2, with the mechanism corrected

Status: **capability (commit 1) implemented and gated; content port (commit 2)
NOT started.** `packs.py` now supports the per-pack `surface:` header. No
shipped `packs/*.yaml` was touched, and the shipped 167 compile to a
byte-identical fingerprint. The fixtures under `protocol/d11-spike/` are
deliberately outside `packs/`, so nothing loads them.

Branch from `experiment-5-frozen-r1` (`ef571b6`). Baseline for this work is
`feb457e`; the ruling transcript is `logs/defect-1-ruling-diagnostic.log` and
the spike transcript is `logs/d11-spike.log`.

---

## 1. The mechanism is not what the ruling said

The ruling (D11, filed `feb457e`) attributed the zero to pack rules carrying
`replacement` instead of `conclusion`:

> All 167 compile at `packs.py:287-300` as `Rule(pattern, replacement)` (82) or
> `MultiRule(premises, replacement)` (85). No pack rule carries a conclusion.
> Backward search unifies a goal against rule conclusions, so a rewrite rule
> offers nothing to unify against.

**That is wrong in its mechanism and right in its conclusion.** The loader
compiles `premises -> replacement` into the same `MultiRule(premises, X)` that
a *taught* law compiles into — the shape that produced `partial matches 1` in
the ruling's A/B. There is no shape gap to close, and no third compile target
to add: `packs.py:287-300` already produces the matchable form.

The spike proves it. One rule, `(divides k p), (divides k q) => (divides k
(plus p q))`, loaded as a pack with nothing taught:

```text
spike-char   heads {char: divides}    goal (divides k (plus p q))  -> partial matches 1
spike-label  heads {sym: DividesLabel} goal (divides k (plus p q)) -> partial matches 0
ablation     spike-char loaded        goal (cornersum t whole)     -> partial matches 0
```

Same rule, same loader, same search, same goal. Only the head vocabulary
differs. The boundary is **atom kind, not rule shape**:

- A session goal is parsed by `_research_parse` (`main.py:4336`) into
  `_RESEARCH_SYMBOLS.atom(name)` → an `M.Char` atom.
- A pack term is compiled by `_compile_term` (`packs.py:130`) from
  `{sym: DividesLabel}` → `self.namespace[name]` → a `ConstructorLabel` atom
  (`labels.py:1170`).
- Unification treats a `Char` and a `Label` as different constants, always.

`M.Char` interning is *not* the barrier and must not be blamed for it:
`M.Char("divides") is M.Char("divides")` is `False`, and the char-form spike
matched across two different string tables anyway — Char atoms compare by
content. It is the kind, not the table.

So all 167 shipped rules contribute zero candidates **because their heads are
Labels and the goal's heads are Chars**, not because they are rewrites.

## 2. What this does to the option choice

The operator chose option 2 for its blast radius: keep the change in the pack
loader and format, leave search/matcher/planner semantics untouched, and reuse
the matching path the A/B already proved works. **That reasoning survives
intact** — it was reasoned from the mechanism I reported, and the mechanism was
wrong, but the constraint it selected (loader and format only) is the right one
and the spike confirms the path works.

What changes is the *shape of the change*. Option 2 as scoped was "the loader
grows a third compile target for conclusion-shaped entries." The capability
being added is instead **a vocabulary mapping**: let a pack declare the surface
name its symbols answer to, and compile `sym:` heads through it.

This is a revision to what was approved, so it is flagged rather than adopted
silently. It is narrower than what was approved, not wider: it touches one
branch of `_compile_term` and pack-header parsing, and it adds no rule shape.

Options 1 and 3 stay **not-built-deliberate** for the reason given: option 1
changes what every session attempts for every goal, and option 3 is a special
case of it. They are held, not rejected — the spike says nothing about whether
a normalization gap sits behind the vocabulary gap. If one does, it is a new
defect with its own number, **not** an expansion of D11.

## 3. The change

Additive, in `packs.py` and the pack header only:

1. A pack may declare `surface:` — a map from its `sym` names to the session's
   surface names (e.g. `DividesLabel: divides`).
2. `_compile_term`'s `sym` branch resolves a declared surface name to the
   session's `Char` atom instead of the `Label` atom.
3. Undeclared symbols compile exactly as they do today.

**Opt-in per pack, and that is load-bearing.** A default-on mapping would
recompile the shipped 167 under different heads and change their behavior,
which fails acceptance item 4 below. The shipped packs declare nothing, compile
byte-identically, and stay as they are until someone ports them.

## 4. The boundary: capability and content are separate deliverables

Written into the scope as the operator required:

- **In this repair:** the loader capability, proven by a minimal test pack in a
  non-FLT domain. Nothing else.
- **Not in this repair:** re-authoring the 167, adding domain rules, or
  touching FLT content. Porting library content is operator/curation work,
  routed per track, after the capability lands. A commit that repairs the
  instrument and also rewrites domain packs mixes the two and fails review.

## 5. Acceptance evidence

The operator's five items, with what the spike already discharges:

```text
1. minimal test pack, non-FLT domain .......... DONE as a fixture
      protocol/d11-spike/d11-spike-char.pack.yaml (one rule, divides/plus)
2. cold start, packs loaded, partial matches >= 1 through the
   pack-loaded rule, provenance LIBRARY_THEOREM ...... ALREADY MEASURED
      spike: "library rules 1; provenance LIBRARY_THEOREM"
             "FAILED. cost=2; rules with a genuine partial match: 1"
      after the fix the same evidence must come from a pack that declares
      surface: and uses {sym:} heads — that is the case the fix adds
3. ablate the entry, partial matches returns to 0 .... ALREADY MEASURED
      spike-char loaded, non-matching goal -> 0
      and spike-label (no surface declaration) -> 0
4. the 82 Rule / 85 MultiRule entries compile unchanged .... TO MEASURE
      opt-in mapping, so the shipped packs take no new path; verify by
      loading all packs and diffing rule counts and the pin set
5. pins 305/218/0 hold; semantic classification; re-cut, then blank
   controls rerun by every operator before any measurement counts  TO MEASURE
```

Item 2 carries the one real requirement: **the passing case must be the
mapping, not the char shorthand.** The spike's char form already works today,
so a fix that only re-expresses entries in char form would be content work
wearing a capability's clothes. The acceptance run uses a pack with `{sym:}`
heads plus a `surface:` declaration — the spelling that does not work today and
must work after.

## 6. Effect on F

Unchanged from the ruling and now better grounded. F is blocked on D11, and
blank controls run on a pre-D11 instrument certify silence, not coverage. After
the fix lands and the re-cut's blank controls pass, the decoy/FLT pair becomes
runnable again — the instrument will have changed, which is the one condition
the pair's closure named. Decoy first, fresh processes, same protocol. Whether
the walls then differ is the first real F measurement this project will have
taken.

## 7. Retroactive items the operator marked

```text
ZeroPartialMatchAmbiguity  -> RESOLVED, subsumed by D11
  "no rule could match vs. criterion too coarse": no rule could match, and
  the reason is now known — Label heads never unify with Char goal heads.
  The criterion was never tested.

F-OP-BLIND-FLT-RETRY null  -> EXPLAINED, verdict unchanged
  334/334 identical residuals were not a property of the goal pair. They are
  what a backward-blind instrument returns for every goal. Reading stays
  withdrawn; the pair stays closed; the moral survives verbatim.

pre-flight item 2          -> BLOCKED ON D11, not merely open
  A nosolutions entry cannot pass "candidate partial match on the toy goal"
  until the vocabulary boundary is crossed, whatever its shape. No one should
  attempt item 2 until this fix lands.

library-only-control       -> name kept, meaning annotated
  On a pre-D11 tag the checkpoint is behaviorally indistinguishable from an
  empty library for backward search. Its three citations in
  protocol/DISTRIBUTION.md (lines 47, 330, 838) are annotated, not voided —
  they were true statements about a blind instrument.
```

## 8. §8 ruling (operator) — per-pack headers

```text
D11 surface mapping location:
  chosen: per-pack header
  rejected: one loader-level global table

reason:
  per-pack headers keep each pack self-describing, reviewable, and ablatable.
  unported packs compile exactly as before.
  porting becomes a visible content decision per pack, not a hidden global
  loader behavior.
```

A loader-level table would silently re-key every shipped rule that names a
mapped label. That mixes a loader capability with a library-content port in one
action. For D11, that is too broad.

The mapping is **opt-in**, **pack-local**, and **constructor-head scoped**:

```text
Within this pack only:
  a declared pack symbol used as a constructor head may compile to the named
  research-surface atom for matching against research-mode parsed goals.

Without this header:
  {sym: DividesLabel} keeps compiling exactly as it does now.
```

A label used as data is never rewritten. The mapping applies only where the
compiler has a position-specific reason to treat the symbol as a constructor
head — the `head` position of a `call`, and nowhere else.

## 9. The two-commit split

**Commit 1 — D11-MAP capability** (this one). Loader support only:

```text
allowed:   packs.py support for the per-pack surface header
           protocol/d11-spike fixture exercising the new header
           a gate proving unported packs compile unchanged
           transcripts proving the A/B/A still discriminates
not allowed: shipped packs/*.yaml port; global table; parser change;
           search change; char-form shortcut as the passing case
```

Classification: **semantic-capable, with default-live behavior unchanged.**
Nothing changes for any pack that declares no header, which today is all of
them. The semantic cut is commit 2, not this one.

**Commit 2 — first shipped pack port.** Not started. Adds a `surface:` header
to one reviewed pack or reviewed subset, records the exact labels mapped and
the before/after reachability. That commit is **semantic, requires a re-cut,
and requires blank controls before any F measurement counts.** No bulk port of
the 167 without an explicit authorization and a full re-baseline plan.

## 10. Audit terms

```text
PackSurfaceMapping(pack_id, label_atom, surface_atom)
LibraryRuleMatchedViaSurfaceMapping(rule_id, pack_id, label_atom, surface_atom)
```

Both are emitted by the loader as audit lines and carried on the `LoadedPack`
(`surface_mapping_audit`, `surface_mapped_rules`) for programmatic readers. The
atoms are held in the tuple; the printed form names the label and the surface
because a `ConstructorLabel` has no host text to print.

`LibraryRuleMatchedViaSurfaceMapping` is emitted **at compile time**, when the
rule's head is compiled through the mapping — not at match time. A rule reached
this way is reachable from research goals *only* through the mapping, so the
attribution is complete at compile time and no match-time hook is needed. That
is a deliberate consequence of "no search change" in commit 1; if the operator
wants the line emitted per match instead, that is a search hook and belongs in
a later commit.

## 11. What commit 1 produced

```text
packs.py          per-pack surface: header; constructor-head-scoped mapping
                  via _compile_term(..., as_head=True); eager validation
tools/d11_gate.py the gate, rerunnable from a fresh clone
protocol/d11-spike/d11-spike-mapped.pack.yaml   the header fixture
protocol/d11-spike/shipped-167-rules.sha256     pre-change fingerprint
logs/d11-map-capability.log                     the transcript
```

Gate result, on a fresh venv after reset #8:

```text
1. shipped 167, no headers     167 rules, sha256 786cff5c... == pre-change
                               probe -> partial matches 0        PASS
2. {sym:} heads, no header     probe -> partial matches 0        PASS
3. {sym:} heads + surface:     probe -> partial matches 1        PASS
                               provenance: pack rule, not taught
                               audit names the pack-local mapping
4. unrelated goal              probe -> partial matches 0        PASS
5. char-form fixture           diagnostic only, not a gate
```

The digest is `sha256` over, per rule, a **kind walk** (the class name of every
atom, preserving pair shape) joined to the rendered content. The kind walk
exists because `PrettyTerm` cannot render a `ConstructorLabel` — it prints `?`
— so a content-only digest could not see a `Label` silently re-keyed to a
`Char`. A rule is a host `Edge`, so the walk runs on `EdgeInputs`; rendering the
rule directly yields its `repr` with a memory address, which made an earlier
version of this digest unstable across boots.

**One deviation from the operator's gate text, flagged rather than faked.** The
gate as specified asks condition 3 to show `provenance LIBRARY_THEOREM`. That
string is the REPL's announcement for `load theorem packs` (`main.py:3479`),
not a per-rule tag: a rule's origin is `origin_tag_for_text(pack origin)`,
which is `primitive` for a pack that declares none — as the fixture does, and
as nine of the thirteen shipped packs do. Asserting the literal string would
have meant either lying or changing provenance mapping, which is out of scope
for a capability commit. The gate instead asserts the discriminating fact: the
match is a pack rule reached through the mapping, attributable by rule id in
the audit, and not a taught law (`HUMAN_SUPPLIED_TRUSTED_THEOREM`). The tag it
carries is printed verbatim in the transcript.
