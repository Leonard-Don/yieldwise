import { test } from "node:test";
import assert from "node:assert/strict";

import {
  MODES,
  getMode,
  yieldColorFor,
  defaultFiltersFor,
  normalizeInitialFiltersFor,
  resolveDefaultFilters,
} from "../../frontend/user/modules/modes.js";

test("MODES: only the rent-sale-ratio workspace is exposed", () => {
  assert.deepEqual(MODES.map((m) => m.id), ["yield"]);
});

test("getMode: returns the matching config", () => {
  const m = getMode("yield");
  assert.equal(m.id, "yield");
  assert.equal(m.label, "租售比观察");
});

test("getMode: unknown and legacy ids fall back to yield", () => {
  assert.equal(getMode("nonsense").id, "yield");
  assert.equal(getMode("home").id, "yield");
  assert.equal(getMode("city").id, "yield");
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

test("defaultFiltersFor: yield mode starts without restrictive filters", () => {
  assert.deepEqual(defaultFiltersFor("yield"), {});
});

test("defaultFiltersFor: legacy modes resolve to the yield defaults", () => {
  assert.deepEqual(defaultFiltersFor("home"), {});
  assert.deepEqual(defaultFiltersFor("city"), {});
});

test("normalizeInitialFiltersFor: migrates the legacy strict yield defaults", () => {
  assert.deepEqual(normalizeInitialFiltersFor("yield", { minYield: 4, maxBudget: 1500 }), {});
  assert.deepEqual(normalizeInitialFiltersFor("yield", { minYield: "4", maxBudget: "1500" }), {});
});

test("normalizeInitialFiltersFor: preserves user-customized filters", () => {
  assert.deepEqual(normalizeInitialFiltersFor("yield", { minYield: 3.5, maxBudget: 1500 }), {
    minYield: 3.5,
    maxBudget: 1500,
  });
});

test("resolveDefaultFilters: yield mode starts without restrictive filters", () => {
  assert.deepEqual(resolveDefaultFilters("yield", null), {});
});

test("resolveDefaultFilters: legacy mode ids no longer pull preference filters", () => {
  assert.deepEqual(resolveDefaultFilters("home", { budget_max_wan: 1200, districts: ["pudong"] }), {});
  assert.deepEqual(resolveDefaultFilters("city", { budget_max_wan: 1200 }), {});
});
