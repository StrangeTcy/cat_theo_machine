from __future__ import annotations

"""Proof provenance, evaluation mode, and failure honesty.

Every success the machine reports can be produced by more than one
mechanism -- a prewritten rule ladder, a stored derivation looked back
up, a replayed schema, or a search that actually expanded states. A
report of "yes" that does not say which is a report that cannot be
audited. Each proof attempt appends one ProvenanceRecord, Pair(tag,
Pair(subject, Pair(witness, EmptyList))), to the graph's provenance
chain.

The tags are machine atoms:

    Axiom                    an asserted fact
    LibraryRule              an ordinary schematic law from a
                             non-ladder pack
    PrewrittenProofLadder    a rule chain authored edge-by-edge for
                             one theorem (the sqrt-real Newton ladder,
                             the engel parity/invariant ladders)
    DerivationCacheHit       lookup_derivation returned a stored
                             proof; no search performed
    SchemaReplay             a stored derivation schema instantiated
    SearchDerived            a search expanded states and reached the
                             goal with no shortcut in the way
    InventedLemmaReplay      a previously approved invented lemma
    InventedLemmaDiscovery   a candidate generated, validated, and
                             approved this run
    Counterexample           a bounded positive-integer grid
                             witnessed the claim fail
    Failure                  no derivation

Evaluation mode (a graph host flag, set like the search console flags)
forbids the derivation cache, stored comparisons, schema replay, the
failure memo, and ladder packs at boot. The only remaining routes are
axioms/library rules and fresh search expansion.

The positive-integer grid check samples polynomial inequality goals on
a bounded a,b grid. A grid hit is a Counterexample over the positive
integers -- the domain of these powers -- and a grid miss is reported
as a capability gap, never as a false statement. Rationals are never
sampled.
"""

import gmpy2

from .core import (
    Char,
    Edge,
    EmptyList,
    Head,
    IdentityCompare,
    Pair,
    Tail,
    Zero,
    false_value,
    truth_value,
)
from .machine import AndAtom, IsPair, NotAtom, OrAtom, PrettyTerm, TreeInsert, TreeLookup, Tree
from .gmprep import GMPRep, GMPRepText
from .labels import (
    ExprAddLabel,
    ExprFracLabel,
    ExprLtLabel,
    ExprMulLabel,
    ExprNegLabel,
    ExprPowLabel,
    NonNegativeLabel,
)


