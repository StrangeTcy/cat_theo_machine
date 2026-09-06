#!/usr/bin/env bash
# SYNTHETIC case 3: child exits before producing a report -> refusal.
source "$(dirname "$0")/fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
a="$T/r2/shard-0"; b="$T/r2/shard-1"; mkdir -p "$a" "$b"
wmeta "$a" r2 deadbeef tree2 0 2; wmeta "$b" r2 deadbeef tree2 1 2
{ echo "Reading pack order-sign..."; } > "$a/raw.log"        # exited early: no marker, no report
printf 'All the tests have passed.\n' | mklog "$b" 1
finish "$a"; finish "$b"
expect_collect_refuse "E_REPORT_TRUNCATED" "$a" "$b"
[ -e "$T/ev.txt" ] && fail "evidence file manufactured despite refusal"
ok "report-less completion refused"
