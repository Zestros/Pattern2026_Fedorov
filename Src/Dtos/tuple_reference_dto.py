class tuple_reference_dto:
    """Временно обозначает ссылку на ещё собираемый неизменяемый кортеж."""

    def __init__(self, identifier: str) -> None:
        """Запоминает ID для связывания после создания кортежа."""
        self.identifier = identifier
