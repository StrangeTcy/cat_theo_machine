# ============================================================
# TEST 29: W9 (pack slice) — functional equations & parity algebra
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test29_imo_funceq_parity_pack.py
#
# Slot note (integration, 2026-10-13): this suite was authored on
# arena/500df21f-cat-theo-machine as slot 22, the slot `delegation/README.md`
# pre-allocates to W9. A second, independent W9 suite from
# arena/87d8295b-cat-theo-machine (families 1-3 over graph_task / the miner /
# the ledger) was authored at the same slot. Slots are append-only (DAG §5
# rule 6), so on integration that suite keeps 22 and this one takes the next
# free number, 29. Nothing below the banner lines changed.
#
# Scope, stated honestly. The brief orders three families and allows partial
# coverage with honest claims. On this branch:
#
#   * Family 1 (combinatorial configurations via `graph_task.py`'s
#     ForwardDeriveFacts, `invariant_miner.py`, `curriculum.py`) is OUT OF
#     SCOPE: none of those modules exist on this branch. Not attempted, not
#     claimed.
#   * Family 2 (functional equations) is delivered: the equation is an input
#     fact, the consequences are derived by the generic schemas in
#     `packs/funceq-nt.pack.yaml` -- additive Cauchy down to f(0) = 0,
#     multiplicative Cauchy down to f(1) = 1 under a visible NonTrivial
#     assumption, and the instances at whatever values the instance
#     supplies.
#   * Family 3 (number theory) is delivered as a parity-algebra slice: the
#     machine's own Add / Multiply edges compute the naturals (their
#     constructor chains were verified structurally during development),
#     and the schemas derive which parity a computed sum or product must
#     carry. The machine has no modulo, subtraction or division primitive,
#     so residues beyond mod 2 and divisibility chains are open.
#   * Checker B, the ledger, the evaluator and the curriculum are absent on
#     this branch, so the done-definition's receipt, promotion, ablation and
#     held-out/decoy items are NOT met here and are NOT claimed.
#
# Host layer only below: file paths, timings, counting, printing, and
# calling the machine's own arithmetic edges. Every assertion about the
# machine is Compare / IdentityCompare / IsPair on machine terms; the
# printer resolves names by IdentityCompare against a table of atoms this
# file created and never reaches into a machine value for a payload.

import importlib
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PARENT = os.path.dirname(REPO)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

PACKAGE = os.path.basename(REPO)

M = importlib.import_module(PACKAGE + ".machine")
P = importlib.import_module(PACKAGE + ".proof")
L = importlib.import_module(PACKAGE + ".labels")
persistence = importlib.import_module(PACKAGE + ".persistence")
packs = importlib.import_module(PACKAGE + ".packs")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
main_mod = importlib.import_module(PACKAGE + ".main")
peano = importlib.import_module(PACKAGE + ".math.peano")
arithmetic = importlib.import_module(PACKAGE + ".math.arithmetic")

T0 = time.time()
EMPTY = M.EmptyList

print("=== TEST 29: W9 (pack slice) functional equations & parity ===")
print()

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    line = "    PASS  " if ok else "    FAIL  "
    if detail:
        line = line + name + "  -- " + detail
    else:
        line = line + name
    print(line)


# ---------------------------------------------------------------------------
# host-layer helpers
# ---------------------------------------------------------------------------

NAMES = EMPTY


def named(term, name):
    global NAMES
    NAMES = M.Pair(M.Pair(term, M.Pair(name, EMPTY)), NAMES)
    return term


def name_of(term):
    cursor = NAMES
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        entry = M.Head(cursor)()
        if M.IdentityCompare(M.Head(entry)(), term)() is M.truth_value:
            return M.Head(M.Tail(entry)())()
        cursor = M.Tail(cursor)()
    return "<?>"


def chain(items):
    out = EMPTY
    index = len(items)
    while index > 0:
        index = index - 1
        out = M.Pair(items[index], out)
    return out


def fact(label, *args):
    return M.Pair(label, chain(args))


def is_list_term(term):
    return M.IdentityCompare(M.IsPair(term)(), M.truth_value)() is M.truth_value


def mpylist(term):
    out = []
    cursor = term
    while is_list_term(cursor):
        out.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return out


