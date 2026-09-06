#!/usr/bin/env bash
# SYNTHETIC case 6: shards recorded against different tested commits -> refuse.
source "$(dirname "$0")/fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
a="$T/r4/shard-0"; b="$T/r4/shard-1"; mkdir -p "$a" "$b"
wmeta "$a" r4 aaa111 t4 0 2; wmeta "$b" r4 bbb222 t4 1 2
printf 'All the tests have passed.\n' | mklog "$a" 0
printf 'All the tests have passed.\n' | mklog "$b" 1
finish "$a"; finish "$b"
expect_collect_refuse "E_COMMIT_MISMATCH" "$a" "$b"
ok "mixed commits refused"
