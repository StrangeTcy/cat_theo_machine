# Audit: carrier-complete hypergraph isomorphism (`2d612b2`)

Run date: 2026-11-02 (Europe/Moscow)
Branch: `arena/e32bd1c7-cat-theo-machine`
Audited commit: `2d612b24fc96a113ed3d67b9e30c7cfbd9184207` — *make hypergraph isomorphism total on the node carrier*
Parent: `b3be7e7d3d46b3ed4f713981a32311aa9140edbb`
Interpreter: `/usr/bin/python` (Python 3.11.2), no conda
Pass type: read-only audit. No source file was modified to reach any verdict below.

Remote tips recorded before the pass (`git ls-remote origin`):

```
2d612b24fc96a113ed3d67b9e30c7cfbd9184207  refs/heads/arena/e32bd1c7-cat-theo-machine
b3be7e7d3d46b3ed4f713981a32311aa9140edbb  refs/heads/arena/f42b3f12-cat-theo-machine
```

## What was audited

`matching.py`: `_carrier`, `_store_values`, `_chain_contains`, `_chains_same_length`,
`_unmapped`, `_complete_mapping`, `_lookup_forward`, `_lookup_reverse`,
`_search_candidate_e2`, `_match_hypergraphs`. Supporting reads: `graph.py:381-400`
(`GraphVersionNodes` / `GraphVersionEdges`) and `graph.py:588-609`
(`GraphPatriciaValues`, `GraphStoreValues`); `search/patricia.py`
(`SearchPatriciaLeaf/Branch/Choice/Entries/IsTree`); `persistence.py:1414`
(node root restored verbatim).

## Regression status on the audited commit

| Suite | Exit | Note |
| --- | --- | --- |
| `validation/test17_hypergraph_matching.py` | 0 | all carrier cases pass |
| `validation/graph_mapping_regressions.py` | 0 | |
| `validation/graph_edge_dependencies_regressions.py` | 0 | |
| `validation/graph_surgery_regressions.py` | 0 | |

The three graph suites import the historical package name `hyge`, which the repository
root shadows with `hyge.py`. They were run from `/home/user` with an import-path alias on
`PYTHONPATH` (`PYTHONPATH=<alias-dir>:/home/user`), no repository edit:

```
cd /home/user
PYTHONPATH=<alias-dir>:/home/user python -u cat_theo_machine/validation/graph_mapping_regressions.py
```

Commands for the probes:

```
python -u probes/carrier_isomorphism_audit_probe.py
python -u probes/carrier_isomorphism_counterexample_probe.py
```

The counterexample probe pins the observed `2d612b2` behaviour in assertions, so a
green run means the defect is present. `BijectionSearch` in that probe is an exhaustive
Machine-native search over carrier-to-carrier bijections with an edge-preservation test at
each leaf.

## Probe sections and observed verdicts

| Section | Fixture | Verdict | Carriers | Map |
| --- | --- | --- | --- | --- |
| 1 | store `[a,b,c]` against `[r,q,p]`, one edge | iso | 3 / 3 | 3 |
| 2 | legacy edge-only fixture, no declared store | iso | 2 / 2 | 2 |
| 3 | edge-free 0/0, 0/1, 1/1, 2/2, 3/3 | iso, not-iso, iso, iso, iso | equal except 0/1 | 0, 0, 1, 2, 3 |
| 4 | two edges plus two isolated, interleaved stores | iso | 6 / 6 | 6 |
| 5 | duplicate store entries `[a,b,b,c]` vs `[p,q,r]`; `[a,a]` vs `[p]` | iso, iso | 3 / 3, 1 / 1 | 3, 1 |
| 6 | Patricia store of 2 against bare chain of 2 | **not-iso** | 3 / 2 | 0 |
| 7 | `R(a,[])` against `R(p,q)` | **not-iso** | 2 / 2 | 0 |
| 8 | one graph, store reordered three ways | iso, iso, iso | 3 / 3 | 3 each |
| extra | nullary edge `Pair(R, [])`, 1v1 and 1v2 | iso, not-iso | 1 / 1, 1 / 2 | 1, 0 |

Duplicate store entries collapse under the same `Compare` equality used for entities, so a
carrier is a set of distinct vertices. That is consistent with the stated design.

## Claim-by-claim

1. **Every edge entity is in the carrier.** Holds for `Pair`-shaped edges, which are this
   codebase's edge form: `IsEdge` accepts any `Pair`, and `testsuite.py:865` builds edges as
   `Pair(Char("p"), Pair(x, Pair(y, EmptyList)))`. One over-inclusion rather than an
   omission: an argument equal to `EmptyList` is added as a vertex (finding A).
2. **Every declared node is in the carrier, even with no incident edge.** Holds for bare
   chain stores in either order, with duplicates and with isolated vertices interleaved.
   Fails for a Patricia-backed store (finding B).
3. **The edge phase maps every edge-involved vertex.** Holds on every ordinary fixture
   (unmapped edge entities 0 on both sides). Fails under finding A.
4. **Every vertex unmatched at completion is isolated.** Holds on ordinary fixtures. Fails
   under finding A, where a vertex can be bound twice and still be reported free.
5. **Any bijection among the remaining isolated vertices preserves structure.** Holds
   whenever claim 4 holds: an unmatched vertex is mentioned by no edge, so its image is
   unconstrained by any edge. No counterexample was found with distinct non-`EmptyList`
   entities.
6. **Store iteration order and representation cannot affect the verdict.** Fails twice:
   edge order flips the verdict (finding A, A3), and store representation flips the
   verdict (finding B).

## Finding A — `EmptyList` sentinel collision

