# Hypergraph visualiser — passive observation of a running Machine

The visualiser shows a Machine hypergraph while the Machine is working, records
what it saw, and replays the recording afterwards. It is a **reader**. It never
starts a Machine, never calls a Machine operation, and cannot modify Machine
state: the only things it opens are a journal file the Machine wrote and the
session files it records itself.

```
Machine script  ──writes──▶  visualiser/run/observed.jsonl  ──reads──▶  server  ──SSE──▶  browser
     (opt-in tap)                                                         │
                                                     recorder ──▶ visualiser/sessions/*.json ──▶ replay
```

## Why the tap lives in the Machine process

The Machine has no event bus, so an outside process can only poll a snapshot.
Polling `snapshots/*.json` from the viewer would mean reloading a 28 MB codec
dump to notice one new vertex, and it would still be a *copy* of the state, not
the state. The available read-only interface is the graph object itself, and
that object only exists inside the process that is running.

So the observed script opts in, with one call, and a daemon thread inside that
process polls the graph roots and appends what changed:

```python
from cat_theo_machine.visualiser.tap import observe
observe(runtime)            # or observe(runtime.graph, journal_path=...)
```

The tap reads `Head`/`Tail`/`IsPair`/`PrettyTerm` and the graph's own roots. It
does not patch a kernel method, does not hold a lock the Machine needs, and
never calls an edge that mutates state. Remove the `observe(...)` line and the
script behaves identically. That is the passive-observer property, and it is
tested: `validation/test48_hypergraph_visualiser.py` asserts that the viewer
server imports no kernel module at all.

## Run it: two terminals, two processes

The visualiser and the Machine are separate processes started separately. The
viewer never launches the script, and the script runs exactly as it would if the
viewer were not there.

**Terminal 1 — the viewer.** Start it first; it is a plain HTTP server that reads
files.

```bash
cd /home/user/cat_theo_machine
PYTHONPATH=/home/user python -m cat_theo_machine.visualiser.server --port 8801
```

It prints the journal path and session directory it is following and then waits.
Leave it running.

**Terminal 2 — a Machine script, started by you.**

```bash
cd /home/user/cat_theo_machine
PYTHONPATH=/home/user python -m cat_theo_machine.visualiser.examples.machine_workload \
    --delay 0.6 --rounds 6 --packs
```

`--packs` loads two knowledge packs before the graph work, which is what puts 25
rules on screen; `--delay` is the pause between steps, so the growth is visible.
Its output looks like:

```
[workload] observing to /home/user/cat_theo_machine/visualiser/run/observed.jsonl
[workload] loaded pack order-sign.pack.yaml
[workload] declared four vertices
[workload] added a ternary hyperedge Between(point_a, midpoint_m, point_b)
...
```

**Browser.** Open <http://127.0.0.1:8801/>. The badge reads `live`, the legend
counts what is drawn, and the graph grows one event at a time while the script
runs. When the script exits the badge goes `offline` and the graph stays.

Run the viewer from `/home/user` (as above), not from inside the package
directory: the repository root has a `hyge.py` stub that shadows the package
alias.

### Watching the interactive live machine

`main.py live` is a text REPL, not the viewer. It journals nothing by default;
`--observe` adds the same read-only tap `observe()` installs, in the same
process, and the viewer in terminal 1 follows it:

```bash
cd /home/user
PYTHONPATH=/home/user python cat_theo_machine/main.py live \
    --live-snapshot /tmp/live-check.json --observe
```

`--live-snapshot` is not needed for the flag; it is there because the default
snapshot in this repository carries live-proof bundles and is expensive to read
(see the last known limitation). Pointing it at a fresh path gives the graph
below, and the file is written on `quit` like any other live session.

```
[machine] Starting a fresh live graph; no compatible named-law snapshot was restored.
[machine] Observing to /home/user/cat_theo_machine/visualiser/run/observed.jsonl
you> load pack arithmetic
[machine] loaded pack arithmetic (12 rules); the tutor now reads it too
you> quit
[machine] goodbye
```

Everything typed at `you>` behaves exactly as it does without the flag: same
output, same snapshot on exit, no extra prompt, no HTTP port, and the viewer is
never consulted. `--observe` only appends to the journal, and on `quit` the
journal closes with `session.stop` (`reason: process exited`), so the badge goes
`offline` and the graph stays on screen for replay.

A pack loaded this way lands in the graph's own rule order rather than the
runtime's compiled list, and the digest reads the graph order when the compiled
list is empty, so the 12 arithmetic rules appear as edges while the session runs.

`--observe-journal PATH` writes somewhere other than
`visualiser/run/observed.jsonl` — useful for keeping one journal per session.
Point the viewer at it with `--journal PATH`.

Without `--observe`, live mode writes no journal at all (measured: the file is
not created), so the viewer shows whatever its own journal last held.

