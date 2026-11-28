import json
from pathlib import Path
from threading import Lock
from typing import TextIO

from Src.Core.event_phase import event_phase
from Src.Dtos.operation_event_dto import operation_event_dto


class operation_logger:
    """Записывает события операций в файл или текстовый поток в формате JSON Lines."""

    # Уровень и сообщение для каждой стадии операции.
    __phase_labels = {
        event_phase.STARTED: ("DEBUG", "Операция начата"),
        event_phase.COMPLETED: ("INFO", "Операция завершена"),
        event_phase.REJECTED: ("INFO", "Операция отклонена"),
        event_phase.FAILED: ("ERROR", "Операция завершилась с ошибкой"),
    }

    def __init__(self, destination: TextIO | Path) -> None:
        """Принимает путь к файлу журнала или открытый текстовый поток."""
        self.__destination = destination
        self.__lock = Lock()

    def write(self, event: operation_event_dto) -> None:
        """Формирует одну запись и пропускает отсутствующие поля."""
        level, message = self.__phase_labels[event.phase]
        record = {
            "subsystem": event.subsystem.value,
            "operation": event.operation,
            "phase": event.phase.value,
            "period": event.occurred_at.isoformat(),
            "level": level,
            "message": message,
            "entity_type": event.entity_type,
            "entity_code": event.entity_code,
            "reason_code": event.reason_code,
            "details": event.details,
        }
        fields = {name: value for name, value in record.items() if value is not None}
        line = json.dumps(fields, ensure_ascii=False) + "\n"
        with self.__lock:
            destination = self.__destination
            if isinstance(destination, Path):
                with destination.open("a", encoding="utf-8") as log_file:
                    log_file.write(line)
            else:
                destination.write(line)
                destination.flush()
