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
import urllib.parse
from hashlib import sha256

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
            value = getattr(Lmod, token[2:])
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
    return (
        WORKER_STATUS_OK(),
        serialize_term(result_store),
        serialize_ledger(ledger),
        serialize_term(frontier_version),
    )


def _worker_entry(queue, serialized_version, serialized_store,
                  serialized_budget, serialized_config, slice_index_text,
                  slice_count_text):
    queue.put(worker_task(
        serialized_version,
        serialized_store,
        serialized_budget,
        serialized_config,
        slice_index_text,
        slice_count_text,
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
        outputs.append(queue.get())
        process.join()
        queue.close()
    return outputs


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
    for status_text, store_blob, ledger_blob, _frontier_blob in outputs:
        reversed_outputs = M.Pair(
            M.Pair(
                M.Char(status_text),
                M.Pair(
                    M.Char(store_blob.decode("utf-8")),
                    M.Pair(M.Char(ledger_blob.decode("utf-8")), M.EmptyList),
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
    remaining_outputs = ordered_outputs
    while M.IdentityCompare(remaining_outputs, M.EmptyList)() is M.false_value:
        entry = M.Head(remaining_outputs)()
        status = M.Head(entry)()
        if M.Compare(status, WORKER_STATUS_OK)() is M.truth_value:
            serialized_store = M.Head(M.Tail(entry)())()
            serialized_ledger = M.Head(M.Tail(M.Tail(entry)())())()
            worker_ledger = deserialize_ledger(
                serialized_ledger().encode("utf-8"), ledger.registry)
            reversed_claims = M.Pair(worker_ledger.records, reversed_claims)
            merged_store = deserialize_term(serialized_store().encode("utf-8"))
        remaining_outputs = M.Tail(remaining_outputs)()
    worker_records = M.EmptyList
    while M.IdentityCompare(reversed_claims, M.EmptyList)() is M.false_value:
        worker_records = M.Pair(M.Head(reversed_claims)(), worker_records)
        reversed_claims = M.Tail(reversed_claims)()

    merged = Gmod.MergeFrontiers(graph_version, worker_records, ledger)()
    merged_version = M.Head(merged)()
    conflicts = M.Head(M.Tail(merged)())()

    activated = Gmod.AutonomyCycle(
        merged_version,
        merged_store,
        ledger,
        budget,
        generator_config,
    )()
    final_version = M.Head(activated)()
    final_store = M.Head(M.Tail(activated)())()
    report = M.Head(M.Tail(M.Tail(activated)())())()
    return M.Pair(
        final_version,
        M.Pair(
            final_store,
            M.Pair(report, M.Pair(conflicts, M.EmptyList)),
        ),
    )


def content_hash(payload_bytes):
    return sha256(payload_bytes).hexdigest()


def serialize_delta(parent_version, child_version, fire_record):
    from .graph import HashRef

    parent_hash = content_hash(serialize_version(parent_version))
    child_hash = content_hash(serialize_version(child_version))
    parent_ref = HashRef(M.Char(parent_hash))()
    child_ref = HashRef(M.Char(child_hash))()
    delta_term = M.Pair(parent_ref, M.Pair(fire_record, M.Pair(child_ref, M.EmptyList)))
    return serialize_term(delta_term)


def apply_delta(version, delta_bytes):
    try:
        delta_term = deserialize_term(delta_bytes)
    except Exception:
        return M.Pair(Lmod.ReasonNetworkLabel, M.Pair(M.Char("delta-corrupt"), M.EmptyList))

    if M.IsPair(delta_term)() is M.false_value:
        return M.Pair(Lmod.ReasonNetworkLabel, M.Pair(M.Char("delta-corrupt"), M.EmptyList))
    parent_ref = M.Head(delta_term)()
    tail1 = M.Tail(delta_term)()
    if M.IsPair(tail1)() is M.false_value:
        return M.Pair(Lmod.ReasonNetworkLabel, M.Pair(M.Char("delta-corrupt"), M.EmptyList))
    fire_record = M.Head(tail1)()
    tail2 = M.Tail(tail1)()
    if M.IsPair(tail2)() is M.false_value:
        return M.Pair(Lmod.ReasonNetworkLabel, M.Pair(M.Char("delta-corrupt"), M.EmptyList))
    child_ref = M.Head(tail2)()

    local_hash = content_hash(serialize_version(version))
    parent_hash_char = M.Head(M.Tail(parent_ref)())()
    expected_parent_hash = parent_hash_char()
    if local_hash != expected_parent_hash:
        return M.Pair(
            Lmod.ReasonNetworkLabel,
            M.Pair(
                M.Char("parent-mismatch"),
                M.Pair(M.Char(local_hash), M.Pair(parent_hash_char, M.EmptyList)),
            ),
        )

    law = fire_record
    if M.IsPair(fire_record)() is M.truth_value:
        tag = M.Head(fire_record)()
        if (
            M.TermEqual(tag, Lmod.FiringRecordLabel)() is M.truth_value
            or M.TermEqual(tag, Lmod.FireLabel)() is M.truth_value
        ):
            law = M.Head(M.Tail(fire_record)())()
        elif M.TermEqual(tag, Lmod.NextLabel)() is M.truth_value:
            fire_sub = M.Head(M.Tail(M.Tail(fire_record)())())()
            if M.IsPair(fire_sub)() is M.truth_value:
                law = M.Head(M.Tail(fire_sub)())()

    from . import graph as Gmod

    installed = Gmod.InstalledLaws(version)()
    matching_law = M.EmptyList
    rem = installed
    while M.IdentityCompare(rem, M.EmptyList)() is M.false_value:
        cand = M.Head(rem)()
        if M.Compare(cand, law)() is M.truth_value:
            matching_law = cand
            break
        rem = M.Tail(rem)()

    if M.IdentityCompare(matching_law, M.EmptyList)() is M.truth_value:
        return M.Pair(Lmod.ReasonNetworkLabel, M.Pair(M.Char("law-absent"), M.EmptyList))

    ordering = M.Pair(matching_law, M.EmptyList)
    replayed = Gmod.FireAny(version, Gmod.DanglingForbid()(), ordering=ordering)()
    replayed_version = M.Head(replayed)()
    if M.IdentityCompare(replayed_version, M.EmptyList)() is M.truth_value:
        return M.Pair(Lmod.ReasonNetworkLabel, M.Pair(M.Char("replay-failed"), M.EmptyList))

    child_hash_char = M.Head(M.Tail(child_ref)())()
    expected_child_hash = child_hash_char()
    replayed_hash = content_hash(serialize_version(replayed_version))
    if replayed_hash != expected_child_hash:
        return M.Pair(
            Lmod.ReasonNetworkLabel,
            M.Pair(
                M.Char("hash-mismatch"),
                M.Pair(M.Char(replayed_hash), M.Pair(child_hash_char, M.EmptyList)),
            ),
        )
    return replayed_version


def verify_checkpoint_hash_chain(path):
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    if len(lines) < 4 or lines[0] != _WIRE_HEADER:
        return M.false_value
    version_bytes = lines[1].encode("utf-8")
    computed_hash = content_hash(version_bytes)
    if len(lines) > 4:
        recorded_hash = lines[4].strip()
        if recorded_hash and recorded_hash != computed_hash:
            return M.false_value
    return M.truth_value


def save_checkpoint(path, graph_version, proposal_store, ledger):
    version_bytes = serialize_version(graph_version)
    lines = [
        _WIRE_HEADER,
        version_bytes.decode("utf-8"),
        serialize_proposal_store(proposal_store).decode("utf-8"),
        serialize_ledger(ledger).decode("utf-8"),
        content_hash(version_bytes),
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
