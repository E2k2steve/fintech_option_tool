"""本地入口 python app.py；Render 的 WSGI 入口为 app:app。"""
from functools import lru_cache
from math import isfinite
import os
from pathlib import Path
import re
from flask import Flask, make_response, render_template, request
from plotly.offline import get_plotlyjs
from charts import create_charts
from models.black_scholes import black_scholes_price, calculate_greeks
from models.monte_carlo import monte_carlo_price
from models.risk import spot_stress_test, volatility_stress_test, spot_vol_stress_test
from models.validation import validate_quantity, validate_simulations

DEFAULTS = {"S": "100", "K": "100", "T": "1", "r": "5", "sigma": "20", "q": "0",
            "option_type": "call", "quantity": "100", "n_simulations": "10000"}
FIELDS = (("S", "标的价格 S", .0001, 1_000_000),
          ("K", "执行价格 K", .0001, 1_000_000),
          ("T", "到期时间 T", .0001, 30), ("r", "无风险利率 r（%）", -20, 100),
          ("sigma", "波动率 σ（%）", .01, 300), ("q", "连续股息率 q（%）", 0, 100))
BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"),
            static_folder=str(BASE_DIR / "static"))
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
app.config["ONLINE_MODE"] = os.environ.get("APP_ENV", "local") == "production"


@app.get("/healthz")
def health_check():
    """供 Render 探活；不执行模拟、不读取实验文件、不依赖外部服务。"""
    return {"status": "ok"}


def parse_form(form: dict) -> tuple[dict, int, int]:
    """边界处统一把百分数转换为小数；保留中文错误。"""
    params = {}
    for key, label, low, high in FIELDS:
        try:
            value = float(form.get(key, ""))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{label} 请输入有效数字。") from exc
        if not isfinite(value) or not low <= value <= high:
            raise ValueError(f"{label} 必须在 {low:g} 至 {high:g} 之间。")
        params[key] = value / 100 if key in ("r", "sigma", "q") else value
    params["option_type"] = form.get("option_type", "")
    if params["option_type"] not in ("call", "put"):
        raise ValueError("请选择 Call（看涨）或 Put（看跌）。")
    integers = {}
    for key, label in (("quantity", "持仓数量"), ("n_simulations", "模拟次数")):
        raw = str(form.get(key, "")).strip()
        if not re.fullmatch(r"[+-]?\d{1,9}", raw):
            raise ValueError(f"{label} 必须为整数，不接受小数或科学计数法。")
        integers[key] = int(raw)
    validate_quantity(integers["quantity"])
    validate_simulations(integers["n_simulations"])
    return params, integers["quantity"], integers["n_simulations"]


def calculate_dashboard(params: dict, quantity: int, n_simulations: int) -> dict:
    """将模型结果组织成模板数据；不在模板中实现金融公式。"""
    price = black_scholes_price(**params)
    greeks = calculate_greeks(**params)
    mc = monte_carlo_price(**params, n_simulations=n_simulations)
    spot = spot_stress_test(**params, quantity=quantity)
    vol = volatility_stress_test(**params, quantity=quantity)
    stress = spot_vol_stress_test(**params, quantity=quantity)
    error = abs(mc["price"] - price)
    warnings = []
    if n_simulations == 1:
        warnings.append("只有 1 次模拟，无法估计样本标准误与 95% 置信区间。建议至少 1,000 次。")
    elif n_simulations < 1000:
        warnings.append("模拟样本较少，95% 区间为正态近似，结果可能不稳定。建议至少 1,000 次。")
    if mc["positive_payoffs"] == 0:
        warnings.append("本次样本的收益全部为零；零标准误不代表没有风险，也不能证明真实期权价值为零。")
    if any(not row["valid"] for row in vol):
        warnings.append("部分负向波动率冲击会使波动率不大于 0，已标为 N/A；未强制截断或替换情景。")
    greek_cards = [("Delta", "delta", "货币 / 标的价格单位"),
                   ("Gamma", "gamma", "Delta / 标的价格单位"),
                   ("Vega", "vega_1pct", "货币 / 波动率 +1 个百分点"),
                   ("Theta", "theta_daily", "货币 / 日历日"),
                   ("Rho", "rho_1pct", "货币 / 利率 +1 个百分点")]
    return dict(price=price, portfolio_value=quantity * price, greeks=greeks, mc=mc,
                absolute_error=error, relative_error=error / price if price > 1e-12 else None,
                spot=spot, vol=vol, stress=stress, quantity=quantity, n_simulations=n_simulations,
                greek_cards=greek_cards, warnings=warnings, params=params,
                plots=create_charts(params, mc, spot, vol, stress))


@app.template_filter("num")
def format_number(value: float | None, digits: int = 4) -> str:
    """缺失结果显式显示 N/A。"""
    return "N/A" if value is None else f"{value:,.{digits}f}"


@app.route("/", methods=["GET", "POST"])
def index():
    form = dict(DEFAULTS) if request.method == "GET" else request.form.to_dict()
    try:
        params, quantity, simulations = parse_form(form)
        result = calculate_dashboard(params, quantity, simulations)
    except ValueError as exc:
        return render_template("index.html", form=form, result=None, error=str(exc)), 422
    return render_template("index.html", form=form, result=result, error=None)


@lru_cache(maxsize=1)
def _plotly_bundle() -> str:
    return get_plotlyjs()


@app.get("/assets/plotly.min.js")
def plotly_bundle():
    """从已安装的 Plotly 包提供 JS；核心功能运行期间不访问 CDN。"""
    response = make_response(_plotly_bundle())
    response.mimetype = "application/javascript"
    response.cache_control.public = True
    response.cache_control.max_age = 86400
    return response


@app.errorhandler(413)
def too_large(_error):
    return render_template("index.html", form=dict(DEFAULTS), result=None,
                           error="提交的内容过长，请只填写数值参数。"), 413


if __name__ == "__main__":
    # 云端 Gunicorn 导入 app:app 时不会执行此分支，原有本地入口保持不变。
    app.run(host="127.0.0.1", port=5000, debug=False)
