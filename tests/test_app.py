import pytest
from app import app, DEFAULTS, parse_form


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_default_page_and_five_charts(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="bs-price">10.4506' in html
    assert html.count("Plotly.newPlot(") == 5
    assert 'src="/assets/plotly.min.js"' in html
    assert "cdn.plot.ly" not in html
    assert "期权定价与风险管理系统" in html and "95% 置信区间" in html


def test_percent_conversion():
    p, quantity, n = parse_form(DEFAULTS)
    assert p["r"] == .05 and p["sigma"] == .2 and p["q"] == 0
    assert quantity == 100 and n == 10000


def test_put_post_and_short_position(client):
    r = client.post("/", data={**DEFAULTS, "option_type": "put", "quantity": "-100"})
    assert r.status_code == 200 and 'id="bs-price">5.5735' in r.get_data(as_text=True)


@pytest.mark.parametrize("key,value", [("S", "0"), ("K", "-1"), ("T", "0"), ("sigma", "0"),
    ("r", "nan"), ("q", "inf"), ("S", "1e309"), ("S", "abc"), ("option_type", "american"),
    ("n_simulations", "0"), ("n_simulations", "1.5"), ("n_simulations", "200001"),
    ("n_simulations", "1e4"), ("quantity", "1.5"), ("S", "<script>alert(1)</script>")])
def test_bad_input_is_chinese_422_not_500(client, key, value):
    r = client.post("/", data={**DEFAULTS, key: value})
    assert r.status_code == 422
    html = r.get_data(as_text=True)
    assert "请检查输入参数" in html
    assert "<script>alert(1)</script>" not in html


@pytest.mark.parametrize("changes", [{"sigma": "5"}, {"n_simulations": "1"}, {"quantity": "0"},
    {"n_simulations": "200000"}, {"S": ".0001", "K": "1000000", "sigma": ".01"},
    {"r": "-20", "q": "100", "T": "30", "sigma": "300"}])
def test_supported_boundaries(client, changes):
    assert client.post("/", data={**DEFAULTS, **changes}).status_code == 200


def test_missing_input(client):
    assert client.post("/", data={}).status_code == 422


def test_oversized_request(client):
    assert client.post("/", data={"S": "a" * 20000}).status_code == 413


def test_offline_plotly_asset(client):
    r = client.get("/assets/plotly.min.js")
    assert r.status_code == 200 and r.mimetype == "application/javascript"
    assert len(r.data) > 1_000_000
