"""The cycling daemon: one writer, running beside a conversation.

A separate process, not a thread. The substrate has global mutable state
-- AllConstructors is reassigned, ConstructedBy mutates nodes in place,
and Zero.value is written during ordinary nat construction -- so two
threads building terms would race and corrupt each other silently. A
process boundary is the isolation the substrate already relies on for
its workers.

The file discipline is one writer per file, which keeps Part 4's
"activation happens in one place" invariant intact across the boundary:

  talk_state.wire   written by the daemon alone, read by both
  talk_inbox.wire   written by the conversation alone, read and cleared
                    by the daemon

The conversation submits proposals into the inbox and never activates.
The daemon folds the inbox into its state, activates what the gates
allow, and writes the result back. Nothing is shared but the files, and
each is written by exactly one process.

Output is a running commentary on stdout, line buffered, so a terminal
draining the pipe sees what fired, what was proposed, and what the
safety floor refused, as it happens.
"""

import os
import time

from . import machine as M
from . import graph as Gmod
from . import wire as Wmod


# Host I/O parameters, not machine values: a poll interval in seconds and
# the two filenames. These live at the process boundary in the same way a
# path or an exit code does.
DAEMON_POLL_SECONDS = 0.5
DAEMON_STATE_NAME = "talk_state.wire"
DAEMON_INBOX_NAME = "talk_inbox.wire"
# Presence of this file means a daemon is cycling. The inbox cannot serve
# as that signal: the daemon consumes it, so its absence is ambiguous.
DAEMON_LIVE_NAME = "talk_daemon.live"

DAEMON_STOP_CYCLES = M.Char("daemon-stop-max-cycles")
DAEMON_STOP_SAFETY = M.Char("daemon-stop-safety-refusal")


