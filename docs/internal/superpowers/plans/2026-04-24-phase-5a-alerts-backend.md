# Phase 5a — Alerts Backend (Diff Logic + State + Rules) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the alerts backend: persist baselines and rules under `data/personal/`, expose `GET /api/v2/alerts/since-last-open`, `POST /api/v2/alerts/mark-seen`, `GET /api/v2/alerts/rules`, and `PATCH /api/v2/alerts/rules`. The since-last-open endpoint diffs each watchlist target's current snapshot against its persisted baseline using configured thresholds; mark-seen captures the current snapshots as the new baseline so the same alerts don't re-fire on every page load. The frontend banner that consumes these endpoints is Phase 5b.

**Architecture:** Reuses the personal-data file layer from Phase 3c-1 (`api/personal_storage.py`). New `api/schemas/alerts.py` defines `AlertsState` (`baselines: dict[str, dict] + last_open_at: str | None`) and `AlertRules` (with sensible defaults). New `api/domains/alerts.py` exposes the four endpoints. The diff logic is one pure function `compute_alerts(watchlist_items, baselines, snapshots, rules) -> list[Alert]` that's exhaustively unit-tested without DB or HTTP. The endpoint layer wires `service.get_building` / `service.get_community` to populate snapshots; tests can exercise the diff function directly with synthetic data.

**Tech Stack:** FastAPI · Pydantic 2.9 · `api/personal_storage.py` (Phase 3c-1) · `api/domains/watchlist.py` (Phase 4a) for the watchlist read · `api/service.py` for snapshot fetchers · pytest + httpx TestClient. No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 6 schemas "AlertsState" + "AlertRules" + section 6 API table for `/api/v2/alerts/*` + section 6 "变化提醒计算时机")

**Prior plan:** 2026-04-24-phase-4b-annotations.md (merged at `8af7553`)

---

## File Structure (Phase 5a outcome)

```
api/
├── main.py                          # MODIFIED: include_router for v2_alerts
├── schemas/
│   └── alerts.py                    # NEW — AlertsState, AlertRules, Alert
└── domains/
    ├── alerts.py                    # NEW — 4 endpoints
    └── alerts_diff.py               # NEW — pure compute_alerts function

tests/api/
├── test_alerts_schema.py            # NEW (~5 cases)
├── test_alerts_diff.py              # NEW (~9 cases — diff logic only)
└── test_v2_alerts.py                # NEW (~7 cases — endpoints)

scripts/phase1_smoke.py              # MODIFIED: +1 row asserting GET /api/v2/alerts/rules
README.md                            # MODIFIED: bump Phase 4b → Phase 5a
```

**Out-of-scope (deferred to Phase 5b and later):**
- Frontend banner — Phase 5b
- New listing detection (`listing_new` rule) — needs a backend listings endpoint that doesn't exist; the rule field stays for forward-compat but the diff logic ignores it for now. Documented in plan and ignored in tests.
- District-level alerts (`district_delta_abs` rule) — Phase 5c. The rule field stays for forward-compat; diff logic ignores it.
- Alerts for non-watchlist targets — only watchlist entries are diffed. Mode-specific defaults (e.g. yield mode adding watch on click) are out of scope.
- Real-time push / WebSocket — alerts are pulled on page load only, per the spec's "客户端主动触发" decision.

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-5a-alerts-backend .worktrees/phase-5a-alerts-backend
cd .worktrees/phase-5a-alerts-backend
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 67 pytest passed; 65 node tests passed; 16 smoke routes OK.

---

### Task 1: Alerts pydantic schemas + tests

**Files:**
- Create: `api/schemas/alerts.py`
- Create: `tests/api/test_alerts_schema.py`

