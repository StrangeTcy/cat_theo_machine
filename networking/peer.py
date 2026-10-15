"""The mesh peer: one process, one mTLS listener, one job at a time.

Topology follows the machine's existing worker model: one coordinator hands out
work, workers dial in over mutual TLS and stay connected. What makes it a *mesh*
rather than a queue is that workers also talk to each other directly -- an idle
peer opens its own mTLS connection to a busy peer and asks for one of its queued
jobs (`STEAL_REQUEST` / `STEAL_GRANT`), so work moves sideways without the
coordinator in the middle.

Invariants this module owns, all of them observable from outside:

* **One writer per scope.** A job's scope -- its declared hypergraph content ids
  and its result artifact -- is leased. The coordinator will not hand out a second
  lease for a live scope, and a worker refuses an offer for a scope it already
  holds. A stolen job carries its lease with it, so ownership moves; a peer that
  dies has its leases reclaimed.
* **Monotonicity.** A peer refuses a job whose per-scope sequence is not greater
  than the highest it has completed for that scope (`refused-stale`), so a result
  computed against older state can never overwrite newer state. This is the mesh
  counterpart of the kernel's `GraphVersion` monotonicity and the rule W17's
  snapshot broadcast will build on.
* **Nothing silently lost.** Every job reaches exactly one terminal record -- a
  result, or a failure with a reason. A worker killed mid-job has its leases
  reclaimed and its job re-dispatched or recorded as `worker-lost`.

Threads per peer: one accept loop, one reader and one writer per connection, one
heartbeat loop, plus (coordinator) a dispatch loop and a liveness loop, and
(worker) a job loop and a steal loop. Shared state sits behind one lock; no loop
blocks on I/O while holding it.

Beyond one filesystem (W20). Three switches let a peer sit behind a NAT, a
tunnel or a notebook with no inbound port, without changing any of the above:
`artifacts="wire"` moves job files over the coordinator link as digest-named
bytes instead of paths on a shared mount (`networking/artifacts.py`);
`inbound=False` runs a worker with no listener at all -- it dials the
coordinator and can still steal from reachable peers, and nobody ever dials it;
`verify="identity"` checks the dialled peer's certificate by common name under
the same CA pin rather than by hostname, which is what an address like
`0.tcp.ngrok.io:12345` or a tailnet IP needs. Every one of them is observable in
the ledger, and the loopback defaults are unchanged.
"""

from __future__ import annotations

import os
import queue
import socket
import ssl
import sys
import threading
import time

from . import artifacts as Artifacts
from . import framing, protocol
from .identity import bind_listener, parse_address, peer_common_name


class Connection:
    """A live, authenticated connection plus its writer thread."""

    def __init__(self, sock, peer_id, on_eof=None, log=None, transient=False):
        self.sock = sock
        self.peer_id = peer_id
        self.transient = transient  # one-shot connections (steal requests) are not members
        self.outbox = queue.Queue()
        # Messages accepted by `send` and not yet *written*: queue.Queue.empty() is
        # not enough, because a writer that has just dequeued a message still has
        # it in hand. Closing the socket under it loses that message -- which is
        # how a coordinator's shutdown notice used to never reach its members.
        self._write_lock = threading.Lock()
        self._queued = 0
        self.closed = threading.Event()
        self.error = None       # the failure that ended the writer, if any
        self.closed_by = ""     # what closed the connection, for the ledger
        self._on_eof = on_eof
        self.on_close = None        # callback(connection, reason) for the ledger
        self._log = log or (lambda text: None)
        self._writer = threading.Thread(target=self._write_loop, name="mesh-writer-%s" % peer_id, daemon=True)
        self._writer.start()

    def send(self, message):
        if self.closed.is_set():
            return False
        with self._write_lock:
            self._queued += 1
        self.outbox.put(message)
        return True

    @property
    def flushed(self):
        """True when every accepted message has reached the socket."""
        with self._write_lock:
            return self._queued == 0

    def _write_loop(self):
        while not self.closed.is_set():
            try:
                message = self.outbox.get(timeout=0.2)
            except queue.Empty:
                continue
            if message is None:
                break
            try:
                framing.send_frame(self.sock, message)
            except OSError as error:
                self.error = error
                with self._write_lock:
                    self._queued -= 1
                self.close("writer:%s" % error.__class__.__name__)
                return
            with self._write_lock:
                self._queued -= 1

    def read(self, timeout=None):
        return framing.recv_frame(self.sock, timeout=timeout)

    def close(self, reason=""):
        if self.closed.is_set():
            return
        if not reason:
            # A connection that goes away without a reason costs hours to debug:
            # record who closed it while the answer is still on the stack.
            try:
                frames = []
                frame = sys._getframe(1)
                for _ in range(4):
                    if frame is None:
                        break
                    frames.append("%s:%d" % (frame.f_code.co_name, frame.f_lineno))
                    frame = frame.f_back
                reason = ">".join(frames)
            except Exception:
                reason = "unknown"
        self.closed_by = reason
        self.closed.set()
        self.outbox.put(None)
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass
        if self.on_close is not None:
            try:
                self.on_close(self, self.closed_by)
            except Exception as error:  # a broken callback must not kill a loop
                self._log("connection close callback failed: %r" % (error,))
        if self._on_eof is not None:
            try:
                self._on_eof(self)
            except Exception as error:  # a broken callback must not kill a loop
                self._log("connection eof callback failed: %r" % (error,))


