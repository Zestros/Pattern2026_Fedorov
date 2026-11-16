from Src.Core.abstract_dto import abstract_dto
from Src.Dtos.entity_dto import entity_dto


class ingredient_dto(abstract_dto):
    """Строка рецепта со ссылкой на продукт, количеством и признаком упаковки."""
    _optional_fields = ("unique_code",)
    _references = {"item": "item"}
    unique_code: str
    item: str
    quantity: int | float
    is_packaging: bool = False


class recipe_dto(entity_dto):
    """Контракт технологической карты с составом и расчётными массами."""
    _references = {"mass_unit": "unit"}
    _read_only_fields = ("packaging_weight", "gross_weight", "net_weight")
    mass_unit: str
    mass_coefficient: int | float = 1
    ingredients: tuple[ingredient_dto, ...] = ()
    packaging_weight: int | float
    gross_weight: int | float
    net_weight: int | float
