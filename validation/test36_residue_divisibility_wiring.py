# ============================================================
# TEST 36: W24 — residue and divisibility schema wiring (W9 remainder)
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test36_residue_divisibility_wiring.py
#
# What this suite is for.  `math/arithmetic.py` already carried the machine
# edges `Divides`, `Gcd`, `Modulo` and `IsCoprime`; `packs/funceq-nt.pack.yaml`
# did not use them, so family 3 of W9(b) stopped at even/odd.  This worker adds
# eight constant-free schemas to that pack -- transitivity of divisibility, the
# gcd's two universal properties, Euclid's lemma, and residue addition and
# multiplication -- and this suite is their evidence.
#
# Honest scope, stated up front:
#   * Instance facts are records of what the machine's own edges computed.
#     `divides_f`, `gcd_f`, `coprime_f`, `mod_f`, `natsum_f`, `natprod_f`
#     below only ever record results the edge returned; no fact is asserted
#     against the machine's answer.
#   * The schemas put no constant in an argument position.  There is no `0`,
#     no `1`, no modulus in the pack: the suite re-runs W9's genericity walk
#     over all 33 rules to pin that.
#   * The closure engine enumerates one join per rule per round (the measured
#     limitation of `test22`/[32]).  Every scenario below is therefore run on
#     its own small fact base; nothing here claims completeness, only that the
#     named derivations occur and the named non-derivations do not.
#   * Residue schemas were exercised at moduli 3, 5 and 7.  They are
#     modulus-agnostic by construction (the modulus is a premise variable and
#     the reduction is a `Mod` record the machine computed), not by a table of
#     small moduli; no exhaustive sweep over moduli is claimed.
#   * d'Alembert-type functional equations remain OUT: they need a minus /
#     subtraction fragment, and W22 delivered recorded grid proofs, not a
#     signed normaliser.  Nothing here changes that.
#   * No host arithmetic was added.  `math/arithmetic.py` is untouched; the
#     residue fact head is `ModLabel`, which already existed and was already
#     registered in `SNAPSHOT_SYMBOL_NAMES` (the append-only label list is
#     unchanged by this worker).
#
# Verification side: at least one derivation is Checker-B-verified directly
# (the transitivity step), the same derivation is shown refused against the
# wrong goal, and the promotion ledger is asked twice -- once to promote the
# transitivity schema through the full evaluator/ablation/holdout gates, and
# once to refuse a candidate whose rule is not trusted, with the refusal
# reason recorded as a machine label.
#
# Host layer only below: file paths, timings, printing, and calling the
# machine's own arithmetic edges.  Every assertion about a machine term is
# `Compare` / `IdentityCompare` / `IsPair`; names are resolved by identity
# against atoms this file created, never by reading a payload.

import importlib
import os
import sys
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
packs = importlib.import_module(PACKAGE + ".packs")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
main_mod = importlib.import_module(PACKAGE + ".main")
arith = importlib.import_module(PACKAGE + ".math.arithmetic")
CheckerB = importlib.import_module(PACKAGE + ".checker_b")
Eval = importlib.import_module(PACKAGE + ".evaluator")
Ledger = importlib.import_module(PACKAGE + ".promotion_ledger")
graph_task = importlib.import_module(PACKAGE + ".graph_task")
peano = importlib.import_module(PACKAGE + ".math.peano")

T0 = time.time()
EMPTY = M.EmptyList

print("=== TEST 36: W24 residue and divisibility schema wiring ===")
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

def chain(items):
    out = EMPTY
    index = len(items)
    while index > 0:
        index = index - 1
        out = M.Pair(items[index], out)
    return out


def fact(label, *args):
    return M.Pair(label, chain(list(args)))


def call(label, *args):
    return M.Pair(label, chain(list(args)))


def is_list_term(term):
    return M.IdentityCompare(M.IsPair(term)(), M.truth_value)() is M.truth_value


