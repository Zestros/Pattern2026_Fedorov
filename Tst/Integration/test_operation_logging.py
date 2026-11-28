"""Интеграционные проверки журнала операций приложения."""

from datetime import datetime
from io import StringIO
import json
from pathlib import Path

import pytest
from starlette.exceptions import HTTPException

from Src.Api.application import create_app
from Src.Core.entity_conflict_exception import entity_conflict_exception
from Src.Core.report_type_enum import report_type_enum
from Src.Core.validator import operation_exception
from Src.Logics.settings_manager import setting_manager
from Src.Logics.storage_manager import storage_manager
from Src.Models.transaction_model import transaction_model


# Период формирования ОСВ в проверках журнала.
TURNOVER_URL = "/api/reports/turnover?date_from=2026-02-01&date_to=2026-02-28"


@pytest.fixture
def observed_app(monkeypatch):
    """Создаёт приложение со своим потоком журнала и чистыми менеджерами."""
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    monkeypatch.delattr(setting_manager, "instance", raising=False)
    stream = StringIO()
    return create_app(log_stream=stream).app, stream


def test_appended_log_create_app_with_existing_log_file(monkeypatch, tmp_path):
    """<summary>Запуск и HTTP-запрос дополняют существующий файл журнала строками JSON в UTF-8.</summary>"""
    # Подготовка
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    monkeypatch.delattr(setting_manager, "instance", raising=False)
    log_path = tmp_path / "operations.log"
    previous = {"message": "Предыдущая запись"}
    log_path.write_text(json.dumps(previous, ensure_ascii=False) + "\n", encoding="utf-8")

    # Действие
    app = create_app(log_path=log_path).app
    response = app.test_client().get("/api/reports/formats")

    # Проверка
    assert response.status_code == 200
    existing, loaded, *_, started, completed = [
        json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()
    ]
    assert existing == previous
    assert (loaded["subsystem"], loaded["operation"]) == ("SETTINGS", "load")
    assert (started["subsystem"], started["phase"]) == ("HTTP", "started")
    assert (completed["subsystem"], completed["phase"]) == ("HTTP", "completed")
    assert completed["details"]["status_code"] == 200


def test_logged_startup_create_app_connects_sources_before_loading(monkeypatch):
    """<summary>Оба источника успевают опубликовать первые события при сборке приложения.</summary>"""
    # Подготовка
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    monkeypatch.delattr(setting_manager, "instance", raising=False)
    load = setting_manager.load
    stream = StringIO()

    def load_demo_settings(manager, file_name):
        """Включает регистрацию демонстрационных движений после чтения файла."""
        load(manager, file_name)
        manager.settings.first_start = True
        manager.settings.seed_demo_transactions = True

    monkeypatch.setattr(setting_manager, "load", load_demo_settings)

    # Действие
    app = create_app(log_stream=stream).app

    # Проверка
    initial, *movements = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert (initial["subsystem"], initial["operation"]) == ("SETTINGS", "load")
    storage = app.extensions["report_storage"]
    assert movements
    assert [(record["operation"], record["entity_code"]) for record in movements] == [
        ("movement_recorded", movement.unique_code) for movement in storage.transactions
    ]


def test_logged_movements_register_models_after_successful_registration(observed_app):
    """<summary>Одиночная и пакетная регистрации дают по записи на движение; повторная регистрация записей не добавляет.</summary>"""
    # Подготовка
    app, stream = observed_app
    storage = app.extensions["report_storage"]
    warehouse = storage.warehouses[0]
    item = storage.items[0]
    unit = item.unit.base_unit
    incoming = transaction_model(datetime(2026, 2, 3), warehouse, item, unit, 5)
    outgoing = transaction_model(datetime(2026, 2, 4), warehouse, item, unit, -2)

    # Действие
    storage.add(transaction_model, incoming)
    storage.register_models(iter((outgoing,)))
    with pytest.raises(entity_conflict_exception):
        storage.add(transaction_model, incoming)

    # Проверка
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    movements = [record for record in records if record.get("entity_code") in {incoming.unique_code, outgoing.unique_code}]
    assert [(record["operation"], record["entity_code"], record["details"]["quantity"]) for record in movements] == [
        ("movement_recorded", incoming.unique_code, 5),
        ("movement_recorded", outgoing.unique_code, -2),
    ]
    assert movements[0]["subsystem"] == "STORAGE"
    assert movements[0]["details"] == {
        "warehouse_code": warehouse.unique_code, "item_code": item.unique_code,
        "unit_code": unit.unique_code, "quantity": 5,
    }


