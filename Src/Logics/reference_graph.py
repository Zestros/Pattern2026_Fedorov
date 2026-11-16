from collections.abc import Iterator
from Src.Core.abstract_model import abstract_model
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator


class reference_graph:
    """Ведёт входящие ссылки; используется внутри блокировки репозитория."""
    def __init__(self) -> None:
        """Создаёт пустой индекс владельцев ссылок."""
        self.__incoming = {}

    def owners(self, code: str) -> tuple[str, ...]:
        """Возвращает снимок кодов владельцев входящих ссылок."""
        return tuple(self.__incoming.get(code, ()))

    def validate_affected(self, models: dict, old_code: str, model: entity_model) -> None:
        """Проверяет изменённую модель и её зависимые сущности по индексу."""
        pending = [old_code]
        visited: set[str] = set()
        while pending:
            code = pending.pop()
            if code in visited:
                continue
            visited.add(code)
            affected = model if code == old_code else models[code]
            affected.validate_state()
            pending.extend(self.__incoming.get(code, ()))

    def validate_targets(
        self, models: dict, pending: dict[str, entity_model], value: entity_model, *, original: entity_model | None = None,
    ) -> set[str]:
        """Проверяет регистрацию целей и возвращает их коды для индекса."""
        targets = set()
        for field, target in self.references(value):
            if target is value or target is original:
                continue
            validator.validate(target, entity_model, field=field)
            registered = pending.get(target.unique_code) or models.get(target.unique_code)
            if registered is not target:
                raise arguments_exception(field, "Связанная сущность отсутствует в хранилище")
            targets.add(target.unique_code)
        return targets

    @staticmethod
    def targets(model: entity_model) -> set[str]:
        """Возвращает коды исходящих связей для удаления записей из индекса."""
        return {target.unique_code for _, target in reference_graph.references(model) if target is not model}

    def add(self, owner: str, targets: set[str]) -> None:
        """Добавляет владельца к входящим ссылкам каждой цели."""
        for target in targets:
            self.__incoming.setdefault(target, set()).add(owner)

    def remove(self, owner: str, targets: set[str]) -> None:
        """Снимает исходящие связи владельца и освобождает пустые записи индекса."""
        for target in targets:
            owners = self.__incoming[target]
            owners.remove(owner)
            if not owners:
                del self.__incoming[target]

    @staticmethod
    def references(model: entity_model) -> Iterator[tuple[str, "entity_model"]]:
        """Находит прямые ссылки через поля модели и вложенные значения."""
        visited = {id(model)}

        def walk(field: str, value: object) -> Iterator[tuple[str, entity_model]]:
            """Разворачивает вложенные значения до границы другой сущности."""
            if isinstance(value, entity_model):
                if value is not model:
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

        for name in model.field_names():
            if name not in model.computed_fields:
                yield from walk(name, getattr(model, name))
