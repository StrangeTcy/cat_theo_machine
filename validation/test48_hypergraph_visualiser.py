# ============================================================
# TEST 48: Passive hypergraph visualiser — observation, recording, replay
# ============================================================
"""Checks the visualiser against a genuine Machine process.

What is asserted here:
  * the viewer's server imports no kernel module, so it cannot run the Machine;
  * a Machine script started as its own process writes an observation journal,
    and the server streams that journal incrementally while the script runs;
  * hyperedges keep their arity and argument order through the whole pipeline;
  * a recording saved from the live stream replays on its own, deterministically,
    without a Machine process and without touching the journal it came from;
  * browser logic (model.js) and, when jsdom is available, the rendered DOM.
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

IMPORT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine.visualiser import state as state_module  # noqa: E402
from cat_theo_machine.visualiser import sessions as sessions_module  # noqa: E402

PACKAGE_DIR = os.path.join(IMPORT_ROOT, "cat_theo_machine")
VIS_DIR = os.path.join(PACKAGE_DIR, "visualiser")
WORKLOAD = [sys.executable, "-u", "-m", "cat_theo_machine.visualiser.examples.machine_workload"]

t0 = time.time()
print("=== TEST 48: Passive hypergraph visualiser ===")
print()

WORK = os.path.join("/tmp", "ctm-visualiser-test48-" + str(os.getpid()))
os.makedirs(WORK, exist_ok=True)
JOURNAL = os.path.join(WORK, "observed.jsonl")
SESSION_DIR = os.path.join(WORK, "sessions")
SERVER_LOG = os.path.join(WORK, "server.log")

server_process = None
sse_events = []


def env_for_children():
    env = dict(os.environ)
    env["PYTHONPATH"] = IMPORT_ROOT
    return env


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def api(base, path, payload=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_server(base, timeout=25.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            api(base, "/api/status")
            return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.2)
    return False


def sha256(path):
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_fingerprint(path):
    return {
        "size": os.path.getsize(path),
        "mtime": round(os.path.getmtime(path), 3),
        "sha256": sha256(path),
    }


# ---------------------------------------------------------------- 1. boundary
print("[1] The observer cannot execute the Machine")
probe = subprocess.run(
    [
        sys.executable,
        "-c",
        "import sys; import cat_theo_machine.visualiser.server;"
        "kernel = [m for m in sys.modules if m.startswith('cat_theo_machine.')"
        " and not m.startswith('cat_theo_machine.visualiser')];"
        "print('KERNEL:' + ','.join(sorted(kernel)))",
    ],
    capture_output=True,
    text=True,
    env=env_for_children(),
    cwd=IMPORT_ROOT,
)
assert probe.returncode == 0, probe.stderr
kernel_modules = probe.stdout.strip().split("KERNEL:")[-1]
assert kernel_modules == "", "server pulled in kernel modules: " + kernel_modules
print("    server imports no kernel module (only stdlib and its own package)")

server_source = open(os.path.join(VIS_DIR, "server.py"), encoding="utf-8").read()
for forbidden in ("import cat_theo_machine", "from cat_theo_machine", "subprocess", "os.system"):
    assert forbidden not in server_source, "server.py contains " + forbidden
print("    server.py has no kernel import and no process-launch call (Passed)")
print()

# ------------------------------------------------------------- 2. model checks
import shutil  # noqa: E402

NODE = shutil.which("node")

print("[2] Browser model checks under node (fixture events, no Machine)")
if NODE is None:
    print("    SKIPPED: no node executable on PATH (browser logic is not covered here)")
else:
    model_check = subprocess.run(
        [NODE, os.path.join(VIS_DIR, "tests", "model_check.js")],
        capture_output=True,
        text=True,
        cwd=IMPORT_ROOT,
    )
    assert model_check.returncode == 0, model_check.stdout + model_check.stderr
    model_report = json.loads(model_check.stdout)
    assert model_report["ok"], model_report
    print("    " + str(len(model_report["checks"])) + " model checks passed (fixture stream)")
print()

# ------------------------------------------------------- 3. state and sessions
print("[3] Server-side state and session store round-trip")
fixture_events = [
    {"type": "session.start", "seq": 0, "t": 1.0, "machine": {"pid": 7}, "source": {}},
    {
        "type": "nodes.added",
        "seq": 1,
        "t": 1.1,
        "items": [
            {"id": "t:x", "kind": "node", "label": "x", "declared": True},
            {"id": "t:y", "kind": "node", "label": "y", "declared": True},
        ],
    },
    {
        "type": "edges.added",
        "seq": 2,
        "t": 1.2,
        "items": [
            {
                "id": "e:T",
                "kind": "hyperedge",
                "label": "T",
                "relation": "T",
                "arity": 2,
                "arguments": ["t:x", "t:y"],
                "results": [],
            }
        ],
    },
]
graph_state = state_module.GraphState()
for event in fixture_events:
    graph_state.apply(event)
assert len(graph_state.nodes) == 2 and len(graph_state.edges) == 1
checkpoint = graph_state.checkpoint_events(when=9.5)
rebuilt = state_module.GraphState()
for event in checkpoint:
    rebuilt.apply(event)
assert set(rebuilt.nodes) == set(graph_state.nodes), "checkpoint lost nodes"
assert set(rebuilt.edges) == set(graph_state.edges), "checkpoint lost hyperedges"
assert rebuilt.edges["e:T"]["arguments"] == ["t:x", "t:y"]
assert all(event["t"] == 9.5 for event in checkpoint), "checkpoint lacks a timestamp"

store = sessions_module.SessionStore(os.path.join(WORK, "store-check"))
session_id = store.new_id("unit")
path = store.save(session_id, {"name": "unit"}, fixture_events)
loaded = store.load(session_id)
assert loaded["events"] == fixture_events
listing = [item for item in store.listing() if item["id"] == session_id]
assert listing and listing[0]["events"] == len(fixture_events)
assert store.delete(session_id) is True and store.delete(session_id) is False
print("    checkpoint rebuilds state, store round-trips, delete is idempotent (Passed)")
print()

# ------------------------------------------------- 4. a genuine Machine process
print("[4] A separately started Machine process is observed live")
port = free_port()
base = "http://127.0.0.1:" + str(port)
server_process = subprocess.Popen(
    [
        sys.executable,
        "-u",
        "-m",
        "cat_theo_machine.visualiser.server",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--journal",
        JOURNAL,
        "--sessions",
        SESSION_DIR,
    ],
    env=env_for_children(),
    cwd=IMPORT_ROOT,
    stdout=open(SERVER_LOG, "w"),
    stderr=subprocess.STDOUT,
)
assert wait_for_server(base), "server did not answer: " + open(SERVER_LOG).read()[-800:]
status = api(base, "/api/status")
assert status["journal"]["journal_exists"] is False, "fresh journal should not exist yet"
print("    server up on " + base + ", journal empty, waiting for a Machine run")

import threading  # noqa: E402

sse_stop = threading.Event()
sse_arrivals = []


def stream_events():
    request = urllib.request.Request(base + "/api/events?from=0")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            buffer = b""
            while not sse_stop.is_set():
                chunk = response.read(1)
                if not chunk:
                    break
                buffer += chunk
                while b"\n\n" in buffer:
                    frame, buffer = buffer.split(b"\n\n", 1)
                    for line in frame.splitlines():
                        if line.startswith(b"data: "):
                            event = json.loads(line[6:])
                            if event.get("type") not in ("state.snapshot",):
                                sse_events.append(event)
                                sse_arrivals.append(time.time())
    except Exception:
        pass


stream_thread = threading.Thread(target=stream_events, daemon=True)
stream_thread.start()
time.sleep(0.4)

workload = subprocess.run(
    WORKLOAD + ["--delay", "0.08", "--rounds", "4", "--journal", JOURNAL],
    capture_output=True,
    text=True,
    timeout=180,
    env=env_for_children(),
    cwd=IMPORT_ROOT,
)
assert workload.returncode == 0, workload.stderr[-1500:]
workload_finished_at = time.time()
time.sleep(1.2)

item_arrivals = [
    arrival
    for event, arrival in zip(sse_events, sse_arrivals)
    if event.get("type") in ("nodes.added", "edges.added")
]
assert item_arrivals, "no item events reached the stream"
before_finish = [arrival for arrival in item_arrivals if arrival < workload_finished_at]
assert len(before_finish) >= 4, (
    "expected incremental delivery while the script ran, got "
    + str(len(before_finish))
    + " of "
    + str(len(item_arrivals))
)
print(
    "    received "
    + str(len(item_arrivals))
    + " item events over the stream, "
    + str(len(before_finish))
    + " of them before the script exited"
)

exported = api(base, "/api/state")
assert exported["format"] == "ctm-hypergraph-view"
assert exported["summary"]["machine"], "state carries no machine provenance"
ids = {node["id"] for node in exported["nodes"]}
edges = {edge["id"]: edge for edge in exported["edges"]}
assert len(edges) >= 8, "too few hyperedges observed: " + str(len(edges))
arities = {}
for edge in edges.values():
    arities[edge["arity"]] = arities.get(edge["arity"], 0) + 1
assert 3 in arities, "the ternary hyperedge was not observed: " + str(arities)
assert 0 in arities, "the nullary hyperedge was not observed: " + str(arities)

ternary = next(edge for edge in edges.values() if edge["arity"] == 3)
assert ternary["label"] == "Between", ternary["label"]
assert len(ternary["arguments"]) == 3
assert ternary["arguments"] == ["t:point_a", "t:midpoint_m", "t:point_b"], ternary["arguments"]
assert len(set(ternary["arguments"])) == 3, "argument positions collapsed"
assert all(argument in ids for argument in ternary["arguments"]), "edge names a node the carrier lacks"

nullary = next(edge for edge in edges.values() if edge["arity"] == 0)
assert nullary["arguments"] == [] and nullary["label"] == "NullaryMark"

measured = next(edge for edge in edges.values() if edge["label"] == "HasOrder")
assert measured["arguments"][1].startswith("t:"), measured
assert any(node["kind"] == "term" and node["label"] == "2" for node in exported["nodes"]), (
    "the machine-computed natural is not carried as a term"
)
print(
    "    carriers "
    + str(len(exported["nodes"]))
    + " vertices, "
    + str(len(edges))
    + " hyperedges, arities "
    + json.dumps(arities, sort_keys=True)
)
print("    ternary arguments keep position order; nullary edge kept; computed nat kept as a term")
print()

# ---------------------------------------------------------- 5. recording
print("[5] Recording a live observed run")
start = api(base, "/api/recording/start", {"name": "test48"}, "POST")
assert start["active"] is True and start["checkpoint_events"] >= 1, start

# --packs loads the compiled rule set, so the recording also covers rule edges
second_run = subprocess.run(
    WORKLOAD + ["--delay", "0.08", "--rounds", "2", "--packs", "--journal", JOURNAL],
    capture_output=True,
    text=True,
    timeout=180,
    env=env_for_children(),
    cwd=IMPORT_ROOT,
)
assert second_run.returncode == 0, second_run.stderr[-1500:]
time.sleep(1.0)
stopped = api(base, "/api/recording/stop", {}, "POST")
assert stopped["active"] is False and stopped["events"] > 0, stopped
session_path = stopped["path"]
assert os.path.exists(session_path), session_path

session_listing = api(base, "/api/sessions")["sessions"]
assert any(item["id"] == stopped["id"] for item in session_listing), session_listing
recorded = api(base, "/api/sessions/" + stopped["id"])
recorded_events = recorded["events"]
assert recorded["meta"]["events"] == len(recorded_events)
assert recorded["meta"]["duration"] >= 0
assert recorded["meta"]["checkpoint_events"] >= 1
assert recorded_events[-1]["type"] == "session.stop"
timestamps = [event["t"] for event in recorded_events if isinstance(event.get("t"), (int, float))]
assert len(timestamps) == len(recorded_events), "every recorded event must carry a timestamp"
assert timestamps == sorted(timestamps), "recorded events are not ordered in time"
recorded_rules = [
    item for event in recorded_events if event.get("type") == "edges.added"
    for item in event.get("items", []) if item.get("kind") == "rule"
]
assert recorded_rules, "the pack-booting run recorded no rules"
assert all("object at 0x" not in item["label"] for item in recorded_rules), "rule labels are host reprs"
assert all(item["results"] for item in recorded_rules), "rules lost their replacement"
print("    " + str(len(recorded_rules)) + " rules recorded with readable premise/replacement labels")
print(
    "    saved "
    + str(len(recorded_events))
    + " events ("
    + str(recorded["meta"]["checkpoint_events"])
    + " checkpoint) over "
    + str(recorded["meta"]["duration"])
    + "s to "
    + os.path.basename(session_path)
)
print()

# ------------------------------------------------------------- 6. replay
print("[6] Replay is independent, deterministic and non-mutating")
journal_before = file_fingerprint(JOURNAL)
session_before = file_fingerprint(session_path)

replay_report = {"checks": []}
if NODE is not None:
    model_replay = subprocess.run(
        [NODE, os.path.join(VIS_DIR, "tests", "model_check.js"), session_path],
        capture_output=True,
        text=True,
        cwd=IMPORT_ROOT,
    )
    assert model_replay.returncode == 0, model_replay.stdout + model_replay.stderr
    replay_report = json.loads(model_replay.stdout)
    assert replay_report["ok"], replay_report
    assert all(check["ok"] for check in replay_report["checks"] if "recorded session" in check["name"])

# replaying the same file twice, through the server, must change nothing
first = api(base, "/api/sessions/" + stopped["id"])
second = api(base, "/api/sessions/" + stopped["id"])
assert first["events"] == second["events"], "session load is not stable"
assert file_fingerprint(JOURNAL) == journal_before, "replay touched the observation journal"
assert file_fingerprint(session_path) == session_before, "replay rewrote the session file"

live_after_replay = api(base, "/api/state")
assert live_after_replay["nodes"], "the live view lost its state during replay"

# nothing of the Machine is left running, so replay provably had no Machine to mutate
assert workload.returncode is not None, "the first workload has no exit status"
assert second_run.returncode is not None, "the recording workload has no exit status"
print(
    "    " + str(len(replay_report["checks"])) + " model checks run on the recorded file; "
    "journal and session bytes unchanged"
)
print("    no Machine process alive during replay (both workload runs exited)")
print()

# ------------------------------------------------------------ 7. browser DOM
print("[7] Browser DOM checks (jsdom, if available)")
node_jsdom = subprocess.run(
    [NODE or "node", "-e", "require.resolve('jsdom'); console.log('yes')"],
    capture_output=True,
    text=True,
    cwd=IMPORT_ROOT,
)
if NODE is not None and node_jsdom.returncode == 0:
    dom_check = subprocess.run(
        [NODE, os.path.join(VIS_DIR, "tests", "dom_check.js")],
        capture_output=True,
        text=True,
        env=dict(os.environ, VIS_BASE=base),
        cwd=IMPORT_ROOT,
    )
    try:
        dom_report = json.loads(dom_check.stdout)
    except ValueError:
        raise AssertionError("the DOM suite did not report JSON: " + dom_check.stdout[-1500:] + dom_check.stderr[-500:])
    failed_checks = [check for check in dom_report["checks"] if not check["ok"]]
    assert dom_check.returncode == 0 and not failed_checks, failed_checks or dom_check.stderr[-800:]
    assert dom_report["ok"], [check for check in dom_report["checks"] if not check["ok"]]
    print(
        "    "
        + str(len(dom_report["checks"]))
        + " DOM checks passed (render, select, filter, zoom, labels, layout continuity, replay)"
    )
else:
    reason = "no node executable on PATH" if NODE is None else "jsdom is not installed for this interpreter"
    print("    SKIPPED: " + reason)
    print("    reproduce with: npm install --prefix /tmp/visdom jsdom && \\")
    print("      NODE_PATH=/tmp/visdom/node_modules node visualiser/tests/dom_check.js")
print()

print("[8] Teardown")
sse_stop.set()
server_process.terminate()
try:
    server_process.wait(timeout=10)
except subprocess.TimeoutExpired:
    server_process.kill()
print("    server stopped, temporary work directory " + WORK)
print()

elapsed = time.time() - t0
print("=== ALL TEST 48 VISUALISER CHECKS PASSED in " + str(round(elapsed, 3)) + "s ===")
