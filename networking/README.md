# `networking/` — the W2 transport (framed RPC over mutual TLS)

This package is the mesh transport for distributed search workers. It generalises
the machine's existing worker model — a manifest file in, a result snapshot out,
spawned by `search/compare_subprocess.py` — into a framed, mutually-authenticated
socket protocol, without replacing it. The file transport still works and is still
what `main.py search-worker` uses; the mesh is a second way to carry the same
contract.

## The contract that did not change

A job is a *manifest* (`start_text` / `goal_text`) plus a *search mode*; a result is
a snapshot written by the codec, with a `.manifest.json` sidecar beside it. In the
mesh, a worker runs that exact code path:

```
main.search_worker_boot(...)      # boot packs once per peer
main.search_worker_resolve_problem(...)   # per job: manifest -> agenda case
main.search_worker_execute(...)           # per job: search, checkpoints, result snapshot
```

`run_search_worker_mode` is now these three calls in sequence, so job semantics are
identical by construction — see the note under "What was fixed on the way".

## Wire format

Every frame is `| 4-byte big-endian length | UTF-8 JSON object |`, with an 8 MiB cap.
Messages carry job *descriptions* and *references*; nothing carries a machine term.

```
worker -> coordinator   join, heartbeat, job-started, job-queued, job-result, job-declined, goodbye
coordinator -> worker   welcome, heartbeat (carries the member digest), job-offer, shutdown, reject
peer -> peer            steal-request, steal-grant, steal-denied
```

`framing.TERM_PAYLOAD_KEYS` rejects a frame containing `pickle`, `term_payload`,
`machine_state` or `serialized_term`: a machine value travels as a snapshot
reference the receiver loads through the codec, never as a serialised object. That
is what "zero-copy" means in `SWARM_EVOLUTION_DAG.md` §3.

## Identity and the certificate path

Each peer holds a leaf certificate issued by a local CA, and both ends of every
connection present a certificate (`ssl.CERT_REQUIRED` on the server side, a
verifying client context on the dialling side). An unauthenticated peer cannot
complete a handshake, so refusals are TLS failures rather than application checks.

The pool of sandbox images this runs in has no OpenSSL CLI guarantee and the
documented virtualenv is `gmpy2` + `pyyaml` only, so certificates are generated **in
Python, by this repository**: `networking/x509.py` implements RSA-2048 key
generation (Miller-Rabin, gmpy2-accelerated when present), minimal DER, and X.509
v3 issuing — `basicConstraints`, `keyUsage`, `extendedKeyUsage`, `subjectAltName`
— signed with SHA-256 + PKCS#1 v1.5. Independent evidence that the output is real
X.509: `openssl x509 -text` parses it, `openssl verify -CAfile ca.crt leaf.crt`
returns OK, and Python's own `ssl` (OpenSSL 3.0.20) completes a mutual handshake
with it. Verify a generated pair yourself with:

```bash
openssl x509 -in ca.crt -noout -text
openssl verify -CAfile ca.crt leaf.crt
```

**Key material never enters the repository.** `identity.pki_directory_guard` refuses
to create or load keys that live inside the working tree unless
`HYGE_MESH_ALLOW_REPO_PKI=1` is set explicitly, and the suite's PKI lives in a
`tempfile.mkdtemp()` directory that is deleted afterwards. That is also why the
generator's private-key parser (`mesh._load_pkcs1_key`) exists rather than a
dependency: it reads back only what this package wrote.

## Membership, scopes and monotonicity

* **Discovery** is a JSON record (`coordinator.json`) in the shared PKI directory:
  the honest, inspectable version of "the coordinator is at 127.0.0.1:port". No
  mDNS, no rendezvous — there is no internet peer to find.
* **Membership** is authenticated: a worker's identity comes from its certificate,
  and the coordinator gossips the member digest in its heartbeats so workers can
  find each other without asking the coordinator again.
* **Scopes and leases.** A job declares the hypergraph content ids it touches and
  the result artifact it writes. The coordinator grants at most one lease per live
  scope, so two peers can never work — or write — the same thing at once. Distinct
  search modes over one problem have distinct result references, so they still run
  in parallel, exactly as the compare flow wants.
* **Monotonicity.** Jobs carry a per-scope sequence. A peer refuses one whose
  sequence is not greater than the highest it has completed for that scope
  (`refused-stale`), so an older input can never overwrite newer state. This is the
  mesh counterpart of the kernel's `GraphVersion` rule and the guard W17's
  monotonic snapshot broadcast will need.
* **Nothing silently lost.** Every job reaches exactly one terminal record. A peer
  whose heartbeat goes stale or whose socket dies has its leases reclaimed, and its
  jobs are re-dispatched (up to `max_attempts`) or recorded as failed with a
  reason. `mesh.write_state` dumps each peer's ledger for post-mortem inspection.

## Work stealing

Stealing is peer-to-peer, not coordinator-mediated: an idle worker opens its own
mTLS connection to a busy peer and asks for one of its *queued* (never running)
jobs. The grant carries the job's lease and sequence with it, and ownership
transfers to the thief when it reports `job-started`. That single rule is what
keeps a slow-but-alive peer from being robbed of work it is already doing, and it
is why a killed peer's mid-flight job is attributed to the peer that really lost it.

