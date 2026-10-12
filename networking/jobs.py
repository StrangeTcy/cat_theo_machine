"""Job execution: turning a mesh `Job` into a result artifact on disk.

The mesh did not invent a second way to run a search. A job is the same
manifest/result contract the file transport already uses:

    manifest (start_text/goal_text) -> result snapshot + ".manifest.json" sidecar

The only difference is *when* the expensive part happens. `run_search_worker_mode`
boots from packs (~20 s) for every process it runs; a mesh peer boots once and then
executes jobs through `main.search_worker_execute`, the very function
`run_search_worker_mode` now delegates to. Job semantics are therefore identical by
construction, which is what lets the suite compare a stolen job's result against a
locally run one and expect them to match.

Machine values never cross the wire here: the job's manifest is plain text and the
result is a reference to a file the snapshot codec wrote.
"""

from __future__ import annotations

import hashlib
import os
import time

from . import protocol


class JobOutcome:
    """What a peer reports back about one job it ran."""

    __slots__ = (
        "job_id",
        "status",
        "exit_code",
        "result_ref",
        "source_digest",
        "elapsed_seconds",
        "reason",
        "peer_id",
        "stolen_from",
        "artifact_bytes",
    )

    def __init__(
        self,
        job_id,
        status,
        exit_code,
        result_ref,
        source_digest,
        elapsed_seconds=0.0,
        reason="",
        peer_id="",
        stolen_from="",
        artifact_bytes=0,
    ):
        self.job_id = job_id
        self.status = status
        self.exit_code = exit_code
        self.result_ref = result_ref
        self.source_digest = source_digest
        self.elapsed_seconds = elapsed_seconds
        self.reason = reason
        self.peer_id = peer_id
        self.stolen_from = stolen_from
        self.artifact_bytes = artifact_bytes

    def as_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "exit_code": self.exit_code,
            "result_ref": self.result_ref,
            "source_digest": self.source_digest,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "reason": self.reason,
            "peer_id": self.peer_id,
            "stolen_from": self.stolen_from,
            "artifact_bytes": self.artifact_bytes,
        }


def exit_code_to_status(exit_code: int) -> str:
    """Map `search_worker_execute`'s return code onto a mesh status."""
    if exit_code == 0:
        return protocol.STATUS_OK
    if exit_code == 2:
        return protocol.STATUS_TIMED_OUT
    if exit_code == 4:
        return protocol.STATUS_DEFERRED
    return protocol.STATUS_FAILED


def artifact_digest(result_ref: str) -> str:
    """Integrity digest of the result artifact as written (bytes, not semantics)."""
    try:
        with open(result_ref, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()[:32]
    except OSError:
        return ""


def project_result(result_ref: str, namespace=None):
    """The machine-semantic projection of a result snapshot.

    Timing and process identity are deliberately excluded: two runs of the same
    job *should* differ in elapsed milliseconds and pid and must not differ in
    what they proved. Everything in this projection comes out of the snapshot's
    roots through the machine's own accessors, so comparing two projections
    compares proofs rather than bytes.
    """
    from .. import main as MA
    from .. import machine as M
    from .. import proof as P
    from ..persistence import SnapshotCodec

    if namespace is None:
        namespace = MA._runtime_namespace()
    state = SnapshotCodec(namespace).load(result_ref)
    roots = state.roots
    registry = roots.get("constructor_registry", M.EmptyList)
    projection = {
        "artifact": os.path.basename(result_ref),
        "worker_stage": "",
        "status": "no-attempt",
        "derivation_digest": "-",
        "derivation_bytes": 0,
        "plan_digest": "-",
        "proof_cost_digest": "-",
    }
    worker_stage = roots.get("worker_stage", M.EmptyList)
    if M.Compare(worker_stage, M.EmptyList)() is M.false_value:
        try:
            projection["worker_stage"] = str(worker_stage())
        except Exception:
            projection["worker_stage"] = ""
    attempts = roots.get("search_history", M.EmptyList)
    if M.Compare(attempts, M.EmptyList)() is M.false_value:
        attempt = M.Head(attempts)()
        status = P.SearchAttemptStatus(attempt)()
        projection["status"] = str(status())
        derivation = P.SearchAttemptDerivation(attempt)()
        if M.Compare(derivation, M.EmptyList)() is M.false_value:
            text = M.PrettyTerm(derivation, registry)()
            projection["derivation_digest"] = hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
            projection["derivation_bytes"] = len(text)
        proof_cost = P.SearchAttemptProofCost(attempt)()
        if M.Compare(proof_cost, M.EmptyList)() is M.false_value:
            text = M.PrettyTerm(proof_cost, registry)()
            projection["proof_cost_digest"] = hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
    plan = roots.get("worker_plan", M.EmptyList)
    if M.Compare(plan, M.EmptyList)() is M.false_value:
        text = M.PrettyTerm(plan, registry)()
        projection["plan_digest"] = hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
    return projection


class SearchJobRunner:
    """Executes jobs on one long-lived, booted runtime.

    A peer owns exactly one runner and runs exactly one job at a time; jobs that
    are dispatched but not yet started sit in the peer's queue, where another
    peer may steal them (see `networking/peer.py`). Booting inside the runner
    rather than inside `run_search_worker_mode` is the whole point: it moves the
    ~20 s pack boot out of the per-job path without touching job semantics.
    """

    def __init__(self, namespace=None, timeout_seconds: int = 6000, supported_modes=None, log=None):
        self.namespace = namespace
        self.timeout_seconds = timeout_seconds
        self.supported_modes = tuple(supported_modes) if supported_modes else ("dfs", "bfs", "astar", "beam", "rewritedfs")
        self._boot = None
        self._log = log or (lambda text: None)

    @property
    def booted(self) -> bool:
        return self._boot is not None

    def supports(self, mode: str) -> bool:
        return mode in self.supported_modes

    def boot(self, job):
        """Boot from packs for the first job and remember the runtime."""
        from .. import main as MA

        if self.namespace is None:
            self.namespace = MA._runtime_namespace()
        self._log("booting the machine for the first job (one boot per peer)")
        started = time.time()
        self._boot = MA.search_worker_boot(job.mode, job.result_ref, self.timeout_seconds)
        self._log("booted in %.1fs" % (time.time() - started))
        return self._boot

    def run(self, job) -> JobOutcome:
        from .. import main as MA
        from .. import machine as M

        started = time.time()
        boot = self._boot if self._boot is not None else self.boot(job)
        if self._boot is not None and self._boot.runtime is not None:
            # Resolve this job's problem against the already-booted runtime. The
            # manifest sidecar is written first because that is what the worker
            # contract reads to choose the agenda case.
            protocol.write_manifest_sidecar(job.manifest, job.result_ref)
            registry = M.FromContextGetConstructors(boot.runtime.graph)()
            label, start, goal, heuristic = MA.search_worker_resolve_problem(
                boot.runtime, boot.packs, job.mode, job.result_ref, registry
            )
            boot = MA.SearchWorkerBoot(
                boot.runtime, boot.packs, registry, label, start, goal, heuristic, False
            )
        exit_code = MA.search_worker_execute(job.mode, job.result_ref, self.timeout_seconds, boot)
        elapsed = time.time() - started
        status = exit_code_to_status(exit_code)
        return JobOutcome(
            job.job_id,
            status,
            exit_code,
            job.result_ref,
            job.source_digest,
            elapsed_seconds=elapsed,
            reason="" if status == protocol.STATUS_OK else status,
            artifact_bytes=os.path.getsize(job.result_ref) if os.path.exists(job.result_ref) else 0,
        )
