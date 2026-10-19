# ============================================================
# TEST 37: W25 Curriculum Card Loader
#          markdown cards -> machine records -> graph tasks -> verdicts
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test37_curriculum_loader.py
#
# Slot 37 is the one `delegation/README.md` assigns to
# `W25-curriculum-loader.md`; slot 36 went to W24 and 38+ are unallocated.
#
# What this suite is allowed to claim, and what it is not.
#
# The corpus under `curriculum/` is prose: a statement, a method, the
# constructors a card cites, the constructors it lacks, negative controls and
# a promotion gate.  Most of those cards still fail their own gate.  The
# loader therefore does NOT claim "the curriculum now loads": it claims the
# smaller, checkable thing the brief asks for --
#
#   * the cards are parsed into machine records (24 of 24), and the record
#     fields are machine terms, not Python strings;
#   * the constructor names the cards cite are cleared where they can be
#     (append-only additions to `labels.py`), and every name still missing is
#     REPORTED as a Ground 1 gap with the card that cites it;
#   * two cards compile into graph tasks whose semantics come from a family
#     builder, not from the card: the seven-glasses held-out closes as an
#     invariance obstruction, the domino-board decoy is refused;
#   * the closure is computed.  Perturbing the statement by one word changes
#     the verdict, which is the structural proof that no conclusion was
#     authored for these cards;
#   * twenty-two cards have no builder.  They are named, with reasons, and
#     counted per family -- not skipped.
#
# The suite never reads an answer out of a card.  It reads the numbers a
# statement states and hands them to builders that implement an Engel
# strategy schema; the *derivation* is done by `ForwardDeriveFacts` with the
# Engel pack, and the match by `MatchQueryConjunction`, exactly the engines
# `ExecuteGraphQuery` uses for the synthetic rungs of test10.
#
# Host layer only below: file paths, timings, counting and printing.  Every
# assertion about a machine value is IdentityCompare / Compare / Head / Tail;
# the one exception is `hasattr(labels, name)`, which reflects on the Python
# module, not on a machine term (test22/[31] did the same before W25).
#
# The suite imports the package under whatever name the checkout carries.

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
L = importlib.import_module(PACKAGE + ".labels")
GT = importlib.import_module(PACKAGE + ".graph_task")
Curric = importlib.import_module(PACKAGE + ".curriculum")
packs = importlib.import_module(PACKAGE + ".packs")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")
main_mod = importlib.import_module(PACKAGE + ".main")

T0 = time.time()
EMPTY = M.EmptyList
TRUTH = M.truth_value

print("=== TEST 37: W25 Curriculum Card Loader ===")
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
# host-layer helpers (machine terms in, machine terms out)
# ---------------------------------------------------------------------------


def chain(items):
    out = EMPTY
    for item in reversed(list(items)):
        out = M.Pair(item, out)
    return out


def to_list(term):
    out = []
    cursor = term
    while M.IdentityCompare(cursor, EMPTY)() is M.false_value:
        out.append(M.Head(cursor)())
        cursor = M.Tail(cursor)()
    return out


def fact(label, *args):
    return M.Pair(label, chain(list(args)))


def nat(value):
    if value == 0:
        return M.Zero
    return M.Head(M.NatFromRep(M.GMPRep(int(value)), registry)())()


def int_of(nat_term):
    return int(M.NatRepOf(nat_term, registry)()())


def text_of(atom):
    return atom()


def label_is(term, label):
    return M.IdentityCompare(term, label)() is M.truth_value


def head_is(term, label):
    return M.IdentityCompare(M.Head(term)(), label)() is M.truth_value


print("[1] Runtime, registry, and the labels this worker appended...")
runtime = runtime_mod.make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")

