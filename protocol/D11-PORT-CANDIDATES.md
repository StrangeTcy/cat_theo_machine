# D11 commit 2 — port candidates

Decision material for the first shipped pack port. **No pack has been
changed.** This is the inventory the operator rules on.

## Method

- **Attested surface vocabulary**: every atom appearing as the head of an
  application in a goal parsed from `logs/*.log` and `protocol/*.md`
  (73 goals), parsed with the real `_research_parse` and rendered with the
  real `_term_text`. These are the names the goal language actually uses.
- **Pack head symbols**: every `{sym: X}` in the head position of a `call`,
  at any depth, in each shipped pack. This is exactly the position the
  D11-MAP mapping applies to — `as_head=True` — so it is the set that a
  port can affect.

### Attested surface vocabulary (24 distinct)

```text
   59  pow
   25  eq
   19  plus
   17  times
   11  divides
    7  primitivetriple
    5  connected
    5  tag
    4  nosolutions
    4  unknowns
    3  anglesum
    3  cyclic
    3  grouporder
    3  cornersum
    2  commuting
    2  congruent
    2  impossible
    1  real
    1  sqrt
    1  forall
    1  implies
    1  greater
    1  badge
    1  crown
```

## Headline finding

**A mechanical port is not possible.** Of the distinct head symbols across
the shipped packs, only **two** reach an attested surface name by naive
derivation (strip `Label`, snake_case):

```text
  DividesLabel -> divides   (number-theory, 8 head uses)  CONFIRMED
  SqrtLabel    -> sqrt      (geometry, order-sign, sqrt-real)  CONFIRMED
```

Everything else is unattested, and the naive candidates for the dominant
arithmetic family are **wrong**, not merely unproven:

```text
  ExprAddLabel  naive: expr_add   attested goal name: plus
  ExprMulLabel  naive: expr_mul   attested goal name: times
  ExprPowLabel  naive: expr_pow   attested goal name: pow
  ExprEqLabel   naive: expr_eq    attested goal name: eq
  ExprLtLabel   naive: expr_lt    NO safe attested name -- `greater` is the
                                  attested comparison, and Lt is less-than,
                                  so mapping it to `greater` would assert the
                                  opposite relation
  ExprNegLabel  naive: expr_neg   `minus` is attested but binary; Neg is unary
  ExprFracLabel naive: expr_frac  nothing attested
```

A port that maps these by shape would compile cleanly, emit the audit
lines, and be semantically wrong. That is worse than no port, because it
would look like a working library.

## Per-pack inventory

### algebra-distribute.pack.yaml (27 rules)

```text
   64  ExprMulLabel                 -> times                UNATTESTED (attested goal name exists: times -- needs ruling)
   24  ExprAddLabel                 -> plus                 UNATTESTED (attested goal name exists: plus -- needs ruling)
   23  ExprFracLabel                -> expr_frac            UNATTESTED (no attested counterpart)
   12  ExprLtLabel                  -> expr_lt              UNATTESTED (no attested counterpart)
   10  ExprNegLabel                 -> expr_neg             UNATTESTED (no attested counterpart)
    4  ExprEqLabel                  -> eq                   UNATTESTED (attested goal name exists: eq -- needs ruling)
```

### arithmetic.pack.yaml (12 rules)

