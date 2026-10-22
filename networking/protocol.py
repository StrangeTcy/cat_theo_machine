"""The mesh protocol: message kinds, jobs, scopes and leases.

Two ideas do the real work here, and both come from the DAG:

* **Scope.** A job declares the hypergraph content it will touch (node/edge ids)
  and the result artifact it will write. The mesh allows at most one active lease
  per scope id, so two peers can never work -- or write -- the same thing at once.
  That is what makes the layer "hyperedge-aware": ownership is keyed by content
  identity, not by job id. Distinct search modes over the same problem have
  distinct result references and no declared content ids, so they run in
  parallel, exactly as `search/compare_subprocess.py` already fans them out.

* **Sequence.** Every job carries a per-scope sequence number assigned by the
  coordinator. A peer refuses a job whose sequence is not greater than the highest
  it has already completed for that scope (`refused-stale`). The guard is the mesh
  counterpart of the snapshot monotonicity that `graph.py`'s `GraphVersion`
  enforces in-kernel: newer state is never overwritten by a result computed
  against older state, and a stale result is reported rather than silently mixed
  in. W17's monotonic snapshot broadcast depends on this rule.

Jobs carry *references* -- a result path on the shared filesystem -- never machine
terms; see `networking/framing.py`.
"""

from __future__ import annotations

import hashlib
import json
import os

PROTOCOL_VERSION = 1

# ---------------------------------------------------------------- message kinds

JOIN = "join"                      # worker -> coordinator: here is my identity and capacity
WELCOME = "welcome"                # coordinator -> worker: membership snapshot, intervals
REJECT = "reject"                  # either direction: protocol/identity refusal
HEARTBEAT = "heartbeat"            # either direction: I am alive, here is my load
JOB_OFFER = "job-offer"            # coordinator -> worker (or peer -> peer on a steal)
JOB_QUEUED = "job-queued"          # worker -> coordinator: accepted, waiting behind a running job
JOB_STARTED = "job-started"        # worker -> coordinator: lease taken, work begins
JOB_DECLINED = "job-declined"      # worker -> coordinator: refused, with a reason
JOB_RESULT = "job-result"          # worker -> coordinator: finished, here is the reference
STEAL_REQUEST = "steal-request"    # idle peer -> busy peer, directly (peer to peer)
STEAL_GRANT = "steal-grant"        # busy peer -> idle peer: take this job and its lease
STEAL_DENIED = "steal-denied"      # busy peer -> idle peer: nothing to hand over
SHUTDOWN = "shutdown"              # coordinator -> peers: finish, release, exit
GOODBYE = "goodbye"                # peer -> peer: leaving the mesh cleanly

# W20 -- artifacts over the wire (see `networking/artifacts.py`). Bytes of the
# codec's own files, chunked and digest-named; never a machine term.
ARTIFACT_FETCH = "artifact-fetch"      # worker -> coordinator: send me this input of job X
ARTIFACT_BEGIN = "artifact-begin"      # either direction: a file follows (ref, size, sha256, chunks)
ARTIFACT_CHUNK = "artifact-chunk"      # either direction: one base64 piece, in order
ARTIFACT_END = "artifact-end"          # either direction: all pieces sent
ARTIFACT_MISSING = "artifact-missing"  # coordinator -> worker: that is not an input I can serve
ARTIFACT_REFUSED = "artifact-refused"  # receiver -> sender: that transfer is not authorised / failed

# How a peer gets at a job's files: on a filesystem both ends share (W2's
# original contract) or as bytes over the mesh connection (W20).
ARTIFACTS_SHARED = "shared"
ARTIFACTS_WIRE = "wire"

# How a dialling peer checks the certificate it is shown, beyond the CA pin that
# every connection has: by hostname/SAN (loopback default) or by the common name
# it expects (identity -- what a tunnel or a NAT-traversed address needs).
VERIFY_HOSTNAME = "hostname"
VERIFY_IDENTITY = "identity"

# Refusal reasons, so tests can assert on them rather than on prose.
REFUSED_STALE = "refused-stale"
REFUSED_SCOPE = "refused-scope-busy"
REFUSED_MODE = "refused-unsupported-mode"
REFUSED_SHUTDOWN = "refused-shutting-down"
REFUSED_DUPLICATE = "refused-duplicate-result"

STATUS_OK = "ok"
STATUS_FAILED = "failed"
STATUS_TIMED_OUT = "timed-out"
STATUS_DEFERRED = "deferred"