Three models:
- `AlertsState` — `baselines: dict[str, dict] = {}` (target_id → snapshot dict), `last_open_at: str | None = None`. `extra="ignore"` for forward-compat.
- `AlertRules` — `yield_delta_abs: float = 0.5` (percentage points; default 0.5 = 0.5%), `price_drop_pct: float = 3.0` (percent of base; default 3.0 = 3%), `score_delta_abs: int = 5`, `listing_new: bool = True` (reserved), `district_delta_abs: float = 1.0` (reserved). `extra="ignore"`. `AlertRulesPatch` mirror with all fields optional, `extra="forbid"`.
- `Alert` — emitted alert row: `target_id`, `target_type` (Literal building/community), `kind` (Literal), `from_value`, `to_value`, `delta`. Used as the response shape for `/since-last-open`.

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_alerts_schema.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.schemas.alerts import Alert, AlertRules, AlertRulesPatch, AlertsState


def test_alerts_state_defaults() -> None:
    state = AlertsState()
    assert state.baselines == {}
    assert state.last_open_at is None


def test_alerts_state_round_trips() -> None:
    payload = {
        "baselines": {
            "zhangjiang-park-b1": {"yield": 4.0, "price": 800.0, "score": 60},
        },
        "last_open_at": "2026-04-24T10:00:00",
    }
    state = AlertsState.model_validate(payload)
    assert state.baselines["zhangjiang-park-b1"]["yield"] == 4.0


def test_alert_rules_defaults_match_spec() -> None:
    rules = AlertRules()
    assert rules.yield_delta_abs == 0.5
    assert rules.price_drop_pct == 3.0
    assert rules.score_delta_abs == 5
    assert rules.listing_new is True
    assert rules.district_delta_abs == 1.0


def test_alert_rules_patch_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        AlertRulesPatch.model_validate({"yield_delta_abs": 1.0, "evil": True})


def test_alert_rules_patch_accepts_partial() -> None:
    patch = AlertRulesPatch.model_validate({"yield_delta_abs": 1.0})
    update = patch.model_dump(exclude_unset=True)
    assert update == {"yield_delta_abs": 1.0}


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

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_alerts_schema.py -v`
Expected: ImportError — `api.schemas.alerts` doesn't exist yet.

- [ ] **Step 3: Implement `api/schemas/alerts.py`**

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AlertTargetType = Literal["building", "community"]
AlertKind = Literal[
    "yield_up",
    "yield_down",
    "price_drop",
    "score_jump",
]


class AlertsState(BaseModel):
    """Persisted at data/personal/alerts_state.json."""

    model_config = ConfigDict(extra="ignore")

    baselines: dict[str, dict[str, Any]] = Field(default_factory=dict)
    last_open_at: str | None = None


class AlertRules(BaseModel):
    """Persisted at data/personal/alert_rules.json. Defaults match spec section 6."""

    model_config = ConfigDict(extra="ignore")

    yield_delta_abs: float = Field(default=0.5, ge=0)
    price_drop_pct: float = Field(default=3.0, ge=0)
    score_delta_abs: int = Field(default=5, ge=0)
    listing_new: bool = True
    district_delta_abs: float = Field(default=1.0, ge=0)


class AlertRulesPatch(BaseModel):
    """PATCH /api/v2/alerts/rules body — partial update."""

    model_config = ConfigDict(extra="forbid")

    yield_delta_abs: float | None = Field(default=None, ge=0)
    price_drop_pct: float | None = Field(default=None, ge=0)
    score_delta_abs: int | None = Field(default=None, ge=0)
    listing_new: bool | None = None
    district_delta_abs: float | None = Field(default=None, ge=0)


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

- [ ] **Step 4: Verify passing**

Run: `pytest tests/api/test_alerts_schema.py -v`
Expected: 6 tests passed.

Run: `pytest -q`
Expected: 73 passed (67 prior + 6 new).

- [ ] **Step 5: Commit**

```bash
git add api/schemas/alerts.py tests/api/test_alerts_schema.py
git commit -m "feat(api): add AlertsState + AlertRules + Alert schemas"
```

---

### Task 2: Pure diff logic (`alerts_diff.py`) + tests

**Files:**
- Create: `api/domains/alerts_diff.py`
- Create: `tests/api/test_alerts_diff.py`

The pure function:
```python
def compute_alerts(
    watchlist_items: list[dict],
    baselines: dict[str, dict],
    snapshots: dict[str, dict | None],
    rules: AlertRules,
) -> list[Alert]:
```

For each watchlist entry:
- Look up `baselines[target_id]` (skip if missing — first time we've seen this target, no diff)
- Look up `snapshots[target_id]` (skip if missing — target gone or fetch failed)
- Compare `yield`, `price`, `score` per rules; emit one alert per crossing threshold (max 2 per target: one yield + one price + one score)

Yield is normalized via the same heuristic the frontend uses (value < 1 means fraction → multiply by 100). This protects against staged-vs-mock unit mismatches.

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_alerts_diff.py`:

