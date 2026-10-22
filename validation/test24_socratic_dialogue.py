# ============================================================
# TEST 24: W15 Socratic tutor
#          concept inspection from the machine's own sources,
#          a claim REPL (Checker B / counterexample / undecided),
#          structure-generated Socratic questions, ledger transparency
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test24_socratic_dialogue.py
#
# Slot 24 is the one `delegation/README.md` pre-allocates to
# `W15-socratic-tutor.md`.
#
# What is verified below, as a scripted deterministic conversation:
#
#   [1] boot: a fresh runtime, two packs (funceq-nt, engel-strategies),
#       a dialogue.Tutor that reads them;
#   [2] concept inspection: a concept that appears in NO prose anywhere in
#       dialogue.py or surface_bridge.py (SemiInvariant, from the Engel pack)
#       is explained from the loaded rules; one the bridge defines (parity)
#       is explained from its definition record; one nobody holds
#       (quaternion) is reported as not represented; a tutor over fewer
#       packs knows less, i.e. the index really is built from what is loaded;
#   [3] the claim grammar round-trips surface -> claim record -> surface,
#       paraphrases meet in one machine record (ClaimsEquivalent via
#       proof.SameKnowledge + Compare), and different claims do not;
#   [4] claims are judged three ways, distinguishably: VERIFIED only when
#       checker_b.VerifyDerivation accepts the derivation (re-run here
#       independently), REFUTED with a counterexample the suite re-evaluates
#       with the machine's arithmetic, UNDECIDED with both pieces of evidence
#       attached -- including a true claim no loaded rule proves, which is
#       honestly left undecided and never upgraded by bounded evidence;
#   [5] Socratic questions come from the goal shape and the loaded rules:
#       the progression over an arithmetic focus and over an Engel-pack goal
#       whose vocabulary dialogue.py never names, ending in a Checker-B
#       verified derivation; a goal no rule concludes yields a rung-6 question;
#   [6] ledger transparency: what each proposal lacks, the receipt it has,
#       and entries of a real promotion ledger;
#   [7] the transcript is a machine chain; the question classes the tutor
#       handles and the ones it falls through on are explicit;
#   [8] the REPL wiring in main.py (live mode, piped stdin);
#   [9] source discipline: no isinstance/hasattr on machine values, the two
#       boundary readers are the only type() uses, core.py is not imported.
#
# Host layer below: paths, timing, counting, printing, string checks on the
# tutor's rendered text.  Every assertion about *machine* content is an
# IdentityCompare / Compare / IsPair on machine terms.

import importlib
import os
import subprocess
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
CB = importlib.import_module(PACKAGE + ".checker_b")
PL = importlib.import_module(PACKAGE + ".promotion_ledger")
AR = importlib.import_module(PACKAGE + ".math.arithmetic")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
main_mod = importlib.import_module(PACKAGE + ".main")
D = importlib.import_module(PACKAGE + ".dialogue")

T0 = time.time()
EMPTY = M.EmptyList

print("=== TEST 24: W15 Socratic tutor ===")
print()

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    line = "    PASS  " if ok else "    FAIL  "
    print(line + name + (("  -- " + detail) if (detail and not ok) else ""))
    return bool(ok)


def is_label(term, label):
    return M.IdentityCompare(term, label)() is M.truth_value


def head_is(term, label):
    return M.IsPair(term)() is M.truth_value and is_label(M.Head(term)(), label)


def say(tutor, text):
    t1 = time.time()
    answer = tutor.ask(text)
    dt = time.time() - t1
    print("      you> " + text)
    for line in answer.text.split("\n"):
        print("      " + line)
    print("      [" + answer.kind + ", %.2fs]" % dt)
    return answer


# ---------------------------------------------------------------------------
# [1] boot
# ---------------------------------------------------------------------------

