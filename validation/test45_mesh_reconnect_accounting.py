"""Test 45 -- W33: mesh reconnect attempt accounting.

Run:
    PYTHONPATH=/home/user .venv/bin/python -u validation/test45_mesh_reconnect_accounting.py

What this suite is for
----------------------
`delegation/W33-mesh-reconnect-accounting.md`, DAG §6.5 / §6.8 / §8 (W33).

`test27` once failed 49/51 like this: a worker was SIGKILLed mid-unit and the
unit was re-dispatched to the survivor (`attempt 2`, the last one the budget
allows). The kill also closed the *survivor's* coordinator connection for
0.2 s (`coordinator-lost`, then `rejoined` on the survivor). The coordinator
counted that blink as a second loss of the already re-dispatched unit, hit
`max_attempts`, finalised it `failed` / `worker-lost` while the survivor
still held it queued, and -- every submitted job now having a terminal
record -- shut down before the survivor ever started it. The W2 follow-up
fixes healed the *outcome* side (a late real success supersedes a recorded
failure); the *attempt accounting* was left exactly as it was.

So this suite pins the distinction the fix has to make:

* a **severed connection** is evidence about a link, not about a peer. It
  makes the member *suspect* for a bounded reconnect grace: owners, job
  states, leases, offer bookkeeping and attempt numbers are frozen, and no
  terminal record is written -- so a coordinator cannot mistake a blink for
  "all jobs settled" and shut down under a queued unit either. A peer that
  re-joins with the same id inside the grace cancels the loss for free.
* a **goodbye** and a **heartbeat timeout** are losses at once, and a suspect
  that stays gone past the grace resolves into the old loss exactly once:
  leases reclaimed, one attempt charged, the job re-dispatched or reported
  `worker-lost`. The crash clause of W2/W16 is unchanged, only deferred.
* the offer watchdog is attempt accounting too: it does not charge an
  unanswered offer against a peer that is merely suspect.

Everything runs over real mTLS sockets with stub runners and explicit gates
(the `test25` phase-2 pattern): no machine boot, no SIGKILL, and no step
waits on a guessed number of seconds where an event can be waited on instead.
The blink itself is reproduced by closing a live worker's coordinator
connection -- on the coordinator that is precisely the connection the
SIGKILL closed in `test27`, only the worker behind it stays alive.
"""

from __future__ import annotations

import os
import shutil
import sys
import threading
import time

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_PARENT = os.path.dirname(PACKAGE_ROOT)
if PACKAGE_PARENT not in sys.path:
    sys.path.insert(0, PACKAGE_PARENT)

from cat_theo_machine import mesh as MeshModule
from cat_theo_machine.networking import identity as IdentityModule
from cat_theo_machine.networking import jobs as MeshJobs
from cat_theo_machine.networking import protocol
from cat_theo_machine.networking.peer import MeshPeer

QUIET = lambda text: None  # noqa: E731 -- the suites pass log callables around


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


class GatedRunner:
    """Deterministic jobs: a gated job runs until the test opens its gate.

    Gates, not sleeps, are what put a job provably in `running` on one peer
    and provably in `queued` on another before a link is cut.
    """

    def __init__(self, modes=("dfs", "bfs", "astar", "beam", "rewritedfs")):
        self.supported_modes = tuple(modes)
        self.booted = True
        self.calls = []
        self._gates = {}
        self._started = {}
        self._lock = threading.Lock()

    def supports(self, mode):
        return mode in self.supported_modes

    def gate(self, job_id):
        with self._lock:
            return self._gates.setdefault(job_id, threading.Event())

    def release(self, job_id):
        self.gate(job_id).set()

    def release_all(self):
        with self._lock:
            gates = list(self._gates.values())
        for gate in gates:
            gate.set()

    def started(self, job_id):
        with self._lock:
            return self._started.setdefault(job_id, threading.Event())

    def run(self, job):
        with self._lock:
            self.calls.append(job.job_id)
            gate = self._gates.get(job.job_id)
        self.started(job.job_id).set()
        if gate is not None:
            # Bounded so a test bug costs seconds, never a hung suite.
            gate.wait(timeout=30.0)
        directory = os.path.dirname(job.result_ref)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(job.result_ref, "w", encoding="utf-8") as handle:
            handle.write("stub:%s" % job.job_id)
        return MeshJobs.JobOutcome(
            job.job_id,
            protocol.STATUS_OK,
            0,
            job.result_ref,
            job.source_digest,
            elapsed_seconds=0.0,
            artifact_bytes=len(job.job_id) + 5,
        )


