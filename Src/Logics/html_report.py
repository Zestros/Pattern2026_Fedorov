from Src.Dtos.report_data_dto import format_report_value
from html import escape

from Src.Core.abstract_report import abstract_report
from Src.Core.validator import validator
from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_result_dto import report_result_dto


class html_report(abstract_report):
    """Представляет данные HTML-страницей."""

    def build(self, data: report_data_dto) -> report_result_dto:
        """Создаёт страницу, экранируя все пользовательские значения."""
        validator.validate(data, report_data_dto)
        parts = ['<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">',
                 f"<title>{escape(data.title)}</title></head><body>",
                 f"<h1>{escape(data.title)}</h1><dl>"]
        for name, value in data.fields:
            parts.append(f"<dt>{escape(name)}</dt><dd>{escape(format_report_value(value))}</dd>")
        parts.append("</dl>")
        if data.columns:
            parts.append("<table><thead><tr>")
            parts.extend(f"<th>{escape(name)}</th>" for name in data.columns)
            parts.append("</tr></thead><tbody>")
            for row in data.rows:
                parts.append("<tr>" + "".join(f"<td>{escape(format_report_value(value))}</td>" for value in row) + "</tr>")
            parts.append("</tbody></table>")
        parts.append("</body></html>")
        return report_result_dto(
            "".join(parts), self.media_type, self.file_extension, download=self.download,
        )

    @property
    def media_type(self) -> str:
        """Возвращает MIME-тип формата."""
        return 'text/html'

    @property
    def file_extension(self) -> str:
        """Возвращает расширение формата."""
        return 'html'

    @property
    def download(self) -> bool:
        """Возвращает способ выдачи формата."""
        return False
