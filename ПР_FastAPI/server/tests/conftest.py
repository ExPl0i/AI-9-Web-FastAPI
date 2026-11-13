"""Общие помощники тестов: тестовый клиент FastAPI и запуск настоящего сервера Uvicorn.

Этот файл писать не нужно, он готовый. pytest подключает его сам.
"""

import socket
import threading
import time

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client():
    """Тестовый клиент: отправляет запросы прямо приложению, без сети и без запуска сервера."""
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def openapi(client):
    """Описание программного интерфейса в формате OpenAPI: то же, что по адресу /openapi.json."""
    response = client.get("/openapi.json")
    assert response.status_code == 200, "приложение не смогло построить /openapi.json"
    return response.json()


@pytest.fixture(autouse=True)
def clean_state():
    """Перед каждым тестом список поездок и журнал запросов пустые."""
    main.TRIPS.clear()
    log = getattr(main, "REQUEST_LOG", None)
    if log is not None:
        log.clear()
    yield
    main.TRIPS.clear()


def error_places(response):
    """Из ответа 422 достает места ошибок: [('query', 'v'), ('body', 'distance'), ...]."""
    assert response.status_code == 422, f"ожидался код 422, получен {response.status_code}: {response.text[:200]}"
    return [tuple(error["loc"]) for error in response.json()["detail"]]


def error_types(response):
    """Из ответа 422 достает виды ошибок: ['greater_than', 'missing', ...]."""
    return [error["type"] for error in response.json()["detail"]]


def free_port():
    """Просит у системы свободный порт: bind на порт 0 выбирает любой незанятый."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server():
    """Настоящий сервер Uvicorn с приложением main.app в фоновом потоке. Возвращает базовый адрес."""
    import uvicorn

    port = free_port()
    config = uvicorn.Config(main.app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 5
    while not server.started:
        if time.time() > deadline or not thread.is_alive():
            pytest.fail("сервер Uvicorn не запустился за 5 секунд")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)
