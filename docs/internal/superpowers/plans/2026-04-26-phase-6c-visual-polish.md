# Phase 6c — Visual Polish (Scroll Shadows + Drawer Skeleton) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two visual polish items the spec lists for Phase 6: (1) edge-fading scroll shadows on every scrollable container so content is hinted at instead of hard-clipping, and (2) a shimmer skeleton placeholder inside the detail drawer body that mirrors the eventual KPI / floor chart / listing summary layout while the per-target detail is in flight.

**Architecture:** Pure CSS + a one-line frontend change. A new shared `.atlas-scroll-shadow` utility class uses the Lea-Verou technique adapted for the dark D1 palette: four stacked backgrounds — two `var(--bg-0)` covers attached `local`, two darker shadow gradients attached `scroll` — produce edge fades that disappear when the user scrolls to the start/end. Applied to the opportunity board list, drawer body, notes list, help overlay list, and onboarding form (all the places where overflow-y: auto already lives).

For the skeleton, `detail-drawer.js`'s `renderLoading` swaps the bare "加载详情中…" status line for a structured placeholder built from new `.atlas-skeleton-*` CSS rules. The placeholder mirrors the post-load DOM (3 KPI shimmer cards, 1 floor-chart shimmer block, 2 listing shimmer cells) so when `renderDetail` overwrites the body the layout doesn't reflow.

**Tech Stack:** Vanilla CSS · vanilla JS (one function body change in detail-drawer.js). No new dependencies, no new tests (visual-only change; existing 95 pytest + 85 node tests remain the regression net).

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 7 Phase 6: 视觉细节（滚动阴影、骨架屏、hover 微动画）)

**Prior plan:** 2026-04-26-phase-6b-alerts-target-names.md (merged at `134a668`)

---

## File Structure (Phase 6c outcome)

```
frontend/user/
├── styles/
│   ├── shell.css                    # MODIFIED: add shared .atlas-scroll-shadow utility + .atlas-skeleton-* rules
│   ├── board.css                    # MODIFIED: opportunity board list uses scroll-shadow
│   ├── drawer.css                   # MODIFIED: drawer body + notes list use scroll-shadow
│   ├── shortcuts.css                # MODIFIED: help list uses scroll-shadow
│   └── onboarding.css               # MODIFIED: onboarding form uses scroll-shadow
└── modules/
    └── detail-drawer.js             # MODIFIED: renderLoading emits skeleton markup

README.md                            # MODIFIED: bump Phase 6b → Phase 6c
```

**Out-of-scope (deferred):**
- Hover micro-animations beyond what's already shipped — existing hovers (board row, mode chip, drawer star, filter chip clear) already animate cleanly. Refining them further is gold-plating.
- Skeleton states for the board, the map, or the alerts banner — only the drawer is touched here. The board's "暂无机会" empty-state flashes briefly but it's already short-lived; map needs AMap and is out of scope; banner appears post-fetch with real data.
- Theme toggle (light/dark) — spec section 9 lists this as a fallback for D1 strain, never required in main scope.
- New tests — visual styling can't be regression-tested via node:test or pytest in this codebase; we lean on `node --check` and visual smoke captures.
- Manual browser screenshot capture — controller will run it after merge.

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-6c-visual-polish .worktrees/phase-6c-visual-polish
cd .worktrees/phase-6c-visual-polish
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 95 pytest passed; 85 node tests passed; 19 smoke routes OK.

---

### Task 1: Shared `.atlas-scroll-shadow` utility + skeleton rules

**Files:**
- Modify: `frontend/user/styles/shell.css`