```text
   14  ExprAddLabel                 -> plus                 UNATTESTED (attested goal name exists: plus -- needs ruling)
   10  ApplyLabel                   -> apply                UNATTESTED (no attested counterpart)
    7  ExprMulLabel                 -> times                UNATTESTED (attested goal name exists: times -- needs ruling)
    5  SuccLabel                    -> succ                 UNATTESTED (no attested counterpart)
    4  SequenceLabel                -> sequence             UNATTESTED (no attested counterpart)
    4  ExprEqLabel                  -> eq                   UNATTESTED (attested goal name exists: eq -- needs ruling)
    3  APNameLabel                  -> a_p_name             UNATTESTED (no attested counterpart)
    2  CommonDifferenceLabel        -> common_difference    UNATTESTED (no attested counterpart)
    2  ArithmeticProgressionLabel   -> arithmetic_progression UNATTESTED (no attested counterpart)
    1  ParameterLabel               -> parameter            UNATTESTED (no attested counterpart)
    1  MiddleTermAverageLabel       -> middle_term_average  UNATTESTED (no attested counterpart)
    1  LengthLabel                  -> length               UNATTESTED (no attested counterpart)
    1  ExprNegLabel                 -> expr_neg             UNATTESTED (no attested counterpart)
```

### engel-blackboard.pack.yaml (13 rules)

```text
   13  ParityLabel                  -> parity               UNATTESTED (no attested counterpart)
   11  ExprAddLabel                 -> plus                 UNATTESTED (attested goal name exists: plus -- needs ruling)
   10  BoardSumLabel                -> board_sum            UNATTESTED (no attested counterpart)
    6  ExprNegLabel                 -> expr_neg             UNATTESTED (no attested counterpart)
    6  ExprMulLabel                 -> times                UNATTESTED (attested goal name exists: times -- needs ruling)
    2  AbsDiffLabel                 -> abs_diff             UNATTESTED (no attested counterpart)
    2  MoveErasesLabel              -> move_erases          UNATTESTED (no attested counterpart)
    1  MinLabel                     -> min                  UNATTESTED (no attested counterpart)
    1  IsEvenLabel                  -> is_even              UNATTESTED (no attested counterpart)
    1  InitialBoardLabel            -> initial_board        UNATTESTED (no attested counterpart)
    1  InvariantLabel               -> invariant            UNATTESTED (no attested counterpart)
    1  TerminalLabel                -> terminal             UNATTESTED (no attested counterpart)
```

### engel-coins.pack.yaml (4 rules)

```text
    4  SuccLabel                    -> succ                 UNATTESTED (no attested counterpart)
```

### engel-means.pack.yaml (0 rules)

```text
```

### geometry-ontology.pack.yaml (16 rules)

```text
   13  TriangleLabel                -> triangle             UNATTESTED (no attested counterpart)
    7  EdgesLabel                   -> edges                UNATTESTED (no attested counterpart)
    3  PolygonLabel                 -> polygon              UNATTESTED (no attested counterpart)
    3  LengthLabel                  -> length               UNATTESTED (no attested counterpart)
    2  DistinctLabel                -> distinct             UNATTESTED (no attested counterpart)
    2  FirstEdgeLabel               -> first_edge           UNATTESTED (no attested counterpart)
    2  SecondEdgeLabel              -> second_edge          UNATTESTED (no attested counterpart)
    2  ThirdEdgeLabel               -> third_edge           UNATTESTED (no attested counterpart)
    1  VerticesLabel                -> vertices             UNATTESTED (no attested counterpart)
    1  SideLengthsLabel             -> side_lengths         UNATTESTED (no attested counterpart)
    1  AnglesLabel                  -> angles               UNATTESTED (no attested counterpart)
    1  FirstAngleLabel              -> first_angle          UNATTESTED (no attested counterpart)
    1  SecondAngleLabel             -> second_angle         UNATTESTED (no attested counterpart)
    1  ThirdAngleLabel              -> third_angle          UNATTESTED (no attested counterpart)
    1  AreaLabel                    -> area                 UNATTESTED (no attested counterpart)
```

### geometry.pack.yaml (48 rules)