### Connecting the tap to your own script

Any script that holds a runtime or a hypergraph can be observed. Add the import
and one call near the top, before the work that builds the graph:

```python
from cat_theo_machine.runtime import make_fresh_runtime
from cat_theo_machine.visualiser.tap import observe

runtime = make_fresh_runtime()
observe(runtime, interval=0.2)        # or observe(runtime.graph) for a bare graph
```

That is the entire integration. It starts a daemon thread inside your process
that polls the graph roots and appends deltas to
`visualiser/run/observed.jsonl`, the file the viewer is already following. Then
run your script as usual in terminal 2:

```bash
PYTHONPATH=/home/user python my_script.py
```

Use a different journal when you do not want the default one to be reused:

```bash
PYTHONPATH=/home/user python -m cat_theo_machine.visualiser.server --port 8801 --journal /tmp/my-run.jsonl
```

```python
observe(runtime, journal_path="/tmp/my-run.jsonl", interval=0.15)
```

The journal is truncated when a new run starts; the server notices and begins a
new session instead of appending, so a restart is never mistaken for growth.
`observe` returns the tap; call `tap.stop()` if your script should stop being
observed before it exits (a normal exit does this automatically).

### Inspecting one transformation

Rules are drawn by default: violet diamonds whose incoming links are premises and
whose outgoing link is the replacement. To look at one closely:

1. Click it. The **Details** tab shows the full premise → replacement text, its
   arity, the provenance of the rule store, and the first event sequence number
   at which it appeared.
2. Press **Focus in graph** in the panel (or search for part of its text and
   press `Enter`). The view zooms to 1.6× on it.
3. At that scale the argument-position numbers on each link are visible, so a
   ternary hyperedge reads `1`, `2`, `3` on its three argument links.

`F` fits the whole graph, `R` resets the layout, the wheel zooms, dragging pans,
and the search box filters by id, label, relation, kind and constructor.

## Recording and replay

With the viewer in terminal 1 and your script in terminal 2 (previous section):

1. In the browser, press **● Record**. The recorder copies the live stream into
   memory and opens the recording with a **checkpoint**: the state that existed
   at that moment, so the file replays on its own. From a shell:
   `curl -s -X POST http://127.0.0.1:8801/api/recording/start -d '{"name":"my-run"}'`.
2. Let the script run. Press **■ Stop** (`POST /api/recording/stop`). The
   recording is written to `visualiser/sessions/my-run-<timestamp>.json`.
3. Stop the Machine script — close terminal 2, or let it finish. Nothing of the
   Machine is needed from here on.
4. Open the **Recordings** tab and press **Replay**. `loadSession` fetches the
   JSON and the browser rebuilds the states itself; `GET /api/sessions/<id>`
   returns the same file, so it can be inspected or re-served by anything.

Replay controls: play/pause, step forward and back, a seek slider over the event
sequence, and 0.25×–8× speed. Times shown are the recorded timestamps, and the
timeline is the ordered event sequence, not a redraw count. Playback happens in
the browser from the file; the server is only asked for the file. Journal and
session bytes are compared before and after replay in the test suite, and no
Machine process is alive at that point.

`GET /api/sessions/<id>` returns the whole recording, so a session file can be
inspected or re-served by anything. **Export state JSON** downloads the current
state (`hypergraph-state.json`: nodes, edges with their argument order, counts,
mode and source); **Export view SVG** downloads the canvas as a standalone
`hypergraph-view.svg` with the stylesheet inlined. Both are exercised in the DOM
checks.

## The event vocabulary

