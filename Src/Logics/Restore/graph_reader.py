from Src.Core.exception import arguments_exception
from Src.Dtos.restoration_context_dto import restoration_context_dto
from Src.Logics.Restore.restore_factory import restore_factory


class graph_reader:
    """Управляет обходом графа и реестром ссылок, поручая типы отдельным обработчикам."""

    def __init__(self) -> None:
        """Создаёт контекст одной операции и фабрику обработчиков."""
        self.context = restoration_context_dto()
        self.factory = restore_factory()

    def read(self, source: object) -> object:
        """Проверяет документ, собирает граф, связывает кортежи и проверяет результат."""
        self._index(source)
        missing = self.context.references - self.context.definitions.keys()
        if missing:
            raise arguments_exception("$ref", f"Неизвестная ссылка: {sorted(missing)}")
        result = self.restore_value(source)
        for identifier, instance in self.context.objects.items():
            handler = self.factory.create(self.context.definitions[identifier])
            handler.resolve(instance, self.context)
        for identifier, instance in self.context.objects.items():
            node = self.context.definitions[identifier]
            self.factory.create(node).check(instance, node)
        return result

    def _index(self, source: object) -> None:
        """Проверяет определения и индексирует ссылки до создания экземпляров."""
        if source is None or isinstance(source, (str, int, float, bool)):
            return
        if not isinstance(source, dict):
            raise arguments_exception("source", "Составные значения требуют метаданные графа")
        if "$ref" in source:
            if set(source) != {"$ref"} or not isinstance(source["$ref"], str):
                raise arguments_exception("$ref", "Ссылка должна содержать только строковый $ref")
            self.context.references.add(source["$ref"])
            return
        handler = self.factory.create(source)
        handler.validate(source)
        if "$id" in source:
            identifier = source["$id"]
            if identifier in self.context.definitions:
                raise arguments_exception("$id", f"Повторное определение ID: {identifier}")
            self.context.definitions[identifier] = source
        for child in handler.children(source):
            self._index(child)

    def restore_value(self, source: object) -> object:
        """Возвращает простое значение или поручает узел выбранному обработчику."""
        if not isinstance(source, dict):
            return source
        if "$ref" in source:
            return self._restore_node(source["$ref"])
        if "$id" in source:
            return self._restore_node(source["$id"])
        return self.factory.create(source).restore(None, source, self)

    def _restore_node(self, identifier: str) -> object:
        """Регистрирует экземпляр до заполнения полей и сохраняет его идентичность."""
        if identifier in self.context.objects:
            return self.context.objects[identifier]
        node = self.context.definitions[identifier]
        handler = self.factory.create(node)
        instance = handler.allocate(node)
        self.context.objects[identifier] = instance
        instance = handler.restore(instance, node, self)
        self.context.objects[identifier] = instance
        return instance
