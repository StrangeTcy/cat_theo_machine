"""Step 42: deterministic canonical byte encoding for machine terms.

WIRE FORMAT (version WIRE1), one UTF-8 line per section:
  term      := atom | "(" term " " term ")"        (a Pair is "(head tail)")
  atom      := "E"                                 M.EmptyList
             | "T" | "F"                           M.truth_value / M.false_value
             | "Z"                                 M.Zero
             | "V"                                 M.VarTag
             | "L:" name                           labels-module singleton
             | "C:" pct                             M.Char (percent-encoded symbol)
             | "G:" digits                          M.GMPRep (decimal text)
             | "N:" digits                          Nat atom (cached GMPRep value)
             | "A:" index                           anonymous atom (Thingy et al.)
Anonymous atoms are numbered by first appearance in head-first traversal
order, so identity sharing inside one blob is preserved and re-serializing
a deserialized blob reproduces the bytes exactly (canonical fixed point).
Anonymous atoms deserialize as fresh Thingy objects: sharing inside one
blob survives, identity across blobs does not — durable structures should
carry labeled nodes. Char and GMPRep tokens are interned per blob, and
Pairs are hash-consed per blob (same head and tail identity -> same Pair
object), so identity sharing of repeated subterms — graph nodes referenced
from both a version's node list and its edges — survives the round trip.
Traversal and parsing are iterative: no recursion limits on deep chains.
Checkpoints (save_checkpoint/load_checkpoint) store version, proposal
store, and ledger records/misses as one WIRE1 document of four sections.
This module is substrate-only: it must never import from search/.
"""

from __future__ import annotations

import os
import sys
import urllib.parse

from . import machine as M
from . import labels as Lmod

HOST_PROCESS_RESERVE = 2


def host_process_budget(requested=0):
    """The one process ceiling every fan-out in the system draws from.

    Three separate places used to claim `cpu_count()` independently -- the
    daemon's worker fan-out, the search comparison layer, and the search
    worker launcher -- so a single conversation could hold three times the
    machine.  They all read this instead.

    `HOST_PROCESS_RESERVE` cores are left for the operating system and the
    foreground conversation, so a proof never takes the whole laptop.  An
    explicit positive `requested` overrides autoscaling and is honoured as
    given, since that is a direct instruction rather than a guess.
    """
    if requested:
        return requested
    import multiprocessing

    try:
        available = multiprocessing.cpu_count()
    except NotImplementedError:
        return 0
    available = available - HOST_PROCESS_RESERVE
    if available < 2:
        return 0
    return available


def share_process_budget(claimants):
    """Split the host budget between concurrent fan-outs.

    `claimants` is how many independent fan-outs are live at once.  One
    claimant takes the whole budget; two share it.  A share below two is
    no fan-out at all, since a lone worker is a process boundary crossed
    for nothing.
    """
    budget = host_process_budget(0)
    if budget < 1:
        return 0
    if claimants < 2:
        return budget
    share = budget // claimants
    if share < 2:
        return 0
    return share


_WIRE_HEADER = "WIRE1"

WORKER_STATUS_OK = M.Char("ok")
WORKER_STATUS_REFUSED = M.Char("refused-nonzero-activations")
WORKER_STATUS_FAILED = M.Char("worker-failed")
# The substrate spends interpreter stack per machine step -- every Edge
# construction, every recursive comparison -- and a real taught graph
# walks deeper than the interpreter's default ceiling. Host process
# configuration, like the timeout beside it: the machine's own bounds
# live in its budgets and caps.
WORKER_RECURSION_LIMIT = 30000
WORKER_JOIN_TIMEOUT = 300.0


def _label_map():
    mapping = {}
    for name in sorted(vars(Lmod)):
        if name.endswith("Label") and name != "ConstructorLabel":
            value = getattr(Lmod, name)
            if getattr(value, "id", None) is not None:
                mapping[value] = name
    return mapping


def _special_atoms():
    return {
        M.EmptyList: "E",
        M.truth_value: "T",
        M.false_value: "F",
        M.Zero: "Z",
        M.VarTag: "V",
    }


