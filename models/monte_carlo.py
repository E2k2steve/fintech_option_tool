"""风险中性 GBM 的精确终值采样；不引入时间离散误差。"""
from math import exp, sqrt
from numbers import Integral
from typing import TypedDict
import numpy as np
from numpy.typing import NDArray
from .validation import validate_inputs, validate_simulations


class MonteCarloResult(TypedDict):
    price: float
    standard_error: float | None
    confidence_interval: tuple[float, float] | None
    terminal_prices: NDArray[np.float64]
    positive_payoffs: int


def monte_carlo_price(S: float, K: float, T: float, r: float, sigma: float,
                      q: float = 0.0, option_type: str = "call",
                      n_simulations: int = 10_000, seed: int = 42) -> MonteCarloResult:
    """估计单份价值及 95% 正态近似区间；N=1 时标准误和区间不可估计。

    固定局部生成器不会修改全局随机状态。区间反映抽样不确定性，非市场风险区间。
    """
    validate_inputs(S, K, T, r, sigma, q, option_type)
    validate_simulations(n_simulations)
    if isinstance(seed, bool) or not isinstance(seed, Integral) or not 0 <= seed < 2**64:
        raise ValueError("随机种子必须是 0 至 2^64-1 的整数。")
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n_simulations)
    with np.errstate(over="raise", invalid="raise"):
        try:
            terminal = S * np.exp((r - q - 0.5 * sigma**2) * T + sigma * sqrt(T) * z)
            sign = 1 if option_type == "call" else -1
            discounted = exp(-r * T) * np.maximum(sign * (terminal - K), 0.0)
            price = float(discounted.mean())
            se = float(discounted.std(ddof=1) / sqrt(n_simulations)) if n_simulations > 1 else None
        except (FloatingPointError, OverflowError) as exc:
            raise ValueError("参数组合超出数值计算范围，请缩小期限、利率或波动率。") from exc
    ci = (price - 1.96 * se, price + 1.96 * se) if se is not None else None
    return {"price": price, "standard_error": se, "confidence_interval": ci,
            "terminal_prices": terminal, "positive_payoffs": int(np.count_nonzero(discounted))}
