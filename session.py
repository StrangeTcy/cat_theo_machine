"""Step 51: the operational shell.

A session is a pure function from checkpoint to checkpoint plus reports.
No web UI, no async, no daemon, no network. `run_session` loads a
checkpoint, loops `distributed_cycle`, and after each cycle writes a new
checkpoint and a rendered curator report to disk.

A session stops on exactly three conditions:

  * the cycle budget `max_cycles` is exhausted;
  * quiescence -- a cycle with zero firings, zero generations and zero
    activations, so running again would change nothing;
  * any safety refusal -- the Step-49 floor reporting a violation stops
    the session rather than being retried.

Human decisions never enter mid-session. They enter between sessions
through two CLI verbs, `approve` and `countersign`, each of which
attaches the corresponding term to one pending proposal and re-serializes
the checkpoint. Neither verb activates anything: activation remains
`activate_proposal`'s alone, on the coordinator, inside a cycle.
"""

from . import machine as M
from . import graph as Gmod
from . import wire as Wmod


SESSION_STOP_CYCLES = M.Char("stop-max-cycles")
SESSION_STOP_QUIESCENT = M.Char("stop-quiescent")
SESSION_STOP_SAFETY = M.Char("stop-safety-refusal")

SESSION_VERB_APPROVE = M.Char("approve")
SESSION_VERB_COUNTERSIGN = M.Char("countersign")


