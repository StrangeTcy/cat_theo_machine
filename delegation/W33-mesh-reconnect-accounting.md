# W33 — Mesh reconnect attempt accounting

**Infra · Phase 7 · Suite slot `test45` · Prereq W2 ✅ W16 ✅ (independent of Phases 4–6)**

Read `delegation/README.md` first. Read DAG §6.5 (kill-phase race), §6.8 (W2 follow-up)
and §8 (W33). You own `networking/peer.py`.

## Why this worker exists

`test27` failed 49/51 once: SIGKILL of the victim also closed the *survivor's*
coordinator connection for 0.2 s (`coordinator-lost`, then `rejoined`). The
coordinator treated that as a second loss of the already re-dispatched unit, hit
`max_attempts`, and finalised it `failed / worker-lost` while the survivor still
held it queued. W2's later fixes (`cbd546a`, `1e98d3e`) ignore progress after
terminal and let a real success supersede a recorded failure — the *outcome* side.
**The attempt double-count itself is unchanged.** If the coordinator shuts down
before the survivor starts the unit, the unit is still `abandoned-on-shutdown`.

## Goal

A transient reconnect is not a second attempt. A job already re-dispatched because
a *different* peer died is not failed because this peer blinked.

1. Distinguish `member-lost` (the worker that held the job) from `coordinator-lost`
   on a different connection.
2. Pin it in `test25` and in a `test45` that reproduces the 0.2 s blink without a
   real SIGKILL if you can; otherwise extend `test27`'s kill phase with a retry loop
   that must pass twice, not once.
3. Do not drop the crash clause: a killed peer's job is still either recovered or
   reported `worker-lost`. Nothing silent.

## Done-definition

`validation/test45_mesh_reconnect_accounting.py` green. `test25` 51/51, `test27`
51/51, `test31` 50/50 still green. The §6.5 race is closed or the suite demonstrates
the remaining window.

## Files

`networking/peer.py`, possibly `networking/jobs.py`. Not `persistence.py` (W32).
Not `core.py`. Keep `framing.Duplex`.

## Non-goals

WAN features (W20, done), boot cost (W32), consensus (W17, done).

## Outcome (2026-10-21, `arena/b94f5f2e-cat-theo-machine`)

Done as briefed. `networking/peer.py` distinguishes the two at the call
site: only a severed connection (`link_loss=True` from `_serve_connection`)
is deferred; the coordinator records `member-suspect` and freezes the
member's owners/states/leases/attempts for `MeshPeer(reconnect_grace=...)`
seconds (default 5.0; 0 restores the old behaviour), while `goodbye` and
heartbeat-timeout callers resolve immediately. A same-id rejoin inside the
grace pops the deferred entry in the same lock section that re-registers
the member (`member-rejoined`); `_expire_deferred_losses`, driven by the
liveness loop, resolves the rest exactly once, reading the orphan set at
resolution time. The offer watchdog skips suspect owners.

`validation/test45_mesh_reconnect_accounting.py` (**20/20**, ~26 s, run
twice) reproduces the 0.2 s blink without a SIGKILL: it cuts a live
worker's coordinator connection while gating its rejoin (phases 1 and 5)
and also unassisted (phase 2). Against the pre-fix code phase 1 showed the
recorded failure (`states={'failed': 1, 'pending': 1}`, the survivor's
own job charged attempt 2). Gate: `test25` 51/51, `test31` 50/50, `test27`
51/51 (kill run 45.8 s, redispatches=1). A goodbye-flush defect in
`shutdown()` was found by phase 2 and fixed in the same commit. Remaining
window: an absence longer than the grace still spends the attempt (W2
supersession remains the outcome backstop), and true-crash recovery now
lands up to `reconnect_grace` + one heartbeat later than before. Full
record: DAG §4 W33 and `networking/README.md` § *Liveness*.
