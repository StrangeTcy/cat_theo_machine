#!/usr/bin/env bash
# REAL-WRAPPER case 4: deliberately terminate a short dummy child mid-run;
# interrupted evidence must not become a baseline. Uses suite_attempt.sh
# itself, so the wrapper's atomic-publish behavior is under test.
source "$(dirname "$0")/fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
AD="$T/attempts"
cat > "$T/dummy.sh" <<'EOF'
#!/usr/bin/env bash
echo "Reading pack order-sign..."
sleep 30
EOF
chmod +x "$T/dummy.sh"

setsid env SUITE_ATTEMPTS_DIR="$AD" bash "$ATTEMPT" --tested-commit deadbeef --shard 0 --count 2 \
  -- "$T/dummy.sh" &
wpid=$!
sleep 1
pg="$(ps -o pgid= "$wpid" | tr -d ' ')"
kill -TERM -- "-$pg" 2>/dev/null || kill -TERM "$wpid" 2>/dev/null
# bounded wait: the kill must not hang the harness
for i in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$wpid" 2>/dev/null || break; sleep 0.2; done
kill -KILL "$wpid" 2>/dev/null; wait "$wpid" 2>/dev/null

d="$AD/$(ls "$AD" | head -1)/shard-0"
[ -d "$d" ] || fail "attempt dir missing"
[ -e "$d/raw.log" ] || fail "raw log missing: interrupted evidence was discarded"
[ -e "$d/completion.json" ] && fail "completion record written for an interrupted run"
grep -q "All the tests" "$d/raw.log" && fail "dummy produced a report after termination"

# same refusal for a shard-1 counterpart copied as a normal attempt
mkdir -p "$T/r3/shard-1"; wmeta "$T/r3/shard-1" r3 deadbeef tree3 1 2
printf 'All the tests have passed.\n' | mklog "$T/r3/shard-1" 1; finish "$T/r3/shard-1"
expect_collect_refuse "E_NO_COMPLETION" "$d" "$T/r3/shard-1"
ok "killed run leaves non-baseline evidence"
