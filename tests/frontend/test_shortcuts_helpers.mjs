import { test } from "node:test";
import assert from "node:assert/strict";

import { parseShortcut } from "../../frontend/user/modules/shortcuts-helpers.js";

function makeEvent(overrides = {}) {
  return {
    key: "",
    metaKey: false,
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    target: { tagName: "DIV", isContentEditable: false },
    ...overrides,
  };
}

test("parseShortcut: ⌘1 → yield", () => {
  assert.equal(parseShortcut(makeEvent({ key: "1", metaKey: true })), "yield");
  assert.equal(parseShortcut(makeEvent({ key: "1", ctrlKey: true })), "yield");
});

test("parseShortcut: ⌘2 → home, ⌘3 → city", () => {
  assert.equal(parseShortcut(makeEvent({ key: "2", metaKey: true })), "home");
  assert.equal(parseShortcut(makeEvent({ key: "3", ctrlKey: true })), "city");
});

test("parseShortcut: bare digits without modifier → null", () => {
  assert.equal(parseShortcut(makeEvent({ key: "1" })), null);
  assert.equal(parseShortcut(makeEvent({ key: "2" })), null);
});

test("parseShortcut: f → star, n → note", () => {
  assert.equal(parseShortcut(makeEvent({ key: "f" })), "star");
  assert.equal(parseShortcut(makeEvent({ key: "n" })), "note");
});

test("parseShortcut: F (uppercase) and N (uppercase) also work", () => {
  assert.equal(parseShortcut(makeEvent({ key: "F", shiftKey: true })), "star");
  assert.equal(parseShortcut(makeEvent({ key: "N", shiftKey: true })), "note");
});

test("parseShortcut: f with Cmd modifier → null (browser bookmark)", () => {
  assert.equal(parseShortcut(makeEvent({ key: "f", metaKey: true })), null);
  assert.equal(parseShortcut(makeEvent({ key: "n", ctrlKey: true })), null);
});

test("parseShortcut: ? (Shift+/) → help", () => {
  assert.equal(parseShortcut(makeEvent({ key: "?", shiftKey: true })), "help");
});

test("parseShortcut: typing in INPUT/TEXTAREA suppresses letter shortcuts", () => {
  assert.equal(
    parseShortcut(makeEvent({ key: "f", target: { tagName: "INPUT", isContentEditable: false } })),
    null,
  );
  assert.equal(
    parseShortcut(makeEvent({ key: "n", target: { tagName: "TEXTAREA", isContentEditable: false } })),
    null,
  );
  assert.equal(
    parseShortcut(makeEvent({ key: "?", shiftKey: true, target: { tagName: "INPUT", isContentEditable: false } })),
    null,
  );
});

test("parseShortcut: ⌘1 still works inside a textarea (mode switch is privileged)", () => {
  const action = parseShortcut(
    makeEvent({ key: "1", metaKey: true, target: { tagName: "TEXTAREA", isContentEditable: false } }),
  );
  assert.equal(action, "yield");
});

test("parseShortcut: contenteditable target suppresses letter shortcuts", () => {
  assert.equal(
    parseShortcut(
      makeEvent({ key: "f", target: { tagName: "DIV", isContentEditable: true } }),
    ),
    null,
  );
});

test("parseShortcut: unrecognised key → null", () => {
  assert.equal(parseShortcut(makeEvent({ key: "x" })), null);
  assert.equal(parseShortcut(makeEvent({ key: "Enter" })), null);
});
