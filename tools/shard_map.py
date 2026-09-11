"""Print every default test's cursor index and shard, without booting.

    python3 tools/shard_map.py [git-ref] [--count N]

Static, because shard assignment *is* static: `TestShardAccept` ticks a
cursor at every registration site and admits a test when the cursor equals
the configured index, so a test's shard is a function of its position in
registration order and nothing else. Walking the source answers it in
milliseconds where installing the suite to ask it costs the better part of
an hour.

With a git ref it reads `testsuite.py` from that ref instead of the working
tree, which is the point:

    python3 tools/shard_map.py HEAD > /tmp/new.txt
    python3 tools/shard_map.py experiment-5-frozen > /tmp/old.txt
    diff /tmp/old.txt /tmp/new.txt      # empty == bit-identical assignment

Two shards reporting the same 147/3/2 is strong evidence that assignment
survived a change; this is the actual check, name by name, and it is what a
D9 fix needs before it can claim the assignment is unchanged.

The reader is the AST, not a regex over names: a name-based scan found 291
of 304 tests and put `learned_memory_checkpoint_test` at index 209 instead
of its pinned 218, because not every test name ends in `_test`. Guard ticks
and registrations are read as call nodes in source order, which is exactly
what the pin test does for its one name.
"""
import ast
import subprocess
import sys


def source_at(ref):
    if ref is None:
        with open("testsuite.py", "r", encoding="utf-8") as handle:
            return handle.read()
    return subprocess.run(
        ["git", "show", "%s:testsuite.py" % ref],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def shard_map(source, shard_count=2):
    tree = ast.parse(source)
    func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "install_default_tests":
            func = node
            break
    if func is None:
        raise SystemExit("install_default_tests not found")

    events = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Attribute) and target.attr == "TestShardAccept":
            events.append((node.lineno, 0, "guard", None))
        elif isinstance(target, ast.Name) and target.id == "_register_test":
            if len(node.args) < 2 or not isinstance(node.args[1], ast.Constant):
                raise SystemExit("registration with a non-literal name at line %d" % node.lineno)
            events.append((node.lineno, 1, "register", node.args[1].value))
    # Registrations sort after the guard on the same line, if that ever happens.
    events.sort(key=lambda event: (event[0], event[1]))

    rows = []
    cursor = 0
    for _lineno, _kind, kind, name in events:
        if kind == "guard":
            cursor += 1
        else:
            index = cursor - 1
            rows.append((index, index % shard_count, name))
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return 0
    count = 2
    if "--count" in sys.argv:
        count = int(sys.argv[sys.argv.index("--count") + 1])
    rows = shard_map(source_at(args[0] if args else None), count)
    for index, shard, name in rows:
        print("%3d  %d  %s" % (index, shard, name))
    print("# %d tests, %d guards, %d shards" % (len(rows), len(rows), count), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
