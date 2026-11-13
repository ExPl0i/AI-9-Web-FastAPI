"""Повышенная сложность. Запуск: pytest -m extra"""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests

import main

pytestmark = pytest.mark.extra

PAUSE = 0.4     # пауза в каждом медленном обработчике, секунд
REQUESTS = 5    # сколько запросов отправляем одновременно


def five_at_once(url):
    """Отправляет 5 запросов одновременно из 5 потоков и возвращает общее время в секундах."""
    def one(_):
        with requests.Session() as session:
            session.trust_env = False       # школьные настройки прокси не мешают тесту
            response = session.get(url, params={"seconds": PAUSE}, timeout=10)
            assert response.status_code == 200, f"{url}: код {response.status_code}"
    started = time.perf_counter()
    with ThreadPoolExecutor(REQUESTS) as pool:
        list(pool.map(one, range(REQUESTS)))
    return time.perf_counter() - started


def test_slow_def_runs_in_parallel(live_server):
    total = five_at_once(live_server + "/api/slow/sync")
    assert total < PAUSE * 2.5, f"5 запросов к обработчику def заняли {total:.2f} с: они должны идти одновременно"


def test_slow_async_with_time_sleep_blocks(live_server):
    total = five_at_once(live_server + "/api/slow/async")
    assert total > PAUSE * (REQUESTS - 0.5), \
        f"5 запросов к async def с time.sleep заняли {total:.2f} с: ожидалось около {PAUSE * REQUESTS:.1f} с, по очереди"


def test_slow_async_with_await_runs_in_parallel(live_server):
    total = five_at_once(live_server + "/api/slow/async-await")
    assert total < PAUSE * 2.5, f"с await asyncio.sleep запросы идут одновременно, а заняли {total:.2f} с"


def test_middleware_writes_log(client):
    assert hasattr(main, "REQUEST_LOG"), "создайте список REQUEST_LOG для журнала запросов"
    client.get("/api/braking", params={"v": 60, "mu": 0.7})
    client.get("/nowhere")
    assert len(main.REQUEST_LOG) == 2, "промежуточный обработчик записывает каждый запрос, даже 404"
    first, second = main.REQUEST_LOG
    assert first["method"] == "GET" and first["path"] == "/api/braking" and first["status"] == 200
    assert second["path"] == "/nowhere" and second["status"] == 404
    assert isinstance(first["ms"], float) and first["ms"] >= 0


def test_middleware_adds_header(client):
    r = client.get("/api/surfaces")
    assert "x-process-time-ms" in r.headers, "добавьте к ответу заголовок X-Process-Time-Ms"
    float(r.headers["x-process-time-ms"])
