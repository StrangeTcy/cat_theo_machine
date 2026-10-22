"""Artifacts over the wire: the W20 extension of the W2 mesh beyond one filesystem.

The W2 contract is that a job carries *references* -- a result path, a unit
snapshot path -- and both ends read and write those paths on a filesystem they
share. That holds on one box and on two laptops with a shared mount; it does not
hold between a laptop and a Colab notebook, which share nothing but a socket.

This module keeps the contract and changes the medium. A peer in `wire` mode
still writes its result where the runner expects a file and still boots a unit
from a file on disk; what differs is how the file gets there:

* an **input** artifact (today: a W16 unit snapshot named by `unit_path`) is
  fetched from the coordinator on demand and written under the worker's own
  artifact root;
* a **result** artifact (the snapshot the runner wrote, plus its manifest
  sidecar) is pushed to the coordinator *before* the `job-result` frame, on the
  same ordered connection, and the coordinator writes it at the exact
  `result_ref` it issued.

Bytes travel as base64 inside ordinary JSON control frames (`artifact-begin`,
`artifact-chunk`, `artifact-end`), chunked under the 8 MiB frame cap, and every
transfer names its SHA-256 up front so a short or corrupt file is detected and
refused rather than loaded. This does **not** relax `framing.TERM_PAYLOAD_KEYS`:
what crosses the wire is the codec's own file, opaque to the transport, and the
receiver loads it through the codec exactly as it would from a shared mount.
There is still one serialisation of a machine term, and it is the snapshot.

Authority is asymmetric on purpose. A coordinator serves only files it named
itself in a job it submitted, and accepts only files at the `result_ref` (or its
sidecar) of a job it submitted -- a worker can neither read nor write an
arbitrary path on the coordinator's machine (`InputAuthority`,
`ResultAuthority`). The worker side maps every coordinator path onto its own
root with `local_path_for`, so two peers never need the same directory layout.
"""

from __future__ import annotations

import base64
import hashlib
import os
import tempfile
import threading
import time

from . import protocol

# Raw bytes per chunk. Base64 inflates by 4/3, and the frame also carries the
# JSON envelope, so 3 MiB raw stays well under framing.MAX_FRAME_BYTES (8 MiB).
CHUNK_BYTES = 3 * 1024 * 1024

KIND_INPUT = "input"
KIND_RESULT = "result"
KIND_SIDECAR = "sidecar"

SIDECAR_SUFFIX = ".manifest.json"


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def local_path_for(ref: str, root: str) -> str:
    """Where a coordinator-side reference lives on this peer.

    Stable (the same ref always maps to the same file, so a re-fetch is a hit),
    collision-free across directories (two refs with one basename differ in the
    hash prefix), and readable (the basename survives for anyone inspecting the
    directory). The sidecar of a result maps beside it, because the runner reads
    `result_ref + ".manifest.json"`.
    """
    if ref.endswith(SIDECAR_SUFFIX):
        return local_path_for(ref[: -len(SIDECAR_SUFFIX)], root) + SIDECAR_SUFFIX
    prefix = hashlib.sha1(ref.encode("utf-8")).hexdigest()[:12]
    return os.path.join(root, prefix + "-" + os.path.basename(ref))


def sidecar_of(ref: str) -> str:
    return ref + SIDECAR_SUFFIX


def new_transfer_id() -> str:
    return os.urandom(8).hex()


def describe(path: str, ref: str, job_id: str, kind: str, transfer_id: str = None) -> dict:
    """The `artifact-begin` payload for one file."""
    size = os.path.getsize(path)
    chunks = (size + CHUNK_BYTES - 1) // CHUNK_BYTES if size else 0
    return {
        "transfer_id": transfer_id or new_transfer_id(),
        "ref": ref,
        "job_id": job_id,
        "artifact_kind": kind,  # not "kind": that key is the frame's message type
        "size": size,
        "sha256": sha256_of(path),
        "chunks": chunks,
    }


def iter_chunks(path: str, chunk_bytes: int = CHUNK_BYTES):
    """Yield (index, base64 text) for a file, never holding more than one chunk."""
    index = 0
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk_bytes)
            if not block:
                return
            yield index, base64.b64encode(block).decode("ascii")
            index += 1