class SessionCycleIsQuiescent(M.Edge):
    """A cycle changed nothing: no firings, no generation, no activation.

    Reads the ordinary AutonomyCycle report rather than counting anything
    itself, so quiescence is whatever the cycle already recorded.
    """

    def __init__(self, report):
        firings = M.EmptyList
        activated = M.EmptyList
        handles = M.EmptyList
        compositions = M.EmptyList
        remaining = report
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            key = M.Head(entry)()
            value = M.Head(M.Tail(entry)())()
            if M.Compare(key, Gmod.AUTONOMY_REPORT_FIRINGS_KEY)() is M.truth_value:
                firings = value
            elif M.Compare(
                key,
                Gmod.AUTONOMY_REPORT_ACTIVATED_KEY,
            )() is M.truth_value:
                activated = value
            elif M.Compare(
                key,
                Gmod.AUTONOMY_REPORT_GENERATED_HANDLES_KEY,
            )() is M.truth_value:
                handles = value
            elif M.Compare(
                key,
                Gmod.AUTONOMY_REPORT_GENERATED_COMPOSITIONS_KEY,
            )() is M.truth_value:
                compositions = value
            remaining = M.Tail(remaining)()

        self.result = M.truth_value
        remaining_counts = M.Pair(
            firings,
            M.Pair(activated, M.Pair(handles, M.Pair(compositions, M.EmptyList))),
        )
        while M.IdentityCompare(
            remaining_counts,
            M.EmptyList,
        )() is M.false_value:
            count = M.Head(remaining_counts)()
            if M.IdentityCompare(count, M.EmptyList)() is M.false_value:
                if SessionCountIsZero(count)() is M.false_value:
                    self.result = M.false_value
                    remaining_counts = M.EmptyList
            if M.IdentityCompare(
                remaining_counts,
                M.EmptyList,
            )() is M.false_value:
                remaining_counts = M.Tail(remaining_counts)()
        super().__init__(inputs=M.Pair(report, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SessionCountIsZero(M.Edge):
    """A report count, however represented, denotes zero."""

    def __init__(self, count):
        self.result = M.false_value
        if M.IdentityCompare(count, M.Zero)() is M.truth_value:
            self.result = M.truth_value
        else:
            rep = M.NatRepOf(count, M.AllConstructors)()
            if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
                if Gmod.GMPEqualText(
                    M.GMPRepText(rep)(),
                    "0",
                )() is M.truth_value:
                    self.result = M.truth_value
        super().__init__(inputs=M.Pair(count, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SessionSafetyRefused(M.Edge):
    """The Step-49 floor is currently violated for this version and store."""

    def __init__(self, graph_version, proposal_store):
        violation = Gmod.CheckSafety(graph_version, proposal_store)()
        self.result = M.false_value
        if M.IdentityCompare(violation, M.EmptyList)() is M.false_value:
            self.result = M.truth_value
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(proposal_store, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


def run_session(
    checkpoint_path,
    report_path,
    budget,
    generator_config,
    worker_count,
    max_cycles,
):
    """Load a checkpoint, cycle until a stop condition, write it back.

    `max_cycles` is a GMP count text. Returns
    Pair(version, Pair(store, Pair(ledger, Pair(stop_reason, EmptyList)))).
    """
    loaded = Wmod.load_checkpoint(checkpoint_path)
    graph_version = M.Head(loaded)()
    proposal_store = M.Head(M.Tail(loaded)())()
    ledger = M.Head(M.Tail(M.Tail(loaded)())())()

    cycles_text = "0"
    max_text = M.GMPRepText(max_cycles)()
    stop_reason = SESSION_STOP_CYCLES
    cycling = M.truth_value

    while M.IdentityCompare(cycling, M.truth_value)() is M.truth_value:
        cycling = M.false_value
        if Gmod.GMPEqualText(cycles_text, max_text)() is M.false_value:
            if SessionSafetyRefused(graph_version, proposal_store)() is M.truth_value:
                stop_reason = SESSION_STOP_SAFETY
            else:
                cycles_text = Gmod.GMPSuccText(cycles_text)()
                outcome = Wmod.distributed_cycle(
                    graph_version,
                    proposal_store,
                    ledger,
                    budget,
                    generator_config,
                    worker_count,
                )
                graph_version = M.Head(outcome)()
                proposal_store = M.Head(M.Tail(outcome)())()
                report = M.Head(M.Tail(M.Tail(outcome)())())()

                Wmod.save_checkpoint(
                    checkpoint_path,
                    graph_version,
                    proposal_store,
                    ledger,
                )
                write_session_report(
                    report_path,
                    proposal_store,
                    ledger,
                    graph_version,
                )

                if SessionSafetyRefused(
                    graph_version,
                    proposal_store,
                )() is M.truth_value:
                    stop_reason = SESSION_STOP_SAFETY
                elif SessionCycleIsQuiescent(report)() is M.truth_value:
                    stop_reason = SESSION_STOP_QUIESCENT
                else:
                    cycling = M.truth_value

    return M.Pair(
        graph_version,
        M.Pair(
            proposal_store,
            M.Pair(ledger, M.Pair(stop_reason, M.EmptyList)),
        ),
    )


def write_session_report(report_path, proposal_store, ledger, graph_version):
    """Render the ordinary curator report to disk. Output only."""
    rendered = Gmod.RenderCuratorReport(
        Gmod.CuratorReport(proposal_store, ledger, graph_version)(),
    )()
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    return report_path


def apply_verb(checkpoint_path, verb, proposal_index, authority_name):
    """Attach one approval or countersignature to one pending proposal.

    The verb attaches a term and re-serializes; it activates nothing and
    evaluates no gate. `proposal_index` is a GMP count text selecting a
    store entry in store order.
    """
    loaded = Wmod.load_checkpoint(checkpoint_path)
    graph_version = M.Head(loaded)()
    proposal_store = M.Head(M.Tail(loaded)())()
    ledger = M.Head(M.Tail(M.Tail(loaded)())())()

    target = M.EmptyList
    cursor_text = "0"
    remaining = Gmod.ProposalStoreEntries(proposal_store)()
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        if Gmod.GMPEqualText(cursor_text, proposal_index)() is M.truth_value:
            target = Gmod.ProposalEntryProposal(M.Head(remaining)())()
            remaining = M.EmptyList
        else:
            cursor_text = Gmod.GMPSuccText(cursor_text)()
            remaining = M.Tail(remaining)()

    if M.IdentityCompare(target, M.EmptyList)() is M.false_value:
        authority = M.Char(authority_name)
        annotation = M.EmptyList
        if M.Compare(verb, SESSION_VERB_APPROVE)() is M.truth_value:
            annotation = Gmod.Approved(target, authority)()
        elif M.Compare(verb, SESSION_VERB_COUNTERSIGN)() is M.truth_value:
            annotation = Gmod.Countersigned(target, authority)()
        if M.IdentityCompare(annotation, M.EmptyList)() is M.false_value:
            proposal_store = Gmod.ProposalStoreAttach(
                proposal_store,
                target,
                annotation,
            )()
            Wmod.save_checkpoint(
                checkpoint_path,
                graph_version,
                proposal_store,
                ledger,
            )
    return proposal_store


def main(argv):
    """CLI verb parser: `approve` and `countersign` only."""
    arguments = M.EmptyList
    remaining = argv
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        arguments = M.Pair(M.Head(remaining)(), arguments)
        remaining = M.Tail(remaining)()
    arguments = Gmod.Reverse(arguments)()

    verb_text = M.Head(M.Tail(arguments)())()
    verb = M.Char(verb_text)
    checkpoint_path = M.Head(M.Tail(M.Tail(arguments)())())()
    proposal_index = M.Head(M.Tail(M.Tail(M.Tail(arguments)())())())()
    authority_name = M.Head(
        M.Tail(M.Tail(M.Tail(M.Tail(arguments)())())())(),
    )()
    return apply_verb(checkpoint_path, verb, proposal_index, authority_name)
