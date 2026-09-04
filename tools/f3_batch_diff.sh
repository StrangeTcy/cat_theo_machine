#!/bin/sh
# F3 batch residual-diff. N transcripts, pairwise identity.
# Prints a matrix of identical / distinct / incomparable.
# Exit 0 if every pair is comparable; 2 if any pair is incomparable.

set -u

PAIR=/home/user/cat_theo_machine/tools/f3-residual-diff.sh
if [ ! -x "$PAIR" ]
then
  PAIR=$(dirname "$0")/f3-residual-diff.sh
fi

if [ "$#" -lt 2 ]
then
  echo "usage: f3_batch_diff.sh <transcript> <transcript>..." >&2
  exit 2
fi

incomp=0
i=0
for a in "$@"
do
  i=$((i + 1))
  j=0
  for b in "$@"
  do
    j=$((j + 1))
    if [ "$i" -gt "$j" ]
    then
      continue
    fi
    if [ "$i" -eq "$j" ]
    then
      echo "$i $j identical $a $b"
      continue
    fi
    out=$($PAIR "$a" "$b" 2>/dev/null)
    code=$?
    if [ "$code" -eq 0 ]
    then
      echo "$i $j identical $a $b"
    elif [ "$code" -eq 1 ]
    then
      echo "$i $j distinct $a $b"
    else
      echo "$i $j incomparable $a $b"
      incomp=1
    fi
  done
done

if [ "$incomp" -eq 1 ]
then
  exit 2
fi
exit 0