# Statuses that mean "this job produced its result". `deferred` is one of them:
# the search ran to a plan and the snapshot holds it; only the derivation replay
# was skipped (the search worker's own rc=4 under
# `HYGE_SEARCH_WORKER_DEFER_DERIVATION=1`). Counting it as a failure invents a
# failure out of a result -- the mesh did exactly that to `main.py mesh`'s exit
# code until this existed.
SUCCESS_STATUSES = (STATUS_OK, STATUS_DEFERRED)


def status_is_success(status) -> bool:
    """True when a job's terminal status carries a result."""
    return status in SUCCESS_STATUSES


def message(kind: str, **payload) -> dict:
    payload["protocol_version"] = PROTOCOL_VERSION
    payload["kind"] = kind
    return payload


def scope_key(nodes, edges) -> str:
    """A stable key for a set of hypergraph node/edge ids."""
    payload = json.dumps(
        {"nodes": sorted(str(node) for node in nodes), "edges": sorted(str(edge) for edge in edges)},
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def source_digest(mode: str, start_text: str, goal_text: str, scope_ids) -> str:
    """The identity of a job's *input*: what a result was computed against."""
    payload = json.dumps(
        {
            "mode": mode,
            "start": start_text,
            "goal": goal_text,
            "scope": sorted(str(item) for item in scope_ids),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


class Job:
    """A unit of work: run one search mode over one problem, write one result."""

    __slots__ = (
        "job_id",
        "mode",
        "manifest",
        "result_ref",
        "scope_ids",
        "sequence",
        "source_digest",
        "origin",
        "attempt",
        "stolen_from",
    )

    def __init__(
        self,
        job_id,
        mode,
        manifest,
        result_ref,
        scope_ids=(),
        sequence=1,
        origin="",
        attempt=1,
        stolen_from="",
    ):
        self.job_id = job_id
        self.mode = mode
        self.manifest = dict(manifest)
        self.result_ref = result_ref
        self.scope_ids = tuple(sorted(str(item) for item in scope_ids))
        self.sequence = int(sequence)
        self.origin = origin
        self.attempt = int(attempt)
        self.stolen_from = stolen_from
        self.source_digest = source_digest(
            mode,
            self.manifest.get("start_text", ""),
            self.manifest.get("goal_text", ""),
            self.scope_ids,
        )

    @property
    def scope_key(self) -> str:
        """Leases are keyed by what a job may write and by its declared content."""
        declared = scope_key(self.scope_ids, ()) if self.scope_ids else ""
        result = scope_key((), (self.result_ref,))
        return declared + "|" + result if declared else result

    @property
    def content_scope_key(self) -> str:
        return scope_key(self.scope_ids, ()) if self.scope_ids else ""

    def as_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "mode": self.mode,
            "manifest": dict(self.manifest),
            "result_ref": self.result_ref,
            "scope_ids": list(self.scope_ids),
            "sequence": self.sequence,
            "source_digest": self.source_digest,
            "origin": self.origin,
            "attempt": self.attempt,
            "stolen_from": self.stolen_from,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Job":
        job = cls(
            payload["job_id"],
            payload["mode"],
            payload.get("manifest", {}),
            payload["result_ref"],
            payload.get("scope_ids", ()),
            payload.get("sequence", 1),
            payload.get("origin", ""),
            payload.get("attempt", 1),
            payload.get("stolen_from", ""),
        )
        declared = payload.get("source_digest")
        if declared and declared != job.source_digest:
            raise ValueError("job source_digest does not match its contents")
        return job


class Lease:
    """The right to work one scope until the job owning it finishes."""

    __slots__ = ("job_id", "peer_id", "scope_key", "sequence", "lease_id")

    def __init__(self, job_id, peer_id, scope_key_value, sequence, lease_id):
        self.job_id = job_id
        self.peer_id = peer_id
        self.scope_key = scope_key_value
        self.sequence = sequence
        self.lease_id = lease_id

    def as_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "peer_id": self.peer_id,
            "scope_key": self.scope_key,
            "sequence": self.sequence,
            "lease_id": self.lease_id,
        }


def write_manifest_sidecar(manifest: dict, result_ref: str) -> str:
    """Write the `search-worker` manifest next to a job's result reference.

    The sidecar is the existing contract between the two transports: the worker
    reads `start_text`/`goal_text` from it to choose which agenda case to search.
    """
    path = result_ref + ".manifest.json"
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle)
    os.replace(temp_path, path)
    return path