def mpylist(term):
    out = []
    cursor = term
    while is_list_term(cursor):
        out.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return out


def has_fact(facts, target):
    cursor = facts
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        if M.Compare(M.Head(cursor)(), target)() is M.truth_value:
            return True
        cursor = M.Tail(cursor)()
    return False


def head_is(term, label):
    return M.IsPair(term)() is M.truth_value and M.IdentityCompare(M.Head(term)(), label)() is M.truth_value


# ---------------------------------------------------------------------------
# [1] boot, pack load, rule inventory, genericity pin
# ---------------------------------------------------------------------------

print("[1] Boot, load packs/funceq-nt.pack.yaml, inventory the new schemas")

runtime = runtime_mod.make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
namespace = main_mod._runtime_namespace()

PACK_PATH = os.path.join(REPO, "packs", "funceq-nt.pack.yaml")
loader = packs.PackLoader(namespace)
pack = loader.load_pack_file(PACK_PATH, graph)
rules = P.CompileRuleChain(pack.rule_chain, registry)()
rule_map = dict((rid, obj()) for rid, obj in pack.rule_map.entries)

NEW_SCHEMA_IDS = (
    "divisibility_transitive",
    "gcd_divides_both",
    "gcd_commutative",
    "coprime_commutative",
    "gcd_greatest_common_divisor",
    "coprimality_euclid",
    "residue_of_sum",
    "residue_of_product",
)

check("pack name is funceq-nt", pack.name == "funceq-nt", pack.name)
check("pack carries 33 schema rules (25 W9 + 8 W24)",
      len(mpylist(pack.rule_chain)) == 33,
      str(len(mpylist(pack.rule_chain))) + " rules")
missing_ids = [rid for rid in NEW_SCHEMA_IDS if rid not in rule_map]
check("all eight W24 schema ids are loaded", not missing_ids, ", ".join(missing_ids))


def pattern_var_count(term):
    if M.IsPair(term)() is M.false_value:
        return 0
    if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
        return 1
    return pattern_var_count(M.Head(term)()) + pattern_var_count(M.Tail(term)())


def ground_data_atoms(term, acc):
    """The genericity pin, machine-side (same walk test29 uses).

    Variables are VarTag-headed pairs; calls are label-headed pairs whose
    tail is the argument chain; structural conses are pair-headed. Heads are
    relation vocabulary, so a leaf reached through an argument or cons
    position is a datum -- and this pack must have none.
    """
    if M.IsPair(term)() is M.false_value:
        return M.Pair(term, acc)
    head = M.Head(term)()
    if M.IdentityCompare(head, M.VarTag)() is M.truth_value:
        return acc
    if M.IsPair(head)() is M.truth_value:
        acc = ground_data_atoms(head, acc)
        return ground_data_atoms(M.Tail(term)(), acc)
    cur = M.Tail(term)()
    while M.IdentityCompare(cur, EMPTY)() is M.false_value:
        acc = ground_data_atoms(M.Head(cur)(), acc)
        cur = M.Tail(cur)()
    return acc


def only_nil(atoms):
    cursor = atoms
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        if M.IdentityCompare(M.Head(cursor)(), EMPTY)() is M.false_value:
            return False
        cursor = M.Tail(cursor)()
    return True


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

check("no rule puts a datum in an argument position (no 0, no 1, no modulus,"
      " no named number anywhere in the pack)", rule_ok)
labels_source = open(os.path.join(REPO, "labels.py"), "r", encoding="utf-8").read()
registration_block = labels_source.split("def sync_from_namespace(namespace):", 1)[1]
registered_names = ("DividesLabel", "GcdLabel", "CoprimeLabel", "ModLabel")
unregistered = [name for name in registered_names
                if ('"' + name + '"') not in registration_block]
