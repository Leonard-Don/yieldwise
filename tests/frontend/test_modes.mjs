import { test } from "node:test";
import assert from "node:assert/strict";

import {
  MODES,
  getMode,
  yieldColorFor,
  defaultFiltersFor,
  resolveDefaultFilters,
  districtColorFor,
} from "../../frontend/user/modules/modes.js";

test("MODES: yield/home/city present in declared order", () => {
  assert.deepEqual(MODES.map((m) => m.id), ["yield", "home", "city"]);
});

test("getMode: returns the matching config", () => {
  const m = getMode("yield");
  assert.equal(m.id, "yield");
  assert.equal(m.label, "收益猎手");
});

test("getMode: unknown id falls back to yield", () => {
  assert.equal(getMode("nonsense").id, "yield");
});

test("yieldColorFor: yieldPct under 3.5 is down/red", () => {
  assert.equal(yieldColorFor(2.0), "var(--down)");
});

test("yieldColorFor: yieldPct between 3.5 and 5 is warn/amber", () => {
  assert.equal(yieldColorFor(4.0), "var(--warn)");
});

test("yieldColorFor: yieldPct >= 5 is up/green", () => {
  assert.equal(yieldColorFor(5.5), "var(--up)");
});

test("yieldColorFor: null/NaN returns dim", () => {
  assert.equal(yieldColorFor(null), "var(--text-dim)");
  assert.equal(yieldColorFor(Number.NaN), "var(--text-dim)");
});

test("defaultFiltersFor: yield mode returns minYield 4 + maxBudget 1500", () => {
  assert.deepEqual(defaultFiltersFor("yield"), { minYield: 4, maxBudget: 1500 });
});

test("defaultFiltersFor: home and city modes default to empty filters", () => {
  assert.deepEqual(defaultFiltersFor("home"), {});
  assert.deepEqual(defaultFiltersFor("city"), {});
});

test("resolveDefaultFilters: yield mode static defaults", () => {
  assert.deepEqual(resolveDefaultFilters("yield", null), { minYield: 4, maxBudget: 1500 });
});

test("resolveDefaultFilters: home with empty prefs returns empty", () => {
  assert.deepEqual(resolveDefaultFilters("home", null), {});
  assert.deepEqual(resolveDefaultFilters("home", {}), {});
  assert.deepEqual(resolveDefaultFilters("home", { budget_max_wan: null, districts: [] }), {});
});

test("resolveDefaultFilters: home with budget pulls maxBudget", () => {
  assert.deepEqual(
    resolveDefaultFilters("home", { budget_max_wan: 1200, districts: [] }),
    { maxBudget: 1200 },
  );
});

test("resolveDefaultFilters: home with districts uses first district", () => {
  assert.deepEqual(
    resolveDefaultFilters("home", { budget_max_wan: 1200, districts: ["pudong", "jingan"] }),
    { maxBudget: 1200, district: "pudong" },
  );
});

test("resolveDefaultFilters: city mode is empty regardless of prefs", () => {
  assert.deepEqual(resolveDefaultFilters("city", { budget_max_wan: 1200 }), {});
});

test("MODES: home mode is now enabled", () => {
  assert.equal(getMode("home").enabled, true);
});

test("districtColorFor: null/NaN returns dim", () => {
  assert.equal(districtColorFor(null, 4), "var(--text-dim)");
  assert.equal(districtColorFor(Number.NaN, 4), "var(--text-dim)");
  assert.equal(districtColorFor(4, null), "var(--text-dim)");
});

test("districtColorFor: value above mean by > 0.2 → up", () => {
  assert.equal(districtColorFor(5, 4), "var(--up)");
});

test("districtColorFor: value below mean by > 0.2 → down", () => {
  assert.equal(districtColorFor(3, 4), "var(--down)");
});

test("districtColorFor: value within ±0.2 of mean → warn", () => {
  assert.equal(districtColorFor(4.1, 4), "var(--warn)");
  assert.equal(districtColorFor(3.9, 4), "var(--warn)");
});

test("districtColorFor: handles fractional yield (auto-scale 0.04 → 4)", () => {
  // The function should accept either fraction or percent — same heuristic as
  // yieldColorFor — to handle staged data that stores yield as 0.04 vs 4.0.
  assert.equal(districtColorFor(0.05, 0.04), "var(--up)");
  assert.equal(districtColorFor(0.03, 0.04), "var(--down)");
});
