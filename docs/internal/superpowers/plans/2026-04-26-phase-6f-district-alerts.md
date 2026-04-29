# Phase 6f — District-Level Alerts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the `district_delta_abs` rule (default 1.0 percentage points, shipped as a placeholder in Phase 5a) into actual alert emission. On `since-last-open`, also diff every Shanghai district's current avg yield vs the persisted baseline; on `mark-seen`, capture district baselines alongside watchlist baselines. The frontend banner already renders any kind of alert generically — this phase only adds two new `kind` values (`district_delta_up`, `district_delta_down`) plus the formatter.

**Architecture:** `AlertTargetType` Literal grows from `building | community` → `building | community | district`. `AlertKind` adds `district_delta_up` / `district_delta_down`. The pure `compute_alerts` gains a sibling internal helper `_diff_district` that emits one alert when `|current_yield - baseline_yield| ≥ rules.district_delta_abs`. The endpoint `/api/v2/alerts/since-last-open` now also walks every district from `service.list_districts()`, snapshots `{name, yield}`, and threads them in alongside watchlist snapshots; `/mark-seen` captures district baselines under the same `baselines` dict (district ids and watchlist target_ids share namespace, but the spec data has no overlap so this is safe). The frontend's `alerts-helpers.formatAlertLine` gains district branches; `severityFor` returns `up` / `down` per direction. No store-shape change.

**Tech Stack:** FastAPI · Pydantic 2.9 · existing `compute_alerts` pure function · `service.list_districts()` (already used by alerts.py for individual snapshots) · vanilla JS · `node:test`. No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 5 三模式语义 row "city: 区级指标跨 ±1%" + section 6 AlertRules schema with `district_delta_abs: 0.01`)

**Prior plan:** 2026-04-26-phase-6e-district-drawer.md (merged at `3e3eae3`)

---

## File Structure (Phase 6f outcome)

```
api/
├── schemas/
│   └── alerts.py                    # MODIFIED: AlertTargetType += "district"; AlertKind += district_delta_up/down
├── domains/
│   ├── alerts_diff.py               # MODIFIED: _diff_district helper; compute_alerts dispatch
│   └── alerts.py                    # MODIFIED: snapshot + mark-seen also handle districts

frontend/user/modules/
└── alerts-helpers.js                # MODIFIED: formatAlertLine + severityFor handle district_delta

tests/api/
├── test_alerts_schema.py            # MODIFIED: +1 case for district_delta literal
├── test_alerts_diff.py              # MODIFIED: +3 cases for district diffs
└── test_v2_alerts.py                # MODIFIED: +2 cases for districts in since-last-open + mark-seen

tests/frontend/
└── test_alerts_helpers.mjs          # MODIFIED: +2 cases for district_delta line + severity

scripts/phase1_smoke.py              # unchanged (existing alerts/* rows still cover the route)
README.md                            # MODIFIED: bump Phase 6e → Phase 6f
```

**Out-of-scope (deferred):**
- 挂牌量突变 (listing count change) per spec — needs listings endpoint that doesn't exist
- District-level alerts in the city-mode map (e.g. coloured ring around districts with active alerts) — frontend banner is the surface for this phase
- Per-district notes — schema's `target_type` Literal for annotations doesn't include "district"
- Streaming / cron alerts — endpoints stay pull-only per spec
- Manual browser screenshot

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-6f-district-alerts .worktrees/phase-6f-district-alerts
cd .worktrees/phase-6f-district-alerts
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs tests/frontend/test_search_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 117 pytest passed; 96 node tests passed; 21 smoke routes OK.

---

### Task 1: Schema extension + tests

**Files:**
- Modify: `api/schemas/alerts.py`
- Modify: `tests/api/test_alerts_schema.py`

`AlertTargetType` gains `"district"`. `AlertKind` gains `"district_delta_up"` and `"district_delta_down"`.

- [ ] **Step 1: Add the failing tests**

Open `tests/api/test_alerts_schema.py`. Append at the end:

