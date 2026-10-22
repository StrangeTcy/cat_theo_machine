"""Pure-Python RSA key generation and X.509 certificate issuing for the mesh.

Why this file exists
--------------------
W2 needs mutual TLS on loopback, with certificates the test can control
precisely: an honest leaf, a leaf from a *rogue* CA, an *expired* leaf, and a
leaf that chains to nothing the peer trusts. The sandbox has no OpenSSL CLI
guarantee and `cryptography` is not in the documented environment
(`.venv/bin/pip install gmpy2 pyyaml`), so the pack's fallback applies:

    "generate the CA/leaf certs in Python ... else fall back to a documented
     self-signed generation path"

This module *is* that documented path. It is deliberately small and boring:
SHA-256 + PKCS#1 v1.5, RSA-2048, the handful of X.509 v3 fields a TLS peer
actually validates. It is not a general-purpose PKI and must not be used for
anything but local, short-lived test material.

Never commit what this produces. `networking/identity.py` refuses to write
key material inside the repository tree unless explicitly overridden.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets

try:  # gmpy2 makes 2048-bit keygen ~10x faster; it is already a documented dependency
    import gmpy2 as _gmpy2
except Exception:  # pragma: no cover - exercised only on a bare interpreter
    _gmpy2 = None


# --------------------------------------------------------------------------
# RSA
# --------------------------------------------------------------------------


def _is_probable_prime(candidate: int, rounds: int = 32) -> bool:
    """Miller-Rabin, accelerated by gmpy2 when it is importable."""
    if _gmpy2 is not None:
        return bool(_gmpy2.is_prime(candidate, rounds))
    if candidate < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for prime in small_primes:
        if candidate % prime == 0:
            return candidate == prime
    d = candidate - 1
    shift = 0
    while d % 2 == 0:
        d //= 2
        shift += 1
    for _ in range(rounds):
        witness = secrets.randbelow(candidate - 3) + 2
        value = pow(witness, d, candidate)
        if value in (1, candidate - 1):
            continue
        for _ in range(shift - 1):
            value = pow(value, 2, candidate)
            if value == candidate - 1:
                break
        else:
            return False
    return True


def _random_prime(bits: int) -> int:
    while True:
        candidate = secrets.randbits(bits)
        candidate |= (1 << (bits - 1)) | 1  # full length, odd
        candidate |= 1 << (bits - 2)  # keep n a full 2*bits wide
        if _is_probable_prime(candidate):
            return candidate


class RsaPrivateKey:
    """An RSA key as plain integers. Enough for PKCS#1 signing and PEM export."""

    def __init__(self, n, e, d, p, q):
        self.n = n
        self.e = e
        self.d = d
        self.p = p
        self.q = q
        self.dp = d % (p - 1)
        self.dq = d % (q - 1)
        self.qinv = pow(q, -1, p)
        self.size_bytes = (n.bit_length() + 7) // 8

    def public_numbers(self):
        return self.n, self.e

    def sign_pkcs1_v1_5(self, message: bytes, digest_name: str = "sha256") -> bytes:
        digest = hashlib.new(digest_name, message).digest()
        digest_info = _DIGEST_INFO_PREFIX[digest_name] + digest
        padding_length = self.size_bytes - len(digest_info) - 3
        if padding_length < 8:
            raise ValueError("RSA modulus too small for this digest")
        encoded = b"\x00\x01" + b"\xff" * padding_length + b"\x00" + digest_info
        signature = pow(int.from_bytes(encoded, "big"), self.d, self.n)
        return signature.to_bytes(self.size_bytes, "big")

    def pkcs1_der(self) -> bytes:
        return _der_sequence(
            _der_integer(0),
            _der_integer(self.n),
            _der_integer(self.e),
            _der_integer(self.d),
            _der_integer(self.p),
            _der_integer(self.q),
            _der_integer(self.dp),
            _der_integer(self.dq),
            _der_integer(self.qinv),
        )

    def pem(self) -> bytes:
        return _pem("RSA PRIVATE KEY", self.pkcs1_der())


_DIGEST_INFO_PREFIX = {
    "sha256": bytes.fromhex("3031300d060960864801650304020105000420"),
}


def generate_rsa_key(bits: int = 2048) -> RsaPrivateKey:
    """Generate an RSA key. 2048-bit is the minimum OpenSSL 3 will negotiate."""
    if bits < 2048:
        raise ValueError("mesh keys are RSA-2048 or larger")
    e = 65537
    while True:
        p = _random_prime(bits // 2)
        q = _random_prime(bits - bits // 2)
        if p == q:
            continue
        if (p - 1) % e == 0 or (q - 1) % e == 0:
            continue
        n = p * q
        if n.bit_length() != bits:
            continue
        phi = (p - 1) * (q - 1)
        try:
            d = pow(e, -1, phi)
        except ValueError:
            continue
        if p < q:  # conventional ordering, and what qinv expects
            p, q = q, p
        return RsaPrivateKey(n, e, d, p, q)


# --------------------------------------------------------------------------
# Minimal DER
# --------------------------------------------------------------------------


def _der_length(length: int) -> bytes:
    if length < 0x80:
        return bytes([length])
    encoded = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(encoded)]) + encoded