```python
from __future__ import annotations

from api.domains.alerts_diff import compute_alerts
from api.schemas.alerts import AlertRules


def _watchlist(target_ids: list[tuple[str, str]]) -> list[dict]:
    return [{"target_id": tid, "target_type": ttype} for tid, ttype in target_ids]


def test_no_baselines_returns_empty() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={},
        snapshots={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        rules=AlertRules(),
    )
    assert items == []


def test_no_snapshot_skips_target() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": None},
        rules=AlertRules(),
    )
    assert items == []


def test_yield_up_crosses_threshold() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": {"yield": 4.6, "price": 800.0, "score": 60}},
        rules=AlertRules(yield_delta_abs=0.5),
    )
    assert len(items) == 1
    assert items[0].kind == "yield_up"
    assert items[0].delta == 0.6
    assert items[0].from_value == 4.0
    assert items[0].to_value == 4.6


def test_yield_down_crosses_threshold() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": {"yield": 3.4, "price": 800.0, "score": 60}},
        rules=AlertRules(yield_delta_abs=0.5),
    )
    assert len(items) == 1
    assert items[0].kind == "yield_down"
    assert items[0].delta == -0.6


def test_yield_within_deadzone_no_alert() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": {"yield": 4.3, "price": 800.0, "score": 60}},
        rules=AlertRules(yield_delta_abs=0.5),
    )
    assert items == []


def test_price_drop_crosses_threshold() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.0, "price": 950.0, "score": 60}},
        rules=AlertRules(price_drop_pct=3.0),
    )
    assert len(items) == 1
    assert items[0].kind == "price_drop"
    # 1000 → 950 is a 5% drop
    assert items[0].delta == -50.0
    assert items[0].from_value == 1000.0
    assert items[0].to_value == 950.0


def test_price_increase_does_not_alert() -> None:
    # spec only flags drops, not increases
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.0, "price": 1100.0, "score": 60}},
        rules=AlertRules(price_drop_pct=3.0),
    )
    assert items == []


def test_score_jump_either_direction() -> None:
    # Spec yield mode: 机会分跳变 ≥5 — symmetric.
    rules = AlertRules(score_delta_abs=5)
    up = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.0, "price": 1000.0, "score": 70}},
        rules=rules,
    )
    assert len(up) == 1
    assert up[0].kind == "score_jump"
    assert up[0].delta == 10
    down = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.0, "price": 1000.0, "score": 50}},
        rules=rules,
    )
    assert len(down) == 1
    assert down[0].delta == -10


def test_yield_unit_normalisation_fraction_input() -> None:
    # baseline is 0.04 (fraction = 4%); snapshot is 0.05 (= 5%); diff = 1.0 pp > 0.5
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 0.04, "price": 800.0, "score": 60}},
        snapshots={"x": {"yield": 0.05, "price": 800.0, "score": 60}},
        rules=AlertRules(yield_delta_abs=0.5),
    )
    assert len(items) == 1
    assert items[0].kind == "yield_up"
    # Reported in percentage points using the larger of the two
    assert abs(items[0].delta - 1.0) < 0.001


def test_multiple_alerts_per_target() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.6, "price": 950.0, "score": 70}},
        rules=AlertRules(),
    )
    kinds = sorted(a.kind for a in items)
    assert kinds == ["price_drop", "score_jump", "yield_up"]
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_alerts_diff.py -v`
Expected: ImportError — `api.domains.alerts_diff` doesn't exist yet.

