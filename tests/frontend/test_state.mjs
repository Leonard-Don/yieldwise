import { test } from "node:test";
import assert from "node:assert/strict";

import { createStore } from "../../frontend/user/modules/state.js";

test("createStore: get returns initial state", () => {
  const store = createStore({ mode: "yield", count: 0 });
  assert.deepEqual(store.get(), { mode: "yield", count: 0 });
});

test("createStore: set merges patch and notifies subscribers", () => {
  const store = createStore({ mode: "yield", count: 0 });
  const calls = [];
  store.subscribe((state) => calls.push(state));
  store.set({ count: 1 });
  assert.deepEqual(store.get(), { mode: "yield", count: 1 });
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0], { mode: "yield", count: 1 });
});

test("createStore: set with no actual change does not notify", () => {
  const store = createStore({ mode: "yield", count: 0 });
  const calls = [];
  store.subscribe((state) => calls.push(state));
  store.set({ count: 0 });
  assert.equal(calls.length, 0);
});

test("createStore: subscribe returns an unsubscribe", () => {
  const store = createStore({ mode: "yield" });
  const calls = [];
  const off = store.subscribe((state) => calls.push(state));
  off();
  store.set({ mode: "home" });
  assert.equal(calls.length, 0);
});

test("createStore: select returns a derived value", () => {
  const store = createStore({ mode: "yield", filters: { minYield: 4 } });
  assert.equal(store.select((s) => s.filters.minYield), 4);
});
