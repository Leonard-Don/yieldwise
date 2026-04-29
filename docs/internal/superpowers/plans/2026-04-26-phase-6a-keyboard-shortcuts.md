# Phase 6a — Keyboard Shortcuts + Help Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up the keyboard shortcuts the spec calls for: ⌘1/⌘2/⌘3 (mode switch), F (toggle ★ on the active selection), N (focus the notes input), and `?` (toggle a help overlay listing all shortcuts). A small `?` chip in the topbar opens the same overlay for discoverability.

**Architecture:** Pure frontend addition. A new `frontend/user/modules/shortcuts.js` registers a single global `keydown` listener. Pure dispatch logic lives in `shortcuts-helpers.js` (`parseShortcut(event)` returns one of `"yield"|"home"|"city"|"star"|"note"|"help"|null` after filtering input/textarea targets) so it can be unit-tested without a DOM. The DOM module looks up the action via that helper, then dispatches: mode switches go through the existing store + URL sync (Phase 2b shell.js), star toggles inline-call `api.watchlist.add/remove` with optimistic state writes (mirrors `watchlist.js`'s pattern), note focus does `querySelector('[data-role="notes-add-input"]').focus()`, and help toggles a `state.helpOpen` slice that drives a new modal mount.

**Tech Stack:** Vanilla JS (browser-native ES modules) · `node:test` for the parseShortcut helper · existing `/api/v2/watchlist` endpoints (Phase 4a) · existing store and modules. No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 7 Phase 6: 键盘快捷键：⌘K 搜索、⌘1/2/3 切模式、F 加关注、N 写笔记)

**Prior plan:** 2026-04-24-phase-5b-alerts-banner.md (merged at `80114c9`)

---

## File Structure (Phase 6a outcome)

```
frontend/user/
├── index.html                       # MODIFIED: add help overlay mount + topbar ? chip
├── styles/
│   ├── shell.css                    # MODIFIED: ? chip styling
│   └── shortcuts.css                # NEW
└── modules/
    ├── shortcuts-helpers.js         # NEW — parseShortcut(event) pure dispatch
    ├── shortcuts.js                 # NEW — DOM module: keydown listener + actions + help overlay
    └── main.js                      # MODIFIED: state.helpOpen slice + initShortcuts wiring

tests/frontend/
└── test_shortcuts_helpers.mjs       # NEW (~9 cases)

scripts/phase1_smoke.py              # MODIFIED: +1 row asserting help overlay mount
README.md                            # MODIFIED: bump Phase 5b → Phase 6a
```

**Out-of-scope (deferred):**
- ⌘K global search — needs a target index (buildings + communities + districts) and an autocomplete UI; spec lists it but it's a separate substantial feature. Phase 6b later.
- Edit-mode shortcuts inside notes (e.g. ⌘+Enter to save) — out of scope; existing 保存/取消 buttons work
- Customizable / user-defined shortcuts — out of scope (single-user)
- Shortcuts on the backstage UI — Phase 6a only touches `frontend/user/`
- View-state mirror, commute minutes, street aggregation, scroll shadows / skeleton screens — separate Phase 6 sub-plans
- Manual browser screenshot

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-6a-keyboard-shortcuts .worktrees/phase-6a-keyboard-shortcuts
cd .worktrees/phase-6a-keyboard-shortcuts
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 90 pytest passed; 73 node tests passed; 18 smoke routes OK.

---

### Task 1: parseShortcut helper + tests

**Files:**
- Create: `frontend/user/modules/shortcuts-helpers.js`
- Create: `tests/frontend/test_shortcuts_helpers.mjs`

