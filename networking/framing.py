"""Framing for the mesh transport: length-prefixed JSON control frames.

The mesh never carries machine terms over the wire. What crosses the socket is a
job *description* (a manifest: search mode, the problem's printed start/goal, the
result reference) and the *reference* to a result artifact on the shared
filesystem, which the receiver loads through the snapshot codec. That is what
"zero-copy" means in the DAG's §3: the same term is never serialised twice, and no
machine object is ever pickled -- see `SWARM_EVOLUTION_DAG.md` §5.2 and this
module's `TERM_PAYLOAD_KEYS` guard, which rejects a frame that tries anyway.

A frame is:

    | 4-byte big-endian length | UTF-8 JSON object of that many bytes |

`recv_frame` returns None on a clean EOF, so callers can treat a closed socket as
"peer went away" without exception handling. It never loses bytes: a frame that
starts arriving is always read to its end, so the short idle timeout readers use
for polling can never desynchronise the stream (see `_read_exactly`).

Two ways to drive a socket
--------------------------
`send_frame` / `recv_frame` are for a *blocking* socket used by one thread at a
time (a raw client in a test, a one-shot steal request). A mesh connection is not
that: one thread reads it while another writes it, and a TLS socket cannot be
used that way as it stands. OpenSSL's connection object is not thread-safe, and
the idle timeout the polling reader sets with `settimeout` is inherited by the
writer, whose `sendall` then gives up in the middle of a record and leaves the
TLS state unusable ("EOF occurred in violation of protocol" on one side, a stall
mid-frame on the other). With W2's small control frames that overlap was rare;
with W20's multi-megabyte artifact chunks it is routine. `Duplex` is the answer:
the socket is non-blocking, every call into the TLS object is a short, non-waiting
step taken under one lock, and all waiting happens on `select` outside it.
"""

from __future__ import annotations

import json
import select
import socket
import ssl
import struct
import threading
import time

MAX_FRAME_BYTES = 8 * 1024 * 1024

# One `send` call under the duplex lock moves at most this much: enough that a
# 4 MiB chunk frame is a handful of steps, small enough that the reader never
# waits long for its turn.
SEND_SLICE_BYTES = 256 * 1024

# How long a peer may be silent *inside* a frame before that frame is abandoned.
# Readers poll with a short idle timeout, so this only matters once a frame has
# started arriving: giving up on it would lose the bytes already read.
FRAME_STALL_SECONDS = 30.0


class FrameError(Exception):
    """Raised for a malformed, oversized, or unpicklable-by-policy frame."""


# Keys that would carry a serialised machine term rather than a reference to one.
# Nothing in this transport may send them; the check is here so that a future
# caller finds out immediately instead of silently inventing a second codec.
TERM_PAYLOAD_KEYS = ("pickle", "term_payload", "machine_state", "serialized_term")


def encode_frame(message: dict) -> bytes:
    if not isinstance(message, dict):
        raise FrameError("frame payload must be a JSON object")
    for key in TERM_PAYLOAD_KEYS:
        if key in message:
            raise FrameError(
                "refusing to send %r: machine values travel as snapshot references, "
                "not payloads (SWARM_EVOLUTION_DAG.md 5.2)" % (key,)
            )
    body = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_FRAME_BYTES:
        raise FrameError("frame of %d bytes exceeds the %d byte limit" % (len(body), MAX_FRAME_BYTES))
    return struct.pack("!I", len(body)) + body


def _read_exactly(sock: socket.socket, count: int, stall_timeout: float = FRAME_STALL_SECONDS):
    """Read exactly `count` bytes, or return None if the peer closed first.

    Readers poll for work with a short idle timeout, so `sock.recv` may time out.
    Before the first byte that only means "nothing to read yet", and it is left to
    propagate so the caller can poll again. *Inside* a frame it may not be: the
    bytes already read would be dropped and every later frame would be parsed at
    the wrong offset. A read that has started therefore waits out a slow peer (up
    to `stall_timeout`) instead of desynchronising the stream, which is what makes
    a frame split across TCP segments safe.
    """
    buffer = bytearray()
    deadline = None
    while len(buffer) < count:
        try:
            chunk = sock.recv(count - len(buffer))
        except OSError as error:
            # "Nothing yet" is not "gone". A poll timeout -- and, on a TLS
            # socket, the equivalent want-read condition -- means the peer is
            # merely silent; it must not be reported as a closed connection.
            if isinstance(error, (socket.timeout, TimeoutError, ssl.SSLWantReadError, ssl.SSLWantWriteError, InterruptedError)):
                now = time.time()
                if not buffer:
                    # Nothing read yet: the caller polls again. Normalise the
                    # exception so every caller can keep catching one type.
                    raise socket.timeout("no frame yet") from error
                if deadline is None:
                    deadline = now + stall_timeout
                if now >= deadline:
                    raise FrameError("peer stalled mid-frame after %d of %d bytes" % (len(buffer), count))
                continue
            # A real EOF is the peer saying goodbye, and it is the only thing
            # that may look like one. The TLS layer reports the two ends of that
            # politely; a refuse-to-verify alert after a rejected handshake (see
            # `_serve_connection`'s `handshake-refused`), a bad record, or a
            # descriptor that was closed underneath us are *failures* -- letting
            # them return None would make an expired certificate
            # indistinguishable from a peer that left quietly.
            if isinstance(error, (ssl.SSLEOFError, ssl.SSLZeroReturnError)):
                return None
            raise
        if not chunk:
            return None
        buffer.extend(chunk)
    return bytes(buffer)