```text
   58  LengthLabel                  -> length               UNATTESTED (no attested counterpart)
   58  ExprPowLabel                 -> pow                  UNATTESTED (attested goal name exists: pow -- needs ruling)
   52  ExprMulLabel                 -> times                UNATTESTED (attested goal name exists: times -- needs ruling)
   43  EdgesLabel                   -> edges                UNATTESTED (no attested counterpart)
   41  ExprAddLabel                 -> plus                 UNATTESTED (attested goal name exists: plus -- needs ruling)
   31  SolvedLabel                  -> solved               UNATTESTED (no attested counterpart)
   30  ExprEqLabel                  -> eq                   UNATTESTED (attested goal name exists: eq -- needs ruling)
   24  SecondEdgeLabel              -> second_edge          UNATTESTED (no attested counterpart)
   20  SideLengthsLabel             -> side_lengths         UNATTESTED (no attested counterpart)
   18  ExprNegLabel                 -> expr_neg             UNATTESTED (no attested counterpart)
   17  ExprFracLabel                -> expr_frac            UNATTESTED (no attested counterpart)
   15  TriangleLabel                -> triangle             UNATTESTED (no attested counterpart)
   14  AreaLabel                    -> area                 UNATTESTED (no attested counterpart)
   14  PerimeterThirdLabel          -> perimeter_third      UNATTESTED (no attested counterpart)
   14  APMiddleSideLabel            -> a_p_middle_side      UNATTESTED (no attested counterpart)
   13  SideOfLabel                  -> side_of              UNATTESTED (no attested counterpart)
   12  CommonDifferenceLabel        -> common_difference    UNATTESTED (no attested counterpart)
   12  APShortSideLabel             -> a_p_short_side       UNATTESTED (no attested counterpart)
   12  APLongSideLabel              -> a_p_long_side        UNATTESTED (no attested counterpart)
   11  SegmentLabel                 -> segment              UNATTESTED (no attested counterpart)
   11  APSideOffsetLabel            -> a_p_side_offset      UNATTESTED (no attested counterpart)
   10  FirstEdgeLabel               -> first_edge           UNATTESTED (no attested counterpart)
    9  ThirdEdgeLabel               -> third_edge           UNATTESTED (no attested counterpart)
    8  PositiveLabel                -> positive             UNATTESTED (no attested counterpart)
    7  CosineLabel                  -> cosine               UNATTESTED (no attested counterpart)
    6  ParameterLabel               -> parameter            UNATTESTED (no attested counterpart)
    6  AnglesLabel                  -> angles               UNATTESTED (no attested counterpart)
    6  DefinesLabel                 -> defines              UNATTESTED (no attested counterpart)
    5  ExprLtLabel                  -> expr_lt              UNATTESTED (no attested counterpart)
    5  PerimeterLabel               -> perimeter            UNATTESTED (no attested counterpart)
    5  APSideRadicandLabel          -> a_p_side_radicand    UNATTESTED (no attested counterpart)
    4  ThirdAngleLabel              -> third_angle          UNATTESTED (no attested counterpart)
    4  ArithmeticProgressionLabel   -> arithmetic_progression UNATTESTED (no attested counterpart)
    4  SqrtLabel                    -> sqrt                 CONFIRMED
    4  APAngleValueLabel            -> a_p_angle_value      UNATTESTED (no attested counterpart)
    3  NonNegativeLabel             -> non_negative         UNATTESTED (no attested counterpart)
    3  DistinctLabel                -> distinct             UNATTESTED (no attested counterpart)
    3  AngleLabel                   -> angle                UNATTESTED (no attested counterpart)
    3  ArccosLabel                  -> arccos               UNATTESTED (no attested counterpart)
    2  FractionLabel                -> fraction             UNATTESTED (no attested counterpart)
    2  EvaluateProblemLabel         -> evaluate_problem     UNATTESTED (no attested counterpart)
    2  AlgebraicApproachLabel       -> algebraic_approach   UNATTESTED (no attested counterpart)
    2  AngleOfLabel                 -> angle_of             UNATTESTED (no attested counterpart)
    2  OppositeLabel                -> opposite             UNATTESTED (no attested counterpart)
    2  VertexOfLabel                -> vertex_of            UNATTESTED (no attested counterpart)
    2  FirstAngleLabel              -> first_angle          UNATTESTED (no attested counterpart)
    2  SecondAngleLabel             -> second_angle         UNATTESTED (no attested counterpart)
    2  APAreaIdentityLabel          -> a_p_area_identity    UNATTESTED (no attested counterpart)
    1  SineLabel                    -> sine                 UNATTESTED (no attested counterpart)
    1  AngleMeasureLabel            -> angle_measure        UNATTESTED (no attested counterpart)
```

