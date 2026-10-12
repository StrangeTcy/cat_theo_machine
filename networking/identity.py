"""Mesh identity: the certificate material a peer holds and the TLS contexts it speaks with.

A peer's identity is a leaf certificate issued by a local CA. Both sides of every
connection present a certificate and verify the other's against the *same* CA, so
the mesh is mutually authenticated: an unauthenticated peer cannot complete a
handshake at all, and the refusal paths (unknown cert, wrong CA, expired cert) are
ordinary TLS failures rather than application-level checks.

Nothing here is secret beyond the local test directory, and nothing here may be
committed: `pki_directory_guard` refuses to create key material inside the
repository tree unless `HYGE_MESH_ALLOW_REPO_PKI=1` is set explicitly.
"""

from __future__ import annotations

import datetime
import os
import socket
import ssl

from . import x509

DEFAULT_CA_NAME = "hyge-mesh-ca"
DEFAULT_LEAF_DAYS = 7


def pki_directory_guard(directory: str) -> str:
    """Refuse to write private keys into the repository tree."""
    absolute = os.path.abspath(directory)
    repository_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.environ.get("HYGE_MESH_ALLOW_REPO_PKI") == "1":
        return absolute
    if absolute == repository_root or absolute.startswith(repository_root + os.sep):
        raise RuntimeError(
            "refusing to write mesh key material inside the repository ("
            + absolute
            + "); use a temporary directory, or set HYGE_MESH_ALLOW_REPO_PKI=1 "
            "if you really mean it"
        )
    return absolute


def _serial() -> int:
    return int.from_bytes(os.urandom(8), "big") | 1


class MeshIdentity:
    """One peer's certificate, its key, and the CA that vouches for it."""

    def __init__(self, common_name, cert_path, key_path, ca_path):
        self.common_name = common_name
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path

    def server_context(self, trust_peers: bool = True, ca_path: str = None):
        """Server-side context: presents this identity, demands a peer certificate."""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.cert_path, self.key_path)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        if trust_peers:
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(ca_path or self.ca_path)
        else:
            context.verify_mode = ssl.CERT_NONE
        return context

    def client_context(self, ca_path: str = None, check_hostname: bool = True):
        """Client-side context: presents this identity, verifies the peer's."""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_cert_chain(self.cert_path, self.key_path)
        context.load_verify_locations(ca_path or self.ca_path)
        context.check_hostname = check_hostname
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        return context


class MeshPki:
    """A local CA and the leaves it has issued, all as files in one directory."""

    def __init__(self, directory: str, ca_identity: MeshIdentity, ca_key):
        self.directory = directory
        self.ca_identity = ca_identity
        self._ca_key = ca_key
        self._identities = {}

    @classmethod
    def create(cls, directory: str, ca_name: str = DEFAULT_CA_NAME, days: int = 30):
        directory = pki_directory_guard(directory)
        os.makedirs(directory, exist_ok=True)
        now = datetime.datetime.now(datetime.timezone.utc)
        ca_key = x509.generate_rsa_key(2048)
        ca_cert = x509.issue_certificate(
            ca_key,
            ca_name,
            _serial(),
            now - datetime.timedelta(days=1),
            now + datetime.timedelta(days=days),
            is_ca=True,
        )
        cert_path, key_path = ca_cert.write(directory, "ca")
        ca_identity = MeshIdentity(ca_name, cert_path, key_path, cert_path)
        pki = cls(directory, ca_identity, ca_key)
        pki._identities[ca_name] = ca_identity
        return pki

    def issue(
        self,
        common_name: str,
        sans=(),
        days: int = DEFAULT_LEAF_DAYS,
        not_before=None,
        not_after=None,
        is_ca: bool = False,
        issuer_key=None,
        issuer_name: str = None,
        ca_path: str = None,
        basename: str = None,
    ) -> MeshIdentity:
        """Issue a leaf (or another CA) and write its PEM pair under the PKI directory."""
        now = datetime.datetime.now(datetime.timezone.utc)
        if not_before is None:
            not_before = now - datetime.timedelta(days=1)
        if not_after is None:
            not_after = now + datetime.timedelta(days=days)
        key = x509.generate_rsa_key(2048)
        cert = x509.issue_certificate(
            key,
            common_name,
            _serial(),
            not_before,
            not_after,
            issuer_cn=issuer_name or self.ca_identity.common_name,
            issuer_key=issuer_key if issuer_key is not None else self._ca_key,
            is_ca=is_ca,
            sans=sans,
        )
        name = basename or common_name
        cert_path, key_path = cert.write(self.directory, name)
        identity = MeshIdentity(
            common_name,
            cert_path,
            key_path,
            ca_path or self.ca_identity.cert_path,
        )
        self._identities[name] = identity
        return identity

    def rogue_ca(self, name: str = "rogue-ca", days: int = 30):
        """A second, independent CA. Leaves it signs are not trusted by the mesh."""
        now = datetime.datetime.now(datetime.timezone.utc)
        key = x509.generate_rsa_key(2048)
        cert = x509.issue_certificate(
            key,
            name,
            _serial(),
            now - datetime.timedelta(days=1),
            now + datetime.timedelta(days=days),
            is_ca=True,
        )
        cert_path, _key_path = cert.write(self.directory, name)
        return name, key, cert_path

    def issue_from(self, issuer, common_name: str, issuer_name: str, ca_path: str, sans=(), days: int = DEFAULT_LEAF_DAYS, basename: str = None):
        """Issue a leaf from a CA other than ours (used to build refusal cases)."""
        _name, issuer_key, _issuer_cert_path = issuer
        return self.issue(
            common_name,
            sans=sans,
            days=days,
            issuer_key=issuer_key,
            issuer_name=issuer_name,
            ca_path=ca_path,
            basename=basename,
        )


def peer_common_name(sock_or_conn) -> str:
    """The authenticated identity of a TLS peer: its certificate's common name."""
    certificate = sock_or_conn.getpeercert()
    if not certificate:
        return ""
    for rdn in certificate.get("subject", ()):
        for key, value in rdn:
            if key == "commonName":
                return value
    return ""


def address_text(host: str, port: int) -> str:
    return "%s:%d" % (host, port)


def parse_address(text: str):
    host, _sep, port = text.rpartition(":")
    if not host:
        host = "127.0.0.1"
    return host, int(port)


def bind_listener(host: str = "127.0.0.1", port: int = 0, backlog: int = 16) -> socket.socket:
    """A listening socket bound to port 0 by default, so parallel runs never collide."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((host, port))
    listener.listen(backlog)
    return listener