def stub_job(job_id, directory, mode="dfs"):
    return protocol.Job(
        job_id,
        mode,
        {"start_text": "stub", "goal_text": "stub"},
        os.path.join(directory, job_id + ".json"),
    )


def events_for(peer, event, job_id=None, peer_id=None):
    found = peer.events(event)
    if job_id is not None:
        found = [entry for entry in found if entry.get("job_id") == job_id]
    if peer_id is not None:
        found = [entry for entry in found if entry.get("peer_id") == peer_id]
    return found


def attempt_of(coordinator, job_id):
    job = coordinator._jobs.get(job_id)
    return job.attempt if job is not None else None


def start_coordinator(directory, name, grace=None, **kwargs):
    peer = MeshPeer(
        MeshModule.ensure_identity(directory, name),
        role=MeshPeer.ROLE_COORDINATOR,
        log=QUIET,
        **kwargs,
    )
    if grace is not None:
        # Post-build tuning, the way test25 owns `redispatch_on_crash`;
        # phase 4 pins the constructor argument itself.
        peer.reconnect_grace = grace
    peer.start()
    return peer


def start_worker(directory, name, runner):
    peer = MeshPeer(
        MeshModule.ensure_identity(directory, name),
        role=MeshPeer.ROLE_WORKER,
        runner=runner,
        steal_enabled=False,  # accounting under test is the coordinator's
        log=QUIET,
    )
    peer.start()
    return peer


def kill_link_and_peer(worker):
    """The test25 crash: the connection dies and the peer never comes back."""
    if worker._coordinator_connection is not None:
        worker._coordinator_connection.close("test45: peer is gone")
    worker._stop.set()


def blink(worker, hold_rejoin=True):
    """Cut a live worker's coordinator link; optionally hold off its rejoin.

    Holding the rejoin (by blanking the address the reconnect loop dials)
    makes the blink's duration the test's choice rather than a race between
    the coordinator's EOF handling and the worker's 0.3 s reconnect poll.
    Returns the address to restore.
    """
    address = worker._coordinator_address
    if hold_rejoin:
        worker._coordinator_address = ""
    worker._coordinator_connection.close("test45: transient blink")
    return address


# --------------------------------------------------------------------- phases


