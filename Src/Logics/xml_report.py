from Src.Dtos.report_data_dto import format_report_value
from xml.etree.ElementTree import Element, SubElement, tostring

from Src.Core.abstract_report import abstract_report
from Src.Core.validator import validator
from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_result_dto import report_result_dto


class xml_report(abstract_report):
    """Представляет поля и таблицу структурированным XML."""

    def build(self, data: report_data_dto) -> report_result_dto:
        """Создаёт XML с экранированием значений стандартной библиотекой."""
        validator.validate(data, report_data_dto)
        root = Element("report")
        SubElement(root, "title").text = data.title
        fields = SubElement(root, "fields")
        for name, value in data.fields:
            SubElement(fields, "field", name=name).text = format_report_value(value)
        columns = SubElement(root, "columns")
        for name in data.columns:
            SubElement(columns, "column").text = name
        rows = SubElement(root, "rows")
        for values in data.rows:
            row = SubElement(rows, "row")
            for value in values:
                SubElement(row, "cell").text = format_report_value(value)
        return report_result_dto(
            tostring(root, encoding="unicode"), self.media_type, self.file_extension, download=self.download,
        )

    @property
    def media_type(self) -> str:
        """Возвращает MIME-тип формата."""
        return 'application/xml'

    @property
    def file_extension(self) -> str:
        """Возвращает расширение формата."""
        return 'xml'

    @property
    def download(self) -> bool:
        """Возвращает способ выдачи формата."""
        return False