check("the residue fact head ModLabel already existed and is in the snapshot"
      " registration list (labels.py untouched by W24)",
      hasattr(L, "ModLabel") and not unregistered,
      ", ".join(unregistered))

print()


# ---------------------------------------------------------------------------
# machine-backed instance facts
# ---------------------------------------------------------------------------

def nat(n):
    return M.Head(M.NatFromRep(M.GMPRep(n), registry)())()


def add(a, b):
    return M.Head(arith.Add(a, b, registry)())()


def mul(a, b):
    return M.Head(arith.Multiply(a, b, registry)())()


def mod(a, m):
    return M.Head(arith.Modulo(a, m, registry)())()


def gcd(a, b):
    return M.Head(arith.Gcd(a, b, registry)())()


def divides_holds(a, b):
    return arith.Divides(a, b, registry)() is M.truth_value


def coprime_holds(a, b):
    return arith.IsCoprime(a, b, registry)() is M.truth_value


def divides_f(a, b):
    return fact(L.DividesLabel, a, b)


def gcd_f(a, b, g):
    return fact(L.GcdLabel, a, b, g)


def coprime_f(a, b):
    return fact(L.CoprimeLabel, a, b)


def mod_f(a, m, r):
    return fact(L.ModLabel, a, m, r)


def natsum_f(a, b, s):
    return fact(L.NatSumLabel, a, b, s)


def natprod_f(a, b, p):
    return fact(L.NatProductLabel, a, b, p)


def derive(facts, depth=5):
    depth_t = M.Head(M.NatFromRep(M.GMPRep(depth), registry)())()
    return graph_task.ForwardDeriveFacts(facts, rules, depth_t, registry)()


# ---------------------------------------------------------------------------
# [2] the machine computes; instance facts record the answer
# ---------------------------------------------------------------------------

print("[2] The machine's own edges compute the instance facts")

check("Add(7, 8) is the machine's 15", M.Compare(add(nat(7), nat(8)), nat(15))() is M.truth_value)
check("Multiply(7, 8) is the machine's 56", M.Compare(mul(nat(7), nat(8)), nat(56))() is M.truth_value)
check("Modulo(7, 5) is the machine's 2", M.Compare(mod(nat(7), nat(5)), nat(2))() is M.truth_value)
check("Gcd(12, 18) is the machine's 6", M.Compare(gcd(nat(12), nat(18)), nat(6))() is M.truth_value)
check("Divides(3, 18) and not Divides(6, 4) -- the edge the schema reads",
      divides_holds(nat(3), nat(18)) and not divides_holds(nat(6), nat(4)))
check("IsCoprime(6, 5) and not IsCoprime(6, 9) -- the gcd is consulted, not assumed",
      coprime_holds(nat(6), nat(5)) and not coprime_holds(nat(6), nat(9)))

print()


# ---------------------------------------------------------------------------
# [3] divisibility: transitivity and the gcd's universal properties
# ---------------------------------------------------------------------------

print("[3] Divisibility schemas")

div_base = chain([divides_f(nat(3), nat(6)), divides_f(nat(6), nat(18))])
div_got = derive(div_base, 4)
check("a | b and b | c derive a | c (3 | 6, 6 | 18 -> 3 | 18)",
      has_fact(div_got, divides_f(nat(3), nat(18))))
check("  ... and the converse is not manufactured (18 | 3 absent)",
      not has_fact(div_got, divides_f(nat(18), nat(3))))

gcd_base = chain([
    gcd_f(nat(12), nat(18), nat(6)),
    divides_f(nat(3), nat(12)),
    divides_f(nat(3), nat(18)),
])
gcd_got = derive(gcd_base, 6)
check("gcd(12, 18) = 6 derives both common-divisor facts (6 | 12, 6 | 18)",
      has_fact(gcd_got, divides_f(nat(6), nat(12)))
      and has_fact(gcd_got, divides_f(nat(6), nat(18))))
