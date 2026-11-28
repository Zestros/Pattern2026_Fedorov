from collections.abc import Callable
from time import perf_counter

from flask import Flask, Response, g, request
from starlette.exceptions import HTTPException

from Src.Core.abstract_event_source import abstract_event_source
from Src.Core.event_phase import event_phase
from Src.Core.log_subsystem import log_subsystem
from Src.Dtos.operation_event_dto import operation_event_dto


class web_request_events(abstract_event_source):
    """Публикует события о запросах и ответах Flask."""

    def __init__(self, *, publish_event: Callable[[operation_event_dto], None]) -> None:
        """Подключает издателя событий Web."""
        self.set_event_publisher(publish_event)

    def set_event_publisher(self, publish_event: Callable[[operation_event_dto], None]) -> None:
        """Подменяет функцию публикации событий Web."""
        self.__publish_event = publish_event

    def register(self, app: Flask) -> None:
        """Подключает методы публикации ко всем маршрутам приложения."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)

    def before_request(self) -> None:
        """Фиксирует начало запроса перед обработкой маршрута."""
        g.web_request_started_at = perf_counter()
        self.__publish_event(operation_event_dto(
            subsystem=log_subsystem.HTTP, operation=request.method, phase=event_phase.STARTED,
            details={"path": request.path},
        ))

    def after_request(self, response: Response) -> Response:
        """Публикует итоговый HTTP-статус и возвращает ответ приложения."""
        self.__publish_result(response.status_code)
        return response

    def teardown_request(self, error: BaseException | None) -> None:
        """Публикует исход, если исключение передано из Flask в Connexion."""
        if error is not None and g.get("web_request_started_at") is not None:
            status_code = error.status_code if isinstance(error, HTTPException) else 500
            self.__publish_result(status_code)

    def __publish_result(self, status_code: int) -> None:
        """Передаёт статус и длительность запроса диспетчеру."""
        if status_code >= 500:
            phase = event_phase.FAILED
        elif status_code >= 400:
            phase = event_phase.REJECTED
        else:
            phase = event_phase.COMPLETED

        details: dict[str, str | int | float | tuple[str, ...]] = {"path": request.path, "status_code": status_code}
        started_at = g.pop("web_request_started_at", None)
        if started_at is not None:
            details["duration_ms"] = round((perf_counter() - started_at) * 1000, 3)
        self.__publish_event(operation_event_dto(
            subsystem=log_subsystem.HTTP, operation=request.method, phase=phase, details=details,
        ))
