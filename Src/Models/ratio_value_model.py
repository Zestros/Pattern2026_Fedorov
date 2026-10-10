from Src.Core.abstract_model import abstract_model
from Src.Core.validator import validator
from Src.Models.ratio_unit_model import ratio_unit_model
from Src.Models.unit_model import unit_model


class ratio_value_model(abstract_model):
    """Положительная характеристика с единицами: плотность или масса штуки."""

    def __init__(self, value: int | float, unit: ratio_unit_model) -> None:
        """Сохраняет положительное значение вместе с составной единицей."""
        super().__init__()
        validator.validate_number(value, "value", allow_zero=False)
        validator.validate(unit, ratio_unit_model, field="unit")
        # Значение характеристики в указанной составной единице.
        self.__value = value
        # Единицы числителя и знаменателя характеристики.
        self.__unit = unit

    @property
    def value(self) -> int | float:
        """Возвращает значение характеристики."""
        return self.__value

    @property
    def unit(self) -> ratio_unit_model:
        """Возвращает составную единицу характеристики."""
        return self.__unit

    def calculate_mass(
        self,
        quantity: int | float,
        source_unit: unit_model,
        target_unit: unit_model,
    ) -> float:
        """Вычисляет массу; числитель характеристики должен задавать массу."""
        validator.validate_number(quantity, "quantity")
        validator.validate(source_unit, unit_model, field="source_unit")
        validator.validate(target_unit, unit_model, field="target_unit")
        amount = source_unit.convert_to(quantity, self.unit.denominator_unit)
        return self.unit.numerator_unit.convert_to(
            amount * self.value, target_unit
        )
