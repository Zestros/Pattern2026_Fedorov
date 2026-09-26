from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Models.group_model import group_model
from Src.Models.unit_model import unit_model


class item_model(entity_model):
    """Номенклатура: сырьё, полуфабрикат, блюдо или упаковка."""

    # Полное наименование номенклатуры.
    __full_name: str

    # Группа номенклатуры.
    __group: group_model

    # Единица измерения номенклатуры.
    __unit: unit_model

    def __init__(
        self,
        name: str,
        full_name: str,
        group: group_model,
        unit: unit_model,
    ) -> None:
        """Создаёт номенклатуру с наименованиями, группой и единицей."""
        super().__init__()
        self.name = name
        self.full_name = full_name
        self.group = group
        self.unit = unit

    @property
    def full_name(self) -> str:
        """Возвращает полное наименование номенклатуры."""
        return self.__full_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        """Устанавливает непустое полное наименование до 255 символов."""
        if not isinstance(value, str):
            raise arguments_exception(
                "full_name",
                "Полное наименование должно быть строкой",
            )

        full_name = value.strip()

        if full_name == "":
            raise arguments_exception(
                "full_name",
                "Полное наименование не может быть пустым",
            )

        if len(full_name) > 255:
            raise arguments_exception(
                "full_name",
                "Полное наименование не может превышать 255 символов",
            )

        self.__full_name = full_name

    @property
    def group(self) -> group_model:
        """Возвращает группу номенклатуры."""
        return self.__group

    @group.setter
    def group(self, value: group_model) -> None:
        """Устанавливает группу номенклатуры."""
        if not isinstance(value, group_model):
            raise arguments_exception(
                "group",
                "Группа должна быть моделью группы номенклатуры",
            )

        self.__group = value

    @property
    def unit(self) -> unit_model:
        """Возвращает единицу измерения номенклатуры."""
        return self.__unit

    @unit.setter
    def unit(self, value: unit_model) -> None:
        """Устанавливает единицу измерения номенклатуры."""
        if not isinstance(value, unit_model):
            raise arguments_exception(
                "unit",
                "Единица измерения должна быть моделью единицы измерения",
            )

        self.__unit = value