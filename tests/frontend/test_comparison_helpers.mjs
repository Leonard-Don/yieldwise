import { test } from "node:test";
import assert from "node:assert/strict";

import {
  addComparisonItem,
  buildDecisionMemoPayload,
  candidateFromItem,
  candidateFromSelection,
  comparisonCount,
  isCompared,
  normalizeComparisonItems,
  removeComparisonItem,
} from "../../frontend/user/modules/comparison-helpers.js";

test("normalizeComparisonItems: drops invalid rows and dedupes", () => {
  const rows = normalizeComparisonItems([
    { target_id: "a", target_type: "community", target_name: "A" },
    { target_id: "a", target_type: "community", target_name: "A duplicate" },
    { target_id: "b", target_type: "unknown" },
    null,
  ]);

  assert.equal(rows.length, 1);
  assert.equal(rows[0].target_id, "a");
});

test("add/remove/isCompared keep a stable comparison list", () => {
  const first = { target_id: "a", target_type: "community", target_name: "A" };
  const second = { target_id: "b", target_type: "building", target_name: "B" };
  const added = addComparisonItem([first], second);

  assert.equal(comparisonCount(added), 2);
  assert.equal(isCompared(added, "b", "building"), true);
  assert.deepEqual(removeComparisonItem(added, "a", "community").map((item) => item.target_id), ["b"]);
});

test("candidateFromItem: city mode creates a district target", () => {
  const candidate = candidateFromItem(
    { id: "pudong", name: "浦东新区", yield: 4.2, score: 88 },
    "city",
  );

  assert.equal(candidate.target_type, "district");
  assert.equal(candidate.target_id, "pudong");
  assert.equal(candidate.yield_pct, 4.2);
});

test("candidateFromItem: yield mode creates a community target with quality", () => {
  const candidate = candidateFromItem(
    {
      id: "x",
      name: "小区 X",
      districtName: "浦东新区",
      yield: 4.2,
      score: 88,
      quality: { status: "usable", label: "可用", sampleLabel: "售 4 / 租 5" },
    },
    "yield",
  );

  assert.equal(candidate.target_type, "community");
  assert.equal(candidate.quality_status, "usable");
  assert.equal(candidate.sample_label, "售 4 / 租 5");
});

test("candidateFromSelection: supports building/community/district selections", () => {
  const candidate = candidateFromSelection({
    type: "building",
    id: "b1",
    props: { name: "1号楼", communityName: "小区", yieldAvg: 4.5 },
  });

  assert.equal(candidate.target_type, "building");
  assert.equal(candidate.target_name, "1号楼");
  assert.equal(candidate.yield_pct, 4.5);
});

test("buildDecisionMemoPayload: maps comparison rows to API targets", () => {
  const payload = buildDecisionMemoPayload([
    { target_id: "a", target_type: "community", target_name: "A" },
    { target_id: "b", target_type: "building", target_name: "B" },
  ]);

  assert.deepEqual(payload, {
    targets: [
      { target_id: "a", target_type: "community" },
      { target_id: "b", target_type: "building" },
    ],
  });
});