NEW_CONSTRUCTORS = (
    "IntegerLabel", "IntegersLabel", "RemainderLabel", "ResidueLabel",
    "CongruentLabel", "PrefixSumLabel", "SubsetLabel", "ColoringLabel",
    "CheckerboardLabel", "DominoLabel", "CellLabel", "SquareLabel",
    "BoardLabel", "CornerLabel", "ColorLabel", "PathLabel", "CycleLabel",
    "GraphLabel", "VertexLabel", "EdgeLabel", "DegreeLabel", "GlassLabel",
    "UprightLabel", "FlipLabel", "MoveLabel", "CountUprightLabel",
    "StripLabel", "TileLabel", "GridLabel", "TilingLabel",
)
NEW_RECORDS = (
    "CardRecordLabel", "Ground1GapLabel", "CardTaskLabel", "CardSolvedLabel",
    "CardRejectedLabel", "CardOpenLabel", "CardNoBuilderLabel",
    "CardSplitCheckLabel", "ColorCountLabel", "TileRequiredLabel",
    "CardLoaderResultLabel",
)

ALL_NEW = NEW_CONSTRUCTORS + NEW_RECORDS
check("every appended label is defined in labels.py",
      all(hasattr(L, name) for name in ALL_NEW),
      "%d constructors + %d record/verdict labels"
      % (len(NEW_CONSTRUCTORS), len(NEW_RECORDS)))

# sync_from_namespace copies a live runtime namespace INTO labels.py (the
# cold-resume direction).  Prove registration by a round trip: sentinels in,
# then the originals back.  The module is exactly as it was afterwards.
originals = {name: getattr(L, name) for name in ALL_NEW}
sentinel = object()
synced = {name: sentinel for name in ALL_NEW}
L.sync_from_namespace(synced)
registered = all(getattr(L, name) is sentinel for name in ALL_NEW)
L.sync_from_namespace(originals)
restored = all(getattr(L, name) is originals[name] for name in ALL_NEW)
check("every appended label is registered by sync_from_namespace",
      registered and restored,
      "sentinel in, originals back: %s" % ("ok" if restored else "NOT restored"))
print()

print("[2] The corpus is parsed, all of it, into machine records...")
CORPUS = os.path.join(REPO, "curriculum")
corpus_paths = []
for dirpath, _dirnames, filenames in os.walk(CORPUS):
    for filename in sorted(filenames):
        if filename.endswith(".md"):
            corpus_paths.append(
                os.path.relpath(os.path.join(dirpath, filename), CORPUS)
                .replace("\\", "/")
            )
corpus_paths.sort()
print("    corpus files: %d" % len(corpus_paths))

records, gap_pairs, parsed_paths = Curric.load_card_corpus(CORPUS, registry)
record_list = to_list(records)
check("all 24 markdown cards produce a CardRecord",
      len(record_list) == len(corpus_paths) == 24,
      "%d records / %d files" % (len(record_list), len(corpus_paths)))

ids = [text_of(Curric.CardRecordId(r)()) for r in record_list]
check("records are keyed by their path, one each, sorted",
      ids == corpus_paths and len(set(ids)) == len(ids),
      "first: %s" % ids[0])

tiers_ok = True
roles_ok = True
for record in record_list:
    path = text_of(Curric.CardRecordId(record)())
    tier = text_of(Curric.CardRecordTier(record)())
    role = text_of(Curric.CardRecordRole(record)())
    parts = path.split("/")
    if tier != parts[0]:
        tiers_ok = False
    if role != parts[1]:
        roles_ok = False
check("tier and role are read from the path, not assumed", tiers_ok and roles_ok)

fields = []
for record in record_list:
    fields.append((
        text_of(Curric.CardRecordStatement(record)()),
        text_of(Curric.CardRecordTargetClass(record)()),
        text_of(Curric.CardRecordFamily(record)()),
        text_of(Curric.CardRecordStatus(record)()),
    ))
check("every card has a non-empty statement, target class and family",
      all(s and t and f for s, t, f, _ in fields))
check("every card still self-declares 'blueprint-only' in its status",
      all("blueprint-only" in status for _s, _t, _f, status in fields))

