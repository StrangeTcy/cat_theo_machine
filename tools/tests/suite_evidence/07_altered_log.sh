#!/usr/bin/env bash
# SYNTHETIC case 7: raw log altered after completion -> digest validation refuses.
source "$(dirname "$0")/fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
a="$T/r5/shard-0"; b="$T/r5/shard-1"; mkdir -p "$a" "$b"
wmeta "$a" r5 deadbeef tree5 0 2; wmeta "$b" r5 deadbeef tree5 1 2
printf 'All the tests have passed.\n' | mklog "$a" 0
printf 'All the tests have passed.\n' | mklog "$b" 1
finish "$a"; finish "$b"
echo "failing_test_planted" >> "$a/raw.log"    # tamper after the digest was recorded
expect_collect_refuse "E_DIGEST_MISMATCH" "$a" "$b"
ok "altered log refused by digest validation"