Every line of a journal (and every element of a session's `events`) is one
object. `seq` is monotonic within a run, `t` is a wall-clock timestamp.

| type | payload | meaning |
| --- | --- | --- |
| `session.start` | `machine`, `source` | process identity: pid, argv, cwd, python |
| `nodes.added` | `items[]` | vertices and argument terms that appeared |
| `edges.added` | `items[]` | hyperedges and rules that appeared |
| `items.removed` | `nodes[]`, `edges[]` | what disappeared (graph surgery) |
| `counts` | `counts` | heartbeat of root sizes |
| `journal.rotated` | — | the journal was truncated by a new Machine run |
| `session.stop` | `reason` | the observed process finished |

A vertex item is `{id, kind, label, term, constructor, declared, source}`. A
hyperedge item is `{id, kind, label, relation, arity, arguments[], results[],
source}` where `arguments` holds one id per argument **in position order**.

### Hyperedge semantics are not flattened

A graph hyperedge is `Pair(relation, args)`. The viewer draws it as its own node
(amber diamond) with one incidence link per argument, numbered by position: a
ternary edge has three links, a nullary edge has none. Nothing is turned into
pairwise edges. `Between(point_a, midpoint_m, point_b)` keeps three distinct
argument ids, and the test suite asserts exactly that, including for a recorded
file.

Rules appear as violet diamonds with their premises as incoming links and their
replacement as an outgoing link, capped by `rule_cap` (default 40 for the tap).

## Colours

| shape | colour | kind |
| --- | --- | --- |
| circle | teal `#2dd4bf` | declared node (`Hypergraph.add_node`) |
| small circle | slate `#94a3b8` | term that only appears as an edge argument, e.g. a machine-computed natural |
| diamond | amber `#f59e0b` | hyperedge (n-ary) |
| diamond | violet `#a78bfa` | rule, premises → result |
| dashed link | grey | argument incidence carried by an edge node, numbered 1,2,3… |

The same legend is drawn in the corner of the canvas and counts what is on
screen: nodes, terms, hyperedges, rules, an arity histogram for hyperedges and,
when rules are present, a separate premise count. Rule arity is not mixed into
the hyperedge histogram, because a rule's incoming links are its premises.

## Controls

Wheel zooms, drag pans, click inspects. `F` fits, `R` resets, `+`/`-` zoom,
space plays or pauses a replay, arrow keys step. The **Details** tab shows the
selected element's id, kind, label, term, constructor, provenance (which root it
came from, whether it is a declared vertex, when it first appeared), its
arguments in order, and the hyperedges incident on a vertex. The search box
filters by id, label, relation, kind and constructor; `Enter` selects the first
hit. All four kinds are shown by default; the kind checkboxes drop whole classes
from the view. Labels are sized against the zoom, so they stay about 11 px on
screen instead of growing into blobs, and terms appear once the view is close
enough for their labels to be readable.

## What this replaced

`inspector/` (served by `python main.py inspect`) is the previous viewer, and it
still works — it is untouched. What it does, and why it is not enough:

* It boots its **own** runtime from packs or a snapshot, so it shows a copy of
  the Machine, not the Machine you are running.
* `MachineRuntime.cytoscape_view` calls `M.EdgeInputs(edge)` on every graph edge.
  A canonical hyperedge is a `Pair`, which has no `.inputs`, so the graph pane
  raises `AttributeError: 'Pair' object has no attribute 'inputs'` as soon as the
  graph contains a hyperedge. In practice only rule edges ever render.
* Every refresh calls `cy.destroy()` and rebuilds the whole graph, so the layout
  jumps and nothing is incremental.
* It loads Cytoscape from `unpkg.com`, which fails on a machine without internet.
* There is no recording, no timeline and no replay.

Salvaged: the idea of drawing a hyperedge as a node with labelled incidence
links, the `kind` vocabulary, and `PrettyTerm`/`PrettyRule` rendering. Replaced:
the runtime ownership, the full-redraw loop, the CDN dependency, and the
cytoscape call that cannot read a `Pair`. New: incremental deltas, journal
observation, recording, timeline replay, filtering, export.

## Files

```
visualiser/
  protocol.py      wire constants; shared by both sides, imports nothing
  events.py        machine graph → JSON events (runs inside the Machine process)
  tap.py           the observer thread (runs inside the Machine process)
  state.py         rebuild observed state from events (server side)
  sessions.py      recording store
  server.py        stdlib HTTP + SSE server; imports no kernel module
  examples/machine_workload.py   a Machine script you run yourself
  tests/model_check.js           model checks, plain node, no dependencies
  tests/dom_check.js             DOM checks, needs jsdom (optional)
  web/             index.html, app.js, model.js, style.css, vendor/d3.min.js
  run/             journals (gitignored)
  sessions/        recordings (gitignored)
```

`web/model.js` is loaded both by the browser and by the node tests, so the
replay logic that ships is the logic that is checked.

## How these screenshots were made

The sandbox has no runnable browser. Chromium, Chrome and Firefox are absent from
the image; a Chromium binary was obtained from an npm package
(`@sparticuz/chromium`, 209 MB, Chromium 153) and it starts far enough to print
`--version`, but every page load dies with SIGSEGV (exit 139) after the stub NSS
shift, so no page was rendered in it. That is why there is no browser screenshot
in this repository.

What the images in `verification/visualiser-round2/` are instead:

* the page is driven in jsdom — the real `app.js`, `model.js`, stylesheet and the
  real data from the server;
* the app's **own** `Export view SVG` produces the file (the same button a user
  clicks, including the inlined stylesheet);
* `@resvg/resvg-js` rasterises that SVG to PNG.

So the geometry, colours, shapes, label positions and link layout in the PNGs are
the page's own output, and the SVG beside each PNG can be opened in a browser to
check. What is **not** in them is HTML chrome — sidebar, toolbar, legend box,
timeline — because jsdom has no layout engine. Those are covered by text and
geometry assertions in `tests/dom_check.js` (56 checks) and by
`capture.json`, which records the mode badge, legend counts and timeline text at
each capture.

