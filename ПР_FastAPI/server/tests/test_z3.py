"""З3. Калькулятор тормозного пути GET /api/braking: параметры запроса с типами и ограничениями."""

import pytest

from basics import braking_distance
from conftest import error_places, error_types


def test_braking_ok(client):
    r = client.get("/api/braking", params={"v": 60, "mu": 0.7})
    assert r.status_code == 200
    assert r.json() == {"v": 60.0, "mu": 0.7, "t": 1.0, "braking_distance": 36.9}, \
        "числа пришли строками, а в ответе они уже float: FastAPI преобразовал их по подсказкам типов"


def test_braking_reaction_time(client):
    assert client.get("/api/braking", params={"v": 60, "mu": 0.7, "t": 0.3}).json()["braking_distance"] == 25.2
    assert client.get("/api/braking", params={"v": 100, "mu": 0.7, "t": 2}).json()["braking_distance"] == 111.8


@pytest.mark.parametrize("params, field, kind", [
    ({"v": -10, "mu": 0.7}, "v", "greater_than"),          # отрицательная скорость
    ({"v": 60, "mu": 0}, "mu", "greater_than"),            # коэффициент 0: машина не остановится никогда
    ({"v": 250, "mu": 0.7}, "v", "less_than_equal"),       # скорость больше 200
    ({"v": "abc", "mu": 0.7}, "v", "float_parsing"),       # не число
    ({"mu": 0.7}, "v", "missing"),                         # нет скорости
    ({"v": 60, "mu": "0,7"}, "mu", "float_parsing"),       # десятичная запятая: FastAPI строже нашего сервера
    ({"v": 60, "mu": 0.7, "t": 10}, "t", "less_than_equal"),
    ({"v": "nan", "mu": 0.7}, "v", None),                  # «не число» тоже не проходит
])
def test_wrong_params_422(client, params, field, kind):
    r = client.get("/api/braking", params=params)
    places = error_places(r)
    assert ("query", field) in places, f"при {params} ошибка должна указывать на параметр {field}, получено {places}"
    if kind:
        assert kind in error_types(r)


def test_all_errors_listed(client):
    places = error_places(client.get("/api/braking", params={"v": "abc", "mu": -1}))
    assert ("query", "v") in places and ("query", "mu") in places, "FastAPI сообщает обо всех ошибках сразу"


def test_function_not_called_on_error(client):
    calls = getattr(braking_distance, "calls", None)
    if calls is None:
        pytest.skip("сначала выполните З1: декоратор count_calls")
    client.get("/api/braking", params={"v": -10, "mu": 0.7})
    assert braking_distance.calls == calls, "при ошибке в параметрах функция расчета не должна вызываться"
    client.get("/api/braking", params={"v": 60, "mu": 0.7})
    assert braking_distance.calls == calls + 1


def test_constraints_are_declared(openapi):
    params = {p["name"]: p for p in openapi["paths"]["/api/braking"]["get"]["parameters"]}
    assert set(params) == {"v", "mu", "t"}
    assert params["v"]["required"] and params["mu"]["required"]
    assert not params["t"].get("required", False), "у t есть значение по умолчанию 1.0"
    assert params["v"]["schema"].get("exclusiveMinimum") == 0 and params["v"]["schema"].get("maximum") == 200, \
        "ограничения скорости задаются в Query(gt=0, le=200), а не проверкой внутри функции"
    assert params["mu"]["schema"].get("exclusiveMinimum") == 0 and params["mu"]["schema"].get("maximum") == 1.2
    assert params["t"]["schema"].get("default") == 1.0