def _der_tlv(tag: int, content: bytes) -> bytes:
    return bytes([tag]) + _der_length(len(content)) + content


def _der_sequence(*parts: bytes) -> bytes:
    return _der_tlv(0x30, b"".join(parts))


def _der_set(*parts: bytes) -> bytes:
    return _der_tlv(0x31, b"".join(parts))


def _der_integer(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative integers are not used in these certificates")
    content = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
    if content[0] & 0x80:
        content = b"\x00" + content
    return _der_tlv(0x02, content)


def _der_boolean(value: bool) -> bytes:
    return _der_tlv(0x01, b"\xff" if value else b"\x00")


def _der_null() -> bytes:
    return b"\x05\x00"


def _der_oid(dotted: str) -> bytes:
    parts = [int(part) for part in dotted.split(".")]
    first = 40 * parts[0] + parts[1]
    body = bytearray([first])
    for part in parts[2:]:
        chunk = [part & 0x7F]
        part >>= 7
        while part:
            chunk.append((part & 0x7F) | 0x80)
            part >>= 7
        body.extend(reversed(chunk))
    return _der_tlv(0x06, bytes(body))


def _der_utf8(text: str) -> bytes:
    return _der_tlv(0x0C, text.encode("utf-8"))


def _der_ia5(text: str) -> bytes:
    return _der_tlv(0x16, text.encode("ascii"))


def _der_octet_string(value: bytes) -> bytes:
    return _der_tlv(0x04, value)


def _der_bit_string(value: bytes, unused_bits: int = 0) -> bytes:
    return _der_tlv(0x03, bytes([unused_bits]) + value)


def _der_utc_time(when) -> bytes:
    if when.year >= 2050 or when.year < 1950:
        raise ValueError("UTCTime covers 1950-2049; use GeneralizedTime for more")
    text = when.strftime("%y%m%d%H%M%SZ")
    return _der_tlv(0x17, text.encode("ascii"))


def _der_context(tag_number: int, content: bytes, constructed: bool = True) -> bytes:
    tag = 0xA0 | tag_number if constructed else 0x80 | tag_number
    return _der_tlv(tag, content)


def _pem(label: str, der: bytes) -> bytes:
    body = base64.encodebytes(der).replace(b"\n", b"")
    lines = [body[index : index + 64] for index in range(0, len(body), 64)]
    return (
        b"-----BEGIN " + label.encode("ascii") + b"-----\n"
        + b"\n".join(lines)
        + b"\n-----END " + label.encode("ascii") + b"-----\n"
    )


# --------------------------------------------------------------------------
# X.509
# --------------------------------------------------------------------------

OID_COMMON_NAME = "2.5.4.3"
OID_ORGANISATION = "2.5.4.10"
OID_SHA256_WITH_RSA = "1.2.840.113549.1.1.11"
OID_RSA_ENCRYPTION = "1.2.840.113549.1.1.1"
OID_BASIC_CONSTRAINTS = "2.5.29.19"
OID_KEY_USAGE = "2.5.29.15"
OID_EXT_KEY_USAGE = "2.5.29.37"
OID_SUBJECT_ALT_NAME = "2.5.29.17"
OID_SERVER_AUTH = "1.3.6.1.5.5.7.3.1"
OID_CLIENT_AUTH = "1.3.6.1.5.5.7.3.2"

# keyUsage BIT STRING positions, and the encoded form OpenSSL expects.
_KEY_USAGE_BITS = {
    "digitalSignature": 0,
    "nonRepudiation": 1,
    "keyEncipherment": 2,
    "dataEncipherment": 3,
    "keyAgreement": 4,
    "keyCertSign": 5,
    "cRLSign": 6,
    "encipherOnly": 7,
    "decipherOnly": 8,
}


def _key_usage_der(names) -> bytes:
    highest = max(_KEY_USAGE_BITS[name] for name in names)
    byte_count = highest // 8 + 1
    buffer = bytearray(byte_count)
    for name in names:
        position = _KEY_USAGE_BITS[name]
        buffer[position // 8] |= 0x80 >> (position % 8)
    unused = 8 * byte_count - (highest + 1)
    return _der_bit_string(bytes(buffer), unused)


def _name_der(common_name: str, organisation: str = "hyge-mesh") -> bytes:
    organisation_rdn = _der_set(
        _der_sequence(_der_oid(OID_ORGANISATION), _der_utf8(organisation))
    )
    common_rdn = _der_set(_der_sequence(_der_oid(OID_COMMON_NAME), _der_utf8(common_name)))
    return _der_sequence(organisation_rdn, common_rdn)


def _algorithm_identifier() -> bytes:
    return _der_sequence(_der_oid(OID_SHA256_WITH_RSA), _der_null())


def _subject_public_key_info(key: RsaPrivateKey) -> bytes:
    rsa_public = _der_sequence(_der_integer(key.n), _der_integer(key.e))
    return _der_sequence(
        _der_sequence(_der_oid(OID_RSA_ENCRYPTION), _der_null()),
        _der_bit_string(rsa_public),
    )


def _extension(oid: str, critical: bool, payload: bytes) -> bytes:
    parts = [_der_oid(oid)]
    if critical:
        parts.append(_der_boolean(True))
    parts.append(_der_octet_string(payload))
    return _der_sequence(*parts)


def _extensions_der(is_ca, sans, client_only: bool) -> bytes:
    extensions = []
    if is_ca:
        extensions.append(
            _extension(OID_BASIC_CONSTRAINTS, True, _der_sequence(_der_boolean(True)))
        )
        extensions.append(
            _extension(
                OID_KEY_USAGE,
                True,
                _key_usage_der(["keyCertSign", "cRLSign", "digitalSignature"]),
            )
        )
    else:
        extensions.append(
            _extension(OID_BASIC_CONSTRAINTS, True, _der_sequence(_der_boolean(False)))
        )
        extensions.append(
            _extension(
                OID_KEY_USAGE,
                True,
                _key_usage_der(
                    ["digitalSignature", "keyEncipherment"]
                    if client_only
                    else ["digitalSignature"]
                ),
            )
        )
        purposes = [_der_oid(OID_CLIENT_AUTH)] if client_only else [
            _der_oid(OID_SERVER_AUTH),
            _der_oid(OID_CLIENT_AUTH),
        ]
        extensions.append(
            _extension(OID_EXT_KEY_USAGE, False, _der_sequence(*purposes))
        )
    if sans:
        general_names = []
        for name in sans:
            if name.count(".") == 3 and all(part.isdigit() for part in name.split(".")):
                general_names.append(_der_context(7, bytes(int(p) for p in name.split(".")), constructed=False))
            else:
                general_names.append(_der_context(2, name.encode("ascii"), constructed=False))
        extensions.append(
            _extension(OID_SUBJECT_ALT_NAME, False, _der_sequence(*general_names))
        )
    return _der_context(3, _der_sequence(*extensions))


class Certificate:
    """An issued certificate plus the key it was built around."""

    def __init__(self, der: bytes, key: RsaPrivateKey, common_name: str, is_ca: bool):
        self.der = der
        self.key = key
        self.common_name = common_name
        self.is_ca = is_ca
        self._pem = _pem("CERTIFICATE", der)

    def pem(self) -> bytes:
        return self._pem

    def write(self, directory: str, basename: str):
        cert_path = os.path.join(directory, basename + ".crt")
        key_path = os.path.join(directory, basename + ".key")
        with open(cert_path, "wb") as handle:
            handle.write(self._pem)
        with open(key_path, "wb") as handle:
            handle.write(self.key.pem())
        os.chmod(key_path, 0o600)
        return cert_path, key_path


def _tbs_certificate(
    subject_key: RsaPrivateKey,
    subject_cn: str,
    issuer_cn: str,
    issuer_key,
    serial: int,
    not_before,
    not_after,
    is_ca: bool,
    sans,
    client_only: bool,
) -> bytes:
    # `issuer_key` is None for a self-signed certificate (the CA itself).
    if issuer_key is None:
        signature_authority = subject_key
    else:
        signature_authority = issuer_key
    return _der_sequence(
        _der_context(0, _der_integer(2)),  # version: v3
        _der_integer(serial),
        _algorithm_identifier(),
        _name_der(issuer_cn),
        _der_sequence(_der_utc_time(not_before), _der_utc_time(not_after)),
        _name_der(subject_cn),
        _subject_public_key_info(subject_key),
        _extensions_der(is_ca, sans, client_only),
    )


def issue_certificate(
    subject_key: RsaPrivateKey,
    subject_cn: str,
    serial: int,
    not_before,
    not_after,
    issuer_cn: str = None,
    issuer_key: RsaPrivateKey = None,
    is_ca: bool = False,
    sans=(),
    client_only: bool = False,
) -> Certificate:
    """Issue one certificate. Omit `issuer_key` for a self-signed certificate."""
    if issuer_cn is None:
        issuer_cn = subject_cn
    tbs = _tbs_certificate(
        subject_key,
        subject_cn,
        issuer_cn,
        issuer_key,
        serial,
        not_before,
        not_after,
        is_ca,
        tuple(sans),
        client_only,
    )
    signer = issuer_key if issuer_key is not None else subject_key
    signature = signer.sign_pkcs1_v1_5(tbs)
    der = _der_sequence(tbs, _algorithm_identifier(), _der_bit_string(signature))
    return Certificate(der, subject_key, subject_cn, is_ca)
