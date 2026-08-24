from __future__ import annotations

from pipeline.scoring import _normalize


def test_normalize_higher_is_better():
    values = {1: 10.0, 2: 20.0, 3: 30.0}
    out = _normalize(values, higher_is_better=1)
    assert out[1] == 0.0
    assert out[3] == 1.0


def test_normalize_lower_is_better():
    values = {1: 10.0, 2: 20.0, 3: 30.0}
    out = _normalize(values, higher_is_better=0)
    assert out[1] == 1.0
    assert out[3] == 0.0


def test_gross_yield_formula():
    rent_m2 = 10.0
    price_m2 = 2400.0
    yield_pct = (rent_m2 * 12 / price_m2) * 100
    assert round(yield_pct, 2) == 5.0
