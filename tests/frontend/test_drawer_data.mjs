import { test } from "node:test";
import assert from "node:assert/strict";

import {
  formatPct,
  formatWan,
  formatYuan,
  normalizeYieldPct,
  normalizeQuality,
  bucketBars,
  pickKpisFor,
  topCommunitiesFromDistrict,
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

test("normalizeQuality: keeps compact visible fields for drawer rendering", () => {
  const quality = normalizeQuality({
    quality: {
      status: "usable",
      label: "可用",
      score: 72.4,
      sampleLabel: "售 4 / 租 5",
      reasons: ["样本足够"],
      checks: [
        { id: "sample_balance", label: "租售样本", status: "ok", detail: "售 4 / 租 5" },
        { id: "yield_signal", label: "收益信号", status: "ok", detail: "4.20%" },
      ],
    },
  });

  assert.equal(quality.status, "usable");
  assert.equal(quality.score, 72);
  assert.equal(quality.sampleLabel, "售 4 / 租 5");
  assert.equal(quality.checks.length, 2);
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

test("pickKpisFor: yield mode focuses on yield/payback/score/sample", () => {
  const detail = {
    yieldAvg: 0.04,
    paybackYears: 25,
    score: 66,
    sampleSize: 13,
    saleMedianWan: 306.85,
    rentMedianMonthly: 12900,
  };
  const kpis = pickKpisFor("yield", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "payback", "score", "sample"]);
  assert.equal(kpis[0].value, "4.00%");
  assert.equal(kpis[1].value, "25.0 年");
});

test("pickKpisFor: home mode focuses on price/rent/payback/sample", () => {
  const detail = {
    yieldAvg: 0.04,
    paybackYears: 25,
    score: 66,
    sampleSize: 13,
    saleMedianWan: 306.85,
    rentMedianMonthly: 12900,
  };
  const kpis = pickKpisFor("home", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["price", "rent", "payback", "sample"]);
  assert.equal(kpis[0].value, "306.85 万");
  assert.equal(kpis[1].value, "¥12,900");
  assert.equal(kpis[2].value, "25.0 年");
});

test("pickKpisFor: city mode focuses on yield/payback/score/sample (community-level KPI labels)", () => {
  const detail = { yield: 4.16, paybackYears: 24, score: 99, sample: 16 };
  const kpis = pickKpisFor("city", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "payback", "score", "sample"]);
  assert.equal(kpis[0].value, "4.16%");
  assert.equal(kpis[1].value, "24.0 年");
});

test("pickKpisFor: unknown mode falls back to yield mode kpis", () => {
  const detail = { yieldAvg: 0.04, paybackYears: 25, score: 66, sampleSize: 13 };
  const kpis = pickKpisFor("nonsense", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "payback", "score", "sample"]);
});

test("pickKpisFor: footprint KPI is inserted next to quantitative tiles", () => {
  const detail = { yieldAvg: 0.04, paybackYears: 25, score: 66, sampleSize: 13, osmFootprintCount: 12 };
  const kpis = pickKpisFor("yield", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "payback", "footprints", "score", "sample"]);
  assert.equal(kpis[2].value, "12 栋");
});

test("topCommunitiesFromDistrict: empty input → []", () => {
  assert.deepEqual(topCommunitiesFromDistrict(null, 5), []);
  assert.deepEqual(topCommunitiesFromDistrict({}, 5), []);
  assert.deepEqual(topCommunitiesFromDistrict({ communities: [] }, 5), []);
});

test("topCommunitiesFromDistrict: returns up to limit rows preserving server order", () => {
  const detail = {
    communities: [
      { id: "a", name: "A", yield: 5.0, score: 80 },
      { id: "b", name: "B", yield: 4.5, score: 70 },
      { id: "c", name: "C", yield: 4.0, score: 60 },
      { id: "d", name: "D", yield: 3.5, score: 50 },
    ],
  };
  const top2 = topCommunitiesFromDistrict(detail, 2);
  assert.deepEqual(top2.map((row) => row.id), ["a", "b"]);
});

test("topCommunitiesFromDistrict: tolerates missing fields", () => {
  const detail = {
    communities: [
      { id: "a", name: "A" },
      { id: "b", yield: 4.0 },
      { name: "C", yield: 3.0 }, // missing id — dropped
    ],
  };
  const rows = topCommunitiesFromDistrict(detail, 5);
  assert.deepEqual(rows.map((r) => r.id), ["a", "b"]);
});
