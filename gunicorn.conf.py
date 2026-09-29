"""Render / Linux / macOS 的 WSGI 配置；无需改动 app.py 本地入口。"""
import os
from pathlib import Path


def positive_integer(name: str, default: int) -> int:
    """错误的部署变量应在启动时显式失败。"""
    value = int(os.environ.get(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


chdir = str(Path(__file__).resolve().parent)
port = positive_integer("PORT", 10000)
if port > 65535:
    raise ValueError("PORT must not exceed 65535")
bind = f"0.0.0.0:{port}"
workers = positive_integer("WEB_CONCURRENCY", 1)
worker_class = "gthread"
threads = positive_integer("GUNICORN_THREADS", 2)
timeout = positive_integer("GUNICORN_TIMEOUT", 120)
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
capture_output = True
