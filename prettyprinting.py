from __future__ import annotations

from . import constructors as C
from .core import Edge, EmptyList, Head, IdentityCompare, Pair, Tail, Zero
from .gmprep import GMPRepText
from .labels import (
    AlgebraicApproachLabel,
    AnglesLabel,
    AreaFormulaAvailableLabel,
    AreaLabel,
    ArithmeticProgressionLabel,
    CosineLabel,
    CommonDifferenceLabel,
    CommonDifferenceGivenLabel,
    CommonDifferenceParameterLabel,
    CosineRuleAvailableLabel,
    ExprAddLabel,
    ExprDivLabel,
    ExprEqLabel,
    ExprFracLabel,
    ExprIntLabel,
    ExprLtLabel,
    ExprMulLabel,
    ExprNegLabel,
    ExprPowLabel,
    FirstAngleLabel,
    FirstEdgeLabel,
    FractionLabel,
    GivenLabel,
    GeometryFactLabel,
    HeronFormulaAvailableLabel,
    EdgesLabel,
    IsCauchyLabel,
    IsRealLabel,
    KnowledgeLabel,
    LengthLabel,
    LimitLabel,
    MachineContextLabel,
    MiddleTermAverageLabel,
    NeedLabel,
    NewtonErrorIdentityLabel,
    NewtonErrorShrinksLabel,
    NewtonPositiveLabel,
    NewtonStepTermLabel,
    ParameterLabel,
    PhysicalConstraintsKnownLabel,
    PositiveLabel,
    PolygonLabel,
    RealNumLabel,
    SequenceLabel,
    SideLengthsLabel,
    SineLabel,
    SineRuleAvailableLabel,
    NonNegativeLabel,
    SolvedLabel,
    SymmetricProgressionNotationLabel,
    SqrtLabel,
    SqrtSeqCauchyLabel,
    SqrtSeqTermLabel,
    SuccLabel,
    TaoProblem11TriangleLabel,
    TaoProblem11VertexULabel,
    TaoProblem11VertexVLabel,
    TaoProblem11VertexWLabel,
    TaoProblem11BaseValueLabel,
    TaoProblem11DifferenceValueLabel,
    TaoProblem11AreaValueLabel,
    TaoProblem11AlphaValueLabel,
    TaoProblem11BetaValueLabel,
    TaoProblem11GammaValueLabel,
    DistinctLabel,
    VertexOfLabel,
    SegmentLabel,
    AngleLabel,
    SideOfLabel,
    AngleOfLabel,
    OppositeLabel,
    AngleMeasureLabel,
    APNameLabel,
    ApplyLabel,
    PerimeterLabel,
    ArccosLabel,
    TaoProblem11PerimeterValueLabel,
    TestFailLabel,
    TestNameLabel,
    TestOKLabel,
    ThirdEdgeLabel,
    ThirdAngleLabel,
    TriangleInequalityAvailableLabel,
    TriangleLabel,
    SecondAngleLabel,
    SecondEdgeLabel,
    EvaluateProblemLabel,
    VerticesLabel,
    WholeLabel,
)
from .logic import false_value, truth_value
from .math.peano import NatEq, NatRepOf


def _machine_module():
    from . import machine as M

    return M


def _proof_module():
    from . import proof as Pmod

    return Pmod


class AtomName(Edge):
    def __init__(self, a):
        self.result = self._name(a)
        super().__init__(inputs=Pair(a, EmptyList), results=EmptyList)

    def _name(self, a):
        if C.Compare(a, Zero)() is truth_value:
            return "Zero"
        if IdentityCompare(a, GeometryFactLabel)() is truth_value:
            return "GeometryFact"
        if IdentityCompare(a, TaoProblem11TriangleLabel)() is truth_value:
            return "TaoProblem1.1Triangle"
        class_name = a.__class__.__name__
        if class_name == "GeometryFactLabel":
            return "GeometryFact"
        if class_name == "TaoProblem11TriangleLabel":
            return "TaoProblem1.1Triangle"
        c = C.GetConstructor(a)()
        if C.Compare(c, EmptyList)() is truth_value:
            val = a()
            return val if val is not None else "<?>"
        label = Head(c)()
        args = Tail(c)()
        if IdentityCompare(label, SuccLabel)() is truth_value:
            return "Succ(" + self._name(Head(args)()) + ")"
        if IdentityCompare(label, TestOKLabel)() is truth_value:
            return "TestOK"
        if IdentityCompare(label, TestFailLabel)() is truth_value:
            return "TestFail"
        if IdentityCompare(label, TestNameLabel)() is truth_value:
            return self._name(Head(args)())
        return "<?>"

    def __call__(self):
        return self.result


