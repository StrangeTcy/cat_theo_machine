"""Live discovery domains preserve user-selected natural bounds and scope."""

from hyge import machine as M
from hyge import playground as PG
from hyge.runtime import make_fresh_runtime


runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()

# The live input that exposed the fixed-value shortcut must produce {1, 2}.
parsed = PG.ParsePlaygroundDomain(M.Char("yes, 1 to 2"), registry)()
domain = M.Head(parsed)()
fields = M.Tail(parsed)()
lower = M.Head(fields)()
count = M.Head(M.Tail(fields)())()
registry = M.Head(M.Tail(M.Tail(fields)())())()
assert M.NatEq(lower, M.one, registry)() is M.truth_value
assert M.NatEq(count, M.two, registry)() is M.truth_value
assert M.Compare(M.Char(PG.FormatSetChain(domain, registry)()), M.Char("{1, 2}"))() is M.truth_value

# Other values, multi-digit bounds, and spaces use the same grammar.
parsed = PG.ParsePlaygroundDomain(M.Char("  YES, 12  to  14  "), registry)()
domain = M.Head(parsed)()
fields = M.Tail(parsed)()
registry = M.Head(M.Tail(M.Tail(fields)())())()
assert M.Compare(M.Char(PG.FormatSetChain(domain, registry)()), M.Char("{12, 13, 14}"))() is M.truth_value
assert M.NatEq(M.Head(M.Tail(fields)())(), M.three, registry)() is M.truth_value

# Bare ranges also serve the two-prompt `yes` path.
parsed = PG.ParsePlaygroundDomain(M.Char("0 to 0"), registry)()
domain = M.Head(parsed)()
fields = M.Tail(parsed)()
registry = M.Head(M.Tail(M.Tail(fields)())())()
assert M.Compare(M.Char(PG.FormatSetChain(domain, registry)()), M.Char("{0}"))() is M.truth_value
assert M.NatEq(M.Head(fields)(), M.Zero, registry)() is M.truth_value
assert M.NatEq(M.Head(M.Tail(fields)())(), M.one, registry)() is M.truth_value

parsed = PG.ParsePlaygroundDomain(M.Char("try on positive integers from 3 to 5"), registry)()
domain = M.Head(parsed)()
fields = M.Tail(parsed)()
registry = M.Head(M.Tail(M.Tail(fields)())())()
assert M.Compare(M.Char(PG.FormatSetChain(domain, registry)()), M.Char("{3, 4, 5}"))() is M.truth_value

# Empty, negative and decorated numerals must never become zero or lose text.
assert PG.ParsePlaygroundDomain(M.Char("yes, -1 to 2"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes, 0 to -2"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes,  to 2"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes, 1 to "), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes, +1 to 2"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes, 1.0 to 2"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes, 1 to 2 and 3"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes, 1 to 2 to 3"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes, 1e0 to 2"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes, 2 to 1"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("try on positive integers from 0 to 2"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("try on positive integers from -1 to 2"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("no"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char("yes"), registry)() is M.EmptyList
assert PG.ParsePlaygroundDomain(M.Char(""), registry)() is M.EmptyList

print("Live domain regressions passed: arbitrary inclusive bounds, zero/singleton and positive scope, malformed/negative/reversed refusal.")
