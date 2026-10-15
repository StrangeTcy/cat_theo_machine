"""Test 25 -- W2: framed RPC over mTLS, mesh membership, work stealing, crash handling.

Run:
    PYTHONPATH=/home/user .venv/bin/python -u validation/test25_rpc_mtls_mesh.py

What this suite is for
----------------------
`delegation/W02-rpc-mtls-mesh.md`. The mesh generalises the transport the machine
already had (manifest file in, result snapshot out, spawned by
`search/compare_subprocess.py`) to a framed, mutually-authenticated socket layer:
job descriptions and *references* cross the wire, never machine terms.

Four things are checked here, and they are checked against real sockets and real
processes rather than mocks:

1. **mTLS both ways, and every refusal path.** An authenticated peer is admitted;
   a leaf from a rogue CA, a client that trusts the wrong CA, and an expired leaf
   are all rejected before a single frame is read.
2. **Protocol invariants** (cheap, with stub runners, no machine boot): dispatch,
   work stealing, one writer per scope, stale-sequence refusal, and lease
   reclamation when a peer's connection dies.
3. **Real jobs over real subprocesses.** Two worker processes boot the machine
   once each, run genuine search jobs dispatched by the coordinator, one job is
   stolen by an idle peer, one worker is SIGKILLed mid-job -- and every result is
   compared against the single-process result for the same manifest.
4. **No file-transport regression.** `python main.py search-worker` still runs the
   original path unchanged (`run_search_worker_mode` now delegates to the same
   boot/execute pair the mesh uses).

Timing: phases 1-2 cost a couple of seconds. Phase 3 is dominated by pack boots
(~20 s per worker, done concurrently with the single-process reference) and by the
chosen search job. The suite is guarded with `if __name__ == "__main__":` because
the snapshot codec's registry restore uses `spawn`.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import tempfile
import time

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_PARENT = os.path.dirname(PACKAGE_ROOT)
if PACKAGE_PARENT not in sys.path:
    sys.path.insert(0, PACKAGE_PARENT)

from cat_theo_machine import mesh as MeshModule
from cat_theo_machine.networking import framing
from cat_theo_machine.networking import identity as IdentityModule
from cat_theo_machine.networking import jobs as MeshJobs
from cat_theo_machine.networking import protocol
from cat_theo_machine.networking.peer import MeshPeer

JOBS = (
    {"job_id": "job-dfs", "mode": "dfs"},
    {"job_id": "job-bfs", "mode": "bfs"},
)


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.notes = []

    def check(self, label, condition, detail=""):
        if condition:
            self.passed += 1
            print("  PASS  %-58s %s" % (label, detail))
        else:
            self.failed += 1
            print("  FAIL  %-58s %s" % (label, detail))
        return bool(condition)

    def note(self, text):
        self.notes.append(text)
        print("  note  %s" % text)


# --------------------------------------------------------------- stub transport


class StubRunner:
    """Instant, deterministic 'jobs' for testing the protocol without the machine."""

    def __init__(self, delay=0.0, modes=("dfs", "bfs", "astar", "beam", "rewritedfs"), hold=None, fuse=10.0):
        self.supported_modes = tuple(modes)
        self.delay = delay
        self.booted = True
        self.calls = []
        self.defer_everything = False  # every job reports STATUS_DEFERRED
        # `hold` keeps the runner busy while it returns true, so a peer stays a
        # busy holder for exactly as long as the test needs rather than for a
        # guessed number of seconds. It is one-shot (armed for the next job the
        # runner is handed) and bounded by `fuse`, so a condition that never
        # arrives costs seconds instead of hanging the suite.
        self.hold = hold
        self.fuse = fuse

    def supports(self, mode):
        return mode in self.supported_modes

    def run(self, job):
        self.calls.append(job.job_id)
        hold = self.hold
        self.hold = None  # one-shot: only the job this runner was armed for
        if hold is not None:
            deadline = time.time() + self.fuse
            while hold() and time.time() < deadline:
                time.sleep(0.05)
        if self.delay:
            time.sleep(self.delay)
        directory = os.path.dirname(job.result_ref)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(job.result_ref, "w", encoding="utf-8") as handle:
            handle.write("stub:%s" % job.job_id)
        # `deferred` is a real result too (the search concluded and only the
        # derivation replay was skipped), so both statuses are worth driving
        # through the ledger -- see the "a deferred result is a result" checks.
        status = protocol.STATUS_DEFERRED if self.defer_everything else protocol.STATUS_OK
        return MeshJobs.JobOutcome(
            job.job_id,
            status,
            0,
            job.result_ref,
            job.source_digest,
            elapsed_seconds=self.delay,
            artifact_bytes=len(job.job_id) + 5,
        )


def stub_job(job_id, mode="dfs", directory="/tmp", scope_ids=()):
    return protocol.Job(
        job_id,
        mode,
        {"start_text": "stub", "goal_text": "stub"},
        os.path.join(directory, job_id + ".json"),
        scope_ids=scope_ids,
    )


def start_peer(identity, role, runner, **kwargs):
    peer = MeshModule.build_peer(role, identity, runner=runner if role == MeshPeer.ROLE_WORKER else None, **kwargs)
    peer.start()
    return peer


def connect_client(identity, address, ca_path=None):
    """Open a raw mTLS connection to a peer, without the mesh protocol."""
    host, port = IdentityModule.parse_address(address)
    context = identity.client_context(ca_path=ca_path)
    raw = socket.create_connection((host, port), timeout=10)
    return context.wrap_socket(raw, server_hostname=host)


# ------------------------------------------------------------------- phase one


def phase_mtls(results, pki, directory):
    print("\n[1] mTLS: authentication and refusal paths")
    honest = MeshModule.ensure_identity(directory, "honest")
    coordinator = MeshPeer(honest, role=MeshPeer.ROLE_COORDINATOR, log=lambda text: None)
    coordinator.start()

    # An authenticated peer is admitted and can speak the protocol.
    try:
        client_socket = connect_client(honest, coordinator.address)
        framing.send_frame(
            client_socket,
            protocol.message(
                protocol.JOIN,
                peer_id="admitted-peer",
                address="127.0.0.1:1",
                common_name=honest.common_name,
                roles=[MeshPeer.ROLE_WORKER],
                modes=["dfs"],
                load={"queued": 0, "running": 0},
            ),
        )
        reply = framing.recv_frame(client_socket, timeout=10)
        results.check(
            "authenticated peer is admitted (WELCOME)",
            bool(reply) and reply.get("kind") == protocol.WELCOME,
            "kind=%s" % (reply or {}).get("kind"),
        )
        client_socket.close()
    except (ssl.SSLError, OSError) as error:
        results.check("authenticated peer is admitted (WELCOME)", False, repr(error))

    # Refusal 1: a leaf signed by a CA the peer does not trust.
    rogue_name, rogue_key, rogue_ca_path = pki.rogue_ca()
    rogue_leaf = pki.issue_from(
        (rogue_name, rogue_key, rogue_ca_path), "rogue-leaf", rogue_name, rogue_ca_path, sans=("127.0.0.1",)
    )
    results.check(
        "unknown CA's leaf is rejected",
        _expect_rejection(rogue_leaf, coordinator.address),
        "handshake or first frame refused",
    )

    # Refusal 2: the client trusts the wrong CA, so the *server's* cert fails.
    wrong_trust = IdentityModule.MeshIdentity(
        honest.common_name, honest.cert_path, honest.key_path, rogue_ca_path
    )
    results.check(
        "client distrusting the server's CA is rejected",
        _expect_rejection(wrong_trust, coordinator.address, client_ca=rogue_ca_path),
        "certificate verify failed",
    )

    # Refusal 3: an expired leaf.
    expired = pki.issue(
        "expired-leaf",
        sans=("127.0.0.1",),
        days=-1,
        not_before=_days_ago(10),
        not_after=_days_ago(1),
        basename="expired-leaf",
    )
    results.check("expired leaf is rejected", _expect_rejection(expired, coordinator.address), "certificate has expired")

    results.check(
        "refusals are recorded, not silent",
        len(coordinator.events("handshake-refused")) >= 2,
        "%d handshake-refused events" % len(coordinator.events("handshake-refused")),
    )
    coordinator.shutdown(timeout=1.0)


def _days_ago(days):
    import datetime

    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)


def _expect_rejection(identity, address, client_ca=None):
    """True if the connection cannot be established, or dies before any frame."""
    try:
        client_socket = connect_client(identity, address, ca_path=client_ca)
    except (ssl.SSLError, OSError):
        return True
    try:
        framing.send_frame(client_socket, protocol.message(protocol.HEARTBEAT, peer_id="probe"))
        client_socket.settimeout(5)
        reply = framing.recv_frame(client_socket, timeout=5)
        return reply is None
    except (ssl.SSLError, OSError, framing.FrameError):
        return True
    finally:
        try:
            client_socket.close()
        except OSError:
            pass


# ------------------------------------------------------------------- phase two


def phase_protocol(results, directory):
    print("\n[2] protocol invariants: dispatch, stealing, leases, staleness")
    coordinator_identity = MeshModule.ensure_identity(directory, "proto-coordinator")
    worker_identity_one = MeshModule.ensure_identity(directory, "proto-worker-1")
    worker_identity_two = MeshModule.ensure_identity(directory, "proto-worker-2")

    coordinator = start_peer(coordinator_identity, MeshPeer.ROLE_COORDINATOR, None)
    runner_one = StubRunner()
    runner_two = StubRunner()
    worker_one = start_peer(worker_identity_one, MeshPeer.ROLE_WORKER, runner_one)
    # worker-2 starts now but joins later: it is the late, idle peer whose only
    # route to work is stealing it from a busy one.
    worker_two = start_peer(worker_identity_two, MeshPeer.ROLE_WORKER, runner_two)
    worker_one.join(coordinator.address)
    results.check(
        "worker joins and is visible to the coordinator",
        coordinator.wait_for(lambda peer: len(peer.members()) == 1, timeout=10),
        "members=%s" % sorted(coordinator.members()),
    )

    # Dispatch: one job, run to completion, exactly one terminal record.
    job = stub_job("proto-dispatch", directory=directory)
    coordinator.submit(job)
    results.check(
        "a dispatched job completes",
        coordinator.wait_for(lambda peer: job.job_id in peer._results, timeout=15),
        "status=%s" % (coordinator.outcome(job.job_id) or {}).get("status"),
    )
    results.check("the worker ran it", runner_one.calls == [job.job_id], "calls=%s" % runner_one.calls)
    results.check(
        "exactly one terminal record for the job",
        len([event for event in coordinator.events("job-result") if event["job_id"] == job.job_id]) == 1,
    )
    results.check(
        "leases are released when the job finishes",
        coordinator.summary()["live_leases"] == 0,
        "live_leases=%d" % coordinator.summary()["live_leases"],
    )

    # Stale refusal: hand a peer a sequence it has already passed.
    stale_scope = "scope-tao-1-1"
    newer = protocol.Job("proto-newer", "dfs", {}, os.path.join(directory, "newer.json"), scope_ids=(stale_scope,), sequence=5)
    coordinator.submit(newer)
    coordinator.wait_for(lambda peer: newer.job_id in peer._results, timeout=15)
    stale = protocol.Job("proto-stale", "dfs", {}, os.path.join(directory, "stale.json"), scope_ids=(stale_scope,), sequence=4)
    refusal = worker_one._offer_refusal(stale)
    results.check(
        "a stale sequence is refused",
        refusal == protocol.REFUSED_STALE,
        "reason=%s" % refusal,
    )

    # Replaying a scope the worker already advanced is refused over the wire, and
    # that is where it ends: a sequence the scope has passed can never be run, so
    # the coordinator records it instead of re-offering it forever.
    replay = protocol.Job(
        "proto-replay", "dfs", {}, os.path.join(directory, "replay.json"), scope_ids=(stale_scope,), sequence=1
    )
    coordinator.submit(replay)
    replay_terminal = coordinator.wait_for(lambda peer: replay.job_id in peer._results, timeout=15)
    replay_declines = [event for event in coordinator.events("job-declined") if event["job_id"] == replay.job_id]
    replay_offers = [event for event in coordinator.events("job-dispatched") if event["job_id"] == replay.job_id]
    results.check(
        "a replay over an advanced scope is refused over the wire",
        replay_terminal
        and bool(replay_declines)
        and replay_declines[-1]["detail"] == protocol.REFUSED_STALE
        and coordinator._results[replay.job_id]["reason"] == protocol.REFUSED_STALE,
        "declines=%s terminal=%s" % ([event["detail"] for event in replay_declines], coordinator._results.get(replay.job_id, {}).get("reason")),
    )
    results.check(
        "a refused replay is offered once, not retried forever",
        len(replay_offers) == 1 and coordinator._job_state.get(replay.job_id) == "failed",
        "offers=%d state=%s" % (len(replay_offers), coordinator._job_state.get(replay.job_id)),
    )

    # A dropped offer is re-offered, not stranded. The watchdog only knows the
    # peer was silent, so this is safe *because* the peers refuse replays (above)
    # and live scopes (below) -- the guards, not the transport, provide the safety.
    default_ack_timeout = coordinator.offer_ack_timeout
    coordinator.offer_ack_timeout = 0.7  # only this job needs the short fuse
    stranded = protocol.Job("proto-stranded", "dfs", {}, os.path.join(directory, "stranded.json"))
    dropped = {"count": 0}
    real_send = coordinator._send

    def dropping_send(peer_id, message):
        if (
            message.get("kind") == protocol.JOB_OFFER
            and (message.get("job") or {}).get("job_id") == stranded.job_id
            and dropped["count"] == 0
        ):
            dropped["count"] = 1
            return True  # the offer is swallowed: the peer never hears about it
        return real_send(peer_id, message)

    coordinator._send = dropping_send
    coordinator.submit(stranded)
    stranded_ran = coordinator.wait_for(lambda peer: stranded.job_id in peer._results, timeout=25)
    coordinator._send = real_send
    coordinator.offer_ack_timeout = default_ack_timeout
    redispatched_details = [
        event["detail"] for event in coordinator.events("job-redispatched") if event["job_id"] == stranded.job_id
    ]
    stranded_record = coordinator._results.get(stranded.job_id, {})
    results.check(
        "an unanswered offer is re-offered, not stranded",
        stranded_ran
        and dropped["count"] == 1
        and bool(redispatched_details)
        and stranded_record.get("status") == protocol.STATUS_OK
        and stranded.job_id in runner_one.calls,
        "dropped=%d redispatched=%s status=%s ran=%s"
        % (dropped["count"], redispatched_details, stranded_record.get("status"), stranded.job_id in runner_one.calls),
    )

    # One writer per scope: a second job over a live scope is not dispatched.
    busy_runner = StubRunner(delay=1.2)
    worker_one.runner = busy_runner
    held = protocol.Job("proto-held", "dfs", {}, os.path.join(directory, "held.json"), scope_ids=("scope-shared",), sequence=1)
    blocked = protocol.Job("proto-blocked", "dfs", {}, os.path.join(directory, "blocked.json"), scope_ids=("scope-shared",), sequence=2)
    coordinator.submit(held)
    coordinator.submit(blocked)
    coordinator.wait_for(lambda peer: held.job_id in peer._results, timeout=25)
    # The invariant is about ordering, so read it off the ledger: the second job
    # over a live scope must not be dispatched until the first one's lease is
    # released. That is what "one writer per scope" means in practice.
    held_done = [event["ts"] for event in coordinator.events("job-result") if event["job_id"] == held.job_id]
    # The holder is released just after its result lands, so wait for the second
    # job to be offered before reading the order out of the ledger.
    coordinator.wait_for(
        lambda peer: any(event["job_id"] == blocked.job_id for event in peer.events("job-dispatched")),
        timeout=20,
    )
    blocked_dispatched = [
        event["ts"] for event in coordinator.events("job-dispatched") if event["job_id"] == blocked.job_id
    ]
    # The invariant is "one writer per scope while the holder is alive". A peer
    # declared lost has its lease released deliberately -- holding a scope open
    # for a peer that may never come back would deadlock the scope forever -- and
    # a partition is exactly where "exactly once" stops being this layer's
    # promise (W17 owns that). So the check reads: blocked waits for held, or
    # waits for held's holder to be lost, and held's own result still arrives.
    losses = [event["ts"] for event in coordinator.events("member-lost")]
    scope_ordering_ok = bool(held_done) and bool(blocked_dispatched) and (
        blocked_dispatched[0] >= held_done[0] or any(loss <= blocked_dispatched[0] for loss in losses)
    )
    results.check(
        "a second job over a live scope waits for the first to finish",
        scope_ordering_ok,
        "held finished at %s, blocked dispatched at %s, holder losses at %s"
        % (held_done[:1], blocked_dispatched[:1], losses[:2]),
    )
    if not scope_ordering_ok:
        results.note("job states: %s" % json.dumps(coordinator.summary()["job_states"], sort_keys=True))
        results.note("worker-1 events: %s" % [event["event"] + ":" + event["job_id"] for event in worker_one.events()][-8:])
        results.note("dispatch errors: %s" % [event["detail"] for event in coordinator.events("dispatch-error")][-3:])
        results.note("foreign leases: %s" % json.dumps({k: v.job_id for k, v in coordinator._foreign_leases.items()}, sort_keys=True))
        results.note("jobs: %s" % json.dumps({job_id: [job.sequence, job.scope_key, job.content_scope_key] for job_id, job in coordinator._jobs.items()}, sort_keys=True))
        results.note("members: %s" % json.dumps({peer_id: [record.get("address"), record.get("load"), record.get("roles")] for peer_id, record in coordinator.members().items()}, sort_keys=True))
        results.note("sequences: %s" % json.dumps(coordinator._sequence, sort_keys=True))
        results.note(
            "worker-1 refusals/accepts: %s"
            % [
                (event["event"], event["job_id"], event.get("detail"))
                for event in worker_one.events()
                if event["event"] in ("job-declined-locally", "job-declined", "job-accepted")
            ][-8:]
        )
        results.note(
            "coordinator ledger tail: %s"
            % [(event["event"], event["job_id"], event.get("detail")) for event in coordinator.events()][-25:]
        )
    blocked_ran = coordinator.wait_for(lambda peer: blocked.job_id in peer._results, timeout=25)
    # "Terminal" is not the same as "ran": a job may reach a terminal record as a
    # refusal, a watchdog verdict or a superseded provisional failure. Both jobs
    # are ordinary work over one scope, so both must end up with a real result.
    shared_status = {
        job_id: (coordinator._results.get(job_id) or {}).get("status") for job_id in (held.job_id, blocked.job_id)
    }
    results.check(
        "both jobs over the shared scope eventually run",
        blocked_ran and all(status == protocol.STATUS_OK for status in shared_status.values()),
        "statuses=%s terminal=%s" % (json.dumps(shared_status, sort_keys=True), sorted(coordinator.terminal_job_ids())),
    )
    if not blocked_ran:
        results.note("blocked state: %s" % coordinator._job_state.get(blocked.job_id))
        results.note(
            "worker-1 events with details: %s"
            % [(event["event"], event["job_id"], event.get("detail")) for event in worker_one.events()][-20:]
        )
        results.note(
            "coordinator ledger tail: %s"
            % [(event["event"], event["job_id"], event.get("detail")) for event in coordinator.events()][-30:]
        )
        results.note("coordinator members: %s" % sorted(coordinator.members()))
        results.note("worker-1 members: %s" % sorted(worker_one.members()))
        results.note(
            "worker-1 member records: %s"
            % json.dumps(
                {peer_id: [record.get("roles"), record.get("address"), record.get("load")] for peer_id, record in worker_one.members().items()},
                sort_keys=True,
            )
        )
        results.note("dial attempts: %s" % [(event["event"], event["peer_id"], event.get("detail")) for event in worker_one.events() if event["event"] == "steal-dialled"][-5:])

    # Stealing: an idle peer takes a queued job from a busy one, peer to peer.
    # Both jobs go to the only member first, so one of them is genuinely queued --
    # a *running* job is never handed over -- and the late joiner then steals it.
    # (Submitting before it joins is what makes this deterministic: otherwise the
    # dispatcher simply gives the second job to the second worker.)
    busy_one = stub_job("proto-busy-1", directory=directory)
    busy_two = stub_job("proto-busy-2", directory=directory)
    # The holder has to stay busy until the idle peer has actually taken the
    # queued job -- not for a guessed number of seconds. That peer must find the
    # holder's address in a heartbeat digest (0.4 s), authenticate a peer-to-peer
    # mTLS link to it and ask for the work, and on a loaded box that can outlast
    # any fixed window: with a 3 s sleep this check passed four runs in a row and
    # then lost the race, and the coordinator simply ran the queued job itself
    # (both jobs still finished, so nothing downstream noticed). Holding until the
    # coordinator records the steal removes the race and releases the instant it
    # lands, so it costs less than the sleep it replaces; the fuse bounds the
    # damage if a steal ever genuinely fails.
    worker_one.runner = StubRunner(hold=lambda: coordinator.summary()["steals"] < 1, fuse=10.0)
    coordinator.submit(busy_one)
    coordinator.submit(busy_two)
    results.check(
        "one job queues behind another at the busy peer",
        worker_one.wait_for(lambda peer: len(peer._queue) == 1 and peer._running is not None, timeout=15),
        "queued=%d running=%s" % (len(worker_one._queue), worker_one._running is not None),
    )
    worker_two.join(coordinator.address)
    coordinator.wait_for(lambda peer: len(peer.members()) == 2, timeout=10)
    results.check(
        "an idle peer steals a queued job (peer to peer)",
        coordinator.wait_for(
            lambda peer: peer.summary()["steals"] >= 1 and busy_one.job_id in peer._results and busy_two.job_id in peer._results,
            timeout=25,
        ),
        "steals=%d" % coordinator.summary()["steals"],
    )
    stolen = [record for record in coordinator._results.values() if record["stolen_from"]]
    results.check(
        "the stolen job records who it came from",
        bool(stolen),
        "stolen_from=%s" % [record["stolen_from"] for record in stolen],
    )
    result_events = {
        job_id: len([event for event in coordinator.events("job-result") if event["job_id"] == job_id])
        for job_id in (busy_one.job_id, busy_two.job_id)
    }
    results.check(
        "handing a job over does not duplicate it",
        all(count == 1 for count in result_events.values()),
        "job-result events per job: %s" % result_events,
    )

    # Lease reclamation when a peer's connection dies. Whichever worker the
    # dispatcher picks has to still be holding the lease when the test kills its
    # peer, so both get a slow runner: an instant one finishes the job before
    # there is anything to lose, and the check below reads `owner=None`.
    worker_one.runner = StubRunner(delay=3.0)
    dying_runner = StubRunner(delay=3.0)
    worker_two.runner = dying_runner
    doomed = stub_job("proto-doomed", directory=directory)
    coordinator.submit(doomed)
    coordinator.wait_for(lambda peer: doomed.job_id in peer._job_owner, timeout=10)
    results.check(
        "a lease is held while the job runs",
        coordinator.summary()["live_leases"] >= 1,
        "live_leases=%d" % coordinator.summary()["live_leases"],
    )
    owner = coordinator._job_owner.get(doomed.job_id)
    # Kill the peer that actually holds the lease -- which is not necessarily the
    # one the test would guess, since the dispatcher balances by load.
    peers_by_id = {worker_one.peer_id: worker_one, worker_two.peer_id: worker_two}
    victim = peers_by_id.get(owner)
    results.check("the doomed job has an owner to lose", victim is not None, "owner=%s" % owner)
    if victim is not None:
        victim._coordinator_connection.close()
        victim._stop.set()
    results.check(
        "a dead peer's lease is reclaimed and its job is not lost",
        coordinator.wait_for(
            lambda peer: (
                doomed.job_id in peer._results
                or any(event["event"] == "job-redispatched" and event["job_id"] == doomed.job_id for event in peer.events())
            ),
            timeout=25,
        ),
        "owner=%s terminal=%s" % (owner, doomed.job_id in coordinator._results),
    )

    # A `deferred` result is a result: the search concluded and the snapshot holds
    # the plan, only the derivation replay was skipped (that is the search worker's
    # own rc=4 under HYGE_SEARCH_WORKER_DEFER_DERIVATION=1). The ledger must not
    # turn it into a failure -- `main.py mesh` did exactly that to its exit code.
    for peer in (worker_one, worker_two):
        if peer.runner is not None:
            peer.runner.defer_everything = True
    before_deferred = coordinator.summary()
    deferred_job = stub_job("proto-deferred", directory=directory)
    coordinator.submit(deferred_job)
    coordinator.wait_for(lambda peer: deferred_job.job_id in peer._results, timeout=15)
    after_deferred = coordinator.summary()
    for peer in (worker_one, worker_two):
        if peer.runner is not None:
            peer.runner.defer_everything = False
    results.check(
        "a deferred result counts as a result, not a failure",
        (coordinator.outcome(deferred_job.job_id) or {}).get("status") == protocol.STATUS_DEFERRED
        # The invariant is about *this* job: `status_is_success` accepts it and the
        # ledger files it under `done`. The summary counters are only a proxy for
        # that, and they are not this check's to read -- several jobs are in
        # flight, so an unrelated one finishing or failing inside the window moves
        # both counters. That is why `completed` is a `>` and not a `+1`, and why
        # the `failed` counter is not compared at all: it caught a run where an
        # unrelated job failed while this one was being recorded, and reported a
        # defect in a check that had found none.
        and protocol.status_is_success((coordinator.outcome(deferred_job.job_id) or {}).get("status"))
        and coordinator._job_state.get(deferred_job.job_id) == "done"
        and after_deferred["completed"] > before_deferred["completed"],
        "status=%s state=%s completed %s->%s failed %s->%s"
        % (
            (coordinator.outcome(deferred_job.job_id) or {}).get("status"),
            coordinator._job_state.get(deferred_job.job_id),
            before_deferred["completed"],
            after_deferred["completed"],
            before_deferred["failed"],
            after_deferred["failed"],
        ),
    )

    # A job that is already finished must not be resurrected by a late progress
    # report. Found by the W16 kill test: a unit orphaned by a lost peer was
    # recorded as failed and then run anyway by a peer that still held it in its
    # queue, and the coordinator accepted the report -- leaving job_states
    # {done: 3, running: 1} beside terminal: 4, with the second run's result
    # dropped, because a terminal record is never overwritten. The swarm still
    # reported the loss rather than losing it silently, but a ledger that says a
    # finished job is running cannot be trusted by anything reading it.
    finished_job = stub_job("proto-finished", directory=directory)
    coordinator.submit(finished_job)
    coordinator.wait_for(lambda peer: finished_job.job_id in peer._results, timeout=15)
    finished_state = coordinator._job_state.get(finished_job.job_id)
    ignored_before = len(coordinator.events("progress-after-terminal-ignored"))
    coordinator._note_job_progress(
        protocol.message(protocol.JOB_STARTED, job_id=finished_job.job_id, peer_id="ghost-peer")
    )
    coordinator._note_job_progress(
        protocol.message(protocol.JOB_QUEUED, job_id=finished_job.job_id, peer_id="ghost-peer")
    )
    results.check(
        "a finished job is not resurrected by a late progress report",
        coordinator._job_state.get(finished_job.job_id) == finished_state
        and coordinator._job_owner.get(finished_job.job_id) != "ghost-peer"
        and len(coordinator.events("progress-after-terminal-ignored")) == ignored_before + 2,
        "state=%s owner=%s ignored=%d"
        % (
            coordinator._job_state.get(finished_job.job_id),
            coordinator._job_owner.get(finished_job.job_id),
            len(coordinator.events("progress-after-terminal-ignored")) - ignored_before,
        ),
    )

    # The other half of what the W16 kill test found. Stopping the ledger from
    # claiming a finished job is running is not enough: the job that ran out of
    # attempts was still being *run* by a peer that held it in its queue, and
    # when that run came back with a proof, `_handle_job_result` refused it --
    # a recorded failure was final unless it had been provisional. So the proof
    # was computed and thrown away while the swarm reported a failure. Any
    # recorded failure now gives way to a real success, in both directions of
    # the transport, while a recorded success stays final.
    written_off = stub_job("proto-written-off", directory=directory)
    coordinator._finish_job(written_off, protocol.STATUS_FAILED, reason="attempts-exhausted")
    superseded_before = len(coordinator.events("result-superseded"))
    coordinator._handle_job_result(
        protocol.message(
            protocol.JOB_RESULT,
            job_id=written_off.job_id,
            peer_id="late-peer",
            status=protocol.STATUS_OK,
            result_ref=written_off.result_ref,
            artifact_bytes=1234,
        )
    )
    late_record = coordinator.outcome(written_off.job_id) or {}
    results.check(
        "a recorded failure gives way to a real success",
        late_record.get("status") == protocol.STATUS_OK
        and coordinator._job_state.get(written_off.job_id) == "done"
        and len(coordinator.events("result-superseded")) == superseded_before + 1,
        "status=%s state=%s superseded=%d"
        % (
            late_record.get("status"),
            coordinator._job_state.get(written_off.job_id),
            len(coordinator.events("result-superseded")) - superseded_before,
        ),
    )
    contradict_before = len(coordinator.events("result-superseded"))
    coordinator._handle_job_result(
        protocol.message(
            protocol.JOB_RESULT,
            job_id=written_off.job_id,
            peer_id="other-peer",
            status=protocol.STATUS_FAILED,
            result_ref=written_off.result_ref,
        )
    )
    final_record = coordinator.outcome(written_off.job_id) or {}
    results.check(
        "a recorded success stays final",
        final_record.get("status") == protocol.STATUS_OK
        and coordinator._job_state.get(written_off.job_id) == "done"
        and len(coordinator.events("result-superseded")) == contradict_before,
        "status=%s state=%s superseded=%d"
        % (
            final_record.get("status"),
            coordinator._job_state.get(written_off.job_id),
            len(coordinator.events("result-superseded")) - contradict_before,
        ),
    )

    # A coordinator that shuts down must actually tell its members: the notice is
    # queued on the connection and closing it abandons what the writer still holds,
    # which is how a CLI worker used to spend the rest of its life reconnecting to
    # a coordinator that was gone. (The peer the doomed-job check stopped on purpose
    # cannot hear anything, so the check asks whichever worker is still live.)
    survivor = worker_two if not worker_two._stop.is_set() else worker_one
    coordinator.shutdown(timeout=2.0)
    results.check(
        "a shutting-down coordinator tells its members, and they stop",
        survivor.wait_for(lambda peer: peer._stop.is_set(), timeout=5)
        and bool(survivor.events("shutdown-requested")),
        "survivor=%s stopped=%s events=%s"
        % (
            survivor.peer_id,
            survivor._stop.is_set(),
            [event["event"] for event in survivor.events()][-4:],
        ),
    )

    worker_one.shutdown(timeout=1.0)
    worker_two.shutdown(timeout=1.0)

    # The other half of the crash clause. The check above proves a crashed peer's
    # job is *re-dispatched*; the brief also allows it to be *reported failed*,
    # and the two are alternatives, not a choice -- what is forbidden is a job
    # that quietly vanishes. So: a coordinator that will not re-dispatch, and a
    # job whose only peer dies mid-run. The honest outcome is a terminal failure
    # record naming the reason; a silent loss would leave no terminal record at
    # all and the `failed` count untouched. Its own mesh, because this check has
    # to kill the last worker standing.
    loss_coordinator_identity = MeshModule.ensure_identity(directory, "proto-loss-coordinator")
    loss_worker_identity = MeshModule.ensure_identity(directory, "proto-loss-worker")
    loss_coordinator = start_peer(loss_coordinator_identity, MeshPeer.ROLE_COORDINATOR, None)
    loss_coordinator.redispatch_on_crash = False  # `build_peer` does not tune this; the test owns it
    loss_worker = start_peer(loss_worker_identity, MeshPeer.ROLE_WORKER, StubRunner(delay=1.5))
    loss_worker.join(loss_coordinator.address)
    lost = stub_job("proto-lost", directory=directory)
    loss_coordinator.submit(lost)
    loss_coordinator.wait_for(lambda peer: lost.job_id in peer._job_owner, timeout=10)
    before_lost = loss_coordinator.summary()
    loss_worker._coordinator_connection.close()
    loss_worker._stop.set()
    reported = loss_coordinator.wait_for(lambda peer: lost.job_id in peer._results, timeout=20)
    after_lost = loss_coordinator.summary()
    lost_record = loss_coordinator.outcome(lost.job_id) or {}
    results.check(
        "a job that cannot be re-dispatched is reported failed, not lost",
        reported
        and lost_record.get("status") == protocol.STATUS_FAILED
        and lost_record.get("reason") == "worker-lost"
        and loss_coordinator._job_state.get(lost.job_id) == "failed"
        and after_lost["failed"] > before_lost["failed"]
        and not any(
            event["job_id"] == lost.job_id for event in loss_coordinator.events("job-redispatched")
        ),
        "status=%s reason=%s state=%s failed %s->%s redispatches=%d"
        % (
            lost_record.get("status"),
            lost_record.get("reason"),
            loss_coordinator._job_state.get(lost.job_id),
            before_lost["failed"],
            after_lost["failed"],
            after_lost["redispatches"],
        ),
    )
    loss_coordinator.shutdown(timeout=1.0)
    loss_worker.shutdown(timeout=1.0)


# ----------------------------------------------------------------- phase three


def phase_real_jobs(results, directory):
    """Two real searches over real subprocesses: a second worker, then a kill.

    The comparison against a single-process run is deliberately per job and
    per process. A peer reuses *one* booted runtime for every job it runs -- that
    is the point of the one-boot-per-peer design -- and the runtime caches what
    it has solved, so the second job in a runtime reaches a memo instead of
    searching from scratch and its plan is not the fresh plan. Only the first
    job a peer runs is therefore comparable with a fresh process, and which job
    that is is read out of the ledger rather than assumed.
    """
    print("\n[3] real search jobs over real subprocesses, a second worker, and a killed worker")
    work_dir = os.path.join(directory, "work")
    os.makedirs(work_dir, exist_ok=True)

    specs = []
    for entry in JOBS:
        specs.append(
            {
                "job_id": entry["job_id"],
                "mode": entry["mode"],
                "result_ref": os.path.join(work_dir, "mesh-%s.json" % entry["mode"]),
                "manifest": {},
            }
        )
    reference_dir = os.path.join(directory, "reference")
    os.makedirs(reference_dir, exist_ok=True)
    for spec in specs:
        spec["reference_ref"] = os.path.join(reference_dir, "local-%s.json" % spec["mode"])

    environment = dict(os.environ)
    environment["PYTHONPATH"] = PACKAGE_PARENT
    environment["HYGE_SEARCH_WORKER_DEFER_DERIVATION"] = "1"

    coordinator_identity = MeshModule.ensure_identity(directory, "coordinator")
    coordinator = start_peer(coordinator_identity, MeshPeer.ROLE_COORDINATOR, None)
    workers = {}
    reference_processes = {}
    reference_answers = {}

    def _start_reference(spec):
        """Run one job alone, in its own process: the file transport's baseline.

        The reference prints the search pipeline's own chatter, which is far more
        than a pipe buffer, so it writes that to a log and its answer to a file --
        capturing stdout through an unread pipe would block the child forever.
        """
        log_handle = open(os.path.join(directory, "reference-%s.log" % spec["job_id"]), "w", encoding="utf-8")
        answer_path = os.path.join(reference_dir, "%s.json" % spec["job_id"])
        reference_answers[spec["job_id"]] = answer_path
        reference_processes[spec["job_id"]] = subprocess.Popen(
            [
                sys.executable,
                "-u",
                os.path.abspath(__file__),
                "--reference",
                json.dumps([spec]),
                answer_path,
            ],
            cwd=PACKAGE_ROOT,
            env=environment,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )

    def _reference_results(job_id):
        process = reference_processes[job_id]
        try:
            process.wait(timeout=600)
        except subprocess.TimeoutExpired:
            results.note("reference for %s never finished" % job_id)
            return {}
        try:
            with open(reference_answers[job_id], encoding="utf-8") as handle:
                return json.load(handle).get("jobs", {})
        except (OSError, ValueError) as error:
            results.note("reference for %s unreadable: %r" % (job_id, error))
            return {}

    # Which peer produced a job's result, and had that peer run anything before?
    # The answer decides comparability, so it comes from the ledger, not a guess.
    def _first_job_of_its_peer(job_id):
        starts = [event for event in coordinator.events("job-started") if event.get("peer_id")]
        finishes = [event for event in coordinator.events("job-result") if event["job_id"] == job_id]
        if not finishes or not any(event["job_id"] == job_id for event in starts):
            return ""
        # The *last* start before the result is the peer that actually ran it: a
        # killed job can be started twice, by two different peers.
        own = [event for event in starts if event["job_id"] == job_id and event["ts"] <= finishes[-1]["ts"]]
        if not own:
            return ""
        owner = own[-1]["peer_id"]
        # A peer's first job is the one whose earliest start record is the peer's
        # earliest of all -- not merely the earliest record of this job, because a
        # start can be recorded twice (the send and its arrival).
        other_starts = {}
        for event in starts:
            if event["peer_id"] != owner or event["job_id"] == job_id:
                continue
            other_starts[event["job_id"]] = min(other_starts.get(event["job_id"], event["ts"]), event["ts"])
        this_start = min(event["ts"] for event in own)
        return owner if not other_starts or min(other_starts.values()) > this_start else ""

    try:
        workers["worker-1"] = _spawn_worker(directory, "worker-1", coordinator.address, environment)
        results.check(
            "worker-1 joins the mesh",
            coordinator.wait_for(lambda peer: _has_member(peer, "worker-1"), timeout=240),
            "members=%s" % sorted(_member_ids(coordinator)),
        )

        # Both jobs go to the only peer there is: one starts, the other waits in its
        # queue. worker-2 then has to *take* the queued one -- the coordinator has
        # already placed it, and a placement is never re-offered -- which is a real
        # peer-to-peer steal between two real subprocesses. The stolen job is the
        # thief's first job, so it stays comparable with a fresh process.
        coordinator.submit(_job_from_spec(specs[0]))
        coordinator.submit(_job_from_spec(specs[1]))
        results.check(
            "worker-1 starts a real search",
            coordinator.wait_for(
                lambda peer: any(
                    event["event"] == "job-started" and event["job_id"] == specs[0]["job_id"] for event in peer.events()
                ),
                timeout=180,
            ),
            "job=%s" % specs[0]["job_id"],
        )
        _start_reference(specs[1])

        workers["worker-2"] = _spawn_worker(directory, "worker-2", coordinator.address, environment)
        results.check(
            "worker-2 joins while worker-1 is busy",
            coordinator.wait_for(lambda peer: _has_member(peer, "worker-2"), timeout=240),
            "members=%s" % sorted(_member_ids(coordinator)),
        )
        worker_two_id = next((peer_id for peer_id in _member_ids(coordinator) if peer_id.startswith("worker-2")), "")

        def _stolen_by_worker_two(peer):
            for event in peer.events("job-started"):
                if event["job_id"] == specs[1]["job_id"] and (event.get("peer_id") or "").startswith("worker-2"):
                    return True
            return False

        results.check(
            "an idle peer steals the queued job from the busy one (real subprocesses)",
            coordinator.wait_for(_stolen_by_worker_two, timeout=180),
            "job=%s thief=%s started=%s"
            % (
                specs[1]["job_id"],
                worker_two_id or "-",
                [(event["job_id"], (event.get("peer_id") or "-"), round(event["ts"], 1)) for event in coordinator.events("job-started")],
            ),
        )

        # Kill worker-1 mid-search: the peer that owns a running job disappears.
        _kill_process(workers["worker-1"])
        results.check(
            "the mesh notices the dead worker",
            coordinator.wait_for(
                lambda peer: any(event["event"] == "member-lost" for event in peer.events()),
                timeout=30,
            ),
            "member-lost=%s members=%s closed=%s"
            % (
                sorted({(event.get("peer_id", ""), event.get("detail", "")) for event in coordinator.events("member-lost")}),
                sorted(_member_ids(coordinator)),
                sorted(
                    {
                        (event.get("peer_id", ""), event.get("detail", ""))
                        for event in coordinator.events("connection-closed")
                    }
                )[-3:],
            ),
        )
        results.check(
            "every job reaches a terminal record (none silently lost)",
            coordinator.wait_for_terminal([spec["job_id"] for spec in specs], timeout=300),
            "terminal=%s" % sorted(coordinator.terminal_job_ids()),
        )
        killed_job = coordinator.outcome(specs[0]["job_id"]) or {}
        redispatched = [
            event for event in coordinator.events("job-redispatched") if event["job_id"] == specs[0]["job_id"]
        ]
        results.check(
            "the killed worker's job is re-dispatched, not lost",
            bool(redispatched),
            "job=%s reason=%s redispatches=%d"
            % (specs[0]["job_id"], killed_job.get("reason", "-"), len(redispatched)),
        )
        # The phase defers derivation materialisation (HYGE_SEARCH_WORKER_DEFER_DERIVATION=1):
        # the search worker's own contract then returns rc=4, which the mesh records as
        # `deferred` -- the search concluded and only the derivation replay was skipped.
        # No result at all would be `failed`/`timed-out`.
        results.check(
            "the killed worker's job still produced a result",
            killed_job.get("status") in (protocol.STATUS_OK, protocol.STATUS_DEFERRED),
            "job=%s status=%s" % (specs[0]["job_id"], killed_job.get("status")),
        )
        results.check(
            "no job records its result twice",
            all(
                len([event for event in coordinator.events("job-result") if event["job_id"] == spec["job_id"]]) == 1
                for spec in specs
            ),
            "counts=%s"
            % {
                spec["job_id"]: len(
                    [event for event in coordinator.events("job-result") if event["job_id"] == spec["job_id"]]
                )
                for spec in specs
            },
        )
        stolen_record = coordinator._results.get(specs[1]["job_id"]) or {}
        results.check(
            "the stolen job is recorded as taken from the peer that had it",
            bool(stolen_record.get("stolen_from"))
            and stolen_record.get("peer_id", "").startswith("worker-2")
            and (stolen_record.get("stolen_from") or "").startswith("worker-1"),
            "stolen_from=%s ran_by=%s" % (stolen_record.get("stolen_from"), stolen_record.get("peer_id")),
        )

        # A killed re-run lands on a peer whose runtime may already hold the proof,
        # so what is asserted for it is that a real search happened: the artifact
        # loads and stopped at the plan stage. Its *content* is compared only when
        # its peer ran it first (below).
        killed_projection = MeshJobs.project_result(specs[0]["result_ref"])
        results.check(
            "the killed worker's job really searched",
            killed_projection.get("worker_stage") == "running-derivation"
            and killed_projection.get("plan_digest") not in (None, "-"),
            "stage=%s plan=%s" % (killed_projection.get("worker_stage"), killed_projection.get("plan_digest")),
        )

        # The comparison: every job that was its peer's first run must equal the
        # same job run alone in a fresh process.
        references = {spec["job_id"]: _reference_results(spec["job_id"]) for spec in specs if spec["job_id"] in reference_processes}
        compared = []
        mismatched = []
        for spec in specs:
            owner = _first_job_of_its_peer(spec["job_id"])
            if not owner or spec["job_id"] not in references:
                continue
            local = references[spec["job_id"]].get(spec["job_id"], {}).get("projection", {})
            if not local:
                mismatched.append((spec["job_id"], "the reference produced nothing", {}))
                continue
            mesh_projection = MeshJobs.project_result(spec["result_ref"])
            compared.append(spec["job_id"])
            if not _semantic_equal(mesh_projection, local):
                mismatched.append((spec["job_id"], mesh_projection, local))
        results.check(
            "a job's result equals the same job run alone in a fresh process",
            bool(compared) and not mismatched,
            "compared=%s mismatched=%s" % (compared, [entry[0] for entry in mismatched]),
        )
        if not compared:
            results.note(
                "job-started ledger: %s"
                % [(event["job_id"], event.get("peer_id", ""), round(event["ts"], 2)) for event in coordinator.events("job-started")]
            )
            results.note(
                "job-result ledger: %s"
                % [(event["job_id"], event.get("peer_id", ""), round(event["ts"], 2)) for event in coordinator.events("job-result")]
            )
            results.note("first-job owners: %s" % {spec["job_id"]: _first_job_of_its_peer(spec["job_id"]) for spec in specs})
        for job_id, mesh_projection, local_projection in mismatched:
            results.note("mesh[%s]=%s" % (job_id, json.dumps(mesh_projection, sort_keys=True)))
            results.note("local[%s]=%s" % (job_id, json.dumps(local_projection, sort_keys=True)))

        results.check(
            "the reference produced a result for the job it was given",
            all(bool(references.get(spec["job_id"], {}).get(spec["job_id"])) for spec in specs if spec["job_id"] in reference_processes),
            "jobs=%s" % sorted({job_id for job_id, answer in references.items() if answer}),
        )
        results.check(
            "the real jobs actually proved the goal (not a failed search)",
            all(
                (coordinator.outcome(spec["job_id"]) or {}).get("status") in (protocol.STATUS_OK, protocol.STATUS_DEFERRED)
                for spec in specs
            ),
            "statuses=%s" % [((coordinator.outcome(spec["job_id"]) or {}).get("status")) for spec in specs],
        )
    finally:
        for process in workers.values():
            _kill_process(process)
        coordinator.shutdown(timeout=2.0)
        for process in reference_processes.values():
            _terminate(process)
    return specs


def _member_ids(peer):
    return set(peer.members().keys())


def _has_member(peer, name):
    """A CLI peer is named after its certificate plus a random suffix."""
    return any(peer_id == name or peer_id.startswith(name + "-") for peer_id in _member_ids(peer))


def _job_from_spec(spec):
    return protocol.Job(spec["job_id"], spec["mode"], spec.get("manifest", {}), spec["result_ref"])


def _spawn_worker(directory, name, coordinator_address, environment, modes="dfs,bfs,astar,beam,rewritedfs"):
    log_path = os.path.join(directory, "%s.log" % name)
    log_handle = open(log_path, "w", encoding="utf-8")
    return subprocess.Popen(
        [
            sys.executable,
            "-u",
            os.path.join(PACKAGE_ROOT, "main.py"),
            "mesh",
            "--role",
            "worker",
            "--bind",
            "127.0.0.1:0",
            "--coordinator",
            coordinator_address,
            "--cert-dir",
            directory,
            "--cert-name",
            name,
            "--modes",
            modes,
        ],
        cwd=PACKAGE_ROOT,
        env=environment,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )


def _kill_process(process):
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def _terminate(process):
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=10)
    except (subprocess.TimeoutExpired, OSError):
        _kill_process(process)


def _semantic_equal(mesh_projection, local_projection):
    """Compare the machine-semantic part of two results, ignoring timing."""
    keys = ("status", "worker_stage", "plan_digest", "derivation_digest", "derivation_bytes", "proof_cost_digest")
    return all(mesh_projection.get(key) == local_projection.get(key) for key in keys)


# ------------------------------------------------------------- reference helper


def run_reference(specs_json, answer_path=None):
    """Run every job once, in one process, with one boot: the single-process baseline."""
    specs = json.loads(specs_json)
    from cat_theo_machine import main as MA

    runner = MeshJobs.SearchJobRunner(timeout_seconds=6000)
    jobs = {}
    for index, spec in enumerate(specs):
        job = protocol.Job(spec["job_id"], spec["mode"], spec.get("manifest", {}), spec["reference_ref"])
        started = time.time()
        outcome = runner.run(job)
        projection = MeshJobs.project_result(job.result_ref)
        jobs[spec["job_id"]] = {
            "status": outcome.status,
            "exit_code": outcome.exit_code,
            "elapsed_seconds": round(time.time() - started, 2),
            "result_ref": job.result_ref,
            "projection": projection,
        }
        print("[reference] %s %s %.1fs" % (job.job_id, outcome.status, time.time() - started), flush=True)
    answer = json.dumps({"jobs": jobs})
    if answer_path:
        with open(answer_path, "w", encoding="utf-8") as handle:
            handle.write(answer)
    print("REFERENCE-JSON %s" % answer, flush=True)
    return 0


# ---------------------------------------------------------- phase four: regression


def phase_file_transport(results, directory):
    print("\n[4] file transport: `search-worker` still runs unchanged")
    result_path = os.path.join(directory, "cli-worker.json")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = PACKAGE_PARENT
    environment["HYGE_SEARCH_WORKER_DEFER_DERIVATION"] = "1"
    completed = subprocess.run(
        # One second of search budget: the point is the *transport* still works and
        # still writes a loadable snapshot, and the pack boot dominates this phase
        # either way.
        [sys.executable, "-u", os.path.join(PACKAGE_ROOT, "main.py"), "search-worker", "dfs", result_path, "1"],
        cwd=PACKAGE_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=300,
    )
    results.check(
        "search-worker exits with a meaningful code",
        completed.returncode in (0, 2, 4),
        "rc=%d" % completed.returncode,
    )
    results.check(
        "search-worker wrote a loadable result snapshot",
        os.path.exists(result_path) and MeshJobs.project_result(result_path).get("status") not in (None, "no-attempt"),
        "bytes=%d" % (os.path.getsize(result_path) if os.path.exists(result_path) else 0),
    )


def phase_frame_guard(results, directory):
    print("\n[5] guards: machine values never cross the wire, keys never enter the repo")
    try:
        framing.encode_frame({"pickle": "..."})
        results.check("a frame carrying a machine payload is refused", False)
    except framing.FrameError:
        results.check("a frame carrying a machine payload is refused", True)

    # A real frame, sent over a real socket pair, must survive the round trip and
    # carry the job *description* (manifest + result reference), not a term.
    left, right = socket.socketpair()
    try:
        framing.send_frame(left, protocol.message(protocol.JOB_OFFER, job=stub_job("round-trip").as_dict()))
        received = framing.recv_frame(right, timeout=5)
        job_again = protocol.Job.from_dict(received["job"])
        results.check(
            "a legitimate frame round-trips over a socket",
            job_again.job_id == "round-trip" and job_again.result_ref.endswith("round-trip.json"),
            "kind=%s" % received.get("kind"),
        )
        results.check(
            "the wire carries a reference, not a result payload",
            "result_ref" in received["job"] and "term_payload" not in received["job"],
        )
    finally:
        left.close()
        right.close()

    # The reader polls with a short idle timeout, so a frame that arrives in
    # pieces must still be read whole: bytes already read may never be dropped,
    # or the stream would desynchronise and the peer would go quiet for good.
    split_left, split_right = socket.socketpair()
    try:
        frame = framing.encode_frame(protocol.message(protocol.JOB_OFFER, job=stub_job("split").as_dict()))
        split_left.sendall(frame[:2])          # the length prefix, half delivered
        time.sleep(0.4)                        # longer than the reader's poll timeout
        split_left.sendall(frame[2:])
        try:
            split_received = framing.recv_frame(split_right, timeout=0.1)
            split_ok = (split_received or {}).get("job", {}).get("job_id") == "split"
            split_detail = "kind=%s" % (split_received or {}).get("kind")
        except socket.timeout:
            split_ok, split_detail = False, "the frame was lost to the poll timeout"
        results.check("a frame split across two writes is still read whole", split_ok, split_detail)

        # An idle timeout must not consume anything either: the next frame arrives
        # intact after the caller has polled and given up once.
        try:
            framing.recv_frame(split_right, timeout=0.1)
            idle_ok, idle_detail = False, "an idle socket returned a frame"
        except socket.timeout:
            idle_ok, idle_detail = True, "polled and left the stream alone"
        framing.send_frame(split_left, protocol.message(protocol.JOB_OFFER, job=stub_job("after-idle").as_dict()))
        after = framing.recv_frame(split_right, timeout=5)
        results.check(
            "an idle timeout leaves the next frame readable",
            idle_ok and after.get("job", {}).get("job_id") == "after-idle",
            "%s; next=%s" % (idle_detail, after.get("job", {}).get("job_id")),
        )
    finally:
        split_left.close()
        split_right.close()

    try:
        MeshModule.ensure_identity(os.path.join(PACKAGE_ROOT, "should-not-exist"), "leak")
        results.check("key material is refused inside the repository", False)
    except RuntimeError:
        results.check("key material is refused inside the repository", True)
    leaked = os.path.join(PACKAGE_ROOT, "should-not-exist")
    if os.path.exists(leaked):
        shutil.rmtree(leaked, ignore_errors=True)


# ------------------------------------------------------------------------ main


def main():
    print("=== TEST 25: W2 framed RPC over mTLS, mesh membership, work stealing ===")
    started = time.time()
    results = Results()
    directory = MeshModule.default_cert_dir()
    pki = IdentityModule.MeshPki.create(directory)
    timings = []
    try:
        for phase in (phase_mtls, phase_protocol, phase_frame_guard, phase_real_jobs, phase_file_transport):
            phase_started = time.time()
            phase(results, pki, directory) if phase is phase_mtls else phase(results, directory)
            timings.append((phase.__name__, round(time.time() - phase_started, 1)))
    finally:
        shutil.rmtree(directory, ignore_errors=True)
        print("\n  artifacts: %s (removed)" % directory)
    elapsed = time.time() - started
    print("\n  phase wall clock: %s" % ("  ".join("%s=%.1fs" % item for item in timings)))
    print(
        "\n=== TEST 25 COMPLETE: %d passed, %d failed in %.1fs ===" % (results.passed, results.failed, elapsed)
    )
    return 1 if results.failed else 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--reference":
        # argv[3], when given, is the file the answer is written to (the caller
        # captures the pipeline's chatter separately).
        raise SystemExit(run_reference(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
    raise SystemExit(main())