class NatText(Edge):
    def __init__(self, x):
        self.result = Pair(self._text(x), EmptyList)
        super().__init__(inputs=Pair(x, EmptyList), results=self.result)

    def _text(self, x):
        rep = NatRepOf(x, C.AllConstructors)()
        if IdentityCompare(rep, EmptyList)() is truth_value:
            return Head(AtomName(x)())()
        return GMPRepText(rep)()

    def __call__(self):
        return self.result


class FractionText(Edge):
    def __init__(self, x, registry):
        self.registry = registry
        self.result = Pair(self._text(x), EmptyList)
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def _text(self, x):
        M = _machine_module()
        a = M.FractionLeft(x, self.registry)()
        b = M.FractionRight(x, self.registry)()
        return Head(NatText(a)())() + " / " + Head(NatText(b)())()

    def __call__(self):
        return self.result


class WholeText(Edge):
    def __init__(self, x, registry):
        self.registry = registry
        self.result = Pair(self._text(x), EmptyList)
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=self.result)

    def _text(self, x):
        M = _machine_module()
        a = M.WholeLeft(x, self.registry)()
        b = M.WholeRight(x, self.registry)()
        a_text = Head(NatText(a)())()
        b_text = Head(NatText(b)())()
        if C.Compare(b, Zero)() is truth_value:
            return a_text
        if C.Compare(a, Zero)() is truth_value:
            return "-" + b_text
        return a_text + " - " + b_text

    def __call__(self):
        return self.result


class PrettyValue(Edge):
    def __init__(self, x, registry):
        self.registry = registry
        self.result = self._pretty(x)
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=EmptyList)

    def _pretty(self, x):
        M = _machine_module()
        if C.Compare(x, EmptyList)() is truth_value:
            return "[]"
        if M.IsFraction(x, self.registry)() is truth_value:
            return Head(FractionText(x, self.registry)())()
        if M.IsWhole(x, self.registry)() is truth_value:
            return Head(WholeText(x, self.registry)())()
        return AtomName(x)()

    def __call__(self):
        return self.result


class PrettyPair(Edge):
    def __init__(self, p, registry):
        self.registry = registry
        self.result = "[" + self._walk(p) + "]"
        super().__init__(inputs=Pair(p, Pair(registry, EmptyList)), results=EmptyList)

    def _show(self, x):
        return PrettyValue(x, self.registry)()

    def _is_pair(self, x):
        M = _machine_module()
        return M.IsPair(x)()

    def _is_2tuple(self, x):
        if self._is_pair(x) is not truth_value:
            return false_value
        t1 = Tail(x)()
        if self._is_pair(t1) is not truth_value:
            return false_value
        t2 = Tail(t1)()
        if C.Compare(t2, EmptyList)() is truth_value:
            return truth_value
        return false_value

    def _walk(self, node):
        if C.Compare(node, EmptyList)() is truth_value:
            return ""
        if self._is_pair(node) is not truth_value:
            return self._show(node)
        h = Head(node)()
        t = Tail(node)()
        if self._is_2tuple(h) is truth_value:
            a = Head(h)()
            b = Head(Tail(h)())()
            h_str = "(" + self._show(a) + ", " + self._show(b) + ")"
        else:
            h_str = self._show(h)
        if C.Compare(t, EmptyList)() is truth_value:
            return h_str
        return h_str + ", " + self._walk(t)

    def __call__(self):
        return self.result


