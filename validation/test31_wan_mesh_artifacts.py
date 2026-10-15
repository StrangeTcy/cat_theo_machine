"""Test 31 -- W20: the mesh beyond one filesystem (a laptop and a Colab notebook).

Run:
    PYTHONPATH=/home/user .venv/bin/python -u validation/test31_wan_mesh_artifacts.py

What this suite is for
----------------------
`delegation/W20-wan-mesh.md`. The W2 mesh assumed one box: every peer could open
every path a job named, every peer could be dialled, and every certificate named
127.0.0.1. A worker in a notebook breaks all three. W20 adds, without touching the
job semantics or the kernel:

* **identity-based verification** (`verify="identity"`): the CA pin is unchanged,
  but the name checked is the certificate's common name rather than the address
  dialled, because a tunnel endpoint is not something a leaf can be issued for;
* **artifacts over the wire** (`artifacts="wire"`): job inputs are fetched from
  the coordinator and results pushed back, in digest-checked chunks on the link
  the worker opened, and the coordinator never takes a path from the wire;
* **no-inbound workers** (`inbound=False`): a peer that only dials out still
  joins, serves, and steals -- it simply cannot be stolen from, and peers that
  cannot be reached are backed off rather than hammered.

Everything here runs on loopback with real sockets and real frames; the only
thing a WAN adds is latency. Phases 1-3 use stub runners (no machine boot);
phase 4 drives the real CLI end to end -- bundle issued, coordinator bound to
0.0.0.0 and advertising another address, a worker started from the bundle alone
-- and compares the search result that came back over the wire with a
single-process run of the same job. Phase 4 costs two pack boots (~20 s each,
concurrent) plus the search.

The suite is guarded with `if __name__ == "__main__":` because the snapshot
codec's registry restore uses `spawn`.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import time

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_PARENT = os.path.dirname(PACKAGE_ROOT)
if PACKAGE_PARENT not in sys.path:
    sys.path.insert(0, PACKAGE_PARENT)

from cat_theo_machine import mesh as MeshModule
from cat_theo_machine.networking import artifacts as Artifacts
from cat_theo_machine.networking import identity as IdentityModule
from cat_theo_machine.networking import jobs as MeshJobs
from cat_theo_machine.networking import protocol
from cat_theo_machine.networking.peer import MeshPeer

QUIET = lambda text: None  # noqa: E731 -- peers log nothing; the ledger is the record


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def check(self, label, condition, detail=""):
        if condition:
            self.passed += 1
            print("  PASS  %-62s %s" % (label, detail))
        else:
            self.failed += 1
            print("  FAIL  %-62s %s" % (label, detail))
        return bool(condition)

    def note(self, text):
        print("  note  %s" % text)


# ------------------------------------------------------------------ stub runner


class WireStubRunner:
    """A deterministic 'search' that produces a result of a chosen size.

    It records the job it was handed -- the *localised* job in wire mode -- so the
    suite can check that a worker only ever touched paths under its own artifact
    root, and that the input it read is byte-for-byte the coordinator's file.
    """

    def __init__(self, size=64, modes=("dfs", "bfs"), hold=None, fuse=20.0, phantom=False):
        self.supported_modes = tuple(modes)
        self.size = size
        self.booted = True
        self.calls = []
        self.hold = hold
        self.fuse = fuse
        self.phantom = phantom  # report success without writing anything

    def supports(self, mode):
        return mode in self.supported_modes

    def run(self, job):
        unit_path = (job.manifest or {}).get("unit_path", "")
        unit_sha = Artifacts.sha256_of(unit_path) if unit_path and os.path.exists(unit_path) else ""
        self.calls.append({"job_id": job.job_id, "result_ref": job.result_ref, "unit_path": unit_path, "unit_sha256": unit_sha})
        hold = self.hold
        self.hold = None
        if hold is not None:
            deadline = time.time() + self.fuse
            while hold() and time.time() < deadline:
                time.sleep(0.05)
        if not self.phantom:
            os.makedirs(os.path.dirname(os.path.abspath(job.result_ref)) or ".", exist_ok=True)
            with open(job.result_ref, "wb") as handle:
                handle.write(os.urandom(self.size))
            protocol.write_manifest_sidecar(job.manifest, job.result_ref)
        return MeshJobs.JobOutcome(
            job.job_id,
            protocol.STATUS_OK,
            0,
            job.result_ref,
            job.source_digest,
            elapsed_seconds=0.01,
            artifact_bytes=0 if self.phantom else self.size,
        )


def _write_random(path, size):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(os.urandom(size))
    return path


def _dump_threads(results, why):
    """Where every thread is, when a wait that should be instant is not."""
    import faulthandler

    results.note("thread dump: %s" % why)
    sys.stdout.flush()
    faulthandler.dump_traceback(file=sys.stdout, all_threads=True)
    sys.stdout.flush()


def _events(peer, name, **match):
    return [
        event
        for event in peer.events(name)
        if all(event.get(key) == value for key, value in match.items())
    ]


def _detail_number(detail, suffix):
    """Pull `N` out of a ledger detail like '... (N chunks)'."""
    words = detail.replace("(", " ").replace(")", " ").replace(",", " ").split()
    for index, word in enumerate(words):
        if word == suffix and index > 0 and words[index - 1].isdigit():
            return int(words[index - 1])
    return -1


# ------------------------------------------------- phase one: identity verification


def phase_identity(results, pki, directory):
    print("\n[1] verification by identity: the CA pin stays, the hostname check goes")
    # The coordinator's leaf names only `localhost`; every worker here dials
    # 127.0.0.1, which is exactly the tunnel situation: a valid certificate for a
    # name that is not the address in front of you.
    coordinator_identity = MeshModule.issue_identity(directory, "coordinator", pki, sans=("localhost",))
    coordinator = MeshPeer(coordinator_identity, role=MeshPeer.ROLE_COORDINATOR, log=QUIET, advertise="tunnel.invalid:7443")
    coordinator.start("127.0.0.1", 0)
    worker_identity = MeshModule.issue_identity(directory, "worker-h", pki)

    def attempt(identity, label, **kwargs):
        peer = MeshPeer(identity, role=MeshPeer.ROLE_WORKER, runner=WireStubRunner(), log=QUIET, inbound=False, **kwargs)
        peer.start()
        error = None
        try:
            peer.join(coordinator.address, timeout=10)
        except (ssl.SSLError, OSError, RuntimeError) as caught:
            error = caught
        return peer, error

    peer, error = attempt(worker_identity, "hostname", verify=protocol.VERIFY_HOSTNAME)
    results.check(
        "hostname mode refuses a certificate that does not name the address dialled",
        isinstance(error, ssl.SSLCertVerificationError),
        error.__class__.__name__ if error else "joined",
    )
    peer.shutdown(timeout=1.0)

    peer, error = attempt(worker_identity, "identity", verify=protocol.VERIFY_IDENTITY, expect_coordinator="coordinator")
    joined = error is None and bool(peer.events("joined"))
    results.check("identity mode admits the same certificate under the expected name", joined, repr(error) if error else "joined")
    if joined:
        coordinator.wait_for(lambda c: any(peer.peer_id == pid for pid in c.members()), timeout=5)
        record = coordinator.members().get(peer.peer_id, {})
        results.check(
            "a no-inbound worker is recorded as unreachable (empty address)",
            record.get("address", "x") == "" and record.get("reachable") is False,
            "address=%r reachable=%r" % (record.get("address"), record.get("reachable")),
        )
        results.check(
            "the coordinator's member record names the peer by its certificate",
            record.get("common_name") == "worker-h",
            "common_name=%r" % record.get("common_name"),
        )
        results.check(
            "the worker learns the coordinator's advertised address, not the bound one",
            peer.members().get(peer._coordinator_id, {}).get("address") == "tunnel.invalid:7443",
            "%r" % peer.members().get(peer._coordinator_id, {}).get("address"),
        )
        results.check("the worker says so itself (inbound-disabled event)", bool(peer.events("inbound-disabled")))
    peer.shutdown(timeout=1.0)

    peer, error = attempt(worker_identity, "wrong-name", verify=protocol.VERIFY_IDENTITY, expect_coordinator="not-the-coordinator")
    results.check(
        "identity mode refuses a valid certificate under the wrong name",
        isinstance(error, RuntimeError) and "identity mismatch" in str(error),
        repr(error)[:90] if error else "joined",
    )
    results.check(
        "the mismatch is a ledger event naming both sides",
        any("expected not-the-coordinator" in event["detail"] and "coordinator" in event["detail"] for event in peer.events("identity-mismatch")),
        "; ".join(event["detail"] for event in peer.events("identity-mismatch")),
    )
    peer.shutdown(timeout=1.0)

    # The CA pin is not relaxed by identity mode: a leaf from another CA, and a
    # client that trusts another CA, both still fail the handshake.
    rogue_name, rogue_key, rogue_ca_path = pki.rogue_ca()
    rogue_leaf = pki.issue_from((rogue_name, rogue_key, rogue_ca_path), "coordinator", rogue_name, rogue_ca_path, sans=("127.0.0.1",), basename="rogue-coordinator")
    peer, error = attempt(rogue_leaf, "rogue", verify=protocol.VERIFY_IDENTITY, expect_coordinator="coordinator")
    results.check(
        "identity mode still rejects a leaf from a CA the mesh does not trust",
        error is not None and not peer.events("joined"),
        error.__class__.__name__ if error else "joined",
    )
    peer.shutdown(timeout=1.0)
    wrong_trust = IdentityModule.MeshIdentity("worker-h", worker_identity.cert_path, worker_identity.key_path, rogue_ca_path)
    peer, error = attempt(wrong_trust, "wrong-trust", verify=protocol.VERIFY_IDENTITY, expect_coordinator="coordinator")
    results.check(
        "identity mode still rejects a coordinator the worker's CA did not sign",
        isinstance(error, ssl.SSLError) and not peer.events("joined"),
        error.__class__.__name__ if error else "joined",
    )
    peer.shutdown(timeout=1.0)
    results.check(
        "refused handshakes are on the coordinator's ledger",
        len(coordinator.events("handshake-refused")) >= 1,
        "%d handshake-refused" % len(coordinator.events("handshake-refused")),
    )
    coordinator.shutdown(timeout=1.0)


# --------------------------------------------- phase two: artifacts over the wire


def phase_artifacts(results, directory):
    print("\n[2] artifacts over the wire: inputs fetched, results pushed, nothing taken on trust")
    home = os.path.join(directory, "home")          # the coordinator's filesystem
    remote = os.path.join(directory, "remote")      # the worker's: a different root
    os.makedirs(home, exist_ok=True)
    os.makedirs(remote, exist_ok=True)
    coordinator = MeshPeer(MeshModule.ensure_identity(directory, "wire-coordinator"), role=MeshPeer.ROLE_COORDINATOR, log=QUIET, artifacts=protocol.ARTIFACTS_WIRE)
    coordinator.start("127.0.0.1", 0)
    ten_mib = 10 * 1024 * 1024
    runner = WireStubRunner(size=ten_mib)
    worker = MeshPeer(
        MeshModule.ensure_identity(directory, "wire-worker"),
        role=MeshPeer.ROLE_WORKER,
        runner=runner,
        log=QUIET,
        artifacts=protocol.ARTIFACTS_WIRE,
        artifact_dir=remote,
        inbound=False,
        verify=protocol.VERIFY_IDENTITY,
        expect_coordinator="wire-coordinator",
    )
    worker.start()
    worker.join(coordinator.address)
    coordinator.wait_for(lambda c: len(c.members()) == 1, timeout=5)

    unit = _write_random(os.path.join(home, "inputs", "unit-000.json"), 4_500_000)
    unit_sha = Artifacts.sha256_of(unit)
    manifest = {"unit_path": unit, "start_text": "stub", "goal_text": "stub"}
    big = protocol.Job("big-1", "dfs", manifest, os.path.join(home, "results", "big-1.json"))
    coordinator.submit(big)
    done = coordinator.wait_for_terminal([big.job_id], timeout=60)
    outcome = coordinator.outcome(big.job_id) or {}
    if not results.check("a job with a 4.5 MB input and a 10 MiB result completes over the wire", done and outcome.get("status") == protocol.STATUS_OK, "status=%s reason=%s" % (outcome.get("status"), outcome.get("reason"))):
        for who, peer in (("coordinator", coordinator), ("worker", worker)):
            for event in peer.events():
                results.note("%s %s %s %s %s" % (who, event["event"], event.get("job_id"), event.get("peer_id"), (event.get("detail") or "")[:80]))
    results.check(
        "the result landed at the coordinator's own result_ref, bytes intact",
        os.path.exists(big.result_ref) and os.path.getsize(big.result_ref) == ten_mib and Artifacts.sha256_of(big.result_ref) == outcome.get("artifact_sha256"),
        "size=%s sha=%s" % (os.path.getsize(big.result_ref) if os.path.exists(big.result_ref) else None, (outcome.get("artifact_sha256") or "")[:12]),
    )
    sidecar = Artifacts.sidecar_of(big.result_ref)
    sidecar_ok = False
    if os.path.exists(sidecar):
        with open(sidecar, encoding="utf-8") as handle:
            sidecar_ok = json.load(handle) == manifest
    results.check("the manifest sidecar travelled with it", sidecar_ok, sidecar)
    call = runner.calls[0] if runner.calls else {}
    results.check(
        "the worker read the input from under its own root, byte-identical",
        call.get("unit_path", "").startswith(remote + os.sep) and call.get("unit_sha256") == unit_sha,
        call.get("unit_path", "-"),
    )
    results.check(
        "the worker wrote its result under its own root, not at the coordinator's path",
        call.get("result_ref", "").startswith(remote + os.sep) and call.get("result_ref") != big.result_ref,
        call.get("result_ref", "-"),
    )
    served = _events(coordinator, "artifact-served", job_id=big.job_id)
    incoming = [event for event in _events(coordinator, "artifact-incoming", job_id=big.job_id) if big.result_ref + " ->" in event["detail"]]
    results.check(
        "the input went out in more than one chunk (%d MiB chunks)" % (Artifacts.CHUNK_BYTES // (1024 * 1024)),
        served and _detail_number(served[0]["detail"], "chunks") == -(-4_500_000 // Artifacts.CHUNK_BYTES),
        served[0]["detail"] if served else "no artifact-served event",
    )
    results.check(
        "the result came back in %d chunks" % -(-ten_mib // Artifacts.CHUNK_BYTES),
        incoming and _detail_number(incoming[0]["detail"], "chunks") == -(-ten_mib // Artifacts.CHUNK_BYTES),
        incoming[0]["detail"] if incoming else "no artifact-incoming event",
    )
    results.check(
        "the worker's ledger tells the story: requested, received, sent",
        all(_events(worker, name, job_id=big.job_id) or _events(worker, name) for name in ("artifact-fetch-requested", "artifact-received", "artifact-sent")),
        ", ".join(sorted({event["event"] for event in worker.events() if event["event"].startswith("artifact")})),
    )

    # The same input again is not fetched twice.
    runner.size = 1024
    again = protocol.Job("big-2", "dfs", manifest, os.path.join(home, "results", "big-2.json"))
    coordinator.submit(again)
    coordinator.wait_for_terminal([again.job_id], timeout=30)
    results.check(
        "a second job naming the same input reuses the local copy",
        (coordinator.outcome(again.job_id) or {}).get("status") == protocol.STATUS_OK and bool(_events(worker, "artifact-cached", job_id=again.job_id)),
        "artifact-cached=%d" % len(_events(worker, "artifact-cached", job_id=again.job_id)),
    )

    # An input the coordinator does not have: a terminal failure with the reason, not a hang.
    ghost = protocol.Job("no-input", "dfs", {"unit_path": os.path.join(home, "inputs", "never-written.json"), "start_text": "s", "goal_text": "g"}, os.path.join(home, "results", "no-input.json"))
    started = time.time()
    coordinator.submit(ghost)
    coordinator.wait_for_terminal([ghost.job_id], timeout=30)
    ghost_outcome = coordinator.outcome(ghost.job_id) or {}
    results.check(
        "a missing input fails the job promptly with its reason",
        ghost_outcome.get("status") == protocol.STATUS_FAILED and ghost_outcome.get("reason", "").startswith("input-missing:") and time.time() - started < 15,
        "status=%s reason=%s after %.1fs" % (ghost_outcome.get("status"), ghost_outcome.get("reason"), time.time() - started),
    )
    results.check(
        "the coordinator refused the fetch and said why",
        any("not-on-disk" in event["detail"] for event in _events(coordinator, "artifact-fetch-refused", job_id=ghost.job_id)),
    )

    # Forgery 1: ask the coordinator for a file that is not an input of any job.
    ca_key = os.path.join(directory, "ca.key")
    link = worker._coordinator_connection
    link.send(protocol.message(protocol.ARTIFACT_FETCH, job_id=big.job_id, ref=ca_key, peer_id=worker.peer_id))
    link.send(protocol.message(protocol.ARTIFACT_FETCH, job_id="no-such-job", ref=unit, peer_id=worker.peer_id))
    worker.wait_for(lambda w: len(w.events("artifact-missing")) >= 3, timeout=10)
    refused = coordinator.events("artifact-fetch-refused")
    results.check(
        "a fetch for a path that is not a job input is refused (the CA key stays home)",
        any(event["detail"].startswith(ca_key) and "ref-not-an-input-of-the-job" in event["detail"] for event in refused)
        and not os.path.exists(Artifacts.local_path_for(ca_key, remote)),
        "; ".join(event["detail"].split(": ")[-1] for event in refused),
    )
    results.check(
        "a fetch under an unknown job id is refused",
        any("unknown-job" in event["detail"] for event in refused),
    )

    # Forgery 2: push a file to a path the coordinator never named.
    forged_target = os.path.join(home, "results", "forged.bin")
    local_blob = _write_random(os.path.join(remote, "blob.bin"), 4096)
    Artifacts.send_file(link, local_blob, forged_target, big.job_id, Artifacts.KIND_RESULT)
    Artifacts.send_file(link, local_blob, unit, big.job_id, Artifacts.KIND_INPUT)
    worker.wait_for(lambda w: len(w.events("artifact-refused-by-peer")) >= 2, timeout=10)
    pushed_refusals = coordinator.events("artifact-refused")
    results.check(
        "an upload to a path that is not the job's result_ref is refused and nothing is written",
        any("ref-not-the-job's-result" in event["detail"] for event in pushed_refusals) and not os.path.exists(forged_target),
        "; ".join(event["detail"].split(": ")[-1] for event in pushed_refusals),
    )
    results.check(
        "the coordinator accepts results only (an 'input' pushed at it is refused)",
        any("coordinator-accepts-results-only" in event["detail"] for event in pushed_refusals),
    )
    results.check("the worker hears each refusal", len(worker.events("artifact-refused-by-peer")) >= 2, "%d" % len(worker.events("artifact-refused-by-peer")))

    # Corruption: a transfer whose bytes do not match its declared digest never
    # becomes the result -- and the genuine upload that follows still does.
    release = threading.Event()
    runner.hold = lambda: not release.is_set()
    held = protocol.Job("held-1", "dfs", {"start_text": "s", "goal_text": "g"}, os.path.join(home, "results", "held-1.json"))
    coordinator.submit(held)
    worker.wait_for(lambda w: w._running is not None and w._running.job_id == held.job_id, timeout=10)
    data = os.urandom(1000)
    transfer_id = "forged-" + os.urandom(4).hex()
    link.send(protocol.message(protocol.ARTIFACT_BEGIN, transfer_id=transfer_id, ref=held.result_ref, job_id=held.job_id, artifact_kind=Artifacts.KIND_RESULT, size=len(data), sha256="0" * 64, chunks=1))
    link.send(protocol.message(protocol.ARTIFACT_CHUNK, transfer_id=transfer_id, index=0, data_b64=base64.b64encode(data).decode("ascii")))
    link.send(protocol.message(protocol.ARTIFACT_END, transfer_id=transfer_id))
    if not coordinator.wait_for(lambda c: bool(c.events("artifact-corrupt")), timeout=10):
        _dump_threads(results, "no artifact-corrupt event within 10 s")
    corrupt = coordinator.events("artifact-corrupt")
    leftovers = [name for name in os.listdir(os.path.join(home, "results")) if name.startswith(".incoming-")]
    results.check(
        "a digest mismatch is rejected as corrupt and leaves no file behind",
        bool(corrupt) and "does not match" in corrupt[0]["detail"] and not os.path.exists(held.result_ref) and not leftovers,
        (corrupt[0]["detail"].split(": ", 1)[-1] if corrupt else "no event") + (" leftovers=%s" % leftovers if leftovers else ""),
    )
    release.set()
    coordinator.wait_for_terminal([held.job_id], timeout=30)
    held_outcome = coordinator.outcome(held.job_id) or {}
    results.check(
        "the genuine upload after it still succeeds, digest verified",
        held_outcome.get("status") == protocol.STATUS_OK and os.path.exists(held.result_ref) and Artifacts.sha256_of(held.result_ref) == held_outcome.get("artifact_sha256"),
        "status=%s" % held_outcome.get("status"),
    )

    # A success without its artifact is not a success.
    runner.phantom = True
    phantom = protocol.Job("phantom-1", "dfs", {"start_text": "s", "goal_text": "g"}, os.path.join(home, "results", "phantom-1.json"))
    coordinator.submit(phantom)
    coordinator.wait_for_terminal([phantom.job_id], timeout=30)
    phantom_outcome = coordinator.outcome(phantom.job_id) or {}
    results.check(
        "a worker's 'ok' without a result file is downgraded to a failure",
        phantom_outcome.get("status") == protocol.STATUS_FAILED and phantom_outcome.get("reason") == "artifact-missing" and bool(_events(coordinator, "result-without-artifact", job_id=phantom.job_id)),
        "status=%s reason=%s" % (phantom_outcome.get("status"), phantom_outcome.get("reason")),
    )
    runner.phantom = False
    results.check("no transfers left open on either side", coordinator._receiver.open_count == 0 and worker._receiver.open_count == 0)
    worker.shutdown(timeout=1.0)
    coordinator.shutdown(timeout=1.0)


# ------------------------------------------- phase three: stealing without inbound


def phase_steal(results, directory):
    print("\n[3] work stealing when one peer cannot be dialled")
    home = os.path.join(directory, "steal-home")
    os.makedirs(os.path.join(home, "results"), exist_ok=True)
    unit = _write_random(os.path.join(home, "inputs", "unit-steal.json"), 200_000)
    coordinator = MeshPeer(MeshModule.ensure_identity(directory, "steal-coordinator"), role=MeshPeer.ROLE_COORDINATOR, log=QUIET, artifacts=protocol.ARTIFACTS_WIRE)
    coordinator.start("127.0.0.1", 0)
    release = threading.Event()
    victim_runner = WireStubRunner(size=256, hold=lambda: not release.is_set(), fuse=30.0)
    victim = MeshPeer(
        MeshModule.ensure_identity(directory, "victim"),
        role=MeshPeer.ROLE_WORKER,
        runner=victim_runner,
        log=QUIET,
        artifacts=protocol.ARTIFACTS_WIRE,
        artifact_dir=os.path.join(directory, "victim-root"),
        verify=protocol.VERIFY_IDENTITY,
        expect_coordinator="steal-coordinator",
    )
    victim.start("127.0.0.1", 0)
    victim.join(coordinator.address)
    coordinator.wait_for(lambda c: len(c.members()) == 1, timeout=5)
    jobs = [
        protocol.Job("steal-%d" % index, "dfs", {"unit_path": unit, "start_text": "s%d" % index, "goal_text": "g"}, os.path.join(home, "results", "steal-%d.json" % index))
        for index in (1, 2)
    ]
    for job in jobs:
        coordinator.submit(job)
    results.check(
        "one job queues behind the running one at the reachable peer",
        victim.wait_for(lambda v: v._running is not None and len(v._queue) == 1, timeout=15),
        "running=%s queued=%d" % (victim._running is not None, len(victim._queue)),
    )
    thief_runner = WireStubRunner(size=256)
    thief = MeshPeer(
        MeshModule.ensure_identity(directory, "thief"),
        role=MeshPeer.ROLE_WORKER,
        runner=thief_runner,
        log=QUIET,
        artifacts=protocol.ARTIFACTS_WIRE,
        artifact_dir=os.path.join(directory, "thief-root"),
        inbound=False,
        verify=protocol.VERIFY_IDENTITY,
        expect_coordinator="steal-coordinator",
    )
    thief.start()
    thief.join(coordinator.address)
    stolen = coordinator.wait_for(lambda c: c.summary()["steals"] >= 1, timeout=25)
    release.set()
    coordinator.wait_for_terminal([job.job_id for job in jobs], timeout=30)
    outcomes = {job.job_id: coordinator.outcome(job.job_id) or {} for job in jobs}
    results.check(
        "the no-inbound peer steals the queued job over its outbound link",
        stolen and any(record.get("stolen_from") == victim.peer_id for record in outcomes.values()),
        "stolen_from=%s" % [record.get("stolen_from") for record in outcomes.values()],
    )
    results.check(
        "both jobs end ok with their artifacts at the coordinator",
        all(record.get("status") == protocol.STATUS_OK and os.path.exists(job.result_ref) for job, record in zip(jobs, outcomes.values())),
        "%s" % {job_id: record.get("status") for job_id, record in outcomes.items()},
    )
    stolen_ids = [job_id for job_id, record in outcomes.items() if record.get("stolen_from")]
    results.check(
        "the stolen job's input was fetched by the thief and its result pushed by the thief",
        bool(stolen_ids) and bool(_events(thief, "artifact-fetch-requested", job_id=stolen_ids[0])) and bool(_events(thief, "artifact-sent", job_id=stolen_ids[0])) and thief_runner.calls and thief_runner.calls[0]["unit_sha256"] == Artifacts.sha256_of(unit),
        "thief ran %s" % [call["job_id"] for call in thief_runner.calls],
    )
    results.check(
        "nobody dialled the no-inbound peer (no address to dial)",
        not _events(victim, "steal-dialled", peer_id=thief.peer_id) and not _events(victim, "steal-unreachable", peer_id=thief.peer_id) and coordinator.members().get(thief.peer_id, {}).get("address") == "",
        "victim steal events: %s" % [event["event"] for event in victim.events() if event["event"].startswith("steal")],
    )
    results.check(
        "the thief verified the victim's identity on the steal link",
        bool(_events(thief, "steal-dialled", peer_id=victim.peer_id)) and not thief.events("identity-mismatch"),
        "steal-dialled=%d identity-mismatch=%d" % (len(_events(thief, "steal-dialled", peer_id=victim.peer_id)), len(thief.events("identity-mismatch"))),
    )

    # A peer whose advertised address answers nothing is backed off, not hammered.
    with thief._lock:
        thief._members["ghost"] = {
            "peer_id": "ghost",
            "address": "127.0.0.1:1",
            "common_name": "ghost",
            "roles": [MeshPeer.ROLE_WORKER],
            "modes": [],
            "direct": False,
            "last_seen": time.time(),
            "load": {"queued": 3, "running": 0},
        }
    first = thief.wait_for(lambda t: bool(_events(t, "steal-unreachable", peer_id="ghost")), timeout=10)
    time.sleep(3.0)
    attempts = len(_events(thief, "steal-unreachable", peer_id="ghost"))
    results.check(
        "an unreachable peer is reported once and backed off (not retried at loop speed)",
        first and 1 <= attempts <= 2,
        "%d steal-unreachable in ~3 s (a 0.05 s loop without backoff would make ~60)" % attempts,
    )
    results.check("the thief is still a member after the failed dials", thief.peer_id in coordinator.members() and not thief._stop.is_set())
    thief.shutdown(timeout=1.0)
    victim.shutdown(timeout=1.0)
    coordinator.shutdown(timeout=1.0)


# --------------------------------------------- phase four: the CLI, end to end


def _free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _semantic_equal(mesh_projection, local_projection):
    keys = ("status", "worker_stage", "plan_digest", "derivation_digest", "derivation_bytes", "proof_cost_digest")
    return all(mesh_projection.get(key) == local_projection.get(key) for key in keys)


def _terminate(process):
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=15)
    except (subprocess.TimeoutExpired, OSError):
        try:
            process.kill()
            process.wait(timeout=5)
        except OSError:
            pass


def phase_cli(results, directory):
    print("\n[4] the operator's path: bundle, tunnel-shaped coordinator, worker from the bundle alone")
    home = os.path.join(directory, "cli-home")
    home_pki = os.path.join(home, "pki")
    bundle = os.path.join(directory, "cli-bundle")
    remote = os.path.join(directory, "cli-remote")
    for path in (home, os.path.join(home, "results"), remote):
        os.makedirs(path, exist_ok=True)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = PACKAGE_PARENT
    environment["HYGE_SEARCH_WORKER_DEFER_DERIVATION"] = "1"
    main_py = os.path.join(PACKAGE_ROOT, "main.py")

    issued = subprocess.run(
        [sys.executable, main_py, "mesh", "--role", "issue", "--cert-dir", home_pki, "--cert-name", "colab-1", "--bundle-dir", bundle],
        cwd=PACKAGE_ROOT, env=environment, capture_output=True, text=True, timeout=120,
    )
    bundle_files = sorted(os.listdir(bundle)) if os.path.isdir(bundle) else []
    results.check(
        "`mesh --role issue` writes a bundle of exactly ca.crt + the leaf pair (no CA key)",
        issued.returncode == 0 and bundle_files == ["bundle.json", "ca.crt", "colab-1.crt", "colab-1.key"],
        "rc=%d files=%s" % (issued.returncode, bundle_files),
    )
    results.check(
        "the CA key is still only on the issuing side",
        os.path.exists(os.path.join(home_pki, "ca.key")) and not os.path.exists(os.path.join(bundle, "ca.key")),
    )
    key_pem = ""
    if os.path.exists(os.path.join(bundle, "colab-1.key")):
        with open(os.path.join(bundle, "colab-1.key"), encoding="utf-8") as handle:
            key_pem = handle.read()
    results.check("the bundled key is the leaf's, not the CA's", "PRIVATE KEY" in key_pem and key_pem != _read(os.path.join(home_pki, "ca.key")))

    port = _free_port()
    result_ref = os.path.join(home, "results", "wan-dfs.json")
    spec = {"job_id": "wan-dfs", "mode": "dfs", "result_ref": result_ref, "manifest": {}}
    with open(os.path.join(home, "jobs.json"), "w", encoding="utf-8") as handle:
        json.dump({"jobs": [spec]}, handle)
    reference_ref = os.path.join(home, "results", "reference-dfs.json")
    reference_answer = os.path.join(home, "reference.json")
    logs = {name: open(os.path.join(directory, "%s.log" % name), "w", encoding="utf-8") for name in ("reference", "coordinator", "worker")}
    processes = {}
    try:
        processes["reference"] = subprocess.Popen(
            [sys.executable, "-u", os.path.abspath(__file__), "--reference", json.dumps(dict(spec, reference_ref=reference_ref)), reference_answer],
            cwd=PACKAGE_ROOT, env=environment, stdout=logs["reference"], stderr=subprocess.STDOUT, text=True,
        )
        processes["coordinator"] = subprocess.Popen(
            [
                sys.executable, "-u", main_py, "mesh", "--role", "coordinator", "--cert-dir", home_pki,
                "--bind", "0.0.0.0:%d" % port, "--advertise", "127.0.0.1:%d" % port,
                "--artifacts", "wire", "--jobs", os.path.join(home, "jobs.json"), "--run-seconds", "400",
            ],
            cwd=PACKAGE_ROOT, env=environment, stdout=logs["coordinator"], stderr=subprocess.STDOUT, text=True,
        )
        deadline = time.time() + 20
        while time.time() < deadline and not os.path.exists(os.path.join(home_pki, "coordinator.json")):
            time.sleep(0.1)
        discovery = {}
        if os.path.exists(os.path.join(home_pki, "coordinator.json")):
            with open(os.path.join(home_pki, "coordinator.json"), encoding="utf-8") as handle:
                discovery = json.load(handle)
        results.check(
            "the coordinator binds 0.0.0.0 and publishes the advertised address",
            discovery.get("address") == "127.0.0.1:%d" % port and discovery.get("bound", "").startswith("0.0.0.0:") and discovery.get("artifacts") == "wire",
            "%s" % {key: discovery.get(key) for key in ("address", "bound", "artifacts")},
        )
        # The worker has: the bundle, the coordinator's address, and nothing else
        # from the coordinator's filesystem -- it is told a bogus result root on
        # purpose so a shared-path assumption anywhere would show up as a failure.
        processes["worker"] = subprocess.Popen(
            [
                sys.executable, "-u", main_py, "mesh", "--role", "worker", "--cert-dir", bundle, "--cert-name", "colab-1",
                "--coordinator", "127.0.0.1:%d" % port, "--no-inbound", "--verify", "identity", "--expect", "coordinator",
                "--artifacts", "wire", "--artifact-dir", remote, "--modes", "dfs", "--run-seconds", "380",
            ],
            cwd=PACKAGE_ROOT, env=environment, stdout=logs["worker"], stderr=subprocess.STDOUT, text=True,
        )
        try:
            rc = processes["coordinator"].wait(timeout=420)
        except subprocess.TimeoutExpired:
            rc = None
        results.check("the coordinator exits 0 once its job has a successful result", rc == 0, "rc=%s" % rc)
        ledger = {}
        if os.path.exists(os.path.join(home_pki, "ledger.json")):
            with open(os.path.join(home_pki, "ledger.json"), encoding="utf-8") as handle:
                ledger = json.load(handle)
        record = ledger.get("results", {}).get("wan-dfs", {})
        names = [event["event"] for event in ledger.get("events", [])]
        results.check(
            "the ledger shows the result arriving in frames before the job-result",
            protocol.status_is_success(record.get("status")) and "artifact-received" in names and names.index("artifact-received") < names.index("job-result") if "job-result" in names and "artifact-received" in names else False,
            "status=%s peer=%s" % (record.get("status"), record.get("peer_id")),
        )
        results.check(
            "the result file's digest is the one the worker declared",
            os.path.exists(result_ref) and record.get("artifact_sha256") and Artifacts.sha256_of(result_ref) == record.get("artifact_sha256"),
            (record.get("artifact_sha256") or "")[:12],
        )
        results.check("the worker ran under the bundled identity", str(record.get("peer_id", "")).startswith("colab-1-"), record.get("peer_id"))
        remote_files = sorted(os.listdir(remote))
        results.check(
            "the worker's artifacts live under its own root (digest-prefixed names)",
            any(name.endswith("-wan-dfs.json") for name in remote_files) and any(name.endswith(".manifest.json") for name in remote_files),
            "%s" % remote_files,
        )
        try:
            processes["reference"].wait(timeout=600)
        except subprocess.TimeoutExpired:
            results.note("reference never finished")
        reference = {}
        if os.path.exists(reference_answer):
            with open(reference_answer, encoding="utf-8") as handle:
                reference = json.load(handle).get("jobs", {}).get("wan-dfs", {})
        mesh_projection = {}
        if os.path.exists(result_ref):
            try:
                mesh_projection = MeshJobs.project_result(result_ref)
            except Exception as error:  # the comparison below reports it
                results.note("projection of the wire result failed: %r" % (error,))
        results.check(
            "the result that crossed the wire proves what a single process proves",
            bool(reference) and bool(mesh_projection) and _semantic_equal(mesh_projection, reference.get("projection", {})),
            "mesh=%s reference=%s" % (mesh_projection.get("derivation_digest", "-"), reference.get("projection", {}).get("derivation_digest", "-")),
        )
        worker_state = {}
        try:
            processes["worker"].wait(timeout=60)
        except subprocess.TimeoutExpired:
            pass
        if os.path.exists(os.path.join(bundle, "peer-colab-1.json")):
            with open(os.path.join(bundle, "peer-colab-1.json"), encoding="utf-8") as handle:
                worker_state = json.load(handle)
        worker_events = [event["event"] for event in worker_state.get("events", [])]
        results.check(
            "the worker's own ledger: no listener, joined, result sent",
            all(name in worker_events for name in ("inbound-disabled", "joined", "artifact-sent", "job-result-local")) and worker_state.get("address") == "",
            ", ".join(name for name in ("inbound-disabled", "joined", "artifact-sent", "job-result-local") if name in worker_events),
        )
    finally:
        for process in processes.values():
            _terminate(process)
        for handle in logs.values():
            handle.close()


def _read(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def run_reference(spec_json, answer_path):
    """One job, one process, one boot: the baseline the wire result is compared with."""
    spec = json.loads(spec_json)
    runner = MeshJobs.SearchJobRunner(timeout_seconds=6000)
    job = protocol.Job(spec["job_id"], spec["mode"], spec.get("manifest", {}), spec["reference_ref"])
    started = time.time()
    outcome = runner.run(job)
    projection = MeshJobs.project_result(job.result_ref)
    answer = {"jobs": {spec["job_id"]: {"status": outcome.status, "elapsed_seconds": round(time.time() - started, 2), "projection": projection}}}
    with open(answer_path, "w", encoding="utf-8") as handle:
        json.dump(answer, handle)
    print("[reference] %s %s %.1fs" % (job.job_id, outcome.status, time.time() - started), flush=True)
    return 0


# ------------------------------------------------------------------------ main


def main():
    print("=== TEST 31: W20 the mesh beyond one filesystem (identity, wire artifacts, no-inbound) ===")
    started = time.time()
    results = Results()
    directory = MeshModule.default_cert_dir()
    pki = IdentityModule.MeshPki.create(directory)
    timings = []
    try:
        wanted = os.environ.get("T31_PHASES", "1234")  # a subset while debugging, e.g. "12"
        for number, phase in enumerate((phase_identity, phase_artifacts, phase_steal, phase_cli), start=1):
            if str(number) not in wanted:
                continue
            phase_started = time.time()
            if phase is phase_identity:
                phase(results, pki, directory)
            else:
                phase(results, directory)
            timings.append((phase.__name__, round(time.time() - phase_started, 1)))
    finally:
        shutil.rmtree(directory, ignore_errors=True)
        print("\n  artifacts: %s (removed)" % directory)
    elapsed = time.time() - started
    print("\n  phase wall clock: %s" % ("  ".join("%s=%.1fs" % item for item in timings)))
    print("\n=== TEST 31 COMPLETE: %d passed, %d failed in %.1fs ===" % (results.passed, results.failed, elapsed))
    return 1 if results.failed else 0


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "--reference":
        raise SystemExit(run_reference(sys.argv[2], sys.argv[3]))
    raise SystemExit(main())
