# Tao Problem 1.1: hypergraph-friendly specification

## Source scope

This document translates Problem 1.1 and its development in Chapter 1, “Strategies in problem solving,” of Terence Tao’s *Solving Mathematical Problems*, using printed pages 1–7 (PDF pages 14–20).

The chapter contains two different kinds of content:

1. the mathematical problem and its derivation;
2. problem-solving strategies: classifying the query, understanding the data and objective, choosing notation, decomposing goals, modifying the problem, looking ahead, prioritizing tactics, and checking the result.

Only the first category belongs in mathematical closure. The second must become executable search control in HYGE. A trace may report which heuristic decisions occurred, but storing Tao's strategies as inert `CandidateMethod`, `PreferredMethod`, or `Subgoal` facts would not implement them.

## Exact problem

A nondegenerate Euclidean triangle has side lengths in an arithmetic progression with common difference $d$. Its area is $t$. Determine all three side lengths and all three angles.

For a canonical orientation, take $d \ge 0$ and associate the sides with opposite angles $\alpha,\beta,\gamma$ so that their lengths are

$$
b-d,\qquad b,\qquad b+d.
$$

The inputs are therefore $d$ and $t$, subject to

$$
d \ge 0,\qquad t>0.
$$

The result is the triangle's metric structure: the length function on its sides and the angle-measure function on its angles. In the centered representation developed by Tao, those assignments have values

$$
b-d,\quad b,\quad b+d
$$

and

$$
\alpha,\quad\beta,\quad\gamma,
$$

with each value attached to its geometric side or angle. This is not a proposition whose natural target is `Solved(Triangle)`, nor a collection of independent requests. It is one parameterized evaluation. The current engine cannot represent that structural evaluation directly: every `SearchJob` has one explicit `goal`. A later planner can preserve the parent evaluation while launching separate jobs for derived obligations, but that is proposed work, not current heuristic behavior.

## Closed-form answer

Tao uses the symmetric middle side $b$. Heron’s formula reduces to

$$
t^2=\frac{3b^2(b^2-4d^2)}{16}.
$$

Equivalently,

$$
3b^4-12d^2b^2-16t^2=0.
$$

Treating $b^2$ as the quadratic unknown gives

$$
b^2=2d^2+\sqrt{4d^4+\frac{16}{3}t^2}.
$$

The other quadratic branch is negative when $t>0$, so it cannot equal $b^2$. Hence

$$
b=\sqrt{2d^2+\sqrt{4d^4+\frac{16}{3}t^2}}.
$$

The side lengths are

$$
\ell_\alpha=b-d,\qquad
\ell_\beta=b,\qquad
\ell_\gamma=b+d.
$$

Here $\ell_\alpha$ is opposite $\alpha$, and similarly for $\beta$ and $\gamma$.

Tao says that the angles then follow from the cosine laws. Written explicitly,

$$
\alpha=\arccos\!\left(
\frac{b^2+(b+d)^2-(b-d)^2}{2b(b+d)}
\right),
$$

$$
\beta=\arccos\!\left(
\frac{(b-d)^2+(b+d)^2-b^2}{2(b-d)(b+d)}
\right),
$$

$$
\gamma=\arccos\!\left(
\frac{(b-d)^2+b^2-(b+d)^2}{2(b-d)b}
\right).
$$

The area assumption also proves feasibility. Since $t>0$,

$$
\sqrt{4d^4+\frac{16}{3}t^2}>2d^2,
$$

so $b^2>4d^2$ and therefore $b>2d$. This gives positive side lengths and the strict triangle inequality

$$
b+d<(b-d)+b.
$$

Thus the formula produces one nondegenerate triangle up to congruence, with the equal-side special case $d=0$ included.

## Problem instance and query

The mathematical state should identify the triangle structurally. A side is determined by its endpoints, and an angle is determined by its vertex and rays. Magnitude and enumeration do not identify either object.

```text
Triangle(triangle_1_1)
VertexOf(u, triangle_1_1)
VertexOf(v, triangle_1_1)
VertexOf(w, triangle_1_1)
Distinct(u, v, w)

SideOf(Segment(v, w), triangle_1_1)
SideOf(Segment(w, u), triangle_1_1)
SideOf(Segment(u, v), triangle_1_1)

AngleOf(Angle(v, u, w), triangle_1_1)
AngleOf(Angle(w, v, u), triangle_1_1)
AngleOf(Angle(u, w, v), triangle_1_1)

Opposite(Segment(v, w), Angle(v, u, w))
Opposite(Segment(w, u), Angle(w, v, u))
Opposite(Segment(u, v), Angle(u, w, v))

Length(Segment(v, w), x)
Length(Segment(w, u), y)
Length(Segment(u, v), z)
AngleMeasure(Angle(v, u, w), alpha)
AngleMeasure(Angle(w, v, u), beta)
AngleMeasure(Angle(u, w, v), gamma)
Area(triangle_1_1, t)
Positive(t)
NonNegative(d)
```

