from Src.Core.abstract_report_source import abstract_report_source
from Src.Core.validator import validator
from Src.Dtos.report_data_dto import report_data_dto
from Src.Models.unit_model import unit_model


class unit_report_source(abstract_report_source[unit_model]):
    """Подготавливает поля сущности unit без рекурсивного обхода ссылок."""

    def build(self, source: unit_model) -> report_data_dto:
        """Возвращает идентификаторы и предметные свойства модели."""
        validator.validate(source, unit_model)
        return report_data_dto(
            title=source.name,
            fields=(
                ("Код", source.unique_code),
                ("Наименование", source.name),
                ("Коэффициент", source.coefficient),
                ("Код базовой единицы", source.base_unit.unique_code),
                ("Базовая единица", source.base_unit.name),
            ),
        )
