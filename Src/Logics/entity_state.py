from contextlib import contextmanager
from Src.Core.entity_model import entity_model


class entity_state:
    """Применяет кандидат к существующему экземпляру на время проверки транзакции."""
    @staticmethod
    @contextmanager
    def apply(model: entity_model, candidate: entity_model):
        """Меняет состояние на время проверки и восстанавливает его при ошибке."""
        previous = vars(model)
        updated = {
            name: model if value is candidate else value
            for name, value in vars(candidate).items()
        }
        object.__setattr__(model, "__dict__", {**previous, **updated})
        try:
            yield
        except BaseException:
            object.__setattr__(model, "__dict__", previous)
            raise

