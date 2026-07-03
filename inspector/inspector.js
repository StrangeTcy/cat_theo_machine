(function () {
  const graphStatus = document.getElementById("graphStatus");
  const selectionDetail = document.getElementById("selectionDetail");
  const packetList = document.getElementById("packetList");
  const workerList = document.getElementById("workerList");
  const comparisonList = document.getElementById("comparisonList");
  const derivationList = document.getElementById("derivationList");
  const packetCount = document.getElementById("packetCount");
  const workerCount = document.getElementById("workerCount");
  const derivationCount = document.getElementById("derivationCount");
  const countsText = document.getElementById("countsText");
  const sourceText = document.getElementById("sourceText");
  const summaryText = document.getElementById("summaryText");
  const maxRuleEdgesInput = document.getElementById("maxRuleEdges");
  const refreshButton = document.getElementById("refreshButton");
  const autoRefresh = document.getElementById("autoRefresh");

  let cy = null;
  let refreshHandle = null;

  function renderEmpty(container, text) {
    container.innerHTML = "";
    const div = document.createElement("div");
    div.className = "empty";
    div.textContent = text;
    container.appendChild(div);
  }

  function prettyJson(value) {
    return JSON.stringify(value, null, 2);
  }

  function setSelection(value) {
    selectionDetail.textContent = prettyJson(value);
  }

  function card(title, lines) {
    const el = document.createElement("article");
    el.className = "card";
    const heading = document.createElement("h3");
    heading.textContent = title;
    el.appendChild(heading);
    lines.forEach((line) => {
      const row = document.createElement("div");
      row.className = "line";
      row.textContent = line;
      el.appendChild(row);
    });
    return el;
  }

  function renderPackets(items) {
    packetCount.textContent = String(items.length);
    if (!items.length) {
      renderEmpty(packetList, "No packet view available.");
      return;
    }
    packetList.innerHTML = "";
    items.forEach((item) => {
      packetList.appendChild(
        card(item.mode + " • " + item.source, [
          item.kind,
          "current: " + item.current,
          "next: " + (item.next_action || "none"),
          "prefix: " + item.prefix,
          "target: " + (item.target_term || "none"),
        ])
      );
    });
  }

  function renderWorkers(items) {
    workerCount.textContent = String(items.length);
    if (!items.length) {
      renderEmpty(workerList, "No live workers.");
      return;
    }
    workerList.innerHTML = "";
    items.forEach((item) => {
      workerList.appendChild(
        card(item.mode + " • slot " + item.slot, [
          "pid: " + item.pid,
          "alive: " + String(item.alive),
          "packet: " + item.packet.current,
          "next: " + (item.packet.next_action || "none"),
        ])
      );
    });
  }

  function renderComparisons(view) {
    comparisonList.innerHTML = "";
    const live = view.live;
    if (live) {
      comparisonList.appendChild(
        card("Live Comparison", [
          "source goal: " + live.goal,
          "active workers: " + live.active_workers,
          "idle executors: " + live.idle_executors,
          "states: " + live.states.length,
        ])
      );
      live.states.forEach((state) => {
        comparisonList.appendChild(
          card(state.mode + " • " + state.status, [
            "phase: " + state.phase,
            "active: " + state.active_packets,
            "pending: " + state.pending_packets,
            "completed: " + state.completed_packets,
            "expanded: " + state.expanded,
            "generated: " + state.generated,
            "frontier peak: " + state.frontier_peak,
          ])
        );
      });
    }

    if (view.paused.length) {
      view.paused.forEach((paused) => {
        comparisonList.appendChild(
          card("Paused " + paused.id, [
            "signature: " + paused.signature,
            "goal: " + paused.goal,
            "outcome: " + paused.outcome,
            "states: " + paused.states.length,
          ])
        );
      });
    }

    if (view.completed.length) {
      view.completed.forEach((completed) => {
        comparisonList.appendChild(
          card("Completed " + completed.id, [
            "signature: " + completed.signature,
            "outcome: " + completed.outcome,
            "attempts: " + completed.attempt_count,
            "best mode: " + (completed.best_mode || "none"),
            "best status: " + (completed.best_status || "none"),
          ])
        );
      });
    }

    if (!live && !view.paused.length && !view.completed.length) {
      renderEmpty(comparisonList, "No comparison state available.");
    }
  }

  function renderDerivations(items) {
    derivationCount.textContent = String(items.length);
    if (!items.length) {
      renderEmpty(derivationList, "No derivation fragments.");
      return;
    }
    derivationList.innerHTML = "";
    items.forEach((item) => {
      const lines = [
        "start: " + item.start,
        "end: " + item.end,
        "steps: " + item.step_count,
        "cost: " + item.cost.value,
      ];
      item.preview_steps.forEach((step) => {
        lines.push(step.index + ". " + step.action);
      });
      derivationList.appendChild(card(item.id, lines));
    });
  }

  function renderGraph(cytoscapeView) {
    const elements = []
      .concat(cytoscapeView.elements.nodes || [])
      .concat(cytoscapeView.elements.edges || []);

    countsText.textContent =
      "nodes " +
      cytoscapeView.counts.cy_nodes +
      " • edges " +
      cytoscapeView.counts.cy_edges +
      " • visible rules " +
      cytoscapeView.counts.visible_rule_edges +
      "/" +
      cytoscapeView.counts.rule_edges;

    if (!window.cytoscape) {
      graphStatus.textContent = "Cytoscape failed to load. The page needs network access to fetch the library.";
      return;
    }

    graphStatus.style.display = "none";

    if (cy) {
      cy.destroy();
    }

    cy = window.cytoscape({
      container: document.getElementById("graph"),
      elements,
      layout: {
        name: "cose",
        animate: false,
        fit: true,
        padding: 30,
      },
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#c88a58",
            label: "data(label)",
            color: "#2a1f17",
            "font-size": 10,
            "text-wrap": "wrap",
            "text-max-width": 140,
            "text-valign": "center",
            "text-halign": "center",
            width: "label",
            height: "label",
            padding: "14px",
            shape: "round-rectangle",
            "border-width": 1,
            "border-color": "#8e4b2a",
          },
        },
        {
          selector: 'node[kind = "term"]',
          style: {
            "background-color": "#f2e2d5",
          },
        },
        {
          selector: 'node[kind = "rule_hyperedge"], node[kind = "graph_hyperedge"]',
          style: {
            shape: "diamond",
            "background-color": "#8e4b2a",
            color: "#fff8f0",
            "border-color": "#5d2a13",
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.6,
            "line-color": "#9c8a78",
            "target-arrow-shape": "triangle",
            "target-arrow-color": "#9c8a78",
            "curve-style": "bezier",
          },
        },
        {
          selector: 'edge[kind *= "incidence_in"]',
          style: {
            "line-style": "dashed",
          },
        },
        {
          selector: ":selected",
          style: {
            "background-color": "#d24c2a",
            "line-color": "#d24c2a",
            "target-arrow-color": "#d24c2a",
          },
        },
      ],
    });

    cy.on("tap", "node, edge", (event) => {
      setSelection(event.target.data());
    });
  }

  async function loadInspector() {
    graphStatus.style.display = "block";
    graphStatus.textContent = "Loading graph…";
    try {
      const maxRuleEdges = Number(maxRuleEdgesInput.value) || 80;
      const response = await fetch("/api/introspection?max_rule_edges=" + encodeURIComponent(maxRuleEdges));
      const payload = await response.json();
      sourceText.textContent = "runtime source: " + payload.source;
      summaryText.textContent =
        "graph nodes " +
        payload.introspection.hypergraph.counts.nodes +
        " • graph edges " +
        payload.introspection.hypergraph.counts.edges +
        " • rules " +
        payload.introspection.hypergraph.counts.rules;
      renderGraph(payload.introspection.hypergraph.cytoscape);
      renderPackets(payload.introspection.search_packets);
      renderWorkers(payload.introspection.active_workers);
      renderComparisons(payload.introspection.comparison_state);
      renderDerivations(payload.introspection.derivation_fragments);
      setSelection(payload.introspection.hypergraph.counts);
    } catch (error) {
      graphStatus.style.display = "block";
      graphStatus.textContent = "Inspector load failed: " + error;
    }
  }

  refreshButton.addEventListener("click", loadInspector);
  autoRefresh.addEventListener("change", () => {
    if (refreshHandle) {
      clearInterval(refreshHandle);
      refreshHandle = null;
    }
    if (autoRefresh.checked) {
      refreshHandle = setInterval(loadInspector, 3000);
    }
  });

  loadInspector();
})();