def show(term):
    if M.IsPair(term)() is M.truth_value:
        head = show(M.Head(term)())
        tail = mpylist(M.Tail(term)())
        rendered = " ".join(show(item) for item in tail)
        if rendered:
            return "(" + head + " " + rendered + ")"
        return "(" + head + ")"
    return name_of(term)


def has_fact(facts, target):
    cursor = facts
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        if M.Compare(M.Head(cursor)(), target)() is M.truth_value:
            return True
        cursor = M.Tail(cursor)()
    return False


def pattern_var_count(term):
    if M.IsPair(term)() is M.false_value:
        return 0
    if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
        return 1
    return pattern_var_count(M.Head(term)()) + pattern_var_count(M.Tail(term)())


def ground_data_atoms(term, acc):
    """
    The genericity pin, machine-side. Patterns in this term language are
    variables (VarTag-headed pairs), calls (label-headed pairs whose tail is
    the argument chain), structural conses (pair-headed), and ground atoms.
    Heads are relation vocabulary and are never data; a hardcoded function,
    number (beyond the Peano constructors this pack uses as nullary/unary
    calls), problem or constant would have to appear as a leaf reached
    through an argument or cons position, and this walk collects exactly
    those. It never asks IsAtom: the machine's atomness predicate accepts
    any non-pair, non-edge host object and never consults the registry it is
    handed (machine.py's IsAtom; reported, not worked around), and no
    machine predicate answers atomness at all -- GetConstructor returns the
    empty constructor for every non-pair object, machine or host alike.
    """
    if M.IsPair(term)() is M.false_value:
        return M.Pair(term, acc)
    head = M.Head(term)()
    if M.IdentityCompare(head, M.VarTag)() is M.truth_value:
        return acc
    if M.IsPair(head)() is M.truth_value:
        acc = ground_data_atoms(head, acc)
        return ground_data_atoms(M.Tail(term)(), acc)
    ccur = M.Tail(term)()
    while M.IdentityCompare(ccur, EMPTY)() is M.false_value:
        acc = ground_data_atoms(M.Head(ccur)(), acc)
        ccur = M.Tail(ccur)()
    return acc


def only_nil(atoms):
    cursor = atoms
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        if M.IdentityCompare(M.Head(cursor)(), EMPTY)() is M.false_value:
            return False
        cursor = M.Tail(cursor)()
    return True


def closure(facts, rules, registry, rounds=8):
    """Monotone forward chaining: rules contribute, nothing is consumed.
    Joined directly with JoinPremises; each family closes over its own small
    fact base, which is what keeps this affordable."""
    rounds_left = rounds
    state = P.Knowledge(facts)()
    while rounds_left > 0:
        rounds_left = rounds_left - 1
        changed = False
        current = P.KnowledgeFacts(state)()
        cursor = rules
        while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
            rule = M.Head(cursor)()
            cursor = M.Tail(cursor)()
            premises = P.RulePremises(rule)()
            replacement = P.RuleReplacement(rule)()
            bindings = P.JoinPremises(premises, current, EMPTY)()
            bcursor = bindings
            while M.IdentityCompare(bcursor, EMPTY)() is M.false_value:
                added = P.InstantiateFactList(replacement, M.Head(bcursor)())()
                acursor = added
                while M.IdentityCompare(acursor, EMPTY)() is M.false_value:
                    one = M.Head(acursor)()
                    if not has_fact(current, one):
                        current = M.Pair(one, current)
                        changed = True
                    acursor = M.Tail(acursor)()
                bcursor = M.Tail(bcursor)()
            state = P.Knowledge(current)()
        if not changed:
            break
    return P.NormalizeKnowledge(state, registry)()


# ---------------------------------------------------------------------------
# [1] boot, load, genericity
# ---------------------------------------------------------------------------

print("[1] Booting a fresh runtime and loading packs/funceq-nt.pack.yaml")

runtime = runtime_mod.make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
namespace = main_mod._runtime_namespace()

PACK_PATH = os.path.join(REPO, "packs", "funceq-nt.pack.yaml")
loader = packs.PackLoader(namespace)
pack = loader.load_pack_file(PACK_PATH, graph)
rules = P.CompileRuleChain(pack.rule_chain, registry)()