def serialize_term(term):
    labels = _label_map()
    specials = _special_atoms()
    anonymous = {}
    pieces = []
    close_marker = object()
    work = [term]
    while work:
        current = work.pop()
        if current is close_marker:
            pieces.append(")")
            continue
        if current in specials:
            pieces.append(specials[current])
            continue
        if M.IsPair(current)() is M.truth_value:
            pieces.append("(")
            work.append(close_marker)
            work.append(M.Tail(current)())
            work.append(M.Head(current)())
            continue
        if current in labels:
            pieces.append("L:" + labels[current])
            continue
        symbol = getattr(current, "symbol", None)
        if symbol is not None:
            pieces.append("C:" + urllib.parse.quote(symbol, safe=""))
            continue
        if getattr(current, "_mpz_value", None) is not None:
            pieces.append("G:" + str(current()))
            continue
        cached = None
        try:
            cached = current()
        except Exception:
            cached = None
        if cached is not None and getattr(cached, "_mpz_value", None) is not None:
            pieces.append("N:" + str(cached()))
            continue
        if current not in anonymous:
            anonymous[current] = len(anonymous)
        pieces.append("A:" + str(anonymous[current]))
    return " ".join(pieces).encode("utf-8")


def deserialize_term(blob):
    text = blob.decode("utf-8")
    tokens = text.replace("(", " ( ").replace(")", " ) ").split()
    anonymous = {}
    interned = {}
    consed = {}
    stack = [[]]
    for token in tokens:
        if token == "(":
            stack.append([])
            continue
        if token == ")":
            frame = stack.pop()
            cons_key = (id(frame[0]), id(frame[1]))
            if cons_key not in consed:
                consed[cons_key] = M.Pair(frame[0], frame[1])
            stack[-1].append(consed[cons_key])
            continue
        if token == "E":
            value = M.EmptyList
        elif token == "T":
            value = M.truth_value
        elif token == "F":
            value = M.false_value
        elif token == "Z":
            value = M.Zero
        elif token == "V":
            value = M.VarTag
        elif token.startswith("L:"):
            try:
                value = getattr(Lmod, token[2:])
            except AttributeError:
                # A checkpoint written by a labels.py this branch does
                # not carry. The token keeps its place as an interned,
                # inert atom -- distinct unknown labels stay distinct,
                # and every head comparison against known labels fails
                # -- instead of sinking the whole boot.
                if token not in interned:
                    interned[token] = M.Thingy()
                value = interned[token]
        elif token.startswith("C:"):
            if token not in interned:
                interned[token] = M.Char(urllib.parse.unquote(token[2:]))
            value = interned[token]
        elif token.startswith("G:"):
            if token not in interned:
                interned[token] = M.GMPRep(token[2:])
            value = interned[token]
        elif token.startswith("N:"):
            if token not in interned:
                rebuilt = M.NatFromRep(M.GMPRep(token[2:]), M.AllConstructors)()
                interned[token] = M.Head(rebuilt)()
            value = interned[token]
        else:
            index = token[2:]
            if index not in anonymous:
                anonymous[index] = M.Thingy()
            value = anonymous[index]
        stack[-1].append(value)
    return stack[0][0]


def serialize_version(graph_version):
    return serialize_term(graph_version)


def deserialize_version(blob):
    return deserialize_term(blob)


def serialize_proposal_store(proposal_store):
    return serialize_term(proposal_store)


def deserialize_proposal_store(blob):
    return deserialize_term(blob)


def serialize_ledger(ledger):
    bundle = M.Pair(ledger.records, M.Pair(ledger.misses, M.EmptyList))
    return serialize_term(bundle)


def deserialize_ledger(blob, registry=M.EmptyList):
    from .graph import FiringLedger

    bundle = deserialize_term(blob)
    ledger = FiringLedger(registry)
    ledger.records = M.Head(bundle)()
    ledger.results = ledger.records
    ledger.misses = M.Head(M.Tail(bundle)())()
    return ledger


