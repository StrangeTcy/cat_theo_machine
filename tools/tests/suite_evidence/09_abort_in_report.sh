#!/usr/bin/env bash
# SYNTHETIC case 9 (instrument-crash class from preflight step 4): shard
# aborted during install with a traceback after the report marker -> refusal.
source "$(dirname "$0")/fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
a="$T/r7/shard-0"; b="$T/r7/shard-1"; mkdir -p "$a" "$b"
wmeta "$a" r7 deadbeef tree7 0 2; wmeta "$b" r7 deadbeef tree7 1 2
{ echo "SHARD 0 elapsed 0.50"; echo "Traceback (most recent call last):"; echo "  crash in install_default_tests"; } | mklog "$a" 0
printf 'All the tests have passed.\n' | mklog "$b" 1
finish "$a"; finish "$b"
expect_collect_refuse "E_ABORT_IN_REPORT" "$a" "$b"
ok "aborted shard refused, never averaged into a baseline"
