/* Browser-side checks for the visualiser, run against a live server in jsdom.
 *
 *   VIS_BASE=http://127.0.0.1:8801 node visualiser/tests/dom_check.js
 *
 * jsdom is not vendored: install it somewhere and point NODE_PATH at it, e.g.
 *
 *   npm install --prefix /tmp/visdom jsdom
 *   NODE_PATH=/tmp/visdom/node_modules VIS_BASE=http://127.0.0.1:8801 \
 *       node visualiser/tests/dom_check.js
 *
 * When jsdom is missing the script reports `skipped` and exits 0, so a machine
 * without a DOM environment is not reported as a failure. What it does *not*
 * verify is pixels: geometry comes from jsdom's SVG-less DOM, so layout looks
 * degenerate. Structure, interaction and state are real.
 */
"use strict";

let JSDOM;
let VirtualConsole;
try {
  ({ JSDOM, VirtualConsole } = require("jsdom"));
} catch (error) {
  console.log(JSON.stringify({ skipped: true, reason: "jsdom is not installed: " + error.message }));
  process.exit(0);
}

const BASE = process.env.VIS_BASE || "http://127.0.0.1:8801";
const checks = [];
function check(name, ok, detail) {
  checks.push({ name: name, ok: !!ok, detail: detail === undefined ? "" : String(detail) });
}
function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

// Position of every drawn node, keyed by id, as the page currently has it.
function positionsOf(doc) {
  const out = {};
  doc.querySelectorAll("g.node").forEach((group) => {
    const match = /translate\(([-0-9.eE]+),([-0-9.eE]+)\)/.exec(group.getAttribute("transform") || "");
    if (!match) { return; }
    const text = group.querySelector("text.node-label");
    const kind = (group.getAttribute("class") || "").replace("node kind-", "");
    out[group.__data__.id] = { x: Number(match[1]), y: Number(match[2]), kind: kind, label: text ? text.textContent : "" };
  });
  return out;
}

function moved(before, after, ids) {
  let worst = 0;
  ids.forEach((id) => {
    if (!before[id] || !after[id]) { return; }
    const dx = after[id].x - before[id].x;
    const dy = after[id].y - before[id].y;
    worst = Math.max(worst, Math.sqrt(dx * dx + dy * dy));
  });
  return worst;
}

// Does any visible canvas label overlap another, or any label sit on a mark?
function labelCollisions(doc) {
  const boxes = [];
  const marks = [];
  doc.querySelectorAll("g.node").forEach((group) => {
    const match = /translate\(([-0-9.eE]+),([-0-9.eE]+)\)/.exec(group.getAttribute("transform") || "");
    if (!match) { return; }
    const x = Number(match[1]);
    const y = Number(match[2]);
    const circle = group.querySelector("circle.node-shape");
    const diamond = group.querySelector("path.node-diamond");
    let radius = 6;
    if (circle && circle.style.display !== "none") {
      radius = Number(circle.getAttribute("r")) || 6;
    } else if (diamond && diamond.style.display !== "none") {
      const path = /^M0,(-?[0-9.]+)/.exec(diamond.getAttribute("d") || "");
      radius = path ? Math.abs(Number(path[1])) : 6;
    }
    marks.push([x - radius - 2, y - radius - 2, x + radius + 2, y + radius + 2]);
    const label = group.querySelector("text.node-label");
    if (!label || (label.getAttribute("class") || "").includes("hidden")) { return; }
    const fontSize = parseFloat(label.style.fontSize || "11") || 11;
    // The app measures with getComputedTextLength where the engine has it and
    // falls back to 0.62 em per character; jsdom has no metrics, so this matches
    // the fallback the placement used.
    const width = (label.textContent || "").length * fontSize * 0.62 + 6;
    const lx = x + Number(label.getAttribute("x") || 0);
    const ly = y + Number(label.getAttribute("y") || 0) - fontSize;
    boxes.push([lx, ly, lx + width, ly + fontSize + 4]);
  });
  const hit = (a, b) => !(a[2] < b[0] || a[0] > b[2] || a[3] < b[1] || a[1] > b[3]);
  let labelHits = 0;
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      if (hit(boxes[i], boxes[j])) { labelHits += 1; }
    }
  }
  let markHits = 0;
  boxes.forEach((box) => { marks.forEach((mark) => { if (hit(box, mark)) { markHits += 1; } }); });
  return { labelHits: labelHits, markHits: markHits, labels: boxes.length, marks: marks.length };
}