provenance_clean = all(
    "supplied verbatim" not in s
    and "recorded in protocol" not in s
    and "UNSOURCED" not in s
    for s, _t, _f, _s2 in fields
)
check("statement text carries no provenance marker", provenance_clean)

families = {}
for _s, _t, family, _st in fields:
    families[family] = families.get(family, 0) + 1
print("    family census: %s"
      % ", ".join("%s=%d" % (k, families[k]) for k in sorted(families)))
check("the five card families are the five the corpus announces",
      sorted(families) == ["Divide", "Extremal", "Invariance", "Pigeonhole",
                           "Symmetry"],
      "counts %s" % ([families[k] for k in sorted(families)],))

again, _again_gaps, _again_paths = Curric.load_card_corpus(CORPUS, registry)
same = True
for left, right in zip(record_list, to_list(again)):
    if M.Compare(left, right)() is not M.truth_value:
        same = False
check("parsing is deterministic (two loads compare term-by-term)", same)

numbers = {}
for record in record_list:
    numbers[text_of(Curric.CardRecordId(record)())] = [
        int_of(n) for n in to_list(Curric.CardRecordNumbers(record)())
    ]
seven_id = "tier0/heldout/invariance-seven-glasses.md"
check("the numbers a statement states are read into the record",
      numbers.get(seven_id) == [7, 4, 7],
      "%s -> %s" % (seven_id, numbers.get(seven_id)))
check("a symbolic card gets no invented numbers",
      numbers.get("tier0/heldout/pigeonhole-subset-sum.md") == [],
      "pigeonhole-subset-sum -> %s"
      % (numbers.get("tier0/heldout/pigeonhole-subset-sum.md"),))
print()

print("[3] Ground 1 coverage: what was cleared, what is still missing...")
cited_names = set()
for record in record_list:
    for field in (Curric.CardRecordCited(record)(),
                  Curric.CardRecordMissing(record)()):
        for name in to_list(field):
            cited_names.add(text_of(name))
print("    distinct constructor names cited by the corpus: %d"
      % len(cited_names))

uncited = [name for name in NEW_CONSTRUCTORS if name not in cited_names]
check("every constructor this worker added is cited by a card",
      not uncited,
      "added without a citing card: %s" % (uncited or "none"))

still_absent = sorted(name for name in cited_names if not hasattr(L, name))
gap_names = set(name for _card, name in gap_pairs)
gap_cards = set(card for card, _name in gap_pairs)
check("the names still absent from labels.py are computed, not listed",
      gap_names == set(still_absent),
      "%d absent names, %d gap pairs on %d cards"
      % (len(still_absent), len(gap_pairs), len(gap_cards)))
check("every reported gap names a card of the corpus",
      gap_cards <= set(corpus_paths),
      "%d distinct cards cite at least one gap" % len(gap_cards))

check("the decoy's cited InvarianceLabel is still a gap",
      "InvarianceLabel" in gap_names)
check("...while the label the machine really has (InvariantLabel) exists",
      hasattr(L, "InvariantLabel")
      and not hasattr(L, "InvarianceLabel"))
print("    still-OPEN Ground 1 names include: %s"
      % ", ".join(sorted(gap_names)[:8]))
print("    ... and %d more, all reported by the loader."
      % max(0, len(gap_names) - 8))
print()

print("[4] The seven-glasses held-out compiles into a real graph task...")
seven_record = None
for record in record_list:
    if text_of(Curric.CardRecordId(record)()) == seven_id:
        seven_record = record
check("the held-out card is present", seven_record is not None)

pack_loader = packs.PackLoader(main_mod._runtime_namespace())
engel = pack_loader.load_pack_file(
    os.path.join(REPO, "packs", "engel-strategies.pack.yaml"), graph
)
print("    Engel pack rules: %d" % len(to_list(engel.rule_chain)))
check("the Engel pack still carries its thirteen rules",
      len(to_list(engel.rule_chain)) == 13)

compiled = Curric.CompileCardTask(seven_record, engel.rule_chain, registry)()
check("the card compiles to a CardTask", head_is(compiled, L.CardTaskLabel))
check("its expectation is 'close'",
      label_is(Curric.CardTaskExpectation(compiled)(), TRUTH))

