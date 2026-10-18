from Src.Core.abstract_report_source import abstract_report_source
from Src.Core.validator import validator
from Src.Dtos.report_data_dto import report_data_dto
from Src.Models.item_model import item_model


class item_report_source(abstract_report_source[item_model]):
    """Подготавливает поля сущности item без рекурсивного обхода ссылок."""

    def build(self, source: item_model) -> report_data_dto:
        """Возвращает идентификаторы и предметные свойства модели."""
        validator.validate(source, item_model)
        return report_data_dto(
            title=source.name,
            fields=(
                ("Код", source.unique_code),
                ("Наименование", source.name),
                ("Полное наименование", source.full_name),
                ("Код группы", source.group.unique_code),
                ("Группа", source.group.name),
                ("Код единицы", source.unit.unique_code),
                ("Единица измерения", source.unit.name),
            ),
        )
