from flask import Response, request, jsonify, url_for

from Src.Api.entity_type_adapter import entity_type_adapter
from Src.Api.http_report import http_report
from Src.Core.abstract_entity_repository import abstract_entity_repository
from Src.Core.entity_conflict_exception import entity_conflict_exception
from Src.Core.exception import arguments_exception
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.report_service import report_not_found_exception
from Src.Logics.recipe_report_source import recipe_report_source
from Src.Models.recipe_item_model import recipe_item_model


def register_report_routes(api, storage: abstract_entity_repository, factory, service) -> None:
    """Регистрирует маршруты отчётности и работы с доменными сущностями."""
    entities = entity_type_adapter(storage)

    def read_fields() -> dict:
        """Читает JSON-объект из тела запроса."""
        fields = request.get_json(silent=True)
        if not isinstance(fields, dict):
            raise arguments_exception("body", "Ожидается JSON-объект")
        return fields

    @api.route("/api/get_report", methods=["GET"])
    def get_report():
        """Формирует текстовый отчёт по стартовому рецепту."""
        product = next(
            (
                item
                for item in storage.list(recipe_item_model)
                if item.name == "Пшеничные лепёшки"
            ),
            None,
        )

        if product is None:
            return Response(
                "Рецепт не найден",
                status=404,
                content_type="text/plain; charset=utf-8",
            )

        report = factory.create(report_type_enum.TXT)
        result = report.build(recipe_report_source().build(product.recipe))

        return http_report.make_report_response(result)


    @api.app.errorhandler(arguments_exception)
    def invalid_arguments(error):
        """Преобразует ошибку входных данных в HTTP 400."""
        return Response(str(error), status=400, content_type="text/plain; charset=utf-8")

    @api.app.errorhandler(entity_conflict_exception)
    def entity_conflict(error):
        """Возвращает HTTP 409 при дубликате кода или входящих ссылках."""
        return Response(str(error), status=409, content_type="text/plain; charset=utf-8")

    @api.app.errorhandler(report_not_found_exception)
    def entity_not_found(error):
        """Преобразует отсутствие сущности в HTTP 404."""
        return Response(str(error), status=404, content_type="text/plain; charset=utf-8")

    @api.route("/api/reports/formats", methods=["GET"])
    def get_report_formats():
        """Возвращает имена форматов, доступных в фабрике отчётов."""
        return jsonify([format_.name for format_ in factory.formats()])

    @api.route("/api/reports/<entity_type>/<code>", methods=["GET"])
    def get_report_by_format(entity_type: str, code: str):
        """Формирует отчёт с обязательным параметром format."""
        try:
            format_ = report_type_enum[request.args.get("format", "").strip().upper()]
        except KeyError as error:
            allowed = ", ".join(format_.name for format_ in factory.formats())
            raise arguments_exception("format", f"Укажите формат из списка: {allowed}") from error
        return http_report.make_report_response(service.build(entity_type_adapter.resolve(entity_type), code, format_))


    @api.route("/api/reports/<entity_type>/<code>/default", methods=["GET"])
    def get_default_report(entity_type: str, code: str):
        """Формирует отчёт с использованием create_default через сервис."""
        return http_report.make_report_response(service.build_default(entity_type_adapter.resolve(entity_type), code))


    @api.route("/api/entities/<entity_type>", methods=["GET"])
    def get_entities(entity_type: str):
        """Возвращает актуальные коды для запросов отчётности."""
        selected = entity_type_adapter.resolve(entity_type)
        response = jsonify([
            {"code": item.unique_code, "name": item.name}
            for item in storage.list(selected)
        ])
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    @api.route("/api/entities/<entity_type>", methods=["POST"])
    def create_entity(entity_type: str):
        """Создаёт сущность и возвращает её представление и адрес."""
        selected = entity_type_adapter.resolve(entity_type)
        model = entities.create(selected, read_fields())
        storage.add(selected, model)
        response = jsonify(entities.encode(model))
        response.status_code = 201
        response.headers["Location"] = url_for(
            "get_entity", entity_type=entity_type, code=model.unique_code,
        )
        return response

    @api.route("/api/entities/<entity_type>/<code>", methods=["GET"])
    def get_entity(entity_type: str, code: str):
        """Возвращает поля зарегистрированной сущности."""
        model = storage.find(entity_type_adapter.resolve(entity_type), code)
        if model is None:
            raise report_not_found_exception("Сущность не найдена")
        return jsonify(entities.encode(model))

    @api.route("/api/entities/<entity_type>/<code>", methods=["PATCH"])
    def update_entity(entity_type: str, code: str):
        """Применяет переданные поля через репозиторий."""
        selected = entity_type_adapter.resolve(entity_type)
        current = storage.find(selected, code)
        if current is None:
            raise report_not_found_exception("Сущность не найдена")
        fields = entities.decode(type(current), read_fields())
        updated = storage.update(selected, code, fields)
        if updated is None:
            raise report_not_found_exception("Сущность не найдена")
        return jsonify(entities.encode(updated))

    @api.route("/api/entities/<entity_type>/<code>", methods=["DELETE"])
    def delete_entity(entity_type: str, code: str):
        """Удаляет сущность, если репозиторий подтверждает отсутствие ссылок."""
        if not storage.delete(entity_type_adapter.resolve(entity_type), code):
            raise report_not_found_exception("Сущность не найдена")
        return Response(status=204)
