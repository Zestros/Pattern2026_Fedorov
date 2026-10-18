from pathlib import Path

import connexion

from Src.Api.report_routes import register_report_routes
from Src.Logics.report_factory import report_factory
from Src.Logics.report_service import report_service
from Src.Logics.report_source_factory import report_source_factory
from Src.Logics.settings_manager import setting_manager
from Src.Logics.storage_manager import storage_manager


def create_app():
    """Создаёт приложение и подключает зависимости и маршруты отчётности."""
    settings = setting_manager()
    settings.load(str(Path(__file__).resolve().parents[2] / "settings.json"))

    storage = storage_manager(settings.settings)
    factory = report_factory(settings.settings)

    service = report_service(storage, report_source_factory(), factory)

    api = connexion.FlaskApp(__name__, specification_dir="./")
    api.app.json.ensure_ascii = False

    register_report_routes(api, storage, factory, service)

    api.app.extensions["report_storage"] = storage
    api.app.extensions["report_settings"] = settings
    return api
