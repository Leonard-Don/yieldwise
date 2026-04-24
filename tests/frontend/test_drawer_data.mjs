import { test } from "node:test";
import assert from "node:assert/strict";

import {
  formatPct,
  formatWan,
  formatYuan,
  normalizeYieldPct,
  bucketBars,
  pickKpisFor,
} from "../../frontend/user/modules/drawer-data.js";

test("formatPct: null/undefined/NaN → —", () => {
  assert.equal(formatPct(null), "—");
  assert.equal(formatPct(undefined), "—");
  assert.equal(formatPct(Number.NaN), "—");
});

test("formatPct: 4.16 → '4.16%'", () => {
  assert.equal(formatPct(4.16), "4.16%");
});

test("formatWan: 306.85 → '306.85 万'", () => {
  assert.equal(formatWan(306.85), "306.85 万");
  assert.equal(formatWan(null), "—");
});

test("formatYuan: 12900 → '¥12,900'", () => {
  assert.equal(formatYuan(12900), "¥12,900");
  assert.equal(formatYuan(null), "—");
});

test("normalizeYieldPct: < 1 treated as fraction → ×100", () => {
  assert.equal(normalizeYieldPct(0.04), 4);
  assert.equal(normalizeYieldPct(4.16), 4.16);
  assert.equal(normalizeYieldPct(null), null);
});

test("bucketBars: returns 3 entries with label/value/pct", () => {
  const bars = bucketBars({ low: 3.2, mid: 4.5, high: 5.1 });
  assert.equal(bars.length, 3);
  assert.deepEqual(bars.map((b) => b.label), ["低层", "中层", "高层"]);
  assert.equal(bars[2].value, 5.1);
  // pct is value relative to the max in the set, scaled 0-100
  assert.equal(bars[2].pct, 100);
  assert.ok(bars[0].pct < bars[2].pct);
});

test("bucketBars: handles all-zero/empty without dividing by zero", () => {
  const bars = bucketBars({ low: 0, mid: 0, high: 0 });
  assert.equal(bars.length, 3);
  assert.equal(bars[0].pct, 0);
  assert.equal(bars[1].pct, 0);
  assert.equal(bars[2].pct, 0);
});

test("pickKpisFor: yield mode focuses on yield/score/sample", () => {
  const detail = {
    yieldAvg: 0.04,
    score: 66,
    sampleSize: 13,
    saleMedianWan: 306.85,
    rentMedianMonthly: 12900,
  };
  const kpis = pickKpisFor("yield", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "score", "sample"]);
  assert.equal(kpis[0].value, "4.00%");
});

test("pickKpisFor: home mode focuses on price/rent/sample", () => {
  const detail = {
    yieldAvg: 0.04,
    score: 66,
    sampleSize: 13,
    saleMedianWan: 306.85,
    rentMedianMonthly: 12900,
  };
  const kpis = pickKpisFor("home", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["price", "rent", "sample"]);
  assert.equal(kpis[0].value, "306.85 万");
  assert.equal(kpis[1].value, "¥12,900");
});

test("pickKpisFor: city mode focuses on yield/score/sample (community-level KPI labels)", () => {
  const detail = { yield: 4.16, score: 99, sample: 16 };
  const kpis = pickKpisFor("city", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "score", "sample"]);
  assert.equal(kpis[0].value, "4.16%");
});

test("pickKpisFor: unknown mode falls back to yield mode kpis", () => {
  const detail = { yieldAvg: 0.04, score: 66, sampleSize: 13 };
  const kpis = pickKpisFor("nonsense", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "score", "sample"]);
});
