#!/bin/sh
# F4 auditor. One transcript in, a sheet out.
# Does not rewrite the log.
# final-classification is single-valued.

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

base=UncharacterizedStall
contaminated=no
if grep -q 'restoring the research checkpoint' "$t"
then
  base=RegimeC
  contaminated=yes
fi
first_taught=$(grep -m 1 '^state: taught rules ' "$t" | sed -n 's/.*taught rules \([0-9][0-9]*\).*/\1/p')
if [ -n "$first_taught" ]
then
  if [ "$first_taught" -gt 0 ]
  then
    base=RegimeC
    contaminated=yes
  fi
fi
if [ "$base" != "RegimeC" ]
then
  tl=$(grep -c '^you> teach law:' "$t" || true)
  if [ -z "$tl" ]
  then
    tl=0
  fi
  if [ "$tl" -eq 0 ]
  then
    base=RegimeA
  else
    base=RegimeB
  fi
fi
echo "base-regime-before-contamination: $base"

circular=0
if grep -q '^you> teach law: (rule (premises) (conclusion' "$t"
then
  circular=1
fi
computable=0
if grep -q 'need=(eq [0-9]' "$t"
then
  computable=1
fi

final=$base
if [ "$contaminated" = "yes" ]
then
  final=Contamination
elif [ "$circular" -eq 1 ]
then
  final=CircularRequest
elif [ "$computable" -eq 1 ]
then
  final=ComputableRequest
fi
echo "final-classification: $final"

teaches=$(grep -c '^you> teach law:' "$t" || true)
if [ -z "$teaches" ]
then
  teaches=0
fi
echo "teach law lines: $teaches"

echo "cite-coverage follows F2; run tools/f2_grader.sh on this path"
echo "instrument class: pre-D11 backward-blind"
