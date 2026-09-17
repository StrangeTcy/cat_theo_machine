# Charter P-Track: Verified Symbolic Surface Realization (Prose-Track)

**Status:** Proposed / Ready for Admission  
**Track:** P-Track (Surface Realization & Reporting Engine)  
**Deliverable Gate:** Surface Back-Check Entailment Verifier & Rent Benchmark  
**Upstream Dependencies:** Gate D (Ontology & Planner Contracts), Gate E (Graph Task Representation)  
**Downstream Dependents:** Gate H (Reversible Surface Language)  

---

## 1. Executive Summary & Purpose

The HYGE Machine represents mathematical and search derivations, obligations, bindings, and execution states as explicit machine terms (`Atom`, `Edge`, `Pair`, `Hypergraph` context structures). At present, the extraction of readable status reports and derivation summaries from machine terms produces brittle, repetitive, or structurally inverted prose.

Prose generation is not an open-ended natural language generation problem, nor does it require stochastic language models (LLMs). Prose in HYGE is an **inert, read-only projection artifact rendered deterministically from machine terms**.

This charter establishes the **P-Track (Prose Track)**: a deterministic symbolic realization pipeline with an independent, round-trip back-check verifier operating as a hard delivery gate. Just as search attempts and worker claims are not admitted without coordinator-side derivation replay, no generated prose artifact is admitted or surfaced unless it parses back and formally entails against the source terms.

```text
INPUT:       Machine terms (derivation tree, claim, obligation, alist, atom, status)
PIPELINE:    Content Selection → Document Planning → Sentence Planning → Surface Realization
VERIFIER:    Surface Back-Check (parse text → candidate terms ⊑ source terms)
OUTPUT:      Inert prose artifact (verified faithful projection)
SECURITY:    NO WRITE ACCESS to accepted state, hypergraph stores, or admission
```

---

## 2. Non-Negotiable Engineering Constraints

All implementation under this charter must adhere strictly to the repository's foundational architecture rules:

1. **`core.py` is invariant**: Do not modify `core.py`.
2. **Prohibited Python constructs**: No `isinstance`, `hasattr`, `type`, `__class__`, or `__new__` in new or revised code.
3. **No host collections or native booleans**: No Python `list`, `dict`, `set`, or Python `bool` (`True`/`False`) inside the machine/runtime state design. All intermediate document trees, plans, lexicons, and tokens must use machine-native `Pair`, `EmptyList`, `truth_value`, `false_value`, and explicit `Edge` constructors.
4. **No LLMs or stochastic models**: All generation, aggregation, planning, and parsing must be 100% deterministic, symbolic, and inspectable in isolation.
5. **Strict read-only isolation**: The realization pipeline possesses zero write, mutation, or admission privileges. It cannot modify `Hypergraph`, mutate context stores, discharge obligations, or alter proof state.
6. **No module globals or monkeypatching**: All state and configurations reside in explicit constructor registries, runtime objects, or machine-native parameter terms.
7. **Primacy of faithfulness over style**: A readability or style score must never override a faithfulness failure. If a sentence fails the back-check, the artifact is rejected.

---

## 3. Architecture: The Three Failure Loci & Standard Pipeline

Defects in machine-generated prose stem from three distinct, decoupled stages. Each stage is isolated into an inspectable machine component:

```text
Machine Source Terms (Hypergraph, PlannerState, Derivations)
      │
      ▼
[1. Content Selection Pass]     <-- Filters surface-worthy nodes; prunes low-level rewrites
      │  (Selected Term Set / Focus Subgraph)
      ▼
[2. Document Planning]          <-- Maps term dependency edges to rhetorical relation trees
      │  (Document Plan Tree: result, because, therefore, despite, still-open)
      ▼
[3. Sentence Planning]          <-- Aggregation, clause grouping, referring-expression generation
      │  (Sentence Plan Structures: merged subjects, pronominalized references)
      ▼
[4. Surface Realization]        <-- Grammar + lexicon application; morphology & agreement
      │  (Candidate Surface Text)
      ▼
[5. Surface Back-Check Gate]    <-- Deterministic parser round-trips text to candidate terms;
      │                             diffs against source terms; checks entailment
      ▼
 Inert, Verified Prose Artifact
```