```python
def test_alert_accepts_district_target_type() -> None:
    payload = {
        "target_id": "pudong",
        "target_name": "浦东新区",
        "target_type": "district",
        "kind": "district_delta_up",
        "from_value": 4.0,
        "to_value": 5.2,
        "delta": 1.2,
    }
    alert = Alert.model_validate(payload)
    assert alert.target_type == "district"
    assert alert.kind == "district_delta_up"
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_alerts_schema.py -v`
Expected: 1 new test fails (Literal rejects "district" + "district_delta_up").

- [ ] **Step 3: Update `api/schemas/alerts.py`**

Find the existing Literals near the top of the file:

```python
AlertTargetType = Literal["building", "community"]
AlertKind = Literal[
    "yield_up",
    "yield_down",
    "price_drop",
    "score_jump",
]
```

Replace with:

```python
AlertTargetType = Literal["building", "community", "district"]
AlertKind = Literal[
    "yield_up",
    "yield_down",
    "price_drop",
    "score_jump",
    "district_delta_up",
    "district_delta_down",
]
```

- [ ] **Step 4: Verify passing**

Run: `pytest tests/api/test_alerts_schema.py -v`
Expected: 9 passed (8 prior + 1 new).

Run: `pytest -q`
Expected: 118 passed.

- [ ] **Step 5: Commit**

```bash
git add api/schemas/alerts.py tests/api/test_alerts_schema.py
git commit -m "feat(api): extend Alert schema for district kind + target type"
```

---

### Task 2: Diff function handles districts

**Files:**
- Modify: `api/domains/alerts_diff.py`
- Modify: `tests/api/test_alerts_diff.py`

`compute_alerts` gains an additional optional argument `district_snapshots: dict | None = None` keyed by district id with values `{name, yield}`. When non-None, after the watchlist loop, the function iterates districts that have BOTH a baseline (looked up in the same `baselines` dict by district id) AND a snapshot, calls a new `_diff_district` helper, extends `out`. Existing call sites (the v2 endpoint) opt-in by passing the new arg.

- [ ] **Step 1: Add the failing tests**

Open `tests/api/test_alerts_diff.py`. Append at the end:

```python
def test_compute_alerts_emits_district_delta_up_when_yield_rises_past_threshold() -> None:
    items = compute_alerts(
        watchlist_items=[],
        baselines={"pudong": {"yield": 4.0}},
        snapshots={},
        rules=AlertRules(district_delta_abs=1.0),
        district_snapshots={"pudong": {"name": "浦东新区", "yield": 5.2}},
    )
    assert len(items) == 1
    a = items[0]
    assert a.target_id == "pudong"
    assert a.target_type == "district"
    assert a.target_name == "浦东新区"
    assert a.kind == "district_delta_up"
    assert abs(a.delta - 1.2) < 0.001


def test_compute_alerts_emits_district_delta_down_when_yield_drops_past_threshold() -> None:
    items = compute_alerts(
        watchlist_items=[],
        baselines={"pudong": {"yield": 4.5}},
        snapshots={},
        rules=AlertRules(district_delta_abs=1.0),
        district_snapshots={"pudong": {"name": "浦东新区", "yield": 3.4}},
    )
    assert len(items) == 1
    assert items[0].kind == "district_delta_down"
    assert items[0].delta < 0


def test_compute_alerts_district_delta_within_dead_zone_emits_no_alert() -> None:
    items = compute_alerts(
        watchlist_items=[],
        baselines={"pudong": {"yield": 4.0}},
        snapshots={},
        rules=AlertRules(district_delta_abs=1.0),
        district_snapshots={"pudong": {"name": "浦东新区", "yield": 4.5}},
    )
    assert items == []
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_alerts_diff.py -v`
Expected: 3 new tests fail (the keyword arg `district_snapshots` is unknown).

- [ ] **Step 3: Update `api/domains/alerts_diff.py`**

Find the existing `compute_alerts` signature:

```python
def compute_alerts(
    watchlist_items: list[dict[str, Any]],
    baselines: dict[str, dict[str, Any]],
    snapshots: dict[str, dict[str, Any] | None],
    rules: AlertRules,
) -> list[Alert]:
    out: list[Alert] = []
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if target_type not in ("building", "community"):
            continue
        baseline = baselines.get(target_id)
        if not baseline:
            continue
        snapshot = snapshots.get(target_id)
        if not snapshot:
            continue
        out.extend(_diff_target(target_id, target_type, baseline, snapshot, rules))
    return out
```

