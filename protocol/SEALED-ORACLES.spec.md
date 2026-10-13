# Sealed-oracle protocol

F audit machinery is the home of the sealing format. INT or the oracle
keeper executes the seal. F does not open a sealed file in a live
session and does not teach from one.

## format

```text
content-id:     <hash of the sealed bytes>
training-visible: no
sealed-at:      <ISO date>
path:           sealed/<content-id>.oracle
keeper:         oracle-keeper | INT
```

## rules

- A sealed oracle is not a curriculum. It is consulted after a
  transcript is recorded, to grade what was asked for.
- `training-visible: no` forbids packs, talk lessons, research
  checkpoints, and operator prompts from carrying the bytes.
- The dated path is the only locator. Copies outside `sealed/` are
  a contamination defect.
- F-op never reads the sealed bytes while a session is open.
- CUR-ENGEL-E3-ORACLE: sealing owed to oracle-keeper/INT, not yet
  executed. This spec is the format; the seal is not performed here.

## audit hook (F4)

A transcript whose prompt or teach text matches a sealed content-id's
payload is contamination: oracle-in-prompt. The check runs after the
session, never during it.
