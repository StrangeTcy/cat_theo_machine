"""mesh.py -- discovery, membership and roles for the W2 loopback mesh.

This module is the layer above `networking/`. It answers the questions a peer has
before it can talk to anyone: *who am I* (identity + PKI), *where is the
coordinator* (discovery), *am I a dispatcher or a worker* (role), and *who else is
out there* (membership, which the coordinator gossips over heartbeats).

Scope is deliberately loopback, matching the brief's hard constraints: there is no
internet peer to find, no mDNS, no rendezvous service. Discovery is a small JSON
file in the shared PKI directory -- the honest, inspectable version of "on this
box, the coordinator is at 127.0.0.1:port". Everything else (framing, leases,
stealing, liveness) lives in `networking/peer.py`.

Loopback-only enrolment, stated plainly: if a peer starts and the directory holds a
CA *key*, that peer issues its own leaf from it. That is self-service enrolment for
local tests, not a security model -- the directory is a temporary directory outside
the repository, and `networking/identity.py` refuses to put key material in the
tree. A real deployment would issue per-peer certificates and publish only the CA.

CLI (also reachable as `python main.py mesh ...`):

    coordinator:  python main.py mesh --role coordinator --cert-dir DIR --jobs jobs.json --run-seconds 120
    worker:       python main.py mesh --role worker --cert-dir DIR --run-seconds 120

The coordinator boots nothing itself; workers boot the machine once and reuse it
for every job they run.
"""

from __future__ import annotations

import json
import os
import tempfile
import time

from .networking import identity as MeshIdentityModule
from .networking import jobs as MeshJobs
from .networking import protocol
from .networking.peer import MeshPeer


def default_cert_dir():
    """A fresh temporary directory outside the repository."""
    return tempfile.mkdtemp(prefix="hyge-mesh-")


def _ca_key_path(directory):
    return os.path.join(directory, "ca.key")


def _identity_paths(directory, name):
    return os.path.join(directory, name + ".crt"), os.path.join(directory, name + ".key")