check("pack name is funceq-nt", pack.name == "funceq-nt", pack.name)
# 25 W9 rules + 8 W24 residue/divisibility schemas (2026-10-19).  The count is
# pinned so a silent removal is caught; W24's own suite is test36.
check("pack carries 33 generic schema rules (25 W9 + 8 W24)",
      len(mpylist(pack.rule_chain)) == 33,
      str(len(mpylist(pack.rule_chain))) + " rules")

rule_ok = True
rcursor = pack.rule_chain
while M.IdentityCompare(rcursor, EMPTY)() is M.false_value:
    rule = M.Head(rcursor)()
    pcursor = P.RulePremises(rule)()
    while M.IdentityCompare(pcursor, EMPTY)() is M.false_value:
        if not only_nil(ground_data_atoms(M.Head(pcursor)(), EMPTY)):
            rule_ok = False
        pcursor = M.Tail(pcursor)()
    rcursor2 = P.RuleReplacement(rule)()
    while M.IdentityCompare(rcursor2, EMPTY)() is M.false_value:
        if not only_nil(ground_data_atoms(M.Head(rcursor2)(), EMPTY)):
            rule_ok = False
        rcursor2 = M.Tail(rcursor2)()
    rcursor = M.Tail(rcursor)()
check("no rule puts a datum in an argument position (the Peano constructors"
      " enter only as calls, the empty list only as the call terminator)", rule_ok)

print()

# ---------------------------------------------------------------------------
# [2] additive Cauchy: the equation is input, f(0)=0 is derived
# ---------------------------------------------------------------------------

print("[2] Additive Cauchy  (section 1 took %.1fs)" % (time.time() - T0))

F_FN = named(M.Char("f"), "f")
G_FN = named(M.Char("g"), "g")
X0 = named(M.Char("x0"), "x0")
X1 = named(M.Char("x1"), "x1")
ZERO_T = named(M.Pair(L.ZeroLabel, EMPTY), "0")
ONE_T = named(M.Pair(L.SuccLabel, M.Pair(ZERO_T, EMPTY)), "1")

apply_f_zero = fact(L.ApplyLabel, F_FN, ZERO_T)
f_zero_is_zero = fact(L.ExprEqLabel, apply_f_zero, ZERO_T)
apply_g_zero = fact(L.ApplyLabel, G_FN, ZERO_T)
g_zero_is_zero = fact(L.ExprEqLabel, apply_g_zero, ZERO_T)

add_facts = chain([
    fact(L.CauchyAddLabel, F_FN),
    fact(L.ValueLabel, X0),
    fact(L.ValueLabel, X1),
])
add_final = closure(add_facts, rules, registry)
add_got = P.KnowledgeFacts(add_final)()

check("the (0,0) instance fires freely (Zero is a constructor, not a datum)",
      has_fact(add_got, fact(L.ExprEqLabel, apply_f_zero,
                             fact(L.ExprAddLabel, apply_f_zero, apply_f_zero))))
check("f(0) = 0 is derived, through the shared-term cancel", has_fact(add_got, f_zero_is_zero))

additivity = fact(L.ExprEqLabel,
                  fact(L.ApplyLabel, F_FN, fact(L.ExprAddLabel, X0, X1)),
                  fact(L.ExprAddLabel, fact(L.ApplyLabel, F_FN, X0), fact(L.ApplyLabel, F_FN, X1)))
check("the equation instance at supplied values is derived", has_fact(add_got, additivity))
additivity_rev = fact(L.ExprEqLabel,
                      fact(L.ExprAddLabel, fact(L.ApplyLabel, F_FN, X1), fact(L.ApplyLabel, F_FN, X0)),
                      fact(L.ApplyLabel, F_FN, fact(L.ExprAddLabel, X1, X0)))
check("  ... and, through symmetry, at (x1, x0) too", has_fact(add_got, additivity_rev))

check("a function with no equation input gets no consequence",
      not has_fact(add_got, g_zero_is_zero))
check("no instance is derived at values the instance did not supply",
      not has_fact(add_got, fact(L.ApplyLabel, F_FN,
                                 fact(L.ExprAddLabel, X0, ONE_T))))

print()

