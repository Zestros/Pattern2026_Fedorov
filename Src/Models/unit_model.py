from __future__ import annotations

import math
from typing import Self
from Src.Core.validator import validator
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception


class unit_model(entity_model):
    """Единица измерения с коэффициентом пересчёта в базовую единицу."""

    # Множитель для перевода количества в базовую единицу.
    __coefficient: int | float

    # Базовая единица измерения.
    __base_unit: unit_model

    def __init__(
        self,
        name: str,
        coefficient: int | float = 1,
        base_unit: unit_model | None = None,
    ) -> None:
        """Создаёт базовую или производную единицу измерения."""
        super().__init__()
        self.name = name

        if isinstance(coefficient, bool) or not isinstance(
            coefficient, (int, float)
        ):
            raise arguments_exception(
                "coefficient",
                "Коэффициент должен быть числом",
            )

        if isinstance(coefficient, float) and not math.isfinite(coefficient):
            raise arguments_exception(
                "coefficient",
                "Коэффициент должен быть конечным числом",
            )

        if coefficient <= 0:
            raise arguments_exception(
                "coefficient",
                "Коэффициент должен быть больше нуля",
            )

        if base_unit is None:
            if coefficient != 1:
                raise arguments_exception(
                    "coefficient",
                    "Коэффициент базовой единицы должен быть равен 1",
                )

            base_unit = self
        else:
            if not isinstance(base_unit, unit_model):
                raise arguments_exception(
                    "base_unit",
                    "Базовая единица должна быть моделью единицы измерения",
                )

        self.__coefficient = coefficient
        self.__base_unit = base_unit
        self.validate_base_unit()

    def validate_base_unit(self) -> None:
        """Проверяет, что единица ссылается на базовую, в том числе на саму себя."""
        if self.base_unit.base_unit is not self.base_unit:
            raise arguments_exception("base_unit", "Нельзя использовать производную единицу как базовую")

    def validate_state(self) -> None:
        """Проверяет изменяемую связь с базовой единицей."""
        self.validate_base_unit()

    def updated_copy(self, fields: dict[str, object]) -> Self:
        """Принимает null как переход к базовой единице при обновлении."""
        self.validate_fields(fields)
        if "base_unit" in fields and fields["base_unit"] is None:
            fields = {**fields, "base_unit": self}
        return super().updated_copy(fields)

    @classmethod
    def from_fields(
        cls, fields: dict[str, object], *, instance: Self | None = None,
    ) -> Self:
        """Инициализирует базовую единицу с сохранением ссылки на себя."""
        base = fields["base_unit"]
        if base is None:
            raise arguments_exception("base_unit", "Ожидается восстановленная базовая единица")
        if base is instance:
            fields = {**fields, "base_unit": None}
        return super().from_fields(fields, instance=instance)

    @property
    def coefficient(self) -> int | float:
        """Возвращает коэффициент пересчёта в базовую единицу."""
        return self.__coefficient

    @property
    def base_unit(self) -> unit_model:
        """Возвращает базовую единицу измерения."""
        return self.__base_unit


    def convert_to(
        self,
        quantity: int | float,
        target_unit: unit_model,
    ) -> float:
        """Переводит количество в единицу с общей базовой единицей."""
        validator.validate_number(quantity, "quantity")
        validator.validate(
            target_unit,
            unit_model,
            field="target_unit",
        )

        if self.base_unit != target_unit.base_unit:
            raise arguments_exception(
                "target_unit",
                "Единицы имеют разные базовые единицы",
            )

        return quantity * (
            self.coefficient / target_unit.coefficient
        )


    """
    Фабричный метод - создать килограмм
    """
    @staticmethod
    def create_kilogram() -> unit_model:
        """Создаёт килограмм с коэффициентом 1000 относительно грамма."""
        gram = unit_model("грамм")
        return unit_model("килограмм", 1000, gram)


    @staticmethod
    def create_liter() -> unit_model:
        """Создаёт литр с базовой единицей — миллилитром."""
        milliliter = unit_model("миллилитр")
        return unit_model("литр", 1000, milliliter)

    @staticmethod
    def create_piece() -> unit_model:
        """Создаёт базовую единицу количества — штуку."""
        return unit_model("штука")
