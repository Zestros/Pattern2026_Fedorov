from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum


def field_values(model: object, path: tuple[str, ...]) -> Iterator[object]:
    """Читает вложенные значения, разворачивая коллекции и пропуская None."""
    pending = [(model, 0)]
    collections = {}
    while pending:
        value, index = pending.pop()
        if isinstance(value, (list, tuple)):
            key = (id(value), index)
            if key not in collections:
                # Держим временные коллекции, чтобы при обходе не переиспользовались их id.
                collections[key] = value
                pending.extend((item, index) for item in reversed(value))
        elif value is not None:
            if index == len(path):
                yield value
            else:
                pending.append((getattr(value, path[index], None), index + 1))


class sort_direction_enum(Enum):
    """Направление сортировки результатов."""

    # По возрастанию.
    ASC = "ASC"
    # По убыванию.
    DESC = "DESC"


@dataclass(frozen=True)
class filter_item:
    """Проверяет условие для значений одного поля."""

    # Сегменты пути к полю модели.
    field: tuple[str, ...]
    # Операция сравнения значения поля со значением фильтра.
    operator: Callable
    # Значение для сравнения.
    value: object

    def matches(self, model: object) -> bool:
        """Возвращает совпадение хотя бы для одного значения на пути."""
        return any(self.operator(actual, self.value) for actual in field_values(model, self.field))


@dataclass(frozen=True)
class sort_item:
    """Задаёт порядок по одному полю."""

    # Сегменты пути к полю модели.
    field: tuple[str, ...]
    # Направление сортировки по этому полю.
    direction: sort_direction_enum
    # Признак сортировки текста без учёта регистра.
    ignore_case: bool = False

    @property
    def descending(self) -> bool:
        """Показывает, нужен ли обратный порядок сравнения ключей."""
        return self.direction is sort_direction_enum.DESC

    def key(self, model: object) -> tuple[bool, object]:
        """Выбирает крайнее значение из коллекции и оставляет пропуски в конце."""
        values = field_values(model, self.field)
        if self.ignore_case:
            values = (value.casefold() for value in values if isinstance(value, str))
        extreme = max if self.descending else min
        value = extreme(values, default=None)
        return ((value is None) != self.descending, value)


@dataclass(frozen=True)
class filter_criteria:
    """Объединяет условия отбора и правила сортировки коллекции."""

    # Условия, которые должны выполняться одновременно.
    filters: tuple[filter_item, ...] = ()
    # Правила сортировки по приоритету.
    sort: tuple[sort_item, ...] = ()
