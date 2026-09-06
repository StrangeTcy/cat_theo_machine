#!/usr/bin/env bash
# Run every acceptance case for the suite-evidence tools (SYNTHETIC fixtures
# plus one real-wrapper kill test). One line per case; non-zero on any FAIL.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
total=0
fails=0
for case in "$here"/[0-9][0-9]_*.sh; do
  total=$((total+1))
  name="$(basename "$case" .sh)"
  out="$(bash "$case" 2>&1)"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "PASS $name"
  else
    echo "FAIL $name"
    echo "$out" | sed 's/^/    /'
    fails=$((fails+1))
  fi
done
green=$((total-fails))
echo "cases: $green/$total green"
[ "$fails" -eq 0 ]