print("[1] Booting a fresh runtime, loading funceq-nt and engel-strategies, building the tutor")
t_boot = time.time()
runtime = runtime_mod.make_fresh_runtime()
namespace = main_mod._runtime_namespace()
pack_funceq = runtime.load_pack(os.path.join(REPO, "packs", "funceq-nt.pack.yaml"), namespace)
pack_engel = runtime.load_pack(os.path.join(REPO, "packs", "engel-strategies.pack.yaml"), namespace)
tutor = D.Tutor(runtime)
print("    boot %.1fs; packs read by the tutor: %s" % (time.time() - t_boot, ", ".join(p.name for p in tutor.packs)))
check("the tutor reads both loaded packs", [p.name for p in tutor.packs] == ["funceq-nt", "engel-strategies"])
# 38 until W24 (2026-10-19) added eight residue/divisibility schemas to
# funceq-nt; the tutor reads every fact-list rule of every loaded pack.
check("the tutor's search rules are the packs' MultiRules (46)", len(D.to_list(tutor.rules())) == 46, str(len(D.to_list(tutor.rules()))))
funceq_rules = dict((rid, obj()) for rid, obj in pack_funceq.rule_map.entries)
engel_rules = dict((rid, obj()) for rid, obj in pack_engel.rule_map.entries)
print()

# ---------------------------------------------------------------------------
# [2] concept inspection
# ---------------------------------------------------------------------------

print("[2] Concept inspection from the machine's sources")
with open(os.path.join(REPO, "dialogue.py"), encoding="utf-8") as fh:
    DIALOGUE_SRC = fh.read()
absent = ("semiinvariant", "semi-invariant", "semi_invariant", "allmovesdecrease", "boundedbelow",
          "monovariant_terminates", "sum_even_odd", "prod_odd_odd", "eventuallydecreases")
check("the probe vocabulary appears nowhere in dialogue.py", all(w not in DIALOGUE_SRC.lower() for w in absent),
      ", ".join(w for w in absent if w in DIALOGUE_SRC.lower()))
no_def = D.SB.QueryConceptDefinition(M.Char(D.normalise_word("semi-invariant")), tutor.definitions)()
check("'semi-invariant' has no definition record in the bridge (QueryConceptDefinition -> DefinitionNotFoundLabel)", head_is(no_def, L.DefinitionNotFoundLabel))

a = say(tutor, "what is a semi-invariant?")
check("semi-invariant: answered (ConceptReportLabel)", a.kind == "concept" and head_is(a.record, L.ConceptReportLabel))
sources = D.to_list(M.Head(M.Tail(M.Tail(a.record)())())())
check("  ... from the engel-strategies rule objects themselves (identity with the pack's rule_map)",
      any(s is engel_rules["semi_invariant_terminates"] for s in sources) and any(s is engel_rules["thread_non_increasing_moves"] for s in sources))
check("  ... the rendered answer names both rules and no definition record", "semi_invariant_terminates" in a.text and "thread_non_increasing_moves" in a.text and "definition record" not in a.text)

a = say(tutor, "what is parity?")
check("parity: answered from the bridge's definition record", a.kind == "concept" and "definition record:" in a.text)
check("  ... and honestly lists no rule (none of the loaded rules carries a Parity label)", "rules mentioning" not in a.text)

a = say(tutor, "what is a quaternion?")
check("quaternion: ConceptNotRepresentedLabel", a.kind == "not-represented" and head_is(a.record, L.ConceptNotRepresentedLabel))
check("  ... the answer says which packs were consulted", "funceq-nt" in a.text and "engel-strategies" in a.text)

a = say(tutor, "what is a monovariant?")
check("monovariant: definition record AND the two engel rules", "definition record" in a.text and "monovariant_terminates" in a.text and "thread_decreasing_moves" in a.text)

