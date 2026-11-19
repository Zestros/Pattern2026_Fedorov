from Src.Dtos.entity_dto import entity_dto


class group_dto(entity_dto):
    """Контракт группы номенклатуры."""

    # Код группы-владельца, если группа входит в другую группу.
    _references = {"parent": "group"}
    parent: str | None = None