# ---------------------------------------------------------------------------
# [3] multiplicative Cauchy: f(1)=1 only under a visible assumption
# ---------------------------------------------------------------------------

print("[3] Multiplicative Cauchy")

apply_f_one = fact(L.ApplyLabel, F_FN, ONE_T)
f_one_is_one = fact(L.ExprEqLabel, apply_f_one, ONE_T)

mul_with = closure(chain([
    fact(L.CauchyMulLabel, F_FN),
    fact(L.NonTrivialLabel, F_FN),
    fact(L.ValueLabel, X0),
]), rules, registry)
mul_with_got = P.KnowledgeFacts(mul_with)()
check("with NonTrivial(f), the (1,1) instance normalises and f(1) = 1 is derived",
      has_fact(mul_with_got, f_one_is_one), show(mul_with))

mul_without = closure(chain([
    fact(L.CauchyMulLabel, F_FN),
    fact(L.ValueLabel, X0),
]), rules, registry)
mul_without_got = P.KnowledgeFacts(mul_without)()
check("without NonTrivial(f) the unit conclusion is refused -- the zero"
      " function is a counterexample and the schema knows it",
      not has_fact(mul_without_got, f_one_is_one))
check("  ... while the (1,1) instance itself still derives (it is free)",
      has_fact(mul_without_got, fact(L.ExprEqLabel, apply_f_one,
                                     fact(L.ExprMulLabel, apply_f_one, apply_f_one))))

multiplicativity = fact(L.ExprEqLabel,
                        fact(L.ApplyLabel, F_FN, fact(L.ExprMulLabel, X0, X0)),
                        fact(L.ExprMulLabel, fact(L.ApplyLabel, F_FN, X0),
                             fact(L.ApplyLabel, F_FN, X0)))
check("multiplicativity at supplied values is derived", has_fact(mul_with_got, multiplicativity))

print()

# ---------------------------------------------------------------------------
# [4] parity over the machine's own naturals
# ---------------------------------------------------------------------------

print("[4] Parity algebra on machine-computed naturals")

# The machine computes; these are its own atoms (result pair: nat + registry).
reg = registry
TWO = peano.two
THREE = peano.three
r = arithmetic.Add(TWO, THREE, reg)()
FIVE = M.Head(r)()
reg = M.Head(M.Tail(r)())()
r = arithmetic.Multiply(TWO, THREE, reg)()
SIX = M.Head(r)()
reg = M.Head(M.Tail(r)())()
r = arithmetic.Add(THREE, THREE, reg)()
SIX_ALT = M.Head(r)()
reg = M.Head(M.Tail(r)())()

# the machine's sums are what it says they are: 2+3 equals Count(5)
count5 = M.Head(peano.Count(chain([EMPTY, EMPTY, EMPTY, EMPTY, EMPTY]), reg)())()
check("the machine's own sum is verified against its own count: Add(2,3) = 5",
      peano.NatEq(FIVE, count5, reg)() is M.truth_value)

par_facts = chain([
    fact(L.EvenLabel, TWO),
    fact(L.OddLabel, THREE),
    fact(L.NatSumLabel, TWO, THREE, FIVE),
    fact(L.NatProductLabel, TWO, THREE, SIX),
    fact(L.NatSumLabel, THREE, THREE, SIX_ALT),
])
par_final = closure(par_facts, rules, registry)
par_got = P.KnowledgeFacts(par_final)()

check("odd + even is odd, on the machine's computed 2+3",
      has_fact(par_got, fact(L.OddLabel, FIVE)))
check("even * even is even, on the machine's computed 2*3",
      has_fact(par_got, fact(L.EvenLabel, SIX)))
check("odd + odd is even, on the machine's computed 3+3",
      has_fact(par_got, fact(L.EvenLabel, SIX_ALT)))
check("  ... and the wrong parities are unreachable",
      not has_fact(par_got, fact(L.EvenLabel, FIVE))
      and not has_fact(par_got, fact(L.OddLabel, SIX))
      and not has_fact(par_got, fact(L.OddLabel, SIX_ALT)))
check("no parity fact exists for a sum the machine never recorded",
      not has_fact(par_got, fact(L.OddLabel, TWO))
      and not has_fact(par_got, fact(L.EvenLabel, THREE)))

