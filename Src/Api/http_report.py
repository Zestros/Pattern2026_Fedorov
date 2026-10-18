from flask import Response
from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_result_dto import report_result_dto


class http_report(abstract_report):
    """Декоратор форматировщика, добавляющий выдачу результата через Flask."""

    def __init__(self, report: abstract_report) -> None:
        """Сохраняет обёрнутый построитель отчёта."""
        self.__report = report

    def build(self, data: report_data_dto) -> report_result_dto:
        """Делегирует форматирование исходному построителю."""
        return self.__report.build(data)

    @staticmethod
    def make_report_response(result: report_result_dto) -> Response:
        """Создаёт HTTP-ответ с MIME-типом и параметрами скачивания."""
        response = Response(result.content, content_type=f"{result.media_type}; charset=utf-8")
        if result.download:
            response.headers.set("Content-Disposition", "attachment", filename=f"report.{result.file_extension}")
        return response
