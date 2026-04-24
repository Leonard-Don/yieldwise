import { test } from "node:test";
import assert from "node:assert/strict";

import { createStorage } from "../../frontend/user/modules/storage.js";

function makeFakeLocalStorage(initial = {}) {
  const data = { ...initial };
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
    },
    setItem(key, value) {
      data[key] = String(value);
    },
    removeItem(key) {
      delete data[key];
    },
    _data: data,
  };
}

test("createStorage: read returns parsed JSON when present", () => {
  const fake = makeFakeLocalStorage({ "atlas:filters": '{"yield":{"minYield":4}}' });
  const store = createStorage("atlas:filters", { backend: fake });
  assert.deepEqual(store.read(), { yield: { minYield: 4 } });
});

test("createStorage: read returns null when key missing", () => {
  const fake = makeFakeLocalStorage();
  const store = createStorage("atlas:filters", { backend: fake });
  assert.equal(store.read(), null);
});

test("createStorage: read returns null when JSON is corrupt", () => {
  const fake = makeFakeLocalStorage({ "atlas:filters": "{not valid json" });
  const store = createStorage("atlas:filters", { backend: fake });
  assert.equal(store.read(), null);
});

test("createStorage: write serializes and stores", () => {
  const fake = makeFakeLocalStorage();
  const store = createStorage("atlas:filters", { backend: fake });
  store.write({ yield: { minYield: 4.5 } });
  assert.equal(fake._data["atlas:filters"], '{"yield":{"minYield":4.5}}');
});

test("createStorage: write swallows backend errors gracefully", () => {
  const failing = {
    getItem: () => null,
    setItem: () => {
      throw new Error("QuotaExceededError");
    },
    removeItem: () => {},
  };
  const store = createStorage("atlas:filters", { backend: failing });
  // Must not throw.
  store.write({ yield: { minYield: 4 } });
});

test("createStorage: clear removes the key", () => {
  const fake = makeFakeLocalStorage({ "atlas:filters": "{}" });
  const store = createStorage("atlas:filters", { backend: fake });
  store.clear();
  assert.equal(fake.getItem("atlas:filters"), null);
});
