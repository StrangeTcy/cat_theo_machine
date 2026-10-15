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

Beyond one box (W20). The same CLI runs a mesh split across a laptop and a remote
worker (a Colab notebook) that cannot see the laptop's filesystem and cannot be
dialled. Three things change, none of them in the protocol's job semantics:

* `--role issue` makes a *bundle* for the remote peer: the CA certificate plus
  one leaf certificate and its key, and nothing else. The CA key stays home. The
  bundle travels out of band (an upload into the notebook's session storage,
  not through the repository, which is public).
* the remote worker runs with `--no-inbound --verify identity --expect NAME
  --artifacts wire --artifact-dir DIR`: it only dials out, it checks the
  coordinator's certificate by common name under the CA pin (a tunnel address is
  nothing a leaf can be issued for), and job inputs and results travel in frames
  rather than being paths on a shared disk.
* the laptop coordinator runs with `--bind 0.0.0.0:PORT --artifacts wire
  --advertise HOST:PORT`, where HOST:PORT is whatever tunnel forwards to it.

CLI (also reachable as `python main.py mesh ...`):

    coordinator:  python main.py mesh --role coordinator --cert-dir DIR --jobs jobs.json --run-seconds 120
    worker:       python main.py mesh --role worker --cert-dir DIR --run-seconds 120
    issue bundle: python main.py mesh --role issue --cert-dir DIR --cert-name colab-1 --bundle-dir OUT
    WAN coord.:   python main.py mesh --role coordinator --cert-dir DIR --bind 0.0.0.0:7443 \
                      --artifacts wire --advertise tunnel.example:7443 --jobs jobs.json
    WAN worker:   python main.py mesh --role worker --cert-dir BUNDLE --cert-name colab-1 \
                      --coordinator tunnel.example:7443 --no-inbound --verify identity \
                      --expect coordinator --artifacts wire --artifact-dir WORK

The coordinator boots nothing itself; workers boot the machine once and reuse it
for every job they run.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time

from .networking import identity as MeshIdentityModule
from .networking import jobs as MeshJobs
from .networking import protocol
from .networking.peer import MeshPeer


ROLE_ISSUE = "issue"


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
    if not os.path.exists(_ca_key_path(directory)):
        # A bundle made by `--role issue` deliberately has no CA key: it can
        # only be the identity it was issued for.
        raise RuntimeError(
            "no certificate named %r in %s, and no CA key there to issue one; "
            "a bundle only holds the leaf it was issued for (check --cert-name), "
            "or issue one on the coordinator with `mesh --role issue`" % (name, directory)
        )
    pki = load_pki(directory)
    return pki.issue(name, sans=("127.0.0.1", "localhost"), days=days, basename=name)


def load_pki(directory):
    """Open the PKI in `directory` (which must hold `ca.crt` and `ca.key`)."""
    directory = MeshIdentityModule.pki_directory_guard(directory)
    ca_path = os.path.join(directory, "ca.crt")
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
    return MeshIdentityModule.MeshPki(directory, ca_identity, ca_key)


def issue_identity(directory, name, pki, days=7, sans=("127.0.0.1", "localhost")):
    """Issue a named leaf from a PKI the caller already holds (used by the suite)."""
    return pki.issue(name, sans=sans, days=days, basename=name)


BUNDLE_FILES = ("ca.crt",)


def issue_bundle(directory, name, bundle_dir, days=7, sans=("127.0.0.1", "localhost")):
    """Issue a leaf for a remote peer and stage exactly what it needs to travel.

    The bundle holds three files: `ca.crt`, `NAME.crt`, `NAME.key`. The CA key is
    not among them, so a leaked bundle is one revocable identity, not the power to
    mint more. The remote side points `--cert-dir` at the unpacked bundle and
    `--cert-name` at NAME; `ensure_identity` then finds the leaf and never looks
    for a CA key. Returns the list of staged paths.
    """
    directory = MeshIdentityModule.pki_directory_guard(directory)
    bundle_dir = MeshIdentityModule.pki_directory_guard(bundle_dir)
    if not os.path.exists(os.path.join(directory, "ca.crt")):
        # First use on this box: create the CA (and the coordinator's own leaf
        # comes later, from the same directory, when the coordinator starts).
        MeshIdentityModule.MeshPki.create(directory)
    pki = load_pki(directory)
    leaf = pki.issue(name, sans=tuple(sans), days=days, basename=name)
    os.makedirs(bundle_dir, exist_ok=True)
    staged = []
    for source in (leaf.ca_path, leaf.cert_path, leaf.key_path):
        target = os.path.join(bundle_dir, os.path.basename(source))
        shutil.copyfile(source, target)
        if source == leaf.key_path:
            os.chmod(target, 0o600)
        staged.append(target)
    with open(os.path.join(bundle_dir, "bundle.json"), "w", encoding="utf-8") as handle:
        json.dump(
            {
                "common_name": name,
                "files": [os.path.basename(path) for path in staged],
                "contains_ca_key": False,
                "note": "copy out of band; never into the repository",
            },
            handle,
            indent=2,
            sort_keys=True,
        )
    return staged


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


