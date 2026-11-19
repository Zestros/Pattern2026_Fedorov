from Src.Core.abstract_dto import abstract_dto


class turnover_row_dto(abstract_dto):
    """Строка складской ОСВ по складу и номенклатуре."""

    # Код и наименование склада.
    warehouse_code: str
    warehouse_name: str
    # Код и наименование номенклатуры.
    item_code: str
    item_name: str
    # Код и наименование базовой единицы.
    unit_code: str
    unit_name: str
    # Остаток до начала периода.
    opening: float
    # Количество поступлений за период.
    receipts: float
    # Количество списаний за период.
    issues: float
    # Остаток после окончания периода.
    closing: float
