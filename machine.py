from __future__ import annotations

from .core import (
    Atom,
    AtomSet,
    Char,
    COMMA,
    Diff,
    Edge,
    EdgeInputs,
    EdgeResults,
    EmptyList,
    EmptySet,
    Head,
    IdentityCompare,
    IdentityLess,
    InputOf,
    LBRACK,
    LPAREN,
    Member,
    Pair,
    RPAREN,
    RBRACK,
    Same,
    SPACE,
    Tail,
    Thingy,
    UniqueId,
    Var,
    VarTag,
    Zero,
)
from .logic import AndAtom, FalseAtom, NandAtom, NotAtom, OrAtom, TrueAtom, false_value, truth_value
from .gmprep import GMPRep, GMPRepText
from .labels import (
    AStarLabel,
    BFSLabel,
    BeamLabel,
    ConstructorLabel,
    DerivationLabel,
    DFSLabel,
    ExprAddLabel,
    ExprDivLabel,
    ExprEqLabel,
    ExprFracLabel,
    ExprIntLabel,
    ExprLtLabel,
    ExprMulLabel,
    ExprNegLabel,
    ExprPowLabel,
    ExactAtomKeyLabel,
    ExactCtorKeyLabel,
    ExactPairKeyLabel,
    IndexAtomKeyLabel,
    IndexCtorKeyLabel,
    IndexPairKeyLabel,
    FractionLabel,
    GoalHeadOrderLabel,
    HypergraphLabel,
    InsertionOrderLabel,
    IsCauchyLabel,
    IsRealLabel,
    KnowledgeLabel,
    LessonLabel,
    EntryLabel,
    GroundedExampleLabel,
    SourceLabel,
    SurfaceLabel,
    MathematicsLabel,
    HistoryLabel,
    ProblemLabel,
    HintLabel,
    UsesStrategyLabel,
    DerivationFragmentLabel,
    GoalLabel,
    ClaimsLabel,
    SupportsLabel,
    HistoricalContradictsLabel,
    OccursOnLabel,
    BeforeLabel,
    CausesLabel,
    ParticipatesInLabel,
    OccursAtLabel,
    ClaimStoreLabel,
    CorrespondenceLawLabel,
    LimitLabel,
    MachineContextLabel,
    ContextConstructorsLabel,
    ContextNodesLabel,
    ContextEdgesLabel,
    ContextTestsLabel,
    ContextTestResultsLabel,
    ContextAllRulesLabel,
    ContextNextRuleIndexLabel,
    ContextRuleOrderLabel,
    ContextDerivationsLabel,
    ContextDerivationSchemataLabel,
    ContextSearchHistoryLabel,
    ContextSearchComparisonsLabel,
    ContextSearchJobsLabel,
    ContextSearchMemoLabel,
    ProofCostLabel,
    NewtonErrorIdentityLabel,
    NewtonErrorShrinksLabel,
    NewtonPositiveLabel,
    NewtonStepTermLabel,
    RealNumLabel,
    RewriteDFSLabel,
    SearchComparisonLabel,
    SearchComparisonSummaryLabel,
    SearchSignatureLabel,
    SearchAttemptLabel,
    SearchCostLabel,
    SearchJobLabel,
    SearchJobProgressLabel,
    SearchJobStoresLabel,
    SearchPairKeyLabel,
    SearchPausedLabel,
    SearchCtorKeyLabel,
    TreeBucketEntryLabel,
    TreeBucketLabel,
    TreePairKeyLabel,
    TreeCtorKeyLabel,
    TreePatriciaTokenLabel,
    TreePatriciaPairTokenLabel,
    TreePatriciaStopTokenLabel,
    TreePatriciaLeafLabel,
    TreePatriciaBranchLabel,
    TreePatriciaChoiceLabel,
    SearchRewriteCursorLabel,
    SearchRewritePathFrameLabel,
    SearchRewriteRuleBundleLabel,
    SearchRunningLabel,
    SearchStateLabel,
    SearchTheoremCursorLabel,
    SearchWorkerMetricsLabel,
    SearchWorkerPayloadLabel,
    SequenceLabel,
    SqrtLabel,
    SqrtSeqCauchyLabel,
    SqrtSeqTermLabel,
    StepLabel,
    SuccLabel,
    TestFailLabel,
    TestLabel,
    TestNameLabel,
    TestOKLabel,
    TheoremActionLabel,
    ThingyLabel,
    TotalCostLabel,
    TreeLabel,
    WholeLabel,
    RewriteActionLabel,
    ZeroLabel,
)
from .trees import (
    EmptyTree,
    ExactKey,
    ExactKeyOf,
    IndexKey,
    Tree,
    TreeEntries,
    TreeFact,
    TreeInsert,
    TreeKey,
    TreeLeft,
    TreeLookup,
    TreeRight,
    TreeRoot,
    TreeStructuralKey,
)
from .constructors import (
    AllConstructors,
    Compare,
    CompareIn,
    ConstructedBy,
    GetConstructor,
    HypergraphRep,
    IsCauchy,
    IsHypergraph,
    IsReal,
    Limit,
    RealNum,
    Sequence,
    SequenceBase,
    SequenceName,
    SequencePattern,
    SequenceReplacement,
    Sqrt,
    SqrtSeq,
    TestFail,
    TestName,
    TestOK,
    set_all_constructors,
)