class DaemonCycleSummary(M.Edge):
    """One line describing what a cycle did, read from its own report.

    The daemon reports what the cycle recorded rather than counting
    anything itself, so the commentary cannot drift from the machine's
    own account of the turn.
    """

    def __init__(self, report):
        firings = M.EmptyList
        activated = M.EmptyList
        handles = M.EmptyList
        compositions = M.EmptyList
        stopped = M.EmptyList
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
            elif M.Compare(
                key,
                Gmod.AUTONOMY_REPORT_STOPPED_REASON_KEY,
            )() is M.truth_value:
                stopped = value
            remaining = M.Tail(remaining)()
        self.result = (
            "fired "
            + DaemonCountText(firings)()
            + ", activated "
            + DaemonCountText(activated)()
            + ", proposed "
            + DaemonCountText(handles)()
            + " handle(s) and "
            + DaemonCountText(compositions)()
            + " composition(s)"
            + DaemonStoppedText(stopped)()
        )
        super().__init__(inputs=M.Pair(report, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DaemonCountText(M.Edge):
    """Render a report count, however represented, as its decimal text."""

    def __init__(self, count):
        self.result = "0"
        if M.IdentityCompare(count, M.EmptyList)() is M.false_value:
            rep = M.NatRepOf(count, M.AllConstructors)()
            if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
                self.result = M.GMPRepText(rep)()
        super().__init__(inputs=M.Pair(count, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DaemonStoppedText(M.Edge):
    """Name the cycle's stop reason, when it recorded one."""

    def __init__(self, stopped):
        self.result = ""
        if M.IdentityCompare(stopped, M.EmptyList)() is M.false_value:
            if M.IsPair(stopped)() is M.false_value:
                self.result = "; stopped: " + stopped()
        super().__init__(inputs=M.Pair(stopped, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DaemonSafetyText(M.Edge):
    """Name a violated safety bound, or empty when the floor is clear."""

    def __init__(self, graph_version, proposal_store):
        self.result = ""
        violation = Gmod.CheckSafety(graph_version, proposal_store)()
        if M.IdentityCompare(violation, M.EmptyList)() is M.false_value:
            self.result = (
                Gmod.SafetyInvariantName(violation)()()
                + " (measure "
                + Gmod.SafetyInvariantMeasure(violation)()()
                + ", bound "
                + M.GMPRepText(Gmod.SafetyInvariantBound(violation)())()
                + ")"
            )
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(proposal_store, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DaemonMergeInbox(M.Edge):
    """Fold every submitted proposal into the daemon's own store.

    Submissions arrive as a proposal store written by the conversation.
    Their annotations travel with them, so an approval typed at the
    prompt is carried across, but activation is not: that decision is
    taken here, by the ordinary gates, on this side of the boundary.
    """

    def __init__(self, proposal_store, submitted):
        current = proposal_store
        merged_text = "0"
        remaining = M.EmptyList
        if M.IdentityCompare(submitted, M.EmptyList)() is M.false_value:
            remaining = Gmod.ProposalStoreEntries(submitted)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            proposal = Gmod.ProposalEntryProposal(entry)()
            known = M.false_value
            probe = Gmod.ProposalStoreEntries(current)()
            while M.IdentityCompare(probe, M.EmptyList)() is M.false_value:
                if M.TermEqual(
                    Gmod.ProposalEntryProposal(M.Head(probe)())(),
                    proposal,
                )() is M.truth_value:
                    known = M.truth_value
                    probe = M.EmptyList
                else:
                    probe = M.Tail(probe)()
            if M.IdentityCompare(known, M.false_value)() is M.truth_value:
                current = Gmod.ProposalStoreSubmit(current, proposal)()
                merged_text = Gmod.GMPSuccText(merged_text)()
            annotations = Gmod.ProposalEntryAnnotations(entry)()
            while M.IdentityCompare(annotations, M.EmptyList)() is M.false_value:
                current = Gmod.ProposalStoreAttach(
                    current,
                    proposal,
                    M.Head(annotations)(),
                )()
                annotations = M.Tail(annotations)()
            remaining = M.Tail(remaining)()
        self.result = M.Pair(current, M.Pair(M.GMPRep(merged_text), M.EmptyList))
        super().__init__(
            inputs=M.Pair(proposal_store, M.Pair(submitted, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


def daemon_budget(graph_version):
    """A conservative per-cycle budget: fire a little, activate a little."""
    one = M.Head(M.Succ(M.Zero, M.AllConstructors)())()
    two = M.Head(M.Succ(one, M.AllConstructors)())()
    node_ceiling = M.Head(
        M.Count(Gmod.GraphNodes(graph_version)(), M.AllConstructors)(),
    )()
    return M.Pair(
        M.Pair(Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY, M.Pair(two, M.EmptyList)),
        M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                M.Pair(node_ceiling, M.EmptyList),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                    M.Pair(one, M.EmptyList),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_ACTIVATE_APPROVED_KEY,
                        M.Pair(M.truth_value, M.EmptyList),
                    ),
                    M.EmptyList,
                ),
            ),
        ),
    )


def run_daemon(snapshot_dir, max_cycles, poll_seconds=DAEMON_POLL_SECONDS,
               worker_count=0):
    """Cycle the shared state until the cycle cap or a safety refusal.

    `max_cycles` is a GMP count text. Every cycle: fold the inbox, run one
    AutonomyCycle, write the state back, and report. The daemon is the
    only writer of talk_state.wire, so the conversation never has to
    coordinate with it beyond dropping submissions in the inbox.
    """
    state_path = os.path.join(snapshot_dir, DAEMON_STATE_NAME)
    inbox_path = os.path.join(snapshot_dir, DAEMON_INBOX_NAME)

    graph_version = Gmod.GraphVersion(M.EmptyList, M.EmptyList, M.EmptyList)()
    proposal_store = Gmod.ProposalStore(M.EmptyList)()
    ledger = Gmod.FiringLedger(M.AllConstructors)
    if os.path.exists(state_path):
        restored = Wmod.load_checkpoint(state_path)
        if M.IdentityCompare(restored, M.EmptyList)() is M.false_value:
            graph_version = M.Head(restored)()
            proposal_store = M.Head(M.Tail(restored)())()
            ledger = M.Head(M.Tail(M.Tail(restored)())())()
    live_path = os.path.join(snapshot_dir, DAEMON_LIVE_NAME)
    with open(live_path, "w", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    print("daemon: cycling shared state at " + state_path, flush=True)

    cycles_text = "0"
    max_text = M.GMPRepText(max_cycles)()
    stop_reason = DAEMON_STOP_CYCLES
    cycling = M.truth_value
    while M.IdentityCompare(cycling, M.truth_value)() is M.truth_value:
        cycling = M.false_value
        if Gmod.GMPEqualText(cycles_text, max_text)() is M.false_value:
            cycles_text = Gmod.GMPSuccText(cycles_text)()

            if os.path.exists(inbox_path):
                submitted = Wmod.load_checkpoint(inbox_path)
                if M.IdentityCompare(submitted, M.EmptyList)() is M.false_value:
                    merged = DaemonMergeInbox(
                        proposal_store,
                        M.Head(M.Tail(submitted)())(),
                    )()
                    proposal_store = M.Head(merged)()
                    merged_count = M.GMPRepText(M.Head(M.Tail(merged)())())()
                    if Gmod.GMPEqualText(merged_count, "0")() is M.false_value:
                        print(
                            "daemon: took "
                            + merged_count
                            + " submission(s) from the conversation",
                            flush=True,
                        )
                os.remove(inbox_path)

            refusal = DaemonSafetyText(graph_version, proposal_store)()
            if refusal:
                print("daemon: refused by the safety floor: " + refusal, flush=True)
                stop_reason = DAEMON_STOP_SAFETY
            else:
                # With workers, the cycle fans generation and firing out
                # through Step 45's distributed_cycle: worker budgets have
                # max_activations forced to Zero, claims are replayed against
                # the coordinator version rather than transplanted, and the
                # single in-process AutonomyCycle is still the only place
                # activation happens. Without workers it is that cycle alone.
                if worker_count:
                    outcome = Wmod.distributed_cycle(
                        graph_version,
                        proposal_store,
                        ledger,
                        daemon_budget(graph_version),
                        M.EmptyList,
                        worker_count,
                    )
                else:
                    outcome = Gmod.AutonomyCycle(
                        graph_version,
                        proposal_store,
                        ledger,
                        daemon_budget(graph_version),
                    )()
                graph_version = M.Head(outcome)()
                proposal_store = M.Head(M.Tail(outcome)())()
                report = M.Head(M.Tail(M.Tail(outcome)())())()
                Wmod.save_checkpoint(
                    state_path,
                    graph_version,
                    proposal_store,
                    ledger,
                )
                print(
                    "daemon cycle " + cycles_text + ": " + DaemonCycleSummary(report)(),
                    flush=True,
                )
                time.sleep(poll_seconds)
                cycling = M.truth_value

    if os.path.exists(live_path):
        os.remove(live_path)
    print("daemon: " + stop_reason(), flush=True)
    return M.Pair(
        graph_version,
        M.Pair(proposal_store, M.Pair(ledger, M.Pair(stop_reason, M.EmptyList))),
    )


def submit_to_inbox(snapshot_dir, proposal_store):
    """Called by the conversation: drop submissions where the daemon reads.

    The conversation writes only this file, and only ever adds to it.
    Activation stays on the daemon's side of the boundary.
    """
    inbox_path = os.path.join(snapshot_dir, DAEMON_INBOX_NAME)
    empty_version = Gmod.GraphVersion(M.EmptyList, M.EmptyList, M.EmptyList)()
    Wmod.save_checkpoint(
        inbox_path,
        empty_version,
        proposal_store,
        Gmod.FiringLedger(M.AllConstructors),
    )
    return inbox_path
