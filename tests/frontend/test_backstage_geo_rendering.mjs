import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "../..");

function loadBackstageFormatContext() {
  const source = fs.readFileSync(path.join(repoRoot, "frontend/backstage/lib/format.js"), "utf8");
  const context = {};
  vm.createContext(context);
  vm.runInContext(source, context, { filename: "frontend/backstage/lib/format.js" });
  return context;
}

test("geoEvidenceTitleMarkup: renders escaped names with a normalized datum badge", () => {
  const { geoEvidenceTitleMarkup } = loadBackstageFormatContext();

  const markup = geoEvidenceTitleMarkup({
    communityName: '静安<script>alert("x")</script>',
    buildingName: "A&B'楼",
    coordinateDatum: "wgs84",
  });

  assert.match(markup, /^<strong>.*<\/strong><span /);
  assert.ok(markup.includes("静安&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"));
  assert.ok(markup.includes("A&amp;B&#39;楼"));
  assert.ok(!markup.includes("<script>"));
  assert.ok(markup.includes('data-geo-datum="wgs84"'));
  assert.ok(markup.includes(">WGS-84<"));
});

test("comparison top-building rows use the datum badge title helper", () => {
  const { geoEvidenceTitleMarkup } = loadBackstageFormatContext();
  const appSource = fs.readFileSync(path.join(repoRoot, "frontend/backstage/app.js"), "utf8");
  const blockStart = appSource.indexOf("selectedGeoRunDetail.comparison.topBuildingChanges");
  const blockEnd = appSource.indexOf("当前批次相对基线还没有显著几何变化", blockStart);
  const comparisonBlock = appSource.slice(blockStart, blockEnd);

  assert.notEqual(blockStart, -1);
  assert.notEqual(blockEnd, -1);
  assert.match(comparisonBlock, /geoEvidenceTitleMarkup\(item\)/);
  assert.doesNotMatch(comparisonBlock, /<strong>\$\{item\.communityName/);

  const comparisonTitleMarkup = geoEvidenceTitleMarkup({
    communityName: "浦东样本小区",
    buildingName: "8号楼",
    coordinateDatum: "gcj02",
  });
  assert.ok(comparisonTitleMarkup.includes('data-geo-datum="gcj02"'));
  assert.ok(comparisonTitleMarkup.includes(">GCJ-02<"));
});
