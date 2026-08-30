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

import multiprocessing
import os
import time

from . import machine as M
from . import graph as Gmod
from . import labels as Lmod
from . import proof as Proof
from . import wire as Wmod
from . import proof_lookup_coordinator as ProofLookup


# Host I/O parameters, not machine values: a poll interval in seconds and
# the two filenames. These live at the process boundary in the same way a
# path or an exit code does.
DAEMON_POLL_SECONDS = 0.5
# The daemon and a foreground search comparison can fan out at the same
# time, so each takes half of the host process budget rather than all of it.
DAEMON_BUDGET_CLAIMANTS = 2
DAEMON_STATE_NAME = "talk_state.wire"
DAEMON_INBOX_NAME = "talk_inbox.wire"
# Presence of this file means a daemon is cycling. The inbox cannot serve
# as that signal: the daemon consumes it, so its absence is ambiguous.
DAEMON_LIVE_NAME = "talk_daemon.live"

DAEMON_STOP_CYCLES = M.Char("daemon-stop-max-cycles")
DAEMON_STOP_SAFETY = M.Char("daemon-stop-safety-refusal")
DAEMON_STOP_QUIESCENT = M.Char("daemon-stop-quiescent")


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
        correspondences = M.EmptyList
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
                Gmod.AUTONOMY_REPORT_GENERATED_CORRESPONDENCES_KEY,
            )() is M.truth_value:
                correspondences = value
            elif M.Compare(
                key,
                Gmod.AUTONOMY_REPORT_STOPPED_REASON_KEY,
            )() is M.truth_value:
                stopped = value
            remaining = M.Tail(remaining)()
        unified_text = DaemonActivatedKindText(activated)()
        self.result = (
            "fired "
            + DaemonCountText(firings)()
            + ", activated "
            + DaemonCountText(activated)()
            + unified_text
            + ", proposed "
            + DaemonCountText(handles)()
            + " handle(s) and "
            + DaemonCountText(compositions)()
            + " composition(s)"
            + ", found "
            + DaemonCountText(correspondences)()
            + " correspondence(s)"
            + DaemonStoppedText(stopped)()
        )
        super().__init__(inputs=M.Pair(report, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DaemonActivatedKindText(M.Edge):
    """Name what a cycle's activations did, from the proposals themselves.

    A count says how many; the payload of each activated proposal says
    what kind of change the graph took -- rules unified, subgraphs
    reformed -- so the commentary can say it in words.
    """

    def __init__(self, activated):
        unified = 0
        reformed = 0
        remaining = activated
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            proposal = M.Head(remaining)()
            payload = Gmod.ProposalLaw(proposal)()
            if Gmod.IsRuleUnification(payload)() is M.truth_value:
                unified = unified + 1
            elif Gmod.IsSubgraphReformulation(payload)() is M.truth_value:
                reformed = reformed + 1
            remaining = M.Tail(remaining)()
        self.result = ""
        if unified:
            self.result = self.result + " (unified " + str(unified) + " rule pair(s)"
            if reformed:
                self.result = (
                    self.result + ", reformed " + str(reformed) + " subgraph(s)"
                )
            self.result = self.result + ")"
        elif reformed:
            self.result = " (reformed " + str(reformed) + " subgraph(s))"
        super().__init__(inputs=M.Pair(activated, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DaemonCycleIsQuiescent(M.Edge):
    """A cycle that changed nothing: no firing, activation, or proposal.

    Read from the cycle's own report rather than counted here, so the stop
    condition cannot drift from the machine's account of the turn.
    """

    def __init__(self, report):
        self.result = M.truth_value
        remaining = report
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            key = M.Head(entry)()
            counted = M.false_value
            if M.Compare(key, Gmod.AUTONOMY_REPORT_FIRINGS_KEY)() is M.truth_value:
                counted = M.truth_value
            elif M.Compare(
                key,
                Gmod.AUTONOMY_REPORT_ACTIVATED_KEY,
            )() is M.truth_value:
                counted = M.truth_value
            elif M.Compare(
                key,
                Gmod.AUTONOMY_REPORT_GENERATED_HANDLES_KEY,
            )() is M.truth_value:
                counted = M.truth_value
            elif M.Compare(
                key,
                Gmod.AUTONOMY_REPORT_GENERATED_COMPOSITIONS_KEY,
            )() is M.truth_value:
                counted = M.truth_value
            if M.IdentityCompare(counted, M.truth_value)() is M.truth_value:
                if Gmod.GMPEqualText(
                    DaemonCountText(M.Head(M.Tail(entry)())())(),
                    "0",
                )() is M.false_value:
                    self.result = M.false_value
                    remaining = M.EmptyList
            if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                remaining = M.Tail(remaining)()
        super().__init__(inputs=M.Pair(report, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DaemonCountText(M.Edge):
    """Render a report count, however represented, as its decimal text."""

    def __init__(self, count):
        self.result = "0"
        candidate = count
        if M.IsPair(candidate)() is M.truth_value:
            candidate = M.Head(candidate)()
            if M.IsPair(candidate)() is M.truth_value:
                candidate = M.Head(candidate)()
        rep = M.NatRepOf(candidate, M.AllConstructors)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            self.result = M.GMPRepText(rep)()
        elif M.IdentityCompare(count, M.EmptyList)() is M.false_value:
            self.result = M.GMPRepText(M.CountRep(count)())()
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


class DaemonCycleFindingsText(M.Edge):
    """The cycle's own count of correspondences found, as text."""

    def __init__(self, report):
        self.result = "0"
        remaining = report
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            key = M.Head(entry)()
            if M.Compare(
                key,
                Gmod.AUTONOMY_REPORT_GENERATED_CORRESPONDENCES_KEY,
            )() is M.truth_value:
                self.result = DaemonCountText(
                    M.Head(M.Head(M.Tail(entry)())())(),
                )()
                remaining = M.EmptyList
            else:
                remaining = M.Tail(remaining)()
        super().__init__(inputs=M.Pair(report, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DaemonCorrespondenceLines(M.Edge):
    """Say, in words, what the cycle's findings are waiting on.

    The proposals carry their own terms; this renders the pending
    machine-found ones as the statements they are -- two rules that are
    one rule, a subgraph the graph holds several times -- so the
    commentary names the correspondence rather than counting it.
    """

    def __init__(self, proposal_store):
        lines = []
        remaining = Gmod.ProposalStoreEntries(proposal_store)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            remaining = M.Tail(remaining)()
            proposal = Gmod.ProposalEntryProposal(entry)()
            origin = Gmod.ProposalOrigin(proposal)()
            machine_found = M.false_value
            if M.IsPair(origin)() is M.truth_value:
                if M.Compare(
                    M.Head(origin)(),
                    M.Char("machine-correspondence"),
                )() is M.truth_value:
                    machine_found = M.truth_value
            if M.IdentityCompare(machine_found, M.false_value)() is M.truth_value:
                continue
            decided = M.false_value
            annotation_scan = Gmod.ProposalEntryAnnotations(entry)()
            while M.IdentityCompare(
                annotation_scan,
                M.EmptyList,
            )() is M.false_value:
                annotation = M.Head(annotation_scan)()
                if M.IsPair(annotation)() is M.truth_value:
                    if M.TermEqual(
                        M.Head(annotation)(),
                        Lmod.ApprovedLabel,
                    )() is M.truth_value:
                        decided = M.truth_value
                        annotation_scan = M.EmptyList
                    elif M.TermEqual(
                        M.Head(annotation)(),
                        Lmod.RejectedLabel,
                    )() is M.truth_value:
                        decided = M.truth_value
                        annotation_scan = M.EmptyList
                if M.IdentityCompare(
                    annotation_scan,
                    M.EmptyList,
                )() is M.false_value:
                    annotation_scan = M.Tail(annotation_scan)()
            if M.IdentityCompare(decided, M.truth_value)() is M.truth_value:
                continue
            payload = Gmod.ProposalLaw(proposal)()
            if Gmod.IsRuleUnification(payload)() is M.truth_value:
                keep = Proof.PrettyRule(
                    Proof.MultiRule(
                        Gmod.RuleUnificationKeepPremises(payload)(),
                        Gmod.RuleUnificationKeepReplacement(payload)(),
                    )(),
                    M.AllConstructors,
                )()
                retire = Proof.PrettyRule(
                    Proof.MultiRule(
                        Gmod.RuleUnificationRetirePremises(payload)(),
                        Gmod.RuleUnificationRetireReplacement(payload)(),
                    )(),
                    M.AllConstructors,
                )()
                kind_text = "up to instantiation"
                if M.Compare(
                    Gmod.RuleUnificationKind(payload)(),
                    M.Char("renaming"),
                )() is M.truth_value:
                    kind_text = "up to renaming"
                lines.append(
                    "the rule '"
                    + keep
                    + "' and the rule '"
                    + retire
                    + "' are one rule "
                    + kind_text,
                )
            elif Gmod.IsSubgraphReformulation(payload)() is M.truth_value:
                lines.append(
                    "the subgraph "
                    + M.PrettyTerm(
                        Gmod.SubgraphReformulationPattern(payload)(),
                        M.AllConstructors,
                    )()
                    + " is in the graph "
                    + M.GMPRepText(
                        Gmod.SubgraphReformulationCount(payload)(),
                    )()
                    + " times",
                )
        self.result = "; ".join(lines)
        super().__init__(inputs=M.Pair(proposal_store, M.EmptyList), results=self.result)

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


class DaemonAnnotationForTarget(M.Edge):
    """Repoint an annotation at the proposal of the entry it lands on.

    An annotation speaks about a proposal: Approved(proposal, ...),
    Rejected(proposal, ...), Activation(proposal), JustifiedBy(proposal,
    ...). A submission whose entry is known under the store's own
    proposal -- the same teaching, or the same term restored from
    another blob -- carries annotations about the submitted term, and
    the gates downstream read them by identity against the entry's own
    proposal. The annotation is rewritten to speak about the proposal
    it now annotates; every other annotation passes through untouched.
    """

    def __init__(self, annotation, submitted, target):
        result = annotation
        if M.IsPair(annotation)() is M.truth_value:
            speaks_of = M.Head(M.Tail(annotation)())()
            if M.Compare(speaks_of, submitted)() is M.truth_value:
                label = M.Head(annotation)()
                if M.TermEqual(label, Lmod.ApprovedLabel)() is M.truth_value:
                    result = Gmod.Approved(
                        target,
                        M.Head(M.Tail(M.Tail(annotation)())())(),
                    )()
                elif M.TermEqual(label, Lmod.RejectedLabel)() is M.truth_value:
                    result = Gmod.Rejected(
                        target,
                        M.Head(M.Tail(M.Tail(annotation)())())(),
                        M.Head(
                            M.Tail(M.Tail(M.Tail(annotation)())())(),
                        )(),
                    )()
                elif M.TermEqual(label, Lmod.ActivationLabel)() is M.truth_value:
                    result = Gmod.Activation(target)()
                elif M.TermEqual(
                    label,
                    Lmod.JustifiedByLabel,
                )() is M.truth_value:
                    result = Gmod.JustifiedBy(
                        target,
                        M.Head(M.Tail(M.Tail(annotation)())())(),
                    )()
                elif M.TermEqual(
                    label,
                    Lmod.CountersignedLabel,
                )() is M.truth_value:
                    result = Gmod.Countersigned(
                        target,
                        M.Head(M.Tail(M.Tail(annotation)())())(),
                    )()
        self.result = result
        super().__init__(
            inputs=M.Pair(
                annotation,
                M.Pair(submitted, M.Pair(target, M.EmptyList)),
            ),
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
            # The entry the annotations land on: the submitted proposal
            # when it is itself known, or the store's own proposal when
            # the teaching is known under a guarded law.
            attach_target = proposal
            probe = Gmod.ProposalStoreEntries(current)()
            while M.IdentityCompare(probe, M.EmptyList)() is M.false_value:
                known_proposal = Gmod.ProposalEntryProposal(
                    M.Head(probe)(),
                )()
                if M.Compare(
                    known_proposal,
                    proposal,
                )() is M.truth_value:
                    known = M.truth_value
                    attach_target = known_proposal
                    probe = M.EmptyList
                else:
                    # The daemon activates a submitted rule under a
                    # guarded law -- the node-budget obligation is added
                    # to the proposal's own law -- so the same teaching
                    # crosses this boundary as two structurally
                    # different proposals. A taught rule is identified
                    # by its teaching: the dialogue-rule origin carrying
                    # its premises and replacement. Same origin, same
                    # entry, whatever guard the law wears.
                    same_teaching = M.false_value
                    known_origin = Gmod.ProposalOrigin(known_proposal)()
                    submitted_origin = Gmod.ProposalOrigin(proposal)()
                    if M.IsPair(known_origin)() is M.truth_value:
                        if M.IsPair(submitted_origin)() is M.truth_value:
                            if M.Compare(
                                M.Head(known_origin)(),
                                M.Char("dialogue-rule"),
                            )() is M.truth_value:
                                if M.Compare(
                                    M.Head(submitted_origin)(),
                                    M.Char("dialogue-rule"),
                                )() is M.truth_value:
                                    if M.Compare(
                                        known_origin,
                                        submitted_origin,
                                    )() is M.truth_value:
                                        same_teaching = M.truth_value
                    if M.IdentityCompare(
                        same_teaching,
                        M.truth_value,
                    )() is M.truth_value:
                        known = M.truth_value
                        attach_target = known_proposal
                        probe = M.EmptyList
                    else:
                        probe = M.Tail(probe)()
            if M.IdentityCompare(known, M.false_value)() is M.truth_value:
                current = Gmod.ProposalStoreSubmit(current, proposal)()
                merged_text = Gmod.GMPSuccText(merged_text)()
            annotations = Gmod.ProposalEntryAnnotations(entry)()
            while M.IdentityCompare(annotations, M.EmptyList)() is M.false_value:
                annotation = DaemonAnnotationForTarget(
                    M.Head(annotations)(),
                    proposal,
                    attach_target,
                )()
                current = Gmod.ProposalStoreAttach(
                    current,
                    attach_target,
                    annotation,
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


# How much the graph may grow in one cycle. A ceiling at the current node
# count is not a budget, it is a prohibition: the first firing that adds a
# node trips it and the cycle ends having done nothing, which is exactly
# what every reported cycle did.
DAEMON_NODE_HEADROOM = M.GMPRep("64")


def daemon_budget(graph_version):
    """A per-cycle budget with room to actually do something.

    max_nodes is the current node count plus headroom, so a firing that
    grows the graph is allowed rather than refused before it starts.
    """
    one = M.Head(M.Succ(M.Zero, M.AllConstructors)())()
    two = M.Head(M.Succ(one, M.AllConstructors)())()
    current_text = M.GMPRepText(
        M.CountRep(Gmod.GraphNodes(graph_version)())(),
    )()
    node_ceiling = Gmod.MineNatFromGMPRep(
        M.GMPRep(
            Gmod.GMPAddText(
                current_text,
                M.GMPRepText(DAEMON_NODE_HEADROOM)(),
            )(),
        ),
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


def daemon_correspondence_config():
    """The live daemon's mining: correspondences only.

    Firing laws over ground facts is one thing the cycle does; finding
    structure is the other, and it is the one the background process is
    for. Handle and composition mining stay off in live sessions -- they
    fire and fold without asking -- while rule correspondence and
    recurring-subgraph findings are proposals for the human.
    """
    return M.Pair(
        M.Pair(
            Gmod.AUTONOMY_GENERATE_CORRESPONDENCES_KEY,
            M.Pair(M.truth_value, M.EmptyList),
        ),
        M.EmptyList,
    )


def daemon_generator_config(graph_version):
    """Switch mining on. Without this the daemon cannot propose anything.

    AutonomyCycle only mines handles or compositions when the config says
    so, and the daemon passed EmptyList -- so every cycle reported
    "proposed 0 handle(s) and 0 composition(s)" not because there was
    nothing to find but because looking was disabled. The distributed
    cycle then had nothing for its workers to divide.

    Handle mining censuses candidate patterns across a version history;
    the current version is that history until a Next chain accumulates.
    Correspondence mining -- rules against rules, subgraphs against the
    graph -- runs in every mode, live included.
    """
    return M.Pair(
        M.Pair(
            Gmod.AUTONOMY_GENERATE_HANDLES_KEY,
            M.Pair(M.truth_value, M.EmptyList),
        ),
        M.Pair(
            M.Pair(
                Gmod.AUTONOMY_GENERATE_COMPOSITIONS_KEY,
                M.Pair(M.truth_value, M.EmptyList),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_GENERATE_CORRESPONDENCES_KEY,
                    M.Pair(M.truth_value, M.EmptyList),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_GENERATOR_VERSIONS_KEY,
                        M.Pair(
                            M.Pair(graph_version, M.EmptyList),
                            M.EmptyList,
                        ),
                    ),
                    M.EmptyList,
                ),
            ),
        ),
    )


def daemon_worker_count(requested):
    """Workers per cycle: what was asked for, or the daemon's share.

    A negative or absent request means autoscale.  The daemon no longer
    claims one process per core: it draws a share of the single host budget
    in `wire.host_process_budget`, because a foreground proof fans out at
    the same time and the two used to oversubscribe the machine between
    them.  An explicit request is honoured as given.
    """
    if requested:
        return requested
    return Wmod.share_process_budget(DAEMON_BUDGET_CLAIMANTS)


def run_proof_worker_service(
    snapshot_dir, proof_worker_count, stop_signal, worker_service_lock,
):
    """Serve foreground graph requests while daemon autonomy restores/cycles.

    Proof requests carry their own machine-native graph, goal, and
    assumptions, so this service does not depend on the autonomy checkpoint.
    It belongs to the daemon process tree and owns the daemon's configured
    worker cardinality.
    """
    os.environ["HYGE_FOREGROUND_WORKERS"] = str(proof_worker_count)
    proof_request_path = os.path.join(
        snapshot_dir, ProofLookup.PROOF_LOOKUP_REQUEST_NAME,
    )
    proof_taken_path = os.path.join(
        snapshot_dir, ProofLookup.PROOF_LOOKUP_TAKEN_NAME,
    )
    proof_response_path = os.path.join(
        snapshot_dir, ProofLookup.PROOF_LOOKUP_RESPONSE_NAME,
    )
    print(
        "daemon proof coordinator " + str(os.getpid())
        + ": worker service ready with " + str(proof_worker_count)
        + " worker(s)",
        flush=True,
    )
    while not stop_signal.is_set():
        if os.path.exists(proof_request_path):
            os.replace(proof_request_path, proof_taken_path)
            with open(proof_taken_path, "rb") as proof_stream:
                proof_request = Wmod.deserialize_term(proof_stream.read())
            proof_graph_version = M.Head(proof_request)()
            proof_goal = M.Head(M.Tail(proof_request)())()
            proof_assumptions = M.Head(M.Tail(M.Tail(proof_request)())())()
            print(
                "daemon: accepted foreground proof lookup; distributing the graph equally across "
                + str(proof_worker_count) + " existing worker(s)",
                flush=True,
            )
            worker_service_lock.acquire()
            try:
                proof_mode = ProofLookup.ParallelProofLookupMode(
                    proof_graph_version, proof_goal, proof_assumptions,
                )()
            finally:
                worker_service_lock.release()
            proof_response_temporary = proof_response_path + ".tmp"
            with open(
                proof_response_temporary, "w", encoding="utf-8",
            ) as proof_response_stream:
                proof_response_stream.write(proof_mode)
            os.replace(proof_response_temporary, proof_response_path)
            if os.path.exists(proof_taken_path):
                os.remove(proof_taken_path)
            print(
                "daemon: foreground proof lookup complete; selected mode="
                + proof_mode,
                flush=True,
            )
        time.sleep(0.1)


def run_daemon(snapshot_dir, max_cycles=M.EmptyList,
               poll_seconds=DAEMON_POLL_SECONDS, worker_count=0):
    """Cycle the shared state until the cycle cap or a safety refusal.

    `max_cycles` is a GMP count text. Every cycle: fold the inbox, run one
    AutonomyCycle, write the state back, and report. The daemon is the
    only writer of talk_state.wire, so the conversation never has to
    coordinate with it beyond dropping submissions in the inbox.
    """
    state_path = os.path.join(snapshot_dir, DAEMON_STATE_NAME)
    inbox_path = os.path.join(snapshot_dir, DAEMON_INBOX_NAME)
    # The fold takes the inbox by renaming it: atomic, so a submission
    # arriving mid-cycle lands in a fresh talk_inbox.wire the next cycle
    # drains, instead of being deleted unread by the end-of-cycle
    # cleanup. A daemon killed between the take and the durable state
    # write leaves the taken file behind; boot folds it back in, so a
    # kill loses nothing.
    inbox_taken_path = os.path.join(snapshot_dir, DAEMON_INBOX_NAME + ".taken")
    proof_request_path = os.path.join(
        snapshot_dir, ProofLookup.PROOF_LOOKUP_REQUEST_NAME,
    )
    proof_taken_path = os.path.join(
        snapshot_dir, ProofLookup.PROOF_LOOKUP_TAKEN_NAME,
    )
    proof_response_path = os.path.join(
        snapshot_dir, ProofLookup.PROOF_LOOKUP_RESPONSE_NAME,
    )
    if os.path.exists(proof_taken_path):
        os.replace(proof_taken_path, proof_request_path)
    live_daemon = M.false_value
    if M.Compare(
        M.Char(os.environ.get("HYGE_LIVE_DAEMON", "")),
        M.Char("1"),
    )() is M.truth_value:
        live_daemon = M.truth_value

    worker_count = daemon_worker_count(worker_count)
    proof_worker_count = worker_count
    if proof_worker_count < 1:
        proof_worker_count = 1
    proof_service_stop_signal = multiprocessing.Event()
    worker_service_lock = multiprocessing.Lock()
    proof_service = multiprocessing.Process(
        target=run_proof_worker_service,
        args=(
            snapshot_dir, proof_worker_count, proof_service_stop_signal,
            worker_service_lock,
        ),
    )
    proof_service.start()
    live_path = os.path.join(snapshot_dir, DAEMON_LIVE_NAME)
    with open(live_path, "w", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    print(
        "daemon: process " + str(os.getpid())
        + " started; proof service is opening while autonomy restores shared state",
        flush=True,
    )
    graph_version = Gmod.GraphVersion(M.EmptyList, M.EmptyList, M.EmptyList)()
    proposal_store = Gmod.ProposalStore(M.EmptyList)()
    ledger = Gmod.FiringLedger(M.AllConstructors)
    if os.path.exists(state_path):
        restored = Wmod.load_checkpoint(state_path)
        if M.IdentityCompare(restored, M.EmptyList)() is M.false_value:
            graph_version = M.Head(restored)()
            proposal_store = M.Head(M.Tail(restored)())()
            ledger = M.Head(M.Tail(M.Tail(restored)())())()
    # An inbox taken but not yet folded into durable state when the
    # previous daemon died: fold it now, before anything else, so the
    # take loses nothing across a kill.
    if os.path.exists(inbox_taken_path):
        taken = Wmod.load_checkpoint(inbox_taken_path)
        if M.IdentityCompare(taken, M.EmptyList)() is M.false_value:
            graph_version = Gmod.MergeGraphVersion(
                graph_version,
                M.Head(taken)(),
            )()
            taken_merge = DaemonMergeInbox(
                proposal_store,
                M.Head(M.Tail(taken)())(),
            )()
            proposal_store = M.Head(taken_merge)()
        os.remove(inbox_taken_path)
    print(
        "daemon: autonomy restored shared state at "
        + state_path
        + " with "
        + str(worker_count)
        + " worker(s)",
        flush=True,
    )

    # An absent cycle cap means the daemon decides for itself: it runs
    # until the work runs out. A cycle that fires nothing, activates
    # nothing and proposes nothing has nothing left to do, and running it
    # again would produce the same nothing -- so quiescence is the stop
    # condition, and the cap is only a ceiling for when one is wanted.
    bounded = M.false_value
    max_text = "0"
    if M.IdentityCompare(
        live_daemon, M.false_value,
    )() is M.truth_value:
        if M.IdentityCompare(max_cycles, M.EmptyList)() is M.false_value:
            bounded = M.truth_value
            max_text = M.GMPRepText(max_cycles)()
    cycles_text = "0"
    stop_reason = DAEMON_STOP_CYCLES
    # Mining reads the version, so it runs when the version moved. A
    # stable graph re-mined every half second would find the same
    # nothing forever; these stamps say whether anything changed since
    # the last pass. Host strings at the process boundary, like the
    # cycle counter beside them.
    mined_nodes_text = ""
    mined_edges_text = ""
    cycling = M.truth_value
    while M.IdentityCompare(cycling, M.truth_value)() is M.truth_value:
        cycling = M.false_value
        capped = M.false_value
        if M.IdentityCompare(bounded, M.truth_value)() is M.truth_value:
            capped = Gmod.GMPEqualText(cycles_text, max_text)()
        if M.IdentityCompare(capped, M.truth_value)() is M.false_value:
            cycles_text = Gmod.GMPSuccText(cycles_text)()

            inbox_taken = M.false_value
            if os.path.exists(inbox_path):
                # Take the whole file by rename before reading it. A
                # submission written while this cycle runs creates a new
                # talk_inbox.wire after the rename, untouched by this
                # cycle's cleanup, and the next cycle drains it.
                os.replace(inbox_path, inbox_taken_path)
                submitted = Wmod.load_checkpoint(inbox_taken_path)
                inbox_taken = M.truth_value
                if M.IdentityCompare(submitted, M.EmptyList)() is M.false_value:
                    graph_version = Gmod.MergeGraphVersion(
                        graph_version,
                        M.Head(submitted)(),
                    )()
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
                version_nodes_text = M.GMPRepText(
                    M.CountRep(Gmod.GraphNodes(graph_version)())(),
                )()
                version_edges_text = M.GMPRepText(
                    M.CountRep(Gmod.GraphEdges(graph_version)())(),
                )()
                version_moved = (
                    version_nodes_text != mined_nodes_text
                    or version_edges_text != mined_edges_text
                )
                generator_config = M.EmptyList
                if version_moved:
                    if M.IdentityCompare(
                        live_daemon, M.truth_value,
                    )() is M.truth_value:
                        generator_config = daemon_correspondence_config()
                    else:
                        generator_config = daemon_generator_config(
                            graph_version,
                        )
                if worker_count:
                    worker_service_lock.acquire()
                    try:
                        outcome = Wmod.distributed_cycle(
                            graph_version,
                            proposal_store,
                            ledger,
                            daemon_budget(graph_version),
                            generator_config,
                            worker_count,
                        )
                    finally:
                        worker_service_lock.release()
                else:
                    outcome = Gmod.AutonomyCycle(
                        graph_version,
                        proposal_store,
                        ledger,
                        daemon_budget(graph_version),
                        generator_config,
                    )()
                graph_version = M.Head(outcome)()
                proposal_store = M.Head(M.Tail(outcome)())()
                report = M.Head(M.Tail(M.Tail(outcome)())())()
                if version_moved:
                    mined_nodes_text = version_nodes_text
                    mined_edges_text = version_edges_text
                Wmod.save_checkpoint(
                    state_path,
                    graph_version,
                    proposal_store,
                    ledger,
                )
                # The taken file is removed only once its content is
                # durable in the state -- at-least-once delivery into an
                # idempotent merge, and never a deletion of a submission
                # this cycle did not read.
                if M.IdentityCompare(inbox_taken, M.truth_value)() is M.truth_value:
                    if os.path.exists(inbox_taken_path):
                        os.remove(inbox_taken_path)
                print(
                    "daemon cycle " + cycles_text + ": " + DaemonCycleSummary(report)(),
                    flush=True,
                )
                findings_text = DaemonCycleFindingsText(report)()
                if findings_text != "0":
                    correspondence_lines = DaemonCorrespondenceLines(
                        proposal_store,
                    )()
                    if correspondence_lines != "":
                        print(
                            "daemon: correspondence: " + correspondence_lines,
                            flush=True,
                        )
                if DaemonCycleIsQuiescent(report)() is M.truth_value:
                    stop_reason = DAEMON_STOP_QUIESCENT
                    if M.IdentityCompare(
                        live_daemon, M.truth_value,
                    )() is M.truth_value:
                        time.sleep(poll_seconds)
                        cycling = M.truth_value
                else:
                    time.sleep(poll_seconds)
                    cycling = M.truth_value

    proof_service_stop_signal.set()
    proof_service.join()
    if os.path.exists(live_path):
        os.remove(live_path)
    print("daemon: " + stop_reason(), flush=True)
    return M.Pair(
        graph_version,
        M.Pair(proposal_store, M.Pair(ledger, M.Pair(stop_reason, M.EmptyList))),
    )


def submit_to_inbox(snapshot_dir, proposal_store, graph_version=M.EmptyList):
    """Deliver append-only taught graph data and proposals to the daemon."""
    inbox_path = os.path.join(snapshot_dir, DAEMON_INBOX_NAME)
    version = graph_version
    if M.IdentityCompare(version, M.EmptyList)() is M.truth_value:
        version = Gmod.GraphVersion(M.EmptyList, M.EmptyList, M.EmptyList)()
    Wmod.save_checkpoint(
        inbox_path,
        version,
        proposal_store,
        Gmod.FiringLedger(M.AllConstructors),
    )
    return inbox_path
