"""Read-only visualiser server for observed Machine hypergraphs.

This process is a *reader*. It imports nothing from ``cat_theo_machine``, starts
no Machine, and has no way to mutate one: its only inputs are a journal file
written by the observation tap and the session files it records itself.

    python -m cat_theo_machine.visualiser.server --port 8801

Endpoints
---------
``GET  /``                       the viewer
``GET  /api/status``             journal, recorder and state summary
``GET  /api/state``              current observed hypergraph as JSON
``GET  /api/events?from=N``      server-sent events, replaying from ``N`` then live
``GET  /api/sessions``           recorded sessions
``POST /api/recording/start``    begin recording what the journal is producing
``POST /api/recording/stop``     finish and save the recording
``GET  /api/sessions/<id>``      one session, ready for replay
``DELETE /api/sessions/<id>``    remove a recording
"""
import argparse
import collections
import json
import os
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .sessions import SessionStore
from .state import GraphState

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
DEFAULT_JOURNAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run", "observed.jsonl")
DEFAULT_PORT = 8801
DEFAULT_HOST = "0.0.0.0"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


class Subscriber:
    """One server-sent-events client's backlog."""

    def __init__(self):
        self.condition = threading.Condition()
        self.pending = []
        self.closed = False
        self.dropped = 0

    def push(self, event):
        with self.condition:
            if len(self.pending) > 20000:
                del self.pending[:10000]
                self.dropped += 10000
            self.pending.append(event)
            self.condition.notify_all()

    def drain(self, timeout):
        with self.condition:
            if not self.pending and not self.closed:
                self.condition.wait(timeout)
            items = self.pending
            self.pending = []
            return items

    def close(self):
        with self.condition:
            self.closed = True
            self.condition.notify_all()


class JournalFollower(threading.Thread):
    """Tail the observation journal and rebuild state from it.

    A journal is one observed run: the tap truncates it when a new run starts.
    Truncation is detected by size, so a restarted Machine is picked up as a new
    session instead of being appended to the old one.
    """

    def __init__(self, path, poll_interval=0.2, on_event=None):
        super().__init__(name="visualiser-journal-follower", daemon=True)
        self.path = path
        self.poll_interval = poll_interval
        self.on_event = on_event
        self.state = GraphState()
        self.offset = 0
        self.recent = collections.deque(maxlen=5000)
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._subscribers = []
        self.session_events = 0
        self.resets = 0

    # -- subscribers ------------------------------------------------------
    def subscribe(self):
        subscriber = Subscriber()
        with self._lock:
            self._subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber):
        with self._lock:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)
        subscriber.close()

    def _broadcast(self, event):
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            subscriber.push(event)

    # -- file reading -----------------------------------------------------
    def _reset(self):
        self.state = GraphState()
        self.offset = 0
        self.recent.clear()
        self.resets += 1
        self._broadcast(
            {
                "type": "journal.rotated",
                "t": time.time(),
                "seq": -1,
                "reason": "the journal was truncated by a new Machine run",
            }
        )

    def read_available(self):
        """Read every complete line appended since the last read."""
        events = []
        try:
            size = os.path.getsize(self.path)
        except OSError:
            return events
        if size < self.offset:
            self._reset()
        if size == self.offset:
            return events
        try:
            with open(self.path, "rb") as handle:
                handle.seek(self.offset)
                chunk = handle.read(size - self.offset)
        except OSError:
            return events
        consumed = chunk.rfind(b"\n")
        if consumed < 0:
            return events
        payload = chunk[: consumed + 1]
        self.offset += len(payload)
        for line in payload.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            self.state.apply(event)
            self.recent.append(event)
            self.session_events += 1
            events.append(event)
        for event in events:
            self._broadcast(event)
            if self.on_event is not None:
                try:
                    self.on_event(event)
                except Exception as error:  # a recorder failure must not stop the feed
                    self.state.errors.append(repr(error))
        return events

    def run(self):
        while not self._stop.wait(self.poll_interval):
            try:
                self.read_available()
            except Exception as error:  # a follower must survive a bad journal
                self.state.errors.append(repr(error))

    def stop(self):
        self._stop.set()

    def status(self):
        exists = os.path.exists(self.path)
        return {
            "journal": os.path.abspath(self.path),
            "journal_exists": exists,
            "journal_bytes": os.path.getsize(self.path) if exists else 0,
            "offset": self.offset,
            "resets": self.resets,
            "events_seen": self.session_events,
            "state": self.state.summary(),
        }