The symbols $x,y,z$ denote values, not side identities. The arithmetic-progression witness orders those values for the purpose of the relation. Reversing the witness does not rename the triangle's sides. When $d=0$, the values coincide while the three sides remain distinct geometric objects.

The intended query is held outside mathematical closure:

```text
EvaluateMetricStructure(triangle_1_1)
```

`EvaluateMetricStructure` is specification notation, not an existing constructor. Its intended completion condition is structural: the mathematical state determines the length assigned to every side and the measure assigned to every angle, with the assignments satisfying the givens and triangle constraints. This avoids six positional `Need` facts and a universal `Solved` wrapper.

The current search API cannot execute that query as written. `SearchJob` accepts one concrete `goal`, and success means either that the current term equals that goal or, for a knowledge state, that the goal occurs as a fact. Evaluation classification and equation-directed planning do not exist. They belong in the proposed planner described below.

## Arithmetic progression in the existing sequence representation

The repository already has a sequence constructor:

```text
Sequence(name, base_value, pattern, replacement)
```

`constructors.py` stores exactly those four arguments. `SequenceName`, `SequenceBase`, `SequencePattern`, and `SequenceReplacement` retrieve them. The only concrete construction example is `SqrtSeq`, whose base is `a` and whose recurrence pattern for the successor term is replaced by the Newton-step expression. There is no `IndexDomain`, `ConsecutiveIntegerDomain`, `TermAt`, `SequenceLength`, or binary `ArithmeticProgression(q,d)` constructor.

An arithmetic progression should therefore be represented as a recurrence, using the same shape rather than a parallel sequence ontology. In schematic term notation:

```text
n = Var(n)
q_name = APName(d)
q_n = Apply(q_name, n)
q_succ_n = Apply(q_name, Succ(n))

Sequence(
    q_name,
    x,
    q_succ_n,
    Add(q_n, d)
)
```

This says that the base value is $x$ and that matching a successor term $q(n+1)$ unfolds to $q(n)+d$. `APName`, `Apply`, and `Add` above describe term shapes; the implementation must choose existing labels or add ordinary labels outside `core.py`. The essential point is that AP structure is carried by the existing `Sequence` fields:

- `name = q_name`;
- `base_value = x`;
- `pattern = q_succ_n`;
- `replacement = q_n+d`.

For Tao's three side values, the recurrence is sampled only at zero, one, and two:

$$
q(0)=x,\qquad q(1)=x+d,\qquad q(2)=x+2d.
$$

The association between those values and the three structural sides is still missing from the repository. It needs an ordinary relation such as

```text
Length(Segment(v, w), Apply(q_name, zero))
Length(Segment(w, u), Apply(q_name, one))
Length(Segment(u, v), Apply(q_name, two))
```

`Segment`, binary `Length`, and the vertex/incidence relations in this document are also required domain additions; current geometry packs use positional unary terms instead.

### Required AP rules that do not currently exist

The `Sequence` constructor is data only. No installed theorem or rewrite rule consumes `SequencePattern` or `SequenceReplacement`. The implementation therefore needs explicit rules:

1. **Base unfolding**

   $$
   q(0)\longrightarrow x.
   $$

   The rule reads `SequenceBase(q)` and rewrites the base application to that value.

2. **Successor unfolding**

   $$
   q(n+1)\longrightarrow q(n)+d.
   $$

   More generally, match the stored `SequencePattern` and instantiate the stored `SequenceReplacement` with the match bindings.

3. **Two concrete unfoldings for this problem**

   $$
   q(1)\longrightarrow x+d,
   \qquad
   q(2)\longrightarrow (x+d)+d.
   $$

4. **Arithmetic normalization and equality rules**

   Normalize $(x+d)+d$ to $x+2d$, orient equalities for substitution, and prove equivalent centered equations after introducing $b=q(1)$:

   $$
   q(0)=b-d,
   \qquad
   q(1)=b,
   \qquad
   q(2)=b+d,
   \qquad
   q(0)+q(2)=2b.
   $$