The helper takes a synthetic event-like `{key, code, metaKey, ctrlKey, shiftKey, altKey, target}` and returns one of `"yield"`, `"home"`, `"city"`, `"star"`, `"note"`, `"help"`, or `null`. Filtering rules:
- Returns `null` when `target` is an `INPUT` / `TEXTAREA` / `SELECT` / `[contenteditable]` element. (`target.tagName` and `target.isContentEditable` are read.) The mode switch (⌘+digit) is the **one exception** that fires regardless of the focus context — the user always wants ⌘1 to switch mode, even from inside a textarea.
- Returns `null` for `?` and unmodified letter keys when any modifier (`metaKey`/`ctrlKey`/`altKey`) is held — those are reserved for browser shortcuts.
- ⌘1/⌘2/⌘3 → `"yield"` / `"home"` / `"city"` (accepts both `metaKey` and `ctrlKey` so Linux/Windows users aren't locked out).
- `f` (no modifier) → `"star"`
- `n` (no modifier) → `"note"`
- `?` (Shift+/) — reads `event.key === "?"` directly (browsers report it that way) → `"help"`

- [ ] **Step 1: Write the failing tests**

Write `tests/frontend/test_shortcuts_helpers.mjs`:

```javascript
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
```

- [ ] **Step 2: Verify failing**

Run: `node --test tests/frontend/test_shortcuts_helpers.mjs`
Expected: ERR_MODULE_NOT_FOUND.

- [ ] **Step 3: Implement `frontend/user/modules/shortcuts-helpers.js`**

```javascript
const MODE_BY_DIGIT = { "1": "yield", "2": "home", "3": "city" };

function isEditableTarget(target) {
  if (!target) return false;
  const tag = (target.tagName || "").toUpperCase();
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (target.isContentEditable) return true;
  return false;
}

export function parseShortcut(event) {
  if (!event) return null;
  const { key, metaKey, ctrlKey, altKey, target } = event;
  const modKey = metaKey || ctrlKey;

  // Mode switch is privileged: works even when typing in a form field.
  if (modKey && !altKey && Object.prototype.hasOwnProperty.call(MODE_BY_DIGIT, key)) {
    return MODE_BY_DIGIT[key];
  }

  // All other shortcuts are suppressed inside editable targets.
  if (isEditableTarget(target)) return null;

  // Modifier-bearing letters are reserved for the browser (Cmd+F / Ctrl+N etc.).
  if (modKey || altKey) return null;

  if (key === "?") return "help";

  const lower = typeof key === "string" ? key.toLowerCase() : "";
  if (lower === "f") return "star";
  if (lower === "n") return "note";

  return null;
}
```

- [ ] **Step 4: Verify passing**

Run: `node --test tests/frontend/test_shortcuts_helpers.mjs`
Expected: 11 tests passed (10 unique tests; one test asserts both Meta + Ctrl variants).

Run: `node --check frontend/user/modules/shortcuts-helpers.js`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/shortcuts-helpers.js tests/frontend/test_shortcuts_helpers.mjs
git commit -m "feat(user): add parseShortcut dispatch helper"
```

---

### Task 2: Help overlay mount + CSS

**Files:**
- Modify: `frontend/user/index.html`
- Modify: `frontend/user/styles/shell.css`
- Create: `frontend/user/styles/shortcuts.css`

The overlay is a small modal that lists the shortcuts. It mounts inside `<main class="atlas-main">` (same scope as the drawer + onboarding modal) so it doesn't cover the topbar. A `?` chip in the topbar opens it for users who haven't discovered the keyboard hint.

- [ ] **Step 1: Add the topbar `?` chip + help overlay markup to `frontend/user/index.html`**

Open `frontend/user/index.html`. Find the topbar (after Phase 4a it has the ★ chip + 偏好 button + runtime tag). Find:

```html
        <span class="atlas-star-tag mono" data-component="watchlist-count" title="关注数">★ —</span>
        <button type="button" class="atlas-prefs-button" data-component="prefs-button">偏好</button>
        <span class="atlas-runtime-tag mono dim" data-component="runtime-tag"></span>
```

Insert a new `?` chip between the prefs button and the runtime tag:

```html
        <span class="atlas-star-tag mono" data-component="watchlist-count" title="关注数">★ —</span>
        <button type="button" class="atlas-prefs-button" data-component="prefs-button">偏好</button>
        <button type="button" class="atlas-help-chip" data-component="help-chip" title="键盘快捷键 (?)">?</button>
        <span class="atlas-runtime-tag mono dim" data-component="runtime-tag"></span>
```

Add the `shortcuts.css` link directly after the `alerts.css` link (around line 14):

```html
    <link rel="stylesheet" href="/styles/shortcuts.css" />
```

Inside `<main class="atlas-main">` (existing — sibling of drawer + onboarding), insert the help overlay markup directly before the `</main>` close (alongside the drawer-backdrop and onboarding sections that are already inside main):

```html
        <div class="atlas-help-backdrop" data-component="help-backdrop" data-open="false"></div>
        <section class="atlas-help" data-component="help-overlay" data-open="false" aria-hidden="true" aria-labelledby="atlas-help-title">
          <header class="atlas-help-header">
            <h2 id="atlas-help-title" class="atlas-help-title">键盘快捷键</h2>
            <button type="button" class="atlas-help-close" data-role="help-close" aria-label="关闭">×</button>
          </header>
          <dl class="atlas-help-list">
            <dt><kbd>⌘1</kbd> / <kbd>⌃1</kbd></dt><dd>切换到收益猎手模式</dd>
            <dt><kbd>⌘2</kbd> / <kbd>⌃2</kbd></dt><dd>切换到自住找房模式</dd>
            <dt><kbd>⌘3</kbd> / <kbd>⌃3</kbd></dt><dd>切换到全市观察模式</dd>
            <dt><kbd>F</kbd></dt><dd>把当前抽屉里的楼栋/小区加入或移出关注夹</dd>
            <dt><kbd>N</kbd></dt><dd>聚焦笔记输入框</dd>
            <dt><kbd>?</kbd></dt><dd>切换本帮助面板</dd>
            <dt><kbd>Esc</kbd></dt><dd>关闭抽屉 / 模态 / 帮助面板</dd>
          </dl>
        </section>
```

- [ ] **Step 2: Append `?` chip styling to `frontend/user/styles/shell.css`**

Open `frontend/user/styles/shell.css` and append at the end:

```css
.atlas-help-chip {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  width: 22px;
  height: 22px;
  font: inherit;
  font-size: 12px;
  line-height: 1;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.atlas-help-chip:hover {
  color: var(--text-0);
  border-color: var(--up);
}
```

- [ ] **Step 3: Create `frontend/user/styles/shortcuts.css`**

```css
.atlas-help {
  position: absolute;
  inset: 32px 32px;
  margin: auto;
  width: min(420px, 100%);
  max-height: calc(100% - 64px);
  background: var(--bg-1);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55);
  z-index: 8;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  opacity: 0;
  transform: translateY(8px);
  pointer-events: none;
  transition: opacity 160ms ease, transform 160ms ease;
}

.atlas-help[data-open="true"] {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.atlas-help-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(7, 10, 16, 0.55);
  z-index: 7;
  opacity: 0;
  pointer-events: none;
  transition: opacity 160ms ease;
}

.atlas-help-backdrop[data-open="true"] {
  opacity: 1;
  pointer-events: auto;
}

.atlas-help-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
}

