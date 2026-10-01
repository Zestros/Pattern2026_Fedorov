from Src.Core.entity_model import entity_model


class group_model(entity_model):
    """Группа для объединения номенклатуры по общему признаку."""

    def __init__(self, name: str):
        """Создаёт группу с уникальным кодом и наименованием."""
        super().__init__()
        self.name = name