Replace with:

```python
def compute_alerts(
    watchlist_items: list[dict[str, Any]],
    baselines: dict[str, dict[str, Any]],
    snapshots: dict[str, dict[str, Any] | None],
    rules: AlertRules,
    district_snapshots: dict[str, dict[str, Any] | None] | None = None,
) -> list[Alert]:
    out: list[Alert] = []
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if target_type not in ("building", "community"):
            continue
        baseline = baselines.get(target_id)
        if not baseline:
            continue
        snapshot = snapshots.get(target_id)
        if not snapshot:
            continue
        out.extend(_diff_target(target_id, target_type, baseline, snapshot, rules))

    if district_snapshots:
        for district_id, district_snap in district_snapshots.items():
            if not district_snap:
                continue
            baseline = baselines.get(district_id)
            if not baseline:
                continue
            alert = _diff_district(district_id, baseline, district_snap, rules)
            if alert is not None:
                out.append(alert)

    return out
```

Then add the new `_diff_district` helper directly below `_diff_target`:

```python
def _diff_district(
    district_id: str,
    baseline: dict[str, Any],
    snapshot: dict[str, Any],
    rules: AlertRules,
) -> Alert | None:
    base = _normalize_yield(baseline.get("yield"))
    snap = _normalize_yield(snapshot.get("yield"))
    if base is None or snap is None:
        return None
    delta = snap - base
    if abs(delta) < rules.district_delta_abs:
        return None
    name_raw = snapshot.get("name")
    target_name = str(name_raw) if name_raw else None
    kind = "district_delta_up" if delta > 0 else "district_delta_down"
    return Alert(
        target_id=district_id,
        target_name=target_name,
        target_type="district",
        kind=kind,
        from_value=base,
        to_value=snap,
        delta=delta,
    )
```

- [ ] **Step 4: Verify passing**

Run: `pytest tests/api/test_alerts_diff.py -v`
Expected: 13 passed (10 prior + 3 new).

Run: `pytest -q`
Expected: 121 passed.

- [ ] **Step 5: Commit**

```bash
git add api/domains/alerts_diff.py tests/api/test_alerts_diff.py
git commit -m "feat(api): compute_alerts emits district_delta when yield crosses threshold"
```

---

### Task 3: Endpoint walks districts on since-last-open + mark-seen

**Files:**
- Modify: `api/domains/alerts.py`
- Modify: `tests/api/test_v2_alerts.py`

`_district_snapshots()` is a new internal helper that walks `list_districts()` once and returns a dict `{district_id: {name, yield}}` for all 16 districts. `since_last_open` passes that into `compute_alerts`. `mark_seen` extends the baselines dict with the current district yields keyed by district id, so the next `since-last-open` returns no district alerts.

- [ ] **Step 1: Add the failing tests**

Open `tests/api/test_v2_alerts.py`. Append at the end:

```python
def test_since_last_open_emits_district_delta_alerts(
    client, isolated_personal_dir: Path
) -> None:
    # No watchlist needed for district alerts; plant a stale district baseline.
    state = {
        "baselines": {
            "pudong": {"yield": 0.5},
        },
        "last_open_at": "2026-04-20T10:00:00",
    }
    (isolated_personal_dir / "alerts_state.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    response = client.get("/api/v2/alerts/since-last-open").json()
    district_alerts = [it for it in response["items"] if it["target_type"] == "district"]
    assert any(a["target_id"] == "pudong" for a in district_alerts)
    pudong = next(a for a in district_alerts if a["target_id"] == "pudong")
    assert pudong["kind"] in ("district_delta_up", "district_delta_down")
    assert pudong.get("target_name")
    assert pudong["target_name"] != pudong["target_id"]


def test_mark_seen_captures_district_baselines(
    client, isolated_personal_dir: Path
) -> None:
    response = client.post("/api/v2/alerts/mark-seen", json={})
    assert response.status_code == 200
    on_disk = json.loads(
        (isolated_personal_dir / "alerts_state.json").read_text(encoding="utf-8")
    )
    # Districts get baselines even with empty watchlist
    assert "pudong" in on_disk["baselines"]
    # Following GET should produce no alerts because baselines == current
    follow = client.get("/api/v2/alerts/since-last-open").json()
    district_alerts = [it for it in follow["items"] if it["target_type"] == "district"]
    assert district_alerts == []
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_v2_alerts.py -v`
Expected: 2 new tests fail (district alerts not emitted yet).

