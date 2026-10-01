from __future__ import annotations

import math

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

            if base_unit.base_unit is not base_unit:
                raise arguments_exception(
                    "base_unit",
                    "Нельзя использовать производную единицу как базовую",
                )

        self.__coefficient = coefficient
        self.__base_unit = base_unit

    @property
    def coefficient(self) -> int | float:
        """Возвращает коэффициент пересчёта в базовую единицу."""
        return self.__coefficient

    @property
    def base_unit(self) -> unit_model:
        """Возвращает базовую единицу измерения."""
        return self.__base_unit