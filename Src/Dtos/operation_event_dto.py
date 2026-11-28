from datetime import datetime, timezone

from Src.Core.abstract_dto import abstract_dto
from Src.Core.event_phase import event_phase
from Src.Core.exception import arguments_exception
from Src.Core.log_subsystem import log_subsystem
from Src.Core.validator import validator


class operation_event_dto(abstract_dto):
    """Передаёт подписчикам сведения об операции."""

    # Время проставляется при создании; сведения о сущности и причине могут отсутствовать.
    _optional_fields = ("occurred_at", "entity_type", "entity_code", "reason_code", "details")
    __entity_type = None
    __entity_code = None
    __reason_code = None
    __details = None

    def __init__(self, **values: object) -> None:
        """Заполняет время текущим моментом, если его не передали."""
        if "occurred_at" not in values:
            values["occurred_at"] = datetime.now(timezone.utc)
        super().__init__(**values)

    @property
    def subsystem(self) -> log_subsystem:
        """Возвращает подсистему, в которой произошла операция."""
        return self.__subsystem

    @subsystem.setter
    def subsystem(self, value: log_subsystem | str) -> None:
        """Принимает известную подсистему или её строковое имя."""
        validator.validate(value, str, field="subsystem")
        try:
            subsystem = log_subsystem(value)
        except ValueError as error:
            raise arguments_exception("subsystem", "Неизвестная подсистема журналирования") from error
        object.__setattr__(self, "_operation_event_dto__subsystem", subsystem)

    @property
    def operation(self) -> str:
        """Возвращает имя операции."""
        return self.__operation

    @operation.setter
    def operation(self, value: str) -> None:
        """Проверяет и сохраняет непустое имя операции."""
        validator.validate(value, str, field="operation")
        object.__setattr__(self, "_operation_event_dto__operation", str(value))

    @property
    def phase(self) -> event_phase:
        """Возвращает стадию операции."""
        return self.__phase

    @phase.setter
    def phase(self, value: event_phase) -> None:
        """Проверяет и сохраняет стадию из перечисления."""
        validator.validate(value, event_phase, field="phase")
        object.__setattr__(self, "_operation_event_dto__phase", value)

    @property
    def occurred_at(self) -> datetime:
        """Возвращает время события в UTC."""
        return self.__occurred_at

    @occurred_at.setter
    def occurred_at(self, value: datetime) -> None:
        """Проверяет часовой пояс и сохраняет тот же момент в UTC."""
        validator.validate(value, datetime, field="occurred_at")
        if value.utcoffset() is None:
            raise arguments_exception("occurred_at", "Ожидается дата и время с часовым поясом")
        object.__setattr__(self, "_operation_event_dto__occurred_at", value.astimezone(timezone.utc))

    @property
    def entity_type(self) -> str | None:
        """Возвращает тип сущности, если он указан."""
        return self.__entity_type

    @entity_type.setter
    def entity_type(self, value: str | None) -> None:
        """Проверяет и сохраняет тип сущности либо очищает его."""
        if value is not None:
            validator.validate(value, str, field="entity_type")
        object.__setattr__(self, "_operation_event_dto__entity_type", value)

    @property
    def entity_code(self) -> str | None:
        """Возвращает код сущности, если он указан."""
        return self.__entity_code

    @entity_code.setter
    def entity_code(self, value: str | None) -> None:
        """Проверяет и сохраняет код сущности либо очищает его."""
        if value is not None:
            validator.validate(value, str, field="entity_code")
        object.__setattr__(self, "_operation_event_dto__entity_code", value)

    @property
    def reason_code(self) -> str | None:
        """Возвращает код причины отклонения, если он указан."""
        return self.__reason_code

    @reason_code.setter
    def reason_code(self, value: str | None) -> None:
        """Проверяет и сохраняет код причины либо очищает его."""
        if value is not None:
            validator.validate(value, str, field="reason_code")
        object.__setattr__(self, "_operation_event_dto__reason_code", value)

    @property
    def details(self) -> dict[str, str | int | float | tuple[str, ...]] | None:
        """Возвращает копию дополнительных сведений об операции."""
        return None if self.__details is None else self.__details.copy()

    @details.setter
    def details(self, value: dict[str, str | int | float | tuple[str, ...]] | None) -> None:
        """Сохраняет копию дополнительных сведений либо очищает их."""
        if value is not None:
            validator.validate(value, dict, field="details")
            value = value.copy()
        object.__setattr__(self, "_operation_event_dto__details", value)