### Stage 1: Content Selection (What to Say)
* **Defect Diagnosed**: Dumps all intermediate substitution steps, restates trivial axiom premises, omits top-level goals or actual open failure points.
* **Mechanism**: A deterministic graph-marking pass over the term graph. Nodes are categorized into surface-worthy classes:
  - `RootGoal` (the query or evaluation target);
  - `DischargedObligation` (terminal milestones);
  - `KeyLemma` (promoted schema or non-trivial theorem application);
  - `TerminalStatus` (`proved`, `exhausted`, `timeout`, `open_failure`).
* Low-level algebraic normalizations and identity steps are pruned by default unless explicitly requested by diagnostic verbosity flags.

### Stage 2: Document Planning (Rhetorical Ordering & Grouping)
* **Defect Diagnosed**: Proof traversal order narrating derivations backwards; conclusions presented before hypotheses; lack of logical paragraph boundaries.
* **Mechanism**: Construction of an explicit intermediate **Document-Plan Tree** from term dependency edges. Rhetorical relations are assigned machine-native labels:
  - `RhetoricalResult`: Headline outcome or claim state.
  - `RhetoricalBecause`: Direct dependency premise edges.
  - `RhetoricalTherefore`: Consequent derivations.
  - `RhetoricalDespite`: Known bounds or intermediate failures overcome.
  - `RhetoricalStillOpen`: Unresolved obligations or pending search branches.
* Traversal follows human rhetorical convention (hypothesis → deduction → conclusion, or headline conclusion → supporting rationale), completely decoupled from raw DFS/BFS execution order.

### Stage 3: Sentence Planning & Aggregation (Syntactic Structure)
* **Defect Diagnosed**: Robotic single-clause repetition (*"Claim a is completed. Claim b is completed. Claim c is completed."*).
* **Mechanism**:
  - **Aggregation**: Combines co-predicated facts sharing identical relation heads across common arguments (*"Claims a, b, and c are discharged"*).
  - **Referring Expression Generation (REG)**: Generates short-form identifiers or pronouns after first mention (e.g., initial full expansion of a polynomial or obligation, followed by symbolic aliases or definite anaphora).

### Stage 4: Surface Realization (Morphology & Lexicon)
* **Defect Diagnosed**: Rigid string interpolation templates, grammatical agreement mismatches (singular/plural), broken punctuation.
* **Mechanism**: Lexicon mapping rules defined over machine label constructors, handling subject-verb-number agreement, connective insertion (*"furthermore"*, *"because"*, *"however"*), and typographic rendering.

---

## 4. The Deliverable Gate: Coordinator-Side Surface Back-Check

No prose artifact is trusted on generation. The central innovation of the P-Track is the **Surface Back-Check Verifier**: an independent parser that round-trips generated text back into machine terms and checks structural entailment against the source context.

```text
Algorithm SurfaceBackCheck(Text T, SourceTermGraph G):
    For each sentence S in T:
        P := ParseSentence(S)           // Deterministic parse -> candidate machine terms
        If P is Empty:
            Reject("Unparseable surface sentence", S)
        
        For each candidate term c in P:
            If Not EntailedBy(c, G):
                Reject("Stated relation has no supporting edge in source graph", c, S)
            
            If StatusOf(c) != StatusIn(G, c):
                Reject("Status atom mismatch (e.g., open vs discharged)", c, S)
    
    // Coverage Completeness Check
    For each mandatory node n in CriticalNodes(G):
        If n Not CoveredBy(T):
            Reject("Critical node omitted from report (e.g., open failure or goal)", n)
            
    Return PASS
```

### Mandatory Rejection Triggers:
1. **Hallucinated Edge / False Entailment**: A sentence asserts an equality, rule application, or relationship that does not exist in the source derivation.
2. **Status Inversion**: Narration describes an open obligation as discharged, or a proved lemma as open.
3. **Completeness / Coverage Defect**: A report labeled as "complete" or "summary" fails to narrate an active failure, timeout, or unsatisfied constraint.
4. **Binding Corruption**: A variable or constant binding in prose diverges from the concrete term in the source alist.