class MeshPeer:
    ROLE_COORDINATOR = "coordinator"
    ROLE_WORKER = "worker"

    def __init__(
        self,
        identity,
        role=ROLE_WORKER,
        runner=None,
        heartbeat_interval=0.4,
        peer_timeout=20.0,
        max_attempts=2,
        offer_ack_timeout=10.0,
        steal_enabled=True,
        redispatch_on_crash=True,
        log=None,
        peer_id=None,
        artifacts=protocol.ARTIFACTS_SHARED,
        artifact_dir=None,
        inbound=True,
        verify=protocol.VERIFY_HOSTNAME,
        expect_coordinator=None,
        fetch_timeout=180.0,
    ):
        self.identity = identity
        self.role = role
        self.runner = runner
        if artifacts not in (protocol.ARTIFACTS_SHARED, protocol.ARTIFACTS_WIRE):
            raise ValueError("artifacts must be %r or %r" % (protocol.ARTIFACTS_SHARED, protocol.ARTIFACTS_WIRE))
        if verify not in (protocol.VERIFY_HOSTNAME, protocol.VERIFY_IDENTITY):
            raise ValueError("verify must be %r or %r" % (protocol.VERIFY_HOSTNAME, protocol.VERIFY_IDENTITY))
        self.artifacts = artifacts
        self.artifact_dir = artifact_dir
        if artifacts == protocol.ARTIFACTS_WIRE and role == self.ROLE_WORKER and not artifact_dir:
            raise ValueError("a wire-mode worker needs an artifact_dir of its own")
        self.inbound = bool(inbound)
        self.verify = verify
        self.expect_coordinator = expect_coordinator
        self.fetch_timeout = fetch_timeout
        self.heartbeat_interval = heartbeat_interval
        self.peer_timeout = peer_timeout
        self.max_attempts = max_attempts
        self.offer_ack_timeout = offer_ack_timeout
        self.steal_enabled = steal_enabled
        self.redispatch_on_crash = redispatch_on_crash
        self._log = log or (lambda text: None)
        self.peer_id = peer_id or ("%s-%s" % (identity.common_name, os.urandom(3).hex()))
        self.address = ""

        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._listener = None
        self._threads = []
        self._connections = {}          # member peer_id -> Connection (accepted or dialled)
        self._coordinator_connection = None
        self._coordinator_id = ""
        self._members = {}              # peer_id -> member record
        self._jobs = {}                 # job_id -> Job (coordinator)
        self._job_owner = {}            # job_id -> peer_id holding it
        self._job_state = {}            # job_id -> state string
        self._queue = []                # accepted here, not started: stealable
        self._running = None
        self._local_leases = {}         # scope_key -> Lease held by this peer
        self._foreign_leases = {}       # scope_key -> Lease held by another peer
        self._completed_sequence = {}   # scope_key -> highest sequence completed here
        self._results = {}              # job_id -> terminal record
        self._ledger = []
        self._sequence = {}             # scope_key -> next sequence (coordinator)
        self._steals = 0
        self._steal_attempts = 0
        self._redispatch_count = 0
        self._offered_at = {}           # job_id -> when its offer went out
        self._acknowledged = set()      # job_ids whose last offer was answered
        self._retry_after = {}          # job_id -> when it may be offered again
        self._coordinator_address = ""  # where a worker rejoins after a drop
        # W20: artifact transfers in flight (either role), what a worker is
        # waiting to receive, which fetches came back empty, and when an
        # unreachable peer may be dialled again for a steal.
        self._receiver = Artifacts.ArtifactReceiver()
        self._result_authority = Artifacts.ResultAuthority(self._jobs)
        self._input_authority = Artifacts.InputAuthority(self._jobs)
        self._awaited = {}              # local path -> threading.Event (worker, wire mode)
        self._fetch_failures = {}       # local path -> reason reported by the coordinator
        self._received_sha256 = {}      # destination path -> sha256 of the last complete transfer
        self._steal_backoff = {}        # peer_id -> time before which it is not dialled again

    # ------------------------------------------------------------------ helpers

    def _record(self, event, job=None, peer_id="", detail="", **extra):
        entry = {
            "ts": round(time.time(), 3),
            "event": event,
            "job_id": job.job_id if job is not None else "",
            "peer_id": peer_id,
            "detail": detail,
        }
        entry.update(extra)
        with self._lock:
            self._ledger.append(entry)
        return entry

    def events(self, event=None):
        with self._lock:
            entries = list(self._ledger)
        if event is None:
            return entries
        return [entry for entry in entries if entry["event"] == event]

    def outcome(self, job_id):
        with self._lock:
            return dict(self._results[job_id]) if job_id in self._results else None

    def members(self):
        with self._lock:
            return {peer_id: dict(record) for peer_id, record in self._members.items()}

    def load(self):
        with self._lock:
            return {"queued": len(self._queue), "running": 1 if self._running is not None else 0}

    def terminal_job_ids(self):
        with self._lock:
            return sorted(self._results.keys())

    def pending_job_ids(self):
        with self._lock:
            return sorted(job_id for job_id, state in self._job_state.items() if state not in ("done", "failed"))

    def summary(self):
        with self._lock:
            states = {}
            for state in self._job_state.values():
                states[state] = states.get(state, 0) + 1
            completed = [
                record for record in self._results.values() if protocol.status_is_success(record["status"])
            ]
            failed = [
                record for record in self._results.values() if not protocol.status_is_success(record["status"])
            ]
            return {
                "peer_id": self.peer_id,
                "role": self.role,
                "completed": len(completed),
                "failed": len(failed),
                "terminal": len(self._results),
                "job_states": states,
                "steals": self._steals,
                "steal_attempts": self._steal_attempts,
                "redispatches": self._redispatch_count,
                "live_leases": len(self._foreign_leases),
                "local_leases": len(self._local_leases),
                "members": sorted(self._members.keys()),
            }

    # --------------------------------------------------------------- lifecycle

    def start(self, host="127.0.0.1", port=0):
        if self.inbound:
            self._listener = bind_listener(host, port)
            bound_host, bound_port = self._listener.getsockname()
            self.address = "%s:%d" % (bound_host, bound_port)
            self._spawn(self._accept_loop, "mesh-accept")
        else:
            if self.role == self.ROLE_COORDINATOR:
                raise ValueError("a coordinator must accept connections; inbound=False is for workers")
            # No listener, no address: nobody can dial this peer, and the member
            # record it announces says so (an empty address is what the steal
            # loop already skips). It can still dial out -- to join, and to steal.
            self._listener = None
            self.address = ""
            self._record("inbound-disabled", peer_id=self.peer_id, detail="no listener; outbound connections only")
        self._spawn(self._heartbeat_loop, "mesh-heartbeat")
        if self.role == self.ROLE_COORDINATOR:
            self._spawn(self._dispatch_loop, "mesh-dispatch")
            self._spawn(self._liveness_loop, "mesh-liveness")
            self._spawn(self._watchdog_loop, "mesh-watchdog")
        else:
            self._spawn(self._job_loop, "mesh-jobs")
            self._spawn(self._reconnect_loop, "mesh-reconnect")
            if self.steal_enabled:
                self._spawn(self._steal_loop, "mesh-steal")
        return self.address

    def _stop_now(self, reason):
        """Stop this peer, recording where the stop came from.

        A peer that stops mid-run is the difference between "the peer went away"
        and "something in this process cancelled it", and only the ledger can
        tell the two apart afterwards.
        """
        try:
            frame = sys._getframe(1)
            where = "%s:%d" % (frame.f_code.co_name, frame.f_lineno)
        except Exception:
            where = "unknown"
        self._record("peer-stop", peer_id=self.peer_id, detail="%s (%s)" % (reason, where))
        self._stop.set()

    def _spawn(self, target, name, *args):
        thread = threading.Thread(target=target, name=name, args=args, daemon=True)
        thread.start()
        self._threads.append(thread)
        return thread

    def join(self, coordinator_address, timeout=15.0):
        """Dial the coordinator, authenticate, register, and stay connected."""
        host, port = parse_address(coordinator_address)
        sock = self._dial(host, port, timeout, expected_name=self.expect_coordinator, purpose="join")
        sock.settimeout(None)
        connection = Connection(sock, self.peer_id, on_eof=self._on_coordinator_eof, log=self._log)
        connection.on_close = self._note_connection_closed
        previous = self._coordinator_connection
        self._coordinator_connection = connection
        self._coordinator_address = coordinator_address
        if previous is not None and previous is not connection:
            previous.close("replaced by a fresh join")
        connection.send(
            protocol.message(
                protocol.JOIN,
                peer_id=self.peer_id,
                address=self.address,
                reachable=bool(self.address),
                common_name=self.identity.common_name,
                roles=[self.role],
                modes=list(self.runner.supported_modes) if self.runner is not None else [],
                load=self.load(),
                artifacts=self.artifacts,
            )
        )
        welcome = connection.read(timeout=timeout)
        if welcome is None:
            raise RuntimeError("coordinator closed the connection during join")
        if welcome.get("kind") == protocol.REJECT:
            raise RuntimeError("join rejected: %s" % welcome.get("reason", "unknown"))
        if welcome.get("kind") != protocol.WELCOME:
            raise RuntimeError("unexpected reply to join: %r" % (welcome.get("kind"),))
        self._coordinator_id = welcome.get("coordinator_id", "coordinator")
        with self._lock:
            for record in welcome.get("members", []):
                self._remember_member(record, note="known by coordinator")
            self._members[self._coordinator_id] = {
                "peer_id": self._coordinator_id,
                "address": welcome.get("address", coordinator_address),
                "roles": [self.ROLE_COORDINATOR],
                "modes": [],
                "last_seen": time.time(),
                "load": {"queued": 0, "running": 0},
            }
        self._record("joined", peer_id=self.peer_id, detail=coordinator_address)
        self._spawn(self._reader_loop, "mesh-coord-reader", connection)
        return welcome

    def _dial(self, host, port, timeout, expected_name=None, purpose="dial"):
        """Open and authenticate an outbound mTLS connection.

        Under `verify="hostname"` the certificate must name the address dialled
        (loopback certificates carry 127.0.0.1 / localhost). Under
        `verify="identity"` the CA pin is unchanged -- a certificate from any
        other CA still fails the handshake -- but the name checked is the
        certificate's common name against `expected_name`, because a tunnel
        endpoint or a tailnet address is not something a leaf can be issued for
        in advance. A mismatch closes the socket and is reported as an
        `identity-mismatch` event rather than a TLS error, so the ledger says
        which peer answered.
        """
        identity_mode = self.verify == protocol.VERIFY_IDENTITY
        context = self.identity.client_context(check_hostname=not identity_mode)
        raw = socket.create_connection((host, port), timeout=timeout)
        raw.settimeout(timeout)
        try:
            sock = context.wrap_socket(raw, server_hostname=host)
        except (ssl.SSLError, OSError):
            raw.close()
            raise
        if identity_mode and expected_name:
            actual = peer_common_name(sock)
            if actual != expected_name:
                self._record(
                    "identity-mismatch",
                    peer_id=self.peer_id,
                    detail="%s: expected %s, certificate says %s" % (purpose, expected_name, actual or "-"),
                )
                try:
                    sock.close()
                except OSError:
                    pass
                raise RuntimeError("peer identity mismatch on %s: expected %s, got %s" % (purpose, expected_name, actual or "-"))
        return sock

    def _on_coordinator_eof(self, connection):
        self._record("coordinator-lost", peer_id=self.peer_id, detail="connection closed")

    def _reconnect_loop(self):
        """Re-join the coordinator when the link to it drops.

        A worker whose connection dies is not dead: it keeps its identity, its
        queue and its running job. Re-joining costs a round trip, and the work it
        already holds is re-announced so the coordinator's picture of who owns
        what is right again -- a dropped link must never turn into a lost job.
        """
        while not self._stop.is_set():
            time.sleep(0.3)
            if self._stop.is_set():
                return
            address = self._coordinator_address
            if not address:
                continue  # never joined yet: not this loop's business
            connection = self._coordinator_connection
            if connection is not None and not connection.closed.is_set():
                continue  # the link is healthy
            try:
                self.join(address, timeout=3.0)
            except (ssl.SSLError, OSError, framing.FrameError, RuntimeError) as error:
                self._record("rejoin-failed", peer_id=self.peer_id, detail=error.__class__.__name__)
                continue
            self._record("rejoined", peer_id=self.peer_id, detail=address)
            self._announce_work()

    def _announce_work(self):
        """Tell the coordinator which jobs this worker holds -- and what it finished.

        Re-announcing queued and running work transfers ownership back to this peer.
        Replaying terminal records closes the other half of a dropped link: a job
        this worker already completed may have had its result die with the
        connection, and a result that exists must reach the coordinator (the
        handler ignores job ids it has already recorded, so a replay is harmless).
        """
        with self._lock:
            running = self._running
            queued = list(self._queue)
            finished = list(self._results.values())
        if running is not None:
            self._notify_coordinator(
                protocol.message(protocol.JOB_STARTED, job_id=running.job_id, peer_id=self.peer_id)
            )
        for job in queued:
            self._notify_coordinator(protocol.message(protocol.JOB_QUEUED, job_id=job.job_id, peer_id=self.peer_id))
        for record in finished:
            if self.artifacts == protocol.ARTIFACTS_WIRE and protocol.status_is_success(record.get("status", "")):
                # The bytes may have died with the link too: send them again
                # ahead of the replayed record. The coordinator overwrites with
                # identical bytes or, if it already has them, skips the write.
                self._upload_result(record.get("job_id", ""), record.get("result_ref", ""))
            self._notify_coordinator(protocol.message(protocol.JOB_RESULT, **record))

    def _note_connection_closed(self, connection, reason):
        """Record every close: a connection that dies must name its killer."""
        self._record(
            "connection-closed",
            peer_id=connection.peer_id,
            detail="closed_by=%s error=%r" % (reason, connection.error),
        )

    def wait_for(self, predicate, timeout=30.0, interval=0.05):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate(self):
                return True
            time.sleep(interval)
        return predicate(self)

    def wait_for_terminal(self, job_ids, timeout=240.0):
        wanted = list(job_ids)
        return self.wait_for(
            lambda peer: all(job_id in peer._results for job_id in wanted),
            timeout=timeout,
        )

    def shutdown(self, timeout=10.0):
        """Stop cleanly: tell peers, release leases, leave no job unrecorded."""
        self._receiver.abandon_all()  # half-received files are never left in place
        if self.role == self.ROLE_COORDINATOR:
            with self._lock:
                member_ids = list(self._members.keys())
            for peer_id in member_ids:
                self._send(peer_id, protocol.message(protocol.SHUTDOWN, reason="coordinator shutting down"))
            # The shutdown notice is *queued*, not yet on the wire, and closing a
            # connection abandons whatever is still in its outbox -- so a
            # coordinator that closed immediately after telling its members would
            # leave them reconnecting to a coordinator that is gone (which is how
            # a CLI worker used to linger for as long as its caller let it). Wait
            # for the writers to drain as well as for the jobs to settle.
            deadline = time.time() + min(2.0, timeout)
            while time.time() < deadline:
                with self._lock:
                    busy = [1 for state in self._job_state.values() if state in ("running", "queued", "dispatched")]
                    pending = [1 for connection in self._connections.values() if not connection.flushed]
                if not busy and not pending:
                    break
                time.sleep(0.05)
        elif self._coordinator_connection is not None:
            self._coordinator_connection.send(protocol.message(protocol.GOODBYE, peer_id=self.peer_id, reason="worker shutting down"))
        with self._lock:
            queued = list(self._queue)
            self._queue = []
            running = self._running
        for job in queued:
            self._finish_job(
                job, status=protocol.STATUS_FAILED, reason="abandoned-on-shutdown", detail="queued at shutdown", provisional=True
            )
        if running is not None:
            self._finish_job(
                running, status=protocol.STATUS_FAILED, reason="abandoned-on-shutdown", detail="running at shutdown", provisional=True
            )
        self._stop_now("shutdown")
        deadline = time.time() + min(1.0, timeout)
        while time.time() < deadline:
            with self._lock:
                pending = [1 for connection in self._connections.values() if not connection.flushed]
            if not pending:
                break
            time.sleep(0.02)
        for connection in list(self._connections.values()):
            connection.close()
        if self._coordinator_connection is not None:
            self._coordinator_connection.close()
        if self._listener is not None:
            try:
                self._listener.close()
            except OSError:
                pass
        for thread in list(self._threads):
            thread.join(timeout=1.0)
        self._record("shutdown-complete", peer_id=self.peer_id)
        return self.summary()

    # ------------------------------------------------------------ connections

    def _accept_loop(self):
        while not self._stop.is_set():
            try:
                raw, _addr = self._listener.accept()
            except OSError:
                return
            self._spawn(self._serve_connection, "mesh-serve", raw)

    def _serve_connection(self, raw):
        """Authenticate an inbound connection and read its frames until EOF.

        One reader per connection: the member reader, the steal one-shot and a
        peer's very first frame all arrive here.
        """
        try:
            sock = self.identity.server_context().wrap_socket(raw, server_side=True)
        except (ssl.SSLError, OSError) as error:
            # Unauthenticated or untrusted peers never get past the handshake.
            self._record("handshake-refused", detail=error.__class__.__name__)
            try:
                raw.close()
            except OSError:
                pass
            return
        sock.settimeout(None)
        connection = Connection(sock, peer_common_name(sock) or "unknown", log=self._log)
        connection.on_close = self._note_connection_closed
        try:
            while not self._stop.is_set() and not connection.closed.is_set():
                try:
                    message = connection.read(timeout=0.5)
                except socket.timeout:
                    continue
                if message is None:
                    break
                self._handle_message(message, connection)
        except (ssl.SSLError, OSError, framing.FrameError) as error:
            self._record(
                "reader-stopped",
                peer_id=connection.peer_id,
                detail="%s closed_by=%s" % (error.__class__.__name__, connection.closed_by or "-"),
            )
        finally:
            was_member = connection.peer_id in self._members
            self._record(
                "connection-closed",
                peer_id=connection.peer_id,
                detail="closed_by=%s error=%r member=%s" % (connection.closed_by, connection.error, was_member),
            )
            connection.close()
            if was_member and not self._stop.is_set():
                self._member_lost(connection.peer_id, "connection closed", connection=connection)

    def _reader_loop(self, connection):
        """Read frames on a connection this peer dialled (its coordinator)."""
        while not self._stop.is_set() and not connection.closed.is_set():
            try:
                message = connection.read(timeout=0.5)
            except socket.timeout:
                continue
            except (ssl.SSLError, OSError, framing.FrameError) as error:
                # A reader that stops is a peer that stops hearing work: never
                # leave that to be guessed from the absence of events.
                self._record(
                    "reader-stopped",
                    peer_id=connection.peer_id,
                    detail="%s closed_by=%s" % (error.__class__.__name__, connection.closed_by or "-"),
                )
                # A connection whose reader has stopped can never be used again:
                # close it so the reconnect watchdog knows to re-join.
                connection.close("reader:%s" % error.__class__.__name__)
                return
            if message is None:
                self._record(
                    "reader-stopped",
                    peer_id=connection.peer_id,
                    detail="peer closed the connection (closed_by=%s)" % (connection.closed_by or "-"),
                )
                connection.close("reader:eof")
                return
            self._handle_message(message, connection)

    def _handle_message(self, message, connection):
        kind = message.get("kind")
        if message.get("protocol_version") != protocol.PROTOCOL_VERSION:
            connection.send(protocol.message(protocol.REJECT, reason="protocol-version"))
            return
        if kind == protocol.JOIN:
            self._handle_join(message, connection)
        elif kind == protocol.HEARTBEAT:
            self._note_heartbeat(message, connection)
        elif kind == protocol.JOB_OFFER:
            self._handle_job_offer(message, connection)
        elif kind == protocol.JOB_RESULT:
            self._handle_job_result(message)
        elif kind in (protocol.JOB_STARTED, protocol.JOB_QUEUED):
            self._note_job_progress(message)
        elif kind == protocol.JOB_DECLINED:
            self._handle_job_declined(message)
        elif kind == protocol.STEAL_REQUEST:
            self._handle_steal_request(message, connection)
        elif kind == protocol.ARTIFACT_FETCH:
            self._handle_artifact_fetch(message, connection)
        elif kind == protocol.ARTIFACT_BEGIN:
            self._handle_artifact_begin(message, connection)
        elif kind == protocol.ARTIFACT_CHUNK:
            self._handle_artifact_chunk(message, connection)
        elif kind == protocol.ARTIFACT_END:
            self._handle_artifact_end(message, connection)
        elif kind == protocol.ARTIFACT_MISSING:
            self._handle_artifact_missing(message)
        elif kind == protocol.ARTIFACT_REFUSED:
            self._record(
                "artifact-refused-by-peer",
                peer_id=connection.peer_id,
                detail="%s: %s" % (message.get("ref", "") or message.get("transfer_id", ""), message.get("reason", "")),
            )
        elif kind == protocol.SHUTDOWN:
            self._record("shutdown-requested", peer_id=connection.peer_id)
            self._stop_now("shutdown-requested")
            connection.close()
        elif kind == protocol.GOODBYE:
            if message.get("peer_id"):
                self._member_lost(message["peer_id"], "goodbye")
        elif kind == protocol.REJECT:
            self._record("rejected", peer_id=message.get("peer_id", ""), detail=message.get("reason", ""))
        else:
            self._record("unknown-message", detail=str(kind))

    def _handle_join(self, message, connection):
        if self.role != self.ROLE_COORDINATOR:
            connection.send(protocol.message(protocol.REJECT, reason="not-a-coordinator"))
            return
        peer_id = message.get("peer_id") or peer_common_name(connection.sock)
        record = {
            "peer_id": peer_id,
            "address": message.get("address", "") if message.get("reachable", True) else "",
            "reachable": bool(message.get("reachable", True)) and bool(message.get("address", "")),
            "artifacts": message.get("artifacts", protocol.ARTIFACTS_SHARED),
            "common_name": message.get("common_name", peer_common_name(connection.sock)),
            "roles": message.get("roles", [self.ROLE_WORKER]),
            "modes": message.get("modes", []),
            "direct": True,
            "last_seen": time.time(),
            "load": message.get("load", {"queued": 0, "running": 0}),
        }
        with self._lock:
            self._members[peer_id] = record
            self._connections[peer_id] = connection
            members = [dict(item) for item in self._members.values()]
        connection.peer_id = peer_id
        connection.send(
            protocol.message(
                protocol.WELCOME,
                coordinator_id=self.peer_id,
                address=self.address,
                members=members,
                heartbeat_interval=self.heartbeat_interval,
            )
        )
        self._record("member-joined", peer_id=peer_id, detail=record["address"], mode_list=record["modes"])

    def _send(self, peer_id, message):
        with self._lock:
            connection = self._connections.get(peer_id)
        if connection is None or connection.closed.is_set():
            return False
        return connection.send(message)

    def _notify_coordinator(self, message):
        connection = self._coordinator_connection
        if connection is None or connection.closed.is_set():
            return False
        return connection.send(message)

    # -------------------------------------------------------------- membership

    def _remember_member(self, record, note=""):
        peer_id = record.get("peer_id")
        if not peer_id or peer_id == self.peer_id:
            return
        self._members[peer_id] = {
            "peer_id": peer_id,
            "address": record.get("address", ""),
            "common_name": record.get("common_name", ""),
            "roles": record.get("roles", []),
            "modes": record.get("modes", []),
            "last_seen": time.time(),
            "direct": bool(record.get("direct", False)),
            "load": record.get("load", {"queued": 0, "running": 0}),
            "note": note,
        }

    def _note_heartbeat(self, message, connection):
        """Take in a heartbeat: refresh the sender's record, learn nothing else.

        No reply is sent. Heartbeats are periodic and one-directional per pair --
        the coordinator's loop tells every member it is alive (and gossips the
        digest), each worker's loop tells the coordinator it is alive -- so an
        answer would be redundant *and* unbounded: two peers answering each
        other's heartbeats answer the answers forever, at wire speed, and the
        offers and results queue up behind that storm.
        """
        peer_id = message.get("peer_id") or connection.peer_id
        with self._lock:
            record = self._members.get(peer_id)
            if record is None and peer_id != self.peer_id:
                self._remember_member(
                    {
                        "peer_id": peer_id,
                        "address": message.get("address", ""),
                        "roles": message.get("roles", []),
                        "modes": message.get("modes", []),
                        "direct": True,
                        "load": message.get("load", {}),
                    },
                    note="learned from heartbeat",
                )
                record = self._members.get(peer_id)
            if record is not None:
                record["direct"] = True
                record["last_seen"] = time.time()
                if "load" in message:
                    record["load"] = message["load"]
            # The coordinator gossips the member digest so workers can find each
            # other; that is how a peer knows whom to steal from.
            gossiped = message.get("members") or []
            for item in gossiped:
                if item.get("peer_id") == self.peer_id:
                    continue
                existing = self._members.get(item.get("peer_id"))
                if existing is None:
                    self._remember_member(item, note="gossiped")
                elif "load" in item:
                    existing["load"] = item["load"]

    def _member_lost(self, peer_id, reason, connection=None):
        with self._lock:
            if connection is not None and self._connections.get(peer_id) is not connection:
                # The peer already re-joined over a newer connection, so this
                # loss is historical: healing it again would discard live work.
                self._record("stale-loss-ignored", peer_id=peer_id, detail=reason)
                return
            record = self._members.pop(peer_id, None)
            connection = self._connections.pop(peer_id, None)
            orphaned = []
            for job_id, owner in list(self._job_owner.items()):
                if owner == peer_id:
                    orphaned.append((self._jobs.get(job_id), self._job_state.get(job_id, "")))
                    self._job_owner.pop(job_id, None)
            released = [
                self._foreign_leases.pop(key)
                for key in [key for key, lease in self._foreign_leases.items() if lease.peer_id == peer_id]
            ]
        if connection is not None:
            connection.close()
        for job, _state in orphaned:
            if job is not None:
                self._offered_at.pop(job.job_id, None)
                self._acknowledged.discard(job.job_id)
        if record is not None:
            self._record("member-lost", peer_id=peer_id, detail=reason)
        for lease in released:
            self._record("lease-released", peer_id=peer_id, job_id=lease.job_id, detail="scope reclaimed after loss")
        for job, state in orphaned:
            if job is None:
                continue
            if self.redispatch_on_crash and job.attempt < self.max_attempts and self.role == self.ROLE_COORDINATOR:
                # Ownership transfers to a peer when work *starts*, so this job
                # really was this peer's to lose. It is recovered, not merely
                # reported: the partial checkpoint is overwritten by the peer that
                # takes it over. (Exactly-once across a partition -- as opposed to
                # a clean kill -- is W17's problem, not this layer's.)
                with self._lock:
                    self._redispatch_count += 1
                    self._job_state[job.job_id] = "pending"
                job.attempt += 1
                self._record(
                    "job-redispatched",
                    job=job,
                    peer_id=peer_id,
                    detail="worker lost %s, attempt %d"
                    % ("mid-job" if state == "running" else "before start", job.attempt),
                )
            else:
                self._finish_job(
                    job, status=protocol.STATUS_FAILED, reason="worker-lost", detail=reason, provisional=True
                )

    # ---------------------------------------------------------------- heartbeat

    def _heartbeat_loop(self):
        while not self._stop.is_set():
            time.sleep(self.heartbeat_interval)
            if self._stop.is_set():
                return
            if self.role == self.ROLE_COORDINATOR:
                with self._lock:
                    digest = [
                        {
                            "peer_id": record["peer_id"],
                            "address": record.get("address", ""),
                            "roles": record.get("roles", []),
                            "modes": record.get("modes", []),
                            "load": record.get("load", {}),
                        }
                        for record in self._members.values()
                    ]
                    peer_ids = list(self._members.keys())
                payload = protocol.message(
                    protocol.HEARTBEAT,
                    peer_id=self.peer_id,
                    address=self.address,
                    roles=[self.role],
                    load=self.load(),
                    members=digest,
                )
                for peer_id in peer_ids:
                    self._send(peer_id, dict(payload))
            else:
                self._notify_coordinator(
                    protocol.message(
                        protocol.HEARTBEAT,
                        peer_id=self.peer_id,
                        address=self.address,
                        roles=[self.role],
                        modes=list(self.runner.supported_modes) if self.runner is not None else [],
                        load=self.load(),
                    )
                )

    def _liveness_loop(self):
        while not self._stop.is_set():
            time.sleep(self.heartbeat_interval)
            if self._stop.is_set():
                return
            deadline = time.time() - self.peer_timeout
            with self._lock:
                stale = [peer_id for peer_id, record in self._members.items() if record["last_seen"] < deadline]
                direct = {peer_id for peer_id in stale if self._members[peer_id].get("direct")}
                hearsay = [peer_id for peer_id in stale if peer_id not in direct]
                for peer_id in hearsay:
                    # A peer we only ever heard about (gossip) is not a peer we
                    # lost, and it must not be reported as one: a digest that
                    # keeps naming a dead worker would otherwise turn into a
                    # stream of losses, each one burning a re-dispatch attempt
                    # on work that was never that peer's.
                    self._members.pop(peer_id, None)
            for peer_id in hearsay:
                self._record("hearsay-expired", peer_id=peer_id, detail="never heard from directly")
            for peer_id in direct:
                self._member_lost(peer_id, "heartbeat timeout")

    # ------------------------------------------------------- coordinator: work

    def submit(self, job):
        """Register a job; the dispatcher places it on an eligible worker."""
        with self._lock:
            self._jobs[job.job_id] = job
            self._job_state[job.job_id] = "pending"
            if not job.origin:
                job.origin = self.peer_id
            scope = job.content_scope_key or job.scope_key
            self._sequence[scope] = self._sequence.get(scope, 0) + 1
            job.sequence = max(job.sequence, self._sequence[scope])
        self._record("job-submitted", job=job, peer_id=self.peer_id, detail=job.mode)
        return job.job_id

    def _dispatch_loop(self):
        while not self._stop.is_set():
            time.sleep(0.1)
            if self._stop.is_set():
                return
            try:
                self._dispatch_once()
            except Exception as error:  # a dispatcher bug must not stall the mesh
                self._record("dispatch-error", detail=repr(error))

    def _dispatch_once(self):
        """Offer pending jobs to eligible workers, one writer per scope.

        Every pending job is considered, not only the oldest one: a job waiting
        for a live scope must not hold back unrelated work queued behind it.
        """
        while True:
            with self._lock:
                pending = [self._jobs[job_id] for job_id, state in self._job_state.items() if state == "pending"]
                if not pending:
                    return
                candidates = [
                    record
                    for record in self._members.values()
                    if self.ROLE_WORKER in record.get("roles", [])
                    and (record.get("address") or record.get("direct"))
                    and self._connections.get(record["peer_id"]) is not None
                    and record["load"].get("queued", 0) + record["load"].get("running", 0) < 2
                ]
                if not candidates:
                    return
                chosen = None
                now = time.time()
                for job in pending:
                    if now < self._retry_after.get(job.job_id, 0.0):
                        continue  # this job was just refused; give it a moment
                    if any(self._is_scope_busy(key, owner=job.job_id) for key in self._scope_keys(job)):
                        continue  # the scope is being worked; leave this job pending
                    able = [record for record in candidates if not record.get("modes") or job.mode in record["modes"]]
                    if able:
                        chosen = (job, able)
                        break
                if chosen is None:
                    return
                job, able = chosen
                scope_keys = self._scope_keys(job)
                target = min(able, key=lambda record: record["load"].get("queued", 0) + record["load"].get("running", 0))
                self._job_state[job.job_id] = "dispatched"
                self._job_owner[job.job_id] = target["peer_id"]
                for key in scope_keys:
                    self._foreign_leases[key] = protocol.Lease(job.job_id, target["peer_id"], key, job.sequence, os.urandom(4).hex())
                target["load"]["queued"] = target["load"].get("queued", 0) + 1
                self._offered_at[job.job_id] = time.time()
                self._acknowledged.discard(job.job_id)
            self._record("job-dispatched", job=job, peer_id=target["peer_id"], detail=job.mode)
            if self._send(target["peer_id"], protocol.message(protocol.JOB_OFFER, job=job.as_dict(), origin=self.peer_id)):
                continue
            # The offer never left the coordinator: undo the placement so the job
            # is retried instead of being stranded as "dispatched" forever.
            self._unplace(job, target["peer_id"], scope_keys)
            self._record("dispatch-failed", job=job, peer_id=target["peer_id"], detail="offer-not-sent")
            return

    def _unplace(self, job, peer_id, scope_keys):
        """Undo a placement that never reached the peer, so it can be retried."""
        with self._lock:
            if self._job_state.get(job.job_id) == "dispatched":
                self._job_state[job.job_id] = "pending"
            self._job_owner.pop(job.job_id, None)
            self._offered_at.pop(job.job_id, None)
            self._acknowledged.discard(job.job_id)
            for key in scope_keys:
                lease = self._foreign_leases.get(key)
                if lease is not None and lease.job_id == job.job_id:
                    self._foreign_leases.pop(key, None)
            member = self._members.get(peer_id)
            if member is not None:
                load = member.get("load", {})
                member["load"] = {
                    "queued": max(0, int(load.get("queued", 0)) - 1),
                    "running": int(load.get("running", 0)),
                }

    def _watchdog_loop(self):
        """Re-offer work whose offer went unanswered.

        Delivery is best effort: if a peer goes quiet between the offer and its
        answer, the job must not stay `dispatched` forever. Re-offering is safe
        precisely because of the guards the workers apply -- a peer that already
        advanced the scope refuses the job as `refused-stale`, and a peer that
        already holds the scope refuses it as `refused-scope-busy`.
        """
        while not self._stop.is_set():
            time.sleep(0.5)
            if self._stop.is_set():
                return
            deadline = time.time() - self.offer_ack_timeout
            with self._lock:
                silent = [
                    job_id
                    for job_id, state in self._job_state.items()
                    if state == "dispatched"
                    and job_id not in self._acknowledged
                    and self._offered_at.get(job_id, 0.0) < deadline
                ]
                decisions = []
                for job_id in silent:
                    job = self._jobs.get(job_id)
                    self._offered_at.pop(job_id, None)
                    self._job_owner.pop(job_id, None)
                    if job is not None:
                        for key in self._scope_keys(job):
                            lease = self._foreign_leases.get(key)
                            if lease is not None and lease.job_id == job_id:
                                self._foreign_leases.pop(key, None)
                        if job.attempt < self.max_attempts:
                            job.attempt += 1
                            self._redispatch_count += 1
                            self._job_state[job_id] = "pending"
                        else:
                            self._job_state[job_id] = "failed"
                    decisions.append(job)
            for job in decisions:
                if job is None:
                    continue
                if self._job_state.get(job.job_id) == "pending":
                    self._record(
                        "job-redispatched",
                        job=job,
                        peer_id="",
                        detail="no answer to the offer, attempt %d" % job.attempt,
                    )
                else:
                    self._finish_job(
                        job,
                        status=protocol.STATUS_FAILED,
                        reason="offer-unanswered",
                        detail="the peer never answered the offer",
                        provisional=True,
                    )

    def _scope_keys(self, job):
        keys = [job.scope_key]
        if job.content_scope_key:
            keys.append(job.content_scope_key)
        return keys

    def _is_scope_busy(self, scope_key_value, owner=""):
        lease = self._foreign_leases.get(scope_key_value)
        if lease is None:
            return False
        return lease.job_id != owner

    def _note_job_progress(self, message):
        """A job started or was queued at a peer: ownership moves with the work."""
        job_id = message.get("job_id", "")
        peer_id = message.get("peer_id", "")
        started = message.get("kind") == protocol.JOB_STARTED
        with self._lock:
            if job_id not in self._job_state:
                return
            if job_id in self._results:
                # This job is already finished. A peer reporting progress for it is
                # working from a queue it never emptied -- which happens when the
                # job was orphaned by a loss, recorded as failed, and then run
                # anyway by a peer that still held it. Accepting the report would
                # put the state back to running/queued beside a terminal record
                # that `_finish_job` refuses to overwrite, so the ledger would
                # claim a job is running that has already been accounted for, and
                # whatever the second run produced would be dropped on the floor.
                # Found by the W16 kill test: killing a worker mid-unit left
                # job_states {done: 3, running: 1} next to terminal: 4.
                finished_status = self._results[job_id].get("status", "")
                finished = True
            else:
                finished_status = ""
                finished = False
            if not finished:
                self._acknowledged.add(job_id)
                self._job_owner[job_id] = peer_id
                self._job_state[job_id] = "running" if started else "queued"
                for key, lease in list(self._foreign_leases.items()):
                    if lease.job_id == job_id and lease.peer_id != peer_id:
                        self._foreign_leases[key] = protocol.Lease(job_id, peer_id, key, lease.sequence, lease.lease_id)
                        self._record("lease-transferred", job=self._jobs.get(job_id), peer_id=peer_id, detail="now held by %s" % peer_id)
                record = self._members.get(peer_id)
                if record is not None and started:
                    load = record.get("load", {})
                    record["load"] = {
                        "queued": max(0, int(load.get("queued", 1)) - 1),
                        "running": 1,
                    }
        if finished:
            self._record(
                "progress-after-terminal-ignored",
                job=self._jobs.get(job_id),
                peer_id=peer_id,
                detail="already recorded %s" % finished_status,
            )
            return
        self._record("job-" + ("started" if started else "queued"), job=self._jobs.get(job_id), peer_id=peer_id)

    def _handle_job_result(self, message):
        job = self._jobs.get(message.get("job_id", ""))
        record = {
            "job_id": message.get("job_id", ""),
            "status": message.get("status", protocol.STATUS_FAILED),
            "result_ref": message.get("result_ref", ""),
            "source_digest": message.get("source_digest", ""),
            "peer_id": message.get("peer_id", ""),
            "stolen_from": message.get("stolen_from", ""),
            "exit_code": message.get("exit_code"),
            "elapsed_seconds": message.get("elapsed_seconds", 0.0),
            "reason": message.get("reason", ""),
            "artifact_bytes": message.get("artifact_bytes", 0),
            "artifact_sha256": message.get("artifact_sha256", ""),
        }
        if (
            self.artifacts == protocol.ARTIFACTS_WIRE
            and job is not None
            and protocol.status_is_success(record["status"])
        ):
            # In wire mode a success is only a success once its bytes are here.
            # The transfer precedes the result on the same ordered link, so a
            # missing or mismatched file is a real defect, not a race.
            problem = self._result_artifact_problem(job, record.get("artifact_sha256", ""))
            if problem:
                self._record("result-without-artifact", job=job, peer_id=record["peer_id"], detail=problem)
                record["status"] = protocol.STATUS_FAILED
                record["reason"] = "artifact-" + problem.split(":")[0]
        superseded = False
        presumed = False
        with self._lock:
            job_id = record["job_id"]
            if job_id in self._results:
                existing = self._results[job_id]
                if existing.get("status") == protocol.STATUS_OK or record["status"] != protocol.STATUS_OK:
                    return  # a recorded success stands, and a second failure adds nothing
                # Any recorded failure gives way to a real success, presumed or not.
                # The provisional case is the one the docstring describes: work
                # written off as lost with a peer that has now turned up with the
                # result. The non-provisional case is the one the W16 kill test
                # found -- a job that ran out of attempts and was recorded failed
                # while a peer that still held it queued went on to prove it.
                # "Attempts exhausted" is bookkeeping; a finished search is a fact.
                # The line above already refuses to replace a success and to record
                # a second failure, so at most one supersession per job: no flapping.
                superseded = True
                presumed = bool(existing.get("provisional"))
            self._acknowledged.add(job_id)
            self._offered_at.pop(job_id, None)
            self._job_state[job_id] = "done" if protocol.status_is_success(record["status"]) else "failed"
            self._job_owner.pop(job_id, None)
            self._results[job_id] = record
            if job is not None:
                scope = job.content_scope_key or job.scope_key
                self._completed_sequence[scope] = max(self._completed_sequence.get(scope, 0), job.sequence)
                for key in self._scope_keys(job):
                    lease = self._foreign_leases.get(key)
                    if lease is not None and lease.job_id == job_id:
                        self._foreign_leases.pop(key, None)
            member = self._members.get(record["peer_id"])
            if member is not None:
                member["load"] = {"queued": 0, "running": 0}
            if record["stolen_from"]:
                self._steals += 1
        if superseded:
            self._record(
                "result-superseded",
                job=job,
                peer_id=record["peer_id"],
                detail="a real result replaced a %s failure" % ("presumed" if presumed else "recorded"),
            )
        self._record(
            "job-result",
            job=job,
            peer_id=record["peer_id"],
            detail=record["status"],
            stolen_from=record["stolen_from"],
            result_ref=record["result_ref"],
        )

    def _handle_job_declined(self, message):
        job = self._jobs.get(message.get("job_id", ""))
        reason = message.get("reason", "declined")
        peer_id = message.get("peer_id", "")
        terminal = reason in (protocol.REFUSED_STALE,)
        with self._lock:
            job_id = message.get("job_id", "")
            self._acknowledged.add(job_id)
            self._offered_at.pop(job_id, None)
            if self._job_state.get(job_id) in ("pending", "dispatched", "queued"):
                self._job_state[job_id] = "pending"
            # A refusal means "not now" (the scope is busy, this peer cannot run
            # it): re-offering it immediately would spin the dispatcher and, worse,
            # flood the ledger while a peer is already struggling to keep up.
            self._retry_after[job_id] = time.time() + 0.5
            self._job_owner.pop(job_id, None)
            if job is not None:
                for key in self._scope_keys(job):
                    lease = self._foreign_leases.get(key)
                    if lease is not None and lease.job_id == job_id:
                        self._foreign_leases.pop(key, None)
            member = self._members.get(peer_id)
            if member is not None:
                load = member.get("load", {})
                member["load"] = {"queued": max(0, int(load.get("queued", 1)) - 1), "running": 0}
        self._record("job-declined", job=job, peer_id=peer_id, detail=reason)
        if terminal and job is not None:
            # Staleness is decided by the scope's sequence, so re-offering the
            # same job can only be refused again: it is a terminal outcome.
            self._finish_job(
                job,
                status=protocol.STATUS_FAILED,
                reason=reason,
                detail="refused as %s" % reason,
            )

    # ------------------------------------------------------------ worker: work

    def _handle_job_offer(self, message, connection):
        try:
            job = protocol.Job.from_dict(message.get("job", {}))
        except (KeyError, ValueError) as error:
            connection.send(
                protocol.message(
                    protocol.JOB_DECLINED,
                    job_id=(message.get("job") or {}).get("job_id", ""),
                    peer_id=self.peer_id,
                    reason="malformed-job",
                    detail=str(error),
                )
            )
            return
        refusal = self._offer_refusal(job)
        if refusal:
            connection.send(protocol.message(protocol.JOB_DECLINED, job_id=job.job_id, peer_id=self.peer_id, reason=refusal))
            self._record("job-declined-locally", job=job, peer_id=self.peer_id, detail=refusal)
            return
        with self._lock:
            for key in self._scope_keys(job):
                self._local_leases[key] = protocol.Lease(job.job_id, self.peer_id, key, job.sequence, os.urandom(4).hex())
            self._queue.append(job)
            will_start = self._running is None
        connection.send(
            protocol.message(
                protocol.JOB_STARTED if will_start else protocol.JOB_QUEUED,
                job_id=job.job_id,
                peer_id=self.peer_id,
            )
        )
        self._record("job-accepted", job=job, peer_id=self.peer_id, detail="starting" if will_start else "queued")

    def _offer_refusal(self, job):
        """Why this peer must not take this job. Empty string means it may."""
        if self._stop.is_set():
            return protocol.REFUSED_SHUTDOWN
        if self.runner is None or not self.runner.supports(job.mode):
            return protocol.REFUSED_MODE
        with self._lock:
            scope = job.content_scope_key or job.scope_key
            if job.sequence <= self._completed_sequence.get(scope, 0):
                return protocol.REFUSED_STALE
            for key in self._scope_keys(job):
                lease = self._local_leases.get(key)
                if lease is not None and lease.job_id != job.job_id:
                    return protocol.REFUSED_SCOPE
        return ""

    def _job_loop(self):
        while not self._stop.is_set():
            job = None
            with self._lock:
                if self._running is None and self._queue:
                    job = self._queue.pop(0)
                    self._running = job
            if job is None:
                time.sleep(0.05)
                continue
            # Ownership transfers to whoever actually starts the work -- including
            # a thief, so the coordinator never redispatch a job that is running.
            self._notify_coordinator(
                protocol.message(
                    protocol.JOB_STARTED,
                    job_id=job.job_id,
                    peer_id=self.peer_id,
                    stolen_from=job.stolen_from,
                )
            )
            self._record(
                "job-start",
                job=job,
                peer_id=self.peer_id,
                detail=("stolen from %s" % job.stolen_from) if job.stolen_from else "local",
            )
            try:
                local_job, problem = self._prepare_job(job)
                if problem:
                    self._finish_job(job, status=protocol.STATUS_FAILED, reason=problem, detail="before the runner started")
                    continue
                outcome = self.runner.run(local_job)
                artifact_sha256 = ""
                if self.artifacts == protocol.ARTIFACTS_WIRE and protocol.status_is_success(outcome.status):
                    artifact_sha256 = self._upload_result(job.job_id, job.result_ref, local_path=local_job.result_ref)
                self._finish_job(
                    job,
                    status=outcome.status,
                    reason=outcome.reason,
                    detail="ran in %.2fs" % (outcome.elapsed_seconds,),
                    elapsed_seconds=outcome.elapsed_seconds,
                    artifact_bytes=outcome.artifact_bytes,
                    exit_code=outcome.exit_code,
                    artifact_sha256=artifact_sha256,
                )
            except Exception as error:
                self._finish_job(job, status=protocol.STATUS_FAILED, reason="runner-error", detail=repr(error))
            finally:
                with self._lock:
                    self._running = None

    def _finish_job(
        self,
        job,
        status,
        reason="",
        detail="",
        elapsed_seconds=0.0,
        artifact_bytes=0,
        exit_code=None,
        provisional=False,
        artifact_sha256="",
    ):
        """Record the one terminal outcome for a job.

        `provisional` marks an outcome this peer only *presumed*: work believed lost
        with a peer, or abandoned at shutdown. A peer that later turns up with an
        actual result supersedes it (see `_handle_job_result`), because a finished
        search is a fact while a missed heartbeat is an inference.
        """
        job_id = job.job_id if job is not None else ""
        record = {
            "job_id": job_id,
            "status": status,
            "reason": reason,
            "result_ref": job.result_ref if job is not None else "",
            "peer_id": self.peer_id,
            "stolen_from": job.stolen_from if job is not None else "",
            "source_digest": job.source_digest if job is not None else "",
            "exit_code": exit_code,
            "elapsed_seconds": elapsed_seconds,
            "artifact_bytes": artifact_bytes,
            "artifact_sha256": artifact_sha256,
            "provisional": bool(provisional),
        }
        with self._lock:
            existing = self._results.get(job_id)
            if existing is not None:
                if existing.get("status") == protocol.STATUS_OK or not protocol.status_is_success(status):
                    return  # a recorded success stands, and a second failure adds nothing
                # The same rule as `_handle_job_result`, on the local path: a real
                # success replaces a recorded failure. `provisional` outcomes are
                # presumptions and never overwrite anything that is already there.
            self._results[job_id] = record
            self._job_state[job_id] = "done" if protocol.status_is_success(status) else "failed"
            self._job_owner.pop(job_id, None)
            self._acknowledged.add(job_id)
            self._offered_at.pop(job_id, None)
            if job is not None:
                scope = job.content_scope_key or job.scope_key
                self._completed_sequence[scope] = max(self._completed_sequence.get(scope, 0), job.sequence)
                for key in self._scope_keys(job):
                    local = self._local_leases.get(key)
                    if local is not None and local.job_id == job_id:
                        self._local_leases.pop(key, None)
                    foreign = self._foreign_leases.get(key)
                    if foreign is not None and foreign.job_id == job_id:
                        self._foreign_leases.pop(key, None)
            self._queue = [queued for queued in self._queue if queued.job_id != job_id]
        self._notify_coordinator(protocol.message(protocol.JOB_RESULT, **record))
        self._record("job-result-local", job=job, peer_id=self.peer_id, detail=status, reason=reason)

    # ------------------------------------------------- artifacts over the wire (W20)

    def _prepare_job(self, job):
        """The job this peer will actually run, with its inputs on local disk.

        Shared mode: the job itself. Wire mode: a copy whose references live under
        this peer's artifact root, every input fetched from the coordinator first.
        Returns `(job_to_run, "")` or `(None, reason)` when an input could not be
        had -- which is a terminal failure for this attempt, with the reason on
        the record, never a hang.
        """
        if self.artifacts != protocol.ARTIFACTS_WIRE:
            return job, ""
        local_job = Artifacts.localised(job, self.artifact_dir)
        os.makedirs(os.path.dirname(os.path.abspath(local_job.result_ref)) or ".", exist_ok=True)
        for ref, local_ref in zip(Artifacts.input_refs(job), Artifacts.input_refs(local_job)):
            if os.path.exists(local_ref):
                self._record("artifact-cached", job=job, peer_id=self.peer_id, detail=ref)
                continue
            problem = self._fetch_input(job, ref, local_ref)
            if problem:
                return None, problem
        return local_job, ""

    def _fetch_input(self, job, ref, local_ref):
        event = threading.Event()
        with self._lock:
            self._awaited[local_ref] = event
            self._fetch_failures.pop(local_ref, None)
        sent = self._notify_coordinator(
            protocol.message(protocol.ARTIFACT_FETCH, job_id=job.job_id, ref=ref, peer_id=self.peer_id)
        )
        self._record("artifact-fetch-requested", job=job, peer_id=self.peer_id, detail=ref if sent else ref + " (no coordinator link)")
        arrived = event.wait(self.fetch_timeout) if sent else False
        with self._lock:
            self._awaited.pop(local_ref, None)
            failure = self._fetch_failures.pop(local_ref, None)
        if failure:
            return "input-missing:" + failure
        if not sent:
            return "input-fetch-no-link"
        if not arrived or not os.path.exists(local_ref):
            return "input-fetch-timeout"
        return ""

    def _upload_result(self, job_id, ref, local_path=None):
        """Push a finished result (and its sidecar) to the coordinator. Returns its sha256."""
        connection = self._coordinator_connection
        if connection is None or connection.closed.is_set():
            self._record("artifact-upload-deferred", peer_id=self.peer_id, detail="%s: no coordinator link" % ref)
            return ""
        local = local_path or Artifacts.local_path_for(ref, self.artifact_dir)
        if not os.path.exists(local):
            self._record("artifact-upload-skipped", peer_id=self.peer_id, detail="%s: nothing on disk" % ref)
            return ""
        header = Artifacts.send_file(connection, local, ref, job_id, Artifacts.KIND_RESULT)
        self._record(
            "artifact-sent",
            peer_id=self.peer_id,
            detail="%s (%d bytes, %d chunks, sha256 %s)" % (ref, header["size"], header["chunks"], header["sha256"][:12]),
            job_id=job_id,
        )
        sidecar_local = Artifacts.sidecar_of(local)
        if os.path.exists(sidecar_local):
            Artifacts.send_file(connection, sidecar_local, Artifacts.sidecar_of(ref), job_id, Artifacts.KIND_SIDECAR)
        return header["sha256"]

    def _result_artifact_problem(self, job, declared_sha256):
        """Why a wire-mode success cannot be accepted yet. Empty string means it can."""
        if not os.path.exists(job.result_ref):
            return "missing: no file at the job's result_ref"
        if declared_sha256:
            known = self._received_sha256.get(job.result_ref)
            actual = known if known else Artifacts.sha256_of(job.result_ref)
            if actual != declared_sha256:
                return "mismatch: on disk %s, result says %s" % (actual[:12], declared_sha256[:12])
        return ""

    def _handle_artifact_fetch(self, message, connection):
        job_id = message.get("job_id", "")
        ref = message.get("ref", "")
        if self.role != self.ROLE_COORDINATOR:
            connection.send(protocol.message(protocol.ARTIFACT_MISSING, job_id=job_id, ref=ref, reason="not-a-coordinator"))
            return
        path, reason = self._input_authority.path_for(job_id, ref)
        if path is None:
            self._record("artifact-fetch-refused", peer_id=connection.peer_id, detail="%s: %s" % (ref, reason), job_id=job_id)
            connection.send(protocol.message(protocol.ARTIFACT_MISSING, job_id=job_id, ref=ref, reason=reason))
            return
        header = Artifacts.send_file(connection, path, ref, job_id, Artifacts.KIND_INPUT)
        self._record(
            "artifact-served",
            peer_id=connection.peer_id,
            detail="%s (%d bytes, %d chunks)" % (ref, header["size"], header["chunks"]),
            job_id=job_id,
        )

    def _artifact_destination(self, message):
        """Where an announced transfer may land here, or why it may not."""
        kind = message.get("artifact_kind", "")
        if self.role == self.ROLE_COORDINATOR:
            if kind not in (Artifacts.KIND_RESULT, Artifacts.KIND_SIDECAR):
                return None, "coordinator-accepts-results-only"
            return self._result_authority.destination_for(message)
        if kind != Artifacts.KIND_INPUT:
            return None, "worker-accepts-inputs-only"
        if not self.artifact_dir:
            return None, "no-artifact-dir"
        local = Artifacts.local_path_for(message.get("ref", ""), self.artifact_dir)
        with self._lock:
            awaited = local in self._awaited
        if not awaited:
            return None, "not-awaited"
        return local, ""

    def _handle_artifact_begin(self, message, connection):
        transfer_id = message.get("transfer_id", "")
        destination, reason = self._artifact_destination(message)
        if destination is None:
            self._record(
                "artifact-refused",
                peer_id=connection.peer_id,
                detail="%s: %s" % (message.get("ref", ""), reason),
                job_id=message.get("job_id", ""),
            )
            self._refused_transfer(transfer_id)
            connection.send(
                protocol.message(protocol.ARTIFACT_REFUSED, transfer_id=transfer_id, ref=message.get("ref", ""), reason=reason)
            )
            return
        try:
            self._receiver.begin(message, destination)
        except (Artifacts.TransferError, OSError) as error:
            self._record("artifact-refused", peer_id=connection.peer_id, detail="%s: %s" % (message.get("ref", ""), error))
            self._refused_transfer(transfer_id)
            connection.send(protocol.message(protocol.ARTIFACT_REFUSED, transfer_id=transfer_id, ref=message.get("ref", ""), reason=str(error)))
            return
        self._record(
            "artifact-incoming",
            peer_id=connection.peer_id,
            detail="%s -> %s (%d bytes, %d chunks)" % (message.get("ref", ""), destination, int(message.get("size", 0)), int(message.get("chunks", 0))),
            job_id=message.get("job_id", ""),
        )

    def _refused_transfer(self, transfer_id):
        refused = getattr(self, "_refused_transfers", None)
        if refused is None:
            refused = self._refused_transfers = set()
        if transfer_id:
            refused.add(transfer_id)

    def _is_refused_transfer(self, transfer_id):
        return transfer_id in getattr(self, "_refused_transfers", ())

    def _handle_artifact_chunk(self, message, connection):
        transfer_id = message.get("transfer_id", "")
        if self._is_refused_transfer(transfer_id):
            return
        pending = self._receiver.peek(transfer_id)
        try:
            self._receiver.chunk(transfer_id, int(message.get("index", -1)), message.get("data_b64", ""))
        except (Artifacts.TransferError, OSError) as error:
            self._artifact_failed(transfer_id, connection, error, pending)

    def _handle_artifact_end(self, message, connection):
        transfer_id = message.get("transfer_id", "")
        if self._is_refused_transfer(transfer_id):
            self._refused_transfers.discard(transfer_id)
            return
        pending = self._receiver.peek(transfer_id)
        try:
            transfer = self._receiver.end(transfer_id)
        except (Artifacts.TransferError, OSError) as error:
            self._artifact_failed(transfer_id, connection, error, pending)
            return
        sha256 = transfer.expected_sha256
        with self._lock:
            self._received_sha256[transfer.destination] = sha256
            waiter = self._awaited.get(transfer.destination)
        self._record(
            "artifact-received",
            peer_id=connection.peer_id,
            detail="%s (%d bytes, sha256 %s)" % (transfer.ref, transfer.received, sha256[:12]),
            job_id=transfer.job_id,
        )
        if waiter is not None:
            waiter.set()

    def _artifact_failed(self, transfer_id, connection, error, pending=None):
        """A transfer that cannot complete: no file, a reason, and any waiter released."""
        ref = pending.ref if pending is not None else transfer_id
        self._record("artifact-corrupt", peer_id=connection.peer_id, detail="%s: %s" % (ref, error))
        self._refused_transfer(transfer_id)
        self._receiver.abandon(transfer_id)
        connection.send(protocol.message(protocol.ARTIFACT_REFUSED, transfer_id=transfer_id, ref=ref, reason=str(error)))
        if pending is None:
            return
        # A worker waiting on this file must not sit out the whole fetch timeout.
        with self._lock:
            waiter = self._awaited.get(pending.destination)
            if waiter is not None:
                self._fetch_failures[pending.destination] = "corrupt: %s" % error
        if waiter is not None:
            waiter.set()

    def _handle_artifact_missing(self, message):
        ref = message.get("ref", "")
        reason = message.get("reason", "missing")
        self._record("artifact-missing", peer_id=self.peer_id, detail="%s: %s" % (ref, reason), job_id=message.get("job_id", ""))
        if not self.artifact_dir:
            return
        local = Artifacts.local_path_for(ref, self.artifact_dir)
        with self._lock:
            self._fetch_failures[local] = reason
            waiter = self._awaited.get(local)
        if waiter is not None:
            waiter.set()

    # ------------------------------------------------------------- work stealing

    def _steal_loop(self):
        while not self._stop.is_set():
            time.sleep(0.05)
            if self._stop.is_set():
                return
            with self._lock:
                idle = self._running is None and not self._queue
                now = time.time()
                candidates = [
                    dict(record)
                    for peer_id, record in self._members.items()
                    if peer_id != self.peer_id
                    and self.ROLE_WORKER in record.get("roles", [])
                    and record.get("address")
                    and record["load"].get("queued", 0) > 0
                    and self._steal_backoff.get(peer_id, 0.0) <= now
                ]
            if not idle:
                continue
            if not candidates:
                continue
            for record in candidates:
                if self._stop.is_set():
                    return
                if self._try_steal(record):
                    break

    def _try_steal(self, record):
        with self._lock:
            self._steal_attempts += 1
        host, port = parse_address(record["address"])
        try:
            sock = self._dial(host, port, 2.0, expected_name=record.get("common_name") or None, purpose="steal")
            sock.settimeout(5.0)
        except (ssl.SSLError, OSError, RuntimeError) as error:
            # A peer that advertises an address nobody can reach -- behind a NAT,
            # on a tunnel that only runs one way -- is not an error to retry at
            # wire speed. Say so once, and leave it alone for a while.
            with self._lock:
                self._steal_backoff[record["peer_id"]] = time.time() + 5.0
            self._record("steal-unreachable", peer_id=record["peer_id"], detail="%s: %s" % (record["address"], error.__class__.__name__))
            return False
        connection = Connection(sock, record["peer_id"], log=self._log, transient=True)
        connection.on_close = self._note_connection_closed
        self._record("steal-dialled", peer_id=record["peer_id"], detail=str(record.get("roles")))
        try:
            connection.send(protocol.message(protocol.STEAL_REQUEST, peer_id=self.peer_id, capacity=1))
            reply = connection.read(timeout=5.0)
        except (ssl.SSLError, OSError, framing.FrameError):
            connection.close()
            return False
        if reply is None or reply.get("kind") != protocol.STEAL_GRANT:
            connection.close()
            return False
        try:
            job = protocol.Job.from_dict(reply["job"])
        except (KeyError, ValueError):
            connection.close()
            return False
        connection.close()
        job.stolen_from = record["peer_id"]
        refusal = self._offer_refusal(job)
        if refusal:
            self._record("steal-refused-locally", job=job, peer_id=self.peer_id, detail=refusal)
            return False
        with self._lock:
            for key in self._scope_keys(job):
                self._local_leases[key] = protocol.Lease(job.job_id, self.peer_id, key, job.sequence, os.urandom(4).hex())
            self._queue.append(job)
        self._record("job-stolen", job=job, peer_id=self.peer_id, detail="from %s" % record["peer_id"])
        return True

    def _handle_steal_request(self, message, connection):
        """Hand over a queued -- never a running -- job, lease included."""
        thief = message.get("peer_id", "")
        with self._lock:
            grant = self._queue.pop(0) if self._queue else None
            if grant is not None:
                for key in self._scope_keys(grant):
                    lease = self._local_leases.get(key)
                    if lease is not None and lease.job_id == grant.job_id:
                        self._local_leases.pop(key, None)
        if grant is None:
            connection.send(protocol.message(protocol.STEAL_DENIED, job_id="", reason="no-queued-work"))
            self._record("steal-denied", peer_id=thief, detail="no queued work")
            return
        connection.send(protocol.message(protocol.STEAL_GRANT, job=grant.as_dict(), from_peer=self.peer_id))
        self._record("job-handed-over", job=grant, peer_id=thief, detail="stolen by %s" % thief)

    # ----------------------------------------------------------------- reporting

    def report(self):
        summary = self.summary()
        return "%s (%s) completed=%d failed=%d terminal=%d steals=%d redispatches=%d" % (
            summary["peer_id"],
            summary["role"],
            summary["completed"],
            summary["failed"],
            summary["terminal"],
            summary["steals"],
            summary["redispatches"],
        )
