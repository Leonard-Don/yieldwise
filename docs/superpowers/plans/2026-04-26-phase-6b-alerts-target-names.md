# Phase 6b — Alerts Banner Target Name Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the raw `target_id` shown for each alert in the change banner (e.g. `daning-jinmaofu-b1`) with the human-readable name resolved server-side from the building/community record (e.g. `1号楼`). The frontend gets a `target_name` field on every Alert and renders that with a graceful `target_id` fallback.

**Architecture:** Backend-only change, plus a one-line frontend tweak. `_snapshot()` in `api/domains/alerts.py` already calls `service.get_building` / `service.get_community` for diff input — it just needs to additionally include the `name` field in the snapshot dict. `compute_alerts` in `api/domains/alerts_diff.py` reads the snapshot's `name` and threads it onto each emitted Alert via a new optional `target_name: str | None` field on the schema. The frontend's `alerts.js` swaps `alert.target_id` for `alert.target_name || alert.target_id` in the row renderer.

**Tech Stack:** FastAPI · Pydantic 2.9 · existing `service.get_building`/`get_community` · existing `compute_alerts` pure function · vanilla JS. No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 5 row 1 "变化横幅" — "关注对象的变化摘要" requires recognisable target identification)

**Prior plan:** 2026-04-26-phase-6a-keyboard-shortcuts.md (merged at `b7b46d6`)

---

## File Structure (Phase 6b outcome)

```
api/
├── schemas/
│   └── alerts.py                    # MODIFIED: Alert gains target_name field
└── domains/
    ├── alerts.py                    # MODIFIED: _snapshot returns name
    └── alerts_diff.py               # MODIFIED: _alert + _diff_target carry name through

frontend/user/modules/
└── alerts.js                        # MODIFIED: renderRow uses target_name with fallback

tests/api/
├── test_alerts_schema.py            # MODIFIED: +1 case for target_name
├── test_alerts_diff.py              # MODIFIED: +1 case for name passthrough
└── test_v2_alerts.py                # MODIFIED: +1 case asserting real mock name surfaces

README.md                            # MODIFIED: bump Phase 6a → Phase 6b row description
```