5. **Finite-use boundary**

   The triangle problem needs only indices zero, one, and two. No general finite-domain machinery is required to state this instance. A later generic finite-sequence layer may add a bound, but this specification does not claim that such a bound exists now.

The repository's current `ArithmeticProgressionLabel` is unary and the arithmetic pack derives only `MiddleTermAverage(object)`. That rule does not define or unfold a recurrence. It should be replaced or bridged to the recurrence representation above before it is used as mathematical evidence.

Reversal and the sign change $d\mapsto-d$ are valid mathematical consequences, but HYGE has no AP reversal rule. They remain requirements, not current capability.

## Required mathematical inference layer

Everything in this section is a target rule/result unless a cited repository rule already provides it. The present packs do not implement the structural geometry relations, recurrence unfolding, Heron reduction, branch admissibility, or angle recovery in this form.

### 1. Instantiate the centered progression

```text
Length(Segment(v, w), b_minus_d)
Length(Segment(w, u), b)
Length(Segment(u, v), b_plus_d)
```

The center $b$ is a value shared by the progression equations. It is not a side name and is not initially a separate query.

### 2. Derive the reduced Heron constraint

From the triangle, its area quantity, and the three side-length formulas:

```text
Equation(heron_equation)
DerivedFrom(heron_equation, HeronFormula)
EquivalentEquation(heron_equation, reduced_heron_equation)
```

The reduced equation is

$$
16t^2=3b^2(b^2-4d^2).
$$

### 3. Normalize to a quadratic in $b^2$

```text
PolynomialEquation(middle_length_polynomial)
PolynomialIn(middle_length_polynomial, b)
QuadraticIn(middle_length_polynomial, b_squared)
```

with

$$
3b^4-12d^2b^2-16t^2=0.
$$

### 4. Select the admissible branch

The quadratic rule produces two candidates for $b^2$. Positivity and the fact that a square is nonnegative reject the inadmissible candidate. The surviving equations determine $b^2$ and then the positive length value $b$. These are ordinary algebraic value/equality facts with derivation provenance; they need no problem-specific `MiddleLengthValue` relation.

### 5. Instantiate side lengths

```text
Length(Segment(v, w), low_expression)
Length(Segment(w, u), middle_expression)
Length(Segment(u, v), high_expression)
```

### 6. Recover angles

A generic cosine-law rule consumes three side values and an `Opposite` relation, producing:

```text
CosineOf(Angle(v, u, w), cosine_alpha_expression)
CosineOf(Angle(w, v, u), cosine_beta_expression)
CosineOf(Angle(u, w, v), cosine_gamma_expression)

AngleMeasure(Angle(v, u, w), alpha_expression)
AngleMeasure(Angle(w, v, u), beta_expression)
AngleMeasure(Angle(u, w, v), gamma_expression)
```

A proposed query evaluator would read these mathematical assignments directly. No such evaluator exists now. It should avoid an `AnswerLength`, `AnswerAngle`, or positional output layer.

## Proposed expression representation

This is a storage recommendation, not current behavior. The existing expression terms are nested constructor terms; no expression-DAG interning layer is implemented for these formulas. A later implementation should avoid copied term trees by assigning each operation result an identity and connecting it to its operands:

```text
Square(expr_d2, d)
Square(expr_d4, expr_d2)
Square(expr_t2, t)
Multiply(expr_4d4, four, expr_d4)
Multiply(expr_16_over_3_t2, sixteen_over_three, expr_t2)
Add(expr_inner_sum, expr_4d4, expr_16_over_3_t2)
SquareRoot(expr_inner_root, expr_inner_sum)
Multiply(expr_2d2, two, expr_d2)
Add(expr_outer_sum, expr_2d2, expr_inner_root)
SquareRoot(expr_b, expr_outer_sum)
```

The same `expr_b` node is used as the value in the middle side's `Length` relation and as an operand in the other side and angle derivations. This prevents repeated copies of the full formula.

Canonical commutative operation nodes could then be interned by structural key, keeping proposed domain relations such as `Length` and `AngleMeasure` shallow regardless of expression size.

## Current executable search behavior

The current heuristic does not perform Tao's strategic operations. Its behavior is limited and inspectable.

### What `heuristics.py` actually provides