class FindBinding(Edge):
    def __init__(self, bindings, var):
        self.result = self._find(bindings, var)
        super().__init__(inputs=Pair(bindings, Pair(var, EmptyList)), results=self.result)

    def _find(self, L, var):
        if Compare(L, EmptyList)() is truth_value:
            return Pair(false_value, EmptyList)
        binding = Head(L)()
        bvar = Head(binding)()
        bval = Head(Tail(binding)())()
        if IdentityCompare(bvar, var)() is truth_value:
            return Pair(truth_value, bval)
        return self._find(Tail(L)(), var)

    def __call__(self):
        return self.result


class MergeBindings(Edge):
    def __init__(self, base_bindings, extra_bindings):
        self.result = self._merge(base_bindings, extra_bindings)
        super().__init__(inputs=Pair(base_bindings, Pair(extra_bindings, EmptyList)), results=self.result)

    def _merge(self, base, extra):
        if Compare(extra, EmptyList)() is truth_value:
            return Pair(truth_value, base)
        b = Head(extra)()
        var = Head(b)()
        val = Head(Tail(b)())()
        found = FindBinding(base, var)()
        found_flag = Head(found)()
        found_val = Tail(found)()
        if Compare(found_flag, truth_value)() is truth_value:
            if TermEqual(found_val, val)() is truth_value:
                return self._merge(base, Tail(extra)())
            return Pair(false_value, EmptyList)
        new_base = Pair(b, base)
        return self._merge(new_base, Tail(extra)())

    def __call__(self):
        return self.result


class MatchArgs(Edge):
    def __init__(self, p_args, t_args):
        self.result = self._match_args(p_args, t_args)
        super().__init__(inputs=Pair(p_args, Pair(t_args, EmptyList)), results=self.result)

    def _match_args(self, pa, ta):
        pa_empty = Compare(pa, EmptyList)()
        ta_empty = Compare(ta, EmptyList)()
        if AndAtom(pa_empty, ta_empty)() is truth_value:
            return Pair(truth_value, EmptyList)
        if OrAtom(pa_empty, ta_empty)() is truth_value:
            return Pair(false_value, EmptyList)
        ph = Head(pa)()
        th = Head(ta)()
        head_match = Match(ph, th)()
        head_flag = Head(head_match)()
        head_bind = Tail(head_match)()
        if Compare(head_flag, truth_value)() is not truth_value:
            return Pair(false_value, EmptyList)
        tail_match = self._match_args(Tail(pa)(), Tail(ta)())
        tail_flag = Head(tail_match)()
        tail_bind = Tail(tail_match)()
        if Compare(tail_flag, truth_value)() is not truth_value:
            return Pair(false_value, EmptyList)
        return MergeBindings(head_bind, tail_bind)()

    def __call__(self):
        return self.result


