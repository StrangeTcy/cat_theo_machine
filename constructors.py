from __future__ import annotations

from .labels import (
    AStarLabel,
    BFSLabel,
    BeamLabel,
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
    FractionLabel,
    GoalHeadOrderLabel,
    HypergraphLabel,
    InsertionOrderLabel,
    IsCauchyLabel,
    IsRealLabel,
    LimitLabel,
    NewtonErrorIdentityLabel,
    NewtonErrorShrinksLabel,
    NewtonPositiveLabel,
    NewtonStepTermLabel,
    PairLabel,
    RealNumLabel,
    RewriteDFSLabel,
    SequenceLabel,
    SearchRewriteCursorLabel,
    SearchRewritePathFrameLabel,
    SearchRewriteRuleBundleLabel,
    SearchTheoremCursorLabel,
    SqrtLabel,
    SqrtSeqCauchyLabel,
    SqrtSeqTermLabel,
    SuccLabel,
    TestFailLabel,
    TestLabel,
    TestNameLabel,
    TestOKLabel,
    ThingyLabel,
    TreeBucketEntryLabel,
    TreeBucketLabel,
    TreeLabel,
    TreePatriciaBranchLabel,
    TreePatriciaChoiceLabel,
    TreePatriciaLeafLabel,
    TreePatriciaPairTokenLabel,
    TreePatriciaStopTokenLabel,
    TreePatriciaTokenLabel,
    WholeLabel,
    ZeroLabel,
)
from .core import (
    Atom,
    Edge,
    EmptyList,
    Head,
    IdentityCompare,
    Pair,
    Tail,
    Thingy,
    VarTag,
    Zero,
    false_value,
    truth_value,
)
from .logic import AndAtom, OrAtom
from .trees import (
    AllConstructors as _InitialAllConstructors,
    Tree,
    TreeInsert,
    TreeLookup,
)

if _InitialAllConstructors is None:
    AllConstructors = Tree(EmptyList)
else:
    AllConstructors = _InitialAllConstructors


def _fresh_registry():
    return Tree(EmptyList)


def _normalize_registry(registry):
    if registry is None:
        registry = _fresh_registry()
        set_all_constructors(registry)
        return registry
    return registry


def set_all_constructors(registry):
    global AllConstructors
    AllConstructors = registry
    return registry


