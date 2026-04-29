import { test } from "node:test";
import assert from "node:assert/strict";

// Mirror of escapeHTML from frontend/admin/admin.js
function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

test("escapeHTML escapes ampersand and angle brackets", () => {
  assert.equal(escapeHTML("<script>alert(1)</script>"), "&lt;script&gt;alert(1)&lt;/script&gt;");
  assert.equal(escapeHTML("a & b"), "a &amp; b");
});

test("escapeHTML escapes quotes", () => {
  assert.equal(escapeHTML(`"x"`), "&quot;x&quot;");
  assert.equal(escapeHTML("'x'"), "&#39;x&#39;");
});

test("escapeHTML coerces non-strings", () => {
  assert.equal(escapeHTML(42), "42");
  assert.equal(escapeHTML(null), "null");
});
