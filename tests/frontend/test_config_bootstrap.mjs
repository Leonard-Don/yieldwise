import { test } from "node:test";
import assert from "node:assert/strict";
import {
  applyCityConfig,
  getActiveCityConfig,
} from "../../frontend/user/modules/config-bootstrap.js";

test("applyCityConfig stores and getActiveCityConfig retrieves", () => {
  const sample = {
    cityId: "shanghai",
    displayName: "上海",
    countryCode: "CN",
    center: [121.4737, 31.2304],
    defaultZoom: 10.8,
    districts: [{ districtCode: 310101, displayName: "黄浦区" }],
  };
  const got = applyCityConfig(sample);
  assert.equal(got.cityId, "shanghai");
  assert.deepEqual(got.center, [121.4737, 31.2304]);
  assert.equal(got.defaultZoom, 10.8);
});

test("getActiveCityConfig after applyCityConfig returns frozen object", () => {
  const cfg = getActiveCityConfig();
  assert.equal(cfg.cityId, "shanghai");
  assert.ok(Object.isFrozen(cfg));
  assert.ok(Object.isFrozen(cfg.districts));
});

test("applyCityConfig rejects invalid input", () => {
  assert.throws(() => applyCityConfig(null), /invalid city config/);
  assert.throws(() => applyCityConfig({}), /invalid city config/);
  assert.throws(() => applyCityConfig({ cityId: "x" }), /invalid city config/);
  assert.throws(
    () => applyCityConfig({ cityId: "x", center: [1] }),
    /invalid city config/,
  );
});
