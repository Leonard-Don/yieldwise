import { test } from "node:test";
import assert from "node:assert/strict";

import {
  isStarred,
  watchlistCount,
} from "../../frontend/user/modules/watchlist-helpers.js";

test("isStarred: empty list → false", () => {
  assert.equal(isStarred([], "abc"), false);
  assert.equal(isStarred(null, "abc"), false);
  assert.equal(isStarred(undefined, "abc"), false);
});

test("isStarred: matching target_id → true", () => {
  const items = [{ target_id: "abc", target_type: "building" }];
  assert.equal(isStarred(items, "abc"), true);
});

test("isStarred: non-matching id → false", () => {
  const items = [{ target_id: "abc", target_type: "building" }];
  assert.equal(isStarred(items, "xyz"), false);
});

test("watchlistCount: returns array length, defaults to 0", () => {
  assert.equal(watchlistCount([]), 0);
  assert.equal(watchlistCount(null), 0);
  assert.equal(watchlistCount([{ target_id: "a" }, { target_id: "b" }]), 2);
});
