import { test } from "node:test";
import assert from "node:assert/strict";

import {
  sortByCreatedDesc,
  targetKey,
} from "../../frontend/user/modules/annotations-helpers.js";

test("sortByCreatedDesc: empty/null input → []", () => {
  assert.deepEqual(sortByCreatedDesc([]), []);
  assert.deepEqual(sortByCreatedDesc(null), []);
  assert.deepEqual(sortByCreatedDesc(undefined), []);
});

test("sortByCreatedDesc: orders newest first", () => {
  const items = [
    { note_id: "a", created_at: "2026-04-20T10:00:00" },
    { note_id: "b", created_at: "2026-04-24T10:00:00" },
    { note_id: "c", created_at: "2026-04-22T10:00:00" },
  ];
  const sorted = sortByCreatedDesc(items);
  assert.deepEqual(sorted.map((it) => it.note_id), ["b", "c", "a"]);
});

test("sortByCreatedDesc: items without created_at sort to the end", () => {
  const items = [
    { note_id: "a", created_at: "2026-04-22T10:00:00" },
    { note_id: "b" },
    { note_id: "c", created_at: "2026-04-24T10:00:00" },
  ];
  const sorted = sortByCreatedDesc(items);
  assert.equal(sorted[0].note_id, "c");
  assert.equal(sorted[2].note_id, "b");
});

test("targetKey: null/non-building-or-community → null", () => {
  assert.equal(targetKey(null), null);
  assert.equal(targetKey({ type: "district", id: "pudong" }), null);
  assert.equal(targetKey({ type: "floor", id: "x" }), null);
});

test("targetKey: building/community → id", () => {
  assert.equal(targetKey({ type: "building", id: "b1" }), "b1");
  assert.equal(targetKey({ type: "community", id: "c2" }), "c2");
});
