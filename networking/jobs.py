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
import json
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


def _snapshot_object_graph(result_ref):
    """The snapshot's persisted object table, indexed by object id.

    This is the codec's own on-disk form: a flat table of tagged entries plus a
    map of root name -> object id. It is read instead of walking the *loaded*
    terms because it is both cheaper (one JSON parse) and canonical -- the object
    ids are assigned by the codec's traversal, so the same proof always produces
    the same table whatever process wrote it.
    """
    with open(result_ref, encoding="utf-8") as handle:
        data = json.load(handle)
    objects = {entry["id"]: entry for entry in data.get("objects", [])}
    return data.get("roots", {}), objects


def _reference_targets(entry):
    """Every object id an entry points at, whatever shape the entry has."""
    for key, value in entry.items():
        if key == "id":
            continue
        if isinstance(value, dict):
            if value.get("tag") == "ref":
                yield value["id"]
            else:
                yield from _reference_targets(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and item.get("tag") == "ref":
                    yield item["id"]
                elif isinstance(item, (dict, list)):
                    yield from _reference_targets(item)


def _relabel_closure(entry, labels):
    """Rewrite a closure so it refers to *positions*, not object ids.

    Two snapshots of the same proof assign the same ids, but two snapshots of
    logically equal proofs need not: the ids depend on how much else the codec
    captured first. Comparing position within the traversal order instead of raw
    ids is what makes the digest a property of the proof rather than of the run.
    """
    if isinstance(entry, dict):
        if entry.get("tag") == "ref":
            return ["@", labels.get(entry["id"], -1)]
        return {key: _relabel_closure(value, labels) for key, value in entry.items()}
    if isinstance(entry, list):
        return [_relabel_closure(item, labels) for item in entry]
    return entry


def _root_digest(roots, objects, root_name):
    """Canonical digest and size of everything reachable from one snapshot root.

    Nothing about the run enters here -- no pid, no clock, no machine id -- so
    two runs that proved the same thing produce the same digest, and a run that
    proved something else cannot.
    """
    root_id = roots.get(root_name)
    if root_id is None:
        return "-", 0
    labels = {}
    order = []
    stack = [root_id]
    while stack:
        object_id = stack.pop()
        if object_id in labels or object_id not in objects:
            continue
        labels[object_id] = len(order)
        order.append(object_id)
        stack.extend(_reference_targets(objects[object_id]))
    canonical = [_relabel_closure({k: v for k, v in objects[object_id].items() if k != "id"}, labels) for object_id in order]
    text = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32], len(text)


def _status_text(status):
    """The machine's own name for an attempt status label.

    The status labels are singletons defined in `labels`, and identity is exactly
    how the rest of the repository tells them apart (see
    `search/compare_subprocess.py`), so no string round trip is needed.
    """
    from .. import labels as L
    from .. import machine as M

    for label, text in (
        ("SearchSuccessLabel", "success-plan-found"),
        ("SearchFailureLabel", "failure-search"),
        ("SearchTimedOutLabel", "timed-out"),
        ("SearchAbortedByUserLabel", "aborted-by-user"),
    ):
        candidate = getattr(L, label, None)
        if candidate is not None and M.IdentityCompare(status, candidate)() is M.truth_value:
            return text
    return "unknown"


def project_result(result_ref: str, namespace=None):
    """The machine-semantic projection of a result snapshot.

    Timing and process identity are deliberately excluded: two runs of the same
    job *should* differ in elapsed milliseconds and pid and must not differ in
    what they proved. Everything in this projection comes out of the snapshot's
    roots -- the status and stage through the machine's own accessors, the plan
    and the attempt through the codec's canonical object graph -- so comparing
    two projections compares proofs rather than bytes.

    The digests deliberately do *not* go through `PrettyTerm`: pretty-printing a
    real plan rebuilds machine ids per node and does not terminate on realistic
    searches (it was measured still spinning after fifteen minutes on a 31-object
    plan). The snapshot's own graph is the same evidence, read directly.
    """
    from .. import main as MA
    from .. import machine as M
    from .. import proof as P
    from ..persistence import SnapshotCodec

    if namespace is None:
        namespace = MA._runtime_namespace()
    state = SnapshotCodec(namespace).load(result_ref)
    roots = state.roots
    graph_roots, objects = _snapshot_object_graph(result_ref)
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
        projection["status"] = _status_text(P.SearchAttemptStatus(attempt)())
        derivation = P.SearchAttemptDerivation(attempt)()
        if M.Compare(derivation, M.EmptyList)() is M.false_value:
            digest, size = _root_digest(graph_roots, objects, "derivations")
            projection["derivation_digest"] = digest
            projection["derivation_bytes"] = size
        if M.Compare(P.SearchAttemptProofCost(attempt)(), M.EmptyList)() is M.false_value:
            # The proof cost lives inside the attempt, so the attempt root is the
            # canonical place to read it from -- and it is timing-free: two runs of
            # the same job persist byte-identical attempt graphs.
            projection["proof_cost_digest"], _ = _root_digest(graph_roots, objects, "search_history")
    plan = roots.get("worker_plan", M.EmptyList)
    if M.Compare(plan, M.EmptyList)() is M.false_value:
        projection["plan_digest"], _ = _root_digest(graph_roots, objects, "worker_plan")
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
            reason="" if protocol.status_is_success(status) else status,
            artifact_bytes=os.path.getsize(job.result_ref) if os.path.exists(job.result_ref) else 0,
        )
