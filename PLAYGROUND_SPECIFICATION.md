# Machine Playground: Tensor Evaluation, Invariant Mining & Algebraic Templates

This document specifies the exact role, architectural separation, and operation of the **Playground**, **Invariant Miner**, **Algebraic Template Engine**, and **Interactive Session Loop**.

---

## 1. True Architectural Purpose of the Playground

The playground is **not** an automated theorem prover, nor is it a hardcoded repository of pre-packaged mathematical tricks (such as fixed quadratic residue filters or mod-4 parity tests). 

The playground is the machine's **empirical laboratory**:
1. **Domain Tensor Generation**: Takes ground collections of Peano naturals / entities (e.g., $D = 0..10$) and forms $k$-ary Cartesian powers:
   $$D^k = D \times D \times \dots \times D$$
2. **Evaluation Tensor Computation**: Multiplies the domain tensor by a predetermined catalog of fundamental operations ($+, -, \times, \div, \text{mod}, \text{divides}, \text{gcd}$):
   $$\mathcal{T}(op, \vec{x}) = op(x_1, \dots, x_k) \quad \forall \vec{x} \in D^k$$
3. **Execution Trace Emittance**: Records the concrete input-output ground evaluation mappings and emits raw evaluation tensors without bias or hardcoded conclusions.

---

## 2. Separation of Responsibilities Across Modules

```
 ┌────────────────────────────────────────────────────────┐
 │                      playground.py                     │
 │  - Build ground domains (0..N)                         │
 │  - Generate Cartesian powers D^k                       │
 │  - Evaluate operations systematically (Add, Mul, etc.) │
 │  - Output raw Evaluation Tensors & Traces              │
 └──────────────────────────┬─────────────────────────────┘
                            │ Raw Evaluation Tensors
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │                   invariant_miner.py                   │
 │  - Mine Algebraic Invariants / Laws:                   │
 │      * Commutativity: op(a,b) == op(b,a)               │
 │      * Associativity: op(op(a,b),c) == op(a,op(b,c))   │
 │      * Identity: op(a,e) == a                          │
 │      * Divisibility preservation                       │
 │  - Extract supporting ground witness sets              │
 │  - Check against known / already-named laws            │
 └──────────────────────────┬─────────────────────────────┘
                            │ Discovered Regularities & Examples
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │                 main.py (Live Dialogue)                │
 │  - Present regularity + witnesses to user:             │
 │    "Observed regularity: mul(a,b) == mul(b,a)...      │
 │     Would you care to give it a name?"                 │
 │  - User response: "Call this commutativity"            │
 │  - Appends to talk_lessons.log                         │
 │  - Promotes named rule into Active Promotion Ledger    │
 └──────────────────────────┬─────────────────────────────┘
                            │ Registered Named Laws
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │             curriculum.py / schemata.py                │
 │                 (Algebraic Templates)                  │
 │  - Synthesize Structural Templates:                    │
 │      Carrier Set + Operations + Satisfied Law Bundle   │
 │      (e.g., Semigroup, Monoid, Group, Ring)            │
 │  - User names the structure ("Call it a Monoid")       │
 │  - Template Checking: Match concrete problem entities  │
 │    (e.g., roots of unity, permutation symmetries,      │
 │     modular units) against known templates             │
 └──────────────────────────┬─────────────────────────────┘
                            │ Verified Template Instances
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │           planner.py / graph_task.py (W13)             │
 │  - Problem Solving & Backward Planning:                │
 │  - When entity matches Template T, import abstract     │
 │    theorems established for T (Lagrange, Abel, etc.)   │
 └────────────────────────────────────────────────────────┘
```

---

## 3. The Interactive Discovery Lifecycle

1. **Step 1: Raw Evaluation**:
   The playground sweeps operations across $(0..10)^k$ to produce ground results.

2. **Step 2: Law Mining & Naming**:
   The invariant miner scans the results. When it finds a universal property (e.g., $a \cdot b = b \cdot a$), it prepares an `ObservedRegularityLabel` with ground examples.
   In `main.py`, the machine prompts:
   `"We have observed regularity op(a,b) == op(b,a) with supporting examples ((1,2)->2, (2,1)->2, ...). Would you care to give it a name?"`
   The user replies:
   `"Call this commutativity of multiplication"`
   The machine logs:
   `"Yes, recorded to talk_lessons.log"`

3. **Step 3: One-Time Discovery Constraint**:
   Once a regularity is named and recorded in `talk_lessons.log`, subsequent sweeps recognise it as an established law and do not re-propose it.

4. **Step 4: Algebraic Structure Synthesis**:
   When a collection of operations over a carrier set satisfies a specific bundle of known laws (e.g., associative, identity, commutative), the system bundles them into an unnamed structure template:
   `"We have an entity with integers and addition satisfying [associativity, identity, commutativity]. We need a name for this sort of entity."`
   User: `"Call it a commutative monoid"`
   Recorded to `talk_lessons.log` and promoted.

5. **Step 5: Problem Solving via Template Matching**:
   When analyzing specific mathematical entities (such as modular residues $(\mathbb{Z}/n\mathbb{Z})^\times$ or roots of unity):
   - The entity is checked against known structural templates.
   - Upon matching (e.g. verified as an abelian group), the prover transfers the general theorems of that template directly to the concrete problem.