- [ ] **Step 3: Update `api/domains/alerts.py`**

Open the file. Find the existing imports near the top:

```python
from ..service import get_building, get_community
from . import alerts_diff
```

Add `list_districts` to the service import:

```python
from ..service import get_building, get_community, list_districts
from . import alerts_diff
```

Find the `_snapshot` function. Directly below it, add a new internal helper:

```python
def _district_snapshots() -> dict[str, dict[str, Any]]:
    rows = list_districts(district="all", min_yield=0, max_budget=10000, min_samples=0)
    snapshots: dict[str, dict[str, Any]] = {}
    for row in rows:
        district_id = row.get("id")
        if not district_id:
            continue
        snapshots[district_id] = {
            "name": row.get("name") or "",
            "yield": row.get("yield"),
        }
    return snapshots
```

Find the `since_last_open` function:

```python
@router.get("/alerts/since-last-open")
def since_last_open() -> dict[str, Any]:
    state = _load_state()
    rules = _load_rules()
    watchlist_items = _load_watchlist()
    snapshots: dict[str, dict[str, Any] | None] = {}
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if not target_id or target_type not in ("building", "community"):
            continue
        snapshots[target_id] = _snapshot(target_id, target_type)
    alerts = alerts_diff.compute_alerts(
        watchlist_items=watchlist_items,
        baselines=state.baselines,
        snapshots=snapshots,
        rules=rules,
    )
    return {
        "items": [a.model_dump() for a in alerts],
        "last_open_at": state.last_open_at,
    }
```

Replace with:

```python
@router.get("/alerts/since-last-open")
def since_last_open() -> dict[str, Any]:
    state = _load_state()
    rules = _load_rules()
    watchlist_items = _load_watchlist()
    snapshots: dict[str, dict[str, Any] | None] = {}
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if not target_id or target_type not in ("building", "community"):
            continue
        snapshots[target_id] = _snapshot(target_id, target_type)
    district_snapshots = _district_snapshots()
    alerts = alerts_diff.compute_alerts(
        watchlist_items=watchlist_items,
        baselines=state.baselines,
        snapshots=snapshots,
        rules=rules,
        district_snapshots=district_snapshots,
    )
    return {
        "items": [a.model_dump() for a in alerts],
        "last_open_at": state.last_open_at,
    }
```

Find the `mark_seen` function:

```python
@router.post("/alerts/mark-seen")
def mark_seen() -> dict[str, Any]:
    watchlist_items = _load_watchlist()
    baselines: dict[str, dict[str, Any]] = {}
    seen = 0
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if not target_id or target_type not in ("building", "community"):
            continue
        snapshot = _snapshot(target_id, target_type)
        if snapshot is None:
            continue
        baselines[target_id] = snapshot
        seen += 1
    state = AlertsState(baselines=baselines, last_open_at=_now())
    personal_storage.write_json(ALERTS_STATE_FILE, state.model_dump())
    return {"items_seen": seen, "last_open_at": state.last_open_at}
```

Replace with:

```python
@router.post("/alerts/mark-seen")
def mark_seen() -> dict[str, Any]:
    watchlist_items = _load_watchlist()
    baselines: dict[str, dict[str, Any]] = {}
    seen = 0
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if not target_id or target_type not in ("building", "community"):
            continue
        snapshot = _snapshot(target_id, target_type)
        if snapshot is None:
            continue
        baselines[target_id] = snapshot
        seen += 1
    for district_id, snap in _district_snapshots().items():
        if snap.get("yield") is None:
            continue
        baselines[district_id] = {"yield": snap.get("yield"), "name": snap.get("name")}
        seen += 1
    state = AlertsState(baselines=baselines, last_open_at=_now())
    personal_storage.write_json(ALERTS_STATE_FILE, state.model_dump())
    return {"items_seen": seen, "last_open_at": state.last_open_at}
```

