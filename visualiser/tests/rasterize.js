/* Turns the SVGs written by pixel_capture.js into PNGs.
 *
 *   node visualiser/tests/rasterize.js verification/visualiser-round2
 *
 * Uses @resvg/resvg-js, an SVG rasteriser, if it is installed. It is not a
 * dependency of the visualiser - the viewer needs no rasteriser to run - so this
 * reports what is missing and exits 0 when it is absent:
 *
 *   npm install --prefix /tmp/resvg @resvg/resvg-js
 *   NODE_PATH=/tmp/resvg/node_modules node visualiser/tests/rasterize.js <dir>
 *
 * Fonts come from the system (DejaVu is present on this image); no font is
 * fetched.
 */
"use strict";

let Resvg;
try {
  ({ Resvg } = require("@resvg/resvg-js"));
} catch (error) {
  console.log(JSON.stringify({ skipped: true, reason: "@resvg/resvg-js is not installed: " + error.message }));
  process.exit(0);
}

const fs = require("fs");
const path = require("path");

const dir = process.argv[2] || "verification/visualiser-round2";
const width = Number(process.argv[3] || 1440);

const files = fs.readdirSync(dir).filter((name) => name.endsWith(".svg")).sort();
const written = [];
files.forEach((name) => {
  const svg = fs.readFileSync(path.join(dir, name), "utf8");
  const renderer = new Resvg(svg, {
    background: "#0b0f14",
    font: { loadSystemFonts: true, defaultFontFamily: "DejaVu Sans" },
    fitTo: { mode: "width", value: width }
  });
  const png = path.join(dir, name.replace(/\.svg$/, ".png"));
  fs.writeFileSync(png, renderer.render().asPng());
  written.push({ png: png, bytes: fs.statSync(png).size });
  console.log(png + "  " + fs.statSync(png).size + " bytes");
});

console.log(JSON.stringify({ rendered: written.length, width: width }, null, 2));
process.exit(written.length ? 0 : 1);