# a tutor that has not seen the Engel pack knows less
runtime_small = runtime_mod.make_fresh_runtime()
runtime_small.load_pack(os.path.join(REPO, "packs", "funceq-nt.pack.yaml"), namespace)
tutor_small = D.Tutor(runtime_small)
a_small = tutor_small.ask("what is a semi-invariant?")
check("with only funceq-nt loaded, 'semi-invariant' is not represented", a_small.kind == "not-represented")
tutor_small.add_pack(pack_engel)
a_small = tutor_small.ask("what is a semi-invariant?")
check("after add_pack(engel-strategies) the same tutor explains it from the rules", a_small.kind == "concept" and "semi_invariant_terminates" in a_small.text)
print()

# ---------------------------------------------------------------------------
# [3] claim grammar: round trip and paraphrase
# ---------------------------------------------------------------------------

print("[3] Claim grammar: surface -> machine record -> surface")
c1 = tutor.parse_claim(D.tokenize("if a is even and b is odd then a + b is odd"))
check("a claim parses to a DialogueClaimLabel record", c1 is not None and head_is(c1, L.DialogueClaimLabel))
hyps = D.to_list(D.claim_hypotheses(c1))
defs = D.to_list(D.claim_definitions(c1))
check("  ... hypotheses are Even/Odd facts in the pack's own labels", len(hyps) == 2 and head_is(hyps[0], L.EvenLabel) and head_is(hyps[1], L.OddLabel))
check("  ... the composite term a+b is defined by a NatSum fact", len(defs) == 1 and head_is(defs[0], L.NatSumLabel))
check("  ... the conclusion is Odd(a+b)", head_is(D.claim_conclusion(c1), L.OddLabel))
rendered = tutor.claim_text(c1)
print("    rendered: " + rendered)
c1_back = tutor.parse_claim(D.tokenize(rendered))
check("round trip: the rendering re-parses to an equivalent record", D.ClaimsEquivalent(c1, c1_back)() is M.truth_value)
paraphrases = [
    "if a is an even number and b is an odd number then the sum of a and b is odd",
    "if b is odd and a is even then a + b is odd",
    "a is even and b is odd implies a + b is odd",
    "whenever a is even and b is odd , a + b is odd",
    "is it true that if a is even and b is odd then a+b is odd",
]
all_equiv = True
for text in paraphrases:
    cp = tutor.parse_claim(D.tokenize(text))
    ok = cp is not None and D.ClaimsEquivalent(c1, cp)() is M.truth_value
    all_equiv = all_equiv and ok
    print("    %s  %s" % ("~" if ok else "X", text))
check("five paraphrases meet in the same machine record", all_equiv)
c_other = tutor.parse_claim(D.tokenize("if a is even and b is odd then a + b is even"))
check("a different conclusion is not equivalent", D.ClaimsEquivalent(c1, c_other)() is M.false_value)
c_other2 = tutor.parse_claim(D.tokenize("if a is even then a + b is odd"))
check("a weaker hypothesis set is not equivalent", D.ClaimsEquivalent(c1, c_other2)() is M.false_value)
c_sq = tutor.parse_claim(D.tokenize("if n is odd then the square of n is odd"))
c_sq2 = tutor.parse_claim(D.tokenize("if n is odd then n * n is odd"))
c_sq3 = tutor.parse_claim(D.tokenize("if n is odd then n squared is odd"))
check("'the square of n', 'n * n' and 'n squared' are one NatProduct(n, n, n*n) node",
      D.ClaimsEquivalent(c_sq, c_sq2)() is M.truth_value and D.ClaimsEquivalent(c_sq, c_sq3)() is M.truth_value)
check("prose that is not a claim does not parse", tutor.parse_claim(D.tokenize("the weather is nice")) is None and tutor.parse_claim(D.tokenize("every prime above 2 is odd")) is None)
print()

# ---------------------------------------------------------------------------
# [4] claims: verified / refuted / undecided
# ---------------------------------------------------------------------------

print("[4] Judging claims")
flat_rules = runtime.flat_rules()