def send_frame(sock: socket.socket, message: dict) -> None:
    sock.sendall(encode_frame(message))


def recv_frame(sock: socket.socket, timeout: float = None):
    """Receive one frame, or None if the peer closed the connection."""
    if timeout is not None:
        sock.settimeout(timeout)
    header = _read_exactly(sock, 4)
    if header is None:
        return None
    (length,) = struct.unpack("!I", header)
    if length > MAX_FRAME_BYTES:
        raise FrameError("peer announced an oversized frame (%d bytes)" % length)
    body = _read_exactly(sock, length)
    if body is None:
        return None
    try:
        message = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrameError("undecodable frame: %s" % (error,))
    if not isinstance(message, dict):
        raise FrameError("frame payload must be a JSON object")
    return message


class Duplex:
    """A socket read by one thread and written by another, safely.

    `recv(timeout)` and `send(message)` are the frame-level operations the mesh
    `Connection` needs. Internally the socket is non-blocking and one lock guards
    every call into it (and so into OpenSSL): a call either completes or reports
    "would block", and the wait for readability / writability happens on `select`
    with the lock released, so the reader and the writer take turns rather than
    overlapping. `pending()` is consulted before every wait because TLS may have
    decrypted more than the frame reader asked for, and that surplus is invisible
    to `select`.

    Semantics match `recv_frame` / `send_frame`: `recv` raises `socket.timeout`
    when no frame *starts* within `timeout`, waits out a slow peer inside a frame
    up to `FRAME_STALL_SECONDS`, and returns None on EOF. `send` raises
    `socket.timeout` when the peer has not accepted any bytes for
    `FRAME_STALL_SECONDS` -- the one case in which a writer may give up, because
    a peer that reads nothing for that long is not coming back.
    """

    def __init__(self, sock: socket.socket, stall_timeout: float = FRAME_STALL_SECONDS):
        self.sock = sock
        self.stall_timeout = stall_timeout
        self._lock = threading.Lock()
        sock.setblocking(False)

    # -- waiting (never under the lock) --

    def _pending(self) -> bool:
        pending = getattr(self.sock, "pending", None)
        if pending is None:
            return False
        with self._lock:
            try:
                return pending() > 0
            except (OSError, ValueError):
                return False

    def _wait(self, readable: bool, timeout: float) -> bool:
        if readable and self._pending():
            return True
        try:
            if readable:
                ready, _, _ = select.select([self.sock], [], [], timeout)
            else:
                _, ready, _ = select.select([], [self.sock], [], timeout)
        except (OSError, ValueError):
            # A descriptor closed under us: let the next recv/send report it.
            return True
        return bool(ready)

    # -- reading --

    def _recv_step(self, count: int):
        """One non-waiting read: bytes, b"" on EOF, or None for "nothing yet"."""
        with self._lock:
            try:
                return self.sock.recv(min(count, 1 << 20))
            except (ssl.SSLWantReadError, ssl.SSLWantWriteError, BlockingIOError, InterruptedError):
                return None
            except (ssl.SSLEOFError, ssl.SSLZeroReturnError):
                return b""

    def _read_exactly(self, count: int, first_timeout: float = None):
        buffer = bytearray()
        deadline = None
        while len(buffer) < count:
            chunk = self._recv_step(count - len(buffer))
            if chunk is None:
                now = time.time()
                if not buffer and first_timeout is not None:
                    if deadline is None:
                        deadline = now + first_timeout
                    if now >= deadline:
                        raise socket.timeout("no frame yet")
                    self._wait(True, max(0.0, min(deadline - now, 0.5)))
                    continue
                if deadline is None or not buffer:
                    deadline = now + self.stall_timeout
                if now >= deadline:
                    raise FrameError("peer stalled mid-frame after %d of %d bytes" % (len(buffer), count))
                self._wait(True, max(0.0, min(deadline - now, 0.5)))
                continue
            if not chunk:
                return None
            buffer.extend(chunk)
            deadline = None
        return bytes(buffer)

    def recv(self, timeout: float = None):
        """One frame; None on EOF; `socket.timeout` if none starts within `timeout`."""
        header = self._read_exactly(4, first_timeout=timeout)
        if header is None:
            return None
        (length,) = struct.unpack("!I", header)
        if length > MAX_FRAME_BYTES:
            raise FrameError("peer announced an oversized frame (%d bytes)" % length)
        body = self._read_exactly(length)
        if body is None:
            return None
        try:
            message = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FrameError("undecodable frame: %s" % (error,))
        if not isinstance(message, dict):
            raise FrameError("frame payload must be a JSON object")
        return message

    # -- writing --

    def send(self, message: dict) -> None:
        data = memoryview(encode_frame(message))
        offset = 0
        deadline = None
        while offset < len(data):
            piece = data[offset : offset + SEND_SLICE_BYTES]
            wait_readable = False
            with self._lock:
                try:
                    sent = self.sock.send(piece)
                except ssl.SSLWantReadError:
                    sent = 0
                    wait_readable = True  # TLS needs the reader's turn first
                except (ssl.SSLWantWriteError, BlockingIOError, InterruptedError):
                    sent = 0
            if sent:
                # OpenSSL finishes a record it started before taking new bytes;
                # a retry after "would block" therefore re-offers the same piece.
                offset += sent
                deadline = None
                continue
            now = time.time()
            if deadline is None:
                deadline = now + self.stall_timeout
            if now >= deadline:
                raise socket.timeout("peer accepted no bytes for %.0f s" % self.stall_timeout)
            self._wait(wait_readable, max(0.0, min(deadline - now, 0.5)))
