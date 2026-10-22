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
worker -> coordinator   artifact-fetch                       (W20, `--artifacts wire` only)
either direction        artifact-begin, artifact-chunk, artifact-end, artifact-refused
coordinator -> worker   artifact-missing
```

`framing.TERM_PAYLOAD_KEYS` rejects a frame containing `pickle`, `term_payload`,
`machine_state` or `serialized_term`: a machine value travels as a snapshot
reference the receiver loads through the codec, never as a serialised object. That
is what "zero-copy" means in `SWARM_EVOLUTION_DAG.md` §3. The W20 `artifact-*`
frames do not weaken this: they carry the *bytes of the codec's own file*
(base64, chunked under the frame cap, SHA-256 named up front), which the receiver
writes to disk and then loads through the codec exactly as it would from a shared
mount — see *Beyond one filesystem* below.

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
  reason. Both halves are pinned by `validation/test25_rpc_mtls_mesh.py`, including
  the one that only fires when there is nobody left to re-dispatch to: with
  `redispatch_on_crash` off, a job orphaned by a dead peer ends as a terminal
  `failed` record naming `reason="worker-lost"` rather than staying pending forever.
  `mesh.write_state` dumps each peer's ledger for post-mortem inspection.

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
* **A dropped link is also not yet a dead peer (W33).** When a member's
  connection closes, the coordinator makes it *suspect* (`member-suspect`,
  listed in `summary()["deferred_losses"]`) for `reconnect_grace` seconds
  (5 s by default, against the worker's 0.3 s reconnect poll and 3 s join).
  Membership ends at once — a suspect is offered nothing new — but its job
  owners, states, leases, offer bookkeeping and attempt numbers are frozen
  and no terminal record is written, which also means a coordinator waiting
  for "every submitted job has a result" cannot mistake a blink for
  completion and shut down under a queued job. A rejoin with the same peer id
  inside the window cancels the loss (`member-rejoined`, no attempt charged);
  a suspect still gone at the deadline resolves into exactly the old loss,
  once: `member-lost`, leases reclaimed, one attempt charged, the job
  re-dispatched or reported `worker-lost`. A `goodbye` and a heartbeat
  timeout are never deferred — the peer said it is leaving, or it has
  already been silent for the full timeout — and the offer watchdog likewise
  does not charge an unanswered offer against an owner that is only
  suspect. `reconnect_grace=0` restores the immediate accounting. What this
  does *not* close: a peer that stays away longer than the grace is charged
  the one attempt even if it later returns with the work; the result still
  supersedes a recorded failure (below), but the attempt stays spent.

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

## Beyond one filesystem (W20): a laptop behind a tunnel and a Colab worker

Everything above assumed the W2 deployment: peers on one box or on two laptops with a
shared mount, every peer reachable by every other, and certificates whose SAN is the
address that gets dialled. A laptop plus a Colab notebook breaks all three — they share
nothing but a socket, the laptop is behind NAT and the notebook has no inbound port at
all, and whatever public name a tunnel hands out is not the one on anybody's
certificate. W20 adds four switches that remove those assumptions one at a time; with
none of them set the layer behaves exactly as before (`test25` and `test27` run in the
default `shared` mode and are unchanged).

| switch | default | what it changes |
| :--- | :--- | :--- |
| `--artifacts wire` | `shared` | job files travel inside the connection (`networking/artifacts.py`). A worker fetches a job's **input** (the W16 unit snapshot named by `unit_path`) with `artifact-fetch` and writes it under its own `--artifact-dir`; it pushes its **result** snapshot and the manifest sidecar to the coordinator *before* the `job-result` frame, on the same ordered connection, and the coordinator writes them at the exact `result_ref` it issued. Authority is asymmetric: the coordinator serves only inputs it named in a job it submitted and accepts only files at a `result_ref` it issued (`InputAuthority`, `ResultAuthority`); a worker maps every coordinator path onto its own root (`local_path_for`), so the two machines never need the same layout. Every transfer declares size and SHA-256 up front; a short or corrupt file is `artifact-refused`, never loaded. `job-result` carries `artifact_sha256` so the coordinator can tell a result from a reference to one it did not receive (`result-without-artifact`). |
| `--no-inbound` | inbound | the worker opens no listening socket and joins with `reachable: false` and `address: ""`. It can still *steal* from reachable peers; nobody can steal from it, because the steal loop never selects a member without an address. A member that *does* advertise an address nobody can dial (NAT, a one-way tunnel) costs one failed dial, a `steal-unreachable` event and a 5 s back-off rather than a retry storm. A Colab runtime is always the first kind of peer. |
| `--verify identity --expect NAME` | `hostname` | the dialling side still pins the CA, but matches the certificate's common name against `NAME` instead of matching its SAN against the address dialled. That is what makes a certificate issued on the laptop valid when the coordinator is reached through an `ngrok`/`bore` host and port: the name is a *who*, not a *where*. A mismatch is a TLS failure plus an `identity-mismatch` event, not a warning. |
| `--advertise HOST:PORT` | the bind address | the address a peer announces in its join/welcome and in the member digest, for the case where the address it binds is not the address anyone can dial (the tunnel's). |

Two more pieces make the remote end bootable without ever moving the CA key:

* `main.py mesh --role issue --cert-name colab-1 --cert-dir DIR --bundle-dir OUT` writes a
  **bundle** — `bundle.json`, `ca.crt`, `colab-1.crt`, `colab-1.key` — for one remote peer.
  The CA key stays in `--cert-dir`; the bundle is what you copy to the other machine (Drive,
  `scp`, a paste into the notebook). `identity.pki_directory_guard` still refuses a bundle
  directory inside the working tree.
* `framing.Duplex` replaces the pattern of one thread reading and another writing the same
  `SSLSocket`. That pattern looked fine on loopback for small frames and broke the moment a
  3 MiB artifact chunk was in flight: an OpenSSL object is not thread-safe, the reader's poll
  `settimeout` landed in the middle of the writer's `sendall`, and the link died with an
  `SSLEOFError` or a half-written record on one end and a stall on the other — intermittently,
  which is the worst way. `Duplex` makes the socket non-blocking, puts one lock around every call
  into OpenSSL, and waits for readability/writability on `select` with the lock released, so
  the two threads take turns instead of overlapping. All mesh `Connection`s go through it;
  the blocking `send_frame`/`recv_frame` remain for single-threaded raw clients only.

The shape of a laptop ⇄ Colab run (the step-by-step version with the tunnel commands is
`colab/README.md`; the notebook is `colab/mesh_worker.ipynb`):

```bash
# laptop: issue the notebook's bundle (CA key never leaves --cert-dir), start a tunnel
PYTHONPATH=.. .venv/bin/python main.py mesh --role issue --cert-name colab-1 \
    --cert-dir ~/hyge-pki --bundle-dir ~/hyge-bundles/colab-1