check("  ... and the gcd is commutative as a fact (Gcd(18, 12, 6))",
      has_fact(gcd_got, gcd_f(nat(18), nat(12), nat(6))))
check("a common divisor 3 divides the gcd: 3 | 6",
      has_fact(gcd_got, divides_f(nat(3), nat(6))))
check("the non-common divisor 4 does not (4 | 12 holds, 4 | 18 does not):"
      " 4 | 6 is absent", not has_fact(gcd_got, divides_f(nat(4), nat(6))))

print()


# ---------------------------------------------------------------------------
# [4] coprimality: Euclid's lemma and the decoy that ignores the gcd
# ---------------------------------------------------------------------------

print("[4] Coprimality schema (Euclid's lemma)")

euclid_base = chain([
    coprime_f(nat(6), nat(5)),
    natprod_f(nat(5), nat(12), nat(60)),
    divides_f(nat(6), nat(60)),
])
euclid_got = derive(euclid_base, 5)
check("coprime(6, 5), 5 * 12 = 60, 6 | 60 derive 6 | 12",
      has_fact(euclid_got, divides_f(nat(6), nat(12))))
check("  ... and coprime is commutative as a fact (Coprime(5, 6))",
      has_fact(euclid_got, coprime_f(nat(5), nat(6))))

decoy_base = chain([
    natprod_f(nat(9), nat(4), nat(36)),
    divides_f(nat(6), nat(36)),
])
decoy_got = derive(decoy_base, 5)
check("the decoy that would hold if the gcd were ignored: 6 | 9 * 4 and 6 | 4 is"
      " false, and the schema refuses because Coprime(6, 9) is not available",
      not has_fact(decoy_got, divides_f(nat(6), nat(4))))
check("  ... the machine itself says 6 does not divide 4 (the decoy is a false"
      " target, not merely an absent fact)", not divides_holds(nat(6), nat(4)))

print()


# ---------------------------------------------------------------------------
# [5] residues: addition and multiplication under three different moduli
# ---------------------------------------------------------------------------

print("[5] Residue schemas (moduli 3, 5 and 7)")

sum5_base = chain([
    mod_f(nat(7), nat(5), nat(2)),
    mod_f(nat(8), nat(5), nat(3)),
    natsum_f(nat(7), nat(8), nat(15)),
    natsum_f(nat(2), nat(3), nat(5)),
    mod_f(nat(5), nat(5), nat(0)),
])
sum5_got = derive(sum5_base, 5)
check("mod 5: 7 = 2, 8 = 3, 2 + 3 = 5 = 0 (mod 5) derives 15 = 0 (mod 5)",
      has_fact(sum5_got, mod_f(nat(15), nat(5), nat(0))))
check("  ... and the unreduced residue sum (15 = 3 mod 5) is NOT derived",
      not has_fact(sum5_got, mod_f(nat(15), nat(5), nat(3))))
check("  ... nor a neighbouring wrong residue (15 = 1 mod 5)",
      not has_fact(sum5_got, mod_f(nat(15), nat(5), nat(1))))

sum3_base = chain([
    mod_f(nat(7), nat(3), nat(1)),
    mod_f(nat(8), nat(3), nat(2)),
    natsum_f(nat(7), nat(8), nat(15)),
    natsum_f(nat(1), nat(2), nat(3)),
    mod_f(nat(3), nat(3), nat(0)),
])
sum3_got = derive(sum3_base, 5)
check("mod 3: 7 = 1, 8 = 2, 1 + 2 = 3 = 0 (mod 3) derives 15 = 0 (mod 3)",
      has_fact(sum3_got, mod_f(nat(15), nat(3), nat(0))))