def phase_blink_is_not_a_second_loss(results, directory):
    print("\n[1] the §6.5 scenario: a re-dispatched job, then its new holder blinks")
    coordinator = start_coordinator(directory, "w33p1-coordinator", grace=3.0)
    victim_runner = GatedRunner()
    survivor_runner = GatedRunner()
    victim = start_worker(directory, "w33p1-victim", victim_runner)
    survivor = start_worker(directory, "w33p1-survivor", survivor_runner)
    try:
        moved = stub_job("w33-moved", directory)
        own = stub_job("w33-own", directory)
        victim_runner.gate(moved.job_id)
        survivor_runner.gate(own.job_id)
        survivor_runner.gate(moved.job_id)

        # Place each job deterministically: only the victim is a member when
        # its job is submitted, only then does the survivor join for its own.
        victim.join(coordinator.address)
        coordinator.submit(moved)
        results.check(
            "the victim starts the job that will move",
            victim_runner.started(moved.job_id).wait(timeout=15),
            "owner=%s" % coordinator._job_owner.get(moved.job_id),
        )
        survivor.join(coordinator.address)
        coordinator.submit(own)
        results.check(
            "the survivor starts its own job (and stays busy)",
            survivor_runner.started(own.job_id).wait(timeout=15),
            "owner=%s" % coordinator._job_owner.get(own.job_id),
        )

        kill_link_and_peer(victim)
        victim_runner.release(moved.job_id)  # let the dead peer's thread tidy up
        redispatched = coordinator.wait_for(
            lambda peer: bool(events_for(peer, "job-redispatched", job_id=moved.job_id)),
            timeout=25,
        )
        queued_at_survivor = coordinator.wait_for(
            lambda peer: peer._job_owner.get(moved.job_id) == survivor.peer_id
            and peer._job_state.get(moved.job_id) == "queued",
            timeout=15,
        )
        results.check(
            "the dead victim's job is re-dispatched once (attempt 2, mid-job)",
            redispatched
            and attempt_of(coordinator, moved.job_id) == 2
            and "mid-job" in events_for(coordinator, "job-redispatched", job_id=moved.job_id)[-1].get("detail", ""),
            "attempt=%s events=%s"
            % (attempt_of(coordinator, moved.job_id), [e.get("detail") for e in events_for(coordinator, "job-redispatched", job_id=moved.job_id)]),
        )
        results.check(
            "and queues behind the survivor's own running job",
            queued_at_survivor
            and survivor.wait_for(lambda peer: any(job.job_id == moved.job_id for job in peer._queue), timeout=10),
            "state=%s survivor queue=%s"
            % (coordinator._job_state.get(moved.job_id), [job.job_id for job in survivor._queue]),
        )

        # ---- the blink: exactly what the SIGKILL did to the survivor ----
        address = blink(survivor, hold_rejoin=True)
        suspect_seen = coordinator.wait_for(
            lambda peer: bool(events_for(peer, "member-suspect", peer_id=survivor.peer_id)),
            timeout=10,
        )
        results.check(
            "a severed link makes the survivor suspect, not lost",
            suspect_seen and not events_for(coordinator, "member-lost", peer_id=survivor.peer_id),
            "suspect=%s lost=%s"
            % (len(events_for(coordinator, "member-suspect", peer_id=survivor.peer_id)),
               len(events_for(coordinator, "member-lost", peer_id=survivor.peer_id))),
        )
        results.check(
            "the worker names its half of the blink coordinator-lost",
            survivor.wait_for(lambda peer: bool(peer.events("coordinator-lost")), timeout=10),
        )
        results.check(
            "no attempt is charged while the holder is only suspect",
            attempt_of(coordinator, moved.job_id) == 2
            and attempt_of(coordinator, own.job_id) == 1
            and len(events_for(coordinator, "job-redispatched", job_id=moved.job_id)) == 1
            and not events_for(coordinator, "job-redispatched", job_id=own.job_id),
            "attempts moved=%s own=%s" % (attempt_of(coordinator, moved.job_id), attempt_of(coordinator, own.job_id)),
        )
        results.check(
            "nothing the suspect holds goes terminal or changes owner",
            moved.job_id not in coordinator._results
            and own.job_id not in coordinator._results
            and coordinator._job_owner.get(moved.job_id) == survivor.peer_id
            and coordinator._job_owner.get(own.job_id) == survivor.peer_id
            and coordinator.summary()["live_leases"] >= 2,
            "states=%s deferred=%s"
            % (coordinator.summary()["job_states"], coordinator.summary().get("deferred_losses")),
        )
        # Still true a moment later: the deferral is a window, not a pause in
        # this thread (0.8 s is four times the recorded 0.2 s blink).
        time.sleep(0.8)
        results.check(
            "and it is still true 0.8s into the blink (grace is 3s)",
            not events_for(coordinator, "member-lost", peer_id=survivor.peer_id)
            and moved.job_id not in coordinator._results
            and attempt_of(coordinator, moved.job_id) == 2,
        )

        # ---- the rejoin cancels the loss for free ----
        survivor._coordinator_address = address
        rejoined = coordinator.wait_for(
            lambda peer: bool(events_for(peer, "member-rejoined", peer_id=survivor.peer_id)),
            timeout=15,
        )
        results.check(
            "rejoining inside the grace cancels the loss",
            rejoined
            and survivor.peer_id in coordinator.members()
            and not coordinator.summary().get("deferred_losses")
            and not events_for(coordinator, "member-lost", peer_id=survivor.peer_id)
            and attempt_of(coordinator, moved.job_id) == 2
            and attempt_of(coordinator, own.job_id) == 1,
            "members=%s" % sorted(coordinator.members()),
        )

        survivor_runner.release(own.job_id)
        survivor_runner.release(moved.job_id)
        finished = coordinator.wait_for_terminal([own.job_id, moved.job_id], timeout=30)
        results.check(
            "both jobs then run once, on the survivor, to a real success",
            finished
            and (coordinator.outcome(own.job_id) or {}).get("status") == protocol.STATUS_OK
            and (coordinator.outcome(moved.job_id) or {}).get("status") == protocol.STATUS_OK
            and survivor_runner.calls == [own.job_id, moved.job_id]
            and len(events_for(coordinator, "job-result", job_id=moved.job_id)) == 1
            and len(events_for(coordinator, "job-redispatched", job_id=moved.job_id)) == 1
            and coordinator.summary()["live_leases"] == 0,
            "survivor calls=%s" % survivor_runner.calls,
        )
    finally:
        victim_runner.release_all()
        survivor_runner.release_all()
        coordinator.shutdown(timeout=2.0)
        survivor.shutdown(timeout=1.0)
        victim.shutdown(timeout=1.0)


