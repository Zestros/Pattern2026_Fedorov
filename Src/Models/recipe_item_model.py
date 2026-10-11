from __future__ import annotations

from Src.Core.validator import validator
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.unit_model import unit_model
from Src.Core.exception import arguments_exception

class recipe_item_model(item_model):
    """Составной продукт с картой; для штучного выхода задаётся размер партии."""

    def __init__(
        self,
        name: str,
        full_name: str,
        group: group_model,
        unit: unit_model,
        recipe: recipe_model,
        output_quantity: int | float | None = None,
    ) -> None:
        """Создаёт составной продукт без выполнения расчётов."""
        super().__init__(name, full_name, group, unit)

        validator.validate(recipe, recipe_model, field="recipe")

        if output_quantity is None:
            if unit.base_unit != recipe.mass_unit.base_unit:
                raise arguments_exception(
                    "output_quantity",
                    "Для продукта не в единицах массы необходимо указать выход партии",
                )
        else:
            validator.validate_number(
                output_quantity,
                "output_quantity",
                allow_zero=False,
            )

        self.__recipe = recipe
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

    @staticmethod
    def create_sponge_layers(
        flour: item_model, sugar: item_model, eggs: item_model,
        gram: unit_model, piece: unit_model,
    ) -> recipe_item_model:
        """Создаёт карту четырёх коржей из 600 г сырья с выходом 90%."""
        validator.validate(flour, item_model, field="flour")
        validator.validate(sugar, item_model, field="sugar")
        validator.validate(eggs, item_model, field="eggs")
        recipe = recipe_model("Бисквитные коржи", gram, mass_coefficient=0.9)
        recipe.add_ingredient(flour, gram.convert_to(200, flour.unit))
        recipe.add_ingredient(sugar, gram.convert_to(150, sugar.unit))
        recipe.add_ingredient(eggs, gram.convert_to(250, eggs.unit))
        return recipe_item_model(
            "Бисквитный корж", "Бисквитный корж для торта",
            flour.group, piece, recipe, output_quantity=4,
        )

    @staticmethod
    def create_sour_cream(
        sour_cream: item_model, sugar: item_model,
        gram: unit_model, piece: unit_model,
    ) -> recipe_item_model:
        """Создаёт одну порцию крема из 300 г сметаны и 100 г сахара."""
        validator.validate(sour_cream, item_model, field="sour_cream")
        validator.validate(sugar, item_model, field="sugar")
        recipe = recipe_model("Сметанный крем", gram, mass_coefficient=1)
        recipe.add_ingredient(sour_cream, gram.convert_to(300, sour_cream.unit))
        recipe.add_ingredient(sugar, gram.convert_to(100, sugar.unit))
        return recipe_item_model(
            "Порция крема", "Порция сметанного крема для торта",
            sour_cream.group, piece, recipe, output_quantity=1,
        )

    @staticmethod
    def create_cake(
        group: group_model, gram: unit_model, piece: unit_model,
    ) -> recipe_item_model:
        """Собирает торт из трёх коржей и порции крема с отдельными картами."""
        flour = item_model("Мука", "Мука пшеничная", group, gram)
        sugar = item_model("Сахар", "Сахар белый", group, gram)
        eggs = item_model("Яйцо", "Яйцо без скорлупы", group, gram)
        sour_cream = item_model("Сметана", "Сметана для крема", group, gram)

        layers = recipe_item_model.create_sponge_layers(
            flour, sugar, eggs, gram, piece,
        )
        cream = recipe_item_model.create_sour_cream(
            sour_cream, sugar, gram, piece,
        )

        recipe = recipe_model("Сборка бисквитного торта", gram, mass_coefficient=1)
        recipe.add_ingredient(layers, 3)
        recipe.add_ingredient(cream, 1)
        return recipe_item_model(
            "Бисквитный торт", "Бисквитный торт со сметанным кремом",
            group, piece, recipe, output_quantity=1,
        )