1. `Heuristic` stores six controls: search mode, rule-order mode, beam width, two cost weights, and canonicalization strength.
2. `HeuristicCanonicalize` optionally normalizes knowledge and recursively canonicalizes pair terms.
3. `HeuristicGoalHeadIndex` collects term heads already present in the explicit goal.
4. `HeuristicGoalHeadNeighborhood` expands that set backward through unary rules whose replacement head is already admitted.
5. `HeuristicGoalHeadAllowsSubterm` rejects rewrite sites whose heads are outside that set.
6. The anchor preference object orders multi-premise matching anchors by lower fanout, fewer variables, greater specificity, and earlier premise position. The consumer is in `proof.py`.

The search engine then uses these controls to:

- choose DFS, BFS, beam, A-star, or rewrite DFS;
- order applicable rules, optionally favoring replacement heads that match the explicit goal head;
- prune rewrite sites by the goal-head neighborhood;
- limit a beam frontier;
- canonicalize terms;
- weight reported proof and search costs.

None of these operations creates a new goal.

### Exact current job and state boundary

A `SearchJob` contains:

```text
start
one goal
rules
heuristic
status
frontier and counters
result plan
visited state
theorem-rule cache
rewrite-rule bundle
```

A `SearchState` contains:

```text
current term
reversed plan
seen terms
steps remaining
cursor
```

A search transition applies a theorem or rewrite rule to the current term, canonicalizes the result, and enqueues another `SearchState` in the same job. For a knowledge term, theorem closure adds justified facts. Success is tested against the job's single goal. The cursor records progress through theorem or rewrite candidates; it is not a goal stack.

The repository has no executable representation for:

- query classification;
- goal or subgoal nodes;
- dependencies among goals;
- creation of child `SearchJob` objects from a parent goal;
- specialization, weakening, reversal, or generalization of a problem;
- transfer of results from a modified problem;
- notation comparison or projected-consequence look-ahead;
- a structural metric-evaluation completion predicate.

The current Tao packs simulate strategy with mathematical labels such as `EvaluateProblem`, `AlgebraicApproach`, and `Solved`. That is encoded content, not planner behavior.

## Proposed planner and search orchestration

This section specifies new behavior. It does not describe `heuristics.py` as it stands. The planner sits above `SearchJob`; ordinary rule application remains inside the existing search engine.

### Planner records

The planner needs explicit records equivalent to:

```text
PlannerProblem(problem_id, start, root_goal, rules, heuristic)
PlannerObligation(obligation_id, problem_id, goal, status)
PlannerDependency(parent_obligation, child_obligation)
PlannerJob(obligation_id, search_job)
PlannerVariant(variant_id, problem_id, transform, variant_start, variant_goal)
PlannerTransfer(variant_id, transfer_rule, validation_goal)
```

These are proposed search-control records, not facts in mathematical closure. They can be represented with normal labels and pairs outside `core.py`.

### Root transition

Given a mathematical start state $K$ and root query $G$:

1. create `PlannerProblem(p, K, G, rules, heuristic)`;
2. create one pending root obligation for $G$;
3. if $G$ is directly executable, construct `SearchJob(K, G, rules, heuristic, ...)`;
4. run the job with the existing engine;
5. on success, store its derivation and mark the obligation proved;
6. on exhaustion, mark that route failed without asserting a mathematical negation.

For `EvaluateMetricStructure`, direct execution first requires expansion into concrete obligations because the current goal check handles one term, not a structural query.

### Backward decomposition transition

For a pending obligation $G$ and a rule $R$ with premises $P_1,\ldots,P_k$ and conclusion $C$:

1. match $C$ against $G$;
2. reject the route if matching fails;
3. apply the resulting bindings to every $P_i$;
4. discard premises already present in $K$;
5. intern each remaining instantiated premise by its canonical goal key so identical obligations are shared;
6. add dependency edges from $G$ to those obligations;
7. launch one `SearchJob` for each runnable obligation, each with one explicit goal;
8. when a child job succeeds, replay its derivation to obtain an updated justified knowledge state;
9. when every premise is proved in a common compatible state, apply $R$ once to derive $G$ and close the parent;
10. if any child route fails, try another rule whose conclusion matches $G$.

This is how subgoal jobs would actually be created. The current `GoalHeadRuleOrderer` only reorders rules; it does not execute steps 1–10.

For Tao's problem, the planner must be given real rules whose conclusions connect the obligations. It cannot infer the chain from prose. A valid rule dependency could be:

