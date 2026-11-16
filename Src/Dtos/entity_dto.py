"""Общие данные сущности; код можно опустить при создании, но нельзя передать null."""
from Src.Core.abstract_dto import abstract_dto


class entity_dto(abstract_dto):
    """Общий контракт сущности с идентификатором и наименованием."""
    _optional_fields = ("unique_code",)
    unique_code: str
    name: str


class entity_summary_dto(abstract_dto):
    """Краткое представление сущности в списке API."""
    code: str
    name: str
