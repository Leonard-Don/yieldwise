# Phase 6g — Hover Micro-Animations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wrap the spec's Phase 6 visual-detail trio (滚动阴影 / 骨架屏 / hover 微动画) — the first two shipped in 6c. This phase adds: a board row left-bar slide-in on hover that mirrors the existing `aria-selected` indicator, smooth `transition` properties on every clickable user-platform element that didn't already animate, and a unified hover-press shadow on mode chips + drawer star + filter chip clear button so they feel "live" instead of static.

**Architecture:** Pure CSS edits across five existing user-platform stylesheets. No JS, no markup, no new tests. The change is additive — every rule already had `cursor: pointer` or a `:hover` selector; we add `transition` properties and tighten the hover delta so the user feels feedback. Strategy is consistency: pick one duration (`120ms`) and one easing (`ease-out`) and apply across the user platform. The board row gets one structural addition — a `transparent` 2px left-bar that animates to `var(--up)` on hover, harmonising with the existing `aria-selected` 2px green left-bar.

**Tech Stack:** Vanilla CSS only. No new dependencies, no new tests (visual change; existing 123 pytest + 100 node tests are the regression net).

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 7 Phase 6: 视觉细节（滚动阴影、骨架屏、hover 微动画）— last unfilled item)

**Prior plan:** 2026-04-26-phase-6f-district-alerts.md (merged at `b9f1913`)

---

## File Structure (Phase 6g outcome)

```
frontend/user/styles/
├── shell.css                        # MODIFIED: mode chip transition + filter chip clear hover
├── board.css                        # MODIFIED: board row left-bar slide-in
├── drawer.css                       # MODIFIED: star button + close button transitions; community row tighter
├── search.css                       # MODIFIED: search row hover transition
└── alerts.css                       # MODIFIED: banner toggle/mark button transitions

README.md                            # MODIFIED: bump Phase 6f → Phase 6g
```

**Out-of-scope (deferred):**
- Layout-level animations (mode-switch transitions, drawer slide refinements) — current `180ms transform` already feels right; over-tweaking risks jank
- Reduced-motion handling (`@media (prefers-reduced-motion)`) — single-user dev tool; can ship if the user requests it
- New tests — visual change; existing test suites + manual smoke are the regression net
- Manual browser screenshot

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-6g-hover-microanimations .worktrees/phase-6g-hover-microanimations
cd .worktrees/phase-6g-hover-microanimations
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs tests/frontend/test_search_helpers.mjs
ATLAS_ENABLE_DEMO_MOCK=1 python3 scripts/phase1_smoke.py
```

Expected: 123 pytest passed; 100 node tests passed; 21 smoke routes OK.

---

### Task 1: Board row hover slide-in + mode chip + filter chip clear

**Files:**
- Modify: `frontend/user/styles/shell.css`
- Modify: `frontend/user/styles/board.css`

`shell.css` already has the mode chip rules; we add a `transition` property and a small hover-press shadow. `shell.css` also has filter chip + filter chip clear button — we add transitions and refine the clear-button hover. `board.css` has `.atlas-board-row` with `:hover` background change and `[aria-selected="true"]` left-bar — we add a transparent 2px left-bar that becomes `var(--up)` on hover, animating in.

- [ ] **Step 1: Update `frontend/user/styles/shell.css`**

Open the file. Find the existing mode chip rule:

```css
.atlas-mode-chip {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 4px 10px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color 80ms ease, border-color 80ms ease, background 80ms ease;
}
```

Replace with:

```css
.atlas-mode-chip {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 4px 10px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color 120ms ease-out, border-color 120ms ease-out,
    background 120ms ease-out, transform 120ms ease-out, box-shadow 120ms ease-out;
}

.atlas-mode-chip:hover:not([aria-pressed="true"]) {
  color: var(--text-0);
  border-color: var(--up);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 214, 143, 0.12);
}

.atlas-mode-chip:active {
  transform: translateY(0);
  box-shadow: none;
}
```

Find the existing `.atlas-filter-chip-clear` rule:

```css
.atlas-filter-chip-clear {
  appearance: none;
  border: none;
  background: transparent;
  color: var(--text-dim);
  font: inherit;
  font-size: 12px;
  line-height: 1;
  padding: 0 2px;
  cursor: pointer;
}

