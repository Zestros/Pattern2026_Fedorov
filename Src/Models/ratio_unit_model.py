from __future__ import annotations

from Src.Core.abstract_model import abstract_model
from Src.Core.validator import validator
from Src.Models.unit_model import unit_model


class ratio_unit_model(abstract_model):
    """Составная единица: отношение двух единиц общего справочника."""

    def __init__(
        self,
        numerator_unit: unit_model,
        denominator_unit: unit_model,
    ) -> None:
        """Сохраняет единицы числителя и знаменателя без копирования."""
        super().__init__()
        validator.validate(numerator_unit, unit_model, field="numerator_unit")
        validator.validate(denominator_unit, unit_model, field="denominator_unit")
        # Единица числителя отношения.
        self.__numerator_unit = numerator_unit
        # Единица знаменателя отношения.
        self.__denominator_unit = denominator_unit

    @property
    def numerator_unit(self) -> unit_model:
        """Возвращает единицу числителя."""
        return self.__numerator_unit

    @property
    def denominator_unit(self) -> unit_model:
        """Возвращает единицу знаменателя."""
        return self.__denominator_unit

    def convert_to(self, value: int | float, target_unit: ratio_unit_model) -> float:
        """Переводит значение с учётом обеих частей составной единицы."""
        validator.validate_number(value, "value")
        validator.validate(target_unit, ratio_unit_model, field="target_unit")
        numerator_factor = self.numerator_unit.convert_to(
            1, target_unit.numerator_unit
        )
        denominator_factor = self.denominator_unit.convert_to(
            1, target_unit.denominator_unit
        )
        return value * numerator_factor / denominator_factor


    """Фабричные методы"""
    @staticmethod
    def grams_per_milliliter(
        gram: unit_model, milliliter: unit_model,
    ) -> ratio_unit_model:
        """Создаёт г/мл из переданных грамма и миллилитра справочника."""
        return ratio_unit_model(gram, milliliter)

    @staticmethod
    def kilograms_per_liter(
        kilogram: unit_model, liter: unit_model,
    ) -> ratio_unit_model:
        """Создаёт кг/л из переданных килограмма и литра справочника."""
        return ratio_unit_model(kilogram, liter)

    @staticmethod
    def grams_per_piece(
        gram: unit_model, piece: unit_model,
    ) -> ratio_unit_model:
        """Создаёт г/шт из переданных грамма и штуки справочника."""
        return ratio_unit_model(gram, piece)

    @staticmethod
    def kilograms_per_piece(
        kilogram: unit_model, piece: unit_model,
    ) -> ratio_unit_model:
        """Создаёт кг/шт из переданных килограмма и штуки справочника."""
        return ratio_unit_model(kilogram, piece)