.atlas-help-title {
  margin: 0;
  font-size: 13px;
  letter-spacing: 0.06em;
}

.atlas-help-close {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  width: 22px;
  height: 22px;
  border-radius: var(--radius-sm);
  font: inherit;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
}

.atlas-help-list {
  margin: 0;
  padding: 12px 16px 16px;
  display: grid;
  grid-template-columns: minmax(0, auto) minmax(0, 1fr);
  gap: 8px 16px;
  overflow-y: auto;
}

.atlas-help-list dt {
  margin: 0;
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  align-items: center;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--text-dim);
}

.atlas-help-list dd {
  margin: 0;
  font-size: 12px;
  color: var(--text-0);
}

.atlas-help-list kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  padding: 2px 6px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-0);
}
```

- [ ] **Step 4: Sanity-check**

Run: `grep -c 'data-component="help-overlay"' frontend/user/index.html`
Expected: 1.

Run: `grep -c 'data-component="help-chip"' frontend/user/index.html`
Expected: 1.

Run: `grep -c 'href="/styles/shortcuts.css"' frontend/user/index.html`
Expected: 1.

Run: `pytest -q`
Expected: 90 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/index.html frontend/user/styles/shell.css frontend/user/styles/shortcuts.css
git commit -m "feat(user): add help overlay mount + topbar ? chip"
```

