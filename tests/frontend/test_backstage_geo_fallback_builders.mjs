import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "../..");

const baselineRun = {
  runId: "demo-building-footprints-baseline-20260411183000",
  providerId: "amap-aoi-poi",
  batchName: "demo-building-footprints-baseline",
  createdAt: "2026-04-11T18:30:00+08:00",
  coveragePct: 80,
  resolvedBuildingCount: 4,
  openTaskCount: 18,
  reviewTaskCount: 1,
  captureTaskCount: 17,
};

const selectedRun = {
  runId: "demo-building-footprints-20260412110000",
  providerId: "amap-aoi-poi",
  batchName: "demo-building-footprints",
  createdAt: "2026-04-12T11:00:00+08:00",
  coveragePct: 100,
  resolvedBuildingCount: 6,
  openTaskCount: 15,
  reviewTaskCount: 0,
  captureTaskCount: 15,
};

function loadFallbackBuildersContext() {
  const operationsOverview = { geoAssetRuns: [baselineRun, selectedRun] };
  const source = fs.readFileSync(path.join(repoRoot, "frontend/backstage/lib/fallback-builders.js"), "utf8");
  const context = {
    effectiveOperationsOverview: () => operationsOverview,
    availableGeoBaselineRunsFor: () => [baselineRun],
  };
  vm.createContext(context);
  vm.runInContext(source, context, { filename: "frontend/backstage/lib/fallback-builders.js" });
  return context;
}

test("buildFallbackGeoAssetRunDetail: mirrors API coordinateDatum contract", () => {
  const { buildFallbackGeoAssetRunDetail } = loadFallbackBuildersContext();

  const detail = buildFallbackGeoAssetRunDetail(selectedRun.runId, baselineRun.runId);

  assert.ok(detail.featurePreview.length > 0);
  assert.ok(detail.comparison.topBuildingChanges.length > 0);
  assert.deepEqual(
    Array.from(detail.featurePreview, (item) => item.coordinateDatum),
    ["gcj02", "gcj02"]
  );
  assert.deepEqual(
    Array.from(detail.comparison.topBuildingChanges, (item) => item.coordinateDatum),
    ["gcj02", "gcj02", "gcj02"]
  );
});
