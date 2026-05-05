import { test } from "node:test";
import assert from "node:assert/strict";

import {
  buildWatchlistMemoPayload,
  candidateStatusLabel,
  candidateMatchesTaskGroup,
  candidateTaskGroupLabel,
  candidateToComparisonItem,
  countTaskGroups,
  formatCandidateMetric,
  isStarred,
  normalizeWatchlistItems,
  reviewDateAfter,
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
    {
      target_id: "a",
      target_type: "community",
      thesis: "收益稳定",
      candidate_tasks: [{ group: "due_review", label: "到期复核" }],
      candidate_triggers: [{ kind: "target_price_hit", label: "总价低于目标" }],
    },
    { target_id: "b", target_type: "building" },
    { target_id: "pudong", target_type: "district" },
  ]);

  assert.deepEqual(payload.targets, [
    { target_id: "a", target_type: "community" },
    { target_id: "b", target_type: "building" },
    { target_id: "pudong", target_type: "district" },
  ]);
  assert.equal(payload.candidate_contexts[0].thesis, "收益稳定");
  assert.deepEqual(payload.candidate_contexts[0].task_labels, ["到期复核"]);
  assert.deepEqual(payload.candidate_contexts[0].trigger_labels, ["总价低于目标"]);
});

test("labels and metric formatting are stable", () => {
  assert.equal(candidateStatusLabel("researching"), "复核中");
  assert.equal(targetTypeLabel("district"), "区");
  assert.equal(formatCandidateMetric(4.234, "%"), "4.23%");
  assert.equal(formatCandidateMetric(780, "万"), "780万");
  assert.equal(formatCandidateMetric(null, "%"), "—");
});

test("task grouping helpers count and match candidate queues", () => {
  const items = [
    {
      target_id: "a",
      target_type: "community",
      candidate_tasks: [{ group: "due_review", label: "到期复核" }],
    },
    {
      target_id: "b",
      target_type: "building",
      status: "shortlisted",
      candidate_tasks: [{ group: "target_rule", label: "目标触发" }],
    },
  ];
  const counts = countTaskGroups(items);
  assert.equal(counts.all, 2);
  assert.equal(counts.due_review, 1);
  assert.equal(counts.target_rule, 1);
  assert.equal(counts.shortlisted, 1);
  assert.equal(candidateMatchesTaskGroup(items[0], "due_review"), true);
  assert.equal(candidateMatchesTaskGroup(items[0], "shortlisted"), false);
  assert.equal(candidateTaskGroupLabel("evidence_missing"), "证据缺口");
});

test("reviewDateAfter returns yyyy-mm-dd", () => {
  assert.equal(reviewDateAfter(7, new Date("2026-05-05T00:00:00Z")), "2026-05-12");
});
