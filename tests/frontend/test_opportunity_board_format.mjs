import { test } from "node:test";
import assert from "node:assert/strict";

import { formatValue } from "../../frontend/user/modules/opportunity-board.js";

// Baseline: explicit-zero is a real value, mirroring sortItems' policy.
test("formatValue pct: explicit 0 renders as 0.00% (not missing)", () => {
  assert.equal(formatValue(0, "pct"), "0.00%");
});

test("formatValue pct/wan/int: null and undefined render as —", () => {
  assert.equal(formatValue(null, "pct"), "—");
  assert.equal(formatValue(undefined, "pct"), "—");
  assert.equal(formatValue(null, "wan"), "—");
  assert.equal(formatValue(undefined, "wan"), "—");
  assert.equal(formatValue(null, "int"), "—");
  assert.equal(formatValue(undefined, "int"), "—");
});

test("formatValue pct/wan/int: literal NaN renders as —", () => {
  assert.equal(formatValue(Number.NaN, "pct"), "—");
  assert.equal(formatValue(Number.NaN, "wan"), "—");
  assert.equal(formatValue(Number.NaN, "int"), "—");
});

// The bug: Number.isNaN("abc") is false, so non-numeric strings slip past the
// guard and Number(value) coerces them to NaN, which then renders to the UI as
// the literal string "NaN%" / "NaN". The renderer must never leak "NaN" into
// the DOM — fall back to the missing marker like the `sample` branch already
// does via Number.isFinite.
test("formatValue pct: non-numeric strings render as — (no leaked 'NaN%')", () => {
  assert.equal(formatValue("abc", "pct"), "—");
  assert.equal(formatValue("--", "pct"), "—");
});

test("formatValue wan: non-numeric strings render as — (no leaked 'NaN')", () => {
  assert.equal(formatValue("abc", "wan"), "—");
});

test("formatValue int: non-numeric strings render as — (no leaked 'NaN')", () => {
  assert.equal(formatValue("abc", "int"), "—");
});

// Empty string is the upstream "no value" marker (see coerceNumber in
// comparison-helpers.js). Number("") coerces to 0, so without an early
// guard pct/wan/int would render "0.00%" / "0" — silently inventing data.
test("formatValue pct/wan/int: empty string renders as — (not silently 0)", () => {
  assert.equal(formatValue("", "pct"), "—");
  assert.equal(formatValue("", "wan"), "—");
  assert.equal(formatValue("", "int"), "—");
});

// Infinity slips through Number.isNaN too. Defensive against bad upstream
// math (e.g. divide-by-zero in a derived metric) — should not render as
// "Infinity%" or "Infinity".
test("formatValue pct/wan/int: Infinity renders as —", () => {
  assert.equal(formatValue(Infinity, "pct"), "—");
  assert.equal(formatValue(-Infinity, "wan"), "—");
  assert.equal(formatValue(Infinity, "int"), "—");
});

// Regression guard for the happy path so the new strictness doesn't break
// numeric strings that the API legitimately serializes (some endpoints send
// numeric IDs/values as strings).
test("formatValue pct/wan/int: numeric strings still format correctly", () => {
  assert.equal(formatValue("4.25", "pct"), "4.25%");
  assert.equal(formatValue("1500", "wan"), "1,500");
  assert.equal(formatValue("88.4", "int"), "88");
});

// `years` already short-circuits non-positive values to "—" by domain choice
// (negative payback is meaningless). Lock that in so the refactor doesn't
// accidentally widen the window.
test("formatValue years: <= 0 stays as — (domain rule, not just a missing marker)", () => {
  assert.equal(formatValue(0, "years"), "—");
  assert.equal(formatValue(-1, "years"), "—");
  assert.equal(formatValue(7.4, "years"), "7.4 年");
});

// `sample` already handles non-numeric input via Number.isFinite — pin that
// behavior so the consolidated guard doesn't regress the label-only path.
test("formatValue sample: label-only when numeric is missing or non-finite", () => {
  assert.equal(
    formatValue(null, "sample", { quality: { label: "可用" } }),
    "可用",
  );
  assert.equal(
    formatValue("abc", "sample", { quality: { label: "可用" } }),
    "可用",
  );
  assert.equal(formatValue(null, "sample", {}), "—");
});
