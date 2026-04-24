import { test } from "node:test";
import assert from "node:assert/strict";

import { MODES, getMode, yieldColorFor } from "../../frontend/user/modules/modes.js";

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
