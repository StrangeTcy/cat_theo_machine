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

`test25` proves both halves of that: phase 2 drives the handshake itself (two
peers, real mTLS sockets, stub jobs so the queue is deterministic), and phase 3
does it with real subprocesses and real searches — two jobs go to the only peer
there is, a second worker joins, and the queued one is stolen from under the first
(`stolen_from=worker-1-…` on its result, `ran_by=worker-2-…`, exactly one terminal
record for it, and that result still equals the same job run alone in a fresh
process). A *placement* is never re-offered, so the only way that job can move is
the thief's own request.

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

* **A heartbeat is not a question.** Each pair of peers has its own periodic
  sender — the coordinator's loop tells every member it is alive and gossips the
  member digest, each worker's loop tells the coordinator it is alive — and
  neither answers what it receives. Replying to a heartbeat is redundant, and it
  is unbounded: two peers answering each other's heartbeats answer the answers
  forever, at wire speed, until offers, results and joins queue up behind the
  storm and the link looks broken while it is only saturated.

How long a peer may be silent before it is declared lost is `MeshPeer`'s default
(20 s, against a 0.4 s heartbeat): a busy peer is a silent peer, because running a
search holds the interpreter, and shortening that fuse is how a healthy worker gets
declared lost mid-job. The CLI therefore takes the class default rather than
passing a shorter one of its own.

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

## The ledger, and which events are load-bearing

Every peer keeps an ordered event log (`peer.events()`, `report()`), and the
coordinator writes `ledger.json`. Two kinds of event live there, and the
difference matters when reading a failing run:

* **Behavioural** — these are what the layer *does*, and a test asserts on them:
  `member-joined` / `member-lost` / `stale-loss-ignored`, `job-submitted` /
  `job-dispatched` / `job-started` / `job-queued` / `job-result` /
  `job-redispatched` / `job-declined`, `lease-released` / `lease-transferred`,
  `rejoined` / `rejoin-failed`, `hearsay-expired`, `result-superseded`,
  `reader-stopped`, `handshake-refused`.
* **Diagnostic** — kept because a transport that fails silently costs hours:
  the `closed_by` chain on a `connection-closed` (`connection.close()` with no
  reason records the four frames that did it), the `on_close` callback that
  guarantees the close is recorded at all, `steal-dialled`, and the
  `member-lost=… members=… closed=…` detail `test25` prints on failure.

Neither kind carries machine semantics, and no event ever decides behaviour: the
guards (scopes, sequences, leases, direct-only loss) are what make the transport
safe, and the events are how a reader checks the guards did their job.

## What was fixed on the way

**Heartbeats were answered, and the answers were answered** (`networking/peer.py`).
`_note_heartbeat` refreshed the sender's record and then sent a heartbeat back.
Two peers doing that to each other never stop: each message provokes one more, so
the link carries heartbeats at whatever rate the two threads can manage — measured
at ~17,000 frames in 10 s, and ~32,000 in 30 s when the link was failing — and the
frames that matter (offers, results, joins) queue up behind them. That is what the reconnect storms were: the
connection was not dropping work, it was drowning in liveness traffic, which also
explains why every hung case had a peer at 100 % CPU. Heartbeats are now
one-directional and unanswered; the same test phase that used to send 17,000
frames in 10 s now sends ~106 in 15 s, and `test25`'s wall time went from a bimodal
10 s/35 s to a flat 16.6 s over seven consecutive green runs.

**The frame reader read *any* socket error as a clean EOF** (`networking/framing.py`).
The idle poll timeout was already handled, but on a TLS socket the same condition
also arrives as `ssl.SSLWantReadError` — which is an `OSError` but *not* a
`TimeoutError` — so it fell into the branch that returns `None`, i.e. "the peer
closed the connection". A refused handshake alert (`SSLV3_ALERT_CERTIFICATE_EXPIRED`),
a bad record, or an `EBADF` from a descriptor closed underneath the reader were all
reported the same way: an expired certificate became indistinguishable from a peer
that left quietly. Now only a real EOF is an EOF (`SSLEOFError`,
`SSLZeroReturnError`, a zero-length read); want-read/want-write are a poll that
returns `socket.timeout` to the caller, and anything else is raised.

**The result projection pretty-printed the proof** (`networking/jobs.py`). Machine
semantics were meant to be compared through digests of `PrettyTerm` text, but
pretty-printing a realistic plan rebuilds machine ids per node and does not finish:
on a 31-object plan that describes the whole proof, `PrettyTerm` was still spinning
at 100 % CPU after fifteen minutes. The reference run in `test25` phase 3 therefore
never completed, and the two "hung" phase-3 runs were this, not the transport. The
projection now reads the snapshot's own persisted object graph — the codec's flat
object table, whose ids come from the codec's traversal — and digests the closure of
the roots it cares about (`worker_plan`, `derivations`, `search_history`). It is the
same evidence, read directly: two independent runs of one job produce byte-identical
closures and equal digests in ~0.7 s per snapshot, and the status comes from the
machine's own label singletons rather than a string round trip.

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