def ensure_identity(directory, name, days=7):
    """Return this peer's identity, creating the PKI or self-enrolling as needed.

    The repository guard in `networking/identity.py` runs first, so a mistyped
    directory cannot scatter private keys into the working tree.
    """
    directory = MeshIdentityModule.pki_directory_guard(directory)
    os.makedirs(directory, exist_ok=True)
    cert_path, key_path = _identity_paths(directory, name)
    ca_path = os.path.join(directory, "ca.crt")
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return MeshIdentityModule.MeshIdentity(name, cert_path, key_path, ca_path)
    if not os.path.exists(ca_path):
        pki = MeshIdentityModule.MeshPki.create(directory)
        leaf = pki.issue(name, sans=("127.0.0.1", "localhost"), days=days, basename=name)
        return leaf
    # Self-service enrolment from an existing CA (loopback test material only).
    with open(_ca_key_path(directory), "rb") as handle:
        ca_key_pem = handle.read()
    ca_key = _load_pkcs1_key(ca_key_pem)
    ca_name = MeshIdentityModule.DEFAULT_CA_NAME
    meta_path = os.path.join(directory, "ca.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as handle:
                ca_name = json.load(handle).get("common_name", ca_name)
        except (OSError, json.JSONDecodeError):
            pass
    ca_identity = MeshIdentityModule.MeshIdentity(ca_name, ca_path, _ca_key_path(directory), ca_path)
    pki = MeshIdentityModule.MeshPki(directory, ca_identity, ca_key)
    return pki.issue(name, sans=("127.0.0.1", "localhost"), days=days, basename=name)


def issue_identity(directory, name, pki, days=7, sans=("127.0.0.1", "localhost")):
    """Issue a named leaf from a PKI the caller already holds (used by the suite)."""
    return pki.issue(name, sans=sans, days=days, basename=name)


def _load_pkcs1_key(pem_bytes):
    """Parse a PKCS#1 RSAPrivateKey PEM produced by `networking/x509.py`."""
    import base64

    from .networking import x509

    body = pem_bytes.split(b"-----BEGIN RSA PRIVATE KEY-----")[1].split(b"-----END RSA PRIVATE KEY-----")[0]
    der = base64.decodebytes(body)
    values = _der_sequence_values(der)
    n, e, d, p, q = values[1], values[2], values[3], values[4], values[5]
    return x509.RsaPrivateKey(n, e, d, p, q)


def _der_sequence_values(der):
    """Read a flat SEQUENCE of INTEGERs. Only used for our own PKCS#1 keys."""
    index = 2
    if der[1] & 0x80:
        length_bytes = der[1] & 0x7F
        index = 2 + length_bytes
    values = []
    while index < len(der):
        if der[index] != 0x02:
            break
        index += 1
        length = der[index]
        index += 1
        if length & 0x80:
            length_bytes = length & 0x7F
            length = int.from_bytes(der[index : index + length_bytes], "big")
            index += length_bytes
        values.append(int.from_bytes(der[index : index + length], "big"))
        index += length
    return values


def publish_coordinator(directory, address, ca_path, extra=None):
    """Write the discovery record workers read to find the coordinator."""
    record = {"address": address, "ca_path": ca_path, "created_at": time.time()}
    if extra:
        record.update(extra)
    path = os.path.join(directory, "coordinator.json")
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(record, handle)
    os.replace(temp_path, path)
    return path


def read_coordinator(directory, timeout=30.0):
    """Wait for the discovery record to appear, then return it."""
    path = os.path.join(directory, "coordinator.json")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    return json.load(handle)
            except (OSError, json.JSONDecodeError):
                pass
        time.sleep(0.05)
    raise RuntimeError("no coordinator record in %s after %.1fs" % (directory, timeout))


def build_peer(role, identity, modes=None, timeout_seconds=6000, steal_enabled=True, log=None, runner=None):
    """Construct a peer with the standard search-job runner unless one is given."""
    if runner is None and role == MeshPeer.ROLE_WORKER:
        runner = MeshJobs.SearchJobRunner(timeout_seconds=timeout_seconds, supported_modes=modes, log=log)
    return MeshPeer(
        identity,
        role=role,
        runner=runner,
        steal_enabled=steal_enabled,
        log=log,
        peer_timeout=6.0,
        heartbeat_interval=0.4,
    )


def load_jobs(path):
    """Read a job file into `protocol.Job` objects.

    A job only needs `mode` and `result_ref`; `job_id` defaults to a deterministic
    name, and `manifest` may carry the problem's printed start/goal (omitting it
    means the agenda's first case, exactly as `search-worker` behaves when the
    sidecar does not match any case).
    """
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    entries = payload.get("jobs", payload) if isinstance(payload, dict) else payload
    jobs = []
    for index, entry in enumerate(entries):
        mode = entry.get("mode", "dfs")
        result_ref = entry["result_ref"]
        job_id = entry.get("job_id") or ("%s-%s" % (mode, os.path.basename(result_ref)))
        jobs.append(
            protocol.Job(
                job_id,
                mode,
                entry.get("manifest", {}),
                result_ref,
                scope_ids=entry.get("scope_ids", ()),
                sequence=entry.get("sequence", 1),
            )
        )
    return jobs


def write_state(directory, name, peer, summary, coordinator=False):
    """Persist a peer's account of itself: summary, event ledger, terminal records.

    Written on clean shutdown, outside the repository, so a subprocess peer is
    inspectable after the fact -- that is how the suite reads what happened inside
    processes it did not own, and how an operator answers "what did that worker
    actually do".
    """
    state = {
        "peer_id": peer.peer_id,
        "role": peer.role,
        "address": peer.address,
        "summary": summary,
        "events": peer.events(),
        "results": {job_id: peer.outcome(job_id) for job_id in peer.terminal_job_ids()},
    }
    path = os.path.join(directory, "peer-%s.json" % name)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    os.replace(temp_path, path)
    if coordinator:
        ledger_path = os.path.join(directory, "ledger.json")
        temp_ledger = ledger_path + ".tmp"
        with open(temp_ledger, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
        os.replace(temp_ledger, ledger_path)
    return path


def run_peer_cli(
    role="worker",
    bind="127.0.0.1:0",
    coordinator=None,
    worker_modes=None,
    timeout_seconds=6000,
    cert_dir=None,
    jobs_file=None,
    run_seconds=0.0,
    cert_name=None,
):
    """Entry point for `python main.py mesh ...`. Returns a process exit code."""
    directory = cert_dir or default_cert_dir()
    modes = [mode.strip() for mode in (worker_modes or "dfs,bfs,astar,beam,rewritedfs").split(",") if mode.strip()]
    name = cert_name or role
    identity = ensure_identity(directory, name)
    host, _sep, port = bind.rpartition(":")
    host = host or "127.0.0.1"
    port = int(port or 0)

    def log(text):
        print("[mesh:%s] %s" % (name, text), flush=True)

    peer = build_peer(role, identity, modes=modes, timeout_seconds=timeout_seconds, log=log)
    address = peer.start(host, port)
    log("listening on %s (mTLS, mutual authentication required)" % address)

    submitted = []
    if role == MeshPeer.ROLE_COORDINATOR:
        publish_coordinator(directory, address, identity.ca_path, extra={"peer_id": peer.peer_id})
        log("published discovery record in %s" % directory)
        if jobs_file:
            for job in load_jobs(jobs_file):
                peer.submit(job)
                submitted.append(job.job_id)
            log("submitted %d job(s): %s" % (len(submitted), ", ".join(submitted)))
    else:
        target = coordinator
        if target is None:
            target = read_coordinator(directory).get("address")
        peer.join(target)
        log("joined %s" % target)

    started = time.time()
    try:
        while not peer._stop.is_set():
            if run_seconds and time.time() - started >= run_seconds:
                break
            if submitted:
                with peer._lock:
                    done = all(job_id in peer._results for job_id in submitted)
                if done:
                    break
            time.sleep(0.1)
    except KeyboardInterrupt:
        log("interrupted")
    summary = peer.shutdown()
    write_state(directory, name, peer, summary, coordinator=(role == MeshPeer.ROLE_COORDINATOR))
    log("summary: %s" % json.dumps(summary, sort_keys=True))
    failures = [job_id for job_id in submitted if (peer.outcome(job_id) or {}).get("status") != protocol.STATUS_OK]
    if failures:
        log("jobs without a successful result: %s" % ", ".join(failures))
        return 1
    return 0