class PrettyTerm(Edge):
    def __init__(self, x, registry):
        self.registry = registry
        self.result = self._show(x)
        super().__init__(inputs=Pair(x, Pair(registry, EmptyList)), results=EmptyList)

    def _nat_value(self, x):
        M = _machine_module()
        rep = NatRepOf(x, self.registry)()
        if IdentityCompare(rep, EmptyList)() is false_value:
            return GMPRepText(rep)()
        if NatEq(x, Zero, self.registry)() is truth_value:
            return "0"
        if NatEq(x, M.one, self.registry)() is truth_value:
            return "1"
        if NatEq(x, M.two, self.registry)() is truth_value:
            return "2"
        if NatEq(x, M.three, self.registry)() is truth_value:
            return "3"
        if NatEq(x, M.four, self.registry)() is truth_value:
            return "4"
        if NatEq(x, M.five, self.registry)() is truth_value:
            return "5"
        if NatEq(x, M.six, self.registry)() is truth_value:
            return "6"
        if NatEq(x, M.seven, self.registry)() is truth_value:
            return "7"
        if NatEq(x, M.eight, self.registry)() is truth_value:
            return "8"
        if NatEq(x, M.nine, self.registry)() is truth_value:
            return "9"
        return None

    def _list_like(self, L):
        M = _machine_module()
        if C.Compare(L, EmptyList)() is truth_value:
            return ""
        if M.IsPair(L)() is false_value:
            return self._show(L)
        h = Head(L)()
        t = Tail(L)()
        if C.Compare(t, EmptyList)() is truth_value:
            return self._show(h)
        return self._show(h) + ", " + self._list_like(t)

    def _show_args(self, args):
        return self._list_like(args)

    def _geometry_tag_key(self, tag):
        M = _machine_module()
        if C.Compare(tag, EmptyList)() is truth_value:
            return ""
        if M.IsPair(tag)() is false_value:
            return None
        head_text = self._nat_value(Head(tag)())
        if head_text is None:
            return None
        rest_text = self._geometry_tag_key(Tail(tag)())
        if rest_text is None:
            return None
        if rest_text == "":
            return head_text
        return head_text + "," + rest_text

    def _geometry_tag_text(self, tag):
        tag_key = self._geometry_tag_key(tag)
        if tag_key == "1":
            return "triangle"
        if tag_key == "2":
            return "sides are in arithmetic progression"
        if tag_key == "3":
            return "an arithmetic-progression difference is given"
        if tag_key == "4":
            return "the triangle area is given"
        if tag_key == "5":
            return "the arithmetic-progression difference is treated as a parameter"
        if tag_key == "6":
            return "the triangle area is treated as a parameter"
        if tag_key == "7":
            return "this is an evaluate-type problem"
        if tag_key == "8":
            return "an algebraic approach is preferred"
        if tag_key == "9":
            return "the sine rule is available"
        if tag_key == "1,0":
            return "the cosine rule is available"
        if tag_key == "1,1":
            return "the area formula is available"
        if tag_key == "1,2":
            return "Heron's formula is available"
        if tag_key == "1,3":
            return "the triangle's physical constraints are known"
        if tag_key == "1,4":
            return "the triangle inequality is available"
        if tag_key == "2,0":
            return "use symmetric arithmetic-progression notation around the middle side"
        if tag_key == "2,1":
            return "the middle side is the average of the other two"
        if tag_key == "3,0":
            return "only the side lengths matter"
        if tag_key == "3,1":
            return "only the middle side needs to be solved"
        if tag_key == "4,0":
            return "the semiperimeter is determined by the middle side"
        if tag_key == "4,1":
            return "Heron's formula yields the key area equation"
        if tag_key == "4,2":
            return "the key equation becomes quadratic in the middle-side square"
        if tag_key == "5,0":
            return "the middle side length is solved"
        if tag_key == "5,1":
            return "all side lengths are solved"
        if tag_key == "6,0":
            return "the angles can be recovered"
        if tag_key == "6,1":
            return "the angles are solved"
        if tag_key == "7,0":
            return "the full problem is solved"
        return self._show(tag)

    def _scoped_fact_text(self, problem, text):
        return self._show(problem) + ": " + text

    def _geometry_fact_text(self, problem, tag):
        return self._scoped_fact_text(problem, self._geometry_tag_text(tag))

    def _arithmetic_label_text(self, label):
        if IdentityCompare(label, ArithmeticProgressionLabel)() is truth_value:
            return "arithmetic progression"
        if IdentityCompare(label, CommonDifferenceGivenLabel)() is truth_value:
            return "common difference is given"
        if IdentityCompare(label, CommonDifferenceParameterLabel)() is truth_value:
            return "common difference is treated as a parameter"
        if IdentityCompare(label, SymmetricProgressionNotationLabel)() is truth_value:
            return "use symmetric progression notation"
        if IdentityCompare(label, MiddleTermAverageLabel)() is truth_value:
            return "the middle term is the average of the outer terms"
        label_class_name = label.__class__.__name__
        if label_class_name == "ArithmeticProgressionLabel":
            return "arithmetic progression"
        if label_class_name == "CommonDifferenceGivenLabel":
            return "common difference is given"
        if label_class_name == "CommonDifferenceParameterLabel":
            return "common difference is treated as a parameter"
        if label_class_name == "SymmetricProgressionNotationLabel":
            return "use symmetric progression notation"
        if label_class_name == "MiddleTermAverageLabel":
            return "the middle term is the average of the outer terms"
        return None

    def _generic_unary_constructor_name(self, label):
        if IdentityCompare(label, ArithmeticProgressionLabel)() is truth_value:
            return "ArithmeticProgression"
        if IdentityCompare(label, SymmetricProgressionNotationLabel)() is truth_value:
            return "SymmetricProgressionNotation"
        if IdentityCompare(label, MiddleTermAverageLabel)() is truth_value:
            return "MiddleTermAverage"
        if IdentityCompare(label, PolygonLabel)() is truth_value:
            return "Polygon"
        if IdentityCompare(label, EdgesLabel)() is truth_value:
            return "Edges"
        if IdentityCompare(label, VerticesLabel)() is truth_value:
            return "Vertices"
        if IdentityCompare(label, TriangleLabel)() is truth_value:
            return "Triangle"
        if IdentityCompare(label, GivenLabel)() is truth_value:
            return "Given"
        if IdentityCompare(label, NeedLabel)() is truth_value:
            return "Need"
        if IdentityCompare(label, ParameterLabel)() is truth_value:
            return "Parameter"
        if IdentityCompare(label, SolvedLabel)() is truth_value:
            return "Solved"
        if IdentityCompare(label, PositiveLabel)() is truth_value:
            return "Positive"
        if IdentityCompare(label, NonNegativeLabel)() is truth_value:
            return "NonNegative"
        if IdentityCompare(label, AreaLabel)() is truth_value:
            return "Area"
        if IdentityCompare(label, SideLengthsLabel)() is truth_value:
            return "SideLengths"
        if IdentityCompare(label, AnglesLabel)() is truth_value:
            return "Angles"
        if IdentityCompare(label, LengthLabel)() is truth_value:
            return "Length"
        if IdentityCompare(label, FirstAngleLabel)() is truth_value:
            return "FirstAngle"
        if IdentityCompare(label, FirstEdgeLabel)() is truth_value:
            return "FirstEdge"
        if IdentityCompare(label, SecondEdgeLabel)() is truth_value:
            return "SecondEdge"
        if IdentityCompare(label, ThirdEdgeLabel)() is truth_value:
            return "ThirdEdge"
        if IdentityCompare(label, SecondAngleLabel)() is truth_value:
            return "SecondAngle"
        if IdentityCompare(label, ThirdAngleLabel)() is truth_value:
            return "ThirdAngle"
        if IdentityCompare(label, CommonDifferenceLabel)() is truth_value:
            return "CommonDifference"
        if IdentityCompare(label, SineLabel)() is truth_value:
            return "Sine"
        if IdentityCompare(label, CosineLabel)() is truth_value:
            return "Cosine"
        if IdentityCompare(label, SineRuleAvailableLabel)() is truth_value:
            return "SineRuleAvailable"
        if IdentityCompare(label, CosineRuleAvailableLabel)() is truth_value:
            return "CosineRuleAvailable"
        if IdentityCompare(label, AreaFormulaAvailableLabel)() is truth_value:
            return "AreaFormulaAvailable"
        if IdentityCompare(label, HeronFormulaAvailableLabel)() is truth_value:
            return "HeronFormulaAvailable"
        if IdentityCompare(label, TriangleInequalityAvailableLabel)() is truth_value:
            return "TriangleInequalityAvailable"
        if IdentityCompare(label, PhysicalConstraintsKnownLabel)() is truth_value:
            return "PhysicalConstraintsKnown"
        if IdentityCompare(label, EvaluateProblemLabel)() is truth_value:
            return "EvaluateProblem"
        if IdentityCompare(label, AlgebraicApproachLabel)() is truth_value:
            return "AlgebraicApproach"
        if IdentityCompare(label, DistinctLabel)() is truth_value:
            return "Distinct"
        if IdentityCompare(label, VertexOfLabel)() is truth_value:
            return "VertexOf"
        if IdentityCompare(label, SegmentLabel)() is truth_value:
            return "Segment"
        if IdentityCompare(label, AngleLabel)() is truth_value:
            return "Angle"
        if IdentityCompare(label, SideOfLabel)() is truth_value:
            return "SideOf"
        if IdentityCompare(label, AngleOfLabel)() is truth_value:
            return "AngleOf"
        if IdentityCompare(label, OppositeLabel)() is truth_value:
            return "Opposite"
        if IdentityCompare(label, AngleMeasureLabel)() is truth_value:
            return "AngleMeasure"
        if IdentityCompare(label, APNameLabel)() is truth_value:
            return "APName"
        if IdentityCompare(label, ApplyLabel)() is truth_value:
            return "Apply"
        if IdentityCompare(label, PerimeterLabel)() is truth_value:
            return "Perimeter"
        if IdentityCompare(label, ArccosLabel)() is truth_value:
            return "arccos"
        label_class_name = label.__class__.__name__
        if label_class_name == "ArithmeticProgressionLabel":
            return "ArithmeticProgression"
        if label_class_name == "SymmetricProgressionNotationLabel":
            return "SymmetricProgressionNotation"
        if label_class_name == "MiddleTermAverageLabel":
            return "MiddleTermAverage"
        if label_class_name == "PolygonLabel":
            return "Polygon"
        if label_class_name == "EdgesLabel":
            return "Edges"
        if label_class_name == "VerticesLabel":
            return "Vertices"
        if label_class_name == "TriangleLabel":
            return "Triangle"
        if label_class_name == "GivenLabel":
            return "Given"
        if label_class_name == "NeedLabel":
            return "Need"
        if label_class_name == "ParameterLabel":
            return "Parameter"
        if label_class_name == "SolvedLabel":
            return "Solved"
        if label_class_name == "PositiveLabel":
            return "Positive"
        if label_class_name == "NonNegativeLabel":
            return "NonNegative"
        if label_class_name == "AreaLabel":
            return "Area"
        if label_class_name == "SideLengthsLabel":
            return "SideLengths"
        if label_class_name == "AnglesLabel":
            return "Angles"
        if label_class_name == "LengthLabel":
            return "Length"
        if label_class_name == "FirstAngleLabel":
            return "FirstAngle"
        if label_class_name == "FirstEdgeLabel":
            return "FirstEdge"
        if label_class_name == "SecondEdgeLabel":
            return "SecondEdge"
        if label_class_name == "ThirdEdgeLabel":
            return "ThirdEdge"
        if label_class_name == "SecondAngleLabel":
            return "SecondAngle"
        if label_class_name == "ThirdAngleLabel":
            return "ThirdAngle"
        if label_class_name == "CommonDifferenceLabel":
            return "CommonDifference"
        if label_class_name == "SineLabel":
            return "Sine"
        if label_class_name == "CosineLabel":
            return "Cosine"
        if label_class_name == "SineRuleAvailableLabel":
            return "SineRuleAvailable"
        if label_class_name == "CosineRuleAvailableLabel":
            return "CosineRuleAvailable"
        if label_class_name == "AreaFormulaAvailableLabel":
            return "AreaFormulaAvailable"
        if label_class_name == "HeronFormulaAvailableLabel":
            return "HeronFormulaAvailable"
        if label_class_name == "TriangleInequalityAvailableLabel":
            return "TriangleInequalityAvailable"
        if label_class_name == "PhysicalConstraintsKnownLabel":
            return "PhysicalConstraintsKnown"
        if label_class_name == "EvaluateProblemLabel":
            return "EvaluateProblem"
        if label_class_name == "AlgebraicApproachLabel":
            return "AlgebraicApproach"
        return None

    def _generic_unary_text(self, label, arg):
        name = self._generic_unary_constructor_name(label)
        if name is None:
            return None
        return name + "(" + self._show(arg) + ")"

    def _geometry_fact_parts(self, x):
        M = _machine_module()
        if M.IsPair(x)() is false_value:
            return None
        head = Head(x)()
        tail = Tail(x)()
        if M.IsPair(tail)() is false_value:
            return None
        if IdentityCompare(head, GeometryFactLabel)() is truth_value:
            return Pair(Head(tail)(), Pair(Head(Tail(tail)())(), EmptyList))
        head_class_name = head.__class__.__name__
        if head_class_name == "GeometryFactLabel":
            return Pair(Head(tail)(), Pair(Head(Tail(tail)())(), EmptyList))
        ctor = C.GetConstructor(x, self.registry)()
        if IdentityCompare(ctor, EmptyList)() is truth_value:
            return None
        label = Head(ctor)()
        args = Tail(ctor)()
        if IdentityCompare(label, GeometryFactLabel)() is truth_value:
            return Pair(Head(args)(), Pair(Head(Tail(args)())(), EmptyList))
        label_class_name = label.__class__.__name__
        if label_class_name == "GeometryFactLabel":
            return Pair(Head(args)(), Pair(Head(Tail(args)())(), EmptyList))
        return None

    def _geometry_fact_problem(self, fact):
        parts = self._geometry_fact_parts(fact)
        if parts is None:
            return None
        return Head(parts)()

    def _geometry_fact_tag(self, fact):
        parts = self._geometry_fact_parts(fact)
        if parts is None:
            return None
        return Head(Tail(parts)())()

    def _unary_scoped_fact_problem(self, fact):
        M = _machine_module()
        if M.IsPair(fact)() is truth_value:
            head = Head(fact)()
            text = self._arithmetic_label_text(head)
            if text is not None:
                tail = Tail(fact)()
                if M.IsPair(tail)() is truth_value and C.Compare(Tail(tail)(), EmptyList)() is truth_value:
                    return Head(tail)()
        ctor = C.GetConstructor(fact, self.registry)()
        if IdentityCompare(ctor, EmptyList)() is truth_value:
            return None
        label = Head(ctor)()
        if self._arithmetic_label_text(label) is None:
            return None
        args = Tail(ctor)()
        return Head(args)()

    def _unary_scoped_fact_text(self, fact):
        M = _machine_module()
        if M.IsPair(fact)() is truth_value:
            text = self._arithmetic_label_text(Head(fact)())
            if text is not None:
                return text
        ctor = C.GetConstructor(fact, self.registry)()
        if IdentityCompare(ctor, EmptyList)() is truth_value:
            return None
        return self._arithmetic_label_text(Head(ctor)())

    def _scoped_fact_problem(self, fact):
        geometry_problem = self._geometry_fact_problem(fact)
        if geometry_problem is not None:
            return geometry_problem
        return self._unary_scoped_fact_problem(fact)

    def _scoped_fact_phrase(self, fact):
        geometry_tag = self._geometry_fact_tag(fact)
        if geometry_tag is not None:
            return self._geometry_tag_text(geometry_tag)
        return self._unary_scoped_fact_text(fact)

    def _scoped_knowledge_problem(self, facts):
        M = _machine_module()
        if C.Compare(facts, EmptyList)() is truth_value:
            return None
        first_fact = Head(facts)()
        problem = self._scoped_fact_problem(first_fact)
        if problem is None:
            return None
        remaining = Tail(facts)()
        while C.Compare(remaining, EmptyList)() is false_value:
            next_fact = Head(remaining)()
            next_problem = self._scoped_fact_problem(next_fact)
            if next_problem is None:
                return None
            if IdentityCompare(next_problem, problem)() is false_value:
                return None
            remaining = Tail(remaining)()
        return problem

    def _scoped_knowledge_facts_text(self, facts):
        if C.Compare(facts, EmptyList)() is truth_value:
            return ""
        fact = Head(facts)()
        here = self._scoped_fact_phrase(fact)
        rest = Tail(facts)()
        if C.Compare(rest, EmptyList)() is truth_value:
            return here
        return here + ", " + self._scoped_knowledge_facts_text(rest)

    def _knowledge_text(self, facts):
        problem = self._scoped_knowledge_problem(facts)
        if problem is not None:
            return "Knowledge(" + self._show(problem) + ": [" + self._scoped_knowledge_facts_text(facts) + "])"
        return "Knowledge([" + self._list_like(facts) + "])"

    def _raw_application(self, x):
        M = _machine_module()
        if M.IsPair(x)() is false_value:
            return None
        head = Head(x)()
        tail = Tail(x)()
        if M.IsPair(tail)() is false_value and C.Compare(tail, EmptyList)() is false_value:
            return None
        constructor_name = self._generic_unary_constructor_name(head)
        if constructor_name is not None:
            return constructor_name + "(" + self._show_args(tail) + ")"
        if IdentityCompare(head, SqrtLabel)() is truth_value:
            return "sqrt(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, SqrtSeqTermLabel)() is truth_value:
            return "SqrtSeq(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, NewtonStepTermLabel)() is truth_value:
            return "NewtonStep(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, NewtonPositiveLabel)() is truth_value:
            return "NewtonPositive(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, NewtonErrorIdentityLabel)() is truth_value:
            return "NewtonErrorIdentity(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, NewtonErrorShrinksLabel)() is truth_value:
            return "NewtonErrorShrinks(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, SqrtSeqCauchyLabel)() is truth_value:
            return "SqrtSeqCauchy(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, IsCauchyLabel)() is truth_value:
            return "IsCauchy(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, RealNumLabel)() is truth_value:
            return "RealNum(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, IsRealLabel)() is truth_value:
            return "IsReal(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, SineLabel)() is truth_value:
            return "sin(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, CosineLabel)() is truth_value:
            return "cos(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, ArccosLabel)() is truth_value:
            return "arccos(" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, LimitLabel)() is truth_value:
            return "Limit(" + self._show(Head(tail)()) + ", " + self._show(Head(Tail(tail)())()) + ")"
        if IdentityCompare(head, ExprAddLabel)() is truth_value:
            return "(" + self._show(Head(tail)()) + " + " + self._show(Head(Tail(tail)())()) + ")"
        if IdentityCompare(head, ExprMulLabel)() is truth_value:
            return "(" + self._show(Head(tail)()) + " * " + self._show(Head(Tail(tail)())()) + ")"
        if IdentityCompare(head, ExprFracLabel)() is truth_value:
            return "(" + self._show(Head(tail)()) + " / " + self._show(Head(Tail(tail)())()) + ")"
        if IdentityCompare(head, ExprDivLabel)() is truth_value:
            return "(" + self._show(Head(tail)()) + " div " + self._show(Head(Tail(tail)())()) + ")"
        if IdentityCompare(head, ExprPowLabel)() is truth_value:
            return "(" + self._show(Head(tail)()) + "^" + self._show(Head(Tail(tail)())()) + ")"
        if IdentityCompare(head, ExprNegLabel)() is truth_value:
            return "(-" + self._show(Head(tail)()) + ")"
        if IdentityCompare(head, ExprEqLabel)() is truth_value:
            return "(" + self._show(Head(tail)()) + " = " + self._show(Head(Tail(tail)())()) + ")"
        if IdentityCompare(head, ExprLtLabel)() is truth_value:
            return "(" + self._show(Head(tail)()) + " < " + self._show(Head(Tail(tail)())()) + ")"
        if IdentityCompare(head, ExprIntLabel)() is truth_value:
            return self._show(Head(tail)())
        if IdentityCompare(head, FractionLabel)() is truth_value:
            return self._show(Head(tail)()) + "/" + self._show(Head(Tail(tail)())())
        if IdentityCompare(head, WholeLabel)() is truth_value:
            return "Whole(" + self._show(Head(tail)()) + ", " + self._show(Head(Tail(tail)())()) + ")"
        if IdentityCompare(head, SequenceLabel)() is truth_value:
            return "Sequence(" + self._show_args(tail) + ")"
        if IdentityCompare(head, KnowledgeLabel)() is truth_value:
            return self._knowledge_text(Head(tail)())
        arithmetic_text = self._arithmetic_label_text(head)
        if arithmetic_text is not None:
            return self._scoped_fact_text(Head(tail)(), arithmetic_text)
        if IdentityCompare(head, GeometryFactLabel)() is truth_value:
            problem = Head(tail)()
            tag = Head(Tail(tail)())()
            return self._geometry_fact_text(problem, tag)
        head_class_name = head.__class__.__name__
        if head_class_name == "KnowledgeLabel":
            return self._knowledge_text(Head(tail)())
        if self._arithmetic_label_text(head) is not None:
            return self._scoped_fact_text(Head(tail)(), self._arithmetic_label_text(head))
        if head_class_name == "GeometryFactLabel":
            problem = Head(tail)()
            tag = Head(Tail(tail)())()
            return self._geometry_fact_text(problem, tag)
        if IdentityCompare(head, MachineContextLabel)() is truth_value:
            return "Context(...)"
        return None

    def _show_constructor_term(self, x):
        c = C.GetConstructor(x, self.registry)()
        if IdentityCompare(c, EmptyList)() is truth_value:
            return None
        label = Head(c)()
        args = Tail(c)()
        if IdentityCompare(label, SqrtLabel)() is truth_value:
            return "sqrt(" + self._show(Head(args)()) + ")"
        if IdentityCompare(label, SequenceLabel)() is truth_value:
            return "Sequence(" + self._show(Head(args)()) + ", ...)"
        if IdentityCompare(label, KnowledgeLabel)() is truth_value:
            return self._knowledge_text(Head(args)())
        if IdentityCompare(label, IsCauchyLabel)() is truth_value:
            return "IsCauchy(" + self._show(Head(args)()) + ")"
        if IdentityCompare(label, RealNumLabel)() is truth_value:
            return "RealNum(" + self._show(Head(args)()) + ")"
        if IdentityCompare(label, IsRealLabel)() is truth_value:
            return "IsReal(" + self._show(Head(args)()) + ")"
        if IdentityCompare(label, LimitLabel)() is truth_value:
            return "Limit(" + self._show(Head(args)()) + ", " + self._show(Head(Tail(args)())()) + ")"
        if IdentityCompare(label, FractionLabel)() is truth_value:
            return self._show(Head(args)()) + "/" + self._show(Head(Tail(args)())())
        if IdentityCompare(label, WholeLabel)() is truth_value:
            return "Whole(" + self._show(Head(args)()) + ", " + self._show(Head(Tail(args)())()) + ")"
        if IdentityCompare(label, TestOKLabel)() is truth_value:
            return "TestOK"
        if IdentityCompare(label, TestFailLabel)() is truth_value:
            return "TestFail"
        if IdentityCompare(label, TestNameLabel)() is truth_value:
            return self._show(Head(args)())
        generic_unary = self._generic_unary_text(label, Head(args)())
        if generic_unary is not None:
            return generic_unary
        arithmetic_text = self._arithmetic_label_text(label)
        if arithmetic_text is not None:
            return self._scoped_fact_text(Head(args)(), arithmetic_text)
        if IdentityCompare(label, GeometryFactLabel)() is truth_value:
            return self._geometry_fact_text(Head(args)(), Head(Tail(args)())())
        label_class_name = label.__class__.__name__
        if label_class_name == "KnowledgeLabel":
            return self._knowledge_text(Head(args)())
        if self._arithmetic_label_text(label) is not None:
            return self._scoped_fact_text(Head(args)(), self._arithmetic_label_text(label))
        if label_class_name == "GeometryFactLabel":
            return self._geometry_fact_text(Head(args)(), Head(Tail(args)())())
        return None

    def _show(self, x):
        M = _machine_module()
        Pmod = _proof_module()
        if C.Compare(x, EmptyList)() is truth_value:
            return "[]"
        nat_val = self._nat_value(x)
        if nat_val is not None:
            return str(nat_val)
        if Pmod.IsVarPattern(x)() is truth_value:
            name = Head(Tail(x)())()
            name_val = name()
            return "?" + str(name_val) if name_val is not None else "?v"
        raw = self._raw_application(x)
        if raw is not None:
            return raw
        ctor = self._show_constructor_term(x)
        if ctor is not None:
            return ctor
        if M.IsPair(x)() is truth_value:
            return "[" + self._list_like(x) + "]"
        if IdentityCompare(x, TaoProblem11TriangleLabel)() is truth_value:
            return "Tao Problem 1.1 triangle"
        if IdentityCompare(x, TaoProblem11VertexULabel)() is truth_value:
            return "u"
        if IdentityCompare(x, TaoProblem11VertexVLabel)() is truth_value:
            return "v"
        if IdentityCompare(x, TaoProblem11VertexWLabel)() is truth_value:
            return "w"
        if IdentityCompare(x, TaoProblem11BaseValueLabel)() is truth_value:
            return "x"
        if IdentityCompare(x, TaoProblem11DifferenceValueLabel)() is truth_value:
            return "d"
        if IdentityCompare(x, TaoProblem11AreaValueLabel)() is truth_value:
            return "A"
        if IdentityCompare(x, TaoProblem11PerimeterValueLabel)() is truth_value:
            return "p"
        if IdentityCompare(x, TaoProblem11AlphaValueLabel)() is truth_value:
            return "alpha"
        if IdentityCompare(x, TaoProblem11BetaValueLabel)() is truth_value:
            return "beta"
        if IdentityCompare(x, TaoProblem11GammaValueLabel)() is truth_value:
            return "gamma"
        if IdentityCompare(x, GeometryFactLabel)() is truth_value:
            return "GeometryFact"
        generic_name = self._generic_unary_constructor_name(x)
        if generic_name is not None:
            return generic_name
        arithmetic_text = self._arithmetic_label_text(x)
        if arithmetic_text is not None:
            return arithmetic_text
        class_name = x.__class__.__name__
        if class_name == "TaoProblem11TriangleLabel":
            return "Tao Problem 1.1 triangle"
        if class_name == "GeometryFactLabel":
            return "GeometryFact"
        if self._generic_unary_constructor_name(x) is not None:
            return self._generic_unary_constructor_name(x)
        if self._arithmetic_label_text(x) is not None:
            return self._arithmetic_label_text(x)
        val = x()
        if val is not None:
            return str(val)
        return "<?>"

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]


