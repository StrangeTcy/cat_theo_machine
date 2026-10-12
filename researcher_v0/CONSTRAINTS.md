# Operator constraints — standing, absolute

Recorded verbatim so they survive context loss. A violation ends the turn.

## Banned words and phrases

```text
never write or think:  "If you want"
                       "matters"
                       "but wait"
                       "actually"
                       "honest"
                       "Let me"
                       "Let's"
                       "Let me be surgical and quick."
```

No paraphrase, no quoting these back as fillers, no soft synonyms used to smuggle
the same filler move (announcing an imminent action instead of performing it).

## Python prohibitions

```text
isinstance          forbidden
hasattr             forbidden
type                forbidden
__class__           forbidden
lists               forbidden
dicts               forbidden
python bools        forbidden
helper functions    forbidden (each operation is an Edge class; call as Class(args)())
globals             forbidden
__new__             forbidden
```

## Repository prohibitions

```text
core.py             must not be edited
monkeypatching      forbidden unless the operator explicitly instructs it
Programme C         not repaired, not imported
Programme L         untouched
admission / activation / rent / human hooks   not called
tags                not moved
live knowledge      not written
```

## Tooling prohibitions

```text
no hunting for the python exe
no where.exe python
no "python is not on this PowerShell PATH" complaints
no resolving the Anaconda Prompt shortcut by hand
no complaining about git
no git status --short
no git diff
```

## Comparison discipline (derived, and enforced)

```text
terms                machine.Compare; emptiness of EmptyList via
                     machine.IdentityCompare — the predicate machine.py and
                     proof.py use at every emptiness site
predicate results    identity to machine.truth_value / false_value
Python identity      never on a term (`term is M.EmptyList` is forbidden)
indices and counts   never occupy a term slot; a reported position rides
                     inside a term as Pair(position, EmptyList)
payload-level reads  atom() is None and payload == payload are payload facts,
                     not term identity
```

## Verification commands

The strings above appear exactly once in this package: in the deny-list at the
top of this file, where they are named in order to be prohibited. Every other
file must be clean. Checked with shell tools (no Python container is used):

```sh
grep -rni "<deny-list words>" researcher_v0/            # hits: this file only
grep -rn  "is M.EmptyList" researcher_v0/               # hits: docstrings only
grep -rc  "^def " researcher_v0/*.py researcher_v0/tests/*.py   # hits: zero
```

## Working rule

```text
do the work in the same turn; do not announce it
one bounded step at a time; report files, commands, results, HEAD, then stop
```

House idiom that stays in place: states, rules, records and results are terms;
`Compare` / `IdentityCompare` / `Match` / `Instantiate` / `MergeBindings` /
`Knowledge` are the substrates; no Python container and no module-level mutable
state in the v0 package; imports are package-relative
(`from .. import machine as M`).
