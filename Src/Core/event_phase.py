from enum import Enum


class event_phase(Enum):
    """Стадия операции, которую фиксирует событие."""

    # Операция началась.
    STARTED = "started"
    # Операция успешно завершилась.
    COMPLETED = "completed"
    # Операция отклонена по известной причине.
    REJECTED = "rejected"
    # Операция прервалась из-за неожиданной ошибки.
    FAILED = "failed"