class Recorder:
    """Copies the live event stream into a replayable session file.

    Recording is a visualiser-side act: the Machine is untouched, and nothing is
    written into its process. The recording opens with a checkpoint of the state
    that existed when the user pressed record, so it can be replayed alone.
    """

    def __init__(self, store, follower):
        self.store = store
        self.follower = follower
        self.active = False
        self.session_id = None
        self.events = []
        self.started_at = None
        self.meta = {}
        self._lock = threading.Lock()

    def start(self, name=None, note=None):
        with self._lock:
            if self.active:
                return {"active": True, "id": self.session_id, "error": "already recording"}
            session_id = self.store.new_id(name)
            state = self.follower.state
            self.started_at = time.time()
            checkpoint = state.checkpoint_events(when=self.started_at)
            self.session_id = session_id
            self.events = list(checkpoint)
            self.meta = {
                "id": session_id,
                "name": name or session_id,
                "note": note,
                "recorded_at": self.started_at,
                "recorded_at_text": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.started_at)),
                "checkpoint_events": len(checkpoint),
                "journal": os.path.abspath(self.follower.path),
                "machine": state.machine,
                "source": state.source,
                "state_at_start": {
                    "nodes": len(state.nodes),
                    "edges": len(state.edges),
                },
            }
            self.active = True
            return {"active": True, "id": session_id, "checkpoint_events": len(checkpoint)}

    def observe(self, event):
        with self._lock:
            if not self.active:
                return
            kind = event.get("type")
            if kind in (
                "nodes.added",
                "edges.added",
                "items.removed",
                "counts",
                "observer.error",
                "journal.rotated",
            ):
                self.events.append(event)

    def stop(self):
        with self._lock:
            if not self.active:
                return {"active": False, "error": "not recording"}
            stopped_at = time.time()
            stop_event = {
                "v": 1,
                "seq": -1,
                "t": round(stopped_at, 6),
                "type": "session.stop",
                "reason": "recording stopped",
            }
            self.events.append(stop_event)
            meta = dict(self.meta)
            meta["stopped_at"] = stopped_at
            meta["stopped_at_text"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(stopped_at)
            )
            meta["duration"] = round(stopped_at - self.started_at, 3)
            meta["events"] = len(self.events)
            meta["final_state"] = {
                "nodes": len(self.follower.state.nodes),
                "edges": len(self.follower.state.edges),
            }
            path = self.store.save(self.session_id, meta, self.events)
            result = {
                "active": False,
                "id": self.session_id,
                "path": path,
                "events": len(self.events),
                "meta": meta,
            }
            self.active = False
            self.events = []
            self.session_id = None
            return result

    def status(self):
        return {
            "active": self.active,
            "id": self.session_id,
            "events": len(self.events),
            "started_at": self.started_at,
        }


class VisualiserServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, journal_path, session_dir, web_dir=WEB_DIR):
        self.store = SessionStore(session_dir)
        self.follower = JournalFollower(journal_path)
        self.recorder = Recorder(self.store, self.follower)
        self.follower.on_event = self.recorder.observe
        self.web_dir = web_dir
        self.journal_path = journal_path
        super().__init__(address, handler)

    def start_following(self):
        self.follower.start()
        return self

    def shutdown(self):
        self.follower.stop()
        super().shutdown()


