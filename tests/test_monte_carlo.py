import numpy as np
import pytest
from models.black_scholes import black_scholes_price
from models.monte_carlo import monte_carlo_price

BASE = dict(S=100., K=100., T=1., r=.05, sigma=.2, q=.02)


@pytest.mark.parametrize("kind", ["call", "put"])
def test_mc_close_to_bs_and_statistics(kind):
    mc = monte_carlo_price(**BASE, option_type=kind, n_simulations=50_000)
    theory = black_scholes_price(**BASE, option_type=kind)
    assert abs(mc["price"] - theory) < 4 * mc["standard_error"]
    sign = 1 if kind == "call" else -1
    values = np.exp(-BASE["r"] * BASE["T"]) * np.maximum(sign * (mc["terminal_prices"] - BASE["K"]), 0)
    assert mc["price"] == pytest.approx(values.mean())
    assert mc["standard_error"] == pytest.approx(values.std(ddof=1) / np.sqrt(len(values)))
    assert mc["confidence_interval"] == pytest.approx((mc["price"] - 1.96 * mc["standard_error"],
                                                     mc["price"] + 1.96 * mc["standard_error"]))


def test_reproducibility_and_global_rng_isolation():
    np.random.seed(123)
    expected = np.random.random(4)
    np.random.seed(123)
    a = monte_carlo_price(**BASE)
    b = monte_carlo_price(**BASE)
    np.testing.assert_array_equal(a["terminal_prices"], b["terminal_prices"])
    np.testing.assert_array_equal(np.random.random(4), expected)


def test_one_sample_no_fake_uncertainty():
    result = monte_carlo_price(**BASE, n_simulations=1)
    assert result["standard_error"] is None
    assert result["confidence_interval"] is None
    assert result["terminal_prices"].shape == (1,)


@pytest.mark.parametrize("n", [0, -1, 1.5, 200_001, True, float("nan")])
def test_bad_simulation_count(n):
    with pytest.raises(ValueError):
        monte_carlo_price(**BASE, n_simulations=n)


def test_maximum_simulation_count():
    assert monte_carlo_price(**BASE, n_simulations=200_000)["terminal_prices"].shape == (200_000,)


@pytest.mark.parametrize("seed", [-1, True, .5, 2**64])
def test_bad_seed(seed):
    with pytest.raises(ValueError):
        monte_carlo_price(**BASE, seed=seed)
