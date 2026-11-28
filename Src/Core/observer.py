from Src.Core.abstract_observation import abstract_observation
from Src.Dtos.operation_event_dto import operation_event_dto


class observer:
    """Доставляет событие подписчикам этого экземпляра."""

    def __init__(self) -> None:
        """Создаёт пустой список подписчиков."""
        self.__subscribers: list[abstract_observation] = []

    def add(self, subscriber: abstract_observation) -> None:
        """Регистрирует подписчика, если его ещё нет в списке."""
        if subscriber not in self.__subscribers:
            self.__subscribers.append(subscriber)

    def delete(self, subscriber: abstract_observation) -> None:
        """Удаляет подписчика, если он зарегистрирован."""
        if subscriber in self.__subscribers:
            self.__subscribers.remove(subscriber)

    def notify(self, event: operation_event_dto) -> None:
        """Синхронно передаёт событие подписчикам по снимку списка."""
        for subscriber in self.__subscribers.copy():
            subscriber.handler(event)
