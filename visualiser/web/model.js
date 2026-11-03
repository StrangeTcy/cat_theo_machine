/* Event model for the Machine hypergraph visualiser.
 *
 * Loaded by the browser as `VisModel` and by the test suite through
 * `require("./model.js")`, so the replay logic that ships is the logic that is
 * tested.
 *
 * The model keeps the machine's structure intact: a hyperedge is a node with an
 * ordered list of argument ids, and the renderer draws one incidence link per
 * argument. Nothing here turns an n-ary edge into pairwise edges.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.VisModel = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var EVENT_TYPES = {
    "session.start": true,
    "nodes.added": true,
    "edges.added": true,
    "items.removed": true,
    counts: true,
    "journal.rotated": true,
    "session.stop": true,
    "observer.error": true
  };

  function createState() {
    return {
      nodes: {},
      edges: {},
      order: [],
      counts: {},
      lastSeq: -1,
      applied: 0,
      startedAt: null,
      stopped: null,
      machine: {},
      source: {},
      errors: [],
      rotations: 0,
      eventTimes: []
    };
  }

  function applyEvent(state, event) {
    if (!event || typeof event.type !== "string") {
      return state;
    }
    var type = event.type;
    if (type === "session.start") {
      state.startedAt = event.t == null ? null : event.t;
      state.machine = event.machine || {};
      state.source = event.source || {};
      state.stopped = null;
    } else if (type === "nodes.added") {
      var items = event.items || [];
      for (var i = 0; i < items.length; i += 1) {
        var item = items[i];
        if (!item || !item.id) continue;
        if (!Object.prototype.hasOwnProperty.call(state.nodes, item.id)) {
          state.order.push(item.id);
          if (item._seq == null) {
            item._seq = typeof event.seq === "number" ? event.seq : null;
            item._t = typeof event.t === "number" ? event.t : null;
          }
        }
        state.nodes[item.id] = item;
      }
    } else if (type === "edges.added") {
      var edgeItems = event.items || [];
      for (var j = 0; j < edgeItems.length; j += 1) {
        var edge = edgeItems[j];
        if (!edge || !edge.id) continue;
        if (state.edges[edge.id] == null && edge._seq == null) {
          edge._seq = typeof event.seq === "number" ? event.seq : null;
          edge._t = typeof event.t === "number" ? event.t : null;
        }
        state.edges[edge.id] = edge;
      }
    } else if (type === "items.removed") {
      var goneNodes = event.nodes || [];
      for (var k = 0; k < goneNodes.length; k += 1) {
        delete state.nodes[goneNodes[k]];
      }
      var goneEdges = event.edges || [];
      for (var m = 0; m < goneEdges.length; m += 1) {
        delete state.edges[goneEdges[m]];
      }
    } else if (type === "counts") {
      state.counts = event.counts || {};
    } else if (type === "session.stop") {
      state.stopped = event.reason || "stopped";
    } else if (type === "observer.error") {
      state.errors.push(event.error || "observer error");
    } else if (type === "journal.rotated") {
      state.rotations += 1;
    }
    if (typeof event.seq === "number" && event.seq > state.lastSeq) {
      state.lastSeq = event.seq;
    }
    if (typeof event.t === "number") {
      state.eventTimes.push(event.t);
    }
    state.applied += 1;
    state.lastEvent = event;
    return state;
  }

  function rebuild(events, upto) {
    var state = createState();
    var limit = typeof upto === "number" ? Math.min(upto, events.length) : events.length;
    for (var i = 0; i < limit; i += 1) {
      applyEvent(state, events[i]);
    }
    return state;
  }

  /* Continue applying events until `upto` events have been consumed. */
  function applyUntil(state, events, upto) {
    var limit = Math.min(upto, events.length);
    while (state.applied < limit) {
      applyEvent(state, events[state.applied]);
    }
    return state;
  }

  function nodeKind(item) {
    return item && item.kind ? item.kind : "term";
  }

  /* Build the renderable graph. Hyperedges stay n-ary: one link per argument,
     carrying the argument position and its direction. */
  function graphModel(state) {
    var nodes = [];
    var byId = {};
    var placeholders = [];

    Object.keys(state.nodes).forEach(function (id) {
      var item = state.nodes[id];
      var node = {
        id: id,
        kind: nodeKind(item),
        label: item.label || id,
        term: item.term || item.label || id,
        constructorText: textField(item, "constructor"),
        declared: item.declared === true,
        source: item.source || "",
        origin: "store"
      };
      byId[id] = node;
      nodes.push(node);
    });

    var links = [];
    Object.keys(state.edges).forEach(function (id) {
      var edge = state.edges[id];
      var edgeNode = {
        id: id,
        kind: edge.kind || "hyperedge",
        label: edge.label || id,
        term: edge.term || edge.label || id,
        relation: edge.relation || "",
        arity: typeof edge.arity === "number" ? edge.arity : 0,
        constructorText: textField(edge, "constructor"),
        source: edge.source || "",
        arguments: edge.arguments || [],
        results: edge.results || [],
        origin: "edge"
      };
      byId[id] = edgeNode;
      nodes.push(edgeNode);

      var args = edge.arguments || [];
      for (var i = 0; i < args.length; i += 1) {
        ensure(byId, nodes, placeholders, args[i]);
        links.push({
          id: id + "\u0000in\u0000" + i,
          edge: id,
          other: args[i],
          source: args[i],
          target: id,
          direction: "in",
          position: i + 1,
          arity: args.length,
          kind: "incidence"
        });
      }
      var results = edge.results || [];
      for (var r = 0; r < results.length; r += 1) {
        ensure(byId, nodes, placeholders, results[r]);
        links.push({
          id: id + "\u0000out\u0000" + r,
          edge: id,
          other: results[r],
          source: id,
          target: results[r],
          direction: "out",
          position: r + 1,
          arity: args.length,
          kind: "incidence"
        });
      }
    });

    return { nodes: nodes, links: links, byId: byId, placeholders: placeholders };
  }

  function ensure(byId, nodes, placeholders, id) {
    if (!id || byId[id]) return byId[id];
    var placeholder = {
      id: id,
      kind: "term",
      label: id,
      term: id,
      constructorText: "",
      declared: false,
      source: "referenced by an edge",
      origin: "placeholder"
    };
    byId[id] = placeholder;
    nodes.push(placeholder);
    placeholders.push(id);
    return placeholder;
  }

  /* A plain object's `constructor` is Object, which stringifies into every
     search haystack. Read the field only when it is really there. */
  function textField(item, key) {
    if (!item || !Object.prototype.hasOwnProperty.call(item, key)) return "";
    var value = item[key];
    return typeof value === "string" ? value : "";
  }

  function matches(node, query) {
    if (!query) return true;
    var needle = query.toLowerCase();
    var haystack = [
      node.id,
      node.label,
      node.term,
      node.kind,
      node.relation || "",
      node.constructorText || ""
    ]
      .join(" ")
      .toLowerCase();
    return haystack.indexOf(needle) >= 0;
  }

  /* Filter by text and by kind. A match keeps the element and its incidences,
     so a selected hyperedge never loses its arguments. */
  function filterModel(model, query, kinds) {
    var kindFilter = kinds || null;
    var matchedIds = {};
    var anyMatch = false;
    model.nodes.forEach(function (node) {
      var kindOk = !kindFilter || kindFilter.indexOf(node.kind) >= 0;
      if (kindOk && matches(node, query)) {
        matchedIds[node.id] = true;
        anyMatch = true;
      }
    });
    if (!query && !kindFilter) {
      return { nodes: model.nodes, links: model.links, matched: null, count: model.nodes.length };
    }
    var nodes = model.nodes.filter(function (node) {
      return matchedIds[node.id];
    });
    var links = model.links.filter(function (link) {
      return matchedIds[link.edge] && matchedIds[link.other];
    });
    return {
      nodes: nodes,
      links: links,
      matched: matchedIds,
      count: nodes.length,
      anyMatch: anyMatch
    };
  }

  function stats(state) {
    var kinds = { node: 0, term: 0, hyperedge: 0, rule: 0 };
    Object.keys(state.nodes).forEach(function (id) {
      var kind = nodeKind(state.nodes[id]);
      kinds[kind] = (kinds[kind] || 0) + 1;
    });
    Object.keys(state.edges).forEach(function (id) {
      var kind = nodeKind(state.edges[id]);
      kinds[kind] = (kinds[kind] || 0) + 1;
    });
    var arities = {};
    var maxArity = 0;
    Object.keys(state.edges).forEach(function (id) {
      var edge = state.edges[id];
      var args = edge.arguments || [];
      var arity = args.length;
      if (arity > maxArity) maxArity = arity;
      arities[arity] = (arities[arity] || 0) + 1;
    });
    return {
      nodes: Object.keys(state.nodes).length,
      edges: Object.keys(state.edges).length,
      kinds: kinds,
      maxArity: maxArity,
      arities: arities,
      applied: state.applied,
      lastSeq: state.lastSeq,
      counts: state.counts
    };
  }

  function toExport(state, meta) {
    return {
      format: "ctm-hypergraph-view",
      version: 1,
      kind: "visualiser-export",
      meta: meta || {},
      summary: stats(state),
      nodes: Object.keys(state.nodes).map(function (id) {
        return state.nodes[id];
      }),
      edges: Object.keys(state.edges).map(function (id) {
        return state.edges[id];
      })
    };
  }

  function eventLabel(event) {
    if (!event) return "no events";
    var type = event.type;
    if (type === "nodes.added") return "nodes +" + (event.items || []).length;
    if (type === "edges.added") return "hyperedges +" + (event.items || []).length;
    if (type === "items.removed") {
      return "removed -" + ((event.nodes || []).length + (event.edges || []).length);
    }
    if (type === "session.start") return "session start";
    if (type === "session.stop") return "session stop";
    if (type === "journal.rotated") return "new Machine run";
    if (type === "counts") return "counts";
    return type || "event";
  }

  return {
    EVENT_TYPES: EVENT_TYPES,
    createState: createState,
    applyEvent: applyEvent,
    applyUntil: applyUntil,
    rebuild: rebuild,
    graphModel: graphModel,
    filterModel: filterModel,
    stats: stats,
    toExport: toExport,
    eventLabel: eventLabel,
    matches: matches
  };
});
