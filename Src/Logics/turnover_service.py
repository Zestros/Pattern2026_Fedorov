from datetime import date

from Src.Core.abstract_entity_repository import abstract_entity_repository
from Src.Core.exception import arguments_exception
from Src.Core.filter_criteria import filter_criteria, filter_item
from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.turnover_row_dto import turnover_row_dto
from Src.Logics.filter_query import filter_query
from Src.Logics.prototype import prototype
from Src.Models.transaction_model import transaction_model


class turnover_service:
    """Формирует количественную ОСВ из отобранных складских движений."""

    def __init__(self, repository: abstract_entity_repository, query: filter_query) -> None:
        """Получает журнал движений и преобразователь DTO в критерии."""
        self.__repository = repository
        self.__query = query

    def build(self, criteria: filter_dto, date_from: date, date_to: date) -> tuple[turnover_row_dto, ...]:
        """Отбирает движения по фильтрам и рассчитывает итоги по складу и товару."""
        if date_from > date_to:
            raise arguments_exception("date_to", "Конец периода должен быть не раньше начала")
        rules = self.__query.prepare(transaction_model, criteria)
        period = filter_item(("occurred_at",), lambda timestamp, end: timestamp.date() <= end, date_to)
        report_criteria = filter_criteria((*rules.filters, period), rules.sort)
        source = prototype(self.__repository.list(transaction_model), report_criteria)

        groups: dict[tuple[str, str], list[transaction_model]] = {}
        for movement in source.clone().data:
            key = (movement.warehouse.unique_code, movement.item.unique_code)
            groups.setdefault(key, []).append(movement)
        return tuple(self.__row(movements, date_from) for movements in groups.values())

    @staticmethod
    def __row(movements: list[transaction_model], date_from: date) -> turnover_row_dto:
        """Считает начальный остаток и обороты в базовой единице строки."""
        opening = receipts = issues = 0.0
        for row in movements:
            if row.occurred_at.date() < date_from:
                opening += row.quantity
            elif row.quantity > 0:
                receipts += row.quantity
            else:
                issues -= row.quantity
        first = movements[0]
        return turnover_row_dto(
            warehouse_code=first.warehouse.unique_code, warehouse_name=first.warehouse.name,
            item_code=first.item.unique_code, item_name=first.item.name,
            unit_code=first.unit.unique_code, unit_name=first.unit.name,
            opening=opening, receipts=receipts, issues=issues, closing=opening + receipts - issues,
        )