def test_logged_web_get_turnover_without_storage_event(observed_app):
    """<summary>Расчёт ОСВ фиксируется как Web-вызов, без события складского движения.</summary>"""
    # Подготовка
    app, stream = observed_app
    client = app.test_client()
    before = stream.tell()

    # Действие
    response = client.post(TURNOVER_URL, json={})

    # Проверка
    assert response.status_code == 200
    started, completed = [json.loads(line) for line in stream.getvalue()[before:].splitlines()]
    assert (started["subsystem"], started["operation"], started["phase"]) == ("HTTP", "POST", "started")
    assert (completed["subsystem"], completed["operation"], completed["phase"]) == ("HTTP", "POST", "completed")
    assert completed["details"]["path"] == "/api/reports/turnover"
    assert completed["details"]["status_code"] == 200
    assert completed["details"]["duration_ms"] >= 0


def test_logged_events_entity_service_after_crud_requests(observed_app):
    """<summary>Каждая CRUD-операция публикует начало и итог; внутреннее чтение PATCH отдельной записи не создаёт.</summary>"""
    # Подготовка
    app, stream = observed_app
    client = app.test_client()
    url = "/api/entities/group"
    code = "operation-log-example"
    entity_url = f"{url}/{code}"

    # Действие
    created = client.post(url, json={"name": "Группа для журнала", "unique_code": code})
    listed = client.get(url)
    found = client.post(f"{url}/search", json={})
    read = client.get(entity_url)
    changed = client.patch(entity_url, json={"name": "Изменённая группа"})
    deleted = client.delete(entity_url)
    missing = client.get(entity_url)

    # Проверка
    responses = created, listed, found, read, changed, deleted, missing
    assert [response.status_code for response in responses] == [201, 200, 200, 200, 200, 204, 404]
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    crud = [record for record in records if record["subsystem"] == "CRUD"]
    expected = ("create", "list", "search", "get", "change", "delete")
    assert [(record["operation"], record["phase"]) for record in crud] == [
        (operation, phase) for operation in expected for phase in ("started", "completed")
    ] + [("get", "started"), ("get", "rejected")]
    assert crud[1]["entity_code"] == code
    assert crud[-1]["entity_code"] == code
    assert crud[-1]["reason_code"] == "entity_not_found"
    http = [record for record in records if record["subsystem"] == "HTTP" and record["phase"] != "started"]
    assert [record["details"]["status_code"] for record in http] == [201, 200, 200, 200, 200, 204, 404]
    assert http[-1]["phase"] == "rejected"


def test_logged_rejections_entity_service_during_request_validation(observed_app):
    """<summary>Ошибки входных данных создания и изменения отражаются в CRUD и HTTP.</summary>"""
    # Подготовка
    app, stream = observed_app
    client = app.test_client()

    # Действие
    invalid = client.post("/api/entities/group", json={})
    missing = client.patch("/api/entities/group/missing-for-log", json={"name": "Другой код"})

    # Проверка
    assert [invalid.status_code, missing.status_code] == [400, 404]
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    crud = [record for record in records if record["subsystem"] == "CRUD" and record["phase"] == "rejected"]
    assert [(record["operation"], record["reason_code"]) for record in crud] == [
        ("create", "invalid_arguments"), ("change", "entity_not_found"),
    ]


def test_logged_failure_after_request_preserves_server_response(observed_app):
    """<summary>Ответ Web с кодом 5xx сохраняется и даёт запись ERROR.</summary>"""
    # Подготовка
    app, stream = observed_app

    @app.get("/failed-for-log")
    def failed_response():
        """Возвращает ошибку сервера для проверки журнала."""
        return "", 503

    # Действие
    response = app.test_client().get("/failed-for-log")

    # Проверка
    assert response.status_code == 503
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    record = records[-1]
    assert (record["subsystem"], record["phase"], record["level"]) == ("HTTP", "failed", "ERROR")
    assert record["details"]["status_code"] == 503


def test_logged_rejection_teardown_request_for_unknown_route(observed_app):
    """<summary>Неизвестный маршрут фиксируется при передаче ошибки из Flask в Connexion.</summary>"""
    # Подготовка
    app, stream = observed_app
    before = stream.tell()

    # Действие
    with pytest.raises(HTTPException) as error:
        app.test_client().get("/missing-web-route")

    # Проверка
    assert error.value.status_code == 404
    records = [json.loads(line) for line in stream.getvalue()[before:].splitlines()]
    assert [(record["subsystem"], record["phase"]) for record in records] == [
        ("HTTP", "started"), ("HTTP", "rejected"),
    ]
    assert records[-1]["details"]["status_code"] == 404


