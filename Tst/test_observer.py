"""Модульные проверки DTO события, доставки и записи в журнал."""

from datetime import datetime, timedelta, timezone
from io import StringIO
import json

import pytest

from Src.Core.crud_operation import crud_operation
from Src.Core.event_phase import event_phase
from Src.Core.exception import arguments_exception
from Src.Core.log_subsystem import log_subsystem
from Src.Core.observer import observer
from Src.Dtos.operation_event_dto import operation_event_dto
from Src.Logics.logging_observer import logging_observer
from Src.Logics.operation_logger import operation_logger


def test_delivered_event_notify_reaches_each_registered_subscriber_once():
    """<summary>Диспетчер доставляет исходное событие своим подписчикам по одному разу.</summary>"""
    # Подготовка
    dispatcher = observer()
    first_stream = StringIO()
    second_stream = StringIO()
    first = logging_observer(operation_logger(first_stream))
    second = logging_observer(operation_logger(second_stream))
    dispatcher.add(first)
    dispatcher.add(second)
    dispatcher.add(first)
    event = operation_event_dto(
        subsystem=log_subsystem.CRUD, operation=crud_operation.DELETE, phase=event_phase.COMPLETED,
    )

    # Действие
    observer().notify(event)
    dispatcher.notify(event)

    # Проверка
    expected = {
        "subsystem": "CRUD", "operation": "delete", "phase": "completed",
        "level": "INFO", "message": "Операция завершена", "period": event.occurred_at.isoformat(),
    }
    assert event.occurred_at.utcoffset() == timedelta(0)
    for stream in (first_stream, second_stream):
        assert stream.getvalue().endswith("\n")
        assert [json.loads(line) for line in stream.getvalue().splitlines()] == [expected]


def test_ignored_event_notify_after_unsubscribe():
    """<summary>После удаления подписчик больше не получает события диспетчера.</summary>"""
    # Подготовка
    dispatcher = observer()
    stream = StringIO()
    subscriber = logging_observer(operation_logger(stream))
    dispatcher.add(subscriber)
    event = operation_event_dto(subsystem="CRUD", operation="get", phase=event_phase.STARTED)

    # Действие
    dispatcher.delete(subscriber)
    dispatcher.notify(event)

    # Проверка
    assert event.subsystem is log_subsystem.CRUD
    assert stream.getvalue() == ""


def test_serialized_event_write_uses_updated_dto_properties():
    """<summary>Логгер читает обновлённые поля DTO, пишет время в UTC и пропускает пустые поля.</summary>"""
    # Подготовка
    stream = StringIO()
    logger = operation_logger(stream)
    event = operation_event_dto(subsystem="CRUD", operation="get", phase=event_phase.STARTED)
    event.entity_type = "group"
    event.entity_code = "group-01"
    event.occurred_at = datetime(2026, 11, 24, 11, 35, tzinfo=timezone(timedelta(hours=8)))

    # Действие
    logger.write(event)
    event.phase = event_phase.REJECTED
    event.reason_code = "entity_not_found"
    logger.write(event)

    # Проверка
    started, rejected = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert started["level"] == "DEBUG"
    assert "reason_code" not in started
    assert rejected == {
        "subsystem": "CRUD", "operation": "get", "phase": "rejected",
        "level": "INFO", "message": "Операция отклонена", "period": "2026-11-24T03:35:00+00:00",
        "entity_type": "group", "entity_code": "group-01", "reason_code": "entity_not_found",
    }


def test_arguments_exception_occurred_at_rejects_time_without_zone():
    """<summary>Сеттер времени отклоняет дату события без часового пояса.</summary>"""
    # Подготовка
    event = operation_event_dto(subsystem="CRUD", operation="get", phase=event_phase.STARTED)

    # Действие и проверка
    with pytest.raises(arguments_exception, match="Поле: occurred_at"):
        event.occurred_at = datetime(2026, 11, 24, 3, 35)


def test_arguments_exception_subsystem_rejects_unknown_name():
    """<summary>DTO допускает имена операций склада и отклоняет неизвестные подсистемы.</summary>"""
    # Подготовка
    event = operation_event_dto(
        subsystem=log_subsystem.STORAGE, operation="movement_recorded", phase=event_phase.COMPLETED,
    )

    # Действие
    with pytest.raises(arguments_exception, match="Поле: subsystem"):
        event.subsystem = "UNKNOWN"

    # Проверка
    assert event.subsystem is log_subsystem.STORAGE
    assert event.operation == "movement_recorded"