AxiomTag = Char("Axiom")
LibraryRuleTag = Char("LibraryRule")
PrewrittenProofLadderTag = Char("PrewrittenProofLadder")
DerivationCacheHitTag = Char("DerivationCacheHit")
SchemaReplayTag = Char("SchemaReplay")
SearchDerivedTag = Char("SearchDerived")
InventedLemmaReplayTag = Char("InventedLemmaReplay")
InventedLemmaDiscoveryTag = Char("InventedLemmaDiscovery")
CounterexampleTag = Char("Counterexample")
FailureTag = Char("Failure")


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class ProvenanceRecord(Edge):
    """One audited attempt: Pair(tag, Pair(subject, Pair(witness, EmptyList))).

    `witness` is machine evidence for the tag: a search cost term for
    SearchDerived (expanded count), an assignment witness chain for
    Counterexample, a grid bound for a grid-miss Failure, EmptyList
    otherwise.
    """

    def __init__(self, tag, subject, witness):
        self.result = Pair(tag, Pair(subject, Pair(witness, EmptyList)))
        super().__init__(inputs=Pair(tag, Pair(subject, Pair(witness, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class ProvenanceRecordTag(Edge):
    def __init__(self, record):
        self.result = Head(record)()
        super().__init__(inputs=Pair(record, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProvenanceRecordSubject(Edge):
    def __init__(self, record):
        self.result = Head(Tail(record)())()
        super().__init__(inputs=Pair(record, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProvenanceRecordWitness(Edge):
    def __init__(self, record):
        self.result = Head(Tail(Tail(record)())())()
        super().__init__(inputs=Pair(record, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RecordProvenance(Edge):
    """Pair(record, chain): the record consed onto the graph's chain."""

    def __init__(self, graph, tag, subject, witness):
        chain = graph._proof_provenance
        record = ProvenanceRecord(tag, subject, witness)()
        self.result = Pair(record, chain)
        super().__init__(inputs=Pair(tag, Pair(subject, Pair(witness, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class ProvenanceChain(Edge):
    def __init__(self, graph):
        self.result = graph._proof_provenance
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ProvenanceCountTag(Edge):
    """How many records on the chain carry this exact tag, as a GMPRep."""

    def __init__(self, chain, tag):
        self.result = self._count(chain, tag, gmpy2.mpz(0))
        super().__init__(inputs=Pair(chain, Pair(tag, EmptyList)), results=self.result)

    def _count(self, chain, tag, total):
        if IdentityCompare(chain, EmptyList)() is truth_value:
            return GMPRep(str(total))
        record = Head(chain)()
        if IdentityCompare(ProvenanceRecordTag(record)(), tag)() is truth_value:
            return self._count(Tail(chain)(), tag, total + gmpy2.mpz(1))
        return self._count(Tail(chain)(), tag, total)

    def __call__(self):
        return self.result


class LatestProvenanceRecord(Edge):
    """The most recent record whose tag matches; EmptyList if none."""

    def __init__(self, chain, tag):
        self.result = self._latest(chain, tag)
        super().__init__(inputs=Pair(chain, Pair(tag, EmptyList)), results=self.result)

    def _latest(self, chain, tag):
        if IdentityCompare(chain, EmptyList)() is truth_value:
            return EmptyList
        record = Head(chain)()
        if IdentityCompare(ProvenanceRecordTag(record)(), tag)() is truth_value:
            return record
        return self._latest(Tail(chain)(), tag)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Evaluation mode
# ---------------------------------------------------------------------------


class EvaluationMode(Edge):
    """Read the graph's evaluation flag; ordinary mode is the default."""

    def __init__(self, graph):
        self.result = graph._proof_evaluation_mode
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SetEvaluationMode(Edge):
    """Set the graph's evaluation flag, returning the flag set."""

    def __init__(self, graph, flag):
        graph._proof_evaluation_mode = flag
        self.result = flag
        super().__init__(inputs=Pair(flag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


# The packs whose rules are theorem-specific proof ladders, authored
# edge-by-edge for one result. They load as ordinary library content in
# normal mode, and are dropped entirely from an evaluation boot.
_LADDER_PACK_NAMES = Pair(
    Char("sqrt-real"),
    Pair(
        Char("engel-coins"),
        Pair(
            Char("engel-means"),
            Pair(Char("engel-blackboard"), EmptyList),
        ),
    ),
)


class LadderPackNames(Edge):
    """The machine chain of Char names for the proof-ladder packs."""

    def __init__(self):
        self.result = _LADDER_PACK_NAMES
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        return self.result


class LadderPackNameChainText(Edge):
    """The ladder pack names rendered as host text for audit output."""

    def __init__(self, names):
        self.result = self._join(names)
        super().__init__(inputs=Pair(names, EmptyList), results=self.result)

    def _join(self, names):
        if IdentityCompare(names, EmptyList)() is truth_value:
            return ""
        name = Head(names)()()
        rest = Tail(names)()
        if IdentityCompare(rest, EmptyList)() is truth_value:
            return name
        return name + ", " + self._join(rest)

    def __call__(self):
        return self.result


class IsLadderPackName(Edge):
    """True when a Char atom names a proof-ladder pack."""

    def __init__(self, name):
        self.result = self._matches(name(), _LADDER_PACK_NAMES)
        super().__init__(inputs=Pair(name, EmptyList), results=self.result)

    def _matches(self, name_text, names):
        if IdentityCompare(names, EmptyList)() is truth_value:
            return false_value
        if Head(names)()() == name_text:
            return truth_value
        return self._matches(name_text, Tail(names)())

    def __call__(self):
        return self.result


class EvaluationPackPaths(Edge):
    """The boot path tuple with ladder packs dropped.

    Filesystem paths are host boundary text; the keep/drop decision for
    each is the machine edge IsLadderPackName over the pack's stem.
    """

    def __init__(self, paths):
        self.result = self._filter(paths, 0, ())
        super().__init__(inputs=EmptyList, results=self.result)

    def _filter(self, paths, index, kept):
        try:
            path = paths[index]
        except IndexError:
            return kept
        import os

        name = os.path.basename(path)
        name = self._strip_pack_suffix(name)
        if IsLadderPackName(Char(name))() is truth_value:
            return self._filter(paths, index + 1, kept)
        return self._filter(paths, index + 1, kept + (path,))

    def _strip_pack_suffix(self, name):
        dot_pack_yaml = ".pack.yaml"
        dot_yaml = ".yaml"
        dot_pack = ".pack"
        if name.endswith(dot_pack_yaml):
            return name[:-10]
        if name.endswith(dot_pack):
            return name[:-5]
        if name.endswith(dot_yaml):
            return name[:-5]
        return name

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Positive-integer grid counterexample check
# ---------------------------------------------------------------------------


class GridBindingValue(Edge):
    """The host integer bound to a variable Char in a witness chain.

    Bindings are Pair(Char("a"), Pair(value, Pair(Char("b"),
    Pair(value, EmptyList)))).
    """

    def __init__(self, var, bindings):
        self.result = self._binding(var, bindings)
        super().__init__(inputs=Pair(var, Pair(bindings, EmptyList)), results=self.result)

    def _binding(self, var, bindings):
        if IdentityCompare(bindings, EmptyList)() is truth_value:
            return EmptyList
        name = Head(bindings)()
        value = Head(Tail(bindings)())()
        rest = Tail(Tail(bindings)())()
        if name() == var():
            return value
        return self._binding(var, rest)

    def __call__(self):
        return self.result


class GridAssignmentWitness(Edge):
    """The binding chain for one positive-integer grid point."""

    def __init__(self, a_value, b_value):
        self.result = Pair(
            Char("a"),
            Pair(
                gmpy2.mpz(a_value),
                Pair(Char("b"), Pair(gmpy2.mpz(b_value), EmptyList)),
            ),
        )
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        return self.result


class WitnessValueA(Edge):
    def __init__(self, witness):
        # Pair(Char("a"), Pair(mpz_a, Pair(Char("b"), Pair(mpz_b, EmptyList))))
        self.result = Head(Tail(witness)())()
        super().__init__(inputs=Pair(witness, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class WitnessValueB(Edge):
    def __init__(self, witness):
        # witness = Pair(Char a, Pair(mpz a, Pair(Char b, Pair(mpz b, E))))
        self.result = Head(Tail(Tail(Tail(witness)())())())()
        super().__init__(inputs=Pair(witness, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GridEvalTerm(Edge):
    """Evaluate an a,b-polynomial term at one positive-integer binding.

    Returns an mpz value, or the EmptyList sentinel when the term is
    not evaluable on this check (fractions, leaves other than the
    bound variables, exponents that are not machine nats).
    """

    def __init__(self, term, bindings):
        self.result = self._eval(term, bindings)
        super().__init__(inputs=Pair(term, Pair(bindings, EmptyList)), results=self.result)

    def _eval(self, term, bindings):
        is_pair = IsPair(term)()
        if is_pair is truth_value:
            return self._eval_compound(term, bindings)
        return self._leaf(term, bindings)

    def _eval_compound(self, term, bindings):
        head = Head(term)()
        args = Tail(term)()
        left_term = Head(args)()
        # args is Pair(arg1, Pair(arg2, EmptyList)); the second arg is the
        # head of that second cell.
        right_term = Head(Tail(args)())

        if IdentityCompare(head, ExprAddLabel)() is truth_value:
            left = self._eval(left_term, bindings)
            right = self._eval(right_term, bindings)
            if left is EmptyList or right is EmptyList:
                return EmptyList
            return left + right

        if IdentityCompare(head, ExprMulLabel)() is truth_value:
            left = self._eval(left_term, bindings)
            right = self._eval(right_term, bindings)
            if left is EmptyList or right is EmptyList:
                return EmptyList
            return left * right

        if IdentityCompare(head, ExprNegLabel)() is truth_value:
            inner = self._eval(left_term, bindings)
            if inner is EmptyList:
                return EmptyList
            return -inner

        if IdentityCompare(head, ExprPowLabel)() is truth_value:
            base = self._eval(left_term, bindings)
            exponent = self._exponent(right_term)
            if base is EmptyList or exponent is EmptyList:
                return EmptyList
            return base ** exponent

        if IdentityCompare(head, ExprFracLabel)() is truth_value:
            return EmptyList

        return EmptyList

    def _exponent(self, exponent_term):
        from . import constructors as Cmod
        from .math.peano import NatRepOf

        rep = NatRepOf(exponent_term, Cmod.AllConstructors)()
        if IdentityCompare(rep, EmptyList)() is truth_value:
            return EmptyList
        try:
            power = int(str(rep()))
        except Exception:
            return EmptyList
        if power < 0:
            return EmptyList
        return power

    def _leaf(self, term, bindings):
        try:
            symbol = term()
        except Exception:
            return EmptyList
        if symbol == "a":
            value = GridBindingValue(Char("a"), bindings)()
            return value
        if symbol == "b":
            value = GridBindingValue(Char("b"), bindings)()
            return value
        return EmptyList

    def __call__(self):
        return self.result


class GridGoalPolynomial(Edge):
    """The polynomial of an inequality goal, or EmptyList.

    Understands NonNegative(poly) (poly >= 0) and ExprLt(Zero, poly)
    (0 < poly).
    """

    def __init__(self, goal):
        is_pair = IsPair(goal)()
        if is_pair is truth_value:
            head = Head(goal)()
            args = Tail(goal)()
            if IdentityCompare(head, NonNegativeLabel)() is truth_value:
                self.result = Head(args)()
            else:
                is_less = IdentityCompare(head, ExprLtLabel)()
                if is_less is truth_value:
                    left = Head(args)()
                    right = Head(Tail(args)())()
                    left_is_zero = IdentityCompare(left, Zero)()
                    if left_is_zero is truth_value:
                        self.result = right
                    else:
                        self.result = EmptyList
                else:
                    self.result = EmptyList
        else:
            self.result = EmptyList
        super().__init__(inputs=Pair(goal, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialCounterexampleGrid(Edge):
    """Scan a bounded positive-integer grid for a counterexample.

    Result is EmptyList when the goal is not an evaluable a,b
    polynomial; otherwise Pair(found, payload):
      Pair(truth_value, witness)  -- counterexample at that assignment
      Pair(false_value, GMPRep)   -- no counterexample in 1..grid_max
    """

    def __init__(self, goal, grid_max=5):
        self.grid_max = grid_max
        self.polynomial = GridGoalPolynomial(goal)()
        if IdentityCompare(self.polynomial, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            self.goal_head = Head(goal)()
            self.result = self._scan(1, 1)
        super().__init__(inputs=Pair(goal, EmptyList), results=self.result)

    def _violates(self, value):
        from .labels import NonNegativeLabel, ExprLtLabel

        if IdentityCompare(self.goal_head, NonNegativeLabel)() is truth_value:
            return value < 0
        if IdentityCompare(self.goal_head, ExprLtLabel)() is truth_value:
            return value <= 0
        return False

    def _scan(self, a_value, b_value):
        witness = GridAssignmentWitness(a_value, b_value)()
        value = GridEvalTerm(self.polynomial, witness)()
        if value is not EmptyList:
            if self._violates(value):
                return Pair(truth_value, witness)
        if b_value < self.grid_max:
            return self._scan(a_value, b_value + 1)
        if a_value < self.grid_max:
            return self._scan(a_value + 1, 1)
        return Pair(false_value, GMPRep(str(self.grid_max)))

    def __call__(self):
        return self.result


class GridCounterexampleText(Edge):
    """The human report for a grid Pair(found, payload) result."""

    def __init__(self, grid_result):
        if IdentityCompare(grid_result, EmptyList)() is truth_value:
            self.result = EmptyList
        else:
            found = Head(grid_result)()
            # grid_result is Pair(found, payload); the payload is the tail.
            payload = Tail(grid_result)()
            if found is truth_value:
                self.result = (
                    "no; bounded positive-integer counterexample found: a = "
                    + str(WitnessValueA(payload)())
                    + ", b = "
                    + str(WitnessValueB(payload)())
                    + ". The claim fails on the positive integers; no lemma "
                    + "invention was attempted."
                )
            else:
                grid_text = str(payload())
                self.result = (
                    "no; no counterexample in the positive-integer grid 1.."
                    + grid_text
                    + " x 1.."
                    + grid_text
                    + ". The statement may be true; the engine has no rule "
                    + "chain that proves it (capability gap, not a false "
                    + "statement)."
                )
        super().__init__(inputs=Pair(grid_result, EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Provenance summary
# ---------------------------------------------------------------------------


_SUMMARY_ROWS = Pair(
    Pair(SearchDerivedTag, Char("search-derived proofs")),
    Pair(
        Pair(InventedLemmaDiscoveryTag, Char("invented lemmas")),
        Pair(
            Pair(InventedLemmaReplayTag, Char("invented lemma replays")),
            Pair(
                Pair(SchemaReplayTag, Char("schema replays")),
                Pair(
                    Pair(DerivationCacheHitTag, Char("cache hits")),
                    Pair(
                        Pair(PrewrittenProofLadderTag, Char("prewritten ladder uses")),
                        Pair(
                            Pair(LibraryRuleTag, Char("library rule uses")),
                            Pair(
                                Pair(AxiomTag, Char("axiom uses")),
                                Pair(
                                    Pair(CounterexampleTag, Char("counterexamples found")),
                                    Pair(
                                        Pair(FailureTag, Char("failures")),
                                        EmptyList,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
)


class ProvenanceSummaryText(Edge):
    """The end-of-transcript tally, one machine-counted line per tag."""

    def __init__(self, graph):
        chain = ProvenanceChain(graph)()
        self.result = "=== PROVENANCE SUMMARY ===" + self._rows(_SUMMARY_ROWS, chain)
        super().__init__(inputs=EmptyList, results=self.result)

    def _rows(self, rows, chain):
        if IdentityCompare(rows, EmptyList)() is truth_value:
            return ""
        row = Head(rows)()
        tag = Head(row)()
        label = Tail(row)()
        count = ProvenanceCountTag(chain, tag)()
        line = "\n" + label() + ": " + str(count())
        return line + self._rows(Tail(rows)(), chain)

    def __call__(self):
        return self.result



PrimitiveTag = Char("primitive")
TaughtTag = Char("taught")
LearnedTag = Char("learned")
EpisodicCacheTag = Char("episodic-cache")
DemoSpecializedTag = Char("demo-specialized")


_ORIGIN_TAGS = Pair(
    PrimitiveTag,
    Pair(TaughtTag, Pair(LearnedTag, Pair(EpisodicCacheTag, Pair(DemoSpecializedTag, EmptyList)))),
)


class IsRuleOrigin(Edge):
    """True when a tag is one of the five rule origin labels."""

    def __init__(self, tag):
        self.result = self._is(tag, _ORIGIN_TAGS)
        super().__init__(inputs=Pair(tag, EmptyList), results=self.result)

    def _is(self, tag, tags):
        if IdentityCompare(tags, EmptyList)() is truth_value:
            return false_value
        if IdentityCompare(Head(tags)(), tag)() is truth_value:
            return truth_value
        return self._is(tag, Tail(tags)())

    def __call__(self):
        return self.result


class RuleOriginTreeEmpty(Edge):
    """A fresh empty association chain Pair(rule, Pair(origin, rest))..."""

    def __init__(self):
        self.result = EmptyList
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        return self.result


class TagRuleOrigin(Edge):
    """Record Pair(rule, origin) at the front of the association chain."""

    def __init__(self, chain, rule, origin, registry=None):
        self.result = Pair(Pair(rule, Pair(origin, EmptyList)), chain)
        super().__init__(inputs=Pair(rule, Pair(origin, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class LookupRuleOrigin(Edge):
    """The origin recorded for a rule (identity match); PrimitiveTag if none.

    An un-tagged rule defaults to PrimitiveTag: the safe admissible
    origin, so generic library laws are usable in cold-learning mode
    unless explicitly quarantined as demo-specialized.
    """

    def __init__(self, chain, rule, registry=None):
        self.result = self._lookup(chain, rule)
        super().__init__(inputs=Pair(rule, EmptyList), results=self.result)

    def _lookup(self, chain, rule):
        if IdentityCompare(chain, EmptyList)() is truth_value:
            return PrimitiveTag
        entry = Head(chain)()
        stored_rule = Head(entry)()
        if IdentityCompare(stored_rule, rule)() is truth_value:
            return Head(Tail(entry)())()
        return self._lookup(Tail(chain)(), rule)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Proof policy
# ---------------------------------------------------------------------------

# The six policy slots, in fixed order, each a truth/false atom.
class ProofPolicy(Edge):
    """Pair-native policy record.

    Pair(allow_exact_cache,
      Pair(allow_search_comparison,
        Pair(allow_schema_replay,
          Pair(allow_taught_rules,
            Pair(allow_demo_specialized_rules,
              Pair(record_proof_provenance, EmptyList))))))
    """

    def __init__(
        self,
        allow_exact_cache,
        allow_search_comparison,
        allow_schema_replay,
        allow_taught_rules,
        allow_demo_specialized_rules,
        record_proof_provenance,
    ):
        self.result = Pair(
            allow_exact_cache,
            Pair(
                allow_search_comparison,
                Pair(
                    allow_schema_replay,
                    Pair(
                        allow_taught_rules,
                        Pair(allow_demo_specialized_rules, Pair(record_proof_provenance, EmptyList)),
                    ),
                ),
            ),
        )
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PolicyAllowExactCache(Edge):
    def __init__(self, policy):
        self.result = Head(policy)()
        super().__init__(inputs=Pair(policy, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolicyAllowSearchComparison(Edge):
    def __init__(self, policy):
        self.result = Head(Tail(policy)())()
        super().__init__(inputs=Pair(policy, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolicyAllowSchemaReplay(Edge):
    def __init__(self, policy):
        self.result = Head(Tail(Tail(policy)())())()
        super().__init__(inputs=Pair(policy, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolicyAllowTaughtRules(Edge):
    def __init__(self, policy):
        self.result = Head(Tail(Tail(Tail(policy)())())())()
        super().__init__(inputs=Pair(policy, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolicyAllowDemoSpecializedRules(Edge):
    def __init__(self, policy):
        self.result = Head(Tail(Tail(Tail(Tail(policy)())())())())()
        super().__init__(inputs=Pair(policy, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolicyRecordProvenance(Edge):
    def __init__(self, policy):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(policy)())())())())())()
        super().__init__(inputs=Pair(policy, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DefaultProofPolicy(Edge):
    """Every convenience admissible: normal operation."""

    def __init__(self):
        self.result = ProofPolicy(
            truth_value, truth_value, truth_value,
            truth_value, truth_value, truth_value,
        )()
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ColdLearningPolicy(Edge):
    """The learning-transfer policy.

    Exact derivation cache, stored search comparisons, and schema replay
    are forbidden (retrieval cannot count as learning); demo-specialized
    ladders are forbidden; taught and (validated) learned rules and
    provenance recording are on.
    """

    def __init__(self):
        self.result = ProofPolicy(
            false_value, false_value, false_value,
            truth_value, false_value, truth_value,
        )()
        super().__init__(inputs=EmptyList, results=self.result)

    def __call__(self):
        return self.result


# Origins a cold-learning proof may use.
_ADMISSIBLE_ORIGINS = Pair(
    PrimitiveTag,
    Pair(TaughtTag, Pair(LearnedTag, EmptyList)),
)


class OriginAdmissible(Edge):
    """True when an origin is permitted in cold-learning mode."""

    def __init__(self, origin):
        self.result = self._admissible(origin, _ADMISSIBLE_ORIGINS)
        super().__init__(inputs=Pair(origin, EmptyList), results=self.result)

    def _admissible(self, origin, origins):
        if IdentityCompare(origins, EmptyList)() is truth_value:
            return false_value
        if IdentityCompare(Head(origins)(), origin)() is truth_value:
            return truth_value
        return self._admissible(origin, Tail(origins)())

    def __call__(self):
        return self.result


class FilterRulesByPolicy(Edge):
    """Keep only rules whose origin the policy admits.

    Walks the compiled/raw rule chain; looks up each rule's origin in the
    graph index; drops demo-specialized rules when the policy forbids
    them. Returns the filtered chain in the same order.
    """

    def __init__(self, rules, origin_tree, policy, registry):
        self.result = self._filter(rules, origin_tree, policy, registry)
        super().__init__(inputs=Pair(rules, Pair(policy, EmptyList)), results=self.result)

    def _filter(self, rules, origin_tree, policy, registry):
        if IdentityCompare(rules, EmptyList)() is truth_value:
            return EmptyList
        rule = Head(rules)()
        raw_rule = self._raw(rule)
        origin = LookupRuleOrigin(origin_tree, raw_rule, registry)()
        # Drop this rule when its origin is one the policy forbids. Each
        # exclusion is a machine conjunction of (origin matches) and
        # (policy switch is off); the overall keep is their negation.
        demo_switch_off = NotAtom(PolicyAllowDemoSpecializedRules(policy)())()
        taught_switch_off = NotAtom(PolicyAllowTaughtRules(policy)())()
        demo_forbidden = AndAtom(
            IdentityCompare(origin, DemoSpecializedTag)(), demo_switch_off)()
        taught_forbidden = AndAtom(
            IdentityCompare(origin, TaughtTag)(), taught_switch_off)()
        drop = OrAtom(demo_forbidden, taught_forbidden)()
        rest = self._filter(Tail(rules)(), origin_tree, policy, registry)
        if drop is truth_value:
            return rest
        return Pair(rule, rest)

    def _raw(self, compiled_rule):
        # A compiled rule wraps its raw rule; a plain rule is itself.
        from .proof import CompiledRuleRaw

        try:
            raw = CompiledRuleRaw(compiled_rule)()
            if IdentityCompare(raw, EmptyList)() is truth_value:
                return compiled_rule
            return raw
        except Exception:
            return compiled_rule

    def __call__(self):
        return self.result


class CountChain(Edge):
    """Machine count of a chain, returned as a GMPRep integer atom."""

    def __init__(self, chain):
        self.result = self._count(chain, gmpy2.mpz(0))
        super().__init__(inputs=Pair(chain, EmptyList), results=self.result)

    def _count(self, chain, total):
        if IdentityCompare(chain, EmptyList)() is truth_value:
            from .gmprep import GMPRep

            return GMPRep(str(total))
        return self._count(Tail(chain)(), total + gmpy2.mpz(1))

    def __call__(self):
        return self.result




def origin_tag_for_text(text):
    """Map a pack-declared origin string to its tag Char (host loader use).

    This is the loader boundary reading declared metadata; no pack name
    or theorem name appears here. Unknown text defaults to PrimitiveTag,
    the safe admissible origin.
    """

    if text == "taught":
        return TaughtTag
    if text == "learned":
        return LearnedTag
    if text == "episodic-cache":
        return EpisodicCacheTag
    if text == "demo-specialized":
        return DemoSpecializedTag
    return PrimitiveTag


# ---------------------------------------------------------------------------
# Proof audit: a pair-native record disclosing how a proof was obtained.
# Built from a finished search job plus the policy and origin index that
# governed it -- never by naming a theorem. The counts threaded through
# the record are machine Pair terms (Char -> Count GMPRep atoms).
# ---------------------------------------------------------------------------

def _zero_counts(tags, registry):
    from .machine import GMPRep

    if IdentityCompare(tags, EmptyList)() is truth_value:
        return EmptyList
    # Each entry: Pair(tag, Pair(count_atom, EmptyList)); the outer chain
    # conses entries. Read as tag at Head, count at Head(Tail).
    return Pair(
        Pair(Head(tags)(), Pair(GMPRep("0"), EmptyList)),
        _zero_counts(Tail(tags)(), registry),
    )


def _bump(origin, counts, tags):
    """Return counts with the slot equal to origin incremented by one.

    Identity compare over the five-tag chain; structurally equal counts
    otherwise. Returns a fresh chain (machine terms are immutable).
    """

    import gmpy2
    from .gmprep import GMPRep

    if IdentityCompare(tags, EmptyList)() is truth_value:
        return EmptyList
    entry = Head(counts)()
    tag = Head(entry)()
    value = Head(Tail(entry)())()
    if IdentityCompare(tag, origin)() is truth_value:
        bumped = gmpy2.mpz(value.value) + gmpy2.mpz(1)
        new_value = GMPRep(str(bumped))
        new_entry = Pair(tag, Pair(new_value, EmptyList))
        return Pair(new_entry, _bump(origin, Tail(counts)(), Tail(tags)()))
    return Pair(entry, _bump(origin, Tail(counts)(), Tail(tags)()))


def _tally_origins(rules, origin_chain, counts, tags, registry):
    """Walk the fired/admissible rule chain, tallying each origin."""

    if IdentityCompare(rules, EmptyList)() is truth_value:
        return counts
    rule = Head(rules)()
    raw_rule = rule
    from .proof import CompiledRuleRaw

    raw = CompiledRuleRaw(rule)()
    raw_nonempty = NotAtom(IdentityCompare(raw, EmptyList)())()
    if raw_nonempty is truth_value:
        raw_rule = raw
    origin = LookupRuleOrigin(origin_chain, raw_rule, registry)()
    next_counts = _bump(origin, counts, tags)
    return _tally_origins(Tail(rules)(), origin_chain, next_counts, tags, registry)


def _count_text(term, registry):
    """Render a search count term to text via the machine's own pretty edge.

    Count terms arrive as an Atom wrapping a GMPRep (or a machine numeral);
    PrettyTerm reduces either to its decimal text, so no host type-guessing
    is needed.
    """

    from .machine import PrettyTerm

    return PrettyTerm(term, registry)()


class BuildProofAudit(Edge):
    """Pair-native proof audit record.

    Inputs (machine):
        policy          active ProofPolicy
        origin_chain    graph rule-origin association chain
        fired_rules     rule chain that governed/closed the proof
        expanded        GMPRep count of states expanded
        generated       GMPRep count of states generated
        exact_cache_hit truth/false: solved by exact derivation retrieval
        comparison_hit  truth/false: solved by stored search comparison
        demo_used       truth/false: a demo-specialized rule fired
        success         truth/false: proof succeeded

    Result chain (all machine terms):
        Pair(success,
         Pair(exact_cache_hit,
          Pair(comparison_hit,
           Pair(schema_replay_hit,
            Pair(demo_used,
             Pair(origin_tally,
              Pair(expanded, Pair(generated, EmptyList))))))))
    """

    def __init__(self, policy, origin_chain, fired_rules, expanded, generated,
                 exact_cache_hit, comparison_hit, demo_used, success, registry):
        tally = _tally_origins(
            fired_rules, origin_chain,
            _zero_counts(_ORIGIN_TAGS, registry), _ORIGIN_TAGS, registry,
        )
        schema_hit = PolicyAllowSchemaReplay(policy)()
        # A cache/comparison hit cannot be recorded when the policy forbids
        # those paths: AND the reported hits with the policy switches, as
        # machine atoms.
        eff_exact = AndAtom(exact_cache_hit, PolicyAllowExactCache(policy)())()
        eff_compare = AndAtom(comparison_hit, PolicyAllowSearchComparison(policy)())()
        expanded_text = Char(_count_text(expanded, registry))
        generated_text = Char(_count_text(generated, registry))
        self.result = Pair(
            success,
            Pair(eff_exact,
                 Pair(eff_compare,
                      Pair(schema_hit,
                           Pair(demo_used,
                                Pair(tally,
                                     Pair(expanded_text, Pair(generated_text, EmptyList))))))),
        )
        super().__init__(inputs=Pair(fired_rules, Pair(policy, EmptyList)),
                         results=self.result)

    def __call__(self):
        return self.result


def _text_chain(chain, sep, registry):
    if IdentityCompare(chain, EmptyList)() is truth_value:
        return ""
    first = Head(chain)()
    rest = Tail(chain)()
    body = first
    rest_nonempty = NotAtom(IdentityCompare(rest, EmptyList)())()
    if rest_nonempty is truth_value:
        return body + sep + _text_chain(rest, sep, registry)
    return body


class ProofAuditText(Edge):
    """Render a ProofAudit record, distinguishing retrieval from search."""

    def __init__(self, audit, registry):
        self.result = self._render(audit, registry)
        super().__init__(inputs=Pair(audit, EmptyList), results=self.result)

    def _is_true(self, atom):
        return IdentityCompare(atom, truth_value)() is truth_value

    def _render(self, audit, registry):
        def slot(chain, depth):
            if depth == 0:
                return Head(chain)()
            return slot(Tail(chain)(), depth - 1)

        success = slot(audit, 0)
        exact = slot(audit, 1)
        compare = slot(audit, 2)
        schema = slot(audit, 3)
        demo = slot(audit, 4)
        tally = slot(audit, 5)
        expanded = slot(audit, 6)
        generated = slot(audit, 7)

        if self._is_true(exact):
            source = "Solved by exact episodic retrieval."
        elif self._is_true(compare):
            source = "Solved by stored search comparison (retrieval)."
        elif self._is_true(demo):
            source = "Solved by demo-specialized rule pack."
        elif self._is_true(success):
            source = "Solved by fresh search."
        else:
            source = "Not proved under the active policy."

        origin_parts = self._tally_text(tally)
        return (
            "proof-audit: " + source + "\n"
            + "  success:             " + ("yes" if self._is_true(success) else "no") + "\n"
            + "  exact-cache-hit:     " + ("yes" if self._is_true(exact) else "no") + "\n"
            + "  search-comparison:   " + ("yes" if self._is_true(compare) else "no") + "\n"
            + "  schema-replay:       " + ("yes" if self._is_true(schema) else "no") + "\n"
            + "  demo-rule-used:      " + ("yes" if self._is_true(demo) else "no") + "\n"
            + "  states-expanded:     " + self._num(expanded) + "\n"
            + "  states-generated:    " + self._num(generated) + "\n"
            + "  rules by origin:     " + origin_parts
        )

    def _num(self, atom):
        # GMPRep count atoms carry an mpz `.value`; other count terms are
        # read by applying them.
        value = atom.value if "value" in dir(atom) else None
        if value is not None:
            return str(value)
        try:
            return str(atom())
        except Exception:
            return str(atom)

    def _tally_text(self, tally):
        def walk(scan):
            if IdentityCompare(scan, EmptyList)() is truth_value:
                return ""
            entry = Head(scan)()
            tag = Head(entry)()
            count = Head(Tail(entry)())()
            piece = tag() + "=" + str(count.value)
            rest = walk(Tail(scan)())
            return piece if rest == "" else piece + " " + rest

        return walk(tally)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Proof-side residual transaction: domain-general candidate propositions.
#
# From a stalled NonNegative(poly) goal, enumerate sign propositions over
# the polynomial's additive leaves -- one general operator among those the
# learning instrument allows (it takes arbitrary terms and never dispatches
# on a theorem name or the goal's signature). Each candidate is a proposition
# to validate independently, never an asserted rule: a zero-premise target
# rule is inadmissible. Bounded by a machine count so the enumeration stays
# finite under uniform configuration.
# ---------------------------------------------------------------------------

from .labels import (
    ExprAddLabel as _AddLabel,
    ExprMulLabel as _MulLabel,
    ExprNegLabel as _NegLabel,
    ExprPowLabel as _PowLabel,
    PositiveLabel as _PositiveLabel,
    IsRealLabel as _IsRealLabel,
)


class SignLeafCandidates(Edge):
    """NonNegative(leaf) for each additive leaf of the goal polynomial.

    Walks the Add-spine of a NonNegative(term) fact; a negated leaf yields
    NonNegative(neg(term)) so the validator can refute it on the domain.
    Result: Pair(candidate_fact_chain, EmptyList).
    """

    def __init__(self, goal_fact, bound, registry):
        poly = GridGoalPolynomial(goal_fact)()
        leaves = _add_leaves(poly, EmptyList)
        self.result = Pair(_leaf_facts(leaves, EmptyList), EmptyList)
        super().__init__(inputs=Pair(goal_fact, Pair(bound, EmptyList)),
                         results=self.result)

    def __call__(self):
        return self.result


def _term_head(term):
    is_pair = IsPair(term)()
    if is_pair is truth_value:
        return Head(term)()
    return EmptyList


def _add_leaves(term, acc):
    head = _term_head(term)
    if IdentityCompare(head, _AddLabel)() is truth_value:
        args = Tail(term)()
        left = Head(args)()
        right = Head(Tail(args)())()
        return _add_leaves(left, _add_leaves(right, acc))
    return Pair(term, acc)


def _leaf_facts(leaves, acc):
    if IdentityCompare(leaves, EmptyList)() is truth_value:
        return acc
    leaf = Head(leaves)()
    fact = Pair(NonNegativeLabel, Pair(leaf, EmptyList))
    return _leaf_facts(Tail(leaves)(), Pair(fact, acc))


class CandidateVerdictText(Edge):
    """Human verdict for a candidate validation status char."""

    def __init__(self, verdict):
        mapping = Pair(
            Pair(Char("proved"), Char("proved (independently derived)")),
            Pair(
                Pair(Char("refuted"), Char("refuted (false on the domain)")),
                Pair(Pair(Char("unknown"), Char("unknown (not derived)")), EmptyList),
            ),
        )
        self.result = _lookup_verdict(mapping, verdict)
        super().__init__(inputs=Pair(verdict, EmptyList), results=self.result)

    def __call__(self):
        return self.result


def _lookup_verdict(mapping, verdict):
    if IdentityCompare(mapping, EmptyList)() is truth_value:
        return Char("unknown (not derived)")
    entry = Head(mapping)()
    if IdentityCompare(Head(entry)(), verdict)() is truth_value:
        return Head(Tail(entry)())()
    return _lookup_verdict(Tail(mapping)(), verdict)


# ---------------------------------------------------------------------------
# Promotion admission gates (learning instrument).
#
# A candidate artifact may be promoted to a 'learned' rule only when:
#   (5) it contains no empty-premise target assertion (no zero-premise rule);
#   (4) it contains no unjustified fresh variable (every variable in the
#       replacement is bound by a premise).
# These are structural checks over machine terms; they dispatch on no
# theorem name.
# ---------------------------------------------------------------------------

class TermVars(Edge):
    """The Char/Atom variables occurring in a term, as a machine chain.

    A Pair compound contributes the variables of its arguments; any Atom
    that is not a constructor Label (i.e. not a Pair) is a variable leaf.
    Deduped by identity comparison.
    """

    def __init__(self, term):
        self.result = self._vars(term, EmptyList)
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def _vars(self, term, acc):
        is_pair = IsPair(term)()
        if is_pair is truth_value:
            return self._vars_args(Tail(term)(), acc)
        return _chain_adjoin(term, acc)

    def _vars_args(self, args, acc):
        empty = IdentityCompare(args, EmptyList)()
        if empty is truth_value:
            return acc
        head = Head(args)()
        acc2 = self._vars(head, acc)
        return self._vars_args(Tail(args)(), acc2)

    def __call__(self):
        return self.result


def _chain_adjoin(item, chain):
    present = _chain_contains(item, chain)
    if present is truth_value:
        return chain
    return Pair(item, chain)


def _chain_contains(item, chain):
    empty = IdentityCompare(chain, EmptyList)()
    if empty is truth_value:
        return false_value
    same = IdentityCompare(Head(chain)(), item)()
    if same is truth_value:
        return truth_value
    return _chain_contains(item, Tail(chain)())


def _chain_vars(chain, acc):
    """Union of TermVars over every fact in a fact chain."""
    empty = IdentityCompare(chain, EmptyList)()
    if empty is truth_value:
        return acc
    head = Head(chain)()
    acc2 = TermVars(head)()
    acc3 = _chain_union(acc2, acc)
    return _chain_vars(Tail(chain)(), acc3)


def _chain_union(chain, acc):
    empty = IdentityCompare(chain, EmptyList)()
    if empty is truth_value:
        return acc
    return _chain_union(Tail(chain)(), _chain_adjoin(Head(chain)(), acc))


def _chain_subset(small, big):
    """Truth iff every element of small is in big."""
    empty = IdentityCompare(small, EmptyList)()
    if empty is truth_value:
        return truth_value
    present = _chain_contains(Head(small)(), big)
    if present is false_value:
        return false_value
    return _chain_subset(Tail(small)(), big)


class RuleHasNoEmptyPremise(Edge):
    """False only for a zero-premise rule asserting its replacement outright."""

    def __init__(self, rule):
        from .proof import RulePremises

        premises = RulePremises(rule)()
        empty = IdentityCompare(premises, EmptyList)()
        if empty is truth_value:
            self.result = false_value
        else:
            self.result = truth_value
        super().__init__(inputs=Pair(rule, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleVarsAdmissible(Edge):
    """Truth iff every replacement variable is bound among the premises."""

    def __init__(self, rule):
        from .proof import RulePremises, RuleReplacement

        premises = RulePremises(rule)()
        replacement = RuleReplacement(rule)()
        premise_vars = _chain_vars(premises, EmptyList)
        replacement_vars = TermVars(replacement)()
        self.result = _chain_subset(replacement_vars, premise_vars)
        super().__init__(inputs=Pair(rule, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PromotionAdmissible(Edge):
    """The structural admission gate for a 'learned' candidate rule.

    Both the no-empty-premise and the no-fresh-variable conditions must
    hold. The remaining gates (independent proof / replay certificate,
    positive/negative examples, reload revalidation) are supplied by the
    caller as truth atoms so the gate can combine machine results.
    """

    def __init__(self, rule, has_certificate, positive_transfer, negative_rejected):
        no_empty = RuleHasNoEmptyPremise(rule)()
        no_fresh = RuleVarsAdmissible(rule)()
        self.result = AndAtom(
            AndAtom(no_empty, no_fresh)(),
            AndAtom(
                AndAtom(has_certificate, positive_transfer)(),
                negative_rejected,
            )(),
        )()
        super().__init__(inputs=Pair(rule, Pair(has_certificate, EmptyList)),
                         results=self.result)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Counterfactual utility test (learning instrument, section 5C).
#
# Given the outcome of two identical searches (same rules, fuel, heuristic)
# -- baseline on the residual, augmented on residual + candidate L -- a
# candidate is useful only when it changes the result: success where the
# baseline failed, or a strictly lower expansion cost. Manufacturing a rule
# L -> goal is NOT tested here; the candidate is added as a premise/lemma and
# the goal search is rerun. This edge only combines machine outcome atoms.
# ---------------------------------------------------------------------------

def _gmp_lt(less_atom, greater_atom):
    """Truth atom: the GMPRep count ``less_atom`` is strictly below
    ``greater_atom``. Callers pass GMPRep count atoms (their ``.value`` is an
    mpz), the same arithmetic ``_bump`` uses; no host type inspection."""
    return truth_value if less_atom.value < greater_atom.value else false_value


class CounterfactualUtility(Edge):
    """Truth iff augmenting with the candidate is causally useful.

    Inputs (machine atoms):
        baseline_success, augmented_success : truth/false
        baseline_expanded,  augmented_expanded  : count terms
    Useful when augmented succeeds and baseline does not (the residual
    closed only with the candidate), or both succeed but the augmented
    search expanded strictly fewer states.
    """

    def __init__(self, baseline_success, augmented_success,
                 baseline_expanded, augmented_expanded):
        closes_residual = AndAtom(
            augmented_success, NotAtom(baseline_success)())()
        both_succeed = AndAtom(augmented_success, baseline_success)()
        cheaper = _gmp_lt(augmented_expanded, baseline_expanded)
        lowers_cost = AndAtom(both_succeed, cheaper)()
        self.result = OrAtom(closes_residual, lowers_cost)()
        super().__init__(
            inputs=Pair(augmented_success, Pair(baseline_success, EmptyList)),
            results=self.result)

    def __call__(self):
        return self.result