def test_logged_settings_load_detects_only_applied_changes(observed_app, tmp_path):
    """<summary>Загрузка нового формата даёт одно событие изменения и сразу обновляет формат отчёта.</summary>"""
    # Подготовка
    app, stream = observed_app
    settings = setting_manager()
    initial_path = Path(__file__).resolve().parents[2] / "settings.json"
    values = json.loads(initial_path.read_text(encoding="utf-8"))
    target = report_type_enum.TXT if settings.settings.response_format is report_type_enum.CSV else report_type_enum.CSV
    changed_path = tmp_path / "settings.json"
    changed_path.write_text(json.dumps(values | {"response_format": target.name}), encoding="utf-8")
    unit = app.extensions["report_storage"].units[0]
    report_url = f"/api/reports/unit/{unit.unique_code}/default"

    # Действие
    settings.load(str(initial_path))
    settings.load(str(changed_path))
    settings.load(str(changed_path))
    changed_path.write_text(json.dumps(values | {"response_format": "unknown"}), encoding="utf-8")
    with pytest.raises(operation_exception):
        settings.load(str(changed_path))
    response = app.test_client().get(report_url)

    # Проверка
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    initial, changed = [record for record in records if record["subsystem"] == "SETTINGS"]
    assert settings is app.extensions["report_settings"]
    assert initial["operation"] == "load"
    assert changed["operation"] == "change"
    assert changed["details"] == {"changed_fields": ["response_format"]}
    assert settings.settings.response_format is target
    assert response.status_code == 200
    assert response.mimetype == ("text/csv" if target is report_type_enum.CSV else "text/plain")


def test_registered_movement_add_despite_unavailable_log_stream(observed_app, capsys):
    """<summary>При недоступном журнале движение сохраняется, а ошибка записи выводится отдельно.</summary>"""
    # Подготовка
    app, stream = observed_app
    storage = app.extensions["report_storage"]
    warehouse = storage.warehouses[0]
    item = storage.items[0]
    movement = transaction_model(datetime(2026, 2, 3), warehouse, item, item.unit.base_unit, 5)
    stream.close()

    # Действие
    storage.add(transaction_model, movement)

    # Проверка
    assert storage.find(transaction_model, movement.unique_code) is movement
    assert "STORAGE/movement_recorded" in capsys.readouterr().err


def test_saved_log_create_app_after_example_operations(observed_app, tmp_path):
    """<summary>Действия всех четырёх подсистем формируют пример журнала в корне проекта.</summary>"""
    # Подготовка
    app, stream = observed_app
    storage = app.extensions["report_storage"]
    settings = app.extensions["report_settings"]
    warehouse = storage.warehouses[0]
    item = next(item for item in storage.items if item.name == "Мука")
    unit = item.unit.base_unit
    receipt = transaction_model(datetime(2026, 2, 3), warehouse, item, unit, 12)
    issue = transaction_model(datetime(2026, 2, 4), warehouse, item, unit, -3)

    project_dir = Path(__file__).resolve().parents[2]
    values = json.loads((project_dir / "settings.json").read_text(encoding="utf-8"))
    target = report_type_enum.TXT if settings.settings.response_format is report_type_enum.CSV else report_type_enum.CSV
    updated_settings = tmp_path / "settings.json"
    updated_settings.write_text(json.dumps(values | {
        "first_start": not settings.settings.first_start,
        "response_format": target.name,
    }), encoding="utf-8")

    # Действие
    storage.add(transaction_model, receipt)
    storage.add(transaction_model, issue)
    settings.load(str(updated_settings))
    created = app.test_client().post("/api/entities/group", json={"name": "Группа из примера журнала"})

    # Проверка
    assert created.status_code == 201
    journal = stream.getvalue()
    records = [json.loads(line) for line in journal.splitlines()]
    initial, *_, received, issued, changed = [
        record for record in records if record["subsystem"] in {"SETTINGS", "STORAGE"}
    ]
    actions = [
        (record["subsystem"], record["operation"], record["phase"])
        for record in (initial, received, issued, changed)
    ]
    assert actions == [
        ("SETTINGS", "load", "completed"),
        ("STORAGE", "movement_recorded", "completed"),
        ("STORAGE", "movement_recorded", "completed"),
        ("SETTINGS", "change", "completed"),
    ]
    assert (received["entity_code"], received["details"]["quantity"]) == (receipt.unique_code, 12)
    assert (issued["entity_code"], issued["details"]["quantity"]) == (issue.unique_code, -3)
    assert changed["details"] == {"changed_fields": ["first_start", "response_format"]}
    assert {record["subsystem"] for record in records} == {"SETTINGS", "STORAGE", "CRUD", "HTTP"}

    (project_dir / "example_operations.log").write_text(journal, encoding="utf-8")
