from collections.abc import Callable, Iterable
from datetime import date

from Src.Core.abstract_entity_repository import abstract_entity_repository
from Src.Core.exception import arguments_exception
from Src.Core.filter_operator_enum import filter_operator_enum
from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.filter_item_dto import filter_item_dto
from Src.Dtos.turnover_row_dto import turnover_row_dto
from Src.Logics.prototype import prototype
from Src.Models.transaction_model import transaction_model


class turnover_service:
    """Формирует количественную ОСВ из отобранных складских движений."""

    def __init__(
        self, repository: abstract_entity_repository, create_prototype: Callable[..., prototype],
    ) -> None:
        """Получает журнал движений и способ создать настроенный прототип."""
        self.__repository = repository
        self.__create_prototype = create_prototype

    def build(self, criteria: filter_dto, date_from: date, date_to: date) -> tuple[turnover_row_dto, ...]:
        """Рассчитывает начальные остатки, затем обороты за период и итоговые строки."""
        if date_from > date_to:
            raise arguments_exception("date_to", "Конец периода должен быть не раньше начала")

        movements = self.__repository.list(transaction_model)
        before_start = filter_item_dto(field="occurred_at", operator=filter_operator_enum.BEFORE, value=date_from)
        history = self.__select(movements, filter_dto(filters=(before_start, *criteria.filters)))
        opening_balances: dict[tuple[str, str], float] = {}
        for row in history:
            key = self.__group_key(row)
            opening_balances[key] = opening_balances.get(key, 0.0) + row.quantity

        from_start = filter_item_dto(field="occurred_at", operator=filter_operator_enum.ON_OR_AFTER, value=date_from)
        through_end = filter_item_dto(field="occurred_at", operator=filter_operator_enum.ON_OR_BEFORE, value=date_to)
        period = self.__select(movements, filter_dto(filters=(from_start, through_end, *criteria.filters)))
        period_groups: dict[tuple[str, str], list[transaction_model]] = {}
        for row in period:
            period_groups.setdefault(self.__group_key(row), []).append(row)

        ordered = self.__select(
            movements, filter_dto(filters=(through_end, *criteria.filters), sort=criteria.sort),
        )

        rows: dict[tuple[str, str], turnover_row_dto] = {}
        for movement in ordered:
            key = self.__group_key(movement)
            if key not in rows:
                rows[key] = self.__row(movement, opening_balances.get(key, 0.0), period_groups.get(key, ()))
        return tuple(rows.values())

    def __select(
        self, movements: Iterable[transaction_model], criteria: filter_dto,
    ) -> tuple[transaction_model, ...]:
        """Клонирует коллекцию движений с указанными условиями или сортировкой."""
        return self.__create_prototype(movements, criteria, transaction_model).clone().data

    @staticmethod
    def __group_key(movement: transaction_model) -> tuple[str, str]:
        """Возвращает ключ остатка по складу и номенклатуре."""
        return movement.warehouse.unique_code, movement.item.unique_code

    @staticmethod
    def __row(
        movement: transaction_model, opening: float, period: Iterable[transaction_model],
    ) -> turnover_row_dto:
        """Суммирует поступления и списания периода и формирует строку."""
        receipts = issues = 0.0
        for row in period:
            if row.quantity > 0:
                receipts += row.quantity
            else:
                issues -= row.quantity
        return turnover_row_dto(
            warehouse_code=movement.warehouse.unique_code, warehouse_name=movement.warehouse.name,
            item_code=movement.item.unique_code, item_name=movement.item.name,
            unit_code=movement.unit.unique_code, unit_name=movement.unit.name,
            opening=opening, receipts=receipts, issues=issues, closing=opening + receipts - issues,
        )
