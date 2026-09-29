"""验证 HTTPS 相对资源、部署环境配置及可迁移目录布局。"""
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import pytest
import app as app_module

ROOT = Path(__file__).resolve().parents[1]


def test_health_check_does_not_run_pricing(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("health check must not calculate prices")
    monkeypatch.setattr(app_module, "calculate_dashboard", unexpected)
    response = app_module.app.test_client().get("/healthz")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


@pytest.mark.parametrize("kind", ["call", "put"])
def test_https_form_and_same_origin_resources(kind):
    client = app_module.app.test_client()
    response = client.post("/", base_url="https://option-lab.example",
                           data={**app_module.DEFAULTS, "option_type": kind})
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'action="/"' in html
    assert "127.0.0.1" not in html and "localhost" not in html
    assert "http://" not in html
    assert html.count("Plotly.newPlot(") == 5
    assert 'href="/static/css/style.css"' in html
    assert 'src="/static/js/main.js"' in html
    assert 'src="/assets/plotly.min.js"' in html
    for path, mimetypes in [("/static/css/style.css", ("text/css",)),
                            ("/static/js/main.js", ("text/javascript", "application/javascript")),
                            ("/assets/plotly.min.js", ("application/javascript",))]:
        asset = client.get(path, base_url="https://option-lab.example")
        assert asset.status_code == 200 and asset.mimetype in mimetypes


def test_gunicorn_environment(monkeypatch):
    for name, value in {"PORT": "18765", "WEB_CONCURRENCY": "2",
                        "GUNICORN_THREADS": "3", "GUNICORN_TIMEOUT": "90"}.items():
        monkeypatch.setenv(name, value)
    config = runpy.run_path(str(ROOT / "gunicorn.conf.py"))
    assert config["bind"] == "0.0.0.0:18765"
    assert config["chdir"] == str(ROOT)
    assert (config["workers"], config["threads"], config["timeout"]) == (2, 3, 90)


@pytest.mark.parametrize("name,value", [("PORT", "0"), ("PORT", "65536"),
    ("PORT", "not-a-port"), ("WEB_CONCURRENCY", "0"), ("GUNICORN_THREADS", "-1"),
    ("GUNICORN_TIMEOUT", "0")])
def test_invalid_deployment_environment(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        runpy.run_path(str(ROOT / "gunicorn.conf.py"))


def test_relocated_application_without_docs_or_original_cwd(tmp_path):
    relocated = tmp_path / "cloud-copy"
    relocated.mkdir()
    for name in ["app.py", "charts.py", "gunicorn.conf.py"]:
        shutil.copy2(ROOT / name, relocated / name)
    for name in ["models", "templates", "static"]:
        shutil.copytree(ROOT / name, relocated / name,
                        ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    check = """
from app import app, DEFAULTS, BASE_DIR
from pathlib import Path
assert BASE_DIR != Path.cwd()
assert app.config['ONLINE_MODE'] is True
assert app.debug is False
client = app.test_client()
assert client.get('/').status_code == 200
assert client.post('/', data={**DEFAULTS, 'option_type': 'put'}).status_code == 200
assert client.get('/healthz').json == {'status': 'ok'}
for path in ['/static/css/style.css', '/static/js/main.js', '/assets/plotly.min.js']:
    assert client.get(path).status_code == 200
assert '在线计算' in client.get('/').get_data(as_text=True)
"""
    env = {**os.environ, "PYTHONPATH": str(relocated), "APP_ENV": "production"}
    result = subprocess.run([sys.executable, "-c", check], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
