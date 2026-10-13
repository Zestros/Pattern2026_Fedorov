from __future__ import annotations

from Src.Core.abstract_model import abstract_model
from Src.Core.validator import validator
from Src.Core.abstract_recipe_component import abstract_recipe_component
from Src.Models.unit_model import unit_model

class recipe_ingredient_model(abstract_model):
    """Строка состава: продукт, количество и назначение в текущей карте."""

    def __init__(
        self, item: abstract_recipe_component, quantity: int | float,
        is_packaging: bool = False,
    ) -> None:
        """Создаёт строку с количеством в единице учёта продукта."""
        super().__init__()
        validator.validate(item, abstract_recipe_component, field="item")
        validator.validate(is_packaging, bool, field="is_packaging")
        # Ссылка неизменяема: замена продукта должна проходить проверку карты.
        self.__item = item
        # Упаковка не входит в пищевое нетто и не подвергается обработке.
        self.__is_packaging = is_packaging
        self.quantity = quantity

    @property
    def item(self) -> abstract_recipe_component:
        """Возвращает обычный или составной продукт."""
        return self.__item

    @property
    def quantity(self) -> int | float:
        """Возвращает количество в единице учёта продукта."""
        return self.__quantity

    @quantity.setter
    def quantity(self, value: int | float) -> None:
        """Устанавливает неотрицательное количество продукта."""
        validator.validate_number(value, "quantity")
        self.__quantity = value

    @property
    def is_packaging(self) -> bool:
        """Показывает, используется ли продукт как упаковка в этой карте."""
        return self.__is_packaging

    def calculate_net_weight(self, target_unit: unit_model) -> float:
        """Возвращает пищевой вклад строки; упаковка даёт нулевой вклад."""
        validator.validate(target_unit, unit_model, field="target_unit")
        if self.is_packaging:
            return 0.0
        return self.item.calculate_net_weight(self.quantity, target_unit)

    def calculate_gross_weight(self, target_unit: unit_model) -> float:
        """Возвращает полную массу компонента с учётом количества строки."""
        return self.item.calculate_gross_weight(self.quantity, target_unit)

    def validate_recipe_path(self, path: set[int]) -> None:
        """Передаёт проверку вложенности компоненту строки."""
        self.item.validate_recipe_path(path)