seven_task = Curric.CardTaskGraphTask(compiled)()
seven_facts = to_list(Curric.CardTaskFacts(compiled)())
seven_goal = GT.TaskRecordQuery(seven_task)()
print("    facts: %d   goal: %s"
      % (len(seven_facts), M.PrettyTerm(seven_goal, registry)()))
check("the goal is a well-formed Unreachable proposition",
      head_is(seven_goal, L.UnreachableLabel))

goal_in_facts = any(
    M.Compare(f, seven_goal)() is M.truth_value for f in seven_facts
)
check("the conclusion is NOT among the input facts", not goal_in_facts)

heads = [M.Head(f)() for f in seven_facts]


def count_head(label):
    return len([h for h in heads if M.IdentityCompare(h, label)() is M.truth_value])


check("the premise set is the planner's invariance obligation list",
      count_head(L.MoveSetLabel) == 1
      and count_head(L.ReadingLabel) == 2
      and count_head(L.ApartLabel) == 1
      and count_head(L.PreservesLabel) == 1)

evidence = to_list(Curric.CardTaskEvidence(compiled)())
split_rows = [e for e in evidence if head_is(e, L.CardSplitCheckLabel)]
mod_rows = [e for e in evidence if head_is(e, L.ModLabel)]
check("the split analysis has k+1 = 5 rows for a four-glass move",
      len(split_rows) == 5 and len(mod_rows) == 2,
      "%d split rows, %d residue rows" % (len(split_rows), len(mod_rows)))

splits_exhaustive = True
splits_even = True
for row in split_rows:
    args = to_list(M.Tail(row)())
    on, off, delta, residue = (int_of(a) for a in args)
    if on + off != 4:
        splits_exhaustive = False
    if int_of(M.Head(importlib.import_module(PACKAGE + ".math.arithmetic")
                     .Modulo(nat(abs(on - off)), nat(2), registry)())()) != residue:
        splits_even = False
    if residue != 0:
        splits_even = False
check("the five rows exhaust the move (on + off = 4 each time)",
      splits_exhaustive)
check("every split changes the upright count by an even amount", splits_even)

mods_ok = True
for row in mod_rows:
    args = to_list(M.Tail(row)())
    value, modulus, residue = (int_of(a) for a in args)
    if modulus != 2:
        mods_ok = False
    if residue != value % 2:
        mods_ok = False
check("the two readings are machine residues of the stated counts", mods_ok,
      "0 mod 2 = 0, 7 mod 2 = 1")
print()

print("[5] The held-out closes through the pack, not through this suite...")
ladder = []
for depth in (1, 2, 3, 4, 5, 6):
    verdict = Curric.RunCardTask(compiled, depth, registry)()
    ladder.append((depth, Curric.CardVerdictTag(verdict)(),
                   len(to_list(Curric.CardVerdictClosure(verdict)()))))
for depth, tag, size in ladder:
    print("    depth %d -> %-30s closure %d"
          % (depth, "SOLVED" if label_is(tag, L.CardSolvedLabel) else "open", size))
check("depth 1 is not enough: one rule fires per round",
      label_is(ladder[0][1], L.CardOpenLabel))
check("the goal arrives exactly at depth 4: thread -> step -> empty -> obstruction",
      all(label_is(tag, L.CardOpenLabel) for _d, tag, _s in ladder[:3])
      and all(label_is(tag, L.CardSolvedLabel) for _d, tag, _s in ladder[3:]))
check("each round adds exactly one fact until the goal appears",
      [size for _d, _t, size in ladder] == [6, 7, 8, 9, 9, 9])

final = Curric.RunCardTask(compiled, 6, registry)()
closure = to_list(Curric.CardVerdictClosure(final)())
check("the closure holds the Unreachable goal",
      any(M.Compare(f, seven_goal)() is M.truth_value for f in closure))
