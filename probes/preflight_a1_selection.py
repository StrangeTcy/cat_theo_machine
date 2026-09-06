import sys
sys.path.insert(0, '/home/user')
import cat_theo_machine.machine as M
import cat_theo_machine.labels as Lmod
import cat_theo_machine.proof as Pmod
from cat_theo_machine import knowledge as Kmod

registry = M.AllConstructors
empty = M.EmptyList

def var(n):
    return M.Pair(M.VarTag, M.Pair(M.Char(n), empty))
def expr(label, *args):
    chain = empty
    for a in reversed(args):
        chain = M.Pair(a, chain)
    return M.Pair(label, chain)

a, b, c, x = var("?a"), var("?b"), var("?c"), var("?x")
E, A, R = Lmod.ExprEqLabel, Lmod.ExprAddLabel, Lmod.IsRealLabel

toy_goal = expr(E, expr(A, x, M.one), x)
producer = Pmod.MultiRule(
    M.Pair(expr(E, a, b), M.Pair(expr(R, b), empty)),
    expr(E, b, a),
)
consumer = Pmod.MultiRule(
    M.Pair(expr(E, a, b), M.Pair(expr(E, b, c), empty)),
    expr(E, a, c),
)

g1 = expr(E, expr(A, M.two, M.one), M.two)   # ground instance of toy shape, x = two
g2 = expr(R, M.two)
facts = M.Pair(g1, M.Pair(g2, empty))

def safe_walk(chain):
    out, cur, n = [], chain, 0
    while cur is not None and n < 20:
        try:
            same = M.IdentityCompare(cur, empty)() is M.truth_value
        except Exception:
            same = False
        if same:
            break
        try:
            out.append(M.Head(cur)())
        except Exception as e:
            out.append("HEAD-ERR " + type(e).__name__)
            break
        try:
            cur = M.Tail(cur)()
        except Exception:
            cur = None
        n += 1
    return out

pj = Pmod.JoinPremises(Pmod.RulePremises(producer)(), facts, empty)()
psets = safe_walk(pj)
print("producer JoinPremises binding-sets:", len(psets))

cj = Pmod.JoinPremises(Pmod.RulePremises(consumer)(), M.Pair(expr(E, M.two, M.two), M.Pair(expr(E, M.two, M.three), empty)), empty)()
csets = safe_walk(cj)
print("consumer JoinPremises binding-sets:", len(csets))

state = Pmod.Knowledge(facts)()
if psets:
    binding = psets[0] if not isinstance(psets[0], str) else None
    if binding is not None:
        nxt = Pmod.ApplyKnowledgeRewrite(state, producer, binding)()
        newfacts = Pmod.KnowledgeFacts(nxt)()
        nf = safe_walk(newfacts)
        print("new board size:", len(nf))
        for t in nf:
            try:
                print("  fact:", M.PrettyTerm(t, registry)())
            except Exception as e:
                print("  fact print err:", type(e).__name__)

expected_fired = expr(E, M.two, expr(A, M.two, M.one))
nf = safe_walk(Pmod.KnowledgeFacts(nxt)())
hits = 0
eq_head = 0
for t in nf:
    try:
        if M.IdentityCompare(M.Head(t)(), E)() is M.truth_value:
            eq_head += 1
        if M.Compare(t, expected_fired)() is M.truth_value:
            hits += 1
    except Exception:
        pass
print("facts with ExprEq head:", eq_head)
print("structural match to Eq(two, 2+1):", hits)
print("toy goal head == ExprEq:", M.IdentityCompare(M.Head(toy_goal)(), E)() is M.truth_value)

print("=== binding inspection ===")
bl = safe_walk(binding)
print("binding pairs:", len(bl))
for item in bl:
    try:
        varname = M.Head(M.Head(item)())()
        val = M.Head(M.Tail(item)())()
        print("  ", varname, "->", M.PrettyTerm(val, registry)())
    except Exception as e:
        print("  pair inspect err:", type(e).__name__, repr(item)[:60])
repl = Pmod.RuleReplacement(producer)()
inst = M.Instantiate(repl, binding)()
print("manual Instantiate(replacement, binding):", M.PrettyTerm(inst, registry)())
print("manual instantiate == expected:", M.Compare(inst, expected_fired)() is M.truth_value)

print("=== decisive board comparison ===")
fired_fact = M.Head(inst)()
print("fired fact pretty:", M.PrettyTerm(fired_fact, registry)())
print("fired == Eq(two, Add(two, one)):", M.Compare(fired_fact, expected_fired)() is M.truth_value)
board = Pmod.KnowledgeFacts(nxt)()
expected_board = M.Pair(fired_fact, empty)
print("board == [fired] exactly:", M.Compare(board, expected_board)() is M.truth_value)
