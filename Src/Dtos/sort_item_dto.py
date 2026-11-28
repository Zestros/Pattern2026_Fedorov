from Src.Core.abstract_dto import abstract_dto
from Src.Core.exception import arguments_exception
from Src.Core.field_path import field_path
from Src.Core.sort_direction_enum import sort_direction_enum
from Src.Core.validator import validator


class sort_item_dto(abstract_dto):
    """Сортировка по одному полю."""

    # По умолчанию правило сортирует по возрастанию.
    _optional_fields = ("direction",)
    __direction = sort_direction_enum.ASC

    @property
    def field(self) -> str:
        """Возвращает путь к полю сортировки."""
        return self.__field

    @field.setter
    def field(self, value: str) -> None:
        """Сохраняет корректный путь из публичных имён."""
        field_path.validate(value)
        object.__setattr__(self, "_sort_item_dto__field", value)

    @property
    def direction(self) -> sort_direction_enum:
        """Возвращает направление сортировки."""
        return self.__direction

    @direction.setter
    def direction(self, value: sort_direction_enum) -> None:
        """Допускает только направления из перечисления."""
        validator.validate(value, sort_direction_enum, field="direction")
        object.__setattr__(self, "_sort_item_dto__direction", value)

    def apply(self, models: list, path: field_path) -> None:
        """Сортирует по одиночному полю и ставит пропуски в конец."""
        if path.is_collection:
            raise arguments_exception("field", f"Сортировка по коллекции недоступна: {self.field}")

        descending = self.direction is sort_direction_enum.DESC
        ignore_case = self.field.rsplit(".", 1)[-1] != "unique_code"

        def key(model: object) -> tuple[bool, str]:
            """Размещает пустые значения после заполненных в обоих направлениях."""
            value = next(path.values(model), None)
            if not isinstance(value, str):
                return not descending, ""
            return descending, value.casefold() if ignore_case else value

        models.sort(key=key, reverse=descending)