- [ ] **Step 4: Verify passing**

Run: `pytest tests/api/test_v2_alerts.py -v`
Expected: 10 passed (8 prior + 2 new).

Run: `pytest -q`
Expected: 123 passed (121 prior + 2 new).

Run: `python3 -m compileall api`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add api/domains/alerts.py tests/api/test_v2_alerts.py
git commit -m "feat(api): /alerts walks districts on since-last-open + mark-seen"
```

---

### Task 4: Frontend formatter handles district_delta

**Files:**
- Modify: `frontend/user/modules/alerts-helpers.js`
- Modify: `tests/frontend/test_alerts_helpers.mjs`

The banner already renders any kind via `formatAlertLine`. We add new branches for `district_delta_up` / `district_delta_down`. `severityFor` returns `up` for `_up` and `down` for `_down`.

- [ ] **Step 1: Add the failing tests**

Open `tests/frontend/test_alerts_helpers.mjs`. Append at the end:

```javascript
test("formatAlertLine: district_delta_up renders pp delta", () => {
  const line = formatAlertLine({
    kind: "district_delta_up",
    from_value: 4.0,
    to_value: 5.2,
    delta: 1.2,
  });
  assert.equal(line, "区均租售比 4.00% → 5.20% (+1.20)");
});

test("formatAlertLine: district_delta_down renders negative", () => {
  const line = formatAlertLine({
    kind: "district_delta_down",
    from_value: 4.5,
    to_value: 3.4,
    delta: -1.1,
  });
  assert.equal(line, "区均租售比 4.50% → 3.40% (−1.10)");
});

test("severityFor: district_delta_up → up", () => {
  assert.equal(severityFor({ kind: "district_delta_up" }), "up");
});

