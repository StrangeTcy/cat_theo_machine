#!/bin/sh
# F2 grader. Transcript path in, five counts out.
# taught-theorem, unlock-evidence, circular-request, computable-request,
# cite-coverage (cited/uncited).
# Counts only printed operator/machine lines. No famous-sentence names.

set -u

if [ "$#" -ne 1 ]
then
  echo "usage: f2_grader.sh <transcript>" >&2
  exit 2
fi

t=$1
if [ ! -r "$t" ]
then
  echo "cannot read $t" >&2
  exit 2
fi

taught=$(grep -c '^you> teach law:' "$t" || true)
trusted=$(grep -c '^you> teach trusted theorem' "$t" || true)
if [ -z "$taught" ]
then
  taught=0
fi
if [ -z "$trusted" ]
then
  trusted=0
fi
taught=$((taught + trusted))

unlock=$(grep -c 'status=DemonstratedUsefulDependency; intervention' "$t" || true)
if [ -z "$unlock" ]
then
  unlock=0
fi

# circular: empty-premises teach whose conclusion is the last attempt/prove goal
circular=0
goal=$(grep -E '^you> (attempt goal:|prove that |prove )' "$t" | tail -n 1)
# a teach with (premises) empty and conclusion matching is circular; scan teach law lines
# Mechanical: "teach law: (rule (premises) (conclusion" with no premise terms
empty_teaches=$(grep -c '^you> teach law: (rule (premises) (conclusion' "$t")
if [ "$empty_teaches" -gt 0 ]
then
  circular=$empty_teaches
fi

# computable: a dependency need that is a ground eq of numerals, or a request
# to evaluate a fully numeric equation. Conservative: need=(eq <digit>...
computable=$(grep -c 'need=(eq [0-9]' "$t")
if [ -z "$computable" ]
then
  computable=0
fi

cited=0
uncited=0
# Walk teach-law line numbers. A teach is cited if a FAILED or residual record
# appears on an earlier line.
nl -ba "$t" | grep 'you> teach law:' | while read -r num rest
do
  before=$((num - 1))
  if [ "$before" -lt 1 ]
  then
    echo uncited
    continue
  fi
  head -n "$before" "$t" | grep -q 'FAILED. cost='
  if [ "$?" -eq 0 ]
  then
    echo CITE
  else
    echo UNCITE
  fi
done > /tmp/f2_cite_$$.txt
cited=$(grep -c '^CITE$' /tmp/f2_cite_$$.txt || true)
uncited=$(grep -c '^UNCITE$' /tmp/f2_cite_$$.txt || true)
rm -f /tmp/f2_cite_$$.txt
if [ -z "$cited" ]
then
  cited=0
fi
if [ -z "$uncited" ]
then
  uncited=0
fi

echo "taught-theorem count:       $taught"
echo "unlock-evidence count:      $unlock"
echo "circular-request count:     $circular"
echo "computable-request count:   $computable"
echo "cite-coverage cited:        $cited"
echo "cite-coverage uncited:      $uncited"