class Match(Edge):
    def __init__(self, pattern, target):
        self.result = self._match(pattern, target)
        super().__init__(inputs=Pair(pattern, Pair(target, EmptyList)), results=self.result)

    def _is_var_pattern(self, p):
        if IsPair(p)() is false_value:
            return false_value
        h = Head(p)()
        t = Tail(p)()
        if IdentityCompare(h, VarTag)() is false_value:
            return false_value
        if IsPair(t)() is false_value:
            return false_value
        if IdentityCompare(Tail(t)(), EmptyList)() is false_value:
            return false_value
        return truth_value

    def _match_pair(self, p, t):
        hp = Head(p)()
        tp = Tail(p)()
        ht = Head(t)()
        tt = Tail(t)()
        head_match = self._match(hp, ht)
        head_flag = Head(head_match)()
        head_bind = Tail(head_match)()
        if IdentityCompare(head_flag, truth_value)() is false_value:
            return Pair(false_value, EmptyList)
        tail_match = self._match(tp, tt)
        tail_flag = Head(tail_match)()
        tail_bind = Tail(tail_match)()
        if IdentityCompare(tail_flag, truth_value)() is false_value:
            return Pair(false_value, EmptyList)
        return MergeBindings(head_bind, tail_bind)()

    def _match(self, p, t):
        if self._is_var_pattern(p) is truth_value:
            binding = Pair(p, Pair(t, EmptyList))
            return Pair(truth_value, Pair(binding, EmptyList))
        p_is_pair = IsPair(p)()
        t_is_pair = IsPair(t)()
        if AndAtom(p_is_pair, t_is_pair)() is truth_value:
            return self._match_pair(p, t)
        if OrAtom(p_is_pair, t_is_pair)() is truth_value:
            return Pair(false_value, EmptyList)
        pc = GetConstructor(p)()
        tc = GetConstructor(t)()
        pc_empty = IdentityCompare(pc, EmptyList)()
        tc_empty = IdentityCompare(tc, EmptyList)()
        if AndAtom(pc_empty, tc_empty)() is truth_value:
            if Compare(p, t)() is truth_value:
                return Pair(truth_value, EmptyList)
            return Pair(false_value, EmptyList)
        if OrAtom(pc_empty, tc_empty)() is truth_value:
            return Pair(false_value, EmptyList)
        plabel = Head(pc)()
        tlabel = Head(tc)()
        if Compare(plabel, tlabel)() is not truth_value:
            return Pair(false_value, EmptyList)
        return MatchArgs(Tail(pc)(), Tail(tc)())()

    def __call__(self):
        return self.result


class Instantiate(Edge):
    def __init__(self, template, bindings):
        self.result = Pair(self._inst(template, bindings), EmptyList)
        super().__init__(inputs=Pair(template, Pair(bindings, EmptyList)), results=self.result)

    def _inst(self, t, bindings):
        lookup = FindBinding(bindings, t)()
        flag = Head(lookup)()
        val = Tail(lookup)()
        if IdentityCompare(flag, truth_value)() is truth_value:
            return val
        if IsPair(t)() is truth_value:
            new_h = self._inst(Head(t)(), bindings)
            new_t = self._inst(Tail(t)(), bindings)
            return Pair(new_h, new_t)
        c = GetConstructor(t)()
        if Compare(c, EmptyList)() is truth_value:
            return t
        label = Head(c)()
        args = Tail(c)()
        new_args = self._inst_args(args, bindings)
        key = Pair(label, new_args)
        existing = TreeLookup(AllConstructors, key, AllConstructors)()
        if IdentityCompare(existing, EmptyList)() is false_value:
            return existing
        new_node = Atom()
        constructed = ConstructedBy(new_node, label, new_args, AllConstructors)()
        set_all_constructors(Head(Tail(constructed)())())
        return new_node

    def _inst_args(self, L, bindings):
        if Compare(L, EmptyList)() is truth_value:
            return EmptyList
        h = Head(L)()
        t = Tail(L)()
        new_h = self._inst(h, bindings)
        new_t = self._inst_args(t, bindings)
        return Pair(new_h, new_t)

    def __call__(self):
        return self.result


class IsPair(Edge):
    def __init__(self, x):
        try:
            Head(x)()
            Tail(x)()
            atom_result = truth_value
        except Exception:
            atom_result = false_value
        self.result = atom_result
        super().__init__(inputs=Pair(x, EmptyList), results=self.result)

    def __call__(self):
        return self.result


from .math.peano import Count, CountRep, NatEq, NatFromRep, NatLess, NatPred, NatRepOf, Succ

if AllConstructors is None:
    AllConstructors = Tree(EmptyList)
    set_all_constructors(AllConstructors)


one_pair = Succ(Zero, AllConstructors)()
one = Head(one_pair)()
AllConstructors = set_all_constructors(Head(Tail(one_pair)())())

two_pair = Succ(one, AllConstructors)()
two = Head(two_pair)()
AllConstructors = set_all_constructors(Head(Tail(two_pair)())())

three_pair = Succ(two, AllConstructors)()
three = Head(three_pair)()
AllConstructors = set_all_constructors(Head(Tail(three_pair)())())

four_pair = Succ(three, AllConstructors)()
four = Head(four_pair)()
AllConstructors = set_all_constructors(Head(Tail(four_pair)())())

five_pair = Succ(four, AllConstructors)()
five = Head(five_pair)()
AllConstructors = set_all_constructors(Head(Tail(five_pair)())())

six_pair = Succ(five, AllConstructors)()
six = Head(six_pair)()
AllConstructors = set_all_constructors(Head(Tail(six_pair)())())

seven_pair = Succ(six, AllConstructors)()
seven = Head(seven_pair)()
AllConstructors = set_all_constructors(Head(Tail(seven_pair)())())

