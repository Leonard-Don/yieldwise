import { test } from "node:test";
import assert from "node:assert/strict";

import {
  clampIndex,
  formatHitLabel,
  debounce,
} from "../../frontend/user/modules/search-helpers.js";

test("clampIndex: empty list → 0", () => {
  assert.equal(clampIndex(0, 0), 0);
  assert.equal(clampIndex(5, 0), 0);
});

test("clampIndex: clamps to last index", () => {
  assert.equal(clampIndex(7, 3), 2);
  assert.equal(clampIndex(2, 3), 2);
});

test("clampIndex: floors negative to zero", () => {
  assert.equal(clampIndex(-1, 5), 0);
});

test("formatHitLabel: with district renders 'district · name'", () => {
  assert.equal(
    formatHitLabel({ target_name: "张江汤臣豪园三期", district_name: "浦东新区" }),
    "浦东新区 · 张江汤臣豪园三期",
  );
});

test("formatHitLabel: without district renders bare name", () => {
  assert.equal(
    formatHitLabel({ target_name: "浦东新区", district_name: null }),
    "浦东新区",
  );
  assert.equal(formatHitLabel({ target_name: "x" }), "x");
});

test("formatHitLabel: missing target_name returns empty string", () => {
  assert.equal(formatHitLabel({}), "");
  assert.equal(formatHitLabel(null), "");
});

test("debounce: only fires once per quiet window", async () => {
  let calls = 0;
  const inc = debounce(() => {
    calls += 1;
  }, 30);
  inc();
  inc();
  inc();
  await new Promise((resolve) => setTimeout(resolve, 60));
  assert.equal(calls, 1);
});
