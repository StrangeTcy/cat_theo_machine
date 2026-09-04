#!/bin/sh
# F4 auditor. One transcript in, a sheet out.
# Does not rewrite the log.

set -u

if [ "$#" -ne 1 ]
then
  echo "usage: f4_auditor.sh <transcript>" >&2
  exit 2
fi

t=$1
if [ ! -r "$t" ]
then
  echo "cannot read $t" >&2
  exit 2
fi

echo "session-id: $(basename "$t")"

if grep -q 'theorem packs loaded:' "$t"
then
  echo "packs: loaded"
else
  echo "packs: not loaded"
fi

state=$(grep -m 1 '^state: taught rules ' "$t" || true)
if [ -n "$state" ]
then
  echo "$state"
else
  echo "state: missing"
fi

if grep -q 'audit knowledge' "$t"
then
  echo "audit knowledge: present"
else
  echo "audit knowledge: missing"
fi

# loaded-class list: first audit block mentions a class name
first_audit=$(awk '/audit knowledge \(research runtime/{flag=1; next} flag && /^you>/{exit} flag{print}' "$t")
if echo "$first_audit" | grep -q 'LIBRARY_THEOREM\|DOMAIN_AXIOM\|HUMAN_SUPPLIED\|theorem packs:'
then
  echo "loaded-class list: present"
else
  echo "loaded-class list: missing"
  echo "D12: first audit omits loaded classes"
fi

if grep -q 'restoring the research checkpoint' "$t"
then
  echo "regime-hint: C restored-checkpoint"
elif grep -q 'theorem packs loaded:' "$t"
then
  echo "regime-hint: A/B packs-on"
else
  echo "regime-hint: A/B packs-off"
fi

teaches=$(grep -c '^you> teach law:' "$t" || true)
if [ -z "$teaches" ]
then
  teaches=0
fi
echo "teach law lines: $teaches"

echo "cite-coverage follows F2; run tools/f2_grader.sh on this path"
echo "instrument class: pre-D11 backward-blind"
