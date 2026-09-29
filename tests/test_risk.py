import pytest
from models.black_scholes import black_scholes_price
from models.risk import spot_stress_test, volatility_stress_test, spot_vol_stress_test

BASE = dict(S=100., K=100., T=1., r=.05, sigma=.2, q=0.)


@pytest.mark.parametrize("kind", ["call", "put"])
@pytest.mark.parametrize("quantity", [-100, 0, 100])
def test_dimensions_origin_and_full_revaluation(kind, quantity):
    p = {**BASE, "option_type": kind}
    spot = spot_stress_test(**p, quantity=quantity)
    vol = volatility_stress_test(**p, quantity=quantity)
    stress = spot_vol_stress_test(**p, quantity=quantity)
    assert len(spot) == 9 and len(vol) == 5
    assert len(stress["pnl"]) == 5 and all(len(row) == 9 for row in stress["pnl"])
    assert spot[4]["pnl"] == 0 and vol[2]["pnl"] == 0 and stress["pnl"][2][4] == 0
    base = black_scholes_price(**p)
    for j, vs in enumerate(stress["vol_shocks"]):
        for i, ss in enumerate(stress["spot_shocks"]):
            expected = quantity * (black_scholes_price(**{**p, "S": p["S"] * (1 + ss),
                                                        "sigma": p["sigma"] + vs}) - base)
            assert stress["pnl"][j][i] == pytest.approx(expected)
    assert stress["pnl"][2] == pytest.approx([row["pnl"] for row in spot])
    assert [row[4] for row in stress["pnl"]] == pytest.approx([row["pnl"] for row in vol])


def test_invalid_vol_scenarios_remain_explicit():
    p = {**BASE, "sigma": .05}
    rows = volatility_stress_test(**p)
    grid = spot_vol_stress_test(**p)
    assert rows[0]["price"] is None and rows[1]["price"] is None
    assert grid["pnl"][0] == [None] * 9 and grid["pnl"][1] == [None] * 9
    assert rows[2]["pnl"] == 0


@pytest.mark.parametrize("shock", [-1, -2, float("nan")])
def test_bad_spot_shocks(shock):
    with pytest.raises(ValueError):
        spot_stress_test(**BASE, shocks=[shock])


@pytest.mark.parametrize("quantity", [True, 1.5, 1_000_001])
def test_bad_quantity(quantity):
    with pytest.raises(ValueError):
        spot_stress_test(**BASE, quantity=quantity)
