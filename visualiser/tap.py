"""Observation tap: a read-only observer installed inside the observed process.

The visualiser never starts a Machine and never touches Machine state. Instead
the Machine script opts in, once, with::

    from cat_theo_machine.visualiser.tap import observe
    observe(runtime)          # or observe(runtime.graph)

That starts a daemon thread in the *script's own* process which polls the graph
roots, renders whatever is new, and appends events to a journal file. The
visualiser reads that journal. No kernel module is patched, no method is wrapped,
and nothing the tap does can change what the Machine computes: every read goes
through ``Head``/``Tail``/``IsPair``/``PrettyTerm`` and the graph's own roots.

Because the tap lives in the script, the script stays in charge of its own
execution. Stop the script and the journal stops growing; the visualiser keeps
whatever it already read, which is what makes recording and replay possible.
"""
import atexit
import json
import os
import threading
import time

from .events import EventStream, GraphDigest, machine_identity

DEFAULT_JOURNAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run", "observed.jsonl")


class GraphObservationTap:
    """Polls one hypergraph and appends what changed to a journal file."""

    def __init__(
        self,
        graph,
        runtime=None,
        journal_path=None,
        interval=0.2,
        rule_cap=60,
        include_rules=True,
        truncate=True,
        source_note=None,
    ):
        self.graph = graph
        self.runtime = runtime
        self.journal_path = journal_path or DEFAULT_JOURNAL
        self.interval = interval
        self.digest = GraphDigest(
            graph, runtime=runtime, rule_cap=rule_cap, include_rules=include_rules
        )
        self.stream = EventStream(source={"note": source_note} if source_note else None)
        self.truncate = truncate
        self._nodes = {}
        self._edges = {}
        self._counts = None
        self._counts_interval = 4.0
        self._last_counts_at = 0.0
        self._lock = threading.Lock()
        self._thread = None
        self._stop_requested = threading.Event()
        self.events_written = 0
        self.polls = 0
        self.errors = []
        self._handle = None

    # -- lifecycle --------------------------------------------------------
    def start(self):
        directory = os.path.dirname(self.journal_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        mode = "w" if self.truncate else "a"
        self._handle = open(self.journal_path, mode, encoding="utf-8")
        self._write(
            self.stream.start(
                machine=machine_identity(),
                journal=os.path.abspath(self.journal_path),
                note="observer started; state at start follows",
            )
        )
        self.poll_once()
        self._thread = threading.Thread(
            target=self._run, name="hypergraph-observation-tap", daemon=True
        )
        self._thread.start()
        return self

    def stop(self, reason="observer stopped"):
        self._stop_requested.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=max(1.0, self.interval * 4))
        with self._lock:
            if self._handle is not None:
                self.poll_locked()
                self._write(self.stream.stop(reason))
                try:
                    self._handle.flush()
                    os.fsync(self._handle.fileno())
                except OSError:
                    pass
                self._handle.close()
                self._handle = None
        return self

    # -- polling ----------------------------------------------------------
    def _run(self):
        while not self._stop_requested.wait(self.interval):
            try:
                with self._lock:
                    self.poll_locked()
            except Exception as error:  # a broken poll must never kill the script
                with self._lock:
                    self.errors.append(repr(error))
                    self._write(
                        self.stream._stamp(
                            {"type": "observer.error", "error": repr(error)}
                        )
                    )

    def poll_once(self):
        """One observation tick. Public so tests can drive it deterministically."""
        with self._lock:
            return self.poll_locked()

    def poll_locked(self):
        if self._handle is None and self.truncate is False:
            return 0
        self.polls += 1
        read = self.digest.read()
        nodes = read["nodes"]
        edges = read["edges"]
        added_nodes = [item for key, item in nodes.items() if key not in self._nodes]
        added_edges = [item for key, item in edges.items() if key not in self._edges]
        removed_nodes = [key for key in self._nodes if key not in nodes]
        removed_edges = [key for key in self._edges if key not in edges]

        written = 0
        for record in self.stream.added(added_nodes, added_edges):
            self._write(record)
            written += 1
        for record in self.stream.removed(removed_nodes, removed_edges):
            self._write(record)
            written += 1
        # Additions carry their own news. Root counts are a slow heartbeat, so a
        # recording does not double in length explaining what the items said.
        now = time.monotonic()
        heartbeat = self._counts is None or (now - self._last_counts_at) >= self._counts_interval
        self._counts = read["counts"]
        if heartbeat:
            self._write(self.stream.counts(read["counts"]))
            written += 1
            self._last_counts_at = now

        self._nodes = nodes
        self._edges = edges
        return written

    # -- output -----------------------------------------------------------
    def _write(self, record):
        if self._handle is None:
            return
        self._handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        self._handle.flush()
        self.events_written += 1

    def status(self):
        return {
            "journal": os.path.abspath(self.journal_path),
            "events": self.events_written,
            "polls": self.polls,
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "errors": list(self.errors),
        }


_ACTIVE = []


def observe(runtime_or_graph, journal_path=None, **options):
    """Observe a runtime or a hypergraph until the process exits.

    ``runtime_or_graph`` is a ``MachineRuntime`` (preferred: it can render its
    compiled rule chain) or a bare ``Hypergraph``.
    """
    runtime = None
    try:
        graph = runtime_or_graph.graph
    except AttributeError:
        graph = runtime_or_graph
    else:
        runtime = runtime_or_graph
    tap = GraphObservationTap(graph, runtime=runtime, journal_path=journal_path, **options)
    tap.start()
    _ACTIVE.append(tap)
    atexit.register(tap.stop, "process exited")
    return tap


def stop_all(reason="observer stopped"):
    """Stop every tap started through :func:`observe`."""
    while _ACTIVE:
        _ACTIVE.pop().stop(reason)