def sync_from_namespace(namespace):
    for name in (
        "ArithmeticProgressionLabel",
        "PolygonLabel",
        "EdgesLabel",
        "VerticesLabel",
        "TriangleLabel",
        "GivenLabel",
        "NeedLabel",
        "ParameterLabel",
        "SolvedLabel",
        "PositiveLabel",
        "NonNegativeLabel",
        "AreaLabel",
        "SideLengthsLabel",
        "AnglesLabel",
        "LengthLabel",
        "FirstAngleLabel",
        "FirstEdgeLabel",
        "SecondEdgeLabel",
        "ThirdEdgeLabel",
        "SecondAngleLabel",
        "ThirdAngleLabel",
        "CommonDifferenceLabel",
        "SineLabel",
        "CosineLabel",
        "SineRuleAvailableLabel",
        "CosineRuleAvailableLabel",
        "AreaFormulaAvailableLabel",
        "HeronFormulaAvailableLabel",
        "TriangleInequalityAvailableLabel",
        "PhysicalConstraintsKnownLabel",
        "EvaluateProblemLabel",
        "AlgebraicApproachLabel",
        "CommonDifferenceGivenLabel",
        "CommonDifferenceParameterLabel",
        "EmptyList",
        "Zero",
        "truth_value",
        "false_value",
        "ExprAddLabel",
        "ExprDivLabel",
        "ExprEqLabel",
        "ExprFracLabel",
        "ExprIntLabel",
        "ExprLtLabel",
        "ExprMulLabel",
        "ExprNegLabel",
        "ExprPowLabel",
        "FractionLabel",
        "GeometryFactLabel",
        "IsCauchyLabel",
        "IsRealLabel",
        "KnowledgeLabel",
        "LimitLabel",
        "MachineContextLabel",
        "MiddleTermAverageLabel",
        "NewtonErrorIdentityLabel",
        "NewtonErrorShrinksLabel",
        "NewtonPositiveLabel",
        "NewtonStepTermLabel",
        "RealNumLabel",
        "SequenceLabel",
        "SymmetricProgressionNotationLabel",
        "SqrtLabel",
        "SqrtSeqCauchyLabel",
        "SqrtSeqTermLabel",
        "SuccLabel",
        "TaoProblem11TriangleLabel",
        "TaoProblem11VertexULabel",
        "TaoProblem11VertexVLabel",
        "TaoProblem11VertexWLabel",
        "TaoProblem11BaseValueLabel",
        "TaoProblem11DifferenceValueLabel",
        "TaoProblem11AreaValueLabel",
        "TaoProblem11AlphaValueLabel",
        "TaoProblem11BetaValueLabel",
        "TaoProblem11GammaValueLabel",
        "DistinctLabel",
        "VertexOfLabel",
        "SegmentLabel",
        "AngleLabel",
        "SideOfLabel",
        "AngleOfLabel",
        "OppositeLabel",
        "AngleMeasureLabel",
        "APNameLabel",
        "ApplyLabel",
        "PerimeterLabel",
        "ArccosLabel",
        "TaoProblem11PerimeterValueLabel",
        "TestFailLabel",
        "TestNameLabel",
        "TestOKLabel",
        "WholeLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]
