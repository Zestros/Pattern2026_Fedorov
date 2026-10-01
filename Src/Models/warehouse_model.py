from Src.Core.entity_model import entity_model


class warehouse_model(entity_model):
    """Склад для учёта запасов номенклатуры."""

    def __init__(self, name: str) -> None:
        """Создаёт склад с уникальным кодом и наименованием."""
        super().__init__()
        self.name = name