We add two utility blocks at the end of `shell.css`: the scroll-shadow rule (using Lea-Verou's four-background technique adapted for the D1 dark palette) and a tiny set of skeleton building blocks (`.atlas-skeleton-row`, `.atlas-skeleton-card`, `.atlas-skeleton-block`) that pulse via a single keyframes animation.

The shadow technique:
- Two `var(--bg-0)` cover gradients attached `local` produce solid edges when the scroll is at top/bottom.
- Two darker radial gradients attached `scroll` produce shadow stripes that emerge as the user scrolls into the middle.
- The cover gradients overlap the shadow gradients so when there's nothing to scroll, no shadow shows.

- [ ] **Step 1: Append to `frontend/user/styles/shell.css`**

The scroll-shadow recipe lives inline at each scrollable container in Task 2 (we don't re-write any HTML to add a shared class). Here we only add the skeleton building blocks that the drawer's `renderLoading` will use in Task 3.

```css
@keyframes atlas-skeleton-pulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 0.95; }
}

.atlas-skeleton-row,
.atlas-skeleton-card,
.atlas-skeleton-block {
  background: linear-gradient(90deg, var(--bg-2), var(--line), var(--bg-2));
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: atlas-skeleton-pulse 1.4s ease-in-out infinite;
}

.atlas-skeleton-row {
  height: 12px;
  margin-bottom: 6px;
}

.atlas-skeleton-card {
  height: 48px;
}

.atlas-skeleton-block {
  height: 80px;
}

.atlas-skeleton-grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

.atlas-skeleton-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.atlas-skeleton-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.atlas-skeleton-label {
  height: 8px;
  width: 60px;
  background: var(--line);
  border-radius: var(--radius-sm);
  margin-bottom: 4px;
  opacity: 0.5;
}
```

- [ ] **Step 2: Sanity-check**

The CSS file is non-executable; the only "compile" check is that the file is well-formed. Run:

```
grep -c '.atlas-skeleton-card' frontend/user/styles/shell.css
```

Expected: 1.

Run: `pytest -q` → 95 passed (no backend touched).

- [ ] **Step 3: Commit**

```bash
git add frontend/user/styles/shell.css
git commit -m "feat(user): add skeleton building blocks for drawer loading state"
```

---

### Task 2: Apply scroll-shadow to scrollable containers

**Files:**
- Modify: `frontend/user/styles/board.css`
- Modify: `frontend/user/styles/drawer.css`
- Modify: `frontend/user/styles/shortcuts.css`
- Modify: `frontend/user/styles/onboarding.css`

Five containers already have `overflow-y: auto`. Each gets the shadow utility applied via `composes`-equivalent: rather than introducing a build step, we add the same background + size declarations directly under each existing rule. This keeps everything inline and the cascade obvious.

To avoid duplicating 10+ lines per file, we lean on a CSS technique: each rule that already does `overflow-y: auto` gets ONE additional declaration — `background-attachment: local, local, scroll, scroll;` — and a `background-image` shorthand. The four-layer trick from Task 1 lives in `shell.css` as `.atlas-scroll-shadow`; we apply that class to each scrollable HTML element where natural — but the markup for the board / drawer / notes / help / onboarding is already locked. Rather than re-writing every Phase 4-5 module to add a class name, we bind the visual effect directly to the existing class selectors so no markup changes are required.

- [ ] **Step 1: Update `frontend/user/styles/board.css`**

Find the existing rule:

```css
.atlas-board-list {
  margin: 0;
  padding: 0;
  list-style: none;
}
```

Wait — the board list itself doesn't scroll; the parent `.atlas-board` does. Find:

```css
.atlas-board {
  background: var(--bg-0);
  overflow-y: auto;
}
```

That's actually in `shell.css`. Re-open `frontend/user/styles/shell.css` and find:

```css
.atlas-board {
  background: var(--bg-0);
  overflow-y: auto;
}
```

Replace with:

```css
.atlas-board {
  overflow-y: auto;
  background:
    linear-gradient(var(--bg-0) 30%, transparent),
    linear-gradient(transparent, var(--bg-0) 70%) 0 100%,
    radial-gradient(farthest-side at 50% 0, rgba(0, 0, 0, 0.45), transparent),
    radial-gradient(farthest-side at 50% 100%, rgba(0, 0, 0, 0.45), transparent) 0 100%;
  background-repeat: no-repeat;
  background-color: var(--bg-0);
  background-size: 100% 28px, 100% 28px, 100% 10px, 100% 10px;
  background-attachment: local, local, scroll, scroll;
}
```

The `background:` shorthand replaces the previous `background: var(--bg-0);` declaration. The `background-color: var(--bg-0);` separate declaration is the fallback for browsers (or scroll positions) where the gradients haven't applied. `board.css` itself does not need changes for this task.

- [ ] **Step 2: Update `frontend/user/styles/drawer.css`** — drawer body

Find:

```css
.atlas-drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
```

Replace with:

```css
.atlas-drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background:
    linear-gradient(var(--bg-1) 30%, transparent),
    linear-gradient(transparent, var(--bg-1) 70%) 0 100%,
    radial-gradient(farthest-side at 50% 0, rgba(0, 0, 0, 0.45), transparent),
    radial-gradient(farthest-side at 50% 100%, rgba(0, 0, 0, 0.45), transparent) 0 100%;
  background-repeat: no-repeat;
  background-color: var(--bg-1);
  background-size: 100% 22px, 100% 22px, 100% 8px, 100% 8px;
  background-attachment: local, local, scroll, scroll;
}
```

(Drawer body's surrounding chrome is `var(--bg-1)`, hence the cover uses `--bg-1` not `--bg-0`.)

- [ ] **Step 3: Update `frontend/user/styles/drawer.css`** — notes section

Find:

```css
.atlas-drawer-notes {
  border-top: 1px solid var(--line);
  padding: 12px 14px;
  max-height: 240px;
  overflow-y: auto;
  background: var(--bg-1);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
```

Replace with:

```css
.atlas-drawer-notes {
  border-top: 1px solid var(--line);
  padding: 12px 14px;
  max-height: 240px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background:
    linear-gradient(var(--bg-1) 30%, transparent),
    linear-gradient(transparent, var(--bg-1) 70%) 0 100%,
    radial-gradient(farthest-side at 50% 0, rgba(0, 0, 0, 0.45), transparent),
    radial-gradient(farthest-side at 50% 100%, rgba(0, 0, 0, 0.45), transparent) 0 100%;
  background-repeat: no-repeat;
  background-color: var(--bg-1);
  background-size: 100% 22px, 100% 22px, 100% 8px, 100% 8px;
  background-attachment: local, local, scroll, scroll;
}
```

- [ ] **Step 4: Update `frontend/user/styles/shortcuts.css`** — help list

Find:

```css
.atlas-help-list {
  margin: 0;
  padding: 12px 16px 16px;
  display: grid;
  grid-template-columns: minmax(0, auto) minmax(0, 1fr);
  gap: 8px 16px;
  overflow-y: auto;
}
```

Replace with:

```css
.atlas-help-list {
  margin: 0;
  padding: 12px 16px 16px;
  display: grid;
  grid-template-columns: minmax(0, auto) minmax(0, 1fr);
  gap: 8px 16px;
  overflow-y: auto;
  background:
    linear-gradient(var(--bg-1) 30%, transparent),
    linear-gradient(transparent, var(--bg-1) 70%) 0 100%,
    radial-gradient(farthest-side at 50% 0, rgba(0, 0, 0, 0.45), transparent),
    radial-gradient(farthest-side at 50% 100%, rgba(0, 0, 0, 0.45), transparent) 0 100%;
  background-repeat: no-repeat;
  background-color: var(--bg-1);
  background-size: 100% 18px, 100% 18px, 100% 8px, 100% 8px;
  background-attachment: local, local, scroll, scroll;
}
```

- [ ] **Step 5: Update `frontend/user/styles/onboarding.css`** — form scroll

Find:

```css
.atlas-onboarding-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 16px 16px;
  overflow-y: auto;
}
```

Replace with:

```css
.atlas-onboarding-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 16px 16px;
  overflow-y: auto;
  background:
    linear-gradient(var(--bg-1) 30%, transparent),
    linear-gradient(transparent, var(--bg-1) 70%) 0 100%,
    radial-gradient(farthest-side at 50% 0, rgba(0, 0, 0, 0.45), transparent),
    radial-gradient(farthest-side at 50% 100%, rgba(0, 0, 0, 0.45), transparent) 0 100%;
  background-repeat: no-repeat;
  background-color: var(--bg-1);
  background-size: 100% 22px, 100% 22px, 100% 8px, 100% 8px;
  background-attachment: local, local, scroll, scroll;
}
```

- [ ] **Step 6: Sanity-check**

Run: `pytest -q` → 95 passed.

Run combined node tests: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs` → 85 passed.

Run: `python3 scripts/phase1_smoke.py` → 19 OK.

- [ ] **Step 7: Commit**

```bash
git add frontend/user/styles/shell.css frontend/user/styles/drawer.css frontend/user/styles/shortcuts.css frontend/user/styles/onboarding.css
git commit -m "feat(user): apply scroll-shadow to board / drawer / notes / help / onboarding"
```

---

### Task 3: Drawer skeleton placeholder

**Files:**
- Modify: `frontend/user/modules/detail-drawer.js`

Replace `renderLoading`'s plain `<div class="atlas-drawer-status">加载详情中…</div>` with a structured skeleton that mirrors the post-load layout: a 3-cell KPI grid, a single floor-chart block, and a 2-cell listing summary grid.

The skeleton uses the building blocks added in Task 1 (`.atlas-skeleton-card`, `.atlas-skeleton-block`, `.atlas-skeleton-grid-3`, `.atlas-skeleton-grid-2`, `.atlas-skeleton-section`, `.atlas-skeleton-label`).

- [ ] **Step 1: Update `frontend/user/modules/detail-drawer.js`**

Find the existing `renderLoading` function:

```javascript
  function renderLoading(sel) {
    titleEl.textContent = sel.props?.name || sel.props?.communityName || sel.id;
    subtitleEl.textContent = (sel.type || "").toUpperCase();
    bodyEl.innerHTML = '<div class="atlas-drawer-status">加载详情中…</div>';
  }
```

Replace with:

```javascript
  function renderLoading(sel) {
    titleEl.textContent = sel.props?.name || sel.props?.communityName || sel.id;
    subtitleEl.textContent = (sel.type || "").toUpperCase();
    bodyEl.innerHTML = `<div class="atlas-skeleton-section"><div class="atlas-skeleton-label"></div><div class="atlas-skeleton-grid-3"><div class="atlas-skeleton-card"></div><div class="atlas-skeleton-card"></div><div class="atlas-skeleton-card"></div></div></div><div class="atlas-skeleton-section"><div class="atlas-skeleton-label"></div><div class="atlas-skeleton-block"></div></div><div class="atlas-skeleton-section"><div class="atlas-skeleton-label"></div><div class="atlas-skeleton-grid-2"><div class="atlas-skeleton-card"></div><div class="atlas-skeleton-card"></div></div></div>`;
  }
```

- [ ] **Step 2: Sanity-check**

Run: `node --check frontend/user/modules/detail-drawer.js`
Expected: exit 0.

Run: `pytest -q` → 95 passed.

Run combined node tests → 85 passed (no test changes; the existing detail-drawer integration is exercised through manual smoke).

- [ ] **Step 3: Commit**

```bash
git add frontend/user/modules/detail-drawer.js
git commit -m "feat(user): replace drawer loading text with shimmer skeleton"
```

---

### Task 4: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Edit `README.md`**

Find `## 路由布局（Phase 6b 起）` and change to `## 路由布局（Phase 6c 起）`. The `/` row description doesn't change in this phase — visual polish doesn't add a new feature visible from a one-line description.

- [ ] **Step 2: Verify all exit criteria**

Run each:
- `pytest -q` → 95 passed
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs` → 85 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 19 OK
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: bump phase 6b → 6c (scroll shadows + skeleton)"
```

---

## Phase 6c Exit Criteria

- [ ] `pytest -q` — 95 passed (no backend changes)
- [ ] `node --test ...` — 85 passed (no test changes)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check`
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 19 rows OK
- [ ] Manual: open `http://127.0.0.1:8013/?mode=yield`, scroll the opportunity board down — top edge fades into shadow as scroll position leaves the start; scroll back to top — shadow disappears. Click a board row, drawer opens — for the brief moment before fetch resolves, the drawer body shows a 3-cell shimmer KPI row + 1-block floor chart placeholder + 2-cell listing placeholder, all pulsing. After data loads the layout doesn't shift visibly because skeleton dimensions match.
- [ ] `git log --oneline 134a668..HEAD` shows exactly 4 commits

## Out of Scope (deferred)

- Hover micro-animations beyond the existing ones (gold-plating)
- Skeleton states for the board / map / banner
- Theme toggle (light/dark)
- New tests (visual change; existing test suites are the regression net)
- Manual browser screenshot — controller will run the visual smoke
