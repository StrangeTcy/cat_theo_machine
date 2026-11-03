/* Pixel capture for the visualiser, for review and for the round-2 evidence log.
 *
 *   VIS_BASE=http://127.0.0.1:8801 node visualiser/tests/pixel_capture.js \
 *       --out verification/visualiser-round2 [--session <id>]
 *
 * What this is, exactly. The sandbox has no runnable browser (see README section
 * "How these screenshots were made"), so the page is driven in jsdom: the real
 * app.js, the real model.js, the real stylesheet and the real served data. Each
 * snapshot asks the page for its **own** exported SVG - the same "Export view
 * SVG" a user clicks - and writes that. A separate rasteriser turns the SVG into
 * a PNG. So the geometry, colours, shapes, labels and link positions in the PNGs
 * are the page's own output, not a re-drawing, and the SVG can be opened in any
 * viewer to check that.
 *
 * What it is not: a browser screenshot. jsdom has no layout engine, so the HTML
 * chrome (sidebar, toolbar, legend box, panels) is not in these images. Those are
 * checked by text assertions in dom_check.js and recorded in capture.json here.
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

const fs = require("fs");
const path = require("path");

const BASE = process.env.VIS_BASE || "http://127.0.0.1:8801";
const argv = process.argv.slice(2);
function arg(name, fallback) {
  const at = argv.indexOf("--" + name);
  return at === -1 ? fallback : argv[at + 1];
}
const OUT = arg("out", "verification/visualiser-round2");
const SESSION = arg("session", null);
const ONLY = arg("only", null);

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function openPage(errors) {
  const virtualConsole = new VirtualConsole();
  virtualConsole.on("jsdomError", (error) => {
    if (/navigation \(except hash changes\)/.test(String(error.message))) { return; }
    errors.push("jsdomError: " + error.message);
  });
  const dom = await JSDOM.fromURL(BASE + "/", {
    runScripts: "dangerously",
    resources: "usable",
    pretendToBeVisual: true,
    virtualConsole,
    beforeParse(window) {
      window.fetch = (url, options) => fetch(new URL(url, BASE).toString(), options);
      // jsdom implements neither EventSource nor layout; the stream is replaced
      // by nothing (the page seeds from /api/state) and the canvas is given a
      // real size so the zoom and fit code has a viewport to work with.
      window.EventSource = class {
        constructor(url) { this.url = url; this.readyState = 1; }
        close() { this.readyState = 2; }
      };
      const capture = { text: null };
      const RealBlob = window.Blob;
      window.Blob = class RecordingBlob extends RealBlob {
        constructor(parts, options) {
          super(parts, options);
          capture.text = (parts || []).join("");
        }
      };
      window.URL.createObjectURL = () => "blob:capture";
      window.URL.revokeObjectURL = () => {};
      window.HTMLAnchorElement.prototype.click = function () {};
      window.__capture = capture;
    }
  });
  const window = dom.window;
  const document = window.document;
  const svg = document.getElementById("canvas");
  Object.defineProperty(svg, "clientWidth", { value: 1440, configurable: true });
  Object.defineProperty(svg, "clientHeight", { value: 900, configurable: true });
  await wait(2000);
  return { dom, win: window, doc: document };
}

async function grab(page, name, report) {
  const { win, doc } = page;
  win.__capture.text = null;
  doc.getElementById("exportSvgButton").dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
  for (let i = 0; i < 40 && !win.__capture.text; i += 1) { await wait(50); }
  const svgText = win.__capture.text;
  if (!svgText) {
    report.push({ name: name, ok: false, reason: "no SVG produced" });
    return;
  }
  fs.mkdirSync(OUT, { recursive: true });
  fs.writeFileSync(path.join(OUT, name + ".svg"), svgText);
  const counts = {};
  doc.querySelectorAll("g.node").forEach((group) => {
    const shape = group.querySelector(".node-shape");
    const kind = ((shape && shape.getAttribute("class")) || "").replace("node-shape kind-", "").replace(" selected", "");
    counts[kind] = (counts[kind] || 0) + 1;
  });
  report.push({
    name: name,
    ok: true,
    svg: path.join(OUT, name + ".svg"),
    svgBytes: svgText.length,
    marks: counts,
    links: doc.querySelectorAll("line.link-line").length,
    linkLabels: Array.from(doc.querySelectorAll("text.link-label"))
      .filter((label) => !(label.getAttribute("class") || "").includes("hidden"))
      .map((label) => label.textContent),
    visibleLabels: doc.querySelectorAll("text.node-label:not(.hidden)").length,
    totalLabels: doc.querySelectorAll("text.node-label").length,
    viewsport: (doc.querySelector("g.viewport") || {}).getAttribute
      ? doc.querySelector("g.viewport").getAttribute("transform") : "",
    legend: (doc.getElementById("legendStats") || {}).textContent || "",
    details: (doc.getElementById("detailsBody") || {}).textContent || "",
    timeline: (doc.getElementById("timeText") || {}).textContent || "",
    mode: (doc.getElementById("modeBadge") || {}).textContent || ""
  });
}

async function main() {
  const errors = [];
  const report = [];
  const page = await openPage(errors);
  const { win, doc } = page;

  const want = (name) => !ONLY || ONLY === name;

  // 1. The state the page shows when it opens against a running viewer.
  if (want("01-live-initial")) {
    await wait(900);
    await grab(page, "01-live-initial", report);
  }

  // The rest runs from a recorded session, so every state is reproducible.
  let sessionId = SESSION;
  if (!sessionId) {
    const listing = await (await fetch(BASE + "/api/sessions")).json();
    const sessions = listing.sessions || [];
    sessionId = sessions.length ? sessions[0].id : null;
  }

  if (sessionId) {
    win.machineObserver.loadSession(sessionId);
    await wait(1800);
    win.machineObserver.fit();
    await wait(900);

    // 2. A graph dense with rules and hyperedges, fitted to the view.
    if (want("02-dense-rules-hyperedges")) {
      await grab(page, "02-dense-rules-hyperedges", report);
    }

    // 3. One hyperedge, close up: its argument links carry positions 1..n.
    if (want("03-hyperedge-closeup")) {
      const graph = win.machineObserver.graph();
      const ternary = graph.nodes.filter((node) => node.kind === "hyperedge" && (node.arguments || []).length >= 3)[0]
        || graph.nodes.filter((node) => node.kind === "hyperedge")[0];
      if (ternary) {
        win.machineObserver.select(ternary.id);
        // Focus is the details panel's own action: it zooms to 1.6x, which is
        // also the scale at which the argument-position numbers are shown.
        win.machineObserver.focus(ternary.id);
        await wait(1200);
        await grab(page, "03-hyperedge-closeup", report);
      }
    }

    // 4. Back out to the whole graph.
    if (want("04-fit-whole-graph")) {
      win.machineObserver.fit();
      await wait(900);
      await grab(page, "04-fit-whole-graph", report);
    }

    // 5. A selected vertex, with the provenance panel filled in.
    if (want("05-selection-provenance")) {
      const graph = win.machineObserver.graph();
      const vertex = graph.nodes.filter((node) => node.kind === "node")[0];
      if (vertex) {
        win.machineObserver.select(vertex.id);
        win.machineObserver.centerOn(vertex.id);
        await wait(900);
        await grab(page, "05-selection-provenance", report);
      }
    }

    // 6. Replay part-way through: the same recording, fewer events applied.
    if (want("06-replay-seek")) {
      const recording = await (await fetch(BASE + "/api/sessions/" + sessionId)).json();
      const third = Math.max(3, Math.floor((recording.events || []).length / 3));
      win.machineObserver.seek(third);
      await wait(900);
      win.machineObserver.fit();
      await wait(900);
      await grab(page, "06-replay-seek", report);
    }
  }

  // 7. A genuinely running Machine, seen from a freshly opened page.
  if (want("07-live-evolution")) {
    const live = await openPage(errors);
    live.win.machineObserver.fit();
    await wait(900);
    await grab(live, "07-live-evolution", report);
    live.dom.window.close();
  }

  fs.writeFileSync(path.join(OUT, "capture.json"), JSON.stringify({
    base: BASE,
    session: sessionId,
    capturedAt: new Date().toISOString(),
    note: "SVG written by the page's own Export view SVG; HTML chrome is not part of it",
    errors: errors,
    captures: report
  }, null, 2));
  const failed = report.filter((item) => !item.ok);
  console.log(JSON.stringify({ ok: failed.length === 0 && report.length > 0, captures: report.length, failed: failed.length, errors: errors }, null, 2));
  process.exit(failed.length === 0 ? 0 : 1);
}

main().catch((error) => {
  console.log(JSON.stringify({ ok: false, fatal: String(error && error.stack || error) }));
  process.exit(1);
});
