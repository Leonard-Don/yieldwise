import { test } from "node:test";
import assert from "node:assert/strict";

import { filtersToApiParams, describeFilter, prunedFilters } from "../../frontend/user/modules/modes.js";

test("filtersToApiParams: yield filters → snake_case params", () => {
  const params = filtersToApiParams({ minYield: 4, maxBudget: 1500 });
  assert.deepEqual(params, { min_yield: 4, max_budget: 1500 });
});

test("filtersToApiParams: district key passes through as 'district'", () => {
  const params = filtersToApiParams({ district: "pudong", maxBudget: 1500 });
  assert.deepEqual(params, { district: "pudong", max_budget: 1500 });
});

test("filtersToApiParams: empty filter object → empty params", () => {
  assert.deepEqual(filtersToApiParams({}), {});
});

test("filtersToApiParams: skips undefined / null / empty-string values", () => {
  const params = filtersToApiParams({
    minYield: 4,
    maxBudget: undefined,
    minSamples: null,
    minScore: "",
  });
  assert.deepEqual(params, { min_yield: 4 });
});

test("filtersToApiParams: passes minSamples and minScore through", () => {
  const params = filtersToApiParams({ minSamples: 2, minScore: 50 });
  assert.deepEqual(params, { min_samples: 2, min_score: 50 });
});

test("describeFilter: renders human-friendly chip labels", () => {
  assert.equal(describeFilter("minYield", 4), "租售比 ≥ 4%");
  assert.equal(describeFilter("maxBudget", 1500), "总价 ≤ 1500 万");
  assert.equal(describeFilter("minSamples", 2), "样本量 ≥ 2");
  assert.equal(describeFilter("minScore", 50), "机会分 ≥ 50");
  assert.equal(describeFilter("district", "pudong"), "区域 = pudong");
});

test("describeFilter: unknown key falls back to key=value", () => {
  assert.equal(describeFilter("custom", 7), "custom = 7");
});

test("prunedFilters: drops keys whose value matches the API default", () => {
  // /api/v2/opportunities defaults: min_yield 0, max_budget 10000,
  // min_samples 0, min_score 0. So filters at the API default are NOT
  // distinct from "no filter" and shouldn't render as chips.
  const pruned = prunedFilters({ minYield: 0, maxBudget: 10000, minScore: 50 });
  assert.deepEqual(pruned, { minScore: 50 });
});

test("prunedFilters: drops district='all' (API default)", () => {
  const pruned = prunedFilters({ district: "all", maxBudget: 1500 });
  assert.deepEqual(pruned, { maxBudget: 1500 });
});