.atlas-filter-chip-clear:hover {
  color: var(--down);
}
```

Replace with:

```css
.atlas-filter-chip-clear {
  appearance: none;
  border: none;
  background: transparent;
  color: var(--text-dim);
  font: inherit;
  font-size: 12px;
  line-height: 1;
  padding: 0 2px;
  cursor: pointer;
  transition: color 120ms ease-out, transform 120ms ease-out;
}

.atlas-filter-chip-clear:hover {
  color: var(--down);
  transform: scale(1.15);
}
```

Find the existing `.atlas-prefs-button` rule:

```css
.atlas-prefs-button {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 4px 10px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.08em;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.atlas-prefs-button:hover {
  color: var(--text-0);
  border-color: var(--up);
}
```

Replace with:

```css
.atlas-prefs-button {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 4px 10px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.08em;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color 120ms ease-out, border-color 120ms ease-out,
    background 120ms ease-out;
}

.atlas-prefs-button:hover {
  color: var(--text-0);
  border-color: var(--up);
  background: rgba(0, 214, 143, 0.06);
}
```

Find the existing `.atlas-help-chip` rule:

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

Replace with:

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
  transition: color 120ms ease-out, border-color 120ms ease-out,
    background 120ms ease-out, transform 120ms ease-out;
}

.atlas-help-chip:hover {
  color: var(--text-0);
  border-color: var(--up);
  background: rgba(0, 214, 143, 0.06);
  transform: scale(1.08);
}
```

- [ ] **Step 2: Update `frontend/user/styles/board.css`**

Find the existing `.atlas-board-row` rule:

```css
.atlas-board-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 10px;
  align-items: baseline;
  padding: 8px 14px;
  border-bottom: 1px solid var(--line);
  cursor: pointer;
  transition: background 80ms ease;
}

.atlas-board-row:hover {
  background: var(--bg-2);
}

.atlas-board-row[aria-selected="true"] {
  background: rgba(0, 214, 143, 0.06);
  border-left: 2px solid var(--up);
  padding-left: 12px;
}
```

Replace with:

```css
.atlas-board-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 10px;
  align-items: baseline;
  padding: 8px 14px;
  border-bottom: 1px solid var(--line);
  border-left: 2px solid transparent;
  cursor: pointer;
  transition: background 120ms ease-out, border-left-color 120ms ease-out,
    padding-left 120ms ease-out;
}

.atlas-board-row:hover {
  background: var(--bg-2);
  border-left-color: rgba(0, 214, 143, 0.5);
  padding-left: 12px;
}

.atlas-board-row[aria-selected="true"] {
  background: rgba(0, 214, 143, 0.06);
  border-left-color: var(--up);
  padding-left: 12px;
}
```

Note: the row now permanently has a 2px transparent left-border so the hover and selected states animate the COLOR, not the border existence — that prevents a 2px reflow when hovering.

- [ ] **Step 3: Sanity-check**

Run: `pytest -q` → 123 passed.

Run combined node tests: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs tests/frontend/test_search_helpers.mjs` → 100 passed.

- [ ] **Step 4: Commit**

```bash
git add frontend/user/styles/shell.css frontend/user/styles/board.css
git commit -m "feat(user): hover transitions for chips + board row left-bar slide-in"
```

---

### Task 2: Drawer + search + alerts banner button transitions

**Files:**
- Modify: `frontend/user/styles/drawer.css`
- Modify: `frontend/user/styles/search.css`
- Modify: `frontend/user/styles/alerts.css`

The drawer's close + star buttons, the search overlay close + row hover, and the alerts banner's toggle + mark buttons all benefit from transition + small lift.

- [ ] **Step 1: Update `frontend/user/styles/drawer.css`**

Find the existing `.atlas-drawer-close` rule:

```css
.atlas-drawer-close {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  font: inherit;
  font-size: 11px;
  width: 22px;
  height: 22px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  line-height: 1;
}

.atlas-drawer-close:hover {
  color: var(--text-0);
  border-color: var(--up);
}
```

Replace with:

```css
.atlas-drawer-close {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  font: inherit;
  font-size: 11px;
  width: 22px;
  height: 22px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  line-height: 1;
  transition: color 120ms ease-out, border-color 120ms ease-out,
    background 120ms ease-out, transform 120ms ease-out;
}

.atlas-drawer-close:hover {
  color: var(--down);
  border-color: var(--down);
  background: rgba(255, 77, 77, 0.08);
  transform: rotate(90deg);
}
```

Find the existing `.atlas-drawer-star` rule and its variants:

```css
.atlas-drawer-star {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  font: inherit;
  font-size: 14px;
  width: 28px;
  height: 22px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  line-height: 1;
}

.atlas-drawer-star[aria-pressed="true"] {
  color: var(--warn);
  border-color: var(--warn);
  background: rgba(255, 176, 32, 0.08);
}

.atlas-drawer-star:hover {
  color: var(--warn);
}

.atlas-drawer-star[disabled] {
  opacity: 0.5;
  cursor: progress;
}
```

Replace with:

```css
.atlas-drawer-star {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  font: inherit;
  font-size: 14px;
  width: 28px;
  height: 22px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  line-height: 1;
  transition: color 120ms ease-out, border-color 120ms ease-out,
    background 120ms ease-out, transform 120ms ease-out;
}

.atlas-drawer-star[aria-pressed="true"] {
  color: var(--warn);
  border-color: var(--warn);
  background: rgba(255, 176, 32, 0.08);
}

.atlas-drawer-star:hover {
  color: var(--warn);
  transform: scale(1.12);
}

.atlas-drawer-star:active {
  transform: scale(0.94);
}

.atlas-drawer-star[disabled] {
  opacity: 0.5;
  cursor: progress;
  transform: none;
}
```

Find the existing `.atlas-note-actions button` rules:

```css
.atlas-note-actions button {
  appearance: none;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--text-dim);
  padding: 2px 8px;
  font: inherit;
  font-size: 10px;
  letter-spacing: 0.06em;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.atlas-note-actions button:hover {
  color: var(--text-0);
  border-color: var(--up);
}

.atlas-note-actions button[data-variant="danger"]:hover {
  color: var(--down);
  border-color: var(--down);
}
```

Replace with:

```css
.atlas-note-actions button {
  appearance: none;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--text-dim);
  padding: 2px 8px;
  font: inherit;
  font-size: 10px;
  letter-spacing: 0.06em;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color 120ms ease-out, border-color 120ms ease-out,
    background 120ms ease-out;
}

