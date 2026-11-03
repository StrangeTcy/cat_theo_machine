"""Server-side reconstruction of an observed hypergraph.

The same event vocabulary the tap writes is replayed here, so the server can
answer "what does the graph look like right now" without importing the Machine.
This module deliberately imports nothing from ``cat_theo_machine``: the
visualiser is a reader of journals, not a participant in Machine execution.
"""
from .protocol import EVENT_VERSION


class GraphState:
    """Node/hyperedge tables rebuilt from journal events."""

    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.counts = {}
        self.last_seq = -1
        self.applied = 0
        self.started_at = None
        self.machine = {}
        self.source = {}
        self.stopped = None
        self.errors = []
        self.rotations = 0

    def apply(self, event):
        """Apply one event. Unknown event types are counted, never fatal."""
        kind = event.get("type")
        seq = event.get("seq")
        if seq is not None:
            # Journals carry integer sequences; a malformed one is ignored rather
            # than allowed to break the rebuild.
            try:
                self.last_seq = int(seq)
            except (TypeError, ValueError):
                pass
        if kind == "session.start":
            self.started_at = event.get("t")
            self.machine = event.get("machine") or {}
            self.source = event.get("source") or {}
            self.stopped = None
        elif kind == "nodes.added":
            for item in event.get("items", []):
                self.nodes[item["id"]] = item
        elif kind == "edges.added":
            for item in event.get("items", []):
                self.edges[item["id"]] = item
        elif kind == "items.removed":
            for node_id in event.get("nodes", []):
                self.nodes.pop(node_id, None)
            for edge_id in event.get("edges", []):
                self.edges.pop(edge_id, None)
        elif kind == "counts":
            self.counts = event.get("counts") or {}
        elif kind == "session.stop":
            self.stopped = event.get("reason") or "stopped"
        elif kind == "observer.error":
            self.errors.append(event.get("error") or "unknown observer error")
        elif kind == "journal.rotated":
            self.rotations += 1
        self.applied += 1
        return event

    def checkpoint_events(self, when=None):
        """Events that rebuild this state from empty -- used to open a recording.

        A recording must be replayable on its own, so it begins with the state
        that existed when the user pressed record.
        """
        events = []
        if self.nodes:
            events.append(
                {
                    "v": EVENT_VERSION,
                    "seq": -1,
                    "t": when,
                    "type": "nodes.added",
                    "checkpoint": True,
                    "items": list(self.nodes.values()),
                }
            )
        if self.edges:
            events.append(
                {
                    "v": EVENT_VERSION,
                    "seq": -1,
                    "t": when,
                    "type": "edges.added",
                    "checkpoint": True,
                    "items": list(self.edges.values()),
                }
            )
        return events

    def summary(self):
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "counts": self.counts,
            "last_seq": self.last_seq,
            "applied": self.applied,
            "started_at": self.started_at,
            "stopped": self.stopped,
            "machine": self.machine,
            "source": self.source,
            "errors": self.errors[-5:],
            "rotations": self.rotations,
        }

    def to_export(self):
        """A standalone JSON document describing the current observable state."""
        return {
            "format": "ctm-hypergraph-view",
            "version": EVENT_VERSION,
            "kind": "observed-state",
            "summary": self.summary(),
            "nodes": list(self.nodes.values()),
            "edges": list(self.edges.values()),
        }