def sync_from_namespace(namespace):
    for name in (
        "AllConstructors",
        "EmptyList",
        "Zero",
        "VarTag",
        "truth_value",
        "false_value",
        "ZeroLabel",
        "SuccLabel",
        "PairLabel",
        "ThingyLabel",
        "HypergraphLabel",
        "TestLabel",
        "TestOKLabel",
        "TestFailLabel",
        "TestNameLabel",
        "SequenceLabel",
        "LimitLabel",
        "IsCauchyLabel",
        "RealNumLabel",
        "IsRealLabel",
        "SqrtLabel",
        "SqrtSeqTermLabel",
        "NewtonStepTermLabel",
        "NewtonPositiveLabel",
        "NewtonErrorIdentityLabel",
        "NewtonErrorShrinksLabel",
        "SqrtSeqCauchyLabel",
        "FractionLabel",
        "WholeLabel",
        "ExprAddLabel",
        "ExprMulLabel",
        "ExprFracLabel",
        "ExprDivLabel",
        "ExprPowLabel",
        "ExprIntLabel",
        "ExprNegLabel",
        "ExprEqLabel",
        "ExprLtLabel",
        "DFSLabel",
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
        "RewriteDFSLabel",
        "InsertionOrderLabel",
        "GoalHeadOrderLabel",
        "SearchTheoremCursorLabel",
        "SearchRewriteCursorLabel",
        "SearchRewritePathFrameLabel",
        "SearchRewriteRuleBundleLabel",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


class ConstructedBy(Edge):
    def __init__(self, node, label, args, registry):
        registry = _normalize_registry(registry)
        key = Pair(label, args)
        fact = node
        fact.constructor = key
        new_registry = TreeInsert(registry, key, fact, registry)()
        self.result = Pair(fact, Pair(new_registry, EmptyList))
        super().__init__(
            inputs=Pair(node, Pair(label, Pair(args, Pair(registry, EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GetConstructor(Edge):
    def __init__(self, x, registry=None):
        if registry is None:
            registry = AllConstructors
        registry = _normalize_registry(registry)
        self.x = x
        self.registry = registry
        self.result = self._direct_constructor(x)
        if IdentityCompare(self.result, EmptyList)() is truth_value:
            try:
                self.result = x.constructor
            except Exception:
                self.result = EmptyList
        super().__init__(inputs=Pair(x, EmptyList), results=self.result)

    def _is_direct_label(self, label):
        if IdentityCompare(label, TreeLabel)() is truth_value:
            return truth_value
        if IdentityCompare(label, TreeBucketLabel)() is truth_value:
            return truth_value
        if IdentityCompare(label, TreeBucketEntryLabel)() is truth_value:
            return truth_value
        if IdentityCompare(label, TreePatriciaTokenLabel)() is truth_value:
            return truth_value
        if IdentityCompare(label, TreePatriciaPairTokenLabel)() is truth_value:
            return truth_value
        if IdentityCompare(label, TreePatriciaStopTokenLabel)() is truth_value:
            return truth_value
        if IdentityCompare(label, TreePatriciaLeafLabel)() is truth_value:
            return truth_value
        if IdentityCompare(label, TreePatriciaBranchLabel)() is truth_value:
            return truth_value
        if IdentityCompare(label, TreePatriciaChoiceLabel)() is truth_value:
            return truth_value
        return false_value

    def _direct_constructor(self, term):
        try:
            label = Head(term)()
        except Exception:
            label = EmptyList
        if IdentityCompare(label, EmptyList)() is false_value:
            if self._is_direct_label(label) is truth_value:
                return term
        try:
            value = term()
        except Exception:
            return EmptyList
        try:
            label = Head(value)()
        except Exception:
            return EmptyList
        if self._is_direct_label(label) is truth_value:
            return value
        return EmptyList

    def __call__(self):
        return self.result


class Compare(Edge):
    def __init__(self, x, y):
        self.result = self._eq(x, y)
        super().__init__(inputs=Pair(x, Pair(y, EmptyList)), results=self.result)

    def _eq(self, x, y):
        if IdentityCompare(x, y)() is truth_value:
            return truth_value
        try:
            Head(x)()
            Tail(x)()
            x_is_pair = truth_value
        except Exception:
            x_is_pair = false_value
        try:
            Head(y)()
            Tail(y)()
            y_is_pair = truth_value
        except Exception:
            y_is_pair = false_value
        if AndAtom(x_is_pair, y_is_pair)() is truth_value:
            head_eq = self._eq(Head(x)(), Head(y)())
            tail_eq = self._eq(Tail(x)(), Tail(y)())
            return AndAtom(head_eq, tail_eq)()
        if OrAtom(x_is_pair, y_is_pair)() is truth_value:
            return false_value
        cx = GetConstructor(x)()
        cy = GetConstructor(y)()
        cx_empty = IdentityCompare(cx, EmptyList)()
        cy_empty = IdentityCompare(cy, EmptyList)()
        if AndAtom(cx_empty, cy_empty)() is truth_value:
            if x() == y():
                if x() is None:
                    return false_value
                return truth_value
            return false_value
        if OrAtom(cx_empty, cy_empty)() is truth_value:
            return false_value
        lx = Head(cx)()
        ly = Head(cy)()
        if IdentityCompare(lx, ly)() is false_value:
            return false_value
        return self._eq_args(Tail(cx)(), Tail(cy)())

    def _eq_args(self, ax, ay):
        ax_empty = IdentityCompare(ax, EmptyList)()
        ay_empty = IdentityCompare(ay, EmptyList)()
        if AndAtom(ax_empty, ay_empty)() is truth_value:
            return truth_value
        if OrAtom(ax_empty, ay_empty)() is truth_value:
            return false_value
        hx = Head(ax)()
        tx = Tail(ax)()
        hy = Head(ay)()
        ty = Tail(ay)()
        head_eq = self._eq(hx, hy)
        tail_eq = self._eq_args(tx, ty)
        return AndAtom(head_eq, tail_eq)()

    def __call__(self):
        return self.result


class CompareIn(Edge):
    def __init__(self, x, y, registry):
        self.registry = registry
        self.result = self._eq(x, y)
        super().__init__(inputs=Pair(x, Pair(y, Pair(registry, EmptyList))), results=self.result)

    def _eq(self, x, y):
        if IdentityCompare(x, y)() is truth_value:
            return truth_value
        try:
            Head(x)()
            Tail(x)()
            x_is_pair = truth_value
        except Exception:
            x_is_pair = false_value
        try:
            Head(y)()
            Tail(y)()
            y_is_pair = truth_value
        except Exception:
            y_is_pair = false_value
        if AndAtom(x_is_pair, y_is_pair)() is truth_value:
            head_eq = self._eq(Head(x)(), Head(y)())
            tail_eq = self._eq(Tail(x)(), Tail(y)())
            return AndAtom(head_eq, tail_eq)()
        if OrAtom(x_is_pair, y_is_pair)() is truth_value:
            return false_value
        cx = GetConstructor(x, self.registry)()
        cy = GetConstructor(y, self.registry)()
        cx_empty = IdentityCompare(cx, EmptyList)()
        cy_empty = IdentityCompare(cy, EmptyList)()
        if AndAtom(cx_empty, cy_empty)() is truth_value:
            if x() == y():
                if x() is None:
                    return false_value
                return truth_value
            return false_value
        if OrAtom(cx_empty, cy_empty)() is truth_value:
            return false_value
        lx = Head(cx)()
        ly = Head(cy)()
        if IdentityCompare(lx, ly)() is false_value:
            return false_value
        return self._eq_args(Tail(cx)(), Tail(cy)())

    def _eq_args(self, ax, ay):
        ax_empty = IdentityCompare(ax, EmptyList)()
        ay_empty = IdentityCompare(ay, EmptyList)()
        if AndAtom(ax_empty, ay_empty)() is truth_value:
            return truth_value
        if OrAtom(ax_empty, ay_empty)() is truth_value:
            return false_value
        hx = Head(ax)()
        tx = Tail(ax)()
        hy = Head(ay)()
        ty = Tail(ay)()
        head_eq = self._eq(hx, hy)
        tail_eq = self._eq_args(tx, ty)
        return AndAtom(head_eq, tail_eq)()

    def __call__(self):
        return self.result


class HypergraphRep(Atom):
    pass


class IsHypergraph(Edge):
    def __init__(self, x, constructor_registry):
        constructor = GetConstructor(x, constructor_registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            atom_result = false_value
        else:
            label = Head(constructor)()
            atom_result = OrAtom(
                IdentityCompare(label, HypergraphLabel)(),
                IdentityCompare(label, TestLabel)(),
            )()
        self.result = atom_result
        super().__init__(inputs=Pair(x, Pair(constructor_registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TestOK(Atom):
    def __init__(self, registry):
        super().__init__()
        ConstructedBy(self, TestOKLabel, EmptyList, registry)()
        self.value = "TestOK"


class TestFail(Atom):
    def __init__(self, registry):
        super().__init__()
        ConstructedBy(self, TestFailLabel, EmptyList, registry)()
        self.value = "TestFail"


class TestName(Atom):
    def __init__(self, name_atom, registry):
        super().__init__()
        stored_name = Thingy()
        stored_name.value = name_atom
        args = Pair(stored_name, EmptyList)
        ConstructedBy(self, TestNameLabel, args, registry)()
        self.value = name_atom


def _construct_or_reuse(label, args, registry):
    registry = _normalize_registry(registry)
    key = Pair(label, args)
    existing = TreeLookup(registry, key, registry)()
    if IdentityCompare(existing, EmptyList)() is truth_value:
        node = Atom()
        constructed = ConstructedBy(node, label, args, registry)()
        new_registry = Head(Tail(constructed)())()
    else:
        node = existing
        new_registry = registry
    return Pair(node, Pair(new_registry, EmptyList))


class Sequence(Edge):
    def __init__(self, name, base_value, pattern, replacement, registry):
        args = Pair(name, Pair(base_value, Pair(pattern, Pair(replacement, EmptyList))))
        self.result = _construct_or_reuse(SequenceLabel, args, registry)
        super().__init__(
            inputs=Pair(name, Pair(base_value, Pair(pattern, Pair(replacement, Pair(registry, EmptyList))))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SequenceName(Edge):
    def __init__(self, seq, registry):
        constructor = GetConstructor(seq, registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            atom_result = EmptyList
        else:
            label = Head(constructor)()
            args = Tail(constructor)()
            atom_result = Head(args)() if IdentityCompare(label, SequenceLabel)() is truth_value else EmptyList
        self.result = atom_result
        super().__init__(inputs=Pair(seq, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SequenceBase(Edge):
    def __init__(self, seq, registry):
        constructor = GetConstructor(seq, registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            atom_result = EmptyList
        else:
            label = Head(constructor)()
            args = Tail(constructor)()
            atom_result = Head(Tail(args)())() if IdentityCompare(label, SequenceLabel)() is truth_value else EmptyList
        self.result = atom_result
        super().__init__(inputs=Pair(seq, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SequencePattern(Edge):
    def __init__(self, seq, registry):
        constructor = GetConstructor(seq, registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            atom_result = EmptyList
        else:
            label = Head(constructor)()
            args = Tail(constructor)()
            atom_result = (
                Head(Tail(Tail(args)())())()
                if IdentityCompare(label, SequenceLabel)() is truth_value
                else EmptyList
            )
        self.result = atom_result
        super().__init__(inputs=Pair(seq, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SequenceReplacement(Edge):
    def __init__(self, seq, registry):
        constructor = GetConstructor(seq, registry)()
        if IdentityCompare(constructor, EmptyList)() is truth_value:
            atom_result = EmptyList
        else:
            label = Head(constructor)()
            args = Tail(constructor)()
            atom_result = (
                Head(Tail(Tail(Tail(args)())())())()
                if IdentityCompare(label, SequenceLabel)() is truth_value
                else EmptyList
            )
        self.result = atom_result
        super().__init__(inputs=Pair(seq, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Limit(Edge):
    def __init__(self, seq, L, registry):
        args = Pair(seq, Pair(L, EmptyList))
        self.result = _construct_or_reuse(LimitLabel, args, registry)
        super().__init__(inputs=Pair(seq, Pair(L, Pair(registry, EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class IsCauchy(Edge):
    def __init__(self, seq, registry):
        args = Pair(seq, EmptyList)
        self.result = _construct_or_reuse(IsCauchyLabel, args, registry)
        super().__init__(inputs=Pair(seq, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class RealNum(Edge):
    def __init__(self, seq, registry):
        args = Pair(seq, EmptyList)
        self.result = _construct_or_reuse(RealNumLabel, args, registry)
        super().__init__(inputs=Pair(seq, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsReal(Edge):
    def __init__(self, x, registry):
        args = Pair(x, EmptyList)
        self.result = _construct_or_reuse(IsRealLabel, args, registry)
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Sqrt(Edge):
    def __init__(self, a, registry):
        args = Pair(a, EmptyList)
        self.result = _construct_or_reuse(SqrtLabel, args, registry)
        super().__init__(inputs=Pair(a, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SqrtSeq(Edge):
    def __init__(self, a, registry):
        n_name = Thingy()
        n = Pair(VarTag, Pair(n_name, EmptyList))
        name = Pair(SqrtLabel, Pair(a, EmptyList))
        x_n = Pair(name, Pair(n, EmptyList))
        succ_n = Pair(SuccLabel, Pair(n, EmptyList))
        a_over_x_n = Pair(ExprFracLabel, Pair(a, Pair(x_n, EmptyList)))
        summed = Pair(ExprAddLabel, Pair(x_n, Pair(a_over_x_n, EmptyList)))
        step_expr = Pair(ExprFracLabel, Pair(summed, Pair(two, EmptyList)))
        self.result = Sequence(name, a, Pair(name, Pair(succ_n, EmptyList)), step_expr, registry)()
        super().__init__(inputs=Pair(a, Pair(registry, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
