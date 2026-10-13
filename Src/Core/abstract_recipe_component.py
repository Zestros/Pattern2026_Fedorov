from abc import ABC, abstractmethod

from Src.Models.unit_model import unit_model


class abstract_recipe_component(ABC):
    """Общий контракт массы и проверки вложенности продукта рецепта."""

    @abstractmethod
    def calculate_net_weight(
        self, quantity: int | float, target_unit: unit_model,
    ) -> float:
        """Возвращает чистую массу указанного количества готового продукта."""
        pass

    @abstractmethod
    def calculate_gross_weight(
        self, quantity: int | float, target_unit: unit_model,
    ) -> float:
        """Возвращает готовую массу продукта вместе с его упаковкой."""
        pass

    @abstractmethod
    def validate_recipe_path(self, path: set[int]) -> None:
        """Проверяет текущий путь вложенных карт на циклы."""
        pass
