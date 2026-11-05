class restoration_context_dto:
    """Хранит определения и восстановленные объекты одного документа."""

    def __init__(self) -> None:
        """Создаёт независимые таблицы одной операции восстановления."""
        # Служебный ID → определение узла JSON.
        self.definitions: dict[str, dict] = {}
        # Все ссылки, обнаруженные при проверке документа.
        self.references: set[str] = set()
        # Служебный ID → созданный экземпляр, включая ещё заполняемые объекты.
        self.objects: dict[str, object] = {}


class tuple_reference_dto:
    """Временно обозначает ссылку на ещё собираемый неизменяемый кортеж."""

    def __init__(self, identifier: str) -> None:
        """Запоминает ID для связывания после создания кортежа."""
        self.identifier = identifier
