from Src.Logics.entity_service import entity_service
from Src.Logics.entity_mappings import entity_mappings, entity_resources
from Src.Logics.dto_mapping import dto_mapper
from Src.Logics.dto_serializer import dto_serializer

from functools import partial
from operator import eq, ge, le, lt
from pathlib import Path
import sys
from typing import TextIO

import connexion
from flask import render_template_string, send_file, send_from_directory, url_for
from swagger_ui_bundle import swagger_ui_path

from Src.Api.report_routes import register_report_routes
from Src.Api.web_request_events import web_request_events
from Src.Core.filter_operator_enum import filter_operator_enum
from Src.Core.observer import observer
from Src.Logics.logging_observer import logging_observer
from Src.Logics.operation_logger import operation_logger
from Src.Logics.prototype import prototype
from Src.Logics.report_factory import report_factory
from Src.Logics.report_service import report_service
from Src.Logics.report_source_factory import report_source_factory
from Src.Logics.settings_manager import setting_manager
from Src.Logics.storage_manager import storage_manager
from Src.Logics.turnover_service import turnover_service


def create_app(*, log_stream: TextIO | None = None, log_path: Path | None = None):
    """Создаёт приложение и подключает зависимости и маршруты отчётности."""

    project_dir = Path(__file__).resolve().parents[2]
    log_destination = log_stream if log_stream is not None else log_path or sys.stdout
    dispatcher = observer()
    dispatcher.add(logging_observer(operation_logger(log_destination)))
    publish_event = dispatcher.notify

    settings = setting_manager(publish_event=publish_event)
    settings.load(str(project_dir / "settings.json"))

    storage = storage_manager(settings.settings, publish_event=publish_event)
    factory = report_factory(settings.settings)

    repository = storage.get_repository()
    service = report_service(repository, report_source_factory(), factory)

    api = connexion.FlaskApp(__name__, specification_dir="./")
    api.app.json.ensure_ascii = False
    web_request_events(publish_event=publish_event).register(api.app)

    mappings = entity_mappings()
    resources = entity_resources(mappings)
    create_prototype = partial(prototype, model_types=mappings.model_types(), operators={
        filter_operator_enum.EQUALS: eq,
        filter_operator_enum.LIKE: lambda actual, expected: expected.casefold() in actual.casefold(),
        filter_operator_enum.BEFORE: lt,
        filter_operator_enum.ON_OR_AFTER: ge,
        filter_operator_enum.ON_OR_BEFORE: le,
    })
    entities = entity_service(
        repository, dto_mapper(mappings, repository, resources), resources, create_prototype,
        publish_event=publish_event,
    )
    turnover = turnover_service(repository, create_prototype)
    register_report_routes(api, repository, factory, service, entities, resources, dto_serializer(), turnover)

    api.app.extensions["report_storage"] = storage
    api.app.extensions["report_settings"] = settings

    @api.app.get("/openapi.yaml")
    def openapi_spec():
        return send_file(project_dir / "openapi.yaml", mimetype="application/yaml")

    @api.app.get("/ui/")
    def swagger_ui():
        template = (swagger_ui_path / "index.j2").read_text(encoding="utf-8")
        return render_template_string(
            template, openapi_spec_url=url_for("openapi_spec")
        )

    @api.app.get("/ui/<path:filename>")
    def swagger_asset(filename):
        return send_from_directory(swagger_ui_path, filename)

    return api
