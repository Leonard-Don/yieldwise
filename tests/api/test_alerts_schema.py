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
