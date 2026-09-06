#!/usr/bin/env bash
# SYNTHETIC case 5: a completed attempt's marker+completion copied onto a
# NEW truncated rerun -> collection refuses (no stitching of attempts).
source "$(dirname "$0")/fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
old="$T/old/shard-0"; new="$T/new/shard-0"; other="$T/old/shard-1"
mkdir -p "$old" "$new" "$other"
wmeta "$old" rA deadbeef treeA 0 2; wmeta "$new" rB deadbeef treeA 0 2; wmeta "$other" rA deadbeef treeA 1 2
printf 'All the tests have passed.\n' | mklog "$old" 0; finish "$old"
printf 'All the tests have passed.\n' | mklog "$other" 1; finish "$other"
# new attempt: rerun cut off mid-output (marker only, no report), old
# completion+digest files copied on top — a naive reader would accept it
{ echo "Reading pack order-sign..."; echo "SHARD 0 elapsed 9.99"; } > "$new/raw.log"
cp "$old/completion.json" "$new/completion.json"
cp "$old/completion.json.sha" "$new/completion.json.sha"
expect_collect_refuse "E_DIGEST_MISMATCH|E_REPORT_TRUNCATED" "$new" "$other"
ok "stale marker over truncated rerun refused"