sum7_base = chain([
    mod_f(nat(10), nat(7), nat(3)),
    mod_f(nat(11), nat(7), nat(4)),
    natsum_f(nat(10), nat(11), nat(21)),
    natsum_f(nat(3), nat(4), nat(7)),
    mod_f(nat(7), nat(7), nat(0)),
])
sum7_got = derive(sum7_base, 5)
check("mod 7: 10 = 3, 11 = 4, 3 + 4 = 7 = 0 (mod 7) derives 21 = 0 (mod 7)",
      has_fact(sum7_got, mod_f(nat(21), nat(7), nat(0))))

prod5_base = chain([
    mod_f(nat(7), nat(5), nat(2)),
    mod_f(nat(8), nat(5), nat(3)),
    natprod_f(nat(7), nat(8), nat(56)),
    natprod_f(nat(2), nat(3), nat(6)),
    mod_f(nat(6), nat(5), nat(1)),
])
prod5_got = derive(prod5_base, 5)
check("mod 5: 7 = 2, 8 = 3, 2 * 3 = 6 = 1 (mod 5) derives 56 = 1 (mod 5)",
      has_fact(prod5_got, mod_f(nat(56), nat(5), nat(1))))
check("  ... and the unreduced residue product (56 = 6 mod 5) is NOT derived",
      not has_fact(prod5_got, mod_f(nat(56), nat(5), nat(6))))

incomplete_base = chain([
    mod_f(nat(7), nat(5), nat(2)),
    natsum_f(nat(7), nat(8), nat(15)),
    natsum_f(nat(2), nat(3), nat(5)),
    mod_f(nat(5), nat(5), nat(0)),
])
incomplete_got = derive(incomplete_base, 5)
check("with one operand's residue record withheld, no residue is derived for the"
      " sum (the schema is not guessing)", not has_fact(incomplete_got, mod_f(nat(15), nat(5), nat(0))))

print()


# ---------------------------------------------------------------------------
# [6] Checker B over a derived fact
# ---------------------------------------------------------------------------

print("[6] Checker B verifies the transitivity derivation, and refuses the wrong goal")

rule_t = rule_map["divisibility_transitive"]
start_state = P.Knowledge(chain([divides_f(nat(3), nat(6)), divides_f(nat(6), nat(18))]))()
joins = P.JoinPremises(P.RulePremises(rule_t)(), P.KnowledgeFacts(start_state)(), EMPTY)()
check("the rule's premises join against the fact state", M.IdentityCompare(joins, EMPTY)() is M.false_value)
bindings = M.Head(joins)()
next_state = P.ApplyKnowledgeRewrite(start_state, rule_t, bindings)()
action = P.TheoremAction(rule_t, bindings)()
step_pair = P.Step(start_state, action, next_state, registry)()
step = M.Head(step_pair)()
step_registry = M.Head(M.Tail(step_pair)())()
trusted = M.Pair(rule_t, EMPTY)
cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
derivation_pair = P.Derivation(M.Pair(step, EMPTY), cost_zero, step_registry)()
derivation = M.Head(derivation_pair)()
derivation_registry = M.Head(M.Tail(derivation_pair)())()
verdict = CheckerB.VerifyDerivation(derivation, start_state, next_state, trusted, derivation_registry)()
check("the one-step derivation is Checker-B verified",
      M.IdentityCompare(M.Head(verdict)(), L.DerivationVerifiedLabel)() is M.truth_value,
      str(M.Head(verdict)()))
wrong_goal = P.Knowledge(chain([divides_f(nat(6), nat(3))]))()
wrong_verdict = CheckerB.VerifyDerivation(derivation, start_state, wrong_goal, trusted, derivation_registry)()
check("the same derivation is refused against the converse goal (GoalMismatch)",
      M.IdentityCompare(M.Head(wrong_verdict)(), L.GoalMismatchLabel)() is M.truth_value,
      str(M.Head(wrong_verdict)()))

print()


# ---------------------------------------------------------------------------
# [7] the promotion ledger: asked to promote, and asked to refuse
# ---------------------------------------------------------------------------

print("[7] Promotion ledger: one promotion through the full gates, one stated refusal")


