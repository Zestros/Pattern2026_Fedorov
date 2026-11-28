from threading import RLock
from collections.abc import Iterable, Callable
from Src.Core.abstract_entity_repository import abstract_entity_repository, validate_entity_type
from Src.Core.entity_model import entity_model
from Src.Core.entity_conflict_exception import entity_conflict_exception
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator
from Src.Logics.reference_graph import reference_graph
from Src.Logics.entity_state import entity_state


class storage_repository(abstract_entity_repository):
    """Хранит объекты по коду и атомарно регистрирует граф их зависимостей."""
    def __init__(self) -> None:
        """Создаёт независимый каталог, граф ссылок и общую блокировку операций."""
        self.__models = {}
        self.__graph = reference_graph()
        self.__lock = RLock()

    def list(self, entity_type: type[entity_model]) -> tuple[entity_model, ...]:
        """Возвращает снимок состава коллекции в порядке регистрации."""
        validate_entity_type(entity_type)
        with self.__lock:
            return tuple(model for model in self.__models.values() if isinstance(model, entity_type))

    def find(self, entity_type: type[entity_model], code: str) -> entity_model | None:
        """Находит зарегистрированный объект по типу и коду."""
        validate_entity_type(entity_type)
        validator.validate(code, str, field="code")
        with self.__lock:
            model = self.__models.get(code.strip())
            return model if isinstance(model, entity_type) else None

    def add(self, entity_type: type[entity_model], value: entity_model) -> None:
        """Регистрирует сущность, используя те же проверки, что и загрузка коллекций."""
        validate_entity_type(entity_type)
        validator.validate(value, entity_type)
        self.register_models((value,))

    def find_references(self, entity_type: type[entity_model], code: str) -> tuple[entity_model, ...]:
        """Находит владельцев входящих ссылок, включая строки и характеристики массы."""
        with self.__lock:
            model = self.find(entity_type, code)
            if model is None:
                return ()
            return tuple(self.__models[owner] for owner in self.__graph.owners(model.unique_code))

    def delete(self, entity_type: type[entity_model], code: str) -> bool:
        """Удаляет сущность без входящих ссылок и снимает её исходящие связи."""
        with self.__lock:
            model = self.find(entity_type, code)
            if model is None:
                return False
            if self.find_references(entity_type, code):
                raise entity_conflict_exception("code", "На сущность ссылаются другие сущности")
            self.__graph.remove(model.unique_code, self.__graph.targets(model))
            del self.__models[model.unique_code]
            model._set_registered(False)
            return True

    def update(
        self, entity_type: type[entity_model], code: str, fields: dict[str, object],
    ) -> entity_model | None:
        """Проверяет частичное изменение и сохраняет идентичность существующей модели."""
        return self.change(entity_type, code, lambda model: model.updated_copy(fields))

    def change(
        self, entity_type: type[entity_model], code: str,
        prepare: Callable[[entity_model], entity_model],
    ) -> entity_model | None:
        """Атомарно принимает подготовленное состояние без словаря полей и рефлексии сборки."""
        with self.__lock:
            model = self.find(entity_type, code)
            if model is None:
                return None
            candidate = prepare(model)
            if type(candidate) is not type(model) or candidate.is_registered:
                raise arguments_exception("candidate", "Ожидается новый экземпляр того же типа")
            old_code = model.unique_code
            new_code = candidate.unique_code
            if new_code != old_code:
                if self.find_references(entity_type, old_code):
                    raise entity_conflict_exception("unique_code", "На сущность ссылаются другие сущности")
                if new_code in self.__models:
                    raise entity_conflict_exception("unique_code", "Объект с таким кодом уже существует")

            pending = {new_code: candidate}
            self.__collect_dependencies(pending, original=model)
            del pending[new_code]
            new_targets = self.__graph.validate_targets(self.__models, pending, candidate, original=model)
            for value in pending.values():
                self.__graph.validate_targets(self.__models, pending, value)
            old_targets = self.__graph.targets(model)
            with entity_state.apply(model, candidate):
                self.__graph.validate_affected(self.__models, old_code, model)
                for value in pending.values():
                    value.validate_state()
                outgoing = {code: self.__graph.targets(value) for code, value in pending.items()}

            self.__publish(pending, outgoing)

            self.__graph.remove(old_code, old_targets)
            if new_code != old_code:
                del self.__models[old_code]
                self.__models[new_code] = model
            self.__graph.add(new_code, new_targets)
            return model

    def register_models(self, values: Iterable[entity_model]) -> None:
        """Регистрирует корни и ещё не сохранённые зависимости единым пакетом."""
        with self.__lock:
            pending: dict[str, entity_model] = {}
            for value in values:
                validator.validate(value, entity_model)
                self.__stage(pending, value)

            self.__collect_dependencies(pending)
            outgoing = {}
            for code, value in pending.items():
                outgoing[code] = self.__graph.validate_targets(self.__models, pending, value)
                value.validate_state()
            self.__publish(pending, outgoing)

    def __collect_dependencies(self, pending: dict, original: entity_model | None = None) -> None:
        """Обходит каждый новый объект один раз, переиспользуя сохранённые зависимости."""
        queue = list(pending.values())
        while queue:
            owner = queue.pop()
            for field, target in self.__graph.references(owner):
                validator.validate(target, entity_model, field=field)
                if target is original:
                    continue
                known = pending.get(target.unique_code) or self.__models.get(target.unique_code)
                if known is target:
                    continue
                if known is not None:
                    raise entity_conflict_exception(field, "Разные объекты имеют одинаковый код")
                self.__stage(pending, target)
                queue.append(target)

    def __publish(self, pending: dict, outgoing: dict) -> None:
        """Публикует проверенные объекты и связи под общей блокировкой репозитория."""
        self.__models.update(pending)
        for code, value in pending.items():
            self.__graph.add(code, outgoing[code])
            value._set_registered(True)

    def __stage(self, pending: dict[str, entity_model], value: entity_model) -> None:
        """Отклоняет повторную регистрацию и конфликт кода между типами."""
        code = value.unique_code
        if code in pending or code in self.__models:
            raise entity_conflict_exception("unique_code", "Объект с таким кодом уже существует")
        if value.is_registered:
            raise entity_conflict_exception("value", "Сущность уже зарегистрирована в другом хранилище")
        pending[code] = value