a_ver = say(tutor, "is it true that if a is even and b is odd then a + b is odd?")
check("VERIFIED: ClaimVerifiedLabel", a_ver.kind == "claim-verified" and head_is(a_ver.record, L.ClaimVerifiedLabel))
payload = D.to_list(M.Tail(a_ver.record)())
derivation, checker_verdict, start_k, goal_k = payload[0], payload[1], payload[2], payload[3]
check("  ... the record carries the checker's own DerivationVerifiedLabel verdict", head_is(checker_verdict, L.DerivationVerifiedLabel))
re_verdict = CB.VerifyDerivation(derivation, start_k, goal_k, flat_rules, tutor.registry)()
check("  ... re-running checker_b.VerifyDerivation here agrees", head_is(re_verdict, L.DerivationVerifiedLabel))
steps = D.to_list(P.DerivationSteps(derivation, tutor.registry)())
step_rule = P.ActionRule(P.StepAction(steps[0], tutor.registry)())()
check("  ... the one step applies the pack's sum_even_odd rule object", len(steps) == 1 and step_rule is funceq_rules["sum_even_odd"])
wrong_goal = P.Knowledge(M.Pair(M.Pair(L.EvenLabel, M.Tail(D.claim_conclusion(tutor.claims[-1]["claim"]))()), EMPTY))()
check("  ... and the checker rejects the same derivation against the wrong goal (GoalMismatchLabel)",
      head_is(CB.VerifyDerivation(derivation, start_k, wrong_goal, flat_rules, tutor.registry)(), L.GoalMismatchLabel))

a_two = say(tutor, "if a is even and b is even and c is odd then a + b + c is odd")
steps_two = D.to_list(P.DerivationSteps(D.to_list(M.Tail(a_two.record)())[0], tutor.registry)())
check("a two-step claim is VERIFIED with two steps (sum_even_even then sum_even_odd)", a_two.kind == "claim-verified" and len(steps_two) == 2
      and P.ActionRule(P.StepAction(steps_two[0], tutor.registry)())() is funceq_rules["sum_even_even"]
      and P.ActionRule(P.StepAction(steps_two[1], tutor.registry)())() is funceq_rules["sum_even_odd"])

a_ref = say(tutor, "claim: if a is even and b is odd then a + b is even")
check("REFUTED: ClaimRefutedLabel with an assignment", a_ref.kind == "claim-refuted" and head_is(a_ref.record, L.ClaimRefutedLabel))
assignment = M.Head(M.Tail(a_ref.record)())()
claim_ref = tutor.claims[-1]["claim"]
# re-evaluate the counterexample with the machine's arithmetic, independently of the tutor
vals = {}
for entry in D.to_list(assignment):
    vals[D._char_text(M.Head(entry)())] = M.Tail(entry)()
reg = tutor.registry
sum_res = AR.Add(vals["a"], vals["b"], reg)()
two = tutor.two()
a_even = M.NatEq(M.Head(AR.Modulo(vals["a"], two, reg)())(), M.Zero, reg)() is M.truth_value
b_odd = M.NatEq(M.Head(AR.Modulo(vals["b"], two, reg)())(), M.Zero, reg)() is M.false_value
s_even = M.NatEq(M.Head(AR.Modulo(M.Head(sum_res)(), two, reg)())(), M.Zero, reg)() is M.truth_value
check("  ... the counterexample really satisfies the hypotheses and violates the conclusion (machine arithmetic)", a_even and b_odd and not s_even)
check("  ... the rendered answer shows the witness values", "a = 0" in a_ref.text and "b = 1" in a_ref.text)

