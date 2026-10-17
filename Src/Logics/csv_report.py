from Src.Dtos.report_data_dto import format_report_value
import csv
from io import StringIO

from Src.Core.abstract_report import abstract_report
from Src.Core.validator import validator
from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_result_dto import report_result_dto


class csv_report(abstract_report):
    """Представляет отчёт парами путь-значение без потери структуры."""

    def build(self, data: report_data_dto) -> report_result_dto:
        """Записывает заголовок, поля, столбцы и ячейки в CSV."""
        validator.validate(data, report_data_dto)
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(("field", "value"))
        writer.writerow(("title", data.title))
        for index, (name, value) in enumerate(data.fields):
            writer.writerow((f"fields[{index}].name", name))
            writer.writerow((f"fields[{index}].value", format_report_value(value)))
        for index, name in enumerate(data.columns):
            writer.writerow((f"columns[{index}]", name))
        for row_index, row in enumerate(data.rows):
            for column_index, value in enumerate(row):
                writer.writerow((f"rows[{row_index}][{column_index}]", format_report_value(value)))
        return report_result_dto(
            (output.getvalue()).encode("utf-8"), "text/csv", "csv", download=True,
        )
