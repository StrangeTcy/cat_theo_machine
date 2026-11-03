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

## Run it

Terminal 1 — the viewer (reads only):

```bash
cd /home/user/cat_theo_machine
PYTHONPATH=/home/user python -m cat_theo_machine.visualiser.server --port 8801
```

Terminal 2 — a Machine script, started by you:

```bash
cd /home/user/cat_theo_machine
PYTHONPATH=/home/user python -m cat_theo_machine.visualiser.examples.machine_workload --delay 0.6
```

Open <http://127.0.0.1:8801/>. The graph grows while the script runs, one
`nodes.added`/`edges.added` event at a time.

To observe **your own** script, add the two lines from the previous section and
point the tap at the journal the server follows:

```bash
python -m cat_theo_machine.visualiser.server --journal /tmp/my-run.jsonl
```

```python
observe(runtime, journal_path="/tmp/my-run.jsonl", interval=0.15)
```

The journal is truncated when a new run starts; the server notices and begins a
new session instead of appending, so a restart is never mistaken for growth.

## Recording and replay

1. With a script running, press **● Record** in the viewer (or `POST
   /api/recording/start`). The recorder copies the live stream into memory and
   opens the recording with a **checkpoint**: the state that existed at that
   moment, so the file replays on its own.
2. Let the script run. Press **■ Stop**. The recording is written to
   `visualiser/sessions/<name>-<timestamp>.json`.
3. Stop the Machine script. Nothing else needs it.
4. Open the **Recordings** tab and press **Replay**.

Replay controls: play/pause, step forward and back, a seek slider over the event
sequence, and 0.25×–8× speed. Times shown are the recorded timestamps, and the
timeline is the ordered event sequence, not a redraw count. Playback happens in
the browser from the file; the server is only asked for the file. Journal and
session bytes are compared before and after replay in the test suite, and no
Machine process is alive at that point.

`GET /api/sessions/<id>` returns the whole recording, so a session file can be
inspected or re-served by anything. **Export state JSON** writes the current
view out; **Export view SVG** writes what is on screen.

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

D3 7.9.1 is vendored at `web/vendor/d3.min.js` (ISC, see
`web/vendor/LICENSE.d3`), so the viewer works without a network.

## Known limitations

* **Rendering is verified structurally, not pixel by pixel.** The DOM checks run
  in jsdom, which has no SVG geometry: element kinds, counts, labels, selection,
  filtering, zoom transforms, label sizing and the whole replay path are checked,
  but the visual layout itself is not.
* **Rule pattern terms churn while packs load.** Rule premises are re-rendered as
  the constructor registry grows, so a loading phase can emit a few
  `items.removed` for term nodes before settling. Steady state is stable; a graph
  built through `add_node`/`add_edge` never churns.
* **Two clients, one journal.** The journal is a single append-only file per run;
  two servers following the same file is fine (both only read), two Machine
  processes writing the same file is not, and the second truncates the first.
* **Derivations and search history are counted, not itemised.** They are trees,
  not carrier vertices; the viewer reports their root sizes in the counts stream
  and in the Details/Status panels.
* **No production caller.** `HypergraphIsomorphismMatch` and the search stack do
  not write to `graph.nodes`/`graph.edges`; the hypergraph content is whatever
  the script puts there. The viewer is faithful to that, not to a "run" that the
  Machine would define on its own.