## Liveness, and what a drop costs

Two rules keep a drop from turning into lost work, and both exist because the
first version of this layer got them wrong:

* **Only a peer we have heard from directly can be "lost".** Membership arrives
  two ways: from the peer itself (join, heartbeat) and from gossip (the member
  digest the coordinator sends, and that workers forward). Gossip is a hint, not
  a liveness signal. A digest that keeps naming a dead worker would otherwise be
  re-learned on every heartbeat and declared lost again on every liveness pass —
  a loss storm, each one burning a re-dispatch attempt on work that peer never
  held. Entries learned from gossip therefore expire quietly (`hearsay-expired`);
  only a directly-heard peer produces `member-lost`, lease reclamation and job
  recovery.
* **A dropped link is repaired, not mourned.** A reader that stops (EOF, a frame
  error) closes its connection, and a worker watches its coordinator link and
  re-joins when it dies, re-announcing the jobs it still holds (`job-started` /
  `job-queued`, which transfer ownership back to it). A `member-lost` for a link
  the peer has already replaced is ignored, so a rejoin is never undone by the
  stale loss of the link it replaced.

The other half is the dispatcher, which is deliberately forgiving:

* **Every pending job is considered**, not just the oldest: a job waiting on a
  live scope must not hold back the queue behind it. Work is only offered to a
  peer we have a live connection to and whose modes cover it.
* **An offer is retried if it goes unanswered.** Delivery is best effort, so
  `_watchdog_loop` re-offers a job whose offer was never acknowledged (bounded by
  `max_attempts`). This is safe *because of* the guards rather than in spite of
  them: a peer that already advanced the scope refuses the replay as
  `refused-stale`, and a peer already holding the scope refuses it as
  `refused-scope-busy`. A stale refusal is a terminal outcome — re-offering it
  can only be refused again.
* **A failed send is not a placement.** If the offer never leaves the
  coordinator, the job returns to `pending` and its lease is dropped instead of
  being stranded as `dispatched` forever.
* **A lease is only released by its owner.** Leases are keyed by scope, and a job
  declares both the content ids it touches and the result it writes, so two jobs
  can share one declared scope. Every release (result, decline, hand-over,
  shutdown) checks the lease's job id first: one job finishing must never drop a
  lease another job is relying on for mutual exclusion.

## Running it

```bash
# coordinator (optionally with a job list and a time limit)
PYTHONPATH=/home/user .venv/bin/python main.py mesh --role coordinator \
    --cert-dir /tmp/hyge-mesh --jobs jobs.json --run-seconds 120

# worker (discovers the coordinator through the shared directory)
PYTHONPATH=/home/user .venv/bin/python main.py mesh --role worker \
    --cert-dir /tmp/hyge-mesh --cert-name worker-1 --run-seconds 120
```

`validation/test25_rpc_mtls_mesh.py` drives all of it: mTLS and its refusal paths,
the protocol invariants with stub runners, then real search jobs over real
subprocesses with a stolen job, a SIGKILLed worker, and every result compared
against the single-process run of the same manifest.

## What was fixed on the way

**The frame reader lost bytes on a poll timeout** (`networking/framing.py`).
Readers poll with a short idle timeout, so `socket.recv` may time out — and it
could time out *after* part of a frame had been read. Those bytes were dropped and
the caller resumed reading at the wrong offset, so the rest of the stream was
misparsed: the reader stopped, the peer went quiet in one direction while its
heartbeats kept flowing in the other, and every later job on that link looked
"dispatched but never answered". A frame that has started arriving is now always
read to its end (bounded by `FRAME_STALL_SECONDS`), so a poll timeout can only
mean "nothing to read yet". `test25` phase 5 pins this with a frame split across
two writes and an idle poll in between.

**Lease releases were matched by scope key alone** (`networking/peer.py`), so a job
finishing could drop the lease of a *different* job that shared its declared
scope — exactly the mutual exclusion the lease exists to provide. Releases now
match the owning job id.

**The dispatcher only ever looked at the oldest pending job**, and treated "that
one is waiting on a live scope" as "nothing to dispatch", stalling the whole queue
behind it. It now walks the pending list, skipping jobs whose scope is being
worked, and never offers work over a link that is not there.

**A connection whose reader stopped was left open**, so a worker that lost its
link never noticed and never re-joined; and a rejoin could be undone by the stale
loss of the link it replaced. Both are fixed, with the reconnect and hearsay rules
above.

**`_SearchWorkerResultGraph`** — the stand-in graph `search_worker_store_result` builds
for a result — had no `nodes`/`edges` attributes, while `SnapshotCodec.capture` has
read them unconditionally since hypergraph content became persistable (`18cdedf`).
Every checkpoint write therefore raised `AttributeError`, which means **the whole
`search-worker` mode could not write a single result** and no suite noticed, because
none of the 19 exercised that mode end to end. The two roots are now set to
`EmptyList` (a result describes an attempt, not a runtime's hypergraph), and
`test25` phase 4 keeps the file transport honest by running the CLI path for real.