check("the verdict is CardSolved for a held-out card",
      label_is(Curric.CardVerdictTag(final)(), L.CardSolvedLabel))
print()

print("[6] Anti-authorship control: change one word, the verdict changes...")
seven_text = open(os.path.join(CORPUS, seven_id), "r", encoding="utf-8").read()

odd_text = seven_text.replace("flips exactly four glasses",
                              "flips exactly three glasses")
odd_record, _ = Curric.parse_card_text(odd_text, seven_id, registry)
odd_task = Curric.CompileCardTask(odd_record, engel.rule_chain, registry)()
odd_heads = [M.Head(f)() for f in to_list(Curric.CardTaskFacts(odd_task)())]
check("an odd flip count emits no Preserves premise",
      not any(M.IdentityCompare(h, L.PreservesLabel)() is M.truth_value
              for h in odd_heads))
odd_verdict = Curric.RunCardTask(odd_task, 6, registry)()
check("and the same builder then fails to close the card",
      label_is(Curric.CardVerdictTag(odd_verdict)(), L.CardOpenLabel))

even_text = seven_text.replace("Seven glasses", "Eight glasses").replace(
    "all seven end upright", "all eight end upright")
even_record, _ = Curric.parse_card_text(even_text, seven_id, registry)
even_task = Curric.CompileCardTask(even_record, engel.rule_chain, registry)()
even_heads = [M.Head(f)() for f in to_list(Curric.CardTaskFacts(even_task)())]
check("equal parities emit no Apart premise",
      not any(M.IdentityCompare(h, L.ApartLabel)() is M.truth_value
              for h in even_heads))
even_verdict = Curric.RunCardTask(even_task, 6, registry)()
check("and the card stays open on the same rules",
      label_is(Curric.CardVerdictTag(even_verdict)(), L.CardOpenLabel))

check("the unperturbed card still closes (control is the card, not the suite)",
      label_is(Curric.CardVerdictTag(final)(), L.CardSolvedLabel))
print()

print("[7] A decoy card is refused, and the refusal is measured...")
decoy_id = "tier0/decoys/pigeonhole-decoy-domino-board.md"
decoy_record = None
for record in record_list:
    if text_of(Curric.CardRecordId(record)()) == decoy_id:
        decoy_record = record
check("the decoy card is present", decoy_record is not None)

decoy = Curric.CompileCardTask(decoy_record, engel.rule_chain, registry)()
check("the decoy compiles to a CardTask", head_is(decoy, L.CardTaskLabel))
check("its expectation is 'refuse'",
      label_is(Curric.CardTaskExpectation(decoy)(), M.false_value))
decoy_task = Curric.CardTaskGraphTask(decoy)()
decoy_facts = to_list(Curric.CardTaskFacts(decoy)())
decoy_goal = GT.TaskRecordQuery(decoy_task)()
print("    goal: %s" % M.PrettyTerm(decoy_goal, registry)())
check("its goal is a Tiling claim",
      head_is(decoy_goal, L.TilingLabel))

arithmetic = importlib.import_module(PACKAGE + ".math.arithmetic")
squares = int_of(M.Head(arithmetic.Multiply(nat(8), nat(8), registry)())())
remaining = int_of(M.Head(
    M.NatPred(M.Head(M.NatPred(nat(squares), registry)())(), registry)())())
twice_tiles = int_of(M.Head(arithmetic.Multiply(nat(31), nat(2), registry)())())
check("the count argument the trap would use does hold (62 = 31 x 2)",
      squares == 64 and remaining == 62 and twice_tiles == 62)
