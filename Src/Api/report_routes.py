from flask import Response, request, jsonify

from Src.Api.http_report import http_report
from Src.Core.entity_type_enum import entity_type_enum
from Src.Core.exception import arguments_exception
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.report_service import report_not_found_exception
from Src.Logics.recipe_report_source import recipe_report_source
from Src.Models.recipe_item_model import recipe_item_model


def register_report_routes(api, storage, factory, service) -> None:
    """Регистрирует маршруты отчётности и обработчики ошибок API."""
    @api.route("/api/get_report", methods=["GET"])
    def get_report():
        """Формирует текстовый отчёт по стартовому рецепту."""
        product = next(
            (
                item
                for item in storage.items
                if isinstance(item, recipe_item_model)
                and item.name == "Пшеничные лепёшки"
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


    def parse_entity_type(value: str) -> entity_type_enum:
        """Преобразует параметр URL в поддерживаемый тип сущности."""
        try:
            return entity_type_enum(value.strip().lower())
        except ValueError as error:
            raise arguments_exception("entity_type", "Ожидается item, unit или recipe") from error


    @api.app.errorhandler(arguments_exception)
    def invalid_arguments(error):
        """Преобразует ошибку входных данных в HTTP 400."""
        return Response(str(error), status=400, content_type="text/plain; charset=utf-8")


    @api.app.errorhandler(report_not_found_exception)
    def entity_not_found(error):
        """Преобразует отсутствие сущности в HTTP 404."""
        return Response(str(error), status=404, content_type="text/plain; charset=utf-8")


    @api.route("/api/reports/<entity_type>/<code>", methods=["GET"])
    def get_report_by_format(entity_type: str, code: str):
        """Формирует отчёт с обязательным параметром format."""
        try:
            format_ = report_type_enum[request.args.get("format", "").strip().upper()]
        except KeyError as error:
            raise arguments_exception("format", "Укажите CSV, Markdown, XML, TXT или HTML") from error
        return http_report.make_report_response(service.build(parse_entity_type(entity_type), code, format_))


    @api.route("/api/reports/<entity_type>/<code>/default", methods=["GET"])
    def get_default_report(entity_type: str, code: str):
        """Формирует отчёт с использованием create_default через сервис."""
        return http_report.make_report_response(service.build_default(parse_entity_type(entity_type), code))


    @api.route("/api/entities/<entity_type>", methods=["GET"])
    def get_entities(entity_type: str):
        """Возвращает актуальные коды для запросов отчётности."""
        selected = parse_entity_type(entity_type)
        collections = {
            entity_type_enum.ITEM: storage.items,
            entity_type_enum.UNIT: storage.units,
            entity_type_enum.RECIPE: tuple(item.recipe for item in storage.items
                                          if isinstance(item, recipe_item_model)),
        }
        response = jsonify([
            {"code": item.unique_code, "name": item.name}
            for item in collections[selected]
        ])
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response