a_und = say(tutor, "if a is even then a + 1 is odd")
check("UNDECIDED: ClaimUndecidedLabel for a true claim no loaded rule proves", a_und.kind == "claim-undecided" and head_is(a_und.record, L.ClaimUndecidedLabel))
search_outcome = M.Head(M.Tail(a_und.record)())()
sweep_outcome = M.Head(M.Tail(M.Tail(a_und.record)())())()
check("  ... search evidence: no derivation (EmptyList)", M.IdentityCompare(search_outcome, EMPTY)() is M.truth_value)
check("  ... sweep evidence: a SweepReportLabel with counts", head_is(sweep_outcome, L.SweepReportLabel))
n_checked = D._nat_value(M.Head(M.Tail(sweep_outcome)())(), tutor.registry)
n_hyps = D._nat_value(M.Head(M.Tail(M.Tail(sweep_outcome)())())(), tutor.registry)
check("  ... 12 assignments checked, hypotheses held on 6", n_checked == 12 and n_hyps == 6, "%s/%s" % (n_checked, n_hyps))
check("  ... the answer says bounded evidence is not a proof", "not a proof" in a_und.text and "VERIFIED" not in a_und.text)

a_div = say(tutor, "if a divides b and b divides c then a divides c")
# W24 (2026-10-19) wired the generic divisibility schemas into funceq-nt, so
# this claim changed verdict: it used to be the honest UNDECIDED control
# ("true, but no loaded rule proves it").  It is now VERIFIED by the tutor's
# own bounded search and Checker B, through the pack rule object itself.
steps_div = D.to_list(P.DerivationSteps(D.to_list(M.Tail(a_div.record)())[0], tutor.registry)()) if a_div.kind == "claim-verified" else []
check("transitivity of divisibility: now VERIFIED by the W24 schema (it was the"
      " UNDECIDED control before the wiring)",
      a_div.kind == "claim-verified" and len(steps_div) == 1
      and P.ActionRule(P.StepAction(steps_div[0], tutor.registry)())() is funceq_rules["divisibility_transitive"])
a_div2 = say(tutor, "if a divides b then b divides a")
check("its converse is REFUTED", a_div2.kind == "claim-refuted")

check("the three verdict labels are three distinct atoms",
      not is_label(L.ClaimVerifiedLabel, L.ClaimRefutedLabel) and not is_label(L.ClaimRefutedLabel, L.ClaimUndecidedLabel) and not is_label(L.ClaimVerifiedLabel, L.ClaimUndecidedLabel))
check("and the three answer kinds are distinct strings", len({a_ver.kind, a_ref.kind, a_und.kind}) == 3)

a_fall = say(tutor, "the weather is nice")
check("fall-through: DialogueFallthroughLabel, kind 'fallthrough', with the handled classes listed",
      a_fall.kind == "fallthrough" and head_is(a_fall.record, L.DialogueFallthroughLabel) and "Handled:" in a_fall.text)
a_prime = say(tutor, "is it true that every prime above 2 is odd?")
check("a claim outside the grammar falls through explicitly (it is not 'undecided')", a_prime.kind == "fallthrough")
print()

# ---------------------------------------------------------------------------
# [5] Socratic progression
# ---------------------------------------------------------------------------

print("[5] Socratic questions from the goal shape and the loaded rules")
a_focus = say(tutor, "let's work on: a + b is odd")
q = a_focus.record
check("focus opens with a rung-2 (join) question: which rule concludes Odd(a+b)",
      a_focus.kind == "focus" and head_is(q, L.SocraticQuestionLabel) and is_label(D.question_rung(q), L.Rung2JoinLabel))
check("  ... the rule it proposes is the pack's sum_even_odd (fewest open premises)", D.question_rule(q) is funceq_rules["sum_even_odd"])
# the obligations the tutor used are those BackwardObligations computes
obls = D.to_list(D.BackwardObligations(tutor.focus["goal"], tutor.focus["known"], tutor.rules())())
check("  ... three loaded rules can conclude the goal (BackwardObligations)", len(obls) == 3 and "3 loaded rules" in a_focus.text)

a_n1 = say(tutor, "next")
q1 = a_n1.record
even_a = D.fact(L.EvenLabel, tutor.grammar.char("a"))
check("'next' asks for the first open premise Even(a) at rung 1 (retrieval)",
      is_label(D.question_rung(q1), L.Rung1RetrievalLabel) and M.Compare(D.question_focus(q1), even_a)() is M.truth_value)

