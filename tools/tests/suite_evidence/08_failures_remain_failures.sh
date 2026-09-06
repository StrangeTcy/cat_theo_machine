#!/usr/bin/env bash
# SYNTHETIC case 8: completed suite WITH recorded failing tests -> failures
# remain failures; exit status 0 never becomes an all-green claim.
source "$(dirname "$0")/fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
a="$T/r6/shard-0"; b="$T/r6/shard-1"; mkdir -p "$a" "$b"
wmeta "$a" r6 deadbeef tree6 0 2; wmeta "$b" r6 deadbeef tree6 1 2
printf 'failing_test_one\nfailing_test_two\n' | mklog "$a" 0
printf 'All the tests have passed.\n' | mklog "$b" 1
finish "$a"; finish "$b"
expect_collect_ok "$T/ev.txt" "$a" "$b"
grep -q "tests-failed: yes (2 names across shards)" "$T/ev.txt" || fail "failures not reported as failures"
grep -q "failing_test_one" "$T/ev.txt" && grep -q "failing_test_two" "$T/ev.txt" || fail "names dropped"
grep -q "baseline-admission-decision: PENDING" "$T/ev.txt" || fail "collector claimed an admission decision"
grep -qi "suite all green\|all tests passed across shards" "$T/ev.txt" && fail "collector manufactured an all-green summary"
ok "failing suite reported as failing, decision left to INT"
