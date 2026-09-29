"""在 macOS / Linux 启动临时 Gunicorn 并检查真实 HTTP 请求；不会部署到公网。"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
FORM = {"S": "100", "K": "100", "T": "1", "r": "5", "sigma": "20", "q": "0",
        "quantity": "100", "n_simulations": "200000"}


def main() -> None:
    if sys.platform == "win32":
        raise SystemExit("Gunicorn 检查请在 Linux / macOS / WSL 执行；Windows 本地仍用 python app.py。")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    base = f"http://127.0.0.1:{port}"

    def fetch(path: str, form: dict | None = None) -> tuple[int, str, str]:
        data = urlencode(form).encode() if form is not None else None
        request = Request(base + path, data=data, headers={"X-Forwarded-Proto": "https"})
        opener = build_opener(ProxyHandler({}))
        try:
            response = opener.open(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.headers.get_content_type(), response.read().decode()

    env = {**os.environ, "PORT": str(port), "APP_ENV": "production", "WEB_CONCURRENCY": "1",
           "GUNICORN_THREADS": "2", "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
           "GUNICORN_CMD_ARGS": "--preload --access-logfile - --bind=0.0.0.0:10000"}
    # 模拟 Render 的注入参数，显式 --bind 必须优先使用本次动态端口。
    command = [sys.executable, "-m", "gunicorn", "--config", str(ROOT / "gunicorn.conf.py"),
               "--bind", f"0.0.0.0:{port}", "app:app"]
    with TemporaryDirectory(prefix="option-render-check-") as directory:
        log_path = Path(directory) / "gunicorn.log"
        with log_path.open("w+") as log:
            process = subprocess.Popen(command, cwd=directory, env=env, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 30
                while True:
                    if process.poll() is not None:
                        raise RuntimeError("Gunicorn 启动失败")
                    try:
                        status, _, body = fetch("/healthz")
                        assert status == 200 and json.loads(body) == {"status": "ok"}
                        break
                    except (URLError, ConnectionError, TimeoutError):
                        if time.monotonic() >= deadline:
                            raise RuntimeError("Gunicorn 启动超时")
                        time.sleep(.1)
                status, _, html = fetch("/")
                assert status == 200 and 'id="bs-price">10.4506' in html
                assert "在线计算" in html and html.count("Plotly.newPlot(") == 5
                for path in ("/static/css/style.css", "/static/js/main.js", "/assets/plotly.min.js"):
                    status, _, body = fetch(path)
                    assert status == 200 and len(body) > 100
                with ThreadPoolExecutor(max_workers=2) as pool:
                    responses = list(pool.map(lambda kind: fetch("/", {**FORM, "option_type": kind}),
                                               ["call", "put"]))
                for response, expected in zip(responses, ["10.4506", "5.5735"]):
                    status, _, html = response
                    assert status == 200 and f'id="bs-price">{expected}' in html
                    assert html.count("Plotly.newPlot(") == 5 and "95% 置信区间" in html
                status, _, html = fetch("/", {**FORM, "option_type": "call", "S": "0"})
                assert status == 422 and "请检查输入参数" in html
                print("Gunicorn HTTP 验收通过：健康检查、默认页、三类资源、并发 Call/Put 各 200,000 次模拟、中文 422。")
                print("已验证：任意工作目录启动、Render 注入参数下使用自定义 PORT。临时服务将在退出时停止。")
            except Exception:
                log.flush()
                print(log_path.read_text(), file=sys.stderr)
                raise
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    main()
