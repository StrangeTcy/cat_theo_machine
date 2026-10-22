# W20 — The mesh beyond one filesystem: a laptop behind a tunnel and a Colab worker

**Swarm / Infra · Phase 3 (late) · Suite slot `test31` · Prereqs: W2 ✅ W16 ✅ · Owner: any session**

> **Status: landed 2026-10-15** on `arena/717c9822` (`aaac6de`, `6301d7c`, `70a5699`, `cedae50`):
> `networking/artifacts.py`, `framing.Duplex`, the W20 switches in `networking/peer.py` /
> `mesh.py` / `main.py mesh`, `colab/mesh_worker.ipynb`, `colab/README.md` §A,
> `validation/test31_wan_mesh_artifacts.py` (50/50, ~60 s). `test25` (51/51) and `test27`
> (all green) are unchanged in the default `shared` mode. **Loopback-verified only**: the
> sandbox has no tunnel and no Colab; the first real laptop ⇄ notebook run is the user's, and
> the runbook names the events to look for in the ledger.

Read `delegation/README.md` first. Invariant 2's "zero-copy" clause (`framing.TERM_PAYLOAD_KEYS`)
stays binding: nothing in W20 serialises a machine term over the wire. What crosses is the
codec's own snapshot *file*, chunked and digest-named, loaded by the receiver through the
codec exactly as from a shared mount. There is still one serialisation of a machine term,
and it is the snapshot.

## The problem

W2's mesh assumes a deployment it was built in: one box, or two laptops with a shared mount.
Three assumptions follow and all three fail for a laptop plus a Colab runtime:

| assumption | where it lives | why Colab breaks it |
| :--- | :--- | :--- |
| a job carries *paths* and both ends read/write them | `networking/jobs.py`, the runners | a notebook VM shares nothing with the laptop but a socket |
| every peer is dialable (join address, steal dials, the shared-directory discovery file) | `networking/peer.py` | Colab has no inbound port; the laptop is behind NAT and needs a tunnel |
| the certificate's SAN is the address being dialled | `networking/identity.py`, `mesh.py` | a `trycloudflare.com` / `bore.pub:NNNNN` name is nobody's SAN, and it changes per run |

## What landed

1. **`--artifacts wire`** (`networking/artifacts.py`; `protocol.ARTIFACT_*`). A worker fetches a
   job's **input** (the W16 unit snapshot named by `unit_path`) with `artifact-fetch` and writes
   it under its own `--artifact-dir`; it pushes its **result** snapshot and manifest sidecar to
   the coordinator *before* the `job-result` frame on the same ordered connection, and the
   coordinator writes them at the exact `result_ref` it issued. 3 MiB raw chunks (base64 under
   the 8 MiB frame cap), size and SHA-256 declared in `artifact-begin`, short or corrupt files
   `artifact-refused` and never loaded; `job-result` carries `artifact_sha256` and a result that
   arrives without its file is recorded `result-without-artifact`. Authority is asymmetric and
   path-free: the coordinator serves only inputs it named in jobs it submitted and accepts only
   its own `result_ref`s (`InputAuthority`, `ResultAuthority`); the worker maps coordinator
   paths onto its own root (`local_path_for`), so the two machines never share a layout.
2. **`--no-inbound`**: the worker opens no listener, joins with `reachable: false` and an empty
   address, can steal from reachable peers and is never selected as a steal target. A member
   that advertises an undialable address costs one failed dial, `steal-unreachable` and a 5 s
   back-off instead of a retry storm.
3. **`--verify identity --expect NAME`** (`protocol.VERIFY_IDENTITY`): under the CA pin, match
   the certificate's common name against the name expected instead of its SAN against the
   address dialled; a mismatch is a TLS failure plus `identity-mismatch`. Member records now
   carry the TLS-proven common name, and steal dials verify it too.
4. **`--advertise HOST:PORT`**: the address a peer announces (join, welcome, member digest)
   when the one it binds is not the one anyone can reach.
5. **`mesh --role issue --cert-name colab-1 --bundle-dir OUT [--sans …]`** (`mesh.issue_bundle`):
   a bundle of `ca.crt` + leaf cert + leaf key + `bundle.json` for a remote peer. The CA key
   never leaves `--cert-dir`; the bundle directory is guarded against the working tree like
   every other PKI path.
6. **`framing.Duplex`** — the fix that the artifact transfers forced. The mesh `Connection` has
   always read the socket from one thread and written it from another; on an `SSLSocket` that
   is unsound (one OpenSSL object, not thread-safe), and it broke the moment a 3 MiB chunk
   was in flight: the reader's poll `settimeout` landed inside the writer's `sendall`, and the
   link died with `SSLEOFError` / a half-written record on one side and a stall on the other,
   intermittently. `Duplex` makes the socket non-blocking, serialises every call into OpenSSL
   under one lock, and waits on `select` with the lock released; `pending()` is consulted
   before every wait because TLS may have decrypted more than was asked for. All mesh
   connections use it; blocking `send_frame`/`recv_frame` remain for single-threaded clients.
7. **`colab/mesh_worker.ipynb`** + **`colab/README.md` §A**: clone the branch, place the
   bundle under `/content/hyge-pki` (never under the repository), run the worker command
   against the tunnel address, read the ledger afterwards. The tunnel options compared in
   the runbook are `ngrok tcp 7443`, `bore local 7443 --to bore.pub` and `ssh -R` to a VPS.

## The suite (`validation/test31_wan_mesh_artifacts.py`, 50 checks)

`phase_identity` — hostname vs identity verification, the wrong-name refusal (a ledger
event naming both sides), a leaf from an untrusted CA refused in both directions. `phase_artifacts` — a real unit snapshot
fetched by a worker whose artifact root is a different temp dir from the coordinator's, a
real result pushed back at the issued `result_ref`, corrupt and unauthorised transfers
refused, `result-without-artifact` recorded. `phase_steal` — a no-inbound worker steals from
a reachable peer and is skipped as a target; an undialable advertised address backs off.
`phase_cli` — `main.py mesh --role issue` (the bundled key is the leaf's, never the CA's),
then coordinator + `--no-inbound --verify identity --artifacts wire` worker as real subprocesses over real search jobs, success read through
`protocol.status_is_success` (a `deferred` result is a success; see the W2 fix log).
`T31_PHASES=123` skips the 47 s CLI phase.

## What the first real run will tell you that loopback cannot

* **Latency × heartbeat**: the liveness window (`networking/README.md`, *Liveness*) was tuned
  on loopback. A tunnel adds 50–300 ms per round trip; if `member-lost` / `rejoined` pairs
  appear in the ledger with no network incident, widen the window before suspecting the
  transport.
* **Throughput of the artifact path**: a W16 unit snapshot is 3–30 MB; at Colab's typical
  egress that is seconds per job, and the per-job boot (~12–30 s, §6.3) still dominates. If
  it does not, chunk size and parallel fetch are the knobs.
* **Colab runtime limits**: the VM is recycled on idle; `--run-seconds` should be under the
  session budget. The worker's own ledger lands in `/content/hyge-pki/peer-<name>.json` when
  it stops; the coordinator's `ledger.json` on the laptop is the authoritative account.
* **The tunnel's address changes per run** (ngrok's free tier, bore): `--advertise` and the
  notebook's `COORDINATOR` field must be updated together; identity verification is what makes that
  harmless.