`_lookup_forward`, `_lookup_reverse` and `_unmapped` use `EmptyList` to mean "absent", but
`EmptyList` is an admissible carrier entity: `IsAtom(EmptyList)` is truth, so
`add_node(EmptyList)` is accepted, and `add_edge(Pair(R, Pair(EmptyList, EmptyList)))` is
accepted. Both routes are open through the public API. No in-repo caller builds such a
graph; the findings below are API-reachable, not currently produced.

### A1 — false positive, pre-existing in the edge phase

G1: nodes `[b, y, z, w]`, edges `R(b,y)`, `S(b,z)`, `T([])`.
G2: nodes `[q, z2]`, edges `R([],q)`, `S(v,z2)`, `T(p)`.

Verdict: `truth`. Returned map: 6 entries over 5 carrier vertices, one source (`b`) bound
twice, and repeated images. An exhaustive search over the bijections of the two carriers
(`BijectionSearch` in the counterexample probe) finds **no** edge-preserving bijection; an
independent host enumeration of all 120 bijections agrees, with 0 hits. The pair is not
isomorphic: `R` forces `b -> []` and `S` forces `b -> v`.

Mechanism: once `b -> []` is recorded, a later forward lookup of `b` returns `[]`, which
`_extend_bijection` reads as "unmapped", so `b` is bound a second time. The pre-patch
matcher (`git show b3be7e7:matching.py`) returns the same `truth` for this pair with 5
entries and no duplicate image, so the unsound accept is pre-existing; the patch adds a
completion step that neither detects it nor repairs the map it returns.

### A2 — false negative, introduced by this patch

G1: nodes `[a]`, edge `R(a,[])`. G2: no declared nodes, edge `R(p,q)`.
Carriers `{a, []}` and `{p, q}` have equal size and the edge-consistent bijection
`a -> p`, `[] -> q` exists, which is exactly what the new docstring promises to accept.

* pre-patch: `truth`, 2 bindings;
* patched: **`not-iso`**, 0 bindings, with `q` reported free although it is mapped.

`_unmapped` calls `_lookup_reverse(q)`, which returns the source `[]`, and the identity test
against the absence sentinel reads that as "no preimage". The free sets then differ in size
and `_complete_mapping` refuses a pair its own definition admits.

### A3 — the verdict depends on edge order

The A1 pair with the edge store reordered:

* `R, S, T` -> `truth`, 6 entries over 5 vertices, one source bound twice;
* `S, R, T` -> `not-iso`.

Same graph pair, same carriers, different verdict. Claim 6 fails on edge order alone.

## Finding B — a Patricia-backed node store is read raw

`_store_values` tests `IsPair` first, then `EmptyList`, and only then falls back to
`GraphStoreValues`. Patricia terms are themselves `Pair`s
(`Pair(SearchPatriciaBranchLabel, Pair(prefix, Pair(choices, EmptyList)))`), so the fallback
is unreachable for exactly the stores it exists to unwrap.

Measured with the repository's own constructors (`SearchPatriciaBranch/Choice/Leaf`):

* `GraphStoreValues(store)` yields the **2** node values;
* `_carrier` yields **3** "vertices" (branch label, prefix, choices);
* two graphs holding the **same two nodes**, one stored as a Patricia and one as a bare
  chain: **`not-iso`**;
* two bare chains of 2: `iso`.

Every other consumer of node and edge stores in `graph.py` reads through `GraphStoreValues`
(lines 626, 738-741, 900-901, 1129-1130, 1340-1341, 1401-1402, 1419-1420, 1430-1433);
`matching.py` is the one reader that does not. Nothing in-repo assigns a Patricia to
`graph.nodes`, so this too is API-reachable rather than currently produced.

## Is the order-based completion mathematically sufficient?

For the implemented semantics as intended — distinct entities, `Pair` edges, chain stores,
no `EmptyList` entity — yes. The premise "unmatched implies edge-free" follows from the edge
phase binding every argument of every unified edge, and any bijection between two edge-free
sets preserves all edges. The pairing order therefore cannot affect validity; it only fixes
which of the admissible maps is returned. Sufficiency fails as implemented because the
premise fails on the two reachable carrier shapes above: the sentinel makes an
edge-involved vertex look free (A), and the store reader can put non-vertices into the
carrier while leaving real ones out (B). Neither the cardinality gate nor the completion
reports either condition.

## Ready to integrate?

The design is sound and ordinary-case behaviour is correct; four of the six claims hold as
stated and one more holds only under an unstated representation assumption. Two narrow
fixes cover the findings:

1. route `_store_values` through `GraphStoreValues` unconditionally — bare chains and
   `EmptyList` pass through that edge unchanged, and a Patricia store is unwrapped the way
   the rest of the codebase unwraps it;
2. give absence a sentinel that cannot be a carrier entity, or refuse `EmptyList` from the
   carrier with a machine term, so `_unmapped`, `_lookup_forward` and `_extend_bijection`
   cannot confuse "absent" with a bound entity.

Regressions to add alongside them: a Patricia store against an equivalent bare chain, an
edge argument equal to `EmptyList`, and a bijectivity assertion on the returned map
(distinct sources, distinct images, entry count equal to carrier size).

## Scope

The verdicts above are for the fixtures in the probe, on this commit, under the graph
semantics the repository implements (`Pair` edges, chain and Patricia stores). The pass says
nothing about graphs built from registered `Edge` subclasses: `_unify_edges` reads
`M.Head(edge)`, which would raise on such an object, although no in-repo caller constructs
one. It also says nothing about callers outside `validation/test17`; the matcher has no
production caller in this tree.
