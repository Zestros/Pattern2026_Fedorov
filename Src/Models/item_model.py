from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Models.group_model import group_model
from Src.Models.unit_model import unit_model
from Src.Models.ratio_value_model import ratio_value_model
from Src.Core.validator import validator


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
        mass_ratio: ratio_value_model | None = None,
    ) -> None:
        """Создаёт номенклатуру с необязательной характеристикой массы."""
        super().__init__()
        self.name = name
        self.full_name = full_name
        self.group = group
        self.unit = unit

        # Плотность или масса штуки с указанием составной единицы.
        self.mass_ratio = mass_ratio

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

    @property
    def mass_ratio(self) -> ratio_value_model | None:
        """Возвращает плотность или массу штуки с единицами измерения."""
        return self.__mass_ratio

    @mass_ratio.setter
    def mass_ratio(self, value: ratio_value_model | None) -> None:
        """Устанавливает характеристику массы или удаляет её через None."""
        if value is not None:
            validator.validate(value, ratio_value_model, field="mass_ratio")

        self.__mass_ratio = value

    def calculate_mass(
        self,
        quantity: int | float,
        target_unit: unit_model,
        source_unit: unit_model | None = None,
    ) -> float:
        """Рассчитывает массу в целевой единице; по умолчанию использует единицу учёта.

        Целевая единица должна задавать массу. При наличии характеристики
        исходная единица должна быть совместима с её знаменателем.
        """
        source = self.unit if source_unit is None else source_unit
        validator.validate(source, unit_model, field="source_unit")

        if self.mass_ratio is not None:
            return self.mass_ratio.calculate_mass(quantity, source, target_unit)

        return source.convert_to(quantity, target_unit)
