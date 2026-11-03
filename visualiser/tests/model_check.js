/* Model checks for visualiser/web/model.js — run with plain node, no dependencies.
 *
 *   node visualiser/tests/model_check.js [session.json]
 *
 * With no argument it builds its own event stream (a labelled fixture, not
 * Machine output). With a session file it checks the recorded stream as well.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const V = require(path.join(__dirname, "..", "web", "model.js"));

const checks = [];
function check(name, condition, detail) {
  checks.push({ name: name, ok: !!condition, detail: detail === undefined ? "" : String(detail) });
}

// ---------------------------------------------------------------- fixture
const events = [
  { v: 1, seq: 0, t: 100.0, type: "session.start", machine: { pid: 1234 }, source: {} },
  {
    v: 1, seq: 1, t: 100.2, type: "nodes.added",
    items: [
      { id: "t:a", kind: "node", label: "a", term: "a", declared: true, source: "node store" },
      { id: "t:b", kind: "node", label: "b", term: "b", declared: true, source: "node store" },
      { id: "t:c", kind: "node", label: "c", term: "c", declared: true, source: "node store" }
    ]
  },
  {
    v: 1, seq: 2, t: 100.4, type: "edges.added",
    items: [
      {
        id: "e:R", kind: "hyperedge", label: "R", relation: "R", arity: 3,
        arguments: ["t:a", "t:b", "t:c"], results: [], source: "edge store"
      }
    ]
  },
  {
    v: 1, seq: 3, t: 100.6, type: "edges.added",
    items: [
      {
        id: "e:N", kind: "hyperedge", label: "N", relation: "N", arity: 0,
        arguments: [], results: [], source: "edge store"
      }
    ]
  },
  { v: 1, seq: 4, t: 100.8, type: "counts", counts: { nodes: 3, edges: 2 } },
  { v: 1, seq: 5, t: 101.0, type: "session.stop", reason: "fixture end" }
];

const state = V.rebuild(events);
check("rebuild applies every event", state.applied === events.length, state.applied);
check("three declared nodes", Object.keys(state.nodes).length === 3);
check("two hyperedges", Object.keys(state.edges).length === 2);
check("session start recorded", state.machine.pid === 1234);
check("session stop recorded", state.stopped === "fixture end");

const model = V.graphModel(state);
check("model has all elements", model.nodes.length === 5, model.nodes.length);
check("incidence links equal total arity", model.links.length === 3, model.links.length);

const ternary = model.links.filter((l) => l.edge === "e:R");
check("ternary hyperedge keeps arity 3", ternary.length === 3, ternary.length);
check(
  "argument positions preserved",
  ternary.map((l) => l.position).join(",") === "1,2,3",
  ternary.map((l) => l.position).join(",")
);
check(
  "argument order preserved",
  ternary.map((l) => l.other).join(",") === "t:a,t:b,t:c",
  ternary.map((l) => l.other).join(",")
);
check("nullary edge produces no links", model.links.filter((l) => l.edge === "e:N").length === 0);
check("no pairwise flattening: 1 hyperedge -> 3 links, not 3 node-node pairs",
  ternary.every((l) => l.edge === "e:R" && l.target === "e:R"));

// provenance stamping
check("origin seq stamped on items", state.nodes["t:a"]._seq === 1, state.nodes["t:a"]._seq);
check("origin time stamped on items", Math.abs(state.nodes["t:a"]._t - 100.2) < 1e-9);

// placeholders for edges whose arguments were never announced
const orphan = V.rebuild([
  { type: "edges.added", items: [{ id: "e:X", kind: "hyperedge", label: "X", arguments: ["t:ghost"] }] }
]);
const orphanModel = V.graphModel(orphan);
check("unknown argument becomes a placeholder node", orphanModel.byId["t:ghost"] !== undefined);
check("placeholder flagged", orphanModel.placeholders.indexOf("t:ghost") >= 0);
check("no dangling links", orphanModel.links.every((l) => orphanModel.byId[l.source] && orphanModel.byId[l.target]));

// removal
const removed = V.rebuild([
  events[1],
  { type: "items.removed", nodes: ["t:b"] }
]);
check("removal drops the node", Object.keys(removed.nodes).length === 2);

// filtering
const filtered = V.filterModel(model, "b", null);
check("text filter keeps the match", filtered.nodes.some((n) => n.id === "t:b"));
check("text filter drops the rest", !filtered.nodes.some((n) => n.id === "t:a"));
const byKind = V.filterModel(model, "", ["hyperedge"]);
check("kind filter keeps hyperedges", byKind.nodes.every((n) => n.kind === "hyperedge"));
check("kind filter counts 2", byKind.nodes.length === 2, byKind.nodes.length);

// determinism and seeking
check(
  "rebuild is deterministic",
  JSON.stringify(V.graphModel(V.rebuild(events))) === JSON.stringify(V.graphModel(V.rebuild(events)))
);
const partial = V.rebuild(events, 2);
check("partial rebuild stops early", partial.applied === 2, partial.applied);
const grown = V.createState();
V.applyUntil(grown, events, 2);
V.applyUntil(grown, events, 5);
check("applyUntil is resumable", grown.applied === 5, grown.applied);
check(
  "resumed state equals a full rebuild",
  JSON.stringify(grown.nodes) === JSON.stringify(V.rebuild(events, 5).nodes)
);

const stats = V.stats(state);
check("stats count kinds", stats.kinds.node === 3 && stats.kinds.hyperedge === 2, JSON.stringify(stats.kinds));
check("stats report max arity", stats.maxArity === 3, stats.maxArity);

// -------------------------------------------------- optional: a real session
const sessionPath = process.argv[2];
if (sessionPath) {
  const doc = JSON.parse(fs.readFileSync(sessionPath, "utf8"));
  const recorded = V.rebuild(doc.events);
  check("recorded session rebuilds", recorded.applied === doc.events.length, recorded.applied);
  const recordedModel = V.graphModel(recorded);
  check(
    "recorded session links are all resolvable",
    recordedModel.links.every((l) => recordedModel.byId[l.source] && recordedModel.byId[l.target])
  );
  // Hyperedge arity only: a rule's incoming links are its premises, and mixing
  // them in would read as graph arity, which is how the legend reports it too.
  const arities = {};
  Object.keys(recorded.edges).forEach((id) => {
    const item = recorded.edges[id];
    if (item.kind === "rule") return;
    const arity = (item.arguments || []).length;
    arities[arity] = (arities[arity] || 0) + 1;
  });
  check("recorded session has hyperedges", Object.keys(recorded.edges).length > 0, Object.keys(recorded.edges).length);
  check("recorded session keeps n-ary edges", Object.keys(arities).some((k) => Number(k) >= 3), JSON.stringify(arities));
  check("recorded session keeps a nullary edge", arities[0] >= 1, JSON.stringify(arities));
  // Seeking is checked on the sequence, not on the element count: an event may
  // legitimately remove something (graph surgery, or a term re-rendered as the
  // constructor registry grows), so a smaller snapshot is not a lost event.
  let prefixesExact = true;
  let sequencesOrdered = true;
  let previousSeq = -1;
  for (let i = 0; i <= doc.events.length; i += 1) {
    const snapshot = V.rebuild(doc.events, i);
    if (snapshot.applied !== i) prefixesExact = false;
    if (snapshot.lastSeq < previousSeq) sequencesOrdered = false;
    previousSeq = snapshot.lastSeq;
  }
  check("every seek prefix applies exactly its events", prefixesExact);
  check("seek prefixes keep sequence order", sequencesOrdered);
  const resumable = V.applyUntil(V.rebuild(doc.events, 1), doc.events, doc.events.length);
  const full = V.rebuild(doc.events);
  check(
    "resuming from a seek reaches the full state",
    Object.keys(resumable.nodes).join() === Object.keys(full.nodes).join() &&
      Object.keys(resumable.edges).join() === Object.keys(full.edges).join() &&
      resumable.applied === full.applied
  );
  const stampOrdered = doc.events.every(
    (event, index) => index === 0 || !(event.t < doc.events[index - 1].t)
  );
  check("recorded timestamps never go backwards", stampOrdered);
  const recordedRules = Object.keys(recorded.edges)
    .map((id) => recorded.edges[id])
    .filter((item) => item.kind === "rule");
  check(
    "recorded rule labels are readable terms, not host reprs",
    recordedRules.every((item) => item.label.indexOf("object at 0x") === -1 && item.label.length > 0),
    recordedRules.length + " rules"
  );
  check(
    "recorded rules keep premises and a replacement",
    recordedRules.every(
      (item) => (item.arguments || []).length >= 1 && (item.results || []).length === 1
    ),
    recordedRules.length + " rules"
  );
}

const failed = checks.filter((c) => !c.ok);
console.log(JSON.stringify({ ok: failed.length === 0, checks: checks, failed: failed.length }, null, 2));
process.exit(failed.length === 0 ? 0 : 1);
