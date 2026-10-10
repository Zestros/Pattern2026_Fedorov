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

    @staticmethod
    def create_dough(
        group: group_model, kilogram: unit_model, liter: unit_model,
    ) -> recipe_item_model:
        """Создаёт тесто и его состав по стартовому рецепту."""
        flour = item_model.create_flour(group, kilogram)
        water = item_model.create_water(group, kilogram, liter)
        oil = item_model.create_oil(group, kilogram, liter)
        salt = item_model.create_salt(group, kilogram)
        recipe = recipe_model(
            "Тесто для пшеничных лепёшек", kilogram.base_unit,
            mass_coefficient=1,
        )
        recipe.add_ingredient(flour, 0.3)
        recipe.add_ingredient(water, 0.18)
        recipe.add_ingredient(oil, 0.015)
        recipe.add_ingredient(salt, 0.005)
        return recipe_item_model(
            "Тесто", "Тесто для пшеничных лепёшек", group, kilogram, recipe,
        )

    @staticmethod
    def create_flatbreads(
        dough: recipe_item_model, piece: unit_model,
    ) -> recipe_item_model:
        """Создаёт шесть лепёшек из полной партии теста на момент создания."""
        validator.validate(dough, recipe_item_model, field="dough")
        validator.validate(piece, unit_model, field="piece")
        recipe = recipe_model(
            "Пшеничные лепёшки", dough.recipe.mass_unit,
            mass_coefficient=0.9,
        )
        dough_quantity = dough.recipe.mass_unit.convert_to(
            dough.recipe.net_weight, dough.unit,
        )
        recipe.add_ingredient(dough, dough_quantity)
        return recipe_item_model(
            "Пшеничные лепёшки", "Пшеничные лепёшки",
            dough.group, piece, recipe, output_quantity=6,
        )
