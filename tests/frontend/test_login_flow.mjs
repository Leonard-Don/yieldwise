import { test } from "node:test";
import assert from "node:assert/strict";

// We test the URL-validation logic by importing it. Since login.js attaches
// to the DOM on import, we extract the safe-redirect helper to a separate
// pure module if testing it inline becomes too DOM-coupled. For v0.2, the
// helper inside login.js is intentionally inline; this test verifies the
// allowed/rejected paths via a mirrored function.
//
// NOTE: this duplicates the helper in frontend/login/login.js rather than
// importing it (login.js has DOM side-effects on import). Keep both copies
// in sync. A cleaner long-term approach is to extract `pickNext` to
// frontend/login/helpers.js and import from both — out of scope for D.1.

function pickNext(query) {
  const params = new URLSearchParams(query);
  const next = params.get("next");
  if (next && next.startsWith("/") && !next.startsWith("//")) return next;
  return "/";
}

test("pickNext accepts same-origin paths", () => {
  assert.equal(pickNext("?next=/backstage/"), "/backstage/");
  assert.equal(pickNext("?next=/admin/users"), "/admin/users");
});

test("pickNext rejects external URLs and protocol-relative URLs", () => {
  assert.equal(pickNext("?next=//evil.example/"), "/");
  assert.equal(pickNext("?next=https://evil.example/"), "/");
  assert.equal(pickNext("?next="), "/");
  assert.equal(pickNext(""), "/");
});
