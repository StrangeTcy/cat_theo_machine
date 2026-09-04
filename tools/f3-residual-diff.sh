#!/bin/sh
# F3 residual-diff tool.
# Compares first-stall rows of two transcripts.
# Exit: 0 identical, 1 distinct, 2 incomparable.
# Fields: cost, partial-match count, unmatched-premise count, residual head.
# Goal term is not an identity field.

set -u

usage() {
  echo "usage: f3-residual-diff.sh <transcript-a> <transcript-b>" >&2
  echo "exit 0 identical / 3 silence-class / 1 distinct / 2 incomparable" >&2
  exit 2
}

if [ "$#" -ne 2 ]
then
  usage
fi

a=$1
b=$2

if [ ! -r "$a" ]
then
  echo "incomparable: cannot read $a" >&2
  exit 2
fi
if [ ! -r "$b" ]
then
  echo "incomparable: cannot read $b" >&2
  exit 2
fi

extract_cost() {
  grep -m 1 'FAILED. cost=' "$1" | sed -n 's/.*FAILED. cost=\([0-9][0-9]*\).*/\1/p'
}

extract_partial() {
  grep -m 1 'genuine partial match:' "$1" | sed -n 's/.*genuine partial match: \([0-9][0-9]*\).*/\1/p'
}

extract_head() {
  grep -m 1 'residual record:' "$1" | sed -n 's/.*residual record: (\([^ ]*\).*/\1/p'
}

extract_unmatched() {
  # first stall: "concrete unmatched formal premises: none" or a residual: missing line
  u=$(grep -m 1 'concrete unmatched formal premises:' "$1" | sed -n 's/.*concrete unmatched formal premises: \(.*\)/\1/p')
  if [ -z "$u" ]
  then
    if grep -q 'residual: missing ' "$1"
    then
      echo missing
    else
      echo none
    fi
  else
    echo "$u"
  fi
}

ca=$(extract_cost "$a")
cb=$(extract_cost "$b")
pa=$(extract_partial "$a")
pb=$(extract_partial "$b")
ha=$(extract_head "$a")
hb=$(extract_head "$b")
ua=$(extract_unmatched "$a")
ub=$(extract_unmatched "$b")

if [ -z "$ca" ] || [ -z "$cb" ] || [ -z "$pa" ] || [ -z "$pb" ]
then
  echo "incomparable: missing cost or partial-match field" >&2
  echo "a cost=$ca partial=$pa head=$ha unmatched=$ua" >&2
  echo "b cost=$cb partial=$pb head=$hb unmatched=$ub" >&2
  exit 2
fi

if [ -z "$ha" ]
then
  ha=none
fi
if [ -z "$hb" ]
then
  hb=none
fi

echo "a cost=$ca partial=$pa head=$ha unmatched=$ua"
echo "b cost=$cb partial=$pb head=$hb unmatched=$ub"

if [ "$ca" = "$cb" ] && [ "$pa" = "$pb" ] && [ "$ha" = "$hb" ] && [ "$ua" = "$ub" ]
then
  echo identical
  exit 0
fi

silence_a=0
silence_b=0
if [ "$pa" = "0" ] && [ "$ua" = "none" ]
then
  if [ "$ha" = "zero-successor-root" ] || [ "$ha" = "none" ]
  then
    silence_a=1
  fi
fi
if [ "$pb" = "0" ] && [ "$ub" = "none" ]
then
  if [ "$hb" = "zero-successor-root" ] || [ "$hb" = "none" ]
  then
    silence_b=1
  fi
fi
if [ "$silence_a" -eq 1 ] && [ "$silence_b" -eq 1 ]
then
  echo silence-class
  exit 3
fi

echo distinct
exit 1
