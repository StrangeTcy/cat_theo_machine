# Visual renders — round 2

Seven captures of the visualiser, made on 2026-11-03, and the evidence behind
them is in `../visualiser-round2-2026-11-03.log`.

**Read this first.** These are not browser screenshots. No browser on this image
can execute a page (Chromium 153 from an npm tarball starts but every page load
dies with SIGSEGV; see section 1 of the log). Instead:

1. the page runs in jsdom — real `app.js`, `model.js`, stylesheet and real data
   from the running server;
2. the page's own **Export view SVG** button produces the file;
3. `@resvg/resvg-js` rasterises that SVG to PNG.

So shapes, colours, positions, labels and links in the PNGs are the page's own
output, and each `.svg` next to a `.png` can be opened in a real browser to check
the same image. The HTML chrome — sidebar, toolbar, legend box, timeline — is not
inside the SVG, so it is absent here; it is covered by the 56 DOM assertions and
by `capture.json`, which records the badge, legend text and timeline text at each
capture.

All seven come from one recorded Machine run,
`round2-residency-20261103-143947`: a script started independently in its own
terminal, 41 events over 31 s, 66 items and 40 edges at the end, including 25
rules and 15 hyperedges (one ternary, one nullary). The Machine process had
exited before these captures were taken.

| file | what it shows |
| --- | --- |
| `01-live-initial` | the page as it opens against a live viewer: the graph of the last run, both terminals idle |
| `02-dense-rules-hyperedges` | the whole recorded graph: 25 violet rule diamonds, 15 amber hyperedges, 55 terms, 12 vertices, 88 incidence links |
| `03-hyperedge-closeup` | focus on a ternary `Between` hyperedge at 1.6x: three argument links numbered 1, 2, 3, rule arrows and premise/replacement labels readable |
| `04-fit-whole-graph` | the same graph fitted into the viewport: 95 of 107 labels placed, no overlaps, marks held above 3.6 px on screen |
| `05-selection-provenance` | one vertex selected and centred, with the details panel describing it |
| `06-replay-seek` | replay seeked to event 13 of 41 (17.61 s): fewer items than the end state, same recording |
| `07-live-evolution` | a freshly opened page against the live server after the run |

`capture.json` holds the machine-readable version of the same facts per capture:
element counts by kind, link count, visible versus total labels, the viewport
transform, the legend text, the details panel text and the timeline text.
