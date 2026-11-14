from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import Self

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import  arguments_exception


class entity_model(abstract_model):
    """Базовая модель с уникальным кодом и наименованием."""

    "Наименование сущности."
    __name:str = ""

    def references(self) -> Iterator[tuple[str, "entity_model"]]:
        """Находит прямые ссылки через поля модели и вложенные значения."""
        visited = {id(self)}

        def walk(field: str, value: object) -> Iterator[tuple[str, entity_model]]:
            """Разворачивает вложенные значения до границы другой сущности."""
            if isinstance(value, entity_model):
                if value is not self:
                    yield field, value
                return
            if not isinstance(value, (abstract_model, list, tuple, dict)) or id(value) in visited:
                return
            visited.add(id(value))
            if isinstance(value, abstract_model):
                for name in value.field_names():
                    if name not in value.computed_fields:
                        yield from walk(f"{field}.{name}", getattr(value, name))
            elif isinstance(value, (list, tuple)):
                for item in value:
                    yield from walk(field, item)
            elif isinstance(value, dict):
                for key, item in value.items():
                    yield from walk(field, key)
                    yield from walk(field, item)

        for name in self.field_names():
            if name not in self.computed_fields:
                yield from walk(name, getattr(self, name))

    def validate_state(self) -> None:
        """Проверяет доменные ограничения после изменения связанных сущностей."""

    def updated_copy(self, fields: dict[str, object]) -> Self:
        """Создаёт кандидат на обновление через фабричный метод модели."""
        self.validate_fields(fields)
        for name in fields.keys() & set(self.computed_fields):
            raise arguments_exception(name, "Расчётное поле нельзя изменить")
        values = {
            name: getattr(self, name) for name in self.field_names()
            if name not in self.computed_fields
        }
        values.update(fields)
        model_type = type(self)
        candidate = model_type.__new__(model_type)
        values = {name: candidate if value is self else value for name, value in values.items()}
        return model_type.from_fields(values, instance=candidate)

    @contextmanager
    def _apply_update(self, candidate: Self) -> Generator[None, None, None]:
        """Меняет состояние на время проверки и восстанавливает его при ошибке."""
        previous = vars(self)
        updated = {
            name: self if value is candidate else value
            for name, value in vars(candidate).items()
        }
        object.__setattr__(self, "__dict__", {**previous, **updated})
        try:
            yield
        except BaseException:
            object.__setattr__(self, "__dict__", previous)
            raise

    @property
    def is_registered(self) -> bool:
        """Показывает, что изменение сущности принадлежит репозиторию."""
        return getattr(self, "_entity_model__registered", False)

    def _set_registered(self, registered: bool) -> None:
        """Фиксирует регистрацию сущности при успешной операции репозитория."""
        object.__setattr__(self, "_entity_model__registered", registered)

    def _ensure_editable(self) -> None:
        """Защищает зарегистрированную сущность от изменения в обход репозитория."""
        if self.is_registered:
            raise arguments_exception("entity", "Изменяйте зарегистрированную сущность через репозиторий")

    def __setattr__(self, name: str, value: object) -> None:
        """Проверяет доступность изменений до вызова сеттера."""
        self._ensure_editable()
        super().__setattr__(name, value)

    @property
    def name(self) -> str:
        """Возвращает наименование сущности."""
        return self.__name

    @name.setter
    def name(self, value:str):
        """Устанавливает непустое наименование длиной до 50 символов."""
        if not isinstance(value, str):
            raise arguments_exception(
                "name",
                "Наименование должно быть строкой",
            )

        name = value.strip()

        if name == "":
            raise arguments_exception(
                "name",
                "Наименование не может быть пустым",
            )

        if len(name) > 50:
            raise arguments_exception(
                "name",
                "Наименование не может превышать 50 символов",
            )

        self.__name = name
