from datetime import date

from flask import Response, request, jsonify, url_for

from Src.Dtos.filter_dto import filter_dto
from Src.Logics.entity_service import entity_service, entity_not_found_exception
from Src.Logics.resource_catalog import resource_catalog
from Src.Logics.dto_serializer import dto_serializer
from Src.Api.http_report import http_report
from Src.Core.abstract_entity_repository import abstract_entity_repository
from Src.Core.entity_conflict_exception import entity_conflict_exception
from Src.Core.exception import arguments_exception
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.report_service import report_not_found_exception
from Src.Logics.recipe_report_source import recipe_report_source
from Src.Logics.turnover_service import turnover_service
from Src.Models.recipe_item_model import recipe_item_model


def register_report_routes(api, storage: abstract_entity_repository, factory, service,
                           entities: entity_service, resources: resource_catalog,
                           serializer: dto_serializer, turnover: turnover_service) -> None:
    """Регистрирует маршруты отчётности и работы с доменными сущностями."""

    def read_fields() -> dict:
        """Читает JSON-объект из тела запроса."""
        fields = request.get_json(silent=True)
        if not isinstance(fields, dict):
            raise arguments_exception("body", "Ожидается JSON-объект")
        return fields

    def read_date(field: str) -> date:
        """Читает календарную дату запроса в формате ГГГГ-ММ-ДД."""
        raw = request.args.get(field, "")
        try:
            value = date.fromisoformat(raw)
        except ValueError as error:
            raise arguments_exception(field, "Ожидается дата в формате ГГГГ-ММ-ДД") from error
        if value.isoformat() != raw:
            raise arguments_exception(field, "Ожидается дата в формате ГГГГ-ММ-ДД")
        return value

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

    @api.app.errorhandler(entity_not_found_exception)
    @api.app.errorhandler(report_not_found_exception)
    def entity_not_found(error):
        """Преобразует отсутствие сущности в HTTP 404."""
        return Response(str(error), status=404, content_type="text/plain; charset=utf-8")

    @api.route("/api/reports/formats", methods=["GET"])
    def get_report_formats():
        """Возвращает имена форматов, доступных в фабрике отчётов."""
        return jsonify(serializer.serialize(tuple(format_.name for format_ in factory.formats())))

    @api.route("/api/reports/<entity_type>/<code>", methods=["GET"])
    def get_report_by_format(entity_type: str, code: str):
        """Формирует отчёт с обязательным параметром format."""
        try:
            format_ = report_type_enum[request.args.get("format", "").strip().upper()]
        except KeyError as error:
            allowed = ", ".join(format_.name for format_ in factory.formats())
            raise arguments_exception("format", f"Укажите формат из списка: {allowed}") from error
        return http_report.make_report_response(service.build(entities.model_type(entity_type), code, format_))


    @api.route("/api/reports/<entity_type>/<code>/default", methods=["GET"])
    def get_default_report(entity_type: str, code: str):
        """Формирует отчёт с использованием create_default через сервис."""
        return http_report.make_report_response(service.build_default(entities.model_type(entity_type), code))


    @api.route("/api/reports/turnover", methods=["POST"])
    def get_turnover():
        """Формирует количественную ОСВ с заданными фильтрами и периодом."""
        criteria = serializer.deserialize(read_fields(), filter_dto)
        rows = turnover.build(criteria, read_date("date_from"), read_date("date_to"))
        return jsonify(serializer.serialize(rows))

    @api.route("/api/entities/<entity_type>/search", methods=["POST"])
    def search_entities(entity_type: str):
        """Возвращает отобранные и отсортированные сущности указанного типа."""
        criteria = serializer.deserialize(read_fields(), filter_dto)
        return jsonify(serializer.serialize(entities.search(entity_type, criteria)))

    @api.route("/api/entities/<entity_type>", methods=["GET"])
    def get_entities(entity_type: str):
        """Список использует те же DTO и сериализатор, что и остальные ответы."""
        return jsonify(serializer.serialize(entities.list(entity_type)))

    @api.route("/api/entities/<entity_type>", methods=["POST"])
    def create_entity(entity_type: str):
        """Разбирает внешний контракт и вызывает общий прикладной сценарий."""
        fields = read_fields()
        dto = serializer.deserialize(fields, resources.request_type(entity_type, fields))
        result = entities.create(dto)
        response = jsonify(serializer.serialize(result))
        response.status_code = 201
        response.headers["Location"] = url_for("get_entity", entity_type=entity_type, code=result.unique_code)
        return response

    @api.route("/api/entities/<entity_type>/<code>", methods=["GET"])
    def get_entity(entity_type: str, code: str):
        """Возвращает сериализованный DTO сущности по коду."""
        return jsonify(serializer.serialize(entities.get(entity_type, code)))

    @api.route("/api/entities/<entity_type>/<code>", methods=["PATCH"])
    def update_entity(entity_type: str, code: str):
        """Разбирает частичный DTO фактического типа, не меняя вид сущности."""
        current = entities.get(entity_type, code)
        dto = serializer.deserialize(read_fields(), type(current), partial=True)
        return jsonify(serializer.serialize(entities.change(entity_type, code, dto)))

    @api.route("/api/entities/<entity_type>/<code>", methods=["DELETE"])
    def delete_entity(entity_type: str, code: str):
        """Удаляет сущность через прикладной сервис и возвращает HTTP 204."""
        entities.delete(entity_type, code)
        return Response(status=204)