**Out-of-scope (deferred):**
- ⌘K global search (separate feature, separate plan).
- Resolving names for districts, floors, listings — schema accepts those target_types but Phase 5a alerts only cover building/community, so only those two need name resolution today.
- A target-name cache or batch lookup endpoint — `_snapshot` already does the per-target lookup as part of the diff; no new fetches are added.
- `last_seen_snapshot` populated with name on `mark-seen` — not required (the baseline doesn't need names; only emitted alerts do).
- Manual browser screenshot.

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-6b-alerts-target-names .worktrees/phase-6b-alerts-target-names
cd .worktrees/phase-6b-alerts-target-names
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 90 pytest passed; 85 node tests passed (5 + 20 + 11 + 6 + 9 + 5 + 4 + 5 + 8 + 12); 19 smoke routes OK.

---

### Task 1: Schema + diff carry target_name

**Files:**
- Modify: `api/schemas/alerts.py`
- Modify: `api/domains/alerts_diff.py`
- Modify: `tests/api/test_alerts_schema.py`
- Modify: `tests/api/test_alerts_diff.py`

We add `target_name: str | None = None` to `Alert`, then thread it through `_diff_target` and `_alert` in alerts_diff.py.

- [ ] **Step 1: Add the failing schema test**

Open `tests/api/test_alerts_schema.py`. Find the existing `test_alert_round_trip` test:

```python
def test_alert_round_trip() -> None:
    payload = {
        "target_id": "x",
        "target_type": "building",
        "kind": "yield_up",
        "from_value": 4.0,
        "to_value": 4.6,
        "delta": 0.6,
    }
    alert = Alert.model_validate(payload)
    assert alert.kind == "yield_up"
    assert alert.delta == 0.6
```

Add directly below it:

```python
def test_alert_round_trip_with_target_name() -> None:
    payload = {
        "target_id": "daning-jinmaofu-b1",
        "target_name": "1号楼",
        "target_type": "building",
        "kind": "yield_up",
        "from_value": 4.0,
        "to_value": 4.6,
        "delta": 0.6,
    }
    alert = Alert.model_validate(payload)
    assert alert.target_name == "1号楼"


def test_alert_target_name_defaults_to_none() -> None:
    alert = Alert.model_validate(
        {
            "target_id": "x",
            "target_type": "building",
            "kind": "yield_up",
            "from_value": 4.0,
            "to_value": 4.6,
            "delta": 0.6,
        }
    )
    assert alert.target_name is None
```

- [ ] **Step 2: Add the failing diff test**

Open `tests/api/test_alerts_diff.py`. Append at the end of the file:

```python
def test_compute_alerts_threads_target_name_from_snapshot() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": {"name": "1号楼", "yield": 4.6, "price": 800.0, "score": 60}},
        rules=AlertRules(),
    )
    assert len(items) == 1
    assert items[0].target_name == "1号楼"


def test_compute_alerts_target_name_none_when_snapshot_lacks_name() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": {"yield": 4.6, "price": 800.0, "score": 60}},
        rules=AlertRules(),
    )
    assert len(items) == 1
    assert items[0].target_name is None
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `pytest tests/api/test_alerts_schema.py tests/api/test_alerts_diff.py -v`
Expected: 4 new tests fail (`target_name` doesn't exist on `Alert`).

- [ ] **Step 4: Add `target_name` to the schema**

Open `api/schemas/alerts.py`. Find the `Alert` class:

```python
class Alert(BaseModel):
    """Single emitted change row."""

    model_config = ConfigDict(extra="ignore")

    target_id: str
    target_type: AlertTargetType
    kind: AlertKind
    from_value: float | None = None
    to_value: float | None = None
    delta: float | None = None
```

Add `target_name: str | None = None` directly after `target_id`:

```python
class Alert(BaseModel):
    """Single emitted change row."""

    model_config = ConfigDict(extra="ignore")

    target_id: str
    target_name: str | None = None
    target_type: AlertTargetType
    kind: AlertKind
    from_value: float | None = None
    to_value: float | None = None
    delta: float | None = None
```

- [ ] **Step 5: Thread the name through `alerts_diff.py`**

Open `api/domains/alerts_diff.py`. Find the `_diff_target` function. The current shape:

```python
def _diff_target(
    target_id: str,
    target_type: str,
    baseline: dict[str, Any],
    snapshot: dict[str, Any],
    rules: AlertRules,
) -> list[Alert]:
    out: list[Alert] = []

    base_yield = _normalize_yield(baseline.get("yield"))
    snap_yield = _normalize_yield(snapshot.get("yield"))
    if base_yield is not None and snap_yield is not None:
        delta = snap_yield - base_yield
        if delta >= rules.yield_delta_abs:
            out.append(_alert(target_id, target_type, "yield_up", base_yield, snap_yield, delta))
        elif -delta >= rules.yield_delta_abs:
            out.append(_alert(target_id, target_type, "yield_down", base_yield, snap_yield, delta))
    # ... (price + score branches similar)
```

Capture `name` once at the top of the function and pass it to every `_alert` call. Replace the function with:

```python
def _diff_target(
    target_id: str,
    target_type: str,
    baseline: dict[str, Any],
    snapshot: dict[str, Any],
    rules: AlertRules,
) -> list[Alert]:
    out: list[Alert] = []
    name_raw = snapshot.get("name")
    target_name = str(name_raw) if name_raw else None

    base_yield = _normalize_yield(baseline.get("yield"))
    snap_yield = _normalize_yield(snapshot.get("yield"))
    if base_yield is not None and snap_yield is not None:
        delta = snap_yield - base_yield
        if delta >= rules.yield_delta_abs:
            out.append(_alert(target_id, target_type, "yield_up", base_yield, snap_yield, delta, target_name))
        elif -delta >= rules.yield_delta_abs:
            out.append(_alert(target_id, target_type, "yield_down", base_yield, snap_yield, delta, target_name))

    base_price = _maybe_float(baseline.get("price"))
    snap_price = _maybe_float(snapshot.get("price"))
    if base_price is not None and snap_price is not None and base_price > 0:
        drop_pct = ((base_price - snap_price) / base_price) * 100.0
        if drop_pct >= rules.price_drop_pct:
            out.append(
                _alert(
                    target_id,
                    target_type,
                    "price_drop",
                    base_price,
                    snap_price,
                    snap_price - base_price,
                    target_name,
                )
            )

    base_score = _maybe_float(baseline.get("score"))
    snap_score = _maybe_float(snapshot.get("score"))
    if base_score is not None and snap_score is not None:
        delta = snap_score - base_score
        if abs(delta) >= rules.score_delta_abs:
            out.append(
                _alert(target_id, target_type, "score_jump", base_score, snap_score, delta, target_name)
            )

    return out
```

Find the existing `_alert` helper:

```python
def _alert(target_id: str, target_type: str, kind: str, base: float, snap: float, delta: float) -> Alert:
    return Alert(
        target_id=target_id,
        target_type=target_type,
        kind=kind,
        from_value=base,
        to_value=snap,
        delta=delta,
    )
```

Replace it with:

```python
def _alert(
    target_id: str,
    target_type: str,
    kind: str,
    base: float,
    snap: float,
    delta: float,
    target_name: str | None = None,
) -> Alert:
    return Alert(
        target_id=target_id,
        target_name=target_name,
        target_type=target_type,
        kind=kind,
        from_value=base,
        to_value=snap,
        delta=delta,
    )
```

- [ ] **Step 6: Run the tests**

Run: `pytest tests/api/test_alerts_schema.py tests/api/test_alerts_diff.py -v`
Expected: all schema and diff tests pass — 8 schema (6 prior + 2 new) + 12 diff (10 prior + 2 new).

Run: `pytest -q`
Expected: 94 passed (90 prior + 4 new).

Run: `python3 -m compileall api`
Expected: exit 0.

- [ ] **Step 7: Commit**

```bash
git add api/schemas/alerts.py api/domains/alerts_diff.py tests/api/test_alerts_schema.py tests/api/test_alerts_diff.py
git commit -m "feat(api): thread target_name through alerts diff"
```

---

### Task 2: Endpoint snapshot includes name + integration test

**Files:**
- Modify: `api/domains/alerts.py`
- Modify: `tests/api/test_v2_alerts.py`

`_snapshot()` already calls `service.get_building` / `service.get_community`. Both records have a `name` field (verified via probe — buildings expose `1号楼` etc., communities expose the full name e.g. `大宁金茂府`). Just include it.

- [ ] **Step 1: Add the failing integration test**

Open `tests/api/test_v2_alerts.py`. Append at the end of the file:

```python
def test_since_last_open_includes_target_name(
    client, isolated_personal_dir: Path
) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    state = {
        "baselines": {
            "zhangjiang-park-b1": {"yield": 1.0, "price": 100.0, "score": 30}
        },
        "last_open_at": "2026-04-20T10:00:00",
    }
    (isolated_personal_dir / "alerts_state.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    response = client.get("/api/v2/alerts/since-last-open").json()
    assert len(response["items"]) >= 1
    # Mock data exposes a building name (e.g. "A座") for zhangjiang-park-b1.
    for item in response["items"]:
        assert item["target_id"] == "zhangjiang-park-b1"
        # target_name is non-empty and distinct from the id
        assert item.get("target_name")
        assert item["target_name"] != item["target_id"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/api/test_v2_alerts.py::test_since_last_open_includes_target_name -v`
Expected: fail because `_snapshot` doesn't include `name`, so `target_name` ends up null.

- [ ] **Step 3: Update `_snapshot` in `api/domains/alerts.py`**

Open `api/domains/alerts.py`. Find the existing `_snapshot` function:

```python
def _snapshot(target_id: str, target_type: str) -> dict[str, Any] | None:
    if target_type == "building":
        record = get_building(target_id)
        if not record:
            return None
        return {
            "yield": record.get("yieldAvg"),
            "price": record.get("saleMedianWan"),
            "score": record.get("score"),
        }
    if target_type == "community":
        record = get_community(target_id)
        if not record:
            return None
        return {
            "yield": record.get("yield"),
            "price": record.get("avgPriceWan"),
            "score": record.get("score"),
        }
    return None
```

Replace with:

```python
def _snapshot(target_id: str, target_type: str) -> dict[str, Any] | None:
    if target_type == "building":
        record = get_building(target_id)
        if not record:
            return None
        return {
            "name": record.get("name"),
            "yield": record.get("yieldAvg"),
            "price": record.get("saleMedianWan"),
            "score": record.get("score"),
        }
    if target_type == "community":
        record = get_community(target_id)
        if not record:
            return None
        return {
            "name": record.get("name"),
            "yield": record.get("yield"),
            "price": record.get("avgPriceWan"),
            "score": record.get("score"),
        }
    return None
```

- [ ] **Step 4: Run the test**

Run: `pytest tests/api/test_v2_alerts.py -v`
Expected: 8 passed (7 prior + 1 new).

Run: `pytest -q`
Expected: 95 passed (94 prior + 1 new).

- [ ] **Step 5: Commit**

```bash
git add api/domains/alerts.py tests/api/test_v2_alerts.py
git commit -m "feat(api): /alerts/since-last-open returns target_name"
```

---

### Task 3: Frontend banner uses target_name + README

**Files:**
- Modify: `frontend/user/modules/alerts.js`
- Modify: `README.md`

The banner row currently does `alert.target_id`. Switch to `alert.target_name || alert.target_id`. No new tests since alerts.js is DOM-heavy; the data path is exercised by the backend integration test.

- [ ] **Step 1: Update `frontend/user/modules/alerts.js`**

Open the file. Find the existing `renderRow`:

```javascript
  function renderRow(alert) {
    const severity = severityFor(alert);
    return `<li class="atlas-banner-row" data-severity="${escapeAttr(severity)}"><span class="atlas-banner-target">${escapeText(alert.target_id || "")}</span><span class="atlas-banner-line">${escapeText(formatAlertLine(alert))}</span></li>`;
  }
```

Replace with:

```javascript
  function renderRow(alert) {
    const severity = severityFor(alert);
    const display = alert.target_name || alert.target_id || "";
    return `<li class="atlas-banner-row" data-severity="${escapeAttr(severity)}"><span class="atlas-banner-target" title="${escapeAttr(alert.target_id || "")}">${escapeText(display)}</span><span class="atlas-banner-line">${escapeText(formatAlertLine(alert))}</span></li>`;
  }
```

The `title` attribute keeps the raw `target_id` accessible on hover, so the user can still see the underlying id when needed.

- [ ] **Step 2: Verify the file compiles**

Run: `node --check frontend/user/modules/alerts.js`
Expected: exit 0.

Run combined node tests: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs`
Expected: 85 passed (no test changes in this task).

- [ ] **Step 3: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 6a 起）` and change to `## 路由布局（Phase 6b 起）`.

Find the row whose third column starts with `用户平台。`. Replace its description with:

```markdown
用户平台。收益模式 + 详情抽屉 + 筛选条 + 自住模式 + 全市模式 + 关注夹（★）+ 笔记 + 变化横幅（含目标名解析）+ 键盘快捷键（⌘1/2/3 切模式、F 关注、N 笔记、? 帮助）。
```

- [ ] **Step 4: Verify all exit criteria**

Run each:
- `pytest -q` → 95 passed
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs` → 85 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 19 OK (no smoke change in this phase)
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/alerts.js README.md
git commit -m "feat(user): banner shows resolved target name with id fallback"
```

---

## Phase 6b Exit Criteria

- [ ] `pytest -q` — 95 passed (90 prior + 2 schema + 2 diff + 1 v2)
- [ ] `node --test ...` — 85 passed (no frontend test changes)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check`
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 19 rows OK
- [ ] Manual: with `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` running, watchlist a real building (e.g. `zhangjiang-park-b1`), plant a stale baseline, then `curl http://127.0.0.1:8013/api/v2/alerts/since-last-open` — each item now has both `target_id` and `target_name`. Open `/?mode=yield`, expand the banner; rows show the human-readable name (`A座`) instead of the slug.
- [ ] `git log --oneline b7b46d6..HEAD` shows exactly 3 commits

## Out of Scope (deferred)

- ⌘K global search — separate plan
- Resolving names for districts / floors / listings (alerts only emit building/community in 5a)
- Target-name caching / batch lookup (per-target lookup is already in the diff path)
- Names persisted into `last_seen_snapshot` — baseline doesn't need them
- Manual browser screenshot
