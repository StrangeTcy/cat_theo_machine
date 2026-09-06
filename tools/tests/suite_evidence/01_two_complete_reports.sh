#!/usr/bin/env bash
# SYNTHETIC case 1: two complete shard reports -> collection succeeds,
# full report text preserved, admission left PENDING.
source "$(dirname "$0")/fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
a="$T/r0/shard-0"; b="$T/r0/shard-1"; mkdir -p "$a" "$b"
wmeta "$a" r0 deadbeef tree0 0 2; wmeta "$b" r0 deadbeef tree0 1 2
printf 'All the tests have passed.\n' | mklog "$a" 0
printf 'All the tests have passed.\n' | mklog "$b" 1
finish "$a"; finish "$b"
expect_collect_ok "$T/ev.txt" "$a" "$b"
grep -q "baseline-admission-decision: PENDING" "$T/ev.txt" || fail "admission not left pending"
grep -q "tests-failed: none listed" "$T/ev.txt" || fail "green status wrong"
ok "two complete reports collected"
