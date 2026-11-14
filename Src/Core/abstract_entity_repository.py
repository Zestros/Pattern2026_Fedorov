from abc import ABC, abstractmethod

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception


def validate_entity_type(entity_type: object) -> None:
    """Проверяет, что передан класс доменной сущности."""
    if not isinstance(entity_type, type) or not issubclass(entity_type, entity_model):
        raise arguments_exception("entity_type", "Ожидается класс доменной сущности")


class abstract_entity_repository(ABC):
    """Контракт доступа к сущностям. Полученные модели предназначены для чтения."""

    @abstractmethod
    def list(self, entity_type: type[entity_model]) -> tuple[entity_model, ...]:
        """Возвращает зарегистрированные сущности указанного типа."""

    @abstractmethod
    def find(self, entity_type: type[entity_model], code: str) -> entity_model | None:
        """Возвращает сущность по коду или None при её отсутствии."""

    @abstractmethod
    def add(self, entity_type: type[entity_model], value: entity_model) -> None:
        """Регистрирует сущность после проверки типа, кода и связей."""

    @abstractmethod
    def find_references(self, entity_type: type[entity_model], code: str) -> tuple[entity_model, ...]:
        """Возвращает сущности с прямой входящей ссылкой или пустой кортеж."""

    @abstractmethod
    def update(
        self, entity_type: type[entity_model], code: str, fields: dict[str, object],
    ) -> entity_model | None:
        """Применяет частичные изменения или возвращает None для отсутствующего кода."""

    @abstractmethod
    def delete(self, entity_type: type[entity_model], code: str) -> bool:
        """Удаляет сущность либо возвращает False, если она отсутствует."""