### number-theory.pack.yaml (8 rules)

```text
    8  DividesLabel                 -> divides              CONFIRMED
    1  EvenPropLabel                -> even_prop            UNATTESTED (no attested counterpart)
    1  ExprAddLabel                 -> plus                 UNATTESTED (attested goal name exists: plus -- needs ruling)
    1  ExprMulLabel                 -> times                UNATTESTED (attested goal name exists: times -- needs ruling)
    1  ModuloLabel                  -> modulo               UNATTESTED (no attested counterpart)
    1  GcdLabel                     -> gcd                  UNATTESTED (no attested counterpart)
```

### order-sign.pack.yaml (13 rules)

```text
   14  NonNegativeLabel             -> non_negative         UNATTESTED (no attested counterpart)
    8  PositiveLabel                -> positive             UNATTESTED (no attested counterpart)
    5  IsRealLabel                  -> is_real              UNATTESTED (no attested counterpart)
    4  SuccLabel                    -> succ                 UNATTESTED (no attested counterpart)
    2  FractionLabel                -> fraction             UNATTESTED (no attested counterpart)
    2  SqrtLabel                    -> sqrt                 CONFIRMED
    1  ExprPowLabel                 -> pow                  UNATTESTED (attested goal name exists: pow -- needs ruling)
    1  ExprAddLabel                 -> plus                 UNATTESTED (attested goal name exists: plus -- needs ruling)
    1  ExprMulLabel                 -> times                UNATTESTED (attested goal name exists: times -- needs ruling)
    1  ExprFracLabel                -> expr_frac            UNATTESTED (no attested counterpart)
```

### real-closure.pack.yaml (3 rules)

```text
   10  IsRealLabel                  -> is_real              UNATTESTED (no attested counterpart)
    2  ExprAddLabel                 -> plus                 UNATTESTED (attested goal name exists: plus -- needs ruling)
    2  ExprMulLabel                 -> times                UNATTESTED (attested goal name exists: times -- needs ruling)
```

### sequence-order.pack.yaml (11 rules)

```text
   28  ApplyLabel                   -> apply                UNATTESTED (no attested counterpart)
   11  ExprLtLabel                  -> expr_lt              UNATTESTED (no attested counterpart)
    9  SequenceLabel                -> sequence             UNATTESTED (no attested counterpart)
    9  SuccLabel                    -> succ                 UNATTESTED (no attested counterpart)
    6  LimitValueLabel              -> limit_value          UNATTESTED (no attested counterpart)
    4  ExprFracLabel                -> expr_frac            UNATTESTED (no attested counterpart)
    4  ConvergesLabel               -> converges            UNATTESTED (no attested counterpart)
    2  ExprEqLabel                  -> eq                   UNATTESTED (attested goal name exists: eq -- needs ruling)
    2  GapContractsLabel            -> gap_contracts        UNATTESTED (no attested counterpart)
    2  DecreasingLabel              -> decreasing           UNATTESTED (no attested counterpart)
    2  ExprAddLabel                 -> plus                 UNATTESTED (attested goal name exists: plus -- needs ruling)
    2  IncreasingLabel              -> increasing           UNATTESTED (no attested counterpart)
    2  ExprMulLabel                 -> times                UNATTESTED (attested goal name exists: times -- needs ruling)
    2  BoundedBelowLabel            -> bounded_below        UNATTESTED (no attested counterpart)
    2  BoundedAboveLabel            -> bounded_above        UNATTESTED (no attested counterpart)
```

