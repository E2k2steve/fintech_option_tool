# 期权定价与风险管理可视化系统

基于 Black-Scholes 与 Monte Carlo 的金融科技课程原型。输入欧式期权参数，比较解析价格与模拟价格、查看 Greeks，并通过完整重定价分析市场冲击。支持本地运行与 Render 在线部署，无需数据库、应用账号或金融 API。本地依赖安装完成后可离线运行；在线用户只需要浏览器和网络，不需要安装 Python。

## 已完成功能

- 含连续股息的欧式 Call / Put 定价，单份及总持仓价值。
- Delta、Gamma、Vega、Theta、Rho，单份及持仓敞口。
- 风险中性 GBM 精确终值采样、固定随机种子 42、标准误、95% 正态近似置信区间。
- Spot、Volatility 和二维 Spot × Volatility 压力测试；每个情景完整重定价。
- 五幅 Plotly 交互图，二维 HTML 数值矩阵，中文输入错误、基本响应式页面。
- 模型与部署自动测试、四组示例参数、可重复实验脚本、CSV/JSON 结果、中文报告和使用说明。
- Render Blueprint、Gunicorn、轻量健康检查与可迁移的模板/静态资源路径。

## 本地运行方式

需要 Python 3.10+。打开终端，进入本 README 所在的 `fintech_option_tool` 目录。

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

Windows CMD：

```bat
.venv\Scripts\activate
```

macOS / Linux：

```bash
source .venv/bin/activate
```

安装并启动：

```bash
python -m pip install -r requirements.txt
python app.py
```

