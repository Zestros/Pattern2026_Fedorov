from Src.Dtos.report_data_dto import format_report_value
from html import escape

from Src.Core.abstract_report import abstract_report
from Src.Core.validator import validator
from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_result_dto import report_result_dto


def escape_markdown(value: object) -> str:
    """Экранирует разметку и сохраняет переносы внутри таблицы."""
    text = escape(format_report_value(value), quote=False)
    for char in "\\`*_{}[]()#+-.!|":
        text = text.replace(char, "\\" + char)
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


class markdown_report(abstract_report):
    """Представляет данные заголовком, полями и Markdown-таблицей."""

    def build(self, data: report_data_dto) -> report_result_dto:
        """Формирует Markdown с экранированием значений."""
        validator.validate(data, report_data_dto)
        lines = ["# " + escape_markdown(data.title), ""] if data.title else []
        lines.extend(
            f"- **{escape_markdown(name)}:** {escape_markdown(value)}"
            for name, value in data.fields
        )
        if data.columns:
            lines.append("")
            lines.append("| " + " | ".join(map(escape_markdown, data.columns)) + " |")
            lines.append("| " + " | ".join("---" for _ in data.columns) + " |")
            lines.extend(
                "| " + " | ".join(map(escape_markdown, row)) + " |"
                for row in data.rows
            )
        return report_result_dto(
            ("\n".join(lines)).encode("utf-8"), "text/markdown", "md", download=True,
        )
