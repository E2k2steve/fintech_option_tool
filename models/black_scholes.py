"""含连续股息率的 Black-Scholes-Merton 闭式价格及解析 Greeks。"""
from math import exp, log, sqrt
from scipy.stats import norm
from .validation import validate_inputs


def _terms(S: float, K: float, T: float, r: float, sigma: float,
           q: float, option_type: str) -> tuple[float, float, float, float]:
    validate_inputs(S, K, T, r, sigma, q, option_type)
    d1 = (log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    return d1, d1 - sigma * sqrt(T), exp(-q * T), exp(-r * T)


def black_scholes_price(S: float, K: float, T: float, r: float,
                        sigma: float, q: float = 0.0,
                        option_type: str = "call") -> float:
    """返回单份欧式期权价格；T 用年，r、sigma、q 用小数。"""
    d1, d2, dq, dr = _terms(S, K, T, r, sigma, q, option_type)
    sign = 1 if option_type == "call" else -1
    price = sign * (S * dq * norm.cdf(sign * d1) - K * dr * norm.cdf(sign * d2))
    return max(float(price), 0.0)  # 清除浮点消减导致的微小负数。


def calculate_greeks(S: float, K: float, T: float, r: float,
                     sigma: float, q: float = 0.0,
                     option_type: str = "call") -> dict[str, float]:
    """返回单份风险：vega/rho 按 1.00 变化；theta 为日历时间流逝一年。"""
    d1, d2, dq, dr = _terms(S, K, T, r, sigma, q, option_type)
    sign = 1 if option_type == "call" else -1
    density = norm.pdf(d1)
    delta = sign * dq * norm.cdf(sign * d1)
    gamma = dq * density / (S * sigma * sqrt(T))
    vega = S * dq * density * sqrt(T)
    theta = (-S * dq * density * sigma / (2 * sqrt(T))
             - sign * r * K * dr * norm.cdf(sign * d2)
             + sign * q * S * dq * norm.cdf(sign * d1))
    rho = sign * K * T * dr * norm.cdf(sign * d2)
    return {"delta": float(delta), "gamma": float(gamma), "vega": float(vega),
            "theta": float(theta), "rho": float(rho),
            "vega_1pct": float(vega * 0.01), "rho_1pct": float(rho * 0.01),
            "theta_daily": float(theta / 365)}
