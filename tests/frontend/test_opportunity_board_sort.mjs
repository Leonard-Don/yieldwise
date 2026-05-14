import { test } from "node:test";
import assert from "node:assert/strict";

import { sortItems } from "../../frontend/user/modules/opportunity-board.js";

test("sortItems: descending sort orders numeric values from high to low", () => {
  const items = [
    { id: "a", yield: 3 },
    { id: "b", yield: 7 },
    { id: "c", yield: 5 },
  ];
  const sorted = sortItems(items, { key: "yield", direction: "desc" });
  assert.deepEqual(sorted.map((i) => i.id), ["b", "c", "a"]);
});

test("sortItems: explicit 0 is a real value, not a missing marker", () => {
  // The board sorts by yield/score; rows with an explicit zero should keep
  // their numeric position relative to other numbers — not be lumped in with
  // null/undefined as "no data".
  const items = [
    { id: "neg", yield: -1 },
    { id: "zero", yield: 0 },
    { id: "pos", yield: 4 },
    { id: "missing", yield: null },
  ];
  const desc = sortItems(items, { key: "yield", direction: "desc" });
  assert.deepEqual(
    desc.map((i) => i.id),
    ["pos", "zero", "neg", "missing"],
    "desc: 0 sits between positive and negative; null goes to the end",
  );
  const asc = sortItems(items, { key: "yield", direction: "asc" });
  assert.deepEqual(
    asc.map((i) => i.id),
    ["neg", "zero", "pos", "missing"],
    "asc: 0 sits between negative and positive; null still goes to the end",
  );
});

test("sortItems: null and undefined values sort to the end regardless of direction", () => {
  const items = [
    { id: "n", yield: null },
    { id: "u", yield: undefined },
    { id: "a", yield: 4 },
    { id: "b", yield: 1 },
  ];
  const desc = sortItems(items, { key: "yield", direction: "desc" });
  assert.deepEqual(desc.slice(0, 2).map((i) => i.id), ["a", "b"]);
  assert.ok(["n", "u"].includes(desc[2].id) && ["n", "u"].includes(desc[3].id));

  const asc = sortItems(items, { key: "yield", direction: "asc" });
  assert.deepEqual(asc.slice(0, 2).map((i) => i.id), ["b", "a"]);
  assert.ok(["n", "u"].includes(asc[2].id) && ["n", "u"].includes(asc[3].id));
});

test("sortItems: NaN values sort to the end like null (no silent reordering)", () => {
  // NaN sneaks through Number() when upstream data is malformed; the board
  // should treat it as 'no data' and push it to the end, not float it to the
  // top because of how IEEE-754 NaN comparisons return false.
  const items = [
    { id: "nan", yield: Number.NaN },
    { id: "low", yield: 1 },
    { id: "high", yield: 9 },
  ];
  const desc = sortItems(items, { key: "yield", direction: "desc" });
  assert.deepEqual(
    desc.map((i) => i.id),
    ["high", "low", "nan"],
    "desc: NaN must go to the end, not the top",
  );
  const asc = sortItems(items, { key: "yield", direction: "asc" });
  assert.deepEqual(
    asc.map((i) => i.id),
    ["low", "high", "nan"],
    "asc: NaN must go to the end, not the top",
  );
});

test("sortItems: Infinity/-Infinity sort to the end like NaN (bogus upstream math)", () => {
  // Infinity escapes Number.isNaN (and Number() coercion) when an upstream
  // metric divides by zero (e.g. rent/price=0 → yield=Infinity). The board's
  // missing-value sink already catches null/undefined/NaN; ±Infinity belongs
  // in the same bucket — otherwise it floats to the top of a desc sort and
  // displaces legitimate rows, while formatValue renders the cell as "—".
  const items = [
    { id: "pos_inf", yield: Number.POSITIVE_INFINITY },
    { id: "neg_inf", yield: Number.NEGATIVE_INFINITY },
    { id: "low", yield: 1 },
    { id: "high", yield: 9 },
  ];
  const desc = sortItems(items, { key: "yield", direction: "desc" });
  assert.deepEqual(
    desc.slice(0, 2).map((i) => i.id),
    ["high", "low"],
    "desc: finite numbers come first, ±Infinity at the end",
  );
  const descTail = desc.slice(2).map((i) => i.id).sort();
  assert.deepEqual(
    descTail,
    ["neg_inf", "pos_inf"],
    "desc: both ±Infinity belong in the missing-marker bucket at the end",
  );
  const asc = sortItems(items, { key: "yield", direction: "asc" });
  assert.deepEqual(
    asc.slice(0, 2).map((i) => i.id),
    ["low", "high"],
    "asc: finite numbers come first, ±Infinity still at the end",
  );
  const ascTail = asc.slice(2).map((i) => i.id).sort();
  assert.deepEqual(
    ascTail,
    ["neg_inf", "pos_inf"],
    "asc: ±Infinity stays in the missing-marker bucket regardless of direction",
  );
});

test("sortItems: mixed null/NaN/numbers — all missing markers cluster at the end", () => {
  const items = [
    { id: "a", score: 50 },
    { id: "nan", score: Number.NaN },
    { id: "null", score: null },
    { id: "b", score: 10 },
    { id: "undef", score: undefined },
    { id: "zero", score: 0 },
  ];
  const sorted = sortItems(items, { key: "score", direction: "desc" });
  // First three are the numeric values, in desc order; last three are the
  // missing markers (any order is fine).
  assert.deepEqual(sorted.slice(0, 3).map((i) => i.id), ["a", "b", "zero"]);
  const tail = sorted.slice(3).map((i) => i.id).sort();
  assert.deepEqual(tail, ["nan", "null", "undef"]);
});

test("sortItems: returns the original list when no sortSpec is supplied", () => {
  const items = [{ id: "a" }, { id: "b" }];
  assert.equal(sortItems(items, null), items);
  assert.equal(sortItems(items, undefined), items);
});
