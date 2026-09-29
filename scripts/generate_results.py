"""从项目根目录运行 python scripts/generate_results.py 重建实验数据。"""
import csv
import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from models.black_scholes import black_scholes_price, calculate_greeks
from models.monte_carlo import monte_carlo_price
from models.risk import spot_stress_test, volatility_stress_test, spot_vol_stress_test

PARAMS = dict(S=100., K=100., T=1., r=.05, sigma=.2, q=0., option_type="call")
OUT = ROOT / "docs" / "generated_results"


def write_csv(name: str, rows: list[dict]) -> None:
    """写入 UTF-8 CSV，字段名称来自记录，浮点数保留 Python 默认精度。"""
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def latex_table(name: str, headers: list[str], rows: list[list[str]]) -> None:
    """产生可供 report.tex input 的 booktabs 表格。"""
    lines = [r"\begin{tabular}{" + "l" + "r" * (len(headers) - 1) + "}", r"\toprule",
             " & ".join(headers) + r" \\", r"\midrule"]
    lines.extend(" & ".join(row) + r" \\" for row in rows)
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bs = black_scholes_price(**PARAMS)
    g = calculate_greeks(**PARAMS)
    experiments = []
    for n in [1000, 5000, 10000, 50000]:
        m = monte_carlo_price(**PARAMS, n_simulations=n)
        experiments.append(dict(n=n, bs_price=bs, mc_price=m["price"],
                          absolute_error=abs(m["price"] - bs),
                          relative_error=abs(m["price"] - bs) / bs,
                          standard_error=m["standard_error"],
                          ci_lower=m["confidence_interval"][0], ci_upper=m["confidence_interval"][1]))
    write_csv("mc_convergence.csv", experiments)
    spot = spot_stress_test(**PARAMS)
    vol = volatility_stress_test(**PARAMS)
    grid = spot_vol_stress_test(**PARAMS)
    write_csv("spot_stress.csv", spot)
    write_csv("volatility_stress.csv", vol)
    write_csv("stress_grid.csv", [dict(vol_shock=vs, spot_shock=ss, pnl=grid["pnl"][j][i])
              for j, vs in enumerate(grid["vol_shocks"]) for i, ss in enumerate(grid["spot_shocks"])])
    write_csv("greeks.csv", [dict(metric=k, per_option=v, portfolio=100 * v) for k, v in g.items()])
    write_csv("price_curve.csv", [dict(spot=float(s), price=black_scholes_price(**{**PARAMS, "S": float(s)}))
              for s in np.linspace(60, 140, 81)])
    m = monte_carlo_price(**PARAMS)
    counts, bins = np.histogram(m["terminal_prices"], bins=40)
    write_csv("terminal_histogram.csv", [dict(terminal=(bins[i] + bins[i+1]) / 2, count=int(c))
              for i, c in enumerate(counts)])
    # 多个独立种子补充检验 O(N^-1/2)，不把单次误差的偶然下降当作必然规律。
    repeated = []
    for n in [1000, 5000, 10000, 50000]:
        runs = [monte_carlo_price(**PARAMS, n_simulations=n, seed=seed) for seed in range(100, 140)]
        errors = np.array([run["price"] - bs for run in runs])
        repeated.append(dict(n=n, seeds=40, rmse=float(np.sqrt(np.mean(errors**2))),
                             mean_se=float(np.mean([run["standard_error"] for run in runs])),
                             coverage=float(np.mean([run["confidence_interval"][0] <= bs <=
                                                    run["confidence_interval"][1] for run in runs]))))
    write_csv("mc_repeated_seeds.csv", repeated)
    summary = dict(parameters=PARAMS, quantity=100, seed=42, bs_price=bs,
                   put_price=black_scholes_price(**{**PARAMS, "option_type": "put"}),
                   portfolio_value=100 * bs, greeks=g, mc=experiments[2],
                   environment={"python": platform.python_version(), **{name: version(name)
                                for name in ["Flask", "numpy", "scipy", "plotly", "pytest"]}})
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metrics = [("BS 单份价格", bs), ("BS 持仓价值", 100 * bs), ("MC 单份价格", m["price"]),
               ("Delta", g["delta"]), ("Gamma", g["gamma"]),
               ("Vega（每 1 pp）", g["vega_1pct"]), ("Theta（每日）", g["theta_daily"]),
               ("Rho（每 1 pp）", g["rho_1pct"]), ("MC 标准误", m["standard_error"])]
    latex_table("baseline_table.tex", ["指标", "结果"], [[k, f"{v:.6f}"] for k, v in metrics])
    latex_table("mc_table.tex", [r"$N$", "MC 价格", "绝对误差", "标准误", r"95\% 区间"],
                [[str(x["n"]), f'{x["mc_price"]:.5f}', f'{x["absolute_error"]:.5f}',
                  f'{x["standard_error"]:.5f}', f'[{x["ci_lower"]:.5f}, {x["ci_upper"]:.5f}]'] for x in experiments])
    latex_table("repeated_table.tex", [r"$N$", "RMSE", "平均标准误", "区间覆盖次数/40"],
                [[str(x["n"]), f'{x["rmse"]:.5f}', f'{x["mean_se"]:.5f}',
                  str(round(x["coverage"] * 40))] for x in repeated])
    latex_table("spot_table.tex", ["标的冲击", "新标的价格", "单份价格", "持仓 PnL"],
                [[f'{x["shock"]*100:+.0f}\\%', f'{x["spot"]:.2f}', f'{x["price"]:.5f}',
                  f'{x["pnl"]:+.4f}'] for x in spot])
    latex_table("vol_table.tex", ["波动率冲击", "新波动率", "单份价格", "持仓 PnL"],
                [[f'{x["shock"]*100:+.0f} pp', f'{x["volatility"]*100:.0f}\\%',
                  f'{x["price"]:.5f}', f'{x["pnl"]:+.4f}'] for x in vol])
    (OUT / "macros.tex").write_text("\n".join([
        rf"\newcommand{{\BSPrice}}{{{bs:.6f}}}",
        rf"\newcommand{{\MCPrice}}{{{m['price']:.6f}}}",
        rf"\newcommand{{\MCLower}}{{{m['confidence_interval'][0]:.6f}}}",
        rf"\newcommand{{\MCUpper}}{{{m['confidence_interval'][1]:.6f}}}",
        rf"\newcommand{{\MCError}}{{{experiments[2]['absolute_error']:.6f}}}",
        rf"\newcommand{{\MCRelative}}{{{experiments[2]['relative_error']*100:.4f}}}",
        rf"\newcommand{{\SpotDown}}{{{spot[0]['pnl']:.4f}}}",
        rf"\newcommand{{\SpotUp}}{{{spot[-1]['pnl']:.4f}}}",
        rf"\newcommand{{\GridLow}}{{{grid['pnl'][0][0]:.4f}}}",
        rf"\newcommand{{\GridHigh}}{{{grid['pnl'][-1][-1]:.4f}}}",
    ]) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"已生成实验结果：{OUT}")


if __name__ == "__main__":
    main()
