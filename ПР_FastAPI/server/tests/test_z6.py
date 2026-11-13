"""З6. Автоматическая документация: описания приложения, маршрутов, тегов и пример тела запроса."""

import re

import main

CYRILLIC = re.compile(r"[а-яА-Я]")


def api_operations(openapi):
    for path, item in openapi["paths"].items():
        if path.startswith("/api/"):
            for method, operation in item.items():
                yield path, method.upper(), operation


def test_app_info(openapi):
    info = openapi["info"]
    assert info["title"] == "Покрытие"
    assert info["version"] == "0.2.0", "версия приложения: FastAPI(version='0.2.0')"
    assert len(info.get("description", "")) >= 30, "добавьте описание приложения: FastAPI(description=...)"


def test_every_route_has_summary_and_description(openapi):
    operations = list(api_operations(openapi))
    assert len(operations) >= 4
    for path, method, op in operations:
        assert CYRILLIC.search(op.get("summary", "")), \
            f"{method} {path}: краткое описание summary на русском (сейчас {op.get('summary')!r})"
        assert len(op.get("description", "")) >= 20, f"{method} {path}: нет подробного описания (строка документации функции)"


def test_every_route_has_tag(openapi):
    described = {tag["name"]: tag.get("description", "") for tag in openapi.get("tags", [])}
    for path, method, op in api_operations(openapi):
        assert op.get("tags"), f"{method} {path}: укажите тег, например tags=['Поездки']"
        for tag in op["tags"]:
            assert described.get(tag), f"у тега {tag!r} нет описания в FastAPI(openapi_tags=...)"


def test_parameters_and_fields_described(openapi):
    for param in openapi["paths"]["/api/braking"]["get"]["parameters"]:
        assert param.get("description"), f"параметр {param['name']}: Query(..., description='...')"
    for name, prop in openapi["components"]["schemas"]["TripIn"]["properties"].items():
        assert prop.get("description"), f"поле TripIn.{name}: Field(..., description='...')"


def test_trip_example(client, openapi):
    examples = openapi["components"]["schemas"]["TripIn"].get("examples")
    assert examples, "добавьте пример тела запроса в TripIn: model_config = ConfigDict(json_schema_extra=...)"
    main.TripIn.model_validate(examples[0])
    r = client.post("/api/trips", json=examples[0])
    assert r.status_code == 201, "пример из документации должен проходить проверку и сохраняться"


def test_404_documented(openapi):
    responses = openapi["paths"]["/api/trips/{trip_id}"]["get"]["responses"]
    assert "404" in responses, "опишите ответ 404: responses={404: {'description': '...'}}"
    assert CYRILLIC.search(responses["404"].get("description", ""))
