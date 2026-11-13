"""З5. Модель ответа TripOut и GET /api/trips/{trip_id}: сервер отдает только обещанные поля."""

import datetime

from conftest import error_places

TRIP = {"date": "2026-11-05", "distance": 12.5, "surface": "wet", "note": "дождь после обеда"}
PUBLIC = {"id", "date", "distance", "surface", "note", "created_at"}


def test_service_field_not_in_response(client):
    r = client.post("/api/trips", json=TRIP)
    assert r.status_code == 201
    body = r.json()
    assert "client_host" not in body, "служебное поле client_host не должно уходить клиенту: response_model=TripOut"
    assert set(body) == PUBLIC, f"в ответе ровно поля модели TripOut, получено {sorted(body)}"
    datetime.datetime.fromisoformat(body["created_at"])


def test_get_trip_by_id(client):
    client.post("/api/trips", json=TRIP)
    client.post("/api/trips", json={**TRIP, "surface": "snow", "distance": 3})
    r = client.get("/api/trips/2")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 2 and body["surface"] == "snow" and body["distance"] == 3
    assert set(body) == PUBLIC


def test_get_missing_trip_404(client):
    r = client.get("/api/trips/99")
    assert r.status_code == 404, "нет поездки – HTTPException(status_code=404)"
    assert "99" in r.json()["detail"], "в тексте ошибки указан номер, которого нет"


def test_wrong_trip_id_422(client):
    assert ("path", "trip_id") in error_places(client.get("/api/trips/abc")), "номер в пути должен быть целым числом"
    assert ("path", "trip_id") in error_places(client.get("/api/trips/0")), "номера начинаются с 1: Path(ge=1)"


def test_response_model_in_docs(openapi):
    schemas = openapi["components"]["schemas"]
    assert "TripOut" in schemas
    assert "client_host" not in schemas["TripOut"]["properties"]
    post = openapi["paths"]["/api/trips"]["post"]["responses"]
    assert "201" in post, "в документации описан ответ 201"
    assert post["201"]["content"]["application/json"]["schema"]["$ref"].endswith("/TripOut")
    get = openapi["paths"]["/api/trips/{trip_id}"]["get"]["responses"]
    assert get["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/TripOut")