def worker_task(serialized_version, serialized_store, serialized_budget,
                serialized_generator_config, slice_index_text, slice_count_text):
    """Step 43: one worker turn — generate and fire, NEVER activate.

    Every argument crosses the wire as canonical WIRE1 bytes (the budget and
    generator config are the same M association chains AutonomyCycle reads).
    The budget MUST carry max_activations = Zero; anything else is refused
    with the Char atom "refused-nonzero-activations" before any work runs.
    Returns (serialized proposal store, serialized ledger, serialized
    frontier version) — claims only; the coordinator re-validates all of it.
    """
    from . import graph as Gmod

    budget = deserialize_term(serialized_budget)
    max_activations = M.EmptyList
    remaining_budget = budget
    while M.IdentityCompare(remaining_budget, M.EmptyList)() is M.false_value:
        association = M.Head(remaining_budget)()
        if M.Compare(
            M.Head(association)(),
            Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
        )() is M.truth_value:
            max_activations = M.Head(M.Tail(association)())()
        remaining_budget = M.Tail(remaining_budget)()
    if M.IdentityCompare(max_activations, M.Zero)() is M.false_value:
        return (WORKER_STATUS_REFUSED(), b"", b"", b"")

    graph_version = deserialize_term(serialized_version)
    proposal_store = deserialize_term(serialized_store)
    generator_config = deserialize_term(serialized_generator_config)
    ledger = Gmod.FiringLedger(M.EmptyList)
    generator_config = M.Pair(
        M.Pair(
            Gmod.AUTONOMY_GENERATOR_SLICE_INDEX_KEY,
            M.Pair(M.GMPRep(slice_index_text), M.EmptyList),
        ),
        M.Pair(
            M.Pair(
                Gmod.AUTONOMY_GENERATOR_SLICE_COUNT_KEY,
                M.Pair(M.GMPRep(slice_count_text), M.EmptyList),
            ),
            generator_config,
        ),
    )
    cycle = Gmod.AutonomyCycle(
        graph_version,
        proposal_store,
        ledger,
        budget,
        generator_config,
    )()
    frontier_version = M.Head(cycle)()
    result_store = M.Head(M.Tail(cycle)())()
    report = M.Head(M.Tail(M.Tail(cycle)())())()
    # What this worker did, said in its own numbers: the report the
    # cycle recorded, not a count taken here.
    scanned_pairs = "0"
    scanned_patterns = "0"
    found = "0"

    def report_count(value):
        # The report's counts ride in the same tolerant shape the
        # daemon's own summary reads: a count, or a pair holding a
        # count, or a pair holding that -- whichever the entry carries.
        candidate = value
        if M.IsPair(candidate)() is M.truth_value:
            candidate = M.Head(candidate)()
            if M.IsPair(candidate)() is M.truth_value:
                candidate = M.Head(candidate)()
        rep = M.NatRepOf(candidate, M.AllConstructors)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            return M.GMPRepText(rep)()
        return "0"

    report_scan = report
    while M.IdentityCompare(
        report_scan, M.EmptyList,
    )() is M.false_value:
        report_entry = M.Head(report_scan)()
        report_key = M.Head(report_entry)()
        report_value = M.Head(M.Tail(report_entry)())()
        if M.Compare(
            report_key, Gmod.AUTONOMY_REPORT_CORRESPONDENCE_SCAN_KEY,
        )() is M.truth_value:
            scanned_pairs = report_count(report_value)
            scanned_patterns = report_count(
                M.Tail(report_value)(),
            )
        elif M.Compare(
            report_key,
            Gmod.AUTONOMY_REPORT_GENERATED_CORRESPONDENCES_KEY,
        )() is M.truth_value:
            found = report_count(report_value)
        report_scan = M.Tail(report_scan)()
    report_text = (
        "scanned "
        + scanned_pairs
        + " rule pairs and "
        + scanned_patterns
        + " subgraph shapes; found "
        + found
        + " correspondence(s)"
    )
    return (
        WORKER_STATUS_OK(),
        serialize_term(result_store),
        serialize_ledger(ledger),
        serialize_term(frontier_version),
        report_text.encode("utf-8"),
    )


