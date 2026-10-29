"""Composition of registered definitions with frozen primitive expansion."""

import os
import tempfile

from hyge import machine as M
from hyge import defined_operations as DO
from hyge import labels as L
from hyge import operation_catalog as OC
from hyge import persistence
from hyge import playground as PG
from hyge import runtime


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
    registry = M.FromContextGetConstructors(rt.graph)()
    f = M.Atom()
    f_arg = M.Atom()
    f_formals = M.Pair(f_arg, M.EmptyList)
    square = M.Pair(L.ExprPowLabel, M.Pair(f_arg, M.Pair(M.two, M.EmptyList)))
    f_body = M.Pair(L.ExprAddLabel, M.Pair(square, M.Pair(M.one, M.EmptyList)))
    registered = DO.RegisterDefinedNatOperation(f, f_formals, f_body, registry)()
    assert M.Head(registered)() is M.truth_value
    registry = M.Head(M.Tail(registered)())()
    g = M.Atom()
    x = M.Atom()
    y = M.Atom()
    formals = M.Pair(x, M.Pair(y, M.EmptyList))
    f_call = M.Pair(f, M.Pair(x, M.EmptyList))
    source = M.Pair(L.ExprMulLabel, M.Pair(f_call, M.Pair(y, M.EmptyList)))
    composed = DO.RegisterDefinedNatOperation(g, formals, source, registry)()
    assert M.Head(composed)() is M.truth_value, "an operation cannot yet depend on an earlier registered definition"
    registry = M.Head(M.Tail(composed)())()