eight_pair = Succ(seven, AllConstructors)()
eight = Head(eight_pair)()
AllConstructors = set_all_constructors(Head(Tail(eight_pair)())())

nine_pair = Succ(eight, AllConstructors)()
nine = Head(nine_pair)()
AllConstructors = set_all_constructors(Head(Tail(nine_pair)())())


class IsEdge(Edge):
    def __init__(self, x, registry):
        is_pair_x = IsPair(x)()
        if is_pair_x is truth_value:
            atom_result = truth_value
        else:
            c = GetConstructor(x, registry)()
            if CompareIn(c, EmptyList, registry)() is truth_value:
                atom_result = false_value
            else:
                label = Head(c)()
                is_hg = IdentityCompare(label, HypergraphLabel)()
                is_test = IdentityCompare(label, TestLabel)()
                if OrAtom(is_hg, is_test)() is truth_value:
                    atom_result = false_value
                else:
                    args = Tail(c)()
                    ar_pair = Count(args, registry)()
                    ar = Head(ar_pair)()
                    reg = Head(Tail(ar_pair)())()
                    atom_result = NatEq(ar, two, reg)()
        self.result = atom_result
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsAtom(Edge):
    def __init__(self, x, registry):
        if IsPair(x)() is truth_value:
            atom_result = truth_value
        else:
            edge_check = IsEdge(x, registry)()
            if edge_check is truth_value:
                atom_result = false_value
            else:
                atom_result = truth_value
        self.result = atom_result
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CanonicalArithmeticTerm(Edge):
    def __init__(self, term, registry):
        self.registry = registry
        self.result = self._canonical(term)
        super().__init__(inputs=Pair(term, Pair(registry, EmptyList)), results=self.result)

    def _canonical(self, term):
        if IsPair(term)() is truth_value:
            label = Head(term)()
            args = Tail(term)()
            if IdentityCompare(label, ExprAddLabel)() is truth_value:
                return self._canonical_ac(label, args)
            if IdentityCompare(label, ExprMulLabel)() is truth_value:
                return self._canonical_ac(label, args)
            if IdentityCompare(label, ExprEqLabel)() is truth_value:
                return self._canonical_eq(args)
            return Pair(self._canonical(label), self._canonical(args))
        constructor = GetConstructor(term, self.registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            return term
        label = Head(constructor)()
        args = Tail(constructor)()
        if IdentityCompare(label, ExprAddLabel)() is truth_value:
            return self._canonical_ac(label, args)
        if IdentityCompare(label, ExprMulLabel)() is truth_value:
            return self._canonical_ac(label, args)
        if IdentityCompare(label, ExprEqLabel)() is truth_value:
            return self._canonical_eq(args)
        canonical_args = self._canonical_arg_chain(args)
        return self._rebuild_constructed(label, canonical_args)

    def _canonical_arg_chain(self, args):
        if IdentityCompare(args, EmptyList)() is truth_value:
            return EmptyList
        return Pair(self._canonical(Head(args)()), self._canonical_arg_chain(Tail(args)()))

    def _rebuild_constructed(self, label, args):
        key = Pair(label, args)
        existing = TreeLookup(self.registry, key, self.registry)()
        if IdentityCompare(existing, EmptyList)() is false_value:
            return existing
        node = Atom()
        constructed = ConstructedBy(node, label, args, self.registry)()
        self.registry = Head(Tail(constructed)())()
        return node

    def _reverse_chain(self, chain):
        result = EmptyList
        remaining = chain
        while IdentityCompare(remaining, EmptyList)() is false_value:
            result = Pair(Head(remaining)(), result)
            remaining = Tail(remaining)()
        return result

    def _flatten_ac_rev(self, label, term, acc):
        term = self._canonical(term)
        if IsPair(term)() is truth_value:
            if IdentityCompare(Head(term)(), label)() is truth_value:
                args = Tail(term)()
                left = Head(args)()
                right = Head(Tail(args)())()
                acc = self._flatten_ac_rev(label, right, acc)
                return self._flatten_ac_rev(label, left, acc)
        constructor = GetConstructor(term, self.registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            return Pair(term, acc)
        if IdentityCompare(Head(constructor)(), label)() is false_value:
            return Pair(term, acc)
        args = Tail(constructor)()
        left = Head(args)()
        right = Head(Tail(args)())()
        acc = self._flatten_ac_rev(label, right, acc)
        return self._flatten_ac_rev(label, left, acc)

    def _exact_key_kind_rank(self, key):
        label = Head(key)()
        if IdentityCompare(label, ExactAtomKeyLabel)() is truth_value:
            return Zero
        if IdentityCompare(label, ExactCtorKeyLabel)() is truth_value:
            return one
        return two

    def _exact_key_payload_head(self, key):
        return Head(Tail(key)())()

    def _exact_key_payload_tail_head(self, key):
        return Head(Tail(Tail(key)())())()

    def _exact_key_chain_less(self, left, right):
        if IdentityCompare(left, EmptyList)() is truth_value:
            if IdentityCompare(right, EmptyList)() is truth_value:
                return false_value
            return truth_value
        if IdentityCompare(right, EmptyList)() is truth_value:
            return false_value
        left_head = Head(left)()
        right_head = Head(right)()
        if self._exact_key_less(left_head, right_head) is truth_value:
            return truth_value
        if self._exact_key_less(right_head, left_head) is truth_value:
            return false_value
        return self._exact_key_chain_less(Tail(left)(), Tail(right)())

    def _exact_key_less(self, left, right):
        if IdentityCompare(left, right)() is truth_value:
            return false_value
        left_label = Head(left)()
        right_label = Head(right)()
        if IdentityCompare(left_label, right_label)() is false_value:
            return NatLess(self._exact_key_kind_rank(left), self._exact_key_kind_rank(right), self.registry)()
        if IdentityCompare(left_label, ExactAtomKeyLabel)() is truth_value:
            return IdentityLess(self._exact_key_payload_head(left), self._exact_key_payload_head(right))()
        if IdentityCompare(left_label, ExactCtorKeyLabel)() is truth_value:
            left_ctor_label = self._exact_key_payload_head(left)
            right_ctor_label = self._exact_key_payload_head(right)
            if IdentityCompare(left_ctor_label, right_ctor_label)() is false_value:
                return IdentityLess(left_ctor_label, right_ctor_label)()
            return self._exact_key_chain_less(
                self._exact_key_payload_tail_head(left),
                self._exact_key_payload_tail_head(right),
            )
        left_head = self._exact_key_payload_head(left)
        right_head = self._exact_key_payload_head(right)
        if self._exact_key_less(left_head, right_head) is truth_value:
            return truth_value
        if self._exact_key_less(right_head, left_head) is truth_value:
            return false_value
        return self._exact_key_less(
            self._exact_key_payload_tail_head(left),
            self._exact_key_payload_tail_head(right),
        )

    def _term_head_label(self, term):
        if IsPair(term)() is truth_value:
            return Head(term)()
        constructor = GetConstructor(term, self.registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            return term
        return Head(constructor)()

    def _term_arg_chain(self, term):
        if IsPair(term)() is truth_value:
            return Tail(term)()
        constructor = GetConstructor(term, self.registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            return EmptyList
        return Tail(constructor)()

    def _term_arg_chain_less(self, left, right):
        if IdentityCompare(left, EmptyList)() is truth_value:
            if IdentityCompare(right, EmptyList)() is truth_value:
                return false_value
            return truth_value
        if IdentityCompare(right, EmptyList)() is truth_value:
            return false_value
        left_head = Head(left)()
        right_head = Head(right)()
        if self._canonical_term_less(left_head, right_head) is truth_value:
            return truth_value
        if self._canonical_term_less(right_head, left_head) is truth_value:
            return false_value
        return self._term_arg_chain_less(Tail(left)(), Tail(right)())

    def _canonical_term_less(self, left, right):
        if IdentityCompare(left, right)() is truth_value:
            return false_value
        if AndAtom(IsNat(left, self.registry)(), IsNat(right, self.registry)())() is truth_value:
            return NatLess(left, right, self.registry)()
        left_head = self._term_head_label(left)
        right_head = self._term_head_label(right)
        if IdentityCompare(left_head, right_head)() is false_value:
            return IdentityLess(left_head, right_head)()
        left_args = self._term_arg_chain(left)
        right_args = self._term_arg_chain(right)
        if IdentityCompare(left_args, EmptyList)() is truth_value:
            if IdentityCompare(right_args, EmptyList)() is truth_value:
                return IdentityLess(left, right)()
            return truth_value
        if IdentityCompare(right_args, EmptyList)() is truth_value:
            return false_value
        return self._term_arg_chain_less(left_args, right_args)

    def _insert_sorted_term(self, term, ordered):
        if IdentityCompare(ordered, EmptyList)() is truth_value:
            return Pair(term, EmptyList)
        head_term = Head(ordered)()
        if self._canonical_term_less(term, head_term) is truth_value:
            return Pair(term, ordered)
        return Pair(head_term, self._insert_sorted_term(term, Tail(ordered)()))

    def _sort_term_chain(self, chain):
        ordered = EmptyList
        remaining = chain
        while IdentityCompare(remaining, EmptyList)() is false_value:
            ordered = self._insert_sorted_term(Head(remaining)(), ordered)
            remaining = Tail(remaining)()
        return ordered

    def _rebuild_application(self, label, args):
        return Pair(label, args)

    def _rebuild_ac(self, label, operands):
        if IdentityCompare(operands, EmptyList)() is truth_value:
            return EmptyList
        left = Head(operands)()
        rest = Tail(operands)()
        if IdentityCompare(rest, EmptyList)() is truth_value:
            return left
        right = self._rebuild_ac(label, rest)
        return self._rebuild_application(label, Pair(left, Pair(right, EmptyList)))

    def _canonical_ac(self, label, args):
        left = Head(args)()
        right = Head(Tail(args)())()
        operands = self._flatten_ac_rev(label, left, EmptyList)
        operands = self._flatten_ac_rev(label, right, operands)
        operands = self._reverse_chain(operands)
        operands = self._sort_term_chain(operands)
        return self._rebuild_ac(label, operands)

    def _canonical_eq(self, args):
        left = self._canonical(Head(args)())
        right = self._canonical(Head(Tail(args)())())
        if self._canonical_term_less(right, left) is truth_value:
            return self._rebuild_application(ExprEqLabel, Pair(right, Pair(left, EmptyList)))
        return self._rebuild_application(ExprEqLabel, Pair(left, Pair(right, EmptyList)))

    def __call__(self):
        return self.result


class Fraction(Edge):
    def __init__(self, p, q, registry):
        p_ok = IsNat(p, registry)()
        q_ok = IsNat(q, registry)()
        if AndAtom(p_ok, q_ok)() is not truth_value:
            raise TypeError("Fraction expects two Nat values")
        args = Pair(p, Pair(q, EmptyList))
        key = Pair(FractionLabel, args)
        existing = TreeLookup(registry, key, registry)()
        if IdentityCompare(existing, EmptyList)() is truth_value:
            node = Atom()
            constructed = ConstructedBy(node, FractionLabel, args, registry)()
            new_registry = Head(Tail(constructed)())()
        else:
            node = existing
            new_registry = registry
        self.result = Pair(node, Pair(new_registry, EmptyList))
        super().__init__(inputs=Pair(p, Pair(q, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class FractionLeft(Edge):
    def __init__(self, x, registry):
        c = GetConstructor(x, registry)()
        if IdentityCompare(c, EmptyList)() is truth_value:
            atom_result = EmptyList
        else:
            label = Head(c)()
            args = Tail(c)()
            atom_result = Head(args)() if IdentityCompare(label, FractionLabel)() is truth_value else EmptyList
        self.result = atom_result
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FractionRight(Edge):
    def __init__(self, x, registry):
        c = GetConstructor(x, registry)()
        if IdentityCompare(c, EmptyList)() is truth_value:
            atom_result = EmptyList
        else:
            label = Head(c)()
            args = Tail(c)()
            atom_result = Head(Tail(args)())() if IdentityCompare(label, FractionLabel)() is truth_value else EmptyList
        self.result = atom_result
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsFraction(Edge):
    def __init__(self, x, registry):
        c = GetConstructor(x, registry)()
        if IdentityCompare(c, EmptyList)() is truth_value:
            atom_result = false_value
        else:
            label = Head(c)()
            if IdentityCompare(label, FractionLabel)() is false_value:
                atom_result = false_value
            else:
                args = Tail(c)()
                if IdentityCompare(args, EmptyList)() is truth_value:
                    atom_result = false_value
                else:
                    num = Head(args)()
                    rest = Tail(args)()
                    if IdentityCompare(rest, EmptyList)() is truth_value:
                        atom_result = false_value
                    else:
                        den = Head(rest)()
                        tail2 = Tail(rest)()
                        if IdentityCompare(tail2, EmptyList)() is false_value:
                            atom_result = false_value
                        else:
                            atom_result = AndAtom(IsNat(num, registry)(), IsNat(den, registry)())()
        self.result = atom_result
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Whole(Edge):
    def __init__(self, a, b, registry):
        a_ok = IsNat(a, registry)()
        b_ok = IsNat(b, registry)()
        if AndAtom(a_ok, b_ok)() is not truth_value:
            raise TypeError("Whole expects two Nat values")
        args = Pair(a, Pair(b, EmptyList))
        key = Pair(WholeLabel, args)
        existing = TreeLookup(registry, key, registry)()
        if IdentityCompare(existing, EmptyList)() is truth_value:
            node = Atom()
            constructed = ConstructedBy(node, WholeLabel, args, registry)()
            new_registry = Head(Tail(constructed)())()
        else:
            node = existing
            new_registry = registry
        self.result = Pair(node, Pair(new_registry, EmptyList))
        super().__init__(inputs=Pair(a, Pair(b, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class WholeLeft(Edge):
    def __init__(self, x, registry):
        c = GetConstructor(x, registry)()
        if IdentityCompare(c, EmptyList)() is truth_value:
            atom_result = EmptyList
        else:
            label = Head(c)()
            args = Tail(c)()
            atom_result = Head(args)() if IdentityCompare(label, WholeLabel)() is truth_value else EmptyList
        self.result = atom_result
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class WholeRight(Edge):
    def __init__(self, x, registry):
        c = GetConstructor(x, registry)()
        if IdentityCompare(c, EmptyList)() is truth_value:
            atom_result = EmptyList
        else:
            label = Head(c)()
            args = Tail(c)()
            atom_result = Head(Tail(args)())() if IdentityCompare(label, WholeLabel)() is truth_value else EmptyList
        self.result = atom_result
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsWhole(Edge):
    def __init__(self, x, registry):
        c = GetConstructor(x, registry)()
        if IdentityCompare(c, EmptyList)() is truth_value:
            atom_result = false_value
        else:
            label = Head(c)()
            if IdentityCompare(label, WholeLabel)() is false_value:
                atom_result = false_value
            else:
                args = Tail(c)()
                if IdentityCompare(args, EmptyList)() is truth_value:
                    atom_result = false_value
                else:
                    a = Head(args)()
                    rest = Tail(args)()
                    if IdentityCompare(rest, EmptyList)() is truth_value:
                        atom_result = false_value
                    else:
                        b = Head(rest)()
                        tail2 = Tail(rest)()
                        if IdentityCompare(tail2, EmptyList)() is false_value:
                            atom_result = false_value
                        else:
                            atom_result = AndAtom(IsNat(a, registry)(), IsNat(b, registry)())()
        self.result = atom_result
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class WholeAdd(Edge):
    def __init__(self, x, y, registry):
        if AndAtom(IsWhole(x, registry)(), IsWhole(y, registry)())() is not truth_value:
            raise TypeError("WholeAdd expects Whole values")
        ax = WholeLeft(x, registry)()
        bx = WholeRight(x, registry)()
        ay = WholeLeft(y, registry)()
        by = WholeRight(y, registry)()
        new_a_pair = Add(ax, ay, registry)()
        new_a = Head(new_a_pair)()
        reg1 = Head(Tail(new_a_pair)())()
        new_b_pair = Add(bx, by, reg1)()
        new_b = Head(new_b_pair)()
        reg2 = Head(Tail(new_b_pair)())()
        self.result = Whole(new_a, new_b, reg2)()
        super().__init__(inputs=Pair(x, Pair(y, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class WholeMultiply(Edge):
    def __init__(self, x, y, registry):
        if AndAtom(IsWhole(x, registry)(), IsWhole(y, registry)())() is not truth_value:
            raise TypeError("WholeMultiply expects Whole values")
        ax = WholeLeft(x, registry)()
        bx = WholeRight(x, registry)()
        ay = WholeLeft(y, registry)()
        by = WholeRight(y, registry)()
        ac_pair = Multiply(ax, ay, registry)()
        ac = Head(ac_pair)()
        reg1 = Head(Tail(ac_pair)())()
        bd_pair = Multiply(bx, by, reg1)()
        bd = Head(bd_pair)()
        reg2 = Head(Tail(bd_pair)())()
        ad_pair = Multiply(ax, by, reg2)()
        ad = Head(ad_pair)()
        reg3 = Head(Tail(ad_pair)())()
        bc_pair = Multiply(bx, ay, reg3)()
        bc = Head(bc_pair)()
        reg4 = Head(Tail(bc_pair)())()
        left_pair = Add(ac, bd, reg4)()
        left = Head(left_pair)()
        reg5 = Head(Tail(left_pair)())()
        right_pair = Add(ad, bc, reg5)()
        right = Head(right_pair)()
        reg6 = Head(Tail(right_pair)())()
        self.result = Whole(left, right, reg6)()
        super().__init__(inputs=Pair(x, Pair(y, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


from .prettyprinting import AtomName, FractionText, NatText, PrettyPair, PrettyTerm, PrettyValue, WholeText


class Add(Edge):
    def __init__(self, left, right, registry):
        from .math.arithmetic import Add as ArithmeticAdd

        self.result = ArithmeticAdd(left, right, registry)()
        super().__init__(inputs=Pair(left, Pair(right, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class Multiply(Edge):
    def __init__(self, left, right, registry):
        from .math.arithmetic import Multiply as ArithmeticMultiply

        self.result = ArithmeticMultiply(left, right, registry)()
        super().__init__(inputs=Pair(left, Pair(right, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class IsNat(Edge):
    def __init__(self, x, registry):
        from .math.arithmetic import IsNat as ArithmeticIsNat

        self.result = ArithmeticIsNat(x, registry)()
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


from .matching import Rewrite, TermEqual
from .context import (
    Context,
    ContextAllRules,
    ContextConstructors,
    ContextDerivations,
    ContextDerivationSchemata,
    ContextEdges,
    ContextNextRuleIndex,
    ContextNodes,
    ContextRuleOrder,
    ContextSearchComparisons,
    ContextSearchComparisonJobs,
    ContextSearchHistory,
    ContextSearchJobs,
    ContextSearchMemo,
    ContextTestResults,
    ContextTests,
    FromContextGetAllRules,
    FromContextGetConstructors,
    FromContextGetDerivations,
    FromContextGetDerivationSchemata,
    FromContextGetEdges,
    FromContextGetNodes,
    FromContextGetRuleOrder,
    FromContextGetSearchComparisons,
    FromContextGetSearchComparisonJobs,
    FromContextGetSearchHistory,
    FromContextGetSearchJobs,
    FromContextGetSearchMemo,
    FromContextGetNatValueIndex,
    FromContextGetTestResults,
    FromContextGetTests,
    HypergraphContext,
    IsContext,
)
from .graph import Hypergraph, Reverse, RunTests, Test
from .heuristics import Heuristic, HeuristicAlpha, HeuristicBeamWidth, HeuristicBeta, HeuristicRuleOrder, HeuristicSearchMode
from .proof import (
    ActionBindings,
    ActionPath,
    ActionRule,
    CollectRules,
    ContainsVar,
    DerivationCost,
    ExplainDerivation,
    IsRewriteAction,
    IsTheoremAction,
    IsKnowledge,
    IsVarPattern,
    Knowledge,
    KnowledgeFacts,
    MultiRule,
    PrettyAction,
    ProofCostRewriteSteps,
    ProofCostSteps,
    ProofCostTheoremSteps,
    ProofCostValue,
    Prove,
    Rule,
    RewriteAction,
    RulePremises,
    RulePattern,
    RuleReplacement,
    SearchAttempt,
    SearchAttemptDerivation,
    SearchAttemptHeuristic,
    SearchAttemptProofCost,
    SearchAttemptSearchCost,
    SearchAttemptTotalCost,
    StepAction,
    TermHead,
    TheoremAction,
    TotalCostAlpha,
    TotalCostBeta,
    TotalCostValue,
)
from .search import (
    CompareSearchModes,
    LookupSearchComparison,
    Search,
    SearchAdviceText,
    SearchBFS,
    SearchBeam,
    SearchComparison,
    SearchComparisonJob,
    SearchComparisonBestAttempt,
    SearchComparisonBestHeuristic,
    SearchComparisonSignature,
    SearchCostExpanded,
    SearchCostFoundDepth,
    SearchCostFrontierPeak,
    SearchCostGenerated,
    SearchCostOutcome,
    SearchCostValue,
    SearchDFS,
    SearchJob,
    SearchJobExpanded,
    SearchJobFrontier,
    SearchJobFrontierSize,
    SearchJobFrontierPeak,
    SearchJobGoal,
    SearchJobHeuristic,
    SearchJobResultPlan,
    SearchJobRewriteRules,
    SearchJobRules,
    SearchJobStart,
    SearchJobStatus,
    SearchJobTheoremRuleCache,
    SearchJobVisited,
    SearchModeText,
    SearchRewriteDFS,
    SearchSignature,
    SearchSignatureForProblem,
    SearchState,
    SearchStateCurrent,
    SearchStateCursor,
    SearchStatePlan,
    SearchTheoremCursor,
    SearchTheoremCursorActions,
    SearchTheoremCursorDelta,
    SearchTheoremCursorExactTrie,
    SearchTheoremCursorGenerated,
    SearchTheoremCursorHeadIndex,
    SearchTheoremCursorNextDelta,
    SearchTheoremCursorRules,
    SearchRewriteCursor,
    SearchRewriteCursorAgenda,
    SearchRewriteCursorGenerated,
    SearchRewriteCursorRestRules,
    SearchRewriteCursorRule,
    SearchRewritePathFrame,
    SearchRewritePathFramePath,
    SearchRewritePathFrameSubterm,
    SearchStateSeen,
    SearchStateStepsRemaining,
    SearchStep,
    LookupSearchAttempt,
    LookupSearchJob,
    RemoveSearchJob,
)

__all__ = [name for name in globals() if not name.startswith("_")]
