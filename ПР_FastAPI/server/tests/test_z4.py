"""З4. Модели Surface и TripIn, POST /api/trips: новая поездка с кодом 201."""

import pytest

import main
from conftest import error_places

TRIP = {"date": "2026-11-05", "distance": 12.5, "surface": "wet", "note": "дождь после обеда"}


def test_create_trip_201(client):
    r = client.post("/api/trips", json=TRIP)
    assert r.status_code == 201, "новая запись создана: код 201 Created (status_code=201 в декораторе)"
    body = r.json()
    assert body["id"] == 1
    for key, value in TRIP.items():
        assert body[key] == value, f"поле {key}: ожидалось {value!r}, получено {body.get(key)!r}"


def test_ids_grow(client):
    client.post("/api/trips", json=TRIP)
    r = client.post("/api/trips", json={**TRIP, "surface": "snow"})
    assert r.status_code == 201 and r.json()["id"] == 2
    assert len(main.TRIPS) == 2, "поездки хранятся в списке TRIPS"


def test_note_is_optional(client):
    trip = {k: v for k, v in TRIP.items() if k != "note"}
    r = client.post("/api/trips", json=trip)
    assert r.status_code == 201 and r.json()["note"] == "", "у note значение по умолчанию – пустая строка"


def test_record_keeps_service_fields(client):
    client.post("/api/trips", json=TRIP)
    record = main.TRIPS[0]
    assert "created_at" in record, "сервер записывает время приема поездки"
    assert record.get("client_host") == "testclient", \
        "служебное поле client_host – адрес клиента (request.client.host); у тестового клиента он 'testclient'"


@pytest.mark.parametrize("change, field", [
    ({"distance": -5}, "distance"),            # расстояние должно быть больше 0
    ({"distance": 0}, "distance"),
    ({"distance": 2500}, "distance"),          # больше 2000 км
    ({"distance": "12,5"}, "distance"),        # не число
    ({"surface": "lava"}, "surface"),          # нет в перечислении
    ({"date": "2026-02-30"}, "date"),          # такой даты нет в календаре
    ({"date": "05.11.2026"}, "date"),          # дата не в виде ГГГГ-ММ-ДД
    ({"note": "а" * 201}, "note"),             # комментарий длиннее 200 символов
])
def test_wrong_trip_422(client, change, field):
    r = client.post("/api/trips", json={**TRIP, **change})
    places = error_places(r)
    assert ("body", field) in places, f"при {change} ошибка должна указывать на поле {field}, получено {places}"
    assert main.TRIPS == [], "поездка с ошибкой не сохраняется"


def test_all_missing_fields_listed(client):
    places = error_places(client.post("/api/trips", json={}))
    for field in ("date", "distance", "surface"):
        assert ("body", field) in places, f"нет обязательного поля {field}: оно должно быть в списке ошибок"
    assert ("body", "note") not in places, "note необязательное поле"


def test_surface_is_enum(openapi):
    schemas = openapi["components"]["schemas"]
    assert "Surface" in schemas, "допустимые покрытия задайте перечислением class Surface(StrEnum)"
    assert schemas["Surface"]["enum"] == ["dry", "wet", "dirt", "snow"]
    trip_in = schemas["TripIn"]["properties"]
    assert trip_in["distance"].get("exclusiveMinimum") == 0 and trip_in["distance"].get("maximum") == 2000
    assert trip_in["note"].get("maxLength") == 200
