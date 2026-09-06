#!/usr/bin/env bash
# SYNTHETIC case 2: more than 25 failures in the reports -> none omitted.
source "$(dirname "$0")/fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
a="$T/r1/shard-0"; b="$T/r1/shard-1"; mkdir -p "$a" "$b"
wmeta "$a" r1 deadbeef tree1 0 2; wmeta "$b" r1 deadbeef tree1 1 2
{ for i in $(seq 1 30); do echo "failing_test_alpha_$i"; done; } | mklog "$a" 0
{ for i in $(seq 1 5);  do echo "failing_test_beta_$i";  done; } | mklog "$b" 1
finish "$a"; finish "$b"
expect_collect_ok "$T/ev.txt" "$a" "$b"
grep -q "tests-failed: yes (35 names across shards)" "$T/ev.txt" || fail "failure total wrong: $(grep tests-failed "$T/ev.txt")"
n=0; for i in $(seq 1 30); do grep -q "failing_test_alpha_$i" "$T/ev.txt" || { echo "missing alpha $i"; exit 1; }; n=$((n+1)); done
for i in $(seq 1 5); do  grep -q "failing_test_beta_$i"  "$T/ev.txt" || { echo "missing beta $i"; exit 1; }; n=$((n+1)); done
[ "$n" -eq 35 ] || fail "only $n of 35 names found"
grep -q "failing_test_alpha_1$" "$T/ev.txt" || fail "first failure lost (head window suspected)"
grep -q "failing_test_alpha_30$" "$T/ev.txt" || fail "last failure lost (tail window suspected)"
ok "35 failures preserved, no window truncation"
