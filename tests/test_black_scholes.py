"""解析基准、无套利关系以及独立有限差分检验。"""
from math import exp
import pytest
from models.black_scholes import black_scholes_price as price, calculate_greeks

BASE = dict(S=100., K=100., T=1., r=.05, sigma=.2, q=0.)


@pytest.mark.parametrize("kind, expected", [("call", 10.450583572185565), ("put", 5.573526022256971)])
def test_reference_prices(kind, expected):
    assert price(**BASE, option_type=kind) == pytest.approx(expected, abs=1e-10)


@pytest.mark.parametrize("S", [60, 100, 160])
@pytest.mark.parametrize("q, r", [(0, .05), (.03, -.01)])
def test_put_call_parity(S, q, r):
    p = {**BASE, "S": S, "q": q, "r": r}
    assert price(**p, option_type="call") - price(**p, option_type="put") == pytest.approx(
        S * exp(-q * p["T"]) - p["K"] * exp(-r * p["T"]), abs=1e-11)


@pytest.mark.parametrize("kind", ["call", "put"])
@pytest.mark.parametrize("S", [70, 100, 130])
def test_delta_ranges_and_positive_gamma_vega(kind, S):
    g = calculate_greeks(**{**BASE, "S": S, "q": .03}, option_type=kind)
    lo, hi = (0, exp(-.03)) if kind == "call" else (-exp(-.03), 0)
    assert lo <= g["delta"] <= hi
    assert g["gamma"] > 0 and g["vega"] > 0


@pytest.mark.parametrize("kind", ["call", "put"])
@pytest.mark.parametrize("q, r", [(0, .05), (.03, -.01)])
def test_all_greeks_against_finite_differences(kind, q, r):
    p = {**BASE, "S": 105., "q": q, "r": r, "option_type": kind}
    g = calculate_greeks(**p)
    for key, greek, step in [("S", "delta", .001), ("sigma", "vega", 1e-5),
                             ("r", "rho", 1e-5), ("T", "theta", 1e-5)]:
        derivative = (price(**{**p, key: p[key] + step}) - price(**{**p, key: p[key] - step})) / (2 * step)
        if greek == "theta":
            derivative = -derivative
        assert g[greek] == pytest.approx(derivative, rel=2e-6, abs=1e-7)
    h = .01
    gamma = (price(**{**p, "S": p["S"] + h}) - 2 * price(**p)
             + price(**{**p, "S": p["S"] - h})) / h**2
    assert g["gamma"] == pytest.approx(gamma, rel=1e-6)
    assert g["vega_1pct"] == g["vega"] * .01
    assert g["rho_1pct"] == g["rho"] * .01
    assert g["theta_daily"] == g["theta"] / 365


@pytest.mark.parametrize("key", ["S", "K", "T", "sigma"])
@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), True])
def test_invalid_positive_parameters(key, value):
    for function in (price, calculate_greeks):
        with pytest.raises(ValueError):
            function(**{**BASE, key: value})


@pytest.mark.parametrize("key", ["r", "q"])
def test_invalid_rates(key):
    with pytest.raises(ValueError):
        price(**{**BASE, key: float("nan")})


def test_invalid_option_type():
    with pytest.raises(ValueError):
        price(**BASE, option_type="american")