```text
KnownMiddleValue(b), APRecurrence(q, d), SideAssociation(q, triangle)
    -> KnownAllSideLengths(triangle)

KnownAllSideLengths(triangle), CosineLawRulesAvailable
    -> KnownAllAngleMeasures(triangle)

KnownAllSideLengths(triangle), KnownAllAngleMeasures(triangle)
    -> EvaluateMetricStructure(triangle)
```

`KnownMiddleValue` and the aggregate heads here are planner-facing specification terms. Their implementation must define exact completion checks or replace them with concrete equality goals.

### Modified-problem transition

A problem modification is never a mutation of the parent job. The planner creates a variant with its own start, goal, and `SearchJob`:

1. choose a declared transform $T$;
2. compute `variant_start = T_start(K)` and `variant_goal = T_goal(G)`;
3. record exactly which facts were added, removed, or rewritten;
4. launch `SearchJob(variant_start, variant_goal, rules, heuristic, ...)`;
5. keep the result isolated when no transfer theorem is supplied;
6. when a transfer rule is supplied, instantiate it with the variant derivation;
7. launch a validation job whose goal is the corresponding parent-state consequence;
8. transfer the consequence only after that validation succeeds.

The four transform classes have different proof obligations:

- **Specialization:** adds a premise such as $d=0$. Its result applies only under that premise unless a separate theorem removes it.
- **Weakening:** removes a given or weakens a goal. Failure of the weakened job proves nothing; success transfers only through an explicit monotonicity or implication rule.
- **Reversal:** rewrites the recurrence and side association. Transfer requires proved equivalence and an inverse mapping, including $d\mapsto-d$.
- **Generalization:** replaces constants or structures by variables and launches a schematic goal. A result transfers only after schema instantiation and derivation replay succeed.

For scaling, the planner would need a declared scaling transform and a theorem connecting the scaled and original equations. Merely observing matching dimensions is not a transferable proof.

### Scheduling and preservation

Runnable obligations are those whose declared dependencies are closed. The scheduler may prioritize jobs, but priority does not alter their mathematical content. Completed derivations are stored through the existing derivation cache. Failed routes and variant outcomes belong to planner history. Only replayed rule conclusions enter mathematical knowledge.

This design preserves the current invariant of one explicit goal per `SearchJob` while adding decomposition and modified-problem exploration above it.

## What the current packs get wrong

The existing packs do not faithfully encode the source problem or the strategies used to solve it:

1. The initial state says that side lengths, angles, area, and common difference exist, but does not bind $d$ and $t$ as values in the relevant relations.
2. The goal `Solved(Triangle(...))` erases the evaluation query and its structural completion condition.
3. `EvaluateProblem` and `AlgebraicApproach` are presented as mathematical consequences instead of configuring search.
4. `FirstEdge(Edges(triangle))` and related selectors confuse collection access with geometric identity.
5. `side_low`, `side_middle`, and similar names would repeat the same error by identifying sides through contingent magnitudes.
6. `ArithmeticProgression(object)` does not state what the terms are, how they are ordered, or what constant successive difference means. `ArithmeticProgression -> MiddleTermAverage` is a consequence without a definition.
7. `Solved` is used for equations, aggregate knowledge, and whole-problem completion.
8. Large expression trees are copied into premises and replacements, forcing repeated structural traversal.
9. Generic ontology rules manufacture positional sides and angles merely from `Triangle(triangle)` instead of representing vertices, segments, angles, and their incidence.
10. The final rule checks aggregate status wrappers rather than evaluating whether the requested metric functions have been determined.
11. Tao's strategies are represented, when represented at all, as theorem-like steps rather than general heuristics for classification, relevance, decomposition, notation, problem modification, look-ahead, and validation.

## Implementation boundary

A corrective implementation needs four separate structures:

1. **Mathematical state:** givens, recurrence data, geometry relations, derived equalities, admissibility facts, and expression terms.
2. **Root query:** the requested metric evaluation and its exact completion check.
3. **Planner state:** obligations, dependencies, child jobs, variants, transfer rules, and route status.
4. **Existing search/proof state:** `SearchJob`, `SearchState`, cursors, rule applications, plans, caches, and derivations.

The heuristic remains configuration consumed by search. It must not be credited with planner transitions. The planner creates and coordinates jobs; the existing search engine proves one explicit goal per job; only replayed derivations add mathematical consequences.

No change to `core.py` is required for this design. New labels, pair-shaped records, constructor edges, planner orchestration, AP recurrence rules, and geometry rules can live in ordinary modules and packs.
