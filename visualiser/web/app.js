/* Machine hypergraph observer — browser client.
 *
 * Two data paths, one renderer:
 *   live    — /api/state seeds the model, /api/events streams deltas
 *   replay  — a recorded session file, applied event by event
 *
 * The page never runs the Machine. It reads a journal the Machine chose to
 * write, and a session file the recorder wrote.
 */
(function () {
  "use strict";

  var V = window.VisModel;
  var d3 = window.d3;

  var el = {
    svg: document.getElementById("canvas"),
    legend: document.getElementById("legend"),
    badge: document.getElementById("modeBadge"),
    sourceText: document.getElementById("sourceText"),
    search: document.getElementById("searchInput"),
    matchText: document.getElementById("matchText"),
    details: document.getElementById("detailsBody"),
    legendStats: document.getElementById("legendStats"),
    banner: document.getElementById("banner"),
    statusBody: document.getElementById("statusBody"),
    sessionList: document.getElementById("sessionList"),
    sessionName: document.getElementById("sessionName"),
    recordStatus: document.getElementById("recordStatus"),
    recordButton: document.getElementById("recordButton"),
    timeline: document.getElementById("timeline"),
    playButton: document.getElementById("playButton"),
    seekSlider: document.getElementById("seekSlider"),
    timeText: document.getElementById("timeText"),
    speedSelect: document.getElementById("speedSelect"),
    replayTitle: document.getElementById("replayTitle")
  };

  var COLORS = {
    node: "#2dd4bf",
    term: "#94a3b8",
    hyperedge: "#f59e0b",
    rule: "#a78bfa"
  };
  var RADIUS = { node: 7, term: 5.5, hyperedge: 9, rule: 8 };

  var mode = "live";
  var live = V.createState();
  var liveSource = null;
  var stream = null;

  var replay = { events: [], state: null, index: 0, meta: {}, id: null };
  var playing = false;
  var speed = 1;
  var playTimer = null;

  var selectedId = null;
  var query = "";
  var kindFilter = ["node", "term", "hyperedge", "rule"];
  var pendingRender = false;
  var recording = false;
  var currentScale = 1;

  // ---------------------------------------------------------------- layout
  var svg = d3.select(el.svg);
  var rootG = svg.append("g").attr("class", "viewport");
  var linkLayer = rootG.append("g").attr("class", "links");
  var labelLayer = rootG.append("g").attr("class", "link-labels");
  var nodeLayer = rootG.append("g").attr("class", "nodes");

  var nodeData = new Map();
  var previousNodeCount = 0;
  var previousLinkCount = 0;
  var linkData = [];
  var modelById = {};

  function viewExtent() {
    var width = el.svg.clientWidth || 900;
    var height = el.svg.clientHeight || 650;
    return [[0, 0], [width, height]];
  }

  var zoom = d3
    .zoom()
    .scaleExtent([0.05, 6])
    .extent(viewExtent)
    .on("zoom", function (event) {
      rootG.attr("transform", event.transform);
      currentScale = event.transform.k;
      updateLabelVisibility();
    });
  svg.call(zoom).on("dblclick.zoom", null);

  var simulation = d3
    .forceSimulation()
    .force("link", d3.forceLink().id(function (d) { return d.id; }).distance(linkDistance).strength(0.35))
    .force("charge", d3.forceManyBody().strength(function (d) { return d.kind === "hyperedge" || d.kind === "rule" ? -420 : -190; }))
    .force("collide", d3.forceCollide(function (d) { return radiusOf(d) + 5; }))
    .force("x", d3.forceX(0).strength(0.035))
    .force("y", d3.forceY(0).strength(0.035))
    .on("tick", ticked);

  function radiusOf(d) { return RADIUS[d.kind] || 6; }
  function linkDistance(l) { return l && (l.direction === "out" ? 74 : 58); }

  // ------------------------------------------------------------- utilities
  function escapeHtml(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function clipboardLink(text) { return text == null ? "" : String(text); }

  function activeState() { return mode === "live" ? live : replay.state; }
  function activeGraph() { return V.graphModel(activeState()); }

  function hashString(text) {
    var hash = 2166136261;
    for (var i = 0; i < text.length; i += 1) {
      hash ^= text.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return hash >>> 0;
  }

  function seededAngle(id) { return (hashString(id) % 3600) / 3600 * Math.PI * 2; }

  // ------------------------------------------------------------- rendering
  function scheduleRender(restart) {
    if (restart) { forceRestart = true; }
    if (pendingRender) { return; }
    pendingRender = true;
    window.requestAnimationFrame(function () {
      pendingRender = false;
      renderGraph(forceRestart);
      forceRestart = false;
    });
  }
  var forceRestart = false;

  function renderGraph(withRestart) {
    var graph = activeGraph();
    modelById = graph.byId;

    var filtered = V.filterModel(graph, query, kindFilter);
    var keep = {};
    filtered.nodes.forEach(function (node) { keep[node.id] = true; });

    // Reuse node objects so positions survive every update.
    var nodes = [];
    graph.nodes.forEach(function (node) {
      if (!keep[node.id]) { return; }
      var existing = nodeData.get(node.id);
      if (existing) {
        Object.keys(node).forEach(function (key) { existing[key] = node[key]; });
        nodes.push(existing);
      } else {
        var fresh = Object.assign({}, node);
        nodes.push(fresh);
        nodeData.set(node.id, fresh);
      }
    });

    var byId = {};
    nodes.forEach(function (node) { byId[node.id] = node; });

    var links = [];
    filtered.links.forEach(function (link) {
      var source = byId[link.source];
      var target = byId[link.target];
      if (!source || !target) { return; }
      links.push({
        id: link.id,
        source: source,
        target: target,
        direction: link.direction,
        position: link.position,
        arity: link.arity,
        edge: link.edge
      });
    });

    // Seed fresh nodes next to a neighbour that already has a position.
    links.forEach(function (link) {
      var a = link.source;
      var b = link.target;
      seed(a, b);
      seed(b, a);
    });

    function seed(node, neighbour) {
      if (typeof node.x === "number") { return; }
      var angle = seededAngle(node.id);
      if (neighbour && typeof neighbour.x === "number") {
        node.x = neighbour.x + Math.cos(angle) * 55;
        node.y = neighbour.y + Math.sin(angle) * 55;
      } else {
        node.x = Math.cos(angle) * 130;
        node.y = Math.sin(angle) * 130;
      }
      node.vx = 0;
      node.vy = 0;
    }

    linkData = links;

    var link = linkLayer.selectAll("line.link-line").data(links, function (d) { return d.id; });
    link.exit().remove();
    link.enter().append("line").attr("class", "link-line").merge(link)
      .attr("class", function (d) {
        return "link-line" + (d.direction === "out" ? " out" : "");
      });

    var linkLabel = labelLayer.selectAll("text.link-label").data(
      links.filter(function (d) { return d.arity >= 3 || d.direction === "out"; }),
      function (d) { return d.id; }
    );
    linkLabel.exit().remove();
    linkLabel.enter().append("text").attr("class", "link-label")
      .merge(linkLabel)
      .text(function (d) { return d.direction === "out" ? "→" : String(d.position); });

    var node = nodeLayer.selectAll("g.node").data(nodes, function (d) { return d.id; });
    node.exit().remove();
    var nodeEnter = node.enter().append("g").attr("class", "node");
    nodeEnter.append("circle").attr("class", "node-shape").attr("r", 6);
    nodeEnter.append("path").attr("class", "node-diamond");
    nodeEnter.append("rect").attr("class", "node-arg");
    nodeEnter.append("text").attr("class", "node-label");

    var nodeAll = nodeEnter.merge(node);
    nodeAll.attr("class", function (d) { return "node kind-" + d.kind; });

    nodeAll.each(function (d) {
      shapeFor(d3.select(this), d);
    });

    nodeAll.select("text.node-label")
      .text(function (d) { return canvasLabel(d); })
      .attr("x", function (d) { return radiusOf(d) + 5; })
      .attr("y", 3)
      .attr("class", function (d) { return "node-label kind-" + d.kind; });

    nodeAll.selectAll("title").remove();
    nodeAll.append("title").text(function (d) { return d.term || d.label || d.id; });

    nodeAll
      .classed("dim", false)
      .classed("selected", function (d) { return d.id === selectedId; })
      .on("click", function (event, d) {
        event.stopPropagation();
        select(d.id);
      });

    var hyperedgeCount = nodes.filter(function (n) { return n.kind === "hyperedge"; }).length;
    var ruleCount = nodes.filter(function (n) { return n.kind === "rule"; }).length;
    var termCount = nodes.filter(function (n) { return n.kind === "term"; }).length;
    var nodeCount = nodes.filter(function (n) { return n.kind === "node"; }).length;
    // The arity mix describes hyperedges only: a rule's incoming links are its
    // premises, and mixing them in would read as graph arity.
    var arities = {};
    var premises = {};
    nodes.forEach(function (n) {
      var list = n.arguments || [];
      if (n.kind === "hyperedge") {
        arities[list.length] = (arities[list.length] || 0) + 1;
      } else if (n.kind === "rule") {
        premises[list.length] = (premises[list.length] || 0) + 1;
      }
    });
    var arityText = Object.keys(arities).sort(function (a, b) { return a - b; })
      .map(function (key) { return key + "-ary:" + arities[key]; }).join("  ");
    var premiseText = Object.keys(premises).sort(function (a, b) { return a - b; })
      .map(function (key) { return key + "-premise:" + premises[key]; }).join("  ");

    el.legendStats.innerHTML =
      "shown " + nodes.length + " of " + graph.nodes.length +
      "<br>nodes " + nodeCount + " · terms " + termCount +
      "<br>hyperedges " + hyperedgeCount + " · rules " + ruleCount +
      (arityText ? "<br>" + escapeHtml(arityText) : "") +
      (ruleCount && premiseText ? "<br>" + escapeHtml(premiseText) : "");

    el.matchText.textContent = query || kindFilter.length < 4
      ? filtered.count + " match" + (filtered.count === 1 ? "" : "es")
      : "";

    updateLabelVisibility();
    simulation.nodes(nodes);
    simulation.force("link").links(links);

    // Layout continuity. A fresh view (a session load, a reset) is allowed to
    // lay the graph out from scratch. An incremental delta must not: reheating
    // the simulation for every arriving event dragged settled nodes around by
    // tens of pixels and made the graph look like it was boiling. So an update
    // that adds nothing only re-binds the data, and one that adds a few elements
    // gets a short, low-energy nudge that lets the newcomers find a place.
    var added = nodes.length - previousNodeCount + links.length - previousLinkCount;
    var bigChange = Math.abs(nodes.length - previousNodeCount) > 40 || added < 0;
    previousNodeCount = nodes.length;
    previousLinkCount = links.length;
    if (withRestart || bigChange) {
      simulation.alpha(0.9).restart();
      window.setTimeout(fitView, 550);
    } else if (added > 0) {
      simulation.alpha(0.08).restart();
    }
    // added === 0: positions are already the ones on screen; leave them alone.
  }

  // A mark is drawn inside the zoomed group, so at fit-to-view on a real graph it
  // shrinks to a couple of pixels and a hyperedge stops looking like a hyperedge.
  // Keep the on-screen size above a floor, and let the shape grow at most three
  // times so a deep zoom-out does not turn the layout into one blob.
  var MARK_FLOOR = 3.6;
  function markRadius(d) {
    var base = radiusOf(d);
    var scale = currentScale > 0 ? currentScale : 1;
    if (base * scale >= MARK_FLOOR) { return base; }
    return Math.min(base * 3, MARK_FLOOR / scale);
  }

  function scaleMarks() {
    var zoom = currentScale || 1;
    var selectionWidth = Math.min(9, Math.max(1.6, 3.2 / zoom));
    nodeLayer.selectAll("g.node").each(function (d) {
      var r = markRadius(d);
      d3.select(this).select("circle.node-shape")
        .attr("r", r)
        .style("stroke-width", d.id === selectedId ? selectionWidth : null);
      d3.select(this).select("path.node-diamond")
        .attr("d", diamondPath(r + 1))
        .style("stroke-width", d.id === selectedId ? selectionWidth : null);
    });
    var stroke = Math.min(6, Math.max(0.6, 1.1 / zoom));
    linkLayer.selectAll("line.link-line").style("stroke-width", stroke);
  }

  function shapeFor(selection, d) {
    var kind = d.kind;
    var r = markRadius(d);
    selection.select("circle.node-shape")
      .style("display", kind === "node" || kind === "term" ? null : "none")
      .attr("r", r)
      .attr("class", "node-shape kind-" + kind + (d.id === selectedId ? " selected" : ""));
    selection.select("path.node-diamond")
      .style("display", kind === "hyperedge" || kind === "rule" ? null : "none")
      .attr("d", diamondPath(r + 1))
      .attr("class", "node-shape kind-" + kind + (d.id === selectedId ? " selected" : ""));
    selection.select("rect.node-arg")
      .style("display", "none");
  }

  // A rule label can be a 170-character premise/replacement chain. On the canvas
  // it is cut to a recognisable length; the full text stays in the details panel
  // and in the hover title, so nothing is lost, only shortened.
  var LABEL_LIMIT = 30;
  function canvasLabel(d) {
    var text = d.label || d.id || "";
    var limit = d.kind === "rule" ? 34 : d.kind === "hyperedge" ? 26 : LABEL_LIMIT;
    return text.length > limit ? text.slice(0, limit - 1) + "\u2026" : text;
  }

  function diamondPath(r) {
    return "M0," + (-r) + " L" + r + ",0 L0," + r + " L" + (-r) + ",0 Z";
  }

  var labelPass = 0;
  function ticked() {
    linkLayer.selectAll("line.link-line")
      .attr("x1", function (d) { return d.source.x; })
      .attr("y1", function (d) { return d.source.y; })
      .attr("x2", function (d) { return d.target.x; })
      .attr("y2", function (d) { return d.target.y; });
    labelLayer.selectAll("text.link-label")
      .attr("x", function (d) { return d.source.x + (d.target.x - d.source.x) * 0.62; })
      .attr("y", function (d) { return d.source.y + (d.target.y - d.source.y) * 0.62; });
    nodeLayer.selectAll("g.node")
      .attr("transform", function (d) { return "translate(" + d.x + "," + d.y + ")"; });
    // While the simulation is warm the nodes move under their labels, so the
    // boxes have to be solved again or two labels can drift into each other.
    // Once it is cold, positions stop changing and a single pass is enough.
    labelPass = (labelPass + 1) % 2;
    if (simulation.alpha() > 0.01 || labelPass === 0) {
      placeLabels();
    }
  }

  // Greedy label placement: walk the visible nodes in priority order and keep a
  // label only when its box does not hit one already kept. Without this, a pack
  // of long rule labels piles up into an unreadable smear in the middle of the
  // canvas. Boxes are estimated from the text length and the current font size,
  // which is enough at these sizes and costs nothing per frame.
  var lastPlacement = { boxes: [], marks: [], placed: 0, dropped: 0 };

  function placeLabels() {
    var keep = [];
    // Obstacles that labels must avoid: link labels and every mark.
    var boxes = [];
    var marks = [];
    // Boxes this pass accepted for node labels.
    var labelBoxes = [];
    var candidates = [];
    labelLayer.selectAll("text.link-label").each(function (d) {
      if (!d || d3.select(this).classed("hidden")) { return; }
      var node = this;
      var text = node.textContent || "";
      if (!text) { return; }
      var size = parseFloat(node.style.fontSize || "9") || 9;
      var x = Number(node.getAttribute("x"));
      var y = Number(node.getAttribute("y"));
      if (!isFinite(x) || !isFinite(y)) { return; }
      boxes.push([x - 2, y - size, x + text.length * size * 0.6 + 2, y + 2]);
    });
    // Marks are obstacles too: a label laid across a neighbouring diamond hides
    // the very distinction the shapes are meant to carry.
    nodeLayer.selectAll("g.node").each(function (d) {
      if (!d || typeof d.x !== "number") { return; }
      var r = markRadius(d) + 2;
      boxes.push([d.x - r, d.y - r, d.x + r, d.y + r]);
      marks.push([d.x - r, d.y - r, d.x + r, d.y + r]);
    });
    nodeLayer.selectAll("g.node").each(function (d) {
      if (!d || typeof d.x !== "number" || typeof d.y !== "number") { return; }
      var text = canvasLabel(d);
      if (!text) { return; }
      candidates.push({
        node: this,
        d: d,
        text: text,
        priority: d.id === selectedId ? 0 : d.kind === "node" ? 1 : d.kind === "hyperedge" ? 2 : d.kind === "rule" ? 3 : 4
      });
    });
    candidates.sort(function (a, b) {
      return a.priority - b.priority || String(a.d.id).localeCompare(String(b.d.id));
    });
    var fontSize = Math.max(5, Math.min(22, 11 / currentScale));
    // Measure the text where the engine can, so a box is the box that is drawn;
    // a DOM without text metrics (jsdom) falls back to a per-character estimate.
    candidates.forEach(function (candidate) {
      var node = d3.select(candidate.node).select("text.node-label").node();
      var measured = 0;
      if (node && typeof node.getComputedTextLength === "function") {
        try { measured = node.getComputedTextLength(); } catch (error) { measured = 0; }
      }
      // 2px of slack on top of the glyph run: a browser's measured width can
      // differ slightly from the character estimate used by a DOM without text
      // metrics, and two boxes that merely touch still look like a collision.
      candidate.width = measured > 0 ? measured + 8 : candidate.text.length * fontSize * 0.62 + 8;
      candidate.height = measured > 0 ? fontSize + 4 : fontSize + 3;
    });
    var dropped = 0;
    var taken = function (box) {
      return boxes.some(function (other) {
        return !(box[2] < other[0] || box[0] > other[2] || box[3] < other[1] || box[1] > other[3]);
      });
    };
    candidates.forEach(function (candidate) {
      var d = candidate.d;
      var width = candidate.width;
      var height = candidate.height;
      var r = markRadius(d);
      // Right of the mark first (the usual reading position), then below it,
      // then to its left. A label is dropped only when all three are taken, so
      // a dense cluster keeps more names visible than a single-position rule.
      var places = [
        [d.x + r + 5, d.y - height / 2],
        [d.x + r + 5, d.y + r + 1],
        [d.x - r - 5 - width, d.y - height / 2]
      ];
      var label = d3.select(candidate.node).select("text.node-label");
      for (var i = 0; i < places.length; i += 1) {
        var x = places[i][0];
        var y = places[i][1];
        var box = [x, y, x + width, y + height];
        if (taken(box)) { continue; }
        boxes.push(box);
        labelBoxes.push(box);
        keep.push(candidate.d.id);
        label.attr("x", x - d.x).attr("y", y - d.y + height / 2 - 1).classed("hidden", false);
        return;
      }
      label.classed("hidden", true);
      dropped += 1;
    });
    // Kept for the inspection tests: the boxes this pass decided on, so a
    // regression can assert against the placement the page made
    // instead of re-deriving baseline arithmetic from attributes.
    lastPlacement = { boxes: labelBoxes, marks: marks, placed: keep.length, dropped: dropped };
    return keep.length;
  }

  function updateLabelVisibility() {
    var showNodes = currentScale >= 0.5;
    var showTerms = currentScale >= 0.85;
    // Labels live inside the zoomed group, so their size is divided by the zoom
    // to keep them legible on screen instead of growing into blobs.
    var nodeSize = Math.max(5, Math.min(22, 11 / currentScale));
    var linkSize = Math.max(4, Math.min(18, 9 / currentScale));
    nodeLayer.selectAll("text.node-label")
      .classed("hidden", function (d) {
        if (d.kind === "node") { return !showNodes; }
        if (d.kind === "term") { return !showTerms; }
        return false;
      })
      .style("font-size", nodeSize + "px");
    scaleMarks();
    placeLabels();
    labelLayer.selectAll("text.link-label")
      .classed("hidden", currentScale < 0.7)
      .style("font-size", linkSize + "px");
  }

  // ------------------------------------------------------------------ view
  function boundsOf(nodes) {
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(function (node) {
      if (typeof node.x !== "number" || !isFinite(node.x)) { return; }
      minX = Math.min(minX, node.x);
      minY = Math.min(minY, node.y);
      maxX = Math.max(maxX, node.x);
      maxY = Math.max(maxY, node.y);
    });
    if (!isFinite(minX)) { return null; }
    return { x: minX, y: minY, dx: Math.max(maxX - minX, 60), dy: Math.max(maxY - minY, 60) };
  }

  // Space the floating legend occupies, so the graph is fitted beside it rather
  // than under it. Zero when there is no layout (tests, headless DOM).
  function legendInset() {
    var box = el.legend ? el.legend.getBoundingClientRect() : null;
    if (!box || !box.height) { return 0; }
    return box.height + 22;
  }

  function fitView() {
    var nodes = Array.from(nodeData.values());
    var bounds = boundsOf(nodes);
    var width = el.svg.clientWidth || 800;
    var height = el.svg.clientHeight || 600;
    if (!bounds) {
      svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity);
      return;
    }
    var pad = 70;
    var usable = Math.max(height - legendInset(), 200);
    var scale = Math.min(2.4, 0.92 * Math.min(width / (bounds.dx + pad * 2), usable / (bounds.dy + pad * 2)));
    var tx = width / 2 - scale * (bounds.x + bounds.dx / 2);
    var ty = usable / 2 - scale * (bounds.y + bounds.dy / 2);
    svg.transition().duration(320).call(
      zoom.transform,
      d3.zoomIdentity.translate(tx, ty).scale(scale)
    );
  }

  function resetView() {
    nodeData.forEach(function (node) {
      delete node.x; delete node.y; delete node.vx; delete node.vy;
    });
    simulation.alpha(1).restart();
    window.setTimeout(fitView, 900);
  }

  // ------------------------------------------------------------- selection
  function select(id) {
    selectedId = id;
    nodeLayer.selectAll("g.node")
      .classed("selected", function (d) { return d.id === id; })
      .each(function (d) { shapeFor(d3.select(this), d); });
    renderDetails(id);
  }

  function shorten(text, limit) {
    var value = String(text == null ? "" : text);
    if (value.length <= limit) { return value; }
    return value.slice(0, limit - 1) + "\u2026 (" + value.length + " characters)";
  }

  function detailRow(label, value) {
    var text = String(value == null ? "" : value);
    var shown = shorten(text, 90);
    var title = text.length > 90 ? " class=\"mono clamp\" title=\"" + escapeHtml(text) + "\"" : " class=\"mono\"";
    return "<tr><th>" + escapeHtml(label) + "</th><td" + title + ">" +
      escapeHtml(shown) + "</td></tr>";
  }

  function renderDetails(id) {
    var state = activeState();
    var item = state.nodes[id] || state.edges[id];
    var node = modelById[id];

    if (!node) {
      el.details.innerHTML = "<p class=\"muted\">Nothing selected.</p>";
      return;
    }

    var rows = [
      detailRow("id", node.id),
      detailRow("kind", node.kind),
      detailRow("label", node.label),
      detailRow("term", node.term)
    ];
    if (node.constructorText) { rows.push(detailRow("constructor", node.constructorText)); }
    if (node.source) { rows.push(detailRow("provenance", node.source)); }
    if (item && item.declared != null) { rows.push(detailRow("declared node", String(item.declared))); }
    if (item && item._seq != null) { rows.push(detailRow("first seen at seq", String(item._seq))); }
    if (item && item._t != null) {
      rows.push(detailRow("first seen at", new Date(item._t * 1000).toISOString()));
    }
    if (node.kind === "hyperedge" || node.kind === "rule") {
      rows.push(detailRow("relation", node.relation || ""));
      rows.push(detailRow("arity", String(node.arity || 0)));
    }

    // A rule label is a full premise/replacement chain and a term can be longer
    // still. The panel shows a readable head with the whole value on click, so a
    // complex element cannot stretch the sidebar to nothing.
    var heading = shorten(node.label, 120);
    var html = "<h3 title=\"" + escapeHtml(node.term || node.label) + "\">" + escapeHtml(heading) +
      "</h3><table class=\"detail-table\">" + rows.join("") + "</table>";

    if (node.kind === "hyperedge" || node.kind === "rule") {
      var args = node.arguments || [];
      html += "<h3 style=\"margin-top:10px\">Arguments (in order)</h3><div class=\"incidence-list\">";
      if (!args.length) { html += "<div class=\"incidence-item muted\">nullary edge</div>"; }
      args.forEach(function (argId, index) {
        var arg = state.nodes[argId] || modelById[argId] || { label: argId };
        html += "<div class=\"incidence-item\">" + (index + 1) + ". " +
          escapeHtml(shorten(arg.label || argId, 120)) + "</div>";
      });
      html += "</div>";
      var results = node.results || [];
      if (results.length) {
        html += "<h3 style=\"margin-top:10px\">Results</h3><div class=\"incidence-list\">";
        results.forEach(function (resultId) {
          var result = state.nodes[resultId] || modelById[resultId] || { label: resultId };
          html += "<div class=\"incidence-item\">→ " + escapeHtml(result.label || resultId) + "</div>";
        });
        html += "</div>";
      }
    } else {
      var incident = linkData.filter(function (link) {
        var otherId = link.source.id === node.id ? link.target.id : link.source.id;
        return link.source.id === node.id || link.target.id === node.id ? otherId : null;
      });
      html += "<h3 style=\"margin-top:10px\">Incident hyperedges</h3><div class=\"incidence-list\">";
      if (!incident.length) {
        html += "<div class=\"incidence-item muted\">isolated: no hyperedge mentions this vertex</div>";
      }
      incident.forEach(function (link) {
        var other = link.source.id === node.id ? link.target : link.source;
        html += "<div class=\"incidence-item\">" +
          (link.direction === "out" ? "result of " : "argument " + link.position + " of ") +
          escapeHtml(other.label) + "</div>";
      });
      html += "</div>";
    }
    html += "<div class=\"detail-actions\"><button type=\"button\" id=\"focusSelected\">Focus in graph</button>" +
      "</div>";
    el.details.innerHTML = html;
    var focusButton = document.getElementById("focusSelected");
    if (focusButton) {
      focusButton.addEventListener("click", function () { centerOn(id, true); });
    }
  }

  // ------------------------------------------------------------- live data
  function seedLiveFromState(payload) {
    live = V.createState();
    if (payload.nodes && payload.nodes.length) {
      V.applyEvent(live, { type: "nodes.added", items: payload.nodes });
    }
    if (payload.edges && payload.edges.length) {
      V.applyEvent(live, { type: "edges.added", items: payload.edges });
    }
    if (payload.summary) {
      live.counts = payload.summary.counts || {};
      live.machine = payload.summary.machine || {};
      live.source = payload.summary.source || {};
      live.startedAt = payload.summary.started_at || null;
      live.stopped = payload.summary.stopped || null;
    }
  }

  function connectLive() {
    if (stream) { stream.close(); stream = null; }
    var from = live.lastSeq >= 0 ? live.lastSeq : 0;
    stream = new EventSource("/api/events?from=" + from);
    stream.onopen = function () { setBadge("live", true); };
    stream.onerror = function () { setBadge("offline", false); };
    stream.onmessage = function (message) {
      var event;
      try { event = JSON.parse(message.data); } catch (error) { return; }
      if (!event || !V.EVENT_TYPES[event.type]) { return; }
      V.applyEvent(live, event);
      if (mode === "live") {
        hideBanner();
        scheduleRender(false);
        if (selectedId) { renderDetails(selectedId); }
      }
    };
  }

  function setBadge(text, connected) {
    el.badge.textContent = text;
    el.badge.className = "badge " + (text === "live" ? "badge-live" : text === "replay" ? "badge-replay" : "badge-offline");
    if (!connected) { el.badge.className = "badge badge-offline"; }
  }

  function showBanner(title, bodyHtml) {
    el.banner.hidden = false;
    el.banner.innerHTML = "<h3>" + escapeHtml(title) + "</h3>" + bodyHtml;
  }
  function hideBanner() { el.banner.hidden = true; }

  // ------------------------------------------------------------- recording
  function postJson(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {})
    }).then(function (response) { return response.json(); });
  }

  function toggleRecording() {
    if (!recording) {
      postJson("/api/recording/start", { name: el.sessionName.value || null })
        .then(function (result) {
          if (result.error) { el.recordStatus.textContent = result.error; return; }
          recording = true;
          el.recordButton.classList.add("armed");
          el.recordButton.textContent = "■ Stop";
          el.recordStatus.textContent = "recording “" + result.id + "”";
        })
        .catch(function (error) { el.recordStatus.textContent = "start failed: " + error; });
      return;
    }
    postJson("/api/recording/stop", {})
      .then(function (result) {
        recording = false;
        el.recordButton.classList.remove("armed");
        el.recordButton.textContent = "● Record";
        if (result.error) { el.recordStatus.textContent = result.error; return; }
        el.recordStatus.textContent = "saved “" + result.id + "” · " + result.events + " events";
        loadSessions();
      })
      .catch(function (error) { el.recordStatus.textContent = "stop failed: " + error; });
  }

  function loadSessions() {
    fetch("/api/sessions")
      .then(function (response) { return response.json(); })
      .then(function (payload) { renderSessions(payload.sessions || []); })
      .catch(function (error) {
        el.sessionList.innerHTML = "<p class=\"muted\">could not list sessions: " +
          escapeHtml(String(error)) + "</p>";
      });
  }

  function renderSessions(sessions) {
    if (!sessions.length) {
      el.sessionList.innerHTML = "<p class=\"muted\">No recordings yet. Press record while a Machine script runs.</p>";
      return;
    }
    el.sessionList.innerHTML = "";
    sessions.forEach(function (session) {
      var meta = session.meta || {};
      var card = document.createElement("article");
      card.className = "session-card";
      var duration = meta.duration != null ? meta.duration.toFixed(1) + "s" : "—";
      card.innerHTML =
        "<h3>" + escapeHtml(meta.name || session.id) + "</h3>" +
        "<div class=\"row\">" + session.events + " events · " + duration + " · " +
        Math.round(session.bytes / 1024) + " kB</div>" +
        "<div class=\"row\">" + escapeHtml(meta.recorded_at_text || "") + "</div>" +
        "<div class=\"row\">start: " + ((meta.state_at_start && meta.state_at_start.nodes) || 0) +
        " nodes · final: " + ((meta.final_state && meta.final_state.nodes) || 0) + " nodes</div>";
      var actions = document.createElement("div");
      actions.className = "actions";
      var load = document.createElement("button");
      load.type = "button";
      load.textContent = "Replay";
      load.addEventListener("click", function () { loadSession(session.id); });
      var download = document.createElement("button");
      download.type = "button";
      download.textContent = "Download";
      download.addEventListener("click", function () {
        window.open("/api/sessions/" + encodeURIComponent(session.id), "_blank");
      });
      var remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "Delete";
      remove.addEventListener("click", function () {
        fetch("/api/sessions/" + encodeURIComponent(session.id), { method: "DELETE" })
          .then(loadSessions);
      });
      actions.appendChild(load);
      actions.appendChild(download);
      actions.appendChild(remove);
      card.appendChild(actions);
      el.sessionList.appendChild(card);
    });
  }

  // ---------------------------------------------------------------- replay
  function loadSession(id) {
    fetch("/api/sessions/" + encodeURIComponent(id))
      .then(function (response) { return response.json(); })
      .then(function (document) {
        replay.id = id;
        replay.meta = document.meta || {};
        replay.events = document.events || [];
        replay.state = V.createState();
        replay.index = replay.events.length;
        V.applyUntil(replay.state, replay.events, replay.index);
        mode = "replay";
        setBadge("replay", true);
        el.timeline.hidden = false;
        el.seekSlider.max = String(replay.events.length);
        el.seekSlider.value = String(replay.index);
        el.replayTitle.textContent = (replay.meta.name || id) + " · " +
          replay.events.length + " events";
        el.sourceText.textContent = "replaying " + (replay.meta.recorded_at_text || id);
        nodeData.clear();
        selectedId = null;
        el.details.innerHTML = "<p class=\"muted\">Select a node or a hyperedge in the graph.</p>";
        selectTab("details");
        scheduleRender(true);
        updateTimeline();
      })
      .catch(function (error) {
        el.sessionList.innerHTML = "<p class=\"muted\">could not load session: " +
          escapeHtml(String(error)) + "</p>";
      });
  }

  function seek(index) {
    if (mode !== "replay" || !replay.events.length) { return; }
    var target = Math.max(0, Math.min(index, replay.events.length));
    replay.index = target;
    if (target >= replay.state.applied) {
      V.applyUntil(replay.state, replay.events, target);
      scheduleRender(false);
    } else {
      replay.state = V.rebuild(replay.events, target);
      scheduleRender(false);
    }
    updateTimeline();
  }

  function updateTimeline() {
    el.seekSlider.value = String(replay.index);
    var events = replay.events;
    var current = events[replay.index - 1];
    var first = events[0];
    var span = first && current && first.t != null && current.t != null
      ? (current.t - first.t).toFixed(2) + "s"
      : "—";
    el.timeText.textContent = replay.index + " / " + events.length + " · " + span;
    el.playButton.textContent = playing ? "❚❚" : "▶";
  }

  function play() {
    if (mode !== "replay") { return; }
    if (replay.index >= replay.events.length) { seek(0); }
    playing = true;
    updateTimeline();
    step();
  }

  function pause() {
    playing = false;
    if (playTimer) { window.clearTimeout(playTimer); playTimer = null; }
    updateTimeline();
  }

  function step() {
    if (!playing) { return; }
    if (replay.index >= replay.events.length) { pause(); return; }
    var index = replay.index;
    var events = replay.events;
    var gap = 120;
    if (index + 1 < events.length && events[index].t != null && events[index + 1].t != null) {
      gap = (events[index + 1].t - events[index].t) * 1000 / speed;
    }
    gap = Math.max(12, Math.min(1500, gap));
    seek(index + 1);
    playTimer = window.setTimeout(step, gap);
  }

  // ---------------------------------------------------------------- status
  function pollStatus() {
    fetch("/api/status")
      .then(function (response) { return response.json(); })
      .then(function (status) {
        var journal = status.journal || {};
        var state = journal.state || {};
        var machine = state.machine || {};

        if (mode === "live") {
          el.sourceText.textContent =
            "journal " + (journal.journal_exists ? journal.events_seen + " events" : "not found") +
            (machine.pid ? " · machine pid " + machine.pid : "") +
            (state.stopped ? " · " + state.stopped : "");
        }

        if (!journal.journal_exists && mode === "live") {
          showBanner(
            "Waiting for an observed Machine run",
            "<div>The visualiser is passive: it reads a journal the Machine writes.</div>" +
            "<pre>python -m cat_theo_machine.visualiser.examples.machine_workload --delay 0.6</pre>" +
            "<div class=\"muted small\">journal: " + escapeHtml(journal.journal) + "</div>"
          );
        }

        recording = !!(status.recording && status.recording.active);
        el.recordButton.classList.toggle("armed", recording);
        el.recordButton.textContent = recording ? "■ Stop" : "● Record";
        if (recording) {
          el.recordStatus.textContent = "recording “" + status.recording.id + "” · " +
            status.recording.events + " events";
        }

        el.statusBody.innerHTML =
          block("server", [
            ["watching", journal.journal],
            ["journal exists", String(journal.journal_exists)],
            ["journal bytes", String(journal.journal_bytes)],
            ["events seen", String(journal.events_seen)],
            ["sessions dir", status.sessions_dir]
          ]) +
          block("observed machine", [
            ["pid", String(machine.pid == null ? "—" : machine.pid)],
            ["python", String(machine.python || "—")],
            ["argv", (machine.argv || []).join(" ")],
            ["cwd", String(machine.cwd || "—")],
            ["started", state.started_at ? new Date(state.started_at * 1000).toISOString() : "—"],
            ["stopped", state.stopped || "running / unknown"]
          ]) +
          block("model", [
            ["nodes in state", String(state.nodes)],
            ["hyperedges in state", String(state.edges)],
            ["events applied", String((mode === "live" ? live : replay.state).applied)],
            ["mode", mode]
          ]);
      })
      .catch(function () { /* status is best-effort */ });
  }

  function block(title, pairs) {
    var rows = pairs.map(function (pair) {
      return "<div class=\"kv\"><span>" + escapeHtml(pair[0]) + "</span><span>" +
        escapeHtml(clipboardLink(pair[1])) + "</span></div>";
    }).join("");
    return "<div class=\"status-block\"><h3>" + escapeHtml(title) + "</h3>" + rows + "</div>";
  }

  // ------------------------------------------------------------------- UI
  function selectTab(name) {
    document.querySelectorAll(".tab").forEach(function (tab) {
      tab.classList.toggle("active", tab.dataset.tab === name);
    });
    document.querySelectorAll(".tab-panel").forEach(function (panel) {
      panel.classList.toggle("active", panel.dataset.panel === name);
    });
  }

  function exportState() {
    var state = activeState();
    var document_ = V.toExport(state, {
      mode: mode,
      session: mode === "replay" ? replay.id : null,
      journal: el.sourceText.textContent
    });
    download(JSON.stringify(document_, null, 2), "hypergraph-state.json", "application/json");
  }

  // The exported file has to carry the stylesheet, or every mark falls back to
  // the SVG default of black on black. Reading cssRules works only for sheets the
  // browser parses, so the same-origin stylesheet is fetched as text and cached.
  var styleText = null;
  function stylesheetText() {
    if (styleText !== null) { return Promise.resolve(styleText); }
    var sheet = document.querySelector('link[rel="stylesheet"]');
    if (!sheet) { return Promise.resolve(""); }
    return fetch(sheet.href, { cache: "force-cache" })
      .then(function (response) { return response.ok ? response.text() : ""; })
      .then(function (text) { styleText = text; return text; })
      .catch(function () { return ""; });
  }

  function exportSvg() {
    return stylesheetText().then(function (css) {
      var clone = el.svg.cloneNode(true);
      clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
      clone.setAttribute("width", String(el.svg.clientWidth || 1200));
      clone.setAttribute("height", String(el.svg.clientHeight || 800));
      // A background, so the export is not white-on-white in a viewer that has
      // no page behind it.
      var backdrop = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      backdrop.setAttribute("x", "0");
      backdrop.setAttribute("y", "0");
      backdrop.setAttribute("width", "100%");
      backdrop.setAttribute("height", "100%");
      backdrop.setAttribute("fill", "#0b0f14");
      // SVG namespace: an HTML-namespaced <style> inside an SVG document is
      // ignored by strict readers, which is exactly how an export loses its
      // colours.
      var style = document.createElementNS("http://www.w3.org/2000/svg", "style");
      style.textContent = css;
      clone.insertBefore(backdrop, clone.firstChild);
      clone.insertBefore(style, clone.firstChild);
      download(new XMLSerializer().serializeToString(clone), "hypergraph-view.svg", "image/svg+xml");
    });
  }

  function download(text, filename, mime) {
    var blob = new Blob([text], { type: mime });
    var url = URL.createObjectURL(blob);
    var anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }

  function applySearch() {
    query = el.search.value.trim();
    scheduleRender(false);
  }

  // --------------------------------------------------------------- events
  document.getElementById("fitButton").addEventListener("click", fitView);
  document.getElementById("resetButton").addEventListener("click", resetView);
  document.getElementById("zoomInButton").addEventListener("click", function () {
    svg.transition().duration(180).call(zoom.scaleBy, 1.35);
  });
  document.getElementById("zoomOutButton").addEventListener("click", function () {
    svg.transition().duration(180).call(zoom.scaleBy, 1 / 1.35);
  });
  el.recordButton.addEventListener("click", toggleRecording);
  document.getElementById("refreshSessions").addEventListener("click", loadSessions);
  document.getElementById("exportStateButton").addEventListener("click", exportState);
  document.getElementById("exportSvgButton").addEventListener("click", exportSvg);
  el.search.addEventListener("input", applySearch);
  el.search.addEventListener("keydown", function (event) {
    if (event.key !== "Enter") { return; }
    var graph = activeGraph();
    var filtered = V.filterModel(graph, query, kindFilter);
    if (filtered.nodes.length) {
      select(filtered.nodes[0].id);
      centerOn(filtered.nodes[0].id);
    }
  });

  document.querySelectorAll(".kindFilter").forEach(function (box) {
    box.addEventListener("change", function () {
      kindFilter = Array.prototype.filter
        .call(document.querySelectorAll(".kindFilter"), function (input) { return input.checked; })
        .map(function (input) { return input.value; });
      scheduleRender(false);
    });
  });

  document.querySelectorAll(".tab").forEach(function (tab) {
    tab.addEventListener("click", function () { selectTab(tab.dataset.tab); });
  });

  document.getElementById("liveButton").addEventListener("click", function () {
    pause();
    mode = "live";
    setBadge("live", true);
    el.timeline.hidden = true;
    replay.state = null;
    nodeData.clear();
    fetch("/api/state")
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        seedLiveFromState(payload);
        scheduleRender(true);
        connectLive();
      });
  });

  el.playButton.addEventListener("click", function () {
    if (playing) { pause(); } else { play(); }
  });
  document.getElementById("stepForwardButton").addEventListener("click", function () {
    pause();
    seek(replay.index + 1);
  });
  document.getElementById("stepBackButton").addEventListener("click", function () {
    pause();
    seek(replay.index - 1);
  });
  el.seekSlider.addEventListener("input", function () {
    var target = Number(el.seekSlider.value); // read before pause() repaints the slider
    pause();
    seek(target);
  });
  el.speedSelect.addEventListener("change", function () {
    speed = Number(el.speedSelect.value) || 1;
  });

  document.addEventListener("keydown", function (event) {
    if (event.target && /input|select|textarea/i.test(event.target.tagName)) { return; }
    if (event.key === "f" || event.key === "F") { fitView(); }
    if (event.key === "r" || event.key === "R") { resetView(); }
    if (event.key === "+" || event.key === "=") { svg.transition().duration(150).call(zoom.scaleBy, 1.3); }
    if (event.key === "-") { svg.transition().duration(150).call(zoom.scaleBy, 1 / 1.3); }
    if (mode === "replay" && event.key === " ") {
      event.preventDefault();
      if (playing) { pause(); } else { play(); }
    }
    if (mode === "replay" && event.key === "ArrowRight") { pause(); seek(replay.index + 1); }
    if (mode === "replay" && event.key === "ArrowLeft") { pause(); seek(replay.index - 1); }
  });

  // Bring one element into view. `zoomIn` is used by the details panel's "focus"
  // action, where the point of the move is to read a single hyperedge's argument
  // links; search keeps the current scale so the surrounding context stays put.
  function centerOn(id, zoomIn) {
    var node = nodeData.get(id);
    if (!node || typeof node.x !== "number") { return; }
    var width = el.svg.clientWidth || 800;
    var height = el.svg.clientHeight || 600;
    var scale = zoomIn ? 1.6 : Math.max(0.6, Math.min(2, currentScale));
    svg.transition().duration(300).call(
      zoom.transform,
      d3.zoomIdentity.translate(width / 2 - node.x * scale, height / 2 - node.y * scale).scale(scale)
    );
  }

  // ----------------------------------------------------------------- boot
  function boot() {
    selectTab("details");
    loadSessions();
    fetch("/api/state")
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        seedLiveFromState(payload);
        scheduleRender(true);
      })
      .catch(function () { scheduleRender(true); });
    connectLive();
    pollStatus();
    window.setInterval(pollStatus, 2500);
    window.addEventListener("resize", function () {
      if (!pendingRender) { scheduleRender(false); }
    });
    window.machineObserver = {
      model: V,
      state: function () { return activeState(); },
      graph: activeGraph,
      mode: function () { return mode; },
      render: renderGraph,
      fit: fitView,
      centerOn: centerOn,
      alpha: function () { return simulation.alpha(); },
      placement: function () { return lastPlacement; },
      focus: function (id) { centerOn(id, true); },
      select: select,
      seek: seek,
      loadSession: loadSession,
      stats: function () { return V.stats(activeState()); }
    };
  }

  boot();
})();