def _worker_entry(queue, serialized_version, serialized_store,
                  serialized_budget, serialized_config, slice_index_text,
                  slice_count_text):
    # A worker is a fresh interpreter under spawn: it sets its own
    # stack depth, since it inherits no one's.
    sys.setrecursionlimit(WORKER_RECURSION_LIMIT)
    try:
        queue.put(worker_task(
            serialized_version,
            serialized_store,
            serialized_budget,
            serialized_config,
            slice_index_text,
            slice_count_text,
        ))
    except KeyboardInterrupt:
        # A console interrupt reaches every attached process; the
        # worker bows out quietly instead of spewing its death stack.
        return None
    except BaseException as failure:
        # A worker that dies silently wedges the coordinator forever:
        # it waits on a queue no one will ever fill again. A failed
        # worker reports itself, and the cycle goes on without its
        # claim.
        queue.put((
            WORKER_STATUS_FAILED(),
            str(failure).encode("utf-8"),
            b"",
            b"",
            b"",
        ))


def run_workers(graph_version, proposal_store, budget, generator_config,
                worker_count):
    """Step 43: fan one generation turn out over a multiprocessing Pool.

    Worker i mines candidate slice i of worker_count; per-worker budgets are
    the caller's budget with max_activations forced to Zero. Outputs are
    collected in worker order (deterministic)."""
    import multiprocessing

    serialized_version = serialize_term(graph_version)
    serialized_store = serialize_term(proposal_store)
    zeroed = M.EmptyList
    remaining_budget = budget
    from . import graph as Gmod

    reversed_budget = M.EmptyList
    while M.IdentityCompare(remaining_budget, M.EmptyList)() is M.false_value:
        association = M.Head(remaining_budget)()
        if M.Compare(
            M.Head(association)(),
            Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
        )() is M.truth_value:
            association = M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                M.Pair(M.Zero, M.EmptyList),
            )
        reversed_budget = M.Pair(association, reversed_budget)
        remaining_budget = M.Tail(remaining_budget)()
    zeroed = M.EmptyList
    while M.IdentityCompare(reversed_budget, M.EmptyList)() is M.false_value:
        zeroed = M.Pair(M.Head(reversed_budget)(), zeroed)
        reversed_budget = M.Tail(reversed_budget)()
    serialized_budget = serialize_term(zeroed)
    serialized_config = serialize_term(generator_config)

    try:
        context = multiprocessing.get_context("fork")
    except ValueError:
        context = multiprocessing.get_context("spawn")
    workers = []
    index = 0
    while index < worker_count:
        queue = context.Queue()
        process = context.Process(
            target=_worker_entry,
            args=(
                queue,
                serialized_version,
                serialized_store,
                serialized_budget,
                serialized_config,
                str(index),
                str(worker_count),
            ),
        )
        process.start()
        workers.append((process, queue))
        index = index + 1
    outputs = []
    for process, queue in workers:
        try:
            outputs.append(queue.get(timeout=WORKER_JOIN_TIMEOUT))
        except Exception:
            process.terminate()
            outputs.append(
                (
                    WORKER_STATUS_FAILED(),
                    b"worker silent",
                    b"",
                    b"",
                    b"",
                ),
            )
        try:
            process.join(timeout=10)
        except Exception:
            pass
        queue.close()
    return outputs


def union_proposal_stores(first, second):
    """The entries of both stores, proposals taken once by structure.

    Each worker mines its slice from the same starting store, so the
    same entry returns from many workers; the findings differ. Entries
    are kept by proposal structure, first occurrence first, so the
    union is order-stable and no worker's finding is lost to another's.
    """
    from . import graph as Gmod

    merged_reversed = M.EmptyList
    scan = Gmod.ProposalStoreEntries(second)()
    while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
        merged_reversed = M.Pair(M.Head(scan)(), merged_reversed)
        scan = M.Tail(scan)()
    scan = Gmod.ProposalStoreEntries(first)()
    while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
        entry = M.Head(scan)()
        proposal = Gmod.ProposalEntryProposal(entry)()
        present = M.false_value
        inner = merged_reversed
        while M.IdentityCompare(inner, M.EmptyList)() is M.false_value:
            if M.Compare(
                Gmod.ProposalEntryProposal(M.Head(inner)())(),
                proposal,
            )() is M.truth_value:
                present = M.truth_value
                inner = M.EmptyList
            else:
                inner = M.Tail(inner)()
        if M.IdentityCompare(present, M.false_value)() is M.truth_value:
            merged_reversed = M.Pair(entry, merged_reversed)
        scan = M.Tail(scan)()
    kept = M.EmptyList
    while M.IdentityCompare(merged_reversed, M.EmptyList)() is M.false_value:
        kept = M.Pair(M.Head(merged_reversed)(), kept)
        merged_reversed = M.Tail(merged_reversed)()
    return Gmod.ProposalStore(kept)()


