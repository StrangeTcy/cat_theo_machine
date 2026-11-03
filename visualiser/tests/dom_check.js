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

  check("no script errors", errors.length === 0, errors.slice(0, 3).join("; "));

  const failed = checks.filter((c) => !c.ok);
  console.log(JSON.stringify({ skipped: false, ok: failed.length === 0, checks: checks, failed: failed.length }, null, 2));
  process.exit(failed.length === 0 ? 0 : 1);
}

main().catch((error) => {
  console.log(JSON.stringify({ skipped: false, ok: false, fatal: String(error && error.stack || error) }));
  process.exit(1);
});
