from __future__ import annotations

from Src.Core.validator import validator
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.unit_model import unit_model


class recipe_item_model(item_model):
    """Составной продукт с картой; для штучного выхода задаётся размер партии."""

    def __init__(
        self, name: str, full_name: str, group: group_model,
        unit: unit_model, recipe: recipe_model,
        output_quantity: int | float | None = None,
    ) -> None:
        """Связывает продукт с картой и выходом в единице учёта продукта.

        Без output_quantity количество означает готовую массу.
        При заданном выходе масса пропорциональна доле партии.
        """
        validator.validate(recipe, recipe_model, field="recipe")
        validator.validate(unit, unit_model, field="unit")
        if output_quantity is None:
            unit.convert_to(1, recipe.mass_unit)
        else:
            validator.validate_number(output_quantity, "output_quantity", allow_zero=False)
        super().__init__(name, full_name, group, unit)
        # Неизменяемая ссылка защищает граф от обхода проверки циклов.
        self.__recipe = recipe
        # Выход одной партии в единице учёта; None для готовой массы.
        self.__output_quantity = output_quantity

    @property
    def recipe(self) -> recipe_model:
        """Возвращает технологическую карту продукта."""
        return self.__recipe

    @property
    def output_quantity(self) -> int | float | None:
        """Возвращает выход партии или None для весового продукта."""
        return self.__output_quantity

    def calculate_mass(
        self, quantity: int | float, target_unit: unit_model,
        source_unit: unit_model | None = None,
    ) -> float:
        """Возвращает пищевую массу без упаковки для указанного количества."""
        source = self.unit if source_unit is None else source_unit
        validator.validate(source, unit_model, field="source_unit")
        if self.output_quantity is None:
            return source.convert_to(quantity, target_unit)
        fraction = source.convert_to(quantity, self.unit) / self.output_quantity
        return self.recipe.mass_unit.convert_to(
            self.recipe.net_weight * fraction, target_unit
        )

    def calculate_packaging_mass(
        self, quantity: int | float, target_unit: unit_model,
    ) -> float:
        """Переносит упаковку вложенной карты пропорционально количеству продукта."""
        validator.validate_number(quantity, "quantity")
        packaging = self.recipe.packaging_weight
        if packaging == 0 or quantity == 0:
            return self.recipe.mass_unit.convert_to(0, target_unit)
        if self.output_quantity is None:
            net_weight = self.recipe.net_weight
            validator.validate_number(net_weight, "net_weight", allow_zero=False)
            fraction = self.unit.convert_to(quantity, self.recipe.mass_unit) / net_weight
        else:
            fraction = quantity / self.output_quantity
        return self.recipe.mass_unit.convert_to(packaging * fraction, target_unit)
