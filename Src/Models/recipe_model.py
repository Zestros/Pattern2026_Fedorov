from __future__ import annotations

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator
from Src.Models.item_model import item_model
from Src.Models.recipe_ingredient_model import recipe_ingredient_model
from Src.Models.unit_model import unit_model


class recipe_model(entity_model):
    """Карта: брутто до обработки, пищевое нетто после обработки и упаковка."""

    def __init__(
        self, name: str, mass_unit: unit_model,
        mass_coefficient: int | float = 1,
    ) -> None:
        """Создаёт пустую карту; mass_unit задаёт единицу всех итоговых масс."""
        super().__init__()
        self.name = name
        validator.validate(mass_unit, unit_model, field="mass_unit")
        validator.validate_number(mass_coefficient, "mass_coefficient", allow_zero=False)
        # Единица расчёта массы из общего справочника.
        self.__mass_unit = mass_unit
        # Коэффициент выхода пищевой части после обработки.
        self.__mass_coefficient = mass_coefficient
        # Коллекцию можно изменять только через методы карты.
        self.__ingredients: list[recipe_ingredient_model] = []

    @property
    def mass_unit(self) -> unit_model:
        """Возвращает общую единицу расчёта масс."""
        return self.__mass_unit

    @property
    def mass_coefficient(self) -> int | float:
        """Возвращает отношение пищевого выхода к входной массе."""
        return self.__mass_coefficient

    @property
    def ingredients(self) -> tuple[recipe_ingredient_model, ...]:
        """Возвращает строки без возможности менять коллекцию напрямую."""
        return tuple(self.__ingredients)

    def add_ingredient(
        self, item: item_model | recipe_ingredient_model,
        quantity: int | float | None = None, *, is_packaging: bool = False,
    ) -> recipe_ingredient_model:
        """Создаёт строку либо принимает готовую; проверяет циклы до добавления."""
        validator.validate(is_packaging, bool, field="is_packaging")
        if isinstance(item, recipe_ingredient_model):
            if quantity is not None or is_packaging:
                raise arguments_exception("ingredient", "Параметры готовой строки уже заданы")
            ingredient = item
        else:
            ingredient = recipe_ingredient_model(item, quantity, is_packaging)
        if any(row is ingredient for row in self.__ingredients):
            raise arguments_exception("ingredient", "Эта строка уже добавлена")
        if ingredient.recipe is not None:
            ingredient.recipe.__check_cycles({id(self)})
        self.__ingredients.append(ingredient)
        return ingredient

    def __check_cycles(self, path: set[int]) -> None:
        """Проверяет текущий путь; общие карты в независимых ветках разрешены."""
        if id(self) in path:
            raise arguments_exception("recipe", "Циклическая ссылка между картами")
        next_path = path | {id(self)}
        for ingredient in self.__ingredients:
            if ingredient.recipe is not None:
                ingredient.recipe.__check_cycles(next_path)

    def remove_ingredient(self, ingredient: recipe_ingredient_model) -> None:
        """Удаляет конкретную строку, не затрагивая другие строки того же продукта."""
        validator.validate(ingredient, recipe_ingredient_model, field="ingredient")
        for index, row in enumerate(self.__ingredients):
            if row is ingredient:
                del self.__ingredients[index]
                return
        raise arguments_exception("ingredient", "Строка отсутствует в карте")

    def __food_weight(self) -> float:
        """Суммирует готовую пищевую массу ингредиентов до текущей обработки."""
        return sum((
            row.item.calculate_mass(row.quantity, self.mass_unit)
            for row in self.__ingredients if not row.is_packaging
        ), 0.0)

    @property
    def packaging_weight(self) -> float:
        """Суммирует прямую упаковку и упаковку внутри составных продуктов."""
        from Src.Models.recipe_item_model import recipe_item_model

        result = 0.0
        for row in self.__ingredients:
            if row.is_packaging:
                result += row.item.calculate_mass(row.quantity, self.mass_unit)
            if isinstance(row.item, recipe_item_model):
                result += row.item.calculate_packaging_mass(row.quantity, self.mass_unit)
        return result

    @property
    def gross_weight(self) -> float:
        """Возвращает входную пищевую массу плюс упаковку текущей партии."""
        return self.__food_weight() + self.packaging_weight

    @property
    def net_weight(self) -> float:
        """Возвращает пищевой выход; упаковка не умножается на коэффициент."""
        return self.__food_weight() * self.mass_coefficient