### sqrt-real.pack.yaml (9 rules)

```text
    4  SqrtSeqTermLabel             -> sqrt_seq_term        UNATTESTED (no attested counterpart)
    2  SqrtLabel                    -> sqrt                 CONFIRMED
    2  NewtonStepTermLabel          -> newton_step_term     UNATTESTED (no attested counterpart)
    2  NewtonPositiveLabel          -> newton_positive      UNATTESTED (no attested counterpart)
    2  NewtonErrorIdentityLabel     -> newton_error_identity UNATTESTED (no attested counterpart)
    2  NewtonErrorShrinksLabel      -> newton_error_shrinks UNATTESTED (no attested counterpart)
    2  SqrtSeqCauchyLabel           -> sqrt_seq_cauchy      UNATTESTED (no attested counterpart)
    2  IsCauchyLabel                -> is_cauchy            UNATTESTED (no attested counterpart)
    2  RealNumLabel                 -> real_num             UNATTESTED (no attested counterpart)
    1  IsRealLabel                  -> is_real              UNATTESTED (no attested counterpart)
```

### trigonometry.pack.yaml (3 rules)

```text
    7  LengthLabel                  -> length               UNATTESTED (no attested counterpart)
    5  ExprMulLabel                 -> times                UNATTESTED (attested goal name exists: times -- needs ruling)
    4  EdgesLabel                   -> edges                UNATTESTED (no attested counterpart)
    3  ExprPowLabel                 -> pow                  UNATTESTED (attested goal name exists: pow -- needs ruling)
    3  SideOfLabel                  -> side_of              UNATTESTED (no attested counterpart)
    3  DistinctLabel                -> distinct             UNATTESTED (no attested counterpart)
    2  ExprEqLabel                  -> eq                   UNATTESTED (attested goal name exists: eq -- needs ruling)
    2  FirstEdgeLabel               -> first_edge           UNATTESTED (no attested counterpart)
    2  SineLabel                    -> sine                 UNATTESTED (no attested counterpart)
    2  SecondAngleLabel             -> second_angle         UNATTESTED (no attested counterpart)
    2  SecondEdgeLabel              -> second_edge          UNATTESTED (no attested counterpart)
    2  FirstAngleLabel              -> first_angle          UNATTESTED (no attested counterpart)
    2  TriangleLabel                -> triangle             UNATTESTED (no attested counterpart)
    2  CosineRuleRelatesLabel       -> cosine_rule_relates  UNATTESTED (no attested counterpart)
    2  ExprAddLabel                 -> plus                 UNATTESTED (attested goal name exists: plus -- needs ruling)
    1  SolvedLabel                  -> solved               UNATTESTED (no attested counterpart)
    1  ExprNegLabel                 -> expr_neg             UNATTESTED (no attested counterpart)
    1  CosineLabel                  -> cosine               UNATTESTED (no attested counterpart)
    1  AngleOfLabel                 -> angle_of             UNATTESTED (no attested counterpart)
    1  AngleMeasureLabel            -> angle_measure        UNATTESTED (no attested counterpart)
    1  OppositeLabel                -> opposite             UNATTESTED (no attested counterpart)
```

## Recommendation

Port **`number-theory`** first.

```text
  surface:
    DividesLabel: divides
```

Why this one:

- its one domain head, `DividesLabel`, is CONFIRMED against the goal
  vocabulary (11 `divides` uses in logged goals)
- it is the domain the D11 spike and the gate already exercise, so
  before/after reachability can be measured with `tools/d11_gate.py`
  without new tooling
- it is small (8 rules), so the first semantic cut is reviewable

Then rule per-symbol on the arithmetic family before any pack that uses
`Expr*Label` is ported. That is a separate decision and a separate commit.
