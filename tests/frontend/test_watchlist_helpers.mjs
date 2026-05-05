import { test } from "node:test";
import assert from "node:assert/strict";

import {
  buildWatchlistMemoPayload,
  candidateStatusLabel,
  candidateToComparisonItem,
  formatCandidateMetric,
  isStarred,
  normalizeWatchlistItems,
  targetTypeLabel,
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

test("normalizeWatchlistItems: accepts district and sorts active candidates first", () => {
  const rows = normalizeWatchlistItems([
    { target_id: "x", target_type: "community", status: "watching", priority: 3 },
    { target_id: "pudong", target_type: "district", status: "shortlisted", priority: 1 },
    { target_id: "bad", target_type: "listing" },
  ]);

  assert.deepEqual(rows.map((item) => item.target_id), ["pudong", "x"]);
  assert.equal(rows[0].status_label, "候选");
});

test("candidateToComparisonItem: uses current snapshot fields", () => {
  const item = candidateToComparisonItem({
    target_id: "b1",
    target_type: "building",
    target_name: "1号楼",
    current_snapshot: {
      yield: 4.5,
      score: 88,
      qualityLabel: "可用",
      qualityStatus: "usable",
      districtName: "浦东新区",
    },
  });

  assert.equal(item.target_type, "building");
  assert.equal(item.yield_pct, 4.5);
  assert.equal(item.quality_status, "usable");
  assert.equal(item.district_name, "浦东新区");
});

test("buildWatchlistMemoPayload: maps first five candidates to decision targets", () => {
  const payload = buildWatchlistMemoPayload([
    { target_id: "a", target_type: "community" },
    { target_id: "b", target_type: "building" },
    { target_id: "pudong", target_type: "district" },
  ]);

  assert.deepEqual(payload.targets, [
    { target_id: "a", target_type: "community" },
    { target_id: "b", target_type: "building" },
    { target_id: "pudong", target_type: "district" },
  ]);
});

test("labels and metric formatting are stable", () => {
  assert.equal(candidateStatusLabel("researching"), "复核中");
  assert.equal(targetTypeLabel("district"), "区");
  assert.equal(formatCandidateMetric(4.234, "%"), "4.23%");
  assert.equal(formatCandidateMetric(780, "万"), "780万");
  assert.equal(formatCandidateMetric(null, "%"), "—");
});