def distributed_cycle(graph_version, proposal_store, ledger, budget,
                      generator_config, worker_count):
    """Step 45: run_workers -> merge_frontiers -> single-process activation.

    A linear Next chain with exactly three links and no branching:

      1. run_workers fans generation and firing out; every worker budget has
         max_activations forced to Zero, so no worker can activate.
      2. MergeFrontiers folds the worker claims into the coordinator version
         by replaying each claimed law against the growing version. Worker
         frontier versions are deserialized only to be discarded: nothing is
         transplanted, and a claim that no longer matches becomes a Miss
         carrying ReasonStale.
      3. AutonomyCycle runs once in this process with the caller's own
         budget, which is the only place activation is permitted.

    Returns a four-link chain: version, store, report, conflicts.
    """
    from . import graph as Gmod

    outputs = run_workers(
        graph_version,
        proposal_store,
        budget,
        generator_config,
        worker_count,
    )

    # run_workers hands back host tuples across the process boundary; convert
    # them to a machine chain once, here, and walk that.
    reversed_outputs = M.EmptyList
    for worker_output in outputs:
        status_text = worker_output[0]
        store_blob = worker_output[1]
        ledger_blob = worker_output[2]
        report_blob = (
            worker_output[4] if len(worker_output) > 4 else b""
        )
        reversed_outputs = M.Pair(
            M.Pair(
                M.Char(status_text),
                M.Pair(
                    M.Char(store_blob.decode("utf-8")),
                    M.Pair(
                        M.Char(ledger_blob.decode("utf-8")),
                        M.Pair(
                            M.Char(report_blob.decode("utf-8")),
                            M.EmptyList,
                        ),
                    ),
                ),
            ),
            reversed_outputs,
        )
    ordered_outputs = M.EmptyList
    while M.IdentityCompare(reversed_outputs, M.EmptyList)() is M.false_value:
        ordered_outputs = M.Pair(M.Head(reversed_outputs)(), ordered_outputs)
        reversed_outputs = M.Tail(reversed_outputs)()

    reversed_claims = M.EmptyList
    merged_store = proposal_store
    worker_position = 0
    worker_total = len(outputs)
    remaining_outputs = ordered_outputs
    while M.IdentityCompare(remaining_outputs, M.EmptyList)() is M.false_value:
        entry = M.Head(remaining_outputs)()
        status = M.Head(entry)()
        worker_position = worker_position + 1
        if M.Compare(
            status, WORKER_STATUS_FAILED,
        )() is M.truth_value:
            failure_text = M.Head(M.Tail(entry)())()
            if M.IsPair(failure_text)() is M.truth_value:
                failure_text = M.Head(M.Tail(failure_text)())()
            print(
                "daemon: worker "
                + str(worker_position)
                + "/"
                + str(worker_total)
                + " failed ("
                + str(failure_text())
                + "); its claim is skipped",
                flush=True,
            )
        elif M.Compare(status, WORKER_STATUS_OK)() is M.truth_value:
            serialized_store = M.Head(M.Tail(entry)())()
            serialized_ledger = M.Head(M.Tail(M.Tail(entry)())())()
            worker_report = M.Head(
                M.Tail(M.Tail(M.Tail(entry)())())(),
            )()
            print(
                "daemon: worker "
                + str(worker_position)
                + "/"
                + str(worker_total)
                + ": "
                + str(worker_report()),
                flush=True,
            )
            worker_ledger = deserialize_ledger(
                serialized_ledger().encode("utf-8"), ledger.registry)
            reversed_claims = M.Pair(worker_ledger.records, reversed_claims)
            # Every worker mined its own slice from the same store; the
            # findings are the point of the fleet, so the stores are
            # unioned -- one worker's proposals are never dropped for
            # arriving beside another's.
            worker_store = deserialize_term(
                serialized_store().encode("utf-8"),
            )
            merged_store = union_proposal_stores(
                merged_store, worker_store,
            )
        remaining_outputs = M.Tail(remaining_outputs)()
    worker_records = M.EmptyList
    while M.IdentityCompare(reversed_claims, M.EmptyList)() is M.false_value:
        worker_records = M.Pair(M.Head(reversed_claims)(), worker_records)
        reversed_claims = M.Tail(reversed_claims)()

    merged = Gmod.MergeFrontiers(graph_version, worker_records, ledger)()
    merged_version = M.Head(merged)()
    conflicts = M.Head(M.Tail(merged)())()

    # The workers mined their slices; the coordinator activates and
    # fires. Mining again here, unsliced, would repeat the whole scan
    # the fleet just divided.
    activated = Gmod.AutonomyCycle(
        merged_version,
        merged_store,
        ledger,
        budget,
        M.EmptyList,
    )()
    final_version = M.Head(activated)()
    final_store = M.Head(M.Tail(activated)())()
    report = M.Head(M.Tail(M.Tail(activated)())())()
    # The report should say what the fleet found, not only what the
    # coordinator itself generated: the entries that entered the store
    # this cycle are counted from the unioned stores, and the finding
    # rides the report the daemon speaks.
    base_count_text = "0"
    base_scan = Gmod.ProposalStoreEntries(proposal_store)()
    while M.IdentityCompare(base_scan, M.EmptyList)() is M.false_value:
        base_scan = M.Tail(base_scan)()
        base_count_text = Gmod.GMPSuccText(base_count_text)()
    union_count_text = "0"
    union_scan = Gmod.ProposalStoreEntries(merged_store)()
    while M.IdentityCompare(union_scan, M.EmptyList)() is M.false_value:
        union_scan = M.Tail(union_scan)()
        union_count_text = Gmod.GMPSuccText(union_count_text)()
    added_text = Gmod.GMPSubText(
        union_count_text, base_count_text,
    )()
    if Gmod.GMPLessText(added_text, "0")() is M.truth_value:
        added_text = "0"
    # The count rides as a Nat in the same shape the cycle's own
    # entries carry, so every reader of the report -- the daemon's
    # summary and correspondence lines among them -- reads it the way
    # they read the cycle's own counts.
    from .mining import MineNatFromGMPRep

    added_nat = MineNatFromGMPRep(M.GMPRep(added_text))()
    report = M.Pair(
        M.Pair(
            Gmod.AUTONOMY_REPORT_GENERATED_CORRESPONDENCES_KEY,
            M.Pair(
                M.Pair(
                    added_nat,
                    M.Pair(M.EmptyList, M.EmptyList),
                ),
                M.EmptyList,
            ),
        ),
        report,
    )
    return M.Pair(
        final_version,
        M.Pair(
            final_store,
            M.Pair(report, M.Pair(conflicts, M.EmptyList)),
        ),
    )


def save_checkpoint(path, graph_version, proposal_store, ledger):
    lines = [
        _WIRE_HEADER,
        serialize_version(graph_version).decode("utf-8"),
        serialize_proposal_store(proposal_store).decode("utf-8"),
        serialize_ledger(ledger).decode("utf-8"),
    ]
    payload = "\n".join(lines) + "\n"
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        handle.write(payload)
    os.replace(temporary, path)
    return path


def load_checkpoint(path, registry=M.EmptyList):
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    if lines[0] != _WIRE_HEADER:
        return M.EmptyList
    graph_version = deserialize_version(lines[1].encode("utf-8"))
    proposal_store = deserialize_proposal_store(lines[2].encode("utf-8"))
    ledger = deserialize_ledger(lines[3].encode("utf-8"), registry)
    return M.Pair(
        graph_version,
        M.Pair(proposal_store, M.Pair(ledger, M.EmptyList)),
    )
