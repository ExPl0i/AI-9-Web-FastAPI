"""З1. Повторение: подсказки типов и декораторы (файл basics.py)."""

import typing

import basics
from basics import ROUTES, average_distance, braking_distance, count_calls, dispatch, register, surface_name


def same_type(a, b):
    """Сравнивает типы без мелочей записи: str | None и Optional[str], list[float] и List[float] – одно и то же."""
    def norm(tp):
        origin = typing.get_origin(tp)
        if origin in (typing.Union, getattr(__import__("types"), "UnionType")):
            return ("union", frozenset(norm(arg) for arg in typing.get_args(tp)))
        if origin is not None:
            return (origin, tuple(norm(arg) for arg in typing.get_args(tp)))
        return tp
    return norm(a) == norm(b)


def check_hints(func, expected):
    hints = typing.get_type_hints(func)
    for name, tp in expected.items():
        assert name in hints, f"у функции {func.__name__} нет подсказки типа для {name!r}"
        assert same_type(hints[name], tp), \
            f"{func.__name__}: подсказка для {name!r} – {hints[name]}, ожидалась {tp}"


def test_results():
    assert braking_distance(60, 0.7) == 36.9, "формула готовая: 60 / 3,6 + 60² / (254 · 0,7) = 36,9 м"
    assert surface_name("snow") == "снег и лед"
    assert surface_name("lava") is None, "неизвестный код – None"
    assert average_distance([10, 20, 30.5]) == 20.2, "(10 + 20 + 30,5) / 3 = 20,17, округление до 0,1"
    assert average_distance([]) is None, "у пустого списка среднего нет: None, а не ошибка деления на 0"


def test_type_hints_braking():
    check_hints(braking_distance, {"v": float, "mu": float, "t": float, "return": float})


def test_type_hints_surface_name():
    check_hints(surface_name, {"code": str, "return": str | None})


def test_type_hints_average():
    check_hints(average_distance, {"distances": list[float], "return": float | None})


def test_count_calls_counts():
    @count_calls
    def double(x: int) -> int:
        """Удваивает число."""
        return 2 * x

    assert hasattr(double, "calls"), "у обертки должен быть атрибут calls"
    assert double.calls == 0, "до вызовов счетчик равен 0"
    assert double(2) == 4 and double(x=5) == 10, "обертка передает аргументы и возвращает результат функции"
    assert double.calls == 2


def test_count_calls_keeps_name_and_hints():
    @count_calls
    def double(x: int) -> int:
        """Удваивает число."""
        return 2 * x

    assert hasattr(double, "calls"), "сначала напишите обертку с атрибутом calls"
    assert double.__name__ == "double", "имя потерялось: оберните wrapper декоратором functools.wraps(func)"
    assert double.__doc__ == "Удваивает число."
    assert typing.get_type_hints(double) == {"x": int, "return": int}, \
        "подсказки типов должны остаться: их переносит functools.wraps"


def test_three_functions_decorated():
    for func in (braking_distance, surface_name, average_distance):
        assert hasattr(func, "calls"), f"функция {func.__name__} не обернута декоратором @count_calls"
    before = surface_name.calls
    surface_name("dry")
    surface_name("wet")
    assert surface_name.calls == before + 2


def test_register_builds_routes():
    assert ROUTES.get("/") is basics.home, "декоратор @register('/') записывает home в ROUTES['/']"
    assert ROUTES.get("/surfaces") is basics.surfaces
    assert dispatch("/surfaces") == "сухой асфальт, мокрый асфальт, грунт, снег и лед"
    assert dispatch("/nowhere") == "404"


def test_register_returns_same_function():
    @register("/test-z1")
    def page() -> str:
        return "ok"

    try:
        assert page is not None, "декоратор должен вернуть функцию, иначе имя page станет None"
        assert ROUTES.get("/test-z1") is page, "декоратор должен записать функцию в ROUTES под ключом пути"
        assert page() == "ok"
    finally:
        ROUTES.pop("/test-z1", None)
