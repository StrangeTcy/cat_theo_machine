# LIVE-INTEGRATION-REPAIR

Date: 2026-09-12 UTC
Repair base: ed1d759fb44246c95cb2d45f000d023781c506f0
Permitted session branch: arena/01a092ed-cat-theo-machine

## Fix A
SHA: b0390fcbb9c943e49697da94f9b4afd796c38e8c
paused-resume: repaired
pristine base: 55b773de6a6f5fd07d1ad63a068b7b324b2e6d30 (pass)
original candidate: ed1d759fb44246c95cb2d45f000d023781c506f0 (fail)
repaired candidate: b0390fcbb9c943e49697da94f9b4afd796c38e8c (pass)

Independent workers were discarding the restored comparison job.
A matching paused job now resumes in-process on the requested
start/goal/rules. Mismatched jobs and missing/corrupted/unmatched
worker requests are refused; bundled-example fallback is not restored.

## Fix B
SHA: e8cc54affdbf40d10b6bd8b61caab9ba85fd10f0
real workers reached through _prove: yes
knowledge/cache/mode regressions: pass
worker failure handling: unsuccessful comparison stays failure

The cache/comparison block no longer sits after the knowledge-goal
return. Ordinary concrete non-knowledge proofs reach CompareSearchModes.
Research and evaluation still skip those shortcuts.

## Combined live acceptance
worker receipts: 15 / 15
formal query: four
isolated-state and foreign-marker checks: pass
dated raw artifacts: verification/2026-09-12-repair-*
remaining failures: none
ready for INT admission rerun: yes
tags cut: none
