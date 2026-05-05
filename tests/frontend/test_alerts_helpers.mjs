import { test } from "node:test";
import assert from "node:assert/strict";

import {
  formatAlertLine,
  severityFor,
} from "../../frontend/user/modules/alerts-helpers.js";

test("formatAlertLine: yield_up renders pp delta", () => {
  const line = formatAlertLine({
    kind: "yield_up",
    from_value: 4.0,
    to_value: 4.6,
    delta: 0.6,
  });
  assert.equal(line, "租售比 4.00% → 4.60% (+0.60)");
});

test("formatAlertLine: yield_down renders negative delta", () => {
  const line = formatAlertLine({
    kind: "yield_down",
    from_value: 4.0,
    to_value: 3.4,
    delta: -0.6,
  });
  assert.equal(line, "租售比 4.00% → 3.40% (−0.60)");
});

test("formatAlertLine: price_drop renders percent off base", () => {
  const line = formatAlertLine({
    kind: "price_drop",
    from_value: 1000.0,
    to_value: 950.0,
    delta: -50.0,
  });
  assert.equal(line, "总价 1000 → 950 万 (−5.0%)");
});

test("formatAlertLine: score_jump renders signed delta", () => {
  const up = formatAlertLine({
    kind: "score_jump",
    from_value: 60,
    to_value: 70,
    delta: 10,
  });
  assert.equal(up, "机会分 60 → 70 (+10)");
  const down = formatAlertLine({
    kind: "score_jump",
    from_value: 60,
    to_value: 50,
    delta: -10,
  });
  assert.equal(down, "机会分 60 → 50 (−10)");
});

test("formatAlertLine: unknown kind falls back to string", () => {
  const line = formatAlertLine({ kind: "mystery", from_value: 1, to_value: 2 });
  assert.equal(line, "mystery 1 → 2");
});

test("severityFor: yield_up + score_jump positive → up", () => {
  assert.equal(severityFor({ kind: "yield_up" }), "up");
  assert.equal(severityFor({ kind: "score_jump", delta: 10 }), "up");
});

test("severityFor: yield_down + price_drop + negative score → down", () => {
  assert.equal(severityFor({ kind: "yield_down" }), "down");
  assert.equal(severityFor({ kind: "price_drop" }), "down");
  assert.equal(severityFor({ kind: "score_jump", delta: -5 }), "down");
});

test("severityFor: unknown kind → warn", () => {
  assert.equal(severityFor({ kind: "mystery" }), "warn");
});

test("formatAlertLine: district_delta_up renders pp delta", () => {
  const line = formatAlertLine({
    kind: "district_delta_up",
    from_value: 4.0,
    to_value: 5.2,
    delta: 1.2,
  });
  assert.equal(line, "区均租售比 4.00% → 5.20% (+1.20)");
});

test("formatAlertLine: district_delta_down renders negative", () => {
  const line = formatAlertLine({
    kind: "district_delta_down",
    from_value: 4.5,
    to_value: 3.4,
    delta: -1.1,
  });
  assert.equal(line, "区均租售比 4.50% → 3.40% (−1.10)");
});

test("severityFor: district_delta_up → up", () => {
  assert.equal(severityFor({ kind: "district_delta_up" }), "up");
});

test("severityFor: district_delta_down → down", () => {
  assert.equal(severityFor({ kind: "district_delta_down" }), "down");
});

test("formatAlertLine: candidate rule and review alerts render labels", () => {
  assert.equal(
    formatAlertLine({ kind: "target_price_hit", from_value: 900, to_value: 880 }),
    "目标价触发 900 → 880 万",
  );
  assert.equal(
    formatAlertLine({ kind: "target_rent_hit", from_value: 18000, to_value: 18500 }),
    "目标租金触发 18000 → 18500 元/月",
  );
  assert.equal(
    formatAlertLine({ kind: "target_yield_hit", from_value: 4.2, to_value: 4.5 }),
    "目标收益触发 4.20% → 4.50%",
  );
  assert.equal(formatAlertLine({ kind: "review_due" }), "候选到期复核");
  assert.equal(formatAlertLine({ kind: "evidence_missing" }), "证据不足，需补样");
  assert.equal(
    formatAlertLine({ kind: "floor_sample_change", from_value: 2, to_value: 5 }),
    "同楼层样本 2 → 5 条",
  );
});

test("severityFor: candidate rule severities", () => {
  assert.equal(severityFor({ kind: "target_yield_hit" }), "up");
  assert.equal(severityFor({ kind: "target_rent_hit" }), "up");
  assert.equal(severityFor({ kind: "floor_sample_change" }), "up");
  assert.equal(severityFor({ kind: "target_price_hit" }), "down");
  assert.equal(severityFor({ kind: "review_due" }), "warn");
});