def send_file(connection, path: str, ref: str, job_id: str, kind: str) -> dict:
    """Queue one file onto a connection as begin/chunk/end frames, in order.

    `Connection.send` is a FIFO served by one writer thread, so frames queued here
    reach the socket in this order and ahead of anything queued afterwards -- which
    is what lets a worker send its result bytes and then its `job-result` without
    an acknowledgement round trip. Returns the begin payload (for the ledger).
    """
    header = describe(path, ref, job_id, kind)
    connection.send(protocol.message(protocol.ARTIFACT_BEGIN, **header))
    for index, data in iter_chunks(path):
        _throttle(connection)
        connection.send(
            protocol.message(
                protocol.ARTIFACT_CHUNK,
                transfer_id=header["transfer_id"],
                index=index,
                data_b64=data,
            )
        )
    connection.send(protocol.message(protocol.ARTIFACT_END, transfer_id=header["transfer_id"]))
    return header


def _throttle(connection, limit=8):
    """Keep at most `limit` chunks queued: a large file must not sit in memory as base64."""
    outbox = getattr(connection, "outbox", None)
    if outbox is None:
        return
    closed = getattr(connection, "closed", None)
    while outbox.qsize() > limit:
        if closed is not None and closed.is_set():
            return
        time.sleep(0.005)


class TransferError(Exception):
    """A transfer that must not produce a file: bad order, bad size, bad digest."""


class IncomingTransfer:
    """One file being reassembled from frames into a temporary neighbour of its target."""

    def __init__(self, header: dict, destination: str):
        self.header = dict(header)
        self.transfer_id = header["transfer_id"]
        self.ref = header["ref"]
        self.job_id = header.get("job_id", "")
        self.kind = header.get("artifact_kind", "")
        self.destination = destination
        self.expected_size = int(header.get("size", 0))
        self.expected_sha256 = header.get("sha256", "")
        self.expected_chunks = int(header.get("chunks", 0))
        self.received = 0
        self.next_index = 0
        self._digest = hashlib.sha256()
        directory = os.path.dirname(os.path.abspath(destination)) or "."
        os.makedirs(directory, exist_ok=True)
        handle, self.temp_path = tempfile.mkstemp(prefix=".incoming-", dir=directory)
        self._handle = os.fdopen(handle, "wb")

    def chunk(self, index: int, data_b64: str):
        if index != self.next_index:
            raise TransferError("chunk %d arrived, expected %d" % (index, self.next_index))
        try:
            block = base64.b64decode(data_b64, validate=True)
        except (ValueError, TypeError) as error:
            raise TransferError("chunk %d is not base64: %s" % (index, error))
        self._handle.write(block)
        self._digest.update(block)
        self.received += len(block)
        self.next_index += 1
        if self.received > self.expected_size:
            raise TransferError("received %d bytes, more than the declared %d" % (self.received, self.expected_size))

    def finish(self) -> str:
        """Verify and move the file into place. Returns its SHA-256."""
        self._handle.close()
        actual = self._digest.hexdigest()
        if self.received != self.expected_size:
            self.discard()
            raise TransferError("received %d bytes, declared %d" % (self.received, self.expected_size))
        if self.next_index != self.expected_chunks:
            self.discard()
            raise TransferError("received %d chunks, declared %d" % (self.next_index, self.expected_chunks))
        if self.expected_sha256 and actual != self.expected_sha256:
            self.discard()
            raise TransferError("sha256 %s does not match the declared %s" % (actual[:12], self.expected_sha256[:12]))
        try:
            os.chmod(self.temp_path, 0o644)  # mkstemp made it private; a result is not a secret
        except OSError:
            pass
        os.replace(self.temp_path, self.destination)
        return actual

    def discard(self):
        try:
            self._handle.close()
        except OSError:
            pass
        try:
            os.unlink(self.temp_path)
        except OSError:
            pass


