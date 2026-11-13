"""Т4.Б1.2. Веб-приложение на FastAPI: маршруты, модели Pydantic, автоматическая документация.

Сервис «Покрытие» из занятия Т4.Б1.1, перенесенный с сокетов на FastAPI.
Запуск (в папке server):
    fastapi dev main.py
затем в браузере http://127.0.0.1:8000/ (страницы) и http://127.0.0.1:8000/docs (документация).

Задания:
    З1  basics.py: подсказки типов и декораторы
    З2  страницы /, /surfaces, перенаправление 301, файлы /static, список покрытий /api/surfaces
    З3  GET /api/braking?v=60&mu=0.7 – тормозной путь с проверкой параметров (Query)
    З4  модели Surface и TripIn, POST /api/trips – новая поездка с кодом 201
    З5  модель ответа TripOut (response_model) и GET /api/trips/{trip_id}
    З6  описания маршрутов, тегов и пример тела запроса в документации

Повышенная сложность (pytest -m extra):
    медленные обработчики def и async def, промежуточный обработчик log_requests

Места, которые нужно дописать, отмечены комментарием # <--
Условия заданий – в файле ЗАДАНИЯ.md.
"""

import asyncio
import datetime
import pathlib
import time
from enum import StrEnum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from basics import SURFACE_NAMES, braking_distance
from offline_docs import DOCS_SETTINGS, add_offline_docs

BASE_DIR = pathlib.Path(__file__).resolve().parent
PAGES_DIR = BASE_DIR / "pages"
STATIC_DIR = BASE_DIR / "static"

# Учебные коэффициенты сцепления шины с дорогой (те же, что в Т4.Б1.1).
SURFACE_MU = {"dry": 0.7, "wet": 0.4, "dirt": 0.5, "snow": 0.15}

# З6. Описания групп маршрутов (тегов) для страницы /docs.
TAGS = [
    # <-- словари {"name": "Покрытия", "description": "..."} для каждого тега: Покрытия, Расчеты, Поездки
]

app = FastAPI(
    title="Покрытие",
    # <-- З6: version="0.2.0", description="...", openapi_tags=TAGS
    **DOCS_SETTINGS,   # готово: документация без интернета, если файлы скачаны в static/docs
)
add_offline_docs(app)

# <-- З2. Подключите папку static, чтобы файлы отдавались по адресам /static/<имя файла>:
#     app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def read_page(name: str) -> str:
    """Готовый помощник: читает страницу из папки pages."""
    return (PAGES_DIR / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------- З2. Страницы и первый JSON

# <-- декоратор: GET /, ответ HTML (response_class=HTMLResponse), страница не попадает
#     в документацию интерфейса (include_in_schema=False)
def index_page():
    """Главная страница."""
    ...   # <-- верните текст страницы index.html (функция read_page)


# <-- декоратор: GET /surfaces, так же, как у главной страницы
def surfaces_page():
    """Страница с таблицей покрытий."""
    ...   # <-- верните текст страницы surfaces.html


# <-- два декоратора друг над другом: GET /index.html и GET /home, оба с include_in_schema=False
def old_address():
    """Старые адреса главной страницы: перенаправление 301 на /."""
    ...   # <-- верните RedirectResponse("/", status_code=301)


@app.get("/api/surfaces")   # <-- З6: tags и summary
def list_surfaces():
    """Возвращает четыре типа покрытия: код, название и учебный коэффициент сцепления.

    Функция возвращает обычный список словарей, а FastAPI сам превращает его в JSON.
    """
    ...   # <-- список словарей {"code": ..., "name": ..., "mu": ...} по SURFACE_NAMES и SURFACE_MU


# ---------------------------------------------------------------- З3. Параметры запроса с проверкой

@app.get("/api/braking")   # <-- З6: tags и summary
def braking(v, mu, t=1.0):   # <-- подсказки типов: Annotated[float, Query(gt=..., le=..., description="...")]
    """Считает тормозной путь в метрах: путь за время реакции плюс путь торможения.

    Если параметр не число или вне диапазона, FastAPI сам отвечает кодом 422
    и указывает, какой параметр неверный. Функция при этом даже не вызывается.
    """
    ...   # <-- верните словарь {"v": v, "mu": mu, "t": t, "braking_distance": braking_distance(v, mu, t)}


# ---------------------------------------------------------------- З4. Модели Pydantic и POST

class Surface(StrEnum):
    """Допустимые коды покрытия. Любое другое значение FastAPI отклонит с кодом 422."""
    dry = "dry"
    # <-- допишите wet, dirt, snow


class TripIn(BaseModel):
    """Поездка, которую присылает клиент."""

    # <-- З6: пример тела запроса
    #     model_config = ConfigDict(json_schema_extra={"examples": [{...}]})

    # <-- поля date, distance, surface, note с типами и ограничениями Field(...) (см. ЗАДАНИЯ.md)
    pass


TRIPS: list[dict] = []   # принятые поездки; хранятся в памяти и пропадают при перезапуске сервера


# ---------------------------------------------------------------- З5. Модель ответа

class TripOut(BaseModel):
    """Поездка в ответе сервера: только то, что сервер обещает клиенту."""
    # <-- поля id, date, distance, surface, note, created_at (служебного поля client_host здесь нет)
    pass


@app.post("/api/trips")   # <-- З4: status_code=201; З5: response_model=TripOut; З6: tags и summary
def create_trip(trip: TripIn, request: Request):
    """Принимает поездку в формате JSON, проверяет ее по модели TripIn и сохраняет.

    Отвечает кодом 201 Created и созданной записью. В записи есть служебное поле
    client_host (адрес компьютера, с которого пришел запрос); в ответ оно не попадает,
    потому что модель ответа TripOut его не содержит.
    """
    ...   # <-- record = trip.model_dump(); добавить id, created_at, client_host; сохранить в TRIPS; вернуть record


@app.get("/api/trips/{trip_id}")   # <-- З5: response_model=TripOut; З6: tags, summary, responses для 404
def get_trip(trip_id: int):   # <-- номер не меньше 1: Annotated[int, Path(ge=1, description="...")]
    """Возвращает одну поездку. Номер берется из пути: /api/trips/7 – поездка номер 7."""
    ...   # <-- найти запись в TRIPS по номеру; если нет – raise HTTPException(status_code=404, detail="...")


# ---------------------------------------------------------------- Повышенная сложность

# <-- 1. Три медленных обработчика с параметром seconds (по умолчанию 0.5, больше 0 и не больше 2):
#        GET /api/slow/sync         – def и time.sleep(seconds)
#        GET /api/slow/async        – async def и time.sleep(seconds)
#        GET /api/slow/async-await  – async def и await asyncio.sleep(seconds)
#     Каждый возвращает {"handler": "...", "seconds": seconds}.

REQUEST_LOG: list[dict] = []   # журнал запросов промежуточного обработчика

# <-- 2. Промежуточный обработчик @app.middleware("http") async def log_requests(request, call_next):
#        засечь время, response = await call_next(request), записать в REQUEST_LOG словарь
#        {"method", "path", "status", "ms"}, добавить заголовок X-Process-Time-Ms, вернуть response.
