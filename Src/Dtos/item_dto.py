from Src.Core.abstract_dto import abstract_dto
from Src.Dtos.entity_dto import entity_dto


class ratio_unit_dto(abstract_dto):
    """Составная единица характеристики массы со ссылками на единицы справочника."""
    _optional_fields = ("unique_code",)
    _references = {"numerator_unit": "unit", "denominator_unit": "unit"}
    unique_code: str
    numerator_unit: str
    denominator_unit: str


class mass_ratio_dto(abstract_dto):
    """Значение характеристики массы и её составная единица."""
    _optional_fields = ("unique_code",)
    unique_code: str
    value: int | float
    unit: ratio_unit_dto


class item_dto(entity_dto):
    """Контракт номенклатуры; внешние связи передаются кодами."""
    _references = {"group": "group", "unit": "unit"}
    full_name: str
    group: str
    unit: str
    mass_ratio: mass_ratio_dto | None = None


class recipe_item_dto(item_dto):
    """Дополнение контракта для продукта по технологической карте."""
    _references = {"recipe": "recipe"}
    recipe: str
    output_quantity: int | float | None = None
