"""Operation tensors stored as nested machine axes, with bounded traversal."""

from . import labels as L
from . import machine as M
from . import playground as PG
from .math import arithmetic as A


class OperationTensorAxes(M.Edge):
    def __init__(self, label, variables, domain, remaining, point, registry, operations):
        rows = M.EmptyList
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            term = M.Pair(label, point)
            call_text = PG.RenderOperationCall(term, M.EmptyList, operations, registry)()
            PG.NaturalPlaygroundDebugEmit(M.Char("Evaluating tensor cell: " + call_text))()
            evaluated = PG.EvaluateNatExpr(term, M.EmptyList, registry, operations)()
            registry = M.Head(M.Tail(evaluated)())()
            value = M.Head(evaluated)()
            rows = M.Pair(value, M.EmptyList)
            PG.NaturalPlaygroundDebugEmit(M.Char(
                "Evaluated tensor cell: " + call_text + " -> "
                + PG.RenderOperationValue(value, registry)()
            ))()
        elif M.IsPair(remaining)() is M.truth_value:
            first = OperationTensorAxes(
                label, M.Tail(variables)(), domain, domain,
                PG.ChainAppendEnd(point, M.Head(remaining)())(), registry, operations,
            )()
            rest = OperationTensorAxes(
                label, variables, domain, M.Tail(remaining)(), point,
                M.Head(M.Tail(first)())(), operations,
            )()
            rows = M.Pair(M.Pair(M.Head(remaining)(), M.Head(first)()), M.Head(rest)())
            registry = M.Head(M.Tail(rest)())()
        self.result = M.Pair(rows, M.Pair(registry, M.EmptyList))
        super().__init__(inputs=M.Pair(label, M.Pair(variables, point)), results=self.result)

    def __call__(self):
        return self.result


class BuildOperationTensorState(M.Edge):
    def __init__(self, domain, operations, registry, all_operations=M.EmptyList):
        tensor = M.EmptyList
        if M.IdentityCompare(all_operations, M.EmptyList)() is M.truth_value:
            all_operations = operations
        if M.IsPair(operations)() is M.truth_value:
            entry = M.Head(operations)()
            variables = M.Head(M.Tail(entry)())()
            label = M.Head(M.Head(M.Tail(M.Tail(entry)())())())()
            axis_domain = domain
            if M.IdentityCompare(label, L.ImpliesLabel)() is M.truth_value:
                axis_domain = M.Pair(M.false_value, M.Pair(M.truth_value, M.EmptyList))
            built = OperationTensorAxes(
                label, variables, axis_domain, axis_domain, M.EmptyList,
                registry, all_operations,
            )()
            registry = M.Head(M.Tail(built)())()
            rest = BuildOperationTensorState(
                domain, M.Tail(operations)(), registry, all_operations,
            )()
            tensor = M.Pair(M.Pair(label, M.Pair(variables, M.Head(built)())), M.Head(rest)())
            registry = M.Head(M.Tail(rest)())()
        self.result = M.Pair(tensor, M.Pair(registry, M.EmptyList))
        super().__init__(inputs=M.Pair(domain, operations), results=self.result)

    def __call__(self):
        return self.result


class OperationTensorRows(M.Edge):
    def __init__(self, tensor, label):
        self.result = M.EmptyList
        if M.IsPair(tensor)() is M.truth_value:
            entry = M.Head(tensor)()
            if M.IdentityCompare(M.Head(entry)(), label)() is M.truth_value:
                self.result = M.Tail(entry)()
            else:
                self.result = OperationTensorRows(M.Tail(tensor)(), label)()
        super().__init__(inputs=M.Pair(tensor, label), results=self.result)

    def __call__(self):
        return self.result


class TensorAxisValue(M.Edge):
    """Read one coordinate per axis; only a complete tuple reaches a cell."""

    def __init__(self, rows, arguments, variables, registry):
        cell = M.EmptyList
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(arguments, M.EmptyList)() is M.truth_value:
                cell = rows
        elif M.IsPair(arguments)() is M.truth_value:
            if M.IsPair(rows)() is M.truth_value:
                row = M.Head(rows)()
                coordinate = M.Head(row)()
                argument = M.Head(arguments)()
                same = M.IdentityCompare(coordinate, argument)()
                if same is M.false_value:
                    if A.IsNat(coordinate, registry)() is M.truth_value:
                        if A.IsNat(argument, registry)() is M.truth_value:
                            same = M.NatEq(coordinate, argument, registry)()
                if same is M.truth_value:
                    cell = TensorAxisValue(
                        M.Tail(row)(), M.Tail(arguments)(), M.Tail(variables)(), registry,
                    )()
                else:
                    cell = TensorAxisValue(M.Tail(rows)(), arguments, variables, registry)()
        self.result = cell
        super().__init__(inputs=M.Pair(rows, M.Pair(arguments, variables)), results=self.result)

    def __call__(self):
        return self.result


class TensorArguments(M.Edge):
    def __init__(self, tensor, arguments, environment, registry):
        values = M.EmptyList
        valid = M.truth_value
        if M.IsPair(arguments)() is M.truth_value:
            first = TensorOperationValue(tensor, M.Head(arguments)(), environment, registry)()
            value = M.Head(first)()
            registry = M.Head(M.Tail(first)())()
            if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                valid = M.false_value
            else:
                rest = TensorArguments(tensor, M.Tail(arguments)(), environment, registry)()
                valid = M.Head(M.Tail(rest)())()
                registry = M.Head(M.Tail(M.Tail(rest)())())()
                if valid is M.truth_value:
                    values = M.Pair(value, M.Head(rest)())
        elif M.IdentityCompare(arguments, M.EmptyList)() is M.false_value:
            valid = M.false_value
        self.result = M.Pair(values, M.Pair(valid, M.Pair(registry, M.EmptyList)))
        super().__init__(inputs=M.Pair(tensor, arguments), results=self.result)

    def __call__(self):
        return self.result


class TensorOperationValue(M.Edge):
    def __init__(self, tensor, term, environment, registry):
        value = M.EmptyList
        if M.IsPair(term)() is M.false_value:
            if A.IsNat(term, registry)() is M.truth_value:
                value = term
            elif M.IdentityCompare(term, M.truth_value)() is M.truth_value:
                value = term
            elif M.IdentityCompare(term, M.false_value)() is M.truth_value:
                value = term
            else:
                value = PG.EnvLookup(environment, term)()
        else:
            label = M.Head(term)()
            arguments = M.Tail(term)()
            if M.IdentityCompare(label, L.ExprIntLabel)() is M.truth_value:
                if PG.ExactArity(arguments, M.one, registry)() is M.truth_value:
                    constant = M.Head(arguments)()
                    if A.IsNat(constant, registry)() is M.truth_value:
                        value = constant
            else:
                evaluated = TensorArguments(tensor, arguments, environment, registry)()
                registry = M.Head(M.Tail(M.Tail(evaluated)())())()
                if M.Head(M.Tail(evaluated)())() is M.truth_value:
                    axes = OperationTensorRows(tensor, label)()
                    if M.IsPair(axes)() is M.truth_value:
                        cell = TensorAxisValue(
                            M.Tail(axes)(), M.Head(evaluated)(), M.Head(axes)(), registry,
                        )()
                        if M.IsPair(cell)() is M.truth_value:
                            value = M.Head(cell)()
        self.result = M.Pair(value, M.Pair(registry, M.EmptyList))
        super().__init__(inputs=M.Pair(tensor, M.Pair(term, environment)), results=self.result)

    def __call__(self):
        return self.result
