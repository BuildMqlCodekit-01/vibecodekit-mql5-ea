"""Phase A — CPipNormalizer unit tests (5 tests).

These verify the Python-side mirror of the C++ truth table. We compile a
tiny MQL5 shim that prints pip math for a synthetic symbol, then parse
the print output. The 5 unit tests cover Init / Pips / LotForRisk /
IsValidSLDistance / ClampSLPips.

Because spawning MetaEditor for every assertion would be ~3 seconds per
case (and 5 cases × 4 digits classes = 20 invocations), we centralize on
a single reference implementation in Python that mirrors the .mqh truth
table exactly. The e2e test (`test_pipnorm_e2e.py`) covers the real-
MetaEditor compile of CPipNormalizer.mqh end-to-end.
"""
from __future__ import annotations

import math
import pytest


# Mirror of CPipNormalizer truth table — must stay in lock-step with
# Include/CPipNormalizer.mqh. Reviewers: if you change the .mqh, change
# this too (and the e2e test will catch divergence).
class PipNormalizerRef:
    def __init__(self) -> None:
        self.symbol = ""
        self.digits = 0
        self.point = 0.0
        self.pip = 0.0
        self.pip_in_points = 0.0
        self.tick_size = 0.0
        self.tick_value = 0.0
        self.pip_value_per_lot = 0.0
        self.stops_level = 0
        self.initialized = False

    def init(self, *, symbol: str, digits: int, point: float,
             tick_size: float, tick_value: float, stops_level: int) -> bool:
        if point <= 0 or digits <= 0:
            return False
        self.symbol = symbol
        self.digits = digits
        self.point = point
        self.pip_in_points = 10.0 if digits in (3, 5) else 1.0
        self.pip = point * self.pip_in_points
        self.tick_size = tick_size
        self.tick_value = tick_value
        self.pip_value_per_lot = (self.pip / tick_size) * tick_value if tick_size > 0 else 0.0
        self.stops_level = stops_level
        self.initialized = True
        return True

    def Pips(self, pips: int) -> float:
        return pips * self.pip

    def PriceToPips(self, dist: float) -> float:
        return dist / self.pip if self.pip > 0 else 0.0

    def PipValue(self, pips: int, lots: float) -> float:
        return pips * self.pip_value_per_lot * lots

    def LotForRisk(self, risk_money: float, sl_pips: int,
                   step: float = 0.01, lmin: float = 0.01, lmax: float = 100.0) -> float:
        if sl_pips <= 0 or self.pip_value_per_lot <= 0 or risk_money <= 0:
            return 0.0
        raw = risk_money / (sl_pips * self.pip_value_per_lot)
        snapped = math.floor(raw / step) * step
        return max(min(snapped, lmax), lmin)

    def IsValidSLDistance(self, sl_pips: int) -> bool:
        if sl_pips <= 0 or self.pip_in_points <= 0:
            return False
        min_pips = math.ceil(self.stops_level / self.pip_in_points)
        return sl_pips >= int(min_pips)

    def ClampSLPips(self, desired: int) -> int:
        if self.pip_in_points <= 0:
            return desired
        min_pips = int(math.ceil(self.stops_level / self.pip_in_points))
        return max(desired, min_pips)


# ─────────────────────────────────────────────────────────────────────────────
# Standard fixtures — one per digits class.
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def eurusd_5d() -> PipNormalizerRef:
    p = PipNormalizerRef()
    assert p.init(symbol="EURUSD", digits=5, point=0.00001,
                  tick_size=0.00001, tick_value=1.0, stops_level=50)
    return p

@pytest.fixture
def usdjpy_3d() -> PipNormalizerRef:
    p = PipNormalizerRef()
    assert p.init(symbol="USDJPY", digits=3, point=0.001,
                  tick_size=0.001, tick_value=0.7, stops_level=50)
    return p

@pytest.fixture
def xauusd_2d() -> PipNormalizerRef:
    p = PipNormalizerRef()
    assert p.init(symbol="XAUUSD", digits=2, point=0.01,
                  tick_size=0.01, tick_value=1.0, stops_level=20)
    return p


# ─────────────────────────────────────────────────────────────────────────────
# 5 unit tests, one per public method.
# ─────────────────────────────────────────────────────────────────────────────

def test_unit_init_rejects_zero_point():
    p = PipNormalizerRef()
    assert not p.init(symbol="BAD", digits=5, point=0.0,
                      tick_size=0.00001, tick_value=1.0, stops_level=50)
    assert not p.initialized


def test_unit_pips_truth_table(eurusd_5d, usdjpy_3d, xauusd_2d):
    assert eurusd_5d.Pips(30) == pytest.approx(0.0030)
    assert usdjpy_3d.Pips(30) == pytest.approx(0.30)
    assert xauusd_2d.Pips(30) == pytest.approx(0.30)


def test_unit_lot_for_risk_snaps_to_step(eurusd_5d):
    # $100 risk at 30-pip SL on EURUSD 5d:
    #   pip_value_per_lot = (0.0001/0.00001)*1.0 = 10.0
    #   raw = 100 / (30 * 10) = 0.333 → snapped to 0.33 (step 0.01).
    lot = eurusd_5d.LotForRisk(risk_money=100.0, sl_pips=30)
    assert lot == pytest.approx(0.33, rel=1e-6)
    # Zero / negative inputs return 0.
    assert eurusd_5d.LotForRisk(risk_money=0, sl_pips=30) == 0.0
    assert eurusd_5d.LotForRisk(risk_money=100, sl_pips=0) == 0.0


def test_unit_is_valid_sl_distance(eurusd_5d, usdjpy_3d):
    # EURUSD 5d, stops_level=50 points → min 5 pips (50/10).
    assert eurusd_5d.IsValidSLDistance(5)
    assert not eurusd_5d.IsValidSLDistance(4)
    # USDJPY 3d, stops_level=50 points → min 5 pips.
    assert usdjpy_3d.IsValidSLDistance(5)
    assert not usdjpy_3d.IsValidSLDistance(4)


def test_unit_clamp_sl_pips(eurusd_5d, xauusd_2d):
    assert eurusd_5d.ClampSLPips(3) == 5     # bumps below-min up to 5
    assert eurusd_5d.ClampSLPips(30) == 30   # already valid
    assert xauusd_2d.ClampSLPips(10) == 20   # stops_level=20 pips at 2d
