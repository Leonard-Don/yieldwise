from __future__ import annotations

from api.service import compute_payback_years, compute_yield_pct


def test_payback_years_basic_round_trip() -> None:
    # 800万 sale price, 12000元/月 rent → 年租 144_000 → 8_000_000 / 144_000 ≈ 55.6 年
    assert compute_payback_years(800, 12000) == 55.6


def test_payback_years_is_inverse_of_yield_when_yield_nonzero() -> None:
    sale_wan, rent_monthly = 600.0, 25000.0
    yield_pct = compute_yield_pct(sale_wan, rent_monthly)
    payback = compute_payback_years(sale_wan, rent_monthly)
    # 100 / yield_pct should approximate payback (rounding may shift slightly).
    assert abs(payback - 100 / yield_pct) < 0.2


def test_payback_years_zero_when_inputs_missing() -> None:
    assert compute_payback_years(None, 12000) == 0.0
    assert compute_payback_years(800, None) == 0.0
    assert compute_payback_years(0, 12000) == 0.0
    assert compute_payback_years(800, 0) == 0.0


def test_payback_years_higher_yield_means_shorter_payback() -> None:
    lower_yield = compute_payback_years(2000, 8000)   # ~208 yrs (low yield, expensive)
    higher_yield = compute_payback_years(300, 8000)   # ~31 yrs (high yield, cheap)
    assert higher_yield < lower_yield
