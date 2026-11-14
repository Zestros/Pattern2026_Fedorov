from pathlib import Path

import connexion
from flask import render_template_string, send_file, send_from_directory, url_for
from swagger_ui_bundle import swagger_ui_path

from Src.Api.report_routes import register_report_routes
from Src.Logics.report_factory import report_factory
from Src.Logics.report_service import report_service
from Src.Logics.report_source_factory import report_source_factory
from Src.Logics.settings_manager import setting_manager
from Src.Logics.storage_manager import storage_manager


def create_app():
    """Создаёт приложение и подключает зависимости и маршруты отчётности."""

    project_dir = Path(__file__).resolve().parents[2]

    settings = setting_manager()
    settings.load(str(project_dir / "settings.json"))

    storage = storage_manager(settings.settings)
    factory = report_factory(settings.settings)

    service = report_service(storage, report_source_factory(), factory)

    api = connexion.FlaskApp(__name__, specification_dir="./")
    api.app.json.ensure_ascii = False

    register_report_routes(api, storage, factory, service)

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
