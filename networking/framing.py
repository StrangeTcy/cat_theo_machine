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
"""

from __future__ import annotations

import json
import socket
import struct
import time

MAX_FRAME_BYTES = 8 * 1024 * 1024

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
        except (socket.timeout, TimeoutError):
            now = time.time()
            if not buffer:
                raise  # nothing read yet: the caller polls again
            if deadline is None:
                deadline = now + stall_timeout
            if now >= deadline:
                raise FrameError("peer stalled mid-frame after %d of %d bytes" % (len(buffer), count))
            continue
        except OSError:
            return None
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
