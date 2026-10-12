# W2 — Distributed RPC & mTLS mesh

**Infrastructure · Phase 0 (still open; the last substrate gap) · Suite slot `test25` · Prereqs: none**

Read `delegation/README.md` first — shared invariants, environment facts and pitfalls are
binding here. W2 is the single blocker for both Phase-3 workers (W16, W17), so it is the
highest-leverage open item in the DAG.

## Start from what exists — do not invent a second protocol

There is already a working distributed-ish worker model, and it is **file + subprocess
based**:

- `main.py` CLI modes: `cold | warm | test | inspect | search-worker`.
- `run_search_worker_mode(worker_mode, result_path, timeout_seconds=6000)` — boots from packs
  (or resumes from a snapshot when `HYGE_SEARCH_WORKER_RESUME_DERIVATION=1`), runs one search
  mode, writes a result snapshot.
- `search/compare_subprocess.py` — spawns workers with `subprocess.Popen(..., stdout=PIPE,
  stderr=STDOUT)` and writes a `<result_path>.manifest.json` sidecar describing the job.
- `_search_worker_result_manifest_path`, `_search_worker_mode_label`,
  `_search_worker_mode_heuristic`, `_search_worker_problem_from_manifest`,
  `_maybe_set_search_worker_memory_limit` in `main.py`.
- `persistence.py` — the snapshot codec, which already parallelises registry restoration with
  `spawn` shards (`_restore_constructor_registry_parallel`), and now persists hypergraph
  `nodes`/`edges` as well as kernel roots.

So: job description = manifest JSON, result = snapshot, transport = files. That design works
and is tested. **Your task is to generalize the transport, not to replace the semantics.**
Keep the manifest/result contract intact so `search-worker` mode and W16 can both use either
transport.

`networking/` and `mesh.py` **do not exist** — the DAG names them as your deliverables.

## Hard environment constraints (design around these, they are not negotiable)

- 2 vCPU, ~3.8 GiB RAM. A mesh of more than a handful of local workers will thrash; design for
  correctness at 2–4 workers and let scale be a parameter.
- **Loopback only.** Outbound network is restricted to a small allowlist of hosts
  (github.com, api.github.com, registry.npmjs.org, pypi.org, files.pythonhosted.org). There
  is no peer to talk to. Everything must be testable on `127.0.0.1` with multiple processes on
  one box.
- No `docker`, no `java`. No third-party RPC frameworks from PyPI beyond what is already
  installed (`gmpy2`, `pyyaml`) — stdlib `socket`, `ssl`, `struct`, `json`, `subprocess`,
  `multiprocessing` only.
- TLS: `ssl` can do mTLS with locally generated certificates. The sandbox has no `openssl`
  CLI guarantee — generate the CA/leaf certs **in Python** (`ssl` + `cryptography` if
  available, else fall back to a documented self-signed generation path) and commit nothing
  secret. If real mTLS cannot be established in-sandbox, implement the full handshake against
  locally generated material and prove the *refusal* paths (unknown peer rejected, expired
  cert rejected, wrong CA rejected) — negative tests are the valuable part here.

## Goal

1. `networking/` — a hyperedge-aware RPC layer: framed messages over a socket, carrying job
   manifests and result references; work-stealing between peers; heartbeats; clean shutdown.
   "Zero-copy" in the DAG's §3 means *don't serialise the same term twice* — pass snapshot
   references, not term payloads, and let the receiver load from the codec.
2. `mesh.py` — peer discovery and membership on loopback, role assignment, and the mTLS
   identity layer (each worker gets a cert; peers authenticate mutually; unauthenticated
   peers are refused).
3. Work-stealing that is *safe under the machine's semantics*: a stolen job must produce the
   same result as a locally run one. Snapshot monotonicity is the guard — see W17's brief and
   `graph.py`'s version handling.

## Done-definition

- A suite that starts 2–4 real subprocesses on loopback, dispatches a search job to each, has
  at least one job stolen by an idle peer, and verifies every result is identical to the
  single-process result for the same manifest.
- mTLS proven both ways: an authenticated peer is admitted, and each refusal path (unknown
  cert, wrong CA, expired) is demonstrated by a test that expects rejection.
- Crash behaviour: kill a worker mid-job, show the mesh notices, and show the job is either
  re-dispatched or reported failed — never silently lost.
- No file-transport regression: `run_search_worker_mode` and `search/compare_subprocess.py`
  still work unchanged, and the new transport is selectable.
- Machine purity applies to any machine value crossing the wire: terms are carried by the
  snapshot codec's format, not by `pickle` of machine objects. `pickle` of arbitrary machine
  state is a correctness and security hazard; if you need it for a control-plane message, keep
  it to plain Python control data and say so.

## Files

- New: `networking/__init__.py` + modules, `mesh.py`, `validation/test25_rpc_mtls_mesh.py`.
- Extend: `main.py` (a mesh/peer CLI mode alongside `search-worker`), `persistence.py` (only
  if a transport needs a codec hook — prefer not to; it was just reconciled and 19 suites
  depend on it).
- Do not edit `core.py`. Do not weaken `checker_b.py` or the promotion ledger.
- Keep generated certs and any run artifacts **out of git** (add to `.gitignore` if needed);
  this repo already carries committed `.pyc` and snapshot artifacts from earlier sessions, and
  the reconciliation deliberately excluded 80 such files. Do not add more.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test25_rpc_mtls_mesh.py` green, plus all
19 existing suites green. Highest regression risk: `test12` (persistence cold resume — 7
probes, including a committed fixture `snapshots/hyge_snapshot_current.json` that must stay
present), and anything exercising `search-worker` mode. Bind your suite's sockets to port 0
and read back the assigned port, so parallel runs never collide.

Budget wall-clock: subprocess-spawning suites are the slowest here (`test13` ~24 s, `test18`
~28 s on 2 vCPU). Keep your suite under ~120 s.

## Non-goals

Internet-scale deployment, cross-host routing, consensus (W17's brief), the prover swarm's
search partitioning policy (W16's brief), and `core.py` edits.
