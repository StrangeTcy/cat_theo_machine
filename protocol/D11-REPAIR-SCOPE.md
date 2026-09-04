# D11 repair scope — option 2, with the mechanism corrected

Status: **written, not started.** Nothing in `packs.py`, `main.py`, or any
pack has been changed for this repair. The two files under `protocol/d11-spike/`
are fixtures for the acceptance run and are deliberately outside `packs/`, so
nothing loads them.

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

## 8. Open question for the operator

The scope above is one loader change with a narrow blast radius. The question
worth ruling on before it starts: when the shipped 167 are eventually ported,
does the mapping live in each pack's header, or in one loader-level table
mapping the label namespace to the surface vocabulary? Per-pack headers keep
packs self-describing and keep the blast radius at zero for unported packs; one
loader table ports everything at once and is a single point of truth, but it
makes every shipped rule reachable in the same commit that lands it — which
risks mixing capability with content after all. The scope as written assumes
**per-pack headers**; say the word if the loader table is preferred.
