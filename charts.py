"""Python 构造交互式 Plotly 图，JS 运行库由同源 Flask 提供。"""
import numpy as np
import plotly.graph_objects as go
from models.black_scholes import black_scholes_price

GREEN = "#087f70"
BLUE = "#427bbf"


def _html(fig: go.Figure, chart_id: str, x_title: str, y_title: str) -> str:
    fig.update_layout(template="plotly_white", height=310,
                      margin=dict(l=60, r=20, t=25, b=55),
                      font=dict(family="Arial, Microsoft YaHei, sans-serif", size=12, color="#627077"),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis_title=x_title, yaxis_title=y_title,
                      hoverlabel=dict(bgcolor="#ffffff"), showlegend=False)
    fig.update_xaxes(gridcolor="#edf1f3", zerolinecolor="#d5dedf")
    fig.update_yaxes(gridcolor="#edf1f3", zerolinecolor="#d5dedf")
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id,
                       config={"responsive": True, "displaylogo": False,
                               "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


def create_charts(params: dict, mc: dict, spot_rows: list[dict],
                  vol_rows: list[dict], stress: dict) -> dict[str, str]:
    """生成终值分布、价格曲线、两类压力曲线以及二维热图。"""
    S = params["S"]
    spots = np.linspace(S * 0.5, S * 1.5, 81)
    prices = [black_scholes_price(**{**params, "S": float(s)}) for s in spots]
    price_fig = go.Figure(go.Scatter(x=spots.tolist(), y=prices, mode="lines",
                        line=dict(color=GREEN, width=3), fill="tozeroy",
                        fillcolor="rgba(8,127,112,.06)",
                        hovertemplate="标的价格 %{x:.2f}<br>期权价格 %{y:.4f}<extra></extra>"))
    price_fig.add_vline(x=S, line_dash="dot", line_color="#93a3a6")
    price_fig.add_scatter(x=[S], y=[black_scholes_price(**params)], mode="markers",
                         marker=dict(color=GREEN, size=8), hoverinfo="skip")
    # 用 numpy 预分箱，避免把 20 万个模拟值发送到浏览器。
    counts, edges = np.histogram(mc["terminal_prices"], bins=50)
    histogram = go.Figure(go.Bar(x=((edges[:-1] + edges[1:]) / 2).tolist(),
                         y=counts.tolist(), width=np.diff(edges).tolist(),
                         customdata=np.column_stack((edges[:-1], edges[1:])).tolist(),
                         marker_color=GREEN, opacity=.82,
                         hovertemplate="终值区间 [%{customdata[0]:.2f}, %{customdata[1]:.2f})"
                                       "<br>样本数 %{y}<extra></extra>"))
    histogram.add_vline(x=params["K"], line_dash="dash", line_color=BLUE,
                        annotation_text="执行价格 K", annotation_position="top right")
    pnl_fig = go.Figure(go.Scatter(x=[x["shock"] * 100 for x in spot_rows],
                       y=[x["pnl"] for x in spot_rows], mode="lines+markers",
                       line=dict(color=GREEN, width=3), marker=dict(size=6),
                       hovertemplate="标的冲击 %{x:+.0f}%<br>持仓 PnL %{y:+.2f}<extra></extra>"))
    pnl_fig.add_hline(y=0, line_color="#a9b6bc", line_dash="dot")
    valid_vol = [x for x in vol_rows if x["valid"]]
    vol_fig = go.Figure(go.Scatter(x=[x["volatility"] * 100 for x in valid_vol],
                       y=[x["price"] for x in valid_vol], mode="lines+markers",
                       line=dict(color=BLUE, width=3), marker=dict(size=6),
                       hovertemplate="波动率 %{x:.2f}%<br>单份价格 %{y:.4f}<extra></extra>"))
    values = [abs(v) for row in stress["pnl"] for v in row if v is not None]
    scale = max(max(values, default=0), 1e-9)
    heatmap = go.Figure(go.Heatmap(x=[x * 100 for x in stress["spot_shocks"]],
                       y=[x * 100 for x in stress["vol_shocks"]], z=stress["pnl"],
                       zmin=-scale, zmax=scale, zmid=0, hoverongaps=False,
                       colorscale=[[0, "#ba555a"], [.5, "#f7faf9"], [1, "#138777"]],
                       colorbar=dict(title="PnL", thickness=12),
                       hovertemplate="标的冲击 %{x:+.0f}%<br>波动率冲击 %{y:+.0f} 个百分点"
                                     "<br>持仓 PnL %{z:+.2f}<extra></extra>"))
    return {"price": _html(price_fig, "chart-price", "标的价格（货币单位）", "单份期权价格"),
            "histogram": _html(histogram, "chart-histogram", "到期标的价格", "样本数"),
            "spot": _html(pnl_fig, "chart-spot", "标的价格冲击（%）", "持仓 PnL"),
            "vol": _html(vol_fig, "chart-vol", "波动率（%）", "单份期权价格"),
            "heatmap": _html(heatmap, "chart-heatmap", "标的价格冲击（%）", "波动率冲击（百分点）")}
