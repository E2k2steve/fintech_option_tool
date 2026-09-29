# 最终验收记录

验收日期：2026-09-29。环境版本详见 `generated_results/summary.json`。

## 自动化验证

执行：`python -m pytest -q`，结果：**107 passed**（原版 96 项及部署新增 11 项）。

- [x] ATM Call / Put 标准价格正确。
- [x] 多组含股息、负利率参数满足 Put-Call Parity。
- [x] 五项 Greeks 经中心有限差分复核，单位缩放一致。
- [x] MC 与 BS 在合理统计容差内接近；标准误和置信区间独立复算一致。
- [x] 固定种子可重复，不影响全局随机状态。
- [x] 支持 1～200,000 次模拟，N=1 的标准误和区间为 N/A。
- [x] 三类压力测试逐情景完整重定价，矩阵维度为 5×9。
- [x] 负持仓与零持仓正确，非正波动率情景为空值。
- [x] 非法输入、缺失参数、NaN/Infinity 和超限请求不返回 500。
- [x] 默认页含五幅 Plotly 图和本地 JS 路由。

## 实际网页检查

通过 `python app.py` 启动本机服务，在浏览器打开 `http://127.0.0.1:5000`。

- [x] 中文 Dashboard 和全部五幅 Plotly 图实际渲染。
- [x] 从 Call 切换 Put 后提交，BS 从 10.4506 更新为 5.5735。
- [x] 修改 sigma=5、quantity=-100、N=1 后，警告、持仓结果、N/A 情景正确展示。
- [x] 恢复默认示例后，BS 恢复 10.4506。
- [x] 浏览器检查未捕获 JavaScript 错误。
- [x] 窄屏测试中，文档可见宽度与内容宽度一致（375px），不存在整页横向溢出。
- [x] 桌面侧栏支持独立滚动，输入和计算按钮可访问。
- [x] 压力曲线、二维热图及数值矩阵可见。

## 实验与文档

- [x] `scripts/generate_results.py` 实际运行，生成 CSV、JSON、LaTeX 表格与数值宏。
- [x] 默认 MC=10.3451820372，SE=0.1476626574，95% CI=[10.0557632287, 10.6346008456]。
- [x] 报告包含 N=1000/5000/10000/50000，以及 40 个种子的补充实验。
- [x] `report.tex` 经 XeLaTeX 多次编译，最终 15 页。
- [x] `user_manual.tex` 经 XeLaTeX 多次编译，部署版最终 7 页，已分别说明本地运行和在线访问。
- [x] 最终编译日志无错误、警告、缺失字符及 overfull/underfull 提示。
- [x] 两份 PDF 全部页面已渲染检查，中文、数学公式、表格和架构图无明显裁切或乱码。

## Render 适配验收

- [x] 新增 Gunicorn 26.2.0（当前实际安装版本）、`gunicorn.conf.py`、`render.yaml`、`.python-version`、`.env.example`。
- [x] `render.yaml` 经 YAML 解析检查，服务类型为 Python Web Service，健康检查为 `/healthz`。
- [x] Gunicorn 读取动态 PORT 并绑定 `0.0.0.0`，显式 CLI 参数覆盖 Render 默认环境参数中的固定端口。
- [x] `python app.py` 的原有 `127.0.0.1:5000`、debug=False 启动分支保留。
- [x] 复制必要运行文件到新目录，在不同工作目录启动后，首页、Put、模板、CSS、JS、Plotly 均通过检查；无需 docs 或实验文件。
- [x] HTTPS 模拟请求的表单及资源地址均为同源相对地址，没有 localhost 或 HTTP 混合资源。
- [x] 健康检查不触发定价或模拟。
- [x] `python scripts/check_deployment.py` 实际启动临时 Gunicorn 并通过 HTTP 请求验收：健康页、首页、CSS/JS/Plotly、并发 Call / Put 各 200,000 次模拟，以及中文 HTTP 422 错误页。
- [x] 实际 Gunicorn 验收从临时工作目录启动，并模拟 Render 注入 `GUNICORN_CMD_ARGS`；动态端口仍正确。检查结束后临时服务自动停止。
- [x] `pip check` 无依赖冲突。
- [x] 最新使用说明 PDF 7 页已全页渲染检查，编译日志无错误、警告或排版溢出。

## 范围说明

未发现阻碍本机课程演示或部署配置验收的未解决问题。Gunicorn 测试运行于本机 Python 3.14.7；Render 配置固定 Python 3.14.3，尚未在远端实际运行。自动化测试与浏览器验收在本机完成，未分别实测所有 Windows / Linux 版本。

本次完成部署适配，没有向用户的 Git 远端推送代码，也没有创建 Render 服务，因此尚无真实公网 URL。HTTPS 的最终可访问性与实例资源表现，应在按 README 部署后以 Render 实际服务验证；文档中的域名均为格式示例。

系统不包含真实行情、提前行权、波动率曲面或交易执行；这些属于明确的模型与项目范围，而不是待修复功能。