def var_conses(term, acc):
    """Collect the rule's own variable patterns, by identity.

    The macro patterns reuse these exact objects so that the bindings the
    evaluator merges are keyed by the variables the rule itself will
    instantiate.  Reusing the rule's variables (rather than fresh patterns)
    is what makes the candidate generalise across holdout instances instead
    of replaying one hard-coded triple.
    """
    if M.IsPair(term)() is M.false_value:
        return acc
    if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
        found = False
        index = 0
        while index < len(acc):
            if M.IdentityCompare(acc[index], term)() is M.truth_value:
                found = True
            index = index + 1
        if not found:
            acc.append(term)
        return acc
    cursor = term
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        acc = var_conses(M.Head(cursor)(), acc)
        cursor = M.Tail(cursor)()
    return acc


premises = P.RulePremises(rule_t)()
rule_vars = var_conses(premises, [])
check("the transitivity rule has exactly three distinct variables",
      len(rule_vars) == 3, str(len(rule_vars)))
va, vb, vc = rule_vars[0], rule_vars[1], rule_vars[2]

start_pattern = M.Pair(
    P.KnowledgeLabel,
    M.Pair(
        M.Pair(call(L.DividesLabel, va, vb),
               M.Pair(call(L.DividesLabel, vb, vc), EMPTY)),
        EMPTY,
    ),
)
goal_pattern = M.Pair(
    P.KnowledgeLabel,
    M.Pair(M.Pair(call(L.DividesLabel, va, vc), EMPTY), EMPTY),
)
plan = M.Pair(P.TheoremAction(rule_t, EMPTY)(), EMPTY)
macro = Eval.CandidateMacro(M.Atom(), start_pattern, goal_pattern, plan)()

instance_start = P.Knowledge(chain([divides_f(nat(3), nat(6)), divides_f(nat(6), nat(18))]))()
instance_goal = P.Knowledge(chain([divides_f(nat(3), nat(18))]))()
trusted_chain = chain([rule_t])

expansion = Eval.ExpandCandidateMacro(macro, instance_start, instance_goal, registry)()
check("the candidate macro expands on a concrete instance",
      M.IdentityCompare(M.Head(expansion)(), L.CandidateExpandedLabel)() is M.truth_value,
      str(M.Head(expansion)()))
evaluation = Eval.EvaluateCandidateProof(macro, instance_start, instance_goal, trusted_chain, registry)()
check("the evaluator's Checker-B gate accepts the expanded derivation",
      M.IdentityCompare(M.Head(evaluation)(), L.CandidateEvaluatedLabel)() is M.truth_value,
      str(M.Head(evaluation)()))

holdouts = chain([
    M.Pair(
        P.Knowledge(chain([divides_f(nat(5), nat(15)), divides_f(nat(15), nat(45))]))(),
        M.Pair(P.Knowledge(chain([divides_f(nat(5), nat(45))]))(), M.Pair(M.truth_value, EMPTY)),
    ),
    M.Pair(
        P.Knowledge(chain([divides_f(nat(2), nat(8)), divides_f(nat(8), nat(24))]))(),
        M.Pair(P.Knowledge(chain([divides_f(nat(2), nat(24))]))(), M.Pair(M.truth_value, EMPTY)),
    ),
    M.Pair(
        P.Knowledge(chain([divides_f(nat(4), nat(12)), divides_f(nat(6), nat(12))]))(),
        M.Pair(P.Knowledge(chain([divides_f(nat(4), nat(6))]))(), M.Pair(M.false_value, EMPTY)),
    ),
])
ledger0 = Ledger.EmptyPromotionLedger(registry)()
baseline_cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
promotion = Ledger.SubmitCandidateForPromotion(
    ledger0,
    macro,
    L.ProofSchemaPromotionLabel,
    instance_start,
    instance_goal,
    baseline_cost,
    holdouts,
    EMPTY,
    trusted_chain,
    registry,
)()
check("the ledger promotes the schema through evaluator, ablation and holdout gates",
      M.IdentityCompare(M.Head(promotion)(), L.PromotionApprovedLabel)() is M.truth_value,
      str(M.Head(promotion)()))