struct_final = closure(chain([fact(L.EvenLabel, ZERO_T)]), rules, registry)
struct_got = P.KnowledgeFacts(struct_final)()
two_term = M.Pair(L.SuccLabel, M.Pair(M.Pair(L.SuccLabel, M.Pair(ZERO_T, EMPTY)), EMPTY))
check("the structural recursion closes on successor terms: Even(0) gives Even(2)",
      has_fact(struct_got, fact(L.EvenLabel, two_term)))
check("  ... and never an odd parity of it",
      not has_fact(struct_got, fact(L.OddLabel, two_term)))

print()

# ---------------------------------------------------------------------------
# [5] the new labels survive a snapshot round-trip
# ---------------------------------------------------------------------------

print("[5] Snapshot symbol round-trip")

NEW_LABEL_NAMES = (
    "CauchyAddLabel",
    "CauchyMulLabel",
    "NonTrivialLabel",
    "ValueLabel",
    "NatSumLabel",
    "NatProductLabel",
)

snapshot_path = os.path.join(tempfile.mkdtemp(prefix="test29-"), "snapshot.json")
codec = persistence.SnapshotCodec(namespace)
codec.save(graph, snapshot_path)
restored = codec.load(snapshot_path)
os.remove(snapshot_path)
os.rmdir(os.path.dirname(snapshot_path))

absent = [name for name in NEW_LABEL_NAMES if name not in restored.symbols]
check("every new label is written into the snapshot symbol table", not absent, ",".join(absent))

identity_ok = True
for name in NEW_LABEL_NAMES:
    if name in restored.symbols:
        if restored.symbols[name] is not namespace[name]:
            identity_ok = False
check("  ... and restores to the live label object", identity_ok)

print()

# ---------------------------------------------------------------------------
# [6] representation checks
# ---------------------------------------------------------------------------

print("[6] Representation checks")

derived = closure(add_facts, rules, registry)
check("the derived knowledge is a Knowledge term", P.IsKnowledge(derived)() is M.truth_value)

fact_cursor = P.KnowledgeFacts(derived)()
facts_ok = True
while M.IdentityCompare(fact_cursor, EMPTY)() is M.false_value:
    one = M.Head(fact_cursor)()
    if M.IsPair(one)() is M.false_value:
        facts_ok = False
    if pattern_var_count(one) > 0:
        facts_ok = False
    fact_cursor = M.Tail(fact_cursor)()
check("  ... whose every fact is a machine pair carrying no pattern variable", facts_ok)

zero_occurrence_ok = True
rcursor = pack.rule_chain
while M.IdentityCompare(rcursor, EMPTY)() is M.false_value:
    rule = M.Head(rcursor)()
    rcursor2 = P.RuleReplacement(rule)()
    while M.IdentityCompare(rcursor2, EMPTY)() is M.false_value:
        one = M.Head(rcursor2)()
        # Zero and Succ may appear only as call heads (constructor calls),
        # never as bare data leaves.
        ccur = M.Tail(one)()
        while M.IdentityCompare(ccur, EMPTY)() is M.false_value:
            arg = M.Head(ccur)()
            if M.IsPair(arg)() is M.false_value:
                if M.IdentityCompare(arg, L.ZeroLabel)() is M.truth_value or \
                   M.IdentityCompare(arg, L.SuccLabel)() is M.truth_value:
                    zero_occurrence_ok = False
            ccur = M.Tail(ccur)()
        rcursor2 = M.Tail(rcursor2)()
    rcursor = M.Tail(rcursor)()
check("the Peano constructors appear only as calls, never as bare data", zero_occurrence_ok)

print()
print("=== TEST 29 RESULTS ===")
passed = 0
for _name, ok, _detail in RESULTS:
    if ok:
        passed = passed + 1
failed = len(RESULTS) - passed
for name, ok, detail in RESULTS:
    if not ok:
        print("  FAILED: " + name + ("  -- " + detail if detail else ""))
print("  Checks passed: " + str(passed) + "/" + str(len(RESULTS)))
print("  Total time:    %.3fs" % (time.time() - T0))
print()
if failed:
    print("=== TEST 29 FAILED ===")
    sys.exit(1)
print("=== TEST 29 COMPLETE ===")