.atlas-note-actions button:hover {
  color: var(--text-0);
  border-color: var(--up);
  background: rgba(0, 214, 143, 0.06);
}

.atlas-note-actions button[data-variant="danger"]:hover {
  color: var(--down);
  border-color: var(--down);
  background: rgba(255, 77, 77, 0.06);
}
```

Find the existing `.atlas-district-row` rule:

```css
.atlas-district-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, auto) minmax(0, auto);
  align-items: baseline;
  gap: 10px;
  padding: 6px 8px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color 80ms ease, background 80ms ease;
}

.atlas-district-row:hover {
  border-color: var(--up);
  background: rgba(0, 214, 143, 0.08);
}
```

Replace with (just lengthen the transition to match the rest of the platform):

```css
.atlas-district-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, auto) minmax(0, auto);
  align-items: baseline;
  gap: 10px;
  padding: 6px 8px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color 120ms ease-out, background 120ms ease-out,
    transform 120ms ease-out;
}

.atlas-district-row:hover {
  border-color: var(--up);
  background: rgba(0, 214, 143, 0.08);
  transform: translateX(2px);
}
```

- [ ] **Step 2: Update `frontend/user/styles/search.css`**

Find the existing `.atlas-search-row` rule and hover variants:

```css
.atlas-search-row {
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--text-0);
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.atlas-search-row:hover,
.atlas-search-row[aria-selected="true"] {
  background: var(--bg-2);
  outline: 1px solid var(--up);
  outline-offset: -1px;
}
```

Replace with:

```css
.atlas-search-row {
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--text-0);
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  outline: 1px solid transparent;
  outline-offset: -1px;
  transition: background 120ms ease-out, outline-color 120ms ease-out,
    transform 120ms ease-out;
}