test("severityFor: district_delta_down → down", () => {
  assert.equal(severityFor({ kind: "district_delta_down" }), "down");
});
```

- [ ] **Step 2: Verify failing**

Run: `node --test tests/frontend/test_alerts_helpers.mjs`
Expected: 4 failures (district lines fall through to the default unknown-kind branch).

- [ ] **Step 3: Update `frontend/user/modules/alerts-helpers.js`**

Find the `formatAlertLine` function. The current shape:

```javascript
export function formatAlertLine(alert) {
  if (!alert) return "";
  const { kind, from_value: from, to_value: to, delta } = alert;
  if (kind === "yield_up" || kind === "yield_down") {
    return `租售比 ${fmt(from)}% → ${fmt(to)}% (${signed(delta)})`;
  }
  if (kind === "price_drop") {
    const fromNum = Number(from);
    const pct = fromNum > 0 ? ((Number(to) - fromNum) / fromNum) * 100 : 0;
    const pctSigned = pct >= 0 ? `+${pct.toFixed(1)}` : `${MINUS}${Math.abs(pct).toFixed(1)}`;
    return `总价 ${fmtInt(from)} → ${fmtInt(to)} 万 (${pctSigned}%)`;
  }
  if (kind === "score_jump") {
    const sign = Number(delta) >= 0 ? "+" : MINUS;
    return `机会分 ${fmtInt(from)} → ${fmtInt(to)} (${sign}${Math.abs(Math.round(Number(delta)))})`;
  }
  return `${kind} ${fmtInt(from)} → ${fmtInt(to)}`;
}
```

Replace with:

```javascript
export function formatAlertLine(alert) {
  if (!alert) return "";
  const { kind, from_value: from, to_value: to, delta } = alert;
  if (kind === "yield_up" || kind === "yield_down") {
    return `租售比 ${fmt(from)}% → ${fmt(to)}% (${signed(delta)})`;
  }
  if (kind === "district_delta_up" || kind === "district_delta_down") {
    return `区均租售比 ${fmt(from)}% → ${fmt(to)}% (${signed(delta)})`;
  }
  if (kind === "price_drop") {
    const fromNum = Number(from);
    const pct = fromNum > 0 ? ((Number(to) - fromNum) / fromNum) * 100 : 0;
    const pctSigned = pct >= 0 ? `+${pct.toFixed(1)}` : `${MINUS}${Math.abs(pct).toFixed(1)}`;
    return `总价 ${fmtInt(from)} → ${fmtInt(to)} 万 (${pctSigned}%)`;
  }
  if (kind === "score_jump") {
    const sign = Number(delta) >= 0 ? "+" : MINUS;
    return `机会分 ${fmtInt(from)} → ${fmtInt(to)} (${sign}${Math.abs(Math.round(Number(delta)))})`;
  }
  return `${kind} ${fmtInt(from)} → ${fmtInt(to)}`;
}
```

Find the `severityFor` function:

```javascript
export function severityFor(alert) {
  if (!alert) return "warn";
  const kind = alert.kind;
  if (kind === "yield_up") return "up";
  if (kind === "yield_down" || kind === "price_drop") return "down";
  if (kind === "score_jump") {
    return Number(alert.delta) >= 0 ? "up" : "down";
  }
  return "warn";
}
```

Replace with:

```javascript
export function severityFor(alert) {
  if (!alert) return "warn";
  const kind = alert.kind;
  if (kind === "yield_up" || kind === "district_delta_up") return "up";
  if (kind === "yield_down" || kind === "price_drop" || kind === "district_delta_down") return "down";
  if (kind === "score_jump") {
    return Number(alert.delta) >= 0 ? "up" : "down";
  }
  return "warn";
}
```

- [ ] **Step 4: Verify passing**

Run: `node --test tests/frontend/test_alerts_helpers.mjs`
Expected: 12 passed (8 prior + 4 new).

Run: `node --check frontend/user/modules/alerts-helpers.js`
Expected: exit 0.

Run combined node tests: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs tests/frontend/test_search_helpers.mjs`
Expected: 100 passed (96 prior + 4 new).

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/alerts-helpers.js tests/frontend/test_alerts_helpers.mjs
git commit -m "feat(user): banner formatter handles district_delta alerts"
```

---

### Task 5: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Edit `README.md`**

Open `README.md`. Find `## 路由布局（Phase 6e 起）` and change to `## 路由布局（Phase 6f 起）`.

The `/` row description doesn't change in this phase — the banner already covered alerts; adding district kinds is internal evolution.

- [ ] **Step 2: Verify all exit criteria**

Run each:
- `pytest -q` → 123 passed
- `node --test ...` (11 frontend test files) → 100 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 21 OK (no smoke change)
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: bump phase 6e → 6f (district alerts)"
```

---

## Phase 6f Exit Criteria

- [ ] `pytest -q` — 123 passed (117 prior + 1 schema + 3 diff + 2 v2 endpoint)
- [ ] `node --test ...` — 100 passed (96 prior + 4 alerts helpers)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check`
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 21 rows OK
- [ ] Manual: `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` running, plant a stale district baseline (`echo '{"baselines": {"pudong": {"yield": 0.5}}}' > data/personal/alerts_state.json`), `curl http://127.0.0.1:8013/api/v2/alerts/since-last-open` returns at least one item with `target_type="district"`, `target_id="pudong"`, `target_name="浦东新区"`, and `kind="district_delta_up"`. Open `/?mode=yield` in a browser — the banner shows the alert as `浦东新区 · 区均租售比 0.50% → 2.82% (+2.32)` colored green (up severity). `POST /api/v2/alerts/mark-seen` then `curl since-last-open` returns no district alerts.
- [ ] `git log --oneline 3e3eae3..HEAD` shows exactly 5 commits

## Out of Scope (deferred)

- 挂牌量突变 listings count change (no listings endpoint)
- District alert markers on the city-mode map polygons (visual)
- Per-district notes (annotation target_type Literal doesn't include "district")
- Streaming / cron alerts (pull-only by spec)
- Manual browser screenshot