def build_peer(
    role,
    identity,
    modes=None,
    timeout_seconds=6000,
    steal_enabled=True,
    log=None,
    runner=None,
    artifacts=protocol.ARTIFACTS_SHARED,
    artifact_dir=None,
    inbound=True,
    verify=protocol.VERIFY_HOSTNAME,
    expect=None,
    advertise=None,
):
    """Construct a peer with the standard search-job runner unless one is given."""
    if runner is None and role == MeshPeer.ROLE_WORKER:
        runner = MeshJobs.SearchJobRunner(timeout_seconds=timeout_seconds, supported_modes=modes, log=log)
    # Liveness tuning is `MeshPeer`'s business: a peer is silent under load (a
    # search job holds the interpreter), so the CLI must not shorten the class's
    # patience with its own default -- that is how a busy peer gets declared lost.
    return MeshPeer(
        identity,
        role=role,
        runner=runner,
        steal_enabled=steal_enabled,
        log=log,
        heartbeat_interval=0.4,
        artifacts=artifacts,
        artifact_dir=artifact_dir,
        inbound=inbound,
        verify=verify,
        expect_coordinator=expect,
        advertise=advertise,
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
    swarm=False,
    artifacts=protocol.ARTIFACTS_SHARED,
    artifact_dir=None,
    inbound=True,
    verify=protocol.VERIFY_HOSTNAME,
    expect=None,
    advertise=None,
    bundle_dir=None,
    sans=None,
):
    """Entry point for `python main.py mesh ...`. Returns a process exit code.

    `swarm` swaps the worker's runner: W16 work units are snapshots rather than
    agenda problems, so they are served by `SwarmJobRunner` instead of the search
    worker. The transport, membership, leases and stealing are unchanged -- that
    is the point of consuming W2 rather than reimplementing it.

    `artifacts`, `artifact_dir`, `inbound`, `verify`, `expect` and `advertise` are
    the W20 switches described in the module docstring; their defaults reproduce
    the one-filesystem mesh exactly. `role="issue"` does not start a peer at all:
    it writes a bundle for a remote peer into `bundle_dir` and returns.
    """
    directory = cert_dir or default_cert_dir()
    modes = [mode.strip() for mode in (worker_modes or "dfs,bfs,astar,beam,rewritedfs").split(",") if mode.strip()]
    name = cert_name or role

    def log(text):
        print("[mesh:%s] %s" % (name, text), flush=True)

    if role == ROLE_ISSUE:
        if not cert_name:
            log("--role issue needs --cert-name (the remote peer's identity, e.g. colab-1)")
            return 2
        target = bundle_dir or os.path.join(tempfile.mkdtemp(prefix="hyge-bundle-"), name)
        san_list = tuple(item.strip() for item in (sans or "127.0.0.1,localhost").split(",") if item.strip())
        staged = issue_bundle(directory, name, target, sans=san_list)
        log("issued %s from the CA in %s" % (name, directory))
        for path in staged:
            log("  staged %s" % path)
        log("bundle in %s: carry it out of band (not through the repository); the CA key stayed home" % target)
        return 0

    identity = ensure_identity(directory, name)
    host, _sep, port = bind.rpartition(":")
    host = host or "127.0.0.1"
    port = int(port or 0)
    if role == MeshPeer.ROLE_WORKER and verify == protocol.VERIFY_IDENTITY and not expect:
        # The coordinator's default certificate name is its role; an operator
        # who named it otherwise says so with --expect.
        expect = MeshPeer.ROLE_COORDINATOR
    if role == MeshPeer.ROLE_WORKER and artifacts == protocol.ARTIFACTS_WIRE and not artifact_dir:
        artifact_dir = tempfile.mkdtemp(prefix="hyge-artifacts-")
        log("no --artifact-dir given; fetched inputs and results go under %s" % artifact_dir)

    runner = None
    if swarm:
        runner = MeshJobs.SwarmJobRunner(timeout_seconds=timeout_seconds, supported_modes=modes, log=log)
    peer = build_peer(
        role,
        identity,
        modes=modes,
        timeout_seconds=timeout_seconds,
        log=log,
        runner=runner,
        artifacts=artifacts,
        artifact_dir=artifact_dir,
        inbound=inbound,
        verify=verify,
        expect=expect,
        advertise=advertise,
    )
    address = peer.start(host, port)
    if address:
        log("listening on %s (mTLS, mutual authentication required)" % address)
        if peer.announced_address != address:
            log("announcing %s to peers" % peer.announced_address)
    else:
        log("no listener (--no-inbound): outbound connections only")
    if artifacts == protocol.ARTIFACTS_WIRE:
        log("artifacts travel over the wire" + ("; local root %s" % artifact_dir if artifact_dir else ""))

    submitted = []
    if role == MeshPeer.ROLE_COORDINATOR:
        publish_coordinator(
            directory,
            peer.announced_address,
            identity.ca_path,
            extra={"peer_id": peer.peer_id, "artifacts": artifacts, "bound": address},
        )
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
        log("joined %s%s" % (target, (" as %s (identity check: %s)" % (name, expect)) if verify == protocol.VERIFY_IDENTITY else ""))

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
    failures = [
        job_id
        for job_id in submitted
        if not protocol.status_is_success((peer.outcome(job_id) or {}).get("status"))
    ]
    if failures:
        log("jobs without a successful result: %s" % ", ".join(failures))
        return 1
    return 0
