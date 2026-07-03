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
            if IdentityCompare(found_val, val)() is truth_value:
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
    SearchTheoremCursorGenerated,
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
