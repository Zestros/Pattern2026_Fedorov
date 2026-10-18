from Src.Dtos.report_data_dto import format_report_value
from Src.Core.abstract_report import abstract_report
from Src.Core.validator import validator
from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_result_dto import report_result_dto


class text_report(abstract_report):
    """Представляет подготовленные поля и таблицу обычным текстом."""

    def build(self, data: report_data_dto) -> report_result_dto:
        """Формирует текст, не обращаясь к доменным моделям."""
        validator.validate(data, report_data_dto)
        lines = [data.title] if data.title else []
        lines.extend(f"{name}: {format_report_value(value)}" for name, value in data.fields)
        if data.columns:
            lines.append(" | ".join(data.columns))
        lines.extend(" | ".join(format_report_value(value) for value in row) for row in data.rows)
        return report_result_dto(
            "\n".join(lines), self.media_type, self.file_extension, download=self.download,
        )

    @property
    def media_type(self) -> str:
        """Возвращает MIME-тип формата."""
        return 'text/plain'

    @property
    def file_extension(self) -> str:
        """Возвращает расширение формата."""
        return 'txt'

    @property
    def download(self) -> bool:
        """Возвращает способ выдачи формата."""
        return False