---

### Task 3: shortcuts.js DOM module

**Files:**
- Create: `frontend/user/modules/shortcuts.js`

The module:
- Installs a single `keydown` listener on `document` and dispatches via `parseShortcut`
- Wires the topbar `?` chip + the help overlay's close button + backdrop click + Esc
- Subscribes to `state.helpOpen` (a new boolean slice) to drive overlay visibility — keeps the overlay state-driven for consistency with onboarding/drawer
- Mode actions: set `state.mode` AND update URL via `history.replaceState` (mirrors shell.js's setMode)
- Star action: when `state.selection` is a building/community, optimistically toggle `state.watchlist` and call `api.watchlist.add/remove`; on error refetch via `api.watchlist.list`
- Note action: query `[data-role="notes-add-input"]` and call `.focus()` if visible
- Help action: toggle `state.helpOpen`

- [ ] **Step 1: Implement `frontend/user/modules/shortcuts.js`**

```javascript
import { api } from "./api.js";
import { parseShortcut } from "./shortcuts-helpers.js";

const VALID_MODES = new Set(["yield", "home", "city"]);

export function initShortcuts({ root, store }) {
  const overlay = root.querySelector('[data-component="help-overlay"]');
  const backdrop = root.querySelector('[data-component="help-backdrop"]');
  const closeBtn = overlay.querySelector('[data-role="help-close"]');
  const chipBtn = root.querySelector('[data-component="help-chip"]');

  document.addEventListener("keydown", handleKeyDown);
  closeBtn.addEventListener("click", () => store.set({ helpOpen: false }));
  backdrop.addEventListener("click", () => store.set({ helpOpen: false }));
  if (chipBtn) {
    chipBtn.addEventListener("click", () => {
      store.set({ helpOpen: !store.get().helpOpen });
    });
  }

  store.subscribe(renderOverlay);
  renderOverlay(store.get());

  function renderOverlay(state) {
    const open = !!state.helpOpen;
    overlay.dataset.open = open ? "true" : "false";
    backdrop.dataset.open = open ? "true" : "false";
    overlay.setAttribute("aria-hidden", open ? "false" : "true");
  }

  function handleKeyDown(event) {
    // Esc always closes the help overlay if it's open. Other Esc semantics
    // (drawer / onboarding) are owned by their own modules.
    if (event.key === "Escape" && store.get().helpOpen) {
      event.preventDefault();
      store.set({ helpOpen: false });
      return;
    }
    const action = parseShortcut(event);
    if (!action) return;
    event.preventDefault();
    if (VALID_MODES.has(action)) {
      switchMode(action);
    } else if (action === "star") {
      void toggleStar();
    } else if (action === "note") {
      focusNoteInput();
    } else if (action === "help") {
      store.set({ helpOpen: !store.get().helpOpen });
    }
  }

  function switchMode(modeId) {
    if (store.get().mode === modeId) return;
    store.set({ mode: modeId });
    const params = new URLSearchParams(window.location.search);
    params.set("mode", modeId);
    window.history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
  }

  function focusNoteInput() {
    const input = root.querySelector('[data-role="notes-add-input"]');
    if (!input) return;
    input.focus();
  }

  async function toggleStar() {
    const state = store.get();
    const sel = state.selection;
    if (!sel || (sel.type !== "building" && sel.type !== "community")) return;
    const items = Array.isArray(state.watchlist) ? state.watchlist : [];
    const isStarred = items.some((it) => it.target_id === sel.id);
    try {
      if (isStarred) {
        const next = items.filter((it) => it.target_id !== sel.id);
        store.set({ watchlist: next });
        await api.watchlist.remove(sel.id);
      } else {
        const optimistic = {
          target_id: sel.id,
          target_type: sel.type,
          added_at: new Date().toISOString().slice(0, 19),
          last_seen_snapshot: null,
        };
        store.set({ watchlist: [...items, optimistic] });
        const saved = await api.watchlist.add(sel.id, sel.type);
        const merged = store
          .get()
          .watchlist.map((it) => (it.target_id === sel.id ? saved : it));
        store.set({ watchlist: merged });
      }
    } catch (err) {
      console.error("[atlas:shortcuts] star toggle failed", err);
      try {
        const fresh = await api.watchlist.list();
        store.set({ watchlist: fresh.items || [] });
      } catch (refetchErr) {
        console.error("[atlas:shortcuts] watchlist refetch failed", refetchErr);
      }
    }
  }
}
```

- [ ] **Step 2: Verify**

Run: `node --check frontend/user/modules/shortcuts.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs`
Expected: 84 passed (5 + 20 + 11 + 6 + 9 + 5 + 4 + 5 + 8 + 11).

Run: `pytest -q`
Expected: 90 passed.

- [ ] **Step 3: Commit**

```bash
git add frontend/user/modules/shortcuts.js
git commit -m "feat(user): add shortcuts DOM module (mode/star/note/help dispatch)"
```

---

### Task 4: Bootstrap + smoke + README

**Files:**
- Modify: `frontend/user/modules/main.js`
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Update `frontend/user/modules/main.js`**

Open the file. Find the import block. After `import { initAlerts } from "./alerts.js";` add:

```javascript
import { initShortcuts } from "./shortcuts.js";
```

Find the `createStore({...})` call. After `alerts: { items: [], last_open_at: null },` add:

```javascript
    helpOpen: false,
```

So the createStore call ends with `helpOpen: false,` as its last entry.

Find the existing `initAlerts({ root, store });` line and add the shortcuts init directly below it:

```javascript
  initShortcuts({ root, store });
```

- [ ] **Step 2: Verify the module compiles**

Run: `node --check frontend/user/modules/main.js`
Expected: exit 0.

- [ ] **Step 3: Extend `scripts/phase1_smoke.py`**

Open `scripts/phase1_smoke.py`. Find the line that asserts `data-component="onboarding"` or `data-component="drawer"`:

```python
            (f"{base}/", 'data-component="drawer"'),
```

Add directly below it:

```python
            (f"{base}/", 'data-component="help-overlay"'),
```

- [ ] **Step 4: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 19 OK, exit 0.

- [ ] **Step 5: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 5b 起）` and change to `## 路由布局（Phase 6a 起）`.

Find the row whose third column starts with `用户平台。`. Replace its description with:

```markdown
用户平台。收益模式 + 详情抽屉 + 筛选条 + 自住模式 + 全市模式 + 关注夹（★）+ 笔记 + 变化横幅 + 键盘快捷键（⌘1/2/3 切模式、F 关注、N 笔记、? 帮助）。
```

- [ ] **Step 6: Verify all exit criteria**

Run each:
- `pytest -q` → 90 passed (no backend changes)
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs` → 84 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 19 OK
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/main.js scripts/phase1_smoke.py README.md
git commit -m "feat(user): wire shortcuts into bootstrap + smoke + docs"
```

---

## Phase 6a Exit Criteria

- [ ] `pytest -q` — 90 passed (no backend changes)
- [ ] `node --test ...` — 84 passed (5 state + 20 modes + 11 drawer + 6 storage + 9 filter helpers + 5 user-prefs helpers + 4 watchlist helpers + 5 annotations helpers + 8 alerts helpers + 11 shortcuts helpers)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check`
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 19 rows OK
- [ ] Manual: `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` — open `/?mode=yield`, press `?` → help overlay appears with the 7-row shortcut list. Press Esc → overlay closes. Press ⌘2 → mode switches to home, URL updates to `?mode=home`. Add a building to the watchlist via the drawer ★, then press F while drawer is open → toggles the star (visible in topbar count change). Press N when drawer is open → focus moves to the notes textarea.
- [ ] `git log --oneline 80114c9..HEAD` shows exactly 4 commits

## Out of Scope (deferred)

- ⌘K global search — needs target index + autocomplete UI
- Edit-mode shortcuts (⌘+Enter to save inside notes)
- View-state mirror, commute minutes, street aggregation, scroll shadows / skeleton screens
- Customizable shortcuts
- Manual browser screenshot
