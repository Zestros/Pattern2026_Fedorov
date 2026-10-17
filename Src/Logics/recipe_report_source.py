from Src.Core.abstract_report_source import abstract_report_source
from Src.Core.validator import validator
from Src.Dtos.report_data_dto import report_data_dto
from Src.Models.recipe_model import recipe_model


class recipe_report_source(abstract_report_source[recipe_model]):
    """Подготавливает существующую таблицу состава рецепта."""

    def build(self, source: recipe_model) -> report_data_dto:
        """Выбирает коды, названия и массы строк рецепта."""
        validator.validate(source, recipe_model)
        return report_data_dto(
            title=source.name,
            fields=(
                ("Код", source.unique_code),
                ("Наименование", source.name),
                ("Код единицы массы", source.mass_unit.unique_code),
                ("Единица массы", source.mass_unit.name),
                ("Брутто", source.gross_weight),
                ("Нетто", source.net_weight),
            ),
            columns=("Код строки", "Наименование", "Код номенклатуры", "Количество", "Брутто", "Нетто"),
            rows=tuple(
                (
                    str(item.unique_code),
                    item.item.name,
                    item.item.unique_code,
                    item.quantity,
                    item.calculate_gross_weight(source.mass_unit),
                    item.calculate_net_weight(source.mass_unit),
                )
                for item in source.ingredients
            ),
        )
