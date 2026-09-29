"""压力测试均采用完整重定价，固定剩余期限；不计算到期损益。"""
from collections.abc import Sequence
from .black_scholes import black_scholes_price
from .validation import finite_number, validate_quantity

SPOT_SHOCKS = (-0.20, -0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20)
VOL_SHOCKS = (-0.10, -0.05, 0.0, 0.05, 0.10)


def _spot_shocks(shocks: Sequence[float]) -> list[float]:
    result = [finite_number(x, "标的冲击") for x in shocks]
    if not result or any(x <= -1 for x in result):
        raise ValueError("标的冲击列表不能为空，且各冲击必须大于 -100%。")
    return result


def spot_stress_test(S: float, K: float, T: float, r: float, sigma: float,
                     q: float = 0.0, option_type: str = "call", quantity: int = 100,
                     shocks: Sequence[float] = SPOT_SHOCKS) -> list[dict]:
    """相对价格冲击；返回单份价格与 quantity 倍的持仓 PnL。"""
    validate_quantity(quantity)
    base = black_scholes_price(S, K, T, r, sigma, q, option_type)
    rows = []
    for shock in _spot_shocks(shocks):
        spot = S * (1 + shock)
        price = black_scholes_price(spot, K, T, r, sigma, q, option_type)
        rows.append({"shock": shock, "spot": spot, "price": price,
                     "value": quantity * price, "pnl": quantity * (price - base)})
    return rows


def volatility_stress_test(S: float, K: float, T: float, r: float, sigma: float,
                           q: float = 0.0, option_type: str = "call", quantity: int = 100,
                           shocks: Sequence[float] = VOL_SHOCKS) -> list[dict]:
    """绝对波动率冲击：0.05 表示 +5 个百分点；非正波动率标为无效。"""
    validate_quantity(quantity)
    base = black_scholes_price(S, K, T, r, sigma, q, option_type)
    if not len(shocks):
        raise ValueError("波动率冲击列表不能为空。")
    rows = []
    for shock in shocks:
        shock = finite_number(shock, "波动率冲击")
        vol = sigma + shock
        valid = vol > 1e-10  # 忽略浮点舍入产生的近零波动率。
        price = black_scholes_price(S, K, T, r, vol, q, option_type) if valid else None
        rows.append({"shock": shock, "volatility": vol, "valid": valid, "price": price,
                     "value": quantity * price if valid else None,
                     "pnl": quantity * (price - base) if valid else None})
    return rows


def spot_vol_stress_test(S: float, K: float, T: float, r: float, sigma: float,
                         q: float = 0.0, option_type: str = "call", quantity: int = 100,
                         spot_shocks: Sequence[float] = SPOT_SHOCKS,
                         vol_shocks: Sequence[float] = VOL_SHOCKS) -> dict:
    """矩阵按 [波动率冲击行][标的冲击列] 排列；无效情景保留 None。"""
    spots = _spot_shocks(spot_shocks)
    vols = volatility_stress_test(S, K, T, r, sigma, q, option_type, quantity, vol_shocks)
    matrix = []
    for row in vols:
        if not row["valid"]:
            matrix.append([None] * len(spots))
            continue
        # 基准必须是原始 sigma 下的当前价格，而非波动率冲击后的价格。
        base = black_scholes_price(S, K, T, r, sigma, q, option_type)
        matrix.append([quantity * (black_scholes_price(S * (1 + shock), K, T, r,
                       row["volatility"], q, option_type) - base) for shock in spots])
    return {"spot_shocks": spots, "vol_shocks": [row["shock"] for row in vols],
            "pnl": matrix}
