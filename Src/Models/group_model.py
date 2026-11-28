from __future__ import annotations

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator


class group_model(entity_model):
    """Группа для объединения номенклатуры по общему признаку."""

    # Для старых данных и корневых групп владелец отсутствует.
    __parent: group_model | None = None

    def __init__(self, name: str, parent: group_model | None = None) -> None:
        """Создаёт группу с необязательной ссылкой на группу-владельца."""
        super().__init__()
        self.name = name
        if parent is not None:
            validator.validate(parent, group_model, field="parent")
        self.__parent = parent
        self.validate_state()

    @property
    def parent(self) -> group_model | None:
        """Возвращает группу-владельца."""
        return self.__parent

    def validate_state(self) -> None:
        """Отклоняет циклические ссылки в цепочке групп-владельцев."""
        visited = {id(self)}
        parent = self.parent
        while parent is not None:
            if id(parent) in visited:
                raise arguments_exception("parent", "Циклическая ссылка между группами")
            visited.add(id(parent))
            parent = parent.parent


    @staticmethod
    def create_grocery() -> group_model:
        """Создаёт группу базовых продуктов."""
        return group_model("Бакалея")