To reproduce:

```bash
# terminal 1: viewer
PYTHONPATH=/home/user python -m cat_theo_machine.visualiser.server --port 8801
# terminal 2: a real Machine run, recorded
curl -s -X POST http://127.0.0.1:8801/api/recording/start -d '{"name":"round2-residency"}'
PYTHONPATH=/home/user python -m cat_theo_machine.visualiser.examples.machine_workload --delay 0.5 --rounds 6 --packs
curl -s -X POST http://127.0.0.1:8801/api/recording/stop

# capture + rasterise
npm install --prefix /tmp/visdom jsdom
npm install --prefix /tmp/resvg @resvg/resvg-js
NODE_PATH=/tmp/visdom/node_modules VIS_BASE=http://127.0.0.1:8801 \
  node visualiser/tests/pixel_capture.js --out verification/visualiser-round2 \
  --session round2-residency-20261103-143947
NODE_PATH=/tmp/resvg/node_modules node visualiser/tests/rasterize.js \
  verification/visualiser-round2 1440
```

## Tests

```bash
PYTHONPATH=/home/user python -u validation/test48_hypergraph_visualiser.py
```

Runs the module-boundary check, the model checks, a genuine Machine process
observed live over SSE, a recording, a replay, and a non-mutation comparison of
journal and session bytes. The DOM section runs when `jsdom` is resolvable and
reports `SKIPPED` with the exact reproduce command otherwise:

```bash
npm install --prefix /tmp/visdom jsdom
NODE_PATH=/tmp/visdom/node_modules \
  PYTHONPATH=/home/user python -u validation/test48_hypergraph_visualiser.py
```

`validation/test49_visualiser_churn.py` covers observation identity and churn on
a real runtime and real packs: two polls of an unchanged graph, the round-1
"premises vanish on the second read" defect, pack growth adding without removing,
a genuine disappearance still being reported, and one graph edit producing
exactly one event.

```bash
PYTHONPATH=/home/user python -u validation/test49_visualiser_churn.py
```

D3 7.9.1 is vendored at `web/vendor/d3.min.js` (ISC, see
`web/vendor/LICENSE.d3`), so the viewer works without a network.

## Known limitations

* **Rendering is verified structurally, not pixel by pixel.** The DOM checks run
  in jsdom, which has no SVG geometry: element kinds, counts, labels, selection,
  filtering, zoom transforms, label sizing and the whole replay path are checked,
  but the visual layout itself is not.
* **The round-1 "term churn while packs load" report was a colouring defect, not
  a machine one.** Rule premise terms were handed back only on the first read of
  a rule, so the second poll lost every premise term and the third brought it
  back — a burst of `items.removed` for a graph nobody touched. Fixed and pinned
  by `validation/test49_visualiser_churn.py`; loading all 17 packs now produces
  zero removals. Genuine surgery is still reported: `items.removed` fires for an
  id that really disappears.
* **Two clients, one journal.** The journal is a single append-only file per run;
  two servers following the same file is fine (both only read), two Machine
  processes writing the same file is not, and the second truncates the first.
* **Derivations and search history are counted, not itemised.** They are trees,
  not carrier vertices; the viewer reports their root sizes in the counts stream
  and in the Details/Status panels.
* **Screenshots are the page's SVG, not a browser screenshot.** See "How these
  screenshots were made": no browser here can execute a page, so the HTML chrome
  is verified by assertions rather than by pixels.
* **Label placement is greedy, not optimal.** Names are placed in priority order
  (selection, vertices, hyperedges, rules, terms) with three candidate positions,
  and a name is dropped rather than overlapped. About 85% of names are placed at
  a fitted 100-element graph; the rest appear as soon as the view is zoomed or
  filtered.
* **A graph carrying live-proof bundles is too heavy to digest.** Every node is
  rendered with `PrettyTerm` to give it a stable text id, and one
  `live-proof-outcome`/`observed-structure-bundle` node of a 6.2 MB restored
  snapshot takes 19-20 s to render, and a full poll of that graph does not
  finish in five minutes. Measured: the same snapshot boots and quits in 30 s
  without the flag; with it, the journal held only `session.start` 240 s in and
  the process had to be killed after a `quit` that was not honoured. Use
  `--live-snapshot` at a fresh path, or a small snapshot, for interactive
  observation. Ordinary sessions (packs, facts, rules, goals) poll in
  milliseconds. A cost-aware label budget is not implemented; it needs care,
  because ids are derived from the rendered text and must stay stable.
* **No production caller.** `HypergraphIsomorphismMatch` and the search stack do
  not write to `graph.nodes`/`graph.edges`; the hypergraph content is whatever
  the script puts there. The viewer is faithful to that, not to a "run" that the
  Machine would define on its own.