def phase_gone_past_the_grace(results, directory):
    print("\n[2] gone past the grace: one loss, one attempt, recovered; a live blink; a goodbye")
    coordinator = start_coordinator(directory, "w33p2-coordinator", grace=1.2)
    runner_a = GatedRunner()
    runner_b = GatedRunner()
    worker_a = start_worker(directory, "w33p2-a", runner_a)
    worker_b = start_worker(directory, "w33p2-b", runner_b)
    try:
        doomed = stub_job("w33-doomed", directory)
        runner_a.gate(doomed.job_id)
        worker_a.join(coordinator.address)
        coordinator.submit(doomed)
        runner_a.started(doomed.job_id).wait(timeout=15)
        worker_b.join(coordinator.address)
        coordinator.wait_for(lambda peer: worker_b.peer_id in peer.members(), timeout=10)

        kill_link_and_peer(worker_a)
        runner_a.release(doomed.job_id)
        suspect_seen = coordinator.wait_for(
            lambda peer: bool(events_for(peer, "member-suspect", peer_id=worker_a.peer_id)),
            timeout=10,
        )
        results.check(
            "a peer that is never coming back is suspect first",
            suspect_seen
            and not events_for(coordinator, "member-lost", peer_id=worker_a.peer_id)
            and attempt_of(coordinator, doomed.job_id) == 1,
            "attempt=%s" % attempt_of(coordinator, doomed.job_id),
        )
        resolved = coordinator.wait_for(
            lambda peer: bool(events_for(peer, "member-lost", peer_id=worker_a.peer_id))
            and bool(events_for(peer, "job-redispatched", job_id=doomed.job_id)),
            timeout=20,
        )
        finished = coordinator.wait_for_terminal([doomed.job_id], timeout=20)
        results.check(
            "past the grace it resolves once: member-lost, attempt 2, recovered",
            resolved
            and finished
            and len(events_for(coordinator, "member-lost", peer_id=worker_a.peer_id)) == 1
            and len(events_for(coordinator, "job-redispatched", job_id=doomed.job_id)) == 1
            and attempt_of(coordinator, doomed.job_id) == 2
            and (coordinator.outcome(doomed.job_id) or {}).get("status") == protocol.STATUS_OK
            and runner_b.calls == [doomed.job_id],
            "status=%s calls-b=%s" % ((coordinator.outcome(doomed.job_id) or {}).get("status"), runner_b.calls),
        )

        # An unassisted blink: close the link and let the worker's own
        # reconnect loop do what it does in production. Either coordinator
        # healing path is honest here -- suspect-then-rejoined, or the older
        # stale-loss-ignored when the rejoin lands first -- but no loss of
        # worker-b and no charged attempt may come out of it.
        live = stub_job("w33-live", directory)
        runner_b.gate(live.job_id)
        coordinator.submit(live)
        runner_b.started(live.job_id).wait(timeout=15)
        blink(worker_b, hold_rejoin=False)
        healed = coordinator.wait_for(
            lambda peer: worker_b.peer_id in peer.members()
            and any(entry.get("event") == "rejoined" for entry in worker_b.events()),
            timeout=15,
        )
        runner_b.release(live.job_id)
        live_done = coordinator.wait_for_terminal([live.job_id], timeout=20)
        results.check(
            "an unassisted blink rejoins and costs no attempt",
            healed
            and live_done
            and not events_for(coordinator, "member-lost", peer_id=worker_b.peer_id)
            and not events_for(coordinator, "job-redispatched", job_id=live.job_id)
            and attempt_of(coordinator, live.job_id) == 1
            and (coordinator.outcome(live.job_id) or {}).get("status") == protocol.STATUS_OK,
            "healer events=%s"
            % ([e["event"] for e in coordinator.events() if e.get("peer_id") == worker_b.peer_id][-4:],),
        )

        # A goodbye is a peer saying it is leaving: a loss at once, never a
        # suspect. (Worker-b is idle now, so nothing is orphaned by it.)
        suspects_before = len(events_for(coordinator, "member-suspect", peer_id=worker_b.peer_id))
        worker_b.shutdown(timeout=1.0)
        results.check(
            "a goodbye is an immediate loss, not a suspect",
            coordinator.wait_for(
                lambda peer: bool(events_for(peer, "member-lost", peer_id=worker_b.peer_id)),
                timeout=10,
            )
            and "goodbye" in [e.get("detail") for e in events_for(coordinator, "member-lost", peer_id=worker_b.peer_id)]
            and len(events_for(coordinator, "member-suspect", peer_id=worker_b.peer_id)) == suspects_before,
            "details=%s" % [e.get("detail") for e in events_for(coordinator, "member-lost", peer_id=worker_b.peer_id)],
        )
    finally:
        runner_a.release_all()
        runner_b.release_all()
        coordinator.shutdown(timeout=2.0)
        worker_a.shutdown(timeout=1.0)
        worker_b.shutdown(timeout=1.0)


