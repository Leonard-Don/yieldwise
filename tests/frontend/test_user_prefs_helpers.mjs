import { test } from "node:test";
import assert from "node:assert/strict";

import { isPrefsEmpty } from "../../frontend/user/modules/user-prefs-helpers.js";

test("isPrefsEmpty: null prefs is empty", () => {
  assert.equal(isPrefsEmpty(null), true);
  assert.equal(isPrefsEmpty(undefined), true);
});

test("isPrefsEmpty: fresh defaults shape is empty", () => {
  const prefs = {
    budget_min_wan: null,
    budget_max_wan: null,
    districts: [],
    area_min_sqm: null,
    area_max_sqm: null,
    office_anchor: null,
    updated_at: null,
  };
  assert.equal(isPrefsEmpty(prefs), true);
});

test("isPrefsEmpty: budget_max_wan set is non-empty", () => {
  const prefs = {
    budget_min_wan: null,
    budget_max_wan: 1500,
    districts: [],
    area_min_sqm: null,
    area_max_sqm: null,
  };
  assert.equal(isPrefsEmpty(prefs), false);
});

test("isPrefsEmpty: districts populated is non-empty", () => {
  const prefs = {
    budget_min_wan: null,
    budget_max_wan: null,
    districts: ["pudong"],
    area_min_sqm: null,
    area_max_sqm: null,
  };
  assert.equal(isPrefsEmpty(prefs), false);
});

test("isPrefsEmpty: area set is non-empty", () => {
  const prefs = {
    budget_min_wan: null,
    budget_max_wan: null,
    districts: [],
    area_min_sqm: 60,
    area_max_sqm: null,
  };
  assert.equal(isPrefsEmpty(prefs), false);
});