if M.IdentityCompare(M.Head(promotion)(), L.PromotionApprovedLabel)() is M.truth_value:
    promoted_ledger = M.Head(M.Tail(promotion)())()
    promoted_entry = M.Head(M.Tail(M.Tail(promotion)())())()
    check("  ... the ledger version advanced to 1 (compared by value: ledger"
          " versions are fresh Succ atoms, not GMP nats)",
          peano.NatEq(Ledger.PromotionLedgerVersion(promoted_ledger)(), nat(1), registry)() is M.truth_value)
    check("  ... the entry is active and carries a ProofReceipt (not an assertion)",
          M.IdentityCompare(Ledger.LedgerEntryStatus(promoted_entry)(), L.PromotionActiveLabel)() is M.truth_value
          and M.IdentityCompare(M.Head(Ledger.LedgerEntryReceipt(promoted_entry)())(), L.ProofReceiptLabel)() is M.truth_value)
else:
    check("  ... the ledger version advanced to 1", False, "promotion refused")
    check("  ... the entry is active and carries a ProofReceipt", False, "promotion refused")

refusal = Ledger.SubmitCandidateForPromotion(
    ledger0,
    macro,
    L.ProofSchemaPromotionLabel,
    instance_start,
    instance_goal,
    baseline_cost,
    holdouts,
    EMPTY,
    EMPTY,
    registry,
)()
refusal_reason = M.Head(M.Tail(refusal)())()
check("a candidate whose rule is not trusted is refused, with the reason recorded"
      " as a machine label (UnknownRule)", 
      M.IdentityCompare(M.Head(refusal)(), L.PromotionRejectedLabel)() is M.truth_value
      and M.IdentityCompare(refusal_reason, L.UnknownRuleLabel)() is M.truth_value,
      str(refusal_reason))

print()


# ---------------------------------------------------------------------------
# [8] what this suite does and does not claim
# ---------------------------------------------------------------------------

print("[8] Scope of the claim")

check("all four divisor-side fact heads used here are pre-existing labels"
      " (no append-only list growth)",
      all(hasattr(L, name) for name in ("DividesLabel", "GcdLabel", "CoprimeLabel", "ModLabel")))
allowed_heads = (L.DividesLabel, L.GcdLabel, L.CoprimeLabel, L.ModLabel,
                 L.NatSumLabel, L.NatProductLabel)
foreign = []
cursor = gcd_got
while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
    head = M.Head(M.Head(cursor)())()
    known = False
    index = 0
    while index < len(allowed_heads):
        if M.Compare(head, allowed_heads[index])() is M.truth_value:
            known = True
        index = index + 1
    if not known:
        foreign.append(head)
    cursor = M.Tail(cursor)()
check("every fact in the closure is headed by one of the six pre-existing labels"
      " (the pack introduces no vocabulary of its own)", not foreign)
print("    NOTE  moduli exercised: 3, 5, 7.  The schemas carry the modulus as a")
print("          premise variable and read the machine's Mod record, so they are")
print("          not restricted to a table of moduli; no exhaustive sweep is claimed.")
print("    NOTE  d'Alembert-type equations remain out of reach: they need a minus")
print("          term, and W22 delivered recorded grid proofs, not a signed")
print("          normaliser.  Nothing here changes that.")
print("    NOTE  the closure engine enumerates one join per rule per round, so the")
print("          scenarios above are isolated fact bases, not a completeness claim.")
print()

print("=== TEST 36 RESULTS ===")
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
    print("=== TEST 36 FAILED ===")
    sys.exit(1)
print("=== TEST 36 COMPLETE ===")
