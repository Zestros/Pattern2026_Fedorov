from enum import Enum


class report_type_enum(Enum):
    """Поддерживаемые форматы отчётов."""

    TXT = 1
    CSV = 2
    MARKDOWN = 3
    XML = 4
    HTML = 5