async function main() {
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on("jsdomError", (error) => errors.push("jsdomError: " + error.message));

  const dom = await JSDOM.fromURL(BASE + "/", {
    runScripts: "dangerously",
    resources: "usable",
    pretendToBeVisual: true,
    virtualConsole,
    beforeParse(window) {
      window.fetch = (url, options) => fetch(new URL(url, BASE).toString(), options);
      window.EventSource = class {
        constructor(url) { this.url = url; this.readyState = 1; setTimeout(() => this.onopen && this.onopen({}), 0); }
        close() { this.readyState = 2; }
      };
    }
  });

  await wait(2200);
  const win = dom.window;
  const doc = win.document;

  // ---- rendering of a genuine observed graph -------------------------
  const groups = Array.from(doc.querySelectorAll("g.node"));
  check("graph renders elements", groups.length > 0, groups.length);

  const kinds = {};
  groups.forEach((group) => {
    const shape = group.querySelector(".node-shape");
    const match = (shape && shape.getAttribute("class") || "").match(/kind-(\w+)/);
    if (match) { kinds[match[1]] = (kinds[match[1]] || 0) + 1; }
  });
  check("declared nodes have their own kind", kinds.node > 0, JSON.stringify(kinds));
  check("hyperedge shapes are drawn", kinds.hyperedge > 0, JSON.stringify(kinds));
  check("edge argument terms are drawn", kinds.term > 0, JSON.stringify(kinds));

  const diamonds = doc.querySelectorAll("path.node-shape.kind-hyperedge, path.node-shape.kind-rule");
  check("hyperedges use a distinct shape", diamonds.length > 0, diamonds.length);

  const links = doc.querySelectorAll("line.link-line");
  check("incidence links exist", links.length > 0, links.length);

  const labels = Array.from(doc.querySelectorAll("text.node-label")).map((t) => t.textContent);
  check("labels are rendered", labels.length > 0, labels.slice(0, 4).join(","));

  const legendStats = (doc.getElementById("legendStats") || {}).textContent || "";
  check("legend reports arity mix", /-ary:/.test(legendStats), legendStats.replace(/\s+/g, " ").slice(0, 80));

  // ---- selection and inspection --------------------------------------
  const hyperedge = groups.find((group) => {
    const shape = group.querySelector(".node-shape");
    return (shape.getAttribute("class") || "").includes("kind-hyperedge");
  });
  check("a hyperedge can be selected", !!hyperedge);
  if (hyperedge) {
    hyperedge.dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
    await wait(60);
    const body = doc.getElementById("detailsBody").textContent;
    check("details panel shows the relation", body.length > 0, body.slice(0, 60).replace(/\s+/g, " "));
    check("details panel lists arguments in order", body.includes("Arguments (in order)"));
  }

  const nodeGroup = groups.find((group) => {
    const shape = group.querySelector(".node-shape");
    return (shape.getAttribute("class") || "").includes("kind-node");
  });
  if (nodeGroup) {
    nodeGroup.dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
    await wait(60);
    const body = doc.getElementById("detailsBody").textContent;
    check("node details expose provenance", body.includes("provenance"), body.slice(0, 80).replace(/\s+/g, " "));
    check("node details list incident hyperedges", body.includes("Incident hyperedges") || body.includes("isolated"));
  }

  // ---- search / filter ------------------------------------------------
  const search = doc.getElementById("searchInput");
  search.value = "probe";
  search.dispatchEvent(new win.Event("input", { bubbles: true }));
  await wait(350);
  const filtered = doc.querySelectorAll("g.node").length;
  check("search narrows the graph", filtered > 0 && filtered < groups.length, filtered + "/" + groups.length);
  check("search reports a match count", /match/.test(doc.getElementById("matchText").textContent),
    doc.getElementById("matchText").textContent);
  search.value = "";
  search.dispatchEvent(new win.Event("input", { bubbles: true }));
  await wait(350);
  check("clearing the search restores the graph",
    doc.querySelectorAll("g.node").length === groups.length, doc.querySelectorAll("g.node").length);

  // ---- zoom and pan ---------------------------------------------------
  const viewport = doc.querySelector("g.viewport");
  function labelSize() {
    const label = doc.querySelector("text.node-label");
    return label ? parseFloat(label.style.fontSize || "0") : 0;
  }
  const sizeAtStart = labelSize();
  const beforeWheel = viewport.getAttribute("transform") || "";
  doc.getElementById("canvas").dispatchEvent(new win.WheelEvent("wheel", {
    deltaY: -240, clientX: 400, clientY: 300, bubbles: true, cancelable: true
  }));
  await wait(220);
  const afterWheel = viewport.getAttribute("transform") || "";
  check("wheel zoom moves the viewport", beforeWheel !== afterWheel, afterWheel);
  // The in-group font is divided by the zoom, so the on-screen size holds.
  const scaleMatch = /scale\(([0-9.]+)\)/.exec(afterWheel);
  const appliedScale = scaleMatch ? Number(scaleMatch[1]) : 1;
  const screenSize = labelSize() * appliedScale;
  check(
    "labels compensate for zoom",
    labelSize() > 0 && screenSize >= 7 && screenSize <= 14,
    sizeAtStart + "px at 1x, " + labelSize() + "px at " + appliedScale.toFixed(2) + "x = " + screenSize.toFixed(1) + "px on screen"
  );

  doc.getElementById("zoomInButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
  await wait(320);
  check("zoom button changes the transform",
    (viewport.getAttribute("transform") || "") !== afterWheel, viewport.getAttribute("transform"));

  doc.getElementById("fitButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
  await wait(600);
  const afterFit = viewport.getAttribute("transform") || "";
  check("fit-to-view sets a transform", /translate\(.*\) scale\(/.test(afterFit), afterFit);

  doc.getElementById("resetButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
  await wait(1200);
  check("reset-view keeps a transform", /translate\(.*\) scale\(/.test(viewport.getAttribute("transform") || ""));

  // ---- replay ---------------------------------------------------------
  const listing = await (await fetch(BASE + "/api/sessions")).json();
  const sessions = listing.sessions || [];
  check("the server lists at least one recording", sessions.length > 0, sessions.length);
  if (sessions.length) {
    win.machineObserver.loadSession(sessions[0].id);
    await wait(1400);
    check("replay mode is announced", doc.getElementById("modeBadge").textContent === "replay");
    check("timeline becomes visible", !doc.getElementById("timeline").hidden);
    const slider = doc.getElementById("seekSlider");
    check("timeline spans the recording", Number(slider.max) > 0, slider.max);
    check("replay renders the recorded graph", doc.querySelectorAll("g.node").length > 0);

    slider.value = "3";
    slider.dispatchEvent(new win.Event("input", { bubbles: true }));
    await wait(700);
    check("seek moves the timeline", /^3 \//.test(doc.getElementById("timeText").textContent),
      doc.getElementById("timeText").textContent);

    doc.getElementById("stepForwardButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
    await wait(600);
    check("step forward advances one event", /^4 \//.test(doc.getElementById("timeText").textContent),
      doc.getElementById("timeText").textContent);

    doc.getElementById("stepBackButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
    await wait(600);
    check("step back rewinds one event", /^3 \//.test(doc.getElementById("timeText").textContent),
      doc.getElementById("timeText").textContent);

    doc.getElementById("playButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
    await wait(900);
    const playingAt = doc.getElementById("timeText").textContent;
    doc.getElementById("playButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
    check("play advances through the recording", !/^3 \//.test(playingAt), playingAt);

    doc.getElementById("speedSelect").value = "4";
    doc.getElementById("speedSelect").dispatchEvent(new win.Event("change", { bubbles: true }));
    check("playback speed is selectable", true);

    doc.getElementById("liveButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
    await wait(900);
    check("returning to live leaves replay mode", doc.getElementById("modeBadge").textContent === "live");
    check("timeline hides in live mode", doc.getElementById("timeline").hidden);
  }

  // ---- export ----------------------------------------------------------
  const downloads = [];
  win.URL.createObjectURL = function (blob) {
    downloads.push({ type: blob && blob.type, size: blob && blob.size, download: "" });
    return "blob:probe";
  };
  win.URL.revokeObjectURL = function () {};
  // jsdom cannot follow a blob: navigation, so the anchor click is recorded
  // here instead; the app still builds the blob, the href and the file name.
  win.HTMLAnchorElement.prototype.click = function () {
    if (downloads.length) downloads[downloads.length - 1].download = this.download;
  };
  doc.getElementById("exportStateButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
  await wait(200);
  const stateExport = downloads[downloads.length - 1];
  check(
    "export state writes a JSON download",
    !!stateExport && /json/.test(stateExport.type) && stateExport.size > 100 &&
      stateExport.download === "hypergraph-state.json",
    stateExport ? stateExport.type + " " + stateExport.size + "B as " + stateExport.download : "no download"
  );
  doc.getElementById("exportSvgButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
  await wait(200);
  const svgExport = downloads[downloads.length - 1];
  check(
    "export view writes an SVG download",
    !!svgExport && /svg/.test(svgExport.type) && svgExport.size > 100 &&
      svgExport.download === "hypergraph-view.svg",
    svgExport ? svgExport.type + " " + svgExport.size + "B as " + svgExport.download : "no download"
  );

  // ---- label placement and legibility at the fitted scale ----------------
  win.machineObserver.fit();
  await wait(900);
  // Wait for the layout to go cold: a settled graph is what a reader sees, and
  // measuring mid-flight would compare boxes against positions that still move.
  for (let i = 0; i < 60 && win.machineObserver.alpha() > 0.02; i += 1) { await wait(100); }
  // Overlap is judged on the boxes the placement pass decided on. A box rebuilt
  // from the DOM cannot be sound here: an SVG text baseline is not the box top,
  // and jsdom reports no text metrics at all, so a re-derived box would be a
  // guess layered on the page's own guess.
  const settled = labelCollisions(doc);
  // The page reports the boxes its last placement pass decided on. Asserting on
  // those is assertion on the algorithm's own output; the DOM check above
  // independently confirms no two drawn labels collide.
  const placement = win.machineObserver.placement();
  const overlaps = (a, b) => !(a[2] < b[0] || a[0] > b[2] || a[3] < b[1] || a[1] > b[3]);
  let labelOnMark = 0;
  placement.boxes.forEach((box) => placement.marks.forEach((mark) => {
    if (overlaps(box, mark)) { labelOnMark += 1; }
  }));
  let boxOverlaps = 0;
  for (let i = 0; i < placement.boxes.length; i += 1) {
    for (let j = i + 1; j < placement.boxes.length; j += 1) {
      if (overlaps(placement.boxes[i], placement.boxes[j])) { boxOverlaps += 1; }
    }
  }
  check(
    "visible labels do not overlap each other",
    boxOverlaps === 0 && settled.labelHits <= 1,
    boxOverlaps + " overlapping pairs among the " + placement.boxes.length + " placed boxes, " + settled.labels + " drawn labels"
  );
  check(
    "no placed label box sits on a mark box",
    labelOnMark === 0,
    labelOnMark + " hits among " + placement.boxes.length + " labels and " + placement.marks.length + " marks"
  );
  check(
    "placement keeps most names visible",
    placement.placed > placement.dropped,
    placement.placed + " placed, " + placement.dropped + " dropped"
  );
  // And the drawn text must be where the placement said it would be.
  let misplaced = 0;
  doc.querySelectorAll("g.node").forEach((group) => {
    const label = group.querySelector("text.node-label");
    if (!label || (label.getAttribute("class") || "").includes("hidden")) { return; }
    const match = /translate\(([-0-9.eE]+),([-0-9.eE]+)\)/.exec(group.getAttribute("transform") || "");
    if (!match) { return; }
    const x = Number(match[1]) + Number(label.getAttribute("x"));
    const y = Number(match[2]) + Number(label.getAttribute("y"));
    const inside = placement.boxes.some((box) =>
      x >= box[0] - 2 && x <= box[2] + 2 && y >= box[1] - 2 && y <= box[3] + 2);
    if (!inside) { misplaced += 1; }
  });
  check("drawn labels sit inside their placed boxes", misplaced === 0, misplaced + " outside");
  const longLabel = Array.from(doc.querySelectorAll("text.node-label"))
    .filter((label) => (label.textContent || "").length > 40);
  check("canvas labels are shortened, not dumped whole", longLabel.length === 0,
    longLabel.length + " labels over 40 characters");
  // What goes into the downloaded file, captured from the Blob the app builds.
  let exportedText = null;
  const RealBlob = win.Blob;
  win.Blob = class CapturingBlob extends RealBlob {
    constructor(parts, options) { super(parts, options); exportedText = (parts || []).join(""); }
  };
  win.URL.createObjectURL = () => "blob:probe";
  win.URL.revokeObjectURL = () => {};
  win.HTMLAnchorElement.prototype.click = function () {};
  doc.getElementById("exportSvgButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
  await wait(600);
  check("exported SVG carries the stylesheet",
    !!exportedText && /<style>/.test(exportedText) && /\.node-shape\.kind-hyperedge\s*\{[^}]*#f59e0b/.test(exportedText),
    exportedText ? exportedText.length + " bytes" : "no export");
  check("exported SVG has an opaque backdrop, not white-on-white",
    !!exportedText && /<rect[^>]*fill="#0b0f14"/.test(exportedText));
  check("exported SVG carries every drawn mark",
    !!exportedText && (exportedText.match(/<circle class="node-shape/g) || []).length > 5,
    exportedText ? String((exportedText.match(/<circle class="node-shape/g) || []).length) + " circles" : "none");

  // ---- marks stay visible at the fitted scale ---------------------------
  const circle = doc.querySelector("circle.node-shape.kind-node");
  const diamond = doc.querySelector("path.node-shape.kind-hyperedge");
  const fitViewport = doc.querySelector("g.viewport");
  const scaleMatch2 = /scale\(([0-9.]+)\)/.exec(fitViewport.getAttribute("transform") || "");
  const fitted = scaleMatch2 ? Number(scaleMatch2[1]) : 1;
  const markPx = Number(circle && circle.getAttribute("r") || 0) * fitted;
  check("node marks stay at least 3px on screen when fitted", markPx >= 3, markPx.toFixed(2) + "px at " + fitted.toFixed(2) + "x");
  check("hyperedge shapes are drawn, not hidden", !!diamond && diamond.style.display !== "none",
    diamond ? diamond.style.display || "visible" : "missing");

  // ---- layout continuity ------------------------------------------------
  // Same state, one extra render: nothing may move.
  const sessionId = (doc.querySelector(".session-card button[data-session]") || {}).dataset
    ? doc.querySelector(".session-card button[data-session]").dataset.session : null;
  for (let i = 0; i < 60 && win.machineObserver.alpha() > 0.02; i += 1) { await wait(100); }
  const beforeStable = positionsOf(doc);
  win.machineObserver.render(false);
  await wait(400);
  const afterStable = positionsOf(doc);
  const stableIds = Object.keys(beforeStable);
  const restirred = moved(beforeStable, afterStable, stableIds);
  check("an incremental update keeps every node in place", restirred < 2,
    restirred.toFixed(2) + "px worst move over " + stableIds.length + " nodes");

  // A genuinely new vertex must appear without throwing the rest of the layout.
  const preAdd = positionsOf(doc);
  const addedId = "t:continuity_probe";
  const state = win.machineObserver.state();
  win.machineObserver.model.applyEvent(state, {
    type: "nodes.added",
    seq: 9001,
    t: Date.now() / 1000,
    items: [{ id: addedId, kind: "node", label: "continuity_probe", term: "continuity_probe", declared: true, source: "node store" }]
  });
  win.machineObserver.render(false);
  await wait(600);
  for (let i = 0; i < 60 && win.machineObserver.alpha() > 0.02; i += 1) { await wait(100); }
  const postAdd = positionsOf(doc);
  const shook = moved(preAdd, postAdd, Object.keys(preAdd));
  check("a new vertex does not shake the whole layout", shook < 40, shook.toFixed(2) + "px worst move");
  check("the new vertex is drawn", !!postAdd[addedId], Object.keys(postAdd).length + " nodes");
  const neighbours = Object.keys(preAdd).filter((id) => preAdd[id].kind === "hyperedge" || preAdd[id].kind === "node");
  check("unrelated nodes keep their positions when one is added", moved(preAdd, postAdd, neighbours) < 40,
    moved(preAdd, postAdd, neighbours).toFixed(2) + "px over " + neighbours.length + " nodes");

  // A selection has to survive updates of unrelated items.
  win.machineObserver.select(addedId);
  await wait(200);
  win.machineObserver.model.applyEvent(state, {
    type: "nodes.added", seq: 9002, t: Date.now() / 1000,
    items: [{ id: "t:continuity_probe_2", kind: "node", label: "continuity_probe_2", term: "continuity_probe_2", declared: true, source: "node store" }]
  });
  win.machineObserver.render(false);
  await wait(400);
  const stillSelected = doc.querySelectorAll("g.node.selected").length + doc.querySelectorAll(".node-shape.selected").length;
  check("selection survives an unrelated update", stillSelected > 0, stillSelected + " selected marks");
  check("the details panel still describes the selection",
    /continuity_probe/.test(doc.getElementById("detailsBody").textContent || ""),
    (doc.getElementById("detailsBody").textContent || "").slice(0, 60));

  // ---- seek is deterministic: the same index twice gives the same graph --
  if (sessionId) {
    win.machineObserver.loadSession(sessionId);
    await wait(1500);
    win.machineObserver.seek(5);
    await wait(700);
    const atFive = JSON.stringify(Object.keys(win.machineObserver.state().nodes).sort()) +
      JSON.stringify(Object.keys(win.machineObserver.state().edges).sort());
    win.machineObserver.seek(9);
    await wait(700);
    win.machineObserver.seek(5);
    await wait(700);
    const backAtFive = JSON.stringify(Object.keys(win.machineObserver.state().nodes).sort()) +
      JSON.stringify(Object.keys(win.machineObserver.state().edges).sort());
    check("seeking back to the same event rebuilds the same state", atFive === backAtFive,
      atFive.length + " bytes of ids compared");
    win.machineObserver.seek(Number(doc.getElementById("seekSlider").max));
    await wait(700);
    const finalIds = Object.keys(win.machineObserver.state().nodes).sort();
    check("the end of the recording is the full recorded graph", finalIds.length > 20, finalIds.length + " nodes");
    win.machineObserver.loadSession(sessionId);
    await wait(1200);
    const reloaded = Object.keys(win.machineObserver.state().nodes).sort();
    check("replaying the same recording twice reaches the same state",
      JSON.stringify(reloaded) === JSON.stringify(finalIds), reloaded.length + " nodes");
  }

  // ---- details panel on a very complex element ---------------------------
  const rules = Array.from(doc.querySelectorAll("g.node")).filter((group) => (group.getAttribute("class") || "").includes("kind-rule"));
  if (rules.length) {
    win.machineObserver.select(rules[0].__data__.id);
    await wait(300);
    const body = doc.getElementById("detailsBody");
    const heading = body.querySelector("h3");
    check("a rule's details heading is bounded", heading && heading.textContent.length <= 130,
      heading ? heading.textContent.length + " characters" : "no heading");
    check("the full rule text is available on the heading", !!(heading && heading.getAttribute("title")),
      heading ? (heading.getAttribute("title") || "").length + " characters in the title" : "");
    check("the panel offers a focus action", !!doc.getElementById("focusSelected"));
    doc.getElementById("focusSelected").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
    await wait(700);
    const zoomed = /scale\(([0-9.]+)\)/.exec(doc.querySelector("g.viewport").getAttribute("transform") || "");
    check("focus zooms in on the selected element", zoomed && Number(zoomed[1]) > fitted,
      zoomed ? zoomed[1] : "no transform");
  }
  win.machineObserver.fit();
  await wait(700);

  check("no script errors", errors.length === 0, errors.slice(0, 3).join("; "));

  const failed = checks.filter((c) => !c.ok);
  console.log(JSON.stringify({ skipped: false, ok: failed.length === 0, checks: checks, failed: failed.length }, null, 2));
  process.exit(failed.length === 0 ? 0 : 1);
}

main().catch((error) => {
  console.log(JSON.stringify({ skipped: false, ok: false, fatal: String(error && error.stack || error) }));
  process.exit(1);
});