a_n2 = say(tutor, "next")
odd_b = D.fact(L.OddLabel, tutor.grammar.char("b"))
check("a second 'next' moves to the other open premise Odd(b) (no repetition)", M.Compare(D.question_focus(a_n2.record), odd_b)() is M.truth_value)

a_as1 = say(tutor, "a is even")
check("asserting 'a is even' is recorded and the open premise becomes Odd(b)", a_as1.kind == "assert" and D.chain_has(tutor.focus["known"], even_a) is M.truth_value
      and M.Compare(D.question_focus(a_as1.record), odd_b)() is M.truth_value)
a_as2 = say(tutor, "b is odd")
check("asserting 'b is odd' closes the obligations: rung-4 (derivation) question", is_label(D.question_rung(a_as2.record), L.Rung4DerivationLabel))
a_why = say(tutor, "why")
check("'why' renders the rule with held and open premises", a_why.kind == "why" and "sum_even_odd" in a_why.text and "premises you hold" in a_why.text)
a_chk = say(tutor, "check")
check("'check' builds the derivation and Checker B verifies it", a_chk.kind == "claim-verified")
check("  ... the checked claim is the one the conversation assembled", "if a is even and b is odd then a + b is odd" in a_chk.text)
texts = {a_focus.text, a_n1.text, a_n2.text, a_as1.text, a_as2.text}
check("five distinct question texts along the way (generated, not scripted)", len(texts) == 5)

print("    -- an Engel-pack goal the grammar never names --")
p_atom, m_atom = M.Char("p"), M.Char("m")
goal_t = D.fact(L.TerminatesLabel, p_atom)
known_t = D.chain([D.fact(L.MonovariantLabel, p_atom, m_atom)])
a_e0 = tutor.set_focus_goal(goal_t, known_t)
print("      " + a_e0.text.replace("\n", "\n      "))
check("Terminates(p) with Monovariant(p, m) known: rung-2 question over monovariant_terminates / semi_invariant_terminates",
      is_label(D.question_rung(a_e0.record), L.Rung2JoinLabel) and "monovariant_terminates" in a_e0.text and "semi_invariant_terminates" in a_e0.text)
a_e1 = say(tutor, "next")
amd = D.fact(L.AllMovesDecreaseLabel, tutor.grammar.char("p"), tutor.grammar.char("m"))
check("  ... first open premise is AllMovesDecrease(p, m), bound through the goal and the known fact", M.Compare(D.question_focus(a_e1.record), amd)() is M.truth_value)
a_e2 = say(tutor, "next")
open_bb = D.question_focus(a_e2.record)
check("  ... the next one, BoundedBelow(m, ?b), still carries an unbound pattern variable and the prompt asks which",
      head_is(open_bb, L.BoundedBelowLabel) and D.term_vocabulary_vars(open_bb) == {"?b"} and "Which ?b" in a_e2.text)
a_e3 = say(tutor, "assume AllMovesDecrease(p, m)")
check("  ... 'assume Name(args)' is read in the loaded rules' vocabulary", a_e3.kind == "assert" and D.chain_has(tutor.focus["known"], amd) is M.truth_value)
a_e4 = say(tutor, "assume BoundedBelow(m, 0)")
check("  ... after BoundedBelow(m, 0) every premise is in hand (rung 4)", is_label(D.question_rung(a_e4.record), L.Rung4DerivationLabel))
a_e5 = say(tutor, "check")
steps_e = D.to_list(P.DerivationSteps(D.to_list(M.Tail(a_e5.record)())[0], tutor.registry)()) if a_e5.kind == "claim-verified" else []
check("  ... Checker B verifies the one-step monovariant_terminates derivation", a_e5.kind == "claim-verified" and len(steps_e) == 1
      and P.ActionRule(P.StepAction(steps_e[0], tutor.registry)())() is engel_rules["monovariant_terminates"])

