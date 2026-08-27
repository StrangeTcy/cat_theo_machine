"""Arc M: mTLS transport and binary length-delimited message framing.

Fixed-width frames: [length:u32][type:u8][version:u8][payload] big-endian.
No custom crypto: only Python's ssl stdlib module.
verify_mode = CERT_REQUIRED in both directions.
"""

from __future__ import annotations

import socket
import ssl
import struct

PROTOCOL_VERSION = 1
FRAME_CAP = 64 * 2**20

HELLO = 1
HEADS = 2
GET_SNAPSHOT = 3
SNAPSHOT = 4
GET_DELTAS = 5
DELTAS = 6
PROPOSALS = 7
LEDGER_RECORDS = 8
ACK = 9
ERR = 10
ANNOTATE = 11

MESSAGE_TYPES = (
    HELLO,
    HEADS,
    GET_SNAPSHOT,
    SNAPSHOT,
    GET_DELTAS,
    DELTAS,
    PROPOSALS,
    LEDGER_RECORDS,
    ACK,
    ERR,
    ANNOTATE,
)

MESSAGE_NAME_TO_TYPE = {
    "HELLO": HELLO,
    "HEADS": HEADS,
    "GET_SNAPSHOT": GET_SNAPSHOT,
    "SNAPSHOT": SNAPSHOT,
    "GET_DELTAS": GET_DELTAS,
    "DELTAS": DELTAS,
    "PROPOSALS": PROPOSALS,
    "LEDGER_RECORDS": LEDGER_RECORDS,
    "ACK": ACK,
    "ERR": ERR,
    "ANNOTATE": ANNOTATE,
}

MESSAGE_TYPE_TO_NAME = {
    HELLO: "HELLO",
    HEADS: "HEADS",
    GET_SNAPSHOT: "GET_SNAPSHOT",
    SNAPSHOT: "SNAPSHOT",
    GET_DELTAS: "GET_DELTAS",
    DELTAS: "DELTAS",
    PROPOSALS: "PROPOSALS",
    LEDGER_RECORDS: "LEDGER_RECORDS",
    ACK: "ACK",
    ERR: "ERR",
    ANNOTATE: "ANNOTATE",
}


def make_server_context(cert_path, key_path, ca_path):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    ctx.load_verify_locations(cafile=ca_path)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = False
    return ctx


def make_client_context(cert_path, key_path, ca_path):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    ctx.load_verify_locations(cafile=ca_path)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = False
    return ctx


def extract_peer_cn(ssl_socket):
    cert = ssl_socket.getpeercert()
    if not cert:
        return ""
    subject = cert.get("subject", ())
    for rdn in subject:
        for key, val in rdn:
            if key == "commonName":
                return val
    return ""


class TransportSession:
    def __init__(self, sock, peer_cn):
        self.sock = sock
        self.peer_cn = peer_cn
        self.closed = False

    def close(self):
        if not self.closed:
            self.closed = True
            try:
                self.sock.close()
            except Exception:
                pass


def open_session(host, port, contexts):
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.connect((host, port))
    ssl_sock = contexts.wrap_socket(raw_sock, server_hostname=None)
    peer_cn = extract_peer_cn(ssl_sock)
    return TransportSession(ssl_sock, peer_cn)


def frame_bytes(msg_type, payload_bytes, version=PROTOCOL_VERSION):
    if msg_type in MESSAGE_NAME_TO_TYPE:
        type_num = MESSAGE_NAME_TO_TYPE[msg_type]
    else:
        type_num = int(msg_type)
    return struct.pack(">IBB", len(payload_bytes), type_num, version) + payload_bytes


def unframe_bytes(data):
    if len(data) < 6:
        return (ERR, b"truncated")
    length, type_byte, version_byte = struct.unpack(">IBB", data[:6])
    if version_byte != PROTOCOL_VERSION:
        return (ERR, b"bad-version")
    if type_byte not in MESSAGE_TYPE_TO_NAME:
        return (ERR, b"unknown-type")
    if length > FRAME_CAP:
        return (ERR, b"oversize")
    payload = data[6 : 6 + length]
    if len(payload) < length:
        return (ERR, b"truncated")
    return (type_byte, payload)


def _read_exact(sock, count):
    chunks = []
    remaining = count
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_frame(session, msg_type, payload_bytes):
    if session.closed:
        return False
    if msg_type in MESSAGE_NAME_TO_TYPE:
        type_num = MESSAGE_NAME_TO_TYPE[msg_type]
    else:
        type_num = int(msg_type)

    if len(payload_bytes) > FRAME_CAP:
        err_frame = frame_bytes(ERR, b"oversize")
        try:
            session.sock.sendall(err_frame)
        except Exception:
            pass
        session.close()
        return False

    packet = frame_bytes(type_num, payload_bytes)
    try:
        session.sock.sendall(packet)
        return True
    except (OSError, ssl.SSLError):
        session.close()
        return False


def recv_frame(session):
    if session.closed:
        return (ERR, b"closed")
    try:
        header = _read_exact(session.sock, 6)
    except (OSError, ssl.SSLError):
        session.close()
        return (ERR, b"connection-error")

    if header is None or len(header) < 6:
        session.close()
        return (ERR, b"truncated")

    length, type_byte, version_byte = struct.unpack(">IBB", header)

    if version_byte != PROTOCOL_VERSION:
        err_frame = frame_bytes(ERR, b"bad-version")
        try:
            session.sock.sendall(err_frame)
        except Exception:
            pass
        session.close()
        return (ERR, b"bad-version")

    if type_byte not in MESSAGE_TYPE_TO_NAME:
        err_frame = frame_bytes(ERR, b"unknown-type")
        try:
            session.sock.sendall(err_frame)
        except Exception:
            pass
        session.close()
        return (ERR, b"unknown-type")

    if length > FRAME_CAP:
        err_frame = frame_bytes(ERR, b"oversize")
        try:
            session.sock.sendall(err_frame)
        except Exception:
            pass
        session.close()
        return (ERR, b"oversize")

    try:
        payload = _read_exact(session.sock, length)
    except (OSError, ssl.SSLError):
        session.close()
        return (ERR, b"connection-error")

    if payload is None or len(payload) < length:
        session.close()
        return (ERR, b"truncated")

    return (type_byte, payload)