def phase_unrecoverable_is_reported(results, directory):
    print("\n[3] deferred is not forgiven: a job with nowhere to go is reported, not lost")
    coordinator = start_coordinator(directory, "w33p3-coordinator", grace=1.0)
    coordinator.redispatch_on_crash = False  # the test owns this, as in test25
    runner = GatedRunner()
    worker = start_worker(directory, "w33p3-only", runner)
    try:
        lost = stub_job("w33-lost", directory)
        runner.gate(lost.job_id)
        worker.join(coordinator.address)
        coordinator.submit(lost)
        runner.started(lost.job_id).wait(timeout=15)

        kill_link_and_peer(worker)
        runner.release(lost.job_id)
        suspect_seen = coordinator.wait_for(
            lambda peer: bool(events_for(peer, "member-suspect", peer_id=worker.peer_id)),
            timeout=10,
        )
        not_yet_terminal = lost.job_id not in coordinator._results
        reported = coordinator.wait_for(lambda peer: lost.job_id in peer._results, timeout=20)
        record = coordinator.outcome(lost.job_id) or {}
        results.check(
            "suspect first, then a terminal worker-lost -- never silence",
            suspect_seen
            and not_yet_terminal
            and reported
            and record.get("status") == protocol.STATUS_FAILED
            and record.get("reason") == "worker-lost"
            and record.get("provisional") is True
            and coordinator._job_state.get(lost.job_id) == "failed"
            and len(events_for(coordinator, "member-lost", peer_id=worker.peer_id)) == 1
            and not events_for(coordinator, "job-redispatched", job_id=lost.job_id),
            "status=%s reason=%s" % (record.get("status"), record.get("reason")),
        )
    finally:
        runner.release_all()
        coordinator.shutdown(timeout=2.0)
        worker.shutdown(timeout=1.0)


def phase_zero_grace_is_the_old_behaviour(results, directory):
    print("\n[4] reconnect_grace=0 (constructor) restores immediate loss accounting")
    coordinator = start_coordinator(directory, "w33p4-coordinator", reconnect_grace=0)
    runner_a = GatedRunner()
    runner_b = GatedRunner()
    worker_a = start_worker(directory, "w33p4-a", runner_a)
    worker_b = start_worker(directory, "w33p4-b", runner_b)
    try:
        job = stub_job("w33-zero", directory)
        runner_a.gate(job.job_id)
        worker_a.join(coordinator.address)
        coordinator.submit(job)
        runner_a.started(job.job_id).wait(timeout=15)
        worker_b.join(coordinator.address)
        coordinator.wait_for(lambda peer: worker_b.peer_id in peer.members(), timeout=10)

        kill_link_and_peer(worker_a)
        runner_a.release(job.job_id)
        finished = coordinator.wait_for_terminal([job.job_id], timeout=25)
        results.check(
            "with no grace the loss charges one attempt and the job recovers",
            finished
            and not events_for(coordinator, "member-suspect", peer_id=worker_a.peer_id)
            and len(events_for(coordinator, "member-lost", peer_id=worker_a.peer_id)) == 1
            and len(events_for(coordinator, "job-redispatched", job_id=job.job_id)) == 1
            and attempt_of(coordinator, job.job_id) == 2
            and (coordinator.outcome(job.job_id) or {}).get("status") == protocol.STATUS_OK
            and runner_b.calls == [job.job_id],
            "calls-b=%s" % runner_b.calls,
        )
    finally:
        runner_a.release_all()
        runner_b.release_all()
        coordinator.shutdown(timeout=2.0)
        worker_a.shutdown(timeout=1.0)
        worker_b.shutdown(timeout=1.0)