class ArtifactReceiver:
    """Reassembles concurrent transfers, each already authorised to a destination."""

    def __init__(self):
        self._open = {}
        self._lock = threading.Lock()  # guards the table; each transfer is fed by one reader thread

    def peek(self, transfer_id: str):
        with self._lock:
            return self._open.get(transfer_id)

    def begin(self, header: dict, destination: str) -> IncomingTransfer:
        transfer_id = header.get("transfer_id", "")
        if not transfer_id:
            raise TransferError("transfer without an id")
        with self._lock:
            if transfer_id in self._open:
                raise TransferError("transfer %s already open" % transfer_id)
        transfer = IncomingTransfer(header, destination)
        with self._lock:
            self._open[transfer_id] = transfer
        return transfer

    def chunk(self, transfer_id: str, index: int, data_b64: str) -> IncomingTransfer:
        transfer = self.peek(transfer_id)
        if transfer is None:
            raise TransferError("chunk for unknown transfer %s" % transfer_id)
        try:
            transfer.chunk(index, data_b64)
        except TransferError:
            with self._lock:
                self._open.pop(transfer_id, None)
            transfer.discard()
            raise
        return transfer

    def end(self, transfer_id: str) -> IncomingTransfer:
        with self._lock:
            transfer = self._open.pop(transfer_id, None)
        if transfer is None:
            raise TransferError("end for unknown transfer %s" % transfer_id)
        transfer.finish()
        return transfer

    def abandon(self, transfer_id: str):
        with self._lock:
            transfer = self._open.pop(transfer_id, None)
        if transfer is not None:
            transfer.discard()

    def abandon_all(self):
        with self._lock:
            pending = list(self._open)
        for transfer_id in pending:
            self.abandon(transfer_id)

    @property
    def open_count(self) -> int:
        with self._lock:
            return len(self._open)


class ResultAuthority:
    """Which incoming files a coordinator will write, and where.

    Only the `result_ref` of a job this coordinator submitted, or that ref's
    manifest sidecar, and only from a peer that may legitimately hold the job
    (the current owner, a thief that just started it, or anyone when ownership is
    unknown because the link dropped -- the job id is the capability; the path is
    never taken from the wire).
    """

    def __init__(self, jobs_by_id):
        self._jobs = jobs_by_id  # live mapping job_id -> Job, shared with the peer

    def destination_for(self, header: dict):
        job = self._jobs.get(header.get("job_id", ""))
        if job is None:
            return None, "unknown-job"
        ref = header.get("ref", "")
        kind = header.get("artifact_kind", "")
        if kind == KIND_RESULT and ref == job.result_ref:
            return job.result_ref, ""
        if kind == KIND_SIDECAR and ref == sidecar_of(job.result_ref):
            return sidecar_of(job.result_ref), ""
        return None, "ref-not-the-job's-result"


class InputAuthority:
    """Which files a coordinator will serve: inputs it named itself, nothing else."""

    def __init__(self, jobs_by_id):
        self._jobs = jobs_by_id

    def path_for(self, job_id: str, ref: str):
        job = self._jobs.get(job_id)
        if job is None:
            return None, "unknown-job"
        for candidate in input_refs(job):
            if candidate == ref:
                if not os.path.exists(candidate):
                    return None, "not-on-disk"
                return candidate, ""
        return None, "ref-not-an-input-of-the-job"


def input_refs(job) -> list:
    """The coordinator-side files a job needs before it can run."""
    refs = []
    unit_path = (job.manifest or {}).get("unit_path")
    if unit_path:
        refs.append(unit_path)
    return refs


def localised(job, root: str):
    """A copy of a job whose references point under this peer's artifact root.

    Only the file references move; `source_digest` hashes the problem text and
    scope, not the paths, so the copy is the same job to every guard that checks
    identity. The original is kept by the caller for everything that goes back
    on the wire -- the coordinator must hear its own references.
    """
    manifest = dict(job.manifest)
    if manifest.get("unit_path"):
        manifest["unit_path"] = local_path_for(manifest["unit_path"], root)
    copy = protocol.Job(
        job.job_id,
        job.mode,
        manifest,
        local_path_for(job.result_ref, root),
        scope_ids=job.scope_ids,
        sequence=job.sequence,
        origin=job.origin,
        attempt=job.attempt,
        stolen_from=job.stolen_from,
    )
    return copy
