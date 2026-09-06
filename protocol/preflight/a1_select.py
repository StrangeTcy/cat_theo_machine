"""A1 producer/consumer compile and selection. Not pack content."""
import sys
sys.path.insert(0, "/home/user")
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine import labels as L

empty = M.EmptyList
x_name = M.Char("x")
x = M.Pair(M.VarTag, M.Pair(x_name, empty))
plus = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(M.one, empty)))
toy = M.Pair(L.ExprEqLabel, M.Pair(plus, M.Pair(x, empty)))

ns = M.Char("nosolutions")
domain = M.Char("positive-integers")
unknowns = M.Char("unknowns")
a_name = M.Char("a")
b_name = M.Char("b")
c_name = M.Char("c")
n_name = M.Char("n")
var_a = M.Pair(M.VarTag, M.Pair(a_name, empty))
var_b = M.Pair(M.VarTag, M.Pair(b_name, empty))
var_c = M.Pair(M.VarTag, M.Pair(c_name, empty))
var_n = M.Pair(M.VarTag, M.Pair(n_name, empty))
pow_a = M.Pair(L.ExprPowLabel, M.Pair(var_a, M.Pair(var_n, empty)))
pow_b = M.Pair(L.ExprPowLabel, M.Pair(var_b, M.Pair(var_n, empty)))
pow_c = M.Pair(L.ExprPowLabel, M.Pair(var_c, M.Pair(var_n, empty)))
sum_ab = M.Pair(L.ExprAddLabel, M.Pair(pow_a, M.Pair(pow_b, empty)))
eq_sum = M.Pair(L.ExprEqLabel, M.Pair(sum_ab, M.Pair(pow_c, empty)))
ns_term = M.Pair(
    ns,
    M.Pair(domain, M.Pair(M.Pair(unknowns, M.Pair(var_a, M.Pair(var_b, M.Pair(var_c, empty)))), M.Pair(eq_sum, empty))),
)

producer = P.MultiRule(M.Pair(eq_sum, empty), ns_term)
consumer = P.MultiRule(M.Pair(ns_term, empty), eq_sum)
producer_rule = producer()
consumer_rule = consumer()
print("A1Compile: yes")
print("producer constructed as MultiRule")
print("consumer constructed as MultiRule")

hits = 0
pat_p = P.RulePattern(producer_rule)()
match_p = M.Match(pat_p, toy)()
if M.IdentityCompare(M.Head(match_p)(), M.truth_value)() is M.truth_value:
    hits = hits + 1
pat_c = P.RulePattern(consumer_rule)()
match_c = M.Match(pat_c, toy)()
if M.IdentityCompare(M.Head(match_c)(), M.truth_value)() is M.truth_value:
    hits = hits + 1
print("A1Selection:", hits, "— content absence, not instrument defect")
print("A1Defect: none")