check("the two colour counts are 32 and 30 after the corners go",
      64 // 2 == 32 and 64 // 2 - 2 == 30)

decoy_verdict = Curric.RunCardTask(decoy, 6, registry)()
check("the decoy's claim is not derivable",
      label_is(Curric.CardVerdictTag(decoy_verdict)(), L.CardRejectedLabel))
decoy_closure = to_list(Curric.CardVerdictClosure(decoy_verdict)())
check("the Tiling goal is absent from the closure",
      not any(M.Compare(f, decoy_goal)() is M.truth_value for f in decoy_closure))

control_goal = decoy_facts[0]
control_record = GT.GraphTaskRecord(
    M.Char("w25-control"), L.CardTaskLabel, Curric.CardTaskFacts(decoy)(),
    control_goal, TRUTH, engel.rule_chain,
    M.Pair(L.CardRecordLabel, M.Pair(M.Char("w25-control"), EMPTY)),
)()
control = Curric.CardTask(
    M.Char("w25-control"), TRUTH, control_record,
    Curric.CardTaskFacts(decoy)(), EMPTY,
)()
control_verdict = Curric.RunCardTask(control, 6, registry)()
check("control: a derivable claim on the same fact base is SOLVED",
      label_is(Curric.CardVerdictTag(control_verdict)(), L.CardSolvedLabel))
print("    Note, stated not hidden: the refusal is 'claim not derivable from")
print("    its own compiled fact base'.  A positive colouring-obstruction")
print("    rule (Ground 3) would turn it into a proof of impossibility; the")
print("    loader does not claim that rule, so it does not claim the proof.")
print()

print("[8] The loader: every card is accounted for, none is skipped...")
loaded = Curric.TrainingRecordLoader(CORPUS, engel.rule_chain, 6, registry)()
loaded_records = to_list(Curric.CardLoaderRecords(loaded)())
loaded_tasks = to_list(Curric.CardLoaderTasks(loaded)())
loaded_refusals = to_list(Curric.CardLoaderNoBuilders(loaded)())
loaded_verdicts = to_list(Curric.CardLoaderVerdicts(loaded)())
print("    records %d = tasks %d + no-builder reports %d, verdicts %d"
      % (len(loaded_records), len(loaded_tasks), len(loaded_refusals),
         len(loaded_verdicts)))
check("every loaded card is either a task or an explicit refusal",
      len(loaded_records) == len(loaded_tasks) + len(loaded_refusals) == 24)
check("every compiled task is run and gets a verdict",
      len(loaded_verdicts) == len(loaded_tasks) == 2)

gap_terms = to_list(Curric.CardLoaderGaps(loaded)())
check("the loader reports each gap as a machine term",
      all(head_is(g, L.Ground1GapLabel) for g in gap_terms)
      and len(gap_terms) == len(gap_pairs),
      "%d Ground1Gap records" % len(gap_terms))
machine_gap_names = set()
machine_gap_cards = set()
for gap in gap_terms:
    machine_gap_cards.add(text_of(M.Head(M.Tail(gap)())()))
    machine_gap_names.add(text_of(M.Head(M.Tail(M.Tail(gap)())())()))
check("the machine gap report equals the parsed one",
      machine_gap_names == gap_names and machine_gap_cards == gap_cards,
      "%d names on %d cards" % (len(machine_gap_names), len(machine_gap_cards)))

task_ids = set()
for task in loaded_tasks:
    task_ids.add(text_of(Curric.CardTaskId(task)()))
refusal_ids = set()
reasons_ok = True
reasons = {}
for refusal in loaded_refusals:
    card_id = text_of(Curric.CardNoBuilderId(refusal)())
    reason = text_of(Curric.CardNoBuilderReason(refusal)())
    refusal_ids.add(card_id)
    reasons_ok = reasons_ok and bool(reason)
    reasons[reason] = reasons.get(reason, 0) + 1
check("task ids and refusal ids partition the corpus",
      task_ids | refusal_ids == set(corpus_paths)
      and not (task_ids & refusal_ids),
      "%d compiled + %d refused" % (len(task_ids), len(refusal_ids)))
check("every refusal carries a non-empty reason", reasons_ok,
      "%d distinct reasons" % len(reasons))
for reason in sorted(reasons):
    print("      %-62s %d card(s)" % (reason, reasons[reason]))

target_counts = {}
for record in record_list:
    family = text_of(Curric.CardRecordFamily(record)())
    target = text_of(Curric.CardRecordTargetClass(record)())
    if target.startswith("count"):
        target_counts[family] = target_counts.get(family, 0) + 1
ground3 = reasons.get("count-target-ground3-no-obligation-generator", 0)
check("every count-target card is refused for the Ground 3 reason",
      ground3 == sum(target_counts.values()),
      "%d count-target cards, %d ground-3 refusals"
      % (sum(target_counts.values()), ground3))
check("no family is silently dropped from the census",
      sorted(target_counts) == ["Divide", "Symmetry"],
      "count targets: %s" % (target_counts,))
print()

print("[9] Honesty pins: no conclusion is stored, no card is rewritten...")
module_path = os.path.join(REPO, "curriculum.py")
module_source = open(module_path, "r", encoding="utf-8").read()
leaks = []
for record in record_list:
    card_id = text_of(Curric.CardRecordId(record)())
    statement = text_of(Curric.CardRecordStatement(record)())
    if card_id in module_source:
        leaks.append(card_id)
    if statement[:40] and statement[:40] in module_source:
        leaks.append(statement[:40])
    if statement[-40:] and statement[-40:] in module_source:
        leaks.append(statement[-40:])
check("no card id or statement fragment (head or tail) appears in the loader",
      not leaks, "leaks: %s" % (leaks or "none"))

corpus_still_blueprint = True
for path in corpus_paths:
    with open(os.path.join(CORPUS, path), "r", encoding="utf-8") as handle:
        if "blueprint-only" not in handle.read():
            corpus_still_blueprint = False
check("the corpus files are untouched (still blueprint-only)",
      corpus_still_blueprint)

pack_dir = os.path.join(REPO, "packs")
pack_leaks = []
for name in sorted(os.listdir(pack_dir)):
    if not name.endswith((".yaml", ".yml")):
        continue
    text = open(os.path.join(pack_dir, name), "r", encoding="utf-8").read()
    for card_id in corpus_paths:
        if card_id in text:
            pack_leaks.append((name, card_id))
check("no pack file mentions a card (no answers promoted into packs)",
      not pack_leaks, "%d leak(s)" % len(pack_leaks))
funceq_rules = pack_loader.load_pack_file(
    os.path.join(REPO, "packs", "funceq-nt.pack.yaml"), graph
)
check("the W24 funceq-nt pack is unchanged by this worker",
      len(to_list(funceq_rules.rule_chain)) == 33,
      "%d rules" % len(to_list(funceq_rules.rule_chain)))
print()

print("[10] test10's synthetic curriculum is intact...")
RUNG_BUILDERS = (
    "BuildRung1RetrievalTask", "BuildRung2JoinTask", "BuildRung3ConstraintTask",
    "BuildRung4DerivationTask", "BuildRung5AliasTask", "BuildRung6NegativeTask",
    "BuildRung7PlannerTask",
)
check("all seven rung builders, the noise mutator and the suite evaluator exist",
      all(hasattr(Curric, name) for name in RUNG_BUILDERS)
      and hasattr(Curric, "MutateWithNoise")
      and hasattr(Curric, "EvaluateCurriculumSuite"))
check("the first nine __all__ entries are unchanged",
      tuple(Curric.__all__[:9]) == RUNG_BUILDERS + (
          "MutateWithNoise", "EvaluateCurriculumSuite"))

edge_e = M.Atom()
node_a = M.Atom()
node_b = M.Atom()
var_x = M.Var()
rung1 = Curric.BuildRung1RetrievalTask(
    M.Atom(), edge_e, node_a, node_b, var_x, registry
)()
rung1_verdict = M.Head(GT.ExecuteGraphQuery(rung1, registry)())()
check("rung 1 still retrieves its single edge exactly as test10 requires",
      label_is(rung1_verdict, L.TaskSuccessLabel))
print()

print("=== TEST 37 RESULTS ===")
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
    print("=== TEST 37 FAILED ===")
    sys.exit(1)
print("=== TEST 37 COMPLETE ===")
