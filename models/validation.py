"""供模型和 Web 层共用的数值检查。"""
from math import isfinite
from numbers import Integral, Real


def finite_number(value: float, name: str) -> float:
    """拒绝布尔值、非实数、NaN 与无穷。"""
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f"{name} 必须是有限数值。")
    return float(value)


def validate_inputs(S: float, K: float, T: float, r: float, sigma: float,
                    q: float, option_type: str) -> None:
    """校验参数；上限用于保护教学程序的浮点数计算。"""
    for name, value, upper in (("S", S, 1e12), ("K", K, 1e12),
                               ("T", T, 100), ("sigma", sigma, 10)):
        value = finite_number(value, name)
        if not 1e-10 <= value <= upper:
            raise ValueError(f"{name} 必须大于 0，且在 [1e-10, {upper:g}] 内。")
    for name, value in (("r", r), ("q", q)):
        if abs(finite_number(value, name)) > 2:
            raise ValueError(f"{name} 的绝对值不能超过 2（200%）。")
    if option_type not in ("call", "put"):
        raise ValueError("期权类型只能为 call 或 put。")


def validate_quantity(quantity: int) -> None:
    """数量按期权份数计；负数表示空头，合约乘数为 1。"""
    if isinstance(quantity, bool) or not isinstance(quantity, Integral) or abs(quantity) > 1_000_000:
        raise ValueError("持仓数量必须是 -1,000,000 至 1,000,000 的整数。")


def validate_simulations(n_simulations: int) -> None:
    """限制样本量，避免网页请求占用过多内存。"""
    if (isinstance(n_simulations, bool) or not isinstance(n_simulations, Integral)
            or not 1 <= n_simulations <= 200_000):
        raise ValueError("模拟次数必须为 1 至 200,000 的整数。")
