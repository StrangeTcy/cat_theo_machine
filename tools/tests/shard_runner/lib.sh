# Shared by the shard-runner tests. Sourced, never executed directly.
# Expects TEST_TMP (a private temp dir) to exist; provides fail/polling
# helpers and per-test isolation of the attempt root.

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

# wait_file <path> <timeout-seconds>: true once the path exists.
wait_file() {
    _WANT=$1
    _LEFT=$2
    while [ ! -e "$_WANT" ]; do
        if [ "$_LEFT" -le 0 ]; then
            return 1
        fi
        sleep 1
        _LEFT=$((_LEFT - 1))
    done
    return 0
}

# wait_status <runner> <attempt> <shard> <want-state> <timeout>: true once
# the status line for that shard shows the wanted state word.
wait_status() {
    _RUNNER=$1
    _ATTEMPT=$2
    _SHARD=$3
    _WANT=$4
    _LEFT=$5
    while [ "$_LEFT" -gt 0 ]; do
        if sh "$_RUNNER" --status "$_ATTEMPT" 2>/dev/null \
            | grep -q "^shard $_SHARD: $_WANT"; then
            return 0
        fi
        sleep 1
        _LEFT=$((_LEFT - 1))
    done
    return 1
}

status_line() {
    sh "$RUNNER" --status "$1" 2>/dev/null | grep "^shard $2: " || true
}

attempt_dir_of() {
    sh "$RUNNER" --status "$1" 2>/dev/null \
        | grep '^attempt-dir: ' | cut -d' ' -f2
}
