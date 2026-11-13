"""З2. Маршруты из Т4.Б1.1 на FastAPI: страницы, перенаправление, файлы, первый ответ JSON."""

HTML = "text/html; charset=utf-8"


def test_main_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"] == HTML, "страница отдается с типом text/html (response_class=HTMLResponse)"
    assert "Сервис «Покрытие»" in r.text


def test_surfaces_page(client):
    r = client.get("/surfaces")
    assert r.status_code == 200 and r.headers["content-type"] == HTML
    assert "снег и лед" in r.text


def test_old_addresses_redirect(client):
    for path in ("/index.html", "/home"):
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 301, f"{path}: ожидалось перенаправление 301"
        assert r.headers["location"] == "/", "новый адрес передается в заголовке Location"
    r = client.get("/home")
    assert r.status_code == 200 and "Сервис «Покрытие»" in r.text, "клиент перешел по перенаправлению на главную"


def test_static_files(client):
    r = client.get("/static/style.css")
    assert r.status_code == 200, "подключите папку static: app.mount('/static', StaticFiles(...))"
    assert r.headers["content-type"].startswith("text/css")
    r = client.get("/static/logo.svg")
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/svg+xml")
    assert client.get("/static/nothing.css").status_code == 404


def test_unknown_path_404(client):
    r = client.get("/nowhere")
    assert r.status_code == 404, "ответ 404 FastAPI отправляет сам"
    assert r.json() == {"detail": "Not Found"}


def test_wrong_method_405(client):
    r = client.post("/surfaces")
    assert r.status_code == 405, "ответ 405 FastAPI тоже отправляет сам"
    assert "GET" in r.headers["allow"]


def test_api_surfaces(client):
    r = client.get("/api/surfaces")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json", "список Python FastAPI сам превращает в JSON"
    assert r.json() == [
        {"code": "dry", "name": "сухой асфальт", "mu": 0.7},
        {"code": "wet", "name": "мокрый асфальт", "mu": 0.4},
        {"code": "dirt", "name": "грунт", "mu": 0.5},
        {"code": "snow", "name": "снег и лед", "mu": 0.15},
    ]


def test_pages_are_not_in_docs(openapi):
    paths = openapi["paths"]
    assert "/api/surfaces" in paths
    for path in ("/", "/surfaces", "/index.html", "/home"):
        assert path not in paths, f"страница {path} не часть программного интерфейса: include_in_schema=False"
