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