- [ ] **Step 3: Implement `api/domains/alerts_diff.py`**

```python
from __future__ import annotations

from typing import Any

from ..schemas.alerts import Alert, AlertRules


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
                )
            )

    base_score = _maybe_float(baseline.get("score"))
    snap_score = _maybe_float(snapshot.get("score"))
    if base_score is not None and snap_score is not None:
        delta = snap_score - base_score
        if abs(delta) >= rules.score_delta_abs:
            out.append(
                _alert(target_id, target_type, "score_jump", base_score, snap_score, delta)
            )

    return out


def _normalize_yield(value: Any) -> float | None:
    num = _maybe_float(value)
    if num is None:
        return None
    # Frontend mirror: a value < 1 is a fraction (e.g. 0.04 = 4%); scale up.
    return num * 100.0 if num < 1 else num


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return result


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

- [ ] **Step 4: Verify passing**

Run: `pytest tests/api/test_alerts_diff.py -v`
Expected: 10 tests passed.

Run: `pytest -q`
Expected: 83 passed (67 prior + 6 schema + 10 diff).

- [ ] **Step 5: Commit**

```bash
git add api/domains/alerts_diff.py tests/api/test_alerts_diff.py
git commit -m "feat(api): add pure compute_alerts diff logic"
```

---

### Task 3: Alerts domain endpoints + tests

**Files:**
- Create: `api/domains/alerts.py`
- Create: `tests/api/test_v2_alerts.py`
- Modify: `api/main.py`

Endpoints:
- `GET /api/v2/alerts/rules` → returns current AlertRules dump (defaults if file missing).
- `PATCH /api/v2/alerts/rules` body=AlertRulesPatch → merges + writes; returns the validated dump.
- `GET /api/v2/alerts/since-last-open` → reads watchlist + alerts_state + alert_rules; for each watchlist target, builds a snapshot via `service.get_building` / `service.get_community`; calls `compute_alerts`; returns `{items, last_open_at}`.
- `POST /api/v2/alerts/mark-seen` body=`{}` → for each watchlist target, captures the current snapshot; writes `alerts_state.json` with `baselines` (target_id → snapshot) and `last_open_at = now()`. Returns `{items_seen, last_open_at}` (count of targets snapshotted).

Snapshot shape (consistent with `compute_alerts` and the watchlist):
- building: `{yield: yieldAvg, price: saleMedianWan, score: score}`
- community: `{yield: yield, price: avgPriceWan, score: score}`

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_v2_alerts.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_personal_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_rules_default_when_no_file(client) -> None:
    response = client.get("/api/v2/alerts/rules")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["yield_delta_abs"] == 0.5
    assert body["price_drop_pct"] == 3.0
    assert body["score_delta_abs"] == 5


def test_rules_patch_merges_and_persists(client) -> None:
    response = client.patch(
        "/api/v2/alerts/rules", json={"yield_delta_abs": 1.0}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["yield_delta_abs"] == 1.0
    # other fields preserved at defaults
    assert body["price_drop_pct"] == 3.0
    follow = client.get("/api/v2/alerts/rules").json()
    assert follow["yield_delta_abs"] == 1.0


def test_rules_patch_rejects_unknown_field_with_422(client) -> None:
    response = client.patch("/api/v2/alerts/rules", json={"evil": True})
    assert response.status_code == 422


def test_since_last_open_returns_empty_with_no_state(client) -> None:
    response = client.get("/api/v2/alerts/since-last-open")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {"items": [], "last_open_at": None}


def test_since_last_open_emits_yield_alert(client, isolated_personal_dir: Path) -> None:
    # Add a real mock building to the watchlist
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    # Plant a stale baseline directly on disk
    state = {
        "baselines": {
            "zhangjiang-park-b1": {"yield": 1.0, "price": 100.0, "score": 30}
        },
        "last_open_at": "2026-04-20T10:00:00",
    }
    (isolated_personal_dir / "alerts_state.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    response = client.get("/api/v2/alerts/since-last-open")
    assert response.status_code == 200
    body = response.json()
    assert body["last_open_at"] == "2026-04-20T10:00:00"
    kinds = {item["kind"] for item in body["items"]}
    # The mock yieldAvg/score are far enough from baseline to trigger
    assert "yield_up" in kinds or "yield_down" in kinds
    assert "score_jump" in kinds


def test_mark_seen_creates_baselines_for_watchlist_targets(
    client, isolated_personal_dir: Path
) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    response = client.post("/api/v2/alerts/mark-seen", json={})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["items_seen"] >= 1
    assert body["last_open_at"] is not None

    on_disk = json.loads(
        (isolated_personal_dir / "alerts_state.json").read_text(encoding="utf-8")
    )
    assert "zhangjiang-park-b1" in on_disk["baselines"]


def test_mark_seen_then_since_last_open_returns_no_alerts(
    client, isolated_personal_dir: Path
) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    client.post("/api/v2/alerts/mark-seen", json={})
    response = client.get("/api/v2/alerts/since-last-open").json()
    # baselines == current → no alerts
    assert response["items"] == []
    assert response["last_open_at"] is not None
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_v2_alerts.py -v`
Expected: all 7 fail (404 — endpoints don't exist yet).

- [ ] **Step 3: Implement `api/domains/alerts.py`**

```python
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from .. import personal_storage
from ..schemas.alerts import AlertRules, AlertRulesPatch, AlertsState
from ..schemas.watchlist import WatchlistEntry
from ..service import get_building, get_community
from . import alerts_diff

router = APIRouter(tags=["alerts"])

ALERTS_STATE_FILE = "alerts_state.json"
ALERT_RULES_FILE = "alert_rules.json"
WATCHLIST_FILE = "watchlist.json"


def _load_watchlist() -> list[dict[str, Any]]:
    raw = personal_storage.read_json(WATCHLIST_FILE)
    if raw is None:
        return []
    if isinstance(raw, dict) and "items" in raw:
        candidates = raw["items"]
    else:
        candidates = raw
    if not isinstance(candidates, list):
        return []
    items: list[dict[str, Any]] = []
    for row in candidates:
        try:
            items.append(WatchlistEntry.model_validate(row).model_dump())
        except Exception:
            continue
    return items


def _load_state() -> AlertsState:
    raw = personal_storage.read_json(ALERTS_STATE_FILE)
    if raw is None:
        return AlertsState()
    try:
        return AlertsState.model_validate(raw)
    except Exception:
        return AlertsState()


def _load_rules() -> AlertRules:
    raw = personal_storage.read_json(ALERT_RULES_FILE)
    if raw is None:
        return AlertRules()
    try:
        return AlertRules.model_validate(raw)
    except Exception:
        return AlertRules()


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


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@router.get("/alerts/rules")
def get_rules() -> dict[str, Any]:
    return _load_rules().model_dump()


@router.patch("/alerts/rules")
def patch_rules(patch: AlertRulesPatch) -> dict[str, Any]:
    current = _load_rules().model_dump()
    update = patch.model_dump(exclude_unset=True)
    merged = {**current, **update}
    rules = AlertRules.model_validate(merged)
    personal_storage.write_json(ALERT_RULES_FILE, rules.model_dump())
    return rules.model_dump()


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

- [ ] **Step 4: Wire into `api/main.py`**

Open `api/main.py`. Find the v2 imports (after Phase 4b):

```python
from .domains import (
    annotations as v2_annotations,
    buildings as v2_buildings,
    communities as v2_communities,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
    user_prefs as v2_user_prefs,
    watchlist as v2_watchlist,
)
```

Add `alerts as v2_alerts` to keep alphabetical order:

```python
from .domains import (
    alerts as v2_alerts,
    annotations as v2_annotations,
    buildings as v2_buildings,
    communities as v2_communities,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
    user_prefs as v2_user_prefs,
    watchlist as v2_watchlist,
)
```

Find the existing `app.include_router(v2_*.router, prefix="/api/v2")` block and add:

```python
app.include_router(v2_alerts.router, prefix="/api/v2")
```

- [ ] **Step 5: Run the tests**

Run: `pytest tests/api/test_v2_alerts.py -v`
Expected: 7 tests pass.

- [ ] **Step 6: Compile + full suite**

Run: `python3 -m compileall api`
Expected: exit 0.

Run: `pytest -q`
Expected: 90 passed (67 prior + 6 schema + 10 diff + 7 v2 alerts).

- [ ] **Step 7: Commit**

```bash
git add api/domains/alerts.py api/main.py tests/api/test_v2_alerts.py
git commit -m "feat(api): add /api/v2/alerts (rules + since-last-open + mark-seen)"
```

---

### Task 4: smoke + README

**Files:**
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Extend smoke**

Open `scripts/phase1_smoke.py`. Find the line:

```python
            (f"{base}/api/v2/annotations/by-target/probe", '"items"'),
```

Add directly below it:

```python
            (f"{base}/api/v2/alerts/rules", '"yield_delta_abs"'),
```

- [ ] **Step 2: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 17 OK, exit 0.

- [ ] **Step 3: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 4b 起）` and change to `## 路由布局（Phase 5a 起）`.

Find the row whose third column begins with `用户平台专属接口。已开放：`. Replace its description with:

```markdown
用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}`、`/user/prefs` (GET + PATCH)、`/watchlist` (GET + POST + DELETE)、`/annotations` (GET-by-target + POST + PATCH + DELETE)、`/alerts/{rules,since-last-open,mark-seen}` (GET + PATCH + POST)
```

The `/` (frontend) row is unchanged in this phase — Phase 5b will update it when the banner ships.

- [ ] **Step 4: Verify all exit criteria**

Run each:
- `pytest -q` → 90 passed
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs` → 65 passed (no frontend changes)
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 17 OK
- `node --check frontend/backstage/app.js` → exit 0 (regression guard, unchanged)

- [ ] **Step 5: Commit**

```bash
git add scripts/phase1_smoke.py README.md
git commit -m "feat(api): wire alerts into smoke + docs"
```

---

## Phase 5a Exit Criteria

- [ ] `pytest -q` — 90 passed (67 prior + 6 schema + 10 diff + 7 v2 alerts)
- [ ] `node --test ...` — 65 passed (frontend untouched)
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 17 rows OK
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] Manual: with `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` running, `curl http://127.0.0.1:8013/api/v2/alerts/rules` returns the defaults; `curl -X PATCH -H 'Content-Type: application/json' -d '{"yield_delta_abs": 1.0}' http://127.0.0.1:8013/api/v2/alerts/rules` merges; the file `data/personal/alert_rules.json` exists.
- [ ] Manual: add a real mock building (e.g. `zhangjiang-park-b1`) to the watchlist via POST. `curl http://127.0.0.1:8013/api/v2/alerts/since-last-open` returns empty (no baseline yet). `curl -X POST http://127.0.0.1:8013/api/v2/alerts/mark-seen -H 'Content-Type: application/json' -d '{}'` writes baselines; `data/personal/alerts_state.json` exists. A second `since-last-open` returns empty since baselines now match current.
- [ ] `git log --oneline 8af7553..HEAD` shows exactly 4 commits

## Out of Scope (deferred)

- Frontend banner — Phase 5b
- New listing detection — needs a backend listings endpoint
- District-level alerts — Phase 5c
- Alerts for non-watchlist targets — out of scope; spec frames alerts around 关注对象
- Real-time push / WebSocket — pull-on-load only
- Manual browser screenshot
