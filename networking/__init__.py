"""The W2 transport: framed RPC over mutual TLS for distributed Hyge workers.

Modules, in dependency order:

* `x509`     -- pure-Python RSA key generation and X.509 issuing (no dependencies)
* `identity` -- a peer's certificate material, the local PKI, and SSL contexts
* `framing`  -- length-prefixed JSON frames; machine terms never cross the wire
* `protocol` -- message kinds, jobs, scopes and leases
* `jobs`     -- running a job on a booted runtime; projecting a result for comparison
* `peer`     -- the peer itself: listener, membership, dispatch, stealing, liveness

`mesh.py` (repository root) sits on top and handles discovery, roles and the CLI.
"""

from . import framing, identity, jobs, peer, protocol, x509

__all__ = ["framing", "identity", "jobs", "peer", "protocol", "x509"]
