from __future__ import annotations

from Src.Core.abstract_model import abstract_model
from Src.Core.validator import validator
from Src.Models.item_model import item_model



class recipe_ingredient_model(abstract_model):
    """Строка состава: продукт, количество и назначение в текущей карте."""

    def __init__(
        self, item: item_model, quantity: int | float,
        is_packaging: bool = False,
    ) -> None:
        """Создаёт строку с количеством в единице учёта продукта."""
        super().__init__()
        validator.validate(item, item_model, field="item")
        validator.validate(is_packaging, bool, field="is_packaging")
        # Ссылка неизменяема: замена продукта должна проходить проверку карты.
        self.__item = item
        # Упаковка не входит в пищевое нетто и не подвергается обработке.
        self.__is_packaging = is_packaging
        self.quantity = quantity

    @property
    def item(self) -> item_model:
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

    @property
    def recipe(self) -> recipe_model | None:
        """Возвращает карту составного продукта без дублирования ссылки."""
        from Src.Models.recipe_item_model import recipe_item_model
        
        return self.item.recipe if isinstance(self.item, recipe_item_model) else None