print("    -- a goal the new schemas can conclude --")
a_r6 = say(tutor, "focus on: a divides b")
# Before W24 no rule concluded Divides(_); this was the rung-6 negative
# control.  The four new schemas make it a rung-2 join, which is the honest
# change; the negative path is pinned separately below on a premise-only head.
check("Divides(a, b): now a rung-2 question -- four loaded schemas can conclude it",
      is_label(D.question_rung(a_r6.record), L.Rung2JoinLabel) and "4 loaded rules" in a_r6.text)
a_r6c = say(tutor, "check")
check("  ... and 'check' still refutes the universal claim", a_r6c.kind == "claim-refuted")

print("    -- a goal no rule concludes --")
neg_goal = D.fact(L.BoundedBelowLabel, m_atom, M.Char("b"))
a_r6n = tutor.set_focus_goal(neg_goal, EMPTY)
check("BoundedBelow(m, b) is premise-only in both packs: rung-6 (negative)"
      " question -- look for a counterexample first",
      is_label(D.question_rung(a_r6n.record), L.Rung6NegativeLabel))
print()

# ---------------------------------------------------------------------------
# [6] ledger transparency
# ---------------------------------------------------------------------------

print("[6] Ledger transparency")
a_led = say(tutor, "show candidates")
check("the report lists every session claim with a status", a_led.kind == "ledger" and all(("claim %d " % c["index"]) in a_led.text for c in tutor.claims))
check("  ... the empty runtime ledger is reported as empty", "promotion ledger: empty" in a_led.text)
und_index = [c["index"] for c in tutor.claims if head_is(c["verdict"], L.ClaimUndecidedLabel)][0]
a_why_not = say(tutor, "why is claim %d not promoted?" % und_index)
check("an undecided claim: 'lacks a receipt' plus the premise that would earn one (Odd(1), from BackwardObligations)",
      "lacks a receipt" in a_why_not.text and "Odd(1)" in a_why_not.text)
ref_index = [c["index"] for c in tutor.claims if head_is(c["verdict"], L.ClaimRefutedLabel)][0]
a_why_ref = say(tutor, "why is claim %d not promoted?" % ref_index)
check("a refuted claim: 'cannot be promoted' with its counterexample", "cannot be promoted" in a_why_ref.text)
ver_index = [c["index"] for c in tutor.claims if head_is(c["verdict"], L.ClaimVerifiedLabel)][0]
a_why_ver = say(tutor, "status of claim %d" % ver_index)
check("a verified claim: has a receipt; the ablation/holdout gates are named as not run", "Checker-B receipt" in a_why_ver.text and "holdout" in a_why_ver.text)
a_no = say(tutor, "why is claim 99 not promoted?")
check("an unknown claim number falls through", a_no.kind == "fallthrough")

# a real ledger entry becomes visible to both the report and concept inspection
reg = tutor.registry
receipt = M.Pair(L.ProofReceiptLabel, M.Pair(M.Char("tutor-session"), M.Pair(start_k, M.Pair(goal_k, M.Pair(derivation, M.Pair(flat_rules, EMPTY))))))
entry = PL.LedgerEntry(M.Char("parity_sum_lemma"), L.ProofSchemaPromotionLabel, M.Pair(L.CandidateMacroLabel, M.Pair(M.Char("parity_sum_lemma"), EMPTY)),
                       receipt, EMPTY, M.Zero, L.PromotionActiveLabel)()
runtime.graph.promotion_ledger = PL.PromotionLedger(M.Pair(entry, EMPTY), EMPTY, M.Zero)()
a_led2 = say(tutor, "ledger")
check("a promotion ledger entry is reported with its status and receipt presence", "parity_sum_lemma: PromotionActive" in a_led2.text and "receipt present" in a_led2.text)
a_con = say(tutor, "what is parity_sum_lemma?")
check("  ... and concept inspection finds the ledger entry by its id", a_con.kind == "concept" and "ledger entry parity_sum_lemma" in a_con.text)
print()