.atlas-search-row:hover,
.atlas-search-row[aria-selected="true"] {
  background: var(--bg-2);
  outline-color: var(--up);
  transform: translateX(2px);
}
```

Find the existing `.atlas-search-close` rule:

```css
.atlas-search-close {
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
```

Replace with:

```css
.atlas-search-close {
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
  transition: color 120ms ease-out, border-color 120ms ease-out,
    background 120ms ease-out, transform 120ms ease-out;
}

.atlas-search-close:hover {
  color: var(--down);
  border-color: var(--down);
  background: rgba(255, 77, 77, 0.08);
  transform: rotate(90deg);
}
```

- [ ] **Step 3: Update `frontend/user/styles/alerts.css`**

Find the existing `.atlas-banner-toggle, .atlas-banner-mark` rules:

```css
.atlas-banner-toggle,
.atlas-banner-mark {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 3px 10px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.06em;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.atlas-banner-toggle:hover,
.atlas-banner-mark:hover {
  color: var(--text-0);
  border-color: var(--warn);
}
```

Replace with:

```css
.atlas-banner-toggle,
.atlas-banner-mark {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 3px 10px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.06em;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color 120ms ease-out, border-color 120ms ease-out,
    background 120ms ease-out, transform 120ms ease-out;
}

.atlas-banner-toggle:hover,
.atlas-banner-mark:hover {
  color: var(--text-0);
  border-color: var(--warn);
  transform: translateY(-1px);
}

.atlas-banner-toggle:active,
.atlas-banner-mark:active {
  transform: translateY(0);
}
```

Find the existing `.atlas-banner-row` rule:

```css
.atlas-banner-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 2fr);
  gap: 10px;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  align-items: baseline;
  padding: 4px 0;
  border-bottom: 1px solid var(--line);
}
```

Replace with (subtle row-level hover so the alerts feel touchable):

```css
.atlas-banner-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 2fr);
  gap: 10px;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  align-items: baseline;
  padding: 4px 6px;
  border-bottom: 1px solid var(--line);
  border-radius: var(--radius-sm);
  transition: background 120ms ease-out;
}

.atlas-banner-row:hover {
  background: rgba(255, 176, 32, 0.06);
}
```

- [ ] **Step 4: Sanity-check**

Run: `pytest -q` → 123 passed.

Run combined node tests → 100 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/styles/drawer.css frontend/user/styles/search.css frontend/user/styles/alerts.css
git commit -m "feat(user): drawer/search/banner button transitions + lift effects"
```

---

### Task 3: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Edit `README.md`**

Find `## 路由布局（Phase 6f 起）` and change to `## 路由布局（Phase 6g 起）`. The `/` row description doesn't change — hover polish is below the granularity of a top-level feature mention.

- [ ] **Step 2: Verify all exit criteria**

Run each:
- `pytest -q` → 123 passed
- `node --test ...` (11 frontend test files) → 100 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `ATLAS_ENABLE_DEMO_MOCK=1 python3 scripts/phase1_smoke.py` → 21 OK
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: bump phase 6f → 6g (hover transitions)"
```

---

## Phase 6g Exit Criteria

- [ ] `pytest -q` — 123 passed (no backend changes)
- [ ] `node --test ...` — 100 passed (no test changes)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check`
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `ATLAS_ENABLE_DEMO_MOCK=1 python3 scripts/phase1_smoke.py` — 21 rows OK
- [ ] Manual: with `uvicorn api.main:app --port 8013` running, hovering a board row slides in a 2px green left-bar from transparent → `var(--up)` over 120ms while the row background fades to `var(--bg-2)`. Hovering a mode chip lifts it 1px with a subtle green glow. The drawer × close button rotates 90° on hover with a red-tinted background. Pressing the ★ button scales it down briefly, releases scaled up. None of the existing functionality regresses.
- [ ] `git log --oneline b9f1913..HEAD` shows exactly 3 commits

## Out of Scope (deferred)

- Reduced-motion support (`prefers-reduced-motion`)
- Layout-level transitions (mode-switch sweep, drawer slide refinements)
- Manual browser screenshot