def phase_watchdog_does_not_charge_a_suspect(results, directory):
    print("\n[5] the offer watchdog does not charge an attempt against a suspect peer")
    coordinator = start_coordinator(directory, "w33p5-coordinator", grace=3.0)
    coordinator.offer_ack_timeout = 0.7  # only this phase needs the short fuse
    runner = GatedRunner()
    worker = start_worker(directory, "w33p5-worker", runner)
    try:
        job = stub_job("w33-swallowed", directory)
        worker.join(coordinator.address)
        coordinator.wait_for(lambda peer: worker.peer_id in peer.members(), timeout=10)

        # Swallow the first offer (test25's stranded-offer pattern): the job
        # sits `dispatched` and unacknowledged, which is what the watchdog
        # normally charges as an attempt after `offer_ack_timeout`.
        dropped = {"count": 0}
        real_send = coordinator._send

        def dropping_send(peer_id, message):
            if (
                message.get("kind") == protocol.JOB_OFFER
                and (message.get("job") or {}).get("job_id") == job.job_id
                and dropped["count"] == 0
            ):
                dropped["count"] = 1
                return True
            return real_send(peer_id, message)

        coordinator._send = dropping_send
        coordinator.submit(job)
        dispatched = coordinator.wait_for(
            lambda peer: peer._job_state.get(job.job_id) == "dispatched"
            and peer._job_owner.get(job.job_id) == worker.peer_id,
            timeout=10,
        )
        results.check("the swallowed offer leaves the job dispatched to the worker", dispatched and dropped["count"] == 1)

        address = blink(worker, hold_rejoin=True)
        coordinator.wait_for(
            lambda peer: bool(events_for(peer, "member-suspect", peer_id=worker.peer_id)),
            timeout=10,
        )
        # Outlast the watchdog's fuse while staying inside the grace.
        time.sleep(1.4)
        results.check(
            "the watchdog stays its hand while the owner is suspect",
            attempt_of(coordinator, job.job_id) == 1
            and coordinator._job_state.get(job.job_id) == "dispatched"
            and not events_for(coordinator, "job-redispatched", job_id=job.job_id),
            "attempt=%s state=%s" % (attempt_of(coordinator, job.job_id), coordinator._job_state.get(job.job_id)),
        )

        coordinator._send = real_send
        worker._coordinator_address = address
        coordinator.wait_for(
            lambda peer: bool(events_for(peer, "member-rejoined", peer_id=worker.peer_id)),
            timeout=15,
        )
        finished = coordinator.wait_for_terminal([job.job_id], timeout=25)
        redispatched = events_for(coordinator, "job-redispatched", job_id=job.job_id)
        results.check(
            "once the peer is back, the unanswered offer costs exactly one attempt",
            finished
            and len(redispatched) == 1
            and "no answer" in redispatched[-1].get("detail", "")
            and attempt_of(coordinator, job.job_id) == 2
            and runner.calls == [job.job_id]
            and (coordinator.outcome(job.job_id) or {}).get("status") == protocol.STATUS_OK,
            "redispatched=%s" % [e.get("detail") for e in redispatched],
        )
    finally:
        runner.release_all()
        coordinator.shutdown(timeout=2.0)
        worker.shutdown(timeout=1.0)


# ------------------------------------------------------------------------ main


def main():
    print("=== TEST 45: W33 mesh reconnect attempt accounting ===")
    started = time.time()
    results = Results()
    directory = MeshModule.default_cert_dir()
    IdentityModule.MeshPki.create(directory)
    phases = (
        phase_blink_is_not_a_second_loss,
        phase_gone_past_the_grace,
        phase_unrecoverable_is_reported,
        phase_zero_grace_is_the_old_behaviour,
        phase_watchdog_does_not_charge_a_suspect,
    )
    timings = []
    try:
        wanted = os.environ.get("T45_PHASES", "12345")  # a subset while debugging
        for number, phase in enumerate(phases, start=1):
            if str(number) not in wanted:
                continue
            phase_started = time.time()
            phase(results, directory)
            timings.append((phase.__name__, round(time.time() - phase_started, 1)))
    finally:
        shutil.rmtree(directory, ignore_errors=True)
        print("\n  artifacts: %s (removed)" % directory)
    elapsed = time.time() - started
    print("\n  phase wall clock: %s" % ("  ".join("%s=%.1fs" % item for item in timings)))
    print("\n=== TEST 45 COMPLETE: %d passed, %d failed in %.1fs ===" % (results.passed, results.failed, elapsed))
    return 1 if results.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
