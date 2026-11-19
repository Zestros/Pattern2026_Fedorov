from Src.Dtos.entity_dto import entity_dto


class unit_dto(entity_dto):
    """Базовая или производная единица измерения."""
    _references = {"base_unit": "unit"}
    coefficient: int | float = 1
    base_unit: str | None = None
