import { test } from "node:test";
import assert from "node:assert/strict";

// Mirror of escapeHTML from frontend/admin/customer-data.js
function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

test("escapeHTML escapes XSS-relevant chars", () => {
  assert.equal(escapeHTML("<img src=x onerror=alert(1)>"), "&lt;img src=x onerror=alert(1)&gt;");
  assert.equal(escapeHTML(`"';&`), "&quot;&#39;;&amp;");
});

test("escapeHTML coerces non-strings", () => {
  assert.equal(escapeHTML(42), "42");
  assert.equal(escapeHTML(null), "null");
});

test("escapeHTML round-trips ascii safe", () => {
  assert.equal(escapeHTML("hello world"), "hello world");
  assert.equal(escapeHTML(""), "");
});