浏览器访问 [http://127.0.0.1:5000](http://127.0.0.1:5000)。终端按 `Ctrl+C` 停止。
macOS / Linux 若只有 `python3`，创建环境时使用 `python3`；激活后使用 `python`。
依赖仅在首次安装时需要网络；完全离线的目标电脑须事先准备对应系统和 Python 版本的依赖包。

端口 5000 已被占用时：

```bash
python -m flask --app app run --host 127.0.0.1 --port 5001
```

然后访问 `http://127.0.0.1:5001`。默认仅绑定本机，debug 关闭。

本地启动方式保持为 `python app.py`，不需要 Gunicorn。Windows 安装 requirements 时会自动跳过仅支持 Unix 的 Gunicorn，其余功能不受影响。

## 在线访问方式（使用者无需安装 Python）

1. 从部署者取得 Render 服务页面显示的 **HTTPS 公网 URL**，形如 `https://<实际服务名>.onrender.com`。这里是格式示例，不是已经上线的地址。
2. 在电脑、平板或手机浏览器中打开该地址，保持网络连接并启用 JavaScript。
3. 首页自动计算默认示例。修改参数、切换 Call / Put，点击“计算价格与风险”即可使用完整的 Black-Scholes、Monte Carlo、Greeks 和三类 Stress Test 功能。
4. 图表支持悬停、缩放与导出，二维矩阵和全部错误提示与本地版一致。

在线计算在 Render 服务器执行，访问者无需下载安装包、Python、虚拟环境或 LaTeX，也不需要 Render 账号。部署成功后，即使开发者关闭自己的电脑，其他用户仍通过 Render 地址访问。`127.0.0.1` 始终指访问者自己的电脑，不能作为对外分享链接。

Render Web Service 提供 `onrender.com` 地址和 HTTPS，平台终止 TLS 后将请求转给 Gunicorn，无需在 Flask 中安装证书。[官方说明](https://render.com/docs/web-services)
免费实例可能在闲置 15 分钟后休眠，下次打开需要等待唤醒；课堂演示前可先打开网页。额度与实例限制以 [Render Free 文档](https://render.com/docs/free) 为准。

## Render 部署方式（项目维护者）

当前交付的是部署配置，尚未在你的 Render 账号创建服务，也没有生成真实公网 URL。完成下列部署后，复制控制台实际显示的 HTTPS 地址给使用者。

### 1. 准备 Git 仓库

建议将 **`fintech_option_tool` 文件夹内的内容**作为 Git 仓库根目录。仓库根应直接包含 `app.py`、`render.yaml`、`.python-version`、`gunicorn.conf.py`、`requirements.txt`、`models/`、`templates/`、`static/`，文件名大小写保持不变。

将代码推送到可由 Render 访问的 GitHub/GitLab/Bitbucket 仓库。不要提交 `.venv`、`.env`、缓存或临时文件，项目已配置 `.gitignore`。运行服务不需要实验 CSV、PDF、XeLaTeX 或本机任何绝对路径。

若仓库根是外层 `TueEvening`，而应用仍在 `fintech_option_tool/` 子目录：手动创建服务时将 **Root Directory** 设置为 `fintech_option_tool`；使用 Blueprint 时选取 `fintech_option_tool/render.yaml`，并在其中该服务的 `runtime: python` 同级增加 `rootDir: fintech_option_tool`。Blueprint 文件所在目录不会自动成为服务根目录。[Blueprint 路径规则](https://render.com/docs/blueprint-spec)

### 2. 使用 Blueprint 部署

在 Render 控制台选择 **New → Blueprint**，连接代码仓库，选取仓库中的 `render.yaml`，核对服务名和 Free 实例后创建。默认按上一节推荐的仓库根布局运行。

配置已包含 Python Web Service、依赖安装命令、Gunicorn 启动命令、`/healthz` 健康检查和环境变量。模型数据来自请求内存，不需要数据库、持久磁盘或金融 API 密钥。

### 3. 或手动创建 Web Service

选择 **New → Web Service**（不是 Static Site），连接仓库，填写：

| Render 设置 | 值 |
|---|---|
| Language / Runtime | Python 3 |
| Root Directory | 推荐布局留空；外层仓库则填 `fintech_option_tool` |
| Build Command | `python -m pip install -r requirements.txt` |
| Start Command | `gunicorn --config gunicorn.conf.py --bind "0.0.0.0:${PORT:-10000}" app:app` |
| Health Check Path | `/healthz` |
| Instance Type | Free（课程演示配置） |

然后把下一节中的环境变量加入 Environment。点击部署，等待状态为 **Live**。服务的公网 HTTPS 地址以控制台为准，不要假定服务名一定对应某个未验证的域名。[Flask 官方部署指南](https://render.com/docs/deploy-flask)

### 4. 环境设置

| 设置 | 默认值及用途 |
|---|---|
| `.python-version` | `3.14.3`，固定 Render 的 Python 运行时；本地仍支持 Python 3.10+ |
| `APP_ENV` | `production`，网页显示“在线计算”；本地未设置时显示“本地计算” |
| `PORT` | 由 Render 注入，Gunicorn 绑定 `0.0.0.0:$PORT`，回退值为 10000 |
| `WEB_CONCURRENCY` | `1` 个 worker，控制课程实例内存占用 |
| `GUNICORN_THREADS` | `2` 个请求线程 |
| `GUNICORN_TIMEOUT` | `120` 秒，worker 超时设置 |
| `PYTHONUNBUFFERED` | `1`，即时输出部署日志 |
| `OPENBLAS_NUM_THREADS` / `OMP_NUM_THREADS` | 均为 `1`，限制底层计算库线程数量 |

`.env.example` 仅是配置说明文件，程序不会自动读取 `.env`。Render 上请使用控制台环境变量或 Blueprint。没有登录、会话和数据库，不需要添加无用途的 `SECRET_KEY` 或数据库密码。

`.python-version` 采用 Render 支持的完整版本；若控制台原来设置过 `PYTHON_VERSION`，该变量会覆盖文件，应删除冲突值或设为同一版本。[Python 版本优先级](https://render.com/docs/python-version)
启动命令显式传入 `--bind`，可以覆盖平台默认 `GUNICORN_CMD_ARGS` 中的固定端口，确保修改 `PORT` 后仍生效。[默认环境变量](https://render.com/docs/environment-variables)

### 5. 部署后检查

- 访问 HTTPS 首页，确认默认 BS 为 10.4506，MC 约为 10.3452，五幅图和二维矩阵显示正常。
- 切换 Put 并提交，默认 BS 应变为 5.5735；修改 quantity 和 N 后重新计算。
- 访问 `/healthz`，应返回 `{"status":"ok"}`；访问 `/static/css/style.css`、`/static/js/main.js`、`/assets/plotly.min.js` 应返回 200。
- 若出现 `ModuleNotFoundError`、找不到 requirements 或模板，检查 Root Directory、Git 中是否遗漏文件及文件名大小写；若端口未检测到，使用上述完整 Gunicorn 命令。

模板与静态目录从 `app.py` 自身所在位置解析，不从终端工作目录或 `/Users/...` 读取。表单及资源通过 `url_for` 生成同源相对 URL，在线页面不指向 localhost、不产生 HTTP 混合内容。Plotly 由同一服务器的 Python 包提供，云端也不依赖图表 CDN。

在 macOS / Linux 本机验证 Gunicorn（先激活虚拟环境）：

```bash
APP_ENV=production PORT=10000 gunicorn --config gunicorn.conf.py --bind "0.0.0.0:10000" app:app
```

随后打开 `http://127.0.0.1:10000`。这是本机 HTTP 检查；公网 HTTPS 由实际部署后的 Render 提供。原有 `python app.py` 仍独立使用本机 5000 端口。

## 操作与单位

网页默认 S=100、K=100、T=1 年、r=5%、sigma=20%、q=0%、Call、quantity=100、N=10000。点击“计算价格与风险”更新所有结果；“恢复默认示例”恢复这些参数。

| 参数 | 网页输入 | 限制 |
|---|---|---|
| S / K | 同一种货币单位 | 0.0001～1,000,000 |
| T | 年 | 0.0001～30 |
| r | 百分数，5 表示 5% | −20%～100% |
| sigma | 百分数，20 表示 20% | 0.01%～300% |
| q | 年化连续股息率百分数 | 0%～100% |
| quantity | 整数份数 | −1,000,000～1,000,000；负数为空头 |
| N | 正整数 | 1～200,000；推荐至少 1,000 |

边界是教学程序的计算保护范围。模型 API 使用小数：r=0.05、sigma=0.20；与网页百分数不同。

所有金额使用同一货币单位，合约乘数固定为 1。若一个现实合约代表多份基础单位，须自己换算成份数。本系统不假定某个交易所的合约乘数。

- Delta = ∂V/∂S；Gamma = ∂²V/∂S²。
- 原始 Vega = ∂V/∂sigma，原始 Rho = ∂V/∂r，均按小数变化 1.00 计；卡片展示原始值 × 0.01，即每增加 **1 个百分点**的局部价值影响。
- 年化 Theta = −∂V/∂T；日 Theta = 年化 Theta / 365。固定当前状态的一阶时间敏感度不是精确的一日重定价。
- 所有持仓 Greeks = quantity × 单份 Greeks。
- 压力测试固定 T，PnL = quantity × (情景 BS 价格 − 当前 BS 价格)，不代表到期收益。
- 波动率冲击使用百分点：20% + 5 pp = 25%。非正波动率情景显示 N/A，热图为空白，不截断为其他值。
- MC 标准误用折现收益的样本标准差（ddof=1）除以 √N。95% 区间 = MC ± 1.96 SE，是正态近似，不是未来收益的概率区间。
- N=1 无法估计标准误和区间，显示 N/A；全部样本收益为零时明确警告；BS 接近零时相对误差显示 N/A。

## 项目结构

```text
fintech_option_tool/
├── app.py                       # Flask 路由、参数解析、结果组织
├── charts.py                    # Python 生成五幅交互图
├── requirements.txt             # 跨 Python 版本兼容的依赖范围
├── render.yaml                  # Render Blueprint
├── gunicorn.conf.py             # WSGI worker、线程、日志与端口配置
├── .python-version              # Render Python 运行时
├── .env.example                 # 环境变量说明（不会自动加载）
├── pytest.ini
├── README.md
├── models/
│   ├── black_scholes.py         # 闭式定价与 Greeks
│   ├── monte_carlo.py           # GBM、标准误、置信区间
│   ├── risk.py                  # 完整重定价压力测试
│   └── validation.py            # 模型共用的数值校验
├── templates/index.html         # 中文 Jinja2 Dashboard
├── static/css/style.css
├── static/js/main.js
├── tests/                       # 模型、统计与网页集成测试
├── examples/scenarios.json      # 四组网页输入示例
├── scripts/generate_results.py  # CSV、JSON、报告表格及数值宏
├── scripts/check_deployment.py  # 启动临时 Gunicorn 验证真实 HTTP 请求
├── docs/
│   ├── report.tex               # 中文作业报告
│   ├── user_manual.tex          # 中文使用说明
│   ├── preamble.tex             # 共享排版设置
│   └── generated_results/      # 程序实际计算结果
└── output/pdf/                  # 已编译报告和使用说明
```

Plotly 的 JavaScript 从已安装 Python 包通过同源 `/assets/plotly.min.js` 提供，不使用 CDN。NumPy 预先计算直方图分箱，网页不必下载全部 20 万个模拟终值。界面使用系统字体。

## 测试与实验

```bash
pytest
python scripts/generate_results.py
```

当前验收：**107 passed**。原版 96 项测试覆盖价格基准、含股息平价关系、Greeks 有限差分、MC 统计量独立复核、随机状态隔离、压力矩阵重定价、空头与零持仓、请求边界与中文错误页。部署版新增 11 项测试，检查健康路由、HTTPS 表单与同源资源、环境变量及复制到新目录后的运行。

macOS / Linux 还可执行 `python scripts/check_deployment.py`：它在临时工作目录启动 Gunicorn，通过真实 HTTP 验证静态资源、并发 Call / Put 各 200,000 次模拟、中文错误页和自定义端口，结束后自动停止服务。它不会向 Render 发布代码。详细记录见 `docs/verification.md`。

默认运行结果（seed=42，N=10000）：

| 指标 | 单份结果 |
|---|---:|
| BS Call | 10.4505835722 |
| BS Put | 5.5735260223 |
| MC Call | 10.3451820372 |
| MC 标准误 | 0.1476626574 |
| MC 95% 区间 | [10.0557632287, 10.6346008456] |
| Delta | 0.6368306512 |
| Gamma | 0.0187620173 |
| Vega / 1 pp | 0.3752403469 |
| Theta / 日 | −0.0175726782 |
| Rho / 1 pp | 0.5323248155 |

`docs/generated_results/summary.json` 记录此次 Python 与依赖版本。范围式 requirements 让不同 Python 版本选择兼容包；如需精确复现实验，可依照 JSON 的版本在相同 Python 环境安装。跨版本浮点数末位可能不同。
脚本还输出 N=1000/5000/10000/50000 的单种子实验，以及种子 100～139 的 40 次重复实验。不同 N 使用同一种子的前 N 个样本，因此各 N 结果相互关联；40 次覆盖比例也不必恰为 95%。

## 编译中文 LaTeX

需要完整 TeX Live 或 MiKTeX，包括 XeLaTeX、ctex、Fandol 字体、TikZ/PGFPlots、booktabs 等常用组件。文档使用 TeX 发行版自带 Fandol 字体，不要求另装个人字体。

源文件和实验表格已经齐备。若更新模型，先在项目根目录重新运行实验脚本，然后进入 docs：

```bash
cd docs
xelatex report.tex
xelatex report.tex
xelatex user_manual.tex
xelatex user_manual.tex
```

双次编译更新目录和交叉引用。以上命令在 docs 下生成 PDF。要把新 PDF 写到约定交付目录：

```bash
xelatex -interaction=nonstopmode -halt-on-error -output-directory=../output/pdf report.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=../output/pdf report.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=../output/pdf user_manual.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=../output/pdf user_manual.tex
```

提交时请保留 `docs/generated_results` 和 `preamble.tex`；报告通过相对路径引用这些文件。无需提交 `.venv`、`__pycache__`、`.pytest_cache` 或 `tmp`。

## 模型假设和范围

连续交易、无交易摩擦、常数利率及波动率、连续股息、GBM 标的价格、欧式到期行权。未实现波动率微笑、跳跃、提前行权、真实市场校准、交易成本、动态对冲、VaR 或隐含波动率反解。压力测试是指定情景的敏感性分析，不为情景附加现实概率。

公式参考：Martin Haugh，[The Black-Scholes Model](https://www.columbia.edu/~mh2078/FoundationsFE/BlackScholes.pdf)，Columbia University。实现为本项目直接编写，并由有限差分与无套利关系独立核验。

## 常见问题

- `ModuleNotFoundError`：先激活虚拟环境，在同一环境运行 `python -m pip install -r requirements.txt`。
- 图表空白：启用 JavaScript，确认当前站点 `/assets/plotly.min.js` 返回成功，刷新页面；不需要图表 CDN。
- 在线地址打不开：使用部署者提供的实际 HTTPS 地址，检查 Render 是否 Live；免费实例唤醒期间稍候刷新。不要将 `127.0.0.1` 分享给他人。
- 参数输入后旧结果未变化：点击计算；网页会显示“参数已修改”的提示。
- 数值输入错误：页面保留输入，显示中文原因；不显示过期定价结果。
- LaTeX 缺少类或字体：补装 TeX 发行版的中文与图表组件，使用 XeLaTeX，勿使用 PDFLaTeX。
- 仅在网页使用，不想编译文档：Python 应用与 LaTeX 相互独立。

## 免责声明

本系统仅用于金融科技课程教学和模型演示，不构成任何投资建议。