ngrok tcp 7443        # or: bore local 7443 --to bore.pub   -> gives TUNNEL_HOST:PORT

# laptop: coordinator, artifacts over the wire, advertising the tunnel's name
PYTHONPATH=.. .venv/bin/python main.py mesh --role coordinator --bind 0.0.0.0:7443 \
    --cert-dir ~/hyge-pki --artifacts wire --advertise TUNNEL_HOST:PORT \
    --jobs jobs.json --run-seconds 1800

# Colab (what the notebook runs): dial out, verify who, not where; nothing inbound
PYTHONPATH=/content python -u -m cat_theo_machine.main mesh --role worker \
    --coordinator TUNNEL_HOST:PORT --verify identity --expect coordinator --no-inbound \
    --artifacts wire --artifact-dir /content/hyge-artifacts \
    --cert-dir /content/hyge-pki --cert-name colab-1 --swarm --run-seconds 1700
```

`validation/test31_wan_mesh_artifacts.py` drives all of it on loopback: identity
verification and its refusals, a real unit snapshot fetched and a real result pushed
through a coordinator that shares no directory with the worker (corrupt and
unauthorised transfers refused), a no-inbound worker stealing and being skipped as a
steal target, and the CLI switches end to end. What it cannot drive is a real tunnel
and a real notebook — the first trial of that is yours, and the runbook says what to
look for.

## The ledger, and which events are load-bearing

Every peer keeps an ordered event log (`peer.events()`, `report()`), and the
coordinator writes `ledger.json`. Two kinds of event live there, and the
difference matters when reading a failing run:

* **Behavioural** — these are what the layer *does*, and a test asserts on them:
  `member-joined` / `member-suspect` / `member-rejoined` / `member-lost` /
  `stale-loss-ignored`, `job-submitted` /
  `job-dispatched` / `job-started` / `job-queued` / `job-result` /
  `job-redispatched` / `job-declined`, `lease-released` / `lease-transferred`,
  `rejoined` / `rejoin-failed`, `hearsay-expired`, `result-superseded`,
  `reader-stopped`, `handshake-refused`; and under W20 `artifact-fetch-requested` /
  `artifact-served` / `artifact-sent` / `artifact-incoming` / `artifact-received`,
  `artifact-missing` / `artifact-refused` / `artifact-corrupt`,
  `result-without-artifact`, `identity-mismatch`, `steal-unreachable`.
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

**A `deferred` result was counted as a failure** (`networking/protocol.py`,
`networking/peer.py`, `mesh.py`). The statuses had three different ideas of success:
a deferred job (the search concluded, the snapshot holds the plan, only the
derivation replay was skipped -- the search worker's own rc=4 under
`HYGE_SEARCH_WORKER_DEFER_DERIVATION=1`) was recorded as `done`? no: as `failed` in
the job state, invisible in `completed`, and enough to make `main.py mesh` exit 1
after a *successful* job. There is now one expression of it,
`protocol.status_is_success`, and the three call sites use it.

**A shutdown notice could be discarded before it was written**
(`networking/peer.py`). `shutdown()` queues `SHUTDOWN` to every member and then
closes the connections; a closing connection abandons what its writer still holds,
and `queue.empty()` is a lying predicate -- a writer that has just dequeued a
message still has it in hand. So the members were never told (a CLI worker spent the
rest of its life reconnecting to a coordinator that was gone, and only exited when
its caller killed it). Connections now track messages accepted-but-not-yet-written
(`Connection.flushed`) and `shutdown()` waits for the writers, not just the queue,
before letting the sockets go. `test25` phase 2 asserts a live member sees
`shutdown-requested` and stops.

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

**A finished job could be resurrected by a late progress report** (`networking/peer.py`,
found by the W16 kill test). `_note_job_progress` checked that a job was *known*
before moving it back to `running`/`queued`, but not that it was *finished*. Kill a
worker mid-job and the sequence is reachable: the job is orphaned, re-dispatched,
lost again past `max_attempts`, recorded `failed` — and then run anyway by a peer
that still had it queued, whose `job-started` the coordinator accepted. Because
`_finish_job` never overwrites a terminal record, the ledger ended up claiming
`job_states {done: 3, running: 1}` beside `terminal: 4`, and whatever the second
run produced was dropped. The swarm still reported the loss instead of losing it
silently, so the crash clause held; the ledger simply could not be trusted. A
progress report for a job that already has a terminal record is now ignored and
recorded as `progress-after-terminal-ignored`, which is a diagnostic and not
behaviour — nothing depends on it except the check that pins the guard.

**The other half of that: a computed proof was being thrown away.** Stopping the
ledger from claiming a finished job is running does not stop the job from being
run. The job that ran out of attempts was still queued on a peer, which proved it
and handed the result back — and `_handle_job_result` refused it, because a
recorded failure was final unless it had been *provisional*. The swarm then
reported a failure while a proof sat on a worker's disk. Any recorded failure now
gives way to a real success, on both the inbound and the local path, and a
recorded success stays final, so at most one supersession can happen per job.
The ordering that makes that safe is the one that was already there: never replace
a success, never record a second failure. `result-superseded` now says which kind
of failure it replaced — `presumed` or `recorded` — because the second is the one
that means the attempt budget raced a peer, which is worth seeing.

**A transient reconnect was charged as a second attempt** (`networking/peer.py`,
W33, found by the W16 kill test, DAG §6.5). Supersession healed that job's
*outcome* when the survivor eventually started it, but the accounting that
produced the failure was untouched: the SIGKILL that closed the victim's
connection also closed the *survivor's* for 0.2 s, the coordinator treated
that EOF as a second loss of the already re-dispatched unit, the attempt
budget hit its ceiling, and the unit was finalised `failed` / `worker-lost`
while still queued on a live worker — at which point a coordinator whose
run loop stops when every job has a terminal record could shut down before
the unit ever started, the one ordering supersession cannot heal. A closed
connection is now suspect before it is a loss (see *Liveness* above):
nothing is charged, released or recorded until the peer either rejoins
inside `reconnect_grace` or stays gone past it, and
`validation/test45_mesh_reconnect_accounting.py` reproduces the §6.5
sequence with stub runners and shows the pre-fix ledger
(`states={'failed': 1, 'pending': 1}` after the blink) turning into no
terminal record, no charged attempt, and the unit run once by its holder.
Found on the way, and fixed in the same commit because the goodbye/loss
distinction is now load-bearing: `shutdown()`'s writer-flush wait covered
`_connections` but not a worker's coordinator connection, so the socket
could close on a `GOODBYE` its writer thread had not sent yet, and the
coordinator would see a bare link loss where the peer had said it was
leaving.