# ---------------------------------------------------------------------------
# [7] transcript and question classes
# ---------------------------------------------------------------------------

print("[7] Transcript and handled classes")
turns = D.to_list(tutor.transcript)
check("the transcript is a machine chain of DialogueTurnLabel records, one per ask()", len(turns) == len(tutor.turns) and all(head_is(t, L.DialogueTurnLabel) for t in turns))
first_turn = turns[-1]
toks = D.to_list(M.Head(M.Tail(first_turn)())())
check("  ... each turn carries the SurfaceToken chain of the question and the answer record", len(toks) == len(D.tokenize(tutor.turns[0][0])) and head_is(M.Head(M.Tail(M.Tail(first_turn)())())(), L.ConceptReportLabel))
kinds = set(k for k, _d in D.QUESTION_CLASSES)
check("the handled question classes are explicit", kinds == {"concept", "claim", "focus", "next", "assert", "check", "why", "ledger"})
seen_kinds = set(a.kind for _t, a in tutor.turns)
check("  ... and this conversation exercised every answer kind plus the fall-through",
      {"concept", "not-represented", "claim-verified", "claim-refuted", "claim-undecided", "focus", "question", "assert", "why", "ledger", "fallthrough"} <= seen_kinds, str(sorted(seen_kinds)))
print()

# ---------------------------------------------------------------------------
# [8] REPL wiring
# ---------------------------------------------------------------------------

print("[8] main.py live mode routes the fall-through through the tutor")
script = "load pack funceq-nt\nwhat is a quaternion?\nif n is odd then n * n is odd\nthe weather is nice\nquit\n"
env = dict(os.environ)
env["PYTHONPATH"] = PARENT
t_repl = time.time()
try:
    proc = subprocess.run([sys.executable, "-m", PACKAGE + ".main", "live"], input=script, capture_output=True, text=True, cwd=PARENT, env=env, timeout=600)
    out = proc.stdout + proc.stderr
except Exception as exc:  # noqa: BLE001 - reported as a failed check
    out = "EXC " + repr(exc)
print("    live mode round trip %.1fs" % (time.time() - t_repl))
check("'load pack funceq-nt' is a REPL command and tells the tutor", "loaded pack funceq-nt (33 rules)" in out)
check("concept inspection answers through the REPL", "'quaternion' is not represented" in out)
check("a claim is VERIFIED through the REPL with the pack loaded there", "VERIFIED: a 1-step derivation" in out and "prod_odd_odd" in out)
check("the tutor's fall-through reaches the pre-existing \"no, I can't prove that\"", "no, I can't prove that" in out)
print()

# ---------------------------------------------------------------------------
# [9] source discipline
# ---------------------------------------------------------------------------

print("[9] Source discipline")
check("dialogue.py never uses isinstance", "isinstance(" not in DIALOGUE_SRC)
check("dialogue.py never calls hasattr", "hasattr(" not in DIALOGUE_SRC)
import ast
type_calls = [node for node in ast.walk(ast.parse(DIALOGUE_SRC)) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "type"]
check("the only type() reads are the two boundary helpers (_label_name, _char_text)", len(type_calls) == 2, str(len(type_calls)))
check("  ... and no machine value is read with .__class__", ".__class__" not in DIALOGUE_SRC)
check("dialogue.py does not import core.py", "import core" not in DIALOGUE_SRC and "from .core" not in DIALOGUE_SRC)
check("no per-concept prose: the bridge's definition sentences are not duplicated", "integer property of being even or odd" not in DIALOGUE_SRC and "strictly decreases at each step" not in DIALOGUE_SRC)
print()

# ---------------------------------------------------------------------------

print("=== TEST 24 RESULTS ===")
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
    print("=== TEST 24 FAILED ===")
    sys.exit(1)
print("=== TEST 24 COMPLETE ===")