class VisualiserHandler(BaseHTTPRequestHandler):
    server_version = "CTMVisualiser/1.0"

    # -- helpers ----------------------------------------------------------
    def _json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, message, status=400):
        self._json({"error": message}, status=status)

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def _static(self, path):
        if path == "/":
            path = "/index.html"
        relative = path.lstrip("/")
        if ".." in relative.split("/"):
            self._error("path escapes the web root", status=403)
            return
        full = os.path.join(self.server.web_dir, relative)
        if not os.path.isfile(full):
            self._error("not found: " + relative, status=404)
            return
        extension = os.path.splitext(full)[1].lower()
        with open(full, "rb") as handle:
            body = handle.read()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(extension, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # -- routes -----------------------------------------------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/status":
            self._json(
                {
                    "journal": self.server.follower.status(),
                    "recording": self.server.recorder.status(),
                    "sessions_dir": self.server.store.root,
                    "web_dir": self.server.web_dir,
                    "server_time": time.time(),
                }
            )
            return
        if path == "/api/state":
            self._json(self.server.follower.state.to_export())
            return
        if path == "/api/events":
            self._stream(query)
            return
        if path == "/api/sessions":
            self._json({"sessions": self.server.store.listing()})
            return
        if path.startswith("/api/sessions/"):
            session_id = urllib.parse.unquote(path[len("/api/sessions/"):])
            try:
                self._json(self.server.store.load(session_id))
            except FileNotFoundError:
                self._error("no such session: " + session_id, status=404)
            except ValueError as error:
                self._error(str(error), status=422)
            return
        self._static(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        body = self._body()
        if parsed.path == "/api/recording/start":
            self._json(
                self.server.recorder.start(name=body.get("name"), note=body.get("note"))
            )
            return
        if parsed.path == "/api/recording/stop":
            self._json(self.server.recorder.stop())
            return
        self._error("no such endpoint", status=404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/sessions/"):
            session_id = urllib.parse.unquote(parsed.path[len("/api/sessions/"):])
            removed = self.server.store.delete(session_id)
            self._json({"removed": removed, "id": session_id})
            return
        self._error("no such endpoint", status=404)

    def _stream(self, query):
        try:
            start = int((query.get("from") or ["0"])[0])
        except ValueError:
            start = 0
        subscriber = self.server.follower.subscribe()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            # Replay anything after the client's last known sequence, so the gap
            # between fetching /api/state and opening this stream cannot lose events.
            for event in list(self.server.follower.recent):
                # Journals carry integer sequences; a foreign or truncated line
                # is not replayed rather than allowed to break the stream.
                try:
                    newer = event.get("seq") > start
                except TypeError:
                    newer = False
                if newer:
                    self._send_event(event)
            while True:
                events = subscriber.drain(timeout=15.0)
                if not events:
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    if subscriber.closed:
                        break
                    continue
                for event in events:
                    self._send_event(event)
                if subscriber.closed:
                    break
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.server.follower.unsubscribe(subscriber)

    def _send_event(self, event):
        payload = json.dumps(event, separators=(",", ":"))
        self.wfile.write(b"data: " + payload.encode("utf-8") + b"\n\n")
        self.wfile.flush()

    def log_message(self, format, *args):
        print("visualiser:", format % args)


def build_server(
    host=DEFAULT_HOST,
    port=DEFAULT_PORT,
    journal_path=None,
    session_dir=None,
    web_dir=WEB_DIR,
    start_following=True,
):
    journal_path = os.path.abspath(journal_path or os.path.expanduser(
        os.environ.get("CTM_VIS_JOURNAL", DEFAULT_JOURNAL)
    ))
    session_dir = os.path.abspath(session_dir or SESSION_DIR)
    server = VisualiserServer((host, port), VisualiserHandler, journal_path, session_dir, web_dir)
    if start_following:
        server.start_following()
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only Machine hypergraph visualiser")
    parser.add_argument("--host", default=DEFAULT_HOST, help="bind address (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--journal", default=None, help="observation journal to follow")
    parser.add_argument("--sessions", default=None, help="directory for recorded sessions")
    parser.add_argument("--open", action="store_true", help="open a browser on start")
    args = parser.parse_args(argv)

    server = build_server(
        host=args.host,
        port=args.port,
        journal_path=args.journal,
        session_dir=args.sessions,
    )
    host, port = server.server_address[0], server.server_address[1]
    print("visualiser listening on http://" + str(host) + ":" + str(port) + "/")
    print("observing journal: " + server.journal_path)
    print("session directory: " + server.store.root)
    if args.open:
        import webbrowser

        webbrowser.open("http://127.0.0.1:" + str(port) + "/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("visualiser stopped")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