---

## 5. Evaluation Framework: Gold Corpus & Prose Rent

The rendering engine must optimize against a quantifiable **Prose Rent** benchmark without compromising soundness.

### A. Hard Gates (Zero Tolerance)
* **Faithfulness Rate**: 100% of factual sentences must successfully pass the Surface Back-Check against source terms.
* **Critical Coverage**: 100% of headline goals, terminal statuses, and unresolved obligations must be present.

### B. Performance Rent (Optimization Metrics)
* **Aggregation Ratio**: $\frac{\text{Aggregated Clauses}}{\text{Potential Redundant Predications}}$ (target: $\ge 0.75$).
* **Repetition Index**: Ratio of duplicate $n$-grams ($n \ge 3$) excluding bound variable identifiers.
* **Clause Depth & Length Bounding**: Enforce human readability ceilings (maximum clause depth $\le 3$, sentence length bounds between 12 and 35 words).
* **Gold Edit Distance**: Normalized Levenshtein / token edit distance evaluated against a curated, held-out Gold Corpus of approved mathematical and search reports.

---

## 6. Phased Implementation Plan

| Work Package | Focus | Scope & Deliverable | Exit Criteria |
|---|---|---|---|
| **P-1** | Baseline Defect Taxonomy & Sample Audit | Collect and inspect 10 representative bad Machine prose outputs. Formally classify every defect across: (1) Selection, (2) Structuring, or (3) Realization. | Dated inspection report filed in `verification/`. Zero renderer code edits before taxonomy is complete. |
| **P-2** | Rhetorical Document-Plan Intermediate | Implement machine-native rhetorical tree constructors (`RhetoricalResult`, `RhetoricalBecause`, `RhetoricalTherefore`, `RhetoricalStillOpen`) from planner/derivation dependency edges. | Document-plan tree constructed for all 10 sample problems independent of proof traversal order. |
| **P-3** | Sentence Planning & Aggregation Engine | Implement predicate aggregation over homogeneous obligation lists and referring expression generation. | Reduction of redundant clause occurrences by $\ge 70\%$ on the inspection corpus. |
| **P-4** | Deterministic Grammar & Lexicon Realizer | Machine-label lexicon rules with morphological agreement and connective placement. | Syntactically well-formed sentences generated across order, arithmetic, and geometry proof domains. |
| **P-5** | Surface Back-Check Gate & Rent Suite | Build the round-trip sentence parser, source term entailment diff, and automated prose rent test suite in `testsuite.py`. | 100% pass on Back-Check faithfulness; automated CI gate active in test suite. |

---

## 7. Deliverable Gate & Audit Checklist (Pass/Fail)

Before P-Track code can be merged and admitted to the runtime:

- [ ] **C1: `core.py` Untouched**: `git diff core.py` is completely empty.
- [ ] **C2: Strictly Deterministic**: Zero LLM calls, zero stochastic sampling, zero network dependencies.
- [ ] **C3: Zero Write Privileges**: Engine is purely functional: takes terms as input, returns inert text artifact; cannot mutate graph or context stores.
- [ ] **C4: Architecture Rule Conformance**: Zero occurrences of `isinstance`, `hasattr`, `type`, `__class__`, `__new__`, or host Python `list`/`dict`/`bool` in machine state paths.
- [ ] **C5: Explicit Document Plan**: Intermediate rhetorical tree is generated and verifiable as a standalone machine term.
- [ ] **C6: Aggregation Verified**: Predicate aggregation demonstrated on test obligations.
- [ ] **C7: Back-Check Hard Gate Operational**: Back-check verifier parses generated text, proves term entailment, and successfully catches intentional injected mutations/inversions.
- [ ] **C8: Gold Corpus Rent Benchmark Integrated**: Regression tests registered in `testsuite.py` with tracked rent metrics.
